# Identity shortcut and processing-branch audit

## Processing logic

An AST and text search of `src/data` and `src/representation` found no processing conditional keyed by session ID, animal ID, filename prefix, known anomaly string, exact duration, exact unit count, or anatomy label. The only identity strings in production source are explanatory report text. Session lists and named fixtures occur in audit scripts and tests, where they select cohorts or regression examples rather than alter scientific processing.

Attribute-based branches are generic and scientifically justified:

- finite versus approved open-ended provenance;
- exact-frame versus guarded incomplete final frame;
- duplicate versus distinct role channels, recorded as provenance;
- variable neuron count and supplied neuron mask;
- annotation validity and conflicts.

No disguised session-specific workaround was found.

## Fields available in the M4 sample object

The current `MultimodalRepresentationSample` deliberately carries both model signals and provenance. A future model adapter must not indiscriminately tensorize the entire object.

| Field or property | Classification | M5 handling implication |
|---|---|---|
| LFP waveform and causal physiological values | scientifically intended signal | eligible model input subject to approved representation decision |
| Population rate / unit-wise counts | scientifically intended signal | eligible model input; unit-mask semantics required |
| Decision-relative observation times and validity masks | scientifically intended control information | eligible for masking/time encoding if identical across cohorts |
| `session_id`, animal ID inferred from manifest, raw path | should never be exposed to model | retain only in provenance/evaluation joins |
| Physical channel numbers | provenance only / potential shortcut | exclude from model input |
| Anatomy labels | provenance only under frozen M4 / potential shortcut | exclude unless a later protocol explicitly approves an anatomy-aware model |
| Local unit number, shank, and cell index | provenance only / potential shortcut | exclude from model input; no cross-session identity meaning |
| Number of stable units and variable tensor width | unavoidable acquisition heterogeneity and potential shortcut | Branch A normalizes by unit count; Branch B needs sensitivity analysis and strict animal-held-out evaluation |
| Neuron padding mask | necessary batching control and potential shortcut | use for masking, but prevent the model from directly exploiting total padded width or mask-count without explicit approval |
| Duplicate recommended/theta role pattern | provenance and potential family shortcut | human representation decision required before training |
| Modality and role masks | necessary validity information and possible acquisition shortcut | expose only when operationally necessary; plan ablation |
| Protocol version/hash | provenance only | exclude from model input |

## Main risk

Five sessions have `recommended_lfp == theta`, so the current two-slot input is `[x, x]`; other sessions typically supply two different physical channels. This pattern is family-correlated and can be inferred from the signal itself even if explicit channel metadata is removed. Variable stable-unit count and padding structure can likewise reveal animal/session family. These are not evidence of current leakage or invalid processing, but they are plausible cross-animal shortcut cues.

## Conclusion

There is no identity-specific processing branch. There are, however, provenance fields and representation-shape properties that a future model could exploit. M5 needs an explicit model-input whitelist and planned shortcut ablations. This audit does not choose or implement that policy.
