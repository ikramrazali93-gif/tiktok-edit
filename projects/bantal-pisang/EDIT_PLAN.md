# Bantal Pisang (35 / 50 / 70cm): edit plan, preview v1

Source: **2 video produk sama, digabung jadi satu** (iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, luar rumah atas rumput)
- **A** (`dl26`, IMG_7877, 49.4s): buka bungkusan bantal pisang 70cm, anak main dan duduk atas bantal
- **B** (`dl28`, IMG_7879, 73.6s): buka saiz paling kecil (35cm), banding 35cm dengan 70cm, CTA

`master1080.mp4` / `proxy.mp4` = A + B disambung (A 0–49.367s, B 49.367–123.0s). Masa transcript B dianjak +49.367s, jadi `edit.py` guna satu timeline. Kekuatan suara A dan B dah sekata (−11.3 / −11.4 / −11.5 LUFS ikut bahagian).

Preview v1: **44.5s** (daripada 123.0s gabungan), 720×1280, 30fps, SDR, −11.5 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (ikut warna pisang)

| Warna | Hex | Guna |
|---|---|---|
| Coklat hujung pisang | `#4A2E14` | outline caption, teks label |
| Kuning pisang | `#FFD93D` | keyword caption, BANTAL PISANG, PISANG 70CM!, end card |
| Hijau tangkai | `#3DBE5A` | NI 35CM, YANG PALING KECIL, NAK PELUK?, jalur bawah cover |
| Hijau daun | `#1F8A3A` | highlight dalam kotak kuning |
| Pink | `#FF5FA2` | perkataan aktif caption (nampak atas bantal kuning), YANG NI 70CM!, progress bar |
| Biru langit | `#5EC8FF` | ANAK PUN SUKA, NAK BAGI BABY? |

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio B 77.6 + 68.8 + 71.1, visual B 73.0 / 85.0 / 71.1 | ⭐ **HOOK** (J-cut atas dua-dua bantal): "Tidak kusangka sebesar ini! Ni 35cm. Yang ni, ni 70cm!" | `TAK SANGKA SEBESAR NI!` 😱 → flash → `NI 35CM` 🤏 → `YANG NI 70CM!` 🍌🤯 |
| 5.3 | A 2.6 | "Ni bantal pisang yang kita nanti-nantikan." | `BANTAL PISANG` 🍌 → `YANG DITUNGGU-TUNGGU` 🥳 |
| 8.4 | A 6.8 | "Wah ni pisang yang besar. Wah, pisang 70cm!" | `WAH BESARNYA!` 🤩 → flash → `PISANG 70CM!` 📏 |
| 12.6 | A 13.0–18.5 | buka plastik (×3) | tag `>> x3` |
| 14.5 | A 36.9 | anak duduk atas bantal: "Ya Allah anakku." | `ANAK PUN SUKA` 🥰 → `YA ALLAH ANAKKU!` 😂 |
| 17.2 | audio A 41.6, visual A 43.0 | "Ih, gebu lah. Besar lah ni. Ni 70cm. Saya pun ada 50cm." | `GEBU!` ☁️ → `BESAR LAH NI` → `70CM` → `ADA 50CM JUGA` 👍 |
| 21.3 | B 52.9 / 57.1 | "Ni bantal pisang yang paling kecil. Oh, dia kompres macam ni." | flash + `YANG PALING KECIL` 🤏 → `DIA KOMPRES` 📦 |
| 26.8 | B 58.7–67.1 | buka saiz kecil (×3) | tag `>> x3` |
| 29.6 | B 81.0 / 86.6 | "Ni kalau nak bagi baby... bagi baby newborn yang pegang. Kecil sangat ni." | `NAK BAGI BABY?` 👶 → `NEWBORN PEGANG` 🍼 → `KECIL SANGAT!` |
| 34.4 | B 93.5 | "Sebab tu saya dalam live saya cakap 35cm jangan ambil, untuk hiasan saja." | flash + `35CM JANGAN AMBIL` 🙅 → `UNTUK HIASAN JE` 🎀 |
| 37.9 | B 97.4 | "Nak peluk ambil 50cm dengan 70cm, macam ni besar." | `NAK PELUK?` 🤗 → `AMBIL 50 / 70CM` 💛 |
| 40.8 | B 114.0 | "Dapatkan dekat beg kuning, kita ada 3 size!" | `TENGOK BEG KUNING` 🛒 → `ADA 3 SIZE!` ✨ |
| 42.7 | B 113.0 (visual, thumbs up) | - | End card: `BANTAL PISANG` / `35 • 50 • 70 CM` / `KORANG NAK SIZE MANA?` / `TEKAN BEG KUNING` |

Dibuang: "Bismillah" (dua-dua klip), "Comel kan?" ×4 (Whisper dengar lain-lain, tak jelas), "Wee, gebu" ×2 masa buka plastik (Whisper dengar "Oh ibu ibu"), "Sekejap" ×6, "Mana boleh buka ni?", "Jangan takut" ×3, "Tak nak", "Orang nak ketuk-ketuk benda dia bulat balik", "Kata dah", "Banana / Oh very small / Ya betul", "guys", "Saya cakap jangan ambil 35. Dapat besar ni je" (diulang lebih jelas di "Sebab tu..."), "Baby yang newborn letak ... bolehlah" (tak jelas), "50cm dengan 70cm besar buat peluk" (ulang), "Ini 35cm. Tak sangka besar ni. Kecil sangat. Comel. Tidak kusangka" (ulang), "Okay guys", "50cm masih ada tapi dalam rumah. Nanti saya tunjuk", jeda.

## Belum pasti

- **"Saya pun ada 50cm"**: Whisper dengar "Amun ada" / "Mana ada". Maksud (ada saiz 50cm juga) sama dengan CTA "3 size", jadi caption tulis "Saya pun ada 50cm".
- **"Dia kompres macam ni"**: semakan preview dengar "Ada pampres". Caption tulis "Oh, dia kompres macam ni" (bantal dimampatkan dalam plastik).
- **"untuk hiasan saja"**: Whisper dengar "eosan / yes and / yearsend". Ikut maksud ayat (35cm terlalu kecil untuk peluk), caption tulis "hiasan".
- **"Sebab tu saya dalam live saya cakap"**: Whisper pertama dengar "saya analyze"; pass kedua dengar "dalam live".
- **"Ih, gebu lah"**: Whisper juga dengar "Wee, gebu" / "gebul".

## Render

```
# A + B digabung dulu (tone-map HLG → bt709 untuk setiap klip, lepas tu concat -c copy)
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_B85.6.png cover.jpg                             # cover 1080x1536 (B 85.6s = 36.2s dalam klip B)
```
