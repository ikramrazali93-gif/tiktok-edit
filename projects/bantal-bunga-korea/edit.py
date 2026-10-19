#!/usr/bin/env python3
"""Edit for the flower cushion (bantal bunga, 50cm, "ala-ala Korea") TikTok video.

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
# One clip (IMG_2928), outdoors on grass: she shows big ribbed flower cushions (purple, beige/brown, yellow).
# v: list of (src_in, src_out, speed, zoom)
# a: 'same' (follow v at speed 1), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK (J-cut): "Ya Allah, terbaiknya! Gebunya bantal ni." over the push-in on the yellow flower's texture (end
    # of the clip), then "Saiz dia 50cm, besar macam ni!" (moved from 17.5s, "Wah masyaAllah" dropped)
    dict(name="hook", a=[(0.05, 3.62), (17.50, 19.75)], v=[(52.18, 55.75, 1, 1.0), (17.50, 19.75, 1, 1.05)]),
    # "Bantal bunga ni tu, ketebalan dia, ya Allah ya Rabbi, sedapnya peluk!"
    dict(name="tebal", a="same", v=[(3.89, 6.40, 1, 1.0), (6.40, 8.95, 1, 1.06)]),
    # "Buat bantal peluk, buat bantal dekat kerusi ofis, alas belakang, alas duduk dalam kereta,
    #  buat bantal kepala pun boleh."
    dict(name="guna", a="same", v=[(9.27, 12.10, 1, 1.0), (12.10, 14.70, 1, 1.07), (14.70, 16.50, 1, 1.0)]),
    # "Dia ada macam-macam colour."  (moved up from 36.4s; the slow "Dan dia... ada macam-macam kaler lah" cut)
    dict(name="kaler", a="same", v=[(36.39, 37.33, 1, 1.04)]),
    # "Ni colour beige, lawa estetik kan. Ni colour purple, nampak tak dia ada line-line, line putih macam ni,
    #  dia nampak lebih menyerlah bunga dia."  (the close-up of the purple flower's white piping)
    dict(name="beige", a="same", v=[(23.22, 27.30, 1, 1.0), (27.30, 32.78, 1, 1.0)]),
    # "Material dia ala-ala Korea kita. Comelnya!"  ("Okay lah" cut)
    dict(name="korea", a="same", v=[(33.28, 36.02, 1, 1.05)]),
    # "Colour-colour macam ala-ala kuning-kuning, oren macam tu. | Colour purple, colour beige, ada dark brown."
    #  ("Ini color," and the pause before "Colour purple" cut)
    dict(name="kuning", a="same", v=[(37.97, 40.58, 1, 1.0), (40.80, 43.82, 1, 1.05)]),
    # "Pink pun cantik. Korang tengok dekat beg kuning!"  ("Ya Allah macam-macam colour lah" cut; the second
    #  "tengok dekat beg kuning, harga dia sangat-sangat berbaloi" cut: no price talk)
    dict(name="cta", a="same", v=[(44.95, 47.10, 1, 1.0)]),
    # holding the yellow + purple flowers, slowed, under the flower-badge end card
    dict(name="end", a=None, v=[(47.60, 50.40, 0.85, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "bantai": "bantal", "color": "colour", "Color": "Colour"}
# hand-checked words (full-file pass + per-chunk re-transcription)
def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


OVERRIDE = {
    0.05: _w(("Ya", 0.05, 0.56), ("Allah,", 0.58, 0.86), ("terbaiknya!", 0.86, 1.72), ("Gebunya", 1.72, 2.44),
             ("bantal", 2.44, 2.86), ("ni.", 2.86, 3.40)),
    17.50: _w(("Saiz", 17.54, 17.72), ("dia", 17.72, 17.86), ("50cm,", 17.86, 18.62), ("besar", 18.88, 19.06),
              ("macam", 19.06, 19.38), ("ni!", 19.38, 19.70)),
    3.89: _w(("Bantal", 3.92, 4.38), ("bunga", 4.38, 4.74), ("ni", 4.74, 5.30), ("tu,", 5.52, 5.74),
             ("ketebalan", 5.74, 6.22), ("dia,", 6.22, 6.38)),
    6.40: _w(("ya", 6.42, 6.64), ("Allah", 6.64, 6.90), ("ya", 6.95, 7.06), ("Rabbi,", 7.06, 7.72),
             ("sedapnya", 7.74, 8.50), ("peluk!", 8.52, 8.92)),
    9.27: _w(("Buat", 9.30, 9.42), ("bantal", 9.42, 9.72), ("peluk,", 9.72, 10.36), ("buat", 10.40, 10.56),
             ("bantal", 10.56, 10.86), ("dekat", 10.86, 11.14), ("kerusi", 11.14, 11.46), ("ofis,", 11.46, 11.94)),
    12.10: _w(("alas", 12.12, 12.28), ("belakang,", 12.28, 12.94), ("alas", 13.10, 13.44), ("duduk", 13.44, 13.78),
              ("dalam", 13.78, 14.00), ("kereta,", 14.00, 14.64)),
    14.70: _w(("buat", 14.90, 15.10), ("bantal", 15.10, 15.50), ("kepala", 15.50, 16.02), ("pun", 16.02, 16.22),
              ("boleh.", 16.22, 16.44)),
    36.39: _w(("Dia", 36.42, 36.54), ("ada", 36.54, 36.68), ("macam", 36.68, 36.82), ("-macam", 36.82, 36.96),
              ("colour.", 36.96, 37.30)),
    23.22: _w(("Ni", 23.30, 23.74), ("colour", 23.74, 23.98), ("beige,", 23.98, 24.72), ("lawa", 24.96, 25.24),
              ("estetik", 25.24, 25.98), ("kan.", 25.98, 26.10), ("Ni", 26.10, 26.32), ("colour", 26.32, 26.56),
              ("purple,", 26.56, 27.16)),
    27.30: _w(("nampak", 27.32, 27.48), ("tak,", 27.48, 27.56), ("dia", 27.56, 27.68), ("ada", 27.68, 27.90),
              ("line", 27.90, 28.12), ("-line,", 28.12, 28.48), ("line", 28.48, 28.82), ("putih", 28.82, 29.24),
              ("macam", 29.24, 29.44), ("ni,", 29.44, 29.74), ("dia", 29.74, 30.02), ("nampak", 30.02, 30.54),
              ("lebih", 30.54, 30.96), ("menyerlah", 30.96, 31.66), ("bunga", 31.66, 32.08), ("dia.", 32.08, 32.40)),
    33.28: _w(("Material", 33.32, 33.60), ("dia", 33.60, 33.76), ("ala", 33.76, 34.02), ("-ala", 34.02, 34.16),
              ("Korea", 34.16, 34.50), ("kita.", 34.50, 35.00), ("Comelnya!", 35.20, 35.94)),
    37.97: _w(("Colour", 38.00, 38.20), ("-colour", 38.20, 38.34), ("macam", 38.34, 38.54), ("ala", 38.54, 38.70),
              ("-ala", 38.70, 38.88), ("kuning", 38.88, 39.14), ("-kuning,", 39.14, 39.40), ("oren", 39.40, 39.86),
              ("macam", 39.88, 40.26), ("tu.", 40.26, 40.54)),
    40.80: _w(("Colour", 40.86, 41.06), ("purple,", 41.06, 41.64), ("colour", 42.06, 42.40), ("beige,", 42.40, 42.80),
              ("ada", 43.02, 43.22), ("dark", 43.22, 43.38), ("brown.", 43.38, 43.78)),
    44.95: _w(("Pink", 45.02, 45.20), ("pun", 45.20, 45.38), ("cantik.", 45.38, 45.78), ("Korang", 45.90, 46.30),
              ("tengok", 46.30, 46.46), ("dekat", 46.46, 46.68), ("beg", 46.68, 46.82), ("kuning!", 46.82, 47.08)),
}
DROP = []
HILITE = {"GEBUNYA", "BANTAL", "BUNGA", "50CM", "BESAR", "KETEBALAN", "SEDAPNYA", "PELUK", "KERUSI", "OFIS",
          "BELAKANG", "DUDUK", "KERETA", "KEPALA", "BEIGE", "PURPLE", "LINE-LINE", "PUTIH", "MENYERLAH", "KOREA",
          "COMELNYA", "KUNING-KUNING", "OREN", "DARK", "BROWN", "PINK", "CANTIK", "BEG", "KUNING", "ESTETIK"}


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
Style: Cap,Fredoka,{CAP_FS},&H00FFFFFF,&H000000FF,&H00203048,&H64203048,-1,0,0,0,100,100,0,0,1,4,1,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Bub,Fredoka,62,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,5,40,40,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,&H00203048,&H64203048,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# palette from the cushions: espresso (dark brown centre / text), lilac (purple flower), cream (piping + beige
# flower), mustard (yellow flower), rose pink (the pink she mentions), leaf green (the grass) for accents
ESPRESSO = "&H00203048&"  # #483020
LILAC = "&H00E2A0B4&"     # #B4A0E2  active-word box, wipes, KALER PURPLE
LILAC_D = "&H00B0607A&"   # #7A60B0  highlight on cream bubbles
CREAM = "&H00E4F2FA&"     # #FAF2E4
MUSTARD = "&H003CB4F2&"   # #F2B43C  keyword caption, progress bar, flower badge
ROSE = "&H00B4A0F5&"      # #F5A0B4
LEAF = "&H0060C27A&"      # #7AC260
YELLOW = "&H003FD2FF&"    # #FFD23F  beg kuning
WHITE = "&H00FFFFFF&"
KEY = MUSTARD


def captions(words):
    """3-word chunks. Refresh v5: the active word sits on a rounded lilac box (drawn behind it, positions measured
    with Pillow) instead of changing colour or getting a blob; keywords are mustard."""
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
        yc = base_y - fs * 0.47
        for j, w in enumerate(ch):
            ws = w["s"] if j else min(w["s"], ch[0]["s"])
            we = ch[j + 1]["s"] if j + 1 < len(ch) else end
            bw, bh = widths[j] + 22, fs * 1.12
            ev.append(f"Dialogue: 1,{ts(ws)},{ts(we)},Shape,,0,0,0,,"
                      rf"{{\an5\pos({lefts[j] + widths[j] / 2:.0f},{yc:.0f})\c{LILAC}\bord3\3c{ESPRESSO}\shad0"
                      rf"\fscx80\fscy80\t(0,80,\fscx100\fscy100)\p1}}{rrect(bw, bh, 16)}{{\p0}}")
            parts = []
            for k, t in enumerate(toks):
                if k == j:
                    parts.append(t)
                elif t.strip("-") in HILITE or t in HILITE:
                    parts.append(r"{\c%s}%s{\c%s}" % (KEY, t, WHITE))   # not {\r}: it would reset \fs
                else:
                    parts.append(t)
            pop = r"\fscx88\fscy88\t(0,90,\fscx100\fscy100)" if j == 0 else ""
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


def bubble_path(w, h, r, tail=None):
    """Rounded rectangle at (0..w, 0..h) with an optional speech-bubble tail ('l', 'r' or None) built into the
    bottom edge, so the outline runs round the tail without a seam."""
    c = 0.5523 * r
    x0, y0, x1, y1 = 0, 0, w, h
    p = [("m", x0 + r, y0), ("l", x1 - r, y0), ("b", x1 - r + c, y0, x1, y0 + r - c, x1, y0 + r),
         ("l", x1, y1 - r), ("b", x1, y1 - r + c, x1 - r + c, y1, x1 - r, y1)]
    if tail:
        tx = w * (0.72 if tail == "r" else 0.28)
        lean = 10 if tail == "r" else -10
        p += [("l", tx + 16, y1), ("l", tx + lean, y1 + 24), ("l", tx - 16, y1)]
    p += [("l", x0 + r, y1), ("b", x0 + r - c, y1, x0, y1 - r + c, x0, y1 - r), ("l", x0, y0 + r),
          ("b", x0, y0 + r - c, x0 + r - c, y0, x0 + r, y0)]
    return " ".join(op + " " + " ".join(_n(v) for v in vals) for op, *vals in p)


def bubble(t0, t1, text, y=236, col=ESPRESSO, fill=CREAM, hi=LILAC_D, tail="l", layer=5, x=CX, size=62):
    """Refresh v5 label: flat speech bubble (thin espresso outline + hard offset shadow, no tilt) that slides up
    and fades in, instead of pills / stickers / tilted boxes. *word* is drawn in the highlight colour."""
    size = fit_size(text, size)
    plain = text.replace("*", "")
    w = _font(size).getlength(plain) * ASS_PER_PIL + size * 0.95
    h = size * 1.28
    parts = text.split("*")
    txt = "".join(p if i % 2 == 0 else rf"{{\c{hi}}}{p}{{\c{col}}}" for i, p in enumerate(parts))
    x0, y0 = x - w / 2, y - h / 2
    mv = lambda ax, ay: rf"\move({ax:.0f},{ay + 26:.0f},{ax:.0f},{ay:.0f},0,170)\fad(110,130)"
    return [
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
        rf"{{\an7{mv(x0, y0)}\c{fill}\3c{ESPRESSO}\bord3\4c{ESPRESSO}\4a&H40&\xshad5\yshad6\p1}}"
        f"{bubble_path(w, h, h * 0.36, tail)}{{\\p0}}",
        f"Dialogue: {layer + 1},{ts(t0)},{ts(t1)},Bub,,0,0,0,,"
        rf"{{\an5{mv(x, y)}\fs{size}\c{col}}}{txt}",
    ]


def wipe(t0, col=LILAC, layer=9, d=0.30):
    """Refresh v5 transition accent: a slanted lilac band sweeping across at a section change (no full flash)."""
    band = f"m 120 0 l 420 0 l 300 {H} l 0 {H}"
    return (f"Dialogue: {layer},{ts(t0)},{ts(t0 + d)},Shape,,0,0,0,,"
            rf"{{\an7\move(-440,0,{W + 20},0)\c{col}\1a&H50&\bord0\shad0\p1}}{band}{{\p0}}")


def flower(r=20, petals=5, rot=0.0):
    """Little flower (petal ellipses round a centre) as an ASS drawing in positive coordinates, size ~4.4r."""
    o = 2.2 * r
    out = []
    for k in range(petals):
        a = rot + 2 * np.pi * k / petals
        out.append(ell(o + r * 1.15 * np.cos(a), o + r * 1.15 * np.sin(a), r * 0.95, r * 0.95))
    return " ".join(out)


def petals(t0, x0, y0, col=LILAC, n=3, layer=4, dx=6, dy=-120):
    """Refresh v5 motif: a few small flowers twirl in and drift up the side of the frame at a section change."""
    ev = []
    for i in range(n):
        x, y = x0 + i * 34 * (1 if x0 < W / 2 else -1), y0 + i * 70
        a = t0 + i * 0.10
        cc = [col, CREAM, MUSTARD][i % 3]
        ev.append(f"Dialogue: {layer},{ts(a)},{ts(t0 + 1.6)},Shape,,0,0,0,,"
                  rf"{{\an5\move({x:.0f},{y:.0f},{x + dx:.0f},{y + dy:.0f})\c{cc}\1a&H20&\bord2\3c{WHITE}\shad0"
                  rf"\fad(80,380)\frz0\t(\frz{200 if i % 2 else -200})\fscx30\fscy30\t(0,160,\fscx100\fscy100)\p1}}"
                  f"{flower(13 - 2 * (i % 2))}{{\\p0}}")
        ev.append(f"Dialogue: {layer + 1},{ts(a)},{ts(t0 + 1.6)},Shape,,0,0,0,,"
                  rf"{{\an5\move({x:.0f},{y:.0f},{x + dx:.0f},{y + dy:.0f})\c{ESPRESSO if cc != MUSTARD else CREAM}"
                  rf"\bord0\shad0\fad(80,380)\fscx30\fscy30\t(0,160,\fscx100\fscy100)\p1}}"
                  f"{ell(9, 9, 9, 9)}{{\\p0}}")
    return ev


def badge_path(cx, cy, r_pet, d_pet, n=6, rot=0.0):
    """Big flower badge for the end card: n round petals around (cx, cy), as one ASS drawing (absolute coords)."""
    return " ".join(ell(cx + d_pet * np.cos(rot + 2 * np.pi * k / n), cy + d_pet * np.sin(rot + 2 * np.pi * k / n),
                        r_pet, r_pet) for k in range(n))


def graphics():
    ev, stickers, sfx = [], [], []
    # progress bar (retention): mustard fill on a thin lilac track, top edge
    ev.append(f"Dialogue: 7,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{LILAC}\1a&H60&\p1}}m 0 0 l {W} 0 {W} 8 0 8{{\p0}}")
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{MUSTARD}\fscx0\t(0,{int(TOTAL * 1000)},\fscx100)\p1}}m 0 0 l {W} 0 {W} 8 0 8{{\p0}}")

    def lab(s0, s1, text, sound="pluck", vol=0.55, **kw):
        ev.extend(bubble(tl(s0), tl(s1), text, **kw))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def stk(em, s0, s1, x, y, size=96):
        stickers.append((em, tl(s0), tl(s1), x, y, size))

    def bstk(em, t0, t1, x, y, size=96):
        stickers.append((em, t0, t1, x, y, size))

    def section(name, side="l", col=LILAC, sound="swish"):
        t0 = BT[name]["t0"]
        ev.append(wipe(t0 - 0.12, col=col))
        ev.extend(petals(t0, 72 if side == "l" else 565, 760, col=col))
        sfx.append((sound, t0 - 0.14, 0.35))

    SL, SR, SY = 92, 560, 150     # stickers sit above the bubble's corners, clear of the cushion

    # ---- HOOK: so good, so fluffy -> 50cm, this big
    lab(0.10, 1.70, "YA ALLAH, *TERBAIK*!", col=ESPRESSO, fill=CREAM, hi=LILAC_D, tail="l", size=66, sound="pluck_hi")
    stk("😍", 0.14, 1.70, SR, SY, 100)
    lab(1.74, 3.56, "*GEBU*NYA!", col=WHITE, fill=LILAC, hi=CREAM, tail="r", size=84, sound="pluck")
    stk("☁️", 1.78, 3.56, SL, SY, 100)
    ev.append(wipe(tl(17.50) - 0.10, col=MUSTARD))
    sfx.append(("whoosh", tl(17.50) - 0.15, 0.4))
    lab(17.56, 18.66, "SAIZ *50CM*!", col=ESPRESSO, fill=MUSTARD, hi=WHITE, tail="l", size=78, sound="pluck_hi")
    stk("📏", 17.60, 18.66, SR, SY, 96)
    lab(18.70, 19.72, "BESAR *MACAM NI*!", col=ESPRESSO, fill=CREAM, hi=LILAC_D, tail="r", size=70)
    stk("🙌", 18.74, 19.72, SL, SY, 96)

    # ---- the flower cushion, thick, nice to hug
    section("tebal", "l", LILAC)
    lab(3.92, 5.70, "BANTAL *BUNGA*", col=ESPRESSO, fill=CREAM, hi=LILAC_D, tail="l", size=70)
    stk("🌼", 3.96, 5.70, SR, SY, 100)
    lab(5.74, 7.70, "*TEBAL* & GEBU", col=WHITE, fill=LILAC, hi=CREAM, tail="r", size=70)
    stk("☁️", 5.78, 7.70, SL, SY, 96)
    lab(7.74, 8.92, "*SEDAP* PELUK!", col=ESPRESSO, fill=MUSTARD, hi=WHITE, tail="l", size=72, sound="sparkle", vol=0.3)
    stk("🤗", 7.78, 8.92, SR, SY, 100)

    # ---- uses
    section("guna", "r", MUSTARD)
    lab(9.30, 10.36, "BANTAL *PELUK*", col=ESPRESSO, fill=CREAM, hi=LILAC_D, tail="l", size=70)
    stk("🫂", 9.34, 10.36, SR, SY, 96)
    lab(10.40, 11.94, "KERUSI *OFIS*", col=WHITE, fill=LILAC, hi=CREAM, tail="r", size=70)
    stk("💼", 10.44, 11.94, SL, SY, 96)
    lab(12.12, 12.94, "ALAS *BELAKANG*", col=ESPRESSO, fill=CREAM, hi=LILAC_D, tail="l", size=68)
    stk("🪑", 12.16, 12.94, SR, SY, 96)
    lab(13.10, 14.64, "ALAS DUDUK *KERETA*", col=ESPRESSO, fill=MUSTARD, hi=WHITE, tail="r", size=66)
    stk("🚗", 13.14, 14.64, SL, SY, 96)
    lab(14.90, 16.44, "BANTAL *KEPALA*", col=WHITE, fill=LILAC, hi=CREAM, tail="l", size=70)
    stk("😴", 14.94, 16.44, SR, SY, 96)

    # ---- colours
    section("kaler", "l", ROSE, sound="whoosh")
    lab(36.45, 37.30, "MACAM-MACAM *KALER*!", col=ESPRESSO, fill=CREAM, hi=LILAC_D, tail="r", size=66, sound="sparkle", vol=0.3)
    stk("🎨", 36.48, 37.30, SL, SY, 96)
    lab(23.30, 24.92, "KALER *BEIGE*", col=ESPRESSO, fill=CREAM, hi=ESPRESSO, tail="l", size=72)
    stk("🤎", 23.34, 24.92, SR, SY, 96)
    lab(24.96, 26.08, "*LAWA* ESTETIK", col=ESPRESSO, fill=MUSTARD, hi=WHITE, tail="r", size=72)
    stk("✨", 25.00, 26.08, SL, SY, 96)
    lab(26.10, 27.20, "KALER *PURPLE*", col=WHITE, fill=LILAC, hi=CREAM, tail="l", size=72)
    stk("💜", 26.14, 27.20, SR, SY, 96)
    lab(27.90, 29.72, "ADA *LINE PUTIH*", col=ESPRESSO, fill=CREAM, hi=LILAC_D, tail="r", size=70)
    stk("🤍", 27.94, 29.72, SL, SY, 96)
    lab(30.02, 32.40, "LEBIH *MENYERLAH*!", col=WHITE, fill=LILAC, hi=CREAM, tail="l", size=68, sound="sparkle", vol=0.3)
    stk("🌟", 30.06, 32.40, SR, SY, 96)

    # ---- Korean-style material
    section("korea", "r", LILAC)
    lab(33.32, 35.00, "ALA-ALA *KOREA*", col=ESPRESSO, fill=CREAM, hi=LILAC_D, tail="r", size=72)
    stk("💫", 33.36, 35.00, SL, SY, 96)
    lab(35.20, 36.00, "*COMEL*NYA!", col=WHITE, fill=ROSE, hi=CREAM, tail="l", size=80, sound="pluck_hi")
    stk("🥰", 35.24, 36.00, SR, SY, 100)

    # ---- more colours
    section("kuning", "l", MUSTARD)
    lab(38.00, 40.54, "KALER *KUNING*", col=ESPRESSO, fill=MUSTARD, hi=WHITE, tail="l", size=72)
    stk("💛", 38.04, 40.54, SR, SY, 96)
    lab(40.86, 42.80, "*PURPLE* • *BEIGE*", col=ESPRESSO, fill=CREAM, hi=LILAC_D, tail="r", size=70)
    stk("💜", 40.90, 42.80, SL, SY, 96)
    lab(43.02, 43.80, "*DARK BROWN*", col=WHITE, fill=ESPRESSO, hi=MUSTARD, tail="l", size=72)
    stk("🤎", 43.06, 43.80, SR, SY, 96)

    # ---- pink + CTA
    lab(45.02, 45.80, "*PINK* PUN CANTIK", col=ESPRESSO, fill=ROSE, hi=WHITE, tail="r", size=70)
    stk("🩷", 45.06, 45.80, SL, SY, 96)
    lab(45.90, 47.08, "TENGOK *BEG KUNING*", col=ESPRESSO, fill=YELLOW, hi=LILAC_D, tail="l", size=68, sound="bloop", vol=0.5)
    stk("🛒", 45.94, 47.08, SR, SY, 96)

    # ---- end card (refresh v5: big mustard flower badge + stacked bubbles, inside the safe area)
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 6,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{CREAM}\1a&HFF&\t(0,280,\1a&H88&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    bx, by = CX, 420
    ev.append(f"Dialogue: 7,{ts(e0 + 0.05)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{MUSTARD}\bord4\3c{WHITE}\4c{ESPRESSO}\4a&H60&\xshad6\yshad7\fad(150,0)\p1}}"
              f"{badge_path(bx, by, 96, 128)}{{\\p0}}")
    ev.append(f"Dialogue: 8,{ts(e0 + 0.05)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{CREAM}\bord0\shad0\fad(150,0)\p1}}{ell(bx, by, 150, 150)}{{\p0}}")
    ev.append(f"Dialogue: 9,{ts(e0 + 0.15)},{ts(TOTAL)},Bub,,0,0,0,,"
              rf"{{\an5\pos({bx},{by - 30})\fs66\c{ESPRESSO}\fad(150,0)}}BANTAL")
    ev.append(f"Dialogue: 9,{ts(e0 + 0.15)},{ts(TOTAL)},Bub,,0,0,0,,"
              rf"{{\an5\pos({bx},{by + 34})\fs72\c{LILAC_D}\fad(150,0)}}BUNGA")
    ev.extend(bubble(e0 + 0.35, TOTAL, "SAIZ *50CM* • ALA-ALA KOREA", col=ESPRESSO, fill=CREAM, hi=LILAC_D,
                     tail=None, y=690, layer=9, size=46))
    ev.extend(bubble(e0 + 0.60, TOTAL, "KORANG SUKA *KALER MANA*?", col=WHITE, fill=LILAC, hi=CREAM,
                     tail=None, y=782, layer=9, size=52))
    ev.extend(bubble(e0 + 0.85, TOTAL, "TEKAN *BEG KUNING*", col=ESPRESSO, fill=YELLOW, hi=LILAC_D,
                     tail=None, y=878, layer=9, size=60))
    ev.extend(petals(e0 + 0.1, 72, 760, col=LILAC))
    bstk("👇", e0 + 0.9, TOTAL, SL, 875, 66)
    sfx += [("whoosh", e0 - 0.1, 0.4), ("sparkle", e0 + 0.1, 0.35), ("pluck", e0 + 0.35, 0.5),
            ("pluck_hi", e0 + 0.60, 0.5), ("ding", e0 + 0.85, 0.4)]
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