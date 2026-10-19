# Kusyen Bunga (grey): edit plan, preview v1

Source: iPhone IMG_7876, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **36.0s** (luar rumah, atas padang)
Preview v1: **15.9s** (dipotong ~20s), 720×1280, 30fps, SDR, −11.7 LUFS
Final: **15.9s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −11.7 LUFS, sudah render
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

Video ni pendek sebab dia tak banyak bercakap (kebanyakan masa buka plastik dan layan anak). Satu produk sahaja dalam video ni.

## Gaya (ikut kusyen)

| Warna | Hex | Guna |
|---|---|---|
| Charcoal | `#3A3F4B` | outline caption, teks label |
| Grey kusyen | `#8E9AAF` | label GREY, end card, tepi bawah cover |
| Cream (bingkai kusyen) | `#F4E3C3` | ADA BUNGA, BUKA PLASTIK, tepi cover |
| Kuning daisy | `#FFD23F` | perkataan aktif caption, DAH SAMPAI!, progress bar |
| Pink / Brown | `#FF8FB1` / `#A86B4C` | warna lain yang dia sebut: + PINK, DAH ADA BROWN |

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio 9.5, visual 22.4 | ⭐ **HOOK** (J-cut atas kusyen dah keluar plastik, bunga jelas): "Ni semua saya repeat order." | flash + `SAYA REPEAT ORDER!` 🔁 🌼 |
| 1.6 | 0.0–5.6 | buka beg kurier (×3) | tag `>> x3`, `JOM UNBOX!` 📦 |
| 3.4 | 5.8 | "Oh ni warna grey." | `WARNA GREY` 🩶 |
| 4.9 | 7.9 | "Ni dah sampai dah." | `DAH SAMPAI!` 🎉 |
| 6.0 | 8.9–11.9 | angkat kusyen, tunjuk bunga (×2) | tag `>> x2`, `ADA BUNGA` 🌼 |
| 7.5 | 11.9 / 13.9 / 16.1 | "Itu dah ada warna, warna brown dengan pink." | `DAH ADA BROWN` 🤎 → `+ PINK` 🩷 |
| 10.4 | 16.7 | "Ni warna grey." | flash + `SEKARANG GREY!` ☁️ |
| 11.8 | 18.1–21.9 | koyak plastik (×2.5) | tag `>> x2.5`, `BUKA PLASTIK` ✂️ |
| 13.3 | 24.0–25.5 (slow-mo 0.6) | - | End card: `KUSYEN BUNGA` / `GREY • BROWN • PINK` / `KORANG NAK KALER APA?` / `TEKAN BEG KUNING` |

Dibuang: "...terusnya" (awal, tak jelas), "hijau, eh," (tersasul, dia betulkan sendiri), jeda 0.85s sebelum "pink", "Adik, dia buat apa ni?" dan "Jangan pegang!" (cakap dengan anak; suara tu dimute masa end card), bahagian akhir (kusyen dah masuk balik beg).

## Belum pasti

- **Nama produk**: dia tak sebut nama dalam video. Aku guna "KUSYEN BUNGA" (bentuk awan, ada bunga). Kalau nama dalam kedai lain (contoh "bantal duduk awan"), tukar label end card, cover dan caption.
- **"repeat order"**: Whisper dengar "repeat all day". Ikut konteks ("ni semua saya…"), "repeat order" paling masuk akal.
- **"warna brown dengan pink"**: sebelum tu dia sebut "hijau, eh," lepas tu betulkan. Aku anggap warna yang dia dah ada ialah brown dan pink.

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_23.0.png cover.jpg                              # cover 1080x1536
```
