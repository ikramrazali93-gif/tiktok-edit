# Bantal Bunga Senyum (lilac, pink, krim): edit plan, preview v1

Source: IMG_2929, iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **53.4s** (luar rumah, atas rumput)
Preview v1: **38.7s** (dipotong ~15s), 720×1280, 30fps, SDR, −11.5 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (ikut bantal) + refresh

| Warna | Hex | Guna |
|---|---|---|
| Plum | `#4A2C5E` | outline caption, teks dalam bubble, outline bubble |
| Lilac | `#B79CE6` / `#8E6BD1` | bubble, wipe, jahitan end card, track progress bar |
| Pink | `#F49BC2` | bubble, kata kunci caption (sebelum disapu), wipe |
| Rose (pipi) | `#F06A9A` | highlight dalam bubble putih, "SENYUM" end card |
| Krim | `#FFF6E6` | kad end card, kelopak motif |
| Madu (muka bunga) | `#FFC93C` | sapuan karaoke caption, bubble, progress bar |

Refresh yang dipakai (lain dari kucing tidur / tembikai):
- **Label speech-bubble**: bubble bulat dengan ekor menunjuk ke bawah (ke bantal), outline plum, tiada senget; bunyi "plink" baru.
- **Caption karaoke**: satu baris 3 perkataan muncul sekali gus, warna madu "menyapu" setiap perkataan ikut masa dia sebut (`\kf`); kata kunci menunggu dalam pink.
- **Motif bunga kecil 6 kelopak** (lilac/pink/krim, tengah madu) berpusing masuk di tepi label penting.
- **Transisi wipe lilac/pink/madu** melintas skrin (ganti flash penuh).
- **Progress bar** lilac yang diisi madu.
- **End card kad krim dengan jahitan lilac putus-putus** (macam tekstur rajut bantal), tajuk + 3 bubble.
- **Cover**: latar belah pepenjuru lilac/pink bertitik, gambar dalam bingkai krim bulat dengan jahitan, tajuk dalam speech bubble, barisan bunga kecil di bawah.

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio 0.5, visual 36.0 | ⭐ **HOOK** (J-cut atas close-up bunga lilac): "Ya Allah, bantal ni paling banyak terjual dalam live saya tau. MashaAllah dia antara yang paling ramai orang repeat order." | `PALING BANYAK TERJUAL!` 🏆 → wipe → `RAMAI REPEAT ORDER!` 🔁 |
| 6.0 | 12.5 | "Memang orang borong sampai 7, 10 biji." | `ORANG BORONG 7-10 BIJI!` 🛍️ |
| 8.5 | 17.1 | "Dah lah comel, ada senyum, ada smile macam ni." | wipe pink + `COMEL, ADA SENYUM!` 😊 + bunga kecil |
| 11.0 | 6.6 | "Saiz dia 45cm." | `SAIZ 45CM` 📏 |
| 12.4 | 19.7 | "Letak dekat kerusi ofis, korang boleh buat sandar, boleh letak alas duduk." | `KERUSI OFIS` 💼 → `BUAT SANDAR` 😌 → `ALAS DUDUK` 🪑 |
| 17.3 | 26.5 | "Nak buat bantal peluk dalam kereta. Lagi nak letak dekat sofa. Memang cantik, naik serilah ruang tamu rumah korang tu." | `PELUK DALAM KERETA` 🚗 → `LETAK ATAS SOFA` 🛋️ → wipe + `NAIK SERI RUANG TAMU!` ✨ |
| 23.9 | audio 33.5, visual 0.5 | "Jangan lupa nanti nak raya, korang boleh grab buat hiasan." (atas shot luas 3 bunga) | `HIASAN RAYA!` 🌙 |
| 28.3 | audio 39.8, visual 9.0 | "Dan ada yang buat hadiah." | `BUAT HADIAH` 🎁 |
| 29.7 | 42.7 | "Waktu sempena Hari Guru itu, sampai ada yang beli sampai 17 biji pun ada!" | `SEMPENA HARI GURU` 🍎 → wipe + `ADA BELI 17 BIJI!` 😱 |
| 34.6 | 49.6 | "Korang, tengok dekat beg kuning." | `TENGOK BEG KUNING` 🛒 |
| 36.3 | 51.5 (visual, slow-mo 0.8×) | - | End card kad krim berjahit: `BANTAL BUNGA / SENYUM` / `LILAC • PINK • KRIM` / `KORANG NAK WARNA MANA?` / `TEKAN BEG KUNING` |

Dibuang:
- **Harga (peraturan tiada harga)**: "tapi harga dia sangat-sangat mesra pocket, harga jimat", "Sekali seller buat promo", "Sekarang ada promo".
- "Ya Allah, mashaAllah, tabarakallah" (selepas borong), "Lagi nak buat apa lagi?", "dekat ruang tamu" (ulang, baru sebut), "Ya Allah, ramai betul yang buat hadiah" (ulang), "Oh mashaAllah, guru", "Okay" yang perlahan sebelum CTA (audio kekal, caption tak tulis).

## Belum pasti

- **"dalam live saya"**: Whisper dengar "life" sekali dan "hidup" dua kali. Untuk penjual, "live" paling masuk akal; caption tulis "live".
- **"Saiz dia 45cm"**: pass penuh "45cm", semakan preview "empat, lima cm"; satu pass dengar "empat peri masing-masing". Label `SAIZ 45CM` dan caption ikut 45cm. Tak dimasukkan dalam CAPTION.md.
- **"sandar"**: Whisper dengar "sandang"; maksud (sandar di kerusi ofis) lebih kena dengan "sandar".
- **"Waktu sempena Hari Guru"**: Whisper dengar "sepenuh hari guruh" / "sempena hari Guru lah".
- **CTA**: Whisper dengar "korang tengah dekat Bek Kunita / bagku"; caption tulis "Korang, tengok dekat beg kuning."

## Render

```
python3 -I sfx.py work38/sfx                                          # SFX (tambah "plink")
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_7.6.png cover.png                               # cover 1080x1536
```
