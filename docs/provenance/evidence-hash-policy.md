# Evidence hash policy (G5 §11)

**Status:** active (2026-10-15, ISS-20261015-PRV-011).  Classifier:
`src/validation/evidence_reconciliation.py::classify_hash_status`.
The code classifies; the registrar decides.  This document is the policy truth;
the code mirrors it and the tests pin the mirror.

## Rule

An evidence entry's `sha256` is recorded **only** when the registrar witnesses
the bytes: read the referenced file, record its SHA-256 together with the
observation time (`observed_at`) and the registrar identity.  A hash is never
back-filled, never copied from another report, and never computed for a file
the registrar did not observe.  An unrecorded hash (`null`) is an explicit
"integrity unknown" state reported as `EVIDENCE_HASH_UNRECORDED` (info), not a
gap to be silently closed.

## What can be hashed

Any **local file with stable bytes at observation time**: registry documents
(`config/*.json`, `metadata/queries/*`, `metadata/windows/*`,
`metadata/artifacts/*`), taxonomy files, and test fixtures.  The positive
example in the registry is `ev-replay-fixture-12m` (pinned hash of the recorded
Google Trends fixture).

## What remains `null`, and why

| Status | Meaning | Examples |
|---|---|---|
| `regenerated_output` | Bytes change on every regeneration (`make audit-snapshots`); a pinned hash would go stale by design. Cited by reference + observation time, never by hash. | `docs/audits/g5-legacy-runs.json` |
| `needs_witnessed_observation` | Pinnable, but only by a witnessed registrar observation (hash + time + identity). An offline edit is not an observation, so the field stays `null` until the owner performs it. | none currently; resolved for the registry/taxonomy entries below on 2026-10-15 |
| `external_unverifiable` | Outside this repository (cloud actor-run URLs, dataset handles, URNs). Cannot be re-checked locally; recorded but never hashed. | cloud-evidence entries (ISS-20261015-PRV-013) and the 37 registry / literature / regulator records listed under Current registry disposition below |
| `reference_unresolvable` | The local reference does not resolve. Fix the reference first (owned as `EVIDENCE_REFERENCE_MISSING` by `check_evidence_registry`); hashing is not applicable. | — (none currently) |

## Current registry disposition (2026-11-15, verified offline)

Of 63 entries in `metadata/provenance/evidence-registry.json`, 7 are pinned, 55 are
external references that are cited by URL and observation time and never hashed, and
1 is the regenerated audit output cited by reference instead of hash. No entry needs
a witnessed observation (`needs_witnessed_observation`) at this time.

The 55 external entries are the THC-O / THCO query-variant evidence set
(ISS-20261104-TAX-029, 2026-11-04), four evidence sets recorded on 2026-11-11 (the
CBE confirmation, the CBL / CBGa confirmations, the THCPO family scope, and the
THCA / THCB topics; ISS-20261111-TAX-040 / TAX-041), and the 18 ChEBI / Wikidata
records verified for the 2026-11-15 compound crosswalk correction
(ISS-20261115-TAX-043).

| `evidence_id` | Reference | Status | Owner action |
|---|---|---|---|
| `ev-legacy-audit-20261013` | `docs/audits/g5-legacy-runs.json` | `regenerated_output` — never pin (stale by design) | none; keep citing by reference |
| `ev-source-registry` | `config/sources.json` | `pinned` | update hash only when the file changes |
| `ev-collector-registry` | `config/collectors.json` | `pinned` | update hash only when the file changes |
| `ev-query-registry` | `metadata/queries/query-registry.json` | `pinned` | update hash only when the file changes |
| `ev-compound-taxonomy` | `metadata/taxonomy/compound-taxonomy.skos.jsonld` | `pinned` | update hash only when the file changes |
| `ev-window-2025-2026` | `metadata/windows/2025-10-12_2026-10-12.json` | `pinned` | update hash only when the file changes |
| `ev-artifact-registry` | `metadata/artifacts/artifact-registry.json` | `pinned` | update hash only when the file changes |
| `ev-replay-fixture-12m` | `tests/.../interest_over_time_cbx_rikiddo_12m.json` | `pinned` | none; the worked example |
| `ev-pubmed-37466480` / `ev-pubchem-cid-198013` / `ev-pubmed-37381980` / `ev-pubmed-36508081` / `ev-cayman-33763-delta9-thco` / `ev-cayman-33762-delta8-thco` | THC-O / THCO literature and vendor URLs | `external_unverifiable` — never hash | none; re-check the URL when citing |
| `ev-gsrs-cannabielsoin` / `ev-wikidata-q22668702` / `ev-pubmed-3254981` / `ev-pubmed-2614640` / `ev-pubmed-1806944` / `ev-doi-10-1055-s-2007-969870` / `ev-pubmed-39062125` | CBE identity evidence (registry, literature) | `external_unverifiable` — never hash | none; re-check the URL when citing |
| `ev-wikidata-q907909` / `ev-gsrs-cannabicyclol` / `ev-pubchem-cid-30607` / `ev-pubchem-cid-59444380` / `ev-pubmed-39811943` / `ev-pubmed-33839545` / `ev-wikidata-q27135612` / `ev-gsrs-cannabigerolic-acid` / `ev-chebi-67081` / `ev-pubchem-cid-6449999` / `ev-pubmed-31686510` / `ev-pubmed-35887277` / `ev-mhlw-2023-edible-report` / `ev-jglobal-cannabigerolic-acid` | CBL / CBGa identity evidence (registries, literature, Japanese references) | `external_unverifiable` — never hash | none; re-check the URL when citing |
| `ev-mhlw-2024-r6-81` / `ev-pubmed-40075559` / `ev-pubchem-cid-172677450` / `ev-pubchem-cid-172874392` / `ev-wikidata-q122689235` | THCPO structural-group and per-isomer records | `external_unverifiable` — never hash | none; re-check the URL when citing |
| `ev-doi-10-1089-can-2016-0008` / `ev-doi-10-1089-can-2021-0003` / `ev-doi-10-1021-acs-jnatprod-9b00876` / `ev-doi-10-1248-yakushi-24-00029` / `ev-mhlw-2024-r6-81-besshi` | THCA / THCB topic literature and the ordinance appendix | `external_unverifiable` — never hash | none; re-check the URL when citing |
| `ev-chebi-69478` / `ev-wikidata-q422917` / `ev-chebi-66964` / `ev-wikidata-q190067` / `ev-chebi-69477` / `ev-wikidata-q412122` / `ev-chebi-3360` / `ev-wikidata-q265831` / `ev-chebi-3357` / `ev-wikidata-q410949` / `ev-chebi-755032` / `ev-wikidata-q254768` / `ev-wikidata-q76009679` / `ev-wikidata-q1104117` / `ev-chebi-2700` / `ev-wikidata-q410228` / `ev-chebi-52392` / `ev-wikidata-q209320` | Compound crosswalk records (ChEBI, Wikidata) for ISS-20261115-TAX-043 | `external_unverifiable` — never hash | none; re-check the URL when citing |

The six registry/window/artifact entries and the taxonomy entry were observed and
pinned on 2026-10-15 under owner instruction for ISS-20261015-PRV-011 (the replay
fixture was pinned on 2026-10-13). They use a new `observed_at` value for that
observation event rather than back-filling the older 2026-10-13 timestamp. If any
referenced file changes, the evidence entry must be updated as a new witnessed
observation (new hash + observation time + registrar note), not patched silently.
The compound taxonomy was re-observed on 2026-11-04 (the THCNM change, then the
`compound_thc_o` identity caveat), several times on 2026-11-11 (the registration
batch, the CBE / CBL / CBGa confirmations, the THCP / THCJD families, the THCPO
scope, the THCA / THCB split, and the THCPO consistency correction), and on
2026-11-15 (the compound external-identifier crosswalk correction,
ISS-20261115-TAX-043, and the candidate-form registration with its audit-correction
scopeNote wording refresh, ISS-20261115-TAX-045); each
re-observation updated `sha256`, `observed_at` and the note together, as this rule
requires.
