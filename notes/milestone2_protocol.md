# Milestone 2 protocol: causal model-ready data pipeline

## Scope

This milestone converts one read-only, aligned fcx-1 session into strict labels and lazy past-only samples. It does not train models, split data, fit normalization statistics, or finalize spectral features.

## One-second base grid and labels

- Full bins are `[0,1), [1,2), ...`; all intervals are half-open `[start,stop)`.
- `BWRat17_121712` supplies 6059 complete bins. The final 6059-6059.4 s tail is reported but cannot be a complete one-second target.
- `WAKE <- WakeTimePairFormat`; `NREM <- SWSPacketTimePairFormat`; `REM <- REMTimePairFormat`.
- `MATimePairFormat`, `WakeInterruptionTimePairFormat`, fine-state gaps, partial-bin boundaries, conflicts, and unlabeled time produce `target_label=IGNORE`, `valid_label=False`, with an explicit `invalid_reason`.
- `SleepTimePairFormat` and `WakeSleepTimePairFormat` are broad-state checks only, never direct NREM targets.
- No priority rule resolves conflicts: conflicting candidates become `IGNORE`.

Coverage for this session: WAKE 2426 s, NREM 952 s, REM 103 s, IGNORE 2578 s. Broad-state-unlabeled time is 2055 s; conflicts are 0 s. WAKE+NREM+REM+IGNORE equals all 6059 complete bins. The unlabeled/conflict counts are diagnostic subsets of IGNORE, not additional classes.

## Causal sample semantics

For decision time `t` and configurable integer context `W` seconds:

`X_t = [t-W,t)`

`y_t = state on [t-1,t)`

No LFP sample with time `>=t`, no spike with time `>=t`, and no future-derived statistic may enter `X_t`. At `t=2431`, `W=30`, the input is `[2401,2431)` and the target is `[2430,2431) -> WAKE`. `[2431,2432)` is broad SLEEP but a fine-state gap, so its strict target is IGNORE, not NREM.

The lightweight index stores session id, decision time, context bounds, target bounds, label, validity, invalid reason, and `target_kind=retrospective_state`. LFP is read lazily only when `get_sample(i)` is called; overlapping LFP windows are not cached as permanent arrays.

## Spike representation

Each bin/unit entry counts events satisfying `start <= spike_time < stop`. Shape is `(6059,50)`, unit is `spikes/bin`, and shank plus `cellIx` identity are retained. A `spikes/s` view is numerically equal only because the bin width is one second. No z-score is applied. Seven spikes in the incomplete 6059-6059.4 s tail are explicitly excluded from the complete-bin matrix.

## LFP representation

Channels are explicit dataset numbers: ACC 13 and dHipp/theta 65 by default. `get_sample` uses the Milestone 1 read-only memory map and returns raw `int16` counts, deterministic microvolt conversion, timestamps, and channel identity for exactly `[t-W,t)`. There is no filtering, downsampling, centered Welch window, or whole-session transform.

## Allowed and forbidden preprocessing

Allowed now: deterministic index-to-seconds conversion, int16-to-volts/microvolts conversion, spike event counting, and clearly marked plotting-only summaries computed wholly inside an already-past window.

Forbidden now: `filtfilt`, zero-phase filters, centered rolling windows, future samples, whole-session z-score, full-session spectral normalization, final bandpower design, and any scaler fit outside future training data. Normalization must later be estimated only from training animals/data; doing it now would leak test-distribution information.

## Known annotation issues

MA `[8145,8155]` and Wake interruption `[6801,6890]` exceed the 6059.4 s recording. They remain in Milestone 1 validation output, contribute an out-of-bounds count of two, and cannot generate a valid bin or sample. Missing labels are not filled.

## Future target interface

Index rows carry `target_kind`, so a later task can extend the target to a future interval such as `(t,t+H]`, with `H=5/10/30 s`, for REM entry, NREM-to-wake transition, or remaining duration. Milestone 2 implements only retrospective current-state classification and performs no transition experiments.

## Causality checks

Tests require `max(lfp_time)<t`, spike-bin stops `<=t`, invariance of a past LFP window after synthetic future perturbation, correct 2431 s label boundaries, exclusion of out-of-range annotations, configurable 5/10/30 s contexts, and continued Milestone 1 regression success.
