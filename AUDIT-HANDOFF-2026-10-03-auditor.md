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

## 9. Verifikasi Auditor atas hasil PIC (bagian 15-19 handoff PIC), 3 Okt 2026 sore

Penanda: **[Terverifikasi Auditor]** = dijalankan atau dibaca langsung. **[Dari handoff PIC]** = tidak saya reproduksi.

- **[Terverifikasi Auditor]** Suite 63 lulus, 0 gagal (mesin Auditor). Run Actions #28-#33 `success`; tidak ada Issue terbuka. `deploy.yml`: blok `on:` (push, issues, satu cron `17 20 * * *`, dispatch) dan action (hanya `actions/*`) tidak berubah dibanding sebelum paket pipeline.
- **[Terverifikasi Auditor]** Q3: salinan sementara dengan `JADWAL_HARI_INI=2030-01-01`: prune menghasilkan 0 event, build sah ("Belum ada kajian mendatang"), prune kedua tetap exit 0 (idempoten), JS valid. Hook `JADWAL_HARI_INI` tidak di-set di `deploy.yml` (0 kemunculan), jadi produksi memakai jam asli.
- **[Dari handoff PIC]** B1 (satu komit bot per run) hanya teruji lokal dengan remote bare; **belum teruji di GitHub dengan data nyata**. Pembuktian pertama: Issue nyata Amal berikutnya, atau cron 03:17 WIB.
- **Pencarian dokumentasi GitHub (hasil pencarian web, bukan halaman penuh):** sintaks dropdown hanya menyebut `options` tidak boleh kosong dan harus unik; tidak ada batas maksimum jumlah opsi yang tertulis. Itu konsisten dengan keputusan Amal menghapus batas 150, tetapi **tidak membuktikan** ketiadaan batas. Pengamatan empiris: sekitar 104 opsi berfungsi.
- Keputusan Amal di chat PIC (bagian 18-19) menggantikan penahanan PIC: paket pipeline dilanjutkan; batas dropdown dihapus; Hapus boleh mengosongkan daftar; uji YAML tidak dipasang di CI (opsi A).
- **[Keputusan Amal, chat Auditor, 3 Okt 2026]** Peringatan tanpa-pemblokir untuk dropdown di atas 150 opsi **tidak perlu dikerjakan**. Risiko yang diketahui (batas GitHub tidak terdokumentasi; formulir bisa tidak tampil lengkap bila terlampaui, tidak terdeteksi CI) diterima. Gejala bila terjadi: kolom Pemateri/Masjid tidak tampil lengkap di formulir; cara pulih ada di `docs/formulir-issue.md`.

## 10. Ekstraksi aturan dan keputusan yang belum tertulis di `CLAUDE.md` (3 Okt 2026, permintaan Amal)

Penanda: **[Keputusan Amal]** = diucapkan Amal (chat Auditor atau tercatat di handoff PIC). **[Praktik PIC/Auditor]** = kebiasaan kerja yang terbukti di git, belum diputuskan Amal. **[Temuan]** = ketidaksesuaian dokumen dengan kenyataan. Semua butir di bawah **usulan**; belum ada yang ditulis ke `CLAUDE.md`.

Cakupan sumber: transkrip sesi Auditor (79 pesan Amal), seluruh handoff dan `CLAUDE.md` ketiga repo, `docs/`. **Tidak termasuk** isi chat langsung Amal dengan tiap PIC yang tidak berakhir di git (tidak terjangkau dari sesi Auditor).

### 10.1 Aturan lintas-repo (usulan masuk `CLAUDE.md` ketiga repo)
| # | Aturan | Sumber | Status |
|---|---|---|---|
| L1 | Jangan menunggu Amal untuk keputusan yang **tidak mengubah tampilan atau fungsi**; putuskan sendiri dan catat. | [Keputusan Amal] 30 Sep: "hapus ketergantungan ke saya jika itu bukanlah keputusan yang akan mengubah tampilan atau fungsi" | Tidak tertulis di repo mana pun |
| L2 | PIC boleh menyimpang dari spesifikasi Auditor bila ada metode lebih aman, **wajib mencatat penyimpangan dan alasannya**, lalu melapor. | [Keputusan Amal] 3 Okt (chat PIC, dikutip handoff PIC bagian 18); praktik PIC: Q3, B2, Q13 | Tidak tertulis |
| L3 | Persetujuan Amal berlaku untuk butir yang disebut; tidak meluas ke butir lain. Pengecualian pipeline/privasi/penghapusan data dikonfirmasi di **chat PIC**; kutipan Amal yang disampaikan Auditor tidak cukup bagi PIC. | [Praktik PIC] bagian 16-18 handoff PIC; konsisten dengan aturan "Eksekusi instruksi Auditor" tetapi eksplisitnya belum ada | Sebagian tersirat |
| L4 | Temuan janggal dilaporkan **disertai usulan perbaikan**, bukan hanya temuan. | [Keputusan Amal] 3 Okt | Tidak tertulis (preferensi melapor hanya mengatur format) |
| L5 | Uji yang menerbitkan data ke situs publik: tanya Amal dulu atau uji lokal. | [Instruksi Auditor] bagian 6.5; PIC pernah menerbitkan event uji ±6 menit | Hanya di handoff Auditor |
| L6 | Perubahan pipeline: satu per push, urut dari risiko rendah ke tinggi (push `deploy.yml` menjalankan versi baru alur itu); kerjakan perubahan yang membuat kondisi tepi aman **sebelum** yang mengandalkannya. | [Praktik PIC] handoff PIC bagian 18 (urutan Push 1-4); catatankajian memisahkan perubahan artifact dari batch lain | Tidak tertulis |
| L7 | Dependensi pihak ketiga disalin ke `lib/` dengan versi dipatok dan integritas dicocokkan ke registry npm; tidak memuat skrip dari CDN tanpa SRI. | [Praktik PIC] bikin (jsPDF) dan catatankajian (Fuse.js) | Hanya di `CLAUDE.md` bikin |
| L8 | Klaim di dokumen, UI, atau data terstruktur harus benar untuk proyek itu: tidak menambah `SearchAction` bila tidak ada fungsinya; kalimat privasi harus akurat (kasus Google Fonts). | [Praktik PIC] catatankajian bagian 4; bikin bagian 2 handoff 29 Sep | Hanya di `CLAUDE.md` bikin (privasi) |
| L9 | Berkas koordinasi yang tidak lagi relevan dihapus, kecuali masih/akan dipakai. | [Keputusan Amal] 2 Okt (soal `COORDINATION-NOTE`, akhirnya dipertahankan) | Tidak tertulis |
| L10 | Perubahan struktur komunikasi/pelaporan diterapkan **simetris** di ketiga repo supaya prediktif bagi Auditor dan pihak luar. | [Keputusan Amal] 22 Sep | Tersirat ("sengaja disamakan"), bukan aturan |
| L11 | Setelah deploy yang mengubah tampilan, belum ada yang melihatnya di perangkat nyata (font asli, ponsel). Setiap laporan harus menyebut "belum dilihat di perangkat nyata" sampai Amal memeriksa. | [Praktik PIC] handoff PIC 30 Sep dan 2 Okt | Tidak tertulis; uji otomatis tidak menilai tampilan |
| L12 | Prinsip kepastian di atas kecepatan: terbit yang pasti lebih penting daripada cepat (waktu tunggu lama tidak masalah). | [Keputusan Amal] 2 Okt | Tersirat di bagian cron jadwalkajian saja |

### 10.2 Khusus repo
| Repo | Aturan/keputusan | Sumber | Status |
|---|---|---|---|
| catatankajian | Bio ustadz/kitab baru ditulis dari riset web **dengan catatan transparan bila sumber tidak solid**. | [Praktik PIC] handoff 22 Sep bagian 2 | `CLAUDE.md` hanya menyebut riset kitab |
| bikin-cv-taaruf | Pemeriksaan aksesibilitas axe-core (0 pelanggaran) sebagai uji standar sebelum push. Handoff PIC menyarankan dua PIC lain melakukan hal serupa. | [Praktik PIC] handoff 30 Sep bagian 6 | Hanya bikin |
| jadwalkajian | Risiko diterima: batas jumlah opsi dropdown GitHub tidak terdokumentasi, tanpa peringatan; gejalanya formulir tidak lengkap. | [Keputusan Amal] 3 Okt | Di handoff dan `docs/`, bukan di `CLAUDE.md` |

### 10.3 Ketidaksesuaian dokumen dengan kenyataan **[Temuan]**
- **`catatankajian/CLAUDE.md` basi:** tidak menyebut `lib/` (Fuse.js lokal), folder `_site` dan daftar berkas yang tayang, atau uji otomatis pasca-deploy; padahal `deploy.yml` repo itu melakukan ketiganya (`cp -r lib`, `_site`, langkah "Uji otomatis pasca-deploy"). Bagian "Struktur" juga belum memuat `lib/`.
- **Daftar `INTERNAL` di uji 404 tidak simetris:** bikin memeriksa semua `AUDIT-HANDOFF-*.md`; jadwalkajian hanya satu nama (`AUDIT-HANDOFF-2026-09-30.md`). Penjaga `_site` tetap mencegah berkas internal ikut, jadi risiko kecil, tetapi bertentangan dengan L10.
- **Batas verifikasi tidak seragam:** catatan "sesi kerja tidak bisa mengakses github.io" hanya ada di `CLAUDE.md` jadwalkajian.

### 10.4 Yang perlu diputuskan Amal
1. Butir L1-L12 mana yang masuk `CLAUDE.md` (saran Auditor: L1-L7 dan L10 sebagai aturan; L8, L9, L11, L12 sebagai catatan singkat).
2. Perbaikan 10.3 (dokumen saja, tidak mengubah fungsi) boleh dikerjakan Auditor sekarang.
3. Bentuk penulisan: bagian "Aturan lintas-repo" bersama di ketiga `CLAUDE.md`, dengan teks identik (menjaga simetri L10).

## 11. Perubahan Auditor 3 Okt 2026 (atas keputusan Amal: "eksekusi semua usulanmu")

- `CLAUDE.md` mendapat bagian **"Aturan lintas-repo"** (13 butir; teks **identik** di ketiga repo, diverifikasi dengan diff).
  Baca bagian itu sebelum bekerja; ia berlaku sebagai aturan tetap.
- `CLAUDE.md` jadwalkajian: risiko dropdown yang diterima Amal dicatat di bagian formulir Issue.

### 11.1 Butir untuk PIC jadwalkajian
- **Butir A (dokumen, boleh langsung):** tugas ekstraksi di 11.2.
- **Butir B (menunggu "lanjut" Amal di chat PIC, menyentuh `deploy.yml`):** samakan uji 404 pasca-terbit dengan bikin-cv-taaruf:
  periksa **semua** `AUDIT-HANDOFF-*.md` (dan `COORDINATION-NOTE-*.md` bila ada) 404, bukan satu nama tetap pada daftar `INTERNAL`.
  Alasan: simetri (aturan lintas-repo butir 9) dan handoff baru otomatis terjaga. Jangan melonggarkan uji lain.
- **Butir C (uji, boleh langsung):** jalankan axe-core di Chromium terhadap beranda (terang/gelap bila ada, lebar 320 dan 430)
  sebagai garis dasar (aturan lintas-repo butir 13). Laporkan temuannya. Perbaikan yang hanya menambah atribut aksesibilitas
  tanpa efek visual boleh langsung dan dilaporkan; perbaikan yang mengubah tampilan/fungsi menunggu Amal. Bila axe-core tidak
  bisa dipasang di sesi kerja (jaringan), katakan itu.

### 11.2. Tugas: ekstrak aturan berguna dari obrolan Anda dengan Amal

Amal meminta tiap PIC mengekstrak aturan dan keputusan yang berguna dari obrolannya dengan Anda dan belum tertulis
formal. Auditor sudah melakukannya untuk sesi Auditor dan dokumen di git; **chat langsung Amal dengan Anda tidak
terjangkau dari sesi Auditor**, jadi hanya Anda yang bisa melakukannya.

**Sumber:** seluruh riwayat percakapan sesi Anda dengan Amal (termasuk bagian sebelum pemadatan konteks), pesan
komit, dan handoff Anda.

**Yang dicari:** keputusan, aturan, atau preferensi Amal yang **berlaku ke depan** dan belum ada di `CLAUDE.md`
repo ini dan `docs/`. Abaikan keputusan sekali pakai yang sudah selesai dan status pekerjaan.

**Format tiap butir** (tabel di handoff Anda): aturan (satu kalimat) | sumber (kutipan pendek Amal + tanggal, atau
"praktik" bila belum diputuskan Amal) | cakupan (repo ini saja atau lintas-repo) | status (sudah tertulis di mana,
atau belum) | usulan teks (maksimal dua baris).

**Cara memproses:**
- Butir yang **keputusan eksplisit Amal dan khusus repo ini**: tambahkan langsung ke `CLAUDE.md` repo ini, ringkas
  (rincian panjang ke `docs/` bila repo punya), dan catat di handoff Anda.
- Butir **lintas-repo** atau yang hanya **praktik** (belum diputuskan Amal): jangan ditulis ke `CLAUDE.md`; cukup
  didaftar di handoff. Auditor yang menyatukan supaya bagian "Aturan lintas-repo" tetap identik di ketiga repo, lalu
  Amal memutuskan.
- Jangan mengubah kode atau workflow untuk tugas ini. Jaga `CLAUDE.md` tetap ringkas (tambahan sekitar 30 baris
  paling banyak).
- **Jangan menyalin data pribadi atau sensitif** (isi CV, kontak, kredensial, token); kutip seperlunya.

**Lapor:** commit ke repo (jalur utama). Beri tahu Auditor lewat pesan hanya sebagai tambahan.

## 12. Konsolidasi ekstraksi aturan dari tiga PIC (3 Okt 2026) — usulan, menunggu keputusan Amal

Penanda: **[Terverifikasi Auditor]** = diperiksa langsung (git, diff, data, Actions). **[Dari handoff PIC]** = kutipan Amal di chat PIC yang tidak terjangkau Auditor; tidak diverifikasi. Belum ada butir di bawah yang ditulis ke bagian "Aturan lintas-repo".

### 12.1 Verifikasi hasil kerja PIC
- **[Terverifikasi Auditor]** Bagian "Aturan lintas-repo" di tiga `CLAUDE.md` masih identik (`diff`). Run Actions terbaru semua `success`: jadwalkajian #34-#35, catatankajian #15-#18, bikin-cv-taaruf #7-#8.
- **[Terverifikasi Auditor]** Penambahan `CLAUDE.md` oleh PIC kecil: jadwalkajian +4/-1 baris, catatankajian +15/-6, bikin-cv-taaruf +13/-1 (batas 30 tidak terlampaui). Tidak ada data pribadi di handoff baru (dibaca penuh).
- **[Terverifikasi Auditor]** catatankajian: 8 nilai `theme` yang ditulis PIC ke `CLAUDE.md` sama persis dengan `themes[]` di `data.json` (dan semuanya dipakai sesi); contoh slug sesuai pola `id` ustadz yang ada. Bahwa itu "keputusan Amal dari brief awal" **[Dari handoff PIC]**.
- Butir B (uji 404 semua handoff) dikerjakan di jadwalkajian dan catatankajian setelah "lanjut" Amal di chat PIC (run #35 dan #18 `success`). jadwalkajian mempertahankan daftar tetap lama dan menambah glob (penyimpangan lebih aman, dicatat). **Temuan:** handoff catatankajian bagian 3 masih menulis Butir B "menunggu konfirmasi", padahal komit `811ce74` menyatakan sudah dikonfirmasi dan dikerjakan; catatan itu basi.

### 12.2 Baseline axe-core (aturan lintas-repo butir 13) — keputusan visual menunggu Amal
| Repo | Hasil (dari handoff PIC) | Sudah diperbaiki | Menunggu Amal |
|---|---|---|---|
| jadwalkajian | 4 jenis pelanggaran | Atribut landmark (`banner`, `region`, `main`, `contentinfo`); tangkapan layar sebelum/sesudah identik per piksel menurut PIC (belum saya reproduksi) | `color-contrast` badge kota (4 dari 7 kota di bawah 4,5:1: Bandung 3,73; Bogor 3,60; Jakarta 3,81; Tangerang 3,04); usul PIC teks L=70% di atas L=20% (minimum 4,76 untuk semua hue), diubah serentak di `index.html` dan `scripts/build.py`. `link-in-text-block`: usul garis bawah pada tautan di kotak "Ingin menambahkan info kajian?" |
| catatankajian | 1 jenis pelanggaran (`color-contrast`) di beranda (26 elemen) dan satu rekap (21 elemen) | Tidak ada (perubahan warna) | Warna `--muted` (`#6B7A8D`) dan chip tema; PIC belum mengusulkan nilai pengganti |
| bikin-cv-taaruf | 0 pelanggaran (praktik lama) | - | - |
- Cara memasang axe-core yang berhasil dipakai tiga PIC: `npm i axe-core playwright-core` di folder sementara, Chromium `executablePath: '/opt/pw-browsers/chromium'`, **terverifikasi bisa dijalankan di sesi kerja** (butir 13 layak).

### 12.3 Usulan butir lintas-repo baru (sudah dihapus duplikatnya)
| # | Usulan aturan (satu kalimat) | Sumber | Rekomendasi Auditor |
|---|---|---|---|
| N1 | Bila konteks kurang, baca riwayat chat, handoff, dan git dulu; baru sumber eksternal. | [Dari handoff PIC] preferensi Amal; sama dengan preferensi akun Amal | Masukkan |
| N2 | Bagian bersama "Preferensi melapor" (sekarang hanya di jadwalkajian): Indonesia, formal, poin/tabel, tanpa emoji; tandai terverifikasi vs saran; jangan mengarang hasil, katakan bila alat/akses tidak tersedia; penjelasan "awam" = analogi dan tabel kecil; akhiri pekerjaan besar dengan "yang perlu Anda ketahui" (belum terbukti, perubahan perilaku, kejadian otomatis, keputusan menunggu). | Gabungan: jadwalkajian A2, A3; catatankajian (jangan mengarang); bikin (label terverifikasi); `CLAUDE.md` jadwalkajian yang ada | Masukkan sebagai bagian bersama identik di tiga repo |
| N3 | Jangan memasang batas buatan yang tidak berdasar platform terverifikasi (kecuali keamanan); catat risikonya. | [Dari handoff PIC] Amal 3 Okt: "Kalo 150 bukan batasan dari github, maka tak perlu dibatasi" | Masukkan |
| N4 | Bila status diragukan (termasuk klaim "sukses" dari jalur otomatis), verifikasi manual sendiri dulu, lalu konfirmasi ke Amal dan Auditor lewat chat dan git. | [Dari handoff PIC] Amal 22 Sep; tertulis di handoff catatankajian 22 Sep | Masukkan |
| N5 | Kerjakan sendiri yang bisa dikerjakan sesi; minta Amal hanya untuk akses yang sesi tidak punya. Pengaturan Pages diubah Amal; PIC menyiapkan workflow dan langkahnya, dan memberi jalur kembali satu langkah sebelum mengalihkan pipeline. | [Dari handoff PIC] Amal; praktik migrasi bikin 30 Sep | Masukkan |
| N6 | Repo publik: jangan commit data pribadi (isi CV, kontak, kredensial), termasuk di handoff dan kutipan chat. | [Dari handoff PIC] praktik bikin | Masukkan (biaya rendah, risiko tinggi bila terlewat) |
| N7 | Praktik uji: uji otomatis deterministik (data beku, jam terkunci); skrip workflow disimulasikan lokal untuk jalur sukses dan gagal sebelum push; perubahan UI diuji dengan tangkapan layar di 320/375/430 px, font asli dari paket npm, jaringan luar diblokir. | Praktik tiga PIC (bukan keputusan Amal) | Masukkan sebagai praktik, bukan aturan keras |
| N8 | Cara menyajikan butir keputusan: pertahankan penomoran asli, "semua" = seluruh butir asli; tiap butir memuat tujuan, akibat bila ditunda, rekomendasi dengan default konservatif; pertanyaan Amal dijawab dengan analisis dan usulan bernomor, perubahan menunggu persetujuan. | [Dari handoff PIC] jadwalkajian A4-A6 (praktik, sebagian dari ucapan Amal) | Opsional; ringkas bila dimasukkan |
| N9 | "Satu batch = satu push = satu deploy". | [Praktik] bikin; berasal dari batas kredit Netlify | **Jangan dimasukkan**: alasan lamanya hilang sejak pindah ke GitHub Pages (gratis); bagian "lapor setelah run `success` terbaca" sudah ada |

### 12.4 Aturan khusus repo yang PIC tambahkan sendiri
- catatankajian: 8 tema baku, deskripsi Bahasa Indonesia, `content` padat satu paragraf untuk mesin pencari, format slug `id`, riset alamat masjid baru.
- bikin-cv-taaruf: footer PDF memuat alamat situs sebagai kredit; persetujuan A.02 memakai "data pribadi yang sensitif"; cara menjalankan axe-core.
- jadwalkajian: keputusan opsi A (uji YAML hanya lokal).

### 12.5 Yang diminta dari Amal
1. Putuskan N1-N8 mana yang masuk (rekomendasi: N1-N6 dan N7 sebagai praktik; N8 opsional; N9 tidak).
2. Putuskan dua temuan visual axe-core: jadwalkajian (kontras badge kota, garis bawah tautan) dan catatankajian (kontras warna muted). Auditor menyarankan PIC catatankajian mengusulkan nilai pengganti dengan angka kontras, seperti yang dilakukan PIC jadwalkajian.
3. Setelah keputusan, Auditor menulis bagian bersama identik di tiga `CLAUDE.md`; PIC catatankajian diminta memperbarui handoff-nya (bagian 3 basi).

## 13. Instruksi 5 Okt 2026: aturan bersama baru + perbaikan visual axe-core

Dasar: **[Keputusan Amal]** 5 Okt 2026 (chat Auditor):
- Butir lintas-repo N1-N7 dan butir baru "bahasa campur ID+English, concise" **masuk** `CLAUDE.md`; N8 dan N9 tidak.
- Temuan visual axe-core: **langsung dieksekusi** (tampilan berubah; konfirmasi Amal sudah ada, tidak perlu tanya lagi).
- Bagian bersama baru di ketiga `CLAUDE.md` (diff identik): `Aturan lintas-repo` butir 14-19 + `Preferensi melapor`.
  Baca dan patuhi. Mulai sekarang tulis handoff/laporan dengan gaya itu (concise, simpel, spesifik, campur English).
- `CLAUDE.md` jadwalkajian: bagian lama "Preferensi Amal saat melapor" diganti bagian bersama `Preferensi melapor`.

### 13.1 Tugas PIC jadwalkajian (satu push, verifikasi run `success`)
1. **Kontras badge kota** (`.area-tag`, 4 dari 7 kota < 4.5:1): pakai usulan PIC, teks L=70% di atas latar L=20% (hue tetap).
   Ubah **serentak** di `cc()` (`index.html`) dan `city_color()` (`scripts/build.py`); uji JS = Python harus tetap hijau.
   Target: min contrast >= 4.5:1 untuk semua hue (PIC hitung 4.76).
2. **Tautan di kotak "Ingin menambahkan info kajian?"**: `text-decoration: underline`, hanya di kotak itu.
3. Re-run axe (320 + 430, 3 keadaan). Harapan: `color-contrast` badge dan `link-in-text-block` hilang. Sisa node "perlu cek
   manual" (gradien/overlap) cukup dilist, tidak wajib diperbaiki.
4. Before/after screenshot; sebut "belum dilihat di perangkat nyata" (butir 11). Update `docs/` bila warna dirujuk di sana.
5. Catat di handoff PIC (bagian 21): tabel kontras sebelum/sesudah per kota, hasil axe, run.
