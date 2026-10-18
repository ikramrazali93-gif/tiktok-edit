#!/usr/bin/env python3
"""Edit for the kids arm + chest float (puddle jumper style) TikTok video.

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
    # HOOK (problem -> solution, J-cut over the monster close-ups at 64s):
    # "Kalau pakai vest tu, dia akan macam melayang, nak terbalik." + "Dia boleh kawal badan dia sendiri."
    dict(name="hook", a=[(52.95, 57.99), (59.78, 61.50)], v=[(64.00, 67.38, 1, 1.0), (67.38, 70.76, 1, 1.1)]),
    # "Okay ni pelampung, pelampung tangan." + "Pelampung apa tu? Yang sekali dengan badan juga tu."
    dict(name="intro", a="same", v=[(0.88, 4.25, 1, 1.0), (6.88, 10.28, 1, 1.1)]),
    dict(name="unbox", a=None, v=[(10.30, 20.00, 3.0, 1.0)]),
    # "Ini bahagian dada dia. Ini bahagian tangan dia."
    dict(name="bahagian", a="same", v=[(22.18, 24.08, 1, 1.0), (24.62, 27.45, 1, 1.1)]),
    # "Okay ni letak dekat sini kan, lepas tu ni pakai dekat tangan."
    dict(name="pakai", a="same", v=[(29.48, 33.62, 1, 1.0)]),
    # "Jadi anak kita, dia terapung lah, nak pergi mandi kolam ke, mandi pantai ke."
    dict(name="apung", a="same", v=[(33.68, 38.56, 1, 1.1)]),
    # "Ni murah pun murah, jimat duit. Tak payah beli mahal-mahal sangat."
    dict(name="murah", a="same", v=[(39.15, 43.25, 1, 1.0)]),
    # "Nak pergi snorkeling ke apa ke, anak sesuai pakai ni. Dia akan balance badan dia."
    dict(name="snorkel", a="same", v=[(43.62, 47.33, 1, 1.1)]),
    # "Dia tak akan tergolek-golek, tak akan berpusing-pusing."
    dict(name="stabil", a="same", v=[(48.00, 52.80, 1, 1.0)]),
    # "Dia boleh macam terapung elok lah."
    dict(name="elok", a="same", v=[(61.76, 63.95, 1, 1.12)]),
    # thumbs up
    dict(name="end", a=None, v=[(70.80, 73.40, 1, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "Okey": "Okay", "dadau": "dada", "snowcling": "snorkeling", "kawai": "kawal",
       "tergolet": "tergolek", "-tergolet": "-golek", "-berpusing": "-pusing", "eloklah": "elok lah"}
# hand-checked words where Whisper drifted or misheard
OVERRIDE = {
    33.68: [dict(s=s, e=e, w=w) for w, s, e in [
        ("Jadi", 33.72, 33.88), ("anak", 33.88, 34.12), ("kita,", 34.12, 34.80), ("dia", 34.96, 35.08),
        ("terapung", 35.08, 35.58), ("lah.", 35.58, 35.90), ("Nak", 35.94, 36.14), ("pergi", 36.14, 36.46),
        ("mandi", 36.46, 37.00), ("kolam", 37.00, 37.46), ("ke,", 37.46, 37.60), ("mandi", 37.60, 37.86),
        ("pantai", 37.86, 38.38), ("ke.", 38.38, 38.54)]],
    48.00: [dict(s=s, e=e, w=w) for w, s, e in [
        ("Dia", 48.06, 48.80), ("tak", 48.88, 49.18), ("akan", 49.20, 49.80), ("tergolek-golek,", 49.82, 51.38),
        ("tak", 51.44, 51.54), ("akan", 51.54, 51.66), ("berpusing-pusing.", 51.66, 52.78)]],
}
DROP = []
HILITE = {"PELAMPUNG", "TANGAN", "BADAN", "DADA", "TERAPUNG", "KOLAM", "PANTAI", "MURAH", "JIMAT", "DUIT",
          "SNORKELING", "BALANCE", "TERGOLEK-GOLEK", "BERPUSING-PUSING", "VEST", "MELAYANG", "TERBALIK", "KAWAL",
          "SENDIRI", "ELOK"}


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
Style: Cap,Fredoka,58,&H00FFFFFF,&H000000FF,&H00782A1E,&H64782A1E,-1,0,0,0,100,100,0,0,1,5,3,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Label,Fredoka,62,&H00782A1E,&H000000FF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,3,16,0,5,40,40,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,&H00782A1E,&H64782A1E,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# palette from the float: monster navy text, turquoise body, yellow headphones, coral for "danger"
MNAVY = "&H00782A1E&"    # #1E2A78  (ASS colours are BGR)
TURQ = "&H00C8C81E&"     # #1EC8C8
YELLOW = "&H003FD2FF&"   # #FFD23F
CORAL = "&H005A5AFF&"    # #FF5A5A
DTEAL = "&H009A9A0E&"    # #0E9A9A (readable teal on white)
WHITE = "&H00FFFFFF&"
ACC = YELLOW
KEY = TURQ


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


def label(t0, t1, text, y=760, col=MNAVY, box=WHITE, hi=DTEAL, rot=-3, layer=5, x=CX, size=62):
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

    # ---- HOOK: vest problem -> this float
    lab(53.00, 55.10, "PAKAI *VEST*?", col=WHITE, box=CORAL, hi=YELLOW, rot=-3, size=74, sound="bloop", vol=0.5)
    stk("🦺", 53.04, 55.10, SR, SY, 110)
    lab(55.12, 57.99, "BUDAK *TERBALIK*!", col=WHITE, box=CORAL, hi=YELLOW, rot=3, size=70, sound="impact", vol=0.35)
    stk("😰", 55.16, 57.99, SR, SY, 110)
    ev.append(flash(tl(59.78), d=0.25))
    lab(59.80, 61.50, "YANG NI *KAWAL BADAN*", col=MNAVY, box=YELLOW, hi=WHITE, rot=-2, sound="ding", vol=0.4)
    stk("✅", 59.84, 61.50, SR, SY, 100)

    # ---- intro
    lab(1.10, 4.25, "*PELAMPUNG* TANGAN", col=MNAVY, box=TURQ, hi=WHITE, rot=-2, sound="whoosh", vol=0.4)
    stk("🏊", 1.14, 4.25, SR, SY, 100)
    lab(7.48, 10.28, "SEKALI DENGAN *BADAN*", rot=2)
    stk("👕", 7.52, 10.28, SR, SY, 100)
    b = BT["unbox"]
    ev.append(f"Dialogue: 6,{ts(b['t0'])},{ts(b['t0'] + b['dur'])},Small,,0,0,0,,"
              rf"{{\an7\pos({SAFE_L},{SAFE_T + 20})\c{YELLOW}}}>> x3")
    sfx += [("swish", b["t0"] - 0.05, 0.45), ("pop", b["t0"] + 1.6, 0.4)]

    # ---- parts
    lab(22.24, 24.08, "BAHAGIAN *DADA*", rot=-2)
    stk("👉", 22.28, 24.08, SL, 640, 90)
    lab(24.66, 27.45, "BAHAGIAN *TANGAN*", rot=2)
    stk("💪", 24.70, 27.45, SR, SY, 100)
    lab(30.18, 31.50, "LETAK KAT *DADA*", col=MNAVY, box=TURQ, hi=WHITE, rot=-3)
    lab(31.70, 33.62, "PAKAI KAT *TANGAN*", col=MNAVY, box=TURQ, hi=WHITE, rot=3)

    # ---- benefit
    lab(35.08, 35.90, "*TERAPUNG*!", col=MNAVY, box=YELLOW, hi=WHITE, rot=-3, size=78, sound="bloop", vol=0.5)
    stk("🛟", 35.12, 35.90, SR, SY, 110)
    lab(36.46, 37.60, "MANDI *KOLAM*", rot=2)
    stk("🏊", 36.50, 37.60, SR, SY, 100)
    lab(37.62, 38.56, "MANDI *PANTAI*", rot=-2)
    stk("🏖️", 37.66, 38.56, SR, SY, 100)
    lab(39.20, 40.46, "*MURAH* PUN MURAH", col=MNAVY, box=YELLOW, hi=WHITE, rot=3, sound="kaching", vol=0.35)
    stk("💸", 39.24, 40.46, SR, SY, 100)
    lab(40.48, 43.25, "*JIMAT DUIT*!", rot=-2, size=72)
    lab(43.70, 46.26, "SESUAI *SNORKELING*", col=WHITE, box=TURQ, hi=MNAVY, rot=2)
    stk("🤿", 43.74, 46.26, SR, SY, 100)
    lab(46.28, 47.33, "*BALANCE* BADAN", rot=-3, sound="ding", vol=0.35)
    stk("⚖️", 46.32, 47.33, SR, SY, 90)
    lab(48.88, 51.40, "TAK *TERGOLEK*", col=MNAVY, box=TURQ, hi=WHITE, rot=2)
    lab(51.44, 52.80, "TAK *BERPUSING*", col=MNAVY, box=TURQ, hi=WHITE, rot=-2)
    stk("👍", 48.92, 52.80, SR, SY, 100)
    lab(62.10, 63.95, "TERAPUNG *ELOK*", col=MNAVY, box=YELLOW, hi=WHITE, rot=3, sound="sparkle", vol=0.3)
    stk("🌊", 62.14, 63.95, SR, SY, 100)

    # ---- end card (inside the safe area)
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 8,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{MNAVY}\1a&HFF&\t(0,250,\1a&H60&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    ev.append(label(e0 + 0.05, TOTAL, "*PELAMPUNG* BUDAK", y=430, rot=-3, layer=9, size=66))
    ev.append(label(e0 + 0.3, TOTAL, "TANGAN + DADA • TAK TERBALIK", col=MNAVY, box=TURQ, hi=WHITE, y=540, rot=2,
                    layer=9, size=42))
    ev.append(label(e0 + 0.6, TOTAL, "TAG MAK *NAK KE PANTAI*!", col=WHITE, box=CORAL, hi=YELLOW, y=655, rot=-2,
                    layer=9, size=48))
    ev.append(label(e0 + 0.9, TOTAL, "TEKAN BEG KUNING", col=MNAVY, box=YELLOW, y=775, rot=2, layer=9, size=58))
    bstk("🛟", e0 + 0.1, TOTAL, SR, 350, 100)
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
