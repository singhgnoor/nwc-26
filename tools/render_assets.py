#!/usr/bin/env python3
"""
Dev-only: render raster assets with a headless browser so Devanagari shapes correctly.

    pip install -r tools/requirements-dev.txt && python -m playwright install chromium
    python tools/render_assets.py            # favicon PNGs + Open Graph image

Outputs (committed): static/img/favicon-32.png, static/img/apple-touch-icon.png,
static/img/og-image.png (1200 x 630). The OG card is drawn from tools/og-card.html,
which uses the site's own fonts, landscape and pillars, so it matches the hero.
"""
import os
import pathlib

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"


def render_favicons(page):
    svg = (STATIC / "img" / "favicon.svg").read_text(encoding="utf-8")
    for size, name in ((32, "favicon-32.png"), (180, "apple-touch-icon.png")):
        page.set_viewport_size({"width": size, "height": size})
        page.set_content('<html><body style="margin:0">%s</body></html>'
                         % svg.replace("<svg ", '<svg width="%d" height="%d" ' % (size, size), 1))
        page.screenshot(path=str(STATIC / "img" / name), omit_background=False)
        print("wrote static/img/%s" % name)


def render_og(page):
    card = ROOT / "tools" / "og-card.html"
    page.set_viewport_size({"width": 1200, "height": 630})
    page.goto(card.as_uri())
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(400)
    page.screenshot(path=str(STATIC / "img" / "og-image.png"))
    print("wrote static/img/og-image.png")


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        render_favicons(page)
        render_og(page)
        browser.close()


if __name__ == "__main__":
    main()
