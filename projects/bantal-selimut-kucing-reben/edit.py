#!/usr/bin/env python3
"""Edit for the bantal selimut kucing reben (IMG_3182): a cream cat pillow with a blue bow that unzips into a long
leopard-print blanket, "Coquette reben & renda" look (satin bows, lace edges, pearls, soft pink/cream/powder blue).
The graphics layer is a HyperFrames (HTML + GSAP) composition with the same face-aware placement as
../bantal-selimut-beruang. Never name the character the product resembles anywhere (she says it once at 61.7s:
that line is cut).

Pipeline (all times in BLOCKS are source times of the original clip, same timeline as the proxy):
  1. base.mp4      - cut/zoomed video + cleaned voice (v2 chain, -11.5 LUFS) + SFX       (ffmpeg)
  2. comp/data.js  - captions, labels, ribbon sweeps, end card + her head boxes for each of them (this script)
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
# One 87s handheld clip on a lawn: opening the blue plastic (its print is another product's, so it is never shown),
# the pillow, the unzip, the leopard blanket spread out, then pillow + blanket together. Her mouth is behind a
# niqab, so J-cuts are free. The hook is her own "design leopard ... tengah trending" line over the blanket flap.
# v: list of (src_in, src_out, speed, zoom); a: 'same' (follow v at 1x), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK: "Design leopard ni kenapa ya? Sekarang ni tengah trending."  (blanket flapped open, pillow on shoulder)
    dict(name="hook", a="same", v=[(43.10, 45.75, 1, 1.0)]),
    # "Wih, estetik je ni."  (pillow + blanket held up together)
    dict(name="estetik", a="same", v=[(75.90, 77.40, 1, 1.0)]),
    # "Wah, lembut, | lembutnya!"  (pause cut; J-cut over the pillow just out of the bag, the bag kept out of shot)
    dict(name="lembut", a=[(7.55, 8.36), (8.85, 10.22)], v=[(8.30, 10.48, 1, 1.0)]),
    # "(Ha) ni senang bawa travel. Senang ni standby dalam kereta satu."
    dict(name="travel", a="same", v=[(17.55, 20.68, 1, 1.0)]),
    # "Ni ada selimut tau. | Bantal dia pun lembut, fluffy."
    dict(name="selimut", a="same", v=[(20.80, 22.20, 1, 1.0), (22.20, 23.66, 1, 1.06)]),
    # "Lepas tu kita buka zip bawah dia."
    dict(name="zip", a="same", v=[(23.78, 25.05, 1, 1.0)]),
    # unzipping and pulling the blanket out (x2.5, "Bismillah" muted)
    dict(name="tarik", a=None, v=[(25.05, 28.40, 2.5, 1.0)]),
    # "Tadaa!"
    dict(name="tada", a="same", v=[(28.60, 29.50, 1, 1.0)]),
    # "Ni riben dia. Riben dia pun leopard."  (she points at the bow: same leopard fabric as the blanket)
    dict(name="riben", a="same", v=[(35.40, 37.52, 1, 1.05)]),
    # "Macam lebih kurang 170cm macam tu lah."  (the blanket held at full length)
    dict(name="panjang", a="same", v=[(52.54, 54.80, 1, 1.0)]),
    # "(Haa) dah habis guna, masukkan balik | selimut dekat dalam bantal ni."
    dict(name="simpan", a="same", v=[(56.86, 58.80, 1, 1.0), (58.80, 60.30, 1, 1.06)]),
    # "Tu mata dia tertutup, macam tu bulu mata panjang."  (the line naming the character before it is cut)
    dict(name="mata", a="same", v=[(64.62, 66.80, 1, 1.0)]),
    # "Bantal dia pun gebu, | selimut pun gebu."
    dict(name="gebu", a="same", v=[(68.78, 70.50, 1, 1.0), (70.50, 71.70, 1, 1.0)]),
    # CTA: "(Eh,) korang tengok dekat beg kuning. Yang mana suka geng-geng estetik tu, ambil ni."
    dict(name="cta", a="same", v=[(77.74, 81.04, 1, 1.0)]),
    # "Ready stock, cepat sampai."  ("tengok harga dekat beg kuning" before it is cut: no prices)
    dict(name="ready", a="same", v=[(83.60, 85.54, 1, 1.0)]),
    # end card over the last shot ("Okay, tengok beg ku ni" muted)
    dict(name="end", a=None, v=[(85.54, 87.30, 1, 1.0)]),
]

FIX = {"bantai": "bantal", "Bantai": "Bantal", "Ciume": "Comel", "ciume": "comel", "kuni": "kuning",
       "riba": "riben", "stop": "stock", "bag": "beg"}


def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


# hand-checked words (per-chunk re-transcription + loudness envelope)
OVERRIDE = {
    43.10: _w(("Design", 43.12, 43.54), ("leopard", 43.54, 43.92), ("ni", 43.92, 44.08), ("kenapa", 44.08, 44.42),
              ("ya?", 44.42, 44.62), ("Sekarang", 44.76, 45.00), ("ni", 45.00, 45.12), ("tengah", 45.12, 45.34),
              ("trending!", 45.34, 45.70)),
    75.90: _w(("Wih,", 75.95, 76.36), ("estetik", 76.40, 77.06), ("je", 77.06, 77.16), ("ni.", 77.16, 77.38)),
    7.55: _w(("Wah,", 7.58, 7.88), ("lembut,", 7.90, 8.32)),
    8.85: _w(("lembutnya!", 8.96, 10.12)),
    17.55: _w(("Ha", 17.55, 17.88), ("ni", 17.94, 18.06), ("senang", 18.06, 18.42), ("bawa", 18.42, 18.68),
              ("travel.", 18.68, 19.10), ("Senang", 19.20, 19.44), ("ni", 19.44, 19.62), ("standby", 19.62, 19.94),
              ("dalam", 19.94, 20.08), ("kereta", 20.08, 20.40), ("satu.", 20.40, 20.64)),
    20.80: _w(("Dia", 20.92, 21.00), ("ada", 21.00, 21.16), ("selimut", 21.16, 21.48), ("tau.", 21.48, 21.68),
              ("Bantal", 21.74, 22.02), ("dia", 22.02, 22.16)),
    22.20: _w(("pun", 22.20, 22.46), ("lembut,", 22.46, 23.02), ("fluffy.", 23.32, 23.62)),
    23.78: _w(("Lepas", 23.82, 24.02), ("tu", 24.02, 24.08), ("kita", 24.08, 24.22), ("buka", 24.22, 24.44),
              ("zip", 24.44, 24.68), ("bawah", 24.68, 24.90), ("dia.", 24.90, 25.02)),
    28.60: _w(("Tadaa!", 28.68, 29.44)),
    35.40: _w(("Ni", 35.44, 35.64), ("riben", 35.64, 36.04), ("dia.", 36.04, 36.20), ("Riben", 36.24, 36.54),
              ("dia", 36.54, 36.64), ("pun", 36.64, 36.80), ("leopard.", 36.80, 37.48)),
    52.54: _w(("Macam", 52.56, 52.70), ("lebih", 52.70, 52.86), ("kurang", 52.86, 53.08), ("170cm", 53.08, 54.30),
              ("macam", 54.30, 54.52), ("tu", 54.52, 54.62), ("lah.", 54.62, 54.78)),
    56.86: _w(("Haa,", 56.88, 57.10), ("dah", 57.10, 57.20), ("habis", 57.20, 57.46), ("guna,", 57.46, 57.68),
              ("masukkan", 57.68, 58.20), ("balik", 58.20, 58.72)),
    58.80: _w(("selimut", 58.86, 59.24), ("dekat", 59.24, 59.52), ("dalam", 59.52, 59.72), ("bantal", 59.72, 60.02),
              ("ni.", 60.02, 60.24)),
    64.62: _w(("Tu", 64.66, 64.78), ("mata", 64.78, 65.02), ("dia", 65.02, 65.20), ("tertutup,", 65.20, 65.58),
              ("macam", 65.62, 65.76), ("tu", 65.76, 65.90), ("bulu", 65.90, 66.10), ("mata", 66.10, 66.30),
              ("panjang.", 66.30, 66.72)),
    68.78: _w(("Bantal", 68.84, 69.26), ("dia", 69.26, 69.36), ("pun", 69.36, 69.44), ("gebu,", 69.44, 70.46)),
    70.50: _w(("selimut", 70.72, 71.10), ("pun", 71.10, 71.24), ("gebu.", 71.24, 71.62)),
    77.74: _w(("Eh,", 77.78, 77.98), ("korang", 77.98, 78.18), ("tengok", 78.18, 78.36), ("dekat", 78.36, 78.54),
              ("beg", 78.54, 78.68), ("kuning.", 78.68, 78.88), ("Yang", 78.96, 79.04), ("mana", 79.04, 79.18),
              ("suka", 79.18, 79.40), ("geng-geng", 79.40, 79.74), ("estetik", 79.74, 80.42), ("tu,", 80.42, 80.52),
              ("ambil", 80.56, 80.82), ("ni.", 80.82, 81.00)),
    83.60: _w(("Ready", 83.70, 83.98), ("stock,", 83.98, 84.26), ("cepat", 84.32, 84.74), ("sampai.", 84.74, 85.40)),
}
DROP = [(17.50, 17.90), (56.80, 57.10), (77.70, 77.98), (52.54, 52.70)]   # filler "Ha" / "Haa," / "Eh," / unclear
#                                                                          "Macam" (audio kept)
KEYWORDS = {"DESIGN", "LEOPARD", "TRENDING!", "TRENDING", "ESTETIK", "LEMBUT", "LEMBUTNYA!", "TRAVEL", "KERETA",
            "STANDBY", "SELIMUT", "FLUFFY", "ZIP", "TADAA!", "RIBEN", "170CM", "PANJANG", "GEBU", "BULU", "BEG",
            "KUNING", "READY", "STOCK", "BANTAL", "TERTUTUP"}

# ---------------------------------------------------------------- her head (face avoidance)
# Head + hood (with its ears) box sampled every second from gridded proxy frames (fractions of the source frame,
# x0, y0, x1, y1). Seconds where the blanket hides her completely have no entry.
HEADS = [
    (7, (0.30, 0.08, 0.75, 0.46)), (8, (0.25, 0.08, 0.85, 0.48)), (9, (0.30, 0.10, 0.85, 0.46)),
    (10, (0.33, 0.10, 0.72, 0.40)), (11, (0.33, 0.12, 0.72, 0.40)),
    (17, (0.28, 0.04, 0.72, 0.32)), (18, (0.30, 0.04, 0.70, 0.32)), (19, (0.30, 0.04, 0.70, 0.30)),
    (20, (0.30, 0.04, 0.72, 0.30)), (21, (0.33, 0.08, 0.72, 0.32)), (22, (0.30, 0.08, 0.72, 0.30)),
    (23, (0.33, 0.06, 0.77, 0.30)), (24, (0.33, 0.06, 0.77, 0.40)), (25, (0.33, 0.06, 0.77, 0.40)),
    (26, (0.28, 0.06, 0.72, 0.40)), (27, (0.33, 0.06, 0.77, 0.40)), (28, (0.33, 0.06, 0.77, 0.38)),
    (29, (0.33, 0.06, 0.72, 0.38)), (30, (0.18, 0.06, 0.62, 0.40)),
    (35, (0.23, 0.03, 0.64, 0.31)), (36, (0.33, 0.03, 0.72, 0.31)), (37, (0.26, 0.03, 0.64, 0.31)),
    (38, (0.33, 0.03, 0.72, 0.31)),
    (43, (0.23, 0.03, 0.62, 0.31)), (44, (0.23, 0.03, 0.62, 0.31)), (45, (0.28, 0.03, 0.67, 0.33)),
    (46, (0.28, 0.00, 0.67, 0.29)),
    (52, (0.38, 0.06, 0.72, 0.31)), (53, (0.28, 0.08, 0.64, 0.33)), (54, (0.43, 0.06, 0.77, 0.31)),
    (55, (0.20, 0.03, 0.72, 0.31)),
    (56, (0.28, 0.03, 0.72, 0.31)), (57, (0.43, 0.03, 0.87, 0.33)), (58, (0.43, 0.03, 0.82, 0.33)),
    (59, (0.43, 0.03, 0.82, 0.31)), (60, (0.33, 0.03, 0.77, 0.31)), (61, (0.38, 0.03, 0.77, 0.31)),
    (64, (0.48, 0.00, 0.94, 0.33)), (65, (0.48, 0.00, 0.94, 0.33)), (66, (0.53, 0.00, 0.94, 0.31)),
    (67, (0.63, 0.00, 1.00, 0.43)), (68, (0.78, 0.00, 1.00, 0.31)), (69, (0.63, 0.00, 1.00, 0.41)),
    (70, (0.68, 0.00, 1.00, 0.46)), (71, (0.63, 0.00, 1.00, 0.31)),
    (75, (0.48, 0.02, 0.94, 0.41)), (76, (0.43, 0.08, 0.87, 0.41)), (77, (0.43, 0.06, 0.87, 0.41)),
    (78, (0.43, 0.08, 0.87, 0.39)), (79, (0.43, 0.06, 0.87, 0.39)), (80, (0.48, 0.06, 0.94, 0.36)),
    (81, (0.48, 0.06, 0.94, 0.36)), (82, (0.48, 0.06, 0.92, 0.36)), (83, (0.43, 0.06, 0.92, 0.36)),
    (84, (0.43, 0.06, 0.87, 0.36)), (85, (0.43, 0.06, 0.87, 0.36)), (86, (0.43, 0.06, 0.87, 0.36)),
    (87, (0.38, 0.08, 0.87, 0.41)),
]
# The cat face on the pillow when it is held up front: graphics steer off these points when they can.
FACES = [
    (9, [(0.35, 0.80)]), (10, [(0.45, 0.62)]),
    (17, [(0.45, 0.58)]), (18, [(0.42, 0.58)]), (19, [(0.42, 0.55)]), (20, [(0.40, 0.58)]), (21, [(0.42, 0.58)]),
    (22, [(0.40, 0.58)]), (23, [(0.30, 0.58)]),
    (35, [(0.20, 0.42)]), (36, [(0.22, 0.40)]), (37, [(0.20, 0.40)]),
    (64, [(0.28, 0.20)]), (65, [(0.30, 0.20)]), (66, [(0.28, 0.22)]),
    (75, [(0.25, 0.42)]), (76, [(0.22, 0.45)]), (77, [(0.22, 0.45)]), (78, [(0.22, 0.42)]), (79, [(0.22, 0.42)]),
    (80, [(0.20, 0.45)]), (81, [(0.20, 0.45)]),
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

    def lab(s0, s1, text, emoji="", sound="harp", vol=0.4, src=True, kind="card", big=False):
        t0, t1 = (tl(s0), tl(s1)) if src else (s0, s1)
        labels.append(dict(t0=t0, t1=t1, html=text, emoji=emoji, kind=kind, big=big,
                           heads=heads_for(t0, t1), faces=faces_for(t0, t1)))
        if sound:
            sfx.append((sound, t0 - 0.03, vol))
        if big:
            sfx.append(("pearl", t0 + 0.12, 0.35))

    def sweep(block, sound="satin", vol=0.55):
        t = BT[block]["t0"]
        wipes.append(dict(t=t))
        sfx.append((sound, t - 0.34, vol))

    def tag(block, text):
        b = BT[block]
        tags.append(dict(t0=b["t0"] + 0.05, t1=b["t0"] + b["dur"] - 0.05, text=text))
        sfx.append(("click", b["t0"] + 0.05, 0.3))

    # hook: the leopard design is trending
    lab(43.12, 44.62, "DESIGN <b>LEOPARD</b>", "🐆", sound="pop", vol=0.45)
    lab(44.76, 45.70, "TENGAH <b>TRENDING!</b>", "🎀", big=True)
    lab(75.95, 77.38, "<b>ESTETIK</b> JE NI", "💗", sound="pearl", vol=0.45)
    lab(7.58, 10.12, "<b>LEMBUTNYA!</b>", "☁️", sound="puff", vol=0.5)
    lab(18.06, 19.10, "SENANG BAWA <b>TRAVEL</b>", "🧳", sound="pop", vol=0.45)
    lab(19.20, 20.64, "STANDBY DALAM <b>KERETA</b>", "🚗")
    lab(20.92, 21.68, "ADA <b>SELIMUT</b> TAU", "🤫", sound="pop", vol=0.45)
    lab(21.74, 23.62, "LEMBUT & <b>FLUFFY</b>", "☁️", sound="puff", vol=0.5)
    lab(23.82, 25.02, "BUKA <b>ZIP</b> BAWAH", "🔓", sound="zip", vol=0.5)
    tag("tarik", "&gt;&gt; x2.5")
    sweep("tada")
    lab(28.68, 29.46, "<b>TADAA!</b>", "✨", big=True, sound="sparkle", vol=0.4)
    lab(35.44, 37.48, "RIBEN PUN <b>LEOPARD</b>", "🎀")
    lab(52.56, 54.78, "SELIMUT ±<b>170CM</b>", "📏", big=True, sound="pearl", vol=0.45)
    lab(57.10, 58.72, "DAH GUNA? <b>SIMPAN</b>", "🫶", sound="pop", vol=0.45)
    lab(58.86, 60.24, "MASUK <b>DALAM BANTAL</b>", "👜")
    lab(64.66, 66.72, "BULU MATA <b>PANJANG</b>", "😴")
    lab(68.84, 71.62, "BANTAL + SELIMUT <b>GEBU</b>", "💕", sound="puff", vol=0.5)
    sweep("cta")
    lab(77.98, 78.88, "TEKAN <b>BEG KUNING</b>", "🛒", sound="ding", vol=0.35)
    lab(78.96, 81.00, "GENG <b>ESTETIK</b>, AMBIL!", "💗", big=True)
    lab(83.80, 85.40, "<b>READY</b> STOCK", "📦", sound="pop", vol=0.45)
    e0 = BT["end"]["t0"] - 0.05
    end = dict(t0=e0, t1=TOTAL, title="BANTAL <b>SELIMUT</b>", kicker="kucing reben",
               sizes="2 IN 1 • LEOPARD • ±170CM", cta="🛒 TEKAN BEG KUNING",
               heads=heads_for(e0, TOTAL), faces=faces_for(e0, TOTAL), py=1150)
    sfx.append(("harp", e0 + 0.05, 0.45))
    sfx.append(("pearl", e0 + 0.35, 0.35))
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
