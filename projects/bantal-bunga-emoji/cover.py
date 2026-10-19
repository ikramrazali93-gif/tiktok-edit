#!/usr/bin/env python3
"""TikTok cover (1080x1536) for the rainbow emoji flower pillow (bantal bunga emoji) video.

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

GRAPE = (59, 31, 92)
RAINBOW = [(255, 90, 95), (255, 159, 28), (255, 217, 61), (92, 201, 107), (77, 150, 255), (155, 93, 229),
           (255, 126, 182)]
RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, PINK = RAINBOW
CREAM = (255, 248, 231)
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


def sunburst():
    """Refresh: rainbow rays radiating from behind the title (cream + petal colours)."""
    bg = Image.new("RGBA", (W, H), (*CREAM, 255))
    d = ImageDraw.Draw(bg)
    cx, cy, n = W / 2, 250, 28
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 0.5) / n
        col = RAINBOW[(i // 1) % len(RAINBOW)]
        d.polygon([(cx, cy), (cx + 2400 * math.cos(a0), cy + 2400 * math.sin(a0)),
                   (cx + 2400 * math.cos(a1), cy + 2400 * math.sin(a1))], fill=(*col, 150))
    return bg


def photo_sticker(img, w, rot):
    """Refresh: the product photo as a rounded sticker with a thick white rim and a dashed rainbow inner line."""
    img = img.resize((w, int(w * img.height / img.width)), Image.LANCZOS).convert("RGBA")
    rim, rad = 22, 46
    out = Image.new("RGBA", (img.width + 2 * rim, img.height + 2 * rim))
    d = ImageDraw.Draw(out)
    d.rounded_rectangle((0, 0, out.width - 1, out.height - 1), radius=rad + rim, fill=WHITE)
    mask = Image.new("L", img.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img.width - 1, img.height - 1), radius=rad, fill=255)
    out.paste(img, (rim, rim), mask)
    # dashed rainbow line just inside the rim
    x0, y0, x1, y1 = rim + 14, rim + 14, out.width - rim - 15, out.height - rim - 15
    seg, k = 34, 0
    for (ax, ay, bx, by) in [(x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)]:
        L = math.hypot(bx - ax, by - ay)
        for t in range(0, int(L) - seg, seg * 2):
            u0, u1 = t / L, (t + seg) / L
            d.line((ax + (bx - ax) * u0, ay + (by - ay) * u0, ax + (bx - ax) * u1, ay + (by - ay) * u1),
                   fill=RAINBOW[k % len(RAINBOW)], width=7)
            k += 1
    return shadow(out.rotate(rot, resample=Image.BICUBIC, expand=True), offset=(0, 16), blur=18, alpha=120)


def main():
    img = Image.open(SRC).convert("RGB").resize((W, SRC_H), Image.LANCZOS)
    img = img.crop((0, 230, W, 1180))
    img = ImageEnhance.Color(img).enhance(1.15)
    img = ImageEnhance.Contrast(img).enhance(1.05)
    base = sunburst()

    paste_center(base, photo_sticker(img, 880, -3), W / 2, 820)

    t1 = shadow(outlined_text("BANTAL BUNGA", 118, WHITE, GRAPE, 12, rot=2))
    t2 = shadow(outlined_text("EMOJI!", 150, YELLOW, GRAPE, 14, rot=-3))
    paste_center(base, t1, W / 2, 135)
    paste_center(base, t2, W / 2 + 4, 290)
    paste_center(base, shadow(emoji("🌼", 96)), 120, 300)
    paste_center(base, shadow(emoji("😜", 96)), 960, 290)

    paste_center(base, shadow(pill("4 GAYA MUKA", 52, PURPLE, WHITE, "🤩", rot=-2)), 330, 1305)
    paste_center(base, shadow(pill("KAIN VELVET", 52, BLUE, WHITE, "🧸", rot=2)), 330, 1412)
    paste_center(base, burst([("LIDAH", 54), ("BOLEH", 54), ("ANGKAT!", 54)], RED, WHITE, -8, 270), 860, 1300)
    base.convert("RGB").save(OUT, quality=95)


if __name__ == "__main__":
    main()
