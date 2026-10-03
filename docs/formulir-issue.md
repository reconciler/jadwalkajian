# Formulir Issue "Tambah kajian" dan "Koreksi atau hapus kajian" — rincian

Dipindahkan verbatim dari `CLAUDE.md` pada 3 Okt 2026 (keputusan Amal: usulan efisiensi no. 3,
supaya `CLAUDE.md` tidak memuat rincian yang hanya perlu saat mengubah sistem input). **Baca berkas ini
sebelum mengubah** `scripts/ingest*.py`, `scripts/adapter_*.py`, `scripts/koreksi_core.py`,
`scripts/tanggal_bebas.py`, templat `.github/ISSUE_TEMPLATE/`, atau `data/kategori.json`.
Aturan keras yang tetap di `CLAUDE.md`: keamanan (isi Issue tidak masuk `run:`), label kolom = kunci parser,
id tidak dipakai ulang, uji `python3 scripts/test_ingest.py` wajib hijau sebelum push.

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
  `2026-10-10`; tahun boleh dihilangkan **tetapi** tanggal tanpa tahun yang jatuh lebih dari **180 hari** ke depan ditolak ("tulis tahunnya"; tepat 180 hari lolos, tanggal dengan tahun eksplisit hanya terkena batas 730 hari); nama hari di depan tanggal = pemeriksa;
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
  (ejaan konsisten).
- **Sinkronisasi master dari event (A1, 3 Okt 2026):** `core.sinkronkan_master(html, kat)` menyamakan
  `data/kategori.json` dengan `index.html`. Event manual yang kota/masjid/pemateri-nya belum ada di master
  menambahkannya: masjid dikenali dari `tampil` + kota (`area`); `nama` = teks tanpa akhiran ` (Kota)`;
  pemateri yang cocok lewat `nama`/`tampil`/`alias` (termasuk nama bersih tanpa gelar) tidak ditambah; "Belum
  ditentukan" dilewati; pemateri berawalan Ustadzah/Ustadzaat ditandai `perempuan`. **Idempoten dan hanya
  menambah** (entri master yang tidak dipakai event tidak pernah dihapus). Event yang tidak bisa diurai
  (kota/masjid kosong, dsb.) menghasilkan **peringatan** (stderr), bukan galat. Dijalankan di awal **setiap** run
  `ingest.py` (semua pemicu); `kategori.json` hanya berubah bila ada selisih, jadi cron tanpa selisih tidak
  menghasilkan komit. Komit sinkron-saja berjudul "Sinkron master dari index.html". CLI tanpa jaringan:
  `python3 scripts/sinkron_master.py [--cek]` (`--cek` hanya menampilkan selisih). Pada data per 3 Okt 2026
  sinkronisasi pertama **tidak menghasilkan selisih**.
- **Uji integritas data hanya peringatan** (keputusan Auditor/Amal 3 Okt 2026; aturan tetap 7: data dari flyer
  tidak boleh ditahan): uji "integritas data nyata" di `test_ingest.py` mencetak `PERINGATAN (integritas data)`
  dan tidak pernah gagal. Uji logika (parser, ingest, koreksi, urutan dropdown) boleh gagal.
- **Urutan dropdown (A2):** pemateri terurut abjad menurut **nama bersih** tanpa gelar (huruf besar/kecil
  diabaikan, `str.casefold`), masjid menurut label `Nama (Kota)`, kota menurut nama; "Belum ditentukan" /
  "Online" / "Lainnya" / "Kota lain" tetap di akhir. Uji `A2` gagal bila entri baru menyisip tidak terurut
  (diuji dengan data nyata dan data acak berhuruf campur/aksen; mutasi urutan di adapter ditangkap).
- **Catatan angka rancangan:** `MAKS_OPSI_DROPDOWN = 150` di `adapter_issue_form.py` adalah angka rancangan
  PIC (bukan batas GitHub yang terverifikasi). Bila opsi Pemateri atau Masjid melebihi itu, kolom otomatis
  menjadi isian teks bebas (bukan dropdown). Per 3 Okt 2026: 99 opsi pemateri, 28 masjid.
