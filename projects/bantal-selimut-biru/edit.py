#!/usr/bin/env python3
"""Edit for the bantal selimut karakter biru (IMG_3183): a blue alien-character pillow that unzips into a
light-blue printed blanket, "Galaksi angkasa" (deep-space) look. The graphics layer is a HyperFrames (HTML + GSAP)
composition, as in ../bantal-durian-2 (same face-aware placement). Never name the character the product resembles anywhere.

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
# One 94s handheld clip on a lawn: she wears a blue alien-character hoodie and shows a matching blue
# alien-character pillow, first still in its plastic, then hugged, then unzipped at the back to pull out a
# light-blue printed blanket, the blanket spread out, and pillow + blanket together. ~10s of price talk is cut.
# The hook is her own matching-outfit line ("pakai dengan baju sama"), then "ada selimut, dua dalam satu".
# v: list of (src_in, src_out, speed, zoom); a: 'same' (follow v at 1x), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK: "Macam mana kalau biru macam ni, pakai dengan baju sama?"  (pillow + matching hoodie)
    dict(name="hook", a="same", v=[(24.50, 28.26, 1, 1.0)]),
    # "Ni ada selimut tau, dua dalam satu."
    dict(name="dua", a="same", v=[(28.42, 31.92, 1, 1.0)]),
    # "Tadaa! | Comel kan! Ya Allah, dia lebih besar, bantal dia ni."  (still in its plastic; pause cut)
    dict(name="tadah", a="same", v=[(0.33, 1.16, 1, 1.0), (2.08, 5.27, 1, 1.05)]),
    # "Bestnya, peluk. Korang letak kat bilik tidur pun sangat sesuai."  (J-cut over her hugging it, plastic off)
    dict(name="peluk", a=[(5.29, 9.12)], v=[(13.00, 16.83, 1, 1.0)]),
    # "Buka zip di belakang dia."
    dict(name="zip", a="same", v=[(32.45, 34.12, 1, 1.0)]),
    # turning it round and opening the zip (x3, the repeated "buka zip" line is dropped)
    dict(name="buka", a=None, v=[(34.12, 40.36, 3, 1.0)]),
    # "Keluarkan selimut dia."
    dict(name="keluar", a="same", v=[(40.62, 41.98, 1, 1.0)]),
    # "Cantik kan? Selimut dia colour biru, | biru muda, biru lembut gitu."  (pause after "biru" cut)
    dict(name="biru", a="same", v=[(42.66, 44.97, 1, 1.0), (45.55, 46.92, 1, 1.05)]),
    # "Okey, ni bantal dia tak kosong. Jadi masih lagi tebal gini, memang selesa lah."  (J-cut: hugging it)
    dict(name="tebal", a=[(46.94, 51.04)], v=[(17.10, 21.20, 1, 1.0)]),
    # "Okey, ni size selimut dia."  (J-cut over the blanket held up)
    dict(name="size", a=[(53.72, 54.84)], v=[(55.10, 56.22, 1, 1.0)]),
    # "Besar juga ni, ngam elok untuk seorang baring."  (blanket spread out, the money shot)
    dict(name="besar", a="same", v=[(82.62, 85.08, 1, 1.0)]),
    # "Material selimut pun lembut, gebu-gebas."
    dict(name="lembut", a="same", v=[(88.18, 90.08, 1, 1.0)]),
    # "Siapa yang belum ada lagi, selimut dengan bantal 2 in 1, | untuk travel boleh ataupun untuk letak dekat
    #  bilik tidur, boleh grab yang ni."
    dict(name="belum", a="same", v=[(63.62, 67.08, 1, 1.0), (67.10, 70.52, 1, 1.04)]),
    # "Kalau minat design macam ni, korang grab sekali dengan baju. Comel ni."
    dict(name="design", a="same", v=[(70.54, 74.40, 1, 1.0)]),
    # end card over her hugging the pillow inside the blanket (silent)
    dict(name="end", a=None, v=[(91.40, 94.10, 1, 1.0)]),
]

FIX = {"bantai": "bantal", "Bantai": "Bantal", "zit": "zip", "zik": "zip", "Silimu": "Selimut", "Comegan!": "Comel kan!",
       "Chomekan!": "Comel kan!", "paka": "pakai", "color": "colour", "Sapa": "Siapa", "Tadah!": "Tadaa!"}


def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


# hand-checked words (per-chunk re-transcription + loudness envelope)
OVERRIDE = {
    24.50: _w(("Macam", 24.55, 24.94), ("mana", 24.94, 25.18), ("kalau", 25.22, 25.44), ("biru", 25.44, 25.80),
              ("macam", 25.80, 25.98), ("ni,", 25.98, 26.46), ("pakai", 26.48, 26.94), ("dengan", 26.94, 27.18),
              ("baju", 27.18, 27.76), ("sama?", 27.76, 28.22)),
    28.42: _w(("Okey,", 28.55, 29.04), ("ni", 29.10, 29.38), ("ada", 29.74, 30.16), ("selimut", 30.16, 30.48),
              ("tau,", 30.48, 30.76),
              ("dua", 31.00, 31.12), ("dalam", 31.12, 31.42), ("satu.", 31.42, 31.86)),
    0.33: _w(("Tadaa!", 0.35, 1.12)),
    2.08: _w(("Comel", 2.12, 2.36), ("kan!", 2.36, 2.60), ("Ya", 2.80, 2.86), ("Allah,", 2.86, 3.42),
             ("dia", 3.56, 3.66), ("lebih", 3.66, 3.86), ("besar,", 3.86, 4.24), ("bantal", 4.48, 4.94),
             ("dia", 4.94, 5.08), ("ni.", 5.08, 5.26)),
    5.29: _w(("Bestnya,", 5.32, 5.98), ("peluk.", 6.04, 6.86), ("Korang", 7.00, 7.16), ("letak", 7.16, 7.44),
             ("kat", 7.44, 7.56), ("bilik", 7.56, 7.84), ("tidur", 7.84, 8.14), ("pun", 8.14, 8.32),
             ("sangat", 8.32, 8.64), ("sesuai.", 8.64, 9.08)),
    32.45: _w(("Buka", 32.50, 33.06), ("zip", 33.06, 33.26), ("di", 33.26, 33.46), ("belakang", 33.46, 33.86),
              ("dia.", 33.86, 34.08)),
    40.62: _w(("Keluarkan", 40.66, 41.10), ("selimut", 41.10, 41.50), ("dia.", 41.50, 41.90)),
    42.66: _w(("Cantik", 42.72, 43.08), ("kan?", 43.08, 43.40), ("Selimut", 43.44, 43.72), ("dia", 43.72, 43.80),
              ("colour", 43.80, 44.14), ("biru,", 44.14, 44.94)),
    45.55: _w(("biru", 45.58, 46.02), ("muda,", 46.02, 46.28), ("biru", 46.30, 46.50), ("lembut", 46.50, 46.66),
              ("gitu.", 46.66, 46.88)),
    46.94: _w(("Okey,", 46.96, 47.06), ("ni", 47.06, 47.18), ("bantal", 47.18, 47.52), ("dia", 47.52, 47.66),
              ("tak", 47.66, 47.84), ("kosong.", 47.84, 48.18), ("Bantal", 48.18, 48.34), ("dia", 48.34, 48.44), ("masih", 48.44, 48.88),
              ("lagi", 48.88, 49.26), ("tebal", 49.26, 49.70), ("gini,", 49.70, 50.14), ("memang", 50.22, 50.46),
              ("selesa", 50.46, 50.88), ("lah.", 50.88, 51.02)),
    53.72: _w(("Okey,", 53.74, 53.92), ("ni", 53.92, 54.12), ("size", 54.12, 54.40), ("selimut", 54.40, 54.70),
              ("dia.", 54.70, 54.82)),
    82.62: _w(("Besar", 82.66, 83.34), ("juga", 83.34, 83.48), ("ni,", 83.48, 83.64), ("ngam", 83.72, 83.88),
              ("elok", 83.88, 84.14), ("untuk", 84.14, 84.42), ("seorang", 84.42, 84.66), ("baring.", 84.66, 85.04)),
    88.18: _w(("Material", 88.24, 88.64), ("selimut", 88.64, 88.96), ("pun", 88.96, 89.10), ("lembut,", 89.10, 89.42),
              ("gebu", 89.48, 89.68), ("-gebas.", 89.68, 90.04)),
    63.62: _w(("Siapa", 63.64, 63.84), ("yang", 63.84, 63.94), ("belum", 63.94, 64.12), ("ada", 64.12, 64.36),
              ("lagi,", 64.36, 65.20), ("selimut", 65.30, 65.72), ("dengan", 65.72, 65.98), ("bantal", 65.98, 66.42),
              ("2", 66.42, 66.60), ("in", 66.60, 66.82), ("1,", 66.82, 67.06)),
    67.10: _w(("untuk", 67.12, 67.32), ("travel", 67.32, 67.70), ("boleh", 67.70, 67.90), ("ataupun", 67.90, 68.34),
              ("untuk", 68.34, 68.50), ("letak", 68.50, 68.66), ("dekat", 68.66, 68.86), ("bilik", 68.86, 69.12),
              ("tidur,", 69.12, 69.64), ("boleh", 69.76, 70.00), ("grab", 70.00, 70.18), ("yang", 70.18, 70.40),
              ("ni.", 70.40, 70.50)),
    70.54: _w(("Kalau", 70.56, 70.80), ("minat", 70.80, 71.16), ("design", 71.16, 71.44), ("macam", 71.44, 71.66),
              ("ni,", 71.66, 71.84), ("korang", 71.94, 72.14), ("grab", 72.14, 72.32), ("sekali", 72.32, 72.52),
              ("dengan", 72.52, 72.74), ("baju.", 72.74, 73.68), ("Comel", 73.78, 74.16), ("ni.", 74.16, 74.36)),
}
DROP = [(28.50, 29.06), (46.95, 47.07), (53.73, 53.93)]   # caption-only filler "Okey"
KEYWORDS = {"BESTNYA", "BIRU", "BAJU", "SAMA?", "SAMA", "SELIMUT", "DUA", "SATU", "TADAA!", "TADAA", "COMEL", "BESAR",
            "PELUK", "TIDUR", "SESUAI", "ZIP", "BELAKANG", "KELUARKAN", "CANTIK", "MUDA", "LEMBUT", "TEBAL",
            "SELESA", "SIZE", "BARING", "GEBU-GEBAS", "2", "IN", "1", "TRAVEL", "GRAB", "DESIGN", "BANTAL"}

# ---------------------------------------------------------------- her head (face avoidance)
# Head + hood box sampled every second from gridded proxy frames (fractions of the source frame, x0, y0, x1, y1).
# The hood is big (ears + teeth trim), so the box covers the whole hood around her face. Seconds where the
# pillow or the blanket hides her completely have no entry.
HEADS = [
    (0, (0.28, 0.08, 0.72, 0.33)), (1, (0.28, 0.04, 0.72, 0.32)), (2, (0.28, 0.03, 0.75, 0.35)),
    (3, (0.24, 0.02, 0.80, 0.41)), (4, (0.24, 0.02, 0.80, 0.41)), (5, (0.24, 0.02, 0.80, 0.41)),
    (6, (0.24, 0.02, 0.80, 0.41)),
    (12, (0.30, 0.13, 0.74, 0.40)), (13, (0.30, 0.15, 0.74, 0.39)), (14, (0.28, 0.17, 0.72, 0.39)),
    (15, (0.32, 0.19, 0.74, 0.38)), (16, (0.28, 0.16, 0.70, 0.41)), (17, (0.30, 0.13, 0.76, 0.39)),
    (18, (0.26, 0.15, 0.74, 0.38)), (19, (0.36, 0.13, 0.76, 0.38)), (20, (0.38, 0.12, 0.78, 0.38)),
    (21, (0.36, 0.13, 0.78, 0.38)), (22, (0.36, 0.13, 0.78, 0.38)),
    (24, (0.33, 0.06, 0.74, 0.31)), (25, (0.36, 0.06, 0.82, 0.31)), (26, (0.40, 0.01, 0.84, 0.34)),
    (27, (0.40, 0.00, 0.84, 0.34)), (28, (0.14, 0.00, 0.84, 0.38)), (29, (0.08, 0.00, 0.84, 0.33)),
    (30, (0.28, 0.00, 1.00, 0.46)), (31, (0.22, 0.00, 0.86, 0.31)), (32, (0.13, 0.00, 0.80, 0.27)),
    (33, (0.48, 0.06, 1.00, 0.37)), (34, (0.60, 0.11, 1.00, 0.49)), (35, (0.46, 0.10, 0.97, 0.46)),
    (36, (0.46, 0.08, 1.00, 0.41)), (37, (0.53, 0.10, 1.00, 0.43)), (38, (0.46, 0.10, 1.00, 0.41)),
    (39, (0.48, 0.08, 1.00, 0.41)), (40, (0.53, 0.08, 1.00, 0.41)), (41, (0.53, 0.10, 1.00, 0.43)),
    (42, (0.53, 0.13, 1.00, 0.49)), (43, (0.38, 0.13, 0.97, 0.49)), (44, (0.48, 0.13, 1.00, 0.49)),
    (45, (0.53, 0.13, 1.00, 0.49)), (46, (0.46, 0.13, 1.00, 0.46)), (47, (0.46, 0.10, 1.00, 0.49)),
    (53, (0.20, 0.10, 0.77, 0.41)), (54, (0.22, 0.10, 0.77, 0.41)), (55, (0.48, 0.05, 0.90, 0.37)),
    (56, (0.48, 0.05, 0.90, 0.37)),
    (64, (0.53, 0.08, 1.00, 0.37)), (65, (0.48, 0.08, 0.97, 0.36)), (66, (0.60, 0.13, 1.00, 0.37)),
    (67, (0.53, 0.06, 1.00, 0.36)), (68, (0.53, 0.08, 0.97, 0.36)), (69, (0.40, 0.06, 0.84, 0.34)),
    (70, (0.36, 0.10, 0.77, 0.34)), (71, (0.30, 0.10, 0.77, 0.36)), (72, (0.30, 0.06, 0.77, 0.31)),
    (73, (0.33, 0.08, 0.80, 0.31)), (74, (0.40, 0.06, 0.87, 0.31)), (75, (0.38, 0.00, 0.87, 0.26)),
    (89, (0.08, 0.10, 0.62, 0.41)), (90, (0.00, 0.08, 0.57, 0.46)), (91, (0.28, 0.12, 0.82, 0.41)),
    (92, (0.23, 0.18, 0.72, 0.41)), (93, (0.30, 0.18, 0.77, 0.43)), (94, (0.23, 0.18, 0.72, 0.41)),
]
# The alien-pillow face (big eyes) when it is held up front: graphics steer off these points when they can.
FACES = [
    (13, [(0.50, 0.62)]), (14, [(0.48, 0.60)]), (15, [(0.50, 0.60)]), (16, [(0.45, 0.62)]),
    (17, [(0.50, 0.60)]), (18, [(0.50, 0.58)]), (19, [(0.52, 0.58)]), (20, [(0.50, 0.57)]), (21, [(0.50, 0.57)]),
    (24, [(0.42, 0.38)]), (25, [(0.45, 0.38)]), (26, [(0.62, 0.45)]), (27, [(0.62, 0.45)]),
    (28, [(0.50, 0.55)]), (29, [(0.55, 0.52)]), (31, [(0.62, 0.45)]),
    (64, [(0.28, 0.45)]), (65, [(0.28, 0.45)]), (66, [(0.25, 0.45)]), (67, [(0.30, 0.45)]),
    (68, [(0.28, 0.45)]), (69, [(0.28, 0.45)]), (70, [(0.28, 0.45)]), (71, [(0.25, 0.45)]),
    (72, [(0.20, 0.36)]), (73, [(0.22, 0.36)]), (74, [(0.30, 0.40)]),
    (92, [(0.30, 0.50)]), (93, [(0.38, 0.52)]), (94, [(0.30, 0.50)]),
]
HEAD_PAD = 0.5          # also count samples this many seconds outside a graphic's source range (1s grid)
LAB_Y, CAP_Y = 1060, 1400  # preferred centres (px): her hood sits high, so labels go mid-frame; captions low


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

    def lab(s0, s1, text, emoji="", sound="warp", vol=0.45, src=True, kind="card", big=False):
        t0, t1 = (tl(s0), tl(s1)) if src else (s0, s1)
        labels.append(dict(t0=t0, t1=t1, html=text, emoji=emoji, kind=kind, big=big,
                           heads=heads_for(t0, t1), faces=faces_for(t0, t1)))
        if sound:
            sfx.append((sound, t0 - 0.03, vol))
        if big or kind == "planet":
            sfx.append(("twinkle", t0 + 0.08, 0.3))

    def warp(block, vol=0.4):
        t = BT[block]["t0"]
        wipes.append(dict(t=t))
        sfx.append(("whoosh", t - 0.32, vol))
        sfx.append(("twinkle", t - 0.02, 0.28))

    def tag(block, text):
        b = BT[block]
        tags.append(dict(t0=b["t0"] + 0.05, t1=b["t0"] + b["dur"] - 0.05, text=text))
        sfx.append(("click", b["t0"] + 0.05, 0.35))

    # hook: the matching blue outfit -> it has a blanket inside, 2 in 1
    lab(24.55, 25.98, "<b>BIRU</b> MACAM NI?", "💙", sound="warp", vol=0.5)
    lab(26.48, 28.22, "PAKAI <b>BAJU SAMA!</b>", "👕", big=True, sound="pop")
    lab(29.74, 30.76, "ADA <b>SELIMUT</b>", "🛏️", sound="warp")
    lab(31.00, 31.86, "<b>2 IN 1</b>", "🪐", kind="planet", sound="hum", vol=0.45)
    # it out of the plastic
    lab(0.35, 1.12, "<b>TADAA!</b>", "✨", big=True, sound="ding", vol=0.3)
    lab(2.12, 3.42, "<b>COMEL</b> KAN!", "🥹", sound="pop")
    lab(3.56, 5.40, "BANTAL <b>BESAR</b>", "🤗", sound="warp")
    lab(5.32, 6.86, "BESTNYA <b>PELUK!</b>", "🫂", sound="pop")
    lab(7.00, 9.08, "SESUAI <b>BILIK TIDUR</b>", "🌙", sound="warp")
    # unzip -> blanket
    lab(32.50, 34.08, "BUKA <b>ZIP</b> BELAKANG", "🔓", sound="zip", vol=0.5)
    tag("buka", "&gt;&gt; x3")
    lab(40.66, 41.90, "KELUARKAN <b>SELIMUT</b>", "🪄", sound="warp")
    warp("biru")
    lab(42.72, 43.40, "<b>CANTIK</b> KAN?", "😍", sound="pop")
    lab(43.44, 44.94, "SELIMUT <b>BIRU</b>", "💙", sound="warp")
    lab(45.58, 46.88, "BIRU MUDA • <b>LEMBUT</b>", "☁️", sound="puff", vol=0.45)
    lab(47.18, 48.18, "TAK <b>KOSONG</b>", "👌", sound="pop")
    lab(48.18, 50.14, "MASIH <b>TEBAL</b>", "💪", sound="warp")
    lab(50.22, 51.02, "<b>SELESA!</b>", "😌", big=True, sound="sparkle", vol=0.35)
    lab(53.92, 54.82, "SIZE <b>SELIMUT</b>", "📏", sound="pop")
    warp("besar")
    lab(82.66, 83.64, "<b>BESAR</b> JUGA!", "😮", sound="pop")
    lab(83.72, 85.04, "MUAT <b>SEORANG BARING</b>", "🛌", big=True, sound="warp")
    lab(88.24, 90.04, "LEMBUT & <b>GEBU-GEBAS</b>", "☁️", sound="puff", vol=0.45)
    lab(63.64, 65.20, "BELUM ADA <b>LAGI?</b>", "👀", sound="pop")
    lab(65.30, 67.06, "SELIMUT + <b>BANTAL</b>", "🌌", big=True, sound="hum", vol=0.45)
    lab(67.12, 69.64, "<b>TRAVEL</b> • BILIK TIDUR", "🚀", sound="warp")
    lab(69.76, 70.50, "<b>GRAB</b> YANG NI!", "🛒", sound="ding", vol=0.3)
    lab(70.56, 71.84, "SUKA <b>DESIGN</b> NI?", "💫", sound="warp")
    lab(71.94, 73.68, "GRAB SEKALI <b>DENGAN BAJU!</b>", "👕", big=True, sound="pop")
    lab(73.78, 74.36, "<b>COMEL!</b>", "🥰", sound="pop")
    e0 = BT["end"]["t0"] - 0.05
    end = dict(t0=e0, t1=TOTAL, title="BANTAL <b>SELIMUT</b> 🪐",
               sizes="💙 2 IN 1 • BIRU LEMBUT • GEBU", cta="🛒 TEKAN BEG KUNING",
               heads=heads_for(e0, TOTAL), faces=faces_for(e0, TOTAL), py=1150)
    sfx.append(("hum", e0 + 0.05, 0.4))
    sfx.append(("twinkle", e0 + 0.2, 0.35))
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
