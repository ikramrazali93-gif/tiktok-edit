# Bantal Kucing Tidur (calico, badan corak): edit plan, preview v1

Source: **3 klip produk sama, digabung jadi satu** (iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, dalam rumah)
- **A** (`dl47`, IMG_2938, 37.0s): dia peluk bantal kucing dan bercakap (semua suara dari sini)
- **B** (`dl48`, IMG_2939, 3.8s): close-up kucing atas riba (tiada suara)
- **C** (`dl49`, IMG_2940, 4.9s): close-up muka kucing, tangan usap kepala (tiada suara)

`master1080.mp4` / `proxy.mp4` = A + B + C disambung (A 0–37.000s, B 37.000–40.838s, C 40.838–45.743s). B dan C jadi B-roll atas suara A.

Preview v1: **25.4s** (daripada 45.7s gabungan), 720×1280, 30fps, SDR, −11.4 LUFS
Final: **25.4s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −11.4 LUFS, sudah render
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (ikut kucing calico)

| Warna | Hex | Guna |
|---|---|---|
| Koko (tompok gelap) | `#4A2C20` | teks label, outline caption |
| Karamel (tompok oren) | `#E99A4E` | keyword caption, pill KEPALA LEMBUT / ALAS BELAKANG / ADA MUSANG, jejak tapak kaki |
| Krim (bulu) | `#FFF5E6` | pill COMELNYA! / BANTAL PELUK, latar end card & cover |
| Blush (hidung pink) | `#F2668B` | "blob" perkataan aktif caption, flash, progress bar, PEMINAT KUCING? |
| Lilac / Sage (bantal bunga di belakang) | `#B79CF2` / `#9CCFB1` | BADAN PUN GEBU, UNTUK ANAK, MINAT GAJAH?, washi tape |
| Kuning | `#FFD23F` | TENGOK BEG KUNING |

## Refresh (lain sikit dari batch sebelum)

- **Label pill bulat** (sticker: rim putih + bayang lembut), bukan kotak segi empat senget.
- **Caption**: perkataan aktif dapat "blob" pink (outline tebal blush) macam highlighter; outline caption lebih nipis.
- **Motif tapak kaki kucing** 🐾 berjalan naik tepi skrin setiap tukar bahagian (lembut, anak, haiwan).
- **Flash warna blush/krim** lembut, bukan flash putih.
- **End card polaroid**: muka kucing dalam bingkai polaroid, washi tape lilac, latar krim bertitik.
- **Cover**: latar krim bertitik + kucing dalam polaroid senget (bukan gambar penuh).

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio A 24.9 + A 0.4, visual B 37.1 + A 0.4 | ⭐ **HOOK**: "Peminat kucing, ambil kucing. Comelnya kucing ni." | `PEMINAT KUCING?` 🐱 → flash → `COMELNYA!` 🥰 |
| 3.9 | A 2.6, visual C 41.2 + B 38.8 | "Kepala dia pun lembut, gebu, badan dia pun gebu." (atas close-up usap kepala + badan) | 🐾 jejak → `KEPALA LEMBUT` ☁️ → `BADAN PUN GEBU` 🤍 |
| 8.0 | A 6.7 | "Boleh buat bantal peluk, bantal kepala, bantal untuk alas belakang. Macam-macam kegunaan." | `BANTAL PELUK` 🤗 → `BANTAL KEPALA` 😴 → `ALAS BELAKANG` 🛋️ → flash + `MACAM-MACAM GUNA!` ✨ |
| 13.6 | A 17.3 | "Korang boleh beli untuk anak korang." | 🐾 → `UNTUK ANAK KORANG` 🧸 |
| 14.8 | A 26.6 | "Kalau korang minat gajah, ada gajah, ada musang, ada anak domba. Macam-macam haiwan ada ni." | 🐾 → `MINAT GAJAH?` 🐘 → `ADA MUSANG` 🦊 → `ADA ANAK DOMBA` 🐑 → flash + `MACAM-MACAM HAIWAN!` 🐾 |
| 21.5 | A 33.6 | "Korang tengok dekat beg kuning ni tahu." | `TENGOK BEG KUNING` 🛒 |
| 22.9 | C 43.6 (visual, ×0.85) | - | End card polaroid: `BANTAL KUCING` / `ADA GAJAH • MUSANG • DOMBA` / `TEKAN BEG KUNING` |

Dibuang: "Comel kan? / Angguk sikit" (tak jelas, Whisper dengar "Jom ikan"), "Tengok dekat beg kuning ni" yang pertama (ulang), **"harga dia sangat-sangat murah. Harga dia memang betul-betul berbaloi"** (peraturan: tiada fokus harga), "Tengok dekat beg kuning ni tahu" kedua (ulang), jeda 0.3s selepas "ada gajah".

## Belum pasti

- **"beg kuning"**: Whisper tulis "bagku" (bunyi laju). Semakan preview dengar "Bek Kuning", jadi caption tulis "beg kuning".
- **"musang"** dan **"anak domba"**: jelas dalam audio, tapi tak nampak dalam video. Label ikut apa yang disebut.
- **Nama produk**: dia cuma sebut "kucing". Label/cover guna "BANTAL KUCING"; folder dinamakan bantal-kucing-tidur sebab kucing ni mata tertutup (lain dari `projects/bantal-kucing` lama).

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py f_44.8.png cover.png                                  # cover 1080x1536 (frame C 44.8s)
```
