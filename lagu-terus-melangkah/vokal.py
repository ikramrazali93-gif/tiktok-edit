"""Jana suara deklamasi bagi setiap baris lirik (suara lelaki matang yang sama seperti video 'Bersedia').

Output: build/vokal/NN.wav + build/vokal.json (tempoh & masa perkataan setiap baris)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT.parent / "bersedia"))
import suara_lelaki as sl  # noqa: E402

BUILD = ROOT / "build"
OUT = BUILD / "vokal"
sl.CACHE = BUILD / "tts_lelaki"   # cache TTS sendiri
sl.CUBAAN = 16
LAJU_BIASA = 0.86                  # deklamasi berirama yang tenang
LAJU_JAMBATAN = 0.76               # jambatan dibaca lebih perlahan


def main():
    from faster_whisper import WhisperModel

    OUT.mkdir(parents=True, exist_ok=True)
    sl.CACHE.mkdir(parents=True, exist_ok=True)
    whisper = WhisperModel("small", device="cpu", compute_type="int8")
    lirik = json.loads((ROOT / "lirik.json").read_text())
    hasil, done = [], {}
    n = 0
    for bah in lirik["bahagian"]:
        for teks in bah["baris"]:
            laju = LAJU_JAMBATAN if bah["nama"] == "jambatan" else LAJU_BIASA
            key = (teks, laju)
            if key not in done:
                best = None
                for seed in range(1, sl.CUBAAN + 1):
                    path = sl.synth(teks, seed)
                    err, heard = sl.score(whisper, path, teks)
                    if best is None or err < best[0]:
                        best = (err, path, heard)
                    if err == 0:
                        break
                sl.LAJU = laju
                out = OUT / f"{n:02d}.wav"
                sl.polish(best[1], out)
                a = sl.suara.baca_wav(out)
                kata = teks.split()
                masa = sl.suara.masa_perkataan(whisper, a, kata)
                done[key] = dict(fail=out.name, tempoh=round(len(a) / sl.SR, 3), ralat=round(best[0], 2),
                                 kata=[{"k": k, "mula": s, "tamat": e} for k, (s, e) in zip(kata, masa)])
                print(f"{n:02d} {bah['nama']:12s} {done[key]['tempoh']:5.2f}s ralat {best[0]:.2f}  {teks}  [{best[2]}]", flush=True)
                n += 1
            hasil.append(dict(bahagian=bah["nama"], teks=teks, **done[key]))
    (BUILD / "vokal.json").write_text(json.dumps(hasil, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
