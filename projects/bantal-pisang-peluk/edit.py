#!/usr/bin/env python3
"""Edit for the banana hug pillow (bantal pisang, IMG_2932: sitting on the grass) TikTok video.

Refreshed look vs. the earlier banana video and the other batch-4 edits: picnic theme -
ticket-stub labels that slide in, a banana-yellow underline bar under the active caption
word, comic starbursts behind the key lines, zoom-punch cuts, a banana progress bar with a
brown "tip", and a red gingham picnic-cloth end card.

All overlays stay inside the TikTok safe zone (SAFE_* below): nothing under the
right-hand profile/like/comment/share column, the bottom caption area or the top tabs.

Needs the Fredoka Bold font (fonts/Fredoka-Bold.ttf, SIL OFL) installed, e.g. in ~/.fonts.

Usage: python3 edit.py <proxy.mp4> <transcript.json> <sfx_dir> <out_dir> [--final]
  preview: 720x1280 proxy -> preview.mp4;  --final: 1080x1920 master -> final.mp4
  --audio-only: re-mix voice + SFX onto the existing render -> *_voice.mp4

All times in BLOCKS are source times of the original clip (same timeline as
the proxy). The script builds:
  base.mp4     - cut/zoomed video + cleaned voice + SFX
  overlay.ass  - captions, labels, starbursts, progress bar, end card
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
VOICE_LUFS = -11.5


# ---------------------------------------------------------------- EDL
# v: list of (src_in, src_out, speed, zoom)
# a: 'same' (follow v at speed 1), None (silence) or list of (src_in, src_out)
def punch(s, e, z=1.0, pz=1.12, d=0.2):
    """Zoom-punch cut: the first few frames of a section a little closer, then settle."""
    return [(s, s + d, 1, pz), (s + d, e, 1, z)]


BLOCKS = [
    # HOOK (moved from 24.4s, she hugs the 70cm one): "Hat ni pisang terlebih nutrisen." +
    # "Hat ni pisang terlebih... gizi."  (breath and a 1s near-silent "aah" before "gizi" cut)
    dict(name="hook", a=[(24.38, 26.32), (26.42, 29.30), (30.36, 30.80)],
         v=[*punch(24.38, 26.32), *punch(26.42, 29.30, pz=1.15), (30.36, 30.80, 1, 1.08)]),
    # "Peminat pisang? Peminat kerepek pisang ke?" + "Peminat pisang banana, salai ke apa ke?"  (laugh + pause cut)
    dict(name="peminat", a=[(0.45, 3.20), (4.20, 8.18)],
         v=[*punch(0.45, 3.20), (4.20, 6.10, 1, 1.0), (6.10, 8.18, 1, 1.08)]),
    # "Korang dah ada ke pisang yang ni? Pisang yang ni tak ada lagi?" + "Kena ada hat ni jugak."
    dict(name="dahada", a=[(8.20, 11.48), (11.55, 12.95)],
         v=[(8.20, 11.48, 1, 1.0), (11.55, 12.95, 1, 1.1)]),
    # sizes: "Hat ni tengoklah, 70cm punya lah gebu, 50cm hat ni, hat ni size sedang-sedang.
    # Hat paling kecil, size 35cm." + "Ada 3 size pisang."  (sound after "35cm" cut)
    dict(name="saiz", a=[(13.06, 22.12), (22.98, 24.30)],
         v=[*punch(13.06, 16.45), (16.45, 19.66, 1, 1.08), (19.66, 22.12, 1, 1.0), (22.98, 24.30, 1, 1.12)]),
    # "Hat ni gebu-gebu macam ni, size 70cm. Memang recommended. Kalau nak bawa travel, ambil 50cm.
    # Untuk baby-baby bawah setahun, boleh ambil yang size 35cm. Korang tengok dekat beg kuning."
    # ("Hat ni ambil hat ni" before it is unclear; "Seller tengah bagi harga runtuh" after it is a price line - cut)
    dict(name="guna", a=[(32.30, 42.74)],
         v=[*punch(32.30, 35.88), (35.88, 38.20, 1, 1.08), (38.20, 41.55, 1, 1.0), (41.55, 42.74, 1, 1.1)]),
    # waving with all three bananas - end card (voice muted: price line)
    dict(name="end", a=None, v=[(43.00, 45.80, 1, 1.0)]),
]

FIX = {"krepik": "kerepek", "Kala": "Kalau", "buat": "bawa", "-gebah": "-gebu", "Kau": "Korang", "ku": "kuning.",
       "-sedang": "-sedang.", "Ini": "Ni", "ini": "ni"}
def _w(*ws):
    return [dict(w=w, s=a, e=b) for w, a, b in ws]


# hand-checked against the RMS envelope: "terlebih" is drawn out, "gizi" lands after a near-silent "aah"
OVERRIDE = {
    26.42: _w(("Hat", 26.45, 26.70), ("ni", 26.70, 26.95), ("pisang", 27.28, 27.70), ("terlebih...", 27.70, 29.28)),
    30.36: _w(("gizi!", 30.40, 30.76)),
}
DROP = [(8.37, 8.40), (41.79, 41.82), (42.47, 42.50)]   # "orang" (Kau orang -> Korang) x2, "ni" (beg ku ni)
HILITE = {"PISANG", "KEREPEK", "BANANA", "SALAI", "GEBU", "GEBU-GEBU", "70CM", "50CM", "35CM", "SEDANG-SEDANG",
          "KECIL", "3", "SIZE", "NUTRISEN", "GIZI", "RECOMMENDED", "TRAVEL", "BABY-BABY", "SETAHUN", "KUNING"}

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


CAP_SIZE = 58
CAP_MV = SAFE_B + 20                      # caption bottom margin
ASS_HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Fredoka,{CAP_SIZE},&H00FFFFFF,&H000000FF,&H00223A5A,&H64223A5A,-1,0,0,0,100,100,0,0,1,5,3,2,{SAFE_L},{SAFE_R},{CAP_MV},1
Style: Tick,Fredoka,60,&H00223A5A,&H000000FF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,&H00223A5A,&H64223A5A,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# picnic palette: banana yellow, red gingham, cream, chocolate (banana tip), leaf green (the grass)
YEL = "&H003BD9FF&"      # #FFD93B  (ASS colours are BGR)
RED = "&H004D48E5&"      # #E5484D
CREAM = "&H00E1F8FF&"    # #FFF8E1
CHOC = "&H00223A5A&"     # #5A3A22
LEAF = "&H004AA84F&"     # #4FA84A
WHITE = "&H00FFFFFF&"
KEY = "&H0087E7FF&"      # #FFE787 soft yellow for keywords in captions

_PIL = {}


def text_w(text, size):
    """Width in ASS px of text set in Fredoka at `size`."""
    f = _PIL.setdefault(size, ImageFont.truetype(FONT_FILE, size))
    return f.getlength(text) * ASS_PER_PIL


def captions(words):
    """3-word chunks; the active word sits on a banana-yellow underline bar (measured with Pillow)."""
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
    sp = text_w(" ", CAP_SIZE)
    base_y = H - CAP_MV                    # bottom of the caption line box
    for i, ch in enumerate(chunks):
        end = ch[-1]["e"] + 0.15
        if i + 1 < len(chunks):
            end = min(end, chunks[i + 1][0]["s"])
        toks = [x["w"].upper().strip(",.") for x in ch]
        line = " ".join(toks)
        full = text_w(line, CAP_SIZE)
        fs = CAP_SIZE if full <= SAFE_W - 30 else int(CAP_SIZE * (SAFE_W - 30) / full)
        scale = fs / CAP_SIZE
        x0 = CX - full * scale / 2
        offs, x = [], x0
        for t in toks:
            wdt = text_w(t, CAP_SIZE) * scale
            offs.append((x, wdt))
            x += wdt + sp * scale
        for j, w in enumerate(ch):
            ws = w["s"] if j else min(w["s"], ch[0]["s"])
            we = ch[j + 1]["s"] if j + 1 < len(ch) else end
            parts = []
            for k, t in enumerate(toks):
                if k == j:
                    parts.append(r"{\c%s}%s{\r}" % (YEL, t))
                elif t.strip("-") in HILITE or t in HILITE:
                    parts.append(r"{\c%s}%s{\r}" % (KEY, t))
                else:
                    parts.append(t)
            pop = r"{\fscx85\fscy85\t(0,90,\fscx100\fscy100)}" if j == 0 else ""
            ev.append(f"Dialogue: 2,{ts(ws)},{ts(we)},Cap,,0,0,0,,{pop}{{\\fs{fs}}}" + " ".join(parts))
            # underline bar under the active word (grows from the left)
            bx, bw = offs[j]
            bh = 11 * scale + 2
            by = base_y - 5
            ev.append(f"Dialogue: 1,{ts(ws)},{ts(we)},Shape,,0,0,0,,"
                      rf"{{\an7\pos({bx - 4:.0f},{by:.0f})\c{YEL}\3c{CHOC}\bord3\fscx0\t(0,90,\fscx100)\p1}}"
                      rf"m 0 0 l {bw + 8:.0f} 0 {bw + 8:.0f} {bh:.0f} 0 {bh:.0f}{{\p0}}")
    return ev


def fit_size(text, size, max_w):
    plain = text.replace("*", "")
    w = text_w(plain, size)
    return size if w <= max_w else int(size * max_w / w)


def ticket_path(w, h):
    """Ticket stub centred on (0,0): notched half-circles on both short sides."""
    r = h * 0.2
    c = r * 1.33
    x0, x1, y0, y1 = -w / 2, w / 2, -h / 2, h / 2
    return (f"m {x0:.0f} {y0:.0f} l {x1:.0f} {y0:.0f} l {x1:.0f} {-r:.0f} "
            f"b {x1 - c:.0f} {-r:.0f} {x1 - c:.0f} {r:.0f} {x1:.0f} {r:.0f} l {x1:.0f} {y1:.0f} l {x0:.0f} {y1:.0f} "
            f"l {x0:.0f} {r:.0f} b {x0 + c:.0f} {r:.0f} {x0 + c:.0f} {-r:.0f} {x0:.0f} {-r:.0f} l {x0:.0f} {y0:.0f}")


def place(path, cx, cy):
    """libass anchors a drawing at its (0,0) origin, so shift a centred path to positive
    coordinates and return it with the top-left position that puts its (0,0) centre at (cx, cy)."""
    toks = path.split()
    nums = [(i, float(t)) for i, t in enumerate(toks) if t not in ("m", "l", "b")]
    xs = [v for k, (i, v) in enumerate(nums) if k % 2 == 0]
    ys = [v for k, (i, v) in enumerate(nums) if k % 2 == 1]
    mx, my = min(xs), min(ys)
    for k, (i, v) in enumerate(nums):
        toks[i] = f"{v - (mx if k % 2 == 0 else my):.0f}"
    return " ".join(toks), cx + mx, cy + my


def ticket(t0, t1, text, y=250, col=CHOC, fill=CREAM, hi=RED, x=CX, size=60, layer=5, side=1, max_w=SAFE_W - 70):
    """Slide-in ticket-stub label with a perforated stub (and a little star) on the left.
    *word* uses the highlight colour. Every piece is a drawing centred on its own point (\\an5)."""
    size = fit_size(text, size, max_w - size * 1.4)
    plain = text.replace("*", "")
    tw = text_w(plain, size)
    h = size * 1.32
    stub = h * 0.62
    w = tw + stub + size * 0.9
    parts = text.split("*")
    body = "".join(p if i % 2 == 0 else rf"{{\c{hi}}}{p}{{\c{col}}}" for i, p in enumerate(parts))
    sx = -side * 46                                    # slide-in offset

    def mv(cx, cy=0):
        return rf"\an5\move({x + sx + cx:.0f},{y + cy:.0f},{x + cx:.0f},{y + cy:.0f},0,170)\fad(120,150)"

    def shape(path, cx, cy, tags):
        pth, px, py = place(path, x + cx, y + cy)
        return (f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
                rf"{{\an7\move({px + sx:.0f},{py:.0f},{px:.0f},{py:.0f},0,170)\fad(120,150){tags}\p1}}{pth}{{\p0}}")

    perf = -w / 2 + stub
    dashes = " ".join(f"m -2 {yy:.0f} l 2 {yy:.0f} l 2 {yy + 7:.0f} l -2 {yy + 7:.0f}"
                      for yy in np.arange(-h / 2 + 7, h / 2 - 12, 12))
    rs = size * 0.25
    star = "m 0 {:.0f} ".format(-rs) + " ".join(
        f"l {rs * (1 if k % 2 == 0 else 0.42) * math.sin(k * math.pi / 5):.0f} "
        f"{-rs * (1 if k % 2 == 0 else 0.42) * math.cos(k * math.pi / 5):.0f}" for k in range(1, 10))
    tp = ticket_path(w, h)
    return [
        shape(tp, 6, 7, rf"\c{CHOC}\1a&H40&"),
        shape(tp, 0, 0, rf"\c{fill}\3c{CHOC}\bord3"),
        shape(dashes, perf, 0, rf"\c{CHOC}\1a&H50&"),
        shape(star, -w / 2 + stub / 2, 3, rf"\c{hi}"),
        f"Dialogue: {layer},{ts(t0)},{ts(t1)},Tick,,0,0,0,,{{{mv(stub / 2 - size * 0.08)}\\fs{size}\\c{col}}}{body}",
    ]


def starburst(t0, t1, x, y, r=150, col=YEL, layer=4):
    """Comic starburst behind a key label, slowly turning."""
    pts = []
    for k in range(24):
        a = k * math.pi / 12
        rr = r if k % 2 == 0 else r * 0.72
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    path = f"m {pts[0][0]:.0f} {pts[0][1]:.0f} " + " ".join(f"l {px:.0f} {py:.0f}" for px, py in pts[1:])
    path, px, py = place(path, x, y)
    return (f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
            rf"{{\an7\pos({px:.0f},{py:.0f})\org({x},{y})\c{col}\3c{WHITE}\bord4\1a&H38&\3a&H30&\fad(120,150)"
            rf"\t(0,{int((t1 - t0) * 1000)},\frz25)\p1}}{path}{{\p0}}")


def gingham(t0, t1, layer=8):
    """Red-and-cream picnic cloth: cream wash + crossing translucent red stripes."""
    ev = [f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
          rf"{{\an7\pos(0,0)\c{CREAM}\1a&HFF&\t(0,250,\1a&H50&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}"]
    S = 60
    hs = " ".join(f"m 0 {y} l {W} {y} l {W} {y + S // 2} l 0 {y + S // 2}" for y in range(0, H, S))
    vs = " ".join(f"m {x} 0 l {x + S // 2} 0 l {x + S // 2} {H} l {x} {H}" for x in range(0, W, S))
    for p in (hs, vs):
        ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
                  rf"{{\an7\pos(0,0)\c{RED}\1a&HFF&\t(0,250,\1a&HA8&)\p1}}{p}{{\p0}}")
    return ev


def graphics():
    ev, stickers, sfx = [], [], []
    LY = 800                       # labels sit on the lower banana bodies, clear of the banana faces
    # progress bar: banana-yellow fill with a brown "banana tip" riding the front
    dur_ms = int(TOTAL * 1000)
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{YEL}\fscx0\t(0,{dur_ms},\fscx100)\p1}}m 0 0 l {W} 0 {W} 9 0 9{{\p0}}")
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an5\move(0,5,{W},5,0,{dur_ms})\c{CHOC}\p1}}m -7 -7 b 2 -9 9 -2 7 7 b -2 9 -9 2 -7 -7{{\p0}}")

    def lab(s0, s1, text, sound="tick", vol=0.55, **kw):
        kw.setdefault("y", LY)
        ev.extend(ticket(tl(s0), tl(s1), text, **kw))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def burst(s0, s1, col=YEL, r=125, y=LY):
        ev.append(starburst(tl(s0), tl(s1), CX, y, r=r, col=col))

    def stk(em, s0, s1, x, y=690, size=96):
        stickers.append((em, tl(s0), tl(s1), x, y, size))

    def bstk(em, t0, t1, x, y, size=100):
        stickers.append((em, t0, t1, x, y, size))

    def whoosh_at(name, vol=0.35):
        sfx.append(("swish", BT[name]["t0"] - 0.04, vol))

    SL, SR = 95, 545
    side = [1]

    def flip():
        side[0] = -side[0]
        return side[0]

    # ---- HOOK: the 70cm one is "terlebih nutrisen ... terlebih gizi"
    burst(24.66, 26.30, col=YEL)
    lab(24.66, 26.30, "PISANG TERLEBIH *NUTRISEN*", fill=CREAM, hi=RED, side=flip(), sound="boing", vol=0.5)
    stk("😂", 24.70, 26.30, SR)
    burst(27.28, 30.78, col=RED, r=135)
    lab(27.28, 30.78, "TERLEBIH *GIZI*!", fill=YEL, hi=RED, size=72, side=flip(), sound="boing", vol=0.55)
    stk("💪", 27.32, 30.78, SL)
    stk("🍌", 27.32, 30.78, SR, 660, 110)

    # ---- fans of banana anything
    whoosh_at("peminat")
    lab(0.56, 1.84, "PEMINAT *PISANG*?", side=flip())
    stk("🍌", 0.60, 1.84, SR)
    lab(1.86, 3.18, "*KEREPEK* PISANG?", fill=YEL, hi=RED, side=flip())
    stk("😋", 1.90, 3.18, SL)
    lab(4.34, 6.06, "PISANG *BANANA*!", side=flip())
    stk("🍌", 4.38, 6.06, SR)
    lab(7.24, 8.16, "PISANG *SALAI*?", fill=YEL, hi=RED, side=flip())
    stk("🤔", 7.28, 8.16, SL)

    # ---- do you have this one yet?
    lab(8.24, 9.96, "DAH ADA *YANG NI*?", side=flip())
    stk("👀", 8.28, 9.96, SR)
    lab(10.10, 11.26, "BELUM ADA *LAGI*?", fill=YEL, hi=RED, side=flip())
    stk("😱", 10.14, 11.26, SL)
    burst(11.72, 12.92, col=RED, r=120)
    lab(11.72, 12.92, "*KENA ADA*!", fill=CREAM, hi=LEAF, size=70, side=flip(), sound="boing", vol=0.5)
    stk("✅", 11.76, 12.92, SR)

    # ---- three sizes
    whoosh_at("saiz")
    lab(13.08, 14.30, "TENGOK NI!", fill=CREAM, side=flip())
    stk("👇", 13.12, 14.30, SR)
    lab(14.34, 16.40, "*70CM* GEBU!", fill=YEL, hi=RED, size=70, side=flip(), sound="bloop", vol=0.5)
    stk("☁️", 14.38, 16.40, SL)
    lab(16.76, 18.26, "*50CM*", fill=CREAM, hi=RED, size=70, side=flip(), sound="bloop", vol=0.5)
    lab(18.30, 19.66, "SIZE *SEDANG*", fill=CREAM, hi=LEAF, side=flip())
    stk("👌", 18.34, 19.66, SR)
    lab(19.70, 22.06, "PALING KECIL *35CM*", fill=YEL, hi=RED, side=flip(), sound="bloop", vol=0.5)
    stk("🤏", 19.74, 22.06, SL)
    burst(23.05, 24.28, col=YEL, r=130)
    lab(23.05, 24.28, "ADA *3 SIZE*!", fill=CREAM, hi=RED, size=74, side=flip(), sound="ding", vol=0.4)
    stk("3️⃣", 23.09, 24.28, SR)

    # ---- which size for what
    whoosh_at("guna")
    lab(32.38, 33.72, "*GEBU-GEBU*", fill=CREAM, hi=RED, side=flip())
    stk("🤗", 32.42, 33.72, SR)
    burst(33.82, 35.84, col=RED, r=135)
    lab(33.82, 35.84, "70CM *RECOMMENDED*!", fill=YEL, hi=RED, side=flip(), sound="ding", vol=0.4)
    stk("👍", 33.86, 35.84, SL)
    lab(36.32, 37.90, "TRAVEL? *50CM*", fill=CREAM, hi=LEAF, side=flip(), sound="whoosh", vol=0.3)
    stk("✈️", 36.36, 37.90, SR)
    lab(38.22, 39.58, "BABY BAWAH *SETAHUN*", fill=CREAM, hi=RED, side=flip())
    stk("👶", 38.26, 39.58, SL)
    lab(39.72, 41.46, "AMBIL *35CM*", fill=YEL, hi=RED, size=70, side=flip(), sound="bloop", vol=0.5)
    stk("🍼", 39.76, 41.46, SR)
    lab(41.86, 42.72, "TEKAN *BEG KUNING*", fill=YEL, hi=RED, side=flip(), sound="pop", vol=0.5)
    stk("🛒", 41.90, 42.72, SL)

    # ---- end card: red gingham picnic cloth + stacked tickets
    e0 = BT["end"]["t0"]
    ev += gingham(e0, TOTAL)
    ev += ticket(e0 + 0.10, TOTAL, "BANTAL *PISANG*", y=380, fill=YEL, hi=RED, size=70, layer=9, side=1)
    ev += ticket(e0 + 0.35, TOTAL, "35 • 50 • 70 CM", y=500, fill=CREAM, hi=RED, size=52, layer=9, side=-1)
    ev += ticket(e0 + 0.60, TOTAL, "KORANG TEAM *SIZE MANA*?", y=615, fill=CREAM, hi=RED, size=46, layer=9, side=1)
    ev += ticket(e0 + 0.85, TOTAL, "TEKAN *BEG KUNING*", y=735, fill=YEL, hi=RED, size=56, layer=9, side=-1)
    bstk("🍌", e0 + 0.15, TOTAL, SR, 260, 100)
    bstk("🧺", e0 + 0.40, TOTAL, SL, 260, 90)
    bstk("🛒", e0 + 0.90, TOTAL, SR, 850, 84)
    sfx += [("whoosh", e0 - 0.1, 0.4), ("tick", e0 + 0.10, 0.55), ("tick", e0 + 0.35, 0.55),
            ("tick", e0 + 0.60, 0.55), ("pop", e0 + 0.85, 0.5)]
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
