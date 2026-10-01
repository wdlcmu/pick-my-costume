#!/usr/bin/env python3
"""Generate per-role share cards for family/group cast ideas.

MagicShot.ai novel-scout steal (2026-09-27): the family share carries one
share card per COSTUME today. This generates one card per FAMILY MEMBER
ROLE instead: images/og/<slug>--<role-slug>.jpg. The family cast share
mints one unfurl link per role, so each member's card can be dropped in the
group chat like MagicShot's shareable squad pack.

Card content is deliberately name-free: kicker = "YOUR FAMILY'S (or
GROUP'S) 2026 HALLOWEEN COSTUME", title = the role (e.g. "Little Pup"),
subline = the costume idea title, decision pill (time · effort) + AI disclosure
as usual.
User-typed names never touch card pixels or URLs (no name leaks); the
recipient's card identifies the ROLE, never the person.

Sources: CASTS in index.html (role labels), mcp-server/bank.json (titles,
audiences, decision pair), photos/<slug>.webp (concept photos).
Fails loudly on missing photos/pairs, role-slug collisions within an
idea, or em/en dashes in baked text (draw_card asserts the last).

Re-run after CASTS or bank edits. Code only: the deploy batch picks these
files up like any other og card.
"""
import json
import os
import re
import sys

from gen_og_cards import draw_card, W, H

ROOT = os.path.dirname(os.path.abspath(__file__))
OG_DIR = os.path.join(ROOT, "images", "og")


def role_slug(role):
    """URL-safe slug for a role label. Mirrors roleSlugFor() in index.html."""
    return re.sub(r"[^a-z0-9]+", "-", role.lower()).strip("-")


def role_display(role):
    """Title-case a role label for card pixels. Preserves internal caps
    (Y2K stays Y2K, 80s stays 80s)."""
    return "-".join(
        " ".join(w[:1].upper() + w[1:] for w in part.split(" "))
        for part in role.split("-")
    )


def parse_casts(src):
    """Brace-counting parse of `var CASTS = {...};` in app.js (index.html in
    older trees)."""
    m = re.search(r"var CASTS = \{", src)
    assert m, "CASTS not found in index.html"
    i, depth = m.end() - 1, 0
    j = i
    while True:
        ch = src[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    body = src[i:j + 1]
    out = {}
    for mm in re.finditer(r'"([a-z0-9-]+)":\{', body):
        slug, depth, k = mm.group(1), 1, mm.end()
        while depth:
            if body[k] == "{":
                depth += 1
            elif body[k] == "}":
                depth -= 1
            k += 1
        seg = body[mm.start():k]
        if 'mode:"assign"' in seg:
            roles = re.findall(r'\{r:"([^"]+)"', seg)
        else:
            pm = re.search(r"pool:\[([^\]]+)\]", seg)
            roles = re.findall(r'"([^"]+)"', pm.group(1)) if pm else []
        # dedupe, keep first-seen order (assign casts repeat kid roles)
        seen, uniq = set(), []
        for r in roles:
            if r not in seen:
                seen.add(r)
                uniq.append(r)
        out[slug] = uniq
    return out


def main():
    bank = json.load(open(os.path.join(ROOT, "mcp-server", "bank.json"),
                          encoding="utf-8"))
    ideas = {it["id"]: it for it in bank["ideas"]}
    instr = bank["instructions"]
    # 2026-10-01: the bank moved from index.html to app.js (bundle split);
    # read app.js first, index.html fallback kept for older trees.
    src_path = os.path.join(ROOT, "app.js")
    if not os.path.exists(src_path):
        src_path = os.path.join(ROOT, "index.html")
    src = open(src_path, encoding="utf-8").read()
    casts = parse_casts(src)
    assert casts, "no CASTS entries parsed"

    only = set(s.strip() for s in os.environ.get("SLUGS", "").split(",")
               if s.strip())

    made, combos = 0, []
    for slug, roles in sorted(casts.items()):
        if only and slug not in only:
            continue
        idea = ideas.get(slug)
        assert idea, "CASTS slug missing from bank: " + slug
        g = instr.get(slug) or {}
        t, e = g.get("time"), g.get("effort")
        assert t and e, "missing decision pair for " + slug
        triple = "%s \u00b7 %s" % (t, e)
        photo = os.path.join(ROOT, "photos", slug + ".webp")
        assert os.path.exists(photo), "missing concept photo: " + photo
        aud = idea.get("audience") or []
        kicker = "A 2026 HALLOWEEN COSTUME IDEA"
        seen_slugs = {}
        for role in roles:
            rs = role_slug(role)
            assert rs, "role slugified empty: %r (%s)" % (role, slug)
            assert rs not in seen_slugs, \
                "role-slug collision in %s: %r and %r both -> %s" % (
                    slug, seen_slugs[rs], role, rs)
            seen_slugs[rs] = role
            card = draw_card(photo, role_display(role), triple,
                             sub=idea["title"], kicker=kicker)
            out = os.path.join(OG_DIR, "%s--%s.jpg" % (slug, rs))
            card.save(out, "JPEG", quality=84)
            combos.append((slug, rs))
            made += 1

    # post-conditions: every file a valid 1200x630 JPEG
    for slug, rs in combos:
        p = os.path.join(OG_DIR, "%s--%s.jpg" % (slug, rs))
        with open(p, "rb") as f:
            from PIL import Image
            im = Image.open(f)
            assert im.size == (W, H), "bad size %s: %s" % (p, im.size)
            assert im.format == "JPEG", "not jpeg: " + p
    print("role share cards: %d written to images/og/ (%d ideas)" %
          (made, len(set(s for s, _ in combos))))


if __name__ == "__main__":
    main()
