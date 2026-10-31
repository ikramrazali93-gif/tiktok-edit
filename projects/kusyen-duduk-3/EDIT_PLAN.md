# Kusyen Duduk, video 3 (Senarai semak / notepad): edit plan, preview v1 (HyperFrames)

Source: IMG_3068, iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **43.0s**
Preview v1: **29.4s** (dipotong ~14s), 720×1280, 30fps, SDR, −11.7 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 165px, bawah 435px, atas 165px (1080×1920).

Video 3 daripada 5 untuk produk yang sama: kusyen duduk tufted bertekstur waffle, warna merah & beige (keluarga
produk sama dengan `../bantal-duduk-merah`). Satu shot 43.0s di jalan tanah, dia pegang kedua-dua kusyen dan
bercakap sepanjang masa. **Tiada sebutan harga** dalam klip ni. Muka dia ditutup niqab, jadi J-cut tak nampak
mulut tak sepadan. Dia pakai hoodie karakter: nama karakter tak disebut di mana-mana.

Pipeline sama dengan siri HyperFrames: potongan, suara v2, SFX dan muzik latar perlahan guna ffmpeg; lapisan
grafik ialah komposisi **HyperFrames** (HTML + CSS + GSAP).

## Peraturan user: "Kurangkan text dan animation bahagian tengah video"

- **Tengah frame bersih:** kotak `KEEP_OUT` (x 160–920, y 480–1340 pada 1080×1920) tiada label, sticker atau
  partikel. `place()` dalam komposisi beri kos besar kalau grafik masuk kotak ni.
- **Label sikit & kecil:** 6 label sahaja untuk 29s (sticky note hook, 1 baris saiz, 1 senarai semak tempat,
  2 sticky note warna, 1 baris CTA).
- **Zon label:** jalur atas (bawah zon tab TikTok, atas hud dia, 44px bebas) atau bucu kiri atas di sebelah
  kepala; jalur bawah betul-betul atas caption hanya bila atas penuh. Caption kekal paling bawah.
- **Peralihan:** tiada wipe skrin penuh. Satu "coretan pen" biru di tepi atas + kilat kertas ringan 0.2s.
- **End card:** halaman buku nota kecil di jalur atas + label CTA merah di jalur bawah. Tiada panel di tengah.

## Gaya: "Senarai semak / notepad"

| Warna / font | Nilai | Guna |
|---|---|---|
| Kertas | `#FFFDF4` + garis biru `rgba(84,140,214,.42)` + garis margin merah `#E5636B` | senarai semak, baris, caption, end card |
| Dakwat biru | `#1D3E9E` / `#122B73` | tulisan tangan, kotak semak, progress bar, coretan pen |
| Merah kusyen | `#C8102E` | tanda ✓, garis bawah bertanda, kata kunci caption, CTA |
| Sticky note | kuning `#FFE680`, merah `#FF7B7B`, beige `#EAD2AE` | hook, "Merah terang", "Lembut & estetik" |
| Highlighter | `#FFE14D` | sapuan di bawah perkataan yang sedang disebut |
| Font tulisan tangan | **Caveat** 600/700 (OFL, `comp/CAVEAT-OFL.txt`) | sticky note, tajuk senarai, end card |
| Font teks | **Patrick Hand** (OFL, `comp/PATRICKHAND-OFL.txt`) | caption, baris senarai semak |

- **Sticky note hook:** kertas kuning dengan pita lut, jatuh masuk (back-out), perkataan "ditulis" satu-satu,
  garis bawah merah dilukis di bawah "lama-lama".
- **Senarai semak tempat (tanda tangan video ni):** kertas bergaris dengan margin merah dan klip kertas, tajuk
  "Ngam untuk:", baris muncul dan **ditanda ✓ tepat bila dia sebut** kerusi ofis, meja makan, dalam kereta, sofa.
- **Baris semak:** jalur kertas kecil dengan kotak + tanda ✓ dilukis (saiz 40 × 40 cm, CTA).
- **Sticky note warna:** merah ("Merah terang ❤️") dan beige ("Lembut & estetik 🤎"), dengan pin biru dan
  bucu terlipat, pecah 2 baris kalau ruang sempit.
- **Caption:** jalur kertas bergaris, tulisan tangan biru, kata kunci merah, sapuan highlighter kuning di bawah
  perkataan yang sedang disebut.
- **Progress:** garis pen biru di tepi atas dengan ✏️ bergerak.
- **SFX:** bunyi baru `pen` (coretan pen), `tick` (tanda pada kotak) dan `stick` (sticky note ditekan). Muzik
  latar dijana (`music.wav`, bukan lagu berlesen), sangat perlahan bawah suara.
- **Cover:** sticky note hook di langit, senarai semak "Ngam untuk:" di kiri kepala, tag 40 × 40 cm dan sticky
  note "Merah terang" / "Beige lembut" di kanan kepala, garis spiral buku nota di atas.

## Muka tak ditutup

- Kotak kepala + hud + niqab ditanda setiap 1s daripada frame proxy bergrid (`HEADS` dalam `edit.py`,
  `HEAD_PAD` 0.55s). Setiap grafik 44px bebas daripada semua kotak kepala dalam tempohnya.
- Sticky note hook berakhir sebelum shot zoom (6s), sebab kepala dia naik dalam shot tu dan jalur atas jadi pendek.
- Sticky note "Lembut & estetik" berakhir bersama shotnya: dalam shot seterusnya kepala dia beralih ke kiri.
- `check.py` (21 frame): tiada label, caption atau end card atas muka dia, dalam kotak tengah atau zon UI.

## Susunan

| TL | Masa asal (audio / visual) | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 1.32–7.98 | ⭐ **HOOK** (ayat pembuka dia sendiri): "Korang yang duduk lama-lama sampai keras, habis belakang ni sakit tu. Cuba ada bantal ni satu." | sticky note `Duduk lama-lama sampai keras? 😩` |
| 6.7 | 18.32–24.42 | "Yang saiz dia 40cm × 40cm ni memang elok, ngam untuk kerusi ofis, kerusi meja makan, dalam kereta." | baris `☑ 40 × 40 cm` → senarai `Ngam untuk:` ✓ kerusi ofis ✓ meja makan ✓ dalam kereta |
| 12.8 | 25.02–28.22 / 25.0 + 13.9 (sisi) | "Sofa semua boleh. Belakang, depan, belakang ni macam ni." | ✓ sofa (senarai yang sama) |
| 16.0 | 29.40–36.62 | coretan pen + "Warna dia pun cantik-cantik. Siapa minat warna merah terang, elok macam ni pun ada. Minat kaler-kaler lembut-lembut, barang-barang estetik pun ada." | sticky `Merah terang ❤️` → sticky `Lembut & estetik 🤎` |
| 23.2 | 38.06–40.00 | "Bukan senang nak cari kaler-kaler gini tau." | (caption sahaja) |
| 25.1 | 40.42–42.42 | CTA: "Tengok dekat bawah sekarang." | baris `☑ Tengok beg kuning 👇` |
| 27.1 | 0.05–1.65 (×0.7, senyap) | shot luas dua kusyen | end card buku nota `Kusyen duduk` ✓ 40×40 ✓ merah & beige ✓ ofis · rumah · kereta + `Tekan beg kuning 🛒` |

Dibuang: "start" di awal, **"Mungkin boleh redakan sikit kan?"** (tiada tuntutan kesihatan dalam siri ni),
"keras-keras / tak nak kaler-kaler…" (tak jelas), "Korang boleh try tengok bantal ni" (ulang hook), "Gitu.",
"Haa,", "nah" selepas "ada", jeda. Tiada ayat harga dalam klip ni.

## Belum pasti

- **"Korang"**: dia sebut "Kau-orang" dengan jeda kecil; Whisper dengar "Kau orang".
- **"Sofa semua boleh"**: Whisper tulis "So far semua boleh"; maksudnya sofa (sambungan senarai tempat).
- **"Belakang, depan, belakang ni macam ni"**: dia tunjuk kedua-dua belah kusyen; caption ikut bunyi.
- **"kaler-kaler gini"**: Whisper dengar "gala-gala guni" / "kala-kala kuni".
- **"ngam"**: Whisper tulis "Engam".

## Render (HyperFrames)

```
cd comp && npm install && cd ..                      # hyperframes@0.8.181 (dipin dalam comp/package.json)
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell   # pilihan

python3 sfx.py sfx/                                                  # semua SFX + music.wav (+ pen, tick, stick)
python3 edit.py proxy.mp4 transcript.json sfx/ out/                  # preview: out/preview.mp4 (720x1280)
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final   # final:   final/final.mp4 (1080x1920)
python3 edit.py proxy.mp4 transcript.json sfx/ out/ --graphics-only  # ubah grafik sahaja, guna semula out/base.mp4
python3 check.py out/ check.jpg                                      # check sheet: zon UI + kotak kepala + kotak tengah

cd cover && npx --prefix ../comp hyperframes snapshot . --at 0.5 --no-end -o snap   # cover -> snap/*.png -> ../cover.jpg
```

Kata-kata caption datang daripada `OVERRIDE` dalam `edit.py` (disemak dengan transkripsi semula per bahagian +
envelope bunyi). `BREAK_BEFORE` tetapkan di mana caption pecah baris.

**Masa render:** di container ni (4 CPU, tiada GPU, render lain berjalan serentak), HyperFrames capture 29.4s
(~882 frame) ambil lebih kurang 1m 45s; keseluruhan pipeline preview ~3m 10s; render grafik sahaja ~3m.
