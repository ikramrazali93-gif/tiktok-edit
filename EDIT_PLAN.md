# Edit: Bantal 2-dalam-1 (Selimut + Beg): PREVIEW

- Asal: 1:51 → edit: **1:13** (dipotong ~38s ulangan, pause, filler)
- Format: 1080x1920 portrait, 30fps (preview 540x960 + watermark PREVIEW)
- Rujukan gaya (FB reel): kapsyen 1–2 perkataan di tengah skrin, keyword **kuning**, latar gelap/kontra
- Tanpa HyperFrames: ffmpeg + faster-whisper (transcribe BM, timestamp setiap perkataan)

## Struktur

| Masa | Bahagian | Isi | Grafik / SFX |
|---|---|---|---|
| 0:00–0:06 | **HOOK** | "Dua dalam satu, bantal, ada selimut sekali, boleh galas sebagai beg" atas montage 3 shot (bantal → selimut terbuka → galas) | "2 DALAM 1" + BANTAL / + SELIMUT / + BEG pop satu-satu, push-in zoom, whoosh setiap cut |
| 0:06–0:14 | Intro | Jom unboxing, ramai orang borong, sangat function | "RAMAI ORANG BORONG" + ding |
| 0:14–0:18 | Galas | Hampa tengok na, boleh galas macam ni | "BOLEH GALAS" |
| 0:18–0:29 | Pilihan | 2 pilihan selimut, biasa vs V2, luar sama dalam beza | "2 PILIHAN SELIMUT", "BIASA vs V2", "LUAR SAMA, DALAM BEZA" |
| 0:29–0:33 | Buka zip | Buka zip keliling → selimut keluar | whoosh |
| 0:33–0:52 | Selimut | 160x100cm, travel/bas/kereta api, berjahit cantum, buka = selimut, tutup = bantal | "160 x 100 CM" + ding, checklist ✓, "BUKA = SELIMUT / TUTUP = BANTAL" |
| 0:52–1:12 | V2 | Selimut asing, guna 2 serentak, pilih bercantum/terpisah | "V2 = SELIMUT ASING", "GUNA 2 SERENTAK", "BERCANTUM vs TERPISAH" |
| 1:12–1:13 | CTA | Korang tengok dekat beg kuning | "TEKAN BEG KUNING" goyang + anak panah, ding |

Sentiasa ada: progress bar kuning di atas, jump-cut zoom (1.0x ↔ 1.12x) untuk sembunyi potongan, audio dinormalkan ke -14 LUFS.

## Yang dibuang (lihat `edit/edl.json` → `cut_reasons`)
- Ulangan: "Ok, sangat-sangat function" + "Dua dalam satu dia ada selimut sekali" (kali ke-2)
- Awkward: "nanti saya masukkan dalam video… saya tengok lagi satu punya", "ni saya tunjuk hat besar dulu", "yang first punya macam ni…"
- Semua pause > 0.3s, filler "Ok," / "haa" di awal ayat bila boleh dipotong bersih

## Ejaan kapsyen (dialek → BM standard)
bantai → bantal, galah → galas, bag → beg, zit → zip, bah → bas, retapi → kereta api, pi → pergi, hat → yang

## Cara render final (selepas preview diluluskan)
```
python3 edit/build.py --final   # -> out/final.mp4 1080x1920
```
