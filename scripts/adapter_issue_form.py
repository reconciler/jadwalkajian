#!/usr/bin/env python3
"""
Adapter formulir Issue GitHub -> paket baku untuk ingest_core.

Dua tugas, keduanya khusus formulir Issue:
  1. render_template(kat): membuat .github/ISSUE_TEMPLATE/tambah-kajian.yml dari
     daftar induk (dropdown selalu mutakhir).
  2. ke_paket(body, kat): mengubah isi Issue (teks markdown yang dibuat GitHub dari
     formulir) menjadi paket baku.

PENTING: nilai LABEL di bawah adalah kunci parsing. Issue menyajikan jawaban di
bawah heading "### <label>". Jangan ubah label tanpa mengubah parser (dan
sebaliknya). Jalur input lain (mis. Google Form) cukup menulis adapter baru yang
menghasilkan paket baku yang sama.
"""

import json
import re

import tanggal_bebas
from ingest_core import (AUDIENCE, BELUM_DITENTUKAN, JENIS_WAKTU, ONLINE,
                         InputError, bersihkan, sekarang_wib)

LABEL = {
    "tanggal": "Tanggal",
    "jenis_waktu": "Jenis waktu",
    "jam": "Jam",
    "judul": "Judul",
    "pemateri": "Pemateri",
    "pemateri_baru": "Pemateri baru",
    "perempuan": "Pemateri perempuan",
    "masjid": "Masjid",
    "masjid_baru": "Nama masjid baru",
    "alamat_baru": "Alamat masjid baru",
    "kota_baru": "Kota masjid baru",
    "kota_lain": "Kota lain",
    "audience": "Audience",
    "rutin": "Kajian rutin",
    "catatan": "Catatan",
}
WAJIB = ["tanggal", "jenis_waktu", "judul", "pemateri", "masjid", "audience"]

JUDUL_ISSUE = "Tambah kajian: "
LAINNYA = "Lainnya (tulis di bawah)"
KOTA_LAIN = "Kota lain (tulis di bawah)"
OPSI_PEREMPUAN = "Pemateri perempuan (otomatis Khusus Akhwat)"
OPSI_RUTIN = "Kajian rutin atau berkala"
MAKS_OPSI_DROPDOWN = 150  # lebih dari ini, kolom Pemateri/Masjid dibuat isian teks
RESPON_KOSONG = "_No response_"


def tampil(nama):
    """Teks opsi dropdown. Koma ASCII diganti koma lebar penuh agar aman bagi
    validasi dropdown GitHub (aturan koma belum terverifikasi)."""
    return nama.replace(",", "，")


def peta_tampil(daftar):
    return {tampil(n): n for n in daftar}


# ---------- templat ----------

def _q(s):
    return json.dumps(s, ensure_ascii=False)


def _unsur(tipe, id_, label, deskripsi=None, placeholder=None, wajib=False, opsi=None, kotak=None):
    b = [f"  - type: {tipe}", f"    id: {id_}", "    attributes:", f"      label: {_q(label)}"]
    if deskripsi:
        b.append(f"      description: {_q(deskripsi)}")
    if placeholder:
        b.append(f"      placeholder: {_q(placeholder)}")
    if opsi is not None:
        b.append("      options:")
        b += [f"        - {_q(o)}" for o in opsi]
    if kotak is not None:
        b.append("      options:")
        b += [f"        - label: {_q(kotak)}"]
    if tipe != "checkboxes":
        b.append("    validations:")
        b.append(f"      required: {'true' if wajib else 'false'}")
    return "\n".join(b)


def render_template(kat):
    pemateri = sorted({p for p in kat["pemateri"] if p != BELUM_DITENTUKAN}, key=str.casefold)
    masjid = sorted(kat["masjid"].keys(), key=str.casefold)
    kota = sorted(kat["kota"], key=str.casefold)

    pem_opsi = [tampil(p) for p in pemateri] + [BELUM_DITENTUKAN, LAINNYA]
    mas_opsi = [tampil(m) for m in masjid] + [ONLINE, LAINNYA]
    kota_opsi = [tampil(k) for k in kota] + [KOTA_LAIN]

    if len(pem_opsi) > MAKS_OPSI_DROPDOWN:
        pem = _unsur("input", "pemateri", LABEL["pemateri"],
                     "Nama pemateri persis seperti di flyer, atau Belum ditentukan.", wajib=True)
    else:
        pem = _unsur("dropdown", "pemateri", LABEL["pemateri"], wajib=True, opsi=pem_opsi)
    if len(mas_opsi) > MAKS_OPSI_DROPDOWN:
        mas = _unsur("input", "masjid", LABEL["masjid"],
                     "Nama masjid persis seperti yang sudah ada, atau Online.", wajib=True)
    else:
        mas = _unsur("dropdown", "masjid", LABEL["masjid"], wajib=True, opsi=mas_opsi)

    unsur = [
        _unsur("input", "tanggal", LABEL["tanggal"],
               "Satu isian. Contoh: 10 Okt 2026 | 10, 17, 24 Okt 2026 | 3-31 Okt 2026 Sabtu | 3 Okt - 4 Okt 2026 | 10/10/2026. "
               "Banyak tanggal = banyak event dengan isian yang sama. Tahun boleh dihilangkan. Cek hasilnya di komentar balasan.",
               "10 Okt 2026", wajib=True),
        _unsur("dropdown", "jenis_waktu", LABEL["jenis_waktu"], wajib=True, opsi=JENIS_WAKTU),
        _unsur("input", "jam", LABEL["jam"],
               "Hanya bila Jenis waktu = Jam eksak. Contoh 09.30 atau 09.30-11.00.", "09.30-11.00"),
        _unsur("input", "judul", LABEL["judul"], wajib=True),
        pem,
        _unsur("input", "pemateri_baru", LABEL["pemateri_baru"],
               "Wajib bila Pemateri = Lainnya. Pemateri baru otomatis masuk daftar."),
        _unsur("checkboxes", "perempuan", LABEL["perempuan"], kotak=OPSI_PEREMPUAN),
        mas,
        _unsur("input", "masjid_baru", LABEL["masjid_baru"],
               "Wajib bila Masjid = Lainnya. Bila Masjid = Online, isi nama penyelenggara di sini."),
        _unsur("input", "alamat_baru", LABEL["alamat_baru"], "Wajib bila Masjid = Lainnya."),
        _unsur("dropdown", "kota_baru", LABEL["kota_baru"], "Wajib bila Masjid = Lainnya.", opsi=kota_opsi),
        _unsur("input", "kota_lain", LABEL["kota_lain"], "Wajib bila Kota masjid baru = Kota lain."),
        _unsur("dropdown", "audience", LABEL["audience"], wajib=True, opsi=AUDIENCE),
        _unsur("checkboxes", "rutin", LABEL["rutin"], kotak=OPSI_RUTIN),
        _unsur("textarea", "catatan", LABEL["catatan"], "Opsional."),
    ]
    kepala = (
        "# DIBUAT OTOMATIS oleh scripts/ingest.py dari data/kategori.json. Jangan edit manual:\n"
        "# perubahan akan tertimpa pada run berikutnya. Label kolom = kunci parser\n"
        "# (scripts/adapter_issue_form.py); jangan diubah tanpa mengubah parser.\n"
        f"name: Tambah kajian\n"
        f"description: Tambah satu atau beberapa kajian ke Jadwal Kajian (hanya pemilik repo).\n"
        f"title: {_q(JUDUL_ISSUE)}\n"
        "body:\n"
    )
    return kepala + "\n".join(unsur) + "\n"


# ---------- parser ----------

def pecah_body(body):
    """Isi Issue -> dict {label: teks}. Teks '_No response_' menjadi ''."""
    teks = (body or "").replace("\r\n", "\n").replace("\r", "\n")
    bagian = re.split(r"^### (.+?)[ \t]*$", teks, flags=re.M)
    hasil = {}
    for i in range(1, len(bagian) - 1, 2):
        nilai = bagian[i + 1].strip()
        hasil[bagian[i].strip()] = "" if nilai == RESPON_KOSONG else nilai
    return hasil


def _centang(nilai):
    return bool(re.search(r"^\s*-\s*\[[xX]\]", nilai or "", re.M))


def ke_paket(body, kat, hari_ini=None):
    """Isi Issue -> paket baku. Menaikkan InputError bila struktur/kolom bersyarat salah."""
    f = pecah_body(body)
    galat = []
    for k in WAJIB:
        if LABEL[k] not in f or not f[LABEL[k]]:
            galat.append(f"Kolom '{LABEL[k]}' kosong atau tidak ditemukan (isi Issue harus dari formulir).")
    if galat:
        raise InputError(galat)

    def v(k):
        return f.get(LABEL[k], "")

    try:
        tanggal = tanggal_bebas.parse(v("tanggal"), hari_ini or sekarang_wib())
    except InputError as e:
        galat.extend(e.pesan)
        tanggal = []

    # pemateri
    pem = v("pemateri")
    if pem == LAINNYA:
        pemateri = v("pemateri_baru")
        if not pemateri:
            galat.append("Pemateri baru: wajib diisi bila Pemateri = Lainnya.")
    else:
        pemateri = peta_tampil(kat["pemateri"]).get(pem, pem)

    # masjid
    mas = v("masjid")
    masjid_baru = None
    if mas == ONLINE:
        penyelenggara = v("masjid_baru")
        if not penyelenggara:
            galat.append("Nama masjid baru: untuk Masjid = Online, isi nama penyelenggara.")
            masjid = ""
        else:
            try:
                pen = bersihkan(penyelenggara, "Nama masjid baru", 100, True)
            except InputError as e:
                galat.extend(e.pesan)
                pen = ""
            masjid = f"{pen} (Online)" if pen else ""
            masjid_baru = {"alamat": f"Online ({pen})", "kota": ONLINE}
    elif mas == LAINNYA:
        masjid = v("masjid_baru")
        kota = v("kota_baru")
        if kota == KOTA_LAIN:
            kota = v("kota_lain")
            if not kota:
                galat.append("Kota lain: wajib diisi bila Kota masjid baru = Kota lain.")
        else:
            kota = peta_tampil(kat["kota"]).get(kota, kota)
        if not masjid:
            galat.append("Nama masjid baru: wajib diisi bila Masjid = Lainnya.")
        if not v("alamat_baru"):
            galat.append("Alamat masjid baru: wajib diisi bila Masjid = Lainnya.")
        if not kota and not any("Kota" in g for g in galat):
            galat.append("Kota masjid baru: wajib dipilih bila Masjid = Lainnya.")
        masjid_baru = {"alamat": v("alamat_baru"), "kota": kota}
    else:
        masjid = peta_tampil(kat["masjid"].keys()).get(mas, mas)

    if galat:
        raise InputError(galat)

    return {
        "tanggal": tanggal,
        "jenis_waktu": v("jenis_waktu"),
        "jam": v("jam"),
        "judul": v("judul"),
        "pemateri": pemateri,
        "pemateri_perempuan": _centang(v("perempuan")),
        "masjid": masjid,
        "masjid_baru": masjid_baru,
        "audience": v("audience"),
        "rutin": _centang(v("rutin")),
        "catatan": v("catatan"),
    }
