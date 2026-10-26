#!/usr/bin/env python3
"""Build reluctant-dresser.html: "Costumes for People Who Hate Costumes".

2026-09-27 (new-ideas stream pm3). The winner: The Reluctant Dresser.

What it is: a staged, self-contained page at repo root. 12 Easy-effort,
10-25 minute costumes from the idea bank, each chosen because the joke
IS the costume (Error 404, Lost Tourist, Boxer in a bathrobe...). The
distribution loop is a FORWARD: "Send this to the person who says 'I'm not
dressing up.'" The sender types a name; each card gets a personalized share
text, a copy button, and a QR to the /c/ build guide. This opens a new
arrival channel nobody else covers: the unwilling partner / teen / friend,
delivered by someone who knows them.

Why it wins: every other share surface assumes the sharer is excited. This
one is for the person the sharer has to DRAG to Halloween, and the gag
(costume not found, a tourist, a bathrobe) is the permission structure.
Bank-grounded, honest by construction: time / effort are the bank's
pair (displayed time is hands-on only: display_time() strips any
"+ ... drying" suffix, per Billy's Oct 1 rule; the live page already
shows stripped times), and the share text never invents a number.

Honesty contract (fails loudly):
- bank holds >= 100 ideas (derived count, never hard-coded), unique ids,
  idea/instruction slug sets equal, the 12 slugs each have instructions
  with the full time/effort pair, never recomputed
- no em/en dashes in any user-facing string (Billy's standing rule)
- no </script inside data payloads
- deterministic share ids (sha1 of slug, first 8 chars): re-running the
  script produces byte-identical output
- page is noindex, not in the sitemap, no inbound links from root pages
  (byte-inert in the shared tree: only this script and its one output file)

Attribution: quiz links carry ?s=<8char>&src=share-reluctant; guide links
carry ?src=share-reluctant. Both are inside the standing LANDING_SRC
allowlist in index.html (share-[a-z-]+).

2026-10-22 reconciliation: the live page's hand edits were ported back
into this generator (live -> generator): de-costed meta / og / sub /
footer copy and the Timed share segment now match live byte for byte,
so a regen differs from live only on bank refresh.

Usage: python3 build_reluctant_dresser.py   (writes ../reluctant-dresser.html)
"""

import hashlib
import string
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BANK = os.path.join(ROOT, "mcp-server", "bank.json")
OUT = os.path.join(ROOT, "reluctant-dresser.html")
QR_LIB = os.path.join(ROOT, "vendor", "qrcode-generator", "qrcode.js")

DASH_RE = re.compile(r"[\u2013\u2014]")

# slug -> the reluctant-dresser one-liner (plain English, no dashes)
CARDS = [
    ("error-404", "Your costume is literally 'costume not found'. The refusal is the costume."),
    ("lost-tourist", "Wear the wrinkliest thing you own and carry a map. Nobody questions it."),
    ("boxer", "Bathrobe, toy gloves, entrance music. You were already 90 percent there."),
    ("office-couple", "White shirt, name tag, done. You go as what you already are."),
    ("banana", "A yellow sweatsuit and a green hat. Comfortable. Zero dignity required."),
    ("classic-ghost", "The oldest costume in history: a sheet with eye holes. Ten minutes, tops."),
    ("zombie-coworker", "Torn shirt, loose tie, coffee mug. Your Monday morning look, weaponized."),
    ("referee", "Striped shirt and a whistle. Blow it at anyone who asks what you are."),
    ("coffee-cup", "Trash bag, cardboard tube, lid hat. For the person fueled entirely by coffee."),
    ("deviled-egg", "White shirt, felt yolk, devil horns. The pun does all the work."),
    ("space-crewmate", "Colored sweatsuit plus a cardboard backpack. Pajamas with a theme."),
    ("extinct-party-animal", "Felt spikes on a normal jacket plus a party hat. Gone but still partying."),
]


def fail(msg):
    print("FAIL:", msg, file=sys.stderr)
    sys.exit(1)


def display_time(t):
    # Displayed times are hands-on only: strip any "+ ... drying" suffix
    # (proven pattern from gen_costumes_hub.py / build_aisle_dupes.py).
    return re.sub(r"\s*\+.*drying\s*$", "", str(t))


def share_id(slug):
    return hashlib.sha1(("reluctant:" + slug).encode()).hexdigest()[:8]


def main():
    if not os.path.exists(QR_LIB):
        fail("QR lib missing: " + QR_LIB)
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
    idea_by_id = {e["id"]: e for e in ideas}

    data = []
    for slug, gag in CARDS:
        e = idea_by_id.get(slug)
        if not e:
            fail("idea missing from bank: " + slug)
        i = ins.get(slug)
        if not i:
            fail("no instructions for " + slug)
        for k in ("time", "effort"):
            if not isinstance(i.get(k), str) or not i[k].strip():
                fail("missing time/effort %s for %s" % (k, slug))
        if i["effort"].lower() != "easy":
            fail("not Easy effort: " + slug)
        row = {
            "id": slug,
            "title": e["title"],
            "blurb": e["blurb"],
            "time": display_time(i["time"]),
            "effort": i["effort"],
            "gag": gag,
            "sid": share_id(slug),
        }
        for k in ("title", "blurb", "time", "effort", "gag"):
            if DASH_RE.search(row[k]):
                fail("em/en dash in %s for %s" % (k, slug))
            if "</script" in row[k].lower():
                fail("</script in %s for %s" % (k, slug))
        data.append(row)

    # og image: verify the file exists, else fall back to a known one
    og = "images/og/error-404.jpg"
    if not os.path.exists(os.path.join(ROOT, og)):
        og = "images/og/emoji-crew.jpg"

    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    card_html = []
    for d in data:
        card_html.append(
            '<article class="card" data-id="{id}">'
            '<h3>{title}</h3>'
            '<p class="blurb">{blurb}</p>'
            '<p class="gag">{gag}</p>'
            '<div class="triple"><span>{time}</span><span>{effort}</span></div>'
            '<div class="actions">'
            '<button class="send" data-act="send">Send this one</button>'
            '<a class="guide" data-act="guide" href="https://pickmycostume.com/c/{id}?src=share-reluctant">Build guide</a>'
            '</div>'
            '<div class="qrwrap"><div class="qr" data-qr="{id}"></div>'
            '<p class="qrnote">Point the camera at it to open the build guide.</p></div>'
            '<p class="status" data-status></p>'
            "</article>".format(**{k: html_escape(d[k]) for k in ("id", "title", "blurb", "gag", "time", "effort")})
        )

    html = string.Template(PAGE).substitute(PAYLOAD=payload,CARDS="\n".join(card_html),OG=og)
    if DASH_RE.search(html):
        fail("em/en dash leaked into page output")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote", OUT, "(%d bytes)" % len(html.encode("utf-8")))


def html_escape(s):
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Costumes for People Who Hate Costumes | Pick My Costume</title>
<meta name="description" content="12 Halloween costumes for the person who says they are not dressing up. Each one barely counts as trying, and each card shows its full timed build. That is the point.">
<meta name="robots" content="noindex">
<link rel="canonical" href="https://pickmycostume.com/reluctant-dresser">
<meta property="og:title" content="Costumes for People Who Hate Costumes">
<meta property="og:description" content="Send this to the person who says they are not dressing up. 12 costumes that barely count as trying, each with its full timed build.">
<meta property="og:image" content="https://pickmycostume.com/$OG">
<meta property="og:type" content="website">
<script src="vendor/qrcode-generator/qrcode.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#1a1033;color:#f5f0ff;line-height:1.5;padding:20px 16px 64px}
main{max-width:720px;margin:0 auto}
.kicker{color:#ff9f43;font-weight:700;letter-spacing:2px;font-size:12px;text-transform:uppercase}
h1{font-size:34px;line-height:1.15;margin:8px 0 12px}
.sub{color:#cfc3ea;font-size:17px;margin-bottom:20px}
.who{background:#2a1d4d;border-radius:16px;padding:18px;margin-bottom:24px}
.who label{display:block;font-weight:600;margin-bottom:8px}
.who input{width:100%;font-size:18px;padding:12px;border-radius:10px;border:2px solid #5b3f9e;background:#1a1033;color:#fff}
.who p{font-size:13px;color:#a89bcb;margin-top:8px}
.grid{display:grid;gap:16px}
@media(min-width:560px){.grid{grid-template-columns:1fr 1fr}}
.card{background:#2a1d4d;border-radius:16px;padding:18px}
.card h3{font-size:20px;margin-bottom:6px}
.blurb{color:#cfc3ea;font-size:15px}
.gag{color:#ffd166;font-size:15px;margin:10px 0;font-weight:600}
.triple{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.triple span{background:#1a1033;border:1px solid #5b3f9e;border-radius:999px;padding:4px 12px;font-size:13px}
.actions{display:flex;gap:10px;margin-bottom:10px}
.send{flex:1;background:#ff6b6b;color:#1a1033;border:0;border-radius:10px;padding:12px;font-size:16px;font-weight:700;cursor:pointer}
.guide{display:inline-block;padding:12px 16px;border-radius:10px;border:2px solid #5b3f9e;color:#f5f0ff;text-decoration:none;font-weight:600}
.qrwrap{display:flex;gap:10px;align-items:center;margin-top:6px}
.qr{background:#fff;border-radius:8px}
.qrnote{font-size:12px;color:#a89bcb}
.status{min-height:22px;font-size:14px;color:#7bed9f;margin-top:8px}
footer{margin-top:36px;color:#a89bcb;font-size:14px;text-align:center}
footer a{color:#ffd166}
</style>
</head>
<body>
<main>
<p class="kicker">For the person who says no</p>
<h1>Costumes for people who hate costumes</h1>
<p class="sub">Twelve costumes that barely count as trying. Each card shows the full timed build. That is the point. Know someone who refuses to dress up? Type their name, then send them the one they cannot argue with.</p>
<div class="who">
<label for="who">Who refuses to dress up?</label>
<input id="who" type="text" placeholder="your partner, your teen, your best friend" autocomplete="off" maxlength="40">
<p>The name only fills in the share text on this page. It is never sent anywhere.</p>
</div>
<div class="grid" id="grid">
$CARDS
</div>
<footer>
<p>Times come straight from each costume's build guide. Build times are estimates. Yours may vary.</p>
<p style="margin-top:10px"><a href="https://pickmycostume.com/?src=share-reluctant">Or take the 2-minute quiz and let it decide</a></p>
<p>Built with Muse.</p></footer>
</main>
<script>
/* PostHog: anonymous usage stats only. No names or answers are sent. Session replay is off. */
(function(){var s=document.createElement("script");s.async=true;s.src="https://us.i.posthog.com/static/array.js";s.onload=function(){try{if(window.posthog&&window.posthog.capture){posthog.init("phc_t9dkHXAZR5VEjPFm3K5JDzGKFsNNxKcwSxxcEBEeLbS7",{api_host:"https://us.i.posthog.com",autocapture:false,capture_pageview:true,disable_session_recording:true});}}catch(e){}};document.head.appendChild(s);})();
function ph(name,props){props=props||{};try{var q=location.search;if(/[?&](probe|sim)=/.test(q)||/[?&]internal=1/.test(q))props.internal=true;if(window.posthog&&window.posthog.capture){window.posthog.capture(name,props);}}catch(e){}}
ph("reluctant_viewed",{});
var DATA=$PAYLOAD;
var BY_ID={};DATA.forEach(function(d){BY_ID[d.id]=d;});
var _tapGuards={};
function tapGuard(key,ms){var n=Date.now();if(n-(_tapGuards[key]||0)<ms)return false;_tapGuards[key]=n;return true;}
function whoName(){var v=document.getElementById("who").value.trim();return v||"someone you know";}
function quizUrl(d){return "https://pickmycostume.com/?s="+d.sid+"&src=share-reluctant";}
function shareText(d){
  return "This costume is for "+whoName()+", who says they are not dressing up this year: "
    +d.title+". "+d.gag+" \\u23F1\\uFE0F Timed: about "+d.time
    +". 2-minute quiz if they want a say in it: "+quizUrl(d);
}
function setStatus(card,msg){card.querySelector("[data-status]").textContent=msg;}
document.getElementById("grid").addEventListener("click",function(ev){
  var btn=ev.target.closest("[data-act]");if(!btn)return;
  var card=btn.closest(".card");var d=BY_ID[card.getAttribute("data-id")];if(!d)return;
  var act=btn.getAttribute("data-act");
  if(act==="guide"){ph("reluctant_guide_tapped",{idea_id:d.id});return;}
  if(act==="send"){
    if(!tapGuard("reluctant-send",2000))return;
    ph("reluctant_card_tapped",{idea_id:d.id});
    var text=shareText(d);
    var done=function(via){ph("reluctant_share_copied",{idea_id:d.id,share_id:d.sid,via:via});
      setStatus(card,via==="native"?"Shared.":"Copied. Paste it in a text to "+whoName()+".");};
    if(navigator.share){
      navigator.share({title:"Costumes for people who hate costumes",text:text}).then(
        function(){done("native");},function(){setStatus(card,"Share cancelled.");});
    }else if(navigator.clipboard&&navigator.clipboard.writeText){
      navigator.clipboard.writeText(text).then(function(){done("copy");},function(){setStatus(card,"Copy failed. Long-press to copy.");});
    }else{
      var ta=document.createElement("textarea");ta.value=text;document.body.appendChild(ta);ta.select();
      try{document.execCommand("copy");done("copy");}catch(e){setStatus(card,"Copy failed. Long-press to copy.");}
      document.body.removeChild(ta);
    }
  }
});
(function(){
  if(typeof qrcode!=="function")return;
  document.querySelectorAll("[data-qr]").forEach(function(box){
    var id=box.getAttribute("data-qr");
    try{
      var qr=qrcode(0,"M");
      qr.addData("https://pickmycostume.com/c/"+id+"?src=share-reluctant");
      qr.make();
      box.innerHTML=qr.createSvgTag({cellSize:3,margin:0,scalable:true});
    }catch(e){box.parentNode.style.display="none";}
  });
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
