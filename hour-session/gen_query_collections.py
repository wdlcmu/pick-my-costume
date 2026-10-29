#!/usr/bin/env python3
"""Generate query-targeted collection pages for Pick My Costume.

Each page answers one real search-query shape with honestly-matched guides
from the bank. This script is the source of truth for:
  - funny-halloween-costumes.html      ("funny halloween costumes")
  - easy-adult-halloween-costumes.html  ("easy halloween costumes for adults")
  - glow-in-the-dark-costumes.html      ("glow in the dark halloween costumes")
  - cute-halloween-costumes.html        ("cute halloween costumes")
  - womens-halloween-costumes.html      ("womens halloween costumes")
  - mens-halloween-costumes.html        ("mens halloween costumes")
  - college-halloween-costumes.html     ("college halloween costumes")
  - homemade-halloween-costumes.html    ("homemade halloween costumes")
  - goth-halloween-costumes.html        ("goth halloween costumes")

Reads build times, effort, and materials from INSTRUCTIONS in app.js so cards
never drift from the guides. Do not hand-edit the outputs; change this script
and re-run.

2026-10-22 reconciliation (parity audit fix list #2): the live pages had
drifted ahead of this generator. Ported live -> generator (never reverse):
display_time() strips the "+ N drying" suffix from chips and the Quick
answer (Billy's display rule: drying counts in Tonight scoring, never
displayed); lede counts render from the real bank size (was hard-coded
164, bank is 169); the disclaimer regained its stopwatch emoji; titles and
blurbs now come from mcp-server/bank.json (app.js blurbs still carry
pre-scrub IP wording on some rows, e.g. toy-box-crew, emerald-witch);
the glow page's 4th pick is the live haunted-animatronics (not
demon-boy-band) and its first and third FAQ answers are the live
wording; three FAQ answers use the live "anything that has to dry"
wording and the womens time answer is the live "15 to 45 minutes" one. Two live quirks
are preserved on purpose in OVERRIDES below (deadpan-diva materials,
tooth-fairy title) because the job is regen parity, not a live edit.

2026-10-28: the Item 132 quiz-entry line (shipped to the live pages
2026-10-26 as a post-generation edit) is now emitted by page_html()
itself, between the lede and the disclaimer, byte-identical to the
shipped line; verified regen parity on all 8 existing pages (the line
was the only diff). Same run: added the goth page, the documented
missing hub (Oct 3 query research; Oct 25 not-indexed audit). Picks are
the bank's true goth shelf only: the three named goth guides, the
Macabre Goth Couple, the Gloom half of Gloom & Bloom, and the vampire /
macabre wing (Classic Vampire, Juke-Joint Vampires, Plague Doctor).
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPJS = os.path.join(ROOT, "app.js")

PAGES = [
    {
        "key": "funny-halloween-costumes",
        "h1": "Funny Halloween Costume Ideas",
        "title": "Funny Halloween Costumes: 10 DIY Ideas That Get Laughs | Pick My Costume",
        "desc": "Ten funny DIY Halloween costumes with real build times and step-by-step guides: duos, groups, and solos that land the joke.",
        "lede": "Funny wins the party. Every costume below scored high on funny in our {N}-guide bank, and each one has a free step-by-step build guide with real materials, numbered steps, and honest build times.",
        "quick": [("ketchup-mustard", "Ketchup & Mustard"), ("error-404", "Error 404"), ("lost-tourist", "Lost Tourist")],
        "quick_tail": "The fastest laughs below.",
        "picks": ["ketchup-mustard", "error-404", "walking-taco", "plug-socket",
                  "pickle", "lost-tourist", "moth-porch-light", "office-couple",
                  "burger-joint-couple", "chips-guac"],
        "faqs": [
            ("What makes a costume read as funny?",
             "Commitment. A name tag, a prop, or one bad pun delivered deadpan sells it. Half-measures read as confused, not funny."),
            ("Can a funny costume still be easy?",
             "Yes. Most of the picks below take 30 minutes or less of hands-on work. Funny comes from the idea, not the effort."),
            ("What if our group cannot agree on one funny idea?",
             "Pick a theme with roles, like Ketchup and Mustard or the Office Couple. Everyone gets their own part and the photo still reads as one joke."),
        ],
    },
    {
        "key": "easy-adult-halloween-costumes",
        "h1": "Easy Halloween Costumes for Adults",
        "title": "Easy Halloween Costumes for Adults: 10 Low-Effort DIY Ideas | Pick My Costume",
        "desc": "Ten easy Halloween costumes for adults with real build times and step-by-step guides. Low effort, high readability.",
        "lede": "You want to look like you tried without actually trying that hard. Every costume below is rated Easy in our {N}-guide bank and built for adults, each with a free step-by-step guide: real materials, numbered steps, and honest build times.",
        "quick": [("classic-ghost", "Classic Ghost"), ("crowd-camouflage", "Crowd Camouflage"), ("error-404", "Error 404")],
        "quick_tail": "Easy builds that still read as intentional.",
        "picks": ["classic-ghost", "error-404", "scarecrow", "garden-gnome",
                  "pirate-captain", "black-cat", "crowd-camouflage", "chill-painter",
                  "deadpan-diva", "fossil-hunter"],
        "faqs": [
            ("What counts as easy here?",
             "Builds rated Easy in our bank, most under 30 minutes of hands-on work. Times are estimates from the guide; yours may vary."),
            ("I do not want to look cheap in front of coworkers.",
             "Pick one hero piece and wear real clothes otherwise. A name tag or a prop does more than a bag of accessories."),
            ("Can I build one of these tonight?",
             "Most of these, yes. Check the time chip on each card; anything that has to dry needs a head start."),
        ],
    },
    {
        "key": "glow-in-the-dark-costumes",
        "h1": "Glow in the Dark Halloween Costume Ideas",
        "title": "Glow in the Dark Halloween Costumes: 4 DIY Ideas | Pick My Costume",
        "desc": "Four glow-in-the-dark DIY Halloween costumes with real build times and step-by-step guides. Visible after dark, built from tape and glow gear.",
        "lede": "Four costumes that light up after dark, from our {N}-guide bank. Each has a free step-by-step build guide with real materials, numbered steps, and honest build times.",
        "quick": [("glow-skeleton", "Glow Skeleton"), ("tin-hero", "The Tin Hero")],
        "quick_tail": "The brightest picks below.",
        "picks": ["glow-skeleton", "neon-demon-hunter", "tin-hero", "haunted-animatronics"],
        "faqs": [
            ("What makes these costumes glow?",
             "Glow-in-the-dark tape and bracelets, glow-in-the-dark temporary tattoos, and battery tea lights. Each guide lists exactly what to get."),
            ("Are they safe for trick-or-treating?",
             "They are more visible than most costumes, which drivers appreciate. Keep face openings wide and props soft."),
            ("How long does the glow last?",
             "Glow tape charges in light and fades over a few hours. Hold it under a lamp for 10 minutes before heading out for a recharge. The battery tea lights in two of the builds stay lit without charging."),
        ],
    },
    {
        "key": "cute-halloween-costumes",
        "h1": "Cute Halloween Costume Ideas",
        "title": "Cute Halloween Costumes: 10 Adorable DIY Ideas | Pick My Costume",
        "desc": "Ten cute DIY Halloween costumes with real build times and step-by-step guides: princesses, fairies, animals, and food cuties.",
        "lede": "Cute is a strategy. Every costume below scored high on cute in our {N}-guide bank, and each one has a free step-by-step build guide with real materials, numbered steps, and honest build times.",
        "quick": [("fairy-tale-princesses", "Fairy Tale Princesses"), ("tiny-snail", "Tiny Snail"), ("ladybug", "Ladybug")],
        "quick_tail": "The cutest quick wins below.",
        "picks": ["fairy-tale-princesses", "garden-fairy", "ladybug", "tiny-snail",
                  "baby-pumpkin", "blue-heeler-pup", "little-lion", "daisy",
                  "pocket-plush", "chipmunk-trio"],
        "faqs": [
            ("What makes a costume read as cute?",
             "Soft shapes, round features, and one oversized detail. Animal ears, a tutu, or a plush texture do the work; the build underneath can stay simple."),
            ("Are these only for kids?",
             "Most of the picks below are kid and family favorites, but cute scales up. A ladybug or a chipmunk works at any age with the right sizing."),
            ("Can I make one tonight?",
             "Yes, most of these take 30 minutes or less of hands-on work. Check the time chip on each card; anything that has to dry needs a head start."),
        ],
    },
    {
        "key": "womens-halloween-costumes",
        "h1": "Women's Halloween Costume Ideas",
        "title": "Women's Halloween Costumes: 10 DIY Ideas | Pick My Costume",
        "desc": "Ten DIY Halloween costumes for women with real build times and step-by-step guides. Witches, cats, divas, and duos.",
        "lede": "Ten costumes built for adult women, from our {N}-guide bank. Each has a free step-by-step build guide with real materials, numbered steps, and honest build times.",
        "quick": [("black-cat", "Black Cat Burglar"), ("deadpan-diva", "Deadpan Diva"), ("emerald-witch", "Emerald Witch")],
        "quick_tail": "Strong solo picks below.",
        "picks": ["emerald-witch", "deadpan-diva", "vampire", "black-cat",
                  "tooth-fairy", "deviled-egg", "pirate-captain", "witchy-sisters",
                  "good-witch-bad-witch", "juke-joint-vampires"],
        "faqs": [
            ("I want cute, not scary. What should I pick?",
             "Start with the Black Cat Burglar or the Tooth Fairy. Both read instantly and neither needs horror makeup."),
            ("What works for a duo or group?",
             "Good Witch Bad Witch and the Witchy Sisters give everyone a distinct role with one shared theme. The Tooth Fairy plus Tooth is a classic couple pick."),
            ("How much time do these take?",
             "Hands-on time runs 15 to 45 minutes. Check the time chip on each card; anything that has to dry needs a head start."),
        ],
    },
    {
        "key": "mens-halloween-costumes",
        "h1": "Men's Halloween Costume Ideas",
        "title": "Men's Halloween Costumes: 10 DIY Ideas | Pick My Costume",
        "desc": "Ten DIY Halloween costumes for men with real build times and step-by-step guides. Pirates, wizards, boxers, and gnomes.",
        "lede": "Ten costumes built for adult men, from our {N}-guide bank. Every one is rated Easy, and each has a free step-by-step build guide with real materials, numbered steps, and honest build times.",
        "quick": [("error-404", "Error 404"), ("boxer", "Boxer"), ("pirate-captain", "Pirate Captain")],
        "quick_tail": "Fast, funny, and classic picks below.",
        "picks": ["pirate-captain", "error-404", "boxer", "zombie-coworker",
                  "wizard", "chill-painter", "vampire", "scarecrow",
                  "astronaut", "garden-gnome"],
        "faqs": [
            ("I want funny, not scary. What should I pick?",
             "Start with Error 404 or the Garden Gnome. Both read instantly and land as a joke, not a scare."),
            ("What if I have a beard?",
             "Two picks turn a beard into the costume: the Garden Gnome draws a white beard, and the Classic Wizard lists a gray beard as optional."),
            ("How much time do these take?",
             "Hands-on time runs 10 to 30 minutes. Check the time chip on each card; anything that has to dry needs a head start."),
        ],
    },
    {
        "key": "college-halloween-costumes",
        "h1": "College Halloween Costume Ideas",
        "title": "College Halloween Costumes: 10 DIY Ideas | Pick My Costume",
        "desc": "Ten DIY Halloween costumes for college students with real build times and step-by-step guides. Hoodie jokes, pun costumes, and group builds.",
        "lede": "Ten costumes built for college students, from our {N}-guide bank. Every one is rated Easy, and each has a free step-by-step build guide with real materials, numbered steps, and honest build times.",
        "quick": [("error-404", "Error 404"), ("crowd-camouflage", "Crowd Camouflage"), ("ketchup-mustard", "Ketchup & Mustard")],
        "quick_tail": "The fastest dorm builds below.",
        "picks": ["error-404", "crowd-camouflage", "yellow-henchmen",
                  "plastic-dream-crew", "numbered-players", "deviled-egg",
                  "player-one-two", "ketchup-mustard", "referee",
                  "raptor-barista"],
        "faqs": [
            ("We want to go as a group. What scales?",
             "The Yellow Henchmen Crew, Plastic Dream Crew, and Numbered Players fit any group size: one shared look, one part per person. For two people, Ketchup & Mustard and Player One & Two are built as pairs."),
            ("I live in a dorm. What can I actually build?",
             "Start with what is already in your closet. Error 404 is a black hoodie and a sheet of paper, Crowd Camouflage is a gray hoodie, and the Referee builds its stripes from tape on a black tee. No sewing, and nothing needs a work table."),
            ("How much time do these take?",
             "Hands-on time runs 5 to 30 minutes. Check the time chip on each card; anything that has to dry needs a head start."),
        ],
    },
    {
        "key": "homemade-halloween-costumes",
        "h1": "Homemade Halloween Costume Ideas",
        "title": "Homemade Halloween Costumes: 10 Real DIY Builds | Pick My Costume",
        "desc": "Ten truly homemade Halloween costumes with real build times and step-by-step guides: cardboard builds, closet builds, and paint builds.",
        "lede": "Actually homemade, not store-bought with a hat. Every costume below is built from cardboard, closet clothes, or craft supplies in our {N}-guide bank, each with a free step-by-step guide: real materials, numbered steps, and honest build times.",
        "quick": [("classic-ghost", "Classic Ghost"), ("error-404", "Error 404"), ("tiny-snail", "Tiny Snail")],
        "quick_tail": "The simplest builds below.",
        "picks": ["pizza-slice", "tiny-snail", "cardboard-knight", "robot-crew",
                  "classic-ghost", "error-404", "toy-box-crew", "boxer",
                  "walking-taco", "chill-painter"],
        "faqs": [
            ("What counts as homemade here?",
             "Builds made from household stuff: cardboard boxes, closet clothes, sheets, felt, and paint. If the guide's first material is a store costume, it did not make this list."),
            ("I have zero craft skills. Where do I start?",
             "The Classic Ghost or Error 404. One is a sheet with eye holes, the other is a hoodie and paper. Both take 10 minutes."),
            ("What about cardboard builds with kids?",
             "The Pizza Slice, Tiny Snail, and Cardboard Knight are built for exactly that: big cardboard, kid-safe steps, and paint."),
        ],
    },
    {
        "key": "goth-halloween-costumes",
        "h1": "Goth Halloween Costume Ideas",
        "title": "Goth Halloween Costumes: 8 DIY Ideas | Pick My Costume",
        "desc": "Eight goth DIY Halloween costumes with real build times and step-by-step guides: black dresses, tight braids, vampires, and one very calm couple.",
        "lede": "Black dresses, pale makeup, and stares that end conversations. Every costume below is a goth look from our {N}-guide bank, and each one has a free step-by-step build guide with real materials, numbered steps, and honest build times.",
        "quick": [("deadpan-diva", "Deadpan Diva"), ("gloom-bloom", "Gloom & Bloom"), ("goth-braids", "Goth Girl with Braids")],
        "quick_tail": "The fastest goth looks below.",
        "picks": ["deadpan-diva", "goth-braids", "goth-schoolgirl",
                  "macabre-couple", "gloom-bloom", "vampire",
                  "juke-joint-vampires", "plague-doctor"],
        "faqs": [
            ("What makes a costume read as goth?",
             "Black clothing, pale makeup, and a calm stare. The look is mostly attitude: one dark outfit worn like you mean it does more than a pile of accessories."),
            ("Is there a goth costume for a kid?",
             "Yes. The Goth Schoolgirl pairs a plaid skirt and black cardigan with braided pigtails and pale makeup. For a duo, Gloom & Bloom puts one wearer in braids and black while the other goes bright."),
            ("Can I build one of these tonight?",
             "Most of them, yes. The Deadpan Diva and Gloom & Bloom take about 15 minutes of hands-on work. Check the time chip on each card; anything that has to dry needs a head start."),
        ],
    },
]

DASHES = re.compile(r"[\u2013\u2014]")


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def load_bank():
    src = open(APPJS).read()
    ideas = {}
    for m in re.finditer(r'\{id:"([a-z0-9-]+)", title:"([^"]+)", blurb:"((?:[^"\\]|\\.)*)"',
                         src[src.index("var IDEAS = ["):]):
        ideas[m.group(1)] = {"title": m.group(2), "blurb": m.group(3)}
    assert len(ideas) >= 100, "bank parse returned too few ideas: %d" % len(ideas)
    start = src.index("var INSTRUCTIONS = {") + len("var INSTRUCTIONS = ")
    depth, i = 0, start
    while i < len(src):
        c = src[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    ins = json.loads(src[start:i + 1])
    assert len(ins) >= 100, "instructions parse returned too few: %d" % len(ins)
    # Titles/blurbs come from mcp-server/bank.json, not app.js: bank.json
    # carries the IP-scrubbed wording the live pages use (2026-10-22).
    bank = json.load(open(os.path.join(ROOT, "mcp-server", "bank.json")))
    bank_ideas = {i["id"]: i for i in bank["ideas"]}
    assert set(bank_ideas) == set(ideas), "bank.json slugs != app.js slugs"
    for slug, rec in bank_ideas.items():
        ideas[slug] = {"title": rec["title"], "blurb": rec["blurb"]}
    for slug, title in TITLE_OVERRIDES.items():
        ideas[slug]["title"] = title
    return ideas, ins


# Live-page quirks preserved for byte-identical regen (2026-10-22):
# - The live womens page's tooth-fairy card still carries the older title
#   "Tooth and Tooth Fairy"; bank.json renamed the idea to "Tooth Fairy".
# - The live deadpan-diva cards (easy-adult + womens pages) list 4
#   materials; the guide has since gained a 5th, optional choker ribbon.
TITLE_OVERRIDES = {"tooth-fairy": "Tooth and Tooth Fairy"}
NEED_OVERRIDES = {
    "deadpan-diva": ("Black dress, 1 (own); Very pale foundation or white "
                     "non-toxic face paint, 1 (buy: toy store); Dark "
                     "eyeliner and lipstick, 1 set (own, or buy: dollar "
                     "store); 2 hair ties (own)"),
}


def display_time(t):
    # Billy's display rule (2026-10-03): drying counts in Tonight scoring
    # but is never displayed. Bank times are "N min" or "N min + M drying".
    assert re.fullmatch(r"\d+ min( \+ .+ drying)?", t), \
        "unexpected bank time format: %r" % t
    return re.sub(r"\s*\+.*drying\s*$", "", t)


def card_html(slug, ideas, ins):
    rec = ideas[slug]
    d = ins[slug]
    mats = NEED_OVERRIDES.get(slug, "; ".join(d["m"]))
    time_chip = display_time(d["time"])
    return (
        '<article class="ccard" data-unit-item="%s">\n'
        '<a href="/c/%s"><img src="/photos/%s.webp" alt="%s Halloween costume" loading="lazy" width="400" height="400"></a>\n'
        '<p class="ai-note">AI-generated concept photo</p>\n'
        '<h3><a href="/c/%s">%s</a></h3>\n'
        '<p class="chips"><span class="chip">\u23f1 %s</span><span class="chip">%s</span></p>\n'
        '<p class="need"><strong>You need:</strong> %s</p>\n'
        '<p class="blurb">%s</p>\n'
        '<p class="go"><a href="/c/%s">Build this costume \u2192</a></p>\n'
        '</article>'
        % (slug, slug, slug, esc(rec["title"]), slug, esc(rec["title"]),
           esc(time_chip), esc(d["effort"]), esc(mats), esc(rec["blurb"]), slug))


POSTHOG = """<script>
var _phq=[];
function track(name, props){ try { if (window.posthog && posthog.capture) posthog.capture(name, props || {}); else _phq.push([name, props || {}]); } catch (e) {} }
(function(){ var s=document.createElement('script'); s.async=true; s.src='https://us.i.posthog.com/static/array.js';
s.onload=function(){ try { if (window.posthog && posthog.init){ posthog.init('phc_t9dkHXAZR5VEjPFm3K5JDzGKFsNNxKcwSxxcEBEeLbS7',{api_host:'https://us.i.posthog.com',autocapture:false,capture_pageview:true,disable_session_recording:true}); _phq.splice(0).forEach(function(e){ try{posthog.capture(e[0],e[1]);}catch(x){} }); } } catch(e){} };
document.head.appendChild(s) })();
</script>"""

CSS = """<style>
:root{--acc:#e8632c;--ink:#1d1a16;--mut:#6b6259;--bg:#fffaf3}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;line-height:1.55}
.top{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px 16px;padding:14px 20px;background:#1d1a16;color:#fff}
.top a{color:#fff;text-decoration:none}.brand{font-weight:800;font-size:18px}.brand span{color:#ffb020}
.sitenav{display:flex;gap:16px;align-items:center;flex-wrap:wrap}.sitenav a{font-weight:600;font-size:15px;padding:12px 8px;display:inline-flex;align-items:center;min-height:44px}
@media (hover:hover){.sitenav a:hover{color:#ffb020}}
main{max-width:1060px;margin:0 auto;padding:24px 20px 60px}
h1{font-size:32px;margin:10px 0 4px}.byline{color:var(--mut);font-size:14px;margin:0 0 12px}
.lede{font-size:18px;max-width:720px}
.disclaimer{font-size:14px;color:var(--mut);max-width:720px;margin:12px 0 0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px;margin:28px 0}
.ccard{background:#fff;border:1px solid #eadfc9;border-radius:14px;overflow:hidden;padding:0 0 16px}
.ccard img{width:100%;height:auto;display:block;aspect-ratio:1/1;object-fit:cover;background:#f3ead8}
.ccard h3,.ccard p{margin:10px 16px}.ccard h3 a{color:var(--ink);text-decoration:none}
.ai-note{font-size:12px;color:var(--mut);margin:6px 16px 0 !important}
.chips{display:flex;flex-wrap:wrap;gap:6px}.chip{background:#f6efe0;border-radius:999px;padding:3px 10px;font-size:13px}
.need{font-size:14px;color:var(--mut)}.blurb{font-size:15px}.go a{color:var(--acc);font-weight:700;text-decoration:none}
.cta{background:#1d1a16;color:#fff;border-radius:14px;padding:24px;margin:32px 0;text-align:center}
.cta a{color:#ffb020;font-weight:700}
footer{border-top:1px solid #eadfc9;margin-top:40px;padding:20px;text-align:center;color:var(--mut);font-size:14px}
footer a{color:var(--mut);margin:0 10px}
.faqsec{margin:32px 0}.faqsec h2{font-size:22px;margin:0 0 12px}
.faqsec details{background:#fff;border:1px solid #eadfc9;border-radius:10px;margin:0 0 10px;padding:12px 16px}
.faqsec summary{font-weight:700;cursor:pointer;font-size:16px}
.faqsec summary::-webkit-details-marker{color:var(--acc)}
.faqsec details p{margin:8px 0 4px;font-size:15px;color:var(--ink)}
.remindbox{margin:26px auto;padding:20px;border:2px solid #ff8c1a;border-radius:14px;text-align:center;background:#fff8f0;max-width:640px}
.remindbox h2{margin:0 0 6px;font-size:20px}
.remindsub{margin:0 0 12px;color:#6b6259;font-size:15px}
.remindform{display:flex;gap:8px;justify-content:center;flex-wrap:wrap}
.remindform input[type=email]{font-size:16px;padding:12px 14px;border-radius:10px;border:1px solid #e0d4c2;min-width:220px}
.remindform button{font-size:16px;font-weight:800;padding:12px 20px;border-radius:10px;border:0;background:#e8632c;color:#fff;cursor:pointer;min-height:48px}
.remindnote{margin:8px 0 0;font-size:14px;color:#6b6259;min-height:20px}
</style>"""

TRACKING = """<script>
(function(){
  var grid=document.getElementById('intent-grid'); if(!grid||grid._ib) return; grid._ib=true;
  function itemId(a){ var m=(a.getAttribute('href')||'').match(/^\\/c\\/([a-z0-9-]+)/); return m?m[1]:'unknown'; }
  function anchors(){ return Array.prototype.slice.call(grid.querySelectorAll('a[href^="/c/"]')); }
  grid.addEventListener('click',function(e){ var a=e.target&&e.target.closest?e.target.closest('a'):null; if(!a||!grid.contains(a))return;
    track('unit_click',{unit_id:grid.getAttribute('data-unit-id'),unit_type:'intent-grid',page:location.pathname,item_id:itemId(a),position:anchors().indexOf(a)}); });
  function fire(){ track('unit_impression',{unit_id:grid.getAttribute('data-unit-id'),unit_type:'intent-grid',page:location.pathname,item_count:anchors().length,item_ids:anchors().map(itemId).slice(0,40)}); }
  if('IntersectionObserver' in window){ var o=new IntersectionObserver(function(es){ es.forEach(function(en){ if(en.isIntersecting){ o.disconnect(); fire(); } }); }); o.observe(grid); }
  else { fire(); }
})();
(function(){
  var f=document.querySelector('.faqsec'); if(!f||f._fq) return; f._fq=true;
  f.addEventListener('toggle',function(e){ var d=e.target&&e.target.closest?e.target.closest('details'):null;
    if(!d||!f.contains(d)||!d.open) return;
    var q=d.querySelector('summary');
    track('unit_click',{unit_id:f.getAttribute('data-unit-id'),unit_type:'intent-faq',page:location.pathname,
      item_id:(q?q.textContent:'').slice(0,60),position:Array.prototype.indexOf.call(f.querySelectorAll('details'),d)}); },true);
})();
</script>"""


def page_html(page, ideas, ins):
    key = page["key"]
    cards = "\n".join(card_html(s, ideas, ins) for s in page["picks"])
    quick_links = ", ".join(
        '<a href="/c/%s">%s</a> (%s)' % (s, esc(t), esc(display_time(ins[s]["time"])))
        for s, t in page["quick"])
    faq_items = "".join(
        "<details><summary>%s</summary><p>%s</p></details>" % (esc(q), esc(a))
        for q, a in page["faqs"])
    faq_ld = json.dumps([{"@type": "Question", "name": q,
                          "acceptedAnswer": {"@type": "Answer", "text": a}}
                         for q, a in page["faqs"]])
    first = page["picks"][0]
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="https://pickmycostume.com/%s">
<meta property="og:type" content="article">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:url" content="https://pickmycostume.com/%s">
<meta property="og:image" content="https://pickmycostume.com/images/og/%s.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%s">
<meta name="twitter:description" content="%s">
<meta name="twitter:image" content="https://pickmycostume.com/images/og/%s.jpg">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Article","headline":"%s","description":"%s",
"author":{"@type":"Organization","name":"Pick My Costume"},
"datePublished":"2026-10-03","mainEntityOfPage":{"@type":"WebPage","@id":"https://pickmycostume.com/%s"},
"image":"https://pickmycostume.com/images/og/%s.jpg"}
</script>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"FAQPage","mainEntity":%s}
</script>
%s
%s
</head>
<body>
<header class="top">
<a class="brand" href="https://pickmycostume.com/">Pick My <span>Costume</span></a>
<nav class="sitenav" aria-label="Site" data-unit-id="%s" data-unit-type="intent-sitenav">
<a href="https://pickmycostume.com/" aria-label="Pick my costume: the quiz">Pick</a>
<a href="https://pickmycostume.com/map/">Explore</a>
<a href="https://pickmycostume.com/pantry">Pantry</a>
<a href="https://pickmycostume.com/play">Play</a>
</nav>
</header>
<main>
<p class="byline">Updated October 2026 · Pick My Costume</p>
<h1>%s</h1>
<p class="quick-answer"><strong>Quick answer:</strong> %s. %s Tap any name for its full build guide: materials list, numbered steps, and safety notes.</p>
<p class="lede">%s</p>
<p style="margin:14px 0 18px;font-size:17px">Can't pick? <a href="/?" style="font-weight:700">Take the 2-minute quiz →</a> Free. No signup.</p>
<p class="disclaimer">⏱️ We timed it, but results may vary.</p>
<div id="intent-grid" data-unit-id="%s" data-unit-type="intent-grid">
<div class="grid">
%s
</div>
</div>
<section class="remindbox" data-unit-id="%s" data-unit-type="intent-remind">
<h2>&#128276; One email on Oct 27</h2>
<p class="remindsub">Want one email on Oct 27 with costumes you can make that night? That&#8217;s it, one email, then you&#8217;re off the list.</p>
<form class="remindform" id="remindForm">
<input type="email" id="remindEmail" placeholder="you@example.com" aria-label="Email address" required>
<button type="submit">Remind me</button>
</form>
<p class="remindnote" id="remindNote" role="status"></p>
</section>
<script>(function(){
var f=document.getElementById('remindForm');if(!f)return;
try{if(localStorage.getItem('pmc_reminded')==='1'){f.style.display='none';}}catch(_){}
f.addEventListener('submit',function(e){e.preventDefault();
var em=document.getElementById('remindEmail').value.trim();
var note=document.getElementById('remindNote');
if(!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]{2,}$/.test(em)){note.textContent='That email doesn\\u2019t look right. Try again?';return;}
note.textContent='Saving\\u2026';
fetch('/reminder-signup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:em,source:'intent'})})
.then(function(r){return r.json();}).then(function(j){
if(j&&j.ok){try{localStorage.setItem('pmc_reminded','1');}catch(_){}note.textContent='\\u2705 You\\u2019re on the list: one email on Oct 27, that\\u2019s it.';}
else{note.textContent='Hmm, that didn\\u2019t save. Try again?';}
},function(){note.textContent='Hmm, that didn\\u2019t save. Try again?';});});})();
</script>
<section class="faqsec" id="faq" data-unit-id="%s" data-unit-type="intent-faq"><h2>Questions, answered</h2>%s</section>
<div class="cta">
<p><strong>Not sure which one?</strong> <a href="/">Take the 2-minute quiz</a> and get your match. Or <a href="/map/">wander the costume galaxy</a>.</p>
</div>
</main>
<footer>
<a href="/about">About</a><a href="/about#faq">FAQ</a><a href="mailto:hello@pickmycostume.com">Contact</a>
<p>Built with Muse.</p>
</footer>
%s
</body>
</html>
""" % (esc(page["title"]), esc(page["desc"]), key,
       esc(page["title"]), esc(page["desc"]), key, first,
       esc(page["title"]), esc(page["desc"]), first,
       esc(page["h1"]), esc(page["desc"]), key, first,
       faq_ld, POSTHOG, CSS,
       key, esc(page["h1"]), quick_links, esc(page["quick_tail"]),
       esc(page["lede"]).replace("{N}", str(len(ideas))), key, cards, key, key, faq_items, TRACKING)


def main():
    ideas, ins = load_bank()
    for page in PAGES:
        assert page["picks"], "empty picks for %s" % page["key"]
        for slug in page["picks"]:
            assert slug in ideas, "pick not in bank: %s" % slug
            assert slug in ins, "pick missing instructions: %s" % slug
            assert os.path.exists(os.path.join(ROOT, "photos", slug + ".webp")), \
                "missing photo: photos/%s.webp" % slug
            assert os.path.exists(os.path.join(ROOT, "images", "og", slug + ".jpg")), \
                "missing og image: images/og/%s.jpg" % slug
        for field in ("h1", "title", "desc", "lede"):
            assert not DASHES.search(page[field]), "em/en dash in %s.%s" % (page["key"], field)
        html = page_html(page, ideas, ins)
        out = os.path.join(ROOT, page["key"] + ".html")
        open(out, "w").write(html)
        print("wrote", out, len(html), "bytes")


if __name__ == "__main__":
    main()
