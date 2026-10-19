#!/usr/bin/env python3
"""Edit for the 90cm banana + eggplant (pisang & terung) hug pillow TikTok video.

All overlays stay inside the TikTok safe zone (SAFE_* below): nothing under the
right-hand profile/like/comment/share column, the bottom caption area or the top tabs.

Needs the Fredoka Bold font (fonts/Fredoka-Bold.ttf, SIL OFL) installed, e.g. in ~/.fonts.

Usage: python3 edit.py <proxy.mp4> <transcript.json> <sfx_dir> <out_dir> [--final]
  preview: 720x1280 proxy -> preview.mp4;  --final: 1080x1920 master -> final.mp4
  --audio-only: re-mix voice + SFX onto the existing render -> *_voice.mp4

All times in BLOCKS are source times of the original clip (same timeline as
the proxy). The script builds:
  base.mp4     - cut/zoomed video + cleaned voice + SFX
  overlay.ass  - captions, slanted badges, duo wipes, hearts, progress bar, end card
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
# Single source clip IMG_2936 (indoors, in front of the plush shelf): two long 90cm hug pillows with faces and
# little arms/legs, a yellow banana and a purple eggplant (terung), held side by side the whole time.
# v: list of (src_in, src_out, speed, zoom); a zoom change inside a block is a punch-in on the beat
# a: 'same' (follow v at speed 1), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK (moved from 10.5s, J-cut over the eggplant close-up): "Jarang-jarang kita jumpa desain yang terung
    #  macam ni kan."
    dict(name="hook", a=[(10.47, 12.70)], v=[(16.80, 19.03, 1, 1.0)]),
    # "Cantiknya terung dengan pisang ni. | Unik kan desain dia, dah lah panjang."
    dict(name="cantik", a="same", v=[(0.62, 3.75, 1, 1.0), (3.75, 6.12, 1, 1.08)]),
    # "90cm."  (breath after it cut)
    dict(name="saiz", a="same", v=[(6.42, 7.58, 1, 1.12)]),
    # "(Ah) buat bantal peluk, best ni kan."
    dict(name="peluk", a="same", v=[(7.92, 10.20, 1, 1.0)]),
    # (the hook line 10.5-12.7 already played)  "Yang mana pun minat purple, korang ambillah terung yang comel doh ni."
    dict(name="purple", a="same", v=[(13.10, 17.40, 1, 1.0)]),
    # "Kalau minat warna kuning ambil pisang, | saiz dia sama 90cm."  (she brings each one to the camera)
    dict(name="kuning", a="same", v=[(17.70, 20.36, 1, 1.0), (20.36, 22.96, 1, 1.08)]),
    # ("Okay" cut) "Nak buat hadiah pun sangat-sangat sesuai."
    dict(name="hadiah", a="same", v=[(23.26, 25.56, 1, 1.0)]),
    # ("Ha," cut) "Ni siapa nak letak dekat bilik tidur ke ataupun nak letak dalam kereta, | boleh juga tapi besar
    #  sikit pula dalam kereta tu. | Tak apa letak kat bilik dekat katil."  ("paling sesak/sedap" unclear, cut)
    dict(name="bilik", a="same", v=[(26.86, 31.86, 1, 1.0), (31.86, 34.05, 1, 1.07), (34.05, 35.56, 1, 1.0)]),
    # ("Okey," cut) "Ada ni kita boleh peluk sambil tidur."
    dict(name="tidur", a="same", v=[(36.90, 39.08, 1, 1.0)]),
    # ("Okey." cut) "...dekat beg kuning."  - end card over both pillows, gentle slow-mo
    dict(name="end", a=[(39.58, 41.55)], v=[(22.90, 24.48, 0.8, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "bantai": "bantal", "Kala": "Kalau", "Okey": "Okay"}
# hand-checked words where Whisper drifted or misheard (re-transcribed per clip)
def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


OVERRIDE = {
    # "Okey. Gerai/(tengok) dekat beg kuning" - the mumbled word before "dekat" is left uncaptioned
    39.58: _w(("Dekat", 39.76, 39.94), ("beg", 39.94, 40.10), ("kuning.", 40.10, 40.76)),
}
DROP = []
HILITE = {"TERUNG", "PISANG", "UNIK", "DESAIN", "PANJANG", "90CM", "BANTAL", "PELUK", "BEST", "PURPLE", "COMEL",
          "KUNING", "SAIZ", "SAMA", "HADIAH", "SESUAI", "BILIK", "TIDUR", "KERETA", "BESAR", "KATIL", "JARANG-JARANG"}

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




# palette from the two plushies: deep plum for text/outline, eggplant purple, light lilac, banana yellow,
# pale butter, stem green, cheek pink, cream
PLUM = bgr("#2E1A4F")
PURP = bgr("#7B4FD6")
LILAC = bgr("#C9B5FF")
YEL = bgr("#FFE14D")
BUTTER = bgr("#FFF2A8")
STEM = bgr("#3FAE49")
CHEEK = bgr("#FF8FB1")
CREAM = bgr("#FFF7E0")
WHITE = "&H00FFFFFF&"
KEY = bgr("#FFE98A")          # caption keywords: soft banana

ASS_HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Fredoka,58,&H00FFFFFF,&H000000FF,{PLUM[:-1]},&H704F1A2E,-1,0,0,0,100,100,0,0,1,5,2,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Label,Fredoka,60,{PLUM[:-1]},&H000000FF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
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


def captions(words):
    """3-word chunks. Refresh: the active word turns eggplant purple with a white rim and a hard banana-yellow
    drop shadow (a little 3D 'duo' look), rising 6px as it lights up."""
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
        size = 58
        while text_w(" ".join(toks), size) + text_w(" ", size) * 0.8 * (len(toks) - 1) > SAFE_W - 70 and size > 36:
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
                    ev.append(f"Dialogue: 3,{ts(ws)},{ts(we)},Cap,,0,0,0,,"
                              rf"{{\an5\move({xs[k]:.0f},{cy:.0f},{xs[k]:.0f},{cy - 6:.0f},0,90)\fs{size}\c{PURP}\3c&HFFFFFF&"
                              rf"\bord5\4c{YEL}\4a&H00&\xshad4\yshad5}}{t}")
                else:
                    col = KEY if (t.strip("-?!") in HILITE or t in HILITE) else "&H00FFFFFF&"
                    ev.append(f"Dialogue: 2,{ts(ws)},{ts(we)},Cap,,0,0,0,,"
                              rf"{{\an5\pos({xs[k]:.0f},{cy:.0f})\fs{size}\c{col}{fade}}}{t}")
    return ev


def fit_size(text, size, max_w):
    w = text_w(text, size)
    return size if w <= max_w else int(size * max_w / w)


def label(t0, t1, text, y=235, col=PLUM, box=YEL, hi=PURP, hi2=STEM, stripe=PURP, layer=5, size=60,
          emoji=None, stickers=None, side=1):
    """Refresh: a slanted 'badge' (parallelogram leaning right) with a hard plum offset shadow, a coloured
    stripe on the leading edge, and the emoji as a corner sticker on the top-right tip. It stamps in
    (big + transparent -> settles) instead of sliding or popping. *x* = hi colour, ~x~ = hi2 colour."""
    plain = text.replace("*", "").replace("~", "")
    lines = plain.split("|")
    size = min(fit_size(ln, size, SAFE_W - 150) for ln in lines)
    tw = max(text_w(ln, size) for ln in lines)
    bh = len(lines) * size * 1.02 + 28
    s = bh * 0.16                                 # lean
    bw = tw + 70
    cx = CX - 12
    txt, mode = "", None
    for ch in text.replace("|", "\n"):
        if ch in "*~":
            want = None if mode == ch else ch
            mode = want
            txt += rf"{{\c{hi if mode == '*' else hi2 if mode == '~' else col}}}"
        else:
            txt += r"\N" if ch == "\n" else ch
    stamp = (r"\fscx135\fscy135\alpha&HFF&\t(0,130,\fscx95\fscy95\alpha&H00&)\t(130,220,\fscx100\fscy100)"
             r"\fad(0,140)")
    ev = [
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{{\\pos({cx + 7:.0f},{y + 8})\\c{PLUM}{stamp}\\p1}}{slant(bw, bh, s)}{{\\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{{\\pos({cx:.0f},{y})\\c{box}\\3c&HFFFFFF&\\bord4{stamp}\\p1}}{slant(bw, bh, s)}{{\\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{{\\pos({cx - bw / 2 + 14:.0f},{y})\\c{stripe}{stamp}\\p1}}{slant(14, bh - 4, s)}{{\\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},Label,,0,0,0,,{{\\an5\\pos({cx + 8:.0f},{y})\\fs{size}\\c{col}{stamp}}}{txt}",
    ]
    if emoji and stickers is not None:
        stickers.append((emoji, t0 + 0.14, t1, cx + bw / 2 + s - 6, y - bh / 2 - 8, 74))
    return ev


def hearts(t0, y=235, layer=4):
    """Refresh motif: a few small yellow + purple hearts float up from the badge and fade."""
    ev = []
    for i, (dx, dy) in enumerate(((-250, 10), (230, 30), (-200, -40), (260, -20), (-120, 50))):
        x, yy = CX + dx, y + dy
        d0 = 60 * i
        col = YEL if i % 2 else PURP
        sc = 70 + 15 * (i % 3)
        ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t0 + 1.2)},ShapeC,,0,0,0,,"
                  rf"{{\move({x:.0f},{yy:.0f},{x + (12 if i % 2 else -12):.0f},{yy - 80:.0f},{d0},1200)\c{col}\3c&HFFFFFF&\bord2"
                  rf"\fscx0\fscy0\t({d0},{d0 + 160},\fscx{sc + 15}\fscy{sc + 15})\t({d0 + 160},{d0 + 260},\fscx{sc}\fscy{sc})"
                  rf"\fad(0,350)\p1}}{HEART}{{\p0}}")
    return ev


def duo_wipe(t0, layer=9):
    """Refresh transition: a banana-yellow triangle sweeps in from the top-left and an eggplant-purple one
    from the bottom-right; they meet on the diagonal for a beat and fade (0.3s)."""
    tl_tri = f"m 0 0 l {W} 0 0 {H}"
    br_tri = f"m {W} 0 l {W} {H} 0 {H}"
    return [
        f"Dialogue: {layer},{ts(t0 - 0.12)},{ts(t0 + 0.2)},Shape,,0,0,0,,"
        rf"{{\an7\move({-W},{-H // 3},0,0,0,120)\c{YEL}\1a&H30&\t(140,320,\1a&HFF&)\p1}}{tl_tri}{{\p0}}",
        f"Dialogue: {layer},{ts(t0 - 0.12)},{ts(t0 + 0.2)},Shape,,0,0,0,,"
        rf"{{\an7\move({W},{H // 3},0,0,0,120)\c{PURP}\1a&H30&\t(140,320,\1a&HFF&)\p1}}{br_tri}{{\p0}}",
    ]


def card(t0, t1, x, y, rot, box, txt_col, title, sub, layer=8):
    """End-card 'duo' card: tilted rounded card with white rim + plum shadow, title and a small subtitle."""
    pop = (rf"\org({x},{y})\frz{rot}\fscx0\fscy0\t(0,200,\fscx108\fscy108)\t(200,300,\fscx100\fscy100)")
    return [
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{{\\pos({x + 8},{y + 10})\\c{PLUM}\\1a&H40&{pop}\\p1}}{rrect(250, 300, 34)}{{\\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{{\\pos({x},{y})\\c{box}\\3c&HFFFFFF&\\bord6{pop}\\p1}}{rrect(250, 300, 34)}{{\\p0}}",
        f"Dialogue: {layer + 1},{ts(t0)},{ts(t1)},Label,,0,0,0,,{{\\an5\\pos({x},{y + 60})\\fs46\\c{txt_col}{pop}}}{title}",
        f"Dialogue: {layer + 1},{ts(t0)},{ts(t1)},Label,,0,0,0,,{{\\an5\\pos({x},{y + 108})\\fs26\\c{txt_col}{pop}}}{sub}",
    ]


def graphics():
    ev, stickers, sfx = [], [], []
    # progress bar (retention): plum track, banana fill with a purple leading edge
    ms = int(TOTAL * 1000)
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{PLUM}\1a&H50&\p1}}m 0 0 l {W} 0 {W} 10 0 10{{\p0}}")
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{YEL}\clip(0,0,0,10)\t(0,{ms},\clip(0,0,{W},10))\p1}}m 0 0 l {W} 0 {W} 10 0 10{{\p0}}")
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\move(-8,0,{W - 8},0,0,{ms})\c{PURP}\p1}}m 0 0 l 8 0 8 10 0 10{{\p0}}")

    def lab(s0, s1, text, sound="pop", vol=0.5, love=False, emoji=None, **kw):
        ev.extend(label(tl(s0), tl(s1), text, emoji=emoji, stickers=stickers, **kw))
        if love:
            ev.extend(hearts(tl(s0), y=kw.get("y", 235)))
            sfx.append(("sparkle", tl(s0) + 0.05, 0.3))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def wipe(src, sound="swish", vol=0.5):
        t0 = tl(src)
        ev.extend(duo_wipe(t0))
        sfx.append((sound, t0 - 0.12, vol))

    # ---- HOOK: rare to find an eggplant design like this
    lab(10.55, 11.50, "*JARANG-JARANG*|JUMPA!", emoji="👀", sound="stamp", vol=0.6, size=66)
    lab(11.52, 12.68, "DESAIN *TERUNG*|MACAM NI!", size=66, box=LILAC, stripe=YEL, emoji="🍆", sound="stamp", vol=0.6)

    # ---- the pair
    wipe(0.62)
    lab(0.70, 3.66, "*TERUNG* & ~PISANG~", box=CREAM, stripe=YEL, emoji="💜", love=True, sound="duo", vol=0.5)
    lab(3.86, 5.10, "UNIK *DESAIN*!", emoji="✨", sound="pop", vol=0.45)
    lab(5.22, 6.08, "DAH LAH *PANJANG*", box=LILAC, stripe=YEL, emoji="📏", sound="pop", vol=0.45)
    lab(6.45, 7.56, "*90CM*!", box=YEL, emoji="🙌", sound="stamp", vol=0.6, size=72)
    lab(7.94, 8.68, "BUAT *BANTAL PELUK*", box=CREAM, stripe=PURP, emoji="🤗", sound="pop", vol=0.45)
    lab(8.70, 10.15, "BEST NI!", box=YEL, emoji="😍", love=True, sound="pop", vol=0.45)

    # ---- pick your colour
    wipe(13.10)
    lab(13.20, 14.42, "MINAT *PURPLE*?", box=LILAC, stripe=PURP, hi=PURP, emoji="💜", sound="duo", vol=0.5)
    lab(14.62, 17.34, "AMBIL *TERUNG* COMEL!", box=CREAM, stripe=PURP, emoji="🍆", sound="pop", vol=0.45)
    lab(17.76, 19.12, "MINAT *KUNING*?", box=BUTTER, stripe=YEL, hi=PURP, emoji="💛", sound="duo", vol=0.5)
    lab(19.30, 20.32, "AMBIL *PISANG*!", box=YEL, stripe=PURP, emoji="🍌", sound="pop", vol=0.45)
    lab(20.48, 22.36, "SAIZ SAMA *90CM*", box=CREAM, stripe=YEL, emoji="📏", sound="stamp", vol=0.55)

    # ---- gift + where to put it
    wipe(23.26)
    lab(23.40, 25.50, "SESUAI *HADIAH*!", box=YEL, emoji="🎁", love=True, sound="pop", vol=0.45)
    lab(26.90, 28.84, "HIASAN *BILIK TIDUR*", box=LILAC, stripe=YEL, emoji="🛏️", sound="pop", vol=0.45)
    lab(28.86, 31.84, "ATAU DALAM *KERETA*", box=CREAM, stripe=PURP, emoji="🚗", sound="pop", vol=0.45)
    lab(31.98, 33.86, "TAPI *BESAR SIKIT*", box=BUTTER, stripe=PURP, emoji="😅", sound="pop", vol=0.45)
    lab(34.10, 35.54, "LETAK ATAS *KATIL*", box=LILAC, stripe=YEL, emoji="🛌", sound="pop", vol=0.45)
    wipe(36.90)
    lab(36.94, 39.05, "PELUK *SAMBIL TIDUR*", box=YEL, emoji="😴", love=True, sound="duo", vol=0.5)

    # ---- end card (refresh): two tilted 'duo' cards side by side + stacked badges
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 6,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{PLUM}\1a&HFF&\t(0,250,\1a&H60&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    ev.extend(label(e0 + 0.05, TOTAL, "BANTAL PELUK *90CM*", y=230, box=CREAM, stripe=YEL, layer=9, size=48,
                    emoji="🤗", stickers=stickers))
    lx, rx, cy = CX - 130, CX + 130, 520
    ev.extend(card(e0 + 0.25, TOTAL, lx, cy, 6, YEL, PLUM, "PISANG", "KUNING CERIA"))
    ev.extend(card(e0 + 0.45, TOTAL, rx, cy, -6, PURP, WHITE, "TERUNG", "PURPLE COMEL"))
    stickers.append(("🍌", e0 + 0.35, TOTAL, lx, cy - 50, 110))
    stickers.append(("🍆", e0 + 0.55, TOTAL, rx, cy - 50, 110))
    ev.append(f"Dialogue: 10,{ts(e0 + 0.6)},{ts(TOTAL)},ShapeC,,0,0,0,,"
              rf"{{\pos({CX},{cy - 150})\c{CHEEK}\3c&HFFFFFF&\bord4\fscx0\fscy0\t(0,180,\fscx230\fscy230)"
              rf"\t(180,280,\fscx200\fscy200)\p1}}{HEART}{{\p0}}")
    ev.extend(label(e0 + 0.8, TOTAL, "KORANG *TEAM MANA*?", y=735, box=LILAC, stripe=YEL, layer=9, size=42,
                    emoji="🤔", stickers=stickers))
    ev.extend(label(e0 + 1.1, TOTAL, "TEKAN BEG KUNING", y=830, box=YEL, stripe=PURP, layer=9, size=44,
                    emoji="🛒", stickers=stickers))
    ev.extend(duo_wipe(e0, layer=11))
    sfx += [("swish", e0 - 0.12, 0.5), ("stamp", e0 + 0.05, 0.5), ("pop", e0 + 0.25, 0.45), ("pop", e0 + 0.45, 0.45),
            ("sparkle", e0 + 0.6, 0.35), ("duo", e0 + 0.8, 0.45), ("ding", e0 + 1.1, 0.4)]
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
