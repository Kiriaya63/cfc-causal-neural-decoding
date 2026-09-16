# Pre-M5 Full Provenance & Pipeline Trust Audit

## Executive conclusion

The source → parser → derived-output chain is internally consistent for the scientific quantities actually used by M1–M4 across all 27 official sessions. No demonstrated corruption, causal leakage, label-source substitution, timestamp requantization, identity-specific processing branch, fitted normalization, or previously unknown EEG geometry failure was found. The existing 57 tests were run unchanged: **57 passed, 0 failed, 0 skipped**.

The audit found **0 FAIL, 4 REVIEW, 7 WARN, and 5 INFO** findings. The four REVIEW findings are:

1. the current two-slot LFP representation treats semantic roles as if they were independent sensor slots, although roles frequently share a physical channel and a dedicated spindle role is omitted in 11 sessions;
2. the current cache can accept a loadable but stale/altered array because source fingerprints are size/mtime only and cached arrays have no content/header authentication;
3. the future M5 model adapter needs an explicit whitelist so provenance and acquisition-identity cues in the sample object cannot become features accidentally;
4. Templeton has a genuine coarse-versus-per-channel anatomy provenance disagreement (official workbook `OFC` versus recommended-channel CSV label `mPFC`).

These findings do not invalidate the present M1–M4 numerical outputs. They do require a human design decision and limited hardening before formal training. The audit verdict is therefore:

## C. HUMAN DESIGN DECISION REQUIRED BEFORE M5

No protocol, parser, representation code, cache schema, test, or raw file was modified during this audit.

## Scope and evidence hierarchy

Audited sources:

- all 27 extracted official session directories under `F:\CfC-Sleep\crcns-downloader\fcx-1\data`;
- original `BasicMetaData.mat`, XML, ChannelAnatomy CSV, GoodSleep, WS interval, SStable and related MAT files;
- official CRCNS data-description PDF, release file list, and `WatsonSleepHomestasis2016Table.xlsx`;
- frozen M1–M4 parsers, reports, sample objects, and caches.

The preferred check was `raw source → parser/code → derived report/cache/sample`. For core geometry, support, labels, stable spikes, and M4 signals, all three levels were checked. Some unused metadata have only source-level cataloguing because the frozen pipeline intentionally does not parse them. Condition and anatomy conflicts are source/source provenance issues rather than parser transformations.

## 1. Metadata field census

The four commonly discussed role fields are only a small subset of the scientifically meaningful release metadata.

### Fields currently used by the pipeline

- acquisition geometry: `Par.nBits`, `nChannels`, `SampleRate`, `lfpSampleRate`, `VoltageRange`, `Amplification`, `Offset`;
- electrode grouping: `Par.AnatGrps`, `Par.SpkGrps`, `goodshanks`;
- time support: `RecordingFileIntervals`, `GoodSleepInterval.timePairFormat`;
- role channels: `goodeegchannel`, `Thetachannel`, `Spindlechannel`, `UPstatechannel`;
- signal scaling provenance: `voltsperunit`;
- stable spikes: `SStable.S_CellFormat`, `shank`, `cellIx`, `numgoodcells`;
- labels: WS `*TimePairFormat` fields.

### Scientifically relevant but intentionally unused in current model representation

- `Spindles.mat` detected events and `SpindleData.detectionchan`;
- `UPDOWNINtervals.mat` UP/DOWN/ON/OFF/Gamma intervals and `UPchannel`;
- `CellIDs` excitatory/inhibitory classifications;
- cluster-quality and stability measures, mean waveforms, clustering notes, SAll/SSubtypes/SBurstFiltered;
- `EMGCorr` and `Motion` (the official description warns that motion is unreliable);
- XML multifile names, file sampling rates, high-pass settings, electrode groups, and unit annotations;
- official experimental category, wake activity, pharmacological and data-quality caveats;
- one-session `RippleNoiseChannel`;
- pre/post-sleep and manually curated fields present only in BWRat21_121813.

### Suspicious or requires provenance caution

- `KetamineStartFile` and `KetamineTimeStamp` occur in 12 BMD files, including home-cage/maze sessions and the official saline session; these appear to include retained MATLAB workspace values and cannot independently define condition;
- `sleepstart`/`sleepstop` occur in 16 files with repeated values across unrelated sessions; they are not equivalent to GoodSleep;
- BWRat21_121813 contains `outvars` copied from another session and a plural `Thetachannels=57` while the canonical `Thetachannel=55`;
- administrative/workspace remnants such as `x`, `y`, `a`, `b`, `dirs`, `names`, `varargin`, and `executestring` have no demonstrated scientific role.

The complete field-by-field presence, datatype/shape, use, and classification is in `metadata_field_catalog.csv`.

## 2. Channel roles and physical-channel semantics

All 27 sessions contain the four canonical BMD roles. `SpindleData.detectionchan` agrees with `Spindlechannel` in 27/27; `UPDOWNINtervals.UPchannel` agrees with `UPstatechannel` in 27/27.

The roles are best interpreted as **semantic roles that map onto physical channels**, not four independent sensors:

- unique physical channels among the four roles: 1 channel in 2 sessions, 2 in 17, 3 in 7, and 4 in 1;
- `goodeegchannel == Spindlechannel` in 16 sessions;
- `goodeegchannel == UPstatechannel` in 25;
- `goodeegchannel == Thetachannel` in 5;
- `Thetachannel == UPstatechannel` in 6.

Role sharing is therefore a normal release property and also has family-specific patterns. The current M4 `[recommended_lfp, theta]` slots are physically duplicated in:

- BWRat19_032413;
- Dino_072114_mPFC;
- Dino_072314_mPFC;
- Dino_072414_mPFC;
- Splinter_020515.

Conversely, the dedicated spindle channel differs from recommended LFP in 11 sessions, yet M4 sigma power is presently computed only on the recommended/theta slots.

### Candidate representation choices requiring human decision

- **A — fixed role slots with `[x,x]`:** simplest and preserves role semantics, but duplicates physical evidence and exposes a family-correlated equality pattern.
- **B — unique physical channels plus explicit role mapping:** scientifically faithful to sensor identity and avoids double counting, but introduces variable channel count and requires a role-aware adapter/mask.
- **C — one standardized GoodEEG waveform for the main benchmark:** clean fixed-width cross-animal baseline with minimal identity cue, but deliberately discards theta/spindle-specific channels.
- **D — role-aware physiological features:** uses the intended semantic detector roles, including spindle, but must define how shared roles and multiple physical sources are combined without double weighting.

No fifth option was strongly justified by the source evidence. The audit does not choose among A–D.

## 3. Indexing audit

No unresolved channel-index ambiguity was found.

| Quantity | Source convention | Internal convention | Exact transformation |
|---|---|---|---|
| BMD role channels | 1-based, explicitly documented | retained 1-based in `SessionMetadata` | NumPy column = source channel − 1 |
| ChannelAnatomy CSV row number | observed 1..N | tuple position 0..N−1 | row number − 1 |
| XML anatomical/spike channels | 0-based | retained 0-based | none |
| raw interleaved EEG column | physical order 0..N−1 | NumPy column | BMD role − 1 |
| SStable shank/cellIx | 1-based local identifiers | retained 1-based | none |
| local unit number | local 1..N provenance | retained 1-based | enumeration + 1 |

Code searches for `+1`, `-1`, and normalization found each production conversion tied to these source conventions. Representative direct byte-offset examples are in `timeline_alignment_examples.md`.

## 4. Anatomy provenance

`ChannelAnatomy.csv` is the only release-wide per-channel textual anatomy source. XML supplies anatomical channel groups and colors but not a reliable per-channel anatomical label. BMD supplies role selections rather than independent anatomy labels.

Findings:

- five selected theta channels have no CSV anatomy label;
- `dHipp` versus `dhipp` is a spelling/case normalization difference, not a physical-channel conflict;
- Templeton has a genuine source/source label conflict: the official workbook groups the animal/session as `OFC`, while ChannelAnatomy labels recommended channel 27 as `mPFC`.

No source disagrees about the physical channel number selected by a BMD role. All raw claims are preserved; anatomy remains provenance only.

## 5. Recording geometry

Across 27 sessions, BMD and XML agree exactly on channel count, bit width, acquisition rate, LFP rate, voltage range/amplification/offset, anatomical groups, and spike groups. EEG geometry was independently recomputed from byte size using int16 interleaving.

Only the two already known Dino releases have a nonzero remainder:

- Dino_061914_ACC: frame width 284 bytes, remainder 142, complete duration 17519.5496 s;
- Dino_061914_mPFC: identical geometry.

The remainder is less than one frame and the verified maximal complete prefix matches the official endpoint guard. No remainder ≥ frame width and no new geometry pattern was found.

The official MATLAB loader uses native `int16`; the Python loader fixes little-endian `<i2`. The release/platform evidence supports this choice, but the official description does not explicitly state byte order, so this remains a documentation WARN rather than a demonstrated mismatch.

## 6. Recording support semantics

Raw `RecordingFileIntervals` and GoodSleep rows were compared numerically with parser objects and M3 reports for all sessions. The frozen rule remains supported:

`I_analysis = I_LFP ∩ I_metadata_constraint ∩ I_GoodSleep_constraint`.

Confirmed across the release:

- the three Jenn sessions preserve `[0,+Inf)` provenance and resolve only against verified finite LFP support;
- the two Dino `[a,a)` rows remain present in raw provenance and contribute the empty set;
- reversed, malformed, and illegal non-finite structures remain distinguishable and rejected;
- neither last spike nor last annotation contributes to support;
- parser-derived analysis support matches the M3 reports in 27/27 sessions.

The alternative BMD `sleepstart/sleepstop` fields are not credible replacements for GoodSleep. They recur with copied values; only BWRat20_101013 would be shortened if they were promoted. The official GoodSleep file and current raw geometry support the frozen rule.

One generic implementation limitation is documented: the current aligned-session loader requires analysis end to equal physical LFP duration when opening the memmap. Every current release session satisfies that equality, but a future valid dataset with GoodSleep shorter than LFP would fail rather than expose a shorter view. This does not change the 27-session conclusion.

## 7. Sleep-label source fidelity

All WS time-pair fields were independently reconstructed from raw MAT files. For all 27 sessions:

- source rows and parser arrays are numerically equal;
- TimePairFormat and IntervalSetFormat duplicates agree;
- independently reconstructed 1-second WAKE/NREM/REM/IGNORE counts equal M2/M3 summaries;
- WAKE comes only from `WakeTimePairFormat`;
- NREM comes only from `SWSPacketTimePairFormat`;
- REM comes only from `REMTimePairFormat`;
- broad Sleep remains diagnostic and is never promoted to NREM;
- MA/WakeInterruption remain auxiliary;
- conflicts and OOB rows remain unsupervised/IGNORE.

No source/code or source/derived label mismatch was found.

## 8. Stable-spike source fidelity

For 27/27 sessions, raw SStable timestamps are finite, nonnegative, per-unit sorted, duplicate-free within each unit, numerically identical after parsing, and binned without rounding/requantization. `numgoodcells`, unit count, local ordering, and CellIDs E/I partition agree.

The Jenn 20140526 event-clock finding is confirmed: its raw timestamps lie on an observed 20 kHz grid while the declared acquisition rate remains 1250 Hz. The exact raw seconds are preserved, and the mismatch is diagnostic only. No other session has this mismatch.

XML `units/unit` is not complete enough to be the stable-unit identity source. SStable contains stable `(shank,cellIx)` pairs absent from XML in four sessions:

- BWRat20_101513: 10 pairs, all on shank 6;
- BWRat21_121613: 4;
- BWRat21_121813: 3;
- Dino_072414_mPFC: 26.

The current loader correctly uses SStable, so derived spikes remain faithful.

## 9. Timeline and M2 boundary audit

Eighteen manually reconstructable raw examples across BWRat, Dino, Jenn, Splinter, and Templeton families were checked. For each example, the direct EEG byte offset/value, spike count, raw annotation row, and parser target share origin 0 and agree in seconds. No hidden offset, concatenation displacement, or alternate session origin was found.

The M2 semantics match code and edge checks:

- `X_t=[t-W,t)` includes a spike at `t-W` and excludes one at `t`;
- `y_t` describes `[t-1,t)`;
- annotation starts are inclusive and stops exclusive in the constructed timeline;
- OOB/conflict/tail bins are never supervised;
- 5/10/30 s windows are strictly past-only.

The production bin validator uses `np.allclose(..., atol=1e-12)` without `rtol=0`. Generated grids are exact integer-rate grids and are unaffected, but a manually supplied large-time grid with a small relative gap could pass validation. This is a numerical-validation WARN and an uncovered regression case.

## 10. M4 observation grid and filtering

The 50-Hz grid is exactly:

- observation bin `k = [k/50,(k+1)/50)`;
- decimation factor 25;
- output samples raw filtered index `25k+24`;
- latest contributing raw time `(25k+24)/1250`, which is 0.8 ms before the observation right edge.

Examples:

- the bin ending at 1.0 s uses raw index 1249 at 0.9992 s;
- a decision at 10.0 s ends at observation step 499 and raw index 12499 at 9.9992 s;
- no raw sample at or after the decision boundary contributes.

### FIR equivalence

The implementation is a 909-tap causal Kaiser FIR with 908-sample history, 454-sample nominal group delay (0.3632 s), and phase-24 decimation. The waveform becomes fully history-valid at observation step 36/right edge 0.74 s.

One-shot causal convolution was compared with the current two-boundary chunked implementation on 750,000 raw frames from each of Templeton, Bogey, Dino_061814_mPFC, and Rizzo_022715. Results were exactly equal after float32 cache rounding. Maximum float64-versus-float32 absolute difference was 0.000484 and maximum relative difference was below `5.95e-8`; no periodic boundary artifact, duplicate, or omission was found.

### Physiological features

Code and independent reconstruction confirm:

- causal order-4 Butterworth SOS for delta 0.5–4, theta 4–10, sigma 10–16, broadband 0.5–20 Hz;
- causal `sosfilt` → square → causal trailing 100-step/2-s mean via `lfilter` → `log1p`;
- no centered window, symmetric padding, `filtfilt`, or future-dependent library default;
- settling steps are 407/99/74/267;
- first fully valid step is `36 + max(407,99,74,267) + 100 − 1 = 542`, whose right edge is 10.86 s;
- cached physiological values reproduce to float32 exactly on the tested segments and remain finite.

## 11. Spike representation integrity

Low-, median-, and high-unit sessions (10, 36, 113 units) were reconstructed directly from raw events over the same 10-second window.

- Branch B sum across units equals the raw half-open event count exactly;
- Branch A equals `population_count / (N_units × 0.02 s)` to floating precision;
- a real unit permutation produces only the corresponding Branch B column permutation;
- population count/rate are invariant;
- padded masked neurons contribute zero, even when their stored padding values are adversarially changed.

No cross-session unit identity assumption was found.

## 12. Cache provenance

The cache identity correctly includes the M4 protocol hash and a hash of all representation Python files. It records role mapping, filter parameters, shapes, runtime versions, and source file size/mtime for EEG/XML/BMD/anatomy.

However, a cache hit does not validate cached array hashes, headers, shapes, dtype, or finiteness, and raw source signatures are not cryptographic. Thus stale/incorrect but loadable caches can be accepted. Existing arrays were independently reproduced and are trustworthy; the weakness is in future invalidation/acceptance. Full details are in `cache_provenance_audit.md`.

## 13. Raw immutability, identity branches, leakage, normalization

Raw-data verification against the earlier frozen manifest found:

- 523/523 files present;
- zero size/mtime changes;
- 491/491 non-EEG SHA-256 hashes unchanged;
- all raw EEG access through read-only `numpy.memmap(mode="r")`;
- no raw write/rename/delete path in production source.

No identity-specific processing branch was found, including attribute-hack searches. Named sessions occur only in tests, diagnostic scripts, cohort manifests, and explanatory report text.

No future leakage was found. Production representation source contains no `filtfilt`, zero-phase filtering, centered rolling/convolution, symmetric/reflect padding, full-session scaling, target-derived features, or label-aware preprocessing. Full-session filtering is causal from session origin; validity masks depend on fixed filter geometry, not future signal content.

No fitted mean/std, z-score, percentile clipping, StandardScaler, release-wide scale, or test-animal statistic enters M1–M4 model arrays. Means/quantiles found elsewhere are descriptive QC or visualization-only. Allowed deterministic count-to-rate and `log1p` transforms are the only relevant transformations.

## 14. Potential identity shortcuts

The M4 sample object includes provenance fields that must not automatically become model inputs: session ID, physical channel IDs, anatomy, local unit/shank/cell identifiers, and protocol hashes. Variable unit count, padding/mask pattern, and duplicate role equality are unavoidable or useful acquisition metadata but can reveal animal/session family. M5 should explicitly whitelist signal tensors and masks and pre-register relevant ablations. See `identity_shortcut_audit.md`.

## 15. Dataset-condition provenance and cohort completeness

The official workbook is the reliable condition/caveat source. It confirms ketamine sessions BWRat20_101513 and BWRat21_121613, saline BWRat21_121813, BWRat21_121113 instability, Dino_072114 low-unit/almost-no-assemblies note, Rizzo_022615 unstable additional units, and Templeton instability/high-frequency-noise caveat. Raw BMD condition-name fields are retained but not promoted when they conflict with this table.

The official release file list has 27 session archives; the workbook has 27 session rows under 11 animal headings; the project manifest maps exactly those 27 sessions to 11 animals; and the raw root contains those 27 intended session directories. No valid official session is omitted and no auxiliary directory is included.

## 16. Regression-test coverage

The unchanged test suite passes 57/57. Strongly covered invariants include support geometry, open ends, empty intervals, incomplete tails, strict labels, conflicts/OOB masking, spike clock handling, half-open bins, past-only windows, future perturbation, variable-N spikes, padding, permutation, startup masks, and absence of fitted normalization.

Important uncovered or only partially covered invariants are:

- full metadata schema/field census;
- explicit end-to-end indexing fixtures;
- role duplication and the chosen physical-channel/role semantics;
- XML-versus-SStable unit provenance;
- shorter-than-LFP legal analysis support;
- large-absolute-time spike-grid validation with `rtol=0` expectation;
- exact phase/right-edge off-by-one regression;
- chunked-versus-one-shot FIR equivalence;
- cache content/header authentication and adversarial invalidation;
- anatomy and condition source conflicts.

The detailed mapping is in `test_coverage_matrix.csv`. No tests were added because this was a read-only audit.

## 17. Finding summary

| Severity | Count | Meaning here |
|---|---:|---|
| FAIL | 0 | no demonstrated violation of frozen semantics, source fidelity, causality, or integrity |
| REVIEW | 4 | human decision/hardening required before formal M5 evaluation |
| WARN | 7 | real ambiguity or generic weakness; current release outputs remain usable |
| INFO | 5 | confirmed provenance or successful negative finding |

Every finding and proposed disposition is listed in `findings.csv`.

## 18. Direct answers to the 27 final questions

1. **Source → parser → derived consistency:** yes for every quantity used by M1–M4; exceptions are source/source provenance conflicts or ignored fields, not silent transformations.
2. **Relevant metadata beyond four roles:** acquisition/scaling/groups, recording and GoodSleep intervals, multifile provenance, stable-unit classifications/quality, spike groups, spindle/UP events, EMG/motion, condition/caveat fields, pre/post sleep fields, and RippleNoiseChannel.
3. **Overlooked information:** no hidden field invalidates current outputs, but spindle/UP roles/events, unit quality/E-I class, condition metadata, and multifile provenance need explicit documentation for future stages.
4. **Indexing ambiguity:** no unresolved operational ambiguity; exact conventions and conversions are documented above.
5. **Source/source conflicts:** yes—Templeton anatomy; incomplete XML unit lists; stale/reused BMD condition/workspace fields; five missing theta anatomy labels.
6. **Source/code mismatch:** none affecting current derived values. Generic shorter-than-LFP support and explicit byte-order provenance are documented limitations.
7. **New recording geometry issue:** no. Only the already approved two Dino 142-byte tails occur.
8. **M3 support rule:** yes, it matches raw evidence for 27/27 sessions.
9. **M2 labels:** yes, exact raw-source reconstruction matches all derived summaries.
10. **Spikes/unit selection:** yes; SStable is faithfully preserved and must remain authoritative over incomplete XML unit lists.
11. **M4 50-Hz alignment/causality:** exact and strictly causal with phase-24 decimation.
12. **Chunked FIR equivalence:** yes, exact after float32 rounding on four representative multi-chunk tests.
13. **Physiological features:** strictly causal; first fully valid right edge is independently reproduced at 10.86 s.
14. **Current role-slot appropriateness:** numerically faithful but scientifically unresolved because semantic roles frequently share channels and spindle roles are omitted; human choice required.
15. **Spike A/B consistency:** exact integer count conservation; rate, permutation, and padding properties pass.
16. **Can stale/incorrect caches be accepted:** yes, adversarially; this is a REVIEW finding even though current caches reproduce correctly.
17. **Identity-specific processing:** none found, including disguised source-attribute checks.
18. **Future leakage:** none found.
19. **Fitted normalization/statistics in inputs:** none found.
20. **Shortcut cues:** duplicate role pattern, unit count/tensor width, padding masks, channel IDs, anatomy, local unit/shank IDs, session ID, and missingness patterns.
21. **Unrecorded caveat fields:** the catalog now records ketamine/saline-related fields, pre/post/manual sleep fields, instability/noise/few-unit notes, and stale-workspace caveats.
22. **Cohort completeness:** confirmed 27 sessions/11 animals by file list, workbook, manifest, and raw directories.
23. **Important missing tests:** chunk equivalence, cache corruption/invalidation, full indexing/schema agreement, role duplication policy, shorter analysis support, XML/SStable provenance, and stricter floating grid checks.
24. **Every REVIEW/FAIL:** four REVIEW findings are PM5-001 through PM5-004 in `findings.csv`; there are no FAIL findings.
25. **Findings requiring M1–M4 change:** current scientific values do not require upstream correction. Cache hardening and possibly the M4 role representation require explicit approval before freeze; the latter is a real representation-design choice.
26. **Documentation-only findings:** XML unit incompleteness with SStable authority, stale condition/workspace fields, ignored sleepstart/stop, byte-order provenance, missing anatomy labels, and official caveats.
27. **Safe to freeze and proceed:** not yet. Current outputs are trustworthy, but formal M5 should wait for the LFP role/physical-channel decision, cache-hardening decision, and explicit model-input whitelist.

## Final disposition

**C. HUMAN DESIGN DECISION REQUIRED BEFORE M5**

Recommended decision order, without implementation:

1. choose the LFP physical-channel/role contract (A–D);
2. approve cache content authentication and validation tests;
3. approve an explicit M5 model-input whitelist and shortcut-ablation plan;
4. decide how Templeton anatomy claims should be represented in provenance-only analyses.

STOP: no M5 work was started.
