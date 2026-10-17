# Bersedia — animasi hitam putih (Bahasa Melayu)

*"Kau takkan pernah rasa bersedia. Sebab bersedia bukan perasaan, ia satu keputusan."*

Konsep diambil daripada reel motivasi Jackkgriffith. Skrip ditulis semula dalam Bahasa Melayu
dan bahagian iklan aplikasi dibuang. Semua animasi dilukis dengan kod.

**Video siap:** [`output/bersedia.mp4`](output/bersedia.mp4) (1080×1920, 30fps, ~54 saat)

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
| 4 | Tapi... rasa itu takkan datang sendiri | Jam retak dan pecah berderai |
| 5 | Tengah bekerja, berbual, atau berlari… | Ikon beg kerja, buih chat, orang berlari |
| 6 | Rasa gementar takkan hilang… | Contengan gelisah di kepala, kemudian melangkah |
| 7 | Rasa bersedia akan menyusul | Bebola cahaya mengejar dan menyatu dengan watak |
| 8 | …walaupun semuanya suruh kau tunggu | Berjalan melawan "angin" perkataan TUNGGU, NANTI… |
| 9 | Orang berani pun bukannya tak takut | Di puncak gunung, zoom ke jantung berdegup + ECG |
| 10 | Kau takkan bangun esok pagi… bersedia | Bilik tidur, jam loceng berbunyi |
| 11 | Kau cuma perlu… buat keputusan | Pintu terbuka, watak berlari ke cahaya, bunga mekar |

## Suara
Narator: suara lelaki matang dan tenang, gaya orang tua yang bijaksana. Dijana dengan model
[mesolitica/Malaysian-TTS-0.6B-v1](https://huggingface.co/mesolitica/Malaysian-TTS-0.6B-v1)
(penutur `husein`), kemudian diproses supaya lebih perlahan, nadanya lebih rendah, dan
bunyinya lebih hangat. Setiap ayat dijana beberapa kali, dan cubaan yang paling tepat dipilih
secara automatik dengan Whisper. 
`suara.py` (Google TTS, suara perempuan) masih ada sebagai pilihan yang lebih pantas.

## Cara jana semula
Perlukan modul daripada `../karung-beras` (lukisan, suara, muzik).
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install transformers soundfile librosa einops vector-quantize-pytorch matplotlib wandb tensorboard \
    git+https://github.com/mesolitica/DistilCodec
python3 suara_lelaki.py   # narasi lelaki + masa perkataan -> build/ (~15 minit di CPU)
python3 muzik.py   # muzik + kesan bunyi + campuran -> build/audio.wav
python3 video.py   # render -> output/bersedia.mp4
```
Pratonton: `python3 video.py --sheet` atau `python3 video.py --still 12.5`.
Ayat boleh diubah dalam `skrip.json` (medan `jeda` pilihan = senyap selepas baris itu).
