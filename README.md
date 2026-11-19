# blueberry-prehistribes_code

Riset reverse-engineering game J2ME **Prehistoric Tribes** (THQ Wireless / Gear Games, 2008, MIDP-2.0, 240x320) dengan REA + CFR.

Repo ini berisi **catatan analisis buatan sendiri**, bukan file game.

## Yang ada di repo ini

- `PETA-SISTEM.md` — peta sistem lengkap dalam Bahasa Indonesia: alur utama, game loop, dunia, bangunan, villager, combat, bahasa, level, save/load, musik, dan yang belum terjawab.
- `ANALISIS-alur-utama.md` — laporan detail alur utama (start, loading, game loop ±20 tick/detik, input, rendering, musik MIDI).

## Yang TIDAK ada di repo ini

- File `.jar` asli game
- File hasil ekstrak JAR (gambar, musik MIDI, teks, data biner)
- File Java hasil decompile mentah

Itu sengaja tidak di-upload ke repo publik karena game ini masih berhak cipta (THQ, 2008). "Abandonware" bukan status hukum — tidak ada kabar baru bukan berarti tidak ada pemilik hak.

## Cara mereproduksi analisisnya

1. Siapkan file JAR game yang kamu miliki sendiri.
2. Unzip JAR, lalu decompile class Java dengan CFR 0.152 (butuh Java 17).
3. Bandingkan hasilnya dengan peta di `PETA-SISTEM.md`.

## Ringkasan temuan

- 7 class, 13.418 baris hasil decompile: `tribes` (entry), `f` (game utama, 6.680 baris), `b` (logika dunia, 5.805 baris), `e` (loader resource), `c` (loader teks), `d` (splash), `a` (pemutar MIDI).
- Strategi desa real-time: 2 suku, maksimal 50 villager + 30 bangunan per suku, peta grid maksimal 96x96, 10 peta, 12 tipe bangunan, 4 resource (food, wood, stones, bones) + senjata.
- 5 bahasa (EN/FR/IT/DE/ES), 7 misi kampanye (tutorial wajib lulus dulu), save 3 slot RecordStore (`t0`/`t1`/`t2`), 5 lagu MIDI dalam satu file.
- Semua angka balance (biaya, HP, damage) ada di file tabel `pd0`, bukan di kode — langkah berikutnya adalah decode `pd0`.

## Lisensi / disclaimer

Analisis di repo ini adalah karya tulis sendiri untuk tujuan belajar dan riset. Game Prehistoric Tribes © 2008 THQ Wireless Inc., dikembangkan Gear Games, Ltd. Jangan gunakan repo ini untuk mendistribusikan ulang file game.
