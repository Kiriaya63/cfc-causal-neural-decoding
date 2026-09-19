"""Build and audit the approved M4 representations without fitting or training."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data import load_aligned_session, load_lfp_window, load_session_manifest
from representation import (
    DEFAULT_CONFIG,
    MODEL_INPUT_SCHEMA_VERSION,
    RepresentationSessionDataset,
    design_physio_filters,
    design_waveform_filter,
    model_input_schema_hash,
    representation_implementation_hash,
)

MANIFEST = ROOT / "config" / "fcx1_milestone3b2_sessions.csv"
M3_DETAILS = ROOT / "reports" / "milestone3b2_2" / "session_details.json"
OUT = ROOT / "reports" / "milestone4"
CACHE = ROOT / "cache" / "milestone4"


def safe(value):
    if isinstance(value, np.ndarray): return safe(value.tolist())
    if isinstance(value, np.generic): return safe(value.item())
    if isinstance(value, Path): return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return "NaN" if math.isnan(value) else ("Infinity" if value > 0 else "-Infinity")
    if isinstance(value, dict): return {key: safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)): return [safe(item) for item in value]
    return value


def raw_snapshot(entries):
    result = {}
    for entry in entries:
        for path in entry.local_path.iterdir():
            if not path.is_file(): continue
            stat = path.stat()
            item = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
            if path.suffix.lower() != ".eeg" and stat.st_size < 100_000_000:
                item["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            result[str(path)] = item
    return result


def identity_branches(entries):
    identities = {e.session_id for e in entries} | {e.animal_id for e in entries}
    findings = []
    for path in (ROOT / "src" / "representation").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.IfExp, ast.Match)):
                strings = {
                    child.value for child in ast.walk(node)
                    if isinstance(child, ast.Constant) and isinstance(child.value, str)
                }
                if strings & identities:
                    findings.append({"file": path.name, "line": node.lineno, "identities": sorted(strings & identities)})
    return findings


def audit_one(entry, inherited, waveform_design, physio_design):
    try:
        session = load_aligned_session(entry.local_path)
        cache_dir = None
        contexts = {}
        sample_shapes = {}
        for width in (5, 10, 30):
            dataset = RepresentationSessionDataset(session, width, CACHE)
            cache_dir = dataset.cache_directory
            checked = []
            for index in sorted({0, len(dataset)//2, len(dataset)-1}) if len(dataset) else []:
                sample = dataset.get_sample(index)
                expected = width * DEFAULT_CONFIG.observation_rate_hz
                okay = (
                    sample.observation_intervals_s.shape == (expected, 2)
                    and sample.lfp_waveform_50hz.shape == (expected, 1)
                    and sample.lfp_physio_50hz.shape == (expected, 4)
                    and sample.spike_population_rate_50hz.shape == (expected, 1)
                    and sample.spike_set_counts_50hz.shape == (expected, session.spikes.n_units)
                    and sample.observation_intervals_s[0, 0] == sample.decision_time_s - width
                    and sample.observation_intervals_s[-1, 1] == sample.decision_time_s
                    and np.all(sample.observation_intervals_s[:, 1] <= sample.decision_time_s)
                    and np.all(sample.causal_validity_mask)
                    and np.all(np.isfinite(sample.lfp_waveform_50hz))
                    and np.all(np.isfinite(sample.lfp_physio_50hz))
                    and np.all(np.isfinite(sample.spike_population_rate_50hz))
                )
                checked.append(bool(okay))
            contexts[str(width)] = {
                "m2_valid_samples": len(dataset.m2_valid_rows),
                "representation_valid_samples": len(dataset.rows),
                "representation_invalid_samples": len(dataset.invalid_rows),
                "invalid_reason": "context_intersects_lfp_feature_startup" if dataset.invalid_rows else None,
                "checked_samples": len(checked),
                "causal_check_passed": bool(checked and all(checked)),
            }
            sample_shapes[str(width)] = {
                "steps": width * 50,
                "lfp_waveform": [width * 50, 1],
                "lfp_physio": [width * 50, 4],
                "spike_population_rate": [width * 50, 1],
                "spike_set_counts": [width * 50, session.spikes.n_units],
                "neuron_mask": [session.spikes.n_units],
                "causal_validity_mask": [width * 50, 4],
            }
        metadata = dataset.cache_metadata
        anomalies = []
        if metadata["role_sharing_present"]: anomalies.append("functional_roles_share_physical_channel_provenance")
        if any(value is None or value == "" for value in metadata["channel_anatomy"]):
            anomalies.append("selected_role_anatomy_missing")
        if any(value["representation_invalid_samples"] for value in contexts.values()):
            anomalies.append("startup_transient_masks_early_m2_samples")
        if inherited["qc"]["qc_status"] == "WARN": anomalies.append("inherited_m3_qc_warning")
        causal = all(value["causal_check_passed"] for value in contexts.values())
        status = "WARN" if causal and anomalies else ("PASS" if causal else "FAIL")
        return {
            "animal_id": entry.animal_id,
            "session_id": entry.session_id,
            "qc_status": status,
            "analysis_duration_s": session.report.common_end_s,
            "input_lfp_rate_hz": session.metadata.lfp_sample_rate_hz,
            "observation_rate_hz": DEFAULT_CONFIG.observation_rate_hz,
            "decimation_factor": DEFAULT_CONFIG.decimation_factor,
            "observation_count": metadata["observation_count"],
            "unrepresented_tail_s": metadata["unrepresented_tail_s"],
            "selected_lfp_role_channels_one_based": metadata["channels_one_based"],
            "selected_lfp_role_anatomy": metadata["channel_anatomy"],
            "role_channel_mapping": metadata["role_channel_mapping"],
            "physio_feature_source_roles": metadata["physio_feature_source_roles"],
            "anatomy_provenance_conflicts": metadata["anatomy_provenance_conflicts"],
            "channel_role_mask": [True],
            "channel_role_anomalies": anomalies,
            "waveform_fir_numtaps": waveform_design.numtaps,
            "waveform_group_delay_s": waveform_design.group_delay_s,
            "waveform_full_history_warmup_s": waveform_design.full_history_warmup_s,
            "waveform_first_valid_right_edge_s": metadata["waveform_first_valid_right_edge_s"],
            "physio_first_valid_right_edge_s": metadata["physio_first_valid_right_edge_s"],
            "physio_bands": list(physio_design.names),
            "stable_unit_count": session.spikes.n_units,
            "spike_branch_a_session_shape": [metadata["observation_count"], 1],
            "spike_branch_b_session_shape": [metadata["observation_count"], session.spikes.n_units],
            "modality_mask": [True, True, True, True],
            "contexts": contexts,
            "sample_shapes": sample_shapes,
            "finite_waveform": metadata["finite_waveform"],
            "finite_physio": metadata["finite_physio"],
            "causal_check_passed": causal,
            "normalization_statistics_fit": metadata["normalization_statistics_fit"],
            "cache_directory": str(cache_dir),
            "protocol_version": DEFAULT_CONFIG.protocol_version,
            "protocol_hash": DEFAULT_CONFIG.protocol_hash,
            "error": None,
        }
    except Exception as error:
        return {
            "animal_id": entry.animal_id, "session_id": entry.session_id,
            "qc_status": "FAIL", "error": f"{type(error).__name__}: {error}",
        }


def write_csv(rows):
    keys = list(dict.fromkeys(key for row in rows for key in row))
    with (OUT / "representation_audit.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(safe(value), ensure_ascii=False) if isinstance(value, (dict, list, tuple)) else safe(value) for key, value in row.items()})


def choose_figure_sessions(rows):
    good = [row for row in rows if row["qc_status"] != "FAIL"]
    ordered = sorted(good, key=lambda row: (row["stable_unit_count"], row["session_id"]))
    low = ordered[0]
    median_units = float(np.median([row["stable_unit_count"] for row in good]))
    median = min(good, key=lambda row: (abs(row["stable_unit_count"] - median_units), row["session_id"]))
    upper = [row for row in good if row["stable_unit_count"] >= np.quantile([x["stable_unit_count"] for x in good], .75)]
    used_anatomy = {low["selected_lfp_role_anatomy"][0], median["selected_lfp_role_anatomy"][0]}
    high = max(upper, key=lambda row: (row["selected_lfp_role_anatomy"][0] not in used_anatomy, row["stable_unit_count"]))
    chosen = [low, median, high]
    covered = {row["selected_lfp_role_anatomy"][0] for row in chosen}
    extra = [row for row in good if row["selected_lfp_role_anatomy"][0] not in covered]
    if extra:
        chosen.append(min(extra, key=lambda row: (abs(row["stable_unit_count"] - median_units), row["session_id"])))
    return chosen


def plot_sample(entry, row):
    session = load_aligned_session(entry.local_path)
    dataset = RepresentationSessionDataset(session, 10, CACHE)
    sample = dataset.get_sample(len(dataset)//2)
    decision = sample.decision_time_s
    raw = load_lfp_window(session.metadata, decision - 2, decision,
        tuple(sample.lfp_channels_one_based), support_end_s=session.report.common_end_s)
    fig, axes = plt.subplots(5, 1, figsize=(13, 12), sharex=False)
    raw_values = raw.counts if raw.counts.ndim == 2 else raw.counts[:, None]
    for channel in range(raw_values.shape[1]): axes[0].plot(raw.time_s, raw_values[:, channel], lw=.45, label=sample.lfp_channel_roles[channel])
    axes[0].set_ylabel("raw ADC"); axes[0].legend(loc="upper left", ncol=2)
    for channel in range(sample.lfp_waveform_50hz.shape[1]): axes[1].plot(sample.observation_right_edges_s, sample.lfp_waveform_50hz[:, channel], lw=.7, label=sample.lfp_channel_roles[channel])
    axes[1].set_ylabel("causal 50 Hz")
    for band, name in enumerate(("delta","theta","sigma","broadband")):
        axes[2].plot(sample.observation_right_edges_s, sample.lfp_physio_50hz[:, band], lw=.8, label=name)
    axes[2].set_ylabel("role-sourced\nlog power"); axes[2].legend(loc="upper left", ncol=4)
    axes[3].plot(sample.observation_right_edges_s, sample.spike_population_rate_50hz[:, 0], lw=.75)
    axes[3].set_ylabel("population Hz")
    axes[4].imshow(sample.spike_set_counts_50hz.T, aspect="auto", origin="lower", interpolation="nearest",
        extent=[decision-10, decision, 0.5, session.spikes.n_units+.5], cmap="Greys")
    axes[4].set_ylabel("local unit"); axes[4].set_xlabel("session time (s)")
    for axis in axes:
        axis.axvspan(decision-1, decision, color="#f5b642", alpha=.15)
        axis.axvline(decision, color="red", ls="--", lw=1)
        axis.set_xlim((decision-2, decision) if axis is axes[0] else (decision-10, decision+.05))
    fig.suptitle(f"{entry.session_id} | units={session.spikes.n_units} | target [t-1,t)={sample.target_label} | t={decision:g}s\nAll representation intervals end at or before the red decision boundary")
    fig.tight_layout()
    path = OUT / "figures" / f"{entry.session_id}_causal_sanity.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return str(path)


def main():
    entries = load_session_manifest(MANIFEST)
    if len(entries) != 27 or len({entry.animal_id for entry in entries}) != 11:
        raise RuntimeError("M4 requires the frozen 27-session / 11-animal cohort.")
    branches = identity_branches(entries)
    if branches: raise RuntimeError(f"Identity-specific representation branches: {branches}")
    OUT.mkdir(parents=True, exist_ok=True)
    before = raw_snapshot(entries)
    inherited = json.loads(M3_DETAILS.read_text(encoding="utf-8"))
    waveform = design_waveform_filter()
    physio = design_physio_filters(waveform)
    design_report = {
        "config": DEFAULT_CONFIG.to_dict(), "protocol_hash": DEFAULT_CONFIG.protocol_hash,
        "cache_array_implementation_hash": representation_implementation_hash(),
        "model_input_schema_version": MODEL_INPUT_SCHEMA_VERSION,
        "model_input_schema_hash": model_input_schema_hash(),
        "waveform": {key: safe(value) for key, value in waveform.__dict__.items() if key != "taps"},
        "waveform_coefficients": waveform.taps.tolist(),
        "physio": {
            "names": physio.names, "sos": [value.tolist() for value in physio.sos],
            "settling_steps": physio.settling_steps,
            "power_window_steps": physio.power_window_steps,
            "first_valid_observation_step": physio.first_valid_observation_step,
        },
    }
    (OUT / "filter_design.json").write_text(json.dumps(safe(design_report), indent=2), encoding="utf-8")
    rows = []
    for index, entry in enumerate(entries, 1):
        row = audit_one(entry, inherited[entry.session_id], waveform, physio)
        rows.append(row)
        print(f"[{index:02d}/27] {entry.session_id}: {row['qc_status']}", flush=True)
    after = raw_snapshot(entries)
    changed = [path for path in before.keys() | after.keys() if before.get(path) != after.get(path)]
    preservation = {"files_checked": len(before), "changed_files": changed,
        "method": "size/mtime for all; SHA256 for non-EEG files under 100 MB; raw files opened read-only"}
    (OUT / "raw_preservation_check.json").write_text(json.dumps(preservation, indent=2), encoding="utf-8")
    if changed: raise RuntimeError(f"Raw files changed: {changed}")
    write_csv(rows)
    shapes = {row["session_id"]: row.get("sample_shapes") for row in rows}
    (OUT / "representation_shapes.json").write_text(json.dumps(shapes, indent=2), encoding="utf-8")
    status = {name: sum(row["qc_status"] == name for row in rows) for name in ("PASS","WARN","FAIL")}
    total_invalid = {str(width): sum(row.get("contexts",{}).get(str(width),{}).get("representation_invalid_samples",0) for row in rows) for width in (5,10,30)}
    total_m2 = {str(width): sum(row.get("contexts",{}).get(str(width),{}).get("m2_valid_samples",0) for row in rows) for width in (5,10,30)}
    summary = {
        "sessions": len(rows), "animals": len({row["animal_id"] for row in rows}),
        "status_counts": status, "protocol_version": DEFAULT_CONFIG.protocol_version,
        "protocol_hash": DEFAULT_CONFIG.protocol_hash, "identity_specific_branches": branches,
        "cache_array_implementation_hash": representation_implementation_hash(),
        "model_input_schema_version": MODEL_INPUT_SCHEMA_VERSION,
        "model_input_schema_hash": model_input_schema_hash(),
        "stable_unit_min_median_max": [min(row["stable_unit_count"] for row in rows if row["qc_status"]!="FAIL"), float(np.median([row["stable_unit_count"] for row in rows if row["qc_status"]!="FAIL"])), max(row["stable_unit_count"] for row in rows if row["qc_status"]!="FAIL")],
        "m2_valid_samples_by_context": total_m2,
        "representation_invalid_samples_by_context": total_invalid,
        "representation_invalid_fraction_by_context": {key: total_invalid[key]/total_m2[key] for key in total_m2},
        "normalization_statistics_fit": False, "raw_preservation": preservation,
        "unresolved_structural_issues": [row for row in rows if row["qc_status"] == "FAIL"],
    }
    figures = []
    by_id = {entry.session_id: entry for entry in entries}
    for row in choose_figure_sessions(rows):
        figures.append(plot_sample(by_id[row["session_id"]], row))
    summary["sanity_figures"] = figures
    (OUT / "global_summary.json").write_text(json.dumps(safe(summary), indent=2), encoding="utf-8")
    lines = ["# Milestone 4 representation audit", "", f"27-session result: `{status}`.", "",
        "| session | animal | status | LFP roles | anatomy | units | 5 s valid/invalid | 10 s valid/invalid | 30 s valid/invalid | anomalies |",
        "|---|---|---|---|---|---:|---:|---:|---:|---|"]
    for row in rows:
        contexts = row.get("contexts", {})
        fmt = lambda width: f"{contexts[str(width)]['representation_valid_samples']}/{contexts[str(width)]['representation_invalid_samples']}" if contexts else "NA"
        lines.append(f"| {row['session_id']} | {row['animal_id']} | {row['qc_status']} | {row.get('selected_lfp_role_channels_one_based')} | {row.get('selected_lfp_role_anatomy')} | {row.get('stable_unit_count')} | {fmt(5)} | {fmt(10)} | {fmt(30)} | {row.get('channel_role_anomalies')} |")
    lines.extend(["", "All sample intervals are explicit half-open 20-ms bins. The raw waveform is GoodEEG-only. Physiological features use their declared functional-role sources; shared physical channels are read once. WARN includes inherited M3 QC, startup masks, role sharing provenance, or missing anatomy provenance; it does not imply exclusion.", "", f"Representation-invalid/M2-valid totals: `{total_invalid}` of `{total_m2}`."])
    (OUT / "representation_audit.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    if summary["unresolved_structural_issues"]:
        (OUT / "structural_issues.md").write_text("# M4 structural issues\n\n"+json.dumps(summary["unresolved_structural_issues"],ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__": main()
