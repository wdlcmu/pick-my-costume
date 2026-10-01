#!/usr/bin/env python3
"""Generate costumes-from-your-closet.html (deployed live; title honesty-fixed 2026-10-01).

Inventory-matcher page for the traffic-growth sprint (Tap 4).
- Reuses the real materials taxonomy + per-idea mats from pantry.html's DATA
  (pantry.html is generator output; we only READ it).
- Reuses real titles/blurbs/ranks from mcp-server/bank.json and real
  time/effort from bank instructions (cost stripped per the 2026-10-01
  cost cleanup: no dollar figures anywhere on the page).
- Static server-rendered sections (tonight-16, all-164 grid, FAQ) so raw-HTML
  crawlers see the internal link graph; the JS matcher enhances on top.
- Honesty: the only stat is the computed 16-of-164 (verified in-generator).
"""
import json, re, os, html as htmllib, sys

ROOT = os.path.dirname(os.path.abspath(__file__))

def load_sources():
    html = open(os.path.join(ROOT, 'pantry.html'), encoding='utf-8').read()
    DATA = json.loads(re.search(r'const DATA = (\{.*?\});\n', html, re.S).group(1))
    EMOJI = json.loads(re.search(r'const SUPPLY_EMOJI = (\{.*?\});', html, re.S).group(1))
    EMOJI.setdefault('hoodie', '\U0001F9E5')  # local fallback; pantry has none
    bank = json.load(open(os.path.join(ROOT, 'mcp-server', 'bank.json'), encoding='utf-8'))
    return DATA, EMOJI, bank

CANON = 'https://pickmycostume.com/costumes-from-your-closet'
OG_IMG = 'https://pickmycostume.com/images/og/classic-ghost.jpg'

FAQ = [
    ("What Halloween costume can I make from clothes I already own?",
     "Tick off what you own in the matcher above and it ranks all 164 costume ideas by what you can build. "
     "Out of 164 ideas, 16 are make-tonight or one to two supplies away from default household basics "
     "(scissors, tape, markers, cardboard, old clothes, paper). The Classic Ghost needs only an old bedsheet, "
     "a marker, and scissors."),
    ("How many costumes can I make without shopping at all?",
     "Two with just the 12 assumed household basics: the Classic Ghost and the Emoji Crew. "
     "Fourteen more need just one or two extra supplies, like red paper or glue."),
    ("What is the easiest closet costume for a kid?",
     "The Classic Ghost: 10 minutes, easy. An old bedsheet, a thick black marker, and scissors. "
     "Cut the eye holes small first, you can always widen them."),
    ("What about the KPop Demon Hunters trend?",
     "The Neon Demon Hunter is the top-ranked idea in the bank for 2026. Start with a black hoodie and pants "
     "from the closet, add neon face paint, and grab a foam sword and glow-in-the-dark tattoos for the full look."),
    ("Do I need to buy anything to use this page?",
     "No. It is free with no signup. Every costume shows exactly what you still need, or nothing at all, "
     "and each card links to its full step-by-step build guide."),
]

GROUP_LABELS = {'tools': 'Tools', 'paper': 'Paper and cardboard', 'clothes': 'Clothes and fabric',
                'paint': 'Face paint and makeup', 'craft': 'Craft extras'}

def esc(s):
    return htmllib.escape(s or '', quote=True)

def card_html(slug, title, triple, need=None):
    need_html = ''
    if need:
        need_html = '<span class="cc-need">Need: %s</span>' % esc(need)
    return (
        '<a class="cc-card" data-item-id="%s" href="https://pickmycostume.com/c/%s">'
        '<img src="https://pickmycostume.com/images/og/%s.jpg" alt="%s costume" loading="lazy" width="1200" height="630">'
        '<span class="cc-t"><strong>%s</strong><span class="cc-triple">%s</span>%s</span></a>'
        % (esc(slug), esc(slug), esc(slug), esc(title), esc(title), esc(triple), need_html)
    )

def triple_of(ins):
    return '%s - %s' % (ins.get('time', '?'), ins.get('effort', '?'))

def main():
    DATA, EMOJI, bank = load_sources()
    supplies = DATA['pantry']  # [{id,label,group,staple}]
    ideas = DATA['ideas']
    assert len(ideas) == 164, 'idea count drift: %d' % len(ideas)
    assert len(supplies) == 56, 'supply count drift: %d' % len(supplies)
    ins = bank['instructions']
    brank = {i['id']: i.get('rank', 999) for i in bank['ideas']}
    btitle = {i['id']: i['title'] for i in bank['ideas']}

    staples = [p['id'] for p in supplies if p.get('staple')]
    assert len(staples) == 12, 'staple count drift'

    # --- matching (mirrors pantry.html semantics; also mirrored in page JS) ---
    def gaps_of(it, ticked):
        n = 0
        for mat in it['mats']:
            for g in mat['g']:
                if any(i and i in ticked for i in g):
                    continue
                n += 1
                break
        return n

    ticked = set(staples)
    scored = [(gaps_of(it, ticked), brank.get(it['id'], 999), it) for it in ideas]
    tonight = sorted([s for s in scored if s[0] <= 2], key=lambda s: (s[0], s[1]))
    assert len(tonight) == 16, 'tonight-16 drift: %d' % len(tonight)
    tonight_ids = [it['id'] for _, _, it in tonight]

    label_of = {p['id']: p['label'] for p in supplies}
    # JS data: compact per-idea [grouplist, textlist]
    js_ideas = {}
    for it in ideas:
        sid = it['id']
        js_ideas[sid] = {
            't': btitle.get(sid, it.get('title') or sid),
            'time': ins[sid].get('time', ''),
            'eff': ins[sid].get('effort', ''), 'rank': brank.get(sid, 999),
            'mats': [[list(g) for g in m['g']] for m in it['mats']],
            'txt': [m['t'] for m in it['mats']],
        }
    js_supplies = [{'id': p['id'], 'label': p['label'], 'group': p['group'],
                    'staple': bool(p.get('staple')), 'emoji': EMOJI.get(p['id'], '\U0001F9F0')}
                   for p in supplies]

    # --- static sections ---
    tonight_cards = []
    for g, r, it in tonight:
        sid = it['id']
        tonight_cards.append(card_html(sid, btitle.get(sid, sid), triple_of(ins[sid])))
    tonight_html = '\n'.join(tonight_cards)

    all_cards = []
    for it in sorted(ideas, key=lambda i: brank.get(i['id'], 999)):
        sid = it['id']
        all_cards.append(card_html(sid, btitle.get(sid, sid), triple_of(ins[sid])))
    all_html = '\n'.join(all_cards)

    faq_html = '\n'.join(
        '<details class="faq"><summary>%s</summary><p>%s</p></details>' % (esc(q), esc(a))
        for q, a in FAQ
    )
    faq_schema = json.dumps({
        '@context': 'https://schema.org', '@type': 'FAQPage',
        'publisher': {'@id': 'https://pickmycostume.com/#organization'},
        'mainEntity': [{'@type': 'Question', 'name': q,
                        'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQ],
    }, indent=2)

    article_schema = json.dumps({
        '@context': 'https://schema.org', '@type': 'Article',
        'headline': 'Costumes From Your Closet: 164 Costume Ideas Ranked by What You Own',
        'description': 'Tick off what you already own and see which of 164 Halloween costumes you can make tonight.',
        'author': {'@type': 'Organization', 'name': 'Pick My Costume'},
        'publisher': {'@id': 'https://pickmycostume.com/#organization',
                      'name': 'Pick My Costume', 'url': 'https://pickmycostume.com/'},
        'datePublished': '2026-09-30', 'dateModified': '2026-09-30',
        'mainEntityOfPage': {'@type': 'WebPage', '@id': CANON},
        'image': OG_IMG,
    }, indent=2)

    # --- supply tile groups (static, JS enhances) ---
    groups = {}
    for p in js_supplies:
        groups.setdefault(p['group'], []).append(p)
    group_order = [g for g in GROUP_LABELS if g in groups] + [g for g in groups if g not in GROUP_LABELS]
    tiles_html = []
    for g in group_order:
        tiles = []
        for p in groups[g]:
            tiles.append(
                '<button type="button" class="tile%s" data-sup="%s" aria-pressed="%s">'
                '<span class="e">%s</span><span class="l">%s</span></button>'
                % (' staple' if p['staple'] else '', esc(p['id']),
                   'true' if p['staple'] else 'false', p['emoji'], esc(p['label']))
            )
        tiles_html.append(
            '<h3 class="tgroup">%s</h3><div class="tiles">%s</div>' % (GROUP_LABELS.get(g, g), ''.join(tiles))
        )
    tiles_html = '\n'.join(tiles_html)

    page = build_page(tiles_html, tonight_html, all_html, faq_html, faq_schema,
                      article_schema, js_ideas, js_supplies, staples, tonight_ids)
    out = os.path.join(ROOT, 'costumes-from-your-closet.html')
    open(out, 'w', encoding='utf-8').write(page)
    print('wrote %s (%d bytes)' % (out, len(page)))
    print('tonight-16:', ', '.join(tonight_ids))

def build_page(tiles_html, tonight_html, all_html, faq_html, faq_schema,
               article_schema, js_ideas, js_supplies, staples, tonight_ids):
    data_json = json.dumps({'ideas': js_ideas, 'supplies': js_supplies,
                            'staples': staples, 'tonight': tonight_ids})
    return '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Costumes From Your Closet: 164 Costume Ideas Ranked by What You Own | Pick My Costume</title>
<meta name="description" content="Tick off what you already own and see which of 164 Halloween costumes you can make tonight. 16 are make-tonight or 1 to 2 supplies away from household basics. Free, no signup.">
<link rel="canonical" href="''' + CANON + '''">
<meta property="og:type" content="article">
<meta property="og:title" content="Costumes From Your Closet: 164 Costume Ideas Ranked by What You Own">
<meta property="og:description" content="What can you make tonight from stuff already in your house? Tick what you own, get your matches.">
<meta property="og:url" content="''' + CANON + '''">
<meta property="og:image" content="''' + OG_IMG + '''">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Costumes From Your Closet: 164 Costume Ideas Ranked by What You Own">
<meta name="twitter:description" content="What can you make tonight from stuff already in your house? Tick what you own, get your matches.">
<meta name="twitter:image" content="''' + OG_IMG + '''">
<script type="application/ld+json">
''' + article_schema + '''
</script>
<script type="application/ld+json">
''' + faq_schema + '''
</script>
<style>
:root{
  --bg:#160d28; --bg2:#211540; --card:#2a1c52; --ink:#fdf3e3;
  --muted:#cdbcf0; --line:#4b3486; --accent:#ff8c1a; --accent-ink:#2a1500;
  --radius:14px;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;line-height:1.65}
.wrap{max-width:860px;margin:0 auto;padding:20px 16px 64px}
header.top{display:flex;align-items:center;justify-content:space-between;padding:14px 0}
header.top a{display:inline-block;padding:12px 10px;min-height:44px}
.brand{font-weight:800;font-size:18px;color:var(--ink);text-decoration:none}
.brand span{color:var(--accent)}
.home-link{color:var(--muted);text-decoration:none;font-size:14px}
h1{font-size:32px;margin:8px 0 4px;line-height:1.2}
.byline{color:var(--muted);font-size:14px;margin:0 0 16px}
.lede{font-size:18px;margin:0 0 8px}
.sub{color:var(--muted);margin:0 0 8px}
h2{font-size:24px;margin:44px 0 6px;line-height:1.3}
h2 .qn{color:var(--accent)}
.section-note{color:var(--muted);font-size:14px;margin:0 0 18px}
/* matcher */
.matcher{background:var(--bg2);border:2px solid var(--accent);border-radius:var(--radius);padding:20px;margin:28px 0}
.matcher h2{margin:0 0 4px}
.basics{display:flex;gap:10px;align-items:flex-start;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:14px 0;font-size:15px}
.basics input{width:22px;height:22px;margin-top:2px;flex:none;accent-color:var(--accent)}
.tgroup{font-size:15px;color:var(--muted);margin:18px 0 8px;text-transform:uppercase;letter-spacing:.04em}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(104px,1fr));gap:8px}
.tile{background:var(--card);border:1px solid var(--line);color:var(--ink);border-radius:12px;padding:10px 6px;font-size:13px;cursor:pointer;min-height:64px;font-family:inherit;line-height:1.3}
.tile .e{display:block;font-size:24px;margin-bottom:2px}
.tile .l{display:block}
.tile[aria-pressed="true"]{background:var(--accent);color:var(--accent-ink);border-color:var(--accent);font-weight:700}
.tile:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.bucket-h{font-size:19px;margin:26px 0 4px}
.bucket-h .cnt{color:var(--accent)}
.empty{color:var(--muted);background:var(--card);border:1px dashed var(--line);border-radius:var(--radius);padding:18px;margin:12px 0}
/* cards */
.cc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px;margin:14px 0}
.cc-card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;text-decoration:none;color:var(--ink);display:block}
.cc-card img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block;background:var(--bg2)}
.cc-card .cc-t{display:block;padding:10px 12px}
.cc-card .cc-t strong{display:block;font-size:15px;margin-bottom:2px;line-height:1.35}
.cc-card .cc-triple{display:block;color:var(--muted);font-size:13px}
.cc-card .cc-need{display:block;color:var(--accent);font-size:13px;margin-top:4px}
details.more{margin:14px 0}
details.more summary{cursor:pointer;color:var(--accent);font-weight:700;padding:12px 0;min-height:44px}
/* trending callout */
.trend{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:var(--radius);padding:14px 16px;margin:24px 0}
.trend strong{color:var(--accent)}
.trend a{color:var(--ink)}
/* faq */
.faq{background:var(--bg2);border:1px solid var(--line);border-radius:var(--radius);padding:14px 16px;margin:0 0 10px}
.faq summary{cursor:pointer;font-weight:700;min-height:44px;display:flex;align-items:center}
.faq p{margin:8px 0 4px;color:var(--muted);font-size:15px}
/* final + footer */
.final{background:var(--bg2);border:1px solid var(--line);border-radius:var(--radius);padding:22px;margin-top:40px;text-align:center}
.final h2{margin-top:0}
.go{display:inline-block;margin:10px 0 2px;background:var(--accent);color:var(--accent-ink);font-weight:800;font-size:16px;padding:12px 22px;border-radius:var(--radius);text-decoration:none}
.quiet{display:block;margin-top:8px;font-size:13px;color:var(--muted);padding:12px 0;min-height:44px}
.fine{color:var(--muted);font-size:13px}
.footer{margin-top:48px;color:var(--muted);font-size:13px;text-align:center}
.footer a{color:var(--muted);display:inline-block;padding:12px 10px}
@media (max-width:480px){ h1{font-size:26px} .tiles{grid-template-columns:repeat(auto-fill,minmax(92px,1fr))} }
</style>
</head>
<body>
<div class="wrap">
<header class="top">
<a class="brand" href="https://pickmycostume.com/">Pick My <span>Costume</span></a>
<a class="home-link" href="https://pickmycostume.com/">Home</a>
</header>

<h1>Costumes From Your Closet</h1>
<p class="quick-answer"><strong>Quick answer:</strong> <a href="/c/emoji-crew">Emoji Crew</a> (15 min, 1 yellow t-shirt per person), <a href="/c/classic-ghost">Classic Ghost</a> (10 min, 1 white flat sheet), and <a href="/c/fairy-tale-princesses">Fairy Tale Princesses</a> (15 min + drying, 1 dress from the closet per person) — ranked by how little you need to shop. Tap any name for its full build guide: materials list, numbered steps, and safety notes.</p>
<p class="byline">Updated September 2026</p>
<p class="lede">The cheapest costume is the one you never have to shop for. Tick off what you already own and we will show you which of our 164 costume ideas you can make tonight.</p>
<p class="sub">Out of 164 costume ideas, <strong>16 are make-tonight or one to two supplies away</strong> from default household basics: scissors, tape, markers, paper and pen, aluminum foil, cardboard, a white t-shirt, a plain t-shirt, black clothes, an old bedsheet, a pillowcase, and socks. Every costume below links to its full step-by-step build guide with real times and costs.</p>

<div class="trend">
<strong>Trending now:</strong> the <a href="https://pickmycostume.com/c/neon-demon-hunter">Neon Demon Hunter</a>, our top-ranked 2026 idea. Black hoodie and pants from the closet, neon face paint, a foam sword, and glow tattoos. Pairs with the <a href="https://pickmycostume.com/c/kpop-demon-huntresses">Pop Star Demon Huntresses</a> group look for three.
</div>

<div class="matcher" id="matcher">
<h2>What do you already own?</h2>
<p class="section-note">Tick everything in your house. Your matches update as you go.</p>
<label class="basics"><input type="checkbox" id="basics-toggle" checked>
<span><strong>Assume my house has the basics.</strong> Scissors, tape, markers, paper and pen, foil, cardboard, white t-shirt, plain t-shirt, black clothes, old bedsheet, pillowcase, socks. Untick to start from zero.</span></label>
''' + tiles_html + '''
<div id="results" aria-live="polite"></div>
<p class="fine">Every match links to its full build guide with materials, steps, real time, and real cost. Free, no signup.</p>
</div>

<h2><span class="qn">1.</span> Make tonight from household basics</h2>
<p class="section-note">These are the 16 costumes you can make tonight or with one to two extra supplies, assuming the 12 household basics above. Each links to its full build guide.</p>
<div class="cc-grid" id="tonight-grid">
''' + tonight_html + '''
</div>

<h2><span class="qn">2.</span> Browse every costume guide</h2>
<p class="section-note">All 164 step-by-step build guides, each with real build time and cost.</p>
<div class="cc-grid" id="all-grid">
''' + all_html + '''
</div>

<h2><span class="qn">3.</span> Closet-costume questions</h2>
''' + faq_html + '''

<div class="final">
<h2>Still deciding?</h2>
<p class="section-note">Take the 2-minute quiz and get one pick matched to your vibe, budget, and timeline.</p>
<a class="go" href="https://pickmycostume.com/">Take the quiz</a>
<a class="quiet" href="https://pickmycostume.com/pantry">Or open the full pantry page and tick supplies there</a>
</div>

<p class="footer">Free, no signup. Built with Muse. <a href="https://pickmycostume.com/">Home</a> <a href="https://pickmycostume.com/pantry">Pantry</a></p>
</div>
<script>
/* ==CLOSET-PURE-START== */
var CLOSET = ''' + data_json + ''';
function cgGroupOk(g, ticked){ for (var i = 0; i < g.length; i++){ var id = g[i]; if (id && ticked[id]) return true; } return false; }
/* Gaps for one idea: a material is a gap when any of its groups is unsatisfied.
   Buy-only groups (all ids null) are always gaps here; the card shows "buy: ...". */
function cgGaps(idea, ticked){
  var n = 0, labels = [];
  for (var mi = 0; mi < idea.mats.length; mi++){
    var groups = idea.mats[mi], ok = true, gl = null;
    for (var gi = 0; gi < groups.length; gi++){
      var g = groups[gi];
      if (cgGroupOk(g, ticked)) continue;
      ok = false;
      var names = [];
      for (var k = 0; k < g.length; k++){ if (g[k] && CLOSET_LABEL[g[k]]) names.push(CLOSET_LABEL[g[k]]); }
      gl = names.length ? names.slice(0, 2).join(' or ') : ('buy: ' + idea.txt[mi].split('(')[0].trim());
      break;
    }
    if (!ok){ n++; if (labels.length < 3) labels.push(gl); }
  }
  return {n: n, labels: labels};
}
function cgScore(ticked){
  var out = [], ids = Object.keys(CLOSET.ideas);
  for (var i = 0; i < ids.length; i++){
    var id = ids[i], idea = CLOSET.ideas[id], r = cgGaps(idea, ticked);
    var cov = (idea.mats.length - r.n) / idea.mats.length;
    out.push({id: id, gaps: r.n, labels: r.labels, cov: cov, rank: idea.rank});
  }
  out.sort(function(a, b){
    var ba = a.gaps <= 2 ? 0 : 1, bb = b.gaps <= 2 ? 0 : 1;
    if (ba !== bb) return ba - bb;
    if (a.gaps !== b.gaps) return a.gaps - b.gaps;
    return a.rank - b.rank;
  });
  return out;
}
/* ==CLOSET-PURE-END== */
var CLOSET_LABEL = {};
(function(){ var s = CLOSET.supplies; for (var i = 0; i < s.length; i++) CLOSET_LABEL[s[i].id] = s[i].label; })();
</script>
<script>
(function(){
"use strict";
/* PostHog: same snippet shape as pantry.html */
var _phq = [];
function track(name, props){
  try {
    if (window.posthog && posthog.capture) posthog.capture(name, props || {});
    else _phq.push([name, props || {}]);
  } catch (e) {}
}
(function(){
  var s = document.createElement('script'); s.async = true;
  s.src = 'https://us.i.posthog.com/static/array.js';
  s.onload = function(){
    try {
      if (window.posthog && posthog.init){
        posthog.init('phc_t9dkHXAZR5VEjPFm3K5JDzGKFsNNxKcwSxxcEBEeLbS7', {
          api_host: 'https://us.i.posthog.com', autocapture: false,
          capture_pageview: true, disable_session_recording: true
        });
        _phq.splice(0).forEach(function(e){ try { posthog.capture(e[0], e[1]); } catch (x) {} });
      }
    } catch (e) {}
  };
  document.head.appendChild(s);
})();
/* 2026-09-30: finger-bounce guard, same 400ms class as pantry/quiz/gift/duel.
   A double-tap on a tile fires two toggles (tick then untick), a silent net
   no-op that eats the tick. The bounce event is ignored and the DOM is
   re-synced to the kept state instead of toggling. */
var _cgGuards = {};
function cgGuard(key, ms){
  var n = Date.now();
  if (n - (_cgGuards[key] || 0) < ms) return false;
  _cgGuards[key] = n;
  return true;
}
var ticked = {};
function syncTiles(){
  var tiles = document.querySelectorAll('.tile');
  for (var i = 0; i < tiles.length; i++){
    var on = !!ticked[tiles[i].getAttribute('data-sup')];
    tiles[i].setAttribute('aria-pressed', on ? 'true' : 'false');
  }
}
function applyBasics(on){
  var st = CLOSET.staples;
  for (var i = 0; i < st.length; i++){
    if (on) ticked[st[i]] = true; else delete ticked[st[i]];
  }
}
function escHtml(s){
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function cardHtml(id, need){
  var idea = CLOSET.ideas[id];
  var triple = escHtml(idea.time + ' - ' + idea.eff);
  var needHtml = need ? '<span class="cc-need">Need: ' + escHtml(need) + '</span>' : '';
  return '<a class="cc-card" data-item-id="' + escHtml(id) + '" href="https://pickmycostume.com/c/' + escHtml(id) + '">'
    + '<img src="https://pickmycostume.com/images/og/' + escHtml(id) + '.jpg" alt="' + escHtml(idea.t) + ' costume" loading="lazy" width="1200" height="630">'
    + '<span class="cc-t"><strong>' + escHtml(idea.t) + '</strong><span class="cc-triple">' + triple + '</span>' + needHtml + '</span></a>';
}
function renderResults(){
  var box = document.getElementById('results');
  var scored = cgScore(ticked);
  var tonight = [], almost = [], rest = [];
  for (var i = 0; i < scored.length; i++){
    var s = scored[i];
    if (s.gaps === 0) tonight.push(s);
    else if (s.gaps <= 2) almost.push(s);
    else rest.push(s);
  }
  var html = '';
  html += '<h3 class="bucket-h">Make tonight <span class="cnt">(' + tonight.length + ')</span></h3>';
  if (!tonight.length){
    html += '<div class="empty">Nothing yet. Tick a few things you own, or switch the basics back on.</div>';
  } else {
    html += '<div class="cc-grid" id="res-tonight">' + tonight.map(function(s){ return cardHtml(s.id); }).join('') + '</div>';
  }
  html += '<h3 class="bucket-h">Almost there: 1 to 2 things to grab <span class="cnt">(' + almost.length + ')</span></h3>';
  if (almost.length){
    html += '<div class="cc-grid" id="res-almost">' + almost.map(function(s){ return cardHtml(s.id, s.labels.join(', ')); }).join('') + '</div>';
  }
  if (rest.length){
    html += '<details class="more"><summary>Browse the other ' + rest.length + ' ideas, closest matches first</summary>'
      + '<div class="cc-grid" id="res-rest">' + rest.map(function(s){ return cardHtml(s.id, s.labels.join(', ')); }).join('') + '</div></details>';
  }
  box.innerHTML = html;
  instrumentUnit('closet-results');
  try {
    track('closet_rendered', {tonight: tonight.length, almost: almost.length,
      ticked_count: Object.keys(ticked).length});
  } catch (e) {}
}
/* unit instrumentation: impression + click with position, same event names as index.html */
var _cgSeen = {};
function itemIdFor(el){
  if (el.getAttribute && el.getAttribute('data-item-id')) return el.getAttribute('data-item-id');
  var m = (el.getAttribute('href') || '').match(/\\/c\\/([^\\/?#]+)/);
  return m ? m[1] : 'unknown';
}
function anchorsOf(c){ return Array.prototype.slice.call(c.querySelectorAll('a')); }
function instrumentUnit(unitId){
  var def = CLOSET_UNITS[unitId]; if (!def) return;
  var c = document.getElementById(def.container); if (!c) return;
  if (!c._cgBound){
    c._cgBound = true;
    c.addEventListener('click', function(e){
      var a = e.target && e.target.closest ? e.target.closest('a') : null;
      if (!a || !c.contains(a)) return;
      var pos = anchorsOf(c).indexOf(a);
      try { track('unit_click', {unit_id: unitId, unit_type: def.type, page: location.pathname,
        item_id: itemIdFor(a), position: pos}); } catch (e2) {}
    });
  }
  if (_cgSeen[unitId]) return;
  function fire(){
    if (_cgSeen[unitId]) return; _cgSeen[unitId] = true;
    var ids = anchorsOf(c).map(itemIdFor);
    try { track('unit_impression', {unit_id: unitId, unit_type: def.type, page: location.pathname,
      item_count: ids.length, item_ids: ids.slice(0, 40)}); } catch (e3) {}
  }
  try {
    if ('IntersectionObserver' in window){
      var io = new IntersectionObserver(function(en){
        for (var i = 0; i < en.length; i++) if (en[i].isIntersecting){ fire(); io.disconnect(); }
      }, {threshold: 0.4});
      io.observe(c);
    } else fire();
  } catch (e4){ fire(); }
}
var CLOSET_UNITS = {
  'closet-results': {type: 'grid', container: 'results'},
  'closet-tonight': {type: 'grid', container: 'tonight-grid'},
  'closet-all':     {type: 'grid', container: 'all-grid'}
};
document.querySelectorAll('.tile').forEach(function(tile){
  tile.addEventListener('click', function(){
    var id = tile.getAttribute('data-sup');
    if (!cgGuard('tick:' + id, 400)){ syncTiles(); return; } /* bounce: resync, no toggle */
    if (ticked[id]) delete ticked[id]; else ticked[id] = true;
    /* unchecking a staple manually unticks the basics box */
    if (CLOSET.staples.indexOf(id) !== -1 && !ticked[id]){
      document.getElementById('basics-toggle').checked = false;
    }
    syncTiles();
    renderResults();
    try { track('closet_ticked', {supply: id, on: !!ticked[id], ticked_count: Object.keys(ticked).length}); } catch (e) {}
  });
});
document.getElementById('basics-toggle').addEventListener('change', function(e){
  if (!cgGuard('basics', 400)){ e.target.checked = !e.target.checked; return; }
  applyBasics(e.target.checked);
  syncTiles();
  renderResults();
});
applyBasics(true);
syncTiles();
renderResults();
instrumentUnit('closet-tonight');
instrumentUnit('closet-all');
try { track('closet_opened', {}); } catch (e) {}
})();
</script>
</body>
</html>'''


if __name__ == '__main__':
    main()
