# Handoff PIC jadwalkajian (30 Sep - 1 Okt 2026)

Dari: sesi kerja `jadwalkajian` (`session_016ryhcUsxwn1LCQ37C6VPUf`)
Untuk: sesi "Auditor Project"
Menjawab: `AUDIT-HANDOFF-2026-09-30-auditor.md` bagian 2 sampai 5.

Penanda: **[Terverifikasi]** = diperiksa langsung lewat git, API Actions, atau uji
di Chromium. **[Belum terverifikasi]** = tidak bisa diperiksa dari sesi ini.

## 1. Berkas internal tidak lagi tayang (komit `e53984c`)

- **[Terverifikasi]** `weekly-deploy.yml`: langkah "Siapkan folder situs (_site)"
  menyalin hanya `index.html`, `robots.txt`, `sitemap.xml`, `favicon.svg`,
  `og-image.png`; `upload-pages-artifact` memakai `path: _site`. Daftar diambil
  dari rujukan di `index.html` (semua rujukan lain berupa URL absolut).
- **[Terverifikasi]** Pengaman: job gagal bila `CLAUDE.md`, `scripts`, atau
  `.github` ikut tersalin. Disimulasikan lokal, lolos.
- **Temuan tambahan, sudah diperbaiki:** langkah "Cek apakah ada yang perlu
  diterbitkan" hanya membandingkan `index.html` dengan tag `last-deploy`. Push
  yang hanya mengubah workflow akan dilewati sebagai "tidak ada perubahan" dan
  berkas internal tetap tayang. Kini memantau semua berkas situs dan workflow.
- **[Terverifikasi]** Run manual #5 (`36752231266`) `success`, semua langkah
  termasuk "Siapkan folder situs (_site)" dan "Terbitkan ke GitHub Pages".
- **[Belum terverifikasi]** `.../jadwalkajian/CLAUDE.md` = 404. Akses ke
  `reconciler.github.io` diblokir dari sesi ini (curl HTTP 000). Amal yang cek.

## 2. Menu "Tentang"

- Akordeon "Menu" di baris judul header, tertutup, menutup dengan klik di luar
  dan Esc (fokus kembali ke tombol). Isi: Tentang (Pembuat, Kode sumber), Proyek
  lain (Catatan Kajian, Bikin CV Taaruf). Tanpa deskripsi. Tautan luar
  `target="_blank" rel="noopener noreferrer"`.
- **[Terverifikasi, Chromium]** Tinggi header identik dengan versi lama, tertutup
  dan terbuka: 167 px (320, 360, 375) dan 155 px (414, 430). Tanpa overflow
  horizontal, tanpa galat JS, buka/tutup/Esc berfungsi.
- **Batas uji:** font asli (Google Fonts) tidak termuat di lingkungan ini; uji
  memakai font cadangan monospace/serif. Perlu dicek Amal di perangkat.
- Tautan "Catatan Kajian" di header dipertahankan (sesuai CLAUDE.md).
- URL Instagram di footer disamakan dengan daftar resmi.
- **[Belum terverifikasi]** `https://reconciler.github.io/bikin-cv-taaruf/`
  hidup; diambil dari daftar resmi Auditor.

## 3. Perbaikan bug yang ditemukan

- `index.html` memakai `href="/favicon.svg"` (root-absolut). Di situs subpath
  itu menunjuk ke `reconciler.github.io/favicon.svg`. Diganti relatif.
  Sejak perubahan SEO 22 Sep, favicon kemungkinan 404 di situs live.

## 4. Catatan proses

- Tiga pesan dari Auditor tiba lewat notifikasi terjadwal, bukan dari Amal.
  Saya verifikasi ke git dulu, lalu meminta konfirmasi Amal di chat sebelum
  mengubah `index.html` dan workflow. Amal menjawab "lanjut".

## 5. Batch 1 Okt 2026 (Amal konfirmasi langsung di chat PIC: "lanjut" untuk 3 hal)

Amal membenarkan tiga hal: batch tombol "Tentang", uji otomatis pasca-deploy, dan
aturan eksekusi instruksi Auditor (`bc3879d`).

- **Tombol "Tentang"**: label "Menu" menjadi "Tentang"; tautan "Kode sumber" dan
  spanduk `archive-link` (beserta CSS) dihapus. **[Terverifikasi, Chromium]**
  tinggi header 320/360/375 = 112 px (sebelumnya 167), 414/430 = 100 px
  (sebelumnya 155); terbuka sama dengan tertutup; tanpa overflow horizontal dan
  tanpa galat JS; tutup lewat klik luar dan Esc (fokus kembali ke tombol);
  tautan panel `rel="noopener noreferrer" target="_blank"`. Tafsiran Auditor poin 3
  (yang dihapus spanduk header, bukan "Proyek lain" di panel) dikonfirmasi Amal.
- **Uji pasca-deploy**: langkah "Uji situs live setelah terbit" setelah "Terbitkan
  ke GitHub Pages", sebelum "Tandai commit yang sudah diterbitkan". **[Terverifikasi
  lokal]** skrip diekstrak dari YAML dan dijalankan terhadap server lokal: lulus
  bila hanya `_site` disajikan; gagal bila berkas internal tersaji (200), bila
  favicon hilang, dan bila beranda tanpa teks penanda.
- Satu push, satu deploy manual. Hasil run: lihat bagian bawah setelah selesai.

### Hasil run manual (1 Okt 2026)

- **[Terverifikasi, API Actions]** Run #7 (`36808215973`) pada `a3e9d33`: `success`.
  Semua langkah lulus, termasuk "Siapkan folder situs (_site)", "Terbitkan ke GitHub
  Pages", "Uji situs live setelah terbit", dan "Tandai commit yang sudah diterbitkan".
- **[Terverifikasi, log job]** Uji live berjalan di runner terhadap
  `https://reconciler.github.io/jadwalkajian/`: "Percobaan 1/12" lalu "Semua cek
  situs live lulus" (200 untuk beranda dan 5 berkas `_site`, 404 untuk 3 berkas
  internal). Tag `last-deploy` pindah dari `e7e3e68` ke `a3e9d33`.
- **Batas yang tetap berlaku:** uji ini memeriksa status HTTP dan teks penanda,
  bukan tampilan. Tampilan tombol "Tentang" (font asli, ponsel) belum dilihat siapa
  pun di perangkat nyata; uji lokal memakai font cadangan.
- Satu push (`9787426`, `d600597`, `a3e9d33`) dan satu deploy, sesuai instruksi.
