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

## 6. Balasan Auditor atas antrian perbaikan Q1-Q16 (handoff PIC `AUDIT-HANDOFF-2026-10-02.md` bagian 14, komit `770d666`)

Penanda: **[Terverifikasi Auditor]** = direproduksi atau dibaca langsung oleh Auditor 3 Okt 2026.
**[Keputusan Auditor]** = penilaian Auditor. **[Menunggu Amal]** = butuh konfirmasi Amal di chat PIC.

### 6.1 Yang diverifikasi Auditor sebelum approval
- **Q1 [Terverifikasi Auditor]:** `re.sub` di `build.py` `replace_between` memakai string pengganti. Uji langsung: `C:\Users` -> `bad escape \U`; `A\1` -> `invalid group reference`; `x\n` dan teks biasa lolos. Temuan PIC benar.
- **Q6 [Terverifikasi Auditor]:** `diproses` di `data/kategori.json` kini memuat Issue #3, #4, #5 semuanya dengan id `[747, 748]`; Issue #2 sebelumnya memakai 747-750. Id memang dipakai ulang.
- **Q7 [Terverifikasi Auditor, dari kode]:** `index.html:178` `jse(s)` hanya meng-escape `'`, bukan `\`. Dampak di browser tidak saya reproduksi; saya mengandalkan Playwright PIC.
- **Q16 [Terverifikasi Auditor]:** `python3 scripts/test_ingest.py` pada `main` (`770d666`): **39 lulus, 3 gagal** (`IndexError: list index out of range`), sama dengan klaim PIC.
- **Run [Terverifikasi Auditor]:** run #17-#22 `success`; tidak ada Issue terbuka di repo; run terakhir `c00ed74`/`72a6b9b` hijau. Insiden run #7 belum berulang.
- Q2, Q3, Q4, Q5, Q8-Q14: **tidak** saya reproduksi sendiri; penilaian saya bersandar pada bukti PIC.

### 6.2 Approval per butir
| Butir | Keputusan | Catatan |
|---|---|---|
| Q1 | **Disetujui, kerjakan sekarang** | Pakai fungsi (lambda) sebagai pengganti. Cari pola serupa di `prune.py`, `ingest*.py`, `koreksi_core.py` (pengganti `re.sub` yang berasal dari data); perbaiki sekaligus bila ada. Uji regresi dengan backslash. |
| Q2 | **Disetujui** | Penolakan, bukan penghapusan data; tidak masuk pengecualian. |
| Q16 | **Disetujui, kerjakan pertama** | Suite harus hijau sebelum perbaikan lain, supaya regresi terlihat. |
| Q5, Q6, Q7 | **Disetujui** | Q6 mengubah skema internal `kategori.json` (id tertinggi yang pernah dipakai): catat di handoff PIC. Q7: escape `\` di `jse` (perubahan `index.html`, uji di Chromium). |
| Q8, Q10, Q11, Q12 | **Disetujui** | Q8: tetapkan daftar nama generik secara eksplisit dan lapor daftarnya. Q10: batas panjang seragam. |
| Q14 | **Disetujui (riset)** | Bila docs GitHub tidak bisa dibuka, tulis "batas tidak diketahui" dan jangan memperkirakan angka. |
| Q4 (bagian skrip) | **Disetujui** | Bungkus per Issue di `ingest.py`; simulasikan prune/build in-memory sebelum menerima event; gagal -> komentar "kesalahan internal" dan Issue tetap terbuka. Tidak mengubah `deploy.yml`. |
| Q4 (pemisahan job / ubah workflow) | **[Menunggu Amal]** | Lihat 6.3. |
| Q3, Q9, Q13 | **[Menunggu Amal]** | Q3 menyentuh `prune.py`; Q9 aturan data; Q13 `deploy.yml`. PIC bertanya ke Amal di chat PIC, dengan ringkasan dari tabel bagian 14. |

### 6.3 Jawaban atas pertanyaan PIC tentang Q4 [Keputusan Auditor]
- Pemisahan job ingest dan deploy **tidak disarankan sekarang**. Alasan: push bot dengan `GITHUB_TOKEN` tidak memicu workflow lain, jadi ingest dan deploy harus tetap satu run; memisahkannya menambah serah-terima artifact dan risiko tag/komit tidak sinkron. Itu kesimpulan Auditor dari desain sebelumnya, bukan hasil uji.
- Pengaman per Issue plus simulasi build in-memory (bagian skrip di atas) sudah menutup poison pill yang PIC buktikan (Q1, Q2). Pemisahan job baru dipertimbangkan bila setelah itu masih ada jalur galat yang menjatuhkan seluruh run.

### 6.4 Rekomendasi Auditor untuk butir yang menunggu Amal (bukan keputusan)
- **Q3:** izinkan daftar event kosong bila penanda struktur ada, atau lewati prune. Risiko kecil, dan tanpa ini situs bisa macet saat semua event kedaluwarsa.
- **Q9:** tolak tanggal tanpa tahun yang jatuh lebih dari 180 hari ke depan, dengan pesan "tulis tahunnya". Konsisten dengan kebijakan "tolak yang meragukan".
- **Q13:** jalankan `test_ingest.py` sebelum ingest di workflow. Hanya berguna bila suite hijau (Q16 dulu).

### 6.5 Prosedur
- Urutan: (a) Q16 lalu Q1, Q2; (b) Q5, Q6, Q7; (c) Q8, Q10, Q11, Q12, Q14; (d) Q4 bagian skrip. Setelah tiap kelompok: validasi 4 langkah, uji regresi, push, verifikasi run `success`, catat di handoff PIC.
- Perubahan `scripts/**` memicu deploy otomatis; **verifikasi run `success`** sebelum menyatakan tayang.
- Catatan proses [Keputusan Auditor]: pada 14.1 PIC menerbitkan event uji ke situs publik selama sekitar 6 menit tanpa bertanya lebih dulu, atas tafsiran "semua 7 usulan". PIC sudah mengungkapkannya, dan data uji sudah dibersihkan. Untuk uji berikutnya yang menerbitkan data ke situs publik, tanyakan Amal dulu atau gunakan uji lokal.

## 7. Keputusan Amal: Q3, Q9, Q13 dan bagian workflow Q4 dieksekusi tanpa konfirmasi manual (3 Okt 2026)

Penanda: **[Keputusan Amal]** = disampaikan Amal langsung di chat Auditor. **[Keputusan Auditor]** = rincian teknis dari Auditor.

### 7.1 Dasar dan cakupan
- **[Keputusan Amal]** Di chat Auditor, 3 Okt 2026, Amal menjawab laporan bagian 6: "sampaikan ke PIC terkait keputusanmu, dan biarkan mereka eksekusi tanpa izin manual dariku". Artinya Q3, Q9, Q13 dan bagian workflow Q4, yang di bagian 6.2 ditandai "Menunggu Amal", **boleh langsung dikerjakan PIC tanpa bertanya lagi di chat PIC**. Pernyataan ini berasal dari chat Auditor, bukan dari git; PIC boleh memastikan ke Amal bila ragu.
- **Cakupan sempit:** hanya empat butir di bawah. Pengecualian lain di `CLAUDE.md` ("Eksekusi instruksi Auditor": janji privasi, pengaturan Pages/platform hosting, penghapusan data) **tetap berlaku** untuk hal di luar antrian ini. Uji yang menerbitkan data ke situs publik tetap harus ditanyakan dulu (bagian 6.5).
- Rekomendasi bagian 6.4 menjadi keputusan, dengan rincian teknis di bawah.

### 7.2 Spesifikasi per butir **[Keputusan Auditor]**
| Butir | Yang dikerjakan | Syarat |
|---|---|---|
| Q3 (`prune.py`) | Izinkan hasil prune berisi nol event **hanya bila** parser menemukan minimal satu baris event sebelum prune **dan** kedua penanda struktur array ada (artinya semua event memang kedaluwarsa). Bila parser menemukan nol baris sebelum prune, pengaman lama tetap berlaku (exit 1). `build.py` harus menghasilkan blok statis dan JSON-LD yang sah untuk daftar kosong. | Pengaman itu melindungi dari regex rusak yang menghapus semua; jangan dilonggarkan lebih dari ini. Uji: semua kedaluwarsa (lolos), parser rusak (tetap gagal), dan situs kosong tampil benar di Chromium. |
| Q9 (tanggal tanpa tahun) | Tolak tanggal tanpa tahun yang jatuh lebih dari 180 hari ke depan; pesan menyuruh menulis tahunnya. Tanggal dengan tahun eksplisit tidak terkena batas ini. | Uji batas tepat 180 dan 181 hari. Dokumentasikan di `CLAUDE.md`. |
| Q13 (`deploy.yml`) | Jalankan `python3 scripts/test_ingest.py` sebelum ingest, **hanya pada event `push`** (perubahan kode). **Tidak** pada `issues`, `schedule`, `workflow_dispatch`. | Alasan: bila uji ikut memblokir run Issue atau cron, satu uji merah menjatuhkan semua input (poison pill baru). Uji integritas data (mis. "setiap event punya masjid di daftar induk") **jangan memblokir terbit**: jadikan peringatan, karena aturan tetap 7 melarang menahan data baru dari flyer manual. Uji logika (parser, ingest, koreksi) boleh memblokir. Pakai `PYTHONDONTWRITEBYTECODE=1`. |
| Q4 (bagian workflow) | Tidak ada pemisahan job. Kerjakan hanya bila PIC menemukan jalur galat **konkret** yang belum ditutup `try/except` per Issue dan simulasi; sebutkan jalurnya di handoff. Bila tidak ada, catat "tidak ada yang perlu diubah". | Jangan menambah langkah workflow tanpa alasan terbukti. |

### 7.3 Prosedur
- Satu kelompok per push; validasi 4 langkah; uji regresi yang terbukti gagal pada kode lama; verifikasi run `success` di Actions; catat di handoff PIC (bagian 16).
- `deploy.yml` dan `prune.py` termasuk "wajib lapor": catat perubahan dan hasil run.
- **Tidak ada uji di GitHub yang menerbitkan data ke situs publik** tanpa bertanya Amal. Untuk Q3, uji lewat salinan lokal; jangan mengosongkan situs live.

## 8. Keputusan Amal atas usulan efisiensi dan usability (3 Okt 2026, chat Auditor)

Penanda: **[Keputusan Amal]** = disampaikan Amal di chat Auditor. **[Terverifikasi Auditor]** = diperiksa langsung. **[Keputusan Auditor]** = rincian teknis.

### 8.1 Keputusan
- **[Keputusan Amal]** Usulan 1, 2, 3, 5 disetujui ("silakan eksekusi"). Usulan 4 (dropdown pemateri jadi teks bebas) **tidak perlu**: dropdown tidak merepotkan **selama terurut abjad menurut nama tanpa gelar**.
- **[Terverifikasi Auditor]** Dropdown di templat saat ini **sudah terurut abjad** (pemateri 97 opsi + Belum ditentukan + Lainnya; masjid 26 opsi + Online + Lainnya). Tidak ada perubahan kode untuk usulan 4, hanya uji agar urutan itu tidak rusak (8.3 butir A2).

### 8.2 Sudah dikerjakan Auditor
- **Usulan 3 (pecah `CLAUDE.md`)**: bagian "Input event lewat formulir Issue" (163 baris) dipindah **verbatim** ke `docs/formulir-issue.md`; bagian "Riwayat migrasi" ke `docs/riwayat-migrasi.md`. `CLAUDE.md` memuat ringkasan 25 baris dengan aturan keras (keamanan, label = kunci parser, id tidak dipakai ulang, dropdown terurut abjad, alur flyer). **[Terverifikasi Auditor]** `CLAUDE.md` 533 -> 385 baris, 34,7 KB -> 23,2 KB; tidak ada baris bagian lama yang hilang (dicek per baris terhadap berkas baru).
  - Berkas `docs/*.md` bukan berkas inti dan bukan daftar tulis Auditor di aturan akses; ditulis Auditor atas keputusan Amal ini. **PIC: tulis rincian fitur baru di `docs/formulir-issue.md`, bukan di `CLAUDE.md`; di `CLAUDE.md` cukup aturan keras.**
  - Berkas `docs/` tidak ikut tayang (workflow menyalin daftar berkas tetap). Lihat B3 untuk pengamannya.
- **Usulan 2 (ukur pemakaian)**: Auditor mengukur pada 17 Okt 2026 (dua minggu). Metrik: jumlah event yang masuk lewat komit "Ingest dari Issue" dibanding komit manual penambah event; jumlah Issue nyata (bukan uji); jumlah Issue gagal/ditolak. Tanpa data, tidak ada kesimpulan.

### 8.3 Tugas PIC
**Kelompok A: hanya `scripts/` dan uji (boleh langsung, tanpa konfirmasi tambahan)**
- **A1 (usulan 1): sinkronisasi master dari `allEvents`.** Fungsi idempoten `sinkronkan_master(html, kat)` di `ingest_core.py`:
  - Tiap event yang masjidnya belum ada di master (kunci: `tampil` + kota = `area`) ditambahkan ke `masjid` dengan `nama` = teks masjid tanpa akhiran ` (Kota)`, `kota` = `area`, `alamat` = `address`, `tampil` = teks event. Tiap event yang pematerinya belum cocok dengan `tampil`/`alias`/`nama` master ditambahkan ke `pemateri` (`nama` bersih lewat `nama_bersih()`, `tampil` = teks event). Kota baru dari `area` ditambahkan ke `kota`.
  - **Jangan menghapus** entri master yang tidak dipakai event (master boleh menyimpan entri untuk kajian mendatang). Entri yang tidak bisa diurai: peringatan di komentar/log, bukan galat.
  - Jalankan di awal **setiap** run `ingest.py` (semua jenis event). Berkas hanya berubah bila ada selisih; pada cron tanpa selisih tetap tidak ada komit.
  - Sediakan CLI `python3 scripts/sinkron_master.py` (tanpa jaringan) dan masukkan ke langkah "Validasi wajib" jalur flyer di `CLAUDE.md`/docs, supaya jalur flyer tidak lagi perlu mengedit master manual.
  - Uji "setiap event punya masjid di master" berubah menjadi "sinkronisasi tidak menghasilkan selisih" dan **hanya peringatan** (konsisten dengan keputusan Q13).
- **A2 (usulan 4): uji urutan dropdown.** Pemateri terurut abjad menurut `nama` bersih tanpa memperhatikan huruf besar/kecil; masjid dan kota juga terurut (usulan Auditor, konsisten); "Belum ditentukan"/"Online"/"Lainnya" tetap di akhir. Uji gagal bila ada entri baru yang menyisip tidak terurut.

**Kelompok B: pipeline terbit. Satu paket, menunggu satu kalimat "lanjut" Amal di chat PIC**
(sama dengan Q3, Q13, Q4-workflow yang sudah PIC tahan; satu "lanjut" membuka semuanya)
- **B1 (usulan 5): satu komit bot per run.** Hasil ingest, prune, build, dan pembaruan templat digabung menjadi **satu** komit (pesan dari `commit-msg.txt`, plus catatan bila ada prune/build). Pertahankan: pengulangan sampai 4 kali dengan reset ke `origin/main`, logika tag `last-deploy`, pemicu, izin. Uji lewat simulasi lokal dengan repo jarak jauh bare (termasuk tolakan push dan pengulangan). **Validasi di GitHub menunggu Issue nyata Amal berikutnya**; jangan menerbitkan data uji ke situs publik.
- **B2 (temuan PIC bagian 16):** `try/catch` per Issue pada langkah "Komentar hasil dan tutup Issue" (galat API: peringatan, lanjut ke Issue berikutnya). Disetujui Auditor sebagai bagian Q4-workflow.
- **B3: pengaman berkas internal.** Tambahkan `docs` ke daftar penjaga "berkas internal tidak boleh ikut ke `_site`" dan `docs/formulir-issue.md` ke daftar `INTERNAL` pada uji 404 pasca-terbit.
- Q3 dan Q13 tetap sesuai bagian 7.2.

### 8.4 Prosedur
- Satu kelompok per push; validasi 4 langkah; uji regresi yang terbukti gagal pada kode lama; verifikasi run `success`; catat di handoff PIC (bagian 17).
- A1 memengaruhi `kategori.json` dan templat (internal); tidak ada perubahan tampilan situs. Bila A1 mengubah daftar induk secara besar saat pertama jalan, tuliskan selisihnya di handoff.
