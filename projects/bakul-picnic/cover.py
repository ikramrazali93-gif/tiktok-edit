#!/usr/bin/env python3
"""TikTok cover (1080x1536) for the woven picnic basket video.

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
SRC_H, CROP_TOP = 1920, 120 # crop window taken from the 1080x1920 frame

NAVY = (31, 47, 92)       # batik trim
TAN = (230, 190, 114)     # rattan weave
PINK = (255, 79, 123)     # inner stripe
YELLOW = (255, 201, 60)
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
        a = int(175 * (1 - y / 420) ** 1.5)
        gd.line([(0, y), (W, y)], fill=(*NAVY, a))
    base.alpha_composite(grad)

    # picnic-blanket gingham strip at the bottom with a scalloped top edge
    band = Image.new("RGBA", (W, H))
    bd = ImageDraw.Draw(band)
    top, cell = 1440, 32
    for yy in range(top - 20, H, cell):
        for xx in range(0, W, cell):
            i, j = (xx // cell) % 2, ((yy - top) // cell) % 2
            col = PINK if i and j else ((255, 170, 190) if i or j else WHITE)
            bd.rectangle((xx, yy, xx + cell, yy + cell), fill=(*col, 255))
    mask = Image.new("L", (W, H))
    md = ImageDraw.Draw(mask)
    md.rectangle((0, top, W, H), fill=255)
    for cx in range(0, W + 60, 60):
        md.ellipse((cx - 30, top - 22, cx + 30, top + 22), fill=255)
    band.putalpha(mask)
    edge = Image.new("RGBA", (W, H))
    ed = ImageDraw.Draw(edge)
    ed.rectangle((0, top - 6, W, H), fill=(*WHITE, 255))
    for cx in range(0, W + 60, 60):
        ed.ellipse((cx - 36, top - 28, cx + 36, top + 28), fill=(*WHITE, 255))
    base.alpha_composite(shadow(edge, (0, -4), 10, 90))
    base.alpha_composite(band)

    t1 = shadow(outlined_text("BAKUL PICNIC", 116, WHITE, NAVY, 11, rot=2))
    t2 = shadow(outlined_text("CUTI SEKOLAH!", 104, YELLOW, NAVY, 12, rot=-3))
    paste_center(base, t1, W / 2 - 30, 95)
    paste_center(base, t2, W / 2 - 20, 222)
    paste_center(base, shadow(emoji("🧺", 120)), 975, 205)

    paste_center(base, shadow(pill("ANYAMAN COMEL", 46, TAN, NAVY, "🥰", rot=3)), 300, 1335)
    paste_center(base, shadow(pill("2 SIZE", 50, YELLOW, NAVY, "📏", rot=-3)), 820, 1345)
    paste_center(base, burst([("WAJIB", 60), ("ADA!", 64)], PINK, WHITE, -10, 230), 150, 420)

    base.convert("RGB").save(OUT, quality=95)


if __name__ == "__main__":
    main()
