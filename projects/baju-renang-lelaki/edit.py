#!/usr/bin/env python3
"""Edit for the men's swim set (baju renang lelaki) TikTok video.

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
    # HOOK (moved from 58.3s): "Sesuai sangatlah untuk pakai pergi pantai, nak pergi bercuti, nak pergi pulau-pulau, kan?"
    #  J-cut over product shots: pants close-up, shorts, top held up
    dict(name="hook", a=[(58.32, 64.42)], v=[(37.90, 40.00, 1, 1.0), (26.20, 27.90, 1, 1.0), (61.10, 63.40, 1, 1.0)]),
    # unboxing, sped up (no speech)
    dict(name="buka", a=None, v=[(11.00, 18.50, 3, 1.0)]),
    # "Baju renang."  (J-cut onto her pulling the set out of the bag; unclear "ini lelaki ber..." cut)
    dict(name="intro", a=[(6.48, 8.12)], v=[(18.60, 20.24, 1, 1.0)]),
    # "Seluar pendek pun boleh. Seluar panjang pun ada."  (unclear "ini seluar dia..." before it cut)
    dict(name="seluar", a="same", v=[(26.38, 28.30, 1, 1.0), (28.78, 30.04, 1, 1.0)]),
    # "Boleh pakai seluar pendek kat rumah."
    dict(name="rumah", a="same", v=[(30.46, 31.66, 1, 1.06)]),
    # "Seluar panjang, jenis fit kan?"  (pause cut; J-cut onto the long pants held up)
    dict(name="fit", a=[(32.12, 33.00), (33.40, 34.44)], v=[(35.00, 36.92, 1, 1.0)]),
    # "Ni baju renang. Tangan panjang. Ni untuk lelaki."  (unclear "wih, kemas ni / oh macam ni betul" cut)
    dict(name="baju", a="same", v=[(41.55, 44.25, 1, 1.0), (44.58, 48.45, 1, 1.08)]),
    # "Kainnya lembut je."  (repeat + unclear "elok-elok / kemas" cut)
    dict(name="kain", a="same", v=[(53.28, 55.32, 1, 1.08)]),
    # holding the top up - end card (her closing line is not captioned)
    dict(name="end", a="same", v=[(65.70, 68.30, 1, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "senak": "seluar", "Senak": "Seluar", "Kayanya": "Kainnya"}
# hand-checked words (the voice is soft; Whisper drifted on several lines - re-transcribed per clip)
def _w(*ws):
    return [dict(w=w, s=a, e=b) for w, a, b in ws]


OVERRIDE = {
    58.32: _w(("Sesuai", 58.44, 58.92), ("sangatlah", 58.92, 59.42), ("untuk", 59.42, 59.54), ("pakai", 59.54, 59.74),
              ("pergi", 59.74, 59.94), ("pantai,", 59.94, 60.68), ("nak", 60.84, 60.88), ("pergi", 60.88, 61.00),
              ("bercuti,", 61.00, 62.04), ("nak", 62.30, 62.34), ("pergi", 62.34, 62.50), ("pulau-pulau,", 62.50, 63.38),
              ("kan?", 63.38, 64.30)),
    6.48: _w(("Baju", 6.58, 7.20), ("renang.", 7.20, 8.05)),
    26.38: _w(("Seluar", 26.40, 26.60), ("pendek", 26.60, 27.32), ("pun", 27.32, 27.58), ("boleh.", 27.58, 28.24)),
    28.78: _w(("Seluar", 28.84, 29.10), ("panjang", 29.10, 29.58), ("pun", 29.58, 29.74), ("ada.", 29.74, 29.98)),
    30.46: _w(("Boleh", 30.48, 30.58), ("pakai", 30.58, 30.76), ("seluar", 30.76, 30.94), ("pendek", 30.94, 31.20),
              ("kat", 31.20, 31.36), ("rumah.", 31.36, 31.60)),
    32.12: _w(("Seluar", 32.18, 32.42), ("panjang,", 32.42, 32.96)),
    33.40: _w(("jenis", 33.46, 33.80), ("fit", 33.80, 33.98), ("kan?", 33.98, 34.40)),
    41.55: _w(("Ni", 41.60, 42.24), ("baju", 42.24, 43.06), ("renang.", 43.06, 44.20)),
    44.58: _w(("Tangan", 44.96, 45.30), ("panjang.", 45.30, 45.92), ("Ni", 46.12, 46.24), ("untuk", 46.24, 46.54),
              ("lelaki.", 46.54, 47.90)),
    53.28: _w(("Kainnya", 53.40, 54.34), ("lembut", 54.40, 55.00), ("je.", 55.00, 55.26)),
}
DROP = [(64.5, 69.0)]
HILITE = {"PANTAI", "BERCUTI", "PULAU-PULAU", "RENANG", "PENDEK", "PANJANG", "RUMAH", "FIT", "LELAKI", "LEMBUT",
          "TANGAN", "KAINNYA"}


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
Style: Cap,Fredoka,58,&H00FFFFFF,&H000000FF,&H0045250B,&H6445250B,-1,0,0,0,100,100,0,0,1,5,3,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Label,Fredoka,62,&H0045250B,&H000000FF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,3,16,0,5,40,40,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,&H0045250B,&H6445250B,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# palette for the men's swim set (black fabric): deep sea navy text, ocean blue, aqua water, sunny yellow, coral
NAVY = "&H0045250B&"     # #0B2545  (ASS colours are BGR)
OCEAN = "&H00C87700&"    # #0077C8
AQUA = "&H00D6C42E&"     # #2EC4D6
SUN = "&H003FD2FF&"      # #FFD23F
CORAL = "&H004A6BFF&"    # #FF6B4A
WHITE = "&H00FFFFFF&"
ESP = NAVY               # default label text colour (kept name for label())
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


def label(t0, t1, text, y=760, col=ESP, box=WHITE, hi=OCEAN, rot=-3, layer=5, x=CX, size=62):
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

    SL, SR, SY = 85, 555, 665

    def speed_tag(name, txt=">> x3"):
        b = BT[name]
        ev.append(f"Dialogue: 6,{ts(b['t0'])},{ts(b['t0'] + b['dur'])},Small,,0,0,0,,"
                  rf"{{\an7\pos({SAFE_L},{SAFE_T + 20})\c{SUN}}}{txt}")
        sfx.append(("swish", b["t0"] - 0.05, 0.45))

    # ---- HOOK: beach / holiday / islands
    lab(58.44, 60.70, "SESUAI KE *PANTAI*!", col=WHITE, box=OCEAN, hi=SUN, rot=-3, size=72, sound="bloop", vol=0.5)
    stk("🏖️", 58.48, 60.70, SR, SY, 110)
    lab(60.84, 62.20, "NAK *BERCUTI*", col=NAVY, box=SUN, hi=OCEAN, rot=2, size=72, sound="whoosh", vol=0.4)
    stk("✈️", 60.88, 62.20, SR, SY, 100)
    ev.append(flash(tl(62.28), d=0.25))
    lab(62.30, 64.30, "PERGI *PULAU*!", col=WHITE, box=CORAL, hi=SUN, rot=-2, size=76, sound="ding", vol=0.4)
    stk("🏝️", 62.34, 64.30, SR, SY, 110)

    # ---- unboxing
    speed_tag("buka")
    b = BT["buka"]
    ev.append(label(b["t0"] + 0.1, b["t0"] + b["dur"], "JOM *UNBOX*!", col=NAVY, box=WHITE, hi=OCEAN, rot=-2))
    sfx.append(("pop", b["t0"] + 0.1, 0.45))
    bstk("📦", b["t0"] + 0.15, b["t0"] + b["dur"], SR, SY, 100)

    # ---- what it is
    lab(6.58, 8.10, "BAJU *RENANG*", col=WHITE, box=OCEAN, hi=SUN, rot=2, size=76, sound="sparkle", vol=0.35)
    stk("🌊", 6.62, 8.10, SR, SY, 110)

    # ---- shorts + long pants
    lab(26.40, 28.26, "SELUAR *PENDEK*", col=NAVY, box=SUN, hi=CORAL, rot=-3, sound="pop", vol=0.5)
    stk("🩳", 26.44, 28.26, SR, SY, 100)
    lab(28.84, 30.02, "+ SELUAR *PANJANG*", col=WHITE, box=OCEAN, hi=SUN, rot=2, sound="pop", vol=0.5)
    stk("👖", 28.88, 30.02, SR, SY, 100)
    lab(30.48, 31.62, "PAKAI *KAT RUMAH*", col=NAVY, box=WHITE, hi=OCEAN, rot=-2, sound="whoosh", vol=0.35)
    stk("🏠", 30.52, 31.62, SR, SY, 100)
    lab(32.18, 34.40, "PANJANG *JENIS FIT*", col=NAVY, box=AQUA, hi=WHITE, rot=2, sound="pop", vol=0.5)
    stk("💪", 32.22, 34.40, SR, SY, 100)

    # ---- the top
    ev.append(flash(tl(41.60), d=0.25))
    lab(41.62, 44.20, "BAJU *RENANG*", col=WHITE, box=OCEAN, hi=SUN, rot=-2, sound="ding", vol=0.35)
    stk("👕", 41.66, 44.20, SR, SY, 100)
    lab(44.96, 45.92, "*TANGAN PANJANG*", col=NAVY, box=SUN, hi=CORAL, rot=2, sound="pop", vol=0.5)
    stk("🙆", 45.00, 45.92, SR, SY, 100)
    lab(46.12, 48.40, "UNTUK *LELAKI*", col=WHITE, box=NAVY, hi=AQUA, rot=-3, size=72, sound="bloop", vol=0.45)
    stk("👨", 46.16, 48.40, SR, SY, 100)

    # ---- fabric
    lab(53.40, 55.30, "KAIN *LEMBUT*", col=NAVY, box=WHITE, hi=OCEAN, rot=2, size=72, sound="sparkle", vol=0.3)
    stk("☁️", 53.44, 55.30, SR, SY, 100)

    # ---- end card (inside the safe area)
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 8,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{NAVY}\1a&HFF&\t(0,250,\1a&H60&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    ev.append(label(e0 + 0.05, TOTAL, "BAJU RENANG *LELAKI*", col=WHITE, box=OCEAN, hi=SUN, y=430, rot=-3,
                    layer=9, size=60))
    ev.append(label(e0 + 0.3, TOTAL, "BAJU • SELUAR PENDEK • PANJANG", col=NAVY, box=WHITE, hi=OCEAN, y=540, rot=2,
                    layer=9, size=40))
    ev.append(label(e0 + 0.6, TOTAL, "TAG GENG *PANTAI* KORANG!", col=WHITE, box=CORAL, hi=SUN, y=655, rot=-2,
                    layer=9, size=50))
    ev.append(label(e0 + 0.9, TOTAL, "TEKAN BEG KUNING", col=NAVY, box=SUN, y=775, rot=2, layer=9, size=58))
    bstk("🏊", e0 + 0.1, TOTAL, SR, 350, 100)
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
