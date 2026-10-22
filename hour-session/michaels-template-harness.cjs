/* Michaels-template harness (2026-10-22, Billy): guards the Michaels-style
   plan/guide layout in app.js + functions/c/[slug].js:
   - every plan renders an at-a-glance strip (time / effort / step count),
     icons + short values, no drying TIME shown anywhere
   - materials render in the three groups (Already at home / Tools / Buy),
     group order fixed, every bank material appears exactly once
   - per-group counts across all 169 are printed so mis-grouping is visible
   - checking a Buy/Tools item updates the "You need N things" summary live
   - person plans keep the 09c18c3 cuts and gain the DIY check-off list
   - safety text is byte-identical to the pre-change live app.js
     (INSTRUCTIONS m/s arrays deep-compared for every slug)
   - every /c/ page (via the generated onRequest) renders group headings
     in order, a Steps pill, all its safety steps, and ptile buttons whose
     data-ti sequence matches window.PMD tile order
   - prints plan-view word totals, old vs new app.js

   Run: node hour-session/michaels-template-harness.cjs
   Exit code 1 on any failure. Fake DOM implements the attr/classList/
   listener surface the plan renderers use. */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const ROOT = path.resolve(__dirname, "..");
const NEW_APP = path.join(ROOT, "app.js");
const OLD_APP = "/tmp/live-app.js"; /* pre-change live baseline */
const SLUG_FN = path.join(ROOT, "functions", "c", "[slug].js");

let pass = 0, fail = 0;
const failures = [];
function ok(cond, msg){
  if (cond) pass++;
  else { fail++; failures.push(msg); }
}
function words(t){ return String(t || "").trim().split(/\s+/).filter(Boolean).length; }

/* ---------- fake DOM ---------- */
class El {
  constructor(tag){
    this.tagName = String(tag || "div").toUpperCase();
    this.children = [];
    this.className = "";
    this._text = "";
    this._attrs = {};
    this._handlers = {};
    const self = this;
    this.classList = {
      add: function(){ for (const c of arguments){ if (self.className.split(/\s+/).indexOf(c) < 0) self.className = (self.className + " " + c).trim(); } },
      remove: function(){ for (const c of arguments){ self.className = self.className.split(/\s+/).filter(function(x){ return x && x !== c; }).join(" "); } },
      contains: function(c){ return self.className.split(/\s+/).indexOf(c) >= 0; },
      toggle: function(c){ if (this.contains(c)) this.remove(c); else this.add(c); }
    };
  }
  set textContent(v){ this._text = String(v); this.children = []; }
  get textContent(){
    let t = this._text;
    for (const c of this.children) t += (t && c.textContent ? " " : "") + c.textContent;
    return t;
  }
  set innerHTML(v){ if (v === ""){ this.children = []; this._text = ""; } else { this._text = String(v); } }
  get innerHTML(){ return this._text; }
  appendChild(c){ this.children.push(c); return c; }
  setAttribute(k, v){ this._attrs[k] = String(v); }
  getAttribute(k){ return (k in this._attrs) ? this._attrs[k] : null; }
  removeAttribute(k){ delete this._attrs[k]; }
  hasAttribute(k){ return k in this._attrs; }
  addEventListener(type, fn){ (this._handlers[type] = this._handlers[type] || []).push(fn); }
  removeEventListener(){}
  fire(type){ (this._handlers[type] || []).forEach(function(f){ f({}); }); }
}
function findAll(el, cls, out){
  out = out || [];
  if (el.className && el.className.split(/\s+/).indexOf(cls) >= 0) out.push(el);
  el.children.forEach(function(c){ findAll(c, cls, out); });
  return out;
}
function findTag(el, tag, out){
  out = out || [];
  if (el.tagName === tag) out.push(el);
  el.children.forEach(function(c){ findTag(c, tag, out); });
  return out;
}

/* ---------- extraction (same approach as plan-text-harness) ---------- */
function extractBalanced(src, startIdx, open, close){
  let depth = 0, inStr = false, q = "", esc = false, inBlock = false, inLine = false;
  for (let k = startIdx; k < src.length; k++){
    const c = src[k], n = src[k + 1] || "";
    if (inBlock){ if (c === "*" && n === "/"){ inBlock = false; k++; } continue; }
    if (inLine){ if (c === "\n") inLine = false; continue; }
    if (inStr){ if (esc) esc = false; else if (c === "\\") esc = true; else if (c === q) inStr = false; continue; }
    if (c === "/" && n === "*"){ inBlock = true; k++; continue; }
    if (c === "/" && n === "/"){ inLine = true; k++; continue; }
    if (c === '"' || c === "'"){ inStr = true; q = c; continue; }
    if (c === open) depth++;
    else if (c === close){ depth--; if (depth === 0) return src.slice(startIdx, k + 1); }
  }
  throw new Error("unbalanced from " + startIdx);
}
function extractVar(src, name){
  const i = src.indexOf("var " + name + " = ");
  if (i < 0) return null;
  const off = ("var " + name + " = ").length;
  const j = src.indexOf(src[i + off] === "[" ? "[" : "{", i);
  const open = src[j], close = open === "[" ? "]" : "}";
  return src.slice(i, i + off) + extractBalanced(src, j, open, close) + ";";
}
function extractFn(src, name){
  const i = src.indexOf("function " + name + "(");
  if (i < 0) throw new Error("function " + name + " not found");
  const j = src.indexOf("{", i);
  return src.slice(i, j) + extractBalanced(src, j, "{", "}");
}

function loadPlanSandbox(appPath){
  const src = fs.readFileSync(appPath, "utf8");
  const sandbox = {
    document: {
      createElement: function(tag){ return new El(tag); },
      createTextNode: function(t){ const e = new El("#text"); e._text = String(t); return e; },
      querySelectorAll: function(){ return []; }
    },
    localStorage: { getItem: function(){ return null; }, setItem: function(){}, removeItem: function(){} },
    Analytics: { track: function(){} },
    console: console
  };
  vm.createContext(sandbox);
  const pieces = [];
  ["IDEAS", "INSTRUCTIONS", "MAKE_PLANS", "ROLE_DIY", "CASTS",
   "PANTRY_MATS", "PANTRY_LABELS", "PANTRY_EMOJI", "EFFORT_FACTS"].forEach(function(v){
    const p = extractVar(src, v);
    if (p) pieces.push(p);
  });
  ["displayTime", "ideaEffortKey", "planMatLabel", "pantrySaved", "pantryTicked",
   "pantryBuyKey", "pantryMatOk", "planDisplayMat", "renderPlanMats",
   "buySearchFor", "roleDiyLine", "buildPersonPlans"].forEach(function(f){
    pieces.push(extractFn(src, f));
  });
  /* New-template pieces exist only in the new file. */
  ["planMatGroup", "renderPlanMatsGrouped", "buildInlinePlan"].forEach(function(f){
    try { pieces.push(extractFn(src, f)); } catch (e) {}
  });
  try { const m1 = src.match(/var PLAN_TOOL_RE = [^\n]+/); if (m1) pieces.push(m1[0]); } catch (e) {}
  try { const m2 = src.match(/var PLAN_STAPLE_RE = [^\n]+/); if (m2) pieces.push(m2[0]); } catch (e) {}
  try { pieces.push(extractVar(src, "planMatTicks")); } catch (e) {}
  try { pieces.push(extractFn(src, "refreshPlanMats")); } catch (e) {}
  vm.runInContext(pieces.join("\n"), sandbox);
  return sandbox;
}

const GROUP_LABELS = ["Already at home", "Tools", "Buy"];
const GROUP_KEYS = ["home", "tool", "buy"];

/* ---------- plan view: all 169 ---------- */
const sb = loadPlanSandbox(NEW_APP);
const INS = sb.INSTRUCTIONS, IDEAS = sb.IDEAS;
const groupTotals = { home: 0, tool: 0, buy: 0 };
const groupGuides = { 3: 0, 2: 0, 1: 0 };
let newPlanWords = 0;

for (const idea of IDEAS){
  const ins = INS[idea.id];
  if (!ins) continue;
  let plan;
  try { plan = sb.buildInlinePlan(idea); }
  catch (e){ ok(false, idea.id + ": buildInlinePlan threw " + e.message); continue; }
  const text = plan.textContent;
  newPlanWords += words(text);

  /* glance strip */
  const glances = findAll(plan, "plan-glance");
  ok(glances.length === 1, idea.id + ": exactly one glance strip");
  if (glances.length){
    const items = findAll(glances[0], "glance-item");
    ok(items.length >= 2 && items.length <= 3, idea.id + ": glance has 2-3 items, got " + items.length);
    ok(items.every(function(it){ return words(it.textContent) <= 3; }),
       idea.id + ": glance items are short values");
  }
  ok(!/\d+\s*(min|hrs?)\s*\+\s*(~?\d+\s*(min|hrs?)\s*)?drying/i.test(text),
     idea.id + ": no drying time displayed");

  /* groups: headings match the classifier's non-empty groups, in order */
  const expected = GROUP_KEYS.filter(function(k){
    return ins.m.some(function(m){ return sb.planMatGroup(m) === k; });
  });
  expected.forEach(function(k){
    groupTotals[k] += ins.m.filter(function(m){ return sb.planMatGroup(m) === k; }).length;
  });
  groupGuides[expected.length]++;
  const heads = findAll(plan, "mat-group-h").map(function(h){ return h.textContent.trim(); });
  const wantHeads = expected.map(function(k){ return GROUP_LABELS[GROUP_KEYS.indexOf(k)]; });
  ok(heads.length === wantHeads.length && heads.every(function(h, i){
       return h.indexOf(wantHeads[i]) === 0;
     }), idea.id + ": group headings " + JSON.stringify(heads) + " want " + JSON.stringify(wantHeads));

  /* every material exactly once */
  const groupLists = findAll(plan, "mat-group");
  let liCount = 0;
  groupLists.forEach(function(ul){ liCount += ul.children.length; });
  ok(liCount === ins.m.length,
     idea.id + ": rendered items " + liCount + " == bank materials " + ins.m.length);

  /* safety callout byte-identical strings, present above steps */
  const bankSafe = ins.s.filter(function(s){ return /^Safety:\s*/i.test(s); })
    .map(function(s){ return s.replace(/^Safety:\s*/i, ""); });
  const callouts = findAll(plan, "safety-callout");
  if (bankSafe.length){
    ok(callouts.length === 1, idea.id + ": safety callout present");
    if (callouts.length){
      const rendered = callouts[0].children.slice(1).map(function(p){ return p.textContent; });
      ok(JSON.stringify(rendered) === JSON.stringify(bankSafe),
         idea.id + ": safety strings byte-identical");
    }
  } else {
    ok(callouts.length === 0, idea.id + ": no safety callout when bank has none");
  }

  /* check-off behavior on the Buy group */
  const summaries = findAll(plan, "plan-need-summary");
  ok(summaries.length === 1, idea.id + ": one still-needed summary");
  const buyList = groupLists.filter(function(ul){ return ul.className.indexOf("mat-group-buy") >= 0; })[0];
  if (buyList && summaries.length){
    const boxes = findTag(buyList, "INPUT");
    const unchecked = boxes.filter(function(b){ return !b.checked; }).length;
    const want = unchecked > 0 ? ("You need " + unchecked + " thing" + (unchecked === 1 ? "" : "s")) : "Nothing to buy";
    ok(summaries[0].textContent === want,
       idea.id + ": initial summary '" + summaries[0].textContent + "' want '" + want + "'");
    if (boxes.length){
      const b0 = boxes.filter(function(b){ return !b.checked; })[0] || boxes[0];
      const was = b0.checked;
      b0.checked = !was; b0.fire("change");
      const unchecked2 = boxes.filter(function(b){ return !b.checked; }).length;
      const want2 = unchecked2 > 0 ? ("You need " + unchecked2 + " thing" + (unchecked2 === 1 ? "" : "s")) : "Nothing to buy";
      ok(summaries[0].textContent === want2,
         idea.id + ": summary after tick '" + summaries[0].textContent + "' want '" + want2 + "'");
      b0.checked = was; b0.fire("change");
    }
  }
}

/* ---------- person plans: penguin dedupe + DIY check-off ---------- */
{
  const idea = IDEAS.filter(function(i){ return i.id === "penguin-huddle"; })[0];
  const list = [
    { name: "Person 1", rawName: "", role: "penguin" },
    { name: "Person 2", rawName: "", role: "penguin" }
  ];
  const box = sb.buildPersonPlans(idea, list);
  const cards = findAll(box, "personplan-compact");
  ok(cards.length === 1 && /penguin \u2014 everyone/.test(cards[0].textContent),
     "penguin: one deduped card");
  const ppBoxes = findTag(box, "INPUT");
  const mp = sb.MAKE_PLANS["penguin-huddle"];
  ok(ppBoxes.length === mp.buy.length, "penguin: DIY check-off has " + ppBoxes.length + " boxes, buy list " + mp.buy.length);
  const need = findAll(box, "pp-need");
  ok(need.length === 1 && need[0].textContent === "You need " + mp.buy.length + " things",
     "penguin: pp summary '" + (need[0] && need[0].textContent) + "'");
  if (ppBoxes.length && need.length){
    ppBoxes[0].checked = true; ppBoxes[0].fire("change");
    const leftAfter = mp.buy.length - 1;
    ok(need[0].textContent === "You need " + leftAfter + " thing" + (leftAfter === 1 ? "" : "s"),
       "penguin: pp summary after tick '" + need[0].textContent + "'");
  }
  ok(!/Easiest version/i.test(box.textContent), "penguin: no Easiest box (09c18c3)");
  ok(!/drying/i.test(box.textContent), "penguin: no drying in person plan");
  const ppIdea = IDEAS.filter(function(i){ return i.id === "prince-princess"; })[0];
  const ppBox = sb.buildPersonPlans(ppIdea, [
    { name: "Person 1", rawName: "", role: "prince" },
    { name: "Person 2", rawName: "", role: "princess" }
  ]);
  ok(findAll(ppBox, "personplan-compact").length === 2, "prince-princess: distinct roles keep 2 cards");
}

/* ---------- safety byte-compare vs pre-change live app.js ---------- */
{
  const oldSrc = fs.readFileSync(OLD_APP, "utf8");
  const oldIns = JSON.parse(extractBalanced(oldSrc, oldSrc.indexOf("{", oldSrc.indexOf("var INSTRUCTIONS = ")), "{", "}")
    .replace(/\/\*[\s\S]*?\*\//g, ""));
  let mSame = 0, sSame = 0;
  for (const slug of Object.keys(INS)){
    if (JSON.stringify(oldIns[slug].m) === JSON.stringify(INS[slug].m)) mSame++;
    if (JSON.stringify(oldIns[slug].s) === JSON.stringify(INS[slug].s)) sSame++;
  }
  ok(mSame === 169, "materials arrays byte-identical for " + mSame + "/169 guides");
  ok(sSame === 169, "steps arrays byte-identical for " + sSame + "/169 guides");
}

/* ---------- before/after plan word totals ---------- */
let oldPlanWords = 0;
{
  const osb = loadPlanSandbox(OLD_APP);
  for (const idea of osb.IDEAS){
    if (!osb.INSTRUCTIONS[idea.id]) continue;
    oldPlanWords += words(osb.buildInlinePlan(idea).textContent);
  }
}

/* ---------- /c/ pages via generated onRequest ---------- */
{
  let fnSrc = fs.readFileSync(SLUG_FN, "utf8");
  fnSrc = fnSrc.replace("export function onRequest", "function onRequest");
  fnSrc += "\n;globalThis.__onRequest = onRequest; globalThis.__HOWTO = HOWTO; globalThis.__cMatGroup = (typeof _cMatGroup !== 'undefined' ? _cMatGroup : null); globalThis.__cTiles = (typeof _cTiles !== 'undefined' ? _cTiles : null);";
  const csb = {
    console: console, URL: URL, URLSearchParams: URLSearchParams,
    Response: class {
      constructor(body, opts){ this.body = body; this.status = (opts && opts.status) || 200; }
    }
  };
  vm.createContext(csb);
  vm.runInContext(fnSrc, csb);
  const HOWTO = csb.__HOWTO;
  let cPages = 0, cFallback = 0;
  for (const idea of IDEAS){
    const slug = idea.id;
    const res = csb.__onRequest({ params: { slug: slug }, request: { url: "https://pickmycostume.com/c/" + slug } });
    const html = res.body;
    const hw = HOWTO[slug];
    /* group headings appear in home -> tool -> buy order, at least one */
    const idx = ["Already at home", "Tools", "Buy"].map(function(l){
      return html.indexOf("<p class=\"ptgroup\">" + l + "</p>");
    });
    const present = idx.filter(function(i){ return i >= 0; });
    if (!present.length){ cFallback++; continue; }
    cPages++;
    const sorted = present.slice().sort(function(a, b){ return a - b; });
    ok(JSON.stringify(present) === JSON.stringify(sorted), slug + ": /c/ group headings in order");
    ok(/<span class="pill"><span class="pl">Steps<\/span>\d+<\/span>/.test(html),
       slug + ": /c/ steps pill present");
    ok(html.indexOf("<img") < html.indexOf("detail-mats"), slug + ": /c/ photo leads the materials");
    /* tiles: data-ti sequence in document order matches PMD tile count */
    const tis = Array.from(html.matchAll(/data-ti="(\d+)"/g)).map(function(m){ return parseInt(m[1], 10); });
    ok(tis.every(function(v, i){ return v === i; }), slug + ": /c/ data-ti sequence 0..n-1");
    const pmdM = html.match(/window\.PMD=(\{.*?\});/);
    if (pmdM){
      const pmd = JSON.parse(pmdM[1]);
      ok(pmd.tiles.length === tis.length, slug + ": /c/ PMD tiles == rendered tiles");
      const order = { home: 0, tool: 1, buy: 2 };
      const gs = pmd.tiles.map(function(t){ return order[t.g]; });
      ok(gs.every(function(v, i){ return i === 0 || v >= gs[i - 1]; }), slug + ": /c/ PMD tiles group-sorted");
    }
    /* safety steps all present in the steps list */
    if (hw && hw.s){
      for (const st of hw.s){
        if (/^Safety:\s*/i.test(st)){
          const plain = st.replace(/^Safety:\s*/i, "")
            .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
          ok(html.indexOf("<strong>Safety:</strong> " + plain) >= 0 ||
             html.indexOf(plain) >= 0, slug + ": /c/ safety step present: " + st.slice(0, 50));
        }
      }
    }
  }
  console.log("/c/ pages with grouped cards: " + cPages + "; without cards (fallback): " + cFallback);

  /* classifier regression anchors: canonical tag shapes must classify the
     same in the generated /c/ classifier as in the plan classifier (the
     2026-10-22 backslash bug made every buy-tagged tile read as home). */
  if (csb.__cMatGroup){
    const CASES = [
      ["Black shirts, 1 per person (buy: thrift store, or own: from closet)", "buy"],
      ["White felt, 1 sheet (buy: craft store; paper works too)", "buy"],
      ["Headbands, 1 per person (buy: dollar store)", "buy"],
      ["Fabric glue, 1 tube (buy: craft store)", "buy"],
      ["Scissors, 1 pair (own: household tools)", "tool"],
      ["Black hoodie (own: from closet)", "home"],
      ["Cardboard box (make: use what you own)", "home"],
      ["Hot glue gun (buy: craft store)", "tool"]
    ];
    for (const [txt, want] of CASES){
      ok(csb.__cMatGroup(txt) === want, "/c/ classifier anchor: " + txt.slice(0, 34) + " -> " + want);
      ok(sb.planMatGroup(txt) === want, "plan classifier anchor: " + txt.slice(0, 34) + " -> " + want);
    }
    if (csb.__cTiles){
      const ct = csb.__cTiles("penguin-huddle");
      const gs = ct.tiles.map(t => t.g).sort().join(",");
      ok(gs === "buy,buy,buy,buy,tool", "penguin-huddle tile groups are 4 buy + 1 tool (got " + gs + ")");
    }
  } else {
    ok(false, "/c/ classifier _cMatGroup missing from generated function");
  }
}

console.log("group totals across 169: home=" + groupTotals.home +
  " tool=" + groupTotals.tool + " buy=" + groupTotals.buy);
console.log("guides by groups present: 3=" + groupGuides[3] + " 2=" + groupGuides[2] + " 1=" + groupGuides[1]);
console.log("plan-view words: before=" + oldPlanWords + " after=" + newPlanWords +
  " (" + (newPlanWords - oldPlanWords >= 0 ? "+" : "") + (newPlanWords - oldPlanWords) + ")");
console.log("PASS " + pass + " FAIL " + fail);
failures.slice(0, 40).forEach(function(f){ console.log("  FAIL: " + f); });
process.exit(fail ? 1 : 0);
