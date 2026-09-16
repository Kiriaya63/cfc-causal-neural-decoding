# Independently reconstructable timeline alignment examples

Each row starts from an integer-second raw annotation bin. The LFP sample is read directly from the little-endian interleaved EEG at `byte_offset = (sample_index*n_channels + channel_zero_based)*2`; spikes are counted directly from raw `S_CellFormat` with left-inclusive/right-exclusive searches.

| session | target | interval s | LFP sample index | raw byte offset | direct GoodEEG int16 count | raw stable spikes in interval | raw annotation evidence | parser target |
|---|---|---:|---:|---:|---:|---:|---|---|
| BWRat17_121712 | WAKE | [30,31) | 37500 | 5400024 | 921 | 63 | WakeTimePairFormat rows [0] | WAKE |
| BWRat17_121712 | NREM | [2432,2433) | 3040000 | 437760024 | 21 | 80 | SleepTimePairFormat rows [0]; SWSPacketTimePairFormat rows [0] | NREM |
| BWRat17_121712 | REM | [3397,3398) | 4246250 | 611460024 | 854 | 77 | SleepTimePairFormat rows [0]; REMTimePairFormat rows [0] | REM |
| BWRat18_020513 | WAKE | [30,31) | 37500 | 10125116 | -341 | 29 | WakeTimePairFormat rows [0] | WAKE |
| BWRat18_020513 | NREM | [1288,1289) | 1610000 | 434700116 | 310 | 51 | SleepTimePairFormat rows [0]; SWSPacketTimePairFormat rows [0] | NREM |
| BWRat18_020513 | REM | [2043,2044) | 2553750 | 689512616 | -236 | 3 | SleepTimePairFormat rows [0]; REMTimePairFormat rows [0] | REM |
| Dino_061914_ACC | WAKE | [10138,10139) | 12672500 | 3598990036 | 261 | 67 | WakeTimePairFormat rows [0] | WAKE |
| Dino_061914_ACC | NREM | [10769,10770) | 13461250 | 3822995036 | -526 | 82 | SleepTimePairFormat rows [0]; SWSPacketTimePairFormat rows [0] | NREM |
| Dino_061914_ACC | REM | [11231,11232) | 14038750 | 3987005036 | -253 | 60 | SleepTimePairFormat rows [0]; REMTimePairFormat rows [0] | REM |
| 20140526_277um | WAKE | [3129,3130) | 3911250 | 750960064 | 355 | 145 | WakeTimePairFormat rows [0] | WAKE |
| 20140526_277um | NREM | [4317,4318) | 5396250 | 1036080064 | -71 | 147 | SleepTimePairFormat rows [0]; SWSPacketTimePairFormat rows [0] | NREM |
| 20140526_277um | REM | [5581,5582) | 6976250 | 1339440064 | -967 | 123 | SleepTimePairFormat rows [0]; REMTimePairFormat rows [0] | REM |
| Splinter_020915 | WAKE | [6005,6006) | 7506250 | 810675084 | 484 | 133 | WakeTimePairFormat rows [0] | WAKE |
| Splinter_020915 | NREM | [7017,7018) | 8771250 | 947295084 | 524 | 42 | SleepTimePairFormat rows [0]; SWSPacketTimePairFormat rows [0] | NREM |
| Splinter_020915 | REM | [8128,8129) | 10160000 | 1097280084 | 275 | 185 | SleepTimePairFormat rows [0]; REMTimePairFormat rows [0] | REM |
| Templeton_032415 | WAKE | [30,31) | 37500 | 7275052 | -636 | 3 | WakeTimePairFormat rows [0] | WAKE |
| Templeton_032415 | NREM | [2344,2345) | 2930000 | 568420052 | -135 | 6 | SleepTimePairFormat rows [0]; SWSPacketTimePairFormat rows [0] | NREM |
| Templeton_032415 | REM | [3511,3512) | 4388750 | 851417552 | 184 | 8 | SleepTimePairFormat rows [0]; REMTimePairFormat rows [0] | REM |

All examples use origin 0 s. LFP index `i` maps to `i/1250` s; spike timestamps and annotation endpoints are already seconds from that origin. No implicit offset was required. RecordingFileIntervals were also checked release-wide: nonempty rows are ordered and touch/continue according to their raw provenance; the two approved zero-duration rows contribute the empty set.
