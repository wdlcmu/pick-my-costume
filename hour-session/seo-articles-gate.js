/* SEO articles gate (2026-09-26): codifies the gates the SEO stream ran as
 * one-off commands when it built the 3 new ranking-content article pages.
 * See hour-session/seo-articles-2026-09-26.md.
 * 1. Sitemap gate: every <loc> in sitemap.xml resolves to a local file or the
 *    dynamic functions/c/[slug].js (160/160 expected).
 * 2. Hub/citation gate, per article page: costumes.html links to it and it
 *    links back; canonical present; no noindex/nosnippet; the 3 JSON-LD blocks
 *    parse with Article/FAQPage/HowTo types; FAQ questions+answers and HowTo
 *    steps all appear in the visible page text (never invent schema text the
 *    user cannot read); zero em/en dashes in visible copy (Billy's rule);
 *    the 60-second picker has a complete TABLE/POOL (every TABLE target in
 *    POOL, every POOL entry with title/triple/copy).
 * Exit 0 = pass, 1 = defects listed.
 */
var fs = require('fs');
var path = require('path');
var ROOT = path.join(__dirname, '..');

var ARTICLES = ['easy-last-minute-halloween-costumes.html',
  'cheap-halloween-costumes.html',
  'school-halloween-costumes.html',
  'easy-diy-halloween-costumes-for-kids.html',
  'couple-halloween-costumes-2026.html',
  'last-minute-halloween-costumes-2026.html',
  'halloween-costume-ideas-quiz.html'];

/* 2026-10-03: hub-link expectations after Billy's 2026-10-01 SEO consolidation
 * (hidden_files/seo/proposed-301-map-2026-10-01.md, "Ship all 15"; amended per
 * his redirect-intent review). Three articles were retired via live 301s and
 * their internal links (costumes.html included) were updated to the canonicals
 * as part of the shipped consolidation: the hub must link the LIVE canonical,
 * never a retired source. /cheap-halloween-costumes was UN-RETIRED (big search
 * term, distinct intent; still in sitemap, live HTTP 200) so the hub keeps the
 * direct article link. /halloween-costume-ideas-quiz was retired to / (the
 * homepage): no hub link is asserted for it. */
var HUB_LINK = {
  'easy-last-minute-halloween-costumes.html': 'last-minute-costumes',
  'cheap-halloween-costumes.html': 'cheap-halloween-costumes',
  'school-halloween-costumes.html': 'school-halloween-costumes',
  'easy-diy-halloween-costumes-for-kids.html': 'easy-diy-halloween-costumes-for-kids',
  'couple-halloween-costumes-2026.html': 'couples-costumes',
  'last-minute-halloween-costumes-2026.html': 'last-minute-costumes',
  'halloween-costume-ideas-quiz.html': null
};

var fails = [];
function ok(c, m){ if (!c) fails.push(m); }

/* Non-tree routes that are served by Cloudflare worker routes, not Pages files. */
var WORKER_ROUTES = {
  '/mcp': 'pick-my-costume-mcp worker (hour-session/chatgpt-directory-prep-2026-09-26.md: /mcp verified live)',
};

function unesc(s){
  return s.replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>')
          .replace(/&quot;/g,'"').replace(/&#39;/g,"'");
}
function visibleText(html){
  var v = html.replace(/<style[\s\S]*?<\/style>/g,'')
              .replace(/<script[\s\S]*?<\/script>/g,'')
              .replace(/<[^>]+>/g,' ');
  return unesc(v).replace(/\s+/g,' ');
}
function ldBlocks(html){
  var out = [], re = /<script type="application\/ld\+json">([\s\S]*?)<\/script>/g, m;
  while ((m = re.exec(html))){
    try { out.push(JSON.parse(m[1])); }
    catch (e){ fails.push('JSON-LD block does not parse: ' + e.message); out.push(null); }
  }
  return out.filter(Boolean);
}

/* ---------- 1. Sitemap: every loc resolves ---------- */
var sm = fs.readFileSync(path.join(ROOT,'sitemap.xml'),'utf8');
var locs = sm.match(/<loc>([^<]*)<\/loc>/g) || [];
var total = 0, missing = [];
locs.forEach(function(l){
  var u = l.replace(/<\/?loc>/g,'').trim();
  if (!/^https:\/\/pickmycostume\.com(\/|$)/.test(u)) { missing.push(u); return; }
  var p = u.replace('https://pickmycostume.com','');
  total++;
  if (WORKER_ROUTES[p]) return; /* served by a Cloudflare worker route */
  var file = null;
  if (p === '/' || p === '') file = 'index.html';
  else if (/^\/c\/[a-z0-9-]+$/.test(p)){
    if (fs.existsSync(path.join(ROOT,'functions','c','[slug].js'))) return; /* dynamic */
    missing.push(u); return;
  }
  /* 2026-10-03 (S67): /map/ region pages are served by the Pages Function
     functions/map/[[path]].js (embeds map.html at build time); verified live
     2026-10-03 (/map/ and /map/dinosaur-land both HTTP 200) and function file
     present in tree. */
  else if (/^\/map(\/[a-z0-9-]+)?\/?$/.test(p)){
    if (fs.existsSync(path.join(ROOT,'functions','map','[[path]].js'))) return; /* dynamic */
    missing.push(u); return;
  }
  else if (/^\/collections\/[a-z0-9-]+$/.test(p)) file = p.slice(1) + '.html';
  else if (/^\/[a-z0-9-]+$/.test(p)) file = p.slice(1) + '.html';
  else { missing.push(u + ' (unmapped shape)'); return; }
  if (!fs.existsSync(path.join(ROOT,file))) missing.push(u + ' -> ' + file);
});
ok(missing.length === 0, 'sitemap URLs with no local target: ' + missing.slice(0,5).join('; '));
/* 2026-10-03 (S67): sitemap grew 169 -> 206 as the bank grew (138 -> 164 ideas) plus new intent/collection and /map/ region pages. Verified live 2026-10-03: curl https://pickmycostume.com/sitemap.xml -> HTTP 200 with 206 <url> entries; local tree sitemap.xml also 206 (164 /c/ bank-idea pages + 42 structural/intent//map/ pages). Expectation updated to match verified reality.
   2026-10-03 (S63 bank+5): sitemap now 217 (169 /c/ bank-idea pages + 48 structural/intent//map/ pages; 6 structural pages added since the 206 count). */
ok(total === 217, 'sitemap URL count changed: ' + total + ' (expected 217: 169 bank-idea /c/ pages + 48 structural/intent//map/ pages)');
if (!fails.length) console.log('sitemap: ' + total + '/' + total + ' URLs resolve');

/* ---------- 2. Hub/citation per article ---------- */
var hub = fs.readFileSync(path.join(ROOT,'costumes.html'),'utf8');
ARTICLES.forEach(function(a){
  var slug = a.replace(/\.html$/,'');
  var f = path.join(ROOT,a);
  if (!fs.existsSync(f)){ fails.push(a + ': FILE MISSING in tree'); return; }
  var html = fs.readFileSync(f,'utf8');
  var want = HUB_LINK[a];
  if (want){
    var isCanonical = want !== slug;
    ok(hub.indexOf('href="/' + want + '"') >= 0 || hub.indexOf('href="/' + want + '.html"') >= 0,
       a + (isCanonical
            ? ': hub does not link to live canonical /' + want + ' (article retired 2026-10-01, see HUB_LINK)'
            : ': hub does not link to article'));
  }
  ok(/href="(https?:\/\/pickmycostume\.com)?\/costumes/.test(html), a + ': no backlink to /costumes');
  ok(/<link rel="canonical" href="https:\/\/pickmycostume\.com\/[a-z0-9-]+"/.test(html),
     a + ': canonical missing or wrong');
  ok(!/noindex|nosnippet/i.test(html), a + ': noindex/nosnippet present');
  var blocks = ldBlocks(html);
  var types = blocks.map(function(b){ return b['@type']; });
  ['Article','FAQPage','HowTo'].forEach(function(t){
    ok(types.indexOf(t) >= 0, a + ': JSON-LD missing ' + t);
  });
  var vis = visibleText(html);
  var faq = blocks.filter(function(b){ return b['@type'] === 'FAQPage'; })[0];
  var how = blocks.filter(function(b){ return b['@type'] === 'HowTo'; })[0];
  if (faq){
    (faq.mainEntity || []).forEach(function(e){
      ok(vis.indexOf(unesc(e.name)) >= 0, a + ': FAQ question not in visible text: ' + e.name);
      var ans = (e.acceptedAnswer && e.acceptedAnswer.text) || '';
      ok(!ans || vis.indexOf(unesc(ans)) >= 0, a + ': FAQ answer not in visible text: ' + e.name);
    });
  }
  if (how){
    (how.step || []).forEach(function(s){
      var t = (s && typeof s === 'object') ? s.text : s;
      ok(!t || vis.indexOf(unesc(t)) >= 0, a + ': HowTo step not in visible text: ' + String(t).slice(0,40));
    });
  }
  ok(!/[—–]/.test(vis), a + ': em/en dash in visible copy');
  var poolM = /var POOL = (\{[\s\S]*?\});/.exec(html);
  var tableM = /var TABLE = (\{[\s\S]*?\});/.exec(html);
  ok(!!poolM && !!tableM, a + ': picker POOL/TABLE missing');
  if (poolM && tableM){
    var POOL = JSON.parse(poolM[1]), TABLE = JSON.parse(tableM[1]);
    var keys = Object.keys(TABLE);
    /* 2026-09-27: couple article runs a 3x3 vibe x time-budget grid (9 combos,
       all build-time asserted); the other articles run 3x2 (6). Both shapes
       are complete, so the gate accepts either.
       2026-10-03 (S67): cheap-halloween-costumes.html redesigned its picker to
       a single audience question ("Who is it for?" -> Just me / My kid /
       A group of us; visible copy line 242, TABLE keys me/kid/group). The
       TABLE/POOL completeness checks below still run unchanged; the shape
       assertion now also accepts the documented 3-audience picker. */
    ok(keys.length === 3 || keys.length === 6 || keys.length === 9,
       a + ': picker TABLE has ' + keys.length + ' combos (expected 3, 6, or 9)');
    keys.forEach(function(k){
      ok(POOL[TABLE[k]], a + ': TABLE[' + k + '] target not in POOL');
    });
    Object.keys(POOL).forEach(function(p){
      ok(POOL[p].t && POOL[p].triple && POOL[p].copy, a + ': POOL[' + p + '] missing t/triple/copy');
    });
  }
  if (!fails.length) console.log('article ok: ' + a);
});

if (fails.length){ console.error('SEO ARTICLES GATE FAIL (' + fails.length + '):\n - ' + fails.join('\n - ')); process.exit(1); }
console.log('SEO ARTICLES GATE PASS');
