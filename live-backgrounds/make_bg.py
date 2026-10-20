"""TikTok LIVE background images (1080x1920), three themes from the shop's plush videos.

Usage: python3 make_bg.py <out_dir>

Layout keeps the LIVE UI clear: text sits in the upper band (y 240-640), the middle stays open
for the host, and only decoration goes where the comments (bottom-left), the gift/share column
(right) and the top bar sit.
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 2                                    # supersample
W, H = 1080 * S, 1920 * S
FONT = "/root/.fonts/Fredoka-Bold.ttf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"


def hexc(h, a=255):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def gradient(top, bottom):
    im = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(im)
    t, b = hexc(top), hexc(bottom)
    for y in range(H):
        k = y / (H - 1)
        d.line([(0, y), (W, y)], fill=tuple(int(t[i] + (b[i] - t[i]) * k) for i in range(3)) + (255,))
    return im


def font(px):
    return ImageFont.truetype(FONT, px * S)


def emoji(ch, px):
    f = ImageFont.truetype(EMOJI, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), ch, font=f, embedded_color=True, anchor="mm")
    im = im.crop(im.getbbox())
    k = px * S / max(im.size)
    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)


def shadow(layer, off=10, blur=14, alpha=70):
    a = layer.split()[3].point(lambda v: v * alpha // 255)
    sh = Image.new("RGBA", layer.size, (60, 30, 60, 0))
    sh.putalpha(a)
    sh = sh.filter(ImageFilter.GaussianBlur(blur * S))
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, off * S))
    out.alpha_composite(layer)
    return out


def text_outlined(d, xy, txt, px, fill, stroke, sw=10, anchor="mm"):
    d.text(xy, txt, font=font(px), fill=hexc(fill), stroke_width=sw * S, stroke_fill=hexc(stroke), anchor=anchor)


def pill(base, cx, cy, txt, px, fg, bg, border="#FFFFFF", pad=(44, 22), emo=None):
    f = font(px)
    tw = f.getlength(txt)
    ew = (px * 1.25 * S + 14 * S) if emo else 0
    w, h = tw + ew + pad[0] * 2 * S, px * S + pad[1] * 2 * S
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    box = [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2]
    d.rounded_rectangle(box, radius=h / 2, fill=hexc(bg), outline=hexc(border), width=7 * S)
    x0 = box[0] + pad[0] * S
    if emo:
        e = emoji(emo, int(px * 1.25))
        lay.alpha_composite(e, (int(x0), int(cy - e.height / 2)))
        x0 += ew
    d.text((x0, cy), txt, font=f, fill=hexc(fg), anchor="lm")
    base.alpha_composite(shadow(lay, off=8, blur=10, alpha=60))


def face(d, cx, cy, r, ink="#4A2C2A", blush="#FF8FAB"):
    e = r * 0.42
    for sx in (-1, 1):
        d.ellipse([cx + sx * e - r * 0.09, cy - r * 0.12, cx + sx * e + r * 0.09, cy + r * 0.06], fill=hexc(ink))
        d.ellipse([cx + sx * (e + r * 0.16) - r * 0.13, cy + r * 0.12, cx + sx * (e + r * 0.16) + r * 0.13,
                   cy + r * 0.26], fill=hexc(blush, 170))
    d.arc([cx - r * 0.16, cy - r * 0.02, cx + r * 0.16, cy + r * 0.24], 15, 165, fill=hexc(ink), width=int(r * 0.06))


def flower(base, cx, cy, r, petal, center, n=6, rot=0, with_face=True, petal_line=None):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i in range(n):
        a = math.radians(rot + 360 * i / n)
        px, py = cx + math.cos(a) * r * 0.62, cy + math.sin(a) * r * 0.62
        pr = r * 0.46
        d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=hexc(petal), outline=hexc(petal_line or petal),
                  width=int(r * 0.05))
    cr = r * 0.42
    d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=hexc(center))
    if with_face:
        face(d, cx, cy, cr)
    base.alpha_composite(shadow(lay, off=10, blur=12, alpha=55))


def scallop_band(base, y, color, r=60, down=True):
    d = ImageDraw.Draw(base)
    r *= S
    d.rectangle([0, 0, W, y], fill=hexc(color)) if down else d.rectangle([0, y, W, H], fill=hexc(color))
    x = -r
    while x < W + r:
        d.ellipse([x, y - r, x + 2 * r, y + r], fill=hexc(color))
        x += 2 * r


def dots(base, colors, n, seed, rmin=6, rmax=16, avoid=None):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(base)
    for _ in range(n):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        if avoid and avoid[0] < x < avoid[2] and avoid[1] < y < avoid[3]:
            continue
        r = rnd.uniform(rmin, rmax) * S
        d.ellipse([x - r, y - r, x + r, y + r], fill=hexc(rnd.choice(colors), 150))


def sparkle(d, cx, cy, r, color):
    pts = []
    for i in range(8):
        a = math.radians(45 * i - 90)
        rr = r if i % 2 == 0 else r * 0.28
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    d.polygon(pts, fill=hexc(color))


def cloud(base, cx, cy, s, color="#FFFFFF", alpha=255, with_face=False):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for dx, dy, rr in ((-0.55, 0.1, 0.42), (-0.15, -0.18, 0.55), (0.35, -0.05, 0.48), (0.7, 0.15, 0.34),
                       (0.05, 0.2, 0.45)):
        d.ellipse([cx + (dx - rr) * s, cy + (dy - rr) * s, cx + (dx + rr) * s, cy + (dy + rr) * s],
                  fill=hexc(color, alpha))
    if with_face:
        face(d, cx + 0.05 * s, cy + 0.02 * s, s * 0.45)
    base.alpha_composite(shadow(lay, off=8, blur=16, alpha=40))


def title_block(base, lines, sub, chip, col, stroke, chip_fg, chip_bg, y0=330):
    d = ImageDraw.Draw(base)
    y = y0 * S
    for txt, px, fill in lines:
        text_outlined(d, (W / 2, y), txt, px, fill, stroke, sw=12)
        y += int(px * 1.08) * S
    if sub:
        text_outlined(d, (W / 2, y + 6 * S), sub, 40, "#FFFFFF", col, sw=8)
        y += 72 * S
    if chip:
        pill(base, W / 2, y + 46 * S, chip, 40, chip_fg, chip_bg, emo="🛒")


# ------------------------------------------------------------------ theme 1: taman bunga pastel
def taman_bunga():
    im = gradient("#F6E9FF", "#FFE4EE")
    dots(im, ["#E6D2FF", "#FFD1E1", "#FFF1B8"], 140, 1, avoid=(260 * S, 700 * S, 820 * S, 1300 * S))
    scallop_band(im, 170 * S, "#C9B2F0", r=64)
    d = ImageDraw.Draw(im)
    for x in range(64 * S, W, 128 * S):
        d.ellipse([x - 9 * S, 120 * S - 9 * S, x + 9 * S, 120 * S + 9 * S], fill=hexc("#FFFFFF", 200))
    # big flowers around the edges, cut off by the frame
    flower(im, -40 * S, 1500 * S, 230 * S, "#FFFFFF", "#F4B740", rot=10, petal_line="#F1E4F7")
    flower(im, 1110 * S, 1260 * S, 210 * S, "#D9C3F7", "#FFF6E6", rot=30)
    flower(im, 1000 * S, 1800 * S, 260 * S, "#FFC4D6", "#FFF6E6", rot=0)
    flower(im, 180 * S, 1880 * S, 190 * S, "#FFE9A8", "#FFFFFF", rot=20)
    flower(im, 80 * S, 760 * S, 120 * S, "#FFC4D6", "#FFF6E6", rot=15)
    flower(im, 1010 * S, 700 * S, 110 * S, "#FFFFFF", "#F4B740", rot=5, petal_line="#F1E4F7")
    for (x, y, r, c) in ((190, 610, 26, "#FFFFFF"), (900, 560, 22, "#FFF1B8"), (960, 980, 18, "#FFFFFF"),
                         (120, 1100, 20, "#FFF1B8"), (540, 1040, 14, "#FFFFFF")):
        sparkle(d, x * S, y * S, r * S, c)
    title_block(im, [("LIVE", 92, "#FFFFFF"), ("BANTAL BUNGA", 104, "#FFE27A")],
                "gebu • lembut • sedap peluk", "TEKAN BEG KUNING", "#9D7BD8", "#7E5BC2", "#5B3A99", "#FFE27A",
                y0=300)
    return im


# ------------------------------------------------------------------ theme 2: kebun buah comel
def watermelon(base, cx, cy, r):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=hexc("#3E9B4F"))
    d.ellipse([cx - r * 0.9, cy - r * 0.9, cx + r * 0.9, cy + r * 0.9], fill=hexc("#E9F5D7"))
    d.ellipse([cx - r * 0.8, cy - r * 0.8, cx + r * 0.8, cy + r * 0.8], fill=hexc("#FF6F7D"))
    rnd = random.Random(int(cx))
    for i in range(10):
        a = math.radians(i * 36 + rnd.uniform(-8, 8))
        sx, sy = cx + math.cos(a) * r * 0.58, cy + math.sin(a) * r * 0.58
        d.ellipse([sx - r * 0.05, sy - r * 0.08, sx + r * 0.05, sy + r * 0.08], fill=hexc("#3A2A2A"))
    face(d, cx, cy, r * 0.5, blush="#FFB3C1")
    base.alpha_composite(shadow(lay))


def avocado(base, cx, cy, r):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.ellipse([cx - r * 0.62, cy - r * 1.05, cx + r * 0.62, cy + r * 0.05], fill=hexc("#5C8A2E"))
    d.ellipse([cx - r * 0.85, cy - r * 0.55, cx + r * 0.85, cy + r * 0.9], fill=hexc("#5C8A2E"))
    d.ellipse([cx - r * 0.52, cy - r * 0.9, cx + r * 0.52, cy - r * 0.05], fill=hexc("#D9EE8E"))
    d.ellipse([cx - r * 0.74, cy - r * 0.45, cx + r * 0.74, cy + r * 0.8], fill=hexc("#D9EE8E"))
    d.ellipse([cx - r * 0.3, cy + r * 0.1, cx + r * 0.3, cy + r * 0.66], fill=hexc("#8A5A3B"))
    face(d, cx, cy - r * 0.28, r * 0.45)
    base.alpha_composite(shadow(lay))


def carrot(base, cx, cy, r, rot=0):
    lay = Image.new("RGBA", (int(r * 3), int(r * 3)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    c = r * 1.5
    for dx in (-0.22, 0, 0.22):
        d.ellipse([c + dx * r - r * 0.13, c - r * 1.25, c + dx * r + r * 0.13, c - r * 0.55], fill=hexc("#5DBB63"))
    d.polygon([(c - r * 0.45, c - r * 0.6), (c + r * 0.45, c - r * 0.6), (c, c + r * 1.25)], fill=hexc("#FF8A3D"))
    d.ellipse([c - r * 0.45, c - r * 0.85, c + r * 0.45, c - r * 0.35], fill=hexc("#FF8A3D"))
    for k in (-0.2, 0.15, 0.5):
        d.line([(c - r * 0.25, c + k * r), (c - r * 0.08, c + k * r)], fill=hexc("#E06A22"), width=int(r * 0.05))
    face(d, c, c - r * 0.45, r * 0.4)
    lay = lay.rotate(rot, resample=Image.BICUBIC, expand=False)
    full = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    full.alpha_composite(lay, (int(cx - c), int(cy - c)))
    base.alpha_composite(shadow(full))


def banana(base, cx, cy, r, rot=0):
    lay = Image.new("RGBA", (int(r * 3), int(r * 3)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    c = r * 1.5
    d.pieslice([c - r * 1.2, c - r * 1.6, c + r * 1.2, c + r * 0.8], 20, 160, fill=hexc("#FFD93B"))
    d.pieslice([c - r * 1.0, c - r * 1.75, c + r * 1.0, c + r * 0.25], 15, 165, fill=(0, 0, 0, 0))
    d.ellipse([c + r * 1.0, c - r * 0.2, c + r * 1.2, c + r * 0.0], fill=hexc("#6B4A2B"))
    d.ellipse([c - r * 1.2, c - r * 0.2, c - r * 1.0, c + r * 0.0], fill=hexc("#6B4A2B"))
    face(d, c, c + r * 0.45, r * 0.35)
    lay = lay.rotate(rot, resample=Image.BICUBIC, expand=False)
    full = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    full.alpha_composite(lay, (int(cx - c), int(cy - c)))
    base.alpha_composite(shadow(full))


def kebun_buah():
    im = gradient("#E7F8EC", "#FFF6DA")
    d = ImageDraw.Draw(im)
    step = 90 * S                         # soft gingham
    for x in range(0, W, step * 2):
        d.rectangle([x, 0, x + step, H], fill=hexc("#CFEFD8", 90))
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    for y in range(0, H, step * 2):
        od.rectangle([0, y, W, y + step], fill=hexc("#CFEFD8", 90))
    im.alpha_composite(over)
    scallop_band(im, 170 * S, "#FF7A8A", r=60)
    d = ImageDraw.Draw(im)
    for x in range(60 * S, W, 120 * S):
        d.ellipse([x - 7 * S, 110 * S - 11 * S, x + 7 * S, 110 * S + 11 * S], fill=hexc("#3A2A2A"))
    watermelon(im, 120 * S, 1560 * S, 210 * S)
    avocado(im, 990 * S, 1250 * S, 170 * S)
    carrot(im, 1000 * S, 1760 * S, 160 * S, rot=-25)
    banana(im, 330 * S, 1850 * S, 150 * S, rot=10)
    watermelon(im, 90 * S, 760 * S, 90 * S)
    avocado(im, 1010 * S, 720 * S, 80 * S)
    for (x, y, r, c) in ((200, 620, 24, "#FFFFFF"), (880, 600, 22, "#FFD93B"), (140, 1080, 18, "#FFFFFF"),
                         (950, 980, 20, "#FFFFFF")):
        sparkle(d, x * S, y * S, r * S, c)
    title_block(im, [("KEBUN BANTAL", 96, "#FFFFFF"), ("BUAH GEBU!", 112, "#FFD93B")],
                "tembikai • avocado • pisang • lobak", "TEKAN BEG KUNING", "#2E8B57", "#2E7D4F", "#2E5E3A",
                "#FFE27A", y0=300)
    return im


# ------------------------------------------------------------------ theme 3: awan mimpi (teman tidur)
def awan_mimpi():
    im = gradient("#BFE3FF", "#E9DDFF")
    d = ImageDraw.Draw(im)
    rnd = random.Random(7)
    for _ in range(70):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H * 0.55)
        if 200 * S < x < 880 * S and 230 * S < y < 700 * S:
            continue
        sparkle(d, x, y, rnd.uniform(8, 18) * S, rnd.choice(["#FFFFFF", "#FFF4B0"]))
    # moon
    mx, my, mr = 900 * S, 330 * S, 110 * S
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=hexc("#FFF2A8"))
    d.ellipse([mx - mr * 0.55, my - mr * 1.05, mx + mr * 1.35, my + mr * 0.75], fill=(0, 0, 0, 0))
    moon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(moon)
    md.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=hexc("#FFF2A8"))
    md.ellipse([mx - mr * 0.35, my - mr * 1.0, mx + mr * 1.45, my + mr * 0.8], fill=(0, 0, 0, 0))
    cut = Image.new("L", (W, H), 0)
    ImageDraw.Draw(cut).ellipse([mx - mr * 0.35, my - mr * 1.0, mx + mr * 1.45, my + mr * 0.8], fill=255)
    a = moon.split()[3]
    a.paste(0, mask=cut)
    moon.putalpha(a)
    bg_patch = gradient("#BFE3FF", "#E9DDFF")
    im.paste(bg_patch.crop((mx - mr * 2, my - mr * 2, mx + mr * 2, my + mr * 2)), (mx - mr * 2, my - mr * 2))
    im.alpha_composite(shadow(moon, off=0, blur=24, alpha=120))
    # clouds framing the bottom and sides
    cloud(im, 120 * S, 1180 * S, 260 * S, alpha=235)
    cloud(im, 980 * S, 1050 * S, 230 * S, alpha=235)
    cloud(im, 260 * S, 1760 * S, 420 * S, with_face=True)
    cloud(im, 900 * S, 1820 * S, 380 * S)
    cloud(im, 560 * S, 1960 * S, 420 * S)
    cloud(im, 150 * S, 560 * S, 150 * S, alpha=210)
    d = ImageDraw.Draw(im)
    for (x, y, r) in ((960, 640, 22), (90, 900, 18), (1010, 1400, 20)):
        sparkle(d, x * S, y * S, r * S, "#FFFFFF")
    title_block(im, [("TEMAN TIDUR", 100, "#FFFFFF"), ("PALING GEBU", 108, "#FFF2A8")],
                "jom peluk sampai lena 💤".replace(" 💤", ""), "TEKAN BEG KUNING", "#7A8FE0", "#5B6FCB",
                "#3E4A99", "#FFF2A8", y0=330)
    return im


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    for name, fn in (("live_bg_1_taman_bunga", taman_bunga), ("live_bg_2_kebun_buah", kebun_buah),
                     ("live_bg_3_awan_mimpi", awan_mimpi)):
        im = fn().resize((1080, 1920), Image.LANCZOS).convert("RGB")
        im.save(os.path.join(out, name + ".png"))
        print("wrote", name)


if __name__ == "__main__":
    main()
