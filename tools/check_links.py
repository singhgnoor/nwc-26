#!/usr/bin/env python3
"""
Dev-only: check every external link in the built page (needs network access).

    python build_site.py && python tools/check_links.py [--maps-screenshots]

For each http(s) link in site/index.html it reports the HTTP status (following
redirects) and where it finally landed. Social sites often refuse plain HTTP
clients (403/429/999) even though the page exists for a browser; those are
re-checked in a real browser (Playwright) and reported with the page title.
With --maps-screenshots it also opens each Google Maps link in a browser and
saves a screenshot to tools/out/maps-*.png so the place can be confirmed by eye.
Not part of the build; the build itself never touches the network.
"""
import argparse
import html
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "site", "index.html")
OUT = os.path.join(ROOT, "tools", "out")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def links():
    text = open(PAGE, encoding="utf-8").read()
    found = []
    for m in re.finditer(r'<a [^>]*href="(https?://[^"]+)"[^>]*>', text):
        label = re.search(r'aria-label="([^"]+)"', m.group(0))
        found.append((html.unescape(m.group(1)), html.unescape(label.group(1)) if label else ""))
    seen, out = set(), []
    for url, label in found:
        if url not in seen:
            seen.add(url)
            out.append((url, label))
    return out


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.geturl()
    except Exception as e:  # network, TLS, timeout
        return None, str(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--maps-screenshots", action="store_true")
    args = ap.parse_args()
    items = links()
    retry, failed = [], []
    print("%d external links in site/index.html\n" % len(items))
    for url, label in items:
        status, final = fetch(url)
        ok = status is not None and 200 <= status < 400
        print("%-5s %s\n      -> %s%s" % (status, url, final, ("   [%s]" % label) if label else ""))
        if not ok:
            retry.append((url, label))
    if retry or args.maps_screenshots:
        from playwright.sync_api import sync_playwright
        os.makedirs(OUT, exist_ok=True)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(user_agent=UA, locale="en-IN", viewport={"width": 1280, "height": 900})
            if retry:
                print("\nRe-checking %d link(s) in a browser:" % len(retry))
            for url, label in retry:
                try:
                    resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    status = resp.status if resp else None
                    print("%-5s %s\n      -> %s  title=%r" % (status, url, page.url, page.title()))
                    if status is None or status >= 400:
                        failed.append(url)
                except Exception as e:
                    print("FAIL  %s (%s)" % (url, e))
                    failed.append(url)
            if args.maps_screenshots:
                print("\nGoogle Maps screenshots:")
                for i, (url, label) in enumerate(u for u in items if "google.com/maps" in u[0]):
                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=45000)
                        page.wait_for_timeout(5000)
                        path = os.path.join(OUT, "maps-%d.png" % (i + 1))
                        page.screenshot(path=path)
                        print("  %s -> %s (title %r)" % (label, os.path.relpath(path, ROOT), page.title()))
                    except Exception as e:
                        print("  FAIL %s (%s)" % (url, e))
            browser.close()
    print("\n%d link(s) failed" % len(failed))
    for url in failed:
        print("  -", url)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
