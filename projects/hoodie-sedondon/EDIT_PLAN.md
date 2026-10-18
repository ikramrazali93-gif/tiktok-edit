# Hoodie + Seluar Sedondon Adik-Beradik: edit plan, preview v1

Source: iPhone, 1080×1920 portrait, HEVC HDR (HLG), 59.94fps, **52.6s**
Preview v1: **40.0s** (dipotong ~13s), 720×1280, 30fps, SDR
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya

| Warna | Hex | Guna |
|---|---|---|
| Ink | `#1F2330` | outline caption, teks label |
| Violet (tudung) | `#7C3AED` | highlight dalam kotak putih, burst `1 SET` |
| Lilac | `#B69CFF` | keyword caption, label ADIK 9 BULAN / TIDUR BILIK AIRCOND |
| Kuning | `#FFE14D` | perkataan aktif caption, SEDONDON, ABANG 3 TAHUN, DAPAT 1 SET, progress bar |

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio 15.0, visual 24.0 | ⭐ **HOOK** (J-cut): "Memang comel dia pakai hoodie ni sedondon." atas visual 2 saiz sebelah-menyebelah | `MEMANG COMEL!` 🥰 → flash → `SEDONDON ADIK-BERADIK` 👕👕 |
| 3.8 | 0.5 | "Okay ni dia baju hoodie, one set sekali dengan seluar, daripada size baby sampai anak besar sikit pun ada." | `HOODIE + SELUAR` ✅ → `SIZE BABY → BUDAK BESAR` 📏 |
| 10.9 | 8.0 | "Saya beli sedondon untuk adik dia. Anak saya umur 9 bulan dengan satu lagi abang dia umur 3 tahun." | `BELI SEDONDON` → `ADIK 9 BULAN` 👶 → `ABANG 3 TAHUN` 👦 |
| 17.5 | 18.8 | "Lepas tu dia ada pocket dekat tengah ni." | `ADA POCKET` 👉 |
| 19.0 | 20.6 | "Material dia pun lawa lah. Boleh pakai dalam mall, tidur bilik aircond, tempat sejuk, dapat one set sekali dengan seluar dia. Nampak tak?" | `MATERIAL LAWA` ✨ → `PAKAI KE MALL` 🛍️ → `TIDUR BILIK AIRCOND` 😴 → `TEMPAT SEJUK` ❄️ → `DAPAT 1 SET` 👖 → `NAMPAK TAK?` |
| 29.5 | 35.2 | "Dia punya material dia tip top. Hoodie dia pun lawa, jahitan dia pun kemas dan bawah dia ni bergetah macam ni." | `MATERIAL TIP TOP` 👌 → `HOODIE LAWA` → `JAHITAN KEMAS` 🧵 → `BAWAH BERGETAH` ✅ |
| 36.0 | 45.3 | "Seluar dia pun elok." | `SELUAR PUN ELOK` 👖 |
| 37.1 | 49.5 | *(tunjuk seluar)* | End card: `HOODIE SEDONDON` / `HOODIE + SELUAR • BABY → BESAR` / `TAG MAK-MAK 2 BERADIK!` / `TEKAN BEG KUNING` |

Dibuang: "Ha tu dia. Okay" + jeda (31–35s), "Allah, jatuh" (terjatuh barang), "Tujia" penutup.

Pembetulan script: perkataan di titik pecah zoom tak lagi keluar dua kali dalam caption (set `seen`), dan perkataan hujung klip tak hilang.

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_36.6.png cover.jpg                              # cover 1080x1536
```
