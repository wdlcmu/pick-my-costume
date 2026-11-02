// POST /reminder-signup -- the Pick My Costume reminder list.
//
// Trust model (mirrors send-instructions.js):
// - The client may ONLY supply {email, source}. No other fields are accepted.
// - Storage is KV-FIRST (2026-11-01, resend-unblock consumers lane):
//   the address is written to the project's REMINDERS KV namespace via
//   the shared list-store module (functions/lib/list-store.mjs), with
//   the "pmc:" list prefix. KV is the system of record, so the list
//   works with NO Resend key in this project's env at all. The fleet
//   agent bridge (builds/resend-unblock-2026-11-01/agent_bridge.py)
//   syncs the KV store into the "Oct 27 reminder" Resend audience
//   (d88543c4-d1bb-4fbd-b5b9-d74bd1753e6a) for any future approved send.
// - Fallback: if the KV binding is ever absent but the legacy Resend
//   env (RESEND_API_KEY + REMINDER_AUDIENCE_ID) is present, the old
//   direct-to-audience behavior runs unchanged.
// - With neither configured the function answers
//   {ok:false, reason:"unconfigured"} so the frontend degrades
//   honestly instead of pretending to save.
// - Per-IP rate limit: KV-backed window when KV is present (the
//   Dadiosity pattern), in-memory per isolate otherwise.
// - Nothing sends from this function, ever. Any future reminder email
//   is staged for Billy's explicit approval of the exact content.

import { ListStore } from "./lib/list-store.mjs";

const RESEND_URL = 'https://api.resend.com/audiences/';
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const LIST_PREFIX = "pmc:";

const WINDOW_MS = 60 * 60 * 1000;
const MAX_PER_WINDOW = 10;
const hits = new Map(); // ip -> {start, count}
function rateLimitedMemory(ip) {
  const now = Date.now();
  const h = hits.get(ip);
  if (!h || now - h.start > WINDOW_MS) { hits.set(ip, { start: now, count: 1 }); return false; }
  h.count++;
  return h.count > MAX_PER_WINDOW;
}

async function rateLimitedKV(kv, ip) {
  const key = LIST_PREFIX + "rl:" + ip;
  const now = Date.now();
  let stamps = [];
  try {
    const raw = await kv.get(key);
    if (raw) stamps = JSON.parse(raw);
  } catch (e) { /* unreadable window = start fresh */ }
  stamps = stamps.filter(function (t) { return now - t < WINDOW_MS; });
  if (stamps.length >= MAX_PER_WINDOW) return true;
  stamps.push(now);
  try { await kv.put(key, JSON.stringify(stamps), { expirationTtl: 3600 }); } catch (e) { /* best effort */ }
  return false;
}

function json(obj, status) {
  return new Response(JSON.stringify(obj), {
    status: status || 200,
    headers: { 'Content-Type': 'application/json' }
  });
}

async function signupKV(env, email, source) {
  const store = new ListStore(env.REMINDERS, { prefix: LIST_PREFIX });
  // startLesson null: a reminder list has no lesson ladder, and a null
  // next_lesson keeps the bridge from sending that property to Resend.
  const r = await store.signup(email, { source: source || "web", startLesson: null });
  if (!r.ok) return json({ ok: false, reason: r.error || 'bad-email' }, 400);
  if (r.duplicate) return json({ ok: true, duplicate: true });
  if (r.rejoined) return json({ ok: true, rejoined: true });
  return json({ ok: true, stored: 'kv' });
}

async function signupResendLegacy(env, email) {
  try {
    const r = await fetch(RESEND_URL + encodeURIComponent(env.REMINDER_AUDIENCE_ID) + '/contacts', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + env.RESEND_API_KEY,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email: email, unsubscribed: false })
    });
    if (!r.ok) {
      // Already-subscribed (409) still counts as success for the visitor.
      if (r.status === 409) return json({ ok: true, duplicate: true });
      // 2026-10-31 (Lane 4): provider errors answer 200, not 502. A 502
      // from a Pages Function is replaced at the edge by Cloudflare's
      // plain-text error page, so the client's r.json() threw and every
      // provider failure collapsed into reason "network" -- the endpoint
      // measured nothing true. 200 + this JSON keeps the honest degrade
      // (and the real reason) reachable end to end.
      return json({ ok: false, reason: 'provider-error' });
    }
    return json({ ok: true });
  } catch (e) {
    return json({ ok: false, reason: 'provider-error' });
  }
}

export async function onRequestPost(context) {
  const { request, env } = context;
  let body = {};
  try { body = await request.json(); } catch (e) { return json({ ok: false, reason: 'bad-body' }, 400); }
  const email = String(body.email || '').trim().toLowerCase();
  if (!EMAIL_RE.test(email)) return json({ ok: false, reason: 'bad-email' }, 400);
  const source = String(body.source || 'web').slice(0, 40);

  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
  if (env.REMINDERS) {
    if (ip !== 'unknown' && await rateLimitedKV(env.REMINDERS, ip)) {
      return json({ ok: false, reason: 'rate-limited' }, 429);
    }
  } else if (rateLimitedMemory(ip)) {
    return json({ ok: false, reason: 'rate-limited' }, 429);
  }

  if (env.REMINDERS) {
    try {
      return await signupKV(env, email, source);
    } catch (e) {
      return json({ ok: false, reason: 'provider-error' });
    }
  }

  if (!env.RESEND_API_KEY || !env.REMINDER_AUDIENCE_ID) {
    return json({ ok: false, reason: 'unconfigured' });
  }
  return signupResendLegacy(env, email);
}
