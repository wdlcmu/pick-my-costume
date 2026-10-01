// POST /reminder-signup -- "One email on Oct 27" reminder list.
//
// Trust model (mirrors send-instructions.js):
// - The client may ONLY supply {email, source}. No other fields are accepted.
// - Storage: the address is added as a contact to a Resend audience
//   (env.RESEND_API_KEY + env.REMINDER_AUDIENCE_ID). One audience = one list,
//   and unsubscribing is handled by Resend.
// - Without those env vars the function answers {ok:false, reason:"unconfigured"}
//   so the frontend degrades honestly instead of pretending to save.
// - Per-IP rate limit (in-memory, per isolate; fine at this volume).
// - No tracking pixels. The single Oct 27 email is staged for Billy's
//   explicit approval -- nothing sends from this function.

const RESEND_URL = 'https://api.resend.com/audiences/';
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

const WINDOW_MS = 60 * 60 * 1000;
const MAX_PER_WINDOW = 10;
const hits = new Map(); // ip -> {start, count}
function rateLimited(ip) {
  const now = Date.now();
  const h = hits.get(ip);
  if (!h || now - h.start > WINDOW_MS) { hits.set(ip, { start: now, count: 1 }); return false; }
  h.count++;
  return h.count > MAX_PER_WINDOW;
}

function json(obj, status) {
  return new Response(JSON.stringify(obj), {
    status: status || 200,
    headers: { 'Content-Type': 'application/json' }
  });
}

export async function onRequestPost(context) {
  const { request, env } = context;
  let body = {};
  try { body = await request.json(); } catch (e) { return json({ ok: false, reason: 'bad-body' }, 400); }
  const email = String(body.email || '').trim().toLowerCase();
  if (!EMAIL_RE.test(email)) return json({ ok: false, reason: 'bad-email' }, 400);

  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
  if (rateLimited(ip)) return json({ ok: false, reason: 'rate-limited' }, 429);

  if (!env.RESEND_API_KEY || !env.REMINDER_AUDIENCE_ID) {
    return json({ ok: false, reason: 'unconfigured' });
  }

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
      return json({ ok: false, reason: 'provider-error' }, 502);
    }
    return json({ ok: true });
  } catch (e) {
    return json({ ok: false, reason: 'provider-error' }, 502);
  }
}
