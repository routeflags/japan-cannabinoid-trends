"""Architecture test: gate verdict modules must not depend on production code (P5).

P5 (``docs/specs/collection-pipeline.md`` §3.3, ``contracts.md`` §3.1): the gate must
not depend on the code that generates its own input.  This test pins the checkable
direction with an AST scan (stdlib only, nothing imported):
``src/validation/gates.py`` and ``src/validation/pipeline.py`` must not import the
production packages (``collection`` / ``processing``) at module level.

Allowed by ``context-map.md`` U5: the reverse direction -- production calling
``pre/post_collection_gate`` -- is workflow enforcement.  Production must follow the
contracts, call validation gates, and stop/quarantine when they fail.  That does not
make production the owner of the gate rules, reasons, or verdict meanings.
Function-level imports (e.g. ``contract_ledger._interface_contracts``) are outside this scan by construction and remain documented at their call sites.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_MODULES = (
    "src/validation/gates.py",
    "src/validation/pipeline.py",
)
PRODUCTION_PACKAGES = ("collection", "processing")


def _absolute_top_levels(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    top_levels: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            top_levels.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                top_levels.add(node.module.split(".")[0])
    return top_levels


def test_gate_verdict_modules_do_not_depend_on_production() -> None:
    offenders = {}
    for relative in GATE_MODULES:
        imported = _absolute_top_levels(REPO_ROOT / relative)
        production = sorted(p for p in PRODUCTION_PACKAGES if p in imported)
        if production:
            offenders[relative] = production
    assert offenders == {}, (
        "P5 violation: gate verdict modules must not depend on production code: "
        f"{offenders}"
    )
