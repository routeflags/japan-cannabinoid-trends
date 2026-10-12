"""Common Cerberus entry point for structural validation of research documents.

This module is the single place in the repository allowed to import
``cerberus``. Callers must not instantiate Cerberus validators directly
(docs/plans/20261013h.md §6: "Cerberusの呼び出しを各所に分散させない").

Design rules
------------
- Structural validation only: required fields, types, ranges, allowed
  values, nested structures and unknown-field rejection (§2 of the
  instruction document). Everything else (registry existence, datetime
  ordering, query/source consistency, file hashes, lineage, git tracking)
  belongs to separate validators and must not be added here.
- ``allow_unknown=False`` and ``purge_unknown=False``: unknown fields fail
  validation and are never silently removed (the exception is a sub-schema
  that intentionally marks an extension area, e.g. collector-specific
  parameters).
- ``normalize=False``: values are never coerced or rewritten during
  validation (Contract Test CV-19). Raw data must not be modified by
  validation (AGENTS.md Raw Data Rule).
- Errors are returned, never swallowed; converting the nested Cerberus error
  structure into the stable Issue format of §14 is the job of the reporting
  layer implemented in a later phase.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from cerberus import Validator

__all__ = ["ValidationResult", "ResearchValidator", "validate_document"]


@dataclass
class ValidationResult:
    """Outcome of a structural validation run.

    ``errors`` keeps the raw nested Cerberus error structure until the
    reporting layer lands. It must not be treated as a public interface.
    """

    valid: bool
    errors: dict[str, Any]


class ResearchValidator(Validator):
    """Shared Cerberus validator carrying the repository's custom rules.

    Custom rules are field-level semantic checks that Cerberus can express
    (docs/plans/20261013h.md §10). Cross-field checks such as "start must be
    earlier than end" belong to the Semantic Validator instead (§2, §11).
    """

    def _validate_iso_datetime(self, enabled: Any, field: str, value: Any) -> None:
        """{'type': 'boolean'}"""
        # The docstring above is the Cerberus rule schema and must keep its
        # exact format.
        #
        # Nullability is controlled by the field's ``nullable``/``type``
        # rules, so None is skipped here: Cerberus still invokes custom
        # rules for nullable fields (verified against cerberus 1.3.8 on
        # Python 3.14), and calling value.replace() on None would raise
        # AttributeError.
        if not enabled or value is None:
            return

        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                self._error(field, "Timezone is required")
        except (ValueError, TypeError):
            self._error(field, "Invalid ISO datetime")


def validate_document(document: dict, schema: dict) -> ValidationResult:
    """Validate ``document`` against ``schema`` without mutating either.

    The document is validated exactly as given: unknown fields fail and no
    value is normalized, coerced or purged. The same document object can be
    safely reused (and hashed) after validation.
    """
    validator = ResearchValidator(
        schema,
        allow_unknown=False,
        purge_unknown=False,
    )

    valid = validator.validate(
        document,
        normalize=False,
    )

    return ValidationResult(
        valid=valid,
        errors=validator.errors,
    )
