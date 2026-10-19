# Bantal Bunga Emoji (pelangi): edit plan, preview v1

Source: IMG_2927, iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **52.5s**, luar rumah atas rumput
Preview v1: **45.4s** (dipotong ~7s), 720×1280, 30fps, SDR, −11.5 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (ikut kelopak pelangi)

| Warna | Hex | Guna |
|---|---|---|
| Grape gelap | `#3B1F5C` | outline caption, teks label |
| Merah / oren / kuning / hijau / biru / ungu / pink | `#FF5A5F` `#FF9F1C` `#FFD93D` `#5CC96B` `#4D96FF` `#9B5DE5` `#FF7EB6` | kotak label, bayang label, perkataan aktif caption (bergilir), progress bar, wipe, pelangi end card |
| Krim | `#FFF8E7` | tengah pelangi end card, latar cover |

## Refresh (lain dari batch sebelum & dari video kucing tidur)

- **Label rata (tak senget)** gaya sticker: kotak dengan **bayang blok berwarna** (offset) dalam warna kelopak, bukan kotak senget.
- **Caption**: perkataan aktif **bertukar warna pelangi** setiap perkataan (merah → oren → kuning → ...), dengan rim putih.
- **Motif**: titik-titik kelopak pelangi meletup keluar dari label masa poin penting.
- **Transisi**: **jalur pelangi menyapu skrin** setiap tukar bahagian (bukan flash putih/blush).
- **Progress bar** pelangi bersegmen.
- **End card**: **pelangi separuh bulatan** di belakang 🌼, label bertingkat.
- **Cover**: latar **sunburst pelangi** + gambar produk jadi **sticker bucu bulat** (rim putih tebal + garis putus-putus pelangi).

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 14.0 | ⭐ **HOOK** (dipindah): "Lidah dia boleh siap angkat lagi, bergerak-gerak lagi, comel kan?" (close-up dia angkat lidah bantal) | `LIDAH BOLEH ANGKAT!` 😛 + letupan kelopak → `BERGERAK-GERAK!` 🤪 |
| 4.2 | 0.0 | wipe pelangi + "Korang dah ada belum bantal bunga yang comel, cute ni? Size dia 38cm. Ada 4 gaya emoji muka dia. Boleh pilih nak muka love ke, nak muka yang kenyit mata macam ni ke" | `BANTAL BUNGA COMEL` 🌼 → `SIZE 38CM` 📏 → `4 GAYA MUKA EMOJI` 🤩 → `MUKA LOVE` 😍 → `MUKA KENYIT MATA` 😉 |
| 17.9 | 18.5 | "Letak dalam kereta pun sangat-sangat sesuai." | `SESUAI DALAM KERETA` 🚗 |
| 20.2 | 22.5 | "Hoi, lawa!" | `HOI, LAWA!` ✨ |
| 21.3 | 24.4–28.9 | pusing bantal (×2, tanpa suara) | tag `>> x2`, `DEPAN • SISI • BELAKANG` 🔄 |
| 23.6 | 29.1 | "Material dia jenis kain velvet. Kain velvet ni dia tahan lasak. Kaler dia tak pudar walaupun kita dah guna lama, kaler dia tetap cantik dan macam baru je. Saya punya ni dah beli lama dah, tapi dia nampak macam baru je kan?" | `KAIN VELVET` 🧸 → `TAHAN LASAK` 💪 → `KALER TAK PUDAR` 🌈 → `TETAP CANTIK` 💖 → `SAYA DAH BELI LAMA` 🗓️ → `MASIH MACAM BARU!` ✨ |
| 37.0 | 44.3 | "Boleh jadi hadiah." | `BOLEH JADI HADIAH` 🎁 |
| 38.1 | 45.7 | "Bolehlah cikgu-cikgu beli banyak-banyak buat hadiah untuk student." | `CIKGU-CIKGU!` 🍎 → `HADIAH STUDENT` 🎒 |
| 41.6 | 51.0 | "Korang tengok beg kuning." | `TENGOK BEG KUNING` 🛒 |
| 42.9 | 11.4 (visual, perlahan) | - | End card pelangi: `BANTAL BUNGA EMOJI` / `4 GAYA • 38CM • VELVET` / `KORANG PILIH MUKA MANA?` / `TEKAN BEG KUNING` |

Dibuang: "Letak dekat cermin bonet tu" (tak jelas), "Ok ni dari depan, ini dari sisi tepi, ini dari belakang" (diganti visual ×2 + label), "Ah, recommended" (bunyi tak jelas, Whisper tak dengar bila dipotong), "Ok, recommended" (ulang), jeda 0.3s selepas "love ke".

Tiada harga dalam video, label, cover atau caption.

## Belum pasti

- **"cermin bonet"**: Whisper dengar "cermin bonet/bonik". Ayat ni dibuang.
- **"Hoi, lawa!"**: Whisper dengar "oi / hui / wuih lawa". Caption tulis "Hoi, lawa!".
- **"Saya punya ni dah beli lama"**: transkrip penuh dengar "saya pun ni", semakan preview dengar "saya punya ni" (dua kali). Caption ikut "Saya punya ni".
- **"beg kuning"**: Whisper dengar "baik/beli kuning" (loghat). Caption tulis "beg kuning".

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_2.0.png cover.jpg                               # cover 1080x1536
```
