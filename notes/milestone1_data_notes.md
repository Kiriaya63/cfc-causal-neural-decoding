# Milestone 1 data notes: `BWRat17_121712`

## Scope and provenance

- Session input (read-only): `F:\CfC-Sleep\crcns-downloader\fcx-1\data\BWRat17_121712`
- Project outputs: `D:\工作相关\望道项目\work`
- Dataset documentation: `F:\CfC-Sleep\crcns-downloader\fcx-1\docs\crcns_fcx-1_data_description.pdf`
- Session date: 2012-12-17
- Recording duration: 6059.4 s = 100 min 59.4 s
- Rule: never write into the session input directory. Open `.eeg` with a read-only memory map and write all derived outputs under the D-drive project.

## 1. `BWRat17_121712_BasicMetaData.mat`

The MAT file contains one top-level MATLAB struct, `bmd`, with raw MATLAB shape `1 x 1`.

| Field | Actual value / shape | Unit or convention | Meaning and later use |
|---|---|---|---|
| `basename` | `BWRat17_121712` | session identifier | Finds files belonging to the same session. |
| `basepath` | `/mnt/brendon12/BWRat17/BWRat17_121712/` | obsolete source path | Provenance only; do not use it as the local path. |
| `Par` | `1 x 1` struct | mixed | Duplicate of the core XML recording parameters. |
| `goodshanks` | `1 x 8`, `[1,...,8]` | MATLAB 1-based shank numbers | Cortical probe shanks containing good units. |
| `goodeegchannel` | scalar `13` | MATLAB/CSV 1-based channel number | Default ACC LFP channel. Convert to Python index 12. |
| `RecordingFileIntervals` | `1 x 2`, `[0, 6059.4]` | seconds from session start | Valid concatenated recording interval. |
| `voltsperunit` | `3.814697265625e-7` | volts per stored int16 count | Converts `.eeg` counts to volts; equals 0.3814697265625 microvolts/count. |
| `UPstatechannel` | scalar `13` | 1-based channel | ACC channel used for UP-state detection. |
| `Spindlechannel` | scalar `13` | 1-based channel | ACC channel used for spindle detection. |
| `Thetachannel` | scalar `65` | 1-based channel | dHipp channel used for theta during sleep scoring; Python index 64. |

Important `Par` fields:

| Field | Actual value / shape | Unit or convention | Meaning and later use |
|---|---|---|---|
| `nBits` | `16` | bits/value | `.eeg` values are signed 16-bit integers. |
| `nChannels` | `72` | channels | Number of interleaved values at each LFP time point. |
| `SampleRate` | `20000` | Hz | Original wideband acquisition rate and time grid on which spike times were detected. It is not the `.eeg` LFP sampling rate. |
| `SampleTime` | `50` | inferred microseconds | Numerically equals `1 / 20000 s = 50 microseconds`; the local documentation does not separately state this field's unit. |
| `lfpSampleRate` | `1250` | Hz | Sampling rate of the downsampled `.eeg` LFP. |
| `VoltageRange` | `20` | acquisition setting; unit not explicitly documented | Retained for provenance. Use `voltsperunit`, not a re-derived scale, for conversion. |
| `Amplification` | `1000` | gain | Acquisition gain setting. |
| `Offset` | `0` | acquisition setting | Acquisition offset. |
| `AnatGrps` | 10 groups; lengths `8,8,8,8,7,7,8,8,4,4` | XML-style 0-based channel numbers | Anatomical/display channel grouping. |
| `SpkGrps` | 9 groups | XML-style 0-based channel numbers | Electrode groups used for spike detection; each uses 32 samples/waveform, peak index 16, and 3 features. |
| `nElecGps` | `9` | groups | Number of spike electrode groups. |

Biologically, these fields describe how electrodes and acquisition hardware map to the data. They are needed to interpret every byte of `.eeg`, select biologically appropriate LFP channels, convert amplitude to volts, and convert sample indices to seconds.

## 2. `BWRat17_121712.xml`

This is a hierarchical XML document with root `<parameters>`, not a rectangular array. It duplicates the core `Par` values and adds acquisition/anatomy notes plus clustering/display configuration.

Verified core fields:

- `acquisitionSystem`: 16 bits, 72 channels, 20000 Hz acquisition, voltage range 20, amplification 1000, offset 0.
- `fieldPotentials/lfpSamplingRate`: 1250 Hz.
- `anatomicalDescription/channelGroups`: 10 groups using 0-based channel numbers. They contain 70 unique channels; XML channels 32 and 33 are intentionally absent and match the two unlabeled CSV rows 33 and 34.
- `spikeDetection/channelGroups`: 9 groups. Every group stores its channel list, `nSamples=32`, `peakSampleIndex=16`, and `nFeatures=3`.
- `units/unit`: 85 XML cluster entries across groups 1-9. This is the clustering catalog, not the post-quality-control stable-unit count.

Anatomy recorded in the XML notes:

- Channels 0-63: 64-site probe in right anterior cingulate cortex (ACC), with eight shanks.
- Channels 64-67: four-wire bundle in dorsal hippocampus (dHipp); XML channel 64 is deepest and 67 shallowest.
- The final four retained channels correspond to non-neural/auxiliary acquisition signals after channel extraction/reordering and are unlabeled in the anatomy CSV.

Numbering warning:

- XML channel numbers are 0-based (`0..71`).
- `BasicMetaData` selected channels and `ChannelAnatomy.csv` are 1-based (`1..72`).
- Therefore `goodeegchannel=13` means Python column 12, and `Thetachannel=65` means Python column 64.

The XML is needed as an independent validation of MAT metadata and for future sessions whose MAT metadata may be incomplete. The verbose neuroscope colors and program settings are not primary model inputs.

## 3. `BWRat17_121712_ChannelAnatomy.csv`

This is a headerless `72 x 2` CSV:

- Column 1: 1-based channel number.
- Column 2: anatomical label.

Actual label counts:

- 62 channels labeled `ACC`: channels 1-32 and 35-64.
- 4 channels labeled `dhipp`: channels 65-68.
- 6 unlabeled channels: 33-34 and 69-72.

Biologically, the map tells us which physical signal comes from frontal cortex versus dorsal hippocampus or an auxiliary channel. We need it to avoid accidentally treating movement/auxiliary signals as cortical LFP and to document why channel 13 is the main ACC LFP while channel 65 is useful for hippocampal theta.

## 4. `BWRat17_121712_WSRestrictedIntervals.mat`

The file contains paired versions of each state:

- `*TimePairFormat`: portable numeric start/stop pairs.
- `*IntervalSetFormat`: MATLAB/TStoolbox objects containing the same intervals.

All annotation times are integer seconds from session start and were scored at 1-second resolution. For Python, use the numeric `TimePairFormat` arrays as the canonical portable representation while checking them against the recording bounds.

| Time-pair field | Raw MATLAB shape | Actual intervals / summary | Biological meaning |
|---|---:|---|---|
| `REMEpisodeTimePairFormat` | `1 x 2` | `[3397, 3500]` | Relatively unfiltered REM episode. |
| `REMTimePairFormat` | `1 x 2` | `[3397, 3500]` | Consolidated REM used in final analysis. |
| `SWSEpisodeTimePairFormat` | `4 x 2` | `[2432,2766]`, `[2839,3027]`, `[3108,3366]`, `[3654,4009]` | Prolonged non-REM episodes; can contain SWS packets and microarousals. |
| `SWSPacketTimePairFormat` | `9 x 2` | range 2432-4009 s | Uninterrupted non-REM/SWS packets between wake-like, REM, or microarousal periods. |
| `MATimePairFormat` | `10 x 2` | 9 in range; one stale interval `[8145,8155]` | Microarousals: short, up to 40 s, wake-like LFP between non-REM packets. |
| `WakeInterruptionTimePairFormat` | `9 x 2` | 8 in range; one stale interval `[6801,6890]` | Wake-like interruptions during sleep; generally longer than microarousals but not long enough to terminate the sleep episode. |
| `WakeTimePairFormat` | `1 x 2` | `[5,2431]` | Consolidated WAKE period of at least 7 minutes. |
| `SleepTimePairFormat` | `1 x 2` | `[2431,4009]` | Consolidated sleep period of at least 20 minutes, including its component substates. |
| `WakeSleepTimePairFormat` | `1 x 1` cell containing a `2 x 2` matrix | `[[5,2431],[2431,4009]]` | The paired WAKE-then-SLEEP episode used as the main analysis unit. |

Interpretation of one row `[start, end]`:

- It is not `[start, duration]` and not a pair of sample indices.
- It says that the interval starts `start` seconds after session time zero and stops at `end` seconds.
- Example: `[3397,3500]` identifies a REM interval around 56 min 37 s to 58 min 20 s after recording start.
- The file is a hierarchy of overlapping/coarse and fine interval types, not a ready-made complete and mutually exclusive label vector.
- For a continuous-time implementation, use an explicit endpoint policy such as half-open `[start,end)` to prevent the shared WAKE/SLEEP boundary at 2431 s from receiving two labels. Because fine intervals are integer, 1-second-resolution annotations, conversion to a categorical per-second table must separately document how endpoint seconds are handled; do not silently assume inclusion.

Bounds issue discovered and investigated:

- Metadata, `.eeg` size, official file list, stable spikes, and `GoodSleepInterval` all agree on `[0,6059.4]` s.
- The local `.eeg` size exactly matches the official data file list, so the recording is not a truncated download.
- Two substate rows lie outside the shared recording: MA `[8145,8155]` and WakeInterruption `[6801,6890]`.
- These rows must be reported as invalid for this shared session and excluded from alignment. They must not be silently clipped or used.
- The official WAKE-SLEEP pair `[5,2431] -> [2431,4009]` is fully in bounds and remains valid.

These intervals provide the ground-truth sleep-state annotation used for sanity checks and later decoding targets. At this milestone they are used only for time alignment and visualization, not model training.

## 5. `BWRat17_121712_SStable.mat`

Top-level variables:

| Variable | Raw MATLAB shape | Actual content / unit | Meaning and later use |
|---|---:|---|---|
| `S_CellFormat` | `1 x 50` cell array | One variable-length vector of timestamps per stable unit; timestamps are seconds from session start. | Preferred portable spike representation. |
| `S_TsdArrayFormat` | `1 x 1` TStoolbox object | Contains 50 `tsd` entries with the same timestamp vectors. | MATLAB-compatible duplicate; not required in Python. |
| `shank` | `50 x 1` | 1-based shank number for each stable unit. | Relates units to electrode groups. |
| `cellIx` | `50 x 1` | original within-shank cell/cluster index | Preserves unit identity. |
| `badcells` | `1 x 1` struct | `allbadcells`, `autobadcells`, `manualbadcells` | Provenance for stability filtering from the original unit set. |
| `numgoodcells` | scalar `50` | units | Explicit stable-unit count. |

Observed spike statistics:

- 50 stable units.
- 345,203 timestamps in total.
- Per-unit spike counts: minimum 121, median 3513, maximum 61,276.
- Global timestamp range: 0.04275 to 6059.355 s.
- All timestamps are finite, non-negative, in bounds, and nondecreasing within each unit.
- Timestamp increments lie on the original 20 kHz time grid: one tick is `1/20000 = 0.00005 s = 50 microseconds`.

What one spike timestamp means:

A value such as `1.23390` in unit 0's vector means the spike-sorting pipeline assigned one extracellular action-potential event to that stable neuron at 1.23390 seconds after the start of the concatenated session. It is an event time, not voltage, spike waveform, spike amplitude, probability, or firing rate. A firing rate is derived later by counting such events inside a chosen time bin and dividing by bin duration.

Biologically, each vector approximates the firing activity of one consistently isolated neuron. We need these events to build a raster or population firing count on the same time axis as LFP and sleep states.

## 6. `BWRat17_121712.eeg`

This is a headerless, signed 16-bit binary LFP file. Values are interleaved by time point:

`t0_ch1, t0_ch2, ..., t0_ch72, t1_ch1, ..., tN_ch72`

Verified layout:

- File size: 1,090,692,000 bytes.
- Bytes per stored channel value: 2.
- Channels per time point: 72.
- Bytes per complete time point: `72 x 2 = 144`.
- Complete time points: `1,090,692,000 / 144 = 7,574,250`.
- Logical shape in Python: `(7_574_250, 72)` with dtype little/native-endian `int16`.
- File-size remainder: 0 bytes, so no partial time point exists.
- Duration: `7,574,250 / 1250 = 6059.4 s`.
- Last sample time: `(7,574,250 - 1) / 1250 = 6059.3992 s`.
- Right boundary after the last sample: `6059.4 s`.

What one `.eeg` sample means:

- A single stored scalar is the instantaneous downsampled extracellular field-potential measurement for one channel at one time point, expressed as an `int16` ADC count.
- A complete time-point sample across the device is a vector of 72 such channel values.
- Convert a raw count `x` to volts with `x * 3.814697265625e-7`; multiply by `1e6` for microvolts.
- Example from the tested window: channel 13 raw count 646 equals about 246.429 microvolts.

Only a read-only memory map was opened. The tested 2428-2433 s window read 6250 samples from each of channels 13 and 65, not the full file. Channel 13 in that window ranged from -1360 to 2455 counts (about -518.8 to 936.5 microvolts); channel 65 ranged from -1887 to 1356 counts (about -719.8 to 517.3 microvolts).

At 1250 Hz:

- One sample interval is `1/1250 = 0.0008 s = 0.8 ms`.
- LFP sample index `i` maps to session time `t_i = i / 1250` seconds, with zero-based `i`.
- A half-open time window `[a,b)` maps to integer sample indices `[round(a*1250), round(b*1250))` when its boundaries lie exactly on the LFP grid.
- Example: `[2428,2429)` maps to `[3,035,000,3,036,250)` and contains exactly 1250 LFP time points per channel.

Biologically, LFP reflects summed, spatially local extracellular population activity, dominated by synaptic and other slow population currents rather than isolated single-neuron action potentials. It is needed to visualize state-dependent rhythms and later derive carefully designed causal features, but feature/filter design belongs to a later milestone.

## 7. Why LFP, spikes, and state intervals share one seconds axis

All three are referenced to the same concatenated session start (`t=0`):

1. LFP stores no explicit timestamp column, so timestamp is reconstructed from its zero-based sample index: `t_lfp = i / 1250` s.
2. Stable spike vectors already store event timestamps in seconds from the same session start. Their 50-microsecond precision reflects the original 20 kHz acquisition grid.
3. Sleep-state rows store start and stop times in seconds from the same session start, at 1-second annotation resolution.

Therefore an event at spike time `t` can be placed between adjacent LFP samples near index `t * 1250` and tested for membership in an annotation interval using the same scalar `t`.

Numerical check around the official transition:

| Seconds bin | LFP indices | LFP time points | Stable spikes | Active units | Broad state | Fine state |
|---|---:|---:|---:|---:|---|---|
| `[2428,2429)` | `[3035000,3036250)` | 1250 | 84 | 26 | WAKE | WAKE |
| `[2429,2430)` | `[3036250,3037500)` | 1250 | 79 | 27 | WAKE | WAKE |
| `[2430,2431)` | `[3037500,3038750)` | 1250 | 65 | 17 | WAKE | WAKE |
| `[2431,2432)` | `[3038750,3040000)` | 1250 | 71 | 19 | SLEEP | no fine label in this second |
| `[2432,2433)` | `[3040000,3041250)` | 1250 | 80 | 22 | SLEEP | SWS packet |

This check proves numerical compatibility of the clocks. It does not yet prove every biological annotation boundary is perfect; the out-of-bounds rows and fine-label gap remain explicit validation findings.

## Next implementation constraints

- Load metadata/XML/CSV before opening `.eeg`.
- Represent channel identity explicitly in both 1-based dataset numbering and 0-based Python indexing.
- Open `.eeg` only with `numpy.memmap(..., mode="r")` or an equivalent read-only windowed reader.
- Normalize every time-pair field to shape `(n_intervals, 2)`, including singleton `1 x 2` arrays and the nested WAKE-SLEEP cell.
- Validate `start <= end`, finite values, sortedness, and `[0, duration]` bounds before use.
- Return out-of-bounds annotations in a validation report; never silently accept them.
- Preserve one spike vector per stable unit and validate finite, sorted, in-bounds seconds.
- Do not build model windows, normalization, splits, or ML datasets in Milestone 1.

## Reusable implementation completed

- `src/data/load_metadata.py`: loads and cross-validates `BasicMetaData.mat`, XML, and channel anatomy.
- `src/data/load_lfp.py`: validates file size and opens `.eeg` with a read-only memory map; copies only requested windows/channels.
- `src/data/load_spikes.py`: returns one read-only seconds array per stable unit plus shank/cell identity.
- `src/data/load_sleep_states.py`: normalizes numeric time pairs and reports invalid rows without silently dropping them.
- `src/data/align_session.py`: reports core clock validity separately from annotation-quality issues.
- `src/visualization/plot_multimodal.py`: produces a short raw-LFP/raster figure and a chunked full-episode summary.
- `scripts/run_milestone1.py`: reusable command accepting any extracted fcx-1 session directory.
- `tests/test_session_pipeline.py`: integration checks fixing the expected facts for `BWRat17_121712`.

Generated artifacts for this session:

- `figures/BWRat17_121712_alignment_report.json`
- `figures/BWRat17_121712_multimodal_3375_3520.png`
- `figures/BWRat17_121712_wake_sleep_episode.png`
