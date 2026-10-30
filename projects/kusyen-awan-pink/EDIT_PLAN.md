# Bantal Awan Tapak Kucing (3 in 1, "Marshmallow awan 3D"): edit plan, preview v1 (HyperFrames)

Source: 2 klip produk sama, iPhone, 1080×1920 portrait, HEVC HDR (HLG), 29.97fps:
- A = IMG_3185, **20.5s**: dia cuba buka beg kelabu lalu berhenti ("sarung bantal... tak mahu lagi"). **Tak diguna.**
- B = IMG_3186, **117.5s**: ulang buka beg yang sama, tunjuk bantal, pocket, selimut.

Digabung A lepas tu B jadi satu master (138.1s; B mula pada **20.521s**), transkrip B dianjak +20.521s.
Preview v1: **46.9s** (dipotong ~91s), 720×1280, 30fps, SDR, −11.3 LUFS
Final: **46.9s**, 1080×1920, 30fps, H.264 SDR (HLG → bt709), −11.3 LUFS, sudah render (HyperFrames)
Cover: `cover.jpg` (1080×1536) · Caption & hashtag: `CAPTION.md`
Safe zone TikTok: kanan 165px, bawah 435px, atas 165px (1080×1920).

Bantal bentuk tapak kucing ("paw") warna pink dengan muka arnab, ada **pocket untuk tangan** (hand warmer) dan
**selimut 170cm** tersimpan dalam (zip belakang): dia panggil "three in one". Dia pakai hud karakter kartun: nama
karakter tu **tak ditulis** di mana-mana. Pipeline sama dengan `../bantal-selimut-beruang`: potongan, suara v2 dan
SFX guna ffmpeg, lapisan grafik ialah komposisi **HyperFrames** (HTML + CSS + GSAP) dengan penempatan automatik
yang elak muka.

## Gaya: "Marshmallow awan 3D"

| Warna | Hex | Guna |
|---|---|---|
| Krim awan | `#FFFFFF` → `#FFF0F7` → `#FFD3E8` | badan awan label, end card, bingkai cover |
| Lilac awan | `#F4ECFF` → `#DCCBFF` | setiap label ketiga, bingkai |
| Pink marshmallow | `#FFC9E3` → `#FF6FAE` / `#FF9CCB` | kiub perkataan aktif, bebola 3 IN 1, pil CTA, bar |
| Pink kata kunci | `#FF4F9A` | kata kunci dalam label |
| Plum | `#6A3A78` / `#8A3E86` | teks label, outline caption |

- **Label:** kad **awan** — badan marshmallow bulat dengan **bonjol awan** di atas, tiada outline keras; bayang
  dalam (atas putih bercahaya, bawah pink) bagi rasa 3D lembut. Masuk dengan squash "jelly" (leper → melantun),
  bonjol pop satu-satu, perkataan naik, emoji melantun. Label "bernafas" perlahan masa atas skrin.
- **Bebola puff:** `3 IN 1!` dan `PAW!` dalam bebola marshmallow bulat dengan cincin awan kecil, gelembung
  terbang keluar.
- **Caption:** huruf krim, outline plum. Perkataan aktif duduk atas **kiub marshmallow** pink yang squish masuk.
- **Peralihan:** **dinding awan** naik dari bawah tutup skrin, kemudian terus naik keluar (2 kali: sebelum "buka
  zip" dan sebelum "selimut 170cm").
- **Gelembung** terapung naik dan pecah dari label besar, bebola puff dan end card.
- **Bar kemajuan:** trek marshmallow, isi pink, ☁️ di hujung.
- **End card:** awan besar: `BANTAL AWAN 🐾` / `3 IN 1 • SELIMUT • HAND WARMER` / pil CTA beg kuning berdenyut.
- **SFX baru:** `poof` (dinding awan), `bubble` (gelembung pop); `jelly` dan `squish` dipakai semula.
- **Cover:** bingkai bonjol awan keliling, tajuk awan, bebola "3 IN 1 / GEBU!", pil "SELIMUT + HAND WARMER",
  gelembung.

## Muka tak ditutup

- Kotak kepala + hud (+ purdah) ditanda **setiap 1 saat** daripada frame proxy bergrid (`HEADS` dalam `edit.py`);
  saat yang selimut tutup dia sepenuhnya tiada kotak. Muka arnab pada bantal ditanda dalam `FACES`.
- Setiap caption, label, bebola dan end card dapat semua kotak kepala dalam tempoh paparannya (±0.5s). Komposisi
  cari tempat terdekat dengan kedudukan pilihan yang **44px jauh** dari semua kotak, tak bertindih caption, dan elak
  muka arnab bila boleh. Label panjang cuba 1 baris dulu, kemudian 2 baris; bebola mengecil dulu sebelum bertindih.
- Kepala dia tinggi dalam frame (hud besar), jadi label duduk di tengah (y≈1060) dan caption di bawah (y≈1405).
- **Check sheet (51 frame):** tiada grafik kena muka atau hud dia, atau zon UI TikTok. Yang tak dapat dielak:
  label tengah bertindih badan bantal/selimut; dinding awan tutup skrin ~0.7s (dibenarkan).

## Susunan

| TL | Masa asal (gabungan) | Ayat | Grafik |
|---|---|---|---|
| 0.0 | 126.4 | ⭐ **HOOK**: "Three in one. Boleh jadi bantal, selimut dan juga boleh jadi hand warmer." | `3 IN 1!` (bebola) → `BANTAL + SELIMUT` ☁️ → `+ HAND WARMER` 🧤 + gelembung |
| 3.6 | 25.2 | "Yang ini pun ada selimut tau." | `ADA SELIMUT TAU!` 🤫 |
| 5.2 | 26.8–42.3 | buka plastik (×5) | tag `>> x5` |
| 8.3 | 42.3 + 44.2 | "Wey, pattern baru lagi. Gebu-gebas ya ni." | `CORAK BARU!` ✨ → `GEBU-GEBAS` ☁️ |
| 10.7 | 52.7 + 55.7 + 60.8 | "Ni design tapak kaki tu. Panggil apa? Paw. Panggil paw tau. Tapak kaki lah saya panggil." | `DESIGN TAPAK KAKI` 🐾 → `PANGGIL APA?` 🤔 → `PAW!` (bebola) |
| 16.1 | 68.7 | "Allah, warna pink pula tu." | `WARNA PINK` 💗 |
| 18.2 | 71.1 | "Yang ni pun ada lubang, ada pocket boleh masukkan tangan." | `ADA LUBANG` 👀 → `MASUK TANGAN!` 🧤 |
| 21.3 | 86.8 | (dinding awan) "Okey, buka zip daripada belakang." | `BUKA ZIP BELAKANG` 🔓 |
| 24.5 | 90.1 | "Keluarkan selimut. Tuh selimut pun gebu, lembut je material selimut dia." | `KELUAR SELIMUT` 🫴 → `SELIMUT GEBU & LEMBUT` ☁️ |
| 28.5 | 94.8 | "Bantal dia tak kosong. Bantal dia still masih gebu." | `BANTAL TAK KOSONG` 👌 → `MASIH GEBU!` 🤗 |
| 32.3 | audio 105.9 + 121.6, visual 114.1 | (dinding awan) "Selimut dia size 170cm. ...ngam elok untuk kita orang dewasa ni buat baring. Ngam elok panjang dia." (J-cut atas selimut terbentang) | `SELIMUT 170CM` 📏 → `NGAM ORANG DEWASA` 🛌 → `PANJANG NGAM!` 👍 |
| 39.1 | 133.5 | "Senang sangat bawa pi rombongan, drive semua. Boleh standby lah satu dalam kereta." | `BAWA ROMBONGAN` 🚌 → `STANDBY DALAM KERETA` 🚗 |
| 43.4 | audio 117.0, visual 58.4 | CTA: "Ha, tengok dekat beg kuning ni." | `TEKAN BEG KUNING` 🛒 |
| 44.4 | 64.6 (visual) | - | End card awan: `BANTAL AWAN 🐾` / `3 IN 1 • SELIMUT • HAND WARMER` / `TEKAN BEG KUNING` |

**Dibuang:** semua klip A (buka beg tak jadi, "sarung bantal... tak mahu lagi"), "Okay bismillah, mashaAllah bantal
baru lagi", "Comel", "secure a lot dia balut / tak basah kalau kena hujan" (tak jelas), "Sebentar lah", "Ah chek",
"Okey tau dah design tapak kaki kucing" (ulang), "Tuh tengok, kita tepuk dia baru unboxing", "Ha Allah comel",
"Ha gitu, three in one, tiga dalam satu, boleh masukkan tangan, lepas tu boleh jadi bantal travel..." (ulang
hook), "Buka zip daripada belakang" pertama, "Bantal gebu, lepas tu selimut pun gebu", "Guna kat bilik tidur...
travel" (ulang), "Okey ni selimut dia", "Comelnya untuk peminat pink... kelabu pun ada... warna lain pun ada"
(warna masuk caption), "Okey ni size selimut dia, nampak tak", "Boleh masukkan tangan dekat pocket dia tadi"
(ulang), jeda. **Tiada sebutan harga** dalam video ni.

## Belum pasti

- **Nama produk:** dia tak sebut nama; label dan end card guna "BANTAL AWAN" (bentuk awan/tapak kucing).
- **"Paw"**: dia sebut "Pou"/"Poh"; caption tulis "PAW".
- **"Allah, warna pink"**: semakan preview dengar "Oh my"; caption ikut "Allah".
- **CTA "dekat beg kuning ni"**: Whisper dengar "bagku ni" / "beg ku ni"; satu pass chunk dengar "di belakang ini".
- **"Okey, buka zip"**: "Okey" kena masuk sekali sebab mula selepas "Okey" potong "buka" (preview dengar "kat dari
  belakang"); caption mula pada "Buka".
- **"drive semua"**: Whisper tulis "driver"; caption tulis "drive".
- **"Selimut dia size 170cm"**: "Se" perlahan; semakan preview pertama dengar "benda size", dah dibetulkan
  (mula 105.92), semakan kedua dengar "Selimut dia size 170cm".

## Render (HyperFrames)

Sama macam `../bantal-durian-2`. Master gabungan dibuat dulu (lihat `build_master.sh`: tone-map A dan B,
concat, proxy):

```
cd comp && npm install && cd ..                      # hyperframes@0.8.181 (dipin dalam comp/package.json)
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell   # pilihan

python3 edit.py proxy.mp4 transcript.json sfx/ out/                  # preview: out/preview.mp4 (720x1280)
python3 edit.py master1080.mp4 transcript.json sfx/ final/ --final   # final:   final/final.mp4 (1080x1920)
python3 edit.py proxy.mp4 transcript.json sfx/ out/ --graphics-only  # ubah grafik sahaja, guna semula out/base.mp4
python3 check.py out/ check.jpg                                      # check sheet: zon UI + kotak kepala + muka bantal

cd cover && npx --prefix ../comp hyperframes snapshot . --at 0.5 --no-end -o snap   # cover -> snap/*.png -> ../cover.jpg
```

`transcript.json` ialah transkrip A + transkrip B (dianjak +20.521s). `sfx.py` menjana semua bunyi
(`python3 sfx.py <dir>`), termasuk `poof` dan `bubble` baru.

**Masa render:** di container ni (4 CPU dikongsi dengan fork lain, tiada GPU), render HyperFrames untuk 46.9s
(1,406 frame) ambil **3m 40s – 6m**; keseluruhan pipeline preview 5.5–8 minit.
