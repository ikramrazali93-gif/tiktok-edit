#!/usr/bin/env python3
"""TikTok cover (1080x1536) for the carrot plush pillow (bantal carrot) video.

Seed-packet look (garden theme, same family as the video's hang tags): kraft-paper packet with a
crimped top edge, a deep-green title band, the photo in a rounded window, a hang-tag tagline,
a round "stamp" and a soil-brown info strip with the sizes.

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
SRC_H, CROP_TOP = 1920, 170 # crop window taken from the 1080x1920 frame

KRAFT = (243, 227, 195)
KRAFT_D = (214, 186, 140)
DEEP = (31, 107, 58)
LEAF = (124, 227, 139)
CARROT = (255, 110, 47)
SOIL = (91, 58, 41)
SUN = (255, 209, 102)
CREAM = (255, 246, 229)
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


def paste_center(base, layer, cx, cy):
    base.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


def rich(d, x, y, text, f, fg, hi):
    """Draw *word* parts in the highlight colour."""
    for i, part in enumerate(text.split("*")):
        d.text((x, y), part, font=f, fill=(hi if i % 2 else fg))
        x += f.getlength(part)


def hang_tag(text, size, fill, fg, hi, rot=0):
    """Hang tag with a pointed left end, punch hole and a short string, like the video labels."""
    f = font(size)
    plain = text.replace("*", "")
    l, t, r, b = f.getbbox(plain)
    tw, th = r - l, b - t
    h = int(th + size * 0.8)
    tip = int(h * 0.42)
    w = tw + int(size * 1.0)
    pad = 24
    im = Image.new("RGBA", (w + tip + 2 * pad, h + 2 * pad + 70))
    d = ImageDraw.Draw(im)
    x0, y0 = pad + tip, pad + 70
    rr = int(h * 0.22)
    body = [(x0 - tip, y0 + h / 2), (x0, y0), (x0 + w - rr, y0), (x0 + w, y0 + rr), (x0 + w, y0 + h - rr),
            (x0 + w - rr, y0 + h), (x0, y0 + h)]
    d.polygon(body, fill=fill, outline=SOIL, width=6)
    hx, hy = x0 + int(h * 0.05), y0 + h / 2
    hr = size * 0.13
    d.line([(hx - 30, pad), (hx - 10, pad + 40), (hx, hy)], fill=SOIL, width=5)
    d.ellipse((hx - hr, hy - hr, hx + hr, hy + hr), fill=SOIL, outline=CREAM, width=3)
    rich(d, x0 + int(size * 0.5) - l, y0 + (h - th) / 2 - t, text, f, fg, hi)
    return im.rotate(rot, resample=Image.BICUBIC, expand=True)


def stamp(lines, r, fill, fg, rot=0):
    """Round seed-packet 'stamp' with a dashed inner ring."""
    s = 2 * r + 20
    im = Image.new("RGBA", (s, s))
    d = ImageDraw.Draw(im)
    c = s / 2
    d.ellipse((10, 10, s - 10, s - 10), fill=fill, outline=WHITE, width=7)
    ri = r - 20
    for k in range(36):
        a0 = k * 10
        d.arc((c - ri, c - ri, c + ri, c + ri), a0, a0 + 5, fill=CREAM, width=4)
    n = len(lines)
    for k, (txt, fs) in enumerate(lines):
        f = font(fs)
        l, t, rr, b = f.getbbox(txt)
        y = c + (k - (n - 1) / 2) * fs * 1.0
        d.text((c - (rr - l) / 2 - l, y - (b - t) / 2 - t), txt, font=f, fill=fg)
    return shadow(im.rotate(rot, resample=Image.BICUBIC, expand=True))


def kraft(w, h):
    im = Image.new("RGBA", (w, h), (*KRAFT, 255))
    d = ImageDraw.Draw(im)
    # faint paper fibres + seed dots
    import random
    rnd = random.Random(4)
    for _ in range(900):
        x, y = rnd.randrange(w), rnd.randrange(h)
        d.line((x, y, x + rnd.randint(4, 14), y + rnd.randint(-2, 2)), fill=(*KRAFT_D, 90), width=1)
    for _ in range(70):
        x, y = rnd.randrange(w), rnd.randrange(h)
        d.ellipse((x - 4, y - 7, x + 4, y + 7), fill=(*SOIL, 60))
    # crimped (zigzag) top edge of the packet
    zz = [(0, 0)]
    for x in range(0, w + 30, 30):
        zz += [(x, 26), (x + 15, 8)]
    zz += [(w, 0)]
    d.polygon(zz, fill=(*KRAFT_D, 255))
    return im


def main():
    img = Image.open(SRC).convert("RGB").resize((W, SRC_H), Image.LANCZOS)
    img = img.crop((0, CROP_TOP, W, CROP_TOP + H))
    img = ImageEnhance.Color(img).enhance(1.08)
    img = ImageEnhance.Contrast(img).enhance(1.05)
    img = ImageEnhance.Brightness(img).enhance(1.04)

    base = kraft(W, H)
    d = ImageDraw.Draw(base)

    # title band
    d.rounded_rectangle((44, 58, W - 44, 238), radius=40, fill=DEEP)
    d.rounded_rectangle((60, 74, W - 60, 222), radius=30, outline=LEAF, width=4)
    f = font(104)
    title = "BANTAL CARROT"
    l, t, r, b = f.getbbox(title, stroke_width=6)
    tx = W / 2 - (r - l) / 2 - l + 34
    d.text((tx, 148 - (b - t) / 2 - t), title, font=f, fill=CREAM, stroke_width=6, stroke_fill=SOIL)
    paste_center(base, emoji("🥕", 92), tx - 70, 146)

    # photo window
    win = (64, 268, W - 64, 1318)
    ww, wh = win[2] - win[0], win[3] - win[1]
    photo = img.resize((ww, int(ww * img.height / img.width)), Image.LANCZOS)
    oy = 0
    photo = photo.crop((0, oy, ww, oy + wh)).convert("RGBA")
    mask = Image.new("L", (ww, wh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, ww, wh), radius=46, fill=255)
    photo.putalpha(mask)
    rim = Image.new("RGBA", (ww + 24, wh + 24))
    ImageDraw.Draw(rim).rounded_rectangle((0, 0, ww + 23, wh + 23), radius=56, fill=CREAM)
    rim.alpha_composite(photo, (12, 12))
    base.alpha_composite(shadow(rim, offset=(0, 12), blur=14, alpha=110), (win[0] - 12 - 40, win[1] - 12 - 40))

    # tagline hang tag over the lower bodies, stamp at the right, sizes strip at the bottom
    paste_center(base, shadow(hang_tag("2 JENIS *SENYUMAN*!", 70, SUN, SOIL, DEEP, rot=3)), W / 2 - 60, 1180)
    paste_center(base, stamp([("GEBU", 56), ("GEBU!", 56)], 120, CARROT, CREAM, rot=-10), 900, 960)
    paste_center(base, shadow(emoji("😁", 86)), 150, 1010)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((110, 1356, W - 110, 1462), radius=53, fill=SOIL)
    f = font(54)
    txt = "3 SIZE: 90 • 70 • 50 CM"
    l, t, r, b = f.getbbox(txt)
    d.text((W / 2 - (r - l) / 2 - l, 1409 - (b - t) / 2 - t), txt, font=f, fill=SUN)
    paste_center(base, emoji("🌱", 64), 170, 1409)
    paste_center(base, emoji("🌱", 64), W - 170, 1409)
    base.convert("RGB").save(OUT, quality=95)


if __name__ == "__main__":
    main()
