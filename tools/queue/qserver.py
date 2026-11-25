"""The HTTP side of the queue: dashboard page, state, and the job API for workers and agents.

Who may do what (docs/design/queue.md §1a):
  - GET (page, state, jobs, docs): this machine without a token; any other machine with the token.
  - POST (submit, cancel, claim, heartbeat, finish, release): only with the token, from anywhere,
    and only as `Content-Type: application/json` (a web page cannot send that to this server
    without a preflight, which is never answered). Without a configured token every POST is
    refused (503).
  - A job is data: the server never executes anything and a worker runs only its own tools.
"""

from __future__ import annotations

import hmac
import json
import socket
import time
from http.server import BaseHTTPRequestHandler
from pathlib import Path

from qjobs import ACTIVE, JobError, Spool

MAX_BODY = 1_000_000
ONLINE_S = 60.0
LOOPBACK = ("127.0.0.1", "::1", "::ffff:127.0.0.1")
DOCS = Path(__file__).resolve().parent / "docs"


class Registry:
    """The workers that spoke to the server recently (kept in memory; they re-announce)."""

    def __init__(self) -> None:
        self.workers: dict[str, dict] = {}

    def seen(self, worker: dict, job: str | None = None) -> None:
        name = worker.get("name")
        if not isinstance(name, str) or not name:
            raise JobError("a worker needs a name")
        self.workers[name] = {
            "name": name,
            "provides": [str(p) for p in worker.get("provides", [])],
            "allow_command": bool(worker.get("allow_command")),
            "info": worker.get("info") if isinstance(worker.get("info"), dict) else {},
            "last_seen_ts": time.time(),
            "job": job,
        }

    def snapshot(self, spool: Spool | None = None) -> list[dict]:
        held = {}
        if spool is not None:
            held = {j["claimed_by"]: j["id"] for j in spool.jobs() if j["state"] in ACTIVE}
        now = time.time()
        out = []
        for w in sorted(self.workers.values(), key=lambda w: w["name"]):
            age = now - w["last_seen_ts"]
            out.append(
                {
                    **{k: v for k, v in w.items() if k != "last_seen_ts"},
                    "job": held.get(w["name"]),
                    "age_s": round(age, 1),
                    "online": age <= ONLINE_S,
                }
            )
        return out


def lan_address() -> str | None:
    """This machine's address on the LAN (no packet is sent)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("192.0.2.1", 9))
            return s.getsockname()[0]
    except OSError:
        return None


def render_doc(name: str, server_url: str, token_set: bool) -> str | None:
    path = DOCS / f"{name}.md"
    if not path.is_file() or "/" in name:
        return None
    return (
        path.read_text()
        .replace("{{SERVER_URL}}", server_url)
        .replace("{{TOKEN_STATE}}", "set" if token_set else "NOT SET (workers cannot connect yet)")
    )


def make_handler(cache, page: bytes, spool: Spool | None, registry: Registry, token: str | None):
    class Handler(BaseHTTPRequestHandler):
        # -- plumbing ----------------------------------------------------------------------
        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, doc) -> None:
            self._send(code, json.dumps(doc).encode(), "application/json")

        def _has_token(self) -> bool:
            header = self.headers.get("Authorization", "")
            return bool(
                token
                and header.startswith("Bearer ")
                and hmac.compare_digest(header[7:].encode(), token.encode())
            )

        def _server_url(self) -> str:
            host = self.headers.get("Host", "")
            if host.startswith(("127.0.0.1", "localhost")):
                lan = lan_address()
                port = host.partition(":")[2] or "8765"
                if lan:
                    return f"http://{lan}:{port}"
            return f"http://{host}"

        # -- GET ---------------------------------------------------------------------------
        def do_GET(self) -> None:
            if self.client_address[0] not in LOOPBACK and not self._has_token():
                return self._json(401, {"error": "token required"})
            path = self.path.split("?", 1)[0]
            if path in ("/", "/index.html"):
                self._send(200, page, "text/html; charset=utf-8")
            elif path == "/api/state":
                self._json(200, cache.snapshot())
            elif path == "/api/jobs":
                self._json(200, {"jobs": spool.jobs() if spool else []})
            elif path.startswith("/docs/") and path.endswith(".md"):
                text = render_doc(path[6:-3], self._server_url(), bool(token))
                if text is None:
                    self._send(404, b"not found", "text/plain")
                else:
                    self._send(200, text.encode(), "text/markdown; charset=utf-8")
            else:
                self._send(404, b"not found", "text/plain")

        # -- POST --------------------------------------------------------------------------
        def do_POST(self) -> None:
            if not token:
                return self._json(503, {"error": "no token configured: set [server] token"})
            if not self._has_token():
                return self._json(401, {"error": "token required"})
            if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                return self._json(415, {"error": "Content-Type must be application/json"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 <= length <= MAX_BODY:
                    return self._json(413, {"error": "body too large"})
                body = json.loads(self.rfile.read(length) or b"{}")
                if not isinstance(body, dict):
                    raise TypeError("a JSON object is expected")
            except (ValueError, TypeError) as exc:
                return self._json(400, {"error": f"bad request body: {exc}"})
            if spool is None:
                return self._json(503, {"error": "this server has no spool"})
            try:
                self._json(200, self._route(self.path.split("?", 1)[0], body))
            except JobError as exc:
                self._json(409, {"error": str(exc)})
            except (KeyError, TypeError) as exc:
                self._json(400, {"error": f"missing or bad field: {exc}"})

        def _route(self, path: str, body: dict):
            parts = [p for p in path.split("/") if p]
            if parts == ["api", "jobs"]:
                allowed = (
                    "kind", "needs", "title", "priority", "first", "study", "runs",
                    "argv", "after", "submitted_by", "note",
                )  # fmt: skip
                return spool.submit(**{k: v for k, v in body.items() if k in allowed})
            if parts == ["api", "claim"]:
                worker = body["worker"]
                registry.seen(worker)
                job = spool.claim(worker)
                if job:
                    registry.seen(worker, job["id"])
                return {"job": job}
            if parts == ["api", "workers", "hello"]:
                registry.seen(body["worker"])
                return {"ok": True}
            if len(parts) == 4 and parts[:2] == ["api", "jobs"]:
                job_id, action = parts[2], parts[3]
                if action == "cancel":
                    return spool.cancel(job_id)
                if action == "priority":
                    return spool.set_priority(job_id, body["priority"])
                worker = body["worker"]
                registry.seen(worker, job_id)
                name = worker["name"]
                if action == "heartbeat":
                    return spool.heartbeat(job_id, name, body.get("progress"))
                if action == "finish":
                    return spool.finish(
                        job_id, name, body["state"], body.get("exit"), str(body.get("note", ""))
                    )
                if action == "release":
                    return spool.release(job_id, name, str(body.get("note", "")))
            raise JobError(f"no such endpoint: {path}")

        def do_PUT(self) -> None:
            self._send(405, b"method not allowed", "text/plain")

        do_DELETE = do_PATCH = do_PUT

        def log_message(self, fmt: str, *args) -> None:  # quiet
            pass

    return Handler
