#!/usr/bin/env python3
"""Edit for the watermelon-slice plush pillow (bantal tembikai, 45 / 60 / 90cm) TikTok video.

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
# v: list of (src_in, src_out, speed, zoom)
# a: 'same' (follow v at speed 1), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK: "Tembikai ni ada lagi besar ke? Ada."  (big slice right up to the camera)
    dict(name="hook", a="same", v=[(0.00, 3.05, 1, 1.05)]),
    # "Okay kita ada lagi besar, size yang ni 90cm."  (pause inside "yang ... ni" cut, zoom hides the jump)
    dict(name="besar", a="same", v=[(4.30, 7.22, 1, 1.0), (7.76, 9.85, 1, 1.07)]),
    # "Okay ni 60cm, ni 90cm."  ("MashaAllah" cut)  two faces side by side
    dict(name="dua", a="same", v=[(10.58, 13.48, 1, 1.0)]),
    # "Tengoklah, beza dari segi ketebalan pun sangat-sangat berbeza."  (rind sides)
    dict(name="tebal", a="same", v=[(13.58, 17.06, 1, 1.0)]),
    # "90cm macam ni, 60cm macam ni dan paling kecil size 45cm."  (all three)
    dict(name="saiz", a="same", v=[(17.06, 23.52, 1, 1.0)]),
    # "Jadi kita ada 3 size semua."  ("Okey ini 45cm" repeat cut)
    dict(name="tiga", a="same", v=[(25.05, 26.58, 1, 1.05)]),
    # "Tembikai, tembikai, tembikai."  (the long repeat of all sizes before it is cut)
    dict(name="tembikai", a="same", v=[(39.06, 42.56, 1, 1.0)]),
    # "Sangat-sangat fluffy."  J-cut over the fur close-up
    dict(name="fluffy", a=[(45.22, 46.44)], v=[(49.92, 51.14, 1, 1.0)]),
    # "Material jenis bulu-bulu fluffy, sangat-sangat gebu."  (second, cleaner take; first one cut)
    dict(name="material", a="same", v=[(52.42, 56.10, 1, 1.0)]),
    # "Recommended."  over the pillow's face close-up
    dict(name="reco", a=[(59.08, 59.70)], v=[(56.10, 56.72, 1, 1.0)]),
    # CTA (moved to the end): "Okay, korang boleh tengok dekat beg kuning tau."
    dict(name="cta", a="same", v=[(42.70, 45.15, 1, 1.0)]),
    # big slice front-on, slowed - end card
    dict(name="end", a=None, v=[(28.70, 29.70, 0.5, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "Okey": "Okay", "itu": "tu"}
# hand-checked words where Whisper drifted or misheard (re-transcribed per clip)
def _w(*ws):
    return [dict(w=w, s=a, e=b) for w, a, b in ws]


OVERRIDE = {
    0.00: _w(("Tembikai", 0.02, 0.94), ("ni", 0.94, 1.20), ("ada", 1.20, 1.36), ("lagi", 1.36, 1.58), ("besar", 1.58, 1.98),
             ("ke?", 1.98, 2.50), ("Ada!", 2.70, 3.02)),
    4.30: _w(("Okay", 4.32, 4.70), ("kita", 4.72, 4.90), ("ada", 4.90, 5.06), ("lagi", 5.06, 5.26), ("besar,", 5.26, 5.98),
             ("size", 6.40, 6.72), ("yang", 6.72, 7.18)),
    7.76: _w(("ni", 7.78, 8.62), ("90cm.", 8.70, 9.80)),
    10.58: _w(("Okay", 10.86, 11.08), ("ni", 11.08, 11.54), ("60cm,", 11.54, 12.32), ("ni", 12.58, 12.82), ("90cm.", 12.82, 13.40)),
    13.58: _w(("Tengoklah,", 13.62, 14.18), ("beza", 14.24, 14.48), ("dari", 14.48, 14.78), ("segi", 14.78, 15.42),
              ("ketebalan", 15.42, 16.00), ("pun", 16.00, 16.20), ("sangat", 16.20, 16.48), ("-sangat", 16.48, 16.76),
              ("berbeza.", 16.76, 17.04)),
    17.06: _w(("90cm", 17.08, 17.57), ("macam", 17.57, 17.79), ("ni,", 17.79, 18.01), ("60cm", 18.37, 18.89),
              ("macam", 18.89, 19.15), ("ni", 19.15, 19.35), ("dan", 19.35, 19.63), ("paling", 19.63, 19.83),
              ("kecil", 19.83, 20.60), ("size", 20.75, 21.15), ("45cm.", 21.40, 23.00)),
    25.05: _w(("Jadi", 25.08, 25.36), ("kita", 25.36, 25.54), ("ada", 25.54, 25.66), ("3", 25.66, 25.92), ("size", 25.92, 26.18),
              ("semua.", 26.18, 26.52)),
    39.06: _w(("Tembikai,", 39.10, 40.22), ("tembikai,", 40.40, 41.30), ("tembikai!", 41.62, 42.40)),
    45.22: _w(("Sangat", 45.24, 45.66), ("-sangat", 45.66, 45.98), ("fluffy!", 45.98, 46.36)),
    52.42: _w(("Material", 52.48, 53.18), ("jenis", 53.26, 53.80), ("bulu", 53.80, 54.04), ("-bulu", 54.04, 54.26),
              ("fluffy,", 54.26, 54.68), ("sangat", 55.22, 55.42), ("-sangat", 55.42, 55.72), ("gebu.", 55.72, 56.06)),
    59.08: _w(("Recommended!", 59.12, 59.64)),
    42.70: _w(("Okay,", 42.80, 43.12), ("korang", 43.16, 43.34), ("boleh", 43.34, 43.58), ("tengok", 43.58, 43.74), ("dekat", 43.74, 44.00),
              ("beg", 44.00, 44.14), ("kuning", 44.14, 44.50), ("tau.", 44.56, 44.90)),
}
DROP = []
HILITE = {"TEMBIKAI", "BESAR", "90CM", "60CM", "45CM", "KETEBALAN", "BERBEZA", "KECIL", "3", "SIZE", "FLUFFY", "BULU-BULU",
          "GEBU", "RECOMMENDED", "KUNING", "BEG", "MATERIAL"}

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
Style: Cap,Fredoka,56,&H00FFFFFF,&H000000FF,&H002E6F13,&H502E6F13,-1,0,0,0,100,100,0,0,1,5,3,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Sticker,Fredoka,68,&H006F3FE8,&H000000FF,&H00FFFFFF,&H002E6F13,-1,0,0,0,100,100,1,0,1,8,5,5,40,40,0,1
Style: Label,Fredoka,62,&H002E6F13,&H000000FF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,3,16,0,5,40,40,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,&H002E6F13,&H502E6F13,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
"""
ASS_HEAD += """
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# palette from the watermelon slice: flesh pink, deep pink, rind green, dark rind, cream rind, seed, plus beg-kuning yellow
PINK = "&H916FFF&"       # #FF6F91  flesh
DPINK = "&H6F3FE8&"      # #E83F6F  deep flesh (sticker text)
GREEN = "&H4AC23C&"      # #3CC24A  rind
DGREEN = "&H2E6F13&"     # #136F2E  dark rind (outlines / shadows)
LGREEN = "&H6AE89B&"     # #9BE86A  caption keywords
CREAM = "&HEEF7FF&"      # #FFF7EE  white rind
SEED = "&H1F1A2A&"       # #2A1A1F
YELLOW = "&H3FD2FF&"     # #FFD23F  beg kuning
WHITE = "&H00FFFFFF&"
KEY = LGREEN


def captions(words):
    """Refresh: the active word gets a thick flesh-pink 'marker' outline instead of a colour change."""
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
                    parts.append(r"{\c&HFFFFFF&\3c%s\bord11\fscx108\fscy108}%s{\r}" % (DPINK, t))
                elif t.strip("-?!") in HILITE or t in HILITE:
                    parts.append(r"{\c%s}%s{\r}" % (KEY, t))
                else:
                    parts.append(t)
            pop = r"{\fscx85\fscy85\t(0,90,\fscx100\fscy100)}" if j == 0 else ""
            ev.append(f"Dialogue: 2,{ts(ws)},{ts(we)},Cap,,0,0,0,,{pop}" + " ".join(parts))
    return ev


_FIT_FONTS = {}


def fit_size(text, size, max_w=SAFE_W - 90):   # room for the outline + pop overshoot
    """Shrink a label's font size so it stays inside the safe area."""
    plain = text.replace("*", "")
    f = _FIT_FONTS.setdefault(size, ImageFont.truetype(FONT_FILE, size))
    w = f.getlength(plain) * ASS_PER_PIL
    return size if w <= max_w else int(size * max_w / w)


def sticker(t0, t1, text, y=235, col=DPINK, hi=GREEN, rot=0, layer=5, x=CX, size=70):
    """Refresh: die-cut sticker text (thick white outline + dark-rind drop shadow), springy pop, no box."""
    size = fit_size(text, size)
    parts = text.split("*")
    text = "".join(p if i % 2 == 0 else rf"{{\c{hi}}}{p}{{\c{col}}}" for i, p in enumerate(parts))
    return (f"Dialogue: {layer},{ts(t0)},{ts(t1)},Sticker,,0,0,0,,"
            rf"{{\an5\pos({x},{y})\frz{rot}\fs{size}\c{col}\fscx0\fscy0"
            rf"\t(0,120,\fscx120\fscy120)\t(120,200,\fscx92\fscy92)\t(200,280,\fscx100\fscy100)\fad(0,150)}}{text}")


def pill(t0, t1, text, y=270, col=DGREEN, box=WHITE, hi=DPINK, rot=0, layer=5, x=CX, size=62):
    """Boxed pill (used on the end card)."""
    size = fit_size(text, size)
    parts = text.split("*")
    text = "".join(p if i % 2 == 0 else rf"{{\c{hi}}}{p}{{\c{col}}}" for i, p in enumerate(parts))
    return (f"Dialogue: {layer},{ts(t0)},{ts(t1)},Label,,0,0,0,,"
            rf"{{\an5\pos({x},{y})\frz{rot}\fs{size}\c{col}\3c{box}\fscx0\fscy0"
            rf"\t(0,140,\fscx112\fscy112)\t(140,240,\fscx100\fscy100)\fad(0,150)}}{text}")


def flash(t0, d=0.35, layer=9, col=CREAM):
    """Refresh: soft cream/pink flash instead of pure white."""
    return (f"Dialogue: {layer},{ts(t0)},{ts(t0 + d)},Shape,,0,0,0,,"
            rf"{{\an7\pos(0,0)\c{col}\1a&H40&\fad(0,{int(d * 1000) - 40})\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")


SEED_SHAPE = "m 0 -11 b 7 -3 6 9 0 11 b -6 9 -7 -3 0 -11"


def seeds(t0, x=CX, y=560, n=10, dur=0.75, layer=7, spread=230):
    """Refresh motif: watermelon seeds burst outward (kept inside the safe area)."""
    import math
    ev = []
    for i in range(n):
        a = 2 * math.pi * i / n + 0.35
        d = spread * (0.75 + 0.25 * ((i * 7) % 3))
        x1 = min(max(x + math.cos(a) * d, SAFE_L + 15), W - SAFE_R - 15)
        y1 = min(max(y + math.sin(a) * d, SAFE_T + 15), H - SAFE_B - 15)
        r0 = (i * 53) % 360
        ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t0 + dur)},Shape,,0,0,0,,"
                  rf"{{\an7\move({x},{y},{int(x1)},{int(y1)},0,{int(dur * 800)})\c{SEED}\3c{CREAM}\bord2"
                  rf"\frz{r0}\t(\frz{r0 + 160})\fad(0,260)\p1}}{SEED_SHAPE}{{\p0}}")
    return ev


def graphics():
    ev, stickers, sfx = [], [], []
    # progress bar (retention): rind-green track with a flesh-pink fill - top edge is clear of the TikTok UI
    ev.append(f"Dialogue: 7,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{GREEN}\1a&H30&\p1}}m 0 0 l {W} 0 {W} 10 0 10{{\p0}}")
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{PINK}\fscx0\t(0,{int(TOTAL * 1000)},\fscx100)\p1}}m 0 0 l {W} 0 {W} 7 0 7{{\p0}}")

    def lab(s0, s1, text, sound="pop", vol=0.5, **kw):
        ev.append(sticker(tl(s0), tl(s1), text, **kw))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def stk(em, s0, s1, x, y, size=100):
        stickers.append((em, tl(s0), tl(s1), x, y, size))

    def bstk(em, t0, t1, x, y, size=100):
        stickers.append((em, t0, t1, x, y, size))

    SL, SR, SY = 90, 552, 150

    # ---- HOOK: is there a bigger one? -> yes!
    lab(0.02, 2.50, "ADA LAGI *BESAR*?", rot=-3, size=72, sound="bloop", vol=0.5)
    stk("🍉", 0.06, 2.50, SR, SY, 105)
    ev.append(flash(tl(2.70), d=0.25, col=PINK))
    ev += seeds(tl(2.70), y=520)
    lab(2.70, 3.02, "ADA!", col=GREEN, hi=DPINK, rot=4, size=110, y=245, sound="impact", vol=0.45)

    # ---- the 90cm
    lab(4.72, 5.98, "LAGI *BESAR*!", rot=-2, size=74, sound="boing", vol=0.45)
    stk("😮", 4.76, 5.98, SR, SY, 100)
    lab(7.78, 9.80, "SIZE *90CM*", col=GREEN, hi=DPINK, rot=2, size=80, sound="pop", vol=0.5)
    stk("📏", 7.82, 9.80, SL, SY, 95)

    # ---- 60 vs 90 side by side
    lab(10.62, 13.40, "*60*CM", col=DPINK, hi=GREEN, x=185, y=240, rot=-4, size=70, sound="pop", vol=0.45)
    lab(12.58, 13.40, "*90*CM", col=DPINK, hi=GREEN, x=455, y=240, rot=4, size=78, sound="pop", vol=0.45)

    # ---- thickness
    lab(13.62, 16.00, "TENGOK *KETEBALAN*", rot=-2, size=64, sound="whoosh", vol=0.35)
    stk("👀", 13.66, 16.00, SR, SY, 95)
    lab(16.00, 17.04, "SANGAT *BEZA*!", col=GREEN, hi=DPINK, rot=2, size=76, sound="boing", vol=0.45)

    # ---- size ladder 90 / 60 / 45
    lab(17.08, 23.48, "*90*CM", col=DPINK, hi=GREEN, y=205, rot=-3, size=86, sound="pop", vol=0.5)
    lab(18.37, 23.48, "*60*CM", col=DPINK, hi=GREEN, y=300, rot=2, size=70, sound="pop", vol=0.5)
    lab(21.40, 23.48, "*45*CM", col=DPINK, hi=GREEN, y=380, rot=-2, size=56, sound="pop", vol=0.5)
    stk("🍉", 17.12, 23.48, SL, 205, 90)
    stk("🍉", 18.41, 23.48, SL, 300, 72)
    stk("🍉", 21.44, 23.48, SL, 380, 56)

    # ---- three sizes
    ev.append(flash(tl(25.66), d=0.25, col=PINK))
    ev += seeds(tl(25.66), y=520)
    lab(25.08, 26.52, "ADA *3 SIZE*!", col=GREEN, hi=DPINK, rot=-3, size=82, sound="ding", vol=0.4)
    stk("✨", 25.12, 26.52, SR, SY, 95)

    # ---- tembikai x3 (fun beat): each one pops in a different spot
    lab(39.10, 42.40, "TEMBIKAI", x=230, y=200, rot=-6, size=58, sound="chomp", vol=0.6)
    lab(40.40, 42.40, "TEMBIKAI", x=410, y=300, rot=5, size=64, sound="chomp", vol=0.6)
    lab(41.62, 42.40, "*TEMBIKAI*!", col=DPINK, hi=GREEN, y=400, rot=-2, size=80, sound="chomp", vol=0.6)
    stk("🍉", 39.14, 42.40, SR, SY, 90)
    stk("🍉", 40.44, 42.40, SL, 380, 80)
    ev += seeds(tl(41.62), y=560, n=8)

    # ---- material
    lab(45.24, 46.36, "SANGAT *FLUFFY*", rot=-2, size=74, sound="sparkle", vol=0.35)
    stk("☁️", 45.28, 46.36, SR, SY, 100)
    lab(52.50, 54.68, "BULU-BULU *FLUFFY*", rot=2, size=66, sound="pop", vol=0.45)
    stk("🧸", 52.54, 54.68, SR, SY, 95)
    lab(55.22, 56.06, "SANGAT *GEBU*!", col=GREEN, hi=DPINK, rot=-2, size=78, sound="boing", vol=0.5)
    stk("🤗", 55.26, 56.06, SR, SY, 100)
    lab(59.12, 59.64, "*RECOMMENDED*!", col=DPINK, hi=GREEN, rot=-3, size=72, sound="sparkle", vol=0.4)
    stk("👍", 59.14, 59.64, SR, SY, 100)

    # ---- CTA
    lab(43.58, 44.90, "TENGOK *BEG KUNING*", col=DGREEN, hi=YELLOW, rot=-2, size=66, sound="kaching", vol=0.4)
    stk("🛒", 43.62, 44.90, SR, SY, 95)

    # ---- end card: ribbon banner + stacked pills + falling seeds (inside the safe area)
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 6,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{DGREEN}\1a&HFF&\t(0,250,\1a&H66&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    ev.append(f"Dialogue: 8,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos({CX},400)\c{PINK}\3c{CREAM}\bord6\fscx0\t(0,200,\fscx100)\p1}}"
              r"m -255 -50 l 255 -50 l 225 0 l 255 50 l -255 50 l -225 0{\p0}")
    ev.append(f"Dialogue: 9,{ts(e0 + 0.1)},{ts(TOTAL)},Sticker,,0,0,0,,"
              rf"{{\an5\pos({CX},400)\fs58\c{WHITE}\3c{DPINK}\bord5\shad0\fad(150,0)}}BANTAL TEMBIKAI")
    ev.append(pill(e0 + 0.35, TOTAL, "45 • 60 • *90* CM", col=WHITE, box=GREEN, hi=YELLOW, y=525, rot=-2, layer=9, size=58))
    ev.append(pill(e0 + 0.6, TOTAL, "KORANG NAK *SIZE* MANA?", col=DGREEN, box=CREAM, hi=DPINK, y=635, rot=2, layer=9, size=54))
    ev.append(pill(e0 + 0.9, TOTAL, "TEKAN BEG KUNING", col=DGREEN, box=YELLOW, hi=DPINK, y=750, rot=-1, layer=9, size=62))
    for i, (sx, d) in enumerate([(90, 0.0), (210, 0.4), (470, 0.2), (560, 0.7), (330, 0.9), (150, 1.2)]):
        t0 = e0 + d
        ev.append(f"Dialogue: 8,{ts(t0)},{ts(TOTAL)},Shape,,0,0,0,,"
                  rf"{{\an7\move({sx},{SAFE_T + 10},{sx + (20 if i % 2 else -20)},{H - SAFE_B - 20},0,{int((TOTAL - t0) * 1000)})"
                  rf"\c{SEED}\3c{CREAM}\bord2\frz{i * 40}\t(\frz{i * 40 + 200})\fad(150,0)\p1}}{SEED_SHAPE}{{\p0}}")
    bstk("🍉", e0 + 0.1, TOTAL, SR, 300, 95)
    bstk("👇", e0 + 0.65, TOTAL, SL, 635, 75)
    bstk("🛒", e0 + 0.95, TOTAL, SR, 750, 85)
    sfx += [("whoosh", e0 - 0.1, 0.4), ("pop", e0 + 0.1, 0.45), ("pop", e0 + 0.35, 0.45), ("pop", e0 + 0.6, 0.4),
            ("kaching", e0 + 0.9, 0.45)]
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
