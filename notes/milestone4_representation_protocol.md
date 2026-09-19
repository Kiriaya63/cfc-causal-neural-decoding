# Milestone 4 — Causal Representation & Preprocessing Protocol

Status: **PASS / FROZEN**. Implementation and full-release representation audit are complete; the Phase I freeze was accepted on 2026-09-16.

Protocol version: `m4-v1.1.0`  
Protocol hash: generated from the frozen `RepresentationConfig` and recorded in the M4 audit outputs.

## 1. Frozen upstream semantics

Milestone 4 consumes the frozen M1–M3 outputs without redefining them:

- analysis support is determined by verified LFP support intersected with the approved metadata and GoodSleep constraints;
- raw spike or annotation endpoints never define recording support;
- targets are `WAKE`, `NREM`, or `REM`; conflict, OOB, broad-only sleep, gaps, malformed annotations, and incomplete tails remain `IGNORE`/unsupervised;
- `X_t = [t-W,t)` and `y_t` is the state on `[t-1,t)` for `W = 5, 10, 30 s`;
- raw CRCNS files are read-only and remain the source of truth.

## 2. Time grids and half-open semantics

- Decision grid: 1 Hz.
- Observation grid: 50 Hz.
- Observation interval: 20 ms.
- Context lengths: 5, 10, and 30 s, giving exactly 250, 500, and 1500 observation steps.
- Every observation bin is stored as an explicit half-open interval `[bin_start, bin_stop)`.
- A spike exactly at `bin_start` belongs to the bin; a spike exactly at `bin_stop` does not.
- The last bin satisfies `bin_stop <= decision_time`; therefore no raw datum at or after the decision boundary enters the sample.

## 3. LFP Branch A: causal waveform

The main waveform uses only the metadata-defined GoodEEG (`goodeegchannel`) physical channel. Channel numbers, anatomy, and role mappings remain provenance, not model features. No fallback channel is guessed. Functional roles do not imply independent sensors: when GoodEEG and another role name the same physical channel, the raw signal is read and filtered once rather than duplicated into `[x,x]` slots.

The 1250 Hz LFP is converted to 50 Hz using a deterministic causal Kaiser-window FIR followed by decimation by 25:

- passband target: at most 20 Hz;
- stopband begins: 25 Hz;
- cutoff: 22.5 Hz;
- required stopband attenuation: at least 60 dB;
- measured stopband attenuation: 60.2863 dB;
- FIR length: 909 taps;
- Kaiser beta: 5.65326;
- nominal group delay: 454 input samples = 0.3632 s;
- complete-history startup: 908 input samples = 0.7264 s;
- first valid 50 Hz right edge: 0.74 s.

Filtering is causal and applied continuously in chunks with the required 908-sample overlap. There is no `filtfilt`, zero-phase operation, centered window, future padding, or delay compensation using future data. The selected decimation phase is the last 1250 Hz input sample strictly before each 20 ms observation right edge.

The waveform tensor has shape `[T, 1]` and remains in ADC counts because a trustworthy release-wide physical calibration was not assumed. Startup samples without complete FIR history are explicitly masked.

## 4. LFP Branch B: causal physiological features

Four causal band-power features are computed on the 50 Hz causal role waveforms, with an explicit feature-to-role contract:

- delta: 0.5–4 Hz from GoodEEG;
- theta: 4–10 Hz from Thetachannel;
- sigma: 10–16 Hz from Spindlechannel;
- broadband: 0.5–20 Hz from GoodEEG.

UPstatechannel is preserved in role provenance but does not create a new M4 feature. If roles share one physical channel, their deterministic transforms may reuse that signal without treating the roles as independent sensors.

Each feature uses an order-4 Butterworth SOS bandpass, causal `sosfilt`, squared amplitude, a trailing 2 s/100-step mean, and deterministic `log1p`. No centered estimate is used. The feature tensor has shape `[T, 4]` in `delta, theta, sigma, broadband` order.

Filter settling is determined from the causal impulse response: the remaining suffix must stay at or below `1e-4` of its peak. The settling lengths are 407, 99, 74, and 267 observation steps for delta, theta, sigma, and broadband. Combining the waveform startup, the slowest band settling, and the 2 s trailing power window yields:

- first valid physiological feature step: 542;
- first valid feature interval: `[10.84, 10.86)` s;
- first valid feature right edge: 10.86 s.

Earlier values are not treated as real observations; the validity mask marks them invalid.

## 5. Spike representations

Both branches are generated from the same unchanged stable spike timestamps and the same 50 Hz half-open bins.

### Branch A — population baseline

- `population_count` is retained for QC/provenance.
- Model input is `population_mean_firing_rate_hz = total_count / (N_units * 0.02 s)`.
- Shape: `[T, 1]`.
- It is invariant to a permutation of unit columns.

### Branch B — variable-neuron set-ready counts

- Local stable-unit counts have shape `[T, N_units]`.
- `N_units` remains session-specific; the audited range is 10–113.
- Unit IDs and column order are local provenance only and do not imply cross-session identity.
- Permuting units only permutes the corresponding columns: the representation is permutation equivariant.
- No full-release `[T, 113]` padding is stored.
- Padding is permitted only when batching and must return a boolean neuron mask; padded neurons cannot contribute to population or set results.

Raw event timestamps are preserved separately by the upstream data layer and are never rounded, requantized, overwritten, or exposed as extra information to one regular-grid model family.

## 6. Unified sample contract

Each causal decision sample contains:

- `decision_time_s`, `target_label`, and target interval `[t-1,t)`;
- explicit observation intervals and right edges;
- `lfp_waveform_50hz [T,1]` and mask;
- `lfp_physio_50hz [T,4]` and mask;
- `spike_population_count_50hz [T,1]`;
- `spike_population_rate_50hz [T,1]`;
- `spike_set_counts_50hz [T,N_units]`;
- boolean neuron mask and local unit provenance;
- modality mask `[4]` for waveform, physiology, population spikes, and set spikes;
- causal validity mask `[T,4]`;
- context length, protocol version, and protocol hash.

The audit representation object retains absolute observation intervals and right edges for alignment, causal checks, debugging, and provenance. The enforceable model-facing adapter does not expose those absolute times. It derives and exposes only `observation_delta_t_s`, the elapsed time since the preceding model observation (with the first value defined by the first observation interval width). For the regular 50-Hz representation every value is `0.02 s`; future irregular interfaces may use non-uniform relative elapsed times. Session position, decision time, context start, and all other absolute recording times are excluded.

The remaining model-facing fields contain only neural values, causal/modality masks, and computational neuron-padding masks. The adapter excludes session/animal identifiers, paths, channel numbers, anatomy, local unit identifiers, recording condition, and role mapping. Unit count is not added as an explicit feature; neuron masks remain necessary for correct variable-size computation.

The model boundary is versioned independently as `m4-model-input-v1.0.0`. Its schema hash covers the whitelist, relative-time semantics, delta-t precision, and explicit exclusion of absolute time/provenance. Model-interface revisions therefore remain reproducible without being treated as changes to cached LFP array contents.

For 5/10/30 s contexts, all dense modalities therefore have `T = 250/500/1500`. The neuron dimension alone varies by session.

## 7. Normalization and fairness

No normalization statistics were fitted in M4. There is no full-release z-score, session-wide learned scaler, or validation/test statistic. Only deterministic transformations are present: count-to-rate conversion, `log1p`, and dtype conversion.

Any future scaler must be fitted only on M5 training animals/data and then frozen for validation, test, and external Intan use. The regular benchmark fairness contract is that every model family receives the same underlying 50 Hz causal LFP and spike information. An event/asynchronous interface is reserved for a separately specified M8 benchmark.

## 8. Full-release audit outcome

- Sessions/animals: 27/11.
- Status: 0 PASS, 27 WARN, 0 FAIL.
- All 27 sessions completed with the same session-agnostic and animal-agnostic pipeline.
- The absence of PASS reflects retained M3 warnings and/or explicit representation warnings; WARN does not imply exclusion.
- Stable-unit range: min 10, median 36, max 113.
- All tensors and cached features passed finite/NaN checks and causal sample checks.
- Duplicate role channel warnings occurred in 5 sessions; roles were preserved without fallback.
- Missing selected-role anatomy provenance occurred in 5 sessions; anatomy was not imputed and is not a feature.
- No unresolved structural issue was found.

The only M2-valid samples made representation-invalid were early decisions whose requested context intersects the causal LFP-feature startup. This is an intentional validity mask, not a change to target semantics:

| Context | M2-valid samples | Representation-invalid | Fraction |
|---:|---:|---:|---:|
| 5 s | 203,805 | 100 | 0.0491% |
| 10 s | 203,765 | 110 | 0.0540% |
| 30 s | 203,565 | 110 | 0.0540% |

The affected sessions are `BWRat17_121712`, `BWRat17_121912`, `BWRat18_020513`, `BWRat19_032413`, `BWRat21_121813`, `Dino_061814_mPFC`, `Dino_072114_mPFC`, `Dino_072314_mPFC`, `Rizzo_022615`, and `Templeton_032415`. Each loses 10 samples at 5 s and 11 samples at 10/30 s. Other sessions have no labeled M2-valid decisions early enough to be affected.

## 9. Cache and raw-data preservation

The rebuildable cache is stored under `cache/milestone4/<protocol+cache-array-implementation hash>/<session>/` as versioned NumPy arrays plus metadata. Cache identity includes the protocol hash and a deliberately scoped implementation hash containing only code that can change cached LFP array contents or geometry, including the relevant metadata/LFP/time-support loaders. Model adapters and sample-interface code are excluded, so an interface-only change cannot invalidate unchanged LFP arrays. Relevant raw/metadata sources receive SHA-256 content fingerprints. Each cached array records and validates shape, dtype, file size, and SHA-256 before acceptance. The cache is never a source of truth.

The explicit role-to-physical-channel provenance records GoodEEG, Theta, Spindle, and UPstate source field, original 1-based value, zero-based NumPy column, and anatomy claim. The known Templeton conflict (official workbook `OFC`; recommended-channel ChannelAnatomy `mPFC`) preserves both claims and a conflict flag, causes no exclusion, and is absent from the model-facing whitelist.

The preservation audit checked 523 raw files. All files were checked by size/mtime; non-EEG files below 100 MB also received SHA256 checks. `changed_files` is empty. Raw files were opened read-only, and no raw value or file was modified.

## 10. Verification and freeze boundary

The complete test suite passes: 72/72, with 0 failed and 0 skipped. In addition to the relative-time boundary tests, the final cache/schema tests verify that model adapters are excluded from cache-array invalidation, the model-input schema has an independent versioned hash, and malformed or non-positive observation timing is rejected.

M4 meets its technical freeze criteria: 27/27 sessions are representable, all causal invariants pass, no future-dependent operation exists, no session/animal branch exists, and no unresolved structural issue remains. The Phase I handoff accepted the formal M4 freeze on 2026-09-16. Entry into M5 remains a separate milestone: this implementation does not create splits, fit normalization statistics, or train any model.
