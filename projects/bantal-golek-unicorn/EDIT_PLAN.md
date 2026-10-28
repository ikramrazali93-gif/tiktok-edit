# Bantal Peluk Unicorn (Pelangi hologram): edit plan, preview v1 (HyperFrames)

Source: IMG_3179, iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps, **156.4s**
Preview v1: **38.4s** (dipotong ~118s), 720×1280, 30fps, SDR. Suara −11.5 LUFS; keseluruhan −14.3 LUFS (kebanyakan muzik)
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 165px, bawah 435px, atas 165px (1080×1920).

Klip asal 156s tapi dia hampir tak bercakap: ~45s buka bungkusan plastik hitam, kemudian angkat, peluk dan hayun
bantal golek pink bercorak unicorn/pelangi. Ayat yang ada cuma "Wih, bantal peluk", "Sekejap, tengok kita buka
ni", ayat harga (dipotong), "Boleh tengok dekat bawah sekarang" dan "Panjang tau". Jadi cerita dibawa oleh label,
dengan **muzik latar lembut** (dijana sendiri dalam `sfx.py` → `music.wav`, bukan lagu berlesen) yang
direndahkan bila dia bercakap. Kalau nak, tukar dengan trending sound dalam TikTok.

Pipeline sama dengan `../bantal-durian-2`: potongan, suara v2, SFX dan muzik guna ffmpeg; lapisan grafik ialah
komposisi **HyperFrames** (HTML + CSS + GSAP).

## Gaya: "Pelangi unicorn hologram"

| Warna | Hex | Guna |
|---|---|---|
| Pelangi foil | `#FF7AD9` `#FFC46B` `#FFF27A` `#7DFFB2` `#6BD7FF` `#A98BFF` | bingkai label (conic gradient), arka pelangi, wipe, bar kemajuan, bintang |
| Mutiara | `#FFF6FD` → `#E6FBFF` | isi kad label, end card |
| Ungu gelap | `#4B1D6B` / `#5B2A86` | huruf label, outline caption |
| Pink panas | `#E0329A` / `#FF4FB4` | kata kunci label, perkataan aktif caption |
| Kuning | `#FFE14D` | pil CTA end card |

- **Label:** kad mutiara dengan bingkai foil pelangi (conic gradient) + cahaya pink. Masuk dengan blur → tajam dan
  elastic, perkataan muncul satu-satu, emoji dalam lencana mutiara berpusing masuk, kilauan (sheen) menyapu kad,
  kad terapung perlahan. Bintang glitter pelangi memancar keluar.
- **Label besar** (PANJANG TAU!, BANTAL PELUK UNICORN, TARAA!) dapat **arka pelangi leper** yang dilukis masuk
  di atasnya, dalam ruang yang dah ditempah oleh label tu (tak sampai ke kepala).
- **Caption:** huruf putih dengan outline ungu. Perkataan aktif jadi pink panas dengan cahaya pink/cyan dan
  melantun sikit. Kata kunci pink muda. Caption cuma ada masa dia bercakap (hook, unboxing, CTA).
- **Peralihan:** jalur hologram pelangi menyerong dengan bintang putih menyapu skrin (sebelum "TARAA" dan
  sebelum end card).
- **Bar kemajuan:** reben pelangi dengan bintang kuning berpusing di hujung. Tag `>> x6` masa unboxing.
- **Glitter ambien:** bintang kecil berkelip di tepi kiri bawah (jauh dari kepala).
- **End card:** kad mutiara di bawah arka pelangi: `BANTAL PELUK / UNICORN 🦄`, `🌈 PANJANG • CORAK PELANGI`,
  CTA kuning `🛒 TEKAN BEG KUNING` yang berdenyut.
- **Bunyi baru:** `shimmer` (glissando tongkat ajaib), `twinkle` (bintang), `music` (pad + kotak muzik + bass
  + shaker, C-G-Am-F, 96 BPM).
- **Cover:** bingkai foil hologram, pil di kawasan pokok atas hud, pil atas kot, kad tajuk + arka pelangi di kiri bawah.

## Muka tak ditutup

- Kotak kepala + hud ditanda daripada frame proxy bergrid (`HEADS` dalam `edit.py`): setiap 1s untuk shot
  montaj, setiap 2-4s untuk shot buka bungkusan (dia berdiri tegak di situ). `HEAD_PAD = 2.0s` supaya setiap
  grafik ambil kira kotak kepala sebelum dan selepas.
- Komposisi (`comp/index.html`, `place()`) cari tempat paling dekat dengan kedudukan pilihan yang 44px bebas
  daripada semua kotak kepala dalam tempoh grafik tu, dan tak bertindih caption. Label panjang dibalut 2 baris
  dulu, baru dikecilkan.
- Bintang glitter yang laluannya masuk kotak kepala dibuang. Arka pelangi duduk dalam ruang label sendiri.
- `check.py` (kotak cyan + zon UI merah atas 39 frame preview): tiada label, caption, bintang atau end card atas
  muka dia. Kepala dia selalu di bahagian atas, jadi kebanyakan label jatuh ke tengah skrin atas bantal/badan
  dia (tak dapat dielak); label hook kadang-kadang atas bantal yang dihayun. Wipe hologram lalu seluruh skrin
  ~0.6s (dibenarkan).

## Susunan

| TL | Masa asal | Ayat / visual | Grafik |
|---|---|---|---|
| 0.0 | audio 154.8 + 3.1, visual 125.8 | ⭐ **HOOK** (J-cut atas dia hayun bantal ke kamera): "Panjang tau! Wih, bantal peluk." | `PANJANG TAU!` 📏 + arka → `BANTAL PELUK UNICORN` 🦄 + arka |
| 3.3 | 5.7 | "Sekejap, tengok kita buka ni." | `JOM UNBOXING!` 📦 |
| 5.0 | 7.4–49.6 | buka bungkusan (×6, muzik) | tag `>> x6`, `SABAR, TENGAH BUKA...` 😆 |
| 12.0 | 49.6–54.1 | bantal keluar dari beg (×1.5) | wipe hologram → `TARAA!` ✨ + arka |
| 15.0 | 59.6 | angkat tinggi | `PANJANG GILA!` 🤩 |
| 18.0 | 66.0 | peluk menyerong | `CORAK UNICORN & PELANGI` 🌈 |
| 20.6 | 80.0 | pegang tegak | `PELUK ATAS KE BAWAH` 🤗 |
| 23.2 | 88.0 | peluk bungkus | `TEMAN TIDUR` 😴 |
| 25.8 | 112.0 | peluk dua tangan | `PELUK KUAT-KUAT` 💞 |
| 28.4 | 130.2 | hayun melintang | `PINK CERIA` 💖 |
| 31.0 | 139.0 | peluk manja | `LENA SAMPAI PAGI` 🌙 |
| 33.6 | 152.0 | "Boleh tengok dekat bawah sekarang." | `TENGOK BEG KUNING` 👇 |
| 35.6 | 144.0 (visual, senyap) | – | wipe → end card |

Dibuang:
- **Pembukaan 0–2s:** tak jelas (Whisper keluar "terima kasih kerana menonton", halusinasi).
- **Ayat harga 148.6–151.9s** ("Harganya sangat-sangat …, harga tak masalah kan"), ikut peraturan tiada harga.
- **Hujung:** "Peluk/… perlu" di hujung klip (tak jelas).
- **Shot lain:** kebanyakan unboxing (dilaju ×6) dan ~70s shot peluk berulang (dipilih 7 shot, 2.6s setiap satu).

## Belum pasti

- **"Wih, bantal peluk":** Whisper dengar "bahan taip peluk" / "bantai peluk" (loghat). Caption tulis "Wih, bantal peluk".
- **"Sekejap,":** satu pass dengar "Tunggu sekejap", satu lagi "Sekejap lah", semakan preview dengar "Sainah".
  Bunyi tu pendek (0.3s). Caption tulis "Sekejap,".
- **CTA:** ada satu bunyi pendek sebelum "boleh" (Whisper: "Apa"). Caption mula pada "Boleh".
- **Klip asal penuh bunyi angin/plastik:** transkrip penuh Whisper berhalusinasi ("Tidak, tidak", "Terima kasih
  kerana menonton"), jadi semua masa perkataan disemak dengan envelope dan transkrip per-chunk (`OVERRIDE`).

## Render (HyperFrames)

```
cd comp && npm install && cd ..                      # hyperframes@0.8.181 (dipin dalam comp/package.json)
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell   # pilihan

python3 sfx.py sfx/                                                  # semua SFX + music.wav
python3 edit.py proxy.mp4 transcript.json sfx/ out/                  # preview: out/preview.mp4 (720x1280)
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final   # final:   final/final.mp4 (1080x1920)
python3 edit.py proxy.mp4 transcript.json sfx/ out/ --graphics-only  # ubah grafik sahaja, guna semula out/base.mp4
python3 check.py out/ check.jpg                                      # check sheet: zon UI + kotak kepala

cd cover && npx --prefix ../comp hyperframes snapshot . --at 0.5 --no-end -o snap   # cover -> snap/*.png -> ../cover.jpg
```

`transcript.json` di sini ialah transkrip dengan VAD + denoise (yang asal penuh halusinasi); kata-kata caption
datang daripada `OVERRIDE` dalam `edit.py`.

**Masa render:** di container ni (4 CPU dikongsi dengan render lain, tiada GPU), render HyperFrames untuk 38.4s
(1,153 frame) ambil 1m 50s – 3m 15s. Keseluruhan pipeline preview 3–5 minit.
