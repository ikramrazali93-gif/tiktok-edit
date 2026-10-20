# Bantal Kucing Bambam (75cm, putih + tompok calico): edit plan, preview v1

Source: iPhone IMG_2941, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **40.2s**
Preview v1: **21.8s** (dipotong ~18s), 720×1280, 30fps, SDR, −11.4 LUFS
Final: **21.8s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −11.5 LUFS, sudah render
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 110px, bawah 290px, atas 110px (720×1280).

## Gaya (ikut kucing putih calico) + refresh

| Warna | Hex | Guna |
|---|---|---|
| Ink lembut | `#3A2E39` | teks & outline tag, outline caption, garis bulu mata (blink), misai |
| Blush (dalam telinga) | `#FFB3CF` | telinga dalam, glow perkataan aktif, tag, progress bar |
| Rose | `#F0609A` | highlight dalam tag, bola benang, hidung end card |
| Biru langit | `#9AD4F5` | tag (kontras atas bulu putih), keyword caption (`#BFE6FF`) |
| Taupe (tompok calico) | `#B8936E` | subtajuk end card |
| Krim | `#FFF6EC` | tag biasa, kelopak mata (blink), kad kepala kucing |
| Mentega | `#FFE27A` | tag COMEL / BANTAL PELUK / TEKAN BEG KUNING |

Refresh (lain dari batch sebelum & semua video batch-4 lain):
- **Label "cat-ear tag"**: tag bulat rata (tak senget), outline ink, **dua telinga kucing** di atas (dalam blush), bayang ink lembut. Masuk gaya **drop-in dari atas + squash** (bukan pop/stamp/slide).
- **Motif misai**: 3 misai ink kecil terbentang di kiri kanan tag.
- **Caption**: perkataan aktif putih dengan **glow blush lembut** (border tebal blur) + membesar 108%; keyword biru langit.
- **Transisi "cat blink"**: dua kelopak mata krim (dengan garis bulu mata ink) tutup dari atas & bawah dan buka semula (0.23s). SFX baru `blink`.
- **SFX baru** `squeak` (bunyi "miau" anak patung) pada hook & "lembut & bambam".
- **Progress bar benang**: garis blush dengan **bola benang rose** bergolek di hujung.
- **End card**: **kad kepala kucing** krim besar (telinga, mata ^ ^, hidung pink, misai) + "BANTAL KUCING / 75CM • BAMBAM • FLUFFY" + tag "KORANG TEAM KUCING?" & "TEKAN BEG KUNING".
- **Cover**: latar **checkerboard blush/krim**, foto dalam **bingkai kepala kucing** (bertelinga), tajuk "KUCING BAMBAM!" dengan misai, dua cat-ear tag.

## Susunan

| TL | Masa asal | Ayat | Grafik |
|---|---|---|---|
| 0.0 | audio 3.7 + 5.7, visual 33.9 | ⭐ **HOOK** (J-cut atas close-up muka kucing di hujung klip): "Bambamnya kucing ni. Comel," | `BAMBAM-NYA KUCING NI!` 😻 (squeak) → `COMEL!` 🥰 (tag di tengah badan, muka kucing tak terlindung) |
| 2.8 | 6.9 | "saiz dia 75cm macam tu." | blink → `SAIZ 75CM` 📏 |
| 5.0 | 9.8 / 13.2 | "Dia punya material bulu-bulu fluffy, lembut, bambam macam ni." (punch-in masa dia usap) | blink → `BULU-BULU FLUFFY` ☁️ → `LEMBUT & BAMBAM` 🤍 |
| 10.0 | 17.9 | "Boleh buat bantal peluk." | blink → `BANTAL PELUK` 🤗 |
| 11.2 | 19.2 | "Boleh buat bantal untuk anak nak baring." | `ANAK NAK BARING` 💤 |
| 13.9 | 21.9 | "Kita pun boleh nak baring ke," | `KITA PUN BOLEH!` 🙌 |
| 15.5 | 23.8 | "atau nak alas belakang dekat dalam kereta ke." | blink → `ALAS BELAKANG / DALAM KERETA` 🚗 |
| 18.4 | 36.7 (visual, tiada suara) | - | blink → kad kepala kucing + `KORANG TEAM KUCING?` 🐱 + `TEKAN BEG KUNING` 🛒 |

Dibuang: "Ah, kucing." (pembukaan lemah), "Okay" sebelum "dia punya", nafas 12.7–13.3, "Gitu awak. Okey, lembutnya." (ulang), "kan" selepas "baring ke", dan **ayat harga** "Harganya sangat-sangat jimat, memang berbaloi. Besar macam ni harga murah, memang heran" (27.1–33.7, peraturan tiada harga). Dia tak sebut CTA beg kuning, jadi CTA hanya di end card.

## Belum pasti

- **"alas belakang dekat dalam kereta"**: Whisper dengar "nak alah belakang dekat dalam reto ke" (dua kali). Maksud paling munasabah: lapik/sandar belakang dalam kereta, jadi caption tulis "alas … kereta".
- **"lembut,"** (13.3s): bila dipotong sendiri Whisper dengar "Boy/Bambui", tapi dengan konteks penuh dengar "lembut". Dah semak, audio tak terpotong (senyap sebelum 13.25).
- **Nama produk**: dia cuma sebut "kucing" & "bambam", jadi label tulis "BANTAL KUCING" / "KUCING BAMBAM".

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
python3 cover.py frame_14.2.png cover.jpg                              # cover 1080x1536
```
