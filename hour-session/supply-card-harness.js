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
//
// 2026-10-13 (run 191): the headline wording went assumption-scoped.
// The static/fresh headline no longer counts assumed basics as owned:
// partial = "N of M things covered, counting basics we assume you
// have.", all-covered = "Everything here is basics we assume you have.
// Nothing to buy." The client re-render is assumption-aware (own ticks
// counted apart from assumed coverage), and this harness mirrors that
// composer independently and exercises it with seeded-pantry DOM sims
// (returning visitor on black-cat and basketball-star).
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

// Set-based mirror of the client matOk() (buy ticks included).
function matOkSet(mat, set, slug, mi) {
  let hasReal = false;
  for (const grp of mat) { for (const id of grp) { if (id) { hasReal = true; break; } } if (hasReal) break; }
  for (const grp of mat) {
    let gok = grp.some(id => id && set.has(id));
    if (!gok && grp.every(id => !id) && (set.has('buy:' + slug + '#' + mi) || hasReal)) gok = true;
    if (!gok) return false;
  }
  return true;
}

// Independent mirror of the client's assumption-aware classification:
// own = covered by the visitor's own ticks alone (saved ids minus the
// staples seed, plus buy ticks); asm = covered only via assumed basics;
// mix = covered only by ticks and assumptions combined.
function classify(pmd, slug, ownIds) {
  const staples = pmd.staples || [];
  const ownSet = new Set((ownIds || []).filter(id => !staples.includes(id)));
  const fullSet = new Set([...staples, ...ownSet]);
  let own = 0, asm = 0, mix = 0;
  pmd.mats.forEach((mat, mi) => {
    if (!matOkSet(mat, fullSet, slug, mi)) return;
    if (matOkSet(mat, ownSet, slug, mi)) { own++; return; }
    const used = ownSet.has('buy:' + slug + '#' + mi)
      || mat.some(grp => grp.some(id => id && ownSet.has(id)));
    if (used) mix++; else asm++;
  });
  return { own, asm, mix, cov: own + asm + mix, total: pmd.mats.length };
}

// Word-for-word mirror of the client headline composer.
function headlineFor(c) {
  const { own, asm, mix, cov, total } = c;
  if (cov === 0) return 'You have 0 of ' + total + ' things for this.';
  if (cov >= total) {
    if (asm === cov) return 'Everything here is basics we assume you have. Nothing to buy.';
    if (own === cov) return 'You have everything for this one. Nothing to buy.';
    if (mix === 0) return 'You have everything for this one: ' + own + ' ticked by you, ' + asm + ' counting basics we assume you have. Nothing to buy.';
    return 'You have everything for this one, from your ticks and basics we assume you have. Nothing to buy.';
  }
  if (asm === cov) return cov + ' of ' + total + ' things covered, counting basics we assume you have.';
  if (own === cov) return 'You already have ' + cov + ' of ' + total + ' things for this.';
  if (mix === 0) return cov + ' of ' + total + ' things covered: ' + own + ' ticked by you, ' + asm + ' counting basics we assume you have.';
  return cov + ' of ' + total + ' things covered, from your ticks and basics we assume you have.';
}

function expected(pmd, slug) {
  const staples = pmd.staples || [];
  const matHave = pmd.mats.map(m => matOkStaples(m, staples));
  const have = matHave.filter(Boolean).length, total = pmd.mats.length;
  const tileHave = pmd.tiles.map(t => t.idxs.every(mi => matHave[mi]));
  const head = headlineFor(classify(pmd, slug, []));
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
    { slug: 'black-cat', kind: 'mixed' },
    { slug: 'vampire', kind: 'mixed' },
    { slug: 'basketball-star', kind: 'no basics' },
  ];
  for (const { slug, kind } of cases) {
    console.log(slug + ' (' + kind + ')');
    const { status, html } = await render(mod, slug);
    ok(status === 200, slug + ' renders 200');
    const pmd = extractPMD(html);
    ok(!!pmd, slug + ' embeds PMD');
    const exp = expected(pmd, slug);
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

  // --- returning-visitor sims: seeded pantry, assumption-aware headline ---
  function paintedHead(html, slug, savedIds) {
    const card = scriptWith(html, 'window.PMD');
    const jdom = new JSDOM(html, { url: 'https://pickmycostume.com/c/' + slug, runScripts: 'outside-only' });
    if (savedIds) jdom.window.localStorage.setItem('pantry2', JSON.stringify(savedIds));
    jdom.window.eval(card);
    const h = jdom.window.document.querySelector('[data-role=chead]').textContent;
    jdom.window.close();
    return h;
  }
  // Pick up to `want` mats not covered by assumed basics whose every
  // group offers a non-staple id, so the ticks complete them outright
  // (own coverage, no mixed mats).
  function pickTickable(pmd, slug, want) {
    const staples = new Set(pmd.staples || []);
    const ids = [];
    let picked = 0;
    pmd.mats.forEach((mat, mi) => {
      if (picked >= want) return;
      if (matOkSet(mat, staples, slug, mi)) return;
      const mine = [];
      for (const grp of mat) {
        const cand = grp.find(id => id && !staples.has(id));
        if (cand) mine.push(cand);
        else if (grp.some(id => id)) return;
      }
      if (!mine.length) return;
      if (!matOkSet(mat, new Set(mine), slug, mi)) return;
      ids.push(...mine); picked++;
    });
    return { ids, picked };
  }

  { // black-cat: tick 2 non-basics on top of 4 assumed -> two-count split
    const slug = 'black-cat';
    console.log(slug + ' (returning visitor, 2 own ticks)');
    const { html } = await render(mod, slug);
    const pmd = extractPMD(html);
    const pk = pickTickable(pmd, slug, 2);
    ok(pk.picked === 2, slug + ' sim: found two tickable non-basic mats', 'picked ' + pk.picked);
    const cls = classify(pmd, slug, pk.ids);
    ok(cls.mix === 0 && cls.own === 2 && cls.asm > 0 && cls.cov < cls.total,
      slug + ' sim: classification is a clean partial two-count split', JSON.stringify(cls));
    const expH = headlineFor(cls);
    const got = paintedHead(html, slug, pk.ids);
    ok(got === expH, slug + ' returning header: "' + expH + '"', 'got "' + got + '"');
    ok(got.includes('ticked by you') && got.includes('counting basics we assume you have'),
      slug + ' returning header names both sources');
  }
  { // black-cat: tick ALL non-basics -> all covered, but NOT the E wording
    const slug = 'black-cat';
    console.log(slug + ' (returning visitor, all non-basics ticked)');
    const { html } = await render(mod, slug);
    const pmd = extractPMD(html);
    const pk = pickTickable(pmd, slug, 99);
    const cls = classify(pmd, slug, pk.ids);
    ok(cls.cov === cls.total && cls.own > 0 && cls.asm > 0 && cls.mix === 0,
      slug + ' sim: all covered with own and assumed parts', JSON.stringify(cls));
    const expH = headlineFor(cls);
    const got = paintedHead(html, slug, pk.ids);
    ok(got === expH, slug + ' all-covered split header: "' + expH + '"', 'got "' + got + '"');
    ok(!got.startsWith('Everything here is basics'),
      slug + ' all-covered header is not the pure-assumption E wording when the visitor ticked non-basics');
  }
  { // basketball-star: no basics at all -> own ticks get no assumption clause
    const slug = 'basketball-star';
    console.log(slug + ' (returning visitor, 1 own tick, zero assumed)');
    const { html } = await render(mod, slug);
    const pmd = extractPMD(html);
    const pk = pickTickable(pmd, slug, 1);
    ok(pk.picked === 1, slug + ' sim: found one tickable mat', 'picked ' + pk.picked);
    const cls = classify(pmd, slug, pk.ids);
    ok(cls.asm === 0 && cls.mix === 0 && cls.own === 1,
      slug + ' sim: coverage is purely the visitor\'s own tick', JSON.stringify(cls));
    const expH = headlineFor(cls);
    const got = paintedHead(html, slug, pk.ids);
    ok(got === expH, slug + ' own-only header: "' + expH + '"', 'got "' + got + '"');
    ok(!got.includes('assume'), slug + ' own-only header carries no assumption clause');
  }

  console.log('\n' + pass + ' passed, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('HARNESS ERROR', e); process.exit(2); });
