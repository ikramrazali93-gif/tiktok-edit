# Baju Sejuk Bayi (Teddy Fleece Jumpsuit): edit plan, preview v1

Source: iPhone, 1080×1920 portrait, HEVC HDR (HLG), 59.94fps, **50.0s**
Preview v1: **33.2s** (dipotong ~17s), 720×1280, 30fps, SDR
Final: **33.2s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −11.8 LUFS, sudah render
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (teddy + tempat sejuk)

| Warna | Hex | Guna |
|---|---|---|
| Koko | `#3B2418` | outline caption, teks label |
| Teddy brown | `#A0522D` | highlight dalam kotak putih/krim |
| Krim (telinga/kaki) | `#FFE8D1` | keyword caption, label ADA EKOR / BULU GEBU-GEBAS |
| Biru ais | `#8FE3FF` | perkataan aktif caption, TEMPAT SEJUK, SEJUK TAU!, BERSETOKIN, progress bar |

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 0.5–12.6 | ⭐ **HOOK** (bukaan asal, panggil terus pembeli): "Hai, yang mana ada bayi nak pakai baju yang comel-comel, nak pergi Cameron ke, tempat-tempat sejuk, Genting ke, atau nak pakai dalam mall, korang boleh grab baju bayi macam ni." | `ADA BAYI?` 👶 → `BAJU COMEL-COMEL` 🧸 → `PERGI CAMERON?` ⛰️ → `TEMPAT SEJUK` ❄️ → `GENTING` → `PAKAI KE MALL` 🛍️ → `GRAB BAJU NI!` 🛒 |
| 11.7 | 13.3 | "Saya beli waktu nak pergi Cameron. Saya pakaikan anak saya memang comel. Sejuk tau pergi Cameron. Kena ada baju ni satu. Barulah anak tidur selesa." | `BELI UNTUK CAMERON` 🏔️ → `COMEL!` → `SEJUK TAU!` 🥶 → `KENA ADA SATU` ☝️ → `TIDUR SELESA` 😴 |
| 18.6 | audio 23.4, visual 31.4 | J-cut: "Di belakang dia ada ekor." atas visual belakang baju (ekor bulat) | `ADA EKOR!` 🐻 |
| 19.7 | 25.5 | "Dia ni butang sampai bawah." | `BUTANG SAMPAI BAWAH` 🔘 |
| 21.2 | 27.3 | "Comel pun comel dan bersetokin sekali. Dia ada hoodie." | `BERSETOKIN` 🧦 → `ADA HOODIE` 🐻 |
| 24.8 | 35.2 | "Comel. Bulu-bulu gebu-gebas. Ada banyak saiz." | `COMEL!` → `BULU GEBU-GEBAS` ☁️ → `ADA BANYAK SAIZ` 📏 |
| 29.0 | 43.0 | "Bulu-bulu dia lembut tau." | `BULU LEMBUT TAU` 🤗 |
| 30.7 | 20.8 (visual) | - | End card: `BAJU SEJUK BAYI` / `HOODIE • EKOR • STOKIN` / `TAG MAK NAK KE CAMERON!` / `TEKAN BEG KUNING` |

Dibuang: "Kan? Okey." + jeda, "beli apa, beli apa" (tak jelas), "Okey, comel kan?", ulangan "bulu dia lembut".

## Belum pasti (perlu disahkan)

- **"Di belakang dia ada ekor"**: Whisper dengar "aircon", tapi visual tunjuk ekor bulat kat belakang. Caption tulis "ekor".
- **"Korang boleh grab baju bayi macam ni"**: Whisper dengar "BAM" atau "berm", mungkin "baju **bear**". Caption tulis "bayi".

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_17.2.png cover.jpg                              # cover 1080x1536
```
