#!/usr/bin/env python3
"""Edit for kusyen duduk #4 (IMG_3069), "Y2K chrome pop" look. Fourth of five videos of the red/beige waffle seat
cushion; the graphics layer is a HyperFrames (HTML + GSAP) composition, as in ../kusyen-duduk-1.

Series rules: keep the middle of the frame clean (no labels, stickers, particles or wipes in x 160-920 /
y 480-1340), few and compact labels, never on her face, no prices.

Pipeline (all times in BLOCKS are source times of the original clip, same timeline as the proxy):
  1. base.mp4      - cut/zoomed video + cleaned voice (v2 chain, -11.5 LUFS) + SFX       (ffmpeg)
  2. comp/data.js  - captions, labels, glints, end card + her head boxes for each of them (this script)
  3. hf.mp4        - comp/index.html rendered by HyperFrames with base.mp4 as its muted video layer; the
                     composition places every graphic itself, outside the centre keep-out box and a margin clear
                     of every head box in its time window
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
# One handheld clip on a dirt path: she holds the beige and the red waffle cushions at her sides, swings them
# into close-ups of the texture, then stacks them. She opens with the strongest line ("kerusi meja makan nampak
# kosong") so the order stays as shot; the price line, the "apa tu, panggil apa?" stumble and the "nah, tu dia"
# filler are cut.
# v: list of (src_in, src_out, speed, zoom); a: 'same' (follow v at 1x), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK: "Kerusi meja makan korang nampak kosong, nak raya ni nanti | nampak kosong, tak cantik lah kan."
    #       (a stray "tak" + 0.4s pause at 4.74-5.28 cut, hidden by the zoom change)
    dict(name="hook", a="same", v=[(0.28, 3.30, 1, 1.0), (3.30, 4.74, 1, 1.06), (5.28, 6.88, 1, 1.0)]),
    # "Nanti tamu mai, korang nak lebih selesa di kerusi tu, letaklah ni."
    dict(name="tamu", a="same", v=[(6.88, 10.32, 1, 1.0), (10.32, 11.54, 1, 1.06)]),
    # "Cushion ni lebih selesa duduk dan tak nampak kosong sangat, naik seri kan."
    #       ("Apa tu, panggil apa?" before it cut)
    dict(name="seri", a="same", v=[(13.18, 15.90, 1, 1.0), (15.90, 17.88, 1, 1.05), (17.88, 19.04, 1, 1.12)]),
    # "Ada macam-macam warna, merah macam ni pun lawa. Warna brown pun lawa."
    #       (price line 19.4-23.2 and "Nah, tu dia tu dia" 23.2-24.5 cut)
    dict(name="warna", a="same", v=[(24.50, 26.88, 1, 1.0), (26.88, 28.78, 1, 1.0)]),
    # "Saiz dia 40cm kali 40cm."  (texture close-up)
    dict(name="saiz", a="same", v=[(28.78, 31.54, 1, 1.0)]),
    # CTA: "Korang boleh tengok dekat bawah sekarang."  ("Ok" before it cut)
    dict(name="cta", a="same", v=[(32.17, 35.02, 1, 1.0)]),
    # end card over the last second in slow motion
    dict(name="end", a=None, v=[(35.02, 36.00, 0.5, 1.0)]),
]

FIX = {"kursi": "kerusi", "Kursi": "Kerusi", "main": "mai", "main,": "mai,", "beram": "brown", "size": "saiz",
       "kali": "×", "color": "colour", "dengar": "tengok", "bag": "beg"}


def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


# hand-checked words (re-transcribed per chunk + loudness envelope)
OVERRIDE = {
    0.28: _w(("Kerusi", 0.33, 0.98), ("meja makan", 0.98, 1.60), ("korang", 1.60, 1.92),
             ("nampak", 1.92, 2.28), ("kosong,", 2.30, 3.22)),
    3.30: _w(("nak", 3.40, 3.74), ("raya ni", 3.74, 4.46), ("nanti…", 4.46, 4.72)),
    5.28: _w(("nampak", 5.30, 5.80), ("kosong,", 5.80, 6.14), ("tak", 6.14, 6.30), ("cantik", 6.30, 6.62),
             ("lah", 6.62, 6.78), ("kan.", 6.78, 6.88)),
    6.88: _w(("Nanti", 6.90, 7.06), ("tamu", 7.06, 7.46), ("mai,", 7.46, 7.72), ("korang", 7.95, 8.16),
             ("nak", 8.16, 8.37), ("lebih selesa", 8.37, 9.18), ("di", 9.22, 9.50), ("kerusi", 9.55, 9.94),
             ("tu,", 9.94, 10.30)),
    10.32: _w(("letaklah", 10.36, 11.10), ("ni.", 11.10, 11.50)),
    13.18: _w(("Cushion ni", 13.28, 14.30), ("lebih selesa", 14.36, 15.06), ("duduk", 15.08, 15.84)),
    15.90: _w(("dan", 15.92, 16.14), ("tak", 16.18, 16.34), ("nampak", 16.34, 16.72), ("kosong", 16.72, 17.14),
              ("sangat,", 17.16, 17.66)),
    17.88: _w(("naik", 17.92, 18.08), ("seri", 18.08, 18.80), ("kan!", 18.84, 19.00)),
    24.50: _w(("Ada", 24.52, 24.70), ("macam-macam", 24.70, 24.96), ("warna,", 24.96, 25.56), ("merah", 25.60, 25.90),
              ("macam ni", 25.94, 26.22), ("pun lawa.", 26.22, 26.84)),
    26.88: _w(("Warna", 27.18, 27.52), ("brown", 27.54, 27.76), ("pun lawa.", 27.78, 28.70)),
    28.78: _w(("Saiz dia", 28.84, 29.12), ("40cm", 29.12, 29.82), ("× 40cm.", 29.84, 31.40)),
    32.17: _w(("Korang", 32.20, 32.50), ("boleh", 32.50, 32.68), ("tengok dekat", 32.68, 33.10),
              ("bawah", 33.56, 33.92), ("sekarang.", 33.94, 34.90)),
}
DROP = []
KEYWORDS = {"KERUSI", "MEJA MAKAN", "RAYA NI", "LEBIH SELESA", "CUSHION NI", "PUN LAWA", "KOSONG", "RAYA", "CANTIK", "TAMU", "SELESA", "CUSHION", "DUDUK", "NAIK",
            "SERI", "MACAM-MACAM", "WARNA", "MERAH", "BROWN", "LAWA", "40CM", "BAWAH"}

# ---------------------------------------------------------------- her head (face avoidance)
# Head + hood box sampled every second from gridded proxy frames (fractions of the source frame, x0, y0, x1, y1).
# 13-14s: the beige cushion is held up over her (box kept conservative); 29-30s: texture close-up, she is out of
# frame (no entry). edit.py turns these into px boxes (zoom applied) for each graphic's time window; the
# composition keeps every graphic HEAD_MARGIN px clear of them.
HEADS = [
    (0, (0.33, 0.16, 0.66, 0.44)), (1, (0.37, 0.17, 0.66, 0.45)), (2, (0.36, 0.19, 0.75, 0.45)),
    (3, (0.48, 0.18, 0.84, 0.45)), (4, (0.47, 0.19, 0.83, 0.46)), (5, (0.47, 0.21, 0.85, 0.48)),
    (6, (0.42, 0.22, 0.83, 0.49)), (7, (0.39, 0.20, 0.89, 0.48)), (8, (0.35, 0.17, 0.76, 0.43)),
    (9, (0.39, 0.15, 0.83, 0.43)), (10, (0.55, 0.14, 0.94, 0.39)), (11, (0.76, 0.18, 1.00, 0.44)),
    (12, (0.70, 0.19, 1.00, 0.47)), (13, (0.78, 0.08, 1.00, 0.42)), (14, (0.40, 0.04, 0.80, 0.32)),
    (15, (0.76, 0.12, 1.00, 0.43)), (16, (0.60, 0.06, 1.00, 0.40)), (17, (0.53, 0.12, 0.95, 0.40)),
    (18, (0.36, 0.14, 0.75, 0.42)), (19, (0.24, 0.16, 0.66, 0.42)),
    (24, (0.55, 0.15, 0.95, 0.44)), (25, (0.55, 0.09, 0.99, 0.38)), (26, (0.75, 0.00, 1.00, 0.32)),
    (27, (0.78, 0.00, 1.00, 0.30)), (28, (0.80, 0.00, 1.00, 0.07)), (31, (0.58, 0.00, 1.00, 0.20)),
    (32, (0.30, 0.13, 0.76, 0.46)), (33, (0.39, 0.23, 0.80, 0.50)), (34, (0.48, 0.19, 0.91, 0.47)),
    (35, (0.64, 0.04, 1.00, 0.40)), (36, (0.64, 0.04, 1.00, 0.40)),
]
FACES = []              # the cushions have no faces
HEAD_PAD = 0.5          # also count samples this many seconds outside a graphic's source range (1s grid)
LAB_Y, LOW_Y, CAP_Y = 250, 1368, 1452   # preferred centres (px): top band, low band above captions, captions
KEEPOUT = [160, 480, 920, 1340]   # centre of the frame: product + her body, no labels/stickers/accents here


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
    labels, flashes, tags, sfx = [], [], [], []

    def lab(s0, s1, text, emoji="", sound="blip", vol=0.35, src=True, big=False, low=False):
        t0, t1 = (tl(s0), tl(s1)) if src else (s0, s1)
        labels.append(dict(t0=t0, t1=t1, html=text, emoji=emoji, big=big, py=LOW_Y if low else LAB_Y,
                           heads=heads_for(t0, t1), faces=faces_for(t0, t1)))
        if sound:
            sfx.append((sound, t0 - 0.03, vol))

    def glint(block, sound="glint", vol=0.28):
        """chrome glint at a section change: a shine runs along the top and bottom edges, pixel stars in the
        corners; nothing crosses the middle"""
        t = BT[block]["t0"]
        flashes.append(dict(t=t))
        sfx.append((sound, t - 0.1, vol))

    # only the key points (7 compact pieces); the captions carry the rest
    lab(0.33, 3.30, "KERUSI <b>NAMPAK KOSONG?</b>", "🪑", sound="pix", vol=0.4, big=True)
    lab(3.40, 6.86, "NAK <b>RAYA</b> NI!", "✨", low=True)
    lab(7.95, 11.48, "LEBIH <b>SELESA</b> DUDUK", "💺", low=True)
    glint("seri")
    lab(17.92, 19.02, "<b>NAIK SERI!</b>", "💖", sound="pix", vol=0.4, big=True)
    glint("warna")
    lab(24.94, 28.72, "<b>MERAH</b> • <b>BROWN</b>", "🎨", low=True)
    lab(29.12, 31.44, "<b>40 × 40</b> CM", "📏", low=True)
    lab(32.20, 34.96, "TEKAN <b>BEG KUNING</b>", "🛒", sound="blip", vol=0.3, low=True)
    e0 = BT["end"]["t0"] - 0.05
    end = dict(t0=e0, t1=TOTAL, title="KUSYEN <b>DUDUK</b>", sizes="40×40 CM • MERAH • BROWN",
               cta="🛒 TEKAN BEG KUNING", heads=heads_for(e0, TOTAL), faces=faces_for(e0, TOTAL), py=1330)
    sfx.append(("glint", e0 - 0.05, 0.3))
    sfx.append(("pix", e0 + 0.4, 0.3))
    return labels, flashes, tags, end, sfx


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
    labels, flashes, tags, end, sfx = graphics()
    data = dict(total=TOTAL, fps=FPS, w=CW, h=CH,
                safe=dict(l=SAFE_L, r=CW - SAFE_R, t=SAFE_T, b=CH - SAFE_B), lab_y=LAB_Y, low_y=LOW_Y, cap_y=CAP_Y,
                keepout=KEEPOUT, captions=caption_chunks(words), labels=labels, flashes=flashes, tags=tags, end=end,
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
