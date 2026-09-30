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
