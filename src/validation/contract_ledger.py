"""Contract ledger: the derived inventory of every declared contract.

Why this exists
---------------
``契約`` was used for five different kinds of declaration (schema contract,
registry document, interface contract, gate contract, decision record) and no
single place listed them.  A document could therefore be added, renamed or
dropped without any check noticing - which is how the publication layer drifted
away from the contracts (see ``docs/reports/20261015c-publication-refresh-plan.md``).
The ledger is that one list.

Derived, never typed twice
--------------------------
- schema contracts: ``validation.schema_registry.SCHEMA_REGISTRY`` /
  ``SCHEMA_VERSIONS``
- registry documents: the same file lists ``validate-registries`` validates
- decision records: the ``metadata/publication/*/`` review envelopes
- gaps: unset scope, undeclared versions and declarations that do not exist

Declared here (no machine-readable source exists)
-------------------------------------------------
- interface contracts (adapter / staging declaration / storage reader)
- gate contracts (plan / post-collection / coverage / comparability /
  publication / cross-study)

Ownership rules (``docs/specs/contracts.md`` §4): the *owner* is the bounded
context that produces the contract; *validation* is the enforcer of every
schema contract.  Gate contracts are owned by the *contract* context and
only executed / inspected by validation and research, so a gate declared
under ``src/validation/`` or ``src/research/`` still records
``owner == "contract"``.  ``tests/validation/test_contract_ledger.py``
fails when a schema is registered without a scope entry below, so the
ownership decision cannot be skipped when a contract is added.
"""

from __future__ import annotations

from pathlib import Path

from validation.schema_registry import SCHEMA_REGISTRY, SCHEMA_VERSIONS

LEDGER_SCHEMA_VERSION = "1.0.0"

#: Bounded contexts of the contract model (docs/specs/contracts.md).
#: ``collection`` and ``processing`` are the producing side the model names
#: 生産 (Production) - the pipeline; ``owner`` records the sub-context that
#: produces a contract, because that is what the declaration paths line up with
#: (contracts.md 3.1/3.2).  ``contract`` is the owner of gate contracts only:
#: the governance context that bundles the verdicts validation and research
#: execute and inspect (contracts.md §2/§4, AGENTS.md Domain Language).
CONTEXTS = ("collection", "storage", "validation", "research", "publication", "contract")

KIND_SCHEMA = "schema_contract"
KIND_INTERFACE = "interface_contract"
KIND_GATE = "gate_contract"

#: Closed set of gap kinds the ledger reports.  Every gap follows from a
#: declaration (scope, version or presence), so a new kind is a deliberate
#: change to this list.
GAP_KINDS = frozenset(
    {
        "scope_undeclared",
        "version_undeclared",
        "declaration_absent",
        "document_absent",
    }
)

#: Owner context and Cerberus group of every registered schema contract.
SCHEMA_SCOPE: dict[str, tuple[str, str]] = {
    # G1 collection pipeline: the source / collector / plan declarations.
    "source-registry-v1": ("collection", "G1"),
    "collector-registry-v1": ("collection", "G1"),
    "collection-plan-v1": ("collection", "P6"),
    # G2 query design.
    "query-registry-v1": ("collection", "G2"),
    "query-variants-v1": ("collection", "G2"),
    "query-variants-registry-v1": ("collection", "G2"),
    # G3 temporal window and coverage manifest (both evaluated by validation;
    # the manifest is the persisted coverage judgment, not a collection record).
    "temporal-window-v1": ("collection", "G3"),
    "coverage-manifest-v1": ("validation", "G3"),
    # G4 artifacts and storage.
    "artifact-manifest-v1": ("storage", "G4"),
    "artifact-registry-v1": ("storage", "G4"),
    # G5 provenance: the run record is produced by collection, the
    # transformation / evidence records by research.
    "collection-run-v1": ("collection", "G5"),
    "collection-run-v1-running": ("collection", "G5"),
    "transformation-v1": ("research", "G5"),
    "evidence-registry-v1": ("research", "G5"),
    # G6 storage classification and the publication decision.
    "storage-policy-registry-v1": ("storage", "G6"),
    "publication-decision-v1": ("publication", "G6"),
    # G6 release manifest (ISS-20261015-REL-014 validation-only slice).
    "release-manifest-v1": ("validation", "G6"),
    # G7 research objects.
    "study-registry-v1": ("research", "G7"),
    "measurement-registry-v1": ("research", "G7"),
    "research-view-v1": ("research", "G7"),
}

#: Interface contracts: what an implementation must provide at a boundary.
#: Built by :func:`_interface_contracts` so the versions are imported lazily:
#: ``collection.core`` imports ``validation.cli``, so a module-level import here
#: would close a cycle through ``validation.cli`` -> this module.
def _interface_contracts() -> tuple[dict, ...]:
    from collection.core.contracts import ADAPTER_CONTRACT_VERSION
    from collection.core.staging import (
        STAGING_DECLARATION_VERSION,
        STAGING_DRIVER_VERSION,
    )

    return (
        {
            "contract_id": "adapter-contract-v1",
            "group": "G1",
            "owner": "collection",
            "version": ADAPTER_CONTRACT_VERSION,
            "declared_at": "src/collection/core/contracts.py",
            "enforced_by": "collection.core.pipeline (adapter contract check)",
            "test": "tests/collection/test_adapter_contract.py",
        },
        {
            "contract_id": STAGING_DECLARATION_VERSION,
            "group": "P6",
            "owner": "collection",
            "version": STAGING_DRIVER_VERSION,
            "declared_at": "src/collection/core/staging.py",
            "enforced_by": "collection.core.cli stage",
            "test": "tests/collection/test_staging_driver.py",
        },
        {
            "contract_id": "storage-reader-contract-v1",
            "group": "G4",
            "owner": "storage",
            # Each reader declares ``reader_version``; the contract itself has
            # no version constant (recorded as a gap, not invented).
            "version": None,
            "declared_at": "src/storage/contracts.py",
            "enforced_by": "validation.storage_contract",
            "test": "tests/validation/test_storage_contract.py",
        },
    )

#: Gate contracts: the stage transition verdicts and where they are carried.
GATE_CONTRACTS: tuple[dict, ...] = (
    {
        "contract_id": "gate-plan",
        "group": "P6",
        "owner": "contract",
        "version": None,
        "declared_at": "src/validation/gates.py",
        "enforced_by": "validation.cli gate-plan",
        "test": "tests/validation/test_gates.py",
    },
    {
        "contract_id": "gate-run",
        "group": "P6",
        "owner": "contract",
        "version": None,
        "declared_at": "src/validation/gates.py",
        "enforced_by": "validation.cli gate-run",
        "test": "tests/validation/test_pipeline.py",
    },
    {
        "contract_id": "gate-coverage",
        "group": "G3",
        "owner": "contract",
        "version": None,
        "declared_at": "src/validation/coverage.py",
        "enforced_by": "validation.cli coverage-run",
        "test": "tests/validation/test_coverage.py",
    },
    {
        "contract_id": "gate-comparability-run",
        "group": "G1",
        "owner": "contract",
        "version": None,
        "declared_at": "src/validation/comparability.py",
        "enforced_by": "validation.cli compare-runs",
        "test": "tests/validation/test_comparability.py",
    },
    {
        "contract_id": "gate-comparability-study",
        "group": "G7",
        "owner": "contract",
        "version": None,
        "declared_at": "src/research/comparability.py",
        "enforced_by": "research.cli compare",
        "test": "tests/research/test_research_catalog.py",
    },
    {
        "contract_id": "gate-publication",
        "group": "G6",
        "owner": "contract",
        "version": None,
        "declared_at": "src/validation/publication_eligibility.py",
        "enforced_by": "validation.cli gate-publication",
        "test": "tests/validation/test_publication_gate.py",
    },
    {
        "contract_id": "gate-release-manifest",
        "group": "G6",
        "owner": "contract",
        "version": None,
        "declared_at": "src/validation/release_manifest.py",
        "enforced_by": "validation.cli validate-release-manifest",
        "test": "tests/validation/test_release_manifest.py",
    },
)


def _schema_contracts() -> list[dict]:
    contracts = []
    for schema_id in sorted(SCHEMA_REGISTRY):
        owner, group = SCHEMA_SCOPE.get(schema_id, ("", ""))
        contracts.append(
            {
                "contract_id": schema_id,
                "kind": KIND_SCHEMA,
                "group": group,
                "owner": owner,
                "version": SCHEMA_VERSIONS[schema_id],
                "declared_at": "src/validation/schemas/",
                "enforced_by": "validation.cli validate-all",
                "test": "tests/validation/test_schema_coverage.py",
            }
        )
    return contracts


def _registry_documents(repo_root: Path) -> list[dict]:
    """Every registry document the framework validates, plus the windows and
    publication envelopes that are discovered by path.

    ``REGISTRY_FILES`` / ``METADATA_REGISTRY_FILES`` are imported here rather
    than duplicated: they are the single declaration of what
    ``validate-registries`` covers.  The import is local because
    ``validation.cli`` imports this module.
    """

    from validation.cli import METADATA_REGISTRY_FILES, REGISTRY_FILES

    documents = []
    for base, entries in (
        (repo_root / "config", REGISTRY_FILES),
        (repo_root / "metadata", METADATA_REGISTRY_FILES),
    ):
        for relative, schema_id in entries:
            path = base / relative
            documents.append(
                {
                    "path": _relative(repo_root, path),
                    "kind": "registry_document",
                    "schema_contract": schema_id,
                    "exists": path.is_file(),
                }
            )
    for path in sorted((repo_root / "metadata" / "windows").glob("*.json")):
        documents.append(
            {
                "path": _relative(repo_root, path),
                "kind": "registry_document",
                "schema_contract": "temporal-window-v1",
                "exists": True,
            }
        )
    publication_root = repo_root / "metadata" / "publication"
    if publication_root.is_dir():
        for directory in sorted(publication_root.iterdir()):
            if not directory.is_dir():
                continue
            documents.append(
                {
                    "path": _relative(repo_root, directory) + "/",
                    "kind": "decision_record",
                    "schema_contract": "publication-decision-v1",
                    "exists": (directory / "decision.json").is_file(),
                }
            )
    return documents


def _relative(repo_root: Path, path: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _gaps(repo_root: Path, contracts: list[dict], documents: list[dict]) -> list[dict]:
    """Mechanically derived gaps - every entry follows from a declaration.

    These are not opinions: an undeclared owner/group, an undeclared contract
    version and a declared file that is not present are all facts about the
    declarations above.
    """

    gaps = []
    for contract in contracts:
        if not contract["owner"] or not contract["group"]:
            gaps.append(
                {
                    "kind": "scope_undeclared",
                    "contract_id": contract["contract_id"],
                    "detail": "owner context / Cerberus group not declared",
                }
            )
        if contract["version"] is None:
            gaps.append(
                {
                    "kind": "version_undeclared",
                    "contract_id": contract["contract_id"],
                    "detail": "contract version is not declared",
                }
            )
        if not (repo_root / contract["declared_at"]).exists():
            gaps.append(
                {
                    "kind": "declaration_absent",
                    "contract_id": contract["contract_id"],
                    "detail": contract["declared_at"],
                }
            )
    for document in documents:
        if not document["exists"]:
            gaps.append(
                {
                    "kind": "document_absent",
                    "contract_id": document["schema_contract"],
                    "detail": document["path"],
                }
            )
    assert {gap["kind"] for gap in gaps} <= GAP_KINDS
    return gaps


def build_contract_ledger(repo_root: Path) -> dict:
    """Build the ledger.  Read-only; the caller writes any report."""

    repo_root = Path(repo_root)
    contracts = _schema_contracts()
    for kind, entries in (
        (KIND_INTERFACE, _interface_contracts()),
        (KIND_GATE, GATE_CONTRACTS),
    ):
        contracts.extend(dict(entry, kind=kind) for entry in entries)
    contracts.sort(key=lambda entry: (entry["kind"], entry["contract_id"]))
    documents = _registry_documents(repo_root)
    gaps = _gaps(repo_root, contracts, documents)

    def count_by(field: str, entries) -> dict:
        counts: dict[str, int] = {}
        for entry in entries:
            counts[entry[field]] = counts.get(entry[field], 0) + 1
        return dict(sorted(counts.items()))

    return {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "generated_by": "validation.cli contract-ledger",
        "summary": {
            "contract_count": len(contracts),
            "document_count": len(documents),
            "by_kind": count_by("kind", contracts),
            "by_owner": count_by("owner", contracts),
            "by_group": count_by("group", contracts),
            "gap_count": len(gaps),
        },
        "contracts": contracts,
        "documents": documents,
        "gaps": gaps,
    }
