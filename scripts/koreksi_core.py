#!/usr/bin/env python3
"""
Koreksi dan hapus event (tahap 2 sistem input Issue).

Inti operasi, tidak tahu apa-apa soal formulir (adapternya: adapter_koreksi_form.py).
Event dirujuk lewat id; satu Issue "Tambah kajian" dapat dirujuk sekaligus lewat #NomorIssue
(semua event yang masih ada dari Issue itu, berdasarkan data/kategori.json "diproses").

Aman-secara-rancangan:
  - semua-atau-tidak-sama-sekali: satu id tak ditemukan / satu event gagal validasi -> tidak ada
    yang berubah;
  - koreksi memakai ulang validasi inti Tambah (ingest_core.bangun_event), jadi aturan dumb-proof
    yang sama berlaku (nama pengganti, kemiripan, jam, pemateri perempuan, dst.);
  - kolom yang tidak diubah dipertahankan apa adanya (bukan dihitung ulang);
  - hasil koreksi yang sama dengan event lain ditolak (duplikat).
"""

import copy
import re

from ingest_core import (JAM_EKSAK, KUNCI_EVENT, MAKS_TANGGAL, WAKTU_SALAT, InputError, bangun_event,
                         baris_event, terapkan_kategori)

BELUM = "Belum ditentukan"
LABEL_KOLOM = [("date", "tanggal"), ("title", "judul"), ("timeLabel", "waktu"), ("ustadz", "pemateri"),
               ("masjid", "masjid"), ("area", "kota"), ("address", "alamat"), ("audience", "audience"),
               ("isRutin", "kajian rutin"), ("note", "catatan")]


# ---------- target ----------

def parse_target(teks, kat, events):
    """'#12', '747', '747-750', '#12, 760' -> daftar id unik (berurutan). Semua id harus ada."""
    t = re.sub(r"\s+", " ", str(teks or "")).strip().lower()
    if not t:
        raise InputError("Target: wajib diisi (mis. #12 untuk semua event dari Issue 12, atau 747-750).")
    ada = {e["id"] for e in events}
    ids, galat = [], []
    for tok in [x.strip() for x in re.split(r"[;,]", t) if x.strip()]:
        m = re.fullmatch(r"(?:#|issue\s*#?|isu\s*#?)\s*(\d+)", tok)
        if m:
            n = int(m.group(1))
            entri = [d for d in kat["diproses"] if d["issue"] == n and not d.get("aksi")]
            if not entri:
                galat.append(f"Target: Issue #{n} tidak ditemukan sebagai Issue 'Tambah kajian' yang sudah diproses.")
                continue
            sisa = [i for i in entri[0]["id"] if i in ada]
            if not sisa:
                galat.append(f"Target: semua event dari Issue #{n} sudah tidak ada (dihapus, atau sudah lewat lalu dihapus otomatis).")
                continue
            ids += sisa
            continue
        m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", tok)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if b < a or b - a + 1 > MAKS_TANGGAL:
                galat.append(f"Target: rentang id '{tok}' tidak sah (urutan terbalik atau lebih dari {MAKS_TANGGAL} id).")
                continue
            ids += list(range(a, b + 1))
        elif tok.isdigit():
            ids.append(int(tok))
        else:
            galat.append(f"Target: '{tok}' tidak dikenali. Tulis #NomorIssue (semua event dari Issue itu) atau id event "
                         "(747, 747-750). Id event ada di komentar Issue 'Tambah kajian'.")
    if galat:
        raise InputError(galat)
    unik = list(dict.fromkeys(ids))
    hilang = [i for i in unik if i not in ada]
    if hilang:
        raise InputError(f"Target: id {', '.join(map(str, hilang))} tidak ditemukan (salah ketik, atau event sudah lewat lalu "
                         "dihapus otomatis). Tidak ada yang diubah.")
    if len(unik) > MAKS_TANGGAL:
        raise InputError(f"Target: {len(unik)} event melebihi batas {MAKS_TANGGAL} per Issue. Pecah menjadi beberapa Issue.")
    return unik


# ---------- penyuntingan index.html ----------

def hapus_baris(html, ids):
    ids = set(ids)
    keluar = []
    for baris in html.split("\n"):
        m = re.match(r"^\s*\{id:(\d+),date:", baris)
        if m and int(m.group(1)) in ids:
            continue
        keluar.append(baris)
    return "\n".join(keluar)


def ganti_baris(html, id_, ev):
    pola = re.compile(r"^ *\{id:" + str(int(id_)) + r",date:.*\},\s*$", re.M)
    hasil, n = pola.subn(lambda _m: baris_event(ev, id_), html)
    if n != 1:
        raise RuntimeError(f"Baris event id {id_} ditemukan {n} kali; koreksi dibatalkan.")
    return hasil


# ---------- koreksi ----------

def _jenis_jam(e):
    tl = e["timeLabel"]
    if tl in WAKTU_SALAT:
        return tl, ""
    return JAM_EKSAK, tl.replace(" WIB", "").replace(" – ", "-").strip()


def _tampil(k, nilai):
    if k == "isRutin":
        return "ya" if nilai else "tidak"
    return str(nilai)


def proses_koreksi(p, kat, events, hari_ini):
    """p: {"ids": [...], "perubahan": {...}, "abaikan_mirip": bool}. perubahan boleh berisi:
    judul, tanggal (ISO), jenis_waktu, jam, pemateri, masjid, masjid_kota, masjid_baru, audience,
    rutin (bool), catatan. Mengembalikan {"ganti": {id: event_baru}, "perbedaan": [...],
    "baru": {...}, "peringatan": [...], "kat_kerja": kat_baru}. Tidak mengubah kat/events."""
    perub = p["perubahan"]
    if not perub:
        raise InputError("Koreksi: tidak ada kolom yang diubah. Isi minimal satu kolom koreksi.")
    ids = set(p["ids"])
    sasaran = [e for e in events if e["id"] in ids]
    if "tanggal" in perub and len(sasaran) > 1:
        raise InputError(f"Tanggal (koreksi): tanggal baru hanya untuk satu event, sedangkan target memuat {len(sasaran)}. "
                         "Koreksi tanggal satu per satu (id tunggal).")

    kerja = copy.deepcopy(kat)
    lain = [e for e in events if e["id"] not in ids]
    baru_total = {"kota": [], "masjid": [], "pemateri": [], "alias": []}
    ganti, perbedaan, peringatan, galat = {}, [], [], []
    waktu_diubah = "jenis_waktu" in perub or "jam" in perub
    masjid_diubah = "masjid" in perub

    for e in sasaran:
        jenis0, _jam0 = _jenis_jam(e)
        if waktu_diubah:
            jenis = perub.get("jenis_waktu") or (JAM_EKSAK if jenis0 == JAM_EKSAK else None)
            if jenis is None:
                galat.append(f"id {e['id']}: waktunya '{e['timeLabel']}' (waktu salat). Untuk memberi jam, pilih Jenis waktu (koreksi) = 'Jam eksak'.")
                continue
            jam = perub.get("jam", "")
        else:
            jenis, jam = "Ba'da Maghrib", ""  # pengisi netral; hasilnya dibuang
        if masjid_diubah:
            masjid, masjid_kota, masjid_baru = perub["masjid"], perub.get("masjid_kota", ""), perub.get("masjid_baru")
        else:
            ent = next((m for m in kerja["masjid"] if m["tampil"] == e["masjid"]), None) or kerja["masjid"][0]
            masjid, masjid_kota, masjid_baru = ent["nama"], ent["kota"], None  # pengisi netral; hasilnya dibuang
        paket = {
            "tanggal": [perub.get("tanggal") or e["date"]], "jenis_waktu": jenis, "jam": jam,
            "judul": perub.get("judul", "x"), "pemateri": perub.get("pemateri", BELUM), "pemateri_perempuan": False,
            "masjid": masjid, "masjid_kota": masjid_kota, "masjid_baru": masjid_baru,
            "audience": perub.get("audience", e["audience"]), "rutin": e["isRutin"],
            "catatan": perub.get("catatan", ""), "abaikan_mirip": p.get("abaikan_mirip", False),
        }
        try:
            hasil = bangun_event(paket, kerja, hari_ini, lain)
        except InputError as ex:
            galat.extend(f"id {e['id']}: {m}" for m in ex.pesan)
            continue
        if not hasil["events"]:
            galat.append(f"id {e['id']}: hasil koreksi sama dengan event lain yang sudah ada (duplikat). Tidak diterapkan.")
            continue
        ev = hasil["events"][0]
        akhir = dict(e)
        if "judul" in perub:
            akhir["title"] = ev["title"]
        if "tanggal" in perub:
            akhir["date"], akhir["dayShort"] = ev["date"], ev["dayShort"]
        if waktu_diubah:
            akhir["timeLabel"], akhir["timeOrder"] = ev["timeLabel"], ev["timeOrder"]
        if "pemateri" in perub:
            akhir["ustadz"] = ev["ustadz"]
        if masjid_diubah:
            akhir["masjid"], akhir["area"], akhir["address"] = ev["masjid"], ev["area"], ev["address"]
        if "audience" in perub or "pemateri" in perub:
            akhir["audience"] = ev["audience"]
        if "rutin" in perub:
            akhir["isRutin"] = bool(perub["rutin"])
        if "catatan" in perub:
            akhir["note"] = ev["note"]
        terapkan_kategori(kerja, hasil)
        for kunci_baru in ("kota", "masjid", "pemateri", "alias"):
            baru_total[kunci_baru] += hasil["baru"][kunci_baru]
        peringatan += [f"id {e['id']}: {w}" for w in hasil["peringatan"]]
        lain.append({**akhir})
        ganti[e["id"]] = akhir
        for k, nama in LABEL_KOLOM:
            if akhir.get(k) != e.get(k):
                perbedaan.append((e["id"], nama, _tampil(k, e.get(k)), _tampil(k, akhir.get(k))))
    if galat:
        raise InputError(galat)
    if not perbedaan:
        raise InputError("Koreksi: isian sama dengan data sekarang; tidak ada yang berubah.")
    return {"ganti": ganti, "perbedaan": perbedaan, "baru": baru_total,
            "peringatan": list(dict.fromkeys(peringatan)), "kat_kerja": kerja}
