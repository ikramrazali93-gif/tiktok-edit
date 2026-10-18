# Tudung / Shawl Shimmer (navy + zamrud): edit plan, preview v1

Source: iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **56.6s**
Preview v1: **40.1s** (dipotong ~16s), 720×1280, 30fps, SDR
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya

| Warna | Hex | Guna |
|---|---|---|
| Navy gelap | `#1A2350` | outline caption, teks label |
| Navy royal (tudung) | `#2E3F9E` | GELAP LAGI CANTIK, DARK BLUE, BLING-BLING |
| Zamrud | `#7FB5A8` | label ZAMRUD, end card |
| Emas shimmer | `#F2C14E` | perkataan aktif caption, CANTIK PUN CANTIK, SHIMMER!, progress bar |

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio 15.2 + 17.2, visual 32.4 | ⭐ **HOOK** (J-cut): "Cantik pun cantik. Kalau gelap lagi cantik kan!" atas shot dia pakai tudung navy | `CANTIK PUN CANTIK` ✨ → `GELAP LAGI CANTIK!` 💙 |
| 2.6 | 2.8 | "Sebab saya pesan dua kaler. Yang ni dark blue, navy. Kita nak pakai dengan jubah kaler navy." | `PESAN 2 KALER` → `DARK BLUE / NAVY` → `MATCHING JUBAH NAVY` 👗 |
| 8.6 | 9.2–14.4 | buka plastik (×2.5) | tag `>> x2.5` |
| 10.6 | 18.9 | "Okay ni untuk kaler dark blue. Kaler dia macam navy blue macam tu lah." | `KALER DARK BLUE` → `MACAM NAVY BLUE` |
| 13.7 | 23.4 / 25.1 | "Okay, pakai." + "Comel lah!" | `JOM PAKAI!` → `COMEL!` 🥰 |
| 15.2 | 27.7 | "Boleh gayakan dengan jubah bling-bling. Saya banyak jubah bling-bling, nanti saya nak pakai gaya, insyaAllah." | `GAYA DENGAN JUBAH BLING` 💎 → `NANTI SAYA GAYAKAN` 💃 |
| 21.4 | 34.1 | "Okay nanti boleh tengok OOTD saya." | `TUNGGU OOTD SAYA!` 📸 |
| 23.7 | 37.0 | "Tudung shimmer-shimmer, shawl bling-bling macam ni, shawl shimmer-shimmer!" | flash + `SHIMMER!` ✨ → `BLING-BLING` |
| 27.4 | 42.0 | "Okay ni dua kaler lah. Yang ni zamrud, yang ni dark blue." (pegang dua-dua) | `2 KALER` → `ZAMRUD` 💚 → `DARK BLUE` 💙 |
| 31.1 | 46.6 | "Boleh tengok dekat beg kuning. Harganya sangatlah murah. Boleh beli banyak lah sis, sebab murah sangat kan." | `TENGOK BEG KUNING` 🛒 → `HARGA SANGAT MURAH` 💸 → `BELI BANYAK PUN BOLEH!` |
| 37.6 | 54.0 (visual) | - | End card: `TUDUNG SHIMMER` / `NAVY • ZAMRUD` / `KORANG SUKA KALER MANA?` / `TEKAN BEG KUNING` |

Dibuang: "Okay ni kaler kedua, Allahuakbar" (bukaan), "Murah je, murah je" (diulang, harga dah ada kat CTA), "Helo/Lawa pun lawa" (tak jelas), "Nah ni", "Kan?", jeda.

## Belum pasti

- Bahagian depan "cantik pun cantik" ada perkataan sebelumnya ("helo/lawa pun lawa") yang tak jelas, jadi aku potong dan mula dari "Cantik pun cantik".

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_47.6.png cover.jpg                              # cover 1080x1536
```
