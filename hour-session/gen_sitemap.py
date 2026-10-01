#!/usr/bin/env python3
"""Regenerate sitemap.xml with <lastmod> on every URL.

Reads the existing sitemap.xml for the non-/c/ page list (loc, changefreq,
priority are preserved as curated), takes the /c/<slug> list from the live
idea bank in index.html (same source as gen_share_function.py), and writes
sitemap.xml with lastmod set to today. Run after bank changes or when the
non-/c/ page list changes. lastmod is a crawl hint; refreshing it on regen
is standard practice for a first indexed submission.
"""
import datetime
import os
import re
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sitemap.xml")
INDEX = os.path.join(ROOT, "app.js")  # bank moved from index.html 2026-09-30

NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
ET.register_namespace("", NS)

tree = ET.parse(SRC)
entries = []  # (loc, changefreq, priority), non-/c/ pages only
for url in tree.getroot().findall("{%s}url" % NS):
    loc = url.find("{%s}loc" % NS).text.strip()
    if "/c/" in loc:
        continue
    cf = url.find("{%s}changefreq" % NS)
    pr = url.find("{%s}priority" % NS)
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

today = datetime.date.today().isoformat()
urlset = ET.Element("{%s}urlset" % NS)


def add_url(loc, changefreq, priority):
    u = ET.SubElement(urlset, "{%s}url" % NS)
    ET.SubElement(u, "{%s}loc" % NS).text = loc
    ET.SubElement(u, "{%s}lastmod" % NS).text = today
    ET.SubElement(u, "{%s}changefreq" % NS).text = changefreq
    ET.SubElement(u, "{%s}priority" % NS).text = priority


for loc, cf, pr in entries:
    add_url(loc, cf, pr)
for slug in sorted(slugs):
    add_url("https://pickmycostume.com/c/" + slug, "monthly", "0.8")

xml = ET.tostring(urlset, encoding="unicode")
with open(SRC, "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + xml + "\n")

# Verify the write parses and covers the bank.
t2 = ET.parse(SRC)
locs = [u.find("{%s}loc" % NS).text for u in t2.getroot().findall("{%s}url" % NS)]
missing = [s for s in slugs if "https://pickmycostume.com/c/" + s not in locs]
assert not missing, "sitemap missing slugs: %s" % missing
print("wrote %s: %d urls (%d guides), lastmod=%s" % (SRC, len(locs), len(slugs), today))
