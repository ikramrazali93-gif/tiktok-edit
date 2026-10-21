#!/usr/bin/env python3
"""Check sheet: frames of the rendered video with the TikTok UI zones (red) and the marked subject (her head =
cyan box, pillow smileys = orange dots) drawn on top, so overlaps between graphics and subject are easy to spot.

Usage: python3 check.py <out_dir> <sheet.jpg> [--final]
Reads <out_dir>/edl.json (blocks + SUBJECT boxes from edit.py) and <out_dir>/preview.mp4 (or final.mp4).
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw

out, sheet = sys.argv[1], sys.argv[2]
final = "--final" in sys.argv
video = os.path.join(out, "final.mp4" if final else "preview.mp4")
edl = json.load(open(os.path.join(out, "edl.json")))
TW, TH = 216, 384                                   # thumb size (1080x1920 / 5)
SAFE = edl["safe"]                                  # in 1080x1920 px
k = TW / 1080

times = []
for b in edl["blocks"]:
    for f in (0.3, 0.7):
        times.append((b["t0"] + b["dur"] * f, b["name"]))
for lab in edl["labels"]:
    times.append(((lab["t0"] + lab["t1"]) / 2, None))
times = sorted({round(t, 2): n for t, n in times}.items())


def block_of(t):
    for b in edl["blocks"]:
        if b["t0"] <= t < b["t0"] + b["dur"]:
            return b["name"]
    return edl["blocks"][-1]["name"]


thumbs = []
for t, _ in times:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1",
                          "-vf", f"scale={TW}:{TH}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    im = Image.frombytes("RGB", (TW, TH), raw).convert("RGBA")
    ov = Image.new("RGBA", im.size)
    d = ImageDraw.Draw(ov)
    red = (255, 0, 0, 90)
    d.rectangle([SAFE["r"] * k, 0, TW, TH], fill=red)                     # right column
    d.rectangle([0, SAFE["b"] * k, TW, TH], fill=red)                     # bottom caption area
    d.rectangle([0, 0, TW, SAFE["t"] * k], fill=red)                      # top tabs
    sub = edl["subject"].get(block_of(t))
    if sub:
        x0, y0, x1, y1 = sub["head"]
        d.rectangle([x0 * TW, y0 * TH, x1 * TW, y1 * TH], outline=(0, 230, 255, 255), width=2)
        for fx, fy in sub["faces"]:
            d.ellipse([fx * TW - 6, fy * TH - 6, fx * TW + 6, fy * TH + 6], outline=(255, 150, 0, 255), width=2)
    im = Image.alpha_composite(im, ov)
    ImageDraw.Draw(im).text((4, 4), f"{t:.1f}", fill=(255, 255, 0, 255))
    thumbs.append(im.convert("RGB"))

cols = 10
rows = (len(thumbs) + cols - 1) // cols
grid = Image.new("RGB", (cols * TW, rows * TH))
for i, im in enumerate(thumbs):
    grid.paste(im, ((i % cols) * TW, (i // cols) * TH))
grid.save(sheet, quality=85)
print(f"{len(thumbs)} frames -> {sheet}")
