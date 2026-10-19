#!/usr/bin/env python3
"""TikTok cover (1080x1536) for the round watermelon plush (bantal tembikai bulat) video.

Usage: python3 cover.py <frame.png> <out.png>
Canvas is 1080x1536 (20% shorter than 1920); key text stays inside a 3:4 crop (y 48-1488).
Refreshed layout: the photo sits in a tilted polaroid frame on a watermelon-flesh background with seeds,
with a rind-striped band along the bottom (instead of the full-bleed photo used before).
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

SRC, OUT = sys.argv[1:3]
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "fonts", "Fredoka-Bold.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
W, H = 1080, 1536          # 20% shorter than 9:16 (1920), per request
PHOTO_BOX = (110, 230, 990, 1390)   # crop of the 1080x1920 frame around the watermelon (x0, y0, x1, y1)

DEEP = (30, 90, 49)
RIND = (63, 163, 77)
LEAF = (185, 228, 160)
FLESH = (255, 92, 138)
FLESH_L = (255, 140, 168)
RED = (224, 36, 94)
SEED = (43, 43, 43)
SUN = (255, 210, 63)
CREAM = (255, 248, 232)
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


def sticker_text(text, size, fill, inner, rot=0):
    """Die-cut sticker text: coloured outline inside a thick white outline (matches the video labels)."""
    f = font(size)
    l, t, r, b = f.getbbox(text, stroke_width=size // 5)
    im = Image.new("RGBA", (r - l + 60, b - t + 60))
    d = ImageDraw.Draw(im)
    d.text((30 - l, 30 - t), text, font=f, fill=WHITE, stroke_width=size // 5, stroke_fill=WHITE)
    d.text((30 - l, 30 - t), text, font=f, fill=fill, stroke_width=size // 11, stroke_fill=inner)
    return im.rotate(rot, resample=Image.BICUBIC, expand=True)


def pill(text, size, bg, fg, icon=None, rot=0, pad=(36, 16)):
    f = font(size)
    l, t, r, b = f.getbbox(text)
    tw, th = r - l, b - t
    ic = emoji(icon, int(size * 1.05)) if icon else None
    iw = ic.width + 14 if ic else 0
    w, h = tw + iw + pad[0] * 2, th + pad[1] * 2
    im = Image.new("RGBA", (w + 12, h + 12))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, w + 6, h + 6), radius=h // 2, fill=bg, outline=WHITE, width=6)
    x = 6 + pad[0]
    if ic:
        im.alpha_composite(ic, (x, 6 + (h - ic.height) // 2))
        x += iw
    d.text((x - l, 6 + pad[1] - t), text, font=f, fill=fg)
    return im.rotate(rot, resample=Image.BICUBIC, expand=True)


def paste_center(base, layer, cx, cy):
    base.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


def seed(size, rot):
    im = Image.new("RGBA", (size * 2, size * 3))
    d = ImageDraw.Draw(im)
    w, h = size * 2, size * 3
    d.ellipse((w * 0.18, h * 0.22, w * 0.82, h * 0.95), fill=SEED)
    d.polygon([(w * 0.5, h * 0.02), (w * 0.22, h * 0.5), (w * 0.78, h * 0.5)], fill=SEED)
    d.ellipse((w * 0.36, h * 0.45, w * 0.5, h * 0.62), fill=(110, 110, 110))   # tiny highlight
    return im.rotate(rot, resample=Image.BICUBIC, expand=True)


def burst(text_lines, fill, fg, rot, size):
    im = Image.new("RGBA", (360, 360))
    d = ImageDraw.Draw(im)
    pts = []
    for i in range(28):
        ang = i * math.pi / 14
        r = 170 if i % 2 == 0 else 142
        pts.append((180 + r * math.cos(ang), 180 + r * math.sin(ang)))
    d.polygon(pts, fill=fill)
    d.line(pts + [pts[0]], fill=WHITE, width=7)
    n = len(text_lines)
    for k, (txt, fs) in enumerate(text_lines):
        f = font(fs)
        l, t, r, b = f.getbbox(txt)
        y = 180 + (k - (n - 1) / 2) * fs * 0.95
        d.text((180 - (r - l) / 2 - l, y - (b - t) / 2 - t), txt, font=f, fill=fg)
    return shadow(im.rotate(rot, resample=Image.BICUBIC, expand=True).resize((size, size), Image.LANCZOS))


def main():
    # background: watermelon flesh with a soft radial lighter centre and scattered seeds
    base = Image.new("RGBA", (W, H), (*FLESH, 255))
    glow = Image.new("RGBA", (W, H))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-200, 150, W + 200, H - 50), fill=(*FLESH_L, 150))
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))
    rnd = random.Random(4)
    for _ in range(46):
        x, y = rnd.uniform(20, W - 20), rnd.uniform(20, H - 160)
        base.alpha_composite(seed(rnd.randint(9, 13), rnd.uniform(-40, 40)), (int(x), int(y)))

    # rind band along the bottom: white -> pale green -> green -> dark green, gently curved
    band = Image.new("RGBA", (W, H))
    bd = ImageDraw.Draw(band)
    for col, top in [(CREAM, 1330), (LEAF, 1362), (RIND, 1398), (DEEP, 1440)]:
        bd.ellipse((-400, top, W + 400, top + 900), fill=(*col, 255))
    base.alpha_composite(band)
    # stripes on the dark rind
    st = Image.new("RGBA", (W, H))
    sd = ImageDraw.Draw(st)
    for x in range(-40, W + 80, 90):
        sd.polygon([(x, H), (x + 30, 1450), (x + 60, 1450), (x + 30, H)], fill=(*RIND, 200))
    base.alpha_composite(st)

    # polaroid photo
    img = Image.open(SRC).convert("RGB").resize((W, 1920), Image.LANCZOS).crop(PHOTO_BOX)
    img = ImageEnhance.Color(img).enhance(1.15)
    img = ImageEnhance.Contrast(img).enhance(1.05)
    img = ImageEnhance.Brightness(img).enhance(1.04)
    pw, ph = 760, int(760 * img.height / img.width)
    img = img.resize((pw, ph), Image.LANCZOS)
    pad, bottom = 26, 90
    pol = Image.new("RGBA", (pw + 2 * pad, ph + pad + bottom), (*WHITE, 255))
    pol.paste(img, (pad, pad))
    pd = ImageDraw.Draw(pol)
    f = font(46)
    txt = "comelnya!"
    l, t, r, b = f.getbbox(txt)
    pd.text(((pol.width - (r - l)) / 2 - l, ph + pad + (bottom - (b - t)) / 2 - t), txt, font=f, fill=RED)
    pol = shadow(pol.rotate(-3, resample=Image.BICUBIC, expand=True), offset=(0, 16), blur=20, alpha=130)
    paste_center(base, pol, W / 2 + 10, 815)

    # washi tape on the polaroid's top corners
    for cx, rot in [(250, 35), (840, -30)]:
        tape = Image.new("RGBA", (190, 56), (*LEAF, 215))
        td = ImageDraw.Draw(tape)
        for x in range(0, 190, 28):
            td.line([(x, 0), (x + 14, 56)], fill=(*RIND, 120), width=6)
        paste_center(base, tape.rotate(rot, resample=Image.BICUBIC, expand=True), cx, 300)

    # title
    paste_center(base, shadow(sticker_text("BANTAL", 104, WHITE, DEEP, rot=2)), W / 2 - 150, 120)
    paste_center(base, shadow(sticker_text("TEMBIKAI!", 128, SUN, RED, rot=-3)), W / 2 + 60, 225)
    paste_center(base, shadow(emoji("🍉", 110)), 925, 105)

    # what she says: over the trees (top left) and her dark top (right), clear of the watermelon
    paste_center(base, shadow(pill("ADA KAKI & TANGAN", 42, RIND, WHITE, "🙌", rot=-3)), 300, 408)
    paste_center(base, shadow(pill("BULU FLUFFY", 44, WHITE, RED, "☁️", rot=3)), 820, 1015)
    paste_center(base, burst([("GEMOY!", 64)], SUN, RED, -10, 250), 905, 470)
    base.convert("RGB").save(OUT, quality=95)


if __name__ == "__main__":
    main()
