# Bantal Bunga Daisy (putih + mustard): edit plan, preview v1

Source: IMG_2937, iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **42.6s**, dalam rumah
Preview v1: **31.4s** (dipotong ~11s), 720×1280, 30fps, SDR, −11.4 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya: "breakfast cafe" (refresh, lain daripada video batch-4 yang lain)

| Warna | Hex | Guna |
|---|---|---|
| Cocoa | `#4A3426` | teks caption & label, outline |
| Mustard (yolk) | `#E8A21F` | blinds, isi progress bar, tengah daisy |
| Butter | `#FFE08A` | isi label, blinds, gelang pinggan |
| Cream | `#FFF8EC` | bar caption, wash end card |
| Sky | `#8FCBEA` / `#2F86C0` | rim pinggan, keyword caption, awning cover |
| Coral | `#F0584A` | perkataan aktif caption, highlight |

Refresh yang dipakai:
- **Label daisy-edge**: badge bertepi kelopak (scallop) putih dengan bulatan tengah butter/putih, pop masuk (overshoot) dan senget ±2°.
- **Caption atas bar krim**: bar bulat krim di belakang setiap chunk, teks cocoa, perkataan aktif coral + membesar sedikit, keyword biru langit.
- **Gelembung**: bulatan lembut naik di tepi kiri/kanan dan pecah setiap kali bahagian baru (SFX `bubble`).
- **Transisi blinds**: 6 jalur mustard/butter melintas dari kiri lalu pudar (SFX `blinds`).
- **Progress bar**: track krim, isi mustard, dan daisy kecil yang **bergolek** di hujungnya.
- **End card pinggan sarapan**: pinggan putih ber-rim biru langit berpusing masuk, teks di dalam pinggan.
- **Cover**: awning kafe jalur biru/putih, latar butter bertabur daisy kecil, foto dalam bingkai tepi kelopak, badge pinggan "NAIK SERI RUANG TAMU!".
- SFX baru: `squish` (picit bantal), `bubble`, `blinds`.
- Stiker emoji kini dilukis **atas** lapisan ASS supaya tak pudar di bawah wash end card.

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 0.4 | ⭐ **HOOK** (masalah → penyelesaian): "Sofa kosong sangat. Letaklah bantal bunga yang gebu ni. Barulah estetik. Barulah naik seri ruang tamu kita kan." | `SOFA KOSONG?` 🛋️ → `LETAK BANTAL BUNGA!` 🌼 → `BARU ESTETIK!` ✨ → `NAIK SERI RUANG TAMU` 🏡 |
| 8.0 | 8.7 | "Ada size 50cm dengan size 35cm." | `SIZE 50CM` 📏 → `& 35CM` |
| 11.3 | 16.8 | "Nah yang ni tengok material bulu-bulu fluffy." (close-up mustard) | `TENGOK MATERIAL` → `BULU-BULU FLUFFY` ☁️ |
| 14.8 | 20.6 | "Ada dua warna. Warna putih. Ya Allah lawa." (close-up putih) | `ADA 2 WARNA` 🎨 → `PUTIH, LAWA!` 🤍 |
| 18.9 | 27.7 | "Lembut je tengok saya picit. Toing-toing. Toing-toing." | `LEMBUT JE!` 🤲 → `TOING-TOING!` 😆 ×2 (SFX squish + boing) |
| 23.6 | 32.7 | "Nak buat bantal dalam kereta pun sangat sesuai. Boleh peluk, boleh peluk macam tu." | `SESUAI DALAM KERETA` 🚗 → `BOLEH PELUK!` 🤗 |
| 27.9 | 37.4 | "Tengok dekat beg kuning." | `TENGOK BEG KUNING` 🛒 |
| 29.0 | 39.5 (visual, ×0.75) | - | End card pinggan: `BANTAL BUNGA` / `SIZE 50 • 35 CM` / `PUTIH • MUSTARD` / `TEKAN BEG KUNING` |

Dibuang:
- **Harga (peraturan tiada harga):** "Harga dia sangat sangat jimat. Korang mesti terkejut tengok harga yang sangat murah ni." dan "Harga dia sangat mesra poket."
- "Okey yang ni untuk size 50 dengan 35cm tu" (ulang saiz), "Okey" sebelum CTA, satu suku kata terpotong sebelum "sofa" di awal klip, jeda.

## Belum pasti

- **Saiz kecil 35cm atau 30cm**: transkripsi penuh dengar "tiga puluh cm", tapi 3 semakan per-chunk (termasuk audio preview) dengar "tiga puluh lima" dan bunyi suku katanya lebih panjang daripada "lima puluh". Caption, label dan end card tulis **35cm**. Tolong sahkan.
- **"picit"**: dia sebut "pichik" (loghat); caption tulis "picit".
- **Warna kedua**: dia cuma sebut "putih"; warna kedua (mustard/kuning tua) diambil dari visual, end card & cover tulis "MUSTARD".

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_7.0.png cover.png                               # cover 1080x1536 (simpan sebagai cover.jpg)
```
