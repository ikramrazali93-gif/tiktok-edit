"""Jana suara narator (Google TTS, Bahasa Melayu) + masa setiap perkataan.

Output:
  build/narasi.wav  - suara penuh
  build/masa.json   - masa mula/tamat setiap baris & setiap perkataan
"""
import difflib
import hashlib
import json
import re
import subprocess
import wave
from pathlib import Path

import numpy as np
from gtts import gTTS

ROOT = Path(__file__).parent
BUILD = ROOT / "build"
SR = 48000
LAJU = 1.32      # gTTS agak perlahan; cepatkan supaya rentak sesuai untuk reel
PIC = 0.95       # rendahkan nada sedikit supaya lebih tenang
JEDA = 0.28      # senyap antara baris (saat)
MULA = 0.4       # senyap di awal video


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def baca_wav(path):
    with wave.open(str(path)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768


def tulis_wav(path, a):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def masa_perkataan(model, audio, kata):
    """Jajarkan perkataan skrip dengan cap masa Whisper; selebihnya diinterpolasi."""
    a16 = audio[:: SR // 16000]
    segs, _ = model.transcribe(a16, language="ms", word_timestamps=True)
    dikesan = [w for s in segs for w in s.words]
    jangka = len(audio) / SR
    masa = [None] * len(kata)
    sm = difflib.SequenceMatcher(a=[norm(k) for k in kata], b=[norm(w.word) for w in dikesan], autojunk=False)
    for blok in sm.get_matching_blocks():
        for i in range(blok.size):
            w = dikesan[blok.b + i]
            masa[blok.a + i] = (w.start, w.end)
    # isi tempat kosong secara berkadar ikut panjang perkataan
    titik = [(-1, 0.0)] + [(i, m[0]) for i, m in enumerate(masa) if m] + [(len(kata), jangka)]
    for (i0, t0), (i1, t1) in zip(titik, titik[1:]):
        if i1 - i0 <= 1:
            continue
        mula_t = masa[i0][1] if i0 >= 0 else t0
        berat = [len(kata[j]) + 2 for j in range(i0 + 1, i1)]
        jumlah = sum(berat)
        t = mula_t
        for j, b in zip(range(i0 + 1, i1), berat):
            d = (t1 - mula_t) * b / jumlah
            masa[j] = (t, t + d)
            t += d
    return [(round(s, 3), round(e, 3)) for s, e in masa]


def main():
    from faster_whisper import WhisperModel

    BUILD.mkdir(exist_ok=True)
    skrip = json.loads((ROOT / "skrip.json").read_text())
    model = WhisperModel("small", device="cpu", compute_type="int8")

    potongan = [np.zeros(int(MULA * SR), np.float32)]
    t = MULA
    hasil = []
    for n, baris in enumerate(skrip):
        mp3 = BUILD / f"baris{n:02d}_{hashlib.md5(baris['teks'].encode()).hexdigest()[:8]}.mp3"
        wav = BUILD / f"baris{n:02d}.wav"
        if not mp3.exists():
            gTTS(baris["teks"], lang="ms").save(str(mp3))
        ffmpeg("-i", str(mp3), "-af",
               f"asetrate=24000*{PIC},aresample={SR},atempo={LAJU / PIC:.4f},"
               "silenceremove=start_periods=1:start_threshold=-45dB,"
               "areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
               "-ac", "1", "-ar", str(SR), str(wav))
        a = baca_wav(wav)
        kata = baris["teks"].split()
        masa = masa_perkataan(model, a, kata)
        hasil.append({
            "babak": baris["babak"],
            "teks": baris["teks"],
            "mula": round(t, 3),
            "tamat": round(t + len(a) / SR, 3),
            "kata": [{"k": k, "mula": round(t + s, 3), "tamat": round(t + e, 3)} for k, (s, e) in zip(kata, masa)],
        })
        jeda = baris.get("jeda", JEDA)  # jeda khas selepas baris ini (pilihan)
        potongan += [a, np.zeros(int(jeda * SR), np.float32)]
        t += len(a) / SR + jeda
        print(f"{n:2d} {baris['babak']:8s} {len(a) / SR:5.2f}s")

    potongan.append(np.zeros(int(1.2 * SR), np.float32))
    suara = np.concatenate(potongan)
    tulis_wav(BUILD / "narasi.wav", suara * (0.9 / max(1e-6, np.abs(suara).max())))
    (BUILD / "masa.json").write_text(json.dumps({"jumlah": round(len(suara) / SR, 3), "baris": hasil}, ensure_ascii=False, indent=1))
    print(f"Jumlah: {len(suara) / SR:.2f}s")


if __name__ == "__main__":
    main()
