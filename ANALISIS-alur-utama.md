# Alur Utama Prehistoric Tribes — dari Kode Decompile

Sumber: tribes.java, d.java, f.java (6.680 baris), a.java, dibantu e.java / c.java. Nama class dan field sudah diacak jadi a–f.

## 1. Alur start: startApp → loading d → game f

- tribes.java:20-28 startApp(): kalau objek game f sudah ada, panggil f.e() (lanjutkan). Kalau belum, Display.getDisplay(), buat Thread baru, thread.start().
- tribes.java:42-65 run(): new d(this), d.a(), setCurrent(d). Urutan angka adalah nomor gambar, bukan nomor menu. Bukti di d.java: d.a() menggambar "/l" + this.a.
  - a=0, tampil 1 detik, lalu d.a() lagi, tunggu 2 detik → l0 = logo THQ Wireless (240x71)
  - a=1, d.a(), tunggu 2 detik → l1 = logo Gear Games (192x114)
  - a=2, d.a() → l2 = layar judul Prehistoric Tribes (240x321)
  - a=5 — bukan gambar. Di d.a(), gambar hanya digambar kalau a < 4. Jadi 5 = tanda "selesai, jangan gambar lagi".
- Total loading sekitar 5 detik (1+2+2), lalu new f(this) dan f.a().
- pauseApp()/destroyApp() meneruskan ke f.d() (jeda) dan f.b() (keluar / notifyDestroyed()).

d.java — layar loading:
- Konstruktor: setFullScreenMode(true).
- a(): pertama kali buat buffer gambar 264x352, isi putih fillRect(11,8,240,321), gambar /l0–/l2 di tengah (131,168, anchor 3 = tengah), lalu repaint().
- paint(): gambar buffer itu ke layar di posisi (-11,-8).
- keyPressed() kosong — tombol apa pun di layar loading diabaikan.

f.java:356-409 — konstruktor f dan f.a():
- Konstruktor menyiapkan bahasa {"en","fr","it","de","es"}, setFullScreenMode(true), nilai awal (mis. U=5, V=4).
- f.a() (baris 406): buat Thread baru dari f dan jalankan — di sinilah f.run() mulai.

## 2. Game loop di f

f.java:485-540 — run():
- Persiapan: f() (baris 412) — buat logika dunia new b(), loader new e(this), lalu setCurrent(this) (layar pindah dari d ke f); g() (baris 428) — alokasi semua array peta/unit.
- Lalu coba baca save: if (!this.d(0)) { this.d(1); this.d(2); } — d(n) di baris 6245 adalah load dari RecordStore "t"+n. Slot 0 dibaca dulu (pengaturan), kalau tidak ada, coba slot 1 dan 2.
- Nilai awal: Q=14, v=0 (mode menu), H=true, R=U.
- Loop while (this.b) tiap putaran:
  1. l = f.a() — f.a() di baris 6539 hanya System.currentTimeMillis(), jadi ini jam awal putaran.
  2. aS() — cek jeda dan musik.
  3. h() — update logika.
  4. m() — gambar ke buffer luar layar.
  5. l() — repaint() dan tunggu sampai paint() selesai (while (this.z && !this.Z) Thread.yield()).
  6. Kalau sedang scroll (ad != 0 || ae != 0), gambar ulang sekali lagi setelah tidur setengah frame (tribes.a(this.i / 2)).
  7. Tidur sisa waktu: l3 = this.i - (waktu yang sudah dipakai), dibatasi 0 sampai i, lalu tribes.a((int)l3).

Berapa tick/detik?
- h() baris 542: this.i = this.c ? 50 : this.j. Jadi target waktu per putaran adalah i milidetik. Kalau i=50, itu 20 tick/detik. Untuk mode satunya (j), nilai pastinya tidak bisa dilacak dengan aman karena nama field bertabrakan (obfuscation). Yang bisa dikatakan: kira-kira 20 kali per detik, dengan target 50 ms per tick saat c benar.

Apa yang di-update tiap tick — h(), baris 541-640:
- Penghitung animasi e: naik tiap tick, reset di 8 (siklus animasi 8 frame). Penghitung f: reset di 120.
- Kalau v==0 (menu): panggil ak() — update menu.
- Kalau v==1 (dalam game):
  - Kalau w==2 atau 4: ae() (mode tertentu, mis. memilih).
  - Kalau tidak: V() (baca input pemain) dan k() (cari bangunan/unit terdekat dari kursor).
  - Lalu penghitung d: tiap 6 tick panggil a(100,0,0,0) — pemicu berkala (kemungkinan hitung sumber daya / waktu game).
  - Lalu j() (baris 636): panggil b.g(), b.e(), b.h(), b.i() — update dunia di b.java (AI, gerakan, produksi). Juga ada logika akhir misi: kalau u mencapai 41 atau 90, pindah ke v=0, Q=24.
- Kalau o mencapai 3, panggil i() untuk reset semua flag input.

## 3. State / mode game

Dua mode besar, dibedakan oleh field v di f:
- v==0 = menu / di luar permainan. paint() (baris 768) menggambar gambar menu a[M].
- v==1 = di dalam permainan. paint() (baris 751) menggambar peta.

Layar/menu memakai nomor Q (dan R = layar sebelumnya, untuk tombol "kembali"). Q ini nomor dari tabel data di b/e, bukan nama:

| Q | Bukti | Arti (sejauh bisa dibuktikan) |
|---|---|---|
| 14 | f.java:495, awal run() | Layar pertama setelah loading — menu utama. G() (baris 2759) mengelompokkan Q 14 bersama 2,3,5,9,12,13 sebagai layar menu. |
| 10 / 11 | f.java:3552, di W() saat tombol kanan ditekan dalam game | Layar jeda/pause dalam game (dipilih dari q < 7 dan t). |
| 20 | f.java:3302-3313, method a(byte,byte,byte) | Popup info: v=0, Q=20, v=12+by — dialog info bangunan/unit. |
| 22 / 23 | f.java:4367, am() | Layar load / hasil: am() menangani T=0 (load level g(q)), T=1 (mulai game, v=1), T=2 (gagal load → kembali). |
| 24 | f.java:686-689, di j() | Layar akhir misi (tercapai saat u==41 atau 90). |
| 25 | f.java:568-571, di h() saat v==1 dan kondisi selesai | Keluar dari game ke layar 25, R=28. Label menang/kalah tidak tertulis di kode. |
| 27 | f.java:6584-6598 (aS()) dan 4397-4412 (al()) | Pause sistem. Bukan dari tombol, tapi dari hideNotify() → f.d() (baris 6551: Y=true, Z=true). Saat disembunyikan, Q lama disimpan ke R, Q jadi 27, loop menunggu (while (this.Y)). Saat kembali (showNotify() → f.e()), al() mengembalikan Q=R. |
| 32 | f.java:2736-2745, di F() | Layar iklan: menggambar langsung Image.createImage("/l3") — gambar iklan Orange berbahasa Prancis. |
| 15,17,18,19 | f.java:2699-2745, dispatcher F() | Layar-layar lain (J(), P(), K(), L()). Nama fungsinya tidak terbaca, jadi tidak diberi label. |

Perpindahan antar state:
- Menu (v==0): ak() baris 4364 — kalau Q 22/23 → am(); kalau tombol kanan (m) → an(); kalau tombol arah/pilih → ao(); kalau tombol atas/bawah (e/f) → aB()/aC() (geser pilihan menu).
- Mulai game: am() baris 4413 — T=1 berarti mulai, v=1, R diisi 10 atau 11. Ada batas q < 7 vs q >= 7 di beberapa tempat (mis. am() baris 4436-4441): level 0–6 satu kelompok, 7 ke atas kelompok lain — cocok dengan mode campaign vs custom game dari teks, tapi kode sendiri tidak menulis kata itu.
- Dalam game kembali ke menu: h() baris 568 (v=0, Q=25) dan j() baris 686 (v=0, Q=24).
- Save/load: d(n) baris 6245 (baca RecordStore "t"+n, slot 0 = pengaturan, 1/2 = save game) dan e(n) baris 6412 (tulis, hapus dulu lalu buat baru). Isi save lengkap: posisi kamera, peta, unit, sumber daya — dibaca field demi field di baris 6250-6400.

## 4. Input

Layar loading (d.java): keyPressed() kosong — tidak ada tombol yang berfungsi.

Dalam game (f.java:3326-3450):
- Semua tombol selain -10 diterima (a(n) baris 3456: return n != -10).
- Softkey kiri/kanan: static int a = -6; static int b = -7; (baris 30-31). Di keyPressed(): n==-6 (atau 6) atau * (42) → flag l=true (kiri); n==-7 (atau 7) atau # (35) → flag m=true (kanan).
- Angka 1/3/7/9: 49 ('1') → i=1, 51 ('3') → i=3, 55 ('7') → i=7, 57 ('9') → i=9, 48 ('0') → i=0. Dipakai di aG()/aH() (baris 5060-5099) untuk ganti grup: i==7 → grup 2, i==9 → grup 3.
- getGameAction(n) dipanggil di baris 3381 (saat tekan) dan 3425 (saat lepas), dibungkus try/catch — kalau gagal, m=666. Hasilnya dipetakan ganda dengan tombol angka (bisa pakai D-pad atau angka):
  - m==1 (UP) atau 50 ('2') → e=true (atas)
  - m==6 (DOWN) atau 56 ('8') → f=true (bawah)
  - m==2 (LEFT) atau 52 ('4') → g=true (kiri)
  - m==5 (RIGHT) atau 54 ('6') → h=true (kanan)
  - m==8 (FIRE/tengah) atau 53 ('5') → i=true, t=true (pilih/aksi)
- keyReleased() (baris 3413): mematikan flag arah yang sama (e/f/g/h=false), dan kalau tombol tengah dilepas cepat (E < 4) → v=true (diartikan sebagai ketukan pilih, bukan tahan).
- Cheat code: m(int n) baris 6595-6680 — urutan tombol disimpan dan dibandingkan dengan j = {56,55,51,57,49} (tombol 8,7,3,9,1). Kalau 5 tombol pertama cocok, tombol ke-6 menentukan: 49 ('1') → af=true, 51 ('3') → ag=true, 55 ('7') → tambah 100 ke 5 sumber daya pertama, 57 ('9') → u=1. Cocok dengan property Cheat-Support: on di manifest.
- Yang dilakukan flag itu — V() baris 3487-3550:
  - Kalau sedang memilih area (u && i): aF() — kumpulkan unit di area yang dipilih.
  - Kalau tombol tengah ditahan (t): aE() — tahan lebih dari 4 tick → pilih grup.
  - Kalau kursor di bangunan (w==1 dan W 51–100): pindah kamera ke bangunan itu.
  - Kalau tidak: d(by) (buka info / pilih bangunan), X() (bangun), atau f(-by) (perintah unit).
  - Scroll halus: ad = af * 11; ae = ag * 8 (baris 3528-3529) — setengah tile.
- Softkey dalam game — W() baris 3536-3555: l (kiri) → buka menu bangun (w=2); m (kanan) → kalau sedang di menu bangun, tutup; kalau sedang memilih unit, batal; kalau tidak, buka layar jeda Q=10/11.

## 5. Rendering

- Double buffer: f.java punya static Image[] a dan static Graphics[] a (4 slot). e.c() baris 107-112 membuat buffer a[1] 264x304, a[3] 264x304, dan satu buffer kecil 79x63. d.a() membuat a[0] 264x352 untuk loading.
- Alurnya: m() (baris 779) menggambar dulu ke buffer luar layar — peta (n()), unit, dan menu (F() kalau v==0). Lalu l() (baris 745) memanggil repaint(), dan paint() (baris 750) menyalin buffer ke layar dengan drawRegion.
- Ukuran: game dirancang 240x320, tapi buffer 264x352. Saat disalin, digeser (-11,-8) — terlihat di d.paint() (drawImage(f.a[0], -11,-8,0)) dan f.paint() (baris 753,768: this.a-11, this.b-8). Jadi ada bingkai 11 px kiri dan 8 px atas.
- Dalam game (v==1, paint() baris 751-766): gambar peta dari buffer a[c[1]] atau a[3] (kalau sedang scroll), lalu loop 20 slot overlay (ikon unit/bangunan, panah, dsb.).
- Menu (v!=1, baris 767-774): gambar a[M] ukuran 251x328, plus dua bilah hitam atas/bawah kalau sedang ada teks berjalan (s && aP < 0).
- Kamera / scroll: peta berupa grid tile 22x16 piksel — bukti n() baris 827-829 (aj = -af * 22; ak = -ag * 16) dan m() baris 795-796 (c(y * 22 - ad, A * 16 - ae)). y/A = posisi tile asal kamera, I/K = posisi kursor di dalam layar, O=11 kolom dan P=18 baris terlihat (dari e.c() baris 100-104). Scroll halus dilakukan setengah tile (11 px horizontal, 8 px vertikal), lalu aK() (baris 5196) menjepit kursor supaya tidak keluar peta.

## 6. Musik / suara

- Hanya ada satu pemutar, class a.java, dan itu MIDI. Tidak ada class efek suara terpisah.
- Data musik: e.g() (di e.java, sekitar baris 234) membaca file /sa (26.616 byte) ke f.w. Tabel di f.java / e.g(): f.e = {8014,6315,5648,3405,3234} (panjang) dan f.f = {0,8014,14329,19977,23382} (posisi awal) — jadi ada 5 lagu MIDI dalam satu file.
- a.java — cara kerja pemutar:
  - Konstruktor: Manager.createPlayer(new ByteArrayInputStream(f.w, f.f[f.f], f.e[f.f]), "audio/midi"), lalu realize() dan addPlayerListener(). Jadi lagu dipilih dari tabel di atas.
  - a(int n) (volume): ambil VolumeControl, kalau n != 0 putar (c()) dan setLevel(n * 20); kalau n==0 berhenti.
  - c() (mulai): kalau state 300, berhenti dulu; kalau belum 400 (started), prefetch() lalu start().
  - a() (berhenti): kalau state 400, setMediaTime(0) lalu stop(). b() (tutup): close().
  - playerUpdate(): kalau deviceUnavailable → berhenti; kalau deviceAvailable → mulai lagi.
- Kapan diputar — f.aQ() baris 6565-6577 dan f.aS() baris 6604-6606:
  - aQ() memilih lagu acak dari tabel b (f = b[h*2 + random 0-1]), kalau belum ada pemutar atau lagunya beda, hentikan yang lama (aR()) dan buat new a("audio/midi") baru, lalu set volume.
  - aS() dipanggil setiap tick dari run(). Di sana: kalau Q != 27 (tidak pause) dan e==2 dan (tidak ada pemutar atau pemutar tidak sedang jalan), panggil aQ(). Field e==2 tidak bernama jelas di hasil decompile, jadi tidak bisa klaim pasti itu "pengaturan musik on" — yang pasti: musik dicek tiap tick, dan kalau tidak ada yang berbunyi, lagu acak diputar ulang. Saat pause sistem (Q=27), musik tidak dimulai ulang.

## Yang belum bisa dipastikan dari kode ini saja

- Label pasti tiap nomor Q (15,17,18,19, dsb.) dan apakah Q 24/25 itu menang atau kalah — nama-namanya hilang karena obfuscation; yang ada hanya nomor dan tabel data.
- Nilai j (interval tick mode kedua) dan arti pasti field e==2 untuk musik — nama field bertabrakan di hasil CFR.
- Isi logika dunia di b.java (5.805 baris: AI musuh, produksi, pertarungan) — itu langkah bedah berikutnya, bukan bagian alur utama ini.
