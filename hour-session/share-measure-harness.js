// share-measure-harness.js -- QA for the 2026-10-13 share-measurement batch.
// Renders real /c/ pages by invoking the generated Pages Function
// (functions/c/[slug].js) and asserts:
//   ITEM 1: body order is crumb -> title -> photo -> timed chips -> plan
//           CTA (+ Share/Print adjacent) -> intro paragraph.
//   ITEM 2: the inline landing script fires recipient_landing_viewed once,
//           only on genuine share arrivals (8+ char s param), with the
//           homepage property names (idea_id, recipient_channel,
//           via_share_id, share_origin).
//   ITEM 3+4: the inline Share button fires share_created (app property
//           names) when a native share resolves or a copy succeeds, fires
//           NOTHING when the sheet is dismissed, and the shared text is at
//           parity with app shares (canonical ask line, UTM block, region
//           campaign, one minted sid shared by text + event).
//   ITEM 7: /c/superhero-family renders the red-sweatsuits pictured caption.
// Inline scripts are executed in jsdom (from ~/workspace/.rt-node) with a
// mock posthog. Exits non-zero on any failure.
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

async function render(mod, slug, query) {
  const res = mod.onRequest({
    params: { slug },
    request: new Request('https://pickmycostume.com/c/' + slug + (query || '')),
  });
  return { status: res.status, html: await res.text() };
}

function scriptWith(html, marker) {
  const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
  return blocks.find(b => b.includes(marker)) || null;
}

function makeDom(url, html) {
  const dom = new JSDOM(html, { url, runScripts: 'outside-only' });
  const events = [];
  dom.window.posthog = { capture: (n, p) => events.push([n, p]) };
  return { dom, events };
}
const tick = () => new Promise(r => setTimeout(r, 30));

(async () => {
  const mod = await renderFn();

  console.log('ITEM 1: first-screen order (classic-ghost)');
  const g = await render(mod, 'classic-ghost');
  ok(g.status === 200, 'classic-ghost renders 200');
  const H = g.html;
  const iCrumb = H.indexOf('class="crumb"');
  const iH1 = H.indexOf('<h1>');
  const iPhoto = H.indexOf('<img src="/photos/classic-ghost.webp"');
  const iChips = H.indexOf('class="triple"');
  const iCtaWrap = H.indexOf('class="ctawrap"');
  const iShareWrap = H.indexOf('class="sharewrap"');
  const iIntro = H.indexOf('class="intro"');
  ok(iCrumb > -1 && iCrumb < iH1, 'breadcrumb above title');
  ok(iH1 > -1 && iPhoto > iH1, 'photo immediately after title', 'h1@' + iH1 + ' photo@' + iPhoto);
  ok(iPhoto > -1 && iChips > iPhoto, 'timed chips after photo');
  ok(iChips > -1 && iCtaWrap > iChips, 'plan CTA after chips');
  ok(iShareWrap > iCtaWrap && iShareWrap < iIntro, 'Share/Print adjacent to CTA, before intro');
  ok(iCtaWrap > -1 && iIntro > iCtaWrap, 'description (intro) after CTA');
  ok(H.includes('id="guideshare"') && H.includes('id="guideprint"'), 'Share and Print buttons present');
  // photo block stays together: AI label + pictured caption under the photo
  const iAi = H.indexOf('class="aiphoto"');
  ok(iAi > iPhoto && iAi < iChips, 'AI photo label sits between photo and chips');
  // recipient banner script still ships and still injects above <main> content
  ok(H.includes('recipientbanner') || H.includes('RECIPIENT_BANNER'), 'recipient banner machinery still present');

  console.log('ITEM 7: superhero-family pictured caption');
  const sf = await render(mod, 'superhero-family');
  ok(sf.html.includes('Pictured: a family of four in matching red sweatsuits with black felt eye masks and a yellow felt lightning bolt on the chest.'),
    'exact red-sweatsuits caption rendered on /c/superhero-family');
  ok(!sf.html.includes('blue superhero suits'), 'old blue-suits caption gone');

  console.log('ITEM 2: recipient_landing_viewed gating + properties');
  const landing = scriptWith(H, 'recipient_landing_viewed');
  ok(!!landing, 'landing script present in page HTML');
  {
    const { dom, events } = makeDom('https://pickmycostume.com/c/classic-ghost?s=abcd1234&o=guide&utm_source=share&utm_medium=copy&utm_campaign=fright-night', H);
    dom.window.eval(landing);
    await tick();
    const ev = events.filter(e => e[0] === 'recipient_landing_viewed');
    ok(ev.length === 1, 'fires exactly once on a genuine arrival', JSON.stringify(events));
    if (ev.length) {
      const p = ev[0][1];
      ok(p.idea_id === 'classic-ghost', 'idea_id is the slug');
      ok(p.via_share_id === 'abcd1234', 'via_share_id from s param');
      ok(p.share_origin === 'guide', 'share_origin from o param');
      ok(typeof p.recipient_channel === 'string' && p.recipient_channel.length > 0, 'recipient_channel inferred (' + p.recipient_channel + ')');
    }
    dom.window.close();
  }
  {
    const { dom, events } = makeDom('https://pickmycostume.com/c/classic-ghost', H);
    dom.window.eval(landing);
    await tick();
    ok(events.length === 0, 'no event on a bare visit');
    dom.window.close();
  }
  {
    const { dom, events } = makeDom('https://pickmycostume.com/c/classic-ghost?s=x&o=guide', H);
    dom.window.eval(landing);
    await tick();
    ok(events.length === 0, 'no event on a forged short s param');
    dom.window.close();
  }
  {
    const { dom, events } = makeDom('https://pickmycostume.com/c/classic-ghost?s=pin99999&o=pin', H);
    dom.window.eval(landing);
    await tick();
    const ev = events.filter(e => e[0] === 'recipient_landing_viewed');
    ok(ev.length === 1 && ev[0][1].share_origin === 'pin', 'pin origin recognized');
    dom.window.close();
  }

  console.log('ITEM 3+4: share_created honesty + share text parity');
  const shareScript = scriptWith(H, 'guideshare');
  ok(!!shareScript, 'share script present in page HTML');
  {
    // native share resolves
    const { dom, events } = makeDom('https://pickmycostume.com/c/classic-ghost', H);
    let shared = null;
    Object.defineProperty(dom.window.navigator, 'share', {
      configurable: true,
      value: (obj) => { shared = obj; return Promise.resolve(); },
    });
    dom.window.eval(shareScript);
    dom.window.document.getElementById('guideshare').click();
    await tick();
    const ev = events.filter(e => e[0] === 'share_created');
    ok(!!shared, 'navigator.share called');
    ok(ev.length === 1, 'share_created fires once on resolved share', JSON.stringify(events));
    const sidm = shared && shared.text.match(/[?&]s=([a-z0-9]{8})/);
    if (ev.length && sidm) {
      const p = ev[0][1];
      ok(p.share_id === sidm[1], 'event share_id equals the sid in the shared link');
      ok(p.idea_id === 'classic-ghost' && p.share_origin === 'guide' && p.via === 'native', 'event props: idea_id, share_origin=guide, via=native');
    }
    ok(shared && shared.text.startsWith('🎃 '), 'share text keeps the pumpkin lead + caption');
    ok(shared && shared.text.includes('Timed: about'), 'share text keeps the Timed line');
    ok(shared && shared.text.includes('What are you going as? Found mine with this 2-minute quiz: https://pickmycostume.com/c/classic-ghost?s='), 'canonical ask line + guide URL');
    ok(shared && shared.text.includes('&o=guide&utm_source=share&utm_medium=native&utm_campaign=fright-night'), 'UTM block with native medium + region campaign');
    ok(shared && !shared.text.includes('Here is the guide'), 'old guide line gone');
    dom.window.close();
  }
  {
    // native share dismissed: nothing fires
    const { dom, events } = makeDom('https://pickmycostume.com/c/classic-ghost', H);
    Object.defineProperty(dom.window.navigator, 'share', {
      configurable: true,
      value: () => Promise.reject(new Error('AbortError')),
    });
    dom.window.eval(shareScript);
    dom.window.document.getElementById('guideshare').click();
    await tick();
    ok(events.filter(e => e[0] === 'share_created').length === 0, 'dismissed share sheet fires nothing');
    dom.window.close();
  }
  {
    // clipboard copy succeeds
    const { dom, events } = makeDom('https://pickmycostume.com/c/classic-ghost', H);
    let copied = null;
    Object.defineProperty(dom.window.navigator, 'clipboard', {
      configurable: true,
      value: { writeText: (t) => { copied = t; return Promise.resolve(); } },
    });
    dom.window.eval(shareScript);
    dom.window.document.getElementById('guideshare').click();
    await tick();
    const ev = events.filter(e => e[0] === 'share_created');
    ok(ev.length === 1 && ev[0][1].via === 'clipboard', 'share_created fires on copy with via=clipboard', JSON.stringify(events));
    ok(copied && copied.includes('utm_medium=copy'), 'copied text carries utm_medium=copy');
    const sidm = copied && copied.match(/[?&]s=([a-z0-9]{8})/);
    ok(!!sidm && ev.length && ev[0][1].share_id === sidm[1], 'copy event share_id equals the sid in the copied link');
    dom.window.close();
  }

  console.log('\n' + pass + ' passed, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('HARNESS ERROR', e); process.exit(2); });
