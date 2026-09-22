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

Dijalankan otomatis di .github/workflows/weekly-deploy.yml setelah prune.py.
Tidak menyentuh baris event di allEvents maupun stempel "Diperbarui:" —
regex prune.py tetap valid.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

FILE = Path(__file__).resolve().parent.parent / "index.html"
TZ = ZoneInfo("Asia/Jakarta")
SITE_URL = "https://jadwalkajian.netlify.app/"

EVENT_LINE_RX = re.compile(r'^\s*\{id:\d+,date:"\d{4}-\d{2}-\d{2}".*\},\s*$')
KNOWN_KEYS = ["id", "date", "dayShort", "timeLabel", "timeOrder", "title",
              "ustadz", "masjid", "area", "address", "audience", "note", "isRutin"]
KEY_RX = re.compile(r'([{,]\s*)(' + "|".join(KNOWN_KEYS) + r'):')

AC = {
    "Bogor": {"accent": "#d4a55a", "badge": "#5c4a2d"},
    "Depok": {"accent": "#5a9fd4", "badge": "#2d4a5c"},
    "Jakarta": {"accent": "#b07ad4", "badge": "#3a2a5c"},
    "Bekasi": {"accent": "#d4705a", "badge": "#5c2a1e"},
    "Jawa Tengah": {"accent": "#5ad49a", "badge": "#1e5c3a"},
    "Jawa Barat": {"accent": "#d45a8a", "badge": "#5c1e35"},
    "Online": {"accent": "#8a8ad4", "badge": "#2d2d5c"},
}

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
    return datetime.now(TZ).date().isoformat()


def decimal_hour_to_clock(h):
    hh = int(h)
    mm = round((h - hh) * 60)
    return f"{hh:02d}:{mm:02d}:00"


def start_datetime_iso(ev):
    return f"{ev['date']}T{decimal_hour_to_clock(ev['timeOrder'])}+07:00"


def render_static_card(ev):
    col = AC.get(ev["area"], AC["Depok"])
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
    return pattern.sub(start_marker + new_inner + end_marker, html, count=1)


def main():
    html = FILE.read_text(encoding="utf-8")
    events = parse_events(html)
    if not events:
        print("ERROR: tidak ada event terdeteksi — parser rusak?", file=sys.stderr)
        return 1

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
