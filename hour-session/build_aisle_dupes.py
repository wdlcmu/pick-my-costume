#!/usr/bin/env python3
"""Generate aisle-dupes.html: "Don't buy it. Make it." (watchdog stream, 2026-09-27).

The gap: 26% of costume inspiration comes from retail stores (NRF). No
surface in the portfolio intercepts the post-aisle sticker-shock moment.
This page maps the NRF 2026 survey's top kid costumes to honest home-built
versions from the bank.

Honesty contracts (asserted below):
- Every home-side displayed time is the bank instruction's own time label
  with any "+ ... drying" suffix stripped (display_time(); Billy's
  2026-10-03 display rule: displayed drying time is dropped on site copy
  even though Tonight scoring still counts it), and effort is quoted
  verbatim. The bank no longer carries a cost field, and the page makes
  no cost claims.
- Every pick has 'kid' in audience and effort 'Easy'.
- No retailer is named; the aisle side is described only as store-bought.
- All numbers and sources are cited in the methodology section.

Additive and inert: writes only aisle-dupes.html at repo root. No inbound
links, no sitemap edit, no index.html edit. ?src=share-aisledupe attribution on
guide links and the quiz CTA (add 'aisledupe' to the quiz origin allowlist
at deploy time). PostHog events aisledupe_viewed / aisledupe_shared carry
the standing probe/sim/internal exclusion.

2026-10-22 reconciliation: the live page had been hand-edited ahead of
this generator (new lede, price row, FAQ, method section, quick-answer
block, and share text; the $42 aisle average, the $1.5 billion lede, and
all cost labels were removed), and the bank dropped its cost field, so
the old generator both crashed (KeyError: 'cost') and would have reverted
the live improvements. The live page was fetched as ground truth and its
wording was ported INTO this generator, never the other direction. The
brittle exact-count bank asserts (== 169) were replaced with content
checks: idea/instruction slug sets must match, the bank must be
non-vacuous, and every record this page uses must carry the expected
title, audience, effort, materials, steps, and display time.

Re-run reproduces the live page byte-for-byte (verified 2026-10-22 by
diffing a fresh regen against the live bytes; see
aisle-dupes-generator-reconciliation-2026-10-22.md).
"""
import os
import re
import json
import html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "mcp-server", "bank.json")
# AISLE_DUPES_OUT lets a verification run write to a scratch path and
# diff against the live page without touching aisle-dupes.html.
OUT = os.environ.get("AISLE_DUPES_OUT",
                     os.path.join(ROOT, "aisle-dupes.html"))

DASHES = re.compile(r"[\u2013\u2014]")

# NRF 2026 Halloween survey, kids' costumes (via thedeadpixelssociety.com).
# rstat strings are the live card's full retail-stat line, quoted from the
# survey writeup, not computed. (The superhero line names both separate
# survey entries, Spider-Man 4.6 million and superhero 2.3 million; they
# are never added together.)
# expect_time is the known display time (bank time, drying stripped) for
# the slug's current bank record; the page's prose (notes, quick answer,
# meta description range) is written against these values, so a bank time
# change must fail loudly here instead of silently desyncing the copy.
# quick is the per-costume shorthand used in the quick-answer block.
DUPES = [
    {
        "retail": "Superhero",
        "rstat": "4.6 million kids are going as Spider-Man, and 2.3 "
                 "million as a superhero",
        "slug": "tin-hero",
        "expect_time": "25 min",
        "quick": "red sweatsuit",
        "note": "Not the licensed suit. A hero you build: red sweatsuit, "
                "gold duct tape, 25 minutes.",
    },
    {
        "retail": "Princess",
        "rstat": "2.2 million kids are going as this",
        "slug": "fairy-tale-princesses",
        "expect_time": "15 min",
        "quick": "a dress from the closet",
        "note": "A dress from the closet and a cereal-box crown. 15 minutes.",
    },
    {
        "retail": "Witch",
        "rstat": "1.6 million kids are going as this",
        "slug": "little-witch",
        "expect_time": "15 min",
        "quick": "black cape",
        "note": "Black cape, pointy hat, striped tights. 15 minutes.",
    },
    {
        "retail": "Ghost",
        "rstat": "1.6 million kids are going as this",
        "slug": "classic-ghost",
        "expect_time": "10 min",
        "quick": "a white sheet",
        "note": "The original DIY: a white sheet and cut-out eyes. 10 minutes.",
    },
]

PAGE_URL = "https://pickmycostume.com/aisle-dupes"

COPY = {
    "title": "Aisle dupes: the 4 costumes America is buying, made at home - Pick My Costume",
    "desc": "These 4 store-bought favorites each have a 10 to 25 minute "
            "home version built from closet basics, with a free "
            "step-by-step build guide.",
    "h1": "Don't buy it. Make it.",
    "lede": "Millions of kids go as these 4 costumes every Halloween "
            "(National Retail Federation, 2026 survey). Below are the 4 "
            "costumes leading the aisle, each with the make-it version: "
            "real build time, closet-first materials, free step-by-step "
            "guide.",
    "share_text": "These 4 aisle favorites each have a make-it home "
                  "version from closet basics: "
                  "https://pickmycostume.com/aisle-dupes",
}

FAQ = [
    ("Is the home version the same costume as the store version?",
     "Same costume idea, home-built version. The Tin Hero is not a licensed "
     "Spider-Man suit. It is a hero your kid builds from a red sweatsuit and "
     "gold duct tape in 25 minutes. Every card below says plainly what the "
     "home version is."),
    ("Where do the time numbers come from?",
     "Each build guide carries its own time and effort labels. The cards "
     "use those labels, so what you see is what the guide says."),
    ("Can I really make these with stuff at home?",
     "Most materials are closet or dollar-store items. Open any build guide "
     "for the full list before you decide."),
]


def esc(s):
    return html.escape(s, quote=True)


def display_time(t):
    # 2026-10-22 display rule (Billy, 2026-10-03): displayed drying time
    # is dropped on site copy even though Tonight scoring still counts
    # it. The live page has always shown hands-on time only, so strip the
    # bank time's "+ ... drying" suffix at build time. Bank times are
    # "N min" or "N min + M drying"; the shape is asserted in main().
    return re.sub(r"\s*\+.*drying\s*$", "", t or "")


def main():
    bank = json.load(open(BANK, encoding="utf-8"))
    ideas = {i["id"]: i for i in bank["ideas"]}
    ins = bank["instructions"]
    # Content checks, not exact totals (replaced 2026-10-22; the old
    # "== 169" asserts broke silently on every bank expansion and said
    # nothing about the records this page actually uses): the bank must
    # be non-vacuous, idea and instruction slug sets must agree, and
    # every record used below is field-checked individually.
    assert len(ideas) >= 100, "bank yielded only %d ideas" % len(ideas)
    assert set(ideas) == set(ins), (
        "bank idea/instruction slug sets differ: %s"
        % sorted(set(ideas) ^ set(ins))[:5])

    for d in DUPES:
        slug = d["slug"]
        assert slug in ideas, "unknown bank id %r" % slug
        assert ideas[slug].get("title"), "%s has no title" % slug
        assert "kid" in ideas[slug]["audience"], "%s not kid audience" % slug
        triple = ins[slug]
        assert triple["effort"] == "Easy", "%s effort is %r" % (slug, triple["effort"])
        for f in ("note", "retail", "rstat", "quick"):
            assert not DASHES.search(d.get(f, "") or ""), "dash in %s/%s" % (slug, f)
        for f in ("time", "effort"):
            assert triple.get(f), "missing %s for %s" % (f, slug)
        assert triple.get("m") and triple.get("s"), (
            "missing materials/steps for %s" % slug)
        assert re.fullmatch(r"\d+ min( \+ .+ drying)?", triple["time"]), (
            "unexpected bank time format for %s: %r" % (slug, triple["time"]))
        assert display_time(triple["time"]) == d["expect_time"], (
            "%s display time is %r, page copy expects %r"
            % (slug, display_time(triple["time"]), d["expect_time"]))
        assert "million" in d["rstat"], "rstat for %s lost its figure" % slug
        photo = os.path.join(ROOT, "photos", slug + ".webp")
        assert os.path.isfile(photo), "missing photo %s" % photo

    og = os.path.join(ROOT, "images", "og", "classic-ghost.jpg")
    assert os.path.isfile(og), "missing og image %s" % og

    for f in COPY.values():
        assert not DASHES.search(f), "dash in page copy"
    for q, a in FAQ:
        assert not DASHES.search(q + a), "dash in FAQ copy"

    cards = []
    for d in DUPES:
        slug = d["slug"]
        rec = ideas[slug]
        tri = ins[slug]
        cards.append(
            '<li class="card">'
            '<div class="retail"><span class="rname">%s</span>'
            '<span class="rstat">%s</span></div>'
            '<div class="pricerow"><span class="aisle">The aisle: store-bought</span>'
            '<span class="home">Home: %s, closet-first</span></div>'
            '<a href="/c/%s?src=share-aisledupe"><img src="/photos/%s.webp" '
            'alt="%s costume" loading="lazy">'
            '<span class="t">%s</span></a>'
            '<span class="tri">%s, %s</span>'
            '<p class="note">%s</p>'
            '<a class="guide" href="/c/%s?src=share-aisledupe">Free build guide</a>'
            '</li>' % (
                esc(d["retail"]), esc(d["rstat"]),
                esc(display_time(tri["time"])),
                slug, slug, esc(rec["title"]), esc(rec["title"]),
                esc(display_time(tri["time"])), esc(tri["effort"]),
                esc(d["note"]), slug,
            )
        )

    quick_segs = []
    for d in DUPES:
        slug = d["slug"]
        quick_segs.append(
            '<a href="/c/%s">%s</a> (%s, %s)' % (
                slug, esc(ideas[slug]["title"]),
                esc(display_time(ins[slug]["time"])), esc(d["quick"]),
            )
        )
    quick_answer = (
        "<strong>Quick answer:</strong> "
        + ", ".join(quick_segs[:-1])
        + ", and "
        + quick_segs[-1]
        + ": DIY takes on the store-bought classics. Tap any name for its "
          "full build guide: materials list, numbered steps, and safety "
          "notes."
    )

    faq_items = []
    for q, a in FAQ:
        faq_items.append(
            '{"@type":"Question","name":%s,"acceptedAnswer":'
            '{"@type":"Answer","text":%s}}' % (json.dumps(q), json.dumps(a))
        )
    faq_json = ('{"@context":"https://schema.org","@type":"FAQPage",'
                '"mainEntity":[%s]}' % ",".join(faq_items))

    page = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s">
<meta property="og:type" content="website">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:url" content="%s">
<meta property="og:image" content="https://pickmycostume.com/images/og/classic-ghost.jpg">
<style>
body{font-family:-apple-system,system-ui,'Segoe UI',Roboto,sans-serif;margin:0;color:#222;background:#fff;}
.wrap{max-width:720px;margin:0 auto;padding:32px 20px 64px;}
h1{font-size:28px;margin:0 0 8px;}
.lede{font-size:16px;color:#555;margin:0 0 24px;line-height:1.5;}
ul{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:16px;}
.card{border:1px solid #eee;border-radius:12px;overflow:hidden;padding:0 0 12px;}
.retail{padding:10px 12px 6px;}
.rname{font-weight:800;font-size:15px;display:block;}
.rstat{font-size:12px;color:#888;}
.pricerow{display:flex;justify-content:space-between;gap:8px;padding:0 12px 8px;font-size:13px;}
.aisle{color:#999;text-decoration:line-through;}
.home{color:#15803d;font-weight:700;}
.card img{width:100%%;aspect-ratio:4/5;object-fit:cover;display:block;}
.card .t{font-weight:700;display:block;padding:10px 12px 2px;font-size:16px;color:#222;}
.card a{text-decoration:none;}
.card .tri{display:block;padding:0 12px;font-size:13px;color:#777;}
.card .note{font-size:14px;color:#555;margin:8px 12px;}
.card .guide{display:inline-block;margin:0 12px;font-size:14px;font-weight:700;color:#0a6cff;}
.method{margin:36px 0 0;font-size:14px;color:#555;line-height:1.6;border-top:1px solid #eee;padding-top:20px;}
.method h2{font-size:18px;color:#222;}
.method ul{list-style:disc;margin:8px 0 8px 20px;padding:0;display:block;}
.method li{margin:4px 0;}
.faq{margin:28px 0 0;}
.faq h2{font-size:18px;}
.faq details{margin:10px 0;border:1px solid #eee;border-radius:10px;padding:10px 14px;}
.faq summary{font-weight:700;cursor:pointer;font-size:15px;}
.faq p{font-size:14px;color:#555;margin:8px 0 4px;line-height:1.6;}
.quizbox{margin:32px 0 0;padding:20px;border-radius:12px;background:#f7f3ff;text-align:center;}
.quizbox p{margin:0 0 12px;font-size:16px;}
.quizbox a{display:inline-block;background:#7c3aed;color:#fff;font-weight:700;padding:12px 24px;border-radius:10px;text-decoration:none;}
.sharebox{margin:16px 0 0;padding:20px;border-radius:12px;background:#f0fdf4;text-align:center;}
.sharebox p{margin:0 0 12px;font-size:16px;}
.sharebox button{background:#15803d;color:#fff;font-weight:700;padding:12px 24px;border:0;border-radius:10px;font-size:16px;cursor:pointer;}
.more{margin-top:24px;text-align:center;}
.more a{color:#0a6cff;}
@media (max-width:560px){ul{grid-template-columns:1fr;}}
</style>
<script type="application/ld+json">%s</script>
</head>
<body>
<div class="wrap">
<h1>%s</h1>
<p class="quick-answer">%s</p>
<p class="lede">%s</p>
<ul>
%s
</ul>
<div class="method">
<h2>Where the numbers come from</h2>
<p>The costume rankings are from the National Retail Federation's 2026
Halloween survey. Every time on the home side comes from the build guide's own label,
.</p>
<p>Source: National Retail Federation 2026 survey
(<a href="https://thedeadpixelssociety.com/nrf-halloween-consumer-spending-expected-to-reach-13-5-billion/">writeup</a>).</p>
</div>
<div class="faq">
<h2>Questions parents ask</h2>
%s
</div>
<div class="quizbox">
<p>Not sold on any of these? Take the 2-minute quiz and get your match.</p>
<a href="/?src=share-aisledupe">Take the quiz</a>
</div>
<div class="sharebox">
<p>Know a parent standing in the costume aisle right now? Send them this page.</p>
<button id="sharebtn" type="button">Share this page</button>
</div>
<p class="more"><a href="/costumes">Browse all %d costume guides</a></p>
</div>
<script>
/* PostHog: anonymous usage stats only. QA traffic is flagged, never mixed in. */
function track(name, props){
  props = props || {};
  try {
    var q = location.search;
    if (/[?&](probe|sim)=/.test(q) || /[?&]internal=1/.test(q)) props.internal = true;
  } catch(e){}
  try {
    if (window.posthog && posthog.capture) posthog.capture(name, props);
  } catch(e){}
}
(function(){
  var s = document.createElement("script");
  s.async = true;
  s.src = "https://us.i.posthog.com/static/array.js";
  s.onload = function(){
    try {
      if (window.posthog && posthog.init) {
        posthog.init("phc_t9dkHXAZR5VEjPFm3K5JDzGKFsNNxKcwSxxcEBEeLbS7", {
          api_host: "https://us.i.posthog.com", autocapture: false,
          capture_pageview: true, disable_session_recording: true
        });
      }
    } catch(e){}
  };
  try { document.head.appendChild(s); } catch(e){}
})();
track("aisledupe_viewed", {});
var SHARE_TEXT = %s;
function doShare(){
  track("aisledupe_shared", {});
  var done = function(){};
  if (navigator.share) {
    navigator.share({text: SHARE_TEXT, url: "%s"}).then(done, function(){ fallbackCopy(); });
  } else { fallbackCopy(); }
}
function fallbackCopy(){
  function promptIt(){ try { window.prompt("Copy this:", SHARE_TEXT + " " + "%s"); } catch(e){} }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(SHARE_TEXT + " " + "%s").then(done, promptIt);
  } else { promptIt(); }
}
document.getElementById("sharebtn").addEventListener("click", doShare);
</script>
</body>
</html>
""" % (
        esc(COPY["title"]), esc(COPY["desc"]), PAGE_URL,
        esc(COPY["title"]), esc(COPY["desc"]), PAGE_URL,
        faq_json,
        esc(COPY["h1"]), quick_answer, esc(COPY["lede"]), "\n".join(cards),
        "\n".join(
            '<details><summary>%s</summary><p>%s</p></details>' % (esc(q), esc(a))
            for q, a in FAQ
        ),
        len(ideas),
        json.dumps(COPY["share_text"]),
        PAGE_URL, PAGE_URL, PAGE_URL,
    )

    assert not DASHES.search(page), "dash slipped into rendered page"
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    print("wrote %s (%d bytes)" % (OUT, len(page)))


if __name__ == "__main__":
    main()
