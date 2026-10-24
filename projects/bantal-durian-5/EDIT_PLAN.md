# Bantal Peluk Durian #5 (Retro sticker 90an): edit plan, preview v1 (HyperFrames)

Source: IMG_3065, iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **50.0s**
Preview v1: **42.2s** (dipotong ~8s), 720×1280, 30fps, SDR, −11.2 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 165px, bawah 435px, atas 165px (1080×1920).

Video kelima dalam siri bantal durian (5 video, produk sama). Pipeline sama dengan `../bantal-durian-2`: potongan,
suara v2 dan SFX guna ffmpeg, dan lapisan grafik ialah komposisi **HyperFrames** (HTML + CSS + GSAP). Gaya,
hook dan sudut caption sengaja dibuat lain daripada video durian #1–#4.

## Gaya: "Retro sticker 90an"

| Warna | Hex | Guna |
|---|---|---|
| Hot pink | `#FF4FA3` | sticker, bayang 3D perkataan aktif, jalur pelangi |
| Teal | `#19C3B5` | sticker, bayang 3D, jalur pelangi |
| Ungu | `#7B4DFF` | sticker, bayang 3D, jalur pelangi |
| Kuning | `#FFD23F` | kata kunci dalam sticker, perkataan aktif caption |
| Dakwat hitam | `#1B1B1B` | outline semua, bayang keras offset, petak checkerboard |
| Krim | `#FFF8E7` | dalam lencana nombor, kertas sticker end card |

- **Label:** sticker die-cut: garis potong putih, isi warna, border dakwat hitam, bayang keras offset 14px,
  tab checkerboard kecil di satu bucu, dan emoji dalam sticker bulat sendiri. Masuk dengan pop "squash & stretch"
  (elastic), perkataan melantun naik satu-satu, emoji bergoyang. Senget kiri/kanan berselang.
- **Lencana nombor** (4 SAIZ, 95CM, 30CM): sticker bulat dengan cincin jalur pelangi, nombor dengan bayang 3D,
  berpusing masuk.
- **Caption:** huruf putih tebal, outline dakwat + bayang keras. Perkataan aktif jadi kuning dengan bayang
  bertingkat pink/teal/ungu (gaya tajuk 90an) dan melantun sedikit. Kata kunci pink lembut. Saiz caption
  dikecilkan sendiri (76 → 66 → 58px) kalau saiz besar tak muat tanpa sentuh muka dia.
- **Doodle memphis:** squiggle, zigzag, segi tiga, bulatan, tambah, terpancar dari sticker besar dan lencana.
- **Peralihan:** checkerboard wipe (petak hitam + warna berpusing masuk dan keluar ikut pepenjuru), 3 kali:
  ke lawak "setia", ke "saiz", ke "gebu-gebas".
- **Bar kemajuan:** jalur pelangi 4 warna dengan 😎 bergolek di hujung.
- **End card:** kertas sticker krim (garis potong putus-putus, jalur checkerboard atas) dengan 4 sticker:
  `BANTAL PELUK DURIAN`, `TEMAN TIDUR PALING SETIA 💛`, `📏 4 SAIZ • 95CM - 30CM`, `🛒 TEKAN BEG KUNING`.
- **SFX baru:** `boing` (sticker pop), `blip` (8-bit arcade), `scratch` (vinyl scratch, peralihan pertama).
- **Cover:** latar jalur pelangi menyerong + lantai checkerboard, gambar jadi sticker die-cut senget, tajuk
  bertingkat 3D, sticker "TAK BERDENGKUR" / "GEBU-GEBAS!" dan lencana "4 SAIZ" atas badan bantal.

## Muka tak ditutup ("kurangkan tutup bahagian muka")

- Kotak kepala + hud ditanda **setiap 1 saat** (50 sampel) daripada frame proxy bergrid (`HEADS` dalam `edit.py`).
  Titik muka bantal dalam close-up besar (31–36s) ditanda dalam `FACES`.
- Untuk setiap caption, label, lencana dan end card, `edit.py` hantar semua kotak kepala dalam tempoh paparan
  elemen tu (±0.5s, zoom dikira) ke `comp/data.js`. Komposisi (`comp/index.html`, `place()`) imbas kawasan safe zone
  untuk tempat paling dekat dengan kedudukan pilihan (label atas, caption bawah) yang **44px jauh** dari semua kotak
  kepala, elak muka bantal close-up bila boleh, dan elak caption yang sedang tayang.
- Kalau tak muat: label cuba 1 baris dulu, kemudian dibalut 2 baris pada 660/540/440px; lencana dikecilkan
  (100/85/70%); caption dikecilkan (76/66/58px).
- Disemak dengan `check.py` (kotak kepala cyan, muka bantal oren, zon UI merah atas 40 frame preview):
  **tiada satu pun label, caption, lencana atau end card atas muka/hud dia.**
- Bahagian atas kepala dia banyak kali tinggi (y≈0.2), jadi kebanyakan label jatuh di tengah-bawah atas badan bantal,
  bukan di jalur atas. Dalam close-up "ada lagi besar" (muka dia besar di tengah) caption naik ke atas, terus di bawah
  label, sebab bawah dagu tak cukup ruang. Wipe checkerboard lalu atas semua frame selama ~0.6s (dibenarkan).

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 0.00 | ⭐ **HOOK** (ayat pembuka dia sendiri, video jalan masuk di-zoom 1.8x/1.35x supaya dia tak kecil): "Ini bukan bantal biasa tahu, ni teman tidur paling setia." | `BUKAN BANTAL BIASA!` 🙅‍♀️ → `PALING SETIA!` 💛 + doodle |
| 5.0 | 31.82 | (wipe + scratch) **lawak dipindah ke depan:** "Dia tak berdengkur, tak bunyi bising, dia teman korang, dia tak tidur. Korang tengok mata dia akan terbuka saja sentiasa, tak pernah tutup mata dia." | `TAK BERDENGKUR` 😴 → `TAK BISING` 🤫 → `TEMAN KORANG` 🫶 → `DIA TAK TIDUR!` 👀 → `MATA TAK TUTUP!` 👁️ |
| 14.1 | 5.08 | (wipe) "Kalau saiz ni tak cukup besar untuk korang, ada lagi saiz yang lagi besar." | `TAK CUKUP BESAR?` 🤔 → `ADA LAGI BESAR!` 😮 |
| 19.4 | 11.93 | "Dia ada macam-macam saiz tahu, empat saiz ada." | `MACAM-MACAM SAIZ` 📏 → lencana `4 SAIZ` |
| 22.0 | 14.88 | "Yang ni paling besar, saiz 95cm, yang ni memang betul-betul peneman tidur macam ni." | `PALING BESAR` 💪 → lencana `95 CM` → `PENEMAN TIDUR` 🛌 |
| 27.6 | 23.06 | "Saiz 30cm untuk anak baby-baby boleh kan." | lencana `30 CM` → `UNTUK BABY` 👶 |
| 31.0 | 26.97 | (wipe) "Gebu-gebas macam ni korang. Yang ni Allah sedapnya buat peneman tidur." | `GEBU-GEBAS!` ☁️ → `SEDAP BUAT TIDUR` 🥱 |
| 35.8 | 41.92 | "Sangat-sangat selesa." | `SANGAT SELESA!` 🥰 |
| 38.5 | 47.86 | CTA: "Tengok dekat bawah sekarang." | `TEKAN BEG KUNING 👇` 🛒 |
| 40.1 | 46.66 | - (thumbs up, slow-mo 0.5x, suara dimute) | End card kertas sticker |

**Dibuang:**
- "MashaAllah," sebelum "dia ada macam-macam saiz"
- "Kalau yang ni tak cukup besar ni, yang ni" sebelum "saiz 30cm" (mengelirukan: dia maksudkan saiz kecil)
- "Okey" sebelum "gebu-gebas"
- jeda 0.3s antara "tak bunyi bising" dan "dia teman korang"
- "ok" dan "gebu-gebas" yang diulang selepas "sangat-sangat selesa"
- jeda panjang sebelum CTA

Tiada sebutan harga dalam video ni.

## Belum pasti

- **"Nah," sebelum "yang ni Allah sedapnya":** suara ada (dikekalkan), tapi semakan preview tak dengar perkataan
  yang jelas, jadi caption tak tulis "Nah".
- **"tak pernah tutup mata dia":** Whisper dengar "pemata" / "permata". Mungkin "pun mata". Caption tulis "mata".
- **"gebu-gebas":** Whisper dengar "kebu-kebas" / "sebuah gebas" (cakap laju). Mula klip dah dibawa ke 26.97 supaya
  suku kata "ge" tak terpotong. Caption tulis "gebu-gebas".
- **"ada lagi saiz":** Whisper letak "ada" sangat pendek (7.84s); caption mula "ada" pada 7.50s ikut envelope.
- **Saiz:** video ni sebut "empat saiz", 95cm dan 30cm. End card tulis `4 SAIZ • 95CM - 30CM` (52cm dari video #1
  belum disahkan, jadi tak disebut).

## Render (HyperFrames)

Sama macam `../bantal-durian` (lihat EDIT_PLAN di sana untuk butiran):

```
cd comp && npm install && cd ..                      # hyperframes@0.8.181 (dipin dalam comp/package.json)
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell   # pilihan

python3 edit.py proxy.mp4 transcript.json sfx/ out/                  # preview: out/preview.mp4 (720x1280)
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final   # final:   final/final.mp4 (1080x1920)
python3 edit.py proxy.mp4 transcript.json sfx/ out/ --graphics-only  # ubah grafik sahaja, guna semula out/base.mp4
python3 check.py out/ check.jpg                                      # check sheet: zon UI + kotak kepala + muka bantal

cd cover && npx --prefix ../comp hyperframes snapshot . --at 0.5 --no-end -o snap   # cover -> snap/*.png -> ../cover.jpg
```

`sfx.py` menjana semua bunyi (`python3 sfx.py <dir>`), termasuk `boing`, `blip` dan `scratch` baru.
Perkataan caption diambil dari `WORDS` dalam `edit.py` (disemak tangan per chunk), bukan terus dari `transcript.json`.

**Masa render:** di container ni (4 CPU dikongsi dengan render lain, tiada GPU), render HyperFrames untuk 42.2s
(1,266 frame) ambil lebih kurang **2 min 15 s – 2 min 45 s**. Keseluruhan pipeline preview lebih kurang 4 minit.
