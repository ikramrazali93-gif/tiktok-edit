#!/usr/bin/env python3
"""Edit for the sunglasses (2 designs: brown round + rimless) TikTok video.

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
    # HOOK (from 87.5s, for hijabi viewers): "Yang ni kalau kita pakai tudung ke apa ke, dia tak nampak kembung sangat."
    dict(name="hook", a="same", v=[(87.48, 89.60, 1, 1.0), (89.60, 91.72, 1, 1.12)]),
    # "Okay ni spek mata. Kita nak beli nak pakai pi pantai ni awak."
    dict(name="intro", a="same", v=[(0.48, 2.50, 1, 1.0), (3.66, 5.47, 1, 1.1)]),
    # "...kita tengok ada orang tu pakai cantik, lepas tu kita pun teracun. Nanti tengok saya pakai nah."
    # + "Okay ada dua jenis spek."
    dict(name="racun", a="same", v=[(10.42, 15.36, 1, 1.0), (16.48, 17.42, 1, 1.1)]),
    dict(name="ramp1", a=None, v=[(17.45, 25.58, 3.0, 1.0)]),
    # "Wow. Ini colour brown." (repeat at 29.8 cut)
    dict(name="brown", a="same", v=[(25.62, 27.12, 1, 1.12)]),
    dict(name="ramp2", a=None, v=[(27.15, 31.95, 2.5, 1.0)]),
    dict(name="pakai", a="same", v=[(32.00, 32.66, 1, 1.0)]),
    # putting the brown pair on, sped up
    dict(name="ramp3", a=None, v=[(32.68, 40.75, 3.0, 1.0)]),
    # "Cantik tak?" (x3 -> once) + "Jujur, jujur, jujur."
    dict(name="cantik", a="same", v=[(40.78, 41.62, 1, 1.15), (46.50, 47.45, 1, 1.0)]),
    # "Okay dah colour brown saya pakai. Saya jarang nak pakai shades ni."
    dict(name="jarang", a="same", v=[(47.98, 51.02, 1, 1.0)]),
    # "Tapi ni tak ada power lah. Nanti saya akan pakai contact lens."
    dict(name="power", a="same", v=[(53.98, 56.88, 1, 1.1)]),
    # "Saja lah nak pi berenang, nak bawa anak main pantai, sah. Nak pakai kan, panas kan, kita pakai shades lah."
    dict(name="pantai", a="same", v=[(57.66, 61.42, 1, 1.0), (62.22, 63.84, 1, 1.1), (64.32, 68.26, 1, 1.0)]),
    # "Okay lagi satu kita ada desain yang ni."
    dict(name="design2", a="same", v=[(68.80, 70.52, 1, 1.0)]),
    # unwrapping + putting on the rimless pair, sped up
    dict(name="ramp4", a=None, v=[(70.55, 83.55, 4.0, 1.0)]),
    # "Sebab nampak tak, dia punya ni halus je."
    dict(name="halus", a="same", v=[(92.28, 96.40, 1, 1.1)]),
    # "Dia tak kembung tudung kita betul. Ha ini tak kembung awak." + "Kalau kata nak bergaya ke apa kan."
    dict(name="kembung", a="same", v=[(102.58, 105.62, 1, 1.0), (106.22, 107.70, 1, 1.1)]),
    # "Harga murahnya, murah sangat. Nak ambil tu, dah saya ambil dua sebab murah saja."
    dict(name="harga", a="same", v=[(118.33, 121.42, 1, 1.0)]),
    # "Okay boleh tengok dekat beg kuning."
    dict(name="cta", a="same", v=[(123.36, 125.08, 1, 1.1)]),
    # both pairs in her hands
    dict(name="end", a=None, v=[(120.80, 123.30, 1, 1.0)]),
]

FIX = {"ini": "ni", "Okey": "Okay", "panah": "panas", "bag": "beg", "begku": "beg"}
# hand-checked words where Whisper drifted or misheard
OVERRIDE = {
    57.66: [dict(s=s, e=e, w=w) for w, s, e in [("Saja", 57.74, 58.00), ("lah", 58.00, 58.14), ("nak", 58.14, 58.46),
                                                ("pi", 58.46, 59.00), ("berenang,", 61.00, 61.40)]],
    62.22: [dict(s=s, e=e, w=w) for w, s, e in [("nak", 62.34, 62.42), ("bawa", 62.42, 62.74), ("anak", 62.74, 62.96),
                                                ("main", 62.96, 63.16), ("pantai.", 63.16, 63.80)]],
}
DROP = []
HILITE = {"SPEK", "MATA", "PANTAI", "CANTIK", "TERACUN", "DUA", "JENIS", "BROWN", "COLOUR", "JUJUR", "SHADES",
          "POWER", "CONTACT", "LENS", "BERENANG", "PANAS", "DESAIN", "TUDUNG", "KEMBUNG", "HALUS", "BERGAYA",
          "HARGA", "MURAH", "MURAHNYA", "BEG", "KUNING"}


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
                if txt.strip(",.?!"):
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
Style: Cap,Fredoka,58,&H00FFFFFF,&H000000FF,&H00121A2B,&H64121A2B,-1,0,0,0,100,100,0,0,1,5,3,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Label,Fredoka,62,&H00121A2B,&H000000FF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,3,16,0,5,40,40,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,&H00121A2B,&H64121A2B,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# palette from the sunglasses + beach theme: espresso text, tortoise brown (round pair),
# amber/gold (rimless tint), sea teal
ESPRESSO = "&H00121A2B&" # #2B1A12  (ASS colours are BGR)
TORT = "&H00205AA8&"     # #A85A20 (highlight on white)
AMBER = "&H0020B0FF&"    # #FFB020
TEAL = "&H00B0B519&"     # #19B5B0
CREAM = "&H00DCF4FF&"    # #FFF4DC
WHITE = "&H00FFFFFF&"
ACC = AMBER
KEY = CREAM


def captions(words):
    ev = []
    chunks, cur = [], []
    for w in words:
        if cur and (len(cur) >= 3 or w["s"] - cur[-1]["e"] > 0.35 or w["clip"] != cur[-1]["clip"]
                    or cur[-1]["w"][-1] in ",."):
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


def label(t0, t1, text, y=760, col=ESPRESSO, box=WHITE, hi=TORT, rot=-3, layer=5, x=CX, size=62):
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
              rf"{{\an7\pos(0,0)\c{AMBER}\fscx0\t(0,{int(TOTAL * 1000)},\fscx100)\p1}}m 0 0 l {W} 0 {W} 8 0 8{{\p0}}")

    def bt(name, off=0.0):
        return BT[name]["t0"] + off

    def end_of(name):
        return BT[name]["t0"] + BT[name]["dur"]

    def lab(s0, s1, text, sound="pop", vol=0.5, **kw):
        ev.append(label(tl(s0), tl(s1), text, **kw))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def blab(t0, t1, text, sound="pop", vol=0.5, **kw):
        ev.append(label(t0, t1, text, **kw))
        if sound:
            sfx.append((sound, t0, vol))

    def stk(em, s0, s1, x, y, size=100):
        stickers.append((em, tl(s0), tl(s1), x, y, size))

    def bstk(em, t0, t1, x, y, size=100):
        stickers.append((em, t0, t1, x, y, size))

    def tag(name, text):
        ev.append(f"Dialogue: 6,{ts(bt(name))},{ts(end_of(name))},Small,,0,0,0,,"
                  rf"{{\an7\pos({SAFE_L},{SAFE_T + 20})\c{AMBER}}}{text}")
        sfx.append(("swish", bt(name) - 0.05, 0.45))

    SL, SR, SY = 85, 555, 665

    # ---- HOOK: for hijabi viewers
    lab(87.50, 89.95, "PAKAI *TUDUNG*?", col=ESPRESSO, box=AMBER, hi=WHITE, rot=-3, size=74, sound="whoosh", vol=0.4)
    stk("🧕", 87.55, 89.95, SR, SY, 110)
    lab(90.42, 91.72, "TAK *KEMBUNG*!", col=WHITE, box=TEAL, hi=AMBER, rot=3, size=78, sound="ding", vol=0.35)
    stk("✅", 90.46, 91.72, SR, SY, 100)

    # ---- intro
    lab(1.52, 2.50, "*SPEK MATA*", rot=-2, size=72)
    stk("🕶️", 1.56, 2.50, SR, SY, 110)
    lab(4.30, 5.47, "PAKAI KE *PANTAI*", col=ESPRESSO, box=CREAM, hi=TORT, rot=2)
    stk("🏖️", 4.34, 5.47, SR, SY, 100)
    lab(11.32, 12.58, "ORANG PAKAI *CANTIK*", rot=-2)
    lab(12.62, 14.20, "KITA PUN *TERACUN*!", col=WHITE, box=ESPRESSO, hi=AMBER, rot=3, sound="bloop", vol=0.5)
    stk("🤭", 12.66, 14.20, SR, SY, 100)
    lab(16.56, 17.42, "*2* JENIS", col=ESPRESSO, box=AMBER, hi=WHITE, rot=-3, size=76)
    stk("🕶️", 16.60, 17.42, SL, 640, 90)
    stk("👓", 16.70, 17.42, SR, SY, 90)
    tag("ramp1", ">> x3")

    # ---- design 1: brown
    lab(26.48, 27.12, "*COLOUR BROWN*", col=WHITE, box=TORT, hi=AMBER, rot=2, sound="sparkle", vol=0.3)
    stk("🤎", 26.52, 27.12, SR, SY, 90)
    tag("ramp2", ">> x2.5")
    tag("ramp3", ">> x3")
    ev.append(flash(bt("cantik"), d=0.25))
    lab(40.90, 41.62, "*CANTIK* TAK?", col=ESPRESSO, box=AMBER, hi=WHITE, rot=-3, size=76, sound="impact", vol=0.4)
    stk("😎", 40.94, 41.62, SR, SY, 110)
    lab(46.52, 47.45, "JUJUR!", rot=3, size=76, sound="bloop", vol=0.5)
    stk("🤔", 46.56, 47.45, SR, SY, 100)
    lab(49.76, 51.02, "JARANG PAKAI *SHADES*", rot=-2)
    lab(54.18, 55.08, "TAK ADA *POWER*", col=WHITE, box=ESPRESSO, hi=AMBER, rot=2)
    stk("👁️", 54.22, 55.08, SR, SY, 90)
    lab(55.10, 56.88, "PAKAI *CONTACT LENS*", rot=-2)
    lab(58.46, 61.42, "PI *BERENANG*", col=WHITE, box=TEAL, hi=AMBER, rot=3)
    stk("🏊", 58.50, 61.42, SR, SY, 100)
    lab(62.34, 63.84, "MAIN *PANTAI*", rot=-2)
    stk("🏖️", 62.38, 63.84, SR, SY, 100)
    lab(65.58, 67.10, "*PANAS* KAN", col=ESPRESSO, box=AMBER, hi=WHITE, rot=2)
    stk("☀️", 65.62, 67.10, SR, SY, 110)
    lab(67.18, 68.26, "PAKAI *SHADES*!", rot=-3, sound="ding", vol=0.35)
    stk("😎", 67.22, 68.26, SR, SY, 100)

    # ---- design 2: rimless
    lab(69.00, 70.52, "DESAIN *KEDUA*", col=WHITE, box=TEAL, hi=AMBER, rot=2, sound="whoosh", vol=0.35)
    stk("✨", 69.04, 70.52, SR, SY, 90)
    tag("ramp4", ">> x4")
    lab(92.30, 94.20, "SEBAB...", rot=3)
    lab(94.28, 96.40, "BINGKAI *HALUS*", col=WHITE, box=TORT, hi=AMBER, rot=-2, sound="sparkle", vol=0.3)
    stk("👓", 94.32, 96.40, SR, SY, 100)
    lab(103.08, 104.20, "TUDUNG *TAK KEMBUNG*", col=WHITE, box=TEAL, hi=AMBER, rot=2)
    stk("🧕", 103.12, 104.20, SR, SY, 100)
    lab(104.66, 105.62, "BETUL!", rot=-3, size=76, sound="ding", vol=0.35)
    lab(106.24, 107.70, "NAK *BERGAYA*", col=ESPRESSO, box=AMBER, hi=WHITE, rot=3)
    stk("💃", 106.28, 107.70, SR, SY, 100)

    # ---- price + CTA
    lab(118.40, 119.74, "HARGA *MURAH*!", col=WHITE, box=ESPRESSO, hi=AMBER, rot=-2, size=72, sound="kaching", vol=0.35)
    stk("💸", 118.44, 119.74, SR, SY, 100)
    lab(119.80, 121.42, "SAYA AMBIL *DUA*!", rot=3)
    stk("✌️", 119.84, 121.42, SR, SY, 100)
    lab(123.40, 125.08, "TENGOK *BEG KUNING*", col=ESPRESSO, box=AMBER, hi=WHITE, rot=-2)
    stk("🛒", 123.44, 125.08, SR, SY, 100)

    # ---- end card (inside the safe area)
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 8,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{ESPRESSO}\1a&HFF&\t(0,250,\1a&H60&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    ev.append(label(e0 + 0.05, TOTAL, "*SHADES* 2 DESAIN", y=430, rot=-3, layer=9, size=66))
    ev.append(label(e0 + 0.3, TOTAL, "BROWN • RIMLESS", col=WHITE, box=TORT, hi=AMBER, y=540, rot=2, layer=9,
                    size=52))
    ev.append(label(e0 + 0.6, TOTAL, "KORANG PILIH *YANG MANA*?", col=WHITE, box=TEAL, hi=AMBER, y=655, rot=-2,
                    layer=9, size=46))
    ev.append(label(e0 + 0.9, TOTAL, "TEKAN BEG KUNING", col=ESPRESSO, box=AMBER, y=775, rot=2, layer=9, size=58))
    bstk("🕶️", e0 + 0.1, TOTAL, SR, 350, 100)
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
