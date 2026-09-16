# Unresolved structural issues

No protocol modifications or exclusions were made.

## Dino_061914_ACC

metadata: ValueError: RecordingFileIntervals contains stop <= start.

- secondary_structural_evidence: `["EEG frame remainder is nonzero"]`
- raw_metadata_recording_intervals_s: `[[0.0, 3508.1], [3508.1, 7807.4], [7807.4, 10149.849999999999], [10149.849999999999, 10149.849999999999], [10149.849999999999, 17519.55]]`
- raw_good_sleep_intervals_s: `[[0.0, 17519.55]]`
- eeg_file_size_bytes: `6219440250`
- eeg_frame_width_bytes: `284`
- eeg_remainder_bytes: `142`
- invalid_metadata_rows: `[{"row_index": 3, "interval_s": [10149.849999999999, 10149.849999999999]}]`
- acquisition_sample_rate_hz: `20000.0`
- mat_acquisition_sample_rate_hz: `20000`
- raw_spike_grid_violations: `[]`

Reproduce from work/src: `python -m data.align_session "F:\CfC-Sleep\crcns-downloader\fcx-1\data\Dino_061914_ACC"`

## Dino_061914_mPFC

metadata: ValueError: RecordingFileIntervals contains stop <= start.

- secondary_structural_evidence: `["EEG frame remainder is nonzero"]`
- raw_metadata_recording_intervals_s: `[[0.0, 3508.1], [3508.1, 7807.4], [7807.4, 10149.849999999999], [10149.849999999999, 10149.849999999999], [10149.849999999999, 17519.55]]`
- raw_good_sleep_intervals_s: `[[0.0, 17519.55]]`
- eeg_file_size_bytes: `6219440250`
- eeg_frame_width_bytes: `284`
- eeg_remainder_bytes: `142`
- invalid_metadata_rows: `[{"row_index": 3, "interval_s": [10149.849999999999, 10149.849999999999]}]`
- acquisition_sample_rate_hz: `20000.0`
- mat_acquisition_sample_rate_hz: `20000`
- raw_spike_grid_violations: `[]`

Reproduce from work/src: `python -m data.align_session "F:\CfC-Sleep\crcns-downloader\fcx-1\data\Dino_061914_mPFC"`

## 20140526_277um

spike: ValueError: Stable unit 1 is not on the 1250 Hz acquisition grid; maximum tick error is 0.5.

- secondary_structural_evidence: `[]`
- raw_metadata_recording_intervals_s: `[[0.0, "Infinity"]]`
- raw_good_sleep_intervals_s: `[[0.0, "Infinity"]]`
- eeg_file_size_bytes: `3257366400`
- eeg_frame_width_bytes: `192`
- eeg_remainder_bytes: `0`
- invalid_metadata_rows: `[]`
- acquisition_sample_rate_hz: `1250.0`
- mat_acquisition_sample_rate_hz: `1250`
- raw_spike_grid_violations: `[{"unit_one_based": 1, "off_grid_count": 4854, "examples_s": [5.68395, 13.38375, 13.47865, 24.32115, 25.74335], "max_tick_error": 0.5}, {"unit_one_based": 2, "off_grid_count": 5101, "examples_s": [18.35275, 18.36635, 76.91185, 77.1953, 111.2827], "max_tick_error": 0.5}, {"unit_one_based": 3, "off_grid_count": 9052, "examples_s": [0.60455, 1.8455, 1.84975, 1.8673, 1.8732], "max_tick_error": 0.5}, {"unit_one_based": 4, "off_grid_count": 8540, "examples_s": [1.3187, 3.32075, 3.3338, 3.3693, 3.82675], "max_tick_error": 0.5}, {"unit_one_based": 5, "off_grid_count": 9971, "examples_s": [10.12115, 10.9701, 15.63115, 18.33665, 18.3994], "max_tick_error": 0.5}, {"unit_one_based": 6, "off_grid_count": 19009, "examples_s": [1.34585, 1.3485, 1.3539, 1.35675, 1.3612], "max_tick_error": 0.5}, {"unit_one_based": 7, "off_grid_count": 35142, "examples_s": [0.699, 2.1876, 2.49415, 3.5514, 6.45575], "max_tick_error": 0.5}, {"unit_one_based": 8, "off_grid_count": 18574, "examples_s": [1.8119, 7.13745, 7.3981, 12.1143, 14.11145], "max_tick_error": 0.5}, {"unit_one_based": 9, "off_grid_count": 121166, "examples_s": [6.69075, 6.98805, 13.1907, 13.29545, 16.7378], "max_tick_error": 0.5}, {"unit_one_based": 10, "off_grid_count": 32954, "examples_s": [0.70945, 0.7295, 0.7373, 2.16865, 2.21035], "max_tick_error": 0.5}, {"unit_one_based": 11, "off_grid_count": 58652, "examples_s": [1.26465, 1.5113, 2.17035, 2.36125, 2.3637], "max_tick_error": 0.5}, {"unit_one_based": 12, "off_grid_count": 38598, "examples_s": [0.73315, 0.96385, 1.3887, 2.2898, 2.81995], "max_tick_error": 0.5}, {"unit_one_based": 13, "off_grid_count": 4047, "examples_s": [6.84905, 64.74945, 75.667, 103.7148, 134.83665], "max_tick_error": 0.5}, {"unit_one_based": 14, "off_grid_count": 50584, "examples_s": [0.04355, 0.2541, 0.94485, 1.0182, 1.1931], "max_tick_error": 0.5}, {"unit_one_based": 15, "off_grid_count": 11204, "examples_s": [11.3773, 16.8374, 67.545, 73.33305, 77.1767], "max_tick_error": 0.5}, {"unit_one_based": 16, "off_grid_count": 8496, "examples_s": [13.2561, 19.40915, 111.30975, 125.0854, 182.90235], "max_tick_error": 0.5}, {"unit_one_based": 17, "off_grid_count": 20068, "examples_s": [1.17635, 1.21965, 1.46265, 1.98085, 3.18065], "max_tick_error": 0.5}, {"unit_one_based": 18, "off_grid_count": 18747, "examples_s": [13.41055, 30.1013, 31.2346, 85.42945, 86.219], "max_tick_error": 0.5}, {"unit_one_based": 19, "off_grid_count": 25443, "examples_s": [0.13735, 0.4131, 0.67775, 0.7276, 0.743], "max_tick_error": 0.5}, {"unit_one_based": 20, "off_grid_count": 6082, "examples_s": [0.18885, 1.48905, 1.58695, 4.0158, 8.03345], "max_tick_error": 0.5}, {"unit_one_based": 21, "off_grid_count": 78410, "examples_s": [0.15895, 0.4738, 1.0075, 2.4494, 2.6437], "max_tick_error": 0.5}, {"unit_one_based": 22, "off_grid_count": 9911, "examples_s": [0.1025, 0.6345, 0.6506, 2.23605, 2.6062], "max_tick_error": 0.5}, {"unit_one_based": 23, "off_grid_count": 22835, "examples_s": [0.52665, 0.7482, 0.81625, 0.9481, 1.23405], "max_tick_error": 0.5}, {"unit_one_based": 24, "off_grid_count": 3231, "examples_s": [0.66365, 0.66795, 2.2727, 17.94575, 19.33445], "max_tick_error": 0.5}, {"unit_one_based": 25, "off_grid_count": 5103, "examples_s": [0.1342, 0.5795, 2.9513, 5.28075, 7.5411], "max_tick_error": 0.5}, {"unit_one_based": 26, "off_grid_count": 3690, "examples_s": [7.3965, 11.91995, 20.3306, 63.6825, 94.24285], "max_tick_error": 0.5}, {"unit_one_based": 27, "off_grid_count": 7723, "examples_s": [0.6959, 0.7326, 0.8969, 2.6795, 4.0143], "max_tick_error": 0.5}, {"unit_one_based": 28, "off_grid_count": 6588, "examples_s": [0.2809, 3.9893, 11.3005, 11.43595, 11.4954], "max_tick_error": 0.5}, {"unit_one_based": 29, "off_grid_count": 5883, "examples_s": [8.4353, 17.22245, 139.9326, 159.05905, 185.92605], "max_tick_error": 0.5}, {"unit_one_based": 30, "off_grid_count": 18005, "examples_s": [0.20155, 0.9975, 1.8477, 2.31925, 2.62255], "max_tick_error": 0.5}, {"unit_one_based": 31, "off_grid_count": 6052, "examples_s": [0.6851, 6.66715, 8.90765, 8.92555, 10.17265], "max_tick_error": 0.5}, {"unit_one_based": 32, "off_grid_count": 137528, "examples_s": [0.44385, 0.76575, 1.1893, 1.9225, 2.1987], "max_tick_error": 0.5}, {"unit_one_based": 33, "off_grid_count": 21754, "examples_s": [0.20755, 1.1687, 1.76615, 1.7735, 2.7649], "max_tick_error": 0.5}, {"unit_one_based": 34, "off_grid_count": 7565, "examples_s": [1.1055, 3.32655, 4.77335, 6.1487, 6.15565], "max_tick_error": 0.5}, {"unit_one_based": 35, "off_grid_count": 132463, "examples_s": [0.02315, 0.17125, 0.1883, 0.2353, 0.5646], "max_tick_error": 0.5}, {"unit_one_based": 36, "off_grid_count": 15132, "examples_s": [10.007, 17.40735, 18.6941, 22.87375, 24.3581], "max_tick_error": 0.5}, {"unit_one_based": 37, "off_grid_count": 18103, "examples_s": [0.3356, 2.80925, 2.9106, 2.93535, 4.0099], "max_tick_error": 0.5}, {"unit_one_based": 38, "off_grid_count": 25343, "examples_s": [0.1404, 0.24205, 0.2819, 0.32365, 0.40215], "max_tick_error": 0.5}, {"unit_one_based": 39, "off_grid_count": 11433, "examples_s": [2.2627, 2.30755, 2.4877, 8.38995, 8.70195], "max_tick_error": 0.5}, {"unit_one_based": 40, "off_grid_count": 15900, "examples_s": [0.6561, 0.7281, 2.53045, 2.6644, 2.91805], "max_tick_error": 0.5}, {"unit_one_based": 41, "off_grid_count": 46900, "examples_s": [0.0117, 0.11515, 0.1354, 0.15195, 0.19865], "max_tick_error": 0.5}, {"unit_one_based": 42, "off_grid_count": 7407, "examples_s": [0.66865, 0.71045, 0.76325, 1.91515, 2.18535], "max_tick_error": 0.5}, {"unit_one_based": 43, "off_grid_count": 27683, "examples_s": [0.48975, 0.49795, 0.5417, 0.5835, 0.7954], "max_tick_error": 0.5}, {"unit_one_based": 44, "off_grid_count": 27099, "examples_s": [0.2051, 1.93655, 1.95265, 3.59495, 3.64185], "max_tick_error": 0.5}, {"unit_one_based": 45, "off_grid_count": 15435, "examples_s": [0.54085, 0.5813, 0.5919, 0.59695, 0.6049], "max_tick_error": 0.5}, {"unit_one_based": 46, "off_grid_count": 5672, "examples_s": [3.46145, 3.4674, 6.18325, 7.2441, 12.8325], "max_tick_error": 0.5}, {"unit_one_based": 47, "off_grid_count": 12711, "examples_s": [1.30885, 1.32805, 3.3129, 8.59455, 11.4979], "max_tick_error": 0.5}, {"unit_one_based": 48, "off_grid_count": 30439, "examples_s": [0.0186, 0.1434, 0.6441, 0.8182, 1.418], "max_tick_error": 0.5}, {"unit_one_based": 49, "off_grid_count": 5089, "examples_s": [3.4646, 27.15335, 31.27565, 35.46585, 39.369], "max_tick_error": 0.5}, {"unit_one_based": 50, "off_grid_count": 24300, "examples_s": [0.007, 3.07975, 24.55615, 47.2277, 80.22515], "max_tick_error": 0.5}, {"unit_one_based": 51, "off_grid_count": 25292, "examples_s": [0.9133, 1.0742, 1.5076, 4.8867, 6.1473], "max_tick_error": 0.5}, {"unit_one_based": 52, "off_grid_count": 2048, "examples_s": [68.21745, 77.2628, 77.3041, 113.3723, 149.1756], "max_tick_error": 0.5}, {"unit_one_based": 53, "off_grid_count": 227404, "examples_s": [0.6238, 0.6762, 2.36125, 2.44285, 2.62225], "max_tick_error": 0.5}, {"unit_one_based": 54, "off_grid_count": 4151, "examples_s": [6.88315, 6.90165, 7.1694, 7.26525, 8.58335], "max_tick_error": 0.5}, {"unit_one_based": 55, "off_grid_count": 81420, "examples_s": [0.5911, 0.7113, 0.7182, 0.73265, 0.8068], "max_tick_error": 0.5}, {"unit_one_based": 56, "off_grid_count": 255314, "examples_s": [0.0635, 0.1142, 0.147, 0.21165, 0.2461], "max_tick_error": 0.5}, {"unit_one_based": 57, "off_grid_count": 94270, "examples_s": [0.0249, 0.0803, 0.0917, 0.10965, 0.17935], "max_tick_error": 0.5}, {"unit_one_based": 58, "off_grid_count": 54950, "examples_s": [0.65475, 0.65905, 0.6638, 0.69085, 0.9362], "max_tick_error": 0.5}, {"unit_one_based": 59, "off_grid_count": 22489, "examples_s": [0.2289, 0.67155, 0.7399, 0.74395, 0.77095], "max_tick_error": 0.5}, {"unit_one_based": 60, "off_grid_count": 3463, "examples_s": [0.9777, 1.405, 1.7996, 1.80725, 2.8722], "max_tick_error": 0.5}, {"unit_one_based": 61, "off_grid_count": 11757, "examples_s": [2.2215, 2.81055, 5.7082, 7.72255, 10.21375], "max_tick_error": 0.5}, {"unit_one_based": 62, "off_grid_count": 32791, "examples_s": [0.01775, 0.35705, 2.5335, 2.54385, 3.4733], "max_tick_error": 0.5}]`

Reproduce from work/src: `python -m data.align_session "F:\CfC-Sleep\crcns-downloader\fcx-1\data\20140526_277um"`
