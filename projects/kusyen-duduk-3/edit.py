#!/usr/bin/env python3
"""Edit for kusyen duduk (red + beige tufted seat cushions), video 3 of 5 (IMG_3068), "Senarai semak / notepad"
look. Hook: her own opening call-out ("Korang yang duduk lama-lama sampai keras, habis belakang ni sakit tu, cuba
ada bantal ni satu."), kept first. The graphics layer is a HyperFrames (HTML + GSAP) composition: lined notepad
paper, checkbox ticks drawing in, a checklist of places that builds up as she names them, coloured sticky notes,
a paperclip, a yellow highlighter swipe under the spoken caption word, blue ink + the cushion red as accent.
User rule for this series: keep the CENTRE of the frame (x 160-920, y 480-1340) free of text and animation;
few, compact labels only in the top band / the lower band above the captions; no full-screen wipes.

Pipeline (all times in BLOCKS are source times of the original clip, same timeline as the proxy):
  1. base.mp4      - cut/zoomed video + cleaned voice (v2 chain, -11.5 LUFS) + soft music bed + SFX   (ffmpeg)
  2. comp/data.js  - captions, labels, pen-stroke accents, end card + her head boxes for each of them (this script)
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
# One 43.0s handheld shot on a dirt road: she holds a red and a beige tufted seat cushion and talks the whole
# time (no price talk in this clip). Her face is covered by the niqab, so J-cuts never show a lip mismatch.
# Her opening line is already the strongest hook (a problem call-out), so it stays first. Dropped: the hedged
# "mungkin boleh redakan sikit kan" (no health claims in this series), the unclear "keras-keras / tak nak
# kaler-kaler..." and the repeat "korang boleh try tengok bantal ni", "Gitu.", "Haa,", "nah" and pauses. "Korang" is
# spoken as "Kau-orang" with a gap (1.40 / 1.75), so the hook starts at 1.32.
# v: list of (src_in, src_out, speed, zoom); a: 'same' (follow v at 1x), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK: "Korang yang duduk lama-lama sampai keras, habis belakang ni sakit tu. | Cuba ada bantal ni satu."
    dict(name="hook", a="same", v=[(1.32, 5.80, 1, 1.0), (5.80, 7.98, 1, 1.06)]),
    # "Yang saiz dia 40cm x 40cm ni memang elok, | ngam untuk kerusi ofis, kerusi meja makan, dalam kereta."
    dict(name="saiz", a="same", v=[(18.32, 21.28, 1, 1.0), (21.28, 24.42, 1, 1.05)]),
    # "Sofa semua boleh. Belakang, depan, belakang ni macam ni." - starts on the red cushion filling the frame, then
    # the side-on shot of both cushions (thickness, from 13.9s) under "depan, belakang ni macam ni"
    dict(name="sofa", a=[(25.02, 28.22)], v=[(25.02, 26.30, 1, 1.0), (13.90, 15.82, 1, 1.0)]),
    # "Warna dia pun cantik-cantik. | Siapa minat warna merah terang, elok macam ni pun ada. |
    #  Minat kaler-kaler lembut-lembut, barang-barang estetik pun ada."
    dict(name="warna", a="same", v=[(29.40, 31.16, 1, 1.0), (31.16, 33.62, 1, 1.05), (33.62, 36.62, 1, 1.0)]),
    # "Bukan senang nak cari kaler-kaler gini tau."
    dict(name="susah", a="same", v=[(38.06, 40.00, 1, 1.04)]),
    # CTA: "Tengok dekat bawah sekarang."
    dict(name="cta", a="same", v=[(40.42, 42.42, 1, 1.0)]),
    # notepad end card over the opening wide shot (both cushions, head low), slowed a little, no voice
    dict(name="end", a=None, v=[(0.05, 1.65, 0.7, 1.0)]),
]

FIX = {"bantai": "bantal", "tahu": "tau", "kala": "kaler", "gala": "kaler", "kuni": "gini", "x": "×", "size": "saiz",
       "reto": "kereta", "reta": "kereta", "engam": "ngam"}


def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


# hand-checked words (per-chunk re-transcription + the loudness envelope)
OVERRIDE = {
    1.32: _w(("Korang", 1.40, 2.16), ("yang", 2.16, 2.28), ("duduk", 2.28, 2.56), ("lama-lama", 2.56, 3.12),
             ("sampai", 3.12, 3.48), ("keras,", 3.48, 3.88), ("habis", 3.88, 4.16), ("belakang", 4.16, 4.80),
             ("ni", 4.80, 5.02), ("sakit", 5.02, 5.44), ("tu.", 5.44, 5.72)),
    5.80: _w(("Cuba", 6.08, 6.40), ("ada", 6.45, 6.82), ("bantal", 6.82, 7.26), ("ni", 7.26, 7.44), ("satu.", 7.44, 7.96)),
    18.32: _w(("Yang", 18.36, 18.80), ("saiz", 18.80, 19.02), ("dia", 19.02, 19.24), ("40cm × 40cm", 19.24, 20.50),
              ("ni", 20.50, 20.66), ("memang", 20.66, 20.90),
              ("elok,", 20.90, 21.26)),
    21.28: _w(("ngam", 21.30, 21.58), ("untuk", 21.58, 21.84), ("kerusi", 21.84, 22.10), ("ofis,", 22.10, 22.72),
              ("kerusi", 22.80, 23.02), ("meja", 23.02, 23.22), ("makan,", 23.22, 23.60), ("dalam", 23.70, 23.98),
              ("kereta.", 23.98, 24.38)),
    25.02: _w(("Sofa", 25.05, 25.68), ("semua", 25.68, 26.38), ("boleh.", 26.38, 26.66), ("Belakang,", 26.68, 27.12),
              ("depan,", 27.24, 27.40), ("belakang", 27.40, 27.76), ("ni", 27.76, 27.88), ("macam", 27.88, 28.08),
              ("ni.", 28.08, 28.20)),
    29.40: _w(("Warna", 29.42, 29.68), ("dia", 29.68, 29.76), ("pun", 29.76, 29.92), ("cantik-cantik.", 29.92, 31.06)),
    31.16: _w(("Siapa", 31.22, 31.40), ("minat", 31.40, 31.54), ("warna", 31.54, 31.82), ("merah", 31.82, 32.20),
              ("terang,", 32.24, 32.58), ("elok", 32.78, 32.96), ("macam", 32.96, 33.16), ("ni", 33.16, 33.30),
              ("pun", 33.30, 33.46), ("ada.", 33.46, 33.60)),
    33.62: _w(("Minat", 33.66, 34.02), ("kaler-kaler", 34.02, 34.78), ("lembut-lembut,", 34.78, 35.26),
              ("barang-barang", 35.26, 35.68), ("estetik", 35.68, 36.24), ("pun", 36.24, 36.40), ("ada.", 36.40, 36.56)),
    38.06: _w(("Bukan", 38.08, 38.24), ("senang", 38.24, 38.60), ("nak", 38.60, 38.76), ("cari", 38.76, 38.98),
              ("kaler-kaler", 38.98, 39.44), ("gini", 39.44, 39.80), ("tau.", 39.80, 39.98)),
    40.42: _w(("Tengok", 40.45, 40.82), ("dekat", 40.82, 41.22), ("bawah", 41.22, 41.70), ("sekarang.", 41.74, 42.38)),
}
DROP = []
BREAK_BEFORE = {3.12, 4.16, 20.66, 22.80, 23.70, 26.68, 27.40, 32.78, 35.26, 38.98}   # forced caption chunk starts (source times)
KEYWORDS = {"40CM × 40CM", "DUDUK", "LAMA-LAMA", "BELAKANG", "BANTAL", "40CM", "KERUSI", "OFIS", "MEJA", "MAKAN", "KERETA",
            "SOFA", "WARNA", "MERAH", "TERANG", "LEMBUT-LEMBUT", "ESTETIK", "BAWAH", "CANTIK-CANTIK"}

# ---------------------------------------------------------------- her head (face avoidance)
# Head + hood box (incl. the niqab) from gridded proxy frames every 1s (fractions of the source frame, x0, y0, x1,
# y1). edit.py turns these into px boxes (zoom applied) for each graphic's time window; the composition keeps
# every graphic HEAD_MARGIN px clear of all of them. Checked by drawing them on the frames (work dir headcheck.jpg).
# 24-26s: the red cushion fills the frame and her head is cut off at the right edge.
HEADS = [
    (0, (0.35, 0.25, 0.64, 0.55)), (1, (0.35, 0.24, 0.64, 0.54)), (2, (0.38, 0.23, 0.66, 0.53)),
    (3, (0.36, 0.25, 0.62, 0.54)), (4, (0.46, 0.22, 0.76, 0.55)), (5, (0.48, 0.20, 0.78, 0.55)),
    (6, (0.41, 0.17, 0.75, 0.55)), (7, (0.44, 0.18, 0.79, 0.52)), (8, (0.44, 0.23, 0.79, 0.53)),
    (9, (0.38, 0.25, 0.69, 0.56)), (10, (0.49, 0.11, 0.84, 0.50)), (11, (0.53, 0.00, 0.99, 0.44)),
    (12, (0.43, 0.00, 0.82, 0.50)), (13, (0.43, 0.00, 0.82, 0.47)), (14, (0.45, 0.12, 0.80, 0.52)),
    (15, (0.48, 0.11, 0.84, 0.54)), (16, (0.46, 0.17, 0.82, 0.56)), (17, (0.43, 0.09, 0.84, 0.52)),
    (18, (0.60, 0.09, 0.99, 0.50)), (19, (0.58, 0.12, 0.97, 0.50)), (20, (0.56, 0.14, 0.94, 0.50)),
    (21, (0.53, 0.11, 0.94, 0.50)), (22, (0.49, 0.06, 0.90, 0.32)), (23, (0.73, 0.01, 1.00, 0.32)),
    (24, (0.80, 0.00, 1.00, 0.26)), (25, (0.84, 0.00, 1.00, 0.20)), (26, (0.84, 0.00, 1.00, 0.12)),
    (27, (0.46, 0.00, 0.84, 0.27)), (28, (0.38, 0.09, 0.77, 0.39)), (29, (0.43, 0.09, 0.80, 0.39)),
    (30, (0.43, 0.10, 0.84, 0.42)), (31, (0.53, 0.09, 0.94, 0.42)), (32, (0.68, 0.09, 1.00, 0.47)),
    (33, (0.68, 0.07, 1.00, 0.47)), (34, (0.43, 0.11, 0.84, 0.42)), (35, (0.38, 0.16, 0.76, 0.45)),
    (36, (0.38, 0.14, 0.77, 0.44)), (37, (0.40, 0.13, 0.84, 0.47)), (38, (0.26, 0.16, 0.68, 0.47)),
    (39, (0.18, 0.16, 0.62, 0.47)), (40, (0.16, 0.17, 0.60, 0.47)), (41, (0.26, 0.19, 0.67, 0.50)),
    (42, (0.38, 0.19, 0.82, 0.52)),
]
FACES = []              # the cushions have no face
HEAD_PAD = 0.55         # samples are 1s apart: look a little further either side
# preferred centres (px): notes in the top band, checklist lines just above the captions, captions low
TOP_Y, LOW_Y, CAP_Y = 270, 1366, 1440
# centre keep-out (user rule: "kurangkan text dan animation bahagian tengah video")
KEEP_OUT = (160, 480, 920, 1340)
MUSIC_VOL, MUSIC_DUCK = 0.35, 0.06   # music.wav gain alone / under her voice (she talks almost all the time)


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
                    out.append(dict(w=txt, s=s, e=e, clip=id(c), src=w["s"]))
    out.sort(key=lambda w: w["s"])
    return out


def caption_chunks(words):
    chunks, cur = [], []
    for w in words:
        tail = w["w"].lower().strip(",.?!") in ("ni", "kan", "dia", "lah") and w["e"] - w["s"] < 0.6   # joins
        chars = sum(len(x["w"]) for x in cur) + len(w["w"])
        if cur and ((len(cur) >= 5 or (chars > 30 and not tail)) or w.get("src") in BREAK_BEFORE
                    or w["s"] - cur[-1]["e"] > 0.35
                    or w["clip"] != cur[-1]["clip"] or cur[-1]["w"][-1] in ".?!"):
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
        end = min(end, BT["end"]["t0"])        # never under the end card
        out.append(dict(t0=ch[0]["s"], t1=end, y=CAP_Y, heads=heads_for(ch[0]["s"], end), faces=faces_for(ch[0]["s"], end),
                        words=[dict(w=x["w"].strip(",."), s=x["s"], e=x["e"],
                                    key=x["w"].upper().strip(",.?!") in KEYWORDS) for x in ch]))
    return out


# ---------------------------------------------------------------- graphics (data for comp/index.html)
def graphics():
    """Few, compact labels (user rule): a yellow sticky note for the hook, one checklist line for the size, a small
    notepad checklist of places that ticks itself as she names them, two colour sticky notes, a CTA line.
    Nothing is drawn in the centre KEEP_OUT box; section turns are edge-only pen strokes + a light flash."""
    labels, turns, sfx = [], [], []

    def lab(t0, t1, style, sound="stick", vol=0.34, block=None, **kw):
        """style 'note': sticky note (Caveat), prefers the top band.
        style 'check': notepad checklist card; kw items=[dict(text, t)] ticks in at t; prefers the top band, left.
        style 'line': one checklist line with a tick; prefers the lower band above the captions.
        style 'sticky': small coloured sticky note (kw tone='red'|'beige'); prefers the top band, left."""
        if block:
            t0, t1 = BT[block]["t0"] + t0, BT[block]["t0"] + t1
        py = LOW_Y if style == "line" else TOP_Y
        labels.append(dict(t0=t0, t1=t1, style=style, py=py, heads=heads_for(t0, t1), faces=faces_for(t0, t1), **kw))
        if sound:
            sfx.append((sound, t0 - 0.03, vol))

    def turn(block, sound="pen", vol=0.30):
        t = BT[block]["t0"]
        turns.append(dict(t=t))
        sfx.append((sound, t - 0.12, vol))

    # hook: "Korang yang duduk lama-lama sampai keras, habis belakang ni sakit tu."
    lab(0.10, tl(5.44), "note", html="Duduk <u>lama-lama</u> sampai keras?", emoji="😩", sound="stick", vol=0.3)
    # "Yang saiz dia 40cm x 40cm ni memang elok,"
    lab(tl(19.24) - 0.05, tl(21.26) + 0.05, "line", html="40 × 40 cm", tick=tl(20.50), sound="tick", vol=0.36)
    # "ngam untuk kerusi ofis, kerusi meja makan, dalam kereta. | Sofa semua boleh."
    items = [dict(text="Kerusi ofis", t=tl(22.10)), dict(text="Meja makan", t=tl(23.22)),
             dict(text="Dalam kereta", t=tl(23.98)), dict(text="Sofa", t=tl(25.05))]
    lab(tl(21.58) - 0.05, tl(26.66) + 0.35, "check", head="Ngam untuk:", items=items, sound="pen", vol=0.24)
    for it in items:
        sfx.append(("tick", it["t"] - 0.02, 0.34))
    turn("warna")
    # "Siapa minat warna merah terang, ..." / "Minat kaler-kaler lembut-lembut, barang-barang estetik pun ada."
    lab(tl(31.82) - 0.05, tl(33.60) + 0.2, "sticky", tone="red", html="Merah terang", emoji="❤️", sound="stick")
    lab(tl(34.78) - 0.05, min(tl(36.56) + 0.3, BT["warna"]["t0"] + BT["warna"]["dur"] - 0.04), "sticky", tone="beige",
        html="Lembut &amp; estetik", emoji="🤎", sound="stick")     # ends with its shot: her head moves left next
    # CTA: "Tengok dekat bawah sekarang."
    lab(tl(40.45) - 0.08, BT["cta"]["t0"] + BT["cta"]["dur"] - 0.04, "line", html="Tengok beg kuning", emoji="👇",
        tick=tl(40.82), sound="tick", vol=0.3)
    e0 = BT["end"]["t0"]
    end = dict(t0=e0, t1=TOTAL, title="Kusyen duduk", rows=["40 × 40 cm", "Merah &amp; beige", "Ofis · rumah · kereta"],
               cta="Tekan beg kuning 🛒", heads=heads_for(e0, TOTAL), faces=faces_for(e0, TOTAL))
    sfx.append(("pen", e0 - 0.05, 0.26))
    for k in range(3):
        sfx.append(("tick", e0 + 0.55 + k * 0.22, 0.3))
    return labels, turns, end, sfx


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
    speech = [(c["t"], c["t"] + c["e"] - c["s"]) for c in ACLIPS if "silence" not in c]
    duck = "+".join(f"between(t,{a - 0.25:.2f},{b + 0.25:.2f})" for a, b in speech) or "0"
    inputs += ["-i", os.path.join(SFX, "music.wav")]
    fc.append(f"[2:a]atrim=0:{TOTAL:.3f},volume='if(gt({duck},0),{MUSIC_DUCK},{MUSIC_VOL})':eval=frame,"
              f"afade=t=out:st={TOTAL - 1.2:.3f}:d=1.2[mus]")
    mix.append("[mus]")
    for j, (name, t, vol) in enumerate(sfx):
        inputs += ["-i", os.path.join(SFX, name + ".wav")]
        ms = max(0, int(t * 1000))
        fc.append(f"[{j + 3}:a]volume={vol},adelay={ms}|{ms}[s{j}]")
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
    labels, turns, end, sfx = graphics()
    data = dict(total=TOTAL, fps=FPS, w=CW, h=CH,
                safe=dict(l=SAFE_L, r=CW - SAFE_R, t=SAFE_T, b=CH - SAFE_B), cap_y=CAP_Y, keep_out=KEEP_OUT,
                captions=caption_chunks(words), labels=labels, turns=turns, end=end,
                blocks=[dict(name=b["name"], t0=b["t0"], dur=b["dur"]) for b in BLOCKS])
    with open(os.path.join(OUT, "edl.json"), "w") as f:
        json.dump(dict(data, sfx=sfx, heads_tl=[(round(i * 0.25, 2), heads_for(i * 0.25, i * 0.25 + 0.01))
                                                for i in range(int(TOTAL / 0.25) + 1)],
                       faces_tl=[(round(i * 0.25, 2), faces_for(i * 0.25, i * 0.25 + 0.01))
                                 for i in range(int(TOTAL / 0.25) + 1)],
                       keep_out=KEEP_OUT,
                       vblocks=[{k: b[k] for k in ("name", "t0", "dur", "v", "a")} for b in BLOCKS]),
                  f, ensure_ascii=False, indent=1)
    print(f"timeline {TOTAL:.2f}s, {len(VCLIPS)} clips, {len(labels)} labels, {len(sfx)} sfx")
    if "--no-render" in sys.argv:
        sys.exit(0)
    if "--graphics-only" not in sys.argv:      # --graphics-only: reuse out/base.mp4, re-render the overlay layer
        render_base(sfx)
    write_comp(data)
    render_hyperframes()
