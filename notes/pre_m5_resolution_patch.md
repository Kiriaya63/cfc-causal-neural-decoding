# Pre-M5 resolution patch

This patch resolves the three REVIEW items approved after the trust audit without entering M5.

- Main causal waveform: GoodEEG only, shape `[T,1]`.
- Physiological features: delta/broadband from GoodEEG, theta from Thetachannel, sigma from Spindlechannel; UPstatechannel remains provenance only.
- Physical channel reads: identical role mappings are deduplicated internally.
- Provenance: all four functional roles retain source field, 1-based physical channel, 0-based NumPy column, and anatomy claim.
- Model boundary: an explicit whitelist exposes only neural observations, relative `observation_delta_t_s`, causal/modality masks, and computational padding masks. Absolute session/recording times never cross the model boundary.
- Cache: relevant source contents and cached arrays are cryptographically fingerprinted; array shape, dtype, size, and content are checked before reuse. The cache-array implementation hash covers only code capable of changing cached array contents/geometry, so model-adapter-only edits no longer invalidate LFP caches.
- Templeton: workbook `OFC` and ChannelAnatomy `mPFC` are both retained with an explicit conflict flag; neither enters model input and the session remains included.

The former `[GoodEEG, Theta]` raw-waveform slots were replaced because functional roles do not imply independent physical sensors. Duplicating a shared channel as `[x,x]` creates artificial weighting and cross-session acquisition-layout differences without adding information.

## Verification

- All 27 sessions rebuilt or loaded through the common representation pipeline: 27 WARN, 0 FAIL.
- The model boundary is independently versioned as `m4-model-input-v1.0.0` and has its own schema hash.
- The complete suite is 72/72 PASS with 0 skipped.
- The raw preservation check covered 523 files and found `changed_files=[]`.
- No session-specific or animal-specific processing branch was introduced.
