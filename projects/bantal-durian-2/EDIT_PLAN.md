# Bantal Peluk Durian #2 (Kebun Durian): edit plan, preview v1 (HyperFrames)

Source: IMG_3061, iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **43.0s**
Preview v1: **36.0s** (dipotong ~7s), 720×1280, 30fps, SDR, −11.4 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 165px, bawah 435px, atas 165px (1080×1920).

Video kedua dalam siri bantal durian (5 video, produk sama). Pipeline sama dengan `../bantal-durian`: potongan,
suara v2 dan SFX guna ffmpeg, dan lapisan grafik ialah komposisi **HyperFrames** (HTML + CSS + GSAP). Gaya,
hook dan sudut caption sengaja dibuat lain daripada video durian pertama.

## Gaya: "Kebun Durian" (dusun)

| Warna | Hex | Guna |
|---|---|---|
| Kayu | `#C58A4E` → `#8E5727` | papan tanda label, papan end card, bingkai cover |
| Dakwat coklat gelap | `#3A2614` | outline tangan semua teks, bingkai papan |
| Krim | `#FFF4D6` | teks atas kayu, caption |
| Kuning durian | `#F6D84A` | perkataan aktif caption, kata kunci label, pil CTA |
| Hijau daun | `#7FB13A` / `#4F7A28` | daun, sapuan berus bawah perkataan, peralihan, bar kemajuan |

- **Label:** papan tanda kayu (ira kayu, dua paku, sepasang daun di bucu). Papan jatuh dari atas dan berayun
  (elastic), perkataan naik satu-satu, daun bergoyang. Label panjang dibalut jadi 2 baris, bukan dikecilkan.
- **Lencana keratan kayu:** "4 SAIZ" dalam keratan batang kayu bergelang, berpusing masuk.
- **Caption:** huruf krim dengan outline dakwat coklat. Perkataan aktif jadi kuning durian dan sapuan berus
  hijau dilukis di bawahnya (SVG stroke-dashoffset). Kata kunci hijau muda.
- **Peralihan:** daun hijau menyapu skrin (2 kali: sebelum "comelnya" dan sebelum "ada macam-macam saiz").
- **Daun berterbangan** keluar dari label besar dan lencana.
- **Bar kemajuan:** sulur hijau dengan sepasang daun di hujung.
- **End card:** timbunan papan kayu (tajuk, "4 SAIZ • GEBU • LEMBUT", CTA beg kuning) jatuh satu-satu.
- **SFX baru:** `knock` (papan kayu mendarat). `rustle` (daun) masa peralihan.
- **Cover:** bingkai kayu dengan daun di bucu bawah, papan tanda tajuk di kawasan pokok atas kepala, pil kuning
  "BUAT ORANG TERSENYUM", lencana kayu "4 SAIZ" di sebelah hud.

## Muka tak ditutup (peraturan baru: "kurangkan tutup bahagian muka")

- Kotak kepala + hud ditanda **setiap 1 saat** daripada frame proxy bergrid (`HEADS` dalam `edit.py`), bukan
  satu kotak per blok, sebab video ni handheld dan kepala dia banyak bergerak.
- Untuk setiap caption, label, lencana dan end card, `edit.py` hantar semua kotak kepala dalam tempoh paparan
  elemen tu (±0.7s, zoom dikira) ke `comp/data.js`.
- Komposisi sendiri cari tempat: imbas seluruh safe zone dan pilih kedudukan paling dekat dengan kedudukan
  pilihan (label atas, caption bawah) yang **kekal 44px jauh dari semua kotak kepala**. Ia juga elak titik muka
  bantal dalam shot close-up (`FACES`) dan tak bertindih dengan caption yang sedang tayang.
- Label yang tak muat satu baris dibalut jadi 2 baris dan dicari tempat semula.
- `check.py` lukis kotak kepala (cyan), titik muka bantal close-up (oren) dan zon UI TikTok (merah) atas
  frame preview. Semakan: tiada grafik masuk kotak kepala.
- Peralihan daun memang menyapu satu skrin sekejap (~0.6s), ini dibenarkan.

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 0.00 | ⭐ **HOOK** (ayat pembuka dia sendiri): "Saya tak sangka bantal macam ni boleh buat orang happy, tersenyum." | `TAK SANGKA!` 😮 → `BUAT ORANG TERSENYUM` 😊 + daun |
| 5.5 | 5.96 | "Kalau kita bagi hadiah dekat kawan, dekat best friend," | `IDEA HADIAH` 🎁 |
| 8.5 | 9.24 | "dekat anak, dekat mak kita yang suka durian ni," | `ANAK • MAK` 👩‍👧 → `PEMINAT DURIAN` 🌳 |
| 11.5 | 13.05 | "Mesti mak tersenyum." | `MAK TERSENYUM` 🥰 |
| 12.5 | 14.12 | (sapuan daun) "Eh, comelnya bantal durian yang gebu lembut ni." | `GEBU & LEMBUT` ☁️ |
| 16.0 | 17.58 | "Boleh peluk atau tidur." | `TEMAN TIDUR` 😴 |
| 17.8 | 19.80 / 22.84 | "Atau nak buat peluk dalam kereta, dalam bas." | `PELUK DALAM KERETA` 🚗 → `DALAM BAS` 🚌 |
| 21.2 | 24.24 | (sapuan daun) "Ada macam-macam saiz." | lencana kayu `4 SAIZ` |
| 22.4 | 25.82 | "Yang paling besar macam ni sampai kecil pun ada." | `PALING BESAR` 💪 → `KECIL PUN ADA` 🐣 |
| 25.4 | 31.30 | "Korang buatlah mak korang tersenyum, beli durian ni, ataupun buat diri sendiri happy kan." | `BUAT MAK TERSENYUM` 😊 → `BELI DURIAN NI` 💛 → `DIRI SENDIRI PUN HAPPY` 🥳 |
| 31.5 | 38.52 | CTA: "Korang tengok dekat beg kuning, boleh dapatkan sekarang." | `TEKAN BEG KUNING` 🛒 |
| 33.9 | 40.88 | - | End card: `BANTAL PELUK DURIAN 🌳` / `📏 4 SAIZ • GEBU • LEMBUT` / `🛒 TEKAN BEG KUNING` |

**Dibuang:**
- "Kan," sebelum "kalau kita bagi hadiah"
- "Haa" sebelum "mesti mak tersenyum"
- "kan?" yang panjang antara "dalam kereta" dan "dalam bas"
- "Ya Rabbi, Ya Allah" (seruan, tak tambah info)
- "Nah," sebelum CTA
- hujung klip ("terima kasih / comel macam ni" tak jelas), suara dimute bawah end card
- jeda-jeda pendek

Tiada sebutan harga dalam video ni.

## Belum pasti

- **"Boleh peluk atau tidur":** Whisper tulis "atau **tidak**" setiap kali. Ikut maksud ayat (dan ayat seterusnya
  "atau nak buat peluk dalam kereta"), caption tulis "tidur". Label cuma `TEMAN TIDUR`.
- **"mak" dalam "mesti mak tersenyum":** satu pass dengar "mata senyum". Caption tulis "mak".
- **"Korang tengok dekat beg kuning":** Whisper dengar "tengah" dan "Beko". Caption tulis "tengok dekat beg kuning".
- **"4 SAIZ":** video ni cuma sebut "paling besar sampai kecil". 4 saiz ikut video durian pertama (produk sama).

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

`sfx.py` menjana semua bunyi (`python3 sfx.py <dir>`), termasuk `knock` baru.

**Masa render:** di container ni (4 CPU dikongsi dengan render lain, tiada GPU), render HyperFrames untuk 36.0s
(1,079 frame) ambil lebih kurang **3 min**. Keseluruhan pipeline preview lebih kurang 4.5 minit.
