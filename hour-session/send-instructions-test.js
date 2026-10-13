// send-instructions-test.js -- QA for functions/send-instructions.js.
// Imports the real handler (via .mjs copies in /tmp) with mock contexts.
// Covers: validation, unknown idea, rate limit, server-side composition
// (no client text; template v2 guide link + tracked Share it URL),
// dry-run, Resend call shape, failures.
// 2026-10-13: composition assertions updated to template v2 (the guide
// link with plan UTMs is intended since 2026-10-02) and to the run177
// spec: the "Share it" URL is /c/<slug>?s=<8 chars>&o=emaillist. The
// pre-v2 "no /c/ link anywhere" assertions were stale and failing.
const fs = require('fs');
const path = require('path');
const os = require('os');

const ROOT = path.join(__dirname, '..');
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'si-test-'));

let pass = 0, fail = 0;
function ok(cond, name, extra) {
  if (cond) { pass++; console.log('  ok:', name); }
  else { fail++; console.log('  FAIL:', name, extra || ''); }
}

function mockReq(payload, ip, raw) {
  return new Request('https://pickmycostume.com/send-instructions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'cf-connecting-ip': ip || '9.9.9.9',
    },
    body: raw !== undefined ? raw : JSON.stringify(payload),
  });
}

(async () => {
  // Stage the ESM function + data as .mjs for node import.
  let fnSrc = fs.readFileSync(path.join(ROOT, 'functions', 'send-instructions.js'), 'utf8');
  fnSrc = fnSrc.replace("from './send-instructions-data.js'", "from './send-instructions-data.mjs'");
  fs.writeFileSync(path.join(TMP, 'send-instructions.mjs'), fnSrc);
  fs.copyFileSync(
    path.join(ROOT, 'functions', 'send-instructions-data.js'),
    path.join(TMP, 'send-instructions-data.mjs')
  );
  const mod = await import('file://' + path.join(TMP, 'send-instructions.mjs'));
  const { onRequestPost, composeEmail, _resetRateLimit } = mod;

  const j = async (res) => ({ status: res.status, body: await res.json() });

  console.log('validation');
  _resetRateLimit();
  let r = await j(await onRequestPost({ request: mockReq({ email: 'not-an-email', idea_id: 'tin-hero' }), env: {} }));
  ok(r.status === 400 && r.body.error === 'bad_email', 'rejects malformed email');
  r = await j(await onRequestPost({ request: mockReq({ email: '', idea_id: 'tin-hero' }), env: {} }));
  ok(r.status === 400 && r.body.error === 'bad_email', 'rejects empty email');
  r = await j(await onRequestPost({ request: mockReq({ email: 'a@b', idea_id: 'tin-hero' }), env: {} }));
  ok(r.status === 400 && r.body.error === 'bad_email', 'rejects short tld');
  r = await j(await onRequestPost({ request: mockReq({ email: 'x'.repeat(250) + '@a.co', idea_id: 'tin-hero' }), env: {} }));
  ok(r.status === 400 && r.body.error === 'bad_email', 'rejects >254 chars');
  r = await j(await onRequestPost({ request: mockReq({ email: '  Test@Example.COM ', idea_id: 'tin-hero' }), env: {} }));
  ok(r.status === 200 && r.body.ok && r.body.dry_run === true, 'trims/lowercases, dry-run without key');
  r = await j(await onRequestPost({ request: mockReq({ email: 'ok@example.com', idea_id: 'nope' }), env: {} }));
  ok(r.status === 404 && r.body.error === 'unknown_idea', 'rejects unknown idea');
  r = await j(await onRequestPost({ request: mockReq(null, '9.9.9.9', 'not json{{'), env: {} }));
  ok(r.status === 400 && r.body.error === 'bad_request', 'rejects bad JSON');

  console.log('server-side composition (template v2 + tracked Share it URL)');
  const idea = { t: 'The Tin Hero', m: ['red shirt'], s: ['put it on'], time: '5 min', cost: '$0', effort: 'Easy' };
  const c = composeEmail(idea);
  ok(c.text.includes('pickmycostume.com/c/costume?utm_source=email&utm_medium=plan&utm_campaign=costume'), 'body guide link carries plan UTMs');
  ok(c.text.includes('YOU NEED:') && c.text.includes('STEPS:'), 'body has materials + steps');
  ok(c.text.includes('Time: 5 min  |  Easy') && !c.text.includes('$0'), 'body has time|effort and no cost figure');
  ok(!/[\r\n]/.test(c.subject), 'subject has no CR/LF');
  // run177 spec: the Share it URL is a tracked share URL, minted per send
  const SHARE_RE = /^Share it: https:\/\/pickmycostume\.com\/c\/[a-z0-9-]+\?s=([a-z0-9]{8})&o=emaillist$/m;
  const m1 = c.text.match(SHARE_RE);
  ok(!!m1, 'Share it URL matches /c/<slug>?s=<8 chars>&o=emaillist');
  ok(c.html.includes('?s=' + (m1 ? m1[1] : '--------') + '&o=emaillist'), 'HTML Share it anchor uses the same tracked URL');
  const cFixed = composeEmail(idea, 'tin-hero', 'abcd1234');
  ok(cFixed.text.includes('Share it: https://pickmycostume.com/c/tin-hero?s=abcd1234&o=emaillist'), 'a passed-in share id is used verbatim');
  const data = (await import('file://' + path.join(TMP, 'send-instructions-data.mjs'))).INSTRUCTIONS_DATA;
  let bad = 0;
  for (const id of Object.keys(data)) {
    const t = composeEmail(data[id], id).text;
    if (!new RegExp('^Share it: https://pickmycostume\\.com/c/' + id + '\\?s=[a-z0-9]{8}&o=emaillist$', 'm').test(t)) bad++;
    if (!t.includes('pickmycostume.com/c/' + id + '?utm_source=email&utm_medium=plan&utm_campaign=' + id)) bad++;
  }
  ok(bad === 0, 'all ' + Object.keys(data).length + ' bank entries compose with tracked Share it + plan-UTM guide link');
  const sids = new Set();
  for (let k = 0; k < 5; k++) { const mm = composeEmail(data['tin-hero'], 'tin-hero').text.match(SHARE_RE); if (mm) sids.add(mm[1]); }
  ok(sids.size === 5, 'share ids are minted per send (5 distinct in 5 composes)');

  console.log('rate limiting');
  _resetRateLimit();
  let last;
  for (let k = 0; k < 6; k++) {
    last = await j(await onRequestPost({ request: mockReq({ email: 'r' + k + '@example.com', idea_id: 'tin-hero' }, '1.1.1.1'), env: {} }));
  }
  ok(last.status === 429 && last.body.error === 'rate_limited', '6th send in an hour trips 429');
  _resetRateLimit();
  r = await j(await onRequestPost({ request: mockReq({ email: 'fresh@example.com', idea_id: 'tin-hero' }, '1.1.1.1'), env: {} }));
  ok(r.status === 200 && r.body.ok, 'other IP unaffected');

  console.log('Resend call shape (mocked fetch)');
  const realFetch = global.fetch;
  let seen;
  global.fetch = async (url, opts) => { seen = { url, opts }; return { ok: true }; };
  _resetRateLimit();
  r = await j(await onRequestPost({
    request: mockReq({ email: 'buyer@example.com', idea_id: 'tin-hero', subject: 'PWNED', text: 'evil', body: 'evil' }, '2.2.2.2'),
    env: { RESEND_API_KEY: 're_test123' },
  }));
  const sent = JSON.parse(seen.opts.body);
  ok(r.status === 200 && r.body.ok && !r.body.dry_run, 'sends when key present');
  ok(seen.url === 'https://api.resend.com/emails', 'posts to resend api');
  ok(seen.opts.headers['Authorization'] === 'Bearer re_test123', 'bearer auth');
  ok(sent.from === 'Pick My Costume <hello@pickmycostume.com>', 'from is hello@pickmycostume.com');
  ok(sent.reply_to === 'Pick My Costume <hello@pickmycostume.com>', 'reply-to is hello@pickmycostume.com');
  ok(sent.to === 'buyer@example.com', 'to is the normalized address');
  ok(sent.subject.includes('Tin Hero') && !sent.subject.includes('PWNED'), 'subject from server data, client subject ignored');
  ok(!sent.text.includes('evil') && sent.text.includes('YOU NEED:'), 'body from server data, client body ignored');
  ok(!/[\r\n]/.test(sent.subject), 'sent subject has no CR/LF');

  global.fetch = async () => ({ ok: false, status: 500 });
  _resetRateLimit();
  r = await j(await onRequestPost({ request: mockReq({ email: 'z@example.com', idea_id: 'tin-hero' }, '3.3.3.3'), env: { RESEND_API_KEY: 're_test123' } }));
  ok(r.status === 502 && r.body.error === 'send_failed', 'resend 500 -> 502 send_failed');
  global.fetch = async () => { throw new Error('down'); };
  _resetRateLimit();
  r = await j(await onRequestPost({ request: mockReq({ email: 'z@example.com', idea_id: 'tin-hero' }, '3.3.3.3'), env: { RESEND_API_KEY: 're_test123' } }));
  ok(r.status === 502 && r.body.error === 'send_failed', 'fetch throw -> 502 send_failed');
  global.fetch = realFetch;

  console.log('no storage of addresses');
  ok(!/KV|D1|put\(|kv\./i.test(fnSrc.replace(/_resetRateLimit|hits\.(get|set|clear)/g, '')), 'no KV/D1/storage writes in handler');

  console.log('\n' + pass + ' passed, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error('HARNESS ERROR', e); process.exit(2); });
