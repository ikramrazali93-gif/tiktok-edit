# Pelampung Budak (tangan + dada): edit plan, preview v1

Source: iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **74.1s**
Preview v1: **47.9s** (dipotong ~26s), 720×1280, 30fps, SDR
Final: **47.9s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −11.8 LUFS, sudah render
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (ikut pelampung)

| Warna | Hex | Guna |
|---|---|---|
| Navy monster | `#1E2A78` | outline caption, teks label |
| Turquoise (badan pelampung) | `#1EC8C8` | keyword caption, label bahagian / snorkeling / tak tergolek |
| Teal gelap | `#0E9A9A` | highlight dalam kotak putih |
| Kuning (headphone monster) | `#FFD23F` | perkataan aktif caption, TERAPUNG!, MURAH, progress bar |
| Coral | `#FF5A5A` | label "masalah": PAKAI VEST?, BUDAK TERBALIK! |

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio 53.0 + 59.8, visual 64.0 | ⭐ **HOOK** (masalah → penyelesaian, J-cut atas close-up monster): "Kalau pakai vest tu, dia akan macam melayang, nak terbalik." + "Dia boleh kawal badan dia sendiri." | `PAKAI VEST?` 🦺 → `BUDAK TERBALIK!` 😰 → flash → `YANG NI KAWAL BADAN` ✅ |
| 6.8 | 0.9 / 6.9 | "Okay ni pelampung, pelampung tangan. Pelampung apa tu? Yang sekali dengan badan juga tu." | `PELAMPUNG TANGAN` 🏊 → `SEKALI DENGAN BADAN` 👕 |
| 13.5 | 10.3–20.0 | unboxing (×3) | tag `>> x3` |
| 16.8 | 22.2 | "Ni bahagian dada dia. Ni bahagian tangan dia." | `BAHAGIAN DADA` 👉 → `BAHAGIAN TANGAN` 💪 |
| 21.5 | 29.5 | "Okay ni letak dekat sini kan, lepas tu ni pakai dekat tangan." | `LETAK KAT DADA` → `PAKAI KAT TANGAN` |
| 25.6 | 33.7 | "Jadi anak kita, dia terapung lah, nak pergi mandi kolam ke, mandi pantai ke." | `TERAPUNG!` 🛟 → `MANDI KOLAM` → `MANDI PANTAI` 🏖️ |
| 30.5 | 39.2 | "Ni murah pun murah, jimat duit. Tak payah beli mahal-mahal sangat." | `MURAH PUN MURAH` 💸 → `JIMAT DUIT!` |
| 34.6 | 43.6 | "Nak pergi snorkeling ke apa ke, anak sesuai pakai ni. Dia akan balance badan dia." | `SESUAI SNORKELING` 🤿 → `BALANCE BADAN` ⚖️ |
| 38.3 | 48.0 | "Dia tak akan tergolek-golek, tak akan berpusing-pusing." | `TAK TERGOLEK` → `TAK BERPUSING` 👍 |
| 43.1 | 61.8 | "Dia boleh macam terapung elok lah." | `TERAPUNG ELOK` 🌊 |
| 45.3 | 70.8 (visual, thumbs up) | - | End card: `PELAMPUNG BUDAK` / `TANGAN + DADA • TAK TERBALIK` / `TAG MAK NAK KE PANTAI!` / `TEKAN BEG KUNING` |

Dibuang: "Oh gini, cini cini cini" (tak jelas), "Ini kan?", "kita kena jaga dia takut terbalik" (dah difahami dari hook), "Ini untuk pelampung untuk pakai mandi manda, snorkeling pun boleh" (ulang), senyap.

## Belum pasti

- **"Dia terapung lah"**: Whisper dengar "dia tak apung lah". Maksud ayat (anak boleh terapung bila mandi) lebih masuk akal dengan "terapung", jadi caption tulis "terapung".

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_64.6.png cover.jpg                              # cover 1080x1536
```
