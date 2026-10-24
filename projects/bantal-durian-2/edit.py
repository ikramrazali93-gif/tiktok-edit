#!/usr/bin/env python3
"""Edit for bantal peluk durian #2 (IMG_3061), "Kebun Durian" look. Second video of the durian series; the
graphics layer is a HyperFrames (HTML + GSAP) composition, as in ../bantal-durian.

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
# One handheld clip, outdoors in an orchard: she holds four durian-segment plush pillows, a few close-ups with
# her hand waving. She opens with the "tak sangka" hook line, so the order stays as shot.
# v: list of (src_in, src_out, speed, zoom); a: 'same' (follow v at 1x), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK: "Saya tak sangka bantal macam ni boleh buat orang happy, tersenyum."
    dict(name="hook", a="same", v=[(0.00, 2.58, 1, 1.0), (2.58, 5.45, 1, 1.05)]),
    # "Kalau kita bagi hadiah dekat kawan, dekat best friend,"  ("Kan," cut)
    dict(name="hadiah", a="same", v=[(5.96, 8.98, 1, 1.0)]),
    # "dekat anak, dekat mak kita yang suka durian ni,"
    dict(name="mak", a="same", v=[(9.24, 12.24, 1, 1.0)]),
    # "Mesti mak tersenyum."  ("haa" cut)
    dict(name="senyum", a="same", v=[(13.05, 14.08, 1, 1.06)]),
    # "Eh, comelnya bantal durian yang gebu lembut ni."
    dict(name="comel", a="same", v=[(14.12, 17.58, 1, 1.0)]),
    # "Boleh peluk atau tidur."
    dict(name="tidur", a="same", v=[(17.58, 19.46, 1, 1.0)]),
    # "Atau nak buat peluk dalam kereta, | dalam bas."  (drawn-out "kan?" between them cut)
    dict(name="kereta", a="same", v=[(19.80, 22.06, 1, 1.0), (22.84, 23.94, 1, 1.05)]),
    # "Ada macam-macam saiz."
    dict(name="saiz", a="same", v=[(24.24, 25.46, 1, 1.0)]),
    # "Yang paling besar macam ni sampai kecil pun ada."
    dict(name="besar", a="same", v=[(25.82, 28.80, 1, 1.0)]),
    # "Korang buatlah mak korang tersenyum, beli durian ni | ataupun buat diri sendiri happy kan."
    #  ("Ya Rabbi, Ya Allah" before it cut)
    dict(name="beli", a="same", v=[(31.30, 34.76, 1, 1.0), (34.76, 37.44, 1, 1.06)]),
    # CTA: "Korang tengok dekat beg kuning, boleh dapatkan sekarang."  ("Nah," cut)
    dict(name="cta", a="same", v=[(38.52, 40.88, 1, 1.0)]),
    # end card over the last shot (unclear "terima kasih / comel macam ni" muted)
    dict(name="end", a=None, v=[(40.88, 42.94, 1, 1.0)]),
]

FIX = {"bantai": "bantal", "doian": "durian", "doyan": "durian", "reto": "kereta", "reta": "kereta",
       "tengah": "tengok", "kekecil": "kecil", "Robi": "Rabbi", "size": "saiz", "tidak": "tidur"}


def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


# hand-checked words (re-transcribed per chunk; Whisper drifts on "bantal", "durian", "kereta")
OVERRIDE = {
    5.96: _w(("Kalau", 5.98, 6.16), ("kita", 6.16, 6.36), ("bagi", 6.36, 6.64), ("hadiah", 6.64, 7.38),
             ("dekat", 7.38, 7.66), ("kawan,", 7.66, 8.10), ("dekat", 8.16, 8.42), ("best", 8.42, 8.70),
             ("friend,", 8.70, 8.96)),
    13.05: _w(("Mesti", 13.08, 13.28), ("mak", 13.28, 13.44), ("tersenyum.", 13.44, 14.04)),
    14.12: _w(("Eh,", 14.14, 14.40), ("comelnya", 14.62, 15.24), ("bantal", 15.24, 15.64), ("durian", 15.64, 15.96),
              ("yang", 15.96, 16.20), ("gebu", 16.20, 16.46), ("lembut", 16.46, 16.90), ("ni.", 16.90, 17.40)),
    17.58: _w(("Boleh", 17.66, 18.10), ("peluk", 18.10, 18.66), ("atau", 18.66, 18.86), ("tidur.", 18.86, 19.44)),
    19.80: _w(("Atau", 19.84, 20.16), ("nak", 20.16, 20.32), ("buat", 20.32, 20.48), ("peluk", 20.48, 20.86),
              ("dalam", 20.86, 21.14), ("kereta,", 21.14, 22.04)),
    22.84: _w(("dalam", 22.88, 23.24), ("bas.", 23.24, 23.80)),
    24.24: _w(("Ada", 24.28, 24.46), ("macam-macam", 24.46, 24.94), ("saiz.", 24.94, 25.44)),
    25.82: _w(("Yang", 25.84, 26.02), ("paling", 26.02, 26.26), ("besar", 26.26, 26.66), ("macam", 26.66, 26.92),
              ("ni", 26.92, 27.12), ("sampai", 27.12, 27.64), ("kecil", 27.64, 28.22), ("pun", 28.22, 28.40),
              ("ada.", 28.40, 28.76)),
    31.30: _w(("Korang", 31.32, 31.58), ("buatlah", 31.58, 32.50), ("mak", 32.70, 33.12), ("korang", 33.12, 33.40),
              ("tersenyum,", 33.40, 34.06), ("beli", 34.10, 34.38), ("durian", 34.38, 34.62), ("ni", 34.62, 34.74)),
    34.76: _w(("ataupun", 34.80, 35.20), ("buat", 35.20, 35.40), ("diri", 35.40, 35.68), ("sendiri", 35.68, 35.94),
              ("happy", 35.94, 36.44), ("kan.", 36.44, 37.00)),
    38.52: _w(("Korang", 38.56, 38.72), ("tengok", 38.72, 38.90), ("dekat", 38.90, 39.10), ("beg", 39.10, 39.28),
              ("kuning,", 39.28, 39.46), ("boleh", 39.46, 39.64), ("dapatkan", 39.64, 40.14),
              ("sekarang.", 40.14, 40.70)),
}
DROP = []
KEYWORDS = {"SANGKA", "HAPPY", "TERSENYUM", "HADIAH", "KAWAN", "BEST", "FRIEND", "ANAK", "MAK", "DURIAN",
            "COMELNYA", "BANTAL", "GEBU", "LEMBUT", "PELUK", "TIDUR", "KERETA", "BAS", "SAIZ", "MACAM-MACAM",
            "BESAR", "KECIL", "BELI", "BEG", "KUNING", "SEKARANG"}

# ---------------------------------------------------------------- her head (face avoidance)
# Head + hood box sampled every second from gridded proxy frames (fractions of the source frame, x0, y0, x1, y1).
# Close-ups where she is out of frame have no entry. edit.py turns these into px boxes (zoom applied) for each
# graphic's time window; the composition keeps every graphic HEAD_MARGIN px clear of all of them.
HEADS = [
    (0, (0.36, 0.17, 0.64, 0.42)), (1, (0.30, 0.17, 0.68, 0.42)), (2, (0.33, 0.17, 0.78, 0.44)),
    (3, (0.55, 0.21, 0.90, 0.47)), (4, (0.50, 0.21, 0.92, 0.47)), (5, (0.52, 0.15, 0.96, 0.42)),
    (6, (0.54, 0.03, 1.00, 0.35)), (7, (0.84, 0.00, 1.00, 0.07)), (8, (0.86, 0.00, 1.00, 0.05)),
    (9, (0.35, 0.00, 0.80, 0.26)), (10, (0.07, 0.09, 0.53, 0.40)), (11, (0.37, 0.12, 0.71, 0.37)),
    (12, (0.46, 0.22, 0.82, 0.50)), (13, (0.45, 0.21, 0.82, 0.49)), (14, (0.47, 0.19, 0.86, 0.44)),
    (15, (0.84, 0.15, 1.00, 0.34)),
    (22, (0.58, 0.17, 1.00, 0.45)), (23, (0.33, 0.16, 0.75, 0.43)), (24, (0.24, 0.19, 0.70, 0.44)),
    (25, (0.30, 0.20, 0.76, 0.48)), (26, (0.55, 0.21, 0.99, 0.45)), (27, (0.61, 0.15, 1.00, 0.40)),
    (28, (0.54, 0.12, 0.93, 0.35)), (29, (0.40, 0.12, 0.83, 0.37)), (30, (0.38, 0.09, 0.84, 0.35)),
    (31, (0.40, 0.11, 0.79, 0.35)), (32, (0.49, 0.25, 0.81, 0.48)), (33, (0.44, 0.21, 0.78, 0.45)),
    (34, (0.41, 0.11, 0.85, 0.37)), (35, (0.31, 0.04, 0.80, 0.35)), (36, (0.33, 0.03, 0.86, 0.32)),
    (37, (0.33, 0.04, 0.83, 0.32)), (38, (0.38, 0.06, 0.84, 0.32)), (39, (0.33, 0.09, 0.75, 0.35)),
    (40, (0.33, 0.12, 0.74, 0.37)), (41, (0.30, 0.12, 0.69, 0.37)), (42, (0.32, 0.15, 0.71, 0.40)),
]
# Pillow smileys in the close-ups (the frame is all pillow there): graphics steer off these points when they can.
FACES = [
    (7, [(0.48, 0.36), (0.42, 0.88), (0.08, 0.60)]), (8, [(0.33, 0.37), (0.30, 0.90), (0.92, 0.30)]),
    (16, [(0.55, 0.27), (0.53, 0.45), (0.86, 0.55)]), (17, [(0.53, 0.26), (0.50, 0.50), (0.88, 0.52)]),
    (18, [(0.52, 0.30), (0.47, 0.50), (0.88, 0.48)]), (19, [(0.52, 0.40), (0.48, 0.60), (0.90, 0.50)]),
    (20, [(0.48, 0.40), (0.47, 0.60), (0.92, 0.45)]), (21, [(0.40, 0.30), (0.80, 0.48), (0.60, 0.75)]),
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
def graphics():
    labels, wipes, tags, sfx = [], [], [], []

    def lab(s0, s1, text, emoji="", sound="knock", vol=0.45, src=True, kind="sign", big=False, unit=None):
        t0, t1 = (tl(s0), tl(s1)) if src else (s0, s1)
        labels.append(dict(t0=t0, t1=t1, html=text, emoji=emoji, kind=kind, big=big, unit=unit,
                           heads=heads_for(t0, t1), faces=faces_for(t0, t1)))
        if sound:
            sfx.append((sound, t0 - 0.03, vol))

    def sweep(block, sound="whoosh", vol=0.4):
        t = BT[block]["t0"]
        wipes.append(dict(t=t))
        sfx.append((sound, t - 0.3, vol))
        sfx.append(("rustle", t - 0.15, 0.35))

    # hook: "tak sangka ... buat orang happy, tersenyum"
    lab(0.02, 2.50, "TAK <b>SANGKA!</b>", "😮", sound="knock", vol=0.5)
    lab(2.58, 5.42, "BUAT ORANG <b>TERSENYUM</b>", "😊", sound="sparkle", vol=0.4, big=True)
    lab(6.36, 8.96, "IDEA <b>HADIAH</b>", "🎁")
    lab(9.30, 10.80, "ANAK • <b>MAK</b>", "👩‍👧")
    lab(10.86, 12.22, "PEMINAT <b>DURIAN</b>", "🌳", sound="pop")
    lab(13.08, 14.06, "MAK <b>TERSENYUM</b>", "🥰", sound="sparkle", vol=0.35)
    sweep("comel")
    lab(14.62, 17.50, "GEBU & <b>LEMBUT</b>", "☁️", big=True)
    lab(17.66, 19.44, "TEMAN <b>TIDUR</b>", "😴", sound="pop")
    lab(19.84, 21.94, "PELUK DALAM <b>KERETA</b>", "🚗")
    lab(22.88, 23.92, "DALAM <b>BAS</b>", "🚌", sound="pop")
    sweep("saiz", sound="swish", vol=0.35)
    lab(24.28, 25.44, "4", "📏", kind="log", unit="SAIZ", sound="impact", vol=0.3)
    lab(25.86, 27.10, "PALING <b>BESAR</b>", "💪")
    lab(27.14, 28.78, "<b>KECIL</b> PUN ADA", "🐣", sound="pop")
    lab(31.32, 34.06, "BUAT MAK <b>TERSENYUM</b>", "😊")
    lab(34.10, 34.74, "BELI <b>DURIAN</b> NI", "💛", sound="pop")
    lab(34.80, 37.40, "DIRI SENDIRI PUN <b>HAPPY</b>", "🥳", sound="sparkle", vol=0.4, big=True)
    lab(38.56, 40.86, "TEKAN <b>BEG KUNING</b>", "🛒", sound="ding", vol=0.35)
    e0 = BT["end"]["t0"] - 0.05
    end = dict(t0=e0, t1=TOTAL, title="BANTAL PELUK <b>DURIAN</b> 🌳",
               sizes="📏 4 SAIZ • GEBU • LEMBUT", cta="🛒 TEKAN BEG KUNING",
               heads=heads_for(e0, TOTAL), faces=faces_for(e0, TOTAL), py=1150)
    sfx.append(("knock", e0 + 0.05, 0.45))
    sfx.append(("rustle", e0 + 0.2, 0.3))
    sfx.append(("ding", e0 + 0.55, 0.3))
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
