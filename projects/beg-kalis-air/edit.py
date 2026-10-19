#!/usr/bin/env python3
"""Edit for the camo waterproof dry bag (beg kalis air / waterproof bag) TikTok video, two source clips joined.

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
#   A (IMG_7884) 0 - 134.868s : opening the parcel, bag reveal, toddler plays with it, aeroplane / umbrella talk
#   B (IMG_7885) 134.868s -   : bag held up, uses, valuables / phone, pattern, CTA
# v: list of (src_in, src_out, speed, zoom)
# a: 'same' (follow v at speed 1), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK: "Untuk pergi pantai, kena ada beg ni lah."  (J-cut, unclear "tak bersih" cut; A bag front -> B bag held)
    dict(name="hook", a=[(36.60, 38.38), (40.08, 41.08)],
         v=[(49.00, 50.78, 1, 1.05), (134.95, 135.95, 1, 1.0)]),
    # B: "Ni waterproof, waterproof bag."
    dict(name="intro", a="same", v=[(136.03, 138.74, 1, 1.0)]),
    # B: "Kita guna untuk snorkeling, nak pergi camping, nak pergi mendaki gunung-gunung yang bersalji."
    #  (first "Kita boleh guna untuk snorkeling, sabar-sabar" cut)
    dict(name="guna", a="same", v=[(144.22, 146.50, 1, 1.0), (146.50, 148.93, 1, 1.08)]),
    # B: "Travel, fishing, untuk memancing ke, nak pergi laut ke."  ("apa lagi dia tulis tadi? Untuk" cut)
    dict(name="travel", a="same", v=[(153.56, 157.14, 1, 1.0)]),
    # B: "Boleh masukkan barang-barang yang berharga dalam ni. Supaya dia tak rosak lah, handphone pun semua
    #     kalau dia jatuh ke apa ke, taklah terendam dengan air kan."  ("Okey ni" cut)
    dict(name="barang", a="same", v=[(162.07, 165.80, 1, 1.05), (165.80, 169.20, 1, 1.0), (169.20, 171.28, 1, 1.1)]),
    # A: "Kita masukkan barang dah ni." / "Lepas tu, boleh tarik dia." / "Lipat, oh lipat-lipat dia."
    #  (J-cut: toddler + her packing the bag, pulling the top strip, bag upright)
    dict(name="demo", a=[(49.72, 51.52), (52.42, 54.72), (56.48, 57.88)],
         v=[(87.00, 88.80, 1, 1.0), (55.20, 57.50, 1, 1.0), (78.80, 80.20, 1, 1.0)]),
    # B: "Oh, comel lah sebab saya selalu tengok dia tak ada corak, kosong. Ni ada corak, comel lah corak dia."
    dict(name="corak", a="same", v=[(180.62, 183.90, 1, 1.0), (183.90, 185.68, 1, 1.08)]),
    # A: "(Okay,) yang mana nak naik aeroplane?" / "Bawa beg ni lah, over thinking sikit macam tu." /
    #    "Kita stand by, sediakan payung sebelum hujan."  (J-cut over the toddler playing with the bag)
    dict(name="aero", a=[(107.82, 109.76), (113.78, 117.16), (120.84, 123.82)],
         v=[(66.80, 71.00, 1, 1.0), (71.40, 73.40, 1, 1.0), (88.80, 90.90, 1, 1.0)]),
    # B CTA: "Okay, dapatkan korang kalau nak pergi snorkeling dekat pantai, dekat pulau, kan?"  (toddler walks past -> other shot)
    dict(name="cta1", a=[(189.22, 192.64)], v=[(189.22, 191.60, 1, 1.0), (196.00, 197.04, 1, 1.0)]),
    # "Nak pergi Sabah atau nak pergi Terengganu, kan?"
    dict(name="cta2", a="same", v=[(193.30, 195.27, 1, 1.05)]),
    # "Okay, dapatkan dekat beg kuning."
    dict(name="cta3", a="same", v=[(200.28, 201.95, 1, 1.0)]),
    # bag held up, slowed
    dict(name="end", a=None, v=[(198.40, 199.20, 0.4, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "Okey": "Okay", "itu": "tu"}
# hand-checked words where Whisper drifted or misheard (re-transcribed per clip)
def _w(*ws):
    return [dict(w=w, s=a, e=b) for w, a, b in ws]


OVERRIDE = {
    36.60: _w(("Untuk", 36.70, 37.28), ("pergi", 37.28, 37.58), ("pantai,", 37.58, 38.34)),
    40.08: _w(("kena", 40.12, 40.30), ("ada", 40.30, 40.50), ("beg", 40.50, 40.66), ("ni", 40.66, 40.82), ("lah!", 40.82, 41.02)),
    136.03: _w(("Ni", 136.05, 136.35), ("waterproof,", 136.35, 136.78), ("waterproof", 137.60, 138.25), ("bag.", 138.25, 138.70)),
    144.22: _w(("Kita", 144.27, 144.61), ("guna", 144.61, 144.89), ("untuk", 144.89, 145.19), ("snorkeling,", 145.19, 145.67),
               ("nak", 145.80, 145.87), ("pergi", 145.87, 146.05), ("camping,", 146.05, 146.49)),
    146.50: _w(("nak", 146.75, 146.81), ("pergi", 146.81, 147.05), ("mendaki", 147.05, 147.55), ("gunung", 147.55, 147.79),
               ("-gunung", 147.79, 148.09), ("yang", 148.09, 148.23), ("bersalji.", 148.23, 148.91)),
    153.56: _w(("Travel,", 153.60, 154.12), ("fishing,", 154.48, 154.72), ("untuk", 155.40, 155.48), ("memancing", 155.48, 156.10),
               ("ke,", 156.10, 156.30), ("nak", 156.38, 156.50), ("pergi", 156.50, 156.66), ("laut", 156.66, 156.90), ("ke.", 156.90, 157.12)),
    162.07: _w(("Boleh", 162.10, 162.23), ("masukkan", 162.23, 162.65), ("barang", 162.65, 162.87), ("-barang", 162.87, 163.45),
               ("yang", 163.45, 164.00), ("berharga", 164.00, 164.83), ("dalam", 164.83, 165.05), ("ni.", 165.05, 165.24)),
    165.80: _w(("Supaya", 165.97, 166.19), ("dia", 166.19, 166.31), ("tak", 166.31, 166.47), ("rosak", 166.47, 166.77),
               ("lah,", 166.77, 166.92), ("handphone", 166.95, 167.38), ("pun", 167.38, 167.50), ("semua", 167.50, 167.62),
               ("kalau", 167.62, 167.72), ("dia", 167.72, 167.83), ("jatuh", 167.83, 168.29), ("ke", 168.29, 168.41),
               ("apa", 168.41, 168.59), ("ke,", 168.59, 169.09)),
    169.20: _w(("taklah", 169.53, 169.95), ("terendam", 169.95, 170.37), ("dengan", 170.37, 170.55), ("air,", 170.55, 171.05),
               ("kan?", 171.11, 171.25)),
    49.72: _w(("Kita", 49.75, 49.86), ("masukkan", 49.86, 50.36), ("barang", 50.36, 50.72), ("dah", 50.72, 50.96), ("ni.", 50.96, 51.26)),
    52.42: _w(("Lepas", 52.45, 52.80), ("tu,", 52.80, 53.30), ("boleh", 53.84, 54.00), ("tarik", 54.00, 54.40), ("dia.", 54.40, 54.70)),
    56.48: _w(("Lipat,", 56.60, 56.84), ("oh", 56.90, 56.98), ("lipat", 56.98, 57.20), ("-lipat", 57.20, 57.52), ("dia.", 57.52, 57.84)),
    180.62: _w(("Oh,", 180.65, 180.93), ("comel", 180.99, 181.20), ("lah", 181.20, 181.37), ("sebab", 181.37, 181.55),
               ("saya", 181.55, 181.69), ("selalu", 181.69, 181.91), ("tengok", 181.91, 182.23), ("dia", 182.23, 182.35),
               ("tak", 182.35, 182.81), ("ada", 182.81, 182.97), ("corak,", 182.97, 183.21), ("kosong.", 183.21, 183.81)),
    183.90: _w(("Ni", 184.03, 184.09), ("ada", 184.09, 184.25), ("corak,", 184.25, 184.57), ("comel", 184.61, 184.85),
               ("lah", 184.85, 185.03), ("corak", 185.03, 185.31), ("dia.", 185.31, 185.59)),
    107.82: _w(("Yang", 107.86, 108.22), ("mana", 108.22, 108.38), ("nak", 108.38, 108.54),
               ("naik", 108.54, 108.70), ("aeroplane?", 108.70, 109.74)),
    113.78: _w(("Bawa", 113.84, 114.44), ("beg", 114.44, 114.64), ("ni", 114.64, 114.86), ("lah,", 114.86, 115.50),
               ("over", 115.54, 115.82), ("thinking", 115.82, 116.12), ("sikit", 116.12, 116.58), ("macam", 116.62, 116.92), ("tu.", 116.92, 117.12)),
    120.84: _w(("Kita", 120.90, 121.34), ("stand", 121.34, 121.70), ("by,", 121.70, 122.20), ("sediakan", 122.30, 122.84),
               ("payung", 122.84, 123.08), ("sebelum", 123.08, 123.36), ("hujan.", 123.36, 123.74)),
    189.22: _w(("Okay,", 189.25, 189.57), ("dapatkan", 189.57, 189.93), ("korang", 189.93, 190.23), ("kalau", 190.23, 190.35), ("nak", 190.35, 190.47),
               ("pergi", 190.47, 190.57), ("snorkeling", 190.57, 190.95), ("dekat", 190.95, 191.17), ("pantai,", 191.17, 191.69),
               ("dekat", 191.80, 191.87), ("pulau,", 191.87, 192.29), ("kan?", 192.43, 192.59)),
    193.30: _w(("Nak", 193.32, 193.43), ("pergi", 193.43, 193.61), ("Sabah", 193.61, 194.03), ("atau", 194.03, 194.17),
               ("nak", 194.17, 194.21), ("pergi", 194.21, 194.35), ("Terengganu,", 194.35, 194.89), ("kan?", 195.01, 195.19)),
    200.28: _w(("Okay,", 200.30, 200.70), ("dapatkan", 200.72, 201.12), ("dekat", 201.12, 201.22), ("beg", 201.22, 201.36),
               ("kuning.", 201.36, 201.84)),
}
DROP = []
HILITE = {"PANTAI", "BEG", "WATERPROOF", "BAG", "SNORKELING", "CAMPING", "MENDAKI", "GUNUNG", "BERSALJI", "TRAVEL",
          "FISHING", "MEMANCING", "LAUT", "BARANG", "BERHARGA", "HANDPHONE", "JATUH", "TERENDAM", "AIR", "TARIK",
          "LIPAT-LIPAT", "CORAK", "KOSONG", "AEROPLANE", "PAYUNG", "HUJAN", "PULAU", "SABAH", "TERENGGANU", "KUNING", "COMEL"}

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

# palette from the camo dry bag: navy (text/outline), royal blue camo, aqua water, army green, sun yellow, coral, sand
NAVY = "&H0045250B&"     # #0B2545  (ASS colours are BGR)
ROYAL = "&H00FF6B1E&"    # #1E6BFF
AQUA = "&H00E6C319&"     # #19C3E6
CAMO = "&H002A6B4F&"     # #4F6B2A
SUN = "&H003FD2FF&"      # #FFD23F  active caption word
CORAL = "&H004A6BFF&"    # #FF6B4A
SAND = "&H00C9F1FF&"     # #FFF1C9
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
                elif t.strip("-?!") in HILITE or t in HILITE:
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
              rf"{{\an7\pos(0,0)\c{SUN}\fscx0\t(0,{int(TOTAL * 1000)},\fscx100)\p1}}m 0 0 l {W} 0 {W} 8 0 8{{\p0}}")

    def lab(s0, s1, text, sound="pop", vol=0.5, **kw):
        ev.append(label(tl(s0), tl(s1), text, **kw))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def stk(em, s0, s1, x, y, size=100):
        stickers.append((em, tl(s0), tl(s1), x, y, size))

    def bstk(em, t0, t1, x, y, size=100):
        stickers.append((em, t0, t1, x, y, size))

    SL, SR, SY = 85, 555, 175     # stickers sit beside the labels, above the bag

    # ---- HOOK: going to the beach -> you need this bag
    lab(36.70, 38.34, "NAK KE *PANTAI*?", col=NAVY, box=AQUA, hi=WHITE, rot=-3, size=72, sound="bloop", vol=0.5)
    stk("🏖️", 36.74, 38.34, SR, SY, 105)
    ev.append(flash(tl(40.10), d=0.25))
    lab(40.12, 41.02, "KENA ADA *BEG NI*!", col=NAVY, box=SUN, hi=ROYAL, rot=2, size=74, sound="impact", vol=0.4)
    stk("🎒", 40.16, 41.02, SR, SY, 105)

    # ---- what it is
    lab(136.05, 138.70, "*WATERPROOF* BAG", col=WHITE, box=ROYAL, hi=SUN, rot=-2, size=72, sound="spray", vol=0.3)
    stk("💦", 136.09, 138.70, SR, SY, 100)

    # ---- uses
    lab(144.89, 145.67, "*SNORKELING*", col=NAVY, box=AQUA, hi=WHITE, rot=-2, size=74, sound="bloop", vol=0.45)
    stk("🤿", 144.93, 145.67, SR, SY, 100)
    lab(145.80, 146.49, "*CAMPING*", col=WHITE, box=CAMO, hi=SUN, rot=2, size=74, sound="pop", vol=0.45)
    stk("⛺", 145.84, 146.49, SR, SY, 100)
    lab(146.75, 148.91, "MENDAKI *GUNUNG*", col=NAVY, box=SAND, hi=ROYAL, rot=-2, sound="pop", vol=0.45)
    stk("🏔️", 146.79, 148.91, SR, SY, 100)
    lab(153.60, 154.12, "*TRAVEL*", col=WHITE, box=ROYAL, hi=SUN, rot=2, size=76, sound="whoosh", vol=0.35)
    stk("✈️", 153.64, 154.12, SR, SY, 100)
    lab(154.48, 156.30, "*FISHING*", col=NAVY, box=SUN, hi=ROYAL, rot=-2, size=76, sound="pop", vol=0.45)
    stk("🎣", 154.52, 156.30, SR, SY, 100)
    lab(156.38, 157.12, "KE *LAUT*", col=NAVY, box=AQUA, hi=WHITE, rot=2, size=76, sound="pop", vol=0.45)
    stk("🌊", 156.42, 157.12, SR, SY, 100)

    # ---- valuables / phone
    ev.append(flash(tl(162.10), d=0.25))
    lab(162.10, 165.24, "SIMPAN *BARANG BERHARGA*", col=NAVY, box=SAND, hi=ROYAL, rot=-2, size=60, sound="bloop", vol=0.5)
    stk("💎", 162.14, 165.24, SR, SY, 100)
    lab(166.95, 169.09, "*HANDPHONE* JATUH?", col=WHITE, box=CORAL, hi=SUN, rot=2, size=66, sound="whoosh", vol=0.35)
    stk("📱", 166.99, 169.09, SR, SY, 100)
    lab(169.53, 171.25, "TAK *TERENDAM*!", col=NAVY, box=AQUA, hi=WHITE, rot=-2, size=74, sound="ding", vol=0.4)
    stk("💧", 169.57, 171.25, SR, SY, 100)

    # ---- how it closes
    lab(49.75, 51.26, "MASUK *BARANG*", col=WHITE, box=ROYAL, hi=SUN, rot=-2, sound="pop", vol=0.45)
    stk("👜", 49.79, 51.26, SR, SY, 100)
    lab(52.45, 54.70, "*TARIK* ATAS", col=NAVY, box=SUN, hi=ROYAL, rot=2, sound="zip", vol=0.35)
    lab(56.50, 57.84, "*LIPAT-LIPAT*", col=NAVY, box=AQUA, hi=WHITE, rot=-2, size=74, sound="swish", vol=0.4)
    stk("🔄", 56.54, 57.84, SR, SY, 95)

    # ---- the camo pattern
    lab(180.65, 181.37, "*COMEL*!", col=WHITE, box=CORAL, hi=SUN, rot=-3, size=80, sound="sparkle", vol=0.35)
    stk("😍", 180.69, 181.37, SR, SY, 100)
    lab(181.69, 183.81, "SELALU *KOSONG* JE", col=NAVY, box=SAND, hi=ROYAL, rot=2, sound="pop", vol=0.45)
    ev.append(flash(tl(184.03), d=0.25))
    lab(184.03, 185.59, "NI ADA *CORAK*!", col=WHITE, box=CAMO, hi=SUN, rot=-2, size=76, sound="ding", vol=0.4)
    stk("💙", 184.07, 185.59, SR, SY, 100)

    # ---- travel worries
    lab(107.86, 109.74, "NAIK *AEROPLANE*?", col=WHITE, box=ROYAL, hi=SUN, rot=-2, size=68, sound="whoosh", vol=0.35)
    stk("✈️", 107.90, 109.74, SR, SY, 100)
    lab(113.84, 115.50, "*BAWA BEG NI*!", col=NAVY, box=SUN, hi=ROYAL, rot=2, size=74, sound="pop", vol=0.45)
    stk("🎒", 113.88, 115.50, SR, SY, 100)
    lab(115.54, 117.12, "OVER*THINKING* SIKIT", col=NAVY, box=SAND, hi=CORAL, rot=-2, sound="pop", vol=0.4)
    stk("🤭", 115.58, 117.12, SR, SY, 100)
    lab(120.90, 122.20, "*STAND BY*", col=WHITE, box=CAMO, hi=SUN, rot=2, size=76, sound="pop", vol=0.45)
    lab(122.30, 123.74, "SEDIA *PAYUNG* SEBELUM HUJAN", col=NAVY, box=AQUA, hi=WHITE, rot=-2, size=56, sound="ding", vol=0.4)
    stk("☂️", 122.34, 123.74, SR, SY, 100)

    # ---- CTA
    lab(190.57, 192.59, "PANTAI • *PULAU*", col=NAVY, box=AQUA, hi=WHITE, rot=-2, size=70, sound="bloop", vol=0.45)
    stk("🏝️", 190.61, 192.59, SR, SY, 100)
    lab(193.32, 195.19, "*SABAH* • *TERENGGANU*", col=WHITE, box=ROYAL, hi=SUN, rot=2, size=62, sound="pop", vol=0.45)
    stk("🌴", 193.36, 195.19, SR, SY, 100)
    lab(200.72, 201.84, "TENGOK *BEG KUNING*", col=NAVY, box=SUN, hi=ROYAL, rot=-2, sound="kaching", vol=0.4)
    stk("🛒", 200.76, 201.84, SR, SY, 100)

    # ---- end card (inside the safe area)
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 8,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{NAVY}\1a&HFF&\t(0,250,\1a&H60&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    ev.append(label(e0 + 0.05, TOTAL, "*WATERPROOF BAG*", col=WHITE, box=ROYAL, hi=SUN, y=430, rot=-3, layer=9, size=64))
    ev.append(label(e0 + 0.3, TOTAL, "PANTAI • SNORKELING • CAMPING", col=NAVY, box=AQUA, hi=WHITE, y=540, rot=2, layer=9, size=44))
    ev.append(label(e0 + 0.6, TOTAL, "KORANG NAK *BAWA* KE MANA?", col=NAVY, box=SAND, hi=ROYAL, y=655, rot=-2,
                    layer=9, size=48))
    ev.append(label(e0 + 0.9, TOTAL, "TEKAN BEG KUNING", col=NAVY, box=SUN, hi=ROYAL, y=775, rot=2, layer=9, size=58))
    bstk("🎒", e0 + 0.1, TOTAL, SR, 350, 100)
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
