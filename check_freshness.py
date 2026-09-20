#!/usr/bin/env python3
"""Mechanically fails if TODAY's edition repeats content from any of the last
few editions — a hard backstop behind the "don't repeat yourself" instructions
already in daily-prompt.txt / build.py's prompt, which are just words an LLM
could still get wrong. This is a deterministic check, not an LLM call.

Usage: python3 check_freshness.py [YYYY-MM-DD]   (defaults to today)
Exit 0 = fresh (or nothing to compare against). Exit 1 = looks like a repeat —
fix editions/TODAY/data.js and run again before publishing.

Also importable: build.py calls find_repeats() directly on in-memory briefs
instead of re-reading them from disk.
"""
import sys, re, json, datetime, pathlib

def load_brief(date):
    f = pathlib.Path("editions") / date / "data.js"
    if not f.exists():
        return None
    t = f.read_text(encoding="utf-8")
    a, b = t.find("{"), t.rfind("}")
    if a == -1 or b == -1:
        return None
    try:
        return json.loads(t[a:b + 1])
    except Exception:
        return None

def recent_edition_dates(today, n=3):
    """Up to n most recent edition dates strictly before today, newest first."""
    folder = pathlib.Path("editions")
    if not folder.exists():
        return []
    dates = sorted((d.name for d in folder.iterdir()
                     if d.is_dir() and re.match(r"\d{4}-\d{2}-\d{2}$", d.name) and d.name < today),
                    reverse=True)
    return dates[:n]

def previous_edition_date(today):
    """Back-compat single-date helper — the single most recent prior edition."""
    dates = recent_edition_dates(today, 1)
    return dates[0] if dates else None

def _norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())

def find_repeats(today_brief, prev_brief):
    """Returns a list of human-readable problems; empty list means fresh."""
    problems = []

    t_title = _norm((today_brief.get("bigIdea") or {}).get("title"))
    p_title = _norm((prev_brief.get("bigIdea") or {}).get("title"))
    if t_title and t_title == p_title:
        problems.append("bigIdea.title is identical to the previous edition: \"%s\"" % t_title)

    t_deals = {_norm(d.get("co")) for d in today_brief.get("deals", []) if d.get("co")}
    p_deals = {_norm(d.get("co")) for d in prev_brief.get("deals", []) if d.get("co")}
    if t_deals and t_deals == p_deals:
        problems.append("deals[] is the exact same set of companies as the previous edition")

    t_trends = {_norm(x.get("h")) for x in today_brief.get("trends", []) if x.get("h")}
    p_trends = {_norm(x.get("h")) for x in prev_brief.get("trends", []) if x.get("h")}
    overlap = t_trends & p_trends
    if overlap:
        problems.append("trends[] repeats a headline from the previous edition: " + "; ".join(sorted(overlap)))

    t_cotd = {_norm(x.get("headline")) for x in today_brief.get("chartsOfTheDay", []) if x.get("headline")}
    p_cotd = {_norm(x.get("headline")) for x in prev_brief.get("chartsOfTheDay", []) if x.get("headline")}
    overlap = t_cotd & p_cotd
    if overlap:
        problems.append("chartsOfTheDay[] repeats a headline from the previous edition: " + "; ".join(sorted(overlap)))

    t_sector = _norm((today_brief.get("history") or {}).get("sector"))
    p_sector = _norm((prev_brief.get("history") or {}).get("sector"))
    if t_sector and t_sector == p_sector:
        problems.append("history.sector is the same backstory sector as the previous edition: \"%s\"" % t_sector)

    return problems

def check_against_recent(today_brief, recent_briefs):
    """recent_briefs: list of (date, brief) tuples, newest first. Returns a list
    of (date, problems) pairs for editions today_brief collides with."""
    hits = []
    for date, brief in recent_briefs:
        problems = find_repeats(today_brief, brief)
        if problems:
            hits.append((date, problems))
    return hits

def main():
    today = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    today_brief = load_brief(today)
    if today_brief is None:
        sys.exit("No readable data.js for " + today + " — write it first, then run this.")

    dates = recent_edition_dates(today, 3)
    if not dates:
        print("No previous editions to compare against — nothing to check.")
        return
    recent_briefs = []
    for d in dates:
        brief = load_brief(d)
        if brief is not None:
            recent_briefs.append((d, brief))

    hits = check_against_recent(today_brief, recent_briefs)
    if hits:
        print("FRESHNESS CHECK FAILED — " + today + " looks too similar to recent editions:")
        for date, problems in hits:
            print("  vs " + date + ":")
            for p in problems:
                print("    - " + p)
        sys.exit(1)
    print("Freshness check passed: " + today + " differs from the last " + str(len(recent_briefs)) + " edition(s) (" + ", ".join(dates) + ").")

if __name__ == "__main__":
    main()
