"""Architecture tests: the production / verification boundary (U5).

U5 (``docs/domain/context-map.md``, owner decision 2026-10-16): production
runs under the contracts and calls validation gates to enforce them, but it
owns neither the verdict rules, the reasons, nor the meaning of pass/fail.
Calling ``pre/post_collection_gate`` is workflow enforcement, not judging.

What these tests pin (T1-T4):

- T1: gate verdict modules (``src/validation/gates.py``,
  ``src/validation/pipeline.py``) do not depend on the production packages
  (``collection`` / ``processing``) - the P5 direction from
  ``docs/specs/collection-pipeline.md`` §3.3 and ``contracts.md`` §3.1.
  The scan covers the whole module tree (including deferred imports), not
  just top-level statements. Out of scope by design: the CLI orchestration
  layer (``validation.cli`` also reads ``storage.*`` - the U3 adjacency)
  and the ledger derivation (``contract_ledger._interface_contracts`` reads
  the declarations lazily; that read direction is explicitly allowed by
  ``contract.md``). P5 is about the verdict modules only.
- T2: production modules (``src/collection`` / ``src/processing``) define
  neither the validation-owned verdict vocabulary (``GateResult``,
  ``pre/post_collection_gate``, the ``_PRE/_POST_ACTIONS`` tables) nor the
  gate rules (the ``check_*`` / ``scan_*`` / ``verify_*`` verdict
  functions). ``L1Decision`` stays allowed: it is a carrier whose
  ``action`` value originates from the gate, not a second verdict
  definition. Likewise ``check_adapter_contract`` (production-owned
  interface contract) and ``scan_output_for_identifiers`` (privacy scan)
  are production code and intentionally absent from the forbidden list.
- T3: production enforces the gates it is allowed to call -
  ``run_collection`` reaches ``pre_collection_gate`` and ``_finalize``,
  ``adopt_staged`` reaches ``_finalize``, ``_finalize`` reaches
  ``evaluate_l1``, ``evaluate_l1`` reaches ``post_collection_gate``; only
  ``_finalize`` may translate a verdict into ``adopted`` / ``quarantined``
  (every other outcome is ``stopped`` refusal or ``staged`` output);
  ``stage_run`` stages only (structural checks, no verdict calls).
  ``_finalize`` consumes ``decision.action`` - the verdict vocabulary
  itself stays owned by validation, so the ``"catalog"`` /
  ``"quarantine"`` literals are deliberately not asserted here.
- T4: the production CLIs (``collection.core.cli``,
  ``processing.cli``) expose no gate-skip shaped option (``--skip*`` /
  ``--bypass*`` / ``--no-gate`` / ``--no-verify`` / ``--no-check*`` /
  ``--without-gate`` / ``--ignore-gate``). The parsers are introspected at
  runtime (imports stay inside the T4 test so T1-T3 remain stdlib-only
  with nothing imported).

Deliberately not pinned here (brittle string matching would be needed;
the operational rules live in ``docs/domain/contracts/production.md``):

- shell-level bypasses (a framework-external shell writing ``datasets/``
  directly) - caught after the fact by ``audit-new-runs`` (A3), not by an
  import scan;
- forbidden collection methods as flags - no such flag exists; the method
  allow-list lives in the registries plus the capability gate (tested in
  ``tests/collection/``);
- gate contract ownership (``owner == "contract"``) - owned and tested by
  the Contract context (``tests/validation/test_contract_ledger.py``,
  ``contracts.md`` §4).
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


# ---------------------------------------------------------------------------
# T2: production must not own or redefine the verdict internals (U5).
# ---------------------------------------------------------------------------

PRODUCTION_TREES = ("src/collection", "src/processing")

#: Verdict vocabulary owned by validation (``src/validation/gates.py``).
VERDICT_DEFINITIONS = frozenset(
    {
        "GateResult",
        "pre_collection_gate",
        "post_collection_gate",
        "_PRE_ACTIONS",
        "_POST_ACTIONS",
    }
)

#: Verdict rule functions owned by validation (``validation.semantic`` /
#: ``validation.windows`` / ``validation.integrity``).  Production calls
#: these; it must not define same-named functions of its own.
GATE_RULE_FUNCTIONS = frozenset(
    {
        "check_capability_gate",
        "check_missingness_consistency",
        "check_execution_consistency",
        "check_registry_references",
        "check_temporal_semantics",
        "check_schema_version",
        "check_query_registry_version",
        "check_plan_window_registry",
        "scan_for_secrets",
        "verify_artifact_manifest",
    }
)


def _production_definitions() -> dict[str, list[str]]:
    """Names bound in production modules that validation owns (T2)."""
    forbidden = VERDICT_DEFINITIONS | GATE_RULE_FUNCTIONS
    offenders: dict[str, list[str]] = {}
    for tree_rel in PRODUCTION_TREES:
        for path in sorted((REPO_ROOT / tree_rel).rglob("*.py")):
            bound: set[str] = set()
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                ):
                    bound.add(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            bound.add(target.id)
                elif isinstance(node, ast.AnnAssign) and isinstance(
                    node.target, ast.Name
                ):
                    bound.add(node.target.id)
            hits = sorted(bound & forbidden)
            if hits:
                offenders[path.relative_to(REPO_ROOT).as_posix()] = hits
    return offenders


def test_production_does_not_redefine_gate_verdicts() -> None:
    offenders = _production_definitions()
    assert offenders == {}, (
        "U5 violation: production must not own or redefine validation's "
        f"verdict vocabulary or gate rules: {offenders}"
    )


# ---------------------------------------------------------------------------
# T3: production enforces the gates it is allowed to call (U5).
# ---------------------------------------------------------------------------

PIPELINE_MODULE = "src/collection/core/pipeline.py"
INTEGRITY_MODULE = "src/collection/core/integrity.py"

#: Gate calls each production entry point must wire (presence pins the
#: enforcement; the verdict meaning stays with the gate).
REQUIRED_GATE_CALLS = {
    PIPELINE_MODULE: {
        "run_collection": {"pre_collection_gate", "validate_full", "_finalize"},
        "adopt_staged": {"_finalize"},
        "_finalize": {"evaluate_l1"},
        "stage_run": {"validate_full"},
    },
    INTEGRITY_MODULE: {
        "evaluate_l1": {"validate_full", "post_collection_gate"},
    },
}

#: ``stage_run`` is the producer side of the staging contract (spec §3.3):
#: it stages, ``adopt`` judges.  It must not reach any verdict call.
STAGE_RUN_FORBIDDEN_CALLS = frozenset(
    {"pre_collection_gate", "post_collection_gate", "evaluate_l1", "_finalize"}
)

#: Only ``_finalize`` may translate an L1 verdict into a terminal pipeline
#: outcome.  Every other path refuses (``stopped``) or stages (``staged``).
VERDICT_TRANSLATOR = "_finalize"
TERMINAL_VERDICT_ACTIONS = ("adopted", "quarantined")


def _calls_by_function(path: Path) -> dict[str, set[str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found: set[str] = set()
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    func = child.func
                    if isinstance(func, ast.Name):
                        found.add(func.id)
                    elif isinstance(func, ast.Attribute):
                        found.add(func.attr)
            calls[node.name] = found
    return calls


def _pipeline_result_actions(path: Path) -> dict[str, set[str]]:
    """``PipelineResult(action=...)`` literals per enclosing function."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    actions: dict[str, set[str]] = {}
    stack: list[str] = []

    def visit(node: ast.AST) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            stack.append(node.name)
            actions.setdefault(node.name, set())
            for child in ast.iter_child_nodes(node):
                visit(child)
            stack.pop()
            return
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "PipelineResult"
        ):
            for keyword in node.keywords:
                if (
                    keyword.arg == "action"
                    and isinstance(keyword.value, ast.Constant)
                    and isinstance(keyword.value.value, str)
                ):
                    actions[stack[-1]].add(keyword.value.value)
        for child in ast.iter_child_nodes(node):
            visit(child)

    visit(tree)
    return actions


def test_production_wires_the_validation_gates() -> None:
    missing: dict[str, dict[str, list[str]]] = {}
    for relative, expected in REQUIRED_GATE_CALLS.items():
        calls = _calls_by_function(REPO_ROOT / relative)
        for function, names in expected.items():
            absent = sorted(names - calls.get(function, set()))
            if absent:
                missing.setdefault(relative, {})[function] = absent
    assert missing == {}, (
        "U5 violation: production must call the validation gates it "
        f"enforces (fail closed): {missing}"
    )


def test_stage_run_produces_without_judging() -> None:
    calls = _calls_by_function(REPO_ROOT / PIPELINE_MODULE)
    reached = sorted(STAGE_RUN_FORBIDDEN_CALLS & calls.get("stage_run", set()))
    assert reached == [], (
        "U5 violation: stage_run is the producer side of the staging "
        f"contract and must not reach a verdict call: {reached}"
    )


def test_verdict_translation_lives_only_in_finalize() -> None:
    actions = _pipeline_result_actions(REPO_ROOT / PIPELINE_MODULE)
    for terminal in TERMINAL_VERDICT_ACTIONS:
        holders = sorted(
            function for function, values in actions.items() if terminal in values
        )
        assert holders == [VERDICT_TRANSLATOR], (
            "U5 violation: only _finalize may translate an L1 verdict into "
            f"{terminal!r} (found in {holders})"
        )
    for function in ("run_collection", "adopt_staged"):
        assert actions.get(function, set()) <= {"stopped"}, (
            f"U5 violation: {function} must only refuse or delegate "
            f"(found {sorted(actions.get(function, set()))})"
        )
    staged = actions.get("stage_run", set())
    assert "staged" in staged, "stage_run must produce a staged run"
    assert not (staged & set(TERMINAL_VERDICT_ACTIONS)), (
        f"U5 violation: stage_run must never adopt: {sorted(staged)}"
    )
    assert "action" in _consumed_verdict_attributes(REPO_ROOT / PIPELINE_MODULE), (
        "_finalize must consume the gate verdict (decision.action)"
    )


def _consumed_verdict_attributes(path: Path) -> set[str]:
    """Attribute names read on call results inside ``_finalize``."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    attributes: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
            node.name == VERDICT_TRANSLATOR
        ):
            for child in ast.walk(node):
                if isinstance(child, ast.Attribute):
                    attributes.add(child.attr)
    return attributes


# ---------------------------------------------------------------------------
# T4: no gate-skip shaped CLI flags on the production CLIs (U5).
# ---------------------------------------------------------------------------

#: Option substrings that would spell a gate bypass.  ``--force`` is out of
#: scope here: overwriting runs is refused behaviorally
#: (``RUN_ID_ALREADY_EXISTS``, covered in ``tests/collection/``).
FORBIDDEN_OPTION_TOKENS = (
    "skip",
    "bypass",
    "no-gate",
    "no-verify",
    "no-check",
    "without-gate",
    "ignore-gate",
)


def _all_options(parser) -> set[str]:
    """Every option string a (sub)parser registers (argparse API)."""
    options: set[str] = set()
    seen: set[int] = set()

    def walk(node) -> None:
        if id(node) in seen:
            return
        seen.add(id(node))
        for action in node._actions:
            options.update(getattr(action, "option_strings", ()))
            if action.__class__.__name__ == "_SubParsersAction":
                for choice in action.choices.values():
                    walk(choice)

    walk(parser)
    return options


def test_production_clis_offer_no_gate_skip_flags() -> None:
    from collection.core.cli import build_parser as build_collection_parser
    from processing.cli import build_parser as build_processing_parser

    offenders = {}
    for name, build in (
        ("collection", build_collection_parser),
        ("processing", build_processing_parser),
    ):
        hits = sorted(
            option
            for option in _all_options(build())
            if any(
                token in option.replace("_", "-").lower()
                for token in FORBIDDEN_OPTION_TOKENS
            )
        )
        if hits:
            offenders[name] = hits
    assert offenders == {}, (
        "U5 violation: production CLIs must not offer a gate bypass flag: "
        f"{offenders}"
    )
