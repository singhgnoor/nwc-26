#!/usr/bin/env python3
"""
Dev-only: face-centred square crops of the speaker photos, exported as WebP.

    pip install -r tools/requirements-dev.txt
    python tools/prepare_photos.py            # crops + tools/out/contact-sheet.png
    python tools/prepare_photos.py --write-content   # also set "photo" in content/content.en.json

Reads tools/photo_map.json (source file in imgaes/ -> speaker ID, optional manual
crop). The originals in imgaes/ are never modified. For each photo it:
  1. applies the EXIF orientation, converts to sRGB, drops all metadata;
  2. finds the face (OpenCV Haar cascade: detection only, no identification) and
     builds a square crop with the face centred, the eyes ~40 % from the top and
     the face ~42-50 % of the crop height, shifting (never padding) to stay
     inside the image; with no face it falls back to a square anchored 15 % from
     the top, and flags it for review;
  3. exports static/img/speakers/<id>-<size>.webp at 128, 208 and 352 px
     (WebP quality 82), never upscaling beyond the crop: a small source is
     exported at its real size instead, and flagged.
"""
import argparse
import io
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageCms, ImageDraw, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "imgaes")
OUT = os.path.join(ROOT, "static", "img", "speakers")
SHEET = os.path.join(ROOT, "tools", "out", "contact-sheet.png")
MAP = os.path.join(ROOT, "tools", "photo_map.json")
CONTENT = os.path.join(ROOT, "content", "content.en.json")
SIZES = (128, 208, 352)  # 64 px chips/avatars @2x, 104 px grid @2x, 176 px dignitary portrait @2x
KHADDAR = (246, 239, 226)
CASCADE = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))


def load(path):
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)
    icc = im.info.get("icc_profile")
    if icc:  # convert embedded colour profiles to sRGB
        try:
            src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            im = ImageCms.profileToProfile(im.convert("RGB") if im.mode not in ("RGB", "RGBA") else im,
                                           src, ImageCms.createProfile("sRGB"),
                                           outputMode="RGBA" if im.mode == "RGBA" else "RGB")
        except (OSError, ImageCms.PyCMSError):
            pass
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, KHADDAR + (255,))
        im = Image.alpha_composite(bg, im)
    return im.convert("RGB")


def faces(im):
    gray = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2GRAY)
    min_side = max(24, min(im.size) // 12)
    found = CASCADE.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=6, minSize=(min_side, min_side))
    return sorted([tuple(int(v) for v in f) for f in found], key=lambda f: -f[2] * f[3])


def clamp_box(cx, top_or_cy, size, W, H, from_center=False):
    size = int(min(size, W, H))
    left = cx - size / 2
    top = (top_or_cy - size / 2) if from_center else top_or_cy
    left = max(0, min(left, W - size))  # shift, never pad
    top = max(0, min(top, H - size))
    return int(round(left)), int(round(top)), size


def crop_box(im, entry):
    W, H = im.size
    if entry.get("crop"):
        c = entry["crop"]
        return clamp_box(c["cx"], c["cy"], c["size"], W, H, from_center=True) + ("manual crop",)
    found = faces(im)
    if not found:
        size = min(W, H)
        return clamp_box(W / 2, (H - size) * 0.15, size, W, H) + ("REVIEW: no face found",)
    x, y, w, h = found[0]  # the largest face; smaller boxes are background false positives
    size = h / 0.42        # Haar box spans brow to chin; the whole head is then ~50 % of the crop
    eyes_y = y + 0.38 * h
    left, top, size = clamp_box(x + w / 2, eyes_y - 0.40 * size, size, W, H)
    note = "%d faces, used the largest" % len(found) if len(found) > 1 else ""
    return left, top, size, note


def export(sid, square):
    os.makedirs(OUT, exist_ok=True)
    for name in os.listdir(OUT):
        if name.startswith(sid + "-") and name.endswith(".webp"):
            os.remove(os.path.join(OUT, name))
    written = []
    for target in SIZES:
        size = min(target, square.width)
        if written and size == written[-1]:
            break
        im = square.resize((size, size), Image.LANCZOS) if size != square.width else square
        path = os.path.join(OUT, "%s-%d.webp" % (sid, size))
        im.save(path, "WEBP", quality=82, method=6)  # no exif= / icc_profile=: metadata is not carried over
        written.append(size)
        if size < target:
            break
    return written


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-content", action="store_true")
    args = ap.parse_args()
    entries = json.load(open(MAP, encoding="utf-8"))["photos"]
    results = []
    for entry in entries:
        im = load(os.path.join(SRC, entry["file"]))
        left, top, size, note = crop_box(im, entry)
        square = im.crop((left, top, left + size, top + size))
        sizes = export(entry["id"], square)
        flag = note
        if sizes[-1] < SIZES[-1]:
            flag = (flag + "; " if flag else "") + "LOW-RES: largest export %d px" % sizes[-1]
        results.append((entry, square, sizes, flag))
        print("%-24s %-34s crop=(%d,%d,%d) sizes=%s %s" % (entry["id"], entry["file"], left, top, size, sizes, flag))

    # contact sheet: each crop at displayed sizes, circle and square, labelled
    os.makedirs(os.path.dirname(SHEET), exist_ok=True)
    try:
        font = ImageFont.truetype("arial.ttf", 13)
    except OSError:
        font = ImageFont.load_default()
    cw, ch, cols = 384, 236, 4
    rows = (len(results) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cw, rows * ch), KHADDAR)
    draw = ImageDraw.Draw(sheet)
    for i, (entry, square, sizes, flag) in enumerate(results):
        ox, oy = (i % cols) * cw, (i // cols) * ch
        x = ox + 8
        for disp in (176, 104, 64):
            tile = square.resize((disp, disp), Image.LANCZOS)
            mask = Image.new("L", (disp, disp), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, disp - 1, disp - 1), fill=255)
            circ = Image.new("RGB", (disp, disp), KHADDAR)
            circ.paste(tile, (0, 0), mask)
            sheet.paste(circ, (x, oy + 8))
            if disp == 64:
                sheet.paste(tile, (x, oy + 8 + 72))
            x += disp + 8
        draw.text((ox + 8, oy + 192), entry["id"], fill=(30, 42, 68), font=font)
        draw.text((ox + 8, oy + 209), flag or "ok", fill=(178, 58, 43) if flag else (31, 107, 102), font=font)
    sheet.save(SHEET)
    print("contact sheet:", os.path.relpath(SHEET, ROOT))

    if args.write_content:
        with open(CONTENT, encoding="utf-8") as f:
            content = json.load(f)
        for entry, _, sizes, _ in results:
            content["speakers"][entry["id"]]["photo"] = "img/speakers/%s-%d.webp" % (entry["id"], sizes[-1])
        with open(CONTENT, "w", encoding="utf-8", newline="\n") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("updated content/content.en.json")


if __name__ == "__main__":
    sys.exit(main())
