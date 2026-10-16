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
#   make audit-new-runs               new-run contract audit (read-only)
#   make audit-snapshots              regenerate tracked docs/audits snapshots
#   make gates                        validation gate scripts

PYTHON ?= .venv/bin/python
WORKSPACE ?= .
DATASETS ?= datasets
CONFIG ?= config
METADATA ?= metadata
GATE ?= registries
GATE_ARGS ?=

.PHONY: help test collect stage adopt-all platform-trends audit-new-runs audit-publication audit-snapshots gates check-venv

help:
	@echo "Targets: test | stage DECLARATION=<file> | adopt-all | platform-trends | audit-new-runs | audit-publication | audit-snapshots | gates"

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

audit-new-runs: check-venv
	$(PYTHON) -m validation.cli audit-new-runs

audit-publication: check-venv
	$(PYTHON) -m validation.cli audit-publication

audit-snapshots: check-venv
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

gates: check-venv
	bash scripts/validation/run-gates.sh $(GATE) $(GATE_ARGS)
