#!/usr/bin/env python3
"""Edit for kusyen duduk (red + beige tufted waffle seat cushions), video 5 of 5 (IMG_3070), "Hygge kait hangat"
look. Hook: her own opening call-out ("Kalau korang nampak kosong, tak ada peneman kat sofa, ambil bantal ni jadi
peneman sofa kita."), kept first. The graphics layer is a HyperFrames (HTML + GSAP) composition: small oatmeal tags
with a cable-knit border and a wool pompom, Fraunces (a soft warm serif), a candle glow behind the hook tag, a
stitched underline drawing in under the spoken caption word, a warm edge-only vignette glow between sections, a
yarn progress line with a rolling yarn ball and a compact knit end card. Slow, warm easing.
User rule for this series: keep the CENTRE of the frame (x 160-920, y 480-1340) free of text and animation;
few, compact labels only in the top band / the lower band above the captions; no full-screen wipes.

Pipeline (all times in BLOCKS are source times of the original clip, same timeline as the proxy):
  1. base.mp4      - cut/zoomed video + cleaned voice (v2 chain, -11.5 LUFS) + soft music bed + SFX   (ffmpeg)
  2. comp/data.js  - captions, labels, edge glows, end card + her head boxes for each of them (this script)
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
# One 37.7s handheld clip under a carport: a face close-up while she asks the question (0-4s), then she lowers the
# phone and holds a red and a beige tufted waffle cushion. No price talk. Her face is covered by the niqab, so J-cuts
# never show a lip mismatch. Her opening line is already the hook (an empty-sofa call-out), so it stays first and
# the whole video plays on the "peneman sofa" idea. Dropped: the 1.1s pause after "sofa,", "Okey," (7.40), the filler
# "kan?" (10.74), "Yang" + its pause (14.1-14.5), the trailing "kan?" (26.4),
# "Ha," (26.6), the unclear "takkan nak kena teman pula sofa korang tu" (28.8-31.8) and "atau komennya?" (33.9),
# and pauses. Cut points sit in envelope dips (outdoor wind noise sits around -22 dB between words).
# v: list of (src_in, src_out, speed, zoom); a: 'same' (follow v at 1x), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK: "Kalau korang nampak kosong, tak ada peneman kat sofa, | ambil bantal ni jadi peneman sofa kita."
    # (face close-up, then she lowers the phone and the cushions come in on "ambil bantal ni")
    dict(name="hook", a="same", v=[(0.00, 3.18, 1, 1.0), (4.24, 7.32, 1, 1.0)]),
    # "Teman macam mana? Letaklah bagi dia duduk kat situ. | Jadi kita boleh duduk atas dia."
    dict(name="teman", a="same", v=[(7.66, 10.68, 1, 1.0), (11.27, 12.70, 1, 1.05)]),
    # "Ni memang selesa, lembut, saiz dia 40cm x 40cm."
    dict(name="selesa", a="same", v=[(14.56, 18.10, 1, 1.0)]),
    # "Material dia pun jenis yang waffle, material jenis comel-comel berkotak-kotak kecil macam ni, cantik." (red
    # cushion brought up to the lens: the waffle texture fills the frame). Kept whole: trimming the repeated
    # "material jenis" made "waffle, comel-comel" run together and read as "macam-macam".
    dict(name="waffle", a="same", v=[(18.10, 24.20, 1, 1.0)]),
    # "Dan boleh basuh juga."
    dict(name="basuh", a="same", v=[(24.20, 26.28, 1, 1.0)]),
    # "Ni buat teman kat sofa."
    dict(name="sofa", a="same", v=[(27.38, 28.68, 1, 1.0)]),
    # CTA: "Tengok kat bawah sekarang."
    dict(name="cta", a="same", v=[(35.42, 36.88, 1, 1.0)]),
    # knit end card over both cushions held up (head right, low in the top band), slowed a little, no voice
    dict(name="end", a=None, v=[(31.00, 33.20, 0.75, 1.0)]),
]

FIX = {"bantai": "bantal", "tahu": "tau", "kala": "kaler", "x": "×", "size": "saiz", "saj": "saiz"}


def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


# hand-checked words (per-chunk re-transcription + the loudness envelope)
OVERRIDE = {
    0.00: _w(("Kalau", 0.02, 0.14), ("korang", 0.14, 0.40), ("nampak", 0.40, 0.74), ("kosong,", 0.74, 1.46),
             ("tak", 1.56, 1.72), ("ada", 1.72, 1.86), ("peneman", 1.86, 2.34), ("kat", 2.34, 2.66), ("sofa,", 2.66, 3.10)),
    4.24: _w(("ambil", 4.26, 4.54), ("bantal", 4.54, 4.94), ("ni", 4.94, 5.12), ("jadi", 5.12, 5.34),
             ("peneman", 5.34, 6.26), ("sofa", 6.26, 6.76), ("kita.", 6.76, 7.24)),
    7.66: _w(("Teman", 7.70, 7.94), ("macam", 7.94, 8.10), ("mana?", 8.10, 8.38), ("Letaklah", 8.52, 8.90),
             ("bagi", 8.90, 9.12), ("dia", 9.12, 9.44), ("duduk", 9.44, 9.78), ("kat", 9.78, 9.96), ("situ.", 9.96, 10.60)),
    11.27: _w(("Jadi", 11.30, 11.48), ("kita", 11.48, 11.68), ("boleh", 11.68, 11.84), ("duduk", 11.84, 12.22),
              ("atas", 12.22, 12.44), ("dia.", 12.44, 12.66)),
    14.56: _w(("Ni", 14.62, 14.82), ("memang", 14.82, 15.10), ("selesa,", 15.10, 15.72), ("lembut,", 15.92, 16.40),
              ("saiz", 16.50, 16.66), ("dia", 16.66, 16.86), ("40cm × 40cm.", 16.86, 17.98)),
    18.10: _w(("Material", 18.20, 18.68), ("dia", 18.68, 18.86), ("pun", 18.86, 19.14), ("jenis", 19.14, 19.74),
              ("yang", 19.74, 20.10), ("waffle,", 20.10, 20.56), ("material", 20.80, 20.96), ("jenis", 20.96, 21.30),
              ("comel-comel", 21.32, 21.84), ("berkotak-kotak", 21.84, 22.60), ("kecil", 22.60, 22.88),
              ("macam", 22.88, 23.10), ("ni,", 23.10, 23.62), ("cantik.", 23.66, 24.15)),
    24.20: _w(("Dan", 24.24, 24.58), ("boleh", 24.58, 24.80), ("basuh", 24.80, 25.30), ("juga.", 25.30, 25.96)),
    27.38: _w(("Ni", 27.42, 27.66), ("buat", 27.66, 27.78), ("teman", 27.78, 28.04), ("kat", 28.04, 28.20),
              ("sofa.", 28.20, 28.58)),
    35.42: _w(("Tengok", 35.46, 35.86), ("kat", 35.86, 36.02), ("bawah", 36.02, 36.24), ("sekarang.", 36.24, 36.80)),
}
DROP = []
BREAK_BEFORE = {1.56, 5.12, 8.52, 9.44, 11.84, 16.50, 19.14, 20.80, 21.84}   # forced caption chunk starts (source times)
KEYWORDS = {"KOSONG", "PENEMAN", "SOFA", "BANTAL", "TEMAN", "DUDUK", "SELESA", "LEMBUT", "40CM × 40CM", "WAFFLE",
            "BERKOTAK-KOTAK", "CANTIK", "BASUH", "BAWAH"}

# ---------------------------------------------------------------- her head (face avoidance)
# Head + hijab box (incl. the niqab) from gridded proxy frames every 1s (fractions of the source frame, x0, y0, x1,
# y1). edit.py turns these into px boxes (zoom applied) for each graphic's time window; the composition keeps
# every graphic HEAD_MARGIN px clear of all of them. Checked by drawing them on the frames (work dir headcheck.jpg).
# 0-3s: face close-up (the head fills the upper two thirds). 23-25s: the red cushion fills the frame and only the
# bottom of her face shows at the top edge.
HEADS = [
    (0, (0.15, 0.10, 0.80, 0.65)), (1, (0.15, 0.12, 0.80, 0.65)), (2, (0.20, 0.10, 0.82, 0.62)),
    (3, (0.20, 0.08, 0.82, 0.62)), (4, (0.30, 0.30, 0.84, 0.72)), (5, (0.36, 0.36, 0.66, 0.62)),
    (6, (0.38, 0.24, 0.68, 0.50)), (7, (0.40, 0.20, 0.72, 0.45)), (8, (0.30, 0.20, 0.58, 0.42)),
    (9, (0.28, 0.00, 0.58, 0.40)), (10, (0.35, 0.06, 0.66, 0.38)), (11, (0.35, 0.13, 0.66, 0.40)),
    (12, (0.33, 0.18, 0.63, 0.42)), (13, (0.32, 0.18, 0.62, 0.42)), (14, (0.22, 0.10, 0.55, 0.40)),
    (15, (0.15, 0.08, 0.55, 0.42)), (16, (0.10, 0.06, 0.48, 0.42)), (17, (0.38, 0.10, 0.78, 0.45)),
    (18, (0.35, 0.12, 0.68, 0.42)), (19, (0.28, 0.12, 0.60, 0.40)), (20, (0.28, 0.12, 0.60, 0.40)),
    (21, (0.36, 0.08, 0.68, 0.38)), (22, (0.30, 0.00, 0.72, 0.32)), (23, (0.30, 0.00, 0.82, 0.20)),
    (24, (0.40, 0.00, 0.85, 0.15)), (25, (0.30, 0.00, 0.80, 0.18)), (26, (0.33, 0.02, 0.65, 0.32)),
    (27, (0.43, 0.16, 0.74, 0.42)), (28, (0.36, 0.18, 0.68, 0.44)), (29, (0.36, 0.22, 0.64, 0.46)),
    (30, (0.38, 0.20, 0.68, 0.46)), (31, (0.43, 0.16, 0.74, 0.40)), (32, (0.50, 0.13, 0.84, 0.40)),
    (33, (0.50, 0.08, 0.88, 0.38)), (34, (0.40, 0.10, 0.80, 0.38)), (35, (0.28, 0.12, 0.78, 0.47)),
    (36, (0.28, 0.20, 0.70, 0.50)), (37, (0.36, 0.13, 0.72, 0.45)),
]
FACES = []              # the cushions have no face
HEAD_PAD = 0.55         # samples are 1s apart: look a little further either side
# preferred centres (px): tags in the top band, small tags just above the captions, captions low
TOP_Y, LOW_Y, CAP_Y = 290, 1366, 1440
# centre keep-out (user rule: "kurangkan text dan animation bahagian tengah video")
KEEP_OUT = (160, 480, 920, 1340)
MUSIC_VOL, MUSIC_DUCK = 0.32, 0.06   # music.wav gain alone / under her voice (she talks almost all the time)

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
    """Few, compact labels (user rule): a candle-glow knit tag for the hook, a tag each for "peneman sofa", the joke,
    the size, the waffle fabric and "boleh basuh"; a warm edge-only vignette glow between sections; a compact knit
    end card with the CTA.
    Nothing is drawn in the centre KEEP_OUT box."""
    labels, turns, sfx = [], [], []

    def lab(t0, t1, style, sound="knit", vol=0.34, low=False, **kw):
        """style 'candle': hook tag with a candle glow; style 'tag': small knit tag (top band unless low=True)."""
        py = LOW_Y if low else TOP_Y
        labels.append(dict(t0=t0, t1=t1, style=style, py=py, heads=heads_for(t0, t1), faces=faces_for(t0, t1), **kw))
        if sound:
            sfx.append((sound, t0 - 0.03, vol))

    def turn(block, sound="crackle", vol=0.30):
        t = BT[block]["t0"]
        turns.append(dict(t=t))
        sfx.append((sound, t - 0.15, vol))

    # hook: "Kalau korang nampak kosong, tak ada peneman kat sofa," (face close-up: the tag sits under her chin,
    # the placer keeps it clear of the head box)
    lab(0.15, tl(3.10), "candle", html="Sofa nampak <u>kosong</u>?", emoji="🛋️", sound="chime", vol=0.30, koPad=70)
    # "ambil bantal ni jadi peneman sofa kita."
    lab(tl(5.30) - 0.05, tl(7.24) + 0.15, "tag", html="Jadi <u>peneman sofa</u>", emoji="🤎")
    # "Jadi kita boleh duduk atas dia."
    lab(tl(11.30) - 0.05, BT["teman"]["t0"] + BT["teman"]["dur"] - 0.04, "tag", html="Duduk <u>atas dia</u>", emoji="😆")
    turn("selesa")
    # "saiz dia 40cm x 40cm."
    lab(tl(16.86) - 0.05, BT["selesa"]["t0"] + BT["selesa"]["dur"] - 0.04, "tag", html="<u>40 × 40</u> cm", emoji="📏",
        vol=0.30)
    # "Material dia pun jenis yang waffle, ... berkotak-kotak kecil"
    lab(tl(20.10) - 0.05, tl(22.88), "tag", html="Kain <u>waffle</u>", emoji="🧇")
    # "Dan boleh basuh juga."
    lab(tl(24.80) - 0.05, BT["basuh"]["t0"] + BT["basuh"]["dur"] - 0.04, "tag", html="Boleh <u>basuh</u>", emoji="🫧")
    turn("sofa")
    # CTA "Tengok kat bawah sekarang." is carried by the caption and the end card (no extra tag: fewer labels)
    e0 = BT["end"]["t0"]
    end = dict(t0=e0, t1=TOTAL, title="Peneman sofa", sub="kusyen duduk 40 × 40", rows=["Merah", "Beige"],
               cta="Tekan beg kuning 🛒", heads=heads_for(e0, TOTAL), faces=faces_for(e0, TOTAL))
    sfx.append(("chime", e0 - 0.05, 0.28))
    sfx.append(("knit", e0 + 0.6, 0.28))
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
