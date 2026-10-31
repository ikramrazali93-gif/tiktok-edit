"""Synthesised SFX + music bed for kusyen duduk video 5 ("Hygge kait hangat"). No licensed audio.

Usage: python3 sfx.py <out_dir>
Writes knit.wav (soft woolly pop for the knit tags), chime.wav (warm low bell for the hook tag and end card),
crackle.wav (short fireplace crackle for the edge-only glow between sections) and music.wav (slow, warm
felt-piano + pad bed, ~72 bpm). The user can swap the music for a trending sound in TikTok.
"""
import os
import sys
import wave

import numpy as np

SR = 48000
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
rng = np.random.default_rng(11)


def save(name, x):
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.9
    st = np.stack([x, x], 1)
    w = wave.open(os.path.join(out, name + ".wav"), "w")
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes()); w.close()


def t(d):
    return np.arange(int(d * SR)) / SR


def smooth(x, n):
    """Cheap lowpass: moving average over n samples."""
    k = np.ones(n) / n
    return np.convolve(x, k, "same")


def bell(f0, d, decay=3.5):
    tt = t(d)
    x = sum(a * np.sin(2 * np.pi * f0 * m * tt) * np.exp(-tt * decay * k)
            for a, m, k in [(1, 1, 1), (0.35, 2.0, 1.6), (0.18, 3.01, 2.4), (0.08, 4.2, 3.2)])
    return x * np.minimum(1, tt * 300)


def knit():
    """Soft woolly pop: a muffled low thump with a little fuzzy noise, like a pompom landing."""
    tt = t(0.22)
    thump = np.sin(2 * np.pi * np.cumsum(220 * np.exp(-tt * 18) + 110) / SR) * np.exp(-tt * 22)
    fuzz = smooth(rng.standard_normal(len(tt)), 24) * np.exp(-tt * 30) * 0.8
    return thump + fuzz


def chime():
    """Warm low bell pair (G4 + D5), slow decay."""
    x = np.zeros(int(1.6 * SR))
    a = bell(392.0, 1.6) * 0.8
    b = bell(587.3, 1.4) * 0.5
    x[:len(a)] += a
    o = int(0.11 * SR)
    x[o:o + len(b)] += b[:len(x) - o]
    return x


def crackle():
    """Short fireplace crackle: sparse clicks over a soft warm hiss, fading in and out."""
    d = 0.9
    tt = t(d)
    hiss = smooth(rng.standard_normal(len(tt)), 12) * 0.12
    x = hiss.copy()
    for _ in range(26):
        o = int(rng.uniform(0, d - 0.02) * SR)
        n = int(rng.uniform(0.002, 0.008) * SR)
        c = rng.standard_normal(n) * np.exp(-np.arange(n) / (n / 4)) * rng.uniform(0.3, 1.0)
        x[o:o + n] += c
    env = np.sin(np.pi * tt / d) ** 0.8
    return x * env


def music(d=40.0, bpm=72):
    """Slow warm bed: felt-piano chords (Fmaj7 - Em7 - Dm7 - Cmaj7, one bar each), a soft pad and a low bass."""
    beat = 60 / bpm
    bar = 4 * beat
    n = int(d * SR)
    x = np.zeros(n)
    tt_all = np.arange(n) / SR
    chords = [[174.61, 220.00, 261.63, 329.63], [164.81, 196.00, 246.94, 293.66],
              [146.83, 174.61, 220.00, 261.63], [130.81, 164.81, 196.00, 246.94]]
    roots = [87.31, 82.41, 73.42, 65.41]
    for b in range(int(np.ceil(d / bar))):
        c, r = chords[b % 4], roots[b % 4]
        o = int(b * bar * SR)
        L = min(int(bar * SR), n - o)
        if L <= 0:
            break
        tt = np.arange(L) / SR
        env = np.minimum(1, tt / 0.8) * np.minimum(1, (bar - tt) / 0.6)
        pad = sum(np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 1.004 * tt) for f in c)
        x[o:o + L] += pad * env * 0.035
        bl = min(int(bar * SR), n - o)
        bt = np.arange(bl) / SR
        x[o:o + bl] += np.sin(2 * np.pi * r * bt) * np.exp(-bt * 0.9) * np.minimum(1, bt * 60) * 0.16
        for k, f in enumerate([c[1] * 2, c[2] * 2, c[3] * 2, c[2] * 2]):     # felt-piano notes on each beat
            po = o + int(k * beat * SR)
            s = bell(f, 1.2, decay=2.2) * 0.12
            pl = min(len(s), n - po)
            if pl > 0:
                x[po:po + pl] += smooth(s, 6)[:pl]
    fade = np.minimum(1, tt_all / 1.5) * np.minimum(1, (d - tt_all) / 2.0)
    return x * fade


save("knit", knit())
save("chime", chime())
save("crackle", crackle())
save("music", music())
print("sfx ->", out)
