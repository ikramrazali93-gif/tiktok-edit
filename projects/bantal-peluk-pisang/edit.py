#!/usr/bin/env python3
"""Edit for the banana hug pillow (bantal peluk pisang, 70 / 50 / 35cm) TikTok video, IMG_2931.

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
# One clip (IMG_2931), outdoors on grass: she stands holding three banana hug pillows (70, 50 and 35cm).
# v: list of (src_in, src_out, speed, zoom)
# a: 'same' (follow v at speed 1), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK (J-cut): "Korang dah ada ke?" (moved from 37.7s) + "Ya Allah, bantal peluk pisang, gebunya!" over her
    # pushing the big banana at the camera (end of the clip), then back to the three bananas
    dict(name="hook", a=[(37.70, 38.74), (0.00, 3.48)], v=[(47.55, 49.66, 1, 1.0), (0.95, 3.36, 1, 1.06)]),
    # "Ada 3 saiz. | 70cm, 50cm dan juga 35cm."  (zoom change on "70cm")
    dict(name="saiz", a="same", v=[(3.48, 5.30, 1, 1.0), (5.30, 10.12, 1, 1.10)]),
    # "Kalau mami-mami, ambil yang besar sekali. Boleh peluk waktu tidur."
    dict(name="mami", a="same", v=[(14.20, 17.50, 1, 1.04)]),
    # "Kalau nak beli untuk bawa drive, boleh ambil saiz 50cm."
    dict(name="drive", a="same", v=[(17.75, 21.38, 1, 1.0)]),
    # "Korang nak naik kereta ke, nak balik kampung, | bantal 50cm ni lebih selesa | kita travel. Kan, boleh buat
    #  alas kepala dalam kereta."  ("Ada yang beli bawa naik bus," and "Adalah" cut)
    dict(name="travel", a=[(23.75, 26.02), (26.52, 33.04)],
         v=[(23.75, 26.02, 1, 1.08), (26.52, 29.28, 1, 1.0), (29.28, 33.04, 1, 1.10)]),
    # "Yang ni 35cm, comel je. Saiz baby-baby."  (the drawn-out "gitu..." after it cut)
    dict(name="baby", a="same", v=[(33.26, 36.20, 1, 1.0)]),
    # "Yang ni nak beli buat hadiah untuk anak korang pun sangat sesuai."  (moved after the 35cm one)
    dict(name="hadiah", a="same", v=[(10.66, 14.14, 1, 1.06)]),
    # "Kalau belum lagi, tengok dekat beg kuning sekarang."  (the price lines after it are cut: no price talk)
    dict(name="cta", a="same", v=[(39.22, 41.56, 1, 1.0)]),
    # all three bananas, slowed, under the ticket end card
    dict(name="end", a=None, v=[(44.00, 46.00, 0.7, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "bantai": "bantal", "Bantai": "Bantal"}
# hand-checked words (full-file pass + per-chunk re-transcription)
def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


OVERRIDE = {
    37.70: _w(("Korang", 37.74, 38.14), ("dah", 38.18, 38.30), ("ada", 38.30, 38.50), ("ke?", 38.50, 38.74)),
    0.00: _w(("Ya", 0.00, 0.40), ("Allah,", 0.40, 0.62), ("bantal", 0.70, 0.96), ("peluk", 0.96, 1.26),
             ("pisang,", 1.26, 2.22), ("gebunya!", 2.40, 3.14)),
    3.48: _w(("Ada", 3.52, 3.78), ("3", 3.78, 4.12), ("saiz.", 4.12, 5.26)),
    5.30: _w(("70cm,", 5.34, 6.30), ("50cm", 6.74, 7.64), ("dan", 7.64, 7.96), ("juga", 7.96, 8.46),
             ("35cm.", 8.46, 9.92)),
    14.20: _w(("Kalau", 14.22, 14.50), ("mami", 14.50, 14.76), ("-mami,", 14.76, 15.12), ("ambil", 15.20, 15.40),
              ("yang", 15.40, 15.56), ("besar", 15.56, 15.76), ("sekali.", 15.76, 16.14), ("Boleh", 16.22, 16.44),
              ("peluk", 16.44, 16.66), ("waktu", 16.66, 16.86), ("tidur.", 16.86, 17.48)),
    17.75: _w(("Kalau", 17.98, 18.14), ("nak", 18.14, 18.30), ("beli", 18.30, 18.88), ("untuk", 18.88, 19.46),
              ("bawa", 19.46, 19.72), ("drive,", 19.72, 20.00), ("boleh", 20.14, 20.22), ("ambil", 20.22, 20.40),
              ("saiz", 20.40, 20.66), ("50cm.", 20.66, 21.30)),
    23.75: _w(("Korang", 23.82, 23.98), ("nak", 23.98, 24.18), ("naik", 24.18, 24.34), ("kereta", 24.34, 24.74),
              ("ke,", 24.74, 24.96), ("nak", 25.32, 25.46), ("balik", 25.46, 25.66), ("kampung,", 25.66, 26.00)),
    26.52: _w(("bantal", 26.60, 27.54), ("50cm", 27.54, 28.12), ("ni", 28.12, 28.40), ("lebih", 28.40, 28.84),
              ("selesa", 28.84, 29.28), ("kita", 29.30, 29.94), ("travel.", 30.20, 30.78), ("Kan,", 31.00, 31.16),
              ("boleh", 31.30, 31.38), ("buat", 31.38, 31.54), ("alas", 31.54, 31.80), ("kepala", 31.80, 32.12),
              ("dalam", 32.12, 32.34), ("kereta.", 32.34, 32.98)),
    33.26: _w(("Yang", 33.34, 33.54), ("ni", 33.54, 33.84), ("35cm,", 33.84, 34.58), ("comel", 34.78, 34.98),
              ("je.", 34.98, 35.18), ("Saiz", 35.22, 35.48), ("baby", 35.48, 35.80), ("-baby.", 35.80, 36.16)),
    39.22: _w(("Kalau", 39.24, 39.42), ("belum", 39.42, 39.70), ("lagi,", 39.70, 40.06), ("tengok", 40.10, 40.48),
              ("dekat", 40.48, 40.80), ("beg", 40.80, 40.92), ("kuning", 40.92, 41.14), ("sekarang.", 41.14, 41.50)),
}
DROP = []
HILITE = {"PISANG", "GEBUNYA", "3", "SAIZ", "70CM", "50CM", "35CM", "MAMI-MAMI", "BESAR", "PELUK", "TIDUR",
          "DRIVE", "KERETA", "KAMPUNG", "SELESA", "TRAVEL", "KEPALA", "COMEL", "BABY-BABY", "HADIAH", "ANAK",
          "BEG", "KUNING"}



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
Style: Cap,Fredoka,{CAP_FS},&H00FFFFFF,&H000000FF,&H0014243A,&H6414243A,-1,0,0,0,100,100,0,0,1,4,1,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Bub,Fredoka,62,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,5,40,40,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,&H0014243A,&H6414243A,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


# palette from the pillows: banana yellow (body), deep banana (shading), choco brown (tip / outlines), blush pink
# (the cheeks), cream, and leaf green (the stem + grass)
BANANA = "&H0035E1FF&"    # #FFE135  tickets, keyword caption, progress bar, iris pop
BANANA_D = "&H0000C2F2&"  # #F2C200  highlight on cream tickets
CHOCO = "&H0014243A&"     # #3A2414  outlines, ticket text, caption outline
BROWN = "&H001E3E6B&"     # #6B3E1E  ticket perforation, highlight on banana tickets
BLUSH = "&H00AB8FFF&"     # #FF8FAB  active-word underline, blush tickets
BERRY = "&H006E3FD6&"     # #D63F6E  highlight on banana tickets
CREAM = "&H00D8F6FF&"     # #FFF6D8
LEAF = "&H0043C07B&"      # #7BC043  stem-green tickets, sparkles
WHITE = "&H00FFFFFF&"
KEY = BANANA


def captions(words):
    """3-word chunks. Refresh v6: the active word gets a thick blush underline bar that grows out under it (drawn
    behind the text, positions measured with Pillow) instead of a box / blob / marker / colour change; keywords
    are banana yellow."""
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
        if total > SAFE_W - 40:                  # shrink long chunks so they stay on one line
            k = (SAFE_W - 40) / total
            fs, sp, widths, total = int(fs * k), sp * k, [w * k for w in widths], total * k
        x = CX - total / 2
        lefts = []
        for wdt in widths:
            lefts.append(x)
            x += wdt + sp
        ybar = base_y - fs * 0.02                # just under the letters
        for j, w in enumerate(ch):
            ws = w["s"] if j else min(w["s"], ch[0]["s"])
            we = ch[j + 1]["s"] if j + 1 < len(ch) else end
            bw, bh = widths[j] + 8, max(9, fs * 0.17)
            ev.append(f"Dialogue: 1,{ts(ws)},{ts(we)},Shape,,0,0,0,,"
                      rf"{{\an5\pos({lefts[j] + widths[j] / 2:.0f},{ybar:.0f})\c{BLUSH}\bord2.5\3c{CHOCO}\shad0"
                      rf"\fscx0\t(0,110,\fscx100)\p1}}{rrect(bw, bh, bh / 2)}{{\p0}}")
            parts = []
            for k, t in enumerate(toks):
                if k == j:
                    parts.append(t)
                elif t.strip("-") in HILITE or t in HILITE:
                    parts.append(r"{\c%s}%s{\c%s}" % (KEY, t, WHITE))   # not {\r}: it would reset \fs
                else:
                    parts.append(t)
            pop = r"\fscx90\fscy90\t(0,90,\fscx100\fscy100)" if j == 0 else ""
            ev.append(f"Dialogue: 2,{ts(ws)},{ts(we)},Cap,,0,0,0,,{{\\fs{fs}{pop}}}" + " ".join(parts))
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


def ticket_path(w, h, nr, r=10):
    """Ticket stub at (0..w, 0..h): rounded corners plus a half-round notch cut into the middle of each short side."""
    c = 0.5523
    cy = h / 2
    p = [("m", r, 0), ("l", w - r, 0), ("b", w - r + c * r, 0, w, r - c * r, w, r),
         ("l", w, cy - nr), ("b", w - c * nr, cy - nr, w - nr, cy - c * nr, w - nr, cy),
         ("b", w - nr, cy + c * nr, w - c * nr, cy + nr, w, cy + nr),
         ("l", w, h - r), ("b", w, h - r + c * r, w - r + c * r, h, w - r, h), ("l", r, h),
         ("b", r - c * r, h, 0, h - r + c * r, 0, h - r), ("l", 0, cy + nr),
         ("b", c * nr, cy + nr, nr, cy + c * nr, nr, cy), ("b", nr, cy - c * nr, c * nr, cy - nr, 0, cy - nr),
         ("l", 0, r), ("b", 0, r - c * r, r - c * r, 0, r, 0)]
    return " ".join(op + " " + " ".join(_n(v) for v in vals) for op, *vals in p)


def perforation(x, h, dash=9, gap=7, wd=3):
    """Dashed tear line (small rectangles) down the ticket at x, as one ASS drawing."""
    out, y = [], 9
    while y + dash <= h - 8:
        out.append(f"m {_n(x)} {_n(y)} l {_n(x + wd)} {_n(y)} {_n(x + wd)} {_n(y + dash)} {_n(x)} {_n(y + dash)}")
        y += dash + gap
    return " ".join(out)


def ticket(t0, t1, text, y=236, col=CHOCO, fill=BANANA, hi=BERRY, side="l", layer=5, x=CX, size=62):
    """Refresh v6 label: a ticket stub (notched ends, dashed tear line on the left, soft blurred shadow) that
    whips in from the side, instead of pills / stickers / speech bubbles / tilted boxes. *word* = highlight."""
    stub_k = 0.62
    size = fit_size(text, size, max_w=SAFE_W - 70 - int(size * 1.28 * stub_k))
    plain = text.replace("*", "")
    h = size * 1.28
    stub = h * stub_k
    w = _font(size).getlength(plain) * ASS_PER_PIL + size * 0.9 + stub
    parts = text.split("*")
    txt = "".join(p if i % 2 == 0 else rf"{{\c{hi}}}{p}{{\c{col}}}" for i, p in enumerate(parts))
    x0, y0 = x - w / 2, y - h / 2
    dx = -60 if side == "l" else min(60, (W - SAFE_R) - (x0 + w) - 4)
    mv = lambda ax, ay: rf"\move({ax + dx:.0f},{ay:.0f},{ax:.0f},{ay:.0f},0,170)\fad(90,130)"
    path = ticket_path(w, h, h * 0.2)
    return [
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
        rf"{{\an7{mv(x0 + 3, y0 + 7)}\c{CHOCO}\1a&H90&\bord0\shad0\blur6\p1}}{path}{{\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
        rf"{{\an7{mv(x0, y0)}\c{fill}\3c{CHOCO}\bord3\shad0\p1}}{path}{{\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
        rf"{{\an7{mv(x0, y0)}\c{col}\1a&H70&\bord0\shad0\p1}}{perforation(stub, h)}{{\p0}}",
        f"Dialogue: {layer + 1},{ts(t0)},{ts(t1)},Bub,,0,0,0,,"
        rf"{{\an5{mv(x0 + stub + (w - stub) / 2, y)}\fs{size}\c{col}}}{txt}",
    ]


def iris(t0, col=BANANA, layer=9, d=0.34):
    """Refresh v6 transition accent: a banana-yellow disc + ring pops out from the centre and fades (no full flash,
    no sweeping band)."""
    cx, cy = CX, 560
    return [
        f"Dialogue: {layer},{ts(t0)},{ts(t0 + d)},Shape,,0,0,0,,"
        rf"{{\an5\pos({cx},{cy})\c{col}\1a&H40&\bord0\shad0\fscx10\fscy10\t(0,{int(d * 1000)},\fscx420\fscy420\1a&HFF&)"
        rf"\p1}}{ell(60, 60, 60, 60)}{{\p0}}",
        f"Dialogue: {layer},{ts(t0 + 0.04)},{ts(t0 + d + 0.06)},Shape,,0,0,0,,"
        rf"{{\an5\pos({cx},{cy})\1a&HFF&\3c{WHITE}\3a&H20&\bord6\shad0\fscx20\fscy20"
        rf"\t(0,{int(d * 1000)},\fscx520\fscy520\3a&HFF&)\p1}}{ell(60, 60, 60, 60)}{{\p0}}",
    ]


def star(r):
    """4-point twinkle star (ASS drawing, positive coords, centre at (r, r))."""
    k = 0.26 * r
    pts = [(r, 0), (r + k, r - k), (2 * r, r), (r + k, r + k), (r, 2 * r), (r - k, r + k), (0, r), (r - k, r - k)]
    return "m " + " l ".join(f"{_n(px)} {_n(py)}" for px, py in pts)


def sparkles(t0, t1, y=236, spread=200, layer=7):
    """Refresh v6 motif: three little stars twinkle (scale in/out + spin) around a key ticket."""
    ev = []
    spots = [(CX - spread, y - 46, 16, LEAF), (CX + spread, y + 40, 13, WHITE), (CX + spread - 40, y - 58, 10, BLUSH)]
    for i, (sx, sy, r, cc) in enumerate(spots):
        sx = min(max(sx, SAFE_L + r + 4), W - SAFE_R - r - 4)
        a = t0 + 0.08 * i
        ms = int((t1 - a) * 1000)
        ev.append(f"Dialogue: {layer},{ts(a)},{ts(t1)},Shape,,0,0,0,,"
                  rf"{{\an5\pos({sx:.0f},{sy:.0f})\c{cc}\bord2\3c{CHOCO}\shad0\fscx0\fscy0\frz0"
                  rf"\t(0,180,\fscx120\fscy120)\t(180,320,\fscx100\fscy100)\t(0,{ms},\frz{90 if i % 2 else -90})"
                  rf"\t({max(ms - 200, 320)},{ms},\fscx0\fscy0)\p1}}{star(r)}{{\p0}}")
    return ev


def graphics():
    ev, stickers, sfx = [], [], []
    # progress bar (retention): banana fill on a thin choco track, top edge
    ev.append(f"Dialogue: 7,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{CHOCO}\1a&H70&\p1}}m 0 0 l {W} 0 {W} 9 0 9{{\p0}}")
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{BANANA}\fscx0\t(0,{int(TOTAL * 1000)},\fscx100)\p1}}m 0 0 l {W} 0 {W} 9 0 9{{\p0}}")

    def lab(s0, s1, text, sound="whip", vol=0.45, spark=False, **kw):
        ev.extend(ticket(tl(s0), tl(s1), text, **kw))
        if sound:
            sfx.append((sound, tl(s0) - 0.03, vol))
        if spark:
            ev.extend(sparkles(tl(s0) + 0.1, tl(s1)))

    def stk(em, s0, s1, x, y, size=96):
        stickers.append((em, tl(s0), tl(s1), x, y, size))

    def bstk(em, t0, t1, x, y, size=96):
        stickers.append((em, t0, t1, x, y, size))

    def section(name, sound="boing", vol=0.4):
        t0 = BT[name]["t0"]
        ev.extend(iris(t0 - 0.06))
        sfx.append((sound, t0 - 0.08, vol))

    SL, SR, SY = 92, 560, 150     # stickers sit above the ticket's ends

    # ---- HOOK: got one yet? -> banana hug pillow, so fluffy
    lab(37.74, 38.74, "KORANG *DAH ADA*?", fill=CREAM, hi=BANANA_D, side="l", size=68, sound="whip", vol=0.5)
    stk("🤔", 37.78, 38.74, SR, SY, 100)
    ev.extend(iris(tl(0.00) - 0.04))
    sfx.append(("boing", tl(0.00) - 0.06, 0.45))
    lab(0.66, 2.30, "BANTAL PELUK *PISANG*!", fill=BANANA, hi=BERRY, side="r", size=64)
    stk("🍌", 0.70, 2.30, SL, SY, 104)
    lab(2.36, 3.48, "*GEBU*NYA!", col=WHITE, fill=BLUSH, hi=CREAM, side="l", size=84, sound="sparkle", vol=0.3,
        spark=True)
    stk("☁️", 2.40, 3.48, SR, SY, 100)

    # ---- 3 sizes
    section("saiz")
    lab(3.52, 5.30, "ADA *3 SAIZ*!", fill=BANANA, hi=BERRY, side="r", size=78)
    stk("📏", 3.56, 5.30, SL, SY, 96)
    lab(5.36, 6.72, "SAIZ *70CM*", fill=CREAM, hi=BANANA_D, side="l", size=76, sound="pop", vol=0.5)
    stk("🤗", 5.40, 6.72, SR, SY, 96)
    lab(6.74, 8.44, "SAIZ *50CM*", fill=BANANA, hi=BERRY, side="r", size=76, sound="pop", vol=0.5)
    stk("🚗", 6.78, 8.44, SL, SY, 96)
    lab(8.46, 10.10, "SAIZ *35CM*", col=WHITE, fill=LEAF, hi=CREAM, side="l", size=76, sound="pop", vol=0.5)
    stk("👶", 8.50, 10.10, SR, SY, 96)

    # ---- the big one for mums
    section("mami", sound="whoosh", vol=0.35)
    lab(14.22, 15.14, "*MAMI-MAMI*?", fill=CREAM, hi=BANANA_D, side="r", size=74)
    stk("👩", 14.26, 15.14, SL, SY, 96)
    lab(15.20, 16.18, "AMBIL *PALING BESAR*", fill=BANANA, hi=BERRY, side="l", size=66)
    stk("💪", 15.24, 16.18, SR, SY, 96)
    lab(16.22, 17.48, "PELUK *WAKTU TIDUR*", col=WHITE, fill=BLUSH, hi=CREAM, side="r", size=66, spark=True)
    stk("😴", 16.26, 17.48, SL, SY, 96)

    # ---- 50cm for driving / travel
    section("drive", sound="boing")
    lab(17.98, 20.04, "TEMAN *DRIVE*", fill=CREAM, hi=BANANA_D, side="l", size=74)
    stk("🚗", 18.02, 20.04, SR, SY, 96)
    lab(20.14, 21.34, "AMBIL *50CM*", fill=BANANA, hi=BERRY, side="r", size=76, sound="pop", vol=0.5)
    stk("👌", 20.18, 21.34, SL, SY, 96)
    section("travel", sound="whoosh", vol=0.35)
    lab(23.82, 25.00, "NAIK *KERETA*?", fill=BANANA, hi=BERRY, side="l", size=74)
    stk("🛣️", 23.86, 25.00, SR, SY, 96)
    lab(25.32, 26.02, "*BALIK KAMPUNG*", col=WHITE, fill=LEAF, hi=CREAM, side="r", size=70)
    stk("🏡", 25.36, 26.02, SL, SY, 96)
    lab(26.60, 29.28, "*50CM* LEBIH SELESA", fill=CREAM, hi=BANANA_D, side="l", size=66)
    stk("😌", 26.64, 29.28, SR, SY, 96)
    lab(29.30, 30.80, "BILA *TRAVEL*", fill=BANANA, hi=BERRY, side="r", size=74)
    stk("🧳", 29.34, 30.80, SL, SY, 96)
    lab(31.30, 32.98, "*ALAS KEPALA* DALAM KERETA", col=WHITE, fill=BLUSH, hi=CREAM, side="l", size=60, spark=True)
    stk("💤", 31.34, 32.98, SR, SY, 96)

    # ---- 35cm, baby size
    section("baby", sound="boing")
    lab(33.34, 34.60, "YANG NI *35CM*", fill=CREAM, hi=BANANA_D, side="r", size=72)
    stk("🍼", 33.38, 34.60, SL, SY, 96)
    lab(34.72, 35.20, "*COMEL* JE!", col=WHITE, fill=BLUSH, hi=CREAM, side="l", size=80, sound="pop", vol=0.5)
    stk("🥰", 34.74, 35.20, SR, SY, 100)
    lab(35.22, 36.20, "SAIZ *BABY-BABY*", fill=BANANA, hi=BERRY, side="r", size=72)
    stk("👶", 35.26, 36.20, SL, SY, 96)

    # ---- gift for the kids
    section("hadiah", sound="whoosh", vol=0.35)
    lab(11.78, 12.96, "BUAT *HADIAH*", fill=CREAM, hi=BANANA_D, side="l", size=76, sound="sparkle", vol=0.3,
        spark=True)
    stk("🎁", 11.82, 12.96, SR, SY, 100)
    lab(12.96, 14.10, "UNTUK *ANAK*!", col=WHITE, fill=LEAF, hi=CREAM, side="r", size=76)
    stk("🧒", 13.00, 14.10, SL, SY, 96)

    # ---- CTA
    section("cta", sound="boing")
    lab(39.24, 40.06, "BELUM ADA *LAGI*?", fill=BANANA, hi=BERRY, side="l", size=70)
    stk("👀", 39.28, 40.06, SR, SY, 96)
    lab(40.10, 41.50, "TENGOK *BEG KUNING*", col=WHITE, fill=CHOCO, hi=BANANA, side="r", size=68, sound="bloop",
        vol=0.5)
    stk("🛒", 40.14, 41.50, SL, SY, 96)

    # ---- end card (refresh v6: a big banana ticket + stacked small tickets, inside the safe area)
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 6,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{CHOCO}\1a&HFF&\t(0,280,\1a&H90&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    bw, bh = 470, 230
    bx0, by0 = CX - bw / 2, 300
    big = ticket_path(bw, bh, 30, 18)
    ev.append(f"Dialogue: 7,{ts(e0 + 0.05)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos({bx0 + 4:.0f},{by0 + 10:.0f})\c{CHOCO}\1a&H80&\bord0\shad0\blur8\fad(150,0)\p1}}{big}{{\p0}}")
    ev.append(f"Dialogue: 7,{ts(e0 + 0.05)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\move({bx0:.0f},{by0 - 40:.0f},{bx0:.0f},{by0:.0f},0,220)\c{BANANA}\3c{CHOCO}\bord4\shad0"
              rf"\fad(150,0)\p1}}{big}{{\p0}}")
    ev.append(f"Dialogue: 8,{ts(e0 + 0.05)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\move({bx0:.0f},{by0 - 40:.0f},{bx0:.0f},{by0:.0f},0,220)\c{BROWN}\1a&H60&\bord0\shad0"
              rf"\fad(150,0)\p1}}{perforation(bw - 64, bh)} {perforation(64, bh)}{{\p0}}")
    ev.append(f"Dialogue: 9,{ts(e0 + 0.15)},{ts(TOTAL)},Bub,,0,0,0,,"
              rf"{{\an5\move({CX},{by0 + 80},{CX},{by0 + 82},0,220)\fs60\c{CHOCO}\fad(150,0)}}BANTAL PELUK")
    ev.append(f"Dialogue: 9,{ts(e0 + 0.15)},{ts(TOTAL)},Bub,,0,0,0,,"
              rf"{{\an5\move({CX},{by0 + 150},{CX},{by0 + 152},0,220)\fs84\c{BROWN}\fad(150,0)}}PISANG")
    ev.extend(ticket(e0 + 0.35, TOTAL, "*70* • *50* • *35* CM", fill=CREAM, hi=BANANA_D, side="l", y=630,
                     layer=9, size=50))
    ev.extend(ticket(e0 + 0.60, TOTAL, "KORANG NAK *SIZE MANA*?", col=WHITE, fill=BLUSH, hi=CREAM, side="r", y=725,
                     layer=9, size=50))
    ev.extend(ticket(e0 + 0.85, TOTAL, "TEKAN *BEG KUNING*", col=WHITE, fill=CHOCO, hi=BANANA, side="l", y=822,
                     layer=9, size=58))
    ev.extend(sparkles(e0 + 0.2, TOTAL, y=410, spread=240))
    bstk("🍌", e0 + 0.15, TOTAL, SR - 20, 290, 96)
    bstk("👇", e0 + 0.9, TOTAL, SL, 822, 66)
    sfx += [("boing", e0 - 0.1, 0.4), ("sparkle", e0 + 0.1, 0.35), ("whip", e0 + 0.35, 0.45),
            ("whip", e0 + 0.60, 0.45), ("ding", e0 + 0.85, 0.4)]
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
           "-filter_complex", f"[0:v][1:v]overlay=0:0:format=auto,ass={ass_path}[v]",
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
