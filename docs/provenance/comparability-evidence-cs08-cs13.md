# CS08–CS13 evidence-emission conditions (comparability)

**Status:** comparison side modeled; collection side pending (ISS-20261015-CMP-005
stays OPEN).  Gate: `src/research/comparability.py::check_cross_study_comparability`.
Definition pinned by synthetic complete-evidence pairs in
`tests/research/test_comparability_gate.py::test_comparable_definition_with_complete_evidence`
and per-condition pins in `tests/research/test_comparability_evidence.py`.
Real repository data stays below `comparable` (see "Real-data position").

`comparable` requires CS01–CS07 identity **plus** recorded evidence for every
row below on **both** sides.  Each row names the evidence carrier (where the
evidence would live), the producer, and which side of the pipeline emits it
today.

| Condition | Evidence carrier (producer) | Comparison side | Collection side |
|---|---|---|---|
| CS08 sampling method explicit | run collection record: sampling method field (no `collection-run-v1` field today) | modeled (`sampling` key; absent → `conditional` + `cs08_sampling_review_required`) | **pending**: adapters must record the sampling method at collection time |
| CS09 coverage `complete` | coverage-manifest-v1 (`src/validation/coverage.py`) | modeled (`coverage` field; `missing` → `not_comparable`, `partial`/absent → `conditional`) | **pending**: no new-run coverage manifests are produced yet |
| CS10 missingness explicit | same manifest: explicit missingness | modeled (`missingness` field; absent → `conditional` + `cs10_missingness_review_required`) | **pending**: same as CS09 |
| CS11 identical normalization scale | fetch-group record (legacy query terms) or declared `normalization_scale` | modeled (different comparison sets → `not_comparable`; untraceable scale → `conditional`) | **pending**: new runs must record their fetch group / comparison set |
| CS12 run + artifact-manifest provenance | `run_metadata.json` + `artifact-manifest.json` + **`transformation-v1` builder records (`src/processing/transformations.py`, 2026-10-15 slice)** | modeled (`run_id` + `artifact_id` presence; manifest-only → `conditional` + `cs12_provenance_partial`) | **partial**: builder exists; emitting records alongside production runs is future work |
| CS13 publication approval | `metadata/publication/*/decision.json` | modeled (`availability` approved/public on both sides; else `conditional` + `cs13_publication_review_required`, internal comparison only) | **pending**: per-artifact approval decisions for new artifacts |

## Real-data position (2026-10-15, re-evaluated)

Legacy runs carry no sampling / coverage / normalization-scale / approval
evidence, so the strongest verdict on repository data is `conditional`.
`test_comparable_is_unreachable_on_repository_data` checks every real-data
pair on every run.  Returning `comparable` there would fabricate evidence
(AGENTS.md), so it stays unreachable until the collection-side column above is
emitted for real runs — which needs live collection work, not an offline
reclassification.
