#!/usr/bin/env python3
"""Generator for weather-costume-check.html (repo root).

A Halloween-night weather costume check: parent types a US ZIP, the page pulls
the typical Oct 31 evening temp (Open-Meteo archive, one small per-year request
for the last 7 Oct 31s, or the real hourly forecast once we are inside 16 days
of Halloween) and shows bank-grounded cozy vs mild costume shortlists plus a
copy-paste group-chat card.

Code only, NO deploy. Deterministic: same bank in = byte-identical file out.
Fail-loud: exits non-zero on any bank drift, missing guide/photo, em/en dash
in rendered copy, or a src value rejected by the live LANDING_SRC allowlist.
"""
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "mcp-server", "bank.json")
APP_JS = os.path.join(ROOT, "app.js")
OUT = os.path.join(ROOT, "weather-costume-check.html")
SITE = "https://pickmycostume.com"
PAGE = "/weather-costume-check"
SRC = "share-weather"
PH = "phc_t9dkHXAZR5VEjPFm3K5JDzGKFsNNxKcwSxxcEBEeLbS7"

COZY_KW = re.compile(
    r"\b(hoodie|sweatshirt|coat|jacket|blanket|pajama|pajamas|robe|sweats|"
    r"sweater|onesie|footie|parka|fleece|snowsuit|thermal|turtleneck|sleeping bag)\b"
)
EMDASH = re.compile(r"[—–]")


def fail(msg):
    print("BUILD FAIL: " + msg, file=sys.stderr)
    sys.exit(1)


def esc(s):
    return html.escape(str(s), quote=True)


def display_time(t):
    # 2026-10-22 display rule (Billy, 2026-10-03): displayed time is
    # hands-on only. The bank time may carry a "+ ... drying" suffix
    # that counts in Tonight scoring but is never displayed. Same
    # helper as gen_costumes_hub.py / gen_closet.py.
    return re.sub(r"\s*\+.*drying\s*$", "", t or "")


def main():
    with open(BANK) as f:
        bank = json.load(f)
    ideas = bank["ideas"]
    instr = bank["instructions"]
    n_ideas = len(ideas)
    if n_ideas < 100:
        fail("bank drift: only %d ideas" % n_ideas)
    idea_by_id = {i["id"]: i for i in ideas}

    cozy = [i for i in ideas if COZY_KW.search((i["title"] + " " + i["blurb"]).lower())]
    if len(cozy) < 8:
        fail("cozy shortlist too small: %d" % len(cozy))
    cozy_ids = {i["id"] for i in cozy}

    def guide(slug, section):
        g = instr.get(slug)
        if not g or not g.get("time") or not g.get("effort") or not g.get("m"):
            fail("%s: slug %s missing guide fields (time/effort/m)" % (section, slug))
        return g

    cozy_sorted = sorted(cozy, key=lambda i: (i.get("rank", 999), i["id"]))[:6]
    mild_pool = [i for i in ideas if i["id"] not in cozy_ids]
    mild_sorted = sorted(mild_pool, key=lambda i: (i.get("rank", 999), i["id"]))[:6]

    for section, lst in (("cozy", cozy_sorted), ("mild", mild_sorted)):
        for i in lst:
            slug = i["id"]
            if idea_by_id[slug]["title"] != i["title"]:
                fail("title byte-mismatch for %s" % slug)
            if not os.path.exists(os.path.join(ROOT, "photos", slug + ".webp")):
                fail("missing photo photos/%s.webp" % slug)
            guide(slug, section)

    # Live allowlist check: ?src=share-weather must pass the LANDING_SRC
    # regex. The allowlist moved from index.html to app.js in the
    # 2026-10-01 bundle split (gen_office_kit.py checks app.js the same way).
    index_src = open(APP_JS).read()
    m = re.search(r"\(\?:collection\|print\|share\)-\[a-z-\]\+", index_src)
    if not m:
        fail("could not locate LANDING_SRC regex in app.js")
    allow = re.compile(r"[?&]src=((?:collection|print|share)-[a-z-]+)")
    if not allow.search("?src=" + SRC):
        fail("src=%s rejected by live allowlist" % SRC)

    def card(i):
        slug = i["id"]
        g = guide(slug, "card")
        return (
            '<article class="pick"><a class="picklink" data-slug="%s" '
            'href="/c/%s?src=%s"><img src="photos/%s.webp" alt="%s" loading="lazy">'
            '<h3>%s</h3><p class="triple">⏱ %s</p></a></article>'
            % (esc(slug), esc(slug), SRC, esc(slug), esc(i["title"]),
               esc(i["title"]), esc(display_time(g["time"])))
        )

    cozy_html = "\n".join(card(i) for i in cozy_sorted)
    mild_html = "\n".join(card(i) for i in mild_sorted)

    js_data = json.dumps([
        {"id": i["id"], "title": i["title"],
         "time": display_time(guide(i["id"], "js")["time"]),
         "effort": guide(i["id"], "js")["effort"]}
        for i in cozy_sorted
    ])

    page_html = TEMPLATE % {
        "n_ideas": n_ideas,
        "cozy_html": cozy_html,
        "mild_html": mild_html,
        "js_data": js_data,
        "site": SITE,
        "page": PAGE,
        "src": SRC,
        "ph": PH,
    }
    if EMDASH.search(page_html):
        bad = EMDASH.search(page_html)
        ctx = page_html[max(0, bad.start() - 60):bad.end() + 60]
        fail("em/en dash in rendered copy near: ...%s..." % ctx)

    with open(OUT, "w") as f:
        f.write(page_html)
    print("wrote %s (%d bytes), cozy=%d mild=%d bank=%d"
          % (OUT, len(page_html.encode()), len(cozy_sorted), len(mild_sorted), n_ideas))


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Will It Be Cold on Halloween Night? Cozy Costume Picks | Pick My Costume</title>
<meta name="description" content="Type your ZIP for the typical October 31 evening temperature in your town, then get cozy Halloween costume ideas that fit over real clothes. Free, no signup.">
<link rel="canonical" href="%(site)s%(page)s">
<meta name="robots" content="noindex">
<meta property="og:title" content="Will your costume freeze on Halloween night?">
<meta property="og:description" content="Type your ZIP. Get the typical Oct 31 evening temp and cozy costume ideas built for layers.">
<meta property="og:type" content="website">
<meta property="og:url" content="%(site)s%(page)s">
<meta property="og:image" content="%(site)s/images/og/classic-ghost.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Will your costume freeze on Halloween night?">
<meta name="twitter:description" content="Type your ZIP. Get the typical Oct 31 evening temp and cozy costume ideas built for layers.">
<meta name="twitter:image" content="%(site)s/images/og/classic-ghost.jpg">
<script>
(function(){
  function isQA(){
    try {
      var q = location.search || "";
      if (/[?&](probe|sim|internal)=/.test(q)) return true;
      if (localStorage.getItem("pmc_internal") === "1") return true;
    } catch(e){}
    return false;
  }
  window._pmcQA = isQA();
  var s = document.createElement("script");
  s.async = true;
  s.src = "https://us.i.posthog.com/static/array.js";
  s.onload = function(){
    try {
      if (window.posthog && posthog.init) {
        posthog.init("%(ph)s", {
          api_host: "https://us.i.posthog.com",
          autocapture: false,
          capture_pageview: !window._pmcQA,
          disable_session_recording: true
        });
      }
    } catch(e){}
  };
  document.head.appendChild(s);
})();
function pmcTrack(name, props){
  try {
    props = props || {};
    if (window._pmcQA) props.internal = true;
    if (window.posthog && posthog.capture) posthog.capture(name, props);
  } catch(e){}
}
</script>
<style>
:root{
  --bg:#160d28; --bg2:#211540; --card:#2a1c52; --ink:#fdf3e3; --muted:#cdbcf0;
  --line:#4b3486; --accent:#ff8c1a; --accent-ink:#2a1500; --good:#7ee2a8;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;line-height:1.55}
.wrap{max-width:760px;margin:0 auto;padding:24px 20px 64px}
h1{font-size:30px;line-height:1.2;margin:8px 0 8px}
.lede{color:var(--muted);font-size:17px;margin:0 0 20px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;margin:18px 0}
.card h2{font-size:20px;margin:0 0 4px}
.card p{margin:8px 0}
.ziprow{display:flex;gap:10px;margin-top:12px}
.ziprow input{flex:1;min-height:48px;font-size:18px;border-radius:10px;border:1px solid var(--line);padding:0 14px;background:#120a22;color:var(--ink)}
button.cta{background:var(--accent);color:var(--accent-ink);border:0;border-radius:10px;font-size:17px;font-weight:700;min-height:48px;padding:0 22px;cursor:pointer}
button.cta:active{transform:scale(.98)}
.err{color:#ffb3b3;margin-top:10px;display:none}
.zipnote{font-size:14px;color:var(--muted);margin:0 0 4px}
.result{display:none;margin-top:16px;background:var(--bg2);border:1px solid var(--line);border-radius:12px;padding:16px}
.result .temp{font-size:26px;font-weight:800}
.result .tempsub{color:var(--muted);font-size:14px}
.band{font-size:18px;margin:10px 0 0}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:12px}
@media (max-width:560px){.grid{grid-template-columns:repeat(2,1fr)}}
.pick{background:#1c1136;border:1px solid var(--line);border-radius:12px;overflow:hidden}
.pick a{color:var(--ink);text-decoration:none;display:block}
.pick img{width:100%%;aspect-ratio:1/1;object-fit:cover;display:block}
.pick h3{font-size:15px;margin:8px 10px 2px;line-height:1.3}
.triple{font-size:13px;color:var(--muted);margin:0 10px 10px}
.seclabel{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:22px 0 4px}
.chatbox{width:100%%;min-height:150px;border-radius:10px;border:1px solid var(--line);background:#120a22;color:var(--ink);font-size:15px;padding:12px;font-family:inherit}
.copyrow{margin-top:10px;display:flex;gap:10px;align-items:center}
.copied{color:var(--good);font-weight:700;display:none}
footer.note{color:var(--muted);font-size:13px;margin-top:28px}
a.home{color:var(--muted)}
</style>
</head>
<body>
<div class="wrap">
  <h1>🎃 Will your costume freeze on Halloween night?</h1>
  <p class="lede">Type your ZIP. We look up the typical October 31 evening temperature for your town, then hand you cozy costume ideas from our %(n_ideas)s-idea bank that fit over real clothes.</p>

  <div class="card">
    <h2>📍 Check your Halloween night</h2>
    <p class="zipnote">US ZIP codes only.</p>
    <div class="ziprow">
      <input id="zip" inputmode="numeric" maxlength="5" placeholder="e.g. 98053" aria-label="ZIP code" autocomplete="postal-code">
      <button class="cta" id="gobtn">Check</button>
    </div>
    <p class="err" id="err" role="alert"></p>
    <div class="result" id="result">
      <div class="temp" id="tempLine"></div>
      <div class="tempsub" id="tempSub"></div>
      <p class="band" id="bandLine"></p>
    </div>
  </div>

  <div id="picks" style="display:none">
    <div class="seclabel">🧥 Built for layers</div>
    <div class="grid" id="cozyGrid">
%(cozy_html)s
    </div>
    <div class="seclabel">☀️ Great if it stays mild</div>
    <div class="grid" id="mildGrid">
%(mild_html)s
    </div>
  </div>

  <div class="card" id="shareCard" style="display:none">
    <h2>💬 Send this to the group chat</h2>
    <p>Parents share the temp, not the costume page. Paste this into your class or neighborhood chat:</p>
    <textarea class="chatbox" id="chatText" readonly></textarea>
    <div class="copyrow">
      <button class="cta" id="copybtn">Copy chat text</button>
      <span class="copied" id="copiedMsg">Copied ✅</span>
    </div>
  </div>

  <div class="card">
    <h2>❓ How it works</h2>
    <p>We take your ZIP, find your town, and ask Open-Meteo for the temperature on recent October 31 evenings, 5pm to 8pm local time. Closer to Halloween (inside 16 days), we switch to the real forecast automatically.</p>
    <p>The cozy shortlist is built from our real costume bank: ideas whose build plans are made for layers (hoodies, robes, sweats, jackets). Every pick links to its free step-by-step guide.</p>
  </div>

  <footer class="note">
    Weather data: Open-Meteo (free, no key). Costume ideas: the real Pick My Costume bank.<br>
    <a class="home" href="/">← Back to Pick My Costume</a>
  <br>Built with Muse.</footer>
</div>
<script>
var COZY = %(js_data)s;
var SITE = "%(site)s";
var SRC = "%(src)s";
pmcTrack("weathercheck_viewed", {});

function showErr(msg){
  var e = document.getElementById("err");
  e.textContent = msg; e.style.display = "block";
  // never leave a previous successful lookup on screen next to an error
  document.getElementById("result").style.display = "none";
  document.getElementById("picks").style.display = "none";
  document.getElementById("shareCard").style.display = "none";
  pmcTrack("weathercheck_zip_fail", {reason: msg.slice(0, 60)});
}
function clearErr(){ var e = document.getElementById("err"); e.style.display = "none"; }

document.getElementById("gobtn").addEventListener("click", function(){
  clearErr();
  var zip = (document.getElementById("zip").value || "").trim();
  if (!/^\\d{5}$/.test(zip)) { showErr("That ZIP does not look right. Five digits, like 98053."); return; }
  this.disabled = true; this.textContent = "Checking…";
  var btn = this;
  fetch("https://api.zippopotam.us/us/" + zip).then(function(r){
    if (!r.ok) throw new Error("zip404");
    return r.json();
  }).then(function(z){
    var p = z.places && z.places[0];
    if (!p) throw new Error("zip404");
    var lat = parseFloat(p.latitude), lng = parseFloat(p.longitude);
    var city = p["place name"], state = p["state abbreviation"];
    fetchWeather(lat, lng, city, state);
  }).catch(function(){
    btn.disabled = false; btn.textContent = "Check";
    showErr("Could not find that ZIP. Double check the digits and try again.");
  });

  function fetchWeather(lat, lng, city, state){
    var now = new Date();
    var halloween = new Date(now.getFullYear(), 9, 31);
    var days = Math.ceil((halloween - now) / 86400000);
    function wxFail(){
      btn.disabled = false; btn.textContent = "Check";
      showErr("The weather lookup failed. Your costumes are still here, just without the temp. Try again in a minute.");
    }
    if (days >= 0 && days <= 16) {
      // Real forecast: hourly temps for Oct 31, averaged over 5pm to 8pm local.
      var d = halloween.getFullYear() + "-10-31";
      var url = "https://api.open-meteo.com/v1/forecast?latitude=" + lat + "&longitude=" + lng +
            "&hourly=temperature_2m&start_date=" + d + "&end_date=" + d +
            "&temperature_unit=fahrenheit&timezone=auto";
      fetch(url).then(function(r){
        if (!r.ok) throw new Error("wx");
        return r.json();
      }).then(function(w){ renderForecast(city, state, w); })
      .catch(wxFail);
    } else {
      // Typical: one small request per past Oct 31 (7 x 24 hourly points),
      // instead of one 6-year mega-download on the visitor's phone.
      var endY = days >= 0 ? now.getFullYear() - 1 : now.getFullYear();
      var startY = endY - 6;
      var reqs = [];
      for (var y = startY; y <= endY; y++) {
        (function(yy){
          var u = "https://archive-api.open-meteo.com/v1/archive?latitude=" + lat + "&longitude=" + lng +
                  "&start_date=" + yy + "-10-31&end_date=" + yy + "-10-31&hourly=temperature_2m" +
                  "&temperature_unit=fahrenheit&timezone=auto";
          reqs.push(fetch(u).then(function(r){
            if (!r.ok) throw new Error("wx");
            return r.json();
          }).catch(function(){ return null; })); // one bad year must not sink the other six
        })(y);
      }
      Promise.all(reqs).then(function(all){
        var got = all.filter(function(w){ return w && w.hourly && w.hourly.time; });
        renderTypical(city, state, got, startY, endY);
      }).catch(wxFail);
    }
  }

  // Average the 5pm-8pm local readings across one or more hourly payloads.
  function eveningAvg(hourlyList){
    var vals = [];
    for (var i = 0; i < hourlyList.length; i++) {
      var h = hourlyList[i];
      for (var k = 0; k < h.time.length; k++) {
        var ts = h.time[k];
        if (ts.slice(5, 10) !== "10-31") continue;
        var hr = parseInt(ts.slice(11, 13), 10);
        if (hr >= 17 && hr <= 20) vals.push(h.temperature_2m[k]);
      }
    }
    if (!vals.length) return null;
    var sum = 0;
    for (var j = 0; j < vals.length; j++) sum += vals[j];
    return Math.round(sum / vals.length);
  }

  function noEvening(){
    showErr("No evening readings came back for that town. Try another ZIP.");
    btn.disabled = false; btn.textContent = "Check";
  }

  function renderForecast(city, state, w){
    var t = eveningAvg([w.hourly]);
    if (t === null) { noEvening(); return; }
    finishRender(city, state, t,
      "This Halloween's forecast for " + city + ", " + state + ", 5pm to 8pm.",
      "forecast around " + t + "°F in the evening", "forecast");
  }

  function renderTypical(city, state, all, startY, endY){
    var hours = all.map(function(w){ return w.hourly; });
    var t = eveningAvg(hours);
    if (t === null) { noEvening(); return; }
    finishRender(city, state, t,
      "Typical Halloween evening in " + city + ", " + state + ", 5pm to 8pm, averaged over Oct 31, " + startY + "-" + endY + ".",
      "typically around " + t + "°F in the evening", "typical");
  }

  function finishRender(city, state, t, sub, chatLead, mode){
    var band = t < 45 ? "cold" : (t <= 58 ? "layer" : "mild");
    var bandText = band === "cold"
      ? "🧥 Bundle-up zone. These cozy picks are built for layers."
      : (band === "layer"
        ? "🧣 Layer zone. The cozy picks fit over a coat. The light ones are a gamble."
        : "☀️ Mild night. Anything goes, and the cozy ones still work.");
    document.getElementById("tempLine").textContent = "🌡 " + t + "°F in " + city + ", " + state;
    document.getElementById("tempSub").textContent = sub;
    document.getElementById("bandLine").textContent = bandText;
    document.getElementById("result").style.display = "block";
    document.getElementById("picks").style.display = "block";
    document.getElementById("shareCard").style.display = "block";
    btn.disabled = false; btn.textContent = "Check";
    var titles = COZY.slice(0, 3).map(function(c){ return c.title + " (" + c.time + ", " + c.effort + ")"; }).join("; ");
    var chat = "🎃 Halloween night in " + city + ": " + chatLead + ". " +
      "Cozy costume ideas that fit over layers: " + titles + ". " +
      "Pick yours in 2 minutes, free, no signup: " + SITE + "/?src=" + SRC;
    document.getElementById("chatText").value = chat;
    pmcTrack("weathercheck_zip_ok", {city: city, state: state, temp_f: t, band: band, mode: mode});
  }
});

document.getElementById("copybtn").addEventListener("click", function(){
  var ta = document.getElementById("chatText");
  function done(ok){
    if (ok) {
      document.getElementById("copiedMsg").style.display = "inline";
      pmcTrack("weathercheck_copied", {ok: true});
    } else {
      ta.select();
      pmcTrack("weathercheck_copied", {ok: false});
    }
  }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(ta.value).then(function(){ done(true); }, function(){
      try { ta.select(); document.execCommand("copy"); done(true); } catch(e){ done(false); }
    });
  } else {
    try { ta.select(); document.execCommand("copy"); done(true); } catch(e){ done(false); }
  }
});

document.querySelectorAll(".picklink").forEach(function(a){
  a.addEventListener("click", function(){
    pmcTrack("weathercheck_costume_clicked", {slug: a.getAttribute("data-slug")});
  });
});
</script>
</body>
</html>
"""


if __name__ == "__main__":
    if "--out" in sys.argv:
        OUT = sys.argv[sys.argv.index("--out") + 1]
    main()
