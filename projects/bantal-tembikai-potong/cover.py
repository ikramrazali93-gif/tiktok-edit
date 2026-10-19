#!/usr/bin/env python3
"""TikTok cover (1080x1536) for the watermelon-slice plush pillow (bantal tembikai) video.

Refresh: a watermelon-rind photo frame (green / cream / pink bands) with seeds, sticker-style title.

Usage: python3 cover.py <frame.png> <out.png>
Canvas is 1080x1536 (20% shorter than 1920); key text stays inside a 3:4 crop (y 48-1488).
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

SRC, OUT = sys.argv[1:3]
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "fonts", "Fredoka-Bold.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
W, H = 1080, 1536          # 20% shorter than 9:16 (1920), per request
SRC_H, CROP_TOP = 1920, 150   # crop window taken from the 1080x1920 frame (both pillow faces in view)

PINK = (255, 111, 145)      # watermelon flesh
DPINK = (232, 63, 111)
GREEN = (60, 194, 74)       # rind
DGREEN = (19, 111, 46)
CREAM = (255, 247, 238)
SEED = (42, 26, 31)
YELLOW = (255, 210, 63)
WHITE = (255, 255, 255)

def font(size):
    return ImageFont.truetype(FONT, size)


def emoji(ch, size):
    f = ImageFont.truetype(EMOJI, 109)
    im = Image.new("RGBA", (160, 160))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)


def shadow(layer, offset=(0, 10), blur=14, alpha=110):
    p = blur * 2 + max(offset)          # pad so the soft shadow isn't clipped into a box
    big = Image.new("RGBA", (layer.width + 2 * p, layer.height + 2 * p))
    big.alpha_composite(layer, (p, p))
    layer = big
    a = layer.split()[-1].filter(ImageFilter.GaussianBlur(blur))
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sh.putalpha(a.point(lambda v: v * alpha // 255))
    out = Image.new("RGBA", layer.size)
    out.alpha_composite(sh, offset)
    out.alpha_composite(layer)
    return out


def outlined_text(text, size, fill, stroke, stroke_w, rot=0):
    f = font(size)
    l, t, r, b = f.getbbox(text, stroke_width=stroke_w)
    im = Image.new("RGBA", (r - l + 40, b - t + 40))
    ImageDraw.Draw(im).text((20 - l, 20 - t), text, font=f, fill=fill, stroke_width=stroke_w, stroke_fill=stroke)
    return im.rotate(rot, resample=Image.BICUBIC, expand=True)


def pill(text, size, bg, fg, icon=None, rot=0, pad=(38, 18)):
    f = font(size)
    l, t, r, b = f.getbbox(text)
    tw, th = r - l, b - t
    ic = emoji(icon, int(size * 1.05)) if icon else None
    iw = ic.width + 16 if ic else 0
    w, h = tw + iw + pad[0] * 2, th + pad[1] * 2
    im = Image.new("RGBA", (w + 12, h + 12))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, w + 6, h + 6), radius=h // 2, fill=bg, outline=WHITE, width=6)
    d.text((6 + pad[0] - l, 6 + pad[1] - t), text, font=f, fill=fg)
    if ic:
        im.alpha_composite(ic, (6 + pad[0] + tw + 16, 6 + (h - ic.height) // 2))
    return im.rotate(rot, resample=Image.BICUBIC, expand=True)


def paste_center(base, layer, cx, cy):
    base.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))

def burst(text_lines, fill, fg, rot, size):
    im = Image.new("RGBA", (360, 360))
    d = ImageDraw.Draw(im)
    pts = []
    for i in range(28):
        ang = i * math.pi / 14
        r = 170 if i % 2 == 0 else 140
        pts.append((180 + r * math.cos(ang), 180 + r * math.sin(ang)))
    d.polygon(pts, fill=fill)
    d.line(pts + [pts[0]], fill=WHITE, width=6)
    n = len(text_lines)
    for k, (txt, fs) in enumerate(text_lines):
        f = font(fs)
        l, t, r, b = f.getbbox(txt)
        y = 180 + (k - (n - 1) / 2) * fs * 0.95
        d.text((180 - (r - l) / 2 - l, y - (b - t) / 2 - t), txt, font=f, fill=fg)
    return shadow(im.rotate(rot, resample=Image.BICUBIC, expand=True).resize((size, size), Image.LANCZOS))


def main():
    img = Image.open(SRC).convert("RGB").resize((W, SRC_H), Image.LANCZOS)
    img = img.crop((0, CROP_TOP, W, CROP_TOP + H))
    img = ImageEnhance.Color(img).enhance(1.18)
    img = ImageEnhance.Contrast(img).enhance(1.06)
    img = ImageEnhance.Brightness(img).enhance(1.04)
    base = img.convert("RGBA")

    grad = Image.new("RGBA", (W, H))
    gd = ImageDraw.Draw(grad)
    for y in range(0, 460):
        a = int(170 * (1 - y / 460) ** 1.4)
        gd.line([(0, y), (W, y)], fill=(*DGREEN, a))
    base.alpha_composite(grad)

    # watermelon-rind photo frame: dark green, light green, cream, then a thin pink edge
    fr = Image.new("RGBA", (W, H))
    fd = ImageDraw.Draw(fr)
    for inset, col, wdt in [(0, DGREEN, 16), (16, GREEN, 18), (34, CREAM, 14), (48, PINK, 7)]:
        fd.rounded_rectangle((inset, inset, W - 1 - inset, H - 1 - inset), radius=46 - inset // 2, outline=col, width=wdt)
    seed = Image.new("RGBA", (40, 56))
    ImageDraw.Draw(seed).ellipse((6, 4, 34, 52), fill=SEED)
    ImageDraw.Draw(seed).ellipse((12, 12, 20, 26), fill=(110, 90, 96))
    for (sx, sy, r) in [(110, 400, 20), (70, 620, -15), (980, 640, 30), (1010, 860, -25), (90, 1120, 10),
                        (960, 1120, -10), (300, 1460, 70), (780, 1470, -60)]:
        sd = seed.rotate(r, resample=Image.BICUBIC, expand=True)
        fr.alpha_composite(sd, (sx - sd.width // 2, sy - sd.height // 2))
    base.alpha_composite(fr)

    t1 = shadow(outlined_text("BANTAL TEMBIKAI", 104, WHITE, DGREEN, 12, rot=2))
    t2 = shadow(outlined_text("ADA 3 SIZE!", 124, DPINK, WHITE, 14, rot=-3))
    paste_center(base, t1, W / 2, 140)
    paste_center(base, t2, W / 2 + 10, 285)
    paste_center(base, shadow(emoji("🍉", 92)), 140, 285)
    paste_center(base, shadow(emoji("✨", 70)), 950, 270)
    paste_center(base, shadow(pill("45 • 60 • 90 CM", 52, GREEN, WHITE, "📏", rot=-2)), W / 2, 1395)
    paste_center(base, burst([("SANGAT", 46), ("GEBU!", 64)], DPINK, WHITE, -8, 195), 960, 1325)
    base.convert("RGB").save(OUT, quality=95)


if __name__ == "__main__":
    main()
