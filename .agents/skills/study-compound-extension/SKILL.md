---
name: study-compound-extension
description: Add one compound, or an owner-specified batch of compounds, to a declared research study across taxonomy identity, query design, source-specific collection, provenance, adoption, coverage, documentation, and downstream scope. Use when expanding a study's compound set.
---

# Extend a study's compound set

This adds compounds to a study that already exists. It does not run a collection, create a new study, authorize publication, or widen a release slice. Apply `AGENTS.md` first; this skill only sequences those rules for compound expansion.

Keep two things apart throughout. A **term** is a substance name the owner wrote (for example `THCB`). A **compound** is the taxonomy concept that term resolves to. A term is a search string; a concept is a registered identity. Registering a term does not establish a chemical identity, and the classification it carries is a registration label that must be marked when it is provisional (section 2).

## 1. Fix ownership and scope

1. Record the study ID, the terms being added, the sources being extended, and who decided the scope. Work only in the owning study; do not fill gaps from another study's records.
2. Read the study's `README.md`, `methodology.md`, its context contract under `docs/domain/contracts/`, and `docs/specs/raw-data-policy.md`. Confirm the study already covers the source; adding a source is a separate decision.
3. Treat an owner's explicit, enumerated instruction as the scope decision, and register every term it lists. An unregistered canonical identity, an unconfirmed chemical identity, or an uncertain route placement is a reason to record uncertainty (section 2), not a reason to drop the term or hold it for a later pass. Holding a term the owner named is a scope change the owner did not make.
4. Register exactly the terms the instruction enumerates. When the instruction also states a count that disagrees with its own list, register the enumerated terms and record the discrepancy as an open question; never invent terms to reach the stated count.
5. Decide before collecting whether an existing adopted run can be reused. Reuse is recorded as reuse with a run ID, never presented as a new collection.
6. Ask the owner only about what the instruction leaves open: which sources and whether collection is authorized. Never infer scope from a filename or from rows a payload happens to contain.

## 2. Register the compound concept

A query cannot exist without the concept: G2 rejects a registry row whose `compound_id` is not a compound notation (`QUERY_COMPOUND_UNREGISTERED`, `src/validation/query_semantics.py`). Registering a term therefore includes its concept, and that is scope work, not a second scope decision.

1. Reuse the repository's identity when it already exists in `metadata/taxonomy/compound-taxonomy.skos.jsonld` (notation, labels, category, identifiers). `research/regulatory-status/` may document a name, but it does not define concept IDs, and `metadata/taxonomy/thc-regulatory-knowledge-graph.json` organizes THC isomers rather than compound notations — do not derive an ID from either (ISS-20261110-TAX-039). Reuse is the normal case and needs no new taxonomy judgement.
2. When no concept exists, add one in the repository's existing convention:
   - `skos:notation`: `compound_` plus the lowercase term with non-alphanumeric characters replaced by `_` (precedents `compound_thc_o`, `compound_h4cbh`, `compound_hhbd`, `compound_2ag`; e.g. `10-OH-HHC` → `compound_10_oh_hhc`).
   - `@id`: `jptr:compound-` plus the notation token with `_` replaced by `-` (precedents `compound_thc_o` → `jptr:compound-thc-o`, `compound_h4cbh` → `jptr:compound-h4cbh`).
   - `skos:prefLabel`: the term as the owner wrote it, in `en` and `ja`. Do not translate a code name into a chemical name (HHBD / H4CBH / THCNM precedent).
   - `skos:altLabel`: only spellings with a recorded basis, plus the `<term> リキッド` product form when the study's design needs it.
   - `skos:broader`: one of the six existing categories, and the parent's `skos:narrower` must list the concept (`tests/validation/test_taxonomy.py` requires a category and a symmetric pair).
3. Do not decide alias-versus-separate-concept by convenience. Add a second concept when the term is not established as another name for an existing concept; when the sources do establish that it is a name for one (THA → THCNM), register a `skos:altLabel` (and query variant) instead. When the instruction gives no basis for the relationship — an acid form, a positional variant, a marketing spelling — register the term as its own concept, assert no relationship beyond what is documented, and record the open question in the scopeNote. Never merge two named terms into one concept silently.
4. Do not assert what has not been verified. Omit `skos:exactMatch` (ChEBI / Wikidata), CAS, PubChem, IUPAC names and chemical class when the term has no verified basis (CBX / H4CBH / HHBD / THCNM precedent); never fill them by inference, and when the owner's instruction says to ignore URLs, record that external verification was not performed rather than that no identifier exists.
5. Record uncertainty in the places the schema actually supports. The taxonomy has no structured verification field, and the query registry has no identity field — its `status` enum (`active` / `deprecated` / `experimental`) is a lifecycle field, and unknown fields are rejected. Free text is the supported mechanism: `skos:scopeNote` (en and ja), `metadata/taxonomy/iptc-mapping.yaml` (`mapping_type: "none"` with notes, or a `deliberately_unmapped` group with a reason), and the provenance ledgers. Write **UNCONFIRMED** / provisional there, say what it covers, and say what would resolve it. Do not add a new schema field for it.
6. A provisional route placement is a registration label, not a verified classification. State in the `skos:scopeNote` that the placement is provisional, what it is based on, and that different evidence would move it (THCNM precedent). A placement made only to satisfy `skos:broader` must say exactly that.
7. Do not quietly overturn a decided taxonomy state. `compound_rare` is intentionally empty, and `tests/validation/test_compound_rare_membership.py` names `compound_cbdp` / `compound_thcp` as concepts not to be created. A batch that adds either, or adds any rare member, must record the superseding decision and update the test, the `docs/provenance/compound-taxonomy.md` ledger and the issue record in the same change (ISS-20261015-TAX-027).
8. Update every layer a new concept touches, in the same change: `metadata/taxonomy/iptc-mapping.yaml`, `docs/data-dictionary.md` §6.4, `docs/provenance/compound-taxonomy.md` (basis per concept), the issue record under `docs/issues/` for the decision, and the regenerated `exports/taxonomy/*` via `bash scripts/export/export-taxonomy.sh` (never hand-edited). `tests/validation/test_taxonomy_consistency.py` mirrors §6.4, checks the IPTC coverage declaration and pins the export label counts, so those expectations move with the concepts.
9. `metadata/provenance/evidence-registry.json` pins the hashes of both the taxonomy (`ev-compound-taxonomy`) and the query registry (`ev-query-registry`); a mismatch is an error. Record a new witnessed observation (new `sha256`, new `observed_at`, note naming this change) instead of editing the previous one.

## 3. Register canonical queries

1. Add every query the compound needs to `metadata/queries/query-registry.json` with `query_id`, `compound_id`, `intent_id`, `language`, `canonical_text`, and `status`; the item schema has exactly those fields and rejects extras.
2. For a batch, give every term the same query set the study's design declares — in the cannabinoid study, `<term>` (`compound_general`) and `<term> リキッド` (`product_liquid`), one `query_id` per term per intent. A term is not registered with fewer queries because its identity is less certain.
3. `query_id` and `canonical_text` are stable identities. Never retarget an existing entry to a new term; add a new ID and deprecate the old one explicitly. Do not give a term a second ID when it is already registered.
4. Add spelling or wording variants to `metadata/queries/query-variants.json` only when a collector uses them or a recorded basis exists; do not pre-create variants for strings that have never been collected (CBC / CBDV precedent).
5. Register the new queries as `active`, the lifecycle state used for a registered but uncollected query; `status` does not carry identity uncertainty.
6. Validate the registry before a collector or declaration refers to a new ID: `make gates GATE=registries`.

## 4. Update the study query design

1. Update `datasets/<study-id>/metadata/query-design.json`, the authoritative declaration of what counts as primary coverage for that study and source.
2. Declare each newly registered compound that has no adopted run in `compound_set.declared_not_yet_collected` with `compound_id`, `query_ids`, `state: "not_collected"`, `decided`, `decided_by`, and the reason (the owner's instruction, plus whether the identity was reused or newly registered). Do not use `excluded_compound_ids` for a compound that is merely uncollected; exclusion is a comparison decision.
3. Record the primary intent(s) and every out-of-primary intent. A retained run outside the design stays raw evidence: it never completes coverage for the compound and is never a required companion run.
4. In the current cannabinoid study, YouTube's primary intent is the liquid product term (`<compound> リキッド`, `product_liquid`); bare compound terms are retained out-of-scope evidence. This is an example only: the study's declaration is authoritative, and other studies or sources may declare a different design. Registering a term expands the required-query set, so `make audit-youtube-coverage` will report the new compounds as missing until runs exist — that is the declared state, not a measurement.
5. Put the identity caveat where a reader of the design meets it (`limitations`, `coverage_state_note`) and keep it out of the coverage counts.
6. Update project-level mirrors such as `project.json` `queryDesign` only where the repository keeps them; they must not become a second source of truth for coverage.

## 5. Classify retention, then collect through the source-specific workflow

Registration is not collection. A registered term with no run stays `not_collected`: do not report it as zero, missing, failed or partial, and do not collect as part of a registration change.

1. **Classify raw retention first** (`docs/specs/raw-data-policy.md` §5). The two states are `git_tracked` (the payload is committed Repository Storage) and `git_untracked` (the payload is not committed; a local copy may exist, and the repository keeps only non-content provenance). They describe Git tracking, not whether a local raw copy exists.
   - Use the `config/storage-policies.json` default for the source kind. If an owner, legal, or publication review decision sets a different state, record `metadata/provenance/retention/<date>-<slug>.json` (`record: "raw_retention_decision"`) with `retention_status`, `reason`, `decision_reference`, `decided_by`, `decided_at`, and a separate `publication_status`. Do not infer a legal conclusion; record the decision that exists.
   - `git_tracked`: keep the payload immutable and commit it with the run; a clone must substantiate it.
   - `git_untracked`: never add raw rows to Git. The local payload may stay under `data/raw/<source>/<run-id>/` (ignored). The repository keeps the declaration, the retention decision, the catalog/aggregates, and any available SHA-256; when the payload is absent from a clone, report the run as `not_repository_retained`, not missing.
2. Use the source's adapter (`src/collection/adapters/<source>/` or `src/collection/<source>/`), its collector configuration, and the matching `.github/skills/apify-*` or `.agents/skills/*` workflow.
3. Write a new `data/raw/<source>/<run-id>/` directory. Never edit, normalize, or deduplicate raw data in place, and never replace a failed collection with a later successful one. For a `git_untracked` run this directory is local only; never add it to Git (staging into `.staging/` is local).
4. Record request conditions separately from the observed data range. A Japanese query is not a geographic filter, and a returned date range is not the search window.
5. Gate the new run with `scripts/validation/run-gates.sh run <run_metadata.json>`; a rejected run is quarantined, not deleted (`docs/specs/collection-pipeline.md` §5-6).

## 6. Adopt external payloads with provenance

1. For a payload obtained outside the pipeline, commit a `staging-declaration-v1` document under `metadata/provenance/declarations/` (`docs/specs/collection-pipeline.md` §3.4). Include the SHA-256, `query_id`, request conditions, observation window, timestamps and their basis, declared counts, and limitations.
2. For a `git_untracked` run, staging and adoption operate on the local payload only. After adoption, confirm that `git status` and `git ls-files` show no raw payload; never use `git add -f` to force it into the repository. The repository evidence is the declaration, the retention decision (when one exists), the catalog, and derived aggregates.
3. Verify every hash and count against the payload. The schema has no `unknown`: an unconfirmed value blocks adoption instead of becoming a placeholder.
4. Keep the requested window (`date_filter`, `reference_time`, limits) separate from the observed range derived from the payload. Mark a declared absolute window as declared, not collector-enforced.
5. Commit the declaration, then run `make stage DECLARATION=<file>`. Inspect `.staging/` before `make adopt-all`, which adopts every staged candidate.
6. Never rewrite a declaration after staging; run metadata pins its SHA-256. Record later corrections as a new `metadata/provenance/corrections/<date>-<slug>.json` document (`record: "declaration_correction"`) with the original and corrected paths and hashes, per-run basis, and a statement that raw was not changed.

## 7. Update catalog, coverage, and documentation

1. Regenerate the study catalog (`.venv/bin/python -m storage.cli catalog --study-dir datasets/<study-id> --persist`) only where the checkout holds the full expected raw state. A partial raw checkout silently drops runs from catalogs, coverage tables, and snapshots.
2. Update the study README, methodology, `data/README.md`, coverage tables, and any project coverage summary so the new compound, run IDs, counts, and observed ranges are traceable.
3. Record each new query in `docs/provenance/query-inventory.md` §1 with its basis, and state explicitly when there is no run (the CBC / CBDV precedent: "run なし", not collected, not zero).
4. Keep the identity status readable from the documentation: taxonomy scopeNote for the concept, `metadata/taxonomy/iptc-mapping.yaml` for the identifier standing, `docs/provenance/compound-taxonomy.md` for the basis, and the study design for the coverage caveat. Do not let a documented "unconfirmed" turn into an unmarked assertion in a README or a table.
5. Update downstream distribution scope explicitly. Adding a compound to a study does not add it to a release; record the change in the release slice's own declarations or documentation and treat widening or narrowing the slice as a release decision.

## 8. Run preflight and postflight checks

```sh
bash scripts/export/export-taxonomy.sh  # after any taxonomy change; never hand-edit exports
make gates GATE=registries             # query/taxonomy/evidence-hash integrity
make audit-raw-retention               # git_tracked / git_untracked decisions + Git index
make audit-raw-completeness            # catalog/declaration/retention claims versus raw
make audit-youtube-coverage            # source coverage; currently YouTube-specific
make audit-distribution-scope          # release slice vs study scope; report-only unless --strict
make audit-new-runs
make audit-publication
make gates
make test
```

- `make audit-snapshots` regenerates tracked audit reports and runs the snapshot guard preflight and postflight. Run it only from a complete raw checkout; it refuses when a `git_tracked` run is absent or a retention decision is invalid, and it does not fail merely because a `git_untracked` run has no local payload. `validation.cli snapshot-guard` accepts `--expected-run-ids` for runs the owner expects but no committed claim names yet.
- Report coverage with the distinct states `observed_zero`, `missing`, `collection_failed`, `partial`, and out-of-scope (retained). Never convert a failure or a missing observation into zero. A `git_untracked` run is not `missing`; report it as `not_repository_retained` (absent) or `local_only_present` (local payload exists).
- Report findings about unrelated runs separately; do not attribute them to this compound.

## 9. Boundaries

- Never record operating cost: no currency amounts, unit prices, budgets, billed totals, estimates, or free/paid pricing notes in tracked artifacts. Write effort as 労力 / 工数 (`AGENTS.md`; enforced by `tests/validation/test_cost_notation_ban.py`).
- Never publish raw social or video rows, even anonymized. Publish aggregates only, and only after the publication review (`AGENTS.md`, COL-030 §4.1).
- Never treat an unverified identity as a reason to drop, merge or hold a term the owner named, and never treat registration as evidence that the substance exists as the term implies. Registration fixes a search string; it does not establish chemistry, and its provisional markings must survive into every downstream document.
- Do not consult external sources when the owner's instruction says to ignore URLs; record the absent verification instead of acting on it.
- Do not use `retainable` / `not_retainable`: those labels read as local raw existence. Use `git_tracked` / `git_untracked` and keep retention separate from publication permission.
- Do not push, publish, delete data, or modify an existing run.

## Completion record

Report the study, sources extended, query IDs, run IDs, the retention status of each run (`git_tracked` / `git_untracked`) and any retention-decision path, declaration and correction paths with SHA-256 values, coverage state per source, documentation and distribution-scope changes, checks actually run, and anything still open. State whether changes are committed.

For a batch, report per term: the term, the `compound_id`, whether the concept was reused or newly registered, the placement and whether it is documented or provisional, the identity facts that remain unverified, and the collection state (`not_collected` with no run). Record any term the instruction did not settle — a count that disagrees with the enumeration, a placement the repository cannot support — as an open question instead of silently resolving it.
