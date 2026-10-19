#!/usr/bin/env python3
"""Edit for the smiley flower pillows (bantal bunga senyum) TikTok video.

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
import json, math, os, subprocess, sys
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
# Single source clip (IMG_2929), outdoors on the grass: she holds up three smiley flower pillows
# (cream/honey face, lilac, pink) and talks the whole time. She wears a niqab, so J-cuts never show lip-sync.
# v: list of (src_in, src_out, speed, zoom)
# a: 'same' (follow v at speed 1), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK: "Ya Allah, bantal ni paling banyak terjual dalam live saya tau. MashaAllah dia antara yang paling
    #  ramai orang repeat order."  over the close-up of the lilac flower's face (36.0s)
    dict(name="hook", a=[(0.48, 6.48)], v=[(36.00, 42.00, 1, 1.0)]),
    # "Memang orang borong sampai 7, 10 biji."  ("Sekali seller buat promo" + price lines cut: no-price rule)
    dict(name="borong", a="same", v=[(12.54, 15.02, 1, 1.05)]),
    # "Dah lah comel, ada senyum, ada smile macam ni."  (white flower pushed to the camera)
    dict(name="comel", a="same", v=[(17.12, 19.64, 1, 1.0)]),
    # "Saiz dia 45cm."  ("tapi harga dia sangat-sangat mesra pocket, harga jimat" cut: no-price rule)
    dict(name="saiz", a="same", v=[(6.62, 8.00, 1, 1.06)]),
    # "Letak dekat kerusi ofis, | korang boleh buat sandar, boleh letak alas duduk."  (0.35s pause cut)
    dict(name="guna", a="same", v=[(19.72, 20.96, 1, 1.0), (21.30, 24.98, 1, 1.07)]),
    # "Nak buat bantal peluk dalam kereta. Lagi nak letak dekat sofa. | Memang cantik, naik serilah ruang tamu
    #  rumah korang tu."  ("Lagi nak buat apa lagi?" cut)
    dict(name="sofa", a="same", v=[(26.52, 29.96, 1, 1.0), (29.96, 33.14, 1, 1.07)]),
    # "Jangan lupa nanti nak raya, korang boleh grab buat hiasan."  ("dekat ruang tamu" cut - said just before)
    #  over the opening wide shot of all three flowers
    dict(name="raya", a=[(33.48, 37.82)], v=[(0.48, 4.82, 1, 1.06)]),
    # "Dan ada yang buat hadiah."  ("Ya Allah, ramai betul yang buat hadiah" cut - repeat)
    dict(name="hadiah", a=[(39.76, 41.10)], v=[(9.00, 10.34, 1, 1.05)]),
    # "Waktu sempena Hari Guru itu, sampai | ada yang beli sampai 17 biji pun ada!"  ("MashaAllah, guru" cut)
    dict(name="guru", a="same", v=[(42.72, 45.16, 1, 1.0), (45.16, 47.62, 1, 1.08)]),
    # "Okay korang, tengok dekat beg kuning."  ("Sekarang ada promo" cut: no-price rule)
    dict(name="cta", a="same", v=[(49.62, 51.44, 1, 1.0)]),
    # white + pink flowers to the camera, gentle slow-mo under the end card (muted)
    dict(name="end", a=None, v=[(51.46, 53.36, 0.8, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "bantai": "bantal", "sandang": "sandar", "pelut": "peluk", "kursi": "kerusi",
       "guruh": "Guru", "sepenuh": "sempena", "Kunita": "kuning", "Bek": "beg", "life": "live"}
# hand-checked words (chunk re-transcription + RMS envelope); Whisper's segment-end timings drift
def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


OVERRIDE = {
    0.48: _w(("Ya", 0.55, 0.72), ("Allah,", 0.72, 0.94), ("bantal", 1.00, 1.32), ("ni", 1.34, 1.54),
             ("paling", 1.54, 1.86), ("banyak", 1.86, 2.18), ("terjual", 2.18, 2.56), ("dalam", 2.58, 2.84),
             ("live", 2.84, 3.02), ("saya", 3.02, 3.38), ("tau.", 3.38, 3.60), ("MashaAllah,", 3.76, 4.14),
             ("dia", 4.16, 4.36), ("antara", 4.36, 4.66), ("yang", 4.66, 4.82), ("paling", 4.82, 5.14),
             ("ramai", 5.14, 5.36), ("orang", 5.36, 5.58), ("repeat", 5.58, 5.90), ("order.", 5.90, 6.30)),
    12.54: _w(("Memang", 12.56, 12.82), ("orang", 12.82, 13.12), ("borong", 13.12, 13.40), ("sampai", 13.40, 13.80),
              ("7", 13.80, 14.28), ("-10", 14.30, 14.72), ("biji.", 14.74, 15.00)),
    17.12: _w(("Dah", 17.16, 17.32), ("lah", 17.32, 17.48), ("comel,", 17.48, 17.84), ("ada", 17.92, 18.06),
              ("senyum,", 18.06, 18.48), ("ada", 18.56, 18.72), ("smile", 18.72, 19.00), ("macam", 19.00, 19.28),
              ("ni.", 19.28, 19.56)),
    6.62: _w(("Saiz", 6.66, 6.86), ("dia", 6.86, 7.04), ("45cm.", 7.06, 7.96)),
    19.72: _w(("Letak", 19.75, 19.96), ("dekat", 19.96, 20.18), ("kerusi", 20.18, 20.50), ("ofis,", 20.50, 20.92)),
    21.30: _w(("korang", 21.34, 21.62), ("boleh", 21.62, 21.80), ("buat", 21.80, 22.02), ("sandar,", 22.02, 22.80),
              ("boleh", 22.88, 23.62), ("letak", 23.62, 23.96), ("alas", 23.96, 24.26), ("duduk.", 24.26, 24.90)),
    26.52: _w(("Nak", 26.56, 26.72), ("buat", 26.72, 26.86), ("bantal", 26.86, 27.14), ("peluk", 27.14, 27.40),
              ("dalam", 27.40, 27.62), ("kereta.", 27.64, 28.22), ("Lagi", 28.36, 28.66), ("nak", 28.66, 28.82),
              ("letak", 28.82, 29.08), ("dekat", 29.08, 29.44), ("sofa.", 29.44, 29.92)),
    29.96: _w(("Memang", 30.00, 30.32), ("cantik,", 30.32, 30.96), ("naik", 31.06, 31.26), ("serilah", 31.26, 31.88),
              ("ruang", 31.88, 32.18), ("tamu", 32.18, 32.42), ("rumah", 32.42, 32.66), ("korang", 32.66, 33.02),
              ("tu.", 33.02, 33.12)),
    33.48: _w(("Jangan", 33.60, 33.92), ("lupa", 33.92, 34.18), ("nanti", 34.18, 34.72), ("nak", 34.72, 35.00),
              ("raya,", 35.00, 35.32), ("korang", 35.32, 35.88), ("boleh", 35.88, 36.42), ("grab", 36.42, 36.96),
              ("buat", 36.96, 37.34), ("hiasan.", 37.34, 37.80)),
    39.76: _w(("Dan", 39.82, 40.04), ("ada", 40.04, 40.32), ("yang", 40.32, 40.44), ("buat", 40.44, 40.64),
              ("hadiah.", 40.64, 41.06)),
    42.72: _w(("Waktu", 42.76, 43.16), ("sempena", 43.16, 43.64), ("Hari", 43.64, 43.84), ("Guru", 43.84, 44.12),
              ("itu,", 44.12, 44.40), ("sampai", 44.40, 45.10)),
    45.16: _w(("ada", 45.16, 45.30), ("yang", 45.30, 45.40), ("beli", 45.40, 45.56), ("sampai", 45.56, 45.80),
              ("17", 45.80, 46.30), ("biji", 46.30, 46.66), ("pun", 46.66, 46.84), ("ada!", 46.84, 47.58)),
    49.62: _w(("Korang,", 50.06, 50.22), ("tengok", 50.22, 50.38), ("dekat", 50.38, 50.56),
              ("beg", 50.58, 50.78), ("kuning.", 50.78, 51.30)),
}
DROP = []
HILITE = {"TERJUAL", "REPEAT", "ORDER", "BORONG", "7-10", "COMEL", "SENYUM", "SMILE", "45CM", "OFIS", "SANDAR",
          "ALAS", "DUDUK", "PELUK", "KERETA", "SOFA", "CANTIK", "RUANG", "TAMU", "RAYA", "HIASAN", "HADIAH",
          "GURU", "17", "BEG", "KUNING", "LIVE"}


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
                if txt.startswith("-") and out and out[-1]["clip"] == id(c):   # "7" + "-10" -> "7-10"
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


# palette from the pillows: lilac, rose pink, cream petals, honey face, plum for outlines
PLUM = "&H005E2C4A&"     # #4A2C5E  outlines, label text
LILAC = "&H00E69CB7&"    # #B79CE6  lilac flower
LILAC_D = "&H00D16B8E&"  # #8E6BD1  deeper lilac
PINK = "&H00C29BF4&"     # #F49BC2  pink flower
ROSE = "&H009A6AF0&"     # #F06A9A  rose (blush cheeks)
CREAM = "&H00E6F6FF&"    # #FFF6E6  cream petals
HONEY = "&H003CC9FF&"    # #FFC93C  honey face (sung caption colour)
WHITE = "&H00FFFFFF&"

ASS_HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Fredoka,56,&H003CC9FF,&H00FFFFFF,&H005E2C4A,&H605E2C4A,-1,0,0,0,100,100,0,0,1,5,2,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Lab,Fredoka,64,&H005E2C4A,&H000000FF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,1,0,1,0,0,5,40,40,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,&H005E2C4A,&H505E2C4A,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def captions(words):
    """Refresh: karaoke sweep. Each 3-word line appears at once; the honey fill sweeps across each word as it
    is spoken (\\kf). Keywords wait in pink before they fill, everything else in white."""
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
        start = ch[0]["s"]
        end = ch[-1]["e"] + 0.15
        if i + 1 < len(chunks):
            end = min(end, chunks[i + 1][0]["s"])
        parts = []
        for j, x in enumerate(ch):
            nxt = ch[j + 1]["s"] if j + 1 < len(ch) else x["e"]
            cs = max(1, int(round((nxt - (x["s"] if j else start)) * 100)))
            t = x["w"].upper().strip(",.")
            unsung = PINK if t.strip(",.?!") in HILITE else WHITE
            parts.append(r"{\kf%d\2c%s}%s" % (cs, unsung, t))
        pop = r"{\fscx88\fscy88\t(0,100,\fscx100\fscy100)}"
        ev.append(f"Dialogue: 2,{ts(start)},{ts(end)},Cap,,0,0,0,,{pop}" + " ".join(parts))
    return ev


_FIT_FONTS = {}


def text_w(text, size):
    f = _FIT_FONTS.setdefault(size, ImageFont.truetype(FONT_FILE, size))
    return f.getlength(text.replace("*", "")) * ASS_PER_PIL


def fit_size(text, size, max_w=SAFE_W - 110):   # bubble padding + pop overshoot
    """Shrink a label's font size so the bubble stays inside the safe area."""
    w = text_w(text, size)
    return size if w <= max_w else int(size * max_w / w)


def _bubble_path(bw, bh, tail, side):
    """Rounded rectangle centred on (0,0) with a speech-bubble tail on the bottom edge."""
    r = min(26, bh / 2)
    x0, y0, x1, y1 = -bw / 2, -bh / 2, bw / 2, bh / 2
    k = 0.55 * r
    tx = {"l": -bw * 0.22, "r": bw * 0.22, "c": 0}[side]
    tip = tx + (-14 if side == "l" else 14 if side == "r" else 0)
    p = [f"m {x0 + r:.0f} {y0:.0f}", f"l {x1 - r:.0f} {y0:.0f}",
         f"b {x1 - r + k:.0f} {y0:.0f} {x1:.0f} {y0 + r - k:.0f} {x1:.0f} {y0 + r:.0f}",
         f"l {x1:.0f} {y1 - r:.0f}",
         f"b {x1:.0f} {y1 - r + k:.0f} {x1 - r + k:.0f} {y1:.0f} {x1 - r:.0f} {y1:.0f}",
         f"l {tx + 16:.0f} {y1:.0f} l {tip:.0f} {y1 + tail:.0f} l {tx - 16:.0f} {y1:.0f}",
         f"l {x0 + r:.0f} {y1:.0f}",
         f"b {x0 + r - k:.0f} {y1:.0f} {x0:.0f} {y1 - r + k:.0f} {x0:.0f} {y1 - r:.0f}",
         f"l {x0:.0f} {y0 + r:.0f}",
         f"b {x0:.0f} {y0 + r - k:.0f} {x0 + r - k:.0f} {y0:.0f} {x0 + r:.0f} {y0:.0f}"]
    return " ".join(p)


def label(t0, t1, text, y=250, bg=WHITE, fg=PLUM, hi=ROSE, side="l", rot=0, layer=5, x=CX, size=62, max_w=SAFE_W - 110):
    """Refresh: speech-bubble label (rounded bubble + tail pointing down at the pillows), no tilt by default.
    *word* is drawn in the highlight colour. Bubble and text pop together (scale around the same origin)."""
    size = fit_size(text, size, max_w)
    bw = text_w(text, size) + 56
    bh = size * 1.02 + 26
    tail = 18
    parts = text.split("*")
    rich = "".join(p if i % 2 == 0 else rf"{{\c{hi}}}{p}{{\c{fg}}}" for i, p in enumerate(parts))
    anim = (r"\fscx0\fscy0\t(0,130,\fscx112\fscy112)\t(130,230,\fscx100\fscy100)\fad(0,140)"
            rf"\org({x},{y})\frz{rot}")
    shape = (f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
             rf"{{\an7\pos({x},{y}){anim}\c{bg}\3c{PLUM}\bord3.5\shad4\4c&H70301A30&\p1}}"
             + _bubble_path(bw, bh, tail, side) + r"{\p0}")
    txt = (f"Dialogue: {layer + 1},{ts(t0)},{ts(t1)},Lab,,0,0,0,,"
           rf"{{\an5\pos({x},{y}){anim}\fs{size}\c{fg}}}{rich}")
    return shape + "\n" + txt


def wipe(t0, d=0.32, col=LILAC, layer=9):
    """Refresh: a quick lilac wipe sweeping left -> right (replaces the full-screen flash)."""
    return (f"Dialogue: {layer},{ts(t0)},{ts(t0 + d)},Shape,,0,0,0,,"
            rf"{{\an7\move({-W},0,{W},0)\c{col}\1a&H50&\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")


def _circle(cx, cy, r):
    k = 0.552 * r
    return (f"m {cx:.0f} {cy - r:.0f} b {cx + k:.0f} {cy - r:.0f} {cx + r:.0f} {cy - k:.0f} {cx + r:.0f} {cy:.0f} "
            f"b {cx + r:.0f} {cy + k:.0f} {cx + k:.0f} {cy + r:.0f} {cx:.0f} {cy + r:.0f} "
            f"b {cx - k:.0f} {cy + r:.0f} {cx - r:.0f} {cy + k:.0f} {cx - r:.0f} {cy:.0f} "
            f"b {cx - r:.0f} {cy - k:.0f} {cx - k:.0f} {cy - r:.0f} {cx:.0f} {cy - r:.0f}")


PETALS = " ".join(_circle(13 * math.cos(a), 13 * math.sin(a), 10) for a in
                  [i * 2 * math.pi / 6 - math.pi / 2 for i in range(6)])
CENTRE = _circle(0, 0, 8)


def blooms(t0, t1, pts, layer=4):
    """Refresh motif: tiny six-petal flowers that spin in around a label (pillow colours)."""
    ev = []
    cols = [LILAC, PINK, CREAM]
    for k, (x, y, sc) in enumerate(pts):
        d = 70 * k
        anim = (rf"\an5\pos({x},{y})\fscx0\fscy0\frz-120\t({d},{d + 220},\fscx{sc}\fscy{sc}\frz0)"
                rf"\t({d + 220},{int((t1 - t0) * 1000)},\frz40)\fad(0,150)")
        ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
                  rf"{{{anim}\c{cols[k % 3]}\3c{WHITE}\bord2\p1}}{PETALS}{{\p0}}")
        ev.append(f"Dialogue: {layer + 1},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
                  rf"{{{anim}\c{HONEY}\bord0\p1}}{CENTRE}{{\p0}}")
    return ev


def graphics():
    ev, stickers, sfx = [], [], []
    # progress bar: lilac track that fills with honey + a little cream bead riding the front
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{LILAC}\1a&H40&\p1}}m 0 0 l {W} 0 {W} 9 0 9{{\p0}}")
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{HONEY}\fscx0\t(0,{int(TOTAL * 1000)},\fscx100)\p1}}m 0 0 l {W} 0 {W} 9 0 9{{\p0}}")

    def lab(s0, s1, text, sound="plink", vol=0.45, **kw):
        ev.append(label(tl(s0), tl(s1), text, **kw))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def stk(em, s0, s1, x, y, size=100):
        stickers.append((em, tl(s0), tl(s1), x, y, size))

    def bstk(em, t0, t1, x, y, size=100):
        stickers.append((em, t0, t1, x, y, size))

    SL, SR, SY = 90, 555, 180     # stickers sit above the bubbles, clear of the pillows

    # ---- HOOK: best seller in my live -> most repeat orders
    lab(1.00, 3.60, "PALING *BANYAK TERJUAL*!", bg=WHITE, fg=PLUM, hi=ROSE, side="l", size=62, sound="bloop")
    stk("🏆", 1.03, 3.60, SR, SY - 40, 100)
    ev += blooms(tl(1.00), tl(3.60), [(80, 330, 100), (600, 335, 80)])
    ev.append(wipe(tl(3.70)))
    sfx.append(("whoosh", tl(3.64), 0.35))
    lab(3.76, 6.30, "RAMAI *REPEAT ORDER*!", bg=HONEY, fg=PLUM, hi=WHITE, side="r", size=64, sound="ding", vol=0.4)
    stk("🔁", 3.79, 6.30, SL, SY - 40, 95)

    # ---- social proof
    lab(12.82, 15.00, "ORANG *BORONG* 7-10 BIJI!", bg=LILAC_D, fg=WHITE, hi=HONEY, side="r", size=60)
    stk("🛍️", 12.85, 15.00, SL, SY - 40, 95)

    # ---- the faces
    ev.append(wipe(tl(17.14), col=PINK))
    sfx.append(("whoosh", tl(17.08), 0.3))
    lab(17.16, 19.56, "COMEL, *ADA SENYUM*!", bg=WHITE, fg=PLUM, hi=ROSE, side="l", size=64, sound="sparkle", vol=0.35)
    stk("😊", 17.19, 19.56, SR, SY - 40, 105)
    ev += blooms(tl(17.16), tl(19.56), [(85, 330, 90), (590, 330, 100), (120, 175, 70)])
    lab(6.66, 7.96, "SAIZ *45CM*", bg=PINK, fg=PLUM, hi=WHITE, side="c", size=66)
    stk("📏", 6.69, 7.96, SR, SY - 40, 90)

    # ---- uses
    lab(19.75, 20.92, "KERUSI *OFIS*", bg=WHITE, fg=PLUM, hi=LILAC_D, side="l", size=66)
    stk("💼", 19.78, 20.92, SR, SY - 40, 95)
    lab(21.34, 22.80, "BUAT *SANDAR*", bg=LILAC_D, fg=WHITE, hi=HONEY, side="r", size=66)
    stk("😌", 21.37, 22.80, SL, SY - 40, 95)
    lab(23.62, 24.90, "*ALAS* DUDUK", bg=WHITE, fg=PLUM, hi=ROSE, side="l", size=66)
    stk("🪑", 23.65, 24.90, SR, SY - 40, 95)
    lab(26.56, 28.22, "PELUK DALAM *KERETA*", bg=PINK, fg=PLUM, hi=WHITE, side="r", size=60)
    stk("🚗", 26.59, 28.22, SL, SY - 40, 95)
    lab(28.36, 29.92, "LETAK ATAS *SOFA*", bg=WHITE, fg=PLUM, hi=LILAC_D, side="l", size=62)
    stk("🛋️", 28.39, 29.92, SR, SY - 40, 95)
    ev.append(wipe(tl(30.00), col=HONEY))
    sfx.append(("whoosh", tl(29.94), 0.3))
    lab(30.02, 33.10, "NAIK SERI *RUANG TAMU*!", bg=HONEY, fg=PLUM, hi=WHITE, side="c", size=60, sound="sparkle", vol=0.35)
    stk("✨", 30.05, 33.10, SR, SY - 40, 100)
    ev += blooms(tl(30.02), tl(33.10), [(80, 330, 90), (600, 330, 90)])

    # ---- raya + gifts
    lab(34.72, 37.80, "HIASAN *RAYA*!", bg=LILAC_D, fg=WHITE, hi=HONEY, side="l", size=70, sound="ding", vol=0.4)
    stk("🌙", 34.75, 37.80, SR, SY - 40, 100)
    lab(39.82, 41.06, "BUAT *HADIAH*", bg=WHITE, fg=PLUM, hi=ROSE, side="r", size=68)
    stk("🎁", 39.85, 41.06, SL, SY - 40, 100)
    lab(42.76, 45.10, "SEMPENA *HARI GURU*", bg=PINK, fg=PLUM, hi=WHITE, side="l", size=62)
    stk("🍎", 42.79, 45.10, SR, SY - 40, 95)
    ev.append(wipe(tl(45.20), col=LILAC))
    sfx.append(("impact", tl(45.78), 0.35))
    lab(45.78, 47.58, "ADA BELI *17 BIJI*!", bg=HONEY, fg=PLUM, hi=ROSE, side="r", size=68, sound="ding", vol=0.4)
    stk("😱", 45.81, 47.58, SL, SY - 40, 105)
    ev += blooms(tl(45.78), tl(47.58), [(85, 335, 90), (595, 335, 90), (590, 175, 70)])

    # ---- CTA
    lab(50.22, 51.30, "TENGOK *BEG KUNING*", bg=WHITE, fg=PLUM, hi=ROSE, side="c", size=64, sound="pop", vol=0.5)
    stk("🛒", 50.25, 51.30, SR, SY - 40, 95)

    # ---- end card: cream card with a dashed lilac "stitch" border (refresh: replaces boxes / polaroid / ribbon)
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 8,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{PLUM}\1a&HFF&\t(0,250,\1a&H80&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    x0, x1, y0, y1 = SAFE_L + 25, W - SAFE_R - 25, 250, 800
    r = 34
    k = 0.55 * r
    card = (f"m {x0 + r} {y0} l {x1 - r} {y0} b {x1 - r + k} {y0} {x1} {y0 + r - k} {x1} {y0 + r} "
            f"l {x1} {y1 - r} b {x1} {y1 - r + k} {x1 - r + k} {y1} {x1 - r} {y1} l {x0 + r} {y1} "
            f"b {x0 + r - k} {y1} {x0} {y1 - r + k} {x0} {y1 - r} l {x0} {y0 + r} b {x0} {y0 + r - k} {x0 + r - k} {y0} {x0 + r} {y0}")
    ev.append(f"Dialogue: 9,{ts(e0 + 0.05)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{CREAM}\bord0\shad6\4c&H60301A30&\fad(180,0)\p1}}{card}{{\p0}}")
    # stitches: short lilac dashes just inside the card edge
    st = []
    m = 16
    for xx in range(x0 + r, x1 - r - 10, 30):
        st += [f"m {xx} {y0 + m - 2} l {xx + 16} {y0 + m - 2} l {xx + 16} {y0 + m + 3} l {xx} {y0 + m + 3}",
               f"m {xx} {y1 - m - 3} l {xx + 16} {y1 - m - 3} l {xx + 16} {y1 - m + 2} l {xx} {y1 - m + 2}"]
    for yy in range(y0 + r, y1 - r - 10, 30):
        st += [f"m {x0 + m - 2} {yy} l {x0 + m + 3} {yy} l {x0 + m + 3} {yy + 16} l {x0 + m - 2} {yy + 16}",
               f"m {x1 - m - 3} {yy} l {x1 - m + 2} {yy} l {x1 - m + 2} {yy + 16} l {x1 - m - 3} {yy + 16}"]
    ev.append(f"Dialogue: 10,{ts(e0 + 0.15)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{LILAC_D}\fad(200,0)\p1}}{' '.join(st)}{{\p0}}")
    ev.append(f"Dialogue: 11,{ts(e0 + 0.15)},{ts(TOTAL)},Lab,,0,0,0,,"
              rf"{{\an5\pos({CX},360)\fs{fit_size('BANTAL BUNGA', 64, 430)}\c{PLUM}\fscx0\fscy0"
              r"\t(0,140,\fscx110\fscy110)\t(140,240,\fscx100\fscy100)}BANTAL BUNGA")
    ev.append(f"Dialogue: 11,{ts(e0 + 0.2)},{ts(TOTAL)},Lab,,0,0,0,,"
              rf"{{\an5\pos({CX},430)\fs{fit_size('SENYUM', 76, 430)}\c{ROSE}\fscx0\fscy0"
              r"\t(0,140,\fscx110\fscy110)\t(140,240,\fscx100\fscy100)}SENYUM")
    ev.append(label(e0 + 0.4, TOTAL, "LILAC • PINK • KRIM", bg=LILAC, fg=WHITE, hi=HONEY, y=530, side="c",
                    layer=12, size=40, max_w=380))
    ev.append(label(e0 + 0.65, TOTAL, "KORANG NAK *WARNA MANA*?", bg=WHITE, fg=PLUM, hi=ROSE, y=625, side="c",
                    layer=12, size=40, max_w=380))
    ev.append(label(e0 + 0.9, TOTAL, "TEKAN *BEG KUNING*", bg=HONEY, fg=PLUM, hi=WHITE, y=720, side="c",
                    layer=12, size=50, max_w=380))
    ev += blooms(e0 + 0.2, TOTAL, [(x0 + 40, y0 + 40, 110), (x1 - 40, y0 + 40, 110), (x0 + 40, y1 - 40, 90),
                                  (x1 - 40, y1 - 40, 90)], layer=13)
    bstk("🌸", e0 + 0.2, TOTAL, CX, 205, 90)
    sfx += [("whoosh", e0 - 0.1, 0.4), ("plink", e0 + 0.15, 0.45), ("plink", e0 + 0.4, 0.4), ("pop", e0 + 0.65, 0.4),
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
