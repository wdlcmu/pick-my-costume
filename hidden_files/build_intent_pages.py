#!/usr/bin/env python3
"""Build 8 static SEO intent pages from bank + pantry materials data.
Emits <slug>.html at repo root. Regenerate with this script; do not hand-edit outputs.
Does NOT touch bank data."""
import re, os, html, json

ROOT = os.path.expanduser('~/workspace/builds/pick-my-costume')
src = open(os.path.join(ROOT, 'app.js'), encoding='utf-8').read()

# ---------- parse bank ----------
ideas = {}
for line in src.split('\n'):
    line = line.strip()
    if not line.startswith('{id:"'):
        continue
    m = re.match(r'\{id:"([a-z0-9-]+)", title:"((?:[^"\\]|\\.)*)", blurb:"((?:[^"\\]|\\.)*)", why:"((?:[^"\\]|\\.)*)", audience:\[([^\]]*)\]', line)
    if not m:
        continue
    tags_m = re.search(r'tags:\{([^}]*)\}', line)
    ideas[m.group(1)] = {'title': m.group(2), 'blurb': m.group(3),
                         'audience': m.group(5), 'tags': tags_m.group(1) if tags_m else ''}
assert len(ideas) == 164, f'idea count drift: {len(ideas)}'

instr = {}
for m in re.finditer(r'"([a-z0-9-]+)":\{"m":\[(.*?)\],"s":\["', src):
    mats = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(2))
    instr.setdefault(m.group(1), {})['m'] = [x.encode().decode('unicode_escape') for x in mats]
for m in re.finditer(r'"time":"((?:[^"\\]|\\.)*)","cost":"((?:[^"\\]|\\.)*)","effort":"((?:[^"\\]|\\.)*)","sizing":"((?:[^"\\]|\\.)*)"', src):
    pass  # handled below per-id
for m in re.finditer(r'"([a-z0-9-]+)":\{"m":\[.*?\],"s":\[.*?\],"time":"((?:[^"\\]|\\.)*)","cost":"((?:[^"\\]|\\.)*)","effort":"((?:[^"\\]|\\.)*)","sizing":"((?:[^"\\]|\\.)*)"', src):
    instr.setdefault(m.group(1), {}).update({'time': m.group(2), 'cost': m.group(3),
        'effort': m.group(4), 'sizing': m.group(5).encode().decode('unicode_escape')})
assert len(instr) == 164

def minutes(t):
    t = (t or '').lower()
    m = re.search(r'(\d+)\s*min', t)
    if m: return int(m.group(1))
    m = re.search(r'(\d+)\s*hr', t)
    if m: return int(m.group(1)) * 60
    return 999

def cost_lo(c):
    m = re.search(r'\$(\d+)', c or '')
    return int(m.group(1)) if m else 999

def photo(iid):
    return os.path.exists(os.path.join(ROOT, 'photos', iid + '.webp'))

def need_line(mats, n=2):
    bits = []
    for x in mats[:n]:
        x = re.sub(r'\s*\(buy:.*$', '', x).strip()
        x = re.sub(r'\s*\(make:.*$', '', x).strip()
        x = re.sub(r'\s*\(own:.*$', '', x).strip()
        bits.append(x[:70])
    return '; '.join(bits)

# ---------- page definitions ----------
PAGES = [
 dict(slug='white-sheet-costumes', kw='white sheet',
      title='White Sheet Costume Ideas: 10 DIY Costumes From a Bedsheet',
      desc='Ten Halloween costumes you can make from a white or black bedsheet: classic ghost, vampire cape, headless horseman and more. Real times, real costs, step-by-step guides.',
      intro=("""That old bedsheet in the linen closet is the fastest costume in the house. A white flat sheet,
scissors, and a marker get you the classic ghost in ten minutes flat, and a black sheet cut into a cape
covers vampires, headless horsemen, and little witches with almost no sewing. The trick most people miss
is sizing the sheet before you cut: twin for kids under eight, full or queen for teens and adults, and
always cut eye holes smaller than you think, you can widen them but you cannot shrink them. Every costume
below starts from a sheet you already own, lists exactly what else you need, and links to a full build
guide with real hands-on time and honest cost. No costume-shop run required."""),
      match=lambda i, d: any(re.search(r'\b(bed\s?sheet|twin sheets?|flat sheet|old sheets?|white sheets?|black sheets?)\b', x, re.I) for x in d.get('m', [])),
      rank=lambda iid: (next((n for n, x in enumerate(instr[iid]['m']) if re.search(r'sheet', x, re.I)), 9), minutes(instr[iid].get('time'))),
      limit=10,
      faqs=[
        ('What size sheet should I use?', 'Twin for kids under eight, full or queen for teens and adults. A sheet that is too big drags on the ground and trips the wearer. You can always trim a sheet, you cannot add fabric back.'),
        ('How do I keep a sheet ghost costume from slipping?', 'Cut eye holes smaller than you think first; you can widen them but not shrink them. A tied sash or belt at the waist holds the sheet in place, and safety pins at the shoulders stop it sliding on kids.'),
        ('Do I need to sew anything?', 'No. Every costume on this page is no-sew. Cut sheet edges do not fray enough to matter for one night, and tape or pins handle the rest.'),
        ('Can my child actually see through the eye holes?', 'Yes, if you place them right. Have the wearer put the sheet on first, mark the eye spots with a washable marker while they look straight ahead, then cut. Cut small, test, then widen.'),
      ],
),
 dict(slug='cardboard-box-costumes', kw='cardboard box',
      title='Cardboard Box Costume Ideas: 12 DIY Costumes From Boxes',
      desc='Twelve Halloween costumes built from cardboard boxes: robots, block games, pizza slices, dinosaurs and more. Real times, real costs, step-by-step guides.',
      intro=("""The box your last delivery came in is a costume waiting to happen. A medium box worn over the
torso becomes a robot, a pizza slice, a game block, or a dinosaur body with nothing more than a box cutter,
tape, and paint. Ask a grocery or liquor store for spares if you need big ones, they give them away free
most mornings. Cut arm and head holes smaller than you think, reinforce inside edges with packing tape so
they survive the night, and keep paint to one or two coats so the cardboard stays light. Every costume
below starts from a box, lists the rest of the supplies honestly, and links to a full build guide with
real hands-on time and cost. The box is free. The costume is not far behind."""),
      match=lambda i, d: any(re.search(r'\bbox\b', x, re.I) and not re.search(r'lunch ?box|box of|toolbox', x, re.I) for x in d.get('m', [])),
      rank=lambda iid: (0 if re.search(r'box per (person|racer)|box, 1 (large|medium)', ' '.join(instr[iid]['m']), re.I) else 1, minutes(instr[iid].get('time'))),
      limit=12,
      exclude={'plastic-dream-crew', 'little-artist', 'space-crewmate'},
      force_in=['pizza-slice', 'donut', 'kart-racers'],
      faqs=[
        ('Where do I get big cardboard boxes for free?', 'Ask grocery or liquor stores in the morning; they give away sturdy boxes free most days. Appliance boxes from a buy-nothing group are the best fit for kid torsos.'),
        ('How do I stop the cardboard tearing at the arm holes?', 'Reinforce every cut edge on the inside with packing tape before the costume goes on. Cut holes smaller than you think and widen slowly; cardboard cut away cannot go back.'),
        ('What paint works on cardboard?', 'Acrylic craft paint or spray paint, one or two thin coats. Thick coats add weight and make the box sag by the end of the night.'),
        ('Is a cardboard box costume safe for little kids?', 'Have an adult do all box-cutter work and tape every inside edge so raw cardboard never scratches skin. Keep the costume away from open flames; cardboard is flammable.'),
      ],
),
 dict(slug='no-sew-costumes', kw='no-sew',
      title='No-Sew Costume Ideas: 12 DIY Costumes Without a Needle',
      desc='Twelve Halloween costumes with zero sewing: closet clothes, safety pins, tape, and glue. Real times, real costs, step-by-step guides.',
      intro=("""If you do not sew, you are not locked out of a good homemade costume. Most of the ideas below
hold together with safety pins, fabric tape, hot glue, or nothing at all, just clothes arranged cleverly.
Pin from the inside so the backs never touch skin, use double-sided fabric tape for hems that need to look
clean, and remember that a hot glue gun sets in under a minute, which beats waiting on stitches you were
never going to do. Every costume below needs no needle, lists exactly what to pull from the closet, and
links to a full build guide with real hands-on time and honest cost. Thread not required."""),
      match=lambda i, d: d.get('effort') == 'Easy' and not any(re.search(r'\bsew\w*|stitch|needle', x, re.I) for x in d.get('m', [])) and any('(own' in x for x in d.get('m', [])),
      rank=lambda iid: (cost_lo(instr[iid].get('cost')), minutes(instr[iid].get('time'))),
      limit=12,
      faqs=[
        ('What holds a no-sew costume together best?', 'Double-sided fabric tape for hems that need to look clean, safety pins from the inside so the backs never touch skin, and a hot glue gun for anything rigid. Hot glue sets in under a minute.'),
        ('Will safety pins show?', 'Not if you pin from the inside of the garment. Pin through a seam or hem where the fabric is doubled so the pin has something to bite.'),
        ('Can I wash clothes after using fabric tape or hot glue?', 'Fabric tape usually survives a gentle wash. Hot glue peels off most fabrics if you pick at an edge. Test a hidden spot first on clothes you care about.'),
      ],
),
 dict(slug='last-minute-costumes', kw='last-minute',
      title='Last-Minute Costume Ideas: 12 Costumes in 30 Minutes or Less',
      desc='Twelve Halloween costumes you can build in 30 minutes or less, tonight, from stuff at home. Real times, real costs, step-by-step guides.',
      intro=("""It is the night of the party and you have nothing. Good news: some of the best costumes on
this site take less time than ordering takeout. The rule for last-minute builds is one hero piece, a ghost
needs only the sheet, a tourist needs only the camera and socks-with-sandals, and everything else is
clothes you already own. Skip anything with drying time unless you have a hair dryer and patience. Every
costume below clocks in at thirty minutes of hands-on work or less, lists exactly what to grab, and links
to a full build guide with honest cost. Set a timer. You will make it."""),
      match=lambda i, d: minutes(d.get('time')) <= 30,
      rank=lambda iid: (minutes(instr[iid].get('time')), cost_lo(instr[iid].get('cost'))),
      limit=12,
      faqs=[
        ('What is the one rule for last-minute costumes?', 'One hero piece. A ghost needs only the sheet, a tourist needs only the camera and socks-with-sandals. Build around a single recognizable item and let closet clothes do the rest.'),
        ('What should I skip when time is short?', 'Anything with drying time: paint, glue-heavy builds, papier-mache. A hair dryer buys you minutes, not miracles.'),
        ('How do I not look like I gave up?', 'Commit to the bit. A name tag, a prop, or a one-line character voice sells a simple costume more than extra accessories do.'),
      ],
),
 dict(slug='family-costumes', kw='family',
      title='Family Halloween Costume Ideas: 12 Group Costumes for the Whole Crew',
      desc='Twelve family Halloween costumes, from toddler-safe to teen-approved. Real times, real costs, step-by-step guides for every group size.',
      intro=("""A family costume only works if the littlest member can actually wear it, sit in it, and
survive the evening in it. The sets below were picked because every member gets a real costume, not a
background role, and the builds scale: make the baby the centerpiece, give the teens the funny parts, and
keep total build time sane by repeating one simple base across the group. Start with the hardest costume
first, usually the smallest person, and fit everything while they are still in a good mood. Every set below
links to full build guides with real hands-on time and honest cost per person, so there are no
day-of surprises."""),
      match=lambda i, d: '"family"' in i['audience'],
      rank=lambda iid: (minutes(instr[iid].get('time')), cost_lo(instr[iid].get('cost'))),
      limit=12,
      faqs=[
        ("Which family member's costume should we build first?", 'The smallest. Fit the toddler or baby while they are still in a good mood, then scale the adult versions off the same simple base.'),
        ('Do we all have to match exactly?', 'No. One repeated color, hat, or prop reads as a group in photos. Matching exactly multiplies the work; a shared element is enough.'),
        ('How do we keep total build time sane?', 'Repeat one simple base across the group instead of building six different costumes. Assembly-line the repeated piece, then add one distinguishing detail per person.'),
      ],
),
 dict(slug='couples-costumes', kw='couples',
      title='Couples Halloween Costume Ideas: 12 Duo Costumes',
      desc='Twelve couples Halloween costumes, from cute to funny to low-effort. Real times, real costs, step-by-step guides.',
      intro=("""The best couples costumes have a joke a stranger gets in three seconds: ketchup and mustard,
plug and socket, sun and moon. Pick the one where both people are equally recognizable, nobody wants to be
the human accessory. Build both halves side by side so the colors and sizes match, and agree in advance on
the effort level, one elaborate half next to one thrown-together half reads as a mistake, not a duo. Every
pair below links to full build guides with real hands-on time and honest cost, so you both know what the
evening is going to take."""),
      match=lambda i, d: '"couple"' in i['audience'],
      rank=lambda iid: (minutes(instr[iid].get('time')), cost_lo(instr[iid].get('cost'))),
      limit=12,
      faqs=[
        ('What makes a couples costume actually work?', 'A joke a stranger gets in three seconds: ketchup and mustard, plug and socket, sun and moon. If you have to explain it, pick a different pair.'),
        ('How do we avoid one person being the boring half?', 'Pick the pair where both halves are equally recognizable, and agree on the effort level in advance. One elaborate half next to a thrown-together half reads as a mistake, not a duo.'),
        ('We waited until the last minute. What still works?', 'Pairs built from closet clothes: office couple, salt and pepper, cat and mouse. Build both halves side by side so the colors and sizes match.'),
      ],
),
 dict(slug='toddler-costumes', kw='toddler',
      title='Toddler Halloween Costume Ideas: 12 Easy Costumes for Ages 1-3',
      desc='Twelve toddler Halloween costumes that are soft, simple, and stroller-friendly. Real times, real costs, step-by-step guides.',
      intro=("""Dressing a toddler is a different sport. Nothing itchy, nothing that covers the face, nothing
with small parts, and it has to survive the stroller, the car seat, and a meltdown. The costumes below were
picked because they go over normal warm clothes, use soft materials, and take under half an hour, since
toddlers do not do fittings. Do the fiddly bits while they nap and save the five-minute dress-up for right
before you leave. Every costume below links to a full build guide with real hands-on time, honest cost, and
sizing notes for little bodies."""),
      match=lambda i, d: 'kid36' in i['tags'] or re.search(r'toddler|ages? 1 (to|-) ?[38]', d.get('sizing', ''), re.I),
      rank=lambda iid: (minutes(instr[iid].get('time')), cost_lo(instr[iid].get('cost'))),
      limit=12,
      faqs=[
        ('What should a toddler costume never include?', 'Nothing itchy, nothing that covers the face, nothing with small parts, and nothing they cannot sit in. If it fails the car-seat test, redesign it.'),
        ('How do I get a toddler into costume without a meltdown?', 'Do the fiddly bits while they nap and save dress-up for five minutes before you leave. Build the costume over normal warm clothes so there is no bare-skin battle.'),
        ('Will it survive the stroller?', 'Keep the silhouette soft and compact: no wide wings, no trailing fabric, no tall hats. Bulky extras come off in the first ten minutes, so plan the costume to look finished without them.'),
      ],
),
 dict(slug='face-paint-costumes', kw='face paint',
      title='Face Paint Costume Ideas: 10 Costumes With Makeup as the Star',
      desc='Ten Halloween costumes where face paint does the heavy lifting: skeletons, witches, animals and more. Real times, real costs, step-by-step guides.',
      intro=("""When the costume is mostly face paint, the outfit can be dead simple, black clothes plus a
painted skeleton face beats a store-bought suit every time. Use proper face paint or makeup, not craft paint
or markers, and do a small patch test on the jaw an hour before in case of sensitive skin. Paint the base
first, let it set, then add details, and keep makeup wipes in your pocket because touch-ups are part of the
deal. Every costume below leans on the paint job, lists the rest honestly, and links to a full build guide
with real hands-on time and cost. The brush is the costume."""),
      match=lambda i, d: any(re.search(r'face paint|makeup', x, re.I) for x in d.get('m', [])),
      rank=lambda iid: (minutes(instr[iid].get('time')), cost_lo(instr[iid].get('cost'))),
      faqs=[
        ('Can I use craft paint or markers on skin?', 'No. Use proper face paint or makeup, and do a small patch test on the jaw an hour before in case of sensitive skin. Craft paint can irritate and stain.'),
        ('What order do I paint in?', 'Base first, let it set, then details. Details painted onto wet base bleed; details painted onto set base stay crisp.'),
        ('How do I keep it from smearing all night?', 'Keep makeup wipes in your pocket because touch-ups are part of the deal, and set the finished paint with a light dusting of translucent powder.'),
      ],
      limit=10),
]

PH_SNIPPET = """<script>
var _phq=[];
function track(name, props){ try { if (window.posthog && posthog.capture) posthog.capture(name, props || {}); else _phq.push([name, props || {}]); } catch (e) {} }
(function(){ var s=document.createElement('script'); s.async=true; s.src='https://us.i.posthog.com/static/array.js';
s.onload=function(){ try { if (window.posthog && posthog.init){ posthog.init('phc_t9dkHXAZR5VEjPFm3K5JDzGKFsNNxKcwSxxcEBEeLbS7',{api_host:'https://us.i.posthog.com',autocapture:false,capture_pageview:true,disable_session_recording:true}); _phq.splice(0).forEach(function(e){ try{posthog.capture(e[0],e[1]);}catch(x){} }); } } catch(e){} };
document.head.appendChild(s); })();
</script>"""

def card(iid):
    i, d = ideas[iid], instr[iid]
    need = need_line(d.get('m', []))
    return f"""<article class="ccard" data-unit-item="{iid}">
<a href="/c/{iid}"><img src="/photos/{iid}.webp" alt="{html.escape(i['title'])} Halloween costume" loading="lazy" width="400" height="400"></a>
<h3><a href="/c/{iid}">{html.escape(i['title'])}</a></h3>
<p class="chips"><span class="chip">⏱ {html.escape(d.get('time',''))} hands-on</span><span class="chip">💲 {html.escape(d.get('cost',''))}</span><span class="chip">{html.escape(d.get('effort',''))}</span></p>
<p class="need"><strong>You need:</strong> {html.escape(need)}</p>
<p class="blurb">{html.escape(i['blurb'])}</p>
<p class="go"><a href="/c/{iid}">Build this costume →</a></p>
</article>"""

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | Pick My Costume</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://pickmycostume.com/{slug}">
<meta property="og:type" content="article">
<meta property="og:title" content="{title} | Pick My Costume">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="https://pickmycostume.com/{slug}">
<meta property="og:image" content="https://pickmycostume.com/images/og/{og}.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title} | Pick My Costume">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="https://pickmycostume.com/images/og/{og}.jpg">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Article","headline":"{title}","description":"{desc}",
"author":{{"@type":"Organization","name":"Pick My Costume"}},
"datePublished":"2026-09-30","mainEntityOfPage":{{"@type":"WebPage","@id":"https://pickmycostume.com/{slug}"}},
"image":"https://pickmycostume.com/images/og/{og}.jpg"}}
</script>
{faq_json}
{ph}
<style>
:root{{--acc:#e8632c;--ink:#1d1a16;--mut:#6b6259;--bg:#fffaf3}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;line-height:1.55}}
.top{{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px 16px;padding:14px 20px;background:#1d1a16;color:#fff}}
.top a{{color:#fff;text-decoration:none}}.brand{{font-weight:800;font-size:18px}}.brand span{{color:#ffb020}}
.sitenav{{display:flex;gap:16px;align-items:center;flex-wrap:wrap}}.sitenav a{{font-weight:600;font-size:15px;padding:12px 8px;display:inline-flex;align-items:center;min-height:44px}}
@media (hover:hover){{.sitenav a:hover{{color:#ffb020}}}}
main{{max-width:1060px;margin:0 auto;padding:24px 20px 60px}}
h1{{font-size:32px;margin:10px 0 4px}}.byline{{color:var(--mut);font-size:14px;margin:0 0 12px}}
.lede{{font-size:18px;max-width:720px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px;margin:28px 0}}
.ccard{{background:#fff;border:1px solid #eadfc9;border-radius:14px;overflow:hidden;padding:0 0 16px}}
.ccard img{{width:100%;height:auto;display:block;aspect-ratio:1/1;object-fit:cover;background:#f3ead8}}
.ccard h3,.ccard p{{margin:10px 16px}}.ccard h3 a{{color:var(--ink);text-decoration:none}}
.chips{{display:flex;flex-wrap:wrap;gap:6px}}.chip{{background:#f6efe0;border-radius:999px;padding:3px 10px;font-size:13px}}
.need{{font-size:14px;color:var(--mut)}}.blurb{{font-size:15px}}.go a{{color:var(--acc);font-weight:700;text-decoration:none}}
.cta{{background:#1d1a16;color:#fff;border-radius:14px;padding:24px;margin:32px 0;text-align:center}}
.cta a{{color:#ffb020;font-weight:700}}
footer{{border-top:1px solid #eadfc9;margin-top:40px;padding:20px;text-align:center;color:var(--mut);font-size:14px}}
footer a{{color:var(--mut);margin:0 10px}}
.faqsec{{margin:32px 0}}.faqsec h2{{font-size:22px;margin:0 0 12px}}
.faqsec details{{background:#fff;border:1px solid #eadfc9;border-radius:10px;margin:0 0 10px;padding:12px 16px}}
.faqsec summary{{font-weight:700;cursor:pointer;font-size:16px}}
.faqsec summary::-webkit-details-marker{{color:var(--acc)}}
.faqsec details p{{margin:8px 0 4px;font-size:15px;color:var(--ink)}}
.remindbox{{margin:26px auto;padding:20px;border:2px solid #ff8c1a;border-radius:14px;text-align:center;background:#fff8f0;max-width:640px}}
.remindbox h2{{margin:0 0 6px;font-size:20px}}
.remindsub{{margin:0 0 12px;color:#6b6259;font-size:15px}}
.remindform{{display:flex;gap:8px;justify-content:center;flex-wrap:wrap}}
.remindform input[type=email]{{font-size:16px;padding:12px 14px;border-radius:10px;border:1px solid #e0d4c2;min-width:220px}}
.remindform button{{font-size:16px;font-weight:800;padding:12px 20px;border-radius:10px;border:0;background:#e8632c;color:#fff;cursor:pointer;min-height:48px}}
.remindnote{{margin:8px 0 0;font-size:14px;color:#6b6259;min-height:20px}}
</style>
</head>
<body>
<header class="top">
<a class="brand" href="https://pickmycostume.com/">Pick My <span>Costume</span></a>
<nav class="sitenav" aria-label="Site">
<a href="https://pickmycostume.com/" aria-label="Find my costume — the quiz">Find</a>
<a href="https://pickmycostume.com/map/">Explore</a>
<a href="https://pickmycostume.com/pantry">Pantry</a>
<a href="https://pickmycostume.com/play">Play</a>
</nav>
</header>
<main>
<p class="byline">Updated September 2026 · Pick My Costume</p>
<h1>{h1}</h1>
<p class="lede">{intro}</p>
<div class="grid" id="intent-grid" data-unit-id="{slug}" data-unit-type="intent-grid">
{cards}
</div>
<section class="remindbox">
<h2>&#128276; One email on Oct 27</h2>
<p class="remindsub">Want one email on Oct 27 with costumes you can make that night? That&#8217;s it, one email, then you&#8217;re off the list.</p>
<form class="remindform" id="remindForm">
<input type="email" id="remindEmail" placeholder="you@example.com" aria-label="Email address" required>
<button type="submit">Remind me</button>
</form>
<p class="remindnote" id="remindNote" role="status"></p>
</section>
<script>(function(){{
var f=document.getElementById('remindForm');if(!f)return;
try{{if(localStorage.getItem('pmc_reminded')==='1'){{f.style.display='none';}}}}catch(_){{}}
f.addEventListener('submit',function(e){{e.preventDefault();
var em=document.getElementById('remindEmail').value.trim();
var note=document.getElementById('remindNote');
if(!/^[^\s@]+@[^\s@]+\.[^\s@]{{2,}}$/.test(em)){{note.textContent='That email doesn\u2019t look right. Try again?';return;}}
note.textContent='Saving\u2026';
fetch('/reminder-signup',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{email:em,source:'intent'}})}})
.then(function(r){{return r.json();}}).then(function(j){{
if(j&&j.ok){{try{{localStorage.setItem('pmc_reminded','1');}}catch(_){{}}note.textContent='\u2705 You\u2019re on the list: one email on Oct 27, that\u2019s it.';}}
else if(j&&j.reason==='unconfigured'){{note.textContent='Reminders are being connected. Check back soon.';}}
else{{note.textContent='Hmm, that didn\u2019t save. Try again?';}}
}},function(){{note.textContent='Hmm, that didn\u2019t save. Try again?';}});}});}})();</script>
{faq_html}
<div class="cta">
<p><strong>Own the supplies already?</strong> <a href="/pantry">Check the Pantry</a> to see which of all 164 costumes you can make tonight from what is in your house. Or <a href="/map/">wander the costume galaxy</a>.</p>
</div>
</main>
<footer>
<a href="/about">About</a><a href="/about#faq">FAQ</a><a href="mailto:hello@pickmycostume.com">Contact</a>
<p>Built with Muse.</p>
</footer>
<script>
(function(){{
  var grid=document.getElementById('intent-grid'); if(!grid||grid._ib) return; grid._ib=true;
  function itemId(a){{ var m=(a.getAttribute('href')||'').match(/^\\/c\\/([a-z0-9-]+)/); return m?m[1]:'unknown'; }}
  function anchors(){{ return Array.prototype.slice.call(grid.querySelectorAll('a[href^="/c/"]')); }}
  grid.addEventListener('click',function(e){{ var a=e.target&&e.target.closest?e.target.closest('a'):null; if(!a||!grid.contains(a))return;
    track('unit_click',{{unit_id:grid.getAttribute('data-unit-id'),unit_type:'intent-grid',page:location.pathname,item_id:itemId(a),position:anchors().indexOf(a)}}); }});
  function fire(){{ track('unit_impression',{{unit_id:grid.getAttribute('data-unit-id'),unit_type:'intent-grid',page:location.pathname,item_count:anchors().length,item_ids:anchors().map(itemId).slice(0,40)}}); }}
  if('IntersectionObserver' in window){{ var o=new IntersectionObserver(function(es){{ es.forEach(function(en){{ if(en.isIntersecting){{ o.disconnect(); fire(); }} }}); }}); o.observe(grid); }}
  else {{ fire(); }}
}})();
(function(){{
  var f=document.querySelector('.faqsec'); if(!f||f._fq) return; f._fq=true;
  f.addEventListener('toggle',function(e){{ var d=e.target&&e.target.closest?e.target.closest('details'):null;
    if(!d||!f.contains(d)||!d.open) return;
    var q=d.querySelector('summary');
    track('unit_click',{{unit_id:f.getAttribute('data-unit-id'),unit_type:'intent-faq',page:location.pathname,
      item_id:(q?q.textContent:'').slice(0,60),position:Array.prototype.indexOf.call(f.querySelectorAll('details'),d)}}); }},true);
}})();
</script>
</body>
</html>
"""

built = []
for p in PAGES:
    cands = [iid for iid in ideas if iid in instr and p['match'](ideas[iid], instr[iid]) and photo(iid)]
    cands = [c for c in cands if c not in p.get('exclude', set())]
    cands.sort(key=p['rank'])
    picked = list(p.get('force_in', [])) + [c for c in cands if c not in p.get('force_in', [])]
    picked = picked[:p['limit']]
    wc = len(p['intro'].split())
    assert len(picked) >= 8, f"{p['slug']}: only {len(picked)} matches"
    assert 80 <= wc <= 150, f"{p['slug']}: intro {wc} words"
    assert len(set(picked)) == len(picked)
    cards = '\n'.join(card(i) for i in picked)
    faq_items = ''.join(
        '<details><summary>%s</summary><p>%s</p></details>' % (html.escape(q), html.escape(a))
        for q, a in p['faqs'])
    faq_html = ('<section class="faqsec" id="faq" data-unit-id="%s" data-unit-type="intent-faq">'
                '<h2>Questions, answered</h2>%s</section>' % (p['slug'], faq_items))
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q,
         "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in p['faqs']]}
    faq_json = '<script type="application/ld+json">\n' + json.dumps(faq_ld, ensure_ascii=False) + '\n</script>'
    assert len(p['faqs']) >= 3, p['slug']
    intro_html = html.escape(' '.join(p['intro'].split()))
    page = TEMPLATE.format(title=p['title'], desc=p['desc'], slug=p['slug'], og=picked[0],
                           faq_html=faq_html, faq_json=faq_json,
                           h1=p['title'].split(':')[0], intro=intro_html, cards=cards, ph=PH_SNIPPET)
    assert 'Pumpkin King and Stitched Bride' not in page
    out = os.path.join(ROOT, p['slug'] + '.html')
    open(out, 'w', encoding='utf-8').write(page)
    built.append((p['slug'], picked))
    print(f"{p['slug']}: {len(picked)} costumes, intro {wc}w -> {picked[0]}")

# ---------- sitemap ----------
sm = os.path.join(ROOT, 'sitemap.xml')
s = open(sm, encoding='utf-8').read()
for slug, _ in built:
    url = f'https://pickmycostume.com/{slug}'
    if url in s:
        continue  # idempotent regen
    s = s.replace('</urlset>', f'  <url><loc>{url}</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>\n</urlset>')
open(sm, 'w', encoding='utf-8').write(s)
import xml.dom.minidom; xml.dom.minidom.parseString(s.encode('utf-8'))
print('sitemap updated + XML valid')

print('\nBUILT:', json.dumps([[s, len(c)] for s, c in built]))
