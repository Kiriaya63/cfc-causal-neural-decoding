# Milestone 3-B1.1 — dataset-wide open-ended time-support rule

## Decision

An official interval `[start, +Inf)` is legal only when `start` is finite. The
positive-infinity stop means **the official provenance supplies no finite upper
bound**. It is preserved unchanged and is never overwritten with an inferred end.

The pipeline keeps these layers separate:

1. `raw_metadata_recording_intervals_s` — unchanged BasicMetaData provenance;
2. `raw_good_sleep_intervals_s` — unchanged GoodSleep provenance;
3. `lfp_support_intervals_s` — physical support calculated from the released EEG;
4. `resolved_metadata_constraint_s` — metadata constraint clipped to verified LFP;
5. `resolved_good_sleep_constraint_s` — GoodSleep constraint clipped to verified LFP;
6. `candidate_analysis_intervals_s` — intersection of LFP and both resolved constraints;
7. `support_resolution_method` — explicit finite or open-ended resolution method.

Formally:

`I_analysis = I_LFP ∩ I_metadata_constraint ∩ I_GoodSleep_constraint`.

For an open stop, resolution is allowed only after all of the following pass:

- the EEG file exists and is non-empty;
- channel count is positive;
- LFP sampling rate is finite and positive;
- the known fcx-1 EEG dtype is little-endian int16 (2 bytes/sample/channel);
- file size is exactly divisible by `n_channels × 2 bytes`;
- the resulting LFP duration is finite and positive.

If any guard fails, the open end remains unresolved and the session fails. NaN,
negative infinity, an infinite start, stop ≤ start, malformed shapes, and
overlapping/unsorted structures remain invalid. They are not covered by this rule.

Stable spikes, sleep annotations, core-state intervals, and WakeSleep episodes are
downstream consistency diagnostics only. Their last timestamps cannot set or
shorten the analysis boundary.

## Verified fcx-1 example

For `20140528_565um`:

- raw metadata: `[0, +Inf)`;
- raw GoodSleep: `[0, +Inf)`;
- verified LFP: `[0, 12395.736)`;
- resolved metadata constraint: `[0, 12395.736)`;
- resolved GoodSleep constraint: `[0, 12395.736)`;
- analysis support: `[0, 12395.736)`;
- method: `open_end_clipped_to_verified_lfp_support`.

The raw positive-infinity values remain present in memory and are serialized as the
explicit string `"Infinity"` in JSON/CSV report fields, avoiding invalid JSON while
preserving their meaning.

## Scope boundary

This decision changes only time-support provenance resolution. Strict labels,
conflict/OOB handling, causal windows, channels, spike representation, filtering,
normalization, data splitting, and model design remain unchanged.
