#!/usr/bin/env python3
"""Build babysitter.html - "The Babysitter's Halloween" (code only, NO deploy).

A forwardable page a parent sends to their teen babysitter (or the sitter's
parents): pick one kid-safe costume from a filtered slice of the idea
bank, then share one link. The sitter opens the link and sees their pick with
a build-guide link; quiz CTAs carry ?src=share-babysitter attribution.

Kid-safe filter (the honest contract, fails loudly on drift):
  - audience includes "kid"
  - instructions effort == "Easy"
  - instructions time parses to <= 45 minutes
  - bank tags.scary < 2  (not mildly-or-more spooky; a teen wears this in
    front of toddlers, so scary >= 2 is out)
  - bank holds >= 100 ideas (derived count, never hard-coded), unique ids,
    idea/instruction slug sets equal, instructions present for every pick

Honesty contract (fails loudly):
  - titles, blurbs, effort are bank-verbatim; nothing invented. Displayed
    time is the bank time with any "+ ... drying" suffix stripped
    (display_time(); Billy's Oct 1 hands-on-only rule). The bank's removed
    cost field is never emitted.
  - no em/en dashes in any user-facing string (Billy's standing rule)
  - no </script inside the data payload
  - PostHog events use the standing probe/sim/internal exclusion
  - every tap target (button, search input, idea chip, quiz CTA) is 44px+
  - the generator writes ONLY ../babysitter.html: no inbound links, no
    sitemap edit, no other file touched. Deploy-time wiring (sitemap entry,
    IndexNow, inbound link placement) is documented for the main agent's
    batch in hour-session/new-ideas-2026-09-27-eve.md.

Usage: python3 build_babysitter.py   (writes ../babysitter.html)
Deterministic: re-running produces byte-identical output.
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BANK = os.path.join(ROOT, "mcp-server", "bank.json")
OUT = os.path.join(ROOT, "babysitter.html")
FUZZY = os.path.join(HERE, "fuzzy_typeahead.js")

PH_KEY = "phc_t9dkHXAZR5VEjPFm3K5JDzGKFsNNxKcwSxxcEBEeLbS7"
SRC_KEY = "share-babysitter"
SITE = "https://pickmycostume.com"
DASH_RE = re.compile(r"[\u2013\u2014]")

EVENTS = {
    "babysitter_view",
    "babysitter_pick_set",
    "babysitter_link_copied",
    "babysitter_share_opened",
    "babysitter_recipient_view",
    "babysitter_quiz_clicked",
}


def fail(msg):
    print("FAIL: " + msg, file=sys.stderr)
    sys.exit(1)


def display_time(t):
    # Displayed times are hands-on only: strip any "+ ... drying" suffix
    # (proven pattern from gen_costumes_hub.py / build_aisle_dupes.py).
    return re.sub(r"\s*\+.*drying\s*$", "", str(t))


def minutes(time_str):
    m = re.search(r"(\d+)\s*min", str(time_str))
    if m:
        return int(m.group(1))
    h = re.search(r"(\d+)\s*(?:hr|hour)", str(time_str))
    if h:
        return int(h.group(1)) * 60
    return None


def load_bank():
    with open(BANK, encoding="utf-8") as f:
        bank = json.load(f)
    ideas = bank["ideas"]
    ins = bank["instructions"]
    # Bank size is derived, never hard-coded: the == 138 asserts froze this
    # page when the bank grew to 169 on Oct 3. Non-vacuous floor + slug-set
    # equality, following the repaired build_aisle_dupes.py pattern.
    if len(ideas) < 100:
        fail("bank yielded only %d ideas" % len(ideas))
    ids = [e["id"] for e in ideas]
    if len(set(ids)) != len(ids):
        fail("duplicate idea ids")
    if set(ins) != set(ids):
        fail("bank idea/instruction slug sets differ")
    return ideas, ins


def kid_safe(idea, ins):
    i = ins.get(idea["id"])
    if not i:
        return False
    if "kid" not in set(idea.get("audience", [])):
        return False
    if i.get("effort") != "Easy":
        return False
    mins = minutes(i.get("time", ""))
    if mins is None or mins > 45:
        return False
    if (idea.get("tags") or {}).get("scary", 0) >= 2:
        return False
    return True


def build_data(ideas, ins):
    picks = [e for e in ideas if kid_safe(e, ins)]
    if not picks:
        fail("kid-safe filter selected nothing; check bank shape")
    data = []
    for e in picks:
        i = ins[e["id"]]
        data.append({
            "id": e["id"],
            "title": e["title"],
            "blurb": e.get("blurb", ""),
            "time": display_time(i.get("time", "")),
            "effort": i.get("effort", ""),
        })
    data.sort(key=lambda d: d["title"])
    for d in data:
        if "drying" in d["time"]:
            fail("drying leaked into displayed time for " + d["id"])
    return data


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Babysitter's Halloween | Pick My Costume</title>
<meta name="description" content="Your sitter needs a costume too. Pick one kid-safe, comfy, easy Halloween costume and send her the link: build guide included.">
<meta name="robots" content="noindex">
<link rel="canonical" href="https://pickmycostume.com/babysitter">
<meta property="og:title" content="The Babysitter's Halloween">
<meta property="og:description" content="Pick your sitter a Halloween costume: kid-safe, comfy, easy to make. One link, build guide included.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://pickmycostume.com/babysitter">
<script>
/* PostHog: anonymous usage stats only. No names are sent. Session replay is off. */
(function(){
  var s = document.createElement("script");
  s.async = true;
  s.src = "https://us.i.posthog.com/static/array.js";
  s.onload = function(){
    try {
      if (window.posthog && posthog.init) {
        posthog.init("__PH_KEY__", {
          api_host: "https://us.i.posthog.com",
          autocapture: false,
          capture_pageview: true,
          disable_session_recording: true
        });
      }
    } catch(e){}
  };
  document.head.appendChild(s);
})();
/* Standing QA exclusion: ?probe=, ?sim=, ?internal=1 tag the event internal. */
function ph(name,props){props=props||{};try{var q=location.search;if(/[?&](probe|sim)=/.test(q)||/[?&]internal=1/.test(q))props.internal=true;if(window.posthog&&window.posthog.capture){window.posthog.capture(name,props);}}catch(e){}}
</script>
<script>
__FUZZY__
</script>
<style>
:root{--ink:#23201a;--mut:#6b655a;--line:#e5ddcf;--card:#fffdf8;--acc:#c2410c;--sel:#fff3e4}
*{box-sizing:border-box}
body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink);background:#faf6ee;margin:0;padding:0 16px 80px}
.wrap{max-width:640px;margin:0 auto}
h1{font-size:30px;margin:28px 0 6px}
.sub{color:var(--mut);font-size:16px;margin:0 0 20px}
.step{font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--acc);margin:26px 0 8px}
.card{background:var(--card);border:2px solid var(--line);border-radius:14px;padding:14px;margin:10px 0}
.card h3{margin:0 0 4px;font-size:18px}
.card p{margin:4px 0;color:var(--mut);font-size:14px}
.card .triple{font-size:14px;color:var(--ink);font-weight:600}
.card .why{font-size:13px;color:var(--acc);font-weight:600}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
button,input[type=search],.chip,.quizcta{min-height:44px}
button{padding:10px 18px;font-size:16px;border-radius:10px;border:2px solid var(--acc);background:var(--acc);color:#fff;font-weight:700;cursor:pointer;font-family:inherit}
button.ghost{background:#fff;color:var(--acc)}
input[type=search]{padding:8px 12px;font-size:16px;border:2px solid var(--line);border-radius:10px;flex:1;min-width:140px;font-family:inherit;width:100%}
.chip{border:2px solid var(--line);background:#fff;border-radius:999px;padding:10px 16px;font-size:15px;cursor:pointer;font-family:inherit;line-height:1.3}
.chip.on{border-color:var(--acc);background:var(--sel);font-weight:700}
.banner{background:var(--sel);border:2px solid var(--acc);border-radius:14px;padding:14px;margin:18px 0}
.banner p{margin:6px 0}
.sharebox textarea{width:100%;min-height:120px;font-size:15px;padding:10px;border:2px solid var(--line);border-radius:10px;font-family:inherit}
.note{font-size:13px;color:var(--mut)}
a{color:var(--acc)}
.quizcta{display:flex;align-items:center;justify-content:center;text-align:center;margin:22px 0;padding:14px;border-radius:12px;background:var(--acc);color:#fff;font-weight:700;text-decoration:none;font-size:17px}
.hits ul{list-style:none;margin:6px 0 0;padding:0;border:2px solid var(--line);border-radius:10px;max-height:240px;overflow:auto;background:#fff}
.hits li{padding:10px 12px;font-size:16px;cursor:pointer;border-bottom:1px solid var(--line);min-height:44px;display:flex;align-items:center}
.hits li:last-child{border-bottom:0}
.hits li:hover,.hits li:focus{background:#faf6ec;outline:none}
details.browse{margin-top:10px}
details.browse summary{cursor:pointer;font-weight:700;color:var(--acc);min-height:44px;display:flex;align-items:center;font-size:16px}
.pickgrid{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.fineprint{font-size:12px;color:var(--mut);margin-top:14px}
footer{margin-top:40px;font-size:13px;color:#777;}</style>
</head>
<body>
<div class="wrap">

<div id="builder">
<h1>The Babysitter's Halloween</h1>
<p class="sub">Your sitter needs a costume too. Pick one that is comfy, easy to make, and kid-safe, then send her the link. Every pick below is a quick build, and each guide shows the full time.</p>

<p class="step">1. Pick her costume</p>
<div class="card">
<input id="q" type="search" placeholder="Start typing a costume" autocomplete="off" aria-label="Search kid-safe costumes">
<div class="hits"><ul id="hits" style="display:none"></ul></div>
<details class="browse">
<summary id="browsesum">Browse all __COUNT__ kid-safe picks</summary>
<div class="pickgrid" id="pickgrid"></div>
</details>
</div>

<div id="pickcard" hidden>
<p class="step">2. Her costume</p>
<div class="card">
<p class="why" id="pickwhy"></p>
<h3 id="picktitle"></h3>
<p id="pickblurb"></p>
<p class="triple" id="picktriple"></p>
<p><a id="pickguide" href="#">Step by step build guide</a></p>
</div>

<p class="step">3. Send her the link</p>
<div class="card sharebox">
<textarea id="sharetext" readonly aria-label="Share text for the sitter"></textarea>
<div class="row" style="margin-top:10px">
<button id="sharebtn">Share</button>
<button class="ghost" id="copybtn">Copy text</button>
</div>
<p class="note">One link per sitter. She sees her costume and the build guide. Nothing to sign up for.</p>
</div>
</div>

<a class="quizcta" id="builderquiz" href="__QUIZURL__">Not the one? Take the 2-minute quiz</a>
<p class="fineprint">Costumes and times come from our own __BANKCOUNT__-idea bank. Nothing is invented.</p>
</div>

<div id="recipient" hidden>
<div class="banner">
<h1 style="margin-top:0">Your Halloween pick</h1>
<p>A family you babysit for picked this for you: comfy, easy to make, and done in 45 minutes or less.</p>
</div>
<div class="card">
<p class="why">Your costume</p>
<h3 id="rtitle"></h3>
<p id="rblurb"></p>
<p class="triple" id="rtriple"></p>
<p><a id="rguide" href="#">Step by step build guide</a></p>
</div>
<a class="quizcta" id="recipquiz" href="__QUIZURL__">Want your own pick? Take the 2-minute quiz</a>
<p class="fineprint">Costumes and times come from our own __BANKCOUNT__-idea bank. Nothing is invented.</p>
</div>

</div>
<script>
var IDEAS=__IDEAS__;
var IDEA_BY_ID={};IDEAS.forEach(function(e){IDEA_BY_ID[e.id]=e;});
var _tapGuards={};
function tapGuard(key,ms){var n=Date.now();if(n-(_tapGuards[key]||0)<ms)return false;_tapGuards[key]=n;return true;}
function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function params(){return new URLSearchParams(window.location.search);}
function guideUrl(id){return "__SITE__/c/"+id+"?src=__SRC__";}
function sitterUrl(id){return "__SITE__/babysitter?sitter="+encodeURIComponent(id)+"&src=__SRC__";}
function triple(e){return e.time+" - "+e.effort+" to make";}
var current=null;

function renderPick(e){
  document.getElementById("pickwhy").textContent="Her costume";
  document.getElementById("picktitle").textContent=e.title;
  document.getElementById("pickblurb").textContent=e.blurb;
  document.getElementById("picktriple").textContent=triple(e);
  document.getElementById("pickguide").href=guideUrl(e.id);
  document.getElementById("pickcard").hidden=false;
  document.getElementById("sharetext").value=shareText(e);
  markOn(e.id);
  ph("babysitter_pick_set",{idea_id:e.id});
}
function markOn(id){
  var grid=document.getElementById("pickgrid");
  for(var i=0;i<grid.children.length;i++){
    grid.children[i].classList.toggle("on",grid.children[i].getAttribute("data-id")===id);
  }
}
function shareText(e){
  var t="Your Halloween pick: "+e.title+". "+e.blurb+" \\u23F1\\uFE0F Timed: about "+e.time+". ";
  t+="Full build guide: "+guideUrl(e.id)+"\\n\\n";
  t+="Pick your own with the 2-minute quiz: __QUIZURL__";
  return t;
}
function doShare(){
  if(!current||!tapGuard("babysitter-share",1000))return;
  var text=document.getElementById("sharetext").value;
  var done=function(){ph("babysitter_share_opened",{idea_id:current.id});};
  if(navigator.share){
    navigator.share({title:"The Babysitter's Halloween",text:text,url:sitterUrl(current.id)}).then(done,function(){});
  }else{
    doCopy();
  }
}
function doCopy(){
  if(!current||!tapGuard("babysitter-copy",1000))return;
  var full=sitterUrl(current.id)+"\\n\\n"+document.getElementById("sharetext").value;
  var done=function(){ph("babysitter_link_copied",{idea_id:current.id});};
  if(navigator.clipboard&&navigator.clipboard.writeText){
    navigator.clipboard.writeText(full).then(function(){done();alert("Copied. Text it to your sitter.");},function(){prompt("Copy this:",full);});
  }else{prompt("Copy this:",full);}
}
function renderRecipient(e){
  document.getElementById("builder").hidden=true;
  document.getElementById("recipient").hidden=false;
  document.getElementById("rtitle").textContent=e.title;
  document.getElementById("rblurb").textContent=e.blurb;
  document.getElementById("rtriple").textContent=triple(e);
  document.getElementById("rguide").href=guideUrl(e.id);
  ph("babysitter_recipient_view",{idea_id:e.id});
}
function quizClick(role){
  return function(){if(!tapGuard("babysitter-quiz",1000))return;ph("babysitter_quiz_clicked",{idea_id:current?current.id:"",role:role});};
}
(function init(){
  var q=document.getElementById("q"),hits=document.getElementById("hits");
  var grid=document.getElementById("pickgrid");
  IDEAS.forEach(function(e){
    var c=document.createElement("button");
    c.type="button";c.className="chip";c.textContent=e.title;
    c.setAttribute("data-id",e.id);
    c.onclick=function(){if(tapGuard("babysitter-pick",400)){current=e;renderPick(e);}};
    grid.appendChild(c);
  });
  function doSearch(){
    var res=FuzzyTypeAhead.search(q.value,IDEAS.map(function(e){return{id:e.id,title:e.title,blurb:e.blurb};}),{max:8});
    hits.innerHTML="";
    res.forEach(function(r){
      var e=IDEA_BY_ID[r.id];
      var li=document.createElement("li");li.tabIndex=0;
      li.textContent=e.title+" ("+e.time+")";
      var go=function(){if(tapGuard("babysitter-pick",400)){current=e;q.value=e.title;renderPick(e);hits.style.display="none";}};
      li.onclick=go;
      li.onkeydown=function(ev){if(ev.key==="Enter"||ev.key===" "){ev.preventDefault();go();}};
      hits.appendChild(li);
    });
    hits.style.display=res.length?"block":"none";
  }
  q.addEventListener("input",doSearch);
  document.getElementById("sharebtn").onclick=doShare;
  document.getElementById("copybtn").onclick=doCopy;
  document.getElementById("builderquiz").addEventListener("click",quizClick("builder"));
  document.getElementById("recipquiz").addEventListener("click",quizClick("recipient"));
  var p=params();
  var sid=p.get("sitter");
  if(sid&&IDEA_BY_ID[sid]){renderRecipient(IDEA_BY_ID[sid]);return;}
  var src=p.get("src")||"";
  ph("babysitter_view",{via:src?src.replace(/^share-/,""):"direct"});
})();
</script>
<footer>Built with Muse.</footer></body>
</html>
"""


def main():
    # --out PATH (slice-9 verifier sandboxing, 2026-10-22): verification
    # runs write to a scratch path instead of rewriting the real page.
    # Default is unchanged and byte-identical: the real babysitter.html.
    out = OUT
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    ideas, ins = load_bank()
    data = build_data(ideas, ins)
    print("kid-safe picks: %d" % len(data))

    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"),
                         sort_keys=True)
    if "</script" in payload.lower():
        fail("data payload contains closing script tag")

    with open(FUZZY, encoding="utf-8") as f:
        fuzzy = f.read()
    if "FuzzyTypeAhead" not in fuzzy:
        fail("fuzzy lib does not look right")

    quiz_url = "%s/?src=%s" % (SITE, SRC_KEY)
    page = TEMPLATE.replace("__PH_KEY__", PH_KEY)
    page = page.replace("__IDEAS__", payload)
    page = page.replace("__FUZZY__", fuzzy)
    page = page.replace("__QUIZURL__", quiz_url)
    page = page.replace("__SITE__", SITE)
    page = page.replace("__SRC__", SRC_KEY)
    page = page.replace("__COUNT__", str(len(data)))
    page = page.replace("__BANKCOUNT__", str(len(ideas)))

    for token in ("__PH_KEY__", "__IDEAS__", "__FUZZY__", "__QUIZURL__",
                  "__SITE__", "__SRC__", "__COUNT__", "__BANKCOUNT__"):
        if token in page:
            fail("unreplaced token " + token)

    if DASH_RE.search(page):
        fail("em/en dash leaked into page")

    # attribution sanity: every ?src= value in the page is the allowlisted key
    srcs = set(re.findall(r"[?&]src=([A-Za-z0-9-]+)", page))
    if srcs != {SRC_KEY}:
        fail("unexpected src values: %r" % sorted(srcs))
    if not re.match(r"^(?:collection|print|share)-[a-z-]+$", SRC_KEY):
        fail("SRC_KEY fails the /c/ allowlist regex")

    # event-name contract: every ph("...") call is an expected event
    found = set(re.findall(r'ph\("([a-z_]+)"', page))
    if found != EVENTS:
        fail("event mismatch: found %r expected %r" % (sorted(found),
                                                       sorted(EVENTS)))

    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print("wrote %s (%d bytes)" % (out, os.path.getsize(out)))


if __name__ == "__main__":
    main()
