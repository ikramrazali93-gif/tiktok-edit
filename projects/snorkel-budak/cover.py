#!/usr/bin/env python3
"""TikTok cover (1080x1920) for the kids goggle + snorkel video.

Usage: python3 cover.py <frame.png> <out.png>
Key text stays inside the 3:4 profile-grid crop (y 240-1680).
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

SRC, OUT = sys.argv[1:3]
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "fonts", "Fredoka-Bold.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
W, H = 1080, 1920

NAVY = (11, 30, 79)
COBALT = (29, 78, 216)
AQUA = (56, 225, 255)
SUN = (255, 214, 10)
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
    img = Image.open(SRC).convert("RGB").resize((W, H), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(1.18)
    img = ImageEnhance.Contrast(img).enhance(1.06)
    img = ImageEnhance.Brightness(img).enhance(1.04)
    base = img.convert("RGBA")

    # soft top gradient so the title reads over the sky/trees
    grad = Image.new("RGBA", (W, H))
    gd = ImageDraw.Draw(grad)
    for y in range(0, 760):
        a = int(160 * (1 - y / 760) ** 1.6)
        gd.line([(0, y), (W, y)], fill=(*NAVY, a))
    base.alpha_composite(grad)

    # water waves at the bottom with bubbles
    wave = Image.new("RGBA", (W, H))
    wd = ImageDraw.Draw(wave)
    for k, (col, off, amp) in enumerate([((*AQUA, 200), 1700, 26), ((*WHITE, 230), 1745, 20),
                                         ((*COBALT, 255), 1775, 24)]):
        pts = [(x, off + amp * math.sin(x / 75 + k * 1.3)) for x in range(0, W + 10, 10)]
        wd.polygon(pts + [(W, H), (0, H)], fill=col)
    base.alpha_composite(wave)
    bd0 = ImageDraw.Draw(base)
    for (x, y, r) in [(90, 1640, 22), (140, 1590, 12), (990, 1620, 26), (940, 1565, 14), (1030, 1540, 9)]:
        bd0.ellipse((x - r, y - r, x + r, y + r), outline=(*WHITE, 230), width=5)

    # title
    t1 = shadow(outlined_text("SET SNORKEL", 128, WHITE, NAVY, 12, rot=2))
    t2 = shadow(outlined_text("BUDAK!", 190, SUN, NAVY, 14, rot=-3))
    paste_center(base, t1, W / 2, 300)
    paste_center(base, t2, W / 2 - 50, 480)
    paste_center(base, shadow(emoji("🤿", 140)), 950, 560)
    paste_center(base, emoji("🫧", 90), 130, 470)

    # badges (bottom, inside the 3:4 crop)
    paste_center(base, shadow(pill("GOGGLE + SNORKEL", 60, COBALT, WHITE, "🥽", rot=3)), 420, 1390)
    paste_center(base, shadow(pill("UNTUK KANAK-KANAK", 56, WHITE, NAVY, "🧒", rot=-2)), 450, 1505)
    paste_center(base, shadow(pill("CUTI SEKOLAH JOM MANDI!", 50, SUN, NAVY, "🏖️", rot=-3)), 500, 1620)

    base.convert("RGB").save(OUT, quality=95)


if __name__ == "__main__":
    main()
