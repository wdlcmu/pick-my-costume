// supply-card-harness.js -- QA for the 2026-10-13 /c/ supply-card fix.
// The card's static HTML used to render every guide as "You have 0 of N
// things for this." with ALL supplies under "Still need:", even supplies
// tagged as assumed household basics (PANTRY staples), which the site
// model (and the card's own client tick script, via its staples seed)
// treats as already owned. The generator's _cCardsHtml now applies
// assumed-basics coverage to the static render.
// This harness renders real /c/ pages from the generated Pages Function
// (functions/c/[slug].js) and asserts, for an all-basics guide
// (classic-ghost), a mixed guide (baby-dino), and a no-basics guide
// (basketball-star):
//   - the static header counts basics as have (all-covered state for
//     classic-ghost, partial count for baby-dino, unchanged 0 for
//     basketball-star);
//   - the static Still-need list holds only genuinely uncovered tiles
//     (hidden entirely when nothing is missing);
//   - the static tiles render have/miss consistently with that split;
//   - after the inline tick script runs with a fresh (empty) pantry, the
//     painted DOM matches the static HTML exactly (no visible flip).
// Expectations are computed independently from the page's own embedded
// PMD (mats/tiles/staples) using the client matOk semantics.
// Exits non-zero on any failure.
const fs = require('fs');
const path = require('path');
const os = require('os');
const { JSDOM } = require('/home/hatch/workspace/.rt-node/node_modules/jsdom');

const ROOT = path.join(__dirname, '..');
let pass = 0, fail = 0;
function ok(cond, name, extra) {
  if (cond) { pass++; console.log('  ok:', name); }
  else { fail++; console.log('  FAIL:', name, extra || ''); }
}

function renderFn() {
  const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'c-fn-'));
  const p = path.join(TMP, 'slug.mjs');
  fs.copyFileSync(path.join(ROOT, 'functions', 'c', '[slug].js'), p);
  return import('file://' + p);
}

async function render(mod, slug) {
  const res = mod.onRequest({
    params: { slug },
    request: new Request('https://pickmycostume.com/c/' + slug),
  });
  return { status: res.status, html: await res.text() };
}

function scriptWith(html, marker) {
  const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
  return blocks.find(b => b.includes(marker)) || null;
}

function extractPMD(html) {
  const marker = 'window.PMD=';
  const i = html.indexOf(marker);
  if (i < 0) return null;
  let start = i + marker.length, depth = 0, k = start, inStr = false, esc = false;
  for (; k < html.length; k++) {
    const c = html[k];
    if (inStr) { if (esc) esc = false; else if (c === '\\') esc = true; else if (c === '"') inStr = false; }
    else if (c === '"') inStr = true;
    else if (c === '{' || c === '[') depth++;
    else if (c === '}' || c === ']') { depth--; if (depth === 0) { k++; break; } }
  }
  return JSON.parse(html.slice(start, k));
}

// Independent mirror of the client tick script's matOk() for a fresh
// visitor: tick set = staples only, no saved pantry, no buy ticks.
function matOkStaples(mat, staples) {
  let hasReal = false;
  for (const grp of mat) { for (const id of grp) { if (id) { hasReal = true; break; } } if (hasReal) break; }
  for (const grp of mat) {
    let gok = grp.some(id => id && staples.includes(id));
    if (!gok && grp.every(id => !id) && hasReal) gok = true;
    if (!gok) return false;
  }
  return true;
}

function expected(pmd) {
  const staples = pmd.staples || [];
  const matHave = pmd.mats.map(m => matOkStaples(m, staples));
  const have = matHave.filter(Boolean).length, total = pmd.mats.length;
  const tileHave = pmd.tiles.map(t => t.idxs.every(mi => matHave[mi]));
  const head = have >= total ? 'You have everything for this one. Nothing to buy.'
    : (have === 0 ? 'You have 0 of ' + total + ' things for this.'
      : 'You already have ' + have + ' of ' + total + ' things for this.');
  const missLabels = pmd.tiles.filter((t, ti) => !tileHave[ti]).map(t => t.e + t.label);
  return { have, total, tileHave, head, missLabels };
}

function cardState(doc) {
  const root = doc.getElementById('detail-mats');
  if (!root) return null;
  const need = root.querySelector('[data-role=cneed]');
  const chipsEl = root.querySelector('[data-role=cchips]');
  return {
    head: root.querySelector('[data-role=chead]').textContent,
    tiles: [...root.querySelectorAll('.ptile')].map(t => ({
      cls: t.className.replace('ptile ', ''),
      badge: t.querySelector('.ptbadge').textContent,
      aria: t.getAttribute('aria-label'),
    })),
    needHidden: need.style.display === 'none',
    chipsHidden: chipsEl.style.display === 'none',
    chips: [...chipsEl.querySelectorAll('.pchip')].map(c => c.textContent),
  };
}

(async () => {
  const mod = await renderFn();
  const cases = [
    { slug: 'classic-ghost', kind: 'all basics' },
    { slug: 'baby-dino', kind: 'mixed' },
    { slug: 'basketball-star', kind: 'no basics' },
  ];
  for (const { slug, kind } of cases) {
    console.log(slug + ' (' + kind + ')');
    const { status, html } = await render(mod, slug);
    ok(status === 200, slug + ' renders 200');
    const pmd = extractPMD(html);
    ok(!!pmd, slug + ' embeds PMD');
    const exp = expected(pmd);
    console.log('    expected: have ' + exp.have + '/' + exp.total + ', miss tiles: ' + exp.missLabels.length);

    // --- static HTML state (no scripts run) ---
    const sdom = new JSDOM(html, { url: 'https://pickmycostume.com/c/' + slug });
    const st = cardState(sdom.window.document);
    ok(!!st, slug + ' static card present');
    ok(st.head === exp.head, slug + ' static header: "' + exp.head + '"', 'got "' + st.head + '"');
    ok(JSON.stringify(st.chips) === JSON.stringify(exp.missLabels),
      slug + ' static Still-need holds exactly the uncovered tiles',
      'got ' + JSON.stringify(st.chips) + ' want ' + JSON.stringify(exp.missLabels));
    ok(st.needHidden === (exp.missLabels.length === 0) && st.chipsHidden === (exp.missLabels.length === 0),
      slug + ' static Still-need hidden iff nothing is missing');
    ok(st.tiles.every((t, ti) => t.cls === (exp.tileHave[ti] ? 'have' : 'miss')),
      slug + ' static tile classes match coverage split', JSON.stringify(st.tiles.map(t => t.cls)));
    ok(st.tiles.every((t, ti) => t.badge === (exp.tileHave[ti] ? '\u2713' : '\u25CB')),
      slug + ' static tile badges match coverage split');
    ok(st.tiles.every((t, ti) => t.aria.endsWith(exp.tileHave[ti] ? ': you have this. Tap to update.' : ': missing. Tap to update.')),
      slug + ' static tile aria-labels match coverage split');
    if (kind === 'all basics') {
      // raw-bytes guard, scoped to the card header element (the tick
      // script source legitimately contains the 0-of-N template string)
      ok(html.includes('data-role="chead">' + exp.head + '<'),
        slug + ' raw card header is the all-covered line, not 0 of N');
      ok(exp.have === exp.total && exp.total > 0, slug + ' is genuinely all-basics in the data');
    }
    if (kind === 'no basics') {
      ok(exp.have === 0, slug + ' is genuinely no-basics in the data');
      ok(st.head.startsWith('You have 0 of '), slug + ' header unchanged from pre-fix behavior');
    }
    if (kind === 'mixed') {
      ok(exp.have > 0 && exp.have < exp.total, slug + ' is genuinely mixed in the data');
    }
    sdom.window.close();

    // --- post-JS state (fresh pantry): must match the static render ---
    const card = scriptWith(html, 'window.PMD');
    ok(!!card, slug + ' tick script present');
    const jdom = new JSDOM(html, { url: 'https://pickmycostume.com/c/' + slug, runScripts: 'outside-only' });
    jdom.window.eval(card);
    const jt = cardState(jdom.window.document);
    ok(jt.head === st.head, slug + ' painted header matches static header', 'painted "' + jt.head + '"');
    ok(JSON.stringify(jt.chips) === JSON.stringify(st.chips), slug + ' painted Still-need matches static');
    ok(JSON.stringify(jt.tiles.map(t => t.cls)) === JSON.stringify(st.tiles.map(t => t.cls)),
      slug + ' painted tile classes match static');
    ok(jt.needHidden === st.needHidden && jt.chipsHidden === st.chipsHidden,
      slug + ' painted Still-need visibility matches static');
    jdom.window.close();
  }

  console.log('\n' + pass + ' passed, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('HARNESS ERROR', e); process.exit(2); });
