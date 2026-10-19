# Bantal Carrot (Lobak Merah): edit plan, preview v1

Source: iPhone IMG_2934, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **53.1s**, luar rumah (atas rumput)
Preview v1: **40.9s** (dipotong ~12s), 720×1280, 30fps, SDR, −11.4 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (tema kebun) + refresh

| Warna | Hex | Guna |
|---|---|---|
| Oren carrot | `#FF6E2F` | highlight dalam tag, circle reveal, titik progress bar |
| Hijau daun (pucat) | `#7CE38B` | keyword caption, pucuk daun |
| Hijau tua | `#1F6B3A` | outline perkataan aktif, highlight atas tag kuning, latar end card |
| Coklat tanah | `#5B3A29` | teks tag, outline caption, tali tag |
| Kuning matahari | `#FFD166` | perkataan aktif caption, tag penting |
| Krim | `#FFF6E5` | tag biasa |
| Kayu | `#E3B07A` / `#8A5A33` | papan tanda end card |

**Refresh (lain dari batch sebelum & dari video batch-4 lain):**
- **Label:** tag gantung (hang-tag) berhujung tirus dengan lubang & tali, berbuai perlahan dari atas (bukan pill / sticker / bubble / tiket / patch).
- **Caption:** perkataan aktif membesar sedikit (116%) dan jadi kuning dengan outline hijau tua; kata kunci hijau daun.
- **Motif:** pucuk daun carrot tumbuh dari bawah (kiri & kanan) setiap kali mula bahagian baru, dengan bunyi "sprout".
- **Transisi:** circle reveal oren (bulatan mengembang lalu hilang), bukan flash / wipe / zoom punch.
- **Progress bar:** barisan biji benih; setiap titik menyala oren bila masa lalu.
- **End card:** papan tanda kayu kebun (tiang + 4 papan jatuh satu-satu dengan bunyi "thud") atas latar hijau.
- **Cover:** gaya paket benih: kertas kraft bertepi zigzag, band tajuk hijau, gambar dalam tingkap, tag gantung, cop bulat "GEBU GEBU!", jalur saiz coklat.

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio 9.7, visual 24.0 / 26.0 / 28.0 (close-up muka) | ⭐ **HOOK** (J-cut): "Dia ada 2 jenis senyuman. Ada senyuman ada gigi. Ada senyuman yang tanpa gigi." | `2 JENIS SENYUMAN!` 😊 → `ADA GIGI!` 🦷 → `TANPA GIGI` 😌 |
| 5.0 | 0.0 | "Ya Allah, comelnya. Carrot ni gebu-gebu ya. Kita ada 3 size, 90cm, 70cm dan juga 50cm." | `COMELNYA!` → `GEBU-GEBU` → `ADA 3 SIZE` → `90CM` → `70CM` → `50CM` |
| 14.3 | 15.0 | "Korang boleh pilih." | `KORANG PILIH!` 👉 |
| 15.2 | 29.6 | "Kalau ni kita boleh buat bantal peluk atau tidur, yang besar ni. Kalau yang ni boleh buat travel, yang kecil ni untuk bayi-bayi. Kan, comel ni." | `BANTAL PELUK` → `TEMAN TIDUR` → `BAWA TRAVEL` → `KECIL UNTUK BAYI` → `COMEL KAN?` |
| 23.8 | 43.6 | "Material dia material kain velvet. Macam ni material dia tahan lasak. Kaler dia tak pudar dan dia tak berbulu." | `KAIN VELVET` ✨ → `TAHAN LASAK` 💪 → `TAK PUDAR` → `TAK BERBULU` 👌 |
| 30.0 | 20.7 (audio), visual 20.7 + 38.3 | "Dan korang boleh beli banyak-banyak. Borong buat hadiah untuk anak buah, anak korang, anak murid, semua anak-anak boleh kan. Nah, mami-mami pun boleh." | `BELI BANYAK-BANYAK` → `HADIAH ANAK BUAH` 🎁 → `ANAK KORANG` → `ANAK MURID` → `MAMI-MAMI PUN BOLEH!` |
| 38.3 | 50.4 (visual) | - | End card papan kayu: `BANTAL CARROT` / `90 • 70 • 50 CM` / `TEAM GIGI KE TANPA GIGI?` / `TEKAN BEG KUNING` |

Dibuang:
- **Ayat harga (peraturan tiada harga):** "Sekarang ni seller tengah bagi harga yang sangat-sangat promo, jimat." dan "Harga dia sangat-sangat jimat. Memang berbaloi."
- "Ok" selepas "50cm", jeda 0.45s selepas "anak korang", nafas sebelum "Macam ni material", bahagian senyap di hujung.
- Tiada CTA beg kuning disebut dalam video, jadi `TEKAN BEG KUNING` hanya di end card.

## Belum pasti

- **"atau tidur"**: Whisper dengar "atau tidong", semakan preview dengar "waktu tidur". Caption tulis "atau tidur"; label `TEMAN TIDUR` betul untuk kedua-duanya.
- **"bayi-bayi"**: semakan preview dengar "baby-baby".
- **"Ya Allah"** di awal blok kedua: semakan preview dengar "Lihatlah".
- **"Kaler dia tak pudar"**: dia sebut "Kala", caption tulis "Kaler".

## Render

```
python3 sfx.py sfx/                                                    # SFX (tambah sprout, thud)
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_2.0.png cover.jpg                               # cover 1080x1536
```
