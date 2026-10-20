# Bantal Peluk Terung & Pisang (90cm): edit plan, preview v1

Source: iPhone IMG_2936, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **41.6s** (dalam rumah, depan rak plushie)
Preview v1: **35.9s** (dipotong ~6s), 720×1280, 30fps, SDR, −11.3 LUFS
Final: **35.9s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −11.3 LUFS, sudah render
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (ikut terung + pisang)

| Warna | Hex | Guna |
|---|---|---|
| Plum gelap | `#2E1A4F` | teks badge, outline caption, bayang keras badge, track progress bar |
| Ungu terung | `#7B4FD6` | perkataan aktif caption, highlight badge, jalur badge, segitiga wipe, kad TERUNG |
| Lilac | `#C9B5FF` | badge "purple" |
| Kuning pisang | `#FFE14D` | bayang 3D perkataan aktif, badge, fill progress bar, segitiga wipe, kad PISANG |
| Butter | `#FFF2A8` / `#FFE98A` | badge, keyword caption |
| Hijau tangkai | `#3FAE49` | highlight kedua (PISANG dalam "TERUNG & PISANG") |
| Pink pipi | `#FF8FB1` | hati end card, heart burst cover |

## Refresh (lain dari batch sebelum & video batch-4 lain)

- **Label = badge senget (parallelogram)** condong ke kanan, bayang plum keras (offset), jalur warna di tepi depan, emoji jadi sticker di bucu atas kanan. Masuk gaya **"stamp"** (besar + lutsinar → mendap), bunyi `stamp` baru.
- **Caption**: perkataan aktif **ungu dengan rim putih + bayang 3D kuning keras**, naik 6px bila menyala.
- **Transisi "duo wipe"**: segitiga kuning masuk dari atas-kiri, segitiga ungu dari bawah-kanan, bertemu di pepenjuru dan pudar (0.3s).
- **Motif**: hati kecil kuning & ungu terapung naik dari badge pada poin penting.
- **SFX baru**: `stamp` (cop getah) dan `duo` (chime dua nada).
- **End card**: dua **kad duo** senget sebelah-menyebelah (PISANG kuning / TERUNG ungu) dengan hati pink di tengah, badge "KORANG TEAM MANA?" + "TEKAN BEG KUNING".
- **Cover**: latar **kuning/ungu dipisah zigzag** dengan hati kecil putih, foto dalam bingkai putih bulat, tajuk dua warna, badge senget + heart burst "TEAM MANA?".

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio 10.5, visual 16.8 (close-up terung) | ⭐ **HOOK** (J-cut): "Jarang-jarang kita jumpa desain yang terung macam ni kan." | `JARANG-JARANG JUMPA!` 👀 → `DESAIN TERUNG MACAM NI!` 🍆 |
| 2.2 | 0.6 | "Cantiknya terung dengan pisang ni. Unik kan desain dia, dah lah panjang." | duo wipe + `TERUNG & PISANG` 💜 + hati → `UNIK DESAIN!` ✨ → `DAH LAH PANJANG` 📏 |
| 7.7 | 6.4 | "90cm." | `90CM!` 🙌 |
| 8.9 | 7.9 | "Buat bantal peluk, best ni kan." | `BUAT BANTAL PELUK` 🤗 → `BEST NI!` 😍 |
| 11.2 | 13.1 | "Yang mana pun minat purple, korang ambillah terung yang comel doh ni." | duo wipe + `MINAT PURPLE?` 💜 → `AMBIL TERUNG COMEL!` 🍆 |
| 15.5 | 17.7 | "Kalau minat warna kuning ambil pisang, saiz dia sama 90cm." | `MINAT KUNING?` 💛 → `AMBIL PISANG!` 🍌 → `SAIZ SAMA 90CM` 📏 |
| 20.7 | 23.3 | "Nak buat hadiah pun sangat-sangat sesuai." | duo wipe + `SESUAI HADIAH!` 🎁 |
| 23.0 | 26.9 | "Ni siapa nak letak dekat bilik tidur ke ataupun nak letak dalam kereta, boleh juga tapi besar sikit pula dalam kereta tu. Tak apa letak kat bilik dekat katil." | `HIASAN BILIK TIDUR` 🛏️ → `ATAU DALAM KERETA` 🚗 → `TAPI BESAR SIKIT` 😅 → `LETAK ATAS KATIL` 🛌 |
| 31.7 | 36.9 | "Ada ni kita boleh peluk sambil tidur." | duo wipe + `PELUK SAMBIL TIDUR` 😴 |
| 33.9 | 39.6 (audio) / 22.9 (visual, slow-mo) | "...dekat beg kuning." | End card: `BANTAL PELUK 90CM` / kad PISANG & TERUNG / `KORANG TEAM MANA?` / `TEKAN BEG KUNING` |

Dibuang: "Ha," dan "Okey" (×3) sebelum ayat, jeda nafas selepas "90cm", "paling sesak/sedap" selepas "katil" (tak jelas), bahagian akhir dia turunkan bantal. Tiada sebut harga dalam video ni.

## Belum pasti

- **"Jarang-jarang"** (hook): dalam konteks penuh Whisper dengar "jarang-jarang", tapi bila dipotong jadi hook dia dengar "jangan-jangan" (bunyi "r" lembut). Audio tak terpotong (mula dalam senyap).
- **"comel doh ni"**: "doh" slang; caption ikut bunyi.
- **"Okey, gerai dekat beg kuning"**: perkataan sebelum "dekat" tak jelas (mungkin "tengok"), jadi caption cuma tulis "Dekat beg kuning".
- **"paling sesak"** selepas "katil": mungkin "paling sedap"; dipotong.

## Render

```
python3 sfx.py sfx/                                                     # SFX (tambah stamp, duo)
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_9.0.png cover.jpg                               # cover 1080x1536
```
