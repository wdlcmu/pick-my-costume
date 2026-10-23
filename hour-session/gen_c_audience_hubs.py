#!/usr/bin/env python3
"""Generate /c/ audience hub pages: family, couples, last-minute.

Why they exist (2026-09-27 novel scouting): the /c/ guides are the site's
citable units, but they lacked an index/hub layer that captures actual search
demand ("family halloween costumes", "couples halloween costumes",
"last minute halloween costumes"). These three hubs give crawlers a
plain-anchor path: home -> /costumes -> /c/<hub> -> /c/<slug>.

Each hub is a Cloudflare Pages Function (functions/c/<hub>.js) that serves
fully-static HTML: plain anchors; the only client JS is the PostHog pageview snippet in <head>. Static segments win over the
dynamic functions/c/[slug].js route, so /c/family never hits the guide
function's 404. HTML is embedded at generation time from the bank.

Selection rules (kept identical to existing site conventions):
  family      = bank audience includes "family"            (36 ideas)
  couples     = bank audience includes "couple"            (38 ideas)
  last-minute = guide build time <= 25 min                 (103 ideas,
                same 5-to-25-minute bar as the /easy-last-minute-halloween-costumes article)

Re-run after any bank change (add/remove/rename idea, time change):
    python3 hour-session/gen_c_audience_hubs.py
then re-run the verify harness:
    node hour-session/verify_c_audience_hubs.mjs
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- bank ----
bank = json.load(open(os.path.join(ROOT, "mcp-server", "bank.json"), encoding="utf-8"))
ideas = bank["ideas"]
ids = [i["id"] for i in ideas]
assert len(ids) == len(set(ids)), "duplicate bank ids"
by_id = {i["id"]: i for i in ideas}

# ---- live guide function: display copy (IDEAS) and build times (HOWTO) ----
src = open(os.path.join(ROOT, "functions", "c", "[slug].js"), encoding="utf-8").read()

# ---- display copy from the live guide function (IDEAS map): this is the
# copy users actually read on /c/<slug>, so the hub index matches it.
# bank.json is used only for audience classification. (2026-09-27: bank.json
# was regenerated from index.html, so all 138 blurbs now agree byte-for-byte
# across index.html, bank.json, the guide function, and these hubs.)
display = {}
for m in re.finditer(r'"([a-z0-9-]+)": \{"t": "((?:[^"\\]|\\.)*)", "b": "((?:[^"\\]|\\.)*)"\}', src):
    display[m.group(1)] = {
        "title": m.group(2).replace('\\"', '"'),
        "blurb": m.group(3).replace('\\"', '"'),
    }
assert set(display) == set(ids), "display copy != bank ids"
fslugs = [m.group(1) for m in re.finditer(r'"([a-z0-9-]+)": \{"m"', src)]
ftimes = re.findall(r'"time": "([^"]+)"', src)
assert len(fslugs) == len(ids) and len(ftimes) == len(ids)
assert set(fslugs) == set(ids), "bank ids != guide slugs"
times = dict(zip(fslugs, ftimes))


def minutes(t):
    m = re.match(r"\s*(\d+)\s*min", t)
    return int(m.group(1)) if m else 999


HUBS = {
    "family": {
        "h1": "Family Halloween costume ideas",
        "title": "Family Halloween costume ideas - Pick My Costume",
        "desc": "family Halloween costume ideas with free DIY build guides: time, cost, materials, and steps for each.",
        "lede": "Matching and theme costumes for the whole crew, from the bank of %d ideas. Each guide lists what you need, the steps, and how long it takes. Free, no signup." % len(ids),
        "og_image": "blue-dog-family",
        "select": lambda i: "family" in i["audience"],
    },
    "couples": {
        "h1": "Couples Halloween costume ideas",
        "title": "Couples Halloween costume ideas - Pick My Costume",
        "desc": "couples Halloween costume ideas with free DIY build guides: time, cost, materials, and steps for each.",
        "lede": "Two-person costumes that read as a pair: duos, food pairs, and opposites. Each guide lists what you need, the steps, and how long it takes. Free, no signup.",
        "og_image": "burger-joint-couple",
        "select": lambda i: "couple" in i["audience"],
    },
    "last-minute": {
        "h1": "Last-minute Halloween costumes",
        "title": "Last-minute Halloween costumes - Pick My Costume",
        "desc": "last-minute Halloween costumes that take 5 to 25 minutes, each with a free DIY build guide: time, cost, materials, and steps.",
        "lede": "Need a costume tonight? Every idea here builds in 25 minutes or less, most in 20. Each guide lists what you need, the steps, and the real time and cost. Free, no signup.",
        "og_image": "classic-ghost",
        "select": lambda i: minutes(times[i["id"]]) <= 25,
    },
}

# PostHog pageview snippet, copied verbatim from index.html lines 44-70
# (homepage pattern: same token, same api_host, capture_pageview: true).
# The pmcInternal / Analytics lines are inert on the hubs: those helpers
# do not exist here, and both are typeof/property-guarded no-ops.
POSTHOG_SNIPPET = '''<script>
/* PostHog: anonymous usage stats only. Quiz answers are never sent. Session replay is off. */
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
          capture_pageview: true,
          disable_session_recording: true
        });
        /* Internal devices (owner's own phone/laptop, flagged via ?internal=1)
           tag even the automatic pageview as internal. */
        try { if (typeof pmcInternal === "function" && pmcInternal() && posthog.register) posthog.register({internal: true}); } catch(e){}
        /* Person property so dashboards can filter internal devices directly. */
        try { if (typeof pmcInternal === "function" && pmcInternal() && posthog.people && posthog.people.set) posthog.people.set({pmc_internal: true}); } catch(e){}
        if (window.Analytics && Analytics._flush) Analytics._flush();
      }
    } catch(e){}
  };
  document.head.appendChild(s);
})();
</script>'''

CSS = ("body{font-family:-apple-system,system-ui,'Segoe UI',Roboto,sans-serif;margin:0;"
       "color:#222;background:#fff;}"
       ".wrap{max-width:720px;margin:0 auto;padding:32px 20px 64px;}"
       ".crumbs{font-size:14px;color:#777;margin:0 0 14px;}"
       ".crumbs a{color:#e07b00;font-weight:700;text-decoration:none;}"
       "h1{font-size:28px;margin:0 0 8px;}"
       ".lede{font-size:16px;color:#555;margin:0 0 20px;}"
       "ul{list-style:none;margin:0;padding:0;}"
       "li{padding:9px 0;border-bottom:1px solid #eee;font-size:16px;line-height:1.45;}"
       "li a{font-weight:700;color:#e07b00;text-decoration:none;}"
       "li a:hover{text-decoration:underline;}"
       "li span{display:block;color:#555;font-size:14px;margin-top:2px;}"
       ".home{margin-top:28px;font-size:15px;}"
       ".home a{color:#e07b00;font-weight:700;}"
       ".quizcta{display:inline-block;margin:6px 0 22px;background:#ff8c1a;color:#2a1500;"
       "font-weight:800;font-size:17px;text-decoration:none;padding:14px 26px;border-radius:14px;}"
       "footer{margin-top:40px;font-size:13px;color:#777;}")


def js_escape(s):
    """Make a string safe to embed in a JS template literal.

    The only script-breakout risk is inside the JSON-LD data; the final page
    is asserted to hold exactly the three </script> closers we placed.
    """
    assert "`" not in s and "${" not in s, "unsafe for template literal: %r" % s[:60]
    return s.replace("\\", "\\\\")


def build_hub(slug, cfg):
    items = sorted([i for i in ideas if cfg["select"](i)],
                   key=lambda i: display[i["id"]]["title"].lower())
    assert items, "empty hub: " + slug
    n = len(items)
    desc = "%d %s" % (n, cfg["desc"])
    canon = "https://pickmycostume.com/c/" + slug

    rows = "\n".join(
        '      <li><a href="/c/%s">%s</a><span>%s</span></li>' % (
            i["id"],
            html.escape(display[i["id"]]["title"]),
            html.escape(display[i["id"]]["blurb"]))
        for i in items)

    collection = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": cfg["h1"],
        "description": desc,
        "url": canon,
        "publisher": {"@id": "https://pickmycostume.com/#organization"},
        # First-publication date of the guide corpus (v7 bank, live
        # 2026-09-23). Fixed per page, never regenerated for freshness:
        # no fake freshness.
        "datePublished": "2026-09-23",
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": n,
            "itemListElement": [
                {"@type": "ListItem", "position": k + 1,
                 "url": "https://pickmycostume.com/c/" + i["id"],
                 "name": display[i["id"]]["title"] + " Halloween costume"}
                for k, i in enumerate(items)
            ],
        },
    }
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Pick My Costume",
             "item": "https://pickmycostume.com/"},
            {"@type": "ListItem", "position": 2, "name": "All costume guides",
             "item": "https://pickmycostume.com/costumes"},
            {"@type": "ListItem", "position": 3, "name": cfg["h1"],
             "item": canon},
        ],
    }
    ld = ('<script type="application/ld+json">%s</script>\n'
          '<script type="application/ld+json">%s</script>' % (
              json.dumps(collection, ensure_ascii=False),
              json.dumps(crumbs, ensure_ascii=False)))

    explore = ('<p class="home" style="margin-top:10px">Explore: '
               + ' &middot; '.join(
                   '<a href="/c/%s">%s</a>' % (s2, c2["h1"])
                   for s2, c2 in HUBS.items() if s2 != slug)
               + ' &middot; <a href="/costumes">All costume guides</a>'
               + ' &middot; <a href="/trending">Trending costumes</a>'
               + ' &middot; <a href="/pantry">What you already own</a></p>')

    page = ("<!DOCTYPE html>\n"
            '<html lang="en">\n<head>\n'
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            "<title>%s</title>\n"
            '<meta name="description" content="%s">\n'
            '<link rel="canonical" href="%s">\n'
            '<meta property="og:type" content="website">\n'
            '<meta property="og:title" content="%s">\n'
            '<meta property="og:description" content="%s">\n'
            '<meta property="og:url" content="%s">\n'
            '<meta property="og:image" content="https://pickmycostume.com/images/og/%s.jpg">\n'
            "%s\n"
            "%s\n"
            "<style>%s</style>\n"
            "</head>\n"
            '<body><main class="wrap">\n'
            '<nav class="crumbs" aria-label="Breadcrumb">'
            '<a href="/">Pick My Costume</a> &rsaquo; '
            '<a href="/costumes">All costume guides</a> &rsaquo; %s</nav>\n'
            "<h1>%s</h1>\n"
            '<p class="lede">%s</p>\n'
            '<a class="quizcta" href="/">Take the 2-minute quiz</a>\n'
            "<ul>\n%s\n</ul>\n"
            '%s\n'
            '<footer>Built with Muse.</footer>\n'
            "</main></body></html>\n" % (
                html.escape(cfg["title"]),
                html.escape(desc),
                canon,
                html.escape(cfg["title"]),
                html.escape(desc),
                canon,
                cfg["og_image"],
                ld,
                POSTHOG_SNIPPET,
                CSS,
                html.escape(cfg["h1"]),
                html.escape(cfg["h1"]),
                html.escape(cfg["lede"]),
                rows,
                explore))

    # Billy's rule: no em/en dashes in user-facing copy.
    assert "\u2014" not in page and "\u2013" not in page, "dash slipped into " + slug
    # The only </script> closers must be the ones we placed: the two
    # JSON-LD blocks plus the PostHog snippet. None may appear inside
    # the JSON data itself (script-breakout).
    assert page.count("</script") == 3, "unexpected </script> in " + slug

    out = os.path.join(ROOT, "functions", "c", slug + ".js")
    js = ("/* Generated by hour-session/gen_c_audience_hubs.py from the live "
          + str(len(ids)) +
          "-idea bank. Do not edit by hand; re-run the generator. */\n"
          "var HTML = `%s`;\n\n"
          "export function onRequest(context) {\n"
          "  var url = new URL(context.request.url);\n"
          '  if (url.pathname !== "/c/%s") {\n'
          '    return Response.redirect("https://pickmycostume.com/c/%s", 308);\n'
          "  }\n"
          "  return new Response(HTML, {\n"
          "    headers: {\n"
          '      "Content-Type": "text/html;charset=utf-8",\n'
          '      "Cache-Control": "public, max-age=3600"\n'
          "    }\n"
          "  });\n"
          "}\n" % (js_escape(page), slug, slug))
    open(out, "w", encoding="utf-8").write(js)
    print("wrote %s (%d guides)" % (out, n))
    return slug, items


for s, cfg in HUBS.items():
    build_hub(s, cfg)
