#!/usr/bin/env python3
"""Regenerate functions/c/[slug].js from the IDEAS bank in index.html.

The Pages Function serves /c/<slug> share pages: each unfurls the shared
costume's own illustration via og:/twitter: meta tags, then redirects
humans to /?idea=<slug>. Re-run after adding, removing, or renaming ideas.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
ideas = re.findall(r'\{id:"([^"]+)", title:"([^"]+)", blurb:"([^"]+)"', src)
assert ideas, "no ideas parsed from index.html"
data = {slug: {"t": title, "b": blurb} for slug, title, blurb in ideas}
for slug in data:
    assert os.path.exists(os.path.join(ROOT, "images", slug + ".png")), \
        "missing illustration: " + slug

# Old slugs renamed in the Sep 2026 IP sweep. Every alias must resolve to a
# slug present in the current bank; the generator asserts this below.
ALIASES = {
    "bluey-family": "blue-dog-family",
    "incredibles-family": "superhero-family",
    "stitch-ohana": "blue-alien-ohana",
    "wednesday-enid": "gloom-bloom",
    "iron-man": "tin-hero",
    "elphaba-glinda": "good-witch-bad-witch",
    "minecraft-crew": "block-game-crew",
    "spider-verse": "web-slinger-crew",
    "spider-man-mj": "web-hero-duo",
    "peppa-pig": "little-pig-family",
    "jurassic-rangers": "dino-rangers",
    "creeper": "block-monster",
    "among-us": "space-crewmate",
    "little-mermaid-crew": "mermaid-crew",
    "bumblebee": "bumble-bee",
    "jim-pam": "office-couple",
    "bob-linda": "burger-joint-couple",
    "be-our-guest": "enchanted-castle-crew",
    "disney-princesses": "fairy-tale-princesses",
}
for old, new in ALIASES.items():
    assert new in data, "alias target missing from bank: " + new
    assert old not in data, "alias source still in bank: " + old

FN = '''// Per-idea share pages: /c/<slug> unfurls the shared costume's own
// illustration for messengers, then redirects humans to /?idea=<slug>.
// Regenerate with gen_share_function.py when the idea bank changes.
var IDEAS = %s;

// Old slugs renamed in the Sep 2026 IP sweep: keep every share link ever
// minted working by resolving them to the current canonical slug.
var ALIASES = %s;

function esc(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;")
          .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

export function onRequest(context) {
  var slug = context.params.slug || "";
  if (ALIASES[slug]) slug = ALIASES[slug]; /* renamed slug -> canonical */
  var idea = IDEAS[slug];
  if (!idea) return new Response("Not found", { status: 404 });
  var title = esc(idea.t), blurb = esc(idea.b);
  var img = "https://pickmycostume.com/images/og/" + slug + ".jpg";
  /* Preserve any extra query params (e.g. tracking tags) across the redirect. */
  var _qp = new URLSearchParams(new URL(context.request.url).search);
  _qp.set("idea", slug);
  var target = "/?" + _qp.toString();
  /* Shared metadata head: identical for every visitor. iMessage's
     sender-side preview fetch uses a spoofed composite UA (Safari plus
     Facebook/Twitter crawler strings); per Apple TN3156 it runs no JS and
     follows no meta refresh, so it gets clean metadata-only HTML with no
     redirect machinery. The tags are identical for everyone: not cloaking. */
  var head = "<!DOCTYPE html>" +
    "<html lang=\\"en\\"><head><meta charset=\\"utf-8\\">" +
    "<title>" + title + " - Pick My Costume</title>" +
    "<meta property=\\"og:type\\" content=\\"website\\">" +
    "<meta property=\\"og:url\\" content=\\"https://pickmycostume.com/c/" + slug + "\\">" +
    "<meta property=\\"og:title\\" content=\\"" + title + " - Pick My Costume\\">" +
    "<meta property=\\"og:description\\" content=\\"" + blurb + "\\">" +
    "<meta property=\\"og:image\\" content=\\"" + img + "\\">" +
    "<meta property=\\"og:image:secure_url\\" content=\\"" + img + "\\">" +
    "<meta property=\\"og:image:type\\" content=\\"image/jpeg\\">" +
    "<meta property=\\"og:image:width\\" content=\\"1200\\">" +
    "<meta property=\\"og:image:height\\" content=\\"630\\">" +
    "<meta property=\\"og:image:alt\\" content=\\"" + title + " costume idea\\">" +
    "<meta name=\\"twitter:card\\" content=\\"summary_large_image\\">" +
    "<meta name=\\"twitter:title\\" content=\\"" + title + " - Pick My Costume\\">" +
    "<meta name=\\"twitter:description\\" content=\\"" + blurb + "\\">" +
    "<meta name=\\"twitter:image\\" content=\\"" + img + "\\">" +
    "<meta name=\\"viewport\\" content=\\"width=device-width, initial-scale=1\\">";
  var _ua = (context.request.headers.get("user-agent") || "").toLowerCase();
  var _imsgFetch = _ua.indexOf("facebookexternalhit") !== -1 &&
                   _ua.indexOf("facebot") !== -1 &&
                   _ua.indexOf("twitterbot") !== -1;
  var html;
  if (_imsgFetch) {
    html = head +
      "</head><body><h1>" + title + "</h1><p>" + blurb + "</p>" +
      "<p><a href=\\"https://pickmycostume.com/\\">Pick My Costume</a></p></body></html>";
  } else {
    html = head +
      "<noscript><meta http-equiv=\\"refresh\\" content=\\"0;url=" + target + "\\"></noscript>" +
      "<script>location.replace(\\"" + target + "\\");</script>" +
      "</head><body><p>Taking you to Pick My Costume&hellip; " +
      "<a href=\\"" + target + "\\">" + title + "</a></p></body></html>";
  }
  return new Response(html, {
    headers: {
      "Content-Type": "text/html;charset=utf-8",
      "Cache-Control": "public, max-age=3600"
    }
  });
}
''' % (json.dumps(data), json.dumps(ALIASES))

out = os.path.join(ROOT, "functions", "c", "[slug].js")
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w", encoding="utf-8").write(FN)
print("wrote %s (%d ideas)" % (out, len(data)))
