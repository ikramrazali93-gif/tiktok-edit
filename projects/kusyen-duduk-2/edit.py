#!/usr/bin/env python3
"""Edit for kusyen duduk (red + beige tufted seat cushions), video 2 of 5 (IMG_3067), "Majalah hiasan rumah"
look. Hook: her call-out to mums and pregnant mums who can't sit long, moved to the front. The graphics layer is a
HyperFrames (HTML + GSAP) composition: interior-magazine headlines (Playfair Display), issue kickers, thin rules,
photo-caption lines, corner crop marks, off-white / charcoal with the cushion red as accent.
New user rule for this series: keep the CENTRE of the frame (x 160-920, y 480-1340) free of text and animation;
few, compact labels only in the top band / the lower band above the captions; no full-screen wipes.

Pipeline (all times in BLOCKS are source times of the original clip, same timeline as the proxy):
  1. base.mp4      - cut/zoomed video + cleaned voice (v2 chain, -11.5 LUFS) + soft music bed + SFX   (ffmpeg)
  2. comp/data.js  - captions, labels, page-turn accents, end card + her head boxes for each of them (this script)
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
# One 40.4s handheld shot on a dirt road: she holds a beige and a red tufted seat cushion and talks the whole
# time (no price talk in this clip). Her face is covered by the niqab, so J-cuts never show a lip mismatch.
# The hook moves her call-out to the front: "Mak-mak korang yang mana tak boleh duduk lama, ataupun mami-mami
# pregnant tak boleh duduk lama tu, korang kena ada satu bantal macam ni." It plays over three shots whose
# head is low in frame (so the top band stays free for the first headline).
# v: list of (src_in, src_out, speed, zoom); a: 'same' (follow v at 1x), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK: audio 31.66-37.78 over the wide two-cushion shot, a closer shot of the beige one, then the real
    # moment (she swings both cushions on "korang kena ada satu bantal macam ni")
    dict(name="hook", a=[(31.66, 37.78)], v=[(8.40, 10.45, 1, 1.0), (26.75, 28.82, 1, 1.06), (35.78, 37.78, 1, 1.0)]),
    # "Tak sangka bantal ni boleh buat kita lebih selesa dekat dalam kereta. | Yang mana drive lama-lama."
    dict(name="kereta", a="same", v=[(0.40, 5.70, 1, 1.0), (5.70, 8.38, 1, 1.07)]),
    # "Selesa. | Sebab korang tengok dia punya ketebalan memang lembut. Memang selesa."  (she squeezes them)
    dict(name="tebal", a="same", v=[(11.28, 12.28, 1, 1.0), (12.28, 16.20, 1, 1.08)]),
    # "Saiz dia pun 40cm x 40cm | ni ngam elok dengan seat driver tu."
    dict(name="saiz", a="same", v=[(16.52, 18.46, 1, 1.0), (18.46, 20.86, 1, 1.06)]),
    # "Kalau korang ada satu macam ni, | lebih selesa dan boleh buat korang tersenyum."
    dict(name="senyum", a="same", v=[(21.72, 23.32, 1, 1.0), (23.32, 26.66, 1, 1.07)]),
    # CTA: "Tengok dekat bawah sekarang."
    dict(name="cta", a="same", v=[(38.50, 39.82, 1, 1.0)]),
    # magazine-cover end card over her waving with the beige cushion (muted: "orang kata boleh duduk lama")
    dict(name="end", a=None, v=[(29.10, 31.62, 1, 1.0)]),
]

FIX = {"bantai": "bantal", "tahu": "tau", "airlock": "elok", "ingam": "ngam", "x": "×", "size": "saiz"}


def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


# hand-checked words (per-chunk re-transcription + the loudness envelope)
OVERRIDE = {
    31.66: _w(("Mak-mak", 31.72, 32.08), ("korang", 32.08, 32.52), ("yang", 32.52, 32.64), ("mana", 32.64, 32.92),
              ("tak", 32.92, 33.08), ("boleh", 33.08, 33.20), ("duduk", 33.20, 33.46), ("lama,", 33.46, 33.84),
              ("ataupun", 34.10, 34.30), ("mami-mami", 34.30, 34.76), ("pregnant", 34.76, 35.02), ("tak", 35.02, 35.18),
              ("boleh", 35.18, 35.28), ("duduk", 35.28, 35.46), ("lama", 35.46, 35.70), ("tu.", 35.70, 35.86),
              ("Korang", 36.08, 36.32), ("kena", 36.32, 36.56), ("ada", 36.56, 36.76), ("satu", 36.76, 37.00),
              ("bantal", 37.00, 37.26), ("macam", 37.26, 37.44), ("ni.", 37.44, 37.62)),
    0.40: _w(("Tak", 0.45, 0.66), ("sangka", 0.66, 0.98), ("bantal", 0.98, 1.48), ("ni", 1.48, 2.14),
             ("boleh", 2.14, 2.52), ("buat", 2.52, 2.74), ("kita", 2.74, 3.08), ("lebih", 3.08, 3.64),
             ("selesa", 3.64, 4.16), ("dekat", 4.16, 4.44), ("dalam", 4.44, 4.62), ("kereta.", 4.62, 5.62)),
    5.70: _w(("Yang", 5.76, 6.30), ("mana", 6.36, 6.64), ("drive", 6.64, 7.18), ("lama-lama.", 7.32, 8.16)),
    11.28: _w(("Selesa.", 11.32, 12.12)),
    12.28: _w(("Sebab", 12.35, 12.49), ("korang", 12.49, 12.69), ("tengok", 12.69, 13.01), ("dia", 13.01, 13.13),
              ("punya", 13.13, 13.27), ("ketebalan", 13.27, 13.75), ("memang", 13.75, 14.11), ("lembut.", 14.11, 14.80),
              ("Memang", 15.22, 15.55), ("selesa.", 15.55, 16.09)),
    16.52: _w(("Saiz", 16.58, 16.88), ("dia", 16.88, 17.04), ("pun", 17.04, 17.40), ("40cm", 17.40, 17.82),
              ("×", 17.82, 18.00), ("40cm", 18.00, 18.44)),
    18.46: _w(("ni", 18.48, 18.76), ("ngam", 18.76, 18.94), ("elok", 18.94, 19.40), ("dengan", 19.40, 19.80),
              ("seat", 19.80, 20.08), ("driver", 20.08, 20.62), ("tu.", 20.62, 20.82)),
    21.72: _w(("Kalau", 21.74, 21.90), ("korang", 21.90, 22.00), ("ada", 22.00, 22.20), ("satu", 22.20, 22.52),
              ("macam", 22.52, 22.80), ("ni,", 22.80, 23.30)),
    23.32: _w(("lebih", 23.34, 23.74), ("selesa", 23.74, 24.44), ("dan", 24.44, 24.74), ("boleh", 24.74, 24.94),
              ("buat", 24.94, 25.18), ("korang", 25.18, 25.52), ("tersenyum.", 25.52, 26.40)),
    38.50: _w(("Tengok", 38.55, 38.96), ("dekat", 38.96, 39.14), ("bawah", 39.14, 39.28), ("sekarang.", 39.34, 39.78)),
}
DROP = []
BREAK_BEFORE = {32.92, 34.10, 35.02, 37.00, 2.14, 4.16, 13.27, 17.40, 19.80, 22.20, 24.74}   # forced caption chunk starts (source times)
KEYWORDS = {"MAK-MAK", "MAMI-MAMI", "PREGNANT", "DUDUK", "LAMA", "LAMA,", "KERETA", "DRIVE", "SELESA", "KETEBALAN",
            "LEMBUT", "40CM", "SEAT", "DRIVER", "TERSENYUM", "BAWAH", "BANTAL"}

# ---------------------------------------------------------------- her head (face avoidance)
# Head + hood box (incl. the niqab) from gridded proxy frames every 1s (fractions of the source frame, x0, y0, x1,
# y1). edit.py turns these into px boxes (zoom applied) for each graphic's time window; the composition keeps
# every graphic HEAD_MARGIN px clear of all of them. Checked by drawing them on the frames (work dir headcheck.jpg).
HEADS = [
    (0, (0.36, 0.20, 0.70, 0.47)), (1, (0.38, 0.18, 0.70, 0.45)), (2, (0.40, 0.17, 0.72, 0.45)),
    (3, (0.40, 0.19, 0.72, 0.47)), (4, (0.40, 0.20, 0.72, 0.47)), (5, (0.40, 0.19, 0.72, 0.45)),
    (6, (0.40, 0.19, 0.72, 0.45)), (7, (0.46, 0.16, 0.86, 0.45)), (8, (0.27, 0.16, 0.63, 0.45)),
    (9, (0.27, 0.16, 0.63, 0.45)), (10, (0.29, 0.18, 0.63, 0.45)), (11, (0.24, 0.16, 0.61, 0.45)),
    (12, (0.31, 0.16, 0.67, 0.45)), (13, (0.17, 0.03, 0.67, 0.45)), (14, (0.17, 0.01, 0.67, 0.42)),
    (15, (0.19, 0.00, 0.67, 0.40)), (16, (0.12, 0.00, 0.62, 0.40)), (17, (0.24, 0.00, 0.71, 0.40)),
    (18, (0.29, 0.03, 0.66, 0.42)), (19, (0.31, 0.09, 0.66, 0.45)), (20, (0.29, 0.16, 0.63, 0.45)),
    (21, (0.39, 0.20, 0.78, 0.47)), (22, (0.41, 0.18, 0.82, 0.45)), (23, (0.41, 0.15, 0.80, 0.45)),
    (24, (0.39, 0.11, 0.76, 0.40)), (25, (0.33, 0.08, 0.76, 0.40)), (26, (0.29, 0.06, 0.76, 0.40)),
    (27, (0.29, 0.06, 0.76, 0.40)), (28, (0.29, 0.11, 0.73, 0.42)), (29, (0.27, 0.16, 0.71, 0.45)),
    (30, (0.29, 0.17, 0.71, 0.47)), (31, (0.31, 0.17, 0.71, 0.47)), (32, (0.31, 0.17, 0.71, 0.47)),
    (33, (0.31, 0.17, 0.71, 0.47)), (34, (0.34, 0.16, 0.73, 0.47)), (35, (0.31, 0.15, 0.71, 0.45)),
    (36, (0.29, 0.15, 0.71, 0.45)), (37, (0.27, 0.14, 0.69, 0.45)), (38, (0.37, 0.11, 0.76, 0.45)),
    (39, (0.37, 0.13, 0.76, 0.45)), (40, (0.19, 0.10, 0.66, 0.45)),
]
FACES = []              # the cushions have no face
HEAD_PAD = 0.8          # samples are 1s apart: look a little further either side
# preferred centres (px): headlines in the top band, photo-caption lines just above the captions, captions low
TOP_Y, LOW_Y, CAP_Y = 250, 1368, 1440
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
        end = min(end, BT["end"]["t0"])        # never under the end card
        out.append(dict(t0=ch[0]["s"], t1=end, y=CAP_Y, heads=heads_for(ch[0]["s"], end), faces=faces_for(ch[0]["s"], end),
                        words=[dict(w=x["w"].strip(",."), s=x["s"], e=x["e"],
                                    key=x["w"].upper().strip(",.?!") in KEYWORDS) for x in ch]))
    return out


# ---------------------------------------------------------------- graphics (data for comp/index.html)
def graphics():
    """Few, compact labels (user rule): 2 magazine headlines in the top band and 5 photo-caption lines just above
    the captions. Nothing is drawn in the centre KEEP_OUT box; turns are edge-only accents + a light flash."""
    labels, turns, sfx = [], [], []

    def lab(t0, t1, text, kick="", style="head", emoji="", sound="click", vol=0.32, block=None):
        """style 'head': kicker + Playfair headline, prefers the top band.
        style 'line': one slim photo-caption line (rule + caps), prefers the lower band above the captions."""
        if block:
            t0, t1 = BT[block]["t0"] + t0, BT[block]["t0"] + t1
        labels.append(dict(t0=t0, t1=t1, html=text, kick=kick, emoji=emoji, style=style,
                           py=TOP_Y if style == "head" else LOW_Y,
                           heads=heads_for(t0, t1), faces=faces_for(t0, t1)))
        if sound:
            sfx.append((sound, t0 - 0.03, vol))

    def turn(block, sound="page", vol=0.30):
        t = BT[block]["t0"]
        turns.append(dict(t=t, folio=f"{len(turns) + 2:02d}"))
        sfx.append((sound, t - 0.12, vol))

    hk = BT["hook"]
    # hook: "Mak-mak korang yang mana tak boleh duduk lama, | ataupun mami-mami pregnant ..."
    lab(0.05, BT["hook"]["v"][0][1] - BT["hook"]["v"][0][0] - 0.08, "Tak boleh <i>duduk lama?</i>",
        "Edisi 02 — Ruang duduk", sound="ding", vol=0.24, block="hook")
    lab(tl(34.10) - 0.05, tl(35.86) + 0.15, "Untuk mak &amp; ibu mengandung", style="line", sound="click")
    # "... boleh buat kita lebih selesa dekat dalam kereta. Yang mana drive lama-lama."
    lab(tl(3.08) - 0.05, tl(5.62) + 0.3, "Selesa <i>dalam kereta</i>", "Perjalanan jauh", sound="ding", vol=0.2)
    turn("tebal")
    lab(tl(13.27) - 0.05, tl(14.80) + 0.25, "Tebal &amp; lembut", style="line")
    lab(tl(17.40) - 0.05, tl(20.82) + 0.05, "40 × 40 cm · ngam seat driver", style="line")
    turn("senyum")
    lab(tl(25.18) - 0.1, tl(26.40) + 0.2, "Duduk selesa, boleh senyum", style="line", emoji="😊")
    lab(tl(38.55) - 0.08, BT["cta"]["t0"] + BT["cta"]["dur"] - 0.04, "Tengok beg kuning", style="line", emoji="👇",
        sound="ding", vol=0.2)
    e0 = BT["end"]["t0"]
    end = dict(t0=e0, t1=TOTAL, issue="Edisi 02", mast="Kusyen Duduk",
               lines="40 × 40 cm · Merah · Beige", cta="Tekan beg kuning 🛒",
               heads=heads_for(e0, TOTAL), faces=faces_for(e0, TOTAL))
    sfx.append(("shutter", e0 - 0.02, 0.28))
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
