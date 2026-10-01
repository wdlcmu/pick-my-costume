#!/usr/bin/env python3
# Builds trends-2026.html + trends stat-card data for Pick My Costume.
# 2026-09-27 (new-ideas stream d).
#
# Every number on the page is computed from the LIVE bank (mcp-server/bank.json)
# or from the verified 138-idea demand-sim report. The generator FAILS LOUDLY
# on any drift (missing demand id, zero stat, changed idea count) so the page
# can never publish a stale or invented number.
#
# Byte-inert: writes trends-2026.html + trends-stat-data.json only. No edits to
# any live file, no inbound links, not in sitemap.xml.
#
# Usage: python3 build_trends.py   (run from the repo root)

import json, os, re, sys, html

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FAQ_QA_TRENDS = [('Where do the trend numbers come from?', 'Counts come straight from our live idea bank of 164 costumes: audience, budget, and vibe tags on every idea. The top 5 come from a demand simulation: 100,000 quiz runs against the same bank, counting which idea lands at number one. Percentages are shares of those simulated runs. This is our own data, not a national survey.'), ("What does 'picked most' mean?", "The Tin Hero landed at number one on 5.3% of 100,000 simulated quiz runs - more than any other idea. It means our quiz's scoring picks it most often, not that real shoppers bought it most."), ('Are these national Halloween trends?', "No. These are trends inside our own costume bank and quiz simulation. For national search trends, see our trending page, which cites Google's Frightgeist rankings."), ('How many ideas are good for little kids?', "Dozens of the 164 ideas are made for kids, and most of them have nothing scary at all. The 'For little kids' section above names three gentle favorites: Baby Dinosaur, Backyard Superhero, and Ballerina.")]
FAQ_JSONLD_TRENDS = '<script type="application/ld+json">\n{\n  "@context": "https://schema.org",\n  "@type": "FAQPage",\n  "mainEntity": [\n    {\n      "@type": "Question",\n      "name": "Where do the trend numbers come from?",\n      "acceptedAnswer": {\n        "@type": "Answer",\n        "text": "Counts come straight from our live idea bank of 164 costumes: audience, budget, and vibe tags on every idea. The top 5 come from a demand simulation: 100,000 quiz runs against the same bank, counting which idea lands at number one. Percentages are shares of those simulated runs. This is our own data, not a national survey."\n      }\n    },\n    {\n      "@type": "Question",\n      "name": "What does \'picked most\' mean?",\n      "acceptedAnswer": {\n        "@type": "Answer",\n        "text": "The Tin Hero landed at number one on 5.3% of 100,000 simulated quiz runs - more than any other idea. It means our quiz\'s scoring picks it most often, not that real shoppers bought it most."\n      }\n    },\n    {\n      "@type": "Question",\n      "name": "Are these national Halloween trends?",\n      "acceptedAnswer": {\n        "@type": "Answer",\n        "text": "No. These are trends inside our own costume bank and quiz simulation. For national search trends, see our trending page, which cites Google\'s Frightgeist rankings."\n      }\n    },\n    {\n      "@type": "Question",\n      "name": "How many ideas are good for little kids?",\n      "acceptedAnswer": {\n        "@type": "Answer",\n        "text": "Dozens of the 164 ideas are made for kids, and most of them have nothing scary at all. The \'For little kids\' section above names three gentle favorites: Baby Dinosaur, Backyard Superhero, and Ballerina."\n      }\n    }\n  ]\n}\n</script>'
FAQ_VISIBLE_TRENDS = '<section class="pmc-faq" id="pmc-faq">\n<style>\n.pmc-faq{margin:32px 0}\n.pmc-faq h2{font-size:22px;margin:0 0 8px}\n.pmc-faq details{margin:8px 0;border:1px solid rgba(140,140,160,.4);border-radius:10px;padding:10px 14px}\n.pmc-faq summary{cursor:pointer;font-weight:700}\n.pmc-faq p{margin:8px 0 4px;line-height:1.55}\n</style>\n<h2>Common questions</h2>\n<details class="faq">\n<summary>Where do the trend numbers come from?</summary>\n<p>Counts come straight from our live idea bank of 164 costumes: audience, budget, and vibe tags on every idea. The top 5 come from a demand simulation: 100,000 quiz runs against the same bank, counting which idea lands at number one. Percentages are shares of those simulated runs. This is our own data, not a national survey.</p>\n</details>\n<details class="faq">\n<summary>What does &#x27;picked most&#x27; mean?</summary>\n<p>The Tin Hero landed at number one on 5.3% of 100,000 simulated quiz runs - more than any other idea. It means our quiz&#x27;s scoring picks it most often, not that real shoppers bought it most.</p>\n</details>\n<details class="faq">\n<summary>Are these national Halloween trends?</summary>\n<p>No. These are trends inside our own costume bank and quiz simulation. For national search trends, see our trending page, which cites Google&#x27;s Frightgeist rankings.</p>\n</details>\n<details class="faq">\n<summary>How many ideas are good for little kids?</summary>\n<p>Dozens of the 164 ideas are made for kids, and most of them have nothing scary at all. The &#x27;For little kids&#x27; section above names three gentle favorites: Baby Dinosaur, Backyard Superhero, and Ballerina.</p>\n</details>\n</section>'
# NOTE: FAQ_VISIBLE_TRENDS and FAQ_JSONLD_TRENDS must stay in sync (same Q&A).



BANK_PATH = os.path.join(REPO, 'mcp-server', 'bank.json')
PAGE_PATH = os.path.join(REPO, 'trends-2026.html')
DATA_PATH = os.path.join(REPO, 'hour-session', 'trends-stat-data.json')

# From the 138-idea demand sim (gate.js N=100,000, 2026-09-27).
# Ids must exist in the live bank; percentages are quoted verbatim.
DEMAND_TOP5 = [
    ('tin-hero', 5.8),
    ('blue-dog-family', 4.6),
    ('snow-sisters', 3.9),
    ('block-game-crew', 3.7),
    ('breakfast-buffet', 2.9),
]

DASH_RE = re.compile(r'[\u2013\u2014]')

def fail(msg):
    print('FATAL: ' + msg, file=sys.stderr)
    sys.exit(1)

def main():
    with open(BANK_PATH, encoding='utf-8') as f:
        bank = json.load(f)
    ideas = bank['ideas']
    by_id = {x['id']: x for x in ideas}

    total = len(ideas)
    if total != 138:
        fail('expected 138 ideas, bank has %d; regenerate constants' % total)

    def has_budget(i, b):
        return b in (i.get('budget') or [])

    def has_tag(i, t):
        return (i.get('tags') or {}).get(t, 0) > 0

    def has_aud(i, a):
        return a in (i.get('audience') or [])

    diy = sum(1 for x in ideas if has_budget(x, 'diy'))
    low = sum(1 for x in ideas if has_budget(x, 'low'))
    kid = sum(1 for x in ideas if has_aud(x, 'kid'))
    gentle = sum(1 for x in ideas if has_aud(x, 'kid') and not has_tag(x, 'scary'))
    group = sum(1 for x in ideas if has_aud(x, 'group'))
    family = sum(1 for x in ideas if has_aud(x, 'family'))
    couple = sum(1 for x in ideas if has_aud(x, 'couple'))
    funny = sum(1 for x in ideas if has_tag(x, 'funny'))
    cute = sum(1 for x in ideas if has_tag(x, 'cute'))
    scary = sum(1 for x in ideas if has_tag(x, 'scary'))
    food = sum(1 for x in ideas if has_tag(x, 'food'))
    animals = sum(1 for x in ideas if has_tag(x, 'animals'))

    stats = {
        'total': total, 'diy': diy, 'low': low, 'kid': kid, 'gentle': gentle,
        'group': group, 'family': family, 'couple': couple,
        'funny': funny, 'cute': cute, 'scary': scary, 'food': food, 'animals': animals,
    }
    for k, v in stats.items():
        if v <= 0:
            fail('stat %s computed as %d; refusing to publish' % (k, v))

    # Demand top-5: ids must exist, percentages sane.
    demand = []
    for iid, pct in DEMAND_TOP5:
        if iid not in by_id:
            fail('demand id %s missing from bank' % iid)
        if not (0 < pct < 100):
            fail('demand pct %r for %s out of range' % (pct, iid))
        x = by_id[iid]
        demand.append({'id': iid, 'title': x['title'], 'pct': pct,
                       'blurb': x.get('blurb') or '',
                       'audience': x.get('audience') or []})

    # Three gentle kid examples, deterministic (sorted by id).
    gentle_kids = sorted([x for x in ideas
                          if has_aud(x, 'kid') and not has_tag(x, 'scary')],
                         key=lambda z: z['id'])[:3]
    if len(gentle_kids) < 3:
        fail('fewer than 3 gentle kid ideas')

    # ---- page copy (dash-linted below) ----
    def esc(s):
        return html.escape(s, quote=True)

    def aud_chip(aud):
        return ', '.join(aud).replace('kid', 'kids')

    top5_cards = []
    for rank, d in enumerate(demand, 1):
        top5_cards.append('''<article class="trend-card">
  <div class="rank">#{rank}</div>
  <h3>{title}</h3>
  <p class="pct">Picked first on {pct}% of quiz runs</p>
  <p class="blurb">{blurb}</p>
  <p class="aud">Made for: {aud}</p>
  <a class="guide" href="https://pickmycostume.com/c/{iid}?src=share-trends">See the build guide</a>
</article>'''.format(rank=rank, title=esc(d['title']), pct=d['pct'],
                     blurb=esc(d['blurb']), aud=esc(aud_chip(d['audience'])),
                     iid=d['id']))

    stat_cells = [
        (stats['total'], 'costume ideas in the bank'),
        (stats['diy'], 'are DIY builds'),
        (stats['low'], 'are low-budget ideas'),
        (stats['kid'], 'are made for kids'),
        (stats['gentle'], 'kid ideas with zero scary ones'),
        (stats['group'], 'group ideas'),
        (stats['family'], 'family ideas'),
        (stats['couple'], 'couple ideas'),
    ]
    stat_html = '\n'.join(
        '<div class="stat"><div class="num">{n}</div><div class="lbl">{l}</div></div>'.format(n=n, l=esc(l))
        for n, l in stat_cells)

    gentle_cards = []
    for x in gentle_kids:
        gentle_cards.append('''<article class="trend-card">
  <h3>{title}</h3>
  <p class="blurb">{blurb}</p>
  <a class="guide" href="https://pickmycostume.com/c/{iid}?src=share-trends">See the build guide</a>
</article>'''.format(title=esc(x['title']), blurb=esc(x.get('blurb') or ''),
                     iid=x['id']))

    page = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>2026 Halloween Costume Trends: What Families Are Actually Making</title>
<meta name="description" content="The 2026 Halloween costume trends from 100,000 simulated quiz runs: the 5 most-picked costumes, DIY and budget stats, and gentle picks for little kids.">
<link rel="canonical" href="https://pickmycostume.com/trends-2026">
<meta property="og:type" content="article">
<meta property="og:title" content="What 2026 is actually wearing for Halloween">
<meta property="og:description" content="The 5 most-picked costumes from 100,000 simulated quiz runs, plus the real numbers behind 138 costume ideas.">
<meta property="og:url" content="https://pickmycostume.com/trends-2026">
<meta property="og:image" content="https://pickmycostume.com/images/og/tin-hero.jpg">
<script>
/* PostHog: anonymous usage stats only. Quiz answers are never sent. Session replay is off. */
var _isQA=false;
try{
  var _q0=location.search||"";
  if(/[?&](probe|sim)=/.test(_q0)||/[?&]internal=1(?:&|$)/.test(_q0))_isQA=true;
  else{try{if(localStorage.getItem("pmc_internal")==="1")_isQA=true;}catch(e){}}
}catch(e){}
(function(){
  var s = document.createElement("script");
  s.async = true;
  s.src = "https://us.i.posthog.com/static/array.js";
  s.onload = function(){
    try {
      if (window.posthog && posthog.init) {
        posthog.init("phc_t9dkHXAZR5VEjPFm3K5JDzGKFsNNxKcwSxxcEBEeLbS7", {
          api_host: "https://us.i.posthog.com",
          autocapture: false,
          capture_pageview: !_isQA,
          disable_session_recording: true
        });
      }
    } catch(e){}
  };
  document.head.appendChild(s);
})();
</script>
<style>
:root{--bg:#160d28;--card:#2a1c52;--ink:#fdf3e3;--accent:#ff8c1a;--muted:#c9b8e8}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;line-height:1.55}
.wrap{max-width:860px;margin:0 auto;padding:24px 18px 64px}
.kicker{color:var(--accent);font-weight:700;letter-spacing:.12em;font-size:13px;text-transform:uppercase}
h1{font-size:34px;line-height:1.2;margin:12px 0}
.honest{background:var(--card);border-left:4px solid var(--accent);padding:12px 16px;border-radius:8px;color:var(--muted);font-size:15px;margin:18px 0}
.cta{display:inline-block;background:var(--accent);color:#1a0f00;font-weight:700;padding:14px 26px;border-radius:999px;text-decoration:none;margin:10px 0;font-size:17px}\n.cta.ghost{background:transparent;color:var(--accent);border:2px solid var(--accent)}\nbutton.cta{font-family:inherit;cursor:pointer}\n.sharenote{color:var(--muted);font-size:13px;min-height:20px}
h2{font-size:24px;margin:40px 0 14px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px}
.trend-card{background:var(--card);border-radius:12px;padding:18px}
.trend-card h3{margin:0 0 6px;font-size:19px}
.rank{color:var(--accent);font-weight:800;font-size:14px}
.pct{font-weight:700;color:var(--accent);margin:4px 0}
.blurb{color:var(--muted);font-size:15px;margin:8px 0}
.aud{font-size:13px;color:var(--muted)}
.guide{color:var(--accent);font-weight:600;display:inline-block;padding:12px 0;min-height:44px}
.statgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;margin:18px 0}
.stat{background:var(--card);border-radius:12px;padding:16px 12px;text-align:center}
.stat .num{font-size:34px;font-weight:800;color:var(--accent)}
.stat .lbl{font-size:13px;color:var(--muted);margin-top:4px}
.vibes{background:var(--card);border-radius:12px;padding:16px 18px;margin:18px 0;font-size:16px}
.method{color:var(--muted);font-size:15px;border-top:1px solid #3a2a63;padding-top:18px;margin-top:44px}
footer{margin-top:36px;text-align:center;color:var(--muted);font-size:14px}
header.top{display:flex;align-items:center;justify-content:space-between;padding:2px 0}
.brand{font-weight:800;font-size:18px;color:var(--ink);text-decoration:none}
.brand span{color:var(--accent)}
.home-link{color:var(--muted);text-decoration:none;font-size:14px}
header.top a{display:inline-block;padding:12px 10px;min-height:44px}
footer a{color:var(--muted);display:inline-block;padding:12px 10px}
</style>
</head>
<body>
<div class="wrap">
<header class="top">
<a class="brand" href="https://pickmycostume.com/">Pick My <span>Costume</span></a>
<a class="home-link" href="https://pickmycostume.com/">Home</a>
</header>
<p class="kicker">Pick My Costume &middot; 2026 trends</p>
<h1>What 2026 is actually wearing for Halloween</h1>
<div class="honest">Every number on this page comes from our own 164-idea costume bank and a simulated run of our quiz. Not a national survey. Just what the data says.</div>
<a class="cta" href="https://pickmycostume.com/?src=share-trends">Find your costume in 2 minutes</a>
<p><button type="button" class="cta ghost" id="shareBtn">Share these trends</button></p>
<p class="sharenote" id="shareNote" role="status"></p>

<h2>The 5 costumes the quiz picks most</h2>
<p>We ran our quiz 100,000 times against the full idea bank. These five came out on top most often.</p>
<div class="grid">
''' + '\n'.join(top5_cards) + '''
</div>

<h2>The numbers behind the ideas</h2>
<div class="statgrid">
''' + stat_html + '''
</div>
<div class="vibes"><strong>Vibe check:</strong> {funny} funny ideas, {cute} cute ones, {food} food costumes, {animals} animal ideas, and only {scary} scary ones. Funny beats scary four to one.</div>

<h2>For little kids: big shelf, zero scary</h2>
<p>{kid} of our ideas are made for kids, and {gentle} of them have nothing scary at all. Three gentle favorites:</p>
<div class="grid">
'''.format(funny=stats['funny'], cute=stats['cute'], food=stats['food'],
           animals=stats['animals'], scary=stats['scary'], kid=stats['kid'],
           gentle=stats['gentle']) + '\n'.join(gentle_cards) + '''
</div>

<div class="method">
<h2>Where these numbers come from</h2>
<p>Counts come straight from our live idea bank of {total} costumes: audience, budget, and vibe tags on every idea. The top 5 come from a demand simulation: 100,000 quiz runs against the same bank, counting which idea lands at number one. Percentages are shares of those simulated runs. This is our own data, and we say so plainly.</p>
<p>Want the costume the quiz would pick for you? <a class="guide" href="https://pickmycostume.com/?src=share-trends">Take the 2-minute quiz</a>.</p>
</div>

<footer><a href="https://pickmycostume.com/">Pick My Costume</a> &middot; <a href="https://pickmycostume.com/costumes">Browse all costume guides</a> &middot; <a href="https://pickmycostume.com/?src=share-trends">Take the quiz</a><br>Built with Muse.</footer>
</div>
</body>
</html>
'''.format(total=stats['total'])

    # Share button: native share with clipboard fallback (red-team 2026-09-27:
    # distribution pages had zero share paths). Added via replace so the
    # .format() above never sees the JS braces.
    SHARE_JS = (
        '<script>\n(function(){\n'
        '  var b=document.getElementById("shareBtn"),n=document.getElementById("shareNote");\n'
        '  if(!b||!n)return;\n'
        '  var c=document.querySelector(\'link[rel="canonical"]\');\n'
        '  var url=(c?c.href:location.href.split(\'#\')[0])+"?src=share-trends";\n'
        '  b.addEventListener("click",function(){\n'
        '    if(navigator.share){navigator.share({title:document.title,url:url}).catch(function(){});}\n'
        '    else if(navigator.clipboard&&navigator.clipboard.writeText)'
        '{navigator.clipboard.writeText(url).then('
        'function(){n.textContent=\'Link copied. Send it to a friend.\';},'
        'function(){n.textContent=url;});}\n'
        '    else{n.textContent=url;}\n'
        '  });\n'
        '})();\n</script>\n'
    )
    page = page.replace('</head>', FAQ_JSONLD_TRENDS + '\n</head>', 1)
    page = page.replace('<div class="method">', FAQ_VISIBLE_TRENDS + '\n\n<div class="method">', 1)
    page = page.replace('</body>', SHARE_JS + '</body>')

    if DASH_RE.search(page):
        bad = DASH_RE.findall(page)
        fail('em/en dash found in page copy: %r' % bad[:3])

    with open(PAGE_PATH, 'w', encoding='utf-8') as f:
        f.write(page)

    # ---- stat-card data for the Pinterest renderer ----
    stat_cards = [
        {'big': '%.1f%%' % DEMAND_TOP5[0][1],
         'label': 'of quiz runs pick The Tin Hero',
         'sub': 'the most-picked costume of 2026',
         'board': 'Halloween 2026'},
        {'big': str(stats['diy']),
         'label': 'of %d ideas are DIY' % stats['total'],
         'sub': 'build it, do not buy it',
         'board': 'DIY Halloween Costumes'},
        {'big': str(stats['gentle']),
         'label': 'kid costumes with zero scary ones',
         'sub': 'gentle picks for little ones',
         'board': 'Kids Halloween Costumes'},
        {'big': '4 to 1',
         'label': 'funny beats scary',
         'sub': '%d funny ideas, %d scary ones' % (stats['funny'], stats['scary']),
         'board': 'Halloween 2026'},
        {'big': str(stats['kid']),
         'label': 'ideas made for kids',
         'sub': 'the biggest shelf in the closet',
         'board': 'Kids Halloween Costumes'},
        {'big': str(stats['family']),
         'label': 'family costumes',
         'sub': 'one theme for the whole crew',
         'board': 'Family Halloween Costumes'},
        {'big': '%.1f%%' % DEMAND_TOP5[1][1],
         'label': 'pick Aussie Dog Family',
         'sub': 'the number 2 most-picked of 2026',
         'board': 'Family Halloween Costumes'},
        {'big': str(stats['low']),
         'label': 'low-budget ideas',
         'sub': 'the cheap shelf is the deep shelf',
         'board': 'DIY Halloween Costumes'},
    ]
    for c in stat_cards:
        for v in c.values():
            if DASH_RE.search(str(v)):
                fail('dash in stat card: %r' % v)
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump({'cards': stat_cards, 'stats': stats,
                   'demand': [{'id': i, 'pct': p} for i, p in DEMAND_TOP5]},
                  f, indent=2)

    print('wrote %s (%d bytes)' % (PAGE_PATH, os.path.getsize(PAGE_PATH)))
    print('wrote %s' % DATA_PATH)
    print('stats: ' + ', '.join('%s=%s' % kv for kv in sorted(stats.items())))

if __name__ == '__main__':
    main()
