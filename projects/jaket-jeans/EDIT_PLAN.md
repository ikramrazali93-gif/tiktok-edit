# Jaket Jeans (Denim + Acid Blue): edit plan, preview v1

Source: iPhone IMG_7878, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **49.3s** (luar rumah, atas padang)
Preview v1: **31.6s** (dipotong ~18s), 720×1280, 30fps, SDR, −11.6 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

Satu produk sahaja dalam video ni: jaket jeans, 2 kaler (Denim + Acid Blue).

## Gaya (ikut denim)

| Warna | Hex | Guna |
|---|---|---|
| Indigo | `#1F2F5C` | outline caption, teks label, end card |
| Denim | `#3E6FA8` | highlight, KEDAI & TIKTOK SHOP, KALAU PASANGAN?, pill DENIM |
| Acid blue (light wash) | `#A9C7E8` | keyword caption, KALER ACID BLUE, CERAH SIKIT, pill ACID BLUE |
| Mustard | `#FFC93C` | perkataan aktif caption, PALING MURAH!, JIMAT RM10!, progress bar, jahitan bawah cover |
| Tangerine | `#FF7A3D` | harga: MAHAL SIKIT, RM10, burst PALING MURAH! |

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio 35.3 + 33.7, visual 43.3 | ⭐ **HOOK** (J-cut atas shot pegang jaket depan kamera): "Saya dah survey banyak dekat kedai, dekat TikTok Shop juga. Yang ni antara yang paling murah." | `DAH SURVEY BANYAK` 🔍 → `KEDAI & TIKTOK SHOP` 🛍️ → flash + `NI PALING MURAH!` 💸 |
| 4.7 | 0.8 / 3.0 | "Ni jacket jeans. Saya beli lagi satu colour." | `JAKET JEANS` 🧥 → `BELI LAGI SATU!` 🛒 |
| 7.7 | 7.45 | "Ni colour acid blue." | `KALER ACID BLUE` 🩵 |
| 9.1 | 9.7 | "Okey, ni denim, ni acid blue. Jadi kita tengok." | `DENIM + ACID BLUE` ✌️ → `JOM TENGOK!` |
| 11.4 | 12.1–16.5 | buka plastik (×3) | tag `>> x3`, `BUKA PLASTIK` ✂️ |
| 12.9 | 16.5 | "Ni cerah sikit colour dia. Kalau pasangan, kan? Cerah sikit je. Saya pakai denim. Yang ni colour acid blue. Dah ada dua colour." | `CERAH SIKIT` ☀️ → `KALAU PASANGAN?` 👫 → `SAYA PAKAI DENIM` 👈 → `NI ACID BLUE` 🩵 → flash + `DAH ADA 2 KALER!` ✌️ |
| 22.7 | 27.9 | "Macam saya pakai, sebijik." | `SEBIJIK MACAM NI!` 👯 |
| 23.8 | 38.7 | "Yang lain, harga atas daripada, mahal sikit. Ni jimat RM10." | `YANG LAIN MAHAL SIKIT` 💰 → flash + `NI JIMAT RM10!` 🤑 |
| 28.1 | 32.3 | "Tengok dekat beg kuning tau." (dipindah ke hujung sebagai CTA) | `TENGOK BEG KUNING` 🛒 |
| 29.1 | 26.3 (visual, jaket dekat kamera, slow-mo) | - | End card: `JAKET JEANS` / `DENIM • ACID BLUE` / `KORANG PILIH KALER MANA?` / `TEKAN BEG KUNING` |

Dibuang: "Saya rasa" (awal), "betul tak?", "ni colour..." yang tersasul + jeda sebelum "acid blue", "cuma ni colour denim, ni colour acid blue" (ulang), "Sebab" (sebelum ayat hook), "Wah... cuma yang baik" di hujung (tak jelas), jeda dan bunyi plastik.

## Belum pasti

- **"survey"**: Whisper tulis "servis". Maksud ayat (dah bandingkan harga dekat kedai dan TikTok Shop) lebih kena dengan "survey".
- **"Kalau pasangan, kan?"**: Whisper dengar "kalau pasang kan". Mungkin maksudnya pakai sedondon dengan pasangan.
- **"sebijik"**: Whisper dengar "wax bijik" / "wad sebiji". Caption tulis "Macam saya pakai, sebijik".
- **"harga atas daripada"**: ayat penuh kurang jelas, caption ikut bunyi. Label cuma tulis `YANG LAIN MAHAL SIKIT`.
- **"jimat RM10"**: Whisper dengar "GMAT RM10" sekali, "jimat RM10" dua kali. Caption tulis "jimat RM10".

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_44.4.png cover.jpg                              # cover 1080x1536
```
