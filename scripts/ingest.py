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

Issue dikenali sebagai formulir dari ISI-nya (judul kolom "### Tanggal", "### Jenis waktu",
"### Masjid"), bukan dari judul Issue; awalan judul "Tambah kajian:" tetap dikenali. Issue dari
akun lain diabaikan. Issue formulir yang sudah diproses lalu diedit mendapat komentar (status
"abaikan"), bukan diam.

Pemakaian:
  python scripts/ingest.py --issues issues.json --out ingest.json --commit-msg msg.txt [--edited N] [--root .]

Format issues.json: [{"number": 12, "title": "Tambah kajian: ...", "body": "...", "login": "reconciler"}, ...]
"""

import argparse
import copy
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adapter_issue_form as adapter  # noqa: E402
import adapter_koreksi_form as adapter_k  # noqa: E402
import ingest_core as core  # noqa: E402
import koreksi_core as koreksi  # noqa: E402
import build  # noqa: E402
import prune  # noqa: E402

PEMILIK = os.environ.get("INGEST_PEMILIK", "reconciler")
FILE_TEMPLATE = ".github/ISSUE_TEMPLATE/tambah-kajian.yml"
FILE_TEMPLATE_KOREKSI = ".github/ISSUE_TEMPLATE/koreksi-hapus-kajian.yml"
FILE_CONFIG = ".github/ISSUE_TEMPLATE/config.yml"
ISI_CONFIG = "blank_issues_enabled: false\n"


def kode(s):
    """Teks dari pengguna dalam code span markdown (tidak memicu mention/tautan)."""
    return "`" + str(s).replace("`", "'").replace("|", "\\|") + "`"


def sidik_pratinjau(aksi, isi):
    """Sidik isi pratinjau (event yang akan dihapus, atau selisih koreksi). Konfirmasi hanya sah bila sidik saat
    ini sama dengan sidik pratinjau yang pernah ditampilkan untuk Issue ini."""
    return hashlib.sha256(json.dumps([aksi, isi], sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def periksa_kunci(konfirmasi, aksi, jumlah, sidik, lama, buat_pratinjau):
    """Terima konfirmasi hanya bila kata+jumlah cocok DAN ada pratinjau sebelumnya yang sidiknya sama dengan sekarang.
    Selain itu raise PerluKonfirmasi dengan pratinjau terbaru (dan sidik baru)."""
    cocok, cat = koreksi.periksa_konfirmasi(konfirmasi, aksi, jumlah)
    if cocok and lama is None:
        cocok, cat = False, ("Konfirmasi belum berlaku: Issue ini belum pernah menampilkan pratinjau. Periksa pratinjau di "
                             "bawah, lalu edit Issue dan isi konfirmasi.")
    elif cocok and lama != sidik:
        cocok, cat = False, ("Data berubah sejak pratinjau sebelumnya. Periksa pratinjau terbaru di bawah, lalu isi "
                             "konfirmasi lagi.")
    if not cocok:
        raise koreksi.PerluKonfirmasi(buat_pratinjau(cat), sidik)


class GalatInternal(Exception):
    """Kegagalan sistem (bukan isian pengguna) yang terdeteksi sebelum perubahan diterima."""


def simulasi_terbit(html, hari_ini):
    """Uji kering (dalam memori) langkah prune + build pada html hasil perubahan. -> None bila lolos, atau teks alasan.
    Mencegah satu Issue membuat prune.py/build.py gagal di langkah workflow berikutnya (yang menjatuhkan semua run)."""
    hari = hari_ini.isoformat()
    cocok = [m for m in (prune.EVENT_RX.match(l) for l in html.splitlines()) if m]
    if not cocok:
        return "prune tidak mengenali satu pun baris event"
    if not any(m.group(2) >= hari for m in cocok):
        return "tidak ada kajian mendatang (prune dan build menolak daftar tanpa kajian mendatang)"
    try:
        events = build.parse_events(html)
        upcoming = sorted((e for e in events if e["date"] >= hari), key=lambda e: (e["date"], e["timeOrder"]))
        if not upcoming:
            return "build tidak menemukan kajian mendatang"
        keluar = build.replace_between(html, "<!--STATIC_EVENTS_START-->", "<!--STATIC_EVENTS_END-->",
                                       build.build_static_html(upcoming))
        keluar = build.replace_between(keluar, "<!--LD_JSON_START-->", "<!--LD_JSON_END-->",
                                       "\n" + build.build_jsonld(upcoming) + "\n")
        json.loads(keluar.split("<!--LD_JSON_START-->")[1].split("<!--LD_JSON_END-->")[0]
                   .split(">", 1)[1].rsplit("</script>", 1)[0])
    except SystemExit:
        return "build menolak berkas (penanda blok tidak ditemukan)"
    except Exception as e:  # noqa: BLE001
        return f"build gagal ({type(e).__name__}: {e})"
    return None


def komentar_internal(e):
    return ("Issue ini **tidak diproses** karena **kesalahan internal sistem** (bukan isian Anda): "
            f"{kode(type(e).__name__ + ': ' + str(e)[:200])}. Tidak ada data yang berubah dan Issue tetap terbuka. "
            "Sistem tidak mencoba ulang otomatis; edit Issue ini (mis. tambahkan satu spasi) untuk mencoba lagi setelah "
            "pemelihara memperbaiki, atau laporkan ke pemelihara.")


def hash_isi(iss):
    """Sidik isi Issue (judul + isi). Dipakai agar Issue gagal diproses ulang bila isinya berubah,
    walau sinyal edit dari run pemicu hilang (run edit dibatalkan antrean)."""
    return hashlib.sha256((str(iss.get("title", "")) + "\n" + str(iss.get("body", ""))).encode("utf-8")).hexdigest()[:16]


def komentar_ok(issue, events, ids, hasil, info=None):
    info = info or {}
    b = ["Kajian dari Issue ini sudah masuk data dan **sudah terbit** di situs.", ""]
    if info.get("pola"):
        b.append(f"- Pola terbaca: {kode(info['pola'])}")
        if info.get("dikecualikan"):
            b.append("- Dikecualikan: " + ", ".join(kode(x) for x in info["dikecualikan"]))
        b.append(f"- Jumlah event ditambahkan: {len(events)}")
        b.append(f"- Kajian rutin: {'ya' if info.get('rutin_nilai') else 'tidak'} ({info.get('rutin', '-')})")
        b.append("")
    b += [
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
    peringatan = list(info.get("peringatan", [])) + list(hasil["peringatan"])
    if peringatan:
        b += ["", "Peringatan:"] + [f"- {p}" for p in peringatan]
    if events:
        b += ["", f"Salah isi? Pakai formulir **Koreksi atau hapus kajian** dengan Target `#{issue}` "
                  "(atau id event di tabel di atas)."]
    return "\n".join(b)


def komentar_tertunda(ids, aksi=None):
    daftar = ", ".join(str(i) for i in ids) or "-"
    isi = {"hapus": "Penghapusan", "koreksi": "Koreksi"}.get(aksi, "Kajian dari Issue ini")
    return (f"{isi} sudah masuk data (id {daftar}) tetapi **belum tayang**: "
            "deploy atau uji situs live gagal pada run ini. Issue tetap terbuka. "
            "Run berikutnya (cron harian atau push) akan mencoba menerbitkan ulang "
            "dan menutup Issue ini setelah uji lolos.")


def komentar_abaikan(ids):
    daftar = ", ".join(str(i) for i in ids) or "tidak ada event baru"
    return ("Issue ini **sudah diproses** (id event: " + daftar + ") dan perubahan pada isinya **tidak diterapkan**. "
            "Untuk mengoreksi atau menghapus event tersebut, minta lewat chat atau buat Issue baru "
            "(formulir Koreksi atau hapus kajian).")


def _baris_event(ev, i):
    return (f"| {i} | {ev['dayShort']} ({ev['date']}) | {kode(ev['timeLabel'])} | {kode(ev['title'])} | "
            f"{kode(ev['ustadz'])} | {kode(ev['masjid'])} | {kode(ev['area'])} |")


def _tabel_lengkap(events):
    """Semua kolom event (agar yang terhapus bisa dikembalikan lewat formulir Tambah)."""
    b = ["| id | tanggal | waktu | judul | pemateri | masjid | kota | alamat | audience | rutin | catatan |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for e in events:
        b.append(f"| {e['id']} | {e['dayShort']} ({e['date']}) | {kode(e['timeLabel'])} | {kode(e['title'])} | "
                 f"{kode(e['ustadz'])} | {kode(e['masjid'])} | {kode(e['area'])} | {kode(e.get('address', ''))} | "
                 f"{kode(e['audience'])} | {'ya' if e.get('isRutin') else 'tidak'} | {kode(e.get('note', ''))} |")
    return b


def _blok_data_lengkap(events):
    baris = "\n".join(core.baris_event(e, e["id"]).replace("```", "'" * 3) for e in events)
    return ["", "<details><summary>Data lengkap (baris asli di index.html)</summary>", "", "```", baris, "```", "",
            "</details>"]


def komentar_hapus(dihapus):
    b = [f"{len(dihapus)} kajian **sudah dihapus** dan tidak lagi tayang di situs:", ""]
    b += _tabel_lengkap(dihapus)
    b += ["", "Bila keliru, tambahkan kembali lewat formulir Tambah kajian (id baru akan dibuat); "
              "semua kolom yang dibutuhkan ada di tabel dan blok di bawah."]
    b += _blok_data_lengkap(dihapus)
    return "\n".join(b)


def pratinjau_hapus(dihapus, catatan=None):
    n = len(dihapus)
    b = ["**Belum ada yang dihapus.** Berikut kajian yang akan dihapus dari situs:", ""]
    b += _tabel_lengkap(dihapus)
    if catatan:
        b += ["", f"Catatan: {catatan}"]
    b += ["", f"Bila sudah benar, edit Issue ini: pada kolom Konfirmasi tulis `HAPUS {n}` lalu simpan. "
              "Bila salah, perbaiki kolom Target atau abaikan Issue ini."]
    return "\n".join(b)


def pratinjau_koreksi(hasil, catatan=None):
    n = len(hasil["ganti"])
    b = [f"**Belum ada yang diubah.** Berikut perubahan pada {n} kajian:", "",
         "| id | kolom | sebelum | sesudah |", "|---|---|---|---|"]
    b += [f"| {i} | {kolom} | {kode(lama)} | {kode(baru)} |" for i, kolom, lama, baru in hasil["perbedaan"]]
    if hasil["peringatan"]:
        b += ["", "Peringatan:"] + [f"- {p}" for p in hasil["peringatan"]]
    if catatan:
        b += ["", f"Catatan: {catatan}"]
    b += ["", f"Bila sudah benar, edit Issue ini: pada kolom Konfirmasi tulis `KOREKSI {n}` lalu simpan. "
              "Bila salah, ubah kolom koreksi atau abaikan Issue ini."]
    return "\n".join(b)


def komentar_koreksi(hasil):
    b = [f"{len(hasil['ganti'])} kajian **sudah dikoreksi** dan perubahannya sudah tayang di situs:", "",
         "| id | kolom | sebelum | sesudah |", "|---|---|---|---|"]
    b += [f"| {i} | {kolom} | {kode(lama)} | {kode(baru)} |" for i, kolom, lama, baru in hasil["perbedaan"]]
    baru = hasil["baru"]
    if baru["kota"] or baru["masjid"] or baru["pemateri"]:
        b += ["", "Ditambahkan ke daftar induk:"]
        if baru["kota"]:
            b.append("- kota: " + ", ".join(kode(x) for x in dict.fromkeys(baru["kota"])))
        if baru["masjid"]:
            b.append("- masjid: " + ", ".join(kode(core.label_masjid(x)) for x in baru["masjid"]))
        if baru["pemateri"]:
            b.append("- pemateri: " + ", ".join(kode(x["tampil"]) for x in baru["pemateri"]))
    if hasil["peringatan"]:
        b += ["", "Peringatan:"] + [f"- {p}" for p in hasil["peringatan"]]
    return "\n".join(b)


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
    # A1: samakan master dengan event yang sudah ada (jalur flyer manual tidak mengisi master). Hanya menambah.
    try:
        sinkron = core.sinkronkan_master(html, kat)
    except Exception as e:  # noqa: BLE001 - tidak boleh menjatuhkan run
        sinkron = {"kota": [], "masjid": [], "pemateri": [], "peringatan": [f"sinkronisasi master gagal ({type(e).__name__}: {e})"]}
    for w in sinkron["peringatan"]:
        print(f"PERINGATAN: {w}", file=sys.stderr)
    ringkas_sinkron = core.ringkas_sinkron(sinkron)

    for iss in issues:
        n = iss["number"]
        if iss.get("login") != PEMILIK:
            continue
        sidik = hash_isi(iss)
        snap_html, snap_kat = html, copy.deepcopy(kat)
        try:
            # Penanda formulir = judul kolom di isi Issue; awalan judul tetap dikenali (kolom hilang -> komentar gagal).
            judul_iss, isi_iss = str(iss.get("title", "")), iss.get("body", "")
            # Isi menentukan lebih dulu (judul bebas diedit); awalan judul hanya dipakai bila isi tidak dikenali.
            if adapter.adalah_formulir(isi_iss):
                bentuk = "tambah"
            elif adapter_k.adalah_koreksi(isi_iss):
                bentuk = "koreksi"
            elif judul_iss.startswith(adapter.JUDUL_ISSUE.strip()):
                bentuk = "tambah"
            elif judul_iss.startswith(adapter_k.JUDUL_KOREKSI.strip()):
                bentuk = "koreksi"
            else:
                continue
            if n in diproses:
                if n == a.edited:  # diedit setelah diproses: beri tahu, jangan diam
                    ids = next(d["id"] for d in kat["diproses"] if d["issue"] == n)
                    hasil_semua.append({"issue": n, "status": "abaikan", "id": ids, "komentar": komentar_abaikan(ids)})
                continue
            gagal_lama = [g for g in kat["gagal"] if g["issue"] == n]
            if gagal_lama and n != a.edited and gagal_lama[0].get("isi") in (None, sidik):
                continue  # sudah dilaporkan gagal dan isinya belum berubah; tunggu diedit
            kat["gagal"] = [g for g in kat["gagal"] if g["issue"] != n]

            events_ada = core.events_dari_html(html)
            if bentuk == "koreksi":
                try:
                    pk = adapter_k.ke_paket(isi_iss, kat, events_ada, hari_ini)
                    if pk["aksi"] == "hapus":
                        dihapus = [e for e in events_ada if e["id"] in set(pk["ids"])]
                        # Prune menolak daftar tanpa event mendatang (pengaman "hapus SEMUA"): tolak sebelum menulis apa pun.
                        sisa = [e for e in events_ada
                                if e["id"] not in set(pk["ids"]) and e["date"] >= hari_ini.isoformat()]
                        if not sisa:
                            raise core.InputError(
                                "Penghapusan ini menyisakan 0 kajian mendatang. Situs tidak boleh kosong "
                                "(prune dan build menolak daftar kosong). Kurangi Target, atau tambahkan kajian lain dulu.")
                        periksa_kunci(pk["konfirmasi"], "hapus", len(dihapus), sidik_pratinjau("hapus", dihapus),
                                      gagal_lama[0].get("pratinjau") if gagal_lama else None,
                                      lambda cat: pratinjau_hapus(dihapus, cat))
                        html_baru = koreksi.hapus_baris(html, pk["ids"])
                        komentar = komentar_hapus(dihapus)
                        ringkas = f"hapus {len(dihapus)} kajian (id {', '.join(map(str, pk['ids']))})"
                    else:
                        hk = koreksi.proses_koreksi(pk, kat, events_ada, hari_ini)
                        periksa_kunci(pk["konfirmasi"], "koreksi", len(hk["ganti"]),
                                      sidik_pratinjau("koreksi", [pk["ids"], hk["perbedaan"]]),
                                      gagal_lama[0].get("pratinjau") if gagal_lama else None,
                                      lambda cat: pratinjau_koreksi(hk, cat))
                        html_baru = html
                        for i_ev, ev in hk["ganti"].items():
                            html_baru = koreksi.ganti_baris(html_baru, i_ev, ev)
                        for kunci_kat in ("kota", "masjid", "pemateri"):
                            kat[kunci_kat] = hk["kat_kerja"][kunci_kat]
                        komentar = komentar_koreksi(hk)
                        ringkas = f"koreksi {len(hk['ganti'])} kajian (id {', '.join(map(str, pk['ids']))})"
                except koreksi.PerluKonfirmasi as e:
                    kat["gagal"].append({"issue": n, "alasan": ["menunggu konfirmasi"], "isi": sidik, "pratinjau": e.digest})
                    hasil_semua.append({"issue": n, "status": "gagal", "id": [], "komentar": e.pratinjau})
                    continue
                except core.InputError as e:
                    kat["gagal"].append({"issue": n, "alasan": e.pesan, "isi": sidik})
                    hasil_semua.append({"issue": n, "status": "gagal", "id": [], "komentar": komentar_gagal(e.pesan)})
                    continue
                galat_sim = simulasi_terbit(html_baru, hari_ini)
                if galat_sim:
                    raise GalatInternal("uji prune/build gagal: " + galat_sim)
                html = html_baru
                kat["diproses"].append({"issue": n, "id": pk["ids"], "aksi": pk["aksi"]})
                diproses.add(n)
                hasil_semua.append({"issue": n, "status": "ok", "id": pk["ids"], "komentar": komentar,
                                    "komentar_tertunda": komentar_tertunda(pk["ids"], pk["aksi"])})
                pesan_commit.append(f"Issue #{n}: {ringkas}")
                continue
            try:
                paket = adapter.ke_paket(iss.get("body", ""), kat, hari_ini)
                hasil = core.bangun_event(paket, kat, hari_ini, events_ada)
            except core.InputError as e:
                kat["gagal"].append({"issue": n, "alasan": e.pesan, "isi": sidik})
                hasil_semua.append({"issue": n, "status": "gagal", "id": [],
                                    "komentar": komentar_gagal(e.pesan)})
                continue

            id0 = core.id_berikutnya(html, kat)
            ids = list(range(id0, id0 + len(hasil["events"])))
            if hasil["events"]:
                html_cand = core.sisipkan(html, [core.baris_event(ev, i) for ev, i in zip(hasil["events"], ids)])
                galat_sim = simulasi_terbit(html_cand, hari_ini)
                if galat_sim:
                    raise GalatInternal("uji prune/build gagal: " + galat_sim)
                html = html_cand
                core.terapkan_kategori(kat, hasil)
            if ids:
                kat["id_tertinggi"] = max(int(kat.get("id_tertinggi") or 0), ids[-1])
            kat["diproses"].append({"issue": n, "id": ids})
            diproses.add(n)
            hasil_semua.append({"issue": n, "status": "ok", "id": ids,
                                "komentar": komentar_ok(n, hasil["events"], ids, hasil, paket.get("info")),
                                "komentar_tertunda": komentar_tertunda(ids)})
            if ids:
                pesan_commit.append(f"Issue #{n}: tambah {len(ids)} kajian (id {ids[0]}-{ids[-1]})")
            else:
                pesan_commit.append(f"Issue #{n}: tidak ada event baru")
        except Exception as e:  # noqa: BLE001 - satu Issue bermasalah tidak boleh menjatuhkan run atau Issue lain
            html = snap_html
            kat.clear()
            kat.update(snap_kat)
            diproses = {d["issue"] for d in kat["diproses"]}
            kat["gagal"] = [g for g in kat["gagal"] if g["issue"] != n]
            kat["gagal"].append({"issue": n, "alasan": ["kesalahan internal"], "isi": sidik})
            hasil_semua.append({"issue": n, "status": "gagal", "id": [], "komentar": komentar_internal(e)})
            print(f"PERINGATAN: Issue #{n} gagal karena kesalahan internal: {type(e).__name__}: {e}", file=sys.stderr)

    if html != awal_html:
        f_html.write_text(html, encoding="utf-8")
    if json.dumps(kat, sort_keys=True, ensure_ascii=False) != awal_kat or html != awal_html:
        # Simpan id tertinggi yang pernah ada (termasuk event yang baru dihapus) agar id tidak pernah dipakai ulang.
        kat["id_tertinggi"] = max(core.id_tertinggi(awal_html, kat), core.id_tertinggi(html, kat))
        core.simpan_kategori(f_kat, kat)

    # templat formulir selalu dibuat ulang dari daftar induk (ditulis hanya bila berubah)
    # Tidak fatal: kegagalan membuat templat tidak boleh menghalangi data kajian terbit.
    try:
        folder = root / ".github" / "ISSUE_TEMPLATE"
        folder.mkdir(parents=True, exist_ok=True)
        baru = adapter.render_template(core.muat_kategori(f_kat))
        f_tpl = root / FILE_TEMPLATE
        if not f_tpl.exists() or f_tpl.read_text(encoding="utf-8") != baru:
            f_tpl.write_text(baru, encoding="utf-8")
        f_tpl_k = root / FILE_TEMPLATE_KOREKSI
        baru_k = adapter_k.render_template(core.muat_kategori(f_kat))
        if not f_tpl_k.exists() or f_tpl_k.read_text(encoding="utf-8") != baru_k:
            f_tpl_k.write_text(baru_k, encoding="utf-8")
        f_cfg = root / FILE_CONFIG
        if not f_cfg.exists() or f_cfg.read_text(encoding="utf-8") != ISI_CONFIG:
            f_cfg.write_text(ISI_CONFIG, encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        print(f"PERINGATAN: templat formulir tidak diperbarui: {type(e).__name__}: {e}", file=sys.stderr)

    Path(a.out).write_text(json.dumps({"hasil": hasil_semua}, ensure_ascii=False), encoding="utf-8")
    if ringkas_sinkron:
        pesan_commit.append(f"Sinkron master dari index.html: {ringkas_sinkron}")
    judul_komit = "Ingest dari Issue GitHub" if hasil_semua else "Sinkron master dari index.html"
    Path(a.commit_msg).write_text(
        (judul_komit + "\n\n" + "\n".join(pesan_commit) + "\n") if pesan_commit else "",
        encoding="utf-8")
    print(f"Issue diperiksa: {len(issues)}; hasil: "
          + (", ".join(f"#{h['issue']}={h['status']}" for h in hasil_semua) or "tidak ada yang diproses"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
