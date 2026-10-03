#!/usr/bin/env python3
"""
Generate static SEO content untuk index.html Jadwal Kajian:
  - HTML statis event (di dalam #cards-container, antara marker
    <!--STATIC_EVENTS_START--> ... <!--STATIC_EVENTS_END-->) supaya crawler
    yang tidak menjalankan JavaScript tetap melihat isi kajian.
  - JSON-LD schema.org/Event (antara marker <!--LD_JSON_START--> ...
    <!--LD_JSON_END--> di <head>).

JavaScript (render()) tetap jalan seperti biasa dan langsung menimpa isi
#cards-container saat halaman dibuka — HTML statis ini hanya untuk crawler
dan tampilan sebelum JS selesai load (progressive enhancement), bukan
pengganti interaktivitas filter.

Dijalankan otomatis di .github/workflows/deploy.yml setelah prune.py.
Tidak menyentuh baris event di allEvents maupun stempel "Diperbarui:" —
regex prune.py tetap valid.
"""

import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

FILE = Path(__file__).resolve().parent.parent / "index.html"
TZ = ZoneInfo("Asia/Jakarta")
SITE_URL = "https://reconciler.github.io/jadwalkajian/"

# Penanda struktur array event di index.html (sama dengan prune.py). Daftar kosong hanya sah bila keduanya ada.
ARRAY_AWAL = re.compile(r"^const allEvents=\[\s*$", re.M)
ARRAY_AKHIR = re.compile(r"^\];\s*$", re.M)


def punya_array_events(html):
    """True bila `const allEvents=[` ada dan disusul penutup `];` (struktur utuh, walau tanpa baris event)."""
    m = ARRAY_AWAL.search(html)
    return bool(m and ARRAY_AKHIR.search(html, m.end()))


def array_events_kosong(html):
    """True bila struktur array utuh DAN badannya hanya spasi/baris kosong (daftar benar-benar kosong).
    Badan berisi baris yang tidak dikenali parser = format berubah/parser rusak, BUKAN daftar kosong."""
    m = ARRAY_AWAL.search(html)
    if not m:
        return False
    a = ARRAY_AKHIR.search(html, m.end())
    return bool(a and html[m.end():a.start()].strip() == "")


EVENT_LINE_RX = re.compile(r'^\s*\{id:\d+,date:"\d{4}-\d{2}-\d{2}".*\},\s*$')
KNOWN_KEYS = ["id", "date", "dayShort", "timeLabel", "timeOrder", "title",
              "ustadz", "masjid", "area", "address", "audience", "note", "isRutin"]
KEY_RX = re.compile(r'([{,]\s*)(' + "|".join(KNOWN_KEYS) + r'):')

def city_color(name):
    """Warna kota otomatis, stabil per nama. Algoritma HARUS sama dengan cc() di index.html
    (FNV-1a atas UTF-8 "b"+nama, hue = hash % 360)."""
    x = 2166136261
    for byte in ("b" + name).encode("utf-8"):
        x ^= byte
        x = (x * 16777619) & 0xFFFFFFFF
    hue = x % 360
    return {"accent": f"hsl({hue},58%,62%)", "badge": f"hsl({hue},36%,25%)"}

def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def parse_events(html):
    events = []
    for line in html.splitlines():
        if not EVENT_LINE_RX.match(line):
            continue
        obj_text = line.strip().rstrip(",")
        json_text = KEY_RX.sub(r'\1"\2":', obj_text)
        events.append(json.loads(json_text))
    return events


def today_iso():
    # JADWAL_HARI_INI hanya untuk uji otomatis (hasil tidak bergantung jam asli); produksi tidak memakainya.
    if os.environ.get("JADWAL_HARI_INI"):
        return date.fromisoformat(os.environ["JADWAL_HARI_INI"]).isoformat()
    return datetime.now(TZ).date().isoformat()


def decimal_hour_to_clock(h):
    hh = int(h)
    mm = round((h - hh) * 60)
    return f"{hh:02d}:{mm:02d}:00"


def start_datetime_iso(ev):
    return f"{ev['date']}T{decimal_hour_to_clock(ev['timeOrder'])}+07:00"


def render_static_card(ev):
    col = city_color(ev["area"])
    rutin = '<div class="rutin-label">RUTIN</div>' if ev.get("isRutin") else ""
    return (
        f'<article class="card" itemscope itemtype="https://schema.org/Event">'
        f'<div class="card-body"><div class="card-time">{rutin}'
        f'<div class="card-date">{esc(ev["dayShort"])}</div>'
        f'<div class="card-time-label">{esc(ev["timeLabel"])}</div></div>'
        f'<div class="card-divider"></div><div class="card-content">'
        f'<h3 class="card-title" itemprop="name">{esc(ev["title"])}</h3>'
        f'<div class="card-ustadz" itemprop="performer">{esc(ev["ustadz"])}</div>'
        f'<div class="card-tags">'
        f'<span class="area-tag" style="background:{col["badge"]};color:{col["accent"]}">'
        f'<span class="dot-sm" style="background:{col["accent"]}"></span>{esc(ev["area"])}</span>'
        f'<span class="masjid-tag" itemprop="location">{esc(ev["masjid"])}</span>'
        f'</div>'
        f'<p class="detail-static">Alamat: {esc(ev["address"])} &middot; Peserta: {esc(ev["audience"])}'
        + (f' &middot; {esc(ev["note"])}' if ev.get("note") else "")
        + f'</p>'
        f'<meta itemprop="startDate" content="{start_datetime_iso(ev)}">'
        f'</div></div></article>'
    )


def build_static_html(events):
    if not events:
        return '<p class="empty">Belum ada kajian mendatang.</p>'
    return "".join(render_static_card(e) for e in events)


def build_jsonld(events):
    items = []
    for ev in events:
        items.append({
            "@type": "Event",
            "name": ev["title"],
            "startDate": start_datetime_iso(ev),
            "eventAttendanceMode": (
                "https://schema.org/OnlineEventAttendanceMode"
                if ev["area"] == "Online"
                else "https://schema.org/OfflineEventAttendanceMode"
            ),
            "eventStatus": "https://schema.org/EventScheduled",
            "location": {
                "@type": "Place",
                "name": ev["masjid"],
                "address": ev["address"],
            },
            "performer": {"@type": "Person", "name": ev["ustadz"]},
            "isAccessibleForFree": True,
            "description": ev.get("note") or f'{ev["title"]} bersama {ev["ustadz"]} di {ev["masjid"]}.',
        })
    payload = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": items,
    }
    return (
        '<script type="application/ld+json">'
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        + "</script>"
    )


def replace_between(html, start_marker, end_marker, new_inner):
    pattern = re.compile(
        re.escape(start_marker) + r'.*?' + re.escape(end_marker), re.S
    )
    if not pattern.search(html):
        print(f"ERROR: marker {start_marker} tidak ditemukan.", file=sys.stderr)
        sys.exit(1)
    # Fungsi sebagai pengganti: new_inner memuat teks pengguna; string pengganti akan menafsirkan backslash
    # (\\s, \\1, \\n) dan merusak build.
    return pattern.sub(lambda _m: start_marker + new_inner + end_marker, html, count=1)


def main():
    html = FILE.read_text(encoding="utf-8")
    events = parse_events(html)
    if not events:
        # Daftar kosong sah (semua event kedaluwarsa) HANYA bila struktur array utuh; selain itu parser/berkas rusak.
        if not array_events_kosong(html):
            print("ERROR: tidak ada event terdeteksi padahal allEvents tidak kosong (atau strukturnya hilang) — parser rusak?",
                  file=sys.stderr)
            return 1
        print("Catatan: daftar event kosong (semua kedaluwarsa); membuat blok statis dan JSON-LD kosong.")

    today = today_iso()
    upcoming = sorted(
        (e for e in events if e["date"] >= today),
        key=lambda e: (e["date"], e["timeOrder"]),
    )

    updated = replace_between(html, "<!--STATIC_EVENTS_START-->", "<!--STATIC_EVENTS_END-->",
                               build_static_html(upcoming))
    updated = replace_between(updated, "<!--LD_JSON_START-->", "<!--LD_JSON_END-->",
                               "\n" + build_jsonld(upcoming) + "\n")

    if updated == html:
        print(f"Tidak ada perubahan. Event upcoming: {len(upcoming)}.")
        return 0

    FILE.write_text(updated, encoding="utf-8")
    print(f"Build statis+JSON-LD selesai. Event upcoming: {len(upcoming)} dari {len(events)} total.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
