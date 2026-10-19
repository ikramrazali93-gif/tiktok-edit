# Bantal Roti Bakar (petak + bulat): edit plan, preview v1

Source: iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **66.8s**
Preview v1: **53.8s** (dipotong ~13s), 720×1280, 30fps, SDR, −11.9 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (ikut roti bakar)

| Warna | Hex | Guna |
|---|---|---|
| Coklat kerak gelap | `#4A2A12` | outline caption, teks label |
| Kerak keemasan | `#C98A3E` | kotak ROTI BAKAR JADI BANTAL, SAIZ SEDERHANA, tepi cover |
| Kuning mentega | `#FFD45C` | perkataan aktif caption, PANDAI DIA BUAT!, progress bar |
| Pink jem strawberi | `#FF5C8A` | keyword caption, HADIAH, BFF, JALAN-JALAN |
| Krim (isi roti) | `#FFF4DC` | kotak label biasa |

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio 56.3, visual 4.3 | ⭐ **HOOK** (J-cut atas shot dua-dua bantal depan kamera): "Pandai tahu, dia pun buat bantal. Roti bakar pun boleh jadi bantal." | `PANDAI DIA BUAT!` 🤭 → flash → `ROTI BAKAR JADI BANTAL!` 🍞 |
| 3.5 | 0.6 | "Comel kan? Ni bantal roti bakar." | `COMEL KAN?` 🥰 → `BANTAL ROTI BAKAR` 🍞 |
| 6.9 | 8.0 | "Okay, dia ada yang roti bakar petak dan roti bakar bulat. Ni bahagian depan ada tangan, ada kaki, boleh jalan-jalan-jalan." | `PETAK` 👈 → `BULAT` 👉 → `ADA TANGAN` 🙌 → `ADA KAKI` 🦶 → `BOLEH JALAN-JALAN!` 🚶 |
| 14.6 | 16.2 | "Tebal-tebal, dan lembut, gebu." | `TEBAL` → `LEMBUT & GEBU` ☁️ |
| 17.4 | 19.3 | "Dan belakang dia ada anti-slip, nak letak dekat kerusi yang licin ke kerusi kayu yang licin-licin, sesuai sangatlah. Dia ada tali, boleh ikat dekat tiang kerusi." | `BELAKANG ANTI-SLIP` 🛡️ → `KERUSI LICIN PUN OK` 🪑 → `SESUAI SANGAT!` → `ADA TALI IKAT KERUSI` 🎀 |
| 26.7 | 29.1 | "Ni saiz dia sederhana. Dia tak kecil dan tak terlalu besar sangat." | `SAIZ SEDERHANA` 📏 → `TAK KECIL, TAK BESAR` 👌 |
| 31.1 | 36.2 | "Boleh buat lapik duduk, peluk pun sedap, lapik kepala pun sedap. Sebab dia sangatlah lembut." | `LAPIK DUDUK` → `PELUK PUN SEDAP` 🤗 → `LAPIK KEPALA` 😴 → `SANGAT LEMBUT!` ☁️ |
| 36.5 | 42.1 | "Ni korang, nak yang mana satu boleh pilih. Nak bagi hadiah, mami nak bagi hadiah dekat anak, birthday anak ke, ni pun sesuai." | `NAK YANG MANA?` 🤔 → `HADIAH UNTUK ANAK` 🎁 → `BIRTHDAY ANAK!` 🎂 |
| 42.9 | 48.6 | "Yang mana kawan-kawan nak bagi hadiah dekat best friend, BFF." | `HADIAH KAWAN-KAWAN` 💝 → `BESTFRIEND / BFF!` 👭 |
| 46.7 | 53.8 | "Desain yang sangat unik, jarang-jarang ada." | `DESAIN UNIK` ✨ → `JARANG ADA!` 💎 |
| 48.9 | 62.7 | "Okay, korang tengok dekat beg kuning sekarang." | `TEKAN BEG KUNING` 🛒 |
| 51.5 | 65.3 (visual, slow) | - | End card: `BANTAL ROTI BAKAR` / `PETAK • BULAT • ANTI-SLIP` / `TAG BFF KORANG!` / `TEKAN BEG KUNING` |

Dibuang: "Ha," di awal, "ayam tus" lepas "roti bakar" (tak jelas), "Dia ada tulisan, dia cakap saya roti bakar" (tulisan "I'M TOAST", tapi Whisper tak pasti "tulisan/perhiasan"), "Okey" sebelum "tebal", "Ha, saiz dia sedang-sedang macam itulah" (ulang), "Ha, ini comellah" dan "Comellah, uniklah" (ulang), "Pandai tahu..." di tempat asal (dah jadi hook), senyap.

## Belum pasti

- **"Tebal-tebal"**: Whisper dengar "tebai-tebainah". Mungkin "tebal-tebal dia". Caption tulis "Tebal-tebal,".
- **"ayam tus"** (lepas "ini bantal roti bakar"): tak jelas, jadi dipotong.

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_12.6.png cover.jpg                              # cover 1080x1536
```
