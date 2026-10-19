#!/usr/bin/env python3
"""Edit for the banana plush pillow (bantal pisang 35/50/70cm) TikTok video, two source clips joined.

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
# Two source clips of the same product, joined into one timeline (master1080/proxy = A + B):
#   A (IMG_7877) 0 - 49.367s : unboxing the 70cm banana pillow, toddler plays with it
#   B (IMG_7879) 49.367s -   : unboxing the 35cm one, size comparison, CTA
# v: list of (src_in, src_out, speed, zoom)
# a: 'same' (follow v at speed 1), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK: "Tidak kusangka sebesar ini! Ni 35cm. Yang ni, ni 70cm."
    #  (J-cut: B both bananas -> B big one across her lap with the small one -> B big one held up; "guys" cut)
    dict(name="hook", a=[(77.58, 79.40), (68.80, 70.14), (71.08, 73.20)],
         v=[(73.00, 74.82, 1, 1.05), (85.00, 86.34, 1, 1.0), (71.08, 73.20, 1, 1.0)]),
    # "Ni bantal pisang yang kita nanti-nantikan."  (A, opening the delivery bag; "Bismillah / Oh" cut)
    dict(name="intro", a="same", v=[(2.62, 5.76, 1, 1.0)]),
    # "Wah ni pisang yang besar. Wah, pisang 70cm!"
    dict(name="wah", a="same", v=[(6.80, 8.62, 1, 1.0), (8.62, 11.00, 1, 1.1)]),
    # taking it out of the plastic, fast
    dict(name="buka", a=None, v=[(13.00, 18.50, 3, 1.0)]),
    # toddler sits on it: "Ya Allah anakku."
    dict(name="anak", a="same", v=[(36.90, 39.60, 1, 1.0)]),
    # "Ih, gebu lah. Besar lah ni. Ni 70cm. Saya pun ada 50cm."  (J-cut onto her hugging it with the toddler)
    dict(name="gebu", a=[(41.62, 45.72)], v=[(43.00, 47.10, 1, 1.0)]),
    # B: "Ni bantal pisang yang paling kecil. Oh, dia kompres macam ni."  ("Bismillah. Kata dah" cut)
    dict(name="kecil", a="same", v=[(52.85, 56.70, 1, 1.0), (57.05, 58.70, 1, 1.08)]),
    # unpacking the small one, fast
    dict(name="buka2", a=None, v=[(58.70, 67.10, 3, 1.0)]),
    # "Ni kalau nak bagi baby... bagi baby newborn yang pegang. Kecil sangat ni."  (unclear "letak as'Allah" cut)
    dict(name="baby", a="same", v=[(81.00, 82.82, 1, 1.0), (86.56, 89.58, 1, 1.08)]),
    # "Sebab tu dalam live saya cakap 35cm jangan ambil, untuk hiasan saja."
    dict(name="hiasan", a="same", v=[(93.50, 97.02, 1, 1.0)]),
    # "Nak peluk ambil 50cm dengan 70cm, macam ni besar."  (repeat "50cm dengan 70cm besar buat peluk" cut)
    dict(name="peluk", a="same", v=[(97.42, 100.26, 1, 1.05)]),
    # "Dapatkan dekat beg kuning, kita ada 3 size."  ("Okay guys" cut)
    dict(name="cta", a="same", v=[(113.96, 115.86, 1, 1.0)]),
    # thumbs up with the big one, slowed
    dict(name="end", a=None, v=[(112.95, 113.75, 0.4, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "Okey": "Okay", "itu": "tu", "bag": "beg", "Bag": "Beg", "bantai": "bantal",
       "tahu": "tau"}
# hand-checked words where Whisper drifted or misheard (re-transcribed per clip)
def _w(*ws):
    return [dict(w=w, s=a, e=b) for w, a, b in ws]


OVERRIDE = {
    77.58: _w(("Tidak", 77.62, 78.20), ("kusangka", 78.20, 78.82), ("sebesar", 78.82, 79.14), ("ini!", 79.14, 79.36)),
    68.80: _w(("Ni", 68.84, 69.32), ("35cm.", 69.32, 70.12)),
    71.08: _w(("Yang", 71.10, 71.32), ("ni,", 71.32, 72.00), ("ni", 72.00, 72.60), ("70cm!", 72.60, 73.18)),
    2.62: _w(("Ni", 2.70, 2.92), ("bantal", 2.92, 3.38), ("pisang", 3.38, 3.92), ("yang", 3.92, 4.18), ("kita", 4.18, 4.62),
             ("nanti", 4.62, 4.96), ("-nantikan.", 4.96, 5.68)),
    6.80: _w(("Wah", 6.86, 7.14), ("ni", 7.14, 7.40), ("pisang", 7.40, 7.70), ("yang", 7.70, 7.80), ("besar.", 7.80, 8.40)),
    8.62: _w(("Wah,", 9.40, 9.56), ("pisang", 9.58, 10.20), ("70cm!", 10.22, 10.96)),
    36.90: _w(("Ya", 38.32, 38.60), ("Allah", 38.60, 39.00), ("anakku.", 39.00, 39.50)),
    41.62: _w(("Ih,", 41.64, 42.06), ("gebu", 42.08, 42.36), ("lah.", 42.36, 42.54), ("Besar", 42.56, 42.86),
              ("lah", 42.86, 42.94), ("ni.", 42.94, 43.16), ("Ni", 43.70, 43.92), ("70cm.", 43.92, 44.56),
              ("Saya", 44.80, 44.92), ("pun", 44.92, 44.98), ("ada", 44.98, 45.12), ("50cm.", 45.12, 45.70)),
    52.85: _w(("Ni", 52.88, 53.14), ("bantal", 53.14, 54.32), ("pisang", 54.32, 55.42), ("yang", 55.42, 55.68),
              ("paling", 55.68, 55.88), ("kecil.", 55.88, 56.60)),
    57.05: _w(("Oh,", 57.07, 57.14), ("dia", 57.14, 57.42), ("kompres", 57.42, 58.12), ("macam", 58.12, 58.42), ("ni.", 58.42, 58.62)),
    81.00: _w(("Ni", 81.02, 81.64), ("kalau", 81.64, 81.78), ("nak", 81.78, 81.92), ("bagi", 81.92, 82.24), ("baby...", 82.24, 82.78)),
    86.56: _w(("Bagi", 86.58, 86.64), ("baby", 86.64, 87.06), ("newborn", 87.06, 87.42), ("yang", 87.44, 87.56),
              ("pegang.", 87.56, 88.00), ("Kecil", 88.86, 89.12), ("sangat", 89.12, 89.36), ("ni.", 89.36, 89.56)),
    93.50: _w(("Sebab", 93.54, 93.66), ("tu", 93.66, 93.78), ("saya", 93.78, 93.96), ("dalam", 93.96, 94.10), ("live", 94.10, 94.24),
              ("saya", 94.24, 94.38), ("cakap", 94.38, 94.62), ("35cm", 94.62, 95.36), ("jangan", 95.38, 95.64),
              ("ambil,", 95.64, 96.02), ("untuk", 96.02, 96.26), ("hiasan", 96.26, 96.70), ("saja.", 96.70, 97.00)),
    97.42: _w(("Nak", 97.44, 98.04), ("peluk", 98.04, 98.22), ("ambil", 98.22, 98.46), ("50cm", 98.46, 98.90),
              ("dengan", 98.90, 99.00), ("70cm,", 99.00, 99.62), ("macam", 99.62, 99.70), ("ni", 99.70, 99.82),
              ("besar.", 99.82, 100.20)),
    113.96: _w(("Dapatkan", 114.00, 114.38), ("dekat", 114.38, 114.52), ("beg", 114.52, 114.66), ("kuning,", 114.66, 114.92),
               ("kita", 114.92, 115.12), ("ada", 115.12, 115.26), ("3", 115.26, 115.52), ("size!", 115.52, 115.82)),
}
DROP = []
HILITE = {"BANTAL", "PISANG", "BESAR.", "BESAR", "70CM", "70CM!", "70CM.", "70CM,", "50CM", "50CM.", "35CM", "35CM.",
          "SEBESAR", "GEBU", "KECIL", "KOMPRES", "BABY", "NEWBORN", "HIASAN", "PELUK", "KUNING", "3", "SIZE", "LIVE",
          "ANAKKU"}

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
Style: Cap,Fredoka,58,&H00FFFFFF,&H000000FF,&H00142E4A,&H64142E4A,-1,0,0,0,100,100,0,0,1,5,3,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Label,Fredoka,62,&H00142E4A,&H000000FF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,3,16,0,5,40,40,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,&H00142E4A,&H64142E4A,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# palette from the banana: brown tip (text/outline), banana yellow, green stem, leaf green, candy pink, sky, cream
BROWN = "&H00142E4A&"    # #4A2E14  (ASS colours are BGR)
BANANA = "&H003DD9FF&"   # #FFD93D
STEM = "&H005ABE3D&"     # #3DBE5A
LEAF = "&H003A8A1F&"     # #1F8A3A
PINK = "&H00A25FFF&"     # #FF5FA2  active caption word (stands out on the yellow pillow)
SKY = "&H00FFC85E&"      # #5EC8FF
CREAM = "&H00D6F6FF&"    # #FFF6D6
WHITE = "&H00FFFFFF&"
ACC = PINK
KEY = BANANA

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


def label(t0, t1, text, y=270, col=BROWN, box=WHITE, hi=PINK, rot=-3, layer=5, x=CX, size=62):
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
              rf"{{\an7\pos(0,0)\c{PINK}\fscx0\t(0,{int(TOTAL * 1000)},\fscx100)\p1}}m 0 0 l {W} 0 {W} 8 0 8{{\p0}}")

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
                  rf"{{\an7\pos({SAFE_L},{SAFE_T + 20})\c{BANANA}}}{txt}")
        sfx.append(("swish", b["t0"] - 0.05, 0.45))

    # ---- HOOK: never expected it this big -> 35cm vs 70cm
    lab(77.62, 79.38, "TAK SANGKA *SEBESAR NI*!", col=BROWN, box=BANANA, hi=PINK, rot=-3, size=68, sound="bloop", vol=0.5)
    stk("😱", 77.66, 79.38, SR, SY, 105)
    ev.append(flash(tl(68.82), d=0.25))
    lab(68.84, 70.12, "NI *35CM*", col=WHITE, box=STEM, hi=BANANA, rot=2, size=74, sound="pop", vol=0.5)
    stk("🤏", 68.88, 70.12, SR, SY, 100)
    lab(71.10, 73.18, "YANG NI *70CM*!", col=WHITE, box=PINK, hi=BANANA, rot=-2, size=76, sound="ding", vol=0.4)
    stk("🍌", 71.14, 73.18, SL, SY, 105)
    stk("🤯", 71.14, 73.18, SR, SY, 100)

    # ---- A: the big one arrives
    lab(2.92, 4.16, "*BANTAL PISANG*", col=BROWN, box=BANANA, hi=LEAF, rot=-2, size=72, sound="bloop", vol=0.5)
    stk("🍌", 2.96, 4.16, SR, SY, 100)
    lab(4.18, 5.70, "YANG *DITUNGGU-TUNGGU*", col=WHITE, box=STEM, hi=BANANA, rot=2, size=60, sound="pop", vol=0.45)
    stk("🥳", 4.22, 5.70, SR, SY, 100)
    lab(6.86, 8.40, "WAH *BESARNYA*!", col=WHITE, box=PINK, hi=BANANA, rot=-2, size=74, sound="whoosh", vol=0.35)
    stk("🤩", 6.90, 8.40, SR, SY, 100)
    ev.append(flash(tl(9.40), d=0.25))
    lab(9.40, 10.96, "PISANG *70CM*!", col=BROWN, box=BANANA, hi=PINK, rot=2, size=76, sound="ding", vol=0.4)
    stk("📏", 9.44, 10.96, SR, SY, 100)
    speed_tag("buka", ">> x3")

    # ---- toddler
    lab(37.00, 38.30, "*ANAK* PUN SUKA", col=WHITE, box=SKY, hi=BANANA, rot=-2, sound="bloop", vol=0.45)
    stk("🥰", 37.04, 38.30, SR, SY, 100)
    lab(38.32, 39.56, "YA ALLAH *ANAKKU*!", col=BROWN, box=CREAM, hi=PINK, rot=2, sound="pop", vol=0.45)
    stk("😂", 38.36, 39.56, SR, SY, 100)
    lab(41.64, 42.54, "*GEBU*!", col=BROWN, box=BANANA, hi=PINK, rot=-3, size=80, sound="sparkle", vol=0.35)
    stk("☁️", 41.68, 42.54, SR, SY, 100)
    lab(42.56, 43.60, "*BESAR* LAH NI", col=WHITE, box=STEM, hi=BANANA, rot=2, sound="pop", vol=0.45)
    lab(43.70, 44.56, "*70CM*", col=WHITE, box=PINK, hi=BANANA, rot=-2, size=80, sound="click", vol=0.5)
    lab(44.80, 45.70, "ADA *50CM* JUGA", col=BROWN, box=CREAM, hi=PINK, rot=2, sound="pop", vol=0.45)
    stk("👍", 44.84, 45.70, SR, SY, 100)

    # ---- B: the small one
    ev.append(flash(tl(52.88), d=0.25))
    lab(52.88, 56.60, "YANG *PALING KECIL*", col=WHITE, box=STEM, hi=BANANA, rot=-2, sound="bloop", vol=0.5)
    stk("🤏", 52.92, 56.60, SR, SY, 100)
    lab(57.07, 58.66, "DIA *KOMPRES*", col=BROWN, box=BANANA, hi=PINK, rot=2, sound="whoosh", vol=0.35)
    stk("📦", 57.11, 58.66, SR, SY, 100)
    speed_tag("buka2", ">> x3")
    lab(81.02, 82.78, "NAK BAGI *BABY*?", col=WHITE, box=SKY, hi=BANANA, rot=-2, sound="bloop", vol=0.45)
    stk("👶", 81.06, 82.78, SR, SY, 100)
    lab(86.58, 88.00, "*NEWBORN* PEGANG", col=BROWN, box=CREAM, hi=PINK, rot=2, sound="pop", vol=0.45)
    stk("🍼", 86.62, 88.00, SR, SY, 100)
    lab(88.86, 89.56, "*KECIL* SANGAT!", col=WHITE, box=PINK, hi=BANANA, rot=-2, sound="pop", vol=0.45)
    ev.append(flash(tl(94.62), d=0.25))
    lab(94.62, 96.02, "*35CM* JANGAN AMBIL", col=WHITE, box=PINK, hi=BANANA, rot=-2, size=64, sound="ding", vol=0.4)
    stk("🙅", 94.66, 96.02, SR, SY, 100)
    lab(96.02, 97.00, "UNTUK *HIASAN* JE", col=BROWN, box=BANANA, hi=PINK, rot=2, sound="pop", vol=0.45)
    stk("🎀", 96.06, 97.00, SR, SY, 100)
    lab(97.44, 98.44, "NAK *PELUK*?", col=WHITE, box=STEM, hi=BANANA, rot=-2, size=76, sound="bloop", vol=0.5)
    stk("🤗", 97.48, 98.44, SR, SY, 105)
    lab(98.46, 100.20, "AMBIL *50 / 70CM*", col=BROWN, box=CREAM, hi=PINK, rot=2, size=70, sound="pop", vol=0.45)
    stk("💛", 98.50, 100.20, SR, SY, 100)

    # ---- CTA
    lab(114.00, 114.92, "TENGOK *BEG KUNING*", col=BROWN, box=BANANA, hi=PINK, rot=-2, sound="kaching", vol=0.4)
    stk("🛒", 114.04, 114.92, SR, SY, 100)
    lab(114.92, 115.84, "ADA *3 SIZE*!", col=WHITE, box=PINK, hi=BANANA, rot=2, size=76, sound="ding", vol=0.4)
    stk("✨", 114.96, 115.84, SR, SY, 100)

    # ---- end card (inside the safe area)
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 8,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{BROWN}\1a&HFF&\t(0,250,\1a&H60&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    ev.append(label(e0 + 0.05, TOTAL, "*BANTAL PISANG*", col=BROWN, box=BANANA, hi=PINK, y=430, rot=-3, layer=9, size=66))
    ev.append(label(e0 + 0.3, TOTAL, "35 • 50 • 70 CM", col=WHITE, box=STEM, hi=BANANA, y=540, rot=2, layer=9, size=50))
    ev.append(label(e0 + 0.6, TOTAL, "KORANG NAK *SIZE* MANA?", col=BROWN, box=CREAM, hi=PINK, y=655, rot=-2,
                    layer=9, size=50))
    ev.append(label(e0 + 0.9, TOTAL, "TEKAN BEG KUNING", col=WHITE, box=PINK, hi=BANANA, y=775, rot=2, layer=9, size=58))
    bstk("🍌", e0 + 0.1, TOTAL, SR, 350, 100)
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
