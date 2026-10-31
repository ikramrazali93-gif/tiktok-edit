# Kusyen Duduk, video 5 (Hygge kait hangat): edit plan, preview v1 (HyperFrames)

Source: IMG_3070, iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **37.7s**
Preview v1: **28.1s** (dipotong ~9.6s), 720×1280, 30fps, SDR, −11.7 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 165px, bawah 435px, atas 165px (1080×1920).

Video 5 daripada 5 untuk produk yang sama: kusyen duduk tufted bertekstur waffle, warna merah & beige (keluarga
produk sama dengan `../bantal-duduk-merah`). Satu klip 37.7s di bawah porch/carport, baju lain daripada video 1–4:
4 saat pertama close-up muka (selfie) masa dia tanya soalan, lepas tu dia turunkan telefon dan pegang kedua-dua
kusyen. **Tiada sebutan harga** dalam klip ni. Muka dia ditutup niqab, jadi J-cut tak nampak mulut tak sepadan.

Pipeline sama dengan siri HyperFrames: potongan, suara v2, SFX dan muzik latar perlahan guna ffmpeg; lapisan
grafik ialah komposisi **HyperFrames** (HTML + CSS + GSAP).

## Peraturan user: "Kurangkan text dan animation bahagian tengah video"

- **Tengah frame bersih:** kotak `KEEP_OUT` (x 160–920, y 480–1340 pada 1080×1920) tiada label, sticker atau
  partikel. Tag di jalur bawah boleh masuk 40px sahaja di tepi bawah kotak (kawasan hujung kusyen / baju), sebab
  dalam shot close-up ruang antara kotak dan caption cuma ~65px. Tag hook (close-up muka, tiada produk) boleh
  masuk 70px.
- **Label sikit & kecil:** 6 tag sahaja untuk 28s (hook, "peneman sofa", "duduk atas dia", 40 × 40 cm, kain
  waffle, boleh basuh). CTA dibawa oleh caption dan end card, tiada tag lain.
- **Pilih saiz:** setiap tag dicuba dalam beberapa saiz (1 baris / 2 baris, 54→36px); yang menang ialah yang bebas
  dan paling dekat jalur atas, jadi tag besar di atas menang atas tag kecil di bawah.
- **Peralihan:** tiada wipe skrin penuh. Cahaya hangat di tepi frame sahaja (vignette amber 0.65s, tengah jernih),
  2 kali.
- **End card:** kad kait kecil di bucu kiri atas (tajuk 2 baris bila ruang sempit) + pil CTA karat di jalur bawah.

## Gaya: "Hygge kait hangat"

| Warna / font | Nilai | Guna |
|---|---|---|
| Krim | `#FBF5EA` | kad tag, caption, end card |
| Oatmeal kait | `#EADCC4` + jahitan V `#D6C09C` | cuff kait di tepi tag, jalur atas end card, jalur cover |
| Koko | `#4A2E22` | tulisan |
| Karat | `#B5502E` | kata kunci (italic), garis bawah jahitan, pil CTA |
| Cahaya lilin | `rgba(255,180,90,…)` | cahaya belakang tag hook, sinar perkataan yang disebut, vignette peralihan |
| Font | **Fraunces** 600/700/800 + italic (OFL, `comp/FRAUNCES-OFL.txt`) | semua tulisan besar |
| Font kecil | Inter Display SemiBold (OFL, `comp/INTER-LICENSE.txt`) | swatch warna end card |

- **Tag kait:** kad krim bucu bulat, cuff tekstur kait di kiri, pompom bulu di bucu kanan atas yang jatuh dengan
  lantunan lembut. Masuk perlahan (naik + kabur → jelas, 0.7s, sine), berayun sangat sikit masa di skrin.
- **Tag hook:** sama + cahaya lilin di belakangnya yang berkelip perlahan.
- **Caption:** pil oatmeal, huruf serif koko, kata kunci karat italic; perkataan yang sedang disebut bercahaya
  hangat dan garis jahitan putus-putus dilukis di bawahnya.
- **Progress:** benang kait berombak di tepi atas dengan 🧶 bergolek.
- **SFX:** `knit` (pompom bulu mendarat), `chime` (loceng rendah hangat), `crackle` (bunyi unggun api untuk
  peralihan). Muzik latar dijana (`music.wav`, felt piano + pad perlahan 72 bpm, bukan lagu berlesen), sangat
  perlahan bawah suara.
- **Cover:** kad kait "Sofa 🛋️ nampak kosong? / ambil peneman sofa ni 🤎" dengan cahaya lilin di langit kiri atas,
  2 tag kecil di bawah kusyen, jalur kait atas & bawah, warna hujung frame dihangatkan.

## Muka tak ditutup

- Kotak kepala + tudung + niqab ditanda setiap 1s daripada frame proxy bergrid (`HEADS` dalam `edit.py`,
  `HEAD_PAD` 0.55s), disemak dengan melukis kotak atas frame (`headcheck.jpg` dalam work dir). Setiap grafik
  44px bebas daripada semua kotak kepala dalam tempohnya.
- 0–3s close-up muka: kepala penuh 2/3 atas frame, jadi tag hook duduk di bawah dagu (atas tudung), bukan atas muka.
- `check.py` (24 frame, termasuk kotak tengah kuning): tiada tag, caption atau end card atas muka dia atau dalam
  zon UI; tag di jalur bawah cuma sentuh tepi bawah kotak tengah.

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 0.00–3.18 + 4.24–7.32 | ⭐ **HOOK** (ayat pembuka dia sendiri, close-up muka → kusyen masuk): "Kalau korang nampak kosong, tak ada peneman kat sofa, ambil bantal ni jadi peneman sofa kita." | tag lilin `Sofa nampak kosong? 🛋️` → `Jadi peneman sofa 🤎` |
| 6.3 | 7.66–10.68 + 11.27–12.70 | "Teman macam mana? Letaklah bagi dia duduk kat situ. Jadi kita boleh duduk atas dia." | `Duduk atas dia 😆` |
| 10.7 | 14.56–18.10 | cahaya hangat tepi + "Ni memang selesa, lembut, saiz dia 40cm × 40cm." | `40 × 40 cm 📏` |
| 14.2 | 18.10–24.20 | "Material dia pun jenis yang waffle, material jenis comel-comel berkotak-kotak kecil macam ni, cantik." (kusyen merah dibawa ke lensa, tekstur waffle penuh skrin) | `Kain waffle 🧇` |
| 20.3 | 24.20–26.28 | "Dan boleh basuh juga." | `Boleh basuh 🫧` |
| 22.4 | 27.38–28.68 | cahaya hangat tepi + "Ni buat teman kat sofa." | (caption sahaja) |
| 23.7 | 35.42–36.88 | CTA: "Tengok kat bawah sekarang." | (caption sahaja) |
| 25.2 | 31.00–33.20 (×0.75, senyap) | dua kusyen diangkat, kepala kanan | end card kait `Peneman sofa 🤎` / kusyen duduk 40 × 40 / ● Merah ● Beige + `Tekan beg kuning 🛒` |

Dibuang: jeda 1.1s selepas "sofa," (3.2–4.2), "Okey," (7.40), "kan?" (10.74), "Yang" + jedanya (14.1–14.5),
"kan?" selepas "basuh juga" (26.4), "Ha," (26.6), **"Takkan nak kena teman pula sofa korang tu"** (28.8–31.8, tak
jelas), **"Atau komennya?"** (33.9, tak jelas), jeda. "material jenis" yang diulang dikekalkan: bila dipotong,
"waffle, comel-comel" bercantum dan kedengaran macam "macam-macam". Tiada ayat harga dalam klip ni.

## Belum pasti

- **"peneman kat sofa"**: Whisper sekali dengar "punya main kat sofa" (transkripsi penuh & per bahagian dengar
  "peneman").
- **"duduk atas dia"**: transkripsi preview penuh dengar "duduk tadi", tapi semakan per bahagian dengar "atas dia".
- **"bantal"**: dia sebut "bantai".
- **"Tengok kat bawah"**: semakan per bahagian dengar "Saya nak tengok di bawah"; transkripsi penuh dengar
  "Tengok kat bawah sekarang".
- **Ayat yang dibuang** "takkan nak kena teman pula sofa korang tu" mungkin lawak tentang sofa perlukan teman;
  tak cukup jelas untuk caption.

## Render (HyperFrames)

```
cd comp && npm install && cd ..                      # hyperframes@0.8.181 (dipin dalam comp/package.json)
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell   # pilihan

python3 sfx.py sfx/                                                  # knit, chime, crackle + music.wav
python3 edit.py proxy.mp4 transcript.json sfx/ out/                  # preview: out/preview.mp4 (720x1280)
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final   # final:   final/final.mp4 (1080x1920)
python3 edit.py proxy.mp4 transcript.json sfx/ out/ --graphics-only  # ubah grafik sahaja, guna semula out/base.mp4
python3 check.py out/ check.jpg                                      # check sheet: zon UI + kotak kepala + kotak tengah

cd cover && npx --prefix ../comp hyperframes snapshot . --at 0.5 --no-end -o snap   # cover -> snap/*.png -> ../cover.jpg
```

Kata-kata caption datang daripada `OVERRIDE` dalam `edit.py` (disemak dengan transkripsi semula per bahagian +
envelope bunyi). `BREAK_BEFORE` tetapkan di mana caption pecah baris.

**Masa render:** di container ni (4 CPU, tiada GPU), HyperFrames capture 28.1s (~844 frame) ambil lebih kurang
1m 20s – 1m 50s; keseluruhan pipeline preview ~2–3 minit.
