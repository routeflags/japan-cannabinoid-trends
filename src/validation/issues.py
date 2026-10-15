"""Issue records must be machine-readable, and a Critical one cannot sit silently open.

Why this exists: eight issues were OPEN in ``docs/issues/``, two of them P0, and one
had been open for eleven days with nothing noticing.  Three files in the same
directory were not issue records at all (a validation report, an instruction
document and an Actor verification report), so the directory did not mean one thing.
No check read any of it.  The directory now has status / milestone subdirectories,
so the audit scans recursively and still enforces the same rule on every issue
record.

The rule, one rule for every issue record under ``docs/issues/``:

1. it is an issue record: ``ID``, ``優先度`` and ``ステータス`` are present;
2. ``優先度`` is ``P0``/``P1``/``P2``/``P3``, and P0 is Critical while P1 is High;
3. ``ステータス`` is one of :data:`STATUSES`;
4. a terminal status carries the date the decision was made -- ``RESOLVED (2026-10-02)``
   -- because a status flip with no evidence is exactly what this repository keeps
   having to undo;
5. ids are unique;
6. **an OPEN P0 is a failure.** Critical means it may not be left silently open; the
   two honest ways forward are to resolve it or to record the reason it is not being
   resolved (``PENDING``/``MITIGATED``/``DOCUMENTED``).  P1 and below are reported,
   not fatal, because a research backlog is a normal state rather than a defect.

What this deliberately does *not* check: whether the paths an issue names exist.  That
was measured and rejected -- 24 of 60 referenced paths are absent by design (removed
artifacts, raw data that was never kept, bare filenames), so the check would be noise.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "AUDIT_VERSION",
    "STATUSES",
    "TERMINAL_STATUSES",
    "PRIORITIES",
    "Issue",
    "audit_issues",
]

AUDIT_VERSION = "1.0.0"

STATUSES = frozenset(
    {"OPEN", "PENDING", "RESOLVED", "DOCUMENTED", "MITIGATED", "ARCHIVED"}
)

#: Statuses that assert something happened, so they must say when.
TERMINAL_STATUSES = frozenset({"RESOLVED", "DOCUMENTED", "MITIGATED", "ARCHIVED"})

#: Priority -> the level word that must accompany it.
PRIORITIES = {"P0": "Critical", "P1": "High"}

_FIELD = re.compile(r"^\*\*(ID|優先度|ステータス):\*\*\s*(.+?)\s*$", re.MULTILINE)
_PRIORITY = re.compile(r"^(P[0-3])\s*\(([^)]+)\)$")


@dataclass(frozen=True)
class Issue:
    path: str
    issue_id: str
    priority: str
    level: str
    status: str
    status_note: str
    problems: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "id": self.issue_id,
            "priority": self.priority,
            "level": self.level,
            "status": self.status,
            "status_note": self.status_note,
            "problems": list(self.problems),
        }


def _parse(path: str, text: str) -> Issue:
    fields = {name: value for name, value in _FIELD.findall(text)}
    problems: list[str] = []

    issue_id = fields.get("ID", "")
    if not issue_id:
        problems.append("missing **ID:**")

    raw_priority = fields.get("優先度", "")
    priority, level = "", ""
    match = _PRIORITY.match(raw_priority)
    if not match:
        problems.append(f"priority is not 'P0 (Critical)' shaped: {raw_priority!r}")
    else:
        priority, level = match.group(1), match.group(2)
        expected = PRIORITIES.get(priority)
        if expected and level != expected:
            problems.append(f"{priority} must be '{expected}', not {level!r}")

    raw_status = fields.get("ステータス", "")
    status, note = raw_status.split("(", 1)[0].strip(), ""
    if "(" in raw_status:
        note = raw_status.split("(", 1)[1].rstrip(")").strip()
    if status not in STATUSES:
        problems.append(f"status is not one of {sorted(STATUSES)}: {raw_status!r}")
    elif status in TERMINAL_STATUSES and not re.search(r"\d{4}-\d{2}-\d{2}", raw_status):
        problems.append(f"{status} must carry the date it was decided, in parentheses")

    return Issue(path, issue_id, priority, level, status, note, tuple(problems))


def audit_issues(root: str | Path, issues_dir: str | Path = "docs/issues") -> dict:
    """Validate every committed issue record.  Read-only."""

    root = Path(root).resolve()
    directory = Path(issues_dir)
    if not directory.is_absolute():
        directory = root / directory

    issues: list[Issue] = []
    if directory.is_dir():
        for path in sorted(directory.rglob("*.md")):
            relative = path.relative_to(root).as_posix()
            issues.append(_parse(relative, path.read_text(encoding="utf-8")))

    seen: dict[str, list[str]] = {}
    for issue in issues:
        if issue.issue_id:
            seen.setdefault(issue.issue_id, []).append(issue.path)
    duplicates = {key: paths for key, paths in seen.items() if len(paths) > 1}

    def bucket(predicate) -> list[str]:
        return [issue.path for issue in issues if predicate(issue)]

    malformed = bucket(lambda i: bool(i.problems))
    open_critical = bucket(lambda i: i.priority == "P0" and i.status == "OPEN")
    open_high = bucket(lambda i: i.priority == "P1" and i.status == "OPEN")
    open_any = bucket(lambda i: i.status == "OPEN")
    duplicate_paths = sorted({path for paths in duplicates.values() for path in paths})

    failures = sorted(set(malformed) | set(open_critical) | set(duplicate_paths))

    return {
        "audit_version": AUDIT_VERSION,
        "root": str(root),
        "issue_count": len(issues),
        "status_counts": {
            status: sum(1 for issue in issues if issue.status == status)
            for status in sorted(STATUSES)
            if any(issue.status == status for issue in issues)
        },
        "open_count": len(open_any),
        "open_critical": open_critical,
        "open_high": open_high,
        "malformed": malformed,
        "duplicate_ids": duplicates,
        "failure_count": len(failures),
        "failures": failures,
        "issues": [issue.to_dict() for issue in issues],
    }
