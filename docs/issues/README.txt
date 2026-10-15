Issue directory layout
======================

This directory stores machine-readable issue records and a milestone index.

validation.cli audit-issues scans Markdown issue records recursively under this
directory. Non-issue index files intentionally use non-Markdown extensions so
they are not confused with issue records.

Layout
------

active/00-needs-user-confirmation/
  User confirmation, owner action, external service action, or adoption decision
  required before implementation can continue.

active/01-time-gated/
  Work that is blocked by an explicit date or measurement interval.

active/10-publication-release-readiness/
  Publication and release readiness before public release.

active/20-cbd-publication-corrections/
  CBD-specific publication corrections.

active/30-production-collection-expansion/
  Production pipeline / collection / window expansion.

active/40-provenance-storage-reproducibility/
  Provenance, storage, readers, and reproducibility.

active/50-taxonomy-standards/
  Taxonomy and standards alignment.

active/60-privacy-identity-governance/
  Privacy and identity governance.

closed/resolved/
  Resolved issues.

closed/documented/
  Documented issues with no follow-up action.

closed/mitigated/
  Mitigated issues whose residual risk remains documented.

closed/archived/
  Archived issues.

milestones.json
  Local milestone index generated from issue metadata. It is an index, not the
  source of truth. The issue files remain the source of truth.

Rules
-----

- Every Markdown file under docs/issues/ must be an issue record with **ID:**,
  **優先度:**, and **ステータス:**.
- Terminal statuses (RESOLVED, DOCUMENTED, MITIGATED, ARCHIVED) must carry a
  decision date.
- OPEN / PENDING issues belong under active/.
- RESOLVED / DOCUMENTED / MITIGATED / ARCHIVED issues belong under closed/.
