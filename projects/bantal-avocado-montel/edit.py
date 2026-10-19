#!/usr/bin/env python3
"""Edit for the round avocado plush pillow (bantal avocado, "bulat montel") TikTok video.

All overlays stay inside the TikTok safe zone (SAFE_* below): nothing under the
right-hand profile/like/comment/share column, the bottom caption area or the top tabs.

Needs the Fredoka Bold font (fonts/Fredoka-Bold.ttf, SIL OFL) installed, e.g. in ~/.fonts.

Usage: python3 edit.py <proxy.mp4> <transcript.json> <sfx_dir> <out_dir> [--final]
  preview: 720x1280 proxy -> preview.mp4;  --final: 1080x1920 master -> final.mp4
  --audio-only: re-mix voice + SFX onto the existing render -> *_voice.mp4

All times in BLOCKS are source times of the original clip (same timeline as
the proxy). The script builds:
  base.mp4     - cut/zoomed video + cleaned voice + SFX
  overlay.ass  - captions, labels, rings, leaves, progress bar, end card
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
# Single source clip IMG_2933 (outdoors, sitting by a flower bed): one round avocado plush with a face,
# brown seed and little arms/legs. She "picks" it from the plants at the start.
# v: list of (src_in, src_out, speed, zoom); a zoom change inside a block is a punch-in on the beat
# a: 'same' (follow v at speed 1), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK (already the opening): "Peminat avocado, korang ada ke avocado yang tuuut... kat sini kita ada
    #  avocado? | Baru fresh-fresh daripada pokok dia."  (she pulls it out of the plants: the joke)
    dict(name="hook", a="same", v=[(0.00, 3.35, 1, 1.0), (3.35, 6.02, 1, 1.08), (6.02, 8.68, 1, 1.0)]),
    # (cut 8.7-14.4: "Ok yang ni, ya Allah harga dia, korang mesti terkejut tengok harga dia" - no price talk)
    # "Ya Allah dia lah gebu macam ni, dia tak nipis tau."
    dict(name="gebu", a="same", v=[(14.45, 16.40, 1, 1.0), (16.40, 17.55, 1, 1.08)]),
    # "Bentuk dia bentuk avocado yang bulat montel macam ni, | size 30cm."
    dict(name="bentuk", a="same", v=[(17.55, 20.70, 1, 1.0), (20.70, 21.82, 1, 1.08)]),
    # ("Harga jimat," cut) "korang boleh buat hadiah, | boleh beli untuk bantal peluk baby ke."
    dict(name="hadiah", a="same", v=[(23.30, 25.05, 1, 1.0), (25.05, 28.00, 1, 1.06)]),
    # "Sebab dia lembut dan dia ada zip, | korang nak basuh ke apa ke senang."  (back of the plush shown)
    dict(name="zip", a="same", v=[(28.80, 31.45, 1, 1.0), (31.45, 33.60, 1, 1.06)]),
    # ("Nah ok," cut) "Ni untuk avocado 30cm." - plays under the end card ("tunggu-tunggu..." after it cut)
    dict(name="end", a="same", v=[(34.32, 37.95, 1, 1.0)]),
]

FIX = {"ini": "ni", "Ini": "Ni", "bantai": "bantal", "avokadu": "avocado", "avokadu,": "avocado,",
       "avokadu?": "avocado?", "Avokadu": "Avocado", "avokado": "avocado", "montan": "montel", "Okey": "Okay"}
# hand-checked words where Whisper drifted or misheard (re-transcribed per clip)
def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


OVERRIDE = {
    0.00: _w(("Peminat", 0.00, 0.74), ("avocado,", 0.74, 1.80), ("korang", 2.02, 2.26), ("ada", 2.26, 2.46),
             ("ke", 2.46, 2.58), ("avocado", 2.58, 3.08), ("yang", 3.08, 3.34)),
    3.35: _w(("tuuu...", 3.38, 4.30), ("kat", 4.40, 4.52), ("sini", 4.52, 4.78), ("kita", 4.78, 4.96),
             ("ada", 4.96, 5.14), ("avocado?", 5.14, 5.86)),
    6.02: _w(("Baru", 6.18, 6.58), ("fresh", 6.60, 7.02), ("-fresh", 7.02, 7.32), ("daripada", 7.32, 7.80),
             ("pokok", 7.80, 8.36), ("dia.", 8.36, 8.62)),
    14.45: _w(("Ya", 14.45, 14.71), ("Allah,", 14.71, 14.90), ("dia", 14.93, 14.97), ("lah", 14.97, 15.13),
              ("gebu", 15.13, 15.41), ("macam", 15.41, 15.73), ("ni.", 15.73, 16.03)),
    16.40: _w(("Dia", 16.45, 16.67), ("tak", 16.67, 16.83), ("nipis", 16.83, 17.25), ("tau.", 17.25, 17.48)),
    17.55: _w(("Bentuk", 17.62, 18.32), ("dia", 18.32, 18.40), ("bentuk", 18.40, 18.66), ("avocado", 18.66, 19.10),
              ("yang", 19.10, 19.30), ("bulat", 19.30, 19.58), ("montel", 19.58, 19.92), ("macam", 19.92, 20.26),
              ("ni,", 20.26, 20.66)),
    20.70: _w(("size", 20.76, 20.98), ("30cm.", 20.98, 21.70)),
    23.30: _w(("Korang", 23.44, 23.64), ("boleh", 23.64, 23.80), ("buat", 23.80, 24.02), ("hadiah,", 24.02, 24.94)),
    25.05: _w(("boleh", 25.10, 25.26), ("beli", 25.26, 25.64), ("untuk", 25.64, 26.40), ("bantal", 26.48, 26.78),
              ("peluk", 26.78, 27.02), ("baby", 27.02, 27.38), ("ke.", 27.38, 27.90)),
    28.80: _w(("Sebab", 28.80, 29.12), ("dia", 29.12, 29.52), ("lembut", 29.52, 30.10), ("dan", 30.10, 30.60),
              ("dia", 30.60, 30.76), ("ada", 30.76, 30.96), ("zip,", 30.96, 31.24)),
    31.45: _w(("korang", 31.58, 31.82), ("nak", 31.82, 31.96), ("basuh", 31.96, 32.42), ("ke", 32.42, 32.56),
              ("apa", 32.56, 32.70), ("ke,", 32.70, 32.90), ("senang.", 32.90, 33.52)),
    34.32: _w(("Ni", 34.62, 34.72), ("untuk", 34.72, 35.44), ("avocado", 35.44, 36.00), ("30cm.", 36.00, 37.70)),
}
DROP = []
HILITE = {"PEMINAT", "AVOCADO", "AVOCADO?", "FRESH", "FRESH-FRESH", "POKOK", "GEBU", "NIPIS", "BULAT", "MONTEL",
          "30CM", "HADIAH", "BANTAL", "PELUK", "BABY", "LEMBUT", "ZIP", "BASUH", "SENANG"}

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




# palette from the plush: deep leaf green for text/outline, avocado skin green, light flesh green, pale flesh,
# brown seed, pink cheeks, cream, butter yellow for the CTA
DEEP = bgr("#2F4A1E")
SKIN = bgr("#5C8A2E")
FLESH = bgr("#C5E25C")
PALE = bgr("#EEF6C8")
SEED = bgr("#7B4A2C")
CHEEK = bgr("#F48FA0")
CREAM = bgr("#FFF8E6")
BUTTER = bgr("#FFD54F")
WHITE = "&H00FFFFFF&"
KEY = bgr("#FFE08A")          # caption keywords: soft butter

ASS_HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Fredoka,58,&H00FFFFFF,&H000000FF,{DEEP[:-1]},&H701E4A2F,-1,0,0,0,100,100,0,0,1,5,2,2,{SAFE_L},{SAFE_R},{SAFE_B + 20},1
Style: Label,Fredoka,60,{DEEP[:-1]},&H000000FF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,{DEEP[:-1]},&H701E4A2F,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: ShapeC,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

_FONTS = {}


def text_w(text, size):
    """libass width of Fredoka text at an ASS font size."""
    f = _FONTS.setdefault(size, ImageFont.truetype(FONT_FILE, size))
    return f.getlength(text) * ASS_PER_PIL


def norm(path):
    """libass aligns a drawing as if its bbox started at (0,0), so shift every path to min x/y = 0;
    with \\an5 the drawing is then centred on \\pos (paths here are built centred on 0,0)."""
    toks = path.split()
    nums = [(i, float(t)) for i, t in enumerate(toks) if t not in "mlbn"]
    xs = [v for k, (i, v) in enumerate(nums) if k % 2 == 0]
    ys = [v for k, (i, v) in enumerate(nums) if k % 2 == 1]
    mx, my = min(xs), min(ys)
    for k, (i, v) in enumerate(nums):
        toks[i] = f"{v - (mx if k % 2 == 0 else my):.1f}".rstrip("0").rstrip(".")
    return " ".join(toks)


def rrect(w, h, r):
    """Rounded rectangle path, w x h, centred on \\pos when drawn with \\an5."""
    x0, y0, x1, y1, k = -w / 2, -h / 2, w / 2, h / 2, 0.55 * r
    return norm(
        f"m {x0 + r:.0f} {y0:.0f} l {x1 - r:.0f} {y0:.0f} b {x1 - r + k:.0f} {y0:.0f} {x1:.0f} {y0 + r - k:.0f} {x1:.0f} {y0 + r:.0f} "
        f"l {x1:.0f} {y1 - r:.0f} b {x1:.0f} {y1 - r + k:.0f} {x1 - r + k:.0f} {y1:.0f} {x1 - r:.0f} {y1:.0f} "
        f"l {x0 + r:.0f} {y1:.0f} b {x0 + r - k:.0f} {y1:.0f} {x0:.0f} {y1 - r + k:.0f} {x0:.0f} {y1 - r:.0f} "
        f"l {x0:.0f} {y0 + r:.0f} b {x0:.0f} {y0 + r - k:.0f} {x0 + r - k:.0f} {y0:.0f} {x0 + r:.0f} {y0:.0f}")


def stitches(w, h, r, dash=13, gap=9, th=3.5):
    """Dashed 'stitch' line along the straight edges of a rounded rect (centred), as one drawing."""
    out = []
    x0, y0, x1, y1 = -w / 2, -h / 2, w / 2, h / 2
    for (ax, ay, bx, by) in [(x0 + r, y0, x1 - r, y0), (x0 + r, y1, x1 - r, y1),
                             (x0, y0 + r, x0, y1 - r), (x1, y0 + r, x1, y1 - r)]:
        L = abs(bx - ax) + abs(by - ay)
        n = max(1, int((L + gap) // (dash + gap)))
        pad = (L - (n * dash + (n - 1) * gap)) / 2
        for i in range(n):
            u0 = (pad + i * (dash + gap)) / L
            u1 = (pad + i * (dash + gap) + dash) / L
            sx, sy = ax + (bx - ax) * u0, ay + (by - ay) * u0
            ex, ey = ax + (bx - ax) * u1, ay + (by - ay) * u1
            if ay == by:
                out.append(f"m {sx:.0f} {sy - th / 2:.1f} l {ex:.0f} {sy - th / 2:.1f} {ex:.0f} {sy + th / 2:.1f} {sx:.0f} {sy + th / 2:.1f}")
            else:
                out.append(f"m {sx - th / 2:.1f} {sy:.0f} l {sx + th / 2:.1f} {sy:.0f} {sx + th / 2:.1f} {ey:.0f} {sx - th / 2:.1f} {ey:.0f}")
    return norm(" ".join(out))



def circle(r):
    k = 0.5523 * r
    return norm(f"m 0 {-r:.0f} b {k:.0f} {-r:.0f} {r:.0f} {-k:.0f} {r:.0f} 0 b {r:.0f} {k:.0f} {k:.0f} {r:.0f} 0 {r:.0f} "
                f"b {-k:.0f} {r:.0f} {-r:.0f} {k:.0f} {-r:.0f} 0 b {-r:.0f} {-k:.0f} {-k:.0f} {-r:.0f} 0 {-r:.0f}")


def captions(words):
    """3-word chunks. Refresh: the active word pops bigger (bounce) in avocado green on top of the line."""
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
    base_y = H - (SAFE_B + 20)                 # bottom of the caption line (\an2)
    for i, ch in enumerate(chunks):
        end = ch[-1]["e"] + 0.15
        if i + 1 < len(chunks):
            end = min(end, chunks[i + 1][0]["s"])
        toks = [x["w"].upper().strip(",.") for x in ch]
        size = 58
        while text_w(" ".join(toks), size) + text_w(" ", size) * 1.3 * (len(toks) - 1) + 0.14 * text_w(max(toks, key=len), size) > SAFE_W - 60 and size > 36:   # room for the bounced word
            size -= 2
        sp = text_w(" ", size) * 2.3
        widths = [text_w(t, size) for t in toks]
        x = CX - (sum(widths) + sp * (len(toks) - 1)) / 2
        xs = []
        for wd in widths:
            xs.append(x + wd / 2)
            x += wd + sp
        cy = base_y - size * 0.6
        for j, w in enumerate(ch):
            ws = w["s"] if j else min(w["s"], ch[0]["s"])
            we = ch[j + 1]["s"] if j + 1 < len(ch) else end
            for k, t in enumerate(toks):
                fade = r"\fad(60,0)" if j == 0 else ""
                if k == j:
                    ev.append(f"Dialogue: 3,{ts(ws)},{ts(we)},Cap,,0,0,0,,"
                              rf"{{\an5\pos({xs[k]:.0f},{cy:.0f})\fs{size}\c{FLESH}\3c{DEEP}\bord6"
                              rf"\fscx100\fscy100\t(0,80,\fscx128\fscy128)\t(80,190,\fscx114\fscy114)}}{t}")
                else:
                    col = KEY if (t.strip("-?!") in HILITE or t in HILITE) else "&H00FFFFFF&"
                    ev.append(f"Dialogue: 2,{ts(ws)},{ts(we)},Cap,,0,0,0,,"
                              rf"{{\an5\pos({xs[k]:.0f},{cy:.0f})\fs{size}\c{col}{fade}}}{t}")
    return ev


def fit_size(text, size, max_w):
    w = text_w(text.replace("*", ""), size)
    return size if w <= max_w else int(size * max_w / w)


def label(t0, t1, text, y=235, col=DEEP, box=PALE, hi=SEED, badge=SEED, layer=5, size=60, emoji=None, stickers=None):
    """Refresh: a 'half avocado' label - pill in flesh/pale green with a round brown 'seed' badge on the left
    that holds the emoji (Pillow sticker). Slides in from the left with a small squash, no tilt."""
    lines = text.replace("*", "").split("|")
    bh0 = len(lines) * size * 1.02 + 30
    D = min(bh0 * 0.9 + 16, 118)                       # seed badge diameter
    size = min(fit_size(ln, size, SAFE_W - D - 70) for ln in lines)
    tw = max(text_w(ln, size) for ln in lines)
    bh = len(lines) * size * 1.02 + 30
    TW = D + 14 + tw + 34                                # badge + gap + text + right padding
    left = CX - TW / 2
    ccx = left + D / 2
    pl, pr = left + D * 0.45, left + TW
    pcx, pw = (pl + pr) / 2, pr - pl
    tcx = (left + D + 14 + pr - 34) / 2 + 0
    parts = text.replace("|", r"\N").split("*")
    txt = "".join(p if i % 2 == 0 else rf"{{\c{hi}}}{p}{{\c{col}}}" for i, p in enumerate(parts))
    ms = 190

    def mv(px, py):
        return (rf"\an5\move({px - 70:.0f},{py},{px:.0f},{py},0,{ms})\fscx88\t(0,{ms},\fscx106)"
                rf"\t({ms},{ms + 90},\fscx100)\fad(90,150)")
    ev = [
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{{{mv(pcx + 4, y + 7)}\\c{DEEP}\\1a&H88&\\blur3\\p1}}{rrect(pw, bh, bh / 2)}{{\\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{{{mv(pcx, y)}\\c{box}\\3c&HFFFFFF&\\bord4\\p1}}{rrect(pw, bh, bh / 2)}{{\\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},ShapeC,,0,0,0,,{{{mv(ccx, y)}\\c{badge}\\3c{CREAM}\\bord5\\p1}}{circle(D / 2)}{{\\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},Label,,0,0,0,,{{{mv(tcx, y)}\\fs{size}\\c{col}}}{txt}",
    ]
    if emoji and stickers is not None:
        stickers.append((emoji, t0 + 0.12, t1, ccx, y, D * 0.62))
    return ev


LEAF = norm("m 0 -20 b 13 -9 13 9 0 20 b -13 9 -13 -9 0 -20")
VEIN = norm("m -1.5 -14 l 1.5 -14 1.5 14 -1.5 14")


def leaves(t0, y=235, layer=4, spots=((-255, -30), (250, -45), (-230, 55), (245, 60))):
    """Refresh motif: little avocado leaves flutter out from a label and drift down while spinning."""
    ev = []
    for i, (dx, dy) in enumerate(spots):
        x, yy = CX + dx * 0.9, y + dy
        d0 = 70 * i
        drift = 60 if i % 2 else -60
        rot0, rot1 = (35, 160) if i % 2 else (-35, -160)
        for shape, col, bord in ((LEAF, FLESH if i % 2 else SKIN, 2), (VEIN, DEEP, 0)):
            ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t0 + 1.3)},ShapeC,,0,0,0,,"
                      rf"{{\move({x:.0f},{yy:.0f},{x + drift * 0.4:.0f},{yy + 70:.0f},{d0},1300)\c{col}\3c{DEEP}\bord{bord}"
                      rf"\frz{rot0}\fscx0\fscy0\t({d0},{d0 + 150},\fscx115\fscy115)\t({d0 + 150},{d0 + 250},\fscx100\fscy100)"
                      rf"\t({d0},1300,\frz{rot1})\fad(0,300)\p1}}{shape}{{\p0}}")
    return ev


def ring(t0, layer=9):
    """Refresh transition: a brown 'seed' ring bursts out from the centre with a quick pale-green wash."""
    return [
        f"Dialogue: {layer},{ts(t0)},{ts(t0 + 0.2)},Shape,,0,0,0,,"
        rf"{{\an7\pos(0,0)\c{PALE}\1a&H50&\t(0,200,\1a&HFF&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}",
        f"Dialogue: {layer},{ts(t0)},{ts(t0 + 0.38)},ShapeC,,0,0,0,,"
        rf"{{\pos({CX},{int(H * 0.42)})\1a&HFF&\3c{SEED}\bord14\fscx15\fscy15\t(0,380,\fscx420\fscy420\bord4)"
        rf"\fad(0,160)\p1}}{circle(80)}{{\p0}}",
    ]


PEAR = norm("m 0 -230 b 92 -230 112 -112 150 -14 b 202 108 152 230 0 230 "
            "b -152 230 -202 108 -150 -14 b -112 -112 -92 -230 0 -230")


def graphics():
    ev, stickers, sfx = [], [], []
    # progress bar (retention): skin-green track, flesh fill, and a little brown seed riding the front
    ms = int(TOTAL * 1000)
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{SKIN}\1a&H40&\p1}}m 0 0 l {W} 0 {W} 10 0 10{{\p0}}")
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{FLESH}\clip(0,0,0,10)\t(0,{ms},\clip(0,0,{W},10))\p1}}m 0 0 l {W} 0 {W} 10 0 10{{\p0}}")
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},ShapeC,,0,0,0,,"
              rf"{{\move(0,6,{W},6,0,{ms})\c{SEED}\3c{CREAM}\bord2\p1}}{circle(8)}{{\p0}}")

    def lab(s0, s1, text, sound="pop", vol=0.5, leafy=False, emoji=None, **kw):
        ev.extend(label(tl(s0), tl(s1), text, emoji=emoji, stickers=stickers, **kw))
        if leafy:
            ev.extend(leaves(tl(s0), y=kw.get("y", 235)))
            sfx.append(("rustle", tl(s0) + 0.05, 0.45))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def punch(src, sound="plop", vol=0.6):
        t0 = tl(src)
        ev.extend(ring(t0))
        sfx.append((sound, t0 - 0.03, vol))

    # ---- HOOK: avocado fans? -> picked fresh from the tree (the plush comes out of the plants)
    lab(0.04, 1.80, "*PEMINAT* AVOCADO?", emoji="🥑", sound="bloop", vol=0.5)
    lab(2.02, 3.34, "KORANG ADA KE?", box=FLESH, hi=SEED, emoji="🤔", sound="pop", vol=0.45)
    punch(3.35)
    lab(4.40, 5.86, "KAT SINI *ADA*!", box=PALE, hi=CHEEK, emoji="👇", sound="pop", vol=0.45)
    punch(6.02, sound="rustle", vol=0.6)
    lab(6.18, 8.62, "BARU PETIK|*DARI POKOK*!", box=FLESH, hi=SEED, emoji="🌳", leafy=True, sound="sparkle", vol=0.35)

    # ---- soft + thick
    lab(14.50, 16.03, "*GEBU*-NYA!", box=PALE, hi=CHEEK, emoji="☁️", sound="puff", vol=0.7)
    punch(16.40)
    lab(16.45, 17.50, "TAK *NIPIS* TAU", box=FLESH, hi=SEED, emoji="👌", sound="pop", vol=0.45)

    # ---- shape + size
    lab(17.62, 20.66, "BULAT *MONTEL*", box=PALE, hi=SEED, emoji="🥑", leafy=True, sound="bloop", vol=0.5)
    punch(20.70)
    lab(20.76, 21.80, "SIZE *30CM*", box=FLESH, hi=SEED, emoji="📏", sound="click", vol=0.5)

    # ---- gift + hug
    lab(23.44, 24.98, "BOLEH BUAT *HADIAH*", box=PALE, hi=CHEEK, emoji="🎁", sound="sparkle", vol=0.35)
    punch(25.05)
    lab(25.10, 27.95, "BANTAL PELUK|*BABY*", box=FLESH, hi=SEED, emoji="👶", leafy=True, sound="puff", vol=0.6)

    # ---- zip + washable
    lab(28.82, 31.40, "LEMBUT & ADA *ZIP*", box=PALE, hi=SEED, emoji="🤐", sound="zip", vol=0.45)
    punch(31.45)
    lab(31.58, 33.55, "*SENANG* BASUH", box=FLESH, hi=SEED, emoji="🫧", sound="pop", vol=0.45)

    # ---- end card (refresh): a big avocado half (skin, flesh, seed) with stacked half-avocado labels
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 6,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{DEEP}\1a&HFF&\t(0,250,\1a&H70&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    cy = 440
    pop = r"\fscx0\fscy0\t(0,200,\fscx108\fscy108)\t(200,300,\fscx100\fscy100)"
    ev.append(f"Dialogue: 7,{ts(e0)},{ts(TOTAL)},ShapeC,,0,0,0,,"
              rf"{{\pos({CX + 6},{cy + 10})\c{DEEP}\1a&H80&\blur5{pop}\p1}}{PEAR}{{\p0}}")
    ev.append(f"Dialogue: 7,{ts(e0)},{ts(TOTAL)},ShapeC,,0,0,0,,"
              rf"{{\pos({CX},{cy})\c{SKIN}\3c&HFFFFFF&\bord5{pop}\p1}}{PEAR}{{\p0}}")
    ev.append(f"Dialogue: 7,{ts(e0)},{ts(TOTAL)},ShapeC,,0,0,0,,"
              rf"{{\pos({CX},{cy + 8})\c{FLESH}\fscx0\fscy0\t(0,200,\fscx95\fscy97)\t(200,300,\fscx88\fscy90)"
              rf"\p1}}{PEAR}{{\p0}}")
    ev.append(f"Dialogue: 8,{ts(e0 + 0.35)},{ts(TOTAL)},ShapeC,,0,0,0,,"
              rf"{{\pos({CX},{cy + 95})\c{SEED}\3c{CREAM}\bord4\fscx0\fscy0\t(0,160,\fscx115\fscy115)"
              rf"\t(160,260,\fscx100\fscy100)\p1}}{circle(62)}{{\p0}}")
    ev.extend(label(e0 + 0.3, TOTAL, "BANTAL *AVOCADO*", y=cy - 130, box=PALE, hi=SEED, layer=9, size=50,
                    emoji="🥑", stickers=stickers))
    ev.extend(label(e0 + 0.55, TOTAL, "BULAT MONTEL • 30CM", y=cy - 40, box=CREAM, layer=9, size=38,
                    emoji="🤍", stickers=stickers))
    ev.extend(label(e0 + 1.0, TOTAL, "TAG KAWAN *PEMINAT AVOCADO*!", y=cy + 250, box=PALE, hi=CHEEK, layer=9,
                    size=38, emoji="🏷️", stickers=stickers))
    ev.extend(label(e0 + 1.3, TOTAL, "TEKAN BEG KUNING", y=cy + 335, box=BUTTER, layer=9, size=44,
                    emoji="🛒", stickers=stickers))
    ev.extend(leaves(e0 + 0.3, y=cy - 130, layer=8, spots=((-250, -60), (240, -70), (-230, 60), (235, 70))))
    stickers.append(("😊", e0 + 0.45, TOTAL, CX, cy + 95, 70))
    sfx += [("whoosh", e0 - 0.1, 0.4), ("plop", e0 + 0.35, 0.6), ("pop", e0 + 0.3, 0.45), ("pop", e0 + 0.55, 0.45),
            ("rustle", e0 + 0.35, 0.4), ("pop", e0 + 1.0, 0.4), ("ding", e0 + 1.3, 0.4)]
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
           "-filter_complex", f"[0:v]ass={ass_path}[a];[a][1:v]overlay=0:0:format=auto[v]",   # emoji sit inside the seed badges, so above the ASS
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
