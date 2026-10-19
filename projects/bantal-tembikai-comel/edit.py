#!/usr/bin/env python3
"""Edit for the round watermelon plush pillow (bantal tembikai comel, 3 sizes) TikTok video, IMG_2943.

All overlays stay inside the TikTok safe zone (SAFE_* below): nothing under the
right-hand profile/like/comment/share column, the bottom caption area or the top tabs.

Needs the Fredoka Bold font (fonts/Fredoka-Bold.ttf, SIL OFL) installed, e.g. in ~/.fonts.

Usage: python3 edit.py <proxy.mp4> <transcript.json> <sfx_dir> <out_dir> [--final]
  preview: 720x1280 proxy -> preview.mp4;  --final: 1080x1920 master -> final.mp4
  --audio-only: re-mix voice + SFX onto the existing render -> *_voice.mp4

All times in BLOCKS are source times of the original clip (same timeline as
the proxy). The script builds:
  base.mp4     - cut/zoomed video + cleaned voice + SFX
  overlay.ass  - typewriter captions, chunky 3D jelly labels, music notes, wedge wipes, size-chart end card
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
VOICE_LUFS = -11.5

# ---------------------------------------------------------------- EDL
# Single source clip IMG_2943 (indoors, plush shelf behind, fried-egg daisy pillows in front): round watermelon
# plush pillows with faces, little green arms and legs, in 3 sizes (55 / 45 / 35cm). She "dances" the big one
# at the camera while singing "tain tain tain tain". Northern dialect ("hampa" = you all).
# v: list of (src_in, src_out, speed, zoom); a zoom change inside a block is a punch-in on the beat
# a: 'same' (follow v at speed 1), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK (moved from 10.8s, J-cut over her playing with the big watermelon): "Kalau anak hampa tengok, memang
    #  dia langkah tak lepas lah."  ("Ha ini ni" before it cut)
    dict(name="hook", a=[(10.78, 13.20)], v=[(6.46, 8.88, 1, 1.0)]),
    # "Tain tain tain tain. Tembikai ada tangan, ada kaki. Allah, comelnya"  (the dance; "hati ni" after it cut)
    dict(name="tain", a="same", v=[(0.00, 2.00, 1, 1.0), (2.00, 5.50, 1, 1.07)]),
    # "Dia untun/runtuh suruh beli" (13.2-14.5) is unclear -> cut.
    # "Tapi yang ni kan memang kalau nak kata pun bukan anak-anak saja minat. | Mama-mama, mami-mami pun suka
    #  (lah) dia gebu macam ni, comel-comel ni kan."
    dict(name="mama", a="same", v=[(15.12, 19.10, 1, 1.0), (19.10, 23.20, 1, 1.06)]),
    # "Ada banyak size" ("okey ni" cut) "untuk size paling besar dia size 55cm."
    dict(name="besar", a="same", v=[(23.46, 24.12, 1, 1.0), (24.52, 27.10, 1, 1.0)]),
    # "Lepas tu kita size sederhana size 45cm."
    dict(name="sedang", a="same", v=[(27.36, 30.30, 1, 1.05)]),
    # "Dan kita ada juga yang paling comel kecil comel ni." + "35cm" (the stumble "Ha ni size tiga puluh" cut)
    dict(name="kecil", a="same", v=[(30.74, 33.46, 1, 1.0), (34.84, 35.86, 1, 1.1)]),
    # ("Hmm/Ok" before it cut) "Kita tengok dia punya material dia jenis bulu-bulu fluffy, gebu."
    dict(name="bulu", a="same", v=[(36.46, 40.64, 1, 1.0)]),
    # ("Ha" cut) "Itu bahagian belakang, | bahagian depan macam ni. Bulat, montel, gebu kan."  (1s pause cut)
    dict(name="depan", a="same", v=[(41.12, 42.56, 1, 1.0), (43.44, 45.70, 1, 1.0), (45.70, 48.36, 1, 1.07)]),
    # ("Ha" cut) "Korang tengok dekat beg kuning okey."
    dict(name="cta", a="same", v=[(48.68, 50.12, 1, 1.0)]),
    # ("Ha" cut) "Ada tiga size." - end card
    dict(name="end", a="same", v=[(50.44, 51.80, 1, 1.0)]),
    dict(name="tail", a=None, v=[(51.80, 53.70, 1, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "comennya": "comelnya!", "Allah": "Allah,", "tangan": "tangan,", "back": "beg",
       "corner": "kuning", "Okey": "Okay", "hampa": "hampa,"}
# hand-checked words where Whisper drifted or misheard (re-transcribed per clip)
def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


OVERRIDE = {
    10.78: _w(("Kalau", 10.82, 11.00), ("anak", 11.00, 11.22), ("hampa", 11.22, 11.46), ("tengok,", 11.46, 11.70),
              ("memang", 11.70, 11.98), ("dia", 11.98, 12.16), ("langkah", 12.16, 12.48), ("tak", 12.48, 12.68),
              ("lepas", 12.68, 12.96), ("lah!", 12.96, 13.18)),
    41.12: _w(("Itu", 41.14, 41.58), ("bahagian", 41.58, 42.00), ("belakang,", 42.00, 42.52)),
    24.52: _w(("untuk", 24.52, 24.70), ("size", 24.70, 24.86), ("paling", 24.86, 25.06), ("besar", 25.06, 25.26),
              ("dia", 25.26, 25.46), ("size", 25.46, 25.78), ("55CM.", 25.78, 27.06)),
    27.36: _w(("Lepas", 27.40, 27.52), ("tu", 27.52, 27.62), ("kita", 27.62, 27.72), ("size", 27.72, 28.00),
              ("sederhana,", 28.00, 28.64), ("size", 28.64, 29.04), ("45CM.", 29.04, 30.24)),
    34.84: _w(("35CM!", 34.88, 35.80)),
    48.68: _w(("Korang", 48.72, 48.88), ("tengok", 48.88, 49.04), ("dekat", 49.04, 49.28), ("beg", 49.28, 49.46),
              ("kuning", 49.46, 49.60), ("okay.", 49.60, 50.04)),
    50.44: _w(("Ada", 50.46, 50.62), ("3", 50.62, 50.88), ("size!", 50.88, 51.72)),
}
DROP = []
HILITE = {"TEMBIKAI", "TANGAN", "KAKI", "COMELNYA", "ANAK", "TENGOK", "LEPAS", "MAMA-MAMA", "MAMI-MAMI", "SUKA",
          "GEBU", "COMEL-COMEL", "SIZE", "BESAR", "55CM", "SEDERHANA", "45CM", "KECIL", "COMEL", "35CM", "MATERIAL",
          "BULU-BULU", "FLUFFY", "BELAKANG", "DEPAN", "BULAT", "MONTEL", "BEG", "KUNING", "3"}

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


def bgr(hexcol):
    """'#RRGGBB' -> ASS '&H00BBGGRR&'"""
    h = hexcol.lstrip("#")
    return f"&H00{h[4:6]}{h[2:4]}{h[0:2]}&".upper()



# palette from the plushie: deep rind green for outlines / 3D extrusion, rind green, light rind, flesh pink,
# deep flesh, cream, sunshine yellow (the yellow pillows behind her), seed charcoal
RIND = bgr("#1C5E34")
GREEN = bgr("#3FA34D")
LIME = bgr("#A6DE7E")
PINK = bgr("#FF5C8A")
FLESH = bgr("#F2557A")
BLUSH = bgr("#FFC2D3")
CREAM = bgr("#FFF6E5")
SUN = bgr("#FFD54A")
SEED = bgr("#2B2B2B")
WHITE = "&H00FFFFFF&"
KEY = bgr("#FFE680")          # caption keywords: soft sunshine

ASS_HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Fredoka,56,&H00FFFFFF,&H000000FF,{RIND[:-1]},&H70345E1C,-1,0,0,0,100,100,0,0,1,5,2,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Label,Fredoka,60,&H00FFFFFF,&H000000FF,{RIND[:-1]},&H00000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: ShapeC,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

_FONTS = {}


def text_w(text, size):
    """libass width of Fredoka text at an ASS font size."""
    f = _FONTS.setdefault(size, ImageFont.truetype(FONT_FILE, size))
    return f.getlength(text) * ASS_PER_PIL


def norm(path):
    """libass aligns a drawing as if its bbox started at (0,0), so shift every path to min x/y = 0;
    with \\an5 the drawing is then centred on \\pos (paths here are built centred on 0,0)."""
    toks = path.split()
    nums = [(i, float(t)) for i, t in enumerate(toks) if t not in "mlbn"]
    xs = [v for k, (i, v) in enumerate(nums) if k % 2 == 0]
    ys = [v for k, (i, v) in enumerate(nums) if k % 2 == 1]
    mx, my = min(xs), min(ys)
    for k, (i, v) in enumerate(nums):
        toks[i] = f"{v - (mx if k % 2 == 0 else my):.1f}".rstrip("0").rstrip(".")
    return " ".join(toks)


def rrect(w, h, r):
    """Rounded rectangle path, w x h, centred on \\pos when drawn with \\an5."""
    x0, y0, x1, y1, k = -w / 2, -h / 2, w / 2, h / 2, 0.55 * r
    return norm(
        f"m {x0 + r:.0f} {y0:.0f} l {x1 - r:.0f} {y0:.0f} b {x1 - r + k:.0f} {y0:.0f} {x1:.0f} {y0 + r - k:.0f} {x1:.0f} {y0 + r:.0f} "
        f"l {x1:.0f} {y1 - r:.0f} b {x1:.0f} {y1 - r + k:.0f} {x1 - r + k:.0f} {y1:.0f} {x1 - r:.0f} {y1:.0f} "
        f"l {x0 + r:.0f} {y1:.0f} b {x0 + r - k:.0f} {y1:.0f} {x0:.0f} {y1 - r + k:.0f} {x0:.0f} {y1 - r:.0f} "
        f"l {x0:.0f} {y0 + r:.0f} b {x0:.0f} {y0 + r - k:.0f} {x0 + r - k:.0f} {y0:.0f} {x0 + r:.0f} {y0:.0f}")


def slant(w, h, s):
    """Parallelogram (badge leaning right by s px), centred on \\pos with \\an5."""
    return norm(f"m {-w / 2 + s:.0f} {-h / 2:.0f} l {w / 2 + s:.0f} {-h / 2:.0f} {w / 2 - s:.0f} {h / 2:.0f} "
                f"{-w / 2 - s:.0f} {h / 2:.0f}")


def circle(r):
    k = 0.5523 * r
    return norm(f"m 0 {-r:.0f} b {k:.0f} {-r:.0f} {r:.0f} {-k:.0f} {r:.0f} 0 b {r:.0f} {k:.0f} {k:.0f} {r:.0f} 0 {r:.0f} "
                f"b {-k:.0f} {r:.0f} {-r:.0f} {k:.0f} {-r:.0f} 0 b {-r:.0f} {-k:.0f} {-k:.0f} {-r:.0f} 0 {-r:.0f}")


HEART = norm("m 0 -6 b -6 -18 -26 -12 -20 4 b -16 14 -4 20 0 26 b 4 20 16 14 20 4 b 26 -12 6 -18 0 -6")



# eighth note: round head + stem + flag (drawn around 0,0, then normalised)
NOTE = norm("m 0 -9 b 5 -9 9 -5 9 0 b 9 5 5 9 0 9 b -5 9 -9 5 -9 0 b -9 -5 -5 -9 0 -9 "
            "m 5 -3 l 9 -3 9 -38 5 -38 "
            "m 9 -38 b 19 -34 25 -26 19 -13 b 19 -21 15 -27 9 -29")


def captions(words):
    """3-word chunks. Refresh: typewriter captions - each word only appears when she says it (the line builds up
    word by word in its final position); the word being said is watermelon pink and pops 115% -> 100%."""
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
    base_y = H - (SAFE_B + 20)                 # bottom of the caption line
    for i, ch in enumerate(chunks):
        end = ch[-1]["e"] + 0.15
        if i + 1 < len(chunks):
            end = min(end, chunks[i + 1][0]["s"])
        toks = [x["w"].upper().strip(",.") for x in ch]
        size = 56
        while text_w(" ".join(toks), size) + text_w(" ", size) * 0.8 * (len(toks) - 1) > SAFE_W - 80 and size > 36:
            size -= 2
        sp = text_w(" ", size) * 1.8
        widths = [text_w(t, size) for t in toks]
        x = CX - (sum(widths) + sp * (len(toks) - 1)) / 2
        xs = []
        for wd in widths:
            xs.append(x + wd / 2)
            x += wd + sp
        cy = base_y - size * 0.6
        for j, w in enumerate(ch):
            ws = w["s"] if j else min(w["s"], ch[0]["s"])
            we = ch[j + 1]["s"] if j + 1 < len(ch) else end
            for k in range(j + 1):            # words not said yet stay hidden
                t = toks[k]
                if k == j:
                    ev.append(f"Dialogue: 3,{ts(ws)},{ts(we)},Cap,,0,0,0,,"
                              rf"{{\an5\pos({xs[k]:.0f},{cy:.0f})\fs{size}\c{PINK}\fscx115\fscy115"
                              rf"\t(0,110,\fscx100\fscy100)}}{t}")
                else:
                    col = KEY if (t.strip("-?!") in HILITE or t in HILITE) else "&H00FFFFFF&"
                    ev.append(f"Dialogue: 2,{ts(ws)},{ts(we)},Cap,,0,0,0,,"
                              rf"{{\an5\pos({xs[k]:.0f},{cy:.0f})\fs{size}\c{col}}}{t}")
    return ev


def fit_size(text, size, max_w):
    w = text_w(text, size)
    return size if w <= max_w else int(size * max_w / w)


JELLY = (r"\fscx0\fscy0\t(0,110,\fscx120\fscy84)\t(110,200,\fscx92\fscy112)\t(200,290,\fscx104\fscy96)"
         r"\t(290,360,\fscx100\fscy100)\fad(0,120)")


def label(t0, t1, text, y=235, face=WHITE, hi=PINK, hi2=SUN, layer=5, size=64, emoji=None, stickers=None,
          esize=74, tilt=-3):
    """Refresh: no box at all - chunky 3D 'jelly' lettering. A stack of rind-green copies offset down-right
    makes a solid extrusion under a white (or pink / sunshine) face with a thick rind outline; the whole word
    pops in with a jelly squash-and-stretch wobble. *x* = hi colour, ~x~ = hi2 colour, | = new line."""
    plain = text.replace("*", "").replace("~", "")
    lines = plain.split("|")
    size = min(fit_size(ln, size, SAFE_W - 130) for ln in lines)
    tw = max(text_w(ln, size) for ln in lines)
    bh = len(lines) * size * 1.0
    cx = CX - 10
    front, mode = "", None
    for ch in text.replace("|", "\n"):
        if ch in "*~":
            mode = None if mode == ch else ch
            front += rf"{{\c{hi if mode == '*' else hi2 if mode == '~' else face}}}"
        else:
            front += r"\N" if ch == "\n" else ch
    back = plain.replace("|", r"\N")
    anim = rf"\frz{tilt}{JELLY}"
    depth = 8
    ev = []
    for d in range(depth, 0, -1):
        ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t1)},Label,,0,0,0,,"
                  rf"{{\an5\pos({cx + d * 1.0:.1f},{y + d * 1.3:.1f})\fs{size}\c{RIND}\3c{RIND}\bord6\q2{anim}}}{back}")
    ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t1)},Label,,0,0,0,,"
              rf"{{\an5\pos({cx},{y})\fs{size}\c{face}\3c{RIND}\bord5\q2{anim}}}{front}")
    if emoji and stickers is not None:
        stickers.append((emoji, t0 + 0.2, t1, cx + tw / 2 + esize * 0.45, y - bh / 2 - 6, esize))
    return ev


def notes(t0, y=235, layer=4):
    """Refresh motif: little music notes (her 'tain tain tain' song) float up and sway around the label."""
    ev = []
    for i, (dx, dy) in enumerate(((-240, 30), (215, 50), (-180, -50), (235, -40), (-90, 70))):
        x, yy = CX + dx, y + dy
        d0 = 70 * i
        col = (PINK, GREEN, SUN)[i % 3]
        sc = 80 + 20 * (i % 2)
        ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t0 + 1.4)},ShapeC,,0,0,0,,"
                  rf"{{\move({x:.0f},{yy:.0f},{x + (18 if i % 2 else -18):.0f},{yy - 95:.0f},{d0},1400)\c{col}"
                  rf"\3c&HFFFFFF&\bord2\frz{-12 if i % 2 else 12}\t({d0},1400,\frz{10 if i % 2 else -10})"
                  rf"\fscx0\fscy0\t({d0},{d0 + 150},\fscx{sc + 20}\fscy{sc + 20})\t({d0 + 150},{d0 + 250},\fscx{sc}\fscy{sc})"
                  rf"\fad(0,400)\p1}}{NOTE}{{\p0}}")
    return ev


def wedge_wipe(t0, layer=9):
    """Refresh transition: like cutting a round watermelon - 8 pie wedges (flesh pink / rind green) appear one
    after another clockwise around the centre until the frame is covered, then the whole pie fades (~0.35s)."""
    import math
    cx, cy, r = W / 2, H / 2, 1600
    ev = []
    for i in range(8):
        a0 = math.radians(-90 + 45 * i)
        a1 = math.radians(-90 + 45 * (i + 1))
        am = (a0 + a1) / 2
        pts = [(cx, cy)] + [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in (a0, am, a1)]
        clip = "m {:.0f} {:.0f} l {:.0f} {:.0f} {:.0f} {:.0f} {:.0f} {:.0f}".format(*[v for p in pts for v in p])
        col = FLESH if i % 2 == 0 else GREEN
        st = t0 - 0.2 + 0.022 * i
        ev.append(f"Dialogue: {layer},{ts(st)},{ts(t0 + 0.16)},Shape,,0,0,0,,"
                  rf"{{\an7\pos(0,0)\c{col}\1a&H10&\clip({clip})\fad(0,140)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    return ev


def graphics():
    ev, stickers, sfx = [], [], []
    # progress bar (retention): rind track, flesh-pink fill with a lime 'rind' edge underneath
    ms = int(TOTAL * 1000)
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{RIND}\1a&H40&\p1}}m 0 0 l {W} 0 {W} 12 0 12{{\p0}}")
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{PINK}\clip(0,0,0,12)\t(0,{ms},\clip(0,0,{W},12))\p1}}m 0 0 l {W} 0 {W} 9 0 9{{\p0}}")
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{LIME}\clip(0,0,0,12)\t(0,{ms},\clip(0,0,{W},12))\p1}}m 0 9 l {W} 9 {W} 12 0 12{{\p0}}")

    def lab(s0, s1, text, sound="jelly", vol=0.5, music=False, **kw):
        ev.extend(label(tl(s0), tl(s1), text, stickers=stickers, **kw))
        if music:
            ev.extend(notes(tl(s0), y=kw.get("y", 235)))
            sfx.append(("note", tl(s0) + 0.05, 0.3))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def wipe(src, sound="slice", vol=0.55):
        t0 = tl(src)
        ev.extend(wedge_wipe(t0))
        sfx.append((sound, t0 - 0.2, vol))

    # ---- HOOK: kids can't walk past it
    lab(10.80, 12.00, "ANAK HAMPA|*TENGOK*?", emoji="👀", size=70)
    lab(12.00, 13.18, "MEMANG|*TAK LEPAS*!", face=SUN, emoji="🤩", music=True, size=70, tilt=3)

    # ---- the dance
    wipe(0.02)
    lab(0.06, 1.86, "TAIN TAIN *TAIN*!", emoji="🎶", music=True, sound="note", vol=0.45)
    lab(2.06, 4.40, "ADA *TANGAN*|& *KAKI*!", emoji="🙌", tilt=3)
    lab(4.62, 5.46, "COMELNYA!", face=PINK, emoji="🥰", size=74)

    # ---- not just for kids
    wipe(15.12)
    lab(15.20, 18.86, "BUKAN *ANAK-ANAK*|SAJA MINAT", emoji="🧒")
    lab(19.18, 20.80, "*MAMA-MAMA*|PUN SUKA!", face=SUN, hi=PINK, emoji="👩", tilt=3)
    lab(21.26, 23.16, "GEBU & *COMEL*!", emoji="☁️", music=True)

    # ---- 3 sizes
    wipe(23.46)
    lab(23.50, 24.12, "ADA *3 SIZE*!", face=SUN, hi=PINK, emoji="🍉", size=72)
    lab(24.70, 27.06, "PALING BESAR|*55CM*", emoji="🍉", esize=96, tilt=3)
    lab(27.70, 30.24, "SEDERHANA|*45CM*", emoji="🍉", esize=80)
    lab(31.40, 33.44, "PALING *KECIL*|& COMEL", emoji="🥹", tilt=3)
    lab(34.88, 35.84, "*35CM*!", size=84, emoji="🍉", esize=62)

    # ---- material
    wipe(36.46)
    lab(36.50, 38.46, "JOM TENGOK|*MATERIAL*", emoji="🔍")
    lab(38.48, 39.82, "BULU-BULU|*FLUFFY*", face=SUN, hi=PINK, emoji="☁️", tilt=3)
    lab(40.08, 40.62, "GEBU!", face=PINK, size=84, emoji="🤗", music=True)

    # ---- back + front
    lab(41.14, 42.54, "*BELAKANG*", emoji="🔄", sound="pop", vol=0.45)
    lab(43.48, 45.68, "*DEPAN* MACAM NI", emoji="😊", tilt=3)
    lab(45.76, 48.34, "BULAT • *MONTEL*|• GEBU!", face=SUN, hi=PINK, emoji="🍉", music=True)

    # ---- CTA
    wipe(48.68)
    lab(48.72, 50.10, "TENGOK|*BEG KUNING*", face=SUN, hi=PINK, emoji="🛒", sound="ding", vol=0.4)

    # ---- end card (refresh): a cream 'size chart' board with three watermelons growing 35 -> 45 -> 55
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 6,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{RIND}\1a&HFF&\t(0,250,\1a&H70&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    ev.extend(label(e0 + 0.05, TOTAL, "TEMBIKAI *COMEL*", y=230, layer=9, size=60, emoji="🍉", stickers=stickers))
    by = 520
    pop = r"\fscx0\fscy0\t(0,180,\fscx106\fscy106)\t(180,260,\fscx100\fscy100)"
    ev.append(f"Dialogue: 8,{ts(e0 + 0.2)},{ts(TOTAL)},ShapeC,,0,0,0,,{{\\pos({CX + 8},{by + 10})\\c{RIND}\\1a&H30&{pop}\\p1}}{rrect(580, 300, 40)}{{\\p0}}")
    ev.append(f"Dialogue: 8,{ts(e0 + 0.2)},{ts(TOTAL)},ShapeC,,0,0,0,,{{\\pos({CX},{by})\\c{CREAM}\\3c{RIND}\\bord6{pop}\\p1}}{rrect(580, 300, 40)}{{\\p0}}")
    ev.append(f"Dialogue: 9,{ts(e0 + 0.3)},{ts(TOTAL)},Label,,0,0,0,,{{\\an5\\pos({CX},{by - 112})\\fs32\\c{RIND}\\fad(150,0)}}PILIH SIZE KORANG:")
    for i, (r, lab_txt, dx) in enumerate(((40, "35CM", -180), (54, "45CM", -10), (68, "55CM", 175))):
        x, yc = CX + dx, by + 20 - (r - 40) * 0.6
        t = e0 + 0.45 + 0.2 * i
        bounce = r"\fscx0\fscy0\t(0,150,\fscx118\fscy118)\t(150,260,\fscx100\fscy100)"
        ev.append(f"Dialogue: 9,{ts(t)},{ts(TOTAL)},ShapeC,,0,0,0,,{{\\pos({x},{yc:.0f})\\c{GREEN}\\3c{RIND}\\bord3{bounce}\\p1}}{circle(r + 9)}{{\\p0}}")
        ev.append(f"Dialogue: 10,{ts(t)},{ts(TOTAL)},ShapeC,,0,0,0,,{{\\pos({x},{yc:.0f})\\c{LIME}{bounce}\\p1}}{circle(r + 3)}{{\\p0}}")
        ev.append(f"Dialogue: 11,{ts(t)},{ts(TOTAL)},ShapeC,,0,0,0,,{{\\pos({x},{yc:.0f})\\c{FLESH}{bounce}\\p1}}{circle(r)}{{\\p0}}")
        for sx, sy in ((-0.35, -0.2), (0.3, -0.3), (0.0, 0.25), (-0.25, 0.3), (0.35, 0.15)):
            ev.append(f"Dialogue: 12,{ts(t + 0.1)},{ts(TOTAL)},ShapeC,,0,0,0,,"
                      rf"{{\pos({x + sx * r:.0f},{yc + sy * r:.0f})\c{SEED}\fscy150\fad(120,0)\p1}}{circle(3)}{{\p0}}")
        ev.append(f"Dialogue: 12,{ts(t)},{ts(TOTAL)},Label,,0,0,0,,{{\\an5\\pos({x},{by + 112})\\fs34\\c{FLESH}\\3c{RIND}\\bord0{bounce}}}{lab_txt}")
        sfx.append(("pop", t, 0.45 + 0.05 * i))
    ev.extend(label(e0 + 1.0, TOTAL, "SATU FAMILY, *3 SIZE*!", y=745, face=SUN, hi=PINK, layer=9, size=46,
                    emoji="🥰", stickers=stickers, esize=62))
    ev.extend(label(e0 + 1.3, TOTAL, "TEKAN *BEG KUNING*", y=840, layer=9, size=48, emoji="🛒", stickers=stickers,
                    esize=62, tilt=3))
    ev.extend(notes(e0 + 0.1, y=240, layer=8))
    ev.extend(wedge_wipe(e0, layer=13))
    sfx += [("slice", e0 - 0.2, 0.5), ("jelly", e0 + 0.05, 0.5), ("note", e0 + 0.15, 0.3), ("pop", e0 + 0.2, 0.4),
            ("jelly", e0 + 1.0, 0.45), ("ding", e0 + 1.3, 0.4)]
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
           "-filter_complex", f"[0:v]ass={ass_path}[a];[a][1:v]overlay=0:0:format=auto[v]",   # emoji are corner stickers on the badges, so above the ASS
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
