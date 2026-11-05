# Jumpa Totoro — vlog pendek (suntingan)

Lawatan ke kafe bertema Totoro (MoriKissa). Suntingan padat ~38 saat, format 9:16, untuk suara
latar yang akan dirakam kemudian. Status: **pratonton, menunggu kelulusan** (belum render akhir).

Media asal (klip & foto) tidak disimpan dalam repo; ia dimuat turun daripada folder Google Drive
pengguna dan dihantar ke skrip sebagai argumen.

## Senarai shot
| # | Mula | Tempoh | Shot |
|---|---|---|---|
| 1 | 0:00.0 | 2.6s | Hook: sampai depan maskot |
| 2 | 0:02.6 | 1.6s | Welcome to MoriKissa |
| 3 | 0:04.2 | 2.6s | Jalan ke patung Totoro |
| 4 | 0:06.8 | 1.9s | Bercakap ke kamera |
| 5 | 0:08.7 | 0.8s | Foto patung 1 |
| 6 | 0:09.5 | 0.8s | Foto patung 2 |
| 7 | 0:10.3 | 1.0s | Foto patung 3 (mendongak) |
| 8 | 0:11.3 | 2.6s | Duduk depan patung |
| 9 | 0:13.9 | 0.8s | Kedai: bas kucing |
| 10 | 0:14.7 | 1.6s | Kedai: bas kucing (pan) |
| 11 | 0:16.3 | 2.0s | Kedai: rak cenderamata |
| 12 | 0:18.3 | 1.6s | Kedai: budak membelek |
| 13 | 0:19.9 | 2.0s | Kedai: dinding patung |
| 14 | 0:21.9 | 1.6s | Menu TEPPAN |
| 15 | 0:23.5 | 0.6s | Depa tangan 1 |
| 16 | 0:24.1 | 0.6s | Depa tangan 2 |
| 17 | 0:24.7 | 0.6s | Depa tangan 3 |
| 18 | 0:25.3 | 4.4s | Berjalan ke arah maskot |
| 19 | 0:29.7 | 6.6s | Jumpa maskot Totoro |
| 20 | 0:36.3 | 2.2s | Penutup (ruang teks) |

## Gaya suntingan
- Potongan pantas mengikut rentak vlog. Bahagian rakaman yang bergoyang dibuang, dan klip patung
  serta kedai distabilkan dengan vidstab.
- Foto diberi gerakan zoom/pan. Foto landskap dan foto "depa tangan" dipaparkan penuh dengan
  latar kabur.
- Warna dicerahkan sedikit untuk suasana malam. Audio asal direndahkan (35%) untuk memberi ruang
  kepada suara latar.
- Pratonton (540×960) memaparkan kod masa dan label shot untuk bantu menulis skrip suara latar.

## Cara jana
```bash
python3 sunting.py "<folder media>" --pratonton          # build/pratonton-jumpa-totoro.mp4
python3 sunting.py "<folder media>" --akhir --vo vo.m4a  # output/jumpa-totoro.mp4 (1080x1920)
```
Untuk mengubah susunan, masa potong atau kelajuan, edit `edl.json`.
