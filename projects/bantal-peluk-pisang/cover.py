#!/usr/bin/env python3
"""TikTok cover (1080x1536) for the banana hug pillow (bantal peluk pisang) video.

Refresh v6: comic-book look - banana-yellow halftone backdrop with speed lines, the photo in a tilted comic panel
(thick choco border + hard offset shadow), a jagged "GEBUNYA!" burst and a ticket stub for the sizes (matching
the ticket labels in the video), instead of a polaroid, arch window, rind frame or sunburst sticker.

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

BANANA = (255, 225, 53)
BANANA_D = (242, 194, 0)
CHOCO = (58, 36, 20)
BROWN = (107, 62, 30)
BLUSH = (255, 143, 171)
BERRY = (214, 63, 110)
CREAM = (255, 246, 216)
LEAF = (123, 192, 67)
WHITE = (255, 255, 255)


def font(size):
    return ImageFont.truetype(FONT, size)


def emoji(ch, size):
    f = ImageFont.truetype(EMOJI, 109)
    im = Image.new("RGBA", (160, 160))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)


def hard_shadow(layer, offset=(16, 18), col=CHOCO):
    """Comic-style flat drop shadow (no blur)."""
    out = Image.new("RGBA", (layer.width + offset[0], layer.height + offset[1]))
    sh = Image.new("RGBA", layer.size, (*col, 255))
    sh.putalpha(layer.split()[-1])
    out.alpha_composite(sh, offset)
    out.alpha_composite(layer)
    return out


def extruded_text(text, size, fill, depth=10, rot=0, stroke=CHOCO, ext=CHOCO):
    """Chunky comic title: thick stroke + a stepped 3D extrusion."""
    f = font(size)
    sw = max(6, size // 11)
    l, t, r, b = f.getbbox(text, stroke_width=sw)
    im = Image.new("RGBA", (r - l + 40 + depth, b - t + 40 + depth))
    d = ImageDraw.Draw(im)
    for k in range(depth, 0, -1):
        d.text((20 - l + k, 20 - t + k), text, font=f, fill=ext, stroke_width=sw, stroke_fill=ext)
    d.text((20 - l, 20 - t), text, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)
    return im.rotate(rot, resample=Image.BICUBIC, expand=True)


def burst(lines, r_out, fill, fg, spikes=14, rot=-8):
    """Jagged comic explosion with text."""
    size = int(r_out * 2 + 40)
    im = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(im)
    c = size / 2
    pts_o, pts_i = [], []
    for k in range(spikes * 2):
        a = math.pi * k / spikes
        rr = r_out if k % 2 == 0 else r_out * (0.70 + 0.08 * ((k // 2) % 3) / 2)
        pts_o.append((c + (rr + 12) * math.cos(a), c + (rr + 12) * math.sin(a)))
        pts_i.append((c + rr * math.cos(a), c + rr * math.sin(a)))
    d.polygon(pts_o, fill=CHOCO)
    d.polygon(pts_i, fill=fill)
    n = len(lines)
    for k, (txt, fs) in enumerate(lines):
        f = font(fs)
        l, t, r, b = f.getbbox(txt, stroke_width=5)
        y = c + (k - (n - 1) / 2) * fs * 1.02
        d.text((c - (r - l) / 2 - l, y - (b - t) / 2 - t), txt, font=f, fill=fg, stroke_width=5, stroke_fill=CHOCO)
    return im.rotate(rot, resample=Image.BICUBIC, expand=True)


def ticket(text, size, bg, fg, hi=None, icon=None, pad=(34, 16)):
    """Ticket stub (notched ends + dashed tear line), same as the video labels. *word* = highlight."""
    f = font(size)
    plain = text.replace("*", "")
    l, t, r, b = f.getbbox(plain)
    tw, th = r - l, b - t
    ic = emoji(icon, int(size * 1.1)) if icon else None
    iw = ic.width + 16 if ic else 0
    h = th + pad[1] * 2
    stub = int(h * 0.62)
    w = tw + iw + pad[0] * 2 + stub
    im = Image.new("RGBA", (w + 8, h + 8))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((4, 4, w + 4, h + 4), radius=12, fill=bg, outline=CHOCO, width=5)
    nr = h * 0.2
    for cx in (4, w + 4):
        d.ellipse((cx - nr, 4 + h / 2 - nr, cx + nr, 4 + h / 2 + nr), fill=(0, 0, 0, 0), outline=CHOCO, width=5)
        d.ellipse((cx - nr + 5, 4 + h / 2 - nr + 5, cx + nr - 5, 4 + h / 2 + nr - 5), fill=(0, 0, 0, 0))
    # clear the half-discs outside the ticket body so the notches read as cut-outs
    mask = Image.new("L", im.size, 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((4 - 3, 4 - 3, w + 4 + 3, h + 4 + 3), radius=14, fill=255)
    for cx in (4, w + 4):
        md.ellipse((cx - nr + 5, 4 + h / 2 - nr + 5, cx + nr - 5, 4 + h / 2 + nr - 5), fill=0)
    im.putalpha(Image.composite(im.split()[-1], Image.new("L", im.size, 0), mask))
    d = ImageDraw.Draw(im)
    y = 14
    while y + 10 <= h - 8:
        d.rectangle((4 + stub, 4 + y, 4 + stub + 4, 4 + y + 10), fill=(*BROWN, 170))
        y += 18
    x = 4 + stub + pad[0]
    for k, part in enumerate(text.split("*")):
        if not part:
            continue
        col = (hi or fg) if k % 2 else fg
        d.text((x - l, 4 + pad[1] - t), part, font=f, fill=col)
        x += f.getlength(part)
    if ic:
        im.alpha_composite(ic, (int(x + 16), 4 + (h - ic.height) // 2))
    return im


def paste_center(base, layer, cx, cy):
    base.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


def main():
    img = Image.open(SRC).convert("RGB").resize((W, SRC_H), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(1.12)
    img = ImageEnhance.Contrast(img).enhance(1.06)
    img = ImageEnhance.Brightness(img).enhance(1.04)

    # banana backdrop: speed lines from the panel centre + halftone dots growing toward the bottom right
    base = Image.new("RGBA", (W, H), (*BANANA, 255))
    d = ImageDraw.Draw(base)
    cx0, cy0 = W / 2, 800
    for k in range(36):
        a0 = 2 * math.pi * k / 36
        a1 = a0 + 2 * math.pi / 36 * 0.45
        R = 1600
        d.polygon([(cx0, cy0), (cx0 + R * math.cos(a0), cy0 + R * math.sin(a0)),
                   (cx0 + R * math.cos(a1), cy0 + R * math.sin(a1))], fill=(*CREAM, 255))
    dots = Image.new("RGBA", (W, H))
    dd = ImageDraw.Draw(dots)
    for j, y in enumerate(range(0, H + 40, 34)):
        for x in range(17 if j % 2 else 0, W + 40, 34):
            r = 2 + 9 * min(1, max(0, (x / W * 0.5 + y / H * 0.7) - 0.25))
            dd.ellipse((x - r, y - r, x + r, y + r), fill=(*BANANA_D, 210))
    base.alpha_composite(dots)

    # photo in a tilted comic panel: thick choco border, white inner line, hard shadow
    pw, ph = 780, 1000
    photo = img.crop((40, 290, 1040, 1572)).resize((pw, ph), Image.LANCZOS).convert("RGBA")
    panel = Image.new("RGBA", (pw + 44, ph + 44), (*CHOCO, 255))
    inner = Image.new("RGBA", (pw + 16, ph + 16), (*WHITE, 255))
    inner.alpha_composite(photo, (8, 8))
    panel.alpha_composite(inner, (14, 14))
    panel = hard_shadow(panel.rotate(-3, resample=Image.BICUBIC, expand=True), offset=(18, 20))
    paste_center(base, panel, W / 2 + 10, 830)

    # title (inside the 3:4 crop)
    paste_center(base, extruded_text("BANTAL PELUK", 92, WHITE, depth=8, rot=3), W / 2 - 40, 125)
    paste_center(base, extruded_text("PISANG!", 150, BANANA, depth=12, rot=3, ext=BERRY), W / 2 + 40, 250)
    paste_center(base, hard_shadow(emoji("🍌", 120), offset=(8, 8)), 930, 150)

    # burst + size ticket
    paste_center(base, burst([("GEBU", 64), ("NYA!", 70)], 150, BERRY, WHITE), 885, 1180)
    paste_center(base, hard_shadow(ticket("ADA *3 SAIZ*", 54, CREAM, CHOCO, hi=BERRY, icon="📏"), (10, 12)),
                 330, 1330)
    paste_center(base, hard_shadow(ticket("*70* • *50* • *35* CM", 50, CHOCO, WHITE, hi=BANANA), (10, 12)),
                 470, 1438)
    paste_center(base, hard_shadow(emoji("💥", 92), offset=(6, 6)), 120, 560)
    base.convert("RGB").save(OUT, quality=95)


if __name__ == "__main__":
    main()
