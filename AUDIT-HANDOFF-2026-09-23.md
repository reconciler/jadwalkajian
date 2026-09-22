# Handoff — repo `jadwalkajian` untuk sesi "Auditor project kajian"

Ditulis oleh sesi Claude "Jadwal kajian repo" (`session_016ryhcUsxwn1LCQ37C6VPUf`),
23 Sep 2026 00:14 WIB, atas permintaan Amal — untuk menghindari miskomunikasi
antar-sesi soal status repo ini.

**Cara pakai dokumen ini**: semua yang ditandai "tervalidasi" di bawah sudah
saya cek langsung lewat git/kode di repo ini pada saat penulisan. Semua yang
ditandai "klaim, belum saya verifikasi independen" datang dari sesi lain atau
dari Amal secara lisan — perlu dicek ulang kalau jadi dasar keputusan.

## 1. Status commit saat ini — tervalidasi

- `main` dan `claude/dreamy-ride-oplf0q` (branch kerja sesi ini) **identik**,
  HEAD di commit **`96522c0`**.
- Branch kerja sesi Anda, `claude/determined-pasteur-3e8e69`, per saat ini
  berhenti di **`4e7ddc0`** — **tertinggal 1 commit** dari `main` (commit
  `96522c0`, prune rutin, lihat §3). Bukan masalah, tapi perlu di-fetch ulang
  kalau Anda mau kerja dari state terbaru.
- Working tree bersih, tidak ada perubahan lokal yang belum di-push.

## 2. Timeline commit relevan di `main` (terbaru → terlama)

| Commit | Ringkasan |
|---|---|
| `96522c0` | Prune rutin (10 event tanggal 22 Sep terhapus otomatis) + regenerate HTML statis/JSON-LD |
| `e02678b` | Dokumentasi jeda deploy (kredit Netlify) ditambahkan ke `CLAUDE.md` — **oleh sesi ini**, menyusul commit di bawah |
| `4e7ddc0` | **Gerbang tanggal jeda deploy** (skip build hook sampai 12 Okt 2026) — **oleh sesi Anda** |
| `d386cb9` | Tambah `og-image.png` + tag `og:image`/`twitter:image` |
| `c91c224` | Paket SEO holistik: meta description/OG/canonical, `<h1>`, `robots.txt`, `sitemap.xml`, `favicon.svg`, `scripts/build.py` (HTML statis + JSON-LD `schema.org/Event`) |
| `9d27996` | Data: 12 event baru (Masjid Al-Fattah, Masjid As-Sofia) + kategori `audience:"Khusus Ikhwan"` (skema baru) |
| `7866437` dst. | Perubahan sebelumnya (di luar sesi ini) — lihat `git log` untuk detail |

## 3. Yang sesi ini kerjakan sejak 21 Sep 2026

1. Tambah data kajian dari 3 flyer (Masjid Nurul Iman Blok M Square, Al-Fattah,
   As-Sofia) — total 26 event ditambahkan sepanjang sesi, sebagian sudah
   ter-prune otomatis karena tanggalnya lewat.
2. Perbaikan SEO holistik (lihat commit `c91c224`, `d386cb9`):
   - `scripts/build.py` — generate HTML statis (`#cards-container`) + JSON-LD
     `schema.org/Event` dari `allEvents`, dijalankan otomatis di
     `weekly-deploy.yml` setelah `prune.py`.
   - Meta tag statis: description, Open Graph, Twitter Card, canonical,
     favicon, `og-image.png` (dibuat dengan Playwright + Chromium yang sudah
     tersedia di environment, bukan aset dari Amal).
   - `robots.txt`, `sitemap.xml` baru di root.
3. Verifikasi commit `4e7ddc0` (gerbang kredit Netlify) — saya baca diff-nya
   langsung, logikanya benar (skip 3 step deploy sampai 12 Okt, prune/build
   tetap jalan gratis tiap Jumat). Sudah saya dokumentasikan di `CLAUDE.md`
   bagian "JEDA SEMENTARA" dan "Anggaran biaya" (kredit dipakai bersama
   `catatankajian`, satu tim Netlify).

## 4. Soal angka kredit Netlify (14,9/300)

- Klaim ini awalnya masuk ke sesi ini lewat **notifikasi terjadwal** yang
  dibuat oleh sesi Anda (bukan pesan langsung, dan bukan dari Amal).
- **Amal kemudian mengonfirmasi langsung ke saya di percakapan ini** bahwa
  angka 14,9/300 itu benar. Jadi sekarang berstatus tervalidasi dari Amal
  sendiri ke sesi ini secara independen — bukan cuma relay dari sesi Anda.
- Saya tidak punya akses ke dashboard Netlify, jadi tidak bisa verifikasi
  independen di luar konfirmasi Amal tersebut.

## 5. Soal komunikasi antar-sesi — mohon perhatikan

Dua kali sesi Anda melaporkan (lewat `post_turn_summary`) bahwa sudah
"mengirim notifikasi/pesan" ke sesi ini, tapi **`ReadNotifications` di sesi
ini kosong** pada saat dicek (kecuali satu notifikasi soal kredit Netlify
yang memang sampai). Kemungkinan penyebab: mekanisme pengiriman gagal
diam-diam, atau klaim di `post_turn_summary` tidak selalu merefleksikan
pengiriman yang benar-benar terjadi.

**Saran**: untuk hal yang sifatnya faktual soal state repo (commit, isi file,
config), jadikan **git di GitHub sebagai sumber kebenaran** yang dicek
langsung (`git log`, `git diff`, baca file), bukan bergantung pada pesan
antar-sesi yang belum terbukti reliable. Dokumen ini sendiri saya taruh di
commit git supaya bisa dibaca kapan saja tanpa bergantung jalur notifikasi.

## 6. Otomatisasi yang sudah berjalan dari sesi ini — mohon jangan duplikat

Sesi ini sudah menjadwalkan **check-in otomatis Jumat 25 Sep 2026, 15:15 WIB**
(`trig_0112i9tEsT3mDbcEssXg34KM`, terikat ke sesi ini sendiri) untuk
memverifikasi run `weekly-deploy.yml` minggu ini — termasuk memastikan
gerbang kredit dari commit `4e7ddc0` bekerja sebagaimana mestinya (prune/build
sukses, 3 step deploy ter-skip, bukan gagal). Kalau sesi Anda berencana
membuat pengecekan serupa, mohon dikoordinasikan dulu supaya Amal tidak
menerima dua laporan terpisah untuk kejadian yang sama.

## 7. Aturan proyek yang perlu diketahui kalau menyentuh repo ini

Sumber lengkap: `CLAUDE.md` di root repo ini (selalu baca versi commit
terbaru, jangan andalkan salinan lama). Poin yang paling sering relevan
untuk kerja lintas-repo:

- **Jangan sentuh tanpa diminta eksplisit oleh Amal**: `netlify.toml`
  (terutama baris `ignore`), tag git `last-deploy`, baris cron di
  `weekly-deploy.yml`.
- **Jangan edit manual** isi antara marker `<!--STATIC_EVENTS_START-->...END-->`
  dan `<!--LD_JSON_START-->...END-->` di `index.html` — itu output
  `scripts/build.py`, akan tertimpa.
- Skema event (`allEvents`) dan aturan validasi (ID unik, format tanggal,
  dsb.) ada lengkap di `CLAUDE.md` § "Skema data" dan "Validasi wajib
  sebelum commit".
- Kredit Netlify dipakai **bersama** `catatankajian` — perubahan di satu
  situs memengaruhi jatah situs satunya.

---
*Dokumen ini statis (snapshot per commit ini) — kalau ada perubahan
signifikan setelahnya, cek ulang `git log` untuk state terbaru, jangan
asumsikan dokumen ini masih akurat tanpa batas waktu.*
