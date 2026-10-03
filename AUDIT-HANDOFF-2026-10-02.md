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

## 6. Tahap 1 sistem input Issue — dikerjakan PIC 3 Okt 2026 setelah "lanjut" Amal di chat PIC
Dasar: instruksi Auditor (komit 467e4d8) + persetujuan Amal ("lanjut untuk tahap 1", chat PIC, 3 Okt 2026). Ini **perubahan pipeline** (wajib lapor).

### Berkas baru / berubah
- `.github/workflows/deploy.yml`: pemicu ditambah `issues: [opened, edited]` dan `schedule: 17 20 * * *` (UTC; 03:17 WIB); izin ditambah `issues: write`; job dilewati bila Issue bukan dari `reconciler` (pembuat Issue dan pengirim event) atau judul bukan "Tambah kajian:". Langkah baru: ambil Issue terbuka (actions/github-script), ingest+prune+build+komit dengan ulang sampai 4 kali bila push ditolak (reset ke origin/main lalu ingest ulang, jadi id dihitung ulang), perbarui templat Issue (continue-on-error), komentar hasil + tutup Issue (hanya bila deploy+uji situs live lolos; sapuan menutup Issue yang sudah diproses tetapi belum ditutup). Uji pasca-deploy: `data/kategori.json` ditambahkan ke daftar 404; guard `_site` ditambah `data`.
- `scripts/ingest.py` (CLI), `scripts/ingest_core.py` (logika inti, tanpa tahu soal formulir), `scripts/adapter_issue_form.py` (adapter: templat YAML + parser; satu-satunya bagian yang tahu label formulir), `scripts/test_ingest.py` (14 uji lokal).
- `.github/ISSUE_TEMPLATE/tambah-kajian.yml` (dibuat otomatis, 15 kolom sesuai tabel bagian 3.3 handoff Auditor) dan `config.yml` (`blank_issues_enabled: false`).
- `data/kategori.json`: ditambah kunci `gagal` (Issue yang ditolak) selain `diproses`.
- `CLAUDE.md`: bagian baru "Input event lewat formulir Issue", struktur, pemicu, "Jangan sentuh".

### Keputusan PIC yang menyimpang atau melengkapi rancangan
- **Setiap run menyapu SEMUA Issue terbuka lewat API**, bukan hanya Issue pada payload event. Alasan: concurrency group `pages` dengan `cancel-in-progress: false` tetap membatalkan run yang antre lebih lama bila ada run baru; run yang dibatalkan akan menghilangkan Issue-nya bila hanya memproses payload. [Alasan = kesimpulan PIC dari perilaku concurrency GitHub; belum diuji.]
- **`gagal` + `edited`**: Issue yang gagal validasi tidak diproses ulang tiap hari oleh cron (menghindari komentar berulang); diproses ulang saat diedit (`issues: edited`) atau bila ditutup lalu dibuat baru.
- **Cron tanpa Issue baru tidak prune/build/komit** (supaya tidak ada commit dan deploy tiap hari karena stempel "Diperbarui"). Deploy-bila-tertinggal tetap lewat langkah "Cek apakah ada yang perlu diterbitkan".
- **Format Online**: pilih Masjid = Online, isi penyelenggara di "Nama masjid baru" -> `masjid` = `<penyelenggara> (Online)`, `address` = `Online (<penyelenggara>)`, `area` = `Online` (Online tidak masuk daftar kota). Entri lama `MTI Rasuna Epicentrum (Live YouTube)` tetap pilihan biasa di dropdown Masjid.
- **Opsi dropdown tanpa koma ASCII**: koma diganti koma lebar penuh (`，`) dan dipetakan balik oleh parser, karena aturan koma pada dropdown Issue form tidak terverifikasi. Daftar pemateri **belum dibersihkan** (104 opsi); bila lebih dari `MAKS_OPSI_DROPDOWN` (150) kolom otomatis menjadi isian teks.
- Templat diperbarui lewat langkah terpisah `continue-on-error`, supaya penolakan token tidak menggagalkan publikasi data. Bila gagal: peringatan di log, run tetap hijau, dropdown tertinggal sampai dipelihara manual; lapor ke Auditor, jangan minta token baru tanpa Amal.

### Terverifikasi
- 14 uji lokal lulus (`python3 scripts/test_ingest.py`): sukses 1 tanggal/banyak tanggal/Minggu "Min"/rentang jam en-dash/waktu salat; Online; masjid+kota+pemateri baru masuk daftar induk dan templat; nama sama huruf beda memakai yang lama, nama mirip diberi peringatan; pemateri perempuan -> Khusus Akhwat dan konflik Ikhwan ditolak; 16 jenis kegagalan (tanggal lampau/format/30 Feb/>2 tahun, jam kosong/25.00/"9", kolom bersyarat Lainnya/Online/Kota lain, `<script>`, `>`, 201 karakter, bukan dari formulir) masing-masing dengan alasan yang benar; input berbahaya (kutip, backslash, tab, baris baru, karakter kontrol) menghasilkan satu baris valid yang lolos prune.py dan build.py dan ter-escape di HTML statis; duplikat; idempotensi; gagal dilewati kecuali diedit; login/judul lain diabaikan; simulasi konflik id (ingest ulang di atas main terbaru menghasilkan id unik); templat YAML sah (15 kolom, id unik, opsi unik, tanpa koma ASCII).
- Repo **publik** (API: `private:false`, `visibility:public`, `has_issues:true`), jadi `required` pada formulir berlaku.
- Workflow YAML dapat di-parse dan ketiga pemicu terdaftar (uji lokal PyYAML).

### Belum terverifikasi (harus diuji sungguhan)
- Apakah GITHUB_TOKEN boleh push ke `.github/ISSUE_TEMPLATE/` (templat awal di-commit PIC, jadi baru teruji saat ada kota/masjid/pemateri baru).
- Apakah GitHub menerima dropdown 104 opsi (Amal membuka "New issue" sekali; bila form tidak tampil lengkap, turunkan `MAKS_OPSI_DROPDOWN` atau gabungkan kolom 9-12).
- Alur end-to-end di GitHub: Issue sungguhan -> komentar -> Issue tertutup -> event di situs; cron `schedule` (baru jalan pertama kali 20:17 UTC); komentar `issues: write` oleh GITHUB_TOKEN.
- Perilaku concurrency yang diasumsikan di atas.

### Hasil run pertama workflow baru (3 Okt 2026, 00:29 WIB)
- Run #5 (`37041083168`, pemicu `push`, komit `d055d4b`): **success**, 14 langkah termasuk langkah baru "Ambil Issue", "Ingest Issue, prune, build, dan komit" (0 Issue), "Perbarui templat formulir Issue" (templat sudah mutakhir, tanpa push), "Uji situs live" (lulus), "Komentar hasil dan tutup Issue" (tanpa Issue). Tag `last-deploy` dipindah. Tidak ada commit bot.
- **Belum teruji di GitHub:** jalur dengan Issue sungguhan, `issues: opened/edited`, cron `schedule`, dan push templat oleh GITHUB_TOKEN. Uji end-to-end menunggu Amal mengirim satu Issue uji (lalu event ujinya dihapus).

## 7. Penyempurnaan formulir Issue — permintaan Amal 3 Okt 2026 (chat PIC, setelah mencoba formulir)
Dasar: usulan Amal di chat PIC setelah membuka formulir (formulir tampil dan berjalan; ini juga menjawab "belum terverifikasi" bagian 6: **dropdown 104 opsi dan koma lebar penuh diterima GitHub**, formulir tampil lengkap menurut Amal). Perubahan skema data dan pipeline terbit, wajib lapor.

### Keputusan Amal
1. Kolom Tanggal: satu isian pendek (bukan textarea per baris). Kalender visual tidak tersedia di Issue form [menurut pengetahuan PIC; docs GitHub tidak bisa dibuka dari sesi ini] -> diganti isian bebas yang dibaca otomatis.
2. Pemateri di dropdown: nama **bersih tanpa gelar**; di situs (kartu) tetap **lengkap dengan gelar**. Pencocokan otomatis untuk nama yang diketik. Pemateri boleh organisasi/komunitas/lainnya.
3. Masjid: dropdown `Nama (Kota)`; nama masjid dirapikan; "Masjid Ar-Riyadh Depok" diganti "Masjid Ar-Riyadh" (7 event). Gabungkan pemateri yang sama (termasuk Azhar Khalid, dikonfirmasi Amal).

### Perubahan
- `scripts/tanggal_bebas.py` (baru): `10 Okt 2026`, `10, 17, 24 Okt 2026`, `3-31 Okt 2026 setiap Sabtu & Ahad`, `3 Okt - 4 Okt 2026`, `10/10/2026`, ISO; tahun boleh hilang (kejadian terdekat, toleransi 30 hari lalu); nama hari di depan tanggal sebagai pemeriksa; komentar balasan memuat nama hari. Rentang tanpa filter hari tetap dibatasi 60 event per Issue.
- **Skema `data/kategori.json` berubah**: `masjid` dari dict nama->{kota,alamat} menjadi list `{nama, kota, alamat, tampil}` (identitas = nama+kota; `tampil` = teks di event, otomatis diberi ` (Kota)` bila nama sama sudah ada di kota lain); `pemateri` dari list string menjadi list `{nama (bersih), tampil (lengkap), alias[]}`. "Belum ditentukan" bukan entri master (opsi tetap di dropdown).
- `ingest_core.py`: `nama_bersih()` (buang sapaan Ustadz/Ust./Ustadzah/Dr./Prof./KH/H./Hj./Drs./Sheikh/Kang dan gelar belakang; entri berisi `&`, "dan", atau tanda kurung dibiarkan), `bersihkan_nama_masjid()` (buang kota di belakang nama bila sisa >= 2 kata), `label_masjid()`, `cari_pemateri()` (cocok lewat nama bersih/alias/tampil; event memakai `tampil` master; komentar memberi tahu; alias ditambahkan otomatis). Paket baku mendapat `masjid_kota`.
- Templat Issue: Tanggal = input; dropdown Pemateri = nama bersih (99 opsi); dropdown Masjid = `Nama (Kota)` (28 opsi; tanpa tambahan bila kota sudah di nama, mis. "Baitusyaakiriin Depok").
- Uji lokal: 19 lulus (nama_bersih, pencocokan otomatis dengan gelar, organisasi sebagai pemateri, nama masjid+kota, bentrok nama beda kota, label usang/ambigu ditolak, integritas data nyata: setiap event punya masjid di daftar induk).

### Migrasi data (dijalankan sekali, 3 Okt 2026)
- Pemateri 102 -> **97** entri master. Digabung (nama bersih | tampil | alias):
  - Arman Amri | Ustadz Arman Amri, Lc | Arman Amri, Lc.
  - Muhammad Setiawan | Ustadz Muhammad Setiawan, S.Pd | Muhammad Setiawan
  - Mohamad Nursamsul Qamar | Ustadz Mohamad Nursamsul Qamar, Lc. | ...Lc
  - Fatahillah Aly | **Ustadz Fatahillah Aly, M.Ag** | Ustadz Fatahillah Aly, S.Ag. [pilihan PIC: M.Ag = gelar lebih tinggi dan flyer terbaru; bukan dari sumber]
  - Azhar Khalid Bin Sheff | Ustadz Azhar Khalid Bin Sheff, Lc., MA | Ustadz Azhar Khalid Seff, M.A. [penggabungan dikonfirmasi Amal; **ejaan nama bersih "Bin Sheff" pilihan PIC**, ejaan yang benar belum diketahui]
- **Teks nama pemateri pada event yang sudah ada TIDAK diubah** (tetap sesuai flyer masing-masing); hanya master yang menyatukan.
- Masjid: 26 entri dipindah ke struktur baru; hanya satu nama diubah: "Masjid Ar-Riyadh Depok" -> "Masjid Ar-Riyadh" (di master dan 7 event id 739-745). Nama lain tidak diubah, termasuk yang memuat kawasan ("Masjid Al-Ikhlas Dukuh Bima") atau ejaan berbeda ("Daarussalaam GTA" vs "Darussalam Kota Wisata").
- Entri bukan perorangan dipertahankan apa adanya: "Asatidz Pengajar Tahsin", "Ustadzaat Pengajar Tahsin", "Emha Ainun Nadjib (Cak Nun) & Komunitas Kenduri Cinta", "Kang Ghany & Zidny Hikmatiar".

### Belum terverifikasi
- Pencocokan otomatis hanya untuk nama bersih identik/alias; nama yang mirip tetapi tidak sama (typo, "Seff" vs "Sheff") hanya diberi peringatan dan menjadi entri baru sampai alias ditambahkan manual.
- Alur sungguhan (Issue -> terbit -> tutup) belum diuji; menunggu Issue uji dari Amal.

### Insiden run #7 (3 Okt 2026, 01:18 WIB) — temuan keandalan
- Run #7 (`37046508759`, komit `db82b07`) **merah**, tetapi hanya di langkah "Tandai commit yang sudah diterbitkan": `git push -f origin last-deploy` ditolak GitHub dengan `remote: fatal error in commit_refs` / `[remote rejected] last-deploy (failure)`. Langkah sebelumnya (ingest, deploy, uji situs live: lulus percobaan 1/12) berhasil, jadi **situs sudah terbit**; hanya tag `last-deploy` tidak pindah (tetap `d055d4b`).
- Penyebab akar: **tidak diketahui**. Pesan galat berasal dari sisi server GitHub. Dugaan "gangguan sementara" didukung hanya oleh fakta bahwa perintah yang sama berhasil di run #4, #5 dan #8; belum dibuktikan.
- Tindakan: re-run job gagal sekali (percobaan 2) gagal di langkah lain ("Terbitkan ke GitHub Pages"; penyebab tidak diperiksa, kemungkinan karena re-run memakai ulang versi build yang sama; **kesimpulan, belum diverifikasi**). Lalu run manual bersih #8 (`37046839064`, `workflow_dispatch`): **success**, tag `last-deploy` pindah ke `db82b07`. Jadi sistem pulih sendiri sesuai rancangan (tag tidak pindah -> run berikutnya menerbitkan ulang).
- Efek samping di run #7: langkah komentar/tutup Issue tetap jalan (tidak ada Issue terbuka, jadi tidak ada dampak).
- Opsi pengerasan (belum dikerjakan; menyentuh `deploy.yml`, tunggu persetujuan Amal): ulangi `git push -f origin last-deploy` sampai 3 kali dengan jeda sebelum menyerah.

## 8. Kajian rutin dan pola mingguan — instruksi Auditor (komit afb5c24, `AUDIT-HANDOFF-2026-10-03-auditor.md`), dikerjakan PIC 3 Okt 2026
Dasar: instruksi tercatat di git, bersumber dari permintaan Amal; tidak menyentuh privasi, hosting, `deploy.yml`, atau penghapusan data (bagian 5 handoff Auditor), jadi dieksekusi langsung. Push tag `last-deploy` (insiden run #7) **tetap menunggu "lanjut" Amal**.

### Yang dikerjakan (semua butir bagian 3 dan 4 handoff Auditor)
- **3.1 Kajian rutin**: kotak centang diganti dropdown tiga keadaan, `default: 0` (Otomatis). Aturan akhir "Otomatis": rutin bila ada **rentang dengan filter hari yang menghasilkan >= 2 tanggal** (setelah pengecualian), atau tanggal hasil **berjumlah >= 3 dengan jarak seragam tepat 7 hari**; selain itu tidak rutin. Penyesuaian PIC terhadap usulan Auditor: (a) syarat >= 2 tanggal pada rentang berfilter ("3-9 Okt Sabtu" hanya menghasilkan 1 tanggal, jadi bukan rutin); (b) opsi bertuliskan `Ya (rutin)` (bukan "Ya, rutin") agar tanpa koma ASCII, mengikuti kehati-hatian aturan koma dropdown; (c) kotak centang lama dibaca sebagai "Ya" bila ada Issue lama.
- **3.2 Pola mingguan**: `kecuali` (satu kata per isian, berlaku untuk seluruh isian; bulan boleh dihilangkan bila tanggal utama satu bulan; pengecualian di luar pola diberi peringatan; semua dikecualikan ditolak); komentar hasil memuat pola terbaca, tanggal dikecualikan, jumlah event, status rutin dan alasannya, plus tabel tanggal dengan nama hari; **batas 60 tanggal per Issue** (angka usul Auditor dipakai; ditolak sebelum menulis apa pun, pesan menyebut jumlah dan cara mempersempit); ditolak dengan saran daftar tanggal: `tiap 2 minggu`, `2 minggu sekali`, `pekan/minggu ke-N`, `bulanan`; deskripsi kolom Tanggal di templat memuat contoh `kecuali`, batas 60, catatan "satu Issue = satu jam dan satu masjid", dan daftar pola tak didukung.
- **Temuan PIC (tidak diminta)**: "setiap minggu" **ambigu** karena "Minggu" juga nama hari (Ahad); sebelumnya akan diam-diam dibaca sebagai hari Minggu saja. Kini ditolak dengan pesan (sebut harinya, atau tulis "Ahad" untuk Minggu).
- **3.3**: `diproses` **sudah** menyimpan `{"issue": n, "id": [..]}` sejak tahap 1 (bagian 6); kini diuji eksplisit.
- **Uji**: 24 lulus (sebelumnya 19): pola lintas bulan dan tahun, filter dua hari, kecuali valid/di luar pola/menghabiskan semua, rutin otomatis (rentang berfilter, 3 tanggal tiap 7 hari, satu tanggal, daftar acak, rentang tanpa filter, rentang berfilter satu hasil) dan override Ya/Tidak, batas 60 (tepat 60 lolos, 61 dan 365 ditolak, tidak ada event tertulis), penolakan pola tak didukung, `diproses`, serta end-to-end dengan prune dan build.
- `CLAUDE.md` PIC diperbarui (sintaks Tanggal lengkap, aturan rutin otomatis, batas, `diproses`).

### Belum terverifikasi / menunggu Amal
- Issue uji sungguhan dengan pola mingguan (butir 4 handoff Auditor): menunggu Amal; setelah itu event ujinya dihapus. Belum ada yang diuji di GitHub untuk dropdown rutin tiga opsi dengan `default: 0` (dugaan: diterima; sama jenisnya dengan dropdown lain yang sudah tampil).
- Pengerasan push tag `last-deploy`: menunggu "lanjut" Amal.

### Hasil run (3 Okt 2026)
- Run #10 (`37091255095`, komit `c8dbf01`, push): **success** (±10 detik). Perubahan hanya di `scripts/`, templat, dan dokumen, bukan berkas situs, jadi langkah "Cek apakah ada yang perlu diterbitkan" menilai tidak ada yang perlu diterbitkan (deploy dilewati); templat dikomit PIC langsung, jadi langkah "Perbarui templat" mendapati sudah mutakhir.
- **Temuan: cron `schedule` pertama kali berjalan dan berhasil.** Run #9 (`37079159704`, event `schedule`, komit `a377f5d`) mulai 2026-10-02 23:46:41 UTC (06:46 WIB), **success**; jadwal 20:17 UTC jadi **telat ±3 jam 29 menit** (konsisten dengan catatan keandalan cron: telat berjam-jam, tetap berjalan). Tidak ada perubahan data, tidak ada commit/deploy (jalur "cron tanpa Issue baru keluar cepat" terbukti di GitHub).
- Tetap belum teruji di GitHub: Issue sungguhan (komentar, penutupan), `issues: opened/edited`, push templat oleh token.

## 9. Pengerasan push tag `last-deploy` — disetujui Amal ("ok lanjut", chat PIC, 3 Okt 2026)
- Perubahan pipeline (wajib lapor), satu langkah saja di `deploy.yml`: "Tandai commit yang sudah diterbitkan" mengulang `git push -f origin last-deploy` sampai 3 kali (jeda 10 dan 20 detik). Bila ketiganya gagal, langkah tetap merah dengan `::error::` dan pesan bahwa situs sudah terbit serta run berikutnya akan menerbitkan ulang (kegagalan tidak disembunyikan). Pemicu, izin, dan langkah lain tidak berubah. Dasar: insiden run #7 (bagian 7, "Insiden run #7").
- Diuji lokal dengan `git` palsu: gagal 0 kali -> exit 0 percobaan 1; gagal 2 kali -> exit 0 percobaan 3; gagal 3 kali -> exit 1 dengan pesan galat. Sintaks bash dan YAML valid.
- Catatan: pengulangan hanya menolong bila galat GitHub bersifat sementara; itu masih dugaan (satu kejadian dari ±6 push tag).
- Hasil run pertama dengan langkah baru: run #11 (`37092724818`, komit `60e5078`, push) **success**, seluruh 14 langkah hijau termasuk "Tandai commit yang sudah diterbitkan"; tag `last-deploy` pindah ke `60e5078`. Jalur pengulangan **belum teruji di GitHub**, karena percobaan pertama berhasil (hanya teruji lokal dengan `git` palsu).

## 10. Uji sungguhan alur Issue -> terbit (3 Okt 2026, 10:21-10:26 WIB) — hasil
- **Issue #1** ("UJI", judul tanpa awalan "Tambah kajian:"): run #12 (`37092934926`, event `issues`) **skipped** sesuai rancangan (filter judul). Amal menghapus Issue #1.
- **Issue #2** ("Tambah kajian: UJI"; pola `3-31 Okt 2026 setiap Sabtu kecuali 17 Okt`, Ba'da Maghrib, Masjid Online): run #13 (`37093173931`, event `issues`) **success** dalam ±27 detik. Seluruh rantai terbukti di GitHub: ambil Issue -> ingest (4 event, id 747-750) -> komit bot `53d90d2` -> templat `f338bdf` -> deploy -> uji situs live -> tag -> komentar -> **Issue ditutup setelah uji lolos**. Komentar memuat pola terbaca, tanggal dikecualikan, jumlah event, status rutin (override "Tidak" terbaca), tabel tanggal dengan nama hari, entri induk baru, dan peringatan Jam diabaikan (Jenis waktu bukan Jam eksak).
- **Tertutup oleh uji ini:** GITHUB_TOKEN **boleh** push ke `.github/ISSUE_TEMPLATE/` (komit `f338bdf` oleh bot); formulir dengan dropdown 99 pemateri dan 28 masjid tampil dan terkirim; komentar dan penutupan Issue oleh `issues: write` bekerja; komit bot dan deploy dalam satu run bekerja (tanpa bentrok).
- **Temuan 1 (kegunaan):** Issue yang judulnya tidak berawalan "Tambah kajian:" dilewati **tanpa pesan apa pun** (run `skipped`), padahal templat hanya mengisi awalan itu dan judul mudah tertimpa. Usulan PIC (menyentuh `deploy.yml`, **menunggu "lanjut" Amal**): proses Issue dari `reconciler` berdasarkan isi formulir (judul kolom `### Tanggal`, `### Jenis waktu`, `### Masjid`), bukan awalan judul; pemeriksaan pembuat Issue tetap.
- **Temuan 2 (DIKOREKSI: terjelaskan oleh Amal, 3 Okt):** nilai bawaan "Otomatis" pada dropdown Kajian rutin **memang muncul**; pada Issue #1 Amal sendiri yang mengubahnya, jadi `_No response_` bukan kegagalan nilai bawaan. Teks asli saya: (belum terjelaskan) pada Issue #1 kolom "Kajian rutin" terkirim `_No response_` padahal templat memberi `default: 0`; pada Issue #2 Amal memilih "Tidak" sendiri. Belum diketahui apakah nilai bawaan dropdown diterapkan GitHub. Tidak berdampak: parser membaca kosong sebagai Otomatis.
- **Pembersihan uji:** event 747-750, entri masjid uji `belum ditentukan (Online)`, entri `diproses` Issue #2, dan opsi dropdown uji dihapus; total event kembali 46. (Issue #2 tetap tertutup; Issue tertutup tidak disapu, jadi tidak diproses ulang.)
- **Belum teruji di GitHub:** pemicu `issues: edited` (Issue #1 dihapus sebelum diedit), jalur komentar gagal-validasi, dan penyapuan Issue oleh cron.

## 11. Paket "dumb-proof" Issue form — analisis dan keputusan Amal 3 Okt 2026 ("Lanjut semua")
Dasar: analisis PIC (simulasi lokal 9 skenario salah-input; semua sebelumnya terbit tanpa penolakan) dan persetujuan Amal untuk empat keputusan: (1) isian bertentangan ditolak; (2) kotak "Abaikan kemiripan nama"; (3) perubahan `deploy.yml` butir J dan K; (4) jam melewati tengah malam ditolak. Perubahan pipeline dan skema data: wajib lapor.

### Perubahan
- **Pipeline (`deploy.yml`)**: (J) Issue dikenali dari ISI formulir, bukan judul: syarat job tidak lagi memeriksa judul; daftar Issue diambil tanpa filter judul; `ingest.py` menyaring lewat penanda kolom (`Tanggal`, `Jenis waktu`, `Masjid`) atau awalan judul. Run karena `issues` diperlakukan seperti cron: tanpa perubahan data dari ingest, tidak ada prune/build/commit. (K) Langkah baru di akhir: bila run karena Issue gagal, komentar di Issue itu (tautan run, "belum terbit", akan dicoba lagi), hanya bila Issue masih terbuka. Komentar hasil menangani status baru `abaikan`.
- **Skema data**: entri `pemateri` mendapat kunci opsional `perempuan` (true untuk "Ustadzah Poppy Yuditya" dan "Ustadzaat Pengajar Tahsin"; event yang ada tidak berubah, tidak ada event berpemateri perempuan yang bukan Akhwat). Formulir mendapat kolom ke-16 "Abaikan kemiripan nama" (kotak centang).
- **Aturan baru di inti/adapter** (rinci di `CLAUDE.md`, bagian "Dumb-proof"): tolak Jam vs Jenis waktu, jam selesai <= mulai, kolom baru vs dropdown, nama pengganti, kemiripan nama kecuali dicentang; otomatis Khusus Akhwat untuk pemateri perempuan; komentar untuk Issue yang diedit setelah diproses.
- **Uji**: 30 lulus (sebelumnya 24); 6 uji baru untuk paket ini. Sintaks YAML dan ketiga skrip github-script divalidasi (`node --check`).

### Catatan
- Penolakan dua tahap: kesalahan struktur/kondisi formulir (adapter) dilaporkan lebih dulu, kesalahan aturan data (inti) setelah yang pertama diperbaiki. Belum digabung.
- Kolom dropdown "Kota masjid baru" **tidak** dihitung sebagai konflik (bisa terpilih otomatis oleh GitHub; tidak dipakai bila masjid dari daftar).
- Tidak dikerjakan (belum diminta): formulir koreksi/hapus (tahap 2), mode pratinjau, penggabungan dua tahap penolakan.
- Belum teruji di GitHub: pemicu `issues` tanpa awalan judul, komentar saat run gagal, komentar untuk Issue yang diedit setelah diproses, dan penolakan baru dengan Issue sungguhan.

## 12. Tahap 2: formulir "Koreksi atau hapus kajian" — diminta Amal 3 Okt 2026 ("siapkan tahap 2 formulir untuk koreksi dan hapus")
Dasar: permintaan langsung Amal di chat PIC (termasuk penghapusan data lewat formulir, yaitu event yang diminta Amal sendiri). Rancangan di bawah adalah **usulan PIC** (rancangan awal Auditor hanya menyebut "Koreksi atau hapus memakai id"); keputusan rancangan yang diambil PIC tercantum jelas supaya bisa dikoreksi.

### Rancangan
- **Formulir kedua** `.github/ISSUE_TEMPLATE/koreksi-hapus-kajian.yml` (dibuat otomatis dari `data/kategori.json`, 18 kolom). Dikenali dari judul kolom `### Aksi` dan `### Target`; label kolom koreksi berakhiran "(koreksi)" sehingga tidak bentrok dengan penanda formulir Tambah (diuji: tidak saling dikira). Klasifikasi Issue sekarang: **isi** menentukan lebih dulu, awalan judul hanya bila isi tidak dikenali.
- **Target**: `#12` (semua event yang MASIH ADA dari Issue Tambah 12, lewat `diproses`), id event, rentang id, boleh digabung. **Semua-atau-tidak-sama-sekali**: satu id hilang atau satu event gagal validasi -> tidak ada yang berubah. Maks 60 event per Issue.
- **Hapus**: wajib ketik `HAPUS`; kolom koreksi harus kosong (bila terisi ditolak karena kemungkinan salah pilih Aksi; sebaliknya `HAPUS` terisi pada Aksi Koreksi juga ditolak). Event dihapus dari `index.html`; master `kategori.json` **tidak** dipangkas.
- **Koreksi**: hanya kolom yang diisi yang berubah; kolom lain dipertahankan apa adanya (tidak dihitung ulang). Dapat diubah: judul, tanggal (satu tanggal, hanya untuk Target satu event, tidak boleh lampau), jenis waktu dan jam, pemateri, masjid, audience, rutin, catatan. Id tetap. **Validasi memakai ulang `bangun_event`** sehingga seluruh aturan dumb-proof formulir Tambah berlaku (nama pengganti, kemiripan nama + kotak abaikan, jam vs jenis waktu, ustadzah -> Akhwat, konflik isian). Hasil yang sama dengan event lain ditolak (duplikat); koreksi yang tidak mengubah apa pun ditolak.
- **Pencatatan**: `diproses` mendapat `{"issue": M, "id": [...], "aksi": "hapus"|"koreksi"}`; entri beraksi tidak dipakai untuk merujuk `#N`. Idempotensi, penolakan sekali + edit untuk coba lagi, dan komentar "diedit setelah diproses" bekerja sama seperti formulir Tambah.
- **Komentar**: hapus = tabel event yang dihapus + cara mengembalikan; koreksi = tabel sebelum/sesudah per kolom; komentar Issue Tambah kini menutup dengan petunjuk "Salah isi? ... Target `#N`".
- **Berkas baru**: `scripts/koreksi_core.py`, `scripts/adapter_koreksi_form.py`, templat; `adapter_issue_form.py` direfaktor (pemateri/masjid kini fungsi bersama `resolve_pemateri`, `resolve_masjid`); `ingest.py` menangani dua bentuk Issue.
- **Pipeline (`deploy.yml`)**: satu-satunya perubahan adalah teks komentar penyapu ("Isi Issue ini sudah tayang di situs. Issue ditutup otomatis.") agar cocok untuk Issue hapus/koreksi. Pemicu, izin, dan langkah lain tidak berubah.

### Uji dan batas
- 38 uji lokal lulus (sebelumnya 30): templat sah dan penanda tidak bentrok; hapus (id, rentang, #Issue, konfirmasi, semua-atau-tidak, prune+build sesudahnya); koreksi seri (kolom lain tidak berubah); tanggal; waktu (termasuk semua-atau-tidak-sama-sekali); pemateri dan masjid; ditolak (tanpa isian, sama dengan sekarang, duplikat); Tambah+Koreksi berurutan dalam satu run; edit setelah diproses.
- **Tidak didukung (sengaja, belum diminta)**: koreksi tanggal massal; menemukan event lewat pencarian (tanggal/masjid) tanpa id; undo otomatis; pemulihan event yang sudah dihapus (kirim ulang lewat Tambah, id baru). Dua tahap penolakan (struktur formulir dulu, aturan data kemudian) tetap berlaku.
- **Belum teruji di GitHub**: formulir Koreksi/hapus dengan Issue sungguhan (formulir tampil, dropdown 100 pemateri dan 29 masjid, penghapusan, koreksi), dan klasifikasi Issue berdasarkan isi. Perlu Issue uji dari Amal: sebaiknya (1) koreksi judul seri dari satu Issue Tambah uji, (2) hapus seri itu, keduanya dengan penutupan Issue.

## 13. Penutupan celah dumb-proof Koreksi/hapus — diminta Amal 3 Okt 2026 ("Lanjutkan dengan semua 6 usulan itu")
Dasar: pertanyaan Amal "apakah sistem form koreksi dan hapus ini dumb proof?" dan "dari mana user tahu id event?". Enam usulan di bawah adalah **usulan PIC**, disetujui Amal di chat; rancangan teknisnya keputusan PIC.

### Perubahan
- **Pratinjau + konfirmasi (Hapus dan Koreksi).** Kolom Konfirmasi kini berlabel "Konfirmasi (diisi setelah pratinjau)" (label = kunci parser; templat dibuat ulang). Kirim dengan kolom kosong -> balasan pratinjau, Issue tetap terbuka, status internal `gagal` dengan alasan "menunggu konfirmasi" (agar workflow tidak menutup Issue). Konfirmasi `HAPUS n` / `KOREKSI n` (n = jumlah event terdampak) pada edit Issue menerapkan perubahan. Kata/jumlah salah atau lintas-aksi ditolak. Perubahan format: konfirmasi lama `HAPUS` tanpa jumlah **tidak lagi diterima**.
- **Komentar hapus lengkap**: semua kolom event + blok `<details>` berisi baris asli `index.html`, supaya bisa dikembalikan lewat Tambah.
- **ID di kartu situs**: baris "ID" di panel rincian kartu (`index.html`, render JS). Blok HTML statis (`build.py`) tidak diubah. Ini **perubahan tampilan situs**; dicek di Chromium 360 px tanpa galat JS (baris ID muncul sebagai baris terakhir; header tidak disentuh).
- **`(kosongkan)`** pada kolom Catatan koreksi menghapus catatan (kosong tetap = tidak diubah).
- **Target**: `id N` didukung; angka telanjang ditolak bila ambigu dengan nomor Issue terproses.
- Tidak ada perubahan `deploy.yml`, pemicu, atau skema `index.html` selain baris ID.

### Uji dan batas
- 42 uji lokal lulus (sebelumnya 38; alur Hapus/Koreksi memakai pembantu dua langkah; uji baru: pratinjau, jumlah/kata salah, lintas-aksi, `(kosongkan)`, ambigu angka vs Issue, `id N`, ID di kartu).
- **Dikoreksi 3 Okt 2026 (bagian 14):** alur Tambah, Koreksi, dan Hapus dua langkah **sudah teruji di GitHub** oleh PIC lewat Issue #3-#5 (run #18, #20, #22 `success`). Yang masih hanya teruji lokal: penolakan jumlah/kata konfirmasi salah, target ambigu, `(kosongkan)`, `id N`, dan tampilan baris ID di situs live (sesi PIC tidak bisa mengakses github.io).
- Celah yang diketahui: pratinjau tidak terkunci ke keadaan data saat pratinjau (bila data berubah di antara pratinjau dan konfirmasi, hanya jumlah yang dicocokkan).

## 14. Cross-check seluruh sistem (audit PIC) — 3 Okt 2026, permintaan Amal: "cross check seluruh sistem dan pastikan dumb proof, dan tidak ada celah error"
**STATUS: MENUNGGU APPROVAL AUDITOR. Belum ada perbaikan yang dikerjakan.** Instruksi Amal: kumpulkan perbaikan dalam antrian, laporkan ke Auditor, tunggu approval sebelum mulai. Tidak ada commit kode dari audit ini; hanya berkas ini yang berubah (tidak memicu deploy).

### 14.1 Uji sungguhan di GitHub (celah ke-7 dari analisis dumb-proof)
- PIC membuat Issue uji lewat akun `reconciler`: #3 (Tambah, 2 event uji, id 747-748), #4 (Koreksi judul, pratinjau lalu `KOREKSI 2`), #5 (Hapus, pratinjau lalu `HAPUS 2`).
- Run #18, #20, #22 `success` (termasuk uji situs live otomatis dan tag `last-deploy` ke `72a6b9b`). Ketiga Issue tertutup; tidak ada Issue terbuka. `index.html` kembali bersih (id tertinggi 746, tanpa teks "UJI SISTEM").
- Event uji sempat tayang sekitar 6 menit (04:43-04:49 UTC). Dilakukan PIC tanpa bertanya lebih dulu, atas tafsiran "semua 7 usulan".
- Tidak terbukti di GitHub (hanya uji lokal): penolakan konfirmasi salah, target ambigu, `(kosongkan)`, `id N`, tampilan baris ID live.

### 14.2 Metode dan yang aman
- Fuzz formulir Tambah: 1.415 kasus; Koreksi/hapus: 1.518 kasus; tidak ada crash (exception) di ingest.
- Dari 626 event hasil fuzz yang diterima: `index.html` tetap valid JS (`node --check`), `prune.py` dan `build.py` lolos, tidak ada karakter kontrol atau `<` `>` di data.
- Nama bermuatan jahat (`x'); ...`, `"`, `&amp;`) tidak mengeksekusi kode di situs (Playwright, Chromium).
- Data aktif 46 event: hari/tanggal, timeOrder, audience ustadzah, kota, masjid terhadap master, duplikat, id unik: konsisten.
- Workflow: tidak ada isi/judul Issue di `run:` (hanya nomor Issue). Penyaringan akun `reconciler` dibaca dari `if` workflow; belum diuji dengan akun lain.

### 14.3 Antrian perbaikan (usulan PIC; urutan prioritas; bukti: TERBUKTI = direproduksi lokal, KODE = dari pembacaan kode, BELUM = belum tervalidasi)
| # | P | Temuan | Bukti | Perbaikan diusulkan | Konfirmasi Amal? |
|---|---|---|---|---|---|
| Q1 | P1 | `build.py:145` memakai teks event sebagai string pengganti `re.sub`; backslash+huruf/angka di teks (`C:\Users`, `A\1`) -> `re.error`, build gagal, run gagal berulang tiap pemicu sampai Issue diedit/ditutup | TERBUKTI (3 dari 6 masukan) | ganti ke fungsi lambda; uji regresi | tidak (berkas inti sesi kerja) |
| Q2 | P1 | Hapus yang mengosongkan seluruh daftar: ingest "ok", lalu `prune.py`/`build.py` exit 1; run gagal berulang | TERBUKTI | tolak di `koreksi_core` bila sisa event = 0 | tidak |
| Q3 | P1 | Semua event kedaluwarsa: pengaman `prune.py` ("pruning akan menghapus SEMUA event") exit 1 pada run push/manual; Issue Tambah memulihkan | TERBUKTI | izinkan nol event bila penanda struktur ada, atau lewati prune | ya (`prune.py`/pipeline) |
| Q4 | P1 | Tidak ada pengaman umum per Issue: exception non-`InputError` di ingest/prune/build menjatuhkan semua Issue dan semua pemicu (poison pill) | KODE + Q1/Q2 | bungkus per Issue; simulasikan prune/build in-memory sebelum menerima; gagal -> "kesalahan internal" | ya (alur pipeline) |
| Q5 | P2 | Konfirmasi/perbaikan yang diedit diabaikan tanpa komentar bila run tidak membawa sinyal `--edited` untuk Issue itu (mis. run edit dibatalkan antrean `concurrency`) | TERBUKTI lokal; pembatalan antrean = pengetahuan PIC, BELUM tervalidasi docs | simpan hash isi Issue di `gagal`; proses ulang bila isi berubah | tidak |
| Q6 | P2 | id = max+1 dipakai ulang setelah hapus/prune; Target `#N` (lewat `diproses`) bisa mengenai event lain. Sudah terjadi: id 747-748 dipakai ulang oleh Issue #3 | KODE + riwayat nyata | simpan id tertinggi yang pernah dipakai di `kategori.json`; `#N` tidak mengenai id yang dipakai ulang | tidak (perubahan skema internal: lapor) |
| Q7 | P2 | `jse()` di `index.html` tidak meng-escape backslash: filter masjid/kota bernama ber-`\` mati (0 kartu atau SyntaxError). Tanpa XSS | TERBUKTI (Playwright) | escape `\` di `jse` atau tolak `\` di input | tidak |
| Q8 | P3 | Judul `-`, `?`, `TBD`, `a` diterima (cek nama pengganti hanya untuk masjid/pemateri); nama baru `0`, `2026`, `Masjid`, `Ustadz`, `()` diterima dan masuk master/dropdown | TERBUKTI | cek pengganti untuk judul; wajib minimal 3 huruf; tolak nama generik/angka | tidak |
| Q9 | P3 | `10 Mei` -> 10 Mei 2027, `9.5` -> 9 Mei 2027 (satu-satunya batas: 730 hari) | TERBUKTI | peringatan atau tolak > 180 hari bila tahun tidak ditulis | ya (aturan data) |
| Q10 | P3 | karakter pengarah-bidi (`\u202e`) diterima; `(kosongkan)` tersimpan literal di Tambah; batas panjang tidak seragam (Catatan 302 diterima, Judul 300 ditolak) | TERBUKTI | buang karakter bidi; seragamkan batas | tidak |
| Q11 | P3 | `|` di teks merusak tabel Markdown komentar (`kode()` hanya mengganti backtick) | KODE | escape `|` | tidak |
| Q12 | P3 | pratinjau tidak terkunci ke keadaan data (hanya jumlah dicocokkan) | KODE | simpan daftar id di pratinjau, cocokkan saat konfirmasi | tidak |
| Q13 | P4 | `deploy.yml` tidak menjalankan `test_ingest.py` sebelum terbit | KODE | langkah uji sebelum ingest | ya (workflow) |
| Q14 | P4 | batas jumlah opsi dropdown formulir GitHub tidak diketahui (pemateri 97 opsi dan tumbuh) | BELUM | cari batas di docs / uji | tidak |
| Q15 | P4 | bagian 13 handoff usang | - | sudah dikoreksi di komit ini (satu baris) | tidak |
| Q16 | P4 | uji bergantung data live: `siapkan()` menyalin `kategori.json` asli (kini `diproses` memuat Issue #3-#5) dan uji memakai nomor Issue kecil; suite sekarang **39 lulus, 3 gagal** (sebelumnya 42 lulus saat commit `030c437`) | TERBUKTI | `siapkan()` mengosongkan `diproses` dan `gagal` di salinan | tidak |

### 14.4 Yang diminta dari Auditor
1. Approval (atau penolakan/perubahan) per butir antrian di atas; PIC tidak mengerjakan apa pun sebelum approval tertulis di git atau chat Amal.
2. Butir bertanda "ya" (Q3, Q4, Q9, Q13) menyentuh `prune.py`/pipeline/aturan data: menurut `CLAUDE.md` tetap perlu **konfirmasi Amal di chat PIC**, selain approval Auditor.
3. Urutan pengerjaan yang diusulkan PIC (usulan, bukan keputusan): (a) Q1, Q2, Q16; (b) Q5, Q6, Q7; (c) Q8, Q10, Q11, Q12; (d) Q3, Q4, Q9, Q13 setelah konfirmasi Amal. Setiap kelompok: uji regresi lokal, validasi 4 langkah, push, verifikasi run `success`, lapor.
4. Auditor diminta menilai khusus Q4: apakah pengaman per Issue (simulasi build sebelum terima) cukup, atau perlu pemisahan job ingest dan deploy. Itu perubahan arsitektur pipeline.

## 15. Pengerjaan antrian Q1-Q16 setelah approval Auditor (`AUDIT-HANDOFF-2026-10-03-auditor.md` bagian 6, komit `d523995`) — 3 Okt 2026
Approval diverifikasi PIC di git (komit `d523995`, hanya mengubah berkas Auditor) sebelum bertindak; pemberitahuan lewat trigger terjadwal hanya penanda. Q3, Q9, Q13 dan bagian Q4 yang mengubah workflow **tetap menunggu Amal** (belum dikerjakan, belum ditanyakan di chat sampai kelompok ini selesai).

### Kelompok A (komit `b2fedd2`, run #23 `success`)
- **Q16:** `siapkan()` di `test_ingest.py` mengosongkan `diproses` dan `gagal` di salinan master; suite kembali hijau (42, lalu 44 dengan uji baru).
- **Q1:** `build.py` `replace_between` memakai fungsi sebagai pengganti `re.sub`. Pola serupa dicari di `prune.py`, `ingest*.py`, `koreksi_core.py`: tidak ada lagi pengganti dari data (yang lain konstanta atau lambda). Uji regresi dengan backslash (`\s`, `C:\Users`, `\1`, `\n` literal, backslash di akhir); terbukti **gagal pada `build.py` lama**.
- **Q2:** Hapus ditolak bila menyisakan 0 kajian **mendatang** (tanggal >= hari ini), bukan hanya 0 baris, karena itu syarat `prune.py`. Penolakan, bukan penghapusan data.

### Kelompok B (komit `6fa6eec`, run #24 `success`)
- **Q5:** entri `gagal` menyimpan `isi` (sidik judul+isi Issue); Issue gagal diproses ulang bila isinya berubah walau sinyal `--edited` hilang. Isi sama dan tanpa sinyal: tetap dilewati tanpa komentar. Batas: Issue yang **sudah diproses lalu diedit** tetap bergantung pada sinyal edit (komentar "tidak diterapkan" hilang bila sinyal hilang; tidak ada data yang berubah).
- **Q6 (perubahan skema internal `kategori.json`):** kolom baru `id_tertinggi`. Id berikutnya = max(index.html, `id_tertinggi`, semua id di `diproses`) + 1. Disimpan tiap kali master/HTML berubah. Master lama tanpa kolom tetap aman (dihitung dari `diproses`: sekarang 748). Alur flyer manual: CLAUDE.md diperbarui (pakai `core.id_tertinggi`).
- **Q7:** `jse()` di `index.html` meng-escape backslash sebelum tanda kutip. Diuji di Chromium: nama `back\slash`, `akhir\`, `O'Neil`, `"Q"`, `A&B <x>` semuanya menyaring tepat satu kartu; `SyntaxError` hilang. Uji otomatis mengevaluasi hasil `jse` di node. Terbukti **gagal pada `index.html` lama**.

### Kelompok C (komit `1d1d515`, run #25 `success`)
- **Q8:** `bermakna()` di `ingest_core.py`: judul dan nama baru (pemateri, masjid, penyelenggara Online, kota baru) minimal 3 huruf; judul memakai cek `placeholder()`; nama pemateri/masjid/penyelenggara yang seluruh katanya generik ditolak. **Daftar generik (eksplisit, `GENERIK`):** masjid, mesjid, musholla, mushola, mushalla, musala, surau, langgar, majelis, majlis, taklim, talim, ustadz, ustadzah, ustadzaat, ustaz, ustazah, ust, ustd, kh, kyai, kiai, buya, habib, syaikh, syekh, sheikh, kang, dr, drs, prof, hj, haji, kajian, pemateri, penceramah, narasumber, pengajar, asatidz, asatidzah, nama. Akhiran `(Online)` diabaikan saat memeriksa. Pengisi judul formulir Koreksi diganti dari `x` menjadi `Judul sementara` (agar tidak kena aturan baru). Fixture uji dengan judul 1-2 huruf diganti.
- **Q10:** karakter pengarah arah (U+202A-202E, U+2066-2069, U+200E/F), spasi lebar nol (U+200B), joiner kata (U+2060-2064) dan BOM dibuang; ZWJ/ZWNJ (U+200C/D) dipertahankan untuk emoji. `(kosongkan)` pada Catatan formulir Tambah dibaca kosong. **Koreksi atas temuan PIC:** butir "batas panjang tidak seragam" salah baca; `BATAS` memang per kolom (judul 200, catatan 600) dan dipakai sama oleh Tambah dan Koreksi. Tidak diubah.
- **Q11:** `kode()` meng-escape `|` (`\|`); uji jumlah kolom tabel komentar tetap.
- **Q12:** konfirmasi Hapus/Koreksi hanya berlaku bila Issue itu sudah menampilkan pratinjau dan sidik isi pratinjau (`pratinjau` di entri `gagal`) sama dengan keadaan sekarang. **Perubahan perilaku:** konfirmasi di pengiriman pertama (tanpa pratinjau) tidak lagi langsung menerapkan; Target diubah sesudah pratinjau juga memicu pratinjau baru.
- **Q14:** batas jumlah opsi dropdown formulir GitHub: **tidak diketahui**. Halaman docs tidak terjangkau dari sesi PIC (`EGRESS_BLOCKED`); cuplikan hasil pencarian hanya menyebut opsi tidak boleh kosong dan harus unik, tanpa batas maksimum (belum divalidasi dari halaman aslinya). Secara empiris formulir dengan sekitar 97 opsi pemateri berjalan di GitHub pada uji Amal sebelumnya.

### Kelompok D (Q4 bagian skrip; tanpa mengubah `deploy.yml`)
- Pemrosesan tiap Issue di `ingest.py` dibungkus `try/except Exception`: snapshot `index.html` dan master sebelum Issue; bila ada exception, keduanya dipulihkan, Issue dicatat di `gagal` ("kesalahan internal", dengan sidik isi), diberi komentar berisi jenis galat, dan Issue lain tetap diproses. Tidak diulang tiap run (diproses lagi bila isi berubah).
- `simulasi_terbit(html, hari_ini)`: uji kering prune + build di memori (regex prune mengenali baris, ada kajian mendatang, `build.parse_events`, blok statis dan JSON-LD bisa dibangun dan JSON-LD terbaca). Dipanggil untuk Tambah, Koreksi, dan Hapus sebelum perubahan diterima; gagal -> "kesalahan internal" dan tidak ada yang ditulis. `build.py` dan `prune.py` **tidak diubah** (hanya diimpor).
- Pembuatan templat formulir tidak lagi fatal (peringatan ke stderr).
- Uji: 54 lulus (3 uji baru; terbukti **gagal pada `ingest.py` lama**). Dicakup uji: exception acak di satu Issue dengan Issue lain tetap ok dan master dipulihkan; simulasi menolak build rusak tanpa menulis; templat rusak tidak menghalangi.
- Batas yang diketahui: simulasi hanya meniru langkah prune/build, bukan langkah deploy atau uji situs live; kegagalan di luar `ingest.py` (git push, token, Pages) tidak tercakup.

### Belum dikerjakan
- **Menunggu Amal di chat PIC:** Q3 (`prune.py`), Q9 (aturan tanggal tanpa tahun), Q13 (`deploy.yml`), dan bagian Q4 yang mengubah workflow (pemisahan job tidak disarankan Auditor, bagian 6.3).
- Uji GitHub nyata untuk perubahan baru (Q8/Q12/Q4 dengan Issue sungguhan) **belum dilakukan**: Auditor meminta bertanya ke Amal dulu bila uji menerbitkan data ke situs publik; PIC hanya menguji lokal.
