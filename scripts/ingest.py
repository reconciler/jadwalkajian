#!/usr/bin/env python3
"""
Ingest event dari Issue GitHub (formulir "Tambah kajian").

Dijalankan oleh .github/workflows/deploy.yml pada SETIAP run (push, Issue
dibuka/diedit, cron harian, manual). Membaca daftar Issue terbuka dari berkas
JSON (bukan dari interpolasi di run:), memproses yang belum diproses, lalu:
  - menambah baris event ke index.html,
  - memperbarui data/kategori.json (kota/masjid/pemateri baru, diproses/gagal),
  - menulis ulang .github/ISSUE_TEMPLATE/tambah-kajian.yml,
  - menulis ringkasan hasil (JSON) dan pesan commit untuk langkah workflow.

Ia tidak melakukan git, tidak memanggil API GitHub, dan tidak menerbitkan apa pun.

Pemakaian:
  python scripts/ingest.py --issues issues.json --out ingest.json --commit-msg msg.txt [--edited N] [--root .]

Format issues.json: [{"number": 12, "title": "Tambah kajian: ...", "body": "...", "login": "reconciler"}, ...]
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adapter_issue_form as adapter  # noqa: E402
import ingest_core as core  # noqa: E402

PEMILIK = os.environ.get("INGEST_PEMILIK", "reconciler")
FILE_TEMPLATE = ".github/ISSUE_TEMPLATE/tambah-kajian.yml"
FILE_CONFIG = ".github/ISSUE_TEMPLATE/config.yml"
ISI_CONFIG = "blank_issues_enabled: false\n"


def kode(s):
    """Teks dari pengguna dalam code span markdown (tidak memicu mention/tautan)."""
    return "`" + str(s).replace("`", "'") + "`"


def komentar_ok(issue, events, ids, hasil):
    b = ["Kajian dari Issue ini sudah masuk data dan **sudah terbit** di situs.", "",
         "| id | tanggal | waktu | judul | pemateri | masjid | kota |", "|---|---|---|---|---|---|---|"]
    for ev, i in zip(events, ids):
        b.append(f"| {i} | {ev['dayShort']} ({ev['date']}) | {kode(ev['timeLabel'])} | {kode(ev['title'])} | "
                 f"{kode(ev['ustadz'])} | {kode(ev['masjid'])} | {kode(ev['area'])} |")
    if not events:
        b.append("| - | - | - | tidak ada event baru | - | - | - |")
    if hasil["dilewati"]:
        b += ["", "Dilewati:"] + [f"- {t}: {a}" for t, a in hasil["dilewati"]]
    baru = hasil["baru"]
    if events and (baru["kota"] or baru["masjid"] or baru["pemateri"]):
        b += ["", "Ditambahkan ke daftar induk:"]
        if baru["kota"]:
            b.append("- kota: " + ", ".join(kode(x) for x in baru["kota"]))
        if baru["masjid"]:
            b.append("- masjid: " + ", ".join(kode(core.label_masjid(x)) for x in baru["masjid"]))
        if baru["pemateri"]:
            b.append("- pemateri: " + ", ".join(kode(x["tampil"]) + " (nama bersih " + kode(x["nama"]) + ")" for x in baru["pemateri"]))
    if hasil["peringatan"]:
        b += ["", "Peringatan:"] + [f"- {p}" for p in hasil["peringatan"]]
    return "\n".join(b)


def komentar_tertunda(ids):
    daftar = ", ".join(str(i) for i in ids) or "-"
    return (f"Kajian dari Issue ini sudah masuk data (id {daftar}) tetapi **belum terbit**: "
            "deploy atau uji situs live gagal pada run ini. Issue tetap terbuka. "
            "Run berikutnya (cron harian atau push) akan mencoba menerbitkan ulang "
            "dan menutup Issue ini setelah uji lolos.")


def komentar_gagal(pesan):
    return ("Issue ini **tidak diproses**. Perbaiki isiannya dengan mengedit Issue ini "
            "(Issue akan diproses ulang otomatis saat diedit) atau tutup lalu buat Issue baru.\n\n"
            + "\n".join(f"- {p}" for p in pesan))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--issues", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--commit-msg", required=True)
    ap.add_argument("--edited", type=int, default=None)
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--today", default=None, help="YYYY-MM-DD (uji)")
    a = ap.parse_args(argv)

    root = Path(a.root)
    f_html, f_kat = root / "index.html", root / "data" / "kategori.json"
    html = f_html.read_text(encoding="utf-8")
    kat = core.muat_kategori(f_kat)
    awal_kat = json.dumps(kat, sort_keys=True, ensure_ascii=False)
    awal_html = html
    hari_ini = core.date.fromisoformat(a.today) if a.today else core.sekarang_wib()

    issues = json.loads(Path(a.issues).read_text(encoding="utf-8"))
    issues.sort(key=lambda i: i["number"])
    diproses = {d["issue"] for d in kat["diproses"]}
    hasil_semua, pesan_commit = [], []

    for iss in issues:
        n = iss["number"]
        if iss.get("login") != PEMILIK or not str(iss.get("title", "")).startswith(adapter.JUDUL_ISSUE.strip()):
            continue
        if n in diproses:
            continue
        gagal_lama = [g for g in kat["gagal"] if g["issue"] == n]
        if gagal_lama and n != a.edited:
            continue  # sudah dilaporkan gagal; tunggu diedit
        kat["gagal"] = [g for g in kat["gagal"] if g["issue"] != n]

        events_ada = core.events_dari_html(html)
        try:
            paket = adapter.ke_paket(iss.get("body", ""), kat, hari_ini)
            hasil = core.bangun_event(paket, kat, hari_ini, events_ada)
        except core.InputError as e:
            kat["gagal"].append({"issue": n, "alasan": e.pesan})
            hasil_semua.append({"issue": n, "status": "gagal", "id": [],
                                "komentar": komentar_gagal(e.pesan)})
            continue

        id0 = core.id_berikutnya(html)
        ids = list(range(id0, id0 + len(hasil["events"])))
        if hasil["events"]:
            html = core.sisipkan(html, [core.baris_event(ev, i) for ev, i in zip(hasil["events"], ids)])
            core.terapkan_kategori(kat, hasil)
        kat["diproses"].append({"issue": n, "id": ids})
        diproses.add(n)
        hasil_semua.append({"issue": n, "status": "ok", "id": ids,
                            "komentar": komentar_ok(n, hasil["events"], ids, hasil),
                            "komentar_tertunda": komentar_tertunda(ids)})
        if ids:
            pesan_commit.append(f"Issue #{n}: tambah {len(ids)} kajian (id {ids[0]}-{ids[-1]})")
        else:
            pesan_commit.append(f"Issue #{n}: tidak ada event baru")

    if html != awal_html:
        f_html.write_text(html, encoding="utf-8")
    if json.dumps(kat, sort_keys=True, ensure_ascii=False) != awal_kat:
        core.simpan_kategori(f_kat, kat)

    # templat formulir selalu dibuat ulang dari daftar induk (ditulis hanya bila berubah)
    folder = root / ".github" / "ISSUE_TEMPLATE"
    folder.mkdir(parents=True, exist_ok=True)
    baru = adapter.render_template(core.muat_kategori(f_kat))
    f_tpl = root / FILE_TEMPLATE
    if not f_tpl.exists() or f_tpl.read_text(encoding="utf-8") != baru:
        f_tpl.write_text(baru, encoding="utf-8")
    f_cfg = root / FILE_CONFIG
    if not f_cfg.exists() or f_cfg.read_text(encoding="utf-8") != ISI_CONFIG:
        f_cfg.write_text(ISI_CONFIG, encoding="utf-8")

    Path(a.out).write_text(json.dumps({"hasil": hasil_semua}, ensure_ascii=False), encoding="utf-8")
    Path(a.commit_msg).write_text(
        ("Ingest dari Issue GitHub\n\n" + "\n".join(pesan_commit) + "\n") if pesan_commit else "",
        encoding="utf-8")
    print(f"Issue diperiksa: {len(issues)}; hasil: "
          + (", ".join(f"#{h['issue']}={h['status']}" for h in hasil_semua) or "tidak ada yang diproses"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
