// POST /send-instructions -- "Email me the instructions", for real.
// Billy 2026-09-28: the old mailto: fallback (user sends to themselves) was
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

import { INSTRUCTIONS_DATA } from './send-instructions-data.js';

const FROM = 'Pick My Costume <hello@pickmycostume.com>';
// Billy 2026-09-28: hello@pickmycostume.com is the confirmed sender AND the
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

// Strip CR/LF so a bank title can never become a header-injection vector.
function cleanHeader(s) {
  return String(s).replace(/[\r\n]+/g, ' ').slice(0, 140);
}

// Server-side composition. NOTE: Billy 2026-09-28 -- no guide/product link
// in the body. The email is the instructions, nothing else.
export function composeEmail(idea) {
  const lines = [];
  lines.push(idea.t.toUpperCase() + ' -- build instructions (via Pick My Costume)');
  lines.push('');
  lines.push('YOU NEED:');
  for (const x of idea.m) lines.push('- ' + x);
  lines.push('');
  lines.push('STEPS:');
  idea.s.forEach((x, i) => lines.push((i + 1) + '. ' + x));
  lines.push('');
  lines.push(idea.time + ' | ' + idea.cost + ' | ' + idea.effort);
  lines.push('');
  lines.push('-- Pick My Costume');
  return {
    subject: 'How to make: ' + idea.t + ' (Pick My Costume)',
    text: lines.join('\n'),
  };
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

  const composed = composeEmail(idea);
  const subject = cleanHeader(composed.subject);

  if (!env.RESEND_API_KEY) {
    // Staged: Billy hasn't connected Resend yet. Plumbing verified, nothing sent.
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
      body: JSON.stringify({ from: FROM, reply_to: FROM, to: email, subject: subject, text: composed.text }),
    });
  } catch (e) {
    return json({ ok: false, error: 'send_failed' }, 502);
  }
  if (!res.ok) return json({ ok: false, error: 'send_failed' }, 502);
  return json({ ok: true });
}
