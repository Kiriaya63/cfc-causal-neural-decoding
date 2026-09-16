# Milestone 3-B1.1 11-animal audit notes

## Frozen protocol used

- Analysis support: verified physical LFP support intersected with resolved metadata and GoodSleep constraints; both official interval sources remain raw provenance.
- The only legal non-finite sentinel is `finite start + positive-infinity stop`; it means no finite official upper bound and is clipped only in the derived constraint layer.
- NaN, negative infinity, non-finite starts, reversed rows, malformed/overlapping interval structures, or unverifiable EEG frame geometry remain failures.
- Stable spikes and annotations validate support but never shorten recording end.
- Strict target policy: valid targets are WAKE/NREM/REM; conflicts, auxiliary substates, gaps, partial bins, OOB rows, and unlabeled bins remain IGNORE/unsupervised.
- Causal samples: `X_t=[t-W,t)`, `y_t` describes `[t-1,t)`, `W=5/10/30 s`.

## Audit outcome

- All 11 directories and seven required file types passed read-only preflight.
- All 11 sessions completed the same aligned-session, strict-label, and causal-window pipeline.
- For `20140528_565um`, raw metadata and GoodSleep `[0, Inf)` provenance remains unchanged; `+Inf` means no finite official upper bound.
- Verified finite EEG/LFP support resolves both derived constraints and analysis support to `[0, 12395.736)`.
- No spike or annotation endpoint participates in support resolution, and no session-specific processing was added.
- Templeton's official `units unstable / high-frequency noise` note is retained as provenance only; it does not trigger exclusion or altered processing.

## Reproducibility

- Manifest: `config/fcx1_milestone3b1_sessions.csv`
- Runner: `scripts/run_milestone3b1.py`
- Reports: `reports/milestone3b1/`
- Protocol decision: `notes/milestone3b1_1_open_ended_time_support.md`
- Raw data remained read-only under `F:/CfC-Sleep/crcns-downloader/fcx-1/data/`.
