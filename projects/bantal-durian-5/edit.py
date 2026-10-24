#!/usr/bin/env python3
"""Edit for bantal peluk durian #5 (IMG_3065), "Retro sticker 90an" look. Fifth video of the durian series; the
graphics layer is a HyperFrames (HTML + GSAP) composition, as in ../bantal-durian and ../bantal-durian-2.

Pipeline (all times in BLOCKS are source times of the original clip, same timeline as the proxy):
  1. base.mp4      - cut/zoomed video + cleaned voice (v2 chain, -11.5 LUFS) + SFX       (ffmpeg)
  2. comp/data.js  - captions, labels, sweeps, end card + her head boxes for each of them (this script)
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
# One handheld clip on a dirt road: she walks up from far away holding the small durian pillow (0-6s), then shows
# the big one, the sizes, close-ups of the big pillow's face, and ends with a thumbs-up.
# Her opening line is the hook ("bukan bantal biasa ... teman tidur paling setia"), so it stays first; the joke that
# pays it off ("tak berdengkur, tak bising, tak tidur, mata sentiasa terbuka", 31.8-41.2s) is moved right after it.
# v: list of (src_in, src_out, speed, zoom); a: 'same' (follow v at 1x), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK: "Ini bukan bantal biasa tahu, | ni teman tidur paling setia."  (walk-in, zoomed so she isn't tiny)
    dict(name="hook", a="same", v=[(0.00, 2.18, 1, 1.8), (2.18, 5.02, 1, 1.35)]),
    # "Dia tak berdengkur, tak bunyi bising, | dia teman korang, dia tak tidur. Korang tengok mata dia akan
    #  terbuka saja sentiasa, | tak pernah tutup mata dia."  (moved from 31.8s; 0.3s pause before "dia teman" cut)
    dict(name="setia", a="same", v=[(31.82, 35.76, 1, 1.0), (36.05, 38.60, 1, 1.0), (38.60, 41.22, 1, 1.08)]),
    # "Kalau saiz ni tak cukup besar untuk korang, ada lagi saiz yang lagi besar."
    dict(name="saiz", a="same", v=[(5.08, 7.70, 1, 1.0), (7.70, 10.34, 1, 1.05)]),
    # "Dia ada macam-macam saiz tahu, empat saiz ada."  ("MashaAllah" cut)
    dict(name="macam", a="same", v=[(11.93, 14.56, 1, 1.0)]),
    # "Yang ni paling besar, saiz 95cm, | yang ni memang betul-betul peneman tidur macam ni."
    dict(name="besar", a="same", v=[(14.88, 17.50, 1, 1.0), (17.50, 20.48, 1, 1.06)]),
    # "Saiz 30cm untuk anak baby-baby boleh kan."  (confusing "kalau yang ni tak cukup besar ni, yang ni" cut)
    dict(name="kecil", a="same", v=[(23.06, 26.40, 1, 1.0)]),
    # "Gebu-gebas macam ni korang. (Nah,) yang ni Allah sedapnya buat peneman tidur."  ("Okey" cut)
    dict(name="gebu", a="same", v=[(26.97, 29.30, 1, 1.0), (29.30, 31.80, 1, 1.05)]),
    # "Sangat-sangat selesa."  ("ok" before it and the repeated "gebu-gebas" after it cut)
    dict(name="selesa", a="same", v=[(41.92, 44.58, 1, 1.0)]),
    # CTA: "Tengok dekat bawah sekarang."  (the yellow bag sits at the bottom of the screen)
    dict(name="cta", a="same", v=[(47.86, 49.52, 1, 1.0)]),
    # end card over her thumbs-up with both pillows, slowed down (muted)
    dict(name="end", a=None, v=[(46.66, 47.70, 0.5, 1.0)]),
]

FIX = {"bantai": "bantal", "tidok": "tidur", "tiduk": "tidur", "berdengker": "berdengkur", "pemata": "mata",
       "permata": "mata", "tau": "tahu", "size": "saiz"}


def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


# hand-checked words for every kept range (re-transcribed per chunk + RMS envelope); used instead of the raw
# full-file transcript
WORDS = _w(
    ("Ini", 0.00, 0.50), ("bukan", 0.50, 0.76), ("bantal", 0.76, 1.14), ("biasa", 1.14, 1.60), ("tahu,", 1.60, 1.96),
    ("ni", 2.18, 2.36), ("teman", 2.36, 2.72), ("tidur", 2.72, 3.10), ("paling", 3.10, 3.68), ("setia.", 3.68, 4.90),
    ("Kalau", 5.10, 5.38), ("saiz", 5.38, 5.66), ("ni", 5.66, 5.78), ("tak", 5.78, 5.98), ("cukup", 5.98, 6.20),
    ("besar", 6.20, 6.36), ("untuk", 6.36, 6.60), ("korang,", 6.60, 7.20), ("ada", 7.50, 7.88), ("lagi", 7.88, 8.18),
    ("saiz", 8.18, 8.58), ("yang", 8.58, 8.80), ("lagi", 8.80, 9.34), ("besar!", 9.34, 10.30),
    ("Dia", 11.95, 12.08), ("ada", 12.08, 12.42), ("macam-macam", 12.42, 12.92), ("saiz", 12.92, 13.20),
    ("tahu,", 13.20, 13.38), ("empat", 13.64, 13.92), ("saiz", 13.92, 14.28), ("ada.", 14.28, 14.52),
    ("Yang", 14.90, 15.16), ("ni", 15.16, 15.38), ("paling", 15.38, 15.64), ("besar,", 15.64, 16.12),
    ("saiz", 16.28, 16.50), ("95cm.", 16.50, 17.40), ("Yang", 17.66, 17.82), ("ni", 17.82, 17.98),
    ("memang", 17.98, 18.24), ("betul-betul", 18.24, 18.76), ("peneman", 18.76, 19.20), ("tidur", 19.20, 19.56),
    ("macam", 19.56, 19.84), ("ni.", 19.84, 20.44),
    ("Saiz", 23.14, 23.44), ("30cm", 23.44, 24.12), ("untuk", 24.12, 24.50), ("anak", 24.50, 24.86),
    ("baby-baby", 24.86, 25.46), ("boleh", 25.46, 26.08), ("kan.", 26.08, 26.38),
    ("Gebu-gebas", 27.00, 27.66), ("macam", 27.66, 27.88), ("ni", 27.88, 28.00), ("korang.", 28.00, 28.58),
    ("Nah,", 28.70, 29.12), ("yang", 29.14, 29.26), ("ni", 29.26, 29.50), ("Allah,", 29.50, 30.04),
    ("sedapnya", 30.04, 30.68), ("buat", 30.68, 30.82), ("peneman", 30.82, 31.40), ("tidur.", 31.40, 31.76),
    ("Dia", 31.86, 32.00), ("tak", 32.00, 32.22), ("berdengkur,", 32.22, 33.54), ("tak", 34.20, 34.40),
    ("bunyi", 34.40, 34.72), ("bising,", 34.72, 35.74),
    ("dia", 36.08, 36.24), ("teman", 36.24, 36.54), ("korang,", 36.54, 36.96), ("dia", 36.98, 37.12),
    ("tak", 37.12, 37.26), ("tidur.", 37.26, 37.60), ("Korang", 37.74, 37.98), ("tengok", 37.98, 38.18),
    ("mata", 38.18, 38.44), ("dia", 38.44, 38.60), ("akan", 38.60, 38.74), ("terbuka", 38.74, 39.28),
    ("saja", 39.28, 39.44), ("sentiasa,", 39.44, 40.00), ("tak", 40.14, 40.22), ("pernah", 40.22, 40.36),
    ("tutup", 40.36, 40.70), ("mata", 40.70, 41.00), ("dia.", 41.00, 41.20),
    ("Sangat-sangat", 41.95, 43.56), ("selesa.", 43.56, 44.56),
    ("Tengok", 47.90, 48.38), ("dekat", 48.38, 48.80), ("bawah", 48.80, 48.98), ("sekarang.", 48.98, 49.40),
)
OVERRIDE = {}
DROP = [(28.65, 29.13)]    # "Nah," - too faint to caption with confidence (audio kept)
KEYWORDS = {"BUKAN", "BIASA", "TEMAN", "TIDUR", "SETIA", "BERDENGKUR", "BISING", "MATA", "TERBUKA", "SENTIASA",
            "SAIZ", "BESAR", "BESAR!", "MACAM-MACAM", "EMPAT", "95CM", "30CM", "BABY-BABY", "GEBU-GEBAS",
            "SEDAPNYA", "PENEMAN", "SELESA", "SANGAT-SANGAT", "BAWAH", "SEKARANG"}

# ---------------------------------------------------------------- her head (face avoidance)
# Head + hood box sampled every second from gridded proxy frames (fractions of the source frame, x0, y0, x1, y1).
# edit.py turns these into px boxes (zoom applied) for each graphic's time window; the composition keeps every
# graphic HEAD_MARGIN px clear of all of them.
HEADS = [
    (0, (0.49, 0.31, 0.63, 0.43)), (1, (0.47, 0.31, 0.62, 0.43)), (2, (0.51, 0.29, 0.66, 0.43)),
    (3, (0.46, 0.29, 0.65, 0.43)), (4, (0.41, 0.29, 0.63, 0.46)), (5, (0.39, 0.27, 0.71, 0.48)),
    (6, (0.29, 0.24, 0.79, 0.51)), (7, (0.21, 0.26, 0.73, 0.59)), (8, (0.00, 0.32, 0.61, 0.69)),
    (9, (0.29, 0.29, 0.96, 0.69)), (10, (0.39, 0.29, 0.81, 0.63)), (11, (0.34, 0.29, 0.72, 0.59)),
    (12, (0.34, 0.29, 0.71, 0.57)), (13, (0.53, 0.29, 0.87, 0.56)), (14, (0.47, 0.22, 0.76, 0.48)),
    (15, (0.39, 0.21, 0.80, 0.48)), (16, (0.32, 0.24, 0.71, 0.49)), (17, (0.39, 0.25, 0.73, 0.51)),
    (18, (0.41, 0.26, 0.74, 0.53)), (19, (0.32, 0.21, 0.73, 0.49)), (20, (0.30, 0.19, 0.67, 0.49)),
    (21, (0.32, 0.18, 0.71, 0.46)), (22, (0.34, 0.19, 0.72, 0.46)), (23, (0.34, 0.19, 0.76, 0.46)),
    (24, (0.36, 0.18, 0.76, 0.43)), (25, (0.36, 0.19, 0.76, 0.45)), (26, (0.36, 0.19, 0.76, 0.45)),
    (27, (0.36, 0.19, 0.78, 0.45)), (28, (0.32, 0.21, 0.68, 0.46)), (29, (0.32, 0.22, 0.72, 0.46)),
    (30, (0.30, 0.18, 0.74, 0.45)), (31, (0.30, 0.11, 0.72, 0.41)), (32, (0.39, 0.02, 0.89, 0.34)),
    (33, (0.51, 0.02, 1.00, 0.36)), (34, (0.61, 0.00, 1.00, 0.31)), (35, (0.69, 0.00, 1.00, 0.26)),
    (36, (0.69, 0.00, 1.00, 0.31)), (37, (0.57, 0.14, 0.96, 0.43)), (38, (0.47, 0.16, 0.89, 0.43)),
    (39, (0.47, 0.22, 0.80, 0.48)), (40, (0.41, 0.21, 0.74, 0.47)), (41, (0.43, 0.21, 0.74, 0.47)),
    (42, (0.51, 0.20, 0.84, 0.44)), (43, (0.41, 0.19, 0.80, 0.43)), (44, (0.34, 0.15, 0.72, 0.39)),
    (45, (0.32, 0.12, 0.72, 0.39)), (46, (0.36, 0.05, 1.00, 0.37)), (47, (0.45, 0.13, 0.93, 0.41)),
    (48, (0.30, 0.21, 0.78, 0.44)), (49, (0.28, 0.23, 0.70, 0.47)),
]
# Pillow smileys in the big close-ups (the frame is mostly pillow there): graphics steer off these when they can.
FACES = [
    (31, [(0.40, 0.30), (0.45, 0.55), (0.45, 0.80)]), (32, [(0.35, 0.33), (0.48, 0.60), (0.44, 0.81)]),
    (33, [(0.42, 0.27), (0.54, 0.55), (0.50, 0.81)]), (34, [(0.42, 0.33), (0.75, 0.75)]),
    (35, [(0.65, 0.35), (0.81, 0.85)]), (36, [(0.60, 0.37), (0.69, 0.77)]),
]
HEAD_PAD = 0.5          # also count samples this many seconds outside a graphic's source range (1s grid)
LAB_Y, CAP_Y = 270, 1405  # preferred centres (px): labels in the top band, captions just above the TikTok caption


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
    words = WORDS                                # hand-checked (see WORDS); TRANSCRIPT is kept for reference
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
        tail = w["w"].lower().strip(",.?!") in ("ni", "kan") and w["e"] - w["s"] < 0.6   # short tail word joins
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

    def lab(s0, s1, text, emoji="", sound="boing", vol=0.4, src=True, kind="sticker", big=False, unit=None,
            color=None):
        t0, t1 = (tl(s0), tl(s1)) if src else (s0, s1)
        labels.append(dict(t0=t0, t1=t1, html=text, emoji=emoji, kind=kind, big=big, unit=unit, color=color,
                           heads=heads_for(t0, t1), faces=faces_for(t0, t1)))
        if sound:
            sfx.append((sound, t0 - 0.03, vol))

    def wipe(block, sound="scratch", vol=0.35):
        t = BT[block]["t0"]
        wipes.append(dict(t=t))
        sfx.append((sound, t - 0.28, vol))

    # hook: walk-in, "bukan bantal biasa ... teman tidur paling setia"
    lab(0.02, 2.12, "BUKAN BANTAL <b>BIASA!</b>", "🙅‍♀️", sound="blip", vol=0.4, big=True, color="pink")
    lab(2.20, 4.96, "PALING <b>SETIA!</b>", "💛", sound="boing", vol=0.45, big=True, color="teal")
    # the payoff joke (moved up)
    wipe("setia", sound="scratch", vol=0.4)
    lab(31.90, 33.54, "TAK <b>BERDENGKUR</b>", "😴", color="purple")
    lab(34.22, 35.74, "TAK <b>BISING</b>", "🤫", sound="blip", color="yellow")
    lab(36.10, 36.96, "TEMAN <b>KORANG</b>", "🫶", sound="pop", color="pink")
    lab(37.00, 38.60, "DIA TAK <b>TIDUR!</b>", "👀", color="teal")
    lab(38.66, 41.20, "MATA <b>TAK TUTUP!</b>", "👁️", sound="blip", big=True, color="yellow")
    # sizes
    wipe("saiz", sound="whoosh", vol=0.35)
    lab(5.10, 7.20, "TAK CUKUP <b>BESAR?</b>", "🤔", color="purple")
    lab(7.50, 10.30, "ADA LAGI <b>BESAR!</b>", "😮", big=True, color="pink")
    lab(11.96, 13.38, "MACAM-MACAM <b>SAIZ</b>", "📏", sound="blip", color="teal")
    lab(13.62, 14.54, "4", "✌️", kind="num", unit="SAIZ", sound="impact", vol=0.3, color="yellow")
    lab(14.90, 16.12, "PALING <b>BESAR</b>", "💪", color="pink")
    lab(16.28, 17.50, "95", "📐", kind="num", unit="CM", sound="impact", vol=0.3, color="teal")
    lab(17.70, 20.44, "PENEMAN <b>TIDUR</b>", "🛌", color="purple")
    lab(23.14, 24.12, "30", "🍼", kind="num", unit="CM", sound="impact", vol=0.3, color="pink")
    lab(24.14, 26.38, "UNTUK <b>BABY</b>", "👶", sound="pop", color="yellow")
    wipe("gebu", sound="whoosh", vol=0.35)
    lab(27.12, 28.58, "GEBU-<b>GEBAS!</b>", "☁️", big=True, color="teal")
    lab(29.50, 31.76, "SEDAP BUAT <b>TIDUR</b>", "🥱", sound="pop", color="purple")
    lab(41.95, 44.56, "SANGAT <b>SELESA!</b>", "🥰", sound="blip", big=True, color="pink")
    lab(47.90, 49.50, "TEKAN <b>BEG KUNING</b> 👇", "🛒", sound="ding", vol=0.35, color="yellow")
    e0 = BT["end"]["t0"] - 0.05
    end = dict(t0=e0, t1=TOTAL, title="BANTAL PELUK <b>DURIAN</b>",
               sub="TEMAN TIDUR PALING SETIA 💛", sizes="📏 4 SAIZ • 95CM - 30CM", cta="🛒 TEKAN BEG KUNING",
               heads=heads_for(e0, TOTAL), faces=faces_for(e0, TOTAL), py=1150)
    sfx.append(("boing", e0 + 0.05, 0.4))
    sfx.append(("blip", e0 + 0.35, 0.3))
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
