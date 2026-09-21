# Jadwal Kajian — panduan kerja

Dashboard jadwal kajian Jabodetabek & sekitarnya.
Live: https://jadwalkajian.netlify.app · Pemilik: Amal (@amalwoodworking)

## Struktur

```
index.html                        # seluruh dashboard — HTML+CSS+JS dalam satu file
scripts/prune.py                  # hapus event lewat + perbarui stempel footer
.github/workflows/daily-prune.yml # menjalankan prune.py tiap 00:05 WIB
```

`index.html` **wajib** berada di root dengan nama persis itu — Netlify menyajikannya
sebagai homepage. Netlify auto-deploy dari branch `main`.

## Alur kerja utama

Amal mengirim screenshot flyer kajian (biasanya dari Instagram masjid). Tugasnya:
baca flyer, ekstrak detail, tambahkan sebagai entri baru di array `allEvents`,
commit, push. Netlify deploy sendiri.

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
   (mis. judul kajian yang sebelumnya generik), **perbarui entri lama** — jangan buat baru.
3. **Jangan tambahkan event yang tanggalnya sudah lewat.** Akan langsung terbuang
   prune berikutnya. Kalau seluruh isi flyer sudah lewat, katakan itu — jangan diam saja.
4. **Hanya area Jabodetabek & sekitarnya.** Masjid di luar itu (mis. Malang) jangan dimasukkan.
5. **Bedakan fakta flyer vs kesimpulan sendiri.** Kalau nama ustadz, alamat, atau jam
   tidak tercantum eksplisit dan diisi dari inferensi/pengetahuan umum, **katakan
   secara eksplisit** di laporan. Amal secara khusus meminta ini.
6. **Jangan ubah `index.html` dengan cara yang merusak regex `scripts/prune.py`:**
   - baris event harus tetap diawali `{id:<angka>,date:"YYYY-MM-DD"` — satu event satu baris
   - string `Diperbarui:` di footer harus tetap ada

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

## Preferensi Amal saat melapor

- Bahasa Indonesia, nada faktual dan formal. Tanpa emoji. Jangan memperhalus masalah.
- Gunakan poin dan tabel, bukan paragraf panjang.
- **Selalu tandai** mana yang tervalidasi dari sumber dan mana yang kesimpulan sendiri.
- Kalau ada yang gagal atau keliru, sebut terus terang — termasuk kekeliruan sendiri
  di giliran sebelumnya.

## Zona waktu

Semua tanggal dan jam dalam WIB (Asia/Jakarta, UTC+7). `prune.py` sudah memakai
`ZoneInfo("Asia/Jakarta")` — jangan diganti ke UTC.

## Situs terkait

Catatan Kajian (arsip sesi yang sudah dihadiri): https://catatankajian.netlify.app
Ditautkan dari header dashboard. Repo terpisah, tidak terintegrasi di level data.
