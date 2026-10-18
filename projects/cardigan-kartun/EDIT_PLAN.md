# Cardigan Kartun Sekeluarga (dewasa + jumpsuit budak): edit plan, preview v1

Source: iPhone, 1080×1920 portrait, HEVC HDR (HLG), 59.94fps, **80.3s**
Preview v1: **58.8s** (dipotong ~21s), 720×1280, 30fps, SDR
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya

| Warna | Hex | Guna |
|---|---|---|
| Navy | `#1B2559` | outline caption, teks label, overlay end card |
| Biru royal (jumpsuit) | `#3B5BDB` | highlight, label DESAIN KARTUN / BIRTHDAY PARTY / ADA EKOR |
| Biru langit (cardigan) | `#9ED8F0` | keyword caption, label CAMERON / TEMPAT SEJUK / JIMAT |
| Pink (dalam telinga) | `#FF8FB1` | perkataan aktif caption, HAI KORANG, SATU KELUARGA, CUN MELECUN, progress bar |

Nama karakter tak digunakan langsung, cuma "kartun".

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 0.0 | ⭐ **HOOK** (bukaan asal): "Hai korang, siapa yang minat baju macam saya pakai ni, dia ada macam-macam desain kartun." | `HAI KORANG!` 👋 → `SIAPA MINAT?` 🙋 → `DESAIN KARTUN` 💙 |
| 6.1 | 6.4 | "Saya suka sangat jenis cardigan yang labuh macam ni, korang boleh pakai dekat Cameron." | `CARDIGAN LABUH` 🧥 → `PAKAI KE CAMERON` ⛰️ |
| 12.5 | audio 13.0, visual 63–69 | J-cut: "…bilik aircond ke, tempat-tempat sejuk ke, boleh sangat" atas close-up hud (mata, gigi) | `BILIK AIRCOND` ❄️ → `TEMPAT SEJUK` 🥶 → `BOLEH SANGAT!` |
| 18.4 | 18.9 | "Nak pakai waktu panas macam saya pakai sekarang pun boleh." | `WAKTU PANAS PUN BOLEH` ☀️ |
| 21.5 | 23.2 | "Yang ni saiz dewasa punya cardigan… budak-budak punya dia jumpsuit sekali dengan seluar. Tengok, boleh pakai satu keluarga." | `SAIZ DEWASA` 👩 → `BUDAK: JUMPSUIT` 🧒 → `SATU KELUARGA!` 👪 |
| 30.7 | 34.9 | "Ada saiz baby, saiz budak besar sikit, dan saiz dewasa. Saya akan letak 3 beg kuning." | `SAIZ BABY` → `SAIZ BUDAK` → `SAIZ DEWASA` → `3 BEG KUNING` 🛒 |
| 39.2 | 43.5 | "Satu family nak buat birthday party tema kartun ke, nak pergi Cameron pakai sedondon ke." | `BIRTHDAY PARTY` 🎂 → `TEMA KARTUN` 🎉 → `PAKAI SEDONDON` 👪 |
| 45.5 | 50.0 | "Cun melecun! Okay nampak. Ha, ni ada … ekor lagi." (dia pusing tunjuk belakang) | `CUN MELECUN!` 😍 → `ADA EKOR!` 👀 |
| 52.0 | 57.6 | "Harga pun murah aje, jimat-jimat aje hampa. Okay tengok dekat beg kuning." | `HARGA MURAH` 💸 → `JIMAT!` → `TENGOK BEG KUNING` 🛒 |
| 56.2 | 77.0 (visual) | - | End card: `CARDIGAN KARTUN` / `DEWASA • BUDAK • BABY` / `TAG FAMILY KORANG!` / `TEKAN BEG KUNING` |

Dibuang: jeda, "ok hampa boleh tengok dekat beg kuning" (CTA pertama yang ulang), senyap 62–80s (close-up hud yang tinggal dipakai untuk J-cut).

## Belum pasti

- **"Ha ni ada ekor lagi"**: Whisper dengar "toin-toin air-con" (bunyi tak jelas). Visual masa tu dia pusing tunjuk belakang, dan cardigan memang ada ekor. Caption tulis "ni ada… ekor lagi".

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_33.6.png cover.jpg                              # cover 1080x1536
```
