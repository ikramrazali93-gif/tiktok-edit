#!/usr/bin/env python3
"""TikTok cover (1080x1536) for the 75cm white 'bambam' cat hug pillow video.

Usage: python3 cover.py <frame.png> <out.png>
Canvas is 1080x1536 (20% shorter than 1920); key text stays inside a 3:4 crop (y 48-1488).
Refresh: blush/cream checkerboard background, the photo inside a cat-head shaped frame (two ears with blush
insides, cream rim, ink outline), whiskers either side of the title, and the same 'cat-ear tags' as the video.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

SRC, OUT = sys.argv[1:3]
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "fonts", "Fredoka-Bold.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
W, H = 1080, 1536          # 20% shorter than 9:16 (1920), per request
SRC_H = 1920

INK = (58, 46, 57)
BLUSH = (255, 179, 207)
ROSE = (240, 96, 154)
SKY = (154, 212, 245)
TAUPE = (184, 147, 110)
CREAM = (255, 246, 236)
BUTTER = (255, 226, 122)
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


def paste_center(base, layer, cx, cy):
    base.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


def ear_poly(cx, base_y, w, h):
    """Cat ear triangle with its base centred on (cx, base_y)."""
    return [(cx - w / 2, base_y), (cx - w * 0.08, base_y - h), (cx + w * 0.08, base_y - h), (cx + w / 2, base_y)]


def checker_bg():
    bg = Image.new("RGBA", (W, H), (*CREAM, 255))
    d = ImageDraw.Draw(bg)
    s = 90
    for j in range(H // s + 1):
        for i in range(W // s + 1):
            if (i + j) % 2 == 0:
                d.rectangle((i * s, j * s, i * s + s - 1, j * s + s - 1), fill=(*BLUSH, 255))
    # soften it so the frame and text stay the hero
    veil = Image.new("RGBA", (W, H), (*CREAM, 120))
    bg.alpha_composite(veil)
    return bg


def cat_frame(img, w):
    """Photo inside a cat-head shaped frame: rounded rect + two ears, cream rim, ink outline, blush inner ears."""
    img = img.resize((w, int(w * img.height / img.width)), Image.LANCZOS).convert("RGBA")
    rim, rad, eh = 22, 70, 120
    fw, fh = img.width + 2 * rim, img.height + 2 * rim
    out = Image.new("RGBA", (fw + 20, fh + eh + 20))
    d = ImageDraw.Draw(out)
    ox, oy = 10, eh + 10
    for ex in (ox + 150, ox + fw - 150):
        d.polygon(ear_poly(ex, oy + 40, 210, eh + 40), fill=CREAM, outline=INK, width=8)
        d.polygon(ear_poly(ex, oy + 30, 110, eh - 10), fill=BLUSH)
    d.rounded_rectangle((ox, oy, ox + fw, oy + fh), radius=rad + rim, fill=CREAM, outline=INK, width=8)
    mask = Image.new("L", img.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img.width - 1, img.height - 1), radius=rad, fill=255)
    out.paste(img, (ox + rim, oy + rim), mask)
    return shadow(out, offset=(0, 18), blur=20, alpha=120)


def ear_tag(text, size, bg, fg, icon=None, hi=None):
    """Same 'cat-ear tag' as in the video: rounded tag, ink outline, two little ears on top."""
    f = font(size)
    parts = text.split("*")
    tw = sum(f.getlength(p) for p in parts)
    l, t, r, b = f.getbbox(text.replace("*", ""))
    th = b - t
    ic = emoji(icon, int(size * 1.1)) if icon else None
    iw = ic.width + 14 if ic else 0
    w, h = int(tw + iw + 60), th + 40
    im = Image.new("RGBA", (w + 20, h + 60))
    d = ImageDraw.Draw(im)
    ox, oy = 10, 46
    for ex in (ox + 42, ox + w - 42):
        d.polygon(ear_poly(ex, oy + 12, 52, 50), fill=bg, outline=INK, width=5)
        d.polygon(ear_poly(ex, oy + 8, 24, 26), fill=BLUSH if bg != BLUSH else CREAM)
    d.rounded_rectangle((ox, oy, ox + w, oy + h), radius=28, fill=bg, outline=INK, width=5)
    x = ox + 30
    for k, p in enumerate(parts):
        d.text((x, oy + 20 - t), p, font=f, fill=(hi if k % 2 else fg))
        x += f.getlength(p)
    if ic:
        im.alpha_composite(ic, (int(x + 14), oy + (h - ic.height) // 2))
    return shadow(im, offset=(4, 10), blur=8, alpha=120)


def whiskers(d, x, y, side, length=90, width=9):
    for dy, slope in ((-26, -0.22), (0, 0), (26, 0.22)):
        x1 = x + side * length
        d.line((x, y + dy, x1, y + dy + slope * length), fill=INK, width=width)


def main():
    img = Image.open(SRC).convert("RGB").resize((W, SRC_H), Image.LANCZOS)
    img = img.crop((200, 200, 1080, 1540))          # just the cat (keeps the busy shelf out)
    img = ImageEnhance.Color(img).enhance(1.08)
    img = ImageEnhance.Contrast(img).enhance(1.05)
    img = ImageEnhance.Brightness(img).enhance(1.04)
    base = checker_bg()

    paste_center(base, cat_frame(img, 600), W / 2, 915)

    t1 = shadow(outlined_text("KUCING", 132, WHITE, INK, 14))
    t2 = shadow(outlined_text("BAMBAM!", 132, ROSE, INK, 14, rot=-2))
    paste_center(base, t1, W / 2, 118)
    paste_center(base, t2, W / 2, 240)
    d = ImageDraw.Draw(base)
    whiskers(d, W / 2 - t2.width / 2 + 10, 240, -1)
    whiskers(d, W / 2 + t2.width / 2 - 10, 240, 1)

    paste_center(base, ear_tag("SAIZ *75CM*", 52, SKY, INK, "📏", hi=ROSE), 250, 1400)
    paste_center(base, ear_tag("BULU *FLUFFY*", 52, BUTTER, INK, "☁️", hi=ROSE), 820, 1400)
    paste_center(base, shadow(emoji("😻", 150)), 900, 600)
    base.convert("RGB").save(OUT, quality=95)


if __name__ == "__main__":
    main()
