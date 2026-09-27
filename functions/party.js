// Per-party og injection for /party invite links.
// Regenerate with: python3 hour-session/build_party.py (emits this file
// from THEMES -- do not hand-edit the table).
//
// party.html is a static file, so every forwarded invite unfurls in chat apps
// with the same generic preview ("Halloween Party Invite - Pick My Costume" /
// emoji-crew image) no matter the party. Per-party og:title/og:description/
// og:image are injected here, server-side, on the fetch path: when the
// request carries a valid theme token ?t=<theme>, the static HTML's
// og/twitter meta values are replaced with per-party ones before serving.
// No token (or an invalid one): the static asset is served untouched,
// byte-identical.
//
// Mirrors the /c/[slug].js pattern: token -> embedded data table -> esc() ->
// og meta values -> Response. The difference is injection into the existing
// static HTML (string replace of the meta tags, matched by tag identity so a
// party.html copy change degrades to the generic preview, never to broken
// HTML) instead of building the page from scratch.
//
// Privacy: the party name/date live in the share URL itself (that is the
// invite mechanism), so reflecting them in the preview adds no new channel.
// og:url stays the canonical /party (no query, no PII): messengers cache the
// preview against the fetched URL, so per-party unfurls still work. Only
// t/n/d are ever read; every other query param is ignored. Host-typed
// name/date are esc()d for the meta content-attribute context and truncated
// to party.html's own caps (60/40).
//
// PARTY_OG is emitted by hour-session/build_party.py from THEMES (single
// source of truth): name + tagline per theme; img is the theme's first
// costume spot as images/og/<slug>.jpg (existence asserted at generation
// time). A theme this table does not know falls through to the generic
// asset.

// (table emitted by build_party.py from THEMES -- see header)
var PARTY_OG = {
  "heroes-night":   { "name": "Movie Heroes Night", "tagline": "Five big-screen heroes. No sewing, no stress.",    "img": "tin-hero" },
  "space-crew":     { "name": "Space Crew",         "tagline": "Three explorers and one very friendly alien.",     "img": "astronaut" },
  "witchy-night":   { "name": "Witchy Night",       "tagline": "Witches, a ghost, and zero scary-movie tears.",    "img": "emerald-witch" },
  "safari-squad":   { "name": "Safari Squad",       "tagline": "Khaki, binoculars, and one extinct party animal.", "img": "safari-zoo-crew" },
  "breakfast-club": { "name": "Breakfast Club",     "tagline": "The tastiest group costume on the block.",         "img": "cereal-crew" },
  "ocean-crew":     { "name": "Ocean Crew",         "tagline": "Mermaids and one little shark.",                   "img": "mermaid-crew" },
  "royal-court":    { "name": "Royal Court",        "tagline": "Crowns for everyone, pins for no one.",            "img": "prince-princess" },
  "monster-mash":   { "name": "Monster Mash",       "tagline": "Classic monsters, zero nightmares.",               "img": "vampire" }
};

// Fallback image: the same generic og:image party.html ships with.
var DEFAULT_OG_IMAGE = "https://pickmycostume.com/images/og/emoji-crew.jpg";

// Same esc() as /c/[slug].js: these values land inside meta content="".
function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
                  .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// Replace the value of one meta tag, matched by tag identity (property/name
// + content attribute). If party.html's copy changes, the match still holds;
// if the tag ever disappears, this is a silent no-op (generic stays).
function setMeta(html, attr, value) {
  var re = new RegExp("<meta " + attr + ' content="[^"]*">');
  return html.replace(re, "<meta " + attr + ' content="' + value + '">');
}

export async function onRequest(context) {
  var url;
  try {
    url = new URL(context.request.url);
  } catch (e) {
    return context.env.ASSETS.fetch(context.request);
  }

  var t = url.searchParams.get("t") || "";
  var th = (/^[a-z0-9-]+$/.test(t) && PARTY_OG[t]) ? PARTY_OG[t] : null;
  if (!th || context.request.method !== "GET") {
    // No (or invalid) theme token, or a non-GET fetch: serve the static
    // asset exactly as-is. Crawlers unfurl with GET, so this path is the
    // only one that ever needs injection.
    return context.env.ASSETS.fetch(context.request);
  }

  var resp = await context.env.ASSETS.fetch(context.request);
  var ctype = resp.headers.get("Content-Type") || "";
  if (!resp.ok || ctype.indexOf("text/html") === -1) return resp;
  var html = await resp.text();
  if (!html) return resp;

  // Host-typed fields, same caps as party.html's own parser (60/40).
  var name = (url.searchParams.get("n") || "").slice(0, 60);
  var date = (url.searchParams.get("d") || "").slice(0, 40);

  var who = name ? name : "Halloween party";
  var title = esc(who + " \u00b7 " + th.name);
  var desc = esc((date ? date + ". " : "") + th.tagline +
                 " Find your costume in 2 minutes.");
  var img = th.img
    ? "https://pickmycostume.com/images/og/" + th.img + ".jpg"
    : DEFAULT_OG_IMAGE;

  html = setMeta(html, 'property="og:title"', title);
  html = setMeta(html, 'name="twitter:title"', title);
  html = setMeta(html, 'property="og:description"', desc);
  html = setMeta(html, 'name="twitter:description"', desc);
  html = setMeta(html, 'property="og:image"', img);
  html = setMeta(html, 'name="twitter:image"', img);
  // og:url intentionally untouched: canonical /party, no query, no PII.

  return new Response(html, {
    headers: {
      "Content-Type": "text/html;charset=utf-8",
      "Cache-Control": "public, max-age=3600"
    }
  });
}
