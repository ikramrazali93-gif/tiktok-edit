"""Muzik latar yang naik berperingkat + kesan bunyi, dicampur dengan narasi.

Output: build/muzik.wav, build/audio.wav
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT.parent / "karung-beras"))
from muzik import SR, add, env, hz, pad, pluck, read_wav, reverb, write_wav  # noqa: E402

BUILD = ROOT / "build"
KAD_AKHIR = 4.2  # mesti sama dengan video.py
BPM = 96
BEAT = 60 / BPM
BAR = 4 * BEAT
# Am - F - C - G
KORD = [[57, 60, 64], [53, 57, 60], [48, 55, 60], [55, 59, 62]]
rng = np.random.default_rng(5)


def band_noise(dur, lo, hi):
    n = int(dur * SR)
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    spec[(f < lo) | (f > hi)] = 0
    x = np.fft.irfft(spec, n).astype(np.float32)
    return x / (np.abs(x).max() + 1e-9)


def kick(dur=0.45):
    t = np.arange(int(dur * SR)) / SR
    f = 45 + 110 * np.exp(-t * 30)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)).astype(np.float32)


def clap():
    x = band_noise(0.25, 900, 6000)
    t = np.arange(len(x)) / SR
    return x * np.exp(-t * 22)


def hat():
    x = band_noise(0.06, 6000, 14000)
    return x * np.exp(-np.arange(len(x)) / SR * 70)


def tick():
    x = band_noise(0.03, 2500, 9000)
    return x * np.exp(-np.arange(len(x)) / SR * 200)


def whoosh(dur=0.5):
    x = band_noise(dur, 250, 3500)
    t = np.linspace(0, 1, len(x))
    return x * np.sin(np.pi * t) ** 2


def impact():
    t = np.arange(int(1.6 * SR)) / SR
    boom = np.sin(2 * np.pi * (38 + 60 * np.exp(-t * 6)) * t) * np.exp(-t * 3)
    return (boom + 0.35 * band_noise(1.6, 60, 2000) * np.exp(-t * 7)).astype(np.float32)


def shatter():
    t = np.arange(int(1.0 * SR)) / SR
    x = band_noise(1.0, 3000, 15000) * np.exp(-t * 6)
    for k in range(10):  # serpihan
        at = rng.uniform(0, 0.5)
        add(x, 0.6 * band_noise(0.04, 4000, 12000) * np.exp(-np.arange(int(0.04 * SR)) / SR * 90), at)
    return x


def beep():
    t = np.arange(int(0.12 * SR)) / SR
    return (np.sin(2 * np.pi * 1760 * t) * env(len(t), 0.005, 0.03)).astype(np.float32)


def riser(dur):
    t = np.arange(int(dur * SR)) / SR
    f = 180 * (6 ** (t / dur))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3
    x = (tone + band_noise(dur, 800, 9000) * 0.6) * (t / dur) ** 2
    return x.astype(np.float32)


def main():
    masa = json.loads((BUILD / "masa.json").read_text())
    by = {b["babak"]: b for b in masa["baris"]}
    word = lambda b, p: next(w["mula"] for w in by[b]["kata"] if w["k"].lower().startswith(p))
    dur = masa["jumlah"] + KAD_AKHIR
    n = int(dur * SR)
    t_pergi = word("pergi", "keputusan")
    sec_b = by["gementar"]["mula"]
    sec_c = by["pilih"]["mula"] - 0.15
    sec_d = by["esok"]["mula"] - 0.15

    music = np.zeros(n + SR * 4, np.float32)
    drums = np.zeros_like(music)
    nbar = int(dur / BAR) + 2
    for b in range(nbar):
        t0 = b * BAR
        if sec_d - 0.2 <= t0 < t_pergi - 0.1:
            continue  # senyap sebelum 'pergi' (hanya pad panjang)
        chord = KORD[b % 4]
        big = t0 >= t_pergi - 0.1
        for m in chord:
            add(music, (0.3 if big else 0.2) * pad(hz(m), BAR + 1.5), t0)
        add(music, 0.3 * pad(hz(chord[0] - 12), BAR + 1.5), t0)
        steps = 8 if t0 >= sec_b or big else 4
        arp = [chord[0] + 12, chord[1] + 12, chord[2] + 12, chord[1] + 24]
        for i in range(steps):
            add(music, 0.15 * pluck(hz(arp[i % 4])), t0 + i * BAR / steps)
        if big:
            for m in chord:
                add(music, 0.12 * pluck(hz(m + 24), 3.0), t0)
    # pad panjang semasa babak 'esok' (bina ketegangan)
    add(music, 0.25 * pad(hz(52), t_pergi - sec_d + 1.2), sec_d)
    add(music, 0.2 * pad(hz(59), t_pergi - sec_d + 1.2), sec_d)
    # dram
    t = sec_b
    i = 0
    while t < dur - 3:
        if sec_d - 0.1 <= t < t_pergi - 0.05:
            t += BEAT
            i += 1
            continue
        level = 0.45 if t < sec_c else 0.7
        add(drums, level * kick(), t)
        if t >= sec_c:
            if i % 2 == 1:
                add(drums, 0.35 * clap(), t)
            for h in range(2):
                add(drums, 0.12 * hat(), t + h * BEAT / 2 + BEAT / 4)
        t += BEAT
        i += 1
    music = reverb(music)[: len(drums)] + drums
    tt = np.arange(len(music)) / SR
    music *= np.clip(tt / 1.0, 0, 1) * np.clip((dur - tt) / 2.0, 0, 1)
    music = music[:n]
    music *= 0.32 / (np.abs(music).max() + 1e-6)

    sfx = np.zeros(n + SR * 2, np.float32)
    starts = [b["mula"] - 0.15 for b in masa["baris"][1:]]
    for s in starts:
        add(sfx, 0.22 * whoosh(0.45), s - 0.1)
    for s in (word("hook", "bersedia"), word("keputusan", "keputusan"), word("takdatang", "datang"), t_pergi):
        add(sfx, 0.55 * impact(), s)
    add(sfx, 0.35 * shatter(), word("takdatang", "datang"))
    t = by["tunggu"]["mula"]
    while t < word("takdatang", "datang"):
        add(sfx, 0.25 * tick(), t)
        t += 0.5
    t = by["esok"]["mula"] - 0.15
    while t < by["pergi"]["mula"] - 0.3:
        for j in range(3):
            add(sfx, 0.12 * beep(), t + j * 0.15)
        t += 0.8
    add(sfx, 0.4 * riser(t_pergi - by["pergi"]["mula"] + 0.3), by["pergi"]["mula"] - 0.3)
    add(sfx, 0.25 * whoosh(0.6), t_pergi + 0.45)
    sfx = sfx[:n]

    write_wav(BUILD / "muzik.wav", music)
    voice = read_wav(BUILD / "narasi.wav")
    # ducking: rendahkan muzik ~6 dB ketika narator bercakap
    hop = SR // 100
    nv = min(len(voice), n)
    rms = np.sqrt(np.convolve(voice[:nv] ** 2, np.ones(hop * 5) / (hop * 5), "same"))
    talk = np.clip(rms / 0.04, 0, 1)
    k = np.ones(SR // 4) / (SR // 4)
    talk = np.convolve(talk, k, "same")  # lancarkan supaya tidak berdenyut
    duck = np.ones(n, np.float32)
    duck[:nv] = 1 - 0.5 * np.clip(talk, 0, 1)
    music = music * duck
    mix = music + sfx
    mix[: len(voice)] += voice[:n]
    mix *= 0.95 / max(1.0, np.abs(mix).max())
    write_wav(BUILD / "audio.wav", mix)
    print(f"audio.wav {dur:.2f}s")


if __name__ == "__main__":
    main()
