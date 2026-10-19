#!/usr/bin/env python3
"""Edit for the sleeping calico cat pillow (bantal kucing) TikTok video, three source clips joined.

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
# Three source clips of the same product (sleeping calico cat pillow), joined into one timeline
# (master1080/proxy = A + B + C, concat):
#   A (IMG_2938)  0.000 - 37.000s : she hugs the cat pillow and talks (all the speech is here)
#   B (IMG_2939) 37.000 - 40.838s : close-up of the cat lying on her lap (no speech)
#   C (IMG_2940) 40.838 - 45.743s : close-up of the cat's face, her hand patting its head (no speech)
# B and C are B-roll under A's voice.
# v: list of (src_in, src_out, speed, zoom)
# a: 'same' (follow v at speed 1), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK: "Peminat kucing, ambil kucing." (moved from 24.9s) over the B close-up, then "Comelnya kucing ni."
    dict(name="hook", a=[(24.86, 26.58), (0.36, 2.58)], v=[(37.05, 38.77, 1, 1.0), (0.36, 2.58, 1, 1.04)]),
    # "Kepala dia pun lembut, gebu, badan dia pun gebu."  over C (hand patting the head) then B (the body)
    dict(name="lembut", a=[(2.60, 6.64)], v=[(41.15, 43.55, 1, 1.0), (38.77, 40.41, 1, 1.08)]),
    # "Boleh buat bantal peluk, bantal kepala, bantal untuk alas belakang. Macam-macam kegunaan."
    dict(name="guna", a="same", v=[(6.65, 9.05, 1, 1.0), (9.05, 12.24, 1, 1.06)]),
    # "Korang boleh beli untuk anak korang"  ("Comel kan? / Angguk sikit", the first "tengok dekat beg kuning"
    #  and the price lines "harga dia sangat-sangat murah ... berbaloi" are cut: no price talk)
    dict(name="anak", a="same", v=[(17.27, 18.53, 1, 1.04)]),
    # "Kalau korang minat gajah, ada gajah, | ada musang, ada anak domba. Macam-macam haiwan ada ni."
    #  (0.3s pause after the second "gajah" tightened)
    dict(name="haiwan", a="same", v=[(26.62, 29.38, 1, 1.0), (29.72, 33.58, 1, 1.05)]),
    # "Korang tengok dekat beg kuning ni tahu."
    dict(name="cta", a="same", v=[(33.62, 35.08, 1, 1.0)]),
    # C: the cat's face close-up, slowed, inside the polaroid end card
    dict(name="end", a=None, v=[(43.55, 45.70, 0.85, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "bantai": "bantal", "Okey": "Okay", "itu": "tu", "berbalut": "berbaloi"}
# hand-checked words where Whisper drifted or misheard (re-transcribed per clip)
def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


OVERRIDE = {
    24.86: _w(("Peminat", 24.90, 25.24), ("kucing,", 25.24, 25.62), ("ambil", 25.70, 25.90), ("kucing.", 25.90, 26.54)),
    0.36: _w(("Comelnya", 0.40, 1.04), ("kucing", 1.04, 1.50), ("ni.", 1.50, 2.20)),
    17.27: _w(("Korang", 17.30, 17.42), ("boleh", 17.42, 17.62), ("beli", 17.62, 17.86), ("untuk", 17.86, 18.04),
              ("anak", 18.04, 18.22), ("korang.", 18.22, 18.50)),
    29.72: _w(("ada", 29.74, 29.84), ("musang,", 29.84, 30.66), ("ada", 31.14, 31.28), ("anak", 31.28, 31.54),
              ("domba.", 31.54, 32.24), ("Macam", 32.56, 32.62), ("-macam", 32.62, 32.84), ("haiwan", 32.84, 33.16),
              ("ada", 33.16, 33.38), ("ni.", 33.38, 33.56)),
    33.62: _w(("Korang", 33.64, 33.82), ("tengok", 33.82, 33.98), ("dekat", 33.98, 34.16), ("beg", 34.16, 34.28),
              ("kuning", 34.28, 34.42), ("ni", 34.42, 34.56), ("tahu.", 34.56, 35.00)),
}
DROP = []
HILITE = {"KUCING", "KUCING.", "KUCING,", "LEMBUT", "LEMBUT,", "GEBU", "GEBU,", "GEBU.", "PELUK", "PELUK,", "KEPALA",
          "KEPALA,", "BELAKANG", "BELAKANG.", "ANAK", "GAJAH", "GAJAH,", "MUSANG", "MUSANG,", "DOMBA", "DOMBA.",
          "HAIWAN", "BEG", "KUNING"}

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
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Fredoka,58,&H00FFFFFF,&H000000FF,&H00202C4A,&H78202C4A,-1,0,0,0,100,100,0,0,1,4,2,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Pill,Fredoka,62,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,5,40,40,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,&H00202C4A,&H64202C4A,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# palette from the calico cat: cocoa (dark patch / text), caramel (ginger patch), cream (fur), blush (nose),
# lilac + sage (the flower pillows around her), butter yellow for the beg kuning CTA
COCOA = "&H00202C4A&"    # #4A2C20
CARAMEL = "&H004E9AE9&"  # #E99A4E
CREAM = "&H00E6F5FF&"    # #FFF5E6
BLUSH = "&H008B66F2&"    # #F2668B  active caption word blob, flashes, progress bar
LILAC = "&H00F29CB7&"    # #B79CF2
SAGE = "&H00B1CF9C&"     # #9CCFB1
YELLOW = "&H003FD2FF&"   # #FFD23F
WHITE = "&H00FFFFFF&"
KEY = CARAMEL


def captions(words):
    """3-word chunks; the active word gets a soft blush 'highlighter blob' (thick blush outline) - refresh v4."""
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
        for j, w in enumerate(ch):
            ws = w["s"] if j else min(w["s"], ch[0]["s"])
            we = ch[j + 1]["s"] if j + 1 < len(ch) else end
            parts = []
            for k, x in enumerate(ch):
                t = x["w"].upper().strip(",.")
                if k == j:
                    parts.append(r"{\c%s\3c%s\bord11\shad0\fscx108\fscy108}%s{\r}" % (WHITE, BLUSH, t))
                elif t.strip("-") in HILITE or t in HILITE:
                    parts.append(r"{\c%s}%s{\r}" % (KEY, t))
                else:
                    parts.append(t)
            pop = r"{\fscx85\fscy85\t(0,90,\fscx100\fscy100)}" if j == 0 else ""
            ev.append(f"Dialogue: 2,{ts(ws)},{ts(we)},Cap,,0,0,0,,{pop}" + " ".join(parts))
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


POP = r"\fscx0\fscy0\t(0,140,\fscx112\fscy112)\t(140,240,\fscx100\fscy100)\fad(0,150)"


def pill(t0, t1, text, y=228, col=COCOA, fill=CREAM, hi=WHITE, rot=-2, layer=5, x=CX, size=62):
    """Refresh v4: rounded pill sticker (white rim + soft cocoa drop shadow) instead of the square tilted box.
    *word* is drawn in the highlight colour."""
    size = fit_size(text, size)
    plain = text.replace("*", "")
    w = _font(size).getlength(plain) * ASS_PER_PIL + size * 0.9
    h = size * 1.22
    parts = text.split("*")
    txt = "".join(p if i % 2 == 0 else rf"{{\c{hi}}}{p}{{\c{col}}}" for i, p in enumerate(parts))
    return [
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
        rf"{{\an5\pos({x},{y})\frz{rot}\c{fill}\3c{WHITE}\bord6\4c{COCOA}\4a&H90&\shad4{POP}\p1}}{rrect(w, h, h / 2)}{{\p0}}",
        f"Dialogue: {layer + 1},{ts(t0)},{ts(t1)},Pill,,0,0,0,,"
        rf"{{\an5\pos({x},{y})\frz{rot}\fs{size}\c{col}{POP}}}{txt}",
    ]


def flash(t0, d=0.3, layer=9, col=BLUSH, alpha="&H90&"):
    """Refresh v4: soft blush flash instead of a white one."""
    return (f"Dialogue: {layer},{ts(t0)},{ts(t0 + d)},Shape,,0,0,0,,"
            rf"{{\an7\pos(0,0)\c{col}\1a{alpha}\fad(0,{int(d * 1000) - 40})\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")


def paw(s=1.0):
    """A cat paw print (pad + 4 toes), ~50px tall at s=1, drawn in positive coordinates (see rrect)."""
    o = 24 * s
    return " ".join([ell(o, o + 9 * s, 17 * s, 14 * s), ell(o - 17 * s, o - 9 * s, 6 * s, 7.5 * s),
                     ell(o - 6.5 * s, o - 19 * s, 6 * s, 7.5 * s), ell(o + 6.5 * s, o - 19 * s, 6 * s, 7.5 * s),
                     ell(o + 17 * s, o - 9 * s, 6 * s, 7.5 * s)])


def paw_trail(t0, x0, y0, dx, dy, col=CARAMEL, n=4, layer=4):
    """Refresh v4 motif: little paw prints walking up the side of the frame at a section change."""
    ev = []
    ang = -np.degrees(np.arctan2(dx, -dy))
    for i in range(n):
        side = 9 if i % 2 else -9
        x, y = x0 + i * dx + side, y0 + i * dy
        a = t0 + i * 0.13
        ev.append(f"Dialogue: {layer},{ts(a)},{ts(t0 + 1.5)},Shape,,0,0,0,,"
                  rf"{{\an5\pos({x:.0f},{y:.0f})\frz{ang:.0f}\c{col}\1a&H38&\bord0\shad0\fad(60,300)"
                  rf"\fscx40\fscy40\t(0,90,\fscx105\fscy105)\t(90,160,\fscx100\fscy100)\p1}}{paw(0.8)}{{\p0}}")
    return ev


def graphics():
    ev, stickers, sfx = [], [], []
    # progress bar (retention) - top edge is clear of the TikTok UI
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{BLUSH}\fscx0\t(0,{int(TOTAL * 1000)},\fscx100)\p1}}m 0 0 l {W} 0 {W} 8 0 8{{\p0}}")

    def lab(s0, s1, text, sound="pop", vol=0.5, **kw):
        ev.extend(pill(tl(s0), tl(s1), text, **kw))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def stk(em, s0, s1, x, y, size=100):
        stickers.append((em, tl(s0), tl(s1), x, y, size))

    def bstk(em, t0, t1, x, y, size=100):
        stickers.append((em, t0, t1, x, y, size))

    SL, SR, SY = 85, 555, 150     # stickers sit beside the labels, above the cat

    # ---- HOOK: cat fans -> how cute
    lab(24.90, 26.54, "PEMINAT *KUCING*?", col=WHITE, fill=BLUSH, hi=CREAM, rot=-3, size=70, sound="bloop", vol=0.5)
    stk("🐱", 24.94, 26.54, SR, SY, 105)
    ev.append(flash(tl(0.40), d=0.3))
    lab(0.40, 2.50, "*COMEL*NYA!", col=COCOA, fill=CREAM, hi=BLUSH, rot=2, size=80, sound="sparkle", vol=0.35)
    stk("🥰", 0.44, 2.50, SL, SY, 100)

    # ---- soft head + soft body
    ev.extend(paw_trail(BT["lembut"]["t0"], 70, 880, 16, -78))
    lab(2.66, 4.58, "KEPALA *LEMBUT*", col=COCOA, fill=CARAMEL, hi=WHITE, rot=-2, size=66, sound="pop", vol=0.5)
    stk("☁️", 2.70, 4.58, SR, SY, 100)
    lab(5.10, 6.60, "BADAN PUN *GEBU*", col=COCOA, fill=LILAC, hi=WHITE, rot=2, size=66, sound="pop", vol=0.5)
    stk("🤍", 5.14, 6.60, SL, SY, 95)

    # ---- uses
    lab(6.68, 7.88, "BANTAL *PELUK*", col=COCOA, fill=CREAM, hi=BLUSH, rot=-2, size=68, sound="bloop", vol=0.45)
    stk("🤗", 6.72, 7.88, SR, SY, 100)
    lab(7.92, 9.00, "BANTAL *KEPALA*", col=WHITE, fill=BLUSH, hi=CREAM, rot=2, size=68, sound="pop", vol=0.45)
    stk("😴", 7.96, 9.00, SL, SY, 100)
    lab(9.08, 10.74, "ALAS *BELAKANG*", col=COCOA, fill=CARAMEL, hi=WHITE, rot=-2, size=68, sound="pop", vol=0.45)
    stk("🛋️", 9.12, 10.74, SR, SY, 100)
    ev.append(flash(tl(10.94), d=0.25, col=CREAM))
    lab(10.94, 12.22, "MACAM-MACAM *GUNA*!", col=COCOA, fill=SAGE, hi=WHITE, rot=2, size=66, sound="ding", vol=0.4)
    stk("✨", 10.98, 12.22, SL, SY, 95)

    # ---- for the kids
    ev.extend(paw_trail(BT["anak"]["t0"], 580, 880, -16, -78, col=BLUSH))
    lab(17.30, 18.50, "UNTUK *ANAK* KORANG", col=COCOA, fill=LILAC, hi=WHITE, rot=-2, size=64, sound="bloop", vol=0.45)
    stk("🧸", 17.34, 18.50, SR, SY, 95)

    # ---- other animals too
    ev.extend(paw_trail(BT["haiwan"]["t0"], 70, 880, 16, -78, col=SAGE))
    lab(27.40, 29.00, "MINAT *GAJAH*?", col=COCOA, fill=SAGE, hi=WHITE, rot=2, size=70, sound="pop", vol=0.45)
    stk("🐘", 27.44, 29.00, SL, SY, 100)
    lab(29.80, 30.70, "ADA *MUSANG*", col=COCOA, fill=CARAMEL, hi=WHITE, rot=-2, size=70, sound="pop", vol=0.45)
    stk("🦊", 29.84, 30.70, SR, SY, 100)
    lab(31.16, 32.26, "ADA *ANAK DOMBA*", col=COCOA, fill=CREAM, hi=BLUSH, rot=2, size=66, sound="pop", vol=0.45)
    stk("🐑", 31.20, 32.26, SL, SY, 100)
    ev.append(flash(tl(32.56), d=0.25))
    lab(32.56, 33.56, "MACAM-MACAM *HAIWAN*!", col=WHITE, fill=BLUSH, hi=CREAM, rot=-2, size=64, sound="ding", vol=0.4)
    stk("🐾", 32.60, 33.56, SR, SY, 95)

    # ---- CTA
    lab(33.64, 35.00, "TENGOK *BEG KUNING*", col=COCOA, fill=YELLOW, hi=BLUSH, rot=2, size=66, sound="bloop", vol=0.5)
    stk("🛒", 33.68, 35.00, SL, SY, 95)

    # ---- end card (refresh v4: polaroid frame around the cat's face, inside the safe area)
    e0 = BT["end"]["t0"]
    wx0, wy0, wx1, wy1 = 104, 190, 556, 610          # photo window
    fx0, fy0, fx1, fy1 = 80, 166, 580, 724           # polaroid frame (thick bottom strip)
    hole = f"m {wx0} {wy0} l {wx0} {wy1} l {wx1} {wy1} l {wx1} {wy0}"     # counter-clockwise -> cut out
    ev.append(f"Dialogue: 7,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{CREAM}\1a&HFF&\t(0,300,\1a&H18&)\p1}}m 0 0 l {W} 0 l {W} {H} l 0 {H} {hole}{{\p0}}")
    # polka dots on the cream backdrop (outside the frame and the text area)
    dots = " ".join(ell(x, y, 9, 9) for y in range(120, 1000, 70) for x in range(52, 640, 70)
                    if not (fx0 - 20 < x < fx1 + 20 and fy0 - 20 < y < fy1 + 20) and not (740 < y < 940))
    ev.append(f"Dialogue: 7,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{BLUSH}\1a&HFF&\t(0,300,\1a&HA0&)\p1}}{dots}{{\p0}}")
    ev.append(f"Dialogue: 8,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{WHITE}\4c{COCOA}\4a&H90&\shad5\bord0\1a&HFF&\t(0,300,\1a&H00&)\p1}}"
              f"m {fx0} {fy0} l {fx1} {fy0} l {fx1} {fy1} l {fx0} {fy1} {hole}{{\\p0}}")
    # washi tape on top of the polaroid
    ev.append(f"Dialogue: 9,{ts(e0 + 0.2)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an5\pos({(fx0 + fx1) // 2},{fy0})\frz4\c{LILAC}\1a&H30&\fad(120,0)\p1}}{rrect(170, 42, 4)}{{\p0}}")
    ev.append(f"Dialogue: 9,{ts(e0 + 0.15)},{ts(TOTAL)},Pill,,0,0,0,,"
              rf"{{\an5\pos({(fx0 + fx1) // 2},{(wy1 + fy1) // 2 + 2})\fs50\c{COCOA}\fad(150,0)}}BANTAL {{\c{BLUSH}}}KUCING")
    ev.extend(pill(e0 + 0.45, TOTAL, "ADA GAJAH • MUSANG • DOMBA", col=COCOA, fill=SAGE, hi=WHITE, y=800, rot=-2,
                   layer=9, size=40))
    ev.extend(pill(e0 + 0.75, TOTAL, "TEKAN *BEG KUNING*", col=COCOA, fill=YELLOW, hi=BLUSH, y=890, rot=2,
                   layer=9, size=54))
    bstk("🐾", e0 + 0.2, TOTAL, 125, (wy1 + fy1) // 2, 58)
    bstk("💗", e0 + 0.2, TOTAL, 535, (wy1 + fy1) // 2, 56)
    bstk("👇", e0 + 0.8, TOTAL, SL, 890, 70)
    sfx += [("whoosh", e0 - 0.1, 0.4), ("sparkle", e0 + 0.15, 0.35), ("pop", e0 + 0.45, 0.45), ("ding", e0 + 0.75, 0.4)]
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
