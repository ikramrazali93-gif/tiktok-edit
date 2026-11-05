"""Sunting video 'Jumpa Totoro' daripada edl.json.

  python3 sunting.py MEDIA_DIR --pratonton        # pratonton 540x960 + kod masa & label shot
  python3 sunting.py MEDIA_DIR --akhir [--vo FAIL] # render akhir 1080x1920 (selepas diluluskan)

MEDIA_DIR = folder yang mengandungi klip & foto asal (tidak disimpan dalam repo).
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).parent
BUILD = ROOT / "build"
FPS = 30
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
GRADE = "eq=contrast=1.06:saturation=1.18:gamma=1.02"   # warna lebih hidup, sesuai suasana malam
AMBIEN = 0.35   # audio asal direndahkan (ruang untuk suara latar)


def run(cmd):
    subprocess.run(cmd, check=True)


def enc_args(final):
    q = ["-crf", "18", "-preset", "slow"] if final else ["-crf", "24", "-preset", "veryfast"]
    return ["-c:v", "libx264", *q, "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]


def stabilised(src):
    """Stabilkan klip penuh sekali (vidstab 2 laluan) dan simpan dalam cache."""
    out = BUILD / "stabil" / src.name
    if out.exists():
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    trf = out.with_suffix(".trf")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", f"vidstabdetect=shakiness=8:accuracy=15:result={trf}", "-f", "null", "-"])
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf",
         f"vidstabtransform=input={trf}:smoothing=18:zoom=4:optzoom=0,unsharp=5:5:0.6",
         "-c:v", "libx264", "-crf", "14", "-preset", "fast", "-c:a", "copy", str(out)])
    return out


def seg_video(s, media, out, W, H, final):
    src = media / s["fail"]
    if s.get("stabil"):
        src = stabilised(src)
    lj = s["laju"]
    dur = (s["hingga"] - s["dari"]) / lj
    vf = f"setpts=(PTS-STARTPTS)/{lj},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},{GRADE},fps={FPS}"
    af = f"asetpts=PTS-STARTPTS,atempo={lj},volume={AMBIEN},afade=t=in:d=0.04,afade=t=out:st={max(0, dur - 0.05):.3f}:d=0.05"
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(s["dari"]), "-to", str(s["hingga"]), "-i", str(src),
         "-vf", vf, "-af", af, "-t", f"{dur:.3f}", *enc_args(final), str(out)])


def seg_foto(s, media, out, W, H, final):
    im = ImageOps.exif_transpose(Image.open(media / s["fail"])).convert("RGB")
    n = int(round(s["tempoh"] * FPS))
    fx, fy = s.get("fokus", [0.5, 0.5])
    # sumber dikecilkan dulu (2x saiz output) supaya pantas
    scale = 2 * H / im.height if im.height / im.width >= H / W else 2 * W / im.width
    if s.get("isi") == "kabur":
        bg = ImageOps.fit(im, (W * 2, H * 2)).filter(ImageFilter.GaussianBlur(40))
        bg = Image.eval(bg, lambda v: int(v * 0.55))
        fg = im.resize((W * 2, int(im.height * W * 2 / im.width)), Image.LANCZOS)
        bg.paste(fg, (0, (H * 2 - fg.height) // 2))
        im = bg
    else:
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    iw, ih = im.size
    base = min(iw / W, ih / H)  # tetingkap 'cover' terbesar
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-f", "lavfi", "-t", f"{n / FPS:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
                             "-vf", GRADE, *enc_args(final), "-shortest", str(out)], stdin=subprocess.PIPE)
    g = s.get("gerak", "zoom-in")
    for i in range(n):
        u = i / max(1, n - 1)
        e = u * u * (3 - 2 * u)
        if g == "zoom-in":
            z = 1.0 + 0.10 * e
        elif g == "zoom-out":
            z = 1.12 - 0.12 * e
        elif g == "punch":       # hentakan zoom pantas kemudian perlahan
            z = 1.14 - 0.10 * (1 - (1 - u) ** 3)
        else:
            z = 1.04
        cw, ch = W * base / z, H * base / z
        cx = fx * iw
        cy = fy * ih
        if g == "pan-down":
            cy = (0.25 + 0.5 * e) * ih
        x0 = min(max(cx - cw / 2, 0), iw - cw)
        y0 = min(max(cy - ch / 2, 0), ih - ch)
        fr = im.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))
        proc.stdin.write(np.asarray(fr, np.uint8).tobytes())
    proc.stdin.close()
    proc.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("media", type=Path)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--pratonton", action="store_true")
    g.add_argument("--akhir", action="store_true")
    ap.add_argument("--vo", type=Path, help="fail suara latar (untuk render akhir)")
    a = ap.parse_args()
    final = a.akhir
    W, H = (1080, 1920) if final else (540, 960)
    edl = json.loads((ROOT / "edl.json").read_text())
    tmp = BUILD / ("akhir" if final else "pratonton")
    tmp.mkdir(parents=True, exist_ok=True)
    parts, t, marks = [], 0.0, []
    for i, s in enumerate(edl["segmen"]):
        out = tmp / f"seg{i:02d}.mp4"
        (seg_video if s["jenis"] == "video" else seg_foto)(s, a.media, out, W, H, final)
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                                 capture_output=True, text=True).stdout)
        marks.append((t, t + d, i + 1, s["label"]))
        print(f"{i + 1:2d} {t:6.2f}-{t + d:6.2f}  {s['label']}", flush=True)
        t += d
        parts.append(out)
    (tmp / "senarai.txt").write_text("".join(f"file '{p.name}'\n" for p in parts))
    joined = tmp / "gabung.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "senarai.txt"), "-c", "copy", str(joined)])
    (BUILD / "shot.json").write_text(json.dumps([dict(no=n, mula=round(s0, 2), tamat=round(s1, 2), label=l) for s0, s1, n, l in marks],
                                                ensure_ascii=False, indent=1))
    if not final:
        # kod masa + label shot, untuk bantu tulis skrip suara latar
        draws = [f"drawtext=fontfile={FONT}:text='%{{pts\\:hms}}':x=14:y=14:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=6"]
        for s0, s1, n, l in marks:
            lab = f"{n}. {l}".replace(":", "\\:").replace("'", "")
            draws.append(f"drawtext=fontfile={FONT}:text='{lab}':x=14:y=h-54:fontsize=22:fontcolor=yellow:box=1:"
                         f"boxcolor=black@0.55:boxborderw=6:enable='between(t,{s0:.2f},{s1 - 0.01:.2f})'")
        draws.append(f"drawtext=fontfile={FONT}:text='PRATONTON':x=w-tw-14:y=14:fontsize=22:fontcolor=white@0.7")
        out = BUILD / "pratonton-jumpa-totoro.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-i", str(joined), "-vf", ",".join(draws), "-c:v", "libx264", "-crf", "25",
             "-preset", "veryfast", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out)])
    else:
        out_dir = ROOT / "output"
        out_dir.mkdir(exist_ok=True)
        out = out_dir / "jumpa-totoro.mp4"
        if a.vo:
            run(["ffmpeg", "-v", "error", "-y", "-i", str(joined), "-i", str(a.vo), "-filter_complex",
                 "[1:a]aresample=48000,asplit=2[vo][vosc];[0:a][vosc]sidechaincompress=threshold=0.05:ratio=6[amb];[amb][vo]amix=inputs=2:normalize=0[a]",
                 "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)])
        else:
            run(["ffmpeg", "-v", "error", "-y", "-i", str(joined), "-c", "copy", "-movflags", "+faststart", str(out)])
    print(f"Jumlah {t:.1f}s -> {out}")


if __name__ == "__main__":
    sys.exit(main())
