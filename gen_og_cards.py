#!/usr/bin/env python3
"""Regenerate images/og/<slug>.jpg as decision cards for every idea.

Replaces gen_og_photos.py (plain center-cropped photos). Each card:
  1200x630, concept photo full-bleed with a dark brand gradient on the left,
  kicker + title + decision pill (time · effort) + pickmycostume.com footer +
  "AI-generated concept photo" disclosure.

Why: the link unfurl (iMessage/SMS/vote/pantry-challenge links) is the
recipient's first impression, and it was a bare photo with no name, cost,
or time. The card carries the decision triple so the preview pre-sells
the pick. Pinterest's save flow also scrapes og:image, so these cards
power the Pinterest bridge too.

Sources: photos/<slug>.webp (concept photos) and index.html -- the idea bank
(titles) and var INSTRUCTIONS (decision pair: time/effort, plus steps).
index.html is the CANONICAL single source of truth, shared with the /c/ page
chips and meta (gen_share_function.py parses the same fields): the og badge
must never be baked from a second source (2026-09-29: three-way drift --
chips said "10 min" from [slug].js, the badge baked "15 min + drying" from a
stale mcp-server/bank.json, and the card file was stale even against that).
The "+ drying" suffix is NOT read from the time field: it is appended only
when a build step mentions paint or glue, so the badge can never claim drying
time the steps do not need.

Per-idea photo overrides: PHOTO_OVERRIDES below. The default cover-crop can
cut the subject badly on tall portraits (error-404's center crop cut the face
at the eyes and hid the cracked phone); "contain-right" fits the whole photo
right-aligned against the dark panel instead, duel-screen style.

Outputs overwrite images/og/<slug>.jpg IN PLACE: the /c/ pages reference
https://pickmycostume.com/images/og/<slug>.jpg, so zero HTML/JS changes.
Fails loudly on any missing photo, missing triple, or em/en dash in
baked text.
"""
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H = 1200, 630

DARK = (22, 13, 40)        # #160d28 brand panel
ORANGE = (255, 140, 26)    # #ff8c1a kicker/pill
CREAM = (253, 243, 227)    # #fdf3e3
LAV = (201, 184, 232)      # #c9b8e8 footer disclosure
WHITE = (255, 255, 255)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
FB = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
FR = os.path.join(FONT_DIR, "DejaVuSans.ttf")
for f in (FB, FR):
    assert os.path.exists(f), "missing font: " + f

# Viewer-neutral: the friend viewing a shared link is the audience, not the
# sharer, so "YOUR ..." was the wrong perspective (2026-09-29).
KICKER = "A 2026 HALLOWEEN COSTUME IDEA"
DISCLOSURE = "AI-generated concept photo"
BRAND = "pickmycostume.com"
BAD_CHARS = ("\u2013", "\u2014")  # en/em dash: never in user-facing art

# Per-idea photo treatment overrides (2026-09-29 #30). Values:
#   "contain-right": fit the whole photo (contain) right-aligned against the
#   dark brand panel instead of cover-cropping. The left text zone keeps its
#   dark gradient; the full composition stays visible.
PHOTO_OVERRIDES = {
    "error-404": "contain-right",  # center crop cut the face at the eyes
                                   # and hid the cracked phone
}


def cover(im, w, h):
    """Cover-fit crop to w x h."""
    sw, sh = im.size
    scale = max(w / sw, h / sh)
    im = im.resize((int(sw * scale + 0.5), int(sh * scale + 0.5)), Image.LANCZOS)
    x0 = (im.width - w) // 2
    y0 = (im.height - h) // 2
    return im.crop((x0, y0, x0 + w, y0 + h))


def left_gradient(w, h, span=760, peak=235):
    """Dark overlay, opaque at the left edge fading to transparent."""
    alpha = Image.new("L", (w, h), 0)
    px = alpha.load()
    for x in range(min(span, w)):
        a = int(peak * (1 - x / span) ** 1.15)
        for y in range(h):
            px[x, y] = a
    solid = Image.new("RGB", (w, h), DARK)
    return solid, alpha


def bottom_band(w, h, top=470, peak=150):
    alpha = Image.new("L", (w, h), 0)
    px = alpha.load()
    for y in range(top, h):
        a = int(peak * (y - top) / (h - top))
        for x in range(w):
            if px[x, y] < a:
                px[x, y] = a
    solid = Image.new("RGB", (w, h), DARK)
    return solid, alpha


def wrap(draw, text, font, max_w, max_lines):
    words = text.split()
    lines, line = [], ""
    for wd in words:
        nxt = (line + " " + wd).strip()
        if draw.textlength(nxt, font=font) <= max_w:
            line = nxt
        else:
            if line:
                lines.append(line)
            line = wd
            if len(lines) == max_lines:
                break
    if len(lines) < max_lines and line:
        lines.append(line)
    elif len(lines) == max_lines and line and lines[-1] != line:
        # trim last line with ellipsis
        t = lines[-1]
        while t and draw.textlength(t + "\u2026", font=font) > max_w:
            t = t.rsplit(" ", 1)[0] if " " in t else t[:-1]
        lines[-1] = (t + "\u2026") if t else "\u2026"
    return lines[:max_lines]


def draw_card(photo_path, title, triple, sub=None, kicker=KICKER,
              photo_mode=None):
    # Role cards (2026-09-27): sub = the costume idea title, drawn as a
    # small line between the role title and the triple pill. None keeps the
    # classic single-card layout byte-identical. kicker defaults to KICKER
    # so the classic path is unchanged; role cards pass their own.
    # photo_mode "contain-right" (PHOTO_OVERRIDES): fit the whole photo
    # right-aligned against the dark panel instead of cover-cropping.
    for s in (title, triple, kicker, DISCLOSURE, BRAND, sub or ""):
        for bad in BAD_CHARS:
            assert bad not in s, "em/en dash in baked text: %r" % s
    if photo_mode == "contain-right":
        im = Image.new("RGB", (W, H), DARK)
        ph = Image.open(photo_path).convert("RGB")
        scale = min(W / ph.width, H / ph.height)
        pw, phh = int(ph.width * scale + 0.5), int(ph.height * scale + 0.5)
        ph = ph.resize((pw, phh), Image.LANCZOS)
        im.paste(ph, (W - pw, (H - phh) // 2))
    else:
        im = cover(Image.open(photo_path).convert("RGB"), W, H)

    solid, alpha = left_gradient(W, H)
    im.paste(solid, (0, 0), alpha)
    solid2, alpha2 = bottom_band(W, H)
    im.paste(solid2, (0, 0), alpha2)

    d = ImageDraw.Draw(im)
    x0 = 64

    # kicker
    fk = ImageFont.truetype(FB, 32)
    d.text((x0, 58), kicker, font=fk, fill=ORANGE)

    # title: up to 2 lines, shrink until it fits
    title_lines, tsize = None, 66
    for tsize in (66, 58, 50, 44):
        ft = ImageFont.truetype(FB, tsize)
        title_lines = wrap(d, title, ft, 660, 2)
        if title_lines:
            break
    assert title_lines, "title would not fit: %r" % title
    y = 118
    for ln in title_lines:
        d.text((x0, y), ln, font=ft, fill=WHITE)
        y += int(tsize * 1.22)
    y += 18
    if sub:
        # role-card subline: the costume idea title, cream, one line
        fs = ImageFont.truetype(FR, 30)
        subline = sub
        while d.textlength(subline, font=fs) > 660 and len(subline) > 1:
            subline = subline.rsplit(" ", 1)[0] if " " in subline else subline[:-1]
        if d.textlength(subline, font=fs) > 660:
            subline = subline[:40]
        d.text((x0, y), subline, font=fs, fill=CREAM)
        y += 44

    # triple pill
    psize = 38
    fp = ImageFont.truetype(FB, psize)
    while d.textlength(triple, font=fp) > 620 and psize > 24:
        psize -= 2
        fp = ImageFont.truetype(FB, psize)
    tw = d.textlength(triple, font=fp)
    pad_x, pad_y, rad = 30, 15, 30
    d.rounded_rectangle([x0, y, x0 + tw + pad_x * 2, y + psize + pad_y * 2],
                        radius=rad, fill=ORANGE)
    d.text((x0 + pad_x, y + pad_y - 3), triple, font=fp, fill=DARK)

    # footer
    fb2 = ImageFont.truetype(FB, 30)
    d.text((x0, H - 62), BRAND, font=fb2, fill=ORANGE)
    fr = ImageFont.truetype(FR, 24)
    dw = d.textlength(DISCLOSURE, font=fr)
    d.text((W - 64 - dw, H - 56), DISCLOSURE, font=fr, fill=LAV)
    return im


# Brace-matching parse of var INSTRUCTIONS in index.html (same technique as
# gen_share_function.py: the object has a trailing comma strict JSON rejects).
def _parse_instructions(src):
    marker = "var INSTRUCTIONS ="
    i = src.index("{", src.index(marker) + len(marker))
    depth, in_str, esc = 0, False, False
    for j in range(i, len(src)):
        ch = src[j]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    seg = re.sub(r",\s*([}\]])", r"\1", src[i:j + 1])
                    return json.loads(seg)
    raise ValueError("INSTRUCTIONS object not balanced")


def main():
    # Canonical source: the bank + INSTRUCTIONS, the same fields
    # the /c/ chips and meta use (2026-09-29 #23: single source of truth).
    # 2026-09-30: the bank moved from index.html to app.js (bundle split);
    # read app.js first, index.html fallback kept for older trees.
    # mcp-server/bank.json is NOT read here; stage 2 syncs its triple fields
    # from the bank instead.
    bank_path = os.path.join(ROOT, "app.js")
    if not os.path.exists(bank_path):
        bank_path = os.path.join(ROOT, "index.html")
    src = open(bank_path, encoding="utf-8").read()
    # Parse ideas ONLY inside the IDEAS bank array (2026-09-29): the
    # QUESTIONS section also uses {id:"...", title:"..."} entries, and a
    # whole-src regex misparsed 6 question ids as ideas. The IDEAS array
    # is the canonical bank boundary; UI edits elsewhere can never poison
    # generation again. INSTRUCTIONS (brace-matched below) is unaffected:
    # "var INSTRUCTIONS =" appears once, in the bank section.
    bank_src = src[src.index("var IDEAS = ["):
                   src.index("/* ================= CONFIG: SHARE")]
    ideas = re.findall(r'\{id:"([^"]+)", title:"([^"]+)"', bank_src)
    assert ideas, "no ideas parsed from " + bank_path
    assert len(ideas) == len(set(s for s, _ in ideas)), "duplicate idea ids"
    titles = {slug: title for slug, title in ideas}
    instr = _parse_instructions(src)
    missing = [s for s in titles if s not in instr]
    assert not missing, "ideas missing instructions: %s" % missing

    og_dir = os.path.join(ROOT, "images", "og")
    os.makedirs(og_dir, exist_ok=True)

    made = 0
    only = set(s.strip() for s in os.environ.get("SLUGS", "").split(",") if s.strip())
    for slug, title in ideas:
        if only and slug not in only:
            continue
        g = instr[slug]
        t, e = g.get("time"), g.get("effort")
        assert t and e, "missing decision pair for %s" % slug
        # "+ drying" is derived, never read: strip any baked suffix, then
        # append only when a build step mentions paint or glue (#23).
        t = re.sub(r"\s*\+\s*drying\s*$", "", t, flags=re.I)
        if any(re.search(r"paint|glue", st, re.I) for st in g.get("s", [])):
            t += " + drying"
        triple = "%s \u00b7 %s" % (t, e)  # middle dot separators
        photo = os.path.join(ROOT, "photos", slug + ".webp")
        assert os.path.exists(photo), "missing concept photo: %s" % photo
        card = draw_card(photo, title, triple,
                         photo_mode=PHOTO_OVERRIDES.get(slug))
        out = os.path.join(og_dir, slug + ".jpg")
        card.save(out, "JPEG", quality=84)
        made += 1

    # post-conditions: every idea's file a valid 1200x630 JPEG
    for slug in titles:
        p = os.path.join(og_dir, slug + ".jpg")
        with Image.open(p) as chk:
            assert chk.size == (W, H), "bad size %s: %s" % (p, chk.size)
            assert chk.format == "JPEG", "not jpeg: %s" % p
    print("og decision cards: %d/%d written to images/og/" % (made, len(titles)))


if __name__ == "__main__":
    main()
