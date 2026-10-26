#!/usr/bin/env python3
"""Generate porch-sign.html: The Porch Sign photo-prop generator.

The first-day-of-school sign is the most posted parent photo genre of the
fall. This is its Halloween twin: a printable sign the kid holds in the
annual porch photo.

  HALLOWEEN 2026
  [Maya is going as / I am going as]
  [photo]
  EMERALD WITCH
  Picked in 2 minutes at pickmycostume.com. Take the quiz, print your sign.

The parent posts the photo to their own feed. Every friend who sees the photo
sees the URL. Zero permission needed, zero performance, zero print cost
beyond one sheet of paper.

Byte-inert until the main agent links it: no inbound links, noindex, not in
sitemap.xml. Attribution: ?src=share-porchsign (accepted by the live
LANDING_SRC allowlist regex in index.html).
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
bank = json.load(open(os.path.join(ROOT, "mcp-server", "bank.json")))
ideas = bank["ideas"]
# Bank size is derived, never hard-coded: the == 138 assert froze this page
# when the bank grew to 169 on Oct 3. Non-vacuous floor + uniqueness below,
# following the repaired build_aisle_dupes.py pattern.
assert len(ideas) >= 100, f"bank yielded only {len(ideas)} ideas"

compact = []
for i in ideas:
    photo = os.path.join(ROOT, "photos", i["id"] + ".webp")
    assert os.path.exists(photo), f"missing photo for {i['id']}"
    assert i["title"] and i["title"] == i["title"].strip(), f"bad title for {i['id']}"
    compact.append({"id": i["id"], "t": i["title"]})
ids = [c["id"] for c in compact]
assert len(set(ids)) == len(ideas), "duplicate bank ids"
compact.sort(key=lambda e: e["t"].lower())
bank_json = json.dumps(compact, ensure_ascii=False, separators=(",", ":"))

TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Porch Sign: a free printable Halloween photo prop | Pick My Costume</title>
<meta name="description" content="Print a Halloween 2026 porch sign: your kid's name, their costume, one sheet of paper. The first-day-of-school sign, but for Halloween.">
<meta name="robots" content="noindex">
<link rel="canonical" href="https://pickmycostume.com/porch-sign">
<meta property="og:title" content="The Porch Sign">
<meta property="og:description" content="A free printable Halloween photo prop: your kid, their costume, one sign.">
<meta property="og:image" content="https://pickmycostume.com/images/og/emoji-crew.jpg">
<meta property="og:type" content="website">
<script>
/* PostHog: anonymous usage stats only. No names are sent. Session replay is off. */
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
<style>
:root{--ink:#1c1a17;--muted:#6f6a61;--paper:#fffdf8;--line:#e9e2d6;--cta:#d9481c;--accent:#ff8c1a}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:700px;margin:0 auto;padding:20px 16px 64px}
.sub{color:var(--muted);margin:0 0 20px}
h1{font-size:28px;line-height:1.2;margin:8px 0}
.steps{counter-reset:st;margin:20px 0;padding:0;list-style:none}
.steps li{display:flex;gap:12px;margin:0 0 18px;align-items:flex-start}
.steps .n{counter-increment:st;flex:0 0 auto;width:32px;height:32px;border-radius:50%;background:var(--ink);color:#fff;font-weight:700;display:flex;align-items:center;justify-content:center}
.steps .n::before{content:counter(st)}
label.lbl{display:block;font-weight:700;margin:18px 0 6px}
input[type=text]{width:100%;font-size:17px;padding:14px 16px;border:2px solid var(--line);border-radius:12px;background:#fff}
input[type=text]:focus{outline:none;border-color:var(--cta)}
.searchbox{position:relative}
#q{width:100%;font-size:17px;padding:14px 16px;border:2px solid var(--line);border-radius:12px;background:#fff}
#q:focus{outline:none;border-color:var(--cta)}
#hits{position:absolute;left:0;right:0;top:100%;z-index:20;background:#fff;border:2px solid var(--line);border-top:none;border-radius:0 0 12px 12px;max-height:280px;overflow:auto;display:none}
#hits.show{display:block}
#hits button{display:flex;width:100%;text-align:left;gap:10px;align-items:center;padding:12px 14px;border:0;background:#fff;font-size:16px;cursor:pointer}
#hits button:hover{background:#faf6ee}
#hits img{width:44px;height:44px;object-fit:cover;border-radius:8px;flex:0 0 auto}
#hits .t{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#arrive{display:none;background:#faf6ee;border:2px dashed var(--line);border-radius:12px;padding:12px 16px;margin:0 0 20px;font-size:15px}
#arrive.show{display:block}
#signwrap{margin:28px 0}
#sign{background:#fff;border:6px solid var(--ink);border-radius:18px;padding:36px 28px 28px;text-align:center;box-shadow:0 8px 28px rgba(28,26,23,.12)}
#sign .yr{font-weight:800;letter-spacing:.35em;font-size:20px;color:var(--cta)}
#sign .kid{font-weight:700;font-size:22px;margin:14px 0 4px;text-transform:uppercase;letter-spacing:.06em}
#sign .photo{width:min(72%,320px);aspect-ratio:4/5;object-fit:cover;border-radius:14px;margin:18px auto;display:block;border:3px solid var(--line)}
#sign .costume{font-weight:800;font-size:34px;line-height:1.15;margin:10px 0 6px}
#sign .foot{margin-top:18px;padding-top:14px;border-top:2px solid var(--line);font-size:15px;color:var(--muted)}
#sign .foot b{color:var(--ink)}
#signempty{border:3px dashed var(--line);border-radius:18px;padding:40px 24px;text-align:center;color:var(--muted)}
.actions{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0}
.actions button{flex:1 1 180px;font-size:17px;font-weight:700;padding:14px 18px;border-radius:12px;border:2px solid var(--ink);background:#fff;cursor:pointer}
.actions button.primary{background:var(--cta);border-color:var(--cta);color:#fff}
.quizcta{margin-top:26px;font-size:17px}
.quizcta a{color:var(--cta);font-weight:700}
.fine{color:var(--muted);font-size:13px;margin-top:28px}
@media print{
  .no-print{display:none !important}
  body{background:#fff}
  .wrap{max-width:none;padding:0;margin:0}
  #signwrap{margin:0}
  #sign{box-shadow:none;border-radius:0;border-width:5px;min-height:95vh;display:flex;flex-direction:column;justify-content:center}
}
footer{margin-top:40px;font-size:13px;color:#777;}</style>
</head>
<body>
<div class="wrap">
  <div class="no-print">
    <h1>The Porch Sign</h1>
    <p class="sub">The first-day-of-school sign, but for Halloween. Pick the costume, add your kid's first name if you like, print one sheet, and let them hold it in the porch photo. Every friend who sees the photo sees where the costume came from.</p>
    <div id="arrive"></div>
    <ol class="steps">
      <li><span class="n"></span><div style="flex:1">
        <label class="lbl" for="q">Pick the costume</label>
        <div class="searchbox">
          <input type="text" id="q" placeholder="Start typing, like witch or robot" autocomplete="off">
          <div id="hits"></div>
        </div>
      </div></li>
      <li><span class="n"></span><div style="flex:1">
        <label class="lbl" for="kid">Kid's first name <span style="font-weight:400;color:var(--muted)">(optional, stays on this page)</span></label>
        <input type="text" id="kid" placeholder="Maya" maxlength="24" autocomplete="off">
      </div></li>
    </ol>
  </div>
  <div id="signwrap">
    <div id="signempty">Your sign appears here once you pick a costume above.</div>
    <div id="sign" style="display:none">
      <div class="yr">HALLOWEEN 2026</div>
      <div class="kid" id="signkid">I AM GOING AS</div>
      <img class="photo" id="signphoto" alt="">
      <div class="costume" id="signtitle"></div>
      <div class="foot">Picked in 2 minutes at <b>pickmycostume.com</b>.<br>Take the quiz, print your sign.</div>
    </div>
  </div>
  <div class="actions no-print">
    <button class="primary" id="printbtn" type="button">Print the sign</button>
    <button id="linkbtn" type="button">Copy sign link</button>
    <button id="capbtn" type="button">Copy feed caption</button>
  </div>
  <p class="quizcta no-print">Still deciding? <a id="quizlink" href="https://pickmycostume.com/?src=share-porchsign">Take the 2-minute quiz</a> and come back with your pick.</p>
  <p class="fine no-print">The name you type never leaves this page except inside the link or caption you choose to copy. __COUNT__ costume ideas, free, no signup.</p>
</div>
<script>
var BANK = __BANK_JSON__;
var BY_ID = {};
(function(){ for (var i = 0; i < BANK.length; i++) BY_ID[BANK[i].id] = BANK[i]; })();
function photoUrl(id){ return "photos/" + id + ".webp"; }

/* ---------- guards ---------- */
function tapGuard(btn, fn, ms){
  var locked = false;
  btn.addEventListener("click", function(){
    if (locked) return;
    locked = true;
    try { fn(); } finally {
      setTimeout(function(){ locked = false; }, ms || 700);
    }
  });
}

/* ---------- name + copy ---------- */
function cleanKid(raw){
  var k = String(raw || "").replace(/<[^>]*>/g, "").replace(/[^A-Za-z '\-]/g, "").slice(0, 20).trim();
  return k;
}
function kidLine(raw){
  var k = cleanKid(raw);
  return k ? (k.toUpperCase() + " IS GOING AS") : "I AM GOING AS";
}
function signUrl(pick, name){
  var u = "https://pickmycostume.com/porch-sign?pick=" + encodeURIComponent(pick.id);
  var k = cleanKid(name);
  if (k) u += "&name=" + encodeURIComponent(k);
  u += "&src=share-porchsign";
  return u;
}
function buildCaption(pickTitle, name){
  var k = cleanKid(name);
  var who = k ? (k + " is going as " + pickTitle + " for Halloween 2026.")
              : ("Our Halloween 2026 costume is " + pickTitle + ".");
  return who + " We picked it in 2 minutes at pickmycostume.com. Print your kid's own porch sign there. Free, no signup.";
}

/* ---------- picker ---------- */
var pick = null;
var q = document.getElementById("q"), hits = document.getElementById("hits");
function renderHits(list){
  hits.innerHTML = "";
  if (!list.length){ hits.classList.remove("show"); return; }
  list.slice(0, 8).forEach(function(e){
    var b = document.createElement("button");
    b.type = "button";
    var im = document.createElement("img");
    im.src = photoUrl(e.id); im.alt = "";
    var sp = document.createElement("span");
    sp.className = "t"; sp.textContent = e.t;
    b.appendChild(im); b.appendChild(sp);
    b.addEventListener("click", function(){ setPick(e.id); });
    hits.appendChild(b);
  });
  hits.classList.add("show");
}
q.addEventListener("input", function(){
  var v = q.value.trim().toLowerCase();
  if (v.length < 2){ renderHits([]); return; }
  var list = BANK.filter(function(e){ return e.t.toLowerCase().indexOf(v) !== -1; });
  renderHits(list);
});
document.addEventListener("click", function(ev){
  if (!hits.contains(ev.target) && ev.target !== q) hits.classList.remove("show");
});

function renderSign(){
  var empty = document.getElementById("signempty"), sign = document.getElementById("sign");
  if (!pick){ empty.style.display = ""; sign.style.display = "none"; return; }
  empty.style.display = "none"; sign.style.display = "";
  document.getElementById("signkid").textContent = kidLine(document.getElementById("kid").value);
  var img = document.getElementById("signphoto");
  img.src = photoUrl(pick.id); img.alt = pick.t + " costume";
  document.getElementById("signtitle").textContent = pick.t;
}
function setPick(id){
  if (!BY_ID[id]) return;
  pick = BY_ID[id];
  q.value = pick.t;
  renderHits([]);
  renderSign();
  ph("porch_sign_viewed", {pick: pick.id, named: cleanKid(document.getElementById("kid").value) ? 1 : 0});
}
document.getElementById("kid").addEventListener("input", renderSign);

/* ---------- actions ---------- */
tapGuard(document.getElementById("printbtn"), function(){
  if (!pick){ alert("Pick a costume first, then print the sign."); return; }
  window.print();
}, 800);
window.addEventListener("beforeprint", function(){
  if (pick) ph("porch_sign_printed", {pick: pick.id});
});
function copyText(text, evtName){
  function done(){ ph(evtName, pick ? {pick: pick.id} : {}); }
  if (navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(text).then(function(){ done(); alert("Copied. Paste it wherever you like."); }, function(){ prompt("Copy this:", text); });
  } else { prompt("Copy this:", text); }
}
tapGuard(document.getElementById("linkbtn"), function(){
  if (!pick){ alert("Pick a costume first, then copy the link."); return; }
  copyText(signUrl(pick, document.getElementById("kid").value), "porch_sign_link_copied");
}, 600);
tapGuard(document.getElementById("capbtn"), function(){
  if (!pick){ alert("Pick a costume first, then copy the caption."); return; }
  copyText(buildCaption(pick.t, document.getElementById("kid").value), "porch_sign_caption_copied");
}, 600);

/* ---------- deep link: /porch-sign?pick=<id>&name=<name> ---------- */
(function(){
  function qp(n){ var m = new RegExp("[?&]" + n + "=([^&]*)").exec(location.search); return m ? decodeURIComponent(m[1]) : ""; }
  var p = qp("pick"), k = cleanKid(qp("name"));
  if (p && BY_ID[p]) pick = BY_ID[p];
  if (k) document.getElementById("kid").value = k;
  if (pick){
    q.value = pick.t;
    renderSign();
    var arr = document.getElementById("arrive");
    arr.textContent = (k ? (k + " is going as " + pick.t + ".") : ("Somebody is going as " + pick.t + ".")) + " Print your own sign below.";
    arr.classList.add("show");
    ph("porch_sign_viewed", {pick: pick.id, named: k ? 1 : 0, recipient: 1});
  }
})();
</script>
<footer class="no-print">Built with Muse.</footer></body>
</html>
'''

html = TEMPLATE.replace("__BANK_JSON__", bank_json).replace("__COUNT__", str(len(ideas)))
assert "__COUNT__" not in html, "count placeholder not replaced"

# fail loudly on drift / honesty / lint
assert html.count("__BANK_JSON__") == 0, "bank placeholder not replaced"
for bad in ("\u2013", "\u2014"):
    assert bad not in html, f"em/en dash leaked into page: {bad!r}"
for slug in ("neon-demon-hunter", "emerald-witch", "glow-skeleton"):
    assert slug in html, f"expected bank id missing: {slug}"
# the page must not link to itself as a path anywhere (byte-inert)
assert html.count('href="/porch-sign"') == 0, "self link leaked"

out_path = os.path.join(ROOT, "porch-sign.html")
# --out PATH: write to a scratch path instead of the real page
# (sandbox pattern from the verify-lastcall/survive fix, 2026-10-22).
# Default is unchanged: the real porch-sign.html.
if "--out" in sys.argv:
    out_path = sys.argv[sys.argv.index("--out") + 1]
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", out_path, len(html), "bytes,", len(compact), "bank entries")
