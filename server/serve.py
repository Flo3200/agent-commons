#!/usr/bin/env python3
"""Lokaler Spiegel-Server fuer dieses Repo (read-only, keine Abhaengigkeiten).

Zweck: Agenten koennen BASE=http://127.0.0.1:8765 setzen und gezielt
einzelne Dateien lesen (z.B. BASE/project/README.md), statt das ganze
Repo zu klonen/durchzulesen - spart Tokens.

GitHub bleibt die kanonische Quelle (Branches/PRs). Dieser Server
spiegelt nur den lokalen Checkout, den er im selben Repo-Ordner findet.

Start: python3 server/serve.py [port]
"""
import http.server
import os
import sys
import urllib.parse

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREFIX = "/project/"

CONTENT_TYPES = {".md": "text/markdown; charset=utf-8", ".json": "application/json"}


class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, status, body, content_type="text/plain; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url_path = urllib.parse.unquote(self.path.split("?")[0])

        if url_path in ("/", "/project"):
            self._send(
                200,
                "agent-commons lokaler Spiegel-Server\n\n"
                "Beispiel: GET /project/README.md\n"
                "Beispiel: GET /project/OVERVIEW.md\n",
            )
            return

        if not url_path.startswith(PREFIX):
            self._send(404, "Not found. Nutze /project/<pfad-im-repo>.")
            return

        rel_path = url_path[len(PREFIX):]
        file_path = os.path.abspath(os.path.join(REPO_ROOT, rel_path))

        # Path-Traversal verhindern: Zielpfad muss innerhalb REPO_ROOT bleiben.
        if not (file_path == REPO_ROOT or file_path.startswith(REPO_ROOT + os.sep)):
            self._send(403, "Forbidden.")
            return

        if not os.path.isfile(file_path):
            self._send(404, f"Not found: {rel_path}")
            return

        ext = os.path.splitext(file_path)[1]
        with open(file_path, "rb") as f:
            data = f.read()
        self._send(200, data, CONTENT_TYPES.get(ext, "text/plain; charset=utf-8"))

    def log_message(self, fmt, *args):
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PORT", 8765))
    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    print(f"agent-commons Spiegel-Server laeuft auf http://127.0.0.1:{port}")
    print(f"Beispiel: http://127.0.0.1:{port}/project/README.md")
    server.serve_forever()


if __name__ == "__main__":
    main()
