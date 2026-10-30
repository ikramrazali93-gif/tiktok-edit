# Beg Bantal Selimut 3 in 1 (Hutan Malam): edit plan, preview v1 (HyperFrames)

Source: IMG_3184, iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **99.8s**
Preview v1: **47.9s** (dipotong ~52s), 720×1280, 30fps, SDR, −11.1 LUFS
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 165px, bawah 435px, atas 165px (1080×1920).

Produk: beg segi empat berbulu (muka burung/burung hantu comel, tali kuning) yang **simpan selimut di dalam**,
beg tu sendiri jadi **bantal** (ada kapas), dan ada **poket tepi untuk tangan** (hand warmer). Dia sebut "3 in 1".
Selimut hijau sage, "size 170cm". Pipeline sama dengan `../bantal-durian-2`: potongan, suara v2 dan SFX guna
ffmpeg, dan lapisan grafik ialah komposisi **HyperFrames** (HTML + CSS + GSAP).

## Gaya: "Hutan malam" (night woodland)

| Warna | Hex | Guna |
|---|---|---|
| Biru malam | `#0B1626` / `#0F2433` | kad lantern, outline teks, tirai malam |
| Hijau hutan | `#16352A` / `#0E2A1B` | kad lantern, siluet daun |
| Amber / lampu | `#F5B94A` / `#FFC861` | bingkai bercahaya, kata kunci, perkataan aktif, kelip-kelip |
| Krim | `#FFF3D6` | teks label dan caption |
| Bulan | `#FFE7A3` | lencana bulan "3 IN 1" / "170 CM", bulan sabit |
| Kayu | `#A06A38` → `#7A4E28` | tag end card, tag kelajuan, tag cover |

- **Label: kad lantern** biru-hijau malam dengan bingkai amber bercahaya, tergantung pada tali dan cincin
  tembaga. Emoji dalam bulatan amber bercahaya, siluet daun di bucu. Kad turun perlahan dan berayun tenang
  (bukan papan kayu jatuh macam durian #2), perkataan naik satu-satu.
- **Lencana bulan purnama** (dengan kawah) untuk "3 IN 1" dan "170 CM", timbul perlahan dan terapung.
- **Kelip-kelip (fireflies)** terbang dan berkelip di sekeliling setiap label, lencana dan end card. Kelip-kelip
  yang laluannya kena kotak kepala dia dibuang.
- **Caption:** huruf krim dengan outline biru malam. Perkataan aktif jadi amber bercahaya, naik sedikit, dengan
  seekor kelip-kelip di atasnya. Kata kunci hijau pucat.
- **Peralihan "tirai malam":** langit biru malam berbintang dengan bulan sabit dan daun turun satu skrin
  (2 kali: sebelum "kita buka" dan sebelum selimut ditarik keluar).
- **Bar kemajuan:** benang amber dengan kelip-kelip di hujung.
- **End card:** dahan berdaun dengan bulan, tiga tag kayu tergantung (tajuk, "3 IN 1 • 170CM • POKET TANGAN",
  CTA amber).
- **SFX baru:** `hoot` (burung hantu "huu-huu" lembut), `chime` (loceng angin malam), `firefly` (kelip halus).
- **Cover:** bingkai biru malam dengan garisan amber, siluet daun di bucu bawah, kad lantern tajuk, lencana bulan
  "3 IN 1", tag kayu bawah, kelip-kelip.

## Muka tak ditutup

- Kotak kepala + hud ditanda **setiap 1 saat** daripada frame bergrid (`HEADS` dalam `edit.py`), dan muka
  burung pada beg (`FACES`).
- Setiap caption, label, lencana, tag kelajuan dan end card dapat semua kotak kepala dalam tempoh paparannya.
  Komposisi cari tempat paling dekat dengan kedudukan pilihan (label bawah kepala, caption bawah) yang
  **kekal 44px jauh dari kotak kepala**, termasuk tali dan cincin di atas kad lantern dan kelip-kelip di atas
  perkataan aktif. Label elak muka burung beg bila boleh; caption kekal di bawah walaupun atas beg.
- Kepala dia penuhi jalur atas frame (rakaman dekat), jadi label kebanyakannya duduk di tengah (atas badan/beg).
  Label panjang dibalut jadi 2–3 baris.
- `check.py` (kotak kepala cyan, muka beg oren, zon UI merah) atas 49 frame: tiada grafik kena kotak kepala
  dia atau zon UI TikTok. Tirai malam memang tutup satu skrin sekejap (~0.8s), ini dibenarkan.

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio 6.78 + 10.92, visual 88.9 + 65.4 | ⭐ **HOOK** (J-cut atas beg dipegang depan, kemudian selimut terbentang + beg): "Yang ini bag boleh jadi selimut dan juga bantal. 3 in 1. Sebab dia ada lubang untuk masukkan tangan juga." | `BEG JADI SELIMUT` 🦉 → `& BANTAL!` ☁️ → bulan `3 IN 1` → `ADA POKET TANGAN` 🧤 |
| 8.1 | 16.10 | (tirai malam) "…kita buka." | `JOM BUKA!` 🎁 |
| 9.1 | 17.06–24.70 | keluarkan dari bungkusan (×4) | tag `>> x4` |
| 11.0 | 24.74 | "Tadaa!" | `TADAA!` ✨ |
| 12.0 | 28.44 | "Ya Allah, comel. Yang ini kan, dia boleh masukkan tangan sebab dia ada pocket kat tepi ni." | `YA ALLAH, COMEL!` 🥹 → `POKET HAND WARMER` 🙌 |
| 17.1 | 34.02 | "Kalau kita sejuk-sejuk dekat ofis ke ataupun dalam bas ke," | `SEJUK DI OFIS?` 🏢 → `DALAM BAS?` 🚌 |
| 20.9 | 40.20 | "Dua-dua tangan boleh masuk." | `DUA-DUA TANGAN MASUK` 🙌 |
| 22.2 | 41.78 | "Dan bantal ni, dalam dia, bag dia ada selimut." | `SELIMUT DALAM BEG` 👜 |
| 26.0 | 48.47 | "Bantal dia pun tak kosong, ada kapas. Jadi sambil kita selimut, kita boleh guna bantal dia." | `BANTAL ADA KAPAS` ☁️ → `SELIMUT + BANTAL` 😴 |
| 30.1 | 53.00–56.00 | (tirai malam) tarik selimut keluar (×2) | - |
| 31.6 | 56.07 | "Selimut dia pun besar panjang. Size memang ngam untuk seorang guna. Size 170cm." | `BESAR & PANJANG` 📏 → `NGAM UNTUK SEORANG` 🛌 → bulan `170 CM` |
| 37.3 | 79.90 | "Okey kan senang bawa travel. Habis guna, simpan balik, tutup balik zip dia." | `SENANG TRAVEL` 🧳 → `SIMPAN BALIK, ZIP!` 👌 |
| 41.8 | 84.86 | CTA: "Comel sangat. Ada macam-macam kaler boleh tengok. Tengok dekat bawah sekarang." | `MACAM-MACAM KALER` 🎨 → `TEKAN BEG KUNING` 👇 |
| 45.8 | 97.60 | - (suara dimute) | End card: `BEG BANTAL SELIMUT 🦉` / `🌙 3 IN 1 • 170CM • POKET TANGAN` / `🛒 TEKAN BEG KUNING` |

**Dibuang:**
- "Tidak mengapa" dan "Banyak betul bantal selimut baru ya hari ini" (pembukaan perlahan)
- "Okey tengoklah", "Okey ini selimut dia macam itu", "Okey dua dalam satu", "Gitu"
- "sejuk boleh masukkan tangan dekat pocket tepi ni" (ulang)
- "Bag ni simpan selimut dalam bag ni balik. Bag ni boleh jadi bantal lah. 3 in 1 sebab dia ada pocket…" (ulang hook)
- "Hand warmer juga dah habis guna. Masuk dalam ni baliklah" (kurang jelas, diganti visual simpan balik)
- "Dah, jom. Nak … bas lah rombongan …" (tak jelas)
- **"Okey kan tengok harga dia pun. Harga tengok promo."** (peraturan tiada harga; suara dimute bawah end card)
- kebanyakan unboxing (×4) dan tarik selimut (×2), jeda-jeda

## Belum pasti

- **"Sekarang kita buka":** pass penuh dengar "Sebentar", pass potongan dengar "Sekarang", semakan preview dengar
  "kat sana". Caption cuma tulis "KITA BUKA".
- **"Okey kan senang bawa travel":** semakan preview dengar "Dia kan senang buat travel". Caption mula dari "KAN".
- **"Ya Allah, comel":** semakan preview dengar "Ia sangat comel".
- **"3 in 1":** bunyi "three" dengar sebelum Whisper tanda "3". Audio tak terpotong.
- **"ngam":** Whisper tulis "enak"/"ngam elok". Caption tulis "ngam".
- Whisper tulis "bantai" untuk "bantal" sepanjang video; caption betulkan jadi "bantal".

## Render (HyperFrames)

```
cd comp && npm install && cd ..                      # hyperframes@0.8.181 (dipin dalam comp/package.json)
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell   # pilihan

python3 edit.py proxy.mp4 transcript.json sfx/ out/                  # preview: out/preview.mp4 (720x1280)
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final   # final:   final/final.mp4 (1080x1920)
python3 edit.py proxy.mp4 transcript.json sfx/ out/ --graphics-only  # ubah grafik sahaja, guna semula out/base.mp4
python3 check.py out/ check.jpg                                      # check sheet: zon UI + kotak kepala + muka beg

cd cover && npx --prefix ../comp hyperframes snapshot . --at 0.5 --no-end -o snap   # cover -> snap/*.png -> ../cover.jpg
```

`sfx.py` menjana semua bunyi (`python3 sfx.py <dir>`), termasuk `hoot`, `chime` dan `firefly` baru.
`cover/frame.jpg` ialah frame 63.0s daripada `master1080.mp4`.

**Masa render:** di container ni (4 CPU dikongsi dengan render lain, tiada GPU), render HyperFrames untuk 47.9s
(1,437 frame) ambil lebih kurang **4–6 min**. Keseluruhan pipeline preview lebih kurang 6 minit.
