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

FN = '''// Per-idea share pages: /c/<slug> unfurls the shared costume's own
// illustration for messengers, then redirects humans to /?idea=<slug>.
// Regenerate with gen_share_function.py when the idea bank changes.
var IDEAS = %s;

function esc(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;")
          .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

export function onRequest(context) {
  var slug = context.params.slug || "";
  var idea = IDEAS[slug];
  if (!idea) return new Response("Not found", { status: 404 });
  var title = esc(idea.t), blurb = esc(idea.b);
  var img = "https://pickmycostume.com/images/" + slug + ".png";
  var target = "/?idea=" + slug;
  var html = "<!DOCTYPE html>" +
    "<html lang=\\"en\\"><head><meta charset=\\"utf-8\\">" +
    "<title>" + title + " - Pick My Costume</title>" +
    "<meta property=\\"og:type\\" content=\\"website\\">" +
    "<meta property=\\"og:url\\" content=\\"https://pickmycostume.com/c/" + slug + "\\">" +
    "<meta property=\\"og:title\\" content=\\"" + title + " - Pick My Costume\\">" +
    "<meta property=\\"og:description\\" content=\\"" + blurb + "\\">" +
    "<meta property=\\"og:image\\" content=\\"" + img + "\\">" +
    "<meta property=\\"og:image:width\\" content=\\"1600\\">" +
    "<meta property=\\"og:image:height\\" content=\\"1600\\">" +
    "<meta name=\\"twitter:card\\" content=\\"summary_large_image\\">" +
    "<meta name=\\"twitter:title\\" content=\\"" + title + " - Pick My Costume\\">" +
    "<meta name=\\"twitter:description\\" content=\\"" + blurb + "\\">" +
    "<meta name=\\"twitter:image\\" content=\\"" + img + "\\">" +
    "<meta name=\\"viewport\\" content=\\"width=device-width, initial-scale=1\\">" +
    "<noscript><meta http-equiv=\\"refresh\\" content=\\"0;url=" + target + "\\"></noscript>" +
    "<script>location.replace(\\"" + target + "\\");</script>" +
    "</head><body><p>Taking you to Pick My Costume&hellip; " +
    "<a href=\\"" + target + "\\">" + title + "</a></p></body></html>";
  return new Response(html, {
    headers: {
      "Content-Type": "text/html;charset=utf-8",
      "Cache-Control": "public, max-age=3600"
    }
  });
}
''' % json.dumps(data)

out = os.path.join(ROOT, "functions", "c", "[slug].js")
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w", encoding="utf-8").write(FN)
print("wrote %s (%d ideas)" % (out, len(data)))
