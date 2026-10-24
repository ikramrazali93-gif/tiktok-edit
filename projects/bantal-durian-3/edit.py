#!/usr/bin/env python3
"""Edit for durian hug-pillow video #3 (IMG_3062, "pop komik" look). Graphics layer is a HyperFrames
(HTML + GSAP) composition, like projects/bantal-durian; this one draws comic speech bubbles, halftone starbursts,
ink-box captions and speed-line slams.

Pipeline (all times in BLOCKS are source times of the original clip, same timeline as the proxy):
  1. base.mp4      - cut/zoomed video + cleaned voice (v2 chain, -11.5 LUFS) + SFX       (ffmpeg)
  2. comp/data.js  - captions, labels, bursts, slams, end card with positions per block (this script)
  3. hf.mp4        - comp/index.html rendered by HyperFrames with base.mp4 as its muted video layer
  4. preview.mp4 / final.mp4 - hf.mp4 video + base.mp4 audio (ffmpeg mux; preview is scaled to 720x1280)

Face rule (user: "kurangkan tutup bahagian muka"): every block has a measured head box (SUBJECT) and the
graphics are placed per block so none of them touch it: labels in the top band above her hood or top-left
beside it, captions in the bottom band, and in the face close-up (hook) the captions move up onto the hood.

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
# Opens on a face close-up gag ("Tengok muka ni... Eh bukan, muka ni!" - the pillow's face), then pillow
# close-ups and her hugging one long durian pillow in a garden. The gag is the hook, so the order stays as shot.
# v: list of (src_in, src_out, speed, zoom); a: 'same' (follow v at 1x), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK: "Stop, stop, stop. Tengok ni. Tengok muka ni. Takkanlah muka ni tak boleh buat korang | happy,
    #  tersenyum."  (0.3s pause before "happy" cut, punch-in after it)
    dict(name="hook", a="same", v=[(0.00, 5.10, 1, 1.0), (5.42, 7.45, 1, 1.06)]),
    # "Eh, bukan, bukan. Muka ni, muka ni. Sebelah saya ni."  (the punchline: the pillow's face)
    dict(name="bukan", a="same", v=[(7.38, 8.75, 1, 1.0), (8.75, 10.85, 1, 1.04)]),
    # "Sini ni, senyum ni."  J-cut: her voice from 14.8s over the big smiley close-up at 11.0s
    #  ("Apa close up sampai kita ni. Kita semua close up sini lah." cut: unclear)
    dict(name="senyum", a=[(14.80, 16.08)], v=[(11.00, 12.28, 1, 1.0)]),
    # "Kita pun tersenyum tengok dia."
    dict(name="kita", a="same", v=[(16.55, 18.55, 1, 1.0)]),
    # "Gebu macam ni, | tu ketebalan dia. Ya Allah, ya Rabbi."  (pause cut)
    dict(name="gebu", a="same", v=[(19.30, 20.15, 1, 1.0), (20.85, 23.05, 1, 1.04)]),
    # "Memang tersenyumlah."
    dict(name="memang", a="same", v=[(23.30, 25.00, 1, 1.0)]),
    # "Tengok muka yang comel ni. | Ada tiga muka."  (pause cut)
    dict(name="comel", a="same", v=[(25.00, 26.55, 1, 1.0), (26.85, 27.96, 1, 1.05)]),
    # "Jangan takut, jangan takut."
    dict(name="takut", a="same", v=[(28.22, 29.22, 1, 1.0)]),
    # "Yang ni, durian yang lembut, yang gebu, yang tebal. | Buat peluk, buat teman tiduuur..." (runs into "Ya Allah")
    dict(name="durian", a="same", v=[(29.26, 32.20, 1, 1.0), (32.48, 34.95, 1, 1.05)]),
    # "Ya Allah, sangat-sangat gebu."  (the unclear "fluffy... sangat peluk" after it is cut)
    dict(name="sangat", a="same", v=[(34.95, 36.28, 1, 1.0)]),
    # "Yang ni saiz paling besar. | Saiz 95cm. Panjang, besar macam orang dah."
    dict(name="besar", a="same", v=[(37.60, 38.58, 1, 1.0), (38.95, 41.98, 1, 1.04)]),
    # "Okey, korang tengok dekat beg kuning, silalah grab sebab memang betul-betul gebu."
    dict(name="cta", a="same", v=[(42.60, 44.62, 1, 1.0), (44.62, 46.90, 1, 1.05)]),
    # end card over the slowed last moment
    dict(name="end", a=None, v=[(46.90, 47.75, 0.5, 1.0)]),
]

FIX = {"doyan": "durian", "keterbalan": "ketebalan", "size": "saiz", "Size": "Saiz", "95cm": "95CM",
       "tengah": "tengok", "bad": "beg", "Okay": "Okey"}


def _w(*ws):
    return [dict(w=w, s=s, e=e) for w, s, e in ws]


# hand-checked words where Whisper drifted or misheard (re-transcribed per chunk)
OVERRIDE = {
    0.00: _w(("Tengok", 1.62, 1.86), ("ni.", 1.86, 2.22), ("Tengok", 2.34, 2.58), ("muka", 2.58, 2.78),
             ("ni.", 2.78, 2.95), ("Takkanlah", 3.00, 3.56), ("muka", 3.56, 3.76), ("ni", 3.76, 3.94),
             ("tak", 3.94, 4.12), ("boleh", 4.12, 4.28), ("buat", 4.28, 4.52), ("korang", 4.52, 5.06)),
    5.42: _w(("happy,", 5.45, 5.96), ("tersenyum.", 6.25, 7.05)),
    7.38: _w(("Eh,", 7.40, 7.82), ("bukan,", 7.90, 8.20), ("bukan!", 8.20, 8.70)),
    8.75: _w(("Muka", 8.78, 8.90), ("ni,", 8.90, 8.98), ("muka", 8.98, 9.22), ("ni.", 9.22, 9.60),
             ("Sebelah", 10.12, 10.36), ("saya", 10.36, 10.54), ("ni.", 10.54, 10.80)),
    14.80: _w(("Sini", 14.84, 15.10), ("ni,", 15.10, 15.40), ("senyum", 15.48, 15.86), ("ni.", 15.86, 16.06)),
    19.30: _w(("Gebu", 19.34, 19.70), ("macam", 19.70, 19.96), ("ni,", 19.96, 20.14)),
    20.85: _w(("tu", 20.90, 20.94), ("ketebalan", 20.94, 21.70), ("dia.", 21.70, 21.90), ("Ya", 22.12, 22.16),
              ("Allah,", 22.16, 22.44), ("ya", 22.46, 22.64), ("Rabbi.", 22.64, 23.02)),
    23.30: _w(("Memang", 23.40, 23.76), ("tersenyumlah!", 23.76, 24.98)),
    26.85: _w(("Ada", 26.96, 27.14), ("tiga", 27.14, 27.40), ("muka.", 27.40, 27.94)),
    32.48: _w(("Buat", 32.64, 33.00), ("peluk,", 33.00, 33.40), ("buat", 33.50, 33.58), ("teman", 33.58, 33.84),
              ("tidur...", 33.84, 34.80)),
    34.95: _w(("Ya", 35.02, 35.14), ("Allah,", 35.14, 35.38), ("sangat-sangat", 35.40, 36.04),
              ("gebu.", 36.04, 36.27)),
    38.95: _w(("Saiz", 38.98, 39.20), ("95CM.", 39.20, 40.30), ("Panjang,", 40.50, 41.02), ("besar", 41.02, 41.30),
              ("macam", 41.30, 41.50), ("orang", 41.50, 41.80), ("dah.", 41.80, 41.96)),
    42.60: _w(("Okey,", 42.66, 42.86), ("korang", 42.88, 43.08), ("tengok", 43.10, 43.24), ("dekat", 43.24, 43.44),
              ("beg", 43.44, 43.58), ("kuning,", 43.58, 43.92), ("silalah", 43.94, 44.60)),
    44.62: _w(("grab", 44.66, 45.06), ("sebab", 45.10, 45.36), ("memang", 45.36, 45.92),
              ("betul-betul", 45.96, 46.36), ("gebu.", 46.38, 46.84)),
}
DROP = [(0.0, 1.55)]                    # "Stop, stop, stop." is shown as the big STOP bubble instead of a caption
KEYWORDS = {"MUKA", "HAPPY", "TERSENYUM", "BUKAN", "SENYUM", "GEBU", "KETEBALAN", "TERSENYUMLAH", "COMEL",
            "TIGA", "TAKUT", "DURIAN", "LEMBUT", "TEBAL", "PELUK", "TIDUR", "SANGAT-SANGAT", "BESAR", "95CM",
            "PANJANG", "BEG", "KUNING", "GRAB", "BETUL-BETUL"}

# ---------------------------------------------------------------- per-block layout (face avoidance)
# Head boxes measured on gridded key frames (fractions of the frame). In the garden shots her hood starts at
# y 0.17-0.25 on the right half, so the band y 0.09-0.16 (trees) is free; the pillow fills the left side.
# Labels are placed automatically from the block's head box (place_label): either the top band above her hood
# (height = head top - margin - LAB_TOP) or the left column beside her head over the pillow / trees
# (width = head left - margin). Big starburst labels take whichever region is roomier; LAYOUT can force one.
# Captions: "bottom" band (robe / pillow ends), "top" band (on the hood) for the face close-up, or "left" over
# the pillow when her face fills the right side.
LAB_TOP, MARGIN = 172, 40
CAP_BOTTOM, CAP_TOP = 1385, 262
LAYOUT = {
    "hook": dict(cap="top", label="top"),         # face fills the frame; only the hood band is free
}
LAYOUT_RANGES = [
    ((7.38, 8.75), dict(cap="left")),             # "Eh, bukan": her face fills the right, the pillow the left
]

SUBJECT = {   # head box (x0, y0, x1, y1) per block + pillow smileys (points), fractions of the frame
    "hook": dict(head=(0.10, 0.19, 0.97, 1.00), faces=[]),
    "bukan": dict(head=(0.42, 0.10, 0.98, 0.56), faces=[(0.12, 0.50)]),
    "senyum": dict(head=(0.95, 0.20, 1.00, 0.40), faces=[(0.48, 0.40)]),
    "kita": dict(head=(0.50, 0.18, 0.86, 0.45), faces=[(0.30, 0.32), (0.34, 0.60), (0.30, 0.83)]),
    "gebu": dict(head=(0.55, 0.13, 1.00, 0.46), faces=[(0.40, 0.30), (0.45, 0.55), (0.40, 0.80)]),
    "memang": dict(head=(0.60, 0.25, 0.97, 0.48), faces=[(0.30, 0.35), (0.32, 0.62)]),
    "comel": dict(head=(0.55, 0.17, 0.92, 0.50), faces=[(0.25, 0.30), (0.28, 0.52), (0.26, 0.78)]),
    "takut": dict(head=(0.45, 0.17, 0.90, 0.42), faces=[(0.25, 0.30), (0.26, 0.55), (0.25, 0.80)]),
    "durian": dict(head=(0.38, 0.17, 0.82, 0.45), faces=[(0.25, 0.32), (0.28, 0.55), (0.30, 0.80)]),
    "sangat": dict(head=(0.45, 0.20, 0.78, 0.45), faces=[(0.25, 0.33), (0.30, 0.56), (0.32, 0.80)]),
    "besar": dict(head=(0.45, 0.20, 0.86, 0.50), faces=[(0.22, 0.35), (0.25, 0.58), (0.27, 0.82)]),
    "cta": dict(head=(0.38, 0.18, 0.80, 0.46), faces=[(0.25, 0.32), (0.28, 0.58), (0.27, 0.83)]),
    "end": dict(head=(0.55, 0.20, 0.96, 0.50), faces=[(0.62, 0.40), (0.64, 0.62), (0.62, 0.84)]),
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
        mode = lay.get("cap", "bottom")
        pos = dict(top=dict(y=CAP_TOP), bottom=dict(y=CAP_BOTTOM),
                   left=dict(y=640, x=SAFE_L + 20 + 160, maxw=320))[mode]
        out.append(dict(t0=ch[0]["s"], t1=end, **pos,
                        words=[dict(w=x["w"].upper().strip(",."), s=x["s"], e=x["e"],
                                    key=x["w"].upper().strip(",.?!") in KEYWORDS) for x in ch]))
    return out


# ---------------------------------------------------------------- graphics (data for comp/index.html)
def place_label(t0, big):
    """Anchor (x centre, top edge) and the box the text must fit, chosen from the head box of the block at t0
    so that nothing (bubble, tail or starburst spikes) comes within MARGIN px of her head."""
    hx0, hy0 = SUBJECT[block_at(t0 + 0.01)]["head"][:2]
    top_h = hy0 * CH - MARGIN - LAB_TOP                 # free height above her hood
    left_w = hx0 * CW - MARGIN - (SAFE_L + 20)          # free width left of her head
    spill = 46 if big else 0                            # starburst spikes reach this far past the text box
    mode = layout_at(t0 + 0.01).get("label")
    if mode is None:
        if big:
            mode = "left" if left_w - 2 * spill >= 330 else "top"
        else:
            mode = "top" if top_h >= 100 else "left"     # one line ~70px still fits 100px
    if mode == "top":
        return dict(x=(SAFE_L + CW - SAFE_R) / 2, top=LAB_TOP + spill, maxw=780 - 2 * spill,
                    maxh=min(top_h - 2 * spill, 170), tail=None)
    w = min(left_w, 640) - 2 * spill
    return dict(x=SAFE_L + 20 + spill + w / 2, top=LAB_TOP + spill, maxw=w, maxh=300 - 2 * spill,
                tail=None if big else "bl")


def graphics():
    labels, bursts, wipes, sfx = [], [], [], []

    def lab(s0, s1, text, emoji="", sound="stamp", vol=0.45, big=False, rot=None, fs=None):
        t0, t1 = tl(s0), tl(s1)
        pos = place_label(t0, big)
        if big and pos["maxh"] < 130:      # no room for a starburst away from her face: big-font bubble instead
            big, pos = False, dict(place_label(t0, False), tail=None, fs=108)
        if fs:
            pos["fs"] = fs
        L = dict(t0=t0, t1=t1, html=text, emoji=emoji, big=big, **pos)
        if rot is not None:
            L["rot"] = rot
        labels.append(L)
        if sound:
            sfx.append((sound, t0 - 0.03, vol))

    def pop(src, text, x, y, color="#FF3B3B", size=250, dur=1.0, rot=8, sound="pop", vol=0.5, t=None):
        t = tl(src) if t is None else t
        bursts.append(dict(t=t, text=text, x=x, y=y, color=color, size=size, dur=dur, rot=rot))
        if sound:
            sfx.append((sound, t - 0.02, vol))

    def slam(block, sound="whoosh", vol=0.4):
        t = BT[block]["t0"]
        wipes.append(dict(t=t))
        sfx.append((sound, t - 0.25, vol))

    # hook: the face gag. Her face fills the frame, so the STOP bubble and captions sit on the hood band only.
    lab(0.02, 1.55, "STOP! STOP! <b>STOP!</b>", "✋", sound="impact", vol=0.35, fs=96)
    # punchline: "Eh, bukan, bukan!" -> the pillow's face
    pop(7.42, "OOPS!", 190, 1010, color="#2EC4F1", size=270, dur=1.25, rot=-8)
    lab(8.78, 10.80, "MUKA <b>NI!</b>", "👈", sound="pop")
    slam("senyum")
    lab(14.84, 16.06, "SENYUM <b>NI!</b>", "😊", sound="impact", vol=0.3, big=True)
    lab(16.64, 18.52, "KITA PUN <b>TERSENYUM</b>", "🥰")
    lab(19.34, 20.14, "GEBU <b>MACAM NI</b>", "☁️")
    lab(20.90, 21.92, "<b>TEBAL!</b>", "💪", sound="pop")
    lab(22.12, 23.04, "YA <b>RABBI!</b>", "😍", sound="stamp")
    lab(23.40, 24.98, "MEMANG <b>TERSENYUM</b>", "😁")
    lab(25.04, 26.54, "MUKA <b>COMEL</b>", "🥹")
    lab(26.90, 27.94, "ADA <b>3</b> MUKA!", "😆", sound="pop")
    lab(28.26, 29.20, "JANGAN <b>TAKUT!</b>", "🙈", sound="pop")
    slam("durian")
    lab(29.30, 32.18, "<b>LEMBUT</b> • GEBU • <b>TEBAL</b>", "☁️")
    lab(32.52, 34.90, "TEMAN <b>TIDUR</b>", "😴")
    lab(35.00, 36.26, "SANGAT <b>GEBU!</b>", "🤩", sound="impact", vol=0.3, big=True)
    slam("besar", sound="swish", vol=0.35)
    lab(37.62, 38.56, "SAIZ PALING <b>BESAR</b>", "📏")
    lab(38.98, 40.40, "<b>95</b>CM!", "😱", sound="impact", vol=0.35, big=True)
    lab(40.50, 41.96, "BESAR MACAM <b>ORANG!</b>", "😂", sound="pop")
    lab(42.66, 43.92, "TENGOK <b>BEG KUNING</b>", "🛒")
    lab(43.94, 45.06, "SILALAH <b>GRAB!</b>", "🏃‍♀️", sound="pop")
    lab(45.10, 46.86, "BETUL-BETUL <b>GEBU</b>", "☁️")
    # end card: comic panel frame, title bubble on top, pills in the bottom band, a burst in the free left gap
    e0 = BT["end"]["t0"] - 0.08
    end = dict(t0=e0, t1=TOTAL,
               title=dict(html="BANTAL PELUK <b>DURIAN</b>", emoji="💛", big=False,
                          **dict(place_label(e0, False), tail=None)),
               pills=[dict(y=1300, html="📏 95 • 75 • 52 • 30 CM", bg="#FFFFFF", fg="#141414"),
                      dict(y=1418, html="🛒 TEKAN BEG KUNING", bg="#FFE135", fg="#141414")],
               bursts=[dict(t=e0 + 0.35, text="GEBU!", x=185, y=1000, color="#FF3B3B", size=230, dur=5, rot=-10)])
    sfx.append(("ding", e0, 0.4))
    sfx.append(("pop", e0 + 0.33, 0.45))
    return labels, bursts, wipes, end, sfx


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
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "12" if FINAL else "16", "-g", "30", "-pix_fmt", "yuv420p",
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
    labels, bursts, wipes, end, sfx = graphics()
    data = dict(total=TOTAL, fps=FPS, w=CW, h=CH,
                safe=dict(l=SAFE_L, r=CW - SAFE_R, t=SAFE_T, b=CH - SAFE_B),
                captions=caption_chunks(words), labels=labels, bursts=bursts, wipes=wipes, tags=[], end=end,
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
