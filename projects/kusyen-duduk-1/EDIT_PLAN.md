# Kusyen Duduk #1 (Kafe kopi & kraft): edit plan, preview v1 (HyperFrames)

Source: IMG_3066, iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **31.7s**
Preview v1: **27.7s** (dipotong ~4s), 720×1280, 30fps, SDR, −11.4 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 165px, bawah 435px, atas 165px (1080×1920).

Video pertama dalam siri kusyen duduk (5 video, produk sama: kusyen petak berbutang, kain waffle, merah & beige).
Pipeline sama dengan `../bantal-durian-2`: potongan, suara v2 dan SFX guna ffmpeg, lapisan grafik ialah komposisi
**HyperFrames** (HTML + CSS + GSAP) yang letak setiap grafik sendiri jauh dari muka dia.

## Peraturan baru: "kurangkan text dan animation bahagian tengah video"

- **Kotak tengah bebas** (x 160–920, y 480–1340 pada 1080×1920; `KEEPOUT` dalam `edit.py`): tiada label, sticker,
  biji kopi atau peralihan di situ. `place()` dalam komposisi beri penalti besar kalau masuk kotak ni (lebih kecil
  daripada penalti muka, lebih besar daripada bertindih caption).
- **Label sikit & kecil:** 8 tag sahaja untuk 27s (bukan satu setiap ayat). Caption bawa yang lain.
- **Label hanya di jalur atas** (atas kepala / sebelah kepala). Bila kepala penuhkan jalur atas, tag dibalut
  2–3 baris dan dikecilkan (sampai 34px) sampai muat di bucu kiri atas.
- **Tiada wipe skrin penuh:** peralihan cuma "wap" krim di tepi skrin (tengah kekal jernih), 2 kali.
- **Biji kopi** keluar dekat tag hook sahaja, dan cuma di tempat luar kotak tengah dan luar kepala.
- **End card** papan kapur kecil di bawah (boleh masuk sikit kotak tengah di hujung video, dibenarkan).
- `check.py` lukis kotak tengah (hijau), kotak kepala (cyan) dan zon UI TikTok (merah).

## Gaya: "Kafe kopi & kraft"

| Warna | Hex | Guna |
|---|---|---|
| Kraft | `#D8B48A` → `#C9A074` | tag kertas kraft, bingkai cover |
| Espresso | `#3B2416` | dakwat teks, outline caption, chip perkataan aktif |
| Krim susu | `#FFF6E6` | caption, jahitan putus-putus pada tag |
| Latte | `#F2C38B` | kata kunci caption, bingkai chip, tajuk papan kapur |
| Merah kusyen | `#C8102E` | kata kunci dalam tag (ikut kusyen merah) |
| Papan kapur | `#26302B` / bingkai `#8B5E3C` | end card, tajuk cover |

- **Label:** tag kertas kraft (hujung kiri bertakuk, lubang + tali twine, jahitan krim putus-putus, emoji dalam
  bulatan krim). Masuk meluncur dari kiri dengan sedikit putaran, perkataan naik satu-satu, berayun perlahan.
- **Caption:** huruf krim, outline espresso. Perkataan aktif duduk atas "chip menu" espresso bergaris latte.
- **Peralihan:** wap krim di tepi skrin (radial, tengah lutsinar), sebelum "macam-macam colour" dan sebelum
  "material jenis waffle".
- **Bar kemajuan:** tali twine kraft di atas dengan ☕ bergerak.
- **End card:** papan kapur menu kecil: "BANTAL ALAS DUDUK" / "40×40 CM • WAFFLE • BOLEH BASUH" / CTA kuning.
- **SFX baru:** `clink` (cawan & piring, tag mendarat), `chalk` (kapur, end card).
- **Cover:** bingkai menu kraft dengan jahitan dan biji kopi di bucu, tajuk papan kapur "LENGUH DUDUK LAMA?"
  (+ "geng ofis, ni untuk korang") di kawasan pokok atas hud, tag kraft "BANTAL ALAS DUDUK 40×40" dan lencana
  bulat "BOLEH BASUH" di bawah. Tiada apa atas muka atau atas dua kusyen.

## Muka tak ditutup

- Kotak kepala + hud ditanda setiap 1 saat (dan 15.2/15.5/15.8/22.7/23.1s masa dia hayun) daripada frame proxy
  bergrid (`HEADS`). Close-up tekstur 23.3–25.9s tiada kepala.
- Setiap caption, tag dan end card dapat semua kotak kepala dalam tempoh paparan (±0.5s) dan duduk sekurang-
  kurangnya 44px jauh. Check sheet (26 frame): tiada grafik atas muka/hud, tiada tag dalam kotak tengah.
- Label "MACAM-MACAM WARNA" dipapar dari "warna merah" (src 16.1s), sebab sebelum tu kepala dia hayun dari kanan
  ke kiri dan seluruh jalur atas tertutup.

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 0.00 | ⭐ **HOOK**: "Yang mana geng-geng ofis lenguh-lenguh duduk lama-lama kan?" | tag `LENGUH DUDUK?` 😩 + biji kopi |
| 3.8 | 4.08 | "Dah ada ke bantal untuk alas duduk? Ni selesa macam ni. Memang ngam elok. Saiz dia 40cm x 40cm." | `SELESA` ☕ → `40 × 40 CM` 📏 |
| 11.0 | 11.30 | "Memang ngam dengan kerusi ofis korang." | `NGAM KERUSI OFIS` 🪑 |
| 14.1 | 14.77 | "Ada macam-macam colour. Warna merah pun cantik sangat-sangat." | wap + `MACAM-MACAM WARNA` ❤️ |
| 18.1 | 19.17 | "Ni ketebalan dia." | (caption sahaja) |
| 19.2 | 22.94 | "Material jenis waffle." (close-up tekstur) | wap + `KAIN WAFFLE` 🧇 |
| 21.5 | 25.70 | "Senang boleh basuh tau korang." | `SENANG BASUH` 🫧 |
| 24.0 | 28.20 | CTA: "Tengok dekat beg kuning di bawah tau." | `TEKAN BEG KUNING` 🛒 |
| 26.2 | 30.90 | (slow-mo ×0.5) | end card papan kapur |

Dibuang: "Okey" sebelum "Ada macam-macam colour", "Okey" sebelum "ni ketebalan dia", ulangan "size 40cm x 40cm ni"
(20.3–22.8s), jeda selepas "dekat" (28.8–29.4s), "beg kuning" yang diulang di hujung (dimute bawah end card).
Tiada sebutan harga dalam video ni.

## Belum pasti

- **"bantal"**: Whisper dengar "bantai" / "bantuan". Caption tulis "bantal".
- **"ngam"**: pass semakan preview dengar "gam". Itu sebutan dia, caption tulis "ngam".
- **"cantik … sangat-sangat"**: ada ~1s suara antara "cantik" (17.2–18.1s) yang Whisper gabung dalam "cantik".
  Audio dikekalkan, caption tunjuk "CANTIK" sepanjang tempoh tu.
- **"Material"**: semakan preview pertama dengar "tira" / "sementara", sebab "dia" dan "Material" bercantum
  tanpa ruang. Dah ditambah ~0.25s senyap (tebal tamat 20.26s, waffle mula 22.94s); semakan akhir dengar
  "dia, material jenis waffle" dengan betul.
- **"Senang"**: satu semakan dengar "Kenang"; potongan dialih ke 25.70s (dalam senyap), semakan akhir dengar "Senang".

## Render (HyperFrames)

```
cd comp && npm install && cd ..                      # hyperframes@0.8.181 (dipin dalam comp/package.json)
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell   # pilihan

python3 sfx.py sfx/                                                  # jana semua bunyi (clink, chalk baru)
python3 edit.py proxy.mp4 transcript.json sfx/ out/                  # preview: out/preview.mp4 (720x1280)
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final   # final:   final/final.mp4 (1080x1920)
python3 edit.py proxy.mp4 transcript.json sfx/ out/ --graphics-only  # ubah grafik sahaja, guna semula out/base.mp4
python3 check.py out/ check.jpg                                      # check sheet: zon UI + kepala + kotak tengah

cd cover && npx --prefix ../comp hyperframes snapshot . --at 0.5 --no-end -o snap   # cover -> snap/*.png -> ../cover.jpg
```

**Masa render:** HyperFrames capture untuk 27.7s (~830 frame) lebih kurang **1 min 35 s**; pipeline preview penuh
lebih kurang 2.5–3 minit (4 CPU, tiada GPU).
