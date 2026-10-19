#!/usr/bin/env python3
"""Edit for the black knit baby beanie (topi baby) TikTok video.

Combines two source clips of the same product into one timeline:
  A = 0 .. 37.567s   hands-only close-ups (no voice, used as b-roll)
  B = 37.567 .. 79.1s talking to camera (all the voice)
master1080.mp4 / proxy.mp4 are A+B concatenated; B transcript times are offset by 37.567s.

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
# Source A (0-37.567) is silent close-up b-roll; all voice comes from source B (37.567-79.1).
BLOCKS = [
    # HOOK (J-cut over A close-ups): "Mummy yang ada baby, grab lah dia."
    # + "Boleh pakai daripada baby new born. Sampai setahun pun boleh pakai."
    dict(name="hook", a=[(37.97, 40.66), (54.25, 57.50)],
         v=[(6.80, 9.49, 1, 1.0), (26.00, 29.25, 1, 1.08)]),
    # A: unboxing from the plastic (x2.5, no voice)
    dict(name="unbox", a=None, v=[(0.30, 5.30, 2.5, 1.0)]),
    # "Topi ni dia material yang stretchable." (over A: stretched open, patch close-up)
    dict(name="topi", a=[(40.92, 43.74)], v=[(16.30, 19.12, 1, 1.0)]),
    # "Kalau baby pakai dia tak memekakkan telinga lah." (Whisper: "memerkakkan")
    dict(name="telinga", a="same", v=[(44.06, 47.30, 1, 1.0)]),
    # "Ni baby selesa, baby pun tak tarik sebab selesa kan."
    dict(name="selesa", a="same", v=[(47.72, 49.90, 1, 1.0), (49.90, 52.18, 1, 1.12)]),
    # "Kat sini dia ada, tu, smile." (B close-up of the smile patch)
    dict(name="smile", a="same", v=[(58.68, 62.40, 1, 1.0)]),
    # "Material pun sedap, selesa, lembut, stretchable macam ni kan." (over A: hat on hand, stretching)
    # + "Ni bahagian belakang, ni bahagian depan. Ada macam-macam warna."
    dict(name="material", a=[(63.00, 71.42)], v=[(20.00, 24.22, 1, 1.0), (67.22, 71.42, 1, 1.0)]),
    # "Lelaki perempuan boleh pakai."
    dict(name="laki", a="same", v=[(75.93, 77.40, 1, 1.08)]),
    # "Boleh tengok dekat beg kuning."
    dict(name="beg", a="same", v=[(71.47, 73.65, 1, 1.0)]),
    # "Comel tahu. Mummy grab lah untuk baby." + end card (over A front close-up)
    dict(name="comel", a=[(73.92, 75.90)], v=[(32.40, 34.38, 1, 1.0)]),
    dict(name="end", a=None, v=[(34.38, 35.98, 1, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "ini?": "ni?", "Okey": "Okay", "itu": "tu", "bayi": "baby",
       "memerkakkan": "memekakkan", "new": "newborn"}
# hand-checked words where Whisper drifted or misheard
OVERRIDE = {
    75.93: [dict(s=s, e=e, w=w) for w, s, e in [
        ("Lelaki", 75.95, 76.40), ("perempuan", 76.45, 76.84), ("boleh", 76.84, 76.99), ("pakai.", 76.99, 77.30)]],
}
# Whisper timings that fall inside a kept clip but whose audio was cut
DROP = [(55.70, 55.95)]   # "born" (merged into "newborn")
HILITE = {"BABY", "MUMMY", "TOPI", "MATERIAL", "STRETCHABLE", "TELINGA", "SELESA", "LELAKI", "NEWBORN", "SETAHUN",
          "SMILE", "SEDAP", "LEMBUT", "BELAKANG", "DEPAN", "WARNA", "MACAM-MACAM", "LAKI", "PEREMPUAN",
          "BEG", "KUNING", "COMEL", "GRAB", "TARIK"}


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
    merged = []
    for w in out:
        if merged and w["w"].startswith("-") and w["clip"] == merged[-1]["clip"]:
            merged[-1] = dict(merged[-1], w=merged[-1]["w"].rstrip(",.") + w["w"], e=w["e"])
        else:
            merged.append(w)
    return merged


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
Style: Cap,Fredoka,58,&H00FFFFFF,&H000000FF,&H0038242A,&H6438242A,-1,0,0,0,100,100,0,0,1,5,3,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Label,Fredoka,62,&H0038242A,&H000000FF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,3,16,0,5,40,40,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,&H0038242A,&H6438242A,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# palette for a black baby beanie with a smiley patch: plum-charcoal ink, baby blue, peach, smiley yellow, mint
INK = "&H0038242A&"      # #2A2438  (ASS colours are BGR)
SKY = "&H00FFD38F&"      # #8FD3FF
PEACH = "&H008AB3FF&"    # #FFB38A
YELLOW = "&H004DD8FF&"   # #FFD84D
MINT = "&H00C4E79B&"     # #9BE7C4
CORAL = "&H006B6BFF&"    # #FF6B6B
WHITE = "&H00FFFFFF&"
ACC = YELLOW
KEY = SKY


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


def label(t0, t1, text, y=200, col=INK, box=SKY, hi=WHITE, rot=-3, layer=5, x=CX, size=62):
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
              rf"{{\an7\pos(0,0)\c{YELLOW}\fscx0\t(0,{int(TOTAL * 1000)},\fscx100)\p1}}m 0 0 l {W} 0 {W} 8 0 8{{\p0}}")

    def lab(s0, s1, text, sound="pop", vol=0.5, **kw):
        ev.append(label(tl(s0), tl(s1), text, **kw))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def stk(em, s0, s1, x, y, size=100):
        stickers.append((em, tl(s0), tl(s1), x, y, size))

    def bstk(em, t0, t1, x, y, size=100):
        stickers.append((em, t0, t1, x, y, size))

    SL, SR, SY = 85, 560, 315   # labels sit at the top (y 200), above the hat; stickers just below-right

    # ---- HOOK: call-out to mums -> newborn to one year
    lab(38.00, 40.66, "MUMMY YANG ADA *BABY*!", col=INK, box=YELLOW, hi=CORAL, rot=-3, size=70, sound="bloop", vol=0.5)
    stk("👶", 38.10, 40.66, SR, SY, 110)
    ev.append(flash(tl(54.25), d=0.25))
    lab(54.27, 55.98, "PAKAI DARI *NEWBORN*", col=WHITE, box=CORAL, hi=YELLOW, rot=3, size=70, sound="sparkle", vol=0.4)
    stk("🍼", 54.36, 55.98, SR, SY, 110)
    lab(56.02, 57.50, "SAMPAI *SETAHUN*!", col=INK, box=SKY, hi=WHITE, rot=-2, size=76, sound="ding", vol=0.35)
    stk("🎂", 56.06, 57.50, SR, SY, 110)

    # ---- unboxing (A, sped up, no voice)
    b = BT["unbox"]
    ev.append(f"Dialogue: 6,{ts(b['t0'])},{ts(b['t0'] + b['dur'])},Small,,0,0,0,,"
              rf"{{\an7\pos({SAFE_L},{SAFE_T + 20})\c{YELLOW}}}>> x2.5")
    ev.append(label(b["t0"] + 0.1, b["t0"] + b["dur"], "*TOPI* BABY", col=INK, box=PEACH, hi=WHITE, y=560, rot=-3,
                    size=78))
    bstk("🧢", b["t0"] + 0.15, b["t0"] + b["dur"], SR, 470, 100)
    sfx += [("swish", b["t0"] - 0.05, 0.45), ("pop", b["t0"] + 0.1, 0.45), ("zip", b["t0"] + 0.8, 0.3)]

    # ---- material
    lab(41.00, 43.74, "MATERIAL *STRETCHABLE*", rot=2, sound="whoosh", vol=0.4)
    stk("🧶", 41.04, 43.74, SR, SY, 100)
    lab(44.10, 45.45, "BILA *BABY* PAKAI", col=INK, box=PEACH, hi=WHITE, rot=-2)
    lab(45.50, 47.30, "*TELINGA* SELESA", col=INK, box=MINT, hi=WHITE, rot=2)
    stk("👂", 45.54, 47.30, SR, SY, 100)
    lab(47.75, 49.40, "*BABY* SELESA", col=INK, box=YELLOW, hi=CORAL, rot=-2, sound="swish", vol=0.4)
    stk("😊", 47.79, 49.40, SR, SY, 100)
    lab(49.69, 52.18, "BABY TAK *TARIK*!", rot=2)
    stk("🙅", 49.73, 52.18, SR, SY, 100)

    # ---- smile patch
    ev.append(flash(tl(61.45), d=0.25))
    lab(58.72, 61.40, "ADA *PATCH* KAT SINI", col=INK, box=PEACH, hi=WHITE, rot=-2)
    lab(61.47, 62.40, "*SMILE*!", col=INK, box=YELLOW, hi=CORAL, rot=3, size=84, sound="sparkle", vol=0.4)
    stk("🙂", 61.50, 62.40, SR, SY, 120)

    # ---- feel, back / front, colours
    lab(63.05, 65.45, "SEDAP & *SELESA*", col=INK, box=MINT, hi=WHITE, rot=2, sound="whoosh", vol=0.4)
    stk("☁️", 63.09, 65.45, SR, SY, 100)
    lab(65.50, 67.22, "*LEMBUT* + STRETCH", rot=-2)
    stk("🧸", 65.54, 67.22, SR, SY, 100)
    lab(67.25, 68.65, "*BELAKANG*", col=INK, box=PEACH, hi=WHITE, rot=2)
    stk("🔄", 67.29, 68.65, SR, SY, 90)
    lab(68.71, 69.92, "*DEPAN*", col=INK, box=YELLOW, hi=CORAL, rot=-2)
    lab(69.99, 71.42, "MACAM-MACAM *WARNA*", col=WHITE, box=CORAL, hi=YELLOW, rot=2, sound="sparkle", vol=0.35)
    stk("🌈", 70.03, 71.42, SR, SY, 100)

    # ---- unisex + CTA
    lab(75.96, 77.40, "*LELAKI* & *PEREMPUAN*", col=INK, box=SKY, hi=WHITE, rot=-2, sound="pop", vol=0.45)
    stk("👦", 76.00, 77.40, SL + 20, SY, 90)
    stk("👧", 76.00, 77.40, SR, SY, 90)
    lab(71.50, 73.65, "TENGOK *BEG KUNING*", col=INK, box=YELLOW, hi=CORAL, rot=2, sound="ding", vol=0.35)
    stk("🛒", 71.54, 73.65, SR, SY, 100)

    # ---- end card (inside the safe area), from "Comel tahu. Mummy grab lah untuk baby."
    e0 = BT["comel"]["t0"]
    ev.append(f"Dialogue: 8,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{INK}\1a&HFF&\t(0,250,\1a&H60&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    ev.append(label(e0 + 0.05, TOTAL, "*TOPI* BABY", col=INK, box=YELLOW, hi=CORAL, y=430, rot=-3, layer=9,
                    size=70))
    ev.append(label(e0 + 0.3, TOTAL, "LEMBUT • STRETCH • COMEL", col=INK, box=WHITE, hi=CORAL, y=540, rot=2,
                    layer=9, size=46))
    ev.append(label(e0 + 0.6, TOTAL, "*NEWBORN* - 1 TAHUN", col=INK, box=SKY, hi=WHITE, y=655, rot=-2,
                    layer=9, size=50))
    ev.append(label(e0 + 0.9, TOTAL, "TEKAN BEG KUNING", col=INK, box=YELLOW, y=775, rot=2, layer=9, size=58))
    bstk("🧢", e0 + 0.1, TOTAL, SR, 350, 100)
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
