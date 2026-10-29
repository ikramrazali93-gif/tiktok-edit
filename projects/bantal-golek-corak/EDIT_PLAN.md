# Bantal Peluk Panjang / bantal golek bercorak (IMG_3178): edit plan, preview v1

Source: iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **94.2s**
Preview v1: **39.6s** (dipotong ~55s), 720×1280, 30fps, SDR, −11.3 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 165px, bawah 435px, atas 165px (1080×1920).

Grafik dibuat dengan **HyperFrames** (HTML + CSS + GSAP, dirender dalam Chrome), sama pipeline macam
`../bantal-durian-2`. Potongan video, suara v2 dan SFX masih guna ffmpeg.

## Gaya: "Crayon taman budak"

| Warna | Hex | Guna |
|---|---|---|
| Dakwat biru gelap | `#2A2A5A` | teks label, outline lukisan tangan, outline caption |
| Kertas | `#FFFDF4` | kertas label, kertas end card |
| Crayon merah | `#E8473B` | bulatan crayon pada perkataan aktif, garisan progress, bulatan "3" |
| Crayon kuning | `#FFD23F` | perkataan aktif caption, nombor "3", jalur CTA |
| Crayon biru / hijau / pink | `#2F7BEA` `#43B649` `#F06AA8` | bayang crayon berlorek label, doodle |

Apa yang baru (berbanding siri durian):
- **Label "kertas koyak":** kertas krim dengan outline dakwat yang goyang macam dilukis tangan (outline "dilukis"
  masa masuk), bayang crayon berlorek warna-warni di belakang, masuk dengan lantunan elastik, perkataan naik satu-satu,
  emoji bergoyang.
- **Caption:** huruf putih tebal dengan outline dakwat; perkataan yang sedang disebut jadi kuning dan **dibulatkan
  dengan crayon merah** (bulatan dilukis masa perkataan disebut).
- **Nombor dibulatkan:** `3 BIJI!` dan `3 = ANAK = 3 BANTAL` dalam bulatan crayon dengan lorek biru + jalur kertas kuning.
- **Letupan `WAAAH!`:** bintang bergerigi kuning dengan bayang lorek merah.
- **Doodle:** bintang, hati, garis berombak dan lingkaran kecil dilukis sendiri di sekeliling label besar.
- **Peralihan "conteng crayon":** tiga calitan crayon tebal (kuning, biru, merah) menutup skrin lalu dipadam.
- **Progress:** garisan crayon merah dilukis sepanjang video dengan 🖍️ di hujungnya.
- **End card:** kertas bertampal pita dengan doodle.
- **Cover:** bingkai crayon tiga warna, tajuk atas kertas di atas hud, bulatan "3 CORAK" atas bantal dino, jalur
  bawah "JANGAN BELI SATU, AMBIL 3!".

## Elak tutup muka

Kotak kepala + hud (hujung telinga hud sampai dagu) ditanda setiap 1 saat dari grid frame (`HEADS` dalam `edit.py`).
Komposisi cari tempat terdekat dalam safe zone yang jauh 44px dari semua kotak kepala dalam tempoh setiap grafik,
dan tak bertindih caption. Label pilihan di tengah (atas bantal), sebab kepala dia selalu di bahagian atas frame.
`check.py` lukis kotak kepala (cyan) + zon UI (merah) atas frame preview: **tiada grafik atas muka/hud**.
Peralihan conteng crayon menutup seluruh skrin ~0.6s (dibenarkan). Ada label yang duduk atas badan bantal golek.

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 73.8 | ⭐ **HOOK** (dipindah ke depan): "Jangan beli satu. Ambil tiga terus macam ni. Anak ada tiga orang, ambil tiga." | `JANGAN BELI SATU!` ✋ → `AMBIL 3 TERUS!` 🙌 → bulatan `3` `ANAK = 3 BANTAL` |
| 4.1 | 78.2 | "Boleh hadiahkan untuk anak. Mesti anak happy." | `HADIAH UNTUK ANAK` 🎁 → `MESTI ANAK HAPPY!` 😆 |
| 6.6 | 7.2 | (conteng crayon) imbas balik unboxing: "Wah, apakah ini?" | `APAKAH INI?` 🤔 |
| 8.0 | 11.2 | "Oh, tiga biji. Wah, tiga biji lah saya pesan." | bulatan `3 BIJI!` → `SAYA PESAN TIGA` 🛍️ |
| 11.3 | 16.0 | "Nampak kan bantal peluk panjang, kan?" | `BANTAL PELUK PANJANG` 📏 |
| 13.3 | 18.0–30.3 | buka plastik (×4) | tag `▶▶ x4` |
| 16.4 | 30.7 | "Wah, comel. Korang tengok ni. Tengok saya beli tiga colour." | `COMEL!` 😍 → `BELI 3 CORAK` 🎨 |
| 22.2 | 37.3 | tarik keluar bantal biru: "Waaah!" | letupan `WAAAH!` ✨ |
| 23.9 | 40.0 | "Ha, ni bantal peluk." | `BANTAL PELUK!` 🤗 |
| 25.8 | 43.7 | "Tepuk-tepuk sikit." | `GEBU, TEPUK-TEPUK` 👏 |
| 27.1 | 55.2 | (conteng crayon) "Wih, yang ni colour pink ni lah." | `YANG PINK NI!` 💗 |
| 28.6 | 60.3 | "Minat lah tiga-tiga kan ni." | `SUKA KETIGA-TIGA` 😍 |
| 30.2 | 62.6 | "Comel. Bantal peluk besar macam ni. Memang sesuai untuk anak-anak kita tu." | `BESAR & PANJANG` 📏 → `SESUAI UNTUK ANAK-ANAK` 🧒 |
| 34.8 | 70.9 | CTA: "Tengok cepat dekat beg kuning." | `TEKAN BEG KUNING` 🛒 |
| 37.0 | 84.7 | - | End card: `BANTAL PELUK PANJANG` / `🦕 DINO • 💙 BIRU • 🌈 PINK` / `🛒 TEKAN BEG KUNING` |

**Dibuang:**
- **Semua ayat harga** (peraturan tiada harga): "Ya Allah, harga ni murah… jimat", "Tengok dia dapat harga berapa
  dekat bawah", "Tapi harga dia tak masuk akal. Hampir.", "Ya Allah, murah." (sebelum hook), "Nah, harga murah…",
  dan hujung klip (masih sebut harga).
- "Okay, unboxing lagi. Bismillah…", "Oh, secure", "Cuba tukar bantal apa ni", "Gini awak", "Okay, gitu", "Wih,
  yang ni" pertama, "Wih, minat lah ni" pertama, "Itu / Ya Allah, yang ni pun comel" (ulang), "Cepat laju-laju,
  ambil tiga" (tak jelas), "wah" masa bergelut dengan plastik, jeda.
- Corak biru tu ada watak kartun: **tak dinamakan** di mana-mana, ditulis "corak biru" sahaja.

## Belum pasti

- **"Minat lah tiga-tiga kan ni":** Whisper dengar "kali ni" / "Mina". Caption tulis "MINAT LAH TIGA-TIGA KAN NI",
  label cuma `SUKA KETIGA-TIGA`.
- **"Boleh hadiahkan untuk anak":** transkrip semula dengar "Haa boleh…" (bunyi kecil sebelum "Boleh"); "happy"
  kadang didengar "head". Caption ikut maksud.
- **"Korang tengok ni":** dia sebut "Kamu tengok ni"; caption tulis "Korang".
- **"tiga colour":** satu pass dengar "tiga warna".

## Render (HyperFrames)

```
cd comp && npm install && cd ..                      # hyperframes@0.8.181 (dipin dalam comp/package.json)
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell   # pilihan

python3 edit.py proxy.mp4 transcript.json sfx/ out/                  # preview: out/preview.mp4 (720x1280)
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final   # final:   final/final.mp4 (1080x1920)
python3 edit.py proxy.mp4 transcript.json sfx/ out/ --graphics-only  # ubah grafik sahaja, guna semula out/base.mp4
python3 check.py out/ check.jpg                                      # check sheet: zon UI + kotak kepala

cd cover && npx --prefix ../comp hyperframes snapshot . --at 0.5 --no-end -o snap   # cover -> snap/*.png -> ../cover.jpg
```

`sfx.py` menjana semua bunyi (`python3 sfx.py <dir>`), termasuk `scribble` (conteng crayon) dan `boing` yang baru.

**Masa render:** di container ni (4 CPU dikongsi dengan render lain, tiada GPU), render HyperFrames untuk 39.6s
(1,187 frame) ambil lebih kurang **2.5–3.5 min**. Keseluruhan pipeline preview lebih kurang 4 minit.
