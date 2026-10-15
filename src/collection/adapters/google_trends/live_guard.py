"""Bounded live-tooling guard for Google Trends MCP recollection.

This module does **not** collect research observations by itself.  It provides
small, auditable wrappers for the unsafe parts around live Google Trends
tooling discovery and collection:

* every child process has an explicit timeout;
* stdout/stderr are captured to an ignored local work area for review;
* outcomes are classified so an issue can record whether a failure was a
  timeout, dependency problem, network/rate-limit problem, configuration
  problem, or collector error;
* the probe path speaks MCP over stdio instead of using ``npx ... --help``.

Logs are intended for ``.staging/tooling_logs/...`` and must not be committed as
research data.  The probe command only initializes the MCP server and lists
tools; it does not call ``interest_over_time`` and therefore writes no raw
payloads.
"""

from __future__ import annotations

import json
import os
import re
import selectors
import signal
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from collection.adapters.google_trends.mcp_session import (
    CLIENT_NAME,
    DEFAULT_SERVER,
    DEFAULT_VERSION,
    PROTOCOL_VERSION,
)

DEFAULT_MCP_COMMAND = ("npx", "-y", f"{DEFAULT_SERVER}@{DEFAULT_VERSION}")
DEFAULT_LOG_ROOT = Path(".staging") / "tooling_logs" / "google_trends"

CLASS_SUCCESS = "success"
CLASS_TIMEOUT = "timeout"
CLASS_DEPENDENCY = "dependency_missing"
CLASS_COLLECTOR = "collector_error"
CLASS_NETWORK = "network_or_rate_limited"
CLASS_INVALID_CONFIG = "invalid_config"

SCRIPT_EXIT_CODES = {
    CLASS_SUCCESS: 0,
    CLASS_TIMEOUT: 124,
    CLASS_DEPENDENCY: 127,
    CLASS_INVALID_CONFIG: 2,
    CLASS_NETWORK: 1,
    CLASS_COLLECTOR: 1,
}

SECRET_PATTERNS = [
    re.compile(r"(?i)(authorization:\s*bearer\s+)[^\s'\"]+"),
    re.compile(r"(?i)((?:api[_-]?key|token|secret|password)\s*[=:]\s*)[^\s'\",}]+"),
]


@dataclass
class GuardResult:
    """Serializable outcome for a bounded live-tooling operation."""

    classification: str
    command: list[str]
    timeout_seconds: float
    timed_out: bool
    exit_code: int | None
    started_at: str
    ended_at: str
    duration_seconds: float
    log_dir: str
    stdout_log: str
    stderr_log: str
    report_path: str
    message: str | None = None
    detail: dict | None = None

    def to_dict(self) -> dict:
        return {
            "classification": self.classification,
            "command": redact_command(self.command),
            "timeout_seconds": self.timeout_seconds,
            "timed_out": self.timed_out,
            "exit_code": self.exit_code,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_seconds": round(self.duration_seconds, 3),
            "log_dir": self.log_dir,
            "stdout_log": self.stdout_log,
            "stderr_log": self.stderr_log,
            "report_path": self.report_path,
            "message": self.message,
            "detail": self.detail or {},
        }


def utc_run_id(prefix: str = "gt-live-guard") -> str:
    """Return a stable filesystem-friendly timestamped identifier."""

    return datetime.now(timezone.utc).strftime(f"%Y%m%dT%H%M%SZ-{prefix}")


def redact_text(text: str) -> str:
    """Best-effort redaction before writing command output to local logs."""

    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(r"\1[REDACTED]", redacted)
    return redacted


def redact_command(command: Iterable[str]) -> list[str]:
    """Redact obvious secret-bearing command arguments in reports."""

    redacted: list[str] = []
    redact_next = False
    for part in command:
        lowered = part.lower()
        if redact_next:
            redacted.append("[REDACTED]")
            redact_next = False
            continue
        if lowered in {"--token", "--api-key", "--apikey", "--secret", "--password"}:
            redacted.append(part)
            redact_next = True
            continue
        if any(marker in lowered for marker in ("token=", "api_key=", "apikey=", "secret=", "password=")):
            key = part.split("=", 1)[0]
            redacted.append(f"{key}=[REDACTED]")
            continue
        redacted.append(part)
    return redacted


def classify_process(
    *,
    exit_code: int | None,
    timed_out: bool,
    stdout: str,
    stderr: str,
    start_error: BaseException | None = None,
) -> str:
    """Classify a child process outcome for issue-ready reporting."""

    if timed_out:
        return CLASS_TIMEOUT
    if start_error is not None:
        return CLASS_DEPENDENCY
    if exit_code == 0:
        return CLASS_SUCCESS

    combined = f"{stdout}\n{stderr}".lower()
    dependency_markers = (
        "command not found",
        "no such file or directory",
        "enoent",
        "cannot find module",
        "not recognized as an internal or external command",
    )
    network_markers = (
        "etimedout",
        "econnreset",
        "econnrefused",
        "enotfound",
        "network",
        "socket hang up",
        "too many requests",
        "rate limit",
        "ratelimit",
        "http 429",
        "status 429",
    )
    invalid_config_markers = (
        "invalid config",
        "invalid --",
        "missing required",
        "unrecognized arguments",
        "usage:",
        "cannot read plan file",
    )
    if any(marker in combined for marker in dependency_markers) or exit_code == 127:
        return CLASS_DEPENDENCY
    if any(marker in combined for marker in network_markers):
        return CLASS_NETWORK
    if any(marker in combined for marker in invalid_config_markers) or exit_code == 2:
        return CLASS_INVALID_CONFIG
    return CLASS_COLLECTOR


def _prepare_log_dir(log_root: Path, run_id: str) -> Path:
    log_dir = log_root / run_id
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def _write_logs(log_dir: Path, stdout: str, stderr: str, report: dict) -> tuple[Path, Path, Path]:
    stdout_path = log_dir / "stdout.log"
    stderr_path = log_dir / "stderr.log"
    report_path = log_dir / "report.json"
    stdout_path.write_text(redact_text(stdout), encoding="utf-8")
    stderr_path.write_text(redact_text(stderr), encoding="utf-8")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return stdout_path, stderr_path, report_path


def _finish_result(
    *,
    command: list[str],
    timeout_seconds: float,
    timed_out: bool,
    exit_code: int | None,
    started_at: datetime,
    stdout: str,
    stderr: str,
    log_dir: Path,
    message: str | None = None,
    detail: dict | None = None,
    start_error: BaseException | None = None,
) -> GuardResult:
    ended_at = datetime.now(timezone.utc)
    classification = classify_process(
        exit_code=exit_code,
        timed_out=timed_out,
        stdout=stdout,
        stderr=stderr,
        start_error=start_error,
    )
    provisional = {
        "classification": classification,
        "command": redact_command(command),
        "timeout_seconds": timeout_seconds,
        "timed_out": timed_out,
        "exit_code": exit_code,
        "started_at": started_at.isoformat(),
        "ended_at": ended_at.isoformat(),
        "duration_seconds": round((ended_at - started_at).total_seconds(), 3),
        "message": message,
        "detail": detail or {},
    }
    stdout_path, stderr_path, report_path = _write_logs(log_dir, stdout, stderr, provisional)
    result = GuardResult(
        classification=classification,
        command=command,
        timeout_seconds=timeout_seconds,
        timed_out=timed_out,
        exit_code=exit_code,
        started_at=started_at.isoformat(),
        ended_at=ended_at.isoformat(),
        duration_seconds=(ended_at - started_at).total_seconds(),
        log_dir=str(log_dir),
        stdout_log=str(stdout_path),
        stderr_log=str(stderr_path),
        report_path=str(report_path),
        message=message,
        detail=detail,
    )
    report_path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def _terminate_process(process: subprocess.Popen, grace_seconds: float = 2.0) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        process.wait(timeout=grace_seconds)
    except (OSError, subprocess.TimeoutExpired):
        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            process.wait(timeout=grace_seconds)
        except OSError:
            pass


def run_bounded_command(
    command: list[str],
    *,
    timeout_seconds: float,
    log_root: Path = DEFAULT_LOG_ROOT,
    run_id: str | None = None,
    cwd: Path | str | None = None,
) -> GuardResult:
    """Run a command with a hard timeout and issue-oriented classification."""

    run_id = run_id or utc_run_id("gt-command")
    log_dir = _prepare_log_dir(log_root, run_id)
    started_at = datetime.now(timezone.utc)
    try:
        process = subprocess.Popen(
            command,
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=(os.name == "posix"),
        )
    except OSError as error:
        return _finish_result(
            command=command,
            timeout_seconds=timeout_seconds,
            timed_out=False,
            exit_code=None,
            started_at=started_at,
            stdout="",
            stderr=f"{error.__class__.__name__}: {error}",
            log_dir=log_dir,
            message="could not start child process",
            start_error=error,
        )

    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        _terminate_process(process)
        stdout, stderr = process.communicate()

    return _finish_result(
        command=command,
        timeout_seconds=timeout_seconds,
        timed_out=timed_out,
        exit_code=process.returncode,
        started_at=started_at,
        stdout=stdout,
        stderr=stderr,
        log_dir=log_dir,
        message="child process timed out" if timed_out else None,
    )


def _json_rpc_request(request_id: int, method: str, params: dict | None = None) -> bytes:
    message = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        message["params"] = params
    return (json.dumps(message) + "\n").encode("utf-8")


def _json_rpc_notification(method: str) -> bytes:
    return (json.dumps({"jsonrpc": "2.0", "method": method}) + "\n").encode("utf-8")


def _extract_messages(buffer: bytes) -> tuple[list[dict], bytes]:
    messages = []
    while b"\n" in buffer:
        raw, buffer = buffer.split(b"\n", 1)
        line = raw.decode("utf-8", "replace").strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            messages.append(parsed)
    return messages, buffer


def probe_mcp_tools(
    command: list[str] | None = None,
    *,
    timeout_seconds: float = 30.0,
    log_root: Path = DEFAULT_LOG_ROOT,
    run_id: str | None = None,
    cwd: Path | str | None = None,
) -> GuardResult:
    """Initialize an MCP server and list tools without fetching observations."""

    command = command or list(DEFAULT_MCP_COMMAND)
    run_id = run_id or utc_run_id("gt-probe")
    log_dir = _prepare_log_dir(log_root, run_id)
    started_at = datetime.now(timezone.utc)
    stdout_chunks: list[bytes] = []
    stderr_chunks: list[bytes] = []
    stdout_buffer = b""
    init_result: dict | None = None
    tools_result: dict | None = None
    timed_out = False
    message: str | None = None

    try:
        process = subprocess.Popen(
            command,
            cwd=str(cwd) if cwd else None,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=(os.name == "posix"),
        )
    except OSError as error:
        return _finish_result(
            command=command,
            timeout_seconds=timeout_seconds,
            timed_out=False,
            exit_code=None,
            started_at=started_at,
            stdout="",
            stderr=f"{error.__class__.__name__}: {error}",
            log_dir=log_dir,
            message="could not start MCP probe process",
            start_error=error,
        )

    assert process.stdin is not None
    assert process.stdout is not None
    assert process.stderr is not None
    deadline = time.monotonic() + timeout_seconds

    try:
        process.stdin.write(
            _json_rpc_request(
                1,
                "initialize",
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": CLIENT_NAME, "version": "1.0.0"},
                },
            )
        )
        process.stdin.flush()

        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")

        while tools_result is None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                message = "MCP probe did not complete within the timeout"
                break
            events = selector.select(remaining)
            if not events and process.poll() is not None:
                message = "MCP probe process exited before tools/list completed"
                break
            if not events:
                continue
            for key, _mask in events:
                chunk = os.read(key.fileobj.fileno(), 65536)
                if chunk == b"":
                    try:
                        selector.unregister(key.fileobj)
                    except KeyError:
                        pass
                    if process.poll() is not None and tools_result is None:
                        message = "MCP probe process exited before tools/list completed"
                    continue
                if key.data == "stderr":
                    stderr_chunks.append(chunk)
                    continue
                stdout_chunks.append(chunk)
                stdout_buffer += chunk
                messages, stdout_buffer = _extract_messages(stdout_buffer)
                for rpc_message in messages:
                    if rpc_message.get("id") == 1:
                        init_result = rpc_message.get("result")
                        if process.stdin and not process.stdin.closed:
                            process.stdin.write(_json_rpc_notification("notifications/initialized"))
                            process.stdin.write(_json_rpc_request(2, "tools/list", {}))
                            process.stdin.flush()
                    elif rpc_message.get("id") == 2:
                        tools_result = rpc_message.get("result")
            if process.poll() is not None and tools_result is None:
                message = message or "MCP probe process exited before tools/list completed"
                break
        if process.stdin and not process.stdin.closed:
            process.stdin.close()
    except (OSError, ValueError) as error:
        message = f"MCP probe I/O error: {error.__class__.__name__}"
        stderr_chunks.append(f"{error.__class__.__name__}: {error}\n".encode("utf-8", "replace"))
    finally:
        _terminate_process(process)

    stdout = b"".join(stdout_chunks).decode("utf-8", "replace")
    if stdout_buffer:
        stdout += stdout_buffer.decode("utf-8", "replace")
    stderr = b"".join(stderr_chunks).decode("utf-8", "replace")
    detail = {"initialize": init_result, "tools": None}
    if isinstance(tools_result, dict):
        tools = tools_result.get("tools")
        detail["tools"] = tools if isinstance(tools, list) else None
        if not isinstance(tools, list) and not message:
            message = "MCP tools/list returned no tools array"

    exit_code = process.returncode
    if tools_result is not None and exit_code not in (0, None):
        # A server may stay alive until terminated after a successful probe.  The
        # probe's contract is satisfied once tools/list is received.
        exit_code = 0
    elif tools_result is None and exit_code == 0:
        # Exiting cleanly before the tooling contract is fulfilled is still a
        # collector/protocol failure, not a successful probe.
        exit_code = 1

    return _finish_result(
        command=command,
        timeout_seconds=timeout_seconds,
        timed_out=timed_out,
        exit_code=exit_code,
        started_at=started_at,
        stdout=stdout,
        stderr=stderr,
        log_dir=log_dir,
        message=message,
        detail=detail,
    )
