# Jadwal Kajian — panduan kerja

Dashboard jadwal kajian Jabodetabek & sekitarnya.
Live: https://jadwalkajian.netlify.app · Pemilik: Amal (@amalwoodworking)

## Struktur

```
index.html                           # seluruh dashboard — HTML+CSS+JS satu file
netlify.toml                         # konfigurasi build; MEMATIKAN deploy-on-push
scripts/prune.py                     # hapus event lewat + perbarui stempel footer
.github/workflows/weekly-deploy.yml  # prune + terbitkan situs, Jumat 15:00 WIB
```

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

## Anggaran biaya

Netlify Free = **300 kredit/bulan**, hard limit, tidak carry-over, situs
dijeda kalau habis. Deploy produksi = **15 kredit**. Plafon ~20 deploy/bulan.

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
| `audience` | `Terbuka untuk umum` atau `Khusus Akhwat` |
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
```

Catatan: perintah ke-3 akan **mengubah** index.html bila ada event kedaluwarsa.
Itu perilaku yang benar — commit hasilnya sekalian.

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
