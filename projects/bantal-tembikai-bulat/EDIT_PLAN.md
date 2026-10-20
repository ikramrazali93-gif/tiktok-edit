# Bantal Tembikai Bulat (ada kaki & tangan): edit plan, preview v1

Source: iPhone IMG_2925, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **67.5s**, luar rumah atas rumput
Preview v1: **41.5s** (dipotong ~26s), 720×1280, 30fps, SDR, −11.4 LUFS
Final: **41.5s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −11.4 LUFS, sudah render
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (tembikai) + refresh

| Warna | Hex | Guna |
|---|---|---|
| Hijau kulit gelap | `#1E5A31` | outline caption, outline label, end card |
| Hijau kulit | `#3FA34D` | label, progress bar |
| Hijau pucat (tangan/kaki) | `#B9E4A0` | keyword caption, garis progress bar |
| Pink isi tembikai | `#FF5C8A` | perkataan aktif caption, flash |
| Merah tembikai | `#E0245E` | outline label "wow", reben end card |
| Kuning | `#FFD23F` | highlight dalam label |

Refresh yang dipakai (lain dari batch sebelum ni):
- **Label gaya sticker die-cut**: tiada kotak; teks putih dengan outline warna + outline putih tebal + bayang.
- **Caption**: perkataan aktif jadi pink tembikai dengan outline putih (macam sticker), keyword hijau pucat.
- **Motif biji tembikai**: biji hitam kecil pop-in dan bergoyang di sekeliling label penting.
- **Flash pink lembut** ganti flash putih; progress bar macam kulit tembikai (2 lapis hijau).
- **End card reben** (banner merah hujung bertakuk) + label sticker bertingkat.
- **Cover**: gambar dalam bingkai polaroid senget, washi tape, latar isi tembikai berbiji, jalur kulit di bawah.

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio 15.3, visual 42.4 | ⭐ **HOOK** (J-cut atas close-up muka tembikai): "Dah ada ke belum tembikai? Comel ni, nampak tak?" | `DAH ADA TEMBIKAI?` 🍉 + biji → flash pink + `COMEL NI!` 👀 |
| 2.8 | 4.6 / 8.2 | "Unboxing lagi, jom kita tengok. Apa pula kali ni?" | `UNBOXING LAGI!` 📦 → `JOM TENGOK!` → `APA KALI NI?` 🤔 |
| 6.5 | 9.3–13.2 | koyak parcel (×3) | tag `>> x3` |
| 7.8 | 13.2 | "Tembikai, korang!" | flash + `TEMBIKAI!` 🍉 + biji |
| 9.6 | 18.1–25.3 | keluarkan dari plastik (×3) | `>> x3`, `BUKA PLASTIK` |
| 12.0 | 25.4 | "Ya Allah! Besar bulat macam ni, gemoy macam ni! Bestnya!" | `YA ALLAH!` 😱 → `BESAR & BULAT` ⭕ → `GEMOY!` 🥹 + biji → `BESTNYA!` 😍 |
| 17.8 | 32.8 | "Boleh buat hadiah, boleh buat bantal peluk." | `BOLEH BUAT HADIAH` 🎁 → `BANTAL PELUK` 🤗 |
| 21.8 | 37.8 | "Comelnya!" | `COMELNYA!` 💕 |
| 22.9 | 40.1 | "Dalam material dia ni bulu-bulu fluffy." | `BULU-BULU FLUFFY` ☁️ |
| 25.2 | 44.6 | "Ada kaki, ada tangan." | `ADA KAKI & TANGAN` 🙌 |
| 26.7 | 46.3 | "Mesti anak korang suka. Bukan anak korang saja suka, mama pun suka!" | `ANAK MESTI SUKA` 👧 → flash + `MAMA PUN SUKA!` 💖 + biji |
| 32.1 | 52.0 | "Belilah satu, beli buat hadiah untuk birthday anak. Confirm anak happy, excited lah!" | `HADIAH BIRTHDAY ANAK` 🎂 → `ANAK HAPPY!` 🥳 |
| 37.8 | 65.8 | "Tekan beg kuning." | `TEKAN BEG KUNING` 🛒 |
| 39.0 | 61.6 (visual, dia pegang tembikai) | - | End card: reben `BANTAL TEMBIKAI` / `BULAT • GEBU • ADA KAKI` / `TAG MAMA YANG SUKA COMEL!` / `TEKAN BEG KUNING` |

Dibuang: 0–1.5s (label parcel/waybill nampak), "Unboxing lagi 1,2,3" yang pertama, "Sebentar kita buka, nampak dia", "Comel kan?" (ulang), "Ya Allah" panjang selepas "fluffy", "Saya pun excited… anak kita tak excited kan… nampaknya" (tak jelas), "Mmm so fluffy" (ulang), jeda.
Harga: video tak sebut harga, jadi tiada apa nak dibuang. Bunyi "kaching" tak dipakai.

## Belum pasti

- **"gemoy"**: Whisper dengar "gemuai" dua kali, "Gemoy" sekali. Caption tulis "gemoy" (slang comel/montel).
- **"material dia ni"**: satu pass dengar "material jenis". Caption tulis "dia ni".
- **"beli buat hadiah untuk birthday anak"**: satu pass dengar "boleh buat hadiah", satu lagi "beli bahagian untuk hari jadi". Caption tulis "beli buat hadiah untuk birthday anak".
- **"anak korang saja suka"**: semakan preview dengar "tu" ganti "saja".

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_62.2.png cover.jpg                              # cover 1080x1536
```
