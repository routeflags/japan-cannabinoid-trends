# japan-cannabinoid-trends production entry points.
#
# Every production script is invoked through this file so runs are
# reproducible from one place (AGENTS.md: reproducibility).  Nothing here
# publishes, pushes, or deletes data; destructive operations have no target.
#
#   make test                         full test suite
#   make stage DECLARATION=<file>      stage external payloads (COL-017 driver)
#   make adopt-all                    adopt every staged run (L1 verdict each)
#   make platform-trends              rebuild processed Google Trends + YouTube release tables
#   make youtube-aggregate            build HHBD YouTube monthly result counts
#   make audit-new-runs               new-run contract audit (read-only)
#   make audit-adoption               adoption backlog: raw run dirs and the metadata a
#                                     declaration needs (run where the raw layer is)
#   make audit-publication            publication contract audit (read-only)
#   make audit-raw-completeness       every catalog/declaration run has raw here
#                                     (git_tracked) or is intentionally untracked
#   make audit-raw-retention          validate the git_tracked / git_untracked
#                                     decisions and the Git index (no raw needed)
#   make audit-youtube-coverage       primary liquid coverage inventory
#   make audit-comparison-scale       common-scale anchor coverage (read-only)
#   make gate-plan PLAN=<file>        pre-collection plan gate (anchors included)
#   make audit-distribution-scope     release slice vs raw study scope
#   make audit-snapshots              regenerate tracked docs/audits snapshots
#   make gates                        validation gate scripts

PYTHON ?= .venv/bin/python
WORKSPACE ?= .
DATASETS ?= datasets
CONFIG ?= config
METADATA ?= metadata
RETENTION ?= metadata/provenance/retention
GATE ?= registries
GATE_ARGS ?=
PLAN ?=

.PHONY: help test collect stage adopt-all platform-trends youtube-aggregate audit-new-runs audit-adoption audit-publication audit-raw-completeness audit-raw-retention audit-youtube-coverage audit-comparison-scale gate-plan audit-distribution-scope audit-snapshots release-preflight gates check-venv

help:
        @echo "Targets: test | stage DECLARATION=<file> | adopt-all | platform-trends | youtube-aggregate | audit-new-runs | audit-adoption | audit-publication | audit-raw-completeness | audit-raw-retention | audit-youtube-coverage | audit-comparison-scale | gate-plan PLAN=<file> | audit-distribution-scope | audit-snapshots | release-preflight | gates"

# Local development runs through .venv (see docs/specs/validation-framework.md
# §2).  Fail fast with setup guidance when the interpreter is absent instead of
# surfacing `No such file or directory` from make or `ModuleNotFoundError` from
# a system-Python fallback.  No fallback is attempted here on purpose.
check-venv:
	@test -x "$(PYTHON)" || command -v "$(PYTHON)" >/dev/null 2>&1 || (echo "missing $(PYTHON)" >&2; echo "Run:" >&2; echo "  python3 -m venv .venv" >&2; echo "  .venv/bin/python -m pip install -e \".[dev]\"" >&2; echo "Then retry the make target." >&2; exit 2)

test: check-venv
	$(PYTHON) -m pytest -q

collect: check-venv
	$(PYTHON) -m collection.core.cli collect --workspace $(WORKSPACE) --datasets-root $(DATASETS) --config-dir $(CONFIG) --metadata-dir $(METADATA) $(ARGS)

stage: check-venv
	@test -n "$(DECLARATION)" || (echo "usage: make stage DECLARATION=<staging-declaration-v1 json>" && exit 2)
	$(PYTHON) -m collection.core.cli stage --declaration $(DECLARATION) --workspace $(WORKSPACE) --datasets-root $(DATASETS) --config-dir $(CONFIG) --metadata-dir $(METADATA) $(ARGS)

adopt-all: check-venv
	@for d in $(WORKSPACE)/.staging/*/; do \
		[ -d "$$d" ] || continue; \
		$(PYTHON) -m collection.core.cli adopt --staged "$$d" --workspace $(WORKSPACE) --datasets-root $(DATASETS) --config-dir $(CONFIG) --metadata-dir $(METADATA) || exit 1; \
	done
	@test -n "$$(ls -A $(WORKSPACE)/.staging/ 2>/dev/null)" || echo "no staged runs remaining"

platform-trends: check-venv
	$(PYTHON) -m processing.cli build-platform-trends --output-dir datasets/cannabinoid-platform-trends/data/processed

youtube-aggregate: check-venv
	$(PYTHON) -m processing.cli youtube-monthly-aggregate

audit-new-runs: check-venv
	$(PYTHON) -m validation.cli audit-new-runs

# The raw layer is machine-local (untracked), so this target has no committed
# snapshot: it answers about the checkout it runs in.
audit-adoption: check-venv
	$(PYTHON) -m validation.cli audit-adoption --datasets-root $(DATASETS)

audit-publication: check-venv
	$(PYTHON) -m validation.cli audit-publication

# Catalog/declaration/retention claims versus the raw layer of this checkout.
# Raw is machine-local, so this target answers about the checkout it runs in; it
# is a local pre-commit/production check, not a CI check.  A git_untracked run
# is reported as not_repository_retained, not missing; a git_tracked run stays
# strict.
audit-raw-completeness: check-venv
	$(PYTHON) -m validation.cli audit-raw-completeness --datasets-root $(DATASETS) --retention-dir $(RETENTION) $(ARGS)

# Raw retention is a Repository Storage (Git tracking) decision, not local raw
# existence.  This audit reads committed decisions, storage policies and the Git
# index only, so it runs on a clone without data/raw/.
audit-raw-retention: check-venv
	$(PYTHON) -m validation.cli audit-raw-retention --datasets-root $(DATASETS) --retention-dir $(RETENTION) $(ARGS)

# The declared query design is study metadata (liquid-only primary for this
# collection); --require-complete is opt-in because an inventory is not a gate.
audit-youtube-coverage: check-venv
	$(PYTHON) -m validation.cli audit-youtube-coverage $(ARGS)

# Common-scale comparison coverage: declared anchors (CBD/THC), missing anchor
# sets and legacy not-comparable runs.  Read-only and checkout-local (the raw
# layer is machine-local); --require-complete makes a missing compound run
# exit 1.  It never regenerates a committed audit snapshot.
audit-comparison-scale: check-venv
	$(PYTHON) -m validation.cli audit-comparison-scale $(ARGS)

# Pre-collection plan gate: structure + registry + the study's comparison
# anchors.  Same implementation as `make gates GATE=plan GATE_ARGS=<plan>`.
gate-plan: check-venv
	@test -n "$(PLAN)" || (echo "usage: make gate-plan PLAN=<plan.json>" && exit 2)
	bash scripts/validation/run-gates.sh plan $(PLAN) --datasets-root $(DATASETS)

# Report-only: changing the release slice is a release decision, not an audit
# side effect.  --strict makes drift findings exit non-zero.
audit-distribution-scope: check-venv
	$(PYTHON) -m validation.cli audit-distribution-scope $(ARGS)

# The guard runs before the first write.  It refuses only when a git_tracked
# run cannot be substantiated or a retention decision is invalid; a
# git_untracked run may be absent from this checkout.  The deterministic scope
# sidecar is written first so the following snapshots are generated under a
# declared scope, then the eleven checkout-local snapshots, then the postflight.
# It is safe in a partial checkout, but it never fabricates raw rows.
audit-snapshots: check-venv
	$(PYTHON) -m validation.cli snapshot-guard --phase preflight --datasets-root $(DATASETS) --retention-dir $(RETENTION) --state-file .staging/audit-snapshot-guard.json
	$(PYTHON) -m validation.cli audit-snapshot-scope --datasets-root $(DATASETS) --retention-dir $(RETENTION) --output docs/audits/snapshot-scope.json
	$(PYTHON) -m validation.cli contract-ledger --output docs/audits/contract-ledger.json
	$(PYTHON) -m validation.cli audit-queries --output docs/audits/g2-query-inventory.json
	$(PYTHON) -m processing.cli gt-summary --output docs/audits/gt-summary.json
	$(PYTHON) -m validation.cli audit-publication --output docs/audits/publication-contract.json
	$(PYTHON) -m validation.cli audit-temporal --output docs/audits/g3-temporal-inventory.json
	$(PYTHON) -m validation.cli audit-artifacts --output docs/audits/g4-storage-inventory.json
	$(PYTHON) -m validation.cli audit-legacy --output docs/audits/g5-legacy-runs.json
	$(PYTHON) -m validation.cli audit-provenance --output docs/audits/g5-provenance-assessment.json
	$(PYTHON) -m validation.cli audit-git-tracking --output docs/audits/g6-git-tracking-inventory.json
	$(PYTHON) -m validation.cli audit-private-catalog --output docs/audits/g6-private-catalog.json
	$(PYTHON) -m research.cli --repo-root . --datasets-root datasets audit-studies --output docs/audits/g7-study-inventory.json
	$(PYTHON) -m validation.cli snapshot-guard --phase postflight --audits-dir docs/audits --state-file .staging/audit-snapshot-guard.json

# Release preflight reuses the existing version-sync script and the version
# consistency test. It must pass before creating a release tag.
release-preflight: check-venv
	bash scripts/validation/validate-version-sync.sh
	$(PYTHON) -m pytest -q tests/validation/test_version_internal_consistency.py

gates: check-venv
	bash scripts/validation/run-gates.sh $(GATE) $(GATE_ARGS)
