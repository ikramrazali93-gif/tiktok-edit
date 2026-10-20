# Bantal Avocado (montel 70cm + panjang 90cm): edit plan, preview v1

Source: IMG_2935, iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **60.5s**, luar rumah atas rumput
Preview v1: **39.6s** (dipotong ~21s), 720×1280, 30fps, SDR, −11.4 LUFS
Final: **39.6s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −11.4 LUFS, sudah render
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (ikut avocado) + refresh

| Warna | Hex | Guna |
|---|---|---|
| Kulit avocado | `#2E5A1C` | outline caption, teks label, bayang, rim end card |
| Hijau daun | `#5E9B2E` | daun jatuh, label hijau, blinds |
| Lime (isi) | `#C9EB4B` | perkataan aktif caption, label lime, titik progress bar, rim badge biji |
| Krim (isi pucat) | `#F6F8D2` | label krim, rim dalam, blinds |
| Biji | `#6A3B1F` | badge biji pada label, biji end card |
| Blush (pipi) | `#FF8FB1` | kata kunci caption, label birthday suami / gebu |

**Refresh (lain dari batch sebelum & batch-4 lain: pill, sticker, bayang blok, speech bubble, patch, tiket):**
- **Label "biji avocado"**: pill rata dengan **badge bulat coklat (biji)** di hujung kiri; emoji duduk dalam biji.
  Label **jatuh dari atas dan mendarat dengan squash** kecil, bunyi baru **"thud"** (bantal).
- **Caption**: perkataan aktif **diangkat keluar** dan dilukis sendiri dalam lime dengan **lantunan skala**
  (posisi diukur dengan Pillow, baris tak beralih); kata kunci pink blush.
- **Transisi blinds**: 6 jalur mendatar lime/hijau/krim masuk dari kiri-kanan berselang lalu tarik balik, bunyi
  baru **"shutter"** (klik-klik).
- **Motif daun avocado** gugur di tepi skrin setiap tukar bahagian.
- **Progress bar bertitik**: titik krim di atas, titik lime "terisi" ikut masa.
- **End card**: **separuh avocado besar** (kulit + rim krim + isi lime + biji) dengan tajuk atas isi + 3 label biji.
- **Cover**: wallpaper mint corak avocado kecil, gambar dalam **tingkap bucu bulat bergelang avocado**
  (kulit/krim/lime), tajuk sticker outline berganda, badge biji "GEBU GEBAS!", pill saiz berbadge biji.
- Render: lapisan emoji sticker kini di **atas** ASS (supaya emoji duduk dalam badge biji).

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio 8.0, visual 38.2 | ⭐ **HOOK** (J-cut atas avocado montel ditolak ke kamera sampai muka penuh skrin): "Korang mana satu? Korang montel ke panjang? Kalau montel ambil montel." | `KORANG MANA SATU?` 🤔 → `MONTEL KE PANJANG?` 🥑 → `MONTEL? AMBIL MONTEL!` 😋 |
| 3.7 | 0.0 | "Peminat warna hijau. Avocado hijau dia cantik betul. Ada dua bentuk. Nak yang montel, nak yang panjang." | blinds → `PEMINAT HIJAU?` 💚 → `AVOCADO CANTIK BETUL` ✨ → `ADA 2 BENTUK!` ✌️ → `YANG MONTEL` → `YANG PANJANG` |
| 11.3 | 12.1 / 14.85 | "Okey ini yang panjang 90cm. Yang ini yang montel 70cm." | `PANJANG 90CM` 📏 → `MONTEL 70CM` 🥑 |
| 16.1 | 17.3 | "Gebu-gebas, sedap peluk." (dia tolak avocado ke kamera) | `GEBU-GEBAS!` ☁️ → `SEDAP PELUK` 🤗 |
| 18.5 | 19.8 / 23.05 (hujung atas muka avocado 41.9) | "Buat hadiah pun sangat sesuai kan. Siapa yang ada bestfriend, birthday bestfriend, birthday anak ke, birthday isteri ke, birthday suami ke." | `SESUAI BUAT HADIAH` 🎁 → `BIRTHDAY BESTFRIEND` 👯 → `ANAK` 🧒 → `ISTERI` 👩 → `SUAMI` 👨 |
| 29.2 | audio 41.4 + 53.1, visual 50.3 (close-up kain belakang) | "Material dia jenis material kain velvet, material tahan lasak, tak berbulu, boleh basuh." + "Ada zip juga." | `KAIN VELVET` 🧵 → `TAHAN LASAK` 💪 → `TAK BERBULU` 👌 → `BOLEH BASUH` 🫧 → `ADA ZIP JUGA` 🤐 |
| 35.2 | 47.7 | "Tengok dekat beg kuning tau." | `TENGOK BEG KUNING` 🛒 |
| 36.6 | 57.2 (wide, slow ×0.8) | - | End card: separuh avocado `BANTAL AVOCADO` / `MONTEL • PANJANG` / `KORANG TEAM MANA?` / `TEKAN BEG KUNING` |

Dibuang:
- "Beli-beli ni, gegar boba(ik) semua boleh. Untuk avocado lembut" (tak jelas: Whisper dengar "gege bobaik" / "gegar boba").
- **"…dan harga dia sangat-sangat mesra poket"** (peraturan tiada harga).
- Ayat hook di tempat asal (8.0s), jeda selepas "90cm", senyap / bunyi angin di hujung.

## Belum pasti

- **"Gebu-gebas"**: Whisper dengar "gebu-gebas" / "gebur-gebur"; caption tulis "Gebu-gebas".
- **"Korang"**: Whisper dengar "Kau orang"; caption tulis "Korang".
- **"montel"** dalam hook: semakan per-chunk dengar "montai"; maksud ayat jelas "montel".
- **"Peminat"**: Whisper tulis "Perminat"; caption betulkan "Peminat".
- **Ayat yang dibuang** "gegar boba… semua boleh": tak dapat dipastikan, jadi tak digunakan.

## Render

```
python3 sfx.py sfx/                                                       # SFX (tambah thud + shutter)
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_20.5.png cover.png                              # cover 1080x1536 (simpan cover.jpg q92)
```
