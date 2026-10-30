# Bantal Selimut Kucing Reben (2 in 1, "Coquette reben & renda"): edit plan, preview v1 (HyperFrames)

Source: IMG_3182, iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **87.3s**
Preview v1: **35.8s** (dipotong ~52s), 720×1280, 30fps, SDR, −11.4 LUFS
Final: **35.8s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −11.4 LUFS, sudah render (HyperFrames)
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 165px, bawah 435px, atas 165px (1080×1920).

Bantal kucing krim (mata tidur, reben biru corak leopard) yang dibuka zip bawah jadi **selimut corak leopard**
lebih kurang 170cm. Produk ni mirip karakter kartun berlesen: namanya **tak ditulis** dalam label, caption,
cover atau hashtag, dan ayat dia yang sebut nama tu (61.7s) dibuang. Plastik biru pembungkus tercetak nama
produk lain, jadi shot buka plastik tak digunakan. Pipeline sama dengan `../bantal-selimut-beruang`:
potongan, suara v2 dan SFX guna ffmpeg, lapisan grafik ialah komposisi **HyperFrames** (HTML + CSS + GSAP)
dengan penempatan automatik yang elak muka.

## Gaya: "Coquette reben & renda"

| Warna | Hex | Guna |
|---|---|---|
| Gading | `#FFFBF7` → `#FFF1F3` | badan kad label, end card, huruf caption |
| Renda putih | `#FFFFFF` + lubang `#F7C3D5` | tepi renda bersisik keliling kad, bingkai cover |
| Satin pink | `#FFC9DA` → `#EE86AA` | reben satin (label besar), reben menyapu, pil perkataan aktif |
| Rose plum | `#8E3B5F` | teks label, outline caption |
| Biru serbuk | `#4F7FC0` / `#E3EEFF` | kata kunci label, pil saiz end card |

- **Font:** Inter Display (OFL, `fonts/INTER-LICENSE.txt`), huruf besar jarak lebar: kemas dan halus.
- **Label:** kad gading dengan **tepi renda bersisik** (SVG, ada lubang renda pink) dan **reben satin** di tengah
  atas. Masuk lembut (naik + fade, `power3.out`), reben pop dan bergoyang perlahan, perkataan muncul satu-satu.
  Label panjang dibalut 2 baris.
- **Label besar:** **reben satin pink** dengan hujung ekor bertakuk, teks putih outline rose, reben putih di atas,
  dan **mutiara + reben kecil** melayang keluar.
- **Caption:** huruf gading, outline rose plum. Perkataan aktif duduk atas **pil satin pink** dengan jahitan
  renda putih putus-putus. Kata kunci biru serbuk.
- **Peralihan:** **reben satin lebar menyapu** menyerong merentas skrin dengan reben besar di tengah (2 kali: sebelum
  "Tadaa!" dan sebelum CTA). Bunyi `satin`.
- **Bar kemajuan:** **rantai mutiara** yang bertukar pink, dengan reben kecil di hujung.
- **End card:** kad renda dengan reben besar, "kucing reben" (kecil, jarak lebar), "BANTAL SELIMUT", pil biru
  "2 IN 1 • LEOPARD • ±170CM" dan pil CTA beg kuning yang berdenyut.
- **SFX baru:** `harp` (glissando harpa bila label masuk), `satin` (desir reben), `pearl` (bunyi mutiara).
- **Cover:** bingkai renda bersisik dengan mutiara di bucu, reben "TENGAH TRENDING 🎀", lencana renda
  "SELIMUT ±170CM 🐆", kad renda "kucing reben / BANTAL SELIMUT" dengan reben, pil "2 IN 1 • DESIGN LEOPARD".

## Muka tak ditutup

- Kotak kepala + hud (dengan telinganya) ditanda **setiap 1 saat** daripada frame proxy bergrid (`HEADS` dalam
  `edit.py`); saat dia terlindung sepenuhnya di belakang selimut tiada kotak. Muka kucing pada bantal ditanda
  dalam `FACES` (penalti besar, elak bila boleh).
- Setiap caption, label dan end card dapat semua kotak kepala dalam tempoh paparannya (±0.5s). Komposisi cari
  tempat terdekat dengan kedudukan pilihan yang **44px jauh** dari semua kotak tu (termasuk reben di atas kad),
  tak bertindih caption. Label panjang cuba 1 baris dulu, kemudian 2 baris.
- Kepala dia tinggi dalam frame, jadi label duduk di tengah skrin (y≈1060) dan caption di bawah (y≈1405).
- **Check sheet (51 frame):** tiada grafik kena muka atau hud dia, atau zon UI TikTok. Yang tak dapat dielak:
  label di tengah bertindih badan bantal/selimut. Reben menyapu tutup skrin ~0.7s (dibenarkan).

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 43.1 | ⭐ **HOOK**: "Design leopard ni kenapa ya? Sekarang ni tengah trending." (selimut dikibar, bantal atas bahu) | `DESIGN LEOPARD` 🐆 → reben `TENGAH TRENDING!` 🎀 + mutiara |
| 2.6 | 75.9 | "Wih, estetik je ni." (bantal + selimut) | `ESTETIK JE NI` 💗 |
| 4.1 | audio 7.6 + 8.9, visual 8.3 | "Wah, lembut, lembutnya!" (J-cut; plastik tak ditunjuk) | `LEMBUTNYA!` ☁️ |
| 6.3 | 17.6 | "Ni senang bawa travel. Senang ni standby dalam kereta satu." | `SENANG BAWA TRAVEL` 🧳 → `STANDBY DALAM KERETA` 🚗 |
| 9.5 | 20.8 | "Dia ada selimut tau. Bantal dia pun lembut, fluffy." | `ADA SELIMUT TAU` 🤫 → `LEMBUT & FLUFFY` ☁️ |
| 12.3 | 23.8 | "Lepas tu kita buka zip bawah dia." | `BUKA ZIP BAWAH` 🔓 |
| 13.6 | 25.1–28.4 | buka zip, tarik selimut (×2.5) | tag `>> x2.5` |
| 14.9 | 28.6 | (reben menyapu) "Tadaa!" | reben `TADAA!` ✨ + mutiara |
| 15.8 | 35.4 | "Ni riben dia. Riben dia pun leopard." (tunjuk reben) | `RIBEN PUN LEOPARD` 🎀 |
| 17.9 | 52.5 | "(Macam) lebih kurang 170cm macam tu lah." (selimut panjang penuh) | reben `SELIMUT ±170CM` 📏 |
| 20.2 | 56.9 | "Dah habis guna, masukkan balik selimut dekat dalam bantal ni." | `DAH GUNA? SIMPAN` 🫶 → `MASUK DALAM BANTAL` 👜 |
| 23.6 | 64.6 | "Tu mata dia tertutup, macam tu bulu mata panjang." | `BULU MATA PANJANG` 😴 |
| 25.8 | 68.8 | "Bantal dia pun gebu, selimut pun gebu." | `BANTAL + SELIMUT GEBU` 💕 |
| 28.7 | 77.7 | (reben menyapu) CTA: "Korang tengok dekat beg kuning. Yang mana suka geng-geng estetik tu, ambil ni." | `TEKAN BEG KUNING` 🛒 → reben `GENG ESTETIK, AMBIL!` 💗 |
| 32.0 | 83.6 | "Ready stock, cepat sampai." | `READY STOCK` 📦 |
| 34.0 | 85.5 (visual) | - | End card renda: `kucing reben` / `BANTAL SELIMUT` / `2 IN 1 • LEOPARD • ±170CM` / `TEKAN BEG KUNING` |

**Dibuang:** buka plastik biru 0–7.5s (plastik tercetak nama produk lain; "Bismillah, mesti kita unboxing lagi"),
"Ini tak tepuk-tepuk dulu bagi dia... balik" (tak jelas), "Wey lembutnya" (ulang), "Bismillah" kedua (dimute
bawah ×2.5), "Wey lembut ya / Lembut, comel, ini bantal dia" (ulang), "Ah comel, Allah minatnya lembut-lembut ni
korang / Hampo ya Allah, comel" (ulang/tak jelas), "Saya suka, eh selimut dia panjang tau" (tak jelas),
"Itu, haa selimut dia", "Size? Apa tu?", "Ni bantal dia tadi", "Comel yaaa", **ayat yang sebut nama karakter
(61.7s)**, "Tu ada riben" (ulang), "Gebu tau", "Lawanya leopard ni / Eh tak sangka comel" (ulang), **"Haa
tengok harga dekat beg kuning" (sebut harga)**, "Okay", "Okay, tengok beg ku ni" (dimute bawah end card), jeda.

## Belum pasti

- **"Riben dia pun leopard"** (36.8s): pass penuh dengar "lembut", chunk dengar "lepet", semakan preview dua kali
  dengar "leopard". Reben pada bantal memang corak leopard sama macam selimut, jadi caption dan label ikut
  "leopard".
- **"Dia ada selimut tau"** (20.9s): pass penuh dengar "Ini ada", chunk "Ni ada", semakan preview dua kali "Dia ada".
  Caption ikut "Dia".
- **"standby dalam kereta"**: pass penuh dengar "sambil dalam kereta", chunk dan preview dengar "stand by".
- **"170cm"** (53.1s): ayat dia sendiri ("lebih kurang 170cm macam tu lah"); label tulis `±170CM`. "Macam" di
  depan tak jelas (preview dengar "Kita"), jadi tak dimasukkan dalam caption.
- **"Design leopard"**: pass penuh dengar "Desain lembut", chunk dan preview dengar "Design leopard".

## Render (HyperFrames)

Sama macam `../bantal-selimut-beruang`:

```
cd comp && npm install && cd ..                      # hyperframes@0.8.181 (dipin dalam comp/package.json)
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell   # pilihan

python3 edit.py proxy.mp4 transcript.json sfx/ out/                  # preview: out/preview.mp4 (720x1280)
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final   # final:   final/final.mp4 (1080x1920)
python3 edit.py proxy.mp4 transcript.json sfx/ out/ --graphics-only  # ubah grafik sahaja, guna semula out/base.mp4
python3 check.py out/ check.jpg                                      # check sheet: zon UI + kotak kepala + muka bantal

cd cover && npx --prefix ../comp hyperframes snapshot . --at 0.5 --no-end -o snap   # cover -> snap/*.png -> ../cover.jpg
```

`sfx.py` menjana semua bunyi (`python3 sfx.py <dir>`), termasuk `harp`, `satin` dan `pearl` baru.
`cover/frame.jpg` ialah frame 79.3s daripada master1080.

**Masa render:** di container ni (4 CPU dikongsi, tiada GPU), render HyperFrames untuk 35.8s (1,073 frame)
ambil lebih kurang **4 min**; keseluruhan pipeline preview lebih kurang 6 minit.
