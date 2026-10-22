# Instruksi Auditor, 22 Okt 2026: proyek baru Kenali Calon dan sinkronisasi empat repo (jadwalkajian)

Dari: sesi "Auditor Project". Untuk: sesi kerja (PIC) repo ini. Penanda: **[Keputusan Amal]**, **[Terverifikasi]** (diperiksa
Auditor di git/Actions/hitungan), **[Usulan Auditor]** (kesimpulan Auditor).

## 1. Dasar dan batas

- **[Keputusan Amal]** 22 Okt 2026 (chat Auditor): Kenali Calon adalah proyek resmi keempat dan PIC-nya sudah ditunjuk;
  bagian credit tiap proyek diperbarui dengan tautan ke Kenali Calon; Auditor mengorkestrasi eksekusinya; temuan celah/error
  dieksekusi tanpa menunggu persetujuan Amal; "aturannya masih sama".
- **[Usulan Auditor]** tafsir "aturannya masih sama": butir 1 dan 2 aturan lintas-repo tetap berlaku. Tautan baru (tampilan)
  sudah disetujui Amal lewat keputusan di atas, jadi **tidak perlu konfirmasi ulang**. Pengecualian butir 2 (pipeline/`deploy.yml`,
  janji privasi, penghapusan data) tetap dikonfirmasi Amal **di chat sesi kerja repo ini**; kutipan di atas tidak
  menggantikannya. Gelombang yang tertahan karena itu ditandai **[DITAHAN]**; gelombang lain jalan terus.
- `CLAUDE.md` repo ini sudah diperbarui Auditor (komit yang sama): Daftar resmi memuat Kenali Calon, cakupan "keempat repo",
  dan bagian baru **"Proyek terkait dan sinkronisasi"** (tabel keempat proyek, apa yang harus sinkron, urutan proyek baru,
  jalur temuan untuk repo lain). Baca bagian itu dulu. Jalankan `git pull --rebase origin main` sebelum edit dan sebelum push.
- Tulis hasil di handoff PIC repo ini (bagian baru, gaya `Preferensi melapor`), lalu beri tahu Auditor. Jalur andal = git.

## 2. Tugas (satu push per gelombang; tiap push: verifikasi run `success`)

### Gelombang 1: tautan Kenali Calon (tampilan, disetujui Amal)
1. `index.html`, `#menu-panel`, grup "Proyek lain": tambah setelah "Bikin CV Taaruf"
   `<a href="https://reconciler.github.io/kenalicalon/" target="_blank" rel="noopener noreferrer">Kenali Calon</a>`.
   Label dan URL persis Daftar resmi.
2. Uji: validasi di `CLAUDE.md`; `python3 scripts/test_ingest.py`; axe-core 320 dan 430 (panel tertutup dan terbuka) harapan 0
   pelanggaran; tinggi header sebelum = sesudah di 320/375/430 (panel tertutup); panel terbuka tidak terpotong di 320.
   Sebut "tampilan berubah" (butir 11). Bot juga menulis `index.html`, jadi `pull --rebase` tepat sebelum push.

### Gelombang 2: perbaikan bug skrip (bukan fitur; keputusan PIC, butir 1)
- Kerjakan **T1 dan T2** di `AUDIT-HANDOFF-2026-10-03-auditor.md` bagian 15.3 (belum ada tanggapan PIC). Amal 22 Okt: temuan
  dieksekusi tanpa menunggu. Pembekuan formulir (opsi A) tidak melarang perbaikan bug. Satu push (menyentuh `scripts/**`,
  jadi CI menjalankan uji; `test_ingest.py` hijau lokal dulu).
- Id 791 berawalan "Ustd." (Anda tandai tapi belum diperbaiki): samakan dengan konvensi `tampil` di `data/kategori.json`,
  putuskan sendiri, catat alasannya.

### Gelombang 3: penjaga aset yang dirujuk `index.html` **[DITAHAN: pipeline]**
- Celah (**[Terverifikasi]** di `catatankajian`, ditemukan PIC Kenali Calon): uji pasca-terbit memeriksa berkas yang ada di
  `_site/`; aset yang dirujuk `index.html` tetapi lupa disalin lewat `cp` tidak pernah diuji, jadi run tetap hijau dan situs 404.
  **Di repo ini belum diperiksa**: simulasikan dulu (hapus satu aset yang dirujuk dari `_site/` di salinan lokal; bila uji tetap
  hijau, celah ada) dan catat hasilnya.
- Bila ada: tambah langkah di "Uji situs live setelah terbit": kumpulkan aset lokal yang dirujuk `index.html` (src/href relatif,
  `url()` relatif, `og:image`/`twitter:image` milik situs) lalu wajib 200. Pola kerja: `deploy.yml` repo `kenalicalon`, langkah
  uji nomor 4d dan 5 (baca di `reconciler/kenalicalon`; sesuaikan, jangan salin buta). Berjalan setelah terbit (tidak menahan
  publikasi), uji lain tidak dilonggarkan. Simulasikan jalur sukses dan gagal lokal (butir 6 dan 19). Satu push khusus.
- **Syarat:** tanya Amal satu kalimat di chat PIC ("Boleh tambah penjaga aset di deploy.yml, berjalan setelah terbit? ya/tidak").
  Tanpa "ya", jangan push gelombang ini; gelombang 1 dan 2 tidak menunggu.

## 3. Lapor
Handoff PIC bagian baru: tabel gelombang, hasil uji (angka), run, hal yang menunggu Amal. Setelah selesai, beri tahu Auditor.
