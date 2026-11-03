#!/usr/bin/env python3
"""Regenerate sitemap.xml with <lastmod> = real content-change dates.

Reads the existing sitemap.xml for the page list (loc, changefreq, priority
are preserved as curated), takes the /c/<slug> list from the live idea bank
in app.js (same source as gen_share_function.py), and writes sitemap.xml
with lastmod set to each page's REAL last content change — not the regen
date. Stamping "today" on every regen burns crawler trust in lastmod, so a
page whose content has not changed keeps its previous lastmod across regens.

Date source (reconciled 2026-11-03, Addendum 1189 lane — see
sitemap-generator-reconcile-2026-11-03/REPORT.md): a checked-in content-hash
manifest, hidden_files/sitemap-lastmod-state.json, covering EVERY sitemap
URL. For each URL the generator hashes the bytes that ARE the served page:

- Static pages (/, /<slug>, /map/, /map/<region>, /mcp, hubs): sha1 over
  the source file(s) named by source_files() / HUBS below.
      /          -> index.html
      /<slug>    -> <slug>.html
      /map/      -> map.html
      /map/<region> -> functions/map/[[path]].js (the generator
        hour-session/build_map_function.py embeds map.html + region
        data at build time, so the generated function IS the served page)
      /mcp       -> hour-session/connector-setup-docs.html (a Cloudflare-
        side route serving the connector docs; currently NOINDEX-dropped)
- /c/<slug>: per-idea content hash of the IDEAS entry + page template in
  functions/c/[slug].js (idea_hash below; unchanged from the original
  generator).

If a URL's hash matches the manifest, its recorded lastmod is kept. If the
hash differs, the content changed since the manifest was written, so the
lastmod becomes today and the manifest is updated. A URL with no manifest
entry yet seeds from its existing lastmod in the current sitemap.xml (or
today if it has none). Local file mtimes are NEVER consulted: bulk file
operations (the Nov 2 fleet sweeps re-touched most files) made mtime a
false change signal — a Nov 3 scratch regen of the previous generator
changed 241 of 247 lastmod values on mtime/hash drift alone. The manifest
is rewritten deterministically (sorted keys, fixed indent), so a regen
over unchanged content rewrites it byte-identically.

URL order: the existing sitemap's order is preserved exactly (the previous
generator regrouped static pages before the /c/ block, silently moving 15
pages that live after it). Hubs or bank slugs missing from the input are
appended at the end (hubs first, then slugs sorted), as before.

/privacy: deliberately IN the sitemap since the Nov 2 Phase B ship, so it
is NOT in NOINDEX_PATHS below (the previous generator dropped it on every
regen: 248 -> 247 URLs). Note _headers still serves X-Robots-Tag: noindex
for /privacy — that conflict lives in _headers, not in this generator,
and is flagged in the reconciliation report.
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
# /privacy is deliberately NOT in this set: it was added to the sitemap by
# the Nov 2 Phase B ship and a regen must not silently remove it again
# (reconciled 2026-11-03; see docstring).
NOINDEX_PATHS = {"/links", "/mcp", "/flyer", "/school-check",
                 "/pantry", "/play"}

# Retired pages that now 301 elsewhere (see _redirects, 2026-10-01). A
# redirected URL must not sit in the sitemap, so the generator drops them
# even if present in the input.
RETIRED_REDIRECTS = {"/halloween-costume-ideas-quiz"}

# Audience hub pages under /c/ (2026-10-23 hub discoverability fix): these
# are separate Pages Functions (functions/c/<hub>.js), NOT bank ideas, so
# the bank-slug loop below never re-adds them and the entries loop drops
# every /c/ URL. They must be explicit entries or every regen deletes
# them from the sitemap. Their content hash is taken over the hub
# function file's bytes (the file on disk IS the served page).
HUBS = [("couples", "functions/c/couples.js"),
        ("family", "functions/c/family.js"),
        ("last-minute", "functions/c/last-minute.js")]
HUB_FILES = dict(HUBS)

NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
ET.register_namespace("", NS)


def source_files(loc):
    """Local file(s) whose bytes ARE the served page, or None for /c/."""
    path = loc[len(SITE):] if loc.startswith(SITE) else loc
    if path in ("", "/"):
        return ["index.html"]
    if path == "/collections/":
        return ["collections/index.html"]
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


def files_hash(files):
    """sha1 over the listed source files' bytes (names included)."""
    h = hashlib.sha1()
    for f in files:
        h.update(f.encode("utf-8"))
        h.update(b"\0")
        with open(os.path.join(ROOT, f), "rb") as fh:
            h.update(fh.read())
        h.update(b"\0")
    return h.hexdigest()


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


def page_hash(loc):
    """Durable content hash for any sitemap URL (None if unmapped)."""
    path = loc[len(SITE):] if loc.startswith(SITE) else loc
    if path.startswith("/c/"):
        slug = path[len("/c/"):]
        if slug in HUB_FILES:
            return files_hash([HUB_FILES[slug]])
        return idea_hash(slug)
    files = source_files(loc)
    if not files:
        return None  # unmapped: keep previous lastmod, hash stays null
    return files_hash(files)


tree = ET.parse(SRC)
old_lastmod = {}
ordered = []  # (loc, changefreq, priority) for EVERY input URL, in order
for url in tree.getroot().findall("{%s}url" % NS):
    loc = url.find("{%s}loc" % NS).text.strip()
    cf = url.find("{%s}changefreq" % NS)
    pr = url.find("{%s}priority" % NS)
    lm = url.find("{%s}lastmod" % NS)
    if lm is not None and lm.text:
        old_lastmod[loc] = lm.text.strip()
    ordered.append((loc,
                    cf.text.strip() if cf is not None else "monthly",
                    pr.text.strip() if pr is not None else "0.5"))

bank_src = open(INDEX, encoding="utf-8").read()
# Same strict parse as gen_share_function.py: quiz question ids (q1, q2,
# qinterest, ...) have no blurb and must not become /c/ sitemap entries.
slugs = [s for s, _t, _b in re.findall(
    r'\{id:"([^"]+)", title:"([^"]+)", blurb:"([^"]+)"', bank_src)]
assert slugs, "no idea slugs parsed from index.html"
assert len(slugs) == len(set(slugs)), "duplicate idea slugs"
slug_set = set(slugs)

today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()

# Content-hash manifest: unchanged content keeps its recorded lastmod.
try:
    with open(STATE, encoding="utf-8") as f:
        state = json.load(f)
except (OSError, ValueError):
    state = {}


def resolve_lastmod(loc, h):
    """Keep the manifest date if content is unchanged; today if it
    changed; the input sitemap's date (or today) for a first sighting."""
    prev = state.get(loc)
    if prev is not None:
        if prev.get("hash") == h:
            return prev["lastmod"]
        if prev.get("hash") is None and h is None:
            return prev["lastmod"]
        return today  # content changed since the manifest was written
    return old_lastmod.get(loc, today)


urlset = ET.Element("{%s}urlset" % NS)


def add_url(loc, lastmod, changefreq, priority):
    u = ET.SubElement(urlset, "{%s}url" % NS)
    ET.SubElement(u, "{%s}loc" % NS).text = loc
    ET.SubElement(u, "{%s}lastmod" % NS).text = lastmod
    ET.SubElement(u, "{%s}changefreq" % NS).text = changefreq
    ET.SubElement(u, "{%s}priority" % NS).text = priority


emitted = set()
new_state = {}
unmapped = []


def emit(loc, cf, pr):
    h = page_hash(loc)
    if h is None:
        unmapped.append(loc)
    lastmod = resolve_lastmod(loc, h)
    add_url(loc, lastmod, cf, pr)
    emitted.add(loc)
    new_state[loc] = {"lastmod": lastmod, "hash": h}


# Single pass over the input sitemap, preserving its exact order.
for loc, cf, pr in ordered:
    path = loc[len(SITE):] if loc.startswith(SITE) else loc
    if path in NOINDEX_PATHS:
        continue  # noindexed utility page: keep out of the sitemap
    if path in RETIRED_REDIRECTS:
        continue  # retired page now 301s elsewhere: keep out of the sitemap
    if path.startswith("/c/"):
        slug = path[len("/c/"):]
        if slug not in HUB_FILES and slug not in slug_set:
            continue  # /c/ page gone from the bank and not a hub: drop it
    emit(loc, cf, pr)
# Append anything the bank/hub list has that the input sitemap lacked.
for hub, _hub_file in HUBS:
    loc = SITE + "/c/" + hub
    if loc not in emitted:
        emit(loc, "monthly", "0.8")
for slug in sorted(slugs):
    loc = SITE + "/c/" + slug
    if loc not in emitted:
        emit(loc, "monthly", "0.8")

xml = ET.tostring(urlset, encoding="unicode")
with open(SRC, "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + xml + "\n")
with open(STATE, "w", encoding="utf-8") as f:
    json.dump(new_state, f, indent=1, sort_keys=True)
    f.write("\n")

# Verify the write parses and covers the bank.
t2 = ET.parse(SRC)
locs = [u.find("{%s}loc" % NS).text for u in t2.getroot().findall("{%s}url" % NS)]
missing = [s for s in slugs if SITE + "/c/" + s not in locs]
assert not missing, "sitemap missing slugs: %s" % missing
missing_hubs = [h for h, _f in HUBS if SITE + "/c/" + h not in locs]
assert not missing_hubs, "sitemap missing hub pages: %s" % missing_hubs
from collections import Counter
dates = Counter(u.find("{%s}lastmod" % NS).text
                for u in t2.getroot().findall("{%s}url" % NS))
print("wrote %s: %d urls (%d guides)" % (SRC, len(locs), len(slugs)))
print("lastmod distribution: %s" % dict(sorted(dates.items())))
if unmapped:
    print("WARNING: no local source mapped, kept previous lastmod: %s"
          % unmapped)
print("state: %s (%d tracked urls)" % (STATE, len(new_state)))
