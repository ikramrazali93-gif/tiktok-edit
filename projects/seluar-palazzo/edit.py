#!/usr/bin/env python3
"""Edit for the palazzo pants (seluar palazzo) TikTok video.

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
    # HOOK (moved from 48.4s): "Ni siapa yang suka pakai palazzo, ni paling sesuai untuk awak kan."
    dict(name="hook", a="same", v=[(48.42, 50.10, 1, 1.12), (50.10, 52.02, 1, 1.0)]),
    # "Wah, palazzo. Material selesa."  (unclear "yakmat" after it is cut)
    dict(name="wah", a="same", v=[(0.50, 2.74, 1, 1.0)]),
    # "Material dia macam, apa tu, anti kedut macam tu. Dia tak nampak keras kejong, dia ironless."
    dict(name="material", a="same", v=[(3.72, 4.82, 1, 1.08), (5.08, 7.34, 1, 1.08), (7.34, 9.92, 1, 1.0)]),
    # "Ni bahagian depan dia ada zip." + "Ni ada cangkuk."  (J-cut onto the waist close-up; "dan ada cangkuk lah" cut)
    dict(name="depan", a=[(11.00, 14.42), (15.92, 16.84)],
         v=[(11.00, 13.20, 1, 1.0), (13.20, 14.42, 1, 1.1), (17.00, 17.92, 1, 1.0)]),
    # "Bahagian belakang ada getah." + "Selesa sangat."  (repeat "bahagian belakang ada getah macam ni" cut;
    #  "selesa sangat" plays over the elastic being stretched)
    dict(name="getah", a=[(18.02, 20.32), (23.46, 24.58)], v=[(18.02, 20.32, 1, 1.0), (21.90, 23.02, 1, 1.0)]),
    # "Yang ni saya ambil free size. Okay ni untuk colour brown macam tu."
    dict(name="saiz", a="same", v=[(24.86, 27.10, 1, 1.0), (27.10, 29.30, 1, 1.1)]),
    # "Dia dekat sini dia ada tulang. Jadi kalau kita pakai tu nampak kemas sangatlah."
    dict(name="tulang", a="same", v=[(31.62, 34.98, 1, 1.08)]),
    # "Material dia paling tip top. Material best." + "...high kualiti lah."  (pause cut)
    dict(name="kualiti", a="same", v=[(35.22, 37.46, 1, 1.0), (38.48, 40.70, 1, 1.0)]),
    # "Material dia lembut elok" + "jahitan pun sangatlah kemas."  ("dan ironless, elok sangat" cut - ironless said already)
    dict(name="lembut", a="same", v=[(40.86, 43.12, 1, 1.0), (46.40, 47.98, 1, 1.1)]),
    # "Pakai dengan t-shirt ke, pakai dengan knitwear ke, pakai dengan baju labuh ke. Semua boleh."
    dict(name="gaya", a="same", v=[(52.28, 53.10, 1, 1.0), (54.28, 56.70, 1, 1.08), (56.70, 59.30, 1, 1.0)]),
    # "Ada macam-macam warna, boleh tengok dekat beg kuning tau."  (first "dekat beg kuning" cut)
    dict(name="cta", a="same", v=[(61.66, 64.28, 1, 1.08)]),
    # holding the pants up, slowed
    dict(name="end", a=None, v=[(0.30, 1.10, 0.4, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "Okey": "Okay", "itu": "tu", "cakoklah": "cangkuk lah", "cakok": "cangkuk",
       "labur": "labuh", "kedud": "kedut", "tahu": "tau"}
# hand-checked words where Whisper drifted or misheard (re-transcribed per clip)
def _w(*ws):
    return [dict(w=w, s=a, e=b) for w, a, b in ws]


OVERRIDE = {
    48.42: _w(("Siapa", 48.44, 48.78), ("yang", 48.78, 48.86), ("suka", 48.86, 49.08), ("pakai", 49.08, 49.38),
              ("palazzo,", 49.38, 50.04)),
    50.10: _w(("ni", 50.24, 50.40), ("paling", 50.40, 50.66), ("sesuai", 50.66, 50.98), ("untuk", 50.98, 51.18),
              ("awak", 51.18, 51.56), ("kan!", 51.56, 51.98)),
    0.50: _w(("Wah,", 0.55, 0.80), ("palazzo!", 0.80, 1.48), ("Material", 1.72, 2.02), ("selesa.", 2.02, 2.70)),
    3.72: _w(("Material", 3.78, 4.36), ("dia", 4.36, 4.70)),
    5.08: _w(("macam", 5.10, 5.40), ("anti", 6.28, 6.40), ("kedut", 6.40, 6.66), ("macam", 6.66, 6.90),
             ("tu.", 6.90, 7.18)),
    7.34: _w(("Dia", 7.36, 7.54), ("tak", 7.54, 7.68), ("nampak", 7.68, 7.96), ("keras", 7.96, 8.30),
             ("kejong,", 8.30, 9.06), ("dia", 9.18, 9.42), ("ironless.", 9.42, 9.90)),
    11.00: _w(("Ni", 11.04, 11.54), ("bahagian", 11.54, 11.88), ("depan", 11.88, 12.22), ("dia", 12.22, 12.76),
              ("ada", 12.76, 13.64), ("zip.", 13.64, 14.40)),
    15.92: _w(("Ni", 15.98, 16.40), ("ada", 16.40, 16.58), ("cangkuk.", 16.58, 16.84)),
    18.02: _w(("Bahagian", 18.06, 18.86), ("belakang", 18.86, 19.34), ("ada", 19.34, 19.54), ("getah.", 19.54, 20.28)),
    23.46: _w(("Selesa", 23.48, 23.80), ("sangat.", 23.80, 24.56)),
    24.86: _w(("Yang", 24.86, 25.02), ("ni", 25.02, 25.12), ("saya", 25.12, 25.30), ("ambil", 25.30, 25.52),
              ("free", 25.52, 25.92), ("size.", 25.92, 26.68)),
    27.10: _w(("Ni", 27.18, 27.42), ("untuk", 27.42, 27.74), ("colour", 27.74, 28.38), ("brown", 28.38, 28.78),
              ("macam", 28.78, 29.02), ("tu.", 29.02, 29.28)),
    31.62: _w(("Dekat", 31.66, 31.86), ("sini", 31.86, 32.04), ("dia", 32.04, 32.16), ("ada", 32.16, 32.32),
              ("tulang.", 32.32, 32.66), ("Jadi", 32.76, 32.86), ("kalau", 32.86, 33.04), ("kita", 33.04, 33.26),
              ("pakai", 33.26, 33.40), ("tu", 33.40, 33.56), ("nampak", 33.56, 33.84), ("kemas", 33.84, 34.24),
              ("sangatlah.", 34.24, 34.96)),
    35.22: _w(("Material", 35.24, 35.32), ("dia", 35.32, 35.48), ("paling", 35.48, 35.76), ("tip", 35.76, 36.04),
              ("top!", 36.04, 36.18), ("Material", 36.28, 36.60), ("best.", 36.60, 37.16)),
    38.48: _w(("Kualiti,", 38.52, 39.12), ("high", 39.14, 39.56), ("kualiti", 39.60, 40.30), ("lah!", 40.30, 40.62)),
    40.86: _w(("Material", 41.10, 41.66), ("dia", 41.66, 41.96), ("lembut,", 41.96, 42.66), ("elok.", 42.66, 43.08)),
    46.40: _w(("Jahitan", 46.42, 46.74), ("pun", 46.74, 46.94), ("sangatlah", 46.94, 47.50), ("kemas.", 47.50, 47.94)),
    52.28: _w(("Pakai", 52.30, 52.48), ("dengan", 52.48, 52.72), ("t-shirt", 52.72, 53.00), ("ke,", 53.00, 53.08)),
    54.28: _w(("pakai", 54.32, 54.62), ("dengan", 54.62, 55.30), ("knitwear", 55.36, 56.20), ("ke,", 56.20, 56.66)),
    56.70: _w(("pakai", 56.84, 56.94), ("dengan", 56.94, 57.14), ("baju", 57.14, 57.60), ("labuh", 57.60, 58.06),
              ("ke.", 58.06, 58.46), ("Semua", 58.50, 58.76), ("boleh!", 58.76, 59.26)),
    61.66: _w(("Ada", 61.70, 61.86), ("macam-macam", 61.86, 62.20), ("warna,", 62.20, 62.52), ("boleh", 62.52, 62.70),
              ("tengok", 62.70, 62.90), ("dekat", 62.90, 63.10), ("beg", 63.10, 63.26), ("kuning", 63.26, 63.56),
              ("tau.", 63.56, 63.98)),
}
DROP = []
HILITE = {"PALAZZO", "SELESA", "ANTI", "KEDUT", "IRONLESS", "ZIP", "CANGKUK", "GETAH", "FREE", "SIZE", "BROWN",
          "TULANG", "KEMAS", "TIP", "TOP", "BEST", "KUALITI", "LEMBUT", "JAHITAN", "T-SHIRT", "KNITWEAR", "LABUH",
          "SEMUA", "WARNA", "KUNING", "KERAS", "KEJONG"}

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
Style: Cap,Fredoka,58,&H00FFFFFF,&H000000FF,&H0014233B,&H6414233B,-1,0,0,0,100,100,0,0,1,5,3,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Label,Fredoka,62,&H0014233B,&H000000FF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,3,16,0,5,40,40,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,&H0014233B,&H6414233B,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# palette from the palazzo: espresso text, caramel/mustard (the pants), sunflower yellow, denim blue (her jacket),
# sky blue keywords (complements the mustard), cream
ESP = "&H0014233B&"      # #3B2314  (ASS colours are BGR)
CARA = "&H002A78B5&"     # #B5782A
SUN = "&H003CC9FF&"      # #FFC93C
DENIM = "&H009E5D2F&"    # #2F5D9E
SKY = "&H00FFD68F&"      # #8FD6FF
CREAM = "&H00DCF3FF&"    # #FFF3DC
WHITE = "&H00FFFFFF&"
ACC = SUN
KEY = SKY

def captions(words):
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
                    parts.append(r"{\c%s\fscx112\fscy112}%s{\r}" % (ACC, t))
                elif t.strip("-") in HILITE or t in HILITE:
                    parts.append(r"{\c%s}%s{\r}" % (KEY, t))
                else:
                    parts.append(t)
            pop = r"{\fscx85\fscy85\t(0,90,\fscx100\fscy100)}" if j == 0 else ""
            ev.append(f"Dialogue: 2,{ts(ws)},{ts(we)},Cap,,0,0,0,,{pop}" + " ".join(parts))
    return ev


_FIT_FONTS = {}


def fit_size(text, size, max_w=SAFE_W - 90):   # room for the box border + pop overshoot
    """Shrink a label's font size so its box stays inside the safe area."""
    plain = text.replace("*", "")
    f = _FIT_FONTS.setdefault(size, ImageFont.truetype(FONT_FILE, size))
    w = f.getlength(plain) * ASS_PER_PIL
    return size if w <= max_w else int(size * max_w / w)


def label(t0, t1, text, y=760, col=ESP, box=WHITE, hi=CARA, rot=-3, layer=5, x=CX, size=62):
    """Pop-in boxed label with a slight tilt. *word* is drawn in the highlight colour."""
    size = fit_size(text, size)
    parts = text.split("*")
    text = "".join(p if i % 2 == 0 else rf"{{\c{hi}}}{p}{{\c{col}}}" for i, p in enumerate(parts))
    return (f"Dialogue: {layer},{ts(t0)},{ts(t1)},Label,,0,0,0,,"
            rf"{{\an5\pos({x},{y})\frz{rot}\fs{size}\c{col}\3c{box}\fscx0\fscy0"
            rf"\t(0,140,\fscx112\fscy112)\t(140,240,\fscx100\fscy100)\fad(0,150)}}{text}")


def flash(t0, d=0.35, layer=9, col=WHITE):
    return (f"Dialogue: {layer},{ts(t0)},{ts(t0 + d)},Shape,,0,0,0,,"
            rf"{{\an7\pos(0,0)\c{col}\1a&H30&\fad(0,{int(d * 1000) - 40})\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")


def chip(t0, t1, x, y, col, name):
    return [
        f"Dialogue: 6,{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
        rf"{{\an5\pos({x},{y})\c{col}\3c&HFFFFFF&\bord5\fscx0\fscy0\t(0,150,\fscx100\fscy100)\fad(0,120)\p1}}"
        r"m -45 0 b -45 -60 45 -60 45 0 b 45 60 -45 60 -45 0{\p0}",
        f"Dialogue: 6,{ts(t0)},{ts(t1)},Small,,0,0,0,,"
        rf"{{\an5\pos({x},{y + 80})\fscx0\fscy0\t(0,150,\fscx100\fscy100)\fad(0,120)}}{name}",
    ]


def graphics():
    ev, stickers, sfx = [], [], []
    # progress bar (retention) - top edge is clear of the TikTok UI
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{SUN}\fscx0\t(0,{int(TOTAL * 1000)},\fscx100)\p1}}m 0 0 l {W} 0 {W} 8 0 8{{\p0}}")

    def bt(name, off=0.0):
        return BT[name]["t0"] + off

    def end_of(name):
        return BT[name]["t0"] + BT[name]["dur"]

    def lab(s0, s1, text, sound="pop", vol=0.5, **kw):
        ev.append(label(tl(s0), tl(s1), text, **kw))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def stk(em, s0, s1, x, y, size=100):
        stickers.append((em, tl(s0), tl(s1), x, y, size))

    def bstk(em, t0, t1, x, y, size=100):
        stickers.append((em, t0, t1, x, y, size))

    SL, SR, SY = 85, 555, 665

    def speed_tag(name, txt=">> x3"):
        b = BT[name]
        ev.append(f"Dialogue: 6,{ts(b['t0'])},{ts(b['t0'] + b['dur'])},Small,,0,0,0,,"
                  rf"{{\an7\pos({SAFE_L},{SAFE_T + 20})\c{SUN}}}{txt}")
        sfx.append(("swish", b["t0"] - 0.05, 0.45))

    # ---- HOOK: palazzo lovers -> this one is for you
    lab(48.44, 50.04, "SUKA *PALAZZO*?", col=WHITE, box=DENIM, hi=SUN, rot=-3, size=74, sound="bloop", vol=0.5)
    stk("👖", 48.48, 50.04, SR, SY, 110)
    ev.append(flash(tl(50.22), d=0.25))
    lab(50.24, 52.00, "NI PALING *SESUAI*!", col=ESP, box=SUN, hi=DENIM, rot=2, size=72, sound="ding", vol=0.4)
    stk("👉", 50.28, 52.00, SR, SY, 110)

    # ---- intro
    lab(0.55, 1.48, "WAH, *PALAZZO*!", col=ESP, box=CREAM, hi=CARA, rot=-3, size=72, sound="pop", vol=0.5)
    stk("🤩", 0.58, 1.48, SR, SY, 100)
    lab(1.72, 2.72, "MATERIAL *SELESA*", col=WHITE, box=CARA, hi=SUN, rot=2, sound="whoosh", vol=0.4)
    stk("☁️", 1.76, 2.72, SR, SY, 100)

    # ---- fabric
    lab(6.28, 7.18, "*ANTI KEDUT*", col=ESP, box=SUN, hi=DENIM, rot=-2, size=74, sound="sparkle", vol=0.3)
    stk("✨", 6.30, 7.18, SR, SY, 100)
    lab(7.36, 9.06, "TAK *KERAS KEJONG*", rot=2, box=CREAM)
    stk("🙅", 7.40, 9.06, SR, SY, 100)
    lab(9.18, 9.92, "*IRONLESS*!", col=WHITE, box=DENIM, hi=SUN, rot=-3, size=74, sound="pop", vol=0.5)
    stk("🙌", 9.20, 9.92, SR, SY, 100)

    # ---- front zip + hook, back elastic
    lab(11.54, 14.40, "DEPAN ADA *ZIP*", rot=-2, box=CREAM, sound="zip", vol=0.45)
    stk("🤐", 11.58, 14.40, SR, SY, 100)
    lab(15.98, 16.84, "+ *CANGKUK*", col=WHITE, box=CARA, hi=SUN, rot=2, size=70, sound="click", vol=0.5)
    stk("🪝", 16.00, 16.84, SR, SY, 100)
    lab(18.06, 20.30, "BELAKANG *GETAH*", col=ESP, box=SUN, hi=DENIM, rot=-2, sound="swish", vol=0.4)
    stk("🔙", 18.10, 20.30, SR, SY, 90)
    lab(23.48, 24.56, "*SELESA* SANGAT!", col=WHITE, box=DENIM, hi=SUN, rot=2, sound="sparkle", vol=0.3)
    stk("😌", 23.50, 24.56, SR, SY, 100)

    # ---- size + colour
    lab(25.12, 26.92, "*FREE SIZE*", col=ESP, box=SUN, hi=DENIM, rot=-3, size=76, sound="pop", vol=0.5)
    stk("📏", 25.16, 26.92, SR, SY, 100)
    lab(27.42, 29.28, "COLOUR *BROWN*", col=WHITE, box=CARA, hi=SUN, rot=2, sound="whoosh", vol=0.35)
    stk("🤎", 27.46, 29.28, SR, SY, 100)

    # ---- crease line -> neat
    lab(32.04, 32.70, "ADA *TULANG*", rot=-2, box=CREAM)
    stk("👇", 32.06, 32.70, SR, SY, 90)
    lab(32.76, 34.96, "NAMPAK *KEMAS*!", col=ESP, box=SUN, hi=DENIM, rot=2, sound="sparkle", vol=0.3)
    stk("✨", 32.80, 34.96, SR, SY, 100)

    # ---- quality
    lab(35.48, 36.20, "*TIP TOP*!", col=WHITE, box=DENIM, hi=SUN, rot=-3, size=76, sound="pop", vol=0.5)
    stk("👍", 35.50, 36.20, SR, SY, 100)
    lab(36.28, 37.44, "MATERIAL *BEST*", rot=2, box=CREAM, sound="pop", vol=0.45)
    stk("💯", 36.30, 37.44, SR, SY, 100)
    ev.append(flash(tl(39.12), d=0.25))
    lab(38.52, 40.66, "*HIGH* KUALITI", col=ESP, box=SUN, hi=DENIM, rot=-2, size=74, sound="ding", vol=0.4)
    stk("🏆", 38.56, 40.66, SR, SY, 100)

    # ---- soft + neat stitching
    lab(41.10, 43.08, "MATERIAL *LEMBUT*", col=WHITE, box=CARA, hi=SUN, rot=2, sound="whoosh", vol=0.35)
    stk("☁️", 41.14, 43.08, SR, SY, 100)
    lab(46.42, 47.96, "JAHITAN *KEMAS*", rot=-2, box=CREAM, sound="pop", vol=0.45)
    stk("🧵", 46.46, 47.96, SR, SY, 100)

    # ---- styling
    lab(52.30, 53.10, "+ *T-SHIRT*", col=ESP, box=CREAM, hi=DENIM, rot=-3, sound="pop", vol=0.45)
    stk("👕", 52.32, 53.10, SR, SY, 100)
    lab(54.32, 56.66, "+ *KNITWEAR*", col=WHITE, box=DENIM, hi=SUN, rot=2, sound="pop", vol=0.45)
    stk("🧶", 54.36, 56.66, SR, SY, 100)
    lab(56.84, 58.46, "+ *BAJU LABUH*", col=ESP, box=SUN, hi=DENIM, rot=-2, sound="pop", vol=0.45)
    stk("👗", 56.88, 58.46, SR, SY, 100)
    ev.append(flash(tl(58.48), d=0.25))
    lab(58.50, 59.28, "*SEMUA BOLEH*!", col=WHITE, box=CARA, hi=SUN, rot=2, size=76, sound="bloop", vol=0.5)
    stk("🙌", 58.52, 59.28, SR, SY, 110)

    # ---- CTA
    lab(61.70, 62.52, "*MACAM-MACAM* WARNA", rot=-2, box=CREAM, hi=DENIM, sound="sparkle", vol=0.3)
    stk("🎨", 61.74, 62.52, SR, SY, 100)
    lab(62.54, 64.26, "TEKAN *BEG KUNING*", col=ESP, box=SUN, hi=DENIM, rot=2, sound="kaching", vol=0.4)
    stk("🛒", 62.58, 64.26, SR, SY, 100)

    # ---- end card (inside the safe area)
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 8,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{ESP}\1a&HFF&\t(0,250,\1a&H60&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    ev.append(label(e0 + 0.05, TOTAL, "*SELUAR* PALAZZO", col=WHITE, box=CARA, hi=SUN, y=430, rot=-3,
                    layer=9, size=64))
    ev.append(label(e0 + 0.3, TOTAL, "ANTI KEDUT • IRONLESS • FREE SIZE", col=ESP, box=CREAM, hi=DENIM, y=540, rot=2,
                    layer=9, size=40))
    ev.append(label(e0 + 0.6, TOTAL, "KORANG NAK *WARNA* APA?", col=WHITE, box=DENIM, hi=SUN, y=655, rot=-2,
                    layer=9, size=50))
    ev.append(label(e0 + 0.9, TOTAL, "TEKAN BEG KUNING", col=ESP, box=SUN, y=775, rot=2, layer=9, size=58))
    bstk("👖", e0 + 0.1, TOTAL, SR, 350, 100)
    bstk("👇", e0 + 0.65, TOTAL, SL, 600, 80)
    bstk("🛒", e0 + 0.95, TOTAL, SR, 700, 90)
    sfx += [("whoosh", e0 - 0.1, 0.4), ("pop", e0 + 0.05, 0.45), ("pop", e0 + 0.3, 0.45), ("pop", e0 + 0.6, 0.4),
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
