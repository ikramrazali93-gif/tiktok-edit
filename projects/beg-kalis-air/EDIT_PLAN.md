# Beg Kalis Air (Waterproof Bag, corak camo): edit plan, preview v1

Source: **2 video produk sama, digabung jadi satu** (iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, luar rumah atas rumput)
- **A** (`dl29`, IMG_7884, 134.9s): buka bungkusan oren, keluarkan beg, anak main dengan beg, cerita naik aeroplane / payung sebelum hujan
- **B** (`dl30`, IMG_7885, 68.4s): beg dipegang depan kamera, kegunaan, barang berharga / handphone, corak, CTA

`master1080.mp4` / `proxy.mp4` = A + B disambung (A 0–134.868s, B 134.868–203.2s). Masa transcript B dianjak +134.868s, jadi `edit.py` guna satu timeline. Kekuatan suara disamakan oleh rantai suara v2 (ukur ebur128 → −11.5 LUFS).

Preview v1: **50.9s** (daripada 203.2s gabungan), 720×1280, 30fps, SDR, −11.6 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (ikut beg camo + air)

| Warna | Hex | Guna |
|---|---|---|
| Navy | `#0B2545` | outline caption, teks label |
| Biru royal (camo) | `#1E6BFF` | WATERPROOF BAG, TRAVEL, MASUK BARANG, NAIK AEROPLANE?, end card |
| Aqua (air) | `#19C3E6` | keyword caption, NAK KE PANTAI?, SNORKELING, TAK TERENDAM!, LIPAT-LIPAT |
| Hijau askar (camo) | `#4F6B2A` | CAMPING, NI ADA CORAK!, STAND BY |
| Kuning matahari | `#FFD23F` | perkataan aktif caption, KENA ADA BEG NI!, BAWA BEG NI!, progress bar |
| Coral | `#FF6B4A` | HANDPHONE JATUH?, COMEL! |
| Pasir | `#FFF1C9` | MENDAKI GUNUNG, BARANG BERHARGA, SELALU KOSONG JE |

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio A 36.6 + 40.1, visual A 49.0 / B 0.1 | ⭐ **HOOK** (J-cut atas beg): "Untuk pergi pantai, kena ada beg ni lah." | `NAK KE PANTAI?` 🏖️ → flash → `KENA ADA BEG NI!` 🎒 |
| 2.8 | B 1.2 | "Ni waterproof, waterproof bag." | `WATERPROOF BAG` 💦 |
| 5.5 | B 9.4 | "Kita guna untuk snorkeling, nak pergi camping, nak pergi mendaki gunung-gunung yang bersalji." | `SNORKELING` 🤿 → `CAMPING` ⛺ → `MENDAKI GUNUNG` 🏔️ |
| 10.2 | B 18.7 | "Travel, fishing, untuk memancing ke, nak pergi laut ke." (anak lalu depan kamera) | `TRAVEL` ✈️ → `FISHING` 🎣 → `KE LAUT` 🌊 |
| 13.8 | B 27.2 | "Boleh masukkan barang-barang yang berharga dalam ni. Supaya dia tak rosak lah, handphone pun semua kalau dia jatuh ke apa ke, taklah terendam dengan air kan." | flash + `SIMPAN BARANG BERHARGA` 💎 → `HANDPHONE JATUH?` 📱 → `TAK TERENDAM!` 💧 |
| 23.0 | audio A 49.7 / 52.4 / 56.5, visual A 87.0 / 55.2 / 78.8 | "Kita masukkan barang dah ni." "Lepas tu, boleh tarik dia." "Lipat, oh lipat-lipat dia." | `MASUK BARANG` 👜 → `TARIK ATAS` → `LIPAT-LIPAT` 🔄 |
| 28.5 | B 45.8 | "Oh, comel lah sebab saya selalu tengok dia tak ada corak, kosong. Ni ada corak, comel lah corak dia." | `COMEL!` 😍 → `SELALU KOSONG JE` → flash + `NI ADA CORAK!` 💙 |
| 33.6 | audio A 107.8 / 113.8 / 120.8, visual A 66.8 / 71.4 / 88.8 (anak main dengan beg) | "Yang mana nak naik aeroplane? Bawa beg ni lah, over thinking sikit macam tu. Kita stand by, sediakan payung sebelum hujan." | `NAIK AEROPLANE?` ✈️ → `BAWA BEG NI!` 🎒 → `OVERTHINKING SIKIT` 🤭 → `STAND BY` → `SEDIA PAYUNG SEBELUM HUJAN` ☂️ |
| 41.9 | B 54.4 | "Okay, dapatkan korang kalau nak pergi snorkeling dekat pantai, dekat pulau, kan?" | `PANTAI • PULAU` 🏝️ |
| 45.3 | B 58.4 | "Nak pergi Sabah atau nak pergi Terengganu, kan?" | `SABAH • TERENGGANU` 🌴 |
| 47.2 | B 65.4 | "Okay, dapatkan dekat beg kuning." | `TENGOK BEG KUNING` 🛒 |
| 48.9 | B 63.5 (visual, beg dipegang, slow) | - | End card: `WATERPROOF BAG` / `PANTAI • SNORKELING • CAMPING` / `KORANG NAK BAWA KE MANA?` / `TEKAN BEG KUNING` |

Dibuang:
- A: "Okay, Bismillah", buka bungkusan oren (±30s), "Okay ni kita tengok apa dia / Oh ini? / Ini nak / Ini pengen apa? Waterproof bag" (ulang), "no clean / tak bersih" (tak jelas), "Bag waterproof" (ulang), "Wah ini ada desain corak ni. Selalu tengok yang kosong saja" (versi B lebih jelas), "Cantik ke bag ni?", cakap dengan anak ("Abang masuk ni", "Amir ada apa?", "Dali duduklah ni", "Buka Allah sayangku"), "ni dapat sekali dengan tali", "Dia kan untuk pergi snorkeling, hiking, tempat-tempat sejuk, tak nak bagi barang-barang kita basah" (B ulang lebih jelas), "takut apa tu, tempat masa lewat kan" (tak jelas), "Husna zon selalu" (tak jelas), "Betul, sungguh-sungguh, kena letak barang dalam ni" (ulang), pamplet.
- B: "Kita boleh guna untuk snorkeling, sabar-sabar" (ulang + cakap dengan anak), "apa lagi dia tulis tadi? Untuk", "Ya, aktiviti ayat-ayat ni kan", "Okey ni", **"Ini boleh buat pelampung ni. Kalau kita tak ada life jacket atau apa-apa, buat ni. Dia terapung lah dengan kita"** (sengaja dibuang: beg kalis air bukan alat keselamatan, jangan galakkan guna ganti life jacket), "Eh, pantai bolehlah", "Waterproof bag" sebelum CTA, jeda.
- **Harga:** tiada ayat harga (RM) dalam video ni, jadi tiada yang perlu dibuang. Tiada label "murah/jimat".

## Belum pasti

- **"dengan air"**: semua pass Whisper dengar "dengan ayah / ayam". Maksud ayat (handphone jatuh, tak terendam) jelas "air", jadi caption tulis "air".
- **"Supaya dia tak rosak lah"**: Whisper dengar "rosak" (pass penuh), "wasap", "wasalkan", "osot". Mungkin "basah". Caption tulis "rosak".
- **"Yang mana nak naik aeroplane"**: preview dengar "Kira mana"; pass lain dengar "awak mana". Caption tulis "Yang mana".
- **"sediakan payung"**: satu pass dengar "Kerjakan / Kudiakan"; dua pass lain jelas "sediakan".
- Nama anak ("Amir", "Dali") cuma dalam bahagian yang dibuang.

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_169.6.png cover.jpg                             # cover 1080x1536 (frame B 34.7s)
```
