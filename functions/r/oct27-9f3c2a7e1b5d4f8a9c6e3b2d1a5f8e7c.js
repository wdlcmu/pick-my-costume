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

function esc(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
function linkify(line) {
  return esc(line).replace(/https:\/\/[^\s)]+/g, (u) => `<a href="${u}">${u}</a>`);
}
const RAW_LINES = TEXT_BODY.split('\n');
// Join indented continuation lines onto the bullet they belong to, so each
// costume (text + link) becomes one logical line.
const LINES = [];
for (const line of RAW_LINES) {
  if (/^\s/.test(line) && line.trim() !== '' && LINES.length > 0 && LINES[LINES.length - 1].startsWith('- ')) {
    LINES[LINES.length - 1] += ' ' + line.trim();
  } else {
    LINES.push(line);
  }
}
const HTML_BODY = LINES.map((line) => {
  // Only the costume bullets are list items: "- " lines carrying their link.
  // ("- Billy" is a signature, not a bullet.)
  if (line.startsWith('- ') && line.includes('http')) return '<li>' + linkify(line.slice(2)) + '</li>';
  if (line.trim() === '') return '';
  return '<p>' + linkify(line) + '</p>';
}).join('\n')
  .replace(/((?:<li>.*<\/li>\n)+)/g, (m) => '<ul>\n' + m + '</ul>\n');

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
      html: `<!doctype html><html><body style="font-family:sans-serif;max-width:600px;margin:0 auto;">${HTML_BODY}</body></html>`,
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
