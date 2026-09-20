#!/usr/bin/env python3
"""
Daily builder. Researches the day's Indian VC news via Claude, then PUBLISHES A
NEW DATED EDITION at editions/YYYY-MM-DD/ and adds it to the archive (editions.js).
The landing page (index.html) and the edition design (edition-template.html) never
change, so nothing can break — each day just adds a new page.

Run locally:  ANTHROPIC_API_KEY=sk-... python3 build.py
The GitHub Actions workflow runs this every morning.
"""
import os, sys, json, datetime, urllib.request, pathlib, shutil, re

API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not API_KEY:
    sys.exit("Set ANTHROPIC_API_KEY first.")

SCHEMA = """
Return ONLY a JSON object (no prose, no code fences) with exactly these keys:
{
  "stats": [ {"n":"$14.9B","l":"short label"}, {"n":"...","l":"..."}, {"n":"...","l":"..."} ],
  "charts": {
    "weekly":   {"labels":["wk1","wk2","wk3"], "values":[num,num,num], "cap":"one plain sentence"},
    "rotation": {
      "monthly":   {"labels":["sector",...], "values":[num,...], "cap":"one plain sentence"},
      "quarterly": {"labels":["sector",...], "values":[num,...], "cap":"one plain sentence"},
      "annual":    {"labels":["sector",...], "values":[num,...], "cap":"one plain sentence"}
    },
    "gov":      {"labels":["scheme",...], "values":[crore_number,...], "cap":"..."}
  },
  "bigIdea": {"title":"short headline","lead":"...","body":"...","why":"..."},
  "trends": [ {"h":"1. ...","p":"what's happening","why":"why it matters"},
              {"h":"2. ...","p":"...","why":"..."},
              {"h":"3. ...","p":"...","why":"..."} ],
  "deals": [ {"amt":"$100M","sub":"Series C","co":"Company","sector":"sector","d":"one plain line"} ],
  "investors": [ {"firm":"VC firm name","country":"country it's based in","focus":"what they usually back","deal":"which deal this week ties to them"} ],
  "deck": {
    "summary":"2-3 plain sentences on the day, written like a consulting exec summary",
    "takeaways":["...","...","..."],
    "implications":["...","...","..."]
  },
  "sources": [ {"t":"headline","s":"Source · why","url":"https://..."} ]  // 5 to 8 items
}
Rules: weekly.values are $ millions. Each of charts.rotation's three windows (monthly,
quarterly, annual) carries the 5-8 sectors most relevant to THAT period — the sets of
sectors can differ between windows — with values as multiples vs the same-length prior
period (baseline 1.0; e.g. quarterly values are vs last quarter, monthly vs last month).
gov.values are in crore. Give 3 trends and 4-6 deals. Give 4-8 investors: real VC firms
actually behind this week's deals, each one's "deal" naming which deal ties to it.
deck.takeaways and deck.implications are each exactly 3 short bullets; deck.summary is
2-3 plain sentences framed like a consulting exec summary of the day. Keep every word
very simple and ELI5. Figures are approximate. Do not add or remove keys.
"""
PROMPT = ("You are writing today's 'India VC, simply' edition for a beginner. "
          "Research the most important Indian venture-capital and startup news from "
          "the last 24-72 hours with web search — including which VC firms are behind "
          "the week's headline deals — then fill in this data. " + SCHEMA)

def call_claude():
    body = {"model":"claude-sonnet-4-6","max_tokens":4000,
            "messages":[{"role":"user","content":PROMPT}],
            "tools":[{"type":"web_search_20250305","name":"web_search"}]}
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",
        data=json.dumps(body).encode(),
        headers={"content-type":"application/json","x-api-key":API_KEY,"anthropic-version":"2023-06-01"})
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.load(r)
    return "".join(b.get("text","") for b in resp.get("content",[]) if b.get("type")=="text")

def extract_json(text):
    a,b = text.find("{"), text.rfind("}")
    if a==-1 or b==-1: raise ValueError("No JSON in model reply.")
    return json.loads(text[a:b+1])

def validate(d):
    for k in ("stats","charts","bigIdea","trends","deals","investors","deck","sources"):
        if k not in d: raise ValueError("Missing key: "+k)
    charts = d["charts"]
    for c in ("weekly","gov"):
        ch=charts[c]
        if len(ch["labels"])!=len(ch["values"]) or not ch["values"]:
            raise ValueError("Chart "+c+" mismatch")
    rot = charts.get("rotation") or {}
    if "labels" in rot:  # back-compat: a flat window counts as "annual"
        rot = {"annual": rot}
    windows = {k: v for k, v in rot.items() if k in ("monthly","quarterly","annual")}
    if not windows:
        raise ValueError("charts.rotation needs at least one of monthly/quarterly/annual")
    for name, win in windows.items():
        if len(win.get("labels",[])) != len(win.get("values",[])) or not win.get("values"):
            raise ValueError("Chart rotation."+name+" mismatch")
    if not (3 <= len(d["sources"]) <= 8): raise ValueError("Need 3-8 sources")
    if not (3 <= len(d["investors"]) <= 10): raise ValueError("Need 3-10 investors")
    if not d["deck"].get("summary"): raise ValueError("deck needs a summary")
    return True

def load_editions():
    p = pathlib.Path("editions.js")
    if not p.exists(): return []
    t = p.read_text(encoding="utf-8")
    a,b = t.find("["), t.rfind("]")
    if a==-1 or b==-1: return []
    try: return json.loads(t[a:b+1])
    except Exception: return []

def save_editions(items):
    out = ("/* List of all editions, newest first. The pipeline prepends a new entry each day. */\n"
           "window.EDITIONS = " + json.dumps(items, ensure_ascii=False, indent=2) + ";\n")
    pathlib.Path("editions.js").write_text(out, encoding="utf-8")

def main():
    data = extract_json(call_claude())
    validate(data)
    today = datetime.date.today()
    date = today.isoformat()
    label = today.strftime("%-d %B %Y")
    data["dateLabel"] = label

    folder = pathlib.Path("editions")/date
    folder.mkdir(parents=True, exist_ok=True)
    (folder/"data.js").write_text(
        "/* auto-generated */\nwindow.BRIEF = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8")
    tpl = pathlib.Path("edition-template.html").read_text(encoding="utf-8")
    base = "https://nebulatris.github.io/editions/" + date + "/"
    tpl = tpl.replace("__OGURL__", base).replace("__OGIMAGE__", base + "poster.png")
    (folder/"index.html").write_text(tpl, encoding="utf-8")

    items = load_editions()
    items = [e for e in items if e.get("date") != date]  # replace if re-run same day
    items.insert(0, {"date":date, "label":label,
                     "url":"editions/"+date+"/", "headline":data["bigIdea"]["title"]})
    items.sort(key=lambda e: e["date"], reverse=True)
    save_editions(items)

    # Tweet caption for YOUR personal use (gitignored — never pushed to the repo).
    # Also printed below so you can copy it from the Actions run log.
    title = data["bigIdea"]["title"]
    lead = data["bigIdea"]["lead"].replace('"', "").replace("\u201c", "").replace("\u201d", "").strip()
    if len(lead) > 90:
        lead = lead[:87].rsplit(" ", 1)[0] + "…"
    url = "https://nebulatris.github.io/editions/" + date + "/"
    caption = ("India VC, simply — " + label + "\n\n" +
               title + " — " + lead + "\n\nFull 5-min edition:\n" + url +
               "\n\n#India #Startups #VentureCapital")
    (folder/"tweet.txt").write_text(caption, encoding="utf-8")
    print("\n----- TWEET (copy this; not committed) -----\n" + caption + "\n--------------------------------------------\n")

    print("Published edition for", label, "->", "editions/"+date+"/")

if __name__ == "__main__":
    main()
