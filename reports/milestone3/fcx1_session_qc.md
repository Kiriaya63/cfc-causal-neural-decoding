# Milestone 3 fcx-1 session QC

Status rules: PASS means core alignment and causal samples pass with no warnings; WARN means the pipeline runs but explicit duration, annotation, coverage, channel, or tail findings remain; FAIL means reliable aligned causal samples could not be established.

Summary: PASS=0, WARN=5, FAIL=0.

| session | animal | status | analysis s | channels | units | spikes | WAKE | NREM | REM | IGNORE | OOB | conflict | duration mismatch |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BWRat17_121712 | BWRat17 | WARN | 6059.4 | 72 | 50 | 345203 | 2426 | 952 | 103 | 2578 | 2 | 0 | False |
| BWRat18_020513 | BWRat18 | WARN | 7591.0 | 135 | 40 | 222046 | 2012 | 4158 | 611 | 810 | 51 | 90 | True |
| BWRat19_032513 | BWRat19 | WARN | 3928.8 | 135 | 61 | 562797 | 453 | 1087 | 227 | 2161 | 54 | 0 | False |
| BWRat20_101013 | BWRat20 | WARN | 13364.3 | 72 | 22 | 1045719 | 705 | 1942 | 654 | 10063 | 26 | 0 | False |
| Splinter_020915 | Splinter | WARN | 23487.5 | 54 | 51 | 2132698 | 3852 | 8336 | 1064 | 10235 | 0 | 86 | False |

All intervals use half-open `[start, stop)` analysis semantics. BasicMetaData, LFP, GoodSleep, and candidate support intervals are retained in each JSON report. Invalid annotation rows are retained as field/value findings; no invalid interval is silently repaired.
