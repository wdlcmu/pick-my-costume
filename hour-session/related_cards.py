#!/usr/bin/env python3
"""Shared related-costume cards + quiz CTA partial for SEO article pages.

2026-09-28 P0 growth fix: ranking article pages linked to /c/ guides only as
plain text links ("Read the full step-by-step guide") and buried the quiz
CTA in the footer block. This module injects, just before the final CTA
block, a tasteful "More costume guides" card grid (3-4 contextual /c/<slug>
cards with the guide's own og image, real time/cost/effort) plus an explicit
"Find my costume" quiz CTA card.

Usage from a builder:
    from related_cards import inject_related_cards
    page = inject_related_cards(page)

Usage on existing files:
    python3 hour-session/related_cards.py <file.html> [more files...]

Design rules (Billy's standing rules):
- zero em/en dashes in user-facing copy (nodash fails loudly)
- every card slug comes from the page's own picks (contextual by
  construction), exists in the bank, and has images/og/<slug>.jpg
- the time/cost/effort line comes from INSTRUCTIONS, never hand-typed
- idempotent: a marker comment means "already injected, skip"
- self-contained CSS with literal colors (article palettes drift between
  builders; this block does not depend on page CSS variables)
"""
import json
import os
import re
import sys
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://pickmycostume.com"
MARKER = "<!-- pmc-related-cards-v1 -->"

_bank = None
_inst = None

def _load():
    global _bank, _inst
    if _bank is None:
        raw = json.load(open(os.path.join(ROOT, "mcp-server", "bank.json"), encoding="utf-8"))
        ideas = raw if isinstance(raw, list) else raw.get("ideas")
        _bank = {i["id"]: i for i in ideas}
    if _inst is None:
        src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
        m = re.search(r'var INSTRUCTIONS = (\{.*?\n\});', src, re.S)
        if not m:
            raise RuntimeError("INSTRUCTIONS block not found in index.html")
        _inst = json.loads(m.group(1))
    return _bank, _inst

def nodash(s):
    if "\u2014" in s or "\u2013" in s:
        raise ValueError("dash found in copy: %s" % s[:80])
    return s

def _esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))

CSS = """<style>
.pmc-rel{margin:44px 0 0}
.pmc-rel h2{font-size:24px;margin:0 0 6px;line-height:1.3}
.pmc-note{color:#cdbcf0;font-size:14px;margin:0 0 18px}
.pmc-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}
.pmc-card{background:#2a1c52;border:1px solid #4b3586;border-radius:14px;overflow:hidden;text-decoration:none;color:#fdf3e3;display:block}
.pmc-card img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block;background:#211540}
.pmc-card .pmc-t{display:block;padding:10px 12px}
.pmc-card .pmc-t strong{display:block;font-size:15px;margin-bottom:2px}
.pmc-card .pmc-t span{color:#cdbcf0;font-size:13px}
.pmc-quiz{display:block;margin-top:14px;background:#211540;border:1px solid #4b3586;border-radius:14px;padding:18px;text-decoration:none;color:#fdf3e3;text-align:center}
.pmc-quiz strong{display:block;font-size:18px;color:#ff8c1a;margin-bottom:4px}
.pmc-quiz span{color:#cdbcf0;font-size:14px}
.pmc-pin{margin-top:10px;text-align:center}
.pmc-pin a{color:#cdbcf0;font-size:14px}
</style>"""

def _triple(pid, inst):
    t = inst[pid]
    return "%s - %s - %s" % (t["time"], t["cost"], t["effort"])

def cards_block(picks):
    """picks: list of (slug, title, triple) tuples, 3-4 items."""
    bank, inst = _load()
    assert 3 <= len(picks) <= 4, "need 3-4 picks, got %d" % len(picks)
    cards = []
    for slug, title, triple in picks:
        nodash(title); nodash(triple)
        og = os.path.join(ROOT, "images", "og", slug + ".jpg")
        assert os.path.exists(og), "og image missing for card: %s" % slug
        cards.append(
            '<a class="pmc-card" href="%s/c/%s">'
            '<img src="%s/images/og/%s.jpg" alt="%s costume" loading="lazy" width="1200" height="630">'
            '<span class="pmc-t"><strong>%s</strong><span>%s</span></span></a>'
            % (SITE, slug, SITE, slug, _esc(title), _esc(title), _esc(triple)))
    quiz_head = nodash("Find my costume")
    quiz_sub = nodash("Answer a few questions and get your pick in 2 minutes. Free, no signup.")
    note = nodash("Step-by-step builds for the picks on this page, with real times and costs.")
    block = (
        MARKER + "\n" + CSS + "\n"
        '<div class="pmc-rel">\n'
        "<h2>More costume guides</h2>\n"
        '<p class="pmc-note">%s</p>\n'
        '<div class="pmc-cards">\n%s\n</div>\n'
        '<a class="pmc-quiz" href="%s/"><strong>%s</strong><span>%s</span></a>\n'
        "</div>"
        % (note, "\n".join(cards), SITE, quiz_head, quiz_sub))
    nodash(block)
    return block

def _page_picks(page):
    """Contextual picks: the page's own /c/ links in order of appearance."""
    bank, inst = _load()
    slugs = []
    for pat in (r'https://pickmycostume\.com/c/([a-z0-9-]+)',
                r'/\?idea=([a-z0-9-]+)'):
        for slug in re.findall(pat, page):
            if slug not in slugs and slug in bank and slug in inst:
                slugs.append(slug)
    return slugs[:4]

def pin_url_for(page):
    """Pinterest save URL for an article page (fix c): url/media/description
    URL-encoded. Media is the page's own og:image; description its
    og:description."""
    m_canon = re.search(r'<link rel="canonical" href="([^"]+)"', page)
    m_img = re.search(r'<meta property="og:image" content="([^"]+)"', page)
    m_desc = re.search(r'<meta property="og:description" content="([^"]+)"', page)
    assert m_canon and m_img and m_desc, "article missing canonical/og tags"
    url = ("https://pinterest.com/pin/create/button/"
           "?url=" + quote(m_canon.group(1), safe="") +
           "&media=" + quote(m_img.group(1), safe="") +
           "&description=" + quote(m_desc.group(1), safe=""))
    return url

def inject_related_cards(page):
    """Insert the cards block before <div class=\\"final\\"> and a Pin-it
    save link into the final share block. Idempotent."""
    if MARKER in page:
        return page
    picks = _page_picks(page)
    assert len(picks) >= 3, "not enough contextual picks on page: %d" % len(picks)
    bank, inst = _load()
    tuples = [(s, bank[s]["title"], _triple(s, inst)) for s in picks]
    block = cards_block(tuples)
    anchor = '<div class="final">'
    assert anchor in page, "no <div class=\"final\"> insertion point"
    page = page.replace(anchor, block + "\n\n" + anchor, 1)
    # Pinterest save link next to the article's share button (fix c)
    pin_anchor = '<p class="fine" id="shareNote" role="status"></p>'
    if "pinterest.com/pin/create/button" not in page:
        pin = pin_url_for(page)
        nodash(pin)
        pin_html = ('<p class="fine pmc-pin">Saving ideas for later? '
                    '<a href="%s" target="_blank" rel="noopener">Pin this guide on Pinterest</a></p>'
                    % _esc(pin))
        if pin_anchor in page:
            page = page.replace(pin_anchor, pin_anchor + "\n" + pin_html, 1)
        else:
            # simpler final blocks (no share button): after the quiz CTA link
            m = re.search(r'(<div class="final">.*?<a class="go" href="https://pickmycostume\.com/">Take the 2-minute quiz</a>)',
                          page, re.S)
            assert m, "no pin insertion point on page"
            page = page[:m.end(1)] + "\n" + pin_html + page[m.end(1):]
    # QA gates on the injected page
    assert MARKER in page
    for slug, title, triple in tuples:
        assert ("/c/%s" % slug) in page, slug
        assert ("images/og/%s.jpg" % slug) in page, slug
    assert "Find my costume" in page
    assert 'href="%s/"' % SITE in page
    assert "\u2014" not in block and "\u2013" not in block
    return page

def process_file(path):
    src = open(path, encoding="utf-8").read()
    out = inject_related_cards(src)
    if out != src:
        open(path, "w", encoding="utf-8").write(out)
        print("injected %s" % path)
    else:
        print("already injected %s" % path)
    return out

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: related_cards.py <file.html> [more files...]")
    for f in sys.argv[1:]:
        process_file(f)
    print("QA: all gates pass")
