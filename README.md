# Japan Cannabinoid Trends

An open research dataset for tracking cannabinoid-related trends in Japan across social media, search, web, and first-party data sources.

## Overview

**Japan Cannabinoid Trends** is a longitudinal research project that collects, processes, and publishes data related to cannabinoid interest, terminology, products, and market trends in Japan.

The project is designed as a multi-source dataset rather than a dataset tied to a single platform.

Potential data sources include:

* X
* YouTube
* Instagram
* TikTok
* Google Trends
* Google Search Console
* Website analytics
* E-commerce data
* Public web data
* Other relevant public or first-party datasets

The objective is to create reproducible time-series datasets that can be independently inspected, cited, and reused for research.

## Research Scope

The repository may contain datasets concerning:

* Cannabinoid names and terminology
* Search interest
* Social-media activity
* Content volume
* Product-related interest
* Emerging cannabinoid trends
* Regulatory-event-related changes
* Website search and traffic trends
* E-commerce trends

Individual studies are organized separately so that their methodology and provenance can be evaluated independently.

## Repository Structure

```text
japan-cannabinoid-trends/

├── README.md
├── AGENTS.md
├── CITATION.cff
├── CHANGELOG.md
├── LICENSE
│
├── datasets/
│   └── <study>/
│       ├── README.md
│       ├── methodology.md
│       ├── data/
│       │   ├── raw/
│       │   ├── interim/
│       │   └── processed/
│       └── metadata/
│
├── src/
│   ├── collection/
│   ├── processing/
│   ├── validation/
│   └── analysis/
│
├── docs/
│   ├── methodology/
│   ├── data-dictionary/
│   └── provenance/
│
└── metadata/
```

### Data lifecycle

```text
Source
  ↓
Collection
  ↓
Raw data
  ↓
Validation
  ↓
Processing
  ↓
Processed dataset
  ↓
Analysis
  ↓
Publication
  ↓
GitHub Release
  ↓
DOI archive
```

Raw data is not automatically considered publishable.

Platform terms, copyright, privacy, contractual restrictions, and applicable law must be evaluated before publication.

## Dataset Layers

### Raw

Original collected data.

```text
data/raw/
```

Raw data exists primarily for reproducibility and internal verification.

It may be excluded from public releases when redistribution is restricted or inappropriate.

### Interim

Intermediate outputs generated during cleaning, normalization, deduplication, or transformation.

```text
data/interim/
```

### Processed

Data intended for analysis or publication.

```text
data/processed/
```

Published datasets should preferentially use this layer.

## Methodology

Each dataset must document at least:

* research question
* observation period
* source
* collection date
* query or selection criteria
* collection method
* API/tool/software used
* pagination or collection limits
* retry strategy
* deduplication method
* transformations
* known missing data
* known platform/API instability
* limitations
* validation procedure

The distinction between **observed facts**, **derived values**, and **researcher interpretation** should be maintained.

## Reproducibility

Where technically and legally possible, this repository publishes the code required to reproduce:

* collection
* normalization
* deduplication
* aggregation
* validation
* statistical analysis

Collection results should not be assumed to be deterministic.

APIs, ranking algorithms, search results, platform availability, and historical-data access may change over time.

For this reason, collection timestamps, parameters, software versions, and relevant execution metadata should be preserved.

## Provenance

Every published dataset should make it possible to determine:

```text
Where did the data come from?
        ↓
How was it collected?
        ↓
What transformations were applied?
        ↓
What was excluded?
        ↓
How were published values calculated?
```

Derived datasets should retain sufficient provenance to trace published observations back to their collection methodology.

## Current Research

### CBX Liquid Trend Study

Initial research tracks the emergence of the Japanese search phrase:

`CBX リキッド`

across a 26-week observation period in 2026.

Initial X collection covered:

**2026-03-19 — 2026-09-17**

The study is being expanded to additional data sources.

Detailed methodology and datasets will be maintained under the corresponding dataset directory.

## Data Quality

Known limitations must be documented rather than silently corrected.

Examples include:

* incomplete API results
* changing search algorithms
* non-deterministic results
* unavailable historical observations
* duplicated records
* deleted content
* sampling bias
* query bias
* platform-specific ranking effects

Absence of collected observations must not automatically be interpreted as absence of real-world activity.

## Privacy and Redistribution

Public availability of a source does not automatically imply unrestricted redistribution.

Before raw records are published, contributors should evaluate:

* personally identifiable information
* platform terms
* API terms
* copyright
* database rights
* contractual restrictions
* applicable law

Where appropriate, publication should use aggregated, anonymized, transformed, or derived datasets instead of raw records.

## Citation

Citation metadata is maintained in `CITATION.cff`.

Versioned research releases are intended to be archived in a DOI-supporting research repository.

When citing a specific analysis, use the corresponding dataset version rather than an unspecified snapshot of the `main` branch.

## Versioning

Dataset releases use semantic-style version identifiers where practical.

Example:

```text
v0.1.0
v0.2.0
v1.0.0
```

Published releases should be immutable.

Corrections should result in a new version with the change documented in `CHANGELOG.md`.

## Status

This repository is under active development.

Collection methodologies, schemas, and publication policies may evolve before the first stable research release.
