#!/usr/bin/env python3
"""Edit for the GoSmell natural deodorant spray TikTok video.

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
VOICE_LUFS = -11.5                  # v1 was -15; SFX levels are absolute and stay unchanged

# ---------------------------------------------------------------- EDL
# v: list of (src_in, src_out, speed, zoom)
# a: 'same' (follow v at speed 1), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK: pain point "biasa kalau kita balik jogging, mesti ketiak kita bau masam lah kan"
    # ("Baru balik jogging ni" dropped - it says jogging twice); punch-in on "bau masam"
    dict(name="hook", a="same", v=[(1.80, 4.45, 1, 1.06), (4.45, 6.20, 1, 1.22)]),
    # "Tapi guna GoSmell ni, smell pun go!" (0.7s pause removed; "dia go pergi okay" dropped)
    dict(name="punch", a="same", v=[(6.30, 6.90, 1, 1.0), (7.55, 10.28, 1, 1.12)]),
    # "Sebelum jogging ataupun lepas mandi hampa spray je, senang. Baru tu hampa nak jogging ke, hampa nak"
    dict(name="bila", a="same", v=[(13.25, 16.68, 1, 1.0), (16.68, 19.52, 1, 1.1)]),
    # cut 19.5-24.7: "...apa tu?" searching for the word
    dict(name="peluh", a="same", v=[(24.68, 26.03, 1, 1.0), (26.38, 27.55, 1, 1.15)]),
    # cut: "dia punya, setiap kali dia"; keep the mist shot
    dict(name="spray", a="same", v=[(30.99, 35.55, 1, 1.0)]),
    dict(name="kuman", a="same", v=[(36.10, 38.08, 1, 1.1), (38.68, 43.40, 1, 1.0), (43.40, 48.62, 1, 1.1)]),
    dict(name="beli", a="same", v=[(49.55, 54.15, 1, 1.0), (54.15, 58.30, 1, 1.12), (58.30, 61.25, 1, 1.0)]),
    dict(name="pack", a="same", v=[(61.72, 65.28, 1, 1.0), (65.88, 66.92, 1, 1.1)]),
    # bottles out of the pouch, sped up (speech here is "ini lime, just lime" - said again below)
    dict(name="unbox", a=None, v=[(66.92, 72.15, 2.5, 1.0)]),
    dict(name="bau", a="same", v=[(72.20, 76.92, 1, 1.0)]),
    # cut 76.9-84.3: "eh less lime, just lime, sebut ikut mana" + "bolehlah nak lagi, senang"
    dict(name="travel", a="same", v=[(84.30, 89.84, 1, 1.06)]),
    # cut "harga muka" (unclear) - end card over both bottles instead
    dict(name="end", a=None, v=[(89.95, 92.10, 1, 1.0)]),
]

FIX = {"kecil": "ketiak", "acem": "masam", "go": "Go", "smell": "Smell", "membas": "membasmi",
       "just": "Lust", "lock": "elok"}
# hand-checked words where Whisper drifted or misheard
OVERRIDE = {
    24.68: [dict(s=s, e=e, w=w) for w, s, e in [("berpeluh", 24.80, 25.32), ("-peluhan", 25.32, 25.88),
                                                ("ke,", 25.88, 26.00)]],
    84.30: [dict(s=s, e=e, w=w) for w, s, e in [
        ("Bawa", 85.00, 85.32), ("pergi", 85.32, 85.74), ("travel", 85.74, 86.22), ("ke,", 86.22, 86.42),
        ("senang.", 86.42, 86.84), ("Botol", 86.86, 87.10), ("dia", 87.10, 87.28), ("ni", 87.28, 87.60),
        ("90ml.", 87.60, 89.80)]],
}
DROP = [(55.70, 56.36)]   # unclear words: no caption rather than a wrong one
HILITE = {"KETIAK", "MASAM", "GO", "SMELL", "SPRAY", "SENANG", "JOGGING", "BERPELUH", "-PELUHAN", "PROBLEM",
          "KUMAN", "-KUMAN", "BAU", "KURANG", "FUNCTION", "SECURE", "MOON", "MELON", "LUST", "LIME",
          "TRAVEL", "90ML", "MEMBASMI", "LAGI"}


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
    out = []
    for c in ACLIPS:
        if "silence" in c:
            continue
        src = OVERRIDE.get(c["s"], words)
        for w in src:
            inside = c["s"] - 0.08 <= w["s"] <= c["e"] - 0.08
            straddle = c["s"] - 0.6 <= w["s"] < c["s"] and w["e"] > c["s"] + 0.15   # word mostly kept
            if (inside or straddle) and not any(d0 <= w["s"] < d1 for d0, d1 in DROP):
                txt = w["w"].strip()
                core = txt.strip(",.")
                txt = txt.replace(core, FIX.get(core, FIX.get(core.lower(), core)))
                s = c["t"] + max(w["s"], c["s"]) - c["s"]
                e = c["t"] + min(w["e"], c["e"]) - c["s"]
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
Style: Cap,Inter Display Black,58,&H00FFFFFF,&H000000FF,&H00520E2A,&H64520E2A,0,0,0,0,100,100,0,0,1,5,3,2,70,110,320,1
Style: Label,Inter Display Black,60,&H00520E2A,&H000000FF,&H00D1F3FF,&H00000000,0,0,0,0,100,100,0,0,3,14,0,5,40,40,0,1
Style: Small,Inter Display ExtraBold,38,&H00FFFFFF,&H000000FF,&H00520E2A,&H64520E2A,0,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# palette taken from the product + video: GoSmell orange / teal label stripes,
# cream bottle label, purple hijab & flowers
ORANGE = "&H001F7AFF&"   # #FF7A1F  (ASS colours are BGR)
TEAL = "&H00D6C61F&"     # #1FC6D6
CREAM = "&H00D1F3FF&"    # #FFF3D1
PURPLE = "&H00520E2A&"   # #2A0E52 deep
VIOLET = "&H00D92B6C&"   # #6C2BD9
WHITE = "&H00FFFFFF&"
ACC = ORANGE


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
                    parts.append(r"{\c%s}%s{\r}" % (TEAL, t))
                else:
                    parts.append(t)
            pop = r"{\fscx85\fscy85\t(0,90,\fscx100\fscy100)}" if j == 0 else ""
            ev.append(f"Dialogue: 2,{ts(ws)},{ts(we)},Cap,,0,0,0,,{pop}" + " ".join(parts))
    return ev


def label(t0, t1, text, y=720, col=PURPLE, box=CREAM, hi=ORANGE, rot=-3, layer=5, x=W // 2, size=None):
    """Pop-in boxed label with a slight tilt. *word* is drawn in the highlight colour."""
    parts = text.split("*")
    text = "".join(p if i % 2 == 0 else rf"{{\c{hi}}}{p}{{\c{col}}}" for i, p in enumerate(parts))
    fs = rf"\fs{size}" if size else ""
    return (f"Dialogue: {layer},{ts(t0)},{ts(t1)},Label,,0,0,0,,"
            rf"{{\an5\pos({x},{y})\frz{rot}{fs}\c{col}\3c{box}\fscx0\fscy0"
            rf"\t(0,140,\fscx118\fscy118)\t(140,240,\fscx100\fscy100)\fad(0,150)}}{text}")


def flash(t0, d=0.35, layer=9, col=CREAM):
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
    # progress bar (retention)
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{ORANGE}\fscx0\t(0,{int(TOTAL * 1000)},\fscx100)\p1}}m 0 0 l {W} 0 {W} 8 0 8{{\p0}}")

    def lab(s0, s1, text, sound="pop", vol=0.5, **kw):
        ev.append(label(tl(s0), tl(s1), text, **kw))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def stk(em, s0, s1, x, y, size=100):
        stickers.append((em, tl(s0), tl(s1), x, y, size))

    # ---- HOOK: pain point
    lab(1.80, 3.75, "LEPAS *JOGGING*...", rot=-3, sound="whoosh", vol=0.35)
    stk("🏃", 1.85, 3.75, 600, 630)
    lab(3.80, 4.45, "*KETIAK*...", rot=3, sound="click")
    lab(4.50, 6.20, "BAU *MASAM*?!", col=WHITE, box=VIOLET, rot=-4, size=72, sound="bloop", vol=0.6)
    stk("🤢", 4.55, 6.20, 600, 620, 120)
    stk("💦", 4.70, 6.20, 120, 640, 90)
    # ---- punch: product reveal
    t_go = tl(7.75)
    ev.append(flash(t_go - 0.05))
    sfx += [("impact", t_go - 0.05, 0.55), ("sparkle", t_go, 0.4)]
    lab(7.75, 9.20, "GUNA *GO*SMELL", sound=None, rot=-2, size=70)
    stk("🧴", 7.80, 9.20, 610, 620, 110)
    stk("✨", 7.95, 9.20, 110, 640, 90)
    lab(9.28, 10.28, "SMELL PUN *GO!*", box=TEAL, hi=WHITE, rot=3, size=72, sound="whoosh", vol=0.45)
    stk("💨", 9.60, 10.28, 600, 620, 110)

    # ---- when to use
    lab(13.52, 14.42, "SEBELUM *JOGGING*", rot=-3)
    lab(14.46, 15.12, "LEPAS *MANDI*", rot=3)
    stk("🚿", 14.46, 15.12, 600, 630)
    lab(15.14, 16.60, "SPRAY JE!", box=TEAL, hi=WHITE, rot=-2, sound=None)
    sfx.append(("spray", tl(15.25), 0.45))
    stk("🏃", 17.60, 19.50, 600, 640)
    lab(24.75, 26.03, "*BERPELUH*?", col=WHITE, box=VIOLET, rot=-3)
    stk("💦", 24.75, 26.03, 590, 630)
    lab(26.45, 27.55, "NO *PROBLEM!*", box=TEAL, hi=WHITE, rot=3, sound="ding", vol=0.35)
    stk("✅", 26.50, 27.55, 610, 630, 90)

    # ---- spray + scents
    sfx.append(("click", tl(31.55), 0.5))
    sfx.append(("spray", tl(32.30), 0.55))
    stk("💨", 32.35, 33.30, 300, 380, 120)
    lab(33.50, 35.55, "MACAM-MACAM *BAU*", rot=-2)
    stk("🌸", 33.55, 35.55, 615, 630, 90)

    # ---- why it works
    lab(36.40, 38.08, "SEBAB APA?", col=WHITE, box=VIOLET, rot=3, sound="pop")
    stk("🤔", 36.45, 38.08, 590, 630)
    lab(38.70, 41.40, "*MEMBASMI* KUMAN", rot=-2, sound="bloop", vol=0.5)
    stk("🦠", 38.75, 41.40, 600, 620, 100)
    stk("🚫", 39.00, 41.40, 120, 640, 80)
    lab(42.50, 43.38, "*PELUH*", rot=0)
    ev.append(label(tl(43.40), tl(44.66), "*PELUH* + *KUMAN*", rot=0))
    sfx.append(("pop", tl(43.40), 0.5))
    lab(44.70, 45.25, "= *BAU*!", col=WHITE, box=VIOLET, rot=-3, sound="bloop", vol=0.6, size=72)
    stk("💦", 42.55, 44.66, 120, 640, 80)
    stk("🦠", 43.45, 44.66, 600, 630, 90)
    stk("🤢", 44.75, 45.25, 600, 620, 110)
    lab(45.60, 47.20, "KUMAN *KURANG*", rot=-2)
    lab(47.24, 48.62, "BAU PUN *KURANG*", box=TEAL, hi=WHITE, rot=2, sound="ding", vol=0.35)
    stk("✅", 47.30, 48.62, 610, 630, 90)
    lab(51.18, 54.10, "INSYAALLAH BAU *KURANG*", rot=-2, size=52)
    stk("✨", 51.25, 54.10, 640, 630, 80)

    # ---- repeat buyer
    lab(54.22, 55.60, "SPRAY *GO*SMELL", rot=2, sound=None)
    sfx.append(("spray", tl(54.25), 0.4))
    lab(56.40, 58.28, "BELI 1, NAK BELI *LAGI!*", rot=-3, sound="pop")
    stk("🛒", 56.45, 58.28, 620, 620, 90)
    lab(59.28, 61.25, "SANGAT *FUNCTION*", box=TEAL, hi=WHITE, rot=3, sound="ding", vol=0.35)
    stk("💯", 59.35, 61.25, 610, 620, 100)

    # ---- packaging
    lab(62.20, 63.55, "PACKAGING *ELOK*", rot=-2)
    stk("📦", 62.25, 63.55, 620, 630, 90)
    lab(64.40, 66.92, "*SECURE*", box=TEAL, hi=WHITE, rot=3)
    stk("🔒", 64.45, 66.92, 520, 630, 90)
    b = BT["unbox"]
    ev.append(f"Dialogue: 6,{ts(b['t0'])},{ts(b['t0'] + b['dur'])},Small,,0,0,0,,"
              rf"{{\an9\pos({W - 30},70)\c{ORANGE}}}>> x2.5")
    sfx += [("swish", b["t0"] - 0.05, 0.45), ("pop", b["t0"] + 1.6, 0.4)]

    # ---- the two scents (chips match the label stripes)
    lab(72.25, 73.90, "NATURAL BASED *DEODORANT*", rot=0, size=46, sound="whoosh", vol=0.35)
    ev += chip(tl(73.96), tl(76.92), 200, 690, TEAL, "MOON MELON")
    stk("🍈", 74.00, 76.92, 200, 560, 80)
    sfx.append(("pop", tl(73.96), 0.45))
    ev += chip(tl(76.20), tl(76.92), 520, 690, ORANGE, "LUST LIME")
    stk("🍋", 76.22, 76.92, 520, 560, 80)
    sfx.append(("pop", tl(76.20), 0.45))

    # ---- travel / size
    lab(85.74, 87.55, "BAWA *TRAVEL* SENANG", rot=-2)
    stk("✈️", 85.80, 87.55, 620, 620, 90)
    lab(87.60, 89.84, "*90ML*", box=TEAL, hi=WHITE, rot=3, size=80, sound="click")
    stk("🧴", 87.65, 89.84, 500, 630, 90)

    # ---- end card
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 8,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{PURPLE}\1a&HFF&\t(0,250,\1a&H50&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    ev.append(label(e0 + 0.05, TOTAL, r"*MOON MELON*", box=CREAM, hi=TEAL, y=470, rot=-3, layer=9, size=64))
    ev.append(f"Dialogue: 9,{ts(e0 + 0.25)},{ts(TOTAL)},Small,,0,0,0,,"
              rf"{{\an5\pos({W // 2},560)\fad(120,0)}}ATAU")
    ev.append(label(e0 + 0.4, TOTAL, r"*LUST LIME*", box=CREAM, hi=ORANGE, y=650, rot=3, layer=9, size=64))
    ev.append(label(e0 + 0.75, TOTAL, "KOMEN PILIHAN KORANG!", col=WHITE, box=VIOLET, y=800, rot=-2, layer=9,
                    size=46))
    ev.append(label(e0 + 1.0, TOTAL, "TEKAN BEG KUNING", col=PURPLE, box=ORANGE, y=900, rot=2, layer=9, size=52))
    stickers.append(("🍈", e0 + 0.1, TOTAL, 600, 420, 90))
    stickers.append(("🍋", e0 + 0.45, TOTAL, 120, 600, 90))
    stickers.append(("👇", e0 + 0.8, TOTAL, 640, 760, 80))
    stickers.append(("🛒", e0 + 1.05, TOTAL, 90, 880, 90))
    sfx += [("whoosh", e0 - 0.1, 0.4), ("pop", e0 + 0.05, 0.45), ("pop", e0 + 0.4, 0.45),
            ("kaching", e0 + 1.0, 0.45)]
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
            frame.alpha_composite(im, (int(x * K - im.width / 2), int(y * K + bob - im.height / 2)))
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
