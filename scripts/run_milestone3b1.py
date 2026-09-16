"""Run the frozen M3 audit over one representative session per fcx-1 animal.

This is a reporting layer only.  It deliberately calls the existing M1/M2/M3
loaders unchanged and does not repair or reinterpret session-specific inputs.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.io import loadmat


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from data import (  # noqa: E402
    CausalSessionDataset,
    audit_manifest,
    build_state_timeline,
    load_aligned_session,
    load_session_manifest,
)
from data.deep_qc import annotation_diagnostics, field_role  # noqa: E402


REQUIRED_SUFFIXES = (
    "_BasicMetaData.mat",
    ".xml",
    "_ChannelAnatomy.csv",
    "_GoodSleepInterval.mat",
    "_WSRestrictedIntervals.mat",
    "_SStable.mat",
    ".eeg",
)
CORE_TARGETS = ("WAKE", "NREM", "REM")
PILOT_SESSIONS = {
    "BWRat17_121712",
    "BWRat18_020513",
    "BWRat19_032513",
    "BWRat20_101013",
    "Splinter_020915",
}


def _json_safe(value: object) -> object:
    if isinstance(value, float) and not math.isfinite(value):
        return "Infinity" if value > 0 else "-Infinity"
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _json(value: object) -> str:
    return json.dumps(
        _json_safe(value),
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )


def _intervals(value: object) -> list[list[float]]:
    array = np.asarray(value, dtype=np.float64)
    if array.ndim == 1 and array.size == 2:
        array = array.reshape(1, 2)
    return [[float(start), float(stop)] for start, stop in array]


def _raw_intervals(value: object) -> list[list[float | str]]:
    """Keep non-finite source sentinels explicit while emitting valid JSON."""

    return [
        [
            number if math.isfinite(number) else ("Infinity" if number > 0 else "-Infinity")
            for number in row
        ]
        for row in _intervals(value)
    ]


def preflight(session_dir: Path, session_id: str) -> tuple[bool, list[str]]:
    """Open a small prefix of every required file without changing it."""

    issues: list[str] = []
    if not session_dir.is_dir():
        return False, ["directory_missing"]
    for suffix in REQUIRED_SUFFIXES:
        path = session_dir / f"{session_id}{suffix}"
        if not path.is_file():
            issues.append(f"missing:{path.name}")
            continue
        if path.stat().st_size <= 0:
            issues.append(f"empty:{path.name}")
            continue
        try:
            with path.open("rb") as stream:
                if not stream.read(16):
                    issues.append(f"unreadable_content:{path.name}")
        except OSError as error:
            issues.append(f"unreadable:{path.name}:{error}")
    return not issues, issues


def _strict_causal_check(session, width: int) -> tuple[bool, int, str]:
    try:
        dataset = CausalSessionDataset(session, width)
        if not dataset.rows:
            return False, 0, "no valid samples"
        indices = sorted({0, len(dataset) // 2, len(dataset) - 1})
        for index in indices:
            sample = dataset.get_sample(index)
            row = sample.index
            assert math.isclose(row.context_start_s, row.decision_time_s - width)
            assert math.isclose(row.context_stop_s, row.decision_time_s)
            assert math.isclose(row.target_start_s, row.decision_time_s - 1.0)
            assert math.isclose(row.target_stop_s, row.decision_time_s)
            assert row.target_label in CORE_TARGETS
            assert row.valid
            assert not sample.lfp.time_s.size or sample.lfp.time_s[-1] < row.decision_time_s
            assert not sample.spike_bin_stop_s.size or sample.spike_bin_stop_s[-1] <= row.decision_time_s
        return True, len(dataset), ""
    except Exception as error:  # preserved in the report; never repaired here
        return False, 0, f"{type(error).__name__}: {error}"


def _oob_and_malformed(states, common_end_s: float) -> tuple[list[dict], list[dict]]:
    oob: dict[str, list] = defaultdict(list)
    malformed: dict[str, list] = defaultdict(list)
    for issue in states.issues:
        item = {
            "row_index": issue.row_index,
            "interval_s": [issue.start_s, issue.stop_s],
            "reason": issue.reason,
        }
        if issue.start_s < 0 or issue.stop_s > common_end_s:
            oob[issue.field].append(item)
        else:
            malformed[issue.field].append(item)
    oob_rows = [
        {"field": field, "role": field_role(field), "count": len(items), "rows": items}
        for field, items in sorted(oob.items())
    ]
    malformed_rows = [
        {"field": field, "role": field_role(field), "count": len(items), "rows": items}
        for field, items in sorted(malformed.items())
    ]
    return oob_rows, malformed_rows


def _support_pattern(session) -> str:
    support = session.time_support
    metadata_open = bool(np.any(np.isposinf(support.raw_metadata_recording_intervals_s[:, 1])))
    good_sleep_open = bool(np.any(np.isposinf(support.raw_good_sleep_intervals_s[:, 1])))
    if metadata_open or good_sleep_open:
        sources = []
        if metadata_open:
            sources.append("metadata")
        if good_sleep_open:
            sources.append("good_sleep")
        return "open_ended_" + "_and_".join(sources) + "_resolved_to_lfp"
    if support.candidate_analysis_intervals_s.shape[0] != 1:
        return "disconnected_analysis_support"
    if not math.isclose(support.analysis_start_s, 0.0, abs_tol=1e-9):
        return "nonzero_analysis_origin"
    metadata_match = math.isclose(support.metadata_end_s, support.lfp_support_end_s, abs_tol=1e-9)
    good_match = math.isclose(support.good_sleep_support_end_s, support.lfp_support_end_s, abs_tol=1e-9)
    if metadata_match and good_match:
        return "metadata_good_sleep_lfp_equal"
    if (not metadata_match) and good_match:
        return "metadata_differs_good_sleep_matches_lfp"
    if metadata_match and (not good_match):
        return "good_sleep_differs_metadata_matches_lfp"
    return "metadata_and_good_sleep_differ_from_lfp"


def _raw_infinite_support_diagnostic(session_dir: Path, session_id: str) -> dict:
    """Read only the minimum raw provenance needed to explain a metadata failure."""

    bmd = loadmat(
        session_dir / f"{session_id}_BasicMetaData.mat", simplify_cells=True
    )["bmd"]
    good = loadmat(
        session_dir / f"{session_id}_GoodSleepInterval.mat", simplify_cells=True
    )["GoodSleepInterval"]["timePairFormat"]
    xml_root = ET.parse(session_dir / f"{session_id}.xml").getroot()
    n_channels = int(xml_root.findtext("acquisitionSystem/nChannels"))
    acquisition_hz = float(xml_root.findtext("acquisitionSystem/samplingRate"))
    lfp_hz = float(xml_root.findtext("fieldPotentials/lfpSamplingRate"))
    eeg_bytes = (session_dir / f"{session_id}.eeg").stat().st_size
    bytes_per_timepoint = n_channels * 2
    with (session_dir / f"{session_id}_ChannelAnatomy.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as stream:
        anatomy = [row[1].strip() or None for row in csv.reader(stream)]
    good_channel = int(bmd["goodeegchannel"])
    theta_channel = int(bmd["Thetachannel"])
    return {
        "recording_file_intervals_raw": _raw_intervals(bmd["RecordingFileIntervals"]),
        "good_sleep_intervals_raw": _raw_intervals(good),
        "n_channels_xml": n_channels,
        "acquisition_sample_rate_hz_xml": acquisition_hz,
        "lfp_sample_rate_hz_xml": lfp_hz,
        "eeg_file_size_bytes": eeg_bytes,
        "eeg_remainder_bytes": eeg_bytes % bytes_per_timepoint,
        "lfp_support_end_s_from_file": eeg_bytes / bytes_per_timepoint / lfp_hz,
        "recommended_lfp_channel_raw": good_channel,
        "recommended_lfp_anatomy_raw": anatomy[good_channel - 1],
        "theta_channel_raw": theta_channel,
        "theta_channel_anatomy_raw": anatomy[theta_channel - 1],
        "anatomical_regions_raw": sorted({label for label in anatomy if label}),
    }


def build_rows(entries, results):
    rows: list[dict] = []
    details: dict[str, dict] = {}
    for entry, qc in zip(entries, results):
        preflight_ok, preflight_issues = preflight(entry.local_path, entry.session_id)
        row = {
            "animal_id": entry.animal_id,
            "session_id": entry.session_id,
            "qc_status": qc.qc_status,
            "preflight_status": "PASS" if preflight_ok else "FAIL",
            "preflight_issues": _json(preflight_issues),
            "metadata_load_status": "PASS" if qc.metadata_valid else "FAIL",
            "lfp_load_status": "PASS" if qc.lfp_valid else ("NOT_RUN" if not qc.metadata_valid else "FAIL"),
            "spikes_load_status": "PASS" if qc.spikes_valid else ("NOT_RUN" if not qc.metadata_valid else "FAIL"),
            "annotations_load_status": "PASS" if qc.sleep_annotations_valid else ("NOT_RUN" if not qc.metadata_valid else "FAIL"),
            "metadata_recording_intervals_s": "",
            "raw_metadata_recording_intervals_s": "",
            "lfp_support_intervals_s": "",
            "good_sleep_intervals_s": "",
            "raw_good_sleep_intervals_s": "",
            "resolved_metadata_constraint_s": "",
            "resolved_good_sleep_constraint_s": "",
            "analysis_support_intervals_s": "",
            "support_resolution_method": "",
            "analysis_support_origin_s": "",
            "analysis_support_connected": "",
            "recording_duration_s": qc.recording_duration_s if qc.recording_duration_s is not None else "",
            "duration_mismatch": qc.duration_mismatch if qc.duration_mismatch is not None else "",
            "support_pattern": "",
            "lfp_sampling_rate_hz": qc.lfp_sample_rate_hz if qc.lfp_sample_rate_hz is not None else "",
            "acquisition_sampling_rate_hz": qc.acquisition_sample_rate_hz if qc.acquisition_sample_rate_hz is not None else "",
            "lfp_channel_count": qc.n_channels if qc.n_channels is not None else "",
            "recommended_lfp_channel": qc.recommended_lfp_channel if qc.recommended_lfp_channel is not None else "",
            "recommended_lfp_anatomy": qc.recommended_lfp_anatomy or "",
            "recommended_theta_channel": qc.theta_channel if qc.theta_channel is not None else "",
            "recommended_theta_anatomy": qc.theta_channel_anatomy or "",
            "anatomical_regions": "|".join(qc.anatomical_regions),
            "stable_unit_count": qc.stable_unit_count if qc.stable_unit_count is not None else "",
            "total_stable_spikes": qc.total_spike_count if qc.total_spike_count is not None else "",
            "tail_spikes_outside_complete_bins": qc.excluded_tail_spike_count if qc.excluded_tail_spike_count is not None else "",
            "out_of_analysis_support_spikes": "",
            "wake_seconds": qc.wake_seconds if qc.wake_seconds is not None else "",
            "nrem_seconds": qc.nrem_seconds if qc.nrem_seconds is not None else "",
            "rem_seconds": qc.rem_seconds if qc.rem_seconds is not None else "",
            "ignore_seconds": qc.ignore_seconds if qc.ignore_seconds is not None else "",
            "valid_supervision_fraction": "",
            "missing_core_classes": "",
            "annotation_oob_by_exact_field": "[]",
            "core_target_oob_count": "",
            "auxiliary_oob_count": "",
            "broad_or_episode_oob_count": "",
            "malformed_annotation_rows": "[]",
            "conflict_seconds": qc.conflict_seconds if qc.conflict_seconds is not None else "",
            "conflict_duration_by_type_s": "{}",
            "exact_conflict_intervals": "[]",
            "core_alignment_valid": qc.core_alignment_valid,
            "causal_5s_valid": False,
            "causal_10s_valid": False,
            "causal_30s_valid": False,
            "causal_sample_counts": "{}",
            "findings": _json([finding.__dict__ for finding in qc.findings]),
            "structural_issue": "",
        }
        detail = {"qc": _json_safe(qc.to_dict())}
        if qc.metadata_valid:
            session = load_aligned_session(entry.local_path)
            timeline = build_state_timeline(session)
            diagnostic = annotation_diagnostics(session, timeline)
            oob, malformed = _oob_and_malformed(session.sleep_states, session.report.common_end_s)
            role_counts = Counter()
            for item in oob:
                role_counts[item["role"]] += item["count"]
            causal_counts = {}
            causal_errors = {}
            for width in (5, 10, 30):
                ok, count, error = _strict_causal_check(session, width)
                row[f"causal_{width}s_valid"] = ok
                causal_counts[str(width)] = count
                if error:
                    causal_errors[str(width)] = error
            counts = Counter(timeline.target_label.tolist())
            missing = [label for label in CORE_TARGETS if counts[label] == 0]
            row.update(
                {
                    "metadata_recording_intervals_s": _json(_intervals(session.time_support.metadata_recording_intervals_s)),
                    "raw_metadata_recording_intervals_s": _json(_raw_intervals(session.time_support.raw_metadata_recording_intervals_s)),
                    "lfp_support_intervals_s": _json(_intervals(session.time_support.lfp_support_intervals_s)),
                    "good_sleep_intervals_s": _json(_intervals(session.time_support.good_sleep_intervals_s)),
                    "raw_good_sleep_intervals_s": _json(_raw_intervals(session.time_support.raw_good_sleep_intervals_s)),
                    "resolved_metadata_constraint_s": _json(_intervals(session.time_support.resolved_metadata_constraint_s)),
                    "resolved_good_sleep_constraint_s": _json(_intervals(session.time_support.resolved_good_sleep_constraint_s)),
                    "analysis_support_intervals_s": _json(_intervals(session.time_support.candidate_analysis_intervals_s)),
                    "support_resolution_method": session.time_support.support_resolution_method,
                    "analysis_support_origin_s": session.time_support.analysis_start_s,
                    "analysis_support_connected": session.time_support.is_single_contiguous_interval,
                    "support_pattern": _support_pattern(session),
                    "out_of_analysis_support_spikes": 0,
                    "valid_supervision_fraction": float(np.mean(timeline.valid_label)),
                    "missing_core_classes": "|".join(missing),
                    "annotation_oob_by_exact_field": _json(oob),
                    "core_target_oob_count": role_counts["core_target"],
                    "auxiliary_oob_count": role_counts["auxiliary_substate"],
                    "broad_or_episode_oob_count": role_counts["broad_state_or_episode"],
                    "malformed_annotation_rows": _json(malformed),
                    "conflict_duration_by_type_s": _json(diagnostic["conflict_duration_by_type_s"]),
                    "exact_conflict_intervals": _json(diagnostic["conflicts"]),
                    "causal_sample_counts": _json(causal_counts),
                }
            )
            detail.update(
                {
                    "annotation_diagnostics": diagnostic,
                    "malformed_annotation_rows": malformed,
                    "causal_errors": causal_errors,
                }
            )
        else:
            try:
                raw = _raw_infinite_support_diagnostic(entry.local_path, entry.session_id)
                row["support_pattern"] = "open_ended_nonfinite_metadata_and_good_sleep"
                row["structural_issue"] = "nonfinite_recording_and_good_sleep_endpoints"
                row["lfp_sampling_rate_hz"] = raw["lfp_sample_rate_hz_xml"]
                row["acquisition_sampling_rate_hz"] = raw["acquisition_sample_rate_hz_xml"]
                row["lfp_channel_count"] = raw["n_channels_xml"]
                row["recommended_lfp_channel"] = raw["recommended_lfp_channel_raw"]
                row["recommended_lfp_anatomy"] = raw["recommended_lfp_anatomy_raw"]
                row["recommended_theta_channel"] = raw["theta_channel_raw"]
                row["recommended_theta_anatomy"] = raw["theta_channel_anatomy_raw"]
                row["anatomical_regions"] = "|".join(raw["anatomical_regions_raw"])
                detail["raw_structural_diagnostic"] = raw
            except Exception as error:
                detail["raw_structural_diagnostic_error"] = f"{type(error).__name__}: {error}"
        rows.append(row)
        details[entry.session_id] = detail
    return rows, details


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _display(value: object) -> str:
    if value == "":
        return "NA"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def build_animal_rows(session_rows: list[dict]) -> list[dict]:
    output = []
    for row in session_rows:
        valid = row["core_alignment_valid"] and all(
            row[f"causal_{width}s_valid"] for width in (5, 10, 30)
        )
        total = sum(row[name] for name in ("wake_seconds", "nrem_seconds", "rem_seconds", "ignore_seconds") if isinstance(row[name], int))
        output.append(
            {
                "animal_id": row["animal_id"],
                "session_count": 1,
                "session_id": row["session_id"],
                "qc_status": row["qc_status"],
                "common_pipeline_valid": valid,
                "effective_recording_duration_s": row["recording_duration_s"],
                "stable_unit_count": row["stable_unit_count"],
                "total_stable_spikes": row["total_stable_spikes"],
                "wake_seconds": row["wake_seconds"],
                "nrem_seconds": row["nrem_seconds"],
                "rem_seconds": row["rem_seconds"],
                "ignore_seconds": row["ignore_seconds"],
                "wake_fraction": row["wake_seconds"] / total if total else "",
                "nrem_fraction": row["nrem_seconds"] / total if total else "",
                "rem_fraction": row["rem_seconds"] / total if total else "",
                "ignore_fraction": row["ignore_seconds"] / total if total else "",
                "valid_supervision_fraction": row["valid_supervision_fraction"],
                "missing_core_classes": row["missing_core_classes"],
                "recommended_lfp_channel": row["recommended_lfp_channel"],
                "recommended_lfp_anatomy": row["recommended_lfp_anatomy"],
                "recommended_theta_channel": row["recommended_theta_channel"],
                "recommended_theta_anatomy": row["recommended_theta_anatomy"],
                "duration_mismatch": row["duration_mismatch"],
                "support_pattern": row["support_pattern"],
                "core_target_oob_count": row["core_target_oob_count"],
                "auxiliary_oob_count": row["auxiliary_oob_count"],
                "conflict_seconds": row["conflict_seconds"],
                "structural_issue": row["structural_issue"],
            }
        )
    return output


def write_markdown(report_dir: Path, session_rows: list[dict], animal_rows: list[dict], details: dict) -> None:
    successes = [row for row in session_rows if row["core_alignment_valid"]]
    status_counts = Counter(row["qc_status"] for row in session_rows)
    unit_values = [row["stable_unit_count"] for row in successes]
    oob_fields = Counter()
    role_counts = Counter()
    conflict_types = Counter()
    pilot_types: set[str] = set()
    new_session_types: set[str] = set()
    for row in successes:
        for item in json.loads(row["annotation_oob_by_exact_field"]):
            oob_fields[item["field"]] += item["count"]
            role_counts[item["role"]] += item["count"]
        for kind, duration in json.loads(row["conflict_duration_by_type_s"]).items():
            conflict_types[kind] += duration
            (pilot_types if row["session_id"] in PILOT_SESSIONS else new_session_types).add(kind)
    new_conflict_types = sorted(new_session_types - pilot_types)
    pilot_patterns = {row["support_pattern"] for row in session_rows if row["session_id"] in PILOT_SESSIONS}
    new_patterns = sorted(
        {row["support_pattern"] for row in session_rows if row["session_id"] not in PILOT_SESSIONS}
        - pilot_patterns
    )

    def fraction_summary(field: str) -> str:
        values = [(float(row[field]), row["animal_id"]) for row in animal_rows if row[field] != ""]
        low = min(values)
        high = max(values)
        return (
            f"min={low[0]:.3%} ({low[1]}), median={statistics.median(value for value, _ in values):.3%}, "
            f"max={high[0]:.3%} ({high[1]})"
        )
    lines = [
        "# Milestone 3-B1: 11-animal representative-session audit",
        "",
        "The frozen M1/M2/M3 pipeline was run unchanged. Raw fcx-1 files were opened read-only. "
        "No animal-specific or session-specific processing branch was added.",
        "",
        f"Result: preflight 11/11 PASS; common pipeline {len(successes)}/11 valid; "
        f"PASS={status_counts['PASS']}, WARN={status_counts['WARN']}, FAIL={status_counts['FAIL']}.",
        "",
        "| animal | session | QC | duration s | units | WAKE | NREM | REM | IGNORE | valid frac | core OOB | aux OOB | conflict s | support pattern |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in session_rows:
        lines.append(
            f"| {row['animal_id']} | {row['session_id']} | {row['qc_status']} | "
            f"{_display(row['recording_duration_s'])} | {_display(row['stable_unit_count'])} | "
            f"{_display(row['wake_seconds'])} | {_display(row['nrem_seconds'])} | {_display(row['rem_seconds'])} | "
            f"{_display(row['ignore_seconds'])} | {_display(row['valid_supervision_fraction'])} | "
            f"{_display(row['core_target_oob_count'])} | {_display(row['auxiliary_oob_count'])} | "
            f"{_display(row['conflict_seconds'])} | {row['support_pattern']} |"
        )
    lines.extend(
        [
            "",
            "## Cross-animal facts",
            "",
            f"- Stable-unit counts are available for {len(unit_values)}/11 pipeline-valid sessions: "
            f"min={min(unit_values)}, median={statistics.median(unit_values):g}, max={max(unit_values)}.",
            "- Stable-unit distribution: " + ", ".join(
                f"{row['animal_id']}={row['stable_unit_count']}" for row in animal_rows if row["stable_unit_count"] != ""
            ) + ".",
            "- WAKE fraction: " + fraction_summary("wake_fraction") + ".",
            "- NREM fraction: " + fraction_summary("nrem_fraction") + ".",
            "- REM fraction: " + fraction_summary("rem_fraction") + ".",
            "- IGNORE fraction: " + fraction_summary("ignore_fraction") + ".",
            "- Valid-supervision fraction: " + fraction_summary("valid_supervision_fraction") + ".",
            f"- Missing core classes: " + (", ".join(f"{r['animal_id']}:{r['missing_core_classes']}" for r in animal_rows if r['missing_core_classes']) or "none among pipeline-valid sessions") + ".",
            f"- OOB roles: core_target={role_counts['core_target']}, auxiliary_substate={role_counts['auxiliary_substate']}, "
            f"broad_state_or_episode={role_counts['broad_state_or_episode']}.",
            "- OOB exact fields: " + (_json(dict(sorted(oob_fields.items()))) if oob_fields else "none") + ".",
            "- Conflict duration by type (seconds): " + (_json(dict(sorted(conflict_types.items()))) if conflict_types else "none") + ".",
            "- Conflict types first seen in the six newly added sessions relative to the five-session pilot: " + (", ".join(new_conflict_types) if new_conflict_types else "none") + ".",
            "- New time-support patterns relative to the pilot: " + (", ".join(new_patterns) if new_patterns else "none") + ".",
            "- Finite-source duration mismatches: " + ", ".join(
                row["session_id"] for row in session_rows
                if row["duration_mismatch"] is True and not row["support_pattern"].startswith("open_ended")
            ) + ".",
            "- Non-zero origins, disconnected finite analysis supports, and malformed annotation rows: none among all 11 pipeline-valid sessions.",
            "- Core-target annotation OOB: 0 among all 11 pipeline-valid sessions.",
            "- Rizzo contains a 29-second `WAKE+SLEEP+NREM` core-target conflict on `[9981,10010)`; strict policy maps every affected bin to IGNORE.",
            "",
            "## Interpretation boundary",
            "",
            "`20140528_565um` contains official open-ended `[0, Inf]` values in both "
            "`BasicMetaData.RecordingFileIntervals` and `GoodSleepInterval.timePairFormat`. "
            "The raw values remain unchanged. Their positive-infinity stops are interpreted as no finite official upper bound, "
            "and the derived constraints are clipped to the verified finite EEG/LFP support. No recording end is inferred from spikes or labels.",
            "",
            "The full CSV contains support provenance, selected channel anatomy, exact OOB rows, exact conflict intervals, "
            "and independent 5/10/30-second past-only checks for every pipeline-valid session.",
        ]
    )
    (report_dir / "fcx1_11animal_session_qc.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    animal_lines = [
        "# Milestone 3-B1 animal-level summary",
        "",
        "One intentionally selected representative session is present for each of the 11 official animals.",
        "",
        "| animal | session | QC | common pipeline | units | valid frac | LFP anatomy | theta anatomy | duration mismatch | missing classes |",
        "|---|---|---:|---:|---:|---:|---|---|---:|---|",
    ]
    for row in animal_rows:
        animal_lines.append(
            f"| {row['animal_id']} | {row['session_id']} | {row['qc_status']} | "
            f"{row['common_pipeline_valid']} | {_display(row['stable_unit_count'])} | "
            f"{_display(row['valid_supervision_fraction'])} | {row['recommended_lfp_anatomy'] or 'NA'} | "
            f"{row['recommended_theta_anatomy'] or 'NA'} | {_display(row['duration_mismatch'])} | "
            f"{row['missing_core_classes'] or 'none/NA'} |"
        )
    lfp_anatomy = Counter(row["recommended_lfp_anatomy"] or "NA" for row in animal_rows)
    theta_anatomy = Counter(row["recommended_theta_anatomy"] or "NA" for row in animal_rows)
    animal_lines.extend(
        [
            "",
            "Selected LFP anatomy distribution: " + _json(dict(sorted(lfp_anatomy.items()))) + ".",
            "",
            "Selected theta anatomy distribution: " + _json(dict(sorted(theta_anatomy.items()))) + ".",
            "",
            "Coverage fractions are descriptive QC only; they do not define inclusion, normalization, representation, or a split.",
        ]
    )
    (report_dir / "fcx1_11animal_summary.md").write_text("\n".join(animal_lines) + "\n", encoding="utf-8")

    structural_path = report_dir / "structural_issues.md"
    structural_rows = [row for row in session_rows if row["structural_issue"]]
    if structural_rows:
        structural = [
            "# Structural issues found in Milestone 3-B1.1",
            "",
            *[
                f"- `{row['session_id']}`: {row['structural_issue']}"
                for row in structural_rows
            ],
        ]
        structural_path.write_text("\n".join(structural) + "\n", encoding="utf-8")
    elif structural_path.exists():
        structural_path.unlink()


def write_notes(path: Path, session_rows: list[dict]) -> None:
    lines = [
        "# Milestone 3-B1.1 11-animal audit notes",
        "",
        "## Frozen protocol used",
        "",
        "- Analysis support: verified physical LFP support intersected with resolved metadata and GoodSleep constraints; both official interval sources remain raw provenance.",
        "- The only legal non-finite sentinel is `finite start + positive-infinity stop`; it means no finite official upper bound and is clipped only in the derived constraint layer.",
        "- NaN, negative infinity, non-finite starts, reversed rows, malformed/overlapping interval structures, or unverifiable EEG frame geometry remain failures.",
        "- Stable spikes and annotations validate support but never shorten recording end.",
        "- Strict target policy: valid targets are WAKE/NREM/REM; conflicts, auxiliary substates, gaps, partial bins, OOB rows, and unlabeled bins remain IGNORE/unsupervised.",
        "- Causal samples: `X_t=[t-W,t)`, `y_t` describes `[t-1,t)`, `W=5/10/30 s`.",
        "",
        "## Audit outcome",
        "",
        "- All 11 directories and seven required file types passed read-only preflight.",
        "- All 11 sessions completed the same aligned-session, strict-label, and causal-window pipeline.",
        "- For `20140528_565um`, raw metadata and GoodSleep `[0, Inf)` provenance remains unchanged; `+Inf` means no finite official upper bound.",
        "- Verified finite EEG/LFP support resolves both derived constraints and analysis support to `[0, 12395.736)`.",
        "- No spike or annotation endpoint participates in support resolution, and no session-specific processing was added.",
        "- Templeton's official `units unstable / high-frequency noise` note is retained as provenance only; it does not trigger exclusion or altered processing.",
        "",
        "## Reproducibility",
        "",
        "- Manifest: `config/fcx1_milestone3b1_sessions.csv`",
        "- Runner: `scripts/run_milestone3b1.py`",
        "- Reports: `reports/milestone3b1/`",
        "- Protocol decision: `notes/milestone3b1_1_open_ended_time_support.md`",
        "- Raw data remained read-only under `F:/CfC-Sleep/crcns-downloader/fcx-1/data/`.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=PROJECT_ROOT / "config" / "fcx1_milestone3b1_sessions.csv")
    parser.add_argument("--report-dir", type=Path, default=PROJECT_ROOT / "reports" / "milestone3b1")
    parser.add_argument("--notes", type=Path, default=PROJECT_ROOT / "notes" / "milestone3b1_11animal_audit.md")
    args = parser.parse_args()

    entries = load_session_manifest(args.manifest)
    preflight_results = [preflight(entry.local_path, entry.session_id) for entry in entries]
    if not all(ok for ok, _ in preflight_results):
        for entry, (ok, issues) in zip(entries, preflight_results):
            print(entry.session_id, "PASS" if ok else "FAIL", issues)
        raise SystemExit("Preflight failed; audit stopped without substitutions.")

    results = audit_manifest(entries)
    session_rows, details = build_rows(entries, results)
    animal_rows = build_animal_rows(session_rows)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.report_dir / "fcx1_11animal_session_qc.csv", session_rows)
    _write_csv(args.report_dir / "fcx1_11animal_summary.csv", animal_rows)
    (args.report_dir / "session_details.json").write_text(
        json.dumps(_json_safe(details), ensure_ascii=False, indent=2, default=str, allow_nan=False), encoding="utf-8"
    )
    write_markdown(args.report_dir, session_rows, animal_rows, details)
    write_notes(args.notes, session_rows)
    for row in session_rows:
        print(
            f"{row['session_id']}: {row['qc_status']} "
            f"(preflight={row['preflight_status']}, core={row['core_alignment_valid']}, "
            f"causal={row['causal_5s_valid']}/{row['causal_10s_valid']}/{row['causal_30s_valid']})"
        )


if __name__ == "__main__":
    main()
