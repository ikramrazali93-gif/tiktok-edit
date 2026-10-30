#!/usr/bin/env python3
"""Edit for the bantal awan tapak kucing (IMG_3185 + IMG_3186): a pink cat-paw cloud cushion with a bunny face that
hides a pink blanket (zip at the back) and has a hand-warmer pocket, "Marshmallow awan 3D" look. Two clips of the
same product were joined: A (IMG_3185, 20.5s, a false start opening the grey bag, not used) then B (IMG_3186).
The graphics layer is a HyperFrames (HTML + GSAP) composition, as in ../bantal-selimut-beruang (same face-aware
placement). She wears a cartoon-character hoodie: it is never named anywhere.

Pipeline (all times in BLOCKS are source times of the joined master A+B; B starts at 20.521s):
  1. base.mp4      - cut/zoomed video + cleaned voice (v2 chain, -11.5 LUFS) + SFX       (ffmpeg)
  2. comp/data.js  - captions, labels, cloud wipes, end card + her head boxes for each of them (this script)
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
# Joined master: A = IMG_3185 (0-20.5s, she fights the grey bag and stops; nothing usable), B = IMG_3186 from
# 20.521s: grey bag -> pink paw cushion in plastic -> "design tapak kaki, panggil paw" -> pocket for the hands ->
# zip at the back -> blanket pulled out -> blanket spread out -> pillow + blanket + thumbs up.
# Hook: her "three in one" summary (bantal, selimut, hand warmer) from the end, over the pillow + blanket shot.
# v: list of (src_in, src_out, speed, zoom); a: 'same' (follow v at 1x), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK: "Three in one. Boleh jadi bantal, selimut dan juga boleh jadi hand warmer." ("Okey" before it cut)
    dict(name="hook", a="same", v=[(126.42, 130.02, 1, 1.0)]),
    # "Yang ini pun ada selimut tau."  (pillow just out of the grey bag)
    dict(name="unbox", a="same", v=[(25.20, 26.80, 1, 1.0)]),
    # pulling the plastic off (x5, no speech)
    dict(name="buka", a=None, v=[(26.80, 42.28, 5, 1.0)]),
    # "Wey, pattern baru lagi. | Gebu-gebas ya ni."
    dict(name="pattern", a="same", v=[(42.28, 43.70, 1, 1.0), (44.22, 45.22, 1, 1.05)]),
    # "Ni design tapak kaki tu. | Panggil apa? Paw. | Ha, panggil paw tau. Tapak kaki lah saya panggil."
    dict(name="paw", a="same", v=[(52.68, 54.42, 1, 1.0), (55.72, 57.18, 1, 1.06), (60.82, 63.03, 1, 1.0)]),
    # "Allah, warna pink pula tu."  ("Ha Allah comel" before it cut)
    dict(name="pink", a="same", v=[(68.72, 70.74, 1, 1.0)]),
    # "Yang ni pun ada lubang, ada pocket boleh masukkan tangan."
    dict(name="pocket", a="same", v=[(71.10, 74.20, 1, 1.0)]),
    # "Okey, buka zip daripada belakang."  (the unzip runs on past the line; starting after "Okey" clipped "buka")
    dict(name="zip", a="same", v=[(86.82, 90.05, 1, 1.0)]),
    # "Keluarkan selimut. Tuh selimut pun gebu, lembut je material selimut dia."
    dict(name="tarik", a="same", v=[(90.06, 94.12, 1, 1.0)]),
    # "Bantal dia tak kosong. Bantal dia still masih gebu."  ("Okey" cut)
    dict(name="kosong", a="same", v=[(94.84, 98.58, 1, 1.0)]),
    # "Selimut dia size 170cm. | ...ngam elok lah untuk kita orang dewasa ni buat baring. Ngam elok panjang dia."
    #  J-cut over the blanket held fully open
    dict(name="size", a=[(105.92, 108.56), (121.55, 125.72)], v=[(114.05, 120.86, 1, 1.0)]),
    # "Senang sangat bawa pi rombongan, drive semua. Boleh standby lah satu dalam kereta."  (thumbs up)
    dict(name="travel", a="same", v=[(133.50, 137.80, 1, 1.0)]),
    # CTA: "Ha tengok dekat beg kuning ni."  (J-cut over her holding the paw cushion)
    dict(name="cta", a=[(117.00, 117.96)], v=[(58.40, 59.36, 1, 1.0)]),
    # end card over her hugging the cushion (her "Ha gitu, three in one" muted)
    dict(name="end", a=None, v=[(64.60, 67.10, 1, 1.0)]),
]

FIX = {"bantai": "bantal", "Bantai": "Bantal", "zik": "zip", "Pou": "paw", "Pou.": "paw.", "pengebu": "pun gebu",
       "bagku": "beg kuning", "reta": "kereta", "driver": "drive", "gebul": "gebu", "kebu": "gebu"}


def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


# hand-checked words (per-chunk re-transcription + loudness envelope; the full pass drifts ~0.2-0.3s here)
OVERRIDE = {
    126.42: _w(("Three", 126.50, 126.72), ("in", 126.72, 126.96), ("one.", 126.96, 127.40), ("Boleh", 127.48, 127.62),
               ("jadi", 127.62, 127.76), ("bantal,", 127.76, 128.12), ("selimut", 128.16, 128.44), ("dan", 128.44, 128.64),
               ("juga", 128.64, 128.84), ("boleh", 128.84, 128.98), ("jadi", 128.98, 129.18), ("hand", 129.18, 129.54),
               ("warmer.", 129.54, 129.92)),
    25.20: _w(("Yang", 25.30, 25.56), ("ini", 25.56, 25.68), ("pun", 25.68, 25.80), ("ada", 25.80, 26.04),
              ("selimut", 26.04, 26.52), ("tau.", 26.52, 26.76)),
    42.28: _w(("Wey,", 42.32, 42.66), ("pattern", 42.74, 42.96), ("baru", 42.96, 43.22), ("lagi.", 43.22, 43.62)),
    44.22: _w(("Gebu-gebas", 44.24, 44.86), ("ya", 44.86, 45.04), ("ni.", 45.04, 45.20)),
    52.68: _w(("Ni", 52.72, 53.36), ("design", 53.36, 53.62), ("tapak", 53.62, 53.90), ("kaki", 53.90, 54.20),
              ("tu.", 54.20, 54.40)),
    55.72: _w(("Panggil", 55.74, 55.94), ("apa?", 55.94, 56.14), ("Paw.", 56.92, 57.16)),
    60.82: _w(("Panggil", 60.94, 61.46), ("paw", 61.46, 61.62), ("tau.", 61.62, 61.78), ("Tapak", 61.84, 62.10),
              ("kaki", 62.10, 62.40), ("lah", 62.40, 62.50), ("saya", 62.50, 62.60), ("panggil.", 62.60, 63.00)),
    68.72: _w(("Allah,", 68.84, 69.50), ("warna", 69.76, 70.12), ("pink", 70.12, 70.32), ("pula", 70.32, 70.52),
              ("tu.", 70.52, 70.70)),
    71.10: _w(("Yang", 71.14, 71.56), ("ni", 71.56, 71.72), ("pun", 71.72, 71.90), ("ada", 71.90, 72.36),
              ("lubang,", 72.36, 72.82), ("ada", 72.94, 73.06), ("pocket", 73.06, 73.30), ("boleh", 73.30, 73.50),
              ("masukkan", 73.50, 73.96), ("tangan.", 73.96, 74.18)),
    86.82: _w(("Buka", 87.02, 87.32), ("zip", 87.40, 87.66), ("daripada", 87.66, 87.84), ("belakang.", 87.84, 88.62)),
    90.06: _w(("Keluarkan", 90.20, 90.48), ("selimut.", 90.48, 90.98), ("Tuh", 91.14, 91.26), ("selimut", 91.26, 91.62),
              ("pun", 91.62, 91.86), ("gebu,", 91.86, 92.14), ("lembut", 92.14, 92.66), ("je", 92.66, 92.86),
              ("material", 92.86, 93.32), ("selimut", 93.32, 93.72), ("dia.", 93.72, 94.08)),
    94.84: _w(("Bantal", 94.86, 95.00), ("dia", 95.00, 95.14), ("tak", 95.14, 95.38), ("kosong.", 95.38, 95.92),
              ("Bantal", 96.20, 96.44), ("dia", 96.44, 96.62), ("still", 96.62, 96.96), ("masih", 96.96, 97.46),
              ("gebu.", 97.46, 98.50)),
    105.92: _w(("Selimut", 106.00, 106.46), ("dia", 106.46, 106.70), ("size", 106.70, 107.30), ("170CM.", 107.42, 108.50)),
    121.55: _w(("Ngam", 121.58, 121.78), ("elok", 121.78, 122.20), ("lah", 122.20, 122.34), ("untuk", 122.34, 122.52),
               ("kita", 122.52, 122.76), ("orang", 122.76, 122.92), ("dewasa", 122.92, 123.54), ("ni", 123.54, 123.70),
               ("buat", 123.70, 123.88), ("baring.", 123.88, 124.32), ("Ngam", 124.34, 124.66), ("elok", 124.66, 125.04),
               ("panjang", 125.04, 125.40), ("dia.", 125.40, 125.70)),
    133.50: _w(("Senang", 133.56, 133.94), ("sangat", 133.94, 134.18), ("bawa", 134.18, 134.36), ("pi", 134.36, 134.52),
               ("rombongan,", 134.52, 135.00), ("drive", 135.00, 135.28), ("semua.", 135.28, 135.58),
               ("Boleh", 135.66, 136.00), ("standby", 136.00, 136.42), ("lah", 136.42, 136.58), ("satu", 136.58, 136.76),
               ("dalam", 136.76, 136.92), ("kereta.", 136.92, 137.40)),
    117.00: _w(("Tengok", 117.16, 117.32), ("dekat", 117.32, 117.56), ("beg", 117.56, 117.68),
               ("kuning", 117.68, 117.80), ("ni.", 117.80, 117.96)),
}
DROP = []
KEYWORDS = {"THREE", "IN", "ONE", "BANTAL", "SELIMUT", "HAND", "WARMER", "PATTERN", "BARU", "GEBU-GEBAS", "TAPAK",
            "KAKI", "PAW", "PINK", "POCKET", "TANGAN", "LUBANG", "ZIP", "BELAKANG", "GEBU", "LEMBUT", "KOSONG",
            "170CM", "DEWASA", "BARING", "PANJANG", "ROMBONGAN", "KERETA", "STANDBY", "BEG", "KUNING"}

# ---------------------------------------------------------------- her head (face avoidance)
# Head + hood (+ niqab) box sampled every second from gridded proxy frames (fractions of the source frame, x0, y0,
# x1, y1). Seconds where the blanket hides her completely have no entry. edit.py turns these into px boxes (zoom
# applied) for each graphic's time window; the composition keeps every graphic HEAD_MARGIN px clear of all of them.
HEADS = [
    (25, (0.38, 0.11, 0.84, 0.46)), (26, (0.30, 0.11, 0.76, 0.46)), (27, (0.36, 0.09, 0.82, 0.46)),
    (28, (0.24, 0.11, 0.64, 0.44)), (29, (0.14, 0.16, 0.62, 0.46)), (30, (0.10, 0.11, 0.62, 0.44)),
    (31, (0.12, 0.11, 0.64, 0.44)), (32, (0.24, 0.11, 0.76, 0.44)), (33, (0.18, 0.14, 0.72, 0.46)),
    (34, (0.22, 0.14, 0.76, 0.46)), (35, (0.18, 0.14, 0.70, 0.44)), (36, (0.24, 0.11, 0.74, 0.44)),
    (37, (0.24, 0.11, 0.76, 0.44)), (38, (0.24, 0.11, 0.76, 0.44)), (39, (0.15, 0.11, 0.66, 0.44)),
    (40, (0.24, 0.11, 0.76, 0.44)), (41, (0.24, 0.11, 0.80, 0.46)), (42, (0.20, 0.14, 0.76, 0.46)),
    (43, (0.20, 0.11, 0.72, 0.46)), (44, (0.20, 0.11, 0.76, 0.46)), (45, (0.24, 0.11, 0.80, 0.46)),
    (52, (0.30, 0.14, 0.80, 0.49)), (53, (0.36, 0.14, 0.88, 0.49)), (54, (0.30, 0.14, 0.76, 0.49)),
    (55, (0.24, 0.14, 0.76, 0.46)), (56, (0.18, 0.12, 0.70, 0.46)), (57, (0.28, 0.11, 0.76, 0.46)),
    (58, (0.18, 0.11, 0.70, 0.46)), (59, (0.20, 0.11, 0.72, 0.46)), (60, (0.20, 0.11, 0.72, 0.46)),
    (61, (0.15, 0.11, 0.66, 0.46)), (62, (0.18, 0.11, 0.72, 0.44)), (63, (0.24, 0.09, 0.76, 0.42)),
    (64, (0.18, 0.09, 0.66, 0.42)), (65, (0.15, 0.09, 0.76, 0.46)), (66, (0.15, 0.11, 0.76, 0.46)),
    (67, (0.24, 0.11, 0.76, 0.46)), (68, (0.34, 0.09, 0.86, 0.49)), (69, (0.30, 0.11, 0.76, 0.46)),
    (70, (0.24, 0.11, 0.76, 0.44)), (71, (0.36, 0.09, 0.93, 0.46)), (72, (0.38, 0.09, 0.96, 0.46)),
    (73, (0.38, 0.14, 0.90, 0.46)), (74, (0.34, 0.16, 0.86, 0.42)), (75, (0.24, 0.14, 0.76, 0.42)),
    (86, (0.54, 0.11, 1.00, 0.51)), (87, (0.60, 0.11, 1.00, 0.51)), (88, (0.76, 0.00, 1.00, 0.51)),
    (89, (0.86, 0.00, 1.00, 0.42)), (90, (0.92, 0.00, 1.00, 0.36)), (93, (0.90, 0.00, 1.00, 0.36)),
    (94, (0.74, 0.00, 1.00, 0.46)), (95, (0.48, 0.07, 0.96, 0.46)), (96, (0.36, 0.09, 0.90, 0.49)),
    (97, (0.44, 0.14, 0.96, 0.49)), (98, (0.54, 0.14, 1.00, 0.51)), (99, (0.38, 0.14, 0.92, 0.49)),
    (114, (0.40, 0.00, 0.96, 0.26)), (115, (0.44, 0.00, 1.00, 0.26)), (118, (0.36, 0.21, 0.70, 0.43)),
    (123, (0.46, 0.21, 0.86, 0.49)), (124, (0.48, 0.19, 0.96, 0.49)), (125, (0.38, 0.14, 0.92, 0.51)),
    (126, (0.13, 0.14, 0.96, 0.71)), (127, (0.33, 0.17, 0.92, 0.49)), (128, (0.36, 0.17, 0.92, 0.49)),
    (129, (0.26, 0.14, 0.86, 0.49)), (130, (0.04, 0.19, 0.66, 0.56)), (131, (0.16, 0.19, 0.74, 0.49)),
    (132, (0.13, 0.17, 0.66, 0.49)), (133, (0.00, 0.17, 0.56, 0.49)), (134, (0.28, 0.14, 0.82, 0.42)),
    (135, (0.28, 0.14, 0.82, 0.42)), (136, (0.28, 0.14, 0.86, 0.42)), (137, (0.33, 0.11, 0.94, 0.40)),
    (138, (0.28, 0.12, 0.82, 0.40)),
]
# The bunny face on the paw cushion when it is held up front: graphics steer off these points when they can.
FACES = [
    (52, [(0.45, 0.50)]), (53, [(0.62, 0.52)]), (61, [(0.50, 0.52)]), (62, [(0.48, 0.48)]), (63, [(0.48, 0.52)]),
    (69, [(0.45, 0.50)]), (70, [(0.45, 0.50)]), (71, [(0.15, 0.55)]), (72, [(0.15, 0.55)]), (73, [(0.20, 0.55)]),
    (74, [(0.48, 0.48)]), (97, [(0.60, 0.55)]), (98, [(0.62, 0.58)]), (114, [(0.35, 0.62)]), (115, [(0.65, 0.62)]),
    (127, [(0.55, 0.55)]), (128, [(0.55, 0.55)]), (129, [(0.55, 0.55)]), (133, [(0.55, 0.50)]),
    (134, [(0.25, 0.55)]), (135, [(0.40, 0.52)]), (136, [(0.38, 0.58)]), (137, [(0.55, 0.50)]),
]
HEAD_PAD = 0.5          # also count samples this many seconds outside a graphic's source range (1s grid)
LAB_Y, CAP_Y = 1060, 1405  # preferred centres (px): her head sits high, so labels go mid-frame; captions low


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
        tail = ((w["w"].lower().strip(",.?!") in ("ni", "kan", "dia", "ini", "lah") and w["e"] - w["s"] < 0.6)
                or (len(cur) == 3 and w["w"][-1] in ",.?!"
                    and sum(len(x["w"]) for x in cur) + len(w["w"]) <= 21))   # a short tail word / the sentence's last word joins
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

    def lab(s0, s1, text, emoji="", sound="jelly", vol=0.5, src=True, kind="cloud", big=False):
        t0, t1 = (tl(s0), tl(s1)) if src else (s0, s1)
        labels.append(dict(t0=t0, t1=t1, html=text, emoji=emoji, kind=kind, big=big,
                           heads=heads_for(t0, t1), faces=faces_for(t0, t1)))
        if sound:
            sfx.append((sound, t0 - 0.03, vol))
        if big:
            sfx.append(("bubble", t0 + 0.1, 0.4))

    def puff(block, sound="poof", vol=0.5):
        t = BT[block]["t0"]
        wipes.append(dict(t=t))
        sfx.append((sound, t - 0.34, vol))

    def tag(block, text):
        b = BT[block]
        tags.append(dict(t0=b["t0"] + 0.05, t1=b["t0"] + b["dur"] - 0.05, text=text))
        sfx.append(("click", b["t0"] + 0.05, 0.35))

    # hook: three in one
    lab(126.50, 127.40, "<b>3 IN 1!</b>", "🐾", kind="puff", sound="jelly", vol=0.6)
    lab(127.48, 128.44, "BANTAL + <b>SELIMUT</b>", "☁️", sound="bubble", vol=0.5)
    lab(128.84, 129.92, "+ <b>HAND WARMER</b>", "🧤", big=True, sound="jelly", vol=0.55)
    # unboxing
    lab(25.30, 26.76, "ADA <b>SELIMUT</b> TAU!", "🤫", sound="pop", vol=0.45)
    tag("buka", "&gt;&gt; x5")
    lab(42.32, 43.62, "<b>CORAK BARU!</b>", "✨", sound="sparkle", vol=0.35)
    lab(44.24, 45.20, "<b>GEBU-GEBAS</b>", "☁️", sound="squish", vol=0.45)
    # the paw
    lab(52.72, 54.40, "DESIGN <b>TAPAK KAKI</b>", "🐾", sound="jelly")
    lab(55.74, 57.16, "PANGGIL <b>APA?</b>", "🤔", sound="bubble", vol=0.45)
    lab(60.94, 63.00, "<b>PAW!</b>", "🐾", kind="puff", sound="jelly", vol=0.6)
    lab(68.84, 70.70, "WARNA <b>PINK</b>", "💗", sound="sparkle", vol=0.35)
    lab(71.14, 72.82, "ADA <b>LUBANG</b>", "👀", sound="pop", vol=0.45)
    lab(72.94, 74.18, "MASUK <b>TANGAN!</b>", "🧤", sound="bubble", vol=0.45)
    puff("zip")
    lab(87.02, 88.62, "BUKA <b>ZIP</b> BELAKANG", "🔓", sound="zip", vol=0.5)
    lab(90.20, 90.98, "KELUAR <b>SELIMUT</b>", "🫴", sound="pop", vol=0.45)
    lab(91.14, 94.08, "SELIMUT <b>GEBU & LEMBUT</b>", "☁️", sound="squish", vol=0.45)
    lab(94.86, 95.92, "BANTAL <b>TAK KOSONG</b>", "👌", sound="jelly")
    lab(96.20, 98.50, "MASIH <b>GEBU!</b>", "🤗", big=True, sound="squish", vol=0.5)
    puff("size")
    lab(106.20, 108.50, "SELIMUT <b>170CM</b>", "📏", big=True, sound="jelly", vol=0.55)
    lab(121.58, 124.32, "NGAM <b>ORANG DEWASA</b>", "🛌", sound="bubble", vol=0.45)
    lab(124.34, 125.70, "<b>PANJANG</b> NGAM!", "👍", sound="pop", vol=0.45)
    lab(133.58, 135.58, "BAWA <b>ROMBONGAN</b>", "🚌", sound="bubble", vol=0.45)
    lab(135.66, 137.40, "STANDBY DALAM <b>KERETA</b>", "🚗", sound="jelly")
    lab(117.02, 117.96, "TEKAN <b>BEG KUNING</b>", "🛒", sound="ding", vol=0.35)
    e0 = BT["end"]["t0"] - 0.05
    end = dict(t0=e0, t1=TOTAL, title="BANTAL <b>AWAN</b> 🐾",
               sizes="☁️ 3 IN 1 • SELIMUT • HAND WARMER", cta="🛒 TEKAN BEG KUNING",
               heads=heads_for(e0, TOTAL), faces=faces_for(e0, TOTAL), py=1120)
    sfx.append(("poof", e0 + 0.02, 0.5))
    sfx.append(("bubble", e0 + 0.3, 0.4))
    sfx.append(("ding", e0 + 0.7, 0.3))
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
