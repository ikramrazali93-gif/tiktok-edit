#!/usr/bin/env python3
"""Edit for the flower / square seat cushion (bantal lapik duduk) TikTok video.

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

# ---------------------------------------------------------------- EDL
# Single source clip IMG_2930 (outdoors on grass): flower (bulat) + square (petak) seat cushions,
# ribbed fabric, brown / pink / grey with a cream flower in the middle.
# v: list of (src_in, src_out, speed, zoom); a zoom change inside a block is a "punch-in" on the beat
# a: 'same' (follow v at speed 1), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK (already the opening line, "Ha" cut): "Yang mana lenguh-lenguh duduk dalam kereta tu, korang kena
    #  ada satu ni bantal untuk lapik duduk ni."  punch-in on "korang kena ada"
    dict(name="hook", a="same", v=[(0.66, 3.42, 1, 1.0), (3.42, 6.50, 1, 1.1)]),
    # "Saiz dia 40cm, ada dua bentuk, ada bentuk petak, ada bentuk bulat macam ni."
    dict(name="saiz", a="same", v=[(6.84, 9.76, 1, 1.0), (9.76, 12.70, 1, 1.08)]),
    # "Sangat-sangat selesa. Tengok ketebalan dia. Lembut, fluffy macam ni."  ("Ha" before, "Kan?" after cut)
    dict(name="selesa", a="same", v=[(13.25, 15.45, 1, 1.0), (15.45, 17.42, 1, 1.07)]),
    # "Ni bentuk petak dia pun sama tebal."  ("Ha" before cut)
    dict(name="petak", a="same", v=[(17.96, 20.52, 1, 1.0)]),
    # "Colour dia sangat-sangat estetik, warna dia soft-soft, warna-warna pastel."  ("Ha dan" cut)
    dict(name="colour", a="same", v=[(21.30, 25.14, 1, 1.05)]),
    # "Ada warna brown, ada warna pink, | ada warna kelabu, cantik kan."  (0.2s pause cut)
    dict(name="warna", a="same", v=[(25.38, 27.40, 1, 1.0), (27.60, 30.14, 1, 1.08)]),
    # "Korang beli letak dekat dalam kereta, | alas duduk dekat seat driver."  ("Nah," before cut)
    dict(name="kereta", a="same", v=[(30.74, 33.50, 1, 1.0), (33.50, 35.47, 1, 1.08)]),
    # "Cepat-cepat tengok beg kuning."  ("Ok ha" before and "harga tengok promo" after cut: no price talk)
    dict(name="cta", a="same", v=[(35.97, 37.53, 1, 1.1)]),
    # grey + pink cushions held up, slowed, under the end card
    dict(name="end", a=None, v=[(37.70, 39.85, 0.8, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "bantai": "bantal", "reta": "kereta", "lengah": "lenguh", "-lengah": "-lenguh",
       "Okey": "Okay"}
# hand-checked words where Whisper drifted or misheard (re-transcribed per clip)
def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


OVERRIDE = {
    35.97: _w(("Cepat", 36.02, 36.58), ("-cepat", 36.58, 36.76), ("tengok", 36.76, 37.00), ("beg", 37.00, 37.12),
              ("kuning.", 37.12, 37.50)),
}
DROP = [(35.30, 35.50)]       # "Ok" at the very end of the seat-driver clip
HILITE = {"LENGUH-LENGUH", "KERETA", "LAPIK", "DUDUK", "40CM", "PETAK", "BULAT", "SELESA", "KETEBALAN", "LEMBUT",
          "FLUFFY", "TEBAL", "ESTETIK", "SOFT-SOFT", "PASTEL", "BROWN", "PINK", "KELABU", "CANTIK", "SEAT", "DRIVER",
          "KUNING", "BENTUK", "BANTAL"}

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


# palette from the cushions: cocoa for text/outline, caramel (brown cushion), blush + rose (pink cushion),
# dove grey (grey cushion), cream (the flower centre + piping), butter yellow for the CTA
COCOA = bgr("#4A2C22")
CARAMEL = bgr("#C98A5E")
BLUSH = bgr("#F2A7BC")
ROSE = bgr("#C2577A")
DOVE = bgr("#9C9CAB")
CREAM = bgr("#FFF4E4")
BUTTER = bgr("#FFD54F")
WHITE = "&H00FFFFFF&"
KEY = bgr("#FFD0DE")          # caption keywords: pale blush

ASS_HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Fredoka,58,&H00FFFFFF,&H000000FF,{COCOA[:-1]},&H70222C4A,-1,0,0,0,100,100,0,0,1,5,2,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Label,Fredoka,60,{COCOA[:-1]},&H000000FF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,{COCOA[:-1]},&H70222C4A,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
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


def stitches(w, h, r, dash=13, gap=9, th=3.5):
    """Dashed 'stitch' line along the straight edges of a rounded rect (centred), as one drawing."""
    out = []
    x0, y0, x1, y1 = -w / 2, -h / 2, w / 2, h / 2
    for (ax, ay, bx, by) in [(x0 + r, y0, x1 - r, y0), (x0 + r, y1, x1 - r, y1),
                             (x0, y0 + r, x0, y1 - r), (x1, y0 + r, x1, y1 - r)]:
        L = abs(bx - ax) + abs(by - ay)
        n = max(1, int((L + gap) // (dash + gap)))
        pad = (L - (n * dash + (n - 1) * gap)) / 2
        for i in range(n):
            u0 = (pad + i * (dash + gap)) / L
            u1 = (pad + i * (dash + gap) + dash) / L
            sx, sy = ax + (bx - ax) * u0, ay + (by - ay) * u0
            ex, ey = ax + (bx - ax) * u1, ay + (by - ay) * u1
            if ay == by:
                out.append(f"m {sx:.0f} {sy - th / 2:.1f} l {ex:.0f} {sy - th / 2:.1f} {ex:.0f} {sy + th / 2:.1f} {sx:.0f} {sy + th / 2:.1f}")
            else:
                out.append(f"m {sx - th / 2:.1f} {sy:.0f} l {sx + th / 2:.1f} {sy:.0f} {sx + th / 2:.1f} {ey:.0f} {sx - th / 2:.1f} {ey:.0f}")
    return norm(" ".join(out))


def captions(words):
    """3-word chunks. Refresh: the active word sits on a rose rounded 'patch' box (drawn per word), not just recoloured."""
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
    base_y = H - (SAFE_B + 20)                 # bottom of the caption line (\an2)
    for i, ch in enumerate(chunks):
        end = ch[-1]["e"] + 0.15
        if i + 1 < len(chunks):
            end = min(end, chunks[i + 1][0]["s"])
        toks = [x["w"].upper().strip(",.") for x in ch]
        size = 58
        while text_w(" ".join(toks), size) > SAFE_W - 100 and size > 36:
            size -= 2
        sp = text_w(" ", size)
        widths = [text_w(t, size) for t in toks]
        x = CX - (sum(widths) + sp * (len(toks) - 1)) / 2
        xs = []
        for wd in widths:
            xs.append(x)
            x += wd + sp
        cy = base_y - size * 0.62
        for j, w in enumerate(ch):
            ws = w["s"] if j else min(w["s"], ch[0]["s"])
            we = ch[j + 1]["s"] if j + 1 < len(ch) else end
            bw, bh = widths[j] + 22, size * 1.02
            bx = xs[j] + widths[j] / 2
            ev.append(f"Dialogue: 1,{ts(ws)},{ts(we)},ShapeC,,0,0,0,,"
                      rf"{{\pos({bx:.0f},{cy:.0f})\c{ROSE}\3c&HFFFFFF&\bord3\shad0\p1}}{rrect(bw, bh, 16)}{{\p0}}")
            parts = []
            for k, t in enumerate(toks):
                if k == j:
                    parts.append(r"{\c&HFFFFFF&}%s{\r}" % t)
                elif t.strip("-?!") in HILITE or t in HILITE:
                    parts.append(r"{\c%s}%s{\r}" % (KEY, t))
                else:
                    parts.append(t)
            pop = r"{\fad(60,0)}" if j == 0 else ""
            ev.append(f"Dialogue: 2,{ts(ws)},{ts(we)},Cap,,0,0,0,,{pop}{{\\fs{size}}}" + " ".join(parts))
    return ev


def fit_size(text, size, max_w=SAFE_W - 110):   # room for the patch padding + white rim + pop overshoot
    """Shrink a label's font size so its patch stays inside the safe area."""
    w = text_w(text.replace("*", ""), size)
    return size if w <= max_w else int(size * max_w / w)


def label(t0, t1, text, y=250, col=COCOA, box=CREAM, hi=ROSE, st=CARAMEL, layer=5, x=CX, size=60, rot=0):
    """Refresh: a rounded fabric 'patch' with a dashed stitch line inside (like the cushion piping),
    soft drop shadow, squishy pop-in. All parts share \\an5 + \\pos so they scale/rotate together."""
    lines = text.replace("*", "").split("|")          # "|" = line break inside the patch
    size = min(fit_size(ln, size) for ln in lines)
    bw, bh = max(text_w(ln, size) for ln in lines) + 64, len(lines) * size * 1.02 + 38
    parts = text.replace("|", r"\N").split("*")
    txt = "".join(p if i % 2 == 0 else rf"{{\c{hi}}}{p}{{\c{col}}}" for i, p in enumerate(parts))
    def anim(px, py):
        return (rf"\an5\pos({px},{py})\frz{rot}\fscx0\fscy0\t(0,130,\fscx116\fscy88)\t(130,230,\fscx94\fscy106)"
                rf"\t(230,320,\fscx100\fscy100)\fad(0,150)")
    shp = "{" + anim(x, y)
    return [
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{{{anim(x + 5, y + 7)}\\c{COCOA}\\1a&H90&\\blur3\\p1}}{rrect(bw, bh, 22)}{{\\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{shp}\\c{box}\\3c&HFFFFFF&\\bord4\\p1}}{rrect(bw, bh, 22)}{{\\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{shp}\\c{st}\\p1}}{stitches(bw - 18, bh - 18, 16)}{{\\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},Label,,0,0,0,,{{{anim(x, y)}\\fs{size}\\c{col}}}{txt}",
    ]


FLOWER = norm(" ".join(
    f"m {14 * np.cos(a) - 9:.0f} {14 * np.sin(a):.0f} b {14 * np.cos(a) - 9:.0f} {14 * np.sin(a) - 12:.0f} "
    f"{14 * np.cos(a) + 9:.0f} {14 * np.sin(a) - 12:.0f} {14 * np.cos(a) + 9:.0f} {14 * np.sin(a):.0f} "
    f"b {14 * np.cos(a) + 9:.0f} {14 * np.sin(a) + 12:.0f} {14 * np.cos(a) - 9:.0f} {14 * np.sin(a) + 12:.0f} "
    f"{14 * np.cos(a) - 9:.0f} {14 * np.sin(a):.0f}"
    for a in np.linspace(0, 2 * np.pi, 5, endpoint=False) - np.pi / 2))
DOT = norm("m -7 0 b -7 -9 7 -9 7 0 b 7 9 -7 9 -7 0")


def flowers(t0, y=250, layer=4, spots=((-250, -40), (240, -55), (-225, 60), (250, 50))):
    """Refresh motif: little cream flowers (like the cushion centres) pop out around a label and spin."""
    ev = []
    for i, (dx, dy) in enumerate(spots):
        x, yy = CX + dx * 0.9, y + dy
        d0 = 60 * i
        for shape, col in ((FLOWER, CREAM), (DOT, CARAMEL)):
            ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t0 + 1.1)},ShapeC,,0,0,0,,"
                      rf"{{\pos({x:.0f},{yy:.0f})\c{col}\3c{COCOA}\bord{2 if shape == FLOWER else 0}\fscx0\fscy0"
                      rf"\t({d0},{d0 + 160},\fscx110\fscy110)\t({d0 + 160},{d0 + 260},\fscx90\fscy90)"
                      rf"\t(0,1100,\frz{200 if i % 2 else -200})\fad(0,260)\p1}}{shape}{{\p0}}")
    return ev


def flash(t0, col=BLUSH, d=0.28, layer=9):
    """Soft pastel flash (refresh: tinted, short) - paired with a zoom punch-in in the EDL."""
    return (f"Dialogue: {layer},{ts(t0)},{ts(t0 + d)},Shape,,0,0,0,,"
            rf"{{\an7\pos(0,0)\c{col}\1a&H40&\t(0,{int(d * 1000)},\1a&HFF&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")


def graphics():
    ev, stickers, sfx = [], [], []
    # progress bar (retention): cocoa track + cream "stitch" dashes revealed left to right
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{COCOA}\1a&H50&\p1}}m 0 0 l {W} 0 {W} 10 0 10{{\p0}}")
    dashes = " ".join(f"m {x} 3 l {x + 16} 3 {x + 16} 7 {x} 7" for x in range(4, W, 26))
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{BLUSH}\clip(0,0,0,10)\t(0,{int(TOTAL * 1000)},\clip(0,0,{W},10))\p1}}{dashes}{{\p0}}")

    def lab(s0, s1, text, sound="pop", vol=0.5, bloom=False, **kw):
        ev.extend(label(tl(s0), tl(s1), text, **kw))
        if bloom:
            ev.extend(flowers(tl(s0), y=kw.get("y", 250)))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def stk(em, s0, s1, x, y, size=100):
        stickers.append((em, tl(s0), tl(s1), x, y, size))

    def bstk(em, t0, t1, x, y, size=100):
        stickers.append((em, t0, t1, x, y, size))

    def punch(src, col=BLUSH, sound="swish", vol=0.35):
        t0 = tl(src)
        ev.append(flash(t0, col))
        sfx.append((sound, t0 - 0.05, vol))

    SL, SR, SY = 80, 560, 150     # stickers sit at the patch corners, above the cushions

    # ---- HOOK: sore from sitting in the car -> you need this seat cushion
    lab(0.72, 3.40, "LENGUH DUDUK|*DALAM KERETA*?", box=CREAM, hi=ROSE, size=62, sound="bloop", vol=0.5)
    stk("😩", 0.76, 3.40, SR, SY, 100)
    punch(3.42)
    lab(3.48, 6.45, "KENA ADA|*LAPIK DUDUK* NI!", box=ROSE, col=WHITE, hi=BUTTER, st=CREAM, size=62,
        sound="puff", vol=0.7, bloom=True)
    stk("🌸", 3.52, 6.45, SL, SY, 100)

    # ---- size + two shapes
    lab(6.92, 8.30, "SIZE *40CM*", box=CREAM, hi=CARAMEL, size=66, sound="click", vol=0.5)
    stk("📏", 6.96, 8.30, SR, SY, 90)
    lab(8.46, 9.70, "ADA *2 BENTUK*", box=CARAMEL, col=WHITE, hi=CREAM, st=CREAM, size=64, sound="pop", vol=0.45)
    stk("✌️", 8.50, 9.70, SR, SY, 95)
    punch(9.76, col=CREAM)
    lab(9.82, 11.30, "BENTUK *PETAK*", box=CREAM, hi=CARAMEL, size=64, sound="pop", vol=0.45)
    stk("🟫", 9.86, 11.30, SR, SY, 80)
    lab(11.42, 12.68, "BENTUK *BULAT*", box=BLUSH, col=COCOA, hi=WHITE, st=CREAM, size=64, sound="pop", vol=0.45,
        bloom=True)
    stk("🌸", 11.46, 12.68, SR, SY, 95)

    # ---- comfort: thickness, soft, fluffy
    lab(13.30, 14.16, "*SANGAT SELESA*", box=CREAM, hi=ROSE, size=68, sound="puff", vol=0.7)
    stk("😌", 13.34, 14.16, SR, SY, 100)
    lab(14.24, 15.42, "TENGOK *KETEBALAN*", box=CARAMEL, col=WHITE, hi=CREAM, st=CREAM, size=60, sound="pop", vol=0.45)
    stk("👀", 14.28, 15.42, SR, SY, 95)
    punch(15.45)
    lab(15.50, 17.38, "LEMBUT & *FLUFFY*", box=BLUSH, col=COCOA, hi=WHITE, st=CREAM, size=64, sound="sparkle",
        vol=0.35, bloom=True)
    stk("☁️", 15.54, 17.38, SL, SY, 100)
    lab(18.02, 20.48, "PETAK PUN *SAMA TEBAL*", box=CREAM, hi=CARAMEL, size=58, sound="puff", vol=0.6)
    stk("👍", 18.06, 20.48, SR, SY, 95)

    # ---- colours
    lab(21.40, 23.12, "KALER *ESTETIK*", box=CREAM, hi=ROSE, size=66, sound="sparkle", vol=0.35)
    stk("🎨", 21.44, 23.12, SR, SY, 95)
    lab(23.24, 25.12, "*SOFT* & *PASTEL*", box=BLUSH, col=COCOA, hi=WHITE, st=CREAM, size=66, sound="pop", vol=0.45,
        bloom=True)
    stk("🍬", 23.28, 25.12, SR, SY, 90)
    lab(25.45, 26.40, "*BROWN*", box=CARAMEL, col=WHITE, hi=WHITE, st=CREAM, size=72, sound="pop", vol=0.45)
    stk("🤎", 25.49, 26.40, SR, SY, 95)
    lab(26.50, 27.40, "*PINK*", box=BLUSH, col=COCOA, hi=COCOA, st=CREAM, size=72, sound="pop", vol=0.45)
    stk("🩷", 26.54, 27.40, SR, SY, 95)
    punch(27.60, col=CREAM)
    lab(27.66, 29.30, "*KELABU*", box=DOVE, col=WHITE, hi=WHITE, st=CREAM, size=72, sound="pop", vol=0.45)
    stk("🩶", 27.70, 29.30, SR, SY, 95)
    lab(29.34, 30.10, "CANTIK KAN?", box=CREAM, col=ROSE, size=66, sound="sparkle", vol=0.35, bloom=True)
    stk("😍", 29.38, 30.10, SR, SY, 95)

    # ---- car use
    lab(30.80, 33.48, "LETAK *DALAM KERETA*", box=CREAM, hi=ROSE, size=60, sound="pop", vol=0.45)
    stk("🚗", 30.84, 33.48, SR, SY, 100)
    punch(33.50)
    lab(33.56, 35.40, "ALAS *SEAT DRIVER*", box=CARAMEL, col=WHITE, hi=CREAM, st=CREAM, size=62, sound="puff", vol=0.6)
    stk("💺", 33.60, 35.40, SR, SY, 95)

    # ---- CTA
    lab(36.02, 37.50, "TENGOK *BEG KUNING*", box=BUTTER, col=COCOA, hi=ROSE, st=CREAM, size=62, sound="bloop", vol=0.5)
    stk("🛒", 36.06, 37.50, SR, SY, 95)

    # ---- end card (refresh): a quilted cream card with stitched border + colour swatches, top of the safe area
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 6,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{COCOA}\1a&HFF&\t(0,250,\1a&H78&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    cw, chh, cy = 520, 470, 420
    pop = r"\fscx0\fscy0\t(0,180,\fscx106\fscy106)\t(180,280,\fscx100\fscy100)"
    ev.append(f"Dialogue: 7,{ts(e0)},{ts(TOTAL)},ShapeC,,0,0,0,,"
              rf"{{\pos({CX + 6},{cy + 9})\c{COCOA}\1a&H80&\blur4{pop}\p1}}{rrect(cw, chh, 34)}{{\p0}}")
    ev.append(f"Dialogue: 7,{ts(e0)},{ts(TOTAL)},ShapeC,,0,0,0,,"
              rf"{{\pos({CX},{cy})\c{CREAM}\3c&HFFFFFF&\bord5{pop}\p1}}{rrect(cw, chh, 34)}{{\p0}}")
    ev.append(f"Dialogue: 7,{ts(e0)},{ts(TOTAL)},ShapeC,,0,0,0,,"
              rf"{{\pos({CX},{cy})\c{CARAMEL}{pop}\p1}}{stitches(cw - 28, chh - 28, 26, dash=16, gap=10, th=4)}{{\p0}}")
    ev.extend(label(e0 + 0.3, TOTAL, "BANTAL *LAPIK DUDUK*", y=cy - 160, box=ROSE, col=WHITE, hi=BUTTER, st=CREAM,
                    layer=9, size=50))
    ev.extend(label(e0 + 0.55, TOTAL, "PETAK • BULAT • 40CM", y=cy - 65, box=CREAM, col=COCOA, st=CARAMEL,
                    layer=9, size=40))
    for k, col in enumerate((CARAMEL, BLUSH, DOVE)):
        d = 800 + 120 * k
        ev.append(f"Dialogue: 9,{ts(e0)},{ts(TOTAL)},ShapeC,,0,0,0,,"
                  rf"{{\pos({CX - 90 + 90 * k},{cy + 25})\c{col}\3c&HFFFFFF&\bord4\fscx0\fscy0"
                  rf"\t({d},{d + 160},\fscx115\fscy115)\t({d + 160},{d + 260},\fscx100\fscy100)\p1}}{rrect(62, 62, 31)}{{\p0}}")
    ev.extend(label(e0 + 1.2, TOTAL, "KORANG NAK *KALER MANA*?", y=cy + 110, box=CREAM, col=COCOA, hi=ROSE,
                    st=CARAMEL, layer=9, size=40))
    ev.extend(label(e0 + 1.45, TOTAL, "TEKAN BEG KUNING", y=cy + 190, box=BUTTER, col=COCOA, st=CREAM,
                    layer=9, size=46))
    ev.extend(flowers(e0 + 0.3, y=cy - 160, layer=8, spots=((-240, -70), (235, -80))))
    bstk("🛒", e0 + 1.5, TOTAL, SR, cy + 190, 80)
    sfx += [("whoosh", e0 - 0.1, 0.4), ("puff", e0 + 0.05, 0.6), ("pop", e0 + 0.3, 0.45), ("pop", e0 + 0.55, 0.45),
            ("click", e0 + 0.8, 0.4), ("click", e0 + 0.92, 0.4), ("click", e0 + 1.04, 0.4), ("pop", e0 + 1.2, 0.4),
            ("ding", e0 + 1.45, 0.4)]
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
