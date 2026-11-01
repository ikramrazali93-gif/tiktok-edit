# Kusyen Duduk #4 (Y2K chrome pop): edit plan, preview v1 (HyperFrames)

Source: IMG_3069, iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **36.1s**
Preview v1: **28.4s** (dipotong ~7.7s), 720×1280, 30fps, SDR, −11.5 LUFS
Final: **28.4s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −11.5 LUFS, sudah render (HyperFrames)
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 165px, bawah 435px, atas 165px (1080×1920).

Video keempat dalam siri kusyen duduk (5 video, produk sama: kusyen petak berbutang, kain waffle, merah & brown).
Pipeline sama dengan `../kusyen-duduk-1`: potongan, suara v2 dan SFX guna ffmpeg, lapisan grafik ialah komposisi
**HyperFrames** (HTML + CSS + GSAP) yang letak setiap grafik sendiri jauh dari muka dia dan luar kotak tengah.

## Peraturan siri: "kurangkan text dan animation bahagian tengah video"

- **Kotak tengah bebas** (x 160–920, y 480–1340; `KEEPOUT` dalam `edit.py`): tiada label, sticker, bintang piksel
  atau peralihan di situ.
- **Label sikit & kecil:** 7 sahaja untuk 28s. Caption bawa yang lain.
- **Dua jalur sahaja:** jalur atas (atas kepala) dan jalur bawah betul-betul atas caption.
  - Tajuk besar chrome cuba satu baris dulu; kalau kepala penuhkan jalur atas, ia jadi satu perkataan sebaris di
    bucu kiri atas. Kalau masih tak muat, ia tukar jadi pil holo kecil di jalur bawah.
  - Pil holo di jalur bawah ("LEBIH SELESA DUDUK", "TEKAN BEG KUNING") tersentuh sikit tepi bawah kotak tengah
    (± 20–30px, atas kot/hujung kusyen), sebab caption duduk betul-betul di bawahnya.
- **Tiada wipe skrin penuh:** peralihan cuma "glint chrome": jalur chrome nipis menyapu tepi atas dan tepi bawah,
  cahaya putih lembut di tepi skrin, bintang piksel di empat bucu. Tengah kekal jernih. 2 kali.
- **End card** kad holo kecil; ia naik ke bucu kiri atas sebab di hujung video dia keluar dari frame.
- `check.py` lukis kotak tengah (hijau), kotak kepala (cyan) dan zon UI TikTok (merah).

## Gaya: "Y2K chrome pop"

| Warna | Hex | Guna |
|---|---|---|
| Chrome | `#FFFFFF` → `#9AA6B4` → `#5E6876` → `#FFFFFF` | huruf tajuk besar, tajuk end card & cover |
| Holo | `#FF8AD8` → `#C9A2FF` → `#8FF3FF` → `#D8FF8A` | badan pil, chip perkataan aktif, bar kemajuan, bingkai cover |
| Ink | `#1B1035` | outline, teks dalam pil |
| Hot pink | `#FF2E9A` | bayang tajuk chrome, kata kunci dalam pil |
| Lime | `#C6FF4A` | kata kunci caption, bahagian `<b>` tajuk chrome |
| Kuning CTA | `#F6E84A` | butang "TEKAN BEG KUNING" |

- **Tajuk besar (2):** huruf chrome berkilat dengan outline ink dan bayang pink, satu kilauan putih menyapu
  huruf, emoji dalam bulatan holo. Masuk "snap" (skala + skew), terapung perlahan.
- **Label kecil (5):** pil holo dengan rim putih + ink, separuh atas berkilat, emoji dalam bulatan mutiara.
  Gradien holo bergerak perlahan sepanjang paparan.
- **Bintang piksel:** 2–4 bintang 8-bit berkelip di tepi label (luar kotak tengah, luar kepala).
- **Caption:** huruf putih outline ink, kata kunci lime. Perkataan aktif duduk atas chip holo.
- **Bar kemajuan:** trek chrome di atas, isi holo, bintang piksel pink berpusing.
- **End card:** kad holo kecil: "KUSYEN DUDUK" (chrome) / "40×40 CM • MERAH • BROWN" / CTA kuning.
- **SFX baru:** `blip` (8-bit, pil masuk), `glint` (kilauan chrome, peralihan), `pix` (arpeggio piksel, tajuk besar).
- **Cover:** bingkai holo dengan bintang piksel di bucu, tajuk chrome dua baris "KERUSI MAKAN / NAMPAK KOSONG?" di
  langit atas hud, lencana holo bulat "✨ NAK RAYA!" di celah kiri kepala, pil holo "KUSYEN DUDUK 40×40 • MERAH •
  BROWN" di bawah. Tiada apa atas muka atau atas dua kusyen.

## Muka tak ditutup

- Kotak kepala + hud ditanda setiap 1 saat daripada frame proxy bergrid (`HEADS`). Close-up tekstur 29–30s tiada
  kepala; 13–14s kusyen beige diangkat depan dia (kotak dikekalkan).
- Setiap caption, label dan end card dapat semua kotak kepala dalam tempoh paparan (±0.5s, zoom dikira) dan duduk
  sekurang-kurangnya 44px jauh. Check sheet (21 frame): tiada grafik atas muka/hud.
- Hook: tajuk chrome satu baris (52px) muat di jalur langit atas kepala. "NAIK SERI!": kepala penuhkan jalur atas
  (zoom 1.12), jadi ia sebaris-sebaris kecil di bucu kiri atas.

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 0.28 | ⭐ **HOOK**: "Kerusi meja makan korang nampak kosong, nak raya ni nanti, nampak kosong, tak cantik lah kan." ("tak" tersasul + jeda 4.74–5.28 dibuang, ditutup tukar zoom) | chrome `KERUSI NAMPAK KOSONG?` 🪑 → pil `NAK RAYA NI!` ✨ |
| 6.1 | 6.88 | "Nanti tamu mai, korang nak lebih selesa di kerusi tu, letaklah ni." | pil `LEBIH SELESA DUDUK` 💺 |
| 10.7 | 13.18 | "Cushion ni lebih selesa duduk dan tak nampak kosong sangat, naik seri kan!" | glint → chrome `NAIK SERI!` 💖 |
| 16.6 | 24.50 | "Ada macam-macam warna, merah macam ni pun lawa. Warna brown pun lawa." | glint → pil `MERAH • BROWN` 🎨 |
| 20.9 | 28.78 | "Saiz dia 40cm × 40cm." (close-up tekstur) | pil `40 × 40 CM` 📏 |
| 23.6 | 32.17 | CTA: "Korang boleh tengok dekat bawah sekarang." | pil `TEKAN BEG KUNING` 🛒 |
| 26.5 | 35.02 | (slow-mo ×0.5) | end card holo |

**Dibuang:**
- **Harga:** "Dan yang penting harga dia murah je" (19.4–23.2s), ikut peraturan tiada harga.
- "Apa tu, panggil apa?" (12.3–13.2s, tersasul cari perkataan)
- "Nah, tu dia tu dia tu dia" (23.2–24.5s)
- "tak" tersasul + jeda (4.74–5.28s)
- bunyi tak jelas selepas "letaklah ni" (11.9–12.2s)
- "Ok" sebelum CTA (31.6–32.2s)

## Belum pasti

- **"tamu mai":** loghat utara untuk "tetamu datang"; Whisper tulis "tamu main". Caption tulis "tamu mai".
- **"Saiz dia":** satu pass dengar "sahaja" / "saya ada", semakan preview dengar "Saat dia". Saiz 40×40cm jelas.
- **"brown":** pass penuh dengar "beram", per-chunk dengar "brown". Kusyen tu warna beige/coklat muda; label dan
  caption tulis "BROWN" ikut sebutan dia.
- **"tengok dekat bawah":** Whisper dengar "dengar" / "tonton"; semakan preview dengar "tengok".
- **"lawa":** Whisper tulis "laur" sekali.

## Semakan

- Preview ditranskrip semula: "Kerusi meja makan korang nampak kosong, nak raya ni nanti nampak kosong tak cantik
  lah kan / Nanti tamu main, korang nak lebih selesa di kerusi tu letaklah ni cushion ni / Lebih selesa duduk dan
  tak nampak kosong sangat, naik seri kan / Ada macam-macam color, warna merah macam ni pun lawa, warna brown pun
  lawa / Saat dia 40cm kali 40cm / Korang boleh tengok dekat bawah sekarang". Tiada perkataan terpotong.
- Render pertama: tajuk hook chrome tak muat atas kepala (kepala tinggi) dan jatuh ke bawah atas caption. Dibaiki
  dengan pilihan satu baris 58/52px (padding kecil), mod "satu perkataan sebaris" untuk kolum sempit, dan fallback
  ke pil holo.

## Render (HyperFrames)

```
cd comp && npm install && cd ..                      # hyperframes@0.8.181 (dipin dalam comp/package.json)
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell   # pilihan

python3 sfx.py sfx/                                                  # jana semua bunyi (blip, glint, pix baru)
python3 edit.py proxy.mp4 transcript.json sfx/ out/                  # preview: out/preview.mp4 (720x1280)
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final   # final:   final/final.mp4 (1080x1920)
python3 edit.py proxy.mp4 transcript.json sfx/ out/ --graphics-only  # ubah grafik sahaja, guna semula out/base.mp4
python3 check.py out/ check.jpg                                      # check sheet: zon UI + kepala + kotak tengah

cd cover && npx --prefix ../comp hyperframes snapshot . --at 0.5 --no-end -o snap   # cover -> snap/*.png -> ../cover.jpg
```

**Masa render:** HyperFrames capture untuk 28.4s (~853 frame) lebih kurang **1 min 47 s – 2 min 38 s**; pipeline
preview penuh lebih kurang 4.5 minit (4 CPU, tiada GPU, CPU dikongsi dengan fork lain).
