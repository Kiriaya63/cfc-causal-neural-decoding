# M3-B2.1 structural-failure diagnosis

Diagnostic scope only. Raw files were read-only. The pipeline, time-support/label/causal protocols, and existing FAIL/WARN decisions were not changed. The 27-session audit was not rerun.

## A. Dino interval and EEG frame evidence

Both failing Dino releases carry the same official metadata intervals:

`[[0, 3508.1), [3508.1, 7807.4), [7807.4, 10149.85), [10149.85, 10149.85), [10149.85, 17519.55)]`

Their official `GoodSleepInterval.timePairFormat` is `[[0, 17519.55)]`. The nominal metadata and GoodSleep ends are both `17519.550000000 s`.

| session | zero row context | bytes / frame | complete frames | remainder | duration from complete prefix |
|---|---|---:|---:|---:|---:|
| Dino_061914_ACC | [[7807.4, 10149.85)] → [[10149.85, 10149.85)] → [[10149.85, 17519.55)] | 6219440250 / 284 | 21899437 | 142 | 17519.549600000 s |
| Dino_061914_mPFC | [[7807.4, 10149.85)] → [[10149.85, 10149.85)] → [[10149.85, 17519.55)] | 6219440250 / 284 | 21899437 | 142 | 17519.549600000 s |

The zero row is `[10149.85, 10149.85)`. Under half-open interval mathematics this is an empty set: it contributes zero duration and no points to a union. If it is omitted only from a hypothetical **derived** union while raw provenance remains untouched, the four non-empty rows touch exactly and cover `[0, 17519.55)` continuously. This is a diagnosis, not an implemented rule.

For each EEG, `6,219,440,250 = 21,899,437 × 284 + 142` bytes. Thus 142 bytes are less than one 284-byte multichannel frame and the maximal complete prefix reshapes exactly as `(21,899,437 frames, 142 channels)` of little-endian int16. Probes at the first, middle, and last complete frames all read as 142-channel int16 rows (details are retained in the CSV).

The 142 bytes after that maximal prefix are physically a file-tail suffix. However, this raw format has no frame markers or checksums per frame, so file length alone cannot prove that no insertion/deletion occurred earlier. We found no positive byte-geometry evidence of an internal displacement; the strongest defensible claim is that the complete prefix is geometrically continuous and the only directly observable incompleteness is the 142-byte tail.

### Release-wide interval/frame scan

- `start == stop`: [{"session_id":"Dino_061914_ACC","row_indices_zero_based":[3]},{"session_id":"Dino_061914_mPFC","row_indices_zero_based":[3]}]
- `stop < start`: []
- non-zero EEG frame remainder: [{"session_id":"Dino_061914_ACC","remainder_bytes":142,"frame_width_bytes":284},{"session_id":"Dino_061914_mPFC","remainder_bytes":142,"frame_width_bytes":284}]
- remainder `>= frame_width`: []

Therefore, within the 27-session release, only these two sessions have a zero-duration `RecordingFileIntervals` row, only these two have a non-zero EEG remainder, no session has `stop < start`, and no remainder can or does reach one frame width.

## B. Jenn spike clock evidence

Residual is `abs(timestamp × candidate_frequency − nearest_integer)`, measured in candidate-clock ticks. “On-grid” uses the frozen loader tolerance `<= 1e-06` tick. Full quantiles and histograms are in `jenn_spike_clock_diagnostics.csv`.

| session | XML / MAT acquisition | LFP | candidate grid | on-grid | off-grid fraction | median / max error (ticks) |
|---|---:|---:|---:|---:|---:|---:|
| 20140526_277um | 1250 / 1250 Hz | 1250 Hz | 1250 Hz | 137189/2214209 | 0.938041531 | 0.25 / 0.5 |
| 20140526_277um | 1250 / 1250 Hz | 1250 Hz | 2500 Hz | 274129/2214209 | 0.876195517 | 0.25 / 0.5 |
| 20140526_277um | 1250 / 1250 Hz | 1250 Hz | 5000 Hz | 547165/2214209 | 0.752884664 | 0.25 / 0.5 |
| 20140526_277um | 1250 / 1250 Hz | 1250 Hz | 10000 Hz | 1106703/2214209 | 0.500181329 | 0.499999985 / 0.5 |
| 20140526_277um | 1250 / 1250 Hz | 1250 Hz | 20000 Hz | 2214209/2214209 | 0 | 0 / 2.98023224e-08 |
| 20140527_421um | 20000 / 20000 Hz | 1250 Hz | 1250 Hz | 79213/1309067 | 0.939488964 | 0.25 / 0.5 |
| 20140527_421um | 20000 / 20000 Hz | 1250 Hz | 2500 Hz | 157911/1309067 | 0.879371339 | 0.25 / 0.5 |
| 20140527_421um | 20000 / 20000 Hz | 1250 Hz | 5000 Hz | 315534/1309067 | 0.758962681 | 0.25 / 0.5 |
| 20140527_421um | 20000 / 20000 Hz | 1250 Hz | 10000 Hz | 647225/1309067 | 0.505582984 | 0.49999997 / 0.5 |
| 20140527_421um | 20000 / 20000 Hz | 1250 Hz | 20000 Hz | 1309067/1309067 | 0 | 0 / 5.96046448e-08 |
| 20140528_565um | 20000 / 20000 Hz | 1250 Hz | 1250 Hz | 70980/1183330 | 0.940016732 | 0.25 / 0.5 |
| 20140528_565um | 20000 / 20000 Hz | 1250 Hz | 2500 Hz | 142055/1183330 | 0.879953183 | 0.25 / 0.5 |
| 20140528_565um | 20000 / 20000 Hz | 1250 Hz | 5000 Hz | 283962/1183330 | 0.760031437 | 0.25 / 0.5 |
| 20140528_565um | 20000 / 20000 Hz | 1250 Hz | 10000 Hz | 585710/1183330 | 0.505032409 | 0.499999985 / 0.5 |
| 20140528_565um | 20000 / 20000 Hz | 1250 Hz | 20000 Hz | 1183330/1183330 | 0 | 0 / 2.98023224e-08 |

### Timestamp integrity

- `20140526_277um`: 62 units, 2214209 spikes; finite=True, nonnegative=True, per-unit sorted=True; spike range=[0.007, 13572.34425] s, verified analysis/LFP support=[0, 13572.36) s, outside support=0; within-unit duplicate events=0, global extra equal-time events=9012; decimal resolution requires 5 places (display quantum 1e-05 s); lowest tested exact event grid=20000 Hz (5e-05 s).
- `20140527_421um`: 29 units, 1309067 spikes; finite=True, nonnegative=True, per-unit sorted=True; spike range=[0.0135, 17615.2527] s, verified analysis/LFP support=[0, 17615.268) s, outside support=0; within-unit duplicate events=0, global extra equal-time events=4764; decimal resolution requires 5 places (display quantum 1e-05 s); lowest tested exact event grid=20000 Hz (5e-05 s).
- `20140528_565um`: 33 units, 1183330 spikes; finite=True, nonnegative=True, per-unit sorted=True; spike range=[0.00615, 12395.73395] s, verified analysis/LFP support=[0, 12395.736) s, outside support=0; within-unit duplicate events=0, global extra equal-time events=11170; decimal resolution requires 5 places (display quantum 1e-05 s); lowest tested exact event grid=20000 Hz (5e-05 s).

For `20140526_277um`, every raw stable spike is on the 20 kHz grid within the existing numerical tolerance, while a substantial fraction is off the 1250 Hz grid. The timestamps are represented to five decimal places, consistent with 50 µs ticks. Support comparisons above are diagnostics only and were not used to infer the recording boundary.

The two adjacent Jenn sessions provide the within-animal comparison: their declared XML and BasicMetaData acquisition rates and their empirical grid results are listed in the table, rather than inferred from file-name proximity.

## C. Is the acquisition-grid invariant required for causal binning?

No mathematical dependency was found in the binning operation. `bin_stable_spikes` uses sorted raw timestamps and two `numpy.searchsorted(..., side="left")` calls per half-open bin. For `[start, stop)`, the count is the index of the first event `>= stop` minus the index of the first event `>= start`. It needs finite timestamps, temporal ordering, and the raw event time in seconds; it does not multiply event times by the acquisition rate.

The current grid check occurs earlier in `load_stable_spikes`: it multiplies each timestamp by `metadata.acquisition_sample_rate_hz`, measures distance to the nearest integer, and raises above `1e-6` tick. Its roles under the current frozen code are:

- **Correctness invariant for causal bin assignment:** no. Half-open bin membership remains mathematically defined for off-grid real-valued timestamps.
- **Integrity diagnostic:** yes. It detects disagreement between event timestamps and the declared acquisition clock.
- **Historical assumption encoded as a fatal guard:** yes. The loader currently assumes every stable spike time was generated on the metadata/XML acquisition grid, so this diagnostic presently blocks the pipeline even though the downstream counting formula does not require it.

This classification is analysis only; the guard was not changed or bypassed.

## D. Candidate dataset-wide extensions for human decision

The evidence supports narrowly scoped, session-agnostic candidates, but none was implemented:

1. **Empty provenance row:** preserve raw rows; allow only exact finite `[a,a)` rows to contribute the empty set to a derived interval union, while all non-empty rows must still be finite/open-ended-valid, sorted, non-overlapping, and otherwise satisfy the frozen constraints.
2. **Incomplete final frame:** preserve the raw EEG; when `0 < remainder < frame_width`, optionally define physical signal support from the maximal complete-frame prefix and record the discarded suffix byte count. This requires an explicit scientific decision because byte geometry cannot independently rule out an earlier displacement.
3. **Event-clock provenance:** separate declared acquisition rate from observed timestamp-grid diagnostics. One possible minimum rule is to retain finite/nonnegative/sorted/support checks as fatal, retain declared-grid disagreement as explicit provenance/QC, and allow causal half-open binning from exact raw seconds only if a reproducible event clock is established dataset-wide. For `20140526`, the candidate is 20 kHz; this is not a session-ID branch and no timestamp would be altered.

These are three independent protocol decisions; accepting one does not imply accepting the others. Existing three FAIL states remain unchanged pending human review.
