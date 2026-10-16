# GoSmell Natural Based Deodorant: edit plan, preview v1

Source: iPhone, 1080×1920 portrait, HEVC HDR (HLG), 59.94fps, **93.1s**
Preview v1: **63.8s** (dipotong ~29s), 720×1280, 30fps, SDR
Final: **63.8s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −12.3 LUFS, sudah render

## Palet warna (ikut produk + video)

| Warna | Hex | Guna |
|---|---|---|
| Oren GoSmell (jalur Lust Lime) | `#FF7A1F` | perkataan aktif caption, highlight label, progress bar, chip Lust Lime |
| Teal (jalur Moon Melon) | `#1FC6D6` | keyword caption, label "positif" (SPRAY JE, NO PROBLEM, SECURE, 90ML), chip Moon Melon |
| Krim (label botol) | `#FFF3D1` | kotak label utama, flash masa reveal |
| Ungu gelap (tudung) | `#2A0E52` | outline caption, teks label, overlay end card |
| Violet | `#6C2BD9` | label "masalah" (BAU MASAM?!, BERPELUH?, SEBAB APA?, = BAU!) |

Logiknya, warna ungu/violet untuk **masalah**, teal untuk **penyelesaian**, dan oren untuk **brand**.

## Potongan

| Masa asal | Ayat | Status |
|---|---|---|
| 0.0–1.7 | Baru balik jogging ni, | ❌ "jogging" disebut 2× |
| 1.8–6.2 | Biasa kalau kita balik jogging, mesti ketiak kita bau masam lah kan | ⭐ **HOOK** (pain point), punch-in 1.22× pada "bau masam" |
| 6.3–10.3 | Tapi *(jeda 0.7s dibuang)* guna GoSmell ni, smell pun go! | ⭐ reveal: flash + impact |
| 10.5–13.2 | dia go, pergi, okay | ❌ ulang |
| 13.3–19.5 | Sebelum jogging ataupun lepas mandi hampa spray je, senang. Baru tu hampa nak jogging ke, hampa nak… | ✅ |
| 19.5–24.7 | …apa tu? *(cari perkataan ±5s)* | ❌ |
| 24.7–27.5 | berpeluh-peluhan ke, no problem | ✅ (jeda dibuang) |
| 27.5–31.0 | *(senyap)* Dia punya, setiap kali dia | ❌ |
| 31.0–35.5 | senang je hampa buka, spray *(shot kabus spray)*, ada macam-macam jenis bau-bauan | ✅ + SFX spray |
| 36.1–48.6 | Sebab apa? Dia orang kata membasmi kuman… peluh campur kuman baru ada bau… kuman kurang, bau kurang | ✅ (jeda 0.6s dibuang) |
| 49.6–61.3 | InsyaAllah bau kurang. Spray la GoSmell… dah beli satu nak beli lagi. Sangat-sangat function | ✅ |
| 61.7–66.9 | Tengok packaging dia elok, packaging dia secure | ✅ (jeda dibuang) |
| 66.9–72.2 | *(keluarkan botol)* ini lime, just lime | ⏩ ×2.5, sebab ayat ni diulang lepas ni |
| 72.2–76.9 | Yang ni saya beli Moon Melon dan satu lagi Lust Lime | ✅ |
| 76.9–84.3 | Eh less lime, just lime, sebut ikut mana… bolehlah, nak lagi? senang | ❌ awkward (keliru sebutan) |
| 84.3–89.8 | Bawa pergi travel ke, senang. Botol dia ni 90ml | ✅ |
| 89.8–90.5 | harga mu…? | ❌ tak jelas, aku tak nak letak caption yang salah |
| 90.0–92.1 | *(pegang 2 botol)* | end card |

## Grafik & SFX

| TL | Grafik | SFX |
|---|---|---|
| 0.0 | `LEPAS JOGGING...` 🏃 | whoosh |
| 2.0 | `KETIAK...` | click |
| 2.7 | `BAU MASAM?!` (violet) 🤢💦 | bloop |
| 5.0 | flash krim + `GUNA GOSMELL` 🧴✨ | impact + sparkle |
| 6.7 | `SMELL PUN GO!` (teal) 💨 | whoosh |
| 8.0–10.7 | `SEBELUM JOGGING` → `LEPAS MANDI` 🚿 → `SPRAY JE!` | pop ×2, spray |
| 14.1 / 15.8 | `BERPELUH?` 💦 → `NO PROBLEM!` ✅ | pop, ding |
| 17.8 | 💨 atas kabus spray | click (buka), spray |
| 21.4–32.8 | `SEBAB APA?` 🤔 → `MEMBASMI KUMAN` 🦠🚫 → `PELUH` + `KUMAN` `= BAU!` → `KUMAN KURANG` → `BAU PUN KURANG` ✅ | pop, bloop, ding |
| 34.6 | `INSYAALLAH BAU KURANG` ✨ | pop |
| 37.7–44.2 | `SPRAY GOSMELL` → `BELI 1, NAK BELI LAGI!` 🛒 → `SANGAT FUNCTION` 💯 | spray, pop, ding |
| 45.2 / 47.4 | `PACKAGING ELOK` 📦 → `SECURE` 🔒 | pop ×2 |
| 49.3 | speed ×2.5 | swish, pop |
| 51.4–56.1 | `NATURAL BASED DEODORANT` + chip teal `MOON MELON` 🍈 + chip oren `LUST LIME` 🍋 | whoosh, pop ×2 |
| 57.6 / 59.4 | `BAWA TRAVEL SENANG` ✈️ → `90ML` 🧴 | pop, click |
| 61.7 | End card: `MOON MELON` atau `LUST LIME`, `KOMEN PILIHAN KORANG!`, `TEKAN BEG KUNING` | whoosh, pop ×2, ka-ching |

Suara guna rantaian v2 (EQ kejelasan + −11.5 LUFS) terus dari awal.

## Render

```
python3 edit.py proxy.mp4 transcript.json sfx/ out/                    # preview 720p
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final     # final 1080x1920
```
