#!/usr/bin/env python3
"""TikTok cover (1080x1536) for the flower / square seat cushion (bantal lapik duduk) video.

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

COCOA = (74, 44, 34)
CARAMEL = (201, 138, 94)
BLUSH = (242, 167, 188)
ROSE = (194, 87, 122)
DOVE = (156, 156, 171)
CREAM = (255, 244, 228)
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


def split_bg():
    """Refresh: three soft vertical colour blocks (the three cushion colours) with a cream stitch between them."""
    bg = Image.new("RGBA", (W, H), (*CREAM, 255))
    d = ImageDraw.Draw(bg)
    cols = [tuple(int(c + (255 - c) * 0.45) for c in col) for col in (CARAMEL, BLUSH, DOVE)]
    for i, col in enumerate(cols):
        d.rectangle((i * W / 3, 0, (i + 1) * W / 3, H), fill=col)
    for i in (1, 2):
        x = i * W / 3
        for y in range(0, H, 34):
            d.line((x, y, x, y + 18), fill=WHITE, width=5)
    return bg


def stitched_photo(img, w, rot):
    """Refresh: the photo as a rounded 'fabric patch' - thick cream rim with a dashed caramel stitch line."""
    img = img.resize((w, int(w * img.height / img.width)), Image.LANCZOS).convert("RGBA")
    rim, rad = 26, 52
    out = Image.new("RGBA", (img.width + 2 * rim, img.height + 2 * rim))
    d = ImageDraw.Draw(out)
    d.rounded_rectangle((0, 0, out.width - 1, out.height - 1), radius=rad + rim, fill=CREAM, outline=WHITE, width=6)
    mask = Image.new("L", img.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img.width - 1, img.height - 1), radius=rad, fill=255)
    out.paste(img, (rim, rim), mask)
    x0, y0, x1, y1 = 13, 13, out.width - 14, out.height - 14
    r = rad + rim - 13
    for (ax, ay, bx, by) in [(x0 + r, y0, x1 - r, y0), (x0 + r, y1, x1 - r, y1), (x0, y0 + r, x0, y1 - r),
                             (x1, y0 + r, x1, y1 - r)]:
        L = math.hypot(bx - ax, by - ay)
        for t in range(0, int(L) - 22, 36):
            u0, u1 = t / L, (t + 22) / L
            d.line((ax + (bx - ax) * u0, ay + (by - ay) * u0, ax + (bx - ax) * u1, ay + (by - ay) * u1),
                   fill=CARAMEL, width=6)
    return shadow(out.rotate(rot, resample=Image.BICUBIC, expand=True), offset=(0, 16), blur=18, alpha=120)


def patch(text, size, bg, fg, icon=None, rot=0):
    """Small stitched patch pill (matches the video labels)."""
    f = font(size)
    l, t, r, b = f.getbbox(text)
    tw, th = r - l, b - t
    ic = emoji(icon, int(size * 1.05)) if icon else None
    iw = ic.width + 14 if ic else 0
    w, h = tw + iw + 70, th + 46
    im = Image.new("RGBA", (w + 12, h + 12))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, w + 6, h + 6), radius=24, fill=bg, outline=WHITE, width=5)
    for (ax, ay, bx, by) in [(36, 17, w - 24, 17), (36, h - 5, w - 24, h - 5)]:
        for x in range(int(ax), int(bx) - 12, 22):
            d.line((x, ay, x + 12, by), fill=CREAM if bg != CREAM else CARAMEL, width=4)
    d.text((6 + 35 - l, 6 + 23 - t), text, font=f, fill=fg)
    if ic:
        im.alpha_composite(ic, (6 + 35 + tw + 14, 6 + (h - ic.height) // 2))
    return im.rotate(rot, resample=Image.BICUBIC, expand=True)


def main():
    img = Image.open(SRC).convert("RGB").resize((W, SRC_H), Image.LANCZOS)
    img = img.crop((0, 300, W, 1720))
    img = ImageEnhance.Color(img).enhance(1.12)
    img = ImageEnhance.Contrast(img).enhance(1.05)
    base = split_bg()

    paste_center(base, stitched_photo(img, 800, 2), W / 2, 880)

    t1 = shadow(outlined_text("LENGUH DUDUK?", 84, WHITE, COCOA, 11, rot=-2))
    t2 = shadow(outlined_text("BANTAL LAPIK DUDUK", 96, BUTTER, COCOA, 12, rot=1))
    paste_center(base, t1, W / 2, 120)
    paste_center(base, t2, W / 2, 245)
    paste_center(base, shadow(emoji("😩", 84)), 985, 112)
    paste_center(base, shadow(emoji("🌸", 80)), 92, 112)

    paste_center(base, shadow(patch("PETAK & BULAT", 46, CREAM, COCOA, "🟫", rot=-3)), 300, 1360)
    paste_center(base, shadow(patch("3 KALER PASTEL", 46, ROSE, WHITE, "🎨", rot=2)), 330, 1440)
    paste_center(base, burst([("SANGAT", 48), ("SELESA!", 52)], CARAMEL, WHITE, -8, 250), 880, 1350)
    base.convert("RGB").save(OUT, quality=95)


if __name__ == "__main__":
    main()
