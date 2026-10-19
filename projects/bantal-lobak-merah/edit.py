#!/usr/bin/env python3
"""Edit for the carrot plush pillow (bantal carrot / lobak merah, IMG_2934: outdoors) TikTok video.

Refreshed "kebun" (vegetable garden) look, different from the other batch-4 edits:
swinging hang-tag labels on a string, the active caption word grows and turns sunny yellow,
carrot-leaf sprouts growing up from the bottom of the safe area at each section, an orange
circle-reveal transition, a seed-row progress bar (dots light up one by one), and a wooden
garden-sign end card.

All overlays stay inside the TikTok safe zone (SAFE_* below): nothing under the
right-hand profile/like/comment/share column, the bottom caption area or the top tabs.

Needs the Fredoka Bold font (fonts/Fredoka-Bold.ttf, SIL OFL) installed, e.g. in ~/.fonts.

Usage: python3 edit.py <proxy.mp4> <transcript.json> <sfx_dir> <out_dir> [--final]
  preview: 720x1280 proxy -> preview.mp4;  --final: 1080x1920 master -> final.mp4
  --audio-only: re-mix voice + SFX onto the existing render -> *_voice.mp4

All times in BLOCKS are source times of the original clip (same timeline as
the proxy). The script builds:
  base.mp4     - cut/zoomed video + cleaned voice + SFX
  overlay.ass  - captions, labels, sprouts, progress dots, end card
  preview.mp4  - base + ASS + colour emoji stickers (rendered with Pillow)
"""
import json, math, os, subprocess, sys
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
# v: list of (src_in, src_out, speed, zoom)
# a: 'same' (follow v at speed 1), None (silence) or list of (src_in, src_out)
# Price lines are cut (no prices): "Sekarang ni seller tengah bagi harga yang sangat-sangat promo,
# jimat" (15.9-20.3) and "Harga dia sangat-sangat jimat. Memang berbaloi." (38.5-40.7).
BLOCKS = [
    # HOOK (moved from 9.8s): "Dia ada 2 jenis senyuman. Ada senyuman ada gigi. Ada senyuman yang tanpa gigi."
    # J-cut over the face close-ups: smiling face -> the face with teeth -> the small one without
    dict(name="hook", a=[(9.72, 14.72)],
         v=[(24.00, 25.56, 1, 1.0), (26.00, 27.55, 1, 1.0), (28.00, 29.89, 1, 1.0)]),
    # "Ya Allah, comelnya. Carrot ni gebu-gebu ya. Kita ada 3 size, 90cm, 70cm dan juga 50cm."  ("Ok" after it cut)
    dict(name="comel", a="same", v=[(0.00, 3.50, 1, 1.0), (3.50, 6.25, 1, 1.1), (6.25, 9.33, 1, 1.0)]),
    # "Korang boleh pilih."
    dict(name="pilih", a="same", v=[(15.00, 15.84, 1, 1.12)]),
    # "Kalau ni kita boleh buat bantal peluk atau tidur, yang besar ni. Kalau yang ni boleh buat travel,
    # yang kecil ni untuk bayi-bayi. Kan, comel ni."
    dict(name="guna", a="same", v=[(29.62, 32.62, 1, 1.0), (32.62, 36.40, 1, 1.08), (36.40, 38.22, 1, 1.0)]),
    # "Material dia material kain velvet. Macam ni material dia tahan lasak. Kaler dia tak pudar dan dia
    # tak berbulu."  (breath before "Macam" cut)
    dict(name="material", a="same", v=[(43.58, 45.50, 1, 1.0), (45.94, 50.30, 1, 1.06)]),
    # "Dan korang boleh beli banyak-banyak. Borong buat hadiah untuk anak buah, anak korang, anak murid,
    # semua anak-anak boleh kan. Nah, mami-mami pun boleh."  (0.45s pause after "korang" cut)
    # visuals: her with all three, then the unused standing shot from the cut price line
    dict(name="hadiah", a=[(20.72, 25.36), (25.80, 29.38)],
         v=[(20.72, 24.30, 1, 1.0), (38.30, 42.94, 1, 1.08)]),
    # holding all three to the camera - end card
    dict(name="end", a=None, v=[(50.40, 53.05, 1, 1.0)]),
]

FIX = {"comennya": "comelnya", "-gebas": "-gebu", "bantai": "bantal", "tidong": "tidur", "Kala": "Kaler",
       "Ini": "Ni", "ini": "ni"}
def _w(*ws):
    return [dict(w=w, s=a, e=b) for w, a, b in ws]


OVERRIDE = {}
DROP = []
HILITE = {"CARROT", "GEBU", "GEBU-GEBU", "3", "SIZE", "90CM", "70CM", "50CM", "2", "SENYUMAN", "GIGI", "TANPA",
          "PILIH", "PELUK", "TIDUR", "TRAVEL", "BAYI-BAYI", "COMEL", "VELVET", "LASAK", "PUDAR", "BERBULU",
          "BANYAK-BANYAK", "HADIAH", "MURID", "MAMI-MAMI", "BORONG"}

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


CAP_SIZE = 58
CAP_MV = SAFE_B + 20                      # caption bottom margin
ASS_HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Fredoka,{CAP_SIZE},&H00FFFFFF,&H000000FF,&H00293A5B,&H64293A5B,-1,0,0,0,100,100,0,0,1,5,3,2,{SAFE_L},{SAFE_R},{CAP_MV},1
Style: Tag,Fredoka,60,&H00293A5B,&H000000FF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,&H00293A5B,&H64293A5B,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# garden palette (ASS colours are BGR): carrot orange, leaf green (the pale leaves), deep leaf green,
# soil brown, cream, sunny yellow, light wood for the sign
CARROT = "&H002F6EFF&"   # #FF6E2F
LEAF = "&H008BE37C&"     # #7CE38B
DEEP = "&H003A6B1F&"     # #1F6B3A
SOIL = "&H00293A5B&"     # #5B3A29
CREAM = "&H00E5F6FF&"    # #FFF6E5
SUN = "&H0066D1FF&"      # #FFD166
WOOD = "&H007AB0E3&"     # #E3B07A
WOOD_D = "&H00335A8A&"   # #8A5A33
WHITE = "&H00FFFFFF&"

_PIL = {}


def text_w(text, size):
    """Width in ASS px of text set in Fredoka at `size`."""
    f = _PIL.setdefault(size, ImageFont.truetype(FONT_FILE, size))
    return f.getlength(text) * ASS_PER_PIL


def captions(words):
    """3-word chunks; the active word grows a little and turns sunny yellow, keywords pale leaf green."""
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
    for i, ch in enumerate(chunks):
        end = ch[-1]["e"] + 0.15
        if i + 1 < len(chunks):
            end = min(end, chunks[i + 1][0]["s"])
        toks = [x["w"].upper().strip(",.") for x in ch]
        line = " ".join(toks)
        full = text_w(line, CAP_SIZE) * 1.06          # room for the enlarged active word
        fs = CAP_SIZE if full <= SAFE_W - 40 else int(CAP_SIZE * (SAFE_W - 40) / full)
        for j, w in enumerate(ch):
            ws = w["s"] if j else min(w["s"], ch[0]["s"])
            we = ch[j + 1]["s"] if j + 1 < len(ch) else end
            parts = []
            for k, t in enumerate(toks):
                if k == j:
                    parts.append(r"{\c%s\3c%s\fscx100\fscy100\t(0,90,\fscx116\fscy116)}%s{\c%s\3c%s\fscx100\fscy100}"
                                 % (SUN, DEEP, t, WHITE, SOIL))
                elif t.strip("-?!") in HILITE or t in HILITE:
                    parts.append(r"{\c%s}%s{\c%s}" % (LEAF, t, WHITE))
                else:
                    parts.append(t)
            pop = r"{\fscx85\fscy85\t(0,90,\fscx100\fscy100)}" if j == 0 else ""
            ev.append(f"Dialogue: 2,{ts(ws)},{ts(we)},Cap,,0,0,0,,{pop}{{\\fs{fs}}}" + " ".join(parts))
    return ev


def fit_size(text, size, max_w):
    plain = text.replace("*", "")
    w = text_w(plain, size)
    return size if w <= max_w else int(size * max_w / w)


def place(path, cx, cy):
    """libass anchors a drawing at its (0,0) origin, so shift a centred path to positive
    coordinates and return it with the top-left position that puts its (0,0) centre at (cx, cy)."""
    toks = path.split()
    nums = [(i, float(t)) for i, t in enumerate(toks) if t not in ("m", "l", "b")]
    xs = [v for k, (i, v) in enumerate(nums) if k % 2 == 0]
    ys = [v for k, (i, v) in enumerate(nums) if k % 2 == 1]
    mx, my = min(xs), min(ys)
    for k, (i, v) in enumerate(nums):
        toks[i] = f"{v - (mx if k % 2 == 0 else my):.0f}"
    return " ".join(toks), cx + mx, cy + my


def circle(r, n=24):
    pts = [(r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    return f"m {pts[0][0]:.0f} {pts[0][1]:.0f} " + " ".join(f"l {x:.0f} {y:.0f}" for x, y in pts[1:])


def tag_path(w, h):
    """Hang tag centred on (0,0): pointed left end, rounded right corners."""
    x0, x1, y0, y1 = -w / 2, w / 2, -h / 2, h / 2
    tip = h * 0.42
    r = h * 0.22
    return (f"m {x0 - tip:.0f} 0 l {x0:.0f} {y0:.0f} l {x1 - r:.0f} {y0:.0f} b {x1:.0f} {y0:.0f} {x1:.0f} {y0:.0f} "
            f"{x1:.0f} {y0 + r:.0f} l {x1:.0f} {y1 - r:.0f} b {x1:.0f} {y1:.0f} {x1:.0f} {y1:.0f} {x1 - r:.0f} {y1:.0f} "
            f"l {x0:.0f} {y1:.0f} l {x0 - tip:.0f} 0")


def hang_tag(t0, t1, text, y=820, col=SOIL, fill=CREAM, hi=CARROT, x=CX, size=60, layer=5, side=1,
             max_w=SAFE_W - 110):
    """Hang-tag label on a string, gently swinging from the string's top. *word* uses the highlight colour.
    Every piece rotates about the same \\org so the tag, hole, string and text swing together."""
    if fill == SUN and hi == CARROT:      # orange on yellow is too weak - use deep leaf green
        hi = DEEP
    size = fit_size(text, size, max_w - size * 0.8)
    plain = text.replace("*", "")
    tw = text_w(plain, size)
    h = size * 1.34
    w = tw + size * 0.9
    tip = h * 0.42
    hole_x = -w / 2 + h * 0.05
    top_x, top_y = x + hole_x - side * 30, y - h / 2 - 95        # where the string is "pinned"
    a = 4.5 * side
    d = int((t1 - t0) * 1000)
    swing = (rf"\org({top_x:.0f},{top_y:.0f})\frz{a:.1f}\t(0,380,\frz{-a * 0.7:.1f})\t(380,760,\frz{a * 0.45:.1f})"
             rf"\t(760,1150,\frz{-a * 0.25:.1f})\t(1150,{max(1500, d)},\frz0)")
    fade = r"\fad(110,150)"
    body = "".join(p if i % 2 == 0 else rf"{{\c{hi}}}{p}{{\c{col}}}" for i, p in enumerate(text.split("*")))

    def shape(path, cx, cy, tags):
        pth, px, py = place(path, x + cx, y + cy)
        return (f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
                rf"{{\an7\pos({px:.0f},{py:.0f}){swing}{fade}{tags}\p1}}{pth}{{\p0}}")

    # string: a thin slightly curved band from the pin down to the hole
    sx0, sy0 = top_x - x, top_y - y
    sx1, sy1 = hole_x, 0
    string = (f"m {sx0 - 1.5:.0f} {sy0:.0f} b {sx0 + 10:.0f} {(sy0 + sy1) / 2:.0f} {sx1 - 8:.0f} {(sy0 + sy1) / 2:.0f} "
              f"{sx1 - 1.5:.0f} {sy1:.0f} l {sx1 + 1.5:.0f} {sy1:.0f} b {sx1 - 5:.0f} {(sy0 + sy1) / 2:.0f} "
              f"{sx0 + 13:.0f} {(sy0 + sy1) / 2:.0f} {sx0 + 1.5:.0f} {sy0:.0f}")
    tp = tag_path(w, h)
    spth, spx, spy = _abs_place(string, x, y)
    return [
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
        rf"{{\an7\pos({spx:.0f},{spy:.0f}){swing}{fade}\c{SOIL}\p1}}{spth}{{\p0}}",
        shape(tp, 5, 7, rf"\c{SOIL}\1a&H48&"),
        shape(tp, 0, 0, rf"\c{fill}\3c{SOIL}\bord3"),
        shape(circle(size * 0.12, 16), hole_x, 0, rf"\c{SOIL}"),
        shape(circle(size * 0.12 + 4, 16), hole_x, 0, rf"\c{WHITE}\1a&HFF&\3c{WOOD_D}\bord2"),
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},Tag,,0,0,0,,{{\\an5\\pos({x + tip * 0.35:.0f},{y + 2:.0f}){swing}{fade}"
        f"\\fs{size}\\c{col}}}{body}",
    ]


def _abs_place(path, x, y):
    """Like place(), for a path whose coordinates are already relative to (x, y) (not centred)."""
    toks = path.split()
    nums = [(i, float(t)) for i, t in enumerate(toks) if t not in ("m", "l", "b")]
    xs = [v for k, (i, v) in enumerate(nums) if k % 2 == 0]
    ys = [v for k, (i, v) in enumerate(nums) if k % 2 == 1]
    mx, my = min(xs), min(ys)
    for k, (i, v) in enumerate(nums):
        toks[i] = f"{v - (mx if k % 2 == 0 else my):.0f}"
    return " ".join(toks), x + mx, y + my


LEAF_PATH = "m 0 0 b -16 -22 -20 -52 0 -84 b 20 -52 16 -22 0 0"


def sprouts(t0, x, layer=4, dur=1.3):
    """A carrot-leaf sprout growing up from the bottom edge of the safe area."""
    ev = []
    base_y = H - SAFE_B - 95            # between the tags and the caption line
    for k, (rot, sc, col) in enumerate([(-28, 0.85, LEAF), (0, 1.1, LEAF), (26, 0.8, LEAF)]):
        pth, px, py = place(LEAF_PATH, x, base_y)
        # anchor: the path's (0,0) (leaf base) sits at (x, base_y)
        ev.append(f"Dialogue: {layer},{ts(t0 + k * 0.05)},{ts(t0 + dur)},Shape,,0,0,0,,"
                  rf"{{\an7\pos({px:.0f},{py:.0f})\org({x},{base_y})\frz{rot}\c{col}\3c{DEEP}\bord3"
                  rf"\fscx{sc * 100:.0f}\fscy0\t(0,260,\fscy{sc * 100:.0f})\fad(0,220)\p1}}{pth}{{\p0}}")
    return ev


def iris(t0, layer=7):
    """Orange circle-reveal accent between sections."""
    pth = circle(820, 32)
    return [f"Dialogue: {layer},{ts(t0)},{ts(t0 + 0.38)},Shape,,0,0,0,,"
            rf"{{\an5\pos({W // 2},{H // 2})\c{CARROT}\1a&H30&\fscx0\fscy0\t(0,190,\fscx100\fscy100)"
            rf"\t(170,380,\1a&HFF&)\p1}}{pth}{{\p0}}"]


def seed_row():
    """Progress bar as a row of seeds: faint dots, each lights up carrot-orange as time passes."""
    ev = []
    n = 22
    step = W / n
    for i in range(n):
        cx = step * (i + 0.5)
        pth, px, py = place(circle(5.5, 12), cx, 10)
        ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
                  rf"{{\an7\pos({px:.0f},{py:.0f})\c{SOIL}\1a&H70&\p1}}{pth}{{\p0}}")
        ton = TOTAL * i / n
        ev.append(f"Dialogue: 8,{ts(ton)},{ts(TOTAL)},Shape,,0,0,0,,"
                  rf"{{\an7\pos({px:.0f},{py:.0f})\org({cx:.0f},10)\c{CARROT}\3c{CREAM}\bord1.5"
                  rf"\fscx40\fscy40\t(0,160,\fscx125\fscy125)\t(160,260,\fscx100\fscy100)\p1}}{pth}{{\p0}}")
    return ev


def plank(t0, t1, text, y, w=None, size=56, col=SOIL, hi=CARROT, layer=9, tilt=0):
    """A wooden garden-sign plank (drops in), with grain lines; *word* in the highlight colour."""
    size = fit_size(text, size, SAFE_W - 90)
    tw = text_w(text.replace("*", ""), size)
    w = w or tw + size * 1.2
    h = size * 1.45
    body = "".join(p if i % 2 == 0 else rf"{{\c{hi}}}{p}{{\c{col}}}" for i, p in enumerate(text.split("*")))
    rect = f"m {-w / 2:.0f} {-h / 2:.0f} l {w / 2:.0f} {-h / 2:.0f} l {w / 2:.0f} {h / 2:.0f} l {-w / 2:.0f} {h / 2:.0f}"
    grain = " ".join(f"m {-w / 2 + 14:.0f} {gy:.0f} l {w / 2 - 14:.0f} {gy:.0f} l {w / 2 - 14:.0f} {gy + 2:.0f} "
                     f"l {-w / 2 + 14:.0f} {gy + 2:.0f}" for gy in (-h * 0.30, h * 0.30))
    mv =rf"\move({CX},{y - 70},{CX},{y},0,220)"
    ev = []
    for path, tags in ((rect, rf"\c{SOIL}\1a&H50&"), (rect, rf"\c{WOOD}\3c{WOOD_D}\bord4"),
                       (grain, rf"\c{WOOD_D}\1a&H90&")):
        pth, px, py = place(path, CX, y)
        off = (6, 7) if tags.endswith("&H50&") else (0, 0)
        ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
                  rf"{{\an7\move({px + off[0]:.0f},{py - 70 + off[1]:.0f},{px + off[0]:.0f},{py + off[1]:.0f},0,220)"
                  rf"\org({CX},{y})\frz{tilt}\fad(100,0){tags}\p1}}{pth}{{\p0}}")
    for nx in (-w / 2 + 16, w / 2 - 16):
        pth, px, py = place(circle(4.5, 10), CX + nx, y)
        ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
                  rf"{{\an7\move({px:.0f},{py - 70:.0f},{px:.0f},{py:.0f},0,220)\org({CX},{y})\frz{tilt}"
                  rf"\fad(100,0)\c{WOOD_D}\p1}}{pth}{{\p0}}")
    ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t1)},Tag,,0,0,0,,{{\\an5{mv}\\org({CX},{y})\\frz{tilt}\\fad(100,0)"
              f"\\fs{size}\\c{col}}}{body}")
    return ev


def garden_sign(t0, t1):
    """End card: soft leaf-green wash, a wooden stake and planks dropping in one by one."""
    ev = [f"Dialogue: 8,{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
          rf"{{\an7\pos(0,0)\c{DEEP}\1a&HFF&\t(0,250,\1a&H58&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}"]
    stake = f"m -16 0 l 16 0 l 16 560 l 0 600 l -16 560"
    pth, px, py = place(stake, CX, 300)
    ev.append(f"Dialogue: 9,{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
              rf"{{\an7\pos({px:.0f},{py:.0f})\c{WOOD_D}\3c{SOIL}\bord3\fad(150,0)\p1}}{pth}{{\p0}}")
    return ev


def graphics():
    ev, stickers, sfx = [], [], []
    LY = 830                       # tags hang over the carrot bodies, clear of the carrot faces
    ev += seed_row()

    def lab(s0, s1, text, sound="tick", vol=0.5, **kw):
        kw.setdefault("y", LY)
        ev.extend(hang_tag(tl(s0), tl(s1), text, **kw))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def stk(em, s0, s1, x, y=690, size=96):
        stickers.append((em, tl(s0), tl(s1), x, y, size))

    def bstk(em, t0, t1, x, y, size=100):
        stickers.append((em, t0, t1, x, y, size))

    def section(name, sound="swish", vol=0.35, iris_on=True):
        t0 = BT[name]["t0"]
        if iris_on and t0 > 0:
            ev.extend(iris(t0 - 0.12))
        ev.extend(sprouts(t0 + 0.05, SAFE_L + 46))
        ev.extend(sprouts(t0 + 0.15, W - SAFE_R - 46))
        sfx.append((sound, max(0, t0 - 0.06), vol))
        sfx.append(("sprout", t0 + 0.05, 0.4))

    SL, SR = 95, 545
    side = [1]

    def flip():
        side[0] = -side[0]
        return side[0]

    # ---- HOOK: two kinds of smile
    section("hook", iris_on=False)
    lab(9.98, 11.28, "2 JENIS *SENYUMAN*!", fill=SUN, side=flip(), sound="boing", vol=0.5)
    stk("😊", 10.02, 11.28, SR)
    lab(11.30, 12.84, "ADA *GIGI*!", fill=CREAM, size=72, side=flip(), sound="boing", vol=0.5)
    stk("🦷", 11.34, 12.84, SL)
    lab(12.90, 14.70, "*TANPA* GIGI", fill=CREAM, hi=DEEP, size=72, side=flip(), sound="pop", vol=0.5)
    stk("😌", 12.94, 14.70, SR)

    # ---- so cute, 3 sizes
    section("comel")
    lab(0.30, 1.50, "*COMELNYA*!", fill=CREAM, side=flip())
    stk("🥕", 0.34, 1.50, SR)
    lab(1.54, 3.44, "*GEBU-GEBU*", fill=SUN, side=flip())
    stk("☁️", 1.58, 3.44, SL)
    lab(3.56, 4.70, "ADA *3 SIZE*", fill=CREAM, side=flip(), sound="ding", vol=0.35)
    lab(4.90, 6.28, "*90CM*", fill=SUN, size=78, side=flip(), sound="bloop", vol=0.5)
    stk("📏", 4.94, 6.28, SR)
    lab(6.30, 7.06, "*70CM*", fill=CREAM, size=74, side=flip(), sound="bloop", vol=0.5)
    lab(7.08, 9.30, "*50CM*", fill=SUN, size=70, side=flip(), sound="bloop", vol=0.5)
    stk("🥕", 7.12, 9.30, SL)

    # ---- you choose
    lab(15.02, 15.84, "KORANG *PILIH*!", fill=CREAM, hi=DEEP, side=flip(), sound="pop", vol=0.5)
    stk("👉", 15.04, 15.84, SR)

    # ---- what each size is for
    section("guna")
    lab(29.66, 31.30, "*BANTAL PELUK*", fill=CREAM, side=flip())
    stk("🤗", 29.70, 31.30, SR)
    lab(31.30, 32.60, "TEMAN *TIDUR*", fill=SUN, hi=DEEP, side=flip())
    stk("😴", 31.34, 32.60, SL)
    lab(32.70, 34.00, "BAWA *TRAVEL*", fill=CREAM, side=flip(), sound="whoosh", vol=0.3)
    stk("✈️", 32.74, 34.00, SR)
    lab(34.10, 36.30, "KECIL UNTUK *BAYI*", fill=SUN, side=flip())
    stk("👶", 34.14, 36.30, SL)
    lab(36.60, 38.20, "*COMEL* KAN?", fill=CREAM, side=flip(), sound="sparkle", vol=0.3)
    stk("🥰", 36.64, 38.20, SR)

    # ---- material
    section("material")
    lab(43.70, 45.48, "KAIN *VELVET*", fill=CREAM, side=flip(), sound="sparkle", vol=0.3)
    stk("✨", 43.74, 45.48, SR)
    lab(46.00, 47.66, "*TAHAN LASAK*", fill=SUN, hi=DEEP, side=flip())
    stk("💪", 46.04, 47.66, SL)
    lab(47.90, 48.84, "*TAK PUDAR*", fill=CREAM, side=flip())
    stk("🎨", 47.94, 48.84, SR)
    lab(48.86, 50.26, "*TAK* BERBULU", fill=SUN, side=flip(), sound="ding", vol=0.35)
    stk("👌", 48.90, 50.26, SL)

    # ---- gifts
    section("hadiah")
    lab(21.00, 22.40, "BELI *BANYAK-BANYAK*", fill=CREAM, side=flip())
    stk("🛍️", 21.04, 22.40, SR)
    lab(22.50, 24.24, "HADIAH *ANAK BUAH*", fill=SUN, side=flip(), sound="sparkle", vol=0.3)
    stk("🎁", 22.54, 24.24, SL)
    lab(24.48, 25.34, "ANAK *KORANG*", fill=CREAM, side=flip())
    lab(25.84, 27.90, "ANAK *MURID*", fill=SUN, hi=DEEP, side=flip())
    stk("🧒", 25.88, 27.90, SR)
    lab(27.92, 29.20, "*MAMI-MAMI* PUN BOLEH!", fill=CREAM, side=flip(), sound="boing", vol=0.45)
    stk("🙋‍♀️", 27.96, 29.20, SL)

    # ---- end card: wooden garden sign
    e0 = BT["end"]["t0"]
    sfx.append(("whoosh", e0 - 0.1, 0.4))
    ev += iris(e0 - 0.12)
    ev += garden_sign(e0, TOTAL)
    ev += plank(e0 + 0.10, TOTAL, "BANTAL *CARROT*", y=330, size=66, tilt=-2)
    ev += plank(e0 + 0.40, TOTAL, "90 • 70 • 50 CM", y=455, size=50, tilt=1.5)
    ev += plank(e0 + 0.70, TOTAL, "TEAM *GIGI* KE *TANPA GIGI*?", y=575, size=42, tilt=-1)
    ev += plank(e0 + 1.00, TOTAL, "TEKAN *BEG KUNING*", y=700, size=52, tilt=1.5)
    ev += sprouts(e0 + 0.2, SAFE_L + 46, dur=TOTAL - e0 - 0.2)
    ev += sprouts(e0 + 0.3, W - SAFE_R - 46, dur=TOTAL - e0 - 0.3)
    bstk("🥕", e0 + 0.15, TOTAL, SL, 230, 96)
    bstk("🌱", e0 + 0.45, TOTAL, SR, 230, 84)
    bstk("🛒", e0 + 1.05, TOTAL, SR, 820, 80)
    sfx += [("thud", e0 + 0.18, 0.5), ("thud", e0 + 0.48, 0.5), ("thud", e0 + 0.78, 0.5), ("pop", e0 + 1.05, 0.5)]
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
