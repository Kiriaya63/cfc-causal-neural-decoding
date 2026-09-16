# CfC causal neural decoding — Phase I handoff

**Frozen scope:** Milestones 1–4 (Data & Representation)  
**Freeze date:** 2026-09-16  
**Next milestone:** M5 — Evaluation protocol and animal-level splitting

## Note to co-workers and supervisors

Phase I is complete and frozen. This repository contains the common, strictly causal data and representation pipeline for all 27 CRCNS fcx-1 recording sessions from 11 animals. We have not started model evaluation or M5, and no formal normalization statistics have been fitted.

The scientific question is not merely whether a CfC model can classify sleep states. The project asks when continuous-time inductive biases are genuinely useful for strictly causal, cross-animal neural decoding. M1–M4 therefore establish the data validity, causal sample definition, full-release audit, and model-facing representations before any major benchmark is run.

The frozen causal formulation is:

\[
X_t=[t-W,t), \qquad y_t=\text{state on }[t-1,t), \qquad W\in\{5,10,30\}\text{ s}.
\]

Future samples, centered or zero-phase processing, and future-derived features are prohibited.

## Frozen representation

- Raw LFP waveform: metadata-defined **GoodEEG only**, shape `[T,1]`.
- Causal physiological LFP features:
  - delta from GoodEEG;
  - theta from Thetachannel;
  - sigma from Spindlechannel;
  - broadband from GoodEEG.
- Spikes:
  - population representation for the robust benchmark path;
  - variable-neuron/set-ready representation retained for later modeling.
- Functional channel roles are distinct from physical electrodes. Shared roles do not create duplicated `[x,x]` waveform inputs.
- The decision grid is 1 Hz and the observation grid is 50 Hz.

The enforceable model adapter exposes only neural observations, relative `delta_t`, and necessary causal/modality/padding masks. It excludes animal and session identifiers, filenames, channel identifiers, anatomy labels, local unit identifiers, recording-condition metadata, role-to-channel provenance, and absolute session time.

## Verification at freeze

- 27/27 sessions processed through the same session-agnostic and animal-agnostic pipeline.
- 11 animals represented.
- 69/69 regression tests pass; 0 failed and 0 skipped.
- Full-release source and representation audit completed.
- Historical checks performed against original fcx-1/Watson processing semantics.
- Cache identity and integrity checks hardened with content fingerprints.
- Raw-data preservation audit: 523 files checked and `changed_files=[]`.
- Focused future-leakage and identity-shortcut tests pass.
- No fitted normalization statistics exist.
- Known metadata inconsistencies remain explicit provenance; they are neither silently repaired nor exposed to models.

All sessions retain a `WARN` audit status because inherited provenance or representation warnings are kept visible. `WARN` is not an exclusion criterion, and the audit found no unresolved structural issue.

## Requested review

Please review M1–M4 as if reviewing the Methods section of a paper. In particular, please look for:

1. hidden future leakage or boundary mistakes;
2. questionable interpretation of fcx-1 metadata or Watson processing semantics;
3. cross-animal identity shortcuts;
4. representation choices that discard or duplicate information;
5. anything that could make the later CfC-versus-baseline comparison scientifically unfair.

The most relevant entry points are:

- `notes/milestone4_representation_protocol.md`
- `notes/pre_m5_resolution_patch.md`
- `reports/milestone4/global_summary.json`
- `reports/milestone4/representation_audit.md`
- `reports/pre_m5_trust_audit/pre_m5_trust_audit_report.md`
- `reports/pre_m5_trust_audit/identity_shortcut_audit.md`

## Next step: M5

M5 will be frozen before any major benchmark is run. It will define animal-level train/validation/test logic, train-only normalization, random seeds, model selection and early stopping, metrics, class handling, and model-comparison fairness. Only after M5 is accepted will the formal CfC-versus-baseline benchmark begin.

Raw CRCNS data and rebuildable representation caches are intentionally excluded from Git. They remain local, read-only inputs or reproducible derivatives.

