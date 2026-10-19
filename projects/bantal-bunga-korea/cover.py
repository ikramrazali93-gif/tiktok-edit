#!/usr/bin/env python3
"""TikTok cover (1080x1536) for the flower cushion (bantal bunga) video.

Refresh v5: diagonal two-colour backdrop (lilac / mustard, the two cushion colours) with the photo in an arch
window and a flower-shaped badge, instead of a full-bleed frame, polaroid or rind frame.

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
SRC_H = 1920

ESPRESSO = (72, 48, 32)
LILAC = (180, 160, 226)
LILAC_D = (122, 96, 176)
CREAM = (250, 242, 228)
MUSTARD = (242, 180, 60)
ROSE = (245, 160, 180)
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


def bubble(text, size, bg, fg, icon=None, tail=None, pad=(36, 18)):
    """Flat speech bubble with a thin espresso outline and a hard offset shadow (matches the video labels)."""
    f = font(size)
    l, t, r, b = f.getbbox(text)
    tw, th = r - l, b - t
    ic = emoji(icon, int(size * 1.05)) if icon else None
    iw = ic.width + 14 if ic else 0
    w, h = tw + iw + pad[0] * 2, th + pad[1] * 2
    im = Image.new("RGBA", (w + 24, h + 46))
    d = ImageDraw.Draw(im)
    for dx, dy, col in [(7, 8, (*ESPRESSO, 150)), (0, 0, bg)]:
        d.rounded_rectangle((4 + dx, 4 + dy, w + 4 + dx, h + 4 + dy), radius=int(h * 0.36), fill=col,
                            outline=ESPRESSO if dx == 0 else None, width=4)
        if tail:
            tx = 4 + dx + w * (0.72 if tail == "r" else 0.28)
            lean = 12 if tail == "r" else -12
            d.polygon([(tx - 18, h + 1 + dy), (tx + 18, h + 1 + dy), (tx + lean, h + 30 + dy)], fill=col,
                      outline=ESPRESSO if dx == 0 else None)
            if dx == 0:
                d.line([(tx - 16, h + 2), (tx + 16, h + 2)], fill=bg, width=5)
    d.text((4 + pad[0] - l, 4 + pad[1] - t), text, font=f, fill=fg)
    if ic:
        im.alpha_composite(ic, (4 + pad[0] + tw + 14, 4 + (h - ic.height) // 2))
    return im


def paste_center(base, layer, cx, cy):
    base.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


def flower(size, petal, centre, n=6, outline=WHITE):
    im = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(im)
    c = size / 2
    rp, dp = size * 0.22, size * 0.28
    for k in range(n):
        a = 2 * math.pi * k / n
        x, y = c + dp * math.cos(a), c + dp * math.sin(a)
        d.ellipse((x - rp - 5, y - rp - 5, x + rp + 5, y + rp + 5), fill=outline)
    for k in range(n):
        a = 2 * math.pi * k / n
        x, y = c + dp * math.cos(a), c + dp * math.sin(a)
        d.ellipse((x - rp, y - rp, x + rp, y + rp), fill=petal)
    d.ellipse((c - size * 0.2, c - size * 0.2, c + size * 0.2, c + size * 0.2), fill=centre)
    return im


def badge(lines, size):
    im = flower(size, MUSTARD, CREAM)
    d = ImageDraw.Draw(im)
    n = len(lines)
    for k, (txt, fs, col) in enumerate(lines):
        f = font(fs)
        l, t, r, b = f.getbbox(txt)
        y = size / 2 + (k - (n - 1) / 2) * fs * 0.98
        d.text((size / 2 - (r - l) / 2 - l, y - (b - t) / 2 - t), txt, font=f, fill=col)
    return shadow(im.rotate(-8, resample=Image.BICUBIC, expand=True), offset=(0, 10), blur=12, alpha=120)


def arch_mask(w, h):
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    d.rectangle((0, w // 2, w, h), fill=255)
    d.ellipse((0, 0, w, w), fill=255)
    return m


def main():
    img = Image.open(SRC).convert("RGB").resize((W, SRC_H), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(1.12)
    img = ImageEnhance.Contrast(img).enhance(1.05)
    img = ImageEnhance.Brightness(img).enhance(1.04)

    # diagonal lilac / mustard split with soft cream dots
    base = Image.new("RGBA", (W, H), (*LILAC, 255))
    d = ImageDraw.Draw(base)
    d.polygon([(0, H * 0.62), (W, H * 0.38), (W, H), (0, H)], fill=(*MUSTARD, 255))
    for j, y in enumerate(range(24, H, 72)):
        for x in range(24 + (36 if j % 2 else 0), W, 72):
            d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(*CREAM, 90))

    # the cushions in an arch window with a cream rim
    aw, ah = 800, 1000
    photo = img.crop((40, 200, 1040, 1450)).resize((aw, ah), Image.LANCZOS)
    rim = Image.new("RGBA", (aw + 36, ah + 36))
    rim.paste(Image.new("RGBA", rim.size, (*CREAM, 255)), (0, 0), arch_mask(aw + 36, ah + 36))
    win = Image.new("RGBA", (aw, ah))
    win.paste(photo, (0, 0), arch_mask(aw, ah))
    rim.alpha_composite(win, (18, 18))
    rim = shadow(rim, offset=(10, 14), blur=16, alpha=120)
    paste_center(base, rim, W / 2, 805)

    # title
    paste_center(base, shadow(outlined_text("BANTAL", 112, ESPRESSO, WHITE, 11, rot=2)), W / 2 - 150, 110)
    paste_center(base, shadow(outlined_text("BUNGA!", 140, LILAC_D, WHITE, 13, rot=-2)), W / 2 + 170, 205)
    paste_center(base, shadow(emoji("🌼", 96)), 120, 230)

    # badges / bubbles
    paste_center(base, badge([("SAIZ", 46, ESPRESSO), ("50CM", 70, LILAC_D)], 300), 905, 1160)
    paste_center(base, bubble("ALA-ALA KOREA", 46, CREAM, ESPRESSO, "💫", tail="l"), 270, 1395)
    paste_center(base, bubble("BANYAK KALER", 46, ROSE, ESPRESSO, "🎨", tail="r"), 760, 1405)
    for (x, y, sz, col) in [(90, 470, 90, CREAM), (990, 520, 80, ROSE), (70, 1050, 70, LILAC)]:
        paste_center(base, flower(sz, col, MUSTARD if col != MUSTARD else CREAM), x, y)
    base.convert("RGB").save(OUT, quality=95)


if __name__ == "__main__":
    main()
