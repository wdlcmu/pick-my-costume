#!/usr/bin/env python3
"""Build lineup.html: the family lineup RSVP page (LIVE at /lineup).

One organizer picks a group theme and texts one link to the family group
chat. Each member opens the link, taps a spot, and gets their costume idea
with time, build guide, and their own share text. 1 share -> N visits.

Data: hour-session/lineup-data.json (themes -> spots). Theme curation
(names, taglines, spot membership/order) is editorial and lives in that
file; every spot title/blurb comes from mcp-server/bank.json and every
time is the bank time with drying stripped (display rule, hands-on
only). No cost field: the bank dropped cost site-wide on 2026-10-01.
Regenerate the data from the current bank with the derivation in
family-d-leftovers-2026-10-22.md, then: python3 hour-session/build_lineup.py

2026-10-22 repair (parity audit Family D): the old data path was
/tmp/lineup-data.json, which no longer exists, and the template had
fallen behind the live page (no share-id loop measurement) and still
demanded the removed cost field. The live page's 2026-09-27 sid-minting
block and handlers are ported back into this template verbatim, the
data file is repo-local now, and every run re-verifies the data against
bank.json (slug set, titles, blurbs, display times) before writing.
"""
import json, html, re, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   'lineup-data.json')))
SITE = "https://pickmycostume.com"

def display_time(t):
    return re.sub(r'\s*\+.*drying\s*$', '', t or '')

# Re-verify the data against the current bank on every run (fail loudly,
# never emit a stale page silently): slug set, titles, blurbs, and
# display times (hands-on only) must match bank.json exactly. Counts
# are derived from the data itself, never hard-coded.
_bank = json.load(open(os.path.join(BASE, 'mcp-server', 'bank.json')))
_bank_ideas = {i['id']: i for i in _bank['ideas']}
_bank_ins = _bank['instructions']
assert len(_bank_ideas) >= 100, 'bank.json yielded %d ideas (< 100)' % len(_bank_ideas)
_n_spots = 0
for _theme in DATA:
    assert _theme['spots'], 'theme %s has no spots' % _theme['slug']
    for _sp in _theme['spots']:
        _n_spots += 1
        _b = _bank_ideas.get(_sp['slug'])
        assert _b is not None, 'lineup slug not in bank: %s' % _sp['slug']
        assert _sp['title'] == _b['title'], 'title drift for %s' % _sp['slug']
        assert _sp['blurb'] == _b['blurb'], 'blurb drift for %s' % _sp['slug']
        assert _sp['time'] == display_time(_bank_ins[_sp['slug']].get('time')), \
            'time drift for %s' % _sp['slug']
assert _n_spots >= 20, 'lineup data vacuous: %d spots' % _n_spots

def esc(s):
    return html.escape(s, quote=True)

def dash_check(s):
    assert "\u2014" not in s and "\u2013" not in s, "em/en dash found: %r" % s[:60]

THEME_CARDS = []
SPOT_SECTIONS = []
DATA_JS = []

for theme in DATA:
    tslug = theme["slug"]
    dash_check(theme["name"]); dash_check(theme["tagline"])
    n = len(theme["spots"])
    word = "spot" if n == 1 else "spots"
    THEME_CARDS.append(
        '<a class="themecard" href="/lineup?t=%s">'
        '<span class="themename">%s</span>'
        '<span class="themetag">%s</span>'
        '<span class="themen">%d %s</span></a>'
        % (esc(tslug), esc(theme["name"]), esc(theme["tagline"]), n, word))
    spots_js = []
    for i, sp in enumerate(theme["spots"]):
        for k in ("title", "blurb", "time"):
            dash_check(sp[k])
        spots_js.append('{"slug":%s,"title":%s,"blurb":%s,"time":%s}' % (
            json.dumps(sp["slug"]), json.dumps(sp["title"]),
            json.dumps(sp["blurb"]), json.dumps(sp["time"])))
    DATA_JS.append('"%s":{"name":%s,"tagline":%s,"spots":[%s]}' % (
        tslug, json.dumps(theme["name"]), json.dumps(theme["tagline"]), ",".join(spots_js)))

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Family Costume Lineup - Pick My Costume</title>
<meta name="description" content="Pick a group theme, text one link to the family chat, and everyone grabs their own costume spot. Free, no signup, no ads.">
<link rel="canonical" href="https://pickmycostume.com/lineup">
<meta property="og:type" content="website">
<meta property="og:url" content="https://pickmycostume.com/lineup">
<meta property="og:title" content="Family Costume Lineup - Pick My Costume">
<meta property="og:description" content="One theme, one link, everyone gets their costume. Text it to the family group chat.">
<meta property="og:image" content="https://pickmycostume.com/images/og/emoji-crew.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Family Costume Lineup - Pick My Costume">
<meta name="twitter:description" content="One theme, one link, everyone gets their costume.">
<meta name="twitter:image" content="https://pickmycostume.com/images/og/emoji-crew.jpg">
<style>
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;margin:0;padding:0 16px 64px;background:#fff8f0;color:#2b2118}
.wrap{max-width:640px;margin:0 auto}
h1{font-size:26px;margin:28px 0 6px}
.sub{color:#6b5b4c;margin:0 0 20px;font-size:15px}
.themegrid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.themecard{display:block;border:2px solid #ead9c2;border-radius:14px;padding:14px;text-decoration:none;color:inherit;background:#fff}
.themecard:active{border-color:#e07830}
.themename{font-weight:700;font-size:16px;display:block}
.themetag{font-size:13px;color:#6b5b4c;display:block;margin:4px 0}
.themen{font-size:12px;color:#a08a70}
.spotcard{border:2px solid #ead9c2;border-radius:14px;padding:14px;margin:0 0 12px;background:#fff}
.spotcard.claimed{border-color:#7ab648;background:#f6fbee}
.spothead{display:flex;justify-content:space-between;align-items:baseline}
.spotnum{font-size:12px;color:#a08a70;text-transform:uppercase;letter-spacing:.06em}
.spottitle{font-weight:700;font-size:18px;margin:4px 0}
.triple{font-size:13px;color:#6b5b4c;margin:0 0 6px}
.blurb{font-size:14px;margin:0 0 10px}
.btnrow{display:flex;flex-wrap:wrap;gap:8px}
.btn{display:inline-block;padding:10px 14px;border-radius:10px;font-size:14px;font-weight:600;text-decoration:none;border:2px solid #e07830;color:#e07830;background:#fff;cursor:pointer;min-height:44px;box-sizing:border-box}
.btn.primary{background:#e07830;color:#fff;border-color:#e07830}
.btn:disabled{opacity:.5}
.claimedby{font-size:13px;color:#4c7a2a;font-weight:600;margin:6px 0 0}
.sharebox{border:2px dashed #e07830;border-radius:14px;padding:16px;margin:24px 0;background:#fff}
.sharebox h2{font-size:18px;margin:0 0 6px}
.sharebox p{font-size:14px;color:#6b5b4c;margin:0 0 12px}
.note{font-size:12px;color:#a08a70;margin:16px 0}
.back{display:inline-block;margin:18px 0;font-size:14px;color:#e07830}
.hidden{display:none!important}
footer{margin-top:40px;font-size:13px;color:#777;}</style>
</head>
<body>
<div class="wrap">
<div id="picker">
<h1>Pick a family lineup</h1>
<p class="sub">Choose a theme, text one link to the family group chat, and everyone grabs their own costume spot. Free, no signup, no ads.</p>
<div class="themegrid">
__THEME_CARDS__
</div>
<p class="note">New here? The <a href="/?src=share-lineup">2-minute quiz</a> picks a costume for one person. Lineups are for the whole crew.</p>
</div>
<div id="themeview" class="hidden">
<a class="back" href="/lineup">&larr; All lineups</a>
<h1 id="tname"></h1>
<p class="sub" id="ttag"></p>
<div id="spots"></div>
<div class="sharebox">
<h2>Send it to the family chat</h2>
<p>One link. Everyone taps in and claims a spot.</p>
<div class="btnrow">
<button class="btn primary" id="smsbtn">Text the family</button>
<button class="btn" id="copybtn">Copy invite link</button>
</div>
</div>
<p class="note">Claims save on this phone only, so if two people want the same spot, the group chat settles it.</p>
</div>
</div>
<script>
/* PURE-TESTABLE-START */
var THEMES = {__THEMES__};
var SITE = "https://pickmycostume.com";
function parseLineupParams(qs){
  var m = /[?&]t=([a-z0-9-]+)/.exec(qs || "");
  var t = m ? m[1] : "";
  return { theme: (t && THEMES[t]) ? t : "" };
}
function claimKey(theme){ return "pmc_lineup_" + theme; }
function getClaims(theme){
  try { return JSON.parse(localStorage.getItem(claimKey(theme)) || "{}"); }
  catch(e){ return {}; }
}
function setClaim(theme, idx, name){
  var c = getClaims(theme); c[String(idx)] = name;
  try { localStorage.setItem(claimKey(theme), JSON.stringify(c)); } catch(e){}
  return c;
}
/* 2026-09-27 loop measurement: one anonymous share id per lineup theme
   page load; minted fresh per share click so each invite is traceable. */
var LINEUP_SID = "";
function newLineupSid(){var a="abcdefghijklmnopqrstuvwxyz0123456789",s="";for(var i=0;i<8;i++)s+=a[Math.floor(Math.random()*a.length)];return s;}
function buildInviteUrl(theme){ return SITE + "/lineup?t=" + theme + "&s=" + (LINEUP_SID || (LINEUP_SID = newLineupSid())) + "&src=share-lineup-invite"; }
function buildSmsUrl(theme){
  var body = "Pick your costume from our " + THEMES[theme].name + " family lineup: " + buildInviteUrl(theme);
  return "sms:?&body=" + encodeURIComponent(body);
}
function buildSpotText(theme, idx){
  var th = THEMES[theme], sp = th.spots[idx];
  return "I am the " + sp.title + " in our " + th.name + " lineup (" + sp.time + "). Grab your spot: " + buildInviteUrl(theme);
}
function buildGuideUrl(theme, slug){ return "/c/" + slug + "?src=share-lineup-" + theme; }
function buildPickUrl(theme, slug){ return "/?pick=" + slug + "&src=share-lineup-" + theme; }
/* PURE-TESTABLE-END */

/* PostHog: anonymous usage stats only. No names are ever sent. */
(function(){
  var s = document.createElement("script");
  s.async = true;
  s.src = "https://us.i.posthog.com/static/array.js";
  s.onload = function(){
    try { if (window.posthog && posthog.init) posthog.init("phc_t9dkHXAZR5VEjPFm3K5JDzGKFsNNxKcwSxxcEBEeLbS7", {api_host:"https://us.i.posthog.com", autocapture:false}); } catch(e){}
  };
  document.head.appendChild(s);
})();
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

function escHtml(s){
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function renderTheme(theme){
  var th = THEMES[theme];
  document.getElementById("picker").classList.add("hidden");
  document.getElementById("themeview").classList.remove("hidden");
  document.getElementById("tname").textContent = th.name + " lineup";
  document.getElementById("ttag").textContent = th.tagline + " Tap a spot to claim it.";
  document.title = th.name + " Lineup - Pick My Costume";
  var claims = getClaims(theme);
  var html = "";
  th.spots.forEach(function(sp, i){
    var who = claims[String(i)];
    html += '<div class="spotcard' + (who ? ' claimed' : '') + '">'
      + '<div class="spothead"><span class="spotnum">Spot ' + (i+1) + ' of ' + th.spots.length + '</span></div>'
      + '<div class="spottitle">' + escHtml(sp.title) + '</div>'
      + '<p class="triple">' + escHtml(sp.time) + '</p>'
      + '<p class="blurb">' + escHtml(sp.blurb) + '</p>'
      + '<div class="btnrow">'
      + '<a class="btn" href="' + escHtml(buildGuideUrl(theme, sp.slug)) + '">Build guide</a>'
      + '<a class="btn" href="' + escHtml(buildPickUrl(theme, sp.slug)) + '">Open in quiz</a>'
      + (who
          ? '<button class="btn" disabled>Claimed</button>'
          : '<button class="btn primary" data-claim="' + i + '">This is mine</button>')
      + '<button class="btn" data-copytext="' + i + '">Copy my text</button>'
      + '</div>'
      + (who ? '<p class="claimedby">Claimed by ' + escHtml(who) + '</p>' : '')
      + '</div>';
  });
  document.getElementById("spots").innerHTML = html;
  track("lineup_opened", {theme: theme});
}

function init(){
  var p = parseLineupParams(location.search);
  if (!p.theme){
    document.getElementById("picker").classList.remove("hidden");
    return;
  }
  /* 2026-09-27 loop measurement: recipient leg. */
  (function(){var vsm=/[?&]s=([a-z0-9]{8,})/.exec(location.search||"");if(vsm)track("lineup_opened",{theme:p.theme,via_share_id:vsm[1],share_origin:"lineup"});})();
  renderTheme(p.theme);
  document.getElementById("smsbtn").addEventListener("click", function(){
    LINEUP_SID = newLineupSid();
    track("lineup_invite_shared", {theme: p.theme, channel: "sms", share_id: LINEUP_SID, share_origin: "lineup"});
    location.href = buildSmsUrl(p.theme);
  });
  document.getElementById("copybtn").addEventListener("click", function(){
    LINEUP_SID = newLineupSid();
    var url = buildInviteUrl(p.theme);
    function done(){ track("lineup_invite_shared", {theme: p.theme, channel: "copy", share_id: LINEUP_SID, share_origin: "lineup"}); }
    if (navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(url).then(done, function(){ prompt("Copy this link:", url); });
    } else { prompt("Copy this link:", url); }
  });
  document.getElementById("spots").addEventListener("click", function(ev){
    var t = ev.target;
    if (t.hasAttribute("data-claim")){
      var idx = parseInt(t.getAttribute("data-claim"), 10);
      var name = prompt("Who is taking this spot? (first name is plenty)");
      if (name && name.trim()){
        setClaim(p.theme, idx, name.trim().slice(0, 24));
        track("lineup_spot_claimed", {theme: p.theme, spot: idx});
        renderTheme(p.theme);
      }
    } else if (t.hasAttribute("data-copytext")){
      var i2 = parseInt(t.getAttribute("data-copytext"), 10);
      LINEUP_SID = newLineupSid();
      var txt = buildSpotText(p.theme, i2);
      track("lineup_slot_text_copied", {theme: p.theme, spot: i2, share_id: LINEUP_SID, share_origin: "lineup"});
      if (navigator.clipboard && navigator.clipboard.writeText){
        navigator.clipboard.writeText(txt).then(function(){}, function(){ prompt("Copy your text:", txt); });
      } else { prompt("Copy your text:", txt); }
    }
  });
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
</script>
<footer>Built with Muse.</footer></body>
</html>
"""

page = (PAGE
        .replace("__THEME_CARDS__", "\n".join(THEME_CARDS))
        .replace("__THEMES__", ",".join(DATA_JS)))
dash_check(page)
out = os.path.join(BASE, "lineup.html")
open(out, "w").write(page)
print("wrote", out, len(page), "bytes")
