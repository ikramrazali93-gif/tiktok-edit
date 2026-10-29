# Bantal Selimut Beruang Strawberry (2 in 1, "Kedai kek strawberry"): edit plan, preview v1 (HyperFrames)

Source: IMG_3181, iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **146.8s**
Preview v1: **40.7s** (dipotong ~106s), 720×1280, 30fps, SDR, −11.4 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 165px, bawah 435px, atas 165px (1080×1920).

Bantal beruang strawberry warna pink yang dibuka zip belakang jadi selimut. Produk ni mirip karakter kartun
berlesen dan namanya tercetak pada bantal: nama tu **tak ditulis** dalam label, caption, cover atau hashtag.
Pipeline sama dengan `../bantal-durian-2`: potongan, suara v2 dan SFX guna ffmpeg, lapisan grafik ialah
komposisi **HyperFrames** (HTML + CSS + GSAP) dengan penempatan automatik yang elak muka.

## Gaya: "Kedai kek strawberry"

| Warna | Hex | Guna |
|---|---|---|
| Krim span | `#FFF8EF` → `#FFEBDD` | badan kad label, end card, caption |
| Aising pink | `#FF8FB1` / `#FF6F98` | aising menitis atas kad, peralihan, manik paip |
| Strawberry | `#F0436E` | kata kunci label, blob perkataan aktif, pil CTA |
| Coklat | `#5A2E2A` | teks label, outline semua bentuk |
| Sprinkle | pink, kuning, mint, ungu, oren | sprinkle atas aising dan letupan |

- **Label:** kad krim dengan **aising pink menitis** di atasnya (SVG dilukis ikut lebar kad, titisan panjang
  pendek bersilih), sprinkle atas aising. Masuk dengan squash-and-stretch (leper → melantun), aising "meleleh"
  turun, perkataan naik satu-satu, emoji bergoyang. Label panjang dibalut 2 baris.
- **Caption:** huruf krim, outline coklat. Perkataan aktif duduk atas **blob aising strawberry** yang pop
  (dengan kilat putih). Kata kunci pink muda.
- **Peralihan:** aising pink **dituang dari atas** menutup skrin, penuh sprinkle, kemudian jatuh keluar (2 kali:
  sebelum "ada selimut dalam" dan sebelum "lawa selimut").
- **Letupan sprinkle + hirisan strawberry** keluar dari label besar dan end card.
- **Bar kemajuan:** manik paip krim yang bertukar pink, dengan 🍓 di hujung.
- **End card:** kad menu kedai kek dengan bingkai **manik krim/pink dipaip** keliling (manik pop satu-satu),
  tajuk, "2 IN 1 • GEBU • PINK" dan pil CTA beg kuning yang berdenyut.
- **SFX baru:** `squish` (aising mendarat), `sprinkles` (sprinkle jatuh).
- **Cover:** bingkai manik paip, tajuk "BANTAL + SELIMUT" dengan aising menitis, pil "2 IN 1 • PINK LOVER WAJIB
  ADA", sticker "GEBU & LEMBUT" atas jalur nama pada bantal, lencana bintang "2 IN 1 SELIMUT".

## Muka tak ditutup

- Kotak kepala + hud ditanda **setiap 1 saat** daripada frame proxy bergrid (`HEADS` dalam `edit.py`); saat
  yang dia terlindung sepenuhnya di belakang selimut tiada kotak.
- Setiap caption, label dan end card dapat semua kotak kepala dalam tempoh paparannya (±0.5s). Komposisi cari
  tempat terdekat dengan kedudukan pilihan yang **44px jauh** dari semua kotak tu, tak bertindih caption, dan
  elak muka beruang pada bantal (`FACES`, penalti besar). Label panjang cuba 1 baris dulu, kemudian 2 baris.
- Kepala dia selalu tinggi dalam frame (hud besar), jadi label duduk di tengah skrin (y≈1020) dan caption di
  bawah (y≈1405).
- **Check sheet (58 frame):** tiada grafik kena muka atau hud dia, atau zon UI TikTok. Yang tak dapat dielak:
  beberapa label di tengah bertindih badan/jalur tulisan bantal (kadang-kadang menutup nama yang tercetak, yang
  memang elok). Tuangan aising tutup skrin ~0.6s (dibenarkan).

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 62.2 + 130.6 | ⭐ **HOOK**: "Siapa minat warna pink-pink gini?" + "Two in one. Dua dalam satu." | `SUKA PINK?` 🍓 → `2 IN 1!` 🎀 → `BANTAL + SELIMUT` 🧁 + sprinkle |
| 3.9 | 41.6 | "Jom kita unboxing." | `JOM UNBOXING!` 🎁 |
| 5.2 | 43.0–50.4 | buka plastik (×4) | tag `>> x4` |
| 7.0 | 50.4 | "Alahai, comelnya." | `COMELNYA!` 🥹 |
| 8.5 | 51.9–58.9 | keluarkan bantal (×4) | tag `>> x4` |
| 10.3 | 58.9 | "Tadaa!" | `TADAA!` ✨ + sprinkle |
| 11.5 | 71.6 | (tuang aising) "Yang ni kan dia ada selimut tau dekat dalam." | `ADA SELIMUT DALAM` 🤫 |
| 13.3 | 83.1 | "Boleh bawa travel, belakang dia ada selimut." | `BOLEH BAWA TRAVEL` 🧳 → `SELIMUT DI BELAKANG` 👀 |
| 17.3 | 88.6 + 91.2 | "Di belakang, ambil selimut dalam dia." | `BUKA ZIP` 🔓 → `TARIK SELIMUT` 🫴 |
| 19.5 | 92.3–96.7 | tarik selimut keluar (×2.5) | tag `>> x2.5` |
| 21.2 | 96.9 + 99.7 | "Bantal dia pun besar lah, gebu lah, lembut lah." | `BANTAL PUN BESAR` 🤗 → `GEBU & LEMBUT` ☁️ |
| 24.5 | 101.5 | "Dan ni selimut dia." | `INI SELIMUT DIA` 🛏️ |
| 25.9 | 108.9 | (tuang aising) "Woi, lawa selimut!" | `LAWA SELIMUT!` 😍 + sprinkle |
| 27.5 | audio 118.5, visual 113.1 | "Nampak tak selimutnya bercorak." (J-cut atas selimut terbentang) | `BERCORAK COMEL` 🍓 |
| 29.6 | 127.6 | "Sekali dengan selimut, dengan bantal dia sekali." | `SELIMUT + BANTAL` 🎀 |
| 32.2 | 136.8 | "Pink lover, sila dapatkan yang ini." | `PINK LOVER, AMBIL!` 💗 + sprinkle |
| 34.5 | 133.0 | CTA: "Korang boleh grab, tengok dekat beg kuning." | `TEKAN BEG KUNING` 🛒 |
| 36.3 | 140.7 | "Cepat sampai, ready stock." | `READY STOCK` 📦 |
| 38.2 | 142.5 (visual) | - | End card kad menu: `BANTAL SELIMUT 🍓` / `2 IN 1 • GEBU • PINK` / `TEKAN BEG KUNING` |

**Dibuang:** buka beg merah 0–41s (terlalu panjang), "Bismillah", "Kena gunting ke apa / kena tarik", "Okay"
(sebelum "jom kita unboxing" dan "two in one"), "Set nak / takut tangan basah", "Ha, belakang dia", "Okay ni
bantal dia, tepuk-tepuk bagi gebu balik", "Okay, ini bantal dia" (ulang), "sebab kemudian tu" (tak jelas),
"Ha, set / pegang set ni", "Ha, ni terbalik", "Lawanya ... yang mana duk tanya / sebelum ni ada dah beg-beg"
(tak jelas), "Comelnya, warna pink pink" (ulang), "Okay, comel", "Okay, terima kasih, selamat tinggal" (dimute
bawah end card), jeda. **Tiada sebutan harga** dalam video ni.

## Belum pasti

- **"Di belakang"** (88.6s): seluruh transkripsi dengar "Buka belakang", semakan chunk dan preview dengar
  "Di belakang". Caption ikut "Di belakang"; label `BUKA ZIP` ikut visual (dia buka zip).
- **"Tadaa!"** (58.9s): perlahan; satu pass dengar "Ta-da", preview check tak tangkap.
- **"Woi, lawa selimut"**: pass penuh dengar "Wah, ... selimut", chunk dengar "Woi, lawa selimut".
- **"Sekali dengan selimut"**: semakan preview dengar "Lepas dengan selimut".
- **"Jom kita unboxing"**: semakan preview dengar "Jangan kita..." (sebutan laju), audio tak terpotong.
- **"Cepat sampai, ready stock"**: ayat dia sendiri; label cuma `READY STOCK`.

## Render (HyperFrames)

Sama macam `../bantal-durian-2`:

```
cd comp && npm install && cd ..                      # hyperframes@0.8.181 (dipin dalam comp/package.json)
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell   # pilihan

python3 edit.py proxy.mp4 transcript.json sfx/ out/                  # preview: out/preview.mp4 (720x1280)
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final   # final:   final/final.mp4 (1080x1920)
python3 edit.py proxy.mp4 transcript.json sfx/ out/ --graphics-only  # ubah grafik sahaja, guna semula out/base.mp4
python3 check.py out/ check.jpg                                      # check sheet: zon UI + kotak kepala + muka bantal

cd cover && npx --prefix ../comp hyperframes snapshot . --at 0.5 --no-end -o snap   # cover -> snap/*.png -> ../cover.jpg
```

`sfx.py` menjana semua bunyi (`python3 sfx.py <dir>`), termasuk `squish` dan `sprinkles` baru.

**Masa render:** di container ni (4 CPU dikongsi, tiada GPU), render HyperFrames untuk 40.7s (1,221 frame)
ambil lebih kurang **2 min**; keseluruhan pipeline preview lebih kurang 3 minit.
