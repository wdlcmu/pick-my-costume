#!/usr/bin/env python3
"""Build party.html: the office/friend-group Halloween party invite page (STAGED, no deploy).

The mechanic: one host picks a costume theme + date and sends ONE link to the
work or friend group chat. Every attendee opens the link and lands on a pretty
invite card with a "Find my costume" quiz CTA. 1 share -> N visits, and it is a
brand-new social graph vs the existing loops (family lineup, classroom,
office contest kit organizer tools).

Recipient URL: /party?t=<theme-slug>&d=<date>&n=<party-name>
Attribution: o=invite on the quiz CTA (NOT o=partyinvite: index.html's origin
regex has no terminators and "partyinvite" prefix-matches the flag-OFF
party-link experiment's o=party arm -- same D1 generic_quick lesson), and
via=partyinvite-<theme> on guide chips. PostHog events
partyinvite_created / partyinvite_opened / partyinvite_shared /
partyinvite_quiz_clicked / partyinvite_costume_clicked (chip taps),
all with the standing probe/sim exclusion.

Theme data: embedded literal, sourced from /tmp/lineup-data.json (the
lineup stream's verified extraction: all slugs checked against
mcp-server/bank.json). Re-extract with the one-liner in the docstring of
build_lineup.py if themes change.

Byte-inert: new file only. No inbound links from any live surface, not in
sitemap.xml. Deploy-time wiring is the main agent's call.

Also emits functions/party.js (2026-09-27 consolidation): the per-party
og-injection worker's PARTY_OG table used to be a third hand-maintained copy
of the theme list (build_party.py -> party.html -> functions/party.js). It is
now generated from THEMES below, so a theme edit regenerates all three from
the single source. The representative og image per theme is its first costume
spot (same convention as the hand-written table this replaced); existence is
asserted at generation time.

Tap targets: .costumechip carries min-height:44px + inline-flex centering
(mirroring .btn's existing 44px convention) so chips meet the iOS 44px
guideline while keeping the pill chip look (R5 red-team fix, 2026-09-27).
Applied globally, not media-scoped: jsdom 22 (the harness toolchain) has no
matchMedia/media-query evaluation, so a media-scoped rule would be
unverifiable, and the chips only live on the phone-first invite card.

Regenerate: python3 hour-session/build_party.py
"""
import json, html, os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://pickmycostume.com"

def esc(s):
    return html.escape(s, quote=True)

def dash_check(s):
    assert "\u2014" not in s and "\u2013" not in s, "em/en dash found in %r" % s[:60]

# Theme data: slug -> {name, tagline, spots:[{slug,title}]}.
# Sourced 2026-09-27 from /tmp/lineup-data.json (lineup stream, slugs verified
# against mcp-server/bank.json). Embedded here so regeneration does not depend
# on /tmp (wiped without warning).
THEMES = [
    {"slug": "heroes-night", "name": "Movie Heroes Night",
     "tagline": "Five big-screen heroes. No sewing, no stress.",
     "spots": [("tin-hero", "The Tin Hero"), ("wizard", "Classic Wizard"),
               ("cardboard-knight", "Cardboard Knight"),
               ("galaxy-knights", "Galaxy Knights"),
               ("dragon-rider-duo", "Dragon Rider Duo")]},
    {"slug": "space-crew", "name": "Space Crew",
     "tagline": "Three explorers and one very friendly alien.",
     "spots": [("astronaut", "Astronaut"),
               ("space-crewmate", "Space Crewmate"),
               ("blue-alien-ohana", "Blue Alien Ohana")]},
    {"slug": "witchy-night", "name": "Witchy Night",
     "tagline": "Witches, a ghost, and zero scary-movie tears.",
     "spots": [("emerald-witch", "Emerald Witch"),
               ("little-witch", "Little Witch"),
               ("good-witch-bad-witch", "Good Witch, Bad Witch"),
               ("classic-ghost", "Classic Ghost")]},
    {"slug": "safari-squad", "name": "Safari Squad",
     "tagline": "Khaki, binoculars, and one extinct party animal.",
     "spots": [("safari-zoo-crew", "Safari / Zoo Crew"),
               ("safari-photographer", "Safari Photographer"),
               ("extinct-party-animal", "Extinct Party Animal")]},
    {"slug": "breakfast-club", "name": "Breakfast Club",
     "tagline": "The tastiest group costume on the block.",
     "spots": [("cereal-crew", "Cereal Crew"),
               ("breakfast-buffet", "Breakfast Buffet"),
               ("bacon-eggs", "Bacon & Eggs")]},
    {"slug": "ocean-crew", "name": "Ocean Crew",
     "tagline": "Mermaids and one little shark.",
     "spots": [("mermaid-crew", "Mermaid Crew"),
               ("little-shark", "Little Shark")]},
    {"slug": "royal-court", "name": "Royal Court",
     "tagline": "Crowns for everyone, pins for no one.",
     "spots": [("prince-princess", "Prince & Princess"),
               ("fairy-tale-princesses", "Fairy Tale Princesses"),
               ("tooth-fairy", "Tooth and Tooth Fairy")]},
    {"slug": "monster-mash", "name": "Monster Mash",
     "tagline": "Classic monsters, zero nightmares.",
     "spots": [("vampire", "Classic Vampire"),
               ("pixel-ghost", "Pixel Ghost"),
               ("ghost-hunters", "Ghost Hunters"),
               ("spider", "Eight-Legged Spider")]},
]

for t in THEMES:
    dash_check(t["name"]); dash_check(t["tagline"])
    for slug, title in t["spots"]:
        dash_check(title)
        assert re.fullmatch(r"[a-z0-9-]+", slug), "bad slug %r" % slug

# Verify every spot slug is a real bank idea (the honesty gate: the invite
# links to /c/<slug> guides, so each slug must exist).
with open(os.path.join(BASE, "mcp-server", "bank.json")) as f:
    bank = json.load(f)
bank_ids = {i["id"] for i in bank["ideas"]}
assert len(bank["ideas"]) == 138
for t in THEMES:
    for slug, title in t["spots"]:
        assert slug in bank_ids, "spot slug not in bank: %r" % slug

THEME_CARDS = []
THEMES_JS = []
for t in THEMES:
    tslug = t["slug"]
    THEME_CARDS.append(
        '<button type="button" class="themecard" data-theme="%s">'
        '<span class="themename">%s</span>'
        '<span class="themetag">%s</span></button>'
        % (esc(tslug), esc(t["name"]), esc(t["tagline"])))
    spots_js = ",".join(
        '{"slug":%s,"title":%s}' % (json.dumps(slug), json.dumps(title))
        for slug, title in t["spots"])
    THEMES_JS.append('"%s":{"name":%s,"tagline":%s,"spots":[%s]}' % (
        tslug, json.dumps(t["name"]), json.dumps(t["tagline"]), spots_js))

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Halloween Party Invite - Pick My Costume</title>
<meta name="description" content="Make one invite link for your Halloween party. Pick a theme, share the link, every guest gets a 2-minute costume quiz. Free.">
<link rel="canonical" href="https://pickmycostume.com/party">
<meta property="og:type" content="website">
<meta property="og:url" content="https://pickmycostume.com/party">
<meta property="og:title" content="Halloween Party Invite - Pick My Costume">
<meta property="og:description" content="One link invites the whole party. Pick a costume theme, share it, and every guest gets a costume idea in 2 minutes.">
<meta property="og:image" content="https://pickmycostume.com/images/og/emoji-crew.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Halloween Party Invite - Pick My Costume">
<meta name="twitter:description" content="One link invites the whole party, costume theme included.">
<meta name="twitter:image" content="https://pickmycostume.com/images/og/emoji-crew.jpg">
<script>
/* PostHog: anonymous usage stats only. No answers or names are sent. Session replay is off. */
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
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;margin:0;padding:0 16px 64px;background:#fff8f0;color:#2b2118}
.wrap{max-width:640px;margin:0 auto}
h1{font-size:26px;margin:28px 0 6px}
.sub{color:#6b5b4c;margin:0 0 20px;font-size:15px}
.card{border:2px solid #ead9c2;border-radius:14px;padding:16px;margin:0 0 16px;background:#fff}
.card h2{font-size:18px;margin:0 0 10px}
label.fl{display:block;font-size:13px;font-weight:600;color:#6b5b4c;margin:10px 0 4px}
input.txt{width:100%;box-sizing:border-box;padding:10px 12px;font-size:16px;border:2px solid #ead9c2;border-radius:10px;background:#fff;color:#2b2118}
input.txt:focus{border-color:#e07830;outline:none}
.themegrid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.themecard{border:2px solid #ead9c2;border-radius:14px;padding:14px;background:#fff;cursor:pointer;text-align:left;font:inherit;color:inherit}
.themecard.sel{border-color:#e07830;background:#fff4e8}
.themename{font-weight:700;font-size:16px;display:block}
.themetag{font-size:13px;color:#6b5b4c;display:block;margin-top:4px}
.btnrow{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.btn{display:inline-block;padding:10px 14px;border-radius:10px;font-size:14px;font-weight:600;text-decoration:none;border:2px solid #e07830;color:#e07830;background:#fff;cursor:pointer;min-height:44px;box-sizing:border-box}
.btn.primary{background:#e07830;color:#fff;border-color:#e07830}
.invitecard{border:3px solid #e07830;border-radius:18px;padding:24px 20px;background:#fff;text-align:center;margin:28px 0 16px}
.invitecard .kicker{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#e07830;font-weight:700}
.invitecard h1{margin:10px 0 6px}
.inametitle{font-size:26px;font-weight:700;margin:10px 0 6px}
.invitecard .when{font-size:16px;color:#6b5b4c;margin:0 0 4px}
.invitecard .theme{font-size:18px;font-weight:700;margin:14px 0 4px}
.invitecard .themetagline{font-size:14px;color:#6b5b4c;margin:0 0 14px}
.costumerow{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin:0 0 6px}
.costumechip{font-size:13px;background:#fff8f0;border:1px solid #ead9c2;border-radius:999px;padding:6px 12px;color:#6b5b4c;text-decoration:none;min-height:44px;box-sizing:border-box;display:inline-flex;align-items:center}
.costumechip:hover{border-color:#e07830;color:#e07830}
.sharebox{border:2px dashed #e07830;border-radius:14px;padding:16px;margin:24px 0;background:#fff}
.sharebox h2{font-size:18px;margin:0 0 6px}
.sharebox p{font-size:14px;color:#6b5b4c;margin:0 0 12px}
.note{font-size:12px;color:#a08a70;margin:16px 0}
.linkout{font-size:14px;color:#6b5b4c;margin:18px 0}
.linkout a{color:#e07830}
.hidden{display:none!important}
</style>
</head>
<body>
<div class="wrap">

<div id="maker">
<h1>Invite the whole party with one link</h1>
<p class="sub">Pick a costume theme, add the date, and text one link to the work or friend group chat. Every guest lands on a party page with a 2-minute costume quiz. Free, no signup, no ads.</p>
<p id="badlink" class="hidden" style="background:#fff4e8;border:2px solid #e07830;border-radius:10px;padding:10px 12px;font-size:14px">That invite link didn't work. Ask the host to resend it, or make your own below.</p>
<div class="card">
<h2>1. Name it and date it</h2>
<label class="fl" for="pname">Party name</label>
<input class="txt" id="pname" maxlength="60" placeholder="Acme Corp Halloween Bash">
<label class="fl" for="pdate">Date</label>
<input class="txt" id="pdate" maxlength="40" placeholder="Fri Oct 30, 7pm">
</div>
<div class="card">
<h2>2. Pick a costume theme</h2>
<p class="sub">A theme makes the group photo. Guests can still take the quiz for their own idea.</p>
<div class="themegrid" id="themegrid">
__THEME_CARDS__
</div>
</div>
<div class="card">
<h2>3. Send the invite</h2>
<div class="btnrow">
<button class="btn primary" id="mkbtn">Make the invite link</button>
</div>
<div id="makeresult" class="hidden">
<label class="fl" for="inviteurl">Your invite link</label>
<input class="txt" id="inviteurl" readonly>
<div class="btnrow">
<button class="btn" id="copyinvite">Copy invite link</button>
<button class="btn" id="smsinvite">Text it to the team</button>
<button class="btn" id="slackinvite">Copy Slack announcement</button>
</div>
</div>
</div>
<p class="note">The link carries only the party name, date, and theme you type. Nothing is stored anywhere; RSVPs live in your group chat, not here.</p>
</div>

<div id="invite" class="hidden">
<div class="invitecard">
<div class="kicker">You are invited</div>
<div id="iname" class="inametitle"></div>
<p class="when" id="idate"></p>
<p class="theme" id="itheme"></p>
<p class="themetagline" id="ithemetag"></p>
<div class="costumerow" id="iexamples"></div>
<div class="btnrow" style="justify-content:center">
<a class="btn primary" id="quizcta" href="#">Find my costume (2 min)</a>
</div>
<p class="linkout">Running the office contest too? <a href="/office-contest-kit">Grab the contest kit</a> for ballots and winners.</p>
</div>
<div class="sharebox">
<h2>Forward this invite</h2>
<p>Know someone else coming? Pass it on. Every forward is a new guest with a costume plan.</p>
<div class="btnrow">
<button class="btn primary" id="fsms">Text this invite</button>
<button class="btn" id="fcopy">Copy invite link</button>
</div>
<p class="linkout" style="margin-top:14px">Hosting your own party? <a href="/party">Make your own invite link</a>.</p>
</div>
<p class="note">RSVPs live in your group chat or email, not here. This page just makes the invite pretty and hands everyone a costume quiz.</p>
</div>

</div>
<script>
/* Pure functions below are unit-tested by hour-session/verify-party.cjs.
   init() is the only DOM-touching entry point. */
var PARTY_THEMES = {__THEMES__};
var SITE = "https://pickmycostume.com";
var ORIGIN = "partyinvite";

function track(name, props){
  props = props || {};
  try {
    if (_isQA) props.internal = true;
  } catch(e){}
  try {
    if (window.posthog && posthog.capture) posthog.capture(name, props);
  } catch(e){}
}

function escHtml(s){
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function isValidTheme(t){ return !!(t && PARTY_THEMES[t]); }

function parsePartyParams(qs){
  var m = /[?&]t=([a-z0-9-]+)/.exec(qs || "");
  var t = m ? m[1] : "";
  if (!isValidTheme(t)) return { theme: "" };
  var dm = /[?&]d=([^&]*)/.exec(qs || "");
  var nm = /[?&]n=([^&]*)/.exec(qs || "");
  var d = "", n = "";
  try { d = dm ? decodeURIComponent(dm[1].replace(/\\+/g, " ")) : ""; } catch(e){}
  try { n = nm ? decodeURIComponent(nm[1].replace(/\\+/g, " ")) : ""; } catch(e){}
  return { theme: t, date: d.slice(0, 40), name: n.slice(0, 60) };
}

function inviteUrl(theme, date, name){
  return SITE + "/party?t=" + encodeURIComponent(theme)
    + "&d=" + encodeURIComponent(date || "")
    + "&n=" + encodeURIComponent(name || "");
}

function quizCtaUrl(theme){
  /* o=invite, deliberately NOT o=partyinvite: index.html's origin regex
     /[?&]o=(card|...|party|...)/ has no terminator, so "partyinvite"
     prefix-matches the flag-OFF party-link experiment's o=party arm and
     would set VIA_SHARE_ORIGIN="party" (same prefix-collision class as the
     D1 generic_quick fix). "invite" matches no arm in either direction.
     2026-09-27 attribution audit: &src=share-partyinvite added so the
     quiz leg attributes (landing_src); the deliberate ?o=invite is untouched. */
  return SITE + "/?o=invite" + (theme ? "&t=" + encodeURIComponent(theme) : "") + "&src=share-partyinvite";
}

function inviteText(theme, date, name){
  var th = PARTY_THEMES[theme];
  var head = "You are invited: " + (name || "Halloween party")
    + (date ? ", " + date : "") + ".";
  return head + " Costume theme: " + th.name + " (" + th.tagline + ")"
    + " Find your costume in 2 minutes: " + inviteUrl(theme, date, name);
}

function slackText(theme, date, name){
  var th = PARTY_THEMES[theme];
  return "Halloween party: " + (name || "Halloween party")
    + (date ? " on " + date : "") + ". Costume theme: " + th.name
    + " (" + th.tagline + "). Get your costume idea in 2 minutes: "
    + inviteUrl(theme, date, name) + " RSVP in this thread.";
}

function smsUrl(theme, date, name){
  return "sms:?&body=" + encodeURIComponent(inviteText(theme, date, name));
}

function copyText(txt, done){
  /* Share is measured as intent (same as the sms path, which tracks before
     navigating): the prompt fallback must also report, or share counts
     silently drop on browsers where the clipboard write fails. */
  if (navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(txt).then(done, function(){ prompt("Copy this:", txt); done(); });
  } else { prompt("Copy this:", txt); done(); }
}

/* ---------- views ---------- */
var makerState = { theme: "" };

function renderMaker(){
  document.getElementById("maker").classList.remove("hidden");
  document.getElementById("invite").classList.add("hidden");
  document.querySelectorAll(".themecard").forEach(function(c){
    c.addEventListener("click", function(){
      document.querySelectorAll(".themecard").forEach(function(x){ x.classList.remove("sel"); });
      c.classList.add("sel");
      makerState.theme = c.getAttribute("data-theme");
    });
  });
  document.getElementById("mkbtn").addEventListener("click", function(){
    if (!makerState.theme){ alert("Pick a costume theme first."); return; }
    var name = document.getElementById("pname").value.trim().slice(0, 60);
    var date = document.getElementById("pdate").value.trim().slice(0, 40);
    var url = inviteUrl(makerState.theme, date, name);
    document.getElementById("inviteurl").value = url;
    document.getElementById("makeresult").classList.remove("hidden");
    track("partyinvite_created", {theme: makerState.theme});
  });
  document.getElementById("copyinvite").addEventListener("click", function(){
    var url = document.getElementById("inviteurl").value;
    copyText(url, function(){ track("partyinvite_shared", {channel: "copy", role: "host"}); });
  });
  document.getElementById("smsinvite").addEventListener("click", function(){
    track("partyinvite_shared", {channel: "sms", role: "host"});
    location.href = smsUrl(makerState.theme,
      document.getElementById("pdate").value.trim().slice(0, 40),
      document.getElementById("pname").value.trim().slice(0, 60));
  });
  document.getElementById("slackinvite").addEventListener("click", function(){
    var txt = slackText(makerState.theme,
      document.getElementById("pdate").value.trim().slice(0, 40),
      document.getElementById("pname").value.trim().slice(0, 60));
    copyText(txt, function(){ track("partyinvite_shared", {channel: "slack", role: "host"}); });
  });
}

function renderInvite(p){
  var th = PARTY_THEMES[p.theme];
  document.getElementById("maker").classList.add("hidden");
  document.getElementById("invite").classList.remove("hidden");
  document.getElementById("iname").textContent = p.name || "Halloween party";
  document.getElementById("idate").textContent = p.date || "Date to be announced";
  document.getElementById("itheme").textContent = "Costume theme: " + th.name;
  document.getElementById("ithemetag").textContent = th.tagline;
  document.title = (p.name || "Halloween party") + " - Pick My Costume";
  var ex = th.spots.slice(0, 3).map(function(s){
    return '<a class="costumechip" data-slug="' + escHtml(s.slug) + '" href="/c/' + escHtml(s.slug) + '?src=share-' + ORIGIN + '-' + escHtml(p.theme) + '">' + escHtml(s.title) + "</a>";
  }).join("");
  document.getElementById("iexamples").innerHTML = ex;
  Array.prototype.forEach.call(document.getElementById("iexamples").querySelectorAll(".costumechip"), function(a){
    a.addEventListener("click", function(){ track("partyinvite_costume_clicked", {theme: p.theme, slug: a.getAttribute("data-slug")}); });
  });
  var q = document.getElementById("quizcta");
  q.href = quizCtaUrl(p.theme);
  q.addEventListener("click", function(){ track("partyinvite_quiz_clicked", {theme: p.theme}); });
  track("partyinvite_opened", {theme: p.theme});
  var url = inviteUrl(p.theme, p.date, p.name);
  document.getElementById("fcopy").addEventListener("click", function(){
    copyText(url, function(){ track("partyinvite_shared", {channel: "copy", role: "guest", theme: p.theme}); });
  });
  document.getElementById("fsms").addEventListener("click", function(){
    track("partyinvite_shared", {channel: "sms", role: "guest", theme: p.theme});
    location.href = smsUrl(p.theme, p.date, p.name);
  });
}

function init(){
  var qs = "";
  try { qs = location.search || ""; } catch(e){}
  var p = parsePartyParams(qs);
  if (p.theme){
    /* Privacy (site convention: index.html strips ?first= / ?nm= the same
       way): the party name can hold personal names and the date field is
       free text. Both are already parsed into memory above, so drop n= and
       d= from the address bar before the PostHog pageview fires -- the
       pageview URL then carries only the theme token. probe=/sim=/internal=
       are preserved so the QA exclusion keeps working. */
    try {
      var tail = "";
      var pm = /[?&]((?:probe|sim)=[^&]*)/.exec(qs);
      if (pm) tail += "&" + pm[1];
      if (/[?&]internal=1(?:&|$)/.test(qs)) tail += "&internal=1";
      if (window.history && history.replaceState)
        history.replaceState(null, "", location.pathname + "?t=" + encodeURIComponent(p.theme) + tail);
    } catch(e){}
    renderInvite(p);
  } else {
    /* Recipient-side red-team 2026-09-27: a guest arriving on a broken or
       mistyped invite link landed on the maker with no explanation. If a t=
       token was present but is not a known theme, say so. */
    try {
      var tm = /[?&]t=([^&]*)/.exec(qs || "");
      if (tm && !isValidTheme(tm[1] || ""))
        document.getElementById("badlink").classList.remove("hidden");
    } catch(e){}
    renderMaker();
  }
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
</script>
</body>
</html>
"""

page = (PAGE
        .replace("__THEME_CARDS__", "\n".join(THEME_CARDS))
        .replace("__THEMES__", ",".join(THEMES_JS)))
dash_check(page)
out = os.path.join(BASE, "party.html")
with open(out, "w") as f:
    f.write(page)
print("wrote", out, len(page), "bytes")

# ---------- functions/party.js emission (2026-09-27 consolidation) ----------
# PARTY_OG used to be a third hand-maintained copy of the theme list. It is
# emitted here from THEMES, so a theme edit regenerates party.html AND
# functions/party.js from the single source. Representative og image per
# theme = its first costume spot (the hand-written table's convention).
OG_ROWS = []
for t in THEMES:
    img_slug = t["spots"][0][0]
    img_path = os.path.join(BASE, "images", "og", img_slug + ".jpg")
    assert os.path.exists(img_path), \
        "missing og image for party theme %r: %s" % (t["slug"], img_path)
    OG_ROWS.append((t["slug"], t["name"], t["tagline"], img_slug))

def _colwidth(items):
    return max(len(x) for x in items) + 1

_kw = _colwidth('  "%s":' % s for s, _, _, _ in OG_ROWS)
_nw = _colwidth('"name": "%s",' % n for _, n, _, _ in OG_ROWS)
_tw = _colwidth('"tagline": "%s",' % g for _, _, g, _ in OG_ROWS)
_og_lines = []
for _i, (_s, _n, _g, _img) in enumerate(OG_ROWS):
    _og_lines.append(
        ('  "%s":' % _s).ljust(_kw) + '{ ' +
        ('"name": "%s",' % _n).ljust(_nw) +
        ('"tagline": "%s",' % _g).ljust(_tw) +
        '"img": "%s" %s' % (_img, "}," if _i < len(OG_ROWS) - 1 else "}"))
OG_TABLE = "\n".join(_og_lines)

# Raw string: the JS contains \u00b7, which must reach the file literally.
FN_PARTY = r"""// Per-party og injection for /party invite links.
// Regenerate with: python3 hour-session/build_party.py (emits this file
// from THEMES -- do not hand-edit the table).
//
// party.html is a static file, so every forwarded invite unfurls in chat apps
// with the same generic preview ("Halloween Party Invite - Pick My Costume" /
// emoji-crew image) no matter the party. Per-party og:title/og:description/
// og:image are injected here, server-side, on the fetch path: when the
// request carries a valid theme token ?t=<theme>, the static HTML's
// og/twitter meta values are replaced with per-party ones before serving.
// No token (or an invalid one): the static asset is served untouched,
// byte-identical.
//
// Mirrors the /c/[slug].js pattern: token -> embedded data table -> esc() ->
// og meta values -> Response. The difference is injection into the existing
// static HTML (string replace of the meta tags, matched by tag identity so a
// party.html copy change degrades to the generic preview, never to broken
// HTML) instead of building the page from scratch.
//
// Privacy: the party name/date live in the share URL itself (that is the
// invite mechanism), so reflecting them in the preview adds no new channel.
// og:url stays the canonical /party (no query, no PII): messengers cache the
// preview against the fetched URL, so per-party unfurls still work. Only
// t/n/d are ever read; every other query param is ignored. Host-typed
// name/date are esc()d for the meta content-attribute context and truncated
// to party.html's own caps (60/40).
//
// PARTY_OG is emitted by hour-session/build_party.py from THEMES (single
// source of truth): name + tagline per theme; img is the theme's first
// costume spot as images/og/<slug>.jpg (existence asserted at generation
// time). A theme this table does not know falls through to the generic
// asset.

// (table emitted by build_party.py from THEMES -- see header)
var PARTY_OG = {
__PARTY_OG_TABLE__
};

// Fallback image: the same generic og:image party.html ships with.
var DEFAULT_OG_IMAGE = "https://pickmycostume.com/images/og/emoji-crew.jpg";

// Same esc() as /c/[slug].js: these values land inside meta content="".
function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
                  .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// Replace the value of one meta tag, matched by tag identity (property/name
// + content attribute). If party.html's copy changes, the match still holds;
// if the tag ever disappears, this is a silent no-op (generic stays).
function setMeta(html, attr, value) {
  var re = new RegExp("<meta " + attr + ' content="[^"]*">');
  return html.replace(re, "<meta " + attr + ' content="' + value + '">');
}

export async function onRequest(context) {
  var url;
  try {
    url = new URL(context.request.url);
  } catch (e) {
    return context.env.ASSETS.fetch(context.request);
  }

  var t = url.searchParams.get("t") || "";
  var th = (/^[a-z0-9-]+$/.test(t) && PARTY_OG[t]) ? PARTY_OG[t] : null;
  if (!th || context.request.method !== "GET") {
    // No (or invalid) theme token, or a non-GET fetch: serve the static
    // asset exactly as-is. Crawlers unfurl with GET, so this path is the
    // only one that ever needs injection.
    return context.env.ASSETS.fetch(context.request);
  }

  var resp = await context.env.ASSETS.fetch(context.request);
  var ctype = resp.headers.get("Content-Type") || "";
  if (!resp.ok || ctype.indexOf("text/html") === -1) return resp;
  var html = await resp.text();
  if (!html) return resp;

  // Host-typed fields, same caps as party.html's own parser (60/40).
  var name = (url.searchParams.get("n") || "").slice(0, 60);
  var date = (url.searchParams.get("d") || "").slice(0, 40);

  var who = name ? name : "Halloween party";
  var title = esc(who + " \u00b7 " + th.name);
  var desc = esc((date ? date + ". " : "") + th.tagline +
                 " Find your costume in 2 minutes.");
  var img = th.img
    ? "https://pickmycostume.com/images/og/" + th.img + ".jpg"
    : DEFAULT_OG_IMAGE;

  html = setMeta(html, 'property="og:title"', title);
  html = setMeta(html, 'name="twitter:title"', title);
  html = setMeta(html, 'property="og:description"', desc);
  html = setMeta(html, 'name="twitter:description"', desc);
  html = setMeta(html, 'property="og:image"', img);
  html = setMeta(html, 'name="twitter:image"', img);
  // og:url intentionally untouched: canonical /party, no query, no PII.

  return new Response(html, {
    headers: {
      "Content-Type": "text/html;charset=utf-8",
      "Cache-Control": "public, max-age=3600"
    }
  });
}
"""

fn_party = FN_PARTY.replace("__PARTY_OG_TABLE__", OG_TABLE)
fn_out = os.path.join(BASE, "functions", "party.js")
with open(fn_out, "w") as f:
    f.write(fn_party)
print("wrote", fn_out, len(fn_party), "bytes")
