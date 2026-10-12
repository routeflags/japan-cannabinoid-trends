"""G3 window compiler + pipeline integration contract tests (c.md §6, §8).

Covers the §14 requirements G3-T07..T10, T19, T20 and the pre-execution
verification semantics (P6): the absolute window is compiled and verified
before anything is collected, and refusals are loud (stable reason codes).
Offline only: recorded replay fixtures; live collection is never executed.
"""

import json
from pathlib import Path

from validation.pipeline import validate_full
from validation.windows import (
    CompiledWindow,
    check_window_compiler,
)

from collection.adapters import get_window_compiler
from collection.adapters.google_trends.compiler import GoogleTrendsWindowCompiler
from collection.core.cli import EXIT_CONFIG, EXIT_GATE, EXIT_OK
from collection.core.cli import main as collection_main
from collection.core.contracts import CollectionResult
from collection.core.pipeline import run_collection
from collection.core.registry import load_registries

from conftest import (
    FIXTURE_12M,
    REFERENCE_NOW,
    REFERENCE_NOW_ISO,
    REPO_CONFIG,
    REPO_METADATA,
    build_replay_adapter,
    load_json,
    make_plan,
    make_workspace,
)

WINDOW_12M = load_json(REPO_METADATA / "windows" / "2025-10-12_2026-10-12.json")
WINDOW_5Y = load_json(REPO_METADATA / "windows" / "2021-10-10_2026-10-12.json")

RUN_ID = "20261013T000000Z-google-trends-g3-window"


def _collect(registries, root, *, plan, run_id=RUN_ID, fixture=FIXTURE_12M, compiler=None):
    adapter = build_replay_adapter(registries, fixture)
    return run_collection(
        plan,
        adapter=adapter,
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
        run_id=run_id,
        now=REFERENCE_NOW,
        compiler=compiler,
    )


# ---------------------------------------------------------------------------
# compiler unit behaviour (c.md §6.3, §14 T07-T10)
# ---------------------------------------------------------------------------


def test_compiler_satisfies_the_common_contract():
    compiler = GoogleTrendsWindowCompiler()
    assert check_window_compiler(compiler) == []
    assert compiler.collector_id == "google-trends-mcp"


def test_compile_12m_window_resolves_to_an_absolute_half_open_interval():
    """The rolling conversion demo: ``today 12-m`` at a collection date
    becomes an absolute half-open interval; the window_id stays the absolute
    registry id (never a relative label)."""

    compiled = GoogleTrendsWindowCompiler().compile(
        WINDOW_12M, reference_time=REFERENCE_NOW, capabilities={"absolute_date_range": "unknown"}
    )
    assert compiled.parameters == {"timeframe": "today 12-m"}
    assert compiled.window_id == "2025-10-12_2026-10-12"
    assert compiled.collector_window_type == "relative_duration"
    assert compiled.reference_time == REFERENCE_NOW_ISO
    assert compiled.resolved_start == "2025-10-13T00:00:00Z"
    assert compiled.resolved_end_exclusive == "2026-10-13T00:00:00Z"
    # G3-T09/T10: no exactness claim while the boundary semantics are
    # unverified.
    assert compiled.exact is False
    assert compiled.boundary_semantics == "unverified"
    assert len(compiled.limitations) >= 2
    assert any("unverified" in text for text in compiled.limitations)


def test_compile_5y_window():
    compiled = GoogleTrendsWindowCompiler().compile(
        WINDOW_5Y, reference_time=REFERENCE_NOW, capabilities={}
    )
    assert compiled.parameters == {"timeframe": "today 5-y"}
    assert compiled.resolved_start == "2021-10-13T00:00:00Z"
    assert compiled.resolved_end_exclusive == "2026-10-13T00:00:00Z"


def test_compile_refuses_a_historical_window_of_a_supported_duration():
    """G3-T08: a 90-day window from 2023 has a matching duration (today 3-m)
    but the wrong era — the compiler must refuse instead of fetching recent
    data for it (P6)."""

    window = {
        "window_id": "2023-q1",
        "timezone": "UTC",
        "start": "2023-01-01T00:00:00Z",
        "end_exclusive": "2023-04-01T00:00:00Z",
    }
    try:
        GoogleTrendsWindowCompiler().compile(window, reference_time=REFERENCE_NOW)
    except Exception as error:  # noqa: BLE001 - asserted below
        assert error.codes == ["no_registered_timeframe_matches"]
    else:  # pragma: no cover - the compiler must refuse
        raise AssertionError("historical window must be refused")


def test_compile_refuses_a_window_without_a_registered_timeframe():
    window = {
        "window_id": "2024-2026",
        "timezone": "UTC",
        "start": "2024-10-13T00:00:00Z",
        "end_exclusive": "2026-10-13T00:00:00Z",
    }
    error = _expect_refusal(window)
    assert error.codes == ["no_registered_timeframe_matches"]


def _expect_refusal(window, **kwargs):
    try:
        GoogleTrendsWindowCompiler().compile(
            window, reference_time=kwargs.pop("reference_time", REFERENCE_NOW), **kwargs
        )
    except Exception as error:  # noqa: BLE001 - asserted by the caller
        return error
    raise AssertionError("compilation should have been refused")


def test_compile_requires_a_reference_time():
    """G3-T07: a relative period without its reference time fails."""

    error = _expect_refusal(WINDOW_12M, reference_time=None)
    assert error.codes == ["reference_time_missing"]


def test_compile_refuses_claimed_absolute_support_without_an_implementation():
    error = _expect_refusal(
        WINDOW_12M, capabilities={"absolute_date_range": "supported"}
    )
    assert error.codes == ["absolute_path_not_implemented"]


def test_compile_rejects_invalid_windows():
    reversed_window = {
        "start": "2026-10-12T00:00:00Z",
        "end_exclusive": "2025-10-12T00:00:00Z",
    }
    assert _expect_refusal(reversed_window).codes == ["window_invalid"]

    bad_timezone = {
        "timezone": "Not/AZone",
        "start": "2025-10-12T00:00:00Z",
        "end_exclusive": "2026-10-12T00:00:00Z",
    }
    assert _expect_refusal(bad_timezone).codes == ["timezone_unknown"]


# ---------------------------------------------------------------------------
# compile-window CLI (dry-run surface)
# ---------------------------------------------------------------------------


def _compile_window_args(root: Path, *extra):
    return [
        "compile-window",
        *extra,
        "--collector",
        "google-trends-mcp",
        "--reference-time",
        REFERENCE_NOW_ISO,
        "--config-dir",
        str(REPO_CONFIG),
        "--metadata-dir",
        str(REPO_METADATA),
        "--format",
        "json",
    ]


def test_compile_window_cli_reports_the_compiled_window(capsys):
    code = collection_main(
        _compile_window_args(Path("."), "--window-id", "2025-10-12_2026-10-12")
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_OK
    assert report["refused"] is False
    assert report["compiled"]["parameters"] == {"timeframe": "today 12-m"}
    assert report["compiled"]["resolved_start"] == "2025-10-13T00:00:00Z"
    assert report["compiled"]["exact"] is False
    assert "COMPILED" in captured.err


def test_compile_window_cli_refuses_a_historical_window(capsys, tmp_path):
    window_path = tmp_path / "window.json"
    window_path.write_text(
        json.dumps(
            {
                "temporal_contract_version": "1.0.0",
                "window_id": "2023-q1",
                "timezone": "UTC",
                "start": "2023-01-01T00:00:00Z",
                "end_exclusive": "2023-04-01T00:00:00Z",
                "granularity": "day",
            }
        ),
        encoding="utf-8",
    )
    code = collection_main(_compile_window_args(tmp_path, "--window", str(window_path)))
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_GATE
    assert report["refused"] is True
    assert report["reason_codes"] == ["no_registered_timeframe_matches"]


def test_compile_window_cli_unknown_collector_exit_2(capsys):
    code = collection_main(
        _compile_window_args(Path("."), "--window-id", "2025-10-12_2026-10-12")
        + []
    )
    assert code == EXIT_OK
    code = collection_main(
        [
            "compile-window",
            "--window-id",
            "2025-10-12_2026-10-12",
            "--collector",
            "no-such-collector",
            "--reference-time",
            REFERENCE_NOW_ISO,
            "--config-dir",
            str(REPO_CONFIG),
            "--metadata-dir",
            str(REPO_METADATA),
        ]
    )
    assert code == EXIT_CONFIG


# ---------------------------------------------------------------------------
# pipeline integration: verification before execution (fail closed)
# ---------------------------------------------------------------------------


def test_pipeline_stops_when_no_timeframe_represents_the_window(tmp_path, registries):
    root = make_workspace(tmp_path)
    plan = make_plan(start="2024-10-13T00:00:00Z", end_exclusive="2026-10-13T00:00:00Z")
    plan["window"].pop("window_id")  # keep the registry check out of the way
    result = _collect(registries, root, plan=plan)
    assert result.action == "stopped"
    assert [issue.code for issue in result.issues] == ["WINDOW_NOT_REPRESENTABLE"]
    assert not (root / ".staging").exists()


def test_pipeline_stops_on_a_declared_timeframe_conflict(tmp_path, registries):
    """P6: the plan's period parameter must agree with the compiled one; a
    mismatch never switches the period silently (G3-T20)."""

    root = make_workspace(tmp_path)
    plan = make_plan(timeframe="today 5-y")
    result = _collect(registries, root, plan=plan)
    assert result.action == "stopped"
    assert [issue.code for issue in result.issues] == ["WINDOW_TIMEFRAME_CONFLICT"]


def test_pipeline_stops_when_an_exact_window_is_required(tmp_path, registries):
    """c.md §6.2: with exact=false, a collection that requires a strict
    period must not run."""

    root = make_workspace(tmp_path)
    plan = make_plan()
    plan["window"]["exact_required"] = True
    result = _collect(registries, root, plan=plan)
    assert result.action == "stopped"
    assert [issue.code for issue in result.issues] == ["WINDOW_EXACTNESS_UNAVAILABLE"]


def test_pipeline_refuses_an_unregistered_window_id(tmp_path, registries):
    root = make_workspace(tmp_path)
    plan = make_plan(window_id="2099-01-01_2099-12-31")
    result = _collect(registries, root, plan=plan)
    assert result.action == "stopped"
    assert "WINDOW_UNREGISTERED" in [issue.code for issue in result.issues]


def test_pipeline_refuses_a_plan_window_that_drifted_from_the_registry(tmp_path, registries):
    root = make_workspace(tmp_path)
    plan = make_plan(end_exclusive="2026-10-05T00:00:00Z")
    result = _collect(registries, root, plan=plan)
    assert result.action == "stopped"
    assert "WINDOW_REGISTRY_MISMATCH" in [issue.code for issue in result.issues]


# ---------------------------------------------------------------------------
# provenance: requested / observed recorded, strict L1 still passes
# ---------------------------------------------------------------------------


def test_compiled_provenance_is_recorded_and_passes_strict_l1(tmp_path, registries):
    root = make_workspace(tmp_path)
    plan = make_plan()
    del plan["query"]["timeframe"]  # the compiler derives it from the window
    result = _collect(registries, root, plan=plan)
    assert result.action == "adopted", [i.code for i in result.issues]

    document = load_json(Path(result.final_dir) / "run_metadata.json")
    provenance = document["temporal_provenance"]
    assert provenance["window_id"] == "2025-10-12_2026-10-12"
    assert provenance["requested_start"] == "2025-10-12T00:00:00Z"
    assert provenance["requested_end_exclusive"] == "2026-10-12T00:00:00Z"
    assert provenance["reference_time"] == REFERENCE_NOW_ISO
    assert provenance["exact_window_match"] is False
    assert provenance["collector_window_type"] == "relative_duration"
    assert provenance["limitations"]
    assert provenance["submitted_parameters"]["timeframe"] == "today 12-m"
    # Observed = the bucket labels actually returned by the fixture series.
    assert provenance["observed_min_timestamp"] == "2025-10-12T00:00:00Z"
    assert provenance["observed_max_timestamp"] == "2026-10-04T00:00:00Z"

    outcome = validate_full(
        document,
        schema_id="collection-run-v1",
        registries=registries,
        base_dir=Path(result.final_dir),
        verify_artifacts=True,
    )
    assert outcome.valid is True, [i.to_dict() for i in outcome.issues]


# ---------------------------------------------------------------------------
# G3-T19: a new source applies the common contract without core changes
# ---------------------------------------------------------------------------


class _FakeWindowCompiler:
    collector_id = "fake-source-mcp"

    def compile(self, window, *, reference_time, capabilities=None):
        return CompiledWindow(
            collector_id=self.collector_id,
            window_id=window.get("window_id"),
            collector_window_type="absolute_datetime",
            parameters={"time": [window["start"], window["end_exclusive"]]},
            boundary_semantics="verified",
            exact=True,
            limitations=(),
            reference_time=reference_time.isoformat().replace("+00:00", "Z"),
            resolved_start=window["start"],
            resolved_end_exclusive=window["end_exclusive"],
            requested_start=window["start"],
            requested_end_exclusive=window["end_exclusive"],
        )


class _FakeAdapter:
    adapter_id = "fake-source-example@1"
    source_id = "fake-source"
    collector_id = "fake-source-mcp"
    version = "0.0.1"

    def __init__(self, capabilities):
        self._capabilities = dict(capabilities)

    def capabilities(self):
        return dict(self._capabilities)

    def validate_plan(self, plan):
        return []

    def collect(self, plan):
        return CollectionResult(
            raw={"ok": True},
            status="success",
            returned_count=1,
            observations=[{"term": plan["query"]["text"]}],
            submitted_parameters={"tool": "fake", "time": plan["query"]["time"]},
            temporal={"granularity": "day"},
        )

    def extract_observations(self, raw):
        return [{"term": "x"}]

    def describe_execution(self):
        return {"tool": "fake", "collection_mode": "test"}


def test_a_new_source_gets_the_common_temporal_contract(tmp_path):
    config = tmp_path / "config"
    metadata = tmp_path / "metadata"
    config.mkdir()
    metadata.mkdir()
    (config / "sources.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "sources": [{"source_id": "fake-source", "kind": "search"}],
            }
        ),
        encoding="utf-8",
    )
    capabilities = {"absolute_date_range": "supported"}
    (config / "collectors.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "collectors": [
                    {
                        "collector_id": "fake-source-mcp",
                        "source_id": "fake-source",
                        "adapter_id": "fake-source-example@1",
                        "status": "active",
                        "capabilities": capabilities,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    registries = load_registries(config, metadata)
    plan = {
        "plan_id": "plan-fake-001",
        "study_id": "fake-study",
        "source_id": "fake-source",
        "collector_id": "fake-source-mcp",
        "query_id": "fake-query",
        "query": {"text": "fake term"},
        "required_capabilities": ["absolute_date_range"],
        "window": {
            "start": "2026-10-01T00:00:00Z",
            "end_exclusive": "2026-10-08T00:00:00Z",
            "granularity": "day",
            "timezone": "UTC",
        },
        "purpose": "G3-T19 fictional source contract test",
    }
    workspace = tmp_path / "workspace"
    (workspace / "datasets" / "fake-study").mkdir(parents=True)

    compiler = _FakeWindowCompiler()
    assert check_window_compiler(compiler) == []
    assert get_window_compiler("fake-source-mcp") is None  # dispatch not pre-registered

    adapter = _FakeAdapter(capabilities)
    result = run_collection(
        plan,
        adapter=adapter,
        workspace_root=workspace,
        datasets_root=workspace / "datasets",
        registries=registries,
        run_id="20261013T000000Z-fake-source-contract",
        now=REFERENCE_NOW,
        compiler=compiler,
    )
    assert result.action == "adopted", [i.to_dict() for i in result.issues]
    document = load_json(Path(result.final_dir) / "run_metadata.json")
    provenance = document["temporal_provenance"]
    assert provenance["reference_time"] == REFERENCE_NOW_ISO
    assert provenance["exact_window_match"] is True
    assert provenance["collector_window_type"] == "absolute_datetime"
    assert document["query_provenance"]["submitted_query"] == "fake term"
