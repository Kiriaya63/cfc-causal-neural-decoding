# M3-B2.2 outcome

All 27 release sessions were freshly audited under the same approved pipeline. Historical M3-B2 reports are preserved.

Preflight: 27/27 PASS. Final status: {"PASS": 0, "WARN": 27, "FAIL": 0}.

The prior 24 successful sessions retain identical support, labels, OOB, conflicts, unit counts and 5/10/30 s sample counts. Frozen label, spike-binning and causal modules match the previous SHA256 snapshot.

| previous FAIL session | current | units | WAKE/NREM/REM/IGNORE seconds | supervision | core OOB | conflict seconds | 5/10/30 sample counts |
|---|---|---:|---|---:|---:|---:|---|
| Dino_061914_ACC | WARN | 52 | 630/1665/299/14925 | 14.80678121% | 0 | 0 | 2594/2594/2594 |
| Dino_061914_mPFC | WARN | 60 | 630/1597/296/14996 | 14.40150694% | 0 | 0 | 2523/2523/2523 |
| 20140526_277um | WARN | 62 | 2141/2754/181/8496 | 37.40053050% | 0 | 0 | 5076/5076/5076 |

## Dino_061914_ACC

- candidate_analysis_intervals_s: `[[0.0, 17519.5496]]`
- lfp_frame_diagnostics: `{"raw_file_size_bytes": 6219440250, "frame_width_bytes": 284, "complete_frame_count": 21899437, "trailing_incomplete_frame_bytes": 142, "complete_prefix_end_s": 17519.5496, "official_end_s": 17519.55, "official_endpoint_source": "BasicMetaData.RecordingFileIntervals", "endpoint_difference_s": 0.0004000000008090865, "incomplete_tail_verified": true}`
- spike_clock_diagnostics: `{"declared_acquisition_rate_hz": 20000.0, "declared_grid_mismatch": false, "declared_off_grid_count": 0, "total_spikes": 1116078, "declared_max_tick_error": 5.960464477539063e-08, "observed_event_clock_hz": 20000.0, "observed_clock_method": "lowest_fully_matching_tested_candidate_at_1e-6_tick_tolerance", "candidate_results": [{"frequency_hz": 1250.0, "off_grid_count": 1046116, "max_tick_error": 0.5}, {"frequency_hz": 2500.0, "off_grid_count": 976058, "max_tick_error": 0.5}, {"frequency_hz": 5000.0, "off_grid_count": 836208, "max_tick_error": 0.5}, {"frequency_hz": 10000.0, "off_grid_count": 556970, "max_tick_error": 0.5}, {"frequency_hz": 20000.0, "off_grid_count": 0, "max_tick_error": 5.960464477539063e-08}]}`
- annotation_oob_by_field: `{"REMEpisodeTimePairFormat": 0, "REMTimePairFormat": 0, "SWSEpisodeTimePairFormat": 0, "SWSPacketTimePairFormat": 0, "MATimePairFormat": 12, "WakeInterruptionTimePairFormat": 13, "WakeTimePairFormat": 0, "SleepTimePairFormat": 0, "WakeSleepTimePairFormat": 0}`
- conflict_types: `{}`
- exact_conflict_intervals: `[]`

## Dino_061914_mPFC

- candidate_analysis_intervals_s: `[[0.0, 17519.5496]]`
- lfp_frame_diagnostics: `{"raw_file_size_bytes": 6219440250, "frame_width_bytes": 284, "complete_frame_count": 21899437, "trailing_incomplete_frame_bytes": 142, "complete_prefix_end_s": 17519.5496, "official_end_s": 17519.55, "official_endpoint_source": "BasicMetaData.RecordingFileIntervals", "endpoint_difference_s": 0.0004000000008090865, "incomplete_tail_verified": true}`
- spike_clock_diagnostics: `{"declared_acquisition_rate_hz": 20000.0, "declared_grid_mismatch": false, "declared_off_grid_count": 0, "total_spikes": 1774204, "declared_max_tick_error": 5.960464477539063e-08, "observed_event_clock_hz": 20000.0, "observed_clock_method": "lowest_fully_matching_tested_candidate_at_1e-6_tick_tolerance", "candidate_results": [{"frequency_hz": 1250.0, "off_grid_count": 1662691, "max_tick_error": 0.5}, {"frequency_hz": 2500.0, "off_grid_count": 1551967, "max_tick_error": 0.5}, {"frequency_hz": 5000.0, "off_grid_count": 1330778, "max_tick_error": 0.5}, {"frequency_hz": 10000.0, "off_grid_count": 886262, "max_tick_error": 0.5}, {"frequency_hz": 20000.0, "off_grid_count": 0, "max_tick_error": 5.960464477539063e-08}]}`
- annotation_oob_by_field: `{"REMEpisodeTimePairFormat": 0, "REMTimePairFormat": 0, "SWSEpisodeTimePairFormat": 0, "SWSPacketTimePairFormat": 0, "MATimePairFormat": 15, "WakeInterruptionTimePairFormat": 18, "WakeTimePairFormat": 0, "SleepTimePairFormat": 0, "WakeSleepTimePairFormat": 0}`
- conflict_types: `{}`
- exact_conflict_intervals: `[]`

## 20140526_277um

- candidate_analysis_intervals_s: `[[0.0, 13572.36]]`
- lfp_frame_diagnostics: `{"raw_file_size_bytes": 3257366400, "frame_width_bytes": 192, "complete_frame_count": 16965450, "trailing_incomplete_frame_bytes": 0, "complete_prefix_end_s": 13572.36, "official_end_s": null, "official_endpoint_source": null, "endpoint_difference_s": null, "incomplete_tail_verified": false}`
- spike_clock_diagnostics: `{"declared_acquisition_rate_hz": 1250.0, "declared_grid_mismatch": true, "declared_off_grid_count": 2077020, "total_spikes": 2214209, "declared_max_tick_error": 0.5, "observed_event_clock_hz": 20000.0, "observed_clock_method": "lowest_fully_matching_tested_candidate_at_1e-6_tick_tolerance", "candidate_results": [{"frequency_hz": 1250.0, "off_grid_count": 2077020, "max_tick_error": 0.5}, {"frequency_hz": 2500.0, "off_grid_count": 1940080, "max_tick_error": 0.5}, {"frequency_hz": 5000.0, "off_grid_count": 1667044, "max_tick_error": 0.5}, {"frequency_hz": 10000.0, "off_grid_count": 1107506, "max_tick_error": 0.5}, {"frequency_hz": 20000.0, "off_grid_count": 0, "max_tick_error": 2.9802322387695312e-08}]}`
- annotation_oob_by_field: `{"REMEpisodeTimePairFormat": 0, "REMTimePairFormat": 0, "SWSEpisodeTimePairFormat": 0, "SWSPacketTimePairFormat": 0, "MATimePairFormat": 0, "WakeInterruptionTimePairFormat": 0, "WakeTimePairFormat": 0, "SleepTimePairFormat": 0, "WakeSleepTimePairFormat": 0}`
- conflict_types: `{}`
- exact_conflict_intervals: `[]`

## Global summary

- validated_unit_count: `{"n": 27, "min": 10.0, "median": 36.0, "max": 113.0}`
- valid_supervision: `{"n": 27, "min": 0.1036579704762789, "median": 0.44376210691175866, "max": 0.8932946910815439}`
- core_OOB_count: `0`
- auxiliary_OOB_count: `2224`
- OOB_fields: `{"REMEpisodeTimePairFormat": 0, "REMTimePairFormat": 0, "SWSEpisodeTimePairFormat": 0, "SWSPacketTimePairFormat": 0, "MATimePairFormat": 1118, "WakeInterruptionTimePairFormat": 1106, "WakeTimePairFormat": 0, "SleepTimePairFormat": 0, "WakeSleepTimePairFormat": 0}`
- conflict_types_seconds: `{"WAKE+MA": 358.0, "WAKE+WakeInterruption": 2544.0, "WAKE+SLEEP+WakeInterruption": 110.0, "WAKE+SLEEP": 10.0, "WAKE+SLEEP+MA": 21.0, "WAKE+SLEEP+NREM": 70.0}`
- missing_core_classes: `{"BWRat19_032413": ["REM"]}`
- LFP_anatomies: `{"ACC": 6, "MotorCtx": 3, "mPFC": 14, "OFC": 4}`
- theta_anatomies: `{"dhipp": 3, "piriformL3": 1, "MotorCtx": 2, "ACC": 3, "": 5, "mPFC": 5, "dHipp": 4, "OFC": 4}`
- duration_mismatch_sessions: `["BWRat18_020513", "BWRat20_101513", "Dino_061914_ACC", "Dino_061914_mPFC", "20140526_277um", "20140527_421um", "20140528_565um", "Bogey_012615"]`
- open_ended_sessions: `["20140526_277um", "20140527_421um", "20140528_565um"]`
- protocol_breaking_sessions: `{}`

27 sessions are release entries, not necessarily 27 independent time periods: paired Dino ACC/mPFC releases can share recording time. No neuron identities were matched across sessions. WARN is not exclusion.

The protocol extensions were approved before implementation. Computational completion is assessed from the audit and test record; M4 remains unstarted pending the user’s next instruction.

## Tests and preservation

Ran 44 tests in 99.510s

OK

Original 32 test cases retained plus 12 structural extension tests; the full-release report/hash fixture references the newly approved version. No skipped tests.

Raw preservation check: `{"files_checked": 523, "changed_files": [], "method": "All file sizes/mtime; SHA256 for non-EEG files below 100 MB. EEG was only opened read-only; no full EEG rehash."}`.
