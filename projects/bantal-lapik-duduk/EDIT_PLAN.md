# Bantal Lapik Duduk (petak + bunga bulat): edit plan, preview v1

Source: IMG_2930, iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **39.9s** (luar, atas rumput)
Preview v1: **35.7s** (dipotong ~4s), 720×1280, 30fps, SDR, −11.6 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

Produk: bantal / kusyen lapik duduk, saiz 40cm, 2 bentuk (petak & bunga bulat), kain beralur, kaler brown, pink, kelabu dengan bunga krim di tengah.

## Gaya (ikut kusyen) + refresh

| Warna | Hex | Guna |
|---|---|---|
| Koko | `#4A2C22` | teks label, outline caption, bayang patch, track progress bar |
| Karamel (kusyen brown) | `#C98A5E` | patch BROWN/petak, garis jahitan, swatch |
| Blush (kusyen pink) | `#F2A7BC` | patch pink, flash lembut, jahitan progress bar |
| Rose | `#C2577A` | kotak perkataan aktif caption, highlight label, patch hook |
| Kelabu dove | `#9C9CAB` | patch KELABU, swatch |
| Krim (bunga tengah) | `#FFF4E4` | patch utama, motif bunga, flash, kad end card |
| Kuning mentega | `#FFD54F` | BEG KUNING, highlight dalam patch rose |
| Blush pucat | `#FFD0DE` | keyword caption |

**Refresh (lain dari batch sebelum & dari kucing tidur / tembikai / bunga emoji):**
- **Label "patch kain berjahit"**: kotak bucu bulat + garis jahitan putus-putus di dalam (macam piping kusyen), bayang lembut, pop "squishy" (lebar → tinggi → normal). Label 2 baris untuk hook.
- **Caption**: perkataan aktif duduk atas **kotak patch rose bucu bulat** (dilukis per perkataan), bukan tukar warna / outline.
- **Motif bunga krim kecil** (macam bunga tengah kusyen) pop keluar & berpusing di tepi label penting.
- **Transisi**: **zoom punch-in** pada beat (zoom berubah dalam blok) + flash pastel blush/krim pendek.
- **Progress bar "jahitan"**: track koko + garis putus-putus blush terisi kiri ke kanan.
- **End card**: **kad krim berjahit (quilted)** + 3 swatch kaler (brown / pink / kelabu) pop satu-satu.
- **Cover**: latar **3 blok kaler pastel** (brown/pink/kelabu) dengan jahitan putih + gambar dalam **bingkai patch krim berjahit**; pill patch kecil + burst "SANGAT SELESA!".
- SFX baru `puff` (bunyi kusyen ditekan) pada poin selesa / tebal.

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 0.66 | ⭐ **HOOK** (ayat pembuka, "Ha" dibuang): "Yang mana lenguh-lenguh duduk dalam kereta tu, korang kena ada satu ni bantal untuk lapik duduk ni." | `LENGUH DUDUK / DALAM KERETA?` 😩 → punch-in + `KENA ADA / LAPIK DUDUK NI!` 🌸 + bunga |
| 5.8 | 6.84 | "Saiz dia 40cm, ada dua bentuk, ada bentuk petak, ada bentuk bulat macam ni." | `SIZE 40CM` 📏 → `ADA 2 BENTUK` ✌️ → `BENTUK PETAK` 🟫 → `BENTUK BULAT` 🌸 |
| 11.7 | 13.25 | "Sangat-sangat selesa. Tengok ketebalan dia. Lembut, fluffy macam ni." | `SANGAT SELESA` 😌 → `TENGOK KETEBALAN` 👀 → `LEMBUT & FLUFFY` ☁️ |
| 15.8 | 17.96 | "Ni bentuk petak dia pun sama tebal." | `PETAK PUN SAMA TEBAL` 👍 |
| 18.4 | 21.30 | "Colour dia sangat-sangat estetik, warna dia soft-soft, warna-warna pastel." | `KALER ESTETIK` 🎨 → `SOFT & PASTEL` 🍬 |
| 22.2 | 25.38 | "Ada warna brown, ada warna pink, ada warna kelabu, cantik kan." | `BROWN` 🤎 → `PINK` 🩷 → `KELABU` 🩶 → `CANTIK KAN?` 😍 |
| 26.8 | 30.74 | "Korang beli letak dekat dalam kereta, alas duduk dekat seat driver." | `LETAK DALAM KERETA` 🚗 → `ALAS SEAT DRIVER` 💺 |
| 31.5 | 35.97 | "Cepat-cepat tengok beg kuning." | `TENGOK BEG KUNING` 🛒 |
| 33.1 | 37.7 (visual) | - | End card kad berjahit: `BANTAL LAPIK DUDUK` / `PETAK • BULAT • 40CM` / 3 swatch / `KORANG NAK KALER MANA?` / `TEKAN BEG KUNING` |

Dibuang: "Ha" di awal setiap ayat, "Kan?" lepas "fluffy macam ni", "Ha dan" sebelum "colour", jeda 0.2s sebelum "kelabu", "Nah," dan "Ok ha", serta **"harga tengok promo"** di hujung (peraturan: tiada fokus harga).

## Belum pasti

- **"lenguh-lenguh"**: Whisper dengar "lengah-lengah" (2 kali). Maksud ayat (penat duduk lama dalam kereta) lebih kena dengan "lenguh", jadi caption tulis "lenguh-lenguh".
- **"Saiz"**: bunyi "S" perlahan; transkrip semula preview dengar "Saj dia 40cm". Audio tak terpotong (sebelum tu senyap dalam klip asal).
- **"Colour"**: transkrip semula dengar "Kala dia" (sebutan dia). Caption tulis "COLOUR".

## Render

```
python3 -I sfx.py sfx/                                                   # SFX (tambah 'puff')
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_2.2.png cover.png                               # cover 1080x1536 -> cover.jpg
```
