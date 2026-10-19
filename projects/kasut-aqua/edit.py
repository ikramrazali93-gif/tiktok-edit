#!/usr/bin/env python3
"""Edit for the aqua shoes (kasut pantai, adult + kids) TikTok video, two source clips joined.

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
# Two source clips of the same product type, joined into one timeline (master1080/proxy = A + B):
#   A (IMG_7886) 0 - 121.21s : unboxing her black aqua shoes on a picnic mat and trying them on
#   B (IMG_7887) 121.21s -   : close-ups of her black pair and the toddler's blue pair walking on the mat
# Source times below are per clip (from a.wav / b.wav); A()/B() map them onto the joined
# timeline (offsets measured by cross-correlating each clip's audio with the joined audio).
def A(t):
    return round(t + 0.02, 3)


def B(t):
    return round(t + 121.254, 3)


# v: list of (src_in, src_out, speed, zoom)
# a: 'same' (follow v at speed 1), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK (B): "Kita pakai kasut nak pergi pantai. Dia macam stokin je tu kan. Dia ada tapak kan, tengok tapak dia.
    #  Ni tapak dia."  (feet of mum + toddler -> toddler's blue pair -> the sole of the black pair)
    #  ("pergi ... pantai" pause tightened)
    dict(name="hook", a="same", v=[(B(0.03), B(1.33), 1, 1.0), (B(2.07), B(2.62), 1, 1.0), (B(9.28), B(10.62), 1, 1.05),
                                   (B(11.23), B(12.78), 1, 1.0), (B(13.83), B(14.78), 1, 1.1)]),
    # A: "Ini kasut pantai."  ("Bismillah / Ini kasut / untuk bunda dengan bapa" cut)
    dict(name="pantai", a="same", v=[(A(14.22), A(15.27), 1, 1.05)]),
    # "Okay saya nak cuba."  ("Padan ke tidak" cut)
    dict(name="cuba", a="same", v=[(A(17.40), A(18.15), 1, 1.0)]),
    # taking them out of the plastic, fast
    dict(name="buka", a=None, v=[(A(18.30), A(24.15), 3, 1.0)]),
    # "Hitam lah. Smart."  (J-cut onto her holding the shoe up; pause between the two cut)
    dict(name="smart", a=[(A(25.40), A(26.04)), (A(26.58), A(27.42))], v=[(A(34.00), A(35.48), 1, 1.08)]),
    # pulling them on, fast
    dict(name="pakai", a=None, v=[(A(46.50), A(57.50), 2.5, 1.0)]),
    # "Dia padan."  ("tapi dia macam ngam-ngam sangat lah, dia kan nak pakai stokin lagi" cut)
    dict(name="padan", a="same", v=[(A(79.30), A(80.28), 1, 1.05)]),
    # "Ngam-ngam sangat lah kasut."
    dict(name="ngam", a="same", v=[(A(109.55), A(110.64), 1, 1.1)]),
    # B: toddler's pair: "Wow, comel!"
    dict(name="comel", a="same", v=[(B(20.55), B(21.80), 1, 1.0)]),
    # mum + toddler walking on the mat (no speech)
    dict(name="jalan", a=None, v=[(B(24.00), B(28.00), 1, 1.0)]),
    # toddler walking, slowed, under the end card
    dict(name="end", a=None, v=[(B(33.60), B(36.10), 0.8, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "Okey": "Okay", "itu": "tu"}
# hand-checked words where Whisper drifted or misheard (re-transcribed per clip)
def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


def _wa(*ws):
    return _w(*[(w, A(s), A(e)) for w, s, e in ws])


def _wb(*ws):
    return _w(*[(w, B(s), B(e)) for w, s, e in ws])


OVERRIDE = {
    B(0.03): _wb(("Kita", 0.06, 0.22), ("pakai", 0.24, 0.40), ("kasut", 0.40, 0.72), ("nak", 0.72, 0.92),
                 ("pergi", 0.92, 1.30)),
    B(2.07): _wb(("pantai.", 2.10, 2.58)),
    B(9.28): _wb(("Dia", 9.30, 9.44), ("macam", 9.46, 9.64), ("stokin", 9.64, 10.20),
                 ("tu", 10.22, 10.42), ("kan.", 10.42, 10.60)),
    B(11.23): _wb(("Dia", 11.25, 11.34), ("ada", 11.34, 11.48), ("tapak", 11.48, 11.86), ("kan,", 11.86, 12.00),
                  ("tengok", 12.20, 12.34), ("tapak", 12.34, 12.56), ("dia.", 12.56, 12.74)),
    B(13.83): _wb(("Ni", 13.85, 14.00), ("tapak", 14.05, 14.42), ("dia.", 14.42, 14.74)),
    A(14.22): _wa(("Ini", 14.25, 14.56), ("kasut", 14.56, 14.86), ("pantai.", 14.86, 15.24)),
    A(17.40): _wa(("Okay", 17.42, 17.62), ("saya", 17.65, 17.78), ("nak", 17.80, 17.92), ("cuba.", 17.94, 18.12)),
    A(25.40): _wa(("Hitam", 25.44, 25.74), ("lah.", 25.74, 26.02)),
    A(26.58): _wa(("Smart.", 26.62, 27.36)),
    A(79.30): _wa(("Dia", 79.32, 79.54), ("padan.", 79.58, 80.26)),
    A(109.55): _wa(("Ngam", 109.57, 109.80), ("-ngam", 109.80, 110.02), ("sangat", 110.02, 110.26), ("lah", 110.26, 110.40),
                   ("kasut.", 110.40, 110.62)),
    B(20.55): _wb(("Wow,", 20.58, 20.98), ("comel!", 21.12, 21.76)),
}
DROP = []
HILITE = {"KASUT", "PANTAI.", "PANTAI", "STOKIN", "TAPAK", "SMART", "SMART.", "HITAM", "PADAN", "PADAN.", "NGAM-NGAM",
          "COMEL", "COMEL!"}

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
Style: Cap,Fredoka,58,&H00FFFFFF,&H000000FF,&H004D2616,&H644D2616,-1,0,0,0,100,100,0,0,1,5,3,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Label,Fredoka,62,&H004D2616,&H000000FF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,3,16,0,5,40,40,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,&H004D2616,&H644D2616,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# palette from the shoes and the beach: navy (text/outline), ocean blue (kids' pair), aqua water, sun yellow,
# coral, sand, charcoal (her black pair)
NAVY = "&H004D2616&"     # #16264D  (ASS colours are BGR)
OCEAN = "&H00E75B2F&"    # #2F5BE7
AQUA = "&H00C5D322&"     # #22D3C5
SUN = "&H003FD2FF&"      # #FFD23F  active caption word (stands out on the black shoes and the maroon mat)
CORAL = "&H005A6BFF&"    # #FF6B5A
SAND = "&H00D6F1FF&"     # #FFF1D6
CHAR = "&H00302A2A&"     # #2A2A30
WHITE = "&H00FFFFFF&"
ACC = SUN
KEY = AQUA

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


def label(t0, t1, text, y=270, col=NAVY, box=WHITE, hi=SUN, rot=-3, layer=5, x=CX, size=62):
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
              rf"{{\an7\pos(0,0)\c{AQUA}\fscx0\t(0,{int(TOTAL * 1000)},\fscx100)\p1}}m 0 0 l {W} 0 {W} 8 0 8{{\p0}}")

    def lab(s0, s1, text, sound="pop", vol=0.5, **kw):
        ev.append(label(tl(s0), tl(s1), text, **kw))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def stk(em, s0, s1, x, y, size=100):
        stickers.append((em, tl(s0), tl(s1), x, y, size))

    def bstk(em, t0, t1, x, y, size=100):
        stickers.append((em, t0, t1, x, y, size))

    SL, SR, SY = 85, 555, 175     # stickers sit beside the labels, above the product

    def speed_tag(name, txt=">> x3"):
        b = BT[name]
        ev.append(f"Dialogue: 6,{ts(b['t0'])},{ts(b['t0'] + b['dur'])},Small,,0,0,0,,"
                  rf"{{\an7\pos({SAFE_L},{SAFE_T + 20})\c{SUN}}}{txt}")
        sfx.append(("swish", b["t0"] - 0.05, 0.45))

    def blab(t0, t1, text, sound="pop", vol=0.5, **kw):
        ev.append(label(t0, t1, text, **kw))
        if sound:
            sfx.append((sound, t0, vol))

    # ---- HOOK (B): beach shoes -> like socks -> but with a sole
    lab(B(0.06), B(2.58), "*KASUT PANTAI*!", col=NAVY, box=SUN, hi=OCEAN, rot=-3, size=74, sound="bloop", vol=0.5)
    stk("🏖️", B(0.10), B(2.58), SR, SY, 105)
    lab(B(9.30), B(10.60), "MACAM *STOKIN*", col=WHITE, box=OCEAN, hi=SUN, rot=2, size=68, sound="whoosh", vol=0.35)
    stk("🧦", B(9.34), B(10.60), SR, SY, 100)
    ev.append(flash(tl(B(11.25)), d=0.25))
    lab(B(11.25), B(12.74), "TAPI ADA *TAPAK*!", col=NAVY, box=AQUA, hi=WHITE, rot=-2, size=70, sound="ding", vol=0.4)
    stk("👟", B(11.29), B(12.74), SR, SY, 100)
    lab(B(13.85), B(14.74), "TENGOK *TAPAK* DIA", col=WHITE, box=CORAL, hi=SUN, rot=2, size=64, sound="click", vol=0.5)
    stk("👀", B(13.89), B(14.74), SR, SY, 95)

    # ---- A: her black pair
    lab(A(14.25), A(15.24), "*UNBOXING*!", col=NAVY, box=SAND, hi=OCEAN, rot=-2, size=70, sound="bloop", vol=0.45)
    stk("📦", A(14.29), A(15.24), SR, SY, 100)
    lab(A(17.42), A(18.12), "JOM *CUBA*!", col=WHITE, box=OCEAN, hi=SUN, rot=2, size=72, sound="pop", vol=0.45)
    speed_tag("buka", ">> x3")
    lab(A(25.44), A(26.02), "*HITAM*", col=WHITE, box=CHAR, hi=SUN, rot=-3, size=76, sound="pop", vol=0.45)
    stk("🖤", A(25.48), A(26.02), SR, SY, 95)
    lab(A(26.62), A(27.36), "*SMART*!", col=NAVY, box=SUN, hi=CORAL, rot=3, size=82, sound="ding", vol=0.4)
    stk("😎", A(26.66), A(27.36), SR, SY, 105)
    speed_tag("pakai", ">> x2.5")
    ev.append(flash(tl(A(79.32)), d=0.25))
    lab(A(79.32), A(80.26), "DIA *PADAN*!", col=WHITE, box=AQUA, hi=NAVY, rot=-2, size=76, sound="bloop", vol=0.5)
    stk("✅", A(79.36), A(80.26), SR, SY, 95)
    lab(A(109.57), A(110.62), "*NGAM-NGAM*!", col=NAVY, box=SUN, hi=CORAL, rot=2, size=78, sound="pop", vol=0.5)
    stk("👌", A(109.61), A(110.62), SR, SY, 100)

    # ---- B: the toddler's pair
    lab(B(20.58), B(21.76), "*COMEL*!", col=WHITE, box=OCEAN, hi=SUN, rot=-3, size=82, sound="sparkle", vol=0.35)
    stk("🥰", B(20.62), B(21.76), SR, SY, 100)
    j0 = BT["jalan"]["t0"]
    blab(j0 + 0.1, j0 + 1.9, "ANAK PUN *ADA*", col=NAVY, box=AQUA, hi=WHITE, rot=-2, sound="bloop", vol=0.45)
    bstk("👦", j0 + 0.15, j0 + 1.9, SR, SY, 100)
    blab(j0 + 2.0, j0 + 3.95, "*BUNDA & ANAK*", col=WHITE, box=CORAL, hi=SUN, rot=2, sound="pop", vol=0.45)
    bstk("👩", j0 + 2.05, j0 + 3.95, SL, SY, 95)
    bstk("👣", j0 + 2.05, j0 + 3.95, SR, SY, 95)

    # ---- end card (inside the safe area)
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 8,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{NAVY}\1a&HFF&\t(0,250,\1a&H60&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    ev.append(label(e0 + 0.05, TOTAL, "*KASUT PANTAI*", col=NAVY, box=SUN, hi=OCEAN, y=430, rot=-3, layer=9, size=66))
    ev.append(label(e0 + 0.3, TOTAL, "DEWASA • BUDAK", col=WHITE, box=OCEAN, hi=SUN, y=540, rot=2, layer=9, size=50))
    ev.append(label(e0 + 0.6, TOTAL, "SIAP NAK KE *PANTAI*?", col=NAVY, box=SAND, hi=CORAL, y=655, rot=-2,
                    layer=9, size=50))
    ev.append(label(e0 + 0.9, TOTAL, "TEKAN BEG KUNING", col=NAVY, box=AQUA, hi=WHITE, y=775, rot=2, layer=9, size=58))
    bstk("🏖️", e0 + 0.1, TOTAL, SR, 350, 100)
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
