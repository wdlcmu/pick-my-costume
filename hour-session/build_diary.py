#!/usr/bin/env python3
"""Build diary.html: a staged, self-contained "my costume build" page.

Status 2026-09-27: STAGED CODE ONLY. Not deployed, not linked from any live
surface, not in sitemap.xml. Byte-inert: this generator writes one new file
(diary.html) and touches nothing else.

What it is: the maker loop. A quiz share reaches one person once; a build
reaches the same person 3-4 times (materials laid out, mid-build, fit check,
finished), each time with a real photo attached in their own messaging app
(photo texts get opened) plus our link. The finished step feeds the two
staged content pipelines that need real builds: the Nov 1 "Made It" gallery
and the @pickmycostume IG cadence (#pickmycostume nudge).

Honesty rules baked in:
- Photos are downscaled on-device and stored in localStorage only. The copy
  says so plainly ("Photos stay on this phone"). Nothing uploads.
- No em/en dashes anywhere in user-facing copy (Billy's standing rule).
- One active build at a time; switching costumes starts a fresh diary.
"""
import json, html, re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "mcp-server", "bank.json")
OUT = os.path.join(ROOT, "diary.html")

POSTHOG_KEY = "phc_t9dkHXAZR5VEjPFm3K5JDzGKFsNNxKcwSxxcEBEeLbS7"  # same project as the rest of the site

DEFAULT_STEPS = [
    "Lay out the materials",
    "Build the main piece",
    "Details and fit check",
    "Wear it",
]

# Share copy per step. Billy's voice: plain, honest, no em/en dashes.
# {title} and {link} are substituted at runtime.
SHARE_TEMPLATES = [
    "Getting ready to make {title} for Halloween. Here is the guide I am following: {link}",
    "Mid-build on my {title} costume. Here is the guide I am following: {link}",
    "Almost done with my {title}. One last fit check, then it is Halloween: {link}",
    "Finished my {title} for Halloween. Your turn, 2-min quiz: {link}",
]

PHOTO_HINT = "Attach your latest build photo above this text in your message app. The photo is yours; the link is ours."

FINISH_NUDGE = ("Post your finished photo wherever your people will see it. "
                "Then share the guide so they can make their own.")


def load_ideas():
    with open(BANK) as f:
        bank = json.load(f)
    ideas = bank["ideas"]
    seen = set()
    out = []
    for it in ideas:
        sid = it["id"]
        assert sid not in seen, "duplicate idea id: " + sid
        seen.add(sid)
        title = it["title"]
        assert title and title.strip(), "empty title for " + sid
        out.append({"id": sid, "title": title})
    # Deterministic order: alphabetical by title, so the picker is scannable.
    out.sort(key=lambda x: x["title"].lower())
    return out


def check_copy(s):
    bad = [c for c in s if c in "\u2013\u2014"]
    assert not bad, "em/en dash found in copy: %r" % s[:60]


def main():
    ideas = load_ideas()
    # Bank size is derived, never hard-coded: the == 138 assert froze this
    # page when the bank grew to 169 on Oct 3. Non-vacuous floor, following
    # the repaired build_aisle_dupes.py pattern. This generator reads no
    # instructions, so there is no slug-set equality to check.
    assert len(ideas) >= 100, "bank yielded only %d ideas" % len(ideas)

    for t in SHARE_TEMPLATES + [PHOTO_HINT, FINISH_NUDGE]:
        check_copy(t)
    for s in DEFAULT_STEPS:
        check_copy(s)

    options = "\n".join(
        '      <option value="%s">%s</option>' % (html.escape(i["id"]), html.escape(i["title"]))
        for i in ideas
    )
    ideas_json = json.dumps(ideas, ensure_ascii=False)
    steps_json = json.dumps(DEFAULT_STEPS, ensure_ascii=False)
    share_json = json.dumps(SHARE_TEMPLATES, ensure_ascii=False)

    page = PAGE_TEMPLATE.format(
        options=options,
        ideas_json=ideas_json,
        steps_json=steps_json,
        share_json=share_json,
        photo_hint=html.escape(PHOTO_HINT),
        finish_nudge=html.escape(FINISH_NUDGE),
        posthog_key=POSTHOG_KEY,
    )
    check_copy(page)  # whole-page dash lint; template copy is user-facing
    with open(OUT, "w") as f:
        f.write(page)
    print("wrote %s (%d bytes, %d ideas)" % (OUT, len(page), len(ideas)))


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>My costume build diary - Pick My Costume</title>
<meta name="description" content="Track your Halloween costume build step by step, snap progress photos, and share each step with friends. Photos stay on your phone. Free, no account.">
<link rel="canonical" href="https://pickmycostume.com/diary">
<meta property="og:type" content="website">
<meta property="og:url" content="https://pickmycostume.com/diary">
<meta property="og:title" content="My costume build diary - Pick My Costume">
<meta property="og:description" content="Track your Halloween costume build step by step and share your progress. Photos stay on your phone.">
<style>
  :root {{ --accent: #7c3aed; --ink: #222; --muted: #666; --line: #e5e0f5; --bg: #faf8ff; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; background: var(--bg); color: var(--ink); }}
  .wrap {{ max-width: 640px; margin: 0 auto; padding: 20px 16px 64px; }}
  h1 {{ font-size: 26px; margin: 8px 0 4px; }}
  .sub {{ color: var(--muted); font-size: 15px; line-height: 1.5; margin: 0 0 20px; }}
  .card {{ background: #fff; border: 1px solid var(--line); border-radius: 14px; padding: 16px; margin: 0 0 14px; }}
  .card h2 {{ font-size: 17px; margin: 0 0 8px; }}
  label.lbl {{ display: block; font-size: 13px; font-weight: 700; color: var(--muted); margin: 0 0 6px; text-transform: uppercase; letter-spacing: .04em; }}
  select, input[type=text] {{ width: 100%; font-size: 16px; padding: 12px; border: 1px solid var(--line); border-radius: 10px; background: #fff; }}
  .step-head {{ display: flex; align-items: center; gap: 10px; }}
  .step-num {{ flex: 0 0 30px; height: 30px; border-radius: 50%; background: var(--accent); color: #fff; font-weight: 700; display: flex; align-items: center; justify-content: center; }}
  .step.done .step-num {{ background: #16a34a; }}
  .step-title {{ flex: 1; font-size: 16px; font-weight: 700; border: 0; padding: 8px 4px; }}
  .step.done .step-title {{ text-decoration: line-through; color: var(--muted); }}
  .photo-row {{ display: flex; gap: 10px; align-items: center; margin: 10px 0; }}
  .photo-row img {{ width: 72px; height: 72px; object-fit: cover; border-radius: 10px; border: 1px solid var(--line); display: none; }}
  .photo-row.has-photo img {{ display: block; }}
  .btn {{ display: inline-block; border: 0; border-radius: 10px; padding: 12px 16px; font-size: 15px; font-weight: 700; cursor: pointer; min-height: 44px; }}
  .btn-primary {{ background: var(--accent); color: #fff; }}
  .btn-ghost {{ background: #f1ecfd; color: var(--accent); }}
  .btn-row {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }}
  .hint {{ font-size: 13px; color: var(--muted); line-height: 1.5; margin: 8px 0 0; }}
  .done-toggle {{ display: flex; align-items: center; gap: 8px; font-size: 15px; margin-top: 10px; }}
  .done-toggle input {{ width: 22px; height: 22px; }}
  .finish {{ border: 2px solid #16a34a; }}
  .fine {{ font-size: 12px; color: var(--muted); line-height: 1.6; margin-top: 24px; }}
  .hidden {{ display: none; }}
footer{{margin-top:40px;font-size:13px;color:#777;}}</style>
</head>
<body>
<div class="wrap">
  <h1>My build diary</h1>
  <p class="sub">Making a costume? Keep the build in one place. Snap a photo at each step and text your progress to the group chat. Photos stay on this phone. Nothing uploads, no account.</p>

  <div class="card">
    <label class="lbl" for="diary-pick">What are you making?</label>
    <select id="diary-pick">
{options}
    </select>
    <p class="hint">Switching costumes starts a fresh diary. Your current build stays until you switch.</p>
  </div>

  <div id="diary-steps"></div>

  <div class="card finish hidden" id="diary-finish">
    <h2>Build complete. Nice work.</h2>
    <p class="sub" style="margin-bottom:10px">{finish_nudge}</p>
    <div class="btn-row">
      <button class="btn btn-primary" id="diary-finish-share">Share the finished build</button>
    </div>
    <p class="hint">{photo_hint}</p>
  </div>

  <p class="fine">Pick My Costume is a free 2-minute Halloween costume quiz. This diary lives on your device only: clearing site data clears it. Anonymous usage stats only, no photos or names leave your phone.</p>
</div>

<script>
/* Build diary (staged 2026-09-27, NOT live-linked). Pure functions up top are
   unit-tested by hour-session/verify-diary.cjs; all DOM work is inside
   initDiary(), which never runs in the harness (no document there). */
var DIARY_IDEAS = {ideas_json};
var DIARY_DEFAULT_STEPS = {steps_json};
var DIARY_SHARE_TEMPLATES = {share_json};
var DIARY_KEY = "pmc_diary_v1";
var DIARY_SID_KEY = "pmc_diary_sid";
var DIARY_MAX_PHOTO = 900; /* px, longest edge */

/* Pure: the share link for a diary build. o=diary keeps attribution with the
   existing share-origin model (?s=<share id>&o=<origin>). */
function diaryLink(slug, sid) {{
  return "https://pickmycostume.com/c/" + slug + "?s=" + sid + "&o=diary";
}}
/* Pure: share text for a build step. No em/en dashes by construction
   (templates are linted at generation time). */
function diaryShareText(stepIdx, title, link) {{
  var t = DIARY_SHARE_TEMPLATES[stepIdx] || DIARY_SHARE_TEMPLATES[0];
  return t.replace("{{title}}", title).replace("{{link}}", link);
}}
/* Pure: downscaled dimensions preserving aspect ratio. */
function downscaleDims(w, h, max) {{
  if (w <= max && h <= max) return {{ w: w, h: h }};
  var s = max / Math.max(w, h);
  return {{ w: Math.round(w * s), h: Math.round(h * s) }};
}}
/* Pure: is this query string asking for a real costume? */
function diaryPickFromQuery(qs, ids) {{
  var m = /[?&]pick=([a-z0-9-]+)/.exec(qs || "");
  if (!m) return null;
  return ids.indexOf(m[1]) >= 0 ? m[1] : null;
}}
/* Pure: blank diary state for a costume. */
function blankDiary(slug) {{
  return {{
    pick: slug,
    steps: DIARY_DEFAULT_STEPS.map(function (label) {{
      return {{ label: label, done: false, photo: null }};
    }})
  }};
}}

function diaryStore() {{
  var mem = {{}};
  try {{
    return {{
      get: function (k) {{ return window.localStorage.getItem(k); }},
      set: function (k, v) {{ window.localStorage.setItem(k, v); }},
      del: function (k) {{ window.localStorage.removeItem(k); }}
    }};
  }} catch (e) {{
    return {{
      get: function (k) {{ return mem[k] || null; }},
      set: function (k, v) {{ mem[k] = String(v); }},
      del: function (k) {{ delete mem[k]; }}
    }};
  }}
}}

function trackDiary(name, props) {{
  try {{
    var p = props || {{}};
    p.via = "diary";
    var q = (typeof location !== "undefined" && location.search) || "";
    if (/[?&](probe|sim)=/.test(q) || /[?&]internal=1/.test(q)) p.internal = true;
    if (window.posthog && posthog.capture) posthog.capture(name, p);
  }} catch (e) {{}}
}}

function initDiary() {{
  var store = diaryStore();
  var ids = DIARY_IDEAS.map(function (i) {{ return i.id; }});
  var byId = {{}};
  DIARY_IDEAS.forEach(function (i) {{ byId[i.id] = i.title; }});

  function getSid() {{
    var sid = store.get(DIARY_SID_KEY);
    if (!sid) {{
      sid = "d" + Math.random().toString(36).slice(2, 10);
      store.set(DIARY_SID_KEY, sid);
    }}
    return sid;
  }}
  function load() {{
    try {{
      var raw = store.get(DIARY_KEY);
      if (!raw) return null;
      var d = JSON.parse(raw);
      if (!d || ids.indexOf(d.pick) < 0 || !d.steps || d.steps.length !== DIARY_DEFAULT_STEPS.length) return null;
      return d;
    }} catch (e) {{ return null; }}
  }}
  function save(d) {{
    try {{ store.set(DIARY_KEY, JSON.stringify(d)); }}
    catch (e) {{ note("Could not save: this phone is out of site storage. Photos are the usual cause."); }}
  }}

  var pick = diaryPickFromQuery(location.search, ids);
  var diary = load();
  if (pick && (!diary || diary.pick !== pick)) {{
    diary = blankDiary(pick);
    save(diary);
  }}
  if (!diary) diary = blankDiary(ids[0]);

  var sel = document.getElementById("diary-pick");
  sel.value = diary.pick;
  sel.addEventListener("change", function () {{
    if (!confirm("Switch to " + byId[sel.value] + "? This starts a fresh diary.")) {{
      sel.value = diary.pick;
      return;
    }}
    diary = blankDiary(sel.value);
    save(diary);
    renderSteps();
    trackDiary("diary_build_started", {{ pick: diary.pick }});
  }});

  var noteEl = null;
  function note(msg) {{
    if (!noteEl) {{
      noteEl = document.createElement("p");
      noteEl.className = "hint";
      noteEl.style.color = "#b91c1c";
      sel.parentNode.appendChild(noteEl);
    }}
    noteEl.textContent = msg;
  }}

  function share(text, stepIdx) {{
    var done = function (ok) {{
      trackDiary("diary_share_created", {{ step: stepIdx, share_id: getSid(), ok: !!ok }});
    }};
    if (navigator.share) {{
      navigator.share({{ title: "Pick My Costume", text: text }}).then(function () {{ done(true); }}, function () {{ done(false); }});
    }} else if (navigator.clipboard && navigator.clipboard.writeText) {{
      navigator.clipboard.writeText(text).then(function () {{ note("Copied. Paste it under your photo in your message app."); done(true); }}, function () {{ done(false); }});
    }} else {{
      prompt("Copy your build update:", text);
      done(false);
    }}
  }}

  function renderSteps() {{
    var host = document.getElementById("diary-steps");
    host.innerHTML = "";
    var sid = getSid();
    var allDone = true;
    diary.steps.forEach(function (st, i) {{
      if (!st.done) allDone = false;
      var card = document.createElement("div");
      card.className = "card step" + (st.done ? " done" : "");
      var head = document.createElement("div");
      head.className = "step-head";
      var num = document.createElement("div");
      num.className = "step-num";
      num.textContent = String(i + 1);
      var titleInput = document.createElement("input");
      titleInput.className = "step-title";
      titleInput.type = "text";
      titleInput.value = st.label;
      titleInput.setAttribute("aria-label", "Step " + (i + 1) + " name");
      titleInput.addEventListener("change", function () {{
        st.label = titleInput.value.trim() || DIARY_DEFAULT_STEPS[i];
        titleInput.value = st.label;
        save(diary);
      }});
      head.appendChild(num);
      head.appendChild(titleInput);
      card.appendChild(head);

      var row = document.createElement("div");
      row.className = "photo-row" + (st.photo ? " has-photo" : "");
      var img = document.createElement("img");
      img.alt = "Build photo, step " + (i + 1);
      if (st.photo) img.src = st.photo;
      var fileBtn = document.createElement("label");
      fileBtn.className = "btn btn-ghost";
      fileBtn.textContent = st.photo ? "Retake photo" : "Add photo";
      var file = document.createElement("input");
      file.type = "file";
      file.accept = "image/*";
      file.style.display = "none";
      file.addEventListener("change", function () {{
        var f = file.files && file.files[0];
        if (!f) return;
        var rd = new FileReader();
        rd.onload = function () {{
          var im = new Image();
          im.onload = function () {{
            try {{
              var d = downscaleDims(im.width, im.height, DIARY_MAX_PHOTO);
              var cv = document.createElement("canvas");
              cv.width = d.w; cv.height = d.h;
              cv.getContext("2d").drawImage(im, 0, 0, d.w, d.h);
              st.photo = cv.toDataURL("image/jpeg", 0.72);
              save(diary);
              trackDiary("diary_photo_added", {{ step: i, pick: diary.pick }});
              renderSteps();
            }} catch (e) {{
              note("That photo is too big to keep on this phone. Try a smaller one.");
            }}
          }};
          im.src = rd.result;
        }};
        rd.readAsDataURL(f);
      }});
      fileBtn.appendChild(file);
      row.appendChild(img);
      row.appendChild(fileBtn);
      card.appendChild(row);

      var toggle = document.createElement("label");
      toggle.className = "done-toggle";
      var cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = !!st.done;
      cb.addEventListener("change", function () {{
        st.done = cb.checked;
        save(diary);
        trackDiary(cb.checked ? "diary_step_done" : "diary_step_undone", {{ step: i, pick: diary.pick }});
        renderSteps();
      }});
      var tspan = document.createElement("span");
      tspan.textContent = "Done";
      toggle.appendChild(cb);
      toggle.appendChild(tspan);
      card.appendChild(toggle);

      var brow = document.createElement("div");
      brow.className = "btn-row";
      var sb = document.createElement("button");
      sb.className = "btn btn-primary";
      sb.textContent = "Share this step";
      sb.addEventListener("click", function () {{
        var link = diaryLink(diary.pick, sid);
        share(diaryShareText(i, byId[diary.pick], link), i);
      }});
      brow.appendChild(sb);
      card.appendChild(brow);
      var hint = document.createElement("p");
      hint.className = "hint";
      hint.textContent = "{photo_hint}";
      card.appendChild(hint);

      host.appendChild(card);
    }});
    var fin = document.getElementById("diary-finish");
    fin.classList.toggle("hidden", !allDone);
  }}

  document.getElementById("diary-finish-share").addEventListener("click", function () {{
    var link = diaryLink(diary.pick, getSid());
    share(diaryShareText(3, byId[diary.pick], link), 3);
  }});

  renderSteps();
  trackDiary("diary_opened", {{ pick: diary.pick }});
}}

if (typeof document !== "undefined") {{
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initDiary);
  else initDiary();
}}

/* PostHog: anonymous usage stats only. No photos, names, or answers are sent. Session replay is off. */
(function () {{
  try {{
    var s = document.createElement("script");
    s.src = "https://us.i.posthog.com/static/array.js";
    s.async = true;
    s.onload = function () {{
      try {{ if (window.posthog && posthog.init) posthog.init("{posthog_key}", {{ api_host: "https://us.i.posthog.com", autocapture: false }}); }} catch (e) {{}}
    }};
    document.head.appendChild(s);
  }} catch (e) {{}}
}})();
</script>
<footer>Built with Muse.</footer></body>
</html>
"""

if __name__ == "__main__":
    main()
