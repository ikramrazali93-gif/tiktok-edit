#!/usr/bin/env python3
"""Edit for bantal golek / bantal peluk unicorn, video 2 (IMG_3180), "Minimal editorial bersih" look. Same product
as ../bantal-golek-unicorn (IMG_3179) but a separate short video with its own hook ("Siapa yang belum ada bantal
peluk...?") and angle (teman dakap malam-malam, untuk seisi rumah). The graphics layer is a HyperFrames (HTML +
GSAP) composition: clean cream cards, Inter Display, thin pink rules, calm easing.

Pipeline (all times in BLOCKS are source times of the original clip, same timeline as the proxy):
  1. base.mp4      - cut/zoomed video + cleaned voice (v2 chain, -11.5 LUFS) + soft music bed + SFX   (ffmpeg)
  2. comp/data.js  - captions, labels, wipes, end card + her head boxes for each of them (this script)
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
# One 34.8s handheld shot outdoors: she stands hugging the long pink unicorn/rainbow bolster and talks the whole
# time. 0-8.6s and 17.4-18.9s are price talk (cut: no prices). The hook moves her best line to the front:
# "Siapa yang belum ada bantal peluk nak dakap malam-malam? Ambil bantal peluk ni."
# v: list of (src_in, src_out, speed, zoom); a: 'same' (follow v at 1x), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK (13.7s): "Siapa yang belum ada bantal peluk nak dakap malam-malam? | Ambil bantal peluk ni."
    dict(name="hook", a="same", v=[(13.69, 15.90, 1, 1.0), (16.20, 17.25, 1, 1.07)]),
    # "Besar macam ni."  (from the price-talk opening; the words around it are cut)
    dict(name="besar", a="same", v=[(3.62, 4.60, 1, 1.0)]),
    # "Tu panjang, ni kita peluk sampai lutut lah."
    dict(name="panjang", a="same", v=[(10.46, 13.16, 1, 1.0)]),
    # "Sangat-sangat selesa."  ("Okey," cut)
    dict(name="selesa", a="same", v=[(23.76, 25.58, 1, 1.07)]),
    # "Ada macam-macam corak-corak dia. | Cantik-cantik, warna. Mak love."  ("Haa" cut)
    dict(name="corak", a="same", v=[(26.32, 28.42, 1, 1.0), (28.42, 30.74, 1, 1.07)]),
    # quiet beat (music + label): she hugs the bolster and laughs (her price line here is muted)
    dict(name="malam", a=None, v=[(0.20, 2.60, 1, 1.10)]),
    # "Boleh beli dua, tiga biji. | Anak remaja perempuan boleh guna."
    dict(name="keluarga", a="same", v=[(19.18, 20.86, 1, 1.0), (20.86, 22.44, 1, 1.07)]),
    # CTA: "Tengok dekat bawah sekarang."
    dict(name="cta", a="same", v=[(32.50, 33.32, 1, 1.0)]),
    # end card over her holding the bolster upright and smiling (muted: price talk)
    dict(name="end", a=None, v=[(5.60, 8.60, 1, 1.0)]),
]

FIX = {"bantai": "bantal", "tahu": "tau"}


def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


# hand-checked words (per-chunk re-transcription + the loudness envelope)
OVERRIDE = {
    13.69: _w(("Siapa", 13.72, 14.02), ("yang", 14.02, 14.12), ("belum", 14.12, 14.22), ("ada", 14.22, 14.40),
              ("bantal", 14.40, 14.64), ("peluk", 14.64, 14.94), ("nak", 14.94, 15.06), ("dakap", 15.06, 15.36),
              ("malam-malam?", 15.36, 15.88)),
    16.20: _w(("Ambil", 16.24, 16.60), ("bantal", 16.60, 16.84), ("peluk", 16.84, 17.10), ("ni.", 17.10, 17.22)),
    3.62: _w(("Besar", 3.70, 3.94), ("macam", 3.94, 4.32), ("ni.", 4.32, 4.56)),
    10.46: _w(("Tu", 10.50, 10.94), ("panjang,", 11.00, 11.40), ("ni", 11.66, 11.76), ("kita", 11.76, 11.90), ("peluk", 11.90, 12.14),
              ("sampai", 12.14, 12.32), ("lutut", 12.32, 12.78), ("lah.", 12.94, 13.10)),
    23.76: _w(("Sangat-sangat", 23.80, 25.00), ("selesa.", 25.00, 25.52)),
    26.32: _w(("Ada", 26.36, 26.52), ("macam-macam", 26.52, 27.38), ("corak-corak", 27.38, 28.06), ("dia.", 28.06, 28.38)),
    28.42: _w(("Cantik-cantik,", 28.46, 29.34), ("warna.", 29.44, 29.88), ("Mak", 30.20, 30.40), ("love.", 30.40, 30.72)),
    19.18: _w(("Boleh", 19.22, 19.58), ("beli", 19.58, 19.86), ("dua,", 19.86, 20.04), ("tiga", 20.10, 20.28),
              ("biji.", 20.28, 20.82)),
    20.86: _w(("Anak", 21.04, 21.18), ("remaja", 21.18, 21.58), ("perempuan", 21.72, 21.94), ("boleh", 21.94, 22.12),
              ("guna.", 22.12, 22.40)),
    32.50: _w(("Tengok", 32.56, 32.76), ("dekat", 32.76, 32.92), ("bawah", 32.92, 33.04), ("sekarang.", 33.04, 33.28)),
}
DROP = []
BREAK_BEFORE = {14.40, 14.94, 12.14, 27.38, 21.94}   # forced caption chunk starts (source times)
KEYWORDS = {"BANTAL", "PELUK", "DAKAP", "PANJANG", "LUTUT", "SELESA", "CORAK-CORAK", "CANTIK-CANTIK", "BESAR",
            "BAWAH", "ANAK", "BIJI"}

# ---------------------------------------------------------------- her head (face avoidance)
# Head + hood box from gridded proxy frames every 1s (fractions of the source frame, x0, y0, x1, y1), padded a
# little. edit.py turns these into px boxes (zoom applied) for each graphic's time window; the composition keeps
# every graphic HEAD_MARGIN px clear of all of them.
HEADS = [
    (0, (0.40, 0.15, 0.82, 0.47)), (1, (0.43, 0.15, 0.84, 0.47)), (2, (0.41, 0.13, 0.84, 0.47)),
    (3, (0.41, 0.13, 0.84, 0.47)), (4, (0.40, 0.14, 0.80, 0.47)), (5, (0.43, 0.16, 0.84, 0.47)),
    (6, (0.43, 0.15, 0.82, 0.47)), (7, (0.43, 0.15, 0.82, 0.47)), (8, (0.53, 0.16, 1.00, 0.52)),
    (9, (0.56, 0.12, 0.98, 0.47)), (10, (0.34, 0.11, 0.82, 0.47)), (11, (0.36, 0.10, 0.84, 0.47)),
    (12, (0.42, 0.13, 0.96, 0.49)), (13, (0.42, 0.11, 0.94, 0.47)), (14, (0.46, 0.10, 0.98, 0.47)),
    (15, (0.42, 0.10, 0.98, 0.47)), (16, (0.52, 0.08, 0.92, 0.47)), (17, (0.52, 0.10, 0.94, 0.47)),
    (18, (0.46, 0.10, 0.90, 0.47)), (19, (0.50, 0.10, 0.98, 0.47)), (20, (0.50, 0.10, 1.00, 0.47)),
    (21, (0.48, 0.06, 0.98, 0.44)), (22, (0.46, 0.04, 0.98, 0.44)), (23, (0.46, 0.05, 0.96, 0.44)),
    (24, (0.52, 0.05, 0.92, 0.44)), (25, (0.50, 0.05, 0.90, 0.44)), (26, (0.48, 0.08, 0.94, 0.47)),
    (27, (0.48, 0.08, 0.92, 0.47)), (28, (0.50, 0.08, 0.98, 0.47)), (29, (0.52, 0.08, 0.98, 0.47)),
    (30, (0.54, 0.10, 0.98, 0.47)), (31, (0.50, 0.10, 0.96, 0.47)), (32, (0.48, 0.08, 0.88, 0.44)),
    (33, (0.30, 0.08, 0.86, 0.44)), (34, (0.30, 0.10, 0.74, 0.47)),
]
FACES = []              # the bolster has no face
HEAD_PAD = 0.8          # samples are 1s apart: look a little further either side
LAB_Y, CAP_Y = 1040, 1395   # preferred centres (px): labels mid-lower (her head is high), captions above TikTok's
MUSIC_VOL, MUSIC_DUCK = 0.50, 0.12   # music.wav gain alone / under her voice


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
        if cur and ((len(cur) >= 5 or (chars > 26 and not tail)) or w.get("src") in BREAK_BEFORE
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
        out.append(dict(t0=ch[0]["s"], t1=end, y=CAP_Y, heads=heads_for(ch[0]["s"], end), faces=faces_for(ch[0]["s"], end),
                        words=[dict(w=x["w"].strip(",."), s=x["s"], e=x["e"],
                                    key=x["w"].upper().strip(",.?!") in KEYWORDS) for x in ch]))
    return out


# ---------------------------------------------------------------- graphics (data for comp/index.html)
def graphics():
    labels, wipes, tags, sfx = [], [], [], []

    def lab(t0, t1, text, kick, emoji="", sound="click", vol=0.35, big=False, block=None):
        """Editorial card on the timeline: small kicker line + headline. With block=, t0/t1 are offsets inside it."""
        if block:
            t0, t1 = BT[block]["t0"] + t0, BT[block]["t0"] + t1
        labels.append(dict(t0=t0, t1=t1, html=text, kick=kick, emoji=emoji, big=big,
                           heads=heads_for(t0, t1), faces=faces_for(t0, t1)))
        if sound:
            sfx.append((sound, t0 - 0.03, vol))

    def wipe(block, sound="swish", vol=0.28):
        t = BT[block]["t0"]
        wipes.append(dict(t=t))
        sfx.append((sound, t - 0.3, vol))

    hk = BT["hook"]
    # hook: "Siapa yang belum ada bantal peluk nak dakap malam-malam? Ambil bantal peluk ni."
    lab(tl(13.72), tl(15.88) + 0.12, "Belum ada <b>bantal peluk?</b>", "Teman tidur", "🌙", sound="ding", vol=0.28,
        big=True)
    lab(tl(16.24) - 0.05, hk["t0"] + hk["dur"] - 0.04, "Ambil <b>yang ni.</b>", "Bantal golek", "🤍", sound="pop")
    lab(tl(11.66) - 0.1, tl(13.10) + 0.04, "Peluk <b>sampai lutut</b>", "Panjang", "📏")
    wipe("corak")
    lab(tl(26.52), tl(28.38) + 0.03, "Macam-macam <b>corak</b>", "Pilihan", "🦄")
    lab(tl(28.46), tl(30.72), "Warna <b>cantik-cantik</b>", "Warna", "🌈")
    lab(0.2, BT["malam"]["dur"] - 0.1, "Dakap <b>malam-malam</b>", "Waktu tidur", "😴", block="malam")
    lab(tl(19.58) - 0.1, tl(20.82) + 0.02, "Ambil <b>2–3 biji</b>", "Seisi rumah", "🏠")
    lab(tl(21.04) - 0.05, tl(22.40) + 0.02, "Untuk <b>anak remaja</b>", "Sesuai", "👧")
    lab(tl(32.56) - 0.08, BT["cta"]["t0"] + BT["cta"]["dur"] - 0.02, "Tengok <b>beg kuning</b>", "Sekarang", "👇",
        sound="ding", vol=0.25)
    wipe("end")
    e0 = BT["end"]["t0"] - 0.05
    end = dict(t0=e0, t1=TOTAL, kick="Bantal golek · No. 02", title="Teman dakap<br><b>malam-malam.</b>",
               sizes="Panjang · Macam-macam corak", cta="Tekan beg kuning 🛒",
               heads=heads_for(e0, TOTAL), faces=faces_for(e0, TOTAL), py=1080)
    sfx.append(("sparkle", e0 + 0.15, 0.25))
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
