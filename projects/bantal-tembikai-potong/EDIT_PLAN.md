# Bantal Tembikai (potong, 45 / 60 / 90cm): edit plan, preview v1

Source: iPhone IMG_2922, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **60.1s**
Preview v1: **35.9s** (dipotong ~24s), 720×1280, 30fps, SDR, −11.5 LUFS
Final: **35.9s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −11.5 LUFS, sudah render
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (tembikai) + refresh

| Warna | Hex | Guna |
|---|---|---|
| Isi tembikai | `#FF6F91` | flash, progress bar, banner end card |
| Pink pekat | `#E83F6F` | teks sticker label, "marker" perkataan aktif caption |
| Hijau kulit | `#3CC24A` | highlight label, pill saiz, track progress bar |
| Hijau gelap | `#136F2E` | outline caption, bayang sticker |
| Hijau muda | `#9BE86A` | keyword caption |
| Krim kulit | `#FFF7EE` | flash lembut, bingkai cover |
| Biji | `#2A1A1F` | motif biji tembikai |
| Kuning | `#FFD23F` | BEG KUNING |

**Refresh (lain dari batch sebelum):**
- Label gaya **sticker die-cut**: teks pink pekat, outline putih tebal + bayang hijau gelap, tiada kotak, pop "spring" (besar → kecik → normal).
- Caption: perkataan aktif kekal putih tapi dapat **outline pink tebal macam marker**, bukan tukar warna.
- Motif **biji tembikai** terpercik masa flash (hook "ADA!", "3 SIZE", "TEMBIKAI!") dan jatuh perlahan atas end card.
- Flash lembut warna pink/krim (bukan putih), progress bar hijau + isi pink.
- End card: **banner reben** pink, pill bertindan. SFX baru: `boing` (gebu) dan `chomp` (tembikai).
- Cover: **bingkai kulit tembikai** (hijau gelap, hijau, krim, pink) dengan biji bertabur.

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 0.0 | ⭐ **HOOK**: "Tembikai ni ada lagi besar ke? Ada!" (bantal besar rapat ke kamera) | `ADA LAGI BESAR?` 🍉 → flash pink + biji + `ADA!` |
| 3.1 | 4.3 | "Okay kita ada lagi besar, size yang ni 90cm." (jeda dalam "yang… ni" dipotong) | `LAGI BESAR!` 😮 → `SIZE 90CM` 📏 |
| 8.1 | 10.6 | "Okay ni 60cm, ni 90cm." (dua muka sebelah-menyebelah) | `60CM` kiri + `90CM` kanan |
| 11.0 | 13.6 | "Tengoklah, beza dari segi ketebalan pun sangat-sangat berbeza." | `TENGOK KETEBALAN` 👀 → `SANGAT BEZA!` |
| 14.4 | 17.1 | "90cm macam ni, 60cm macam ni dan paling kecil size 45cm." | tangga saiz `90CM` / `60CM` / `45CM` + 🍉 besar-kecil |
| 20.9 | 25.1 | "Jadi kita ada 3 size semua." | flash + biji + `ADA 3 SIZE!` ✨ |
| 22.4 | 39.1 | "Tembikai, tembikai, tembikai!" (beat kelakar) | 3× `TEMBIKAI` pop di tempat lain + `chomp` |
| 25.9 | audio 45.2, visual 49.9 | "Sangat-sangat fluffy!" (J-cut atas close-up bulu) | `SANGAT FLUFFY` ☁️ |
| 27.2 | 52.4 | "Material jenis bulu-bulu fluffy, sangat-sangat gebu." | `BULU-BULU FLUFFY` 🧸 → `SANGAT GEBU!` 🤗 |
| 30.8 | audio 59.1, visual 56.1 | "Recommended!" (atas muka bantal) | `RECOMMENDED!` 👍 |
| 31.5 | 42.7 | "Okay, korang boleh tengok dekat beg kuning tau." (dipindah ke hujung) | `TENGOK BEG KUNING` 🛒 |
| 33.9 | 28.7 (visual, slow-mo) | - | End card: reben `BANTAL TEMBIKAI` / `45 • 60 • 90 CM` / `KORANG NAK SIZE MANA?` / `TEKAN BEG KUNING` |

Dibuang: "MashaAllah", "Okey ini 45cm" (ulang), ulangan semua saiz (30–38s), take pertama "Material jenis bulu-bulu fluffy, gebu kita", jeda.
Tiada sebut harga dalam video.

## Belum pasti

- **"Ada!"** (hook, 2.7s): pass pertama Whisper dengar "Ada.", semakan preview tak tangkap (suara perlahan). Caption tulis "Ada!".
- **"korang boleh tengok dekat beg kuning"**: Whisper dengar "terlihat" / "nanti liat tengok" / "boleh tengok". Caption ikut "boleh tengok".
- **"Material"** take kedua: satu pass dengar "Ah, material". Caption tulis "Material".

## Render

```
python3 -I sfx.py sfx/                                                  # SFX (tambah boing + chomp)
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_12.6.png cover.png                              # cover 1080x1536
```
