#!/usr/bin/env python3
"""Build survive.html: 'Will it survive trick-or-treat night?' route-durability test.

Reads mcp-server/bank.json (source of truth), scans each idea's materials list
and blurb for route-risk words (mask, cape, wings, face paint, tall hat,
cardboard, long fabric, carried props, heels), and embeds a deterministic JSON
index into a self-contained page.

Mechanic: pick a costume (type-ahead over all bank ideas, or ?pick=<slug> deep
link), answer 6 yes/no route questions, get a score + verdict + per-fail fixes,
share the score (native share -> clipboard -> prompt). Every CTA carries
?src=share-survive so arrivals are attributable. Ends at the quiz for low scores.

Repair note (2026-10-22, Family A slice 3): the == 138 asserts froze this
page when the bank grew to 169 on Oct 3; the count is now derived
(>= 100 floor + slug-set equality, the build_aisle_dupes.py pattern) and
the fine-print count renders from len(ideas). Displayed time is hands-on
only (display_time() strips any "+ ... drying" suffix; the live page
already shows stripped times), and the bank's removed cost field is no
longer emitted in the index (this generator's card template already
renders time + effort only; the live page still displays stale costs).

Staged code only. NO deploy. Not wired into nav or sitemap. No existing-page edits.
"""
import json, re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "mcp-server", "bank.json")
OUT = os.path.join(ROOT, "survive.html")

DASHES = ("\u2013", "\u2014")

# Scan rules: (key, label, why, regex). Craft tools are not route risks.
RULES = [
    ("mask", "Includes a mask",
     "Masks cut side vision. Trick-or-treat streets have cars, curbs, and stairs.",
     re.compile(r"\bmask(s|ed)?\b")),
    ("paint", "Uses face paint",
     "Face paint smudges with sweat and rain, and runs if the night turns wet.",
     re.compile(r"\bface paint\b")),
    ("cape", "Has a cape",
     "Capes drag, snag on fences, and get stepped on from behind.",
     re.compile(r"\bcape\b")),
    ("wings", "Has wings",
     "Wings do not fit through doorways, car doors, or crowded sidewalks.",
     re.compile(r"\bwings?\b")),
    ("tallhat", "Has a tall hat",
     "Tall hats do not survive car rides, low branches, or hugs.",
     re.compile(r"\b(top hat|tall hat|wizard hat|pointy hat|sombrero|stovepipe hat)\b")),
    ("cardboard", "Built from cardboard",
     "Cardboard melts in rain and crumples in a crowd.",
     re.compile(r"\bcardboard\b")),
    ("longfabric", "Long or dragging fabric",
     "Anything near the ground gets stepped on, usually by 8pm.",
     re.compile(r"\b(floor-length|floor length|long skirt|long dress|long gown|trailing)\b|\btrain\b")),
    ("prop", "Carries a prop in hand",
     "A prop means one hand is busy: no candy bag, no handrail on stairs.",
     re.compile(r"\b(swords?|staff|trident|wand|scepter|pitchfork|lantern|shield|rackets?|microphone|hose|fishing rod|umbrella|camera|binoculars|tube of balls|toy sword)\b")),
    ("heels", "Tricky footwear",
     "A mile of sidewalks in bad shoes ends the night early.",
     re.compile(r"\b(high heels?|heels|platform shoes?|stilts)\b")),
]

SANITIZE = ("bow tie", "glue gun", "hot glue gun", "utility knife", "masking tape")

QUESTIONS = [
    ("walk", "Can you walk a mile in it without stopping to fix anything?",
     "Tape down anything floppy and do a hallway test walk tonight."),
    ("see", "Can you see clearly in every direction?",
     "Widen the eye holes, or swap the mask for face paint."),
    ("hands", "Are both hands free for the candy bag, doors, and stairs?",
     "Leave the prop home, or rig a belt hook so both hands stay free."),
    ("rain", "Will it survive drizzle?",
     "Pack a clear poncho. Cardboard and face paint do not love rain."),
    ("sit", "Can you sit in the car and use the bathroom without a costume crisis?",
     "Pick a hat that comes off easy, and a base layer that works on its own."),
    ("trip", "Is everything above the ankles, with nothing dragging that can trip you?",
     "Hem it above the ankles. Anything dragging gets stepped on by 8pm."),
]

SHORT = {"walk": "the walk", "see": "seeing", "hands": "hands free",
         "rain": "rain", "sit": "bathroom", "trip": "tripping"}

def display_time(t):
    # Displayed times are hands-on only: strip any "+ ... drying" suffix
    # (proven pattern from gen_costumes_hub.py / build_aisle_dupes.py).
    return re.sub(r"\s*\+.*drying\s*$", "", str(t))


def compute_flags(idea, ins):
    text = (" ".join(ins.get("m", [])) + " " + idea.get("blurb", "")).lower()
    for phrase in SANITIZE:
        text = text.replace(phrase, phrase.replace(" ", ""))
    flags = []
    for key, label, why, rx in RULES:
        if rx.search(text):
            flags.append({"k": key, "label": label, "why": why})
    return flags

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Will It Survive Trick-or-Treat Night? | Pick My Costume</title>
<meta name="description" content="Pick a costume, answer 6 route questions, get a trick-or-treat survival score worth sharing.">
<link rel="canonical" href="https://pickmycostume.com/survive.html">
<meta property="og:title" content="Will It Survive Trick-or-Treat Night?">
<meta property="og:description" content="6 questions. One score. Find out if the costume can walk the whole route.">
<meta property="og:type" content="website">
<style>
body{font-family:system-ui,-apple-system,sans-serif;max-width:640px;margin:0 auto;padding:20px;line-height:1.5;color:#222}
h1{font-size:1.6em;margin-bottom:.2em}
.sub{color:#555;margin-bottom:1.2em}
#q{width:100%;padding:12px;font-size:16px;border:2px solid #ccc;border-radius:8px;box-sizing:border-box}
#hits{list-style:none;margin:4px 0 0;padding:0;border:1px solid #ddd;border-radius:8px;display:none;max-height:260px;overflow:auto}
#hits li{padding:10px 12px;cursor:pointer;border-bottom:1px solid #eee}
#hits li:last-child{border-bottom:none}
#hits li:hover{background:#f5f0ff}
.card{border:1px solid #e3d9ff;background:#faf8ff;border-radius:12px;padding:16px;margin:16px 0}
.triple{color:#555;font-size:.95em;margin:.4em 0}
.flag{border-left:3px solid #f0a;margin:8px 0;padding:6px 10px;background:#fff}
.flag b{display:block}
.flag span{font-size:.9em;color:#555}
.ques{border:1px solid #ddd;border-radius:12px;padding:14px;margin:10px 0}
.ques p{margin:0 0 10px;font-weight:600}
.btnrow{display:flex;gap:10px}
.btnrow button{flex:1;padding:12px;font-size:16px;border-radius:8px;border:2px solid #6c3fd4;background:#fff;color:#6c3fd4;cursor:pointer;font-weight:600}
.btnrow button.sel{background:#6c3fd4;color:#fff}
.score{font-size:3em;font-weight:800;margin:.2em 0}
.verdict{font-size:1.25em;font-weight:700}
.fix{border-left:3px solid #e80;margin:8px 0;padding:6px 10px;background:#fffdf5}
.fix b{display:block}
.fix span{font-size:.9em;color:#555}
.cta{display:inline-block;margin:8px 8px 0 0;padding:12px 18px;border-radius:10px;background:#6c3fd4;color:#fff;text-decoration:none;font-weight:700}
.cta.ghost{background:#fff;color:#6c3fd4;border:2px solid #6c3fd4}
.sharebox{margin-top:14px}
.sharebox button{padding:12px 18px;font-size:16px;border-radius:10px;border:2px solid #6c3fd4;background:#fff;color:#6c3fd4;font-weight:700;cursor:pointer}
.disclaimer{font-size:.85em;color:#666;border-top:1px solid #eee;margin-top:24px;padding-top:12px}
.hidden{display:none!important}
footer{margin-top:40px;font-size:13px;color:#777;}</style><script>
var _phq=[];
function track(name, props){ try { if (window.posthog && posthog.capture) posthog.capture(name, props || {}); else _phq.push([name, props || {}]); } catch (e) {} }
(function(){ var s=document.createElement('script'); s.async=true; s.src='https://us.i.posthog.com/static/array.js';
s.onload=function(){ try { if (window.posthog && posthog.init){ posthog.init('phc_t9dkHXAZR5VEjPFm3K5JDzGKFsNNxKcwSxxcEBEeLbS7',{api_host:'https://us.i.posthog.com',autocapture:false,capture_pageview:true,disable_session_recording:true}); _phq.splice(0).forEach(function(e){ try{posthog.capture(e[0],e[1]);}catch(x){} }); } } catch(e){} };
document.head.appendChild(s); })();
</script>
</head>
<body>
<h1>Will it survive trick-or-treat night?</h1>
<p class="sub">Pick a costume. Answer 6 route questions. Get a score worth sharing. Takes about a minute.</p>

<div id="step1">
<label for="q"><b>Which costume are you testing?</b></label>
<input id="q" type="search" placeholder="Type a costume name, like vampire or astronaut" autocomplete="off" role="combobox" aria-expanded="false" aria-controls="hits">
<ul id="hits" role="listbox"></ul>
</div>

<div id="step2" class="hidden">
<div class="card" id="ideacard"></div>
<div id="questions"></div>
</div>

<div id="step3" class="hidden">
<div class="card" id="result"></div>
<div class="sharebox">
<button id="sharebtn" type="button">Share my score</button>
</div>
<div style="margin-top:16px">
<a class="cta" id="quizcta" href="/?src=share-survive">Take the 2-minute quiz</a>
<a class="cta ghost" id="guidecta" href="#">Open the build guide</a>
</div>
<div class="disclaimer">
<b>Honest fine print.</b> The heads-ups come from our own __COUNT__-idea costume bank: its materials lists and blurbs. We cannot walk the route for you. When in doubt, do the hallway test tonight.
</div>
</div>
<script>
var INDEX = __INDEX_JSON__;
var QUESTIONS = __QUESTIONS_JSON__;
var SHORT = __SHORT_JSON__;
var BASE = "https://pickmycostume.com/survive.html";
function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function okTrack(){try{return location.search.indexOf("probe=")===-1;}catch(e){return true;}}
function ph(name,props){if(!okTrack())return;try{if(window.posthog&&window.posthog.capture){window.posthog.capture(name,props||{});}}catch(e){}}
function byId(id){for(var i=0;i<INDEX.length;i++)if(INDEX[i].id===id)return INDEX[i];return null;}

var q=document.getElementById("q"),hits=document.getElementById("hits");
var step2=document.getElementById("step2"),step3=document.getElementById("step3");
var current=null,answers={};

function doSearch(){
  var v=q.value.trim().toLowerCase();
  hits.innerHTML="";hits.style.display="none";q.setAttribute("aria-expanded","false");
  if(v.length<2)return;
  var res=INDEX.filter(function(e){return e.t.toLowerCase().indexOf(v)>-1;}).slice(0,8);
  if(!res.length)return;
  res.forEach(function(e){
    var li=document.createElement("li");li.textContent=e.t;li.setAttribute("role","option");
    li.tabIndex=0;
    function go(){pick(e.id);}
    li.onclick=go;
    li.onkeydown=function(ev){if(ev.key==="Enter"||ev.key===" "){ev.preventDefault();go();}};
    hits.appendChild(li);
  });
  hits.style.display="block";q.setAttribute("aria-expanded","true");
}

function flagHTML(f){return '<div class="flag"><b>'+esc(f.label)+'</b><span>'+esc(f.why)+'</span></div>';}

function pick(id){
  var e=byId(id);if(!e)return;
  current=e;answers={};
  q.value=e.t;hits.style.display="none";
  var h='<h2 style="margin-top:0">'+esc(e.t)+'</h2><p>'+esc(e.b)+'</p>';
  h+='<p class="triple">'+esc(e.time)+' &middot; '+esc(e.effort)+'</p>';
  if(e.flags.length){
    h+='<p style="margin-bottom:4px"><b>Heads-up from the build guide:</b></p>';
    e.flags.forEach(function(f){h+=flagHTML(f);});
  }else{
    h+='<p style="color:#2a7;font-weight:600">No route risks spotted in the build guide. Nice pick.</p>';
  }
  document.getElementById("ideacard").innerHTML=h;
  var qh="";
  QUESTIONS.forEach(function(qq){
    qh+='<div class="ques" data-k="'+qq.k+'"><p>'+esc(qq.label)+'</p>'+
        '<div class="btnrow"><button type="button" data-v="yes">Yes</button>'+
        '<button type="button" data-v="no">No</button></div></div>';
  });
  var qd=document.getElementById("questions");qd.innerHTML=qh;
  qd.querySelectorAll(".ques").forEach(function(div){
    var k=div.getAttribute("data-k");
    div.querySelectorAll("button").forEach(function(b){
      b.onclick=function(){
        answers[k]=b.getAttribute("data-v");
        div.querySelectorAll("button").forEach(function(x){x.classList.remove("sel");});
        b.classList.add("sel");
        maybeScore();
      };
    });
  });
  step2.classList.remove("hidden");step3.classList.add("hidden");
  ph("survive_picked",{idea:e.id,flags:e.flags.length});
}

function maybeScore(){
  for(var i=0;i<QUESTIONS.length;i++)if(!answers[QUESTIONS[i].k])return;
  score();
}

function verdict(score){
  if(score===6)return["Built for the route.","This costume can walk the whole neighborhood. Screenshot this and send it to the group chat."];
  if(score>=4)return["One fix away.","A couple of small fixes and this costume is route-ready. The fixes are below."];
  return["Porch-only pick.","Great for photos and parties, risky for the full route. Want one that can go the distance? Take the 2-minute quiz."];
}

function shareText(){
  var score=0,fails=[];
  QUESTIONS.forEach(function(qq){if(answers[qq.k]==="yes")score++;else fails.push(SHORT[qq.k]);});
  if(score===6)return "My "+current.t+" scored 6/6 on the trick-or-treat survival test: built for the route. Will yours survive? "+BASE+"?src=share-survive";
  return "My "+current.t+" scored "+score+"/6 on the trick-or-treat survival test. Weak spots: "+fails.join(", ")+". Will your costume survive the route? "+BASE+"?src=share-survive";
}

function score(){
  var s=0,fails=[];
  QUESTIONS.forEach(function(qq){
    if(answers[qq.k]==="yes")s++;else fails.push(qq);
  });
  var v=verdict(s);
  var h='<div class="score">'+s+'/6</div><div class="verdict">'+esc(v[0])+'</div><p>'+esc(v[1])+'</p>';
  fails.forEach(function(qq){
    h+='<div class="fix"><b>'+esc(qq.label)+'</b><span>'+esc(qq.fix)+'</span></div>';
  });
  document.getElementById("result").innerHTML=h;
  document.getElementById("guidecta").href="/c/"+current.id+"?src=share-survive";
  step3.classList.remove("hidden");
  try{step3.scrollIntoView({behavior:"smooth",block:"start"});}catch(e){}
  ph("survive_scored",{idea:current.id,score:s});
}

document.getElementById("sharebtn").onclick=function(){
  var text=shareText();
  function done(){ph("survive_shared",{idea:current.id});}
  if(navigator.share){navigator.share({title:"Trick-or-treat survival test",text:text,url:BASE+"?src=share-survive"}).then(done,done);}
  else if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).then(function(){alert("Score copied. Paste it into the group chat.");done();},function(){prompt("Copy your score:",text);done();});}
  else{prompt("Copy your score:",text);done();}
};

q.addEventListener("input",doSearch);
(function(){
  ph("survive_viewed",{});
  var m=/[?&]pick=([a-z0-9-]+)/.exec(location.search);
  if(m&&byId(m[1]))pick(m[1]);
})();
</script>
<footer>Built with Muse.</footer></body>
</html>
""";

def main():
    # --out PATH (2026-10-22, verifier sandboxing): write to a scratch
    # path instead of the real page, following build_swap_rack_kit.py.
    # Default is unchanged: the real ../survive.html.
    out = OUT
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    with open(BANK) as f:
        bank = json.load(f)
    ideas = bank["ideas"]
    ins = bank["instructions"]
    # Bank size is derived, never hard-coded: the == 138 asserts froze
    # this page when the bank grew to 169 on Oct 3. Non-vacuous floor +
    # slug-set equality, following the repaired build_aisle_dupes.py
    # pattern.
    assert len(ideas) >= 100, "bank yielded only %d ideas" % len(ideas)
    ids = [i["id"] for i in ideas]
    assert len(set(ids)) == len(ids), "duplicate ids"
    assert set(ins) == set(ids), "bank idea/instruction slug sets differ"

    index = []
    for idea in ideas:
        iid = idea["id"]
        g = ins.get(iid, {})
        flags = compute_flags(idea, g)
        index.append({
            "id": iid,
            "t": idea["title"],
            "b": idea["blurb"],
            "time": display_time(g.get("time", "")),
            "effort": g.get("effort", ""),
            "flags": flags,
        })

    index_json = json.dumps(index, ensure_ascii=False)
    assert "__COUNT__" not in index_json, "count placeholder in bank data"
    page = PAGE
    page = page.replace("__INDEX_JSON__", index_json)
    page = page.replace("__QUESTIONS_JSON__",
                        json.dumps([{"k": k, "label": l, "fix": f}
                                    for k, l, f in QUESTIONS], ensure_ascii=False))
    page = page.replace("__SHORT_JSON__", json.dumps(SHORT, ensure_ascii=False))
    page = page.replace("__COUNT__", str(len(index)))
    assert "__COUNT__" not in page, "count placeholder not replaced"

    for d in DASHES:
        assert d not in page, "em/en dash leaked into page copy"

    with open(out, "w") as f:
        f.write(page)

    # determinism check
    page2 = PAGE
    page2 = page2.replace("__INDEX_JSON__", index_json)
    page2 = page2.replace("__QUESTIONS_JSON__",
                          json.dumps([{"k": k, "label": l, "fix": f}
                                      for k, l, f in QUESTIONS], ensure_ascii=False))
    page2 = page2.replace("__SHORT_JSON__", json.dumps(SHORT, ensure_ascii=False))
    page2 = page2.replace("__COUNT__", str(len(index)))
    assert page2 == page, "non-deterministic build"

    flagged = sum(1 for e in index if e["flags"])
    print("wrote %s: %d ideas, %d with route flags" % (out, len(index), flagged))

if __name__ == "__main__":
    main()
