# Bantal Rabbit (arnab putih gebu): edit plan, preview v1

Source: iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **70.4s**
Preview v1: **40.7s** (dipotong ~30s), 720×1280, 30fps, SDR, −11.5 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280). Label diletak di y 560 (atas muka arnab) supaya mata & mulut arnab tak tertutup.

## Gaya (arnab putih + latar pastel)

| Warna | Hex | Guna |
|---|---|---|
| Berry gelap | `#5A2350` | outline caption, teks label |
| Pink gula-gula | `#FF8FB8` | kotak label default, keyword caption, progress bar |
| Biru langit (denim) | `#7EC8F2` | GEBU, BAGI ANAK, DAKAP WAKTU TIDUR, 2 MATA |
| Kuning mentega | `#FFD84D` | perkataan aktif caption, APAKAH NI?, HADIAH BIRTHDAY |
| Hot pink | `#E8457F` | COMEL!, BANTAL RABBIT, COMEL KAN? |

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio 2.9 + 5.6, visual 55.9 + 46.0 | ⭐ **HOOK** (J-cut atas close-up muka arnab): "Wah, apakah ni? Oh, comel." | `WAH, APAKAH NI?` 🤔 → flash → `OH, COMEL!` 🐰 |
| 3.3 | 18.1–26.2 | "Ni rabbit. Comel. Ni gebu lah. Bulu-bulu kita. Kita tepuk-tepuk dia, ulit-ulit dia bagi dia gebu." | `NI RABBIT!` 🐇 → `COMEL` → `GEBU + BULU-BULU` ☁️ → `TEPUK-TEPUK, ULIT-ULIT` 🤗 |
| 10.2 | 27.2 / 30.5 | "Ni untuk bantal rabbit. Size dia comel saja. Ni untuk buat peluk dalam kereta, bagi anak kita ke, bagi hadiah kat birthday anak ke." | `BANTAL RABBIT` 🎀 → `SIZE COMEL SAJA` → `PELUK DALAM KERETA` 🚗 → `BAGI ANAK` 👶 → `HADIAH BIRTHDAY!` 🎁 |
| 19.6 | 38.1 / 40.6 / 43.8 | "Size dia sedang-sedang macam tu. Buat dakap-dakap waktu tidur. Buat hiasan, letak dekat kerusi." | `SIZE SEDANG-SEDANG` 📏 → `DAKAP WAKTU TIDUR` 😴 → `HIASAN KERUSI` 🛋️ |
| 24.9 | 47.7 | "Dia ada telinga, dia ada dua mata dan mulut." | `ADA TELINGA` 🐰 → `2 MATA + MULUT` 👀 |
| 29.8 | 53.9 | "Warna putih. Comel lah. Material dia bulu-bulu macam ni." | `WARNA PUTIH` 🤍 → `MATERIAL BULU-BULU` ☁️ |
| 33.0 | 59.3 / 60.8 / 61.8 | "Ni belakang dia. Ni depan dia. Tebal dia macam ni." | `BELAKANG` 🔄 → `DEPAN` → `TEBAL MACAM NI` 👌 |
| 35.9 | 64.3 | "Comel kan?" | flash + `COMEL KAN?` 🥰 |
| 36.9 | 66.6–70.3 | "Mummy-mummy nak beli untuk anak pun boleh. Comel." | End card: `BANTAL RABBIT` / `PUTIH • GEBU • COMEL` / `HADIAH BIRTHDAY ANAK!` / `TEKAN BEG KUNING` |

Dibuang: "Hai, jom kita unboxing" (bukaan lambat), "Oh, sayang/di sana", "Tengok", "Ni gebu. Gebu lah. Ni rabbit." pertama (ulang, arnab masih berkedut dalam plastik), "Dia comel lah" (terlalu banyak "comel"), "Buat peluk lah" (ulang), "Letak dalam kereta" kedua (ulang), "Ni comel. Desain dia simple", "Okay ni rabbit", "Ni material dia" (ulang), "Kau tengok kat ...ni tau" (tak jelas, CTA beg kuning ada di end card), jeda.

## Belum pasti

- **"Kau tengok kat beg kuning ni tau"**: Whisper dengar "back-book / bagku". Mungkin "beg kuning", tapi sebab tak pasti aku buang ayat ni; end card tetap ada `TEKAN BEG KUNING`.
- **"Bulu-bulu"**: Whisper dengar "bulus-bulus". Caption tulis "bulu-bulu".
- **"Dakap-dakap waktu tidur"**: Whisper dengar "dakak-dakak". Aku anggap "dakap" (peluk).
- **"Buat hiasan"**: Whisper dengar "yasan".
- **"Bantal rabbit"**: dia sebut "rebit"; caption & label tulis "RABBIT".

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_21.6.png cover.jpg                              # cover 1080x1536
```
