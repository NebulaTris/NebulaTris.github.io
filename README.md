# India VC, simply — a self-publishing daily briefing

A beautiful landing page plus a growing archive of daily editions on Indian venture
capital, hosted **free** on GitHub Pages. Each morning a pipeline adds a **new dated
page** — nothing is overwritten.

Your site will live at **https://nebulatris.github.io**.

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

## 1. Put it online (~5 minutes, no coding)
1. Sign in at **github.com** -> **+ -> New repository**.
2. Name it exactly **`NebulaTris.github.io`**. Set **Public** -> **Create**.
3. **Add file -> Upload files.** Drag in EVERYTHING here, keeping the folder structure
   (including the `editions/` and `.github/workflows/` folders). Commit.
4. **Settings -> Pages ->** Source: **Deploy from a branch**, Branch **main**, **/(root)** -> Save.
5. Wait a minute, open **https://nebulatris.github.io**. Live, showing the landing page
   and the first edition.

## 2. Turn on daily auto-publishing (~2 minutes)
1. Get an API key at **console.anthropic.com**.
2. Repo **Settings -> Secrets and variables -> Actions -> New repository secret**:
   name **`ANTHROPIC_API_KEY`**, paste your key.
3. Done. Each morning a new dated edition appears and the archive grows. Trigger it now
   any time: **Actions tab -> Daily publish -> Run workflow**.

> Prefer doing it by hand? Copy the `editions/2026-09-18/` folder to a new date, edit its
> `data.js`, and add a line to `editions.js`. The site updates in about a minute.

## 3. Turn on the view counter (~2 minutes)
Uses **GoatCounter** (free, no cookies).
1. Sign up at **goatcounter.com**, pick a code (e.g. `nebulavc`).
2. In BOTH `index.html` and `edition-template.html`, replace `YOURCODE` with your code.
3. The top-right pill shows total views, plus a full dashboard.

No-signup alternative (instant): replace the counter pill with
`<img src="https://hits.sh/nebulatris.github.io.svg?label=views&color=12795a" alt="views">`

---

## Notes
- Learning project, **not investment advice**. Figures are approximate -- verify before quoting.
- `build.py` validates the AI output; if anything looks wrong it stops without writing,
  so a bad generation can never break your live site.

---

## 4. Daily poster + caption (post to X yourself)

Each edition generates:
- a shareable poster at `editions/<date>/poster.png` (1080x1350), and
- a ready caption at `editions/<date>/tweet.txt` **for your personal use**.

`tweet.txt` is listed in `.gitignore`, so it is **never pushed to the repo** — it
stays private. During each automated run the caption is also printed in the
**Actions run log** (open the run -> "Build today's edition" step) so you can copy
it from there. Then post the poster + caption to X yourself.

Each edition page also uses its poster as the social-share preview image, so pasting
an edition link on X/WhatsApp/LinkedIn shows the poster automatically.
