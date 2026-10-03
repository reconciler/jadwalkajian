#!/usr/bin/env python3
"""Samakan data/kategori.json dengan event di index.html (tanpa jaringan).

Dipakai di jalur flyer manual: setelah menambah event ke index.html, jalankan skrip ini supaya kota/masjid/pemateri
barunya masuk master (dan dropdown formulir Issue) tanpa mengedit kategori.json manual. Idempoten; hanya MENAMBAH
entri (tidak pernah menghapus); event yang tidak bisa diurai menghasilkan peringatan, bukan galat.

  python3 scripts/sinkron_master.py          # tulis kategori.json bila ada selisih
  python3 scripts/sinkron_master.py --cek    # hanya tampilkan selisih, tidak menulis
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ingest_core as core  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--cek", action="store_true", help="hanya tampilkan selisih; tidak menulis")
    a = ap.parse_args(argv)
    root = Path(a.root)
    html = (root / "index.html").read_text(encoding="utf-8")
    f_kat = root / "data" / "kategori.json"
    kat = core.muat_kategori(f_kat)
    baru = core.sinkronkan_master(html, kat)
    for w in baru["peringatan"]:
        print(f"PERINGATAN: {w}", file=sys.stderr)
    ringkas = core.ringkas_sinkron(baru)
    if not ringkas:
        print("Master sudah sama dengan event di index.html. Tidak ada perubahan.")
        return 0
    for k in baru["kota"]:
        print(f"  + kota: {k}")
    for m in baru["masjid"]:
        print(f"  + masjid: {m['tampil']} ({m['kota']})")
    for p in baru["pemateri"]:
        print(f"  + pemateri: {p['tampil']} (nama bersih: {p['nama']})")
    if a.cek:
        print(f"Selisih: {ringkas} (tidak ditulis: --cek).")
        return 0
    core.simpan_kategori(f_kat, kat)
    print(f"data/kategori.json diperbarui: {ringkas}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
