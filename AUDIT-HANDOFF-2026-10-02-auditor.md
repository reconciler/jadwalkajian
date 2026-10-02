# Audit handoff — 2026-10-02 (Auditor): sistem input event lewat formulir Issue GitHub

Dari: sesi "Auditor Project" (`session_01V7K2gPxpghoLSqB74zsXWV`)
Untuk: sesi PIC `jadwalkajian`

Penanda: **[Terverifikasi]** = diperiksa langsung Auditor (git, API, data).
**[Usulan Auditor]** = rancangan Auditor, belum divalidasi sumber luar.
**[Belum terverifikasi]** = harus diuji PIC.

## 1. Keputusan Amal (2 Okt 2026)

- Jalur input: **formulir Issue GitHub** (tanpa Google Form, tanpa Apps Script,
  tanpa token tambahan). Hanya Amal yang menginput.
- Tanggal: satu tanggal per baris. Catatan: opsional.
- Kategori konsisten sebagai **kota**: dropdown hanya memuat kota; kajian di luar
  daerah mengisi nama kotanya. **"Online" dipertahankan** sebagai pilihan khusus.
- Dropdown untuk kategori terbatas; kategori baru bisa ditambah lewat form tanpa
  campur tangan Claude.
- Hosting tetap publik. Deploy kapan saja (tanpa irama Jumat).
- Disetujui satu **cron pengaman harian** (lihat bagian 6). `CLAUDE.md` bagian
  "Jangan sentuh" sudah disesuaikan oleh Auditor.
- Syarat Amal: event yang masuk harus **pasti terbit**; waktu tunggu lama tidak masalah.
- Arsitektur harus mudah diganti ke jalur input lain (Google Form) kelak: semua
  logika di skrip ingest bermasukan satu format baku; hanya adapter yang berbeda.

## 2. Fakta kondisi saat ini

- **[Terverifikasi]** 45 event; 16 masjid; setiap masjid tepat satu `area` dan satu
  `address` (tanpa pengecualian). Semua `area` terpakai sudah berupa kota
  (Jakarta, Depok, Bogor, Bekasi, Tangerang). `Jawa Tengah`, `Jawa Barat`, `Online`
  terdaftar tetapi tidak terpakai sekarang. `note` terisi di semua event.
- **[Terverifikasi]** Daftar area terkunci di: `index.html` (tombol baris ~124–131,
  `AC` baris ~138, daftar di `render()` baris ~205) dan `scripts/build.py` (`AC`
  baris ~37–44; cabang `Online` baris ~113–114). `prune.py` tidak punya daftar area.
- **[Terverifikasi]** Prune menghapus event lewat, jadi daftar masjid/area yang
  diturunkan dari `allEvents` ikut menyusut. Karena itu perlu **daftar induk**
  terpisah (bagian 3.2).
- **[Terverifikasi]** Aktor workflow pemilik repo: login GitHub `reconciler`.
- **[Terverifikasi]** Push bot dengan `GITHUB_TOKEN` tidak memicu workflow lain
  (tercatat di `CLAUDE.md` PIC). Ingest dan deploy harus satu run.

## 3. Komponen

### 3.1 Dashboard: kota dinamis (tahap 0, berdiri sendiri)

- Tombol filter kota diturunkan dari data (seperti filter masjid yang sudah dinamis).
- Warna kota dibuat otomatis dari palet, stabil per nama, algoritma **sama** di
  `index.html` dan `build.py`.
- `Online` tetap dikenali lewat namanya (jalur schema.org `OnlineEventAttendanceMode`).
- Label UI "Kota". Nama bidang data tetap `area`. Hapus daftar hardcoded di atas.
- Perbarui teks meta yang menyebut "Depok, Bogor, Jakarta, Bekasi" bila perlu.

### 3.2 Daftar induk `data/kategori.json` (internal, TIDAK masuk `_site`)

- Isi: `kota` (daftar nama + `Online` khusus), `masjid` (nama → kota, alamat),
  `pemateri` (daftar nama, termasuk "Belum ditentukan"), `diproses` (nomor Issue
  yang sudah diproses + `id` event yang dihasilkan, untuk idempotensi).
- **Bootstrap:** dari event sekarang **ditambah riwayat git** `index.html`
  (masjid/pemateri yang sudah terhapus prune). Buang `Jawa Tengah`/`Jawa Barat`
  dari daftar kota. Untuk format event `Online`, periksa riwayat git; bila belum
  pernah ada, usulkan bentuk minimal (mis. penyelenggara di kolom masjid) dan
  laporkan di handoff.
- Daftar ini sumber dropdown; ingest menambah entri baru ke sini.
- Perbarui daftar `INTERNAL` di uji pasca-deploy bila berkas internal baru perlu
  dicek 404 (`data/kategori.json` tidak ikut `_site`).

### 3.3 Templat `.github/ISSUE_TEMPLATE/tambah-kajian.yml` + `config.yml`

- `config.yml`: `blank_issues_enabled: false`. `title:` templat berawalan "Tambah kajian:".
- Templat **dibuat ulang oleh ingest** dari daftar induk di setiap run (dropdown
  selalu mutakhir). **[Belum terverifikasi]** token bawaan workflow boleh mengubah
  `.github/ISSUE_TEMPLATE/` (yang dilarang hanya `.github/workflows/`). Uji lebih
  dulu dengan perubahan sepele. Bila ditolak: dropdown dipelihara manual oleh PIC
  dan laporkan ke Auditor (jangan meminta token baru tanpa Amal).
- Label kolom = kunci parsing (Issue menyajikan jawaban di bawah heading `### label`).
  **Jangan ubah label tanpa mengubah parser.**

| # | Label (persis) | Jenis | Wajib | Pilihan / aturan |
|---|---|---|---|---|
| 1 | Tanggal | textarea | ya | satu per baris, `YYYY-MM-DD` |
| 2 | Jenis waktu | dropdown | ya | Jam eksak; Dhuha; Ba'da Subuh; Ba'da Zuhur; Ba'da Ashar; Ba'da Maghrib |
| 3 | Jam | input | tidak | hanya untuk Jam eksak: `09.30` atau `09.30-11.00` |
| 4 | Judul | input | ya | |
| 5 | Pemateri | dropdown | ya | daftar induk + "Belum ditentukan" + "Lainnya (tulis di bawah)" |
| 6 | Pemateri baru | input | tidak | wajib bila memilih Lainnya |
| 7 | Pemateri perempuan | checkboxes | tidak | satu opsi; bila dicentang `audience` = `Khusus Akhwat` |
| 8 | Masjid | dropdown | ya | daftar induk + "Online" + "Lainnya (tulis di bawah)" |
| 9 | Nama masjid baru | input | tidak | wajib bila Lainnya |
| 10 | Alamat masjid baru | input | tidak | wajib bila Lainnya |
| 11 | Kota masjid baru | dropdown | tidak | daftar kota + "Kota lain (tulis di bawah)" |
| 12 | Kota lain | input | tidak | wajib bila memilih Kota lain |
| 13 | Audience | dropdown | ya | Terbuka untuk umum (bawaan); Khusus Akhwat; Khusus Ikhwan |
| 14 | Kajian rutin | checkboxes | tidak | satu opsi |
| 15 | Catatan | textarea | tidak | opsional |

- Kolom yang bersyarat ("hanya bila Lainnya") **divalidasi di ingest**, bukan di form
  (form tidak punya logika kondisional).
- **[Belum terverifikasi]** tidak ditemukan batas jumlah kolom di dokumentasi.
  Pastikan templat tampil lengkap (Amal membuka "New issue" sekali). Bila ada
  batas, gabungkan kolom 9–12 menjadi satu textarea berformat baku.
- `required` pada form hanya berlaku di repo publik. Ingest harus tetap memvalidasi
  semuanya sendiri.

### 3.4 `scripts/ingest.py`

Alur: baca isi Issue **dari berkas event (`$GITHUB_EVENT_PATH`) atau variabel
lingkungan, bukan interpolasi di `run:`** → adapter mengubah ke paket baku →
validasi → tambah event → perbarui daftar induk → prune/build → keluarkan ringkasan.

- **KEAMANAN (wajib):** jangan pernah menulis `${{ github.event.issue.body }}` atau
  `title` langsung di `run:` (injeksi skrip). Teruskan lewat `env:` atau baca berkas.
- Tulis baris event dengan serialisasi aman (mis. `json.dumps(ensure_ascii=False)`),
  satu event satu baris, awalan tetap `{id:<angka>,date:"YYYY-MM-DD"` (aturan 6).
  Escape HTML untuk blok statis; tolak/bersihkan karakter kontrol dan `</script>`;
  batasi panjang tiap kolom.
- Per tanggal pada kolom Tanggal dibuat satu event dengan kolom lain sama.
- Hitung otomatis: `id` (max+1, **hitung ulang setelah rebase**), `dayShort`
  (Minggu "Min"), `timeLabel` (`09.30 – 11.00 WIB` dengan en-dash, atau label salat),
  `timeOrder` (aturan di `CLAUDE.md`).
- Aturan: pemateri perempuan → `Khusus Akhwat`; audience bawaan `Terbuka untuk umum`.
- Validasi mekanis: format tanggal/jam, tanggal lampau (laporkan, jangan tambahkan),
  konsistensi "Lainnya", duplikat (tanggal + masjid + jam + judul), nama baru yang
  cocok tanpa memperhatikan huruf besar/kecil dengan daftar induk (pakai yang lama),
  nama baru yang **mirip** (beri peringatan di komentar, tetap diproses).
- Idempotensi: nomor Issue yang sudah ada di `diproses` dilewati.
- Aturan lama "hanya Jabodetabek" sudah tidak menjadi syarat otomatis; kategori
  baru selalu diterima (aturan 7 `CLAUDE.md`).
- **Adapter terpisah** dari logika inti, agar jalur lain (Google Form) bisa ditambah
  kelak tanpa mengubah ingest.

### 3.5 Workflow `deploy.yml` (pipeline: perlu "lanjut" Amal, lihat bagian 7)

- Tambah pemicu `issues: types: [opened]`. Jalankan hanya bila
  `github.event.issue.user.login == 'reconciler'` dan judul berawalan "Tambah kajian:".
  Issue dari akun lain: abaikan tanpa membalas.
- Izin: `contents: write`, `issues: write`, `pages: write`, `id-token: write`.
- Langkah: checkout → ingest → prune/build → komit ke `main` (rebase dan ulang bila
  push ditolak) → deploy → uji pasca-deploy → komentar hasil → tutup Issue.
- Komentar sukses memuat daftar event + `id`, kategori baru yang dibuat, peringatan.
  Komentar gagal memuat alasan; **Issue tetap terbuka**.
- **Issue hanya ditutup setelah uji pasca-deploy lolos** (terbuka = belum terbit).
- Hanya action resmi `actions/*`. Concurrency satu antrean `pages`, tanpa pembatalan.

## 4. Menjamin event pasti terbit

1. Ingest, komit, deploy, dan uji dalam satu run; Issue ditutup hanya bila lolos.
2. **[Terverifikasi di `CLAUDE.md`]** tag `last-deploy` tidak dipindah bila uji gagal,
   sehingga deploy berikutnya menerbitkan ulang. Tidak ada data yang terlewat.
3. Cron pengaman harian (bagian 6) menutup celah "tidak ada pemicu berikutnya".

## 5. Tahapan

| Tahap | Isi | Perlu "lanjut" Amal? |
|---|---|---|
| 0 | Kota dinamis (3.1) dan daftar induk (3.2). Tidak mengubah `deploy.yml`. | Tidak |
| 1 | Templat, ingest, pemicu `issues`, komentar/tutup Issue, cron pengaman (3.3 sampai 3.5, bagian 6) | **Ya** (perubahan pipeline) |
| 2 (nanti) | Formulir "Koreksi atau hapus" memakai `id`; pola mingguan | Belum diminta |

## 6. Cron pengaman (disetujui Amal 2 Okt 2026)

- Satu jadwal **harian**, jam di luar jam sibuk dan bukan menit 00 (usul
  `17 20 * * *` UTC, sekitar 03:17 WIB; PIC boleh memilih lain). Ingat cron memakai **UTC**.
- Tugas: (a) deploy bila `last-deploy` tertinggal dari `main`; (b) proses Issue
  terbuka milik `reconciler` yang belum ada di `diproses` (menangkap kejadian
  `issues` yang hilang); (c) selain itu keluar cepat tanpa mengubah apa pun.
- **[Terverifikasi]** cron GitHub pernah telat 5 jam 34 menit di repo ini (25 Sep)
  tetapi tetap berjalan; keterlambatan hanya berarti event terbit lebih lambat.
- **[Hasil pencarian dokumentasi, belum diuji di sini]** jadwal nonaktif bila repo
  publik 60 hari tanpa aktivitas. Repo ini aktif, jadi risikonya kecil.

## 7. Prosedur dan pengujian

- Tahap 0 boleh langsung dikerjakan (aturan "Eksekusi instruksi Auditor").
- Tahap 1 menyentuh `deploy.yml` dan pemicu: **menunggu "lanjut" Amal di chat PIC**.
- Uji lokal sebelum push: jalankan `ingest.py` pada contoh isi Issue untuk jalur
  sukses, banyak tanggal, tiap jenis kegagalan, input berbahaya (`</script>`, tanda
  kutip, baris baru), dan duplikat. Simulasikan konflik `id` setelah rebase.
- Uji sungguhan: Amal membuka "New issue" dan mengirim satu event uji; verifikasi
  komentar, penutupan Issue, event di situs; lalu hapus event uji. Jalankan juga
  cron secara manual satu kali.
- Verifikasi bahwa repo publik (agar `required` berlaku) dan laporkan.
- Perbarui `CLAUDE.md` PIC (alur kerja, skema `area` = kota, daftar induk, cara
  menambah kota/masjid/pemateri lewat form) dan catat hasil di handoff PIC.

## 8. Yang tidak berubah

- Alur "screenshot flyer ke Claude" tetap berlaku untuk ekstraksi dari gambar.
- Aturan data di `CLAUDE.md` (duplikat, tanggal lampau, ustadzah → Akhwat) tetap;
  sekarang sebagian ditegakkan otomatis oleh ingest.
