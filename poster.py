#!/usr/bin/env python3
"""Render a shareable poster PNG (1080x1350, @2x) for an edition.
Usage: python3 poster.py [YYYY-MM-DD]   (defaults to today)
Runs in the pipeline after build.py. Needs Playwright + Chromium (the workflow
installs them). The poster design lives in poster.html; only data changes."""
import sys, datetime, pathlib
from playwright.sync_api import sync_playwright

date = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
folder = pathlib.Path("editions") / date
tpl = pathlib.Path("poster.html").read_text(encoding="utf-8")
data = (folder / "data.js").read_text(encoding="utf-8")
html = tpl.replace('<script src="data.js"></script>', "<script>\n" + data + "\n</script>")
tmp = folder / "_poster.html"
tmp.write_text(html, encoding="utf-8")

with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=2)
    pg.goto(tmp.resolve().as_uri())
    pg.wait_for_timeout(800)  # let the embedded font settle
    pg.screenshot(path=str(folder / "poster.png"),
                  clip={"x": 0, "y": 0, "width": 1080, "height": 1350})
    b.close()
tmp.unlink(missing_ok=True)
print("Wrote", folder / "poster.png")
