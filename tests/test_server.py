"""server.py: routing, HEAD/GET parity, headers, caching, and every traversal / leak attempt."""
import email.utils
import os
import subprocess
import sys
import unittest

from tests.helpers import PREFIX, REPO, RunningServer, cleanup, make_fixture, raw_request, server

LOG_LINES = []


def setUpModule():
    server.log = LOG_LINES.append  # keep test output quiet, but let tests inspect the log


class ServerTestCase(unittest.TestCase):
    with_404 = True

    @classmethod
    def setUpClass(cls):
        cls.tmp, cls.site = make_fixture(with_404=cls.with_404)
        cls.srv = RunningServer(cls.site)

    @classmethod
    def tearDownClass(cls):
        cls.srv.stop()
        cleanup(cls.tmp)

    def get(self, path, method="GET", **kw):
        return raw_request(self.srv.port, method, path, **kw)

    def assertNotLeaked(self, response):
        self.assertEqual(response.status, 404, response.status_line)
        self.assertNotIn(b"SECRET", response.body)


class TestRouting(ServerTestCase):
    def test_root_and_prefix_serve_index(self):
        for path in ("/", PREFIX + "/", PREFIX + "/index.html", "/index.html"):
            r = self.get(path)
            self.assertEqual(r.status, 200, path)
            self.assertIn(b"HOME-PAGE", r.body)
            self.assertEqual(r.header("Content-Type"), "text/html; charset=utf-8")

    def test_clean_urls(self):
        for path in ("/about", "/about.html", PREFIX + "/about", PREFIX + "/about.html"):
            r = self.get(path)
            self.assertEqual(r.status, 200, path)
            self.assertIn(b"ABOUT-PAGE", r.body)
        r = self.get(PREFIX + "/hi/")
        self.assertEqual(r.status, 200)
        self.assertIn(b"HINDI-PAGE", r.body)

    def test_head_matches_get(self):
        for path in ("/", PREFIX + "/", PREFIX + "/about", "/assets/css/main.css", "/missing", "/healthz",
                     PREFIX, "/.git/HEAD"):
            g, h = self.get(path), self.get(path, "HEAD")
            self.assertEqual(g.status, h.status, path)
            strip = lambda r: {k: v for k, v in r.headers.items() if k != "date"}
            self.assertEqual(strip(g), strip(h), path)
            self.assertEqual(h.body, b"", path)

    def test_bare_prefix_redirects_with_slash(self):
        r = self.get(PREFIX)
        self.assertEqual(r.status, 301)
        self.assertEqual(r.header("Location"), PREFIX + "/")
        r = self.get(PREFIX + "?utm=mail")
        self.assertEqual(r.header("Location"), PREFIX + "/?utm=mail")

    def test_folder_without_slash_redirects(self):
        r = self.get(PREFIX + "/hi")
        self.assertEqual(r.status, 301)
        self.assertEqual(r.header("Location"), PREFIX + "/hi/")
        self.assertEqual(self.get("/hi").header("Location"), "/hi/")

    def test_prefix_must_end_at_a_path_boundary(self):
        self.assertEqual(self.get(PREFIX + "foo").status, 404)
        self.assertEqual(self.get(PREFIX + "foo/").status, 404)

    def test_custom_404_with_base_href(self):
        r = self.get(PREFIX + "/a/b/missing")
        self.assertEqual(r.status, 404)
        self.assertIn(b"CUSTOM-404", r.body)
        self.assertIn(('<base href="%s/">' % PREFIX).encode(), r.body)
        self.assertEqual(r.header("Cache-Control"), "no-cache")
        r = self.get("/missing")
        self.assertIn(b'<base href="/">', r.body)

    def test_other_methods_get_405(self):
        for method in ("POST", "PUT", "DELETE", "PATCH", "OPTIONS", "TRACE", "FOO"):
            r = self.get(PREFIX + "/", method)
            self.assertEqual(r.status, 405, method)
            self.assertEqual(r.header("Allow"), "GET, HEAD", method)
            self.assertIn("content-security-policy", r.headers, method)

    def test_healthz(self):
        for path in ("/healthz", PREFIX + "/healthz"):
            r = self.get(path)
            self.assertEqual(r.status, 200)
            self.assertEqual(r.body, b"ok\n")
            self.assertTrue(r.header("Content-Type").startswith("text/plain"))

    def test_security_headers_on_every_response(self):
        expected = {
            "x-content-type-options": "nosniff",
            "referrer-policy": "strict-origin-when-cross-origin",
            "x-frame-options": "SAMEORIGIN",
            "permissions-policy": "camera=(), microphone=(), geolocation=()",
            "content-security-policy": server.CSP,
        }
        for path, method in (("/", "GET"), ("/missing", "GET"), (PREFIX, "GET"), ("/", "POST"),
                             ("/assets/css/main.css", "GET"), ("/healthz", "HEAD")):
            r = self.get(path, method)
            for name, value in expected.items():
                self.assertEqual(r.header(name), value, (path, method, name))
            self.assertEqual(r.header("Server"), "nwc")
            self.assertNotIn("python", r.header("Server").lower())

    def test_mime_types(self):
        self.assertEqual(self.get("/assets/img/logo.svg").header("Content-Type"), "image/svg+xml")
        self.assertEqual(self.get("/assets/fonts/f.woff2").header("Content-Type"), "font/woff2")
        self.assertEqual(self.get("/assets/css/main.css").header("Content-Type"), "text/css; charset=utf-8")
        for ext, mime in ((".webp", "image/webp"), (".avif", "image/avif"), (".json", "application/json"),
                          (".webmanifest", "application/manifest+json"), (".ico", "image/x-icon")):
            self.assertEqual(server.Handler.extensions_map[ext], mime)

    def test_caching(self):
        self.assertEqual(self.get("/").header("Cache-Control"), "no-cache")
        self.assertEqual(self.get("/assets/css/main.css").header("Cache-Control"), "public, max-age=86400")
        r = self.get("/assets/css/main.css")
        self.assertIsNotNone(r.header("Last-Modified"))

    def test_if_modified_since(self):
        mtime = os.path.getmtime(os.path.join(self.site, "assets", "css", "main.css"))
        later = email.utils.formatdate(mtime + 60, usegmt=True).encode()
        earlier = email.utils.formatdate(mtime - 3600, usegmt=True).encode()
        r = self.get("/assets/css/main.css", extra_headers=b"If-Modified-Since: " + later + b"\r\n")
        self.assertEqual(r.status, 304)
        self.assertEqual(r.body, b"")
        r = self.get("/assets/css/main.css", extra_headers=b"If-Modified-Since: " + earlier + b"\r\n")
        self.assertEqual(r.status, 200)
        r = self.get("/assets/css/main.css", extra_headers=b"If-Modified-Since: not a date\r\n")
        self.assertEqual(r.status, 200)

    def test_log_line(self):
        LOG_LINES.clear()
        self.get(PREFIX + "/about", extra_headers=b"X-Forwarded-For: 6.6.6.6, 203.0.113.9\r\n")
        line = [l for l in LOG_LINES if "/about" in l][-1]
        self.assertIn('203.0.113.9 "GET %s/about" 200' % PREFIX, line)
        self.assertNotIn("6.6.6.6", line)  # spoofable entries ignored
        self.assertTrue(line.endswith("ms"))


class TestTraversalAndLeaks(ServerTestCase):
    def test_traversal_attempts(self):
        attempts = [
            "/../server.py", "/%2e%2e/server.py", "/%252e%252e/", "/%252e%252e/server.py", "/..%2fserver.py",
            "/.git/HEAD", "/.env", "/assets/../../build_site.py", "/assets/%2e%2e/%2e%2e/build_site.py",
            PREFIX + "/../server.py", PREFIX + "/%2e%2e/outside.txt", PREFIX + "/.git/HEAD", PREFIX + "/.env",
            "/..", "/%2e%2e", "/./index.html", "/emptydir/", "/emptydir", "/emptydir/notindex",
            "/%2e%2e%5cserver.py", "/..%5cserver.py", "/%c0%ae%c0%ae/server.py", "/%ff",
            "//server.py", "/assets//../../server.py",
        ]
        for path in attempts:
            with self.subTest(path=path):
                self.assertNotLeaked(self.get(path))
                self.assertNotLeaked(self.get(path, "HEAD"))

    def test_raw_backslash_and_nul(self):
        for raw in (b"/..\\server.py", b"/assets\\..\\..\\server.py", b"/index.html\x00.txt", b"/%00",
                    b"/index.html%00", b"/x%0d%0aSet-Cookie:%20a=b"):
            with self.subTest(raw=raw):
                r = raw_request(self.srv.port, "GET", "", raw_path=raw)
                self.assertIn(r.status, (400, 404))
                self.assertNotIn(b"SECRET", r.body)
                self.assertNotIn("set-cookie", r.headers)

    def test_symlink_escape(self):
        link = os.path.join(self.site, "escape.txt")
        dirlink = os.path.join(self.site, "escapedir")
        try:
            os.symlink(os.path.join(self.tmp, "outside.txt"), link)
            os.symlink(self.tmp, dirlink, target_is_directory=True)
        except (OSError, NotImplementedError) as e:
            self.skipTest("symlinks not available here: %s" % e)
        try:
            for path in ("/escape.txt", "/escapedir/outside.txt", "/escapedir/server.py", "/escapedir/"):
                with self.subTest(path=path):
                    self.assertNotLeaked(self.get(path))
        finally:
            os.remove(link)
            os.remove(dirlink) if os.path.islink(dirlink) else os.rmdir(dirlink)

    def test_malformed_request_line(self):
        with __import__("socket").create_connection(("127.0.0.1", self.srv.port), timeout=10) as sock:
            sock.sendall(b"GARBAGE\r\n\r\n")
            data = sock.recv(65536)
        # The stdlib answers a one-word request line HTTP/0.9-style (body only). What matters:
        # nothing leaks, and the server keeps serving afterwards.
        self.assertIn(b"Bad request", data)
        self.assertNotIn(b"SECRET", data)
        r = raw_request(self.srv.port, "GET", "", raw_path=b"/ HTTP/1.0 extra")
        self.assertEqual(r.status, 400)
        self.assertIn("content-security-policy", r.headers)
        self.assertEqual(self.get("/").status, 200)  # still serving


class TestFallback404(ServerTestCase):
    with_404 = False

    def test_plain_text_404_when_page_missing(self):
        r = self.get("/missing")
        self.assertEqual(r.status, 404)
        self.assertEqual(r.body, b"Not found\n")
        self.assertTrue(r.header("Content-Type").startswith("text/plain"))


class TestStartup(unittest.TestCase):
    def test_fails_fast_without_index(self):
        tmp, site = make_fixture()
        try:
            os.remove(os.path.join(site, "index.html"))
            env = dict(os.environ, NWC_SITE_DIR=site, NWC_PORT="0")
            p = subprocess.run([sys.executable, os.path.join(REPO, "server.py")], env=env,
                               capture_output=True, text=True, timeout=30)
            self.assertNotEqual(p.returncode, 0)
            self.assertIn("no index.html", p.stderr)
            self.assertIn("build_site.py", p.stderr)
        finally:
            cleanup(tmp)

    @unittest.skipIf(os.name == "nt", "SIGTERM cannot be caught on Windows; runs on the Linux server")
    def test_sigterm_stops_cleanly(self):
        import signal
        import socket
        import time
        tmp, site = make_fixture()
        with socket.socket() as s:  # find a free port
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        env = dict(os.environ, NWC_SITE_DIR=site, NWC_PORT=str(port))
        p = subprocess.Popen([sys.executable, os.path.join(REPO, "server.py")], env=env,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            for _ in range(100):
                try:
                    socket.create_connection(("127.0.0.1", port), timeout=1).close()
                    break
                except OSError:
                    time.sleep(0.05)
            p.send_signal(signal.SIGTERM)
            output, _ = p.communicate(timeout=10)
            self.assertEqual(p.returncode, 0, output)
            self.assertIn("nwc: stopped", output)
        finally:
            if p.poll() is None:
                p.kill()
            cleanup(tmp)

    def test_prefix_parsing(self):
        self.assertEqual(server.parse_prefixes("/a/, /b ,"), ["/a", "/b"])
        with self.assertRaises(SystemExit):
            server.parse_prefixes("no-slash")

    def test_longest_prefix_wins(self):
        tmp, site = make_fixture()
        srv = RunningServer(site, prefixes=(PREFIX, PREFIX + "/staging"))
        try:
            os.makedirs(os.path.join(site, "staging"), exist_ok=True)
            r = raw_request(srv.port, "GET", PREFIX + "/staging/about")
            self.assertEqual(r.status, 200)
            self.assertIn(b"ABOUT-PAGE", r.body)
        finally:
            srv.stop()
            cleanup(tmp)


if __name__ == "__main__":
    unittest.main()
