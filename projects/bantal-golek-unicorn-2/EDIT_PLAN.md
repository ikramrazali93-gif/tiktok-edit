# Bantal Golek Unicorn, video 2 (Minimal editorial bersih): edit plan, preview v1 (HyperFrames)

Source: IMG_3180, iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **34.8s**
Preview v1: **22.7s** (dipotong ~12s), 720×1280, 30fps, SDR. Suara −11.5 LUFS; keseluruhan −12.0 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 165px, bawah 435px, atas 165px (1080×1920).

Produk sama dengan `../bantal-golek-unicorn` (IMG_3179): bantal golek pink corak unicorn/pelangi. Ini video
berasingan yang pendek, dengan hook dan sudut lain: **teman dakap malam-malam, untuk seisi rumah**.
Satu shot 34.8s, dia berdiri peluk bantal golek dan bercakap sepanjang masa. 0–8.6s dan 17.4–18.9s ialah cakap
pasal harga (dipotong). Muzik latar lembut yang sama dengan video unicorn pertama (`music.wav` dijana dalam
`sfx.py`, bukan lagu berlesen) direndahkan bawah suara dia.

Pipeline sama dengan `../bantal-golek-unicorn`: potongan, suara v2, SFX dan muzik guna ffmpeg; lapisan grafik
ialah komposisi **HyperFrames** (HTML + CSS + GSAP).

## Gaya: "Minimal editorial bersih"

| Warna / font | Nilai | Guna |
|---|---|---|
| Krim kertas | `#FFFDF9` / `#FBF7F1` | kad label, jalur caption, end card, wipe |
| Dakwat | `#24212A` | huruf, pil CTA end card |
| Blush | `#E5578C` | bar kiri kad, garis halus, kicker, kata kunci, garis bawah caption, bar kemajuan |
| Kelabu lembut | `#8C8590` / `#6E6772` | nombor kicker, baris kecil end card |
| Font | **Inter Display** 500/600/700 (OFL, `comp/INTER-LICENSE.txt`) | semua teks (bukan Fredoka macam video lain) |

- **Label:** kad kertas krim dengan bayang lembut, bar blush di kiri, kicker kecil berjarak huruf
  (`01 —— TEMAN TIDUR`, nombor naik ikut label) dan tajuk Inter Display 70px (kata kunci blush). Masuk dengan
  reveal dari kiri (clip-path, power3), kicker + garis halus melebar, perkataan naik satu-satu. Keluar: pudar ke
  atas sikit. Tiada lantunan, tiada bintang: tenang dan bersih. Label sentiasa rapat ke margin kiri (gaya majalah).
- **Caption:** jalur krim lut sikit, huruf dakwat Inter Display 58px (ayat biasa, bukan huruf besar semua).
  Perkataan aktif jadi blush dengan **garis bawah nipis yang meluncur** ke perkataan tu.
- **Peralihan:** "page-turn" panel krim dengan tepi blush menyapu skrin (sebelum "corak" dan sebelum end card).
- **Bar kemajuan:** garis halus 4px di atas.
- **End card:** kad krim `BANTAL GOLEK · NO. 02` / `Teman dakap malam-malam.` / garis / `Panjang · Macam-macam
  corak` / pil dakwat `Tekan beg kuning 🛒` (berdenyut perlahan).
- **SFX:** `click` lembut untuk label, `ding` untuk hook dan CTA, `swish` untuk wipe, `sparkle` di end card.
- **Cover:** foto penuh, garis bingkai krim nipis, kicker `NO. 02 — BANTAL GOLEK` di kawasan pokok kiri atas,
  kad krim editorial di atas kot dia (kanan bawah).

## Muka tak ditutup

- Kotak kepala + hud ditanda setiap 1s daripada frame proxy bergrid (`HEADS` dalam `edit.py`, `HEAD_PAD` 0.8s).
- Komposisi (`comp/index.html`, `place()`) cari tempat paling dekat dengan kedudukan pilihan (label: rapat kiri,
  y≈1040; caption: tengah, y≈1395) yang 44px bebas daripada semua kotak kepala dalam tempoh grafik tu, dan tak
  bertindih caption. Label panjang dibalut 2 baris dulu, baru dikecilkan.
- `check.py` (kotak cyan + zon UI merah atas 25 frame preview): tiada label, caption atau end card atas muka dia.
  Kepala dia sentiasa di bahagian atas tengah-kanan, jadi label jatuh di kiri tengah atas bantal/lengan dia.
  Wipe krim lalu seluruh skrin ~0.7s (dibenarkan).

## Susunan

| TL | Masa asal | Ayat / visual | Grafik |
|---|---|---|---|
| 0.0 | 13.69–17.25 | ⭐ **HOOK**: "Siapa yang belum ada bantal peluk nak dakap malam-malam? Ambil bantal peluk ni." | `01 TEMAN TIDUR · Belum ada bantal peluk? 🌙` → `02 BANTAL GOLEK · Ambil yang ni. 🤍` |
| 3.3 | 3.62–4.60 | "Besar macam ni." | caption sahaja |
| 4.2 | 10.46–13.16 | "Tu panjang, ni kita peluk sampai lutut lah." | `03 PANJANG · Peluk sampai lutut 📏` |
| 6.9 | 23.76–25.58 | "Sangat-sangat selesa." | caption sahaja |
| 8.8 | 26.32–30.74 | wipe + "Ada macam-macam corak-corak dia. Cantik-cantik, warna. Mak love." | `04 PILIHAN · Macam-macam corak 🦄` → `05 WARNA · Warna cantik-cantik 🌈` |
| 13.2 | 0.20–2.60 (senyap) | dia peluk bantal & ketawa, muzik | `06 WAKTU TIDUR · Dakap malam-malam 😴` |
| 15.6 | 19.18–22.44 | "Boleh beli dua, tiga biji. Anak remaja perempuan boleh guna." | `07 SEISI RUMAH · Ambil 2–3 biji 🏠` → `08 SESUAI · Untuk anak remaja 👧` |
| 18.8 | 32.50–33.32 | CTA: "Tengok dekat bawah sekarang." | `09 SEKARANG · Tengok beg kuning 👇` |
| 19.7 | 5.60–8.60 (senyap) | dia pegang bantal tegak & senyum | wipe + end card |

Dibuang:
- **Harga (peraturan tiada harga):** "Ya Allah ampun. Tengok harga dia. Tengok harga dia sekarang." (0–3.3s),
  "Harga tak masuk akal, saya tak boleh brain lah harga yang murah macam ni." (5–8.6s), "Harga je, mak. Harga
  mesra poket, okey?" (17.4–18.9s).
- "Ni bantal peluk dia … tau, panjang." (8.8–10.4s, satu perkataan tak jelas; "Tu panjang" lepas tu disimpan).
- "Haa" sebelum "ada macam-macam", "Okey," sebelum "sangat-sangat selesa", "dah. Haa ni dia." selepas "guna",
  "Terima kasih, tengok-tengok dekat beg." (cubaan CTA pertama), "okey?" di hujung, jeda.

## Belum pasti

- **"nak dakap malam-malam"**: Whisper dengar "datang" (2×) dan "dakak" (1×). "Dakap" paling masuk akal
  (peluk), jadi caption & label tulis "dakap".
- **"Besar macam ni"**: suara perlahan; satu pass dengar "Sok macam ni" (mungkin loghat "besaq").
- **"Tu panjang"**: pass lain dengar "Itu", "Aduh" atau "toh".
- **"Anak remaja perempuan boleh guna"**: semakan preview dengar "anak remaja atau pembeli guna". Caption ikut
  pass pertama (perempuan).
- **"Mak love"**: dia sebut macam "Mak love" (suka sangat); semakan dengar "mak leluh".
- **CTA "dekat bawah"**: dia maksudkan beg kuning di bawah skrin, jadi label tulis `Tengok beg kuning 👇`.

## Render (HyperFrames)

```
cd comp && npm install && cd ..                      # hyperframes@0.8.181 (dipin dalam comp/package.json)
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell   # pilihan

python3 sfx.py sfx/                                                  # semua SFX + music.wav
python3 edit.py proxy.mp4 transcript.json sfx/ out/                  # preview: out/preview.mp4 (720x1280)
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final   # final:   final/final.mp4 (1080x1920)
python3 edit.py proxy.mp4 transcript.json sfx/ out/ --graphics-only  # ubah grafik sahaja, guna semula out/base.mp4
python3 check.py out/ check.jpg                                      # check sheet: zon UI + kotak kepala

cd cover && npx --prefix ../comp hyperframes snapshot . --at 0.5 --no-end -o snap   # cover -> snap/*.png -> ../cover.jpg
```

Kata-kata caption datang daripada `OVERRIDE` dalam `edit.py` (disemak dengan transkripsi semula per bahagian +
envelope bunyi). `BREAK_BEFORE` tetapkan di mana caption pecah baris.

**Masa render:** di container ni (4 CPU, tiada GPU), render HyperFrames untuk 22.7s (680 frame) ambil lebih
kurang 1m 30s – 3m 20s bergantung pada render lain yang berjalan serentak; keseluruhan pipeline preview 2–4 minit.
