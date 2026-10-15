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

.PHONY: help test collect stage adopt-all platform-trends audit-new-runs audit-publication audit-snapshots gates

help:
	@echo "Targets: test | stage DECLARATION=<file> | adopt-all | platform-trends | audit-new-runs | audit-publication | audit-snapshots | gates"

test:
	$(PYTHON) -m pytest -q

collect:
	$(PYTHON) -m collection.core.cli collect --workspace $(WORKSPACE) --datasets-root $(DATASETS) --config-dir $(CONFIG) --metadata-dir $(METADATA) $(ARGS)

stage:
	@test -n "$(DECLARATION)" || (echo "usage: make stage DECLARATION=<staging-declaration-v1 json>" && exit 2)
	$(PYTHON) -m collection.core.cli stage --declaration $(DECLARATION) --workspace $(WORKSPACE) --datasets-root $(DATASETS) --config-dir $(CONFIG) --metadata-dir $(METADATA) $(ARGS)

adopt-all:
	@for d in $(WORKSPACE)/.staging/*/; do \
		[ -d "$$d" ] || continue; \
		$(PYTHON) -m collection.core.cli adopt --staged "$$d" --workspace $(WORKSPACE) --datasets-root $(DATASETS) --config-dir $(CONFIG) --metadata-dir $(METADATA) || exit 1; \
	done
	@test -n "$$(ls -A $(WORKSPACE)/.staging/ 2>/dev/null)" || echo "no staged runs remaining"

platform-trends:
	$(PYTHON) -m processing.cli build-platform-trends --output-dir datasets/cannabinoid-platform-trends/data/processed

audit-new-runs:
	$(PYTHON) -m validation.cli audit-new-runs

audit-publication:
	$(PYTHON) -m validation.cli audit-publication

audit-snapshots:
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

gates:
	bash scripts/validation/run-gates.sh $(GATE) $(GATE_ARGS)
