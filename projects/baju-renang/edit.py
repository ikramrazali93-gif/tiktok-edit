#!/usr/bin/env python3
"""Edit for the kids long-sleeve swimsuit (baju renang) TikTok video.

Needs the Fredoka Bold font (fonts/Fredoka-Bold.ttf, SIL OFL) installed, e.g. in ~/.fonts.

Usage: python3 edit.py <proxy.mp4> <transcript.json> <sfx_dir> <out_dir> [--final]
  preview: 720x1280 proxy -> preview.mp4;  --final: 1080x1920 master -> final.mp4
  --audio-only: re-mix voice + SFX onto the existing render -> *_voice.mp4

All times in BLOCKS are source times of the original clip (same timeline as
the proxy). The script builds:
  base.mp4     - cut/zoomed video + cleaned voice + SFX
  overlay.ass  - captions, labels, flashes, progress bar
  preview.mp4  - base + ASS + colour emoji stickers (rendered with Pillow)
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

PROXY, TRANSCRIPT, SFX, OUT = sys.argv[1:5]
W, H, FPS = 720, 1280, 30          # layout space for ASS / sticker coordinates
FINAL = "--final" in sys.argv       # --final: 1080x1920 from a full-res master
K = 1.5 if FINAL else 1.0
RW, RH = int(W * K), int(H * K)     # render size
VOICE_LUFS = -11.5                  # v1 was -15; SFX levels are absolute and stay unchanged

# ---------------------------------------------------------------- EDL
# v: list of (src_in, src_out, speed, zoom)
# a: 'same' (follow v at speed 1), None (silence) or list of (src_in, src_out)
BLOCKS = [
    # HOOK (moved from 29.3s): call-out to the buyer while she holds the top up
    # "Ini untuk siapa nak beli baju renang, baju mandi, tangan panjang untuk anak. Seluar panjang."
    dict(name="hook", a="same", v=[(29.25, 31.62, 1, 1.0), (31.62, 35.05, 1, 1.12)]),
    # silent unwrapping at the start, sped up
    dict(name="unbox", a=None, v=[(0.00, 4.35, 3.0, 1.0)]),
    # "Ini baju renang Abang Furqan." + "...saya tengok. Padan tak?"
    dict(name="intro", a="same", v=[(4.35, 7.75, 1, 1.0), (8.52, 10.27, 1, 1.1)]),
    # "Ini saiz paling kecil kan?" + "Saiz paling kecil, padan kot." (1.8s pause cut)
    dict(name="saiz", a="same", v=[(11.32, 12.42, 1, 1.0), (14.18, 16.20, 1, 1.12)]),
    dict(name="seluar", a="same", v=[(17.42, 20.72, 1, 1.0)]),
    # cut "hmm" 22.1-22.5; "Ui, panjang seluar dia. Abang kan rendah aje." / "Boleh dah. Tapi baju dia nampak padan..."
    dict(name="panjang", a="same", v=[(22.76, 25.43, 1, 1.1), (25.93, 28.68, 1, 1.0)]),
    # cut "hmm" 36.2-37.0 and the repeated "two pieces"
    dict(name="2pcs", a="same", v=[(37.10, 38.75, 1, 1.12), (40.12, 41.22, 1, 1.0)]),
    # flat-lay of the set on the box -> end card
    dict(name="end", a=None, v=[(41.30, 43.50, 1, 1.0)]),
]

FIX = {"selok": "seluar", "padang": "padan", "Padang": "Padan", "Furkan": "Furqan", "Furkan.": "Furqan."}
# hand-checked words where Whisper drifted or misheard
OVERRIDE = {
    8.52: [dict(s=s, e=e, w=w) for w, s, e in [
        ("Saya", 9.34, 9.42), ("tengok.", 9.42, 9.85), ("Padan", 9.90, 10.10), ("tak?", 10.10, 10.26)]],
    14.18: [dict(s=s, e=e, w=w) for w, s, e in [
        ("Saiz", 14.18, 14.30), ("paling", 14.30, 14.54), ("kecil,", 14.54, 15.50), ("padan", 15.60, 16.00),
        ("kot.", 16.02, 16.18)]],
    17.42: [dict(s=s, e=e, w=w) for w, s, e in [
        ("Yang", 17.48, 17.56), ("ada", 17.56, 17.72), ("seluar", 17.72, 18.04), ("sekali,", 18.04, 18.72),
        ("elok", 18.88, 19.18), ("aje.", 19.18, 19.40), ("Harga", 19.44, 19.82), ("pun", 19.82, 19.92),
        ("murah", 19.92, 20.14), ("aje", 20.14, 20.34), ("kan?", 20.34, 20.66)]],
    22.76: [dict(s=s, e=e, w=w) for w, s, e in [
        ("Ui,", 22.82, 22.98), ("panjang", 22.98, 23.30), ("seluar", 23.34, 23.56), ("dia.", 23.56, 23.90),
        ("Abang", 24.08, 24.34), ("kan", 24.34, 24.58), ("rendah", 24.58, 25.04), ("aje.", 25.04, 25.40)]],
    25.93: [dict(s=s, e=e, w=w) for w, s, e in [
        ("Boleh", 26.00, 26.18), ("dah.", 26.18, 26.50), ("Tapi", 27.06, 27.20), ("baju", 27.20, 27.40),
        ("dia", 27.40, 27.50), ("nampak", 27.50, 27.70), ("padan", 27.70, 27.98), ("aje,", 27.98, 28.20),
        ("insyaAllah.", 28.20, 28.66)]],
    37.10: [dict(s=s, e=e, w=w) for w, s, e in [
        ("Okay,", 37.14, 37.32), ("dia", 37.50, 37.62), ("2", 37.62, 38.20), ("piece.", 38.20, 38.68)]],
}
DROP = []
HILITE = {"RENANG", "BAJU", "MANDI", "TANGAN", "PANJANG", "SELUAR", "ANAK", "PADAN", "KECIL", "MURAH", "HARGA",
          "2", "PIECE", "COMEL", "FURQAN", "SAIZ", "ELOK"}


def build_timeline():
    vclips, aclips, t = [], [], 0.0
    src_map = []  # (src_in, src_out, tl_start) for audio that plays at 1x
    for b in BLOCKS:
        b["t0"] = t
        dur = 0.0
        for (s, e, sp, z) in b["v"]:
            d = (e - s) / sp
            vclips.append(dict(s=s, e=e, sp=sp, z=z, t=t + dur, d=d))
            dur += d
        if b["a"] == "same":
            al = [(s, e) for (s, e, sp, z) in b["v"]]
        else:
            al = b["a"]
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


# ---------------------------------------------------------------- words
def timeline_words():
    segs = json.load(open(TRANSCRIPT))
    words = [w for s in segs for w in s["words"]]
    out = []
    for c in ACLIPS:
        if "silence" in c:
            continue
        src = OVERRIDE.get(c["s"], words)
        for w in src:
            inside = c["s"] - 0.08 <= w["s"] <= c["e"] - 0.08
            straddle = c["s"] - 0.6 <= w["s"] < c["s"] and w["e"] > c["s"] + 0.15   # word mostly kept
            if (inside or straddle) and not any(d0 <= w["s"] < d1 for d0, d1 in DROP):
                txt = w["w"].strip()
                core = txt.strip(",.")
                txt = txt.replace(core, FIX.get(core, FIX.get(core.lower(), core)))
                s = c["t"] + max(w["s"], c["s"]) - c["s"]
                e = c["t"] + min(w["e"], c["e"]) - c["s"]
                if txt.strip(",.?!"):
                    out.append(dict(w=txt, s=s, e=e, clip=id(c)))
    out.sort(key=lambda w: w["s"])
    return out


# ---------------------------------------------------------------- ASS
def ts(t):
    t = max(0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


ASS_HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Fredoka,60,&H00FFFFFF,&H000000FF,&H004A2013,&H644A2013,-1,0,0,0,100,100,0,0,1,5,3,2,70,110,230,1
Style: Label,Fredoka,62,&H004A2013,&H000000FF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,3,16,0,5,40,40,0,1
Style: Small,Fredoka,40,&H00FFFFFF,&H000000FF,&H004A2013,&H644A2013,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,0,1
Style: Shape,Inter,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# palette taken from the swimsuit + pool vibe: aqua sleeve print, navy body,
# red price tag (coral), sunny yellow for the active word against grass/sky
AQUA = "&H00EED322&"     # #22D3EE  (ASS colours are BGR)
NAVY = "&H004A2013&"     # #13204A
CORAL = "&H005F5AFF&"    # #FF5A5F
SUN = "&H003BD4FF&"      # #FFD43B
WHITE = "&H00FFFFFF&"
ACC = SUN
KEY = AQUA


def captions(words):
    ev = []
    chunks, cur = [], []
    for w in words:
        if cur and (len(cur) >= 3 or w["s"] - cur[-1]["e"] > 0.35 or w["clip"] != cur[-1]["clip"]
                    or cur[-1]["w"][-1] in ",."):
            chunks.append(cur)
            cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    for i, ch in enumerate(chunks):
        end = ch[-1]["e"] + 0.15
        if i + 1 < len(chunks):
            end = min(end, chunks[i + 1][0]["s"])
        for j, w in enumerate(ch):
            ws = w["s"] if j else min(w["s"], ch[0]["s"])
            we = ch[j + 1]["s"] if j + 1 < len(ch) else end
            parts = []
            for k, x in enumerate(ch):
                t = x["w"].upper().strip(",.")
                if k == j:
                    parts.append(r"{\c%s\fscx112\fscy112}%s{\r}" % (ACC, t))
                elif t.strip("-") in HILITE or t in HILITE:
                    parts.append(r"{\c%s}%s{\r}" % (KEY, t))
                else:
                    parts.append(t)
            pop = r"{\fscx85\fscy85\t(0,90,\fscx100\fscy100)}" if j == 0 else ""
            ev.append(f"Dialogue: 2,{ts(ws)},{ts(we)},Cap,,0,0,0,,{pop}" + " ".join(parts))
    return ev


def label(t0, t1, text, y=760, col=NAVY, box=WHITE, hi=CORAL, rot=-3, layer=5, x=W // 2, size=None):
    """Pop-in boxed label with a slight tilt. *word* is drawn in the highlight colour."""
    parts = text.split("*")
    text = "".join(p if i % 2 == 0 else rf"{{\c{hi}}}{p}{{\c{col}}}" for i, p in enumerate(parts))
    fs = rf"\fs{size}" if size else ""
    return (f"Dialogue: {layer},{ts(t0)},{ts(t1)},Label,,0,0,0,,"
            rf"{{\an5\pos({x},{y})\frz{rot}{fs}\c{col}\3c{box}\fscx0\fscy0"
            rf"\t(0,140,\fscx118\fscy118)\t(140,240,\fscx100\fscy100)\fad(0,150)}}{text}")


def flash(t0, d=0.35, layer=9, col=WHITE):
    return (f"Dialogue: {layer},{ts(t0)},{ts(t0 + d)},Shape,,0,0,0,,"
            rf"{{\an7\pos(0,0)\c{col}\1a&H30&\fad(0,{int(d * 1000) - 40})\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")


def chip(t0, t1, x, y, col, name):
    return [
        f"Dialogue: 6,{ts(t0)},{ts(t1)},Shape,,0,0,0,,"
        rf"{{\an5\pos({x},{y})\c{col}\3c&HFFFFFF&\bord5\fscx0\fscy0\t(0,150,\fscx100\fscy100)\fad(0,120)\p1}}"
        r"m -45 0 b -45 -60 45 -60 45 0 b 45 60 -45 60 -45 0{\p0}",
        f"Dialogue: 6,{ts(t0)},{ts(t1)},Small,,0,0,0,,"
        rf"{{\an5\pos({x},{y + 80})\fscx0\fscy0\t(0,150,\fscx100\fscy100)\fad(0,120)}}{name}",
    ]


def graphics():
    ev, stickers, sfx = [], [], []
    # progress bar (retention)
    ev.append(f"Dialogue: 8,{ts(0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{AQUA}\fscx0\t(0,{int(TOTAL * 1000)},\fscx100)\p1}}m 0 0 l {W} 0 {W} 8 0 8{{\p0}}")

    def lab(s0, s1, text, sound="pop", vol=0.5, **kw):
        ev.append(label(tl(s0), tl(s1), text, **kw))
        if sound:
            sfx.append((sound, tl(s0), vol))

    def stk(em, s0, s1, x, y, size=100):
        stickers.append((em, tl(s0), tl(s1), x, y, size))

    # ---- HOOK: buyer call-out over the top held up
    lab(29.30, 31.00, "SIAPA NAK *BELI*?", col=WHITE, box=CORAL, hi=SUN, rot=-3, size=70, sound="whoosh", vol=0.4)
    stk("🙋", 29.35, 31.00, 620, 680, 110)
    lab(31.00, 33.10, "BAJU RENANG *ANAK*", box=AQUA, hi=WHITE, rot=2, size=68, sound="bloop", vol=0.55)
    stk("🏊", 31.05, 33.10, 610, 670, 110)
    stk("🫧", 31.10, 35.05, 110, 640, 90)
    stk("🫧", 31.40, 35.05, 640, 420, 70)
    lab(33.14, 34.32, "*TANGAN* PANJANG", rot=-2, sound="pop")
    stk("✅", 33.18, 34.32, 620, 680, 90)
    lab(34.36, 35.05, "*SELUAR* PANJANG", rot=2, sound="pop")
    stk("✅", 34.40, 35.05, 620, 680, 90)

    # ---- unboxing ramp
    b = BT["unbox"]
    ev.append(f"Dialogue: 6,{ts(b['t0'])},{ts(b['t0'] + b['dur'])},Small,,0,0,0,,"
              rf"{{\an9\pos({W - 30},70)\c{SUN}}}>> x3")
    sfx += [("swish", b["t0"] - 0.05, 0.45), ("pop", b["t0"] + b["dur"] - 0.2, 0.4)]

    # ---- intro / size
    lab(6.30, 7.75, "UNTUK *ABANG FURQAN*", rot=-2, size=56)
    stk("👦", 6.35, 7.75, 640, 670, 100)
    lab(9.90, 10.27, "*PADAN* TAK?", col=WHITE, box=CORAL, hi=SUN, rot=3, sound="bloop", vol=0.5)
    stk("🤔", 9.92, 10.27, 620, 670, 100)
    lab(11.50, 12.42, "SAIZ PALING *KECIL*", rot=-2)
    stk("📏", 11.55, 12.42, 640, 670, 90)
    lab(15.60, 16.20, "*PADAN!*", box=AQUA, hi=WHITE, rot=3, size=76, sound="ding", vol=0.35)
    stk("✅", 15.62, 16.20, 600, 670, 100)

    # ---- set + price
    lab(17.72, 19.40, "ADA *SELUAR* SEKALI", rot=-2)
    stk("👖", 17.76, 19.40, 640, 670, 100)
    lab(19.44, 20.72, "HARGA *MURAH!*", col=WHITE, box=CORAL, hi=SUN, rot=3, size=74, sound="kaching", vol=0.35)
    stk("💰", 19.48, 20.72, 620, 660, 110)

    # ---- fit
    lab(22.98, 24.05, "*SELUAR* PANJANG", rot=-3)
    lab(24.08, 25.43, "ABANG *RENDAH* JE", rot=2, sound="bloop", vol=0.5)
    stk("😆", 24.12, 25.43, 630, 670, 100)
    lab(26.00, 27.00, "BOLEH *DAH!*", box=AQUA, hi=WHITE, rot=-2)
    stk("👍", 26.02, 27.00, 620, 670, 100)
    lab(27.50, 28.68, "NAMPAK *PADAN*", rot=3, sound="sparkle", vol=0.3)
    stk("✨", 27.55, 28.68, 630, 670, 90)

    # ---- two piece
    lab(37.62, 38.75, "*2 PIECE*", box=AQUA, hi=WHITE, rot=-3, size=80)
    stk("👕", 37.66, 38.75, 140, 670, 100)
    stk("👖", 37.80, 38.75, 600, 670, 100)
    sfx.append(("pop", tl(37.80), 0.45))
    lab(40.12, 41.22, "*COMEL!*", rot=3, size=78, sound="ding", vol=0.35)
    stk("🥰", 40.16, 41.22, 620, 670, 100)

    # ---- end card over the flat-lay
    e0 = BT["end"]["t0"]
    ev.append(f"Dialogue: 8,{ts(e0)},{ts(TOTAL)},Shape,,0,0,0,,"
              rf"{{\an7\pos(0,0)\c{NAVY}\1a&HFF&\t(0,250,\1a&H60&)\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\p0}}")
    ev.append(label(e0 + 0.05, TOTAL, "BAJU RENANG *ANAK*", box=WHITE, hi=CORAL, y=470, rot=-3, layer=9, size=62))
    ev.append(label(e0 + 0.3, TOTAL, "TANGAN + SELUAR *PANJANG*", box=AQUA, hi=WHITE, y=580, rot=2, layer=9,
                    size=46))
    ev.append(label(e0 + 0.7, TOTAL, "TEKAN BEG KUNING", col=NAVY, box=SUN, y=720, rot=-2, layer=9, size=58))
    stickers.append(("🏊", e0 + 0.1, TOTAL, 610, 380, 100))
    stickers.append(("🫧", e0 + 0.2, TOTAL, 110, 400, 80))
    stickers.append(("🛒", e0 + 0.75, TOTAL, 110, 800, 100))
    sfx += [("whoosh", e0 - 0.1, 0.4), ("pop", e0 + 0.05, 0.45), ("pop", e0 + 0.3, 0.45),
            ("kaching", e0 + 0.7, 0.45)]
    return ev, stickers, sfx


# ---------------------------------------------------------------- emoji stickers
def sticker_frames(stickers):
    font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
    cache = {}
    for em, *_ in stickers:
        if em not in cache:
            im = Image.new("RGBA", (160, 160))
            ImageDraw.Draw(im).text((10, 10), em, font=font, embedded_color=True)
            cache[em] = im.crop(im.getbbox())
    n = int(round(TOTAL * FPS))
    for f in range(n):
        t = f / FPS
        frame = Image.new("RGBA", (RW, RH))
        for i, (em, t0, t1, x, y, size) in enumerate(stickers):
            if not (t0 <= t < t1):
                continue
            u = t - t0
            sc = min(1.0, u / 0.12) * 1.25 if u < 0.12 else (1.25 - 0.25 * min(1, (u - 0.12) / 0.1))
            if t1 - t < 0.12:
                sc *= max(0.0, (t1 - t) / 0.12)
            if sc <= 0.02:
                continue
            bob = 5 * K * np.sin(2 * np.pi * 1.6 * u + i)
            img = cache[em]
            s = max(1, int(size * sc * K))
            im = img.resize((s, int(s * img.height / img.width)), Image.LANCZOS)
            im = im.rotate(8 * np.sin(2 * np.pi * 0.9 * u + i), resample=Image.BICUBIC, expand=True)
            frame.alpha_composite(im, (int(x * K - im.width / 2), int(y * K + bob - im.height / 2)))
        yield frame.tobytes()


# ---------------------------------------------------------------- render
def run(cmd, **kw):
    print("+", " ".join(cmd[:6]), "...", flush=True)
    subprocess.run(cmd, check=True, **kw)


def render_base(sfx):
    # video: one ffmpeg per clip (a single graph with many trims of one input
    # buffers frames and runs out of memory at 1080p), then stream-copy concat
    cdir = os.path.join(OUT, "clips")
    os.makedirs(cdir, exist_ok=True)
    lst = []
    for i, c in enumerate(VCLIPS):
        z = c["z"]
        # frame count from rounded timeline positions so clips never drift from the audio
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
    fc = []
    al = []
    for i, c in enumerate(ACLIPS):
        if "silence" in c:
            fc.append(f"anullsrc=r=48000:cl=mono,atrim=0:{c['silence']:.3f}[a{i}]")
        else:
            d = c["e"] - c["s"]
            fc.append(f"[1:a]atrim={c['s']}:{c['e']},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=mono,"
                      f"afade=t=in:d=0.02,afade=t=out:st={d - 0.03:.3f}:d=0.03[a{i}]")
        al.append(f"[a{i}]")
    fc.append("".join(al) + f"concat=n={len(al)}:v=0:a=1,"
              # clarity: cut rumble + mud, lift presence/air, tame sibilance
              "highpass=f=100,afftdn=nf=-25:tn=1,"
              "equalizer=f=250:t=q:w=1.0:g=-3,equalizer=f=3200:t=q:w=1.2:g=4,"
              "treble=g=2.5:f=9000,deesser=i=0.35,"
              # even out quiet words before the gain stage
              "acompressor=threshold=-26dB:ratio=4:attack=4:release=90:makeup=2")
    # pass 1: measure the processed voice, pass 2: exact gain to VOICE_LUFS + peak limiter
    probe = subprocess.run(["ffmpeg", "-nostats", "-vn", "-i", PROXY, "-filter_complex",
                            ";".join(fc).replace("[1:a]", "[0:a]") + ",ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
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


def render_preview(stickers, ass_path):
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", os.path.join(OUT, "base.mp4"),
           "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{RW}x{RH}", "-r", str(FPS), "-i", "-",
           "-filter_complex", f"[0:v][1:v]overlay=0:0:format=auto,ass={ass_path}[v]",
           "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "slow" if FINAL else "medium", "-crf", "18" if FINAL else "21",
           "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-c:a", "copy", "-movflags", "+faststart",
           os.path.join(OUT, "final.mp4" if FINAL else "preview.mp4")]
    print("+ preview", flush=True)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fr in sticker_frames(stickers):
        p.stdin.write(fr)
    p.stdin.close()
    assert p.wait() == 0


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    words = timeline_words()
    ev, stickers, sfx = graphics()
    ass_path = os.path.join(OUT, "overlay.ass")
    with open(ass_path, "w") as f:
        f.write(ASS_HEAD + "\n".join(ev + captions(words)) + "\n")
    with open(os.path.join(OUT, "edl.json"), "w") as f:
        json.dump(dict(total=TOTAL, blocks=[{k: b[k] for k in ("name", "t0", "dur", "v", "a")} for b in BLOCKS],
                       words=words, sfx=sfx, stickers=stickers), f, ensure_ascii=False, indent=1)
    print(f"timeline {TOTAL:.2f}s, {len(VCLIPS)} clips, {len(sfx)} sfx, {len(stickers)} stickers")
    if "--audio-only" in sys.argv:
        # re-mix audio onto an already rendered video (graphics untouched)
        src = os.path.join(OUT, "final.mp4" if FINAL else "preview.mp4")
        render_audio(sfx, ["-i", src], os.path.join(OUT, ("final" if FINAL else "preview") + "_voice.mp4"))
    elif "--no-render" not in sys.argv:
        render_base(sfx)
        render_preview(stickers, ass_path)
