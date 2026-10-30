# Bantal Selimut Karakter Biru (2 in 1, "Galaksi angkasa"): edit plan, preview v1 (HyperFrames)

Source: IMG_3183, iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **94.3s**
Preview v1: **46.9s** (dipotong ~47s), 720×1280, 30fps, SDR, −11.1 LUFS
Final: **46.9s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −11.1 LUFS, sudah render (HyperFrames)
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 165px, bawah 435px, atas 165px (1080×1920).

Bantal karakter alien biru yang dibuka zip belakang jadi selimut biru muda bercorak. Dia pakai hud yang sama
warna. Produk dan hud ni mirip karakter kartun berlesen dan namanya tercetak pada bantal/selimut: nama tu **tak
ditulis** dalam label, caption, cover atau hashtag. Pipeline sama dengan `../bantal-selimut-beruang` dan
`../bantal-durian-2`: potongan, suara v2 dan SFX guna ffmpeg, lapisan grafik ialah komposisi **HyperFrames**
(HTML + CSS + GSAP) dengan penempatan automatik yang elak muka.

## Gaya: "Galaksi angkasa"

| Warna | Hex | Guna |
|---|---|---|
| Navy angkasa | `#0E1234` → `#2C165C` | kaca panel label, end card, peralihan warp |
| Cyan neon | `#5FF4FF` | rim + glow panel, kata kunci, kapsul perkataan aktif, bar orbit |
| Ungu nebula | `#A778FF` / `#C9B6FF` | rim kedua, planet, kata kunci caption |
| Kuning bintang | `#FFE45C` | bintang, bulan orbit, pil CTA |

- **Label:** panel kaca gelap bergradien navy-ungu dengan **rim neon cyan + ungu** dan cahaya, bintik bintang
  kecil di dalam, emoji dalam "planet" bulat ungu. Masuk terapung dari bawah dengan blur → tajam (easing lembut
  macam graviti sifar), perkataan naik satu-satu, **komet** menyapu melintasi panel, panel terapung naik turun
  perlahan. Label panjang dibalut 2 baris.
- **Lencana planet:** bola ungu dengan **cincin neon** (separuh belakang di belakang bola) untuk `2 IN 1`.
- **Caption:** huruf putih, outline navy, kata kunci ungu muda. Perkataan aktif jadi cyan dalam **kapsul orbit
  neon** yang bercahaya, dan terapung sedikit.
- **Letupan bintang:** bintang 4 bucu (putih, cyan, ungu, kuning) keluar dari label besar dan end card.
- **Peralihan "warp":** garis bintang memancar dari tengah (hyperspace) atas latar navy, 2 kali: sebelum
  "cantik kan" (selimut keluar) dan sebelum "besar juga ni" (selimut terbentang).
- **Bar kemajuan:** garis orbit nipis bertukar cyan, dengan 🚀 di hujung.
- **End card:** panel holo dengan **orbit putus-putus** keliling dan bulan kuning, tajuk, "2 IN 1 • BIRU LEMBUT
  • GEBU" dan pil CTA kuning yang berdenyut.
- **SFX baru:** `warp` (bunyi "pew" sci-fi), `twinkle` (loceng bintang), `hum` (dengung kapal angkasa).
- **Cover:** bingkai angkasa (bintang + garis orbit neon), panel holo tajuk, pil kuning, planet "2 IN 1",
  sticker kaca "GEBU & LEMBUT".

## Muka tak ditutup

- Kotak kepala + hud (hud besar: telinga, jalur gigi) ditanda **setiap 1 saat** daripada frame proxy bergrid
  (`HEADS` dalam `edit.py`); saat yang bantal atau selimut menutup dia sepenuhnya tiada kotak.
- Setiap caption, label dan end card dapat semua kotak kepala dalam tempoh paparannya (±0.5s). Komposisi cari
  tempat terdekat dengan kedudukan pilihan yang **44px jauh** dari semua kotak tu, tak bertindih caption, dan
  elak muka bantal (`FACES`, penalti besar). Label panjang cuba 1 baris dulu, kemudian 2 baris.
- Hud dia selalu tinggi dalam frame, jadi label duduk di tengah skrin (y≈1060) dan caption di bawah (y≈1400).
- **Check sheet (58 frame):** tiada grafik kena muka atau hud dia, atau zon UI TikTok. Yang tak dapat dielak:
  beberapa label tengah bertindih badan/mata bantal (bantal besar penuh frame). Peralihan warp tutup skrin ~0.6s
  (dibenarkan).

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 24.5 | ⭐ **HOOK**: "Macam mana kalau biru macam ni, pakai dengan baju sama?" | `BIRU MACAM NI?` 💙 → `PAKAI BAJU SAMA!` 👕 + bintang |
| 3.8 | 28.4 | "Okey, ni ada selimut tau, dua dalam satu." | `ADA SELIMUT` 🛏️ → planet `2 IN 1` 🪐 |
| 7.3 | 0.3 + 2.1 | "Tadaa! Comel kan! Ya Allah, dia lebih besar, bantal dia ni." (masih dalam plastik) | `TADAA!` ✨ → `COMEL KAN!` 🥹 → `BANTAL BESAR` 🤗 |
| 11.3 | audio 5.3, visual 13.0 | "Bestnya, peluk. Korang letak kat bilik tidur pun sangat sesuai." (J-cut atas dia peluk bantal) | `BESTNYA PELUK!` 🫂 → `SESUAI BILIK TIDUR` 🌙 |
| 15.1 | 32.5 | "Buka zip di belakang dia." | `BUKA ZIP BELAKANG` 🔓 |
| 16.8 | 34.1–40.4 | pusing bantal, buka zip (×3) | tag `>> x3` |
| 18.9 | 40.6 | "Keluarkan selimut dia." | `KELUARKAN SELIMUT` 🪄 |
| 20.2 | 42.7 + 45.6 | (warp) "Cantik kan? Selimut dia colour biru, biru muda, biru lembut gitu." | `CANTIK KAN?` 😍 → `SELIMUT BIRU` 💙 → `BIRU MUDA • LEMBUT` ☁️ |
| 23.9 | audio 46.9, visual 17.1 | "Okey, ni bantal dia tak kosong. Bantal dia masih lagi tebal gini, memang selesa lah." (J-cut: dia peluk bantal) | `TAK KOSONG` 👌 → `MASIH TEBAL` 💪 → `SELESA!` 😌 |
| 28.0 | audio 53.7, visual 55.1 | "Okey, ni size selimut dia." (selimut diangkat) | `SIZE SELIMUT` 📏 |
| 29.1 | 82.6 | (warp) "Besar juga ni, ngam elok untuk seorang baring." (selimut terbentang) | `BESAR JUGA!` 😮 → `MUAT SEORANG BARING` 🛌 + bintang |
| 31.6 | 88.2 | "Material selimut pun lembut, gebu-gebas." | `LEMBUT & GEBU-GEBAS` ☁️ |
| 33.5 | 63.6 + 67.1 | "Siapa yang belum ada lagi, selimut dengan bantal 2 in 1, untuk travel boleh ataupun untuk letak dekat bilik tidur, boleh grab yang ni." | `BELUM ADA LAGI?` 👀 → `SELIMUT + BANTAL` 🌌 → `TRAVEL • BILIK TIDUR` 🚀 → `GRAB YANG NI!` 🛒 |
| 40.4 | 70.5 | "Kalau minat design macam ni, korang grab sekali dengan baju. Comel ni." | `SUKA DESIGN NI?` 💫 → `GRAB SEKALI DENGAN BAJU!` 👕 → `COMEL!` 🥰 |
| 44.2 | 91.4 (visual) | - | End card: `BANTAL SELIMUT 🪐` / `2 IN 1 • BIRU LEMBUT • GEBU` / `TEKAN BEG KUNING` |

**Dibuang:** semua ayat harga (11.9–22.0s: "kalau harga dekat kedai mahal punya mahal… harga jimat", dua kali),
"Okey, dia besar macam ni" (ulang), jeda selepas "Tadaa", "Buka zip dekat belakang kita" (ulang), jeda selepas
"biru,", "Ini selimutnya", "Okey, dua dalam satu" (ulang, dah ada dalam hook), "2-in-1. Selimut bercorak tau /
selimut dia bercorak" (ulang), "Okey, ni selimut bercorak kita", "2-in-1" di hujung, jeda. Video ni tak sebut CTA
beg kuning, jadi `TEKAN BEG KUNING` cuma di end card (dia sebut "boleh grab yang ni").

## Belum pasti

- **"Comel kan!"** (2.1s): pass Whisper dengar "Chomekan", "Comegan" atau "Jom Egan"; semakan preview tak tangkap.
  Label `COMEL KAN!` ikut maksud.
- **"dia lebih besar"** (3.6s): satu pass dengar "dia dah besar".
- **"Bestnya, peluk"** (5.3s): satu pass dengar "Ya, peluk"; dua pass dan semakan preview dengar "bestnya".
- **"Siapa yang belum ada lagi"** (63.6s): pass penuh dengar "Apa yang belum ada lagi".
- **"ngam elok"**: semakan preview dengar "enam elok"; caption tulis "ngam".
- **"grab sekali dengan baju"**: dia maksudkan hud/baju yang sama corak. Kalau baju tu bukan produk yang dijual,
  buang baris "Pakai baju sama" dalam caption.

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

`sfx.py` menjana semua bunyi (`python3 sfx.py <dir>`), termasuk `warp`, `twinkle` dan `hum` baru.

**Masa render:** di container ni (4 CPU dikongsi, tiada GPU), render HyperFrames untuk 46.9s (1,407 frame)
ambil lebih kurang **5 min**; keseluruhan pipeline preview lebih kurang 7.5 minit.
