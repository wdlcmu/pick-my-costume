#!/usr/bin/env python3
"""Build last-call.html: a deadline-aware last-minute costume page.

Mechanic: client-side JS computes days until the upcoming Oct 31 and shows
only the ideas whose build time fits the remaining runway. Every triple
(time/cost/effort) comes verbatim from bank.json INSTRUCTIONS.

Bands:
  days >= 8 : all 164 ideas ("The runway")
  4..7      : build time <= 60 min ("Build week")
  1..3      : <= 30 min, Easy, no drying ("Last call")
  0         : <= 20 min, Easy, no drying ("Tonight")

Byte-inert by design: writes ../last-call.html only. No inbound links are
added to any live surface; deploy wiring is staged separately.

Fails loudly on bank drift. Deterministic: byte-identical re-runs.
"""
import json, re, sys, os, hashlib, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "mcp-server", "bank.json")
OUT = os.path.join(ROOT, "last-call.html")
SITE = "https://pickmycostume.com"

DASH_RE = re.compile(r'[\u2013\u2014]')
MIN_RE = re.compile(r'(\d+)\s*min')

fails = []
def fail(msg):
    fails.append(msg)

def minutes_and_drying(time_str, iid):
    m = MIN_RE.search(time_str)
    if not m:
        fail("unparseable time %r for %s" % (time_str, iid))
        return None, False
    return int(m.group(1)), ("drying" in time_str.lower())

def main():
    with open(BANK) as f:
        bank = json.load(f)
    ideas = bank["ideas"]
    ins = bank["instructions"]

    if len(ideas) != 138:
        fail("expected 138 ideas, got %d" % len(ideas))
    ids = [i["id"] for i in ideas]
    if len(set(ids)) != len(ids):
        fail("duplicate idea ids")

    recs = []
    for i in ideas:
        iid = i["id"]
        if iid not in ins:
            fail("no instructions for %s" % iid)
            continue
        t, c, e = ins[iid].get("time"), ins[iid].get("cost"), ins[iid].get("effort")
        if not (t and c and e):
            fail("missing triple for %s" % iid)
            continue
        mins, drying = minutes_and_drying(t, iid)
        if mins is None:
            continue
        recs.append({
            "id": iid,
            "title": i["title"],
            "blurb": i["blurb"],
            "time": t, "cost": c, "effort": e,
            "minutes": mins, "drying": drying,
            "tonight": mins <= 30 and e == "Easy" and not drying,
            "rank": i.get("rank", 999),
        })

    # Band filters (mirrored in client JS; keep in sync)
    bands = {
        "runway":    sorted(recs, key=lambda r: r["rank"]),
        "buildweek": sorted([r for r in recs if r["minutes"] <= 60],
                            key=lambda r: (r["minutes"], r["rank"])),
        "lastcall":  sorted([r for r in recs if r["minutes"] <= 30 and r["effort"] == "Easy" and not r["drying"]],
                            key=lambda r: (r["minutes"], r["rank"])),
        "tonight":   sorted([r for r in recs if r["minutes"] <= 20 and r["effort"] == "Easy" and not r["drying"]],
                            key=lambda r: (r["minutes"], r["rank"])),
    }
    for name, lst in bands.items():
        if not lst:
            fail("band %s is empty" % name)

    # Page copy (user-facing): dash lint applies to all of it
    copy = {
        "runway_title": "Halloween is {n} days out. Build something good.",
        "runway_sub": "Every idea below has a real step-by-step build guide with a real build time. Filter yourself by how much time you actually have.",
        "buildweek_title": "{n} days left. This is build week.",
        "buildweek_sub": "Only showing costumes that take an hour or less to build, fastest first.",
        "lastcall_title": "{n} days left. Only showing what you can actually finish.",
        "lastcall_sub": "Quick, easy builds with no drying time. Pick one, build it, wear it.",
        "tonight_title": "Halloween is tonight. Only showing what you can make right now.",
        "tonight_sub": "Twenty minutes or less, easy, no drying. You have got this.",
        "share_runway": "Halloween is {n} days out and I finally picked a costume plan. This site only shows builds with real times: {url}",
        "share_buildweek": "Halloween is {n} days out and I still have no costume. This page only shows builds I can finish in under an hour: {url}",
        "share_lastcall": "Halloween is {n} days away and I still have no costume. Only showing what I can actually finish: {url}",
        "share_tonight": "Halloween is TONIGHT and I have no costume. This page only shows what I can make right now: {url}",
        "method": "Build times come from our own 164-idea costume bank. Nothing here is a guess: every time, cost, and effort label is the one attached to that costume's build guide.",
    }
    for k, v in copy.items():
        if DASH_RE.search(v):
            fail("em/en dash in copy %s" % k)
    for r in recs:
        if DASH_RE.search(r["title"] + " " + r["blurb"]):
            fail("em/en dash in idea %s" % r["id"])

    payload = {"ideas": [
        {k: r[k] for k in ("id", "title", "blurb", "time", "cost", "effort",
                           "minutes", "drying", "tonight", "rank")}
        for r in recs
    ]}
    ideas_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    # Sanity: round-trip and id coverage
    back = json.loads(ideas_json)
    if {r["id"] for r in back["ideas"]} != set(ids):
        fail("embedded JSON id mismatch")

    # Static ItemList for SEO: tonight band, top 12, labeled honestly
    itemlist = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Fastest Halloween costume builds in our 164-idea bank",
        "itemListElement": [
            {"@type": "ListItem", "position": p + 1,
             "name": r["title"], "url": "%s/c/%s?src=share-lastcall" % (SITE, r["id"])}
            for p, r in enumerate(bands["tonight"][:12])
        ],
    }

    faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question",
             "name": "I left my costume to the last minute. What can I still make?",
             "acceptedAnswer": {"@type": "Answer",
                "text": "This page filters our 164-idea costume bank by how many days are left until Halloween, using each costume's real build time. With one to three days left, it only shows easy builds of 30 minutes or less with no drying time."}},
            {"@type": "Question",
             "name": "Where do the build times come from?",
             "acceptedAnswer": {"@type": "Answer",
                "text": "Every time, cost, and effort label on this page is the one attached to that costume's step-by-step build guide in our own costume bank. Nothing is estimated for this page."}},
            {"@type": "Question",
             "name": "Can I make one of these tonight?",
             "acceptedAnswer": {"@type": "Answer",
                "text": "Costumes marked Make tonight take 30 minutes or less, are rated easy, and need no drying time. Each one links to its full build guide."}},
        ],
    }

    page = PAGE_TEMPLATE
    page = page.replace("__IDEAS_JSON__", ideas_json)
    page = page.replace("__COPY_JSON__", json.dumps(copy, sort_keys=True, ensure_ascii=False))
    page = page.replace("__ITEMLIST_JSON__", json.dumps(itemlist, ensure_ascii=False, indent=1))
    page = page.replace("__FAQ_JSON__", json.dumps(faq, ensure_ascii=False, indent=1))
    # visible FAQ section (mirrors the FAQPage JSON-LD above, kept in sync)
    faq_items = "\n".join(
        '<details class="faq">\n<summary>%s</summary>\n<p>%s</p>\n</details>' % (
            html.escape(q["name"]), html.escape(q["acceptedAnswer"]["text"]))
        for q in faq["mainEntity"])
    faq_html = (
        '<section class="pmc-faq" id="pmc-faq">\n<style>\n'
        '.pmc-faq{margin:32px 0}\n'
        '.pmc-faq h2{font-size:22px;margin:0 0 8px}\n'
        '.pmc-faq details{margin:8px 0;border:1px solid rgba(140,140,160,.4);border-radius:10px;padding:10px 14px}\n'
        '.pmc-faq summary{cursor:pointer;font-weight:700}\n'
        '.pmc-faq p{margin:8px 0 4px;line-height:1.55}\n'
        '</style>\n<h2>Common questions</h2>\n' + faq_items + '\n</section>')
    page = page.replace("__FAQ_HTML__", faq_html)
    page = page.replace("__BAND_COUNTS__", json.dumps({k: len(v) for k, v in bands.items()}, sort_keys=True))

    if "__" in page and re.search(r'__[A-Z_]+__', page):
        fail("unreplaced placeholder left in page")

    if fails:
        print("BUILD FAILED:")
        for m in fails:
            print(" -", m)
        sys.exit(1)

    with open(OUT, "w") as f:
        f.write(page)
    h = hashlib.sha256(page.encode()).hexdigest()[:12]
    print("wrote %s (%d bytes, sha %s)" % (OUT, len(page), h))
    print("bands: " + ", ".join("%s=%d" % (k, len(v)) for k, v in bands.items()))

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Last-Call Halloween Costumes: What You Can Still Make</title>
<meta name="description" content="Halloween is coming fast. This page filters 164 real costume builds by how many days are left, using each costume's real build time, and only shows what you can actually finish. Free, no signup.">
<link rel="canonical" href="https://pickmycostume.com/last-call">
<meta property="og:title" content="Last-Call Halloween Costumes">
<meta property="og:description" content="Only showing costumes you can actually finish before Halloween, filtered by the real build time.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://pickmycostume.com/last-call">
<meta property="og:image" content="https://pickmycostume.com/images/og/neon-demon-hunter.jpg">
<meta property="og:image:secure_url" content="https://pickmycostume.com/images/og/neon-demon-hunter.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
__ITEMLIST_JSON__
</script>
<script type="application/ld+json">
__FAQ_JSON__
</script>
<style>
  :root{ --bg:#14092b; --card:#1f1140; --ink:#f5efff; --muted:#c9bce8; --acc:#ffb020; --acc2:#7ef0c1; --line:#3a2568; --hot:#ff6b6b; }
  *{ box-sizing:border-box; }
  body{ margin:0; background:var(--bg); color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
  .wrap{ max-width:920px; margin:0 auto; padding:20px 16px 64px; }
  header.hero{ text-align:center; padding:28px 8px 8px; }
  .clock{ font-size:44px; }
  h1{ font-size:30px; margin:10px 0 6px; letter-spacing:-0.5px; }
  .sub{ color:var(--muted); font-size:16px; margin:0 auto 6px; max-width:620px; line-height:1.5; }
  .bandtag{ display:inline-block; margin-top:10px; padding:6px 14px; border:1px solid var(--line); border-radius:999px; color:var(--acc); font-weight:700; font-size:14px; }
  .bandtag.hot{ color:var(--hot); border-color:var(--hot); }
  .quizcta{ display:inline-block; margin:14px 0 0; padding:12px 26px; border-radius:999px; background:var(--acc); color:#241300; font-weight:800; font-size:16px; text-decoration:none; }
  .quizcta:active{ transform:scale(0.97); }
  .sharebtn{ display:inline-block; margin:14px 0 0 8px; padding:12px 22px; border-radius:999px; background:transparent; color:var(--ink); font-weight:700; font-size:16px; border:1px solid var(--line); cursor:pointer; }
  .grid{ display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:14px; margin-top:26px; }
  .card{ background:var(--card); border:1px solid var(--line); border-radius:16px; padding:16px; display:flex; flex-direction:column; }
  .card h2{ margin:0 0 6px; font-size:19px; }
  .triple{ display:flex; gap:6px; flex-wrap:wrap; margin-bottom:10px; }
  .tchip{ font-size:12px; font-weight:700; padding:4px 10px; border-radius:999px; background:#2a1750; color:var(--acc2); border:1px solid var(--line); }
  .blurb{ color:var(--muted); font-size:14px; line-height:1.5; margin:0 0 12px; flex:1; }
  .guide{ display:block; text-align:center; padding:11px 14px; border-radius:12px; font-weight:700; font-size:15px; text-decoration:none; background:var(--acc2); color:#0b2b1d; }
  .tonightbadge{ align-self:flex-start; font-size:11px; font-weight:800; letter-spacing:1px; color:#241300; background:var(--acc); border-radius:6px; padding:3px 10px; margin-bottom:8px; }
  .method{ margin-top:34px; padding:16px 18px; border:1px dashed var(--line); border-radius:14px; color:var(--muted); font-size:13.5px; line-height:1.6; }
  footer{ margin-top:30px; text-align:center; color:var(--muted); font-size:13px; }
  footer a{ color:var(--acc2); }
</style>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <div class="clock" aria-hidden="true">⏰</div>
    <h1 id="band-title">Loading...</h1>
    <p class="sub" id="band-sub"></p>
    <div><span class="bandtag" id="band-tag"></span></div>
    <div>
      <a class="quizcta" id="quiz-cta" href="https://pickmycostume.com/?src=share-lastcall">Take the 2-minute quiz</a>
      <button class="sharebtn" id="share-btn" type="button">Share my deadline</button>
    </div>
  </header>
  <main><div class="grid" id="grid"></div></main>
  <section class="method" id="method"></section>
  __FAQ_HTML__
  <footer>Built with Muse. &middot; <a href="https://pickmycostume.com/?src=share-lastcall">pickmycostume.com</a></footer>
</div>
<script>
(function(){
  var IDEAS = __IDEAS_JSON__.ideas;
  var COPY = __COPY_JSON__;
  var SITE = "https://pickmycostume.com";
  var URL = SITE + "/last-call?src=share-lastcall"; /* 2026-09-27 attribution audit: inbound share URL attributes the arrival leg (quiz CTA on the page carries src=share-lastcall) */

  function track(name, props){
    if (window.posthog && posthog.capture) posthog.capture(name, props || {});
  }

  function daysToHalloween(now){
    now = now || new Date();
    var y = now.getFullYear();
    var h = new Date(y, 9, 31, 23, 59, 59);
    if (now > h) h = new Date(y + 1, 9, 31, 23, 59, 59);
    return Math.round((h - now) / 86400000);
  }

  function bandFor(days){
    if (days <= 0) return "tonight";
    if (days <= 3) return "lastcall";
    if (days <= 7) return "buildweek";
    return "runway";
  }

  function filterFor(band, ideas){
    var out = ideas.filter(function(r){
      if (band === "runway") return true;
      if (r.minutes > (band === "buildweek" ? 60 : band === "lastcall" ? 30 : 20)) return false;
      if (band === "buildweek") return true;
      return r.effort === "Easy" && !r.drying;
    });
    if (band === "runway") out.sort(function(a,b){ return a.rank - b.rank; });
    else out.sort(function(a,b){ return (a.minutes - b.minutes) || (a.rank - b.rank); });
    return out;
  }

  var BAND_TEXT = {
    runway:    {title: COPY.runway_title,    sub: COPY.runway_sub,    tag: "THE RUNWAY", share: COPY.share_runway,    hot: false},
    buildweek: {title: COPY.buildweek_title, sub: COPY.buildweek_sub, tag: "BUILD WEEK", share: COPY.share_buildweek, hot: false},
    lastcall:  {title: COPY.lastcall_title,  sub: COPY.lastcall_sub,  tag: "LAST CALL",   share: COPY.share_lastcall,  hot: true},
    tonight:   {title: COPY.tonight_title,   sub: COPY.tonight_sub,   tag: "TONIGHT",     share: COPY.share_tonight,   hot: true}
  };

  function esc(s){ return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }

  function cardHTML(r){
    var badge = r.tonight ? '<span class="tonightbadge">MAKE TONIGHT</span>' : '';
    return '<article class="card">' + badge +
      '<h2>' + esc(r.title) + '</h2>' +
      '<div class="triple"><span class="tchip">' + esc(r.time) + '</span>' +
      '<span class="tchip">' + esc(r.cost) + '</span>' +
      '<span class="tchip">' + esc(r.effort) + '</span></div>' +
      '<p class="blurb">' + esc(r.blurb) + '</p>' +
      '<a class="guide" href="' + SITE + '/c/' + esc(r.id) + '?src=share-lastcall">Build guide</a></article>';
  }

  function render(now){
    var days = daysToHalloween(now);
    var band = bandFor(days);
    var t = BAND_TEXT[band];
    var title = t.title.replace("{n}", String(days));
    document.getElementById("band-title").textContent = title;
    document.getElementById("band-sub").textContent = t.sub;
    var tag = document.getElementById("band-tag");
    tag.textContent = t.tag + (band === "tonight" ? "" : ": " + days + (days === 1 ? " DAY" : " DAYS"));
    if (t.hot) tag.classList.add("hot");
    var list = filterFor(band, IDEAS);
    document.getElementById("grid").innerHTML = list.map(cardHTML).join("");
    document.getElementById("method").textContent = COPY.method;
    track("lastcall_viewed", {band: band, days: days, count: list.length});
    return {days: days, band: band, count: list.length, title: title};
  }

  function share(now){
    var days = daysToHalloween(now);
    var band = bandFor(days);
    var text = BAND_TEXT[band].share.replace("{n}", String(days)).replace("{url}", URL);
    var done = function(via){ track("lastcall_shared", {band: band, days: days, via: via}); };
    if (navigator.share) {
      navigator.share({title: "Last-Call Halloween Costumes", text: text})
        .then(function(){ done("native"); }).catch(function(){});
    } else if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(function(){
        done("clipboard");
        alert("Copied. Paste it into any chat so nobody else shows up empty-handed.");
      });
    } else {
      window.prompt("Copy this:", text);
      done("prompt");
    }
  }

  document.getElementById("share-btn").addEventListener("click", function(){ share(); });
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function(){ render(); });
  } else { render(); }

  window.LastCall = { daysToHalloween: daysToHalloween, bandFor: bandFor,
                      filterFor: filterFor, render: render, share: share,
                      ideas: IDEAS, BAND_TEXT: BAND_TEXT, COPY: COPY };
})();
</script>
<script>
  (function(){
    var s = document.createElement("script"); s.async = true;
    s.src = "https://us.i.posthog.com/static/array.js";
    s.onload = function(){
      if (window.posthog && posthog.init) {
        posthog.init("phc_t9dkHXAZR5VEjPFm3K5JDzGKFsNNxKcwSxxcEBEeLbS7", {
          api_host: "https://us.i.posthog.com", autocapture: false,
          persistence: "memory"
        });
      }
    };
    document.head.appendChild(s);
  })();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
