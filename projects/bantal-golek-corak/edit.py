#!/usr/bin/env python3
"""Edit for bantal peluk panjang / bantal golek bercorak (IMG_3178), "Crayon taman budak" look: crayon and marker
doodles, wobbly hand-drawn outlines, paper-scrap labels, primary-colour scribbles, bouncy easing. The graphics
layer is a HyperFrames (HTML + GSAP) composition, as in ../bantal-durian-2.

Pipeline (all times in BLOCKS are source times of the original clip, same timeline as the proxy):
  1. base.mp4      - cut/zoomed video + cleaned voice (v2 chain, -11.5 LUFS) + SFX       (ffmpeg)
  2. comp/data.js  - captions, labels, scribble wipes, end card + her head boxes for each of them (this script)
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
# One handheld clip outdoors on grass: she unboxes three printed bolsters (dinosaur on mint, a blue print, a
# pink rainbow print) from black plastic bags, then holds all three. The raw clip is 94s with a lot of price
# talk; the strongest line ("jangan beli satu, ambil tiga ... anak ada tiga orang") comes near the end, so it is
# moved to the front as the hook, then the unboxing plays as a flashback.
# v: list of (src_in, src_out, speed, zoom); a: 'same' (follow v at 1x), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK (moved from 73.8s): "Jangan beli satu. Ambil tiga terus macam ni. Anak ada tiga orang, ambil tiga."
    #  ("Ya Allah, murah." before it cut: no prices)
    dict(name="hook", a="same", v=[(73.78, 75.95, 1, 1.0), (75.95, 77.90, 1, 1.06)]),
    # "Boleh hadiahkan untuk anak. Mesti anak happy."
    dict(name="hadiah", a="same", v=[(78.16, 80.67, 1, 1.0)]),
    # flashback: "Wah, apakah ini?" (opening "unboxing lagi, bismillah" cut)
    dict(name="unbox", a="same", v=[(7.18, 8.56, 1, 1.0)]),
    # "Oh, tiga biji. Wah, tiga biji lah saya pesan."  ("Oh, secure" cut)
    dict(name="tiga", a="same", v=[(11.22, 14.48, 1, 1.0)]),
    # "Nampak kan bantal peluk panjang, kan?"  ("Cuba tukar bantal apa ni" cut)
    dict(name="nampak", a="same", v=[(16.03, 18.04, 1, 1.0)]),
    # wrestling the bags open (x4, no speech; the "wah"s are dropped)
    dict(name="buka", a=None, v=[(18.04, 30.30, 4, 1.0)]),
    # "Wah, comel. Kamu tengok ni. Tengok saya beli tiga colour."
    dict(name="comel", a="same", v=[(30.70, 35.78, 1, 1.0)]),
    # pulling the first one out (x2), then the drawn-out "Waaah" as the blue one comes up
    dict(name="tarik", a=None, v=[(35.78, 37.30, 2, 1.0)]),
    dict(name="wah", a="same", v=[(37.30, 39.00, 1, 1.0)]),
    # "Ha, ni bantal peluk."
    dict(name="peluk", a="same", v=[(40.00, 41.95, 1, 1.0)]),
    # "Tepuk-tepuk sikit."  ("Gini awak" and "Okay, gitu" cut)
    dict(name="tepuk", a="same", v=[(43.68, 44.95, 1, 1.05)]),
    # price talk 47-53.6 cut ("harga ni murah... dapat harga berapa")
    # "Wih, yang ni colour pink ni lah."
    dict(name="pink", a="same", v=[(55.18, 56.78, 1, 1.0)]),
    # "Minat lah tiga-tiga kan ni."
    dict(name="minat", a="same", v=[(60.30, 61.86, 1, 1.0)]),
    # "Comel. Bantal peluk besar macam ni. | Memang sesuai untuk anak-anak kita tu."
    dict(name="besar", a="same", v=[(62.56, 64.95, 1, 1.0), (64.95, 67.15, 1, 1.06)]),
    # price line "tapi harga dia tak masuk akal. Hampir." cut
    # CTA: "Tengok cepat dekat beg kuning."
    dict(name="cta", a="same", v=[(70.86, 72.96, 1, 1.0)]),
    # end card over her holding all three (voice muted: more price talk there)
    dict(name="end", a=None, v=[(84.70, 87.30, 1, 1.0)]),
]

FIX = {"pantai": "bantal", "Pantai": "Bantal", "sesal": "sesuai", "color": "colour", "Kamu": "Korang",
       "kali": "kan"}


def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


# hand-checked words (re-transcribed per chunk + envelope; Whisper drifts on "bantal" and the gift line)
OVERRIDE = {
    78.16: _w(("Boleh", 78.22, 78.60), ("hadiahkan", 78.62, 79.02), ("untuk", 79.14, 79.44), ("anak.", 79.48, 79.70),
              ("Mesti", 79.75, 79.98), ("anak", 79.98, 80.18), ("happy.", 80.25, 80.64)),
    7.18: _w(("Wah,", 7.20, 7.64), ("apakah", 7.66, 7.95), ("ini?", 7.96, 8.44)),
    30.70: _w(("Wah,", 30.75, 31.06), ("comel.", 31.15, 32.46), ("Korang", 32.74, 32.98), ("tengok", 32.98, 33.30),
              ("ni.", 33.30, 33.70), ("Tengok", 34.54, 34.76), ("saya", 34.76, 34.90), ("beli", 34.90, 35.10),
              ("tiga", 35.10, 35.38), ("colour.", 35.38, 35.70)),
    37.30: _w(("Waaah!", 37.34, 38.95)),
    40.00: _w(("Ha,", 40.06, 40.56), ("ni", 40.58, 40.78), ("bantal", 40.80, 41.02), ("peluk.", 41.14, 41.92)),
}
DROP = []
KEYWORDS = {"JANGAN", "SATU", "TIGA", "AMBIL", "ANAK", "HADIAHKAN", "HAPPY", "APAKAH", "BIJI", "PESAN", "BANTAL",
            "PELUK", "PANJANG", "COMEL", "COLOUR", "WAAAH!", "TEPUK-TEPUK", "PINK", "MINAT", "TIGA-TIGA", "BESAR",
            "SESUAI", "ANAK-ANAK", "BEG", "KUNING", "CEPAT"}

# ---------------------------------------------------------------- her head (face avoidance)
# Head + hood box (hood ears to chin) sampled every second from gridded proxy frames (fractions of the source
# frame, x0, y0, x1, y1). edit.py turns these into px boxes (zoom applied) for each graphic's time window; the
# composition keeps every graphic HEAD_MARGIN px clear of all of them.
HEADS = [
    (7, (0.18, 0.20, 0.74, 0.55)), (8, (0.14, 0.20, 0.72, 0.55)), (9, (0.14, 0.14, 0.79, 0.53)),
    (10, (0.25, 0.22, 0.83, 0.56)), (11, (0.14, 0.24, 0.76, 0.57)), (12, (0.14, 0.16, 0.76, 0.53)),
    (13, (0.14, 0.00, 0.76, 0.26)), (14, (0.17, 0.00, 0.58, 0.18)), (15, (0.28, 0.00, 0.76, 0.22)),
    (16, (0.30, 0.03, 0.94, 0.36)), (17, (0.35, 0.12, 0.94, 0.45)), (18, (0.35, 0.13, 0.94, 0.45)),
    (19, (0.30, 0.12, 0.90, 0.45)), (20, (0.25, 0.12, 0.88, 0.45)), (21, (0.25, 0.12, 0.88, 0.45)),
    (22, (0.25, 0.12, 0.88, 0.45)), (23, (0.25, 0.12, 0.88, 0.45)), (24, (0.25, 0.12, 0.88, 0.45)),
    (25, (0.25, 0.12, 0.88, 0.45)), (26, (0.25, 0.12, 0.88, 0.45)), (27, (0.25, 0.12, 0.88, 0.45)),
    (28, (0.25, 0.12, 0.88, 0.45)), (29, (0.20, 0.12, 0.85, 0.45)),
    (30, (0.19, 0.10, 0.85, 0.44)), (31, (0.21, 0.10, 0.83, 0.44)), (32, (0.23, 0.10, 0.88, 0.44)),
    (33, (0.23, 0.10, 0.88, 0.45)), (34, (0.17, 0.10, 0.81, 0.45)), (35, (0.17, 0.09, 0.76, 0.43)),
    (36, (0.17, 0.07, 0.76, 0.41)), (37, (0.12, 0.07, 0.76, 0.41)), (38, (0.21, 0.09, 0.81, 0.44)),
    (39, (0.21, 0.09, 0.81, 0.44)), (40, (0.35, 0.09, 0.97, 0.44)), (41, (0.44, 0.10, 1.00, 0.44)),
    (42, (0.26, 0.12, 0.90, 0.45)), (43, (0.21, 0.13, 0.90, 0.46)), (44, (0.21, 0.15, 0.90, 0.48)),
    (45, (0.26, 0.18, 0.95, 0.50)),
    (55, (0.40, 0.16, 0.90, 0.46)), (56, (0.28, 0.13, 0.76, 0.38)), (57, (0.35, 0.15, 0.78, 0.41)),
    (58, (0.37, 0.20, 0.76, 0.46)), (59, (0.37, 0.21, 0.78, 0.45)), (60, (0.35, 0.21, 0.76, 0.45)),
    (61, (0.35, 0.21, 0.76, 0.45)), (62, (0.37, 0.21, 0.81, 0.45)), (63, (0.26, 0.21, 0.67, 0.46)),
    (64, (0.28, 0.20, 0.71, 0.45)), (65, (0.30, 0.21, 0.76, 0.46)), (66, (0.37, 0.22, 0.81, 0.48)),
    (67, (0.40, 0.24, 0.81, 0.49)),
    (70, (0.33, 0.22, 0.71, 0.42)), (71, (0.33, 0.22, 0.71, 0.42)), (72, (0.39, 0.21, 0.75, 0.44)),
    (73, (0.41, 0.17, 0.77, 0.41)), (74, (0.31, 0.13, 0.70, 0.37)), (75, (0.28, 0.13, 0.65, 0.37)),
    (76, (0.42, 0.16, 0.78, 0.40)), (77, (0.41, 0.17, 0.77, 0.41)), (78, (0.35, 0.15, 0.76, 0.38)),
    (79, (0.46, 0.15, 0.76, 0.37)), (80, (0.46, 0.16, 0.80, 0.40)), (81, (0.43, 0.16, 0.72, 0.40)),
    (84, (0.41, 0.17, 0.73, 0.40)), (85, (0.41, 0.17, 0.73, 0.40)), (86, (0.44, 0.15, 0.81, 0.38)),
    (87, (0.37, 0.15, 0.69, 0.38)), (88, (0.39, 0.15, 0.71, 0.38)),
]
FACES = []              # the bolsters' prints have no big faces to steer around
HEAD_PAD = 0.5          # also count samples this many seconds outside a graphic's source range (1s grid)
LAB_Y, CAP_Y = 1000, 1405  # preferred centres (px): labels mid-frame over the bolsters (her head sits high), captions low


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
# ---------------------------------------------------------------- graphics (data for comp/index.html)
def graphics():
    labels, wipes, tags, sfx = [], [], [], []

    def lab(s0, s1, text, emoji="", sound="scribble", vol=0.45, src=True, kind="paper", big=False, unit=None,
            color=None):
        t0, t1 = (tl(s0), tl(s1)) if src else (s0, s1)
        labels.append(dict(t0=t0, t1=t1, html=text, emoji=emoji, kind=kind, big=big, unit=unit, color=color,
                           heads=heads_for(t0, t1), faces=faces_for(t0, t1)))
        if sound:
            sfx.append((sound, t0 - 0.03, vol))

    def scrib(block, sound="scribble", vol=0.5):
        t = BT[block]["t0"]
        wipes.append(dict(t=t))
        sfx.append((sound, t - 0.32, vol))
        sfx.append(("whoosh", t - 0.25, 0.25))

    def tag(block, text):
        b = BT[block]
        tags.append(dict(t0=b["t0"], t1=b["t0"] + b["dur"], text=text,
                         heads=heads_for(b["t0"], b["t0"] + b["dur"])))

    # hook: "jangan beli satu, ambil tiga ... anak ada tiga orang, ambil tiga"
    lab(73.84, 74.50, "JANGAN BELI <b>SATU!</b>", "✋", sound="boing", vol=0.5, color="red")
    lab(74.66, 76.06, "AMBIL <b>3</b> TERUS!", "🙌", big=True, color="yellow")
    lab(76.54, 77.88, "3", "👧👦👶", kind="num", unit="ANAK = 3 BANTAL", sound="pop", vol=0.5)
    lab(78.22, 79.70, "HADIAH UNTUK <b>ANAK</b>", "🎁", color="blue")
    lab(79.75, 80.64, "MESTI ANAK <b>HAPPY!</b>", "😆", sound="boing", vol=0.45, big=True, color="yellow")
    scrib("unbox")
    lab(7.20, 8.50, "APAKAH <b>INI?</b>", "🤔", color="green")
    lab(11.26, 11.94, "3", "📦", kind="num", unit="BIJI!", sound="pop", vol=0.5)
    lab(12.52, 14.44, "SAYA PESAN <b>TIGA</b>", "🛍️", color="red")
    lab(16.10, 18.02, "BANTAL PELUK <b>PANJANG</b>", "📏", big=True, color="blue")
    tag("buka", "▶▶ x4")
    lab(30.75, 32.46, "<b>COMEL!</b>", "😍", sound="boing", vol=0.45, color="yellow")
    lab(34.54, 35.72, "BELI <b>3 CORAK</b>", "🎨", color="green")
    lab(37.34, 38.98, "WAAAH!", "✨", sound="sparkle", vol=0.4, kind="burst")
    lab(40.06, 41.92, "BANTAL <b>PELUK!</b>", "🤗", color="blue")
    lab(43.88, 44.92, "GEBU, <b>TEPUK-TEPUK</b>", "👏", sound="puff", vol=0.55, color="red")
    scrib("pink", vol=0.4)
    lab(55.20, 56.70, "YANG <b>PINK</b> NI!", "💗", color="pink")
    lab(60.38, 61.84, "SUKA <b>KETIGA-TIGA</b>", "😍", color="yellow")
    lab(62.58, 64.92, "BESAR & <b>PANJANG</b>", "📏", sound="boing", vol=0.4, color="green")
    lab(65.26, 67.12, "SESUAI UNTUK <b>ANAK-ANAK</b>", "🧒", big=True, color="blue")
    lab(70.92, 72.94, "TEKAN <b>BEG KUNING</b>", "🛒", sound="ding", vol=0.35, color="yellow")
    e0 = BT["end"]["t0"] - 0.05
    end = dict(t0=e0, t1=TOTAL, title="BANTAL PELUK <b>PANJANG</b>",
               sizes="🦕 DINO • 💙 BIRU • 🌈 PINK", cta="🛒 TEKAN BEG KUNING",
               heads=heads_for(e0, TOTAL), faces=faces_for(e0, TOTAL), py=1050)
    sfx.append(("scribble", e0, 0.45))
    sfx.append(("boing", e0 + 0.3, 0.35))
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
