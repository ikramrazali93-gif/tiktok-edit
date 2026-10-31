# Kusyen Duduk, video 2 (Majalah hiasan rumah): edit plan, preview v1 (HyperFrames)

Source: IMG_3067, iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **40.4s**
Preview v1: **32.1s** (dipotong ~8s), 720×1280, 30fps, SDR, −11.7 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 165px, bawah 435px, atas 165px (1080×1920).

Video 2 daripada 5 untuk produk yang sama: kusyen duduk tufted bertekstur waffle, warna merah & beige (keluarga
produk sama dengan `../bantal-duduk-merah`). Satu shot 40.4s di jalan tanah, dia pegang kedua-dua kusyen dan
bercakap sepanjang masa. **Tiada sebutan harga** dalam klip ni. Muka dia ditutup niqab, jadi J-cut tak nampak
mulut tak sepadan.

Pipeline sama dengan siri HyperFrames: potongan, suara v2, SFX dan muzik latar perlahan guna ffmpeg; lapisan
grafik ialah komposisi **HyperFrames** (HTML + CSS + GSAP).

## Peraturan baru user: "Kurangkan text dan animation bahagian tengah video"

- **Tengah frame bersih:** kotak `KEEP_OUT` (x 160–920, y 480–1340 pada 1080×1920) tiada label, sticker,
  partikel atau burst. `place()` dalam komposisi beri kos besar kalau grafik masuk kotak ni.
- **Label sikit & kecil:** 7 label sahaja untuk 32s (2 tajuk majalah + 5 baris photo-caption nipis).
- **Zon label:** tajuk di jalur atas (bawah zon tab TikTok, atas hud dia, 44px bebas); baris photo-caption di
  jalur bawah betul-betul atas caption (y ~1342–1395). Caption kekal paling bawah (y ~1395–1470).
- **Peralihan:** tiada wipe skrin penuh. Dua "page-turn" hanya di tepi: garis merah menyapu tepi atas, nombor
  halaman `— 02 / — 03` di bucu kiri atas, dan kilat putih ringan 0.25s.
- **End card:** kulit majalah kecil: jalur masthead di atas, 2 baris kecil di bawah. Tiada panel besar di tengah.
- `check.py` lukis kotak tengah (kuning) bersama kotak kepala (cyan) dan zon UI (merah): tiada grafik dalam
  kotak tengah, termasuk end card.

## Gaya: "Majalah hiasan rumah"

| Warna / font | Nilai | Guna |
|---|---|---|
| Kertas | `#F7F3ED` | kad tajuk, baris photo-caption, jalur masthead, tanda potong |
| Dakwat | `#1F1C1A` | huruf tajuk, jalur caption (lut 84%), garis halus |
| Merah kusyen | `#C21F2C` / `#FF5A5F` | kicker, kata italik, segi empat kecil, garis bawah caption, progress, CTA |
| Font tajuk | **Playfair Display** 600–800 + italik (OFL, `comp/PLAYFAIR-OFL.txt`) | tajuk, masthead, kata kunci caption |
| Font teks | **Inter Display** 500/600/700 (OFL, `comp/INTER-LICENSE.txt`) | kicker, baris photo-caption, caption |

- **Tajuk (2):** kad kertas dengan bingkai garis halus dua lapis, kicker merah berjarak huruf
  (`—— PERJALANAN JAUH`) dan tajuk Playfair (kata kedua italik merah). Masuk dengan reveal dari atas, garis kicker
  melebar, perkataan naik satu-satu. Kalau jalur atas pendek (kepala dia tinggi), kicker dibuang dulu, kemudian
  huruf dikecilkan.
- **Baris photo-caption (5):** jalur kertas nipis, segi empat merah kecil, huruf besar Inter berjarak, garis halus
  atas & bawah yang melebar (gaya kapsyen gambar majalah).
- **Caption:** jalur dakwat lut, huruf kertas Inter 46px; kata kunci (duduk, lama, kereta, selesa, lembut,
  tersenyum…) dalam **Playfair italik**; garis merah meluncur ke perkataan yang sedang disebut.
- **Hiasan tepi:** tanda potong (crop marks) nipis di empat bucu safe zone, garis progress halus di atas.
- **End card:** jalur masthead `Kusyen Duduk EDISI 02` (Playfair, "Duduk" italik merah) di atas; `40 × 40 cm ·
  Merah · Beige` + pil merah `Tekan beg kuning 🛒` di bawah.
- **SFX:** `ding` lembut untuk tajuk & CTA, `click` untuk baris photo-caption, bunyi baru `page` (selak kertas)
  untuk page-turn, bunyi baru `shutter` (kamera) untuk end card. Muzik latar dijana (`music.wav`, bukan lagu
  berlesen), sangat perlahan bawah suara.
- **Cover:** kulit majalah: masthead `Kusyen Duduk` di langit, tag `40×40`, cover line di jalur bawah.

## Muka tak ditutup

- Kotak kepala + hud + niqab ditanda setiap 1s daripada frame proxy bergrid (`HEADS` dalam `edit.py`,
  `HEAD_PAD` 0.8s), disemak dengan melukis kotak atas frame. Setiap grafik 44px bebas daripada semua kotak kepala
  dalam tempohnya.
- Hook dibina atas shot yang kepala dia rendah (8.4s, 26.8s, 35.8s), supaya tajuk pertama muat di jalur atas.
- `check.py` (23 frame): tiada label, caption atau end card atas muka dia, dalam kotak tengah atau zon UI.
  Bila kepala dia tinggi (close-up 13–18s, 24–28s), label jadi baris photo-caption di jalur bawah.

## Susunan

| TL | Masa asal (audio / visual) | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 31.66–37.78 / 8.4, 26.8, 35.8 | ⭐ **HOOK** (J-cut): "Mak-mak korang yang mana tak boleh duduk lama, ataupun mami-mami pregnant tak boleh duduk lama tu, korang kena ada satu bantal macam ni." | tajuk `Tak boleh duduk lama?` → baris `UNTUK MAK & IBU MENGANDUNG` |
| 6.1 | 0.40–8.38 | "Tak sangka bantal ni boleh buat kita lebih selesa dekat dalam kereta. Yang mana drive lama-lama." | tajuk `PERJALANAN JAUH · Selesa dalam kereta` |
| 14.1 | 11.28–16.20 | page-turn + "Selesa. Sebab korang tengok dia punya ketebalan memang lembut. Memang selesa." (dia picit kusyen) | baris `TEBAL & LEMBUT` |
| 19.0 | 16.52–20.86 | "Saiz dia pun 40cm × 40cm, ni ngam elok dengan seat driver tu." | baris `40 × 40 CM · NGAM SEAT DRIVER` |
| 23.4 | 21.72–26.66 | page-turn + "Kalau korang ada satu macam ni, lebih selesa dan boleh buat korang tersenyum." | baris `DUDUK SELESA, BOLEH SENYUM 😊` |
| 28.3 | 38.50–39.82 | CTA: "Tengok dekat bawah sekarang." | baris `TENGOK BEG KUNING 👇` |
| 29.6 | 29.10–31.62 (senyap) | dia lambai dengan kusyen beige | end card kulit majalah |

Dibuang: "kan." selepas "lama-lama", "Korang kena ada satu bantal macam ni." yang pertama (9.2–11.1s, sama dengan
hujung hook), "okay" kecil sebelum "Memang selesa", "Orang kata boleh duduk lama lah." (27.5–31.1s, mengulang hook;
bawah end card suara dimute), jeda dan hujung klip. Tiada ayat harga dalam klip ni.

## Belum pasti

- **"ngam elok dengan seat driver"**: Whisper dengar "ingam airlock" / "ngam airlock". Maksudnya "ngam elok"
  (muat elok), jadi caption tulis "ngam elok".
- **"ataupun mami-mami pregnant"**: semakan preview dengar "mak-mak pregnant". Caption ikut pass per bahagian
  ("mami-mami").
- **"Kalau korang ada satu macam ni"**: "Kalau" perlahan; transkripsi penuh tak dengar.
- **"Yang mana drive lama-lama"**: ada bunyi pendek "ok" sebelum "Yang" (disimpan dalam audio, tak masuk caption).
- **CTA "dekat bawah"**: dia maksudkan beg kuning di bawah skrin, jadi label tulis `Tengok beg kuning 👇`.

## Render (HyperFrames)

```
cd comp && npm install && cd ..                      # hyperframes@0.8.181 (dipin dalam comp/package.json)
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell   # pilihan

python3 sfx.py sfx/                                                  # semua SFX + music.wav (+ page, shutter)
python3 edit.py proxy.mp4 transcript.json sfx/ out/                  # preview: out/preview.mp4 (720x1280)
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final   # final:   final/final.mp4 (1080x1920)
python3 edit.py proxy.mp4 transcript.json sfx/ out/ --graphics-only  # ubah grafik sahaja, guna semula out/base.mp4
python3 check.py out/ check.jpg                                      # check sheet: zon UI + kotak kepala + kotak tengah

cd cover && npx --prefix ../comp hyperframes snapshot . --at 0.5 --no-end -o snap   # cover -> snap/*.png -> ../cover.jpg
```

Kata-kata caption datang daripada `OVERRIDE` dalam `edit.py` (disemak dengan transkripsi semula per bahagian +
envelope bunyi). `BREAK_BEFORE` tetapkan di mana caption pecah baris.

**Masa render:** di container ni (4 CPU, tiada GPU, render lain berjalan serentak), HyperFrames capture 32.1s
(964 frame) ambil lebih kurang 2m 6s; keseluruhan pipeline preview ~3m 50s; render grafik sahaja ~4m 20s.
