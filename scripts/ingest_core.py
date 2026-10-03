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
  pemateri           str        nama bersih dari daftar ATAU nama baru persis seperti di
                                flyer (dicocokkan otomatis ke master) atau "Belum ditentukan"
  pemateri_perempuan bool
  masjid             str        nama masjid (tanpa kota)
  masjid_kota        str        kota masjid yang DIPILIH dari daftar induk (opsional;
                                wajib bila nama sama ada di beberapa kota)
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

# Pengarah arah teks (bidi), spasi lebar nol, joiner kata, BOM: dibuang (bukan diganti spasi). ZWJ/ZWNJ (200C, 200D)
# dipertahankan karena dipakai urutan emoji.
_BIDI = re.compile("[\u200b\u200e\u200f\u202a-\u202e\u2060-\u2064\u2066-\u2069\ufeff]")

# Kata generik (Q8): nama baru yang SELURUH katanya ada di daftar ini ditolak. Daftar eksplisit, mudah diubah di sini.
GENERIK = frozenset({
    "masjid", "mesjid", "musholla", "mushola", "mushalla", "musala", "surau", "langgar", "majelis", "majlis", "taklim", "talim",
    "ustadz", "ustadzah", "ustadzaat", "ustaz", "ustazah", "ust", "ustd", "kh", "kyai", "kiai", "buya", "habib", "syaikh",
    "syekh", "sheikh", "kang", "dr", "drs", "prof", "hj", "haji", "kajian", "pemateri", "penceramah", "narasumber",
    "pengajar", "asatidz", "asatidzah", "nama",
})
MIN_HURUF = 3



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
    s = _BIDI.sub("", s)
    s = _KONTROL.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if wajib and not s:
        raise InputError(f"{nama}: wajib diisi.")
    if "<" in s or ">" in s:
        raise InputError(f"{nama}: tanda < dan > tidak diperbolehkan.")
    if batas and len(s) > batas:
        raise InputError(f"{nama}: terlalu panjang ({len(s)} karakter, maksimum {batas}).")
    return s


def bermakna(teks, nama, generik=False):
    """Tolak teks yang jelas bukan nama/judul: kurang dari MIN_HURUF huruf (mis. '0', '2026', '()', 'a'), atau (bila
    generik=True) seluruh katanya ada di GENERIK (mis. 'Masjid', 'Ustadz', 'Kajian')."""
    huruf = sum(1 for c in teks if unicodedata.category(c).startswith("L"))
    if huruf < MIN_HURUF:
        raise InputError(f"{nama}: '{teks}' bukan nama yang bermakna (minimal {MIN_HURUF} huruf).")
    if generik:
        kata = [k for k in (re.sub(r"[^\w]", "", t).casefold() for t in teks.split()) if k]
        if kata and all(k in GENERIK for k in kata):
            raise InputError(f"{nama}: '{teks}' hanya kata umum; tulis nama lengkapnya.")


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


# ---------- nama bersih ----------

_SAPAAN = (r"(?:assoc\.?|prof\.?|dr\.?\s*\(hc\)|dr\.?|drs\.?|k\.?h\.?|hj\.?|h\.?a\.?|h\.?|"
           r"ustadzah|ustadz|ust\.?|syaikh|sheikh|syekh|kang)")
_GELAR_AKHIR = re.compile(r"(?:lc|ma|mm|msi|me|mh|sh|m\.?ag|s\.?pd|s\.?ag|m\.?pd|m\.?hum|b\.?il|cifp|cfrm)\.?", re.I)
_MAJEMUK = re.compile(r"&| dan |\((?!hc\))", re.I)


def nama_bersih(teks):
    """Nama pemateri tanpa sapaan dan gelar, untuk dropdown, pencarian, dan pencocokan.
    'Ustadz Dr. Ahmad Ba'mualim, Lc., M.Pd.' -> "Ahmad Ba'mualim".
    Entri majemuk/organisasi (memuat &, 'dan', atau tanda kurung) dibiarkan apa adanya."""
    n = re.sub(r"\s+", " ", str(teks)).strip()
    if _MAJEMUK.search(n):
        return n
    n = n.split(",")[0].strip()
    toks = n.split()
    while len(toks) > 1 and _GELAR_AKHIR.fullmatch(toks[-1]):
        toks.pop()
    n = " ".join(toks)
    sebelumnya = None
    while sebelumnya != n:
        sebelumnya = n
        m = re.match(r"^" + _SAPAAN + r"\s+(?=\S)", n, re.I)
        if m:
            n = n[m.end():].strip()
    return n or str(teks).strip()


def bersihkan_nama_masjid(nama, kota):
    """Buang nama kota di belakang nama masjid ('Masjid Ar-Riyadh Depok' + Depok ->
    'Masjid Ar-Riyadh'). Hanya bila sisanya masih >= 2 kata dan kota bukan Online."""
    if not kota or kunci(kota) == kunci(ONLINE):
        return nama
    m = re.fullmatch(r"(.+?)[\s,\-]+" + re.escape(kota) + r"\s*", nama, re.I)
    if m and len(m.group(1).split()) >= 2:
        return m.group(1).strip()
    return nama


def label_masjid(m):
    """Teks dropdown masjid: 'Nama (Kota)'; tanpa tambahan bila kota sudah ada di nama / Online."""
    if kunci(m["kota"]) == kunci(ONLINE) or kunci(m["nama"]).endswith(" " + kunci(m["kota"])):
        return m["nama"]  # Online, atau kota sudah ada di namanya ("Baitusyaakiriin Depok")
    return f"{m['nama']} ({m['kota']})"


PLACEHOLDER = {"belum ditentukan", "belum ada", "belum diketahui", "tbd", "tba", "-", "--", "?", "??",
               "n/a", "na", "tidak ada", "kosong", "nama masjid", "nama pemateri"}
_PEREMPUAN = re.compile(r"^(?:ustadzah|ustadzaat|ustazah)\b", re.I)


def placeholder(teks):
    """True bila teks hanya isian pengganti (mis. 'belum ditentukan', '-'), bukan nama sungguhan."""
    return kunci(re.sub(r"\s*\(online\)\s*$", "", str(teks), flags=re.I)) in PLACEHOLDER


def pemateri_perempuan(tampil):
    """Sapaan perempuan di nama lengkap (Ustadzah/Ustadzaat) -> kajiannya Khusus Akhwat."""
    return bool(_PEREMPUAN.match(str(tampil).strip()))


# ---------- daftar induk ----------
#   kota        list[str]
#   kota_khusus list[str]   (Online)
#   masjid      list[{nama, kota, alamat, tampil}]  identitas = (nama, kota); tampil = teks di event
#   pemateri    list[{nama, tampil, alias[]}]       nama = bersih (dropdown); tampil = lengkap (event)
#   diproses    list[{issue, id[]}]    gagal list[{issue, alasan[]}]

def muat_kategori(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    d.setdefault("kota", [])
    d.setdefault("kota_khusus", [ONLINE])
    d.setdefault("masjid", [])
    d.setdefault("pemateri", [])
    d.setdefault("diproses", [])
    d.setdefault("gagal", [])
    d.setdefault("id_tertinggi", 0)  # id event tertinggi yang pernah dipakai; id tidak pernah dipakai ulang
    return d


def simpan_kategori(path, d):
    d["kota"] = sorted(set(d["kota"]), key=str.casefold)
    d["masjid"] = sorted(d["masjid"], key=lambda m: (m["nama"].casefold(), m["kota"].casefold()))
    d["pemateri"] = sorted(d["pemateri"], key=lambda p: p["nama"].casefold())
    Path(path).write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cari_pemateri(kat, teks):
    """Pemateri master yang cocok dengan teks (nama bersih, tampil, atau alias), atau None."""
    k, kb = kunci(teks), kunci(nama_bersih(teks))
    for p in kat["pemateri"]:
        if kunci(p["nama"]) in (k, kb) or kunci(p["tampil"]) == k:
            return p
        for a in p.get("alias", []):
            if kunci(a) == k or kunci(nama_bersih(a)) == kb:
                return p
    return None


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
    if len(hasil) == 2 and hasil[1][0] * 60 + hasil[1][1] <= hasil[0][0] * 60 + hasil[0][1]:
        raise InputError("Jam: jam selesai harus setelah jam mulai (rentang yang melewati tengah malam tidak didukung; "
                         "tulis jam mulai saja atau pecah menjadi Issue terpisah).")
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
    if jam:
        raise InputError(f"Jam: diisi '{jam}' tetapi Jenis waktu '{jenis}' bukan Jam eksak. "
                         "Pilih Jenis waktu 'Jam eksak' atau kosongkan kolom Jam.")
    return jenis, WAKTU_SALAT[jenis], None


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
    if judul:
        if placeholder(judul):
            galat.append(f"Judul: '{judul}' bukan judul. Isi judul kajian yang sebenarnya.")
        else:
            aman(bermakna, judul, "Judul")
    catatan = aman(bersihkan, paket.get("catatan"), "Catatan", BATAS["catatan"])
    pemateri_in = aman(bersihkan, paket.get("pemateri"), "Pemateri", BATAS["pemateri"], True)
    masjid_in = aman(bersihkan, paket.get("masjid"), "Masjid", BATAS["masjid"], True)
    tanggal = aman(parse_tanggal, paket.get("tanggal") or [], hari_ini)
    jam = aman(bersihkan, paket.get("jam"), "Jam", 40)
    waktu = aman(label_waktu, paket.get("jenis_waktu"), jam or "")

    audience = paket.get("audience")
    if audience not in AUDIENCE:
        galat.append(f"Audience: '{audience}' tidak dikenal.")
    perempuan = bool(paket.get("pemateri_perempuan"))
    abaikan_mirip = bool(paket.get("abaikan_mirip"))

    peringatan = []

    def kemiripan(pesan):
        """Nama baru yang mirip nama lama: ditolak kecuali pengguna mencentang 'Abaikan kemiripan nama'."""
        if abaikan_mirip:
            peringatan.append(pesan + " (kemiripan diabaikan atas permintaan pengguna)")
        else:
            galat.append(pesan + " Pilih dari daftar, atau centang 'Abaikan kemiripan nama' bila yakin ini baru.")

    baru = {"kota": [], "masjid": [], "pemateri": [], "alias": []}

    # pemateri: cocokkan otomatis ke master (nama bersih/alias); event memakai nama lengkap master
    ustadz = None
    if pemateri_in:
        if kunci(pemateri_in) == kunci(BELUM_DITENTUKAN):
            ustadz = BELUM_DITENTUKAN
        else:
            p = cari_pemateri(kat, pemateri_in)
            if p:
                ustadz = p["tampil"]
                if p.get("perempuan") or pemateri_perempuan(p["tampil"]):
                    perempuan = True
                if kunci(pemateri_in) not in (kunci(p["tampil"]), kunci(p["nama"])):
                    peringatan.append(f"Pemateri '{pemateri_in}' dicocokkan otomatis dengan '{p['tampil']}'; event memakai '{p['tampil']}'.")
                    baru["alias"].append((p["nama"], pemateri_in))
            elif placeholder(pemateri_in):
                galat.append(f"Pemateri: '{pemateri_in}' bukan nama. Isi nama pemateri, atau pilih 'Belum ditentukan'.")
            else:
                aman(bermakna, pemateri_in, "Pemateri baru", True)
                nama = nama_bersih(pemateri_in)
                ustadz = pemateri_in
                ent = {"nama": nama, "tampil": pemateri_in, "alias": []}
                if pemateri_perempuan(pemateri_in):
                    ent["perempuan"] = True
                    perempuan = True
                baru["pemateri"].append(ent)
                for m in mirip(nama, [x["nama"] for x in kat["pemateri"]])[:3]:
                    kemiripan(f"Pemateri baru '{nama}' mirip dengan yang sudah ada: '{m}'.")

    # masjid + kota: identitas = (nama, kota)
    entri = None
    if masjid_in:
        mb = paket.get("masjid_baru")
        if mb is None:  # dipilih dari daftar induk
            cand = [m for m in kat["masjid"] if kunci(m["nama"]) == kunci(masjid_in)]
            kp = re.sub(r"\s+", " ", str(paket.get("masjid_kota") or "")).strip()
            if kp:
                cand = [m for m in cand if kunci(m["kota"]) == kunci(kp)]
            if len(cand) == 1:
                entri = cand[0]
            elif not cand:
                galat.append(f"Masjid '{masjid_in}' tidak ada di daftar induk. Pilih 'Lainnya' untuk menambahkannya.")
            else:
                galat.append(f"Masjid '{masjid_in}' ada di beberapa kota ({', '.join(m['kota'] for m in cand)}); pilih yang memuat nama kota.")
        else:
            a = aman(bersihkan, mb.get("alamat"), "Alamat masjid baru", BATAS["alamat"], True)
            k = aman(bersihkan, mb.get("kota"), "Kota masjid baru", BATAS["kota"], True)
            if a and k:
                kota = ONLINE if kunci(k) == kunci(ONLINE) else (cocok(k, kat["kota"]) or rapikan_huruf(k))
                nama = bersihkan_nama_masjid(masjid_in, kota)
                if placeholder(nama):
                    galat.append(f"Masjid: '{masjid_in}' bukan nama. Isi nama masjid atau penyelenggara yang sebenarnya.")
                else:
                    aman(bermakna, re.sub(r"\s*\(online\)\s*$", "", nama, flags=re.I), "Nama masjid baru", True)
                if kota != ONLINE and not cocok(kota, kat["kota"]):
                    aman(bermakna, kota, "Kota masjid baru")
                if nama != masjid_in:
                    peringatan.append(f"Nama masjid dirapikan: '{masjid_in}' menjadi '{nama}' (kota dicatat terpisah: {kota}).")
                ada = [m for m in kat["masjid"] if kunci(m["nama"]) == kunci(nama) and kunci(m["kota"]) == kunci(kota)]
                if ada:
                    entri = ada[0]
                    if kunci(a) != kunci(entri["alamat"]):
                        peringatan.append(f"Masjid '{label_masjid(entri)}' sudah ada; alamat dari daftar induk dipakai, isian baru diabaikan.")
                else:
                    bentrok = [m for m in kat["masjid"] if kunci(m["nama"]) == kunci(nama)]
                    tampil = f"{nama} ({kota})" if bentrok else nama
                    if bentrok:
                        peringatan.append(f"Nama '{nama}' sudah dipakai masjid di {', '.join(m['kota'] for m in bentrok)}; masjid baru ditulis '{tampil}' agar filter tidak tertukar.")
                    for m in mirip(nama, [x["nama"] for x in kat["masjid"]])[:3]:
                        kemiripan(f"Masjid baru '{nama}' mirip dengan yang sudah ada: '{m}'.")
                    entri = {"nama": nama, "kota": kota, "alamat": a, "tampil": tampil}
                    baru["masjid"].append(entri)
                    if kota != ONLINE and kota not in kat["kota"]:
                        baru["kota"].append(kota)
                        for m in mirip(kota, kat["kota"])[:3]:
                            kemiripan(f"Kota baru '{kota}' mirip dengan yang sudah ada: '{m}'.")

    if perempuan:
        if audience == "Khusus Ikhwan":
            galat.append("Audience: pemateri perempuan tidak cocok dengan Khusus Ikhwan.")
        elif audience != "Khusus Akhwat":
            if not paket.get("pemateri_perempuan"):
                peringatan.append("Pemateri perempuan terdeteksi (Ustadzah); Audience otomatis 'Khusus Akhwat'.")
            audience = "Khusus Akhwat"

    if galat:
        raise InputError(galat)

    ke_depan, lampau = tanggal
    label, order, pw = waktu
    if pw:
        peringatan.append(pw)

    masjid, area, alamat = entri["tampil"], entri["kota"], entri["alamat"]
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
    """Masukkan kota/masjid/pemateri/alias baru ke daftar induk (hanya bila ada event baru)."""
    if not hasil["events"]:
        return
    for k in hasil["baru"]["kota"]:
        if k not in kat["kota"]:
            kat["kota"].append(k)
    kat["masjid"].extend(hasil["baru"]["masjid"])
    kat["pemateri"].extend(hasil["baru"]["pemateri"])
    for nama, alias in hasil["baru"]["alias"]:
        for p in kat["pemateri"]:
            if p["nama"] == nama and alias not in p["alias"] and kunci(alias) != kunci(p["tampil"]):
                p["alias"].append(alias)


# ---------- penulisan ke index.html ----------

def baris_event(ev, id_):
    pasangan = [("id", id_)] + [(k, ev[k]) for k in KUNCI_EVENT[1:]]
    return "  {" + ",".join(f"{k}:{json.dumps(v, ensure_ascii=False)}" for k, v in pasangan) + "},"


def id_tertinggi(html, kat=None):
    """Id tertinggi yang pernah dipakai: dari index.html, `id_tertinggi` di master, dan semua id di `diproses`
    (event yang dihapus atau di-prune tidak boleh membuat id dipakai ulang, supaya Target #N tidak salah sasaran)."""
    ids = [int(i) for i in re.findall(r"\{id:(\d+),date:", html)]
    if kat is not None:
        ids.append(int(kat.get("id_tertinggi") or 0))
        for d in kat.get("diproses", []):
            ids += [int(i) for i in d.get("id", [])]
    return max(ids) if ids else 0


def id_berikutnya(html, kat=None):
    return id_tertinggi(html, kat) + 1


def sisipkan(html, baris):
    cocokan = [m for m in re.finditer(r"^ *\{id:\d+,date:.*\},\s*$", html, re.M)]
    if not cocokan:
        raise RuntimeError("Tidak ada baris event di index.html; tidak bisa menyisipkan.")
    akhir = cocokan[-1].end()
    return html[:akhir] + "\n" + "\n".join(baris) + html[akhir:]


def events_dari_html(html):
    return build.parse_events(html)


def sinkronkan_master(html, kat):
    """Samakan master (kategori.json) dengan event di index.html. Idempoten dan hanya MENAMBAH: entri master yang
    tidak dipakai event tidak pernah dihapus. kat diubah di tempat.
    -> {"kota": [...], "masjid": [...], "pemateri": [...], "peringatan": [...]}  (yang baru ditambahkan)
    Event yang tidak bisa diurai menghasilkan peringatan, bukan galat."""
    baru = {"kota": [], "masjid": [], "pemateri": [], "peringatan": []}
    try:
        events = events_dari_html(html)
    except Exception as e:  # noqa: BLE001
        baru["peringatan"].append(f"index.html tidak bisa dibaca untuk sinkronisasi master ({type(e).__name__}: {e})")
        return baru
    for e in events:
        try:
            eid = e.get("id")
            area = bersihkan(e.get("area"), "area")
            tampil = bersihkan(e.get("masjid"), "masjid")
            if not area or not tampil:
                baru["peringatan"].append(f"event id {eid}: masjid atau kota kosong; dilewati.")
                continue
            ada_kota = {kunci(k) for k in kat["kota"]} | {kunci(k) for k in kat.get("kota_khusus", [ONLINE])}
            if kunci(area) not in ada_kota:
                kat["kota"].append(area)
                baru["kota"].append(area)
            if not any(kunci(m["tampil"]) == kunci(tampil) and kunci(m["kota"]) == kunci(area) for m in kat["masjid"]):
                nama = tampil
                akhiran = f" ({area})"
                if kunci(nama).endswith(kunci(akhiran)):
                    nama = nama[:-len(akhiran)].rstrip()
                if any(kunci(m["nama"]) == kunci(nama) and kunci(m["kota"]) == kunci(area) for m in kat["masjid"]):
                    baru["peringatan"].append(
                        f"event id {eid}: masjid '{tampil}' ({area}) mirip entri master yang ada (nama+kota sama, tampil berbeda); tidak ditambahkan.")
                else:
                    ent = {"nama": nama, "kota": area, "alamat": bersihkan(e.get("address"), "alamat"), "tampil": tampil}
                    kat["masjid"].append(ent)
                    baru["masjid"].append(ent)
            ustadz = bersihkan(e.get("ustadz"), "pemateri")
            if ustadz and kunci(ustadz) != kunci(BELUM_DITENTUKAN) and not cari_pemateri(kat, ustadz):
                nama = nama_bersih(ustadz)
                if not nama:
                    baru["peringatan"].append(f"event id {eid}: pemateri '{ustadz}' tidak punya nama bersih; dilewati.")
                else:
                    ent = {"nama": nama, "tampil": ustadz, "alias": []}
                    if pemateri_perempuan(ustadz):
                        ent["perempuan"] = True
                    kat["pemateri"].append(ent)
                    baru["pemateri"].append(ent)
        except Exception as ex:  # noqa: BLE001
            baru["peringatan"].append(f"event id {e.get('id')}: tidak bisa disinkronkan ({type(ex).__name__}: {ex}).")
    return baru


def ringkas_sinkron(baru):
    """Teks satu baris untuk log/pesan komit; kosong bila tidak ada tambahan."""
    bagian = [f"+{len(baru[k])} {k}" for k in ("kota", "masjid", "pemateri") if baru[k]]
    return ", ".join(bagian)


def sekarang_wib():
    return datetime.now(TZ).date()
