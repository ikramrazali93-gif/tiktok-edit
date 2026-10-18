#!/usr/bin/env python3
"""TikTok cover (1080x1536) for the long cat pillow video.

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
SRC_H, CROP_TOP = 1920, 0  # crop window taken from the 1080x1920 frame

COCOA = (74, 44, 26)
CARAMEL = (255, 198, 133)
CREAM = (255, 243, 223)
PINK = (255, 126, 179)
SKY = (142, 209, 245)
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

    # soft top gradient so the title reads over the trees
    grad = Image.new("RGBA", (W, H))
    gd = ImageDraw.Draw(grad)
    for y in range(0, 560):
        a = int(170 * (1 - y / 560) ** 1.5)
        gd.line([(0, y), (W, y)], fill=(*COCOA, a))
    base.alpha_composite(grad)

    # cream scallops at the bottom with paw prints
    edge = Image.new("RGBA", (W, H))
    ed = ImageDraw.Draw(edge)
    ed.rectangle((0, 1460, W, H), fill=(*CREAM, 255))
    for i, x in enumerate(range(-40, W + 120, 150)):
        r = 105 if i % 2 == 0 else 85
        ed.ellipse((x - r, 1460 - r * 0.8, x + r, 1460 + r * 1.2), fill=(*CREAM, 255))
    base.alpha_composite(shadow(edge, offset=(0, -6), blur=10, alpha=80))
    for i, x in enumerate(range(120, W, 210)):
        paste_center(base, emoji("🐾", 56).rotate(-15 if i % 2 else 15, expand=True), x, 1490)

    # title (above the cat's head)
    t1 = shadow(outlined_text("BANTAL", 130, WHITE, COCOA, 12, rot=2))
    t2 = shadow(outlined_text("KUCING!", 178, PINK, COCOA, 14, rot=-3))
    paste_center(base, t1, W / 2 - 40, 140)
    paste_center(base, t2, W / 2 - 30, 300)
    paste_center(base, shadow(emoji("😻", 130)), 930, 150)
    paste_center(base, emoji("🐾", 80), 110, 310)

    # feature badges (bottom-left, over the cat's lower body)
    paste_center(base, shadow(pill("PANJANG & LEMBUT", 58, CARAMEL, COCOA, "🤗", rot=3)), 380, 1110)
    paste_center(base, shadow(pill("KAIN BALDU", 60, SKY, COCOA, "✨", rot=-2)), 300, 1222)
    paste_center(base, shadow(pill("ADA TANGAN, KAKI, EKOR", 48, CREAM, COCOA, "🐾", rot=-3)), 440, 1334)

    # "MEOW!" burst
    burst = Image.new("RGBA", (360, 360))
    bd = ImageDraw.Draw(burst)
    pts = []
    for i in range(28):
        ang = i * math.pi / 14
        r = 170 if i % 2 == 0 else 140
        pts.append((180 + r * math.cos(ang), 180 + r * math.sin(ang)))
    bd.polygon(pts, fill=PINK)
    bd.line(pts + [pts[0]], fill=WHITE, width=6)
    f1 = font(82)
    l, t, r, b = f1.getbbox("MEOW!")
    bd.text((180 - (r - l) / 2 - l, 180 - (b - t) / 2 - t), "MEOW!", font=f1, fill=WHITE, stroke_width=4,
            stroke_fill=COCOA)
    burst = shadow(burst.rotate(10, resample=Image.BICUBIC, expand=True).resize((290, 290), Image.LANCZOS))
    paste_center(base, burst, 890, 1000)

    base.convert("RGB").save(OUT, quality=95)


if __name__ == "__main__":
    main()
