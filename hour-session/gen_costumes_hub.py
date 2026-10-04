#!/usr/bin/env python3
"""Generate costumes.html: a plain-anchor A-Z hub of all /c/ guide pages.

Why it exists: the /c/ share/guide pages are the site's citable units,
but only 8 are reachable by plain <a> anchors from the homepage (the proof
strip). Pantry cards build their /c/ hrefs in JS, invisible to no-JS
crawlers. This hub gives every /c/ page a 2-click plain-anchor path:
home -> /costumes -> /c/<slug>.

Re-run after any bank change (add/remove/rename idea):
    python3 hour-session/gen_costumes_hub.py

2026-10-03 P0 repair (Stream 70): the bank moved from index.html to app.js
on 2026-10-01, but this generator kept parsing index.html -- both anchors
at 0 occurrences, asserts passing vacuously (0 == 0). A regen would have
emitted a hub with ZERO idea links, wiping all 164 /c/ links from live
/costumes. Now parses app.js with non-vacuous anchor asserts (fail loudly
per AGENTS.md 2026-10-03). Template re-derived FROM the live costumes.html
so all hand-patched drift (2026 title/meta, .updated line+CSS, FAQ JSON-LD,
quick-answer, pmc-faq section, current navs) is carried by the generator.
The .updated line carries Stream 19's staged freshness copy (item 6).
"""
import html
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- bank parse: app.js is the source of truth (moved from index.html 2026-10-01) ---
APP_JS = os.path.join(ROOT, "app.js")
src = open(APP_JS, encoding="utf-8").read()

# Anchor-existence asserts: fail LOUDLY if the source of truth moves again.
# (AGENTS.md 2026-10-03: generators must assert their anchor at run time;
# never emit vacuous output silently.)
assert "var IDEAS = [" in src, "P0: IDEAS anchor missing in app.js -- bank moved?"
assert "var INSTRUCTIONS = {" in src, "P0: INSTRUCTIONS anchor missing in app.js -- bank moved?"

QUIZ_IDS = {"q1", "q2", "q4", "q5kid", "qocc", "qinterest"}
ideas = [(s, t, b) for s, t, b in
         re.findall(r'\{id:"([^"]+)", title:"([^"]+)", blurb:"([^"]+)"', src)
         if s not in QUIZ_IDS]
instr_n = len(set(re.findall(r'"([a-z0-9-]+)":\{"m":\[', src)))
assert len(ideas) >= 100, "P0: IDEAS parse yielded %d (< 100) -- anchor drift?" % len(ideas)
assert len(ideas) == instr_n, "IDEAS parse %d != INSTRUCTIONS keys %d" % (len(ideas), instr_n)
assert len({s for s, _, _ in ideas}) == len(ideas), "duplicate slugs"
ideas.sort(key=lambda x: x[1].lower())
N = len(ideas)  # dynamic bank count (was hardcoded 164)

items = "\n".join(
    '      <li><a href="/c/%s">%s</a><span>%s</span></li>' % (
        s, html.escape(t), html.escape(b))
    for s, t, b in ideas)

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>All Costume Guides 2026 - Pick My Costume</title>
<meta name="description" content="Updated for Halloween 2026: all 164 Pick My Costume ideas, A to Z, each with a free DIY build guide: time and materials, and steps.">
<link rel="canonical" href="https://pickmycostume.com/costumes">
<meta property="og:type" content="website">
<meta property="og:title" content="All Costume Guides 2026 - Pick My Costume">
<meta property="og:description" content="Updated for Halloween 2026: all 164 costume ideas, A to Z, each with a free DIY build guide.">
<meta property="og:url" content="https://pickmycostume.com/costumes">
<meta property="og:image" content="https://pickmycostume.com/images/og/blue-dog-family.jpg">
<meta name="twitter:card" content="summary_large_image">
<!-- 2026-09-27 red-team discover: X/Twitter falls back to a small summary card
     without twitter:card; the costume photo deserves the large image. -->
<style>
body{font-family:-apple-system,system-ui,'Segoe UI',Roboto,sans-serif;margin:0;color:#222;background:#fff;}
.wrap{max-width:720px;margin:0 auto;padding:32px 20px 64px;}
h1{font-size:28px;margin:0 0 8px;}
.updated{font-size:14px;color:#6f6a61;margin:0 0 22px;}
.lede{font-size:16px;color:#555;margin:0 0 20px;}
ul{list-style:none;margin:0;padding:0;}
li{padding:0;border-bottom:1px solid #eee;}
/* 2026-09-27 red-team discover: guide links were inline text (~23px tall tap
   target). The anchor is now a full-row block: 12px + 23px text + 12px = ~47px,
   full width, clearing the 44px minimum with no visual change. */
li a{display:block;font-weight:700;color:#e07b00;text-decoration:none;font-size:16px;line-height:1.45;padding:12px 0;}
li a:hover{text-decoration:underline;}
li span{display:block;color:#555;font-size:14px;margin:0 0 12px;}
.home{margin-top:28px;font-size:15px;}
.home a{color:#e07b00;font-weight:700;}
.quizcta{display:inline-block;margin:6px 0 22px;background:#ff8c1a;color:#2a1500;font-weight:800;font-size:17px;text-decoration:none;padding:14px 26px;border-radius:14px;}
</style>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "How many costume guides are there?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "164, A to Z. Every one is a free step-by-step DIY build guide."
      }
    },
    {
      "@type": "Question",
      "name": "What does each guide include?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "The real build time, materials cost, and effort level up front, then the full materials list and steps. The numbers come from the guide itself - nothing is estimated for this page."
      }
    },
    {
      "@type": "Question",
      "name": "Can I make one of these tonight?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "16 of the 164 are make-tonight or 1-2 supplies away from default household basics. The make-it-tonight page lists all of them."
      }
    },
    {
      "@type": "Question",
      "name": "How do I pick one?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Take the 2-minute quiz and get one personal pick, or browse A-Z and open anything that catches your eye."
      }
    }
  ]
}
</script>
</head>
<body><main class="wrap">
<h1>All costume guides</h1>
<p class="quick-answer"><strong>Quick answer:</strong> <a href="/c/neon-demon-hunter">Neon Demon Hunter</a> (25 min + drying, black hoodie), <a href="/c/superhero-family">Superhero Family</a> (30 min, matching red sweatsuits), and <a href="/c/gloom-bloom">Gloom & Bloom</a> (15 min + drying, 1 set black clothes from the closet) — a spread of the most-built guides in the bank. Tap any name for its full build guide: materials list, numbered steps, and safety notes.</p>
<p class="lede">Every Pick My Costume idea, A to Z. Each guide lists what you need, the steps, and how long it takes. Free, no signup.</p>
<p class="updated">Updated for Halloween 2026: all 164 guides re-checked this October, and guide titles now spell out hands-on minutes (like Easy 10-Min Build).</p>
<a class="quizcta" href="/">Take the 2-minute quiz</a>
<!-- 2026-09-26 SEO articles batch: plain-anchor path home -> /costumes -> article.
     Folded into the generator 2026-09-27 (red-team): a regen used to drop this
     line, the quiz CTA, and the Explore nav below.
     2026-10-01 SEO consolidation (Billy: "Ship all 15"; hidden_files/seo/proposed-301-map-2026-10-01.md):
     /easy-last-minute-halloween-costumes and /last-minute-halloween-costumes-2026 retired
     via 301 to /last-minute-costumes; /couple-halloween-costumes-2026 retired via 301 to
     /couples-costumes. Internal links (this line included) were updated to the canonicals
     as part of the shipped consolidation: the hub links the LIVE canonical, never a
     retired source. seo-articles-gate.js asserts hub->canonical for retired articles.
     2026-10-03: /cheap-halloween-costumes was UN-RETIRED in Billy's 2026-10-01
     redirect-intent review (big search term, distinct intent; quality standalone, still in
     sitemap, live HTTP 200). The consolidation had pointed this line at
     /costumes-from-your-closet per the proposed map; restored the live article href here
     and kept the gate's hub->article assertion for cheap. -->
<p class="home" style="margin:2px 0 22px">Costume guides by question: <a href="/what-should-i-be-for-halloween">What should I be?</a> &middot; <a href="/what-should-my-kid-be-for-halloween">What should my kid be?</a> &middot; <a href="/halloween-costume-ideas-2026">2026 ideas</a> &middot; <a href="/halloween-costume-ideas-quiz">Costume ideas quiz</a> &middot; <a href="/last-minute-costumes">Last-minute costumes</a> &middot; <a href="/cheap-halloween-costumes">Cheap costumes</a> &middot; <a href="/school-halloween-costumes">School costumes</a> &middot; <a href="/office-costumes">Office costumes</a> &middot; <a href="/scary-halloween-costumes-2026">Scary costumes</a> &middot; <a href="/easy-diy-halloween-costumes-for-kids">Easy DIY kid costumes</a> &middot; <a href="/couples-costumes">Couple costumes</a> &middot; <a href="/last-minute-costumes">Night-before costumes</a> &middot; <a href="/teen-halloween-costumes-2026">Teen costumes</a> &middot; <a href="/toddler-costumes">Toddler costumes</a> &middot; <a href="/family-costumes">Family costumes</a></p>
"""

TAIL = """
<p class="home"><a href="/">Back to Pick My Costume</a> and take the 2-minute quiz to get one picked for you.</p>
<!-- 2026-09-26 red-team distro: hub cross-links, folded into the generator
     2026-09-27. Pantry label matches the page's real title (the rename). -->
<!-- 2026-09-27 red-team hubs: the three collection links pointed at
     /c/family, /c/couples, /c/last-minute -- all 404. Collections actually
     live at /collections/<name> and the couples article is its own page. -->
<p class="home" style="margin-top:10px">Explore: <a href="/family-costumes">Family costumes</a> &middot; <a href="/couples-costumes">Couples costumes</a> &middot; <a href="/last-minute-costumes">Last-minute costumes</a> &middot; <a href="/trending">Trending costumes</a> &middot; <a href="/compare">Compare easy costumes</a> &middot; <a href="/group-costumes">Group packs</a> &middot; <a href="/pantry">What you already own</a></p>
<script>
/* 2026-09-27 attribution: carry a validated ?src= (collection/print/share)
   into the quiz CTA and /c/ guide links, so arrivals from staged pages
   (e.g. the block board's /costumes?src=share-blockboard) keep their
   landing_src at the quiz. Junk/forged values are dropped. */
(function(){
  var m = /[?&]src=((?:collection|print|share)-[a-z-]+)/.exec(location.search || "");
  if (!m) return;
  var enc = encodeURIComponent(m[1]);
  function add(a){
    var h = a.getAttribute("href");
    if (!h || h.indexOf("src=") !== -1) return;
    a.setAttribute("href", h + (h.indexOf("?") === -1 ? "?" : "&") + "src=" + enc);
  }
  var q = document.querySelector("a.quizcta");
  if (q) add(q);
  var links = document.querySelectorAll('ul li a[href^="/c/"]');
  for (var i = 0; i < links.length; i++) add(links[i]);
})();
</script>
<section class="pmc-faq" id="pmc-faq">
<style>
.pmc-faq{margin:32px 0}
.pmc-faq h2{font-size:22px;margin:0 0 8px}
.pmc-faq details{margin:8px 0;border:1px solid rgba(140,140,160,.4);border-radius:10px;padding:10px 14px}
.pmc-faq summary{cursor:pointer;font-weight:700}
.pmc-faq p{margin:8px 0 4px;line-height:1.55}
</style>
<h2>Common questions</h2>
<details class="faq">
<summary>How many costume guides are there?</summary>
<p>164, A to Z. Every one is a free step-by-step DIY build guide.</p>
</details>
<details class="faq">
<summary>What does each guide include?</summary>
<p>The real build time, materials cost, and effort level up front, then the full materials list and steps. The numbers come from the guide itself - nothing is estimated for this page.</p>
</details>
<details class="faq">
<summary>Can I make one of these tonight?</summary>
<p>16 of the 164 are make-tonight or 1-2 supplies away from default household basics. The make-it-tonight page lists all of them.</p>
</details>
<details class="faq">
<summary>How do I pick one?</summary>
<p>Take the 2-minute quiz and get one personal pick, or browse A-Z and open anything that catches your eye.</p>
</details>
</section>
</main></body></html>
"""

page = HEAD + items + TAIL
# Dynamic bank count: the template was derived from live HTML with hardcoded
# 164s; substitute the live count so regens track bank growth.
for _old, _new in [
    ("all 164 Pick My Costume ideas", "all %d Pick My Costume ideas" % N),
    ("all 164 costume ideas", "all %d costume ideas" % N),
    ("164, A to Z. Every one", "%d, A to Z. Every one" % N),
    ("16 of the 164 are make-tonight", "16 of the %d are make-tonight" % N),
    ("all 164 guides re-checked", "all %d guides re-checked" % N),
]:
    assert _old in page, "hub template drift: %r missing" % _old
    page = page.replace(_old, _new)

out = os.path.join(ROOT, "costumes.html")
open(out, "w", encoding="utf-8").write(page)
print("wrote %s (%d ideas)" % (out, len(ideas)))
