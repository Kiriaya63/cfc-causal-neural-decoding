# CfC strictly causal cross-animal neural decoding

This repository contains the frozen Phase I data and representation pipeline for CRCNS fcx-1: 27 recording sessions from 11 animals. Milestones 1–4 are complete and frozen; model evaluation and Milestone 5 have not started.

The scientific goal is to test when continuous-time inductive biases are useful for strictly causal, cross-animal neural decoding—not simply whether CfC can classify sleep states.

See [`PHASE_I_HANDOFF.md`](PHASE_I_HANDOFF.md) for the co-worker/supervisor handoff and requested review, and [`notes/milestone4_representation_protocol.md`](notes/milestone4_representation_protocol.md) for the frozen representation contract.

## Frozen causal contract

For context lengths `W = 5, 10, 30 s`:

```text
X_t = [t-W, t)
y_t = state on [t-1, t)
```

Future samples, centered/zero-phase processing, and future-derived features are prohibited. Raw data are read-only. Normalization statistics will be fitted only on future M5 training animals.

## Layout

- `src/data/load_metadata.py`: MAT/XML/CSV metadata loader and cross-file checks.
- `src/data/load_lfp.py`: `.eeg` size validation, read-only memory map, and short-window reader.
- `src/data/load_spikes.py`: stable per-unit spike timestamps in seconds.
- `src/data/load_sleep_states.py`: normalized start/stop pairs plus explicit invalid-row reports.
- `src/data/align_session.py`: unified-clock validation report.
- `src/representation/`: causal 50 Hz LFP and spike representations plus the restricted model-facing adapter.
- `src/visualization/plot_multimodal.py`: short-window and full WAKE-to-SLEEP plots.
- `scripts/run_milestone1.py`: command-line entry point.
- `tests/`: 69 regression, causality, integrity, and representation tests.
- `notes/milestone1_data_notes.md`: field, dimension, unit, and interpretation notes.

## Run this session

From this `work` directory:

```powershell
python -B .\scripts\run_milestone1.py F:\CfC-Sleep\crcns-downloader\fcx-1\data\BWRat17_121712
```

The session directory is an argument, not a hard-coded dependency. To run a future fcx-1 session, pass its extracted session folder instead. File names are derived from the folder basename.

## Run integration checks

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
python -B -m unittest discover -s .\tests -v
```

Set `FCX1_SESSION_DIR` to override the test session path.

## Frozen validation result

- 27/27 sessions and 11/11 animals pass through one common pipeline.
- 69/69 tests pass with 0 skipped.
- The raw preservation audit checked 523 files and found no changes.
- No normalization statistics have been fitted.
- Known metadata inconsistencies are retained as provenance and excluded from model inputs.

Machine-readable evidence is in `reports/milestone4/global_summary.json`; the complete trust audit is in `reports/pre_m5_trust_audit/`.

## Historical single-session validation

`BWRat17_121712` has a valid common 0-6059.4 s LFP/spike/WAKE-SLEEP clock. Two released substate rows are outside that range. They remain visible in the raw sleep-state result and alignment report; aligned consumers must request `valid_only=True`.

## Milestone 2

Run the strict causal pipeline with a configurable context:

```powershell
python -B .\scripts\run_milestone2.py F:\CfC-Sleep\crcns-downloader\fcx-1\data\BWRat17_121712 --context 30 --decision-time 2431
```

The causal protocol is in `notes/milestone2_protocol.md`. No normalization, filtering, splitting, or model training is performed.

## Milestone 3

Run the five-session, manifest-driven audit:

```powershell
python -B .\scripts\run_milestone3.py
```

The centralized session list is `config/fcx1_milestone3_sessions.csv`. Outputs are
written to `reports/milestone3/`, with the human-readable dataset audit in
`notes/milestone3_dataset_audit.md`. The audit preserves raw metadata intervals as
provenance and defines candidate analysis support only from actual LFP support and
`GoodSleepInterval`.

## Milestone 4

The frozen M4 protocol defines a 1 Hz decision grid and 50 Hz observation grid, a GoodEEG-only raw waveform, causal role-specific physiological features, population and variable-neuron spike representations, explicit masks, relative elapsed time, cache authentication, and a strict model-input whitelist. See `notes/milestone4_representation_protocol.md`.

## Next: Milestone 5

M5 will freeze animal-level splits, train-only normalization, seeds, model selection, early stopping, metrics, class handling, and comparison fairness before formal benchmarking begins.
