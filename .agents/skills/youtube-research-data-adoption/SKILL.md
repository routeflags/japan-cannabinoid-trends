---
name: youtube-research-data-adoption
description: Adopt YouTube collection payloads into a declared research study with verified provenance, immutable raw data, and reproducible staging.
---

# YouTube research-data adoption

Use this skill when a YouTube payload is being considered for adoption into a study. Adoption means cataloguing an existing collection in the explicitly named study; it does not authorize a new collection, publication, or reuse in another study.

## 1. Establish scope and candidate

1. Record the exact target study ID and candidate payload path. Work only within that study and candidate; do not use another study's records to fill gaps.
2. Confirm the payload was explicitly selected for adoption. Check whether it is already represented in the target study and whether the same collection has been adopted elsewhere. Reuse across studies must be stated as reuse, not represented as a new collection.
3. Inspect the applicable study documentation, study registry, query registry, collector inventory, and `.github/skills/apify-youtube-scraper/SKILL.md`.
4. Identify the exact actor and its supported inputs for this payload. Do not infer search terms, filters, or limits from a directory name, filename, video title, or returned rows.
5. Do not claim Japan-only results merely because the query is Japanese. Confirm a supported geographic restriction and its actual request value before describing the collection as geographically filtered.

## 2. Inspect and preserve the payload

1. Read the payload without modifying it. Record its format, field names, record count, and any available request or execution evidence.
2. Calculate a SHA-256 digest before staging. Copy the payload byte-for-byte into the staging input; verify the staged copy has the same digest.
3. Keep raw observations immutable. Do not clean, normalize, deduplicate, or edit the source payload during adoption.
4. Treat request conditions and returned observations separately:
   - Request conditions include the submitted query, supported filters, relative date selector, reference time, and result limit.
   - Observed range is derived from payload fields only when their meaning is established.
5. Do not convert relative labels such as “months ago” into exact publication dates without a documented, reproducible basis. If the owner accepts relative periods, preserve their source representation and record the limitation.

## 3. Establish provenance without guessing

1. Create a `staging-declaration-v1` document using the repository schema and validation rules.
2. Include only confirmed values. Do not invent a query, limit, timestamp, geographic filter, collector version, or observation window to satisfy a field.
3. Distinguish confirmed values, derived values, and unrecorded historical details. Missing historical metadata alone does not make an otherwise reproducible request method unusable; document what is not recorded and how a future execution can reproduce the request.
4. Preserve available actor run ID, dataset ID, actor/build version, request input, start/end timestamps, completion state, and result count. Where evidence came from an owner-provided console record, describe it as such.
5. If a required declaration value cannot be confirmed or safely represented, stop before staging and ask the owner for the missing fact or a schema-compatible decision.
6. Commit the declaration before running the staging or adoption commands. This preserves the declaration as the controlling input to adoption.

## 4. Stage and adopt through the production workflow

1. Inspect `.staging/` before starting. `make adopt-all` processes every staged candidate, not just the one currently under discussion.
2. Run:

   ```sh
   make stage DECLARATION=<committed-declaration-path>
   ```

3. Inspect the stage result and staged files. Confirm the candidate identity, target study, source, run ID, payload count, and digest.
4. Run `make adopt-all` only when `.staging/` contains exactly the intended candidate(s).
5. Do not manually copy directly into `data/raw/`, bypass staging, or alter raw data after adoption.

## 5. Verify and document

1. Confirm the L1 adoption verdict and inspect every reported issue. Distinguish blocking failures from informational limitations, such as a collector reference marked unverified.
2. Verify the adopted payload digest and record count against the original. Confirm the run metadata and manifest identify the intended study, source, and run.
3. Regenerate the study catalog:

   ```sh
   .venv/bin/python -m storage.cli catalog --study-dir datasets/<study-id> --persist
   ```

4. Update only the target study's README, methodology, and `data/README.md` as needed. State the request conditions, observed range, missing historical details, and reuse status without implying more than the evidence supports.
5. Keep per-video YouTube records in the restricted raw layer. Do not copy them into processed or publication outputs without a separate, explicit publication review; anonymization does not make per-post social datasets publishable.
6. Keep raw payloads out of Git unless the repository's privacy and redistribution review explicitly authorizes otherwise. A local source file may be needed to replay staging; document its expected location and digest without adding sensitive payloads to the repository.

## 6. Run repository checks

Use the repository's Makefile entry points:

```sh
make audit-adoption
make audit-new-runs
make audit-publication
make audit-snapshots
make test
```

Check that the new run is catalogued and that the audits report no new blocking findings. Existing findings for unrelated runs must be reported separately rather than attributed to the current adoption.

## Completion record

Report the target study and run ID, payload path, digest, record count, declaration path, adoption verdict, any informational limitations, checks run, and whether the declaration was committed before staging. Do not push or publish unless explicitly requested.
