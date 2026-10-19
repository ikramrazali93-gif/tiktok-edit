# Bantal Duduk Merah (kusyen tufted): edit plan, preview v1

Source: iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **69.8s**
Preview v1: **49.5s** (dipotong ~20s), 720×1280, 30fps, SDR, −11.7 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (ikut bantal merah + patung bunga pastel)

| Warna | Hex | Guna |
|---|---|---|
| Burgundy | `#5A0F1E` | outline caption, teks label, kotak label "merah" (kontras atas kusyen merah) |
| Merah ceri | `#E0182F` | highlight dalam kotak putih/kuning |
| Kuning cerah | `#FFD93D` | perkataan aktif caption (nampak jelas atas merah), GEBU!, LEMBUT, progress bar |
| Pink candy | `#FF8FB1` | keyword caption, COMEL SANGAT, BUAT PELUK / SANDAR |

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio 50.3, visual 60.7 (close-up) + 51.9 | ⭐ **HOOK** (J-cut atas close-up kusyen): "Comel sangat. Colour dia pun terang, cantik. Yang mana cari colour terang-terang, ambil bantal merah ni." | `COMEL SANGAT!` 🥰 → `TERANG, CANTIK` ❤️ → flash → `CARI KALER TERANG?` 🔎 → `AMBIL BANTAL MERAH NI!` 👉 |
| 6.5 | 0.4 | "Korang yang mana mencari bantal duduk, kita ada juga yang macam ni." | `BANTAL DUDUK` 🪑 |
| 10.0 | 4.1 | "Ini colour merah." | `KALER MERAH` ❤️ |
| 11.1 | 9.3 | "Letak dalam kereta, letak dekat kerusi, letak dekat ofis, dekat sofa." | `DALAM KERETA` 🚗 → `ATAS KERUSI` 🪑 → `DI OFIS` 💼 → `ATAS SOFA` 🛋️ |
| 15.6 | 14.1 | "Ini dari sisi-sisi tepi dia macam ni, belakang macam ni. Lembut, tebal dia tu sederhana lah, elok-elok untuk kita buat duduk." | `SISI & BELAKANG` 👀 → `LEMBUT` ☁️ → `TEBAL SEDERHANA` → `ELOK BUAT DUDUK` ✅ |
| 23.1 | 21.8–31.1 | "Okey macam ni kita buat duduk." + jalan (×3) + "Okay letak dekat sini." + duduk (×3) | `JOM DUDUK!` → tag `>> x3` → `LETAK KAT SINI` 👇 |
| 28.1 | 31.1 | "Gebu, sedap buat duduk." | `GEBU!` ☁️ → `SEDAP BUAT DUDUK` 😌 |
| 30.9 | 39.5 | "Ini depannya ada butang. Ini depannya." | `ADA BUTANG DEPAN` 🔘 |
| 33.6 | 42.5 | "Okey letak macam ni pun boleh." | `ATAS RIBA PUN BOLEH` 👍 |
| 35.3 | 44.5 | "Nak buat peluk pun boleh. Dia lembut." | `BUAT PELUK` 🤗 → `LEMBUT!` |
| 38.1 | 48.0 | "Nak buat sandar pun boleh." | `BUAT SANDAR` 😴 |
| 40.0 | 57.2 | "Material dia waffle." | `MATERIAL WAFFLE` 🧇 |
| 41.9 | 63.4 | "Boleh basuh tahu. Ada apa-apa kotor boleh basuh guys." | `BOLEH BASUH!` 🫧 → `KOTOR? BASUH JE` 🧼 |
| 44.9 | 67.4 | "Okey mami grab dekat beg kuning." | `TEKAN BEG KUNING` 🛒 |
| 47.0 | 68.3 (visual, thumbs up, slow-mo) | - | End card: `BANTAL DUDUK MERAH` / `GEBU • LEMBUT • BOLEH BASUH` / `TAG KAWAN SUKA MERAH!` / `TEKAN BEG KUNING` |

Dibuang: "ang-ang" selepas "merah" (tak jelas), "Yang mana mencari colour terang-terang ini memang sesuai lah" (ulang hook), "Ini," + bunyi tak jelas masa jalan, "Lepas itu buat duduk" (Whisper dengar "masuk balik duduk", tak jelas), "Nak buat lapis, rebuah pun boleh. Contoh nak tak tak rebuah, oh ini-ini depannya" (tak jelas), "Okey" lebih, "material waffle macam itu" (ulang), "Okey" sebelum "boleh basuh", senyap.

## Belum pasti

- **"Letak dalam kereta"**: Whisper dengar "reta" / "naretan". Senarai tempat (kerusi, ofis, sofa) buat "kereta" paling masuk akal.
- **"Gebu"** (28.1s): Whisper penuh dengar "Gebu", tapi bila potong klip dengar "Boo!/Oh". Caption tulis "Gebu".
- **"Ada apa-apa kotor boleh basuh"**: Whisper dengar "kotak"; caption tulis "kotor".

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_40.2.png cover.jpg                              # cover 1080x1536
```
