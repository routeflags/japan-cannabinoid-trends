# Citation Opportunities Backlog

**Last Updated:** 2026-10-02
**Maintainer:** Citation Stakeholder Strategist

---

## OPP-001 — Japan Cannabinoid Emerging Compound Early Warning Index

| Field | Value |
|---|---|
| **ID** | OPP-001 |
| **TITLE** | Japan Cannabinoid Emerging Compound Early Warning Index (bilingual EN/JA) |
| **PRIMARY_STAKEHOLDER** | Journalist / data journalist |
| **SECONDARY_STAKEHOLDERS** | Policymaker, forensic toxicologist, academic (NPS/drug policy), harm-reduction NGO |
| **QUESTION** | Which cannabinoid terms are newly appearing in Japanese public search attention, and how quickly are they peaking or fading? |
| **INFORMATION_GAP** | English-accessible, Japan-specific, longitudinal first-mention + momentum series does not exist publicly. Regulatory/policy audiences currently rely on news fragments or US/EU data. |
| **PROPOSED_DATA** | Structured table: compound, SKOS concept id, first-mention date (with 5y-censoring flag), first value, peak value + week, 12-m standalone mean, comparison-set mean, persistence class (durable / episodic / fading), last observed nonzero week. Source data already in `datasets/cannabinoid-multi-trends/` + first-mention research MNT-20261002. |
| **DATA_SOURCE** | Google Trends (JP), today 12-m + today 5-y; public only. Cross-reference published product/regulatory dates where verifiable (not required for v1). |
| **METHOD** | Descriptive statistics + first-detection rule + persistence classification (share of observed weeks with value > 0 in trailing 12 months; explicit censoring for terms below Trends threshold). No causal claims. |
| **OUTPUT** | 1) Machine-readable CSV/JSON; 2) English landing page with citation units; 3) quarterly refresh; 4) DOI via existing Zenodo pipeline. |
| **UPDATE_FREQUENCY** | Quarterly |
| **CITATION_REASON** | Journalists need "when did X appear in Japan" numbers; policymakers need early-warning framing; academics need structured JP NPS-adjacent series. Easy validation sentences. |
| **SEO_VALUE** | MEDIUM — English compound+Japan queries underserved |
| **CITATION_VALUE** | HIGH — originality + scarcity + media/policy utility |
| **COST** | LOW — data already collected; primarily curation, English writeup, chart, method note |
| **RISKS** | Google Trends relative-index misuse; polysemy (CBD/THC); COI perception if framed as promoting CBX-adjacent compounds; 5-year left-censoring for legacy compounds |
| **STATUS** | **PRIORITIZED** |

---

## OPP-002 — Japan Cannabinoid Product Transparency Survey

| Field | Value |
|---|---|
| **ID** | OPP-002 |
| **TITLE** | Japan Cannabinoid Product Transparency Survey (market sample, not own SKUs) |
| **PRIMARY_STAKEHOLDER** | Consumer organization |
| **SECONDARY_STAKEHOLDERS** | Journalist, policymaker, analytical laboratory |
| **QUESTION** | What proportion of Japan-market cannabinoid products disclose COAs, batch info, quantified cannabinoid content, and safety-relevant labeling? |
| **INFORMATION_GAP** | No open, reproducible market-wide transparency rate for Japan. Own-product COA study (cbx-product-coa) is PLANNED and COI-critical — cannot serve as market evidence. |
| **PROPOSED_DATA** | Preregistered checklist scored on public product pages / packaging photos: COA link present, COA current (<12 months), batch ID linkable, quantified major cannabinoids, THC residual stated, manufacturer identifiable, Japanese-language ingredient disclosure. Publish per-product scores + aggregate rates with inclusion criteria. |
| **DATA_SOURCE** | Public e-commerce and brand product pages (manual/scripted collection of public listing data only; no login, no PII, no scraping against ToS where prohibited — prefer manual sample of N=60–100). |
| **METHOD** | Descriptive prevalence statistics + inter-rater agreement if multi-coder; fixed checklist; publish inclusion frame; report confidence intervals as descriptive only (non-probability sample caveat). |
| **OUTPUT** | Survey report (EN+JA), aggregate CSV (product-level scores without proprietary pricing if needed), methodology + preregistration note. |
| **UPDATE_FREQUENCY** | Semiannual or annual |
| **CITATION_REASON** | Highest historical citation density for consumer-safety market audits; concrete "% COA available" numbers journalists and NGOs reuse. |
| **SEO_VALUE** | MEDIUM–HIGH |
| **CITATION_VALUE** | HIGH |
| **COST** | MEDIUM — sampling frame design, collection labor, COI controls |
| **RISKS** | **High COI** — must exclude publisher's own products from primary rate or report stratified results; competitor challenges on sample bias; legal care around comparative claims |
| **STATUS** | **RESEARCHING** (design stage) |

---

## OPP-003 — Quarterly Cannabinoid Attention Brief (JP, English)

| Field | Value |
|---|---|
| **ID** | OPP-003 |
| **TITLE** | Quarterly Cannabinoid Attention Brief — Japan |
| **PRIMARY_STAKEHOLDER** | Journalist / newsletter writer |
| **SECONDARY_STAKEHOLDERS** | Industry analyst, peer e-commerce |
| **QUESTION** | What changed in Japanese public attention to cannabinoids this quarter? |
| **INFORMATION_GAP** | Data exists as one-off collections; no recurring English "state of" series with stable citation URLs. |
| **PROPOSED_DATA** | Fixed 5–8 citation units per quarter: top compound by comparison mean; fastest rise/fall among tracked terms; new first-mentions if any; social corpus counts with caveats; link to full dataset release. |
| **DATA_SOURCE** | Existing Google Trends + X + YouTube collection pipeline (research-keyword-trends / research-x-search / research-youtube-search skills). |
| **METHOD** | Same as OPP-001; brief is presentation layer over standardized metrics. |
| **OUTPUT** | Quarterly web page + PDF-ish HTML + CSV appendix + DOI-linked release note. |
| **UPDATE_FREQUENCY** | Quarterly |
| **CITATION_REASON** | Creates recurring citation targets; journalists cite "as of QX 2026" numbers. |
| **SEO_VALUE** | MEDIUM |
| **CITATION_VALUE** | MEDIUM–HIGH (grows with series age) |
| **COST** | LOW–MEDIUM after pipeline is stable |
| **RISKS** | Must not become promotional; must keep COI disclosure and separate market data from product marketing |
| **STATUS** | **DISCOVERED** |

---

## OPP-004 — Interest–Event Timing Series (search lag after market signals)

| Field | Value |
|---|---|
| **ID** | OPP-004 |
| **TITLE** | Cannabinoid Interest–Event Timing Series (Japan) |
| **PRIMARY_STAKEHOLDER** | Academic (public health / drug policy) |
| **SECONDARY_STAKEHOLDERS** | Policymaker, journalist |
| **QUESTION** | What is the observed lag between publicly documented market/regulatory events and Google Trends interest in related cannabinoid terms in Japan? |
| **INFORMATION_GAP** | Event calendars (product launch, regulatory notice, media coverage) are not systematically joined to interest series. |
| **PROPOSED_DATA** | Event table (date, event type, source URL, compound) + aligned weekly Trends series + descriptive lag metrics (days from event to first nonzero week / to peak). Explicitly non-causal. |
| **DATA_SOURCE** | Existing Trends data + carefully sourced public event dates (press releases, official notices, major news). |
| **METHOD** | Descriptive event alignment; optionally interrupted time-series only if pre-periods are adequate — default to simple lag description. |
| **OUTPUT** | Event-joined dataset + methods note + limitations on confounding. |
| **UPDATE_FREQUENCY** | Annual + event-driven |
| **CITATION_REASON** | Unique Japan-specific timing evidence for NPS/market-emergence literature. |
| **SEO_VALUE** | LOW–MEDIUM |
| **CITATION_VALUE** | MEDIUM–HIGH (academic) |
| **COST** | MEDIUM — event sourcing is labor-intensive |
| **RISKS** | Causal overreach; event-source bias; COI if events selected to flatter CBX narrative |
| **STATUS** | **DISCOVERED** |

---

## OPP-005 — Multi-compound Search Interest Citation Layer (English)

| Field | Value |
|---|---|
| **ID** | OPP-005 |
| **TITLE** | English Citation Layer for Cannabinoid Multi-Trends (JP) |
| **PRIMARY_STAKEHOLDER** | International academic / Wikipedia editor |
| **SECONDARY_STAKEHOLDERS** | Journalist |
| **QUESTION** | Where can non-Japanese researchers find citable JP cannabinoid trend tables with methods? |
| **INFORMATION_GAP** | Much analysis is Japanese-only; processed citation-ready tables with polysemy caveats are incomplete. |
| **PROPOSED_DATA** | Clean processed CSV per compound + comparison sets + methodology PDF/MD in English; stable URLs per table. |
| **DATA_SOURCE** | `datasets/cannabinoid-multi-trends/data/` already collected. |
| **METHOD** | Curation + documentation only. |
| **OUTPUT** | English data pages + machine-readable files linked from CITATION.cff references. |
| **UPDATE_FREQUENCY** | Per dataset release |
| **CITATION_REASON** | Lowers barrier to academic reuse of existing assets. |
| **SEO_VALUE** | MEDIUM |
| **CITATION_VALUE** | MEDIUM (enables other citations) |
| **COST** | LOW |
| **RISKS** | Overclaiming market share from relative Trends scores |
| **STATUS** | **RESEARCHING** |

---

## Rejected / Deferred

| ID | Idea | Reason for Rejection |
|---|---|---|
| R-01 | "Most popular cannabinoid brand" rankings from own catalog | Self-promotion appearance; competitors can challenge methodology |
| R-02 | Clinical efficacy dashboards from market data | Scientific misuse; regulatory risk |
| R-03 | Raw social post dumps as primary product | Platform TOS / copyright / privacy; use aggregates instead |
| R-04 | Single-site GSC "market demand" index | Not market-representative; COI-heavy |
| R-05 | Complex ML anomaly scores without interpretable baselines | Citation-unfriendly; overfits sophistication |

---

## Priority Score (reasoning framework)

PRIORITY ≈ Citation Value × Data Scarcity × Stakeholder Demand × Business Value × Feasibility

| Opp | Citation | Scarcity | Demand | Business | Feasibility | Verdict |
|---|:---:|:---:|:---:|:---:|:---:|---|
| OPP-001 Early Warning Index | HIGH | HIGH (EN/JP gap) | HIGH | MEDIUM | HIGH (data in hand) | **NOW** |
| OPP-002 Transparency Survey | HIGH | HIGH | HIGH | HIGH | MEDIUM | **NEXT** (needs design + COI controls) |
| OPP-003 Quarterly Brief | MED–HIGH | MED | HIGH | MED | HIGH | AFTER OPP-001 metrics locked |
| OPP-004 Event Timing | MED–HIGH | HIGH | MED | MED | MED | 2027 research cycle |
| OPP-005 EN Citation Layer | MED | MED | MED | MED | HIGH | Parallel enablement |
