# Bantal Avocado (bulat montel): edit plan, preview v1

Source: iPhone IMG_2933, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **39.3s** (luar, tepi pokok bunga)
Preview v1: **29.2s** (dipotong ~10s), 720×1280, 30fps, SDR, −11.3 LUFS
Final: **29.2s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −11.3 LUFS, sudah render
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (ikut avocado) + refresh

| Warna | Hex | Guna |
|---|---|---|
| Hijau daun gelap | `#2F4A1E` | teks label, outline caption, bayang |
| Hijau kulit avocado | `#5C8A2E` | track progress bar, kulit avocado end card, daun |
| Hijau isi avocado | `#C5E25C` | perkataan aktif caption (bounce), label, isi end card, fill progress bar |
| Isi pucat | `#EEF6C8` | label, wash transisi |
| Coklat biji | `#7B4A2C` | badge "biji" label, cincin transisi, biji progress bar & end card |
| Pink pipi | `#F48FA0` | highlight label |
| Butter | `#FFD54F` / `#FFE08A` | TEKAN BEG KUNING, keyword caption |

## Refresh (lain dari batch sebelum & video batch-4 lain)

- **Label "separuh avocado"**: pill hijau pucat/isi + **badge bulat coklat (biji)** di kiri yang pegang emoji; **slide masuk dari kiri** dengan squash kecil, tak senget.
- **Caption bounce**: setiap perkataan diletak berasingan (jarak lebih luas); perkataan aktif **membesar & melantun** (128% → 114%) warna hijau isi avocado.
- **Motif daun**: daun avocado kecil terbang keluar dari label dan jatuh berpusing (SFX `rustle` baru).
- **Transisi "biji"**: cincin coklat meletup dari tengah + wash hijau pucat (SFX `plop` baru), bukan flash/wipe.
- **Progress bar**: track hijau kulit, fill hijau isi, dan **biji coklat kecil bergerak** di depan.
- **End card**: **avocado separuh besar** (kulit + isi + biji 😊) dengan label separuh-avocado bersusun.
- **Cover**: latar **gingham picnic** hijau, gambar jadi **sticker die-cut** (rim putih tebal), daun di tepi, label separuh-avocado + burst coklat "SIZE 30CM!".

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 0.0–8.7 | ⭐ **HOOK** (memang ayat pembuka, dia "petik" avocado dari pokok): "Peminat avocado, korang ada ke avocado yang tuuu... kat sini kita ada avocado? Baru fresh-fresh daripada pokok dia." | `PEMINAT AVOCADO?` 🥑 → `KORANG ADA KE?` 🤔 → cincin biji → `KAT SINI ADA!` 👇 → cincin → `BARU PETIK DARI POKOK!` 🌳 + daun |
| 8.7 | 14.45 | "Ya Allah, dia lah gebu macam ni. Dia tak nipis tau." | `GEBU-NYA!` ☁️ → cincin → `TAK NIPIS TAU` 👌 |
| 11.8 | 17.55 | "Bentuk dia bentuk avocado yang bulat montel macam ni, size 30cm." | `BULAT MONTEL` 🥑 + daun → cincin → `SIZE 30CM` 📏 |
| 16.1 | 23.3 | "Korang boleh buat hadiah, boleh beli untuk bantal peluk baby ke." | `BOLEH BUAT HADIAH` 🎁 → cincin → `BANTAL PELUK BABY` 👶 + daun |
| 20.8 | 28.8 | "Sebab dia lembut dan dia ada zip, korang nak basuh ke apa ke, senang." (tunjuk belakang) | `LEMBUT & ADA ZIP` 🤐 → cincin → `SENANG BASUH` 🫧 |
| 25.6 | 34.3 | "Ni untuk avocado 30cm." (suara bawah end card) | End card avocado separuh: `BANTAL AVOCADO` / `BULAT MONTEL • 30CM` / `TAG KAWAN PEMINAT AVOCADO!` / `TEKAN BEG KUNING` |

Dibuang:
- **Harga (peraturan tiada harga):** "Ok yang ni, ya Allah harga dia, korang mesti terkejut tengok harga dia" (8.7–14.4) dan "Harga jimat," (22.1–23.3).
- "Nah ok," sebelum ayat penutup, dan "tunggu-tunggu, saya ambil ini, okey?" di hujung.
- Jeda / bunyi angin.

Tiada CTA beg kuning dalam suara; `TEKAN BEG KUNING` ada pada end card.

## Belum pasti

- **"tuuu..."** (3.4–4.3s): bunyi panjang/main-main; Whisper tulis "tuuuuut". Caption tulis "tuuu...".
- **"korang (dah) ada ke"**: semakan preview dengar "korang **dah** ada ke"; transkrip penuh tak dengar "dah". Caption tak letak "dah".
- **"montel"**: Whisper dengar "montan" (dibetulkan).
- **"30cm"** pada ayat penutup: satu pass dengar "30M".

## Render

```
python3 sfx.py sfx/                                                    # SFX (tambah plop + rustle)
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_20.4.png cover.png                              # cover 1080x1536
```
