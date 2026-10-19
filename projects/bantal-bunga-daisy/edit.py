#!/usr/bin/env python3
"""Edit for the daisy flower plush pillow (bantal bunga, IMG_2937: indoors) TikTok video.

Refreshed "breakfast cafe" look, different from the other batch-4 edits: scalloped daisy-edge
labels that pop in, captions sitting on a soft cream rounded bar (cocoa text, coral active word),
soft bubbles floating up at each section, a striped "blinds" transition, a little daisy rolling
along the top as the progress bar, and a breakfast-plate end card.

All overlays stay inside the TikTok safe zone (SAFE_* below): nothing under the
right-hand profile/like/comment/share column, the bottom caption area or the top tabs.

Needs the Fredoka Bold font (fonts/Fredoka-Bold.ttf, SIL OFL) installed, e.g. in ~/.fonts.

Usage: python3 edit.py <proxy.mp4> <transcript.json> <sfx_dir> <out_dir> [--final]
  preview: 720x1280 proxy -> preview.mp4;  --final: 1080x1920 master -> final.mp4
  --audio-only: re-mix voice + SFX onto the existing render -> *_voice.mp4

All times in BLOCKS are source times of the original clip (same timeline as
the proxy). The script builds:
  base.mp4     - cut/zoomed video + cleaned voice + SFX
  overlay.ass  - captions, labels, bubbles, blinds, rolling daisy, end card
  preview.mp4  - base + ASS, then colour emoji stickers on top (rendered with Pillow)
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
# Price lines are cut (no prices): "Harga dia sangat sangat jimat. Korang mesti terkejut tengok harga yang
# sangat murah ni." (12.05-16.72) and "Harga dia sangat mesra poket." (38.54-40.6).
BLOCKS = [
    # HOOK (her opening, problem -> fix): "Sofa kosong sangat. Letaklah bantal bunga yang gebu ni. Barulah
    # estetik. Barulah naik seri ruang tamu kita kan."  (a clipped syllable before "sofa" is skipped)
    dict(name="hook", a="same", v=[(0.40, 4.60, 1, 1.0), (4.60, 8.40, 1, 1.1)]),
    # "Ada size 50cm dengan size 35cm."
    dict(name="size", a="same", v=[(8.66, 11.97, 1, 1.04)]),
    # "Nah yang ni tengok material bulu-bulu fluffy."  (yellow close-up)
    dict(name="material", a="same", v=[(16.78, 20.25, 1, 1.0)]),
    # "Ada dua warna. Warna putih. Ya Allah lawa."  (white close-up)
    dict(name="warna", a="same", v=[(20.58, 24.72, 1, 1.0)]),
    # "Lembut je tengok saya picit. Toing-toing. Toing-toing."  (the repeated "yang ni untuk size 50
    # dengan 30cm tu" before it is cut)
    dict(name="picit", a="same", v=[(27.73, 32.38, 1, 1.0)]),
    # "Nak buat bantal dalam kereta pun sangat sesuai. Boleh peluk, boleh peluk macam tu."
    dict(name="kereta", a="same", v=[(32.66, 34.86, 1, 1.0), (34.86, 36.98, 1, 1.08)]),
    # "Tengok dekat beg kuning."  ("Okey" before it and the price line after it cut)
    dict(name="cta", a="same", v=[(37.36, 38.50, 1, 1.0)]),
    # holding both to the camera, gentle slow-mo - end card
    dict(name="end", a=None, v=[(39.50, 41.30, 0.75, 1.0)]),
]

FIX = {"banta": "bantal", "pichik": "picit", "Ini": "Ni", "ini": "ni", "Toing": "Toing", "aje": "je"}
def _w(*ws):
    return [dict(w=w, s=a, e=b) for w, a, b in ws]


OVERRIDE = {}
DROP = []
HILITE = {"SOFA", "KOSONG", "BANTAL", "BUNGA", "GEBU", "ESTETIK", "SERI", "RUANG", "TAMU", "50CM", "35CM", "SIZE",
          "BULU-BULU", "FLUFFY", "DUA", "WARNA", "PUTIH", "LAWA", "LEMBUT", "PICIT", "TOING-TOING", "KERETA",
          "SESUAI", "PELUK", "BEG", "KUNING"}

OVERRIDE[8.66] = _w(("Ada", 8.72, 8.94), ("size", 8.94, 9.16), ("50cm", 9.16, 10.04), ("dengan", 10.04, 10.46),
                    ("size", 10.46, 10.86), ("35cm.", 10.86, 11.82))

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



CAP_SIZE = 54
CAP_MV = SAFE_B + 26                      # caption bottom margin
ASS_HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Fredoka,{CAP_SIZE},&H0026344A,&H000000FF,&H00ECF8FF,&H00000000,-1,0,0,0,100,100,0,0,1,1.5,0,2,{SAFE_L},{SAFE_R},{CAP_MV},1
Style: Tag,Fredoka,60,&H0026344A,&H000000FF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# breakfast-cafe palette from the pillows (ASS colours are BGR): cocoa text, mustard yolk, butter,
# cream, daisy white, sky blue (fresh contrast to the mustard) and a coral accent
COCOA = "&H0026344A&"    # #4A3426
YOLK = "&H001FA2E8&"     # #E8A21F
BUTTER = "&H008AE0FF&"   # #FFE08A
CREAM = "&H00ECF8FF&"    # #FFF8EC
SKY = "&H00EACB8F&"      # #8FCBEA
SKY_D = "&H00C0862F&"    # #2F86C0
CORAL = "&H004A58F0&"    # #F0584A
WHITE = "&H00FFFFFF&"

_PIL = {}


def text_w(text, size):
    """Width in ASS px of text set in Fredoka at `size`."""
    f = _PIL.setdefault(size, ImageFont.truetype(FONT_FILE, size))
    return f.getlength(text) * ASS_PER_PIL


def rrect(w, h, r):
    """Rounded rectangle centred on (0,0), clockwise on screen."""
    x0, y0, x1, y1 = -w / 2, -h / 2, w / 2, h / 2
    r = min(r, h / 2, w / 2)
    return (f"m {x0 + r:.0f} {y0:.0f} l {x1 - r:.0f} {y0:.0f} b {x1:.0f} {y0:.0f} {x1:.0f} {y0:.0f} {x1:.0f} {y0 + r:.0f} "
            f"l {x1:.0f} {y1 - r:.0f} b {x1:.0f} {y1:.0f} {x1:.0f} {y1:.0f} {x1 - r:.0f} {y1:.0f} "
            f"l {x0 + r:.0f} {y1:.0f} b {x0:.0f} {y1:.0f} {x0:.0f} {y1:.0f} {x0:.0f} {y1 - r:.0f} "
            f"l {x0:.0f} {y0 + r:.0f} b {x0:.0f} {y0:.0f} {x0:.0f} {y0:.0f} {x0 + r:.0f} {y0:.0f}")


def norm(path):
    """libass lays a drawing out from (0,0), so negative coordinates break \\an5 centring:
    shift the path so its bounding box starts at (0,0); \\an5 then centres it on \\pos."""
    toks = path.split()
    idx = [i for i, t in enumerate(toks) if t not in ("m", "l", "b")]
    xs = [float(toks[i]) for k, i in enumerate(idx) if k % 2 == 0]
    ys = [float(toks[i]) for k, i in enumerate(idx) if k % 2 == 1]
    mx, my = min(xs), min(ys)
    for k, i in enumerate(idx):
        toks[i] = f"{float(toks[i]) - (mx if k % 2 == 0 else my):.1f}"
    return " ".join(toks)


def circle(r, n=24, cx=0.0, cy=0.0):
    pts = [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    return f"m {pts[0][0]:.1f} {pts[0][1]:.1f} " + " ".join(f"l {x:.1f} {y:.1f}" for x, y in pts[1:])


def scallop(w, h):
    """Daisy-edge (scalloped) badge centred on (0,0): a rounded rect ringed with petal bumps."""
    rb = h * 0.20
    cw, ch = w - rb * 0.6, h - rb * 0.6
    # walk the rounded-rect perimeter and drop a bump every ~1.45*rb
    per = []
    r = ch / 2
    straight = max(0.0, cw - 2 * r)
    length = 2 * straight + 2 * math.pi * r
    n = max(8, int(length / (rb * 1.45)))
    for k in range(n):
        d = length * k / n
        if d < straight:                                   # top edge, left -> right
            per.append((-straight / 2 + d, -r))
        elif d < straight + math.pi * r:                   # right cap
            a = -math.pi / 2 + (d - straight) / r
            per.append((straight / 2 + r * math.cos(a), r * math.sin(a)))
        elif d < 2 * straight + math.pi * r:               # bottom edge, right -> left
            per.append((straight / 2 - (d - straight - math.pi * r), r))
        else:                                              # left cap
            a = math.pi / 2 + (d - 2 * straight - math.pi * r) / r
            per.append((-straight / 2 + r * math.cos(a), r * math.sin(a)))
    return rrect(cw, ch, ch / 2) + " " + " ".join(circle(rb, 14, x, y) for x, y in per)


def captions(words):
    """3-word chunks on a soft cream rounded bar; cocoa text, the active word coral and a little bigger,
    keywords sky blue."""
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
        full = text_w(line, CAP_SIZE) * 1.05
        fs = CAP_SIZE if full <= SAFE_W - 70 else int(CAP_SIZE * (SAFE_W - 70) / full)
        # the bar behind the whole chunk
        bw = text_w(line, fs) * 1.05 + 46
        bh = fs * 1.32
        by = H - CAP_MV - fs * 0.56
        t0 = min(x["s"] for x in ch)
        ev.append(f"Dialogue: 1,{ts(t0)},{ts(end)},Shape,,0,0,0,,"
                  rf"{{\an5\pos({CX},{by + 4:.0f})\c{COCOA}\1a&HA0&\fscx92\fscy92\t(0,90,\fscx100\fscy100)\p1}}"
                  rf"{norm(rrect(bw, bh, bh / 2))}{{\p0}}")
        ev.append(f"Dialogue: 1,{ts(t0)},{ts(end)},Shape,,0,0,0,,"
                  rf"{{\an5\pos({CX},{by:.0f})\c{CREAM}\1a&H18&\3c{BUTTER}\bord2\fscx92\fscy92\t(0,90,\fscx100\fscy100)\p1}}"
                  rf"{norm(rrect(bw, bh, bh / 2))}{{\p0}}")
        for j, w in enumerate(ch):
            ws = w["s"] if j else min(w["s"], ch[0]["s"])
            we = ch[j + 1]["s"] if j + 1 < len(ch) else end
            parts = []
            for k, t in enumerate(toks):
                if k == j:
                    parts.append(r"{\c%s\fscx100\fscy100\t(0,80,\fscx112\fscy112)}%s{\c%s\fscx100\fscy100}"
                                 % (CORAL, t, COCOA))
                elif t.strip("-?!") in HILITE or t in HILITE:
                    parts.append(r"{\c%s}%s{\c%s}" % (SKY_D, t, COCOA))
                else:
                    parts.append(t)
            ev.append(f"Dialogue: 2,{ts(ws)},{ts(we)},Cap,,0,0,0,,{{\\fs{fs}}}" + " ".join(parts))
    return ev


def fit_size(text, size, max_w):
    plain = text.replace("*", "")
    w = text_w(plain, size)
    return size if w <= max_w else int(size * max_w / w)


def badge(t0, t1, text, y=300, fill=BUTTER, col=COCOA, hi=CORAL, x=CX, size=58, layer=5, rot=0.0,
          max_w=SAFE_W - 120):
    """Scalloped daisy-edge badge: white petal rim, coloured centre, pops in with a little overshoot."""
    size = fit_size(text, size, max_w)
    tw = text_w(text.replace("*", ""), size)
    h = size * 1.42
    w = tw + size * 1.15
    pop = (r"\fscx55\fscy55\t(0,140,\fscx108\fscy108)\t(140,240,\fscx100\fscy100)\fad(60,140)"
           rf"\org({x},{y})\frz{rot:.1f}")
    body = "".join(p if i % 2 == 0 else rf"{{\c{hi}}}{p}{{\c{col}}}" for i, p in enumerate(text.split("*")))
    sc = scallop(w + h * 0.35, h * 1.28)
    return [
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,{{\\an5\\pos({x + 5},{y + 8}){pop}\\c{COCOA}\\1a&H70&\\p1}}{norm(sc)}{{\\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,{{\\an5\\pos({x},{y}){pop}\\c{WHITE}\\3c{COCOA}\\bord3\\p1}}{norm(sc)}{{\\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,{{\\an5\\pos({x},{y}){pop}\\c{fill}\\p1}}{norm(rrect(w, h, h / 2))}{{\\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},Tag,,0,0,0,,{{\\an5\\pos({x},{y + 2}){pop}\\fs{size}\\c{col}}}{body}",
    ]


def bubbles(t0, side, layer=4, n=6, seed=0):
    """Soft bubbles floating up one side of the safe area and popping."""
    rnd = np.random.default_rng(seed)
    ev = []
    x0 = SAFE_L + 34 if side < 0 else W - SAFE_R - 34
    cols = [CREAM, BUTTER, SKY, WHITE]
    for k in range(n):
        r = float(rnd.uniform(7, 16))
        x = x0 + float(rnd.uniform(-18, 18))
        y0 = H - SAFE_B - 60 - float(rnd.uniform(0, 120))
        dy = float(rnd.uniform(220, 330))
        st = t0 + k * 0.09
        dur = float(rnd.uniform(1.1, 1.5))
        ms = int(dur * 1000)
        ev.append(f"Dialogue: {layer},{ts(st)},{ts(st + dur)},Shape,,0,0,0,,"
                  rf"{{\an5\move({x:.0f},{y0:.0f},{x + rnd.uniform(-14, 14):.0f},{y0 - dy:.0f})"
                  rf"\c{cols[k % 4]}\1a&H40&\3c{WHITE}\bord2\fscx40\fscy40\t(0,200,\fscx100\fscy100)"
                  rf"\t({ms - 160},{ms},\fscx150\fscy150\alpha&HFF&)\p1}}{norm(circle(r, 18))}{{\p0}}")
    return ev


def blinds(t0, layer=7):
    """Striped 'blinds' transition: 6 bands (yolk / butter) slide across from the left, then fade."""
    ev = []
    n = 6
    bh = H / n
    for k in range(n):
        col = YOLK if k % 2 == 0 else BUTTER
        a = k * 22
        ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t0 + 0.48)},Shape,,0,0,0,,"
                  rf"{{\an7\pos(0,{k * bh:.0f})\c{col}\1a&H20&\fscx0\t({a},{a + 130},\fscx100)"
                  rf"\t({a + 200},{a + 330},\1a&HFF&)\p1}}m 0 0 l {W} 0 l {W} {bh + 1:.0f} l 0 {bh + 1:.0f}{{\p0}}")
    return ev


def daisy_path(r):
    """Daisy centred on (0,0): 8 round petals; returns (petals, centre)."""
    petals = " ".join(circle(r * 0.42, 12, r * 0.62 * math.cos(2 * math.pi * k / 8), r * 0.62 * math.sin(2 * math.pi * k / 8))
                      for k in range(8))
    return petals, circle(r * 0.40, 16)


def rolling_daisy():
    """Progress bar: a butter track with a yolk fill and a little daisy rolling along its front edge."""
    y = 16
    x0, x1 = SAFE_L, W - SAFE_R
    ev = [f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
          rf"{{\an7\pos({x0},{y - 3})\c{CREAM}\1a&H50&\p1}}m 0 0 l {x1 - x0} 0 l {x1 - x0} 6 l 0 6{{\p0}}",
          f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
          rf"{{\an7\pos({x0},{y - 3})\c{YOLK}\fscx0\t(0,{int(TOTAL * 1000)},\fscx100)\p1}}m 0 0 l {x1 - x0} 0 l {x1 - x0} 6 l 0 6{{\p0}}"]
    # the daisy is drawn in short steps so it can roll (rotate about its own moving centre)
    petals, centre = daisy_path(13)
    step = 0.25
    t = 0.0
    while t < TOTAL:
        t2 = min(TOTAL, t + step)
        xa = x0 + (x1 - x0) * t / TOTAL
        xb = x0 + (x1 - x0) * t2 / TOTAL
        rot0 = -(xa - x0) / 13 * 180 / math.pi
        rot1 = -(xb - x0) / 13 * 180 / math.pi
        ms = int((t2 - t) * 1000)
        for path, tags in ((petals, rf"\c{WHITE}\3c{COCOA}\bord1.5"), (centre, rf"\c{YOLK}")):
            ev.append(f"Dialogue: 9,{ts(t)},{ts(t2)},Shape,,0,0,0,,"
                      rf"{{\an5\move({xa:.1f},{y},{xb:.1f},{y})\frz{rot0:.0f}\t(0,{ms},\frz{rot1:.0f}){tags}\p1}}{norm(path)}{{\p0}}")
        t = t2
    return ev


def plate(t0, t1, cx=CX, cy=470, r=235):
    """End card: cream wash and a breakfast plate (sky rim, white plate, butter inner ring) that spins in."""
    spin = rf"\fscx30\fscy30\frz-25\t(0,260,\fscx104\fscy104\frz3)\t(260,380,\fscx100\fscy100\frz0)"
    return [
        f"Dialogue: 8,{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
        rf"{{\an7\pos(0,0)\c{CREAM}\1a&HFF&\t(0,250,\1a&H50&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}",
        f"Dialogue: 9,{ts(t0)},{ts(t1)},Shape,,0,0,0,,{{\\an5\\pos({cx + 8},{cy + 12}){spin}\\c{COCOA}\\1a&H80&\\p1}}{norm(circle(r, 64))}{{\\p0}}",
        f"Dialogue: 9,{ts(t0)},{ts(t1)},Shape,,0,0,0,,{{\\an5\\pos({cx},{cy}){spin}\\c{SKY}\\3c{COCOA}\\bord3\\p1}}{norm(circle(r, 64))}{{\\p0}}",
        f"Dialogue: 9,{ts(t0)},{ts(t1)},Shape,,0,0,0,,{{\\an5\\pos({cx},{cy}){spin}\\c{WHITE}\\p1}}{norm(circle(r - 22, 64))}{{\\p0}}",
        f"Dialogue: 9,{ts(t0)},{ts(t1)},Shape,,0,0,0,,{{\\an5\\pos({cx},{cy}){spin}\\c{WHITE}\\1a&HFF&\\3c{BUTTER}\\bord4\\p1}}{norm(circle(r - 62, 64))}{{\\p0}}",
    ]


def plate_text(t0, t1, text, y, size, col=COCOA, hi=YOLK, layer=10):
    size = fit_size(text, size, 380)
    body = "".join(p if i % 2 == 0 else rf"{{\c{hi}}}{p}{{\c{col}}}" for i, p in enumerate(text.split("*")))
    return [f"Dialogue: {layer},{ts(t0)},{ts(t1)},Tag,,0,0,0,,{{\\an5\\pos({CX},{y})\\fs{size}\\c{col}"
            rf"\fscx70\fscy70\alpha&HFF&\t(0,160,\fscx104\fscy104\alpha&H00&)\t(160,240,\fscx100\fscy100)}}{body}"]


def graphics():
    ev, stickers, sfx = [], [], []
    LY = 300                       # badges sit high, above the pillows' yolk centres
    ev += rolling_daisy()
    tilt = [2.0]

    def lab(s0, s1, text, sound="pop", vol=0.5, **kw):
        kw.setdefault("y", LY)
        tilt[0] = -tilt[0]
        kw.setdefault("rot", tilt[0])
        ev.extend(badge(tl(s0), tl(s1), text, **kw))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def stk(em, s0, s1, x, y=208, size=90):
        stickers.append((em, tl(s0), tl(s1), x, y, size))

    def bstk(em, t0, t1, x, y, size=96):
        stickers.append((em, t0, t1, x, y, size))

    def section(name, seed, blind=True):
        t0 = BT[name]["t0"]
        if blind and t0 > 0:
            ev.extend(blinds(t0 - 0.2))
            sfx.append(("blinds", max(0, t0 - 0.2), 0.45))
        ev.extend(bubbles(t0 + 0.05, -1, seed=seed))
        ev.extend(bubbles(t0 + 0.20, 1, seed=seed + 50))
        sfx.append(("bubble", t0 + 0.1, 0.3))

    SL, SR = 100, 540

    # ---- HOOK: empty sofa -> put the flower pillows -> aesthetic living room
    section("hook", 1, blind=False)
    lab(0.55, 2.30, "SOFA *KOSONG*?", fill=WHITE, hi=SKY_D, size=64, sound="boing", vol=0.5)
    stk("🛋️", 0.60, 2.30, SR)
    lab(2.36, 4.55, "LETAK *BANTAL BUNGA*!", fill=BUTTER)
    stk("🌼", 2.40, 4.55, SL)
    lab(4.72, 6.02, "BARU *ESTETIK*!", fill=WHITE, size=64, sound="sparkle", vol=0.35)
    stk("✨", 4.76, 6.02, SR)
    lab(6.06, 8.38, "NAIK *SERI* RUANG TAMU", fill=BUTTER, hi=SKY_D)
    stk("🏡", 6.10, 8.38, SL)

    # ---- sizes
    section("size", 2)
    lab(8.72, 10.04, "SIZE *50CM*", fill=WHITE, size=66, sound="ding", vol=0.35)
    stk("📏", 8.76, 10.04, SR)
    lab(10.04, 11.95, "& *35CM*", fill=BUTTER, size=66, sound="bloop", vol=0.5)

    # ---- fluffy material (yellow close-up)
    section("material", 3)
    lab(17.26, 18.70, "TENGOK *MATERIAL*", fill=WHITE, hi=SKY_D)
    lab(18.76, 20.22, "BULU-BULU *FLUFFY*", fill=BUTTER, sound="sparkle", vol=0.3)
    stk("☁️", 18.80, 20.22, SR)

    # ---- colours (white close-up)
    section("warna", 4)
    lab(20.86, 22.40, "ADA *2 WARNA*", fill=BUTTER)
    stk("🎨", 20.90, 22.40, SL)
    lab(22.50, 24.70, "*PUTIH*, LAWA!", fill=WHITE, hi=SKY_D, size=64, sound="sparkle", vol=0.35)
    stk("🤍", 22.54, 24.70, SR)

    # ---- squeeze test
    section("picit", 5)
    lab(27.80, 29.62, "*LEMBUT* JE!", fill=BUTTER, size=64)
    stk("🤲", 27.84, 29.62, SL)
    lab(29.84, 31.30, "*TOING-TOING*!", fill=WHITE, size=68, sound="squish", vol=0.55)
    stk("😆", 29.88, 31.30, SR)
    lab(31.36, 32.36, "*TOING-TOING*!", fill=BUTTER, size=72, sound="squish", vol=0.55)
    sfx.append(("boing", tl(30.20), 0.3))
    sfx.append(("boing", tl(31.86), 0.3))

    # ---- car + hug
    section("kereta", 6)
    lab(32.82, 34.84, "SESUAI DALAM *KERETA*", fill=WHITE, hi=SKY_D, sound="whoosh", vol=0.3)
    stk("🚗", 32.86, 34.84, SR)
    lab(34.86, 36.95, "BOLEH *PELUK*!", fill=BUTTER, size=66)
    stk("🤗", 34.90, 36.95, SL)

    # ---- CTA
    section("cta", 7)
    lab(37.38, 38.48, "TENGOK *BEG KUNING*", fill=BUTTER, hi=CORAL, size=60, sound="ding", vol=0.35)
    stk("🛒", 37.42, 38.48, SR)

    # ---- end card: breakfast plate
    e0 = BT["end"]["t0"]
    ev += blinds(e0 - 0.2)
    sfx.append(("blinds", e0 - 0.2, 0.45))
    ev += plate(e0, TOTAL)
    ev += plate_text(e0 + 0.30, TOTAL, "BANTAL *BUNGA*", 405, 62)
    ev += plate_text(e0 + 0.55, TOTAL, "SIZE 50 • 35 CM", 478, 42, col=CORAL)
    ev += plate_text(e0 + 0.80, TOTAL, "PUTIH • MUSTARD", 540, 36, col=SKY_D)
    ev += badge(e0 + 1.05, TOTAL, "TEKAN *BEG KUNING*", y=775, fill=BUTTER, hi=CORAL, size=52, layer=11)
    ev += bubbles(e0 + 0.3, -1, seed=91, n=8)
    ev += bubbles(e0 + 0.5, 1, seed=92, n=8)
    bstk("🌼", e0 + 0.35, TOTAL, CX, 196, 72)
    bstk("🛒", e0 + 1.10, TOTAL, SR, 690, 72)
    sfx += [("whoosh", e0 - 0.05, 0.4), ("pop", e0 + 0.30, 0.5), ("pop", e0 + 0.55, 0.45),
            ("pop", e0 + 0.80, 0.45), ("ding", e0 + 1.05, 0.35)]
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
