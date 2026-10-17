#!/usr/bin/env python3
"""TikTok cover (1080x1920) for the grey cloud cushion video.

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
SRC_H, CROP_TOP = 1920, 230  # crop window taken from the 1080x1920 frame

SLATE = (43, 49, 80)
GREYBLUE = (135, 150, 200)
PERI = (79, 95, 168)
CREAM = (255, 244, 220)
GOLD = (255, 201, 60)
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


def main():
    img = Image.open(SRC).convert("RGB").resize((W, SRC_H), Image.LANCZOS)
    img = img.crop((0, CROP_TOP, W, CROP_TOP + H))
    img = ImageEnhance.Color(img).enhance(1.18)
    img = ImageEnhance.Contrast(img).enhance(1.06)
    img = ImageEnhance.Brightness(img).enhance(1.04)
    base = img.convert("RGBA")

    # soft top gradient so the title reads over the sky/trees
    grad = Image.new("RGBA", (W, H))
    gd = ImageDraw.Draw(grad)
    for y in range(0, 620):
        a = int(160 * (1 - y / 620) ** 1.6)
        gd.line([(0, y), (W, y)], fill=(*SLATE, a))
    base.alpha_composite(grad)

    # cream "cloud" scallops at the bottom, like the cushion's piping
    cloud = Image.new("RGBA", (W, H))
    cd = ImageDraw.Draw(cloud)
    cd.rectangle((0, 1460, W, H), fill=(*CREAM, 255))
    for i, x in enumerate(range(-40, W + 120, 150)):
        r = 105 if i % 2 == 0 else 85
        cd.ellipse((x - r, 1460 - r * 0.8, x + r, 1460 + r * 1.2), fill=(*CREAM, 255))
    base.alpha_composite(shadow(cloud, offset=(0, -6), blur=10, alpha=80))

    # title
    t1 = shadow(outlined_text("BANTAL", 150, WHITE, SLATE, 12, rot=2))
    t2 = shadow(outlined_text("GEBU!", 200, GOLD, SLATE, 14, rot=-3))
    paste_center(base, t1, W / 2 - 60, 190)
    paste_center(base, t2, W / 2 - 40, 375)
    paste_center(base, shadow(emoji("☁️", 170)), 860, 190)
    paste_center(base, shadow(emoji("🤤", 120)), 870, 400)

    # star row (customers satisfied)
    for i in range(5):
        paste_center(base, shadow(emoji("⭐", 70)), 300 + i * 88, 515)

    # feature badges (bottom, inside the 3:4 crop, left/centre)
    paste_center(base, shadow(pill("TEBAL & LEMBUT", 60, CREAM, SLATE, "☁️", rot=3)), 360, 1100)
    paste_center(base, shadow(pill("BEST BUAT DUDUK", 58, GREYBLUE, WHITE, "👍", rot=-2)), 430, 1212)
    paste_center(base, shadow(pill("RAMAI BELI DI LIVE", 56, SLATE, WHITE, "🔥", rot=-3)), 410, 1324)

    # restock burst
    burst = Image.new("RGBA", (360, 360))
    bd = ImageDraw.Draw(burst)
    pts = []
    for i in range(28):
        ang = i * math.pi / 14
        r = 170 if i % 2 == 0 else 140
        pts.append((180 + r * math.cos(ang), 180 + r * math.sin(ang)))
    bd.polygon(pts, fill=GOLD)
    bd.line(pts + [pts[0]], fill=WHITE, width=6)
    f1, f2 = font(76), font(50)
    for txt, f, y in [("RE-", f1, 140), ("STOCK!", f2, 210)]:
        l, t, r, b = f.getbbox(txt)
        bd.text((180 - (r - l) / 2 - l, y - (b - t) / 2 - t), txt, font=f, fill=SLATE)
    burst = shadow(burst.rotate(-12, resample=Image.BICUBIC, expand=True).resize((300, 300), Image.LANCZOS))
    paste_center(base, burst, 880, 1040)

    base.convert("RGB").save(OUT, quality=95)


if __name__ == "__main__":
    main()
