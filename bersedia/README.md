# Bersedia — animasi hitam putih (Bahasa Melayu)

*"Kau takkan pernah rasa bersedia. Sebab bersedia bukan perasaan, ia satu keputusan."*

Konsep diambil daripada reel motivasi Jackkgriffith. Skrip ditulis semula dalam Bahasa Melayu
dan bahagian iklan aplikasi dibuang. Semua animasi dilukis dengan kod.

**Video siap:** [`output/bersedia.mp4`](output/bersedia.mp4) (1080×1920, 30fps, ~50 saat)

## Gaya
- Hitam putih sepenuhnya, latar hitam, garis neon putih yang "melukis sendiri"
- Peralihan babak berbentuk gelombang yang mengalir, dan partikel mengalir sepanjang video
- Tipografi kinetik: kata kunci besar (HURUF BESAR, bergaris bawah), perkataan muncul ikut suara
- Gegaran skrin + hentakan bunyi pada saat penting (BERSEDIA, KEPUTUSAN, DATANG, PERGI)
- Muzik naik berperingkat, dengan kesan bunyi detik jam, kaca pecah, jam loceng dan riser
- Penutup: bunga mekar + "MULA HARI INI."

## Babak
| # | Ayat | Animasi |
|---|---|---|
| 1 | Kau takkan pernah rasa bersedia | Watak di tebing memandang matahari |
| 2 | Bersedia bukan perasaan, ia satu keputusan | Hati dipangkah, kemudian bertukar jadi anak panah |
| 3 | Semua orang tunggu saat yang sempurna | Orang duduk menunggu, jam berputar laju |
| 4 | Saat itu takkan datang | Jam retak dan pecah berderai |
| 5 | Bukan untuk kerja / perbualan / perjalanan | Ikon beg kerja, buih chat, kapal terbang |
| 6 | Rasa gementar takkan hilang… | Contengan gelisah di kepala, kemudian melangkah |
| 7 | Rasa bersedia akan menyusul | Bebola cahaya mengejar dan menyatu dengan watak |
| 8 | …walaupun semuanya suruh kau tunggu | Berjalan melawan "angin" perkataan TUNGGU, NANTI… |
| 9 | Orang berani pun bukannya tak takut | Di puncak gunung, zoom ke jantung berdegup + ECG |
| 10 | Kau takkan bangun esok pagi… bersedia | Bilik tidur, jam loceng berbunyi |
| 11 | Kau cuma perlu… pergi | Pintu terbuka, watak berlari ke cahaya, bunga mekar |

## Cara jana semula
Perlukan modul daripada `../karung-beras` (lukisan, suara, muzik).
```bash
python3 suara.py   # narasi + masa perkataan -> build/
python3 muzik.py   # muzik + kesan bunyi + campuran -> build/audio.wav
python3 video.py   # render -> output/bersedia.mp4
```
Pratonton: `python3 video.py --sheet` atau `python3 video.py --still 12.5`.
Ayat boleh diubah dalam `skrip.json` (medan `jeda` pilihan = senyap selepas baris itu).
