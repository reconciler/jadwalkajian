# Riwayat migrasi Netlify -> GitHub Pages — arsip

Dipindahkan verbatim dari `CLAUDE.md` pada 3 Okt 2026. Hanya konteks sejarah; tidak ada aturan aktif di sini.

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
