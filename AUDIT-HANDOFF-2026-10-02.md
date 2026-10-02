# Handoff PIC jadwalkajian — 2 Oktober 2026

Dicatat PIC (sesi kerja repo `jadwalkajian`). Semua poin di bawah **diputuskan/diminta Amal langsung di chat PIC (2 Okt 2026)**; ini catatan, bukan permintaan persetujuan.

## 1. Perubahan pipeline terbit (wajib lapor)
- Jadwal mingguan Jumat 15:00 WIB (cron `0 8 * * 5`) **dihapus**. Alasan Amal: jadwal itu ada karena batas deploy saat masih di Netlify.
- Pemicu baru: **push ke `main`** yang mengubah `index.html`, `robots.txt`, `sitemap.xml`, `favicon.svg`, `og-image.png`, `scripts/**`, atau `deploy.yml`; plus manual (`workflow_dispatch`). Push yang hanya mengubah `CLAUDE.md`/`AUDIT-HANDOFF-*.md` tidak memicu run.
- `weekly-deploy.yml` diganti nama menjadi **`deploy.yml`**; nama workflow di Actions: "Prune & deploy".
- Prune + build tetap jalan di tiap run. Event lewat tetap disembunyikan di browser oleh `isEventPast`/`up()`; blok statis/JSON-LD untuk crawler bisa memuat event kedaluwarsa sampai run berikutnya (diterima Amal).
- Push bot memakai `GITHUB_TOKEN` (tidak memicu run baru, tidak ada loop). Ditambahkan `git pull --rebase origin main` sebelum push bot.
- Tidak berubah: folder `_site` (5 berkas), uji situs live, tag `last-deploy`, Settings → Pages → Source "GitHub Actions".
- Konsekuensi untuk Auditor: klaim "push tidak menerbitkan" / "tunggu Jumat" di `CLAUDE.md` repo ini sudah diganti. Bila `CLAUDE.md` repo `catatankajian`/`bikin-cv-taaruf` merujuk irama Jumat jadwalkajian, perbarui.
- Hasil run pertama dicatat di bagian 4 setelah selesai.

## 2. Perubahan skema data (wajib lapor)
- Nilai `area` baru: **`Tangerang`** (mencakup Tangerang dan Tangerang Selatan). Dipicu dua kajian Musyaffa' Ad-Dariny (Sawah Baru, BSD) yang sempat ditahan karena tidak ada area. Warna `#4fc3c9`. Diubah di `index.html` (tombol filter, `AC`, CSS) dan `scripts/build.py` (`AC`).
- Aturan baru Amal: (a) lokasi/masjid/ustadz/area yang belum ada di dashboard **harus ditambahkan**, tidak ditahan; (b) bila flyer tidak menyebut pembatasan eksplisit, `audience` = "Terbuka untuk umum".

## 3. Data (tidak wajib lapor, hanya info)
- Commit `969288c` (27 kajian 3–31 Okt dari 11 flyer) dan `f601038` (2 kajian Tangerang). Tidak dimasukkan: Masjid Jaza (Bandung, di luar area) dan semua sesi 1–2 Okt (sudah lewat).

## 4. Hasil run
- Run pertama `deploy.yml` (#1, pemicu `push`, commit `b235aa4`): id `37010091851`, **success** (13 langkah, termasuk "Uji situs live setelah terbit": percobaan 1/12, "Semua cek situs live lulus"). Tag `last-deploy` a3e9d33 -> b235aa4. Durasi ±20 detik. Run ini menerbitkan commit `969288c` dan `f601038` sekaligus (38 event aktif).
- Tidak ada commit bot pada run ini (prune/build tidak mengubah apa pun).
- Belum teruji: push-bot hasil prune dengan `git pull --rebase` (belum pernah ada perubahan prune pada run baru), dan dua push beruntun yang berdempetan. Dicatat jika muncul masalah.
- Tampilan situs live (area Tangerang, warna) belum dilihat siapa pun; sesi kerja tidak bisa mengakses github.io.

## 5. Tahap 0 sistem input Issue (instruksi Auditor, komit 467e4d8) — dikerjakan PIC 3 Okt 2026 (00:xx WIB)
Dasar eksekusi: instruksi tercatat di git (`AUDIT-HANDOFF-2026-10-02-auditor.md`), bersumber dari keputusan Amal, bagian 7 menyatakan tahap 0 boleh langsung. **Tahap 1 (templat Issue, ingest, pemicu `issues`, cron pengaman, perubahan `deploy.yml`) BELUM dikerjakan; menunggu "lanjut" Amal di chat PIC.**

### Selesai
- **Filter kota dinamis** (`index.html`): daftar tombol hardcoded dan kelas CSS per kota dihapus. Tombol diturunkan dari event yang tampil (urut abjad, `Online` terakhir). Label UI "Area:" -> "Kota:". Legenda juga dinamis. Nama bidang data tetap `area`.
- **Warna otomatis**: `cc()` di `index.html` dan `city_color()` di `scripts/build.py`, algoritma sama: FNV-1a 32-bit atas UTF-8 `"b"+nama`, hue = hash % 360; aksen `hsl(h,58%,62%)`, lencana `hsl(h,36%,25%)`, teks tombol `hsl(h,70%,88%)`. Awalan "b" dipilih agar enam nama yang ada (Depok, Bogor, Jakarta, Bekasi, Tangerang, Online) berjarak hue minimal 30 derajat. Diuji di Chromium: warna JS sama dengan Python untuk 7 nama (termasuk karakter non-ASCII), tidak ada error JS, tinggi header tetap 112 px (lebar 390).
- **Dampak tampilan yang terlihat pengunjung**: warna tiap kota berubah dari palet lama (mis. Jakarta dari ungu menjadi merah-oranye). Itu konsekuensi "warna otomatis" dari instruksi.
- **Meta description/OG/Twitter**: daftar "Depok, Bogor, Jakarta, Bekasi" dihapus (kini tidak lengkap); kalimat dasar "Jabodetabek & sekitarnya" tetap.
- **`data/kategori.json`** (internal; `_site` hanya menyalin 5 berkas, jadi tidak tayang): dibootstrap dari event sekarang + riwayat git `index.html` (18 versi terbaca). Isi: `kota` 6 (Bandung, Bekasi, Bogor, Depok, Jakarta, Tangerang), `kota_khusus` ["Online"], `masjid` 26 (nama -> kota, alamat), `pemateri` 103, `diproses` []. `Jawa Tengah`/`Jawa Barat` tidak dimasukkan (tidak pernah terpakai di data yang terbaca).
- `CLAUDE.md` PIC diperbarui: struktur (`data/kategori.json`), baris `area` (nama kota bebas, warna otomatis), aturan 4 (kajian luar Jabodetabek tetap dimasukkan, dasar: keputusan Amal di bagian 1 handoff Auditor).

### Temuan untuk Auditor
- **Format event Online di riwayat git**: ada 7 baris (id lama, `MTI Rasuna Epicentrum`) dengan `area:"Online"`, `masjid:"MTI Rasuna Epicentrum (Live YouTube)"`, `address:"Online via YouTube (MTI Rasuna Epicentrum)"`. Jadi bentuk minimal yang sudah pernah dipakai: penyelenggara + "(Live YouTube)" di kolom masjid, alamat "Online via YouTube (penyelenggara)". Bentuk ini masuk `kategori.json` sebagai satu entri masjid dengan kota `Online`; ingest tahap 1 perlu memutuskan apakah "Online" memakai nama penyelenggara bebas atau entri ini.
- **Tidak ada masjid dengan lebih dari satu (kota, alamat) di riwayat** — pernyataan Auditor "tiap masjid satu area dan satu alamat" juga berlaku untuk riwayat.
- **Pemateri 103 entri tanpa normalisasi semantik**: hanya spasi/huruf besar-kecil yang digabung. Variasi penulisan nama orang yang sama (mis. dengan/tanpa "Ustadz", gelar berbeda) tetap terpisah, dan ada entri gabungan ("... & Komunitas ..."). Dropdown 103 opsi mungkin panjang; **[Belum terverifikasi]** batas jumlah opsi dropdown Issue form. Perlu keputusan Amal/Auditor soal pembersihan sebelum tahap 1.
- **Keputusan PIC yang perlu dikonfirmasi**: kajian **Masjid Jaza, Bandung** (Qiyamul Lail, Min 4 Okt 02.30 WIB) yang sebelumnya sengaja tidak dimasukkan karena di luar area, **kini dimasukkan** (id 746, area `Bandung`) berdasarkan keputusan Amal (bagian 1 handoff Auditor + pesan Amal 2 Okt "lokasi yang belum ada harus ditambahkan"). Bila Amal tidak bermaksud mencakup Bandung, hapus id 746 dan entri `Bandung`/`Masjid Jaza` di `kategori.json`.
