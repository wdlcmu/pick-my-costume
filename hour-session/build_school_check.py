#!/usr/bin/env python3
"""Build school-check.html: 'Will the school let them wear it?' dress-code checker.

Reads mcp-server/bank.json (source of truth), computes per-idea flags from real
bank data (mask mentions, weapon words, scary tag weight, face paint), and embeds
a deterministic JSON index into a self-contained page.

Staged code only. NO deploy. Not wired into nav or sitemap.

Repair note (2026-10-22, Family A slice 3): the == 138 asserts froze this
page when the bank grew to 169 on Oct 3; the count is now derived
(>= 100 floor + slug-set equality, the build_aisle_dupes.py pattern) and
template counts render from len(ideas). Displayed time is hands-on only
(display_time() strips any "+ ... drying" suffix; the live page already
shows stripped times), and the bank's removed cost field is no longer
emitted in the index (the live index already carries no cost key, and
the page JS never read it).
"""
import json, re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "mcp-server", "bank.json")
OUT = os.path.join(ROOT, "school-check.html")
FUZZY_JS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "fuzzy_typeahead.js")

# Cross-link pairing (2026-09-27): the classroom swap-rack starter kit.
# share-schoolcheck passes the site LANDING_SRC allowlist.
SWAP_KIT_URL = "https://pickmycostume.com/swap-rack-kit?src=share-schoolcheck"

DASHES = ("\u2013", "\u2014")

WEAPONS = re.compile(
    r"\b(swords?|knives?|daggers?|guns?|pistols?|bow and arrow|arrows?|axes?|"
    r"spears?|tridents?|nunchucks?|maces?|shurikens?|weapons?|lightsabers?)\b")
MASK = re.compile(r"\bmask(s|ed)?\b")
FACEPAINT = re.compile(r"\bface paint\b")

COPY_CHECKS = [
    ("weapon", "fake weapon", "Most schools ban weapons, even fake ones."),
    ("mask", "mask", "Most schools ask for no masks on campus."),
    ("scary2", "spooky", "Our bank tags this one spooky. Some schools ban scary costumes."),
    ("scary1", "a little spooky", "Fine at most schools, but check yours if they ban scary costumes."),
]

def display_time(t):
    # Displayed times are hands-on only: strip any "+ ... drying" suffix
    # (proven pattern from gen_costumes_hub.py / build_aisle_dupes.py).
    return re.sub(r"\s*\+.*drying\s*$", "", str(t))


def compute_flags(idea, ins):
    text = (" ".join(ins.get("m", [])) + " " + idea.get("blurb", "")).lower()
    # craft tools are not prop weapons; bow ties are not bows;
    # a face-paint "mask stripe" is not a mask
    for phrase in ("bow tie", "glue gun", "hot glue gun", "utility knife",
                   "mask stripe"):
        text = text.replace(phrase, phrase.replace(" ", ""))
    flags = []
    if WEAPONS.search(text):
        flags.append(("weapon", "Has a prop weapon",
                      "Most schools ban weapons, even fake ones."))
    if MASK.search(text):
        flags.append(("mask", "Includes a mask",
                      "Most schools ask for no masks on campus."))
    scary = idea.get("tags", {}).get("scary", 0)
    if scary >= 2:
        flags.append(("scary2", "Tagged spooky",
                      "Our bank tags this one spooky. Some schools ban scary costumes."))
    elif scary == 1:
        flags.append(("scary1", "A little spooky",
                      "Fine at most schools, but check yours if they ban scary costumes."))
    paint = bool(FACEPAINT.search(text)) and not MASK.search(text)
    return flags, paint

def main():
    # --out PATH: write to a scratch path instead of the real page
    # (sandbox pattern from the verify-lastcall/survive fix, 2026-10-22).
    # Default is unchanged: the real school-check.html.
    out_path = OUT
    if "--out" in sys.argv:
        out_path = sys.argv[sys.argv.index("--out") + 1]
    with open(BANK) as f:
        bank = json.load(f)
    ideas = bank["ideas"]
    ins = bank["instructions"]
    # Bank size is derived, never hard-coded: the == 138 asserts froze
    # this page when the bank grew to 169 on Oct 3. Non-vacuous floor +
    # slug-set equality, following the repaired build_aisle_dupes.py
    # pattern.
    assert len(ideas) >= 100, f"bank yielded only {len(ideas)} ideas"
    ids = [i["id"] for i in ideas]
    assert len(set(ids)) == len(ids), "duplicate ids"
    assert set(ins) == set(ids), "bank idea/instruction slug sets differ"

    index = []
    for idea in sorted(ideas, key=lambda i: i["id"]):
        iid = idea["id"]
        flags, paint = compute_flags(idea, ins.get(iid, {}))
        e = ins.get(iid, {})
        entry = {
            "id": iid,
            "t": idea["title"],
            "b": idea["blurb"],
            "time": display_time(e.get("time", "")),
            "effort": e.get("effort", ""),
            "flags": [{"k": k, "label": l, "why": w} for k, l, w in flags],
            "paint": paint,
        }
        index.append(entry)

    # shared fuzzy type-ahead, vendored byte-identical from fuzzy_typeahead.js
    with open(FUZZY_JS, encoding="utf-8") as f:
        fuzzy_js = f.read()
    fuzzy_block = ("/*__FUZZY_TYPEAHEAD_BEGIN__*/\n" + fuzzy_js.strip("\n") +
                   "\n/*__FUZZY_TYPEAHEAD_END__*/")
    index_json = json.dumps(index, ensure_ascii=False, separators=(",", ":"))
    calm = sum(1 for i in ideas if i.get("tags", {}).get("scary", 0) == 0)
    assert "__COUNT__" not in index_json, "count placeholder in bank data"
    page = (TEMPLATE.replace("__INDEX_JSON__", index_json)
                  .replace("__CALM__", str(calm))
                  .replace("__COUNT__", str(len(ideas)))
                  .replace("__SWAP_KIT_URL__", SWAP_KIT_URL)
                  .replace("__FUZZY_TYPEAHEAD__", fuzzy_block))
    assert "__COUNT__" not in page, "count placeholder not replaced"

    # lint: no em/en dashes in the staged copy or embedded data
    for c in DASHES:
        assert c not in page, f"dash lint failed: {c!r} in page"

    # determinism: rebuild must be byte-identical
    if os.path.exists(out_path):
        with open(out_path) as f:
            old = f.read()
    else:
        old = None
    with open(out_path, "w") as f:
        f.write(page)
    if old is not None and old != page:
        print("note: output changed vs previous build (expected on first run or bank change)")

    flagged = sum(1 for e in index if e["flags"])
    print(f"school-check.html built: {len(index)} ideas, {flagged} flagged, "
          f"{len(index)-flagged} school-safe by our tags")
    # distribution sanity print
    by = {}
    for e in index:
        for fl in e["flags"]:
            by[fl["k"]] = by.get(fl["k"], 0) + 1
    print("flag counts:", by)

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Will the School Let Them Wear It? | Pick My Costume</title>
<meta name="description" content="Pick a Halloween costume and check it against the stuff schools ban: masks, fake weapons, scary. Built from our __COUNT__-idea costume bank.">
<meta property="og:title" content="Will the School Let Them Wear It?">
<meta property="og:description" content="Check any of our __COUNT__ costumes against the usual school rules: masks, fake weapons, scary. Then ask the teacher.">
<meta property="og:image" content="https://pickmycostume.com/images/og/emoji-crew.jpg">
<meta property="og:url" content="https://pickmycostume.com/school-check">
<meta property="og:type" content="website">
<script>
/* PostHog: anonymous usage stats only. Quiz answers are never sent. Session replay is off. */
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
:root{--ink:#1c1a17;--muted:#6f6a61;--paper:#fffdf8;--card:#ffffff;--line:#e9e2d6;--green:#2e7d43;--greenbg:#e9f5ec;--amber:#9a6206;--amberbg:#fdf3e0;--cta:#d9481c}
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
#hits li.none{cursor:default;color:var(--muted);font-style:italic}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px;margin-top:20px;display:none}
.card.show{display:block}
.verdict{font-size:19px;font-weight:700;margin:0 0 4px}
.verdict.green{color:var(--green)}
.verdict.amber{color:var(--amber)}
.verdsub{color:var(--muted);font-size:14px;margin:0 0 12px}
.flag{border:1px solid var(--line);border-left:4px solid var(--amber);background:var(--amberbg);border-radius:8px;padding:10px 12px;margin:8px 0}
.flag b{display:block}
.flag span{color:var(--muted);font-size:14px}
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
.swapcard{margin-top:20px;border:1px solid var(--line);border-radius:12px;padding:16px;background:#fff}
.swapcard p{color:var(--muted);font-size:14px;margin:8px 0 12px}
footer{margin-top:40px;font-size:13px;color:#777;}</style>
</head>
<body>
<div class="wrap">
  <p class="sub"><a href="/" style="color:inherit">Pick My Costume</a></p>
  <h1>Will the school let them wear it?</h1>
  <p class="sub">Pick a costume. We check our bank's tags for the stuff schools usually ban: masks, fake weapons, scary. Your school's rule is still the boss.</p>
  <div class="searchbox">
    <input id="q" type="search" placeholder="Start typing a costume, like Little Baker" autocomplete="off" aria-label="Search costumes">
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
      <button class="btn share" id="sharebtn">Send to the class chat</button>
      <a class="btn ghost" id="quiz" href="/?src=share-schoolcheck">Find your kid's costume</a>
    </div>
  </div>
  <div class="disclaimer">
    <b>Honest fine print.</b> We cannot read your school's actual dress code. This check comes from our own __COUNT__-idea costume bank: its tags and materials lists. When in doubt, ask the teacher.
  </div>
  <div class="method">
    How we check: we scan the costume's materials and blurb for mask and prop-weapon words, and read the bank's own spooky tag. __CALM__ of __COUNT__ ideas carry no spooky tag at all.
  </div>
  <div class="swapcard">
    <b>Need a costume cheap? Start a classroom swap.</b>
    <p>Outgrown costumes are free costumes. The classroom swap-rack starter kit has a door sign, swap-day rules, a sign-up sheet, and tear-off slips, all printable.</p>
    <a class="btn ghost" href="__SWAP_KIT_URL__">Get the swap-rack kit</a>
  </div>
</div>
<script>
var INDEX = __INDEX_JSON__;
function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function ph(name,props){
  props=props||{};
  try{
    if(_isQA)props.internal=true;
  }catch(e){}
  try{if(window.posthog&&window.posthog.capture){window.posthog.capture(name,props);}}catch(e){}
}
var q=document.getElementById("q"),hits=document.getElementById("hits"),card=document.getElementById("card");
var current=null;
__FUZZY_TYPEAHEAD__
/* Search index for the shared module: {id, title, blurb} views over INDEX. */
var SEARCH_INDEX=INDEX.map(function(e){return{id:e.id,title:e.t,blurb:e.b};});
var INDEX_BY_ID={};INDEX.forEach(function(e){INDEX_BY_ID[e.id]=e;});
function doSearch(){
  hits.innerHTML="";hits.style.display="none";
  var found=FuzzyTypeAhead.search(q.value,SEARCH_INDEX);
  if(!found.length){
    if(String(q.value).replace(/\\s+/g,"").length>=2){
      var none=document.createElement("li");
      none.textContent="No costumes match. Try fewer words.";
      none.className="none";
      hits.appendChild(none);hits.style.display="block";
    }
    return;
  }
  if(found[0].tier===3){ph("schoolcheck_fuzzy",{});}
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
  if(e.flags.length){
    v.textContent="Worth asking the teacher about";v.className="verdict amber";
    vs.textContent="Our tags found "+e.flags.length+" thing"+(e.flags.length>1?"s":"")+" worth a second look against your school's rules.";
  }else{
    v.textContent="Looks school-safe by our tags";v.className="verdict green";
    vs.textContent="No masks, no fake weapons, and our bank does not tag it spooky.";
  }
  document.getElementById("ctitle").textContent=e.t;
  document.getElementById("cblurb").textContent=e.b;
  document.getElementById("triple").innerHTML=
    "<span>"+esc(e.time)+"</span><span>"+esc(e.effort)+"</span>";
  var fh="";
  e.flags.forEach(function(f){fh+='<div class="flag"><b>'+esc(f.label)+'</b><span>'+esc(f.why)+'</span></div>';});
  if(e.paint&&!e.flags.some(function(f){return f.k==="mask";})){fh+='<div class="clear">Uses face paint, not a mask. Most schools are fine with face paint.</div>';}
  if(!e.flags.length){fh+='<div class="clear">Checked: no mask words, no prop-weapon words, spooky tag is off.</div>';}
  document.getElementById("flags").innerHTML=fh;
  document.getElementById("guide").href="/c/"+e.id+"?src=share-schoolcheck";
  card.classList.add("show");
  ph("schoolcheck_viewed",{idea:e.id,flags:e.flags.length});
  if(history.replaceState){try{history.replaceState(null,"","/school-check?pick="+encodeURIComponent(e.id));}catch(err){}}
}
q.addEventListener("input",doSearch);
document.getElementById("sharebtn").onclick=function(){
  if(!current)return;
  /* 2026-09-27 loop measurement: mint an anonymous share id so the recipient
     leg is traceable. */
  var _scsid="", _abc="abcdefghijklmnopqrstuvwxyz0123456789";
  for(var _i=0;_i<8;_i++)_scsid+=_abc[Math.floor(Math.random()*_abc.length)];
  var verdict=current.flags.length?"needs a teacher check":"looks school-safe by our tags";
  var text="The school costume checker says "+current.t+" "+verdict+": "+
    (current.flags.length?current.flags.map(function(f){return f.label.toLowerCase();}).join("; "):"no masks, no fake weapons, not scary")+
    ". Check your kid's costume before the parade: https://pickmycostume.com/school-check?pick="+encodeURIComponent(current.id)+"&s="+_scsid+"&src=share-schoolcheck";
  ph("schoolcheck_shared",{idea:current.id,share_id:_scsid,share_origin:"schoolcheck"});
  if(navigator.share){navigator.share({text:text}).catch(function(){});}
  else if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).then(function(){alert("Copied. Paste it in the class chat.");},function(){prompt("Copy this:",text);});}
  else{prompt("Copy this:",text);}
};
(function(){
  var m=/[?&]pick=([^&]+)/.exec(location.search);
  if(!m)return;
  var id;try{id=decodeURIComponent(m[1]);}catch(e){return;}
  var e=null;for(var i=0;i<INDEX.length;i++){if(INDEX[i].id===id){e=INDEX[i];break;}}
  if(e){pick(e.id);}
  /* 2026-09-27 loop measurement: recipient leg. Stamp via_share_id from ?s=
     so the open traces back to the sender's schoolcheck_shared.share_id. */
  var vsm=/[?&]s=([a-z0-9]{8,})/.exec(location.search||"");
  if(vsm)ph("schoolcheck_opened",{idea:id,via_share_id:vsm[1],share_origin:"schoolcheck"});
})();
</script>
<footer>Built with Muse.</footer></body>
</html>
"""

if __name__ == "__main__":
    main()
