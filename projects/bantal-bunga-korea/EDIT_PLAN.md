# Bantal Bunga 50cm (ala-ala Korea): edit plan, preview v1

Source: iPhone (IMG_2928), 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, luar rumah atas rumput, **55.8s**
Preview v1: **42.4s** (dipotong ~13s), 720×1280, 30fps, SDR, −11.6 LUFS
Final: **42.4s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −11.6 LUFS, sudah render
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (ikut bantal bunga)

| Warna | Hex | Guna |
|---|---|---|
| Espresso (tengah bunga dark brown) | `#483020` | teks label, outline caption & bubble |
| Lilac (bunga purple) | `#B4A0E2` | kotak perkataan aktif caption, wipe, bubble purple |
| Lilac gelap | `#7A60B0` | highlight dalam bubble krim, "BUNGA" |
| Krim (paip putih + bunga beige) | `#FAF2E4` | bubble, latar end card |
| Mustard (bunga kuning) | `#F2B43C` | keyword caption, progress bar, badge bunga end card |
| Rose (kaler pink) | `#F5A0B4` | COMELNYA!, PINK PUN CANTIK |
| Kuning | `#FFD23F` | TENGOK / TEKAN BEG KUNING |

## Refresh (lain dari batch sebelum, dan lain dari kucing-tidur / tembikai-potong)

- **Label speech bubble**: bubble rata (outline espresso nipis + bayang keras offset), ekor kiri/kanan berselang,
  tiada senget; masuk dengan **slide-up + fade** (bukan pop skala). SFX baru **pluck** (petik tali) untuk bubble.
- **Caption**: perkataan aktif duduk atas **kotak lilac bulat** (kedudukan diukur dengan Pillow), bukan tukar warna /
  blob / marker. Keyword warna mustard. Chunk panjang dikecilkan supaya kekal satu baris.
- **Transisi**: **jalur lilac/mustard senget menyapu** skrin setiap tukar bahagian (bukan flash penuh).
- **Motif bunga kecil** (lilac/krim/mustard) berpusing naik di tepi skrin setiap tukar bahagian.
- **End card**: **badge bunga mustard besar** ("BANTAL BUNGA") + 3 bubble bertindan.
- **Cover**: latar **dua warna bersilang** (lilac/mustard) bertitik, gambar dalam **tingkap arch**, badge bunga "SAIZ 50CM".

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio 0.05 + 17.5, visual 52.2 (push-in tekstur bunga kuning) + 17.5 | ⭐ **HOOK** (J-cut): "Ya Allah, terbaiknya! Gebunya bantal ni." + "Saiz dia 50cm, besar macam ni!" | `YA ALLAH, TERBAIK!` 😍 → `GEBUNYA!` ☁️ → wipe → `SAIZ 50CM!` 📏 → `BESAR MACAM NI!` 🙌 |
| 5.8 | 3.9 | "Bantal bunga ni tu, ketebalan dia, ya Allah ya Rabbi, sedapnya peluk!" | `BANTAL BUNGA` 🌼 → `TEBAL & GEBU` ☁️ → `SEDAP PELUK!` 🤗 |
| 10.9 | 9.3 | "Buat bantal peluk, buat bantal dekat kerusi ofis, alas belakang, alas duduk dalam kereta, buat bantal kepala pun boleh." | `BANTAL PELUK` 🫂 → `KERUSI OFIS` 💼 → `ALAS BELAKANG` 🪑 → `ALAS DUDUK KERETA` 🚗 → `BANTAL KEPALA` 😴 |
| 18.1 | 36.4 | "Dia ada macam-macam colour." | `MACAM-MACAM KALER!` 🎨 |
| 19.0 | 23.2 | "Ni colour beige, lawa estetik kan. Ni colour purple, nampak tak, dia ada line-line, line putih macam ni, dia nampak lebih menyerlah bunga dia." (close-up paip putih) | `KALER BEIGE` 🤎 → `LAWA ESTETIK` ✨ → `KALER PURPLE` 💜 → `ADA LINE PUTIH` 🤍 → `LEBIH MENYERLAH!` 🌟 |
| 28.6 | 33.3 | "Material dia ala-ala Korea kita. Comelnya!" | `ALA-ALA KOREA` 💫 → `COMELNYA!` 🥰 |
| 31.4 | 38.0 / 40.8 | "Colour-colour macam ala-ala kuning-kuning, oren macam tu. Colour purple, colour beige, ada dark brown." | `KALER KUNING` 💛 → `PURPLE • BEIGE` 💜 → `DARK BROWN` 🤎 |
| 37.0 | 45.0 | "Pink pun cantik. Korang tengok dekat beg kuning!" | `PINK PUN CANTIK` 🩷 → `TENGOK BEG KUNING` 🛒 |
| 39.1 | 47.6 (visual, ×0.85) | - | End card: badge bunga `BANTAL BUNGA` / `SAIZ 50CM • ALA-ALA KOREA` / `KORANG SUKA KALER MANA?` / `TEKAN BEG KUNING` |

Dibuang: "Wah masyaAllah", "Dan dia... apa tu ada macam-macam kaler lah" (lambat, diganti versi pendek di 36.4s),
"Okay lah", "ha" selepas "Comelnya", "Ini color,", "Ya Allah macam-macam colour lah", **"ha, tengok dekat beg kuning,
harga dia sangat-sangat berbaloi"** (ulang CTA + sebut harga: peraturan tiada harga), senyap/angin di hujung.

## Belum pasti

- **"kerusi ofis"**: Whisper tulis "kursi ofis"; caption tulis "kerusi".
- **"Comelnya!"** (35.2s): pass pertama dengar "cerminnya", pass kedua "Comelnya". Caption ikut "Comelnya".
- **"Dia ada macam-macam colour"**: semakan preview awal dengar "Tak ada"; titik mula dianjak sedikit, semakan akhir dengar "dia ada".
- **Senarai kaler**: dia sebut beige, purple, kuning/oren, dark brown, pink. Dalam video hanya purple, beige (tengah coklat) dan kuning ditunjuk.

## Render

```
python3 sfx.py sfx/                                                     # SFX (tambah pluck, pluck_hi)
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_48.6.png cover.jpg                              # cover 1080x1536
```
