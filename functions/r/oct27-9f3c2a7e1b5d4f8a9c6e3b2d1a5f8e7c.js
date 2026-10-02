// POST /r/<capability-path> -- one-time Oct 27 reminder broadcast sender.
//
// Why this exists: the Resend API key and audience ID live as Cloudflare
// production secrets (unreadable from outside). This function runs inside
// that runtime, so it can send the broadcast Billy approved Oct 1, 2026.
// Triggered by Billy's Oct 27 cron; the path itself is an unguessable
// 128-bit capability URL (never linked anywhere on the site).
//
// Safeguards:
// - Date gate: refuses unless it is Oct 27, 2026 in America/Los_Angeles.
// - Idempotency: checks Resend for an already-sent broadcast with our
//   subject before sending; a second trigger returns already_sent.
// - No request body fields are honored; the content is fixed to the copy
//   Billy approved (oct-27-reminder-email-FINAL-v4.md; v4 removes dollar
//   figures per his Oct 1 no-dollar decision, pending his re-approval).
// - If REMINDER_AUDIENCE_ID is missing it returns unconfigured (no send).

const SUBJECT = 'Halloween is 4 days away. You already own a costume.';
const FROM = 'Pick My Costume <hello@pickmycostume.com>';

const TEXT_BODY = `Hi,

You asked for one email on Oct 27, so here it is.

No costume yet? You probably already own one.

Pick My Costume's pantry check ranks all 164 costume ideas by what you can make tonight from stuff already in your house:

https://pickmycostume.com/pantry

Here are 16 that are genuinely make-tonight, with real build times straight from the guides.

Most of these build from stuff already in your house.

- Classic Ghost (10 min): white sheet, black marker for the eyes, scissors
  https://pickmycostume.com/c/classic-ghost
- Ninja (10 min + drying): all-black closet outfit, headband wrap, an old tie as the sash
  https://pickmycostume.com/c/ninja
- Emoji Crew (15 min): yellow tee per person, paper plate face, markers
  https://pickmycostume.com/c/emoji-crew
- Breakfast Buffet (25 min): cardboard from boxes you have, markers, string
  https://pickmycostume.com/c/breakfast-buffet
- Coffee Cup (20 min): white sheet or trash bag, a cardboard tube, a paper lid
  https://pickmycostume.com/c/coffee-cup
- Salt & Pepper (15 min + drying): white outfit for Salt, black for Pepper, cardboard shaker tops
  https://pickmycostume.com/c/salt-pepper
- Decades Crew (20 min): your own closet clothes, a hand-lettered decade card
  https://pickmycostume.com/c/decades-crew
- Plug and Socket (45 min + drying): two cardboard panels, gray and white paint
  https://pickmycostume.com/c/plug-socket
- Player One & Two (20 min): matching tees, iron-on 1 and 2
  https://pickmycostume.com/c/player-one-two
- Ghost Hunters (30 min): thrift-store khaki outfit, a cardboard box pack, paper name patches
  https://pickmycostume.com/c/ghost-hunters
- Ice Cream Cone (20 min + drying): paper cone hat, white tee, paper-dot sprinkles
  https://pickmycostume.com/c/ice-cream-cone
- Cereal Crew (20 min): solid-color shirt and pants, empty cereal boxes
  https://pickmycostume.com/c/cereal-crew
- Block Game Crew (45 min + drying): big cardboard boxes, paint in hero colors
  https://pickmycostume.com/c/block-game-crew
- Fairy Tale Princesses (15 min + drying): a dress from the closet, a cereal-box crown, gold paint
  https://pickmycostume.com/c/fairy-tale-princesses
- Block Monster (30 min + drying): a solid sweatsuit, cardboard blocks, tape
  https://pickmycostume.com/c/block-monster
- Space Crewmate (20 min): a plain sweatsuit, cardboard and foil for the pack
  https://pickmycostume.com/c/space-crewmate

Every guide shows the build time and what you need before you start.

I had AI help me build this site, and I keep the build times honest.

That's the one email. You're off the list.

Happy Halloween.

- Billy
Pick My Costume (https://pickmycostume.com)

P.S. If a friend is still costumeless, the 2-minute quiz picks one for them: https://pickmycostume.com`;

// 2026-10-02: branded template (Billy-approved v4 copy in the template).
// TEXT_BODY above stays VERBATIM. Date gate, idempotency, audience flow untouched.
const OCT27_HTML_BODY = "<!DOCTYPE html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><meta name=\"color-scheme\" content=\"light dark\"><meta name=\"supported-color-schemes\" content=\"light dark\"><title>Halloween is 4 days away. You already own a costume.</title></head><body style=\"margin:0;padding:0;background:#fdf3e3;font-family:Arial,Helvetica,sans-serif;\"><div style=\"display:none;max-height:0;overflow:hidden;opacity:0;\">You asked for one email on Oct 27, so here it is.</div><table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"background:#fdf3e3;\"><tr><td align=\"center\" style=\"padding:24px 12px;\"><table role=\"presentation\" width=\"600\" cellpadding=\"0\" cellspacing=\"0\" style=\"max-width:600px;width:100%;background:#ffffff;border-radius:14px;overflow:hidden;\"><tr><td style=\"background:#241a38;padding:16px 24px;text-align:center;\"><span style=\"font-family:Arial,Helvetica,sans-serif;font-size:19px;font-weight:800;color:#ffffff;letter-spacing:0.3px;\">&#127875; Pick My Costume</span></td></tr><tr><td style=\"padding:24px 28px 8px 28px;\"><h1 style=\"margin:0 0 14px 0;font-family:Arial,Helvetica,sans-serif;font-size:24px;line-height:1.3;color:#241a38;\">Halloween is 4 days away. You already own a costume.</h1><p style=\"margin:0 0 14px 0;font-size:15px;line-height:1.6;color:#2b2b2b;\">Hi,</p>\n<p style=\"margin:0 0 14px 0;font-size:15px;line-height:1.6;color:#2b2b2b;\">You asked for one email on Oct 27, so here it is.</p>\n<p style=\"margin:0 0 14px 0;font-size:15px;line-height:1.6;color:#2b2b2b;\">No costume yet? You probably already own one.</p>\n<p style=\"margin:0 0 14px 0;font-size:15px;line-height:1.6;color:#2b2b2b;\">Pick My Costume's pantry check ranks all 164 costume ideas by what you can make tonight from stuff already in your house:</p>\n<table role=\"presentation\" cellpadding=\"0\" cellspacing=\"0\" style=\"margin:6px 0 14px 0;\"><tr><td align=\"center\"><a href=\"https://pickmycostume.com/pantry\" style=\"display:inline-block;background:#ff8c1a;color:#241a38;font-weight:800;font-size:16px;font-family:Arial,Helvetica,sans-serif;text-decoration:none;padding:14px 34px;border-radius:999px;\">Check the pantry ranking &rarr;</a></td></tr></table>\n<p style=\"margin:0 0 14px 0;font-size:15px;line-height:1.6;color:#2b2b2b;\">Here are 16 that are genuinely make-tonight, with real build times straight from the guides.</p>\n<p style=\"margin:0 0 14px 0;font-size:15px;line-height:1.6;color:#2b2b2b;\">Most of these build from stuff already in your house.</p>\n<li style=\"margin:0 0 10px 0;font-size:15px;line-height:1.55;color:#2b2b2b;\">Classic Ghost (10 min): white sheet, black marker for the eyes, scissors <a href=\"https://pickmycostume.com/c/classic-ghost\" style=\"color:#7a5fc4;font-weight:700;\">Build guide &rarr;</a></li>\n<li style=\"margin:0 0 10px 0;font-size:15px;line-height:1.55;color:#2b2b2b;\">Ninja (10 min + drying): all-black closet outfit, headband wrap, an old tie as the sash <a href=\"https://pickmycostume.com/c/ninja\" style=\"color:#7a5fc4;font-weight:700;\">Build guide &rarr;</a></li>\n<li style=\"margin:0 0 10px 0;font-size:15px;line-height:1.55;color:#2b2b2b;\">Emoji Crew (15 min): yellow tee per person, paper plate face, markers <a href=\"https://pickmycostume.com/c/emoji-crew\" style=\"color:#7a5fc4;font-weight:700;\">Build guide &rarr;</a></li>\n<li style=\"margin:0 0 10px 0;font-size:15px;line-height:1.55;color:#2b2b2b;\">Breakfast Buffet (25 min): cardboard from boxes you have, markers, string <a href=\"https://pickmycostume.com/c/breakfast-buffet\" style=\"color:#7a5fc4;font-weight:700;\">Build guide &rarr;</a></li>\n<li style=\"margin:0 0 10px 0;font-size:15px;line-height:1.55;color:#2b2b2b;\">Coffee Cup (20 min): white sheet or trash bag, a cardboard tube, a paper lid <a href=\"https://pickmycostume.com/c/coffee-cup\" style=\"color:#7a5fc4;font-weight:700;\">Build guide &rarr;</a></li>\n<li style=\"margin:0 0 10px 0;font-size:15px;line-height:1.55;color:#2b2b2b;\">Salt &amp; Pepper (15 min + drying): white outfit for Salt, black for Pepper, cardboard shaker tops <a href=\"https://pickmycostume.com/c/salt-pepper\" style=\"color:#7a5fc4;font-weight:700;\">Build guide &rarr;</a></li>\n<li style=\"margin:0 0 10px 0;font-size:15px;line-height:1.55;color:#2b2b2b;\">Decades Crew (20 min): your own closet clothes, a hand-lettered decade card <a href=\"https://pickmycostume.com/c/decades-crew\" style=\"color:#7a5fc4;font-weight:700;\">Build guide &rarr;</a></li>\n<li style=\"margin:0 0 10px 0;font-size:15px;line-height:1.55;color:#2b2b2b;\">Plug and Socket (45 min + drying): two cardboard panels, gray and white paint <a href=\"https://pickmycostume.com/c/plug-socket\" style=\"color:#7a5fc4;font-weight:700;\">Build guide &rarr;</a></li>\n<li style=\"margin:0 0 10px 0;font-size:15px;line-height:1.55;color:#2b2b2b;\">Player One &amp; Two (20 min): matching tees, iron-on 1 and 2 <a href=\"https://pickmycostume.com/c/player-one-two\" style=\"color:#7a5fc4;font-weight:700;\">Build guide &rarr;</a></li>\n<li style=\"margin:0 0 10px 0;font-size:15px;line-height:1.55;color:#2b2b2b;\">Ghost Hunters (30 min): thrift-store khaki outfit, a cardboard box pack, paper name patches <a href=\"https://pickmycostume.com/c/ghost-hunters\" style=\"color:#7a5fc4;font-weight:700;\">Build guide &rarr;</a></li>\n<li style=\"margin:0 0 10px 0;font-size:15px;line-height:1.55;color:#2b2b2b;\">Ice Cream Cone (20 min + drying): paper cone hat, white tee, paper-dot sprinkles <a href=\"https://pickmycostume.com/c/ice-cream-cone\" style=\"color:#7a5fc4;font-weight:700;\">Build guide &rarr;</a></li>\n<li style=\"margin:0 0 10px 0;font-size:15px;line-height:1.55;color:#2b2b2b;\">Cereal Crew (20 min): solid-color shirt and pants, empty cereal boxes <a href=\"https://pickmycostume.com/c/cereal-crew\" style=\"color:#7a5fc4;font-weight:700;\">Build guide &rarr;</a></li>\n<li style=\"margin:0 0 10px 0;font-size:15px;line-height:1.55;color:#2b2b2b;\">Block Game Crew (45 min + drying): big cardboard boxes, paint in hero colors <a href=\"https://pickmycostume.com/c/block-game-crew\" style=\"color:#7a5fc4;font-weight:700;\">Build guide &rarr;</a></li>\n<li style=\"margin:0 0 10px 0;font-size:15px;line-height:1.55;color:#2b2b2b;\">Fairy Tale Princesses (15 min + drying): a dress from the closet, a cereal-box crown, gold paint <a href=\"https://pickmycostume.com/c/fairy-tale-princesses\" style=\"color:#7a5fc4;font-weight:700;\">Build guide &rarr;</a></li>\n<li style=\"margin:0 0 10px 0;font-size:15px;line-height:1.55;color:#2b2b2b;\">Block Monster (30 min + drying): a solid sweatsuit, cardboard blocks, tape <a href=\"https://pickmycostume.com/c/block-monster\" style=\"color:#7a5fc4;font-weight:700;\">Build guide &rarr;</a></li>\n<li style=\"margin:0 0 10px 0;font-size:15px;line-height:1.55;color:#2b2b2b;\">Space Crewmate (20 min): a plain sweatsuit, cardboard and foil for the pack <a href=\"https://pickmycostume.com/c/space-crewmate\" style=\"color:#7a5fc4;font-weight:700;\">Build guide &rarr;</a></li>\n<p style=\"margin:0 0 14px 0;font-size:15px;line-height:1.6;color:#2b2b2b;\">Every guide shows the build time and what you need before you start.</p>\n<p style=\"margin:0 0 14px 0;font-size:15px;line-height:1.6;color:#2b2b2b;\">I had AI help me build this site, and I keep the build times honest.</p>\n<p style=\"margin:0 0 14px 0;font-size:15px;line-height:1.6;color:#2b2b2b;\">That's the one email. You're off the list.</p>\n<p style=\"margin:0 0 14px 0;font-size:15px;line-height:1.6;color:#2b2b2b;\">Happy Halloween.</p>\n<p style=\"margin:18px 0 0 0;font-size:15px;line-height:1.6;color:#2b2b2b;\"><strong>- Billy</strong></p>\n<p style=\"margin:0 0 14px 0;font-size:15px;line-height:1.6;color:#2b2b2b;\">Pick My Costume (<a href=\"https://pickmycostume.com\" style=\"color:#7a5fc4;\">https://pickmycostume.com</a>)</p>\n<p style=\"margin:0 0 14px 0;font-size:15px;line-height:1.6;color:#2b2b2b;\">P.S. If a friend is still costumeless, the 2-minute quiz picks one for them: <a href=\"https://pickmycostume.com\" style=\"color:#7a5fc4;\">https://pickmycostume.com</a></p></td></tr></table><table role=\"presentation\" width=\"600\" cellpadding=\"0\" cellspacing=\"0\" style=\"max-width:600px;width:100%;\"><tr><td style=\"padding:16px 8px 0 8px;\"><p style=\"margin:0 0 8px 0;font-family:Arial,Helvetica,sans-serif;font-size:12px;line-height:1.6;color:#8a7a5c;\">That was the one email, as promised. Your address is off the list. <a href=\"https://pickmycostume.com/privacy\" style=\"color:#7a5fc4;\">Privacy</a></p></td></tr></table></td></tr></table></body></html>";

function json(obj, status) {
  return new Response(JSON.stringify(obj), {
    status: status || 200,
    headers: { 'Content-Type': 'application/json' },
  });
}

function isSendDay() {
  // Oct 27, 2026 in America/Los_Angeles.
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Los_Angeles',
    year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(new Date());
  const get = (t) => parts.find((p) => p.type === t).value;
  return get('year') === '2026' && get('month') === '10' && get('day') === '27';
}

async function resend(path, apiKey, opts) {
  const r = await fetch('https://api.resend.com' + path, {
    method: (opts && opts.method) || 'GET',
    headers: {
      'Authorization': 'Bearer ' + apiKey,
      'Content-Type': 'application/json',
    },
    body: opts && opts.body ? JSON.stringify(opts.body) : undefined,
  });
  let data = null;
  try { data = await r.json(); } catch (e) { /* non-JSON */ }
  return { status: r.status, ok: r.ok, data };
}

export async function onRequestPost(context) {
  const { env } = context;

  if (!isSendDay()) {
    return json({ ok: false, reason: 'not-send-day' }, 400);
  }
  if (!env.RESEND_API_KEY || !env.REMINDER_AUDIENCE_ID) {
    return json({ ok: false, reason: 'unconfigured' }, 400);
  }

  // Idempotency: never send twice.
  const list = await resend('/broadcasts', env.RESEND_API_KEY);
  if (list.ok && Array.isArray(list.data && list.data.data)) {
    const prior = list.data.data.find(
      (b) => b.subject === SUBJECT && (b.status === 'sent' || b.status === 'sending' || b.status === 'scheduled')
    );
    if (prior) return json({ ok: true, already_sent: true, broadcast_id: prior.id });
  }

  const created = await resend('/broadcasts', env.RESEND_API_KEY, {
    method: 'POST',
    body: {
      audience_id: env.REMINDER_AUDIENCE_ID,
      from: FROM,
      subject: SUBJECT,
      html: OCT27_HTML_BODY,
      text: TEXT_BODY,
    },
  });
  if (!created.ok || !created.data || !created.data.id) {
    return json({ ok: false, reason: 'broadcast-create-failed', status: created.status, detail: created.data }, 502);
  }

  const sent = await resend('/broadcasts/' + created.data.id + '/send', env.RESEND_API_KEY, { method: 'POST' });
  if (!sent.ok) {
    return json({ ok: false, reason: 'broadcast-send-failed', broadcast_id: created.data.id, status: sent.status, detail: sent.data }, 502);
  }
  return json({ ok: true, broadcast_id: created.data.id });
}

// Non-POST methods: not allowed.
export async function onRequest(context) {
  if (context.request.method === 'POST') return onRequestPost(context);
  return json({ ok: false, reason: 'method-not-allowed' }, 405);
}
