#!/usr/bin/env python3
"""Preview edit for the 2-in-1 bantal/selimut/beg TikTok video.

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
    # HOOK: "Dua dalam satu - bantal, dan ada selimut sekali, dan dia boleh galas sebagai beg"
    # voice from 8.40-14.42 (filler 9.13-10.40 removed), visuals cut to each function
    dict(name="hook", a=[(8.40, 9.13), (10.40, 14.42)],
         v=[(41.10, 42.57, 1, 1.08), (63.90, 65.10, 1, 1.0), (27.40, 29.48, 1, 1.05)]),
    # "Okay jom kita unboxing lagi." + "yang ni memang ramai orang borong..." (stutter x3 removed)
    dict(name="intro", a="same", v=[(0.05, 1.18, 1, 1.0), (4.12, 8.22, 1, 1.12)]),
    dict(name="unbox", a=None, v=[(8.30, 14.50, 2.2, 1.0)]),
    dict(name="hampa", a="same", v=[(14.62, 15.32, 1, 1.0)]),
    dict(name="ramp1", a=None, v=[(15.32, 19.30, 3.0, 1.0)]),
    dict(name="galas", a="same", v=[(19.30, 21.25, 1, 1.1)]),
    # cut: 21.25-29.15 pose silence + "sangat-sangat function" + "dua dalam satu ada selimut" (repeats)
    dict(name="pilihan", a="same", v=[(29.15, 34.45, 1, 1.0)]),
    # cut: "Dia ada," false start
    dict(name="v2a", a="same", v=[(35.30, 45.25, 1, 1.12)]),
    # cut: "ni saya tunjuk hat besar dulu" + 2.5s fumble
    dict(name="zip", a="same", v=[(49.80, 51.35, 1, 1.0)]),
    dict(name="ramp2", a=None, v=[(51.35, 56.50, 2.5, 1.0)]),
    dict(name="reveal", a="same", v=[(56.50, 60.10, 1, 1.0)]),
    dict(name="size", a="same", v=[(60.55, 66.40, 1, 1.0)]),
    dict(name="travel", a="same", v=[(66.40, 70.30, 1, 1.1)]),
    dict(name="jahit", a="same", v=[(70.90, 74.80, 1, 1.0)]),
    dict(name="bukatutup", a="same", v=[(75.30, 79.40, 1, 1.12)]),
    # cut: "lipat balik, tutup zip" (repeat) + "nanti saya masukkan dalam video" (note to editor)
    dict(name="v2b", a="same", v=[(88.86, 93.95, 1, 1.0)]),
    # cut: "yang tu selimut dia asing" + "okay selimut asing macam ni" (repeat)
    dict(name="duapcs", a="same", v=[(97.95, 102.15, 1, 1.1)]),
    dict(name="cta", a="same", v=[(102.50, 108.15, 1, 1.0)]),
    dict(name="end", a=None, v=[(108.15, 109.80, 1, 1.0)]),
]

FIX = {"bantai": "bantal", "galah": "galas", "bag": "beg", "zit": "zip", "-zit": "-zip",
       "bar": "bas", "retapi": "keretapi", "bagku": "beg"}
# re-checked word timings (second Whisper pass) where the first pass drifted
OVERRIDE = {4.12: [dict(s=s, e=e, w=w) for w, s, e in [
    ("yang", 4.20, 4.45), ("ni", 4.45, 4.78), ("memang", 4.80, 5.02), ("ramai", 5.02, 5.38),
    ("orang", 5.38, 5.56), ("borong.", 5.56, 6.27), ("Sebab", 6.30, 6.54), ("dia", 6.54, 6.74),
    ("sangat", 6.74, 6.94), ("-sangat", 6.94, 7.18), ("function", 7.18, 7.68), ("tau.", 7.68, 7.90)]]}
HILITE = {"BANTAL", "SELIMUT", "BEG", "GALAS", "V2", "BORONG", "FUNCTION", "160CM", "100CM",
          "BERJAHIT", "TRAVEL", "ASING", "BERCANTUM", "TERPISAH", "ZIP", "BESAR", "PILIHAN"}


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
            if c["s"] - 0.05 <= w["s"] <= c["e"] - 0.08:
                txt = w["w"].strip()
                core = txt.strip(",.")
                txt = txt.replace(core, FIX.get(core, FIX.get(core.lower(), core)))
                s = c["t"] + max(w["s"], c["s"]) - c["s"]
                e = c["t"] + min(w["e"], c["e"]) - c["s"]
                out.append(dict(w=txt, s=s, e=e, clip=id(c)))
    # whisper put "bantal" (10.30) just before the hook's second clip; re-add it
    if not any(w["w"].startswith("bantal") for w in out if w["s"] < 3):
        t0 = BT["hook"]["t0"] + (9.13 - 8.40)
        out.append(dict(w="bantal,", s=t0 + 0.08, e=t0 + 0.72, clip=-1))
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
Style: Cap,Inter Display Black,58,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,5,3,2,70,110,330,1
Style: Label,Inter Display Black,64,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,3,14,0,5,40,40,0,1
Style: Title,Inter Display Black,62,&H0000E5FF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,6,4,8,40,40,150,1
Style: Small,Inter Display ExtraBold,40,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

YEL = "&H0000E5FF&"   # BGR
PINK = "&H00B469FF&"
GREEN = "&H0050D050&"
RED = "&H003C3CF0&"


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
                    parts.append(r"{\c%s\fscx112\fscy112}%s{\r}" % (YEL, t))
                elif t.strip("-") in HILITE:
                    parts.append(r"{\c%s}%s{\r}" % (YEL, t))
                else:
                    parts.append(t)
            pop = r"{\fscx85\fscy85\t(0,90,\fscx100\fscy100)}" if j == 0 else ""
            ev.append(f"Dialogue: 2,{ts(ws)},{ts(we)},Cap,,0,0,0,,{pop}" + " ".join(parts))
    return ev


def label(t0, t1, text, y=470, col="&H00FFFFFF&", box="&H00000000&", style="Label", rot=-3, layer=5):
    """Pop-in boxed label with a slight tilt; slides/fades out."""
    return (f"Dialogue: {layer},{ts(t0)},{ts(t1)},{style},,0,0,0,,"
            rf"{{\an5\pos({W // 2},{y})\frz{rot}\c{col}\3c{box}\fscx0\fscy0"
            rf"\t(0,140,\fscx118\fscy118)\t(140,240,\fscx100\fscy100)\fad(0,150)}}{text}")


def flash(t0, d=0.35, layer=9):
    return (f"Dialogue: {layer},{ts(t0)},{ts(t0 + d)},Shape,,0,0,0,,"
            rf"{{\an7\pos(0,0)\c&HFFFFFF&\1a&H20&\fad(0,{int(d * 1000) - 40})\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")


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
    hk = BT["hook"]["t0"]
    # progress bar (retention)
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{YEL}\fscx0\t(0,{int(TOTAL * 1000)},\fscx100)\p1}}m 0 0 l {W} 0 {W} 8 0 8{{\p0}}")

    # ---- HOOK
    ev.append(f"Dialogue: 7,{ts(0)},{ts(hk + 4.75)},Title,,0,0,0,,"
              r"{\fscx60\fscy60\t(0,180,\fscx105\fscy105)\t(180,260,\fscx100\fscy100)}"
              r"1 BENDA, {\c&HFFFFFF&}3 FUNGSI!")
    beats = [(0.0, 1.47, "BANTAL", "😴"), (1.47, 2.67, "SELIMUT", "🛌"), (2.67, 4.75, "BEG GALAS", "🎒")]
    for i, (a, b, txt, em) in enumerate(beats):
        ev.append(label(hk + a + 0.05, hk + b, f"{i + 1}. {txt}", y=640, box=YEL.replace("E5FF", "E5FF"),
                        col="&H00000000&", rot=-4 + 4 * i))
        stickers.append((em, hk + a + 0.12, hk + b, 560, 560, 110))
        stickers.append(("✅", hk + a + 0.30, hk + b, 160, 560, 80))
        sfx += [("pop", hk + a + 0.05, 0.55), ("whoosh", hk + a - 0.15, 0.35)]
    sfx.append(("swish", hk + 4.6, 0.5))

    # ---- INTRO
    ev.append(label(tl(0.7), tl(1.18) + 0.2, "UNBOXING!", y=470, rot=3))
    stickers.append(("📦", tl(0.7), tl(1.18) + 0.2, 560, 400, 100))
    sfx.append(("pop", tl(0.7), 0.5))
    ev.append(label(tl(5.5), tl(8.2), r"RAMAI {\c" + YEL + r"}BORONG!", y=470, rot=-3))
    stickers.append(("🔥", tl(5.5), tl(8.2), 590, 400, 100))
    sfx.append(("ding", tl(5.5), 0.35))

    # ---- speed ramps
    for nm, tag in [("unbox", ">> x2"), ("ramp1", ">> x3"), ("ramp2", ">> x2.5")]:
        b = BT[nm]
        ev.append(f"Dialogue: 6,{ts(b['t0'])},{ts(b['t0'] + b['dur'])},Small,,0,0,0,,"
                  rf"{{\an9\pos({W - 30},70)\c{YEL}}}{tag}")
        sfx.append(("swish", b["t0"] - 0.05, 0.45))
    sfx.append(("pop", BT["unbox"]["t0"] + 2.3, 0.4))   # pillow out of plastic
    sfx.append(("zip", BT["ramp2"]["t0"] + 0.2, 0.6))
    sfx.append(("zip", BT["ramp2"]["t0"] + 0.9, 0.6))

    # ---- galas
    ev.append(label(tl(19.5), tl(21.2), "BOLEH GALAS!", y=470, rot=-3))
    stickers.append(("🎒", tl(19.5), tl(21.2), 590, 380, 100))
    sfx.append(("pop", tl(19.5), 0.5))

    # ---- 2 pilihan (her peace sign lands here)
    ev.append(label(tl(29.6), tl(31.3), r"{\c" + YEL + r"}2 {\c&HFFFFFF&}PILIHAN SELIMUT", y=470, rot=3))
    stickers.append(("✌️", tl(29.6), tl(31.3), 600, 380, 100))
    sfx.append(("pop", tl(29.6), 0.5))
    ev.append(label(tl(33.0), tl(34.45), "1. BIASA", y=470, rot=-2))
    sfx.append(("click", tl(33.0), 0.5))

    # ---- biasa vs V2
    ev.append(label(tl(36.3), tl(41.4), r"BIASA {\c" + YEL + r"}VS{\c&HFFFFFF&} V2", y=470, rot=0))
    sfx.append(("whoosh", tl(36.2), 0.4))
    ev += chip(tl(38.2), tl(41.4), 200, 610, "&H00285A8B&", "BIASA")
    ev += chip(tl(40.1), tl(41.4), 520, 610, "&H00285A8B&", "V2")
    sfx += [("pop", tl(38.2), 0.4), ("pop", tl(40.1), 0.4)]
    ev.append(label(tl(41.7), tl(43.5), r"LUAR {\c" + YEL + r"}SAMA", y=470, rot=-3))
    ev.append(label(tl(43.6), tl(45.25), r"DALAM {\c" + YEL + r"}BEZA!", y=470, rot=3))
    stickers.append(("👀", tl(43.6), tl(45.25), 600, 390, 90))
    sfx += [("click", tl(41.7), 0.5), ("pop", tl(43.6), 0.5)]

    # ---- zip + reveal
    ev.append(label(tl(49.85), BT["ramp2"]["t0"] + BT["ramp2"]["dur"], "BUKA ZIP", y=470, rot=-3))
    stickers.append(("🤐", tl(49.85), BT["ramp2"]["t0"] + BT["ramp2"]["dur"], 560, 390, 90))
    sfx.append(("riser", tl(56.55), 0.35))
    rv = tl(57.85)
    ev.append(flash(rv))
    ev.append(label(rv + 0.05, tl(60.1), "TADAAA!", y=470, rot=-4))
    stickers.append(("✨", rv + 0.05, tl(60.1), 140, 380, 100))
    stickers.append(("✨", rv + 0.25, tl(60.1), 590, 400, 80))
    sfx += [("impact", rv, 0.6), ("sparkle", rv + 0.1, 0.4)]

    # ---- size / travel
    ev.append(label(tl(61.3), tl(64.6), r"{\c" + YEL + r"}160cm {\c&HFFFFFF&}x {\c" + YEL + r"}100cm", y=470, rot=0))
    stickers.append(("📏", tl(61.3), tl(64.6), 620, 380, 90))
    sfx += [("click", tl(61.3), 0.5), ("click", tl(63.0), 0.5)]
    ev.append(label(tl(64.75), tl(66.4), "BESAR!", y=470, rot=-4))
    sfx.append(("pop", tl(64.75), 0.5))
    for src, em, x in [(67.9, "✈️", 170), (69.2, "🚌", 360), (69.95, "🚆", 550)]:
        stickers.append((em, tl(src), tl(70.3), x, 470, 110))
        sfx.append(("pop", tl(src), 0.5))
    ev.append(label(tl(67.4), tl(70.3), "BAWA TRAVEL", y=600, rot=-2, col="&H00000000&", box=YEL))

    # ---- berjahit / buka-tutup
    ev.append(label(tl(72.4), tl(74.8), r"BERJAHIT {\c" + YEL + r"}CANTUM", y=470, rot=-3))
    stickers.append(("🧵", tl(72.4), tl(74.8), 610, 380, 90))
    sfx.append(("pop", tl(72.4), 0.5))
    ev.append(label(tl(75.5), tl(77.05), r"BUKA = {\c" + YEL + r"}SELIMUT", y=470, rot=-2))
    ev.append(label(tl(77.1), tl(79.4), r"TUTUP = {\c" + YEL + r"}BANTAL", y=470, rot=2))
    sfx += [("whoosh", tl(75.45), 0.35), ("whoosh", tl(77.05), 0.35)]

    # ---- V2 separate blanket
    ev.append(label(tl(89.2), tl(93.95), r"{\c" + YEL + r"}V2{\c&HFFFFFF&} = SELIMUT ASING", y=470, rot=-2))
    sfx.append(("whoosh", tl(89.1), 0.4))
    for src, x, col, nm in [(90.9, 160, "&H00285A8B&", "BROWN"), (92.2, 360, "&H0040D8FF&", "YELLOW"),
                            (93.2, 560, "&H00C1B6FF&", "PINK")]:
        ev += chip(tl(src), tl(93.95), x, 620, col, nm)
        sfx.append(("pop", tl(src), 0.45))
    ev.append(label(tl(98.9), tl(102.15), r"GUNA {\c" + YEL + r"}2 SERENTAK", y=470, rot=2))
    stickers.append(("🙌", tl(98.9), tl(102.15), 610, 380, 90))
    sfx.append(("pop", tl(98.9), 0.5))

    # ---- CTA
    ev.append(label(tl(102.8), tl(104.3), "KORANG PILIH!", y=470, rot=-3))
    stickers.append(("🤔", tl(102.8), tl(104.3), 600, 390, 90))
    ev.append(label(tl(104.4), tl(108.15), r"{\c" + YEL + r"}BERCANTUM", y=420, rot=-3))
    ev.append(f"Dialogue: 6,{ts(tl(105.2))},{ts(tl(108.15))},Small,,0,0,0,,"
              rf"{{\an5\pos({W // 2},510)\fad(120,120)}}ATAU")
    ev.append(label(tl(106.6), tl(108.15), r"{\c" + YEL + r"}TERPISAH", y=600, rot=3))
    stickers.append(("🔗", tl(104.4), tl(108.15), 610, 350, 80))
    stickers.append(("✂️", tl(106.6), tl(108.15), 110, 640, 80))
    sfx += [("pop", tl(104.4), 0.5), ("pop", tl(106.6), 0.5)]

    # ---- end card
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 8,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c&H000000&\1a&HFF&\t(0,250,\1a&H60&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    ev.append(label(e0 + 0.1, TOTAL, "KOMEN PILIHAN KORANG!", y=520, rot=-2, layer=9))
    ev.append(label(e0 + 0.45, TOTAL, r"TEKAN {\c&H00000000&}BEG KUNING", y=680, rot=2,
                    col="&H00000000&", box=YEL, layer=9))
    stickers.append(("👇", e0 + 0.15, TOTAL, 600, 430, 90))
    stickers.append(("🛒", e0 + 0.5, TOTAL, 110, 760, 100))
    sfx += [("whoosh", e0 - 0.1, 0.4), ("kaching", e0 + 0.45, 0.45)]
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
