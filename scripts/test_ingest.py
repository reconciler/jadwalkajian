#!/usr/bin/env python3
"""Uji lokal ingest (tanpa jaringan, tanpa menyentuh repo asli): python3 scripts/test_ingest.py"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import adapter_issue_form as ad  # noqa: E402
import build  # noqa: E402
import ingest  # noqa: E402
import ingest_core as core  # noqa: E402

TODAY = "2026-10-03"
LULUS = []


def siapkan():
    d = Path(tempfile.mkdtemp())
    shutil.copy(REPO / "index.html", d / "index.html")
    (d / "data").mkdir()
    shutil.copy(REPO / "data" / "kategori.json", d / "data" / "kategori.json")
    shutil.copytree(HERE, d / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    return d


def form(**k):
    """Isi Issue seperti yang dibuat GitHub dari formulir."""
    v = {"Tanggal": "2026-10-10", "Jenis waktu": "Ba'da Maghrib", "Jam": "", "Judul": "Kajian Uji",
         "Pemateri": "Belum ditentukan", "Pemateri baru": "", "Pemateri perempuan": "", "Masjid": "Masjid Al-Adhim (Depok)",
         "Nama masjid baru": "", "Alamat masjid baru": "", "Kota masjid baru": "", "Kota lain": "",
         "Audience": "Terbuka untuk umum", "Kajian rutin": "", "Catatan": ""}
    v.update({kk.replace("_", " "): vv for kk, vv in k.items()})
    out = []
    for lab in [ad.LABEL[x] for x in ad.LABEL]:
        val = v.get(lab, "")
        out.append(f"### {lab}\n\n{val if val else '_No response_'}\n")
    return "\n".join(out)


def jalankan(d, issues, edited=None, today=TODAY):
    (d / "issues.json").write_text(json.dumps(issues), encoding="utf-8")
    argv = ["--issues", str(d / "issues.json"), "--out", str(d / "out.json"),
            "--commit-msg", str(d / "msg.txt"), "--root", str(d), "--today", today]
    if edited:
        argv += ["--edited", str(edited)]
    ingest.main(argv)
    return json.loads((d / "out.json").read_text(encoding="utf-8"))["hasil"]


def iss(n, body, login="reconciler", title="Tambah kajian: uji"):
    return {"number": n, "title": title, "body": body, "login": login}


def events(d):
    return build.parse_events((d / "index.html").read_text(encoding="utf-8"))


def kat(d):
    return json.loads((d / "data" / "kategori.json").read_text(encoding="utf-8"))


def uji(nama):
    def deko(f):
        def w():
            f()
            LULUS.append(nama)
            print("lulus:", nama)
        w.__name__ = f.__name__
        UJI.append(w)
        return w
    return deko


UJI = []


@uji("sukses satu tanggal, jam eksak, pemateri ber-koma, rutin")
def _():
    d = siapkan(); k = kat(d)
    pem = next(p for p in k["pemateri"] if "," in p["tampil"])
    n0 = len(events(d)); id0 = core.id_berikutnya((d / "index.html").read_text(encoding="utf-8"))
    h = jalankan(d, [iss(1, form(Jenis_waktu="Jam eksak", Jam="19.30", Pemateri=pem["nama"], Kajian_rutin=ad.RUTIN_YA, Catatan="Catatan uji"))])
    assert h[0]["status"] == "ok", h
    ev = events(d)
    assert len(ev) == n0 + 1
    e = ev[-1]
    assert e["id"] == id0 and e["date"] == "2026-10-10" and e["dayShort"] == "Sab 10 Okt", e
    assert e["timeLabel"] == "19.30 WIB" and e["timeOrder"] == 19.5 and e["ustadz"] == pem["tampil"] and e["isRutin"] is True
    assert e["area"] == "Depok" and e["masjid"] == "Masjid Al-Adhim" and e["audience"] == "Terbuka untuk umum"
    assert any(x["issue"] == 1 and x["id"] == [id0] for x in kat(d)["diproses"])


@uji("banyak tanggal, Minggu = Min, rentang jam en-dash")
def _():
    d = siapkan(); id0 = core.id_berikutnya((d / "index.html").read_text(encoding="utf-8"))
    h = jalankan(d, [iss(2, form(Tanggal="2026-10-10\n2026-10-11\n2026-10-12", Jenis_waktu="Jam eksak", Jam="09.30-11.00"))])
    assert h[0]["id"] == [id0, id0 + 1, id0 + 2]
    e = events(d)[-3:]
    assert [x["dayShort"] for x in e] == ["Sab 10 Okt", "Min 11 Okt", "Sen 12 Okt"]
    assert e[0]["timeLabel"] == "09.30 – 11.00 WIB" and e[0]["timeOrder"] == 9.5


@uji("waktu salat memberi timeOrder baku")
def _():
    d = siapkan()
    for i, (j, o) in enumerate([("Dhuha", 9), ("Ba'da Subuh", 4.5), ("Ba'da Zuhur", 12.5), ("Ba'da Ashar", 15.5), ("Ba'da Maghrib", 18)]):
        jalankan(d, [iss(10 + i, form(Judul=f"W{i}", Jenis_waktu=j))])
        e = events(d)[-1]
        assert e["timeLabel"] == j and e["timeOrder"] == o, (j, e)


@uji("Online: penyelenggara, kota Online tidak masuk daftar kota")
def _():
    d = siapkan()
    h = jalankan(d, [iss(3, form(Masjid="Online", Nama_masjid_baru="MTI Contoh"))])
    assert h[0]["status"] == "ok", h
    e = events(d)[-1]
    assert e["masjid"] == "MTI Contoh (Online)" and e["area"] == "Online" and e["address"] == "Online (MTI Contoh)"
    assert "Online" not in kat(d)["kota"]


@uji("masjid dan kota baru masuk daftar induk dan templat")
def _():
    d = siapkan()
    h = jalankan(d, [iss(4, form(Masjid=ad.LAINNYA, Nama_masjid_baru="Masjid Uji Baru", Alamat_masjid_baru="Jl. Uji 1", Kota_masjid_baru=ad.KOTA_LAIN, Kota_lain="semarang", Pemateri=ad.LAINNYA, Pemateri_baru="Ustadz Uji Baru"))])
    assert h[0]["status"] == "ok", h
    e = events(d)[-1]
    assert e["masjid"] == "Masjid Uji Baru" and e["area"] == "Semarang" and e["address"] == "Jl. Uji 1" and e["ustadz"] == "Ustadz Uji Baru"
    k = kat(d)
    assert "Semarang" in k["kota"] and {"nama": "Masjid Uji Baru", "kota": "Semarang", "alamat": "Jl. Uji 1", "tampil": "Masjid Uji Baru"} in k["masjid"]
    assert {"nama": "Uji Baru", "tampil": "Ustadz Uji Baru", "alias": []} in k["pemateri"]
    tpl = (d / ".github/ISSUE_TEMPLATE/tambah-kajian.yml").read_text(encoding="utf-8")
    assert "Masjid Uji Baru (Semarang)" in tpl and "Semarang" in tpl and '"Uji Baru"' in tpl and "Ustadz Uji Baru" not in tpl


@uji("masjid: nama+kota sama (huruf beda) memakai yang lama; nama mirip diberi peringatan")
def _():
    d = siapkan(); m0 = kat(d)["masjid"][0]
    n0 = len(kat(d)["masjid"])
    h = jalankan(d, [iss(5, form(Masjid=ad.LAINNYA, Nama_masjid_baru=m0["nama"].upper(), Alamat_masjid_baru="x", Kota_masjid_baru=m0["kota"]))])
    assert events(d)[-1]["masjid"] == m0["tampil"] and len(kat(d)["masjid"]) == n0, h
    h = jalankan(d, [iss(6, form(Masjid=ad.LAINNYA, Nama_masjid_baru=m0["nama"] + "a", Alamat_masjid_baru="x", Kota_masjid_baru=m0["kota"]))])
    assert "mirip" in h[0]["komentar"], h[0]["komentar"]


@uji("masjid: kota di belakang nama dibuang; nama sama di kota lain diberi (Kota); dipilih lewat label Nama (Kota)")
def _():
    d = siapkan()
    h = jalankan(d, [iss(80, form(Masjid=ad.LAINNYA, Nama_masjid_baru="Masjid Contoh Baru Depok", Alamat_masjid_baru="Jl. C 1", Kota_masjid_baru="Depok"))])
    assert events(d)[-1]["masjid"] == "Masjid Contoh Baru" and "dirapikan" in h[0]["komentar"], h[0]["komentar"]
    h = jalankan(d, [iss(81, form(Masjid=ad.LAINNYA, Nama_masjid_baru="Masjid Contoh Baru", Alamat_masjid_baru="Jl. C 2", Kota_masjid_baru=ad.KOTA_LAIN, Kota_lain="Bandung"))])
    assert events(d)[-1]["masjid"] == "Masjid Contoh Baru (Bandung)" and events(d)[-1]["area"] == "Bandung" and "sudah dipakai" in h[0]["komentar"]
    h = jalankan(d, [iss(82, form(Masjid="Masjid Contoh Baru (Bandung)"))])
    assert events(d)[-1]["masjid"] == "Masjid Contoh Baru (Bandung)" and events(d)[-1]["address"] == "Jl. C 2"
    h = jalankan(d, [iss(83, form(Masjid="Masjid Contoh Baru (Depok)", Judul="Kajian Depok"))])
    assert events(d)[-1]["masjid"] == "Masjid Contoh Baru" and events(d)[-1]["address"] == "Jl. C 1"
    h = jalankan(d, [iss(84, form(Masjid="Masjid Contoh Baru"))])  # label usang/ambigu ditolak
    assert h[0]["status"] == "gagal" and "beberapa kota" in h[0]["komentar"], h[0]["komentar"]


@uji("pemateri: dropdown nama bersih -> nama lengkap; ketik dengan gelar dicocokkan otomatis; organisasi boleh")
def _():
    import json as _j
    d = siapkan(); k = kat(d); npem = len(k["pemateri"])
    p = next(x for x in k["pemateri"] if x["nama"] == "Abu Hurairah")
    jalankan(d, [iss(90, form(Pemateri="Abu Hurairah"))])
    assert events(d)[-1]["ustadz"] == p["tampil"]
    h = jalankan(d, [iss(91, form(Judul="Judul 91", Pemateri=ad.LAINNYA, Pemateri_baru="Ustadz Dr. Abu Hurairah, M.A."))])
    assert h[0]["status"] == "ok" and events(d)[-1]["ustadz"] == p["tampil"] and "dicocokkan otomatis" in h[0]["komentar"], h[0]["komentar"]
    k = kat(d); assert len(k["pemateri"]) == npem and "Ustadz Dr. Abu Hurairah, M.A." in next(x for x in k["pemateri"] if x["nama"] == "Abu Hurairah")["alias"]
    h = jalankan(d, [iss(92, form(Judul="Judul 92", Pemateri=ad.LAINNYA, Pemateri_baru="Komunitas Kajian Contoh"))])
    k = kat(d); assert events(d)[-1]["ustadz"] == "Komunitas Kajian Contoh" and {"nama": "Komunitas Kajian Contoh", "tampil": "Komunitas Kajian Contoh", "alias": []} in k["pemateri"]
    h = jalankan(d, [iss(93, form(Judul="Judul 93", Pemateri=ad.LAINNYA, Pemateri_baru="Ust. Fulan bin Contoh, Lc., M.A."))])
    assert {"nama": "Fulan bin Contoh", "tampil": "Ust. Fulan bin Contoh, Lc., M.A.", "alias": []} in kat(d)["pemateri"]


@uji("nama_bersih: sapaan dan gelar dibuang, majemuk apa adanya")
def _():
    kasus = {
        "Ustadz Dr. Ahmad Ba'mualim, Lc., M.Pd.": "Ahmad Ba'mualim", "Assoc. Prof. Dr. KH. Akhmad Alim, Lc., M.A.": "Akhmad Alim",
        "Dr. (HC) H. Sholeh Asri, M.A.": "Sholeh Asri", "DR. K.H. Amang Syafrudin, Lc., M.M": "Amang Syafrudin",
        "Drs. H.A. Dzulfatah Yasin, M.Ag.": "Dzulfatah Yasin", "Ustadz Mohamad Nursamsul Qamar Lc": "Mohamad Nursamsul Qamar",
        "Ustadzah Poppy Yuditya": "Poppy Yuditya", "Sheikh Assim Al Hakeem": "Assim Al Hakeem", "Muhammad Setiawan": "Muhammad Setiawan",
        "Emha Ainun Nadjib (Cak Nun) & Komunitas Kenduri Cinta": "Emha Ainun Nadjib (Cak Nun) & Komunitas Kenduri Cinta",
        "Kang Ghany & Zidny Hikmatiar": "Kang Ghany & Zidny Hikmatiar", "Haris Abu Naufal": "Haris Abu Naufal",
    }
    for a, b in kasus.items():
        assert core.nama_bersih(a) == b, (a, core.nama_bersih(a), b)
    assert core.bersihkan_nama_masjid("Masjid Ar-Riyadh Depok", "Depok") == "Masjid Ar-Riyadh"
    assert core.bersihkan_nama_masjid("Baitusyaakiriin Depok", "Depok") == "Baitusyaakiriin Depok"  # sisa 1 kata: dibiarkan
    assert core.bersihkan_nama_masjid("Masjid Jaza", "Bandung") == "Masjid Jaza"


@uji("integritas data nyata: setiap event punya masjid di daftar induk; Ar-Riyadh sudah diganti nama")
def _():
    k = core.muat_kategori(REPO / "data" / "kategori.json")
    tampil = {m["tampil"] for m in k["masjid"]}
    ev = build.parse_events((REPO / "index.html").read_text(encoding="utf-8"))
    hilang = sorted({e["masjid"] for e in ev if e["masjid"] not in tampil})
    assert not hilang, hilang
    assert not any(e["masjid"] == "Masjid Ar-Riyadh Depok" for e in ev)
    assert len({(m["nama"].casefold(), m["kota"].casefold()) for m in k["masjid"]}) == len(k["masjid"])
    assert len({m["tampil"].casefold() for m in k["masjid"]}) == len(k["masjid"])
    assert len({p["nama"].casefold() for p in k["pemateri"]}) == len(k["pemateri"])


@uji("perempuan => Khusus Akhwat; konflik dengan Ikhwan ditolak")
def _():
    d = siapkan()
    jalankan(d, [iss(7, form(Pemateri_perempuan="- [x] Pemateri perempuan (otomatis Khusus Akhwat)"))])
    assert events(d)[-1]["audience"] == "Khusus Akhwat"
    h = jalankan(d, [iss(8, form(Pemateri_perempuan="- [x] x", Audience="Khusus Ikhwan"))])
    assert h[0]["status"] == "gagal"


@uji("kegagalan: tanggal lampau, format, kolom bersyarat, karakter terlarang, panjang, struktur")
def _():
    d = siapkan(); n0 = len(events(d))
    kasus = [
        form(Tanggal="2026-10-02"), form(Tanggal="besok"), form(Tanggal="2026-02-30"), form(Tanggal="2031-01-01"),
        form(Jenis_waktu="Jam eksak"), form(Jenis_waktu="Jam eksak", Jam="25.00"), form(Jenis_waktu="Jam eksak", Jam="9"),
        form(Pemateri=ad.LAINNYA), form(Masjid=ad.LAINNYA), form(Masjid="Online"),
        form(Masjid=ad.LAINNYA, Nama_masjid_baru="X", Alamat_masjid_baru="Y", Kota_masjid_baru=ad.KOTA_LAIN),
        form(Judul="a</script><script>alert(1)"), form(Judul="x" * 201), form(Catatan="a > b"),
        "bukan dari formulir", "",
    ]
    h = jalankan(d, [iss(100 + i, b) for i, b in enumerate(kasus)])
    assert len(h) == len(kasus) and all(x["status"] == "gagal" for x in h), [(x["issue"], x["status"]) for x in h]
    assert len(events(d)) == n0, "tidak boleh ada event ditambahkan"
    assert len(kat(d)["gagal"]) == len(kasus)


@uji("input berbahaya: kutip, backslash, baris baru, kontrol aman; baris tetap valid untuk prune/build")
def _():
    d = siapkan()
    judul = 'Kutip "dua" \\ backslash\ttab'
    h = jalankan(d, [iss(20, form(Judul=judul, Catatan='baris1\nbaris2\x00\x1f "q" \\n'))])
    assert h[0]["status"] == "ok", h
    e = events(d)[-1]
    assert e["title"] == 'Kutip "dua" \\ backslash tab' and "\n" not in e["note"] and "\x00" not in e["note"], e
    baris = [l for l in (d / "index.html").read_text(encoding="utf-8").split("\n") if l.startswith(f"  {{id:{e['id']},")]
    assert len(baris) == 1 and re.match(r'^\s*\{id:\d+,date:"\d{4}-\d{2}-\d{2}"', baris[0]) and "</" not in baris[0]
    r = subprocess.run([sys.executable, str(d / "scripts" / "prune.py")], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"})
    assert r.returncode == 0, r.stderr
    r = subprocess.run([sys.executable, str(d / "scripts" / "build.py")], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"})
    assert r.returncode == 0, r.stderr
    assert "&quot;dua&quot;" in (d / "index.html").read_text(encoding="utf-8")


@uji("duplikat tidak membuat event ganda")
def _():
    d = siapkan()
    jalankan(d, [iss(30, form())]); n1 = len(events(d))
    h = jalankan(d, [iss(31, form())])
    assert h[0]["status"] == "ok" and len(events(d)) == n1 and h[0]["id"] == []


@uji("idempoten; gagal dilewati kecuali diedit; login lain dan judul lain diabaikan")
def _():
    d = siapkan()
    jalankan(d, [iss(40, form())]); n1 = len(events(d))
    assert jalankan(d, [iss(40, form())]) == [] and len(events(d)) == n1
    jalankan(d, [iss(41, form(Tanggal="2020-01-01"))])
    assert jalankan(d, [iss(41, form(Tanggal="2020-01-01"))]) == []
    h = jalankan(d, [iss(41, form(Tanggal="2026-11-01"))], edited=41)
    assert h and h[0]["status"] == "ok" and not [g for g in kat(d)["gagal"] if g["issue"] == 41]
    assert jalankan(d, [iss(42, form(), login="orang-lain")]) == []
    assert jalankan(d, [iss(43, "Hanya catatan biasa, bukan formulir.", title="Pertanyaan biasa")]) == []


@uji("id berlanjut dari max di main terbaru (simulasi konflik: ingest ulang di atas hasil lain)")
def _():
    a = siapkan(); b = siapkan()
    jalankan(a, [iss(50, form(Judul="A"))]); jalankan(b, [iss(51, form(Judul="B"))])
    assert events(a)[-1]["id"] == events(b)[-1]["id"]  # bentrok bila keduanya dipush
    shutil.copy(b / "index.html", a / "index.html"); shutil.copy(b / "data" / "kategori.json", a / "data" / "kategori.json")  # = reset ke main terbaru
    h = jalankan(a, [iss(50, form(Judul="A"))])
    ids = [e["id"] for e in events(a)]
    assert len(ids) == len(set(ids)) and h[0]["id"] == [events(a)[-1]["id"]]


@uji("templat YAML sah: 16 unsur, id unik, opsi dropdown unik tanpa koma ASCII, label = kunci parser")
def _():
    import yaml
    t = yaml.safe_load(ad.render_template(core.muat_kategori(REPO / "data" / "kategori.json")))
    assert t["title"] == ad.JUDUL_ISSUE and len(t["body"]) == 16
    assert next(x for x in t["body"] if x["id"] == "tanggal")["type"] == "input"
    rt = next(x for x in t["body"] if x["id"] == "rutin")
    assert rt["type"] == "dropdown" and rt["attributes"]["options"] == ad.OPSI_RUTIN and rt["attributes"]["default"] == 0
    assert not any("," in s for s in rt["attributes"]["options"])
    assert "kecuali" in next(x for x in t["body"] if x["id"] == "tanggal")["attributes"]["description"]
    ids = [x["id"] for x in t["body"]]; assert len(ids) == len(set(ids))
    assert [x["attributes"]["label"] for x in t["body"]] == [ad.LABEL[k] for k in ad.LABEL]
    for x in t["body"]:
        if x["type"] == "dropdown":
            o = x["attributes"]["options"]
            assert len(o) == len(set(o)) and not any("," in s for s in o), x["id"]
        if x["id"] == "pemateri":
            assert "Abu Hurairah" in x["attributes"]["options"] and not any(s.startswith(("Ustadz ", "Dr. ", "Ust. ")) for s in x["attributes"]["options"])
        if x["id"] == "masjid":
            assert "Masjid Al-Adhim (Depok)" in x["attributes"]["options"]


@uji("tanggal bebas: berbagai format, filter hari, tahun dihilangkan, pemeriksa hari")
def _():
    import tanggal_bebas as tb
    H = core.date(2026, 10, 3)
    ok = {
        "10 Okt 2026": ["2026-10-10"], "10 okt": ["2026-10-10"], "10/10/2026": ["2026-10-10"], "10-10-2026": ["2026-10-10"],
        "sabtu 10 okt 2026": ["2026-10-10"], "10, 17, 24 Okt 2026": ["2026-10-10", "2026-10-17", "2026-10-24"],
        "3 Okt - 4 Okt 2026": ["2026-10-03", "2026-10-04"], "3 s/d 5 Okt 2026": ["2026-10-03", "2026-10-04", "2026-10-05"],
        "3-31 Okt 2026 Sabtu": ["2026-10-03", "2026-10-10", "2026-10-17", "2026-10-24", "2026-10-31"],
        "3-31 Okt 2026 setiap Sabtu & Ahad": [f"2026-10-{d:02d}" for d in (3, 4, 10, 11, 17, 18, 24, 25, 31)],
        "3-31 Okt 2026, Sab": ["2026-10-03", "2026-10-10", "2026-10-17", "2026-10-24", "2026-10-31"],
        "2026-10-10\n2026-10-11": ["2026-10-10", "2026-10-11"], "5 Jan": ["2027-01-05"],
        "28 Des 2026 - 3 Jan 2027": ["2026-12-28", "2026-12-29", "2026-12-30", "2026-12-31", "2027-01-01", "2027-01-02", "2027-01-03"],
        "Jum'at 2 Okt 2026": ["2026-10-02"], "10 Oktober 2026; 17 Oktober 2026": ["2026-10-10", "2026-10-17"],
    }
    for s, e in ok.items():
        assert tb.parse(s, H) == e, (s, tb.parse(s, H))
    for s in ["besok", "", "30 Feb 2026", "10 Foo 2026", "minggu 10 okt 2026", "31-3 Okt 2026", "Sabtu", "32 Okt 2026", "13/13/2026", "3-31 Okt 2026 Selasa 2027"]:
        try:
            tb.parse(s, H); raise AssertionError(f"harus gagal: {s!r}")
        except core.InputError:
            pass
    # ujung ke ujung: rentang + filter hari menjadi banyak event, komentar memuat nama hari
    d = siapkan()
    h = jalankan(d, [iss(70, form(Tanggal="3-31 Okt 2026 setiap Sabtu"))])
    assert h[0]["status"] == "ok" and len(h[0]["id"]) == 5 and "Sab 31 Okt (2026-10-31)" in h[0]["komentar"], h[0]["komentar"]


@uji("rutin: otomatis (rentang berfilter, 3 tanggal tiap 7 hari), bukan rutin (satu tanggal, acak), override Ya/Tidak")
def _():
    d = siapkan()
    kasus = [  # (Tanggal, pilihan rutin, harapan)
        ("3-31 Okt 2026 setiap Sabtu", "", True), ("3-31 Okt 2026 setiap Sabtu", ad.RUTIN_OTOMATIS, True),
        ("10 Okt 2026", "", False), ("3, 10, 17 Okt 2026", "", True), ("3, 11, 17 Okt 2026", "", False),
        ("3-5 Okt 2026", "", False), ("3-9 Okt 2026 Sabtu", "", False),
        ("3-31 Okt 2026 Sabtu kecuali 17 Okt", "", True),
        ("3-31 Okt 2026 Sabtu", ad.RUTIN_TIDAK, False), ("10 Okt 2026", ad.RUTIN_YA, True), ("3, 11, 17 Okt 2026", ad.RUTIN_YA, True),
    ]
    for i, (tg, pil, harap) in enumerate(kasus):
        h = jalankan(d, [iss(200 + i, form(Judul=f"Rutin {i}", Tanggal=tg, Kajian_rutin=pil))])
        assert h[0]["status"] == "ok", (tg, h)
        ev = [e for e in events(d) if e["title"] == f"Rutin {i}"]
        assert ev and all(e["isRutin"] is harap for e in ev), (tg, pil, harap, [e["isRutin"] for e in ev])
    assert "otomatis" in jalankan(d, [iss(300, form(Judul="K", Tanggal="3-31 Okt 2026 Sabtu"))])[0]["komentar"]


@uji("pola: lintas bulan dan tahun, dua hari, kecuali valid/di luar pola/menghabiskan semua, komentar lengkap")
def _():
    d = siapkan()
    h = jalankan(d, [iss(210, form(Judul="Lintas", Tanggal="28 Des 2026 - 16 Jan 2027 setiap Sabtu & Ahad"))])
    tg = sorted(e["date"] for e in events(d) if e["title"] == "Lintas")
    assert tg == ["2027-01-02", "2027-01-03", "2027-01-09", "2027-01-10", "2027-01-16"], tg  # lintas tahun, hanya Sab & Min
    k = h[0]["komentar"]
    assert "Pola terbaca" in k and "Jumlah event ditambahkan: 5" in k and "hanya hari Sab & Min" in k, k
    h = jalankan(d, [iss(211, form(Judul="Kec", Tanggal="3-31 Okt 2026 setiap Sabtu kecuali 17, 24 Okt"))])
    assert [e["date"] for e in events(d) if e["title"] == "Kec"] == ["2026-10-03", "2026-10-10", "2026-10-31"]
    assert "Dikecualikan" in h[0]["komentar"] and "Jumlah event ditambahkan: 3" in h[0]["komentar"]
    h = jalankan(d, [iss(212, form(Judul="Kec2", Tanggal="3-31 Okt 2026 setiap Sabtu kecuali 17 Okt, 20 Okt"))])
    assert "bukan bagian pola" in h[0]["komentar"] and len([e for e in events(d) if e["title"] == "Kec2"]) == 4
    h = jalankan(d, [iss(213, form(Judul="Kec3", Tanggal="3-31 Okt 2026 setiap Sabtu kecuali 3, 10, 17, 24, 31 Okt"))])
    assert h[0]["status"] == "gagal" and "dikecualikan" in h[0]["komentar"]
    assert not [e for e in events(d) if e["title"] == "Kec3"]


@uji("batas 60 event per Issue: tepat 60 lolos, 61 ditolak sebelum menulis apa pun, pesan menyebut jumlah")
def _():
    d = siapkan(); n0 = len(events(d))
    h = jalankan(d, [iss(220, form(Judul="Enam puluh", Tanggal="1 Nov - 30 Des 2026"))])
    assert h[0]["status"] == "ok" and len(h[0]["id"]) == 60 and len(events(d)) == n0 + 60
    h = jalankan(d, [iss(221, form(Judul="Enam puluh satu", Tanggal="1 Nov - 31 Des 2026"))])
    assert h[0]["status"] == "gagal" and "61 tanggal" in h[0]["komentar"] and "Persempit" in h[0]["komentar"], h[0]["komentar"]
    h = jalankan(d, [iss(222, form(Judul="Setahun", Tanggal="1 Jan - 31 Des 2027"))])
    assert h[0]["status"] == "gagal" and "365 tanggal" in h[0]["komentar"]
    assert len(events(d)) == n0 + 60


@uji("pola tak didukung ditolak dengan saran daftar tanggal: tiap 2 minggu, pekan ke-N, bulanan, setiap minggu")
def _():
    d = siapkan(); n0 = len(events(d))
    for i, tg in enumerate(["tiap 2 minggu 3-31 Okt 2026", "3-31 Okt 2026 setiap 2 pekan", "minggu ke-2 Okt 2026", "pekan ketiga 2026",
                            "setiap bulan 10 Okt 2026", "10 Okt 2026 bulanan", "3-31 Okt 2026 setiap minggu"]):
        h = jalankan(d, [iss(230 + i, form(Judul=f"T{i}", Tanggal=tg))])
        assert h[0]["status"] == "gagal", tg
        assert ("daftar tanggal" in h[0]["komentar"]) or ("Sebut hari" in h[0]["komentar"]), (tg, h[0]["komentar"])
    assert len(events(d)) == n0


@uji("diproses menyimpan nomor Issue -> daftar id event; end-to-end pola mingguan lolos prune dan build")
def _():
    d = siapkan()
    h = jalankan(d, [iss(240, form(Judul="Mingguan uji", Tanggal="3-31 Okt 2026 setiap Sabtu kecuali 17 Okt"))])
    ids = h[0]["id"]
    assert len(ids) == 4 and {"issue": 240, "id": ids} in kat(d)["diproses"]
    assert sorted(e["id"] for e in events(d) if e["title"] == "Mingguan uji") == ids
    env = {"PATH": "/usr/bin:/bin"}
    for s in ("prune.py", "build.py"):
        r = subprocess.run([sys.executable, str(d / "scripts" / s)], capture_output=True, text=True, env=env)
        assert r.returncode == 0, r.stderr
    assert len([e for e in events(d) if e["title"] == "Mingguan uji"]) == 4


@uji("dumb-proof: isian bertentangan ditolak (Jam vs jenis waktu, jam terbalik, kolom baru vs dropdown), tidak ada event tertulis")
def _():
    d = siapkan(); n0 = len(events(d))
    kasus = [
        ("Jam diisi tapi Jenis waktu bukan Jam eksak", dict(Jenis_waktu="Ba'da Maghrib", Jam="10.00"), "bukan Jam eksak"),
        ("jam selesai sebelum mulai", dict(Jenis_waktu="Jam eksak", Jam="18.00-09.00"), "jam selesai harus setelah"),
        ("jam selesai sama dengan mulai", dict(Jenis_waktu="Jam eksak", Jam="09.00-09.00"), "jam selesai harus setelah"),
        ("Pemateri baru terisi tanpa Lainnya", dict(Pemateri="Belum ditentukan", Pemateri_baru="Ustadz Penting, Lc."), "Pemateri baru: terisi"),
        ("kolom masjid baru terisi, masjid dari daftar", dict(Masjid="Masjid Al-Adhim (Depok)", Nama_masjid_baru="Masjid Lain", Alamat_masjid_baru="Jl X"), "dipilih dari daftar"),
        ("Kota lain terisi, masjid dari daftar", dict(Masjid="Masjid Al-Adhim (Depok)", Kota_lain="Bogor"), "dipilih dari daftar"),
        ("Online dengan alamat terisi", dict(Masjid="Online", Nama_masjid_baru="Penyelenggara X", Alamat_masjid_baru="Jl X"), "Online tidak memakai"),
        ("Kota lain terisi padahal kota dipilih dari daftar", dict(Masjid=ad.LAINNYA, Nama_masjid_baru="Masjid Contoh", Alamat_masjid_baru="Jl C", Kota_masjid_baru="Depok", Kota_lain="Bogor"), "Kota lain: terisi"),
    ]
    for i, (nama, k, harap) in enumerate(kasus):
        h = jalankan(d, [iss(400 + i, form(Judul=f"DP{i}", **k))])
        assert h[0]["status"] == "gagal" and harap in h[0]["komentar"], (nama, h[0]["komentar"])
    assert len(events(d)) == n0


@uji("dumb-proof: nama pengganti (belum ditentukan, -, TBD) ditolak untuk masjid/penyelenggara/pemateri baru")
def _():
    d = siapkan(); n0 = len(events(d))
    for i, k in enumerate([dict(Masjid="Online", Nama_masjid_baru="belum ditentukan"), dict(Masjid="Online", Nama_masjid_baru="-"),
                           dict(Masjid=ad.LAINNYA, Nama_masjid_baru="TBD", Alamat_masjid_baru="Jl X", Kota_masjid_baru="Depok"),
                           dict(Pemateri=ad.LAINNYA, Pemateri_baru="-"), dict(Pemateri=ad.LAINNYA, Pemateri_baru="TBA")]):
        h = jalankan(d, [iss(420 + i, form(Judul=f"PH{i}", **k))])
        assert h[0]["status"] == "gagal" and "bukan nama" in h[0]["komentar"], (k, h[0]["komentar"])
    assert len(events(d)) == n0
    h = jalankan(d, [iss(430, form(Judul="PHok", Pemateri=ad.LAINNYA, Pemateri_baru="Belum ditentukan"))])  # sah: sama dengan opsi bawaan
    assert h[0]["status"] == "ok" and events(d)[-1]["ustadz"] == "Belum ditentukan"


@uji("dumb-proof: nama kota/masjid/pemateri baru yang mirip ditolak kecuali 'Abaikan kemiripan nama' dicentang")
def _():
    d = siapkan(); n0 = len(events(d))
    kota_typo = dict(Masjid=ad.LAINNYA, Nama_masjid_baru="Masjid Uji Satu", Alamat_masjid_baru="Jl U", Kota_masjid_baru=ad.KOTA_LAIN, Kota_lain="Jakrta")
    h = jalankan(d, [iss(440, form(Judul="MR1", **kota_typo))])
    assert h[0]["status"] == "gagal" and "Jakarta" in h[0]["komentar"] and "Abaikan kemiripan nama" in h[0]["komentar"], h[0]["komentar"]
    assert len(events(d)) == n0 and "Jakrta" not in kat(d)["kota"]
    cek = "- [x] " + ad.OPSI_ABAIKAN
    h = jalankan(d, [iss(441, form(Judul="MR2", Abaikan_kemiripan_nama=cek, **kota_typo))], edited=440)  # tetap Issue lain; baru
    assert h[0]["status"] == "ok" and "diabaikan atas permintaan pengguna" in h[0]["komentar"] and "Jakrta" in kat(d)["kota"], h[0]["komentar"]
    m0 = kat(d)["masjid"][0]
    h = jalankan(d, [iss(442, form(Judul="MR3", Masjid=ad.LAINNYA, Nama_masjid_baru=m0["nama"] + "a", Alamat_masjid_baru="x", Kota_masjid_baru=m0["kota"]))])
    assert h[0]["status"] == "gagal" and "mirip" in h[0]["komentar"]
    p0 = next(p for p in kat(d)["pemateri"] if p["nama"] == "Abu Hurairah")
    h = jalankan(d, [iss(443, form(Judul="MR4", Pemateri=ad.LAINNYA, Pemateri_baru="Abu Hurairoh"))])
    assert h[0]["status"] == "gagal" and "mirip" in h[0]["komentar"]


@uji("dumb-proof: pemateri ustadzah otomatis Khusus Akhwat (master dan nama baru); konflik dengan Ikhwan ditolak")
def _():
    d = siapkan()
    assert next(p for p in kat(d)["pemateri"] if p["nama"] == "Poppy Yuditya").get("perempuan") is True
    h = jalankan(d, [iss(450, form(Judul="UA1", Pemateri="Poppy Yuditya"))])
    assert events(d)[-1]["audience"] == "Khusus Akhwat" and "Ustadzah" in h[0]["komentar"]
    h = jalankan(d, [iss(451, form(Judul="UA2", Pemateri=ad.LAINNYA, Pemateri_baru="Ustadzah Fulanah binti Contoh, Lc."))])
    assert events(d)[-1]["audience"] == "Khusus Akhwat"
    assert next(p for p in kat(d)["pemateri"] if p["tampil"].startswith("Ustadzah Fulanah"))["perempuan"] is True
    h = jalankan(d, [iss(452, form(Judul="UA3", Pemateri="Poppy Yuditya", Audience="Khusus Ikhwan"))])
    assert h[0]["status"] == "gagal" and "Ikhwan" in h[0]["komentar"]


@uji("dumb-proof: Issue diedit setelah diproses mendapat komentar (bukan diam); tanpa edit tidak ada komentar")
def _():
    d = siapkan()
    h = jalankan(d, [iss(460, form(Judul="ED"))]); ids = h[0]["id"]
    assert jalankan(d, [iss(460, form(Judul="ED2"))]) == []
    h = jalankan(d, [iss(460, form(Judul="ED2"))], edited=460)
    assert h[0]["status"] == "abaikan" and h[0]["id"] == ids and str(ids[0]) in h[0]["komentar"] and "tidak diterapkan" in h[0]["komentar"]
    assert [e["title"] for e in events(d) if e["id"] in ids] == ["ED"]  # data tidak berubah


@uji("Issue dikenali dari isi formulir, bukan judul; judul berawalan tetapi kolom hilang -> gagal berpesan; non-formulir diabaikan")
def _():
    d = siapkan(); n0 = len(events(d))
    h = jalankan(d, [iss(470, form(Judul="TanpaAwalan"), title="UJI")])
    assert h[0]["status"] == "ok" and len(events(d)) == n0 + 1
    h = jalankan(d, [iss(471, "### Tanggal\n\n10 Okt 2026\n", title="Tambah kajian: setengah")])
    assert h[0]["status"] == "gagal" and "formulir" in h[0]["komentar"]
    assert jalankan(d, [iss(472, "Catatan pribadi tanpa formulir.", title="Ingatkan beli kopi")]) == []
    assert jalankan(d, [iss(473, form(Judul="Orang lain"), title="UJI", login="orang-lain")]) == []
    assert ad.adalah_formulir(form()) and not ad.adalah_formulir("### Tanggal\n\nx\n") and not ad.adalah_formulir("")


@uji("pecah_body: heading, _No response_, centang")
def _():
    f = ad.pecah_body("### Tanggal\n\n2026-10-10\n\n### Jam\n\n_No response_\n\n### Kajian rutin\n\n- [X] Kajian rutin atau berkala\n")
    assert f == {"Tanggal": "2026-10-10", "Jam": "", "Kajian rutin": "- [X] Kajian rutin atau berkala"}
    assert ad._centang(f["Kajian rutin"]) and not ad._centang("- [ ] x")


if __name__ == "__main__":
    gagal = 0
    for fn in UJI:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            gagal += 1
            import traceback
            print("GAGAL:", fn.__name__); traceback.print_exc()
    print(f"\n{len(LULUS)} lulus, {gagal} gagal")
    sys.exit(1 if gagal else 0)
