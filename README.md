# India VC, simply — a self-publishing daily briefing

A beautiful landing page plus a growing archive of daily editions on Indian venture
capital, hosted **free** on GitHub Pages. Each morning a pipeline adds a **new dated
page** — nothing is overwritten.

The site is live at **https://nebulatris.github.io**.

## What's in the folder
- `index.html` — the **landing page** (explains the site, shows the latest edition, lists the archive).
- `editions.js` — the archive list. The pipeline adds one line per day.
- `edition-template.html` — the design of a single edition. Fixed, so it can never break.
- `editions/YYYY-MM-DD/` — one folder per day: a copy of the template + that day's `data.js`.
- `build.py` — researches the news and creates today's edition folder.
- `.github/workflows/publish.yml` — runs `build.py` every morning and commits.

**The idea:** design and data are separate. `index.html` and `edition-template.html`
never change. Each day the pipeline only *adds* a new `editions/<date>/` folder and one
line to `editions.js`. So the site keeps a full history and the design stays rock-solid.

---

## Notes
- Learning project, **not investment advice**. Figures are approximate -- verify before quoting.
- `build.py` validates the AI output; if anything looks wrong it stops without writing,
  so a bad generation can never break your live site.

---
