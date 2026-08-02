#!/usr/bin/env python3
"""Perseus Vault public demo wrapper.

This small stdlib-only HTTP service exposes a deliberately narrow slice of the
real Vault MCP server: remember, recall, context preparation, and follow-rate
feedback. Every browser session is mapped to a deterministic, opaque
workspace_hash so visitors cannot see one another's demo memories.
"""
from __future__ import annotations

import hashlib
import json
import os
import select
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PERSEUS_VAULT = os.environ.get("PERSEUS_VAULT_BIN", "/usr/local/bin/perseus-vault")
VAULT_IMAGE = os.environ.get("VAULT_IMAGE", "local/perseus-vault-demo:aesthetic-collapsible")
VAULT_VERSION = os.environ.get("VAULT_VERSION", "2.22.0")
SOURCE_REPOSITORY = os.environ.get(
    "SOURCE_REPOSITORY", "https://github.com/Perseus-Computing-LLC/perseus-vault-demo"
)
SOURCE_REVISION = os.environ.get("SOURCE_REVISION", "main")
LEDGER_URL = os.environ.get("LEDGER_URL", "https://ledger.perseus.observer")
LEDGER_ORG = os.environ.get("LEDGER_ORG", "")
LEDGER_API_KEY = os.environ.get("LEDGER_API_KEY", "")
LEDGER_EXTERNAL_REF = os.environ.get("LEDGER_EXTERNAL_REF", "vault-demo")
DB = os.environ.get("DEMO_DB", "/data/demo.db")
PORT = int(os.environ.get("PORT", "8092"))
HERE = os.path.dirname(os.path.abspath(__file__))
MAX_BODY = 16_384

_lock = threading.Lock()
_hits: dict[str, list[float]] = {}


def rate_ok(ip: str, limit: int = 40, window: int = 60) -> bool:
    now = time.time()
    queue = [stamp for stamp in _hits.get(ip, []) if now - stamp < window]
    queue.append(now)
    _hits[ip] = queue
    return len(queue) <= limit


def workspace_for(session: Any) -> str:
    """Turn a browser-provided session id into an opaque Vault scope."""
    raw = str(session or "anon")[:128].encode("utf-8", "replace")
    return hashlib.sha256(b"perseus-vault-demo:" + raw).hexdigest()[:32]


def vault_call(tool: str, args: dict[str, Any], timeout: float = 25) -> dict[str, Any]:
    """Spawn the real Vault binary, perform one MCP call, and parse its result."""
    proc = subprocess.Popen(
        [PERSEUS_VAULT, "serve", "--db", DB],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )
    deadline = time.time() + timeout

    def send(payload: dict[str, Any]) -> None:
        assert proc.stdin is not None
        proc.stdin.write(json.dumps(payload) + "\n")
        proc.stdin.flush()

    def read_until(wanted_id: int) -> dict[str, Any] | None:
        assert proc.stdout is not None
        while time.time() < deadline:
            ready, _, _ = select.select([proc.stdout], [], [], max(0.1, deadline - time.time()))
            if not ready:
                continue
            line = proc.stdout.readline()
            if not line:
                return None
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            if message.get("id") == wanted_id:
                return message
        return None

    try:
        send(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "perseus-vault-demo", "version": "2.0"},
                },
            }
        )
        if read_until(1) is None:
            return {"error": "Perseus Vault initialization timed out"}
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        send(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": tool, "arguments": args},
            }
        )
        response = read_until(2)
        if response is None:
            return {"error": "Perseus Vault request timed out"}
        if "error" in response:
            return {"error": str(response["error"])}
        content = response.get("result", {}).get("content", [])
        text = "\n".join(
            item.get("text", "") for item in content if item.get("type") == "text"
        )
        try:
            return {"ok": True, "data": json.loads(text)}
        except json.JSONDecodeError:
            return {"ok": True, "text": text}
    except OSError as exc:
        return {"error": f"Perseus Vault is unavailable: {exc}"}
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def clean_category(value: Any) -> str:
    value = str(value or "decision").strip().lower()
    return value if value in {"decision", "convention", "lesson", "preference", "fact"} else "decision"


def clean_type(value: Any) -> str:
    value = str(value or "decision").strip().lower()
    return value if value in {"decision", "convention", "insight", "reference"} else "insight"


def result_payload(out: dict[str, Any], started: float, **meta: Any) -> tuple[int, dict[str, Any]]:
    body = dict(out)
    # Vault may return internal retrieval diagnostics when a fresh demo scope
    # has no embedded memories. Keep those implementation details server-side;
    # the public product surface should explain the empty result in task terms.
    if meta.get("operation") == "recall" and isinstance(body.get("data"), dict):
        data = dict(body["data"])
        data.pop("diagnostic", None)
        body["data"] = data
    body["latency_ms"] = round((time.perf_counter() - started) * 1000, 1)
    body.update(meta)
    return (502 if out.get("error") else 200), body


def ledger_evidence() -> tuple[int, dict[str, Any]]:
    """Fetch a sanitized, scoped Ledger receipt without exposing the API key."""
    if not LEDGER_URL or not LEDGER_ORG or not LEDGER_API_KEY:
        return 503, {"error": "optional Ledger evidence is not configured"}

    query = urlencode({"org": LEDGER_ORG, "external_ref": LEDGER_EXTERNAL_REF})
    request = Request(
        f"{LEDGER_URL.rstrip('/')}/api/audit?{query}",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {LEDGER_API_KEY}",
            "User-Agent": "perseus-vault-demo/1.0",
        },
    )
    try:
        with urlopen(request, timeout=10) as response:
            receipt = json.loads(response.read(256_000))
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError):
        return 502, {"error": "Ledger evidence could not be fetched"}

    events = receipt.get("events") if isinstance(receipt, dict) else []
    verification = receipt.get("verification") if isinstance(receipt, dict) else {}
    organization = receipt.get("organization") if isinstance(receipt, dict) else {}
    if not isinstance(events, list):
        events = []
    if not isinstance(verification, dict):
        verification = {}
    if not isinstance(organization, dict):
        organization = {}
    return 200, {
        "available": True,
        "receipt_version": receipt.get("receipt_version"),
        "organization_id": organization.get("id"),
        "external_ref": receipt.get("external_ref", LEDGER_EXTERNAL_REF),
        "event_count": len(events),
        "chain_ok": verification.get("chain_ok"),
        "verified_events": verification.get("verified_events"),
        "verification_method": verification.get("method"),
        "ledger_url": LEDGER_URL,
        "events_included": False,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "PerseusVaultDemo/2"

    def _send(self, code: int, body: Any, content_type: str = "application/json") -> None:
        payload = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_args: Any) -> None:
        return

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in {"/", "/index.html"}:
            with open(os.path.join(HERE, "index.html"), "rb") as handle:
                return self._send(200, handle.read(), "text/html; charset=utf-8")
        if path == "/healthz":
            return self._send(200, {
                "ok": True,
                "service": "perseus-vault-demo",
                "runtime": "greg",
                "vault_version": VAULT_VERSION,
                "source_revision": SOURCE_REVISION,
            })
        if path == "/api/provenance":
            return self._send(200, {
                "service": "perseus-vault-demo",
                "runtime": "self-hosted Greg container",
                "sandbox": "browser-scoped workspace; never production data",
                "vault": {
                    "binary": PERSEUS_VAULT,
                    "version": VAULT_VERSION,
                },
                "source": {
                    "repository": SOURCE_REPOSITORY,
                    "revision": SOURCE_REVISION,
                },
                "ledger": {
                    "available": bool(LEDGER_URL and LEDGER_ORG and LEDGER_API_KEY),
                    "url": LEDGER_URL,
                    "external_ref": LEDGER_EXTERNAL_REF,
                    "mode": "optional evidence inspection; no demo claim is fabricated",
                },
            })
        if path == "/api/evidence":
            code, payload = ledger_evidence()
            return self._send(code, payload)
        return self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        ip = self.headers.get("CF-Connecting-IP") or self.client_address[0]
        if not rate_ok(ip):
            return self._send(429, {"error": "rate limited, slow down a moment"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_BODY:
                return self._send(413, {"error": "request too large"})
            body = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return self._send(400, {"error": "bad json"})

        path = self.path.split("?", 1)[0]
        workspace = workspace_for(body.get("session"))
        started = time.perf_counter()

        with _lock:
            if path == "/api/remember":
                text = str(body.get("text", "")).strip()[:1_200]
                if not text:
                    return self._send(400, {"error": "enter a decision or convention first"})
                key = str(body.get("key", "")).strip()[:80]
                if not key:
                    key = f"demo-{int(time.time() * 1000)}"
                category = clean_category(body.get("category"))
                entity_type = clean_type(body.get("type"))
                document = {
                    "content": text,
                    "summary": text[:240],
                    "origin": {
                        "capture_method": "public_demo",
                        "memory_kind": "asserted",
                        "source_system": "perseus-vault-demo",
                        "observed_at_unix_ms": int(time.time() * 1000),
                    },
                }
                out = vault_call(
                    "perseus_vault_remember",
                    {
                        "category": category,
                        "key": key,
                        "type": entity_type,
                        "body_json": json.dumps(document),
                        "workspace_hash": workspace,
                        "agent_id": "public-demo",
                        "importance": 0.7,
                        "tags": ["public-demo"],
                    },
                )
                code, payload = result_payload(
                    out, started, operation="remember", category=category, key=key
                )
                return self._send(code, payload)

            if path == "/api/recall":
                query = str(body.get("query", "")).strip()[:240]
                if not query:
                    return self._send(400, {"error": "ask a question first"})
                mode = str(body.get("mode", "hybrid")).strip().lower()
                if mode not in {"hybrid", "dense", "fts5"}:
                    mode = "hybrid"
                out = vault_call(
                    "perseus_vault_recall",
                    {
                        "query": query,
                        "mode": mode,
                        "limit": 8,
                        "include_confidence": True,
                        "reinforce": mode in {"hybrid", "dense"},
                        "workspace_hash": workspace,
                    },
                )
                code, payload = result_payload(
                    out, started, operation="recall", query=query, mode=mode
                )
                return self._send(code, payload)

            if path == "/api/context":
                query = str(body.get("query", "")).strip()[:400]
                if not query:
                    return self._send(400, {"error": "describe the work the agent is about to do"})
                out = vault_call(
                    "perseus_vault_context",
                    {
                        "query": query,
                        "mode": "on_demand",
                        "limit": 8,
                        "max_context_chars": 2_400,
                        "categories": ["decision", "convention", "lesson", "preference", "fact"],
                        "workspace_hash": workspace,
                    },
                )
                code, payload = result_payload(
                    out, started, operation="context", query=query
                )
                return self._send(code, payload)

            if path == "/api/follow":
                category = clean_category(body.get("category"))
                key = str(body.get("key", "")).strip()[:80]
                if not key:
                    return self._send(400, {"error": "missing memory key"})
                out = vault_call(
                    "perseus_vault_follow",
                    {
                        "category": category,
                        "key": key,
                        "followed": bool(body.get("followed", True)),
                        "context": "public demo feedback",
                        "workspace_hash": workspace,
                    },
                )
                code, payload = result_payload(
                    out, started, operation="follow", category=category, key=key
                )
                return self._send(code, payload)

        return self._send(404, {"error": "not found"})


if __name__ == "__main__":
    print(f"perseus-vault-demo on :{PORT} (vault={PERSEUS_VAULT}, db={DB})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
