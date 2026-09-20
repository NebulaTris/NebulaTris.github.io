#!/usr/bin/env python3
"""Render a shareable poster PNG for EACH "chart of the day" item in an edition —
the a16z-tweet-style single-claim card: punchy headline, stat bullets, one
hand-drawn chart (bar/doughnut/line — no Chart.js, so rendering never depends
on network access), source line. One static PNG (1080x1350, @2x) per item.

Usage: python3 cotd_poster.py [YYYY-MM-DD]   (defaults to today)
Run after poster.py. Needs Playwright + Chromium. The design lives in
cotd-poster.html; only data changes. No-ops (prints a note, exits 0) if the
edition has no chartsOfTheDay."""
import sys, json, datetime, pathlib
from playwright.sync_api import sync_playwright

date = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
folder = pathlib.Path("editions") / date
data_path = folder / "data.js"
data_text = data_path.read_text(encoding="utf-8")
a, b = data_text.find("{"), data_text.rfind("}")
brief = json.loads(data_text[a:b + 1])
items = brief.get("chartsOfTheDay") or []
if not items:
    print("No chartsOfTheDay in", data_path, "— nothing to render.")
    sys.exit(0)

tpl = pathlib.Path("cotd-poster.html").read_text(encoding="utf-8")

# cotd-poster.html's build finishes revealing everything (bullets, chart) by
# ~2.2s — capture after that so the PNG shows the settled, fully-drawn state.
BUILD_SETTLE_MS = 2600

with sync_playwright() as p:
    b_ = p.chromium.launch(args=["--no-sandbox"])
    for i, item in enumerate(items):
        html = tpl.replace(
            '<script src="data.js"></script>',
            "<script>window.COTD_INDEX=" + str(i) + ";\n" + data_text + "\n</script>",
        )
        tmp = folder / ("_cotd_poster_%d.html" % i)
        tmp.write_text(html, encoding="utf-8")
        stem = "cotd-%d" % (i + 1)

        pg = b_.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=2)
        pg.goto(tmp.resolve().as_uri())
        pg.wait_for_timeout(BUILD_SETTLE_MS)
        pg.screenshot(path=str(folder / (stem + ".png")),
                      clip={"x": 0, "y": 0, "width": 1080, "height": 1350})
        pg.close()

        tmp.unlink(missing_ok=True)
        print("Wrote", folder / (stem + ".png"))
    b_.close()
