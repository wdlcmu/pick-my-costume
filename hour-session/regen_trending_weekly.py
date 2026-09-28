#!/usr/bin/env python3
"""Weekly /trending regen for pickmycostume.com.

Pulls the trailing-7-day top 8 costume ideas from PostHog (pick_saved events,
verification probes/sims excluded), then regenerates the "Trending on Pick My
Costume" card grid in trending.html with a fresh month-precision dateline
("Updated <Month YYYY>.").

Usage:
    python3 regen_trending_weekly.py            # dry run: writes trending-regen-scratch/trending.regen.html
    python3 regen_trending_weekly.py --write    # writes the real trending.html (then deploy + verify live)
    python3 verify_trending_regen.py            # asserts the regen output has all 8 slugs + a valid dateline

Both modes emit trending.regen.json (top8 slugs, saves, window, dateline)
for the verification step.

The script never deploys. After --write, deploy trending.html via ./deploy.sh
and byte-verify the live page (Cloudflare propagation takes 5-10 minutes).

Method notes (see hub-pages-redteam-2026-09-26.md):
- Signal is pick_saved with properties.idea_id. quiz_completed carries no
  per-idea property, so saves are the per-idea engagement signal.
- Ties are broken by slug ascending so the output is deterministic.
- If fewer than 8 ideas have saves in the trailing 7 days, the window is
  widened to 14 then 30 days. If still fewer than 8, the script aborts rather
  than publishing a short or padded list.
"""

import html
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHAPI = os.path.expanduser("~/workspace/skills/posthog/bin/phapi")
TRENDING = os.path.join(BASE, "trending.html")
INDEX = os.path.join(BASE, "index.html")
PHOTOS = os.path.join(BASE, "photos")
OG = os.path.join(BASE, "images", "og")
# Scratch lives in hour-session (NOT /tmp: /tmp is wiped without warning).
SCRATCH = os.path.join(BASE, "hour-session", "trending-regen-scratch")

HOGQL = """SELECT properties.idea_id AS idea, count() AS saves
FROM events
WHERE event = 'pick_saved'
  AND timestamp >= now() - INTERVAL {days} DAY
  AND (properties.$current_url NOT LIKE '%?probe=%' OR properties.$current_url IS NULL)
  AND (properties.$current_url NOT LIKE '%?sim=%' OR properties.$current_url IS NULL)
GROUP BY idea
ORDER BY saves DESC
LIMIT 12"""


def query_top(days):
    r = subprocess.run([PHAPI, HOGQL.format(days=days)],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError("phapi failed (day window %d): %s" % (days, r.stderr[:300]))
    d = json.loads(r.stdout)
    if d.get("error"):
        raise RuntimeError("PostHog error: %s" % d["error"])
    rows = [(row[0], row[1]) for row in d.get("results", []) if row[0]]
    rows.sort(key=lambda x: (-x[1], x[0]))  # saves desc, slug asc (deterministic ties)
    return rows


def load_titles():
    lines = open(INDEX, encoding="utf-8").read().split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith("var IDEAS = ["))
    end = next(i for i in range(start, len(lines)) if lines[i].startswith("];"))
    block = "\n".join(lines[start:end])
    pairs = re.findall(r'id:"([a-z0-9-]+)", title:"((?:[^"\\]|\\.)*)"', block)
    if len(pairs) != 144 or len(set(p[0] for p in pairs)) != 144:
        raise RuntimeError("bank sanity failed: %d entries" % len(pairs))
    return dict(pairs)


def card_html(rank, slug, title, trends=None):
    fire = '<span class="fire">\U0001f525</span>' if rank <= 3 else ""
    t = html.escape(title, quote=True)
    # 2026-09-26 pm3 red-team: the About copy promises "each card shows its stat
    # and source". Only emit the stat line when the bank actually carries trend
    # data for this slug (never invent one for a weekly top-8 pick that the
    # bank does not flag as trending).
    stat = ""
    if trends and slug in trends:
        lane, s = trends[slug]
        stat = ('<span class="tstat">Trending &middot; %s: %s</span>'
                % (html.escape(lane, quote=True), html.escape(s, quote=True)))
    return ('    <a class="card" href="/c/%s"><img src="/photos/%s.webp" '
            'alt="%s costume" loading="lazy"><span class="n">%s#%d %s</span>%s</a>'
            % (slug, slug, t, fire, rank, t, stat))


def load_trends():
    """Map slug -> (trendLane, trendStat) from the index.html bank, only for
    ideas flagged trending:true. Records are newline-separated; parse each
    record independently so fields never leak across ideas."""
    text = open(INDEX, encoding="utf-8").read()
    start = text.index("var IDEAS = [")
    end = text.index("];", start)
    block = text[start:end]
    out = {}
    # Records start at line beginnings ("  {id:\"...\") so nested objects
    # (tags:{...}, venue:{...}) cannot split them.
    for rec in re.split(r'\n(?=  \{id:")', block):
        m = re.search(r'id:"([a-z0-9-]+)"', rec)
        if not m or "trending:true" not in rec:
            continue
        lane = re.search(r'trendLane:"((?:[^"\\]|\\.)*)"', rec)
        stat = re.search(r'trendStat:"((?:[^"\\]|\\.)*)"', rec)
        if lane and stat:
            out[m.group(1)] = (lane.group(1), stat.group(1))
    return out



def rail_html(rank, slug, title):
    badge = '<span class="proofbadge">\U0001f525 #%d</span>' % rank if rank <= 3 else ""
    t = html.escape(title, quote=True)
    return ('            <a href="/c/%s" role="listitem">%s<img src="photos/%s.webp" '
            'alt="%s costume" loading="lazy"><span>%s</span></a>'
            % (slug, badge, slug, t, t))

def main():
    write = "--write" in sys.argv

    # 1. Pull ranking, widening the window if data is thin.
    rows, used_days = None, None
    for days in (7, 14, 30):
        rows = query_top(days)
        if len(rows) >= 8:
            used_days = days
            break
    if used_days is None:
        raise SystemExit("ABORT: only %d ideas with saves in trailing 30 days; "
                         "not enough for a top-8 list." % len(rows))
    top8 = rows[:8]

    # 2. Resolve titles from the bank.
    titles = load_titles()
    for slug, saves in top8:
        if slug not in titles:
            raise SystemExit("ABORT: PostHog idea_id %r not in the costume bank." % slug)
    if len(set(s for s, _ in top8)) != 8:
        raise SystemExit("ABORT: duplicate slugs in top 8.")

    # 3. Asset checks: every card needs a photo and an OG card.
    for slug, _ in top8:
        if not os.path.exists(os.path.join(PHOTOS, slug + ".webp")):
            raise SystemExit("ABORT: missing photo for %s" % slug)
        if not os.path.exists(os.path.join(OG, slug + ".jpg")):
            raise SystemExit("ABORT: missing OG card for %s" % slug)

    # 4. Build the new grid block.
    trends = load_trends()
    cards = "\n".join(card_html(i + 1, slug, titles[slug], trends) for i, (slug, _) in enumerate(top8))
    new_grid = "  <div class=\"grid\">\n%s\n  </div>" % cards
    if re.search(r"[\u2013\u2014]", new_grid):
        raise SystemExit("ABORT: em/en dash in generated block.")

    # 5. Patch trending.html.
    src = open(TRENDING, encoding="utf-8").read()
    anchor = "<h2>\U0001f525 Trending on Pick My Costume</h2>"
    if anchor not in src:
        raise SystemExit("ABORT: on-site section anchor not found in trending.html.")
    head, rest = src.split(anchor, 1)
    m = re.search(r'  <div class="grid">\n.*?\n  </div>', rest, re.DOTALL)
    if not m:
        raise SystemExit("ABORT: card grid not found in trending.html.")
    rest = rest[:m.start()] + new_grid + rest[m.end():]

    today = datetime.now(ZoneInfo("America/Los_Angeles"))
    # Month-precision by design (red-team 2026-09-27): day-precision datelines
    # imply a freshness the weekly regen cannot honestly promise per-day.
    dateline = today.strftime("%B %Y")
    rest2, n1 = re.subn(r"Updated [A-Z][a-z]+ \d{4}\.",
                        "Updated %s." % dateline, rest, count=1)
    if n1 != 1:
        raise SystemExit("ABORT: dateline replacement failed (n1=%d)." % n1)

    # og:image follows the #1 idea. (It lives in <head>, before the section anchor.)
    head, n3 = re.subn(r'<meta property="og:image" content="https://pickmycostume.com/images/og/[a-z0-9-]+\.jpg">',
                       '<meta property="og:image" content="https://pickmycostume.com/images/og/%s.jpg">' % top8[0][0],
                       head, count=1)
    if n3 != 1:
        raise SystemExit("ABORT: og:image replacement failed.")

    out = head + anchor + rest2

    os.makedirs(SCRATCH, exist_ok=True)
    dest = TRENDING if write else os.path.join(SCRATCH, "trending.regen.html")
    open(dest, "w", encoding="utf-8").write(out)
    # Sidecar for the verification step (shared by dry-run and --write).
    open(os.path.join(SCRATCH, "trending.regen.json"), "w", encoding="utf-8").write(
        json.dumps({"slugs": [s for s, _ in top8],
                    "saves": [n for _, n in top8],
                    "window_days": used_days,
                    "dateline": dateline,
                    "page": dest}, indent=1))

    # 6. Keep the homepage "Trending" rail in sync (it is a static snapshot
    #    that would otherwise drift from /trending).
    rail = "\n".join(rail_html(i + 1, slug, titles[slug]) for i, (slug, _) in enumerate(top8))
    idx_src = open(INDEX, encoding="utf-8").read()
    rail_anchor = '<div class="proofrow" id="row-trending" role="tabpanel" aria-label="Popular costumes this week">'
    if rail_anchor not in idx_src:
        raise SystemExit("ABORT: row-trending anchor not found in index.html.")
    head_i, rest_i = idx_src.split(rail_anchor, 1)
    m_i = re.search(r'</div>', rest_i)
    if not m_i:
        raise SystemExit("ABORT: row-trending close not found in index.html.")
    rest_i = "\n" + rail + "\n          " + rest_i[m_i.start():]
    idx_out = head_i + rail_anchor + rest_i
    idx_dest = INDEX if write else os.path.join(SCRATCH, "index.regen.html")
    open(idx_dest, "w", encoding="utf-8").write(idx_out)

    print("window: trailing %d days" % used_days)
    print("top 8 (idea_id: saves):")
    for i, (slug, saves) in enumerate(top8, 1):
        print("  #%d %-20s %s (%d saves)" % (i, slug, titles[slug], saves))
    print("dateline: Updated %s" % dateline)
    print("wrote: %s" % dest)
    if not write:
        print("dry run only. Re-run with --write to update trending.html, then deploy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
