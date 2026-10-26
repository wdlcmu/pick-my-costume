#!/usr/bin/env python3
"""Partner Split (2026-09-27): derive the two halves of every couple-audience
costume idea and generate split.html, the sender page for the "draft your
partner" share loop.

Loop: quiz result (couple idea) -> "Split it with a partner" -> sender picks
their half, names their partner -> native share sheet sends a drafted link ->
partner lands on /c/<slug>?for=<idx>&partner=<name>&s=<sid>&o=split and sees a
"You've been drafted" banner with THEIR half + the full build guide + a quiz
CTA that preserves ?s= attribution.

Halves come from the idea title ("Salt & Pepper" -> ["Salt", "Pepper"]) with
hand-authored overrides for titles that don't split cleanly. load_halves() is
imported by gen_share_function.py so the /c/ guides and split.html can never
disagree about what the halves are.

Usage: python3 gen_split.py   (writes split.html)
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))

# Hand-authored halves for couple titles that don't split cleanly on &/and.
# Trademark-safe, plain-English, each half a wearable identity.
OVERRIDES = {
    "plumber-duo": ["Red plumber", "Green plumber"],
    "office-couple": ["The boss", "The assistant"],
    "burger-joint-couple": ["The cook", "The server"],
    "web-hero-duo": ["The web hero", "The sidekick"],
    "the-olympians": ["The lightning god", "The owl god"],
    "tennis-duo": ["The server", "The receiver"],
    "caped-duo": ["The masked hero", "The partner in crime"],
    "dragon-rider-duo": ["The viking rider", "The dragon"],
    "galaxy-knights": ["The knight", "The squire"],
    "plastic-dream-crew": ["The pink dream", "The dream date"],
    "haunted-portraits": ["The haunted portrait", "The gilt frame"],
    "player-one-two": ["Player One", "Player Two"],
    "tetris-duo": ["The L-block", "The square block"],
    "juke-joint-vampires": ["The trumpet player", "The bandleader"],
    "smores-duo": ["The marshmallow", "The graham cracker"],
    "macabre-couple": ["The goth bride", "The undertaker"],
    # 2026-10-09: bank's own pictured caption is the source of truth:
    # "Pictured: the tooth and the tooth fairy."
    "tooth-fairy": ["The tooth", "The tooth fairy"],
}

_SPLIT_RE = re.compile(r"\s+&\s+|\s+and\s+|\s*\+\s*", re.IGNORECASE)


def _strip_article(s):
    s = s.strip()
    if s[:4].lower() == "the ":
        s = s[4:]
    return s.strip()


def derive_halves(title):
    parts = [p for p in _SPLIT_RE.split(title) if p.strip()]
    if len(parts) != 2:
        return None
    halves = [_strip_article(p) for p in parts]
    if not all(halves) or halves[0].lower() == halves[1].lower():
        return None
    return halves


def load_bank():
    src = open(os.path.join(ROOT, "app.js"), encoding="utf-8").read()  # bank moved to app.js (2026-10-01)
    ideas = re.findall(
        r'\{id:"([^"]+)", title:"([^"]+)", blurb:"([^"]+)"[^}]*?audience:\[([^\]]*)\]',
        src,
    )
    assert ideas, "no ideas parsed from index.html"
    return ideas


def load_halves():
    """{slug: [halfA, halfB]} for every couple-audience idea. Asserts full
    coverage: a bank edit can never silently leave a couple idea half-less."""
    halves = {}
    for slug, title, _blurb, aud in load_bank():
        if "couple" not in aud:
            continue
        h = OVERRIDES.get(slug) or derive_halves(title)
        assert h and len(h) == 2 and all(h), \
            "no halves for couple idea %r (title %r): add an OVERRIDES entry" % (slug, title)
        assert h[0].lower() != h[1].lower(), "identical halves for %s" % slug
        halves[slug] = h
    assert halves, "no couple ideas found in bank"
    return halves


POSTHOG_SNIPPET = """<script>
/* PostHog (same snippet as party.html/school-check.html) */
!function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.async=!0,p.src=s.api_host+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="capture identify alias people.set people.set_once set_config register register_once unregister opt_out_capturing has_opted_out_capturing opt_in_capturing reset isFeatureEnabled onFeatureFlags getFeatureFlag getFeatureFlagPayload reloadFeatureFlags group updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures getActiveMatchingSurveys getSurveys".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);
posthog.init("phc_t9dkHXAZR5VEjPFm3K5JDzGKFsNNxKcwSxxcEBEeLbS7",{api_host:"https://us.i.posthog.com"});
function track(n,p){try{if(window.posthog&&posthog.capture)posthog.capture(n,p||{});}catch(e){}}
</script>"""

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Split the costume | Pick My Costume</title>
<meta name="description" content="Going as a duo this Halloween? Pick your half, draft your partner, and send them their one-tap build guide.">
<link rel="canonical" href="https://pickmycostume.com/split.html">
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#1a1033;color:#f5efff;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;line-height:1.5;padding:20px 16px 64px}}
.wrap{{max-width:520px;margin:0 auto}}
a{{color:#ff9f43}}
h1{{font-size:28px;margin:8px 0 4px}}
.sub{{color:#b8a8d8;margin:0 0 20px}}
.card{{background:#2a1b4d;border:1px solid #4a3578;border-radius:16px;padding:16px;margin:16px 0;text-align:center}}
.card img{{width:100%;border-radius:12px;display:block}}
.card .t{{font-weight:800;font-size:20px;margin:12px 0 2px}}
.card .halves{{color:#b8a8d8;font-size:14px}}
.halfrow{{display:flex;gap:10px;margin:16px 0}}
button.half{{flex:1;background:#2a1b4d;border:2px solid #4a3578;color:#f5efff;border-radius:14px;padding:16px 8px;font-size:16px;font-weight:700;cursor:pointer;min-height:64px}}
button.half.on{{border-color:#ff9f43;background:#3a2666}}
label.lbl{{display:block;font-weight:700;margin:18px 0 6px}}
input.name{{width:100%;background:#241545;border:2px solid #4a3578;color:#f5efff;border-radius:12px;padding:14px;font-size:17px}}
button.cta{{display:block;width:100%;background:#ff9f43;color:#1a1033;font-weight:800;font-size:18px;padding:16px;border:0;border-radius:14px;margin:22px 0 8px;cursor:pointer}}
button.cta:disabled{{opacity:.45;cursor:default}}
a.ghost{{display:block;text-align:center;color:#b8a8d8;margin-top:10px;font-size:15px}}
.status{{min-height:24px;color:#b8a8d8;font-size:14px;text-align:center}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:16px}}
.grid a{{background:#2a1b4d;border:1px solid #4a3578;border-radius:14px;overflow:hidden;text-decoration:none;color:#f5efff}}
.grid img{{width:100%;display:block;aspect-ratio:1/1;object-fit:cover}}
.grid .gt{{padding:10px;font-size:14px;font-weight:700}}
.grid .gh{{padding:0 10px 10px;font-size:12px;color:#b8a8d8}}
.home{{display:inline-block;margin-bottom:8px;color:#b8a8d8;font-size:14px}}
footer{{margin-top:40px;font-size:13px;color:#777;}}</style>
{posthog}
</head>
<body>
<div class="wrap">
<a class="home" href="/">Pick My Costume</a>
<div id="app"></div>
</div>
<script>
var SPLIT_DATA = {data_json};
var app = document.getElementById("app");
var q = new URLSearchParams(location.search || "");
var ideaId = q.get("idea") || "";
/* tapGuard (standing lesson 2026-09-27): finger bounces must not double-fire shares. */
var _lastTap = {{}};
function tapGuard(key, ms){{ var n = Date.now(); if (_lastTap[key] && n - _lastTap[key] < ms) return false; _lastTap[key] = n; return true; }}
function esc(s){{ return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }}
function newShareId(){{ var c="abcdefghijklmnopqrstuvwxyz0123456789",s=""; for(var i=0;i<8;i++) s+=c[Math.floor(Math.random()*c.length)]; return s; }}
function doCopy(t, done){{ function fb(){{ var ta=document.createElement("textarea"); ta.value=t; document.body.appendChild(ta); ta.select(); try{{document.execCommand("copy");}}catch(e){{}} document.body.removeChild(ta); done(true); }} if(navigator.clipboard&&navigator.clipboard.writeText){{ navigator.clipboard.writeText(t).then(function(){{done(true);}},fb); }} else fb(); }}

function renderPicker() {{
  var slugs = Object.keys(SPLIT_DATA).sort(function(a,b){{ return SPLIT_DATA[a].t.localeCompare(SPLIT_DATA[b].t); }});
  var h = "<h1>Split the costume</h1>" +
    "<p class='sub'>Going as a duo this Halloween? Pick the costume, claim your half, and draft your partner. They get their one-tap build guide.</p>" +
    "<div class='grid'>";
  slugs.forEach(function(s){{ var d = SPLIT_DATA[s];
    h += "<a href='/split.html?idea=" + s + "'><img src='" + d.img + "' alt='" + esc(d.t) + " costume' loading='lazy'><div class='gt'>" + esc(d.t) + "</div><div class='gh'>" + esc(d.halves[0]) + " + " + esc(d.halves[1]) + "</div></a>";
  }});
  h += "</div>";
  app.innerHTML = h;
  track("split_view", {{view: "picker"}});
}}

function renderSender(slug) {{
  var d = SPLIT_DATA[slug];
  var myHalf = -1;
  var h = "<h1>Split: " + esc(d.t) + "</h1>" +
    "<p class='sub'>Draft your partner. They get their half and the build guide in one tap.</p>" +
    "<div class='card'><img src='" + d.img + "' alt='" + esc(d.t) + " costume'><div class='t'>" + esc(d.t) + "</div>" +
    "<div class='halves'>" + esc(d.halves[0]) + " + " + esc(d.halves[1]) + "</div></div>" +
    "<label class='lbl'>Which half are you?</label><div class='halfrow'>" +
    "<button type='button' class='half' data-i='0'>" + esc(d.halves[0]) + "</button>" +
    "<button type='button' class='half' data-i='1'>" + esc(d.halves[1]) + "</button></div>" +
    "<label class='lbl' for='pname'>Your partner's name <span style='color:#b8a8d8;font-weight:400'>(optional)</span></label>" +
    "<input class='name' id='pname' maxlength='24' placeholder='e.g. Maya' autocomplete='off'>" +
    "<button type='button' class='cta' id='sendbtn' disabled>Pick your half first</button>" +
    "<a class='ghost' href='/split.html'>Pick a different duo</a>" +
    "<p class='status' id='st'></p>";
  app.innerHTML = h;
  track("split_view", {{view: "sender", idea_id: slug}});
  var btns = app.querySelectorAll("button.half");
  var send = document.getElementById("sendbtn");
  var st = document.getElementById("st");
  btns.forEach(function(b){{ b.onclick = function() {{
    btns.forEach(function(x){{ x.classList.remove("on"); }});
    b.classList.add("on");
    myHalf = parseInt(b.getAttribute("data-i"), 10);
    send.disabled = false;
    send.textContent = "Send them their half";
    track("split_half_picked", {{idea_id: slug, half_idx: myHalf}});
  }}; }});
  function cleanName(s){{ return String(s || "").replace(/[~|&=<>\\"']/g, "").trim().slice(0, 24); }}
  send.onclick = function() {{
    if (myHalf < 0) return;
    if (!tapGuard("splitsend", 2000)) return;
    var theirHalf = 1 - myHalf;
    var pname = cleanName(document.getElementById("pname").value);
    var sid = newShareId();
    var url = "https://pickmycostume.com/c/" + slug + "?for=" + theirHalf +
      (pname ? "&partner=" + encodeURIComponent(pname) : "") +
      "&s=" + sid + "&o=split";
    var text = "I'm going as " + d.halves[myHalf] + " this Halloween. " +
      (pname ? pname + ", you're " : "You're ") + d.halves[theirHalf] + "! " +
      "Your one-tap build guide: " + url;
    function done(ok, via) {{
      if (ok) {{
        st.textContent = via === "native" ? "Shared. Now go build your half." : "Copied. Paste it into any message.";
        track("split_shared", {{idea_id: slug, half_idx: myHalf, share_id: sid, share_origin: "split", via: via}});
        /* 2026-09-27 red-team: the site's attribution chain joins
           share_created.share_id -> recipient_landing_viewed.via_share_id.
           Without share_created, split arrivals are orphans in the funnel
           and the running card-vs-generic open counting misses them. */
        track("share_created", {{share_id: sid, idea_id: slug, share_origin: "split", via: via}});
      }} else {{
        st.textContent = "Share cancelled. Nothing was sent.";
      }}
    }}
    if (navigator.share) {{
      try {{
        navigator.share({{title: "Pick My Costume", text: text, url: url}}).then(
          function(){{ done(true, "native"); }},
          function(){{ done(false); }}
        );
        return;
      }} catch (e) {{}}
    }}
    doCopy(text, function(){{ done(true, "clipboard"); }});
  }};
}}

if (ideaId && SPLIT_DATA[ideaId]) renderSender(ideaId);
else renderPicker();
</script>
<footer>Built with Muse.</footer></body>
</html>
"""


def main():
    halves = load_halves()
    titles = {s: t for s, t, _b, _a in load_bank()}
    data = {}
    for slug, h in sorted(halves.items()):
        title = titles[slug]
        img = "images/og/%s.jpg" % slug
        assert os.path.exists(os.path.join(ROOT, img)), \
            "missing share image for couple idea: " + img
        data[slug] = {"t": title, "halves": h, "img": "/" + img}
    html = PAGE_TEMPLATE.format(
        posthog=POSTHOG_SNIPPET,
        data_json=json.dumps(data),
    )
    # Template uses doubled braces for JS/CSS; the .format above needs the
    # data_json placeholder only. Verify no stray single braces broke it.
    out = os.path.join(ROOT, "split.html")
    open(out, "w", encoding="utf-8").write(html)
    print("wrote %s (%d couple ideas)" % (out, len(data)))


if __name__ == "__main__":
    main()
