#!/usr/bin/env python3
"""Edit for kusyen duduk #1 (IMG_3066), "Kafe kopi & kraft" look. First of five videos of the red/beige waffle
seat cushion; the graphics layer is a HyperFrames (HTML + GSAP) composition, as in ../bantal-durian-2.

New user rule for this series: keep the middle of the frame clean (no labels, stickers, particles or wipes in
x 160-920 / y 480-1340), fewer and more compact labels, never on her face.

Pipeline (all times in BLOCKS are source times of the original clip, same timeline as the proxy):
  1. base.mp4      - cut/zoomed video + cleaned voice (v2 chain, -11.5 LUFS) + SFX       (ffmpeg)
  2. comp/data.js  - captions, labels, flashes, end card + her head boxes for each of them (this script)
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
# One handheld clip outdoors: she holds a beige and a red tufted waffle cushion, with a few close-ups of the
# texture and the thickness. She opens with the "geng ofis lenguh" hook line, so the order stays as shot.
# v: list of (src_in, src_out, speed, zoom); a: 'same' (follow v at 1x), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK: "Yang mana geng-geng ofis lenguh-lenguh duduk lama-lama kan?"
    dict(name="hook", a="same", v=[(0.00, 1.24, 1, 1.0), (1.24, 3.80, 1, 1.05)]),
    # "Dah ada ke bantal untuk alas duduk? Ni selesa macam ni. | Memang ngam elok. Saiz dia 40cm x 40cm."
    dict(name="alas", a="same", v=[(4.08, 8.02, 1, 1.0), (8.02, 11.25, 1, 1.05)]),
    # "Memang ngam dengan kerusi ofis korang."
    dict(name="kerusi", a="same", v=[(11.30, 14.47, 1, 1.0)]),
    # "Ada macam-macam colour. Warna merah pun cantik ... sangat-sangat."  ("Okey" before it cut)
    dict(name="warna", a="same", v=[(14.77, 18.70, 1, 1.0)]),
    # "Ni ketebalan dia."  ("Okey" before it and the repeated "size 40cm x 40cm ni" after it cut)
    dict(name="tebal", a="same", v=[(19.17, 20.26, 1, 1.0)]),
    # "Material jenis waffle."  (texture close-up)
    dict(name="waffle", a="same", v=[(22.94, 25.32, 1, 1.0)]),
    # "Senang boleh basuh tau korang. Tengok dekat"
    dict(name="basuh", a="same", v=[(25.70, 28.84, 1, 1.0)]),
    # CTA: "beg kuning di bawah tau."  (pause after "dekat" cut)
    dict(name="cta", a="same", v=[(29.38, 30.90, 1, 1.0)]),
    # end card over the last second in slow motion (the repeated "beg kuning" muted)
    dict(name="end", a=None, v=[(30.90, 31.64, 0.5, 1.0)]),
]

FIX = {"bantai": "bantal", "bantuan": "bantal", "lengoh": "lenguh", "-lengoh": "-lenguh", "bag": "beg",
       "color": "colour", "size": "saiz", "Size": "Saiz", "office": "ofis", "tahu": "tau"}


def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


# hand-checked words (re-transcribed per chunk + loudness envelope; Whisper hears "bantai/bantuan" for "bantal")
OVERRIDE = {
    0.00: _w(("Yang", 0.00, 0.38), ("mana", 0.38, 0.82), ("geng-geng", 0.82, 1.22)),
    1.24: _w(("ofis", 1.24, 1.76), ("lenguh-lenguh", 1.78, 2.34), ("duduk", 2.34, 2.60), ("lama-lama", 2.60, 3.24),
             ("kan?", 3.24, 3.74)),
    4.08: _w(("Dah", 4.12, 4.52), ("ada", 4.52, 4.74), ("ke", 4.74, 4.90), ("bantal", 4.90, 5.20),
             ("untuk", 5.20, 5.44), ("alas", 5.44, 5.74), ("duduk?", 5.74, 6.48), ("Ni", 6.56, 6.86),
             ("selesa", 6.86, 7.32), ("macam", 7.32, 7.70), ("ni.", 7.70, 8.00)),
    8.02: _w(("Memang", 8.04, 8.42), ("ngam", 8.42, 8.58), ("elok.", 8.58, 9.02), ("Saiz", 9.04, 9.28),
             ("dia", 9.28, 9.42), ("40×40cm.", 9.42, 11.20)),
    11.30: _w(("Memang", 11.32, 11.76), ("ngam", 11.80, 12.00), ("dengan", 12.00, 12.26), ("kerusi", 12.26, 12.64),
              ("ofis", 12.64, 13.20), ("korang.", 13.20, 14.40)),
    14.77: _w(("Ada", 14.80, 15.12), ("macam-macam", 15.12, 15.46), ("colour.", 15.46, 15.84), ("Warna", 16.00, 16.12),
              ("merah", 16.12, 16.48), ("pun", 16.48, 16.72), ("cantik", 16.74, 18.10), ("sangat-sangat.", 18.14, 18.66)),
    19.17: _w(("Ni", 19.20, 19.44), ("ketebalan", 19.44, 19.98), ("dia.", 19.98, 20.12)),
    22.94: _w(("Material", 23.08, 23.56), ("jenis", 23.56, 24.06), ("waffle.", 24.06, 25.26)),
    25.70: _w(("Senang", 25.76, 26.20), ("boleh", 26.20, 26.42), ("basuh", 26.42, 26.88), ("tau", 26.88, 27.06),
              ("korang.", 27.06, 28.18), ("Tengok", 28.20, 28.60), ("dekat", 28.60, 28.80)),
    29.38: _w(("beg", 29.42, 29.66), ("kuning", 29.66, 29.96), ("di", 29.96, 30.10), ("bawah", 30.10, 30.36),
              ("tau.", 30.36, 30.86)),
}
DROP = []
KEYWORDS = {"OFIS", "LENGUH-LENGUH", "DUDUK", "BANTAL", "ALAS", "SELESA", "NGAM", "40×40CM", "KERUSI",
            "MACAM-MACAM", "COLOUR", "MERAH", "CANTIK", "KETEBALAN", "WAFFLE", "BASUH", "BEG", "KUNING"}

# ---------------------------------------------------------------- her head (face avoidance)
# Head + hood box sampled every second (plus a few in-between samples where she swings) from gridded proxy frames (fractions of the source frame, x0, y0, x1, y1).
# Texture close-ups where she is out of frame (23.3-25.9s) have no entry. edit.py turns these into px boxes (zoom
# applied) for each graphic's time window; the composition keeps every graphic HEAD_MARGIN px clear of them.
HEADS = [
    (0, (0.33, 0.16, 0.70, 0.44)), (1, (0.34, 0.15, 0.75, 0.42)), (2, (0.38, 0.16, 0.80, 0.42)),
    (3, (0.33, 0.17, 0.69, 0.43)), (4, (0.41, 0.20, 0.77, 0.44)), (5, (0.39, 0.19, 0.77, 0.44)),
    (6, (0.25, 0.18, 0.61, 0.43)), (7, (0.39, 0.19, 0.79, 0.43)), (8, (0.53, 0.20, 0.87, 0.45)),
    (9, (0.53, 0.19, 0.91, 0.46)), (10, (0.65, 0.09, 1.00, 0.37)), (11, (0.57, 0.04, 1.00, 0.35)),
    (12, (0.57, 0.04, 1.00, 0.35)), (13, (0.63, 0.01, 1.00, 0.32)), (14, (0.65, 0.01, 1.00, 0.32)),
    (15, (0.39, 0.00, 0.97, 0.30)), (15.2, (0.22, 0.00, 0.86, 0.32)), (15.5, (0.00, 0.00, 0.64, 0.30)),
    (15.8, (0.00, 0.00, 0.54, 0.26)), (16, (0.00, 0.00, 0.27, 0.27)), (17, (0.00, 0.00, 0.18, 0.28)),
    (18, (0.00, 0.00, 0.12, 0.26)), (19, (0.00, 0.00, 0.20, 0.20)), (20, (0.21, 0.00, 0.67, 0.24)),
    (21, (0.45, 0.00, 0.89, 0.26)), (22, (0.39, 0.00, 0.89, 0.27)), (22.7, (0.38, 0.00, 0.78, 0.14)),
    (23.1, (0.45, 0.00, 0.82, 0.07)),
    (26, (0.50, 0.00, 1.00, 0.20)), (27, (0.57, 0.05, 1.00, 0.33)), (28, (0.53, 0.16, 0.91, 0.41)),
    (29, (0.53, 0.21, 0.91, 0.45)), (30, (0.51, 0.21, 0.89, 0.46)), (31, (0.55, 0.20, 0.95, 0.45)),
]
FACES = []              # the cushions have no faces
HEAD_PAD = 0.5          # also count samples this many seconds outside a graphic's source range (1s grid)
LAB_Y, CAP_Y = 300, 1435  # preferred centres (px): labels in the top band, captions just above the TikTok caption
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

    def lab(s0, s1, text, emoji="", sound="clink", vol=0.4, src=True, big=False):
        t0, t1 = (tl(s0), tl(s1)) if src else (s0, s1)
        labels.append(dict(t0=t0, t1=t1, html=text, emoji=emoji, big=big,
                           heads=heads_for(t0, t1), faces=faces_for(t0, t1)))
        if sound:
            sfx.append((sound, t0 - 0.03, vol))

    def flash(block, sound="swish", vol=0.3):
        """light warm 'steam' flash at a section change (edges only, nothing sweeps through the middle)"""
        t = BT[block]["t0"]
        flashes.append(dict(t=t))
        sfx.append((sound, t - 0.12, vol))

    # only the key points (8 compact kraft tags), the captions carry the rest
    lab(0.04, 3.70, "<b>LENGUH</b> DUDUK?", "😩", vol=0.45, big=True)
    lab(6.58, 7.98, "<b>SELESA</b>", "☕", sound="pop", vol=0.4)
    lab(9.06, 11.18, "<b>40 × 40</b> CM", "📏")
    lab(11.34, 14.36, "NGAM <b>KERUSI OFIS</b>", "🪑")
    flash("warna")
    lab(16.10, 18.64, "MACAM-MACAM <b>WARNA</b>", "❤️")   # from "warna merah": her head swings across before it
    flash("waffle")
    lab(23.12, 25.24, "KAIN <b>WAFFLE</b>", "🧇")
    lab(25.82, 28.16, "SENANG <b>BASUH</b>", "🫧", sound="pop")
    lab(28.22, 30.84, "TEKAN <b>BEG KUNING</b>", "🛒", sound="ding", vol=0.3)
    e0 = BT["end"]["t0"] - 0.1
    end = dict(t0=e0, t1=TOTAL, title="BANTAL <b>ALAS DUDUK</b>", sizes="40×40 CM • WAFFLE • BOLEH BASUH",
               cta="🛒 TEKAN BEG KUNING", heads=heads_for(e0, TOTAL), faces=faces_for(e0, TOTAL), py=1330)
    sfx.append(("chalk", e0 + 0.02, 0.35))
    sfx.append(("clink", e0 + 0.45, 0.35))
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
                safe=dict(l=SAFE_L, r=CW - SAFE_R, t=SAFE_T, b=CH - SAFE_B), lab_y=LAB_Y, cap_y=CAP_Y,
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
