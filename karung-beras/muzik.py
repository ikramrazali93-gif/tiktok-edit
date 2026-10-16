"""Jana muzik latar (pad + piano arpeggio, bebas hak cipta) dan campur dengan narasi.

Output: build/muzik.wav, build/audio.wav (narasi + muzik + kesan bunyi)
"""
import json
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent
BUILD = ROOT / "build"
SR = 48000
KAD_AKHIR = 2.6  # mesti sama dengan video.py

# Am - F - C - G (setiap kord 4 saat)
KORD = [[57, 60, 64], [53, 57, 60], [48, 55, 60], [55, 59, 62]]
BAR = 4.0


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env(n, a, r):
    e = np.ones(n, np.float32)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def pad(freq, dur):
    t = np.arange(int(dur * SR)) / SR
    x = sum(np.sin(2 * np.pi * freq * d * t + p) for d, p in ((1.0, 0), (1.004, 1.3), (0.996, 2.1)))
    x += 0.25 * np.sin(2 * np.pi * freq * 2 * t)
    return (x / 3.3 * env(len(t), 1.4, 1.8)).astype(np.float32)


def pluck(freq, dur=2.2):
    t = np.arange(int(dur * SR)) / SR
    x = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t) * np.exp(-t * 3) + 0.12 * np.sin(6 * np.pi * freq * t) * np.exp(-t * 5)
    return (x * np.exp(-t * 2.2) * env(len(t), 0.004, 0.2)).astype(np.float32)


def reverb(x, sec=2.8, mix=0.35):
    rng = np.random.default_rng(1)
    n = int(sec * SR)
    ir = rng.standard_normal(n).astype(np.float32) * np.exp(-np.linspace(0, 7, n)).astype(np.float32)
    ir /= np.sqrt((ir ** 2).sum())
    size = 1 << int(np.ceil(np.log2(len(x) + n)))
    wet = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)].astype(np.float32)
    return (1 - mix) * x + mix * wet * 3


def add(buf, sig, at):
    i = int(at * SR)
    j = min(len(buf), i + len(sig))
    if i < j:
        buf[i:j] += sig[: j - i]


def read_wav(path):
    with wave.open(str(path)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768


def write_wav(path, x, ch=1):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def main():
    masa = json.loads((BUILD / "masa.json").read_text())
    dur = masa["jumlah"] + KAD_AKHIR
    n = int(dur * SR)
    music = np.zeros(n + SR * 4, np.float32)
    bars = int(np.ceil(dur / BAR)) + 1
    for b in range(bars):
        chord = KORD[b % 4]
        t0 = b * BAR
        for m in chord:
            add(music, 0.22 * pad(hz(m), BAR + 1.8), t0)
        add(music, 0.30 * pad(hz(chord[0] - 12), BAR + 1.8), t0)
        if b >= 1:  # piano masuk selepas bar pertama
            arp = [chord[0] + 12, chord[1] + 12, chord[2] + 12, chord[1] + 24]
            for i in range(8):
                add(music, 0.16 * pluck(hz(arp[i % 4])), t0 + i * BAR / 8)
    music = reverb(music)[:n]
    # dinamik: lembut di awal, naik pada babak refleksi, pudar di hujung
    t = np.arange(n) / SR
    starts = {b["babak"]: b["mula"] for b in masa["baris"]}
    level = 0.55 + 0.45 * np.clip((t - starts["kafan"] + 2) / 4, 0, 1)
    level *= np.clip(t / 2.0, 0, 1) * np.clip((dur - t) / 2.5, 0, 1)
    music *= level
    music *= 0.22 / (np.abs(music).max() + 1e-6)
    write_wav(BUILD / "muzik.wav", music)

    voice = read_wav(BUILD / "narasi.wav")
    mix = music.copy()
    mix[: len(voice)] += voice[: n]
    # kesan bunyi: karung jatuh (selari dengan video.py: t_land = 1.2)
    tt = np.arange(int(0.6 * SR)) / SR
    thud = (np.sin(2 * np.pi * 70 * tt) * np.exp(-tt * 14) + 0.3 * np.random.default_rng(2).standard_normal(len(tt)) * np.exp(-tt * 30)).astype(np.float32)
    add(mix, 0.5 * thud, 1.2)
    mix *= 0.95 / max(1.0, np.abs(mix).max())
    write_wav(BUILD / "audio.wav", mix)
    print(f"audio.wav {dur:.2f}s")


if __name__ == "__main__":
    main()
