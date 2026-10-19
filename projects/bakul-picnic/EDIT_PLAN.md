# Bakul Picnic Anyaman (2 size): edit plan, preview v1

Source: iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **50.9s**
Preview v1: **29.4s** (dipotong ~21s), 720×1280, 30fps, SDR, −11.7 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (ikut bakul)

| Warna | Hex | Guna |
|---|---|---|
| Navy batik (bingkai bakul) | `#1F2F5C` | outline caption, teks label, end card |
| Pink (jalur dalam bakul) | `#FF4F7B` | keyword caption, CUTI SEKOLAH = PICNIC!, COMEL PUN COMEL, BARANG PICNIC |
| Tan rotan / anyaman | `#E6BE72` | label size (40 x 30 CM, 30 x 20 CM), ADA PELEKAT |
| Kuning cerah | `#FFC93C` | perkataan aktif caption, WAJIB ADA NI!, BOLEH PILIH SIZE, progress bar |

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio 24.2 + 26.5, visual 31.4 / 18.4 / 12.3 | ⭐ **HOOK** (J-cut atas close-up bakul): "Cuti sekolah ni nak pergi picnic kan. Haa, wajiblah kena ada ni." | `CUTI SEKOLAH = PICNIC!` ☀️ → flash → `WAJIB ADA NI!` 🧺 |
| 4.0 | 7.3 | "Ni ada size besar dan ada size kecil, yang saya punya size 40x30cm." | `SIZE BESAR + KECIL` 📏 → `SAYA PUNYA 40 x 30 CM` |
| 8.6 | 13.8 / 17.1 | "Okay, dia ada pelekat macam ni." + "Okay, dalam dia macam ni Mummy." | `ADA PELEKAT` 👌 → `TENGOK DALAM DIA` 👀 |
| 12.4 | 20.1 / 22.7 | "Nak letak pinggan-pinggan, barang-barang picnic." | `LETAK PINGGAN` 🍽️ → `BARANG PICNIC` 🥪 |
| 15.2 | 29.6 | "Comel kan? Comel pun comel." | flash + `COMEL PUN COMEL` 🥰 |
| 16.9 | 33.4–39.1 | "Ni bahagian depan. Ni bahagian sisi tepi. Ni belakang dia." | `BAHAGIAN DEPAN` 👉 → `SISI TEPI` → `BAHAGIAN BELAKANG` 🔄 |
| 21.4 | 40.7 / 43.0 / 46.4 | "Okay, boleh pilih size apa yang Mummy nak. Paling kecil 30x20cm kan. Ni yang besar sikit." | `BOLEH PILIH SIZE` 🤔 → `PALING KECIL 30 x 20 CM` → `YANG BESAR SIKIT` 👆 |
| 26.9 | 48.4 (+ "Comel lah.") | - | End card: `BAKUL PICNIC` / `ANYAMAN • 2 SIZE` / `TAG GENG PICNIC KORANG!` / `TEKAN BEG KUNING` |

Dibuang: "Haa, Mummy nak pergi picnic kan, cuti-cuti sekolah nanti" (sama dengan hook), "mesti kena ada basket rotan ni" (sama dengan hook), "Rebak yang ni 40cm" (tak jelas, ulang size), "Haa, gitu", "nak letak apa tu", "Dia ada tepi ni macam ni", "Haa" sebelum "paling kecil", senyap.

## Belum pasti

- **"pelekat"**: Whisper dengar "perlekak / perlekat". Aku anggap maksudnya pelekat (velcro) penutup bakul.
- **"basket rotan"**: Whisper dengar "basket rata / rota". Ayat ni dibuang, jadi label guna "BAKUL PICNIC ANYAMAN" (tak sebut rotan).
- **Size**: dia sebut "saya punya size 40x30cm" dan "paling kecil 30x20cm". Caption ikut apa yang disebut.

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_12.6.png cover.jpg                              # cover 1080x1536
```
