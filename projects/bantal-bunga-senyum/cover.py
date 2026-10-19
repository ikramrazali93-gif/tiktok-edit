#!/usr/bin/env python3
"""TikTok cover (1080x1536) for the smiley flower pillows (bantal bunga senyum) video.

Usage: python3 cover.py <frame.png> <out.png>
Canvas is 1080x1536 (20% shorter than 1920); key text stays inside a 3:4 crop (y 48-1488).
Refreshed layout (different from the polaroid / rind-frame covers): diagonal lilac/pink split background with
honey dots, the photo in a rounded cream frame with a dashed lilac "stitch" line, the title in a speech bubble
(matching the video's bubble labels) and a row of little six-petal flowers along the bottom.
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
PHOTO_BOX = (0, 400, 1080, 1400)    # crop of the 1080x1920 frame around the three pillows (x0, y0, x1, y1)

PLUM = (74, 44, 94)
LILAC = (183, 156, 230)
LILAC_D = (142, 107, 209)
PINK = (244, 155, 194)
ROSE = (240, 106, 154)
CREAM = (255, 246, 230)
HONEY = (255, 201, 60)
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


def bubble(lines, bg, tail_x=0.5, pad=(56, 30), gap=6):
    """Speech bubble holding one or more (text, size, colour) lines; tail at the bottom pointing down."""
    fs = [font(s) for _, s, _ in lines]
    boxes = [f.getbbox(t) for f, (t, _, _) in zip(fs, lines)]
    tw = max(b[2] - b[0] for b in boxes)
    th = sum(b[3] - b[1] for b in boxes) + gap * (len(lines) - 1)
    w, h, tail = tw + 2 * pad[0], th + 2 * pad[1], 46
    im = Image.new("RGBA", (w + 20, h + tail + 20))
    d = ImageDraw.Draw(im)
    tx = 10 + w * tail_x
    d.polygon([(tx - 34, 10 + h - 8), (tx + 6, 10 + h + tail), (tx + 30, 10 + h - 8)], fill=bg, outline=PLUM)
    d.rounded_rectangle((10, 10, 10 + w, 10 + h), radius=48, fill=bg, outline=PLUM, width=7)
    d.polygon([(tx - 27, 10 + h - 12), (tx + 5, 10 + h + tail - 10), (tx + 23, 10 + h - 12)], fill=bg)
    # redraw the tail outline sides only (the top is hidden inside the bubble)
    d.line([(tx - 31, 10 + h), (tx + 6, 10 + h + tail)], fill=PLUM, width=7)
    d.line([(tx + 6, 10 + h + tail), (tx + 28, 10 + h)], fill=PLUM, width=7)
    y = 10 + pad[1]
    for f, (t, _, col), b in zip(fs, lines, boxes):
        d.text((10 + (w - (b[2] - b[0])) / 2 - b[0], y - b[1]), t, font=f, fill=col)
        y += b[3] - b[1] + gap
    return im


def pill(text, size, bg, fg, icon=None, rot=0, pad=(34, 16)):
    f = font(size)
    l, t, r, b = f.getbbox(text)
    tw, th = r - l, b - t
    ic = emoji(icon, int(size * 1.05)) if icon else None
    iw = ic.width + 14 if ic else 0
    w, h = tw + iw + pad[0] * 2, th + pad[1] * 2
    im = Image.new("RGBA", (w + 12, h + 12))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, w + 6, h + 6), radius=h // 2, fill=bg, outline=WHITE, width=6)
    x = 6 + pad[0]
    if ic:
        im.alpha_composite(ic, (x, 6 + (h - ic.height) // 2))
        x += iw
    d.text((x - l, 6 + pad[1] - t), text, font=f, fill=fg)
    return im.rotate(rot, resample=Image.BICUBIC, expand=True)


def bloom(size, petal, centre=HONEY, rot=0):
    """Six-petal flower (the video's motif)."""
    im = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(im)
    c, pr, rr = size / 2, size * 0.22, size * 0.26
    for i in range(6):
        a = i * math.pi / 3 + math.radians(rot)
        x, y = c + rr * math.cos(a), c + rr * math.sin(a)
        d.ellipse((x - pr, y - pr, x + pr, y + pr), fill=petal, outline=WHITE, width=max(2, size // 30))
    d.ellipse((c - size * 0.16, c - size * 0.16, c + size * 0.16, c + size * 0.16), fill=centre)
    return im


def main():
    # background: diagonal lilac / pink split with scattered honey dots
    base = Image.new("RGBA", (W, H), (*LILAC, 255))
    split = Image.new("RGBA", (W, H))
    ImageDraw.Draw(split).polygon([(0, H * 0.62), (W, H * 0.30), (W, H), (0, H)], fill=(*PINK, 255))
    base.alpha_composite(split)
    rnd = random.Random(7)
    dots = Image.new("RGBA", (W, H))
    dd = ImageDraw.Draw(dots)
    for _ in range(70):
        x, y, r = rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(5, 11)
        dd.ellipse((x - r, y - r, x + r, y + r), fill=(*CREAM, 150))
    base.alpha_composite(dots)

    # photo in a rounded cream frame with a dashed "stitch" line
    img = Image.open(SRC).convert("RGB").resize((W, 1920), Image.LANCZOS).crop(PHOTO_BOX)
    img = ImageEnhance.Color(img).enhance(1.12)
    img = ImageEnhance.Contrast(img).enhance(1.05)
    img = ImageEnhance.Brightness(img).enhance(1.05)
    pw = 900
    ph = int(pw * img.height / img.width)
    img = img.resize((pw, ph), Image.LANCZOS)
    m = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, pw - 1, ph - 1), radius=56, fill=255)
    bw = 26
    frame = Image.new("RGBA", (pw + 2 * bw, ph + 2 * bw))
    fd = ImageDraw.Draw(frame)
    fd.rounded_rectangle((0, 0, frame.width - 1, frame.height - 1), radius=56 + bw, fill=(*CREAM, 255))
    frame.paste(img, (bw, bw), m)
    # stitches just inside the cream border
    s = 12
    for x in range(bw + 60, frame.width - bw - 60, 34):
        fd.rounded_rectangle((x, s - 3, x + 18, s + 3), radius=3, fill=LILAC_D)
        fd.rounded_rectangle((x, frame.height - s - 3, x + 18, frame.height - s + 3), radius=3, fill=LILAC_D)
    for y in range(bw + 60, frame.height - bw - 60, 34):
        fd.rounded_rectangle((s - 3, y, s + 3, y + 18), radius=3, fill=LILAC_D)
        fd.rounded_rectangle((frame.width - s - 3, y, frame.width - s + 3, y + 18), radius=3, fill=LILAC_D)
    paste_center(base, shadow(frame, offset=(0, 16), blur=22, alpha=120), W / 2, 845)

    # title in a speech bubble, tail pointing at the pillows
    title = bubble([("BANTAL BUNGA", 84, PLUM), ("SENYUM!", 112, ROSE)], WHITE, tail_x=0.36)
    paste_center(base, shadow(title, offset=(0, 12)), W / 2, 205)
    paste_center(base, shadow(emoji("😊", 110)), 965, 330)
    paste_center(base, shadow(emoji("🌸", 96)), 150, 330)

    # what she says, kept clear of the three faces: sky (top-left of photo) and the grass below the pillows
    paste_center(base, shadow(pill("PALING BANYAK TERJUAL", 42, HONEY, PLUM, "🏆", rot=-3)), 400, 455)
    paste_center(base, shadow(pill("RAMAI REPEAT ORDER", 44, LILAC_D, WHITE, "🔁", rot=2)), 400, 1112)

    # row of little flowers along the bottom (motif)
    cols = [LILAC, CREAM, PINK]
    for i, x in enumerate(range(70, W, 135)):
        paste_center(base, shadow(bloom(92 if i % 2 else 76, cols[i % 3], rot=i * 17), offset=(0, 5), blur=8),
                     x, 1440 if i % 2 else 1470)
    base.convert("RGB").save(OUT, quality=95)


if __name__ == "__main__":
    main()
