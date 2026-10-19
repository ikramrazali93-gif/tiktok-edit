#!/usr/bin/env python3
"""TikTok cover (1080x1536) for the 90cm banana + eggplant (pisang & terung) hug pillow video.

Usage: python3 cover.py <frame.png> <out.png>
Canvas is 1080x1536 (20% shorter than 1920); key text stays inside a 3:4 crop (y 48-1488).
Refresh: banana-yellow / eggplant-purple background split by a zigzag seam with tiny hearts, the photo in a
rounded white frame, slanted 'duo' badges (same as the video) and a heart burst.
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

PLUM = (46, 26, 79)
PURP = (123, 79, 214)
LILAC = (201, 181, 255)
YEL = (255, 225, 77)
BUTTER = (255, 242, 168)
CHEEK = (255, 143, 177)
CREAM = (255, 247, 224)
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


def heart_poly(cx, cy, r):
    pts = []
    for i in range(60):
        t = 2 * math.pi * i / 60
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * r / 16, cy - y * r / 16))
    return pts


def duo_bg():
    """Yellow left / purple right, split by a vertical zigzag seam, sprinkled with small hearts."""
    bg = Image.new("RGBA", (W, H), (*YEL, 255))
    d = ImageDraw.Draw(bg)
    pts = [(W, 0), (W, H)]
    zig, x0 = 60, W / 2
    for i, y in enumerate(range(H, -zig, -zig)):
        pts.append((x0 + (28 if i % 2 else -28), y))
    d.polygon(pts, fill=PURP)
    d.line(pts[2:], fill=WHITE, width=10)
    hl = Image.new("RGBA", (W, H))
    dh = ImageDraw.Draw(hl)
    for k, (x, y) in enumerate(((90, 520), (160, 900), (70, 1180), (990, 600), (930, 980), (1010, 1250),
                                (230, 1420), (850, 1440), (120, 380), (960, 400))):
        col = (255, 255, 255, 150)
        dh.polygon(heart_poly(x, y, 22 + 8 * (k % 3)), fill=col)
    bg.alpha_composite(hl)
    return bg


def framed_photo(img, w, rot):
    """The photo in a rounded white frame with a soft shadow."""
    img = img.resize((w, int(w * img.height / img.width)), Image.LANCZOS).convert("RGBA")
    rim, rad = 20, 46
    out = Image.new("RGBA", (img.width + 2 * rim, img.height + 2 * rim))
    ImageDraw.Draw(out).rounded_rectangle((0, 0, out.width - 1, out.height - 1), radius=rad + rim, fill=WHITE)
    mask = Image.new("L", img.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img.width - 1, img.height - 1), radius=rad, fill=255)
    out.paste(img, (rim, rim), mask)
    return shadow(out.rotate(rot, resample=Image.BICUBIC, expand=True), offset=(0, 18), blur=20, alpha=120)


def badge(text, size, bg, fg, icon, stripe):
    """Slanted 'duo' badge (as in the video): parallelogram, hard plum shadow, coloured leading stripe."""
    f = font(size)
    l, t, r, b = f.getbbox(text)
    tw, th = r - l, b - t
    h = th + 40
    s = int(h * 0.16)
    ic = emoji(icon, int(size * 1.15))
    w = tw + 70 + ic.width + 14
    im = Image.new("RGBA", (w + 2 * s + 30, h + 30))
    d = ImageDraw.Draw(im)

    def para(ox, oy, ww, col, outline=None):
        poly = [(ox + s, oy), (ox + ww + s, oy), (ox + ww - s, oy + h), (ox - s, oy + h)]
        d.polygon(poly, fill=col)
        if outline:
            d.line(poly + [poly[0]], fill=outline, width=6)
    para(s + 12, 12, w, PLUM)
    para(s + 2, 2, w, bg, WHITE)
    d.polygon([(s + 2 + s, 6), (s + 2 + s + 16, 6), (s + 2 - s + 16, h - 2), (s + 2 - s, h - 2)], fill=stripe)
    d.text((s + 2 + 40 - l, 2 + 20 - t), text, font=f, fill=fg)
    im.alpha_composite(ic, (s + 2 + 40 + tw + 14, 2 + (h - ic.height) // 2))
    return im


def heart_burst(lines, size):
    im = Image.new("RGBA", (400, 400))
    d = ImageDraw.Draw(im)
    d.polygon(heart_poly(200, 210, 185), fill=CHEEK)
    d.line(heart_poly(200, 210, 185) + [heart_poly(200, 210, 185)[0]], fill=WHITE, width=10)
    n = len(lines)
    for k, (txt, fs) in enumerate(lines):
        f = font(fs)
        l, t, r, b = f.getbbox(txt)
        y = 190 + (k - (n - 1) / 2) * fs * 1.0
        d.text((200 - (r - l) / 2 - l, y - (b - t) / 2 - t), txt, font=f, fill=WHITE, stroke_width=4, stroke_fill=PLUM)
    return shadow(im.rotate(-8, resample=Image.BICUBIC, expand=True).resize((size, size), Image.LANCZOS))


def main():
    img = Image.open(SRC).convert("RGB").resize((W, SRC_H), Image.LANCZOS)
    img = img.crop((30, 120, 1050, 1500))
    img = ImageEnhance.Color(img).enhance(1.1)
    img = ImageEnhance.Contrast(img).enhance(1.05)
    base = duo_bg()

    paste_center(base, framed_photo(img, 740, 0), W / 2, 850)

    t1 = shadow(outlined_text("BANTAL PELUK", 84, WHITE, PLUM, 12))
    t2a = outlined_text("TERUNG", 104, PURP, WHITE, 12, rot=-3)
    t2b = outlined_text("& PISANG!", 104, YEL, PLUM, 12, rot=-3)
    paste_center(base, t1, W / 2, 110)
    gap = -10
    x0 = W / 2 - (t2a.width + t2b.width + gap) / 2
    paste_center(base, shadow(t2a), x0 + t2a.width / 2, 245)
    paste_center(base, shadow(t2b), x0 + t2a.width + gap + t2b.width / 2, 245)

    paste_center(base, shadow(badge("PANJANG 90CM", 46, YEL, PLUM, "📏", PURP)), 330, 1330)
    paste_center(base, shadow(badge("UNIK DESAIN", 46, LILAC, PLUM, "✨", YEL)), 300, 1430)
    paste_center(base, heart_burst([("TEAM", 62), ("MANA?", 70)], 280), 880, 1360)
    base.convert("RGB").save(OUT, quality=95)


if __name__ == "__main__":
    main()
