"""Validation CLI (Phase 5, h.md §13 / §14).

Commands
--------
- ``validate``            one file against one registered schema
- ``validate-study``      every ``run_metadata.json`` under a study
- ``validate-registries`` every known registry file that exists
- ``validate-all``        registries + all studies (JSON report for CI)
- ``gate-plan``           pre-collection gate for a collection plan (P6-1)
- ``gate-run``            post-collection L1 gate: catalog vs quarantine (P6-2)
- ``compare-runs``        L2 run-level comparability (G1 §12, C1-C3; G3 T6/T7
                          with ``--coverage-a`` / ``--coverage-b``)
- ``coverage-run``        G3 §9 coverage manifest for one run (on-demand
                          report; explicit ``--persist`` writes the canonical
                          ``<run-dir>/coverage-manifest.json``)
- ``audit-temporal``      non-destructive G3 §15 temporal inventory
- ``classify-query``      Stage-1 query-string classification (G2 §8)
- ``compare-queries``     definition-level query comparability (G2 §9)
- ``audit-queries``       non-destructive G2 query inventory (b.md §13)
- ``audit-legacy``        non-destructive G5 legacy audit (Phase 8)
- ``audit-provenance``    non-destructive G5 provenance assessment (§9/§10)
- ``audit-artifacts``     non-destructive G4 §16 artifact inventory
- ``audit-git-tracking``  non-destructive G6 §15 git tracking inventory
- ``audit-private-catalog`` non-destructive G6 §13 private data boundary catalog
- ``audit-apify-evidence`` read-only PRV-013 checklist: the Apify cloud evidence
                        request list against its source declaration (never calls
                        Apify; exit 0 means honest, not complete)
- ``audit-adoption``      the adoption backlog: every raw run directory and the
                        state of the metadata a declaration needs
- ``contract-ledger``     the derived inventory of every declared contract
- ``audit-publication``   the publication contract (record-only; see the module)
- ``gate-publication``    record-only G6 §10 publication eligibility gate
- ``validate-release-manifest``
                        read-only G6 release-manifest check: a clean archive
                        against a ``release-manifest-v1`` document (never
                        publishes or uploads)

Exit codes (h.md §13)
---------------------
==========  =============================================
 code        meaning
==========  =============================================
0           validation passed
1           data validation failure
2           schema / configuration error (unknown schema, malformed
            registry, legacy profile not allowed for this run)
3           file I/O error (target unreadable, artifact/manifest missing)
==========  =============================================

Precedence when several classes occur in one invocation: 2 > 3 > 1 > 0.
The CLI itself never modifies files except the ``--output`` report path and
the explicit opt-in persist targets (``coverage-run --persist`` writes only
the canonical ``<run-dir>/coverage-manifest.json``).

Streams: machine-readable JSON goes to stdout (or ``--output``); human-
readable lines go to stderr (h.md §13 "エラー内容は標準エラー出力またはJSON
レポートへ出力する").
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validation.adoption import build_adoption_backlog
from validation.apify_evidence import audit_apify_evidence
from validation.boundary import build_boundary_report
from validation.comparability import compare_runs
from validation.coverage import (
    build_temporal_inventory,
    coverage_manifest_path_for_run,
    evaluate_coverage,
    write_coverage_manifest,
)
from validation.contract_ledger import build_contract_ledger
from validation.gates import post_collection_gate, pre_collection_gate
from validation.g6_inventory import build_git_tracking_inventory
from validation.integrity import IO_ISSUE_CODES, sha256_file
from validation.issues import audit_issues
from validation.new_runs import audit_new_runs
from validation.private_catalog import build_private_catalog
from validation.publication_eligibility import evaluate_eligibility
from validation.x_identity import audit_x_identity
from validation.legacy import LegacyProfileNotAllowed, audit_record
from validation.pipeline import validate_full
from validation.provenance import (
    build_provenance_assessment,
    check_evidence_registry,
    find_duplicate_run_ids,
)
from validation.publication_contract import build_publication_contract_report
from validation.query_semantics import (
    build_query_inventory,
    check_query_registry,
    check_query_variants,
    classify_query_text,
    compare_query_definitions,
    load_compound_vocabulary,
)
from validation.reporting import (
    VALIDATION_VERSION,
    Issue,
    Report,
    ReportBundle,
    dump_json,
)
from validation.release_manifest import (
    SCHEMA_ID as RELEASE_MANIFEST_SCHEMA_ID,
    check_release_manifest,
    structural_problems as release_manifest_structural_problems,
)
from validation.schema_registry import get_schema, get_schema_version
from validation.semantic import (
    Registries,
    check_measurement_registry,
    check_study_registry,
    check_temporal_semantics,
    scan_for_secrets,
)
from validation.storage_contract import check_artifact_registry
from validation.windows import (
    check_window_registry_files,
    load_window_documents,
)

from storage.inventory import build_artifact_inventory
from storage.registry import ArtifactRegistry

__all__ = ["main"]

EXIT_OK = 0
EXIT_DATA = 1
EXIT_CONFIG = 2
EXIT_IO = 3

#: Precedence used when one invocation produces several failure classes
#: (documented in the module docstring): 2 > 3 > 1 > 0.
_EXIT_PRECEDENCE = {
    EXIT_OK: 0,
    EXIT_DATA: 1,
    EXIT_IO: 2,
    EXIT_CONFIG: 3,
}

#: registry file -> schema ID (P5-3; missing files are skipped with a note)
REGISTRY_FILES = (
    ("sources.json", "source-registry-v1"),
    ("collectors.json", "collector-registry-v1"),
    ("storage-policies.json", "storage-policy-registry-v1"),
)

METADATA_REGISTRY_FILES = (
    ("queries/query-registry.json", "query-registry-v1"),
    ("queries/query-variants.json", "query-variants-registry-v1"),
    ("studies/study-registry.json", "study-registry-v1"),
    ("measurements/measurement-registry.json", "measurement-registry-v1"),
    ("artifacts/artifact-registry.json", "artifact-registry-v1"),
    # G5 evidence registry (e.md §11): machine-readable provenance evidence.
    ("provenance/evidence-registry.json", "evidence-registry-v1"),
)


def _err(message: str) -> None:
    print(message, file=sys.stderr)


def _load_json(path: Path):
    """Load JSON or raise OSError/JSONDecodeError (callers map to exit 3)."""
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _load_optional_json(path: Path):
    """Load an existing registry file; missing -> None, malformed -> error."""
    if not path.is_file():
        return None
    try:
        return _load_json(path)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ConfigError(f"registry file cannot be read as JSON: {path}") from error


class ConfigError(Exception):
    """Schema / configuration problem (exit code 2)."""


def _load_query_vocabulary(metadata_dir: Path):
    """Load the compound taxonomy for query semantic checks (G2).

    Returns ``None`` when the taxonomy file is absent (the same convention as
    a missing registry: the corresponding cross-checks are disabled instead
    of producing false failures).  An unreadable taxonomy is a configuration
    error.
    """
    path = Path(metadata_dir) / "taxonomy" / "compound-taxonomy.skos.jsonld"
    if not path.is_file():
        return None
    try:
        return load_compound_vocabulary(path)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ConfigError(
            f"compound taxonomy cannot be read as JSON-LD: {path}"
        ) from error


def load_registries(config_dir: Path, metadata_dir: Path) -> Registries:
    """Build the reference-check registries from present files only.

    Returns an empty ``Registries`` while a registry file does not exist yet;
    reference checks are then skipped instead of failing.  The query variants
    bundle and the query-registry version ride along with the query registry
    (G2 vertical slice); the G3 window documents ride along the same way.
    """
    try:
        window_documents = load_window_documents(Path(metadata_dir) / "windows")
    except ValueError as error:
        raise ConfigError(str(error)) from error
    return Registries.from_documents(
        source_registry=_load_optional_json(config_dir / "sources.json"),
        collector_registry=_load_optional_json(config_dir / "collectors.json"),
        query_registry=_load_optional_json(
            metadata_dir / "queries" / "query-registry.json"
        ),
        query_variants_registry=_load_optional_json(
            metadata_dir / "queries" / "query-variants.json"
        ),
        study_registry=_load_optional_json(
            metadata_dir / "studies" / "study-registry.json"
        ),
        window_documents=window_documents,
        artifact_registry=_load_optional_json(
            metadata_dir / "artifacts" / "artifact-registry.json"
        ),
    )


def _exit_code(issues) -> int:
    if any(issue.code in IO_ISSUE_CODES for issue in issues):
        return EXIT_IO
    if any(issue.severity == "error" for issue in issues):
        return EXIT_DATA
    return EXIT_OK


def _exit_code_for_reports(reports) -> int:
    all_issues = [issue for report in reports for issue in report.issues]
    return _exit_code(all_issues)


def _human_lines(report: Report) -> list[str]:
    verdict = "OK" if report.valid else "FAIL"
    lines = [f"{verdict} {report.profile} {report.schema_id} {report.target}"]
    if report.legacy is not None:
        lines.append(
            f"  legacy_audit run_id={report.legacy.get('run_id')} "
            f"status={report.legacy.get('status')} "
            f"missing_fields={len(report.legacy.get('missing_fields', ()))}"
        )
    for issue in report.issues:
        lines.append(f"  [{issue.code}] {issue.path}: {issue.message}")
    summary = {}
    for issue in report.issues:
        summary[issue.severity] = summary.get(issue.severity, 0) + 1
    if summary:
        lines.append(
            "  issues: "
            + ", ".join(f"{key}={summary[key]}" for key in sorted(summary))
        )
    return lines


def _emit(
    document: dict,
    *,
    fmt: str,
    output: str | None,
    human_lines: list[str],
    human_stream=None,
) -> None:
    """Emit the report: JSON to stdout / --output, human lines to stderr.

    ``human_stream`` is resolved at call time (tests replace ``sys.stderr``).
    """
    if fmt == "json":
        text = dump_json(document)
        if output:
            path = Path(output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
    stream = human_stream if human_stream is not None else sys.stderr
    for line in human_lines:
        print(line, file=stream)


def _write_output(output: str, document: dict) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_json(document), encoding="utf-8")


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


def cmd_validate(args) -> int:
    try:
        get_schema(args.schema)  # unknown schema -> config error before reading
    except ValueError as error:
        _err(str(error))
        return EXIT_CONFIG

    target = Path(args.file)
    try:
        document = _load_json(target)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        _err(f"cannot read input file: {target} ({error.__class__.__name__})")
        return EXIT_IO

    try:
        registries = load_registries(
            Path(args.config_dir), Path(args.metadata_dir)
        )
    except ConfigError as error:
        _err(str(error))
        return EXIT_CONFIG

    try:
        outcome = validate_full(
            document,
            schema_id=args.schema,
            target=str(target),
            profile=args.profile,
            registries=registries if registries.any() else None,
            base_dir=target.parent,
            verify_artifacts=args.verify_artifacts,
        )
    except LegacyProfileNotAllowed as error:
        _err(str(error))
        return EXIT_CONFIG
    except ValueError as error:
        _err(str(error))
        return EXIT_CONFIG

    report = outcome.to_report()
    code = _exit_code(outcome.issues)
    _emit(
        report.to_dict(),
        fmt=args.format,
        output=args.output,
        human_lines=_human_lines(report),
    )
    return code


# ---------------------------------------------------------------------------
# validate-study / validate-all
# ---------------------------------------------------------------------------


def _study_dirs(datasets_root: Path):
    if not datasets_root.is_dir():
        return []
    return sorted(
        path
        for path in datasets_root.iterdir()
        if path.is_dir()
    )


def _study_run_files(study_dir: Path):
    return sorted(study_dir.rglob("run_metadata.json"))


def _validate_study(study_id: str, args) -> tuple[ReportBundle, int]:
    datasets_root = Path(args.datasets_root)
    study_dir = datasets_root / study_id
    if not study_dir.is_dir():
        return (
            ReportBundle(
                profile=args.profile,
                note=f"no study directory found: {study_dir}",
            ),
            EXIT_OK,
        )

    files = _study_run_files(study_dir)
    if not files:
        return (
            ReportBundle(
                profile=args.profile,
                note=f"no run_metadata.json found under {study_dir}",
            ),
            EXIT_OK,
        )

    try:
        registries = load_registries(
            Path(args.config_dir), Path(args.metadata_dir)
        )
    except ConfigError as error:
        _err(str(error))
        return ReportBundle(profile=args.profile), EXIT_CONFIG

    bundle = ReportBundle(profile=args.profile)
    pending: list = []
    for path in files:
        try:
            document = _load_json(path)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            bundle.reports.append(
                Report(
                    schema_id=args.schema,
                    target=str(path),
                    valid=False,
                    issues=[
                        _io_issue("TARGET_FILE_UNREADABLE", str(path))
                    ],
                )
            )
            continue
        try:
            outcome = validate_full(
                document,
                schema_id=args.schema,
                target=str(path),
                profile=args.profile,
                registries=registries if registries.any() else None,
                base_dir=path.parent,
                verify_artifacts=True,
            )
        except LegacyProfileNotAllowed as error:
            _err(f"{path}: {error}")
            return bundle, EXIT_CONFIG
        pending.append((outcome.to_report(), outcome.profile, document))

    _apply_run_id_uniqueness(pending, schema_id=args.schema)
    for report, _, _ in pending:
        bundle.reports.append(report)

    return bundle, _exit_code_for_reports(bundle.reports)


def _apply_run_id_uniqueness(pending, *, schema_id: str) -> None:
    """G5 §8.2 P01: flag duplicate run_ids across strict runs (in place).

    Only ``collection-run-v1`` strict reports participate: legacy-audit
    reports describe frozen history (duplicates there, if any, belong to a
    new audit, not to this gate), and unreadable files carry no identity.
    Each additional claimant gets ``RUN_ID_DUPLICATE`` (error) and its
    report flips to invalid.
    """
    if schema_id != "collection-run-v1":
        return
    entries = []
    for report, profile, document in pending:
        if profile != "strict":
            continue
        run_id = document.get("run_id") if isinstance(document, dict) else None
        entries.append((report, run_id))
    duplicates = find_duplicate_run_ids(
        ((report.target, run_id) for report, run_id in entries)
    )
    if not duplicates:
        return
    try:
        version = get_schema_version(schema_id)
    except ValueError:
        version = ""
    for report, run_id in entries:
        if run_id in duplicates:
            report.issues.append(
                Issue(
                    code="RUN_ID_DUPLICATE",
                    path="/run_id",
                    severity="error",
                    message="run_id is claimed by more than one run in this study",
                    rule="run_identity",
                    schema_version=version,
                )
            )
            report.issues.sort(key=lambda issue: issue.sort_key())
            report.valid = False


def _io_issue(code: str, target: str):
    return Issue(
        code=code,
        path="",
        severity="error",
        message=f"file cannot be read: {target}",
        rule="io",
    )


def cmd_validate_study(args) -> int:
    bundle, code = _validate_study(args.study, args)
    _emit(
        bundle.to_dict(),
        fmt=args.format,
        output=args.output,
        human_lines=_bundle_lines(bundle),
    )
    return code


def _bundle_lines(bundle: ReportBundle) -> list[str]:
    lines: list[str] = []
    if bundle.note:
        lines.append(f"NOTE {bundle.note}")
    for report in bundle.reports:
        lines.extend(_human_lines(report))
    lines.append(
        f"summary: {len(bundle.reports)} target(s), "
        f"{'valid' if bundle.valid else 'invalid'}"
    )
    return lines


def cmd_validate_all(args) -> int:
    bundle = ReportBundle(profile=args.profile)
    codes: list[int] = []

    registry_reports, registry_code = _validate_registries(args)
    for report in registry_reports.reports:
        bundle.reports.append(report)
    codes.append(registry_code)

    datasets_root = Path(args.datasets_root)
    if datasets_root.is_dir():
        for study_dir in _study_dirs(datasets_root):
            study_bundle, code = _validate_study(study_dir.name, args)
            bundle.reports.extend(study_bundle.reports)
            codes.append(code)

    if not bundle.reports:
        bundle.note = "no validation targets found"

    # None of the target failures is fatal to the others: report everything
    # and keep the highest-precedence exit code (2 > 3 > 1 > 0).
    exit_code = EXIT_OK
    for code in codes:
        if _EXIT_PRECEDENCE[code] > _EXIT_PRECEDENCE[exit_code]:
            exit_code = code

    _emit(
        bundle.to_dict(),
        fmt=args.format,
        output=args.output,
        human_lines=_bundle_lines(bundle),
    )
    return exit_code


# ---------------------------------------------------------------------------
# validate-registries
# ---------------------------------------------------------------------------


def _validate_registries(args) -> tuple[ReportBundle, int]:
    config_dir = Path(args.config_dir)
    metadata_dir = Path(args.metadata_dir)
    # ``validate-registries`` has no --profile option; registry documents are
    # always validated strictly.
    bundle = ReportBundle(profile=getattr(args, "profile", "strict"))

    # G2 sibling documents / taxonomy for the query-registry semantic checks.
    # A file that cannot be loaded here is reported on its own turn below;
    # the query checks then run without the missing cross-reference (missing
    # registries disable checks instead of producing false failures).
    try:
        query_document = _load_optional_json(
            metadata_dir / "queries" / "query-registry.json"
        )
        variants_document = _load_optional_json(
            metadata_dir / "queries" / "query-variants.json"
        )
        vocabulary = _load_query_vocabulary(metadata_dir)
    except ConfigError:
        query_document = None
        variants_document = None
        vocabulary = None

    found = False
    for directory, entries in (
        (config_dir, REGISTRY_FILES),
        (metadata_dir, METADATA_REGISTRY_FILES),
    ):
        for relative, schema_id in entries:
            path = directory / relative
            if not path.is_file():
                continue
            found = True
            try:
                document = _load_json(path)
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                bundle.reports.append(
                    Report(
                        schema_id=schema_id,
                        target=str(path),
                        valid=False,
                        issues=[_io_issue("TARGET_FILE_UNREADABLE", str(path))],
                    )
                )
                continue
            extra_checks = []
            if schema_id == "query-registry-v1":
                extra_checks.append(
                    lambda document, _vocabulary=vocabulary: check_query_registry(
                        document, vocabulary=_vocabulary
                    )
                )
            elif schema_id == "query-variants-registry-v1":
                extra_checks.append(
                    lambda document,
                    _registry=query_document,
                    _vocabulary=vocabulary: check_query_variants(
                        document, query_registry=_registry, vocabulary=_vocabulary
                    )
                )
            elif schema_id == "artifact-registry-v1":
                extra_checks.append(
                    lambda document: check_artifact_registry(document)
                )
            elif schema_id == "study-registry-v1":
                extra_checks.append(
                    lambda document: check_study_registry(document)
                )
            elif schema_id == "measurement-registry-v1":
                extra_checks.append(
                    lambda document: check_measurement_registry(document)
                )
            elif schema_id == "evidence-registry-v1":
                # G5 §11: local references must exist, recorded hashes must
                # match; external references are info-only (unverifiable).
                # P7: the registry itself is secret-scanned (paths only).
                repo_root = Path(args.metadata_dir).parent
                extra_checks.append(
                    lambda document, _root=repo_root: check_evidence_registry(
                        document, repo_root=_root
                    )
                )
                extra_checks.append(lambda document: scan_for_secrets(document))
            outcome = validate_full(
                document,
                schema_id=schema_id,
                target=str(path),
                extra_checks=extra_checks,
            )
            bundle.reports.append(outcome.to_report())

    # G3: the absolute window registry (metadata/windows/*.json).  Each
    # document is validated with ``temporal-window-v1`` plus the temporal
    # semantics; cross-file checks (duplicate window_id, file name) are
    # computed over all documents at once.
    windows_dir = metadata_dir / "windows"
    if windows_dir.is_dir():
        window_items = []
        for path in sorted(windows_dir.glob("*.json")):
            found = True
            try:
                window_items.append((path, _load_json(path)))
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                bundle.reports.append(
                    Report(
                        schema_id="temporal-window-v1",
                        target=str(path),
                        valid=False,
                        issues=[_io_issue("TARGET_FILE_UNREADABLE", str(path))],
                    )
                )
        cross_checks = check_window_registry_files(window_items)
        for path, document in window_items:
            outcome = validate_full(
                document,
                schema_id="temporal-window-v1",
                target=str(path),
                extra_checks=[
                    lambda document: check_temporal_semantics(document),
                    lambda document, _path=path: cross_checks.get(str(_path), []),
                ],
            )
            bundle.reports.append(outcome.to_report())

    if not found:
        bundle.note = "no registry files found; nothing to validate"
    return bundle, _exit_code_for_reports(bundle.reports)


def cmd_validate_registries(args) -> int:
    bundle, code = _validate_registries(args)
    _emit(
        bundle.to_dict(),
        fmt=args.format,
        output=args.output,
        human_lines=_bundle_lines(bundle),
    )
    return code


# ---------------------------------------------------------------------------
# audit-legacy (Phase 8)
# ---------------------------------------------------------------------------


def cmd_audit_legacy(args) -> int:
    datasets_root = Path(args.datasets_root)
    files = sorted(datasets_root.rglob("run_metadata.json")) if datasets_root.is_dir() else []

    runs = []
    for path in files:
        entry = {
            "profile": "legacy_audit",
            "run_id": None,
            "status": "unreadable",
            "missing_fields": [],
            "path": str(path),
            "sha256": None,
            "sha256_after": None,
            "unchanged": None,
        }
        try:
            before = sha256_file(path)
            document = _load_json(path)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            runs.append(entry)
            continue
        record = audit_record(document, sha256=before)
        after = sha256_file(path)
        entry.update(
            {
                "run_id": record.run_id,
                "status": record.status,
                "missing_fields": record.missing_fields,
                "sha256": before,
                "sha256_after": after,
                "unchanged": before == after,
            }
        )
        runs.append(entry)

    audit = {
        "audit_version": "1.0.0",
        "profile": "legacy_audit",
        "schema_id": "collection-run-v1",
        "target_glob": "datasets/**/run_metadata.json",
        "count": len(runs),
        "raw_modified": any(entry.get("unchanged") is False for entry in runs),
        "runs": runs,
    }

    if args.output:
        try:
            _write_output(args.output, audit)
        except OSError as error:
            _err(f"cannot write audit output: {args.output} ({error.__class__.__name__})")
            return EXIT_IO
        _err(f"legacy audit written: {args.output} ({len(runs)} run(s))")
    else:
        print(dump_json(audit), end="")

    incomplete = sum(1 for entry in runs if entry.get("status") != "complete")
    _err(f"legacy audit: {len(runs)} run(s), {incomplete} incomplete")
    return EXIT_OK


# ---------------------------------------------------------------------------
# audit-provenance (G5 §9 / §10)
# ---------------------------------------------------------------------------


def cmd_audit_provenance(args) -> int:
    """Non-destructive G5 provenance assessment over run_metadata files.

    Read-only report (always exit 0, like the other audits): per-run
    completeness / confidence / integrity / readiness plus lineage edges.
    Absent provenance is reported as ``unknown``, never inferred (P2/P5).
    """
    try:
        registries = load_registries(
            Path(args.config_dir), Path(args.metadata_dir)
        )
    except ConfigError as error:
        _err(str(error))
        return EXIT_CONFIG
    assessment = build_provenance_assessment(
        Path(args.datasets_root),
        registries=registries if registries.any() else None,
    )
    if args.output:
        try:
            _write_output(args.output, assessment)
        except OSError as error:
            _err(
                f"cannot write audit output: {args.output} "
                f"({error.__class__.__name__})"
            )
            return EXIT_IO
        _err(
            f"provenance assessment written: {args.output} "
            f"({assessment['count']} run(s), "
            f"raw_modified={assessment['raw_modified']})"
        )
    else:
        print(dump_json(assessment), end="")
    summary = ", ".join(
        f"{key}={value}"
        for key, value in sorted(assessment["summary"]["readiness"].items())
    )
    _err(
        f"provenance assessment: {assessment['count']} run(s), "
        f"strict_valid={assessment['summary']['strict_valid']} [{summary}]"
    )
    return EXIT_OK


# ---------------------------------------------------------------------------
# audit-artifacts (G4 §16)
# ---------------------------------------------------------------------------


def cmd_audit_artifacts(args) -> int:
    """Non-destructive G4 §16 artifact inventory over a datasets root.

    Read-only: every artifact file is hashed before and after the scan and
    ``raw_modified`` records any drift.  Legacy artifacts without a manifest
    are recorded as missing metadata (never reconstructed, P8); page
    sequences distinguish a missing page (取得失敗/未収集) from an observed
    zero page.  A malformed artifact registry is a configuration error.
    """
    try:
        artifact_registry = ArtifactRegistry.load(
            Path(args.metadata_dir) / "artifacts" / "artifact-registry.json"
        )
    except ValueError as error:
        _err(str(error))
        return EXIT_CONFIG
    inventory = build_artifact_inventory(
        Path(args.datasets_root),
        artifact_registry=artifact_registry,
        include_private=args.include_private,
    )
    if args.output:
        try:
            _write_output(args.output, inventory)
        except OSError as error:
            _err(
                f"cannot write audit output: {args.output} "
                f"({error.__class__.__name__})"
            )
            return EXIT_IO
        _err(
            f"artifact inventory written: {args.output} "
            f"({inventory['count']} file(s), raw_modified={inventory['raw_modified']})"
        )
    else:
        print(dump_json(inventory), end="")
    summary = ", ".join(
        f"{key}={value}" for key, value in sorted(inventory["judgment_summary"].items())
    )
    _err(
        f"artifact inventory: {inventory['count']} file(s), "
        f"{inventory['run_count']} run(s) [{summary}]"
    )
    return EXIT_OK


# ---------------------------------------------------------------------------
# audit-git-tracking / audit-private-catalog / gate-publication (G6 §10/§13/§15)
# ---------------------------------------------------------------------------


def cmd_audit_x_identity(args) -> int:
    """Policy gate: X post text, handles, display names and post permalinks must
    not be tracked.  Read-only; see ``validation/x_identity.py`` for the rule."""
    try:
        report = audit_x_identity(Path.cwd())
    except (OSError, KeyError, ValueError) as error:
        _err(f"x identity audit failed: {error.__class__.__name__}: {error}")
        return EXIT_CONFIG
    if args.output:
        try:
            _write_output(args.output, report)
        except OSError as error:
            _err(f"cannot write audit output: {args.output} ({error.__class__.__name__})")
            return EXIT_IO
        _err(
            f"x identity audit written: {args.output} "
            f"({report['finding_count']} finding(s))"
        )
    elif args.format == "json":
        print(dump_json(report), end="")
    else:
        for finding in report["findings"]:
            print(f"{finding['kind']:16} {finding['path']}  {finding['detail']}")
    _err(
        f"x identity audit: scanned={report['scanned_count']} "
        f"findings={report['finding_count']} "
        f"acknowledged={len(report['acknowledged'])} "
        f"stale_acknowledgements={len(report['stale_acknowledgements'])}"
    )
    return EXIT_DATA if report["failures"] else EXIT_OK


def cmd_audit_apify_evidence(args) -> int:
    """Offline PRV-013 checklist: the cloud evidence request list is an honest
    transcription of its source declaration, and per adopted run which cloud
    fields still need owner retrieval.

    Read-only and offline: the two committed JSON documents are compared and
    nothing else is touched -- no Apify, Zenodo, GitHub or other external API
    is called, and no token is read.  Exit 0 means the list is honest (no
    invented values), not that cloud evidence exists: ``blocked`` counts stay
    non-zero until the owner retrieves and registers the missing fields.
    """
    try:
        requests_document = _load_json(Path(args.requests))
        declaration = _load_json(Path(args.declaration))
    except OSError as error:
        _err(f"apify evidence audit failed: {error.__class__.__name__}: {error}")
        return EXIT_IO
    except ValueError as error:
        _err(f"apify evidence audit failed: {error.__class__.__name__}: {error}")
        return EXIT_CONFIG
    report = audit_apify_evidence(requests_document, declaration)
    if args.output:
        try:
            _write_output(args.output, report)
        except OSError as error:
            _err(f"cannot write audit output: {args.output} ({error.__class__.__name__})")
            return EXIT_IO
        _err(f"apify evidence audit written: {args.output}")
    elif args.format == "json":
        print(dump_json(report), end="")
    else:
        for entry in report["blocked"]:
            print(
                f"{entry['run_id']} "
                f"pending={','.join(entry['pending']) or '-'} "
                f"missing={','.join(entry['missing']) or '-'}"
            )
    _err(
        f"apify evidence audit: {report['run_count']} run(s) "
        f"pending={report['pending_count']} "
        f"missing={report['missing_count']} "
        f"observed={report['observed_count']} "
        f"cloud_evidence_obtained={report['cloud_evidence_obtained']} "
        f"violations={len(report['violations'])}"
    )
    return EXIT_DATA if report["violations"] else EXIT_OK


def cmd_audit_new_runs(args) -> int:
    """Runs outside the frozen legacy list must satisfy the current contract.

    This is the enforceable half of the Phase 6 wiring gap: a collection that
    bypassed the framework cannot pass strict validation, so the bypass shows up
    as a failing gate instead of silent data (see ``validation/new_runs.py``).
    """
    try:
        registries = load_registries(Path(args.config_dir), Path(args.metadata_dir))
        report = audit_new_runs(
            Path.cwd(), args.datasets_root, registries=registries
        )
    except (OSError, ValueError) as error:
        _err(f"new-run audit failed: {error.__class__.__name__}: {error}")
        return EXIT_CONFIG

    if args.output:
        try:
            _write_output(args.output, report)
        except OSError as error:
            _err(f"cannot write audit output: {args.output} ({error.__class__.__name__})")
            return EXIT_IO
        _err(f"new-run audit written: {args.output}")
    elif args.format == "json":
        print(dump_json(report), end="")
    else:
        for failure in report["failures"]:
            print(
                f"{failure['run_id'] or '(no run_id)'} {failure['path']} "
                f"[{', '.join(failure['issue_codes'])}]"
            )
    _err(
        f"new-run audit: {report['run_count']} run(s), "
        f"frozen_legacy_seen={report['frozen_legacy_seen']} "
        f"(declared {report['frozen_legacy_declared']}), "
        f"new={report['new_run_count']}, failures={report['failure_count']}"
    )
    return EXIT_DATA if report["failure_count"] else EXIT_OK


def cmd_audit_adoption(args) -> int:
    """Every raw run directory, with the state of its declaration inputs.

    ``audit-new-runs`` and ``audit-provenance`` discover runs by their metadata
    file, so a raw run directory without one is absent from both.  This audit
    walks the raw layer instead and reports the adoption backlog (see
    ``validation/adoption.py``).  Informational by design: an undeclared run is
    a backlog item, not a data failure; only unreadable metadata and an empty
    run directory are violations.
    """
    try:
        report = build_adoption_backlog(
            args.datasets_root, include_private=args.include_private
        )
    except (OSError, ValueError) as error:
        _err(f"adoption audit failed: {error.__class__.__name__}: {error}")
        return EXIT_CONFIG

    if args.output:
        try:
            _write_output(args.output, report)
        except OSError as error:
            _err(
                f"cannot write audit output: {args.output} "
                f"({error.__class__.__name__})"
            )
            return EXIT_IO
        _err(f"adoption audit written: {args.output}")
    elif args.format == "json":
        print(dump_json(report), end="")
    else:
        for run in report["runs"]:
            if run["state"] == "run_metadata":
                continue
            print(
                f"{run['study_id']}/{run['source_id']}/{run['run_dir']} "
                f"{run['state']}"
                f"{'' if run['run_id_form'] else ' (not in run-id form)'}"
                f"{'' if not run['catalogued'] else ' catalogued'}"
            )
        for entry in report["loose_files"]:
            print(
                f"{entry['study_id']}/{entry['source_id']}/{entry['name']} "
                f"loose_payload_file"
            )
    _err(
        f"adoption audit: {report['run_count']} run dir(s) in "
        f"{report['source_count']} source dir(s), "
        f"run_metadata={report['run_metadata_count']}, "
        f"no_run_metadata={report['no_run_metadata_count']}, "
        f"request_unrecorded={report['request_unrecorded_count']}, "
        f"window_unrecorded={report['window_unrecorded_count']}, "
        f"run_id_mismatch={report['run_id_mismatch_count']}, "
        f"uncatalogued={report['uncatalogued_count']}, "
        f"sources_without_catalog={report['sources_without_catalog_count']}, "
        f"empty={report['empty_run_count']}, "
        f"loose_files={report['loose_file_count']}, "
        f"violations={len(report['violations'])}"
    )
    return EXIT_DATA if report["violations"] else EXIT_OK


def cmd_audit_issues(args) -> int:
    """Issue records must be machine-readable, and an OPEN P0 must not pass quietly.

    Read-only; see ``validation/issues.py`` for the rule and why the
    referenced-path check was rejected.
    """
    try:
        report = audit_issues(Path.cwd(), args.issues_dir)
    except OSError as error:
        _err(f"issue audit failed: {error.__class__.__name__}: {error}")
        return EXIT_IO

    if args.output:
        try:
            _write_output(args.output, report)
        except OSError as error:
            _err(f"cannot write audit output: {args.output} ({error.__class__.__name__})")
            return EXIT_IO
        _err(f"issue audit written: {args.output}")
    elif args.format == "json":
        print(dump_json(report), end="")
    else:
        for path in report["failures"]:
            print(path)
    _err(
        f"issue audit: {report['issue_count']} issue(s) "
        f"[{', '.join(f'{k}={v}' for k, v in report['status_counts'].items())}] "
        f"open_p0={len(report['open_critical'])} "
        f"open_p1={len(report['open_high'])} "
        f"failures={report['failure_count']}"
    )
    if report["open_critical"]:
        _err("OPEN P0 issue(s) — resolve them, or record why not (PENDING/MITIGATED):")
        for path in report["open_critical"]:
            _err(f"  {path}")
    return EXIT_DATA if report["failure_count"] else EXIT_OK


def cmd_audit_publication(args) -> int:
    """Publication contract audit.  Record-only: the rules need a content
    refresh to pass, so findings are recorded and the exit code stays 0 (same
    treatment as ``gate-publication`` and ``boundary-report``).

    Read-only; the rule set and why it is not fatal live in
    ``validation/publication_contract.py``.
    """
    try:
        report = build_publication_contract_report(Path.cwd())
    except (OSError, ValueError) as error:
        _err(f"publication contract audit failed: {error.__class__.__name__}: {error}")
        return EXIT_CONFIG

    summary = report["summary"]
    if args.output:
        try:
            _write_output(args.output, report)
        except OSError as error:
            _err(
                f"cannot write audit output: {args.output} "
                f"({error.__class__.__name__})"
            )
            return EXIT_IO
        _err(
            f"publication contract written: {args.output} "
            f"({summary['finding_count']} finding(s))"
        )
    elif args.format == "json":
        print(dump_json(report), end="")
    else:
        for finding in report["findings"]:
            print(
                f"{finding['rule']:5} {finding['kind']:28} "
                f"{finding['path']}  {finding['detail']}"
            )
        for gap in report["declared_gaps"]:
            print(f"GAP   {gap['kind']:28} {gap['path']}  {gap['detail']}")
    _err(
        f"publication contract: {summary['artifact_count']} artifact(s) "
        f"findings={summary['finding_count']} "
        f"[{', '.join(f'{key}={value}' for key, value in summary['by_rule'].items())}] "
        f"declared_gaps={summary['declared_gap_count']} "
        f"(record-only)"
    )
    return EXIT_OK


def cmd_contract_ledger(args) -> int:
    """The contract ledger: every declared contract in one derived inventory.

    Read-only; see ``validation/contract_ledger.py`` for what is derived there
    and what is declared in that module (and why the ledger exists at all).
    """
    try:
        ledger = build_contract_ledger(Path.cwd())
    except (OSError, ValueError) as error:
        _err(f"contract ledger failed: {error.__class__.__name__}: {error}")
        return EXIT_CONFIG

    summary = ledger["summary"]
    if args.output:
        try:
            _write_output(args.output, ledger)
        except OSError as error:
            _err(
                f"cannot write ledger output: {args.output} "
                f"({error.__class__.__name__})"
            )
            return EXIT_IO
        _err(
            f"contract ledger written: {args.output} "
            f"({summary['contract_count']} contract(s))"
        )
    elif args.format == "json":
        print(dump_json(ledger), end="")
    else:
        for contract in ledger["contracts"]:
            print(
                f"{contract['kind']:18} {contract['contract_id']:32} "
                f"{contract['group']:3} {contract['owner']}"
            )
        for gap in ledger["gaps"]:
            print(f"GAP {gap['kind']:20} {gap['contract_id']}  {gap['detail']}")
    _err(
        f"contract ledger: {summary['contract_count']} contract(s) "
        f"[{', '.join(f'{key}={value}' for key, value in summary['by_kind'].items())}] "
        f"documents={summary['document_count']} gaps={summary['gap_count']}"
    )
    return EXIT_OK


def cmd_audit_git_tracking(args) -> int:
    """Non-destructive G6 §15 git tracking inventory (read-only git only)."""
    repo_root = Path.cwd()
    inventory = build_git_tracking_inventory(
        repo_root,
        datasets_root=Path(args.datasets_root),
        include_private=args.include_private,
    )
    if args.output:
        try:
            _write_output(args.output, inventory)
        except OSError as error:
            _err(f"cannot write audit output: {args.output} ({error.__class__.__name__})")
            return EXIT_IO
        _err(
            f"git tracking inventory written: {args.output} "
            f"({inventory['count']} file(s), raw_modified={inventory['raw_modified']})"
        )
    else:
        print(dump_json(inventory), end="")
    summary = ", ".join(
        f"{key}={value}" for key, value in sorted(inventory["state_summary"].items())
    )
    _err(f"git tracking inventory: {inventory['count']} file(s) [{summary}]")
    return EXIT_OK


def cmd_audit_private_catalog(args) -> int:
    """Non-destructive G6 §13 private boundary catalog (existence only).

    Default output is committed-safe (repository facts only, no local-disk
    state); ``--include-local-state`` inspects this checkout's disk instead.
    """
    catalog = build_private_catalog(
        Path.cwd(), include_local_state=args.include_local_state
    )
    if args.output:
        try:
            _write_output(args.output, catalog)
        except OSError as error:
            _err(f"cannot write audit output: {args.output} ({error.__class__.__name__})")
            return EXIT_IO
        _err(
            f"private catalog written: {args.output} "
            f"({catalog['count']} marker(s), present={catalog['present']})"
        )
    else:
        print(dump_json(catalog), end="")
    _err(f"private catalog: {catalog['count']} marker(s), present={catalog['present']}")
    return EXIT_OK


def cmd_gate_publication(args) -> int:
    """Record-only G6 §10 publication eligibility gate (never publishes)."""
    try:
        artifact = _load_json(Path(args.artifact))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        _err(f"cannot read artifact file: {args.artifact}")
        return EXIT_IO
    decision = None
    if args.decision:
        try:
            decision = _load_json(Path(args.decision))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            _err(f"cannot read decision file: {args.decision}")
            return EXIT_IO
    evidence: dict = {}
    if args.evidence:
        try:
            loaded = _load_json(Path(args.evidence))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            _err(f"cannot read evidence file: {args.evidence}")
            return EXIT_IO
        if isinstance(loaded, dict):
            evidence = loaded
    result = evaluate_eligibility(artifact, decision, evidence=evidence)
    if args.output:
        try:
            _write_output(args.output, result)
        except OSError as error:
            _err(f"cannot write gate output: {args.output} ({error.__class__.__name__})")
            return EXIT_IO
        _err(f"publication gate written: {args.output} (verdict={result['verdict']})")
    else:
        print(dump_json(result), end="")
    _err(f"publication gate: {result['artifact_id']} -> {result['verdict']}")
    # Record-only: a BLOCKED verdict is an artifact finding, not a CLI
    # failure.  Exit 0 unless the inputs themselves are unreadable (above).
    return EXIT_OK


# ---------------------------------------------------------------------------
# validate-release-manifest (ISS-20261015-REL-014; validation only)
# ---------------------------------------------------------------------------


def _release_manifest_report(manifest_path: str, archive_path: str, problems: list[str]) -> dict:
    """Stable JSON report for ``validate-release-manifest`` (sorted problems)."""
    return {
        "validation_version": VALIDATION_VERSION,
        "schema_id": RELEASE_MANIFEST_SCHEMA_ID,
        "manifest": manifest_path,
        "archive": archive_path,
        "valid": not problems,
        "problems": sorted(problems),
    }


def cmd_validate_release_manifest(args) -> int:
    """Validate a clean release archive against a release manifest (read-only).

    Exit semantics: 0 == archive matches the manifest; 1 == archive content
    defect (missing required path, forbidden path, out-of-scope path,
    version/DOI mismatch); 2 == malformed manifest (schema/config error);
    3 == unreadable manifest/archive file.  Nothing is created, published,
    pushed, or uploaded; only ``--output`` writes a JSON report.
    """
    manifest_path = Path(args.file)
    try:
        manifest = _load_json(manifest_path)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        _err(f"cannot read manifest file: {manifest_path} ({error.__class__.__name__})")
        return EXIT_IO

    structural = (
        release_manifest_structural_problems(manifest)
        if isinstance(manifest, dict)
        else ["manifest is not a JSON object"]
    )
    archive_text = str(args.archive) if args.archive else ""
    if not archive_text and isinstance(manifest, dict):
        block = manifest.get("archive")
        if isinstance(block, dict) and block.get("path"):
            archive_text = str(block["path"])
    if structural:
        _emit(
            _release_manifest_report(str(manifest_path), archive_text, structural),
            fmt=args.format,
            output=args.output,
            human_lines=[
                f"FAIL {RELEASE_MANIFEST_SCHEMA_ID} {archive_text or manifest_path}",
                *(_human_manifest_problems(structural)),
            ],
        )
        return EXIT_CONFIG

    archive_path = Path(archive_text)
    if not archive_text or not archive_path.is_file():
        _err(f"cannot read archive file: {archive_text or '(no archive path in manifest)'}")
        return EXIT_IO
    problems = check_release_manifest(manifest, archive=archive_path)
    verdict = "OK" if not problems else "FAIL"
    _emit(
        _release_manifest_report(str(manifest_path), str(archive_path), problems),
        fmt=args.format,
        output=args.output,
        human_lines=[
            f"{verdict} {RELEASE_MANIFEST_SCHEMA_ID} {archive_path}",
            *(_human_manifest_problems(problems)),
        ],
    )
    return EXIT_OK if not problems else EXIT_DATA


def _human_manifest_problems(problems: list[str]) -> list[str]:
    """One stable ``  - <problem>`` line per finding (stderr only)."""
    return [f"  - {problem}" for problem in sorted(problems)]


# ---------------------------------------------------------------------------
# gate-plan (Phase 6 / P6-1 initial CLI surface)
# ---------------------------------------------------------------------------


def cmd_gate_plan(args) -> int:
    """Pre-collection gate: structural validation + registry/capability gate.

    Exit 0 = proceed, 1 = stop (fail closed), 2 = config error, 3 = I/O error.
    This is an initial surface for P6-1; a full Collection Plan contract lands
    with the G1 adapter contract and may extend the checks.
    """
    try:
        get_schema("collection-plan-v1")
    except ValueError as error:
        _err(str(error))
        return EXIT_CONFIG

    target = Path(args.file)
    try:
        document = _load_json(target)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        _err(f"cannot read input file: {target}")
        return EXIT_IO

    try:
        registries = load_registries(Path(args.config_dir), Path(args.metadata_dir))
    except ConfigError as error:
        _err(str(error))
        return EXIT_CONFIG

    outcome = validate_full(
        document,
        schema_id="collection-plan-v1",
        target=str(target),
        registries=registries if registries.any() else None,
    )
    issues = list(outcome.issues)
    if outcome.valid:
        gate = pre_collection_gate(document, registries=registries)
        issues.extend(gate.issues)
        action = gate.action
    else:
        action = "stop"
    issues.sort(key=lambda issue: issue.sort_key())

    report = {
        "validation_version": VALIDATION_VERSION,
        "schema_id": "collection-plan-v1",
        "target": str(target),
        "profile": "gate",
        "action": action,
        "valid": not any(issue.severity == "error" for issue in issues),
        "issues": [issue.to_dict() for issue in issues],
    }
    lines = [f"{action.upper()} collection-plan-v1 {target}"]
    for issue in issues:
        lines.append(f"  [{issue.code}] {issue.path}: {issue.message}")
    _emit(report, fmt=args.format, output=args.output, human_lines=lines)
    return _exit_code(issues)


# ---------------------------------------------------------------------------
# gate-run (Phase 6 / L1 post-collection decision)
# ---------------------------------------------------------------------------


def cmd_gate_run(args) -> int:
    """Post-collection L1 gate: structural + semantic + missingness + artifacts.

    Exit 0 = catalog (adoptable), 1 = quarantine (keep raw, do not adopt),
    2 = config error, 3 = I/O error.  The command only decides; moving the
    run into/out of staging is the caller's job (G1 §13).
    """
    target = Path(args.file)
    try:
        document = _load_json(target)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        _err(f"cannot read input file: {target}")
        return EXIT_IO

    try:
        registries = load_registries(Path(args.config_dir), Path(args.metadata_dir))
    except ConfigError as error:
        _err(str(error))
        return EXIT_CONFIG

    try:
        outcome = validate_full(
            document,
            schema_id="collection-run-v1",
            target=str(target),
            registries=registries if registries.any() else None,
            base_dir=target.parent,
            verify_artifacts=True,
        )
    except ValueError as error:
        _err(str(error))
        return EXIT_CONFIG

    issues = list(outcome.issues)
    if outcome.valid:
        gate = post_collection_gate(
            document,
            registries=registries if registries.any() else None,
            base_dir=target.parent,
        )
        issues.extend(gate.issues)
        action = gate.action
    else:
        action = "quarantine"
    issues.sort(key=lambda issue: issue.sort_key())

    report = {
        "validation_version": VALIDATION_VERSION,
        "schema_id": "collection-run-v1",
        "target": str(target),
        "profile": "gate",
        "action": action,
        "valid": not any(issue.severity == "error" for issue in issues),
        "issues": [issue.to_dict() for issue in issues],
    }
    lines = [f"{action.upper()} collection-run-v1 {target}"]
    for issue in issues:
        lines.append(f"  [{issue.code}] {issue.path}: {issue.message}")
    _emit(report, fmt=args.format, output=args.output, human_lines=lines)
    return _exit_code(issues)


# ---------------------------------------------------------------------------
# compare-runs (G1 §12 L2)
# ---------------------------------------------------------------------------


def cmd_compare_runs(args) -> int:
    """L2 run-level comparability report (C1 / C2 / C3 + optional T6/T7).

    Exit code is 0 for any produced verdict: L2 restricts comparison, it does
    not invalidate data (P5).  Unreadable inputs are I/O errors (exit 3).
    When ``--coverage-a`` / ``--coverage-b`` are given (run directories or
    ``run_metadata.json`` paths), the G3 coverage manifests are evaluated and
    the temporal gate additionally applies the T6/T7 coverage conditions.
    """
    documents = []
    for label, path_str in (("a", args.a), ("b", args.b)):
        path = Path(path_str)
        try:
            documents.append(_load_json(path))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            _err(f"cannot read input file ({label}): {path}")
            return EXIT_IO

    coverage_a = None
    coverage_b = None
    if args.coverage_a:
        coverage_a = evaluate_coverage(args.coverage_a)
    if args.coverage_b:
        coverage_b = evaluate_coverage(args.coverage_b)

    result = compare_runs(
        documents[0],
        documents[1],
        purpose=args.purpose or "",
        coverage_a=coverage_a,
        coverage_b=coverage_b,
    )
    report = {
        "validation_version": VALIDATION_VERSION,
        "gate": "L2",
        "schema_id": "collection-run-v1",
        "a": str(args.a),
        "b": str(args.b),
        "purpose": args.purpose or "direct_comparison",
        "status": result.status,
        "reasons": list(result.reasons),
    }
    if coverage_a is not None or coverage_b is not None:
        report["coverage"] = {
            "a": (coverage_a or {}).get("coverage", {}).get("status"),
            "b": (coverage_b or {}).get("coverage", {}).get("status"),
        }
    lines = [f"L2 {result.status} {args.a} vs {args.b}"]
    for reason in result.reasons:
        lines.append(f"  reason: {reason}")
    _emit(report, fmt=args.format, output=args.output, human_lines=lines)
    return EXIT_OK


# ---------------------------------------------------------------------------
# coverage-run (G3 §9)
# ---------------------------------------------------------------------------


def cmd_coverage_run(args) -> int:
    """G3 §9 coverage manifest for one run (read-only by default).

    Without ``--persist`` the command reports the on-demand manifest and
    writes nothing except the ``--output`` path (existing behavior).  With
    ``--persist`` it writes exactly one canonical file,
    ``<run-dir>/coverage-manifest.json`` (derived metadata, never raw data),
    and reports the persisted target on stderr.  ``--persist`` cannot be
    combined with ``--output`` (configuration error, exit 2) so the two
    cannot create competing artifacts.

    The command reports; it never invalidates data, so the exit code is 0
    for any produced manifest (like ``compare-runs``).  Unreadable targets
    and persistence write failures are I/O errors (exit 3).
    """
    persist = bool(getattr(args, "persist", False))
    if persist and args.output:
        _err(
            "coverage-run: --persist writes only to "
            "<run-dir>/coverage-manifest.json; "
            "--output cannot be combined with --persist"
        )
        return EXIT_CONFIG
    target = Path(args.file)
    if not target.exists():
        _err(f"cannot read target: {target}")
        return EXIT_IO
    manifest = evaluate_coverage(target)
    coverage = manifest["coverage"]
    if persist:
        run_dir = target if target.is_dir() else target.parent
        canonical = coverage_manifest_path_for_run(run_dir)
        try:
            write_coverage_manifest(manifest, canonical)
        except OSError as error:
            _err(
                f"cannot write coverage manifest: {canonical} "
                f"({error.__class__.__name__})"
            )
            return EXIT_IO
        _err(
            f"coverage manifest persisted: {canonical} "
            f"(status={coverage['status']} run_id={manifest['run_id']})"
        )
        return EXIT_OK
    lines = [
        f"COVERAGE {coverage['status']} run_id={manifest['run_id']} "
        f"window_id={manifest['window_id']}",
        f"  target: {target}",
    ]
    for reason in coverage["reasons"]:
        lines.append(f"  reason: {reason}")
    for term, entry in sorted(coverage["states"].items()):
        lines.append(
            f"  term {term}: state={entry['state']} "
            f"points={entry['point_count']} zeros={entry['zero_count']}"
        )
    _emit(manifest, fmt=args.format, output=args.output, human_lines=lines)
    return EXIT_OK


def cmd_boundary_report(args) -> int:
    """Relative-timeframe boundary evidence table + promotion rule (read-only).

    ISS-20261015-GT-001 / ``docs/specs/gt-boundary-verification.md``: reports,
    per run, the collected relative timeframe, the nominal resolution and the
    observed bucket labels, and evaluates the `exact` promotion rule over the
    measurement cohort.  The command reports; it never promotes and never
    writes anything except the ``--output`` path, so the exit code is always 0
    (like ``coverage-run``).
    """
    report = build_boundary_report(
        Path(args.datasets_root), study=args.study, run=args.run
    )
    rule = report["rule"]
    lines = [
        f"BOUNDARY rows={report['row_count']} "
        f"measurement_runs={report['measurement_row_count']} "
        f"eligible={rule['eligible']}"
    ]
    for row in report["rows"]:
        parts = [
            f"run_id={row.get('run_id')}",
            f"class={row.get('evidence_class')}",
            f"timeframe={row.get('timeframe')}",
            f"verdict={row['verdict']}",
        ]
        if row.get("first_offset_days") is not None:
            parts.append(f"first_offset_days={row['first_offset_days']}")
            parts.append(f"last_end_offset_days={row['last_end_offset_days']}")
        if row.get("reasons"):
            parts.append("reasons=" + ",".join(row["reasons"]))
        lines.append("  row " + " ".join(parts))
    for timeframe, verdict in sorted(rule["timeframes"].items()):
        lines.append(
            f"  timeframe {timeframe}: consistent_runs={verdict['consistent_runs']} "
            f"reference_days={len(verdict['reference_days'])} "
            f"reference_span_days={verdict['reference_span_days']} "
            f"satisfied={verdict['satisfied']}"
        )
    for reason in rule["reasons"]:
        lines.append(f"  rule_reason: {reason}")
    _emit(report, fmt=args.format, output=args.output, human_lines=lines)
    return EXIT_OK


# ---------------------------------------------------------------------------
# audit-temporal (G3 §15)
# ---------------------------------------------------------------------------


def cmd_audit_temporal(args) -> int:
    """Non-destructive G3 §15 temporal inventory over run metadata files.

    Read-only: every file touched is hashed before and after, and
    ``raw_modified`` records any drift.  Relative legacy periods are never
    converted into absolute windows (``resolved_absolute_window: null``).
    """
    inventory = build_temporal_inventory(Path(args.datasets_root))
    if args.output:
        try:
            _write_output(args.output, inventory)
        except OSError as error:
            _err(
                f"cannot write audit output: {args.output} "
                f"({error.__class__.__name__})"
            )
            return EXIT_IO
        _err(
            f"temporal inventory written: {args.output} "
            f"({inventory['count']} run(s), raw_modified={inventory['raw_modified']})"
        )
    else:
        print(dump_json(inventory), end="")
    summary = ", ".join(
        f"{key}={value}"
        for key, value in sorted(inventory["classification_summary"].items())
    )
    _err(f"temporal inventory: {inventory['count']} run(s) [{summary}]")
    return EXIT_OK


# ---------------------------------------------------------------------------
# classify-query / compare-queries / audit-queries (G2 §8 / §9 / §13)
# ---------------------------------------------------------------------------


def _query_registry_payload(registries: Registries) -> dict:
    return {
        "schema_version": registries.query_registry_version,
        "queries": list(registries.queries),
    }


def _query_variants_payload(registries: Registries) -> dict:
    return {"variant_sets": list(registries.query_variants)}


def _query_reference(entry: dict) -> dict:
    return {
        "query_id": entry.get("query_id"),
        "compound_id": entry.get("compound_id"),
        "intent_id": entry.get("intent_id"),
        "canonical_text": entry.get("canonical_text"),
        "status": entry.get("status"),
    }


def cmd_classify_query(args) -> int:
    """Stage-1 deterministic classification of one query string (G2 §8).

    Exit 0 = the text resolves to a registered query in ``active`` status
    (adoptable as that query); 1 = not adoptable (irrelevant / ambiguous /
    unknown, or a non-active registration); 2 = configuration error (query
    registry missing or unreadable).
    """
    try:
        registries = load_registries(Path(args.config_dir), Path(args.metadata_dir))
        vocabulary = _load_query_vocabulary(Path(args.metadata_dir))
    except ConfigError as error:
        _err(str(error))
        return EXIT_CONFIG
    if not registries.queries:
        _err("query registry not found (metadata/queries/query-registry.json)")
        return EXIT_CONFIG

    result = classify_query_text(
        args.text,
        query_registry=_query_registry_payload(registries),
        variant_registry=_query_variants_payload(registries),
        vocabulary=vocabulary,
    )
    result["registry_version"] = registries.query_registry_version
    adoptable = (
        result["classification"] == "relevant"
        and result.get("query_status") == "active"
    )
    lines = [f"{result['classification'].upper()} {result['text']!r}"]
    if result.get("query_id"):
        lines.append(
            f"  query_id: {result['query_id']} "
            f"(status={result.get('query_status')})"
        )
    if result.get("variant_id"):
        lines.append(f"  variant_id: {result['variant_id']}")
    if result.get("rule_id"):
        lines.append(f"  rule: {result['rule_id']} - {result.get('rationale')}")
        lines.append(f"  evidence: {result.get('evidence')}")
    if result.get("matched_tokens"):
        lines.append("  matched tokens: " + ", ".join(result["matched_tokens"]))
    for reason in result.get("reasons", []):
        lines.append(f"  reason: {reason}")
    _emit(result, fmt=args.format, output=args.output, human_lines=lines)
    return EXIT_OK if adoptable else EXIT_DATA


def cmd_compare_queries(args) -> int:
    """Definition-level comparability of two registered queries (G2 §9).

    The verdict never invalidates data (exit 0 for any produced verdict,
    like ``compare-runs``); an unknown query_id is a configuration error
    (exit 2, fail closed).
    """
    try:
        registries = load_registries(Path(args.config_dir), Path(args.metadata_dir))
    except ConfigError as error:
        _err(str(error))
        return EXIT_CONFIG
    if not registries.queries:
        _err("query registry not found (metadata/queries/query-registry.json)")
        return EXIT_CONFIG

    entries = {
        query.get("query_id"): query
        for query in registries.queries
        if isinstance(query, dict)
    }
    for name in (args.a, args.b):
        if name not in entries:
            _err(f"unknown query_id: {name}")
            return EXIT_CONFIG

    result = compare_query_definitions(
        entries[args.a],
        entries[args.b],
        registry_version_a=registries.query_registry_version,
        registry_version_b=registries.query_registry_version,
    )
    report = {
        "validation_version": VALIDATION_VERSION,
        "gate": "G2-query-comparability",
        "schema_id": "query-registry-v1",
        "registry_version": registries.query_registry_version,
        "a": _query_reference(entries[args.a]),
        "b": _query_reference(entries[args.b]),
        "status": result.status,
        "reasons": list(result.reasons),
    }
    lines = [f"G2 {result.status} {args.a} vs {args.b}"]
    for reason in result.reasons:
        lines.append(f"  reason: {reason}")
    _emit(report, fmt=args.format, output=args.output, human_lines=lines)
    return EXIT_OK


def cmd_audit_queries(args) -> int:
    """Non-destructive b.md §13 query inventory over run metadata files.

    Read-only: each file is hashed before and after reading and
    ``raw_modified`` records any drift.  Exit 0 on success, 2 for a missing
    query registry / configuration error, 3 when the output cannot be
    written.
    """
    try:
        registries = load_registries(Path(args.config_dir), Path(args.metadata_dir))
        vocabulary = _load_query_vocabulary(Path(args.metadata_dir))
    except ConfigError as error:
        _err(str(error))
        return EXIT_CONFIG
    if not registries.queries:
        _err("query registry not found (metadata/queries/query-registry.json)")
        return EXIT_CONFIG

    datasets_root = Path(args.datasets_root)
    files = (
        sorted(datasets_root.rglob("run_metadata.json"))
        if datasets_root.is_dir()
        else []
    )
    entries = []
    for path in files:
        entry = {
            "path": str(path),
            "document": None,
            "sha256": None,
            "sha256_after": None,
            "unchanged": None,
        }
        try:
            before = sha256_file(path)
            document = _load_json(path)
            after = sha256_file(path)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            entries.append(entry)
            continue
        entry.update(
            {
                "document": document,
                "sha256": before,
                "sha256_after": after,
                "unchanged": before == after,
            }
        )
        entries.append(entry)

    audit = build_query_inventory(
        entries,
        query_registry=_query_registry_payload(registries),
        variant_registry=_query_variants_payload(registries),
        vocabulary=vocabulary,
    )

    if args.output:
        try:
            _write_output(args.output, audit)
        except OSError as error:
            _err(
                f"cannot write audit output: {args.output} "
                f"({error.__class__.__name__})"
            )
            return EXIT_IO
        _err(
            f"query inventory written: {args.output} "
            f"({audit['count']} run(s), {audit['query_count']} string(s))"
        )
    else:
        print(dump_json(audit), end="")
    summary = ", ".join(
        f"{key}={value}" for key, value in sorted(audit["summary"].items())
    )
    _err(
        f"query inventory: {audit['count']} run(s), "
        f"{audit['query_count']} string(s) [{summary}]"
    )
    return EXIT_OK


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------


def _add_common(parser, *, with_profile=True):
    parser.add_argument(
        "--format", choices=("text", "json"), default="text",
        help="report format (json goes to stdout or --output)",
    )
    parser.add_argument("--output", help="write the JSON report to this path")
    if with_profile:
        parser.add_argument(
            "--profile", choices=("strict", "legacy"), default="strict",
            help="strict (new runs) or legacy (frozen legacy run IDs only)",
        )
    parser.add_argument("--config-dir", default="config")
    parser.add_argument("--metadata-dir", default="metadata")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m validation.cli",
        description="Cerberus validation framework CLI (docs/specs/validation-framework.md)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate one file against one schema")
    validate.add_argument("--schema", required=True)
    validate.add_argument("--file", required=True)
    validate.add_argument(
        "--verify-artifacts", action="store_true",
        help="also verify the artifact manifest referenced by the document",
    )
    _add_common(validate)
    validate.set_defaults(handler=cmd_validate)

    study = sub.add_parser("validate-study", help="validate every run under a study")
    study.add_argument("--study", required=True)
    study.add_argument("--datasets-root", default="datasets")
    study.add_argument("--schema", default="collection-run-v1")
    _add_common(study)
    study.set_defaults(handler=cmd_validate_study)

    registries = sub.add_parser(
        "validate-registries", help="validate every registry file that exists"
    )
    _add_common(registries, with_profile=False)
    registries.set_defaults(handler=cmd_validate_registries)

    all_parser = sub.add_parser(
        "validate-all", help="registries plus every study (CI-oriented)"
    )
    all_parser.add_argument("--datasets-root", default="datasets")
    all_parser.add_argument("--schema", default="collection-run-v1")
    _add_common(all_parser)
    all_parser.set_defaults(handler=cmd_validate_all)

    gate = sub.add_parser(
        "gate-plan", help="pre-collection gate for a collection plan (P6-1)"
    )
    gate.add_argument("--file", required=True)
    _add_common(gate, with_profile=False)
    gate.set_defaults(handler=cmd_gate_plan)

    gate_run = sub.add_parser(
        "gate-run",
        help="post-collection L1 gate: catalog vs quarantine (P6-2)",
    )
    gate_run.add_argument("--file", required=True)
    _add_common(gate_run, with_profile=False)
    gate_run.set_defaults(handler=cmd_gate_run)

    compare = sub.add_parser(
        "compare-runs", help="L2 run-level comparability report (G1 §12)"
    )
    compare.add_argument("--a", required=True, help="first run_metadata.json")
    compare.add_argument("--b", required=True, help="second run_metadata.json")
    compare.add_argument(
        "--purpose",
        default="",
        help="comparison purpose; only direct_comparison is modelled today",
    )
    compare.add_argument(
        "--coverage-a",
        help="run directory / run_metadata.json for the G3 coverage conditions "
        "(T6/T7) on side a",
    )
    compare.add_argument(
        "--coverage-b",
        help="run directory / run_metadata.json for the G3 coverage conditions "
        "(T6/T7) on side b",
    )
    compare.add_argument("--format", choices=("text", "json"), default="text")
    compare.add_argument("--output", help="write the JSON report to this path")
    compare.set_defaults(handler=cmd_compare_runs)

    coverage_run = sub.add_parser(
        "coverage-run",
        help="G3 §9 coverage manifest for one run "
        "(on-demand report; --persist writes "
        "<run-dir>/coverage-manifest.json)",
    )
    coverage_run.add_argument(
        "--file", required=True, help="run directory or run_metadata.json"
    )
    coverage_run.add_argument("--format", choices=("text", "json"), default="text")
    coverage_run.add_argument("--output", help="write the JSON manifest to this path")
    coverage_run.add_argument(
        "--persist",
        action="store_true",
        help="write the manifest to <run-dir>/coverage-manifest.json "
        "(derived metadata; incompatible with --output; "
        "existing raw files are never modified)",
    )
    coverage_run.set_defaults(handler=cmd_coverage_run)

    boundary_report = sub.add_parser(
        "boundary-report",
        help="relative-timeframe boundary evidence table + `exact` promotion "
        "rule (ISS-20261015-GT-001; read-only report)",
    )
    boundary_report.add_argument("--datasets-root", default="datasets")
    boundary_report.add_argument("--study", help="restrict the scan to one study id")
    boundary_report.add_argument(
        "--run", help="inspect one run directory instead of the datasets root"
    )
    boundary_report.add_argument("--format", choices=("text", "json"), default="text")
    boundary_report.add_argument("--output", help="write the JSON report to this path")
    boundary_report.set_defaults(handler=cmd_boundary_report)

    audit_temporal = sub.add_parser(
        "audit-temporal",
        help="non-destructive G3 §15 temporal inventory over run_metadata files",
    )
    audit_temporal.add_argument("--datasets-root", default="datasets")
    audit_temporal.add_argument(
        "--output", default="docs/audits/g3-temporal-inventory.json"
    )
    audit_temporal.set_defaults(handler=cmd_audit_temporal)

    classify = sub.add_parser(
        "classify-query",
        help="Stage-1 classification of one query string (G2 §8)",
    )
    classify.add_argument("--text", required=True)
    _add_common(classify, with_profile=False)
    classify.set_defaults(handler=cmd_classify_query)

    compare_queries = sub.add_parser(
        "compare-queries",
        help="definition-level comparability of two registered queries (G2 §9)",
    )
    compare_queries.add_argument("--a", required=True, help="query_id (query registry)")
    compare_queries.add_argument("--b", required=True, help="query_id (query registry)")
    _add_common(compare_queries, with_profile=False)
    compare_queries.set_defaults(handler=cmd_compare_queries)

    audit_queries = sub.add_parser(
        "audit-queries",
        help="non-destructive G2 query inventory over run_metadata files (b.md §13)",
    )
    audit_queries.add_argument("--datasets-root", default="datasets")
    audit_queries.add_argument(
        "--output", default="docs/audits/g2-query-inventory.json"
    )
    audit_queries.add_argument("--config-dir", default="config")
    audit_queries.add_argument("--metadata-dir", default="metadata")
    audit_queries.set_defaults(handler=cmd_audit_queries)

    audit = sub.add_parser(
        "audit-legacy", help="non-destructive G5 legacy audit (Phase 8)"
    )
    audit.add_argument("--datasets-root", default="datasets")
    audit.add_argument(
        "--output", default="docs/audits/g5-legacy-runs.json"
    )
    audit.set_defaults(handler=cmd_audit_legacy)

    audit_provenance = sub.add_parser(
        "audit-provenance",
        help="non-destructive G5 provenance assessment: completeness / "
        "confidence / integrity / readiness (e.md §9/§10)",
    )
    audit_provenance.add_argument("--datasets-root", default="datasets")
    audit_provenance.add_argument(
        "--output", default="docs/audits/g5-provenance-assessment.json"
    )
    audit_provenance.add_argument("--config-dir", default="config")
    audit_provenance.add_argument("--metadata-dir", default="metadata")
    audit_provenance.set_defaults(handler=cmd_audit_provenance)

    audit_artifacts = sub.add_parser(
        "audit-artifacts",
        help="non-destructive G4 §16 artifact inventory over a datasets root",
    )
    audit_artifacts.add_argument("--datasets-root", default="datasets")
    audit_artifacts.add_argument(
        "--output", default="docs/audits/g4-storage-inventory.json"
    )
    audit_artifacts.add_argument("--metadata-dir", default="metadata")
    audit_artifacts.add_argument(
        "--include-private",
        action="store_true",
        help="also scan directories named 'private' (excluded by default; "
        "AGENTS.md private data)",
    )
    audit_artifacts.set_defaults(handler=cmd_audit_artifacts)

    audit_git = sub.add_parser(
        "audit-git-tracking",
        help="non-destructive G6 §15 git tracking inventory (read-only git)",
    )
    audit_git.add_argument("--datasets-root", default="datasets")
    audit_git.add_argument(
        "--output", default="docs/audits/g6-git-tracking-inventory.json"
    )
    audit_git.add_argument(
        "--include-private",
        action="store_true",
        help="also scan directories named 'private' (excluded by default; "
        "AGENTS.md private data; paths only, values never read)",
    )
    audit_git.set_defaults(handler=cmd_audit_git_tracking)

    audit_x = sub.add_parser(
        "audit-x-identity",
        help="policy gate: X handles, post text/URLs and identity columns must not be tracked",
    )
    audit_x.add_argument("--output", default=None)
    audit_x.add_argument("--format", choices=("text", "json"), default="text")
    audit_x.set_defaults(handler=cmd_audit_x_identity)

    audit_apify = sub.add_parser(
        "audit-apify-evidence",
        help="offline PRV-013 checklist: the Apify cloud evidence request list "
        "against its source declaration (never calls Apify)",
    )
    audit_apify.add_argument(
        "--requests",
        default="metadata/provenance/apify-cloud-evidence-requests.json",
        help="committed cloud evidence request list",
    )
    audit_apify.add_argument(
        "--declaration",
        default="metadata/provenance/declarations/20261015-youtube-csv-adoption.json",
        help="source staging declaration the request list transcribes",
    )
    audit_apify.add_argument("--output", default=None)
    audit_apify.add_argument("--format", choices=("text", "json"), default="text")
    audit_apify.set_defaults(handler=cmd_audit_apify_evidence)

    audit_adoption = sub.add_parser(
        "audit-adoption",
        help="adoption backlog: every raw run directory and the metadata a "
        "declaration needs (read-only; no default output because the raw "
        "layer is machine-local)",
    )
    audit_adoption.add_argument("--datasets-root", default="datasets")
    audit_adoption.add_argument("--output", default=None)
    audit_adoption.add_argument("--format", choices=("text", "json"), default="text")
    audit_adoption.add_argument(
        "--include-private",
        action="store_true",
        help="also scan directories named 'private' (excluded by default; "
        "AGENTS.md private data)",
    )
    audit_adoption.set_defaults(handler=cmd_audit_adoption)

    audit_new = sub.add_parser(
        "audit-new-runs",
        help="runs outside the frozen legacy list must satisfy the current contract",
    )
    audit_new.add_argument("--datasets-root", default="datasets")
    audit_new.add_argument("--config-dir", default="config")
    audit_new.add_argument("--metadata-dir", default="metadata")
    audit_new.add_argument("--output", default=None)
    audit_new.add_argument("--format", choices=("text", "json"), default="text")
    audit_new.set_defaults(handler=cmd_audit_new_runs)

    audit_issues_parser = sub.add_parser(
        "audit-issues",
        help="issue records must be well formed and an OPEN P0 must not pass quietly",
    )
    audit_issues_parser.add_argument("--issues-dir", default="docs/issues")
    audit_issues_parser.add_argument("--output", default=None)
    audit_issues_parser.add_argument("--format", choices=("text", "json"), default="text")

    contract_ledger_parser = sub.add_parser(
        "contract-ledger",
        help=(
            "the derived inventory of every declared contract "
            "(schema / interface / gate)"
        ),
    )
    contract_ledger_parser.add_argument("--output", default=None)
    contract_ledger_parser.add_argument(
        "--format", choices=("text", "json"), default="text"
    )
    contract_ledger_parser.set_defaults(handler=cmd_contract_ledger)

    audit_publication_parser = sub.add_parser(
        "audit-publication",
        help=(
            "publication contract: release version/DOI, section depth, policy-out "
            "sources (record-only)"
        ),
    )
    audit_publication_parser.add_argument("--output", default=None)
    audit_publication_parser.add_argument(
        "--format", choices=("text", "json"), default="text"
    )
    audit_publication_parser.set_defaults(handler=cmd_audit_publication)
    audit_issues_parser.set_defaults(handler=cmd_audit_issues)

    audit_private = sub.add_parser(
        "audit-private-catalog",
        help="non-destructive G6 §13 private boundary catalog (existence only)",
    )
    audit_private.add_argument(
        "--output", default="docs/audits/g6-private-catalog.json"
    )
    audit_private.add_argument(
        "--include-local-state",
        action="store_true",
        help="also record this checkout's disk state (exists/present/absent); "
        "excluded by default so the committed snapshot stays checkout-independent "
        "(ISS-20261016-MNT-002; local-mode output must not be committed)",
    )
    audit_private.set_defaults(handler=cmd_audit_private_catalog)

    gate_pub = sub.add_parser(
        "gate-publication",
        help="record-only G6 §10 publication eligibility gate (never publishes)",
    )
    gate_pub.add_argument("--artifact", required=True, help="artifact descriptor JSON file")
    gate_pub.add_argument("--decision", help="publication decision JSON file")
    gate_pub.add_argument("--evidence", help="review evidence JSON file")
    gate_pub.add_argument(
        "--output", default="docs/audits/g6-publication-eligibility.json"
    )
    gate_pub.set_defaults(handler=cmd_gate_publication)

    manifest = sub.add_parser(
        "validate-release-manifest",
        help="read-only G6 release-manifest check: a clean archive against a "
        "release-manifest-v1 document (ISS-20261015-REL-014; never publishes)",
    )
    manifest.add_argument("--file", required=True, help="release-manifest-v1 JSON document")
    manifest.add_argument(
        "--archive",
        help="zip archive to check (overrides the manifest archive.path)",
    )
    manifest.add_argument("--format", choices=("text", "json"), default="text")
    manifest.add_argument("--output", help="write the JSON report to this path")
    manifest.set_defaults(handler=cmd_validate_release_manifest)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
