"""Read-only diagnostics for the three M3-B2 structural failures.

This script deliberately does not import or alter the alignment/audit pipeline.  It
reads raw provenance and signal geometry, writes diagnostic-only reports, and does
not change any session QC status.
"""

from __future__ import annotations

import csv
import json
import math
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.io import loadmat


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "fcx1_milestone3b2_sessions.csv"
OUT = ROOT / "reports" / "milestone3b2_1"
DINO_SESSIONS = ("Dino_061914_ACC", "Dino_061914_mPFC")
JENN_SESSIONS = ("20140526_277um", "20140527_421um", "20140528_565um")
CANDIDATE_CLOCKS_HZ = (1250, 2500, 5000, 10000, 20000)
ON_GRID_TOLERANCE_TICKS = 1e-6


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _fmt_number(value: float | int) -> str:
    if isinstance(value, int):
        return str(value)
    if math.isinf(value):
        return "Inf" if value > 0 else "-Inf"
    if math.isnan(value):
        return "NaN"
    return f"{value:.12g}"


def _fmt_intervals(intervals: np.ndarray) -> str:
    rows = ", ".join(
        f"[{_fmt_number(float(start))}, {_fmt_number(float(stop))})"
        for start, stop in intervals
    )
    return f"[{rows}]"


def _read_manifest() -> list[dict[str, str]]:
    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 27 or len({row["session_id"] for row in rows}) != 27:
        raise RuntimeError("Expected the frozen 27-session manifest.")
    return rows


def _xml_rates_and_channels(session_dir: Path, session_id: str) -> tuple[int, float, float]:
    root = ET.parse(session_dir / f"{session_id}.xml").getroot()
    return (
        int(root.findtext("acquisitionSystem/nChannels")),
        float(root.findtext("acquisitionSystem/samplingRate")),
        float(root.findtext("fieldPotentials/lfpSamplingRate")),
    )


def _raw_metadata(session_dir: Path, session_id: str) -> tuple[dict, np.ndarray]:
    bmd = loadmat(
        session_dir / f"{session_id}_BasicMetaData.mat", simplify_cells=True
    )["bmd"]
    intervals = np.asarray(bmd["RecordingFileIntervals"], dtype=np.float64).reshape(-1, 2)
    return bmd, intervals


def _raw_good_sleep(session_dir: Path, session_id: str) -> np.ndarray:
    value = loadmat(
        session_dir / f"{session_id}_GoodSleepInterval.mat", simplify_cells=True
    )["GoodSleepInterval"]["timePairFormat"]
    return np.asarray(value, dtype=np.float64).reshape(-1, 2)


def _load_raw_spike_trains(session_dir: Path, session_id: str) -> list[np.ndarray]:
    raw = loadmat(
        session_dir / f"{session_id}_SStable.mat",
        simplify_cells=False,
        squeeze_me=False,
        struct_as_record=False,
        variable_names=["S_CellFormat"],
    )
    return [
        np.asarray(value, dtype=np.float64).reshape(-1, order="F")
        for value in np.asarray(raw["S_CellFormat"], dtype=object).ravel(order="F")
    ]


def _frame_diagnostics(rows: list[dict[str, str]]) -> tuple[list[dict], dict]:
    diagnostics: list[dict] = []
    release = {
        "zero_duration_sessions": [],
        "reversed_interval_sessions": [],
        "nonzero_remainder_sessions": [],
        "remainder_ge_frame_width_sessions": [],
    }
    for manifest_row in rows:
        session_id = manifest_row["session_id"]
        session_dir = Path(manifest_row["local_path"])
        bmd, intervals = _raw_metadata(session_dir, session_id)
        n_channels, xml_acq_hz, lfp_hz = _xml_rates_and_channels(session_dir, session_id)
        file_size = (session_dir / f"{session_id}.eeg").stat().st_size
        bytes_per_channel_sample = 2
        frame_width = n_channels * bytes_per_channel_sample
        complete_frames, remainder = divmod(file_size, frame_width)
        zero_rows = np.flatnonzero(intervals[:, 0] == intervals[:, 1]).tolist()
        reversed_rows = np.flatnonzero(intervals[:, 1] < intervals[:, 0]).tolist()
        if zero_rows:
            release["zero_duration_sessions"].append(
                {"session_id": session_id, "row_indices_zero_based": zero_rows}
            )
        if reversed_rows:
            release["reversed_interval_sessions"].append(
                {"session_id": session_id, "row_indices_zero_based": reversed_rows}
            )
        if remainder:
            release["nonzero_remainder_sessions"].append(
                {
                    "session_id": session_id,
                    "remainder_bytes": remainder,
                    "frame_width_bytes": frame_width,
                }
            )
        if remainder >= frame_width:
            release["remainder_ge_frame_width_sessions"].append(session_id)

        if session_id not in DINO_SESSIONS:
            continue
        good_sleep = _raw_good_sleep(session_dir, session_id)
        zero_index = zero_rows[0]
        nonempty = intervals[intervals[:, 1] > intervals[:, 0]]
        continuous_after_empty_removed = bool(
            nonempty.size
            and np.allclose(nonempty[1:, 0], nonempty[:-1, 1], rtol=0, atol=1e-12)
        )
        prefix_bytes = complete_frames * frame_width
        mmap = np.memmap(
            session_dir / f"{session_id}.eeg",
            dtype=np.dtype("<i2"),
            mode="r",
            shape=(complete_frames, n_channels),
            order="C",
        )
        probe_indices = sorted({0, complete_frames // 2, complete_frames - 1})
        probes = [
            {
                "frame_index": int(index),
                "channel_count": int(mmap[index].size),
                "min_int16": int(mmap[index].min()),
                "max_int16": int(mmap[index].max()),
            }
            for index in probe_indices
        ]
        del mmap
        diagnostics.append(
            {
                "session_id": session_id,
                "raw_recording_file_intervals": _fmt_intervals(intervals),
                "zero_duration_row_index_zero_based": zero_index,
                "previous_row": _fmt_intervals(intervals[zero_index - 1 : zero_index]),
                "zero_duration_row": _fmt_intervals(intervals[zero_index : zero_index + 1]),
                "next_row": _fmt_intervals(intervals[zero_index + 1 : zero_index + 2]),
                "raw_good_sleep_interval": _fmt_intervals(good_sleep),
                "metadata_nominal_end_s": float(np.max(intervals[:, 1])),
                "good_sleep_end_s": float(np.max(good_sleep[:, 1])),
                "xml_acquisition_rate_hz": xml_acq_hz,
                "lfp_sample_rate_hz": lfp_hz,
                "eeg_byte_size": file_size,
                "channel_count": n_channels,
                "bytes_per_channel_sample": bytes_per_channel_sample,
                "frame_width_bytes": frame_width,
                "complete_frame_count": complete_frames,
                "complete_prefix_bytes": prefix_bytes,
                "remainder_bytes": remainder,
                "remainder_less_than_one_frame": remainder < frame_width,
                "complete_frame_duration_s": complete_frames / lfp_hz,
                "nonempty_interval_union": _fmt_intervals(nonempty),
                "nonempty_rows_touch_continuously": continuous_after_empty_removed,
                "probe_frames": _json(probes),
                "tail_localization_statement": (
                    "Maximal complete prefix ends at byte complete_prefix_bytes; the remaining "
                    "bytes are physically the file suffix. Flat int16 has no internal frame markers, "
                    "so absence of a prior insertion/deletion cannot be proven from this file alone."
                ),
                "mat_acquisition_rate_hz": float(bmd["Par"]["SampleRate"]),
            }
        )
    return diagnostics, release


def _decimal_resolution(values: np.ndarray) -> dict:
    if values.size == 0:
        return {"decimal_places_needed": 0, "decimal_quantum_s": None}
    scale = max(1.0, float(np.max(np.abs(values))))
    tolerance_s = 5e-13 * scale
    for places in range(0, 11):
        rounded = np.round(values, places)
        if float(np.max(np.abs(values - rounded))) <= tolerance_s:
            return {
                "decimal_places_needed": places,
                "decimal_quantum_s": 10.0 ** (-places),
            }
    return {"decimal_places_needed": ">10", "decimal_quantum_s": None}


def _residual_summary(
    values: np.ndarray, trains: list[np.ndarray], frequency_hz: int
) -> dict:
    residuals = np.abs(values * frequency_hz - np.rint(values * frequency_hz))
    on_grid = residuals <= ON_GRID_TOLERANCE_TICKS
    quantiles = np.quantile(residuals, [0, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 1])
    bins = np.asarray([0, 1e-9, 1e-6, 0.125, 0.25, 0.375, 0.500000000001])
    hist, _ = np.histogram(residuals, bins=bins)
    per_unit_off_grid = [
        int(
            np.count_nonzero(
                np.abs(train * frequency_hz - np.rint(train * frequency_hz))
                > ON_GRID_TOLERANCE_TICKS
            )
        )
        for train in trains
    ]
    return {
        "candidate_frequency_hz": frequency_hz,
        "units_total": len(trains),
        "units_all_on_grid": int(sum(count == 0 for count in per_unit_off_grid)),
        "units_with_off_grid": int(sum(count > 0 for count in per_unit_off_grid)),
        "total_spikes": int(values.size),
        "on_grid_count": int(np.count_nonzero(on_grid)),
        "off_grid_count": int(np.count_nonzero(~on_grid)),
        "off_grid_fraction": float(np.mean(~on_grid)),
        "max_tick_error": float(np.max(residuals)) if values.size else 0.0,
        "median_tick_error": float(np.median(residuals)) if values.size else 0.0,
        "residual_q0_ticks": float(quantiles[0]),
        "residual_q25_ticks": float(quantiles[1]),
        "residual_q50_ticks": float(quantiles[2]),
        "residual_q75_ticks": float(quantiles[3]),
        "residual_q90_ticks": float(quantiles[4]),
        "residual_q95_ticks": float(quantiles[5]),
        "residual_q99_ticks": float(quantiles[6]),
        "residual_q100_ticks": float(quantiles[7]),
        "residual_histogram_tick_bins": _json(
            {
                "[0,1e-9]": int(hist[0]),
                "(1e-9,1e-6]": int(hist[1]),
                "(1e-6,0.125]": int(hist[2]),
                "(0.125,0.25]": int(hist[3]),
                "(0.25,0.375]": int(hist[4]),
                "(0.375,0.5]": int(hist[5]),
            }
        ),
    }


def _jenn_diagnostics(rows: list[dict[str, str]]) -> tuple[list[dict], dict]:
    by_id = {row["session_id"]: row for row in rows}
    output_rows: list[dict] = []
    integrity: dict[str, dict] = {}
    for session_id in JENN_SESSIONS:
        session_dir = Path(by_id[session_id]["local_path"])
        bmd, metadata_intervals = _raw_metadata(session_dir, session_id)
        n_channels, xml_acq_hz, lfp_hz = _xml_rates_and_channels(session_dir, session_id)
        mat_acq_hz = float(bmd["Par"]["SampleRate"])
        eeg_size = (session_dir / f"{session_id}.eeg").stat().st_size
        frames, remainder = divmod(eeg_size, n_channels * 2)
        support_end_s = frames / lfp_hz
        trains = _load_raw_spike_trains(session_dir, session_id)
        values = np.concatenate(trains) if trains else np.empty(0, dtype=np.float64)
        decimal = _decimal_resolution(values)
        within_unit_duplicate_count = int(
            sum(np.count_nonzero(np.diff(train) == 0) for train in trains)
        )
        global_unique, global_counts = np.unique(values, return_counts=True)
        cross_train_extra_duplicates = int(np.sum(global_counts - 1))
        per_unit_monotonic = [bool(np.all(np.diff(train) >= 0)) for train in trains]
        out_mask = (values < 0) | (values >= support_end_s)
        integrity[session_id] = {
            "n_units": len(trains),
            "total_spikes": int(values.size),
            "xml_acquisition_rate_hz": xml_acq_hz,
            "metadata_acquisition_rate_hz": mat_acq_hz,
            "lfp_rate_hz": lfp_hz,
            "metadata_intervals": _fmt_intervals(metadata_intervals),
            "verified_lfp_support_s": [0.0, support_end_s],
            "eeg_remainder_bytes": remainder,
            "all_timestamps_finite": bool(np.all(np.isfinite(values))),
            "all_timestamps_nonnegative": bool(np.all(values >= 0)),
            "all_units_monotonic_nondecreasing": bool(all(per_unit_monotonic)),
            "nonmonotonic_unit_numbers_one_based": [
                index + 1 for index, okay in enumerate(per_unit_monotonic) if not okay
            ],
            "inside_support_count": int(np.count_nonzero(~out_mask)),
            "outside_support_count": int(np.count_nonzero(out_mask)),
            "outside_support_fraction": float(np.mean(out_mask)),
            "first_spike_s": float(np.min(values)) if values.size else None,
            "last_spike_s": float(np.max(values)) if values.size else None,
            "outside_support_min_s": (
                float(np.min(values[out_mask])) if np.any(out_mask) else None
            ),
            "outside_support_max_s": (
                float(np.max(values[out_mask])) if np.any(out_mask) else None
            ),
            "within_unit_duplicate_event_count": within_unit_duplicate_count,
            "global_extra_duplicate_timestamp_count": cross_train_extra_duplicates,
            "global_unique_timestamp_count": int(global_unique.size),
            **decimal,
        }
        session_clock_rows = []
        for frequency_hz in CANDIDATE_CLOCKS_HZ:
            clock_row = {
                    "session_id": session_id,
                    "xml_acquisition_rate_hz": xml_acq_hz,
                    "metadata_acquisition_rate_hz": mat_acq_hz,
                    "lfp_rate_hz": lfp_hz,
                    "spike_decimal_places_needed": decimal["decimal_places_needed"],
                    "spike_decimal_quantum_s": decimal["decimal_quantum_s"],
                    "on_grid_tolerance_ticks": ON_GRID_TOLERANCE_TICKS,
                    **_residual_summary(values, trains, frequency_hz),
                }
            output_rows.append(clock_row)
            session_clock_rows.append(clock_row)
        exact_candidate_grids = [
            row["candidate_frequency_hz"]
            for row in session_clock_rows
            if row["off_grid_count"] == 0
        ]
        integrity[session_id]["lowest_tested_exact_grid_hz"] = (
            min(exact_candidate_grids) if exact_candidate_grids else None
        )
        integrity[session_id]["lowest_tested_exact_grid_period_s"] = (
            1.0 / min(exact_candidate_grids) if exact_candidate_grids else None
        )
    return output_rows, integrity


def _write_csv(path: Path, rows: list[dict]) -> None:
    fields = list(rows[0])
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _markdown_report(
    dino_rows: list[dict], release: dict, jenn_rows: list[dict], integrity: dict
) -> str:
    dino_table = [
        "| session | zero row context | bytes / frame | complete frames | remainder | duration from complete prefix |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in dino_rows:
        context = f'{row["previous_row"]} → {row["zero_duration_row"]} → {row["next_row"]}'
        dino_table.append(
            f'| {row["session_id"]} | {context} | {row["eeg_byte_size"]} / '
            f'{row["frame_width_bytes"]} | {row["complete_frame_count"]} | '
            f'{row["remainder_bytes"]} | {row["complete_frame_duration_s"]:.9f} s |'
        )

    clock_table = [
        "| session | XML / MAT acquisition | LFP | candidate grid | on-grid | off-grid fraction | median / max error (ticks) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in jenn_rows:
        clock_table.append(
            f'| {row["session_id"]} | {row["xml_acquisition_rate_hz"]:g} / '
            f'{row["metadata_acquisition_rate_hz"]:g} Hz | {row["lfp_rate_hz"]:g} Hz | '
            f'{row["candidate_frequency_hz"]} Hz | {row["on_grid_count"]}/'
            f'{row["total_spikes"]} | {row["off_grid_fraction"]:.9g} | '
            f'{row["median_tick_error"]:.9g} / {row["max_tick_error"]:.9g} |'
        )

    integrity_lines = []
    for session_id in JENN_SESSIONS:
        item = integrity[session_id]
        integrity_lines.append(
            f'- `{session_id}`: {item["n_units"]} units, {item["total_spikes"]} spikes; '
            f'finite={item["all_timestamps_finite"]}, nonnegative={item["all_timestamps_nonnegative"]}, '
            f'per-unit sorted={item["all_units_monotonic_nondecreasing"]}; '
            f'spike range=[{item["first_spike_s"]}, {item["last_spike_s"]}] s, '
            f'verified analysis/LFP support=[0, {item["verified_lfp_support_s"][1]}) s, '
            f'outside support={item["outside_support_count"]}; '
            f'within-unit duplicate events={item["within_unit_duplicate_event_count"]}, '
            f'global extra equal-time events={item["global_extra_duplicate_timestamp_count"]}; '
            f'decimal resolution requires {item["decimal_places_needed"]} places '
            f'(display quantum {item["decimal_quantum_s"]} s); lowest tested exact event grid='
            f'{item["lowest_tested_exact_grid_hz"]} Hz '
            f'({item["lowest_tested_exact_grid_period_s"]} s).'
        )

    release_text = (
        f'- `start == stop`: {_json(release["zero_duration_sessions"])}\n'
        f'- `stop < start`: {_json(release["reversed_interval_sessions"])}\n'
        f'- non-zero EEG frame remainder: {_json(release["nonzero_remainder_sessions"])}\n'
        f'- remainder `>= frame_width`: {_json(release["remainder_ge_frame_width_sessions"])}'
    )

    return f"""# M3-B2.1 structural-failure diagnosis

Diagnostic scope only. Raw files were read-only. The pipeline, time-support/label/causal protocols, and existing FAIL/WARN decisions were not changed. The 27-session audit was not rerun.

## A. Dino interval and EEG frame evidence

Both failing Dino releases carry the same official metadata intervals:

`{dino_rows[0]['raw_recording_file_intervals']}`

Their official `GoodSleepInterval.timePairFormat` is `{dino_rows[0]['raw_good_sleep_interval']}`. The nominal metadata and GoodSleep ends are both `{dino_rows[0]['metadata_nominal_end_s']:.9f} s`.

{chr(10).join(dino_table)}

The zero row is `[10149.85, 10149.85)`. Under half-open interval mathematics this is an empty set: it contributes zero duration and no points to a union. If it is omitted only from a hypothetical **derived** union while raw provenance remains untouched, the four non-empty rows touch exactly and cover `[0, 17519.55)` continuously. This is a diagnosis, not an implemented rule.

For each EEG, `6,219,440,250 = 21,899,437 × 284 + 142` bytes. Thus 142 bytes are less than one 284-byte multichannel frame and the maximal complete prefix reshapes exactly as `(21,899,437 frames, 142 channels)` of little-endian int16. Probes at the first, middle, and last complete frames all read as 142-channel int16 rows (details are retained in the CSV).

The 142 bytes after that maximal prefix are physically a file-tail suffix. However, this raw format has no frame markers or checksums per frame, so file length alone cannot prove that no insertion/deletion occurred earlier. We found no positive byte-geometry evidence of an internal displacement; the strongest defensible claim is that the complete prefix is geometrically continuous and the only directly observable incompleteness is the 142-byte tail.

### Release-wide interval/frame scan

{release_text}

Therefore, within the 27-session release, only these two sessions have a zero-duration `RecordingFileIntervals` row, only these two have a non-zero EEG remainder, no session has `stop < start`, and no remainder can or does reach one frame width.

## B. Jenn spike clock evidence

Residual is `abs(timestamp × candidate_frequency − nearest_integer)`, measured in candidate-clock ticks. “On-grid” uses the frozen loader tolerance `<= {ON_GRID_TOLERANCE_TICKS:g}` tick. Full quantiles and histograms are in `jenn_spike_clock_diagnostics.csv`.

{chr(10).join(clock_table)}

### Timestamp integrity

{chr(10).join(integrity_lines)}

For `20140526_277um`, every raw stable spike is on the 20 kHz grid within the existing numerical tolerance, while a substantial fraction is off the 1250 Hz grid. The timestamps are represented to five decimal places, consistent with 50 µs ticks. Support comparisons above are diagnostics only and were not used to infer the recording boundary.

The two adjacent Jenn sessions provide the within-animal comparison: their declared XML and BasicMetaData acquisition rates and their empirical grid results are listed in the table, rather than inferred from file-name proximity.

## C. Is the acquisition-grid invariant required for causal binning?

No mathematical dependency was found in the binning operation. `bin_stable_spikes` uses sorted raw timestamps and two `numpy.searchsorted(..., side="left")` calls per half-open bin. For `[start, stop)`, the count is the index of the first event `>= stop` minus the index of the first event `>= start`. It needs finite timestamps, temporal ordering, and the raw event time in seconds; it does not multiply event times by the acquisition rate.

The current grid check occurs earlier in `load_stable_spikes`: it multiplies each timestamp by `metadata.acquisition_sample_rate_hz`, measures distance to the nearest integer, and raises above `1e-6` tick. Its roles under the current frozen code are:

- **Correctness invariant for causal bin assignment:** no. Half-open bin membership remains mathematically defined for off-grid real-valued timestamps.
- **Integrity diagnostic:** yes. It detects disagreement between event timestamps and the declared acquisition clock.
- **Historical assumption encoded as a fatal guard:** yes. The loader currently assumes every stable spike time was generated on the metadata/XML acquisition grid, so this diagnostic presently blocks the pipeline even though the downstream counting formula does not require it.

This classification is analysis only; the guard was not changed or bypassed.

## D. Candidate dataset-wide extensions for human decision

The evidence supports narrowly scoped, session-agnostic candidates, but none was implemented:

1. **Empty provenance row:** preserve raw rows; allow only exact finite `[a,a)` rows to contribute the empty set to a derived interval union, while all non-empty rows must still be finite/open-ended-valid, sorted, non-overlapping, and otherwise satisfy the frozen constraints.
2. **Incomplete final frame:** preserve the raw EEG; when `0 < remainder < frame_width`, optionally define physical signal support from the maximal complete-frame prefix and record the discarded suffix byte count. This requires an explicit scientific decision because byte geometry cannot independently rule out an earlier displacement.
3. **Event-clock provenance:** separate declared acquisition rate from observed timestamp-grid diagnostics. One possible minimum rule is to retain finite/nonnegative/sorted/support checks as fatal, retain declared-grid disagreement as explicit provenance/QC, and allow causal half-open binning from exact raw seconds only if a reproducible event clock is established dataset-wide. For `20140526`, the candidate is 20 kHz; this is not a session-ID branch and no timestamp would be altered.

These are three independent protocol decisions; accepting one does not imply accepting the others. Existing three FAIL states remain unchanged pending human review.
"""


def main() -> None:
    rows = _read_manifest()
    dino_rows, release = _frame_diagnostics(rows)
    jenn_rows, integrity = _jenn_diagnostics(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    _write_csv(OUT / "dino_frame_diagnostics.csv", dino_rows)
    _write_csv(OUT / "jenn_spike_clock_diagnostics.csv", jenn_rows)
    (OUT / "structural_failure_diagnosis.md").write_text(
        _markdown_report(dino_rows, release, jenn_rows, integrity), encoding="utf-8"
    )
    print(f"Wrote diagnostics to {OUT}")


if __name__ == "__main__":
    main()
