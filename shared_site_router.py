#!/usr/bin/env python3
"""Shared public router and independent project-link landing page."""

import http.client
import mimetypes
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

LANDING_ROOT = Path(os.environ.get("LANDING_ROOT", "/opt/mateusz-link-hub/public")).resolve()
MASTER_PREFIX = os.environ.get("MASTER_PREFIX", "/master-compounder").rstrip("/")
LEGACY_MASTER_PREFIX = os.environ.get("LEGACY_MASTER_PREFIX", "/master_compounder").rstrip("/")
MASTER_ROOT = os.environ.get("MASTER_ROOT", "/home/opc/master_compounder_web")
TOFUFU_PREFIX = os.environ.get("TOFUFU_PREFIX", "/tofufu").rstrip("/")
TOFUFU_HOST = os.environ.get("TOFUFU_HOST", "127.0.0.1")
TOFUFU_PORT = int(os.environ.get("TOFUFU_PORT", "8083"))
THOUGHTS_HOST = os.environ.get("THOUGHTS_HOST", "127.0.0.1")
THOUGHTS_PORT = int(os.environ.get("THOUGHTS_PORT", "8082"))
PUBLIC_PORT = int(os.environ.get("PUBLIC_PORT", "8080"))

mimetypes.add_type("application/wasm", ".wasm")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/javascript", ".mjs")

LANDING_FILES = {
    "/": "index.html",
    "/index.html": "index.html",
    "/styles.css": "styles.css",
    "/assets/project-constellation.svg": "assets/project-constellation.svg",
    "/assets/favicon.svg": "assets/favicon.svg",
    "/assets/cards/profile-icon.png": "assets/cards/profile-icon.png",
    "/assets/cards/thoughts-blog-icon.svg": "assets/cards/thoughts-blog-icon.svg",
    "/assets/cards/tofufu-icon.png": "assets/cards/tofufu-icon.png",
    "/assets/cards/ballistics-wallet-icon.png": "assets/cards/ballistics-wallet-icon.png",
}


def matches_prefix(path, prefix):
    return path == prefix or path.startswith(prefix + "/")


class Router(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".wasm": "application/wasm",
        ".js": "text/javascript; charset=utf-8",
        ".mjs": "text/javascript; charset=utf-8",
        ".svg": "image/svg+xml",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=MASTER_ROOT, **kwargs)

    def log_message(self, fmt, *args):
        print(
            "%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(), fmt % args),
            flush=True,
        )

    def _path(self):
        return urlsplit(self.path).path

    def _redirect(self, location, status=308):
        self.send_response(status)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _redirect_legacy_master(self):
        parsed = urlsplit(self.path)
        suffix = parsed.path[len(LEGACY_MASTER_PREFIX) :] or "/"
        self._redirect(urlunsplit(("", "", MASTER_PREFIX + suffix, parsed.query, "")))

    def _serve_landing(self, head=False):
        relative_path = LANDING_FILES[self._path()]
        file_path = LANDING_ROOT / relative_path
        if not file_path.is_file():
            self.send_error(404, "Landing page asset is unavailable")
            return
        data = file_path.read_bytes()
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        if content_type.startswith("text/"):
            content_type += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Last-Modified", self.date_time_string(file_path.stat().st_mtime))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.send_header("Cache-Control", "no-cache" if relative_path == "index.html" else "public, max-age=3600")
        self.end_headers()
        if not head:
            self.wfile.write(data)

    def _strip_master_prefix(self):
        parsed = urlsplit(self.path)
        if parsed.path == MASTER_PREFIX:
            self._redirect(MASTER_PREFIX + "/")
            return False
        stripped = parsed.path[len(MASTER_PREFIX) :] or "/"
        self.path = urlunsplit(("", "", stripped, parsed.query, ""))
        requested = self.translate_path(self.path)
        if not os.path.exists(requested) and "." not in os.path.basename(stripped):
            self.path = urlunsplit(("", "", "/index.html", parsed.query, ""))
        return True

    def end_headers(self):
        if getattr(self, "_serving_master", False):
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
            self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
            clean = urlsplit(self.path).path
            if clean in ("/", "/index.html"):
                self.send_header("Cache-Control", "no-cache")
            elif clean.startswith(("/assets/", "/canvaskit/")) or clean.endswith((".wasm", ".js", ".mjs")):
                self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        super().end_headers()

    def _serve_master_index(self, head=False):
        index_path = os.path.join(MASTER_ROOT, "index.html")
        if not os.path.isfile(index_path):
            self.send_error(404, "Master Compounder build is missing index.html")
            return
        with open(index_path, "rb") as index_file:
            data = index_file.read().replace(b"/master_compounder/", b"/master-compounder/")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Last-Modified", self.date_time_string(os.path.getmtime(index_path)))
        self.end_headers()
        if not head:
            self.wfile.write(data)

    def _serve_master(self, head=False):
        if not self._strip_master_prefix():
            return
        self._serving_master = True
        try:
            if urlsplit(self.path).path in ("/", "/index.html"):
                return self._serve_master_index(head=head)
            return SimpleHTTPRequestHandler.do_HEAD(self) if head else SimpleHTTPRequestHandler.do_GET(self)
        finally:
            self._serving_master = False

    def _proxy(self, host, port):
        length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(length) if length else None
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in {"host", "connection", "content-length"}
        }
        headers["Host"] = self.headers.get("Host", f"{host}:{port}")
        headers["X-Forwarded-Proto"] = "http"
        headers["X-Forwarded-Host"] = self.headers.get("Host", "")
        headers["X-Real-IP"] = self.client_address[0]
        connection = http.client.HTTPConnection(host, port, timeout=30)
        try:
            connection.request(self.command, self.path, body=body, headers=headers)
            response = connection.getresponse()
            data = response.read() if self.command != "HEAD" else b""
            self.send_response(response.status, response.reason)
            for key, value in response.getheaders():
                if key.lower() not in {"connection", "transfer-encoding", "content-length"}:
                    self.send_header(key, value)
            if self.command != "HEAD":
                self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)
        finally:
            connection.close()

    def _dispatch(self, head=False):
        clean = self._path()
        if self.command in {"GET", "HEAD"} and clean in LANDING_FILES:
            return self._serve_landing(head=head)
        if matches_prefix(clean, LEGACY_MASTER_PREFIX):
            return self._redirect_legacy_master()
        if matches_prefix(clean, MASTER_PREFIX):
            return self._serve_master(head=head)
        if matches_prefix(clean, TOFUFU_PREFIX):
            return self._proxy(TOFUFU_HOST, TOFUFU_PORT)
        return self._proxy(THOUGHTS_HOST, THOUGHTS_PORT)

    def do_GET(self):
        return self._dispatch(False)

    def do_HEAD(self):
        return self._dispatch(True)

    def do_POST(self):
        return self._dispatch(False)

    def do_PUT(self):
        return self._dispatch(False)

    def do_PATCH(self):
        return self._dispatch(False)

    def do_DELETE(self):
        return self._dispatch(False)

    def do_OPTIONS(self):
        return self._dispatch(False)


if __name__ == "__main__":
    print(
        f"Serving link hub at /, thoughts via {THOUGHTS_HOST}:{THOUGHTS_PORT}, "
        f"master at {MASTER_PREFIX}/, and Tofufu at {TOFUFU_PREFIX}/ on 0.0.0.0:{PUBLIC_PORT}",
        flush=True,
    )
    ThreadingHTTPServer(("0.0.0.0", PUBLIC_PORT), Router).serve_forever()
