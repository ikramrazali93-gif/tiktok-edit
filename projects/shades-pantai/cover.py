#!/usr/bin/env python3
"""TikTok cover (1080x1536) for the sunglasses (2 designs) video.

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
SRC_H, CROP_TOP = 1920, 150  # crop window taken from the 1080x1920 frame

ESPRESSO = (43, 26, 18)
TORT = (168, 90, 32)
AMBER = (255, 176, 32)
TEAL = (25, 181, 176)
CREAM = (255, 244, 220)
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
    for y in range(0, 420):
        a = int(170 * (1 - y / 420) ** 1.5)
        gd.line([(0, y), (W, y)], fill=(*ESPRESSO, a))
    base.alpha_composite(grad)

    # sandy scallops + sea wave at the bottom
    edge = Image.new("RGBA", (W, H))
    ed = ImageDraw.Draw(edge)
    ed.rectangle((0, 1460, W, H), fill=(*CREAM, 255))
    for i, x in enumerate(range(-40, W + 120, 150)):
        r = 105 if i % 2 == 0 else 85
        ed.ellipse((x - r, 1460 - r * 0.8, x + r, 1460 + r * 1.2), fill=(*CREAM, 255))
    base.alpha_composite(shadow(edge, offset=(0, -6), blur=10, alpha=80))
    for i, x in enumerate(range(120, W, 210)):
        paste_center(base, emoji("☀️" if i % 2 else "🐚", 52), x, 1490)

    # title above the glasses
    t1 = shadow(outlined_text("SHADES", 120, WHITE, ESPRESSO, 11, rot=2))
    t2 = shadow(outlined_text("TAK KEMBUNG!", 120, AMBER, ESPRESSO, 12, rot=-3))
    paste_center(base, t1, W / 2 - 90, 90)
    paste_center(base, t2, W / 2, 225)
    paste_center(base, shadow(emoji("😎", 110)), 880, 85)

    paste_center(base, shadow(pill("SESUAI PAKAI TUDUNG", 50, TEAL, WHITE, "🧕", rot=3)), 470, 1110)
    paste_center(base, shadow(pill("2 DESAIN: BROWN + RIMLESS", 44, AMBER, ESPRESSO, "🕶️", rot=-2)), 500, 1222)
    paste_center(base, shadow(pill("HARGA MURAH!", 56, CREAM, ESPRESSO, "💸", rot=-3)), 330, 1334)
    paste_center(base, burst([("JOM", 58), ("PANTAI!", 60)], TORT, WHITE, -10, 250), 930, 760)

    base.convert("RGB").save(OUT, quality=95)


if __name__ == "__main__":
    main()
