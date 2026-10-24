#!/usr/bin/env python3
"""Edit for bantal peluk durian #4 (IMG_3064), "Pastel lembut" (soft dreamy) look. Fourth video of the durian
series; the graphics layer is a HyperFrames (HTML + GSAP) composition, as in ../bantal-durian and ../bantal-durian-2.

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
# One handheld clip under a carport: she holds a big and a smaller durian pillow (a third, small one in the last
# shots). She opens with the "bilik nampak kosong" problem line, so the order stays as shot.
# v: list of (src_in, src_out, speed, zoom); a: 'same' (follow v at 1x), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK: "Bilik nampak kosong sangat, | tak seri kan?"  (punch-in on "tak seri")
    dict(name="hook", a="same", v=[(0.00, 2.78, 1, 1.0), (2.78, 3.88, 1, 1.08)]),
    # "(Haa,) korang tengok bantal durian ni boleh menyerikan bilik korang."  (pause + "hmm" before it cut)
    dict(name="serikan", a="same", v=[(4.50, 8.14, 1, 1.0)]),
    # "Letak kat katil tu."
    dict(name="katil", a="same", v=[(8.14, 9.06, 1, 1.05)]),
    # "Boleh peluk, teman tidur dan nampak berseri-seri."  (pause before it cut)
    dict(name="peluk", a="same", v=[(9.40, 13.62, 1, 1.0)]),
    # "Letak je satu bantal ni dah boleh naik seri kan."
    dict(name="seri", a="same", v=[(13.62, 16.10, 1, 1.06)]),
    # "(Ha,) dah lembut, gebu macam ni, fluffy, sedap peluk ni."  (pause before it cut; "Ha, dah" runs together
    #  with no gap, so the cut sits in the silence before "Ha" instead of clipping "dah")
    dict(name="lembut", a="same", v=[(16.52, 20.56, 1, 1.0)]),
    # "Ada banyak saiz. Kalau nak letak dalam kereta, boleh ambil yang ni..."
    dict(name="saiz", a="same", v=[(20.86, 23.36, 1, 1.0)]),
    # "...saiz 52cm."  (pause between "yang ni" and "size" cut)
    dict(name="s52", a="same", v=[(23.66, 25.08, 1, 1.05)]),
    # "Kalau yang ni saiz 75cm, buat peluk waktu tidur."
    dict(name="s75", a="same", v=[(25.10, 28.58, 1, 1.0)]),
    # CTA: "Korang tengok sekarang dekat bawah."  (her false start "korang tengok... (kat beg) betul" before it cut)
    dict(name="cta", a="same", v=[(31.02, 32.58, 1, 1.0)]),
    # end card over the last shot, gentle slow-mo
    dict(name="end", a=None, v=[(32.00, 32.96, 0.5, 1.0)]),
]

FIX = {"bantai": "bantal", "doian": "durian", "doyan": "durian", "reto": "kereta", "reta": "kereta",
       "tidak": "tidur", "katit": "katil", "size": "saiz", "Kau": "Korang", "75mm": "75cm"}


def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


# hand-checked words (re-transcribed per chunk; Whisper drifts on "bantal", "durian", "tidur")
OVERRIDE = {
    0.00: _w(("Bilik", 0.20, 0.64), ("nampak", 0.64, 0.90), ("kosong", 0.90, 1.44), ("sangat,", 1.44, 2.70),
             ("tak", 2.82, 2.96), ("seri", 2.96, 3.40), ("kan?", 3.40, 3.86)),
    4.50: _w(("Korang", 4.74, 4.90), ("tengok", 4.90, 5.20), ("bantal", 5.20, 5.58), ("durian", 5.58, 5.86),
             ("ni", 5.86, 6.14), ("boleh", 6.14, 6.42), ("menyerikan", 6.42, 7.04), ("bilik", 7.04, 7.36),
             ("korang.", 7.36, 8.00)),
    8.14: _w(("Letak", 8.14, 8.36), ("kat", 8.36, 8.50), ("katil", 8.50, 8.96), ("tu.", 8.96, 9.04)),
    9.40: _w(("Boleh", 9.44, 9.72), ("peluk,", 9.72, 10.56), ("teman", 10.82, 11.08), ("tidur", 11.08, 11.70),
             ("dan", 11.76, 12.02), ("nampak", 12.02, 12.48), ("berseri", 12.48, 13.12), ("-seri.", 13.12, 13.58)),
    13.62: _w(("Letak", 13.62, 13.98), ("je", 13.98, 14.06), ("satu", 14.06, 14.28), ("bantal", 14.28, 14.60),
              ("ni", 14.60, 14.84), ("dah", 14.84, 15.22), ("boleh", 15.22, 15.42), ("naik", 15.42, 15.70),
              ("seri", 15.70, 16.04), ("kan.", 16.04, 16.08)),
    16.52: _w(("Dah", 16.76, 16.90), ("lembut,", 16.90, 17.40), ("gebu", 17.44, 17.72), ("macam", 17.72, 18.02),
              ("ni,", 18.02, 18.20), ("fluffy,", 18.24, 18.80), ("sedap", 18.80, 19.40), ("peluk", 19.40, 19.82),
              ("ni.", 19.82, 20.42)),
    20.86: _w(("Ada", 20.88, 21.04), ("banyak", 21.04, 21.28), ("saiz.", 21.28, 21.52), ("Kalau", 21.62, 21.74),
              ("nak", 21.74, 21.86), ("letak", 21.86, 22.08), ("dalam", 22.08, 22.24), ("kereta,", 22.24, 22.70),
              ("boleh", 22.70, 22.94), ("ambil", 22.94, 23.18), ("yang", 23.18, 23.30), ("ni...", 23.30, 23.34)),
    23.66: _w(("saiz", 23.68, 23.90), ("52cm.", 23.90, 25.02)),
    25.10: _w(("Kalau", 25.12, 25.30), ("yang", 25.30, 25.42), ("ni", 25.42, 25.56), ("saiz", 25.56, 25.88),
              ("75cm,", 25.88, 26.82), ("buat", 26.82, 27.08), ("peluk", 27.08, 27.40), ("waktu", 27.40, 27.54),
              ("tidur.", 27.54, 28.50)),
    31.02: _w(("Korang", 31.04, 31.23), ("tengok", 31.23, 31.41), ("sekarang", 31.41, 31.75), ("dekat", 31.75, 31.95),
              ("bawah.", 31.95, 32.55)),
}
DROP = []
KEYWORDS = {"KOSONG", "SERI", "DURIAN", "BANTAL", "MENYERIKAN", "BILIK", "KATIL", "PELUK", "TIDUR", "BERSERI-SERI",
            "NAIK", "LEMBUT", "GEBU", "FLUFFY", "SEDAP", "SAIZ", "KERETA", "52CM", "75CM", "SEKARANG", "BAWAH"}

# ---------------------------------------------------------------- her head (face avoidance)
# Head + hood box (down to the chin of the face cover) sampled every second from gridded proxy frames (fractions of
# the source frame, x0, y0, x1, y1). edit.py turns these into px boxes (zoom applied) for each graphic's time
# window; the composition keeps every graphic HEAD_MARGIN px clear of all of them.
HEADS = [
    (0, (0.30, 0.15, 0.71, 0.44)), (1, (0.29, 0.15, 0.68, 0.44)), (2, (0.23, 0.14, 0.65, 0.43)),
    (3, (0.18, 0.11, 0.61, 0.43)), (4, (0.10, 0.12, 0.58, 0.43)), (5, (0.07, 0.09, 0.57, 0.41)),
    (6, (0.26, 0.14, 0.70, 0.43)), (7, (0.30, 0.18, 0.76, 0.46)), (8, (0.29, 0.16, 0.73, 0.44)),
    (9, (0.36, 0.16, 0.84, 0.45)), (10, (0.38, 0.15, 0.88, 0.44)), (11, (0.25, 0.15, 0.71, 0.45)),
    (12, (0.25, 0.15, 0.70, 0.44)), (13, (0.26, 0.15, 0.72, 0.44)), (14, (0.23, 0.19, 0.71, 0.46)),
    (15, (0.15, 0.25, 0.61, 0.55)), (16, (0.10, 0.26, 0.58, 0.56)), (17, (0.16, 0.19, 0.52, 0.49)),
    (18, (0.14, 0.12, 0.57, 0.45)), (19, (0.22, 0.14, 0.61, 0.49)), (20, (0.34, 0.15, 0.73, 0.46)),
    (21, (0.34, 0.17, 0.71, 0.46)), (22, (0.36, 0.18, 0.71, 0.46)), (23, (0.34, 0.17, 0.71, 0.45)),
    (24, (0.26, 0.19, 0.65, 0.46)), (25, (0.26, 0.23, 0.61, 0.54)), (26, (0.24, 0.24, 0.65, 0.56)),
    (27, (0.30, 0.20, 0.67, 0.54)), (28, (0.22, 0.11, 0.65, 0.47)), (29, (0.30, 0.10, 0.77, 0.45)),
    (30, (0.30, 0.13, 0.69, 0.45)), (31, (0.34, 0.20, 0.73, 0.52)), (32, (0.24, 0.18, 0.65, 0.54)),
    (33, (0.24, 0.18, 0.65, 0.54)),
]
# Pillow smileys only matter in close-ups; this clip has none (medium shots throughout).
FACES = []
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

    def lab(s0, s1, text, emoji="", sound="chime", vol=0.4, src=True, kind="card", big=False, unit=None):
        t0, t1 = (tl(s0), tl(s1)) if src else (s0, s1)
        labels.append(dict(t0=t0, t1=t1, html=text, emoji=emoji, kind=kind, big=big, unit=unit,
                           heads=heads_for(t0, t1), faces=faces_for(t0, t1)))
        if sound:
            sfx.append((sound, t0 - 0.03, vol))

    def bloom(block, vol=0.45):
        t = BT[block]["t0"]
        wipes.append(dict(t=t))
        sfx.append(("breeze", t - 0.45, vol))
        sfx.append(("sparkle", t - 0.05, 0.25))

    # hook: problem -> fix
    lab(0.20, 2.76, "BILIK NAMPAK <b>KOSONG?</b>", "🛏️", sound="bubble", vol=0.5, big=True)
    lab(2.82, 3.86, "TAK <b>BERSERI</b>", "🥲", sound="bubble", vol=0.4)
    lab(4.74, 6.40, "BANTAL <b>DURIAN</b> NI", "💛")
    lab(6.42, 8.00, "<b>SERIKAN</b> BILIK!", "✨", sound="sparkle", vol=0.35, big=True)
    lab(8.14, 9.04, "LETAK ATAS <b>KATIL</b>", "🛏️", sound="bubble", vol=0.45)
    lab(9.44, 10.70, "BOLEH <b>PELUK</b>", "🤗", sound="bubble", vol=0.4)
    lab(10.82, 11.74, "TEMAN <b>TIDUR</b>", "😴", sound="bubble", vol=0.4)
    lab(11.76, 13.58, "NAMPAK <b>BERSERI-SERI</b>", "🌸")
    lab(13.62, 16.06, "TERUS <b>NAIK SERI</b>", "🪄", sound="sparkle", vol=0.35)
    bloom("lembut")
    lab(16.78, 18.20, "LEMBUT & <b>GEBU</b>", "☁️")
    lab(18.24, 20.42, "FLUFFY, <b>SEDAP PELUK</b>", "🧸", sound="bubble", vol=0.45)
    bloom("saiz", vol=0.4)
    lab(20.88, 21.56, "BANYAK <b>SAIZ</b>", "📏", sound="bubble", vol=0.45)
    lab(21.62, 23.34, "NAK LETAK <b>DALAM KERETA?</b>", "🚗")
    lab(23.68, 25.02, "52", "🚗", kind="orb", unit="CM", sound="chime", vol=0.45)
    lab(25.56, 26.82, "75", "🛌", kind="orb", unit="CM", sound="chime", vol=0.45)
    lab(26.84, 28.50, "PELUK <b>WAKTU TIDUR</b>", "😴", sound="bubble", vol=0.4)
    lab(31.04, 32.56, "TENGOK <b>BEG KUNING</b> 👇", "🛒", sound="ding", vol=0.3)
    e0 = BT["end"]["t0"] - 0.05
    end = dict(t0=e0, t1=TOTAL, title="BANTAL PELUK <b>DURIAN</b> 🌸",
               sizes="✨ NAIK SERI BILIK • GEBU", cta="🛒 TEKAN BEG KUNING",
               heads=heads_for(e0, TOTAL), faces=faces_for(e0, TOTAL), py=1150)
    sfx.append(("chime", e0 + 0.05, 0.45))
    sfx.append(("breeze", e0 - 0.2, 0.3))
    sfx.append(("bubble", e0 + 0.6, 0.35))
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
