#!/usr/bin/env python3
"""TikTok cover (1080x1536) for the avocado plush pillows (bantal avocado, "montel" 70cm + "panjang" 90cm) video.

Refresh v7: a mint wallpaper of little avocado halves, the photo in a rounded window with avocado "rings" (dark
skin rim, cream and lime inner rims), a sticker title with a double outline, and seed-badge pills that match the
seed labels in the video, instead of a polaroid, arch window, rind frame, sunburst, stitched patch, gingham or
comic panel.

Usage: python3 cover.py <frame.png> <out.png>
Canvas is 1080x1536 (20% shorter than 1920); key text stays inside a 3:4 crop (y 48-1488).
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

SKIN = (46, 90, 28)
LEAF = (94, 155, 46)
LIME = (201, 235, 75)
CREAM = (246, 248, 210)
MINT = (214, 240, 196)
SEED = (106, 59, 31)
BLUSH = (255, 143, 177)
WHITE = (255, 255, 255)


def font(size):
    return ImageFont.truetype(FONT, size)


def emoji(ch, size):
    f = ImageFont.truetype(EMOJI, 109)
    im = Image.new("RGBA", (160, 160))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)


def soft_shadow(layer, offset=(0, 14), blur=14, alpha=110):
    out = Image.new("RGBA", (layer.width + 60, layer.height + 60))
    sh = Image.new("RGBA", layer.size, (*SKIN, 0))
    sh.putalpha(layer.split()[-1].point(lambda a: a * alpha // 255))
    out.alpha_composite(sh, (30 + offset[0], 30 + offset[1]))
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(layer, (30, 30))
    return out


def avocado_half(w, rim=True):
    """Small avocado-half icon (skin rim, flesh, seed) for the wallpaper / decorations."""
    h = int(w * 1.38)
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)

    def pear(k, col):
        mx, my = w * (1 - k) / 2, h * (1 - k) / 2
        x0, x1, y0, y1 = mx, w - mx, my, h - my
        d.ellipse((x0, y0 + (y1 - y0) * 0.30, x1, y1), fill=col)                       # round bottom
        d.ellipse((x0 + (x1 - x0) * 0.17, y0, x1 - (x1 - x0) * 0.17, y0 + (y1 - y0) * 0.66), fill=col)  # top

    if rim:
        pear(1.0, SKIN)
        pear(0.86, CREAM)
    pear(0.76, LIME)
    r = w * 0.2
    d.ellipse((w / 2 - r, h * 0.66 - r, w / 2 + r, h * 0.66 + r), fill=SEED)
    return im


def sticker_text(text, size, fill, hi=None, stroke=SKIN):
    """Title text with a dark inner stroke + thick white outer stroke (die-cut sticker). *word* = highlight."""
    f = font(size)
    plain = text.replace("*", "")
    s1, s2 = max(6, size // 12), max(14, size // 6)
    l, t, r, b = f.getbbox(plain, stroke_width=s2)
    im = Image.new("RGBA", (r - l + 40, b - t + 40))
    d = ImageDraw.Draw(im)
    d.text((20 - l, 20 - t), plain, font=f, fill=WHITE, stroke_width=s2, stroke_fill=WHITE)
    x = 20 - l
    for k, part in enumerate(text.split("*")):
        if not part:
            continue
        d.text((x, 20 - t), part, font=f, fill=(hi or fill) if k % 2 else fill, stroke_width=s1, stroke_fill=stroke)
        x += f.getlength(part)
    return im


def seed_pill(text, size, bg, fg, hi=None, icon=None):
    """Pill with a round brown seed badge on the left (emoji inside), same as the video labels."""
    f = font(size)
    plain = text.replace("*", "")
    l, t, r, b = f.getbbox(plain)
    h = int(size * 1.35)
    rb = int(h * 0.62)
    tw = r - l
    w = tw + int(size * 0.9) + int(rb * 1.6)
    pad = 12
    im = Image.new("RGBA", (w + rb + pad * 2, rb * 2 + pad * 2))
    d = ImageDraw.Draw(im)
    cy = pad + rb
    px0 = pad + int(rb * 0.45)
    d.rounded_rectangle((px0, cy - h / 2, px0 + w, cy + h / 2), radius=h / 2, fill=bg, outline=SKIN, width=5)
    bx = px0 + int(rb * 0.55)
    d.ellipse((bx - rb, cy - rb, bx + rb, cy + rb), fill=SEED, outline=LIME, width=6)
    d.ellipse((bx - rb * 0.62, cy - rb * 0.72, bx - rb * 0.05, cy - rb * 0.38), fill=(*CREAM, 120))
    if icon:
        ic = emoji(icon, int(rb * 1.25))
        im.alpha_composite(ic, (int(bx - ic.width / 2), int(cy - ic.height / 2)))
    x = px0 + int(rb * 1.6) + int(size * 0.45) - l
    for k, part in enumerate(text.split("*")):
        if not part:
            continue
        d.text((x, cy - (b + t) / 2), part, font=f, fill=(hi or fg) if k % 2 else fg)
        x += f.getlength(part)
    return im


def paste_center(base, layer, cx, cy):
    base.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


def main():
    img = Image.open(SRC).convert("RGB").resize((W, SRC_H), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(1.10)
    img = ImageEnhance.Contrast(img).enhance(1.05)
    img = ImageEnhance.Brightness(img).enhance(1.04)

    # mint wallpaper: vertical mint -> pale lime gradient + a grid of small tilted avocado halves
    base = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(base)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(MINT[i] * (1 - k) + (232, 246, 176)[i] * k) for i in range(3)) + (255,))
    icon = avocado_half(70)
    for j, y in enumerate(range(-20, H + 60, 150)):
        for i, x in enumerate(range(-30 + (75 if j % 2 else 0), W + 60, 150)):
            ic = icon.rotate(18 if (i + j) % 2 else -18, resample=Image.BICUBIC, expand=True)
            ic.putalpha(ic.split()[-1].point(lambda a: a * 70 // 255))
            base.alpha_composite(ic, (x, y))

    # photo in a rounded window with avocado rings: dark skin rim, cream rim, lime rim
    pw, ph = 860, 1032
    photo = img.crop((40, 196, 1080, 196 + int(1040 * ph / pw))).resize((pw, ph), Image.LANCZOS).convert("RGBA")
    ring = [(SKIN, 30), (CREAM, 18), (LIME, 10)]
    tot = sum(t for _, t in ring)
    win = Image.new("RGBA", (pw + 2 * tot, ph + 2 * tot))
    wd = ImageDraw.Draw(win)
    off, rad = 0, 96
    for col, t in ring:
        wd.rounded_rectangle((off, off, win.width - off, win.height - off), radius=rad - off, fill=col)
        off += t
    mask = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, pw, ph), radius=rad - tot, fill=255)
    win.paste(photo, (tot, tot), mask)
    paste_center(base, soft_shadow(win), W / 2, 860)

    # title (inside the 3:4 crop)
    paste_center(base, sticker_text("TEAM *MONTEL*", 116, LIME, hi=CREAM), W / 2, 150)
    paste_center(base, sticker_text("KE *PANJANG*?", 116, LIME, hi=CREAM), W / 2, 285)

    # decorations: an avocado half peeking at the top-right corner of the window, leaves, sizes pill, seed badge
    paste_center(base, soft_shadow(avocado_half(150).rotate(-16, resample=Image.BICUBIC, expand=True)), 960, 400)
    paste_center(base, soft_shadow(seed_pill("*MONTEL* 70CM • *PANJANG* 90CM", 46, CREAM, SKIN, hi=LEAF, icon="🥑")),
                 W / 2, 1418)
    badge = Image.new("RGBA", (250, 250))
    bd = ImageDraw.Draw(badge)
    bd.ellipse((10, 10, 240, 240), fill=SEED, outline=LIME, width=10)
    bd.ellipse((50, 40, 120, 80), fill=(*CREAM, 110))
    for k, (txt, fs) in enumerate([("GEBU", 54), ("GEBAS!", 48)]):
        f = font(fs)
        l, t, r, b = f.getbbox(txt)
        bd.text((125 - (r - l) / 2 - l, 125 + (k - 0.5) * 58 - (b - t) / 2 - t), txt, font=f, fill=CREAM)
    badge = badge.resize((205, 205), Image.LANCZOS)
    paste_center(base, soft_shadow(badge.rotate(10, resample=Image.BICUBIC, expand=True)), 122, 1235)
    paste_center(base, soft_shadow(emoji("💚", 86)), 112, 420)
    base.convert("RGB").save(OUT, quality=95)


if __name__ == "__main__":
    main()
