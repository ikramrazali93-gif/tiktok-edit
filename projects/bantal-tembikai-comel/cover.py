#!/usr/bin/env python3
"""TikTok cover (1080x1536) for the round watermelon plush pillow (bantal tembikai comel) video.

Usage: python3 cover.py <frame.png> <out.png>
Canvas is 1080x1536 (20% shorter than 1920); key text stays inside a 3:4 crop (y 48-1488).
Refresh: cream background with a seed-dot pattern and a wavy rind band, the photo cut into a big CIRCLE framed by
watermelon rings (flesh pink -> white -> rind green), chunky 3D 'jelly' title (as in the video), music notes,
a sunshine size pill and a pink "GEBU!" burst.
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

RIND = (28, 94, 52)
GREEN = (63, 163, 77)
LIME = (166, 222, 126)
PINK = (255, 92, 138)
FLESH = (242, 85, 122)
BLUSH = (255, 194, 211)
CREAM = (255, 246, 229)
SUN = (255, 213, 74)
SEED = (43, 43, 43)
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



def chunky(text, size, face, rot=0, depth=12):
    """Chunky 3D 'jelly' lettering: rind-green extrusion stacked down-right under a face with a thick rind rim."""
    f = font(size)
    sw = max(6, size // 9)
    l, t, r, b = f.getbbox(text, stroke_width=sw)
    im = Image.new("RGBA", (r - l + 40 + depth, b - t + 40 + int(depth * 1.3)))
    d = ImageDraw.Draw(im)
    for k in range(depth, 0, -1):
        d.text((20 - l + k, 20 - t + int(k * 1.3)), text, font=f, fill=RIND, stroke_width=sw, stroke_fill=RIND)
    d.text((20 - l, 20 - t), text, font=f, fill=face, stroke_width=sw, stroke_fill=RIND)
    return im.rotate(rot, resample=Image.BICUBIC, expand=True)


def note_poly(d, x, y, s, col):
    d.ellipse((x - 11 * s, y - 8 * s, x + 11 * s, y + 8 * s), fill=col)
    d.rectangle((x + 7 * s, y - 46 * s, x + 12 * s, y), fill=col)
    d.polygon([(x + 12 * s, y - 46 * s), (x + 30 * s, y - 34 * s), (x + 26 * s, y - 20 * s), (x + 12 * s, y - 30 * s)],
              fill=col)


def melon_bg():
    """Cream with a soft seed-dot pattern and a wavy rind-green band along the bottom."""
    bg = Image.new("RGBA", (W, H), (*CREAM, 255))
    d = ImageDraw.Draw(bg)
    for row, y in enumerate(range(40, H, 90)):
        for x in range(40 + (45 if row % 2 else 0), W, 90):
            d.ellipse((x - 5, y - 8, x + 5, y + 8), fill=(*BLUSH, 255))
    for col, (y0, amp) in ((LIME, (1360, 26)), (GREEN, (1395, 22)), (RIND, (1440, 18))):
        pts = [(0, H)] + [(x, y0 + amp * math.sin(x / 70)) for x in range(0, W + 10, 10)] + [(W, H)]
        d.polygon(pts, fill=(*col, 255))
    return bg


def melon_circle(img, cx, cy, r, diam):
    """Circular crop of the photo (centre cx,cy radius r in source px) framed by watermelon rings."""
    crop = img.crop((cx - r, cy - r, cx + r, cy + r)).resize((diam, diam), Image.LANCZOS).convert("RGBA")
    rings = [(RIND, 10), (GREEN, 26), (LIME, 10), (WHITE, 14), (FLESH, 16), (WHITE, 10)]
    total = sum(w for _, w in rings)
    size = diam + 2 * total
    out = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(out)
    off = 0
    for col, w in rings:
        d.ellipse((off, off, size - off - 1, size - off - 1), fill=(*col, 255))
        off += w
    mask = Image.new("L", (diam, diam))
    ImageDraw.Draw(mask).ellipse((0, 0, diam - 1, diam - 1), fill=255)
    out.paste(crop, (total, total), mask)
    return shadow(out, offset=(0, 18), blur=22, alpha=120)


def main():
    img = Image.open(SRC).convert("RGB").resize((W, SRC_H), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(1.12)
    img = ImageEnhance.Contrast(img).enhance(1.05)
    base = melon_bg()

    paste_center(base, melon_circle(img, 540, 940, 540, 820), W / 2, 830)

    notes = Image.new("RGBA", (W, H))
    dn = ImageDraw.Draw(notes)
    for x, y, s, c in ((110, 520, 1.6, PINK), (960, 470, 1.3, GREEN), (70, 1250, 1.2, GREEN), (1000, 1240, 1.3, PINK),
                       (170, 330, 1.0, SUN), (900, 330, 1.0, PINK)):
        note_poly(dn, x, y, s, (*c, 255))
    base.alpha_composite(notes)

    paste_center(base, shadow(chunky("TEMBIKAI", 120, PINK, rot=-3), offset=(0, 8), blur=10, alpha=90), W / 2, 125)
    paste_center(base, shadow(chunky("ADA KAKI!", 104, SUN, rot=2), offset=(0, 8), blur=10, alpha=90), W / 2 + 10, 265)

    paste_center(base, shadow(pill("3 SIZE: 35 • 45 • 55CM", 50, (*SUN, 255), RIND, icon="🍉")), W / 2, 1300)
    paste_center(base, burst([("GEBU!", 76)], (*PINK, 255), WHITE, -10, 250), 905, 1100)
    paste_center(base, shadow(emoji("🥰", 120), offset=(0, 6), blur=8, alpha=90), 165, 1150)
    base.convert("RGB").save(OUT, quality=95)


if __name__ == "__main__":
    main()
