# Jadwal Kajian — panduan kerja

Dashboard jadwal kajian Jabodetabek & sekitarnya.
Live: https://jadwalkajian.netlify.app · Pemilik: Amal (@amalwoodworking)

## Struktur

```
index.html                           # seluruh dashboard — HTML+CSS+JS satu file
netlify.toml                         # konfigurasi build; MEMATIKAN deploy-on-push
robots.txt                           # izinkan semua crawler, tunjuk ke sitemap.xml
sitemap.xml                          # daftar URL untuk Google Search Console (1 URL, single-page)
favicon.svg                          # ikon tab browser
scripts/prune.py                     # hapus event lewat + perbarui stempel footer
scripts/build.py                     # generate HTML statis + JSON-LD (SEO) dari allEvents
.github/workflows/weekly-deploy.yml  # prune + build + terbitkan situs, Jumat 15:00 WIB
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

`index.html` **wajib** di root dengan nama persis itu — Netlify menyajikannya
sebagai homepage.

## PENTING — push TIDAK menerbitkan situs

Baca ini sebelum melapor apa pun ke Amal.

`netlify.toml` berisi `ignore = "exit 0"`. Artinya **setiap build yang dipicu
push akan dibatalkan Netlify.** Commit dan push sebanyak apa pun tidak mengubah
situs live dan tidak memakan biaya.

Situs hanya terbit lewat workflow `weekly-deploy.yml`, yang memanggil Netlify
build hook. Build hook mengabaikan aturan `ignore`, jadi itulah satu-satunya
jalur publikasi.

Konsekuensi untuk sesi ini:

- Setelah commit + push, **jangan katakan event sudah tayang.** Katakan event
  sudah masuk antrean, dan akan terbit pada jadwal berikutnya.
- Jadwal terbit otomatis: **setiap Jumat pukul 15:00 WIB** (cron `0 8 * * 5`).
- Batas commit agar ikut terbit pekan itu: **Jumat sebelum jam 3 sore WIB.**
- Kalau ada kajian mendesak yang harus tayang sekarang, Amal bisa menjalankan
  workflow manual: tab Actions → *Prune & deploy mingguan* → Run workflow.
  **Sarankan ini bila relevan, tapi jangan jalankan tanpa persetujuan Amal** —
  setiap eksekusi memakan 15 kredit.

### JEDA SEMENTARA — kredit tim Netlify habis (sejak 22 Sep 2026)

Kredit **tim** Netlify "Amal" (dipakai bersama `jadwalkajian` **dan**
`catatankajian` — satu tim yang sama) tersisa 14,9/300 pada 22 Sep 2026,
di bawah 15 kredit yang dibutuhkan satu deploy. Regrant berikutnya: **12
Oktober 2026**.

Ditambahkan step **"Cek masa jeda kredit Netlify"** di `weekly-deploy.yml`
(commit `4e7ddc0`, oleh sesi lain — "Integrasi dua project kajian") yang
melewati pemicuan build hook + penandaan tag `last-deploy` sampai 12 Okt
2026. **Prune dan build tetap jalan normal tiap Jumat (gratis)** — cuma
penerbitan situsnya yang ditunda.

- Jumat **25 Sep, 2 Okt, 9 Okt 2026**: workflow jalan, tapi deploy
  **sengaja dilewati** — ini bukan kegagalan.
- Jumat **16 Okt 2026** dan seterusnya: jalan normal lagi tanpa perlu
  diubah manual.
- **Jangan hapus/revert gerbang ini atau coba trigger manual sebelum 12
  Okt**, kecuali Amal memintanya secara eksplisit (dan kalau diminta,
  ingatkan bahwa itu kemungkinan besar akan gagal karena saldo tidak
  cukup, atau Amal perlu upgrade plan Netlify dulu).
- Setelah 12 Okt dan kredit dipastikan sehat, step "Cek masa jeda kredit"
  dan kondisi `steps.jeda.outputs.boleh == 'true'` di tiga step terakhir
  boleh dihapus.

## Anggaran biaya

Netlify Free = **300 kredit/bulan**, hard limit, tidak carry-over, situs
dijeda kalau habis. Deploy produksi = **15 kredit**. Plafon ~20 deploy/bulan.

**Kredit ini per-tim, bukan per-situs** — dipakai bersama situs
`catatankajian` (tim Netlify "Amal" yang sama). Deploy di salah satu situs
mengurangi jatah untuk situs satunya juga. Lihat bagian "JEDA SEMENTARA" di
atas untuk status kredit terkini.

Karena push tidak memicu deploy, **jumlah commit tidak lagi memengaruhi biaya
sama sekali.** Yang memakan kredit hanya eksekusi workflow deploy. Jadi tidak
perlu menggabungkan flyer ke satu commit demi hemat — commit sesering yang
paling rapi untuk riwayat.

Prune ikut berjalan di dalam workflow deploy, jadi tidak menambah deploy
terpisah. Prune bersifat kosmetik: dashboard sudah menyembunyikan event lewat
di sisi browser (`isEventPast`/`up` di index.html), jadi menunda prune tidak
membuat pengunjung melihat data basi.

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

- **`netlify.toml`** — mengubah `ignore` akan menghidupkan lagi deploy-on-push
  dan bisa menghabiskan jatah kredit dalam hitungan hari.
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

Catatan Kajian (arsip sesi yang sudah dihadiri): https://catatankajian.netlify.app
Ditautkan dari header dashboard. Repo terpisah, tidak terintegrasi di level data.
