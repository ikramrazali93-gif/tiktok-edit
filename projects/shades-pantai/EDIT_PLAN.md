# Shades / Cermin Mata Hitam (2 desain): edit plan, preview v1

Source: iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **126.2s**
Preview v1: **61.4s** (dipotong ~65s), 720×1280, 30fps, SDR
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (pantai / shades)

| Warna | Hex | Guna |
|---|---|---|
| Espresso | `#2B1A12` | outline caption, teks label |
| Tortoise brown (design bulat) | `#A85A20` | highlight, COLOUR BROWN, BINGKAI HALUS |
| Amber (tint rimless) | `#FFB020` | perkataan aktif caption, PAKAI TUDUNG?, CANTIK TAK?, progress bar |
| Teal (laut) | `#19B5B0` | TAK KEMBUNG!, PI BERENANG, DESAIN KEDUA |

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 87.5 | ⭐ **HOOK** (dipindah, untuk penonton bertudung): "Yang ni kalau kita pakai tudung ke apa ke, dia tak nampak kembung sangat." | `PAKAI TUDUNG?` 🧕 → `TAK KEMBUNG!` ✅ |
| 4.2 | 0.5 | "Okay ni spek mata. Kita nak beli nak pakai pi pantai ni awak." | `SPEK MATA` 🕶️ → `PAKAI KE PANTAI` 🏖️ |
| 8.1 | 10.4 | "Kita tengok ada orang tu pakai cantik, lepas tu kita pun teracun. Nanti tengok saya pakai. Okay ada dua jenis spek." | `ORANG PAKAI CANTIK` → `KITA PUN TERACUN!` 🤭 → `2 JENIS` |
| 14.0 | 17.5–40.8 | unboxing + "Wow, ni colour brown" + "Tengok saya pakai" + pakai (×3, ×2.5, ×3) | `COLOUR BROWN` 🤎 |
| 23.4 | 40.8 / 46.5 | "Cantik tak?" + "Jujur, jujur, jujur." | flash + `CANTIK TAK?` 😎 → `JUJUR!` |
| 25.2 | 48.0 | "Okay dah colour brown saya pakai. Saya jarang nak pakai shades ni." | `JARANG PAKAI SHADES` |
| 28.3 | 54.0 | "Tapi ni tak ada power lah. Nanti saya akan pakai contact lens." | `TAK ADA POWER` 👁️ → `PAKAI CONTACT LENS` |
| 31.2 | 57.7 | "Saja lah nak pi berenang, nak bawa anak main pantai. Nak pakai kan, panas kan, kita pakai shades lah." | `PI BERENANG` 🏊 → `MAIN PANTAI` → `PANAS KAN` ☀️ → `PAKAI SHADES!` |
| 40.5 | 68.8 | "Okay lagi satu kita ada desain yang ni." | `DESAIN KEDUA` ✨ |
| 42.2 | 70.6–83.6 | buka + pakai rimless (×4) | tag `>> x4` |
| 45.5 | 92.3 | "Sebab nampak tak, dia punya ni halus je." | `SEBAB...` → `BINGKAI HALUS` 👓 |
| 49.6 | 102.6 | "Dia tak kembung tudung kita betul. Ini tak kembung awak. Kalau kata nak bergaya ke apa kan." | `TUDUNG TAK KEMBUNG` → `BETUL!` → `NAK BERGAYA` 💃 |
| 54.1 | 118.3 | "Harga murahnya, murah sangat. Dah saya ambil dua sebab murah saja." | `HARGA MURAH!` 💸 → `SAYA AMBIL DUA!` ✌️ |
| 57.2 | 123.4 | "Okay boleh tengok dekat beg kuning." | `TENGOK BEG KUNING` 🛒 |
| 58.9 | 120.8 (visual, pegang 2 shades) | - | End card: `SHADES 2 DESAIN` / `BROWN • RIMLESS` / `KORANG PILIH YANG MANA?` / `TEKAN BEG KUNING` |

Dibuang: "Dahsyat", "Sebentar lagi saya pakai", "Ini colour brown" ulang, "Cantik tak?" ×2 ulang, "Cuba kau main cantik tidak" (tak jelas), "Cantik tak?" design 2 (0.4s, tak jelas), "Yang ni macam… sebentar lah", "macam ni pula, janggal pula", CTA beg kuning pertama, senyap.

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_124.0.png cover.jpg                             # cover 1080x1536
```
