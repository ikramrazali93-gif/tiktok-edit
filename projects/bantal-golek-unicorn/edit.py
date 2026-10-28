#!/usr/bin/env python3
"""Edit for bantal golek / bantal peluk unicorn (IMG_3179), "Pelangi unicorn hologram" look. The graphics layer is
a HyperFrames (HTML + GSAP) composition, as in ../bantal-durian-2. She barely talks in this clip (opening line, a
price line that is cut, the CTA), so the story is told by labels over a soft synthesized music bed (music.wav
from sfx.py, ducked under her voice).

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
# One 156s clip outdoors on grass: ~45s of opening a black plastic parcel, then she lifts, hugs and swings a long
# pink bolster with a unicorn/rainbow print. Speech: "Wih, bantal peluk" (3s), "Sekejap, tengok kita buka ni"
# (6s), a price line (149-152s, cut), "Boleh tengok dekat bawah sekarang" (152s) and "Panjang tau" (155s).
# The hook J-cuts "Panjang tau! Wih, bantal peluk." over her swinging the bolster at the camera.
# v: list of (src_in, src_out, speed, zoom); a: 'same' (follow v at 1x), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK: "Panjang tau!" (155s) + "Wih, bantal peluk." (3s) over the bolster held up and swung sideways
    dict(name="hook", a=[(154.82, 155.56), (3.12, 5.72)], v=[(125.80, 127.50, 1, 1.0), (127.50, 129.14, 1, 1.06)]),
    # "Sekejap, tengok kita buka ni."
    dict(name="buka", a="same", v=[(5.74, 7.42, 1, 1.0)]),
    # opening the black parcel, x6, no speech
    dict(name="unbox", a=None, v=[(7.42, 49.60, 6, 1.0)]),
    # the bolster slides out of the bag (x1.5)
    dict(name="reveal", a=None, v=[(49.60, 54.10, 1.5, 1.0)]),
    # montage, no speech (music bed + labels): lifted high / hug diagonal / held upright / wrap hug /
    # both arms / swung sideways / cuddle
    dict(name="panjang", a=None, v=[(59.60, 62.60, 1, 1.0)]),
    dict(name="corak", a=None, v=[(66.00, 68.60, 1, 1.0)]),
    dict(name="atas", a=None, v=[(80.00, 82.60, 1, 1.0)]),
    dict(name="tidur", a=None, v=[(88.00, 90.60, 1, 1.0)]),
    dict(name="kuat", a=None, v=[(112.00, 114.60, 1, 1.0)]),
    dict(name="pink", a=None, v=[(130.20, 132.80, 1, 1.0)]),
    dict(name="lena", a=None, v=[(139.00, 141.60, 1, 1.0)]),
    # CTA: "Boleh tengok dekat bawah sekarang."  (the price line before it is cut: no prices)
    dict(name="cta", a="same", v=[(151.97, 153.95, 1, 1.0)]),
    # end card over a cuddle shot, muted
    dict(name="end", a=None, v=[(144.00, 146.80, 1, 1.0)]),
]

FIX = {"bantai": "bantal", "bukak": "buka", "tahu": "tau"}


def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


# hand-checked words (Whisper hallucinates on this clip's wind/plastic noise; timings from the envelope)
OVERRIDE = {
    154.82: _w(("Panjang", 154.86, 155.30), ("tau!", 155.30, 155.54)),
    3.12: _w(("Wih,", 3.18, 3.74), ("bantal", 4.10, 4.76), ("peluk.", 4.80, 5.68)),
    5.74: _w(("Sekejap,", 5.78, 6.08), ("tengok", 6.48, 6.70), ("kita", 6.70, 6.92), ("buka", 6.92, 7.20),
             ("ni.", 7.20, 7.38)),
    151.97: _w(("Boleh", 152.00, 152.20), ("tengok", 152.20, 152.64), ("dekat", 152.68, 152.88),
               ("bawah", 152.88, 153.04), ("sekarang.", 153.04, 153.92)),
}
DROP = []
KEYWORDS = {"PANJANG", "TAU!", "BANTAL", "PELUK", "BUKA", "BAWAH", "SEKARANG"}

# ---------------------------------------------------------------- her head (face avoidance)
# Head + hood box sampled from gridded proxy frames (fractions of the source frame, x0, y0, x1, y1). The parcel
# shots (7-50s) are sampled every 2-4s: she stands still there. edit.py turns these into px boxes (zoom applied)
# for each graphic's time window; the composition keeps every graphic HEAD_MARGIN px clear of all of them.
HEADS = [
    (3, (0.35, 0.17, 0.72, 0.42)), (4, (0.33, 0.17, 0.72, 0.42)), (5, (0.33, 0.17, 0.72, 0.42)),
    (6, (0.33, 0.17, 0.72, 0.42)), (7, (0.33, 0.17, 0.72, 0.42)), (8, (0.33, 0.17, 0.72, 0.42)),
    (12, (0.33, 0.18, 0.72, 0.43)), (16, (0.33, 0.18, 0.72, 0.43)), (20, (0.33, 0.18, 0.72, 0.43)),
    (24, (0.33, 0.18, 0.72, 0.43)), (28, (0.30, 0.20, 0.70, 0.45)), (32, (0.30, 0.19, 0.70, 0.45)),
    (36, (0.33, 0.19, 0.72, 0.45)), (40, (0.33, 0.19, 0.72, 0.45)), (44, (0.33, 0.19, 0.72, 0.45)),
    (48, (0.33, 0.19, 0.72, 0.45)), (50, (0.33, 0.18, 0.72, 0.43)), (51, (0.33, 0.17, 0.72, 0.42)),
    (52, (0.35, 0.17, 0.75, 0.42)), (53, (0.40, 0.17, 0.78, 0.42)), (54, (0.30, 0.17, 0.78, 0.42)),
    (60, (0.52, 0.16, 0.85, 0.40)), (61, (0.50, 0.17, 0.90, 0.42)), (62, (0.47, 0.15, 0.90, 0.42)),
    (63, (0.48, 0.13, 0.95, 0.40)), (66, (0.45, 0.12, 0.90, 0.40)), (67, (0.45, 0.12, 0.92, 0.40)),
    (68, (0.45, 0.10, 0.95, 0.38)), (69, (0.45, 0.10, 0.93, 0.38)), (80, (0.50, 0.08, 1.00, 0.36)),
    (81, (0.50, 0.09, 1.00, 0.42)), (82, (0.55, 0.08, 1.00, 0.42)), (83, (0.45, 0.08, 1.00, 0.42)),
    (88, (0.25, 0.12, 0.78, 0.47)), (89, (0.25, 0.12, 0.78, 0.47)), (90, (0.22, 0.12, 0.78, 0.47)),
    (91, (0.22, 0.12, 0.78, 0.47)), (112, (0.42, 0.12, 0.92, 0.45)), (113, (0.40, 0.12, 0.92, 0.45)),
    (114, (0.36, 0.12, 0.84, 0.45)), (115, (0.40, 0.17, 0.85, 0.45)), (125, (0.36, 0.14, 0.86, 0.42)),
    (126, (0.40, 0.12, 0.92, 0.42)), (127, (0.25, 0.06, 0.75, 0.36)), (128, (0.36, 0.15, 0.82, 0.48)),
    (129, (0.40, 0.15, 0.90, 0.42)), (130, (0.36, 0.17, 0.88, 0.42)), (131, (0.30, 0.18, 0.82, 0.42)),
    (132, (0.36, 0.18, 0.85, 0.42)), (133, (0.36, 0.18, 0.86, 0.43)), (139, (0.50, 0.20, 0.97, 0.47)),
    (140, (0.55, 0.20, 0.97, 0.47)), (141, (0.55, 0.20, 0.97, 0.47)), (142, (0.45, 0.20, 0.92, 0.47)),
    (144, (0.42, 0.18, 0.95, 0.45)), (145, (0.45, 0.17, 0.96, 0.45)), (146, (0.42, 0.17, 0.96, 0.45)),
    (147, (0.45, 0.17, 0.96, 0.45)), (152, (0.36, 0.17, 0.92, 0.47)), (153, (0.36, 0.17, 0.92, 0.47)),
    (154, (0.36, 0.17, 0.92, 0.47)),
]
FACES = []              # the bolster has no face
HEAD_PAD = 2.0          # samples are up to 4s apart in the parcel shots: look a bit further either side
LAB_Y, CAP_Y = 270, 1405  # preferred centres (px): labels in the top band, captions just above the TikTok caption
MUSIC_VOL, MUSIC_DUCK = 0.58, 0.16   # music.wav gain alone / under her voice


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

    def lab(t0, t1, text, emoji="", sound="twinkle", vol=0.45, kind="holo", big=False, block=None):
        """Label on the timeline; with block=, t0/t1 are offsets inside that block (most blocks are silent)."""
        if block:
            t0, t1 = BT[block]["t0"] + t0, BT[block]["t0"] + t1
        labels.append(dict(t0=t0, t1=t1, html=text, emoji=emoji, kind=kind, big=big,
                           heads=heads_for(t0, t1), faces=faces_for(t0, t1)))
        if sound:
            sfx.append((sound, t0 - 0.03, vol))

    def wipe(block, sound="whoosh", vol=0.4):
        t = BT[block]["t0"]
        wipes.append(dict(t=t))
        sfx.append((sound, t - 0.3, vol))
        sfx.append(("sparkle", t - 0.05, 0.3))

    # hook: "Panjang tau! Wih, bantal peluk."
    lab(tl(154.86), tl(155.54), "PANJANG <b>TAU!</b>", "📏", sound="impact", vol=0.3, big=True)
    lab(tl(4.10) - 0.35, BT["hook"]["dur"] - 0.04, "BANTAL PELUK <b>UNICORN</b>", "🦄", sound="shimmer", vol=0.45,
        big=True)
    lab(tl(6.48) - 0.1, tl(7.38) + 0.02, "JOM <b>UNBOXING!</b>", "📦", sound="pop")
    tags.append(dict(t0=BT["unbox"]["t0"], t1=BT["unbox"]["t0"] + BT["unbox"]["dur"], text=">> x6"))
    lab(0.6, 6.6, "SABAR, TENGAH <b>BUKA</b>...", "😆", block="unbox")
    wipe("reveal", sound="riser", vol=0.35)
    lab(0.9, 2.95, "<b>TARAA!</b>", "✨", sound="shimmer", vol=0.5, big=True, block="reveal")
    lab(0.2, 2.9, "PANJANG <b>GILA!</b>", "🤩", block="panjang")
    lab(0.15, 2.5, "CORAK <b>UNICORN & PELANGI</b>", "🌈", block="corak")
    lab(0.15, 2.5, "PELUK <b>ATAS KE BAWAH</b>", "🤗", block="atas")
    lab(0.15, 2.5, "TEMAN <b>TIDUR</b>", "😴", block="tidur")
    lab(0.15, 2.5, "PELUK <b>KUAT-KUAT</b>", "💞", block="kuat")
    lab(0.15, 2.5, "PINK <b>CERIA</b>", "💖", block="pink")
    lab(0.15, 2.5, "LENA <b>SAMPAI PAGI</b>", "🌙", block="lena")
    lab(tl(152.00) - 0.05, tl(153.92), "TENGOK <b>BEG KUNING</b>", "👇", sound="ding", vol=0.35)
    wipe("end", sound="swish", vol=0.35)
    e0 = BT["end"]["t0"] - 0.05
    end = dict(t0=e0, t1=TOTAL, title="BANTAL PELUK<br><b>UNICORN</b> 🦄",
               sizes="🌈 PANJANG • CORAK PELANGI", cta="🛒 TEKAN BEG KUNING",
               heads=heads_for(e0, TOTAL), faces=faces_for(e0, TOTAL), py=1150)
    sfx.append(("shimmer", e0 + 0.1, 0.4))
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
