# Bantal Kucing (bantal peluk panjang): edit plan, preview v1

Source: iPhone, 1080×1920 portrait, HEVC HDR (HLG), 59.94fps, **52.0s**
Preview v1: **33.7s** (dipotong ~18s), 720×1280, 30fps, SDR
Final: **33.7s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −12.1 LUFS, sudah render
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: sama macam `bantal-awan` (kanan 110px, bawah 290px, atas 110px pada 720×1280).

## Gaya (ikut kucing + hoodie Stitch)

- **Font:** Fredoka Bold.

| Warna | Hex | Guna |
|---|---|---|
| Koko | `#4A2C1A` | outline caption, teks label, overlay end card |
| Karamel (bulu kucing) | `#FFC685` | keyword caption, label BANTAL KUCING / WARNA BROWN |
| Coklat | `#B5652B` | highlight dalam kotak krim |
| Krim | `#FFF3DF` | kotak label biasa |
| Pink (tapak kaki kucing) | `#FF7EB3` | perkataan aktif caption, MEOW MEOW, SAYA MEOW, ADA EKOR, progress bar |
| Biru langit (hoodie) | `#8ED1F5` | HAI HAI!, KAIN BALDU, TEKAN BEG KUNING |

## Susunan

| TL | Masa asal | Ayat | Grafik | SFX |
|---|---|---|---|---|
| 0.0 | 25.4 | ⭐ **HOOK**: "Meow meow, siapa peminat kucing?" (dipindah ke depan) | `MEOW MEOW~` 😺 → `SIAPA PEMINAT KUCING?` 🙋🐾 | bloop, pop |
| 2.5 | 41.1 | ⭐ "Hai hai, I'm meow! Saya meow!" (lambai tangan kucing, macam puppet) | `HAI HAI!` 👋 → `I'M MEOW!` 🐱 → `SAYA MEOW!` 🐾 | pop, bloop ×2 |
| 6.1 | 0.4–10.6 | *(buka kotak, ×4)* | `JOM UNBOXING` 📦 | whoosh |
| 8.6 | 10.6 | "Bantal kucing, waduh yang kotak ya. Oi, comel!" | `BANTAL KUCING` 🐈 → `COMEL!` 🥰 | pop, ding |
| 12.6 | 14.6–24.7 | *(buka plastik, ×3.5)* | tag `>> x3.5` | swish, sparkle |
| 15.5 | 28.0 | "Kalau boleh tengok bantal kucing yang comel macam ni, warna dia macam brown-brown gitu." | `COMEL MACAM NI` 😻 → `WARNA BROWN` 🤎 | pop ×2 |
| 20.3 | 33.3 | "Dalam dia kapas, luar dia material kain baldu. Bagus, lembut juga. Ah, cute." | `DALAM: KAPAS` ☁️ → `LUAR: KAIN BALDU` ✨ → `LEMBUT JUGA!` 🤗 → `CUTE!` 💕 | pop, pop, bloop, sparkle |
| 27.1 | 45.3 | "Ada tangan, ada kaki, ada ekor juga dekat belakangnya." | `ADA TANGAN` → `ADA KAKI` → `ADA EKOR JUGA!` 🐾✅ | pop ×3 |
| 30.9 | 49.1 | *(peluk kucing)* | End card: `BANTAL KUCING` / `PANJANG • LEMBUT • COMEL` / `TAG PEMINAT KUCING!` 👇 / `TEKAN BEG KUNING` 🛒 | whoosh, pop ×3, ka-ching |

Dibuang: "Jom unboxing, bismillahirrahmanirrahim" + senyap (0–10s), "Comel" yang tenggelam masa buka plastik, jeda-jeda pendek.

Suara guna rantaian v2 (EQ kejelasan + −11.5 LUFS).

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_31.0.png cover.jpg                              # cover 1080x1536 (frame dari master1080 @31.0s)
```
