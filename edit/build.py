#!/usr/bin/env python3
"""Bina video TikTok dari EDL + transcript (tanpa HyperFrames, ffmpeg sahaja).

  python3 edit/build.py            -> out/preview.mp4 (540x960, watermark PREVIEW)
  python3 edit/build.py --final    -> out/final.mp4   (1080x1920)  [jangan jalan sebelum preview diluluskan]
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDIT = os.path.join(ROOT, "edit")
OUT = os.path.join(ROOT, "out")
SRC = os.path.join(ROOT, "source", "main.mp4")
FINAL = "--final" in sys.argv
W, H = (1080, 1920) if FINAL else (540, 960)
FPS = 30
os.makedirs(OUT, exist_ok=True)

edl = json.load(open(os.path.join(EDIT, "edl.json")))["blocks"]
tx = json.load(open(os.path.join(EDIT, "transcript_raw.json")))
words = [w for s in tx["segments"] for w in s["words"]]

# ---------- timeline ----------
off = 0.0
for b in edl:
    b["dur"] = b["a"][1] - b["a"][0]
    b["v"] = b.get("v") or [b["a"]]
    vd = sum(e - s for s, e in b["v"])
    assert abs(vd - b["dur"]) < 0.02, (b["id"], vd, b["dur"])
    b["off"] = off
    off += b["dur"]
TOTAL = off


def m(src_t):
    """source time -> output time (berdasarkan audio)."""
    for b in edl:
        if b["a"][0] - 0.05 <= src_t <= b["a"][1] + 0.05:
            return b["off"] + max(0.0, src_t - b["a"][0])
    raise ValueError(f"{src_t} tidak ada dalam EDL")


def bid(i):
    return next(b for b in edl if b["id"] == i)


# ---------- captions (gaya rujukan: 1-2 perkataan, tengah skrin, keyword kuning) ----------
FIX = {"bantai": "bantal", "galah": "galas", "bag": "beg", "zit": "zip", "-zit": "zip",
       "bah": "bas", "retapi": "kereta api", "hat": "yang", "bagku": "beg kuning",
       "-sangat": "sangat", "160cm": "160CM", "100cm": "100CM", "x": "X", "pi": "pergi"}
KEY = {"bantal", "selimut", "beg", "galas", "function", "borong", "160cm", "100cm", "v2", "travel",
       "bas", "kereta", "api", "terpisah", "bercantum", "dua", "satu", "kuning", "besar", "berjahit",
       "cantum", "asing", "pilihan", "berbeza", "ramai", "unboxing", "pieces", "zip"}
YEL = r"{\c&H00D4FF&}"   # BGR -> #FFD400
WHT = r"{\c&HFFFFFF&}"


def clean(w):
    core = re.sub(r"[,.?!]", "", w.strip())
    return FIX.get(core.lower(), core)


cap_words = []
for b in edl:
    a0, a1 = b["a"]
    for w in words:
        mid = (w["s"] + min(w["e"], w["s"] + 0.6)) / 2
        if a0 <= mid <= a1:
            cap_words.append({"t": clean(w["w"]), "s": b["off"] + max(0, w["s"] - a0),
                              "brk": w["w"].strip()[-1:] in ",.?!", "blk": b["id"]})

groups, cur = [], []
for i, w in enumerate(cap_words):
    cur.append(w)
    nxt = cap_words[i + 1] if i + 1 < len(cap_words) else None
    if (len(cur) >= 2 or w["brk"] or nxt is None or nxt["blk"] != w["blk"]
            or len(" ".join(x["t"] for x in cur)) > 11):
        groups.append(cur); cur = []


def ts(t):
    t = max(0, t); h = int(t // 3600); mm = int(t % 3600 // 60); s = t % 60
    return f"{h}:{mm:02d}:{s:05.2f}"


ev = []
for gi, g in enumerate(groups):
    st = g[0]["s"]
    en = groups[gi + 1][0]["s"] if gi + 1 < len(groups) else TOTAL
    blk = bid(g[-1]["blk"])
    en = min(en, blk["off"] + blk["dur"], st + 1.6)
    txt = " ".join((YEL if any(k in x["t"].lower().split() for k in KEY) else WHT) + x["t"].upper() for x in g)
    pop = r"{\pos(540,1300)\fscx70\fscy70\t(0,90,\fscx112\fscy112)\t(90,160,\fscx100\fscy100)}"
    ev.append(f"Dialogue: 1,{ts(st)},{ts(en)},Cap,,0,0,0,,{pop}{txt}")

# ---------- motion graphics ----------
sfx = []  # (time, name, gain)


def gfx(start, end, text, style="Box", y=330, sound="pop", extra=""):
    anim = r"{\fscx0\fscy0\t(0,120,\fscx115\fscy115)\t(120,200,\fscx100\fscy100)}"
    ev.append(f"Dialogue: 2,{ts(start)},{ts(end)},{style},,0,0,0,,{{\\pos(540,{y})}}{anim}{extra}{text}")
    if sound:
        sfx.append((start, sound, 1.0))


hook = bid("HOOK"); hook_end = hook["dur"]
gfx(0.0, hook_end, "2 DALAM 1", "Box", 190, sound="whoosh")
gfx(m(10.40), hook_end, "BANTAL", "Big", 315)
gfx(m(11.68), hook_end, "+ SELIMUT", "Big", 425)
gfx(m(13.90), hook_end, "+ BEG", "Big", 535)
gfx(m(5.56), m(7.85), "RAMAI ORANG BORONG", "Box", 300, sound="ding")
gfx(m(19.96), m(20.9), "BOLEH GALAS", "Box", 300)
gfx(m(29.66), m(30.6), "2 PILIHAN SELIMUT", "Box", 300)
gfx(m(36.36), m(41.2), "BIASA  vs  V2", "Box", 300)
gfx(m(42.6), m(45.1), "LUAR SAMA, DALAM BEZA", "Box", 300)
gfx(m(61.62), m(65.95), "160 x 100 CM", "Huge", 360, sound="ding")
gfx(m(67.96), m(70.9) + 0.6, "✓ TRAVEL", "Check", 300)
gfx(m(68.98), m(70.9) + 0.6, "✓ BAS", "Check", 420)
gfx(m(70.00), m(70.9) + 0.6, "✓ KERETA API", "Check", 540)
gfx(m(72.62), m(74.6), "BERJAHIT · CANTUM", "Box", 300)
gfx(m(75.58), m(82.4), "BUKA = SELIMUT", "Box", 300)
gfx(m(77.58), m(82.4), "TUTUP = BANTAL", "Box2", 440)
gfx(m(90.92), m(94.8), "V2 = SELIMUT ASING", "Box", 300)
gfx(m(98.92), m(102.2), "GUNA 2 SERENTAK", "Box", 300)
gfx(m(104.9), m(108.1), "BERCANTUM  vs  TERPISAH", "Box", 300)
gfx(m(109.15), TOTAL, "TEKAN BEG KUNING", "Huge", 360, sound="ding",
    extra=r"{\t(300,600,\frz-3)\t(600,900,\frz3)\t(900,1200,\frz0)}")
ev.append(f"Dialogue: 2,{ts(m(109.4))},{ts(TOTAL)},Big,,0,0,0,,{{\\move(540,480,540,540,0,400)}}▼")

# whoosh pada setiap potongan shot hook + peralihan penting
t = 0.0
for s, e in hook["v"][:-1]:
    t += e - s
    sfx.append((t - 0.15, "whoosh", 0.8))
sfx.append((hook_end - 0.2, "whoosh", 1.0))
sfx.append((m(51.3) - 0.1, "whoosh", 0.6))   # sebelum buka zip
sfx.append((m(60.55), "whoosh", 0.8))        # reveal selimut
sfx.append((m(88.85), "whoosh", 0.6))

if not FINAL:
    ev.append(r"Dialogue: 9,0:00:00.00," + ts(TOTAL) + r",Wm,,0,0,0,,{\pos(1040,60)}PREVIEW")

ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Black,96,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,7,3,5,40,40,0,1
Style: Box,Inter Black,84,&H00000000,&H00000000,&H0000D4FF,&H00000000,0,0,0,0,100,100,1,0,3,18,0,5,40,40,0,1
Style: Box2,Inter Black,84,&H0000D4FF,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,1,0,3,18,0,5,40,40,0,1
Style: Big,Inter Black,96,&H0000D4FF,&H0000D4FF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,8,4,5,40,40,0,1
Style: Huge,Inter Black,120,&H00000000,&H00000000,&H0000D4FF,&H00000000,0,0,0,0,100,100,1,0,3,24,0,5,40,40,0,1
Style: Check,Inter Black,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,7,3,5,40,40,0,1
Style: Wm,Inter Black,40,&H80FFFFFF,&H80FFFFFF,&H80000000,&H00000000,0,0,0,0,100,100,2,0,1,2,0,9,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(ev) + "\n"
ass_path = os.path.join(OUT, "captions.ass")
open(ass_path, "w").write(ass)

# ---------- SFX (disintesis, tiada fail luar) ----------
SFXD = os.path.join(OUT, "sfx"); os.makedirs(SFXD, exist_ok=True)
gen = {
    "pop": "aevalsrc='0.7*sin(2*PI*(500+2200*exp(-t*35))*t)*exp(-t*22)':d=0.18:s=48000",
    "ding": "aevalsrc='0.35*(sin(2*PI*1318*t)+0.6*sin(2*PI*1976*t)+0.3*sin(2*PI*2637*t))*exp(-t*4.5)':d=1.0:s=48000",
}
for k, expr in gen.items():
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", expr, "-ac", "2",
                    os.path.join(SFXD, k + ".wav")], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.5:c=pink:r=48000:a=0.6",
                "-af", "highpass=f=400,lowpass=f=5000,afade=t=in:d=0.3:curve=exp,afade=t=out:st=0.3:d=0.2,volume=0.9",
                "-ac", "2", os.path.join(SFXD, "whoosh.wav")], check=True)

print(f"Tempoh akhir: {TOTAL:.1f}s  |  blok: {len(edl)}  |  kapsyen: {len(groups)}  |  sfx: {len(sfx)}")

# ---------- peringkat 1: potong setiap shot video (jimat RAM) ----------
pre = f"scale={W}:{H}:flags=bicubic,fps={FPS},setsar=1"
SEGD = os.path.join(OUT, "seg_final" if FINAL else "seg_preview"); os.makedirs(SEGD, exist_ok=True)
seg_files = []
vt = 0.0  # masa keluaran kumulatif supaya bilangan frame tak drift
for b in edl:
    z = b.get("zoom", 1.0)
    for (s, e) in b["v"]:
        frames = int(round((vt + e - s) * FPS)) - int(round(vt * FPS)); vt += e - s
        chain = pre
        if z == "push":
            chain += (f",zoompan=z='1.0+0.10*on/{max(frames, 1)}':x='iw/2-(iw/zoom/2)':y='ih*0.35-(ih/zoom*0.35)'"
                      f":d=1:s={W}x{H}:fps={FPS}")
        elif z != 1.0:
            sw, sh = int(W * z) // 2 * 2, int(H * z) // 2 * 2
            chain += f",scale={sw}:{sh},crop={W}:{H}:(iw-{W})/2:(ih-{H})*0.30"
        f = os.path.join(SEGD, f"v{len(seg_files):02d}.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.3f}", "-i", SRC, "-an",
                        "-vf", chain + ",setsar=1", "-frames:v", str(frames),
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "10" if FINAL else "18",
                        "-pix_fmt", "yuv420p", f], check=True)
        seg_files.append(f)

# ---------- peringkat 2: gabung + audio + grafik ----------
fc, alabels = [], []
vlabels = [f"[{k + 1}:v]" for k in range(len(seg_files))]
for b in edl:
    a0, a1 = b["a"]
    i = len(alabels)
    fc.append(f"[0:a]atrim={a0}:{a1},asetpts=PTS-STARTPTS,aresample=48000,"
              f"afade=t=in:d=0.012,afade=t=out:st={b['dur'] - 0.015:.3f}:d=0.015[a{i}]")
    alabels.append(f"[a{i}]")

fc.append("".join(vlabels) + f"concat=n={len(vlabels)}:v=1:a=0[vc]")
fc.append("".join(alabels) + f"concat=n={len(alabels)}:v=0:a=1,highpass=f=80,"
          "acompressor=threshold=0.1:ratio=3:attack=5:release=120,volume=1.4[voice]")
# progress bar kuning di atas
bar_h = max(6, H // 160)
fc.append(f"color=c=0xFFD400:s={W}x{bar_h}:r={FPS}:d={TOTAL:.3f}[bar]")
fc.append(f"[vc][bar]overlay=x='-W+W*t/{TOTAL:.3f}':y=0:shortest=1[vb]")
fc.append(f"[vb]ass='{ass_path}'[vout]")

inputs = ["-i", SRC] + [x for f in seg_files for x in ("-i", f)]
sfx_lbls = []
for j, (t0, name, g) in enumerate(sorted(sfx)):
    inputs += ["-i", os.path.join(SFXD, name + ".wav")]
    vol = {"pop": 0.35, "ding": 0.30, "whoosh": 0.45}[name] * g
    d = int(max(0, t0) * 1000)
    fc.append(f"[{j + 1 + len(seg_files)}:a]volume={vol:.2f},adelay={d}|{d}[s{j}]")
    sfx_lbls.append(f"[s{j}]")
fc.append("[voice]" + "".join(sfx_lbls) +
          f"amix=inputs={1 + len(sfx_lbls)}:normalize=0:duration=first,"
          "loudnorm=I=-14:TP=-1.5:LRA=11[aout]")

out = os.path.join(OUT, "final.mp4" if FINAL else "preview.mp4")
open(os.path.join(OUT, "filtergraph.txt"), "w").write(";\n".join(fc))
cmd = ["ffmpeg", "-v", "error", "-stats", "-y", *inputs, "-filter_complex_script",
       os.path.join(OUT, "filtergraph.txt"), "-map", "[vout]", "-map", "[aout]",
       "-c:v", "libx264", "-preset", "slow" if FINAL else "veryfast", "-crf", "18" if FINAL else "26",
       "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k" if FINAL else "128k",
       "-movflags", "+faststart", "-t", f"{TOTAL:.3f}", out]
subprocess.run(cmd, check=True)
print("->", out)
