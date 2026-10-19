# Baju Renang Lelaki (baju + seluar pendek + seluar panjang): edit plan, preview v1

Source: iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **69.0s** (IMG_6524)
Preview v1: **27.8s** (dipotong ~41s), 720×1280, 30fps, SDR, −11.5 LUFS
Final: **27.8s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −11.5 LUFS, sudah render
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (pantai / air)

| Warna | Hex | Guna |
|---|---|---|
| Navy laut dalam | `#0B2545` | outline caption, teks label |
| Biru laut | `#0077C8` | label BAJU RENANG, PANTAI, end card |
| Aqua (air kolam) | `#2EC4D6` | keyword caption, progress bar, JENIS FIT |
| Kuning matahari | `#FFD23F` | perkataan aktif caption, BERCUTI, SELUAR PENDEK |
| Coral | `#FF6B4A` | PERGI PULAU!, TAG GENG PANTAI |

Kain set ni hitam, jadi semua label pakai kotak terang (putih / kuning / biru) supaya jelas atas kain.

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio 58.3, visual 37.9 / 26.2 / 61.1 | ⭐ **HOOK** (J-cut atas close-up seluar panjang, seluar pendek, baju): "Sesuai sangatlah untuk pakai pergi pantai, nak pergi bercuti, nak pergi pulau-pulau, kan?" | `SESUAI KE PANTAI!` 🏖️ → `NAK BERCUTI` ✈️ → flash → `PERGI PULAU!` 🏝️ |
| 6.1 | 11.0–18.5 | buka plastik (×3) | tag `>> x3`, `JOM UNBOX!` 📦 |
| 8.6 | audio 6.5, visual 18.6 | "Baju renang." (J-cut atas dia keluarkan set) | `BAJU RENANG` 🌊 |
| 10.2 | 26.4 / 28.8 | "Seluar pendek pun boleh. Seluar panjang pun ada." | `SELUAR PENDEK` 🩳 → `+ SELUAR PANJANG` 👖 |
| 13.4 | 30.5 | "Boleh pakai seluar pendek kat rumah." | `PAKAI KAT RUMAH` 🏠 |
| 14.6 | audio 32.1 + 33.4, visual 35.0 | "Seluar panjang, jenis fit kan?" (jeda dibuang, J-cut atas seluar panjang) | `PANJANG JENIS FIT` 💪 |
| 16.5 | 41.6 / 44.6 | "Ni baju renang. Tangan panjang. Ni untuk lelaki." | flash + `BAJU RENANG` 👕 → `TANGAN PANJANG` 🙆 → `UNTUK LELAKI` 👨 |
| 23.1 | 53.3 | "Kainnya lembut je." | `KAIN LEMBUT` ☁️ |
| 25.2 | 65.7 (visual, pegang baju) | (suara penutup dia tak dicaption) | End card: `BAJU RENANG LELAKI` / `BAJU • SELUAR PENDEK • PANJANG` / `TAG GENG PANTAI KORANG!` / `TEKAN BEG KUNING` |

Dibuang: "Bismillahirrahmanirrahim", "Ini lelaki ber…, kan?" (tak jelas), "Ini seluar dia… sekali" (tak jelas), "Oh," , "Wah, seluarnya …" (tak jelas), "Wih, kemas ni", "Oh, macam ni, betul", "Wih, elok-elok, elok kan? Oh, kemas" (Whisper dengar "enak/elak", tak pasti), "Kainnya lembut je" yang kedua (ulang), "Macam tu", jeda / bunyi plastik.

## Belum pasti

Suara dalam video ni perlahan dan banyak bunyi plastik, jadi Whisper kurang yakin:

- **"Sesuai sangatlah"** (hook): Whisper dengar "Susah sangatlah" / "Selesai sangatlah". Ikut maksud ayat ("…untuk pakai pergi pantai") caption tulis "Sesuai".
- **"seluar"**: Whisper dengar "senak / selok / nak" sepanjang video. Caption tulis "seluar".
- **"kat rumah"**: dua kali dengar "kat rumah", sekali dengar "kat luar". Label tulis `PAKAI KAT RUMAH`.
- **"Tangan panjang"**: satu pass dengar "Pantang panjang". Masa tu dia tunjuk baju lengan panjang, jadi caption tulis "Tangan panjang".
- **"Ni untuk lelaki"**: dua pass dengar "lelaki", satu dengar "untuk dia lagi".
- **Ayat penutup** (65.7s): Whisper dengar "Lepaskan dekat beg kuning" / "Sampai jumpa di video selanjutnya". Tak dicaption; end card dah ada `TEKAN BEG KUNING`.

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_60.4.png cover.jpg                              # cover 1080x1536
```
