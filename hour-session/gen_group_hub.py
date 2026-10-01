#!/usr/bin/env python3
"""Generate group-costumes.html: a static SEO hub of group costume packs.

Why it exists: the red-team finding of 2026-09-25 was that the real social
loop is household coordination, not viral friend-quizzes - and the site had
no acquisition channel. Group/theme searches ("classroom halloween themes",
"couple costume ideas diy", "trunk or treat group") peak Oct 1-15, and the
bank already holds 70+ couple/family/group ideas. This hub packages them as
six themed packs with photos, the decision triple, and plain anchors to the
/c/ guides - the same static-page playbook as costumes.html (no JS, crawlable,
zero interaction with the running share-message A/B/C/D experiment).

Re-run after any bank change (add/remove/rename idea):
    python3 hour-session/gen_group_hub.py
The builder FAILS LOUDLY on: missing idea ids, missing time/cost/effort
triples, missing photos, or duplicate pack slugs.
"""
import html
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PACKS = [
    {"slug": "couples", "title": "Couple costumes",
     "lede": "Two people, one theme. Both costumes build from what's at home, and each one works solo too.",
     "ideas": ["plumber-duo", "sun-moon", "pbj", "cat-mouse", "beekeeper-bee", "tetris-duo"]},
    {"slug": "families", "title": "Family costumes",
     "lede": "A theme for three, four, or five. Everyone gets their own costume, nobody has to match perfectly.",
     "ideas": ["blue-dog-family", "little-pig-family", "dinosaur-family", "superhero-family", "snow-sisters", "safari-zoo-crew"]},
    {"slug": "classrooms", "title": "Classroom and big-group themes",
     "lede": "One theme for the whole class: every child picks a variation, the teacher coordinates, the photo looks incredible.",
     "ideas": ["emoji-crew", "emotion-crew", "numbered-players", "kart-racers", "bowling-pins", "block-game-crew"]},
    {"slug": "trunk-or-treat", "title": "Trunk-or-treat teams",
     "lede": "Neighborhood-friendly, trunk-friendly, and readable from across a parking lot.",
     "ideas": ["ghost-hunters", "breakfast-buffet", "cereal-crew", "fruit-salad", "mermaid-crew", "toy-box-crew"]},
    {"slug": "siblings", "title": "Sibling pairs",
     "lede": "Two kids, zero fights over who is who. Each sibling's costume is its own thing.",
     "ideas": ["snow-sisters", "good-witch-bad-witch", "cat-mouse", "dragon-rider-duo", "blue-alien-ohana", "chipmunk-trio"]},
    {"slug": "teen-crews", "title": "Teen crews",
     "lede": "Group costumes that do not look childish and do not cost $60 per person.",
     "ideas": ["web-slinger-crew", "demon-boy-band", "haunted-animatronics", "headless-horsemen", "the-olympians", "galaxy-knights"]},
]

src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
QUIZ_IDS = {"q1", "q2", "q4", "q5kid", "qocc", "qinterest"}
ideas = {}
for s, t, b in re.findall(r'\{id:"([^"]+)", title:"([^"]+)", blurb:"([^"]+)"', src):
    if s not in QUIZ_IDS:
        ideas[s] = (t, b)

m = re.search(r'INSTRUCTIONS = \{(.*?)\n\};', src, re.S)
triples = {}
for s, ti, co, ef in re.findall(
        r'"([a-z0-9-]+)":\{"m":\[.*?"time":"([^"]+)",\s*"cost":"([^"]+)",\s*"effort":"([^"]+)"',
        m.group(1), re.S):
    triples[s] = (ti, co, ef)

slugs = [p["slug"] for p in PACKS]
assert len(slugs) == len(set(slugs)), "duplicate pack slugs"

for p in PACKS:
    for sid in p["ideas"]:
        assert sid in ideas, "pack %s: idea %s not in bank" % (p["slug"], sid)
        assert sid in triples, "pack %s: idea %s missing time/cost/effort" % (p["slug"], sid)
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

CSS = """body{font-family:-apple-system,system-ui,'Segoe UI',Roboto,sans-serif;margin:0;color:#222;background:#fff;}
.wrap{max-width:900px;margin:0 auto;padding:32px 20px 64px;}
h1{font-size:30px;margin:0 0 8px;}
h2{font-size:22px;margin:40px 0 4px;}
.lede{font-size:16px;color:#555;margin:0 0 18px;line-height:1.5;}
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
footer{margin-top:40px;text-align:center;color:#777;font-size:13px;}"""

FAQ_JSONLD = r'''<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "How do group costume packs work?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Each pack is one theme your whole crew builds from what is at home. Open any idea for its free build guide with the real time, cost, and materials up front - no matching outfits to buy."
      }
    },
    {
      "@type": "Question",
      "name": "What is a good couples costume?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Pick a pair with built-in contrast so the two halves read together. The couples section above has the full list, and every idea links to its own build guide."
      }
    },
    {
      "@type": "Question",
      "name": "What about a whole classroom or trunk-or-treat team?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "The classroom and trunk-or-treat sections have big-group themes where one base idea scales to the whole group, with room for everyone to be a little different."
      }
    },
    {
      "@type": "Question",
      "name": "How much do group costumes cost?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Every build guide lists its own materials cost. Most of our 164 ideas cost $10 or less in materials, and each guide shows its exact number before you start."
      }
    }
  ]
}
</script>'''
FAQ_VISIBLE = r'''<section class="pmc-faq" id="pmc-faq">
<style>
.pmc-faq{margin:32px 0}
.pmc-faq h2{font-size:22px;margin:0 0 8px}
.pmc-faq details{margin:8px 0;border:1px solid rgba(140,140,160,.4);border-radius:10px;padding:10px 14px}
.pmc-faq summary{cursor:pointer;font-weight:700}
.pmc-faq p{margin:8px 0 4px;line-height:1.55}
</style>
<h2>Common questions</h2>
<details class="faq">
<summary>How do group costume packs work?</summary>
<p>Each pack is one theme your whole crew builds from what is at home. Open any idea for its free build guide with the real time, cost, and materials up front - no matching outfits to buy.</p>
</details>
<details class="faq">
<summary>What is a good couples costume?</summary>
<p>Pick a pair with built-in contrast so the two halves read together. The couples section above has the full list, and every idea links to its own build guide.</p>
</details>
<details class="faq">
<summary>What about a whole classroom or trunk-or-treat team?</summary>
<p>The classroom and trunk-or-treat sections have big-group themes where one base idea scales to the whole group, with room for everyone to be a little different.</p>
</details>
<details class="faq">
<summary>How much do group costumes cost?</summary>
<p>Every build guide lists its own materials cost. Most of our 164 ideas cost $10 or less in materials, and each guide shows its exact number before you start.</p>
</details>
</section>'''
# NOTE: FAQ_VISIBLE and FAQ_JSONLD must stay in sync (same Q&A).


page_lines = []
page_lines.append('<!DOCTYPE html>')
page_lines.append('<html lang="en">')
page_lines.append('<head>')
page_lines.append('<meta charset="utf-8">')
page_lines.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
page_lines.append('<title>Group Halloween Costume Ideas: DIY Packs for Couples, Families and Classrooms</title>')
page_lines.append('<meta name="description" content="Group costume packs for Halloween: couples, families, classrooms, trunk-or-treat teams, siblings, and teen crews. Every pack has free DIY build guides with time, cost, and materials.">')
page_lines.append('<link rel="canonical" href="https://pickmycostume.com/group-costumes">')
page_lines.append('<meta property="og:title" content="Group costume packs - Pick My Costume">')
page_lines.append('<meta property="og:description" content="Couples, families, classrooms, trunk-or-treat teams, siblings, teen crews: a theme your whole group can build from what is at home.">')
page_lines.append('<meta property="og:type" content="website">')
page_lines.append(FAQ_JSONLD)
page_lines.append('<style>')
page_lines.append(CSS)
page_lines.append('</style>')
page_lines.append('</head>')
page_lines.append('<body><main class="wrap">')
page_lines.append('<h1>Group costume packs</h1>')
page_lines.append('<p class="lede">Costume season is a group project. Each pack is one theme your whole crew builds from what is at home - every idea links to a free build guide with the time, cost, and materials up front. No matching outfits to buy.</p>')
page_lines.append('<nav class="packs" aria-label="Costume packs">')
page_lines.append('<a href="#couples">Couples</a><a href="#families">Families</a><a href="#classrooms">Classrooms</a><a href="#trunk-or-treat">Trunk-or-treat</a><a href="#siblings">Siblings</a><a href="#teen-crews">Teen crews</a>')
page_lines.append('</nav>')
page_lines.append(sections)
page_lines.append(FAQ_VISIBLE)
page_lines.append('<div class="quiz-cta">')
page_lines.append('<p>Still deciding? Take the 2-minute quiz and get one picked for you.</p>')
page_lines.append('<a href="/">Find your costume</a>')
page_lines.append('</div>')
page_lines.append('<p class="home"><a href="/costumes">Browse all 164 costume guides A-Z</a></p>')
page_lines.append('<footer>Built with Muse.</footer>')
page_lines.append('</main></body></html>')
page = "\n".join(page_lines) + "\n"

for ch in ("—", "–"):
    assert ch not in page, "em/en dash leaked into page"

out = os.path.join(ROOT, "group-costumes.html")
open(out, "w", encoding="utf-8").write(page)
n = sum(len(p["ideas"]) for p in PACKS)
print("wrote %s (%d packs, %d idea slots)" % (out, len(PACKS), n))
