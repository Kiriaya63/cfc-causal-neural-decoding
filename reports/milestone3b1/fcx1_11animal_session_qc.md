# Milestone 3-B1: 11-animal representative-session audit

The frozen M1/M2/M3 pipeline was run unchanged. Raw fcx-1 files were opened read-only. No animal-specific or session-specific processing branch was added.

Result: preflight 11/11 PASS; common pipeline 11/11 valid; PASS=0, WARN=11, FAIL=0.

| animal | session | QC | duration s | units | WAKE | NREM | REM | IGNORE | valid frac | core OOB | aux OOB | conflict s | support pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| BWRat17 | BWRat17_121712 | WARN | 6059.4 | 50 | 2426 | 952 | 103 | 2578 | 0.574517 | 0 | 2 | 0 | metadata_good_sleep_lfp_equal |
| BWRat18 | BWRat18_020513 | WARN | 7591 | 40 | 2012 | 4158 | 611 | 810 | 0.893295 | 0 | 51 | 90 | metadata_differs_good_sleep_matches_lfp |
| BWRat19 | BWRat19_032513 | WARN | 3928.8 | 61 | 453 | 1087 | 227 | 2161 | 0.449847 | 0 | 54 | 0 | metadata_good_sleep_lfp_equal |
| BWRat20 | BWRat20_101013 | WARN | 13364.3 | 22 | 705 | 1942 | 654 | 10063 | 0.247007 | 0 | 26 | 0 | metadata_good_sleep_lfp_equal |
| Splinter | Splinter_020915 | WARN | 23487.5 | 51 | 3852 | 8336 | 1064 | 10235 | 0.564227 | 0 | 0 | 86 | metadata_good_sleep_lfp_equal |
| JennBuzsaki22 | 20140528_565um | WARN | 12395.7 | 33 | 789 | 2746 | 523 | 8337 | 0.32739 | 0 | 0 | 0 | open_ended_metadata_and_good_sleep_resolved_to_lfp |
| Bogey | Bogey_012615 | WARN | 24263.4 | 36 | 3460 | 6519 | 788 | 13496 | 0.443762 | 0 | 0 | 184 | metadata_and_good_sleep_differ_from_lfp |
| BWRat21 | BWRat21_121813 | WARN | 21705.8 | 12 | 6308 | 7669 | 3458 | 4270 | 0.803271 | 0 | 449 | 310 | metadata_good_sleep_lfp_equal |
| Dino | Dino_072314_mPFC | WARN | 10321.1 | 16 | 1644 | 1834 | 610 | 6233 | 0.396086 | 0 | 97 | 713 | metadata_good_sleep_lfp_equal |
| Rizzo | Rizzo_022715 | WARN | 25932.1 | 93 | 4886 | 6514 | 1718 | 12814 | 0.505861 | 0 | 0 | 131 | metadata_good_sleep_lfp_equal |
| Templeton | Templeton_032415 | WARN | 19057.6 | 10 | 4405 | 9199 | 1755 | 3698 | 0.805951 | 0 | 0 | 130 | metadata_good_sleep_lfp_equal |

## Cross-animal facts

- Stable-unit counts are available for 11/11 pipeline-valid sessions: min=10, median=36, max=93.
- Stable-unit distribution: BWRat17=50, BWRat18=40, BWRat19=61, BWRat20=22, Splinter=51, JennBuzsaki22=33, Bogey=36, BWRat21=12, Dino=16, Rizzo=93, Templeton=10.
- WAKE fraction: min=5.275% (BWRat20), median=16.401%, max=40.040% (BWRat17).
- NREM fraction: min=14.532% (BWRat20), median=26.868%, max=54.775% (BWRat18).
- REM fraction: min=1.700% (BWRat17), median=5.779%, max=15.932% (BWRat21).
- IGNORE fraction: min=10.671% (BWRat18), median=49.414%, max=75.299% (BWRat20).
- Valid-supervision fraction: min=24.701% (BWRat20), median=50.586%, max=89.329% (BWRat18).
- Missing core classes: none among pipeline-valid sessions.
- OOB roles: core_target=0, auxiliary_substate=679, broad_state_or_episode=0.
- OOB exact fields: {"MATimePairFormat":279,"WakeInterruptionTimePairFormat":400}.
- Conflict duration by type (seconds): {"WAKE+MA":125.0,"WAKE+SLEEP":1.0,"WAKE+SLEEP+NREM":29.0,"WAKE+SLEEP+WakeInterruption":61.0,"WAKE+WakeInterruption":1428.0}.
- Conflict types first seen in the six newly added sessions relative to the five-session pilot: WAKE+SLEEP, WAKE+SLEEP+NREM, WAKE+SLEEP+WakeInterruption.
- New time-support patterns relative to the pilot: metadata_and_good_sleep_differ_from_lfp, open_ended_metadata_and_good_sleep_resolved_to_lfp.
- Finite-source duration mismatches: BWRat18_020513, Bogey_012615.
- Non-zero origins, disconnected finite analysis supports, and malformed annotation rows: none among all 11 pipeline-valid sessions.
- Core-target annotation OOB: 0 among all 11 pipeline-valid sessions.
- Rizzo contains a 29-second `WAKE+SLEEP+NREM` core-target conflict on `[9981,10010)`; strict policy maps every affected bin to IGNORE.

## Interpretation boundary

`20140528_565um` contains official open-ended `[0, Inf]` values in both `BasicMetaData.RecordingFileIntervals` and `GoodSleepInterval.timePairFormat`. The raw values remain unchanged. Their positive-infinity stops are interpreted as no finite official upper bound, and the derived constraints are clipped to the verified finite EEG/LFP support. No recording end is inferred from spikes or labels.

The full CSV contains support provenance, selected channel anatomy, exact OOB rows, exact conflict intervals, and independent 5/10/30-second past-only checks for every pipeline-valid session.
