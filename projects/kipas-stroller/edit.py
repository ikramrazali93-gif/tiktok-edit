#!/usr/bin/env python3
"""Edit for the octopus stroller fan (kipas stroller) TikTok video.

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
    # HOOK (J-cut over the fan close-up + coiled octopus legs):
    # "Mummy mana yang tengah mencari kipas stroller yang high quality? Inilah jawapannya!"
    dict(name="hook", a=[(4.36, 10.00)], v=[(41.00, 43.84, 1, 1.1), (129.00, 131.80, 1, 1.0)]),
    # "Ni kipas desain terbaru."  (brand name after it is cut - unsure of spelling)
    dict(name="desain", a="same", v=[(11.72, 13.44, 1, 1.08)]),
    # "Bateri dia sangat tahan lama. Saya dah guna 3 hari, bateri dia tak habis-habis,"
    # + "tak pernah charge lagi, sebab dia sampai tu dah ada 70% bateri." + "Tu paling puas hati sekali!" (from 97.6)
    dict(name="bateri", a=[(18.22, 22.80), (23.04, 26.70), (97.56, 98.84)],
         v=[(18.22, 20.56, 1, 1.0), (20.56, 22.80, 1, 1.1), (23.04, 26.70, 1, 1.0), (97.56, 98.84, 1, 1.08)]),
    # "Ni lampu. Ada lampu, nak guna malam-malam tengah gelap pun no problem."  (J-cut onto the lit ring at 76s)
    dict(name="lampu", a=[(54.56, 59.20)], v=[(76.00, 78.30, 1, 1.0), (78.30, 80.64, 1, 1.15)]),
    # "Dia ada sampai lima speed." + "Dia slow je bunyi dia. Tu yang best, tak bising." + "Ni paling lajulah, speed ke lima!"
    dict(name="speed", a=[(65.86, 67.50), (72.12, 74.86), (81.50, 84.14)],
         v=[(65.86, 67.50, 1, 1.0), (72.12, 74.86, 1, 1.08), (81.50, 84.14, 1, 1.0)]),
    # "Dia boleh adjust, dia punya kepala dia untuk nak ke tepi sikit ke, untuk ke sini sikit ke." + "Boleh bagi pusing!"
    dict(name="adjust", a=[(84.72, 91.24), (92.32, 93.14)],
         v=[(84.72, 88.00, 1, 1.0), (88.00, 91.24, 1, 1.1), (92.32, 93.14, 1, 1.0)]),
    # "Ni dia punya kaki dia. Boleh gerak-gerak lah. Kita boleh balut dekat bahagian stroller.
    #  Kalau baby kita, anak kita tendang ke, dia tak jatuh, sebab dia kan melekat elok lah."
    dict(name="kaki", a=[(115.40, 127.06)],
         v=[(115.40, 119.30, 1, 1.0), (119.30, 122.10, 1, 1.1), (122.10, 127.06, 1, 1.0)]),
    # "Untuk octopus ni paling recommended untuk kipas stroller!"
    dict(name="rec", a=[(131.58, 136.08)], v=[(131.58, 133.90, 1, 1.08), (133.90, 136.08, 1, 1.0)]),
    # "Okay, tengok kat beg kuning."
    dict(name="cta", a="same", v=[(136.88, 138.94, 1, 1.0)]),
    # fan front-on, slowed
    dict(name="end", a=None, v=[(44.00, 45.20, 0.5, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "Okey": "Okay", "itu": "tu", "Itu": "Tu", "roller": "stroller",
       "Mami": "Mummy"}
# hand-checked words where Whisper drifted or misheard (re-transcribed per clip)
def _w(*ws):
    return [dict(w=w, s=a, e=b) for w, a, b in ws]


OVERRIDE = {
    4.36: _w(("Mummy", 4.40, 4.98), ("mana", 4.98, 5.54), ("yang", 5.54, 5.68), ("tengah", 5.68, 5.90),
             ("mencari", 5.90, 6.18), ("kipas", 6.18, 6.64), ("stroller", 6.64, 6.94), ("yang", 6.94, 7.44),
             ("high", 7.44, 7.66), ("quality?", 7.66, 8.20), ("Inilah", 8.74, 9.38), ("jawapannya!", 9.38, 9.90)),
    11.72: _w(("Ni", 11.80, 12.00), ("kipas", 12.00, 12.52), ("desain", 12.52, 12.84), ("terbaru!", 12.84, 13.42)),
    18.22: _w(("Bateri", 18.26, 18.58), ("dia", 18.58, 18.88), ("sangat", 18.88, 19.28), ("tahan", 19.28, 19.54),
              ("lama.", 19.54, 19.80), ("Saya", 19.90, 20.10), ("dah", 20.10, 20.28), ("guna", 20.28, 20.58),
              ("3", 20.58, 20.84), ("hari,", 20.84, 21.22), ("bateri", 21.22, 21.64), ("dia", 21.64, 21.80),
              ("tak", 21.80, 21.90), ("habis-habis!", 21.90, 22.78)),
    23.04: _w(("Tak", 23.08, 23.18), ("pernah", 23.18, 23.38), ("charge", 23.38, 23.60), ("lagi,", 23.60, 23.86),
              ("sebab", 23.86, 24.06), ("dia", 24.06, 24.20), ("sampai", 24.20, 24.48), ("tu", 24.48, 24.72),
              ("dah", 24.72, 25.02), ("ada", 25.02, 25.24), ("70%", 25.24, 25.86), ("bateri.", 25.86, 26.62)),
    97.56: _w(("Tu", 97.62, 97.74), ("paling", 97.74, 98.06), ("puas", 98.06, 98.34), ("hati", 98.34, 98.58),
              ("sekali!", 98.58, 98.80)),
    54.56: _w(("Ni", 54.64, 54.84), ("lampu.", 54.84, 55.50), ("Ada", 55.66, 55.92), ("lampu,", 55.92, 56.40),
              ("nak", 56.40, 56.54), ("guna", 56.54, 56.82), ("malam-malam", 56.82, 57.64), ("tengah", 57.64, 58.18),
              ("gelap", 58.18, 58.42), ("pun", 58.42, 58.60), ("no", 58.60, 58.80), ("problem!", 58.80, 59.10)),
    65.86: _w(("Dia", 66.00, 66.18), ("ada", 66.18, 66.50), ("sampai", 66.50, 66.82), ("lima", 66.82, 67.24),
              ("speed.", 67.24, 67.48)),
    72.12: _w(("Dia", 72.22, 72.50), ("slow", 72.55, 73.08), ("je", 73.08, 73.24), ("bunyi", 73.24, 73.52),
              ("dia.", 73.52, 73.68), ("Tu", 73.90, 73.98), ("yang", 73.98, 74.12), ("best,", 74.12, 74.36),
              ("tak", 74.36, 74.56), ("bising!", 74.56, 74.84)),
    81.50: _w(("Ni", 81.56, 81.76), ("paling", 81.76, 82.82), ("lajulah,", 82.82, 83.30), ("speed", 83.30, 83.50),
              ("ke", 83.50, 83.70), ("lima!", 83.70, 84.12)),
    84.72: _w(("Dia", 84.76, 84.90), ("boleh", 84.90, 85.06), ("adjust,", 85.06, 86.00), ("dia", 86.00, 86.24),
              ("punya", 86.24, 86.94), ("kepala", 86.94, 87.38), ("dia", 87.38, 87.68), ("untuk", 87.68, 88.02),
              ("nak", 88.25, 88.50), ("ke", 88.74, 88.90), ("tepi", 88.90, 89.20), ("sikit", 89.20, 89.48),
              ("ke,", 89.48, 89.92), ("untuk", 89.92, 90.26), ("ke", 90.26, 90.46), ("sini", 90.46, 90.66),
              ("sikit", 90.66, 90.92), ("ke.", 90.92, 91.22)),
    92.32: _w(("Boleh", 92.34, 92.44), ("bagi", 92.44, 92.72), ("pusing!", 92.72, 93.02)),
    115.40: _w(("Ni", 115.44, 115.88), ("dia", 115.88, 116.56), ("punya", 116.56, 116.78), ("kaki", 116.78, 117.12),
               ("dia.", 117.12, 117.26), ("Boleh", 117.26, 117.54), ("gerak-gerak", 117.54, 118.10),
               ("lah.", 118.10, 118.36), ("Kita", 118.36, 118.64), ("boleh", 118.64, 119.32), ("balut", 119.32, 120.38),
               ("dekat", 120.38, 120.86), ("bahagian", 120.86, 121.32), ("stroller.", 121.32, 122.02),
               ("Kalau", 122.32, 122.52), ("baby", 122.52, 122.96), ("kita,", 122.96, 123.26), ("anak", 123.26, 123.52),
               ("kita", 123.52, 123.86), ("tendang", 123.86, 124.40), ("ke,", 124.40, 124.56), ("dia", 124.56, 124.70),
               ("tak", 124.70, 124.86), ("jatuh,", 124.86, 125.22), ("sebab", 125.22, 125.42), ("dia", 125.42, 125.60),
               ("kan", 125.60, 126.14), ("melekat", 126.14, 126.52), ("elok", 126.52, 126.80), ("lah!", 126.80, 127.04)),
    131.58: _w(("Untuk", 131.80, 132.22), ("octopus", 132.22, 132.64), ("ni", 132.64, 132.88), ("paling", 132.88, 133.12),
               ("recommended", 133.12, 133.64), ("untuk", 134.05, 134.65), ("kipas", 134.98, 135.48),
               ("stroller!", 135.48, 136.06)),
    136.88: _w(("Okay,", 137.10, 137.26), ("tengok", 137.36, 137.54), ("kat", 137.54, 137.66), ("beg", 137.66, 137.92),
               ("kuning!", 137.92, 138.72)),
}
DROP = []
HILITE = {"KIPAS", "STROLLER", "HIGH", "QUALITY?", "QUALITY", "DESAIN", "TERBARU", "BATERI", "TAHAN", "LAMA",
          "3", "HARI", "HABIS-HABIS", "CHARGE", "70%", "PUAS", "HATI", "LAMPU", "MALAM-MALAM", "GELAP", "NO", "PROBLEM",
          "LIMA", "SPEED", "SLOW", "BEST", "BISING", "LAJULAH", "ADJUST", "KEPALA", "PUSING", "KAKI", "GERAK-GERAK",
          "BALUT", "TENDANG", "JATUH", "MELEKAT", "OCTOPUS", "RECOMMENDED", "BEG", "KUNING"}


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
Style: Cap,Fredoka,58,&H00FFFFFF,&H000000FF,&H005C2A1F,&H6414233B,-1,0,0,0,100,100,0,0,1,5,3,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Label,Fredoka,62,&H005C2A1F,&H000000FF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,3,16,0,5,40,40,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,&H005C2A1F,&H6414233B,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# palette from the fan: deep navy text, butter yellow (the fan), aqua breeze, mint (active word),
# warm orange (the lit ring), cream
NAVY = "&H005C2A1F&"     # #1F2A5C  (ASS colours are BGR)
BUTTER = "&H0066E0FF&"   # #FFE066
AQUA = "&H00B6C42E&"     # #2EC4B6
MINT = "&H00DCF25C&"     # #5CF2DC
ORANGE = "&H00428CFF&"   # #FF8C42
CREAM = "&H00DAF6FF&"    # #FFF6DA
WHITE = "&H00FFFFFF&"
ACC = MINT
KEY = BUTTER

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


def label(t0, t1, text, y=330, col=NAVY, box=WHITE, hi=AQUA, rot=-3, layer=5, x=CX, size=62):
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
              rf"{{\an7\pos(0,0)\c{BUTTER}\fscx0\t(0,{int(TOTAL * 1000)},\fscx100)\p1}}m 0 0 l {W} 0 {W} 8 0 8{{\p0}}")

    def lab(s0, s1, text, sound="pop", vol=0.5, **kw):
        ev.append(label(tl(s0), tl(s1), text, **kw))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def stk(em, s0, s1, x, y, size=100):
        stickers.append((em, tl(s0), tl(s1), x, y, size))

    def bstk(em, t0, t1, x, y, size=100):
        stickers.append((em, t0, t1, x, y, size))

    # labels sit high (over her hijab), clear of the fan in the middle of the frame
    LY = 330
    SL, SR, SY = 85, 555, 455

    # ---- HOOK: mummy looking for a good stroller fan -> this is the answer
    lab(4.40, 6.94, "MUMMY CARI *KIPAS STROLLER*?", col=WHITE, box=NAVY, hi=BUTTER, rot=-3, size=66, y=LY,
        sound="bloop", vol=0.5)
    stk("🤔", 4.44, 6.94, SL, SY, 100)
    lab(6.94, 8.20, "*HIGH QUALITY*?", col=NAVY, box=BUTTER, hi=ORANGE, rot=2, size=74, y=LY, sound="pop", vol=0.5)
    stk("⭐", 6.98, 8.20, SR, SY, 100)
    ev.append(flash(tl(8.72), d=0.25))
    lab(8.74, 9.96, "INILAH *JAWAPANNYA*!", col=NAVY, box=MINT, hi=WHITE, rot=-2, size=70, y=LY,
        sound="ding", vol=0.4)
    stk("🐙", 8.78, 9.98, SR, SY, 115)

    lab(11.80, 13.42, "*DESAIN* TERBARU", col=NAVY, box=CREAM, hi=AQUA, rot=2, y=LY, sound="sparkle", vol=0.3)
    stk("✨", 11.84, 13.42, SR, SY, 100)

    # ---- battery
    lab(18.26, 19.80, "BATERI *TAHAN LAMA*", col=WHITE, box=AQUA, hi=BUTTER, rot=-2, y=LY, sound="pop", vol=0.5)
    stk("🔋", 18.30, 19.80, SR, SY, 100)
    lab(19.90, 22.78, "GUNA *3 HARI* TAK HABIS!", col=NAVY, box=BUTTER, hi=ORANGE, rot=2, y=LY, sound="whoosh", vol=0.35)
    stk("🙌", 19.94, 22.78, SL, SY, 100)
    lab(23.08, 24.06, "TAK PERNAH *CHARGE*", col=NAVY, box=CREAM, hi=AQUA, rot=-3, y=LY, sound="pop", vol=0.45)
    stk("🔌", 23.12, 24.06, SR, SY, 100)
    lab(24.20, 26.62, "MASIH ADA *70%*", col=WHITE, box=NAVY, hi=MINT, rot=2, size=70, y=LY, sound="ding", vol=0.35)
    stk("🔋", 24.24, 26.62, SR, SY, 100)
    ev.append(flash(tl(97.60), d=0.25))
    lab(97.62, 98.80, "*PUAS HATI*!", col=NAVY, box=MINT, hi=WHITE, rot=-3, size=76, y=LY, sound="bloop", vol=0.5)
    stk("😍", 97.66, 98.80, SR, SY, 110)

    # ---- light
    lab(54.64, 55.50, "ADA *LAMPU*", col=NAVY, box=BUTTER, hi=ORANGE, rot=-2, size=72, y=LY, sound="click", vol=0.5)
    stk("💡", 54.68, 56.40, SR, SY, 100)
    lab(55.66, 56.40, "*LAMPU*!", col=WHITE, box=ORANGE, hi=NAVY, rot=2, size=72, y=LY, sound=None)
    lab(56.82, 59.10, "MALAM GELAP? *NO PROBLEM*!", col=WHITE, box=NAVY, hi=BUTTER, rot=-2, y=LY,
        sound="sparkle", vol=0.3)
    stk("🌙", 56.86, 59.10, SR, SY, 100)

    # ---- 5 speeds, quiet
    lab(66.00, 67.48, "*5 SPEED*", col=NAVY, box=MINT, hi=WHITE, rot=-3, size=78, y=LY, sound="whoosh", vol=0.45)
    stk("🌀", 66.04, 67.48, SR, SY, 100)
    lab(72.22, 73.68, "SLOW = *SENYAP*", col=NAVY, box=CREAM, hi=AQUA, rot=2, y=LY, sound="pop", vol=0.45)
    stk("🤫", 72.26, 74.84, SR, SY, 100)
    lab(73.90, 74.84, "*TAK BISING*!", col=WHITE, box=AQUA, hi=BUTTER, rot=-2, size=74, y=LY, sound="pop", vol=0.45)
    ev.append(flash(tl(81.54), d=0.25))
    lab(81.56, 84.12, "SPEED 5 *PALING LAJU*!", col=NAVY, box=BUTTER, hi=ORANGE, rot=2, y=LY, sound="whoosh", vol=0.5)
    stk("💨", 81.60, 84.12, SL, SY, 110)

    # ---- adjustable head
    lab(84.76, 86.00, "BOLEH *ADJUST*", col=WHITE, box=NAVY, hi=MINT, rot=-2, size=72, y=LY, sound="swish", vol=0.4)
    stk("🔄", 84.80, 86.00, SR, SY, 100)
    lab(86.94, 88.50, "*KEPALA* KIPAS", col=NAVY, box=CREAM, hi=AQUA, rot=2, y=LY, sound="pop", vol=0.4)
    lab(88.74, 91.22, "KE TEPI • *KE SINI*", col=NAVY, box=MINT, hi=WHITE, rot=-2, y=LY, sound="swish", vol=0.4)
    stk("↔️", 88.78, 91.22, SR, SY, 100)
    lab(92.34, 93.02, "*BOLEH PUSING*!", col=NAVY, box=BUTTER, hi=ORANGE, rot=3, size=72, y=LY, sound="pop", vol=0.5)
    stk("🔄", 92.38, 93.02, SR, SY, 100)

    # ---- octopus legs
    lab(116.78, 118.36, "KAKI *GERAK-GERAK*", col=WHITE, box=AQUA, hi=BUTTER, rot=-2, y=LY, sound="bloop", vol=0.45)
    stk("🐙", 116.82, 118.36, SR, SY, 110)
    lab(118.64, 122.02, "BALUT KAT *STROLLER*", col=NAVY, box=BUTTER, hi=ORANGE, rot=2, y=LY, sound="whoosh", vol=0.35)
    stk("👶", 118.68, 122.02, SR, SY, 100)
    lab(122.32, 124.56, "BABY *TENDANG*?", col=NAVY, box=CREAM, hi=ORANGE, rot=-3, y=LY, sound="pop", vol=0.45)
    stk("🦶", 122.36, 124.56, SR, SY, 100)
    ev.append(flash(tl(124.66), d=0.25))
    lab(124.70, 125.60, "*TAK JATUH*!", col=WHITE, box=NAVY, hi=MINT, rot=2, size=78, y=LY, sound="impact", vol=0.35)
    stk("✅", 124.74, 125.60, SR, SY, 110)
    lab(126.14, 127.04, "*MELEKAT* ELOK", col=NAVY, box=MINT, hi=WHITE, rot=-2, y=LY, sound="pop", vol=0.45)
    stk("💪", 126.18, 127.04, SR, SY, 100)

    # ---- recommendation
    lab(131.80, 133.64, "*OCTOPUS* FAN", col=WHITE, box=AQUA, hi=BUTTER, rot=-3, size=74, y=LY, sound="bloop", vol=0.45)
    stk("🐙", 131.84, 133.64, SR, SY, 110)
    lab(134.05, 136.06, "PALING *RECOMMENDED*!", col=NAVY, box=BUTTER, hi=ORANGE, rot=2, y=LY, sound="ding", vol=0.4)
    stk("👍", 134.09, 136.06, SR, SY, 110)

    # ---- CTA
    lab(137.36, 138.72, "TEKAN *BEG KUNING*", col=NAVY, box=BUTTER, hi=AQUA, rot=-2, y=LY, sound="kaching", vol=0.4)
    stk("🛒", 137.40, 138.72, SR, SY, 100)

    # ---- end card (inside the safe area)
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 8,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{NAVY}\1a&HFF&\t(0,250,\1a&H60&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    ev.append(label(e0 + 0.05, TOTAL, "KIPAS *STROLLER*", col=NAVY, box=BUTTER, hi=AQUA, y=430, rot=-3,
                    layer=9, size=64))
    ev.append(label(e0 + 0.3, TOTAL, "5 SPEED • LAMPU • KAKI OCTOPUS", col=NAVY, box=CREAM, hi=AQUA, y=540, rot=2,
                    layer=9, size=40))
    ev.append(label(e0 + 0.6, TOTAL, "MUMMY NAK *SATU*?", col=WHITE, box=AQUA, hi=BUTTER, y=655, rot=-2,
                    layer=9, size=50))
    ev.append(label(e0 + 0.9, TOTAL, "TEKAN BEG KUNING", col=NAVY, box=BUTTER, y=775, rot=2, layer=9, size=58))
    bstk("🐙", e0 + 0.1, TOTAL, SR, 350, 100)
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
