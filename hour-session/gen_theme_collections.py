#!/usr/bin/env python3
"""Generate 4 bank-backed theme collection pages + cross-link strip + ItemList JSON-LD.

2026-10-06 fix batch (Billy approved all).
New root-level pages (template inherits collections/*.html structure/style):
  food-costumes.html      <- bank tag food    (31 ideas, bank-verified)
  animal-costumes.html    <- bank tag animals (20 ideas, bank-verified)
  dinosaur-costumes.html  <- bank tag dinos   (13 ideas, bank-verified; NOT 14 --
                             the 14th raw "dinos:" hit is the qinterest quiz record)
  superhero-costumes.html <- bank tag heroes  (14 ideas, bank-verified)

Also, on ALL collection pages (4 new + 5 existing in collections/):
  - "Explore more collections" cross-link strip (excludes self)
  - ItemList JSON-LD (last-call.html style) for carousel rich-result eligibility
  - legacy footer "Browse all 138" -> "Browse all 169" staleness fix

Sitemap: appends the 4 new URLs (monthly/0.7, like other collection entries).
Idempotent: re-running regenerates identical output; sitemap insert skips present URLs.

Reads app.js (bank) only; writes new HTML files, patches collections/*.html, sitemap.xml.
"""
import os
import re
import html
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = "2026-10-06"

DASHES = re.compile(r"[\u2013\u2014]")

NEW_COLLECTIONS = [
    {
        "key": "food-costumes",
        "tag": "food",
        "expected": 31,
        "h1": "Food Halloween costumes",
        "title": "Food Halloween Costumes 2026 - Pick My Costume",
        "desc": "31 food Halloween costumes you can build at home, from walking tacos to ramen bowls. Every one has a free step-by-step build guide.",
        "lede": "Hungry for a costume idea? These 31 food costumes turn snacks, meals, and grocery runs into Halloween gold, and every one has a free step-by-step build guide. Pick your craving, or take the 2-minute quiz and get your match.",
        "jsonld_name": "31 food Halloween costumes with free DIY build guides",
    },
    {
        "key": "animal-costumes",
        "tag": "animals",
        "expected": 20,
        "h1": "Animal Halloween costumes",
        "title": "Animal Halloween Costumes 2026 - Pick My Costume",
        "desc": "20 animal Halloween costumes for the whole kingdom, from bumblebees to sharks. Every one has a free step-by-step build guide.",
        "lede": "Go wild this Halloween. These 20 animal costumes cover the whole kingdom, from bumblebees to sharks, and each one has a free step-by-step build guide. Pick your creature, or take the 2-minute quiz and get your match.",
        "jsonld_name": "20 animal Halloween costumes with free DIY build guides",
    },
    {
        "key": "dinosaur-costumes",
        "tag": "dinos",
        "expected": 13,
        "h1": "Dinosaur Halloween costumes",
        "title": "Dinosaur Halloween Costumes 2026 - Pick My Costume",
        "desc": "13 dinosaur Halloween costumes, from baby dinos to a full fossil-hunter crew. Every one has a free step-by-step build guide.",
        "lede": "Rawr means I love you in dinosaur. These 13 dino costumes run from babies to full herds, and each one has a free step-by-step build guide. Pick your species, or take the 2-minute quiz and get your match.",
        "jsonld_name": "13 dinosaur Halloween costumes with free DIY build guides",
    },
    {
        "key": "superhero-costumes",
        "tag": "heroes",
        "expected": 14,
        "h1": "Superhero Halloween costumes",
        "title": "Superhero Halloween Costumes 2026 - Pick My Costume",
        "desc": "14 DIY superhero Halloween costumes, from web-slingers to caped duos. Every one has a free step-by-step build guide.",
        "lede": "Every hero needs an origin story. These 14 superhero costumes are all DIY builds, and each one has a free step-by-step guide. Pick your powers, or take the 2-minute quiz and get your match.",
        "jsonld_name": "14 superhero Halloween costumes with free DIY build guides",
    },
]

# Cross-link strip family: (label, canonical path). Self is excluded per page.
STRIP_FAMILY = [
    ("Food costumes", "/food-costumes"),
    ("Animal costumes", "/animal-costumes"),
    ("Dinosaur costumes", "/dinosaur-costumes"),
    ("Superhero costumes", "/superhero-costumes"),
    ("Last-minute costumes", "/last-minute-costumes"),
    ("Toddler costumes", "/toddler-costumes"),
    ("Family costumes", "/family-costumes"),
    ("Easy DIY kids costumes", "/easy-diy-halloween-costumes-for-kids"),
    ("Closet costumes", "/costumes-from-your-closet"),
]

# Legacy collections/*.html -> canonical self path (for strip self-exclusion).
LEGACY_SELF = {
    "collections/last-minute-costumes.html": "/last-minute-costumes",
    "collections/toddler-costumes.html": "/toddler-costumes",
    "collections/family-group-costumes.html": "/family-costumes",
    "collections/easy-diy-kids-costumes.html": "/easy-diy-halloween-costumes-for-kids",
    "collections/cheap-homemade-costumes.html": "/costumes-from-your-closet",
}


def parse_bank(src):
    order, ideas = [], {}
    for m in re.finditer(r'\{id:"([a-z0-9-]+)", title:"([^"]+)", blurb:"([^"]+)"', src):
        slug = m.group(1)
        if slug.startswith("q"):
            continue  # quiz question records, not bank ideas
        order.append(slug)
        ideas[slug] = {"title": m.group(2), "blurb": m.group(3)}
    assert len(ideas) == 169, "expected 169 bank ideas, got %d" % len(ideas)
    members = {}
    for m in re.finditer(r"(food|animals|dinos|heroes):\d", src):
        tag = m.group(1)
        start = src.rfind('{id:"', 0, m.start())
        sid = re.match(r'\{id:"([a-z0-9-]+)"', src[start:start + 60]).group(1)
        if sid.startswith("q"):
            continue
        assert sid in ideas, "tag on unknown idea %s" % sid
        members.setdefault(tag, []).append(sid)
    # bank order, deduplicated
    for tag in members:
        seen = set()
        members[tag] = [s for s in order if s in set(members[tag]) and not (s in seen or seen.add(s))]
    ins = {}
    for m in re.finditer(
            r'"([a-z0-9-]+)":\{"m":\[.*?"time":"([^"]+)","cost":"[^"]+","effort":"([^"]+)"',
            src):
        ins[m.group(1)] = {"time": m.group(2), "effort": m.group(3)}
    return order, ideas, members, ins


def esc(s):
    return html.escape(s, quote=True)


def jsonld_block(name, items):
    """ItemList JSON-LD in the last-call.html pretty-printed style."""
    lines = ["{", ' "@context": "https://schema.org",', ' "@type": "ItemList",',
             ' "name": %s,' % json.dumps(name), ' "itemListElement": [']
    for i, (slug, title) in enumerate(items):
        lines.append("  {")
        lines.append('   "@type": "ListItem",')
        lines.append('   "position": %d,' % (i + 1))
        lines.append('   "name": %s,' % json.dumps(title))
        lines.append('   "url": "https://pickmycostume.com/c/%s"' % slug)
        lines.append("  }" + ("," if i < len(items) - 1 else ""))
    lines += [" ]", "}"]
    return '<script type="application/ld+json">\n' + "\n".join(lines) + "\n</script>"


STRIP_CSS = """.collections-strip{margin-top:28px;padding:18px;border:1px solid #eee;border-radius:12px;background:#fafafa;text-align:center;}
.collections-strip .cs-h{font-weight:700;margin:0 0 8px;font-size:15px;color:#222;}
.collections-strip .cs-links{margin:0;font-size:14px;line-height:2.1;}
.collections-strip a{color:#0a6cff;text-decoration:none;margin:0 6px;white-space:nowrap;}"""


def strip_html(self_path):
    links = [" ".join(
        '<a href="%s">%s</a>' % (p, l) for l, p in STRIP_FAMILY if p != self_path)]
    return ('<div class="collections-strip">\n'
            '<p class="cs-h">Explore more collections</p>\n'
            '<p class="cs-links">%s</p>\n'
            '</div>') % " ".join(links)


def page_html(col, items, ideas, ins):
    """Full new collection page inheriting the collections/*.html template."""
    first_slug = items[0][0]
    cards = []
    for slug, title in items:
        tri = "%s, %s" % (ins[slug]["time"], ins[slug]["effort"])
        rec = ideas[slug]
        cards.append(
            '<li class="card">'
            '<a href="/c/%s"><img src="/photos/%s.webp" alt="%s costume" loading="lazy">'
            '<span class="t">%s</span></a>'
            '<span class="tri">%s</span>'
            '<p class="bl">%s</p>'
            '<a class="guide" href="/c/%s">Free build guide</a>'
            '</li>' % (slug, slug, esc(rec["title"]), esc(rec["title"]),
                       esc(tri), esc(rec["blurb"]), slug))
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="https://pickmycostume.com/%s">
<meta property="og:type" content="website">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:url" content="https://pickmycostume.com/%s">
<meta property="og:image" content="https://pickmycostume.com/images/og/%s.jpg">
%s
<style>
body{font-family:-apple-system,system-ui,'Segoe UI',Roboto,sans-serif;margin:0;color:#222;background:#fff;}
.wrap{max-width:720px;margin:0 auto;padding:32px 20px 64px;}
h1{font-size:28px;margin:0 0 8px;}
.lede{font-size:16px;color:#555;margin:0 0 20px;}
ul{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:16px;}
.card{border:1px solid #eee;border-radius:12px;overflow:hidden;padding:0 0 12px;}
.card img{width:100%%;aspect-ratio:4/5;object-fit:cover;display:block;}
.card .t{font-weight:700;display:block;padding:10px 12px 2px;font-size:16px;color:#222;}
.card a{text-decoration:none;}
.card .tri{display:block;padding:0 12px;font-size:13px;color:#777;}
.card .bl{font-size:14px;color:#555;margin:8px 12px;}
.card .guide{display:inline-block;margin:0 12px;font-size:14px;font-weight:700;color:#0a6cff;}
.quizbox{margin:32px 0 0;padding:20px;border-radius:12px;background:#f7f3ff;text-align:center;}
.quizbox p{margin:0 0 12px;font-size:16px;}
.quizbox a{display:inline-block;background:#7c3aed;color:#fff;font-weight:700;padding:12px 24px;border-radius:10px;text-decoration:none;}
%s
.more{margin-top:24px;text-align:center;}
.more a{color:#0a6cff;}
</style>
</head>
<body>
<div class="wrap">
<h1>%s</h1>
<p class="lede">%s</p>
<ul>
%s
</ul>
<div class="quizbox">
<p>Not seeing the one? Take the 2-minute quiz and get your match.</p>
<a href="/?src=collection-%s">Take the quiz</a>
</div>
%s
<p class="more"><a href="/costumes">Browse all 169 costume guides</a></p>
</div>
</body>
</html>
""" % (esc(col["title"]), esc(col["desc"]), col["key"],
       esc(col["title"]), esc(col["desc"]), col["key"], first_slug,
       jsonld_block(col["jsonld_name"], items),
       STRIP_CSS,
       esc(col["h1"]), esc(col["lede"]), "\n".join(cards), col["key"],
       strip_html("/" + col["key"]))


def patch_legacy(path, self_path, ideas):
    """Add strip CSS, strip HTML, ItemList JSON-LD; fix 138->169 staleness."""
    with open(path, encoding="utf-8") as f:
        src = f.read()
    orig = src
    # 1. strip CSS before ".more{" rule
    assert ".more{margin-top:24px;text-align:center;}" in src, "CSS anchor moved in %s" % path
    src = src.replace(".more{margin-top:24px;text-align:center;}",
                      STRIP_CSS + "\n.more{margin-top:24px;text-align:center;}", 1)
    # 2. ItemList JSON-LD before </head>: items from the page's own /c/ links
    slugs = []
    for s in re.findall(r'href="/c/([a-z0-9-]+)"', src):
        if s not in slugs:
            slugs.append(s)
    assert len(slugs) == 6, "%s: expected 6 ideas, got %d" % (path, len(slugs))
    items = [(s, ideas[s]["title"]) for s in slugs]
    h1 = re.search(r"<h1>([^<]+)</h1>", src).group(1)
    jl = jsonld_block("%s: free DIY build guides" % h1, items)
    assert "</head>" in src
    src = src.replace("</head>", jl + "\n</head>", 1)
    # 3. strip HTML after the quizbox div, before the first <p class="more">
    assert '<p class="more">' in src, "more anchor missing in %s" % path
    src = src.replace('<p class="more">', strip_html(self_path) + '\n<p class="more">', 1)
    # 4. staleness fix
    src = src.replace("Browse all 138 costume guides", "Browse all 169 costume guides")
    assert src != orig, "no changes applied to %s" % path
    assert not DASHES.search(src), "em/en dash in patched %s" % path
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    print("patched %s (%d items)" % (path, len(slugs)))


def update_sitemap(keys):
    sm = os.path.join(ROOT, "sitemap.xml")
    xml = open(sm, encoding="utf-8").read()
    added = 0
    for key in keys:
        loc = "https://pickmycostume.com/" + key
        if loc + "</loc>" in xml:
            continue
        anchor = "<url><loc>https://pickmycostume.com/group-costumes</loc>"
        assert anchor in xml, "sitemap anchor moved; not editing blindly"
        entry = ("<url><loc>%s</loc><lastmod>%s</lastmod>"
                 "<changefreq>monthly</changefreq><priority>0.7</priority></url>\n"
                 % (loc, TODAY))
        xml = xml.replace(anchor, entry + anchor, 1)
        added += 1
    with open(sm, "w", encoding="utf-8") as f:
        f.write(xml)
    print("sitemap: +%d urls (%d total)" % (added, xml.count("<url>")))


def main():
    src = open(os.path.join(ROOT, "app.js"), encoding="utf-8").read()
    order, ideas, members, ins = parse_bank(src)

    for col in NEW_COLLECTIONS:
        for field in ("h1", "title", "desc", "lede", "jsonld_name"):
            assert not DASHES.search(col[field]), "em/en dash in %s %s" % (col["key"], field)

    # build + verify + write the 4 new pages
    for col in NEW_COLLECTIONS:
        slugs = members[col["tag"]]
        assert len(slugs) == col["expected"], \
            "%s: bank has %d <%s> ideas, expected %d" % (col["key"], len(slugs), col["tag"], col["expected"])
        items = [(s, ideas[s]["title"]) for s in slugs]
        for s, _ in items:
            assert s in ins, "missing INSTRUCTIONS for %s" % s
            assert os.path.exists(os.path.join(ROOT, "photos", s + ".webp")), \
                "missing photo: photos/%s.webp" % s
        assert os.path.exists(os.path.join(ROOT, "images", "og", slugs[0] + ".jpg")), \
            "missing og image for %s" % slugs[0]
        out = page_html(col, items, ideas, ins)
        assert not DASHES.search(out), "em/en dash in generated %s" % col["key"]
        assert out.count('class="card"') == col["expected"], "card count mismatch"
        with open(os.path.join(ROOT, col["key"] + ".html"), "w", encoding="utf-8") as f:
            f.write(out)
        print("%s: %d ideas bank-verified -> %s" % (col["key"], len(slugs), ", ".join(slugs[:3]) + ", ..."))

    # patch the 5 legacy collection pages
    for rel, self_path in LEGACY_SELF.items():
        patch_legacy(os.path.join(ROOT, rel), self_path, ideas)

    # sitemap
    update_sitemap([c["key"] for c in NEW_COLLECTIONS])


if __name__ == "__main__":
    main()
