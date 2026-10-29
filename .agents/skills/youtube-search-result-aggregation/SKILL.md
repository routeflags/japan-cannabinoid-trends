---
name: youtube-search-result-aggregation
description: Build reproducible, privacy-preserving aggregates from adopted YouTube search-result runs. Use when a YouTube raw run needs aggregation for a study.
---

# Aggregate YouTube search-result runs

Use this skill only after a payload has been adopted into an explicitly named study. Aggregation does not authorize a new collection, reuse in another study, or publication.

## Scope and input checks

1. Confirm the target `study_id`, run ID, and input artifact path. Read only the raw run belonging to that study; do not borrow data from another study.
2. Confirm `run_metadata.json` and `artifact-manifest.json` identify the same study/run and source, and verify the raw payload's SHA-256 and record count against the manifest and run metadata.
3. Confirm the registered query ID and submitted query from provenance. Never infer search terms, filters, dates, or geography from filenames, titles, or returned rows.
4. Treat `date` as a publication date only when the collector contract or methodology defines it. Parse timezone-aware timestamps and convert them to UTC before assigning a calendar month. Reject missing, invalid, or timezone-naive timestamps instead of guessing.

## Aggregation rules

1. Keep raw immutable. Read it without editing, normalizing, filtering, or replacing it.
2. Use a documented identifier such as the run's video ID for within-run deduplication. Count each distinct video ID once. If duplicates disagree on the aggregation period, fail rather than choosing one silently.
3. Name the metric as a count of records returned by the search run, not as the number of all videos uploaded to YouTube. Search results are a sample, not a platform census.
4. Do not create rows for months with no returned records. An absent month is not an observed zero for YouTube activity.
5. Keep output aggregate-only. Do not emit video IDs, titles, channel names, descriptions, URLs, or per-video engagement values. Do not add an engagement measure unless its collection-time meaning and aggregation rule are separately specified.
6. Document source run, query, unit, period boundaries, deduplication, row counts, missingness, and limits. Ensure the aggregate sum reconciles with the number of unique source IDs.

## Repository workflow

1. Implement the transformation as deterministic code under `src/processing/`; add fixture tests for parsing, timezone boundaries, duplicates, missing values, and output privacy.
2. Register the derivation in `processing.reproduce.DERIVATIONS` so it can be re-derived from the local raw input. Since social raw may be non-published, mark that dependency accurately; do not pretend a clean clone can reproduce it without the local input.
3. Expose production through the Makefile and write only to the target study's documented downstream layer. Do not modify `data/raw/`.
4. Update that study's methodology and data README with the exact derivation and its interpretation limits.
5. Keep social aggregates behind publication review. A generated aggregate is not publication approval; do not commit it to a public repository or release it until the publication gate and owner approval are complete.

## Artifact-specific publication review

Aggregation, adoption, and publication are separate decisions. The raw source can remain private while a derived aggregate is approved; approval of the aggregate never authorizes publishing raw records.

1. Review the exact output file, not a similar artifact from another study, source, collector, or run. Record its path, schema, row count, SHA-256, and derivation in `metadata/publication/<artifact_id>/artifact.json`.
2. Perform and record the privacy review explicitly (PUB-04 and PUB-09). Inspect the actual output columns and granularity for identifiers, links, text, per-record measures, and possible linkage from sparse cells. Report the exact number and distribution of small cells to the owner. Do not silently suppress data or apply another study's cell threshold. Record the owner's decision for this artifact, including whether the accepted output keeps small cells or uses an explicitly specified coarsening rule.
3. Confirm source terms, redistribution, and copyright/contract conditions for the specific source and derived output (PUB-06 through PUB-08). A general assessment for a different study or collector is not evidence by itself. If the owner confirms the conditions are checked, record that confirmation as an owner attestation; do not present it as an independent legal review unless supporting evidence was actually examined.
4. Document the output schema and metric meaning (PUB-03). State that counts describe the returned search-result sample, not all YouTube uploads. Cite the transformation and methodology. Record evidence and its date in `evidence.json`; unknowns must remain unconfirmed rather than being turned into PASS.
5. Record an `approved` decision only when the owner clearly approves publication of this exact processed artifact. Pin `decision.json` to the artifact's SHA-256 and state the scope, especially that raw is excluded when that is the owner's instruction. Approval of an intermediate aggregate is not an instruction to create a release, upload it, push, or otherwise publish it externally.
6. Run `validation.cli gate-publication` with the artifact, evidence, and decision files. `SUPPORTED` requires all PUB-01..PUB-10 checks to pass. Keep the gate result as an artifact-specific audit report and register its generator and artifact path in `tests/validation/test_audit_report_freshness.py`; then run `make audit-snapshots` and `make test`. Do not describe a pending or blocked review as approved.
7. If a gate check is not satisfied, report the exact check IDs, what is missing, and concise decision questions the owner can answer. Keep privacy acceptance, terms confirmation, and publication approval as separate questions; do not omit privacy just because the output is aggregated.

## Completion report

State the target study and run, output path, aggregation rule, raw and distinct counts, number of output periods, input hash verification, tests/reproduction checks, and whether publication review is complete. Never describe search-result counts as total platform uploads.
