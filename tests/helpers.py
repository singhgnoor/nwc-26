"""Shared test helpers: a fixture site, a server on an ephemeral port, and raw HTTP requests."""
import os
import shutil
import socket
import sys
import tempfile
import threading

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import server  # noqa: E402

PREFIX = "/national-wellbeing-conclave-2026"


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def make_fixture(with_404=True):
    """A temp folder laid out like the repo: secrets OUTSIDE site/, a small site INSIDE it."""
    tmp = tempfile.mkdtemp(prefix="nwc-test-")
    write(os.path.join(tmp, "server.py"), "SECRET-SERVER-SOURCE")
    write(os.path.join(tmp, "build_site.py"), "SECRET-BUILD-SOURCE")
    write(os.path.join(tmp, ".env"), "SECRET-ENV")
    write(os.path.join(tmp, ".git", "HEAD"), "SECRET-GIT-HEAD")
    write(os.path.join(tmp, "outside.txt"), "SECRET-OUTSIDE")
    site = os.path.join(tmp, "site")
    write(os.path.join(site, "index.html"), "<!doctype html><html><head><title>home</title></head><body>HOME-PAGE</body></html>")
    write(os.path.join(site, "about.html"), "<!doctype html><html><head></head><body>ABOUT-PAGE</body></html>")
    write(os.path.join(site, "hi", "index.html"), "<!doctype html><html><head></head><body>HINDI-PAGE</body></html>")
    write(os.path.join(site, "assets", "css", "main.css"), ":root{--x:1}")
    write(os.path.join(site, "assets", "img", "logo.svg"), "<svg xmlns='http://www.w3.org/2000/svg'/>")
    write(os.path.join(site, "assets", "fonts", "f.woff2"), "font")
    write(os.path.join(site, "emptydir", "notindex.txt"), "SECRET-LISTING")
    write(os.path.join(site, ".env"), "SECRET-SITE-DOTFILE")
    write(os.path.join(site, ".git", "HEAD"), "SECRET-SITE-GIT")
    if with_404:
        write(os.path.join(site, "404.html"),
              "<!doctype html><html><head><title>nf</title></head><body>CUSTOM-404</body></html>")
    return tmp, site


class RunningServer:
    def __init__(self, site_dir, prefixes=(PREFIX,)):
        self.httpd = server.Server(("127.0.0.1", 0), site_dir, list(prefixes))
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()


class Response:
    def __init__(self, raw):
        head, _, self.body = raw.partition(b"\r\n\r\n")
        lines = head.decode("latin-1").split("\r\n")
        self.status_line = lines[0]
        self.status = int(lines[0].split()[1])
        self.headers = {}
        self.header_names = []
        for line in lines[1:]:
            name, _, value = line.partition(":")
            self.headers[name.strip().lower()] = value.strip()
            self.header_names.append(name.strip().lower())

    def header(self, name):
        return self.headers.get(name.lower())


def raw_request(port, method, path, extra_headers=b"", raw_path=None):
    """Send exactly the bytes given (no client-side normalisation) and read until close."""
    target = raw_path if raw_path is not None else path.encode("latin-1")
    request = method.encode() + b" " + target + b" HTTP/1.0\r\nHost: localhost\r\n" + extra_headers + b"\r\n"
    with socket.create_connection(("127.0.0.1", port), timeout=10) as sock:
        sock.sendall(request)
        chunks = []
        while True:
            data = sock.recv(65536)
            if not data:
                break
            chunks.append(data)
    return Response(b"".join(chunks))


def cleanup(tmp):
    shutil.rmtree(tmp, ignore_errors=True)
