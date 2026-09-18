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
    "rotation": {"labels":["Fintech","SaaS","Deeptech","Consumer / D2C"], "values":[num,...], "cap":"..."},
    "gov":      {"labels":["scheme",...], "values":[crore_number,...], "cap":"..."}
  },
  "bigIdea": {"title":"short headline","lead":"...","body":"...","why":"..."},
  "trends": [ {"h":"1. ...","p":"what's happening","why":"why it matters"},
              {"h":"2. ...","p":"...","why":"..."},
              {"h":"3. ...","p":"...","why":"..."} ],
  "deals": [ {"amt":"$100M","sub":"Series C","co":"Company","sector":"sector","d":"one plain line"} ],
  "sources": [ {"t":"headline","s":"Source · why","url":"https://..."} ]  // 5 to 8 items
}
Rules: weekly.values are $ millions; rotation.values are multiples vs last year
(baseline 1.0); gov.values are in crore. Give 3 trends and 4-6 deals. Keep every
word very simple and ELI5. Figures are approximate. Do not add or remove keys.
"""
PROMPT = ("You are writing today's 'India VC, simply' edition for a beginner. "
          "Research the most important Indian venture-capital and startup news from "
          "the last 24-72 hours with web search, then fill in this data. " + SCHEMA)

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
    for k in ("stats","charts","bigIdea","trends","deals","sources"):
        if k not in d: raise ValueError("Missing key: "+k)
    for c in ("weekly","rotation","gov"):
        ch=d["charts"][c]
        if len(ch["labels"])!=len(ch["values"]) or not ch["values"]:
            raise ValueError("Chart "+c+" mismatch")
    if not (3 <= len(d["sources"]) <= 8): raise ValueError("Need 3-8 sources")
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
