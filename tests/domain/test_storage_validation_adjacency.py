"""Architecture tests: the validation <-> storage adjacency (U3).

U3 (``docs/domain/context-map.md`` §4, owner decision 2026-10-16): storage
and validation are adjacent. Validation may read storage's public interface
to check the storage conditions; the inventory may reuse the ``sha256_file``
hash primitive. The inventory must not own or reference gates / verdicts /
CLI / judgments, and validation must not create or modify stored artifacts.

What these tests pin (A1-A2, allowlist over the two measured files only):

- A1: ``src/validation/storage_contract.py`` reads storage modules only
  from the allowlist (``storage.contracts`` / ``storage.readers`` /
  ``storage.registry`` / ``storage.sniff``), and all four edges are present.
- A2: ``src/storage/inventory.py`` reuses from validation only
  ``validation.integrity.sha256_file``, and that edge is present. Module
  imports (``import validation.integrity``) and symbol imports
  (``from validation.integrity import sha256_file``) are both recognized;
  ``import *`` is not accepted.

Deliberately not pinned here (left for a later task after surveying the
existing examples):

- a tree-wide scan of ``src/validation/**`` and ``src/storage/**`` - only
  the two measured files above are covered;
- the production/research -> storage edges (``staging.py``,
  ``views.py``) - separate edges, not this protocol;
- ``validation.cli``'s ``storage.*`` reads - CLI orchestration is out of
  scope (same convention as T1 in
  ``test_production_verification_separation.py``).
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

STORAGE_CONTRACT_FILE = "src/validation/storage_contract.py"
INVENTORY_FILE = "src/storage/inventory.py"

#: U3 §4 allowlist: the storage packages ``validation.storage_contract``
#: may read. Submodules count as their parent package edge (e.g.
#: ``storage.readers.csv`` is the ``storage.readers`` edge).
ALLOWED_STORAGE_MODULES = frozenset(
    {
        "storage.contracts",
        "storage.readers",
        "storage.registry",
        "storage.sniff",
    }
)

#: U3 §4 allowlist: the only validation reuse ``storage.inventory`` may make.
ALLOWED_INVENTORY_VALIDATION_MODULE = "validation.integrity"
ALLOWED_INVENTORY_VALIDATION_SYMBOLS = frozenset({"sha256_file"})

#: Modules the inventory must never touch directly. Anything outside the A2
#: allowlist already fails; these exist so the failure message says *why*
#: the edge is dangerous (U3 §4 prohibition).
FORBIDDEN_INVENTORY_VALIDATION_MODULES = (
    "validation.gates",
    "validation.pipeline",
    "validation.storage_contract",
    "validation.cli",
)

#: Verdict vocabulary owned by validation (cf. T2 in
#: ``test_production_verification_separation.py``). The inventory must not
#: import these from anywhere.
FORBIDDEN_INVENTORY_VERDICT_SYMBOLS = frozenset(
    {
        "GateResult",
        "pre_collection_gate",
        "post_collection_gate",
        "validate_full",
        "evaluate_l1",
    }
)


def _imports(path: Path) -> list[tuple[str, str | None, int]]:
    """``(module, symbol, lineno)`` for every absolute import in the file.

    ``symbol`` is None for a module import (``import x.y``) and the imported
    name for a symbol import (``from x.y import name``). The whole tree is
    walked so deferred (function-level) imports are covered too. Relative
    imports stay inside the package and are out of scope here.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[tuple[str, str | None, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append((alias.name, None, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.level != 0 or not node.module:
                continue
            for alias in node.names:
                found.append((node.module, alias.name, node.lineno))
    return found


def _storage_edge(module: str, symbol: str | None) -> str | None:
    """Normalize one import to the ``storage.<package>`` edge it uses."""
    if module == "storage":
        if symbol is None or symbol == "*":
            return "storage"
        return f"storage.{symbol.split('.')[0]}"
    if module == "storage" or module.startswith("storage."):
        return ".".join(module.split(".")[:2])
    return None


def _validation_edge(module: str, symbol: str | None) -> tuple[str, str | None]:
    """Normalize ``from validation import <submodule>`` to module form."""
    if module == "validation" and symbol not in (None, "*"):
        return (f"validation.{symbol.split('.')[0]}", None)
    return (module, symbol)


def test_storage_contract_storage_imports_are_allowlisted() -> None:
    observed: dict[str, list[int]] = {}
    for module, symbol, lineno in _imports(REPO_ROOT / STORAGE_CONTRACT_FILE):
        edge = _storage_edge(module, symbol)
        if edge is not None:
            observed.setdefault(edge, []).append(lineno)
    extra = sorted(set(observed) - ALLOWED_STORAGE_MODULES)
    missing = sorted(ALLOWED_STORAGE_MODULES - set(observed))
    assert extra == [] and missing == [], (
        "U3 violation: validation.storage_contract may read only the "
        f"allowlisted storage modules {sorted(ALLOWED_STORAGE_MODULES)}: "
        f"extra={extra} (lines { {e: observed[e] for e in extra} }), "
        f"missing={missing} (an intentionally removed edge needs a doc "
        "update in U3-validation-storage-dependency.md §4 plus this test)"
    )


def test_inventory_validation_imports_are_allowlisted() -> None:
    observed = [
        (*_validation_edge(module, symbol), lineno)
        for module, symbol, lineno in _imports(REPO_ROOT / INVENTORY_FILE)
        if module == "validation" or module.startswith("validation.")
    ]
    forbidden_modules = sorted(
        {module for module, _, _ in observed if module == "validation" or any(
            module == prefix or module.startswith(prefix + ".")
            for prefix in FORBIDDEN_INVENTORY_VALIDATION_MODULES
        )}
    )
    assert forbidden_modules == [], (
        "U3 violation: storage.inventory must not reference validation "
        f"gates / verdicts / CLI / judgments: {forbidden_modules}"
    )
    forbidden_symbols = sorted(
        {symbol for _, symbol, _ in observed if symbol in FORBIDDEN_INVENTORY_VERDICT_SYMBOLS}
    )
    assert forbidden_symbols == [], (
        "U3 violation: storage.inventory must not import validation's "
        f"verdict vocabulary: {forbidden_symbols}"
    )
    outside = sorted(
        {f"{module}:{symbol}" for module, symbol, _ in observed if not (
            module == ALLOWED_INVENTORY_VALIDATION_MODULE
            and (symbol is None or symbol in ALLOWED_INVENTORY_VALIDATION_SYMBOLS)
        )}
    )
    assert outside == [], (
        "U3 violation: storage.inventory may reuse only "
        f"{ALLOWED_INVENTORY_VALIDATION_MODULE}."
        f"{sorted(ALLOWED_INVENTORY_VALIDATION_SYMBOLS)} from validation: "
        f"{outside}"
    )
    assert any(
        module == ALLOWED_INVENTORY_VALIDATION_MODULE for module, _, _ in observed
    ), (
        "U3 violation: the allowed edge "
        f"{ALLOWED_INVENTORY_VALIDATION_MODULE}."
        f"{sorted(ALLOWED_INVENTORY_VALIDATION_SYMBOLS)} is missing from "
        f"{INVENTORY_FILE} (an intentionally removed edge needs a doc "
        "update in U3-validation-storage-dependency.md §4 plus this test)"
    )
