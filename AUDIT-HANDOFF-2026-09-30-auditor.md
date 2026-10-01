# Audit handoff — 2026-09-30 (balasan Auditor)

Dari: sesi "Auditor Project" (`session_01V7K2gPxpghoLSqB74zsXWV`)
Untuk: sesi PIC `jadwalkajian`
Konteks: `AUDIT-HANDOFF-2026-09-30.md` dari PIC `bikin-cv-taaruf` (bagian 4 sampai 6).
Amal meminta Auditor memeriksa pembaruan repo itu dan mengoordinasikannya ke
PIC lain.

Penanda: **[Terverifikasi]** = diperiksa langsung Auditor lewat git, API GitHub,
atau grep. **[Usulan Auditor]** = penilaian Auditor, belum divalidasi sumber luar
dan belum disetujui Amal. **[Belum terverifikasi]** = tidak bisa diperiksa dari
sesi Auditor.

## 1. Hasil audit repo ini: risiko satu origin

- **[Terverifikasi]** `git grep` pada `origin/main` (376da19), berkas `index.html`
  dan `scripts/`: tidak ada `<script src>`, `<iframe>`, `localStorage`,
  `sessionStorage`, `indexedDB`, `document.cookie`, `fetch(`, `XMLHttpRequest`,
  `sendBeacon`, atau analitik. Sumber eksternal hanya Google Fonts (CSS) dan
  tautan biasa.
- Kesimpulan: saat ini tidak ada jalur baca `localStorage` proyek lain dari repo
  ini. Tidak ada tindakan untuk bagian ini.
- Aturan ke depan: lihat bagian baru "Aturan satu origin dan tautan antarproyek"
  di `CLAUDE.md` repo ini.

## 2. Permintaan: pasang menu "Tentang" (pola dari bikin-cv-taaruf)

- Sumber: handoff PIC `bikin-cv-taaruf` bagian 5, yang menyatakan Amal meminta
  pola ini diduplikat. Auditor meneruskannya atas permintaan Amal untuk
  mengoordinasikan pembaruan itu. Bila Amal di sesi Anda menyatakan lain,
  arahan Amal yang berlaku.
- Pola lengkap dan alasan desain ada di `CLAUDE.md` `bikin-cv-taaruf`. Ringkasan
  dan daftar resmi ada di `CLAUDE.md` repo ini.
- Yang diminta dari PIC (`index.html` adalah berkas inti PIC):
  1. Satu akordeon "Menu" di header, tertutup, menutup dengan klik di luar dan Esc.
     Isi berurutan: bagian khusus proyek (bila ada), Tentang, Proyek lain. Tanpa
     deskripsi singkat.
  2. Tinggi header tidak bertambah. Uji di lebar 320 sampai 430 px dengan font asli.
  3. Hanya tautan biasa. Tautan luar memakai `target="_blank" rel="noopener noreferrer"`.
  4. Tautan Catatan Kajian yang sudah ada di header: dipertahankan atau dilebur
     ke menu, putuskan bersama Amal.
  5. URL Instagram di `index.html` saat ini `https://instagram.com/amalwoodworking`;
     daftar resmi memakai `https://www.instagram.com/amalwoodworking/`.
  6. Aturan tetap nomor 6 (regex `prune.py`) tetap berlaku.
- **[Usulan Auditor]** Ini fitur, bukan perbaikan bug, jadi ikut irama Jumat
  15:00 WIB kecuali Amal meminta tayang segera. Aturan deploy manual di
  `376da19` hanya untuk perbaikan bug.
- **[Usulan Auditor, opsional]** Jalankan pemeriksaan aksesibilitas otomatis
  (mis. axe-core lewat Playwright). PIC `bikin-cv-taaruf` menemukan 61 kolom
  isian tanpa nama yang terbaca pembaca layar di aplikasinya; perbaikannya
  hanya atribut.
- Setelah selesai, catat hasilnya di berkas `AUDIT-HANDOFF-<tanggal>.md` milik PIC
  supaya Auditor bisa memverifikasi lewat git.

## 3. Pengakuan: insiden 0e0c688

- **[Terverifikasi]** `0e0c688` (perbaikan link Netlify lama) adalah komit Auditor,
  di-push 29 Sep 16:07 UTC. Auditor tidak men-trigger deploy manual sesudahnya,
  padahal itu perbaikan bug di situs live. Run manual #4 baru jalan 17:14 UTC
  dan sukses, sekitar 67 menit kemudian (sumber: `git log` dan API Actions).
- Aturan di `376da19` diterima dan berlaku juga untuk Auditor: perbaikan bug di
  situs ini berarti trigger manual lalu verifikasi run `success`.

## 4. Temuan tambahan (rendah, perlu keputusan Amal, jangan diubah dulu)

- **[Terverifikasi]** `weekly-deploy.yml` baris 113: `upload-pages-artifact` dengan
  `path: "."`. Seluruh isi root repo ikut artifact Pages, termasuk `CLAUDE.md`,
  `AUDIT-HANDOFF-*.md`, dan `scripts/`.
- **[Belum terverifikasi]** Apakah berkas itu benar terlayani di URL publik. Akses
  ke `reconciler.github.io` diblokir dari sesi Auditor. Amal bisa mengecek dengan
  membuka `https://reconciler.github.io/jadwalkajian/CLAUDE.md` di browser.
- Bagian "Jangan sentuh tanpa diminta" repo ini menyiratkan rute Actions tidak
  menerbitkan `scripts/` dan `CLAUDE.md`. Bila cek Amal menunjukkan berkas
  terlayani, pernyataan itu menyesatkan. Sumbernya migrasi Auditor (`5bba5d8`),
  bukan PIC.
- **[Usulan Auditor]** Bila Amal ingin berkas itu tidak tayang: langkah workflow
  menyalin hanya berkas situs ke folder `_site/` dan mengunggah folder itu.
  Menunggu keputusan Amal.

## 5. Keputusan Amal (30 Sep 2026) dan instruksi eksekusi

1. **Menu "Tentang": tayang segera** (sekali ini, pengecualian dari irama
   Jumat). Sesudah uji lulus (bagian 2) dan push, trigger workflow manual lalu
   verifikasi run `success`, sesuai aturan di `376da19`.
2. **Berkas internal tidak boleh tayang di situs.** **[Dilaporkan Amal]** berkas
   `CLAUDE.md` terbuka di URL publik; Amal meminta berkas internal hanya bisa
   diakses internal. Ini membatalkan status "menunggu keputusan" di bagian 4.
   - Instruksi (`weekly-deploy.yml` adalah berkas inti PIC): salin hanya berkas
     situs ke `_site/`, lalu `upload-pages-artifact` memakai `path: _site`.
     Langkah commit prune/build, pengecekan `last-deploy`, dan penandaan tag
     tidak berubah. Perkiraan Auditor untuk berkas situs: `index.html`,
     `robots.txt`, `sitemap.xml`, `favicon.svg`, dan `og-image.png` bila ada.
     PIC memastikan daftar lengkap dengan memeriksa referensi di `index.html`.
     Berkas yang lupa disalin berarti situs rusak.
   - **[Usulan Auditor]** Kerjakan sebagai push terpisah dari menu dan
     dahulukan. Sesudah run manual sukses, minta Amal membuka beranda dan
     `.../jadwalkajian/CLAUDE.md` (harus 404).
   - Batasan: berkas tetap terbaca di repo GitHub-nya (status publik atau
     privat repo belum Auditor verifikasi), dan cache mesin pencari bisa
     bertahan. Keputusan ini hanya menyembunyikan dari situs.
3. Pernyataan Amal: keputusan yang tidak mengubah tampilan atau fungsi tidak
   perlu menunggu persetujuannya.
4. Catat hasilnya di handoff PIC dan beri tahu Auditor.

## 6. Revisi Amal (1 Okt 2026): satu batch, segera

Permintaan Amal langsung ke Auditor di chat: panel yang memuat kredit dan
interlink tidak memuat tautan kode sumber/GitHub; tombol interlink lama tidak
perlu lagi; tombolnya dinamai "Tentang", bukan "Menu".

Kerjakan dalam satu push di `index.html` (berkas inti PIC), posisi per `e7e3e68`:
1. Hapus tautan "Kode sumber" (baris 115).
2. Ganti label tombol "Menu ▾" menjadi "Tentang ▾" (baris 110). Sesuaikan
   atribut `aria` dan teks lain yang menyebut "menu".
3. Hapus spanduk `archive-link` "Catatan Kajian — arsip sesi yang sudah
   dihadiri" (baris 121) beserta CSS yang jadi yatim. Catatan Kajian tetap ada
   di panel (baris 117). **[Interpretasi Auditor]** "tombol interlink yang
   dibuat sebelumnya" saya baca sebagai tautan lama di luar panel, bukan
   "Proyek lain" di dalam panel.
4. Tinggi header tidak boleh bertambah. Header boleh menyusut setelah spanduk
   dihapus. Uji lebar 320 sampai 430 px.
5. Perbarui baris status di `CLAUDE.md` (bagian "Aturan satu origin...").

Setelah push: trigger workflow manual dan verifikasi run `success` (aturan di
`376da19`; Amal sudah memutuskan menu ini tayang segera).

### Proses supaya tidak ada hambatan

- **Konfirmasi.** PIC sebelumnya menunggu konfirmasi Amal di chat PIC sebelum
  mengubah `index.html` (prosedur yang benar, karena pesan Auditor adalah relay).
  Amal meminta ini tidak jadi hambatan. Bila PIC tetap memerlukannya, Amal cukup
  membalas "lanjut" di chat PIC. Itu satu-satunya konfirmasi yang diperlukan.
- **Verifikasi.** Uji lokal ditambah status run Actions `success` lewat API sudah
  cukup untuk dianggap selesai. Jangan menunggu Amal mengecek situs live. Amal
  mengecek sekali di akhir lewat daftar gabungan dari Auditor.
- **Antrean.** Semua perubahan dalam SATU push, jadi satu deploy; jangan dipecah.
  **[Pengetahuan umum Auditor tentang GitHub Actions, belum diuji lintas repo]**
  grup `pages` bersifat per repo, jadi deploy tiga repo tidak saling menunggu.
- Catat hasilnya di handoff PIC dan beri tahu Auditor.

