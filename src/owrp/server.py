from __future__ import annotations

import json
import os
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from owrp.findings import get_finding
from owrp.storage.sqlite_store import SQLiteStore


class Handler(BaseHTTPRequestHandler):
    root = Path.cwd()
    token: str | None = None
    cors_origin: str | None = None

    def send_json(self, status: int, payload: object) -> None:
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        request_origin = self.headers.get("Origin")
        if self.cors_origin and request_origin == self.cors_origin:
            self.send_header("Access-Control-Allow-Origin", self.cors_origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()
        self.wfile.write(data)

    def authorized(self) -> bool:
        if not self.token:
            return True
        supplied = self.headers.get("Authorization", "")
        expected = f"Bearer {self.token}"
        return hmac.compare_digest(supplied, expected)

    def do_OPTIONS(self) -> None:
        origin = self.headers.get("Origin")
        if not self.cors_origin or origin != self.cors_origin:
            return self.send_json(403, {"error": "cors_origin_not_allowed"})
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", self.cors_origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    @staticmethod
    def bounded_integer(raw: str, default: int, maximum: int) -> int:
        try:
            return min(maximum, max(1, int(raw)))
        except (TypeError, ValueError):
            return default

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in ("/health", "/health/live"):
            return self.send_json(200, {"status": "ok"})
        if not self.authorized():
            return self.send_json(401, {"error": "unauthorized"})

        store = SQLiteStore(self.root)
        try:
            params = parse_qs(parsed.query)
            if parsed.path == "/health/ready":
                return self.send_json(200, {"status": "ok", **store.status()})
            if parsed.path == "/api/status":
                return self.send_json(200, store.status())
            if parsed.path == "/api/repositories":
                return self.send_json(200, {"repositories": store.repositories()})
            if parsed.path == "/api/query":
                query = params.get("q", [""])[0][:500]
                limit = self.bounded_integer(params.get("limit", ["8"])[0], 8, 100)
                return self.send_json(200, {"hits": [hit.to_dict() for hit in store.query(query, limit)]})
            if parsed.path == "/api/capsules":
                return self.send_json(200, {"capsules": store.capsules()})
            if parsed.path.startswith("/api/findings/"):
                pair_id = unquote(parsed.path.removeprefix("/api/findings/")).strip()
                if not pair_id or len(pair_id) > 200 or "/" in pair_id:
                    return self.send_json(400, {"error": "invalid_finding_id"})
                finding = get_finding(store, pair_id)
                if finding is None:
                    return self.send_json(404, {"error": "finding_not_found"})
                return self.send_json(200, finding)
            return self.send_json(404, {"error": "not_found"})
        finally:
            store.close()

    def log_message(self, fmt: str, *args: object) -> None:
        return


def serve(root: Path, host: str = "127.0.0.1", port: int = 8787) -> None:
    token = os.environ.get("OWRP_API_TOKEN")
    if host not in {"127.0.0.1", "localhost", "::1"} and not token:
        raise RuntimeError("OWRP_API_TOKEN is required when binding beyond loopback")
    Handler.root = root
    Handler.token = token
    Handler.cors_origin = os.environ.get("OWRP_CORS_ORIGIN")
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"OWRP API listening on http://{host}:{port}")
    server.serve_forever()
