# Kasut Pantai / Kasut Aqua (dewasa + budak): edit plan, preview v1

Source: **2 video produk sama jenis, digabung jadi satu** (iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, luar rumah atas tikar)
- **A** (`dl31`, IMG_7886, 121.2s): buka bungkusan kasut hitam dia, cuba pakai
- **B** (`dl32`, IMG_7887, 37.2s): close-up kaki, kasut hitam dia dengan kasut biru anak, jalan atas tikar

`master1080.mp4` / `proxy.mp4` = A + B disambung (A 0–121.21s, B selepas tu). Masa transcript dianjak ikut cross-correlation audio: A +0.02s, B +121.254s (`A()` / `B()` dalam `edit.py`). Kekuatan suara bahagian B (−11.6 LUFS) dan A (−11.5 LUFS) dah sekata.

Preview v1: **25.8s** (daripada 158.4s gabungan), 720×1280, 30fps, SDR, −12.0 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

Video ni pendek sebab dalam klip A kebanyakan masa dia cuba pakai sambil cakap perlahan / tak jelas ("padan ke tidak", "nampak kecil", bercakap dengan anak). Yang jelas saja disimpan.

## Gaya (ikut kasut + pantai)

| Warna | Hex | Guna |
|---|---|---|
| Navy | `#16264D` | outline caption, teks label |
| Biru laut (kasut anak) | `#2F5BE7` | MACAM STOKIN, JOM CUBA!, COMEL!, DEWASA • BUDAK |
| Aqua | `#22D3C5` | keyword caption, TAPI ADA TAPAK!, DIA PADAN!, progress bar, ombak cover |
| Kuning matahari | `#FFD23F` | perkataan aktif caption, KASUT PANTAI!, SMART!, NGAM-NGAM! |
| Coral | `#FF6B5A` | TENGOK TAPAK DIA, BUNDA & ANAK |
| Pasir | `#FFF1D6` | UNBOXING!, SIAP NAK KE PANTAI? |
| Charcoal (kasut dia) | `#2A2A30` | HITAM |

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | B 0.0 / 2.1 / 9.3 / 11.2 / 13.8 | ⭐ **HOOK** (klip B, kaki ibu + anak, tapak kasut): "Kita pakai kasut nak pergi pantai. Dia macam stokin tu kan. Dia ada tapak kan, tengok tapak dia. Ni tapak dia." | `KASUT PANTAI!` 🏖️ → `MACAM STOKIN` 🧦 → flash → `TAPI ADA TAPAK!` 👟 → `TENGOK TAPAK DIA` 👀 |
| 5.7 | A 14.2 | "Ni kasut pantai." | `UNBOXING!` 📦 |
| 6.7 | A 17.4 | "Okay saya nak cuba." | `JOM CUBA!` |
| 7.5 | A 18.3–24.2 | keluarkan dari plastik (×3) | tag `>> x3` |
| 9.4 | audio A 25.4 + 26.6, visual A 34.0 | "Hitam lah. Smart." (J-cut atas dia angkat kasut) | `HITAM` 🖤 → `SMART!` 😎 |
| 10.9 | A 46.5–57.5 | pakai kasut (×2.5) | tag `>> x2.5` |
| 15.3 | A 79.3 | "Dia padan." | flash + `DIA PADAN!` ✅ |
| 16.3 | A 109.6 | "Ngam-ngam sangat lah kasut." | `NGAM-NGAM!` 👌 |
| 17.4 | B 20.6 | kasut biru anak: "Wow, comel!" | `COMEL!` 🥰 |
| 18.6 | B 24.0–28.0 | ibu + anak jalan atas tikar (tiada suara) | `ANAK PUN ADA` 👦 → `BUNDA & ANAK` 👩👣 |
| 22.6 | B 33.6 (perlahan ×0.8) | - | End card: `KASUT PANTAI` / `DEWASA • BUDAK` / `SIAP NAK KE PANTAI?` / `TEKAN BEG KUNING` |

Dibuang: "Okay, Bismillah. Ini kasut", "Wah, ini …?" (tak jelas), "Kaki Furqan macam kecil ya", "Oh ini untuk bunda dengan bapa" (tak pasti "bapa"), "Padan ke tidak?" ×4, "Sebentar", "Tepis sikit, abang Furqan", **baris saiz** (Whisper tulis "RM34.35" / "RM38.39"; sebenarnya bunyi macam nombor saiz 34-35 / 38-39, tapi tak jelas, jadi tiada harga atau saiz dalam video, label, cover atau caption), "Abang tanya…", "nampak kecil… tak tahu padan ke tidak", "tapi dia macam ngam-ngam sangat lah, dia kan nak pakai stokin lagi", "Sebab awal tu bawa air…", "Orang pakai ngam-ngam macam ni ke? Orang pakai stokin", klip B "Sekarang mari kita tengok…/Ini kasut nak pergi pantai" (tak jelas / ulang), "Comel kan?", ketawa anak, jeda.

## Belum pasti

- **"Dia macam stokin tu kan"**: Whisper dengar "stokir je / stokirnya / stocking yang". Caption tulis "stokin".
- **"tapak"**: Whisper tulis "tapok" (bunyi loghat); caption tulis "tapak".
- **"Hitam lah"**: satu pass dengar "hitam lawa", satu lagi "hitamlah awak". Caption tulis "Hitam lah."
- **"Okay saya nak cuba"**: semakan preview dengar "okey je nak try".
- **"Ngam-ngam"** bermaksud muat-muat / sendat. Dia juga sebut "dia kan nak pakai stokin lagi" (bahagian tu dipotong). Kalau nak beritahu pembeli supaya ambil saiz besar sikit kalau pakai stokin, tambah dalam caption.
- **Saiz**: baris saiz tak jelas dan dibuang (lihat atas). Kalau ada saiz yang betul, boleh tambah dalam caption.

## Render

```
# A + B digabung dulu (tone-map HLG → bt709 untuk setiap klip, lepas tu concat -c copy)
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_B20.7.png cover.jpg                             # cover 1080x1536 (B 20.7s: kasut hitam ibu + kasut biru anak)
```
