#!/usr/bin/env python3
"""Edit for the 75cm white 'bambam' cat hug pillow TikTok video (IMG_2941).

All overlays stay inside the TikTok safe zone (SAFE_* below): nothing under the
right-hand profile/like/comment/share column, the bottom caption area or the top tabs.

Needs the Fredoka Bold font (fonts/Fredoka-Bold.ttf, SIL OFL) installed, e.g. in ~/.fonts.

Usage: python3 edit.py <proxy.mp4> <transcript.json> <sfx_dir> <out_dir> [--final]
  preview: 720x1280 proxy -> preview.mp4;  --final: 1080x1920 master -> final.mp4
  --audio-only: re-mix voice + SFX onto the existing render -> *_voice.mp4

All times in BLOCKS are source times of the original clip (same timeline as
the proxy). The script builds:
  base.mp4     - cut/zoomed video + cleaned voice + SFX
  overlay.ass  - captions, cat-ear tags, whiskers, cat-blink transitions, yarn progress bar, end card
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
# Single source clip IMG_2941 (indoors, plush shelf behind, fried-egg flower pillow in front): she hugs a tall
# white cat pillow (calico ears/tail, stitched round 'paws') upright the whole time; 33.9-40.2 is a close-up of
# the cat's face with no talking.
# v: list of (src_in, src_out, speed, zoom); a zoom change inside a block is a punch-in on the beat
# a: 'same' (follow v at speed 1), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK (J-cut over the silent face close-up at the end): "Bambamnya kucing ni. | Comel,"
    #  (the opening "Ah, kucing." is dropped)
    dict(name="hook", a=[(3.66, 5.30), (5.65, 6.78)], v=[(33.90, 35.40, 1, 1.0), (35.40, 36.67, 1, 1.08)]),
    # "saiz dia 75cm macam tu."
    dict(name="saiz", a="same", v=[(6.86, 9.08, 1, 1.0)]),
    # ("Okay" cut) "Dia punya material bulu-bulu fluffy, | lembut, bambam macam ni."  (breath 12.7-13.3 cut;
    #  she strokes the cat in close, so a small punch-in on the second half)
    dict(name="material", a="same", v=[(9.83, 12.70, 1, 1.0), (13.22, 15.30, 1, 1.08)]),
    # ("Gitu awak. Okey, lembutnya." cut - repeat) "Boleh buat bantal peluk."
    dict(name="peluk", a="same", v=[(17.94, 19.15, 1, 1.0)]),
    # "Boleh buat bantal untuk anak nak baring."
    dict(name="anak", a="same", v=[(19.20, 21.86, 1, 1.05)]),
    # "Kita pun boleh nak baring ke,"  ("kan" cut)
    dict(name="kita", a="same", v=[(21.86, 23.50, 1, 1.0)]),
    # "atau nak alas belakang dekat dalam kereta ke."
    dict(name="kereta", a="same", v=[(23.80, 26.68, 1, 1.0)]),
    # (27.1-33.7 price lines cut - no-price rule)  end card over the face close-up, no voice
    dict(name="end", a=None, v=[(36.67, 40.12, 1, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "bantai": "bantal", "reto": "kereta", "alah": "alas", "bamba": "bambam",
       "Bambamnya": "Bambamnya", "size": "saiz"}
# hand-checked words where Whisper drifted or misheard (re-transcribed per clip)
def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


OVERRIDE = {
    # the full-file pass put "Dia" at 9.34-9.94 (on top of the cut "Okay"); per-clip pass timing
    9.83: _w(("Dia", 9.86, 10.02), ("punya", 10.02, 10.22), ("material", 10.22, 10.70), ("bulu", 10.70, 11.36),
             ("-bulu", 11.36, 11.74), ("fluffy,", 11.74, 12.40)),
    21.86: _w(("Kita", 21.88, 22.12), ("pun", 22.12, 22.30), ("boleh", 22.30, 22.46), ("nak", 22.46, 22.64),
              ("baring", 22.64, 23.16), ("ke,", 23.16, 23.46)),
    23.80: _w(("Atau", 23.82, 24.20), ("nak", 24.20, 24.40), ("alas", 24.40, 24.58), ("belakang", 24.58, 25.24),
              ("dekat", 25.24, 25.48), ("dalam", 25.48, 25.70), ("kereta", 25.70, 26.20), ("ke.", 26.26, 26.62)),
}
DROP = [(21.80, 21.85)]       # full-file "Kita" timing straddles the anak/kita split; the kita clip captions it
HILITE = {"KUCING", "BAMBAMNYA", "BAMBAM", "COMEL", "SAIZ", "75CM", "MATERIAL", "BULU-BULU", "FLUFFY", "LEMBUT",
          "BANTAL", "PELUK", "ANAK", "BARING", "KERETA", "BELAKANG"}

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


# palette from the white calico cat: soft ink for text/outlines, inner-ear blush, rose, sky blue (contrast on
# white fur), calico taupe/caramel, cream, butter
INK = bgr("#3A2E39")
BLUSH = bgr("#FFB3CF")
ROSE = bgr("#F0609A")
SKY = bgr("#9AD4F5")
TAUPE = bgr("#B8936E")
CREAM = bgr("#FFF6EC")
BUTTER = bgr("#FFE27A")
WHITE = "&H00FFFFFF&"
KEY = bgr("#BFE6FF")          # caption keywords: pale sky

ASS_HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Fredoka,56,&H00FFFFFF,&H000000FF,{INK[:-1]},&H70392E3A,-1,0,0,0,100,100,0,0,1,4,2,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Label,Fredoka,60,{INK[:-1]},&H000000FF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
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


def ear(w, h):
    """Rounded-tip cat ear (triangle), w wide at the base, h tall, centred on \\pos with \\an5."""
    k = w * 0.12
    return norm(f"m {-w / 2:.0f} {h / 2:.0f} l {-k:.0f} {-h / 2 + k:.0f} b 0 {-h / 2 - k * 0.4:.0f} 0 {-h / 2 - k * 0.4:.0f} "
                f"{k:.0f} {-h / 2 + k:.0f} l {w / 2:.0f} {h / 2:.0f}")


def circle(r):
    k = 0.5523 * r
    return norm(f"m 0 {-r:.0f} b {k:.0f} {-r:.0f} {r:.0f} {-k:.0f} {r:.0f} 0 b {r:.0f} {k:.0f} {k:.0f} {r:.0f} 0 {r:.0f} "
                f"b {-k:.0f} {r:.0f} {-r:.0f} {k:.0f} {-r:.0f} 0 b {-r:.0f} {-k:.0f} {-k:.0f} {-r:.0f} 0 {-r:.0f}")


def bar(l, th):
    """Thin rounded stroke l long, th thick (a whisker), centred on \\pos with \\an5."""
    return rrect(l, th, th / 2 - 0.1)


def captions(words):
    """3-word chunks. Refresh: the active word gets a soft blush-pink glow (blurred thick border behind white
    text) and swells to 108%; keywords wait in pale sky blue."""
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
            for k, t in enumerate(toks):
                fade = r"\fad(60,0)" if j == 0 else ""
                if k == j:
                    swell = r"\fscx100\fscy100\t(0,90,\fscx108\fscy108)"
                    ev.append(f"Dialogue: 2,{ts(ws)},{ts(we)},Cap,,0,0,0,,"
                              rf"{{\an5\pos({xs[k]:.0f},{cy:.0f})\fs{size}\c{ROSE}\3c{BLUSH}\bord11\blur7\shad0{swell}}}{t}")
                    ev.append(f"Dialogue: 3,{ts(ws)},{ts(we)},Cap,,0,0,0,,"
                              rf"{{\an5\pos({xs[k]:.0f},{cy:.0f})\fs{size}\c&HFFFFFF&\3c{ROSE}\bord3.5\shad0{swell}}}{t}")
                else:
                    col = KEY if (t.strip("-?!") in HILITE or t in HILITE) else "&H00FFFFFF&"
                    ev.append(f"Dialogue: 2,{ts(ws)},{ts(we)},Cap,,0,0,0,,"
                              rf"{{\an5\pos({xs[k]:.0f},{cy:.0f})\fs{size}\c{col}{fade}}}{t}")
    return ev


def fit_size(text, size, max_w):
    w = text_w(text, size)
    return size if w <= max_w else int(size * max_w / w)


def drop_in(x, y, d=60):
    """Refresh entrance: the tag drops in from above, lands with a little squash and settles."""
    return (rf"\move({x:.0f},{y - d:.0f},{x:.0f},{y:.0f},0,170)\alpha&HFF&\t(0,90,\alpha&H00&)"
            rf"\t(170,240,\fscx107\fscy92)\t(240,330,\fscx100\fscy100)\fad(0,130)")


def label(t0, t1, text, y=250, col=INK, box=CREAM, hi=ROSE, hi2=TAUPE, inner=BLUSH, layer=5, size=58,
          emoji=None, stickers=None, whisk=True):
    """Refresh: a 'cat-ear tag' - flat rounded tag with an ink outline and two little cat ears (blush inside) on
    top, soft ink drop shadow, no tilt. Drops in from above with a squash. *x* = hi colour, ~x~ = hi2 colour.
    Optional whiskers fan out from both sides."""
    plain = text.replace("*", "").replace("~", "")
    lines = plain.split("|")
    size = min(fit_size(ln, size, SAFE_W - 190) for ln in lines)
    tw = max(text_w(ln, size) for ln in lines)
    bh = len(lines) * size * 1.02 + 30
    bw = tw + 64
    cx = CX
    txt, mode = "", None
    for ch in text.replace("|", "\n"):
        if ch in "*~":
            want = None if mode == ch else ch
            mode = want
            txt += rf"{{\c{hi if mode == '*' else hi2 if mode == '~' else col}}}"
        else:
            txt += r"\N" if ch == "\n" else ch
    ew, eh = 46, 40
    exl, exr, ey = cx - bw / 2 + 40, cx + bw / 2 - 40, y - bh / 2 - eh / 2 + 8
    ev = [
        # shadow, ears (behind the tag so its outline covers their base), inner ears, tag, text
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{{{drop_in(cx + 4, y + 9)}\\c{INK}\\1a&H90&\\blur3\\p1}}{rrect(bw, bh, 26)}{{\\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{{{drop_in(exl, ey)}\\c{box}\\3c{INK}\\bord4\\p1}}{ear(ew, eh)}{{\\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{{{drop_in(exr, ey)}\\c{box}\\3c{INK}\\bord4\\p1}}{ear(ew, eh)}{{\\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{{{drop_in(exl, ey + 6)}\\c{inner}\\p1}}{ear(ew * 0.5, eh * 0.55)}{{\\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{{{drop_in(exr, ey + 6)}\\c{inner}\\p1}}{ear(ew * 0.5, eh * 0.55)}{{\\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{{{drop_in(cx, y)}\\c{box}\\3c{INK}\\bord4\\p1}}{rrect(bw, bh, 26)}{{\\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},Label,,0,0,0,,{{\\an5{drop_in(cx, y + 2)}\\fs{size}\\c{col}}}{txt}",
    ]
    if whisk:
        ev += whiskers(t0, t1, cx, y, bw, layer)
    if emoji and stickers is not None:
        stickers.append((emoji, t0 + 0.17, t1, cx + bw / 2 - 6, y + bh / 2 + 6, 68))
    return ev


def whiskers(t0, t1, cx, y, bw, layer=5):
    """Refresh motif: three short ink whiskers fan out from each side of a tag and fade with it."""
    ev = []
    for side in (-1, 1):
        x = cx + side * (bw / 2 + 30)
        for i, (dy, rot) in enumerate(((-14, 12), (0, 0), (14, -12))):
            r = rot * side
            ev.append(f"Dialogue: {layer},{ts(t0 + 0.2)},{ts(t1)},ShapeC,,0,0,0,,"
                      rf"{{\pos({x:.0f},{y + dy:.0f})\org({cx:.0f},{y + dy:.0f})\frz{r}\c{INK}\fscx0"
                      rf"\t({40 * i},{140 + 40 * i},\fscx100)\fad(0,130)\p1}}{bar(34, 5)}{{\p0}}")
    return ev


def blink(t0, layer=11):
    """Refresh transition: a 'cat blink' - two cream eyelids (with an ink lash line) close from top and bottom in
    0.11s and open again over the cut."""
    top = f"m 0 0 l {W} 0 {W} {H // 2} 0 {H // 2}"
    lash = f"m 0 0 l {W} 0 {W} 10 0 10"
    ev = []
    for a, b, opening in ((t0 - 0.11, t0, False), (t0, t0 + 0.12, True)):
        y0, y1 = (0, -H // 2) if opening else (-H // 2, 0)
        b0, b1 = (H // 2, H) if opening else (H, H // 2)
        ms = int((b - a) * 1000)
        ev += [f"Dialogue: {layer},{ts(a)},{ts(b)},Shape,,0,0,0,,{{\\an7\\move(0,{y0},0,{y1},0,{ms})\\c{CREAM}\\p1}}{top}{{\\p0}}",
               f"Dialogue: {layer},{ts(a)},{ts(b)},Shape,,0,0,0,,{{\\an7\\move(0,{y0 + H // 2 - 10},0,{y1 + H // 2 - 10},0,{ms})\\c{INK}\\p1}}{lash}{{\\p0}}",
               f"Dialogue: {layer},{ts(a)},{ts(b)},Shape,,0,0,0,,{{\\an7\\move(0,{b0},0,{b1},0,{ms})\\c{CREAM}\\p1}}{top}{{\\p0}}",
               f"Dialogue: {layer},{ts(a)},{ts(b)},Shape,,0,0,0,,{{\\an7\\move(0,{b0},0,{b1},0,{ms})\\c{INK}\\p1}}{lash}{{\\p0}}"]
    return ev


def cat_card(t0, t1, x, y, w=400, h=260, layer=8):
    """End card: a big cream cat-head card (ears with blush insides, ink outline), sleepy ^ ^ eyes, pink nose
    and whiskers, popping in with a bounce."""
    pop = r"\fscx0\fscy0\t(0,200,\fscx108\fscy108)\t(200,300,\fscx100\fscy100)"
    org = rf"\org({x},{y})"
    ew, eh = 120, 100
    ev = [
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{{\\pos({x + 8},{y + 12}){org}\\c{INK}\\1a&H80&\\blur4{pop}\\p1}}{rrect(w, h, 70)}{{\\p0}}",
    ]
    for side in (-1, 1):
        ex = x + side * (w / 2 - 80)
        ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{{\\pos({ex:.0f},{y - h / 2 - 30:.0f}){org}\\c{CREAM}\\3c{INK}\\bord6{pop}\\p1}}{ear(ew, eh)}{{\\p0}}")
        ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{{\\pos({ex:.0f},{y - h / 2 - 18:.0f}){org}\\c{BLUSH}{pop}\\p1}}{ear(ew * 0.5, eh * 0.55)}{{\\p0}}")
    ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{{\\pos({x},{y}){org}\\c{CREAM}\\3c{INK}\\bord6{pop}\\p1}}{rrect(w, h, 70)}{{\\p0}}")
    # sleepy eyes (^ ^), nose, whiskers
    for side in (-1, 1):
        exx = x + side * 70
        ev.append(f"Dialogue: {layer + 1},{ts(t0)},{ts(t1)},Label,,0,0,0,,{{\\an5\\pos({exx},{y - 68}){org}\\fs54\\c{INK}{pop}}}^")
        for i, (dy, rot) in enumerate(((-12, 10), (4, 0), (20, -10))):
            wx = x + side * (w / 2 - 4)
            ev.append(f"Dialogue: {layer + 1},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{{\\pos({wx:.0f},{y - 40 + dy})\\org({x},{y - 40 + dy})"
                      rf"\frz{rot * side}\c{{INK}}{pop}\p1}}{bar(70, 6)}{{\p0}}".replace("{INK}", INK))
    ev.append(f"Dialogue: {layer + 1},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{{\\pos({x},{y - 44}){org}\\c{ROSE}{pop}\\fscy70\\p1}}{circle(12)}{{\\p0}}")
    return ev


def graphics():
    ev, stickers, sfx = [], [], []
    # progress bar (retention): ink track, blush 'yarn' line with a rose yarn ball rolling at its front
    ms = int(TOTAL * 1000)
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{INK}\1a&H60&\p1}}m 0 0 l {W} 0 {W} 8 0 8{{\p0}}")
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{BLUSH}\clip(0,0,0,8)\t(0,{ms},\clip(0,0,{W},8))\p1}}m 0 0 l {W} 0 {W} 8 0 8{{\p0}}")
    ev.append(f"Dialogue: 9,{ts(0)},{ts(TOTAL)},ShapeC,,0,0,0,,"
              rf"{{\move(0,10,{W},10,0,{ms})\c{ROSE}\3c{CREAM}\bord2\p1}}{circle(9)}{{\p0}}")
    ev.append(f"Dialogue: 10,{ts(0)},{ts(TOTAL)},ShapeC,,0,0,0,,"
              rf"{{\move(0,10,{W},10,0,{ms})\c{CREAM}\1a&H40&\frz35\p1}}{bar(16, 2.4)}{{\p0}}")

    def lab(s0, s1, text, sound="pop", vol=0.5, emoji=None, **kw):
        ev.extend(label(tl(s0), tl(s1), text, emoji=emoji, stickers=stickers, **kw))
        if sound:
            sfx.append((sound, tl(s0) + 0.12, vol))

    def cut(src, sound="blink", vol=0.55):
        t0 = tl(src)
        ev.extend(blink(t0))
        sfx.append((sound, t0 - 0.11, vol))

    # ---- HOOK: plump cat close-up
    lab(3.70, 5.30, "*BAMBAM*-NYA|KUCING NI!", emoji="😻", sound="squeak", vol=0.45, size=64, box=WHITE, y=640)
    lab(5.70, 6.76, "*COMEL!*", emoji="🥰", sound="pop", vol=0.5, size=74, box=BUTTER, hi=ROSE, y=640)

    # ---- size
    cut(6.86)
    lab(6.92, 9.05, "SAIZ *75CM*", emoji="📏", sound="pop", vol=0.5, size=66, box=SKY, hi=ROSE, col=INK)

    # ---- fur
    cut(9.83)
    lab(10.22, 12.66, "BULU-BULU *FLUFFY*", emoji="☁️", sound="pop", vol=0.45)
    lab(13.32, 15.26, "LEMBUT & *BAMBAM*", emoji="🤍", sound="squeak", vol=0.35, box=WHITE)

    # ---- uses
    cut(17.94)
    lab(17.98, 19.12, "BANTAL *PELUK*", emoji="🤗", sound="pop", vol=0.45, box=BUTTER)
    lab(19.30, 21.80, "ANAK NAK *BARING*", emoji="💤", sound="pop", vol=0.45, box=SKY, hi=ROSE)
    lab(21.90, 23.46, "KITA PUN *BOLEH*!", emoji="🙌", sound="pop", vol=0.45)
    cut(23.80)
    lab(24.20, 26.60, "ALAS BELAKANG|DALAM *KERETA*", emoji="🚗", sound="pop", vol=0.45, box=BLUSH, hi=INK, col=INK, size=54, y=262)

    # ---- end card: big cat-head card + stacked cat-ear tags
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 6,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{INK}\1a&HFF&\t(0,250,\1a&H70&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    ev.extend(blink(e0))
    ev.extend(cat_card(e0 + 0.12, TOTAL, CX, 430))
    ev.append(f"Dialogue: 10,{ts(e0 + 0.12)},{ts(TOTAL)},Label,,0,0,0,,{{\\an5\\pos({CX},{450})\\fs52\\c{INK}"
              r"\fscx0\fscy0\t(0,200,\fscx108\fscy108)\t(200,300,\fscx100\fscy100)}"
              rf"BANTAL {{\c{ROSE}}}KUCING")
    ev.append(f"Dialogue: 10,{ts(e0 + 0.3)},{ts(TOTAL)},Label,,0,0,0,,{{\\an5\\pos({CX},{505})\\fs30\\c{TAUPE}\\fad(150,0)}}"
              "75CM • BAMBAM • FLUFFY")
    ev.extend(label(e0 + 0.6, TOTAL, "KORANG *TEAM KUCING*?", y=690, box=SKY, hi=ROSE, layer=9, size=42,
                    emoji="🐱", stickers=stickers, whisk=False))
    ev.extend(label(e0 + 0.95, TOTAL, "TEKAN BEG KUNING", y=800, box=BUTTER, layer=9, size=44,
                    emoji="🛒", stickers=stickers, whisk=False))
    sfx += [("blink", e0 - 0.11, 0.55), ("squeak", e0 + 0.15, 0.4), ("sparkle", e0 + 0.35, 0.3),
            ("pop", e0 + 0.7, 0.45), ("ding", e0 + 1.05, 0.4)]
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
