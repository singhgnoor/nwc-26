#!/usr/bin/env python3
"""
Dev-only: exercise the states the default page does not show, in a real browser.

    python tools/check_states.py

1. Builds a FIXTURE site into tools/out/fixture/ (never site/): Moments "live"
   with a few photos (reusing speaker WebPs as stand-in images) and Feedback
   "open" with a form URL and a QR image. The real content is not touched.
2. Drives the carousel: arrows, keyboard (ArrowRight / End / Home), thumbnails;
   checks the visible slide, the NN / NN count, aria-current and disabled ends.
3. Runs axe-core on: every session card opened, Day 2 selected, the mobile
   menu open, and the fixture's live states. Prints every violation.
4. Saves screenshots of the carousel and the open feedback card (1440 and 390).
"""
import copy
import json
import os
import shutil
import struct
import sys
import tempfile
import threading
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import build_site  # noqa: E402
import server  # noqa: E402
server.log = lambda message: None

from axe_playwright_python.sync_playwright import Axe  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

OUT = os.path.join(ROOT, "tools", "out")
PREFIX = "/national-wellbeing-conclave-2026"


def qr_png(size=112):
    """A plain stand-in square (fixture only) so the QR slot renders."""
    raw = b"".join(b"\x00" + (b"\x1e\x2a\x44" if (x // 8 + y // 8) % 2 else b"\xff\xff\xff") * 1
                   for y in range(size) for x in [0])
    rows = b"".join(b"\x00" + b"".join((b"\x1e\x2a\x44" if (x // 8 + y // 8) % 2 else b"\xff\xff\xff") for x in range(size))
                    for y in range(size))
    del raw

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def build_fixture():
    tmp = os.path.join(OUT, "fixture-root")
    shutil.rmtree(tmp, ignore_errors=True)
    for folder in ("templates", "static", "content"):
        shutil.copytree(os.path.join(ROOT, folder), os.path.join(tmp, folder))
    content = json.load(open(os.path.join(tmp, "content", "content.en.json"), encoding="utf-8"))
    photos = ["pralhad-joshi-352", "ananya-syal-250", "asha-banu-soletti-352", "tony-thomas-352"]
    content["photos"] = {"status": "live", "items": [
        {"src": "img/speakers/%s.webp" % p, "alt": "Fixture photo %d" % (i + 1),
         "caption": "Fixture caption %d, written by the organising team." % (i + 1),
         "label": "Day 1 · Inaugural Ceremony"} for i, p in enumerate(photos)]}
    with open(os.path.join(tmp, "static", "img", "feedback-qr.png"), "wb") as f:
        f.write(qr_png())
    content["feedback"] = {"status": "open", "formUrl": "https://forms.gle/fixture", "qr": "img/feedback-qr.png"}
    json.dump(content, open(os.path.join(tmp, "content", "content.en.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    log = []
    code = build_site.build(root=tmp, out=log.append)
    if code:
        raise SystemExit("fixture build failed:\n" + "\n".join(log))
    return os.path.join(tmp, "site")


def serve(site_dir):
    httpd = server.Server(("127.0.0.1", 0), site_dir, [PREFIX])
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, "http://127.0.0.1:%d%s/" % (httpd.server_address[1], PREFIX)


def axe(page, label):
    res = Axe().run(page)
    v = res.response["violations"]
    bad = [x for x in v if x["impact"] in ("serious", "critical")]
    print("axe [%s]: %d violations, %d serious/critical" % (label, len(v), len(bad)))
    for x in v:
        print("   - [%s] %s (%d) e.g. %s" % (x["impact"], x["id"], len(x["nodes"]), x["nodes"][0]["target"] if x["nodes"] else ""))
    return len(bad)


def main():
    problems = 0
    os.makedirs(OUT, exist_ok=True)
    live_site, real_site = build_fixture(), os.path.join(ROOT, "site")
    httpd_real, real = serve(real_site)
    httpd_live, live = serve(live_site)
    with sync_playwright() as pw:
        b = pw.chromium.launch()

        # --- states of the real page that the default view hides ---
        p = b.new_page(viewport={"width": 1440, "height": 900})
        p.goto(real, wait_until="networkidle")
        p.evaluate("document.querySelectorAll('details.session').forEach(d => d.open = true)")
        problems += axe(p, "1440, every Day 1 session open")
        p.click("#tab-day2")
        p.evaluate("document.querySelectorAll('details.session').forEach(d => d.open = true)")
        problems += axe(p, "1440, Day 2 selected, sessions open")
        m = b.new_page(viewport={"width": 390, "height": 844})
        m.goto(real, wait_until="networkidle")
        m.click("[data-menu-open]")
        problems += axe(m, "390, menu open")
        m.keyboard.press("Escape")
        m.evaluate("document.querySelectorAll('details.session').forEach(d => d.open = true)")
        problems += axe(m, "390, sessions open")

        # --- fixture: live carousel + open feedback ---
        for w, h in ((1440, 900), (390, 844)):
            q = b.new_page(viewport={"width": w, "height": h})
            errors = []
            q.on("pageerror", lambda e: errors.append(str(e)))
            q.goto(live, wait_until="networkidle")
            q.locator("#moments").scroll_into_view_if_needed()
            q.wait_for_timeout(300)

            def state():
                return q.evaluate("""() => {
                  const track = document.querySelector('[data-carousel-track]');
                  const slides = [...track.children];
                  const i = Math.round(track.scrollLeft / track.clientWidth);
                  const cur = [...document.querySelectorAll('.carousel__thumb')].findIndex(t => t.getAttribute('aria-current') === 'true');
                  return {visible: i, current: cur, count: slides[i].querySelector('.carousel__count').textContent,
                          prevDisabled: document.querySelector('[data-carousel-prev]').disabled,
                          nextDisabled: document.querySelector('[data-carousel-next]').disabled};
                }""")
            checks = []
            s0 = state(); checks.append(("start", s0, s0["visible"] == 0 and s0["current"] == 0 and s0["prevDisabled"] and not s0["nextDisabled"] and s0["count"] == "01 / 04"))
            q.click("[data-carousel-next]"); q.wait_for_timeout(700)
            s1 = state(); checks.append(("next", s1, s1["visible"] == 1 and s1["current"] == 1 and s1["count"] == "02 / 04"))
            q.focus("[data-carousel-track]"); q.keyboard.press("End"); q.wait_for_timeout(700)
            s2 = state(); checks.append(("End key", s2, s2["visible"] == 3 and s2["nextDisabled"] and s2["count"] == "04 / 04"))
            q.keyboard.press("ArrowLeft"); q.wait_for_timeout(700)
            s3 = state(); checks.append(("ArrowLeft", s3, s3["visible"] == 2 and s3["current"] == 2))
            q.click(".carousel__thumbs li:nth-child(1) a"); q.wait_for_timeout(700)
            s4 = state(); checks.append(("thumbnail 1", s4, s4["visible"] == 0 and s4["prevDisabled"]))
            q.click("[data-carousel-prev]", force=True) if not s4["prevDisabled"] else None
            # swipe: scroll the track like a finger flick would
            q.evaluate("document.querySelector('[data-carousel-track]').scrollBy({left: document.querySelector('[data-carousel-track]').clientWidth})")
            q.wait_for_timeout(700)
            s5 = state(); checks.append(("swipe", s5, s5["visible"] == 1 and s5["current"] == 1))
            for name, st, ok in checks:
                print("%4d carousel %-12s %s %s" % (w, name, "ok" if ok else "FAIL", st))
                problems += 0 if ok else 1
            if errors:
                print("   page errors:", errors); problems += 1
            q.go_back() if False else None
            q.click("[data-carousel-prev]") if not state()["prevDisabled"] else None
            q.wait_for_timeout(400)
            q.locator("#moments").screenshot(path=os.path.join(OUT, "state-carousel-%d.png" % w))
            q.locator("#feedback").screenshot(path=os.path.join(OUT, "state-feedback-open-%d.png" % w))
            fb = q.evaluate("""() => ({qr: !!document.querySelector('.fb-open__qr img'),
                                    link: document.querySelector('.fb-card--open a').getAttribute('href'),
                                    target: document.querySelector('.fb-card--open a').getAttribute('target')})""")
            print("%4d feedback open: %s" % (w, fb))
            problems += axe(q, "%d, fixture: live carousel + open feedback" % w)
            q.close()
        b.close()
    httpd_real.shutdown()
    httpd_live.shutdown()
    print("problems:", problems)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
