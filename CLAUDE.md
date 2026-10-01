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
.github/workflows/weekly-deploy.yml  # prune + build + terbitkan ke GitHub Pages, Jumat 15:00 WIB
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

`build.py` dijalankan otomatis di `weekly-deploy.yml` setelah `prune.py`,
jadi tidak perlu dijalankan manual tiap kali menambah event — **kecuali**
saat validasi lokal sebelum commit (lihat bagian Validasi di bawah), supaya
`index.html` yang di-commit sudah konsisten dengan data terbaru.

Meta tag statis (`description`, `og:*`, `twitter:*`, `canonical`) ditulis
manual sekali di `<head>`, tidak berubah tiap event — tidak perlu diupdate
rutin. **Belum ada `og:image`** (butuh aset gambar banner asli dari Amal,
belum dibuat).

`index.html` **wajib** di root dengan nama persis itu — GitHub Pages
menyajikannya sebagai homepage.

## PENTING — push TIDAK menerbitkan situs

Baca ini sebelum melapor apa pun ke Amal.

Situs di-host **GitHub Pages** (Settings → Pages → Build and deployment →
Source: **"GitHub Actions"**, bukan "Deploy from a branch"). Publikasi
**hanya** terjadi lewat job di `weekly-deploy.yml` — push biasa ke `main`
tidak memicu apa pun di luar itu. Ini murni untuk menjaga **irama
publikasi** (lihat di bawah), bukan lagi soal biaya — GitHub Pages gratis
tanpa batas kredit untuk situs sekecil ini.

Konsekuensi untuk sesi ini:

- Setelah commit + push, **jangan katakan event sudah tayang.** Katakan event
  sudah masuk antrean, dan akan terbit pada jadwal berikutnya.
- Jadwal terbit otomatis: **setiap Jumat pukul 15:00 WIB** (cron `0 8 * * 5`).
- Batas commit agar ikut terbit pekan itu: **Jumat sebelum jam 3 sore WIB.**
- Kalau ada kajian mendesak yang harus tayang sekarang, Amal bisa menjalankan
  workflow manual: tab Actions → *Prune & deploy mingguan* → Run workflow.
  **Gratis** — boleh disarankan dan dijalankan kapan pun perlu, tidak perlu
  menahan diri seperti waktu masih di Netlify.
- **Catatan keandalan cron**: pada 25 Sep 2026, cron ini pernah telat >5 jam
  dari jadwalnya (delay dari sisi GitHub, workflow-nya sendiri tidak
  bermasalah). Kalau situs lama tidak ter-update setelah Jumat 15:00 WIB,
  cek tab Actions dulu sebelum menyimpulkan ada yang rusak.

### WAJIB: deploy manual segera setelah push yang memperbaiki bug di situs

**Insiden 29 Sep 2026**: commit `0e0c688` memperbaiki link rusak (menunjuk
ke domain Netlify lama) di tombol Catatan Kajian, tapi tidak langsung
di-deploy — situs live tetap menampilkan link rusak selama ±1 jam sampai
ada yang sadar dan trigger manual. Root cause: publikasi memang sengaja
tidak otomatis tiap push (lihat di atas), tapi itu berlaku untuk **data
kajian rutin**, bukan untuk **bug/defect yang sedang tayang di situs**.

Aturan untuk mencegah ini terulang — **berlaku untuk sesi kerja repo ini
DAN untuk siapa pun yang push ke `main`**:

- Kalau commit yang baru di-push **memperbaiki sesuatu yang salah/rusak di
  situs live** (link mati, salah domain, bug tampilan, kesalahan struktur
  HTML, dll.) — **langsung trigger workflow manual** (tab Actions →
  *Prune & deploy mingguan* → Run workflow) begitu selesai push. Jangan
  tunggu Jumat, dan jangan asumsikan sesi/orang lain akan melakukannya.
- Ini **berbeda** dari commit yang menambah/mengubah **data kajian rutin**
  dari flyer — itu tetap boleh menunggu jadwal mingguan seperti biasa,
  sesuai desain irama publikasi yang sudah dipilih Amal.
- Bedanya: data basi (event lama belum ke-prune) tidak terlihat pengunjung
  karena `isEventPast`/`up()` di JS sudah menyaring sisi browser — jadi
  aman ditunda. **Bug/link rusak justru terlihat langsung** — menunda
  publikasinya berarti sengaja membiarkan situs live rusak lebih lama dari
  perlu, padahal deploy manual gratis dan instan.
- Setelah trigger manual, **verifikasi run-nya `success`** (cek tab
  Actions atau `list_workflow_runs`) sebelum melapor ke Amal bahwa
  perbaikan sudah tayang — jangan asumsikan trigger otomatis berhasil.

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
  `weekly-deploy.yml`, atas keputusan Amal 1 Okt 2026): runner memeriksa URL
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
mingguan (Jumat 15:00 WIB) **dipertahankan** karena alasannya independen
dari soal biaya — supaya jadwal akhir pekan sudah stabil sebelum orang
merencanakan Sabtu-Ahad, bukan berubah-ubah kapan saja sepanjang minggu.

Prune tetap berjalan di dalam workflow yang sama, jadi tidak menambah
job terpisah. Prune bersifat kosmetik: dashboard sudah menyembunyikan event
lewat di sisi browser (`isEventPast`/`up` di index.html), jadi menunda
prune tidak membuat pengunjung melihat data basi.

## Alur kerja utama

Amal mengirim screenshot flyer kajian (biasanya dari Instagram masjid). Tugasnya:
baca flyer, ekstrak detail, tambahkan sebagai entri baru di array `allEvents`,
validasi, commit, push. Lalu beri tahu kapan itu akan terbit (lihat bagian di atas).

## Skema data

Satu event = satu baris di array `allEvents`, format object literal:

```js
{id:864,date:"2026-09-20",dayShort:"Min 20 Sep",timeLabel:"Ba'da Maghrib",timeOrder:18,title:"...",ustadz:"...",masjid:"...",area:"Jakarta",address:"...",audience:"Terbuka untuk umum",note:"...",isRutin:true},
```

| Field | Aturan |
|---|---|
| `id` | Unik. Ambil dari max id yang ada + 1. **Wajib dicek tidak duplikat.** |
| `date` | `YYYY-MM-DD` |
| `dayShort` | `Sen Sel Rab Kam Jum Sab Min` + tanggal + bulan singkat. Minggu **selalu "Min"**, jangan "Ahd" |
| `timeLabel` | Jam eksak (`19.30 WIB`, `10.00 – 11.45 WIB`) atau waktu sholat (`Ba'da Subuh`, `Dhuha`, `Ba'da Zuhur`, `Ba'da Ashar`, `Ba'da Maghrib`) |
| `timeOrder` | Jam desimal untuk sorting. Subuh 4.5 · Dhuha 9 · Zuhur 12.5 · Ashar 15.5 · Maghrib 18. Untuk jam eksak, pakai jam mulai (19.30 → 19.5) |
| `area` | Persis salah satu: `Depok` `Bogor` `Jakarta` `Bekasi` `Jawa Tengah` `Jawa Barat` `Online` |
| `audience` | `Terbuka untuk umum`, `Khusus Akhwat`, atau `Khusus Ikhwan` |
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
4. **Hanya area Jabodetabek & sekitarnya.** Masjid di luar itu (mis. Malang) jangan dimasukkan.
5. **Bedakan fakta flyer vs kesimpulan sendiri.** Kalau nama ustadz, alamat, atau jam
   tidak tercantum eksplisit dan diisi dari inferensi atau pengetahuan umum,
   **katakan eksplisit** di laporan. Amal secara khusus meminta ini.
6. **Jangan ubah `index.html` dengan cara yang merusak regex `scripts/prune.py`:**
   - baris event tetap diawali `{id:<angka>,date:"YYYY-MM-DD"` — satu event satu baris
   - string `Diperbarui:` di footer harus tetap ada

## Jangan sentuh tanpa diminta

- **Settings → Pages → Source** — harus tetap "GitHub Actions". Mengubahnya
  kembali ke "Deploy from a branch" akan menerbitkan `main` apa adanya tiap
  push (termasuk file `scripts/`, `CLAUDE.md`, dll ikut ter-publish di URL),
  melewati logika mingguan di `weekly-deploy.yml` sepenuhnya.
- **Tag git `last-deploy`** — dipakai workflow untuk tahu commit mana yang sudah
  diterbitkan. Kalau dihapus atau dipindah manual, workflow akan deploy ulang
  tanpa perlu (boros) atau melewatkan perubahan (data tidak terbit).
- **Baris cron di `weekly-deploy.yml`** — jadwalnya sudah dipilih Amal
  (Jumat 15:00 WIB, untuk mengantisipasi orang merencanakan akhir pekan).
- Catatan: jam di cron adalah **UTC**. `08:00 UTC` masih hari yang sama di WIB,
  tapi jam >= `17:00 UTC` mendarat di **hari berikutnya** WIB. Mudah salah sehari.

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
- Repo ini terbit lewat workflow manual atau jadwal Jumat; untuk perubahan ini, trigger manual setelah push.

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
  `.github/workflows/weekly-deploy.yml`.
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
- Perubahan skema data (`allEvents`, nilai `audience` baru, dsb.)
- Perubahan pipeline/workflow/hosting (`weekly-deploy.yml`, pengaturan
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
