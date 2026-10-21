# Bantal Peluk Durian (4 saiz): edit plan, preview v1 (ujian HyperFrames)

Source: iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **50.7s**
Preview v1: **41.7s** (dipotong ~9s), 720×1280, 30fps, SDR, −11.3 LUFS
Final: **41.8s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −11.3 LUFS, sudah render (HyperFrames capture 3m 45s, keseluruhan ~7.5 min)
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 165px, bawah 435px, atas 165px (1080×1920).

Video pertama yang lapisan grafiknya (caption, label, emoji, peralihan, end card) dibina dengan **HyperFrames**
(HTML + CSS + GSAP, render dalam Chrome) dan bukan ASS + Pillow macam projek lain. Potongan video, suara v2
dan SFX masih guna pipeline lama (ffmpeg).

## Gaya: "kulit durian"

| Warna | Hex | Guna |
|---|---|---|
| Hijau kulit durian | `#6E9A2A` | rim berduri label, peralihan, bingkai cover |
| Hijau gelap | `#2F4A12` | outline caption, bayang 3D |
| Isi durian (krim) | `#FFF4C2` | isi label |
| Kuning durian | `#FFD93B` | pil perkataan aktif caption, label saiz, progress bar |
| Pink blush | `#E3367A` | nombor saiz (95/75/52/30) |

Benda baru yang HyperFrames buat lebih senang berbanding ASS:
- **Label "durian":** pil krim dengan rim hijau berduri (SVG dilukis ikut saiz teks). Ia masuk dengan easing elastic, perkataan naik satu-satu, dan emoji bergoyang.
- **Caption pil bergerak:** satu pil kuning meluncur dari perkataan ke perkataan, ukurannya ikut lebar sebenar perkataan.
- **Emoji berwarna terus dalam teks**, tanpa lapisan sticker berasingan.
- **Auto-fit:** teks mengecil sendiri kalau terlalu panjang. Label yang di tepi kepala dibalut jadi 2–3 baris.
- **Peralihan "kupas durian":** jalur kulit hijau berduri dengan isi kuning menyapu skrin.
- **Lain-lain:** bintang kecil memancar pada label besar, progress bar dengan tombol hijau, end card dengan tajuk di atas dan pil saiz serta CTA di bawah.

## Elak tutup subjek (peraturan baru)

Bantal hampir penuhi frame, jadi ruang kosong sedikit. Setiap blok ditanda dengan kotak kepala dan titik muka
bantal (`SUBJECT` dalam `edit.py`), dan disemak dengan `check.py`, yang melukis kotak tu bersama zon UI TikTok
atas frame preview.
- **Label** di jalur atas (pokok di atas kepala, y 0.10–0.18). Ada yang tersentuh bahagian atas hud, tapi bukan muka.
- **Caption** di jalur bawah (jubah dan hujung bantal, y 0.70–0.77), betul-betul di atas kawasan caption TikTok.
- **Pengecualian:**
  - Close-up 52/30cm: label di **kiri atas**, sebab muka dia di tengah atas.
  - Close-up "Ya Rabbi, comelnya": caption naik ke **y 0.61** (kuning kosong), sebab muka bantal besar ada di bawah.
  - "Yang mana belum ada?": label di kiri atas, sebab kepala dia kembali di tengah.
- **Tak dapat dielak sepenuhnya:** label 75CM menyentuh atas hud dia, dan beberapa caption bawah menyentuh hujung muka bantal paling bawah. Muka dia sendiri tak ditutup.

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 0.55 | ⭐ **HOOK**: "Korang malam tadi tidur peluk apa?" | `TIDUR PELUK APA?` 🤔 + bintang |
| 2.8 | 4.62 | "Ada suami? Peluk suami." | `ADA SUAMI?` 💑 → `PELUK SUAMI!` 🤭 |
| 4.4 | 6.40 | "Kalau tak ada suami, yang single-single tu peluk apa?" | `YANG SINGLE?` 🙋‍♀️ |
| 6.7 | 9.02 / 11.90 | "Memang ni, kita nak share ni, bantal peluk, durian yang gebu-gebas macam ni." | peralihan kupas durian + `BANTAL PELUK DURIAN` 💛 |
| 10.8 | 13.88 | "Ada macam-macam saiz. Ni saiz paling besar," | `MACAM-MACAM SAIZ` 📏 → `PALING BESAR!` 💪 |
| 13.3 | 17.46 | "95cm, gebu-gebas, tebal macam tu, sangat selesa." | `95CM` 😱 → `TEBAL & SELESA` ☁️ |
| 17.6 | 22.04 | "Nak yang ni pun besar juga ni, ni saiz 75cm." | `YANG NI PUN BESAR` 🤗 → `75CM` 💛 |
| 20.4 | 27.78 | "Ada lagi, saiz yang kecil pun ada." | peralihan + `SAIZ KECIL PUN ADA` 🐣 |
| 23.0 | 30.80–32.15 | (bawa bantal kecil, ×1.5) | tag `>> x1.5` |
| 23.9 | 33.20 | "Saiz yang lebih kecil, saiz 52cm dengan saiz 30cm." | `LEBIH KECIL` 🤏 → `52CM` ✨ → `30CM` 🥹 (kiri atas) |
| 28.4 | 38.02 | "Ya Rabbi, comelnya korang. Yang mana tak ada lagi," | `YA RABBI, COMELNYA!` 🥰 → `YANG MANA BELUM ADA?` 👀 |
| 32.1 | 42.04 | "Boleh tengok ni. Ambik nak saiz mana satu, pilihlah. Ada empat-empat saiz ni. Lembut, gebu, fluffy. Buat teman tidur, okey?" | `TENGOK NI!` 👇 → `PILIH SAIZ MANA?` 🤔 → `ADA 4 SAIZ!` 📏 → `LEMBUT • GEBU • FLUFFY` ☁️ → `TEMAN TIDUR` 😴 (punch-in ikut rentak) |
| 40.0 | 49.92 (×0.45) | - | End card: `BANTAL PELUK DURIAN` / `📏 95 • 75 • 52 • 30 CM` / `🛒 TEKAN BEG KUNING` |

**Dibuang:**
- "Ha," dan jeda selepas soalan hook
- "Okay" sebelum "kalau"
- "doian" (tersasul sebelum "durian")
- "dah besar sahaja dah"
- "Ni pun bagi saya dah cukup besar dah" (ulang)
- "Nah ni" dan bunyi bising sebelum "saiz yang lebih kecil"
- jeda selepas "lagi"

Tiada sebutan harga dalam video ni.

## Belum pasti

- **"52cm":** Whisper dengar "52cm" dua kali, tapi saiz ni pelik berbanding 95/75/30. Mungkin sebenarnya 50cm atau 55cm. Label dan caption tulis 52CM.
- **"Ambik nak saiz mana satu":** Whisper dengar "Amik nak saiz **sama** satu". Caption tulis "mana" ikut maksud ayat.
- **"Ya Rabbi":** Whisper tulis "Ya Robi".
- **"Yang mana tak ada lagi":** "Yang" perlahan. Label tulis `YANG MANA BELUM ADA?`.

## Render (HyperFrames)

Keperluan: ffmpeg, Node 18+, dan Chrome/Chromium (HyperFrames boleh muat turun sendiri, atau set
`HYPERFRAMES_BROWSER_PATH` ke Chrome sedia ada).

```
cd comp && npm install && cd ..                      # pasang hyperframes@0.8.181 (dipin dalam comp/package.json)
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell   # pilihan

python3 edit.py proxy.mp4 transcript.json sfx/ out/                  # preview: out/preview.mp4 (720x1280)
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final   # final:   final/final.mp4 (1080x1920)
python3 edit.py proxy.mp4 transcript.json sfx/ out/ --graphics-only  # ubah grafik sahaja, guna semula out/base.mp4
python3 check.py out/ check.jpg                                      # check sheet: zon UI + kotak subjek

cd cover && npx --prefix ../comp hyperframes snapshot . --at 0.5 --no-end -o snap   # cover -> snap/*.png -> ../cover.jpg
```

**Apa `edit.py` buat:**
1. Potong dan zoom video, kemudian campur suara v2 dan SFX, jadi `base.mp4`.
2. Tulis `comp/data.js` (caption, label, peralihan, end card, susun atur per blok) dan salin `base.mp4` ke dalam `comp/`.
3. `npx hyperframes render` untuk `comp/index.html`. Komposisi sentiasa 1080×1920, dengan `base.mp4` sebagai lapisan video senyap.
4. Gabung video HyperFrames dengan audio `base.mp4`. Untuk preview, video dikecilkan ke 720×1280.

**Masa render:** di container ni (4 CPU, tiada GPU, beginframe capture, 3 worker), render HyperFrames untuk
41.7s (1,253 frame) ambil lebih kurang **2 min 15 s**. Keseluruhan pipeline preview, termasuk potong video dan
audio, ambil lebih kurang 4 minit.
