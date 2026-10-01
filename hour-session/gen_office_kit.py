#!/usr/bin/env python3
"""Generate office-costumes.html: the Office Halloween Contest Kit.

Why it exists: every distribution bet so far recruits family chats, classrooms,
or strangers on social. Nobody recruits the workplace - and the office costume
contest is a real October coordination moment (Slack #halloween channels,
all-hands judging, HR-safe constraints) that the kid-heavy site otherwise
never reaches. This page is a net-new acquisition channel aimed at the
solo/adult audience, following the proven group-costumes.html playbook:
static, no-JS-dependence, fully crawlable, canonical, og tags.

The page has three jobs:
  1. Four office-safe packs (every idea solo/couple audience + Easy effort,
     asserted from the live bank - no masks, no fake blood, no HR meetings).
  2. A printable contest ballot (beforeprint-tracked).
  3. A copy-paste Slack announcement kit (copy-tracked, ?src=collection-office
     attribution so quiz starts from this page are measurable per landing_src).

Re-run after any bank change (add/remove/rename idea):
    python3 hour-session/gen_office_kit.py
The builder FAILS LOUDLY on: missing idea ids, missing time/cost/effort
triples, non-Easy effort in an office pack, over-30-minute builds in the
under-30 pack, missing photos, duplicate pack slugs, or em/en dashes.
"""
import html
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PACKS = [
    {"slug": "desk-classics", "title": "Desk-job classics",
     "lede": "Readable on a video call, comfortable at a desk, and nobody has to explain anything twice.",
     "ideas": ["coffee-cup", "error-404", "raptor-barista", "crowd-camouflage"]},
    {"slug": "coworker-duos", "title": "Coworker duos",
     "lede": "Pair up with your work bestie for the contest. Each one works solo too, in case they bail.",
     "ideas": ["office-couple", "bacon-eggs", "salt-pepper", "plug-socket"]},
    {"slug": "under-30", "title": "Under 30 minutes",
     "lede": "For the procrastinator. Every build here clocks in under 30 minutes, materials included.",
     "ideas": ["banana", "boxer", "lost-tourist", "referee"]},
    {"slug": "meeting-safe", "title": "Meeting-safe funny",
     "lede": "Funny without the HR risk. No fake blood, no full-face masks, nothing that beeps during standup.",
     "ideas": ["deviled-egg", "hot-dog", "pickle", "donut"]},
]

src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
QUIZ_IDS = {"q1", "q2", "q4", "q5kid", "qocc", "qinterest"}
ideas = {}
for s, t, b in re.findall(r'\{id:"([^\"]+)\", title:"([^\"]+)\", blurb:"([^\"]+)"', src):
    if s not in QUIZ_IDS:
        ideas[s] = (t, b)

m = re.search(r'INSTRUCTIONS = \{(.*?)\n\};', src, re.S)
triples = {}
for s, ti, co, ef in re.findall(
        r'"([a-z0-9-]+)":\{"m":\[.*?"time":"([^\"]+)",\s*"cost":"([^\"]+)",\s*"effort":"([^\"]+)"',
        m.group(1), re.S):
    triples[s] = (ti, co, ef)

slugs = [p["slug"] for p in PACKS]
assert len(slugs) == len(set(slugs)), "duplicate pack slugs"

for p in PACKS:
    for sid in p["ideas"]:
        assert sid in ideas, "pack %s: idea %s not in bank" % (p["slug"], sid)
        assert sid in triples, "pack %s: idea %s missing time/cost/effort" % (p["slug"], sid)
        ti, co, ef = triples[sid]
        assert ef == "Easy", "pack %s: idea %s is effort %r, office packs must be Easy" % (p["slug"], sid, ef)
        if p["slug"] == "under-30":
            mm = re.match(r"(\d+)\s*min", ti)
            assert mm and int(mm.group(1)) <= 30, \
                "pack under-30: idea %s takes %r" % (sid, ti)
        photo = os.path.join(ROOT, "photos", sid + ".webp")
        assert os.path.isfile(photo), "pack %s: missing photo %s" % (p["slug"], photo)


def card(sid):
    title, blurb = ideas[sid]
    ti, co, ef = triples[sid]
    L = []
    L.append('      <article class="card">')
    L.append('        <a href="/c/%s"><img src="/photos/%s.webp" alt="%s" loading="lazy" width="600" height="600"></a>' % (sid, sid, html.escape(title, quote=True)))
    L.append('        <div class="cardbody">')
    L.append('          <h3><a href="/c/%s">%s</a></h3>' % (sid, html.escape(title)))
    L.append('          <p class="triple">%s &middot; %s &middot; %s</p>' % (html.escape(ti), html.escape(co), html.escape(ef)))
    L.append('          <p class="blurb">%s</p>' % html.escape(blurb))
    L.append('          <p class="cta"><a href="/c/%s">Build guide</a></p>' % sid)
    L.append('        </div>')
    L.append('      </article>')
    return "\n".join(L)


def pack_section(p):
    L = []
    L.append('  <section id="%s">' % p["slug"])
    L.append('    <h2>%s</h2>' % html.escape(p["title"]))
    L.append('    <p class="lede">%s</p>' % html.escape(p["lede"]))
    L.append('    <div class="grid">')
    for sid in p["ideas"]:
        L.append(card(sid))
    L.append('    </div>')
    L.append('  </section>')
    return "\n".join(L)


sections = "\n".join(pack_section(p) for p in PACKS)

SLACK_TEXT = """Halloween costume contest is ON: Friday Oct 30, winners announced at the all-hands.
Categories: Funniest, Most Creative, Best DIY, Best Duo.
Need a costume? Take the 2-minute quiz. It picks one you can build from stuff at home: https://pickmycostume.com/?src=collection-office
Office-friendly ideas if you want a head start: https://pickmycostume.com/office-costumes"""

CSS = """body{font-family:-apple-system,system-ui,'Segoe UI',Roboto,sans-serif;margin:0;color:#222;background:#fff;}
.wrap{max-width:900px;margin:0 auto;padding:32px 20px 64px;}
h1{font-size:30px;margin:0 0 8px;}
h2{font-size:22px;margin:40px 0 4px;}
.lede{font-size:16px;color:#555;margin:0 0 18px;line-height:1.5;}
#countline{font-size:15px;font-weight:700;color:#b35c00;margin:0 0 8px;}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px;}
.card{border:1px solid #eee;border-radius:12px;overflow:hidden;background:#fff;}
.card img{width:100%;height:auto;display:block;aspect-ratio:1/1;object-fit:cover;}
.cardbody{padding:12px 14px 16px;}
.card h3{margin:0 0 4px;font-size:17px;}
.card h3 a{color:#1a1a1a;text-decoration:none;}
.card h3 a:hover{color:#e07b00;text-decoration:underline;}
.triple{margin:0 0 6px;font-size:13px;font-weight:700;color:#b35c00;}
.blurb{margin:0 0 10px;font-size:14px;color:#555;line-height:1.45;}
.cta{margin:0;}
.cta a{color:#e07b00;font-weight:700;text-decoration:none;font-size:15px;}
.cta a:hover{text-decoration:underline;}
nav.packs{margin:20px 0 8px;font-size:15px;line-height:2;}
nav.packs a{color:#e07b00;font-weight:700;margin-right:14px;text-decoration:none;}
.quiz-cta{margin:48px 0 0;padding:24px;border:1px solid #eee;border-radius:12px;text-align:center;background:#fffaf2;}
.quiz-cta p{margin:0 0 12px;font-size:17px;}
.quiz-cta a{display:inline-block;background:#e07b00;color:#fff;font-weight:700;padding:12px 28px;border-radius:10px;text-decoration:none;font-size:17px;}
.home{margin-top:32px;font-size:15px;text-align:center;}
.home a{color:#e07b00;font-weight:700;}
footer{margin-top:40px;text-align:center;color:#777;font-size:13px;}
#ballot{border:2px dashed #e07b00;border-radius:12px;padding:20px 22px;margin:16px 0;background:#fffdf8;}
#ballot h3{margin:0 0 2px;font-size:20px;}
.ballot-date{margin:0 0 12px;color:#555;font-size:14px;}
.ballot-cat{margin:14px 0 2px;font-weight:700;font-size:16px;}
.ballot-lines{margin:0 0 4px;color:#777;font-size:14px;line-height:2;}
.ballot-foot{margin:14px 0 0;font-size:13px;color:#555;}
.btn{display:inline-block;background:#e07b00;color:#fff;font-weight:700;padding:10px 22px;border-radius:10px;border:0;font-size:16px;cursor:pointer;margin:6px 8px 6px 0;}
.btn.ghost{background:#fff;color:#e07b00;border:2px solid #e07b00;}
#slacktext{width:100%;font-size:14px;line-height:1.5;padding:12px;border:1px solid #ddd;border-radius:10px;font-family:inherit;}
@media print{
  body *{visibility:hidden;}
  #ballot,#ballot *{visibility:visible;}
  #ballot{position:absolute;left:0;top:0;width:100%;border:0;}
  .btn{display:none;}
}"""

JS = """/* PostHog: anonymous usage stats only. Nothing personal is sent. Session replay is off. */
(function(){
  var s=document.createElement("script");s.async=true;
  s.src="https://us.i.posthog.com/static/array.js";
  s.onload=function(){try{if(window.posthog&&posthog.init){posthog.init("phc_t9dkHXAZR5VEjPFm3K5JDzGKFsNNxKcwSxxcEBEeLbS7",{api_host:"https://us.i.posthog.com",autocapture:false,capture_pageview:true,disable_session_recording:true});}}catch(e){}};
  document.head.appendChild(s);
})();
function officeTrack(name,props){try{if(window.posthog&&posthog.capture)posthog.capture(name,props||{});}catch(e){}}
/* Honest countdown: real date math, rolls to next year after Halloween. */
(function(){
  function daysToHalloween(){var n=new Date();var y=n.getFullYear();var h=new Date(y,9,31);if(n>h)h=new Date(y+1,9,31);return Math.ceil((h-n)/86400000);}
  var el=document.getElementById("countline");
  if(el)el.textContent="Halloween is "+daysToHalloween()+" days out. The contest waits for no one.";
})();
document.getElementById("printballot").addEventListener("click",function(){window.print();});
window.addEventListener("beforeprint",function(){officeTrack("office_ballot_printed",{});});
document.getElementById("copyslack").addEventListener("click",function(){
  var ta=document.getElementById("slacktext");var btn=this;
  function done(){btn.textContent="Copied";setTimeout(function(){btn.textContent="Copy text";},2000);officeTrack("office_slack_copied",{});}
  ta.select();
  try{if(document.execCommand("copy")){done();return;}}catch(e){}
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(ta.value).then(done,done);}
  else{done();}
});"""

FAQ_JSONLD = r'''{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "publisher": {
    "@id": "https://pickmycostume.com/#organization"
  },
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What are good categories for an office costume contest?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Pick four or five: Funniest, Most Creative, Best DIY, Best Duo or Team, Most Desk-Friendly, and a light Scariest. Fewer categories mean every vote counts."
      }
    },
    {
      "@type": "Question",
      "name": "How do you vote in an office costume contest fairly?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "One ballot per person, no voting for yourself, anonymous tally. For small teams, a three-person judging panel beats a popular vote."
      }
    },
    {
      "@type": "Question",
      "name": "Do you need prizes for an office costume contest?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No, but they help turnout. Leave early on a Friday, a coffee card, and a traveling trophy cover it. Keep the budget under $25."
      }
    },
    {
      "@type": "Question",
      "name": "What if nobody at the office wants to dress up?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Keep it opt-in and give people an easy on-ramp. A 2-minute costume quiz that builds a costume from things at home removes the biggest excuse, which is not having an idea."
      }
    },
    {
      "@type": "Question",
      "name": "How do you include remote workers in a costume contest?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Photo parade in a shared thread, a 24-hour voting window for every timezone, winners announced on a video call, and the prize shipped by email."
      }
    },
    {
      "@type": "Question",
      "name": "Should an office costume contest be mandatory?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No. Voluntary contests with good categories get higher turnout than forced ones, and mandatory dress-up punishes tight budgets and real objections."
      }
    },
    {
      "@type": "Question",
      "name": "How many contest categories is too many?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Six is the ceiling and four or five is the sweet spot. Every category needs at least three real contenders or the win feels hollow."
      }
    },
    {
      "@type": "Question",
      "name": "What is the best way to announce contest winners?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "At the all-hands or in the main team channel, one line per winner saying what they won and why. Copy the Slack announcement above and paste it as-is."
      }
    }
  ]
}'''
FAQ_VISIBLE = r'''<section id="faq">
<h2>FAQ</h2>
<h3>What are good categories for an office costume contest?</h3>
<p class="body">Pick four or five: Funniest, Most Creative, Best DIY, Best Duo or Team, Most Desk-Friendly, and a light Scariest. Fewer categories mean every vote counts.</p>
<h3>How do you vote in an office costume contest fairly?</h3>
<p class="body">One ballot per person, no voting for yourself, anonymous tally. For small teams, a three-person judging panel beats a popular vote.</p>
<h3>Do you need prizes for an office costume contest?</h3>
<p class="body">No, but they help turnout. Leave early on a Friday, a coffee card, and a traveling trophy cover it. Keep the budget under $25.</p>
<h3>What if nobody at the office wants to dress up?</h3>
<p class="body">Keep it opt-in and give people an easy on-ramp. A 2-minute costume quiz that builds a costume from things at home removes the biggest excuse, which is not having an idea.</p>
<h3>How do you include remote workers in a costume contest?</h3>
<p class="body">Photo parade in a shared thread, a 24-hour voting window for every timezone, winners announced on a video call, and the prize shipped by email.</p>
<h3>Should an office costume contest be mandatory?</h3>
<p class="body">No. Voluntary contests with good categories get higher turnout than forced ones, and mandatory dress-up punishes tight budgets and real objections.</p>
<h3>How many contest categories is too many?</h3>
<p class="body">Six is the ceiling and four or five is the sweet spot. Every category needs at least three real contenders or the win feels hollow.</p>
<h3>What is the best way to announce contest winners?</h3>
<p class="body">At the all-hands or in the main team channel, one line per winner saying what they won and why. Copy the Slack announcement above and paste it as-is.</p>
</section>'''
# NOTE: FAQ_VISIBLE and FAQ_JSONLD must stay in sync (same Q&A).

page_lines = []
page_lines.append('<!DOCTYPE html>')
page_lines.append('<html lang="en">')
page_lines.append('<head>')
page_lines.append('<meta charset="utf-8">')
page_lines.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
page_lines.append('<title>Office Halloween Costume Ideas: Easy DIY Costumes for Work</title>')
page_lines.append('<meta name="description" content="Work-appropriate Halloween costume ideas: 16 easy DIY office costumes, a printable contest ballot, and a copy-paste Slack announcement.">')
page_lines.append('<link rel="canonical" href="https://pickmycostume.com/office-costumes">')
page_lines.append('<meta property="og:title" content="Office Halloween Contest Kit - Pick My Costume">')
page_lines.append('<meta property="og:description" content="16 work-appropriate DIY costumes, a printable contest ballot, and a Slack announcement kit. Every build guide is free.">')
page_lines.append('<meta property="og:type" content="website">')
page_lines.append('<meta property="og:image" content="https://pickmycostume.com/images/og/coffee-cup.jpg">')
page_lines.append('<script type="application/ld+json">')
page_lines.append(FAQ_JSONLD)
page_lines.append('</script>')
page_lines.append('<style>')
page_lines.append(CSS)
page_lines.append('</style>')
page_lines.append('</head>')
page_lines.append('<body><main class="wrap">')
page_lines.append('<h1>The office Halloween contest kit</h1>')
page_lines.append('<p id="countline"></p>')
page_lines.append('<p class="lede">Sixteen costumes that survive the office: easy builds, no fake blood, no full-face masks, nothing that beeps during standup. Every idea links to a free build guide with the time, cost, and materials up front. Plus a printable ballot and a Slack announcement you can paste as-is.</p>')
page_lines.append('<nav class="packs" aria-label="Costume packs">')
page_lines.append('<a href="#desk-classics">Desk-job classics</a><a href="#coworker-duos">Coworker duos</a><a href="#under-30">Under 30 minutes</a><a href="#meeting-safe">Meeting-safe funny</a><a href="#contest-kit">Contest kit</a>')
page_lines.append('</nav>')
page_lines.append(sections)
page_lines.append('<section id="contest-kit">')
page_lines.append('<h2>Run the contest</h2>')
page_lines.append('<p class="lede">Print the ballot, paste the announcement, done. The contest runs itself from here.</p>')
page_lines.append('<div id="ballot">')
page_lines.append('<h3>Office costume contest ballot</h3>')
page_lines.append('<p class="ballot-date">Friday, October 30, 2026 - one ballot per voter</p>')
for cat in ["Funniest", "Most creative", "Best DIY", "Best duo"]:
    page_lines.append('<p class="ballot-cat">%s</p>' % cat)
    page_lines.append('<p class="ballot-lines">Name: ______________________________<br>Name: ______________________________<br>Name: ______________________________</p>')
page_lines.append('<p class="ballot-foot">Winners announced at the all-hands. Ballots in the box by 3pm.</p>')
page_lines.append('</div>')
page_lines.append('<button class="btn" id="printballot" type="button">Print the ballot</button>')
page_lines.append('<h3 style="margin-top:28px;">The Slack announcement</h3>')
page_lines.append('<p class="lede">Paste this in #halloween, or wherever your office plans things:</p>')
page_lines.append('<textarea id="slacktext" readonly rows="7">%s</textarea>' % html.escape(SLACK_TEXT))
page_lines.append('<button class="btn ghost" id="copyslack" type="button">Copy text</button>')
page_lines.append('</section>')
page_lines.append(FAQ_VISIBLE)
page_lines.append('<div class="quiz-cta">')
page_lines.append('<p>Still deciding? Take the 2-minute quiz and get one picked for you.</p>')
page_lines.append('<a href="/?src=collection-office">Find your costume</a>')
page_lines.append('</div>')
page_lines.append('<p class="home"><a href="/group-costumes">Group costume packs</a> &middot; <a href="/costumes">Browse all 164 costume guides A-Z</a></p>')
page_lines.append('<footer>Built with Muse.</footer>')
page_lines.append('</main>')
page_lines.append('<script>')
page_lines.append(JS)
page_lines.append('</script>')
page_lines.append('</body></html>')
page = "\n".join(page_lines) + "\n"

for ch in ("\u2014", "\u2013"):
    assert ch not in page, "em/en dash leaked into page"
assert "collection-office" in page
# The LANDING_SRC allowlist in index.html accepts collection-[a-z-]+; verify it still does.
assert re.search(r'src=\(collection-\[a-z-\]\+\)', src), "index.html ?src= allowlist changed; office attribution would break"

out = os.path.join(ROOT, "office-costumes.html")
open(out, "w", encoding="utf-8").write(page)
n = sum(len(p["ideas"]) for p in PACKS)
print("wrote %s (%d packs, %d idea slots)" % (out, len(PACKS), n))
