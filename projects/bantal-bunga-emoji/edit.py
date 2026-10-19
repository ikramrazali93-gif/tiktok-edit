#!/usr/bin/env python3
"""Edit for the rainbow emoji flower pillow (bantal bunga emoji) TikTok video.

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
# Single source clip IMG_2927 (outdoors on grass): two rainbow-petal emoji flower pillows.
# v: list of (src_in, src_out, speed, zoom)
# a: 'same' (follow v at speed 1), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK (moved from 14.0s): "Lidah dia boleh siap angkat lagi, bergerak-gerak lagi, comel kan?"
    #  (she pulls the winking pillow close and flicks its tongue)
    dict(name="hook", a="same", v=[(13.97, 18.20, 1, 1.05)]),
    # "Korang dah ada belum bantal bunga yang comel, cute ni? Size dia 38cm. Ada 4 gaya emoji muka dia.
    #  Boleh pilih nak muka love ke, nak muka yang kenyit mata macam ni ke"  (0.3s pause after "love ke" cut)
    dict(name="intro", a="same", v=[(0.00, 6.12, 1, 1.0), (6.12, 9.30, 1, 1.08), (9.30, 11.08, 1, 1.0),
                                    (11.40, 13.95, 1, 1.1)]),
    # "Letak dalam kereta pun sangat-sangat sesuai."  ("Letak dekat cermin bonet tu" cut: unclear)
    dict(name="kereta", a="same", v=[(18.53, 20.90, 1, 1.05)]),
    # "Hoi, lawa!"
    dict(name="lawa", a="same", v=[(22.50, 23.60, 1, 1.0)]),
    # front / side / back of the pillow, fast, no speech ("Ok ni dari depan, dari sisi, dari belakang" cut)
    dict(name="view", a=None, v=[(24.40, 28.90, 2, 1.0)]),
    # "Material dia jenis kain velvet. Kain velvet ni dia tahan lasak. Kaler dia tak pudar walaupun kita dah
    #  guna lama, kaler dia tetap cantik dan macam baru je. | Saya pun ni dah beli lama dah, tapi dia nampak
    #  macam baru je kan?"
    dict(name="velvet", a="same", v=[(29.12, 34.00, 1, 1.0), (34.00, 39.37, 1, 1.07), (39.37, 42.55, 1, 1.0)]),
    # "Boleh jadi hadiah."  ("Ah, recommended" before it cut: filler, Whisper can't hear it out of context)
    dict(name="hadiah", a="same", v=[(44.30, 45.35, 1, 1.05)]),
    # "Bolehlah cikgu-cikgu beli banyak-banyak buat hadiah untuk student."  ("Ok, recommended" repeat cut)
    dict(name="cikgu", a="same", v=[(45.73, 49.22, 1, 1.0)]),
    # "Korang tengok beg kuning."
    dict(name="cta", a="same", v=[(50.98, 52.32, 1, 1.05)]),
    # the winking pillow close, slowed, under the end card
    dict(name="end", a=None, v=[(11.40, 13.40, 0.8, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "bantai": "bantal", "belom": "belum", "kau": "ke", "reta": "kereta",
       "kala": "kaler", "Okey": "Okay"}
# hand-checked words where Whisper drifted or misheard (re-transcribed per clip)
def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


OVERRIDE = {
    13.97: _w(("Lidah", 14.02, 14.30), ("dia", 14.32, 14.46), ("boleh", 14.82, 14.97), ("siap", 14.97, 15.27),
              ("angkat", 15.27, 15.70), ("lagi,", 15.77, 16.10), ("bergerak", 16.20, 16.80), ("-gerak", 16.82, 17.18),
              ("lagi,", 17.21, 17.48), ("comel", 17.58, 17.93), ("kan?", 17.93, 18.15)),
    22.50: _w(("Hoi,", 22.55, 23.00), ("lawa!", 23.02, 23.52)),
    39.37: _w(("Saya", 39.40, 39.84), ("punya", 39.84, 39.98), ("ni", 39.98, 40.06), ("dah", 40.06, 40.20),
              ("beli", 40.20, 40.40), ("lama", 40.40, 40.72), ("dah,", 40.72, 41.00), ("tapi", 41.02, 41.48),
              ("dia", 41.48, 41.66), ("nampak", 41.66, 41.84), ("macam", 41.84, 42.00), ("baru", 42.00, 42.30),
              ("je", 42.30, 42.46), ("kan?", 42.46, 42.55)),
    44.30: _w(("Boleh", 44.36, 44.52), ("jadi", 44.52, 44.70), ("hadiah.", 44.70, 45.28)),
    45.73: _w(("Bolehlah", 45.76, 46.16), ("cikgu", 46.17, 46.37), ("-cikgu", 46.37, 46.63), ("beli", 46.63, 47.01),
              ("banyak", 47.01, 47.23), ("-banyak", 47.23, 47.47), ("buat", 47.47, 47.68), ("hadiah", 47.71, 47.89),
              ("untuk", 47.89, 48.40), ("student.", 48.50, 49.05)),
    50.98: _w(("Korang", 51.00, 51.30), ("tengok", 51.30, 51.44), ("beg", 51.44, 51.62), ("kuning.", 51.64, 52.25)),
}
DROP = []
HILITE = {"BANTAL", "BUNGA", "38CM", "EMOJI", "LOVE", "KENYIT", "MATA", "LIDAH", "ANGKAT", "KERETA", "LAWA!",
          "VELVET", "TAHAN", "LASAK", "PUDAR", "CANTIK", "BARU", "HADIAH", "HADIAH.", "CIKGU-CIKGU", "STUDENT",
          "STUDENT.", "KUNING", "COMEL", "RECOMMENDED"}

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


# palette from the rainbow petals: deep grape for text/outline, the seven petal colours, butter-yellow face, cream
GRAPE = bgr("#3B1F5C")
RED, ORANGE, YELLOW = bgr("#FF5A5F"), bgr("#FF9F1C"), bgr("#FFD93D")
GREEN, BLUE, PURPLE, PINK = bgr("#5CC96B"), bgr("#4D96FF"), bgr("#9B5DE5"), bgr("#FF7EB6")
CREAM = bgr("#FFF8E7")
WHITE = "&H00FFFFFF&"
RAINBOW = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, PINK]
KEY = YELLOW

ASS_HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Fredoka,61,&H00FFFFFF,&H000000FF,{GRAPE[:-1]},&H645C1F3B,-1,0,0,0,100,100,0,0,1,5,3,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Label,Fredoka,62,{GRAPE[:-1]},&H000000FF,&H00FFFFFF,{RED[:-1]},-1,0,0,0,100,100,0,0,3,15,7,5,40,40,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,{GRAPE[:-1]},&H645C1F3B,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def captions(words):
    """3-word chunks; the active word cycles through the rainbow petal colours (refresh: was one accent colour)."""
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
    n = 0
    for i, ch in enumerate(chunks):
        end = ch[-1]["e"] + 0.15
        if i + 1 < len(chunks):
            end = min(end, chunks[i + 1][0]["s"])
        for j, w in enumerate(ch):
            ws = w["s"] if j else min(w["s"], ch[0]["s"])
            we = ch[j + 1]["s"] if j + 1 < len(ch) else end
            acc = RAINBOW[n % len(RAINBOW)]
            n += 1
            parts = []
            for k, x in enumerate(ch):
                t = x["w"].upper().strip(",.")
                if k == j:
                    parts.append(r"{\c%s\3c&HFFFFFF&\bord6\fscx114\fscy114}%s{\r}" % (acc, t))
                elif t.strip("-") in HILITE or t in HILITE:
                    parts.append(r"{\c%s}%s{\r}" % (KEY, t))
                else:
                    parts.append(t)
            pop = r"{\fscx85\fscy85\t(0,90,\fscx100\fscy100)}" if j == 0 else ""
            ev.append(f"Dialogue: 2,{ts(ws)},{ts(we)},Cap,,0,0,0,,{pop}" + " ".join(parts))
    return ev


_FIT_FONTS = {}


def fit_size(text, size, max_w=SAFE_W - 90):   # room for the box border + shadow + pop overshoot
    """Shrink a label's font size so its box stays inside the safe area."""
    plain = text.replace("*", "")
    f = _FIT_FONTS.setdefault(size, ImageFont.truetype(FONT_FILE, size))
    w = f.getlength(plain) * ASS_PER_PIL
    return size if w <= max_w else int(size * max_w / w)


def label(t0, t1, text, y=270, col=GRAPE, box=WHITE, hi=PURPLE, sh=RED, layer=5, x=CX, size=62, rot=0):
    """Refresh: flat (no tilt) sticker label with a solid offset 'drop' box in a petal colour."""
    size = fit_size(text, size)
    parts = text.split("*")
    text = "".join(p if i % 2 == 0 else rf"{{\c{hi}}}{p}{{\c{col}}}" for i, p in enumerate(parts))
    return (f"Dialogue: {layer},{ts(t0)},{ts(t1)},Label,,0,0,0,,"
            rf"{{\an5\pos({x},{y})\frz{rot}\fs{size}\c{col}\3c{box}\4c{sh}\fscx0\fscy0"
            rf"\t(0,140,\fscx112\fscy112)\t(140,240,\fscx100\fscy100)\fad(0,150)}}{text}")


def petals(t0, x=CX, y=270, layer=4):
    """Refresh motif: little rainbow petal dots burst out from behind a label."""
    ev = []
    for i in range(10):
        ang = 2 * np.pi * i / 10 + 0.3
        dx, dy = 205 * np.cos(ang), 105 * np.sin(ang)
        col = RAINBOW[i % len(RAINBOW)]
        ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t0 + 0.55)},Shape,,0,0,0,,"
                  rf"{{\an7\move({x},{y},{x + dx:.0f},{y + dy:.0f},0,450)\c{col}\3c&HFFFFFF&\bord2\fad(0,250)\p1}}"
                  r"m -10 0 b -10 -13 10 -13 10 0 b 10 13 -10 13 -10 0{\p0}")
    return ev


def wipe(t0, layer=9):
    """Refresh transition: rainbow bands sweep across the frame (was a white flash)."""
    ev = []
    bh = H / 7
    for i, col in enumerate(RAINBOW):
        d0 = i * 25
        ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t0 + 0.6)},Shape,,0,0,0,,"
                  rf"{{\an7\move({-W},{i * bh:.0f},{W},{i * bh:.0f},{d0},{d0 + 420})\c{col}\1a&H25&\p1}}"
                  rf"m 0 0 l {W} 0 {W} {bh + 1:.0f} 0 {bh + 1:.0f}{{\p0}}")
    return ev


def half_disc(r):
    k = 0.5523 * r
    return (f"m {-r} 0 b {-r} {-k:.0f} {-k:.0f} {-r} 0 {-r} b {k:.0f} {-r} {r} {-k:.0f} {r} 0 l {-r} 0")


def rainbow_arc(t0, t1, x, y, r0=225, step=17, layer=8):
    """End-card rainbow: stacked half discs, outer red to inner purple, cream centre."""
    ev = []
    for i, col in enumerate(RAINBOW[:6] + [CREAM]):
        r = r0 - i * step if i < 6 else r0 - 6 * step - 4
        d = 60 * i
        ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
                  rf"{{\an7\pos({x},{y})\c{col}\fscx0\fscy0\t({d},{d + 220},\fscx100\fscy100)\p1}}{half_disc(r)}{{\p0}}")
    return ev


def graphics():
    ev, stickers, sfx = [], [], []
    # progress bar (retention) - rainbow segments, top edge is clear of the TikTok UI
    seg = W / 7
    for i, col in enumerate(RAINBOW):
        ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
                  rf"{{\an7\pos(0,0)\c{col}\clip(0,0,0,8)\t(0,{int(TOTAL * 1000)},\clip(0,0,{W},8))\p1}}"
                  rf"m {i * seg:.0f} 0 l {(i + 1) * seg:.0f} 0 {(i + 1) * seg:.0f} 8 {i * seg:.0f} 8{{\p0}}")

    def lab(s0, s1, text, sound="pop", vol=0.5, burst=False, **kw):
        ev.append(label(tl(s0), tl(s1), text, **kw))
        if burst:
            ev.extend(petals(tl(s0), y=kw.get("y", 270)))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def stk(em, s0, s1, x, y, size=100):
        stickers.append((em, tl(s0), tl(s1), x, y, size))

    def bstk(em, t0, t1, x, y, size=100):
        stickers.append((em, t0, t1, x, y, size))

    def blab(t0, t1, text, sound="pop", vol=0.5, **kw):
        ev.append(label(t0, t1, text, **kw))
        if sound:
            sfx.append((sound, t0, vol))

    def cut(name, sound="swish", vol=0.4):
        t0 = BT[name]["t0"]
        ev.extend(wipe(t0 - 0.12))
        sfx.append((sound, t0 - 0.12, vol))

    SL, SR, SY = 85, 555, 175     # stickers sit beside the labels, above the pillows

    def speed_tag(name, txt=">> x2"):
        b = BT[name]
        ev.append(f"Dialogue: 6,{ts(b['t0'])},{ts(b['t0'] + b['dur'])},Small,,0,0,0,,"
                  rf"{{\an7\pos({SAFE_L},{SAFE_T + 20})\c{YELLOW}}}{txt}")

    # ---- HOOK: the tongue lifts and wiggles
    lab(14.02, 15.75, "LIDAH *BOLEH ANGKAT*!", box=YELLOW, hi=RED, sh=PURPLE, size=70, sound="bloop", burst=True)
    stk("😛", 14.06, 15.75, SR, SY, 110)
    lab(16.20, 18.15, "*BERGERAK-GERAK*!", box=WHITE, hi=PINK, sh=BLUE, size=72, sound="sparkle", vol=0.35)
    stk("🤪", 16.24, 18.15, SL, SY, 105)

    # ---- intro: the product, size, the four faces
    cut("intro")
    lab(0.05, 3.15, "BANTAL *BUNGA* COMEL", box=WHITE, hi=ORANGE, sh=GREEN, size=64, sound="bloop", vol=0.45)
    stk("🌼", 0.10, 3.15, SR, SY, 100)
    lab(4.28, 6.10, "SIZE *38CM*", box=BLUE, col=WHITE, hi=YELLOW, sh=PURPLE, size=70, sound="click", vol=0.5)
    stk("📏", 4.32, 6.10, SR, SY, 90)
    lab(6.20, 9.25, "*4 GAYA* MUKA EMOJI", box=YELLOW, hi=PURPLE, sh=RED, size=64, sound="ding", vol=0.4, burst=True)
    stk("🤩", 6.24, 9.25, SR, SY, 100)
    lab(9.56, 11.05, "MUKA *LOVE*", box=PINK, col=WHITE, hi=YELLOW, sh=PURPLE, size=72, sound="pop", vol=0.45)
    stk("😍", 9.60, 11.05, SR, SY, 100)
    lab(11.45, 13.90, "MUKA *KENYIT MATA*", box=WHITE, hi=GREEN, sh=ORANGE, size=66, sound="pop", vol=0.45)
    stk("😉", 11.49, 13.90, SR, SY, 100)

    # ---- car + views
    cut("kereta")
    lab(18.58, 20.88, "SESUAI *DALAM KERETA*", box=GREEN, col=WHITE, hi=YELLOW, sh=BLUE, size=62, sound="pop", vol=0.45)
    stk("🚗", 18.62, 20.88, SR, SY, 100)
    lab(22.55, 23.52, "HOI, *LAWA*!", box=YELLOW, hi=RED, sh=PINK, size=78, sound="sparkle", vol=0.35, burst=True)
    stk("✨", 22.59, 23.52, SR, SY, 95)
    v0, vd = BT["view"]["t0"], BT["view"]["dur"]
    speed_tag("view", ">> x2")
    blab(v0 + 0.05, v0 + vd, "DEPAN • SISI • *BELAKANG*", box=WHITE, hi=BLUE, sh=YELLOW, size=56, sound="whoosh", vol=0.35)
    bstk("🔄", v0 + 0.1, v0 + vd, SR, SY, 90)

    # ---- velvet, colour stays, bought long ago
    cut("velvet")
    lab(29.12, 31.56, "KAIN *VELVET*", box=PURPLE, col=WHITE, hi=YELLOW, sh=PINK, size=74, sound="bloop", vol=0.45)
    stk("🧸", 29.16, 31.56, SR, SY, 100)
    lab(31.60, 33.56, "*TAHAN LASAK*", box=WHITE, hi=RED, sh=ORANGE, size=74, sound="pop", vol=0.45)
    stk("💪", 31.64, 33.56, SR, SY, 100)
    lab(33.62, 36.30, "KALER *TAK PUDAR*", box=YELLOW, hi=PURPLE, sh=GREEN, size=68, sound="ding", vol=0.4, burst=True)
    stk("🌈", 33.66, 36.30, SR, SY, 100)
    lab(36.40, 39.30, "TETAP *CANTIK*", box=PINK, col=WHITE, hi=GRAPE, sh=BLUE, size=72, sound="pop", vol=0.45)
    stk("💖", 36.44, 39.30, SR, SY, 95)
    lab(39.42, 41.00, "SAYA DAH *BELI LAMA*", box=WHITE, hi=BLUE, sh=PURPLE, size=62, sound="pop", vol=0.45)
    stk("🗓️", 39.46, 41.00, SR, SY, 90)
    lab(41.02, 42.50, "MASIH *MACAM BARU*!", box=GREEN, col=WHITE, hi=YELLOW, sh=ORANGE, size=64, sound="sparkle", vol=0.35)
    stk("✨", 41.06, 42.50, SR, SY, 95)

    # ---- gift idea
    cut("hadiah")
    lab(44.36, 45.30, "BOLEH JADI *HADIAH*", box=WHITE, hi=PINK, sh=GREEN, size=64, sound="pop", vol=0.45, burst=True)
    stk("🎁", 44.40, 45.30, SR, SY, 100)
    lab(45.76, 47.45, "*CIKGU-CIKGU*!", box=BLUE, col=WHITE, hi=YELLOW, sh=RED, size=70, sound="pop", vol=0.45)
    stk("🍎", 45.80, 47.45, SR, SY, 95)
    lab(47.47, 49.05, "HADIAH *STUDENT*", box=YELLOW, hi=PURPLE, sh=BLUE, size=66, sound="pop", vol=0.45)
    stk("🎒", 47.51, 49.05, SR, SY, 95)

    # ---- CTA
    lab(51.02, 52.28, "TENGOK *BEG KUNING*", box=WHITE, hi=ORANGE, sh=YELLOW, size=64, sound="bloop", vol=0.5)
    stk("🛒", 51.06, 52.28, SR, SY, 95)

    # ---- end card: rainbow arc (refresh) + stacked flat stickers, inside the safe area
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 7,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{GRAPE}\1a&HFF&\t(0,250,\1a&H60&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    ev.extend(rainbow_arc(e0, TOTAL, CX, 470))
    bstk("🌼", e0 + 0.45, TOTAL, CX, 395, 110)
    ev.append(label(e0 + 0.35, TOTAL, "BANTAL *BUNGA EMOJI*", box=WHITE, hi=ORANGE, sh=RED, y=530, layer=9, size=60))
    ev.append(label(e0 + 0.6, TOTAL, "4 GAYA • 38CM • VELVET", box=PURPLE, col=WHITE, hi=YELLOW, sh=PINK, y=640,
                    layer=9, size=44))
    ev.append(label(e0 + 0.85, TOTAL, "KORANG PILIH *MUKA MANA*?", box=YELLOW, hi=RED, sh=GREEN, y=745, layer=9,
                    size=46))
    ev.append(label(e0 + 1.1, TOTAL, "TEKAN BEG KUNING", box=GREEN, col=WHITE, hi=YELLOW, sh=BLUE, y=850, layer=9,
                    size=54))
    bstk("👇", e0 + 0.9, TOTAL, SL, 690, 80)
    bstk("🛒", e0 + 1.15, TOTAL, SR, 800, 90)
    sfx += [("whoosh", e0 - 0.1, 0.4), ("sparkle", e0 + 0.1, 0.35), ("pop", e0 + 0.35, 0.45), ("pop", e0 + 0.6, 0.45),
            ("pop", e0 + 0.85, 0.4), ("ding", e0 + 1.1, 0.4)]
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
