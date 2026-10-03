# Audit handoff — 2026-10-03 (Auditor): formulir "Tambah kajian" harus mencakup kajian rutin dan pola mingguan

Dari: sesi "Auditor Project" (`session_01V7K2gPxpghoLSqB74zsXWV`)
Untuk: sesi PIC `jadwalkajian`

Penanda: **[Terverifikasi]** = diperiksa langsung Auditor (git, kode, uji).
**[Usulan Auditor]** = rancangan Auditor, belum disetujui Amal; PIC boleh menyesuaikan
dan wajib melaporkan penyesuaiannya. **[Belum terverifikasi]** = harus diuji PIC.

## 1. Permintaan Amal (3 Okt 2026)

Amal meminta formulir "Tambah kajian" **memastikan kebutuhan kajian rutin dan pola
mingguan tercakup**. Amal sudah lebih dulu mengusulkan kolom Tanggal berupa isian bebas
langsung ke PIC; usulan itu yang dipakai. Rencana Auditor sebelumnya (kolom pola
terpisah: pola, hari, dari, sampai, kecuali) **dibatalkan**, karena isian bebas PIC
lebih sederhana.

## 2. Kondisi saat ini (penilaian Auditor atas komit `db82b07`/`a377f5d`)

- **[Terverifikasi]** Pola mingguan dasar **sudah tercakup** oleh `tanggal_bebas.py`:
  `3-31 Okt 2026 Sabtu` menghasilkan 5 tanggal; `setiap Sabtu & Ahad` menghasilkan 9;
  ada uji end-to-end (`test_ingest.py`). Batas rentang 370 hari.
- **[Terverifikasi]** "Kajian rutin" saat ini hanya **kotak centang manual**
  (`isRutin` = dicentang atau tidak). Tidak ada hubungan dengan pola mingguan.
- **[Terverifikasi dari dokumentasi sintaks di berkas]** Belum didukung: pengecualian
  tanggal ("kecuali 17 Okt"), selang lebih dari satu minggu ("tiap 2 minggu"), dan
  "pekan ke-N dalam bulan". Tidak ada batas jumlah event per Issue selain batas
  rentang 370 hari (salah ketik rentang bisa membuat puluhan event sekaligus).

## 3. Yang diminta

### 3.1 Kajian rutin: dari kotak centang menjadi dropdown tiga keadaan **[Usulan Auditor]**

Kotak centang tidak bisa membedakan "tidak dicentang" dari "belum disentuh", sehingga
tidak bisa otomatis. Ganti kolom "Kajian rutin" dengan dropdown:

| Opsi | Efek |
|---|---|
| **Otomatis (rutin bila berulang tiap minggu)** — bawaan | `isRutin` ditentukan skrip dari pola tanggal |
| Ya, rutin | `isRutin = true` |
| Tidak | `isRutin = false` |

Aturan "Otomatis" (PIC boleh menyempurnakan, laporkan aturan akhirnya): rutin bila
tanggal berasal dari rentang dengan filter hari, atau berupa daftar **tiga tanggal atau
lebih** dengan jarak seragam 7 hari. Selain itu tidak rutin (satu tanggal, daftar acak).
Label kolom = kunci parser: perbarui `adapter_issue_form.py`, templat otomatis, dan uji.
Issue lama yang sudah diproses tidak diproses ulang (idempotensi `diproses`).

### 3.2 Pola mingguan: lengkapi sintaks Tanggal yang ada

1. **Pengecualian:** `3-31 Okt 2026 setiap Sabtu kecuali 17 Okt` dan
   `... kecuali 17, 24 Okt`. Tanggal pengecualian di luar rentang atau yang bukan
   bagian pola: beri peringatan di komentar. Bila semua tanggal dikecualikan: tolak
   dengan alasan jelas.
2. **Komentar hasil** menampilkan pola terbaca, daftar tanggal beserta nama hari,
   tanggal yang dikecualikan, dan jumlah event (sudah ada daftar hasil; lengkapi
   dengan pola dan pengecualian).
3. **Batas jumlah event per Issue** untuk menahan salah ketik rentang (usul 60; PIC
   memilih angka dan mendokumentasikannya). Lewat batas: tolak sebelum menulis apa
   pun, dengan pesan yang menyebut jumlah yang dihasilkan dan cara mempersempit.
4. **Tidak didukung, tolak dengan pesan yang menyarankan alternatif** (tulis daftar
   tanggal): "tiap 2 minggu" dan "pekan ke-N". Jangan dibangun kecuali Amal meminta.
5. Deskripsi kolom Tanggal di templat: tambahkan contoh `kecuali`, dan catatan
   bahwa satu Issue = satu jam dan satu masjid (waktu berbeda per hari = Issue terpisah).

### 3.3 Catatan seri untuk pembatalan kelak

Pastikan `diproses` menyimpan **nomor Issue → daftar `id` event yang dihasilkan**
(laporkan bila sudah ada). Ini dasar formulir "Koreksi atau hapus" berikutnya, supaya
satu seri yang salah ketik bisa dibatalkan sekaligus. Formulir itu **belum diminta**.

## 4. Pengujian

- Tambahkan uji: pola lintas bulan dan tahun; filter dua hari; `kecuali` valid, di luar
  pola, dan menghabiskan semua tanggal; rutin otomatis (pola mingguan → true; satu
  tanggal → false; tiga tanggal berjarak 7 hari → true; daftar acak → false);
  override "Ya" dan "Tidak"; batas jumlah event; ingest end-to-end dengan prune dan
  build.
- Alur sungguhan masih menunggu Issue uji dari Amal (tercatat di handoff PIC bagian 7).
  Jadikan satu kasus pola mingguan sebagai Issue uji itu, lalu hapus event ujinya.

## 5. Prosedur

- Perubahan di `ingest*.py`, adapter, templat, dan uji **tidak menyentuh** privasi,
  hosting, pipeline terbit (`deploy.yml`), maupun penghapusan data, sehingga boleh
  dikerjakan langsung (aturan "Eksekusi instruksi Auditor"). Bila ada langkah yang
  menurut PIC masuk pengecualian, hentikan dan tanya Amal.
- Perbarui `CLAUDE.md` PIC (sintaks Tanggal, aturan rutin otomatis, batas jumlah
  event) dan catat hasil di handoff PIC.
- Butir terbuka yang **bukan** bagian ini: opsi pengerasan push tag `last-deploy`
  (insiden run #7) menyentuh `deploy.yml`; tetap menunggu "lanjut" Amal.
