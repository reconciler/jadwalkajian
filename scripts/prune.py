#!/usr/bin/env python3
"""
Prune event yang sudah lewat dari index.html Jadwal Kajian,
lalu perbarui stempel "Diperbarui:" di footer.

Dijalankan otomatis oleh GitHub Actions setiap hari 00:05 WIB.
Logikanya deterministik — tidak ada penilaian/AI di sini.

Keluar dengan kode 0 dan tidak menulis apa pun bila tidak ada perubahan.
"""

import os
import re
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

FILE = Path(__file__).resolve().parent.parent / "index.html"
TZ = ZoneInfo("Asia/Jakarta")

BULAN = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Mei", 6: "Jun",
    7: "Jul", 8: "Agu", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Des",
}

EVENT_RX = re.compile(r'^\s*\{id:(\d+),date:"(\d{4}-\d{2}-\d{2})"')
STAMP_RX = re.compile(r'(Diperbarui:\s*)([^<]*)')
# Penanda struktur array event (sama dengan build.py). Hasil prune boleh nol event HANYA bila keduanya ada.
ARRAY_AWAL = re.compile(r"^const allEvents=\[\s*$")
ARRAY_AKHIR = re.compile(r"^\];\s*$")


def _batas_array(lines):
    awal = next((i for i, l in enumerate(lines) if ARRAY_AWAL.match(l)), None)
    if awal is None:
        return None
    akhir = next((i for i in range(awal + 1, len(lines)) if ARRAY_AKHIR.match(lines[i])), None)
    return None if akhir is None else (awal, akhir)


def struktur_array_ada(lines):
    return _batas_array(lines) is not None


def array_kosong(lines):
    """Struktur utuh dan badannya hanya baris kosong: daftar benar-benar kosong (bukan parser yang gagal mengenali)."""
    b = _batas_array(lines)
    return b is not None and all(not l.strip() for l in lines[b[0] + 1:b[1]])


def main() -> int:
    if not FILE.exists():
        print(f"ERROR: {FILE} tidak ditemukan", file=sys.stderr)
        return 1

    # JADWAL_HARI_INI (YYYY-MM-DD) hanya untuk uji otomatis agar hasil tidak bergantung jam asli; produksi tidak memakainya.
    today = date.fromisoformat(os.environ["JADWAL_HARI_INI"]) if os.environ.get("JADWAL_HARI_INI") else datetime.now(TZ).date()
    today_iso = today.isoformat()
    stamp = f"{today.day} {BULAN[today.month]} {today.year}"

    original = FILE.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)

    kept, removed, total = [], [], 0
    for line in lines:
        m = EVENT_RX.match(line)
        if m:
            total += 1
            if m.group(2) < today_iso:
                removed.append((m.group(1), m.group(2)))
                continue
        kept.append(line)

    # Pengaman: jangan pernah menulis file yang kehilangan seluruh event.
    # Kalau ini terjadi, struktur file berubah dan skrip tidak lagi valid.
    if total == 0 and not array_kosong(lines):
        print("ERROR: tidak ada event terdeteksi padahal allEvents tidak kosong (atau strukturnya hilang) — "
              "struktur file berubah? Tidak ada yang ditulis.", file=sys.stderr)
        return 1
    if total == 0:
        print("Catatan: daftar event sudah kosong (penanda array utuh); tidak ada yang di-prune.")
    if total > 0 and total - len(removed) == 0:
        # Semua event memang kedaluwarsa: sah bila struktur array utuh dan parser menemukan >= 1 baris sebelum prune.
        # Bila penanda array hilang, ini kemungkinan regex/struktur rusak: pengaman lama tetap berlaku.
        if not struktur_array_ada(lines):
            print("ERROR: pruning akan menghapus SEMUA event dan penanda array allEvents tidak utuh. Dibatalkan.",
                  file=sys.stderr)
            return 1
        print("Catatan: semua event kedaluwarsa; daftar dikosongkan (penanda array utuh).")

    updated = "".join(kept)
    updated, n_stamp = STAMP_RX.subn(lambda m: m.group(1) + stamp, updated)

    if updated == original:
        print(f"Tidak ada perubahan. Event aktif: {total}. Tanggal: {today_iso}")
        return 0

    FILE.write_text(updated, encoding="utf-8")

    print(f"Tanggal (WIB)   : {today_iso}")
    print(f"Event sebelum   : {total}")
    print(f"Di-prune        : {len(removed)}")
    print(f"Event tersisa   : {total - len(removed)}")
    print(f"Stempel footer  : {stamp} ({n_stamp} lokasi)")
    for eid, d in removed:
        print(f"  - id={eid} date={d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
