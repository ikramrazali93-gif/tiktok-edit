# Set Goggle + Snorkel Budak: edit plan, preview v1

Source: iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **106.5s**
Preview v1: **28.5s** (dipotong ~78s), 720×1280, 30fps, SDR
Cover: `cover.jpg` · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: sama macam `bantal-awan` (kanan 110px, bawah 290px, atas 110px pada 720×1280).

## Cabaran video ni

Sebahagian besar video (±80s) ialah unboxing yang **senyap**. Percakapan yang jelas cuma 4 ayat:
- "Ini goggle." (6.3s)
- "Ini kanak-kanak punya goggle." (8.8s)
- "Ini tempat bernafas, sedut kat mulut kan?" (80.8s)
- "Oh sini, kita duduk dekat sini kan." (93.3s)

Bahagian lain cuma bunyi plastik dan "hmm", dan Whisper "berhalusinasi" jadi "terima kasih kerana menonton" berulang kali. Jadi edit ni:
- **J-cut**: suara dari awal video dipasang atas visual terbaik dari belakang (hook dan "Ini goggle").
- Unboxing dipercepatkan (×7, ×1.5, ×1.3).
- Caption hanya untuk 4 ayat tu. Bahagian lain diisi dengan label dan SFX.
- **Muzik sangat penting** untuk video ni (bahagian senyap banyak): masukkan trending sound dalam TikTok/CapCut.

## Gaya (pantai / air, ikut produk)

| Warna | Hex | Guna |
|---|---|---|
| Navy | `#0B1E4F` | outline caption, teks label, overlay end card |
| Cobalt (warna mask) | `#1D4ED8` | kotak label GOGGLE BUDAK, WARNA BIRU, SEDUT DI MULUT |
| Aqua (lensa/air) | `#38E1FF` | keyword caption |
| Kuning (jalur pelangi snorkel) | `#FFD60A` | perkataan aktif caption, `+ SNORKEL!`, `CUBA PAKAI!`, TEKAN BEG KUNING |

## Susunan

| TL | Visual (asal) | Suara (asal) | Grafik | SFX |
|---|---|---|---|---|
| 0.0 | 76.2s pegang snorkel + goggle | "Ini kanak-kanak punya goggle" (8.8s) | `GOGGLE BUDAK` 🥽 | whoosh |
| 1.2 | 86.3s pakai goggle kat muka | - | flash + `+ SNORKEL!` 🤿🌊 | impact + sparkle |
| 2.9 | 28.4s keluarkan pek biru | "Ini goggle" (6.3s) | `UNBOXING` 📦 | pop |
| 4.6 | 30.1s tunjuk pek | - | `WARNA BIRU` 💙 | pop |
| 6.8 | 38–66s potong plastik (×7) | - | tag `>> x7` | swish, click ×4 (gunting) |
| 10.8 | 66–70.5s keluarkan set (×1.5) | - | `SET LENGKAP` ✅ | ding |
| 13.8 | 77.4s tunjuk set | - | `GOGGLE` 🥽 → `SNORKEL` 🤿 | pop ×2 |
| 17.2 | 80.8s | "Ini tempat bernafas, sedut kat mulut kan?" | `TEMPAT BERNAFAS` 💨 → `SEDUT DI MULUT` 👄 | pop ×2 |
| 20.0 | 85.8–90.6s cuba pakai (×1.3) | - | flash + `CUBA PAKAI!` 😎🫧 | bloop |
| 23.6 | 93.3s | "Oh sini, kita duduk dekat sini kan" | `PASANG SNORKEL` 👌 | pop |
| 25.5 | 101.4s | - | End card: `SET SNORKEL BUDAK` / `GOGGLE + SNORKEL` / `CUTI SEKOLAH JOM MANDI!` / `TEKAN BEG KUNING` | whoosh, pop ×3, ka-ching |

Dibuang: "Bismillah", unboxing beg luar & beg kertas (0–28s), "hmm" berulang, ayat yang tak jelas ("dah siap kan…", "…anggun… undang-undang"), "Okey" penutup.

Suara guna rantaian v2 (EQ kejelasan + −11.5 LUFS).

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_76.6.png cover.jpg                              # cover (frame dari master1080 @76.6s)
```
