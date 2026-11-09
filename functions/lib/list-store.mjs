// list-store.mjs — shared KV-backed email list store (system of record).
//
// Built 2026-11-01 (resend-unblock lane). Purpose: a site never needs a
// Resend Contacts-capable key at runtime to run a list. Signups,
// per-contact state (status / source / next_lesson / properties),
// unsubscribe tokens, and the suppression list all live in a Cloudflare
// KV namespace the site already controls. Resend is used ONLY to send,
// via one of two drivers:
//   (a) agent_bridge.py — the fleet agent syncs this store into a
//       Resend audience and/or runs the send pass using the vault's
//       stored full-access key (no key ever sits in a site's env), or
//   (b) a sending-scoped key in the site env for plain /emails calls,
//       reading recipients from this store instead of the Contacts API.
//
// Storage contract: any object with async get(key), put(key, value),
// delete(key), list({prefix}) -> {keys:[{name}]}. A real KV namespace
// binding satisfies it; the test harness uses an in-memory shim.
//
// Key layout inside the namespace:
//   sub:<email>        -> JSON contact record (see signup())
//   supp:<email>       -> JSON {email, ts, reason}  (hard suppression:
//                         bounce/complaint/manual — checked before sends)
//   rl:<ip>            -> signup rate-limit window (optional helper)
//
// Contact record:
//   { email, ts (ISO signup), status, source, next_lesson,
//     properties: {...}, unsubscribed: bool, unsub_ts, resend_id }
//
// Unsubscribe tokens: HMAC-SHA256(email, secret) base64url — the same
// scheme as Dadiosity's functions/lib/unsub.js, so tokens minted by
// either implementation validate in both.

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export function normalizeEmail(raw) {
  const email = String(raw || "").trim().toLowerCase();
  return EMAIL_RE.test(email) ? email : null;
}

function b64url(bytes) {
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export async function unsubToken(secret, email) {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(String(email).toLowerCase()));
  return b64url(new Uint8Array(sig));
}

export async function unsubTokenValid(secret, email, token) {
  if (!secret || !email || !token) return false;
  const expected = await unsubToken(secret, email);
  if (expected.length !== token.length) return false;
  let diff = 0;
  for (let i = 0; i < expected.length; i++) diff |= expected.charCodeAt(i) ^ token.charCodeAt(i);
  return diff === 0;
}

export class ListStore {
  constructor(kv, { prefix = "" } = {}) {
    if (!kv) throw new Error("ListStore needs a KV-like binding");
    this.kv = kv;
    this.prefix = prefix; // e.g. "dadiosity:" when several lists share one namespace
  }

  k(kind, email) { return this.prefix + kind + ":" + email; }

  async getContact(email) {
    const raw = await this.kv.get(this.k("sub", email));
    return raw ? JSON.parse(raw) : null;
  }

  async putContact(rec, opts = {}) {
    // SPEC-PMC-COLDQA1109-01 (2026-11-09): an optional ttlSeconds lets a
    // caller give the record a real KV expiry (the reminder list uses it
    // so the promised post-Oct-27 deletion happens in code, not just in
    // the privacy copy). No ttlSeconds = the old no-expiry behavior, so
    // every other caller is unchanged.
    const ttl = opts && opts.ttlSeconds;
    if (ttl && ttl > 60) {
      await this.kv.put(this.k("sub", rec.email), JSON.stringify(rec), { expirationTtl: Math.floor(ttl) });
    } else {
      await this.kv.put(this.k("sub", rec.email), JSON.stringify(rec));
    }
    return rec;
  }

  // Add a signup. A repeat signup is a duplicate and changes nothing,
  // EXCEPT a contact who left (unsubscribed / status "left"): a fresh
  // explicit opt-in rejoins them at the start, mirroring the live
  // Dadiosity signup semantics.
  async signup(email, { source = "web", properties = {}, startLesson = 1, ttlSeconds = null } = {}) {
    email = normalizeEmail(email);
    if (!email) return { ok: false, error: "bad-email" };
    const existing = await this.getContact(email);
    if (existing) {
      if (existing.unsubscribed || existing.status === "left") {
        const rec = {
          ...existing,
          unsubscribed: false,
          status: "active",
          source,
          next_lesson: startLesson,
          properties: { ...existing.properties, ...properties },
          rejoined_ts: new Date().toISOString()
        };
        await this.putContact(rec, { ttlSeconds });
        return { ok: true, rejoined: true, contact: rec };
      }
      return { ok: true, duplicate: true, contact: existing };
    }
    const rec = {
      email,
      ts: new Date().toISOString(),
      status: "active",
      source,
      next_lesson: startLesson,
      properties: { ...properties },
      unsubscribed: false,
      resend_id: null
    };
    await this.putContact(rec, { ttlSeconds });
    return { ok: true, contact: rec };
  }

  // One-click unsubscribe: token-gated, idempotent.
  async unsubscribe(email, token, secret) {
    email = normalizeEmail(email);
    if (!email) return { ok: false, error: "bad-email" };
    if (!(await unsubTokenValid(secret, email, token))) return { ok: false, error: "bad-token" };
    const rec = await this.getContact(email);
    if (!rec) return { ok: false, error: "not-found" };
    if (rec.unsubscribed) return { ok: true, already: true };
    rec.unsubscribed = true;
    rec.status = "left";
    rec.unsub_ts = new Date().toISOString();
    await this.putContact(rec);
    return { ok: true };
  }

  // Hard suppression (bounce / complaint / manual). Suppressed addresses
  // are excluded from every send list even if their record says active.
  async suppress(email, reason = "manual") {
    email = normalizeEmail(email);
    if (!email) return { ok: false, error: "bad-email" };
    await this.kv.put(this.k("supp", email), JSON.stringify({ email, ts: new Date().toISOString(), reason }));
    return { ok: true };
  }

  async isSuppressed(email) {
    return (await this.kv.get(this.k("supp", email))) !== null;
  }

  async listContacts() {
    const out = [];
    let cursor;
    do {
      const page = await this.kv.list({ prefix: this.prefix + "sub:", cursor });
      for (const key of page.keys) {
        const raw = await this.kv.get(key.name);
        if (raw) out.push(JSON.parse(raw));
      }
      cursor = page.list_complete ? undefined : page.cursor;
    } while (cursor);
    return out;
  }

  // The send driver's view: who gets mail in this pass.
  // status must match, not unsubscribed, not suppressed.
  async sendable({ status = "active" } = {}) {
    const all = await this.listContacts();
    const out = [];
    for (const rec of all) {
      if (rec.status !== status || rec.unsubscribed) continue;
      if (await this.isSuppressed(rec.email)) continue;
      out.push(rec);
    }
    return out;
  }

  // Advance a contact after a successful send (the sender's PATCH,
  // against our own store — no Contacts API involved).
  async advance(email, { by = 1, patch = {} } = {}) {
    const rec = await this.getContact(email);
    if (!rec) return { ok: false, error: "not-found" };
    if (typeof rec.next_lesson === "number") rec.next_lesson += by;
    Object.assign(rec, patch);
    rec.last_sent_ts = new Date().toISOString();
    await this.putContact(rec);
    return { ok: true, contact: rec };
  }

  // Export for the agent bridge (sync into a Resend audience).
  async exportAll() {
    const contacts = await this.listContacts();
    const suppressed = [];
    let cursor;
    do {
      const page = await this.kv.list({ prefix: this.prefix + "supp:", cursor });
      for (const key of page.keys) suppressed.push(key.name.slice((this.prefix + "supp:").length));
      cursor = page.list_complete ? undefined : page.cursor;
    } while (cursor);
    return { exported_at: new Date().toISOString(), contacts, suppressed };
  }
}
