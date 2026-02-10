"""MCP server inspection — connect via SSE and enumerate available tools."""

from __future__ import annotations

import json
import sys
import threading
import time
from typing import Dict, List, Optional, Tuple

import requests


class MCPInspector:
    """Minimal MCP inspector to list tool names via SSE JSON-RPC."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.sse_url = f"{self.base_url}/sse"
        self.message_url = f"{self.base_url}/message"
        self.session_url: Optional[str] = None
        self._id = 0
        self._responses: Dict[int, Dict] = {}
        self._sse_thread: Optional[threading.Thread] = None
        self._connected = threading.Event()

    def _next_id(self) -> int:
        self._id += 1
        return self._id

    def _listen_sse(self) -> None:
        try:
            resp = requests.get(self.sse_url, stream=True, timeout=(10, None))
            event_type = None
            for line in resp.iter_lines(decode_unicode=True):
                if line is None:
                    continue
                line = line.strip()
                if line.startswith("event:"):
                    event_type = line[len("event:"):].strip()
                elif line.startswith("data:"):
                    data = line[len("data:"):].strip()
                    if event_type == "endpoint":
                        if data.startswith("http"):
                            self.session_url = data
                        else:
                            self.session_url = f"{self.base_url}{data}"
                        self._connected.set()
                    elif event_type == "message":
                        try:
                            msg = json.loads(data)
                            if "id" in msg:
                                self._responses[msg["id"]] = msg
                        except Exception:
                            pass
                    event_type = None
        except Exception as exc:
            print(f"[SSE] error: {exc}", file=sys.stderr)

    def _send(self, method: str, params: Optional[dict] = None) -> dict:
        rid = self._next_id()
        payload: dict = {"jsonrpc": "2.0", "id": rid, "method": method}
        if params is not None:
            payload["params"] = params

        url = self.session_url or self.message_url
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()

        for _ in range(100):
            if rid in self._responses:
                return self._responses.pop(rid)
            time.sleep(0.1)
        return {"error": "timeout waiting for response"}

    def connect(self) -> None:
        self._sse_thread = threading.Thread(target=self._listen_sse, daemon=True)
        self._sse_thread.start()
        if not self._connected.wait(timeout=10):
            raise RuntimeError("Timed out waiting for SSE endpoint event")

    def initialize(self) -> dict:
        return self._send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "toolshield-inspector", "version": "0.1.0"},
        })

    def list_tools(self) -> dict:
        return self._send("tools/list", {})


def inspect_mcp_tools(base_url: str) -> Tuple[str, List[str]]:
    """Connect to an MCP server and return (description, tool_names)."""
    inspector = MCPInspector(base_url)
    inspector.connect()
    init_resp = inspector.initialize()
    tools_resp = inspector.list_tools()

    description = ""
    try:
        server_info = init_resp.get("result", {}).get("serverInfo", {})
        description = server_info.get("description") or server_info.get("name") or ""
    except Exception:
        description = ""

    tools = tools_resp.get("result", {}).get("tools", [])
    tool_names = [t.get("name") for t in tools if t.get("name")]
    if not tool_names:
        raise RuntimeError("No tools found from MCP server.")
    return description, tool_names
