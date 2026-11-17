#!/usr/bin/env python3
"""
Web server for the Samarasyam 2026 portal (3rd National Well-being Conclave).

    browser -> nginx (iitrpr.ac.in) -> this process on 127.0.0.1:8100

It serves ONLY the files in the built site/ folder, read-only. There is no
database, no API and nothing that stores what visitors send. Standard library
only, Python 3.8+. Settings come from environment variables:

    NWC_HOST      address to listen on      (default 127.0.0.1)
    NWC_PORT      port to listen on         (default 8100)
    NWC_SITE_DIR  folder to serve           (default: site/ next to this file)
    NWC_PREFIXES  URL prefixes nginx passes (default /national-wellbeing-conclave-2026,
                  comma-separated, e.g. to add a staging prefix)
"""
import email.utils
import os
import posixpath
import shutil
import signal
import sys
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

HERE = os.path.dirname(os.path.abspath(__file__))
CSP = ("default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
       "font-src 'self'; frame-src https://docs.google.com; form-action https://docs.google.com; "
       "base-uri 'self'; frame-ancestors 'self'")
SECURITY_HEADERS = (
    ("X-Content-Type-Options", "nosniff"),
    ("Referrer-Policy", "strict-origin-when-cross-origin"),
    ("X-Frame-Options", "SAMEORIGIN"),
    ("Permissions-Policy", "camera=(), microphone=(), geolocation=()"),
    ("Content-Security-Policy", CSP),
)


def log(message):
    print(time.strftime("%Y-%m-%dT%H:%M:%S ") + message, flush=True)


def printable(text):
    """Escape control and non-ASCII characters so a request can't forge log lines."""
    out = []
    for c in str(text):
        o = ord(c)
        out.append(c if 32 <= o < 127 and c != '"' else ("\\x%02x" % o if o < 256 else "\\u%04x" % o))
    return "".join(out)


class Handler(BaseHTTPRequestHandler):
    server_version = "nwc"   # the Server header; hides the Python version
    sys_version = ""
    timeout = 30             # seconds; a slow or idle client can't hold a thread forever
    extensions_map = {
        ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
        ".js": "text/javascript; charset=utf-8", ".json": "application/json",
        ".txt": "text/plain; charset=utf-8", ".xml": "application/xml",
        ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".gif": "image/gif", ".webp": "image/webp", ".avif": "image/avif", ".ico": "image/x-icon",
        ".woff2": "font/woff2", ".woff": "font/woff", ".pdf": "application/pdf",
        ".webmanifest": "application/manifest+json",
    }

    def version_string(self):
        return self.server_version

    # ----- Plumbing: one log line per request, security headers on every response -----
    def handle_one_request(self):
        self._started, self._status, self._sent = time.monotonic(), None, 0
        try:
            super().handle_one_request()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            self.close_connection = True
            self._log_request_line("client disconnected")
            return
        if self._status is not None:
            self._log_request_line()

    def _log_request_line(self, note=""):
        headers = getattr(self, "headers", None)
        forwarded = headers.get("X-Forwarded-For", "") if headers else ""
        # nginx appends the real client address last; earlier entries can be faked by the client.
        client = forwarded.split(",")[-1].strip() or self.client_address[0]
        log('%s "%s %s" %s %d %.1fms%s' % (
            printable(client), printable(getattr(self, "command", None) or "-"),
            printable(getattr(self, "path", None) or "-"), self._status or "-", self._sent,
            (time.monotonic() - self._started) * 1000, (" " + note) if note else ""))

    def log_request(self, code="-", size="-"):
        pass  # replaced by _log_request_line, which also records bytes and duration

    def log_message(self, fmt, *args):
        log("%s %s" % (self.client_address[0], printable(fmt % args)))

    def send_response(self, code, message=None):
        self._status = code
        super().send_response(code, message)

    def end_headers(self):
        for name, value in SECURITY_HEADERS:
            self.send_header(name, value)
        super().end_headers()

    def send_error(self, code, message=None, explain=None):
        # Used by the standard library for malformed requests (400, 414, 431, ...).
        self.close_connection = True
        self._send_text(code, message or HTTPStatus(code).phrase)

    def _write(self, body):
        if getattr(self, "command", None) != "HEAD":  # HEAD: same headers, no body
            self.wfile.write(body)
            self._sent += len(body)

    def _send_text(self, code, text, extra_headers=()):
        body = (text + "\n").encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        for name, value in extra_headers:
            self.send_header(name, value)
        self.end_headers()
        self._write(body)

    def __getattr__(self, name):
        # Any method other than GET and HEAD (POST, PUT, DELETE, ...) gets 405.
        if name.startswith("do_"):
            return lambda: self._send_text(405, "Method not allowed", [("Allow", "GET, HEAD")])
        raise AttributeError(name)

    # ----- Requests -----
    def do_GET(self):
        target, _, query = self.path.partition("?")
        target = target.partition("#")[0]
        if not target.startswith("/") or any(ord(c) < 32 or ord(c) == 127 for c in self.path):
            return self._not_found("")
        prefix = ""
        for p in self.server.prefixes:  # longest first
            if target == p:  # relative links need the trailing slash
                return self._redirect(p + "/" + ("?" + query if query else ""))
            if target.startswith(p + "/"):
                prefix, target = p, target[len(p):]
                break
        if target == "/healthz":
            return self._send_text(200, "ok")
        found = self._resolve(target)
        if found == "add-slash":
            return self._redirect(prefix + target + "/" + ("?" + query if query else ""))
        if found is None:
            return self._not_found(prefix)
        self._send_file(found)

    do_HEAD = do_GET  # identical status and headers; _write() leaves out the body

    def _resolve(self, target):
        """Map a URL path to a regular file inside site/. Returns a path, "add-slash" or None."""
        try:
            decoded = unquote(target, errors="strict")  # decode exactly once
        except UnicodeDecodeError:
            return None
        for p in (target, decoded, posixpath.normpath(decoded)):
            if "\x00" in p or "\\" in p or any(ord(c) < 32 for c in p):
                return None
            if any(seg.startswith(".") for seg in p.split("/")):  # "..", ".git", ".env", "."
                return None
        base = os.path.join(self.server.site_dir, *[s for s in decoded.split("/") if s])
        # Clean URLs: /x -> x, then x.html; /x/ -> x/index.html
        candidates = [os.path.join(base, "index.html")] if decoded.endswith("/") else [base, base + ".html"]
        for candidate in candidates:
            real = self._inside_site(candidate)
            if real and os.path.isfile(real):
                return real
        if not decoded.endswith("/") and self._inside_site(os.path.join(base, "index.html")):
            if os.path.isfile(os.path.join(base, "index.html")):
                return "add-slash"  # a folder: /hi -> /hi/
        return None  # includes folders without index.html: never a listing

    def _inside_site(self, path):
        """The real path (symlinks resolved) if it is inside site/ and not a dotfile, else None."""
        root, real = self.server.site_dir, os.path.realpath(path)
        try:
            if os.path.commonpath([root, real]) != root:
                return None
        except ValueError:  # e.g. a different drive on Windows
            return None
        if any(seg.startswith(".") for seg in os.path.relpath(real, root).split(os.sep) if seg != "."):
            return None
        return real

    def _send_file(self, path):
        try:
            f = open(path, "rb")
        except OSError:
            return self._not_found("")
        with f:
            size, mtime = os.fstat(f.fileno()).st_size, int(os.fstat(f.fileno()).st_mtime)
            rel = os.path.relpath(path, self.server.site_dir).replace(os.sep, "/")
            cache = "public, max-age=86400" if rel.startswith("assets/") else "no-cache"
            last_modified = email.utils.formatdate(mtime, usegmt=True)
            since = self.headers.get("If-Modified-Since")
            if since:
                try:
                    if mtime <= email.utils.parsedate_to_datetime(since).timestamp():
                        self.send_response(304)
                        self.send_header("Last-Modified", last_modified)
                        self.send_header("Cache-Control", cache)
                        return self.end_headers()
                except (TypeError, ValueError, IndexError, OverflowError):
                    pass  # unreadable date: just send the file
            ext = os.path.splitext(path)[1].lower()
            self.send_response(200)
            self.send_header("Content-Type", self.extensions_map.get(ext, "application/octet-stream"))
            self.send_header("Content-Length", str(size))
            self.send_header("Last-Modified", last_modified)
            self.send_header("Cache-Control", cache)
            self.end_headers()
            if self.command != "HEAD":
                shutil.copyfileobj(f, self.wfile)
                self._sent += size

    def _redirect(self, location):
        self.send_response(301)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _not_found(self, prefix):
        try:
            with open(os.path.join(self.server.site_dir, "404.html"), "rb") as f:
                body = f.read()
        except OSError:
            return self._send_text(404, "Not found")
        # A <base> makes the page's relative links work at any depth, e.g. /prefix/a/b/c.
        body = body.replace(b"<head>", b'<head>\n<base href="' + (prefix + "/").encode() + b'">', 1)
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self._write(body)


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, site_dir, prefixes):
        self.site_dir = os.path.realpath(site_dir)
        self.prefixes = sorted(prefixes, key=len, reverse=True)
        super().__init__(address, Handler)

    def handle_error(self, request, client_address):
        log("%s internal error: %r" % (client_address[0], sys.exc_info()[1]))


def parse_prefixes(value):
    prefixes = [p.strip().rstrip("/") for p in value.split(",") if p.strip().rstrip("/")]
    for p in prefixes:
        if not p.startswith("/"):
            sys.exit("nwc: every NWC_PREFIXES entry must start with '/': %r" % p)
    return prefixes


def stop(signum, frame):
    raise KeyboardInterrupt  # unwinds serve_forever() so systemctl stop/restart is clean


def main():
    site_dir = os.path.realpath(os.environ.get("NWC_SITE_DIR") or os.path.join(HERE, "site"))
    if not os.path.isfile(os.path.join(site_dir, "index.html")):
        sys.exit("nwc: %s has no index.html. Build the site first: python3 build_site.py" % site_dir)
    host = os.environ.get("NWC_HOST", "127.0.0.1")
    try:
        port = int(os.environ.get("NWC_PORT", "8100"))
    except ValueError:
        sys.exit("nwc: NWC_PORT must be a number")
    prefixes = parse_prefixes(os.environ.get("NWC_PREFIXES", "/national-wellbeing-conclave-2026"))
    server = Server((host, port), site_dir, prefixes)
    signal.signal(signal.SIGTERM, stop)
    log("nwc: serving %s on http://%s:%d (prefixes: %s)" % (site_dir, host, port, ", ".join(prefixes) or "none"))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        log("nwc: stopped")


if __name__ == "__main__":
    main()
