# [AGENTS.md](http://AGENTS.md)

## Repository Mission

This repository maintains reproducible longitudinal datasets concerning cannabinoid-related trends in Japan.

Data may originate from:

- social platforms
- search platforms
- public web sources
- analytics systems
- first-party websites
- e-commerce systems
- other documented research sources

The repository must remain source-agnostic.

Do not design schemas, pipelines, or directory structures around a single provider unless they belong to a source-specific adapter.

---

# Core Principles

All agents operating in this repository must prioritize:

1. reproducibility
2. provenance
3. preservation of source data
4. methodological transparency
5. deterministic transformations where possible
6. explicit uncertainty
7. privacy and redistribution constraints
8. separation of observation from interpretation

Never modify research data merely to make results appear cleaner or more consistent.

---

# Data Architecture

Use the following conceptual pipeline:

```text
SOURCE
  ↓
COLLECTION
  ↓
RAW
  ↓
VALIDATION
  ↓
INTERIM
  ↓
PROCESSING
  ↓
PROCESSED
  ↓
ANALYSIS
  ↓
PUBLICATION

```

These stages must remain distinguishable.

---

# Raw Data Rule

Raw data is immutable.

Agents MUST NOT:

- manually edit raw observations
- silently remove records
- normalize raw fields in place
- overwrite an original collection
- replace an unsuccessful collection with a successful one without retaining provenance

Corrections and transformations belong downstream.

Prefer:

```text
raw/
    ↓
interim/
    ↓
processed/

```

over editing `raw/`.

---

# Source Separation

Source-specific collection logic belongs in separate adapters.

Example:

```text
src/collection/
├── x/
├── youtube/
├── instagram/
├── tiktok/
├── google_trends/
├── google_search_console/
├── analytics/
├── ecommerce/
└── web/

```

Do not force heterogeneous sources into identical raw schemas.

Normalize them only at the appropriate processing layer.

---

# Dataset Structure

Each independent study should use:

```text
datasets/<study-id>/
├── README.md
├── methodology.md
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── metadata/
└── analysis/

```

A study must be understandable independently from unrelated studies in the repository.

---

# Required Collection Metadata

Every collection run should preserve, where available:

```text
source
collection_timestamp
observation_period
query
filters
parameters
collector
collector_version
API/tool version
pagination settings
maximum result settings
retry number
run identifier
raw record count
deduplicated record count

```

If a field is unavailable, do not fabricate it.

---

# Run Identity

Every collection execution should have a unique run identifier.

Recommended form:

```text
YYYYMMDDTHHMMSSZ-source-study

```

Example:

```text
20260917T120000Z-x-cbx-liquid

```

Repeated runs of the same query must remain distinguishable.

---

# Repeated Collection

Search and social APIs may produce non-deterministic results.

Never assume:

```text
same query + same parameters = same dataset

```

When repeated runs differ:

- retain the run metadata
- calculate differences
- document instability
- define the selection or aggregation rule explicitly

Do not silently select the run that best supports a hypothesis.

---

# Missing Data

Zero observations and missing observations are different states.

Never automatically convert:

```text
collection failure

```

into:

```text
count = 0

```

Recommended states include:

```text
observed_zero
observed_nonzero
missing
collection_failed
partial
unknown

```

---

# Deduplication

Deduplication must be reproducible.

Document:

- unique identifier
- fields used
- normalization applied
- duplicate-selection rule
- records removed

Whenever possible preserve:

```text
raw_count
deduplicated_count
duplicates_removed

```

---

# Derived Data

Every derived field should have a documented derivation.

Example:

```text
monthly_post_count

```

must be traceable to:

```text
source records
→ date normalization
→ filtering
→ deduplication
→ monthly aggregation

```

Do not create unexplained analytical fields.

---

# Cross-Source Analysis

Do not assume metrics from different platforms are directly comparable.

For example:

```text
X posts
Google searches
YouTube views
website sessions
orders

```

measure different phenomena.

Cross-source datasets should preserve source-specific units.

Prefer:

```text
source
metric
value
unit
observation_period

```

over treating heterogeneous counts as equivalent.

---

# First-Party Data

First-party analytics and e-commerce data require additional care.

Before publication, inspect for:

- customer identifiers
- email addresses
- IP addresses
- order identifiers
- transaction identifiers
- precise user-level timestamps
- other potentially identifying information

Prefer aggregated publication.

Never publish secrets, credentials, access tokens, or customer-level private data.

---

# Social Data

Before publishing social-platform records, evaluate:

- redistribution rights
- account identifiers
- usernames
- profile information
- post text
- deleted content
- platform/API terms
- copyright
- privacy implications

Public accessibility does not automatically mean unrestricted redistribution.

When raw redistribution is unsuitable, publish derived or aggregated data plus methodology.

---

# Evidence Levels

Agents must distinguish:

## Observed

Directly present in collected data.

## Derived

Calculated reproducibly from observed data.

## Interpretation

Researcher explanation or hypothesis.

Never present interpretation as an observed fact.

---

# Validation

Before publication, validate at minimum:

```text
schema
encoding
date ranges
record counts
duplicate counts
missing values
unexpected nulls
source identifiers
aggregation totals
metadata completeness

```

Processed totals should be reconcilable with upstream records.

---

# Research Claims

Do not infer causality from temporal correlation.

For example:

```text
search volume increased after event X

```

does not establish:

```text
event X caused search volume to increase

```

Use appropriately limited language.

---

# Reproducibility

Prefer executable transformations over manual spreadsheet operations.

When manual intervention is unavoidable, document:

```text
what changed
why
when
by whom

```

Processing code should preferably accept immutable inputs and produce new outputs.

---

# Publication Gate

Before moving data into a public release, verify:

1. provenance exists
2. methodology exists
3. schema is documented
4. transformations are reproducible
5. counts reconcile
6. limitations are documented
7. privacy has been reviewed
8. redistribution conditions have been reviewed
9. secrets are absent
10. release metadata is complete

Failure of a publication gate must block release until resolved or explicitly documented.

---

# Git Rules

Never commit:

```text
.env
credentials
API tokens
private keys
customer-level private data
unreviewed sensitive raw data

```

Raw datasets should not automatically be committed merely because they exist locally.

Review publication eligibility first.

---

# Versioning

Never rewrite a published research release to hide corrections.

Use:

```text
new commit
→ CHANGELOG
→ new release

```

Published versions should remain historically reproducible.

---

# Citation and DOI

The repository is intended to support formal citation.

Maintain:

```text
CITATION.cff
release metadata
authors
dataset title
version
release date
license information

```

When DOI archiving is enabled, GitHub releases should correspond to identifiable dataset versions.

Do not place a DOI in metadata until it has actually been assigned.

---

# Agent Behavior

Before changing research data, an agent must determine:

```text
What layer is this?

RAW?
INTERIM?
PROCESSED?
ANALYSIS?
PUBLICATION?

```

If RAW:

STOP modification and create a downstream transformation instead.

If PROCESSED:

ensure the transformation is reproducible.

If PUBLICATION:

run the publication validation gate.

---

# Definition of Done

A dataset is not complete merely because a CSV or JSON file exists.

A publishable dataset requires:

```text
data
+
methodology
+
schema
+
provenance
+
validation
+
limitations
+
citation metadata
+
version

```

Research reproducibility takes priority over presentation convenience.