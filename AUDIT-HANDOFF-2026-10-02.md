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
(diisi PIC setelah run pertama `deploy.yml` selesai)
