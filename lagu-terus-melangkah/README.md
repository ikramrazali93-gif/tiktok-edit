# Terus Melangkah — lagu deklamasi (Bahasa Melayu)

Lagu inspirasi berdasarkan mesej video [`bersedia/`](../bersedia): tak perlu tunggu rasa
bersedia; bersedia ialah keputusan; terus melangkah.

**Lagu:** [`output/terus-melangkah.mp3`](output/terus-melangkah.mp3) (~2:06, 88 BPM)
· lirik bermasa: [`output/terus-melangkah.lrc`](output/terus-melangkah.lrc)

Gaya: deklamasi. Suara lelaki matang yang sama seperti video "Bersedia" membaca lirik secara
berirama, setiap baris jatuh tepat pada permulaan bar. Melodi korus dimainkan oleh instrumen lead.

## Lirik
**[Rangkap 1]** Lama aku menunggu di hujung jalan / Menanti hati rasa tenang /
Kata mereka, tunggu saat yang tepat / Tapi saat itu tak pernah datang

**[Pra-korus]** Takut takkan pergi / Takkan beri izin / Bersedia bukan perasaan / Ia satu pilihan

**[Korus]** Terus melangkah, walau hati gementar / Terus melangkah, walau jalan berliku /
Bersedia kan menyusul di pertengahan / Hari ini ku pilih, langkah pertamaku

**[Rangkap 2]** Yang berani pun pernah rasa takut / Bezanya, mereka tak lagi menunggu /
Pagi esok takkan pernah sempurna / Tapi langkah kecil tetap menuju

**[Jambatan]** Jangan tunggu esok… / Jangan tunggu nanti… / Bersedia itu bukan perasaan, / ia satu keputusan.

**[Korus akhir]** (naik 2 semiton) · **[Penutup]** Terus melangkah… / Langkah pertama… hari ini.

## Susunan
| Bahagian | Muzik |
|---|---|
| Intro | Piano lembut, petikan melodi hook |
| Rangkap 1 | Piano arpeggio, dram "langkah kaki" lembut, shaker, bass |
| Pra-korus | Dram semakin rapat, strings, tom fill, kemudian snare roll dan riser |
| Korus ×2 | Dram 4/4 seperti derap berjalan, bass 1/8, strings, melodi lead, crash |
| Rangkap 2 | Seperti rangkap 1, ditambah tepukan |
| Jambatan | Muzik direndahkan: pad dan degupan jantung, bacaan perlahan |
| Korus akhir | Naik 2 semiton, ditambah shaker 1/16 |
| Penutup | Kord piano yang berdengung hingga habis |

## Cara jana semula
```bash
python3 vokal.py   # suara deklamasi setiap baris (guna ../bersedia/suara_lelaki.py) -> build/vokal/
python3 lagu.py    # gubah, susun & campur -> output/terus-melangkah.mp3 (+ .wav, .lrc)
```
Dalam `lirik.json`, satu baris boleh ditulis sebagai `{"teks": ..., "sebutan": ...}`. `teks`
ialah lirik yang dipaparkan, manakala `sebutan` ialah teks dengan tanda baca khas untuk suara.
