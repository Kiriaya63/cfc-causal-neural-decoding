# Milestone 3-B: pilot deep QC and full-data availability

M3-A has been accepted by the user. M3-B is incomplete: only 5 of 27 release sessions are locally extracted. Animal identities for missing sessions remain unknown pending source verification.

All results below describe the pilot only. IGNORE is excluded supervision time, not a valid sleep class. Animal totals sum session durations; units are per-session counts, not distinct neurons across days.

## Out-of-bounds fields

| Session | Field | Role | Rows |
|---|---|---|---:|
| BWRat17_121712 | MATimePairFormat | auxiliary_substate | 1 |
| BWRat17_121712 | WakeInterruptionTimePairFormat | auxiliary_substate | 1 |
| BWRat18_020513 | MATimePairFormat | auxiliary_substate | 29 |
| BWRat18_020513 | WakeInterruptionTimePairFormat | auxiliary_substate | 22 |
| BWRat19_032513 | MATimePairFormat | auxiliary_substate | 29 |
| BWRat19_032513 | WakeInterruptionTimePairFormat | auxiliary_substate | 25 |
| BWRat20_101013 | MATimePairFormat | auxiliary_substate | 16 |
| BWRat20_101013 | WakeInterruptionTimePairFormat | auxiliary_substate | 10 |

Counts refer to source rows, not unique episodes or seconds. Core target fields are Wake/REM/SWSPacket; Sleep/WakeSleep are broad-state/episode validation; MA/WakeInterruption are auxiliary.

## Exact conflict intervals

Half-open seconds; combinations include broad SLEEP as context. Only bins marked conflicting by the unchanged strict policy are listed.

| Session | Active annotations | Start | Stop | Seconds |
|---|---|---:|---:|---:|
| BWRat18_020513 | WAKE+MA | 3644.0 | 3653.0 | 9.0 |
| BWRat18_020513 | WAKE+WakeInterruption | 3712.0 | 3793.0 | 81.0 |
| Splinter_020915 | WAKE+WakeInterruption | 17349.0 | 17424.0 | 75.0 |
| Splinter_020915 | WAKE+MA | 17432.0 | 17443.0 | 11.0 |

## Animal summary

| Animal | Sessions | Support s | WAKE | NREM | REM | IGNORE | Units/session | Missing class |
|---|---:|---:|---:|---:|---:|---:|---|---|
| BWRat17 | 1 | 6059.4 | 2426 | 952 | 103 | 2578 | [50] | [] |
| BWRat18 | 1 | 7591.0 | 2012 | 4158 | 611 | 810 | [40] | [] |
| BWRat19 | 1 | 3928.8 | 453 | 1087 | 227 | 2161 | [61] | [] |
| BWRat20 | 1 | 13364.3 | 705 | 1942 | 654 | 10063 | [22] | [] |
| Splinter | 1 | 23487.5 | 3852 | 8336 | 1064 | 10235 | [51] | [] |
