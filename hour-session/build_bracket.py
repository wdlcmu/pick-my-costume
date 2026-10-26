#!/usr/bin/env python3
"""Build bracket.html: "Beat My Bracket", the costume showdown bracket.

2026-09-27 (new-ideas stream, report w). The winner: a March-Madness-style
bracket over the idea bank.

What it is: one self-contained page at repo root. A deterministic seeded
bracket of 16 bank costumes (default seed "2026"). The player taps winners
through Round of 16 -> Quarterfinals -> Semifinals -> Final. The champion
screen offers the /c/ build guide, a share button, and the quiz CTA.
Shared links carry ?b=<seed>&c=<champion-id>(&n=<name>); the recipient sees
"X's champion is Y. Think yours wins? Play the same bracket below" and can
fill the identical bracket (same seed => same 16, same order) and fire it
back. Every matchup card links to its /c/ build guide (?src=share-bracket).

Why it wins: the bracket is a proven group-chat viral format; 15 taps of
engagement per player; every matchup exposes two costumes with guide links;
the champion share creates the forward; the recipient gets a directed
challenge ("beat Maya's champion"); zero backend (each bracket is local,
the social game is comparing champions in the chat); measurable day one
via ?src=share-bracket, accepted by the live LANDING_SRC allowlist regex
in index.html ((?:collection|print|share)-[a-z-]+) with zero site changes.

Honesty contract (fails loudly):
- titles and emoji are the bank's, verbatim; nothing invented
- "play the same bracket" is literally true: the seed drives a
  deterministic PRNG, asserted by the harness (same seed => same 16 in
  the same order across boots; recipient banner only names a real idea)
- generator raises on bank drift: >= 100 ideas (derived count, never
  hard-coded), unique ids, emoji for all, instructions present, and the
  idea/instruction slug sets equal
- recipient name is rendered via textContent only (XSS-escaped by
  construction); bogus ?c= ids are ignored, never rendered
- no em/en dashes in any user-facing string (Billy's standing rule)
- no </script inside the data payload
- page is noindex, not in the sitemap, no inbound links (byte-inert)

2026-10-22 reconciliation (live -> generator): the live page share-id
system was ported back into this template (newShareId(), the &s= share
param, the share_created event, share_id on bracket_shared, and
via_share_id on bracket_viewed), along with the live page flattened
closing-div indentation in the champion block, so a regen no longer
loses them.

Usage: python3 build_bracket.py   (writes ../bracket.html)
Deterministic: re-running produces byte-identical output.
"""

import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BANK = os.path.join(ROOT, "mcp-server", "bank.json")
OUT = os.path.join(ROOT, "bracket.html")
PH_KEY = "phc_t9dkHXAZR5VEjPFm3K5JDzGKFsNNxKcwSxxcEBEeLbS7"
DASH_RE = re.compile(r"[\u2013\u2014]")


def fail(msg):
    print("FAIL:", msg, file=sys.stderr)
    sys.exit(1)


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
        if not ins.get(e["id"]):
            fail("no instructions for " + e["id"])
        if not isinstance(e.get("title"), str) or not e["title"].strip():
            fail("missing title for " + e["id"])
    return ideas


def load_emoji():
    out = subprocess.run(
        [sys.executable, os.path.join(HERE, "gen_idea_emoji.py")],
        capture_output=True, text=True, check=True,
    ).stdout
    return dict(re.findall(r'"([^"]+)":\s*"([^"]+)"', out))


def build_data(ideas, emoji):
    data = []
    for e in ideas:
        em = emoji.get(e["id"], "")
        if not em:
            fail("missing emoji for " + e["id"])
        data.append({"id": e["id"], "title": e["title"], "emoji": em})
    return data


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Beat My Bracket: Costume Showdown | Pick My Costume</title>
<meta name="description" content="16 costumes enter. You pick the winners. Fill the bracket, crown your champion, and challenge a friend to beat it.">
<meta name="robots" content="noindex">
<link rel="canonical" href="https://pickmycostume.com/bracket">
<meta property="og:title" content="Beat My Bracket: Costume Showdown">
<meta property="og:description" content="I crowned my costume champion. Think yours wins? Play the same bracket.">
<meta property="og:image" content="https://pickmycostume.com/images/og/emoji-crew.jpg">
<meta property="og:type" content="website">
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
var BRACKET_DATA = __DATA__;
</script>
<style>
:root{--ink:#1c1a17;--muted:#6f6a61;--paper:#fffdf8;--card:#ffffff;--line:#e9e2d6;--cta:#d9481c;--gold:#b8860b}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.5}
.wrap{max-width:560px;margin:0 auto;padding:20px 16px 64px}
h1{font-size:28px;margin:8px 0 4px}
.sub{color:var(--muted);margin:0 0 20px}
.banner{background:#fff7e8;border:2px solid var(--gold);border-radius:14px;padding:14px 16px;margin:0 0 18px;font-size:16px}
.banner .who{font-weight:700}
.roundhead{font-size:13px;font-weight:800;text-transform:uppercase;letter-spacing:1px;color:var(--muted);margin:18px 0 10px}
.match{margin:0 0 14px}
.vs{text-align:center;color:var(--muted);font-size:12px;font-weight:800;margin:6px 0}
.card{background:var(--card);border:2px solid var(--line);border-radius:14px;overflow:hidden}
.card.won{border-color:var(--cta)}
button.pick{display:flex;align-items:center;gap:12px;width:100%;background:none;border:0;padding:14px;font-size:17px;cursor:pointer;text-align:left;color:var(--ink);font-family:inherit}
button.pick .e{font-size:34px;line-height:1}
button.pick .t{font-weight:700;flex:1}
button.pick:active{background:#faf3e6}
.card.won button.pick{background:#fff3e4}
a.guide{display:block;text-align:center;font-size:13px;color:var(--muted);padding:8px;text-decoration:none;border-top:1px dashed var(--line)}
a.guide:active{background:#faf3e6}
.champ{text-align:center;padding:8px 0}
.champ .e{font-size:88px;line-height:1.1}
.champ .t{font-size:26px;font-weight:800;margin:8px 0 2px}
.champ .lbl{font-size:13px;font-weight:800;text-transform:uppercase;letter-spacing:1px;color:var(--gold)}
.btn{display:inline-block;background:var(--cta);color:#fff;border:0;border-radius:999px;padding:13px 24px;font-size:16px;font-weight:700;cursor:pointer;margin:8px 6px 0 0;text-decoration:none;font-family:inherit}
.btn.ghost{background:#fff;color:var(--ink);border:1px solid var(--line)}
.btn:active{transform:scale(.98)}
.quizbox{margin-top:22px;background:#f4efe4;border-radius:14px;padding:16px;text-align:center}
.quizbox p{margin:0 0 10px;color:var(--muted)}
.namerow{margin:10px 0}
.namerow input{font-size:16px;padding:10px 12px;border:1px solid var(--line);border-radius:10px;width:220px;max-width:100%}
.fineprint{font-size:12px;color:var(--muted);margin-top:18px;text-align:center}
.toprow{display:flex;justify-content:space-between;align-items:center;margin-top:16px}
button.linklike{background:none;border:0;color:var(--muted);font-size:14px;cursor:pointer;text-decoration:underline;font-family:inherit}
footer{margin-top:40px;font-size:13px;color:#777;}</style>
</head>
<body>
<div class="wrap">
  <div id="banner" class="banner" hidden></div>
  <h1>Beat My Bracket</h1>
  <p class="sub" id="sub">16 costumes enter. You pick the winners, round by round, until one champion is left. Then challenge a friend to beat it.</p>
  <div id="play"></div>
  <div id="champ" class="champ" hidden>
    <div class="lbl">Your champion</div>
    <div class="e" id="ce"></div>
    <div class="t" id="ct"></div>
    <div class="namerow">
      <input id="nm" maxlength="40" placeholder="Your name (for the challenge)" aria-label="Your name for the challenge">
</div>
    <div>
      <a class="btn" id="buildbtn" href="#">Build this costume</a>
      <button class="btn ghost" id="sharebtn">Challenge a friend</button>
</div>
    <div class="quizbox">
      <p>Not your vibe? Find the costume that actually fits you.</p>
      <a class="btn" href="https://pickmycostume.com/?src=share-bracket">Take the 2-minute quiz</a>
</div>
</div>
  <div class="toprow">
    <button class="linklike" id="resetbtn">Start over</button>
    <a class="linklike" href="https://pickmycostume.com/?src=share-bracket" style="text-decoration:none"><button class="linklike" type="button">Skip to the quiz</button></a>
</div>
  <p class="fineprint">Same link, same bracket: a shared link always deals the same 16 in the same order.</p>
</div>
<script>
var _tapGuards={};
function tapGuard(key,ms){var n=Date.now();if(n-(_tapGuards[key]||0)<ms)return false;_tapGuards[key]=n;return true;}
function newShareId(){var c="abcdefghijklmnopqrstuvwxyz0123456789",s="";for(var i=0;i<8;i++)s+=c[Math.floor(Math.random()*c.length)];return s;}
function $(id){return document.getElementById(id);}
function esc(s){return String(s==null?"":s);}
/* Deterministic PRNG: xmur3 string hash + mulberry32. Same seed => same shuffle. */
function xmur3(str){var h=1779033703^str.length;for(var i=0;i<str.length;i++){h=Math.imul(h^str.charCodeAt(i),3432918353);h=h<<13|h>>>19;}return function(){h=Math.imul(h^(h>>>16),2246822507);h=Math.imul(h^(h>>>13),3266489909);return (h^=h>>>16)>>>0;};}
function mulberry32(a){return function(){a|=0;a=a+0x6D2B79F5|0;var t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
function seededSixteen(seed){
  var rand=mulberry32(xmur3(String(seed))());
  var idx=[];for(var i=0;i<BRACKET_DATA.length;i++)idx.push(i);
  for(var j=idx.length-1;j>0;j--){var k=Math.floor(rand()*(j+1));var t=idx[j];idx[j]=idx[k];idx[k]=t;}
  return idx.slice(0,16).map(function(i){return BRACKET_DATA[i];});
}
var byId={};BRACKET_DATA.forEach(function(e){byId[e.id]=e;});
function qp(name){var m=new RegExp("[?&]"+name+"=([^&]*)").exec(location.search||"");return m?decodeURIComponent(m[1].replace(/\+/g," ")):"";}
var SEED=qp("b")||"2026";
var ROUND_NAMES=["Round of 16","Quarterfinals","Semifinals","Final"];
var slots=seededSixteen(SEED);
var roundIdx=0, decided=[];
function guideURL(e){return "https://pickmycostume.com/c/"+e.id+"?src=share-bracket";}
function cardHTML(e){
  return '<div class="card" data-id="'+e.id+'"><button class="pick" data-id="'+e.id+'"><span class="e">'+e.emoji+'</span><span class="t">'+e.title+'</span></button><a class="guide" href="'+guideURL(e)+'">build guide</a></div>';
}
function renderRound(){
  var n=Math.pow(2,4-roundIdx);
  var html='<div class="roundhead">'+ROUND_NAMES[roundIdx]+'</div>';
  for(var m=0;m<n/2;m++){
    var a=slots[m*2],b=slots[m*2+1];
    html+='<div class="match">'+cardHTML(a)+'<div class="vs">vs</div>'+cardHTML(b)+'</div>';
  }
  $("play").innerHTML=html;
  $("champ").hidden=true;
  var picks=$("play").querySelectorAll("button.pick");
  for(var i=0;i<picks.length;i++){
    (function(btn){var key="bracket-advance-"+roundIdx+"-"+btn.getAttribute("data-id");btn.addEventListener("click",function(){
      if(!tapGuard(key,400))return;
      advance(btn.getAttribute("data-id"));
    });})(picks[i]);
  }
}
function advance(id){
  decided.push(id);
  var cards=$("play").querySelectorAll(".card");
  for(var i=0;i<cards.length;i++){if(cards[i].getAttribute("data-id")===id)cards[i].classList.add("won");}
  var need=Math.pow(2,4-roundIdx)/2;
  if(decided.length>=need){
    slots=decided.map(function(id){return byId[id];});decided=[];roundIdx++;
    if(roundIdx>=4){showChampion(slots[0]);}
    else{renderRound();}
  }
}
function showChampion(e){
  $("play").innerHTML="";
  $("champ").hidden=false;
  $("ce").textContent=e.emoji;
  $("ct").textContent=e.title;
  $("buildbtn").href=guideURL(e);
  window._champId=e.id;
  ph("bracket_champion",{seed:SEED,idea_id:e.id});
  try{window.scrollTo(0,0);}catch(x){}
}
function shareURL(){
  var u="https://pickmycostume.com/bracket?b="+encodeURIComponent(SEED)+"&c="+encodeURIComponent(window._champId||"");
  var nm=$("nm").value.trim().slice(0,40);
  if(nm)u+="&n="+encodeURIComponent(nm);
  if(window._bracketSid)u+="&s="+encodeURIComponent(window._bracketSid);
  return u;
}
function shareText(){
  var e=byId[window._champId];if(!e)return "";
  var nm=$("nm").value.trim().slice(0,40);
  var who=nm?nm+" crowns ":"My bracket crowns ";
  return who+e.emoji+" "+e.title+" costume champion. Think yours wins? Play the same bracket: "+shareURL();
}
$("sharebtn").addEventListener("click",function(){
  if(!tapGuard("bracket-share",1000))return;
  window._bracketSid=newShareId();
  var text=shareText();if(!text)return;
  ph("bracket_shared",{seed:SEED,idea_id:window._champId||"",share_id:window._bracketSid});
  ph("share_created",{share_id:window._bracketSid,idea_id:window._champId||"",share_origin:"bracket"});
  if(window.navigator&&window.navigator.share){
    window.navigator.share({title:"Beat My Bracket",text:text,url:shareURL()}).catch(function(){});
  }else if(window.navigator&&window.navigator.clipboard&&window.navigator.clipboard.writeText){
    window.navigator.clipboard.writeText(text).catch(function(){});
  }else{
    try{window.prompt("Copy your challenge:",text);}catch(x){}
  }
});
$("resetbtn").addEventListener("click",function(){
  slots=seededSixteen(SEED);roundIdx=0;decided=[];renderRound();
});
(function init(){
  var label=$("sub");
  label.textContent=SEED==="2026"
    ?"The 2026 bracket: 16 costumes enter. You pick the winners, round by round, until one champion is left. Then challenge a friend to beat it."
    :"A custom bracket ("+SEED+"): 16 costumes enter. You pick the winners, round by round, until one champion is left. Then challenge a friend to beat it.";
  var cid=qp("c"),e=cid&&byId[cid];
  if(e){
    var b=$("banner");b.hidden=false;
    var nm=qp("n").trim().slice(0,40);
    var who=document.createElement("span");who.className="who";
    who.textContent=nm?nm:"Your friend";
    b.appendChild(who);
    var rest=document.createElement("span");
    rest.textContent=" crowns "+e.emoji+" "+e.title+" champion. Think yours wins? Play the same bracket below. ";
    b.appendChild(rest);
    var g=document.createElement("a");g.href=guideURL(e);g.textContent="See the build guide.";
    b.appendChild(g);
  }
  ph("bracket_viewed",{seed:SEED,recipient:!!e,via_share_id:qp("s")||""});
  renderRound();
})();
</script>
<footer>Built with Muse.</footer></body>
</html>
"""

# nested <a><button> is invalid HTML: fix the reset row to avoid it
TEMPLATE = TEMPLATE.replace(
    '<a class="linklike" href="https://pickmycostume.com/?src=share-bracket" style="text-decoration:none"><button class="linklike" type="button">Skip to the quiz</button></a>',
    '<a class="linklike" href="https://pickmycostume.com/?src=share-bracket">Skip to the quiz</a>',
)


def main():
    # --out PATH: write to a scratch path instead of the real page
    # (sandbox pattern from the verify-lastcall/survive fix, 2026-10-22).
    # Default is unchanged: the real bracket.html.
    out = OUT
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    ideas = load_bank()
    emoji = load_emoji()
    data = build_data(ideas, emoji)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if "</script" in payload.lower():
        fail("payload contains </script")
    if DASH_RE.search(payload):
        fail("payload contains em/en dash")
    page = TEMPLATE.replace("__DATA__", payload).replace("__PH_KEY__", PH_KEY)
    if DASH_RE.search(page):
        fail("page contains em/en dash")
    if "__DATA__" in page or "__PH_KEY__" in page:
        fail("unreplaced template token")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    h = hashlib.sha256(page.encode("utf-8")).hexdigest()
    print("wrote %s (%d bytes, sha256 %s...)" % (out, len(page), h[:16]))


if __name__ == "__main__":
    main()
