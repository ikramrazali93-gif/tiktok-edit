#!/usr/bin/env python3
"""Edit for the durian hug-pillow (bantal peluk durian, 4 sizes) TikTok video. First project whose graphics
layer is a HyperFrames (HTML + GSAP) composition instead of ASS subtitles + Pillow stickers.

Pipeline (all times in BLOCKS are source times of the original clip, same timeline as the proxy):
  1. base.mp4      - cut/zoomed video + cleaned voice (v2 chain, -11.5 LUFS) + SFX       (ffmpeg, as before)
  2. comp/data.js  - captions, labels, wipes, end card, per-block layout for the composition (this script)
  3. hf.mp4        - comp/index.html rendered by HyperFrames with base.mp4 as its muted video layer
  4. preview.mp4 / final.mp4 - hf.mp4 video + base.mp4 audio (ffmpeg mux; preview is scaled to 720x1280)

Graphics never go under the TikTok UI (SAFE_* below) and are laid out per block so they avoid her face and the
pillows' smiley faces where the frame allows it: labels in the top band (trees above her head), captions in the
bottom band (robe / pillow ends), with per-block overrides (LAYOUT) for shots where that band holds a face.

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
# Single clip, outdoors: she holds long durian-segment plush pillows with smiley faces (95 / 75 / 52 / 30cm)
# that fill most of the frame. Opens with a question hook, so the order stays as shot.
# v: list of (src_in, src_out, speed, zoom); a: 'same' (follow v at 1x), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK: "Korang malam tadi tidur peluk apa?"  ("Ha," before it cut)
    dict(name="hook", a="same", v=[(0.55, 3.32, 1, 1.0)]),
    # "Ada suami? Peluk suami."  (pause + "Ha" cut)
    dict(name="suami", a="same", v=[(4.62, 6.24, 1, 1.04)]),
    # "Kalau tak ada suami, yang single-single tu peluk apa?"  ("Okay" cut)
    dict(name="single", a="same", v=[(6.40, 8.74, 1, 1.0)]),
    # "Memang ni, kita nak share ni, bantal peluk, | durian yang gebu-gebas macam ni."  (stumble "doian" cut)
    dict(name="durian", a="same", v=[(9.02, 11.24, 1, 1.0), (11.90, 13.74, 1, 1.06)]),
    # "Ada macam-macam saiz. Ni saiz paling besar,"  ("dah besar sahaja dah" cut)
    dict(name="saiz", a="same", v=[(13.88, 16.40, 1, 1.0)]),
    # "95cm, gebu-gebas, tebal macam tu, sangat selesa."
    dict(name="s95", a="same", v=[(17.46, 19.62, 1, 1.0), (19.62, 21.76, 1, 1.05)]),
    # "Nak yang ni pun besar juga ni, ni saiz 75cm."  ("Ni pun bagi saya dah cukup besar dah" cut)
    dict(name="s75", a="same", v=[(22.04, 24.82, 1, 1.0)]),
    # "Ada lagi, saiz yang kecil pun ada."
    dict(name="kecil", a="same", v=[(27.78, 30.40, 1, 1.0)]),
    # bringing the small ones up (x1.5, no speech)
    dict(name="bawa", a=None, v=[(30.80, 32.15, 1.5, 1.0)]),
    # "Saiz yang lebih kecil, saiz 52cm dengan saiz 30cm."  ("Nah ni" cut)
    dict(name="s52", a="same", v=[(33.20, 35.30, 1, 1.0), (35.30, 37.70, 1, 1.0)]),
    # "Ya Rabbi, comelnya korang. Yang mana tak ada lagi,"
    dict(name="comel", a="same", v=[(38.02, 41.74, 1, 1.0)]),
    # "Boleh tengok ni. Ambik nak saiz mana satu, pilihlah. Ada empat-empat saiz ni. Lembut, gebu, fluffy.
    #  Buat teman tidur, okey?"  (pause after "lagi" cut; punch-ins on the beat)
    dict(name="pilih", a="same", v=[(42.04, 44.96, 1, 1.0), (44.96, 46.45, 1, 1.06), (46.45, 48.90, 1, 1.0),
                                     (48.90, 49.92, 1, 1.08)]),
    # end card over the slowed last moment
    dict(name="end", a=None, v=[(49.92, 50.70, 0.45, 1.0)]),
]

FIX = {"bantai": "bantal", "Robi": "Rabbi", "Amik": "Ambik", "Okay": "Okay", "korang": "korang",
       "52cm": "52CM", "95cm": "95CM", "75cm": "75CM", "30cm": "30CM"}


def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


# hand-checked words where Whisper drifted or misheard (re-transcribed per chunk)
OVERRIDE = {
    0.55: _w(("Korang", 0.58, 1.08), ("malam", 1.08, 1.54), ("tadi", 1.54, 2.06), ("tidur", 2.06, 2.46),
             ("peluk", 2.46, 2.70), ("apa?", 2.70, 3.28)),
    4.62: _w(("Ada", 4.70, 4.84), ("suami?", 4.84, 5.28), ("Peluk", 5.46, 5.68), ("suami.", 5.68, 6.18)),
    6.40: _w(("Kalau", 6.48, 6.66), ("tak", 6.66, 6.82), ("ada", 6.82, 6.88), ("suami,", 6.88, 7.32),
             ("yang", 7.38, 7.58), ("single-single", 7.58, 8.12), ("tu", 8.12, 8.28), ("peluk", 8.28, 8.46),
             ("apa?", 8.46, 8.72)),
    11.90: _w(("durian", 12.02, 12.32), ("yang", 12.32, 12.52), ("gebu-gebas", 12.52, 13.08),
              ("macam", 13.08, 13.34), ("ni.", 13.34, 13.72)),
    17.46: _w(("95CM,", 17.50, 18.42), ("gebu-gebas,", 18.52, 19.40), ("tebal", 19.62, 19.88)),
    33.20: _w(("Saiz", 33.22, 33.52), ("yang", 33.52, 33.68), ("lebih", 33.68, 33.88), ("kecil,", 33.88, 34.28)),
    42.04: _w(("Boleh", 42.10, 42.24), ("tengok", 42.24, 42.54), ("ni.", 42.54, 42.94), ("Ambik", 43.22, 43.50),
              ("nak", 43.50, 43.68), ("saiz", 43.68, 43.90), ("mana", 43.90, 44.06), ("satu,", 44.06, 44.34),
              ("pilihlah.", 44.62, 44.94)),
    46.45: _w(("Lembut,", 46.66, 47.02), ("gebu,", 47.26, 47.56), ("fluffy.", 47.96, 48.60)),
}
DROP = []
KEYWORDS = {"PELUK", "SUAMI", "SINGLE-SINGLE", "BANTAL", "DURIAN", "GEBU-GEBAS", "SAIZ", "BESAR", "95CM",
            "TEBAL", "SELESA", "75CM", "KECIL", "52CM", "30CM", "COMELNYA", "TENGOK", "PILIHLAH", "EMPAT-EMPAT",
            "LEMBUT", "GEBU", "FLUFFY", "TEMAN", "TIDUR"}

# ---------------------------------------------------------------- per-block layout (subject avoidance)
# Measured on gridded key frames (fractions of the frame): her face sits at y 0.20-0.42 and the pillows fill
# x 0.02-0.95, y 0.18-0.85. Free space: the trees above her head (y 0.09-0.17) and the robe / pillow ends just
# above the TikTok caption area (y 0.71-0.77). Labels go top, captions bottom, unless a block says otherwise.
#   label: "top" (centred in the top band) | "topleft" (top band, left of her head)
#   cap_y: caption centre in px
LAB_Y, CAP_Y = 258, 1410
LAYOUT = {
    "s52": dict(label="topleft"),                  # 35-36s close-up: her face is in the top band, centre
}
# finer overrides by source time range (inside one block)
LAYOUT_RANGES = [
    ((38.02, 40.72), dict(cap_y=1180)),             # extreme close-ups: big smiley at y~0.80, plain yellow at 0.6
    ((40.72, 41.74), dict(label="topleft")),        # back to the medium shot: her head is centre-top again
]

# subject boxes per block for the check sheet: head box + pillow smiley points (fractions of the frame)
SUBJECT = {
    "hook": dict(head=(0.35, 0.17, 0.63, 0.34), faces=[(0.22, 0.30), (0.30, 0.46), (0.33, 0.65), (0.63, 0.37),
                                                       (0.55, 0.48), (0.52, 0.62)]),
    "suami": dict(head=(0.36, 0.18, 0.62, 0.34), faces=[(0.22, 0.31), (0.30, 0.48), (0.31, 0.66), (0.66, 0.40),
                                                        (0.60, 0.50), (0.58, 0.62)]),
    "single": dict(head=(0.38, 0.17, 0.66, 0.33), faces=[(0.25, 0.30), (0.33, 0.55), (0.34, 0.70), (0.66, 0.40),
                                                         (0.62, 0.54), (0.60, 0.66)]),
    "durian": dict(head=(0.40, 0.25, 0.62, 0.40), faces=[(0.33, 0.40), (0.36, 0.56), (0.35, 0.70), (0.72, 0.45),
                                                         (0.66, 0.55), (0.64, 0.66)]),
    "saiz": dict(head=(0.42, 0.25, 0.62, 0.42), faces=[(0.32, 0.38), (0.28, 0.55), (0.30, 0.72), (0.70, 0.50),
                                                       (0.66, 0.62)]),
    "s95": dict(head=(0.40, 0.19, 0.60, 0.32), faces=[(0.72, 0.34), (0.68, 0.48)]),
    "s75": dict(head=(0.36, 0.10, 0.62, 0.28), faces=[(0.10, 0.20), (0.12, 0.42), (0.14, 0.60), (0.60, 0.33),
                                                      (0.58, 0.56)]),
    "kecil": dict(head=(0.38, 0.18, 0.64, 0.34), faces=[(0.32, 0.32), (0.31, 0.47), (0.31, 0.62), (0.73, 0.43),
                                                        (0.70, 0.54), (0.68, 0.66)]),
    "bawa": dict(head=(0.42, 0.22, 0.62, 0.36), faces=[(0.25, 0.70), (0.30, 0.82)]),
    "s52": dict(head=(0.40, 0.06, 0.64, 0.24), faces=[(0.40, 0.48), (0.30, 0.65), (0.66, 0.24), (0.72, 0.42),
                                                      (0.70, 0.58)]),
    "comel": dict(head=(0.82, 0.00, 1.00, 0.14), faces=[(0.32, 0.22), (0.35, 0.40), (0.62, 0.40), (0.48, 0.80)]),
    "pilih": dict(head=(0.36, 0.20, 0.62, 0.36), faces=[(0.22, 0.38), (0.26, 0.52), (0.62, 0.48), (0.68, 0.60),
                                                        (0.64, 0.74)]),
    "end": dict(head=(0.40, 0.20, 0.62, 0.34), faces=[(0.22, 0.40), (0.62, 0.48), (0.66, 0.62)]),
}


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


def layout_at(t):
    lay = dict(LAYOUT.get(block_at(t), {}))
    for (s0, s1), extra in LAYOUT_RANGES:
        if tl(s0) - 1e-6 <= t < tl(s1):
            lay.update(extra)
    return lay


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
        if cur and (len(cur) >= 3 or w["s"] - cur[-1]["e"] > 0.35 or w["clip"] != cur[-1]["clip"]
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
        lay = layout_at(ch[0]["s"])
        out.append(dict(t0=ch[0]["s"], t1=end, y=lay.get("cap_y", CAP_Y),
                        words=[dict(w=x["w"].upper().strip(",."), s=x["s"], e=x["e"],
                                    key=x["w"].upper().strip(",.?!") in KEYWORDS) for x in ch]))
    return out


# ---------------------------------------------------------------- graphics (data for comp/index.html)
def graphics():
    labels, wipes, tags, sfx = [], [], [], []

    def lab(s0, s1, text, emoji="", sound="jelly", vol=0.5, src=True, kind="pill", big=False):
        t0, t1 = (tl(s0), tl(s1)) if src else (s0, s1)
        place = layout_at(t0 + 0.01).get("label", "top")
        labels.append(dict(t0=t0, t1=t1, html=text, emoji=emoji, place=place, kind=kind, big=big))
        if sound:
            sfx.append((sound, t0 - 0.03, vol))

    def wipe(block, sound="whoosh", vol=0.4):
        t = BT[block]["t0"]
        wipes.append(dict(t=t))
        sfx.append((sound, t - 0.25, vol))

    # hook: the question itself is the hook, so it gets the big treatment
    lab(0.62, 3.30, "TIDUR PELUK <b>APA?</b>", "🤔", sound="sparkle", vol=0.45, big=True)
    lab(4.70, 5.44, "ADA <b>SUAMI?</b>", "💑")
    lab(5.46, 6.22, "PELUK <b>SUAMI!</b>", "🤭", sound="pop")
    lab(7.36, 8.74, "YANG <b>SINGLE?</b>", "🙋‍♀️", sound="pop")
    wipe("durian")
    lab(10.50, 13.72, "BANTAL PELUK <b>DURIAN</b>", "💛", sound="sparkle", vol=0.45, big=True)
    lab(13.92, 15.10, "MACAM-MACAM <b>SAIZ</b>", "📏")
    lab(15.12, 16.38, "PALING <b>BESAR!</b>", "💪", sound="pop")
    lab(17.52, 19.60, "<b>95</b>CM", "😱", sound="impact", vol=0.35, big=True)
    lab(19.66, 21.74, "TEBAL & <b>SELESA</b>", "☁️")
    lab(22.08, 23.30, "YANG NI PUN <b>BESAR</b>", "🤗")
    lab(23.32, 24.80, "<b>75</b>CM", "💛", sound="impact", vol=0.3, big=True)
    wipe("kecil")
    lab(27.80, 30.38, "SAIZ <b>KECIL</b> PUN ADA", "🐣")
    tags.append(dict(t0=BT["bawa"]["t0"], t1=BT["bawa"]["t0"] + BT["bawa"]["dur"], text=">> x1.5"))
    sfx.append(("swish", BT["bawa"]["t0"] - 0.05, 0.4))
    lab(33.22, 34.30, "LEBIH <b>KECIL</b>", "🤏")
    lab(34.62, 35.50, "<b>52</b>CM", "✨", sound="impact", vol=0.3, big=True)
    lab(35.90, 37.68, "<b>30</b>CM", "🥹", sound="impact", vol=0.3, big=True)
    wipe("comel", sound="swish", vol=0.35)
    lab(38.06, 40.70, "YA RABBI, <b>COMELNYA!</b>", "🥰", sound="sparkle", vol=0.4)
    lab(40.76, 41.72, "YANG MANA <b>BELUM</b> <b>ADA?</b>", "👀", sound="pop")
    lab(42.10, 42.94, "TENGOK <b>NI!</b>", "👇", sound="pop")
    lab(43.20, 44.94, "PILIH SAIZ <b>MANA?</b>", "🤔")
    lab(45.00, 46.40, "ADA <b>4</b> <b>SAIZ!</b>", "📏", sound="ding", vol=0.35)
    lab(46.62, 48.86, "LEMBUT • GEBU • <b>FLUFFY</b>", "☁️")
    lab(48.96, 49.92, "TEMAN <b>TIDUR</b>", "😴", sound="pop")
    end = dict(t0=BT["end"]["t0"] - 0.1, t1=TOTAL)
    sfx.append(("ding", end["t0"], 0.4))
    sfx.append(("sparkle", end["t0"] + 0.3, 0.3))
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
                safe=dict(l=SAFE_L, r=CW - SAFE_R, t=SAFE_T, b=CH - SAFE_B), lab_y=LAB_Y,
                captions=caption_chunks(words), labels=labels, wipes=wipes, tags=tags, end=end,
                blocks=[dict(name=b["name"], t0=b["t0"], dur=b["dur"]) for b in BLOCKS])
    with open(os.path.join(OUT, "edl.json"), "w") as f:
        json.dump(dict(data, sfx=sfx, subject=SUBJECT, layout=LAYOUT,
                       vblocks=[{k: b[k] for k in ("name", "t0", "dur", "v", "a")} for b in BLOCKS]),
                  f, ensure_ascii=False, indent=1)
    print(f"timeline {TOTAL:.2f}s, {len(VCLIPS)} clips, {len(labels)} labels, {len(sfx)} sfx")
    if "--no-render" in sys.argv:
        sys.exit(0)
    if "--graphics-only" not in sys.argv:      # --graphics-only: reuse out/base.mp4, re-render the overlay layer
        render_base(sfx)
    write_comp(data)
    render_hyperframes()
