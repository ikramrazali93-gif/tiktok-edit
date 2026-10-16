# Karung Beras — video reel (Bahasa Melayu)

Kisah teladan tentang sekarung beras yang jatuh dari lori. Burung-burung hanya ambil
secukupnya, tapi seorang lelaki kaut semuanya kerana risaukan hari esok.
*"Kain kafan tiada poket."*

Konsep diambil daripada reel ReCode Mind, tapi skrip ditulis semula dalam Bahasa Melayu dan
semua visual dilukis sendiri dengan kod.

**Video siap:** [`output/karung-beras.mp4`](output/karung-beras.mp4) (1080×1920, 30fps, ~80 saat)

## Gaya
- Lukisan garis putih atas latar hitam; watak utama bercahaya emas (neon)
- Sari kata perkataan demi perkataan, perkataan yang sedang disebut diwarnakan emas
- Suara narator Bahasa Melayu (Google TTS) dan muzik latar piano/pad yang dijana sendiri (bebas hak cipta)
- Kad penutup: *"Ambil secukupnya. Nikmati perjalanan."*

## Cara jana semula
```bash
pip install -r requirements.txt
apt-get install -y ffmpeg fonts-montserrat libegl1
python3 suara.py   # narasi + masa setiap perkataan  -> build/narasi.wav, build/masa.json
python3 muzik.py   # muzik latar + campuran audio    -> build/audio.wav
python3 video.py   # render video                    -> output/karung-beras.mp4
```
Pratonton pantas: `python3 video.py --sheet` (satu bingkai bagi setiap babak) atau
`python3 video.py --still 12.5`.

Untuk tukar ayat, edit `skrip.json` (setiap baris = satu babak) dan jalankan semula ketiga-tiga skrip.

## Fail
| Fail | Fungsi |
|---|---|
| `skrip.json` | Skrip narasi, satu baris bagi setiap babak |
| `suara.py` | Jana suara dan selaraskan masa setiap perkataan (Whisper) |
| `muzik.py` | Jana muzik latar, kesan bunyi, dan campur dengan narasi |
| `lukis.py` | Primitif lukisan: watak, burung, lori, karung, rumah kampung, dll. |
| `video.py` | Babak, gerakan kamera, sari kata, render |
