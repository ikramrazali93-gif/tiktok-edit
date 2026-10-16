# Patung Gajah Pink 25cm: edit plan, preview v1

Source: iPhone, 1080×1920 portrait, HEVC HDR (HLG), 30fps, **56.5s**
Preview v1: **37.5s** (dipotong ~19s), 720×1280, 30fps, SDR
Final: **37.5s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −11.6 LUFS, sudah render

## Gaya: comel / pastel (ikut video)

- **Font:** Fredoka Bold, bulat dan comel. Ada dalam `fonts/` (SIL OFL), install ke `~/.fonts` sebelum render.
- **Palet warna:** diambil dari gajah pink, bantal tembikai dan hoodie Stitch biru.

| Warna | Hex | Guna |
|---|---|---|
| Pink | `#FF5FA2` | label utama (ADA ANAK GIRL?, GAJAH PINK!, ADA EKOR!), progress bar |
| Hijau daun (daun gajah / kulit tembikai) | `#8BDB3C` | perkataan aktif caption, label SAIZ 25CM, BULU-BULU LEMBUT, TEKAN BEG KUNING |
| Biru lembut (hoodie) | `#7FD4FF` | keyword caption, label CLOSE UP, MAINAN BAYI, BOBOI? JANGAN! |
| Berry | `#8A1347` | outline caption, teks label, overlay end card |
| Putih | | kotak label biasa |

Perkataan aktif sengaja guna hijau, bukan pink. Caption duduk atas bantal tembikai yang pink, jadi pink akan tenggelam.

## Potongan

| Masa asal | Ayat | Status |
|---|---|---|
| 0.9–1.9 | Okay | ❌ |
| 1.9–6.6 | Korang yang mana ada anak girl? *(buka plastik)* Okay, ta-da! | ⭐ **HOOK**: misteri plastik → reveal |
| 6.6–7.6 | *(bersin)* | ❌ |
| 7.7–8.4 | Comel. | ✅ |
| 8.4–12.7 | Anak girl. Siapa yang ada anak girl, | ❌ "anak girl" kali ke-2 dan ke-3 |
| 12.7–17.4 | Nak cari mainan untuk anak girl, ada gajah yang ni. Ini gajah comel ni. | ✅ |
| 17.4–18.9 | Okay, comel je. | ❌ ulang |
| 18.9–20.7 | Saiz dia 25cm | ✅ |
| 20.7–23.2 | tak silap. Comel je. | ❌ "tak silap" melemahkan; comel ulang |
| 23.2–29.5 | Tapi warna dia lawa. Aesthetic ya warna dia. Warna pink-pink lembut macam tu. Okay, nampak saya close up dia. | ✅ |
| 29.5–32.6 | *(close-up, senyap)* | ⏩ ×2 |
| 32.6–34.4 | Ada **ekor** lah gajah ni. *(Whisper dengar "air cong")* | ✅ |
| 34.4–35.9 | *(bunyi tak jelas)* | ❌ |
| 35.9–39.3 | Itu dia. Comel, material jenis bulu-bulu lembut. | ✅ |
| 40.3–48.6 | Korang boleh beli buat hadiah ataupun mainan untuk bayi-bayi, anak-anak kecil girl lah sebab warna pink. | ✅ (jeda 0.6s dibuang) |
| 49.4–51.3 | Okay, kalau boboi jangan. | ✅ |
| 51.5–52.3 | Boboi jangan. | ❌ ulang |
| 52.4–53.7 | Warna pink tak boleh boboi. | ✅ penutup lawak |
| 53.8–55.9 | *(tolak gajah ke kamera)* | end card |

## Grafik & SFX

| TL | Grafik | SFX |
|---|---|---|
| 0.1 | `ADA ANAK GIRL?` (pink) 👧 ❓ | whoosh |
| 3.7 | flash putih + `TA-DAA!` ✨✨ | riser → impact + sparkle |
| 4.8 | `COMEL!` 🥰 | ding |
| 5.9 / 7.6 | `MAINAN ANAK GIRL` 🧸 → `GAJAH PINK!` 🐘 | pop ×2 |
| 9.4 | 💕 | pop |
| 10.6 | `SAIZ 25CM` (hijau) 📏 | click |
| 12.6–16.8 | `WARNA LAWA` → `AESTHETIC ✦` 🌸 → `PINK LEMBUT` 💗 | pop, sparkle, pop |
| 17.4 | `CLOSE UP` 🔍 | whoosh |
| 18.1 | speed ×2 | swish |
| 19.9 | `ADA EKOR!` 👉 (tunjuk ekor) | bloop |
| 22.7 | `BULU-BULU LEMBUT` ☁️ | pop |
| 26.0–31.6 | `BUAT HADIAH` 🎁 → `MAINAN BAYI` 👶 → `SESUAI ANAK GIRL` 🎀 | pop ×4 |
| 33.1 / 34.0 | `BOBOI? JANGAN!` 🙅 → `PINK TAK BOLEH BOBOI` 😂 | bloop, pop |
| 35.3 | End card: `TAG MAMA YANG ADA ANAK GIRL!` 👇 + `TEKAN BEG KUNING` 🛒 | whoosh, pop ×2, ka-ching |

Suara guna rantaian v2 (EQ kejelasan + −11.5 LUFS).

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
```
