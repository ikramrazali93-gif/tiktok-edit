# Bantal Peluk Durian #3 (gaya pop komik): edit plan, preview v1

Source: IMG_3062, iPhone 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **47.8s**
Preview v1: **39.0s** (dipotong ~9s), 720×1280, 30fps, SDR, −11.3 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 165px, bawah 435px, atas 165px (1080×1920).

Video ketiga daripada siri 5 video bantal durian. Lapisan grafik dibina dengan **HyperFrames** (HTML + CSS +
GSAP), sama macam `projects/bantal-durian`, tapi gayanya lain sama sekali supaya siri ni tak nampak berulang.
Potongan video, suara v2 dan SFX masih guna ffmpeg.

## Gaya: "pop komik"

| Warna | Hex | Guna |
|---|---|---|
| Dakwat hitam | `#141414` | outline tebal, bayang keras semua elemen |
| Kuning komik | `#FFE135` | kotak perkataan aktif, starburst, label "punch", latar slam |
| Merah pop | `#FF3B3B` | perkataan penting dalam label, progress bar, burst "GEBU!" |
| Cyan | `#2EC4F1` | burst "OOPS!" |
| Putih | `#FFFFFF` | belon cakap |

- **Label belon cakap:** belon putih dengan outline dakwat tebal dan bayang keras. Ekornya menunjuk ke bawah
  ke arah bantal (macam bantal yang bercakap). Masuk dengan "pop" (back easing), perkataan muncul satu-satu,
  emoji melompat.
- **Label "punch" kuning:** untuk ayat kuat (STOP!, SANGAT GEBU!, 95CM!), font besar atas belon kuning.
- **Starburst halftone:** untuk "SENYUM NI!" (close-up muka bantal), bintang bergerigi kuning dengan corak titik.
- **Caption:** tulisan komik putih beroutline hitam; perkataan aktif melompat masuk ke kotak kuning berdakwat
  (bertukar senget kiri/kanan), bukan pil yang meluncur macam video pertama.
- **Burst onomatopoeia:** "OOPS!" bila dia sedar muka siapa yang patut ditengok, "GEBU!" di end card.
- **Peralihan "slam":** jalur halftone kuning menyapu skrin + garis laju (speed lines) memancar dari tengah.
- **Progress bar:** jalur merah beroutline hitam, dipindah ke **bawah** (atas zon caption TikTok) supaya jalur
  atas kosong untuk label.
- **End card:** bingkai panel komik hitam, belon tajuk, dua pil (saiz + CTA) yang meluncur masuk, burst "GEBU!".

## Elak tutup muka (user: "kurangkan tutup bahagian muka")

Setiap blok ada kotak kepala (`SUBJECT` dalam `edit.py`, diukur dari key frame bergrid). `place_label()`
kira sendiri ruang yang boleh dipakai dengan margin 40px dari kepala:
- **Jalur atas** (atas hud): tinggi = atas kepala − margin − 172px. Dipakai bila muat satu baris (≥100px).
- **Kolum kiri** (atas bantal / pokok, sebelah kiri kepala): lebar = kiri kepala − margin. Dipakai bila hud dia
  terlalu tinggi (blok "bukan" dan "gebu"). Teks dibalut 2–3 baris dan font mengecil sendiri.
- **Starburst besar** cuma dipakai bila ada ruang untuk gerigi dia; kalau tak, ia jadi label "punch" kuning
  (font besar, belon biasa) supaya gerigi tak kena kepala.
- **Hook (close-up muka penuh):** satu-satunya ruang bukan muka ialah jalur hud di atas cermin mata, jadi label
  STOP dan caption duduk di situ (y≈262), tiada apa-apa atas mata atau purdah.
- **"Eh, bukan, bukan":** muka dia di kanan, bantal di kiri, jadi caption pindah ke kolum kiri atas bantal dan
  burst "OOPS!" di bawahnya.
- `check.py` lukis kotak kepala (cyan) + zon UI TikTok atas 46 frame preview untuk semakan.
- **Tak dapat dielak:** tiada yang kena muka. Caption bawah kadang-kadang lalu atas muka senyum bantal paling
  bawah (hujung bantal panjang tu sampai ke kaki).

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 0.0 | ⭐ **HOOK** (lawak close-up muka): "Stop, stop, stop. Tengok ni. Tengok muka ni. Takkanlah muka ni tak boleh buat korang happy, tersenyum." | `STOP! STOP! STOP!` ✋ (belon kuning) atas hud, caption atas hud |
| 7.1 | 7.4 | "Eh, bukan, bukan! Muka ni, muka ni. Sebelah saya ni." (punchline: muka bantal) | burst `OOPS!`, caption kiri, `MUKA NI!` 👈 |
| 10.6 | audio 14.8, visual 11.0 | J-cut: "Sini ni, senyum ni." atas close-up muka bantal | slam + starburst `SENYUM NI!` 😊 |
| 11.9 | 16.6 | "Kita pun tersenyum tengok dia." | `KITA PUN TERSENYUM` 🥰 |
| 13.9 | 19.3 | "Gebu macam ni, tu ketebalan dia. Ya Allah, ya Rabbi." | `GEBU MACAM NI` ☁️ → `TEBAL!` 💪 → `YA RABBI!` 😍 |
| 16.9 | 23.3 | "Memang tersenyumlah." | `MEMANG TERSENYUM` 😁 |
| 18.6 | 25.0 | "Tengok muka yang comel ni. Ada tiga muka." | `MUKA COMEL` 🥹 → `ADA 3 MUKA!` 😆 |
| 21.3 | 28.2 | "Jangan takut, jangan takut." | `JANGAN TAKUT!` 🙈 |
| 22.3 | 29.3 | "Yang ni, durian yang lembut, yang gebu, yang tebal. Buat peluk, buat teman tiduuur… Ya Allah, sangat-sangat gebu." | slam, `LEMBUT • GEBU • TEBAL` → `TEMAN TIDUR` 😴 → `SANGAT GEBU!` 🤩 |
| 29.0 | 37.6 | "Yang ni saiz paling besar. Saiz 95cm. Panjang, besar macam orang dah." | slam, `SAIZ PALING BESAR` 📏 → `95CM!` 😱 → `BESAR MACAM ORANG!` 😂 |
| 33.0 | 42.6 | "Okey, korang tengok dekat beg kuning, silalah grab sebab memang betul-betul gebu." | `TENGOK BEG KUNING` 🛒 → `SILALAH GRAB!` 🏃‍♀️ → `BETUL-BETUL GEBU` ☁️ |
| 37.3 | 46.9 (visual, slow-mo) | - | End card: panel komik, `BANTAL PELUK DURIAN` 💛, `95 • 75 • 52 • 30 CM`, `TEKAN BEG KUNING`, burst `GEBU!` |

Dibuang: jeda 0.3s sebelum "happy", "Apa close up sampai kita ni. Kita semua close up sini lah" (tak jelas),
"fluffy… sangat peluk" selepas "sangat-sangat gebu" (tak jelas), jeda lain. Tiada sebutan harga dalam video ni.

## Belum pasti

- **"silalah grab"**: Whisper dengar "sila low grab", "lelah ogret", "leluh grek". Caption tulis "silalah grab".
- **"ketebalan"**: Whisper tulis "keterbalan" (dia sebut laju).
- **"durian"**: dia sebut "doyan/doian", caption tulis "durian".
- **Saiz lain:** video ni cuma sebut 95cm. 75/52/30cm pada end card dan cover ikut video durian pertama
  (52cm pun masih belum disahkan).

## Render (HyperFrames)

Keperluan: ffmpeg, Node 18+, Chrome/Chromium (set `HYPERFRAMES_BROWSER_PATH` ke Chrome sedia ada supaya
HyperFrames tak muat turun browser sendiri).

```
cd comp && npm install && cd ..                      # pasang hyperframes@0.8.181 (dipin dalam comp/package.json)
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell

python3 sfx.py sfx/                                                  # SFX sintetik
python3 edit.py proxy.mp4 transcript.json sfx/ out/                  # preview: out/preview.mp4 (720x1280)
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final   # final:   final/final.mp4 (1080x1920)
python3 edit.py proxy.mp4 transcript.json sfx/ out/ --graphics-only  # ubah grafik sahaja, guna semula out/base.mp4
python3 check.py out/ check.jpg                                      # check sheet: zon UI + kotak kepala

cd cover && npx --prefix ../comp hyperframes snapshot . --at 0.5 --no-end -o snap   # cover -> snap/*.png -> ../cover.jpg
```

**Apa `edit.py` buat:**
1. Potong dan zoom video (keyframe setiap 1s), campur suara v2 dan SFX, jadi `base.mp4`.
2. Tulis `comp/data.js`: caption, label (dengan kedudukan dan kotak muat yang dikira dari kotak kepala), burst,
   slam dan end card. Salin `base.mp4` ke dalam `comp/`.
3. `npx hyperframes render` untuk `comp/index.html` (komposisi sentiasa 1080×1920, `base.mp4` lapisan video senyap).
4. Gabung video HyperFrames dengan audio `base.mp4`. Untuk preview, video dikecilkan ke 720×1280.

**Masa render:** di container ni (4 CPU, tiada GPU, beginframe capture, 3 worker), HyperFrames render 39.0s
(1,172 frame) dalam lebih kurang **3 min 4 s**. Keseluruhan pipeline preview (potong video, audio, render, mux)
ambil lebih kurang **4 min 40 s**. `--graphics-only` jimat lebih kurang 1 minit.
