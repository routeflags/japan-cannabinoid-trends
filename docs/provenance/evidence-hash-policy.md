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
| `external_unverifiable` | Outside this repository (cloud actor-run URLs, dataset handles, URNs). Cannot be re-checked locally; recorded but never hashed. | future cloud-evidence entries (ISS-20261015-PRV-013) |
| `reference_unresolvable` | The local reference does not resolve. Fix the reference first (owned as `EVIDENCE_REFERENCE_MISSING` by `check_evidence_registry`); hashing is not applicable. | — (none currently) |

## Current registry disposition (2026-10-15, verified offline)

Of 8 entries in `metadata/provenance/evidence-registry.json`, 7 are pinned and
1 carries info-level `EVIDENCE_HASH_UNRECORDED`.  The remaining unpinned entry is
the regenerated audit output and is intentionally cited by reference instead of
hash:

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

The 6 registry/taxonomy/window/artifact entries were observed and pinned on
2026-10-15 under owner instruction for ISS-20261015-PRV-011.  They use a new
`observed_at` value for that observation event rather than back-filling the
older 2026-10-13 timestamp.  If any referenced file changes, the evidence entry
must be updated as a new witnessed observation (new hash + observation time +
registrar note), not patched silently.
