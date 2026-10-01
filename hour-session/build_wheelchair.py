#!/usr/bin/env python3
"""Build wheelchair-costumes.html: wheelchair & mobility-aid costume guide.

"Rolls With It": 8 chair-first builds where the wheelchair IS the costume
(curated from the kid bank), plus a check-any-costume tool that scans the
bank's materials for wheel trouble (drag, bulk, sightlines, hands, headpieces).

Reads mcp-server/bank.json (source of truth). Staged code only. NO deploy.
Not wired into nav or sitemap. No inbound links from live surfaces.
"""
import json, re, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "mcp-server", "bank.json")
OUT = os.path.join(ROOT, "wheelchair-costumes.html")
FUZZY_JS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "fuzzy_typeahead.js")

DASHES = ("\u2013", "\u2014")
SRC = "share-wheelchair"
CANON = "https://pickmycostume.com/wheelchair-costumes"
OG = "https://pickmycostume.com/images/og/tiny-firefighter.jpg"

# (id, chair concept, build note). All ids must be kid-audience bank ideas.
BUILDS = [
    ("tiny-firefighter", "The chair is the fire truck.",
     "Red cardboard panels zip tied to the armrests, paper plate wheels taped "
     "flat on the push wheels so they spin free, and a cardboard ladder across "
     "the back. The kid wears the firefighter gear from the guide."),
    ("cardboard-knight", "The chair is the castle.",
     "Gray cardboard panels with cut out crenellations taped to the frame "
     "below the seat. Keep everything below the armrests so the knight can "
     "see the whole kingdom."),
    ("little-lifeguard", "The chair is the rescue boat.",
     "Red and white striped panels on the sides, a hand lettered RESCUE banner "
     "across the backrest, and a toy life ring looped on a push handle. The "
     "handles stay fully grippable."),
    ("robot-ranger", "The chair is the command station.",
     "A foil covered cardboard control panel laid across the lap, plus two "
     "blinking bike lights clipped to the frame. Nothing goes on the wheels."),
    ("ice-cream-cone", "The chair is the ice cream truck.",
     "White side panels with a hand lettered ICE CREAM sign on the back and "
     "red stripes along the armrests. The kid is the cone."),
    ("popcorn-bucket", "The chair is the popcorn cart.",
     "Red and white vertical stripes on the side panels and a POPCORN sign up "
     "top. Every panel stops well above the wheels."),
    ("fairy-tale-princesses", "The chair is the royal carriage.",
     "Gold cardboard panels on the sides and tulle draped only above the seat "
     "line, never near the wheels. A paper crown beats bobby pins."),
    ("spider", "The chair grows the other six legs.",
     "Black pool noodle legs zip tied to the frame above the wheels, angled "
     "outward. Wheels, brakes, and push rims stay fully clear."),
]

SAFETY = [
    ("Wheels spin free",
     "Nothing taped to the tires or spokes. Decorations live on the frame or above the wheels."),
    ("Push handles stay clear",
     "Whoever pushes needs the full grip. Hang things from the handles, never wrap them."),
    ("Nothing drags near the ground",
     "Hems, streamers, and panels stop well above the wheels. The ground always wins."),
    ("See and be seen",
     "Reflective tape on the back of the chair, and a clear sightline for the kid. Drivers are looking for ghosts, not chairs."),
]

# Sanitize phrases that look like flags but are not.
SANITIZE = [
    ("fabric paint", "fabricpaint"),
    ("mask stripe", "maskstripe"),
    ("drawn mustache", "drawnmustache"),
    ("drawn mustaches", "drawnmustaches"),
    ("for the beard", "forthebeard"),
    ("for mustache", "formustache"),
    ("for mustaches", "formustaches"),
    ("toy train", "toytrain"),
    ("train set", "trainset"),
]

# (key, regex, label, why, fix)
FLAGS = [
    ("drag", r"\bcape(s)?\b|\btrain\b|floor-length|\bdrag(s|ging)?\b|trailing|\bpuddle\b",
     "Drags near the wheels",
     "Anything that trails near the ground finds the wheels: capes, dress trains, long hems.",
     "Hem it to ankle length or pin it up for the night."),
    ("bulk", r"\btutu\b|\bcrinoline\b|\bhoop skirt\b|\bpuffy\b|\binflatable\b",
     "Bulky around the seat",
     "Skirt volume under the seat cushion tangles in the wheels and push rims.",
     "Keep the fullness above the seat. The chair does the twirl."),
    ("vision", r"\bmask(s|ed)?\b",
     "Blocks sightlines",
     "In a chair, seeing where you are going matters more. Masks shrink the world to two eye holes.",
     "Bigger eye holes first. If it still bugs them, the costume reads without the mask."),
    ("hands", r"\bstaff\b|\bbroom\b",
     "Needs both hands",
     "Kids who self propel need their hands on the push rims, not holding a prop.",
     "Mount the prop on the chair frame instead of in a hand."),
    ("tippy", r"\btall\b.{0,16}\bhat\b|\bpointy hat\b|\bcrown(s)?\b",
     "Tall headpiece",
     "Tall hats catch wind and doorframes, and they slide when the chair moves.",
     "A shorter version reads the same in photos."),
]

COMPILED = [(k, re.compile(rx), label, why, fix) for k, rx, label, why, fix in FLAGS]


def compute_flags(idea, ins):
    text = (" ".join(ins.get("m", [])) + " " + idea.get("blurb", "")).lower()
    for phrase, glued in SANITIZE:
        text = text.replace(phrase, glued)
    flags = []
    for k, rx, label, why, fix in COMPILED:
        if rx.search(text):
            flags.append((k, label, why, fix))
    return flags

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Wheelchair Halloween Costume Ideas: 8 Builds Where the Chair Is the Costume | Pick My Costume</title>
<meta name="description" content="Wheelchair costume ideas where the chair is part of the costume: fire truck, castle, rescue boat, ice cream truck. Plus a check that scans any of our 138 costumes for wheel trouble. Cardboard, tape, and a free build guide for each.">
<link rel="canonical" href="__CANON__">
<meta property="og:title" content="Wheelchair Costume Ideas: the Chair Is the Costume">
<meta property="og:description" content="8 builds where the wheelchair becomes the fire truck, the castle, the rescue boat. Plus a wheel-trouble check for any costume.">
<meta property="og:image" content="__OG__">
<meta property="og:type" content="website">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
{"@type":"Question","name":"Is this medical advice?","acceptedAnswer":{"@type":"Answer","text":"No. These are craft notes for decorating a wheelchair as part of a costume, built from our own costume bank. They cannot know your child or their chair. When in doubt, ask the kid."}},
{"@type":"Question","name":"Do I need to buy anything special for the chair builds?","acceptedAnswer":{"@type":"Answer","text":"No. Every build note uses cardboard, tape or zip ties, and craft supplies. The costume itself comes from our free build guides."}},
{"@type":"Question","name":"Will decorating damage the wheelchair?","acceptedAnswer":{"@type":"Answer","text":"Use painter's tape and zip ties, never hot glue or screws on the frame. Test any tape on a hidden spot first, and keep everything off the tires, spokes, brakes, and push handles."}},
{"@type":"Question","name":"My kid only uses the chair part time. Do these still work?","acceptedAnswer":{"@type":"Answer","text":"Yes. The chair builds are decorations on the chair for the hours it is in use, and every costume below also works fully on foot."}}]}
</script>
<style>
:root{--ink:#1c1a17;--muted:#6f6a61;--paper:#fffdf8;--card:#ffffff;--line:#e9e2d6;--green:#2e7d43;--greenbg:#e9f5ec;--amber:#9a6206;--amberbg:#fdf3e0;--red:#b3261e;--redbg:#fbeae8;--cta:#d9481c;--blue:#1d5fa8;--bluebg:#e9f1fb}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:680px;margin:0 auto;padding:20px 16px 64px}
.crumbs{font-size:13px;color:var(--muted);margin:0 0 8px}
.crumbs a{color:inherit}
h1{font-size:30px;line-height:1.2;margin:8px 0}
.sub{color:var(--muted);margin:0 0 20px}
h2{font-size:22px;margin:36px 0 8px}
h2 .em{font-style:normal}
.secsub{color:var(--muted);margin:0 0 16px;font-size:15px}
.build{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px;margin:12px 0}
.build h3{margin:0 0 2px;font-size:19px}
.chairline{color:var(--blue);font-weight:700;margin:4px 0 8px;font-size:15px}
.triple{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
.triple span{background:#f4efe4;border-radius:999px;padding:4px 12px;font-size:13px}
.blurb{color:var(--muted);font-size:15px;margin:8px 0}
.chairnote{font-size:15px;margin:8px 0 0}
.chairnote b{display:block;margin-bottom:2px}
.build .btns{margin-top:12px}
a.btn,button.btn{font-size:16px;padding:12px 18px;border-radius:12px;border:none;cursor:pointer;text-decoration:none;display:inline-block}
a.btn.primary{background:var(--cta);color:#fff}
a.btn.ghost{background:#fff;border:1px solid var(--line);color:var(--ink)}
button.btn.share{background:#1c1a17;color:#fff}
.btns{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}
.safety{display:grid;gap:10px;margin-top:12px}
.rule{background:var(--bluebg);border:1px solid #c9dcf2;border-radius:12px;padding:12px 14px;font-size:14px}
.rule b{display:block;margin-bottom:2px}
.searchbox{position:relative;margin-top:8px}
#q{width:100%;font-size:17px;padding:14px 16px;border:2px solid var(--line);border-radius:12px;background:#fff}
#q:focus{outline:none;border-color:var(--cta)}
#hits{list-style:none;margin:8px 0 0;padding:0;border:1px solid var(--line);border-radius:12px;background:#fff;max-height:280px;overflow:auto;display:none}
#hits li{padding:12px 14px;border-bottom:1px solid var(--line);cursor:pointer;font-size:16px}
#hits li:last-child{border-bottom:none}
#hits li:active{background:#f7f3ea}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px;margin-top:20px;display:none}
.card.show{display:block}
.verdict{font-size:19px;font-weight:700;margin:0 0 4px}
.verdict.green{color:var(--green)}
.verdict.amber{color:var(--amber)}
.verdict.red{color:var(--red)}
.verdsub{color:var(--muted);font-size:14px;margin:0 0 12px}
.flag{border:1px solid var(--line);border-left:4px solid var(--amber);background:var(--amberbg);border-radius:8px;padding:10px 12px;margin:8px 0}
.flag b{display:block}
.flag span{color:var(--muted);font-size:14px}
.flag .fix{display:block;margin-top:6px;color:var(--ink);font-size:14px}
.clear{background:var(--greenbg);border:1px solid #cfe5d4;border-radius:8px;padding:10px 12px;margin:8px 0;font-size:14px}
.kit{background:#f7f3ea;border-radius:16px;padding:18px;margin:12px 0}
.kit h3{margin:0 0 6px;font-size:17px}
.kit pre{background:#fff;border:1px solid var(--line);border-radius:8px;padding:12px;font-size:13px;white-space:pre-wrap;font-family:inherit;margin:8px 0}
.kit button{margin-top:4px}
.method{margin-top:28px;font-size:13px;color:var(--muted);border-top:1px solid var(--line);padding-top:16px}
.disclaimer{background:#f7f3ea;border-radius:12px;padding:14px;margin-top:16px;font-size:14px}
@media print{.btns,.searchbox,.kit button,.crumbs{display:none}}
</style>
</head>
<body>
<div class="wrap">
  <p class="crumbs"><a href="/">Pick My Costume</a> / wheelchair costumes</p>
  <h1>Rolls with it &#9855;</h1>
  <p class="sub">The best wheelchair costumes do not work around the chair. They make the chair the costume. Eight builds below, each with a free step by step guide. Then a wheel-trouble check for any costume in our bank.</p>

  <h2><span class="em">&#127875;</span> 8 builds where the chair is the costume</h2>
  <p class="secsub">Cardboard, tape, and zip ties. Every build note keeps the wheels, brakes, and push handles clear.</p>
  __BUILDS_HTML__

  <h2><span class="em">&#128663;</span> The 4 rules of chair builds</h2>
  <div class="safety">
  __SAFETY_HTML__
  </div>

  <h2><span class="em">&#128269;</span> Check any costume for wheel trouble</h2>
  <p class="secsub">Pick a costume. We scan its materials for the five things that fight a wheelchair: drag near the wheels, bulk around the seat, blocked sightlines, two-handed props, and tall headpieces.</p>
  <div class="searchbox">
    <input id="q" type="search" placeholder="Start typing a costume, like Tiny Firefighter" autocomplete="off" aria-label="Search costumes">
    <ul id="hits" role="listbox"></ul>
  </div>
  <div class="card" id="card" aria-live="polite">
    <p class="verdict" id="verdict"></p>
    <p class="verdsub" id="verdsub"></p>
    <h2 id="ctitle" style="margin:12px 0 0;font-size:22px"></h2>
    <p class="blurb" id="cblurb"></p>
    <div class="triple" id="triple"></div>
    <div id="flags"></div>
    <div class="btns">
      <a class="btn primary" id="guide" href="#">Build guide</a>
      <button class="btn share" id="sharebtn">Send to the parent chat</button>
      <a class="btn ghost" id="quiz" href="/?src=__SRC__">Take the 2-minute quiz</a>
    </div>
  </div>

  <h2><span class="em">&#128172;</span> Share kit</h2>
  <p class="secsub">Copy, paste, done. For the parent group chat, the class chat, or Pinterest.</p>
  <div class="kit">
    <h3>Parent group chat</h3>
    <pre id="chattext">Building a wheelchair costume this year? These 8 builds make the chair the costume (fire truck, castle, rescue boat), and the wheel-trouble check scans any costume for drag, bulk, and blocked sightlines: __CANON__?src=__SRC__ &#127875;</pre>
    <button class="btn share" id="copychat">Copy chat text</button>
  </div>
  <div class="kit">
    <h3>Pinterest description</h3>
    <pre id="pintext">Wheelchair Halloween costumes where the chair IS the costume: fire truck, castle, rescue boat, ice cream truck, popcorn cart, royal carriage. Free build guides plus a wheel-trouble check for any costume. __CANON__?src=__SRC__ &#9855;&#127875;</pre>
    <button class="btn share" id="copypin">Copy pin text</button>
  </div>

  <div class="disclaimer">
    <b>Honest fine print.</b> This page scans our own __N__-idea costume bank and adds craft notes for decorating a wheelchair. It is not medical advice, and it cannot know your child or their chair. Painter's tape and zip ties, never glue or screws on the frame. When in doubt, ask the kid.
  </div>
  <div class="method">
    How we check: we scan each costume's materials and blurb for the five wheel-trouble families and list everything we find with a one-line fix. __CALM__ of __N__ ideas carry zero flags.
  </div>
</div>
__FAQ_HTML__
<script>
var INDEX = __INDEX_JSON__;
function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function ph(name,props){props=props||{};try{var q=location.search;if(/[?&](probe|sim)=/.test(q)||/[?&]internal=1/.test(q))props.internal=true;if(window.posthog&&window.posthog.capture){window.posthog.capture(name,props);}}catch(e){}}
ph("wheelchair_opened",{});
var q=document.getElementById("q"),hits=document.getElementById("hits"),card=document.getElementById("card");
var current=null;
__FUZZY_TYPEAHEAD__
var SEARCH_INDEX=INDEX.map(function(e){return{id:e.id,title:e.t,blurb:e.b};});
var INDEX_BY_ID={};INDEX.forEach(function(e){INDEX_BY_ID[e.id]=e;});
function doSearch(){
  hits.innerHTML="";hits.style.display="none";
  var found=FuzzyTypeAhead.search(q.value,SEARCH_INDEX);
  if(!found.length)return;
  found.forEach(function(r){
    var e=INDEX_BY_ID[r.id];
    var li=document.createElement("li");li.textContent=e.t;li.setAttribute("role","option");
    li.setAttribute("tabindex","0");
    li.onclick=function(){pick(e.id);};
    li.onkeydown=function(ev){if(ev.key==="Enter"||ev.key===" "){ev.preventDefault();pick(e.id);}};
    hits.appendChild(li);
  });
  hits.style.display="block";
}
function pick(id){
  var e=INDEX_BY_ID[id];if(!e)return;current=e;
  hits.style.display="none";q.value=e.t;
  var v=document.getElementById("verdict"),vs=document.getElementById("verdsub");
  if(e.flags.length===0){
    v.textContent="Chair-ready from the materials";v.className="verdict green";
    vs.textContent="No drag, bulk, blocked sightlines, two-handed props, or tall headpieces in the materials list.";
  }else if(e.flags.length===1){
    v.textContent="One fix and it rolls";v.className="verdict amber";
    vs.textContent="One thing in the materials might fight the wheelchair. The fix is below.";
  }else{
    v.textContent="Worth a rethink";v.className="verdict red";
    vs.textContent=e.flags.length+" things in the materials might fight the wheelchair. Fixes below, or find a chair-ready pick with the quiz.";
  }
  document.getElementById("ctitle").textContent=e.t;
  document.getElementById("cblurb").textContent=e.b;
  document.getElementById("triple").innerHTML=
    "<span>"+esc(e.time)+"</span><span>"+esc(e.cost)+"</span><span>"+esc(e.effort)+"</span>";
  var fh="";
  e.flags.forEach(function(f){fh+='<div class="flag"><b>'+esc(f.label)+'</b><span>'+esc(f.why)+'</span><span class="fix">Fix: '+esc(f.fix)+'</span></div>';});
  if(e.flags.length===0){fh+='<div class="clear">Checked: no capes, trains, floor-length hems, tutus, masks, staffs, or tall hats in the materials.</div>';}
  document.getElementById("flags").innerHTML=fh;
  document.getElementById("guide").href="/c/"+e.id+"?src=__SRC__";
  card.classList.add("show");
  ph("wheelchair_checked",{idea:e.id,flags:e.flags.length});
  if(history.replaceState){try{history.replaceState(null,"","/wheelchair-costumes?pick="+encodeURIComponent(e.id));}catch(err){}}
}
q.addEventListener("input",doSearch);
function copyText(id,okmsg){
  var t=document.getElementById(id).textContent;
  ph("wheelchair_shared",{which:id});
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(function(){alert(okmsg);},function(){prompt("Copy this:",t);});}
  else{prompt("Copy this:",t);}
}
document.getElementById("copychat").onclick=function(){copyText("chattext","Copied. Paste it in the parent chat.");};
document.getElementById("copypin").onclick=function(){copyText("pintext","Copied. Paste it as the pin description.");};
document.getElementById("sharebtn").onclick=function(){
  if(!current)return;
  var verdict=current.flags.length===0?"looks chair-ready from the materials":
    "has "+current.flags.length+" flag"+(current.flags.length>1?"s":"")+": "+
    current.flags.map(function(f){return f.label.toLowerCase();}).join(", ");
  var text="The wheel-trouble check says "+current.t+" "+verdict+". Building a wheelchair costume this year? __CANON__?src=__SRC__";
  ph("wheelchair_shared",{which:"verdict",idea:current.id});
  if(navigator.share){navigator.share({text:text}).catch(function(){});}
  else if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).then(function(){alert("Copied. Paste it in the parent chat.");},function(){prompt("Copy this:",text);});}
  else{prompt("Copy this:",text);}
};
(function(){
  var m=/[?&]pick=([^&]+)/.exec(location.search);
  if(!m)return;
  var id;try{id=decodeURIComponent(m[1]);}catch(e){return;}
  if(INDEX_BY_ID[id]){pick(id);}
})();
var buildLinks=document.querySelectorAll("[data-build]");
for(var i=0;i<buildLinks.length;i++){
  (function(a){a.addEventListener("click",function(){ph("wheelchair_build_clicked",{slug:a.getAttribute("data-build")});});})(buildLinks[i]);
}
</script>
</body>
</html>
"""

def build_card(iid, idea, e, concept, note):
    return (
        '<div class="build">'
        '<h3>' + idea["title"] + ' &#9855;</h3>'
        '<p class="chairline">' + concept + '</p>'
        '<p class="blurb">' + idea["blurb"] + '</p>'
        '<div class="triple"><span>' + e["time"] + '</span><span>' + e["cost"] +
        '</span><span>' + e["effort"] + '</span></div>'
        '<p class="chairnote"><b>Chair build:</b>' + note + '</p>'
        '<div class="btns"><a class="btn primary" data-build="' + iid +
        '" href="/c/' + iid + '?src=' + SRC + '">Free build guide</a></div>'
        '</div>'
    )


def safety_card(title, text):
    return '<div class="rule"><b>' + title + '</b>' + text + '</div>'


def esc_html(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


FAQ_HTML = r"""<section class="pmc-faq" id="pmc-faq">
<style>
.pmc-faq{margin:32px 0}
.pmc-faq h2{font-size:22px;margin:0 0 8px}
.pmc-faq details{margin:8px 0;border:1px solid rgba(140,140,160,.4);border-radius:10px;padding:10px 14px}
.pmc-faq summary{cursor:pointer;font-weight:700}
.pmc-faq p{margin:8px 0 4px;line-height:1.55}
</style>
<h2>Common questions</h2>
<details class="faq">
<summary>Is this medical advice?</summary>
<p>No. These are craft notes for decorating a wheelchair as part of a costume, built from our own costume bank. They cannot know your child or their chair. When in doubt, ask the kid.</p>
</details>
<details class="faq">
<summary>Do I need to buy anything special for the chair builds?</summary>
<p>No. Every build note uses cardboard, tape or zip ties, and craft supplies. The costume itself comes from our free build guides.</p>
</details>
<details class="faq">
<summary>Will decorating damage the wheelchair?</summary>
<p>Use painter&#x27;s tape and zip ties, never hot glue or screws on the frame. Test any tape on a hidden spot first, and keep everything off the tires, spokes, brakes, and push handles.</p>
</details>
<details class="faq">
<summary>My kid only uses the chair part time. Do these still work?</summary>
<p>Yes. The chair builds are decorations on the chair for the hours it is in use, and every costume below also works fully on foot.</p>
</details>
</section>"""
# NOTE: FAQ_HTML must stay in sync with the FAQPage JSON-LD in TEMPLATE above.


def main():
    with open(BANK) as f:
        bank = json.load(f)
    ideas = bank["ideas"]
    ins = bank["instructions"]
    n = len(ideas)
    assert n == 164, "bank drift: %d ideas" % n
    ids = [i["id"] for i in ideas]
    assert len(set(ids)) == n, "duplicate ids"
    by_id = {i["id"]: i for i in ideas}

    # Validate the curated builds against the live bank.
    for iid, concept, note in BUILDS:
        assert iid in by_id, "build id not in bank: %s" % iid
        idea = by_id[iid]
        assert "kid" in idea.get("audience", []), "build not kid audience: %s" % iid
        e = ins.get(iid, {})
        for k in ("time", "cost", "effort"):
            assert e.get(k), "empty triple %s for %s" % (k, iid)
        assert not any(c in idea["title"] for c in DASHES)
        assert not any(c in idea["blurb"] for c in DASHES)
        assert not any(c in concept for c in DASHES), "dash in concept: %s" % iid
        assert not any(c in note for c in DASHES), "dash in note: %s" % iid

    builds_html = "\n".join(
        build_card(iid, by_id[iid], ins[iid], concept, note)
        for iid, concept, note in BUILDS)
    safety_html = "\n".join(safety_card(t, x) for t, x in SAFETY)
    assert len(SAFETY) == 4
    for t, x in SAFETY:
        assert not any(c in t + x for c in DASHES), "dash in safety"

    index = []
    for idea in sorted(ideas, key=lambda i: i["id"]):
        iid = idea["id"]
        e = ins.get(iid, {})
        flags = compute_flags(idea, e)
        index.append({
            "id": iid,
            "t": idea["title"],
            "b": idea["blurb"],
            "time": e.get("time", ""),
            "cost": e.get("cost", ""),
            "effort": e.get("effort", ""),
            "flags": [{"k": k, "label": l, "why": w, "fix": f}
                      for k, l, w, f in flags],
        })
    for e in index:
        assert e["time"] and e["cost"] and e["effort"], "empty triple: %s" % e["id"]
        for fl in e["flags"]:
            for k in ("label", "why", "fix"):
                assert not any(c in fl[k] for c in DASHES), \
                    "dash in flag: %s %s" % (e["id"], k)

    with open(FUZZY_JS, encoding="utf-8") as f:
        fuzzy_js = f.read()
    fuzzy_block = ("/*__FUZZY_TYPEAHEAD_BEGIN__*/\n" + fuzzy_js.strip("\n") +
                   "\n/*__FUZZY_TYPEAHEAD_END__*/")
    index_json = json.dumps(index, ensure_ascii=False, separators=(",", ":"))
    calm = sum(1 for e in index if not e["flags"])

    page = TEMPLATE
    page = page.replace("__BUILDS_HTML__", builds_html)
    page = page.replace("__SAFETY_HTML__", safety_html)
    page = page.replace("__INDEX_JSON__", index_json)
    page = page.replace("__CALM__", str(calm))
    page = page.replace("__N__", str(n))
    page = page.replace("__CANON__", CANON)
    page = page.replace("__OG__", OG)
    page = page.replace("__SRC__", SRC)
    page = page.replace("__FUZZY_TYPEAHEAD__", fuzzy_block)
    page = page.replace("__FAQ_HTML__", FAQ_HTML)

    for c in DASHES:
        assert c not in page, "dash lint failed"
    for ph in ("__BUILDS_HTML__", "__SAFETY_HTML__", "__INDEX_JSON__",
               "__CALM__", "__N__", "__CANON__", "__OG__", "__SRC__",
               "__FUZZY_TYPEAHEAD__", "__FAQ_HTML__"):
        assert ph not in page, "unsubstituted placeholder: %s" % ph

    if os.path.exists(OUT):
        with open(OUT) as f:
            old = f.read()
    else:
        old = None
    with open(OUT, "w") as f:
        f.write(page)
    if old is not None and old != page:
        print("note: output changed vs previous build")

    flagged = sum(1 for e in index if e["flags"])
    print("wheelchair-costumes.html built: %d ideas, %d flagged, %d zero-flag"
          % (len(index), flagged, len(index) - flagged))
    by = {}
    for e in index:
        for fl in e["flags"]:
            by[fl["k"]] = by.get(fl["k"], 0) + 1
    print("flag distribution:", dict(sorted(by.items(), key=lambda x: -x[1])))
    for e in index:
        if e["flags"]:
            print("  flagged:", e["id"], [f["k"] for f in e["flags"]])


if __name__ == "__main__":
    main()
