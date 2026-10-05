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
scripts/test_ingest.py               # uji lokal ingest (python3 scripts/test_ingest.py); memakai data BEKU di scripts/fixtures/
scripts/fixtures/                    # events.txt (isi allEvents) + kategori.json beku untuk uji; perbarui bila skema event/master berubah
.github/ISSUE_TEMPLATE/              # DIBUAT OTOMATIS dari data/kategori.json; jangan edit manual
docs/formulir-issue.md                # rincian sistem input Issue (internal, tidak tayang; baca sebelum mengubah ingest/adapter/templat)
docs/riwayat-migrasi.md              # arsip sejarah migrasi Netlify -> Pages (bukan aturan aktif)
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
- **Uji logika di CI (Q13, 3 Okt 2026):** pada event `push` yang mengubah `scripts/**` atau `deploy.yml`, langkah
  "Uji logika skrip" menjalankan `scripts/test_ingest.py` SEBELUM ingest; **merah = push kode itu tidak diterbitkan**.
  Tidak berlaku untuk `issues`, `schedule`, `workflow_dispatch`, maupun push yang hanya mengubah data event
  (`index.html`). Uji memakai data beku `scripts/fixtures/` dan jam terkunci (`JADWAL_HARI_INI`, hanya untuk
  uji; jangan dipakai di produksi). Uji ber-PyYAML/node dilewati (bukan gagal) bila alatnya tidak ada.
  Integritas data nyata hanya peringatan. Jalankan lokal sebelum push kode: `python3 scripts/test_ingest.py`.
  **Keputusan Amal 3 Okt 2026 (opsi A):** tiga uji ber-PyYAML (templat Tambah, templat Koreksi/hapus, urutan dropdown)
  sengaja hanya berjalan lokal; **jangan** menambah paket PyPI ke workflow untuk itu kecuali Amal memutuskan.
- **Satu komit bot per run (B1, 3 Okt 2026):** hasil ingest, prune, build, dan templat formulir Issue
  (`.github/ISSUE_TEMPLATE/`, ditulis `ingest.py`) masuk satu komit; push ditolak = reset ke `origin/main` dan ulangi
  ingest (sampai 4 kali). Langkah "Perbarui templat" terpisah dihapus. Alur ini diuji lokal dengan remote bare
  (tanpa perubahan, event manual, Issue, push ditolak, templat saja, penolakan permanen); **belum** teruji dengan
  Issue nyata di GitHub (tunggu Issue nyata Amal berikutnya; jangan menerbitkan data uji ke situs publik).
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

## Input event lewat formulir Issue (sejak 3 Okt 2026) — ringkasan

Jalur input kedua selain "screenshot flyer ke Claude" (keputusan Amal 2 Okt 2026). **Rincian lengkap (kolom,
sintaks Tanggal, rutin otomatis, aturan dumb-proof, Koreksi/hapus, pemateri, masjid): `docs/formulir-issue.md`**
(berkas internal, tidak tayang di situs; baca sebelum mengubah sistem input).

- Cara pakai (Amal): tab Issues -> New issue -> "Tambah kajian" atau "Koreksi atau hapus kajian" -> isi -> Submit.
  Hanya Issue dari `reconciler` yang isinya formulir yang diproses. Dalam beberapa menit: event masuk, situs
  terbit, Issue diberi komentar dan ditutup. **Issue terbuka = belum terbit.** Gagal validasi: Issue tetap terbuka
  dengan komentar alasan; edit Issue untuk memproses ulang.
- Kebijakan: **tolak yang meragukan, jangan diam, jangan terbitkan data yang kemungkinan salah.**
  Koreksi/hapus selalu dua langkah (pratinjau, lalu edit Issue dan tulis `HAPUS n` / `KOREKSI n`).
- **Keamanan (jangan dilanggar):** isi/judul Issue **tidak pernah** diinterpolasi ke `run:` di workflow
  (injeksi skrip), dibaca dari berkas JSON. Baris event ditulis lewat `json.dumps`; `<` `>` ditolak; karakter
  kontrol dibuang. Hanya action resmi `actions/*`.
- **Label kolom = kunci parser.** Mengubah label di `adapter_issue_form.py` (`LABEL`) wajib diikuti pengubahan
  parser. Templat di `.github/ISSUE_TEMPLATE/` dibuat otomatis dari `data/kategori.json`; jangan diedit manual.
- **Id tidak pernah dipakai ulang:** id berikutnya = `core.id_tertinggi(html, kat)` + 1 (bukan max id di
  `index.html` saja). `data/kategori.json` (internal, tidak tayang) menyimpan daftar induk kota/masjid/pemateri,
  `diproses`, `gagal`, `id_tertinggi`; jangan diedit manual kecuali memperbaiki data.
- **Alur flyer ke Claude** tetap memakai langkah manual (edit `index.html`). Samakan ejaan kota/masjid/pemateri
  dengan `tampil` di `data/kategori.json`. Kota/masjid/pemateri **baru tidak perlu lagi diketik ke master**:
  jalankan `python3 scripts/sinkron_master.py` (idempoten, hanya menambah, tanpa jaringan); setiap run `ingest.py`
  juga menyinkronkan master dari event yang ada. Uji: `python3 scripts/test_ingest.py`.
- Dropdown formulir **harus terurut abjad** menurut nama bersih (keputusan Amal 3 Okt 2026), "Lainnya" di akhir;
  tanpa batas jumlah opsi buatan sendiri (keputusan Amal 3 Okt 2026). Daftar kajian boleh kosong (0 event sah).
  **Risiko diterima Amal (3 Okt 2026, tanpa peringatan):** batas jumlah opsi dropdown GitHub tidak terdokumentasi; bila
  terlampaui, kolom Pemateri/Masjid tidak tampil lengkap dan CI tidak mendeteksinya. Cara pulih: `docs/formulir-issue.md`.

## Berkas yang tayang di situs (folder `_site`)

Sejak 1 Okt 2026 workflow **tidak lagi** mengunggah seluruh root repo. Langkah
"Siapkan folder situs (_site)" menyalin hanya: `index.html`, `robots.txt`,
`sitemap.xml`, `favicon.svg`, `og-image.png`. `CLAUDE.md`, `AUDIT-HANDOFF-*.md`,
`scripts/`, `data/`, `docs/`, dan `.github/` **tidak tayang** (workflow gagal bila ada yang ikut
tersalin; `docs` masuk penjaga sejak 3 Okt 2026).

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
  `AUDIT-HANDOFF-2026-09-30.md`, `scripts/prune.py`, `data/kategori.json`, `docs/formulir-issue.md`,
  `docs/riwayat-migrasi.md` 404, **ditambah semua `AUDIT-HANDOFF-*.md` dan `COORDINATION-NOTE-*.md` yang ada di repo**
  (dihitung otomatis tiap run; handoff baru otomatis terjaga). Gagal = run merah dan
  tag `last-deploy` tidak dipindah, jadi run berikutnya menerbitkan ulang.
  **Jangan dilonggarkan supaya hijau**; selidiki penyebabnya. Uji ini tidak
  menilai tampilan. Bila nama berkas internal di daftar `INTERNAL` pada langkah
  itu berubah, perbarui daftarnya.
- Sesi kerja tidak bisa mengakses `reconciler.github.io`; verifikasi situs live
  dilakukan oleh langkah uji otomatis di atas (hasilnya ada di log run Actions).

## Riwayat migrasi Netlify -> GitHub Pages

Arsip sejarah (bukan aturan aktif): `docs/riwayat-migrasi.md`. Ringkas: pindah 29 Sep 2026; `netlify.toml` dan
`NETLIFY_BUILD_HOOK` sudah tidak dipakai; jadwal mingguan Jumat dihapus Amal 2 Okt 2026 (lihat bagian Publikasi).

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
   - `const allEvents=[` dan penutupnya `];` harus tetap masing-masing di barisnya sendiri. Daftar event boleh
     **kosong** (semua kedaluwarsa; Q3, 3 Okt 2026) hanya bila penanda itu utuh dan badan array benar-benar
     kosong; badan berisi baris yang tidak dikenali parser tetap membuat `prune.py`/`build.py` gagal
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

# 5. (jalur flyer manual) samakan master kota/masjid/pemateri dengan event; commit kategori.json bila berubah
python3 scripts/sinkron_master.py
```

Catatan: perintah ke-3 dan ke-4 akan **mengubah** index.html (event
kedaluwarsa terhapus, blok statis/JSON-LD di-regenerate). Itu perilaku yang
benar — commit hasilnya sekalian. Urutan penting: jalankan `build.py`
**setelah** `prune.py`, supaya HTML statis tidak memuat event yang baru saja
dihapus.

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

## Aturan lintas-repo (teks identik di jadwalkajian, catatankajian, bikin-cv-taaruf)

Ditetapkan/dikonfirmasi Amal 3 Okt 2026 (butir 14-19: 5 Okt 2026). **Ubah serentak di ketiga repo (dijaga Auditor); jangan hanya satu.**

1. **Keputusan tanpa dampak tampilan atau fungsi** diambil sendiri oleh sesi kerja dan dicatat; jangan menunggu Amal.
   Perubahan tampilan, fungsi, privasi, hosting/pipeline terbit, atau penghapusan data tetap perlu konfirmasi Amal.
2. **Cakupan persetujuan:** persetujuan Amal hanya untuk butir yang disebut. Pengecualian pada butir 1 (pipeline, privasi,
   penghapusan data) dikonfirmasi Amal di **chat sesi kerja repo itu**; kutipan Amal yang disampaikan sesi lain tidak cukup.
3. **Menyimpang dari spesifikasi** (dari Auditor atau siapa pun) boleh bila ada metode yang lebih aman. Catat penyimpangan
   dan alasannya di handoff, lalu lapor.
4. **Temuan janggal dilaporkan disertai usulan perbaikan**, bukan hanya temuan.
5. **Data uji:** jangan menerbitkan data uji ke situs publik tanpa bertanya Amal; pakai uji lokal.
6. **Urutan perubahan pipeline:** satu per push, risiko rendah dulu. Push yang mengubah `deploy.yml` menjalankan versi
   baru alur itu. Buat kondisi tepi aman sebelum perubahan yang mengandalkannya.
7. **Dependensi pihak ketiga:** salin ke `lib/` (atau setara), patok versi, cocokkan integritas ke registry npm; jangan
   memuat skrip dari CDN tanpa SRI.
8. **Klaim harus benar** untuk proyek itu: dokumen, UI, meta tag, dan data terstruktur tidak boleh mengklaim hal yang tidak
   ada (mis. `SearchAction` tanpa fungsinya; "tidak ada data terkirim" bila Google Fonts dimuat).
9. **Simetri:** perubahan cara komunikasi, pelaporan, atau struktur koordinasi diterapkan serentak di ketiga repo.
10. **Kebersihan berkas:** hapus berkas koordinasi yang tidak lagi relevan; pertahankan yang masih atau akan dipakai.
11. **Verifikasi tampilan:** uji otomatis tidak menilai tampilan, dan sesi kerja tidak bisa membuka `reconciler.github.io`.
    Laporan perubahan tampilan wajib menyebut "belum dilihat di perangkat nyata" sampai Amal memeriksa.
12. **Kepastian terbit lebih penting daripada kecepatan.**
13. **Aksesibilitas:** untuk perubahan UI, jalankan axe-core di Chromium bila tersedia; laporkan 0 pelanggaran atau daftar
    temuannya.
14. **Konteks kurang:** baca riwayat chat, handoff, dan git dulu; baru sumber eksternal.
15. **Status ragu** (termasuk klaim "sukses" dari jalur otomatis): verifikasi manual sendiri, lalu konfirmasi ke Amal dan
    Auditor lewat chat + git.
16. **Batas buatan:** jangan pasang tanpa dasar platform yang terverifikasi (kecuali keamanan); catat risikonya.
17. **Pembagian kerja:** kerjakan sendiri yang bisa; minta Amal hanya untuk akses yang sesi tak punya. Settings Pages hanya
    Amal yang ubah: PIC siapkan workflow + langkahnya, dan beri jalur kembali satu langkah sebelum mengalihkan pipeline.
18. **Repo publik:** jangan commit data pribadi (isi CV, kontak, kredensial), termasuk di handoff dan kutipan chat.
19. **Praktik uji** (bukan aturan keras): uji deterministik (data beku, jam terkunci); simulasikan skrip workflow lokal
    (jalur sukses + gagal) sebelum push; UI: screenshot 320/375/430 px, font asli, jaringan luar diblokir.

## Preferensi melapor (teks identik di jadwalkajian, catatankajian, bikin-cv-taaruf)

Berlaku untuk laporan, handoff, dan chat. Ditetapkan Amal 5 Okt 2026.

- **Bahasa:** Indonesia, campur English untuk istilah yang populer (mis. deploy, commit, workflow). **Concise, simpel,
  spesifik**: hemat token dan mudah dipahami Amal.
- Faktual dan formal, tanpa emoji; pakai poin/tabel, bukan paragraf panjang. Jangan memperhalus masalah.
- Tandai mana yang **tervalidasi** (sumber) vs **kesimpulan sendiri**. Jangan mengarang hasil atau angka; bila tak ada
  data, atau alat/akses tak tersedia, katakan.
- Gagal atau keliru (termasuk kesalahan sendiri) disebut terus terang.
- Penjelasan "awam": analogi + tabel kecil, tanpa jargon.
- Akhiri pekerjaan besar dengan "yang perlu diketahui": belum terbukti, perubahan perilaku, kejadian otomatis, keputusan
  yang menunggu.

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
