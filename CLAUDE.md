# Jadwal Kajian — panduan kerja

Dashboard jadwal kajian Jabodetabek & sekitarnya.
Live: https://reconciler.github.io/jadwalkajian/ · Pemilik: Amal (@amalwoodworking)

Migrasi dari Netlify ke GitHub Pages: **29 September 2026**. URL lama
(`jadwalkajian.netlify.app`) sudah tidak dipakai.

## Struktur

```
index.html                           # seluruh dashboard — HTML+CSS+JS satu file
robots.txt                           # izinkan semua crawler, tunjuk ke sitemap.xml
sitemap.xml                          # daftar URL untuk Google Search Console (1 URL, single-page)
favicon.svg                          # ikon tab browser
scripts/prune.py                     # hapus event lewat + perbarui stempel footer
scripts/build.py                     # generate HTML statis + JSON-LD (SEO) dari allEvents
data/kategori.json                   # daftar induk kota/masjid(nama,kota)/pemateri(nama bersih+lengkap) + Issue diproses/gagal (internal, TIDAK tayang di _site)
scripts/ingest.py                    # CLI ingest Issue -> event (dipanggil workflow)
scripts/ingest_core.py               # logika inti: validasi, pembuatan event, daftar induk (tanpa tahu soal formulir)
scripts/adapter_issue_form.py        # adapter formulir Issue: templat YAML + parser isi Issue -> paket baku
scripts/koreksi_core.py              # inti koreksi/hapus event (tahap 2): target, ganti/hapus baris, validasi ulang
scripts/adapter_koreksi_form.py      # adapter formulir "Koreksi atau hapus kajian": templat YAML + parser
scripts/tanggal_bebas.py             # pengurai isian Tanggal bebas (10 Okt 2026, 3-31 Okt 2026 Sabtu, ...)
scripts/test_ingest.py               # uji lokal ingest (python3 scripts/test_ingest.py)
.github/ISSUE_TEMPLATE/              # DIBUAT OTOMATIS dari data/kategori.json; jangan edit manual
.github/workflows/deploy.yml         # prune + build + terbitkan ke GitHub Pages (push ke main + manual)
```

## SEO — konten statis & JSON-LD (jangan edit manual)

`index.html` punya dua blok yang di-generate otomatis oleh `scripts/build.py`,
ditandai komentar HTML:

- `<!--LD_JSON_START-->...<!--LD_JSON_END-->` di `<head>` — JSON-LD
  `schema.org/Event` untuk semua kajian upcoming.
- `<!--STATIC_EVENTS_START-->...<!--STATIC_EVENTS_END-->` di dalam
  `#cards-container` — HTML statis daftar kajian, supaya crawler yang tidak
  menjalankan JavaScript tetap melihat isi kajian. JS `render()` tetap
  menimpa ini saat halaman dibuka (progressive enhancement) — tidak
  mengubah interaktivitas filter untuk pengunjung biasa.

**Jangan edit isi antara marker ini secara manual** — akan tertimpa saat
`build.py` jalan lagi. Kalau perlu ubah tampilan/struktur kartu statis, edit
`render_static_card()` di `scripts/build.py`, bukan HTML-nya langsung.

`build.py` dijalankan otomatis di `deploy.yml` setelah `prune.py`,
jadi tidak perlu dijalankan manual tiap kali menambah event — **kecuali**
saat validasi lokal sebelum commit (lihat bagian Validasi di bawah), supaya
`index.html` yang di-commit sudah konsisten dengan data terbaru.

Meta tag statis (`description`, `og:*`, `twitter:*`, `canonical`) ditulis
manual sekali di `<head>`, tidak berubah tiap event — tidak perlu diupdate
rutin. **Belum ada `og:image`** (butuh aset gambar banner asli dari Amal,
belum dibuat).

`index.html` **wajib** di root dengan nama persis itu — GitHub Pages
menyajikannya sebagai homepage.

## Publikasi — push ke `main` menerbitkan situs

Baca ini sebelum melapor apa pun ke Amal.

**Berubah 2 Okt 2026 (keputusan Amal):** jadwal mingguan Jumat 15:00 WIB
**dihapus**. Jadwal itu ada karena batas kredit Netlify, yang tidak relevan
sejak pindah ke GitHub Pages. File workflow diganti nama dari
`weekly-deploy.yml` menjadi `deploy.yml` (nama workflow di tab Actions:
*Prune & deploy*).

Situs di-host **GitHub Pages** (Settings → Pages → Build and deployment →
Source: **"GitHub Actions"**, bukan "Deploy from a branch"). Publikasi hanya
lewat `deploy.yml`, dengan empat pemicu (Issue dan cron ditambah 3 Okt 2026, tahap 1
sistem input Issue):

- **Push ke `main`** yang mengubah `index.html`, `robots.txt`, `sitemap.xml`,
  `favicon.svg`, `og-image.png`, `scripts/**`, atau `deploy.yml` — otomatis.
  Push yang hanya mengubah `CLAUDE.md`/`AUDIT-HANDOFF-*.md` tidak memicu apa pun.
- **Issue dari `reconciler`** dibuka/diedit — dikenali dari **isi** formulir (judul
  kolom), bukan judul Issue; lihat bagian "Input event lewat formulir Issue" di bawah.
- **Cron pengaman harian** `17 20 * * *` UTC (03:17 WIB; satu-satunya cron yang
  disetujui Amal 2 Okt 2026): menerbitkan bila `last-deploy` tertinggal dari
  `main`, memproses Issue yang terlewat, menutup Issue yang sudah terbit. Tanpa
  Issue baru, cron **tidak** prune/build/commit (tidak ada deploy harian). Cron
  GitHub bisa telat berjam-jam; itu hanya menunda terbit.
- **Manual**: tab Actions → *Prune & deploy* → Run workflow (gratis, kapan saja).

Konsekuensi untuk sesi ini:

- Setelah push yang mengubah berkas situs, run otomatis berjalan. **Verifikasi
  run-nya `success`** (tab Actions atau `actions_list`) sebelum bilang event/
  perbaikan sudah tayang. Kalau run gagal, laporkan terus terang; jangan
  menyebut sudah tayang.
- Tidak ada lagi "antrean sampai Jumat" dan tidak ada batas commit mingguan.
- Push dari bot (hasil prune/build, memakai `GITHUB_TOKEN`) **tidak** memicu run
  baru, jadi tidak ada loop. Konsekuensinya `main` di remote bisa lebih maju
  dari lokal: **`git pull --rebase origin main` sebelum push** berikutnya.
- Prune dan build jalan di tiap run, jadi event lewat terhapus dari `index.html`
  dan dari blok HTML statis/JSON-LD setiap kali terbit. Di browser pengunjung,
  event lewat tetap disembunyikan oleh `isEventPast`/`up()` walau belum
  di-prune — ini yang menjamin end user tidak melihat event lewat. Batas
  yang diketahui: tanpa cron, blok statis/JSON-LD untuk crawler bisa memuat
  event kedaluwarsa sampai push/run berikutnya (Amal: tidak masalah).
- Sebelum 2 Okt 2026, cron pernah telat >5 jam (25 Sep) dan sesi lain sempat
  menunggu Jumat padahal ada bug live (insiden 29 Sep, `0e0c688`). Dua masalah
  itu hilang bersama jadwal mingguan.

## Input event lewat formulir Issue (sejak 3 Okt 2026)

Jalur input kedua selain "screenshot flyer ke Claude". Keputusan Amal 2 Okt 2026,
rancangan di `AUDIT-HANDOFF-2026-10-02-auditor.md`, penerapan di
`AUDIT-HANDOFF-2026-10-02.md` bagian 6.

- **Cara pakai (Amal):** tab Issues → New issue → "Tambah kajian" → isi → Submit.
  Hanya Issue dari `reconciler` yang **isinya formulir** (judul kolom `### Tanggal`,
  `### Jenis waktu`, `### Masjid`) yang diproses; judul Issue bebas (awalan "Tambah
  kajian:" tetap dikenali). Issue non-formulir dari `reconciler` diabaikan.
  Dalam beberapa menit: event masuk, situs terbit, Issue diberi komentar dan
  ditutup. **Issue terbuka = belum terbit.** Gagal validasi: Issue tetap terbuka
  dengan komentar alasan; edit Issue untuk memproses ulang.
- **Kolom:** Tanggal (SATU isian bebas, bukan satu per baris; contoh `10 Okt 2026`,
  `10, 17, 24 Okt 2026`, `3-31 Okt 2026 Sabtu`, `3 Okt - 4 Okt 2026`, `10/10/2026`,
  `2026-10-10`; tahun boleh dihilangkan; nama hari di depan tanggal = pemeriksa;
  rinci di `scripts/tanggal_bebas.py`; Issue form GitHub tidak punya pemilih
  kalender [menurut pengetahuan PIC, belum tervalidasi docs]), Jenis waktu, Jam
  (hanya Jam eksak: `09.30` atau `09.30-11.00`), Judul, Pemateri (dropdown **nama
  bersih tanpa gelar**) + Pemateri baru, Pemateri perempuan (→ `Khusus Akhwat`),
  Masjid (dropdown **`Nama (Kota)`**) + Nama/Alamat masjid baru, Kota masjid baru /
  Kota lain, Audience (bawaan Terbuka untuk umum), Kajian rutin (dropdown tiga
  keadaan, lihat di bawah), Abaikan kemiripan nama (kotak centang, lihat "Dumb-proof"),
  Catatan (opsional). Masjid = **Online**: isi penyelenggara di "Nama masjid baru" →
  `masjid` = `<penyelenggara> (Online)`, `area` = `Online`. Komentar balasan
  menampilkan tiap tanggal dengan nama hari; cek di sana.
- **Sintaks Tanggal lengkap** (`scripts/tanggal_bebas.py`, instruksi Auditor 3 Okt 2026):
  satu tanggal, daftar (`10, 17, 24 Okt 2026`), rentang (`3 Okt - 4 Okt 2026`,
  `3-31 Okt 2026`), rentang dengan filter hari (`3-31 Okt 2026 setiap Sabtu & Ahad`),
  pengecualian (`3-31 Okt 2026 setiap Sabtu kecuali 17, 24 Okt`; satu kata `kecuali`
  per isian, berlaku untuk seluruh isian; pengecualian di luar pola diberi
  peringatan; bila semua tanggal dikecualikan ditolak). **Batas 60 tanggal per Issue**
  (dihitung setelah pengecualian; lewat batas ditolak sebelum menulis apa pun, pesan
  menyebut jumlahnya). **Ditolak dengan saran "tulis daftar tanggal":** `tiap 2 minggu`,
  `2 minggu sekali`, `pekan/minggu ke-N`, `bulanan`; dan `setiap minggu` (ambigu: tiap
  pekan atau hari Minggu; tulis `Ahad` untuk Minggu). Satu Issue = satu jam dan satu
  masjid (waktu/masjid berbeda per hari = Issue terpisah).
- **Kajian rutin** (dropdown tiga keadaan; kotak centang lama dibaca sebagai "Ya"):
  `Otomatis (rutin bila berulang tiap minggu)` (bawaan), `Ya (rutin)`, `Tidak`.
  Otomatis = rutin bila ada **rentang dengan filter hari yang menghasilkan ≥ 2
  tanggal**, atau tanggal hasil **berjumlah ≥ 3 dengan jarak seragam tepat 7 hari**;
  selain itu tidak rutin (satu tanggal, daftar acak, rentang tanpa filter hari).
  Aturan ini usulan Auditor yang disempurnakan PIC (syarat ≥ 2 tanggal pada rentang
  berfilter; pilihan opsi tanpa koma ASCII). Komentar balasan menyebut pola terbaca,
  tanggal dikecualikan, jumlah event, dan apakah rutin (beserta alasannya).
- `diproses` menyimpan `Issue -> daftar id event` (`{"issue": n, "id": [..]}`); dasar
  untuk formulir koreksi/hapus kelak (belum diminta).
- **Dumb-proof — kebijakan: tolak yang meragukan, jangan diam, jangan terbitkan data
  yang kemungkinan salah** (analisis dan keputusan Amal 3 Okt 2026). Ditolak (Issue
  tetap terbuka, komentar menyebut alasan; edit Issue untuk memproses ulang):
  isian bertentangan — Jam diisi padahal Jenis waktu bukan Jam eksak; jam selesai ≤ jam
  mulai (rentang melewati tengah malam tidak didukung); "Pemateri baru" terisi tetapi
  Pemateri bukan Lainnya; kolom masjid baru (nama, alamat, Kota lain) terisi padahal
  masjid dipilih dari daftar; Online dengan alamat/Kota lain terisi; Kota lain terisi
  padahal kota dipilih dari daftar; nama pengganti (`belum ditentukan`, `-`, `TBD`, `?`,
  dst.) sebagai **judul**, nama masjid, penyelenggara Online, atau pemateri baru; judul dan nama baru
  (pemateri, masjid/penyelenggara, kota) dengan **kurang dari 3 huruf** (mis. `0`, `2026`, `()`, `a`),
  serta nama pemateri/masjid/penyelenggara baru yang **seluruh katanya generik** (daftar eksplisit `GENERIK`
  di `scripts/ingest_core.py`: masjid, mushola, majelis, taklim, ustadz, ustadzah, kh, dr, kajian, pemateri,
  penceramah, dst.; ubah daftarnya di berkas itu); nama kota/masjid/
  pemateri baru yang **mirip** (kemiripan ≥ 0,85) dengan yang ada, kecuali kotak
  **Abaikan kemiripan nama** dicentang (lalu hanya peringatan). Otomatis: pemateri
  perempuan (master menandai `perempuan`; nama baru berawalan Ustadzah/Ustadzaat) →
  `Khusus Akhwat`; konflik dengan Audience Ikhwan ditolak. Issue yang **sudah diproses
  lalu diedit** mendapat komentar "perubahan tidak diterapkan" (bukan diam). Run yang
  gagal sebelum berkomentar menempelkan komentar kegagalan di Issue pemicu.
  Penolakan dilaporkan dalam dua tahap (kolom/kondisi formulir dulu, lalu aturan data).
  Karakter pengarah arah teks dan spasi lebar nol dibuang dari semua isian; `(kosongkan)` pada Catatan
  formulir Tambah dibaca kosong. Salah ketik semantik (judul, pemateri keliru) tidak bisa dideteksi mesin; jalurnya
  formulir **Koreksi atau hapus kajian** (di bawah).
- **Koreksi atau hapus (tahap 2, 3 Okt 2026)** — formulir kedua di "New issue":
  `.github/ISSUE_TEMPLATE/koreksi-hapus-kajian.yml` (dibuat otomatis dari
  `data/kategori.json`, jangan diedit manual). Dikenali dari judul kolom `### Aksi` dan
  `### Target`; label kolom berakhiran "(koreksi)" agar tidak tertukar dengan formulir
  Tambah. **Target:** `#12` (semua event yang MASIH ADA dari Issue Tambah 12), id event
  (`id 747`), rentang id (`747-750`), boleh digabung dengan koma; id tampil di panel rincian
  kartu situs (baris "ID", sejak 3 Okt 2026) dan di komentar Issue Tambah. Angka telanjang
  (`747`) dibaca sebagai id event, **kecuali** ada Issue terproses bernomor sama: ditolak
  sebagai ambigu (tulis `#747` atau `id 747`). **Semua-atau-tidak-sama-sekali:** satu id tak ditemukan atau satu event gagal
  validasi → tidak ada yang berubah.
  - **Dua langkah (pratinjau + konfirmasi, 3 Okt 2026):** kirim Issue dengan kolom
    **Konfirmasi kosong** → sistem hanya membalas pratinjau (tabel event yang akan dihapus,
    atau tabel sebelum/sesudah), Issue tetap terbuka, tidak ada yang berubah. Lalu **edit
    Issue** dan tulis `HAPUS <jumlah>` atau `KOREKSI <jumlah>` (jumlah = event terdampak
    sesuai pratinjau) → baru diterapkan. Kata atau jumlah salah, atau konfirmasi untuk Aksi
    lain, ditolak. Penolakan validasi biasa tetap muncul lebih dulu (sebelum pratinjau).
    Pratinjau dicatat di `gagal` dengan alasan "menunggu konfirmasi".
  - **Konfirmasi dikunci ke pratinjau (Q12, 3 Okt 2026):** konfirmasi hanya berlaku bila Issue itu
    **sudah pernah menampilkan pratinjau** dan isi pratinjau (event yang akan dihapus / selisih koreksi)
    **sama** dengan keadaan sekarang. Target diubah atau data berubah sesudah pratinjau → pratinjau baru
    muncul ("Data berubah sejak pratinjau"), konfirmasi harus diisi ulang. Konfirmasi tanpa pratinjau
    ditolak dengan pesan serupa.
  - **Hapus:** konfirmasi `HAPUS <jumlah>` (lihat di atas); ditolak bila penghapusan menyisakan **0
    kajian mendatang** (prune dan build menolak daftar kosong); kolom koreksi harus kosong
    (kalau terisi ditolak: kemungkinan Aksi salah pilih). Event dihapus dari `index.html`;
    master (`kategori.json`) tidak dipangkas. Kembalikan lewat formulir Tambah (id baru).
  - **Koreksi:** isi hanya kolom yang ingin diubah (kosong atau `(tidak diubah)` = tetap).
    Kolom yang tidak diubah dipertahankan apa adanya. Yang bisa diubah: judul, tanggal
    (satu tanggal; hanya bila Target satu event), jenis waktu dan jam, pemateri, masjid
    (dropdown, Lainnya, atau Online), audience, rutin, catatan (ketik `(kosongkan)` untuk
    menghapus catatan; kolom kosong = tetap). Id tetap. Aturan
    dumb-proof formulir Tambah berlaku sama (nama pengganti, kemiripan nama, jam,
    ustadzah → Akhwat, konflik isian). Koreksi yang membuat event sama dengan event lain
    ditolak (duplikat); koreksi yang tidak mengubah apa pun ditolak.
  - Hasilnya dicatat di `diproses` sebagai `{"issue": M, "id": [...], "aksi": "hapus"|"koreksi"}`
    (entri beraksi tidak dipakai untuk merujuk `#N`). Komentar balasan memuat tabel hapus
    atau tabel sebelum/sesudah; komentar hapus memuat semua kolom (alamat, audience, rutin,
    catatan) plus baris asli di blok `<details>` agar bisa dikembalikan lewat formulir Tambah.
    Issue ditutup setelah situs terbit seperti formulir Tambah.
  - Tidak didukung (sengaja): koreksi massal tanggal, koreksi berdasarkan pencarian
    (tanggal/masjid) tanpa id, pembatalan (undo) otomatis.
- **Pemateri** (keputusan Amal 3 Okt 2026): master menyimpan `nama` (bersih, untuk
  dropdown/pencarian/deteksi duplikat) dan `tampil` (lengkap dengan gelar, yang
  muncul di kartu situs), plus `alias`. Memilih dari dropdown → event memakai
  `tampil`. Mengetik "Pemateri baru" persis dari flyer (dengan gelar) →
  dicocokkan otomatis ke master lewat nama bersih/alias (komentar memberi tahu);
  bila tidak ada, dibuat entri baru (`tampil` = ketikan, `nama` = hasil
  pembersihan sapaan/gelar). Pemateri boleh organisasi/komunitas/kelompok
  ("Asatidz Pengajar Tahsin", "... & Komunitas ..."): entri dengan `&`, "dan",
  atau tanda kurung tidak dibersihkan. Nama mirip tapi beda hanya diberi
  peringatan; gabungkan manual dengan menambah `alias` di `data/kategori.json`.
- **Masjid** (keputusan Amal 3 Okt 2026): identitas = pasangan (`nama`, `kota`);
  dropdown `Nama (Kota)`. Event memakai `tampil` (biasanya = `nama`). Masjid baru:
  nama kota di belakang nama dibuang bila sisanya ≥ 2 kata ("Masjid Ar-Riyadh
  Depok" + Depok → "Masjid Ar-Riyadh"); bila nama yang sama sudah ada di kota lain,
  `tampil` memakai ` (Kota)` agar filter masjid di situs tidak menggabungkan dua
  masjid berbeda (filter mencocokkan teks nama).
- **Menambah kota/masjid/pemateri baru:** pilih "Lainnya" dan isi kolom barunya;
  otomatis masuk `data/kategori.json` dan dropdown berikutnya. Nama yang sama
  (abaikan huruf besar/kecil) memakai yang sudah ada.
- **Dropdown selalu mutakhir:** `.github/ISSUE_TEMPLATE/tambah-kajian.yml` dibuat
  ulang oleh `scripts/ingest.py` dari `data/kategori.json` di setiap run. Jangan
  edit manual. Opsi dropdown memakai koma lebar penuh (`，`) sebagai pengganti
  koma ASCII; parser memetakannya kembali.
- **Label kolom = kunci parser.** Mengubah label di `adapter_issue_form.py`
  (`LABEL`) wajib diikuti pengubahan parser; uji: `python3 scripts/test_ingest.py`.
- **Arsitektur:** `ingest_core.py` hanya menerima "paket baku"; formulir Issue
  hanya satu adapter (`adapter_issue_form.py`). Jalur lain (mis. Google Form)
  cukup menulis adapter baru.
- **Pengaman per Issue (Q4, 3 Okt 2026):** pemrosesan tiap Issue dibungkus `try/except`;
  exception tak terduga di satu Issue memulihkan `index.html`/master ke keadaan sebelum Issue itu,
  mencatatnya di `gagal` ("kesalahan internal"), mengomentari Issue, dan **tidak menjatuhkan Issue lain**
  atau run. Sebelum menerima perubahan, `simulasi_terbit()` (di `ingest.py`) menguji kering prune + build
  di memori (baris event terbaca, ada kajian mendatang, blok statis/JSON-LD bisa dibangun); gagal →
  "kesalahan internal", tidak ada yang ditulis. Kegagalan membuat templat formulir tidak fatal.
  Entri "kesalahan internal" tidak diulang otomatis; diproses lagi saat isi Issue berubah.
- **Keamanan (jangan dilanggar):** isi/judul Issue **tidak pernah** diinterpolasi
  ke `run:` di workflow (injeksi skrip) — dibaca dari berkas JSON. Baris event
  ditulis lewat `json.dumps`; tanda `<` `>` ditolak; karakter kontrol dibuang.
  Hanya action resmi `actions/*`.
- **Daftar induk `data/kategori.json`** juga menyimpan `diproses` (Issue → id event,
  untuk idempotensi), `gagal` (Issue yang ditolak; dilewati sampai **isinya berubah** atau diedit;
  tiap entri menyimpan sidik isi `isi` dan, untuk pratinjau, `pratinjau`), dan `id_tertinggi` (id event
  tertinggi yang pernah dipakai; **id tidak pernah dipakai ulang** walau event dihapus atau di-prune,
  supaya Target `#N` tidak salah sasaran; dihitung juga dari semua id di `diproses`).
  Jangan edit manual kecuali memperbaiki data; ia tidak tayang di situs.
- Alur flyer ke Claude tetap memakai langkah manual (edit `index.html`). Pakai
  `tampil` dari `data/kategori.json` untuk pemateri dan masjid yang sudah ada
  (ejaan konsisten); bila ada kota/masjid/pemateri baru, tambahkan juga ke
  `data/kategori.json` agar dropdown mengikutinya (event manual tidak otomatis
  masuk daftar induk). Uji konsistensi: `python3 scripts/test_ingest.py`
  (setiap event harus punya masjid di daftar induk).

## Berkas yang tayang di situs (folder `_site`)

Sejak 1 Okt 2026 workflow **tidak lagi** mengunggah seluruh root repo. Langkah
"Siapkan folder situs (_site)" menyalin hanya: `index.html`, `robots.txt`,
`sitemap.xml`, `favicon.svg`, `og-image.png`. `CLAUDE.md`, `AUDIT-HANDOFF-*.md`,
`scripts/`, dan `.github/` **tidak tayang** (workflow gagal bila ada yang ikut
tersalin).

- **Menambah aset baru yang dirujuk `index.html`** (gambar, CSS/JS terpisah,
  dll.)? Tambahkan ke daftar `cp` di langkah itu **dan** ke variabel `WATCH`
  di langkah "Cek apakah ada yang perlu diterbitkan". Kalau lupa, situs tayang
  dengan aset hilang atau perubahan aset dilewati sebagai "tidak ada perubahan".
- Rujukan lokal di `index.html` harus **relatif** (`favicon.svg`), bukan
  root-absolut (`/favicon.svg`): situs ada di subpath `/jadwalkajian/`, jadi
  `/favicon.svg` menunjuk ke `reconciler.github.io/favicon.svg` (404).
- Berkas tetap terbaca di repo GitHub-nya; ini hanya menyembunyikannya dari situs.
- **Uji otomatis setelah terbit** (langkah "Uji situs live setelah terbit" di
  `deploy.yml`, atas keputusan Amal 1 Okt 2026): runner memeriksa URL
  publik sampai 12 kali (jeda 10 detik): beranda 200 dan memuat teks "Jadwal
  Kajian"; setiap berkas langsung di `_site/` 200; `CLAUDE.md`,
  `AUDIT-HANDOFF-2026-09-30.md`, `scripts/prune.py` 404. Gagal = run merah dan
  tag `last-deploy` tidak dipindah, jadi run berikutnya menerbitkan ulang.
  **Jangan dilonggarkan supaya hijau**; selidiki penyebabnya. Uji ini tidak
  menilai tampilan. Bila nama berkas internal di daftar `INTERNAL` pada langkah
  itu berubah, perbarui daftarnya.
- Sesi kerja tidak bisa mengakses `reconciler.github.io`; verifikasi situs live
  dilakukan oleh langkah uji otomatis di atas (hasilnya ada di log run Actions).

## Riwayat migrasi Netlify → GitHub Pages (29 Sep 2026)

Sebelumnya situs ini di Netlify, dengan mekanisme `netlify.toml`
(`ignore = "exit 0"`) + build hook untuk menahan biaya kredit (kredit tim
Netlify sempat habis 22 Sep 2026, dipakai bersama `catatankajian`). Setelah
pindah ke GitHub Pages, seluruh masalah kredit itu tidak relevan lagi —
`netlify.toml` sudah dihapus, secret `NETLIFY_BUILD_HOOK` sudah tidak
dipakai (boleh dihapus dari repo secrets kalau belum). Irama publikasi
mingguan (Jumat 15:00 WIB) sempat **dipertahankan** pada migrasi, lalu
**dihapus Amal 2 Okt 2026** — lihat bagian "Publikasi" di atas.

Prune tetap berjalan di dalam workflow yang sama, jadi tidak menambah
job terpisah. Prune bersifat kosmetik: dashboard sudah menyembunyikan event
lewat di sisi browser (`isEventPast`/`up` di index.html).

## Alur kerja utama

Amal mengirim screenshot flyer kajian (biasanya dari Instagram masjid). Tugasnya:
baca flyer, ekstrak detail, tambahkan sebagai entri baru di array `allEvents`,
validasi, commit, push. Push otomatis memicu deploy; tunggu run `success` lalu
lapor event sudah tayang (lihat bagian "Publikasi").

## Skema data

Satu event = satu baris di array `allEvents`, format object literal:

```js
{id:864,date:"2026-09-20",dayShort:"Min 20 Sep",timeLabel:"Ba'da Maghrib",timeOrder:18,title:"...",ustadz:"...",masjid:"...",area:"Jakarta",address:"...",audience:"Terbuka untuk umum",note:"...",isRutin:true},
```

| Field | Aturan |
|---|---|
| `id` | Unik. Ambil dari **`id_tertinggi`** (lihat `core.id_tertinggi(html, kat)` di `scripts/ingest_core.py`: max dari `index.html`, `data/kategori.json` dan semua id di `diproses`) + 1, **bukan** max id di `index.html` saja (id event yang dihapus/di-prune tidak boleh dipakai ulang). **Wajib dicek tidak duplikat.** |
| `date` | `YYYY-MM-DD` |
| `dayShort` | `Sen Sel Rab Kam Jum Sab Min` + tanggal + bulan singkat. Minggu **selalu "Min"**, jangan "Ahd" |
| `timeLabel` | Jam eksak (`19.30 WIB`, `10.00 – 11.45 WIB`) atau waktu sholat (`Ba'da Subuh`, `Dhuha`, `Ba'da Zuhur`, `Ba'da Ashar`, `Ba'da Maghrib`) |
| `timeOrder` | Jam desimal untuk sorting. Subuh 4.5 · Dhuha 9 · Zuhur 12.5 · Ashar 15.5 · Maghrib 18. Untuk jam eksak, pakai jam mulai (19.30 → 19.5) |
| `area` | **Nama kota** dengan ejaan konsisten (`Depok` `Bogor` `Jakarta` `Bekasi` `Tangerang` `Bandung` …) atau `Online`. Nama bidang tetap `area`; di UI berlabel "Kota". Filter dan warna dibuat otomatis dari data (tidak ada daftar di kode, warna dihitung dari nama oleh `cc()` di `index.html` dan `city_color()` di `scripts/build.py` dengan algoritma sama). Kota baru: cukup tulis namanya. Cek ejaan yang sudah ada di `data/kategori.json`. `Tangerang` mencakup Kota/Kab. Tangerang dan Tangerang Selatan. |
| `audience` | `Terbuka untuk umum`, `Khusus Akhwat`, atau `Khusus Ikhwan`. **Bila flyer tidak menyebut pembatasan eksplisit, isi `Terbuka untuk umum`** (aturan Amal, 2 Okt 2026). |
| `isRutin` | `true` bila flyer menyebut kajian rutin/berkala |

Bulan singkat: Jan Feb Mar Apr Mei Jun Jul Agu Sep Okt Nov Des

## Aturan tetap — jangan dilanggar

1. **Semua kajian yang dibawakan ustadzah adalah `audience:"Khusus Akhwat"`.**
   Berlaku walau flyer tidak menyebutkannya.
2. **Cek duplikat sebelum menambah.** Grep judul/ustadz/tanggal dulu. Flyer sering
   dikirim ulang. Kalau event sudah ada tapi flyer baru memberi detail lebih spesifik
   (mis. judul yang sebelumnya generik), **perbarui entri lama** — jangan buat baru.
3. **Jangan tambahkan event yang tanggalnya sudah lewat.** Akan terbuang prune
   berikutnya. Kalau seluruh isi flyer sudah lewat, katakan itu — jangan diam saja.
4. **Kajian di luar Jabodetabek tetap dimasukkan** dengan nama kotanya sebagai `area` (keputusan Amal 2 Okt 2026, dicatat Auditor di `AUDIT-HANDOFF-2026-10-02-auditor.md` bagian 1; contoh: Masjid Jaza, Bandung). Dulu aturan ini membatasi ke Jabodetabek.
5. **Bedakan fakta flyer vs kesimpulan sendiri.** Kalau nama ustadz, alamat, atau jam
   tidak tercantum eksplisit dan diisi dari inferensi atau pengetahuan umum,
   **katakan eksplisit** di laporan. Amal secara khusus meminta ini.
6. **Jangan ubah `index.html` dengan cara yang merusak regex `scripts/prune.py`:**
   - baris event tetap diawali `{id:<angka>,date:"YYYY-MM-DD"` — satu event satu baris
   - string `Diperbarui:` di footer harus tetap ada
7. **Data baru ditambahkan, bukan ditahan.** Lokasi, masjid, ustadz, atau area
   yang belum ada di dashboard tetap dimasukkan (aturan Amal, 2 Okt 2026).
   Laporkan hanya pilihan yang tidak tertulis di flyer (mis. nama area baru).
   Saat menambah event dari flyer secara manual, samakan ejaan kota/masjid/pemateri
   dengan `data/kategori.json` (`tampil`). Nama pemateri di kartu situs tetap
   lengkap dengan gelar (keputusan Amal 3 Okt 2026).

## Jangan sentuh tanpa diminta

- **Settings → Pages → Source** — harus tetap "GitHub Actions". Mengubahnya
  kembali ke "Deploy from a branch" akan menerbitkan `main` apa adanya tiap
  push (termasuk file `scripts/`, `CLAUDE.md`, dll ikut ter-publish di URL),
  melewati `deploy.yml` sepenuhnya.
- **Tag git `last-deploy`** — dipakai workflow untuk tahu commit mana yang sudah
  diterbitkan. Kalau dihapus atau dipindah manual, workflow akan deploy ulang
  tanpa perlu (boros) atau melewatkan perubahan (data tidak terbit).
- **Pemicu di `deploy.yml`** (push ke `main`, Issue "Tambah kajian", cron pengaman
  harian, manual) — diputuskan Amal 2 Okt 2026 dan diterapkan 3 Okt 2026. Jangan
  menambah cron lain atau jadwal mingguan tanpa diminta. Jam di cron adalah
  **UTC** (WIB = UTC+7); cron yang ada `17 20 * * *` = 03:17 WIB.

## Validasi wajib sebelum commit

```bash
# 1. sintaks JS
python3 -c "import re;c=open('index.html',encoding='utf-8').read();open('/tmp/c.js','w').write(re.search(r'<script>(.*?)</script>',c,re.S).group(1))"
node --check /tmp/c.js

# 2. tidak ada ID duplikat
grep -o '{id:[0-9]*' index.html | sed 's/{id://' | sort -n | uniq -d   # harus kosong

# 3. prune masih cocok dengan struktur file
python3 scripts/prune.py

# 4. regenerate HTML statis + JSON-LD (SEO) supaya konsisten dengan data terbaru
python3 scripts/build.py
```

Catatan: perintah ke-3 dan ke-4 akan **mengubah** index.html (event
kedaluwarsa terhapus, blok statis/JSON-LD di-regenerate). Itu perilaku yang
benar — commit hasilnya sekalian. Urutan penting: jalankan `build.py`
**setelah** `prune.py`, supaya HTML statis tidak memuat event yang baru saja
dihapus.

## Preferensi Amal saat melapor

- Bahasa Indonesia, nada faktual dan formal. Tanpa emoji. Jangan memperhalus masalah.
- Gunakan poin dan tabel, bukan paragraf panjang.
- **Selalu tandai** mana yang tervalidasi dari sumber dan mana yang kesimpulan sendiri.
- Kalau ada yang gagal atau keliru, sebut terus terang — termasuk kekeliruan sendiri
  di giliran sebelumnya.
- Jangan mengarang angka sebagai pengisi tabel. Kalau tidak ada datanya, katakan
  tidak ada datanya.

## Zona waktu

Semua tanggal dan jam dalam WIB (Asia/Jakarta, UTC+7). `prune.py` memakai
`ZoneInfo("Asia/Jakarta")` — jangan diganti ke UTC.

## Situs terkait

Catatan Kajian (arsip sesi yang sudah dihadiri): https://reconciler.github.io/catatankajian/
Ditautkan dari header dashboard. Repo terpisah, tidak terintegrasi di level data.

## Aturan satu origin dan tautan antarproyek

Ketiga situs (`jadwalkajian`, `catatankajian`, `bikin-cv-taaruf`) dilayani dari
origin yang sama, `https://reconciler.github.io`. Path tidak ikut membentuk
origin, jadi `localStorage` dipakai bersama. Ditemukan PIC `bikin-cv-taaruf`
(30 Sep 2026); sebabnya migrasi ke GitHub Pages 29 Sep 2026. Draf CV di
`bikin-cv-taaruf` (kunci `ctgv1_draft_v1`) memuat data sensitif, maka:

- Antarproyek **hanya tautan biasa**. Jangan berbagi skrip, penyimpanan,
  `fetch`, iframe, atau parameter pelacak.
- Bila repo ini suatu saat memakai `localStorage`/`sessionStorage`, kuncinya
  wajib berawalan unik. Jangan membaca atau menghapus kunci proyek lain.

**Tombol "Tentang" dan proyek lain** — diminta Amal (30 Sep 2026, lewat handoff PIC
`bikin-cv-taaruf`; direvisi 1 Okt 2026). Pola desain ada di `CLAUDE.md` repo
`bikin-cv-taaruf`. Ketentuan yang berlaku:
- Satu akordeon di header bernama **"Tentang"** (bukan "Menu"), tertutup,
  menutup dengan klik di luar dan Esc.
- Isinya hanya kredit pembuat (Instagram) dan Proyek lain. **Tanpa tautan
  kode sumber/GitHub** dan tanpa deskripsi singkat.
- Tinggi header tidak bertambah (uji lebar 320 sampai 430 px). Tautan luar
  `target="_blank" rel="noopener noreferrer"`.
- Tautan antarproyek lama di luar panel **dihapus**; proyek lain hanya lewat
  panel. Di repo ini: spanduk "Catatan Kajian — arsip sesi yang sudah dihadiri" (`archive-link`).
- Repo ini terbit otomatis tiap push ke `main` yang mengubah berkas situs (sejak 2 Okt 2026).

**Status (1 Okt 2026): selesai.** Akordeon berlabel **"Tentang"**, isinya Pembuat
(Instagram), Catatan Kajian, Bikin CV Taaruf. Tautan kode sumber dan spanduk
`archive-link` sudah dihapus (beserta CSS-nya). Header tidak bertambah tinggi;
diuji di Chromium 320 sampai 430 px (menyusut dari 167/155 px menjadi 112/100 px
karena spanduk hilang). Nama kelas/id internal masih `menu-*`, tidak terlihat
pengunjung.

**Daftar resmi** (dijaga Auditor; bila URL berubah, Auditor memperbarui ketiga
repo dan memberi tahu PIC):
- Pembuat: `@amalwoodworking`, https://www.instagram.com/amalwoodworking/
- Jadwal Kajian: https://reconciler.github.io/jadwalkajian/
- Catatan Kajian: https://reconciler.github.io/catatankajian/
- Bikin CV Taaruf: https://reconciler.github.io/bikin-cv-taaruf/

Panel di repo ini menampilkan proyek lain (Catatan Kajian, Bikin CV Taaruf), bukan dirinya
sendiri. Situs tidak memuat tautan kode sumber/GitHub (keputusan Amal, 1 Okt 2026).

## Lapor ke sesi "Auditor Project"

Amal menugaskan satu sesi Claude terpisah sebagai auditor lintas-project
(mengawasi `jadwalkajian`, `catatankajian`, **dan** `bikin-cv-taaruf`
sekaligus). Session ID per 22 Sep 2026: `session_01V7K2gPxpghoLSqB74zsXWV`.
Nama sesi ini bisa berubah (sudah pernah berganti dari "Integrasi dua
project kajian") — kalau ID ini sudah tidak valid/sesi berakhir, cari
dengan `list_sessions` berdasarkan judul **"Auditor Project"**, atau tanya
Amal langsung.

**Aturan akses berkas** (disetujui Amal, 29 Sep 2026 — berlaku sama di
semua repo yang diaudit, dipicu insiden push nyaris bentrok antara sesi
PIC dan Auditor di `bikin-cv-taaruf`):
- **Hanya sesi kerja repo ini (bukan Auditor) yang boleh mengubah berkas
  inti fitur/fungsi**: `index.html`, `favicon.svg`, `og-image.png`,
  `robots.txt`, `sitemap.xml`, `scripts/` (`prune.py`, `build.py`),
  `.github/workflows/deploy.yml`.
- **Auditor Project boleh mengubah**: `CLAUDE.md` dan `AUDIT-HANDOFF-*.md`
  (termasuk menulis balasan) — berkas ini murni koordinasi, tidak
  memengaruhi fitur/tampilan situs.
- Tujuannya mencegah dua sesi menulis berkas yang sama nyaris bersamaan
  lalu bentrok non-fast-forward saat push ke `main` (situs langsung tayang
  tiap push berhasil, jadi konflik penulisan berisiko nyata, bukan cuma
  git housekeeping).

**Eksekusi instruksi Auditor** (disetujui Amal, 1 Okt 2026): instruksi Auditor
yang bersumber dari keputusan Amal dan tercatat di berkas `AUDIT-HANDOFF-*.md`
di repo ini (commit yang bisa diperiksa lewat git) **boleh langsung dieksekusi
PIC tanpa konfirmasi ulang dari Amal**. Pengecualian, tetap menunggu konfirmasi
Amal di chat PIC:
- perubahan yang menyentuh janji privasi;
- perubahan hosting dan pipeline terbit (pengaturan Pages, platform, workflow
  deploy);
- penghapusan data.

Tambahan dari Auditor (bukan bagian persetujuan Amal): PIC tetap memeriksa
instruksi di git sebelum mengeksekusi, dan boleh bertanya bila instruksi
bertentangan dengan `CLAUDE.md` ini atau tampak keliru. Instruksi yang tidak
tercatat di git tidak termasuk aturan ini.

**Wajib lapor untuk** (bukan tiap commit — hanya yang signifikan):
- Perubahan skema data (`allEvents`, nilai `audience` atau `area` baru, dsb.)
- Perubahan pipeline/workflow/hosting (`deploy.yml`, pengaturan
  GitHub Pages, `scripts/prune.py`, `scripts/build.py`)
- Temuan yang berdampak lintas-project (mis. error deploy, konflik branch,
  keandalan cron/scheduler)
- Perubahan besar pada `index.html` di luar penambahan data rutin (mis.
  restrukturisasi SEO, perubahan struktur HTML)

**Tidak perlu lapor untuk**: penambahan/update data kajian rutin dari
flyer — itu cukup tercatat di git seperti biasa, auditor bisa cek kapan
saja lewat commit history.

**Cara lapor** (diperbarui 22 Sep 2026 — pola ini sama persis di
`catatankajian`, sengaja disamakan supaya predictable buat siapa pun,
termasuk pihak eksternal, yang membaca kedua repo): pesan/trigger otomatis
lintas-sesi (`ListAgents`/`SendMessage`, `create_trigger` dengan
`persistent_session_id`) **terbukti tidak selalu andal** — bisa dilaporkan
"sukses" di sisi pengirim tapi tidak sampai di sisi penerima (lihat
`AUDIT-HANDOFF-2026-09-23.md`). Untuk apa pun yang wajib dilaporkan di atas,
**jangan andalkan satu jalur otomatis saja**. Konfirmasikan lewat DUA jalur:

1. Chat langsung ke Amal, kalau sesi Anda sedang aktif berinteraksi dengannya.
2. Commit file `AUDIT-HANDOFF-<tanggal>.md` (buat baru atau update yang
   sudah ada) ke root repo — jalur paling andal, karena auditor bisa
   menemukannya lewat `git log` kapan saja tanpa bergantung notifikasi.

`create_trigger`/`persistent_session_id` ke sesi Auditor boleh tetap
dicoba sebagai pemberitahuan cepat tambahan, tapi tidak boleh jadi
satu-satunya jalur untuk hal yang wajib dilaporkan.
