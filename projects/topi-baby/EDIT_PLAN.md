# Topi Baby (beanie hitam, patch smile): edit plan, preview v1

Source: **2 video produk sama, digabung jadi satu** (iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps)
- **A** (`dl18`, 37.6s): close-up tangan, unboxing dan tunjuk topi, **tiada suara** (dipakai sebagai b-roll)
- **B** (`dl19`, 41.5s): bercakap depan kamera sambil pegang topi (semua suara dari sini)

`master1080.mp4` / `proxy.mp4` = A + B disambung (A 0–37.567s, B 37.567–79.1s). Masa transcript B dianjak +37.567s, jadi `edit.py` guna satu timeline.

Preview v1: **37.8s** (daripada 79.1s gabungan), 720×1280, 30fps, SDR, −11.9 LUFS
Final: **37.8s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −11.9 LUFS, sudah render
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (topi hitam + patch smile, tema baby)

| Warna | Hex | Guna |
|---|---|---|
| Plum-charcoal | `#2A2438` | outline caption, teks label |
| Baby blue | `#8FD3FF` | keyword caption, label utama, band cover |
| Peach | `#FFB38A` | TOPI BABY, BILA BABY PAKAI, BELAKANG |
| Kuning smile | `#FFD84D` | perkataan aktif caption, MUMMY YANG ADA BABY!, SMILE!, progress bar |
| Mint | `#9BE7C4` | TELINGA SELESA, SEDAP & SELESA |
| Coral | `#FF6B6B` | PAKAI DARI NEWBORN, MACAM-MACAM WARNA |

Label diletak di atas (y 200), atas topi, supaya produk tak terlindung.

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio B 37.97 + 54.25, visual A 6.8 + 26.0 | ⭐ **HOOK** (J-cut atas close-up A): "Mummy yang ada baby, grab lah dia." + "Boleh pakai daripada baby newborn, sampai setahun pun boleh pakai." | `MUMMY YANG ADA BABY!` 👶 → flash → `PAKAI DARI NEWBORN` 🍼 → `SAMPAI SETAHUN!` 🎂 |
| 5.9 | A 0.3–5.3 | unboxing dari plastik (×2.5, tiada suara) | tag `>> x2.5` + `TOPI BABY` |
| 7.9 | audio B 40.9, visual A 16.3 | "Topi ni dia material yang stretchable." | `MATERIAL STRETCHABLE` 🧶 |
| 10.8 | B 44.1 | "Kalau baby pakai dia tak memekakkan telinga lah." | `BILA BABY PAKAI` → `TELINGA SELESA` 👂 |
| 14.0 | B 47.7 | "Ni baby selesa, baby pun tak tarik sebab selesa kan." | `BABY SELESA` 😊 → `BABY TAK TARIK!` |
| 18.5 | B 58.7 | "Kat sini dia ada, tu, smile." (close-up patch) | `ADA PATCH KAT SINI` → flash + `SMILE!` 🙂 |
| 22.2 | audio B 63.0, visual A 20.0 + B 67.2 | "Material pun sedap, selesa, lembut, stretchable macam ni kan. Ni bahagian belakang, ni bahagian depan. Ada macam-macam warna." | `SEDAP & SELESA` → `LEMBUT + STRETCH` 🧸 → `BELAKANG` → `DEPAN` → `MACAM-MACAM WARNA` 🌈 |
| 30.6 | B 75.9 | "Lelaki perempuan boleh pakai." (dipindah ke sebelum CTA) | `LELAKI & PEREMPUAN` 👦👧 |
| 32.1 | B 71.5 | "Boleh tengok dekat beg kuning." | `TENGOK BEG KUNING` 🛒 |
| 34.2 | audio B 73.9, visual A 32.4 | "Comel tahu. Mummy grab lah untuk baby." | End card: `TOPI BABY` / `LEMBUT • STRETCH • COMEL` / `NEWBORN - 1 TAHUN` / `TEKAN BEG KUNING` |

Dibuang: "Ha," pembuka, "Okey" ×3, "ini material stretchable macam ni" (ulang, dah ada dalam ayat topi), bahagian unboxing A yang lambat, semua jeda. Ayat "Terima kasih kerana menonton" yang Whisper dengar dalam video A tu halusinasi (A tiada suara), jadi tak dipakai.

## Belum pasti

- **"tak memekakkan telinga"**: Whisper dengar "memerkakkan" (4 kali cubaan, semua sama). Caption tulis "memekakkan" ikut bunyi, label tulis `TELINGA SELESA` supaya selamat walau perkataan sebenar lain (contoh "menekan").
- **"Lelaki perempuan"**: Whisper dengar "laki-laki perempuan" / "lelaki perempuan". Caption tulis "Lelaki perempuan".

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_8.6.png cover.jpg                               # cover 1080x1536 (frame A 8.6s)
```

Bina master gabungan: tone-map setiap klip (A, B) → `concat` video (stream copy) + audio A dipotong/pad tepat 1127 frame (37.567s) → mux.
