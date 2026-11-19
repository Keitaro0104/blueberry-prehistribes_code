# Peta Sistem — Prehistoric Tribes (J2ME, THQ / Gear Games, 2008)

Bahasa Indonesia, untuk belajar di level source code.
Sumber: JAR `prehistoric_tribes_240x320-84398_4_at1w.jar` (487 KB, MIDP-2.0, 240x320),
decompile CFR 0.152 → 13.418 baris, 7 class. Nama class/field sudah diacak jadi `a`–`f`,
jadi sebagian arti disimpulkan dari konteks dan teks game. Bagian yang belum pasti ditandai.

## 1. Identitas game

- MIDlet: `Prehistoric Tribes`, versi 0.1.28, vendor THQ, `MIDlet-1: Prehistoric Tribes, icon.png, tribes`
- `MicroEdition-Profile: MIDP-2.0`, `CLDC-1.0`, `Cheat-Support: off` di manifest (tapi kode cheat ada, lihat §4)
- Credit di teks: © 2008 THQ Wireless Inc., versi wireless dikembangkan Gear Games, Ltd.
- Genre: strategi desa real-time, bukan arcade. Dua suku (pemain + musuh) di peta grid.

## 2. Peta kode (7 class)

| Class | Baris | Peran |
|---|---|---|
| `tribes` | 78 | MIDlet entry. `startApp` → thread → loading → game |
| `d` | 53 | Layar loading / splash (Canvas) |
| `f` | 6.680 | Game utama: Canvas + game loop + input + rendering + save/load |
| `b` | 5.805 | Logika dunia: peta, villager, bangunan, AI musuh, combat |
| `e` | 280 | Loader resource (`ma`, `pd0`, `pi0/pi8/pi9`, `sa`, font) |
| `c` | 404 | Loader teks/bahasa (`s`, `t`, `d0`) + gambar teks |
| `a` | 118 | Pemutar musik MIDI |

## 3. Alur utama

`startApp()` → `run()` di `tribes`:
- Buat layar loading `d`, tampilkan `l0` (logo THQ, 1 detik) → `l1` (logo Gear Games, 2 detik) → `l2` (layar judul, 2 detik). Total ±5 detik. Angka 5 = tanda selesai (gambar hanya digambar kalau nomor < 4).
- Lalu `new f(this)`, `f.a()` membuat thread game.
- `pauseApp()` → `f.d()`, `destroyApp()` → `f.b()`.

Game loop `f.run()` (baris 485-540):
- Siapkan dunia `new b()`, loader `new e(this)`, `setCurrent(this)`.
- Coba baca save: `d(0)` dulu (pengaturan), kalau gagal coba `d(1)`, `d(2)`.
- Nilai awal: `Q=14` (menu utama), `v=0` (mode menu).
- Tiap putaran: `aS()` (jeda + musik) → `h()` (update logika) → `m()` (gambar ke buffer) → `l()` (repaint + tunggu paint selesai) → tidur sisa waktu.
- Target ±50 ms per tick kalau mode `c` benar → **±20 tick/detik**. Mode satunya tidak bisa dipastikan nilainya karena nama field bertabrakan.
- `h()`: penghitung animasi reset di 8, penghitung lain reset di 120. Kalau `v==0` (menu) → `ak()`; kalau `v==1` (dalam game) → `V()` (input) + `k()` (cari bangunan/unit terdekat), tiap 6 tick pemicu berkala, lalu `j()` → `b.g(), b.e(), b.h(), b.i()` (update dunia). Kalau penghitung akhir misi `u` = 41 atau 90 → `v=0, Q=24` (layar akhir misi).

State (`v` dan `Q`, nomor layar, bukan nama):
- `v==0` = menu, `v==1` = dalam game. `R` = layar sebelumnya (untuk kembali).
- Q 14 = menu utama. Q 10/11 = jeda dalam game. Q 20 = popup info bangunan/unit. Q 22/23 = load/hasil. Q 24 = akhir misi. Q 25 = keluar dari game. Q 27 = pause sistem (dari `hideNotify()`, bukan tombol; kembali lewat `showNotify()` → `Q=R`). Q 32 = layar iklan `/l3`.
- Mulai game: `am()`, `T=1` → `v=1`. Ada batas level `q < 7` vs `q >= 7` (kampanye vs custom, cocok dengan teks tapi kode tidak menulis kata itu).

## 4. Input

- Layar loading: `keyPressed()` kosong, tombol diabaikan.
- Softkey: kiri `-6` (atau `6` / `*`), kanan `-7` (atau `7` / `#`).
- D-pad via `getGameAction` + angka: atas `2`, bawah `8`, kiri `4`, kanan `6`, pilih/tengah `5` (FIRE). Angka `1/3/7/9` = ganti grup, `0` = grup 0.
- `keyReleased()`: matikan flag arah; lepas tombol tengah cepat (< 4 tick) = ketukan pilih.
- Softkey dalam game: kiri → buka menu bangun (`w=2`); kanan → tutup menu / batal pilih / buka jeda Q 10/11.
- Cheat (fakta kode, `m()` baris 6595-6680): urutan `8,7,3,9,1` lalu tombol ke-6: `1` → flag `af`, `3` → flag `ag`, `7` → +100 ke 5 resource pertama, `9` → `u=1`. Manifest bilang Cheat-Support off, tapi kode cheat-nya ada.

## 5. Rendering

- Double buffer: `Image[]` / `Graphics[]` 4 slot. Loading `a[0]` 264x352; game `a[1]` dan `a[3]` 264x304, plus buffer kecil 79x63.
- Alur: `m()` gambar ke buffer (peta, unit, menu) → `l()` → `repaint()` → `paint()` salin buffer ke layar dengan `drawRegion`.
- Game dirancang 240x320 tapi buffer 264x352, disalin dengan geser (-11,-8) — bingkai 11 px kiri, 8 px atas.
- Tile peta 22x16 piksel. Kamera: 11 kolom x 18 baris terlihat. Scroll halus setengah tile (11 px horizontal, 8 px vertikal).

## 6. Dunia (b.java)

- Peta grid maksimal **96x96 tile**. Ukuran tiap level dari tabel: level 0 dipaksa 40x32, level 5 lebar dikurangi 32.
- Dua grid: `b[][]` = jenis tanah, `c[][]` = penghuni (0 kosong, positif = nomor villager 1-100, negatif = nomor bangunan).
- Peta disimpan di file `ma` (42.381 byte), 10 potong (offset 0, 2545, 6965, 10649, 15487, 22633, 27261, 31708, 35466, 39214). Byte ≥ 250 = kode pengulangan (kompresi RLE sederhana).
- 10 nama peta di teks: outside, revenge, escape, wastelands, a new home, great lake, desert pass, forest belt, slaughter, plot of land.
- Semua angka keseimbangan (biaya, HP, damage) ada di file `pd0` (96.990 byte: 11 tabel short + 25 tabel byte), bukan di kode. Jadi angka pastinya belum bisa dibaca tanpa decode `pd0`.

### Bangunan — 12 tipe

| # | Bangunan | Fungsi |
|---|---|---|
| 0 | armoury | tukang senjata produksi senjata |
| 1 | gym | warrior latih jarak dekat |
| 2 | hut | villager istirahat + berkembang biak, 1 hut = 4 orang |
| 3 | chief's hut | rumah chief, tempat tetua bermusyawarah |
| 4 | kitchen | tempat makan, butuh cook |
| 5 | range | warrior latih lempar |
| 6 | store | simpan semua resource + senjata |
| 7 | disco | naikkan semangat, butuh DJ |
| 8 | sanctuary | shaman sembuhkan + mantra |
| 9 | pia center | latih scout, lihat lebih jauh, sembunyi |
| 10 | nursery | anak-anak aman dari hewan/musuh |
| 11 | tower | guard lihat jauh + serang dengan senjata lempar |

- Maksimal 30 bangunan per suku. Hut +4 living space (dibatasi 50). Menu bangunan: upgrade, repair, cancel upgrade/repair, demolish. HP habis → "building is lost!".
- Syarat bangun: stok cukup (kalau tidak → "need resources!") + peran yang dibutuhkan ada (kalau tidak → "we need a cook / shaman / armourer / dj").

### Villager

- Maksimal 50 villager per suku (pemain `u=0`, musuh `u=1`). Teks: "max villagers".
- Disimpan sebagai slot bernomor + banyak array sejajar, bukan objek. Field yang terbaca: posisi, umur, gender (0 laki / 1 perempuan), HP / HP maks, tugas/status, 2 skill tempur, 7 skill sipil, kecepatan, 3 meter kebutuhan, peran/pekerjaan.
- Peran: villager, warrior, chief, shaman, cook, armourer, DJ, scout, guard, child. Default saat lahir = 9 (menganggur). Chief istimewa, nomor slotnya disimpan terpisah; kalau chief mati → "the chief is dead! … choose a new one", pemain pilih chief baru.
- Lahir/tumbuh: umur naik tiap 125 tick (pemain) / 50 tick (musuh). Dewasa umur 12, diberi skill, tugas direset. Anak < 12 tidak bisa bekerja.
- Berkembang biak: pasangan lawan jenis dengan mood cukup pergi ke hut, status 109→110→111, anak lahir dari hut (penghitung kelahiran hut mencapai 3 → villager baru umur 2).
- Tiga meter 0-99 (happiness, hunger, tiredness — label di teks): mood dihitung dari bangunan/disco minus lapar/lelah. Mood rendah → villager mogok ("leave me alone, tyrant! i'm depressed"). Lapar/lelah turun seiring waktu, villager otomatis cari makan/istirahat. Meter sampai 0 bisa mati. Makanan berkurang dari stok; tanpa kitchen → "our tribe is starving!".
- Penyakit: flag sakit, menular +8 ke villager di tile sebelah. Shaman menyembuhkan.
- Mati: HP ≤ 0 → slot dikosongkan, teks "…is dead". HP maks berubah mengikuti umur (tabel `pd0`).
- Nama: 122 nama acak di teks (jafar, jumbo, juju, mumbo, konan, fred, barney, … ubika).

### Resource / ekonomi

- Stok tiap suku: array 25 angka, dibatasi 999.
- 4 resource bahan (label teks): **food, wood, stones, bones**, plus senjata sebagai stok terpisah (diproduksi armoury, disimpan di store).
- Produksi: tiap tugas selesai, `J()` menambah stok sesuai tabel `pd0`. Konsumsi: bangun/upgrade/repair dan makan mengurangi stok.
- Angka produksi/konsumsi per bangunan tidak bisa dipastikan tanpa decode `pd0`.

### Combat / musuh

- 6 senjata: club, stone, spear, stone axe, bone mace, tomahawk. 3 jebakan: net trap, spring trap, pit trap (tipe 20-22, bukan bangunan biasa).
- Serangan lempar = proyektil parabola: waktu terbang dari jarak + gravitasi tabel, posisi tiap tick rumus kuadrat, damage = skill penyerang + bonus senjata − pertahanan target + acak.
- Musuh muncul bergelombang, bukan terus-menerus: timer serangan dari tabel (`tabel[214] − tabel[215] × kesulitan` + acak), jumlah penyerang naik seiring waktu (dibatasi tabel), dikirim bertahap tiap 150 tick. Peringatan: "enemy sighted!", "we're under attack!".
- AI musuh bermain dengan sistem yang sama: bangun/upgrade/repair bangunan sendiri, atur serangan, beri peran ke villagernya dari tabel per level. Bukan skrip sekali jalan.
- Pertahanan pemain: tower, scout pia center, jebakan, perintah "form up!" dan "call to arms!".
- Menang/kalah: teks "you have lost!" / "hurrah! you've won!", pemicu di kode `u` = 41 (menang) / 90 (kalah) di satu jalur, dan `b.k()` menilai kondisi suku di jalur lain — syarat spesifik tiap misi belum terpetakan penuh.
- Ada serangan hewan liar + pencurian anak ("animals have eaten a child!", "the enemy has stolen a child!").

### Sistem lain

- Real-time dengan tick, bukan giliran. Tiap tick `b.e()` memproses kedua suku bergantian (50 villager + 30 bangunan tiap suku), lalu `g()` memproses bangunan.
- Random: `new Random(1L)` — seed tetap 1. Dipakai untuk statistik awal, damage, AI, kelahiran, dll.
- Pathfinding: jalan selangkah ke 8 arah, maksimal 80 langkah, coba arah lain kalau buntu. Pencarian spiral untuk tile kosong terdekat, pencarian target dalam radius yang membesar selapis demi selapis. Jarak sudah dihitung di tabel 25x25.
- Cuaca/musim: **tidak ada**. Grep weather/season/rain/snow/day/night di `b.java`/`f.java` = tidak ada.
- Fog of war: ada bitmask penglihatan yang dibangun ulang di `b.d()` — kemungkinan peta yang sudah terlihat, belum dipastikan fungsinya.

## 7. Data: bahasa, teks, level, save/load

### Bahasa

- 5 folder: 0 Inggris, 1 Prancis, 2 Italia, 3 Jerman, 4 Spanyol. Ganti bahasa = ganti angka folder, muat ulang teks.
- Daftar nama bahasa hanya ada di folder 0, jadi layar pilih bahasa selalu tampil dalam bahasa Inggris.
- Jumlah string (pemisah `|`): `s` (UI) = 229 potongan, `t` (bantuan/pesan) = 72 potongan, `d0` = 236 potongan.
- Huruf beraksen disimpan dengan kode pengganti (`franc[ais` = français, `hu^tte` = hütte), diterjemahkan loader lewat tabel font. File mentah kelihatan rusak, di game tampil benar.

### Teks penting (Inggris)

- Menu utama: play | help | options | about | more games | exit
- Menu jeda: resume | save | load | quit
- Mode: new game | continue | campaign | custom game | tutorial
- Opsi: music | hints | off | on | difficulty | easy | hard
- Pesan: "building is ready.", "enemy sighted!", "we're under attack!", "building is lost!", "need resources!", "max buildings", "max villagers", "we need a cook / shaman / armourer / dj."
- Peringatan: "our tribe is starving! we need a kitchen!", "not enough living space! build more huts.", "our tribe is depressed! a disco will help…", "animals have eaten a child!…", "the chief is dead!…"
- Nama penduduk: ±124 nama acak.

### Kampanye / level

- Kampanye: **7 misi**, `q = 0`–`6`. Kalau `q < 5` setelah menang, naik ke misi berikut; kalau `q == 6` (terakhir), selesai dan `q` jadi 7.
- 10 nama peta ada di teks, tapi kampanye hanya 7 misi — pemetaan nama ke misi belum terbukti (kemungkinan 7 pertama kampanye, sisanya custom, atau 10 peta dipakai bergantian; tabel di `pd0` belum diuraikan).
- Tutorial: mode sendiri + opsi "enable tutorial?". Isinya naskah dialog terpandu di `d0[18]`–`d0[84]` (±67 potongan): bangun store, pilih villager, bangun hut/kitchen, kumpul kayu/batu, hotkey grup (`7`/`9`), bangun gym/armoury/range, "call to arms", happiness, upgrade/repair, memancing, berburu.
- Kampanye terkunci sampai tutorial lulus: "pass the tutorial first!". Kalau belum ada progres (`r == 0`), game memaksa masuk tutorial dulu.
- Isi `d0` lengkap: [0]–[17] cerita pembuka (zaman es, suku Avnotaklu), [18]–[84] tutorial, [85]–[212] dialog/cutscene antar misi, [213]–[228] mantra shaman + agen PIA + upgrade, [229] kontrol, [230]–[231] penjelasan game (4 resource; atribut penduduk: nama, gender, umur, happiness, HP, hunger, fatigue; skill tempur vs sipil), [233] credit, [234] label skor akhir.

### Save / load

- RecordStore: awalan `"t"`, 3 slot: **`t0`, `t1`, `t2`**, tiap slot 1 record.
- `t0` = pengaturan + progres kampanye (7 nilai: 1 int, 1 boolean, 5 byte; `r` = level kampanye tertinggi yang terbuka).
- `t1` = save game kampanye (`q < 7`), `t2` = save game custom (`q >= 7`).
- Isi save: nomor level, kesulitan, seluruh peta (grid 96x96, 3 lapis), penduduk (sampai 100 orang + atribut/skill), bangunan (sampai 60 + posisi/tipe/HP), 26 angka resource, posisi kamera, skor/waktu, flag. Ditulis berurutan dengan `DataOutputStream`, dibaca dengan urutan persis sama — kalau urutan beda, save rusak.
- Load saat game mulai (coba `t0`, kalau gagal coba `t1`/`t2`). Save manual lewat menu save → "game saved." / "not enough memory to save game." Save otomatis setelah misi selesai dan setelah menang kampanye. Tidak ada autosave tiap detik.
- Save menimpa: `deleteRecordStore` dulu baru buat baru. Save korup akan dihapus lalu dicoba load lagi, bukan diperbaiki.

### Resource loader (e.java)

| File | Ukuran | Isi |
|---|---|---|
| `/pd0` | 96.990 | Tabel data game (angka balance/level). `e.b()`: lewati 1 byte, baca 11 tabel short + 25 tabel byte |
| `/ma` | 42.381 | Data peta/level mentah, 9-10 potongan (offset di atas) |
| `/pi0` | 62.502 | Kumpulan PNG (sprite sheet 1) |
| `/pi9` | 8.597 | Kumpulan PNG (sprite sheet 2) |
| `/pi8` | 129.809 | Kumpulan PNG (sprite sheet 3), dimuat sesuai kebutuhan |
| `/sa` | 26.616 | Musik MIDI, 5 lagu ditempel. Panjang {8014,6315,5648,3405,3234}, posisi {0,8014,14329,19977,23382} |
| `/a` | 18.842 | Data font/huruf (312 angka panjang + blob 17.638 byte) |
| `icon.png` | 2.168 | Ikon 48x48 |

- Prefix 2 byte di `pi0/pi8/pi9`: bukan satu PNG, melainkan banyak PNG ditempel, tiap PNG diawali 2 byte panjang (big-endian). Contoh: `pi0` PNG pertama 9.120 byte, `pi8` 10.910 byte, `pi9` 2.814 byte. Gambar pertama: `pi0` 128x136, `pi8` 240x130, `pi9` 76x111 (PNG 8-bit palet).
- Gambar `l0`–`l3` (PNG biasa): `l0` logo THQ Wireless 240x71, `l1` logo Gear Games 192x114, `l2` layar judul 240x321, `l3` iklan Orange Prancis 240x320 ("Plus de jeux sur ton mobile? Envoie PLUS au 2 33 33*…") — iklan operator, bukan bagian game.

## 8. Musik

- Satu pemutar, class `a`, hanya MIDI, tidak ada efek suara terpisah.
- 5 lagu dalam satu file `/sa`. `aQ()` pilih lagu acak, `aS()` dicek tiap tick: kalau tidak ada yang berbunyi dan tidak pause (Q != 27), putar lagu acak. Volume `setLevel(n * 20)`.

## 9. Yang belum terjawab

1. Angka persis biaya/HP/damage tiap bangunan, senjata, level — butuh decode tabel `pd0`.
2. Pemetaan pasti 10 nama peta ke 7 misi kampanye + mode tutorial/custom.
3. Syarat menang/kalah spesifik tiap misi (di `b.k()`).
4. Arti pasti tiap kode tugas villager (0–111) — hanya sebagian bisa ditebak dari konteks.
5. Label pasti tiap nomor layar Q (15, 17, 18, 19, dll) dan fungsi bitmask penglihatan.
6. Format persis tiap potongan di `ma` (tile terkompresi/dikodekan sederhana, belum di-decode penuh).

## 10. File kerja

- `extracted/` — 43 file hasil unzip JAR
- `decompiled-cfr/` — 7 file Java hasil CFR
- `ANALISIS-alur-utama.md` — laporan alur utama
- `tools/` — Java 17 (Temurin) + CFR 0.152 + JADX 1.5.2 (zip)
