# Bantal Pisang (peluk, duduk atas rumput, IMG_2932): edit plan, preview v1

Source: iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **45.9s**
Preview v1: **40.3s** (dipotong ~6s; dia bercakap hampir tanpa henti), 720×1280, 30fps, SDR, −11.7 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (piknik) + refresh

| Warna | Hex | Guna |
|---|---|---|
| Kuning pisang | `#FFD93B` | perkataan aktif + bar bawahnya, tiket penting, progress bar |
| Merah gingham | `#E5484D` | highlight dalam tiket, bintang tiket, starburst, kain piknik end card/cover |
| Krim | `#FFF8E1` | tiket biasa, latar kain piknik |
| Coklat (hujung pisang) | `#5A3A22` | teks tiket, outline caption, "hujung pisang" progress bar |
| Hijau daun | `#4FA84A` | highlight sekunder (KENA ADA, SEDANG, 50CM travel) |

Refresh (lain dari batch sebelum, `bantal-pisang` lama dan video batch-4 lain):
- **Label tiket (ticket stub)**: takuk separuh bulat kiri/kanan, garis perforasi putus-putus + bintang kecil
  pada stub, bayang keras coklat; masuk dengan **slide dari tepi** (kiri/kanan berselang) + fade, bunyi "tick" kertas.
- **Caption**: perkataan aktif kuning + **bar garis bawah kuning** (outline coklat) di bawah perkataan tu,
  diukur dengan Pillow; chunk panjang dikecilkan supaya kekal satu baris.
- **Starburst komik** (kuning/merah, berpusing perlahan) di belakang ayat penting: NUTRISEN/GIZI, KENA ADA,
  3 SIZE, RECOMMENDED. SFX baru "boing" untuk lawak "terlebih gizi".
- **Zoom-punch** setiap mula bahagian (0.2s dekat sikit lepas tu normal), bukan flash.
- **Progress bar** pisang: isi kuning + "hujung pisang" coklat bergerak di depan.
- **End card kain piknik gingham merah-krim** + 4 tiket bertingkat.
- **Cover**: bingkai kain piknik gingham, gambar dalam tingkap bucu bulat rim putih, tajuk tiket
  "PISANG TERLEBIH / GIZI!", tiket saiz di bawah, burst "GEBU SANGAT!".

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 24.4 + 26.4 + 30.4 | ⭐ **HOOK** (lawak, dia peluk yang 70cm): "Hat ni pisang terlebih nutrisen. Hat ni pisang terlebih... gizi!" | burst + tiket `PISANG TERLEBIH NUTRISEN` 😂 → burst merah + `TERLEBIH GIZI!` 💪🍌 |
| 5.3 | 0.5 / 4.2 | "Peminat pisang? Peminat kerepek pisang ke? Peminat pisang banana, salai ke apa ke?" | `PEMINAT PISANG?` → `KEREPEK PISANG?` → `PISANG BANANA!` → `PISANG SALAI?` |
| 12.0 | 8.2 / 11.6 | "Korang dah ada ke pisang yang ni? Pisang yang ni tak ada lagi?" + "Kena ada hat ni jugak." | `DAH ADA YANG NI?` 👀 → `BELUM ADA LAGI?` 😱 → burst + `KENA ADA!` ✅ |
| 16.7 | 13.1–24.3 | "Hat ni tengoklah, 70cm punya lah gebu, 50cm hat ni, hat ni size sedang-sedang. Hat paling kecil, size 35cm." + "Ada 3 size pisang." | `TENGOK NI!` → `70CM GEBU!` ☁️ → `50CM` → `SIZE SEDANG` 👌 → `PALING KECIL 35CM` 🤏 → burst + `ADA 3 SIZE!` |
| 27.1 | 32.3–42.7 | "Hat ni gebu-gebu macam ni, size 70cm. Memang recommended. Kalau nak bawa travel, ambil 50cm. Untuk baby-baby bawah setahun, boleh ambil yang size 35cm. Korang tengok dekat beg kuning." | `GEBU-GEBU` 🤗 → burst + `70CM RECOMMENDED!` 👍 → `TRAVEL? 50CM` ✈️ → `BABY BAWAH SETAHUN` 👶 → `AMBIL 35CM` 🍼 → `TEKAN BEG KUNING` 🛒 |
| 37.5 | 43.0 (visual, lambai dengan 3 pisang) | - (suara dimute) | End card gingham: `BANTAL PISANG` / `35 • 50 • 70 CM` / `KORANG TEAM SIZE MANA?` / `TEKAN BEG KUNING` |

Dibuang:
- **"Seller tengah bagi harga runtuh"** (ayat harga/promo, ikut peraturan tiada harga).
- Bunyi/gelak selepas "kerepek pisang ke?" dan selepas "35cm", "aah" senyap sebelum "gizi".
- "Hat ni ambil hat ni" (tak jelas, sebelum "gebu-gebu").

## Belum pasti

- **"hat ni"** (loghat utara = "yang ni"): Whisper dengar "hat ni", "harga ni", "ani" atau "hati ni". Caption tulis "hat ni".
- **"gizi"** di hujung hook: Whisper dengar "jeezy"; ikut maksud ("terlebih nutrisen / terlebih gizi") caption tulis "gizi".
- **"Peminat pisang banana"**: semakan preview tak tangkap "Peminat" yang kedua (perlahan), transkrip penuh dengar.
- **"bawa travel"**: Whisper dengar "buat travel" dan "bawa travel"; caption tulis "bawa".
- **"gebu-gebu"**: Whisper dengar "gebu-gebah".

## Render

```
python3 sfx.py sfx/
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_2.0.png cover.jpg                               # cover 1080x1536
```
