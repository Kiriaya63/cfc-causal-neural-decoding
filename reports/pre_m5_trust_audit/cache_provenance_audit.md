# Cache provenance and invalidation audit

## Scope

This is a read-only review of `src/representation/cache.py` and the existing M4 caches. No cache file or cache schema was changed.

## What the current identity covers

The cache directory identity is derived from:

- the complete `RepresentationConfig` protocol hash;
- a SHA-256 implementation hash over every `src/representation/*.py` file.

The per-session `cache_metadata.json` additionally records:

- EEG, XML, `BasicMetaData.mat`, and `ChannelAnatomy.csv` paths;
- size and `mtime_ns` for those four sources;
- selected 1-based role channels and anatomy labels;
- waveform and physiological-feature shapes;
- FIR design, coefficient hash, physiological-filter settings, runtime versions, and finite-value flags.

Consequently, ordinary representation-code edits, configuration edits, role-channel metadata edits, and normal source-file replacement invalidate the cache.

## Scientifically appropriate exclusions

`SStable.mat` and `WSRestrictedIntervals.mat` are not in the LFP cache source signature. This is appropriate for the present context-independent LFP cache because spike and label data are read afresh when samples are constructed and do not define cached LFP values. Their absence must not be interpreted as permission to cache complete multimodal samples under the same key in the future.

`GoodSleepInterval.mat` is also absent. The cached arrays cover the verified physical LFP prefix, while analysis support is applied by the current sample index, so a GoodSleep edit does not change array values. However, the cache metadata does not record analysis support, which weakens provenance when a cache is inspected independently of its live `AlignedSession`.

## Weaknesses

### REVIEW — source fingerprints are not content fingerprints

The source signature uses only `size` and `mtime_ns`. A source file whose contents change while preserving both values is accepted as unchanged. This is unlikely in routine use but insufficient for a formal, adversarial model-evaluation chain.

### REVIEW — cached arrays are not authenticated

On a cache hit, the implementation checks only that the two `.npy` files exist. It does not verify:

- content hashes;
- actual dtype;
- actual shape against metadata;
- finite values after reopening;
- agreement between metadata and array headers.

Therefore a replaced, edited, or partially corrupted `.npy` that remains loadable can be silently accepted. This was not observed in the current caches: independent one-shot reconstruction agreed exactly after float32 rounding on four sessions spanning low, median, and high unit counts and multiple anatomy families. The weakness concerns future acceptance, not a demonstrated error in current M4 outputs.

### WARN — runtime dependency changes do not invalidate

Python, NumPy, and SciPy versions are recorded after construction but are not part of `_cache_identity` or `_metadata_matches`. A cache built with another runtime can be accepted. Since coefficients and implementation hashes are fixed and current cached arrays were independently reproduced, this is not a current numerical failure, but runtime identity should be considered in the cache trust policy.

### WARN — support provenance is not self-contained

The cache records the physical frame count and observation count but not the live M3 analysis-support interval or its resolution method. Current sample construction recomputes support, so scientific behavior is correct, but a detached cache directory cannot establish which time interval was legally eligible for sampling.

## Adversarial scenarios

| Scenario | Current result | Desired trust property |
|---|---|---|
| Representation Python code changes | invalidated | satisfied |
| Representation config changes | invalidated | satisfied |
| Selected role channel changes in BMD | normally invalidated by size/mtime | normally satisfied, not cryptographic |
| Raw EEG contents change with same size/mtime | accepted | content fingerprint should invalidate |
| Valid `.npy` is replaced with same-named array | accepted | array hash/header validation should reject |
| `.npy` shape changes but remains loadable | accepted until downstream shape use | validate at cache open |
| GoodSleep changes | LFP arrays accepted; support recomputed live | scientifically safe now, but provenance should record support |
| SciPy version changes | accepted | decide whether runtime or output hash is authoritative |

## Conclusion

The present cache is rebuildable and the current cached numerical content passed independent reconstruction, but stale or incorrect cache content can be accepted in adversarial cases. This is a **REVIEW** finding before formal M5 training. The audit recommends a human-approved cache-hardening change and regression tests; it does not implement them.
