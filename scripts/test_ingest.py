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
         "Pemateri": "Belum ditentukan", "Pemateri baru": "", "Pemateri perempuan": "", "Masjid": "Masjid Al-Adhim",
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
    pem = next(p for p in k["pemateri"] if "," in p)
    n0 = len(events(d)); id0 = core.id_berikutnya((d / "index.html").read_text(encoding="utf-8"))
    h = jalankan(d, [iss(1, form(Jenis_waktu="Jam eksak", Jam="19.30", Pemateri=ad.tampil(pem), Kajian_rutin="- [x] Kajian rutin atau berkala", Catatan="Catatan uji"))])
    assert h[0]["status"] == "ok", h
    ev = events(d)
    assert len(ev) == n0 + 1
    e = ev[-1]
    assert e["id"] == id0 and e["date"] == "2026-10-10" and e["dayShort"] == "Sab 10 Okt", e
    assert e["timeLabel"] == "19.30 WIB" and e["timeOrder"] == 19.5 and e["ustadz"] == pem and e["isRutin"] is True
    assert e["area"] == k["masjid"]["Masjid Al-Adhim"]["kota"] and e["audience"] == "Terbuka untuk umum"
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
    assert "Semarang" in k["kota"] and k["masjid"]["Masjid Uji Baru"] == {"kota": "Semarang", "alamat": "Jl. Uji 1"} and "Ustadz Uji Baru" in k["pemateri"]
    tpl = (d / ".github/ISSUE_TEMPLATE/tambah-kajian.yml").read_text(encoding="utf-8")
    assert "Masjid Uji Baru" in tpl and "Semarang" in tpl and "Ustadz Uji Baru" in tpl


@uji("nama baru yang sama (huruf beda) memakai yang lama; yang mirip diberi peringatan")
def _():
    d = siapkan(); k = kat(d)
    lama = next(iter(k["masjid"]))
    h = jalankan(d, [iss(5, form(Masjid=ad.LAINNYA, Nama_masjid_baru=lama.upper(), Alamat_masjid_baru="x", Kota_masjid_baru="Bogor"))])
    assert events(d)[-1]["masjid"] == lama and not kat(d)["masjid"].get(lama.upper())
    h = jalankan(d, [iss(6, form(Masjid=ad.LAINNYA, Nama_masjid_baru=lama + "a", Alamat_masjid_baru="x", Kota_masjid_baru="Bogor"))])
    assert "mirip" in h[0]["komentar"], h[0]["komentar"]


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
        form(Tanggal="2026-10-02"), form(Tanggal="10-10-2026"), form(Tanggal="2026-02-30"), form(Tanggal="2031-01-01"),
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
    assert jalankan(d, [iss(43, form(), title="Pertanyaan biasa")]) == []


@uji("id berlanjut dari max di main terbaru (simulasi konflik: ingest ulang di atas hasil lain)")
def _():
    a = siapkan(); b = siapkan()
    jalankan(a, [iss(50, form(Judul="A"))]); jalankan(b, [iss(51, form(Judul="B"))])
    assert events(a)[-1]["id"] == events(b)[-1]["id"]  # bentrok bila keduanya dipush
    shutil.copy(b / "index.html", a / "index.html"); shutil.copy(b / "data" / "kategori.json", a / "data" / "kategori.json")  # = reset ke main terbaru
    h = jalankan(a, [iss(50, form(Judul="A"))])
    ids = [e["id"] for e in events(a)]
    assert len(ids) == len(set(ids)) and h[0]["id"] == [events(a)[-1]["id"]]


@uji("templat YAML sah: 15 unsur, id unik, opsi dropdown unik tanpa koma ASCII, label = kunci parser")
def _():
    import yaml
    t = yaml.safe_load(ad.render_template(core.muat_kategori(REPO / "data" / "kategori.json")))
    assert t["title"] == ad.JUDUL_ISSUE and len(t["body"]) == 15
    ids = [x["id"] for x in t["body"]]; assert len(ids) == len(set(ids))
    assert [x["attributes"]["label"] for x in t["body"]] == [ad.LABEL[k] for k in ad.LABEL]
    for x in t["body"]:
        if x["type"] == "dropdown":
            o = x["attributes"]["options"]
            assert len(o) == len(set(o)) and not any("," in s for s in o), x["id"]


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
