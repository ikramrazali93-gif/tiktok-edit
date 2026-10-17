# Baju Renang Anak (2 piece): edit plan, preview v1

Source: iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **47.4s**
Preview v1: **29.2s** (dipotong ~18s), 720×1280, 30fps, SDR
Final: **29.2s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −11.8 LUFS, sudah render
Cover: `cover.jpg` · Caption & hashtag: `CAPTION.md`

## Gaya: kolam renang / budak (ikut produk)

- **Font:** Fredoka Bold (bulat, mesra budak), ada dalam `fonts/`.

| Warna | Hex | Guna |
|---|---|---|
| Aqua (corak lengan) | `#22D3EE` | keyword caption, label "positif" (BAJU RENANG ANAK, PADAN!, 2 PIECE), progress bar |
| Navy (badan baju) | `#13204A` | outline caption, teks label, overlay end card |
| Coral (tag harga merah) | `#FF5A5F` | label soalan/harga (SIAPA NAK BELI?, PADAN TAK?, HARGA MURAH!) |
| Kuning cerah | `#FFD43B` | perkataan aktif caption: paling menonjol atas rumput dan langit |

## Potongan

| Masa asal | Ayat | Status |
|---|---|---|
| 29.3–35.0 | Ini untuk siapa nak beli baju renang, baju mandi, tangan panjang untuk anak. Seluar panjang. | ⭐ **HOOK** (dipindah ke depan): panggil terus pembeli sasaran sambil tunjuk baju |
| 0.0–4.4 | *(buka plastik, senyap)* | ⏩ ×3 |
| 4.4–7.8 | Ini baju renang Abang Furqan. | ✅ |
| 7.8–8.5 | *(senyap)* | ❌ |
| 8.5–10.3 | …saya tengok. Padan tak? | ✅ |
| 11.3–12.4 | Ini saiz paling kecil kan? | ✅ |
| 12.4–14.2 | *(jeda 1.8s)* | ❌ |
| 14.2–16.2 | Saiz paling kecil, padan kot. | ✅ |
| 17.4–20.7 | Yang ada seluar sekali, elok aje. Harga pun murah aje kan? | ✅ |
| 20.7–22.8 | *(senyap)* hmm | ❌ filler |
| 22.8–25.4 | Ui, panjang seluar dia. Abang kan rendah aje. | ✅ |
| 25.9–28.7 | Boleh dah. Tapi baju dia nampak padan aje, insyaAllah. | ✅ |
| 35.5–37.1 | Ha ini. Hmm | ❌ filler |
| 37.1–38.8 | Okay, dia two piece. | ✅ |
| 38.8–40.1 | two piece *(ulang)* | ❌ |
| 40.1–41.2 | Comel lah. Nanti bagi cuba. | ✅ |
| 41.3–43.5 | *(susun set atas kotak)* | end card |
| 45.3–47.4 | Okay guys / terima kasih | ❌ |

## Grafik & SFX

| TL | Grafik | SFX |
|---|---|---|
| 0.0 | `SIAPA NAK BELI?` (coral) 🙋 | whoosh |
| 1.7 | `BAJU RENANG ANAK` (aqua) 🏊 🫧 | bloop |
| 3.9 / 5.1 | `TANGAN PANJANG` ✅ → `SELUAR PANJANG` ✅ | pop ×2 |
| 5.8 | speed ×3 | swish, pop |
| 9.2 | `UNTUK ABANG FURQAN` 👦 | pop |
| 12.0 | `PADAN TAK?` 🤔 | bloop |
| 12.6 / 14.9 | `SAIZ PALING KECIL` 📏 → `PADAN!` ✅ | pop, ding |
| 15.8 / 17.5 | `ADA SELUAR SEKALI` 👖 → `HARGA MURAH!` 💰 | pop, ka-ching |
| 19.0–23.6 | `SELUAR PANJANG` → `ABANG RENDAH JE` 😆 → `BOLEH DAH!` 👍 → `NAMPAK PADAN` ✨ | pop, bloop, pop, sparkle |
| 24.8 | `2 PIECE` 👕👖 | pop ×2 |
| 25.9 | `COMEL!` 🥰 | ding |
| 27.0 | End card atas flat-lay: `BAJU RENANG ANAK` / `TANGAN + SELUAR PANJANG` / `TEKAN BEG KUNING` 🛒 | whoosh, pop ×2, ka-ching |

Suara guna rantaian v2 (EQ kejelasan + −11.5 LUFS).

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_15.3.png cover.jpg                              # cover (frame dari master1080 @15.3s)
```
