# Bantal Gebu Grey (bentuk awan): edit plan, preview v1

Source: iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **53.0s**
Preview v1: **33.1s** (dipotong ~20s), 720×1280, 30fps, SDR
Cover: `cover.jpg` · Caption & hashtag: `CAPTION.md`

## Safe zone TikTok (baru)

Semua grafik duduk **di luar** kawasan UI TikTok:

| Zon dikosongkan | Saiz (720×1280 / 1080×1920) | Sebab |
|---|---|---|
| Kolum kanan | 110px / 165px | profile, like, komen, save, share |
| Bawah | 290px / 435px | nama akaun, caption, muzik |
| Atas | 110px / 165px | tab For You / Following, search |

Dalam `edit.py`:
- `SAFE_L/R/T/B` dan `CX` (tengah kawasan selamat). Label diletak pada `CX`, bukan tengah skrin.
- `fit_size()` kecilkan font label automatik kalau teks terlalu panjang (ukur dengan Pillow; nisbah libass/Pillow = 0.82).
- Sticker emoji di-*clamp*, jadi tak boleh masuk zon UI walaupun koordinat salah.
- Caption guna MarginL/MarginR/MarginV ikut safe zone, jadi baris panjang wrap dalam kawasan selamat.
- Tag speed (`>> x3`) dipindah ke kiri atas.

## Gaya

- **Font:** Fredoka Bold (bulat, cozy).

| Warna | Hex | Guna |
|---|---|---|
| Slate | `#2B3150` | outline caption, teks label, kotak "penekanan" |
| Grey-blue (kain kusyen) | `#8796C8` | badge end card / cover |
| Krim (piping kusyen) | `#FFF4DC` | kotak label biasa, keyword caption |
| Periwinkle | `#4F5FA8` | highlight dalam kotak krim |
| Emas (cahaya petang) | `#FFC93C` | perkataan aktif caption, RESTOCK!, GEBU-GEBU, progress bar |

## Potongan

| Masa asal | Ayat | Status |
|---|---|---|
| 24.7–26.1 | Hmm… lembut. *(picit kusyen)* | ⭐ **COLD OPEN** (dipindah ke depan) |
| 0.0–2.5 | Tiga, bismillah. | ❌ kiraan sebelum rakam |
| 2.5–4.2 | Bantal, colour grey. | ✅ |
| 4.2–6.3 | *(tarik dari plastik)* | ❌ |
| 6.3–13.5 | Tambah lagi bantal ni. Bantal ni ramai yang beli dekat live saya. Ramai sangat yang order dan berpuas hati. | ⭐ social proof |
| 13.9–16.9 | Sebab apa? Dia tebal, dia lembut. | ✅ |
| 17.0–19.4 | Boleh tengok sini. Dia punya tebal tu. | ✅ (jeda dibuang) |
| 19.4–24.6 | *(buka plastik)*, Dia tebal dan dia lembut *(ulang)* | ⏩ ×3, ayat ulang dibuang |
| 26.4–27.9 | Kalau buat duduk, the best. | ✅ |
| 28.0–32.4 | Ini dari depan, ini dari belakang, macam tu. | ✅ (jeda 1.2s dibuang) |
| 33.0–36.4 | …dia pun cantik dan material dia gebu-gebu gitu. | ✅ |
| 36.4–41.8 | *(senyap)* | ❌ |
| 41.8–47.7 | Korang boleh tengok dekat beg kuning tau, macam-macam dah bantal. Yang ni paling best lah bantal yang saya buat live tu kan. | ✅ CTA |
| 47.7–51.6 | Ini awak boleh tengok tau, boleh masuk live… beg kuning. | ❌ ulang CTA |
| 49.9–52.3 | *(visual)* | end card |

## Grafik & SFX

| TL | Grafik | SFX |
|---|---|---|
| 0.0 | `LEMBUT GILA!` (slate) 🤤 ☁️ | bloop |
| 1.5 | `BANTAL GREY` ☁️ | whoosh |
| 3.3 | `RESTOCK!` (emas) 📦 | ding |
| 5.6 | `RAMAI BELI DI LIVE` 🔥 | pop |
| 9.6 | `BERPUAS HATI` + ⭐⭐⭐⭐⭐ (satu-satu) | ding + pop ×5 |
| 10.5–12.9 | `SEBAB APA?` 🤔 → `TEBAL` → `TEBAL + LEMBUT` ✅ | pop ×3 |
| 13.6 / 14.5 | `TENGOK NI` 👀 → `TEBAL DIA` 💪 | whoosh, pop |
| 15.2 | speed ×3 (tag kiri atas) | swish |
| 17.4 | `BUAT DUDUK THE BEST` 👍 | pop |
| 19.5 / 20.4 | `DEPAN` → `BELAKANG` 🔄 | whoosh ×2 |
| 22.2 / 24.4 | `CANTIK` 🌼 → `GEBU-GEBU` ☁️ | sparkle, bloop |
| 25.6–30.7 | `TENGOK BEG KUNING` 🛒 → `MACAM-MACAM BANTAL` → `YANG NI PALING BEST` ⭐ → `DARI LIVE SAYA` 🔴 | pop ×4 |
| 30.7 | End card: `BANTAL GREY` / `TEBAL • LEMBUT • GEBU` / `TEKAN BEG KUNING` / `ATAU JOIN LIVE SAYA` | whoosh, pop ×3, ka-ching |

Suara guna rantaian v2 (EQ kejelasan + −11.5 LUFS).

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_48.4.png cover.jpg                              # cover (frame dari master1080 @48.4s)
```
