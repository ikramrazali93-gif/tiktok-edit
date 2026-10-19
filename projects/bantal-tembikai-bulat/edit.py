#!/usr/bin/env python3
"""Edit for the round watermelon plush pillow (bantal tembikai bulat) TikTok video.

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
# Single source clip (IMG_2925), outdoors on the grass: J&T parcel -> plastic bag -> round watermelon plush
# with a face, little arms and legs. The first ~1.5s (shipping label visible) is never used.
# v: list of (src_in, src_out, speed, zoom)
# a: 'same' (follow v at speed 1), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK (moved from 15.3s): "Dah ada ke belum tembikai? Comel ni, nampak tak?"
    #  J-cut over the close-up of the watermelon's face (42.4s)
    dict(name="hook", a=[(15.30, 18.08)], v=[(42.40, 45.18, 1, 1.06)]),
    # "Unboxing lagi, jom kita tengok. | Apa pula kali ni?"  (pause between cut; parcel label never shown)
    dict(name="intro", a="same", v=[(4.62, 7.20, 1, 1.0), (8.22, 9.32, 1, 1.06)]),
    # tearing the parcel open (x3, no speech)
    dict(name="buka", a=None, v=[(9.32, 13.20, 3, 1.0)]),
    # "Tembikai, korang!"  (rind showing through the torn parcel)
    dict(name="tembikai", a="same", v=[(13.22, 15.10, 1, 1.05)]),
    # pulling it out of the plastic (x3; "Sebentar kita buka, nampak dia" muted)
    dict(name="plastik", a=None, v=[(18.10, 25.30, 3, 1.0)]),
    # "Ya Allah! | Besar bulat macam ni, gemoy macam ni! | Bestnya!"  (zoom split, pause before "Bestnya" cut)
    dict(name="wow", a="same", v=[(25.40, 27.10, 1, 1.0), (27.10, 30.62, 1, 1.08), (31.10, 31.68, 1, 1.0)]),
    # "Boleh buat hadiah, | boleh buat bantal peluk."
    dict(name="hadiah", a="same", v=[(32.82, 34.20, 1, 1.0), (34.48, 37.08, 1, 1.06)]),
    # "Comelnya!"  ("comel kan?" cut - repeat)
    dict(name="comel", a="same", v=[(37.78, 38.86, 1, 1.0)]),
    # "Dalam material dia ni bulu-bulu fluffyyy."  (the "Ya Allah" after it is cut)
    dict(name="fluffy", a="same", v=[(40.12, 42.45, 1, 1.08)]),
    # "Ada kaki, ada tangan."
    dict(name="kaki", a="same", v=[(44.56, 46.05, 1, 1.0)]),
    # "Mesti anak korang suka. | Bukan anak korang saja suka, mama pun suka!"
    dict(name="suka", a="same", v=[(46.28, 47.92, 1, 1.0), (48.22, 51.98, 1, 1.06)]),
    # "Belilah satu, beli buat hadiah untuk birthday anak. | Confirm anak happy, excited lah!"
    dict(name="beli", a="same", v=[(52.02, 55.32, 1, 1.0), (55.32, 57.72, 1, 1.08)]),
    # "Tekan beg kuning."  ("Saya pun excited… nampaknya", "so fluffy" cut)
    dict(name="cta", a="same", v=[(65.80, 66.94, 1, 1.0)]),
    # her hugging the watermelon, gentle slow-mo under the end card (muted)
    dict(name="end", a=None, v=[(61.60, 63.60, 0.8, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "bantai": "bantal"}
# hand-checked words (chunk re-transcription + RMS envelope); Whisper's segment-end timings drift
def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


OVERRIDE = {
    15.30: _w(("Dah", 15.33, 15.52), ("ada", 15.52, 15.74), ("ke", 15.74, 15.86), ("belum", 15.86, 16.16),
              ("tembikai?", 16.16, 17.04), ("Comel", 17.10, 17.54), ("ni,", 17.54, 17.72), ("nampak", 17.82, 17.98),
              ("tak?", 17.98, 18.06)),
    4.62: _w(("Unboxing", 4.66, 5.22), ("lagi,", 5.22, 6.10), ("jom", 6.38, 6.76), ("kita", 6.76, 7.00),
             ("tengok.", 7.00, 7.18)),
    8.22: _w(("Apa", 8.25, 8.54), ("pula", 8.54, 8.76), ("kali", 8.76, 8.98), ("ni?", 8.98, 9.28)),
    13.22: _w(("Tembikai,", 13.25, 14.05), ("korang!", 14.10, 15.05)),
    25.40: _w(("Ya", 25.45, 25.90), ("Allah!", 25.90, 27.05)),
    27.10: _w(("Besar", 27.15, 28.02), ("bulat", 28.02, 28.46), ("macam", 28.46, 28.76), ("ni,", 28.76, 28.98),
              ("gemoy", 29.05, 29.50), ("macam", 29.50, 29.94), ("ni!", 29.94, 30.58)),
    31.10: _w(("Bestnya!", 31.13, 31.65)),
    32.82: _w(("Boleh", 32.84, 33.00), ("buat", 33.00, 33.20), ("hadiah,", 33.20, 34.16)),
    34.48: _w(("boleh", 35.22, 35.42), ("buat", 35.42, 35.64), ("bantal", 35.64, 36.00), ("peluk.", 36.00, 37.04)),
    37.78: _w(("Comelnya!", 37.80, 38.84)),
    40.12: _w(("Dalam", 40.15, 40.36), ("material", 40.36, 40.66), ("dia", 40.66, 40.86), ("ni", 40.86, 41.08),
              ("bulu", 41.08, 41.32), ("-bulu", 41.32, 41.58), ("fluffy.", 41.58, 42.40)),
    44.56: _w(("Ada", 44.58, 44.80), ("kaki,", 44.80, 45.24), ("ada", 45.40, 45.54), ("tangan.", 45.54, 46.02)),
    46.28: _w(("Mesti", 46.33, 46.82), ("anak", 46.82, 47.06), ("korang", 47.06, 47.40), ("suka.", 47.40, 47.88)),
    48.22: _w(("Bukan", 48.27, 48.66), ("anak", 48.66, 48.88), ("korang", 48.88, 49.16), ("saja", 49.16, 49.28),
              ("suka,", 49.28, 49.56), ("mama", 49.80, 50.68), ("pun", 50.68, 50.98), ("suka!", 50.98, 51.95)),
    52.02: _w(("Belilah", 52.05, 52.56), ("satu,", 52.56, 53.00), ("beli", 53.35, 54.04), ("buat", 54.04, 54.20),
              ("hadiah", 54.20, 54.50), ("untuk", 54.50, 54.70), ("birthday", 54.70, 54.95), ("anak.", 54.95, 55.28)),
    55.32: _w(("Confirm", 55.35, 55.82), ("anak", 55.82, 56.12), ("happy,", 56.12, 56.92), ("excited", 57.18, 57.56),
              ("lah!", 57.56, 57.70)),
    65.80: _w(("Tekan", 65.84, 66.14), ("beg", 66.20, 66.40), ("kuning.", 66.40, 66.90)),
}
DROP = []
HILITE = {"TEMBIKAI", "TEMBIKAI?", "COMEL", "GEMOY", "BESAR", "BULAT", "HADIAH", "PELUK", "COMELNYA", "FLUFFY",
          "BULU-BULU", "KAKI", "TANGAN", "SUKA", "MAMA", "BIRTHDAY", "HAPPY", "EXCITED", "KUNING", "BESTNYA"}


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
Style: Cap,Fredoka,60,&H00FFFFFF,&H000000FF,&H00315A1E,&H50315A1E,-1,0,0,0,100,100,0,0,1,5,2,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Stk,Fredoka,64,&H00FFFFFF,&H000000FF,&H00FFFFFF,&H55000000,-1,0,0,0,100,100,1,0,1,16,4,5,40,40,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,&H00315A1E,&H50315A1E,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# palette from the watermelon: rind greens, flesh pinks, seed black, cream
DEEP = "&H00315A1E&"     # #1E5A31  dark rind green (caption outline, label outlines)
RIND = "&H004DA33F&"     # #3FA34D  rind green
LEAF = "&H00A0E4B9&"     # #B9E4A0  pale green (the arms / legs)
FLESH = "&H008A5CFF&"    # #FF5C8A  watermelon pink (active caption word)
RED = "&H005E24E0&"      # #E0245E  deep watermelon red
CREAM = "&H00E8F8FF&"    # #FFF8E8
SEED = "&H002B2B2B&"     # #2B2B2B
SUN = "&H003FD2FF&"      # #FFD23F
WHITE = "&H00FFFFFF&"


def captions(words):
    """Refreshed caption look: white words, dark-green outline; the active word turns watermelon pink
    with a white outline (sticker style) and pops slightly."""
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
                    parts.append(r"{\c%s\3c%s\bord6\fscx116\fscy116}%s{\r}" % (FLESH, WHITE, t))
                elif t.strip(",.?!") in HILITE:
                    parts.append(r"{\c%s}%s{\r}" % (LEAF, t))
                else:
                    parts.append(t)
            pop = r"{\fscx85\fscy85\t(0,90,\fscx100\fscy100)}" if j == 0 else ""
            ev.append(f"Dialogue: 2,{ts(ws)},{ts(we)},Cap,,0,0,0,,{pop}" + " ".join(parts))
    return ev


_FIT_FONTS = {}


def fit_size(text, size, max_w=SAFE_W - 90):   # room for the thick sticker outline + pop overshoot
    """Shrink a label's font size so it stays inside the safe area."""
    plain = text.replace("*", "")
    f = _FIT_FONTS.setdefault(size, ImageFont.truetype(FONT_FILE, size))
    w = f.getlength(plain) * ASS_PER_PIL
    return size if w <= max_w else int(size * max_w / w)


def label(t0, t1, text, y=265, col=WHITE, ol=DEEP, hi=SUN, rot=0, layer=5, x=CX, size=66):
    """Refreshed label: die-cut sticker text (thick white outline + coloured inner outline), no box.
    *word* is drawn in the highlight colour. Two stacked lines: white cut line behind, coloured text in front."""
    size = fit_size(text, size)
    plain = text.replace("*", "")
    parts = text.split("*")
    rich = "".join(p if i % 2 == 0 else rf"{{\c{hi}}}{p}{{\c{col}}}" for i, p in enumerate(parts))
    anim = (rf"\an5\pos({x},{y})\frz{rot}\fs{size}\fscx0\fscy0"
            r"\t(0,140,\fscx115\fscy115)\t(140,240,\fscx100\fscy100)\fad(0,150)")
    back = (f"Dialogue: {layer},{ts(t0)},{ts(t1)},Stk,,0,0,0,,"
            rf"{{{anim}\bord15\shad4\c&HFFFFFF&\3c&HFFFFFF&}}{plain}")
    front = (f"Dialogue: {layer + 1},{ts(t0)},{ts(t1)},Stk,,0,0,0,,"
             rf"{{{anim}\bord6\shad0\c{col}\3c{ol}}}{rich}")
    return back + "\n" + front


def flash(t0, d=0.3, layer=9, col=FLESH):
    """Soft watermelon-pink flash (refresh: replaces the white flash)."""
    return (f"Dialogue: {layer},{ts(t0)},{ts(t0 + d)},Shape,,0,0,0,,"
            rf"{{\an7\pos(0,0)\c{col}\1a&H60&\fad(0,{int(d * 1000) - 40})\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")


SEED_SHAPE = r"m 0 -16 b 10 -16 13 6 0 19 b -13 6 -10 -16 0 -16"


def seeds(t0, t1, pts, layer=4):
    """Watermelon-seed motif: little black seeds that pop in (and wobble) around a label."""
    ev = []
    for k, (x, y, r) in enumerate(pts):
        d = 60 * k
        ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
                  rf"{{\an7\pos({x},{y})\c{SEED}\3c&HFFFFFF&\bord2\frz{r}\fscx0\fscy0"
                  rf"\t({d},{d + 140},\fscx110\fscy110)\t({d + 140},{d + 220},\fscx100\fscy100)"
                  rf"\t({d + 220},{int((t1 - t0) * 1000)},\frz{r + 25})\fad(0,150)\p1}}{SEED_SHAPE}{{\p0}}")
    return ev


def graphics():
    ev, stickers, sfx = [], [], []
    # progress bar styled as a watermelon rind: dark green with a pale-green inner line
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{RIND}\fscx0\t(0,{int(TOTAL * 1000)},\fscx100)\p1}}m 0 0 l {W} 0 {W} 10 0 10{{\p0}}")
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,10)\c{LEAF}\fscx0\t(0,{int(TOTAL * 1000)},\fscx100)\p1}}m 0 0 l {W} 0 {W} 4 0 4{{\p0}}")

    def lab(s0, s1, text, sound="pop", vol=0.5, **kw):
        ev.append(label(tl(s0), tl(s1), text, **kw))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def stk(em, s0, s1, x, y, size=100):
        stickers.append((em, tl(s0), tl(s1), x, y, size))

    def bstk(em, t0, t1, x, y, size=100):
        stickers.append((em, t0, t1, x, y, size))

    SL, SR, SY = 85, 560, 180     # stickers sit beside the labels, above the product

    def speed_tag(name, txt=">> x3"):
        b = BT[name]
        ev.append(f"Dialogue: 6,{ts(b['t0'])},{ts(b['t0'] + b['dur'])},Small,,0,0,0,,"
                  rf"{{\an7\pos({SAFE_L},{SAFE_T + 20})\c{SUN}}}{txt}")
        sfx.append(("swish", b["t0"] - 0.05, 0.45))

    def blab(t0, t1, text, sound="pop", vol=0.5, **kw):
        ev.append(label(t0, t1, text, **kw))
        if sound:
            sfx.append((sound, t0, vol))

    # ---- HOOK: do you have a watermelon yet? -> cute, see?
    lab(15.33, 17.06, "DAH ADA *TEMBIKAI*?", col=WHITE, ol=DEEP, hi=FLESH, size=70, sound="bloop", vol=0.5)
    stk("🍉", 15.36, 17.06, SR, SY - 60, 105)
    ev += seeds(tl(15.33), tl(17.06), [(70, 330, -20), (600, 330, 15), (110, 205, 30)])
    ev.append(flash(tl(17.10), d=0.28))
    lab(17.10, 18.06, "*COMEL* NI!", col=WHITE, ol=RED, hi=SUN, rot=-3, size=80, sound="ding", vol=0.4)
    stk("👀", 17.13, 18.06, SR, SY - 60, 100)

    # ---- intro / unboxing
    lab(4.66, 6.10, "*UNBOXING* LAGI!", col=WHITE, ol=DEEP, hi=SUN, rot=-2, size=70, sound="whoosh", vol=0.35)
    stk("📦", 4.70, 6.10, SR, SY - 60, 95)
    lab(6.38, 7.18, "JOM *TENGOK*!", col=WHITE, ol=RIND, hi=SUN, rot=2, size=70)
    lab(8.25, 9.28, "APA *KALI NI*?", col=WHITE, ol=RED, hi=SUN, rot=-2, size=70, sound="bloop", vol=0.45)
    stk("🤔", 8.28, 9.28, SR, SY - 60, 95)
    speed_tag("buka", ">> x3")
    ev.append(flash(tl(13.25), d=0.28))
    lab(13.25, 15.05, "*TEMBIKAI*!", col=WHITE, ol=DEEP, hi=FLESH, rot=-3, size=88, sound="ding", vol=0.45)
    stk("🍉", 13.28, 15.05, SR, SY - 60, 110)
    ev += seeds(tl(13.25), tl(15.05), [(85, 340, -10), (585, 335, 20)])
    speed_tag("plastik", ">> x3")
    b = BT["plastik"]
    blab(b["t0"] + 0.1, b["t0"] + b["dur"], "BUKA *PLASTIK*", col=WHITE, ol=DEEP, hi=LEAF, rot=2, sound=None)

    # ---- reveal
    stk("😱", 25.45, 27.05, SR, SY + 20, 110)
    lab(25.45, 27.05, "YA ALLAH!", col=WHITE, ol=RED, hi=SUN, rot=-3, size=78, sound="impact", vol=0.4)
    lab(27.15, 28.98, "*BESAR* & *BULAT*", col=WHITE, ol=DEEP, hi=FLESH, rot=2, size=70, sound="pop", vol=0.5)
    stk("⭕", 27.18, 28.98, SR, SY - 60, 90)
    lab(29.05, 30.58, "*GEMOY*!", col=WHITE, ol=RED, hi=SUN, rot=-3, size=96, sound="bloop", vol=0.5)
    stk("🥹", 29.08, 30.58, SR, SY - 60, 110)
    ev += seeds(tl(29.05), tl(30.58), [(95, 330, 10), (580, 330, -15), (140, 200, -30)])
    lab(31.13, 31.65, "BESTNYA!", col=WHITE, ol=RIND, hi=SUN, rot=2, size=80, sound="sparkle", vol=0.35)
    stk("😍", 31.15, 31.65, SL, SY - 60, 100)

    # ---- uses
    lab(32.84, 34.16, "BOLEH BUAT *HADIAH*", col=WHITE, ol=DEEP, hi=SUN, rot=-2, size=66, sound="pop", vol=0.5)
    stk("🎁", 32.87, 34.16, SR, SY - 60, 100)
    lab(35.22, 37.04, "*BANTAL PELUK*", col=WHITE, ol=RED, hi=LEAF, rot=2, size=74, sound="bloop", vol=0.45)
    stk("🤗", 35.25, 37.04, SR, SY - 60, 100)
    lab(37.80, 38.84, "*COMELNYA*!", col=WHITE, ol=RED, hi=SUN, rot=-3, size=84, sound="sparkle", vol=0.35)
    stk("💕", 37.83, 38.84, SL, SY - 60, 95)
    lab(40.15, 42.40, "BULU-BULU *FLUFFY*", col=WHITE, ol=DEEP, hi=LEAF, rot=2, size=66, sound="pop", vol=0.5)
    stk("☁️", 40.18, 42.40, SR, SY - 60, 100)
    lab(44.58, 46.02, "ADA *KAKI* & *TANGAN*", col=WHITE, ol=RIND, hi=SUN, rot=-2, size=64, sound="bloop", vol=0.45)
    stk("🙌", 44.61, 46.02, SR, SY - 60, 100)

    # ---- kids + mum
    lab(46.33, 47.88, "ANAK MESTI *SUKA*", col=WHITE, ol=DEEP, hi=FLESH, rot=2, size=66, sound="pop", vol=0.5)
    stk("👧", 46.36, 47.88, SR, SY - 60, 100)
    ev.append(flash(tl(49.80), d=0.28))
    lab(49.80, 51.95, "MAMA PUN *SUKA*!", col=WHITE, ol=RED, hi=SUN, rot=-3, size=74, sound="ding", vol=0.4)
    stk("💖", 49.83, 51.95, SR, SY - 60, 100)
    ev += seeds(tl(49.80), tl(51.95), [(80, 330, -20), (590, 330, 20)])

    # ---- gift + CTA
    lab(53.35, 55.28, "HADIAH *BIRTHDAY* ANAK", col=WHITE, ol=DEEP, hi=SUN, rot=2, size=62, sound="pop", vol=0.5)
    stk("🎂", 53.38, 55.28, SR, SY - 60, 100)
    lab(55.35, 57.70, "ANAK *HAPPY*!", col=WHITE, ol=RED, hi=SUN, rot=-2, size=78, sound="sparkle", vol=0.35)
    stk("🥳", 55.38, 57.70, SR, SY - 60, 105)
    lab(65.84, 66.90, "TEKAN *BEG KUNING*", col=WHITE, ol=DEEP, hi=SUN, rot=2, size=66, sound="pop", vol=0.5)
    stk("🛒", 65.87, 66.90, SR, SY - 60, 95)

    # ---- end card: ribbon banner + pills (refresh: replaces the stacked boxes)
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 8,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{DEEP}\1a&HFF&\t(0,250,\1a&H70&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    by = 400
    ev.append(f"Dialogue: 9,{ts(e0 + 0.05)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos({CX},{by})\c{RED}\3c&HFFFFFF&\bord5\shad4\4c&H60000000&\frz-3\fscx0\t(0,200,\fscx100)\p1}}"
              r"m -270 -52 l 270 -52 l 236 0 l 270 52 l -270 52 l -236 0{\p0}")
    ev.append(f"Dialogue: 10,{ts(e0 + 0.15)},{ts(TOTAL)},Stk,,0,0,0,,"
              rf"{{\an5\pos({CX},{by})\frz-3\fs{fit_size('BANTAL TEMBIKAI', 58, 430)}\bord0\shad0\c&HFFFFFF&\fad(120,0)}}"
              "BANTAL TEMBIKAI")
    ev.append(label(e0 + 0.35, TOTAL, "BULAT • GEBU • ADA KAKI", col=WHITE, ol=RIND, hi=SUN, y=520, rot=2,
                    layer=11, size=44))
    ev.append(label(e0 + 0.6, TOTAL, "TAG MAMA YANG *SUKA COMEL*!", col=WHITE, ol=DEEP, hi=FLESH, y=625, rot=-2,
                    layer=11, size=46))
    ev.append(label(e0 + 0.9, TOTAL, "TEKAN *BEG KUNING*", col=WHITE, ol=RED, hi=SUN, y=740, rot=2,
                    layer=11, size=56))
    ev += seeds(e0 + 0.1, TOTAL, [(90, 470, -20), (575, 470, 25), (100, 690, 15), (560, 690, -10)], layer=12)
    bstk("🍉", e0 + 0.1, TOTAL, SR, 300, 100)
    bstk("👇", e0 + 0.65, TOTAL, SL, 690, 80)
    bstk("🛒", e0 + 0.95, TOTAL, SR, 800, 85)
    sfx += [("whoosh", e0 - 0.1, 0.4), ("pop", e0 + 0.05, 0.45), ("pop", e0 + 0.35, 0.45), ("pop", e0 + 0.6, 0.4),
            ("ding", e0 + 0.9, 0.35)]
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
