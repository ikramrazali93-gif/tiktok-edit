"""Narasi suara lelaki matang (Malaysian-TTS-0.6B, penutur 'husein') + masa setiap perkataan.

Setiap ayat dijana beberapa kali; cubaan yang paling tepat (disemak dengan Whisper) dipilih.
Kemudian suara diproses supaya lebih perlahan, dalam dan hangat — gaya lelaki 50-an yang bijaksana.

Output: build/narasi.wav, build/masa.json (format sama seperti suara.py)
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT.parent / "karung-beras"))
import suara  # noqa: E402  (baca_wav, tulis_wav, masa_perkataan)

BUILD = ROOT / "build"
CACHE = BUILD / "tts_lelaki"
SR = suara.SR
PENUTUR = "husein"
CUBAAN = 10         # bilangan maksimum cubaan bagi setiap ayat
LAJU = 0.9          # lebih perlahan = lebih tenang
PIC = 0.95          # rendahkan nada ~1 semiton
JEDA_AYAT = 0.38    # senyap antara ayat dalam satu baris
JEDA = 0.45         # senyap lalai antara baris
MULA = 0.6

_tts = None


def load_tts():
    global _tts
    if _tts:
        return _tts
    import torch
    from distilcodec import DistilCodec
    from huggingface_hub import hf_hub_download
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.set_num_threads(4)
    cfg = json.load(open(hf_hub_download("IDEA-Emdoor/DistilCodec-v1.0", "model_config.json")))
    codec = DistilCodec(cfg)
    codec.device = torch.device("cpu")  # pustaka asal menganggap CUDA
    sd = DistilCodec.load_checkpoint(hf_hub_download("IDEA-Emdoor/DistilCodec-v1.0", "g_00204000"), codec.device)
    codec.generator.load_state_dict(sd["generator"])
    codec.encoder.load_state_dict(sd["encoder"])
    codec.quantizer.load_state_dict(sd["quantizer"])
    codec.move_to_cuda()
    codec.eval()
    tok = AutoTokenizer.from_pretrained("mesolitica/Malaysian-TTS-0.6B-v1")
    model = AutoModelForCausalLM.from_pretrained("mesolitica/Malaysian-TTS-0.6B-v1", dtype=torch.float32).eval()
    _tts = (torch, codec, tok, model)
    return _tts


def synth(text, seed):
    """Jana satu ayat -> numpy float32 @ 24 kHz (dengan cache)."""
    key = hashlib.md5(f"{PENUTUR}|{text}|{seed}".encode()).hexdigest()[:12]
    path = CACHE / f"{key}.wav"
    if path.exists():
        return path
    torch, codec, tok, model = load_tts()
    torch.manual_seed(seed)
    enc = tok(f"<|im_start|>{PENUTUR}: {text}<|speech_start|>", return_tensors="pt", add_special_tokens=False)
    with torch.no_grad():
        out = model.generate(**enc, max_new_tokens=1024, temperature=0.7, do_sample=True, repetition_penalty=1.1)
        speech = tok.decode(out[0]).split("<|speech_start|>")[-1]
        codes = list(map(int, re.findall(r"speech_(\d+)", speech)))
        c = torch.tensor(codes, dtype=torch.int64).unsqueeze(0).unsqueeze(0).unsqueeze(-1)
        y = codec.generator(codec.quantizer.decode(indices=c))[0, 0].numpy()
    import soundfile as sf
    sf.write(path, y, 24000)
    return path


def norm_words(s):
    return [w for w in re.sub(r"[^a-z0-9\s-]", " ", s.lower()).split() if w]


def score(whisper, path, text):
    """Kadar ralat perkataan (0 = sempurna)."""
    import difflib
    import librosa
    y, _ = librosa.load(path, sr=16000)
    segs, _ = whisper.transcribe(y, language="ms")
    got = norm_words(" ".join(s.text for s in segs))
    want = norm_words(text)
    sm = difflib.SequenceMatcher(a=want, b=got, autojunk=False)
    return 1 - sum(b.size for b in sm.get_matching_blocks()) / max(1, len(want)), " ".join(got)


def polish(src, dst):
    """Perlahan, nada rendah, hangat, gema bilik halus."""
    suara.ffmpeg(
        "-i", str(src), "-af",
        f"silenceremove=start_periods=1:start_threshold=-42dB,areverse,silenceremove=start_periods=1:start_threshold=-42dB,areverse,"
        f"asetrate=24000*{PIC},aresample={SR},atempo={LAJU / PIC:.4f},"
        "highpass=f=70,bass=g=3:f=150,equalizer=f=3200:t=q:w=1.2:g=-1.5,treble=g=-2:f=8000,"
        "acompressor=threshold=-20dB:ratio=2.5:attack=15:release=200,"
        "aecho=0.85:0.5:38|71:0.10|0.06",
        "-ac", "1", "-ar", str(SR), str(dst))


def ayat(teks):
    return [s.strip() for s in re.findall(r"[^.?!]+[.?!]*", teks) if s.strip()]


def main():
    from faster_whisper import WhisperModel

    BUILD.mkdir(exist_ok=True)
    CACHE.mkdir(exist_ok=True)
    whisper = WhisperModel("small", device="cpu", compute_type="int8")
    skrip = json.loads((ROOT / "skrip.json").read_text())

    potongan = [np.zeros(int(MULA * SR), np.float32)]
    t = MULA
    hasil = []
    for n, baris in enumerate(skrip):
        bahagian = []
        for s in ayat(baris["teks"]):
            best = None
            for seed in range(1, CUBAAN + 1):
                path = synth(s.replace("...", ",").replace("…", ","), seed)
                err, heard = score(whisper, path, s)
                if best is None or err < best[0]:
                    best = (err, path, heard)
                if err == 0:
                    break
            print(f"  {s!r} -> ralat {best[0]:.2f} ({best[2]})", flush=True)
            out = CACHE / (best[1].stem + "_p.wav")
            polish(best[1], out)
            bahagian += [suara.baca_wav(out), np.zeros(int(JEDA_AYAT * SR), np.float32)]
        a = np.concatenate(bahagian[:-1])
        kata = baris["teks"].split()
        masa = suara.masa_perkataan(whisper, a, kata)
        hasil.append({
            "babak": baris["babak"], "teks": baris["teks"], "mula": round(t, 3), "tamat": round(t + len(a) / SR, 3),
            "kata": [{"k": k, "mula": round(t + s0, 3), "tamat": round(t + e0, 3)} for k, (s0, e0) in zip(kata, masa)],
        })
        jeda = baris.get("jeda", JEDA)
        potongan += [a, np.zeros(int(jeda * SR), np.float32)]
        t += len(a) / SR + jeda
        print(f"{n:2d} {baris['babak']:10s} {len(a) / SR:5.2f}s", flush=True)

    potongan.append(np.zeros(int(1.2 * SR), np.float32))
    v = np.concatenate(potongan)
    suara.tulis_wav(BUILD / "narasi.wav", v * (0.9 / max(1e-6, np.abs(v).max())))
    (BUILD / "masa.json").write_text(json.dumps({"jumlah": round(len(v) / SR, 3), "baris": hasil}, ensure_ascii=False, indent=1))
    print(f"Jumlah: {len(v) / SR:.2f}s")


if __name__ == "__main__":
    main()
