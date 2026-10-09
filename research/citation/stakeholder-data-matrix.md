# Stakeholder × Data Matrix

**Last Updated:** 2026-10-02
**Maintainer:** Citation Stakeholder Strategist
**Source Evidence:** v1.7.1 (DOI 10.5281/zenodo.23097769), EXP-20261002, MNT-20261002

---

## Matrix

| Stakeholder | Question | Missing Evidence | Dataset | Citation Unit | Citation Probability | Business Value | Cost | Priority |
|---|---|---|---|---|:---:|:---:|:---:|:---:|
| Journalist / data journalist | When did cannabinoid X first appear in Japan? Which semi-synthetic is emerging now? | English, Japan-specific first-mention series; ranking-ready numbers | Japan Cannabinoid Search Emergence Tracker | "HHBD first appeared in Japanese Google Trends data on 2025-11-30, roughly 8 months after H4CBH (2025-04-06)." | 4/5 | 3/5 | LOW | **P1** |
| Journalist / consumer media | Do Japanese cannabinoid products disclose COAs / labeling? | Market-wide (not own-product) transparency rates | Japan Cannabinoid Product Transparency Survey | "Only X% of sampled Japan-market cannabinoid products displayed a current certificate of analysis." | 4/5 | 4/5 | MEDIUM | **P1** |
| Academic — drug policy / forensic tox | How does consumer attention to semi-synthetic cannabinoids evolve in Japan? | Machine-readable multi-compound longitudinal JP series in English | Cannabinoid Attention Index (JP, quarterly) + first-mention timeline dataset | "Quarterly Google Trends (JP) relative interest for 10 cannabinoid terms, 2021-09-26 to 2026-10-03, with documented first-mention dates." | 3/5 | 2/5 | LOW | P2 |
| Academic — public health / NPS monitoring | What is the lag between market introduction and public search interest? | Cross-walk of market events vs interest spikes (needs public regulatory/product dates) | Interest–Event Timing Series | "Search interest in CBX liquid rose from 0 to a peak score of 100 in the week of 2026-09-20, two months after reported July 2026 sales start." | 3/5 | 2/5 | MEDIUM | P2 |
| Government / policymaker | Which cannabinoids are emerging without regulatory clarity in Japan? | Search emergence signal with regulatory status overlay; English policy brief | Emerging Cannabinoid Japan Cannabinoid Search Emergence Tracker + JP Regulatory Status Table | "Two semi-synthetic cannabinoids (H4CBH, HHBD) crossed detection thresholds in Japan in 2025; regulatory status as of 2026-10 remains [status]." | 4/5 | 2/5 | MEDIUM | **P1** |
| Consumer organization | How transparent is the market? What are common product-information gaps? | Independent product-information completeness rates | Product Information Completeness Checklist results | "Of N sampled products, % lacked batch-level COA links; % lacked quantified cannabinoid breakdown." | 4/5 | 2/5 | MEDIUM | P2 |
| Analytical laboratory | Which compounds are driving testing demand / public interest in Japan? | Attention-to-compound mapping; emerging compound shortlist | Compound Attention–Demand Brief | "Public search interest in CBG (12-m mean score 60) exceeded HHC (40) in Japan during 2025-09 to 2026-10." | 3/5 | 3/5 | LOW | P2 |
| Manufacturer / supplier | Which formats and compounds are gaining attention? | Search + social attention by compound and format | Cannabinoid Momentum Index (JP) | "In Japan Google Trends comparison set A, CBD led (mean 47), followed by THC (12), CBG (3), HHC (1), THCH (0)." | 3/5 | 4/5 | LOW | P2 |
| Investor / business analyst | Is the Japan cannabinoid niche growing or fragmenting? | Category-level (not brand-level) trend series | State of Cannabinoids in Japan (annual) | "From 2021 to 2026, Japanese Google Trends data show continued search demand for CBD while semi-synthetic terms show episodic, short-lived spikes." | 3/5 | 3/5 | LOW | P3 |
| Peer e-commerce / SEO analysts | What queries and compounds are competitors targeting? | Non-first-party, market-wide demand signals | Multi-compound Search Interest CSV | "Google Trends (JP) comparative scores for 10 cannabinoid terms, published under CC BY 4.0 with methodology." | 2/5 | 4/5 | LOW | P3 |
| Industry association / compliance | What terminology is entering consumer discourse? | SKOS-backed compound vocabulary + first-use dates | Compound Terminology Timeline (SKOS-mapped) | "H4CBH first entered measurable Japanese search interest in April 2025; taxonomy concept compound_h4cbh." | 3/5 | 3/5 | LOW | P3 |
| Wikipedia / reference editors | What is the documented Japanese market history of cannabinoid terms? | Stable, citable JP-first timeline with DOIs | First-Mention Timeline Dataset | "According to the Japan Cannabinoid Trends first-mention dataset (v1.7.1), HHC first appeared in Japanese Google Trends data on 2021-11-28." | 2/5 | 1/5 | LOW | P3 |
| Harm-reduction / NGO | Are semi-synthetics reaching consumers faster than health messaging? | Search emergence + disclosure combination | Early Warning + Transparency combined brief | "H4CBH and HHBD first appeared in JP search data in 2025; in a companion transparency audit, X% of sampled products listing these terms provided COAs." | 3/5 | 2/5 | MEDIUM | P3 |

---

## Key Gaps Classified

| Gap | Classification | Stakeholder Impact |
|---|---|---|
| Japan cannabinoid regulatory status by compound (English) | MISSING | Policy, academic, compliance |
| Market-wide product transparency (COA/labeling) rates | MISSING / FRAGMENTED | Consumer orgs, journalists |
| Multi-compound English citation layer for JP trends | PARTIAL (data exists; English citation units incomplete) | International academic, media |
| Longitudinal monthly/quarterly series (not one-off 2026-10 snapshots) | NOT_LONGITUDINAL yet | All |
| Cross-country comparison (JP vs US/EU) | MISSING | Academic, policy, industry |
| Regulatory event dates overlaid on interest time series | MISSING | Academic, policy |
| GSC data is first-party only (single site) | NOT_MARKET_REPRESENTATIVE | Must not be cited as market share |
| CBD/THC polysemy in Google Trends | METHODOLOGICAL LIMIT | Undercuts uncritical citation of raw scores |
| COA study currently own-products only | COI RISK | Must expand sample before external citation |

---

## Citation-Ready Findings Already Available (2026-10-02)

| ID | Finding | Source Layer | Primary Persona |
|---|---|---|---|
| F-01 | HHBD first appeared in JP Google Trends on 2025-11-30; peak 100 week of 2025-12-07 | Google Trends 12m/5y | Journalist, Policy |
| F-02 | H4CBH first appeared 2025-04-06; peak 100 week of 2026-07-26 | Google Trends | Journalist, Policy |
| F-03 | HHC first appeared 2021-11-28; peaked spring 2022; near-zero by 2025-2026 | Google Trends 5y | Academic, Journalist |
| F-04 | THC-O first appeared 2022-03-13; brief 2022 spring spike; largely absent since | Google Trends 5y | Academic |
| F-05 | CBG first appeared 2021-09-26; sustained moderate interest (12-m standalone mean ~60) | Google Trends | Industry, Academic |
| F-06 | Comparison set A (JP): CBD 47 > THC 12 > CBG 3 > HHC 1 > THCH 0 (relative) | Google Trends compare | Journalist, Industry |
| F-07 | CBX liquid JP interest: 0 until mid-Sept 2026 → 44 → 100 peak (week 2026-09-20) → 92 | Google Trends | Journalist |
| F-08 | X corpus 2026-09: 316 posts across 7 cannabinoid keywords | X via Apify | Industry, Academic (limited) |
| F-09 | YouTube corpus: 182 videos across 7 keywords | YouTube via Apify | Industry |
| F-10 | COI disclosed: publisher is cannabinoid e-commerce; methodology provided for independent evaluation | methodology.md | All (credibility) |

**Not yet citable as market facts:** GSC single-site metrics; own-product COA purity claims as market truth; raw CBD/THC Trends scores without polysemy caveat.
