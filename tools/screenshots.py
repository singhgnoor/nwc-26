#!/usr/bin/env python3
"""
Dev-only: screenshot the built site at every breakpoint, plus interaction states.

    python build_site.py && python tools/screenshots.py [--only 1440,390] [--states] [--axe]

Starts server.py's handler on a free port (serving site/ under the real URL
prefix), then writes PNGs to tools/out/ (gitignored). With --axe it also runs
axe-core (axe-playwright-python) and prints serious/critical violations.
Checks horizontal overflow at each width and reports it.
"""
import argparse
import os
import sys
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import server  # noqa: E402
server.log = lambda message: None  # keep the screenshot run quiet

from playwright.sync_api import sync_playwright  # noqa: E402

OUT = os.path.join(ROOT, "tools", "out")
PREFIX = "/national-wellbeing-conclave-2026"
WIDTHS = [(360, 780), (390, 844), (414, 896), (768, 1024), (1024, 768), (1280, 800), (1440, 900), (1920, 1080),
          (844, 390), (896, 414)]

OVERFLOW_JS = """() => {
  const w = document.documentElement.clientWidth, bad = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    if (el.closest('.nearby__list, .carousel__track, .carousel__thumbs, .nav__list, .sprite, .visually-hidden')) continue;
    if (r.right > w + 1 || r.left < -1) bad.push((el.className && el.className.baseVal === undefined ? el.className : el.tagName) + ' ' + Math.round(r.left) + '..' + Math.round(r.right));
  }
  return {scroll: document.documentElement.scrollWidth, width: w, bad: bad.slice(0, 12)};
}"""


def serve(site_dir):
    httpd = server.Server(("127.0.0.1", 0), site_dir, [PREFIX])
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, "http://127.0.0.1:%d%s/" % (httpd.server_address[1], PREFIX)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default=os.path.join(ROOT, "site"))
    ap.add_argument("--only", default="")
    ap.add_argument("--states", action="store_true")
    ap.add_argument("--axe", action="store_true")
    ap.add_argument("--nojs", action="store_true")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    httpd, url = serve(args.site)
    only = {int(x) for x in args.only.split(",") if x}
    problems = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for w, h in WIDTHS:
            if only and w not in only:
                continue
            ctx = browser.new_context(viewport={"width": w, "height": h}, java_script_enabled=not args.nojs,
                                      timezone_id="Asia/Kolkata")
            page = ctx.new_page()
            errors = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(url, wait_until="load")
            name = "%s%dx%d%s" % (args.tag, w, h, "-nojs" if args.nojs else "")
            if args.nojs:  # page scripts are off, so Playwright cannot evaluate; scroll with the wheel instead
                for _ in range(60):
                    page.mouse.wheel(0, 900)
                    page.wait_for_timeout(30)
                page.wait_for_timeout(500)
                page.screenshot(path=os.path.join(OUT, name + ".png"), full_page=True)
                print("%-12s screenshot written (no overflow check without JS)" % name)
                ctx.close()
                continue
            page.evaluate("document.fonts.ready")
            # scroll through the page so lazy-loaded photos load, then back to the top
            page.evaluate("""async () => {
              for (let y = 0; y < document.body.scrollHeight; y += 600) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 40)); }
              window.scrollTo(0, 0);
            }""")
            page.wait_for_timeout(500)
            page.screenshot(path=os.path.join(OUT, name + ".png"), full_page=True)
            ov = page.evaluate(OVERFLOW_JS)
            status = "ok" if ov["scroll"] <= ov["width"] and not ov["bad"] else "OVERFLOW"
            if status != "ok":
                problems += 1
            print("%-12s %s scrollWidth=%s width=%s %s" % (name, status, ov["scroll"], ov["width"], "; ".join(ov["bad"])))
            if errors:
                problems += 1
                print("   console errors:", errors)
            if w == 1440 and not args.nojs:
                page.click("#tab-day2")
                page.wait_for_timeout(200)
                page.screenshot(path=os.path.join(OUT, name + "-day2.png"), full_page=True)
            if args.states and not args.nojs:
                if w >= 1024:
                    page.click("#tab-day1")
                    card = page.locator("#details-s5 summary")
                    card.scroll_into_view_if_needed()
                    card.hover()
                    page.wait_for_timeout(250)
                    page.locator("#session-s5").screenshot(path=os.path.join(OUT, name + "-hover.png"))
                    card.click()
                    page.mouse.move(5, 5)
                    page.wait_for_timeout(250)
                    page.locator("#session-s5").screenshot(path=os.path.join(OUT, name + "-expanded.png"))
                else:
                    page.evaluate("window.scrollTo(0, 0)")
                    page.click("[data-menu-open]")
                    page.wait_for_timeout(250)
                    page.screenshot(path=os.path.join(OUT, name + "-menu.png"))
                    page.keyboard.press("Escape")
            if args.axe and not args.nojs:
                from axe_playwright_python.sync_playwright import Axe
                results = Axe().run(page)
                bad = [v for v in results.response["violations"] if v["impact"] in ("serious", "critical")]
                print("   axe: %d violations (%d serious/critical)" % (len(results.response["violations"]), len(bad)))
                for v in results.response["violations"]:
                    print("     - [%s] %s: %s (%d nodes) e.g. %s" % (v["impact"], v["id"], v["help"], len(v["nodes"]),
                                                               v["nodes"][0]["target"] if v["nodes"] else ""))
                problems += len(bad)
            ctx.close()
        browser.close()
    httpd.shutdown()
    print("problems:", problems)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
