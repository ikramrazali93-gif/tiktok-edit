#!/usr/bin/env python3
"""TikTok cover (1080x1536) for the round avocado plush (bantal avocado, bulat montel) video.

Usage: python3 cover.py <frame.png> <out.png>
Canvas is 1080x1536 (20% shorter than 1920); key text stays inside a 3:4 crop (y 48-1488).
Refresh: green gingham picnic-cloth background, the photo as a die-cut sticker, half-avocado badges.
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
SRC_H = 1920

DEEP = (47, 74, 30)
SKIN = (92, 138, 46)
FLESH = (197, 226, 92)
PALE = (238, 246, 200)
SEED = (123, 74, 44)
CHEEK = (244, 143, 160)
CREAM = (255, 248, 230)
BUTTER = (255, 213, 79)
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


def gingham():
    """Picnic-cloth gingham in soft avocado greens."""
    bg = Image.new("RGBA", (W, H), (*CREAM, 255))
    band = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(band)
    s = 90
    for x in range(0, W, 2 * s):
        d.rectangle((x, 0, x + s - 1, H), fill=(*FLESH, 140))
    for y in range(0, H, 2 * s):
        d.rectangle((0, y, W, y + s - 1), fill=(*FLESH, 140))
    bg.alpha_composite(band)
    return bg


def sticker_photo(img, w, rot):
    """The photo as a die-cut sticker: rounded, thick white border, soft shadow."""
    img = img.resize((w, int(w * img.height / img.width)), Image.LANCZOS).convert("RGBA")
    rim, rad = 22, 70
    out = Image.new("RGBA", (img.width + 2 * rim, img.height + 2 * rim))
    ImageDraw.Draw(out).rounded_rectangle((0, 0, out.width - 1, out.height - 1), radius=rad + rim, fill=WHITE)
    mask = Image.new("L", img.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img.width - 1, img.height - 1), radius=rad, fill=255)
    out.paste(img, (rim, rim), mask)
    return shadow(out.rotate(rot, resample=Image.BICUBIC, expand=True), offset=(0, 18), blur=20, alpha=120)


def seed_label(text, size, bg, fg, icon, hi=None):
    """Half-avocado label (matches the video): pill + brown seed badge holding an emoji."""
    f = font(size)
    l, t, r, b = f.getbbox(text)
    tw, th = r - l, b - t
    h = th + 44
    D = h + 18
    w = D + 18 + tw + 48
    im = Image.new("RGBA", (w + 16, D + 16))
    d = ImageDraw.Draw(im)
    py = 8 + (D - h) // 2
    d.rounded_rectangle((8 + D * 0.45, py, 8 + w, py + h), radius=h // 2, fill=bg, outline=WHITE, width=6)
    d.ellipse((8, 8, 8 + D, 8 + D), fill=SEED, outline=CREAM, width=7)
    d.text((8 + D + 18 - l, py + 22 - t), text, font=f, fill=fg)
    ic = emoji(icon, int(D * 0.6))
    im.alpha_composite(ic, (int(8 + D / 2 - ic.width / 2), int(8 + D / 2 - ic.height / 2)))
    return shadow(im)


def leaf(size, rot, col):
    im = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(im)
    d.ellipse((size * 0.3, 2, size * 0.7, size - 2), fill=col, outline=DEEP, width=4)
    d.line((size / 2, 10, size / 2, size - 10), fill=DEEP, width=4)
    return im.rotate(rot, resample=Image.BICUBIC, expand=True)


def main():
    img = Image.open(SRC).convert("RGB").resize((W, SRC_H), Image.LANCZOS)
    img = img.crop((40, 230, 1040, 1530))
    img = ImageEnhance.Color(img).enhance(1.12)
    img = ImageEnhance.Contrast(img).enhance(1.05)
    base = gingham()

    paste_center(base, sticker_photo(img, 760, -2), W / 2, 830)
    for (x, y, rot, col) in ((120, 400, 30, SKIN), (965, 470, -40, FLESH), (110, 1240, -20, FLESH), (975, 1180, 25, SKIN)):
        paste_center(base, shadow(leaf(120, rot, col)), x, y)

    t1 = shadow(outlined_text("PEMINAT AVOCADO?", 92, WHITE, DEEP, 12))
    t2 = shadow(outlined_text("BULAT MONTEL!", 112, FLESH, DEEP, 14, rot=-2))
    paste_center(base, t1, W / 2, 125)
    paste_center(base, t2, W / 2, 255)

    paste_center(base, seed_label("GEBU & TEBAL", 44, PALE, DEEP, "☁️"), 320, 1345)
    paste_center(base, seed_label("ADA ZIP", 44, FLESH, DEEP, "🤐"), 300, 1435)
    paste_center(base, burst([("SIZE", 46), ("30CM!", 56)], SEED, WHITE, 8, 250), 870, 1360)
    base.convert("RGB").save(OUT, quality=95)


if __name__ == "__main__":
    main()
