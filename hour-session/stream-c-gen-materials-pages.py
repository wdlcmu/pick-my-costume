#!/usr/bin/env python3
"""Stream C (Week-2 traffic sprint): generate two staged hub pages.
Sources (all real, site-native):
  - pantry.html const DATA  -> 169 ideas {id,title,mats:[{t,g}]}, 56 pantry materials {id,label,group,staple}
  - functions/c/[slug].js   -> canonical /c/ guide data {time,cost,effort} and materials texts {m}
  - pantry-mats.json         -> cross-check slug universe (164)
Pages are written to the repo working tree (STAGED, not deployed).
"""
import json, re, html, os

REPO = os.path.expanduser('~/workspace/builds/pick-my-costume')
SITE = 'https://pickmycostume.com'

def load_pantry_data():
    src = open(os.path.join(REPO, 'pantry.html'), encoding='utf-8').read()
    i = src.find('const DATA = '); j = src.find('{', i)
    depth = 0; k = j; in_str = False; esc = False
    while k < len(src):
        c = src[k]
        if in_str:
            if esc: esc = False
            elif c == '\\': esc = True
            elif c == '"': in_str = False
        else:
            if c == '"': in_str = True
            elif c == '{': depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0: break
        k += 1
    return json.loads(src[j:k+1])

def load_cguide_data():
    src = open(os.path.join(REPO, 'functions/c/[slug].js'), encoding='utf-8').read()
    def field(seg, name):
        m = re.search(r'"%s":\s*"((?:[^"\\]|\\.)*)"' % name, seg)
        return m.group(1) if m else ''
    def mlist(seg):
        m = re.search(r'"m":\s*\[(.*?)\],\s*"s":', seg, re.S)
        if not m: return []
        return re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))
    out = {}
    slugs = list(json.load(open(os.path.join(REPO, 'pantry-mats.json')))['mats'].keys())
    for s in slugs:
        i = src.find('"'+s+'": {"m"')
        assert i >= 0, 'missing /c/ data for ' + s
        seg = src[i:i+60000]
        out[s] = {'time': field(seg,'time'), 'cost': field(seg,'cost'),
                  'effort': field(seg,'effort'), 'mats': mlist(seg)}
    return out

PANTRY = load_pantry_data()
CG = load_cguide_data()
IDEAS = {x['id']: x for x in PANTRY['ideas']}
MAT_LABEL = {x['id']: x['label'] for x in PANTRY['pantry']}
STAPLES = {x['id'] for x in PANTRY['pantry'] if x.get('staple')}
GROUPS = PANTRY['groups']
assert len(IDEAS) == 169, len(IDEAS)
assert set(IDEAS) == set(CG), 'slug universe mismatch'

def mins(time_str):
    m = re.search(r'(\d+(?:\.\d+)?)\s*(min|hr)', time_str or '')
    if not m: return 10**9
    v = float(m.group(1))
    return v*60 if m.group(2) == 'hr' else v

def reqs_of(idea):
    """Per-requirement data: list of (display_text, [groups of [material ids]]).
    A requirement is covered only if EVERY group has an alternative in the
    kit, matching pantry.html's reqOk. Null-only groups (closet/buy items
    with no pantry material) make the requirement uncovered at default."""
    out = []
    for mat in idea['mats']:
        groups = [sorted({a for a in g if a}) for g in mat['g']]
        out.append((mat['t'], groups))
    return out

def uncovered_reqs(idea, have):
    """Requirements not covered by `have` (set of material ids).
    Mirrors pantry.html score(): requirement missing if any group is
    unsatisfied (null-only groups count as missing at the default kit)."""
    out = []
    for mat in idea['mats']:
        ok = True
        for g in mat['g']:
            alts = [a for a in g if a]
            if not alts or not any(a in have for a in alts):
                ok = False
                break
        if not ok:
            out.append(mat['t'])
    return out

E = html.escape

HEAD_STYLE = """<style>
:root{
  --bg:#160d28; --bg2:#211540; --card:#2a1c52; --ink:#fdf3e3;
  --muted:#cdbcf0; --line:#4b3486; --accent:#ff8c1a; --accent-ink:#2a1500;
  --radius:14px; --good:#7ee2a8;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;line-height:1.65}
.wrap{max-width:860px;margin:0 auto;padding:20px 16px 64px}
header.top{display:flex;align-items:center;justify-content:space-between;padding:14px 0}
.brand{font-weight:800;font-size:18px;color:var(--ink);text-decoration:none}
.brand span{color:var(--accent)}
.home-link{color:var(--muted);text-decoration:none;font-size:14px}
h1{font-size:32px;margin:8px 0 4px;line-height:1.2}
.byline{color:var(--muted);font-size:14px;margin:0 0 16px}
.lede{font-size:18px;color:var(--ink);margin:0 0 8px}
.sub{color:var(--muted);margin:0 0 8px}
h2{font-size:24px;margin:44px 0 6px;line-height:1.3}
h2 .qn{color:var(--accent)}
.section-note{color:var(--muted);font-size:14px;margin:0 0 18px}
.answer{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:16px 18px;margin:0 0 14px}
.answer h3{margin:0 0 6px;font-size:18px}
.answer p{margin:6px 0}
.triple{display:inline-block;background:var(--bg2);border:1px solid var(--line);border-radius:999px;padding:3px 12px;font-size:13px;color:var(--muted);margin:8px 0 4px}
.triple b{color:var(--ink)}
.go{display:inline-block;margin:10px 0 2px;background:var(--accent);color:var(--accent-ink);font-weight:800;font-size:16px;padding:12px 22px;border-radius:var(--radius);text-decoration:none}
.quiet{display:block;margin-top:8px;font-size:13px;color:var(--muted);padding:12px 0;min-height:44px}
.final{background:var(--bg2);border:1px solid var(--line);border-radius:var(--radius);padding:22px;margin-top:40px;text-align:center}
.final h2{margin-top:0}
.fine{color:var(--muted);font-size:13px}
.fine a{display:inline-block;padding:12px 6px;margin:-12px 0}
.footer{margin-top:48px;color:var(--muted);font-size:13px;text-align:center}
header.top a{display:inline-block;padding:12px 10px;min-height:44px}
.footer a{color:var(--muted);display:inline-block;padding:12px 10px}
.faq{background:var(--bg2);border:1px solid var(--line);border-radius:var(--radius);padding:16px 18px;margin:0 0 12px}
.faq h3{margin:0 0 6px;font-size:16px}
.faq p{margin:0;color:var(--muted);font-size:15px}
.faq a{color:var(--accent)}
.tierhead{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.tierhead .count{color:var(--muted);font-size:14px}
.ccard{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:14px 16px;margin:0 0 12px}
.ccard h3{margin:0 0 2px;font-size:18px}
.ccard h3 a{color:var(--ink);text-decoration:none}
.ccard h3 a:hover{text-decoration:underline}
.ccard .triple{margin:6px 0 2px}
.need{font-size:14px;color:var(--muted);margin:6px 0}
.need.ready{color:var(--good);font-weight:700}
.ccard details{margin-top:6px}
.ccard summary{cursor:pointer;color:var(--muted);font-size:13px;padding:8px 0;min-height:44px}
.ccard ul{margin:4px 0 8px;padding-left:20px;color:var(--muted);font-size:14px}
.ccard ul li{margin:3px 0}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}
.chip{background:var(--card);border:1px solid var(--line);color:var(--ink);border-radius:999px;padding:10px 16px;font-size:14px;cursor:pointer;min-height:44px}
.chip.on{background:var(--accent);color:var(--accent-ink);border-color:var(--accent);font-weight:700}
.chip:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.mgroup{margin:14px 0 4px}
.mgroup h4{margin:0 0 6px;font-size:14px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.filterbox{background:var(--bg2);border:2px solid var(--accent);border-radius:var(--radius);padding:20px;margin:28px 0}
.filterbox h2{margin:0 0 4px}
.resultline{font-weight:700;margin:16px 0 4px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:640px){.grid{grid-template-columns:1fr}}
.grid .ccard{margin:0}
a{color:var(--accent)}
.basics{font-size:13px;color:var(--muted);background:var(--bg2);border:1px solid var(--line);border-radius:var(--radius);padding:12px 14px;margin:16px 0}
</style>"""

def head_meta(slug, title, desc, og_img):
    return f"""<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{SITE}/{slug}">
<meta property="og:type" content="article">
<meta property="og:title" content="{E(title.split('|')[0].strip())}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{SITE}/{slug}">
<meta property="og:image" content="{SITE}/images/og/{og_img}.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{E(title.split('|')[0].strip())}">
<meta name="twitter:description" content="{E(desc)}">
<meta name="twitter:image" content="{SITE}/images/og/{og_img}.jpg">
"""

def article_ld(slug, title, desc, og_img, date_pub="2026-09-30"):
    return f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": {json.dumps(title.split('|')[0].strip())},
  "description": {json.dumps(desc)},
  "author": {{"@type": "Organization", "name": "Pick My Costume"}},
  "publisher": {{"@id": "{SITE}/#organization", "@type": "Organization", "name": "Pick My Costume", "url": "{SITE}/"}},
  "datePublished": "{date_pub}",
  "dateModified": "{date_pub}",
  "mainEntityOfPage": {{"@type": "WebPage", "@id": "{SITE}/{slug}"}},
  "image": "{SITE}/images/og/{og_img}.jpg"
}}
</script>"""

def faq_ld(faqs):
    ents = []
    for q, a in faqs:
        ents.append({"@type": "Question", "name": q,
                     "acceptedAnswer": {"@type": "Answer", "text": a}})
    return '<script type="application/ld+json">\n' + json.dumps(
        {"@context": "https://schema.org", "@type": "FAQPage",
         "publisher": {"@id": SITE + "/#organization"},
         "mainEntity": ents}, indent=2) + '\n</script>'

def header():
    return f"""<div class="wrap">
<header class="top">
<a class="brand" href="{SITE}/">Pick My <span>Costume</span></a>
<a class="home-link" href="{SITE}/">Home</a>
</header>"""

def footer():
    return f"""<div class="footer">
<p><a href="{SITE}/">Pick My Costume</a> &middot; <a href="{SITE}/costumes">Browse all 169 costume guides</a> &middot; <a href="{SITE}/pantry">What your closet can build</a></p>
<p class="fine">Built with Muse.</p>
</div>
</div>"""

# ---------------------------------------------------------------- page 1
def build_page1():
    slug = 'diy-costumes-by-materials'
    title = 'Easy DIY Halloween Costumes by Materials You Already Have | Pick My Costume'
    desc = ('Filter 169 easy DIY Halloween costumes by the materials you already own. '
            'Tick your craft stash and see exactly what each costume still needs, with real build times and step-by-step guides.')
    faqs = [
        ("How does the materials filter work?",
         "Tick the supplies you already own and every one of the 169 costumes is re-ranked by what it still needs: fully covered builds lead, then builds missing one or two supplies, then the rest. The materials lists are the real ones from each costume's build guide."),
        ("What household basics do you assume I have?",
         "Scissors, tape, markers, paper and pen, aluminum foil, cardboard, a white t-shirt, a plain t-shirt, black clothes, an old bedsheet, a pillowcase, and socks. These 12 staples are assumed present on this page; the pantry page lets you untick anything you don't actually have."),
        ("Do any costumes need zero extra shopping?",
         "Yes. Two builds are make-tonight from the household basics alone: the Classic Ghost (a white sheet with cut-out eyes) and the Emoji Crew (a yellow tee, a paper plate, and markers). Fourteen more need just 1 or 2 supplies, so one quick store run covers all 16."),
        ("Can I also filter by build time?",
         "Yes. The build-time chips use the real build times from each costume's guide: show only costumes that take 30 minutes or less, or an hour or less."),
        ("Where do the materials lists come from?",
         "Every costume on Pick My Costume has a full DIY build guide with a materials list and numbered steps. This page reuses those same lists, so what you see here matches the guide you'll open."),
    ]
    non_staples = [x for x in PANTRY['pantry'] if not x.get('staple')]
    grp_label = {g['id']: g['label'] for g in GROUPS}

    # default ordering: fewest missing requirements (staples only), then minutes, then title
    # matches pantry.html score() buckets exactly
    cards = []
    for sid, idea in IDEAS.items():
        miss = uncovered_reqs(idea, STAPLES)
        cards.append((len(miss), mins(CG[sid]['time']), idea['title'], sid, miss))
    cards.sort(key=lambda c: (c[0], c[1], c[2]))
    ready_n = sum(1 for c in cards if c[0] == 0)
    one_two = sum(1 for c in cards if 1 <= c[0] <= 2)
    assert ready_n + one_two == 17, (ready_n, one_two)  # the make-tonight/almost 17

    def need_line(miss):
        if not miss:
            return '<p class="need ready">Ready to build: you have everything.</p>'
        shown = miss[:3]
        extra = f' and {len(miss)-3} more' if len(miss) > 3 else ''
        return f'<p class="need">Still need {len(miss)}: {E("; ".join(shown))}{E(extra)}</p>'

    card_html = []
    for n, mn, t, sid, miss in cards:
        r = reqs_of(IDEAS[sid])
        rjson = E(json.dumps([{'t': txt, 'g': gs} for txt, gs in r]), quote=True)
        mat_items = ''.join(f'<li>{E(m["t"])}</li>' for m in IDEAS[sid]['mats'])
        triple = f"{E(CG[sid]['time'])} &middot; {E(CG[sid]['effort'])}"
        card_html.append(
            f'<article class="ccard" data-slug="{sid}" data-mins="{mn}" data-reqs=\'{rjson}\'>'
            f'<h3><a href="{SITE}/c/{sid}">{E(t)}</a></h3>'
            f'<p class="triple"><b>{triple}</b></p>'
            f'{need_line(miss)}'
            f'<details><summary>Full materials list ({len(IDEAS[sid]["mats"])})</summary><ul>{mat_items}</ul></details>'
            f'<a class="quiet" href="{SITE}/c/{sid}">Read the full step-by-step guide &rarr;</a>'
            f'</article>')
    cards_block = '\n'.join(card_html)

    chip_groups = []
    for g in GROUPS:
        items = [x for x in non_staples if x['group'] == g['id']]
        chips = ''.join(
            f'<button class="chip" type="button" data-mat="{x["id"]}" aria-pressed="false">{E(x["label"])}</button>'
            for x in items)
        chip_groups.append(f'<div class="mgroup"><h4>{E(grp_label[g["id"]])}</h4><div class="chips">{chips}</div></div>')
    chips_block = '\n'.join(chip_groups)

    staples_line = ', '.join(MAT_LABEL[s].lower() for s in
        ['scissors','tape','paper-pen','markers','foil','cardboard','white-tshirt','tshirt','black-clothes','bedsheet','pillowcase','socks'])

    body = f"""{header()}
<h1>Easy DIY Halloween Costumes, Filtered by What You Already Own</h1>
<p class="byline">Updated September 2026</p>
<p class="lede">Don't start from the store. Start from the junk drawer. Tick the materials you already have and all <strong>169 costume ideas</strong> re-rank around your stash: fully covered builds first, then the ones missing just a supply or two.</p>
<p class="sub">Every materials list below is the real one from that costume's build guide, and the build times are the real ones too. No guessing, no "easy" hand-waving.</p>

<div class="basics"><strong>We assume you have the 12 household basics:</strong> {E(staples_line)}. Untick anything you don't actually own on the <a href="{SITE}/pantry">pantry page</a>, which fine-tunes every costume.</div>

<div class="filterbox" id="filterbox">
<h2>Your stash</h2>
<p class="section-note">Tap everything you already own. Builds you can make right now jump to the top.</p>
{chips_block}
<div class="mgroup"><h4>Build time</h4><div class="chips" id="timechips">
<button class="chip on" type="button" data-tmax="99999" aria-pressed="true">Any build time</button>
<button class="chip" type="button" data-tmax="30" aria-pressed="false">30 minutes or less</button>
<button class="chip" type="button" data-tmax="60" aria-pressed="false">1 hour or less</button>
</div></div>
<p class="resultline" id="resultline" aria-live="polite">With just the household basics, you can build {ready_n} costume{"" if ready_n==1 else "s"} fully, and {one_two} more with 1-2 extra supplies.</p>
</div>

<h2><span class="qn">1.</span> All 169 costumes, ranked by your stash</h2>
<p class="section-note">Sorted by what each build still needs, from the 12 assumed basics. Tap materials above to re-rank.</p>
<div class="grid" id="grid">
{cards_block}
</div>

<h2><span class="qn">2.</span> In a hurry tonight?</h2>
<p class="section-note">If the clock matters more than the craft drawer, start with the costumes built for tonight.</p>
<div class="answer">
<h3>Make-it-tonight builds</h3>
<p>17 of the 169 ideas are <strong>make-tonight or 1-2 supplies away</strong> from default household basics: the Classic Ghost and the Emoji Crew need zero extra shopping. They are tiered by real build time, 15 minutes to 45 minutes.</p>
<a class="go" href="{SITE}/make-it-tonight-costumes">See the 17 make-it-tonight costumes</a>
<a class="quiet" href="{SITE}/pantry">Or tick everything you own on the pantry page &rarr;</a>
</div>

<h2>FAQ</h2>
{''.join(f'<div class="faq"><h3>{E(q)}</h3><p>{E(a)}</p></div>' for q, a in faqs)}

<div class="final">
<h2>Not sure where to start?</h2>
<p>The 2-minute quiz picks 3 costume ideas from the bank of 169, free, no signup.</p>
<a class="go" href="{SITE}/">Take the quiz</a>
<p class="fine">Prefer to browse? <a href="{SITE}/costumes\">Browse all 169 guides</a> &middot; <a href="{SITE}/easy-last-minute-halloween-costumes">Last-minute picks</a></p>
</div>
{footer()}
<script>
(function(){{
  var STAPLES = {json.dumps(sorted(STAPLES))};
  var LABELS = {json.dumps(MAT_LABEL)};
  var have = new Set(STAPLES);
  var tmax = 99999;
  var grid = document.getElementById('grid');
  var cards = Array.prototype.slice.call(grid.querySelectorAll('.ccard'));
  var resultline = document.getElementById('resultline');

  /* tapGuard: ignore finger-bounce re-taps within 300ms */
  var lastTap = {{}};
  function guarded(key, fn){{
    var now = Date.now();
    if (lastTap[key] && now - lastTap[key] < 300) return;
    lastTap[key] = now; fn();
  }}

  function needLine(miss){{
    if (!miss.length) return '<p class="need ready">Ready to build: you have everything.</p>';
    var shown = miss.slice(0,3).map(function(m){{ return m.t; }});
    var extra = miss.length > 3 ? ' and ' + (miss.length-3) + ' more' : '';
    return '<p class="need">Still need ' + miss.length + ': ' +
      shown.map(function(s){{ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;'); }}).join('; ') + extra + '</p>';
  }}

  function cardReqs(card){{
    return JSON.parse(card.getAttribute('data-reqs'));
  }}

  function reqCovered(req){{
    return req.g.every(function(group){{
      return group.some(function(id){{ return have.has(id); }});
    }});
  }}

  function refresh(){{
    var ready = 0, oneTwo = 0, shown = 0;
    cards.forEach(function(card){{
      var mins = parseFloat(card.getAttribute('data-mins'));
      if (mins > tmax) {{ card.style.display = 'none'; return; }}
      card.style.display = '';
      shown++;
      var miss = [];
      cardReqs(card).forEach(function(req){{
        if (!reqCovered(req)) miss.push({{t: req.t}});
      }});
      if (miss.length === 0) ready++;
      else if (miss.length <= 2) oneTwo++;
      var old = card.querySelector('.need');
      if (old) {{ var tmp = document.createElement('div'); tmp.innerHTML = needLine(miss); old.replaceWith(tmp.firstChild); }}
      card._miss = miss.length;
    }});
    cards.sort(function(a,b){{
      if (a.style.display === 'none' && b.style.display === 'none') return 0;
      if (a.style.display === 'none') return 1;
      if (b.style.display === 'none') return -1;
      return (a._miss - b._miss) || a.getAttribute('data-slug').localeCompare(b.getAttribute('data-slug'));
    }});
    cards.forEach(function(card){{ grid.appendChild(card); }});
    resultline.innerHTML = 'With what you ticked, you can build <strong>' + ready + '</strong> costume' +
      (ready === 1 ? '' : 's') + ' fully, and <strong>' + oneTwo + '</strong> more with 1-2 extra supplies.' +
      (shown < cards.length ? ' (' + shown + ' shown by build-time filter.)' : '');
  }}

  document.querySelectorAll('#filterbox .chip[data-mat]').forEach(function(chip){{
    chip.addEventListener('click', function(){{
      guarded('m:' + chip.getAttribute('data-mat'), function(){{
        var id = chip.getAttribute('data-mat');
        var on = chip.classList.toggle('on');
        chip.setAttribute('aria-pressed', on ? 'true' : 'false');
        if (on) have.add(id); else have.delete(id);
        refresh();
      }});
    }});
  }});

  document.querySelectorAll('#timechips .chip').forEach(function(chip){{
    chip.addEventListener('click', function(){{
      guarded('t:' + chip.getAttribute('data-tmax'), function(){{
        document.querySelectorAll('#timechips .chip').forEach(function(x){{
          x.classList.remove('on'); x.setAttribute('aria-pressed','false');
        }});
        chip.classList.add('on'); chip.setAttribute('aria-pressed','true');
        tmax = parseFloat(chip.getAttribute('data-tmax'));
        refresh();
      }});
    }});
  }});
}})();
</script>
"""

    page = f"""<!DOCTYPE html>
<html lang="en">
{head_meta(slug, title, desc, 'ninja')}
{article_ld(slug, title, desc, 'ninja')}
{faq_ld(faqs)}
{HEAD_STYLE}
</head>
<body>
{body}
</body>
</html>
"""
    open(os.path.join(REPO, slug + '.html'), 'w', encoding='utf-8').write(page)
    print('wrote', slug + '.html', len(page), 'bytes;', len(cards), 'cards;', ready_n, 'ready default')

# ---------------------------------------------------------------- page 2
TIER_DEFS = [
    ('15 minutes or less', 15),
    ('20 to 30 minutes', 30),
    ('45 minutes', 45),
]

def build_page2():
    slug = 'make-it-tonight-costumes'
    title = 'Make-It-Tonight Halloween Costumes: 17 Builds You Can Finish This Evening | Pick My Costume'
    desc = ('17 Halloween costumes you can make tonight from household basics: 5 take 15 minutes or less, '
            '9 take 20 to 30 minutes, and 3 take up to 45 minutes. Real build times and step-by-step guides.')
    mt17 = ['classic-ghost','ninja','emoji-crew','fairy-tale-princesses','salt-pepper',
            'breakfast-buffet','cereal-crew','decades-crew','ice-cream-cone','player-one-two',
            'space-crewmate','coffee-cup','ghost-hunters','block-monster',
            'block-game-crew','plug-socket','night-hero']
    tiers = {15: [], 30: [], 45: []}
    for s in mt17:
        m = mins(CG[s]['time'])
        tier = 15 if m <= 15 else (30 if m <= 30 else 45)
        tiers[tier].append(s)
    assert sum(len(v) for v in tiers.values()) == 17
    print('tiers:', {k: len(v) for k, v in tiers.items()})

    titles = {'classic-ghost': 'Classic Ghost', 'ninja': 'Ninja', 'emoji-crew': 'Emoji Crew',
              'fairy-tale-princesses': 'Fairy Tale Princesses', 'salt-pepper': 'Salt & Pepper'}
    # titles from pantry DATA for the rest
    for s in mt17:
        titles[s] = IDEAS[s]['title']

    blurbs = {
        'classic-ghost': 'A white sheet, two cut-out eyes, and you are done. The zero-shopping classic.',
        'ninja': 'All black, a belt sash, and a slit headband. Ten minutes and kids go feral for it.',
        'emoji-crew': 'Yellow tee, a drawn-on emoji face, and the whole group matches in minutes.',
        'fairy-tale-princesses': 'Gold poster-board crowns and plastic gems. Fifteen minutes plus drying.',
        'salt-pepper': 'One white tee, one dark tee, cardboard shakers. The couples classic in 15 minutes.',
        'breakfast-buffet': 'Poster board, markers, and string: wear the most important meal of the day.',
        'cereal-crew': 'An empty cereal box front you decorate, worn sandwich-board style. Scales to any group.',
        'decades-crew': 'Thrift accessories over closet clothes: pick a decade, dress the joke.',
        'ice-cream-cone': 'A tan poster-board cone and a dot-sticker scoop. Sweet and photo-ready.',
        'player-one-two': 'Two plain tees, fabric markers, toy controllers. The duo that reads instantly.',
        'space-crewmate': 'A cardboard box, colored duct tape, and you are the imposter. Twenty minutes.',
        'coffee-cup': 'A cardboard tube, brown poster board, and a white trash-bag lid. You are a giant coffee cup.',
        'ghost-hunters': 'Name patches, small boxes, and a toy hose. Half an hour to a full team look.',
        'block-monster': 'Foam blocks or small boxes plus face paint. Thirty minutes plus drying.',
        'block-game-crew': 'Cardboard boxes and an acrylic paint set: become the game pieces. The biggest build here.',
        'plug-socket': 'Cardboard, black and white paint. The couples costume that fits together.',
        'night-hero': 'A dark cowl and a cape cut from an old t-shirt. Rooftop patrol starts at home.',
    }

    def card(s):
        c = CG[s]
        triple = f"{E(c['time'])} &middot; {E(c['effort'])}"
        mats = ''.join(f'<li>{E(m)}</li>' for m in c['mats'])
        return (f'<article class="ccard">'
                f'<h3><a href="{SITE}/c/{s}">{E(titles[s])}</a></h3>'
                f'<p class="triple"><b>{triple}</b></p>'
                f'<p class="need">{E(blurbs[s])}</p>'
                f'<details><summary>What you need ({len(c["mats"])})</summary><ul>{mats}</ul></details>'
                f'<a class="go" href="{SITE}/c/{s}">Read the step-by-step guide</a>'
                f'<a class="quiet" href="{SITE}/?idea={s}">Open this costume in the quiz &rarr;</a>'
                f'</article>')

    tier_blocks = []
    for label, t in TIER_DEFS:
        items = tiers[t]
        tier_blocks.append(
            f'<div class="tierhead"><h2><span class="qn">&#9201;</span> {label}</h2>'
            f'<span class="count">{len(items)} costume{"" if len(items)==1 else "s"}</span></div>'
            f'<p class="section-note">Hands-on build time from each costume\'s real guide{" (plus drying where noted)" if t in (15,30,45) else ""}.</p>'
            + '\n'.join(card(s) for s in items))

    faqs = [
        ("What does \"make it tonight\" mean?",
         "Buildable this evening from the 12 default household basics (scissors, tape, markers, cardboard, old clothes, paper) plus at most 1 or 2 extra supplies. Two of the 17, the Classic Ghost and the Emoji Crew, need zero extra shopping."),
        ("How many make-tonight costumes are there?",
         "17 out of the 169 costume ideas on Pick My Costume. Two of them, the Classic Ghost and the Emoji Crew, need zero extra shopping from the household basics. The other 15 need just one quick grab of 1 to 2 supplies, so a single dollar-store or craft-aisle run covers all of them."),
        ("What is the fastest costume I can make?",
         "The Classic Ghost and the Ninja, 10 minutes each. The Emoji Crew, Fairy Tale Princesses, and Salt & Pepper take 15 minutes."),
        ("Which make-it-tonight costumes need nothing new?",
         "The Classic Ghost and the Emoji Crew build entirely from the 12 household basics, with zero extra shopping."),
        ("What if I don't have the 1 or 2 extra supplies?",
         "One quick store run covers all 17. Every costume below lists exactly what it still needs."),
    ]

    body = f"""{header()}
<h1>Make-It-Tonight Halloween Costumes</h1>
<p class="byline">Updated September 2026</p>
<p class="lede">It's the evening of the party and you have no costume. These <strong>17 builds</strong>, out of the 169 costume ideas on Pick My Costume, are make-tonight or 1-2 supplies away from default household basics. The longest takes 45 minutes.</p>
<p class="sub">"Tonight" means tonight: real build times from each costume's guide, tiered below. The Classic Ghost and the Emoji Crew need zero extra shopping; the other 15 need one quick grab of 1-2 supplies.</p>

{''.join(tier_blocks)}

<h2><span class="qn">&#10067;</span> Know what you already own?</h2>
<p class="section-note">If the craft drawer is fuller than the basics, start from your stash instead.</p>
<div class="answer">
<h3>Filter all 169 costumes by your materials</h3>
<p>Tick what you own: face paint colors, felt, headbands, yarn, and every costume re-ranks by what it still needs. Fully covered builds jump to the top.</p>
<a class="go" href="{SITE}/diy-costumes-by-materials">Filter by my materials</a>
<a class="quiet" href="{SITE}/pantry">Or tick everything you own on the pantry page &rarr;</a>
</div>

<h2>FAQ</h2>
{''.join(f'<div class="faq"><h3>{E(q)}</h3><p>{E(a)}</p></div>' for q, a in faqs)}

<div class="final">
<h2>Want a pick instead of a list?</h2>
<p>The 2-minute quiz picks 3 costume ideas from the bank of 169, free, no signup.</p>
<a class="go" href="{SITE}/">Take the quiz</a>
<p class="fine">More ways in: <a href="{SITE}/costumes\">Browse all 169 guides</a> &middot; <a href="{SITE}/easy-last-minute-halloween-costumes">Last-minute picks</a> &middot; <a href="{SITE}/cheap-halloween-costumes">Cheap builds</a></p>
</div>
{footer()}
"""

    page = f"""<!DOCTYPE html>
<html lang="en">
{head_meta(slug, title, desc, 'classic-ghost')}
{article_ld(slug, title, desc, 'classic-ghost')}
{faq_ld(faqs)}
{HEAD_STYLE}
</head>
<body>
{body}
</body>
</html>
"""
    open(os.path.join(REPO, slug + '.html'), 'w', encoding='utf-8').write(page)
    print('wrote', slug + '.html', len(page), 'bytes')

if __name__ == '__main__':
    build_page1()
    build_page2()
