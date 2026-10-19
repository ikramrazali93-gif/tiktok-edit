#!/usr/bin/env python3
"""Edit for the denim jacket (jaket jeans, Denim + Acid Blue) TikTok video.

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
    # HOOK (moved from 35.3s): "Saya dah survey banyak dekat kedai, dekat TikTok Shop juga. Yang ni antara yang
    # paling murah."  J-cut over her holding the Acid Blue jacket up to the camera
    dict(name="hook", a=[(35.34, 38.69), (33.66, 35.03)], v=[(43.30, 48.03, 1, 1.0)]),
    # "Ni jacket jeans. Saya beli lagi satu colour."  ("Saya rasa" + "betul tak?" dropped, pause cut)
    dict(name="intro", a="same", v=[(0.79, 1.97, 1, 1.0), (3.00, 4.80, 1, 1.05)]),
    # "Ni colour acid blue."  (the false start "ni colour..." + pause before it cut)
    dict(name="acid", a="same", v=[(7.45, 8.80, 1, 1.05)]),
    # "Okey, ni denim, ni acid blue. Jadi kita tengok."
    dict(name="dua", a="same", v=[(9.72, 12.05, 1, 1.0)]),
    # tearing the plastic open (x3, no speech)
    dict(name="buka", a=None, v=[(12.05, 16.45, 3, 1.0)]),
    # "Ni cerah sikit colour dia. Kalau pasangan, kan? Cerah sikit je. | Saya pakai denim. Yang ni colour
    # acid blue. Dah ada dua colour."  (zoom-in split for variety)
    dict(name="cerah", a="same", v=[(16.45, 21.80, 1, 1.0), (21.80, 26.25, 1, 1.08)]),
    # "Macam saya pakai, sebijik."  (the repeated "cuma ni colour denim, ni colour acid blue" is cut)
    dict(name="sebijik", a="same", v=[(27.85, 29.00, 1, 1.0)]),
    # (v2) "Yang lain, harga atas daripada, mahal sikit. Ni jimat RM10." dropped: no specific prices
    # "Tengok dekat beg kuning tau."  (moved to the end as the CTA)
    dict(name="cta", a="same", v=[(32.33, 33.29, 1, 1.0)]),
    # jacket close to the camera, gentle slow-mo - end card
    dict(name="end", a=None, v=[(26.25, 27.75, 0.6, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "color": "colour"}
# hand-checked words (re-transcribed per clip)
def _w(*ws):
    return [dict(w=w, s=a, e=b) for w, a, b in ws]


_ACID = _w(("Ni", 7.55, 7.90), ("colour", 7.90, 8.10), ("acid", 8.10, 8.44), ("blue.", 8.44, 8.72))
_CERAH = _w(("Ni", 16.55, 16.86), ("cerah", 16.86, 17.24), ("sikit", 17.24, 17.42), ("colour", 17.42, 17.62),
            ("dia.", 17.62, 18.10), ("Kalau", 18.18, 18.84), ("pasangan,", 18.84, 19.70), ("kan?", 20.10, 20.28),
            ("Cerah", 20.34, 20.66), ("sikit", 20.66, 21.18), ("je.", 21.18, 21.58),
            ("Saya", 22.32, 22.44), ("pakai", 22.44, 22.66), ("denim.", 22.66, 23.38), ("Yang", 23.52, 23.82),
            ("ni", 23.82, 23.96), ("colour", 23.96, 24.22), ("acid", 24.22, 24.66), ("blue.", 24.66, 25.00),
            ("Dah", 25.44, 25.54), ("ada", 25.54, 25.68), ("dua", 25.68, 25.84), ("colour.", 25.84, 26.20))
_INTRO = _w(("Ni", 0.84, 1.04), ("jacket", 1.04, 1.34), ("jeans.", 1.34, 1.90),
            ("Saya", 3.04, 3.10), ("beli", 3.10, 3.38), ("lagi", 3.38, 3.64), ("satu", 3.64, 3.96),
            ("colour.", 3.96, 4.26))
OVERRIDE = {
    35.34: _w(("Saya", 35.36, 35.53), ("dah", 35.53, 35.67), ("survey", 35.67, 35.97), ("banyak", 35.97, 36.53),
              ("dekat", 36.53, 37.09), ("kedai,", 37.09, 37.67), ("dekat", 37.67, 38.07), ("TikTok", 38.07, 38.31),
              ("Shop", 38.31, 38.51), ("juga.", 38.51, 38.67)),
    33.66: _w(("Yang", 33.68, 33.93), ("ni", 33.93, 34.11), ("antara", 34.11, 34.43), ("yang", 34.43, 34.53),
              ("paling", 34.53, 34.75), ("murah!", 34.75, 35.01)),
    0.79: _INTRO, 3.00: _INTRO,
    7.45: _ACID,
    9.72: _w(("Okey,", 9.80, 10.05), ("ni", 10.10, 10.30), ("denim,", 10.30, 10.64), ("ni", 10.76, 10.94), ("acid", 10.94, 11.18),
             ("blue.", 11.18, 11.38), ("Jadi", 11.50, 11.56), ("kita", 11.56, 11.68), ("tengok.", 11.68, 11.98)),
    16.45: _CERAH, 21.80: _CERAH,
    27.85: _w(("Macam", 27.88, 28.04), ("saya", 28.04, 28.14), ("pakai,", 28.14, 28.44), ("sebijik.", 28.44, 28.96)),
    38.69: _w(("Yang", 38.70, 38.80), ("lain,", 38.80, 39.34), ("harga", 39.74, 39.86), ("atas", 39.86, 40.30),
              ("daripada,", 40.30, 41.02), ("mahal", 41.02, 41.36), ("sikit.", 41.36, 41.54),
              ("Ni", 41.86, 42.12), ("jimat", 42.12, 42.42), ("RM10.", 42.42, 42.82)),
    32.33: _w(("Tengok", 32.42, 32.56), ("dekat", 32.56, 32.78), ("beg", 32.78, 32.88), ("kuning", 32.88, 33.14),
              ("tau.", 33.14, 33.26)),
}
DROP = []
HILITE = {"DENIM", "ACID", "BLUE", "TIKTOK", "SHOP", "CERAH", "SEBIJIK", "KUNING"}


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
Style: Cap,Fredoka,58,&H00FFFFFF,&H000000FF,&H005C2F1F,&H64401808,-1,0,0,0,100,100,0,0,1,5,3,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Label,Fredoka,62,&H005C2F1F,&H000000FF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,3,16,0,5,40,40,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,&H005C2F1F,&H64401808,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# palette for the denim jacket (Denim + Acid Blue, picnic on the grass): indigo text, denim blue,
# acid-wash light blue, mustard (warm contrast to all the blue), tangerine for the price
INDIGO = "&H005C2F1F&"   # #1F2F5C  (ASS colours are BGR)
DENIM = "&H00A86F3E&"    # #3E6FA8
ACIDB = "&H00E8C7A9&"    # #A9C7E8
MUST = "&H003CC9FF&"     # #FFC93C
TANG = "&H003D7AFF&"     # #FF7A3D
WHITE = "&H00FFFFFF&"
ESP = INDIGO             # default label text colour (kept name for label())
ACC = MUST
KEY = ACIDB


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
                t = x["w"].upper().strip(",.!?")
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


def label(t0, t1, text, y=330, col=ESP, box=WHITE, hi=DENIM, rot=-3, layer=5, x=CX, size=62):
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


def graphics():
    ev, stickers, sfx = [], [], []
    # progress bar (retention) - top edge is clear of the TikTok UI
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{MUST}\fscx0\t(0,{int(TOTAL * 1000)},\fscx100)\p1}}m 0 0 l {W} 0 {W} 8 0 8{{\p0}}")

    def lab(s0, s1, text, sound="pop", vol=0.5, **kw):
        ev.append(label(tl(s0), tl(s1), text, **kw))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def stk(em, s0, s1, x, y, size=100):
        stickers.append((em, tl(s0), tl(s1), x, y, size))

    def bstk(em, t0, t1, x, y, size=100):
        stickers.append((em, t0, t1, x, y, size))

    def blab(name, text, sound="pop", vol=0.45, d0=0.1, **kw):
        b = BT[name]
        ev.append(label(b["t0"] + d0, b["t0"] + b["dur"], text, **kw))
        if sound:
            sfx.append((sound, b["t0"] + d0, vol))

    SL, SR, SY = 85, 555, 330

    def speed_tag(name, txt=">> x3"):
        b = BT[name]
        ev.append(f"Dialogue: 6,{ts(b['t0'])},{ts(b['t0'] + b['dur'])},Small,,0,0,0,,"
                  rf"{{\an7\pos({SAFE_L},{SAFE_T + 20})\c{MUST}}}{txt}")
        sfx.append(("swish", b["t0"] - 0.05, 0.45))

    # ---- HOOK: surveyed everywhere -> this one is among the cheapest
    ev.append(flash(0.0, d=0.3))
    lab(35.36, 37.05, "DAH *SURVEY* BANYAK", col=INDIGO, box=WHITE, hi=DENIM, rot=-3, size=70, sound="bloop", vol=0.5)
    stk("🔍", 35.40, 37.05, SR, SY - 100, 95)
    lab(37.09, 38.67, "KEDAI & *TIKTOK SHOP*", col=WHITE, box=DENIM, hi=MUST, rot=2, size=66, sound="pop", vol=0.5)
    stk("🛍️", 37.12, 38.67, SL, SY - 100, 90)
    ev.append(flash(tl(33.68), d=0.25))
    lab(33.68, 35.03, "NI *PILIHAN SAYA*!", col=INDIGO, box=MUST, hi=WHITE, rot=-3, size=76, sound="ding", vol=0.45)
    stk("👍", 33.72, 35.03, SR, SY - 100, 105)

    # ---- intro
    lab(0.84, 1.90, "JAKET *JEANS*", col=INDIGO, box=WHITE, hi=DENIM, rot=-2, size=74, sound="whoosh", vol=0.35)
    stk("🧥", 0.88, 1.90, SR, SY - 100, 100)
    lab(3.04, 4.26, "BELI *LAGI SATU*!", col=WHITE, box=DENIM, hi=MUST, rot=2, size=70)
    stk("🛒", 3.08, 4.26, SL, SY - 100, 90)

    # ---- colours
    lab(7.55, 8.80, "KALER *ACID BLUE*", col=INDIGO, box=ACIDB, hi=DENIM, rot=-2, size=72, sound="sparkle", vol=0.35)
    stk("🩵", 7.52, 8.75, SR, SY - 100, 100)
    lab(9.86, 11.40, "*DENIM* + *ACID BLUE*", col=WHITE, box=INDIGO, hi=MUST, rot=2, size=66, sound="pop", vol=0.5)
    stk("✌️", 9.90, 11.40, SR, SY - 100, 95)
    lab(11.50, 11.98, "JOM *TENGOK*!", col=INDIGO, box=MUST, hi=DENIM, rot=-3, size=70, sound="pop", vol=0.45)

    # ---- unboxing
    speed_tag("buka")
    blab("buka", "BUKA *PLASTIK*", col=INDIGO, box=WHITE, hi=DENIM, rot=2)
    b = BT["buka"]
    bstk("✂️", b["t0"] + 0.15, b["t0"] + b["dur"], SR, SY - 100, 90)

    # ---- acid blue is lighter
    lab(16.86, 18.10, "*CERAH* SIKIT", col=INDIGO, box=ACIDB, hi=DENIM, rot=-2, size=74, sound="sparkle", vol=0.35)
    stk("☀️", 16.90, 18.10, SR, SY - 100, 100)
    lab(18.18, 20.28, "KALAU *PASANGAN*?", col=WHITE, box=DENIM, hi=MUST, rot=2, size=68, sound="pop", vol=0.45)
    stk("👫", 18.22, 20.28, SR, SY - 100, 100)
    lab(22.32, 23.38, "SAYA PAKAI *DENIM*", col=WHITE, box=INDIGO, hi=ACIDB, rot=-3, size=68, sound="pop", vol=0.45)
    stk("👈", 22.36, 23.38, SL, SY - 100, 90)
    lab(23.52, 25.00, "NI *ACID BLUE*", col=INDIGO, box=ACIDB, hi=DENIM, rot=2, size=72, sound="pop", vol=0.45)
    stk("🩵", 23.56, 25.00, SR, SY - 100, 100)
    ev.append(flash(tl(25.44), d=0.25))
    lab(25.44, 26.20, "DAH ADA *2 KALER*!", col=INDIGO, box=MUST, hi=DENIM, rot=-2, size=72, sound="ding", vol=0.4)
    stk("✌️", 25.48, 26.20, SR, SY - 100, 100)
    lab(27.88, 28.96, "*SEBIJIK* MACAM NI!", col=WHITE, box=DENIM, hi=MUST, rot=2, size=70, sound="bloop", vol=0.45)
    stk("👯", 27.92, 28.96, SR, SY - 100, 100)

    # ---- CTA
    lab(32.42, 33.29, "TENGOK *BEG KUNING*", col=INDIGO, box=MUST, hi=DENIM, rot=-2, size=68, sound="pop", vol=0.5)
    stk("🛒", 32.46, 33.29, SR, SY - 100, 95)

    # ---- end card (inside the safe area, above the jacket)
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 8,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{INDIGO}\1a&HFF&\t(0,250,\1a&H70&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    ev.append(label(e0 + 0.05, TOTAL, "JAKET *JEANS*", col=WHITE, box=DENIM, hi=MUST, y=300, rot=-3,
                    layer=9, size=74))
    ev.append(label(e0 + 0.3, TOTAL, "DENIM • ACID BLUE", col=INDIGO, box=ACIDB, hi=DENIM, y=410, rot=2,
                    layer=9, size=46))
    ev.append(label(e0 + 0.6, TOTAL, "KORANG PILIH *KALER MANA*?", col=WHITE, box=INDIGO, hi=MUST, y=525, rot=-2,
                    layer=9, size=48))
    ev.append(label(e0 + 0.9, TOTAL, "TEKAN BEG KUNING", col=INDIGO, box=MUST, y=645, rot=2, layer=9, size=58))
    bstk("🧥", e0 + 0.1, TOTAL, SR, 225, 90)
    bstk("👇", e0 + 0.65, TOTAL, SL, 470, 80)
    bstk("🛒", e0 + 0.95, TOTAL, SR, 575, 90)
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
