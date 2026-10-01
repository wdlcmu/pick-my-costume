#!/usr/bin/env python3
"""Generate functions/map/[[path]].js from galaxy-data.json (per-URL og meta for /map/*).

The function serves map.html with og:title/og:description/og:image/og:url
replaced per path segment, so /map/food-court and /map/food-court/pizza-slice
unfurl with their own previews in chat apps.

§4b SEO (2026-10-01): for /map/<region> pages the function ALSO injects,
server-side (so it is in the served HTML, not JS-only):
  - search-term-led <title> and <meta name="description"> (<=155 chars),
  - a per-region canonical (region pages must index on their own URL),
  - a static region header block: kicker subtitle + H1 + "Quick answer"
    paragraph (3 named costumes with build time + key material, each linking
    to its /c/<slug> guide),
  - ItemList + BreadcrumbList JSON-LD listing the region's costumes.

Usage: python3 hidden_files/galaxy/build_map_function.py
Output: functions/map/[[path]].js  (both files are checked in, like
         build_party.py -> party.js)
"""
import html
import json
import pathlib

ROOT = pathlib.Path('/home/hatch/workspace/builds/pick-my-costume')
GX = ROOT / 'hidden_files' / 'galaxy'

data = json.loads((GX / 'galaxy-data.json').read_text(encoding='utf-8'))
idea_ids = {i['id'] for i in data['ideas']}
ideas_by_id = {i['id']: i for i in data['ideas']}
assert len(data['ideas']) == 164

# map.html is embedded at build time (see MAP_HTML in the JS template). We do
# NOT fetch it from ASSETS at request time: the account's pretty-URL rule
# 308s every *.html request to its extensionless form, so an internal
# ASSETS.fetch("/map.html") returns "308 Location: /map", which the old code
# returned to the client verbatim -> infinite /map redirect loop (outage
# 2026-10-01, caused by the Section 2 regen). The embedded copy also freezes
# the exact map.html the meta injection was built against.
map_html = (ROOT / 'map.html').read_text(encoding='utf-8')
assert '<meta property="og:title"' in map_html, 'map.html missing og meta for injection'
assert len(map_html) > 50000, f'map.html suspiciously small ({len(map_html)} bytes)'
assert '<link rel="canonical" href="https://pickmycostume.com/map/">' in map_html, \
    'map.html canonical tag changed; update the §4b injection'
assert map_html.count('</head>') == 1, 'expected exactly one </head> for JSON-LD insert'

# The generic page header block, replaced per region with the search-led H1 +
# static quick answer. Extracted (not hardcoded) so a map.html header edit
# fails loudly here instead of silently shipping the generic header.
_hs = map_html.index('<header class="page-head">')
_he = map_html.index('</header>', _hs) + len('</header>')
PAGE_HEAD_DEFAULT = map_html[_hs:_he]
assert map_html.count(PAGE_HEAD_DEFAULT) == 1, 'page-head block not unique'

# Per-region SEO. Order matches data['regions'] (cluster id == list index).
# title: search-term-led <title>; meta: <=155 chars (asserted below);
# quick: 3 flagship-ish costumes as (slug, key material) -- names and times
# are pulled from galaxy-data.json (single source of truth), material phrases
# are hand-written from the blurbs and verified by eye 2026-10-01.
REGIONS = [
    dict(slug='dinosaur-land', name='Dinosaur Land',
         syn='Stomp, roar, repeat \u2014 Jurassic joy for every age.', flag='baby-dino',
         kicker='Dinosaur Land', h1='Dinosaur Costume Ideas',
         title='10 DIY Dinosaur Costume Ideas (Baby Dino, Raptor, Family) | Pick My Costume',
         meta='10 DIY dinosaur costume ideas, from a 10-minute dino tourist to a full dino family. Felt spikes, hoodies and free step-by-step guides.',
         quick=[('baby-dino', 'green hoodie, felt spikes, stuffed tail'),
                ('dino-tourist', 'Hawaiian shirt, dino tail, fanny pack'),
                ('raptor-barista', 'dino snout hood, tiny T. rex arms')]),
    dict(slug='food-court', name='Food Court',
         syn='Dress as dinner. The tastiest corner of the galaxy.', flag='pizza-slice',
         kicker='The Food Court', h1='Food Costume Ideas',
         title='31 DIY Food Costume Ideas (Pizza, Taco, Couples) | Pick My Costume',
         meta='31 DIY food costume ideas \u2014 pizza, taco, sushi, donut and more. Most build in under 30 minutes with cardboard and felt. Free guides.',
         quick=[('pizza-slice', 'cardboard triangle, felt pepperoni'),
                ('banana', 'yellow sweatsuit, green felt stem hat'),
                ('ketchup-mustard', 'red and yellow bottle tunics')]),
    dict(slug='princess-castle', name='Princess Castle',
         syn='Tiaras, fairy wings, and happily-ever-after.', flag='fairy-tale-princesses',
         kicker='Princess Castle', h1='Princess & Fairy Tale Costume Ideas',
         title='13 DIY Princess & Fairy Tale Costume Ideas | Pick My Costume',
         meta='13 princess and fairy tale costume ideas \u2014 royal gowns, fairies, witches and mermaids. Most take 20 minutes or less. Free step-by-step guides.',
         quick=[('fairy-tale-princesses', 'a dress or crown from the closet'),
                ('prince-princess', 'crown and cape, thrifted gown and tiara'),
                ('garden-fairy', 'tulle wings, flower crown, wand')]),
    dict(slug='fright-night', name='Fright Night',
         syn='Ghosts, ghouls, and things that go bump.', flag='classic-ghost',
         kicker='Fright Night', h1='Scary DIY Halloween Costumes',
         title='18 Scary DIY Halloween Costumes (Ghost, Vampire, Zombie) | Pick My Costume',
         meta='18 scary DIY Halloween costumes \u2014 classic ghost, vampire, zombie coworker and more. Most take 30 minutes or less. Free build guides.',
         quick=[('classic-ghost', 'white sheet, cut-out eyes'),
                ('vampire', 'black cape, fangs'),
                ('zombie-coworker', 'torn button-down, pale makeup')]),
    dict(slug='hero-headquarters', name='Hero Headquarters',
         syn='Capes on. Time to save Halloween.', flag='superhero-family',
         kicker='Hero Headquarters', h1='Superhero Costume Ideas',
         title='12 DIY Superhero Costume Ideas (Family, Kids & Groups) | Pick My Costume',
         meta='12 DIY superhero costume ideas \u2014 capes, masks and family teams. Most build in 30 minutes or less. Free step-by-step guides.',
         quick=[('superhero-family', 'red sweatsuits, black eye masks, felt logo'),
                ('backyard-hero', 'short cape, first initial on the chest'),
                ('cardboard-knight', 'silver-painted cardboard armor, pool-noodle sword')]),
    dict(slug='animal-kingdom', name='Animal Kingdom',
         syn='Go wild \u2014 from buzzing bees to big jungle energy.', flag='bumble-bee',
         kicker='Animal Kingdom', h1='Animal Costume Ideas',
         title='16 DIY Animal Costume Ideas (Bee, Lion, Shark & More) | Pick My Costume',
         meta='16 DIY animal costume ideas \u2014 bumble bee, little lion, shark and more. Easy builds, mostly 30 minutes or less. Free guides.',
         quick=[('bumble-bee', 'black sweats, yellow tape stripes, felt antennae'),
                ('little-lion', 'tan sweatsuit, fuzzy mane hood'),
                ('cat-mouse', 'cat ears versus mouse ears')]),
    dict(slug='sports-arena', name='Sports Arena',
         syn='Game on \u2014 the MVPs of the costume world.', flag='soccer-squad',
         kicker='Sports Arena', h1='Sports Costume Ideas',
         title='8 DIY Sports Costume Ideas (Soccer, Basketball & More) | Pick My Costume',
         meta='8 DIY sports costume ideas \u2014 soccer squad, basketball star, boxer and more. All easy, most under 25 minutes. Free guides.',
         quick=[('soccer-squad', 'jerseys, black for the ref, one red card'),
                ('basketball-star', 'jersey, eye-black stripes'),
                ('referee', 'striped shirt, whistle, yellow penalty flag')]),
    dict(slug='pop-culture-plaza', name='Pop Culture Plaza',
         syn='Screen legends, memes, and main characters.', flag='mystery-crew',
         kicker='Pop Culture Plaza', h1='Pop Culture Costume Ideas',
         title='32 DIY Pop Culture Costume Ideas (Movies, Memes & Games) | Pick My Costume',
         meta='32 DIY pop culture costume ideas \u2014 movie icons, memes, video games and more. Free step-by-step guides, most under 45 minutes.',
         quick=[('mystery-crew', 'leader, style icon, brains, goofball, one good dog'),
                ('goggle-crew', 'yellow tees, denim overalls, goggles'),
                ('neon-demon-hunter', 'streetwear, glowing sigils, foam sword')]),
    dict(slug='silly-street', name='Silly Street',
         syn='Pure silliness, zero scares.', flag='moth-porch-light',
         kicker='Silly Street', h1='Funny DIY Halloween Costumes',
         title='24 Funny DIY Halloween Costumes (Silly, Easy & Last-Minute) | Pick My Costume',
         meta='24 funny DIY Halloween costumes \u2014 moth and porch light, error 404, party pinata. Easy builds, several in 10 minutes. Free guides.',
         quick=[('moth-porch-light', 'cardboard wings / yellow and a lampshade'),
                ('error-404', 'all black, blank white page'),
                ('party-pinata', 'cardboard box, rainbow fringe')]),
]
assert len(REGIONS) == 9

# Verify against galaxy-data.json: order == cluster ids, flagship ids exist,
# names/counts match, quick-answer costumes exist with their data time
# (names + times are the single source of truth; never re-typed).
data_regions = {r['name']: r for r in data['regions']}
total = 0
for idx, r in enumerate(REGIONS):
    assert r['flag'] in idea_ids, f"flagship {r['flag']} missing from ideas"
    assert r['name'] in data_regions, f"region name {r['name']!r} missing from data"
    assert data['regions'][idx]['name'] == r['name'], 'REGIONS order != cluster order'
    count = data_regions[r['name']]['count']
    assert count == sum(1 for i in data['ideas'] if i['cluster'] == idx), \
        f"{r['name']}: data count {count} != idea rows"
    total += count
    assert len(r['meta']) <= 155, f"{r['slug']}: meta {len(r['meta'])} chars > 155"
    assert len(r['quick']) == 3, f"{r['slug']}: quick answer needs exactly 3 costumes"
    for slug, _material in r['quick']:
        assert slug in idea_ids, f"quick {slug} missing from ideas"
        assert ideas_by_id[slug].get('time'), f"quick {slug} has no time in data"
    r['count'] = count
assert total == 164, f'region idea total {total} != 164'


def live_title(iid):
    # Live-bank title override (the galaxy-data.json copy renamed it).
    return 'Pumpkin King and Stitched Bride' if iid == 'pumpkin-king-bride' \
        else ideas_by_id[iid]['title']


def quick_sentence(r):
    # 3 named costumes + build time + key material, each linking to /c/<slug>.
    bits = []
    for slug, material in r['quick']:
        bits.append('<a href="/c/%s">%s</a> (%s; %s)' % (
            slug, html.escape(live_title(slug)),
            html.escape(ideas_by_id[slug]['time']), html.escape(material)))
    return 'start with the ' + ', the '.join(bits[:-1]) + ', or the ' + bits[-1] + '.'


def region_head(r):
    # Static region header: subtitle kicker + search-led H1 + quick answer.
    # Served in the HTML by the function (not JS-only). Reuses the page-head
    # classes so no new CSS is needed.
    return ('<header class="page-head">\n'
            '  <p class="kicker">' + html.escape(r['kicker']) + '</p>\n'
            '  <h1>' + html.escape(r['h1']) + '</h1>\n'
            '  <p class="lede"><strong>Quick answer:</strong> ' + quick_sentence(r) +
            ' Every costume below links to a free step-by-step build guide.</p>\n'
            '</header>')


def region_ld(r, idx):
    # ItemList (region costumes -> /c/ guides) + BreadcrumbList.
    members = [i['id'] for i in data['ideas'] if i['cluster'] == idx]
    assert len(members) == r['count']
    ld = {
        '@context': 'https://schema.org',
        '@graph': [
            {'@type': 'BreadcrumbList', 'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': 'Pick My Costume',
                 'item': 'https://pickmycostume.com/'},
                {'@type': 'ListItem', 'position': 2, 'name': 'Costume Galaxy',
                 'item': 'https://pickmycostume.com/map/'},
                {'@type': 'ListItem', 'position': 3, 'name': r['name'],
                 'item': 'https://pickmycostume.com/map/' + r['slug']},
            ]},
            {'@type': 'ItemList', 'name': '%d %s' % (r['count'], r['h1']),
             'numberOfItems': r['count'], 'itemListElement': [
                 {'@type': 'ListItem', 'position': n + 1,
                  'name': live_title(iid),
                  'url': 'https://pickmycostume.com/c/' + iid}
                 for n, iid in enumerate(members)]},
        ],
    }
    return '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=True) + '</script>'


regions_js = {}
for idx, r in enumerate(REGIONS):
    regions_js[r['slug']] = {
        'name': r['name'], 'syn': r['syn'], 'img': r['flag'], 'count': r['count'],
        'seoTitle': r['title'], 'seoDesc': r['meta'],
        'head': region_head(r), 'ld': region_ld(r, idx),
    }

# Compact idea table: id -> {t: title, b: blurb}, with the live bank title
# (the galaxy-data.json copy renamed it; the live bank keeps
# 'Pumpkin King and Stitched Bride').
ideas_js = {}
for i in data['ideas']:
    title = i['title']
    if i['id'] == 'pumpkin-king-bride':
        title = 'Pumpkin King and Stitched Bride'
    ideas_js[i['id']] = {'t': title, 'b': i['blurb']}
assert ideas_js['pumpkin-king-bride']['t'] == 'Pumpkin King and Stitched Bride'

GEN_TITLE = 'Costume Galaxy: explore all 164 costumes | Pick My Costume'
GEN_DESC = ('All 164 Halloween costume ideas as an explorable galaxy \u2014 9 worlds '
            'from Dinosaur Land to Food Court. Zoom in, tap a costume, open the '
            'free DIY build guide.')
GEN_IMG = 'https://pickmycostume.com/images/og/blue-dog-family.jpg'
GEN_URL = 'https://pickmycostume.com/map/'

js = '''// Per-URL og injection for /map region + costume deep links.
// Regenerate with: python3 hidden_files/galaxy/build_map_function.py (emits this
// file from galaxy-data.json -- do not hand-edit the tables).
//
// map.html is a static file, so every shared /map/* URL would unfurl in chat
// apps with the same generic preview ("Costume Galaxy: explore all 164
// costumes" / blue-dog-family image). Per-region and per-costume
// og:title/og:description/og:image/og:url are injected here, server-side, on
// the fetch path. Unknown regions, unknown costume ids, and /map itself fall
// through to the generic asset meta.
//
// §4b SEO (2026-10-01): /map/<region> pages additionally get, server-side:
// search-led <title> + <meta name="description">, a per-region canonical, a
// static region header (kicker subtitle + H1 + "Quick answer" paragraph with
// 3 named /c/<slug> costume links), and ItemList + BreadcrumbList JSON-LD.
//
// The page HTML is EMBEDDED at build time (var MAP_HTML below), NOT fetched
// from ASSETS: the account's pretty-URL rule 308s every *.html request to its
// extensionless form, so ASSETS.fetch("/map.html") returns a 308
// Location:/map that leaks to the client as an infinite redirect loop
// (outage 2026-10-01). Never fetch map.html from ASSETS here.
// The embedded copy keeps query params (?probe=) passing through untouched.
//
// Mirrors the /party pattern: region/idea table -> esc() -> og meta values ->
// Response. The difference is a table lookup keyed by the URL path segments
// instead of a query token. All methods share the embedded-HTML path (there
// is no static asset at /map/*, only /map.html which the pretty-URL rule
// redirects, so an ASSETS passthrough would 404/308 instead of serving).

// Embedded copy of map.html at build time (see header note). Do not replace
// with ASSETS.fetch.
var MAP_HTML = /*__MAP_HTML__*/;

// (tables emitted by build_map_function.py from galaxy-data.json -- see header)
var MAP_REGIONS = %s;

var MAP_IDEAS = %s;

// Generic meta: the same preview map.html ships with.
var DEFAULT_OG_TITLE = %s;
var DEFAULT_OG_DESCRIPTION = %s;
var DEFAULT_OG_IMAGE = %s;
var DEFAULT_OG_URL = %s;

// The generic page-head block in map.html, replaced per region (server-side)
// with the search-led H1 + static quick answer. Extracted by the generator;
// if map.html's header ever changes shape, the generator fails loudly instead
// of shipping the generic header on region pages.
var PAGE_HEAD_DEFAULT = %s;

// Same esc() as /c/[slug].js: these values land inside meta content="".
function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
                  .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// Replace the value of one meta tag, matched by tag identity (property/name
// + content attribute). If map.html's copy changes, the match still holds;
// if the tag ever disappears, this is a silent no-op (generic stays).
function setMeta(html, attr, value) {
  var re = new RegExp("<meta " + attr + ' content="[^"]*">');
  return html.replace(re, "<meta " + attr + ' content="' + value + '">');
}

// Replace the <title> element. Exactly one <title>...</title> exists in
// map.html (the only other "<title>" is a JS comment with no closing tag).
function setTitle(html, value) {
  return html.replace(/<title>[^<]*<\\/title>/, "<title>" + value + "</title>");
}

// Point the canonical at the region URL. A canonical to /map/ on every
// region page would tell Google they are duplicates of /map/ and keep them
// out of the index -- defeating the §4b SEO work.
function setCanonical(html, value) {
  return html.replace(/<link rel="canonical" href="[^"]*">/,
                      '<link rel="canonical" href="' + value + '">');
}

export async function onRequest(context) {
  var url;
  try {
    url = new URL(context.request.url);
  } catch (e) {
    // Unparseable URL: serve the generic galaxy page rather than erroring.
    return new Response(MAP_HTML, {
      headers: {
        "Content-Type": "text/html;charset=utf-8",
        "Cache-Control": "max-age=0, must-revalidate"
      }
    });
  }

  var segs = url.pathname.split("/").filter(function(s){ return s; });
  // segs: ["map"] | ["map", region] | ["map", region, costume]
  var region = segs.length > 1 ? segs[1].toLowerCase() : "";
  var costume = segs.length > 2 ? segs[2].toLowerCase() : "";
  var rg = MAP_REGIONS[region] || null;

  var title = DEFAULT_OG_TITLE;
  var desc = DEFAULT_OG_DESCRIPTION;
  var img = DEFAULT_OG_IMAGE;
  var ogurl = DEFAULT_OG_URL;

  if (rg) {
    title = rg.name + " \\u2014 Costume Galaxy | Pick My Costume";
    desc = rg.syn + " " + rg.count + " costume ideas to explore.";
    img = "https://pickmycostume.com/images/og/" + rg.img + ".jpg";
    ogurl = "https://pickmycostume.com/map/" + region;
    var idea = costume ? MAP_IDEAS[costume] : null;
    if (idea) {
      title = idea.t + " | Costume Galaxy \\u2014 Pick My Costume";
      desc = idea.b;
      img = "https://pickmycostume.com/images/og/" + costume + ".jpg";
      ogurl = "https://pickmycostume.com/map/" + region + "/" + costume;
    }
    // Unknown costume id: the region meta stands.
  }
  // Unknown region (or /map itself): the generic meta stands.

  var rewritten = new URL(url);
  // NOTE: do NOT ASSETS.fetch("/map.html") here -- the pretty-URL rule 308s
  // it (see header). The embedded build-time copy is the page.
  var html = MAP_HTML;

  html = setMeta(html, 'property="og:title"', esc(title));
  html = setMeta(html, 'name="twitter:title"', esc(title));
  html = setMeta(html, 'property="og:description"', esc(desc));
  html = setMeta(html, 'name="twitter:description"', esc(desc));
  html = setMeta(html, 'property="og:image"', img);
  html = setMeta(html, 'name="twitter:image"', img);
  html = setMeta(html, 'property="og:url"', ogurl);

  // §4b region-page SEO (served HTML, not JS-only). Costume deep links keep
  // the idea og unfurl above; only bare /map/<region> gets the SEO block.
  if (rg && !costume) {
    html = setTitle(html, esc(rg.seoTitle));
    html = setMeta(html, 'name="description"', esc(rg.seoDesc));
    html = setCanonical(html, ogurl);
    html = html.split(PAGE_HEAD_DEFAULT).join(rg.head);
    html = html.replace("</head>", rg.ld + "</head>");
  }

  return new Response(html, {
    headers: {
      "Content-Type": "text/html;charset=utf-8",
      "Cache-Control": "max-age=0, must-revalidate"
    }
  });
}
/* 2026-10-01: Cache-Control is max-age=0, must-revalidate (P0 fix 2026-10-01,
   commit 1e29b9dd). Do NOT raise max-age here; the Galaxy page must never
   serve stale. */
''' % (
    json.dumps(regions_js, ensure_ascii=True, indent=2),
    json.dumps(ideas_js, ensure_ascii=True),
    json.dumps(GEN_TITLE, ensure_ascii=True),
    json.dumps(GEN_DESC, ensure_ascii=True),
    json.dumps(GEN_IMG, ensure_ascii=True),
    json.dumps(GEN_URL, ensure_ascii=True),
    json.dumps(PAGE_HEAD_DEFAULT, ensure_ascii=True),
)

# Insert the embedded map.html via token replace (not % formatting: the HTML
# contains literal % characters that would need escaping).
assert '/*__MAP_HTML__*/' in js, 'MAP_HTML token missing from JS template'
js = js.replace('/*__MAP_HTML__*/', json.dumps(map_html, ensure_ascii=False))
assert '/*__MAP_HTML__*/' not in js

out = ROOT / 'functions' / 'map' / '[[path]].js'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(js, encoding='utf-8')
print(f'wrote {out} ({len(js)} bytes, {len(regions_js)} regions, {len(ideas_js)} ideas, map.html embedded {len(map_html)} bytes)')
