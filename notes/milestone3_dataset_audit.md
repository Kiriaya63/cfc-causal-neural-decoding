# Milestone 3 dataset audit

## Scope and decision rules

- Audited 5 sessions from 5 manifest animal identities.
- Animal IDs are the animal component of each released session ID and were corroborated by `BasicMetaData.basepath`; no animal identity was guessed from physiology.
- Candidate analysis support is actual LFP support intersected with `GoodSleepInterval`.
- Spikes and primary WAKE/SLEEP annotations validate that support but never shorten it.
- `BasicMetaData.RecordingFileIntervals` remains unchanged provenance; disagreements are `duration_mismatch` findings.
- PASS/WARN/FAIL follows the deterministic rules in `reports/milestone3/fcx1_session_qc.md`.

## Observed facts

- Uniform pipeline outcome: 5/5 sessions produced aligned causal samples; FAIL=0.
- Analysis duration ranges from 3928.8 s to 23487.5 s (5.98x range).
- Stable-unit count ranges from 22 to 61; therefore a fixed assumption of 50 units does not generalize.
- Total spike count ranges from 222,046 to 2,132,698. Per-session count distributions and shank unit distributions are stored in the CSV/JSON reports.
- Observed anatomy labels across sessions: ACC, CeA, MotorCtx, OFC, dhipp, piriformL3. Recommended LFP/theta channel numbers and their anatomy vary by session, so BWRat17 channel numbers cannot be reused globally.
- IGNORE coverage ranges from 10.7% to 75.3% across 54,429 complete 1-s bins.
- Sessions with out-of-support annotation rows: BWRat17_121712 (2), BWRat18_020513 (51), BWRat19_032513 (54), BWRat20_101013 (26).
- Sessions with strict-label conflicts: BWRat18_020513 (90 s), Splinter_020915 (86 s).
- Sessions with `duration_mismatch`: BWRat18_020513.
- Every non-failed session passed label arithmetic and at least one sampled strict causal boundary check for each of 5, 10, and 30 s contexts.

## Assumptions supported across these sessions

- LFP sample time is `sample_index / lfp_sample_rate_hz`, with a shared zero-second origin for aligned modalities.
- Stable spike timestamps and released sleep intervals can be checked on the same seconds axis.
- Metadata-selected LFP and theta channels exist and have anatomy labels in all five audited sessions.
- The same strict WAKE/NREM/REM/IGNORE and past-only window code runs without a session-specific branch.

## Assumptions that must not be retained

- Recording end cannot always be taken from `BasicMetaData.RecordingFileIntervals` (BWRat18 is the verified counterexample).
- Stable-unit count, shank distribution, channel number, and anatomical region are not constant across sessions.
- Annotation quality is not uniform: out-of-support rows and strict-label conflicts occur in different sessions.
- High valid-label coverage cannot be assumed; unlabeled and fine-state-gap bins remain explicit IGNORE.

## Unresolved design questions (not decided in Milestone 3)

- How variable neuron sets will be represented (fixed-N, population rate, shank aggregation, or neuron encoder/pooling).
- Which cross-animal anatomical/channel policy will define future multimodal inputs.
- Whether and how raw LFP will be causally filtered, downsampled, or transformed into features.
- The future animal-level train/validation/test protocol and training-only normalization policy.

## Reproducibility artifacts

- Manifest: `config/fcx1_milestone3_sessions.csv`
- Aggregate reports: `reports/milestone3/fcx1_session_qc.csv` and `.md`
- Individual structured reports: `reports/milestone3/sessions/*_qc.json`
- Audit runner: `scripts/run_milestone3.py`
