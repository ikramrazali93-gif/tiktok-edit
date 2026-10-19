#!/usr/bin/env python3
"""TikTok cover (1080x1536) for the banana hug pillow (bantal pisang, sitting on the grass) video.

Picnic look: the photo sits in a rounded window on a red gingham picnic-cloth frame, with a
ticket-stub title (same family as the video labels).

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
SRC_H, CROP_TOP = 1920, 250 # crop window taken from the 1080x1920 frame

CHOC = (90, 58, 34)
YEL = (255, 217, 59)
RED = (229, 72, 77)
CREAM = (255, 248, 225)
LEAF = (79, 168, 74)
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


def gingham(w, h, sq=54):
    """Red-and-cream picnic cloth: translucent red bands crossing on cream."""
    im = Image.new("RGBA", (w, h), (*CREAM, 255))
    band = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(band)
    for y in range(0, h, sq):
        d.rectangle((0, y, w, y + sq // 2), fill=(*RED, 110))
    im.alpha_composite(band)
    band = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(band)
    for x in range(0, w, sq):
        d.rectangle((x, 0, x + sq // 2, h), fill=(*RED, 110))
    im.alpha_composite(band)
    return im


def ticket(text, size, fill, fg, hi=None, rot=0):
    """Ticket stub: notched short sides, dashed perforation and a star on the stub. *word* in `hi`."""
    f = font(size)
    plain = text.replace("*", "")
    l, t, r, b = f.getbbox(plain)
    tw, th = r - l, b - t
    h = int(th + size * 0.75)
    stub = int(h * 0.62)
    w = tw + stub + int(size * 0.95)
    pad = 16
    im = Image.new("RGBA", (w + 2 * pad, h + 2 * pad))
    d = ImageDraw.Draw(im)
    box = (pad, pad, pad + w, pad + h)
    d.rectangle(box, fill=fill, outline=CHOC, width=6)
    nr = int(h * 0.2)
    cy = pad + h // 2
    for nx in (pad, pad + w):           # notches punched out of both short sides
        d.ellipse((nx - nr, cy - nr, nx + nr, cy + nr), fill=(0, 0, 0, 0), outline=CHOC, width=6)
        d.ellipse((nx - nr + 6, cy - nr + 6, nx + nr - 6, cy + nr - 6), fill=(0, 0, 0, 0))
    px = pad + stub
    for yy in range(pad + 12, pad + h - 14, 16):
        d.rectangle((px - 3, yy, px + 3, yy + 9), fill=(*CHOC, 150))
    rs = size * 0.28
    scx, scy = pad + stub / 2, cy
    pts = [(scx + (rs if k % 2 == 0 else rs * 0.42) * math.sin(k * math.pi / 5),
            scy - (rs if k % 2 == 0 else rs * 0.42) * math.cos(k * math.pi / 5)) for k in range(10)]
    d.polygon(pts, fill=hi or RED)
    x = pad + stub + int(size * 0.42) - l
    y = cy - th / 2 - t
    for i, part in enumerate(text.split("*")):
        d.text((x, y), part, font=f, fill=(hi if i % 2 else fg))
        x += f.getlength(part)
    return im.rotate(rot, resample=Image.BICUBIC, expand=True)


def main():
    img = Image.open(SRC).convert("RGB").resize((W, SRC_H), Image.LANCZOS)
    img = img.crop((0, CROP_TOP, W, CROP_TOP + H))
    img = ImageEnhance.Color(img).enhance(1.15)
    img = ImageEnhance.Contrast(img).enhance(1.05)
    img = ImageEnhance.Brightness(img).enhance(1.04)

    base = gingham(W, H)
    # photo window: rounded, white rim, inset so the gingham reads as a picnic-cloth frame
    m_side, m_top, m_bot = 46, 250, 70
    win = (m_side, m_top, W - m_side, H - m_bot)
    ww, wh = win[2] - win[0], win[3] - win[1]
    photo = img.resize((ww, int(ww * img.height / img.width)), Image.LANCZOS)
    oy = max(0, (photo.height - wh) // 2 - 40)
    photo = photo.crop((0, oy, ww, oy + wh)).convert("RGBA")
    mask = Image.new("L", (ww, wh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, ww, wh), radius=56, fill=255)
    photo.putalpha(mask)
    rim = Image.new("RGBA", (ww + 28, wh + 28))
    ImageDraw.Draw(rim).rounded_rectangle((0, 0, ww + 27, wh + 27), radius=68, fill=WHITE)
    rim.alpha_composite(photo, (14, 14))
    base.alpha_composite(shadow(rim, offset=(0, 14), blur=16, alpha=120), (win[0] - 14 - 46, win[1] - 14 - 46))

    # title tickets over the top band (inside the 3:4 crop, y 48-1488)
    paste_center(base, shadow(ticket("PISANG TERLEBIH", 70, CREAM, CHOC, RED, rot=2)), W / 2 - 40, 118)
    paste_center(base, shadow(ticket("*GIZI*!", 112, YEL, CHOC, RED, rot=-3)), W / 2 + 120, 262)
    paste_center(base, shadow(emoji("😂", 104)), 150, 270)
    paste_center(base, shadow(emoji("🍌", 92)), 990, 92)

    # sizes + use cases at the bottom corners, clear of the banana faces
    paste_center(base, shadow(ticket("*3 SIZE*: 35 • 50 • 70CM", 44, CREAM, CHOC, RED, rot=-2)), W / 2, 1385)
    paste_center(base, burst([("GEBU", 58), ("SANGAT!", 46)], YEL, CHOC, -10, 220), 930, 1160)
    base.convert("RGB").save(OUT, quality=95)


if __name__ == "__main__":
    main()
