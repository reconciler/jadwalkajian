#!/usr/bin/env python3
"""
Adapter formulir Issue "Koreksi atau hapus kajian" (tahap 2) -> paket koreksi baku untuk koreksi_core.

Seperti adapter_issue_form: label kolom = kunci parser (Issue menyajikan jawaban di bawah
"### label"). Label sengaja berbeda dari formulir Tambah ("... (koreksi)") supaya Issue koreksi
tidak pernah dikira Issue Tambah, dan sebaliknya.
"""

import json

import tanggal_bebas
from adapter_issue_form import (KOTA_LAIN, LAINNYA, OPSI_ABAIKAN, RUTIN_TIDAK, RUTIN_YA, _centang, _unsur,
                                pecah_body, resolve_masjid, resolve_pemateri, tampil)
from ingest_core import (AUDIENCE, BELUM_DITENTUKAN, JENIS_WAKTU, ONLINE, InputError, bersihkan, label_masjid,
                         sekarang_wib)
from koreksi_core import parse_target

JUDUL_KOREKSI = "Koreksi kajian: "
TIDAK_DIUBAH = "(tidak diubah)"
AKSI_KOREKSI = "Koreksi"
AKSI_HAPUS = "Hapus"
KATA_KONFIRMASI = "HAPUS"
OPSI_RUTIN_K = [TIDAK_DIUBAH, RUTIN_YA, RUTIN_TIDAK]
PENANDA_KOREKSI = ("Aksi", "Target")

LABEL = {
    "aksi": "Aksi",
    "target": "Target",
    "konfirmasi": "Ketik HAPUS untuk konfirmasi",
    "judul": "Judul (koreksi)",
    "tanggal": "Tanggal (koreksi)",
    "jenis_waktu": "Jenis waktu (koreksi)",
    "jam": "Jam (koreksi)",
    "pemateri": "Pemateri (koreksi)",
    "pemateri_baru": "Pemateri baru (koreksi)",
    "masjid": "Masjid (koreksi)",
    "masjid_baru": "Nama masjid baru (koreksi)",
    "alamat_baru": "Alamat masjid baru (koreksi)",
    "kota_baru": "Kota masjid baru (koreksi)",
    "kota_lain": "Kota lain (koreksi)",
    "audience": "Audience (koreksi)",
    "rutin": "Kajian rutin (koreksi)",
    "abaikan_mirip": "Abaikan kemiripan nama (koreksi)",
    "catatan": "Catatan (koreksi)",
}
WAJIB = ["aksi", "target"]
# "kota_baru" (dropdown opsional) sengaja tidak dihitung: bisa terpilih otomatis oleh GitHub dan baru dipakai
# bila masjid dipilih 'Lainnya'.
KOLOM_KOREKSI = ["judul", "tanggal", "jenis_waktu", "jam", "pemateri", "pemateri_baru", "masjid", "masjid_baru",
                 "alamat_baru", "kota_lain", "audience", "rutin", "catatan"]


def render_template(kat):
    pemateri = sorted({p["nama"] for p in kat["pemateri"]}, key=str.casefold)
    masjid = sorted({label_masjid(m) for m in kat["masjid"]}, key=str.casefold)
    kota = sorted(kat["kota"], key=str.casefold)
    unsur = [
        _unsur("dropdown", "aksi", LABEL["aksi"],
               "Koreksi = ubah kolom yang Anda isi di bawah. Hapus = hilangkan event dari situs.",
               wajib=True, opsi=[AKSI_KOREKSI, AKSI_HAPUS]),
        _unsur("input", "target", LABEL["target"],
               "Event yang dituju: #12 (semua event yang masih ada dari Issue 12), id event (747), atau rentang id (747-750). "
               "Boleh digabung dengan koma. Id event ada di komentar Issue 'Tambah kajian'. Semua-atau-tidak-sama-sekali.",
               "#12", wajib=True),
        _unsur("input", "konfirmasi", LABEL["konfirmasi"],
               f"Hanya untuk Aksi = Hapus: ketik {KATA_KONFIRMASI}. Kosongkan untuk Koreksi."),
        _unsur("input", "judul", LABEL["judul"], "Kosong = tidak diubah."),
        _unsur("input", "tanggal", LABEL["tanggal"],
               "Satu tanggal baru, mis. 10 Okt 2026. Hanya bila Target satu event. Kosong = tidak diubah."),
        _unsur("dropdown", "jenis_waktu", LABEL["jenis_waktu"],
               "Mengubah waktu: pilih jenisnya (dan isi Jam bila Jam eksak).", opsi=[TIDAK_DIUBAH] + JENIS_WAKTU, bawaan=0),
        _unsur("input", "jam", LABEL["jam"],
               "09.30 atau 09.30-11.00. Hanya untuk Jam eksak (boleh diisi sendiri bila event sudah memakai jam eksak)."),
        _unsur("dropdown", "pemateri", LABEL["pemateri"], "Nama tanpa gelar.",
               opsi=[TIDAK_DIUBAH] + [tampil(p) for p in pemateri] + [BELUM_DITENTUKAN, LAINNYA], bawaan=0),
        _unsur("input", "pemateri_baru", LABEL["pemateri_baru"],
               "Wajib bila Pemateri = Lainnya. Tulis persis seperti di flyer; dicocokkan otomatis dengan yang sudah ada."),
        _unsur("dropdown", "masjid", LABEL["masjid"], "Format: Nama (Kota).",
               opsi=[TIDAK_DIUBAH] + [tampil(m) for m in masjid] + [ONLINE, LAINNYA], bawaan=0),
        _unsur("input", "masjid_baru", LABEL["masjid_baru"],
               "Wajib bila Masjid = Lainnya (nama saja, tanpa kota); untuk Online isi nama penyelenggara."),
        _unsur("input", "alamat_baru", LABEL["alamat_baru"], "Wajib bila Masjid = Lainnya."),
        _unsur("dropdown", "kota_baru", LABEL["kota_baru"], "Wajib bila Masjid = Lainnya.",
               opsi=[tampil(k) for k in kota] + [KOTA_LAIN]),
        _unsur("input", "kota_lain", LABEL["kota_lain"], "Wajib bila Kota masjid baru = Kota lain."),
        _unsur("dropdown", "audience", LABEL["audience"], opsi=[TIDAK_DIUBAH] + AUDIENCE, bawaan=0),
        _unsur("dropdown", "rutin", LABEL["rutin"], opsi=OPSI_RUTIN_K, bawaan=0),
        _unsur("checkboxes", "abaikan_mirip", LABEL["abaikan_mirip"],
               "Hanya bila sistem menolak karena nama baru mirip nama yang sudah ada dan Anda yakin nama itu baru.",
               kotak=OPSI_ABAIKAN),
        _unsur("textarea", "catatan", LABEL["catatan"], "Catatan baru (menggantikan yang lama). Kosong = tidak diubah."),
    ]
    kepala = (
        "# DIBUAT OTOMATIS oleh scripts/ingest.py dari data/kategori.json. Jangan edit manual.\n"
        "# Label kolom = kunci parser (scripts/adapter_koreksi_form.py); jangan diubah tanpa mengubah parser.\n"
        "name: Koreksi atau hapus kajian\n"
        "description: Koreksi atau hapus kajian yang sudah terbit (hanya pemilik repo).\n"
        f"title: {json.dumps(JUDUL_KOREKSI, ensure_ascii=False)}\n"
        "body:\n"
    )
    return kepala + "\n".join(unsur) + "\n"


def adalah_koreksi(body):
    """True bila isi Issue memuat judul kolom penanda formulir Koreksi atau hapus."""
    f = pecah_body(body)
    return all(k in f for k in PENANDA_KOREKSI)


def ke_paket(body, kat, events, hari_ini=None):
    """Isi Issue -> paket koreksi baku. Menaikkan InputError untuk struktur/konflik/target salah."""
    f = pecah_body(body)
    galat = []
    for k in WAJIB:
        if LABEL[k] not in f or not f[LABEL[k]]:
            galat.append(f"Kolom '{LABEL[k]}' kosong atau tidak ditemukan (isi Issue harus dari formulir Koreksi atau hapus).")
    if galat:
        raise InputError(galat)

    def v(k):
        return f.get(LABEL[k], "")

    aksi = v("aksi")
    if aksi not in (AKSI_KOREKSI, AKSI_HAPUS):
        raise InputError(f"Aksi: '{aksi}' tidak dikenal (pilih {AKSI_KOREKSI} atau {AKSI_HAPUS}).")
    try:
        ids = parse_target(v("target"), kat, events)
    except InputError as e:
        galat.extend(e.pesan)
        ids = []

    terisi = [LABEL[k] for k in KOLOM_KOREKSI
              if v(k) and v(k) != TIDAK_DIUBAH]
    if aksi == AKSI_HAPUS:
        if v("konfirmasi").strip().casefold() != KATA_KONFIRMASI.casefold():
            galat.append(f"Konfirmasi: untuk Aksi = Hapus, ketik {KATA_KONFIRMASI} pada kolom '{LABEL['konfirmasi']}'.")
        if terisi:
            galat.append("Aksi = Hapus, tetapi kolom koreksi terisi (" + ", ".join(terisi) + "). "
                         "Bila maksud Anda mengubah data, pilih Aksi = Koreksi. Bila ingin menghapus, kosongkan kolom koreksi.")
        if galat:
            raise InputError(galat)
        return {"aksi": "hapus", "ids": ids}

    # Koreksi
    if v("konfirmasi").strip():
        galat.append(f"Aksi = Koreksi, tetapi '{LABEL['konfirmasi']}' terisi. Pilih Aksi = Hapus, atau kosongkan kolom itu.")
    perub = {}
    if v("judul"):
        perub["judul"] = v("judul")
    if v("catatan"):
        perub["catatan"] = v("catatan")
    if v("tanggal"):
        try:
            rinci = tanggal_bebas.parse_rinci(v("tanggal"), hari_ini or sekarang_wib())
            if len(rinci["tanggal"]) != 1:
                galat.append("Tanggal (koreksi): isi satu tanggal saja (tanpa rentang atau daftar).")
            else:
                perub["tanggal"] = rinci["tanggal"][0]
        except InputError as e:
            galat.extend(e.pesan)
    if v("jenis_waktu") and v("jenis_waktu") != TIDAK_DIUBAH:
        perub["jenis_waktu"] = v("jenis_waktu")
    if v("jam"):
        perub["jam"] = v("jam")
    if v("audience") and v("audience") != TIDAK_DIUBAH:
        perub["audience"] = v("audience")
    if v("rutin") == RUTIN_YA:
        perub["rutin"] = True
    elif v("rutin") == RUTIN_TIDAK:
        perub["rutin"] = False

    def get_p(k):
        return v(k)

    # pemateri: (tidak diubah) -> kolom baru tidak boleh terisi
    if v("pemateri") in ("", TIDAK_DIUBAH):
        if v("pemateri_baru"):
            galat.append(f"Pemateri baru (koreksi): terisi '{v('pemateri_baru')}' tetapi Pemateri (koreksi) masih '{TIDAK_DIUBAH}'. "
                         f"Pilih '{LAINNYA}' atau kosongkan kolom itu.")
    else:
        perub["pemateri"] = resolve_pemateri(get_p, kat, galat)
    # masjid
    if v("masjid") in ("", TIDAK_DIUBAH):
        terisi_m = [LABEL[k] for k in ("masjid_baru", "alamat_baru", "kota_lain") if v(k)]
        if terisi_m:
            galat.append(f"Masjid (koreksi) masih '{TIDAK_DIUBAH}', tetapi kolom masjid baru terisi ({', '.join(terisi_m)}). "
                         f"Pilih masjid atau '{LAINNYA}', atau kosongkan kolom tersebut.")
    else:
        masjid, masjid_kota, masjid_baru = resolve_masjid(get_p, kat, galat, LABEL)
        perub["masjid"], perub["masjid_kota"], perub["masjid_baru"] = masjid, masjid_kota, masjid_baru
    if galat:
        raise InputError(galat)
    if not perub:
        raise InputError("Koreksi: tidak ada kolom koreksi yang diisi. Isi minimal satu kolom (kolom kosong atau "
                         f"'{TIDAK_DIUBAH}' berarti tidak diubah).")
    return {"aksi": "koreksi", "ids": ids, "perubahan": perub, "abaikan_mirip": _centang(v("abaikan_mirip"))}
