# Bantal Peluk Durian #4 (Pastel lembut): edit plan, preview v1 (HyperFrames)

Source: IMG_3064, iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **33.0s**
Preview v1: **30.1s** (dipotong ~3s), 720×1280, 30fps, SDR, −11.0 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 165px, bawah 435px, atas 165px (1080×1920).

Video keempat dalam siri bantal durian (5 video, produk sama). Pipeline sama dengan `../bantal-durian-2`: potongan,
suara v2 dan SFX guna ffmpeg, dan lapisan grafik ialah komposisi **HyperFrames** (HTML + CSS + GSAP). Gaya,
hook dan sudut caption sengaja dibuat lain daripada video durian #1 (tidur peluk apa) dan #2 (hadiah).

## Gaya: "Pastel lembut" (dreamy)

| Warna | Hex | Guna |
|---|---|---|
| Blush pink | `#FFE1EC` → `#FFC1D8` | kad label (gradien ke mint), bola saiz, bokeh |
| Mint lembut | `#DDF7EC` / `#BDEFD9` | hujung gradien kad, bar kemajuan, bokeh |
| Plum | `#6B3F7A` | teks label & caption |
| Pink tua | `#E2588F` | kata kunci label, perkataan aktif caption, pil CTA |
| Hijau mint tua | `#2E9C7A` | kata kunci caption |
| Putih | `#FFFFFF` | bingkai kad, outline caption, kilauan |

- **Label:** kad bulat (pil) gradien blush→mint, bingkai putih dengan cahaya lembut, kilat kaca di atas, emoji
  dalam gelembung bulat. Masuk dengan blur → jelas + naik perlahan (expo.out), perkataan muncul satu-satu,
  kemudian terapung naik-turun perlahan selagi di skrin. Keluar dengan blur lembut.
- **Bola saiz:** "52 CM" dan "75 CM" dalam bola pastel berkilat yang terapung, dengan kilauan.
- **Caption:** huruf plum dengan outline putih lembut dan bayang. Perkataan aktif bertukar pink, naik sedikit
  dan bercahaya (glow), bertukar perlahan (bukan pil bergerak macam #1, bukan sapuan berus macam #2).
  Kata kunci hijau mint.
- **Peralihan:** "bloom" lembut, bulatan cahaya putih-blush-mint mengembang dari tengah dan pudar, dengan kilauan
  (2 kali: sebelum "dah lembut" dan sebelum "ada banyak saiz"). Bunyi `breeze`.
- **Ambien:** bokeh pastel terapung naik perlahan di tepi kiri dan kanan sepanjang video; kilauan 4 bucu keluar
  dari label besar.
- **Bar kemajuan:** bar gradien blush → kuning → mint dengan titik putih bercahaya.
- **End card:** kad lembut (blush → mint) dengan tajuk, pil putih "NAIK SERI BILIK • GEBU" dan pil CTA pink yang
  berdenyut.
- **SFX baru:** `chime` (loceng kaca lembut), `bubble` (gelembung pecah lembut), `breeze` (hembusan angin).
- **Cover:** latar pastel blush-mint dengan bokeh dan kilauan, gambar dalam tingkap bulat berbingkai putih,
  tajuk "BILIK NAMPAK KOSONG?" + pil "SATU JE, TERUS NAIK SERI" di jalur atas (di luar gambar), pil
  "BANTAL PELUK DURIAN" di bawah. Muka dia jelas.

## Muka tak ditutup ("kurangkan tutup bahagian muka")

- Kotak kepala + hud (sampai bawah penutup muka) ditanda **setiap 1 saat** daripada frame proxy bergrid
  (`HEADS` dalam `edit.py`).
- Untuk setiap caption, label, bola saiz dan end card, `edit.py` hantar semua kotak kepala dalam tempoh paparan
  elemen tu (±0.5s, zoom dikira) ke `comp/data.js`.
- Komposisi cari tempat sendiri: imbas safe zone dan pilih kedudukan paling dekat dengan kedudukan pilihan
  yang **kekal 44px jauh dari semua kotak kepala** dan tak bertindih caption yang sedang tayang. Label panjang
  dibalut 2 baris; kalau masih tak muat, versi kompak (font lebih kecil) dicuba dulu sebelum apa-apa bertindih.
- Dalam video ni kepala dia di tengah atas dan jalur atas sempit, jadi label kebanyakannya duduk **betul-betul
  bawah dagu** (atas badan bantal), caption di bawah. Bola "75 CM" duduk di bucu kiri atas.
- `check.py` lukis kotak kepala (cyan) dan zon UI TikTok (merah) atas frame preview. Semakan: tiada label,
  caption, bola atau end card masuk kotak kepala. Label kadang-kadang menutup sebahagian badan/muka bantal
  (tiada ruang lain), tapi tak pernah muka dia.
- Peralihan "bloom" memang menutup skrin sekejap (~0.5s), ini dibenarkan.

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 0.00 | ⭐ **HOOK** (ayat pembuka dia sendiri, masalah → penyelesaian): "Bilik nampak kosong sangat, tak seri kan?" (punch-in pada "tak seri") | `BILIK NAMPAK KOSONG?` 🛏️ + kilauan → `TAK BERSERI` 🥲 |
| 3.9 | 4.50 | "Korang tengok bantal durian ni boleh menyerikan bilik korang." | `BANTAL DURIAN NI` 💛 → `SERIKAN BILIK!` ✨ |
| 7.5 | 8.14 | "Letak kat katil tu." | `LETAK ATAS KATIL` 🛏️ |
| 8.4 | 9.40 | "Boleh peluk, teman tidur dan nampak berseri-seri." | `BOLEH PELUK` 🤗 → `TEMAN TIDUR` 😴 → `NAMPAK BERSERI-SERI` 🌸 |
| 12.7 | 13.62 | "Letak je satu bantal ni dah boleh naik seri kan." | `TERUS NAIK SERI` 🪄 |
| 15.1 | 16.52 | (bloom) "(Ha,) dah lembut, gebu macam ni, fluffy, sedap peluk ni." | `LEMBUT & GEBU` ☁️ → `FLUFFY, SEDAP PELUK` 🧸 |
| 18.9 | 20.86 | (bloom) "Ada banyak saiz. Kalau nak letak dalam kereta, boleh ambil yang ni..." | `BANYAK SAIZ` 📏 → `NAK LETAK DALAM KERETA?` 🚗 |
| 21.4 | 23.66 | "...saiz 52cm." | bola `52 CM` 🚗 |
| 22.9 | 25.10 | "Kalau yang ni saiz 75cm, buat peluk waktu tidur." | bola `75 CM` 🛌 → `PELUK WAKTU TIDUR` 😴 |
| 26.3 | 31.02 | CTA: "Korang tengok sekarang dekat bawah." | `TENGOK BEG KUNING 👇` 🛒 |
| 27.9 | 32.00 | - (slow-mo 0.5×) | End card: `BANTAL PELUK DURIAN 🌸` / `✨ NAIK SERI BILIK • GEBU` / `🛒 TEKAN BEG KUNING` |

**Dibuang:**
- jeda + "hmm/haa" panjang selepas "tak seri kan?" (3.9–4.5)
- jeda selepas "letak kat katil tu" (9.06–9.40)
- jeda sebelum "(ha,) dah lembut" (16.10–16.52); "Ha, dah" bersambung tanpa jeda, jadi "Ha" dikekalkan supaya "dah" tak terpotong
- jeda antara "yang ni" dan "saiz 52cm" (23.36–23.66)
- jeda + "haa" selepas "waktu tidur" (28.58–31.02), termasuk percubaan CTA pertama yang tak jelas
  ("korang tengok... kat beg, betul") (29.3–31.0); CTA yang jelas di 31.0 dikekalkan
- hujung klip lepas "dekat bawah" (suara senyap bawah end card)

Tiada sebutan harga dalam video ni.

## Belum pasti

- **"teman tidur" / "waktu tidur":** Whisper tulis "tidak" setiap kali (sama macam video durian lain). Ikut maksud
  ayat, caption tulis "tidur".
- **"bantal durian":** Whisper dengar "bantai doyan". Caption tulis "bantal durian".
- **"dekat bawah" (CTA):** dia tunjuk ke bawah, maksudnya beg kuning di bawah skrin. Label tulis
  `TENGOK BEG KUNING 👇`.
- **Percubaan CTA pertama yang dibuang (29.3–31.0):** Whisper dengar "korang tengok itu / tidak, betul / kat bag".
  Tak jelas, jadi dibuang; CTA kedua yang jelas dikekalkan.

## Render (HyperFrames)

Sama macam `../bantal-durian` dan `../bantal-durian-2` (lihat EDIT_PLAN di sana untuk butiran):

```
cd comp && npm install && cd ..                      # hyperframes@0.8.181 (dipin dalam comp/package.json)
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell   # pilihan

python3 edit.py proxy.mp4 transcript.json sfx/ out/                  # preview: out/preview.mp4 (720x1280)
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final   # final:   final/final.mp4 (1080x1920)
python3 edit.py proxy.mp4 transcript.json sfx/ out/ --graphics-only  # ubah grafik sahaja, guna semula out/base.mp4
python3 check.py out/ check.jpg                                      # check sheet: zon UI + kotak kepala + muka bantal

cd cover && npx --prefix ../comp hyperframes snapshot . --at 0.5 --no-end -o snap   # cover -> snap/*.png -> ../cover.jpg
```

`sfx.py` menjana semua bunyi (`python3 sfx.py <dir>`), termasuk bunyi pastel baru `chime`, `bubble` dan `breeze`.

**Masa render:** di container ni (4 CPU dikongsi dengan render lain, tiada GPU), render HyperFrames untuk 30.1s
(903 frame) ambil lebih kurang **2 min**. Keseluruhan pipeline preview lebih kurang 3–4 minit.
