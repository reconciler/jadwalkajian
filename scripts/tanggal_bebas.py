#!/usr/bin/env python3
"""
Penguraian isian tanggal bebas (satu kolom) -> daftar tanggal ISO.

Dipakai adapter formulir Issue supaya Amal cukup mengetik satu isian pendek,
mis. `10 Okt 2026`, `10, 17, 24 Okt 2026`, `3-31 Okt 2026 Sabtu`,
`3 Okt - 4 Okt 2026`, `2026-10-10`. Issue form GitHub tidak punya pemilih
kalender, jadi inilah gantinya. Komentar balasan selalu menampilkan hasil
penguraian lengkap dengan nama hari supaya salah ketik terlihat.

Format yang dikenali (huruf besar/kecil bebas; apostrof diabaikan):
  - ISO: 2026-10-10 (boleh banyak, dipisah spasi/koma/baris baru)
  - Hari Bulan [Tahun]: 10 Okt 2026, 10 Oktober, sabtu 10 okt 2026
  - Angka: 10/10/2026, 10-10-2026, 10.10.2026, 10/10   (urutan hari/bulan/tahun)
  - Daftar: pisahkan dengan koma atau titik koma; "10, 17, 24 Okt 2026" memakai
    bulan/tahun dari tanggal terakhir yang lengkap
  - Rentang: 3-31 Okt 2026 | 3 Okt - 31 Okt 2026 | 3 Okt s/d 4 Okt | sampai | hingga
  - Filter hari untuk rentang: tambahkan nama hari di belakang, boleh "setiap",
    boleh beberapa dengan & atau dan atau /: "3-31 Okt 2026 setiap Sabtu & Ahad"
  - Nama hari di depan satu tanggal berfungsi sebagai pemeriksa: bila tidak cocok
    dengan tanggalnya, isian ditolak.
  - Tahun boleh dihilangkan: dipakai kejadian terdekat yang tidak lebih dari 30 hari
    yang lalu (mis. "5 Jan" ditulis bulan Desember = tahun depan).
  - Pengecualian: "3-31 Okt 2026 setiap Sabtu kecuali 17 Okt" atau "kecuali 17, 24 Okt"
    (berlaku untuk seluruh isian; satu kata "kecuali" saja; bulan boleh dihilangkan bila
    seluruh tanggal utama berada di satu bulan). Pengecualian di luar pola diberi peringatan.
  - Batas MAKS_TANGGAL (60) tanggal per isian, dihitung setelah pengecualian.
  - Ditolak dengan pesan alternatif (tidak dibangun): "tiap 2 minggu", "2 minggu sekali",
    "pekan/minggu ke-N", "bulanan", dan "setiap minggu" (ambigu: tiap pekan atau hari Minggu?).
  parse_rinci() juga mengembalikan pola yang terbaca dan penilaian "rutin otomatis":
  rutin bila ada rentang dengan filter hari yang menghasilkan >= 2 tanggal, atau bila
  tanggal hasil berjumlah >= 3 dengan jarak seragam 7 hari. Selain itu tidak rutin.
"""

import re
from datetime import date, timedelta

from ingest_core import BULAN as BULAN_SINGKAT
from ingest_core import HARI as HARI_SINGKAT
from ingest_core import MAKS_TANGGAL, InputError

BULAN = {
    "januari": 1, "jan": 1, "februari": 2, "pebruari": 2, "feb": 2, "maret": 3, "mar": 3,
    "april": 4, "apr": 4, "mei": 5, "juni": 6, "jun": 6, "juli": 7, "jul": 7,
    "agustus": 8, "agu": 8, "agt": 8, "ags": 8, "september": 9, "sep": 9, "sept": 9,
    "oktober": 10, "okt": 10, "november": 11, "nov": 11, "nop": 11, "desember": 12, "des": 12,
}
HARI = {
    "senin": 0, "sen": 0, "selasa": 1, "sel": 1, "rabu": 2, "rab": 2, "kamis": 3, "kam": 3,
    "jumat": 4, "jum": 4, "sabtu": 5, "sab": 5, "minggu": 6, "ahad": 6, "min": 6,
}
KATA_PENGANTAR = {"setiap", "tiap", "hari"}
PENGHUBUNG = {"&", "/", "dan"}
MAKS_RENTANG_HARI = 370
TOLERANSI_LALU = 30

_RENTANG = re.compile(r"\s+(?:-|s/d|sd|sampai|hingga)\s+")
_ISO = re.compile(r"\d{4}-\d{2}-\d{2}")


def _normal(teks):
    t = str(teks or "").lower().replace("'", "").replace("’", "").replace("`", "")
    t = t.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", t).strip()


def _tahun_terdekat(bulan, hari, hari_ini):
    """Tahun untuk tanggal tanpa tahun: kejadian terdekat yang tidak > 30 hari lalu."""
    for tahun in (hari_ini.year, hari_ini.year + 1, hari_ini.year + 2):
        try:
            d = date(tahun, bulan, hari)
        except ValueError:
            continue
        if d >= hari_ini - timedelta(days=TOLERANSI_LALU):
            return tahun
    return hari_ini.year


def _buat(tahun, bulan, hari, asal):
    try:
        return date(tahun, bulan, hari)
    except ValueError:
        raise InputError(f"Tanggal: '{asal}' bukan tanggal yang valid.")


def _tanggal_tunggal(ekspr, hari_ini, bawaan=None):
    """Satu tanggal. bawaan = (bulan, tahun) dari sisi lain rentang/daftar untuk 'D' polos.
    -> (date, (bulan, tahun_eksplisit_atau_None))"""
    asal = ekspr
    kata = ekspr.split(" ")
    nama_hari = None
    if kata and kata[0] in HARI and len(kata) > 1:
        nama_hari = HARI[kata[0]]
        kata = kata[1:]
    e = " ".join(kata)

    if _ISO.fullmatch(e):
        d = _buat(int(e[:4]), int(e[5:7]), int(e[8:]), asal)
        info = (d.month, d.year)
    else:
        m = re.fullmatch(r"(\d{1,2})[/.\-](\d{1,2})(?:[/.\-](\d{4}))?", e)
        if m:
            h, b, t = int(m.group(1)), int(m.group(2)), m.group(3)
            if not 1 <= b <= 12:
                raise InputError(f"Tanggal: '{asal}' bulan harus 1-12 (urutan hari/bulan/tahun).")
            tahun = int(t) if t else _tahun_terdekat(b, h, hari_ini)
            d = _buat(tahun, b, h, asal)
            info = (b, int(t) if t else None)
        else:
            m = re.fullmatch(r"(\d{1,2})(?: ([a-z]+))?(?: (\d{4}))?", e)
            if not m:
                raise InputError(f"Tanggal: '{asal}' tidak dikenali. Contoh: 10 Okt 2026, 3-31 Okt 2026 Sabtu.")
            h, nb, t = int(m.group(1)), m.group(2), m.group(3)
            if nb is None:
                if t is not None or bawaan is None:
                    raise InputError(f"Tanggal: '{asal}' perlu nama bulan (contoh: 10 Okt 2026).")
                b, tahun_info = bawaan
            else:
                if nb not in BULAN:
                    raise InputError(f"Tanggal: '{nb}' bukan nama bulan yang dikenali di '{asal}'.")
                b, tahun_info = BULAN[nb], (int(t) if t else None)
            tahun = tahun_info if tahun_info else _tahun_terdekat(b, h, hari_ini)
            d = _buat(tahun, b, h, asal)
            info = (b, tahun_info)
    if nama_hari is not None and d.weekday() != nama_hari:
        nama = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Ahad"][d.weekday()]
        raise InputError(f"Tanggal: '{asal}' tidak cocok, {d.isoformat()} adalah hari {nama}.")
    return d, info


def _pisah_filter_hari(item):
    """'3-31 okt 2026 setiap sabtu & ahad' -> ('3-31 okt 2026', {5, 6})."""
    kata = item.split(" ")
    hari, i = set(), len(kata)
    while i > 0:
        k = kata[i - 1]
        if k in HARI:
            hari.add(HARI[k])
        elif k in KATA_PENGANTAR or k in PENGHUBUNG:
            pass
        else:
            break
        i -= 1
    sisa = " ".join(kata[:i])
    if not hari:
        return item, set()
    return sisa, hari


def _daftar_rentang(a, b, hari_filter, asal):
    if b < a:
        raise InputError(f"Tanggal: rentang '{asal}' terbalik (akhir sebelum awal).")
    if (b - a).days > MAKS_RENTANG_HARI:
        raise InputError(f"Tanggal: rentang '{asal}' lebih dari {MAKS_RENTANG_HARI} hari.")
    hasil, d = [], a
    while d <= b:
        if not hari_filter or d.weekday() in hari_filter:
            hasil.append(d)
        d += timedelta(days=1)
    if not hasil:
        raise InputError(f"Tanggal: rentang '{asal}' tidak memuat hari yang dipilih.")
    return hasil


def _hanya_hari(item):
    kata = item.split(" ")
    return (all((k in HARI) or (k in KATA_PENGANTAR) or (k in PENGHUBUNG) for k in kata)
            and any(k in HARI for k in kata))


def _konteks_bulan(sisa):
    """(nama_bulan, tahun|None) bila item memuat nama bulan di akhir, selain itu None."""
    m = re.search(r"([a-z]+)(?: (\d{4}))?$", sisa)
    if m and m.group(1) in BULAN:
        return m.group(1), m.group(2)
    return None


def _fmt(d):
    return f"{HARI_SINGKAT[d.weekday()]} {d.day} {BULAN_SINGKAT[d.month - 1]} {d.year}"


_ALT = "Tulis daftar tanggalnya, mis. '3, 17, 31 Okt 2026'."
_TOLAK = [
    (re.compile(r"\b(?:tiap|setiap)\s+(?:\d+|dua|tiga|empat)\s+(?:minggu|pekan)\b"), "selang lebih dari satu minggu"),
    (re.compile(r"\b(?:\d+|dua|tiga|empat)\s+(?:minggu|pekan)\s+sekali\b"), "selang lebih dari satu minggu"),
    (re.compile(r"\b(?:minggu|pekan)\s+ke-?\s*(?:\d+|[ivx]+|satu|dua|tiga|empat|pertama|kedua|ketiga|keempat|terakhir)\b"), "pola 'pekan ke-N'"),
    (re.compile(r"\b(?:tiap|setiap)\s+bulan\b|\bbulanan\b"), "pola bulanan"),
]
_AMBIGU = re.compile(r"\b(?:tiap|setiap)\s+minggu\b")


def _tolak_pola_tak_didukung(t):
    for rx, nama in _TOLAK:
        m = rx.search(t)
        if m:
            raise InputError(f"Tanggal: '{m.group(0)}' tidak didukung ({nama}). {_ALT}")
    m = _AMBIGU.search(t)
    if m:
        raise InputError("Tanggal: 'setiap minggu' ambigu (tiap pekan atau hari Minggu?). "
                         "Sebut hari yang dimaksud (mis. 'setiap Sabtu') atau tulis 'Ahad' untuk hari Minggu.")


def _item_ke_tanggal(sisa, filt, asli, hari_ini):
    """Satu item (sudah tanpa filter hari di ujungnya) -> (daftar date, deskripsi, rentang_berfilter)."""
    bagian = _RENTANG.split(sisa)
    m = re.fullmatch(r"(\d{1,2})\s*-\s*(\d{1,2})( [a-z]+)?( \d{4})?", sisa)
    if m and m.group(3):
        bagian = [m.group(1), f"{m.group(2)}{m.group(3)}{m.group(4) or ''}"]
    if len(bagian) == 1:
        d, _ = _tanggal_tunggal(bagian[0], hari_ini)
        if filt and d.weekday() not in filt:
            raise InputError(f"Tanggal: '{asli}': {d.isoformat()} bukan hari yang disebut.")
        return [d], f"tanggal {_fmt(d)}", False
    if len(bagian) == 2:
        kanan, _ = _tanggal_tunggal(bagian[1], hari_ini)
        kiri, _ = _tanggal_tunggal(bagian[0], hari_ini, (kanan.month, kanan.year))
        if kiri.month > kanan.month and kiri.year == kanan.year and not re.search(r"\d{4}", bagian[0]):
            kiri = date(kiri.year - 1, kiri.month, kiri.day)  # "28 Des - 3 Jan 2027"
        hasil = _daftar_rentang(kiri, kanan, filt, asli)
        desk = f"rentang {_fmt(kiri)} s/d {_fmt(kanan)}"
        if filt:
            desk += ", hanya hari " + " & ".join(HARI_SINGKAT[h] for h in sorted(filt))
        return hasil, desk, bool(filt)
    raise InputError(f"Tanggal: '{asli}' memuat lebih dari satu rentang.")


def _parse_item_list(t, hari_ini, ctx_default=None):
    """Teks tanpa 'kecuali' -> (daftar date, [deskripsi item], ada_rentang_berfilter_ge2)."""
    token = [x for x in re.split(r"[\s,;]+", t) if x]
    if token and all(_ISO.fullmatch(x) for x in token):
        ds = [_buat(int(x[:4]), int(x[5:7]), int(x[8:]), x) for x in token]
        return ds, [f"{len(set(ds))} tanggal ISO"], False

    mentah = [x.strip() for x in re.split(r"[;,\n]", t) if x.strip()]
    galat, item_list = [], []
    for item in mentah:
        if _hanya_hari(item):
            if item_list:
                item_list[-1][1] |= _pisah_filter_hari(item)[1]
            else:
                galat.append(f"Tanggal: '{item}' berdiri sendiri; tulis nama hari di belakang rentang tanggalnya.")
            continue
        sisa, filt = _pisah_filter_hari(item)
        item_list.append([sisa, set(filt), item])
    if galat:
        raise InputError(galat)

    # "10, 17, 24 Okt 2026": tanggal polos meminjam bulan/tahun dari item berikutnya yang bernama bulan
    ctx = ctx_default
    for entri in reversed(item_list):
        sisa = entri[0]
        k = _konteks_bulan(sisa)
        if k:
            ctx = k
        elif ctx and re.fullmatch(r"(?:[a-z]+ )?\d{1,2}", sisa):
            entri[0] = f"{sisa} {ctx[0]}" + (f" {ctx[1]}" if ctx[1] else "")

    hasil, deskripsi, rentang_filter = [], [], False
    for sisa, filt, asli in item_list:
        try:
            ds, desk, berfilter = _item_ke_tanggal(sisa, filt, asli, hari_ini)
        except InputError as e:
            galat.extend(e.pesan)
            continue
        hasil += ds
        deskripsi.append(desk)
        if berfilter and len(set(ds)) >= 2:
            rentang_filter = True
    if galat:
        raise InputError(galat)
    return hasil, deskripsi, rentang_filter


def _seragam_tujuh(ds):
    ds = sorted(set(ds))
    return len(ds) >= 3 and all((b - a).days == 7 for a, b in zip(ds, ds[1:]))


def parse_rinci(teks, hari_ini):
    """-> dict: tanggal (ISO unik terurut), pola (teks), dikecualikan (ISO), peringatan (list),
    rutin_otomatis (bool), rutin_alasan (teks). Menaikkan InputError bila isian tidak sah."""
    t = _normal(teks)
    if not t:
        raise InputError("Tanggal: wajib diisi (contoh: 10 Okt 2026).")
    _tolak_pola_tak_didukung(t)

    bagian = re.split(r"\bkecuali\b", t)
    if len(bagian) > 2:
        raise InputError("Tanggal: kata 'kecuali' hanya boleh sekali; gabungkan tanggal pengecualian dalam satu daftar.")
    utama = bagian[0].strip(" ,;")
    if not utama:
        raise InputError("Tanggal: tulis tanggal atau rentang sebelum 'kecuali'.")
    if len(bagian) == 2 and not bagian[1].strip(" ,;"):
        raise InputError("Tanggal: tulis tanggal yang dikecualikan setelah 'kecuali' (mis. 'kecuali 17 Okt').")

    ds, deskripsi, rentang_filter = _parse_item_list(utama, hari_ini)
    himpunan = sorted(set(ds))
    peringatan, dikecualikan = [], []

    if len(bagian) == 2:
        bulan_tahun = {(d.month, d.year) for d in himpunan}
        ctx = None
        if len(bulan_tahun) == 1:
            (b, y), = bulan_tahun
            nama_bulan = next(k for k, v in BULAN.items() if v == b and len(k) >= 3 and k not in ("sept", "agt", "ags", "nop", "pebruari"))
            ctx = (nama_bulan, str(y))
        ex, _, _ = _parse_item_list(bagian[1].strip(" ,;"), hari_ini, ctx)
        tahun_utama = sorted({d.year for d in himpunan})
        ada = set(himpunan)
        for e in sorted(set(ex)):
            kandidat = [e] + [date(y, e.month, e.day) for y in tahun_utama if e.year != y and not (e.month == 2 and e.day == 29)]
            cocok_ = next((k for k in kandidat if k in ada), None)
            if cocok_:
                dikecualikan.append(cocok_)
            else:
                peringatan.append(f"Pengecualian {_fmt(e)} bukan bagian pola; diabaikan.")
        ada -= set(dikecualikan)
        himpunan = sorted(ada)
        if not himpunan:
            raise InputError("Tanggal: semua tanggal dikecualikan; tidak ada event yang tersisa.")

    if len(himpunan) > MAKS_TANGGAL:
        raise InputError(f"Tanggal: isian ini menghasilkan {len(himpunan)} tanggal, melebihi batas {MAKS_TANGGAL} per Issue. "
                         "Persempit rentangnya (mis. tambah filter hari 'setiap Sabtu') atau pecah menjadi beberapa Issue.")

    pola = "; ".join(deskripsi)
    if len(deskripsi) > 1 and all(x.startswith("tanggal ") for x in deskripsi):
        pola = f"daftar {len(deskripsi)} tanggal"
    if dikecualikan:
        pola += "; kecuali " + ", ".join(_fmt(d) for d in dikecualikan)
    if rentang_filter and len(himpunan) >= 2:
        rutin, alasan = True, "rentang dengan filter hari"
    elif _seragam_tujuh(himpunan):
        rutin, alasan = True, "tiga tanggal atau lebih berjarak tepat 7 hari"
    else:
        rutin, alasan = False, "satu tanggal, daftar tidak seragam, atau rentang tanpa filter hari"
    return {"tanggal": [d.isoformat() for d in himpunan], "pola": pola,
            "dikecualikan": [d.isoformat() for d in dikecualikan], "peringatan": peringatan,
            "rutin_otomatis": rutin, "rutin_alasan": alasan}


def parse(teks, hari_ini):
    """-> daftar tanggal ISO unik terurut (lihat parse_rinci untuk pola/pengecualian/rutin otomatis)."""
    return parse_rinci(teks, hari_ini)["tanggal"]
