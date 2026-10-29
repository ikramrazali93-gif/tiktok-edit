#!/usr/bin/env python3
"""Edit for the bantal selimut beruang strawberry (IMG_3181): a pink strawberry-bear pillow that unzips into a
blanket, "Kedai kek strawberry" (bakery) look. The graphics layer is a HyperFrames (HTML + GSAP) composition, as in
../bantal-durian-2 (same face-aware placement). Never name the character the product resembles anywhere.

Pipeline (all times in BLOCKS are source times of the original clip, same timeline as the proxy):
  1. base.mp4      - cut/zoomed video + cleaned voice (v2 chain, -11.5 LUFS) + SFX       (ffmpeg)
  2. comp/data.js  - captions, labels, icing pours, end card + her head boxes for each of them (this script)
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
# One 147s handheld clip on a lawn: ~60s of opening a red heart-print bag and the plastic, then the pillow, the
# unzip, the blanket spread out, and the pillow + blanket together. The hook pairs her "siapa minat warna pink"
# question with the "two in one" line from the end, then a fast unboxing and the unzip -> blanket reveal.
# v: list of (src_in, src_out, speed, zoom); a: 'same' (follow v at 1x), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK: "Siapa minat warna pink-pink gini?" (pillow up front) + "Okay, two in one. Dua dalam satu." (pillow +
    #  blanket together, from the end of the clip)
    dict(name="hook", a="same", v=[(62.15, 63.85, 1, 1.0), (130.55, 132.75, 1, 1.0)]),
    # "Okay, jom kita unboxing."
    dict(name="unbox", a="same", v=[(41.62, 42.88, 1, 1.0)]),
    # opening the plastic (x4, no speech)
    dict(name="buka1", a=None, v=[(43.0, 50.36, 4, 1.0)]),
    # "Alahai, comelnya."
    dict(name="comel", a="same", v=[(50.36, 51.88, 1, 1.05)]),
    # pulling the pillow out of the plastic (x4)
    dict(name="buka2", a=None, v=[(51.9, 58.86, 4, 1.0)]),
    # "Tadaa!"
    dict(name="tada", a="same", v=[(58.88, 60.12, 1, 1.0)]),
    # "Yang ni kan dia ada selimut tau dekat dalam."
    dict(name="dalam", a="same", v=[(71.55, 73.30, 1, 1.0)]),
    # "Boleh bawa travel, | belakang dia ada selimut."
    dict(name="travel", a="same", v=[(83.05, 84.70, 1, 1.0), (84.70, 87.06, 1, 1.06)]),
    # "Di belakang, | ambil selimut dalam dia."  (pause between cut; Whisper also heard "Buka belakang")
    dict(name="zip", a="same", v=[(88.62, 89.72, 1, 1.0), (91.15, 92.25, 1, 1.05)]),
    # pulling the blanket out (x2.5)
    dict(name="tarik", a=None, v=[(92.3, 96.7, 2.5, 1.0)]),
    # "Bantal dia pun besar lah, | gebu lah, lembut lah."  (unclear "sebab kemudian tu" cut)
    dict(name="besar", a="same", v=[(96.82, 98.86, 1, 1.0), (99.70, 100.98, 1, 1.05)]),
    # "Dan ni selimut dia."
    dict(name="selimut", a="same", v=[(101.40, 102.75, 1, 1.0)]),
    # "Woi, lawa selimut."  (blanket thrown open)
    dict(name="lawa", a="same", v=[(108.85, 110.42, 1, 1.0)]),
    # "Nampak tak selimutnya bercorak."  (J-cut over the blanket held fully open)
    dict(name="corak", a=[(118.45, 120.62)], v=[(113.05, 115.22, 1, 1.0)]),
    # "Sekali dengan selimut, dengan bantal dia sekali."
    dict(name="sekali", a="same", v=[(127.55, 130.08, 1, 1.0)]),
    # "Pink lover, sila dapatkan yang ini."
    dict(name="pink", a="same", v=[(136.72, 139.05, 1, 1.0)]),
    # CTA: "Korang boleh grab, tengok dekat beg kuning."
    dict(name="cta", a="same", v=[(132.95, 134.78, 1, 1.0)]),
    # "Cepat sampai, ready stock."
    dict(name="ready", a="same", v=[(140.62, 142.45, 1, 1.0)]),
    # end card over the last shot ("Okay, terima kasih ..." muted)
    dict(name="end", a=None, v=[(142.45, 145.0, 1, 1.0)]),
]

FIX = {"bantai": "bantal", "comenya": "comelnya", "Comenya": "Comelnya", "gebul": "gebu", "grad": "grab",
       "bag": "beg", "kebu": "gebu"}


def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


# hand-checked words (per-chunk re-transcription + loudness envelope; the full pass drifts up to ~0.9s here)
OVERRIDE = {
    62.15: _w(("Siapa", 62.20, 62.40), ("minat", 62.40, 62.62), ("warna", 62.62, 62.90), ("pink-pink", 62.90, 63.36),
              ("gini?", 63.36, 63.80)),
    130.55: _w(("Okay,", 130.62, 130.78), ("two", 130.78, 130.90), ("in", 130.90, 131.10), ("one.", 131.10, 131.40),
               ("Dua", 131.66, 131.82), ("dalam", 131.82, 132.12), ("satu.", 132.12, 132.68)),
    41.62: _w(("Okay,", 41.66, 41.90), ("jom", 41.92, 42.08), ("kita", 42.08, 42.42), ("unboxing.", 42.42, 42.86)),
    50.36: _w(("Alahai,", 50.40, 51.00), ("comelnya.", 51.00, 51.84)),
    58.88: _w(("Tadaa!", 58.92, 60.06)),
    71.55: _w(("Yang", 71.60, 71.76), ("ni", 71.76, 71.88), ("kan", 71.88, 72.02), ("dia", 72.02, 72.14),
              ("ada", 72.14, 72.30), ("selimut", 72.30, 72.68), ("tau", 72.68, 72.80), ("dekat", 72.80, 72.96),
              ("dalam.", 72.96, 73.26)),
    83.05: _w(("Boleh", 83.10, 83.56), ("bawa", 83.56, 83.78), ("travel,", 83.78, 84.52)),
    84.70: _w(("belakang", 84.80, 85.02), ("dia", 85.02, 85.16), ("ada", 85.16, 85.36), ("selimut.", 85.36, 86.60)),
    88.62: _w(("Di", 88.64, 88.98), ("belakang,", 88.98, 89.68)),
    91.15: _w(("ambil", 91.20, 91.46), ("selimut", 91.46, 91.76), ("dalam", 91.76, 92.00), ("dia.", 92.00, 92.22)),
    96.82: _w(("Bantal", 96.86, 97.68), ("dia", 97.68, 97.82), ("pun", 97.82, 97.96), ("besar", 97.96, 98.48),
              ("lah,", 98.48, 98.84)),
    99.70: _w(("gebu", 99.74, 100.16), ("lah,", 100.16, 100.36), ("lembut", 100.36, 100.70), ("lah.", 100.70, 100.92)),
    101.40: _w(("Dan", 101.52, 101.86), ("ni", 101.86, 102.12), ("selimut", 102.12, 102.58), ("dia.", 102.58, 102.72)),
    108.85: _w(("Woi,", 108.90, 109.20), ("lawa", 109.26, 109.80), ("selimut!", 109.80, 110.38)),
    118.45: _w(("Nampak", 118.50, 118.82), ("tak", 118.82, 119.00), ("selimutnya", 119.00, 119.42),
               ("bercorak.", 119.42, 120.54)),
    127.55: _w(("Sekali", 127.58, 127.72), ("dengan", 127.72, 127.96), ("selimut,", 127.96, 128.76),
               ("dengan", 128.80, 129.12), ("bantal", 129.12, 129.58), ("dia", 129.58, 129.76),
               ("sekali.", 129.76, 130.04)),
    136.72: _w(("Pink", 136.80, 137.32), ("lover,", 137.32, 137.72), ("sila", 137.72, 138.10),
               ("dapatkan", 138.10, 138.52), ("yang", 138.52, 138.68), ("ini.", 138.68, 139.00)),
    132.95: _w(("Korang", 133.00, 133.50), ("boleh", 133.50, 133.68), ("grab,", 133.68, 133.90),
               ("tengok", 133.90, 134.10), ("dekat", 134.10, 134.32), ("beg", 134.32, 134.44),
               ("kuning.", 134.44, 134.74)),
    140.62: _w(("Cepat", 140.70, 141.34), ("sampai,", 141.34, 141.70), ("ready", 141.70, 142.10),
               ("stock.", 142.10, 142.40)),
}
DROP = [(130.60, 130.76), (41.64, 41.91)]     # the filler "Okay," before "two in one" / "jom kita unboxing"
KEYWORDS = {"PINK-PINK", "PINK", "TWO", "IN", "ONE", "DUA", "SATU", "UNBOXING", "COMELNYA", "TADAA!", "SELIMUT",
            "TRAVEL", "BELAKANG", "BANTAL", "BESAR", "GEBU", "LEMBUT", "LAWA", "BERCORAK", "LOVER", "BEG",
            "KUNING", "READY", "STOCK", "DALAM", "TADAA"}

# ---------------------------------------------------------------- her head (face avoidance)
# Head + hood box sampled every second from gridded proxy frames (fractions of the source frame, x0, y0, x1, y1).
# Seconds where the blanket hides her completely have no entry. edit.py turns these into px boxes (zoom applied)
# for each graphic's time window; the composition keeps every graphic HEAD_MARGIN px clear of all of them.
HEADS = [
    (41, (0.30, 0.12, 0.82, 0.42)), (42, (0.30, 0.12, 0.82, 0.42)), (43, (0.33, 0.12, 0.85, 0.42)),
    (44, (0.33, 0.13, 0.85, 0.42)), (45, (0.33, 0.12, 0.85, 0.42)), (46, (0.36, 0.12, 0.88, 0.43)),
    (47, (0.33, 0.13, 0.85, 0.45)), (48, (0.33, 0.12, 0.85, 0.45)), (49, (0.25, 0.13, 0.85, 0.45)),
    (50, (0.30, 0.13, 0.82, 0.45)), (51, (0.30, 0.13, 0.80, 0.45)), (52, (0.33, 0.13, 0.85, 0.45)),
    (53, (0.25, 0.13, 0.83, 0.45)), (54, (0.30, 0.13, 0.85, 0.42)), (55, (0.33, 0.15, 0.85, 0.42)),
    (56, (0.33, 0.17, 0.88, 0.42)), (57, (0.33, 0.17, 0.88, 0.40)), (58, (0.25, 0.17, 0.85, 0.40)),
    (59, (0.30, 0.17, 0.82, 0.40)), (60, (0.33, 0.17, 0.88, 0.40)), (61, (0.33, 0.13, 0.88, 0.38)),
    (62, (0.25, 0.13, 0.80, 0.38)), (63, (0.30, 0.12, 0.80, 0.36)), (64, (0.30, 0.12, 0.85, 0.36)),
    (71, (0.35, 0.13, 0.85, 0.42)), (72, (0.30, 0.13, 0.80, 0.40)), (73, (0.30, 0.13, 0.80, 0.40)),
    (74, (0.30, 0.12, 0.85, 0.32)),
    (83, (0.40, 0.08, 0.88, 0.33)), (84, (0.45, 0.08, 0.92, 0.33)), (85, (0.50, 0.08, 1.00, 0.33)),
    (86, (0.50, 0.12, 1.00, 0.38)), (87, (0.45, 0.15, 0.95, 0.40)), (88, (0.40, 0.16, 0.95, 0.42)),
    (89, (0.40, 0.15, 0.95, 0.40)), (90, (0.40, 0.15, 0.98, 0.40)), (91, (0.50, 0.15, 1.00, 0.42)),
    (92, (0.50, 0.15, 1.00, 0.42)), (93, (0.48, 0.13, 1.00, 0.40)), (94, (0.45, 0.13, 0.95, 0.40)),
    (95, (0.40, 0.13, 0.85, 0.40)), (96, (0.45, 0.13, 0.95, 0.40)), (97, (0.45, 0.15, 0.98, 0.40)),
    (98, (0.45, 0.17, 0.98, 0.40)), (99, (0.40, 0.15, 0.90, 0.36)), (100, (0.40, 0.15, 0.90, 0.38)),
    (101, (0.40, 0.15, 0.90, 0.37)), (102, (0.35, 0.13, 0.90, 0.35)),
    (114, (0.40, 0.18, 0.62, 0.30)), (123, (0.38, 0.20, 0.56, 0.32)), (124, (0.42, 0.15, 0.66, 0.27)),
    (125, (0.40, 0.13, 0.66, 0.27)), (127, (0.50, 0.13, 0.85, 0.33)), (128, (0.42, 0.13, 0.88, 0.38)),
    (129, (0.28, 0.13, 0.72, 0.42)), (130, (0.28, 0.15, 0.66, 0.38)), (131, (0.38, 0.18, 0.72, 0.38)),
    (132, (0.38, 0.22, 0.66, 0.40)), (133, (0.42, 0.20, 0.72, 0.38)), (134, (0.45, 0.18, 0.80, 0.38)),
    (135, (0.45, 0.18, 0.82, 0.38)), (136, (0.40, 0.15, 0.78, 0.38)), (137, (0.35, 0.15, 0.75, 0.40)),
    (138, (0.36, 0.17, 0.75, 0.40)), (139, (0.38, 0.17, 0.75, 0.40)), (140, (0.45, 0.18, 0.80, 0.40)),
    (141, (0.48, 0.18, 0.82, 0.40)), (142, (0.48, 0.18, 0.82, 0.40)), (143, (0.48, 0.18, 0.82, 0.40)),
    (144, (0.48, 0.20, 0.82, 0.42)), (145, (0.50, 0.20, 0.85, 0.42)),
]
# The bear face on the pillow when it is held up front: graphics steer off these points when they can.
FACES = [
    (60, [(0.52, 0.45)]), (61, [(0.50, 0.45)]), (62, [(0.53, 0.40)]), (63, [(0.50, 0.40)]), (64, [(0.53, 0.42)]),
    (98, [(0.22, 0.38)]), (99, [(0.45, 0.43)]), (100, [(0.45, 0.43)]), (101, [(0.50, 0.45)]),
    (136, [(0.70, 0.45)]), (137, [(0.68, 0.45)]), (138, [(0.70, 0.45)]), (139, [(0.78, 0.45)]),
    (140, [(0.72, 0.42)]), (141, [(0.72, 0.42)]), (142, [(0.73, 0.43)]), (143, [(0.73, 0.43)]),
]
HEAD_PAD = 0.5          # also count samples this many seconds outside a graphic's source range (1s grid)
LAB_Y, CAP_Y = 1020, 1405  # preferred centres (px): her head sits high, so labels go mid-frame; captions low


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

    def lab(s0, s1, text, emoji="", sound="squish", vol=0.55, src=True, kind="card", big=False):
        t0, t1 = (tl(s0), tl(s1)) if src else (s0, s1)
        labels.append(dict(t0=t0, t1=t1, html=text, emoji=emoji, kind=kind, big=big,
                           heads=heads_for(t0, t1), faces=faces_for(t0, t1)))
        if sound:
            sfx.append((sound, t0 - 0.03, vol))
        if big:
            sfx.append(("sprinkles", t0 + 0.08, 0.35))

    def pour(block, sound="whoosh", vol=0.4):
        t = BT[block]["t0"]
        wipes.append(dict(t=t))
        sfx.append((sound, t - 0.32, vol))
        sfx.append(("sprinkles", t - 0.05, 0.3))

    def tag(block, text):
        b = BT[block]
        tags.append(dict(t0=b["t0"] + 0.05, t1=b["t0"] + b["dur"] - 0.05, text=text))
        sfx.append(("click", b["t0"] + 0.05, 0.35))

    # hook: pink lovers -> two in one
    lab(62.20, 63.82, "SUKA <b>PINK?</b>", "🍓", sound="pop", vol=0.5)
    lab(130.80, 131.62, "<b>2 IN 1!</b>", "🎀", big=True, sound="squish", vol=0.6)
    lab(131.66, 132.70, "BANTAL + <b>SELIMUT</b>", "🧁", big=True, sound=None)
    # fast unboxing
    lab(41.66, 42.86, "JOM <b>UNBOXING!</b>", "🎁", sound="pop")
    tag("buka1", "&gt;&gt; x4")
    lab(50.40, 51.84, "<b>COMELNYA!</b>", "🥹", sound="sparkle", vol=0.4)
    tag("buka2", "&gt;&gt; x4")
    lab(58.92, 60.08, "<b>TADAA!</b>", "✨", big=True, sound="ding", vol=0.35)
    pour("dalam")
    lab(71.60, 73.26, "ADA <b>SELIMUT</b> DALAM", "🤫")
    lab(83.10, 84.52, "BOLEH BAWA <b>TRAVEL</b>", "🧳", sound="pop")
    lab(84.80, 86.60, "SELIMUT DI <b>BELAKANG</b>", "👀")
    lab(88.64, 89.68, "BUKA <b>ZIP</b>", "🔓", sound="zip", vol=0.5)
    lab(91.20, 92.22, "TARIK <b>SELIMUT</b>", "🫴", sound="pop")
    tag("tarik", "&gt;&gt; x2.5")
    lab(96.86, 98.84, "BANTAL PUN <b>BESAR</b>", "🤗")
    lab(99.74, 100.92, "GEBU & <b>LEMBUT</b>", "☁️", sound="puff", vol=0.5)
    lab(101.52, 102.72, "INI <b>SELIMUT</b> DIA", "🛏️", sound="pop")
    pour("lawa", sound="swish", vol=0.4)
    lab(108.90, 110.38, "LAWA <b>SELIMUT!</b>", "😍", big=True, sound="sparkle", vol=0.4)
    lab(118.50, 120.54, "<b>BERCORAK</b> COMEL", "🍓")
    lab(127.58, 130.04, "SELIMUT + <b>BANTAL</b>", "🎀")
    lab(136.80, 139.00, "<b>PINK LOVER</b>, AMBIL!", "💗", big=True, sound="sparkle", vol=0.4)
    lab(133.00, 134.74, "TEKAN <b>BEG KUNING</b>", "🛒", sound="ding", vol=0.35)
    lab(140.70, 142.40, "<b>READY</b> STOCK", "📦", sound="pop")
    e0 = BT["end"]["t0"] - 0.05
    end = dict(t0=e0, t1=TOTAL, title="BANTAL <b>SELIMUT</b> 🍓",
               sizes="🎀 2 IN 1 • GEBU • PINK", cta="🛒 TEKAN BEG KUNING",
               heads=heads_for(e0, TOTAL), faces=faces_for(e0, TOTAL), py=1150)
    sfx.append(("squish", e0 + 0.05, 0.55))
    sfx.append(("sprinkles", e0 + 0.2, 0.35))
    sfx.append(("ding", e0 + 0.6, 0.3))
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
