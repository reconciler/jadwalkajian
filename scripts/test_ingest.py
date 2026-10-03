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
import adapter_koreksi_form as adk  # noqa: E402
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
    # Uji tidak boleh bergantung pada riwayat Issue live (nomor Issue/id yang sudah terpakai): kosongkan di salinan.
    f_kat = d / "data" / "kategori.json"
    k = json.loads(f_kat.read_text(encoding="utf-8"))
    k["diproses"], k["gagal"] = [], []
    f_kat.write_text(json.dumps(k, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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


def fk(aksi, target, **k):
    """Isi Issue formulir Koreksi atau hapus (kunci = kunci LABEL adapter_koreksi_form)."""
    v = {"aksi": aksi, "target": target, "konfirmasi": "", "judul": "", "tanggal": "", "jenis_waktu": adk.TIDAK_DIUBAH,
         "jam": "", "pemateri": adk.TIDAK_DIUBAH, "pemateri_baru": "", "masjid": adk.TIDAK_DIUBAH, "masjid_baru": "",
         "alamat_baru": "", "kota_baru": "", "kota_lain": "", "audience": adk.TIDAK_DIUBAH, "rutin": adk.TIDAK_DIUBAH,
         "abaikan_mirip": "", "catatan": ""}
    v.update(k)
    return "\n".join(f"### {adk.LABEL[x]}\n\n{v[x] if v[x] else '_No response_'}\n" for x in adk.LABEL)


def seri(d, n=500, judul="Seri uji", **k):
    """Buat satu seri event lewat Issue Tambah; kembalikan daftar id."""
    h = jalankan(d, [iss(n, form(Judul=judul, Tanggal="3-31 Okt 2026 setiap Sabtu", **k))])
    assert h[0]["status"] == "ok", h
    return h[0]["id"]


def jalankan(d, issues, edited=None, today=TODAY):
    (d / "issues.json").write_text(json.dumps(issues), encoding="utf-8")
    argv = ["--issues", str(d / "issues.json"), "--out", str(d / "out.json"),
            "--commit-msg", str(d / "msg.txt"), "--root", str(d), "--today", today]
    if edited:
        argv += ["--edited", str(edited)]
    ingest.main(argv)
    return json.loads((d / "out.json").read_text(encoding="utf-8"))["hasil"]


def dua(d, issues, edited=None, today=TODAY):
    """Alur dua langkah formulir Koreksi/hapus: kirim dengan Konfirmasi kosong -> pratinjau (status gagal);
    lalu edit Issue dengan konfirmasi dari pratinjau. Hasil yang bukan pratinjau dikembalikan apa adanya."""
    h = jalankan(d, issues, edited=edited, today=today)
    akhir = []
    for x, i in zip(h, issues):
        m = re.search(r"tulis `((?:HAPUS|KOREKSI) \d+)`", x["komentar"])
        if x["status"] == "gagal" and "Belum ada yang" in x["komentar"] and m:
            lab = "### " + adk.LABEL["konfirmasi"] + "\n\n_No response_"
            assert lab in i["body"]
            baru = dict(i, body=i["body"].replace(lab, "### " + adk.LABEL["konfirmasi"] + "\n\n" + m.group(1)))
            x = jalankan(d, [baru], edited=i["number"], today=today)[0]
        akhir.append(x)
    return akhir


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
        jalankan(d, [iss(10 + i, form(Judul=f"Judul W{i}", Jenis_waktu=j))])
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
        form(Judul="a</script><script>alert(1)"), form(Judul="Judul x" * 201), form(Catatan="a > b"),
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
    jalankan(a, [iss(50, form(Judul="Judul A"))]); jalankan(b, [iss(51, form(Judul="Judul B"))])
    assert events(a)[-1]["id"] == events(b)[-1]["id"]  # bentrok bila keduanya dipush
    shutil.copy(b / "index.html", a / "index.html"); shutil.copy(b / "data" / "kategori.json", a / "data" / "kategori.json")  # = reset ke main terbaru
    h = jalankan(a, [iss(50, form(Judul="Judul A"))])
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
    assert "otomatis" in jalankan(d, [iss(300, form(Judul="Judul K", Tanggal="3-31 Okt 2026 Sabtu"))])[0]["komentar"]


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
        h = jalankan(d, [iss(230 + i, form(Judul=f"Judul T{i}", Tanggal=tg))])
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
        h = jalankan(d, [iss(400 + i, form(Judul=f"Judul DP{i}", **k))])
        assert h[0]["status"] == "gagal" and harap in h[0]["komentar"], (nama, h[0]["komentar"])
    assert len(events(d)) == n0


@uji("dumb-proof: nama pengganti (belum ditentukan, -, TBD) ditolak untuk masjid/penyelenggara/pemateri baru")
def _():
    d = siapkan(); n0 = len(events(d))
    for i, k in enumerate([dict(Masjid="Online", Nama_masjid_baru="belum ditentukan"), dict(Masjid="Online", Nama_masjid_baru="-"),
                           dict(Masjid=ad.LAINNYA, Nama_masjid_baru="TBD", Alamat_masjid_baru="Jl X", Kota_masjid_baru="Depok"),
                           dict(Pemateri=ad.LAINNYA, Pemateri_baru="-"), dict(Pemateri=ad.LAINNYA, Pemateri_baru="TBA")]):
        h = jalankan(d, [iss(420 + i, form(Judul=f"Judul PH{i}", **k))])
        assert h[0]["status"] == "gagal" and "bukan nama" in h[0]["komentar"], (k, h[0]["komentar"])
    assert len(events(d)) == n0
    h = jalankan(d, [iss(430, form(Judul="PHok", Pemateri=ad.LAINNYA, Pemateri_baru="Belum ditentukan"))])  # sah: sama dengan opsi bawaan
    assert h[0]["status"] == "ok" and events(d)[-1]["ustadz"] == "Belum ditentukan"


@uji("dumb-proof: nama kota/masjid/pemateri baru yang mirip ditolak kecuali 'Abaikan kemiripan nama' dicentang")
def _():
    d = siapkan(); n0 = len(events(d))
    kota_typo = dict(Masjid=ad.LAINNYA, Nama_masjid_baru="Masjid Uji Satu", Alamat_masjid_baru="Jl U", Kota_masjid_baru=ad.KOTA_LAIN, Kota_lain="Jakrta")
    h = jalankan(d, [iss(440, form(Judul="Judul MR1", **kota_typo))])
    assert h[0]["status"] == "gagal" and "Jakarta" in h[0]["komentar"] and "Abaikan kemiripan nama" in h[0]["komentar"], h[0]["komentar"]
    assert len(events(d)) == n0 and "Jakrta" not in kat(d)["kota"]
    cek = "- [x] " + ad.OPSI_ABAIKAN
    h = jalankan(d, [iss(441, form(Judul="Judul MR2", Abaikan_kemiripan_nama=cek, **kota_typo))], edited=440)  # tetap Issue lain; baru
    assert h[0]["status"] == "ok" and "diabaikan atas permintaan pengguna" in h[0]["komentar"] and "Jakrta" in kat(d)["kota"], h[0]["komentar"]
    m0 = kat(d)["masjid"][0]
    h = jalankan(d, [iss(442, form(Judul="Judul MR3", Masjid=ad.LAINNYA, Nama_masjid_baru=m0["nama"] + "a", Alamat_masjid_baru="x", Kota_masjid_baru=m0["kota"]))])
    assert h[0]["status"] == "gagal" and "mirip" in h[0]["komentar"]
    p0 = next(p for p in kat(d)["pemateri"] if p["nama"] == "Abu Hurairah")
    h = jalankan(d, [iss(443, form(Judul="Judul MR4", Pemateri=ad.LAINNYA, Pemateri_baru="Abu Hurairoh"))])
    assert h[0]["status"] == "gagal" and "mirip" in h[0]["komentar"]


@uji("dumb-proof: pemateri ustadzah otomatis Khusus Akhwat (master dan nama baru); konflik dengan Ikhwan ditolak")
def _():
    d = siapkan()
    assert next(p for p in kat(d)["pemateri"] if p["nama"] == "Poppy Yuditya").get("perempuan") is True
    h = jalankan(d, [iss(450, form(Judul="Judul UA1", Pemateri="Poppy Yuditya"))])
    assert events(d)[-1]["audience"] == "Khusus Akhwat" and "Ustadzah" in h[0]["komentar"]
    h = jalankan(d, [iss(451, form(Judul="Judul UA2", Pemateri=ad.LAINNYA, Pemateri_baru="Ustadzah Fulanah binti Contoh, Lc."))])
    assert events(d)[-1]["audience"] == "Khusus Akhwat"
    assert next(p for p in kat(d)["pemateri"] if p["tampil"].startswith("Ustadzah Fulanah"))["perempuan"] is True
    h = jalankan(d, [iss(452, form(Judul="Judul UA3", Pemateri="Poppy Yuditya", Audience="Khusus Ikhwan"))])
    assert h[0]["status"] == "gagal" and "Ikhwan" in h[0]["komentar"]


@uji("dumb-proof: Issue diedit setelah diproses mendapat komentar (bukan diam); tanpa edit tidak ada komentar")
def _():
    d = siapkan()
    h = jalankan(d, [iss(460, form(Judul="Judul ED"))]); ids = h[0]["id"]
    assert jalankan(d, [iss(460, form(Judul="Judul ED2"))]) == []
    h = jalankan(d, [iss(460, form(Judul="Judul ED2"))], edited=460)
    assert h[0]["status"] == "abaikan" and h[0]["id"] == ids and str(ids[0]) in h[0]["komentar"] and "tidak diterapkan" in h[0]["komentar"]
    assert [e["title"] for e in events(d) if e["id"] in ids] == ["Judul ED"]  # data tidak berubah


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


@uji("tahap 2 templat: formulir Koreksi/hapus sah, labelnya tidak bentrok dengan Tambah (tidak saling dikira)")
def _():
    import yaml
    t = yaml.safe_load(adk.render_template(core.muat_kategori(REPO / "data" / "kategori.json")))
    assert t["title"] == adk.JUDUL_KOREKSI and len(t["body"]) == len(adk.LABEL) == 18
    assert [x["attributes"]["label"] for x in t["body"]] == [adk.LABEL[k] for k in adk.LABEL]
    ids = [x["id"] for x in t["body"]]; assert len(ids) == len(set(ids))
    for x in t["body"]:
        if x["type"] == "dropdown":
            o = x["attributes"]["options"]
            assert len(o) == len(set(o)) and not any("," in s for s in o), x["id"]
    assert adk.adalah_koreksi(fk("Hapus", "#1")) and not ad.adalah_formulir(fk("Hapus", "#1"))
    assert ad.adalah_formulir(form()) and not adk.adalah_koreksi(form())
    assert not set(adk.LABEL.values()) & set(ad.PENANDA_FORMULIR)


@uji("hapus: pratinjau dulu, lalu HAPUS <jumlah>; semua-atau-tidak-sama-sekali; tercatat di diproses; komentar lengkap")
def _():
    d = siapkan(); ids = seri(d, Catatan="catatan penting"); n0 = len(events(d))
    # tanpa konfirmasi: pratinjau, tidak ada yang berubah
    h = jalankan(d, [iss(510, fk("Hapus", f"{ids[0]}"), title="Hapus")])
    assert h[0]["status"] == "gagal" and "Belum ada yang dihapus" in h[0]["komentar"] and "`HAPUS 1`" in h[0]["komentar"]
    assert "catatan penting" in h[0]["komentar"] and len(events(d)) == n0
    assert any(g["issue"] == 510 and g["alasan"] == ["menunggu konfirmasi"] and g.get("isi") for g in kat(d)["gagal"])
    # konfirmasi salah: kata lain, tanpa jumlah, jumlah keliru, lintas-aksi
    for i, (konf, harap) in enumerate([("HAPUS", "belum memuat jumlah"), ("HAPUS 5", "berbeda dengan jumlah"),
                                       ("KOREKSI 1", "untuk Koreksi. Pilih Aksi = Koreksi"), ("ya", "tidak dikenali")]):
        h = jalankan(d, [iss(516 + i, fk("Hapus", f"{ids[0]}", konfirmasi=konf))])
        assert h[0]["status"] == "gagal" and harap in h[0]["komentar"] and len(events(d)) == n0, (konf, h[0]["komentar"])
    h = jalankan(d, [iss(511, fk("Hapus", f"{ids[0]}, 999999", konfirmasi="HAPUS 1"))])
    assert h[0]["status"] == "gagal" and "999999" in h[0]["komentar"] and len(events(d)) == n0, h[0]["komentar"]
    h = jalankan(d, [iss(512, fk("Hapus", f"{ids[0]}", konfirmasi="HAPUS 1", judul="Maksudnya koreksi"))])
    assert h[0]["status"] == "gagal" and "pilih Aksi = Koreksi" in h[0]["komentar"] and len(events(d)) == n0
    # Q12: Target diubah sesudah pratinjau -> konfirmasi tidak berlaku, pratinjau baru muncul
    h = jalankan(d, [iss(510, fk("Hapus", f"{ids[0]}-{ids[1]}", konfirmasi="hapus 2"))], edited=510)
    assert h[0]["status"] == "gagal" and "Data berubah sejak pratinjau" in h[0]["komentar"] and len(events(d)) == n0
    # konfirmasi benar (edit Issue yang sama sesudah pratinjau terbaru)
    h = jalankan(d, [iss(510, fk("Hapus", f"{ids[0]}-{ids[1]}", konfirmasi="hapus 2"))], edited=510)
    assert h[0]["status"] == "ok" and h[0]["id"] == ids[:2] and "sudah dihapus" in h[0]["komentar"] and len(events(d)) == n0 - 2
    assert "alamat" in h[0]["komentar"] and "catatan penting" in h[0]["komentar"] and "<details>" in h[0]["komentar"]
    assert "{id:%d,date:" % ids[0] in h[0]["komentar"]
    assert {"issue": 510, "id": ids[:2], "aksi": "hapus"} in kat(d)["diproses"]
    assert not any(g["issue"] == 510 for g in kat(d)["gagal"])
    h = dua(d, [iss(514, fk("Hapus", "#500"))])  # sisa seri, lewat dua langkah
    assert h[0]["status"] == "ok" and h[0]["id"] == ids[2:] and len(events(d)) == n0 - len(ids)
    h = dua(d, [iss(515, fk("Hapus", "#500"))])
    assert h[0]["status"] == "gagal" and "sudah tidak ada" in h[0]["komentar"]
    env = {"PATH": "/usr/bin:/bin"}
    for sc in ("prune.py", "build.py"):
        assert subprocess.run([sys.executable, str(d / "scripts" / sc)], capture_output=True, text=True, env=env).returncode == 0


@uji("koreksi: pratinjau selisih dulu, KOREKSI <jumlah> menerapkan; jumlah salah atau konfirmasi Hapus ditolak")
def _():
    d = siapkan(); ids = seri(d, judul="Judul lama"); sebelum = events(d)
    h = jalankan(d, [iss(590, fk("Koreksi", "#500", judul="Judul baru"))])
    assert h[0]["status"] == "gagal" and "Belum ada yang diubah" in h[0]["komentar"] and f"`KOREKSI {len(ids)}`" in h[0]["komentar"]
    assert "`Judul lama`" in h[0]["komentar"] and "`Judul baru`" in h[0]["komentar"] and events(d) == sebelum
    for i, (konf, harap) in enumerate([(f"KOREKSI {len(ids) + 1}", "berbeda dengan jumlah"), ("HAPUS 1", "untuk Hapus. Pilih Aksi = Hapus"),
                                       ("KOREKSI", "belum memuat jumlah")]):
        h = jalankan(d, [iss(591 + i, fk("Koreksi", "#500", judul="Judul baru", konfirmasi=konf))])
        assert h[0]["status"] == "gagal" and harap in h[0]["komentar"] and events(d) == sebelum, (konf, h[0]["komentar"])
    h = jalankan(d, [iss(590, fk("Koreksi", "#500", judul="Judul baru", konfirmasi=f"koreksi {len(ids)}"))], edited=590)
    assert h[0]["status"] == "ok" and all(e["title"] == "Judul baru" for e in events(d) if e["id"] in ids)


@uji("koreksi catatan: (kosongkan) menghapus catatan; kolom kosong tetap mempertahankan")
def _():
    d = siapkan(); ids = seri(d, Catatan="catatan lama")
    h = dua(d, [iss(595, fk("Koreksi", f"{ids[0]}", judul="Judul lain"))])
    assert h[0]["status"] == "ok" and next(e for e in events(d) if e["id"] == ids[0])["note"] == "catatan lama"
    h = dua(d, [iss(596, fk("Koreksi", f"{ids[0]}", catatan="(kosongkan)"))])
    assert h[0]["status"] == "ok" and next(e for e in events(d) if e["id"] == ids[0])["note"] == ""


@uji("target: 'id N' eksplisit; angka telanjang yang ambigu dengan nomor Issue terproses ditolak; #N tetap Issue")
def _():
    d = siapkan(); ids = seri(d, n=500)
    # buat Issue terproses bernomor sama dengan id event (nomor Issue = ids[0])
    kk = kat(d); kk["diproses"].append({"issue": ids[0], "id": []}); core.simpan_kategori(d / "data" / "kategori.json", kk)
    h = jalankan(d, [iss(597, fk("Hapus", f"{ids[0]}"))])
    assert h[0]["status"] == "gagal" and "ambigu" in h[0]["komentar"] and f"id {ids[0]}" in h[0]["komentar"]
    h = jalankan(d, [iss(598, fk("Hapus", f"id {ids[0]}"))])
    assert h[0]["status"] == "gagal" and "Belum ada yang dihapus" in h[0]["komentar"] and "`HAPUS 1`" in h[0]["komentar"]
    # Q12: konfirmasi tanpa pernah melihat pratinjau tidak berlaku; sesudah pratinjau tampil, edit yang sama berlaku
    h = jalankan(d, [iss(599, fk("Hapus", f"id {ids[0]}", konfirmasi="HAPUS 1"))])
    assert h[0]["status"] == "gagal" and "belum pernah menampilkan pratinjau" in h[0]["komentar"]
    h = jalankan(d, [iss(599, fk("Hapus", f"id {ids[0]}", konfirmasi="HAPUS 1"))], edited=599)
    assert h[0]["status"] == "ok" and h[0]["id"] == [ids[0]]


@uji("kartu situs menampilkan ID di rincian; HTML statis tidak berubah")
def _():
    html = (REPO / "index.html").read_text(encoding="utf-8")
    assert '<div class="dt">ID</div><div class="dd">${e.id}</div>' in html


@uji("koreksi seri: judul diganti untuk seluruh #Issue, kolom lain tidak berubah, id tetap, selisih ada di komentar")
def _():
    d = siapkan(); ids = seri(d, judul="Judul salah", Catatan="catatan asli")
    sebelum = {e["id"]: e for e in events(d)}
    h = dua(d, [iss(520, fk("Koreksi", "#500", judul="Judul benar"))])
    assert h[0]["status"] == "ok" and h[0]["id"] == ids and "sudah dikoreksi" in h[0]["komentar"], h[0]["komentar"]
    sesudah = {e["id"]: e for e in events(d)}
    for i in ids:
        a, b = sebelum[i], sesudah[i]
        assert b["title"] == "Judul benar" and {k: v for k, v in a.items() if k != "title"} == {k: v for k, v in b.items() if k != "title"}
    assert all(sesudah[i] == sebelum[i] for i in sebelum if i not in ids)
    assert "`Judul salah`" in h[0]["komentar"] and "`Judul benar`" in h[0]["komentar"]


@uji("koreksi tanggal: hanya satu event, satu tanggal, tidak boleh lampau; dayShort ikut berubah")
def _():
    d = siapkan(); ids = seri(d)
    h = dua(d, [iss(530, fk("Koreksi", f"{ids[0]}", tanggal="11 Okt 2026"))])
    e = next(x for x in events(d) if x["id"] == ids[0])
    assert h[0]["status"] == "ok" and e["date"] == "2026-10-11" and e["dayShort"] == "Min 11 Okt", (h[0]["komentar"], e)
    for i, (tg, harap) in enumerate([("11 Okt 2026", None), ("3-5 Okt 2026", "satu tanggal"), ("2026-10-02", "sudah lewat"), ("besok", "tidak dikenali")]):
        target = f"{ids[1]}, {ids[2]}" if i == 0 else f"{ids[1]}"
        h = dua(d, [iss(531 + i, fk("Koreksi", target, tanggal=tg))])
        assert h[0]["status"] == "gagal" and (harap is None and "hanya untuk satu event" in h[0]["komentar"] or harap in h[0]["komentar"]), (tg, h[0]["komentar"])


@uji("koreksi waktu: Jam saja hanya untuk event berjam eksak; jenis salat + Jam ditolak; semua-atau-tidak-sama-sekali")
def _():
    d = siapkan()
    a = jalankan(d, [iss(540, form(Judul="Jam A", Tanggal="10 Okt 2026", Jenis_waktu="Jam eksak", Jam="09.00"))])[0]["id"][0]
    b = jalankan(d, [iss(541, form(Judul="Jam B", Tanggal="11 Okt 2026"))])[0]["id"][0]  # Ba'da Maghrib
    h = dua(d, [iss(542, fk("Koreksi", f"{b}", jam="10.00"))])
    assert h[0]["status"] == "gagal" and "Jam eksak" in h[0]["komentar"]
    h = dua(d, [iss(543, fk("Koreksi", f"{b}", jenis_waktu="Ba'da Subuh", jam="10.00"))])
    assert h[0]["status"] == "gagal" and "bukan Jam eksak" in h[0]["komentar"]
    h = dua(d, [iss(544, fk("Koreksi", f"{a}, {b}", jam="10.00"))])  # b gagal -> a juga tidak berubah
    assert h[0]["status"] == "gagal" and next(x for x in events(d) if x["id"] == a)["timeLabel"] == "09.00 WIB"
    h = dua(d, [iss(545, fk("Koreksi", f"{b}", jenis_waktu="Jam eksak", jam="19.30-21.00"))])
    e = next(x for x in events(d) if x["id"] == b)
    assert h[0]["status"] == "ok" and e["timeLabel"] == "19.30 – 21.00 WIB" and e["timeOrder"] == 19.5
    h = dua(d, [iss(546, fk("Koreksi", f"{b}", jam="20.00"))])  # kini berjam eksak
    assert h[0]["status"] == "ok" and next(x for x in events(d) if x["id"] == b)["timeLabel"] == "20.00 WIB"
    h = dua(d, [iss(547, fk("Koreksi", f"{b}", jenis_waktu="Dhuha"))])
    e = next(x for x in events(d) if x["id"] == b)
    assert h[0]["status"] == "ok" and e["timeLabel"] == "Dhuha" and e["timeOrder"] == 9


@uji("koreksi pemateri dan masjid: dropdown, Lainnya, pencocokan otomatis, ustadzah -> Akhwat, konflik ditolak")
def _():
    d = siapkan(); ids = seri(d)
    i0 = ids[0]; ev = lambda: next(x for x in events(d) if x["id"] == i0)  # noqa: E731
    h = dua(d, [iss(550, fk("Koreksi", f"{i0}", pemateri="Abu Hurairah"))])
    assert h[0]["status"] == "ok" and ev()["ustadz"] == "Ustadz Abu Hurairah, MA"
    h = dua(d, [iss(551, fk("Koreksi", f"{i0}", pemateri=ad.LAINNYA, pemateri_baru="Ustadz Dr. Abu Hurairah, M.A."))])
    assert h[0]["status"] == "gagal" and "tidak ada yang berubah" in h[0]["komentar"]  # cocok otomatis = sama dengan sekarang
    h = dua(d, [iss(552, fk("Koreksi", f"{i0}", pemateri="Poppy Yuditya"))])
    assert h[0]["status"] == "ok" and ev()["audience"] == "Khusus Akhwat" and ev()["ustadz"] == "Ustadzah Poppy Yuditya"
    h = dua(d, [iss(553, fk("Koreksi", f"{i0}", pemateri_baru="Ustadz X"))])
    assert h[0]["status"] == "gagal" and "masih '(tidak diubah)'" in h[0]["komentar"]
    h = dua(d, [iss(554, fk("Koreksi", f"{i0}", masjid="Masjid Istiqlal (Jakarta)"))])
    assert h[0]["status"] == "ok" and ev()["masjid"] == "Masjid Istiqlal" and ev()["area"] == "Jakarta"
    h = dua(d, [iss(558, fk("Koreksi", f"{i0}", masjid="Masjid Istiqlal (Jakarta)"))])  # sama dengan sekarang
    assert h[0]["status"] == "gagal" and "tidak ada yang berubah" in h[0]["komentar"]
    h = dua(d, [iss(555, fk("Koreksi", f"{i0}", masjid=ad.LAINNYA, masjid_baru="Masjid Koreksi Baru", alamat_baru="Jl K 1", kota_baru="Bogor"))])
    assert h[0]["status"] == "ok" and ev()["masjid"] == "Masjid Koreksi Baru" and ev()["area"] == "Bogor" and ev()["address"] == "Jl K 1"
    assert any(m["nama"] == "Masjid Koreksi Baru" for m in kat(d)["masjid"])
    h = dua(d, [iss(556, fk("Koreksi", f"{i0}", alamat_baru="Jl Z"))])
    assert h[0]["status"] == "gagal" and "kolom masjid baru terisi" in h[0]["komentar"]
    h = dua(d, [iss(557, fk("Koreksi", f"{i0}", masjid="Online", masjid_baru="belum ditentukan"))])
    assert h[0]["status"] == "gagal" and "bukan nama" in h[0]["komentar"]


@uji("koreksi: tanpa isian, sama dengan sekarang, atau jadi duplikat event lain -> ditolak; Tambah+Koreksi dalam satu run berurutan")
def _():
    d = siapkan(); ids = seri(d, judul="Judul X")
    h = dua(d, [iss(560, fk("Koreksi", f"{ids[0]}"))])
    assert h[0]["status"] == "gagal" and "tidak ada kolom koreksi" in h[0]["komentar"]
    h = dua(d, [iss(561, fk("Koreksi", f"{ids[0]}", judul="Judul X"))])
    assert h[0]["status"] == "gagal" and "tidak ada yang berubah" in h[0]["komentar"]
    jalankan(d, [iss(562, form(Judul="Judul Y", Tanggal="3 Okt 2026", Jenis_waktu="Ba'da Subuh", Masjid="Masjid Al-Adhim (Depok)"))])
    h = dua(d, [iss(563, fk("Koreksi", f"{ids[0]}", judul="Judul Y", jenis_waktu="Ba'da Subuh", masjid="Masjid Al-Adhim (Depok)"))])
    assert h[0]["status"] == "gagal" and "duplikat" in h[0]["komentar"]
    h = jalankan(d, [iss(570, form(Judul="Satu run", Tanggal="12 Okt 2026"))]); h = dua(d, [iss(571, fk("Koreksi", "#570", judul="Satu run (dikoreksi)"))])
    assert [x["status"] for x in h] == ["ok"] and any(e["title"] == "Satu run (dikoreksi)" for e in events(d))


@uji("Issue koreksi/hapus yang diedit setelah diproses mendapat komentar; Issue koreksi tanpa kolom -> gagal berpesan")
def _():
    d = siapkan(); ids = seri(d)
    dua(d, [iss(580, fk("Koreksi", f"{ids[0]}", judul="Baru"))])
    h = jalankan(d, [iss(580, fk("Koreksi", f"{ids[0]}", judul="Baru lagi"))], edited=580)
    assert h[0]["status"] == "abaikan" and "tidak diterapkan" in h[0]["komentar"]
    assert next(x for x in events(d) if x["id"] == ids[0])["title"] == "Baru"
    h = dua(d, [iss(581, "### Aksi\n\nHapus\n", title="Koreksi kajian: setengah")])
    assert h[0]["status"] == "gagal" and "Koreksi atau hapus" in h[0]["komentar"]


@uji("Q1: backslash di teks event tidak merusak build.py; teks tersimpan apa adanya di blok statis dan JSON-LD")
def _():
    for i, (kolom, nilai) in enumerate([("Judul", "Kajian \\sunnah"), ("Judul", "C:\\Users\\x"), ("Catatan", "baris\\nbaru"),
                                       ("Pemateri baru", "Ustadz A\\1"), ("Judul", "akhir\\")]):
        d = siapkan()
        kw = {kolom.replace(" ", "_"): nilai}
        if kolom == "Pemateri baru":
            kw["Pemateri"] = ad.LAINNYA
        h = jalankan(d, [iss(900 + i, form(**kw))])
        assert h[0]["status"] == "ok", (nilai, h)
        for sc in ("prune.py", "build.py"):
            r = subprocess.run([sys.executable, str(d / "scripts" / sc)], capture_output=True, text=True, cwd=d)
            assert r.returncode == 0, (nilai, sc, r.stderr[-200:])
        html = (d / "index.html").read_text(encoding="utf-8")
        ld = html.split("<!--LD_JSON_START-->")[1].split("<!--LD_JSON_END-->")[0]
        data = json.loads(re.search(r"<script[^>]*>(.*)</script>", ld, re.S).group(1))
        teks = nilai
        assert teks in html.split("<!--STATIC_EVENTS_START-->")[1].split("<!--STATIC_EVENTS_END-->")[0], nilai  # tidak diubah jadi karakter lain
        assert teks in json.dumps(data, ensure_ascii=False).replace("\\\\", "\\"), nilai


@uji("Q2: Hapus yang menyisakan 0 kajian mendatang ditolak sebelum pratinjau; hapus sebagian tetap jalan")
def _():
    d = siapkan(); semua = [e["id"] for e in events(d)]
    n0 = len(semua)
    tg = ", ".join(f"id {i}" for i in semua[:60])
    h = jalankan(d, [iss(910, fk("Hapus", tg))])
    assert h[0]["status"] == "gagal" and "menyisakan 0 kajian mendatang" in h[0]["komentar"], h[0]["komentar"]
    h = jalankan(d, [iss(911, fk("Hapus", tg, konfirmasi=f"HAPUS {len(semua[:60])}"))])
    assert h[0]["status"] == "gagal" and "menyisakan 0 kajian mendatang" in h[0]["komentar"] and len(events(d)) == n0
    # sisa hanya event yang sudah lewat (tanggal uji maju): tetap ditolak
    h = jalankan(d, [iss(912, fk("Hapus", f"id {semua[0]}"))], today="2030-01-01")
    assert h[0]["status"] == "gagal" and len(events(d)) == n0
    # sebagian saja: pratinjau normal
    h = jalankan(d, [iss(913, fk("Hapus", f"id {semua[0]}"))])
    assert h[0]["status"] == "gagal" and "Belum ada yang dihapus" in h[0]["komentar"]


@uji("Q5: Issue gagal diproses ulang bila isinya berubah walau sinyal edit hilang; isi sama -> tetap dilewati tanpa komentar")
def _():
    d = siapkan(); ids = seri(d); n0 = len(events(d))
    h = jalankan(d, [iss(920, fk("Hapus", f"id {ids[0]}"))])
    assert h[0]["status"] == "gagal" and "Belum ada yang dihapus" in h[0]["komentar"]
    h = jalankan(d, [iss(920, fk("Hapus", f"id {ids[0]}"))])  # run lain tanpa sinyal edit, isi sama
    assert h == [] and len(events(d)) == n0
    h = jalankan(d, [iss(920, fk("Hapus", f"id {ids[0]}", konfirmasi="HAPUS 1"))])  # isi berubah, TANPA --edited
    assert h and h[0]["status"] == "ok" and len(events(d)) == n0 - 1, h
    # Tambah yang gagal lalu diperbaiki tanpa sinyal edit
    d2 = siapkan()
    h = jalankan(d2, [iss(921, form(Judul="Perbaiki", Tanggal="besok sekali"))])
    assert h[0]["status"] == "gagal"
    h = jalankan(d2, [iss(921, form(Judul="Perbaiki", Tanggal="12 Okt 2026"))])
    assert h and h[0]["status"] == "ok" and any(e["title"] == "Perbaiki" for e in events(d2))


@uji("Q6: id tidak pernah dipakai ulang (setelah hapus dan setelah prune); #N lama tidak mengenai event baru")
def _():
    d = siapkan(); ids = seri(d, n=930, judul="Seri satu")
    tertinggi = max(ids)
    h = dua(d, [iss(931, fk("Hapus", "#930"))])
    assert h[0]["status"] == "ok"
    baru = seri(d, n=932, judul="Seri dua", Jenis_waktu="Ba'da Subuh")
    assert min(baru) > tertinggi, (ids, baru)
    assert kat(d)["id_tertinggi"] >= max(baru)
    h = jalankan(d, [iss(933, fk("Hapus", "#930"))])  # Issue lama: semua event sudah tidak ada
    assert h[0]["status"] == "gagal" and "sudah tidak ada" in h[0]["komentar"] and all(e["id"] in [x["id"] for x in events(d)] for e in events(d) if e["id"] in baru)
    # prune: baris event dibuang langsung dari index.html (seperti prune), id tidak boleh dipakai ulang
    html = (d / "index.html").read_text(encoding="utf-8")
    html = "\n".join(l for l in html.split("\n") if not any(l.lstrip().startswith("{id:%d," % i) for i in baru))
    (d / "index.html").write_text(html, encoding="utf-8")
    ids3 = seri(d, n=934, judul="Seri tiga", Jenis_waktu="Dhuha")
    assert min(ids3) > max(baru), (baru, ids3)
    # master lama tanpa id_tertinggi tetap aman (dihitung dari diproses)
    k = kat(d); k.pop("id_tertinggi"); core.simpan_kategori(d / "data" / "kategori.json", k)
    ids4 = seri(d, n=935, judul="Seri empat", Jenis_waktu="Ba'da Ashar")
    assert min(ids4) > max(ids3)


@uji("Q7: jse() mengubah nama apa pun menjadi literal JS yang bernilai sama setelah entitas atribut HTML didekode")
def _():
    html = (REPO / "index.html").read_text(encoding="utf-8")
    fungsi = re.search(r"function esc\(s\)\{.*?\}\nfunction jse\(s\)\{.*?\}", html, re.S)
    assert fungsi, "esc/jse tidak ditemukan"
    nama = ["Masjid back\\slash", "akhir\\", "Masjid O'Neil", 'Masjid "Q"', "A&B <x>", "\\'dua\\\\", "a\\nb", "plain"]
    js = fungsi.group(0) + """
const nama=%s;
const attr=s=>s.replace(/&quot;/g,'"').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
let ok=true;
for(const n of nama){ const lit=attr("'"+jse(n)+"'"); if(eval(lit)!==n){ok=false;console.log('BEDA',JSON.stringify(n));} }
console.log(ok?'OK':'GAGAL');
""" % json.dumps(nama)
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True)
    assert r.stdout.strip() == "OK", (r.stdout, r.stderr)


@uji("Q8: judul pengganti/terlalu pendek dan nama baru generik/angka ditolak; nama wajar (termasuk organisasi) diterima")
def _():
    d = siapkan(); n0 = len(events(d))
    for i, j in enumerate(["-", "?", "TBD", "belum ditentukan", "a", "..", "N/A", "ab", "12", "()"]):
        h = jalankan(d, [iss(940 + i, form(Judul=j, Tanggal=f"{10 + i} Okt 2026"))])
        assert h[0]["status"] == "gagal" and "Judul" in h[0]["komentar"], (j, h[0]["komentar"])
    for i, nm in enumerate(["0", "2026", "Ustadz", "()", "&", "KH", "Ust.", "Kajian", "Masjid Masjid", "Ustadz Pemateri"]):
        h = jalankan(d, [iss(960 + i, form(Judul=f"Uji nama {i}", Pemateri=ad.LAINNYA, Pemateri_baru=nm))])
        assert h[0]["status"] == "gagal" and "Pemateri baru" in h[0]["komentar"], (nm, h[0]["komentar"])
    for i, nm in enumerate(["Masjid", "Mushola", "()", "2026", "Majelis Taklim"]):
        h = jalankan(d, [iss(980 + i, form(Judul=f"Uji masjid {i}", Masjid=ad.LAINNYA, Nama_masjid_baru=nm, Alamat_masjid_baru="Jl A 1", Kota_masjid_baru="Depok"))])
        assert h[0]["status"] == "gagal" and "Nama masjid baru" in h[0]["komentar"], (nm, h[0]["komentar"])
    for i, nm in enumerate(["Kajian", "Ustadz"]):  # penyelenggara Online memakai jalur yang sama
        h = jalankan(d, [iss(990 + i, form(Judul=f"Uji online {i}", Masjid="Online", Nama_masjid_baru=nm))])
        assert h[0]["status"] == "gagal" and "Nama masjid baru" in h[0]["komentar"], (nm, h[0]["komentar"])
    h = jalankan(d, [iss(995, form(Judul="Uji kota", Masjid=ad.LAINNYA, Nama_masjid_baru="Masjid Uji Kota", Alamat_masjid_baru="Jl A 1", Kota_masjid_baru=ad.KOTA_LAIN, Kota_lain="12"))])
    assert h[0]["status"] == "gagal" and "Kota masjid baru" in h[0]["komentar"], h[0]["komentar"]
    assert len(events(d)) == n0
    for i, (j, nm) in enumerate([("Q&A Fiqih Jual Beli", "Asatidz Pengajar Tahsin"), ("Kajian Subuh", "Ustadz Ali")]):
        h = jalankan(d, [iss(996 + i, form(Judul=j, Tanggal=f"{20 + i} Okt 2026", Pemateri=ad.LAINNYA, Pemateri_baru=nm))])
        assert h[0]["status"] == "ok", (j, nm, h[0]["komentar"])


@uji("Q10: karakter pengarah arah/lebar nol dibuang; '(kosongkan)' pada Catatan Tambah menjadi kosong; ZWJ emoji dipertahankan")
def _():
    d = siapkan()
    h = jalankan(d, [iss(1000, form(Judul="\u202eKajian\u200b Fiqih\ufeff", Catatan="(kosongkan)", Tanggal="10 Okt 2026"))])
    e = events(d)[-1]
    assert h[0]["status"] == "ok" and e["title"] == "Kajian Fiqih" and e["note"] == "", e
    h = jalankan(d, [iss(1001, form(Judul="Kajian keluarga \U0001F468\u200d\U0001F469\u200d\U0001F467", Tanggal="11 Okt 2026"))])
    assert h[0]["status"] == "ok" and "\u200d" in events(d)[-1]["title"]
    h = jalankan(d, [iss(1002, form(Judul="\u202e\u200b", Tanggal="12 Okt 2026"))])
    assert h[0]["status"] == "gagal" and "Judul: wajib diisi" in h[0]["komentar"]


@uji("Q11: pipa di teks tidak merusak tabel Markdown komentar (jumlah kolom tetap)")
def _():
    assert ingest.kode("a|b") == "`a\\|b`"
    d = siapkan()
    h = jalankan(d, [iss(1010, form(Judul="Fiqih | Tauhid | Akhlak", Tanggal="10 Okt 2026"))])
    assert h[0]["status"] == "ok"
    baris = [l for l in h[0]["komentar"].split("\n") if l.startswith("|")]
    kolom = {len(re.split(r"(?<!\\)\|", l)) for l in baris}
    assert len(baris) >= 3 and len(kolom) == 1, (baris, kolom)


@uji("Q12: Koreksi - data berubah di antara pratinjau dan konfirmasi -> konfirmasi tidak berlaku, pratinjau baru muncul")
def _():
    d = siapkan(); ids = seri(d, n=1020, judul="Judul awal")
    h = jalankan(d, [iss(1021, fk("Koreksi", "#1020", judul="Judul akhir"))])
    assert h[0]["status"] == "gagal" and "Belum ada yang diubah" in h[0]["komentar"]
    h = dua(d, [iss(1022, fk("Koreksi", f"{ids[0]}", judul="Judul tengah"))])  # Issue lain mengubah satu event
    assert h[0]["status"] == "ok"
    h = jalankan(d, [iss(1021, fk("Koreksi", "#1020", judul="Judul akhir", konfirmasi=f"KOREKSI {len(ids)}"))], edited=1021)
    assert h[0]["status"] == "gagal" and "Data berubah sejak pratinjau" in h[0]["komentar"], h[0]["komentar"]
    assert next(e for e in events(d) if e["id"] == ids[0])["title"] == "Judul tengah"
    h = jalankan(d, [iss(1021, fk("Koreksi", "#1020", judul="Judul akhir", konfirmasi=f"KOREKSI {len(ids)}"))], edited=1021)
    assert h[0]["status"] == "ok" and all(e["title"] == "Judul akhir" for e in events(d) if e["id"] in ids)


@uji("Q4: exception tak terduga di satu Issue -> 'kesalahan internal', data tidak berubah, Issue lain tetap diproses; tidak diulang tiap run")
def _():
    d = siapkan(); n0 = len(events(d)); k0 = kat(d)
    asli = core.bangun_event

    def bom(paket, kat_, hari, ada):
        if paket.get("judul") == "Judul BOOM":
            kat_["pemateri"].append({"nama": "kotor", "tampil": "kotor"})  # perubahan sebagian yang harus dibatalkan
            raise ValueError("ledakan uji")
        return asli(paket, kat_, hari, ada)
    core.bangun_event = bom
    try:
        h = jalankan(d, [iss(1030, form(Judul="Judul BOOM", Tanggal="10 Okt 2026")),
                         iss(1031, form(Judul="Judul aman", Tanggal="11 Okt 2026"))])
        assert [x["status"] for x in h] == ["gagal", "ok"], h
        assert "kesalahan internal" in h[0]["komentar"] and "ValueError" in h[0]["komentar"]
        assert [e["title"] for e in events(d)].count("Judul BOOM") == 0 and len(events(d)) == n0 + 1
        assert not any(p_["nama"] == "kotor" for p_ in kat(d)["pemateri"])  # master dipulihkan
        assert not any(x["issue"] == 1030 for x in kat(d)["diproses"])
        assert any(g["issue"] == 1030 and g["alasan"] == ["kesalahan internal"] for g in kat(d)["gagal"])
        assert jalankan(d, [iss(1030, form(Judul="Judul BOOM", Tanggal="10 Okt 2026"))]) == []  # run berikutnya: tanpa komentar ulang
        h = jalankan(d, [iss(1030, form(Judul="Judul BOOM", Tanggal="10 Okt 2026", Catatan="diedit"))])  # isi berubah -> dicoba lagi
        assert h and h[0]["status"] == "gagal" and "kesalahan internal" in h[0]["komentar"]
    finally:
        core.bangun_event = asli
    h = jalankan(d, [iss(1030, form(Judul="Judul BOOM", Tanggal="10 Okt 2026", Catatan="diedit lagi"))])  # setelah diperbaiki: berhasil
    assert h and h[0]["status"] == "ok"


@uji("Q4: simulasi prune/build menolak perubahan yang akan merusak pipeline (tanpa menulis apa pun)")
def _():
    d = siapkan(); html = (d / "index.html").read_text(encoding="utf-8")
    assert ingest.simulasi_terbit(html, core.date.fromisoformat(TODAY)) is None
    assert "tidak ada kajian mendatang" in ingest.simulasi_terbit(html, core.date.fromisoformat("2035-01-01"))
    assert "prune tidak mengenali" in ingest.simulasi_terbit("<html></html>", core.date.fromisoformat(TODAY))
    rusak = html.replace("<!--STATIC_EVENTS_START-->", "<!--HILANG-->", 1)
    assert "penanda blok" in ingest.simulasi_terbit(rusak, core.date.fromisoformat(TODAY))
    n0 = len(events(d)); html0 = (d / "index.html").read_text(encoding="utf-8")
    asli = build.build_jsonld

    def pecah(*a, **k):
        raise RuntimeError("build rusak uji")
    build.build_jsonld = pecah
    try:
        h = jalankan(d, [iss(1040, form(Judul="Judul sim", Tanggal="10 Okt 2026"))])
    finally:
        build.build_jsonld = asli
    assert h[0]["status"] == "gagal" and "kesalahan internal" in h[0]["komentar"] and "uji prune/build gagal" in h[0]["komentar"], h[0]["komentar"]
    assert (d / "index.html").read_text(encoding="utf-8") == html0 and len(events(d)) == n0
    assert not any(x["issue"] == 1040 for x in kat(d)["diproses"])


@uji("Q4: kegagalan membuat templat formulir tidak menghalangi data terbit")
def _():
    d = siapkan(); asli = ad.render_template

    def pecah(*a, **k):
        raise RuntimeError("templat rusak uji")
    ad.render_template = pecah
    try:
        h = jalankan(d, [iss(1050, form(Judul="Judul templat", Tanggal="10 Okt 2026"))])
    finally:
        ad.render_template = asli
    assert h[0]["status"] == "ok" and any(e["title"] == "Judul templat" for e in events(d))


@uji("Q9: tanggal TANPA tahun lebih dari 180 hari ke depan ditolak (180 lolos, 181 ditolak); dengan tahun eksplisit tidak terkena batas")
def _():
    hari = core.date.fromisoformat(TODAY)
    bln = core.BULAN
    ok = hari + core.timedelta(days=180)
    lewat = hari + core.timedelta(days=181)
    d = siapkan()
    h = jalankan(d, [iss(1060, form(Judul="Tepat seratus delapan puluh", Tanggal=f"{ok.day} {bln[ok.month - 1]}"))])
    assert h[0]["status"] == "ok" and events(d)[-1]["date"] == ok.isoformat(), h[0]["komentar"]
    h = jalankan(d, [iss(1061, form(Judul="Lewat satu hari", Tanggal=f"{lewat.day} {bln[lewat.month - 1]}"))])
    assert h[0]["status"] == "gagal" and "tanpa tahun" in h[0]["komentar"] and f"{lewat.year}" in h[0]["komentar"], h[0]["komentar"]
    h = jalankan(d, [iss(1062, form(Judul="Angka tanpa tahun", Tanggal=f"{lewat.day}/{lewat.month}"))])
    assert h[0]["status"] == "gagal" and "tanpa tahun" in h[0]["komentar"]
    h = jalankan(d, [iss(1063, form(Judul="Tahun eksplisit", Tanggal=f"{lewat.day} {bln[lewat.month - 1]} {lewat.year}"))])
    assert h[0]["status"] == "ok" and events(d)[-1]["date"] == lewat.isoformat()
    h = jalankan(d, [iss(1064, form(Judul="Rentang tanpa tahun", Tanggal=f"{lewat.day}-{lewat.day} {bln[lewat.month - 1]}"))])
    assert h[0]["status"] == "gagal" and "tanpa tahun" in h[0]["komentar"]
    # Koreksi tanggal memakai pengurai yang sama
    ids = seri(d, n=1065, judul="Seri koreksi tanggal")
    h = jalankan(d, [iss(1066, fk("Koreksi", f"{ids[0]}", tanggal=f"{lewat.day} {bln[lewat.month - 1]}"))])
    assert h[0]["status"] == "gagal" and "tanpa tahun" in h[0]["komentar"], h[0]["komentar"]


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
