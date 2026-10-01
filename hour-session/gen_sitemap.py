#!/usr/bin/env python3
"""Regenerate sitemap.xml with <lastmod> = real content-change dates.

Reads the existing sitemap.xml for the page list (loc, changefreq, priority
are preserved as curated), takes the /c/<slug> list from the live idea bank
in app.js (same source as gen_share_function.py), and writes sitemap.xml
with lastmod set to each page's REAL last content change — not the regen
date. Stamping "today" on every regen burns crawler trust in lastmod, so a
page whose content has not changed keeps its previous lastmod across regens.

Date sources:
- Static pages (/, /<slug>, /map/): the local file's mtime (UTC date).
  The file on disk IS the served content, so its mtime is the change date.
  /          -> index.html
  /<slug>    -> <slug>.html
  /map/      -> map.html
- /map/<region>: functions/map/[[path]].js mtime. The generator
  (hour-session/build_map_function.py) embeds map.html + region data at
  build time, so the generated function IS the served page.
- /mcp: hour-session/connector-setup-docs.html mtime. /mcp is a
  Cloudflare-side route that serves the connector docs.
- /c/<slug>: per-idea content hash of the IDEAS entry + page template in
  functions/c/[slug].js, tracked in hidden_files/sitemap-lastmod-state.json.
  Unchanged content keeps its previous lastmod; changed or new content gets
  today's date. First-run seed: functions/c/[slug].js mtime (the last regen
  of the served pages).

Fallback: if a URL has no mappable local source, reuse its existing
lastmod from the current sitemap.xml; if it has none either, use today.
"""
import datetime
import hashlib
import json
import os
import re
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sitemap.xml")
INDEX = os.path.join(ROOT, "app.js")  # bank moved from index.html 2026-09-30
STATE = os.path.join(ROOT, "hidden_files", "sitemap-lastmod-state.json")
SHARE_FN = os.path.join(ROOT, "functions", "c", "[slug].js")
MAP_FN = os.path.join(ROOT, "functions", "map", "[[path]].js")
MCP_DOC = os.path.join(ROOT, "hour-session", "connector-setup-docs.html")
SITE = "https://pickmycostume.com"

# Utility pages: served with X-Robots-Tag: noindex (see _headers, 2026-10-01
# hygiene pass). A noindexed URL must not sit in the sitemap sending the
# opposite signal, so the generator drops them even if present in the input.
NOINDEX_PATHS = {"/links", "/mcp", "/flyer", "/privacy", "/school-check",
                 "/pantry", "/play"}

# Retired pages that now 301 elsewhere (see _redirects, 2026-10-01). A
# redirected URL must not sit in the sitemap, so the generator drops them
# even if present in the input.
RETIRED_REDIRECTS = {"/halloween-costume-ideas-quiz"}

NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
ET.register_namespace("", NS)


def utc_date(path):
    """Content-change date of a local file: mtime as a UTC date."""
    return datetime.datetime.fromtimestamp(
        os.path.getmtime(path), tz=datetime.timezone.utc).date().isoformat()


def source_files(loc):
    """Local file(s) whose bytes ARE the served page, or None for /c/."""
    path = loc[len(SITE):] if loc.startswith(SITE) else loc
    if path in ("", "/"):
        return ["index.html"]
    if path == "/mcp":
        return ["hour-session/connector-setup-docs.html"]
    if path.startswith("/map/"):
        rest = path[len("/map/"):]
        if rest in ("", "/"):
            return ["map.html"]
        return ["functions/map/[[path]].js"]
    if "/c/" in path:
        return None  # per-idea hashing, handled separately
    cand = path.lstrip("/") + ".html"
    if os.path.exists(os.path.join(ROOT, cand)):
        return [cand]
    return []  # unknown: caller falls back to previous lastmod


def share_fn_parts():
    """Split functions/c/[slug].js into (ideas_source, template_hash)."""
    src = open(SHARE_FN, encoding="utf-8").read()
    m = re.search(r"var IDEAS = ", src)
    assert m, "IDEAS var not found in %s" % SHARE_FN
    start = src.index("{", m.start())
    depth, instr, esc, end = 0, False, False, None
    for j in range(start, len(src)):
        ch = src[j]
        if instr:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                instr = False
        else:
            if ch == '"':
                instr = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = j
                    break
    assert end is not None, "unbalanced IDEAS object"
    ideas_src = src[start:end + 1]
    template = src[:m.start()] + "/*IDEAS*/" + src[end + 1:]
    return ideas_src, hashlib.sha1(template.encode("utf-8")).hexdigest()


IDEAS_SRC, TEMPLATE_HASH = share_fn_parts()
ENTRY_RE_CACHE = {}


def idea_hash(slug):
    """Content hash for one /c/<slug> page: its IDEAS entry + template."""
    if slug not in ENTRY_RE_CACHE:
        ENTRY_RE_CACHE[slug] = re.compile(
            r'"' + re.escape(slug) +
            r'": \{"t": "(?:[^"\\]|\\.)*", "b": "(?:[^"\\]|\\.)*"\}')
    m = ENTRY_RE_CACHE[slug].search(IDEAS_SRC)
    assert m, "no IDEAS entry for slug %s" % slug
    return hashlib.sha1(
        (TEMPLATE_HASH + "|" + m.group(0)).encode("utf-8")).hexdigest()


tree = ET.parse(SRC)
old_lastmod = {}
entries = []  # (loc, changefreq, priority), non-/c/ pages only
for url in tree.getroot().findall("{%s}url" % NS):
    loc = url.find("{%s}loc" % NS).text.strip()
    cf = url.find("{%s}changefreq" % NS)
    pr = url.find("{%s}priority" % NS)
    lm = url.find("{%s}lastmod" % NS)
    if lm is not None and lm.text:
        old_lastmod[loc] = lm.text.strip()
    if "/c/" in loc:
        continue
    path = loc[len(SITE):] if loc.startswith(SITE) else loc
    if path in NOINDEX_PATHS:
        continue  # noindexed utility page: keep out of the sitemap
    if path in RETIRED_REDIRECTS:
        continue  # retired page now 301s elsewhere: keep out of the sitemap
    entries.append((loc,
                    cf.text.strip() if cf is not None else "monthly",
                    pr.text.strip() if pr is not None else "0.5"))

bank_src = open(INDEX, encoding="utf-8").read()
# Same strict parse as gen_share_function.py: quiz question ids (q1, q2,
# qinterest, ...) have no blurb and must not become /c/ sitemap entries.
slugs = [s for s, _t, _b in re.findall(
    r'\{id:"([^"]+)", title:"([^"]+)", blurb:"([^"]+)"', bank_src)]
assert slugs, "no idea slugs parsed from index.html"
assert len(slugs) == len(set(slugs)), "duplicate idea slugs"

today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()

# Per-/c/-URL change tracking: unchanged content keeps its previous lastmod.
try:
    with open(STATE, encoding="utf-8") as f:
        state = json.load(f)
except (OSError, ValueError):
    state = {}
seed_date = utc_date(SHARE_FN)
c_lastmod = {}
for slug in slugs:
    loc = SITE + "/c/" + slug
    h = idea_hash(slug)
    prev = state.get(loc)
    if prev and prev.get("hash") == h:
        lastmod = prev["lastmod"]  # content unchanged: keep real date
    elif prev:
        lastmod = today            # content changed: it changed now
    else:
        lastmod = seed_date        # first run: last regen of served pages
    c_lastmod[loc] = lastmod
    state[loc] = {"lastmod": lastmod, "hash": h}

urlset = ET.Element("{%s}urlset" % NS)


def add_url(loc, lastmod, changefreq, priority):
    u = ET.SubElement(urlset, "{%s}url" % NS)
    ET.SubElement(u, "{%s}loc" % NS).text = loc
    ET.SubElement(u, "{%s}lastmod" % NS).text = lastmod
    ET.SubElement(u, "{%s}changefreq" % NS).text = changefreq
    ET.SubElement(u, "{%s}priority" % NS).text = priority


unmapped = []
for loc, cf, pr in entries:
    files = source_files(loc)
    if files:
        lastmod = max(utc_date(os.path.join(ROOT, f)) for f in files)
    else:
        unmapped.append(loc)
        lastmod = old_lastmod.get(loc, today)
    add_url(loc, lastmod, cf, pr)
for slug in sorted(slugs):
    add_url(SITE + "/c/" + slug, c_lastmod[SITE + "/c/" + slug],
            "monthly", "0.8")

xml = ET.tostring(urlset, encoding="unicode")
with open(SRC, "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + xml + "\n")
with open(STATE, "w", encoding="utf-8") as f:
    json.dump(state, f, indent=1, sort_keys=True)
    f.write("\n")

# Verify the write parses and covers the bank.
t2 = ET.parse(SRC)
locs = [u.find("{%s}loc" % NS).text for u in t2.getroot().findall("{%s}url" % NS)]
missing = [s for s in slugs if SITE + "/c/" + s not in locs]
assert not missing, "sitemap missing slugs: %s" % missing
from collections import Counter
dates = Counter(u.find("{%s}lastmod" % NS).text
                for u in t2.getroot().findall("{%s}url" % NS))
print("wrote %s: %d urls (%d guides)" % (SRC, len(locs), len(slugs)))
print("lastmod distribution: %s" % dict(sorted(dates.items())))
if unmapped:
    print("WARNING: no local source mapped, kept previous lastmod: %s"
          % unmapped)
print("state: %s (%d tracked /c/ urls)" % (STATE, len(state)))
