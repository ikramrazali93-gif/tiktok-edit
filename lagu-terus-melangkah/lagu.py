"""Gubah & campur lagu deklamasi 'Terus Melangkah'.

Setiap baris lirik diletakkan tepat pada permulaan bar/rentak. Susunan:
intro -> rangkap 1 -> pra-korus (+bar binaan) -> korus (+hook) -> rangkap 2 -> korus
-> jambatan (pecahan) -> korus akhir (naik 2 semiton, +hook) -> penutup.

Output: output/terus-melangkah.mp3, output/terus-melangkah.wav, output/terus-melangkah.lrc
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT.parent / "karung-beras"))
from muzik import SR, add, env, hz, pad, pluck, read_wav, reverb, write_wav  # noqa: E402

BUILD = ROOT / "build"
OUT = ROOT / "output"
BPM = 88
BEAT = 60 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(7)

# ------------------------------------------------------------------ bunyi asas

def band_noise(dur, lo, hi):
    n = max(1, int(dur * SR))
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    spec[(f < lo) | (f > hi)] = 0
    x = np.fft.irfft(spec, n).astype(np.float32)
    return x / (np.abs(x).max() + 1e-9)


def decay(n, rate):
    return np.exp(-np.arange(n) / SR * rate).astype(np.float32)


def kick():
    t = np.arange(int(0.5 * SR)) / SR
    f = 48 + 120 * np.exp(-t * 32)
    return (np.tanh(1.6 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t * 8)).astype(np.float32)


def snare():
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * 185 * t) * np.exp(-t * 25)
    return (0.5 * body + band_noise(0.3, 1200, 9000) * decay(n, 18)).astype(np.float32)


def clap():
    x = band_noise(0.28, 900, 7000)
    out = np.zeros_like(x)
    for d in (0, 0.011, 0.023):  # tepukan berlapis
        i = int(d * SR)
        out[i:] += x[: len(x) - i] * decay(len(x) - i, 20)
    return out / 2


def hat(open_=False):
    d = 0.25 if open_ else 0.05
    x = band_noise(d, 6500, 15000)
    return x * decay(len(x), 12 if open_ else 80)


def shaker():
    x = band_noise(0.09, 5000, 12000)
    t = np.linspace(0, 1, len(x))
    return x * np.sin(np.pi * t) ** 2


def tom(f0=110):
    t = np.arange(int(0.45 * SR)) / SR
    f = f0 * (1 + 0.6 * np.exp(-t * 20))
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)).astype(np.float32)


def crash():
    x = band_noise(2.5, 3000, 16000)
    return x * decay(len(x), 1.8)


def riser(dur):
    t = np.arange(int(dur * SR)) / SR
    tone = 0.25 * np.sin(2 * np.pi * np.cumsum(150 * 8 ** (t / dur)) / SR)
    return ((tone + 0.7 * band_noise(dur, 1500, 12000)) * (t / dur) ** 2.2).astype(np.float32)


def impact():
    t = np.arange(int(2.0 * SR)) / SR
    boom = np.sin(2 * np.pi * (36 + 70 * np.exp(-t * 7)) * t) * np.exp(-t * 2.5)
    return (boom + 0.3 * band_noise(2.0, 60, 2500) * np.exp(-t * 6)).astype(np.float32)


def bass(freq, dur):
    t = np.arange(int(dur * SR)) / SR
    x = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t) + 0.12 * np.sin(6 * np.pi * freq * t)
    return (np.tanh(1.3 * x) * env(len(t), 0.01, min(0.12, dur / 3))).astype(np.float32)


def lead(freq, dur):
    """Lead lembut (seakan seruling/synth) dengan vibrato."""
    t = np.arange(int((dur + 0.25) * SR)) / SR
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - 0.15) / 0.2, 0, 1)
    ph = 2 * np.pi * np.cumsum(freq * vib) / SR
    x = np.sin(ph) + 0.45 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph) + 0.1 * np.sin(4 * ph)
    e = np.ones(len(t), np.float32)
    na, nr = int(0.03 * SR), int(0.25 * SR)
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return (x * e * 0.5).astype(np.float32)


def piano(freq, dur=2.5, vel=1.0):
    t = np.arange(int(dur * SR)) / SR
    x = (np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(4 * np.pi * freq * t) * np.exp(-t * 2.5)
         + 0.25 * np.sin(6 * np.pi * freq * t) * np.exp(-t * 4) + 0.1 * np.sin(8 * np.pi * freq * t) * np.exp(-t * 6))
    return (x * np.exp(-t * 1.6) * env(len(t), 0.004, 0.15) * vel).astype(np.float32)


def strings(freq, dur):
    t = np.arange(int(dur * SR)) / SR
    x = sum(np.sin(2 * np.pi * freq * d * t + p) for d, p in ((1.0, 0), (1.003, 1.1), (0.997, 2.3), (2.0, 0.5)))
    return (x / 4 * env(len(t), 0.5, 0.8)).astype(np.float32)


def delay(x, t=0.75 * BEAT, fb=0.35, n=4):
    out = x.copy()
    d = int(t * SR)
    for k in range(1, n + 1):
        out[d * k:] += x[: len(x) - d * k] * fb ** k
    return out


# ------------------------------------------------------------------ harmoni
CHORD = {  # akar (oktaf 2) + triad sekitar C4
    "C": (36, [48, 52, 55]), "Dm": (38, [50, 53, 57]), "Em": (40, [52, 55, 59]), "F": (41, [53, 57, 60]),
    "G": (43, [55, 59, 62]), "Am": (45, [57, 60, 64]),
}
PROG = {
    "intro": ["Am", "F", "C", "G"], "rangkap": ["Am", "F", "C", "G"], "prakorus": ["Dm", "Em", "F", "G"],
    "korus": ["F", "C", "G", "Am"], "hook": ["F", "G"], "jambatan": ["Am", "F", "C", "G"], "penutup": ["F", "G", "C", "C"],
}
_ = None
MELODI_KORUS = [  # grid 1/8; '-' = sambung nota; None = rehat
    [69, "-", 72, "-", 69, 67, 65, "-"],
    [64, 67, 72, "-", 74, 72, 67, "-"],
    [71, 74, 79, "-", 77, 76, 74, "-"],
    [72, "-", 71, 69, "-", "-", 64, "-"],
]
MELODI_HOOK = [[72, 74, 76, "-", 74, 72, 69, "-"], [71, "-", 74, "-", 79, "-", "-", "-"]]


def melody(buf, bars, t0, transpose, gain):
    step = BAR / 8
    notes = []
    for b, bar in enumerate(bars):
        for i, n in enumerate(bar):
            t = t0 + b * BAR + i * step
            if n == "-":
                if notes:
                    notes[-1][2] += step
            elif n is None:
                notes.append(None)
            else:
                notes.append([n, t, step])
    for nt in notes:
        if nt:
            add(buf, gain * lead(hz(nt[0] + transpose), nt[2] * 0.95), nt[1])


# ------------------------------------------------------------------ susunan

def slot_beats(dur, allowed):
    for b in allowed:
        if dur <= b * BEAT * 0.97:
            return b
    return allowed[-1]


def plan(vokal):
    """Tentukan masa mula setiap bahagian & baris (dikuantumkan ke rentak)."""
    by = {}
    for v in vokal:
        by.setdefault(v["bahagian"], []).append(v)
    order = [("intro", 4), ("rangkap1", None), ("prakorus", None), ("bina", 1), ("korus", None), ("hook", 2),
             ("rangkap2", None), ("korus2", None), ("hook2", 2), ("jambatan", None), ("bina2", 1),
             ("korus_akhir", None), ("hook3", 2), ("penutup", None), ("akhir", 2)]
    sections, lines = [], []
    t = 0.0
    for name, bars in order:
        src = {"korus2": "korus"}.get(name, name)
        if bars is None:
            beats_used = 0
            allowed = [2, 4, 8] if src == "prakorus" else [4, 8]
            for v in by[src]:
                sb = slot_beats(v["tempoh"], allowed)
                lines.append(dict(v, mula=round(t + beats_used * BEAT + (0.08 if src != "prakorus" else 0.03), 3),
                                  bahagian=name))
                beats_used += sb
            bars = math.ceil(beats_used / 4)
        sections.append(dict(nama=name, mula=t, bar=bars))
        t += bars * BAR
    return sections, lines, t


def kind_of(name):
    for k in ("intro", "rangkap", "prakorus", "bina", "korus", "hook", "jambatan", "penutup", "akhir"):
        if name.startswith(k):
            return k
    return name


def main():
    vokal = json.loads((BUILD / "vokal.json").read_text())
    sections, lines, total = plan(vokal)
    total += 3.0
    n = int(total * SR)
    L = lambda: np.zeros(n + SR * 4, np.float32)  # noqa: E731
    pads, keys, bs, lds, drm, fx = L(), L(), L(), L(), L(), L()

    for sec in sections:
        k = kind_of(sec["nama"])
        tr = 2 if sec["nama"] in ("bina2", "korus_akhir", "hook3", "penutup", "akhir") else 0
        prog = PROG.get(k, PROG["intro"]) if k not in ("bina", "akhir") else (["G"] if k == "bina" else ["C", "C"])
        if k == "rangkap":
            prog = PROG["rangkap"]
        for b in range(sec["bar"]):
            t0 = sec["mula"] + b * BAR
            ch = prog[b % len(prog)]
            root, tri = CHORD[ch]
            big = k in ("korus", "hook")
            # pad / strings
            if k != "akhir" or b == 0:
                for m in tri:
                    add(pads, (0.16 if big else 0.11) * pad(hz(m + tr), BAR + 1.2), t0)
                if k in ("korus", "hook", "prakorus", "bina", "penutup"):
                    for m in tri:
                        add(pads, 0.07 * strings(hz(m + 12 + tr), BAR + 0.6), t0)
            # piano
            if k in ("intro", "rangkap", "jambatan", "penutup"):
                arp = [tri[0] + 12, tri[1] + 12, tri[2] + 12, tri[1] + 24]
                steps = 4 if k == "jambatan" else 8
                for i in range(steps):
                    add(keys, 0.11 * pluck(hz(arp[i % 4] + tr)), t0 + i * BAR / steps)
            if k in ("korus", "hook", "prakorus"):
                for beat in (0, 2.5) if k != "prakorus" else (0, 1, 2, 3):
                    for m in tri:
                        add(keys, 0.07 * piano(hz(m + 12 + tr), 1.6), t0 + beat * BEAT)
            if k == "akhir" and b == 0:
                for m in tri + [tri[0] + 12]:
                    add(keys, 0.14 * piano(hz(m + 12 + tr), 4.5), t0)
            # bass
            if k in ("rangkap", "prakorus"):
                add(bs, 0.30 * bass(hz(root + tr), BAR * 0.95), t0)
            elif k in ("korus", "hook"):
                for i in range(8):
                    add(bs, 0.26 * bass(hz(root + tr + (12 if i % 4 == 3 else 0)), BEAT * 0.45), t0 + i * BEAT / 2)
            elif k == "penutup":
                add(bs, 0.25 * bass(hz(root + tr), BAR * 0.95), t0)
            # dram
            if k == "rangkap":
                second = sec["nama"] == "rangkap2"
                for beat in range(4):
                    if beat in (0, 2):
                        add(drm, 0.45 * kick(), t0 + beat * BEAT)
                    if second and beat in (1, 3):
                        add(drm, 0.22 * clap(), t0 + beat * BEAT)
                    for h in range(2):
                        add(drm, 0.08 * shaker(), t0 + beat * BEAT + h * BEAT / 2)
            elif k == "prakorus":
                for beat in range(4):
                    add(drm, 0.5 * kick(), t0 + beat * BEAT)
                    add(drm, 0.1 * hat(), t0 + beat * BEAT + BEAT / 2)
                for i, f0 in enumerate((180, 150, 120, 100)):
                    if b == sec["bar"] - 1:
                        add(drm, 0.25 * tom(f0), t0 + (2 + i * 0.5) * BEAT)
            elif k == "bina":
                for i in range(16):
                    add(drm, (0.08 + 0.3 * i / 16) * snare(), t0 + i * BEAT / 4)
                add(fx, 0.35 * riser(BAR), t0)
            elif k in ("korus", "hook"):
                for beat in range(4):
                    add(drm, 0.62 * kick(), t0 + beat * BEAT)                 # langkah kaki 4/4
                    if beat in (1, 3):
                        add(drm, 0.42 * snare() + 0.0, t0 + beat * BEAT)
                        add(drm, 0.25 * clap(), t0 + beat * BEAT)
                    add(drm, 0.10 * hat(), t0 + beat * BEAT + BEAT / 2)
                    if sec["nama"] in ("korus_akhir", "hook3"):
                        for s in range(4):
                            add(drm, 0.05 * shaker(), t0 + beat * BEAT + s * BEAT / 4)
                if b % 4 == 3:
                    for i, f0 in enumerate((160, 130, 105)):
                        add(drm, 0.22 * tom(f0), t0 + (3 + i / 3) * BEAT)
            elif k == "jambatan":
                for lub in (0, 0.28):  # degupan jantung
                    add(drm, (0.4 if lub == 0 else 0.28) * kick(), t0 + lub * BEAT)
                if b == 0:
                    add(fx, 0.3 * impact(), t0)
            elif k == "penutup":
                add(drm, 0.35 * kick(), t0)
                add(drm, 0.15 * snare(), t0 + 2 * BEAT)
        # aksen permulaan bahagian
        if kind_of(sec["nama"]) in ("korus",):
            add(fx, 0.35 * crash(), sec["mula"])
            add(fx, 0.4 * impact(), sec["mula"])
        if sec["nama"] == "akhir":
            add(fx, 0.3 * crash(), sec["mula"])
        # melodi
        if k == "korus":
            melody(lds, MELODI_KORUS, sec["mula"], tr, 0.05)
        if k == "hook":
            melody(lds, MELODI_HOOK, sec["mula"], tr, 0.11)
        if sec["nama"] == "intro":
            melody(lds, [[_, _, _, _, _, _, _, _], [_, _, _, _, _, _, _, _]] + MELODI_HOOK, sec["mula"], 0, 0.05)
        if sec["nama"] == "penutup":
            melody(lds, MELODI_HOOK, sec["mula"] + BAR, tr, 0.07)

    music = reverb(pads + keys + 0.6 * lds, 3.0, 0.4) + reverb(delay(0.4 * lds), 2.0, 0.3) + bs + drm + fx
    music = music[:n]

    # suara
    voice = np.zeros(n, np.float32)
    for ln in lines:
        a = read_wav(BUILD / "vokal" / ln["fail"])
        add(voice, a, ln["mula"])
    voice = voice / (np.abs(voice).max() + 1e-6) * 0.8
    voice_fx = voice + 0.25 * reverb(delay(voice, BEAT / 2, 0.25, 2), 1.6, 1.0)[:n]

    # ducking muzik bila suara aktif
    hop = SR // 100
    rms = np.sqrt(np.convolve(voice ** 2, np.ones(hop * 5) / (hop * 5), "same"))
    talk = np.convolve(np.clip(rms / 0.04, 0, 1), np.ones(SR // 5) / (SR // 5), "same")
    music *= 1 - 0.38 * np.clip(talk, 0, 1)

    t = np.arange(n) / SR
    music *= np.clip(t / 0.5, 0, 1) * np.clip((total - t) / 2.5, 0, 1)
    music *= 0.5 / (np.abs(music).max() + 1e-6)
    mix = music + voice_fx
    mix = np.tanh(mix * 1.2) / np.tanh(1.2)  # pengehad lembut

    OUT.mkdir(exist_ok=True)
    raw = BUILD / "campuran.wav"
    write_wav(raw, mix)
    wav = OUT / "terus-melangkah.wav"
    mp3 = OUT / "terus-melangkah.mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000",
                    str(wav)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-c:a", "libmp3lame", "-b:a", "256k",
                    "-metadata", "title=Terus Melangkah", "-metadata", "language=msa", str(mp3)], check=True)
    # lirik bermasa (LRC) + jadual untuk video lirik
    lrc = ["[ti:Terus Melangkah]"]
    for ln in lines:
        m, s = divmod(ln["mula"], 60)
        lrc.append(f"[{int(m):02d}:{s:05.2f}]{ln['teks']}")
    (OUT / "terus-melangkah.lrc").write_text("\n".join(lrc) + "\n")
    (BUILD / "susunan.json").write_text(json.dumps(dict(bpm=BPM, jumlah=total, bahagian=sections, baris=lines),
                                                   ensure_ascii=False, indent=1))
    for s in sections:
        print(f"{s['nama']:12s} {s['mula']:6.2f}s  {s['bar']} bar")
    print(f"Jumlah {total:.1f}s -> {mp3}")


if __name__ == "__main__":
    main()
