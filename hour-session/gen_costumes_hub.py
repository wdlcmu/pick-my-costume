#!/usr/bin/env python3
"""Generate costumes.html: a plain-anchor A-Z hub of all /c/ guide pages.

Why it exists: the /c/ share/guide pages are the site's citable units,
but only 8 are reachable by plain <a> anchors from the homepage (the proof
strip). Pantry cards build their /c/ hrefs in JS, invisible to no-JS
crawlers. This hub gives every /c/ page a 2-click plain-anchor path:
home -> /costumes -> /c/<slug>.

Re-run after any bank change (add/remove/rename idea):
    python3 hour-session/gen_costumes_hub.py

2026-10-13 landing-audit rework: the hub now carries the standard site
header + dark theme, the intro above the list is ONE line (the Quick answer
top-3 block moved below the list, verbatim), and the 15-link category wall
became a compact chip row. Per-row stopwatch times are emitted HERE from
mcp-server/bank.json instructions[*].time (verbatim) -- before this date
they were a one-off hand generation in the live file (2026-10-12) and a
regen would have wiped them. Template re-derived from the live file again
(FAQ wording + counts had drifted ahead of the generator).

2026-10-22 FAQ fix: the "Can I make one of these tonight?" answer now
carries the verified counts (17 supplies-light, 126 fast; see
costumes-faq-14-check-2026-10-22.md), and the row chips render
display_time() -- hands-on time only, drying stripped per Billy's
display rule -- so a regen matches the live page except for intended
lines. Before this, a regen silently re-added "+ N drying" to 105
chips and to the Quick answer block.

2026-10-23 blurb reconciliation: the live hub carried IP-scrubbed
wording on 21 rows that neither app.js nor bank.json carried, so a
regen silently regressed them (found by the stale-comment cleanup's
scratch gate). The live wording was ported back into app.js IDEAS
(the origin: bank.json is built from app.js by
mcp-server/scripts/build-bank.mjs), bank.json was rebuilt locally
only (frozen: not deployed, not pushed), and a scratch regen now
reproduces the live page byte-for-byte. See
costumes-blurb-reconciliation-2026-10-23.md.

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
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- bank parse: rows come from mcp-server/bank.json (see below); app.js is
# still read for the anchor asserts + slug cross-check (it moved from
# index.html to app.js 2026-10-01) ---
APP_JS = os.path.join(ROOT, "app.js")
src = open(APP_JS, encoding="utf-8").read()

# Anchor-existence asserts: fail LOUDLY if the source of truth moves again.
# (AGENTS.md 2026-10-03: generators must assert their anchor at run time;
# never emit vacuous output silently.)
assert "var IDEAS = [" in src, "P0: IDEAS anchor missing in app.js -- bank moved?"
assert "var INSTRUCTIONS = {" in src, "P0: INSTRUCTIONS anchor missing in app.js -- bank moved?"

QUIZ_IDS = {"q1", "q2", "q4", "q5kid", "qocc", "qinterest"}
# Row data (id/title/blurb/time) comes from mcp-server/bank.json: the
# 2026-10-12 one-off that added the stopwatch times built the live rows
# from bank.json. bank.json is NOT the origin, though: it is built from
# app.js IDEAS by mcp-server/scripts/build-bank.mjs, so blurb wording
# must be fixed in app.js and bank.json rebuilt, never edited here or
# in bank.json alone. (An earlier version of this comment claimed
# bank.json carried IP-scrubbed wording app.js lacked; that was
# inverted by 2026-10-23, when bank.json == app.js on all rows and the
# live hub alone carried the scrubbed wording on 21 rows — reconciled
# 2026-10-23, see the docstring note.) app.js is still cross-checked
# below so a bank move fails loudly instead of emitting a stale hub.
_bank = json.load(open(os.path.join(ROOT, "mcp-server", "bank.json"),
                      encoding="utf-8"))
ideas = [(i["id"], i["title"], i["blurb"]) for i in _bank["ideas"]]
TIMES = {k: v.get("time") for k, v in _bank["instructions"].items()}
_app_ids = {s for s, _, _ in
            re.findall(r'\{id:"([^"]+)", title:"([^"]+)", blurb:"([^"]+)"',
                       src)
            if s not in QUIZ_IDS}
assert len(ideas) >= 100, "P0: bank.json yielded %d ideas (< 100)" % len(ideas)
assert {s for s, _, _ in ideas} == _app_ids, (
    "bank.json slugs != app.js slugs: %s" % (
        sorted({s for s, _, _ in ideas} ^ _app_ids)[:5]))
assert len({s for s, _, _ in ideas}) == len(ideas), "duplicate slugs"
ideas.sort(key=lambda x: x[1].lower())
N = len(ideas)  # dynamic bank count (was hardcoded 164)

# --- per-row build times: TIMES (loaded with the bank above) holds
# bank.json instructions[*].time, verbatim (the same strings the /c/
# guides carry). Fail loudly if a bank idea has no time: a row without
# its stopwatch time is a silent downgrade.
_missing_times = [s for s, _, _ in ideas if not TIMES.get(s)]
assert not _missing_times, (
    "bank.json instructions have no time for: %s" % _missing_times[:5])
# 2026-10-22 display rule (Billy, 2026-10-03): displayed drying time is
# dropped on site copy even though Tonight scoring still counts it. The
# live hub has always shown hands-on time only, so the chip renders the
# bank time with its "+ ... drying" suffix stripped. Bank times are
# "N min" or "N min + M drying" -- assert that shape so a new format
# fails loudly here instead of being mangled or leaked into the chip.
assert all(re.fullmatch(r"\d+ min( \+ .+ drying)?", TIMES[s])
           for s, _, _ in ideas), "unexpected bank time format"
def display_time(t):
    return re.sub(r"\s*\+.*drying\s*$", "", t)
TT = "⏱️ "  # stopwatch + variation selector, as rendered on the live hub

items = "\n".join(
    '      <li><a href="/c/%s">%s</a><span>%s</span>'
    '<span class="tt">%s%s</span></li>' % (
        s, html.escape(t), html.escape(b), TT,
        html.escape(display_time(TIMES[s])))
    for s, t, b in ideas)

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>All Costume Guides 2026 - Pick My Costume</title>
<meta name="description" content="Updated for Halloween 2026: all 169 Pick My Costume ideas, A to Z, each with a free DIY build guide: time and materials, and steps.">
<link rel="canonical" href="https://pickmycostume.com/costumes">
<meta property="og:type" content="website">
<meta property="og:title" content="All Costume Guides 2026 - Pick My Costume">
<meta property="og:description" content="Updated for Halloween 2026: all 169 costume ideas, A to Z, each with a free DIY build guide.">
<meta property="og:url" content="https://pickmycostume.com/costumes">
<meta property="og:image" content="https://pickmycostume.com/images/og/blue-dog-family.jpg">
<meta name="twitter:card" content="summary_large_image">
<!-- 2026-09-27 red-team discover: X/Twitter falls back to a small summary card
     without twitter:card; the costume photo deserves the large image. -->
<style>
:root{--bg:#160d28;--bg2:#211540;--card:#2a1c52;--ink:#fdf3e3;--muted:#cdbcf0;--line:#4b3486;--accent:#ff8c1a;--accent-ink:#2a1500;}
body{font-family:-apple-system,system-ui,'Segoe UI',Roboto,sans-serif;margin:0;color:var(--ink);background:var(--bg);}
.wrap{max-width:720px;margin:0 auto;padding:0 20px 64px;}
/* 2026-10-13: standard site header (same markup as the homepage sitehead,
   adapted to this page's 720px wrap) + the site dark theme. Before this the
   hub had no header and a white unstyled look. */
.sitehead{position:sticky;top:0;z-index:100;background:rgba(22,13,40,.94);-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);margin:0 -20px 4px;padding:0 20px;display:flex;align-items:center;gap:12px;}
.sitehead-link{display:flex;align-items:center;gap:10px;min-height:54px;color:var(--ink);text-decoration:none;font-weight:800;font-size:18px;}
.sitehead-mark{font-size:22px;line-height:1;}
.sitehead-name{white-space:nowrap;}
.sitenav{margin-left:auto;display:flex;align-items:center;gap:2px;}
.sitenav a{color:var(--muted);text-decoration:none;font-size:14px;font-weight:700;padding:12px 10px;border-radius:10px;white-space:nowrap;}
@media (hover:hover){.sitehead-link:hover{color:var(--ink);text-decoration:none;}.sitenav a:hover{color:var(--ink);}}
@media (max-width:899px){.sitehead{flex-wrap:wrap;gap:0 12px;padding-top:8px;padding-bottom:4px;}.sitehead-link{min-height:0;}.sitenav{margin-left:0;flex:1 1 100%;justify-content:space-between;}.sitenav a{padding:8px 4px;font-size:13px;}}
h1{font-size:28px;margin:18px 0 8px;}
.intro{font-size:16px;color:var(--muted);margin:0 0 16px;line-height:1.55;}
.quizcta{display:inline-block;margin:6px 0 18px;background:var(--accent);color:var(--accent-ink);font-weight:800;font-size:17px;text-decoration:none;padding:14px 26px;border-radius:14px;}
/* 2026-10-13: the 15-link category wall became a compact chip row. */
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 8px;}
.chips a{color:var(--ink);background:var(--bg2);border:1px solid var(--line);border-radius:999px;padding:8px 13px;font-size:13.5px;font-weight:600;text-decoration:none;}
.chips a:hover{border-color:var(--accent);color:var(--accent);}
ul{list-style:none;margin:6px 0 0;padding:0;}
li{padding:0;border-bottom:1px solid var(--line);}
/* 2026-09-27 red-team discover: guide links were inline text (~23px tall tap
   target). The anchor is now a full-row block: 12px + 23px text + 12px = ~47px,
   full width, clearing the 44px minimum with no visual change. */
li a{display:block;font-weight:700;color:var(--accent);text-decoration:none;font-size:16px;line-height:1.45;padding:12px 0;}
li a:hover{text-decoration:underline;}
li span{display:block;color:var(--muted);font-size:14px;margin:0 0 6px;}
li .tt{display:block;font-size:13px;color:var(--muted);margin:0 0 12px;}
.quick-answer{font-size:15.5px;line-height:1.6;color:var(--ink);background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:26px 0 0;}
.quick-answer a{color:var(--accent);font-weight:700;}
.home{margin-top:28px;font-size:15px;color:var(--muted);}
.home a{color:var(--accent);font-weight:700;}footer{margin-top:40px;font-size:13px;color:var(--muted);}
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
        "text": "169, A to Z. Every one is a free step-by-step DIY build guide."
      }
    },
    {
      "@type": "Question",
      "name": "What does each guide include?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "The real build time, materials, and effort level up front, then the full materials list and steps. The numbers come straight from each guide."
      }
    },
    {
      "@type": "Question",
      "name": "Can I make one of these tonight?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. 17 of the 169 need nothing new, or just 1 or 2 extra supplies, if you have the basic supplies at home. The closet page lists all 17. Fast builds are a bigger group: 126 of the 169 take 30 minutes or less of work."
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
</script><script>
var _phq=[];
function track(name, props){ try { if (window.posthog && posthog.capture) posthog.capture(name, props || {}); else _phq.push([name, props || {}]); } catch (e) {} }
(function(){ var s=document.createElement('script'); s.async=true; s.src='https://us.i.posthog.com/static/array.js';
s.onload=function(){ try { if (window.posthog && posthog.init){ posthog.init('phc_t9dkHXAZR5VEjPFm3K5JDzGKFsNNxKcwSxxcEBEeLbS7',{api_host:'https://us.i.posthog.com',autocapture:false,capture_pageview:true,disable_session_recording:true}); _phq.splice(0).forEach(function(e){ try{posthog.capture(e[0],e[1]);}catch(x){} }); } } catch(e){} };
document.head.appendChild(s); })();
</script>
</head>
<body><main class="wrap">
<header class="sitehead">
  <a class="sitehead-link" href="/" aria-label="Pick My Costume: home">
    <span class="sitehead-mark" aria-hidden="true">&#127875;</span>
    <span class="sitehead-name">Pick My Costume</span>
  </a>
  <!-- 2026-10-01 IA: Pick (quiz) -> Explore (galaxy) -> Pantry -> Play. -->
  <nav class="sitenav" aria-label="Site">
    <a href="/" aria-label="Pick my costume: the quiz">Pick</a>
    <a href="/map/">Explore</a>
    <a href="/pantry">Pantry</a>
    <a href="/play">Play</a>
  </nav>
</header>
<h1>All costume guides</h1>
<p class="intro">Every Pick My Costume idea, A to Z: what you need, the steps, and how long it takes. ⏱️ We timed it, but results may vary. Free, no signup.</p>
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
<nav class="chips" aria-label="Costume guides by question"><a href="/what-should-i-be-for-halloween">What should I be?</a><a href="/what-should-my-kid-be-for-halloween">What should my kid be?</a><a href="/halloween-costume-ideas-2026">2026 ideas</a><a href="/halloween-costume-ideas-quiz">Costume ideas quiz</a><a href="/last-minute-costumes">Last-minute costumes</a><a href="/cheap-halloween-costumes">Cheap costumes</a><a href="/school-halloween-costumes">School costumes</a><a href="/office-costumes">Office costumes</a><a href="/scary-halloween-costumes-2026">Scary costumes</a><a href="/easy-diy-halloween-costumes-for-kids">Easy DIY kid costumes</a><a href="/couples-costumes">Couple costumes</a><a href="/last-minute-costumes">Night-before costumes</a><a href="/teen-halloween-costumes-2026">Teen costumes</a><a href="/toddler-costumes">Toddler costumes</a><a href="/family-costumes">Family costumes</a></nav>
<!-- Per-row build times emitted by this generator from mcp-server/bank.json instructions[*].time (verbatim). -->
<ul>
"""

TAIL = """
</ul>
<!-- 2026-10-13: the Quick answer top-3 block moved below the list (it used
     to sit above it with two more intro paragraphs). Text verbatim from the
     live page, only the separator normalized to the injector's style. -->
<p class="quick-answer"><strong>Quick answer:</strong> <a href="/c/neon-demon-hunter">Neon Demon Hunter</a> (25 min, black hoodie) (not a tonight build; needs 2 hrs drying), <a href="/c/superhero-family">Superhero Family</a> (30 min, matching red sweatsuits), and <a href="/c/gloom-bloom">Gloom & Bloom</a> (15 min, 1 set black clothes from the closet): a spread of the most-built guides in the bank. Tap any name for its full build guide: materials list, numbered steps, and safety notes.</p>
<p class="home"><a href="/">Back to Pick My Costume</a> and take the 2-minute quiz to get one picked for you.</p>
<!-- 2026-09-26 red-team distro: hub cross-links, folded into the generator
     2026-09-27. Pantry label matches the page's real title (the rename). -->
<p class="home" style="margin-top:10px">Explore: <a href="/family-costumes">Family costumes</a> &middot; <a href="/couples-costumes">Couples costumes</a> &middot; <a href="/last-minute-costumes">Last-minute costumes</a> &middot; <a href="/trending">Trending costumes</a> &middot; <a href="/compare">Compare easy costumes</a> &middot; <a href="/group-costumes">Group packs</a> &middot; <a href="/pantry">What you already own</a> &middot; <a href="/c/couples">Couples costume ideas</a> &middot; <a href="/c/family">Family costume ideas</a> &middot; <a href="/c/last-minute">Last-minute costume ideas</a></p>
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
<p>169, A to Z. Every one is a free step-by-step DIY build guide.</p>
</details>
<details class="faq">
<summary>What does each guide include?</summary>
<p>The real build time, materials, and effort level up front, then the full materials list and steps. The numbers come straight from each guide.</p>
</details>
<details class="faq">
<summary>Can I make one of these tonight?</summary>
<p>Yes. 17 of the 169 need nothing new, or just 1 or 2 extra supplies, if you have the basic supplies at home. The closet page lists all 17. Fast builds are a bigger group: 126 of the 169 take 30 minutes or less of work.</p>
</details>
<details class="faq">
<summary>How do I pick one?</summary>
<p>Take the 2-minute quiz and get one personal pick, or browse A-Z and open anything that catches your eye.</p>
</details>
</section>
<footer>Built with Muse.</footer></main></body></html>
"""

page = HEAD + items + TAIL
# Dynamic bank count: the template was derived from live HTML with hardcoded
# counts (164s originally, 169s at the 2026-10-13 re-derivation); substitute
# the live count so regens track bank growth.
for _old, _new in [
    ("all 169 Pick My Costume ideas", "all %d Pick My Costume ideas" % N),
    ("all 169 costume ideas", "all %d costume ideas" % N),
    ("169, A to Z. Every one", "%d, A to Z. Every one" % N),
    ("17 of the 169 need nothing new", "17 of the %d need nothing new" % N),
    ("126 of the 169 take 30 minutes", "126 of the %d take 30 minutes" % N),
]:
    assert _old in page, "hub template drift: %r missing" % _old
    page = page.replace(_old, _new)

out = os.path.join(ROOT, "costumes.html")
open(out, "w", encoding="utf-8").write(page)
print("wrote %s (%d ideas)" % (out, len(ideas)))
