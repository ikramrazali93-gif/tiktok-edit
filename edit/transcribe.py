import sys, json
from faster_whisper import WhisperModel
src, out, lang = sys.argv[1], sys.argv[2], (sys.argv[3] if len(sys.argv)>3 else None)
m = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=4)
import numpy as np, wave
wf=wave.open(src); audio=np.frombuffer(wf.readframes(wf.getnframes()),np.int16).astype(np.float32)/32768
segs, info = m.transcribe(audio, language=lang, word_timestamps=True, vad_filter=False, beam_size=5)
res = {"language": info.language, "segments": []}
for s in segs:
    res["segments"].append({"start": s.start, "end": s.end, "text": s.text,
        "words": [{"w": w.word, "s": round(w.start,2), "e": round(w.end,2), "p": round(w.probability,2)} for w in s.words]})
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text}", flush=True)
json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
