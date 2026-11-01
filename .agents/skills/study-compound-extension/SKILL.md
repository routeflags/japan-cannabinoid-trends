---
name: study-compound-extension
description: Add a compound to a declared research study across query design, source-specific collection, provenance, adoption, coverage, documentation, and downstream scope. Use when expanding a study's compound set.
---

# Extend a study's compound set

This adds one compound to a study that already exists. It does not create a new study, authorize publication, or widen a release slice. Apply `AGENTS.md` first; this skill only sequences those rules for compound expansion.

## 1. Fix ownership and scope

1. Record the study ID, compound ID, sources being extended, and who decided the scope. Work only in the owning study; do not fill gaps from another study's records.
2. Read the study's `README.md`, `methodology.md`, its context contract under `docs/domain/contracts/`, and `docs/specs/raw-data-policy.md`. Confirm the study already covers the source; adding a source is a separate decision.
3. Use the compound identity the repository already defines (`metadata/taxonomy/`, knowledge graph); do not invent an ID or alias.
4. Decide before collecting whether an existing adopted run can be reused. Reuse is recorded as reuse with a run ID, never presented as a new collection.
5. Stop and ask the owner when scope is ambiguous. Do not infer it from a filename or from rows a payload happens to contain.

## 2. Register canonical queries

Add every query the compound needs to `metadata/queries/query-registry.json` with `query_id`, `compound_id`, `intent_id`, `language`, `canonical_text`, and `status`. Add spelling or wording variants to `metadata/queries/query-variants.json` when a collector uses them.

- `query_id` and `canonical_text` are stable identities. Never retarget an existing entry to a new term; add a new ID and deprecate the old one explicitly.
- Validate the registry before a collector or declaration refers to a new ID: `make gates GATE=registries`.

## 3. Update the study query design

1. Update `datasets/<study-id>/metadata/query-design.json`, the authoritative declaration of what counts as primary coverage for that study and source.
2. Record the primary intent(s) and every out-of-primary intent. A retained run outside the design stays raw evidence: it never completes coverage for the compound and is never a required companion run.
3. In the current cannabinoid study, YouTube's primary intent is the liquid product term (`<compound> リキッド`, `product_liquid`); bare compound terms are retained out-of-scope evidence. This is an example only: the study's declaration is authoritative, and other studies or sources may declare a different design.
4. Update project-level mirrors such as `project.json` `queryDesign` only where the repository keeps them; they must not become a second source of truth for coverage.

## 4. Collect through the source-specific workflow

1. Use the source's adapter (`src/collection/adapters/<source>/` or `src/collection/<source>/`), its collector configuration, and the matching `.github/skills/apify-*` or `.agents/skills/*` workflow.
2. Write a new `data/raw/<source>/<run-id>/` directory. Never edit, normalize, or deduplicate raw data in place, and never replace a failed collection with a later successful one.
3. Record request conditions separately from the observed data range. A Japanese query is not a geographic filter, and a returned date range is not the search window.
4. Gate the new run with `scripts/validation/run-gates.sh run <run_metadata.json>`; a rejected run is quarantined, not deleted (`docs/specs/collection-pipeline.md` §5-6).

## 5. Adopt external payloads with provenance

1. For a payload obtained outside the pipeline, commit a `staging-declaration-v1` document under `metadata/provenance/declarations/` (`docs/specs/collection-pipeline.md` §3.4). Include the SHA-256, `query_id`, request conditions, observation window, timestamps and their basis, declared counts, and limitations.
2. Verify every hash and count against the payload. The schema has no `unknown`: an unconfirmed value blocks adoption instead of becoming a placeholder.
3. Keep the requested window (`date_filter`, `reference_time`, limits) separate from the observed range derived from the payload. Mark a declared absolute window as declared, not collector-enforced.
4. Commit the declaration, then run `make stage DECLARATION=<file>`. Inspect `.staging/` before `make adopt-all`, which adopts every staged candidate.
5. Never rewrite a declaration after staging; run metadata pins its SHA-256. Record later corrections as a new `metadata/provenance/corrections/<date>-<slug>.json` document (`record: "declaration_correction"`) with the original and corrected paths and hashes, per-run basis, and a statement that raw was not changed.

## 6. Update catalog, coverage, and documentation

1. Regenerate the study catalog (`.venv/bin/python -m storage.cli catalog --study-dir datasets/<study-id> --persist`) only where the checkout holds the full expected raw state. A partial raw checkout silently drops runs from catalogs, coverage tables, and snapshots.
2. Update the study README, methodology, `data/README.md`, coverage tables, and any project coverage summary so the new compound, run IDs, counts, and observed ranges are traceable.
3. Update downstream distribution scope explicitly. Adding a compound to a study does not add it to a release; record the change in the release slice's own declarations or documentation and treat widening or narrowing the slice as a release decision.

## 7. Run preflight and postflight checks

```sh
make audit-raw-completeness    # catalog/declaration claims resolve to raw
make audit-youtube-coverage    # source coverage; currently YouTube-specific
make audit-distribution-scope  # release slice vs study scope; report-only unless --strict
make audit-new-runs
make audit-publication
make gates
make test
```

- `make audit-snapshots` regenerates tracked audit reports and runs the snapshot guard preflight and postflight. Run it only from a complete raw checkout; it refuses when a claimed run is absent and fails if a run ID disappears. `validation.cli snapshot-guard` accepts `--expected-run-ids` for runs the owner expects but no committed claim names yet.
- Report coverage with the distinct states `observed_zero`, `missing`, `collection_failed`, `partial`, and out-of-scope (retained). Never convert a failure or a missing observation into zero.
- Report findings about unrelated runs separately; do not attribute them to this compound.

## 8. Boundaries

- Never record operating cost: no currency amounts, unit prices, budgets, billed totals, estimates, or free/paid pricing notes in tracked artifacts. Write effort as 労力 / 工数 (`AGENTS.md`; enforced by `tests/validation/test_cost_notation_ban.py`).
- Never publish raw social or video rows, even anonymized. Publish aggregates only, and only after the publication review (`AGENTS.md`, COL-030 §4.1).
- Do not push, publish, delete data, or modify an existing run.

## Completion record

Report the study and compound, sources extended, query IDs, run IDs, declaration and correction paths with SHA-256 values, coverage state per source, documentation and distribution-scope changes, checks actually run, and anything still open. State whether changes are committed.
