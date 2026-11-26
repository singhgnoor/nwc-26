#!/usr/bin/env python3
"""
Dev-only: build the logo files in static/img/logos/ from the official sources.

    pip install -r tools/requirements-dev.txt
    python tools/prepare_logos.py --emblem path/to/Emblem_of_India.svg --mmttp path/to/ugc_logo.png

Sources are listed in static/img/logos/SOURCES.md. Nothing here redraws or
recolours the Government of India emblem or the MMTTP logo:
  * emblem: the Wikimedia Commons SVG rendered, unaltered, to a transparent lossless WebP
    (the SVG is 437 KB, far too heavy for a 72 px slot);
  * MMTTP: the official PNG copied byte for byte;
  * IIT Ropar seal: imgaes/iitrpr-logo.svg is a 946x1039 PNG wrapped in SVG, so
    the colour seal is that PNG resized (WebP); the white line version for the indigo
    footer maps the artwork to white and its white paper to transparent
    (allowed for the institute's own seal).
"""
import argparse
import base64
import io
import os
import re
import shutil

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "static", "img", "logos")
SEAL_SVG = os.path.join(ROOT, "imgaes", "iitrpr-logo.svg")
HEIGHT = 288  # 4x the 72 px header slot


def seal_png():
    text = open(SEAL_SVG, encoding="utf-8").read()
    m = re.search(r'data:image/png;base64,([^"]+)"', text, re.S)
    raw = re.sub(r"&#\d+;|[^A-Za-z0-9+/=]", "", m.group(1))
    return Image.open(io.BytesIO(base64.b64decode(raw))).convert("RGBA")


def resize_h(im, h):
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


def white_version(im):
    """Dark/colour artwork -> white; white paper -> transparent (luminance to alpha)."""
    px = im.load()
    out = Image.new("RGBA", im.size, (255, 255, 255, 0))
    po = out.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
            alpha = int(round((1 - lum) * a))
            alpha = min(255, int(alpha * 1.35))  # keep thin strokes solid
            po[x, y] = (255, 255, 255, alpha)
    return out


def render_svg(svg_path, png_path, height):
    from playwright.sync_api import sync_playwright
    html = os.path.join(os.path.dirname(os.path.abspath(svg_path)), "_render.html")
    with open(html, "w", encoding="utf-8") as f:
        f.write('<!doctype html><body style="margin:0;background:transparent">'
                '<img id="i" src="%s" style="height:%dpx;display:block">' % (os.path.basename(svg_path), height))
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 2000, "height": height})
            page.goto("file:///" + html.replace("\\", "/"))
            page.wait_for_timeout(300)
            page.locator("#i").screenshot(path=png_path, omit_background=True)
            browser.close()
    finally:
        os.remove(html)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emblem", required=True, help="Emblem_of_India.svg from Wikimedia Commons")
    ap.add_argument("--mmttp", required=True, help="ugc_logo.png from mmc.ugc.ac.in")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    shutil.copyfile(args.mmttp, os.path.join(OUT, "mmttp.png"))

    tmp = os.path.join(OUT, "_emblem.png")
    render_svg(args.emblem, tmp, HEIGHT)
    # lossless WebP: pixel-identical to the rendering, the emblem stays unaltered
    Image.open(tmp).save(os.path.join(OUT, "emblem-of-india.webp"), "WEBP", lossless=True, method=6)
    os.remove(tmp)

    seal = seal_png()
    resize_h(seal, HEIGHT).save(os.path.join(OUT, "iit-ropar-seal.webp"), "WEBP", quality=90, method=6)
    resize_h(white_version(seal), HEIGHT).save(os.path.join(OUT, "iit-ropar-seal-white.webp"), "WEBP", quality=90, method=6)

    for name in sorted(os.listdir(OUT)):
        if name.endswith((".png", ".webp")):
            im = Image.open(os.path.join(OUT, name))
            print("%-28s %4dx%-4d %6d bytes" % (name, im.width, im.height, os.path.getsize(os.path.join(OUT, name))))


if __name__ == "__main__":
    main()
