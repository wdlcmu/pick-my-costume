// POST /send-instructions -- "Email me the instructions", for real.
// 2026-09-28: the old mailto: fallback (user sends to themselves) was
// backwards. Now the visitor types their address and the SITE sends it.
//
// Trust model:
// - The client may ONLY supply {email, idea_id}. Subject and body are composed
//   SERVER-SIDE from INSTRUCTIONS_DATA (generated from the idea bank). Raw
//   body/subject text from the client is never accepted.
// - No email addresses are stored anywhere: send and forget.
// - Per-IP rate limit (in-memory, per isolate; fine at this volume).
// - No tracking pixels, no list machinery. One transactional send.
//
// Provider: Resend (Cloudflare's documented 2026 path for Workers/Pages).
// Requires env.RESEND_API_KEY. Without it the function answers dry_run:true
// so the frontend can be honest instead of pretending to send.
//
// 2026-10-02: template v2 (Billy-approved). composeEmail returns
// { subject, text, html, preheader }: branded HTML + plain-text fallback.
// No em dashes, no dollar figures, no tracking pixels.

import { INSTRUCTIONS_DATA } from './send-instructions-data.js';

const FROM = 'Pick My Costume <hello@pickmycostume.com>';
// 2026-09-28: hello@pickmycostume.com is the confirmed sender AND the
// default reply-to (matches the site's contact link). No gmail anywhere.
const RESEND_URL = 'https://api.resend.com/emails';

// Rate limit: 5 sends per IP per hour.
const WINDOW_MS = 60 * 60 * 1000;
const MAX_PER_WINDOW = 5;
const hits = new Map(); // ip -> {start, count}
function rateLimited(ip) {
  const now = Date.now();
  const h = hits.get(ip);
  if (!h || now - h.start > WINDOW_MS) { hits.set(ip, { start: now, count: 1 }); return false; }
  h.count++;
  return h.count > MAX_PER_WINDOW;
}
// Exported for the QA harness (hour-session/send-instructions-test.js).
export function _resetRateLimit() { hits.clear(); }

function validEmail(e) {
  if (typeof e !== 'string') return false;
  e = e.trim();
  if (e.length < 3 || e.length > 254) return false;
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(e);
}

// Escape bank strings for HTML output.
function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// Slugs are the INSTRUCTIONS_DATA keys; lock to lowercase alnum + dashes so
// a slug can never become a URL/header injection vector.
function cleanSlug(s) {
  const c = String(s || '').toLowerCase().replace(/[^a-z0-9-]/g, '').slice(0, 80);
  return c || 'costume';
}

// Strip CR/LF so a bank title can never become a header-injection vector.
function cleanHeader(s) {
  return String(s).replace(/[\r\n]+/g, ' ').slice(0, 140);
}

// Hands-on time for the subject: "20 min + 15 min drying" -> "20 min".
// Also tolerates the old bare format "20 min + drying" -> "20 min".
function handsOn(time) {
  const t = String(time || '').split('+')[0].trim();
  return t || String(time || '').trim();
}

// First sentence of the intro, for the one-liner + preheader.
function firstSentence(intro) {
  const s = String(intro || '').trim();
  if (!s) return '';
  const m = s.match(/^(.+?\.)\s/);
  return m ? m[1] : s;
}

// Server-side composition. idea = INSTRUCTIONS_DATA entry (+ optional
// .intro), slug = its key. Returns { subject, text, html, preheader }.
export function composeEmail(idea, slug) {
  slug = cleanSlug(slug);
  const title = String(idea.t);
  const guideUrl = 'https://pickmycostume.com/c/' + slug;
  const guideUtm = guideUrl + '?utm_source=email&utm_medium=plan&utm_campaign=' + slug;
  const shareUrl = guideUrl; // plain link for the "Share it" line
  const browseUtm = 'https://pickmycostume.com/?utm_source=email';
  const photoUrl = 'https://pickmycostume.com/photos/' + slug + '-480.webp';
  const privacyUrl = 'https://pickmycostume.com/privacy';
  const introOne = firstSentence(idea.intro);
  const preheader = introOne ||
    'Here is your game plan for the ' + title + '.';
  const subject = cleanHeader('Your costume plan: ' + title + ' (' + handsOn(idea.time) + ')');
  const statRow = idea.time + '  |  ' + idea.effort;

  // ---- Split steps into regular / safety / pro-finish ----
  const regular = [], safety = [], pro = [];
  for (const raw of idea.s) {
    const step = String(raw);
    if (/^safety\s*:/i.test(step)) safety.push(step.replace(/^safety\s*:\s*/i, ''));
    else if (/^optional pro finish\s*:/i.test(step)) pro.push(step.replace(/^optional pro finish\s*:\s*/i, ''));
    else regular.push(step);
  }

  // ================= PLAIN TEXT =================
  const t = [];
  t.push(subject);
  t.push('');
  if (introOne) { t.push(introOne); t.push(''); }
  t.push("Here's your game plan for the " + title + '.');
  t.push('Time: ' + statRow);
  t.push('');
  t.push('YOU NEED:');
  for (const x of idea.m) t.push('[ ] ' + x);
  t.push('');
  t.push('STEPS:');
  regular.forEach((x, i) => t.push((i + 1) + '. ' + x));
  for (const x of safety) { t.push(''); t.push('SAFETY: ' + x); }
  for (const x of pro) { t.push(''); t.push('PRO FINISH: ' + x); }
  t.push('');
  t.push('Open the full guide (photos, tips, answers):');
  t.push(guideUtm);
  t.push('');
  t.push('Share it: ' + shareUrl);
  t.push('Pick another costume: ' + browseUtm);
  t.push('');
  t.push('Hope it turns out great. Happy Halloween!');
  t.push('- Billy, Pick My Costume');
  t.push('');
  t.push('---');
  t.push('You got this because you tapped "Email me the instructions" on');
  t.push('pickmycostume.com. Nothing is stored and you are not on any list.');
  t.push('Privacy: ' + privacyUrl);
  t.push('Want one reminder on Oct 27? Tick "Remind me Oct 27" on the');
  t.push('results page. One email, then you are off the list.');
  const text = t.join('\n');

  // ================= HTML =================
  const F = "font-family:Arial,Helvetica,sans-serif;";
  const mats = idea.m.map(x =>
    '<tr><td valign="top" style="padding:0 10px 8px 0;font-size:16px;color:#b4530a;">&#9744;</td>' +
    '<td valign="top" style="padding:0 0 8px 0;font-size:15px;line-height:1.55;color:#2b2b2b;">' + esc(x) + '</td></tr>'
  ).join('');
  const stepsHtml = regular.map((x, i) =>
    '<tr><td valign="top" style="padding:0 10px 12px 0;font-weight:700;color:#b4530a;font-size:15px;">' + (i + 1) + '.</td>' +
    '<td valign="top" style="padding:0 0 12px 0;font-size:15px;line-height:1.6;color:#2b2b2b;">' + esc(x) + '</td></tr>'
  ).join('');
  const safetyHtml = safety.map(x =>
    '<tr><td style="background:#fff8e1;border-left:4px solid #f0c419;padding:12px 14px;border-radius:0 8px 8px 0;">' +
    '<p style="margin:0;' + F + 'font-size:14px;line-height:1.55;color:#5c4a00;"><strong>&#9888; Safety:</strong> ' + esc(x) + '</p>' +
    '</td></tr><tr><td style="height:10px;font-size:0;line-height:0;">&nbsp;</td></tr>'
  ).join('');
  const proHtml = pro.map(x =>
    '<tr><td style="background:#f3efff;border-left:4px solid #7a5fc4;padding:12px 14px;border-radius:0 8px 8px 0;">' +
    '<p style="margin:0;' + F + 'font-size:14px;line-height:1.55;color:#3a2f6b;"><strong>&#11088; Pro finish:</strong> ' + esc(x) + '</p>' +
    '</td></tr><tr><td style="height:10px;font-size:0;line-height:0;">&nbsp;</td></tr>'
  ).join('');

  const html =
'<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
'<meta name="color-scheme" content="light dark"><meta name="supported-color-schemes" content="light dark">' +
'<title>' + esc(subject) + '</title></head>' +
'<body style="margin:0;padding:0;background:#fdf3e3;' + F + '">' +
// Preheader (hidden preview text)
'<div style="display:none;max-height:0;overflow:hidden;opacity:0;">' + esc(preheader) +
'<span style="display:none;">&#847;&zwnj;&nbsp;&#8199;&shy;&#847;&zwnj;&nbsp;&#8199;&shy;</span></div>' +
'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#fdf3e3;"><tr><td align="center" style="padding:24px 12px;">' +
'<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:14px;overflow:hidden;">' +
// 1. Header bar with wordmark (matches the site header: pumpkin + name)
'<tr><td style="background:#241a38;padding:16px 24px;text-align:center;">' +
'<span style="' + F + 'font-size:19px;font-weight:800;color:#ffffff;letter-spacing:0.3px;">&#127875; Pick My Costume</span>' +
'</td></tr>' +
// 2. Costume photo (absolute URL, alt text)
'<tr><td style="padding:0;">' +
'<img src="' + photoUrl + '" alt="' + esc(title) + ' costume" width="600" style="display:block;width:100%;max-width:600px;height:auto;border:0;">' +
'</td></tr>' +
// 3. Name + one-line intro
'<tr><td style="padding:24px 28px 6px 28px;">' +
'<h1 style="margin:0 0 8px 0;' + F + 'font-size:26px;line-height:1.25;color:#241a38;">' + esc(title) + '</h1>' +
(introOne ? '<p style="margin:0;' + F + 'font-size:15px;line-height:1.6;color:#4a4a4a;">' + esc(introOne) + '</p>' : '') +
'</td></tr>' +
// 4. Stat row
'<tr><td style="padding:10px 28px 0 28px;">' +
'<p style="margin:0;' + F + 'font-size:14px;font-weight:700;color:#b4530a;">&#9201; ' + esc(statRow) + '</p>' +
'</td></tr>' +
// Opener
'<tr><td style="padding:12px 28px 0 28px;">' +
'<p style="margin:0;' + F + 'font-size:15px;line-height:1.6;color:#2b2b2b;">Here is your game plan for the <strong>' + esc(title) + '</strong>. ' +
'Gather the stuff below, give yourself the full time including drying, and you are set.</p>' +
'</td></tr>' +
// 5. Materials checklist
'<tr><td style="padding:20px 28px 0 28px;">' +
'<h2 style="margin:0 0 12px 0;' + F + 'font-size:18px;color:#241a38;">You need</h2>' +
'<table role="presentation" cellpadding="0" cellspacing="0" width="100%">' + mats + '</table>' +
'</td></tr>' +
// 6. Steps + safety callout + pro-finish tip box
'<tr><td style="padding:20px 28px 0 28px;">' +
'<h2 style="margin:0 0 12px 0;' + F + 'font-size:18px;color:#241a38;">Steps</h2>' +
'<table role="presentation" cellpadding="0" cellspacing="0" width="100%">' + stepsHtml + '</table>' +
'</td></tr>' +
(safetyHtml || proHtml ? '<tr><td style="padding:6px 28px 0 28px;"><table role="presentation" cellpadding="0" cellspacing="0" width="100%">' + safetyHtml + proHtml + '</table></td></tr>' : '') +
// 7. Big orange button
'<tr><td align="center" style="padding:22px 28px 6px 28px;">' +
'<a href="' + guideUtm + '" style="display:inline-block;background:#ff8c1a;color:#241a38;font-weight:800;font-size:16px;' + F + 'text-decoration:none;padding:14px 34px;border-radius:999px;">Open the full guide &rarr;</a>' +
'<p style="margin:10px 0 0 0;' + F + 'font-size:13px;color:#6b6b6b;">Photos, tips, and answers to common questions.</p>' +
'</td></tr>' +
// 8. Secondary line
'<tr><td align="center" style="padding:8px 28px 0 28px;">' +
'<p style="margin:0;' + F + 'font-size:14px;color:#4a4a4a;"><a href="' + shareUrl + '" style="color:#7a5fc4;">Share it</a>' +
'<span style="color:#bdbdbd;"> &nbsp;·&nbsp; </span>' +
'<a href="' + browseUtm + '" style="color:#7a5fc4;">Pick another costume</a></p>' +
'</td></tr>' +
// Sign-off
'<tr><td style="padding:20px 28px 28px 28px;">' +
'<p style="margin:0;' + F + 'font-size:15px;line-height:1.6;color:#2b2b2b;">Hope it turns out great. Happy Halloween!<br><strong>- Billy</strong></p>' +
'</td></tr>' +
'</table>' +
// 9. Footer
'<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;"><tr><td style="padding:16px 8px 0 8px;">' +
'<p style="margin:0 0 8px 0;' + F + 'font-size:12px;line-height:1.6;color:#8a7a5c;">You got this because you tapped &ldquo;Email me the instructions&rdquo; on pickmycostume.com. Nothing is stored and you are not on any list. <a href="' + privacyUrl + '" style="color:#7a5fc4;">Privacy</a></p>' +
'<p style="margin:0;' + F + 'font-size:12px;line-height:1.6;color:#8a7a5c;">Want one reminder on Oct 27? Tick &ldquo;Remind me Oct 27&rdquo; on the results page. One email, then you are off the list.</p>' +
'</td></tr></table>' +
'</td></tr></table></body></html>';

  return { subject, text, html, preheader };
}

function json(obj, status) {
  return new Response(JSON.stringify(obj), {
    status: status || 200,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });
}

export async function onRequestPost(context) {
  const { request, env } = context;
  let body;
  try {
    body = await request.json();
  } catch (e) {
    return json({ ok: false, error: 'bad_request' }, 400);
  }
  const email = typeof body.email === 'string' ? body.email.trim().toLowerCase() : '';
  const ideaId = typeof body.idea_id === 'string' ? body.idea_id.trim() : '';
  if (!validEmail(email)) return json({ ok: false, error: 'bad_email' }, 400);
  const idea = INSTRUCTIONS_DATA[ideaId];
  if (!idea) return json({ ok: false, error: 'unknown_idea' }, 404);

  const ip = request.headers.get('cf-connecting-ip') || 'unknown';
  if (rateLimited(ip)) return json({ ok: false, error: 'rate_limited' }, 429);

  const composed = composeEmail(idea, ideaId);
  const subject = cleanHeader(composed.subject);

  if (!env.RESEND_API_KEY) {
    // Staged: Resend hasn't been connected yet. Plumbing verified, nothing sent.
    return json({ ok: true, dry_run: true });
  }
  let res;
  try {
    res = await fetch(RESEND_URL, {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + env.RESEND_API_KEY,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ from: FROM, reply_to: FROM, to: email, subject: subject, text: composed.text, html: composed.html }),
    });
  } catch (e) {
    return json({ ok: false, error: 'send_failed' }, 502);
  }
  if (!res.ok) return json({ ok: false, error: 'send_failed' }, 502);
  return json({ ok: true });
}
