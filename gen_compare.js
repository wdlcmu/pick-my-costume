/* gen_compare.js — generates the dynamic /compare page.
 *
 * Build flow: node gen_compare.js
 * Output: compare.html at repo root (staged; NOT deployed).
 *
 * What changed 2026-09-30: the page used to be a static 4-costume table.
 * It is now a dynamic head-to-head tool: a search-first picker (2 to 3
 * costumes, hard cap 3), shareable ?vs= URLs via history.replaceState, a swap
 * button for 2-costume matchups, and the same bank-derived rows per card.
 * The default matchup (Classic Ghost vs Classic Vampire) is server-rendered
 * by the generator so crawlers see a real comparison; the client JS hydrates
 * the picker on top. Pure renderers live in compare-app.js and are shared
 * between Node (this generator) and the browser, so static and dynamic
 * output can never drift.
 *
 * Row derivation (the 2026-09-30 ghost fix): a material counts as
 * "Use from home" when its enriched stash groups (pantry.html DATA.ideas,
 * the same mapping the live pantry page uses) are ALL covered by the
 * pantry's assumed staples (DATA.pantry, the user-facing contract), or when
 * the bank marks it (own)/(make). Derived at generator time, so pantry
 * reconciliations are picked up on regen. The old marker-only derivation
 * left "Use from home: None" for the ghost; the generator asserts
 * classic-ghost now has home items.
 *
 * Visible copy rule: no em/en dashes anywhere (redteam-distro-hubs gate).
 */
'use strict';
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const DEFAULT_IDS = ['classic-ghost', 'vampire'];
const MAXPICK = 3;

/* ---------------- load bank ---------------- */
/* 2026-10-22 parser fix (generator parity audit, Family D): the old
   extractors anchored on a newline terminator ("\n];" / "\n};"), which
   matched the bank's old pretty-printed layout. INSTRUCTIONS is now one
   giant line that ends "}};" on the same line, so the "\n};" search
   skipped its real terminator and captured ~50 KB of following code
   (MAKE_PLANS and beyond); the eval then died with
   "SyntaxError: Unexpected token ';'" at the captured ';'. IDEAS still
   ends in "\n];" by luck, not by contract. All three bank literals are
   now read with one balanced scan from the opening bracket — the same
   approach as the working gen_question_pages.js extractor — hardened to
   ignore brackets inside quoted strings, so a bracket in costume copy
   cannot end a literal early. */
function extractLiteral(src, decl, openCh, closeCh) {
  const start = src.indexOf(decl);
  if (start < 0) throw new Error(decl + 'not found in app.js');
  const open = src.indexOf(openCh, start);
  if (open < 0) throw new Error(decl + 'has no opening ' + openCh + ' in app.js');
  let depth = 0, quote = null, esc = false, end = -1;
  for (let i = open; i < src.length; i++) {
    const ch = src[i];
    if (quote) {
      if (esc) esc = false;
      else if (ch === '\\') esc = true;
      else if (ch === quote) quote = null;
      continue;
    }
    if (ch === '"' || ch === "'") { quote = ch; continue; }
    if (ch === openCh) depth++;
    else if (ch === closeCh) { depth--; if (!depth) { end = i; break; } }
  }
  if (end < 0) throw new Error(decl + 'unbalanced in app.js');
  return eval('(' + src.slice(open, end + 1) + ')');
}
function extractVar(src, name) {
  return extractLiteral(src, 'var ' + name + ' = ', '[', ']');
}
function extractObj(src, name) {
  return extractLiteral(src, 'var ' + name + ' = ', '{', '}');
}
const indexHtml = fs.readFileSync(path.join(ROOT, 'app.js'), 'utf8');
const IDEAS = extractVar(indexHtml, 'IDEAS');
const INS = extractObj(indexHtml, 'INSTRUCTIONS');
/* PINPOINT_MAP is a single giant line ending "},};" — same balanced scan. */
function extractBalanced(src, decl) {
  return extractLiteral(src, decl, '{', '}');
}
const PINPOINT = extractBalanced(indexHtml, 'var PINPOINT_MAP = ');
const byId = {};
IDEAS.forEach(i => { byId[i.id] = i; });

/* ---------------- load pantry stash catalog (assumed staples) ----------------
 * pantry.html DATA is the live contract: DATA.pantry is the stash catalog
 * (array of {id,label,group,staple}), and DATA.ideas[].mats[] is the
 * enriched per-material mapping {t, g} where t is the bank material text
 * with its trailing (buy|make|own) marker stripped and g is the list of
 * alternative stash-id groups ([[null]] = unmapped). We align by
 * stripMarker(bankText) === t. Materials with no enriched entry fall back
 * to marker-only classification (honest, never invented). */
const pantryHtml = fs.readFileSync(path.join(ROOT, 'pantry.html'), 'utf8');
const dataStart = pantryHtml.indexOf('const DATA = ');
if (dataStart < 0) throw new Error('const DATA = not found in pantry.html');
let brace = pantryHtml.indexOf('{', dataStart), depth = 0, end = brace;
for (; end < pantryHtml.length; end++) {
  const ch = pantryHtml[end];
  if (ch === '{') depth++;
  else if (ch === '}') { depth--; if (!depth) break; }
}
const DATA = JSON.parse(pantryHtml.slice(brace, end + 1));
const CATALOG = {};
const STAPLES = new Set();
DATA.pantry.forEach(item => {
  CATALOG[item.id] = item;
  if (item.staple) STAPLES.add(item.id);
});
if (!STAPLES.size) throw new Error('no staples found in pantry.html DATA');
const ENRICHED = {};
DATA.ideas.forEach(entry => {
  const map = {};
  (entry.mats || []).forEach(mt => { map[mt.t] = mt.g; });
  ENRICHED[entry.id] = map;
});

/* ---------------- load compare-app.js pure renderers ---------------- */
const appSrc = fs.readFileSync(path.join(ROOT, 'compare-app.js'), 'utf8');
if (!/function cmpCard\(d\)/.test(appSrc)) throw new Error('compare-app.js missing cmpCard');
if (!/typeof window !== 'undefined'/.test(appSrc)) throw new Error('compare-app.js missing window guard');
const APP = new Function(appSrc + '\nreturn {cmpCards:cmpCards,cmpH2:cmpH2,cmpBluf:cmpBluf,cmpTradeoffs:cmpTradeoffs};')();

/* ---------------- material derivation ---------------- */
function classifyMaterial(m) {
  const hasBuy = /\bbuy\b/i.test(m);
  const hasMake = /\bmake\b/i.test(m);
  const hasOwn = /\bown\b/i.test(m);
  if (hasOwn && !hasBuy) return 'own';
  if (hasMake && !hasBuy) return 'make';
  if (hasBuy && !hasMake && !hasOwn) return 'buy';
  if (hasBuy && (hasMake || hasOwn)) return 'either';
  return 'unmarked';
}
function stripMarker(m) {
  return m.replace(/\s*\((buy|make|own)[^)]*\)\s*$/i, '').trim();
}
/* condensed buy-name port of pantry.html shortMaterialName */
function shortName(t) {
  let s = t.replace(/\s*\([^)]*\)\s*/g, ' ').replace(/\s+/g, ' ').trim();
  s = s.replace(/,?\s*\d+\s*(pair|pairs|set|pack|packs|roll|rolls|sheet|sheets|tube|tubes|bag|bags|box|boxes|squares?|strips?|pieces?)\b.*$/i, '').trim();
  s = s.split(',')[0].trim();
  s = s.split(/\s+or\s+/i)[0].trim();
  s = s.replace(/^\d+\s+/, '');
  return s.length > 46 ? s.slice(0, 46).trim() + '...' : s;
}
function whoFor(audience) {
  const a = audience || [];
  /* "family" in the bank means parents dress up too (old page: ghost read
     "Kids and adults" with audience kid/solo/family). */
  const kid = a.includes('kid'), adult = a.includes('adult') || a.includes('family');
  if (kid && adult) return 'Kids and adults';
  if (kid) return 'Kids (and patient parents)';
  return 'Teens and adults';
}
const VIBE_WORDS = { scary: 'Spooky', cute: 'Cute', funny: 'Silly', crafty: 'Crafty', simple: 'Simple', couch: 'Cozy', heroes: 'Heroic', tv: 'TV-inspired', animals: 'Animal', food: 'Foodie' };
function vibe(tags) {
  const e = Object.entries(tags || {}).filter(([k]) => VIBE_WORDS[k])
    .sort((a, b) => b[1] - a[1]).slice(0, 2).map(([k]) => VIBE_WORDS[k]);
  return e.length ? e.join(' + ') : 'Easygoing';
}

function derive(id) {
  const idea = byId[id], ins = INS[id];
  if (!idea || !ins) throw new Error('missing bank entry: ' + id);
  const rawMats = ins.m || [];
  const enriched = ENRICHED[id] || {};
  const buy = [], home = [], either = [], note = [];
  const seenHome = new Set();
  const pushHome = label => { if (label && !seenHome.has(label)) { seenHome.add(label); home.push(label); } };
  rawMats.forEach(text => {
    const cls = classifyMaterial(text);
    const optional = /\([^)]*optional/i.test(text);
    const key = stripMarker(text);
    /* enriched t is usually the marker-stripped text, but a few entries keep
       the raw bank text — try both. */
    const groups = enriched[key] || enriched[text] || null;
    const stashIds = [];
    if (groups) groups.forEach(g => g.forEach(s => { if (s && !stashIds.includes(s)) stashIds.push(s); }));
    /* covered = every alternative group has at least one assumed staple.
       [[null]] (unmapped) and non-staple stashes never count as covered. */
    const covered = !!(groups && groups.length && groups.every(g => g.some(s => s && STAPLES.has(s))));
    if (covered) {
      stashIds.forEach(s => { if (STAPLES.has(s)) pushHome(CATALOG[s] ? CATALOG[s].label : s); });
      return;
    }
    if (cls === 'own' || cls === 'make') { pushHome(key); return; }
    const label = (cls === 'buy' ? (shortName(text) || key) : key) + (optional ? ' (optional)' : '');
    if (cls === 'buy') buy.push({ label, optional });
    else if (cls === 'either') either.push({ label: label + (optional ? '' : ' (or make it)'), optional });
    else note.push(key);
  });
  const hard = arr => arr.filter(e => !e.optional).length;
  const buyN = hard(buy) + hard(either);
  const tonight = buyN === 0 && note.length === 0;
  const aliases = [];
  Object.keys(PINPOINT).forEach(k => {
    if (PINPOINT[k].idea === id) aliases.push(k);
  });
  return {
    id, t: idea.title, b: idea.blurb, w: idea.why,
    time: ins.time, effort: ins.effort,
    aud: whoFor(idea.audience), kid: (idea.audience || []).includes('kid'),
    vibe: vibe(idea.tags), spook: (idea.tags && idea.tags.scary) || 0,
    tonight, buyN,
    buy: buy.map(e => e.label).concat(either.map(e => e.label)),
    home, note, al: aliases
  };
}

/* ---------------- build CMP_DATA for every idea ---------------- */
const CMP_DATA = {};
IDEAS.forEach(i => { CMP_DATA[i.id] = derive(i.id); });

/* ---------------- static default matchup ---------------- */
const staticH2 = APP.cmpH2(DEFAULT_IDS, CMP_DATA);
const staticBluf = APP.cmpBluf(DEFAULT_IDS, CMP_DATA);
const staticCards = APP.cmpCards(DEFAULT_IDS, CMP_DATA);
const staticTradeoffs = APP.cmpTradeoffs(DEFAULT_IDS, CMP_DATA);

/* ---------------- assertions (verify before writing) ---------------- */
function fail(msg) { throw new Error('ASSERT: ' + msg); }
DEFAULT_IDS.forEach(id => {
  if (!byId[id]) fail('default id not in bank: ' + id);
  if (!INS[id]) fail('default id missing INSTRUCTIONS: ' + id);
  if (!fs.existsSync(path.join(ROOT, 'photos', id + '.webp'))) fail('default id missing photo: ' + id);
});
/* 2026-09-30 ghost fix: the old marker-only derivation produced
   "Use from home: None" for the ghost. The stash derivation must fix it. */
if (!CMP_DATA['classic-ghost'].home.length) fail('classic-ghost derived home list is empty (ghost bug regressed)');
IDEAS.forEach(i => {
  const d = CMP_DATA[i.id];
  if (!d.t || !d.time) fail('incomplete CMP_DATA: ' + i.id);
});
/* no em/en dashes in visible copy */
[staticH2, staticBluf, staticCards, staticTradeoffs].forEach((s, n) => {
  if (/[—–]/.test(s)) fail('em/en dash in static copy block ' + n);
});
/* every static /c/ link is a real bank id */
const linkRe = /href="\/c\/([a-z0-9-]+)"/g;
let lm;
while ((lm = linkRe.exec(staticCards))) {
  if (!byId[lm[1]]) fail('static /c/ link to unknown bank id: ' + lm[1]);
}
/* never reintroduce the "Supply" fallback */
if (appSrc.includes('"Supply"') || appSrc.includes("'Supply'")) fail('compare-app.js contains the "Supply" fallback');
const aliasTotal = Object.values(CMP_DATA).reduce((n, d) => n + d.al.length, 0);
if (aliasTotal < 200) fail('alias index suspiciously small: ' + aliasTotal);

/* ---------------- page template ---------------- */
const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Compare Halloween Costumes Head to Head | Pick My Costume</title>
<meta name="description" content="Pick any 2 or 3 Halloween costumes and compare build time, effort, and what you already own, side by side. From the Pick My Costume costume bank.">
<link rel="canonical" href="https://pickmycostume.com/compare">
<meta property="og:type" content="website">
<meta property="og:title" content="Compare Halloween Costumes Head to Head | Pick My Costume">
<meta property="og:description" content="Pick any 2 or 3 costumes and compare them side by side: build time, effort, materials. From our costume bank.">
<meta property="og:url" content="https://pickmycostume.com/compare">
<meta property="og:image" content="https://pickmycostume.com/images/og/compare.jpg">
<meta name="twitter:card" content="summary_large_image">
<!-- 2026-09-27 red-team discover: X falls back to a small summary card without twitter:card. -->
<style>
:root{
  --bg:#160d28; --bg2:#211540; --card:#2a1c52; --ink:#fdf3e3;
  --muted:#cdbcf0; --line:#4b3486; --accent:#ff8c1a; --accent-ink:#2a1500;
  --radius:14px;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;line-height:1.5}
.wrap{max-width:960px;margin:0 auto;padding:20px 16px 64px}
header.top{display:flex;align-items:center;justify-content:space-between;padding:14px 0}
.brand{font-weight:800;font-size:18px;color:var(--ink);text-decoration:none}
.brand span{color:var(--accent)}
.home-link{color:var(--muted);text-decoration:none;font-size:14px;display:inline-block;padding:12px 8px;margin:-12px -8px}
/* 2026-09-27 red-team hubs: the header "Take the quiz" link was ~21px tall,
   well under the 44px minimum tap target. Padding + negative margin expands
   the hit area to ~45px with zero layout change. */
h1{font-size:32px;margin:8px 0 4px;line-height:1.2}
.sub{color:var(--muted);margin:0 0 24px}
h2{font-size:24px;margin:36px 0 8px}
h3{font-size:19px;margin:28px 0 8px}
.bluf{background:var(--bg2);border:1px solid var(--line);border-radius:var(--radius);padding:14px 16px;font-size:15px}
.takeaways{margin:8px 0 0;padding-left:20px}
.takeaways li{margin:0 0 10px}
.cta{display:block;text-align:center;background:var(--accent);color:var(--accent-ink);font-weight:800;font-size:18px;padding:16px;border-radius:var(--radius);text-decoration:none;margin:36px 0 8px}
.fine{color:var(--muted);font-size:13px}
.method{background:var(--bg2);border:1px solid var(--line);border-radius:var(--radius);padding:16px;margin-top:32px}
.method h3{margin:0 0 8px;font-size:16px}
.method p{margin:0 0 8px;font-size:14px;color:var(--muted)}
.method a{color:var(--accent)}
footer{margin-top:40px;text-align:center}
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
/* 2026-09-30: picker + cards for the dynamic compare tool */
.picker{background:var(--bg2);border:1px solid var(--line);border-radius:var(--radius);padding:16px;margin:0 0 8px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px}
.chips:empty{display:none}
.chip{background:var(--card);border:1px solid var(--accent);color:var(--ink);border-radius:999px;padding:10px 14px;font-size:15px;cursor:pointer;min-height:44px}
.chip:disabled{opacity:.55;cursor:default}
.chip span{color:var(--accent)}
#cmp-search{width:100%;background:var(--bg);border:1px solid var(--line);border-radius:10px;color:var(--ink);padding:12px 14px;font-size:16px;min-height:48px}
.cmp-results{margin:8px 0 0;display:grid;gap:6px}
.cmp-results[hidden]{display:none}
.cmp-hit{background:var(--card);border:1px solid var(--line);color:var(--ink);border-radius:10px;padding:12px 14px;font-size:15px;text-align:left;cursor:pointer;min-height:48px}
.cmp-hit:hover,.cmp-hit:focus{border-color:var(--accent)}
.cmp-hit:disabled{opacity:.5;cursor:default}
.browse{margin-top:12px}
.browse summary{cursor:pointer;color:var(--accent);padding:12px 4px;font-size:15px;min-height:44px;display:inline-block}
.browse-list{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;max-height:300px;overflow-y:auto;padding-bottom:4px}
.browse-btn{background:var(--bg);border:1px solid var(--line);color:var(--muted);border-radius:8px;padding:10px 12px;font-size:14px;cursor:pointer;min-height:44px}
.browse-btn:hover{color:var(--ink);border-color:var(--accent)}
.cmp-grid{display:grid;gap:16px;margin:16px 0;grid-template-columns:1fr}
@media(min-width:720px){.cmp-grid{grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}}
.cmp-card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;display:flex;flex-direction:column}
.cmp-photo{display:block;aspect-ratio:3/2;overflow:hidden;background:var(--bg2)}
.cmp-photo img{width:100%;height:100%;object-fit:cover;display:block}
.cmp-title{margin:14px 16px 4px;font-size:21px}
.cmp-title a{color:var(--ink);text-decoration:none;display:inline-block;padding:8px 4px;margin:-8px -4px}
.cmp-blurb{margin:0 16px 12px;color:var(--muted);font-size:14px}
.cmp-rows{margin:0 16px;display:grid;gap:10px;padding:0 0 4px}
.cr dt{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:0 0 2px}
.cr dd{margin:0;font-size:15px}
.cmp-guide{margin:12px 16px 16px;color:var(--accent);font-weight:700;text-decoration:none;display:inline-block;padding:12px 4px}
.swap-wrap{margin:0 0 4px}
#cmp-swap{background:var(--bg2);border:1px solid var(--accent);color:var(--accent);border-radius:10px;padding:12px 18px;font-size:15px;cursor:pointer;min-height:48px}
#cmp-swap[hidden]{display:none}
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <a class="brand" href="/">🎃 Pick My <span>Costume</span></a>
    <a class="home-link" href="/">Take the quiz</a>
  </header>

  <h1>Compare Halloween costumes, head to head</h1>
  <p class="sub">Pick any two or three costumes and see build time, effort, and what you already own, side by side. Every cell comes from our costume bank, the same one that powers the quiz.</p>

  <section aria-label="Pick costumes to compare">
    <h2>Pick your matchup</h2>
    <div class="picker" id="cmp-picker">
      <div class="chips" id="cmp-chips" aria-live="polite"></div>
      <label class="vh" for="cmp-search">Search costumes to compare</label>
      <input id="cmp-search" type="search" autocomplete="off" placeholder="Type a costume name, e.g. ghost, vampire, bluey">
      <div class="cmp-results" id="cmp-results" role="listbox" aria-label="Matching costumes" hidden></div>
      <p class="fine" id="cmp-hint">Pick 2 or 3 costumes to compare - 3 is the max.</p>
      <details class="browse"><summary id="cmp-browse-sum">Browse all costumes</summary><div class="browse-list" id="cmp-browse"></div></details>
    </div>
  </section>

  <section id="easy-classics" aria-label="Costume comparison">
  <h2 id="cmp-h2">${staticH2}</h2>
  <p class="bluf" id="cmp-bluf">${staticBluf}</p>
  <div class="swap-wrap"><button id="cmp-swap" type="button" data-item-id="swap">Swap sides</button></div>
  <div class="cmp-grid" id="cmp-cards">
${staticCards}
  </div>
  <h3>The trade-offs, in plain English</h3>
  <ul class="takeaways" id="cmp-tradeoffs">
${staticTradeoffs}
  </ul>
  <p class="fine">Every idea above also has a full free build guide with materials, numbered steps, and parent FAQs. Tap a photo or title.</p>
  </section>

  <a class="cta" href="/">Pick my costume →</a>
  <p class="fine" style="text-align:center">5 questions · 2 minutes · free forever</p>

  <div class="method">
    <h3>Where this comes from</h3>
    <p>Every number and material list on this page comes from the same costume bank that powers the Pick My Costume quiz: build time, difficulty, and per-idea materials. That is why this page always matches the quiz.</p>
    <p style="margin:0">We show them side by side and recommend nothing in particular: the right costume is the one you will actually finish before the party.</p>
</div>

  <footer>
    <!-- 2026-09-26 red-team distro: hub cross-links. /compare was an orphan:
         no inbound links from any deployed page. Folded into the generator
         2026-09-27 (red-team): a regen used to drop this nav. Pantry label
         matches the page's real title (the rename). -->
    <p class="fine" style="text-align:center">Explore: <a href="/costumes" style="color:var(--accent)">All costume guides</a> &middot; <a href="/trending" style="color:var(--accent)">Trending costumes</a> &middot; <a href="/group-costumes" style="color:var(--accent)">Group packs</a> &middot; <a href="/pantry" style="color:var(--accent)">What you already own</a></p>
    <p class="fine">Built with Muse.</p>
  </footer>
</div>
<!-- 2026-09-27 red-team: /compare had zero analytics, so SEO/recipient visits
     and the quiz CTA funnel were invisible to PostHog. PostHog beacon now
     lives in compare-app.js (same anonymous pattern pantry.html uses;
     autocapture off, no session recording). UnitTrack covers compare-picker
     and compare-cards per the standing instrumentation rule. -->
<script>
var CMP_DATA = ${JSON.stringify(CMP_DATA)};
var CMP_DEFAULT = ${JSON.stringify(DEFAULT_IDS)};
${appSrc}
</script>
</body>
</html>
`;

fs.writeFileSync(path.join(ROOT, 'compare.html'), html);
console.log('compare.html written:', html.length, 'bytes,', IDEAS.length, 'ideas in CMP_DATA,', aliasTotal, 'aliases indexed');
console.log('default matchup ghost home:', JSON.stringify(CMP_DATA['classic-ghost'].home));
console.log('default matchup ghost buy:', JSON.stringify(CMP_DATA['classic-ghost'].buy));
console.log('default matchup vampire buyN/tonight:', CMP_DATA['vampire'].buyN, CMP_DATA['vampire'].tonight);
