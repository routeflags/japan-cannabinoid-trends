"""Stable Issue / Validation Report layer (rollout instruction §14, Phase 5).

Responsibilities
----------------
- Convert the nested Cerberus error structure into the stable Issue format
  required by h.md §14: ``code`` / ``path`` / ``severity`` / ``message`` /
  ``rule`` / ``schema_version``.  Cerberus errors are never exposed directly
  ("Cerberusのネストしたエラー形式を、そのまま外部インターフェースへ公開しない").
- Build the machine-readable Validation Report (``validation_version`` /
  ``schema_id`` / ``target`` / ``valid`` / ``issues``) in a deterministic
  shape: issues are sorted and every message comes from a fixed template.
- Keep secrets out of messages (§14): Cerberus interpolates the offending
  value into some messages ("unallowed value <value>"); this layer replaces
  such messages with fixed text so a copied report cannot leak a credential.

The report is JSON-serializable and stable: identical input documents produce
byte-identical output (CV-17 golden tests).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

#: Version of the report/issue format itself (not of any schema).
VALIDATION_VERSION = "1.0.0"

SEVERITIES = ("error", "warning", "info")


@dataclass(frozen=True)
class Issue:
    """One normalized validation finding (h.md §14 required fields)."""

    code: str
    path: str
    severity: str
    message: str
    rule: str
    schema_version: str = ""

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "path": self.path,
            "severity": self.severity,
            "message": self.message,
            "rule": self.rule,
            "schema_version": self.schema_version,
        }

    def sort_key(self):
        return (self.path, self.code, self.message)


# ---------------------------------------------------------------------------
# Cerberus error -> Issue mapping
# ---------------------------------------------------------------------------
#
# Every entry maps a Cerberus message (or a message prefix) to a stable code,
# the validation rule that produced it, and a *fixed* human-readable message.
# Fixed messages are required so that values Cerberus interpolates into its
# own messages (e.g. "unallowed value <secret>") never reach the report.
_MESSAGE_RULES = (
    # (predicate, code, rule, message)
    (lambda m: m == "required field", "REQUIRED_FIELD_MISSING", "required",
     "required field is missing"),
    (lambda m: m == "unknown field", "UNKNOWN_FIELD", "unknown_field",
     "unknown field is not allowed"),
    (lambda m: m == "empty values not allowed", "EMPTY_VALUE", "empty",
     "empty value is not allowed"),
    (lambda m: m == "null value not allowed", "NULL_VALUE", "empty",
     "null value is not allowed"),
    (lambda m: m.startswith("must be of "), "TYPE_MISMATCH", "type",
     None),  # message kept: only the type name is interpolated (not user data)
    (lambda m: m.startswith("unallowed value"), "UNALLOWED_VALUE", "allowed",
     "value is not one of the allowed values"),
    (lambda m: m.startswith("unallowed values"), "UNALLOWED_VALUE", "allowed",
     "value is not one of the allowed values"),
    (lambda m: m.startswith("min value"), "VALUE_BELOW_MINIMUM", "min",
     "value is below the allowed minimum"),
    (lambda m: m.startswith("max value"), "VALUE_ABOVE_MAXIMUM", "max",
     "value is above the allowed maximum"),
    (lambda m: m.startswith("min length is"), "VALUE_BELOW_MINIMUM", "minlength",
     "value is shorter than the allowed minimum"),
    (lambda m: m.startswith("max length is"), "VALUE_ABOVE_MAXIMUM", "maxlength",
     "value is longer than the allowed maximum"),
    (lambda m: m.startswith("value does not match regex"), "PATTERN_MISMATCH", "regex",
     "value does not match the required pattern"),
    (lambda m: m == "Timezone is required", "DATETIME_TIMEZONE_MISSING", "iso_datetime",
     "timezone is required for datetimes"),
    (lambda m: m == "Invalid ISO datetime", "DATETIME_INVALID", "iso_datetime",
     "value is not a parseable ISO 8601 datetime"),
)


def join_pointer(path: str, token: object) -> str:
    """Public JSON Pointer join used by semantic checks (RFC 6901 escaped)."""
    return _join(path, token)


def _message_to_issue(message: str, path: str, schema_version: str) -> Issue:
    for predicate, code, rule, fixed in _MESSAGE_RULES:
        if predicate(message):
            return Issue(
                code=code,
                path=path,
                severity="error",
                message=fixed if fixed is not None else message,
                rule=rule,
                schema_version=schema_version,
            )
    # Unknown Cerberus message: keep it for debuggability (Cerberus messages
    # do not normally contain field values, but custom rules could).
    return Issue(
        code="VALIDATION_ERROR",
        path=path,
        severity="error",
        message=message,
        rule="cerberus",
        schema_version=schema_version,
    )


def _escape_token(token: str) -> str:
    """Escape one JSON Pointer reference token (RFC 6901)."""
    return token.replace("~", "~0").replace("/", "~1")


def _join(path: str, token: object) -> str:
    return f"{path}/{_escape_token(str(token))}"


def _walk(errors: object, path: str, schema_version: str, out: list[Issue]) -> None:
    if isinstance(errors, dict):
        for key, value in errors.items():
            _walk(value, _join(path, key), schema_version, out)
        return
    if isinstance(errors, list):
        for item in errors:
            # Cerberus wraps nested structures in single-element lists; list
            # item errors appear as {'<index>': [...]} entries.
            if isinstance(item, (dict, list)):
                _walk(item, path, schema_version, out)
            elif isinstance(item, str):
                out.append(_message_to_issue(item, path, schema_version))
        return
    if isinstance(errors, str):
        out.append(_message_to_issue(errors, path, schema_version))


def normalize_cerberus_errors(
    errors: dict, *, schema_version: str = ""
) -> list[Issue]:
    """Convert nested Cerberus errors into a sorted, stable Issue list."""
    issues: list[Issue] = []
    _walk(errors, "", schema_version, issues)
    return sorted(issues, key=lambda issue: issue.sort_key())


# ---------------------------------------------------------------------------
# Report construction
# ---------------------------------------------------------------------------


@dataclass
class Report:
    """One target's validation report (serialized by ``to_dict``)."""

    schema_id: str
    target: str
    valid: bool
    issues: list[Issue] = field(default_factory=list)
    profile: str = "strict"
    legacy: dict | None = None

    def to_dict(self) -> dict:
        report: dict = {
            "validation_version": VALIDATION_VERSION,
            "schema_id": self.schema_id,
            "target": self.target,
            "profile": self.profile,
        }
        if self.legacy is not None:
            # Legacy audit record fields (h.md §18): profile / run_id /
            # status / missing_fields are merged so a single JSON document
            # carries both the audit verdict and the stable report envelope.
            report["run_id"] = self.legacy.get("run_id")
            report["status"] = self.legacy.get("status")
            report["missing_fields"] = list(self.legacy.get("missing_fields", ()))
            if "sha256" in self.legacy:
                report["sha256"] = self.legacy["sha256"]
        report["valid"] = self.valid
        report["issues"] = [issue.to_dict() for issue in self.issues]
        return report


@dataclass
class ReportBundle:
    """Multi-target report for validate-study / validate-all / registries."""

    reports: list[Report] = field(default_factory=list)
    profile: str = "strict"
    note: str | None = None

    @property
    def valid(self) -> bool:
        return all(report.valid for report in self.reports)

    def to_dict(self) -> dict:
        bundle: dict = {
            "validation_version": VALIDATION_VERSION,
            "profile": self.profile,
            "valid": self.valid,
        }
        if self.note is not None:
            bundle["note"] = self.note
        bundle["reports"] = [report.to_dict() for report in self.reports]
        return bundle


def dump_json(document: dict) -> str:
    """Serialize a report deterministically (stable key order, UTF-8)."""
    return json.dumps(document, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
