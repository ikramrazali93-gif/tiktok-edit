#!/usr/bin/env python3
"""TikTok cover (1080x1536) for the daisy flower pillow (bantal bunga) video.

Breakfast-cafe look (same family as the video's daisy-edge badges and plate end card): a striped
sky/white cafe awning with a scalloped edge, butter background with tiny daisies, the photo in a
white scalloped (petal-edge) frame, a round "plate" badge and a sizes/colours strip.

Usage: python3 cover.py <frame.png> <out.png>
Canvas is 1080x1536 (20% shorter than 1920); key text stays inside a 3:4 crop (y 48-1488).
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

SRC, OUT = sys.argv[1:3]
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "fonts", "Fredoka-Bold.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
W, H = 1080, 1536          # 20% shorter than 9:16 (1920), per request
SRC_H, CROP_TOP = 1920, 160 # crop window taken from the 1080x1920 frame

COCOA = (74, 52, 38)
YOLK = (232, 162, 31)
BUTTER = (255, 224, 138)
CREAM = (255, 248, 236)
SKY = (143, 203, 234)
SKY_D = (47, 134, 192)
CORAL = (240, 88, 74)
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


def paste_center(base, layer, cx, cy):
    base.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


def rich(d, x, y, text, f, fg, hi, **kw):
    """Draw *word* parts in the highlight colour."""
    for i, part in enumerate(text.split("*")):
        d.text((x, y), part, font=f, fill=(hi if i % 2 else fg), **kw)
        x += f.getlength(part)


def scallop_mask(w, h, r, bump):
    """Rounded rect ringed with petal bumps (the video's daisy-edge badge), as an L mask."""
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    inset = bump
    d.rounded_rectangle((inset, inset, w - inset, h - inset), radius=r, fill=255)
    # bumps along the inset rectangle's edges
    step = bump * 1.5
    x0, y0, x1, y1 = inset, inset, w - inset, h - inset
    pts = []
    n = int((x1 - x0 - 2 * r) / step)
    for k in range(n + 1):
        x = x0 + r + (x1 - x0 - 2 * r) * k / max(1, n)
        pts += [(x, y0), (x, y1)]
    n = int((y1 - y0 - 2 * r) / step)
    for k in range(n + 1):
        y = y0 + r + (y1 - y0 - 2 * r) * k / max(1, n)
        pts += [(x0, y), (x1, y)]
    for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x1 - r, y1 - r), (x0 + r, y1 - r)):
        for a in range(0, 360, 30):
            pts.append((cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))))
    for x, y in pts:
        d.ellipse((x - bump, y - bump, x + bump, y + bump), fill=255)
    return m


def badge(text, size, fill, fg, hi, rot=0):
    """Daisy-edge badge like the video labels: white scalloped rim, coloured rounded centre."""
    f = font(size)
    plain = text.replace("*", "")
    l, t, r, b = f.getbbox(plain)
    tw, th = r - l, b - t
    h = int(th + size * 0.85)
    w = tw + int(size * 1.2)
    bump = int(h * 0.2)
    W2, H2 = w + 4 * bump, h + 4 * bump
    rim = scallop_mask(W2, H2, int(h * 0.5), bump)
    im = Image.new("RGBA", (W2, H2))
    outline = Image.new("RGBA", (W2, H2), (*COCOA, 255))
    outline.putalpha(rim.filter(ImageFilter.MaxFilter(7)))
    im.alpha_composite(outline)
    white = Image.new("RGBA", (W2, H2), (*WHITE, 255))
    white.putalpha(rim)
    im.alpha_composite(white)
    d = ImageDraw.Draw(im)
    x0, y0 = (W2 - w) / 2, (H2 - h) / 2
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=h // 2, fill=fill)
    rich(d, x0 + size * 0.6 - l, y0 + (h - th) / 2 - t, text, f, fg, hi)
    return shadow(im.rotate(rot, resample=Image.BICUBIC, expand=True), offset=(4, 10))


def plate(lines, r, rot=0):
    """Round 'breakfast plate' badge: sky rim, white plate, butter inner ring."""
    s = 2 * r + 20
    im = Image.new("RGBA", (s, s))
    d = ImageDraw.Draw(im)
    c = s / 2
    d.ellipse((10, 10, s - 10, s - 10), fill=SKY, outline=COCOA, width=6)
    d.ellipse((c - r + 22, c - r + 22, c + r - 22, c + r - 22), fill=WHITE)
    d.ellipse((c - r + 48, c - r + 48, c + r - 48, c + r - 48), outline=BUTTER, width=6)
    n = len(lines)
    for k, (txt, fs, col) in enumerate(lines):
        f = font(fs)
        l, t, rr, b = f.getbbox(txt)
        y = c + (k - (n - 1) / 2) * fs * 1.05
        d.text((c - (rr - l) / 2 - l, y - (b - t) / 2 - t), txt, font=f, fill=col)
    return shadow(im.rotate(rot, resample=Image.BICUBIC, expand=True))


def daisy(size):
    im = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(im)
    c, pr = size / 2, size * 0.2
    for k in range(8):
        a = 2 * math.pi * k / 8
        x, y = c + size * 0.27 * math.cos(a), c + size * 0.27 * math.sin(a)
        d.ellipse((x - pr, y - pr, x + pr, y + pr), fill=WHITE)
    d.ellipse((c - size * 0.17, c - size * 0.17, c + size * 0.17, c + size * 0.17), fill=YOLK)
    return im


def background():
    im = Image.new("RGBA", (W, H), (*BUTTER, 255))
    rnd = random.Random(7)
    for _ in range(55):
        s = rnd.randint(26, 46)
        dz = daisy(s).rotate(rnd.randint(0, 45))
        dz.putalpha(dz.split()[-1].point(lambda v: v * 150 // 255))
        im.alpha_composite(dz, (rnd.randrange(-20, W), rnd.randrange(120, H)))
    # cafe awning: sky / white stripes with a scalloped lower edge
    d = ImageDraw.Draw(im)
    sw = 90
    for k in range(W // sw + 1):
        col = SKY if k % 2 == 0 else WHITE
        x = k * sw
        d.rectangle((x, 0, x + sw, 96), fill=col)
        d.ellipse((x, 96 - sw / 2, x + sw, 96 + sw / 2), fill=col)
    d.line((0, 96, W, 96), fill=(*COCOA, 60), width=2)
    return im


def main():
    img = Image.open(SRC).convert("RGB").resize((W, SRC_H), Image.LANCZOS)
    img = img.crop((0, CROP_TOP, W, CROP_TOP + H))
    img = ImageEnhance.Color(img).enhance(1.08)
    img = ImageEnhance.Contrast(img).enhance(1.05)
    img = ImageEnhance.Brightness(img).enhance(1.05)

    base = background()

    # photo inside a white petal-edge frame
    win = (96, 300, W - 96, 1290)
    ww, wh = win[2] - win[0], win[3] - win[1]
    # fit the full frame width into the window so both pillows stay in, then pick the band with them
    full = ImageEnhance.Color(Image.open(SRC).convert("RGB")).enhance(1.08)
    full = ImageEnhance.Brightness(ImageEnhance.Contrast(full).enhance(1.05)).enhance(1.05)
    photo = full.resize((ww, int(full.height * ww / full.width)), Image.LANCZOS)
    oy = 250
    photo = photo.crop((0, oy, ww, oy + wh)).convert("RGBA")
    m = Image.new("L", (ww, wh), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, ww, wh), radius=60, fill=255)
    photo.putalpha(m)
    bump = 26
    fw, fh = ww + 4 * bump, wh + 4 * bump
    rim = scallop_mask(fw, fh, 80, bump)
    frame = Image.new("RGBA", (fw, fh))
    ol = Image.new("RGBA", (fw, fh), (*COCOA, 255))
    ol.putalpha(rim.filter(ImageFilter.MaxFilter(7)))
    frame.alpha_composite(ol)
    wh_ = Image.new("RGBA", (fw, fh), (*WHITE, 255))
    wh_.putalpha(rim)
    frame.alpha_composite(wh_)
    frame.alpha_composite(photo, (2 * bump, 2 * bump))
    paste_center(base, shadow(frame, offset=(0, 14), blur=16, alpha=120), W / 2, (win[1] + win[3]) / 2)

    # title: question + product name, as daisy-edge badges over the top of the photo
    paste_center(base, badge("SOFA *KOSONG*?", 58, WHITE, COCOA, SKY_D, rot=-3), W / 2 - 170, 168)
    paste_center(base, badge("BANTAL *BUNGA* GEBU!", 70, BUTTER, COCOA, CORAL, rot=2), W / 2, 318)
    paste_center(base, shadow(emoji("🌼", 88)), W / 2 + 290, 170)

    # plate badge over the lower right of the photo, a sparkle at the left
    paste_center(base, plate([("NAIK", 50, SKY_D), ("SERI", 62, CORAL), ("RUANG TAMU!", 34, COCOA)], 128, rot=-8),
                 W - 200, 1130)
    paste_center(base, shadow(emoji("✨", 76)), 165, 560)

    # sizes + colours strip
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((110, 1356, W - 110, 1462), radius=53, fill=COCOA)
    f = font(50)
    txt = "50 • 35 CM  |  PUTIH • MUSTARD"
    l, t, r, b = f.getbbox(txt)
    d.text((W / 2 - (r - l) / 2 - l, 1409 - (b - t) / 2 - t), txt, font=f, fill=BUTTER)
    base.convert("RGB").save(OUT, quality=95)


if __name__ == "__main__":
    main()
