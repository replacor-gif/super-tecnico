from __future__ import annotations

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / "data" / "connectors" / "catalog.json").read_text(encoding="utf-8"))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        if parsed.path != "/api/index.php":
            return super().do_GET()
        action = parse_qs(parsed.query).get("action", [""])[0]
        if action == "admin-session":
            return self.send_json({"ok": True, "csrf": "visual-test-token"})
        if action == "admin-connector-catalog":
            return self.send_json({"ok": True, "catalog_version": CATALOG["catalog_version"], "records": CATALOG["records"]})
        if action == "admin-connector-imports":
            return self.send_json({"ok": True, "items": []})
        if action == "admin-list":
            return self.send_json({"ok": True, "items": []})
        return self.send_json({"ok": False, "error": "not_mocked"}, 404)

    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8766), Handler).serve_forever()
