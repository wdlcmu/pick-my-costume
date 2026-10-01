#!/usr/bin/env python3
"""Build sensory-check.html: 'Is this costume sensory-friendly?'

Reads mcp-server/bank.json (source of truth), computes per-idea sensory flags
from real bank data (materials lists + blurbs), and embeds a deterministic
JSON index into a self-contained page.

Flag families: face coverings (mask, face paint, beard, mustache, goggles),
head pressure (wig, helmet, crown), itch (tights, tulle, sequins, fur,
feathers), noise (whistle), drape/tangle (cape, wings).

Staged code only. NO deploy. Not wired into nav or sitemap.
"""
import json, re, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "mcp-server", "bank.json")
OUT = os.path.join(ROOT, "sensory-check.html")
FUZZY_JS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "fuzzy_typeahead.js")

DASHES = ("\u2013", "\u2014")

# Sanitize phrases that look like flags but are not.
SANITIZE = [
    ("fabric paint", "fabricpaint"),   # neon fabric paint on clothes, not face
    ("mask stripe", "maskstripe"),     # a face-paint stripe, not a mask
    ("drawn mustache", "drawnmustache"),
    ("drawn mustaches", "drawnmustaches"),
    ("for the beard", "forthebeard"),       # painted-on beard, not glue-on
    ("for mustache", "formustache"),         # painted-on mustache, not fake
    ("for mustaches", "formustaches"),
]

# (key, regex, label, why, fix)
FLAGS = [
    ("mask", r"\bmask(s|ed)?\b", "Includes a mask",
     "Masks block vision and breathing space, and the strap presses behind the ears.",
     "Make the eye holes bigger first. If the mask still bugs them, the costume works without it."),
    ("facepaint", r"\bface paint\b", "Uses face paint",
     "Face paint feels sticky and weird to a lot of kids, and it does not wash off fast.",
     "Test a dot on the arm an hour before. If they hate the feeling, skip it; the costume still reads."),
    ("beard", r"\bbeard\b", "Glue-on or stick-on beard",
     "Stick-on beards itch and peel, and the spirit-gum smell bothers some kids.",
     "A drawn-on beard line in face paint keeps the look with none of the itch."),
    ("mustache", r"\b(moustaches?|mustaches?)\b", "Fake mustache",
     "Fake mustaches tickle the upper lip and fall off by 7pm.",
     "A drawn mustache line works better, or skip it entirely."),
    ("goggles", r"\bgoggles?\b", "Goggles",
     "Goggles press tight around the eyes and fog up fast.",
     "Let them wear the rest of the costume without the goggles."),
    ("wig", r"\bwigs?\b", "Wig",
     "Wigs itch, slip, and trap heat.",
     "A colored hair spray or a styled headband is kinder than a full wig."),
    ("helmet", r"\bhelmets?\b", "Toy helmet",
     "Helmets run hot and sound loud inside, and the strap digs under the chin.",
     "A cap keeps the look without the weight. Five minutes at home first, no matter what."),
    ("crown", r"\bcrowns?\b", "Crown",
     "Crown points dig into the scalp, and bobby pins on little kids are miserable.",
     "Tape the crown to a headband instead of pinning it in."),
    ("tights", r"\btights\b", "Tights",
     "Tights itch and ride down, and they snag on everything.",
     "Bare legs or leggings underneath instead."),
    ("tulle", r"\btulle\b", "Tulle",
     "Tulle is the scratchiest fabric in the craft drawer.",
     "One soft layer underneath fixes most complaints."),
    ("sequin", r"\bsequins?\b", "Sequins",
     "Sequins scratch bare skin and snag on coats.",
     "Keep them on the outside layer, off the skin."),
    ("fur", r"\b(faux fur|fur)\b", "Faux fur",
     "Faux fur runs hot and itches where it touches skin.",
     "Limit it to a trim instead of the whole suit."),
    ("feather", r"\bfeathers?\b", "Feathers",
     "Feathers tickle, shed, and end up in the mouth.",
     "Skip them if touch is the issue."),
    ("whistle", r"\bwhistles?\b", "Whistle",
     "The whistle is the funnest part for ten minutes and the worst part for two hours.",
     "The whistle is a prop, not the costume. Parent pockets it after photos."),
    ("cape", r"\bcapes?\b", "Cape",
     "Capes drag, snag on fences, and get stepped on from behind.",
     "A shorter cape, or one pinned back over the shoulders, fixes it."),
    ("wings", r"\bwings?\b", "Wings",
     "Wings catch on doorframes, car seats, and siblings.",
     "Snap-on wings that come off indoors survive the night."),
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
<title>Is This Costume Sensory-Friendly? | Pick My Costume</title>
<meta name="description" content="Pick a Halloween costume and check it for the stuff that bugs sensory-sensitive kids: face paint, masks, itchy fabric, noise. Built from our 138-idea costume bank.">
<meta property="og:title" content="Is This Costume Sensory-Friendly?">
<meta property="og:description" content="Check any of our 138 costumes against the usual sensory irritants: face paint, masks, itchy fabric, whistles. With one-line fixes.">
<meta property="og:image" content="https://pickmycostume.com/images/og/emoji-crew.jpg">
<meta property="og:type" content="website">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
{"@type":"Question","name":"What does the sensory check look for?","acceptedAnswer":{"@type":"Answer","text":"We scan each costume's materials list for face coverings, head pressure, itchy fabric, noise, and drape, and list everything we find with a one-line fix."}},
{"@type":"Question","name":"Is this medical advice?","acceptedAnswer":{"@type":"Answer","text":"No. This checks our own costume bank's materials lists. It cannot know your child. When in doubt, ask the kid."}},
{"@type":"Question","name":"My kid's costume got flagged. Now what?","acceptedAnswer":{"@type":"Answer","text":"Each flag carries a one-line fix that keeps the costume. Or take the 2-minute quiz to find a calmer pick."}}]}
</script>
<style>
:root{--ink:#1c1a17;--muted:#6f6a61;--paper:#fffdf8;--card:#ffffff;--line:#e9e2d6;--green:#2e7d43;--greenbg:#e9f5ec;--amber:#9a6206;--amberbg:#fdf3e0;--red:#b3261e;--redbg:#fbeae8;--cta:#d9481c}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:640px;margin:0 auto;padding:20px 16px 64px}
h1{font-size:28px;line-height:1.2;margin:8px 0}
.sub{color:var(--muted);margin:0 0 20px}
.searchbox{position:relative}
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
.triple{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
.triple span{background:#f4efe4;border-radius:999px;padding:4px 12px;font-size:13px}
.blurb{color:var(--muted);font-size:15px;margin:8px 0 0}
.btns{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}
a.btn,button.btn{font-size:16px;padding:12px 18px;border-radius:12px;border:none;cursor:pointer;text-decoration:none;display:inline-block}
a.btn.primary{background:var(--cta);color:#fff}
button.btn.share{background:#1c1a17;color:#fff}
a.btn.ghost{background:#fff;border:1px solid var(--line);color:var(--ink)}
.method{margin-top:28px;font-size:13px;color:var(--muted);border-top:1px solid var(--line);padding-top:16px}
.disclaimer{background:#f7f3ea;border-radius:12px;padding:14px;margin-top:16px;font-size:14px}
</style>
</head>
<body>
<div class="wrap">
  <p class="sub"><a href="/" style="color:inherit">Pick My Costume</a></p>
  <h1>Is this costume sensory-friendly?</h1>
  <p class="sub">Pick a costume. We check our bank's materials for the stuff that bugs sensory-sensitive kids: face paint, masks, itchy fabric, noise. Every kid is different; this is the starting point, not the verdict.</p>
  <div class="searchbox">
    <input id="q" type="search" placeholder="Start typing a costume, like Glow Skeleton" autocomplete="off" aria-label="Search costumes">
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
      <a class="btn ghost" id="quiz" href="/?src=share-sensory">Find a calmer costume</a>
    </div>
  </div>
  <div class="disclaimer">
    <b>Honest fine print.</b> This check scans our own 138-idea costume bank: its materials lists and blurbs. It is not medical advice, and it cannot know your child. When in doubt, ask the kid.
  </div>
  <div class="method">
    How we check: we scan the costume's materials and blurb for face coverings, head pressure, itch, noise, and drape words, and list everything we find with a one-line fix. __CALM__ of 164 ideas carry zero flags.
  </div>
</div>
__FAQ_HTML__
<script>
var INDEX = __INDEX_JSON__;
function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function ph(name,props){props=props||{};try{var q=location.search;if(/[?&](probe|sim)=/.test(q)||/[?&]internal=1/.test(q))props.internal=true;if(window.posthog&&window.posthog.capture){window.posthog.capture(name,props);}}catch(e){}}
var q=document.getElementById("q"),hits=document.getElementById("hits"),card=document.getElementById("card");
var current=null;
__FUZZY_TYPEAHEAD__
/* Search index for the shared module: {id, title, blurb} views over INDEX. */
var SEARCH_INDEX=INDEX.map(function(e){return{id:e.id,title:e.t,blurb:e.b};});
var INDEX_BY_ID={};INDEX.forEach(function(e){INDEX_BY_ID[e.id]=e;});
function doSearch(){
  hits.innerHTML="";hits.style.display="none";
  var found=FuzzyTypeAhead.search(q.value,SEARCH_INDEX);
  if(!found.length)return;
  if(found[0].tier===3){ph("sensory_fuzzy",{});}
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
  var e=null;for(var i=0;i<INDEX.length;i++){if(INDEX[i].id===id){e=INDEX[i];break;}}
  if(!e)return;current=e;
  hits.style.display="none";q.value=e.t;
  var v=document.getElementById("verdict"),vs=document.getElementById("verdsub");
  if(e.flags.length===0){
    v.textContent="Looks sensory-friendly from the materials";v.className="verdict green";
    vs.textContent="No face coverings, head pressure, itch, noise, or drape in the materials list.";
  }else if(e.flags.length===1){
    v.textContent="One flag to work around";v.className="verdict amber";
    vs.textContent="One thing in the materials might bug a sensory-sensitive kid. The fix is below.";
  }else{
    v.textContent="Worth a second look";v.className="verdict red";
    vs.textContent=e.flags.length+" things in the materials might bug a sensory-sensitive kid. Fixes below, or find a calmer pick with the quiz.";
  }
  document.getElementById("ctitle").textContent=e.t;
  document.getElementById("cblurb").textContent=e.b;
  document.getElementById("triple").innerHTML=
    "<span>"+esc(e.time)+"</span><span>"+esc(e.cost)+"</span><span>"+esc(e.effort)+"</span>";
  var fh="";
  e.flags.forEach(function(f){fh+='<div class="flag"><b>'+esc(f.label)+'</b><span>'+esc(f.why)+'</span><span class="fix">Fix: '+esc(f.fix)+'</span></div>';});
  if(e.flags.length===0){fh+='<div class="clear">Checked: no mask, face paint, beard, goggles, wig, helmet, crown, itchy fabric, whistle, cape, or wings words in the materials.</div>';}
  document.getElementById("flags").innerHTML=fh;
  document.getElementById("guide").href="/c/"+e.id+"?src=share-sensory";
  card.classList.add("show");
  ph("sensory_viewed",{idea:e.id,flags:e.flags.length});
  if(history.replaceState){try{history.replaceState(null,"","/sensory-check?pick="+encodeURIComponent(e.id));}catch(err){}}
}
q.addEventListener("input",doSearch);
document.getElementById("sharebtn").onclick=function(){
  if(!current)return;
  var verdict=current.flags.length===0?"looks sensory-friendly from the materials":
    "has "+current.flags.length+" flag"+(current.flags.length>1?"s":"")+": "+
    current.flags.map(function(f){return f.label.toLowerCase();}).join(", ");
  var text="The sensory check says "+current.t+" "+verdict+". Will your kid's costume survive Halloween night? https://pickmycostume.com/sensory-check?src=share-sensory";
  ph("sensory_shared",{idea:current.id});
  if(navigator.share){navigator.share({text:text}).catch(function(){});}
  else if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).then(function(){alert("Copied. Paste it in the parent chat.");},function(){prompt("Copy this:",text);});}
  else{prompt("Copy this:",text);}
};
(function(){
  var m=/[?&]pick=([^&]+)/.exec(location.search);
  if(!m)return;
  var id;try{id=decodeURIComponent(m[1]);}catch(e){return;}
  var e=null;for(var i=0;i<INDEX.length;i++){if(INDEX[i].id===id){e=INDEX[i];break;}}
  if(e){pick(e.id);}
})();
</script>
</body>
</html>
"""


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
<summary>What does the sensory check look for?</summary>
<p>We scan each costume&#x27;s materials list for face coverings, head pressure, itchy fabric, noise, and drape, and list everything we find with a one-line fix.</p>
</details>
<details class="faq">
<summary>Is this medical advice?</summary>
<p>No. This checks our own costume bank&#x27;s materials lists. It cannot know your child. When in doubt, ask the kid.</p>
</details>
<details class="faq">
<summary>My kid&#x27;s costume got flagged. Now what?</summary>
<p>Each flag carries a one-line fix that keeps the costume. Or take the 2-minute quiz to find a calmer pick.</p>
</details>
</section>"""
# NOTE: FAQ_HTML must stay in sync with the FAQPage JSON-LD in TEMPLATE above.


def main():
    with open(BANK) as f:
        bank = json.load(f)
    ideas = bank["ideas"]
    ins = bank["instructions"]
    assert len(ideas) == 138, "bank drift: %d ideas" % len(ideas)
    ids = [i["id"] for i in ideas]
    assert len(set(ids)) == 138, "duplicate ids"

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

    with open(FUZZY_JS, encoding="utf-8") as f:
        fuzzy_js = f.read()
    fuzzy_block = ("/*__FUZZY_TYPEAHEAD_BEGIN__*/\n" + fuzzy_js.strip("\n") +
                   "\n/*__FUZZY_TYPEAHEAD_END__*/")
    index_json = json.dumps(index, ensure_ascii=False, separators=(",", ":"))
    calm = sum(1 for e in index if not e["flags"])
    page = (TEMPLATE.replace("__INDEX_JSON__", index_json)
                    .replace("__CALM__", str(calm))
                    .replace("__FUZZY_TYPEAHEAD__", fuzzy_block)
                    .replace("__FAQ_HTML__", FAQ_HTML))

    for c in DASHES:
        assert c not in page, "dash lint failed: %r in page" % c

    # every flag string must also be dash-free at the source level
    for e in index:
        for fl in e["flags"]:
            for k in ("label", "why", "fix"):
                assert not any(c in fl[k] for c in DASHES), "dash in flag: %s %s" % (e["id"], k)

    if os.path.exists(OUT):
        with open(OUT) as f:
            old = f.read()
    else:
        old = None
    with open(OUT, "w") as f:
        f.write(page)
    if old is not None and old != page:
        print("note: output changed vs previous build (expected on first run or bank change)")

    flagged = sum(1 for e in index if e["flags"])
    print("sensory-check.html built: %d ideas, %d flagged, %d zero-flag"
          % (len(index), flagged, len(index) - flagged))
    by = {}
    for e in index:
        for fl in e["flags"]:
            by[fl["k"]] = by.get(fl["k"], 0) + 1
    print("flag distribution:", dict(sorted(by.items(), key=lambda x: -x[1])))


if __name__ == "__main__":
    main()
