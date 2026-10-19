#!/usr/bin/env python3
"""TikTok cover (1080x1536) for the sleeping calico cat pillow (bantal kucing) video.

Refresh v4: dotted pastel backdrop with the cat in a tilted polaroid (instead of a full-bleed frame).

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
SRC_H, CROP_TOP = 1920, 300 # crop window taken from the 1080x1920 frame

COCOA = (74, 44, 32)
CARAMEL = (233, 154, 78)
CREAM = (255, 245, 230)
BLUSH = (242, 102, 139)
LILAC = (183, 156, 242)
SAGE = (156, 207, 177)
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


def paw(size, col):
    im = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(im)
    u = size / 50
    d.ellipse((8 * u, 22 * u, 42 * u, 48 * u), fill=col)
    for cx, cy in [(6, 16), (17, 5), (33, 5), (44, 16)]:
        d.ellipse(((cx - 6) * u, (cy - 7) * u, (cx + 6) * u, (cy + 7) * u), fill=col)
    return im


def polaroid(photo, caption):
    bw, top, bot = 30, 30, 140
    pw, ph = photo.width + 2 * bw, photo.height + top + bot
    im = Image.new("RGBA", (pw, ph))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, pw - 1, ph - 1), radius=14, fill=WHITE)
    im.paste(photo, (bw, top))
    f = font(64)
    parts = [(caption[0], COCOA), (caption[1], BLUSH)]
    tw = sum(f.getlength(t) for t, _ in parts)
    x = (pw - tw) / 2
    for t, c in parts:
        l, tt, r, b = f.getbbox(t)
        d.text((x, top + photo.height + (bot - (b - tt)) / 2 - tt), t, font=f, fill=c)
        x += f.getlength(t)
    return im


def main():
    img = Image.open(SRC).convert("RGB").resize((W, SRC_H), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(1.12)
    img = ImageEnhance.Contrast(img).enhance(1.05)
    img = ImageEnhance.Brightness(img).enhance(1.05)

    # cream backdrop with blush polka dots and a few paw prints
    base = Image.new("RGBA", (W, H), (*CREAM, 255))
    d = ImageDraw.Draw(base)
    for j, y in enumerate(range(30, H, 78)):
        for x in range(30 + (39 if j % 2 else 0), W, 78):
            d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(*BLUSH, 70))
    for (x, y, sz, rot, col) in [(90, 420, 70, 20, CARAMEL), (150, 560, 60, 35, CARAMEL), (980, 640, 66, -25, LILAC),
                                 (930, 790, 58, -10, LILAC), (70, 1320, 64, 15, SAGE)]:
        paste_center(base, paw(sz, (*col, 200)).rotate(rot, resample=Image.BICUBIC, expand=True), x, y)

    # the cat in a tilted polaroid, washi tape on top
    photo = img.crop((60, 170, 1020, 1313)).resize((700, 834), Image.LANCZOS)
    pol = polaroid(photo, ("BANTAL ", "KUCING"))
    pol = shadow(pol.rotate(-3, resample=Image.BICUBIC, expand=True), offset=(0, 14), blur=18, alpha=120)
    paste_center(base, pol, W / 2, 815)
    tape = Image.new("RGBA", (230, 58), (*LILAC, 190))
    paste_center(base, tape.rotate(5, resample=Image.BICUBIC, expand=True), W / 2 + 10, 330)

    # title
    t1 = shadow(outlined_text("PEMINAT", 108, COCOA, WHITE, 10, rot=2))
    t2 = shadow(outlined_text("KUCING?", 138, BLUSH, WHITE, 13, rot=-3))
    paste_center(base, t1, W / 2 - 40, 105)
    paste_center(base, t2, W / 2 + 10, 225)
    paste_center(base, shadow(emoji("🐱", 96)), 905, 95)
    paste_center(base, shadow(emoji("🐾", 80)), 150, 235)

    paste_center(base, burst([("COMEL!", 70)], BLUSH, WHITE, -8, 240), 900, 1185)
    paste_center(base, shadow(pill("LEMBUT & GEBU", 46, CARAMEL, COCOA, "☁️", rot=-3)), 300, 1410)
    paste_center(base, shadow(pill("BANTAL PELUK", 46, LILAC, COCOA, "🤗", rot=2)), 775, 1415)
    base.convert("RGB").save(OUT, quality=95)


if __name__ == "__main__":
    main()
