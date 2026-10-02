#!/usr/bin/env python3
"""
Logika inti ingest event (tahap 1 sistem input lewat Issue GitHub).

Modul ini TIDAK tahu apa-apa soal formulir Issue. Ia menerima "paket baku"
(dict) dari adapter mana pun (sekarang: adapter_issue_form.py; kelak bisa
Google Form) lalu memvalidasi, membuat baris event, dan memperbarui daftar
induk data/kategori.json.

Paket baku:
  tanggal            list[str]  "YYYY-MM-DD" (sudah dipecah per baris)
  jenis_waktu        str        "Jam eksak" | "Dhuha" | "Ba'da Subuh" | ...
  jam                str        "09.30" atau "09.30-11.00" (hanya Jam eksak)
  judul              str
  pemateri           str        nama final (atau "Belum ditentukan")
  pemateri_perempuan bool
  masjid             str        nama final
  masjid_baru        dict|None  {"alamat": str, "kota": str} bila masjid belum
                                ada di daftar induk (atau untuk Online)
  audience           str
  rutin              bool
  catatan            str

Keamanan: semua teks dibersihkan (karakter kontrol dibuang, spasi/baris baru
dilipat, tanda < dan > ditolak) dan baris event ditulis lewat json.dumps, jadi
tidak ada jalan menutup <script> atau merusak regex prune.py.
"""

import difflib
import json
import re
import sys
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402  (parse_events, EVENT_LINE_RX)

TZ = ZoneInfo("Asia/Jakarta")
HARI = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

JAM_EKSAK = "Jam eksak"
WAKTU_SALAT = {
    "Dhuha": 9,
    "Ba'da Subuh": 4.5,
    "Ba'da Zuhur": 12.5,
    "Ba'da Ashar": 15.5,
    "Ba'da Maghrib": 18,
}
JENIS_WAKTU = [JAM_EKSAK] + list(WAKTU_SALAT)
AUDIENCE = ["Terbuka untuk umum", "Khusus Akhwat", "Khusus Ikhwan"]
BELUM_DITENTUKAN = "Belum ditentukan"
ONLINE = "Online"

BATAS = {"judul": 200, "pemateri": 120, "masjid": 120, "alamat": 250, "kota": 60, "catatan": 600}
MAKS_TANGGAL = 60
MAKS_HARI_KE_DEPAN = 730
AMBANG_MIRIP = 0.85

KUNCI_EVENT = ["id", "date", "dayShort", "timeLabel", "timeOrder", "title", "ustadz",
               "masjid", "area", "address", "audience", "note", "isRutin"]

_KONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f  ]")


class InputError(Exception):
    """Isian tidak valid. .pesan = daftar alasan (Bahasa Indonesia)."""

    def __init__(self, pesan):
        if isinstance(pesan, str):
            pesan = [pesan]
        self.pesan = list(pesan)
        super().__init__("; ".join(self.pesan))


# ---------- pembersihan teks ----------

def bersihkan(nilai, nama, batas=None, wajib=False):
    """Satu baris teks aman. Ganti baris baru/tab dengan spasi, buang karakter kontrol."""
    s = unicodedata.normalize("NFC", str(nilai or ""))
    s = _KONTROL.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if wajib and not s:
        raise InputError(f"{nama}: wajib diisi.")
    if "<" in s or ">" in s:
        raise InputError(f"{nama}: tanda < dan > tidak diperbolehkan.")
    if batas and len(s) > batas:
        raise InputError(f"{nama}: terlalu panjang ({len(s)} karakter, maksimum {batas}).")
    return s


def rapikan_huruf(s):
    """Bila seluruhnya huruf kecil atau besar, ubah ke huruf kapital awal tiap kata."""
    if s and (s == s.lower() or s == s.upper()):
        return s.title()
    return s


def kunci(s):
    return re.sub(r"\s+", " ", s).strip().casefold()


def cocok(nama, daftar):
    """Nama kanonik dari daftar yang sama (abaikan huruf besar/kecil & spasi), atau None."""
    k = kunci(nama)
    for d in daftar:
        if kunci(d) == k:
            return d
    return None


def mirip(nama, daftar):
    """Entri daftar yang mirip tetapi tidak sama persis."""
    k = kunci(nama)
    hasil = []
    for d in daftar:
        kd = kunci(d)
        if kd != k and difflib.SequenceMatcher(None, k, kd).ratio() >= AMBANG_MIRIP:
            hasil.append(d)
    return hasil


# ---------- daftar induk ----------

def muat_kategori(path):
    p = Path(path)
    d = json.loads(p.read_text(encoding="utf-8"))
    d.setdefault("kota", [])
    d.setdefault("kota_khusus", [ONLINE])
    d.setdefault("masjid", {})
    d.setdefault("pemateri", [])
    d.setdefault("diproses", [])
    d.setdefault("gagal", [])
    return d


def simpan_kategori(path, d):
    d["kota"] = sorted(set(d["kota"]), key=str.casefold)
    d["masjid"] = dict(sorted(d["masjid"].items(), key=lambda x: x[0].casefold()))
    belum = [p for p in d["pemateri"] if p == BELUM_DITENTUKAN]
    lain = sorted({p for p in d["pemateri"] if p != BELUM_DITENTUKAN}, key=str.casefold)
    d["pemateri"] = lain + belum
    Path(path).write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---------- waktu ----------

def parse_jam(jam):
    """'09.30' / '9:30' / '09.30-11.00' -> (timeLabel, timeOrder)."""
    s = jam.replace("–", "-").replace("—", "-").replace("WIB", "").replace("wib", "").strip()
    bagian = [b.strip() for b in s.split("-")]
    if len(bagian) not in (1, 2) or not all(bagian):
        raise InputError("Jam: gunakan format 09.30 atau 09.30-11.00.")
    hasil = []
    for b in bagian:
        m = re.fullmatch(r"(\d{1,2})[.:](\d{2})", b)
        if not m:
            raise InputError(f"Jam: '{b}' bukan format jam yang valid (contoh 09.30).")
        h, mnt = int(m.group(1)), int(m.group(2))
        if h > 23 or mnt > 59:
            raise InputError(f"Jam: '{b}' di luar rentang 00.00-23.59.")
        hasil.append((h, mnt))
    label = " – ".join(f"{h:02d}.{m:02d}" for h, m in hasil) + " WIB"
    order = round(hasil[0][0] + hasil[0][1] / 60, 2)
    if order == int(order):
        order = int(order)
    return label, order


def label_waktu(jenis, jam):
    """-> (timeLabel, timeOrder, peringatan|None)."""
    if jenis == JAM_EKSAK:
        if not jam:
            raise InputError("Jam: wajib diisi bila Jenis waktu = Jam eksak.")
        label, order = parse_jam(jam)
        return label, order, None
    if jenis not in WAKTU_SALAT:
        raise InputError(f"Jenis waktu: '{jenis}' tidak dikenal.")
    order = WAKTU_SALAT[jenis]
    peringatan = "Kolom Jam diabaikan karena Jenis waktu bukan Jam eksak." if jam else None
    return jenis, order, peringatan


def parse_tanggal(teks_list, hari_ini):
    """-> (daftar date unik terurut, daftar (tanggal, alasan) yang dilewati karena lampau)."""
    if not teks_list:
        raise InputError("Tanggal: wajib diisi (satu tanggal per baris, YYYY-MM-DD).")
    if len(teks_list) > MAKS_TANGGAL:
        raise InputError(f"Tanggal: maksimum {MAKS_TANGGAL} tanggal per Issue.")
    unik, galat = {}, []
    for t in teks_list:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", t):
            galat.append(f"Tanggal: '{t}' bukan format YYYY-MM-DD.")
            continue
        try:
            d = date.fromisoformat(t)
        except ValueError:
            galat.append(f"Tanggal: '{t}' bukan tanggal yang valid.")
            continue
        if d > hari_ini + timedelta(days=MAKS_HARI_KE_DEPAN):
            galat.append(f"Tanggal: '{t}' lebih dari {MAKS_HARI_KE_DEPAN} hari ke depan (salah tahun?).")
            continue
        unik[d] = True
    if galat:
        raise InputError(galat)
    lampau = [(d.isoformat(), "sudah lewat") for d in unik if d < hari_ini]
    ke_depan = sorted(d for d in unik if d >= hari_ini)
    return ke_depan, lampau


# ---------- membangun event ----------

def day_short(d):
    return f"{HARI[d.weekday()]} {d.day} {BULAN[d.month - 1]}"


def bangun_event(paket, kat, hari_ini, events_ada):
    """Validasi paket dan buat event (tanpa id). Mengembalikan dict hasil.

    kat tidak diubah di sini; perubahan daftar induk dikembalikan di 'baru'
    dan diterapkan oleh terapkan_kategori().
    """
    galat = []

    def aman(fungsi, *a, **kw):
        try:
            return fungsi(*a, **kw)
        except InputError as e:
            galat.extend(e.pesan)
            return None

    judul = aman(bersihkan, paket.get("judul"), "Judul", BATAS["judul"], True)
    catatan = aman(bersihkan, paket.get("catatan"), "Catatan", BATAS["catatan"])
    pemateri_in = aman(bersihkan, paket.get("pemateri"), "Pemateri", BATAS["pemateri"], True)
    masjid_in = aman(bersihkan, paket.get("masjid"), "Masjid", BATAS["masjid"], True)
    tanggal = aman(parse_tanggal, paket.get("tanggal") or [], hari_ini)
    jam = aman(bersihkan, paket.get("jam"), "Jam", 40)
    waktu = aman(label_waktu, paket.get("jenis_waktu"), jam or "")

    audience = paket.get("audience")
    if audience not in AUDIENCE:
        galat.append(f"Audience: '{audience}' tidak dikenal.")
    if paket.get("pemateri_perempuan"):
        if audience == "Khusus Ikhwan":
            galat.append("Audience: pemateri perempuan tidak cocok dengan Khusus Ikhwan.")
        audience = "Khusus Akhwat"

    peringatan, baru = [], {"kota": [], "masjid": [], "pemateri": []}

    # pemateri
    ustadz = None
    if pemateri_in:
        if kunci(pemateri_in) == kunci(BELUM_DITENTUKAN):
            ustadz = BELUM_DITENTUKAN
        else:
            ada = cocok(pemateri_in, kat["pemateri"])
            if ada:
                ustadz = ada
            else:
                ustadz = pemateri_in
                baru["pemateri"].append(ustadz)
                for m in mirip(ustadz, kat["pemateri"])[:3]:
                    peringatan.append(f"Pemateri baru '{ustadz}' mirip dengan yang sudah ada: '{m}'. Diproses sebagai pemateri baru.")

    # masjid + kota
    masjid = area = alamat = None
    if masjid_in:
        ada = cocok(masjid_in, kat["masjid"].keys())
        if ada:
            masjid = ada
            area = kat["masjid"][ada]["kota"]
            alamat = kat["masjid"][ada]["alamat"]
            mb = paket.get("masjid_baru") or {}
            alamat_in = re.sub(r"\s+", " ", str(mb.get("alamat") or "")).strip()
            if alamat_in and kunci(alamat_in) != kunci(alamat):
                peringatan.append(f"Masjid '{masjid}' sudah ada; alamat dan kota dari daftar induk dipakai, isian baru diabaikan.")
        else:
            mb = paket.get("masjid_baru") or {}
            a = aman(bersihkan, mb.get("alamat"), "Alamat masjid baru", BATAS["alamat"], True)
            k = aman(bersihkan, mb.get("kota"), "Kota masjid baru", BATAS["kota"], True)
            if a and k:
                if kunci(k) == kunci(ONLINE):
                    kota = ONLINE
                else:
                    kota = cocok(k, kat["kota"]) or rapikan_huruf(k)
                    if kota not in kat["kota"]:
                        baru["kota"].append(kota)
                        for m in mirip(kota, kat["kota"])[:3]:
                            peringatan.append(f"Kota baru '{kota}' mirip dengan yang sudah ada: '{m}'. Diproses sebagai kota baru.")
                masjid, area, alamat = masjid_in, kota, a
                baru["masjid"].append(masjid)
                for m in mirip(masjid, kat["masjid"].keys())[:3]:
                    peringatan.append(f"Masjid baru '{masjid}' mirip dengan yang sudah ada: '{m}'. Diproses sebagai masjid baru.")

    if galat:
        raise InputError(galat)

    ke_depan, lampau = tanggal
    label, order, pw = waktu
    if pw:
        peringatan.append(pw)

    ada_kunci = {(e["date"], kunci(e["masjid"]), e["timeLabel"], kunci(e["title"])) for e in events_ada}
    events, dilewati = [], [(t, a) for t, a in lampau]
    for d in ke_depan:
        tanda = (d.isoformat(), kunci(masjid), label, kunci(judul))
        if tanda in ada_kunci:
            dilewati.append((d.isoformat(), "duplikat (sudah ada)"))
            continue
        ada_kunci.add(tanda)
        events.append({
            "date": d.isoformat(), "dayShort": day_short(d), "timeLabel": label,
            "timeOrder": order, "title": judul, "ustadz": ustadz, "masjid": masjid,
            "area": area, "address": alamat, "audience": audience, "note": catatan,
            "isRutin": bool(paket.get("rutin")),
        })

    if not events and any(a == "sudah lewat" for _, a in dilewati) and not any(a.startswith("duplikat") for _, a in dilewati):
        raise InputError("Semua tanggal sudah lewat; tidak ada event yang ditambahkan.")

    return {"events": events, "dilewati": dilewati, "peringatan": peringatan,
            "baru": baru, "alamat": alamat, "area": area}


def terapkan_kategori(kat, hasil):
    """Masukkan kota/masjid/pemateri baru ke daftar induk (hanya bila ada event baru)."""
    if not hasil["events"]:
        return
    for k in hasil["baru"]["kota"]:
        if k not in kat["kota"]:
            kat["kota"].append(k)
    for m in hasil["baru"]["masjid"]:
        kat["masjid"][m] = {"kota": hasil["area"], "alamat": hasil["alamat"]}
    for p in hasil["baru"]["pemateri"]:
        if p not in kat["pemateri"]:
            kat["pemateri"].append(p)


# ---------- penulisan ke index.html ----------

def baris_event(ev, id_):
    pasangan = [("id", id_)] + [(k, ev[k]) for k in KUNCI_EVENT[1:]]
    return "  {" + ",".join(f"{k}:{json.dumps(v, ensure_ascii=False)}" for k, v in pasangan) + "},"


def id_berikutnya(html):
    ids = [int(i) for i in re.findall(r"\{id:(\d+),date:", html)]
    return (max(ids) if ids else 0) + 1


def sisipkan(html, baris):
    cocokan = [m for m in re.finditer(r"^ *\{id:\d+,date:.*\},\s*$", html, re.M)]
    if not cocokan:
        raise RuntimeError("Tidak ada baris event di index.html; tidak bisa menyisipkan.")
    akhir = cocokan[-1].end()
    return html[:akhir] + "\n" + "\n".join(baris) + html[akhir:]


def events_dari_html(html):
    return build.parse_events(html)


def sekarang_wib():
    return datetime.now(TZ).date()
