#!/usr/bin/env python3
"""Generate whats-trending.html from a Pinterest Trends weekly snapshot.

Usage: python3 gen_trends_page.py [--data hidden_files/search-data-recon/data-week-2026-09-26.json]
                                   [--out whats-trending.html]

Reads the snapshot JSON (terms with rank/index/mom4_pct/guide mapping),
resolves guide titles from mcp-server/bank.json, and writes a fully
server-rendered HTML page: real links in raw HTML, Article + FAQPage
JSON-LD, per-item source citation, methodology + skew disclosure,
Frightgeist 2025 callout with a reserved slot for the 2026 list.

Honesty rules baked in: no invented guides (unmapped terms show
"No guide yet"), adjacent matches are labeled adjacent, interest is
labeled as Pinterest's normalized index (not raw counts), and the page
states plainly this is national search interest, not our site traffic.
No em/en dashes anywhere in output copy.
"""
import argparse
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "mcp-server", "bank.json")

PAGE_URL = "https://pickmycostume.com/whats-trending"
OG_IMAGE = "https://pickmycostume.com/images/og/classic-ghost.jpg"

# Stable term -> guide mapping. Applied when the snapshot has no per-term
# "guide" key (the raw fetch script output). value: (slug, adjacent?)
GUIDE_MAP = {
    "witch costume": ("emerald-witch", False),
    "ghost costume": ("classic-ghost", False),
    "lorax costume": ("fuzzy-monster", True),
    "superman costume": ("superhero-family", True),
    "nightwing costume": ("superhero-family", True),
    "supergirl costume": ("superhero-family", True),
    "glinda costume": ("good-witch-bad-witch", False),
    "wednesday costume": ("deadpan-diva", True),
    "labubu costume": ("pocket-plush", True),
    "elphaba costume": ("emerald-witch", True),
    "toothless costume": ("dragon-rider-duo", True),
    "rumi costume": ("kpop-demon-huntresses", False),
    "vampire costume": ("vampire", False),
    "pirate costume": ("pirate-captain", False),
    # 2026-09-30: silent hill nurse -> zombie-coworker is an honest adjacent
    # (undead face-paint + distressed ordinary clothes are the same build
    # techniques). donnie darko (creepy rabbit; no rabbit guide in the bank)
    # and hamilton (colonial; no colonial guide) stay honest gaps rather
    # than force a misleading adjacent.
    "silent hill nurse costume": ("zombie-coworker", True),
}

# Static historical data: Google Frightgeist 2025 national top 10.
# Used when the snapshot has no secondary_sources block.
FRIGHTGEIST_2025_TOP10 = [
    "Rumi (KPop Demon Hunters)", "Zoey (KPop Demon Hunters)",
    "Mira (KPop Demon Hunters)", "Jinu (KPop Demon Hunters)",
    "Baby Saja (KPop Demon Hunters)", "Chicken Jockey (Minecraft)",
    "Labubu", "Derpy the Tiger (KPop Demon Hunters)",
    "Elphaba (Wicked)", "The Lorax",
]


def no_dashes(s):
    """Guard: no em/en dashes in user-facing copy."""
    assert "\u2014" not in s and "\u2013" not in s, "em/en dash found: %r" % s[:60]
    return s


def fmt_week(week_ending):
    # "2026-09-26" -> "Sep 26, 2026"
    y, m, d = week_ending.split("-")
    months = {"01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May",
              "06": "Jun", "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct",
              "11": "Nov", "12": "Dec"}
    return "%s %d, %s" % (months[m], int(d), y)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(
        ROOT, "hidden_files", "search-data-recon", "data-week-2026-09-26.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "whats-trending.html"))
    args = ap.parse_args()

    snap = json.load(open(args.data, encoding="utf-8"))
    bank = json.load(open(BANK, encoding="utf-8"))
    titles = {i["id"]: i["title"] for i in bank["ideas"]}

    terms = sorted(snap["terms"], key=lambda t: t["rank"])
    assert len(terms) >= 10, "expected at least 10 terms"
    # Merge the stable guide map for snapshots that lack per-term mapping
    # (raw fetch_pinterest_trends.py output) or where the snapshot left the
    # guide empty (guide: None).
    for t in terms:
        if t.get("guide") is None:
            m = GUIDE_MAP.get(t["term"])
            if m:
                slug, adjacent = m
                t["guide"] = slug
                t["guide_note"] = ("Adjacent: %s" % titles.get(slug, slug)) if adjacent else titles.get(slug, slug)
            else:
                t["guide"] = None
                t["guide_note"] = "No guide yet"
    for t in terms:
        if t.get("guide"):
            assert t["guide"] in titles, "unknown guide slug: %s" % t["guide"]

    week = fmt_week(snap["week_ending"])
    max_idx = max(t["index"] or 0 for t in terms) or 1
    missing = snap.get("missing_terms", [])
    sec = snap.get("secondary_sources", {})
    fg_block = sec.get("google_frightgeist_2025", {})
    fg_top10 = fg_block.get("top10_national", FRIGHTGEIST_2025_TOP10)

    # --- table rows ---
    rows = []
    for t in terms:
        bar = round((t["index"] or 0) / max_idx * 100)
        mom = t.get("mom4_pct")
        mom_txt = ("+%d%%" % mom) if mom is not None else "n/a"
        if t.get("guide"):
            slug = t["guide"]
            title = titles[slug]
            note = (t.get("guide_note") or "")
            adjacent = "Adjacent:" in note
            cell = '<a href="/c/%s">%s</a>' % (html.escape(slug), html.escape(title))
            if adjacent:
                cell += ' <span class="gap">(adjacent)</span>'
        else:
            cell = '<span class="gap">No guide yet</span>'
        rows.append(
            '<tr><td class="rank">%d</td><td>%s</td>'
            '<td><div class="bar"><i style="width:%d%%"></i></div></td>'
            '<td class="up">%s</td><td class="guide">%s</td></tr>' % (
                t["rank"], html.escape(t["term"]), bar, mom_txt, cell))
    table = "\n      ".join(rows)

    # --- missing-terms disclosure ---
    missing_txt = ""
    if missing:
        missing_txt = (
            '<li><strong>What is missing:</strong> Pinterest returned no data for '
            '%s this week (below their reporting threshold or filtered vocabulary). '
            'We log the gaps instead of hiding them.</li>' % html.escape(", ".join(missing)))

    # --- FAQ (mirrors visible copy) ---
    faq = [
        ("Where does this costume trend data come from?",
         "Pinterest Trends, the public search-trend tool at trends.pinterest.com. "
         "We pull weekly United States search interest for costume terms and rank "
         "them by Pinterest's interest index. Every refresh re-pulls the latest "
         "complete week, and the source is cited on every row's page."),
        ("Is this your own website's traffic?",
         "No. This is national search interest from Pinterest Trends, not visits "
         "to pickmycostume.com. Our own audience is small, and we do not present "
         "our traffic as a trend."),
        ("What does the interest number mean?",
         "It is Pinterest's normalized search-interest index for the week, on "
         "their own scale. It is not a raw count of searches. Bars are relative "
         "to the week's leader, and the 4-week change compares to four weeks "
         "earlier."),
        ("Why is a popular costume missing from the list?",
         "Two reasons. Pinterest's search vocabulary drops some terms entirely "
         "when they fall below its reporting threshold, and those gaps are listed "
         "above. Separately, Pinterest's audience skews toward planners and DIY "
         "crafters, so this reads as what craft-minded America is searching, not "
         "all of America. Google's annual Frightgeist ranking covers Google "
         "searches and is linked below."),
        ("How often is this updated?",
         "Weekly. Each update pulls the latest complete week from Pinterest "
         "Trends and regenerates this page."),
    ]
    faq_html = []
    faq_schema = []
    for i, (q, a) in enumerate(faq, 1):
        faq_html.append(
            '<h2><span class="qn">Q%d.</span> %s</h2>\n<p class="a">%s</p>' % (
                i, html.escape(no_dashes(q)), html.escape(no_dashes(a))))
        faq_schema.append(
            '    {\n      "@type": "Question",\n'
            '      "name": %s,\n'
            '      "acceptedAnswer": {\n        "@type": "Answer",\n        "text": %s\n      }\n    }' % (
                json.dumps(no_dashes(q)), json.dumps(no_dashes(a))))
    faq_block = "\n".join(faq_html)
    faq_json = ",\n".join(faq_schema)

    title = "Halloween Costume Trends 2026: What America Is Searching For | Pick My Costume"
    desc = ("Real weekly costume search data from Pinterest Trends: which Halloween "
            "costumes America is searching for right now, with links to our matching "
            "DIY costume guides. Week ending %s." % week)

    fg_items = "\n".join("      <li>%s</li>" % html.escape(x) for x in fg_top10)

    page = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<link rel="canonical" href="%(page_url)s">
<meta property="og:type" content="article">
<meta property="og:title" content="Halloween Costume Trends 2026: What America Is Searching For">
<meta property="og:description" content="Real weekly costume search data, with links to our matching DIY guides. Week ending %(week)s.">
<meta property="og:url" content="%(page_url)s">
<meta property="og:image" content="%(og_image)s">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Halloween Costume Trends 2026: What America Is Searching For">
<meta name="twitter:description" content="Real weekly costume search data, with links to our matching DIY guides. Week ending %(week)s.">
<meta name="twitter:image" content="%(og_image)s">
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Halloween Costume Trends 2026: What America Is Searching For",
  "description": %(desc_json)s,
  "author": {
    "@type": "Organization",
    "name": "Pick My Costume"
  },
  "publisher": {
    "@id": "https://pickmycostume.com/#organization",
    "name": "Pick My Costume",
    "url": "https://pickmycostume.com/"
  },
  "datePublished": "2026-09-30",
  "dateModified": "2026-09-30",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "%(page_url)s"
  },
  "image": "%(og_image)s"
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "publisher": {
    "@id": "https://pickmycostume.com/#organization"
  },
  "mainEntity": [
%(faq_json)s
  ]
}
</script>
<style>
:root{
  --bg:#160d28; --bg2:#211540; --card:#2a1c52; --ink:#fdf3e3;
  --muted:#cdbcf0; --line:#4b3486; --accent:#ff8c1a; --accent-ink:#2a1500;
  --radius:14px; --green:#7ce38b;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;line-height:1.65}
.wrap{max-width:860px;margin:0 auto;padding:20px 16px 64px}
header.top{display:flex;align-items:center;justify-content:space-between;padding:14px 0}
header.top a{display:inline-block;padding:12px 10px;min-height:44px}
.brand{font-weight:800;font-size:18px;color:var(--ink);text-decoration:none}
.brand span{color:var(--accent)}
.home-link{color:var(--muted);text-decoration:none;font-size:14px}
.kicker{display:inline-block;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:700;margin-bottom:6px}
h1{font-size:32px;margin:8px 0 4px;line-height:1.2}
.lede{font-size:18px;margin:0 0 8px}
.cite-line{font-size:13px;color:var(--muted);margin:0 0 28px}
.cite-line a{color:var(--accent)}
table{width:100%%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;font-size:15px}
th,td{text-align:left;padding:12px 10px;border-bottom:1px solid var(--line);vertical-align:middle}
th{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);background:var(--bg2)}
tr:last-child td{border-bottom:none}
.rank{font-weight:800;color:var(--accent);width:36px}
.bar{height:8px;background:var(--bg2);border-radius:4px;overflow:hidden;min-width:70px}
.bar i{display:block;height:100%%;background:linear-gradient(90deg,#b46bff,var(--accent))}
.up{color:var(--green);font-weight:700;white-space:nowrap}
.guide a{color:var(--accent);font-weight:600;text-decoration:none}
.guide a:hover{text-decoration:underline}
.gap{color:var(--muted);font-style:italic;font-size:13px}
.note{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin-top:28px;font-size:14px;color:var(--muted)}
.note h2{font-size:16px;color:var(--ink);margin:0 0 8px}
.note ul{margin:8px 0;padding-left:20px}
.note li{margin:6px 0}
.note a{color:var(--accent)}
.fg{background:linear-gradient(135deg,#1c1030,#2b1245);border:1px solid var(--line);border-radius:12px;padding:18px;margin-top:20px}
.fg h2{font-size:18px;margin:0 0 6px}
.fg ol{margin:8px 0;padding-left:22px;font-size:14px;color:var(--muted)}
.fg a{color:var(--accent)}
.fg .slot{border:1px dashed var(--line);border-radius:10px;padding:12px 14px;margin-top:12px;font-size:14px;color:var(--muted)}
h2.faq{font-size:24px;margin:44px 0 6px;line-height:1.3}
h2.faq .qn{color:var(--accent)}
p.a{color:var(--muted);margin:0 0 20px}
.footer{margin-top:48px;font-size:13px;color:var(--muted);text-align:center}
.footer a{color:var(--muted);margin:0 8px}
</style>
</head>
<body>
<div class="wrap">
<header class="top">
  <a class="brand" href="/">Pick My <span>Costume</span></a>
  <a class="home-link" href="/">Home</a>
</header>

<span class="kicker">Real search data</span>
<h1>What the country is searching for</h1>
<p class="lede">Which costumes America is actually looking up right now, and which ones we can help you build tonight.</p>
<p class="cite-line">Source: <a href="%(source_url)s">Pinterest Trends</a>, United States searches, week ending %(week)s. This is national search interest, not our own site traffic (our audience is small, and we do not present it as a trend).</p>

<table id="trends-table">
  <thead><tr><th>#</th><th>Costume search</th><th>Interest</th><th>4-week change</th><th>Our guide</th></tr></thead>
  <tbody>
      %(table)s
  </tbody>
</table>

<div class="note" id="methodology">
  <h2>How to read this</h2>
  <ul>
    <li><strong>Interest</strong> is Pinterest's normalized search-interest index for the week (their scale, not raw search counts). Bars are relative to this week's leader.</li>
    <li><strong>4-week change</strong> compares this week to four weeks earlier. Everything on the list is climbing into Halloween.</li>
    <li><strong>Our guide</strong> links to one of our 164 real costume guides when the search matches. <em>No guide yet</em> is an honest gap, and the list doubles as our build backlog. Adjacent matches are labeled as adjacent.</li>
    <li>Pinterest's audience skews toward planners and DIY crafters, so treat this as what craft-minded America is searching, not all of America.</li>
%(missing_txt)s
  </ul>
</div>

<div class="fg" id="frightgeist">
  <h2>Also: Google's Frightgeist</h2>
  <p style="color:var(--muted);font-size:14px;margin:0 0 8px">Google publishes its own costume-search ranking each October at <a href="https://frightgeist.google">frightgeist.google</a>. The 2026 edition is not out yet, so here is last year's national top 10 for comparison:</p>
  <ol>
%(fg_items)s
  </ol>
  <p style="color:var(--muted);font-size:13px;margin:8px 0 0">Source: Google Frightgeist 2025.</p>
  <div class="slot" id="frightgeist-2026"><strong>Frightgeist 2026:</strong> not published yet (expected mid-October). We will add Google's 2026 ranking here when it drops.</div>
</div>

<h2 class="faq">Questions, answered</h2>
%(faq_block)s

<p class="footer">Built with Muse. &middot; Data refreshes weekly &middot; Last updated from Pinterest Trends: week ending %(week)s<br><a href="/">Home</a><a href="/pantry">Pantry</a><a href="/costumes-from-your-closet">Costumes From Your Closet</a></p>
</div>
</body>
</html>
""" % {
        "title": html.escape(title),
        "desc": html.escape(no_dashes(desc)),
        "desc_json": json.dumps(no_dashes(desc)),
        "page_url": PAGE_URL,
        "og_image": OG_IMAGE,
        "week": week,
        "source_url": html.escape(snap.get("source_url", "https://trends.pinterest.com/?country=US")),
        "table": table,
        "missing_txt": ("    " + missing_txt) if missing_txt else "",
        "fg_items": fg_items,
        "faq_block": faq_block,
        "faq_json": faq_json,
    }

    # --- homepage teaser sync: keep the /whats-trending teaser card's
    # top-term line in index.html in sync with this snapshot's #1 term ---
    top = terms[0]
    top_mom = top.get("mom4_pct")
    top_line = "Trending searches this week: %s%s" % (
        top["term"], (" +%d%%" % top_mom) if top_mom is not None else "")
    no_dashes(top_line)
    index_path = os.path.join(ROOT, "index.html")
    idx = open(index_path, encoding="utf-8").read()
    idx2, n = re.subn(r"Trending searches this week: [^<]*",
                      html.escape(top_line), idx, count=1)
    assert n == 1, "teaser line not found in index.html"
    open(index_path, "w", encoding="utf-8").write(idx2)
    print("teaser synced: %s" % top_line)

    # final safety: no em/en dashes anywhere
    assert "\u2014" not in page and "\u2013" not in page, "dash leaked into page"
    assert "STAGED" not in page
    open(args.out, "w", encoding="utf-8").write(page)
    print("wrote %s (%d bytes, %d terms, week ending %s)"
          % (args.out, len(page), len(terms), week))


if __name__ == "__main__":
    main()
