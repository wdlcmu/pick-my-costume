#!/usr/bin/env node
/* Stream C QA harness: cold-user flow walk + input-handler audit for the two
   staged pages. Runs in jsdom (no live site hits, no analytics pollution). */
const fs = require('fs');
const { JSDOM } = require('/home/hatch/workspace/.rt-node/node_modules/jsdom');
const path = require('path');

const REPO = '/home/hatch/workspace/builds/pick-my-costume';
let failures = 0, checks = 0;
function ok(cond, name) {
  checks++;
  if (!cond) { failures++; console.log('FAIL:', name); }
  else console.log('pass:', name);
}
function load(file) {
  const html = fs.readFileSync(path.join(REPO, file), 'utf8');
  return new JSDOM(html, { runScripts: 'dangerously' });
}

/* ---------- PAGE 1: diy-costumes-by-materials ---------- */
const p1 = load('diy-costumes-by-materials.html');
const d1 = p1.window.document;

// raw-HTML crawler checks (no JS)
const cards = d1.querySelectorAll('#grid .ccard');
ok(cards.length === 164, `page1: 164 cards in raw HTML (got ${cards.length})`);
let badLinks = 0, noTriple = 0, noReqs = 0;
cards.forEach(c => {
  const a = c.querySelector('h3 a');
  if (!a || !/^https:\/\/pickmycostume\.com\/c\/[a-z0-9-]+$/.test(a.href)) badLinks++;
  if (!c.querySelector('.triple')) noTriple++;
  if (!c.getAttribute('data-reqs')) noReqs++;
});
ok(badLinks === 0, `page1: all cards have real /c/ links (bad: ${badLinks})`);
ok(noTriple === 0, 'page1: all cards have time/cost/effort triple');
ok(noReqs === 0, 'page1: all cards carry data-reqs for the filter');
// every /c/ slug in sitemap
const sm = fs.readFileSync(path.join(REPO, 'sitemap.xml'), 'utf8');
let missingSm = 0;
cards.forEach(c => {
  const slug = c.getAttribute('data-slug');
  if (!sm.includes(`https://pickmycostume.com/c/${slug}`)) missingSm++;
});
ok(missingSm === 0, `page1: all /c/ slugs exist in sitemap (missing: ${missingSm})`);
// default ordering: first two cards are the fully-covered ones
const firstTwo = [cards[0].getAttribute('data-slug'), cards[1].getAttribute('data-slug')].sort();
ok(JSON.stringify(firstTwo) === JSON.stringify(['classic-ghost','emoji-crew']),
  `page1: default top-2 are the make-tonight pair (got ${firstTwo})`);
// resultline default
ok(/you can build 2 costumes? fully/.test(d1.getElementById('resultline').textContent) &&
   /14 more with/.test(d1.getElementById('resultline').textContent),
  'page1: default resultline reads 2 fully + 14 with 1-2 supplies');
// chips: count non-staple materials
const chips = d1.querySelectorAll('#filterbox .chip[data-mat]');
ok(chips.length === 44, `page1: 44 material chips (got ${chips.length})`);
// JSON-LD parses
d1.querySelectorAll('script[type="application/ld+json"]').forEach((s, i) => {
  try { JSON.parse(s.textContent); ok(true, `page1: JSON-LD #${i} parses`); }
  catch (e) { ok(false, `page1: JSON-LD #${i} parses (${e.message})`); }
});
// FAQPage has 5 questions
const faqLd = JSON.parse(d1.querySelectorAll('script[type="application/ld+json"]')[1].textContent);
ok(faqLd['@type'] === 'FAQPage' && faqLd.mainEntity.length === 5, 'page1: FAQPage with 5 questions');
// honesty: no forbidden claims
const html1 = fs.readFileSync(path.join(REPO, 'diy-costumes-by-materials.html'), 'utf8');
ok(!/most popular|best-selling|thousands of|all 164 (costumes )?are/i.test(html1), 'page1: no popularity/all-164 claims');
// footer intact
ok(html1.includes('Built with Muse.'), 'page1: footer Built with Muse');
// title/meta unique and DIY-targeted
ok(d1.title.includes('DIY Halloween Costumes') && d1.title.includes('Materials'), `page1: title targets DIY query ("${d1.title}")`);
ok(/easy DIY halloween costumes|materials/i.test(d1.querySelector('meta[name="description"]').content), 'page1: meta description targets DIY queries');

/* input-handler audit: chip toggle flips state and re-ranks */
function click(el) { el.dispatchEvent(new p1.window.MouseEvent('click', { bubbles: true })); }
const feltChip = d1.querySelector('.chip[data-mat="felt"]');
const resBefore = d1.getElementById('resultline').innerHTML;
click(feltChip);
ok(feltChip.classList.contains('on'), 'page1: chip toggles on');
ok(d1.getElementById('resultline').innerHTML !== resBefore, 'page1: resultline updates after ticking felt');
// ticking felt should not change make-tonight counts for felt-requiring 16 (they were already counted) but card order/nedd lines update
const ghostCard = d1.querySelector('.ccard[data-slug="classic-ghost"]');
ok(/Ready to build/.test(ghostCard.querySelector('.need').textContent), 'page1: classic-ghost stays ready after ticking felt');
// finger-bounce guard: two rapid clicks within 300ms => only one toggle
const yarnChip = d1.querySelector('.chip[data-mat="yarn"]');
click(yarnChip); // on
click(yarnChip); // bounce: ignored
ok(yarnChip.classList.contains('on'), 'page1: tapGuard swallows finger-bounce (chip stays on after rapid double-tap)');
click(yarnChip); // still within 300ms of previous accepted? may be ignored -> wait
setTimeout(() => {
  click(yarnChip); // after guard window: toggles off
  ok(!yarnChip.classList.contains('on'), 'page1: chip toggles off after guard window');
  // time filter: 30 min or less hides 45-min cards
  const t30 = d1.querySelector('#timechips .chip[data-tmax="30"]');
  click(t30);
  const bgc = d1.querySelector('.ccard[data-slug="block-game-crew"]');
  ok(bgc.style.display === 'none', 'page1: 30-min filter hides the 45-min block-game-crew');
  const ninja = d1.querySelector('.ccard[data-slug="ninja"]');
  ok(ninja.style.display !== 'none', 'page1: 30-min filter keeps ninja');
  // time chips are single-select
  const t60 = d1.querySelector('#timechips .chip[data-tmax="60"]');
  click(t60);
  ok(t60.classList.contains('on') && !t30.classList.contains('on'), 'page1: time chips single-select');
  ok(bgc.style.display !== 'none', 'page1: 1-hour filter restores block-game-crew');

  /* ---------- PAGE 2: make-it-tonight-costumes ---------- */
  const p2 = load('make-it-tonight-costumes.html');
  const d2 = p2.window.document;
  const cards2 = d2.querySelectorAll('.ccard');
  ok(cards2.length === 16, `page2: 16 tier cards in raw HTML (got ${cards2.length})`);
  // tier headings
  const h2s = Array.from(d2.querySelectorAll('h2')).map(h => h.textContent);
  ok(h2s.some(h => h.includes('15 minutes or less')) && h2s.some(h => h.includes('20 to 30 minutes')) && h2s.some(h => h.includes('45 minutes')),
    'page2: three time tiers present');
  // tier membership matches canonical times
  const cdata = JSON.parse(fs.readFileSync('/tmp/slug_tc.json', 'utf8'));
  function tierOf(timeStr) {
    const m = timeStr.match(/(\d+(?:\.\d+)?)\s*(min|hr)/);
    const v = parseFloat(m[1]) * (m[2] === 'hr' ? 60 : 1);
    return v <= 15 ? 15 : (v <= 30 ? 30 : 45);
  }
  let tierErr = 0;
  const expected = { 15: [], 30: [], 45: [] };
  Object.keys(cdata).filter(s => ['classic-ghost','block-game-crew','block-monster','breakfast-buffet','cereal-crew','decades-crew','emoji-crew','fairy-tale-princesses','ghost-hunters','ice-cream-cone','ninja','player-one-two','plug-socket','salt-pepper','space-crewmate','coffee-cup'].includes(s))
    .forEach(s => expected[tierOf(cdata[s].time)].push(s));
  ['15 minutes or less', '20 to 30 minutes', '45 minutes'].forEach((label, i) => {
    const t = [15, 30, 45][i];
    const h2 = Array.from(d2.querySelectorAll('h2')).find(h => h.textContent.includes(label));
    let node = h2.parentElement.nextSibling, found = [];
    while (node) {
      if (node.classList && node.classList.contains('tierhead')) break;
      if (node.classList && node.classList.contains('ccard')) {
        found.push(node.querySelector('h3 a').href.split('/c/')[1]);
      }
      if (node.tagName === 'H2') break;
      node = node.nextSibling;
    }
    const exp = expected[t].sort(), got = found.sort();
    if (JSON.stringify(exp) !== JSON.stringify(got)) { tierErr++; console.log('  tier mismatch', label, 'exp', exp, 'got', got); }
  });
  ok(tierErr === 0, 'page2: tier membership matches canonical build times (5/9/2)');
  // every card: triple matches canonical /c/ time+cost, real /c/ link, materials list
  let cardErr = 0;
  cards2.forEach(c => {
    const slug = c.querySelector('h3 a').href.split('/c/')[1];
    const triple = c.querySelector('.triple').textContent;
    if (!triple.includes(cdata[slug].time) || !triple.includes(cdata[slug].cost)) { cardErr++; console.log('  card mismatch', slug, triple); }
    if (!c.querySelector('details ul li')) cardErr++;
  });
  ok(cardErr === 0, 'page2: all cards show canonical time/cost and a materials list');
  // cross-links between pages
  const html2 = fs.readFileSync(path.join(REPO, 'make-it-tonight-costumes.html'), 'utf8');
  ok(html2.includes('https://pickmycostume.com/diy-costumes-by-materials'), 'page2: links to page 1');
  ok(html1.includes('https://pickmycostume.com/make-it-tonight-costumes'), 'page1: links to page 2');
  // inbound from existing pages not added (deferred); outbound links to pantry/quiz/costumes exist
  ok(html1.includes('https://pickmycostume.com/pantry') && html2.includes('https://pickmycostume.com/pantry'), 'both pages link to pantry');
  // honesty constraints
  ok(/16 (of|out of)( the)? 164/.test(html2) && !/most popular|thousands/i.test(html2), 'page2: honest 16-of-164 stat, no popularity claims');
  ok(html2.includes('Built with Muse.'), 'page2: footer Built with Muse');
  d2.querySelectorAll('script[type="application/ld+json"]').forEach((s, i) => {
    try { JSON.parse(s.textContent); ok(true, `page2: JSON-LD #${i} parses`); }
    catch (e) { ok(false, `page2: JSON-LD #${i} parses`); }
  });
  ok(d2.title.includes('Make-It-Tonight'), `page2: unique title ("${d2.title}")`);

  console.log(`\n${checks - failures}/${checks} checks passed`);
  process.exit(failures ? 1 : 0);
}, 400);
