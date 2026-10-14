"""Live MCP session for the Google Trends collector (stdio transport).

Where this sits in the pipeline
-------------------------------
The **pipeline collects** (``collection.core.pipeline.run_collection``: plan
validation, capability gate, adapter contract, L1 gate, catalog/quarantine).
This module is only the transport underneath the adapter: it carries
``interest_over_time`` to the ``google-trends-mcp`` server over stdio and
returns the **verbatim tool result** so the adapter parses and the pipeline
records it.  It derives nothing.

Why it is a separate module
---------------------------
``SessionMcpTransport`` accepts an injected callable and refuses without one,
so offline tests keep replaying a recorded fixture.  Live execution happens
only when a caller passes ``--live`` (see ``collection.core.cli collect``), and
the MCP server is the collector named in ``config/collectors.json``
(``google-trends-mcp``: npm, MIT, no API key, no billing).

Protocol notes
--------------
MCP over stdio is newline-delimited JSON-RPC 2.0: ``initialize``, then the
``notifications/initialized`` notification, then ``tools/call``.  Non-JSON
lines (server banners / logs) are skipped, a response is waited for with a
deadline, and any protocol or process failure raises
:class:`McpSessionError` so the adapter records a *failed* collection rather
than an empty series (AGENTS.md: a collection failure is not zero).
"""

from __future__ import annotations

import json
import os
import select
import subprocess
import time
from pathlib import Path

__all__ = ["McpSessionError", "McpStdioSession", "DEFAULT_SERVER", "DEFAULT_VERSION"]

#: The collector named in ``config/collectors.json``; version pinned so a live
#: run records which server answered (the recorded runs say 0.1.1).
DEFAULT_SERVER = "google-trends-mcp"
DEFAULT_VERSION = "0.1.1"

PROTOCOL_VERSION = "2024-11-05"
CLIENT_NAME = "japan-cannabinoid-trends"


class McpSessionError(Exception):
    """The session could not start, or a request failed."""


class McpStdioSession:
    """An MCP session over a child process' stdin/stdout.

    Use as a context manager so the child is always reaped::

        with McpStdioSession() as session:
            result = session.call("interest_over_time", params)
    """

    def __init__(
        self,
        command: list[str] | None = None,
        *,
        server: str = DEFAULT_SERVER,
        version: str = DEFAULT_VERSION,
        timeout: float = 180.0,
        cwd: Path | str | None = None,
    ) -> None:
        self.server = server
        self.version = version
        self.timeout = timeout
        self.cwd = str(cwd) if cwd else None
        self.command = command or [
            "npx",
            "-y",
            f"{server}@{version}",
        ]
        self._process: subprocess.Popen | None = None
        self._next_id = 0
        #: Line buffer for the server's stdout (see :meth:`_read_message`).
        self._buffer = b""

    # -- lifecycle ---------------------------------------------------------

    def __enter__(self) -> "McpStdioSession":
        self.start()
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    def start(self) -> None:
        if self._process is not None:
            return
        try:
            self._process = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.cwd,
            )
        except OSError as error:
            raise McpSessionError(
                f"cannot start the MCP server {self.command[0]!r}: {error.__class__.__name__}"
            ) from error

        result = self._request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": CLIENT_NAME, "version": "1.0.0"},
            },
        )
        if not isinstance(result, dict) or "serverInfo" not in result:
            raise McpSessionError("MCP initialize returned no serverInfo")
        self.server_info = result["serverInfo"]
        self._notify("notifications/initialized")

    def close(self) -> None:
        process, self._process = self._process, None
        if process is None:
            return
        try:
            if process.stdin and not process.stdin.closed:
                process.stdin.close()
            process.wait(timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            process.kill()
            process.wait(timeout=10)
        finally:
            for stream in (process.stdout, process.stderr):
                if stream and not stream.closed:
                    stream.close()
        self._buffer = b""

    # -- calls -------------------------------------------------------------

    def describe(self) -> dict:
        return {
            "collection_mode": "live",
            "transport": "mcp_stdio",
            "server": self.server,
            "server_version": self.version,
            "command": self.command,
        }

    def list_tools(self) -> list:
        result = self._request("tools/list", {})
        tools = result.get("tools") if isinstance(result, dict) else None
        if not isinstance(tools, list):
            raise McpSessionError("tools/list returned no tools")
        return tools

    def call(self, tool: str, params: dict) -> dict:
        """Invoke ``tool`` and return the verbatim tool result.

        The returned document is exactly what the server sent
        (``content`` / ``isError``), so the raw payload the pipeline stores is
        the server's response and nothing else.
        """

        result = self._request("tools/call", {"name": tool, "arguments": params})
        if not isinstance(result, dict):
            raise McpSessionError(f"{tool} returned no result object")
        return result

    # -- transport ---------------------------------------------------------

    def _request(self, method: str, params: dict):
        self._next_id += 1
        request_id = self._next_id
        self._send(
            {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        )
        while True:
            message = self._read_message()
            if message.get("id") != request_id:
                continue
            if "error" in message:
                error = message["error"]
                raise McpSessionError(
                    f"{method} failed: {error.get('code')} {error.get('message')}"
                )
            return message.get("result")

    def _notify(self, method: str) -> None:
        self._send({"jsonrpc": "2.0", "method": method})

    def _send(self, message: dict) -> None:
        process = self._process
        if process is None or process.stdin is None:
            raise McpSessionError("the MCP session is not running")
        try:
            process.stdin.write((json.dumps(message) + "\n").encode("utf-8"))
            process.stdin.flush()
        except (OSError, ValueError) as error:
            raise McpSessionError(
                f"cannot write to the MCP server: {error.__class__.__name__}"
            ) from error

    def _read_message(self) -> dict:
        """Return the next JSON-RPC message from the server.

        Reads the pipe in binary with ``os.read`` and keeps its own line buffer:
        a text wrapper (or a buffered reader) may swallow the bytes after the
        first line, which makes the following ``select`` report "no data" and
        the session time out even though the server answered.
        """

        process = self._process
        if process is None or process.stdout is None:
            raise McpSessionError("the MCP session is not running")
        deadline = time.monotonic() + self.timeout
        while True:
            while b"\n" in self._buffer:
                raw, self._buffer = self._buffer.split(b"\n", 1)
                line = raw.decode("utf-8", "replace").strip()
                if not line:
                    continue
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    continue  # server banner / log line, not a JSON-RPC message
                if isinstance(message, dict):
                    return message

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise McpSessionError(
                    f"the MCP server did not answer within {self.timeout:.0f}s"
                )
            ready, _writable, _error = select.select([process.stdout], [], [], remaining)
            if not ready:
                continue
            chunk = os.read(process.stdout.fileno(), 65536)
            if chunk == b"":
                trailing = self._buffer.decode("utf-8", "replace").strip()
                hint = f" (last output: {trailing[:120]!r})" if trailing else ""
                if process.poll() is None:
                    hint += " (the server is still running)"
                raise McpSessionError(f"the MCP server closed the session{hint}")
            self._buffer += chunk
