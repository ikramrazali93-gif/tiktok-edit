# Seluar Palazzo (brown): edit plan, preview v1

Source: iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **64.6s**
Preview v1: **46.1s** (dipotong ~18s), 720×1280, 30fps, SDR, −11.9 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (ikut seluar + jaket denim)

| Warna | Hex | Guna |
|---|---|---|
| Espresso | `#3B2314` | outline caption, teks label |
| Karamel / mustard (seluar) | `#B5782A` | MATERIAL SELESA, COLOUR BROWN, MATERIAL LEMBUT |
| Kuning bunga matahari | `#FFC93C` | perkataan aktif caption, ANTI KEDUT, FREE SIZE, HIGH KUALITI, progress bar |
| Denim (jaket) | `#2F5D9E` | SUKA PALAZZO?, IRONLESS, SELESA SANGAT |
| Biru langit | `#8FD6FF` | keyword dalam caption (kontras dengan mustard) |

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 48.4 | ⭐ **HOOK** (dipindah dari hujung): "Siapa yang suka pakai palazzo, ni paling sesuai untuk awak kan!" | `SUKA PALAZZO?` 👖 → flash → `NI PALING SESUAI!` 👉 |
| 3.6 | 0.5 | "Wah, palazzo! Material selesa." | `WAH, PALAZZO!` 🤩 → `MATERIAL SELESA` ☁️ |
| 5.8 | 3.7 | "Material dia macam… anti kedut macam tu. Dia tak nampak keras kejong, dia ironless." | `ANTI KEDUT` ✨ → `TAK KERAS KEJONG` 🙅 → `IRONLESS!` 🙌 |
| 11.8 | 11.0 / 15.9 | "Ni bahagian depan dia ada zip." + "Ni ada cangkuk." (J-cut atas close-up pinggang) | `DEPAN ADA ZIP` 🤐 (SFX zip) → `+ CANGKUK` 🪝 |
| 16.1 | 18.0 / 23.5 | "Bahagian belakang ada getah." + "Selesa sangat." (atas shot getah ditarik) | `BELAKANG GETAH` 🔙 → `SELESA SANGAT!` 😌 |
| 19.5 | 24.9 | "Yang ni saya ambil free size. Ni untuk colour brown macam tu." | `FREE SIZE` 📏 → `COLOUR BROWN` 🤎 |
| 24.0 | 31.6 | "Dekat sini dia ada tulang. Jadi kalau kita pakai tu nampak kemas sangatlah." | `ADA TULANG` 👇 → `NAMPAK KEMAS!` ✨ |
| 27.3 | 35.2 / 38.5 | "Material dia paling tip top! Material best." + "Kualiti, high kualiti lah!" | `TIP TOP!` 👍 → `MATERIAL BEST` 💯 → flash `HIGH KUALITI` 🏆 |
| 31.8 | 40.9 / 46.4 | "Material dia lembut, elok." + "Jahitan pun sangatlah kemas." | `MATERIAL LEMBUT` ☁️ → `JAHITAN KEMAS` 🧵 |
| 35.6 | 52.3 | "Pakai dengan t-shirt ke, pakai dengan knitwear ke, pakai dengan baju labuh ke. Semua boleh!" | `+ T-SHIRT` 👕 → `+ KNITWEAR` 🧶 → `+ BAJU LABUH` 👗 → flash `SEMUA BOLEH!` 🙌 |
| 41.5 | 61.7 | "Ada macam-macam warna, boleh tengok dekat beg kuning tau." | `MACAM-MACAM WARNA` 🎨 → `TEKAN BEG KUNING` 🛒 |
| 44.1 | 0.3 (visual, pegang seluar, perlahan) | - | End card: `SELUAR PALAZZO` / `ANTI KEDUT • IRONLESS • FREE SIZE` / `KORANG NAK WARNA APA?` / `TEKAN BEG KUNING` |

Dibuang: "yakmat" (tak jelas), "dan ada cangkuk lah" (ulang, tinggal "Ni ada cangkuk"), "Bahagian belakang ada getah macam ni" (ulang), "Okey" ×4, "Ini sangat selesa" (ulang), "Memang kualiti" (ulang), "dan ironless, elok sangat" (ironless dah sebut), "Okey, dekat beg kuning" pertama (ulang), jeda panjang (cth. 1.2s selepas "t-shirt ke").

## Belum pasti

- **"Wah, palazzo"**: Whisper dengar "Wah, apa lazu". Konteks jelas "palazzo".
- **"cangkuk"**: Whisper dengar "cakok / cakot". Aku anggap maksudnya cangkuk (kancing besi) di pinggang depan.
- **"anti kedut"**: Whisper dengar "anti kedud / gedut".
- **"baju labuh"**: Whisper dengar "baju labur".
- **"Dekat sini dia ada tulang"**: satu pass dengar "dekat sini saja ada tulang". Caption tulis "dia".
- **"Selesa sangat"** (selepas getah): satu pass dengar "susah/besar sangat", tapi transcribe penuh dan pass konteks dengar "selesa sangat".

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_12.0.png cover.jpg                              # cover 1080x1536
```
