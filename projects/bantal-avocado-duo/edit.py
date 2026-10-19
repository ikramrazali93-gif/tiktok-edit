#!/usr/bin/env python3
"""Edit for the avocado plush pillows (bantal avocado: "montel" 70cm + "panjang" 90cm) TikTok video, IMG_2935.

All overlays stay inside the TikTok safe zone (SAFE_* below): nothing under the
right-hand profile/like/comment/share column, the bottom caption area or the top tabs.

Needs the Fredoka Bold font (fonts/Fredoka-Bold.ttf, SIL OFL) installed, e.g. in ~/.fonts.

Usage: python3 edit.py <proxy.mp4> <transcript.json> <sfx_dir> <out_dir> [--final]
  preview: 720x1280 proxy -> preview.mp4;  --final: 1080x1920 master -> final.mp4
  --audio-only: re-mix voice + SFX onto the existing render -> *_voice.mp4

All times in BLOCKS are source times of the original clip (same timeline as
the proxy). The script builds:
  base.mp4     - cut/zoomed video + cleaned voice + SFX
  overlay.ass  - captions, labels, flashes, progress bar
  preview.mp4  - base + ASS + colour emoji stickers (rendered with Pillow)
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

PROXY, TRANSCRIPT, SFX, OUT = sys.argv[1:5]
W, H, FPS = 720, 1280, 30          # layout space for ASS / sticker coordinates
FINAL = "--final" in sys.argv       # --final: 1080x1920 from a full-res master
K = 1.5 if FINAL else 1.0
RW, RH = int(W * K), int(H * K)     # render size
# TikTok UI safe zone, in 720x1280 layout px (scaled x1.5 for 1080x1920):
# right column (profile, like, comment, save, share) ~ last 100px, bottom
# username + caption ~ 270px, top tabs ~ 110px.
SAFE_L, SAFE_R, SAFE_T, SAFE_B = 40, 110, 110, 290
CX = (SAFE_L + W - SAFE_R) // 2          # horizontal centre of the safe area
SAFE_W = W - SAFE_L - SAFE_R              # usable width
FONT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Fredoka-Bold.ttf")
ASS_PER_PIL = 0.82                        # libass width / Pillow width for Fredoka (measured)
VOICE_LUFS = -11.5                  # v1 was -15; SFX levels are absolute and stay unchanged
CAP_FS = 56                        # caption size (chunks that would wrap are shrunk to one line)


# ---------------------------------------------------------------- EDL
# One clip (IMG_2935), outdoors on grass: she holds two avocado plush pillows, the long one ("panjang", 90cm) and
# the chubby one ("montel", 70cm).
# v: list of (src_in, src_out, speed, zoom)
# a: 'same' (follow v at speed 1), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK (J-cut, moved from 8.0s): "Korang mana satu? Korang montel ke panjang? Kalau montel ambil montel." over
    # the chubby avocado being pushed up to the camera until its face fills the frame
    dict(name="hook", a=[(8.02, 11.68)], v=[(38.20, 41.86, 1, 1.0)]),
    # "Peminat warna hijau. Avocado hijau dia cantik betul. | Ada dua bentuk. Nak yang montel, nak yang panjang."
    dict(name="intro", a="same", v=[(0.00, 3.90, 1, 1.0), (3.90, 7.68, 1, 1.08)]),
    # "Okey ini yang panjang 90cm. | Yang ini yang montel 70cm."  (the pause after "90cm" cut)
    dict(name="saiz", a="same", v=[(12.08, 14.45, 1, 1.04), (14.85, 17.20, 1, 1.10)]),
    # "Gebu-gebas, sedap peluk."  (she pushes the chubby one at the camera)
    dict(name="gebu", a="same", v=[(17.28, 19.76, 1, 1.0)]),
    # "Buat hadiah pun sangat sesuai kan. | Siapa yang ada bestfriend, birthday bestfriend, birthday anak ke, |
    #  birthday isteri ke, birthday suami ke."  (the slow 3rd "birthday" runs 27.4-28.3; last part over the face)
    dict(name="hadiah", a=[(19.84, 22.47), (23.05, 31.04)],
         v=[(19.84, 22.47, 1, 1.0), (23.05, 27.22, 1, 1.06), (41.90, 45.72, 1, 1.0)]),
    # "Material dia jenis material kain velvet, material tahan lasak, tak berbulu, boleh basuh." + "Ada zip juga."
    # (from 53.1s) over the back-of-pillow fabric close-ups. The unclear "beli-beli ni ... avocado lembut" and the
    # price line "harga dia sangat-sangat mesra poket" before it are cut (no price talk).
    dict(name="material", a=[(41.36, 46.38), (53.12, 54.18)], v=[(50.30, 56.38, 1, 1.0)]),
    # "Tengok dekat beg kuning tau."
    dict(name="cta", a="same", v=[(47.70, 49.05, 1, 1.0)]),
    # both avocados, wide and slowed, under the end card
    dict(name="end", a=None, v=[(57.20, 59.60, 0.8, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "Perminat": "Peminat", "bag": "beg", "istri": "isteri"}
# hand-checked words (full-file pass + per-chunk re-transcription)
def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


OVERRIDE = {
    8.02: _w(("Korang", 8.10, 8.30), ("mana", 8.30, 8.48), ("satu?", 8.48, 8.84), ("Korang", 8.90, 9.18),
             ("montel", 9.18, 9.50), ("ke", 9.50, 9.62), ("panjang?", 9.62, 10.14), ("Kalau", 10.24, 10.44),
             ("montel", 10.44, 10.72), ("ambil", 10.72, 10.92), ("montel.", 10.92, 11.60)),
}
DROP = []
HILITE = {"HIJAU", "AVOCADO", "MONTEL", "PANJANG", "DUA", "BENTUK", "90CM", "70CM", "GEBU-GEBAS", "PELUK",
          "HADIAH", "BIRTHDAY", "BESTFRIEND", "VELVET", "LASAK", "BASUH", "ZIP", "BEG", "KUNING"}





def build_timeline():
    vclips, aclips, t = [], [], 0.0
    src_map = []  # (src_in, src_out, tl_start) for audio that plays at 1x
    for b in BLOCKS:
        b["t0"] = t
        dur = 0.0
        for (s, e, sp, z) in b["v"]:
            d = (e - s) / sp
            vclips.append(dict(s=s, e=e, sp=sp, z=z, t=t + dur, d=d))
            dur += d
        if b["a"] == "same":
            al = [(s, e) for (s, e, sp, z) in b["v"]]
        else:
            al = b["a"]
        if al is None:
            aclips.append(dict(silence=dur, t=t))
        else:
            at = t
            for (s, e) in al:
                aclips.append(dict(s=s, e=e, t=at))
                src_map.append((s, e, at))
                at += e - s
            assert abs(at - t - dur) < 0.02, (b["name"], at - t, dur)
        b["dur"] = dur
        t += dur
    return vclips, aclips, src_map, t


VCLIPS, ACLIPS, SRC_MAP, TOTAL = build_timeline()
BT = {b["name"]: b for b in BLOCKS}


def tl(src):
    """Map a source time (inside a kept 1x audio clip) to the timeline."""
    for s, e, at in SRC_MAP:
        if s - 0.05 <= src <= e + 0.05:
            return at + (min(max(src, s), e) - s)
    raise ValueError(f"source time {src} was cut")


# ---------------------------------------------------------------- words
def timeline_words():
    segs = json.load(open(TRANSCRIPT))
    words = [w for s in segs for w in s["words"]]
    out, seen = [], set()
    for c in ACLIPS:
        if "silence" in c:
            continue
        src = OVERRIDE.get(c["s"], words)
        for w in src:
            inside = c["s"] - 0.08 <= w["s"] <= c["e"] - 0.04
            straddle = c["s"] - 0.6 <= w["s"] < c["s"] and w["e"] > c["s"] + 0.15   # word mostly kept
            key = (round(w["s"], 2), w["w"])
            if key in seen:            # already captioned in the previous (contiguous) clip
                continue
            if (inside or straddle) and not any(d0 <= w["s"] < d1 for d0, d1 in DROP):
                seen.add(key)
                txt = w["w"].strip()
                core = txt.strip(",.")
                txt = txt.replace(core, FIX.get(core, FIX.get(core.lower(), core)))
                s = c["t"] + max(w["s"], c["s"]) - c["s"]
                e = c["t"] + min(w["e"], c["e"]) - c["s"]
                if txt.startswith("-") and out and out[-1]["clip"] == id(c):   # "sisi" + "-sisi" -> "sisi-sisi"
                    out[-1]["w"] = out[-1]["w"].rstrip(",.") + txt
                    out[-1]["e"] = e
                elif txt.strip(",.?!"):
                    out.append(dict(w=txt, s=s, e=e, clip=id(c)))
    out.sort(key=lambda w: w["s"])
    return out


# ---------------------------------------------------------------- ASS
def ts(t):
    t = max(0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


ASS_HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Fredoka,{CAP_FS},&H00FFFFFF,&H000000FF,&H001C5A2E,&H641C5A2E,-1,0,0,0,100,100,0,0,1,4,1,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Bub,Fredoka,62,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,5,40,40,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,&H001C5A2E,&H641C5A2E,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


# palette from the pillows: dark avocado skin, leaf green, lime flesh, pale flesh, seed brown, blush (the cheeks)
SKIN = "&H001C5A2E&"     # #2E5A1C  outlines, label text, shadows, end-card rim
LEAF = "&H002E9B5E&"     # #5E9B2E  leaves, green labels, blinds
LIME = "&H004BEBC9&"     # #C9EB4B  active caption word, lime labels, progress dots, blinds
CREAM = "&H00D2F8F6&"    # #F6F8D2  cream labels, inner rim, blinds
SEED = "&H001F3B6A&"     # #6A3B1F  seed badge, highlight on cream labels
BLUSH = "&H00B18FFF&"    # #FF8FB1  caption keywords, blush labels
WHITE = "&H00FFFFFF&"
KEY = BLUSH
BLUSH_FILL = "&H00B18FFF&"   # blush label fill (white text)


def captions(words):
    """3-word chunks. Refresh v7: the active word is lifted out of the line and drawn on its own in lime with a
    springy scale bounce (positions measured with Pillow, so the line never reflows), instead of a box / blob /
    marker / underline / colour sweep; keywords are blush pink."""
    ev = []
    chunks, cur = [], []
    for w in words:
        if cur and (len(cur) >= 3 or w["s"] - cur[-1]["e"] > 0.35 or w["clip"] != cur[-1]["clip"]
                    or cur[-1]["w"][-1] in ",.?!"):
            chunks.append(cur)
            cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    base_y = H - (SAFE_B + 20)                   # bottom of the caption line (alignment 2)
    for i, ch in enumerate(chunks):
        end = ch[-1]["e"] + 0.15
        if i + 1 < len(chunks):
            end = min(end, chunks[i + 1][0]["s"])
        toks = [x["w"].upper().strip(",.") for x in ch]
        fs = CAP_FS
        sp = _font(fs).getlength(" ") * ASS_PER_PIL
        widths = [_font(fs).getlength(t) * ASS_PER_PIL for t in toks]
        total = sum(widths) + sp * (len(toks) - 1)
        if total > SAFE_W - 70:                  # shrink long chunks: one line, with room for the bounce
            k = (SAFE_W - 70) / total
            fs, sp, widths, total = int(fs * k), sp * k, [w * k for w in widths], total * k
        x = CX - total / 2
        lefts = []
        for wdt in widths:
            lefts.append(x)
            x += wdt + sp
        for j, w in enumerate(ch):
            ws = w["s"] if j else min(w["s"], ch[0]["s"])
            we = ch[j + 1]["s"] if j + 1 < len(ch) else end
            parts = []
            for k, t in enumerate(toks):
                if k == j:
                    parts.append(r"{\1a&HFF&\3a&HFF&\4a&HFF&}%s{\1a&H00&\3a&H00&\4a&H64&}" % t)   # hole for it
                elif t.strip("-") in HILITE or t in HILITE:
                    parts.append(r"{\c%s}%s{\c%s}" % (KEY, t, WHITE))   # not {\r}: it would reset \fs
                else:
                    parts.append(t)
            ev.append(f"Dialogue: 2,{ts(ws)},{ts(we)},Cap,,0,0,0,,{{\\fs{fs}}}" + " ".join(parts))
            ev.append(f"Dialogue: 3,{ts(ws)},{ts(we)},Cap,,0,0,0,,"
                      rf"{{\an2\pos({lefts[j] + widths[j] / 2:.0f},{base_y + 4})\fs{fs}\c{LIME}\bord5\frz-3"
                      rf"\fscx92\fscy92\t(0,90,\fscx126\fscy126)\t(90,190,\fscx114\fscy114)}}{toks[j]}")
    return ev

_FIT_FONTS = {}


def _font(size):
    return _FIT_FONTS.setdefault(size, ImageFont.truetype(FONT_FILE, size))


def fit_size(text, size, max_w=SAFE_W - 110):   # room for the pill ends + white border + pop overshoot
    """Shrink a label's font size so its pill stays inside the safe area."""
    plain = text.replace("*", "")
    w = _font(size).getlength(plain) * ASS_PER_PIL + size * 0.9
    return size if w <= max_w else int(size * max_w / w)


def _n(v):
    return f"{v:.0f}"


def rrect(w, h, r, cx=None, cy=None):
    """ASS drawing of a rounded rectangle. libass measures a drawing's box from (0, 0), so by default it sits at
    (0..w, 0..h) and \\an5 then centres it on \\pos."""
    cx = w / 2 if cx is None else cx
    cy = h / 2 if cy is None else cy
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    c = 0.5523 * r
    p = [("m", x0 + r, y0), ("l", x1 - r, y0), ("b", x1 - r + c, y0, x1, y0 + r - c, x1, y0 + r),
         ("l", x1, y1 - r), ("b", x1, y1 - r + c, x1 - r + c, y1, x1 - r, y1), ("l", x0 + r, y1),
         ("b", x0 + r - c, y1, x0, y1 - r + c, x0, y1 - r), ("l", x0, y0 + r),
         ("b", x0, y0 + r - c, x0 + r - c, y0, x0 + r, y0)]
    return " ".join(op + " " + " ".join(_n(v) for v in vals) for op, *vals in p)


def ell(cx, cy, rx, ry):
    c = 0.5523
    return (f"m {_n(cx + rx)} {_n(cy)} b {_n(cx + rx)} {_n(cy + c * ry)} {_n(cx + c * rx)} {_n(cy + ry)} {_n(cx)} {_n(cy + ry)} "
            f"b {_n(cx - c * rx)} {_n(cy + ry)} {_n(cx - rx)} {_n(cy + c * ry)} {_n(cx - rx)} {_n(cy)} "
            f"b {_n(cx - rx)} {_n(cy - c * ry)} {_n(cx - c * rx)} {_n(cy - ry)} {_n(cx)} {_n(cy - ry)} "
            f"b {_n(cx + c * rx)} {_n(cy - ry)} {_n(cx + rx)} {_n(cy - c * ry)} {_n(cx + rx)} {_n(cy)}")



def circ(cx, cy, r):
    return ell(cx, cy, r, r)


def seed_label(t0, t1, text, y=180, col=SKIN, fill=CREAM, hi=SEED, layer=5, x=CX, size=62):
    """Refresh v7 label: a flat pill with a round brown "avocado seed" badge on its left end (the emoji sticker
    sits inside the seed). It drops in from above and lands with a little squash, instead of pills / stickers /
    speech bubbles / patches / tickets. *word* = highlight. Returns (events, badge centre x, badge radius)."""
    size = fit_size(text, size, max_w=SAFE_W - 30 - int(size * 1.6))
    plain = text.replace("*", "")
    h = size * 1.3
    r = h * 0.6                                   # seed badge radius (pokes out above and below the pill)
    tw = _font(size).getlength(plain) * ASS_PER_PIL + size * 0.85
    w = tw + r * 1.6
    x0 = x - (w - r * 0.45) / 2                   # centre the pill + the badge that pokes out on the left
    bx = x0 + r * 0.55                            # badge centre
    parts = text.split("*")
    txt = "".join(p if i % 2 == 0 else rf"{{\c{hi}}}{p}{{\c{col}}}" for i, p in enumerate(parts))
    land = r"\t(190,250,\fscx108\fscy90)\t(250,340,\fscx100\fscy100)\fad(0,120)"

    def mv(ax, ay):
        return rf"\move({ax:.0f},{ay - 45:.0f},{ax:.0f},{ay:.0f},0,190)"

    pill = rrect(w, h, h / 2)
    ev = [
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
        rf"{{\an5{mv(x, y + 7)}\c{SKIN}\1a&H70&\bord0\shad0{land}\p1}}{pill}{{\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
        rf"{{\an5{mv(x, y)}\c{fill}\3c{SKIN}\bord3.5\shad0{land}\p1}}{pill}{{\p0}}",
        f"Dialogue: {layer + 1},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
        rf"{{\an5{mv(bx, y)}\c{SEED}\3c{LIME}\bord4\shad0{land}\p1}}{circ(r, r, r)}{{\p0}}",
        f"Dialogue: {layer + 1},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
        rf"{{\an5{mv(bx - r * 0.38, y - r * 0.42)}\c{CREAM}\1a&H90&\bord0\shad0{land}\p1}}"
        rf"{ell(r * 0.3, r * 0.17, r * 0.3, r * 0.17)}{{\p0}}",
        f"Dialogue: {layer + 1},{ts(t0)},{ts(t1)},Bub,,0,0,0,,"
        rf"{{\an5{mv(x0 + r * 1.6 + tw / 2 - r * 0.05, y)}\fs{size}\c{col}{land}}}{txt}",
    ]
    return ev, bx, r


def blinds(t0, layer=9, n=6):
    """Refresh v7 transition: horizontal blinds in lime / leaf / cream shoot in from alternate sides and pull back
    (no flash, no sweeping band, no iris)."""
    ev = []
    bh = H / n
    cols = [LIME, LEAF, CREAM]
    for i in range(n):
        a = t0 + 0.022 * i
        left = i % 2 == 0
        an, px = (4, 0) if left else (6, W)
        ev.append(f"Dialogue: {layer},{ts(a)},{ts(a + 0.30)},Shape,,0,0,0,,"
                  rf"{{\an{an}\pos({px},{bh * i + bh / 2:.0f})\c{cols[i % 3]}\1a&H28&\bord0\shad0\fscx0"
                  rf"\t(0,110,\fscx100)\t(150,290,\fscx0)\p1}}m 0 0 l {W} 0 {W} {bh + 1:.0f} 0 {bh + 1:.0f}{{\p0}}")
    return ev


def leaf(sz):
    """Avocado-leaf shape (pointed oval + midrib cut), positive coords."""
    return (f"m 0 {_n(sz * 0.5)} b {_n(sz * 0.35)} {_n(-sz * 0.05)} {_n(sz * 1.35)} {_n(-sz * 0.05)} "
            f"{_n(sz * 1.8)} {_n(sz * 0.5)} b {_n(sz * 1.35)} {_n(sz * 1.05)} {_n(sz * 0.35)} {_n(sz * 1.05)} "
            f"0 {_n(sz * 0.5)}")


def falling_leaves(t0, layer=7):
    """Refresh v7 motif: three avocado leaves flutter down the sides of the safe area at each section change."""
    ev = []
    spots = [(64, 150, 20, LEAF, 1), (118, 120, 14, LIME, -1), (566, 160, 17, LEAF, -1)]
    for i, (lx, ly, sz, cc, d) in enumerate(spots):
        a = t0 + 0.12 * i
        ev.append(f"Dialogue: {layer},{ts(a)},{ts(a + 1.7)},Shape,,0,0,0,,"
                  rf"{{\an5\move({lx},{ly},{lx + 26 * d},{ly + 300},0,1700)\c{cc}\3c{SKIN}\bord2\shad0"
                  rf"\frz{-30 * d}\t(0,1700,\frz{70 * d})\fad(120,450)\p1}}{leaf(sz)}{{\p0}}")
    return ev


def avocado_half(s=1.0):
    """Avocado-half outline (narrow top, round bottom), positive coords inside (0..260s, 0..360s)."""
    pts = [(130, 0), (200, 0, 240, 110, 250, 200), (260, 290, 210, 360, 130, 360),
           (50, 360, 0, 290, 10, 200), (20, 110, 60, 0, 130, 0)]
    out = f"m {_n(pts[0][0] * s)} {_n(pts[0][1] * s)}"
    for p in pts[1:]:
        out += " b " + " ".join(_n(v * s) for v in p)
    return out


def graphics():
    ev, stickers, sfx = [], [], []
    # progress bar (retention): a row of cream dots along the top edge; a lime copy is revealed by a growing clip
    dots = " ".join(circ(9 + 18 * i, 9, 4.2) for i in range(W // 18 + 1))
    ev.append(f"Dialogue: 7,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{CREAM}\1a&H80&\bord0\shad0\p1}}{dots}{{\p0}}")
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{LIME}\3c{SKIN}\bord1.5\shad0\clip(0,0,0,20)\t(0,{int(TOTAL * 1000)},\clip(0,0,{W},20))"
              rf"\p1}}{dots}{{\p0}}")

    def lab(s0, s1, text, emoji, sound="thud", vol=0.55, **kw):
        t0, t1 = tl(s0), tl(s1)
        e, bx, r = seed_label(t0, t1, text, **kw)
        ev.extend(e)
        stickers.append((emoji, t0 + 0.2, t1, bx, kw.get("y", 180), int(r * 1.45)))
        if sound:
            sfx.append((sound, t0 + 0.15, vol))

    def blab(t0, t1, text, emoji, sound="thud", vol=0.55, **kw):
        e, bx, r = seed_label(t0, t1, text, **kw)
        ev.extend(e)
        stickers.append((emoji, t0 + 0.2, t1, bx, kw.get("y", 180), int(r * 1.45)))
        if sound:
            sfx.append((sound, t0 + 0.15, vol))

    def section(name, sound="shutter", vol=0.5):
        t0 = BT[name]["t0"]
        ev.extend(blinds(t0 - 0.08))
        ev.extend(falling_leaves(t0 + 0.1))
        sfx.append((sound, t0 - 0.08, vol))

    # ---- HOOK: team chubby or team long?
    lab(8.10, 8.86, "KORANG *MANA SATU*?", "🤔", fill=CREAM, size=66)
    lab(8.90, 10.16, "*MONTEL* KE *PANJANG*?", "🥑", fill=LIME, hi=SEED, size=64, sound="boing", vol=0.4)
    lab(10.22, 11.66, "MONTEL? *AMBIL MONTEL*!", "😋", col=WHITE, fill=LEAF, hi=LIME, size=62)

    # ---- intro: green lovers, two shapes
    section("intro")
    lab(0.04, 1.90, "PEMINAT *HIJAU*?", "💚", fill=CREAM, size=70)
    lab(2.00, 3.88, "AVOCADO *CANTIK BETUL*", "✨", fill=LIME, hi=SEED, size=62)
    lab(4.20, 5.52, "ADA *2 BENTUK*!", "✌️", col=WHITE, fill=LEAF, hi=LIME, size=72, sound="pop", vol=0.5)
    lab(5.56, 6.66, "YANG *MONTEL*", "🫶", fill=CREAM, size=70)
    lab(6.72, 7.66, "YANG *PANJANG*", "📏", fill=LIME, hi=SEED, size=70)

    # ---- sizes
    section("saiz")
    lab(12.34, 14.44, "PANJANG *90CM*", "📏", col=WHITE, fill=LEAF, hi=LIME, size=72)
    lab(14.96, 17.18, "MONTEL *70CM*", "🥑", fill=LIME, hi=SEED, size=72)

    # ---- soft, huggable
    section("gebu", sound="boing", vol=0.4)
    lab(17.30, 18.42, "*GEBU-GEBAS*!", "☁️", col=WHITE, fill=BLUSH_FILL, hi=SKIN, size=76, sound="sparkle", vol=0.35)
    lab(18.50, 19.74, "SEDAP *PELUK*", "🤗", fill=CREAM, size=72)

    # ---- gift ideas
    section("hadiah")
    lab(19.88, 22.40, "SESUAI *BUAT HADIAH*", "🎁", fill=LIME, hi=SEED, size=64, sound="sparkle", vol=0.3)
    lab(23.10, 25.86, "BIRTHDAY *BESTFRIEND*", "👯", fill=CREAM, size=60)
    lab(26.16, 27.20, "BIRTHDAY *ANAK*", "🧒", col=WHITE, fill=LEAF, hi=LIME, size=66)
    lab(27.45, 29.22, "BIRTHDAY *ISTERI*", "👩", fill=LIME, hi=SEED, size=66)
    lab(29.56, 31.02, "BIRTHDAY *SUAMI*", "👨", col=WHITE, fill=BLUSH_FILL, hi=SKIN, size=66)

    # ---- material + zip (over the back-of-pillow fabric)
    section("material")
    lab(41.40, 43.92, "KAIN *VELVET*", "🧵", fill=CREAM, size=74)
    lab(44.32, 45.10, "*TAHAN LASAK*", "💪", col=WHITE, fill=LEAF, hi=LIME, size=72, sound="pop", vol=0.5)
    lab(45.14, 45.76, "*TAK BERBULU*", "👌", fill=LIME, hi=SEED, size=72, sound="pop", vol=0.5)
    lab(45.78, 46.36, "*BOLEH BASUH*", "🫧", fill=CREAM, size=72, sound="pop", vol=0.5)
    lab(53.12, 54.16, "ADA *ZIP* JUGA", "🤐", col=WHITE, fill=LEAF, hi=LIME, size=72, sound="zip", vol=0.45)

    # ---- CTA
    section("cta", vol=0.4)
    lab(47.72, 49.04, "TENGOK *BEG KUNING*", "🛒", col=WHITE, fill=SKIN, hi=LIME, size=66, sound="bloop", vol=0.5)

    # ---- end card (refresh v7: a big avocado half with the title on the flesh + stacked seed labels)
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 6,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{SKIN}\1a&HFF&\t(0,280,\1a&H80&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    ev.extend(blinds(e0 - 0.08))
    s = 1.12
    aw, ah = 260 * s, 360 * s
    ax, ay = CX - aw / 2, 150
    for k, (cc, sc, lay) in enumerate([(SKIN, 1.0, 7), (CREAM, 0.92, 8), (LIME, 0.84, 8)]):
        ox, oy = ax + aw * (1 - sc) / 2, ay + ah * (1 - sc) / 2
        bord = r"\3c%s\bord4" % SEED if k == 0 else r"\bord0"
        ev.append(f"Dialogue: {lay + k},{ts(e0 + 0.05)},{ts(TOTAL)},Shape,,0,0,0,,"
                  rf"{{\an7\move({ox:.0f},{oy - 60:.0f},{ox:.0f},{oy:.0f},0,230){bord}\c{cc}\shad0\fad(140,0)"
                  rf"\t(230,290,\fscy94)\t(290,380,\fscy100)\p1}}{avocado_half(s * sc)}{{\p0}}")
    sy = ay + ah * 0.70
    ev.append(f"Dialogue: 11,{ts(e0 + 0.25)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an5\pos({CX},{sy:.0f})\c{SEED}\3c{SKIN}\bord3\shad0\fscx0\fscy0\t(0,160,\fscx112\fscy112)"
              rf"\t(160,260,\fscx100\fscy100)\p1}}{circ(58, 58, 58)}{{\p0}}")
    ev.append(f"Dialogue: 12,{ts(e0 + 0.25)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an5\pos({CX - 22},{sy - 24:.0f})\c{CREAM}\1a&H90&\bord0\shad0\fad(200,0)\p1}}"
              rf"{ell(18, 10, 18, 10)}{{\p0}}")
    ev.append(f"Dialogue: 12,{ts(e0 + 0.30)},{ts(TOTAL)},Bub,,0,0,0,,"
              rf"{{\an5\pos({CX},{ay + ah * 0.30:.0f})\fs42\c{SKIN}\fad(180,0)}}BANTAL")
    ev.append(f"Dialogue: 12,{ts(e0 + 0.30)},{ts(TOTAL)},Bub,,0,0,0,,"
              rf"{{\an5\pos({CX},{ay + ah * 0.42:.0f})\fs54\c{SKIN}\fad(180,0)}}AVOCADO")
    blab(e0 + 0.45, TOTAL, "*MONTEL* • *PANJANG*", "🥑", fill=CREAM, y=650, layer=13, size=52)
    blab(e0 + 0.70, TOTAL, "KORANG *TEAM MANA*?", "🤔", fill=LIME, hi=SEED, y=750, layer=13, size=52)
    blab(e0 + 0.95, TOTAL, "TEKAN *BEG KUNING*", "🛒", col=WHITE, fill=SKIN, hi=LIME, y=850, layer=13, size=56,
         sound="ding", vol=0.4)
    ev.extend(falling_leaves(e0 + 0.2))
    sfx += [("boing", e0 + 0.15, 0.4), ("sparkle", e0 + 0.3, 0.35)]
    return ev, stickers, sfx


# ---------------------------------------------------------------- emoji stickers
def sticker_frames(stickers):
    font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
    cache = {}
    for em, *_ in stickers:
        if em not in cache:
            im = Image.new("RGBA", (160, 160))
            ImageDraw.Draw(im).text((10, 10), em, font=font, embedded_color=True)
            cache[em] = im.crop(im.getbbox())
    n = int(round(TOTAL * FPS))
    for f in range(n):
        t = f / FPS
        frame = Image.new("RGBA", (RW, RH))
        for i, (em, t0, t1, x, y, size) in enumerate(stickers):
            if not (t0 <= t < t1):
                continue
            u = t - t0
            sc = min(1.0, u / 0.12) * 1.25 if u < 0.12 else (1.25 - 0.25 * min(1, (u - 0.12) / 0.1))
            if t1 - t < 0.12:
                sc *= max(0.0, (t1 - t) / 0.12)
            if sc <= 0.02:
                continue
            bob = 5 * K * np.sin(2 * np.pi * 1.6 * u + i)
            img = cache[em]
            s = max(1, int(size * sc * K))
            im = img.resize((s, int(s * img.height / img.width)), Image.LANCZOS)
            im = im.rotate(8 * np.sin(2 * np.pi * 0.9 * u + i), resample=Image.BICUBIC, expand=True)
            # keep stickers out of the TikTok UI (right column, bottom caption, top tabs)
            px = min(max(x * K, SAFE_L * K + im.width / 2), (W - SAFE_R) * K - im.width / 2)
            py = min(max(y * K + bob, SAFE_T * K + im.height / 2), (H - SAFE_B) * K - im.height / 2)
            frame.alpha_composite(im, (int(px - im.width / 2), int(py - im.height / 2)))
        yield frame.tobytes()


# ---------------------------------------------------------------- render
def run(cmd, **kw):
    print("+", " ".join(cmd[:6]), "...", flush=True)
    subprocess.run(cmd, check=True, **kw)


def render_base(sfx):
    # video: one ffmpeg per clip (a single graph with many trims of one input
    # buffers frames and runs out of memory at 1080p), then stream-copy concat
    cdir = os.path.join(OUT, "clips")
    os.makedirs(cdir, exist_ok=True)
    lst = []
    for i, c in enumerate(VCLIPS):
        z = c["z"]
        # frame count from rounded timeline positions so clips never drift from the audio
        n = round((c["t"] + c["d"]) * FPS) - round(c["t"] * FPS)
        path = os.path.join(cdir, f"{i:02d}.mp4")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{c['s']}", "-to", f"{c['e']}", "-i", PROXY, "-an",
             "-vf", f"setpts=(PTS-STARTPTS)/{c['sp']},"
                    f"scale={int(RW * z) // 2 * 2}:{int(RH * z) // 2 * 2},crop={RW}:{RH}:(iw-{RW})/2:(ih-{RH})/2*0.6,"
                    f"fps={FPS},setsar=1,tpad=stop_mode=clone:stop=3,trim=end_frame={n}",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "12" if FINAL else "16", "-pix_fmt", "yuv420p",
             path])
        lst.append(f"file '{os.path.abspath(path)}'")
    with open(os.path.join(cdir, "list.txt"), "w") as f:
        f.write("\n".join(lst) + "\n")
    render_audio(sfx, ["-f", "concat", "-safe", "0", "-i", os.path.join(cdir, "list.txt")],
                 os.path.join(OUT, "base.mp4"))


def render_audio(sfx, video_input, out_path):
    """Voice + SFX mix, muxed with input 0's video stream (stream copy)."""
    fc = []
    al = []
    for i, c in enumerate(ACLIPS):
        if "silence" in c:
            fc.append(f"anullsrc=r=48000:cl=mono,atrim=0:{c['silence']:.3f}[a{i}]")
        else:
            d = c["e"] - c["s"]
            fc.append(f"[1:a]atrim={c['s']}:{c['e']},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=mono,"
                      f"afade=t=in:d=0.02,afade=t=out:st={d - 0.03:.3f}:d=0.03[a{i}]")
        al.append(f"[a{i}]")
    fc.append("".join(al) + f"concat=n={len(al)}:v=0:a=1,"
              # clarity: cut rumble + mud, lift presence/air, tame sibilance
              "highpass=f=100,afftdn=nf=-25:tn=1,"
              "equalizer=f=250:t=q:w=1.0:g=-3,equalizer=f=3200:t=q:w=1.2:g=4,"
              "treble=g=2.5:f=9000,deesser=i=0.35,"
              # even out quiet words before the gain stage
              "acompressor=threshold=-26dB:ratio=4:attack=4:release=90:makeup=2")
    # pass 1: measure the processed voice, pass 2: exact gain to VOICE_LUFS + peak limiter
    probe = subprocess.run(["ffmpeg", "-nostats", "-vn", "-i", PROXY, "-filter_complex",
                            ";".join(fc).replace("[1:a]", "[0:a]") + ",ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    measured = float(probe.split("Summary:")[1].split("I:")[1].split("LUFS")[0])
    gain = VOICE_LUFS - measured
    print(f"  voice {measured:.1f} LUFS -> {VOICE_LUFS} (gain {gain:+.1f} dB)", flush=True)
    fc[-1] += (f",volume={gain:.2f}dB,alimiter=limit=0.84:attack=3:release=60:level=false,"
               "aformat=channel_layouts=stereo[voice]")
    inputs = [*video_input, "-vn", "-i", PROXY]
    mix = ["[voice]"]
    for j, (name, t, vol) in enumerate(sfx):
        inputs += ["-i", os.path.join(SFX, name + ".wav")]
        ms = max(0, int(t * 1000))
        fc.append(f"[{j + 2}:a]volume={vol},adelay={ms}|{ms}[s{j}]")
        mix.append(f"[s{j}]")
    fc.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=first,alimiter=limit=0.95[aout]")
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc),
         "-map", "0:v", "-map", "[aout]", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "192k", "-t", f"{TOTAL:.3f}", "-movflags", "+faststart", out_path])


def render_preview(stickers, ass_path):
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", os.path.join(OUT, "base.mp4"),
           "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{RW}x{RH}", "-r", str(FPS), "-i", "-",
           # stickers go on top of the ASS layer: the emoji sit inside the seed badges drawn by ASS
           "-filter_complex", f"[0:v]ass={ass_path}[a];[a][1:v]overlay=0:0:format=auto[v]",
           "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "slow" if FINAL else "medium", "-crf", "18" if FINAL else "21",
           "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-c:a", "copy", "-movflags", "+faststart",
           os.path.join(OUT, "final.mp4" if FINAL else "preview.mp4")]
    print("+ preview", flush=True)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fr in sticker_frames(stickers):
        p.stdin.write(fr)
    p.stdin.close()
    assert p.wait() == 0


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    words = timeline_words()
    ev, stickers, sfx = graphics()
    ass_path = os.path.join(OUT, "overlay.ass")
    with open(ass_path, "w") as f:
        f.write(ASS_HEAD + "\n".join(ev + captions(words)) + "\n")
    with open(os.path.join(OUT, "edl.json"), "w") as f:
        json.dump(dict(total=TOTAL, blocks=[{k: b[k] for k in ("name", "t0", "dur", "v", "a")} for b in BLOCKS],
                       words=words, sfx=sfx, stickers=stickers), f, ensure_ascii=False, indent=1)
    print(f"timeline {TOTAL:.2f}s, {len(VCLIPS)} clips, {len(sfx)} sfx, {len(stickers)} stickers")
    if "--audio-only" in sys.argv:
        # re-mix audio onto an already rendered video (graphics untouched)
        src = os.path.join(OUT, "final.mp4" if FINAL else "preview.mp4")
        render_audio(sfx, ["-i", src], os.path.join(OUT, ("final" if FINAL else "preview") + "_voice.mp4"))
    elif "--no-render" not in sys.argv:
        render_base(sfx)
        render_preview(stickers, ass_path)

