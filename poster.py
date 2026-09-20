#!/usr/bin/env python3
"""Render a shareable poster for an edition: a static PNG (1080x1350, @2x) showing
the fully-revealed design, and an animated GIF (1080x1350, 1x) that plays the same
page's motion-graphic build: headline/takeaway fade in, the deal-of-the-day band
pops in with its amount counting up, sector-momentum bars grow in staggered with
their multiples counting up, and the three stat numbers count up — then holds
before looping.

Usage: python3 poster.py [YYYY-MM-DD]   (defaults to today)
Runs in the pipeline after build.py. Needs Playwright + Chromium (the workflow
installs them) and Pillow for the GIF (pip install pillow). The poster design
lives in poster.html; only data changes."""
import sys, io, datetime, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image
from poster_gif import save_gif

date = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
folder = pathlib.Path("editions") / date
tpl = pathlib.Path("poster.html").read_text(encoding="utf-8")
data = (folder / "data.js").read_text(encoding="utf-8")
html = tpl.replace('<script src="data.js"></script>', "<script>\n" + data + "\n</script>")
tmp = folder / "_poster.html"
tmp.write_text(html, encoding="utf-8")

# poster.html's motion-graphic build finishes revealing everything by ~2.4s
# (see its JS timeline). The GIF plays the full build, holds on the finished
# state for a beat, then loops (an abrupt cut back to blank is normal for this
# style of animated infographic). The static PNG is captured after the hold
# begins, so it shows the complete, settled state rather than a mid-build frame.
BUILD_SETTLE_MS = 2800
GIF_DURATION_MS = 3800
GIF_FRAMES = 30
GIF_STEP_MS = GIF_DURATION_MS // GIF_FRAMES

with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox"])

    # Static PNG, @2x for crisp sharing / OG-image use — captured post-build.
    pg = b.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=2)
    pg.goto(tmp.resolve().as_uri())
    pg.wait_for_timeout(BUILD_SETTLE_MS)
    pg.screenshot(path=str(folder / "poster.png"),
                  clip={"x": 0, "y": 0, "width": 1080, "height": 1350})
    pg.close()

    # Animated GIF, 1x (keeps file size reasonable for sharing/upload limits).
    # Only a brief settle before frame 0 — the build starts at 100ms, so waiting
    # long here (like the PNG does) would skip straight past the reveal.
    pg = b.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
    pg.goto(tmp.resolve().as_uri())
    pg.wait_for_timeout(60)
    frames = []
    for i in range(GIF_FRAMES):
        if i:
            pg.wait_for_timeout(GIF_STEP_MS)
        png_bytes = pg.screenshot(clip={"x": 0, "y": 0, "width": 1080, "height": 1350})
        frames.append(Image.open(io.BytesIO(png_bytes)).convert("RGB"))
    pg.close()
    b.close()

save_gif(frames, folder / "poster.gif", GIF_STEP_MS)

tmp.unlink(missing_ok=True)
print("Wrote", folder / "poster.png")
print("Wrote", folder / "poster.gif")
