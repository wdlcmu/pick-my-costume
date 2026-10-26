#!/usr/bin/env python3
"""Build receipt.html: the shareable Costume Receipt.

2026-09-27 (new-ideas stream pm4). The winner: "The Costume Receipt".

What it is: one self-contained page at repo root. Pick any costume in the
bank via type-ahead and get a receipt-style card built ONLY from the
bank's own numbers: build time and effort (verbatim), the supplies count,
a QR to the /c/ build guide (?src=share-receipt), and a share kit.
(Cost was removed from the receipt site-wide Oct 1.) The share text is a
craft flex:

  "My Halloween costume receipt: <emoji> Astronaut. <stopwatch escape> Timed: about 25 min. Easy.
   Find yours with the 2-minute quiz: <url>"

2026-10-22 reconciliation (live -> generator): the live page was
de-costed and reworded by hand ahead of this generator. Ported back
verbatim: meta description (no count, no cost), og:description
("Find yours", no cost), the sub line ending ("or find your own"),
the fineprint (no count), and the share text Timed segment (stopwatch
as a JS unicode escape in the output, never a literal emoji in this
source). No template copy now carries a count or a cost promise;
the __COUNT__ replace in main() is retained only as a guard so any
future __COUNT__ token is still derived from len(data), never
hard-coded.

Why it wins: it opens a NEW share motivation (craft pride, not
showing off and not asking for help), which the funnel data says we need:
pick_saved 118 -> share_created 45 (38%), and the family-vote share
already covers consultation while Partner Split covers assignment.
Zero new content cost (every idea already carries its time and effort),
honest by construction, and measurable day one via ?src=share-receipt plus ?s=.

Honesty contract (fails loudly):
- time / effort are the bank's, verbatim, except displayed time is
  hands-on only: display_time() strips any "+ ... drying" suffix
  (Billy's Oct 1 rule; the live page already shows stripped times)
- generator raises on bank drift: >= 100 ideas (derived count, never
  hard-coded), unique ids, idea/instruction slug sets equal, emoji for
  all, instructions + time/effort pair present for all. The bank's
  removed cost field is never required or emitted (Oct 1 cleanup; the
  live payload already carries no cost key)
- no em/en dashes in any user-facing string (Billy's standing rule)
- no </script inside data payloads
- page is noindex, not in the sitemap, no inbound links (byte-inert)

Usage: python3 build_receipt.py   (writes ../receipt.html)
       python3 build_receipt.py --out PATH   (writes to a scratch path
       instead of the real page; sandbox pattern from the
       verify-lastcall/survive + slice 3-4 fixes, 2026-10-22/23.
       Default is unchanged: the real ../receipt.html.)
Deterministic: re-running produces byte-identical output.
"""

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BANK = os.path.join(ROOT, "mcp-server", "bank.json")
OUT = os.path.join(ROOT, "receipt.html")
FUZZY = os.path.join(HERE, "fuzzy_typeahead.js")
QR_LIB = os.path.join(ROOT, "vendor", "qrcode-generator", "qrcode.js")
PH_KEY = "phc_t9dkHXAZR5VEjPFm3K5JDzGKFsNNxKcwSxxcEBEeLbS7"
DASH_RE = re.compile(r"[\u2013\u2014]")


def fail(msg):
    print("FAIL:", msg, file=sys.stderr)
    sys.exit(1)


def display_time(t):
    # Displayed times are hands-on only: strip any "+ ... drying" suffix
    # (proven pattern from gen_costumes_hub.py / build_aisle_dupes.py).
    return re.sub(r"\s*\+.*drying\s*$", "", str(t))


def load_bank():
    with open(BANK, encoding="utf-8") as f:
        bank = json.load(f)
    ideas = bank["ideas"]
    ins = bank["instructions"]
    # Bank size is derived, never hard-coded: the == 138 assert froze this
    # page when the bank grew to 169 on Oct 3. Non-vacuous floor + slug-set
    # equality, following the repaired build_aisle_dupes.py pattern.
    if len(ideas) < 100:
        fail("bank yielded only %d ideas" % len(ideas))
    ids = [e["id"] for e in ideas]
    if len(set(ids)) != len(ids):
        fail("duplicate idea ids")
    if set(ins) != set(ids):
        fail("bank idea/instruction slug sets differ")
    for e in ideas:
        i = ins.get(e["id"])
        if not i:
            fail("no instructions for " + e["id"])
        if not isinstance(e.get("title"), str) or not e["title"].strip():
            fail("missing title for " + e["id"])
        for k in ("time", "effort"):
            if not isinstance(i.get(k), str) or not i[k].strip():
                fail("missing time/effort %s for %s" % (k, e["id"]))
        if not isinstance(i.get("m"), list) or not i["m"]:
            fail("empty materials for " + e["id"])
    return ideas, ins


def load_emoji():
    out = subprocess.run(
        [sys.executable, os.path.join(HERE, "gen_idea_emoji.py")],
        capture_output=True, text=True, check=True,
    ).stdout
    return dict(re.findall(r'"([^"]+)":\s*"([^"]+)"', out))


def build_data(ideas, ins, emoji):
    data = []
    for e in ideas:
        em = emoji.get(e["id"], "")
        if not em:
            fail("missing emoji for " + e["id"])
        i = ins[e["id"]]
        data.append({
            "id": e["id"],
            "title": e["title"],
            "emoji": em,
            "time": display_time(i["time"]),
            "effort": i["effort"],
            "supplies": len(i["m"]),
        })
    return data


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Costume Receipt | Pick My Costume</title>
<meta name="description" content="Pick any Halloween costume and get a shareable receipt: how long it takes, how hard it is, straight from the build guide.">
<meta name="robots" content="noindex">
<link rel="canonical" href="https://pickmycostume.com/receipt">
<meta property="og:title" content="My Halloween Costume Receipt">
<meta property="og:description" content="How long my costume takes, how hard it is. Find yours with the 2-minute quiz.">
<meta property="og:image" content="https://pickmycostume.com/images/og/emoji-crew.jpg">
<meta property="og:type" content="website">
<script src="vendor/qrcode-generator/qrcode.js"></script>
<script>
/* PostHog: anonymous usage stats only. No answers or names are sent. Session replay is off. */
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
function ph(name,props){props=props||{};try{var q=location.search;if(/[?&](probe|sim)=/.test(q)||/[?&]internal=1/.test(q))props.internal=true;if(window.posthog&&window.posthog.capture){window.posthog.capture(name,props);}}catch(e){}}
</script>
<script>
__FUZZY__
</script>
<style>
:root{--ink:#1c1a17;--muted:#6f6a61;--paper:#fffdf8;--card:#ffffff;--line:#e9e2d6;--cta:#d9481c}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.5}
.wrap{max-width:720px;margin:0 auto;padding:20px 16px 64px}
h1{font-size:28px;margin:8px 0 4px}
.sub{color:var(--muted);margin:0 0 20px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin:0 0 16px}
#q{width:100%;font-size:16px;padding:12px 14px;border:1px solid var(--line);border-radius:10px}
.hits ul{list-style:none;margin:6px 0 0;padding:0;border:1px solid var(--line);border-radius:10px;max-height:240px;overflow:auto;background:#fff}
.hits li{padding:10px 12px;font-size:16px;cursor:pointer;border-bottom:1px solid var(--line)}
.hits li:last-child{border-bottom:0}
.hits li:hover,.hits li:focus{background:#faf6ec;outline:none}
.btn{display:inline-block;background:var(--cta);color:#fff;border:0;border-radius:999px;padding:12px 22px;font-size:16px;font-weight:600;cursor:pointer;margin:6px 8px 0 0}
.btn.ghost{background:#fff;color:var(--ink);border:1px solid var(--line)}
#receipt{display:none}
#receipt.show{display:block}
.paper{max-width:380px;margin:12px auto;background:#fff;border:1px solid var(--line);border-top:6px solid var(--ink);border-bottom:6px solid var(--ink);padding:20px 18px;font-family:"Courier New",Courier,monospace}
.rhead{text-align:center;font-weight:700;letter-spacing:1px}
.rdiv{border-top:2px dashed #bbb;margin:12px 0}
.remo{text-align:center;font-size:56px;line-height:1.1}
.rtitle{text-align:center;font-size:22px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin:4px 0}
.rrow{display:flex;align-items:baseline;gap:8px;font-size:15px;margin:7px 0}
.rrow .dots{flex:1;border-bottom:2px dotted #999;min-width:20px}
.rrow .val{font-weight:700;text-align:right}
.rpaid{text-align:center;font-weight:700}
.rqr{text-align:center}
.rqr svg{width:120px;height:120px}
.rqrcap{font-size:10px;color:var(--muted);word-break:break-all;text-align:center;margin-top:4px}
.rfoot{text-align:center;font-size:12px;color:var(--muted);margin-top:8px}
textarea#sharepreview{width:100%;min-height:110px;font-size:14px;padding:10px;border:1px solid var(--line);border-radius:10px;background:#fafafa}
.fineprint{font-size:12px;color:var(--muted);margin-top:14px}
.status{font-size:14px;color:var(--muted);margin-top:8px;min-height:20px}
footer{margin-top:40px;font-size:13px;color:#777;}</style>
</head>
<body>
<div class="wrap">
  <h1>Costume receipt</h1>
  <p class="sub">Pick a costume. Get a receipt: how long it takes, how hard it is, straight from the build guide. Share the flex, or find your own.</p>
  <div class="card">
    <input id="q" type="search" placeholder="Which costume is on your receipt? Start typing" autocomplete="off" aria-label="Search costumes">
    <div class="hits"><ul id="hits" style="display:none"></ul></div>
  </div>
  <div id="receipt">
    <div class="card">
      <div class="paper" id="paper">
        <div class="rhead">PICK MY COSTUME<br>*** COSTUME RECEIPT ***</div>
        <div class="rdiv"></div>
        <div class="remo" id="remo" aria-hidden="true"></div>
        <div class="rtitle" id="rtitle"></div>
        <div class="rdiv"></div>
        <div class="rrow"><span>BUILD TIME</span><span class="dots"></span><span class="val" id="rtime"></span></div>
        <div class="rrow"><span>DIFFICULTY</span><span class="dots"></span><span class="val" id="reffort"></span></div>
        <div class="rrow"><span>SUPPLIES</span><span class="dots"></span><span class="val" id="rsupplies"></span></div>
        <div class="rdiv"></div>
        <div class="rpaid">*** PAID IN FULL ***<br>one fun Halloween</div>
        <div class="rdiv"></div>
        <div class="rqr" id="qr"></div>
        <div class="rqrcap" id="qrurl"></div>
        <div class="rfoot">Scan for the build guide.<br>Find your own costume (2 min quiz):<br><span id="quizurl"></span></div>
      </div>
      <div style="margin-top:12px">
        <button class="btn" id="sharebtn" type="button">Share my receipt</button>
        <button class="btn ghost" id="copybtn" type="button">Copy receipt text</button>
      </div>
      <div class="status" id="status"></div>
      <div style="margin-top:12px">
        <textarea id="sharepreview" readonly aria-label="Share text preview"></textarea>
      </div>
    </div>
  </div>
  <p class="fineprint">Time and difficulty come from our own idea bank, word for word.</p>
</div>
<script>
var IDEAS=__IDEAS__;
var IDEA_BY_ID={};IDEAS.forEach(function(e){IDEA_BY_ID[e.id]=e;});
var _tapGuards={};
function tapGuard(key,ms){var n=Date.now();if(n-(_tapGuards[key]||0)<ms)return false;_tapGuards[key]=n;return true;}
var q=document.getElementById("q"),hits=document.getElementById("hits"),receipt=document.getElementById("receipt");
var current=null,shareId=null;
function guideUrl(id){return "https://pickmycostume.com/c/"+id+"?src=share-receipt";}
function newShareId(){var c="abcdefghjkmnpqrstuvwxyz23456789",s="";for(var i=0;i<8;i++)s+=c[Math.floor(Math.random()*c.length)];return s;}
function quizUrl(){return "https://pickmycostume.com/?s="+shareId+"&src=share-receipt";}
function doSearch(){
  var res=FuzzyTypeAhead.search(q.value,IDEAS.map(function(e){return{id:e.id,title:e.title};}),{max:8});
  hits.innerHTML="";
  res.forEach(function(r){
    var e=IDEA_BY_ID[r.id];
    var li=document.createElement("li");li.tabIndex=0;
    li.textContent=e.emoji+" "+e.title;
    var go=function(){if(tapGuard("receipt-pick",400))pick(e.id);};
    li.onclick=go;
    li.onkeydown=function(ev){if(ev.key==="Enter"||ev.key===" "){ev.preventDefault();go();}};
    hits.appendChild(li);
  });
  hits.style.display=res.length?"block":"none";
}
function pick(id){
  var e=IDEA_BY_ID[id];if(!e)return;current=e;shareId=newShareId();
  hits.style.display="none";q.value=e.title;
  document.getElementById("remo").textContent=e.emoji;
  document.getElementById("rtitle").textContent=e.title;
  document.getElementById("rtime").textContent=e.time;
  document.getElementById("reffort").textContent=e.effort;
  document.getElementById("rsupplies").textContent=e.supplies+(e.supplies===1?" item":" items");
  var url=guideUrl(id);
  document.getElementById("qrurl").textContent=url;
  document.getElementById("quizurl").textContent=quizUrl();
  var qrbox=document.getElementById("qr");qrbox.innerHTML="";
  try{
    if(typeof qrcode==="function"){
      var qr=qrcode(0,"M");qr.addData(url);qr.make();
      qrbox.innerHTML=qr.createSvgTag({cellSize:4,margin:0,scalable:true});
    }else{qrbox.textContent="QR unavailable";}
  }catch(err){qrbox.textContent="QR unavailable";}
  document.getElementById("sharepreview").value=shareText();
  receipt.classList.add("show");
  ph("receipt_viewed",{idea_id:e.id});
}
function shareText(){
  return "My Halloween costume receipt: "+current.emoji+" "+current.title+
    ". \\u23F1\\uFE0F Timed: about "+current.time+
    ". "+current.effort+
    ". Find yours with the 2-minute quiz: "+quizUrl();
}
function setStatus(t){document.getElementById("status").textContent=t;}
q.addEventListener("input",doSearch);
document.getElementById("sharebtn").onclick=function(){
  if(!current||!tapGuard("receipt-share",2000))return;
  var text=shareText();
  var done=function(via){
    ph("receipt_shared",{idea_id:current.id,share_id:shareId,via:via});
    setStatus(via==="native"?"Shared.":"Copied. Paste it in the group chat.");
  };
  if(navigator.share){
    try{
      navigator.share({title:"My costume receipt",text:text}).then(
        function(){done("native");},
        function(){setStatus("Share cancelled.");}
      );
    }catch(e){
      doCopy(text,function(){done("clipboard");});
    }
  }else{
    doCopy(text,function(){done("clipboard");});
  }
};
function doCopy(text,cb){
  if(navigator.clipboard&&navigator.clipboard.writeText){
    navigator.clipboard.writeText(text).then(function(){cb();},function(){fallbackCopy(text,cb);});
  }else{fallbackCopy(text,cb);}
}
function fallbackCopy(text,cb){
  var ta=document.createElement("textarea");ta.value=text;document.body.appendChild(ta);
  ta.select();try{document.execCommand("copy");}catch(e){}
  document.body.removeChild(ta);cb();
}
document.getElementById("copybtn").onclick=function(){
  if(!current||!tapGuard("receipt-copy",1000))return;
  var text=shareText();
  doCopy(text,function(){
    ph("receipt_text_copied",{idea_id:current.id,share_id:shareId,via:"clipboard"});
    setStatus("Copied. Paste it in the group chat.");
  });
};
(function(){
  var m=/[?&]pick=([^&]+)/.exec(location.search||"");
  if(!m)return;
  var id;try{id=decodeURIComponent(m[1]);}catch(e){return;}
  if(IDEA_BY_ID[id])pick(id);
})();
</script>
<footer>Built with Muse.</footer></body>
</html>
"""


def lint_template():
    if DASH_RE.search(TEMPLATE):
        m = DASH_RE.search(TEMPLATE)
        fail("em/en dash in template near: %r" % TEMPLATE[max(0, m.start()-40):m.start()+40])


def main():
    # --out PATH: write to a scratch path instead of the real page
    # (sandbox pattern, 2026-10-23). Default is unchanged: OUT.
    out = OUT
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    ideas, ins = load_bank()
    emoji = load_emoji()
    data = build_data(ideas, ins, emoji)
    for d in data:
        for k in ("title", "time", "effort"):
            if DASH_RE.search(d[k]):
                fail("em/en dash in %s %s: %r" % (d["id"], k, d[k]))
    with open(FUZZY, encoding="utf-8") as f:
        fuzzy = f.read()
    if DASH_RE.search(fuzzy):
        fail("em/en dash in fuzzy_typeahead.js")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if "</script" in payload.lower():
        fail("closing script tag in payload")
    if DASH_RE.search(payload):
        fail("em/en dash in payload")
    lint_template()
    if "__COUNT__" in payload or "__COUNT__" in fuzzy:
        fail("count placeholder collides with payload or fuzzy source")
    html = TEMPLATE.replace("__PH_KEY__", PH_KEY).replace("__FUZZY__", fuzzy).replace("__IDEAS__", payload).replace("__COUNT__", str(len(data)))
    if "__PH_KEY__" in html or "__FUZZY__" in html or "__IDEAS__" in html or "__COUNT__" in html:
        fail("unreplaced template token")
    with open(QR_LIB, encoding="utf-8") as f:
        qr = f.read()
    if "qrcode = function" not in qr or "createSvgTag" not in qr:
        fail("QR lib looks wrong")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote %s (%d bytes, %d ideas)" % (out, len(html), len(data)))


if __name__ == "__main__":
    main()
