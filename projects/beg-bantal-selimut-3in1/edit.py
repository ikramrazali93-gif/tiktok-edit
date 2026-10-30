#!/usr/bin/env python3
"""Edit for beg bantal selimut 3 in 1 (IMG_3184), "Hutan malam" (night woodland) look: a fluffy square bag with
a cute bird/owl face that holds a blanket inside, works as a pillow, and has hand-warmer pockets. The graphics
layer is a HyperFrames (HTML + GSAP) composition, as in ../bantal-durian-2.

Pipeline (all times in BLOCKS are source times of the original clip, same timeline as the proxy):
  1. base.mp4      - cut/zoomed video + cleaned voice (v2 chain, -11.5 LUFS) + SFX       (ffmpeg)
  2. comp/data.js  - captions, labels, night wipes, end card + her head boxes for each of them (this script)
  3. hf.mp4        - comp/index.html rendered by HyperFrames with base.mp4 as its muted video layer; the
                     composition places every graphic itself, scanning the safe area for the spot nearest its
                     preferred position that keeps a margin clear of every head box in its time window
  4. preview.mp4 / final.mp4 - hf.mp4 video + base.mp4 audio (preview is scaled to 720x1280)

Usage: python3 edit.py <proxy.mp4|master1080.mp4> <transcript.json> <sfx_dir> <out_dir> [--final]
         [--no-render | --graphics-only]
Needs: ffmpeg, Node 18+, `npm install` inside comp/ (pins hyperframes), Chrome/Chromium for HyperFrames
(set HYPERFRAMES_BROWSER_PATH to use a preinstalled one).
"""
import json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
COMP = os.path.join(HERE, "comp")
PROXY, TRANSCRIPT, SFX, OUT = map(os.path.abspath, sys.argv[1:5])
FINAL = "--final" in sys.argv
FPS = 30
CW, CH = 1080, 1920                     # composition canvas (always 1080x1920; preview is scaled down after)
RW, RH = (1080, 1920) if FINAL else (720, 1280)   # base.mp4 size
VOICE_LUFS = -11.5
# TikTok UI safe zone in 1080x1920 px: right column (profile/like/comment/share), bottom caption, top tabs
SAFE_L, SAFE_R, SAFE_T, SAFE_B = 60, 165, 165, 435

# ---------------------------------------------------------------- EDL
# One locked-off clip on a lawn: she opens a grey parcel, shows the bird-face bag, its side pockets, unzips the
# blanket out of it, spreads it, then packs it back. The opening is a slow unboxing, so the hook is her
# "beg boleh jadi selimut dan bantal, 3 in 1" line J-cut over the finished product (bag + spread blanket).
# v: list of (src_in, src_out, speed, zoom); a: 'same' (follow v at 1x), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK (J-cut): "Yang ini bag boleh jadi selimut dan juga bantal. | 3 in 1. Sebab dia ada lubang untuk
    # masukkan tangan juga."  over: bag held up face-front (88.9s), then bag + spread blanket (65.4s)
    dict(name="hook", a=[(6.78, 10.18), (10.92, 15.64)], v=[(88.90, 92.30, 1, 1.0), (65.40, 70.12, 1, 1.0)]),
    # "Sekarang kita buka."
    dict(name="buka", a="same", v=[(16.10, 17.06, 1, 1.0)]),
    # pulling it out of the parcel and the plastic (x4, no speech)
    dict(name="unbox", a=None, v=[(17.06, 24.70, 4, 1.0)]),
    # "Tadaa!"
    dict(name="tadaa", a="same", v=[(24.74, 25.76, 1, 1.1)]),
    # "Ya Allah, comel. Yang ini kan, | dia boleh masukkan tangan sebab dia ada pocket kat tepi ni."
    dict(name="comel", a="same", v=[(28.44, 30.90, 1, 1.0), (30.90, 33.48, 1, 1.08)]),
    # "Kalau kita sejuk-sejuk dekat ofis ke ataupun dalam bas ke,"  (repeat "sejuk boleh masukkan tangan
    # dekat pocket tepi ni" cut)
    dict(name="sejuk", a="same", v=[(34.02, 37.91, 1, 1.0)]),
    # "Dua-dua tangan boleh masuk."
    dict(name="dua", a="same", v=[(40.20, 41.49, 1, 1.0)]),
    # "Dan bantal ni, dalam dia, bag dia ada selimut."
    dict(name="dalam", a="same", v=[(41.78, 45.52, 1, 1.0)]),
    # "Bantal dia pun tak kosong, ada kapas. Jadi sambil kita selimut, kita boleh guna bantal dia."
    dict(name="kapas", a="same", v=[(48.47, 52.56, 1, 1.0)]),
    # pulling the blanket out of the bag (x2, "Okey ini selimut dia macam itu" cut)
    dict(name="tarik", a=None, v=[(53.00, 56.00, 2, 1.0)]),
    # "Selimut dia pun besar panjang. Size memang ngam untuk seorang guna. Size 170cm."
    dict(name="besar", a="same", v=[(56.07, 61.84, 1, 1.0)]),
    # "Okey kan senang bawa travel. Habis guna, simpan balik, tutup balik zip dia."
    dict(name="travel", a="same", v=[(79.90, 84.36, 1, 1.0)]),
    # CTA: "Comel sangat. Ada macam-macam kaler boleh tengok. Tengok dekat bawah sekarang."
    dict(name="cta", a="same", v=[(84.86, 88.86, 1, 1.0)]),
    # end card over her wave (the price line underneath is muted)
    dict(name="end", a=None, v=[(97.60, 99.70, 1, 1.0)]),
]

FIX = {"bantai": "bantal", "bus": "bas", "color": "kaler", "enak": "ngam"}


def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


# hand-checked words (re-transcribed per chunk + loudness envelope; Whisper writes "bantai" for "bantal")
_COMEL = _w(("Ya", 28.46, 28.66), ("Allah,", 28.66, 28.90), ("comel.", 29.14, 29.84), ("Yang", 29.92, 30.14),
            ("ini", 30.14, 30.32), ("kan,", 30.32, 30.74), ("dia", 30.92, 31.10), ("boleh", 31.10, 31.38),
            ("masukkan", 31.38, 31.94), ("tangan", 31.94, 32.26), ("sebab", 32.26, 32.44), ("dia", 32.44, 32.50),
            ("ada", 32.50, 32.64), ("pocket", 32.64, 32.94), ("kat", 32.94, 33.14), ("tepi", 33.14, 33.32),
            ("ni.", 33.32, 33.46))
OVERRIDE = {
    6.78: _w(("Yang", 6.82, 7.20), ("ini", 7.20, 7.58), ("bag", 7.60, 8.10), ("boleh", 8.10, 8.46),
             ("jadi", 8.46, 8.76), ("selimut", 8.76, 9.20), ("dan", 9.20, 9.44), ("juga", 9.44, 9.74),
             ("bantal.", 9.74, 10.16)),
    10.92: _w(("3", 11.00, 11.40), ("in", 11.46, 11.80), ("1.", 11.80, 12.46), ("Sebab", 12.48, 12.92),
              ("dia", 12.92, 13.04), ("ada", 13.04, 13.86), ("lubang", 13.88, 14.26), ("untuk", 14.26, 14.52),
              ("masukkan", 14.52, 15.12), ("tangan", 15.12, 15.46), ("juga.", 15.46, 15.62)),
    16.10: _w(("kita", 16.56, 16.80), ("buka.", 16.80, 17.04)),   # first word unclear ("Sekarang"?), left uncaptioned
    24.74: _w(("Tadaa!", 24.76, 25.74)),
    28.44: _COMEL,
    30.90: _COMEL,
    34.02: _w(("Kalau", 34.04, 34.46), ("kita", 34.46, 34.82), ("sejuk-sejuk", 34.82, 35.70), ("dekat", 35.70, 35.94),
              ("ofis", 35.94, 36.48), ("ke", 36.48, 36.68), ("ataupun", 36.68, 37.18), ("dalam", 37.18, 37.52),
              ("bas", 37.52, 37.78), ("ke,", 37.78, 37.90)),
    40.20: _w(("Dua-dua", 40.26, 40.86), ("tangan", 40.96, 41.16), ("boleh", 41.16, 41.24), ("masuk.", 41.24, 41.46)),
    41.78: _w(("Dan", 41.84, 42.30), ("bantal", 42.36, 42.96), ("ni,", 42.96, 43.20), ("dalam", 43.20, 43.46),
              ("dia,", 43.46, 43.70), ("bag", 43.70, 43.84), ("dia", 43.84, 43.98), ("ada", 43.98, 44.22),
              ("selimut.", 44.22, 45.48)),
    48.47: _w(("Bantal", 48.56, 49.04), ("dia", 49.04, 49.22), ("pun", 49.22, 49.42), ("tak", 49.42, 49.62),
              ("kosong,", 49.62, 49.96), ("ada", 50.02, 50.16), ("kapas.", 50.16, 50.60), ("Jadi", 50.62, 50.82),
              ("sambil", 50.82, 51.08), ("kita", 51.08, 51.28), ("selimut,", 51.28, 51.58), ("kita", 51.58, 51.74),
              ("boleh", 51.74, 51.86), ("guna", 51.86, 52.04), ("bantal", 52.04, 52.24), ("dia.", 52.24, 52.52)),
    56.07: _w(("Selimut", 56.10, 56.60), ("dia", 56.60, 56.72), ("pun", 56.72, 56.90), ("besar", 56.90, 57.14),
              ("panjang.", 57.14, 57.66), ("Size", 57.74, 58.04), ("memang", 58.04, 58.46), ("ngam", 58.46, 58.86),
              ("untuk", 58.86, 59.12), ("seorang", 59.12, 59.60), ("guna.", 59.60, 60.50), ("Size", 60.58, 60.78),
              ("170cm.", 60.78, 61.80)),
    79.90: _w(("kan", 80.00, 80.36),   # first word unclear ("Okey"/"Dia"), folded into "kan"
              ("senang", 80.36, 80.64), ("bawa", 80.64, 80.84),
              ("travel.", 80.84, 81.44), ("Habis", 81.96, 82.08), ("guna,", 82.08, 82.24), ("simpan", 82.24, 82.58),
              ("balik,", 82.58, 82.84), ("tutup", 82.84, 83.14), ("balik", 83.14, 83.38), ("zip", 83.38, 83.58),
              ("dia.", 83.58, 84.30)),
    84.86: _w(("Comel", 84.92, 85.30), ("sangat.", 85.30, 85.62), ("Ada", 85.64, 85.82), ("macam-macam", 85.82, 86.16),
              ("kaler", 86.16, 86.44), ("boleh", 86.44, 86.70), ("tengok.", 86.70, 87.40), ("Tengok", 87.70, 88.14),
              ("dekat", 88.14, 88.36), ("bawah", 88.36, 88.60), ("sekarang.", 88.60, 88.84)),
}
DROP = []
KEYWORDS = {"BAG", "SELIMUT", "BANTAL", "3", "IN", "1", "LUBANG", "TANGAN", "POCKET", "COMEL", "SEJUK-SEJUK",
            "OFIS", "BAS", "DUA-DUA", "KAPAS", "BESAR", "PANJANG", "SEORANG", "170CM", "TRAVEL", "ZIP", "KALER",
            "BAWAH", "TADAA!", "BUKA"}

# ---------------------------------------------------------------- her head (face avoidance)
# Head + hood box sampled every second from gridded proxy frames (fractions of the source frame, x0, y0, x1, y1).
# edit.py turns these into px boxes (zoom applied) for each graphic's time window; the composition keeps every
# graphic HEAD_MARGIN px clear of all of them.
HEADS = [
    (6, (0.33, 0.19, 0.78, 0.42)), (7, (0.34, 0.19, 0.78, 0.42)), (8, (0.33, 0.19, 0.78, 0.42)),
    (9, (0.37, 0.18, 0.82, 0.42)), (10, (0.38, 0.17, 0.86, 0.42)), (11, (0.41, 0.16, 0.88, 0.41)),
    (12, (0.39, 0.17, 0.87, 0.41)), (13, (0.37, 0.17, 0.85, 0.41)), (14, (0.30, 0.16, 0.78, 0.42)),
    (15, (0.31, 0.16, 0.77, 0.42)), (16, (0.29, 0.15, 0.77, 0.43)), (17, (0.29, 0.16, 0.75, 0.44)),
    (18, (0.32, 0.16, 0.79, 0.43)), (19, (0.34, 0.16, 0.83, 0.43)), (20, (0.39, 0.16, 0.87, 0.43)),
    (21, (0.43, 0.16, 0.91, 0.44)), (22, (0.44, 0.18, 0.93, 0.43)), (23, (0.44, 0.17, 0.93, 0.43)),
    (24, (0.54, 0.18, 1.00, 0.43)), (25, (0.46, 0.18, 0.90, 0.41)), (26, (0.39, 0.14, 0.84, 0.41)),
    (27, (0.37, 0.16, 0.82, 0.41)), (28, (0.34, 0.23, 0.86, 0.51)), (29, (0.37, 0.17, 0.93, 0.45)),
    (30, (0.21, 0.17, 0.73, 0.47)), (31, (0.44, 0.16, 0.93, 0.43)), (32, (0.44, 0.16, 0.93, 0.43)),
    (33, (0.47, 0.16, 0.96, 0.43)), (34, (0.44, 0.16, 0.93, 0.43)), (35, (0.32, 0.15, 0.81, 0.41)),
    (36, (0.37, 0.14, 0.83, 0.39)), (37, (0.41, 0.13, 0.87, 0.39)), (38, (0.32, 0.13, 0.81, 0.39)),
    (39, (0.39, 0.14, 0.87, 0.41)), (40, (0.41, 0.15, 0.89, 0.41)), (41, (0.29, 0.14, 0.76, 0.43)),
    (42, (0.34, 0.16, 0.81, 0.43)), (43, (0.37, 0.15, 0.81, 0.41)), (44, (0.37, 0.15, 0.81, 0.41)),
    (45, (0.39, 0.14, 0.85, 0.41)),
    (48, (0.17, 0.07, 0.61, 0.39)), (49, (0.29, 0.09, 0.76, 0.34)), (50, (0.31, 0.09, 0.76, 0.34)),
    (51, (0.31, 0.09, 0.76, 0.34)), (52, (0.33, 0.09, 0.76, 0.34)), (53, (0.37, 0.07, 0.81, 0.35)),
    (54, (0.31, 0.09, 0.76, 0.35)), (55, (0.34, 0.09, 0.79, 0.35)), (56, (0.39, 0.09, 0.83, 0.35)),
    (57, (0.39, 0.09, 0.86, 0.35)), (58, (0.44, 0.09, 0.91, 0.35)), (59, (0.47, 0.09, 0.96, 0.35)),
    (60, (0.57, 0.09, 0.99, 0.35)), (61, (0.59, 0.09, 1.00, 0.35)), (62, (0.57, 0.07, 0.99, 0.35)),
    (65, (0.54, 0.04, 0.99, 0.33)), (66, (0.54, 0.04, 0.99, 0.33)), (67, (0.57, 0.04, 0.99, 0.33)),
    (68, (0.59, 0.04, 1.00, 0.33)), (69, (0.61, 0.04, 1.00, 0.33)), (70, (0.54, 0.09, 0.96, 0.33)),
    (79, (0.39, 0.07, 0.89, 0.33)), (80, (0.37, 0.05, 0.86, 0.33)), (81, (0.39, 0.05, 0.89, 0.33)),
    (82, (0.31, 0.05, 0.81, 0.33)), (83, (0.37, 0.05, 0.86, 0.33)), (84, (0.39, 0.05, 0.89, 0.33)),
    (85, (0.39, 0.05, 0.89, 0.33)), (86, (0.14, 0.03, 0.71, 0.33)), (87, (0.24, 0.05, 0.76, 0.33)),
    (88, (0.27, 0.05, 0.79, 0.33)), (89, (0.29, 0.03, 0.79, 0.31)), (90, (0.29, 0.03, 0.81, 0.31)),
    (91, (0.14, 0.05, 0.66, 0.33)), (92, (0.19, 0.05, 0.71, 0.35)), (93, (0.19, 0.05, 0.71, 0.35)),
    (97, (0.49, 0.07, 0.96, 0.41)), (98, (0.24, 0.07, 0.76, 0.33)), (99, (0.29, 0.03, 0.86, 0.33)),
]
# The bag's bird face (eyes + beak centre): graphics steer off these points when they can.
FACES = [
    (24, [(0.30, 0.55)]), (25, [(0.40, 0.55)]), (29, [(0.45, 0.67)]), (30, [(0.30, 0.73)]),
    (31, [(0.33, 0.60)]), (32, [(0.33, 0.60)]), (33, [(0.35, 0.60)]), (34, [(0.40, 0.62)]),
    (35, [(0.55, 0.33)]), (36, [(0.55, 0.33)]), (37, [(0.60, 0.33)]),
    (41, [(0.55, 0.70)]), (42, [(0.50, 0.65)]), (43, [(0.40, 0.60)]), (44, [(0.45, 0.72)]), (45, [(0.55, 0.68)]),
    (49, [(0.40, 0.30)]), (50, [(0.33, 0.40)]), (51, [(0.33, 0.40)]),
    (65, [(0.62, 0.57)]), (66, [(0.62, 0.55)]), (67, [(0.62, 0.55)]), (68, [(0.62, 0.55)]), (69, [(0.70, 0.55)]),
    (80, [(0.38, 0.58)]), (81, [(0.40, 0.58)]), (82, [(0.40, 0.62)]), (83, [(0.45, 0.60)]),
    (85, [(0.55, 0.60)]), (86, [(0.30, 0.60)]), (87, [(0.30, 0.60)]), (88, [(0.40, 0.58)]),
    (89, [(0.45, 0.62)]), (90, [(0.40, 0.75)]), (91, [(0.20, 0.72)]), (92, [(0.40, 0.65)]),
]
HEAD_PAD = 0.5          # also count samples this many seconds outside a graphic's source range (1s grid)
LAB_Y, CAP_Y = 880, 1405  # preferred centres (px): labels below her head (it fills the top band), captions low


# ---------------------------------------------------------------- timeline
def build_timeline():
    vclips, aclips, t = [], [], 0.0
    src_map = []
    for b in BLOCKS:
        b["t0"] = t
        dur = 0.0
        for (s, e, sp, z) in b["v"]:
            d = (e - s) / sp
            vclips.append(dict(s=s, e=e, sp=sp, z=z, t=t + dur, d=d, block=b["name"]))
            dur += d
        al = [(s, e) for (s, e, sp, z) in b["v"]] if b["a"] == "same" else b["a"]
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


def block_at(t):
    for b in BLOCKS:
        if b["t0"] - 1e-6 <= t < b["t0"] + b["dur"]:
            return b["name"]
    return BLOCKS[-1]["name"]


def _windows(t0, t1):
    for c in VCLIPS:
        a, b = max(t0, c["t"]), min(t1, c["t"] + c["d"])
        if a < b:
            yield c, c["s"] + (a - c["t"]) * c["sp"], c["s"] + (b - c["t"]) * c["sp"]


def faces_for(t0, t1):
    """Pillow-smiley points (px) shown in timeline window [t0, t1] (close-ups only, see FACES)."""
    pts = []
    for c, s0, s1 in _windows(t0, t1):
        z = c["z"]
        for st, ps in FACES:
            if s0 - 0.5 <= st <= s1 + 0.5:
                pts += [[round((x * z - (z - 1) * 0.5) * CW), round((y * z - (z - 1) * 0.3) * CH)] for x, y in ps]
    return pts


def heads_for(t0, t1):
    """Her head boxes (px, 1080x1920 composition space) for timeline window [t0, t1]: every 1s sample whose source
    time falls in (or within HEAD_PAD of) the source range shown in that window, with the clip's zoom applied."""
    boxes = []
    for c in VCLIPS:
        a, b = max(t0, c["t"]), min(t1, c["t"] + c["d"])
        if a >= b:
            continue
        s0 = c["s"] + (a - c["t"]) * c["sp"]
        s1 = c["s"] + (b - c["t"]) * c["sp"]
        z = c["z"]
        for st, (x0, y0, x1, y1) in HEADS:
            if s0 - HEAD_PAD <= st <= s1 + HEAD_PAD:
                # same crop as render_base: centred in x, 60% of the excess cut from the top
                fx = lambda x: (x * z - (z - 1) * 0.5) * CW
                fy = lambda y: (y * z - (z - 1) * 0.3) * CH
                boxes.append([round(fx(x0)), round(fy(y0)), round(fx(x1)), round(fy(y1))])
    return boxes


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
            straddle = c["s"] - 0.6 <= w["s"] < c["s"] and w["e"] > c["s"] + 0.15
            key = (round(w["s"], 2), w["w"])
            if key in seen:
                continue
            if (inside or straddle) and not any(d0 <= w["s"] < d1 for d0, d1 in DROP):
                seen.add(key)
                txt = w["w"].strip()
                core = txt.strip(",.?!")
                txt = txt.replace(core, FIX.get(core, core))
                s = c["t"] + max(w["s"], c["s"]) - c["s"]
                e = c["t"] + min(w["e"], c["e"]) - c["s"]
                if txt.startswith("-") and out and out[-1]["clip"] == id(c):   # "gebu" + "-gebas"
                    out[-1]["w"] = out[-1]["w"].rstrip(",.") + txt
                    out[-1]["e"] = e
                elif txt.strip(",.?!"):
                    out.append(dict(w=txt, s=s, e=e, clip=id(c)))
    out.sort(key=lambda w: w["s"])
    return out


def caption_chunks(words):
    chunks, cur = [], []
    for w in words:
        tail = w["w"].lower().strip(",.?!") in ("ni", "kan", "ke") and w["e"] - w["s"] < 0.6   # short tail word joins
        if cur and ((len(cur) >= 3 and not tail) or w["s"] - cur[-1]["e"] > 0.35 or w["clip"] != cur[-1]["clip"]
                    or cur[-1]["w"][-1] in ",.?!"):
            chunks.append(cur)
            cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    out = []
    for i, ch in enumerate(chunks):
        end = ch[-1]["e"] + 0.18
        if i + 1 < len(chunks):
            end = min(end, chunks[i + 1][0]["s"])
        out.append(dict(t0=ch[0]["s"], t1=end, y=CAP_Y, heads=heads_for(ch[0]["s"], end), faces=faces_for(ch[0]["s"], end),
                        words=[dict(w=x["w"].upper().strip(",."), s=x["s"], e=x["e"],
                                    key=x["w"].upper().strip(",.?!") in KEYWORDS) for x in ch]))
    return out


# ---------------------------------------------------------------- graphics (data for comp/index.html)
def graphics():
    labels, wipes, tags, sfx = [], [], [], []

    def lab(s0, s1, text, emoji="", sound="firefly", vol=0.5, src=True, kind="lantern", big=False, unit=None):
        t0, t1 = (tl(s0), tl(s1)) if src else (s0, s1)
        labels.append(dict(t0=t0, t1=t1, html=text, emoji=emoji, kind=kind, big=big, unit=unit,
                           heads=heads_for(t0, t1), faces=faces_for(t0, t1)))
        if sound:
            sfx.append((sound, t0 - 0.03, vol))

    def night(block, sound="whoosh", vol=0.4):
        t = BT[block]["t0"]
        wipes.append(dict(t=t))
        sfx.append((sound, t - 0.35, vol))
        sfx.append(("chime", t - 0.1, 0.22))

    # hook: bag -> blanket + pillow, 3 in 1, hand pockets
    lab(7.00, 9.18, "BEG JADI <b>SELIMUT</b>", "🦉", sound="hoot", vol=0.55, big=True)
    lab(9.20, 10.16, "&amp; <b>BANTAL</b>!", "☁️", sound="pop", vol=0.45)
    lab(11.00, 12.46, "3", "🌙", kind="moon", unit="IN 1", sound="chime", vol=0.4)
    lab(12.48, 15.60, "ADA POKET <b>TANGAN</b>", "🧤")
    night("buka")
    lab(16.14, 17.04, "JOM <b>BUKA</b>!", "🎁", sound="pop", vol=0.45)
    u0, u1 = BT["unbox"]["t0"], BT["unbox"]["t0"] + BT["unbox"]["dur"]
    tags.append(dict(t0=u0, t1=u1, text="&gt;&gt; x4", heads=heads_for(u0, u1)))
    lab(24.76, 25.74, "<b>TADAA!</b>", "✨", sound="sparkle", vol=0.4, big=True)
    lab(28.46, 29.84, "YA ALLAH, <b>COMEL</b>!", "🥹", sound="hoot", vol=0.45)
    lab(30.92, 33.46, "POKET <b>HAND</b> <b>WARMER</b>", "🙌")
    lab(34.04, 36.68, "SEJUK DI <b>OFIS</b>?", "🏢")
    lab(36.68, 37.90, "DALAM <b>BAS</b>?", "🚌", sound="pop", vol=0.4)
    lab(40.26, 41.46, "<b>DUA-DUA</b> TANGAN MASUK", "🙌", sound="pop", vol=0.4)
    lab(41.84, 45.48, "SELIMUT <b>DALAM</b> <b>BEG</b>", "👜")
    lab(48.56, 50.60, "BANTAL <b>ADA</b> <b>KAPAS</b>", "☁️")
    lab(50.62, 52.52, "SELIMUT + <b>BANTAL</b>", "😴", sound="chime", vol=0.35)
    night("tarik")
    lab(56.10, 57.66, "BESAR &amp; <b>PANJANG</b>", "📏")
    lab(57.74, 60.50, "NGAM UNTUK <b>SEORANG</b>", "🛌")
    lab(60.58, 61.80, "170", "🌙", kind="moon", unit="CM", sound="chime", vol=0.4)
    lab(80.00, 81.44, "SENANG <b>TRAVEL</b>", "🧳")
    lab(81.96, 84.30, "SIMPAN BALIK, <b>ZIP</b>!", "👌", sound="pop", vol=0.4)
    lab(84.92, 87.40, "MACAM-MACAM <b>KALER</b>", "🎨")
    lab(87.70, 88.84, "TEKAN <b>BEG</b> <b>KUNING</b>", "👇", sound="ding", vol=0.35)
    e0 = BT["end"]["t0"] - 0.05
    end = dict(t0=e0, t1=TOTAL, title="BEG BANTAL <b>SELIMUT</b> 🦉",
               sizes="🌙 3 IN 1 • 170CM • POKET TANGAN", cta="🛒 TEKAN BEG KUNING",
               heads=heads_for(e0, TOTAL), faces=faces_for(e0, TOTAL), py=1100)
    sfx.append(("hoot", e0 + 0.05, 0.45))
    sfx.append(("chime", e0 + 0.3, 0.3))
    sfx.append(("ding", e0 + 0.65, 0.3))
    return labels, wipes, tags, end, sfx


# ---------------------------------------------------------------- render
def run(cmd, **kw):
    print("+", " ".join(cmd[:6]), "...", flush=True)
    subprocess.run(cmd, check=True, **kw)


def render_base(sfx):
    cdir = os.path.join(OUT, "clips")
    os.makedirs(cdir, exist_ok=True)
    lst = []
    for i, c in enumerate(VCLIPS):
        z = c["z"]
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
    fc, al = [], []
    for i, c in enumerate(ACLIPS):
        if "silence" in c:
            fc.append(f"anullsrc=r=48000:cl=mono,atrim=0:{c['silence']:.3f}[a{i}]")
        else:
            d = c["e"] - c["s"]
            fc.append(f"[1:a]atrim={c['s']}:{c['e']},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=mono,"
                      f"afade=t=in:d=0.02,afade=t=out:st={d - 0.03:.3f}:d=0.03[a{i}]")
        al.append(f"[a{i}]")
    fc.append("".join(al) + f"concat=n={len(al)}:v=0:a=1,"
              "highpass=f=100,afftdn=nf=-25:tn=1,"
              "equalizer=f=250:t=q:w=1.0:g=-3,equalizer=f=3200:t=q:w=1.2:g=4,"
              "treble=g=2.5:f=9000,deesser=i=0.35,"
              "acompressor=threshold=-26dB:ratio=4:attack=4:release=90:makeup=2")
    probe = subprocess.run(["ffmpeg", "-nostats", "-vn", "-i", PROXY, "-filter_complex",
                            ";".join(fc).replace("[1:a]", "[0:a]") + ",ebur128", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
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


def write_comp(data):
    """comp/data.js + root duration + base video for the HyperFrames composition."""
    with open(os.path.join(COMP, "data.js"), "w") as f:
        f.write("// generated by edit.py - do not edit by hand\nwindow.EDIT = " +
                json.dumps(data, ensure_ascii=False, indent=1) + ";\n")
    idx = os.path.join(COMP, "index.html")
    html = open(idx).read()
    html = re.sub(r'(data-composition-id="main"[^>]*?data-duration=")[0-9.]+', rf"\g<1>{TOTAL:.3f}", html)
    html = re.sub(r'(id="bg"[^>]*?data-duration=")[0-9.]+', rf"\g<1>{TOTAL:.3f}", html)
    open(idx, "w").write(html)
    shutil.copyfile(os.path.join(OUT, "base.mp4"), os.path.join(COMP, "base.mp4"))


def render_hyperframes():
    hf = os.path.join(OUT, "hf.mp4")
    env = dict(os.environ)
    run(["npx", "--no-install", "hyperframes", "render", ".", "-o", hf, "--fps", str(FPS), "--workers", "3",
         "--quality", "delivery" if FINAL else "looks"], cwd=COMP, env=env)
    name = "final.mp4" if FINAL else "preview.mp4"
    scale = [] if FINAL else ["-vf", "scale=720:1280:flags=lanczos"]
    run(["ffmpeg", "-v", "error", "-y", "-i", hf, "-i", os.path.join(OUT, "base.mp4"), "-map", "0:v", "-map", "1:a",
         *scale, "-c:v", "libx264", "-preset", "slow" if FINAL else "medium", "-crf", "18" if FINAL else "20",
         "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
         "-c:a", "copy", "-t", f"{TOTAL:.3f}", "-movflags", "+faststart", os.path.join(OUT, name)])


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    words = timeline_words()
    labels, wipes, tags, end, sfx = graphics()
    data = dict(total=TOTAL, fps=FPS, w=CW, h=CH,
                safe=dict(l=SAFE_L, r=CW - SAFE_R, t=SAFE_T, b=CH - SAFE_B), lab_y=LAB_Y, cap_y=CAP_Y,
                captions=caption_chunks(words), labels=labels, wipes=wipes, tags=tags, end=end,
                blocks=[dict(name=b["name"], t0=b["t0"], dur=b["dur"]) for b in BLOCKS])
    with open(os.path.join(OUT, "edl.json"), "w") as f:
        json.dump(dict(data, sfx=sfx, heads_tl=[(round(i * 0.25, 2), heads_for(i * 0.25, i * 0.25 + 0.01))
                                                for i in range(int(TOTAL / 0.25) + 1)],
                       faces_tl=[(round(i * 0.25, 2), faces_for(i * 0.25, i * 0.25 + 0.01))
                                 for i in range(int(TOTAL / 0.25) + 1)],
                       vblocks=[{k: b[k] for k in ("name", "t0", "dur", "v", "a")} for b in BLOCKS]),
                  f, ensure_ascii=False, indent=1)
    print(f"timeline {TOTAL:.2f}s, {len(VCLIPS)} clips, {len(labels)} labels, {len(sfx)} sfx")
    if "--no-render" in sys.argv:
        sys.exit(0)
    if "--graphics-only" not in sys.argv:      # --graphics-only: reuse out/base.mp4, re-render the overlay layer
        render_base(sfx)
    write_comp(data)
    render_hyperframes()
