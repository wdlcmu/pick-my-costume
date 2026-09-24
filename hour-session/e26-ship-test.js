/* E26 ship QA: realistic bubbling-event tests for the 2026-09-24 production push.
   Usage: node hour-session/e26-ship-test.js
   Evals the REAL main script from index.html against a fake DOM with real event
   semantics (bubbling, focus/blur, stopPropagation, closest), then drives:
     A. cast state-loss fix (re-tap picked card = no-op, names/size/roles survive;
        full re-render restores a 4-person cast, not size 2)
     B. fit refinement (conditional chip row, chips really re-score the ordered
        top 3; panel restore on re-render)
     C. one-hero results (hero + 2 compact runners-up, single shared detail;
        picked runner-up auto-reopens after a re-render)
     D. personal role cards (one card per cast member, "Send this card to <name>"
        with a name / "Send this card" without; share-sheet branch when
        navigator.share exists, clipboard fallback otherwise)
     E. browse parity (card body opens full detail w/ pick + AI + share) & sticky bar
     F. flowOrder never exceeds 5 questions
*/
var fs = require("fs");
var vm = require("vm");
var HTML = process.env.PMC_TEST_HTML || (process.env.HOME + "/workspace/builds/pick-my-costume/index.html");
var src = fs.readFileSync(HTML, "utf8");

(function(){
"use strict";
/* silence the app's console.debug chatter */
var _dbg = console.debug; console.debug = function(){};

/* ---------- fake DOM with real event semantics ---------- */
function matches(el, sel){
  if (!el || !el.tagName) return false;
  if (sel[0] === ".") return (el.className || "").split(/\s+/).indexOf(sel.slice(1)) >= 0;
  if (sel[0] === "#") return el.getAttribute && el.getAttribute("id") === sel.slice(1);
  return el.tagName.toLowerCase() === sel.toLowerCase();
}
function makeEl(tag){
  var el = {
    tagName: String(tag).toUpperCase(), children: [], parentNode: null,
    style: {}, className: "", _text: "", _html: "",
    value: "", placeholder: "", maxLength: 0, type: "", selected: false,
    disabled: false, checked: false,
    onclick: null, oninput: null, onchange: null, onfocus: null, onblur: null,
    _listeners: {}, _attrs: {},
    setAttribute: function(k, v){ this._attrs[k] = String(v); },
    getAttribute: function(k){ return (k in this._attrs) ? this._attrs[k] : null; },
    appendChild: function(c){ c.parentNode = this; this.children.push(c); return c; },
    removeChild: function(c){ var i = this.children.indexOf(c); if (i >= 0){ this.children.splice(i,1); c.parentNode = null; } return c; },
    insertBefore: function(c, ref){ c.parentNode = this; var i = ref ? this.children.indexOf(ref) : -1; if (i < 0) this.children.push(c); else this.children.splice(i, 0, c); return c; },
    addEventListener: function(t, f){ (this._listeners[t] = this._listeners[t] || []).push(f); },
    closest: function(sel){ var e = this; while (e){ if (matches(e, sel)) return e; e = e.parentNode; } return null; },
    scrollIntoView: function(){}, select: function(){}, blur0: null,
    focus: function(){
      if (document.activeElement && document.activeElement !== this && document.activeElement.blur) document.activeElement.blur();
      document.activeElement = this;
      this.dispatchEvent({ type: "focus", bubbles: false });
    },
    blur: function(){
      if (document.activeElement === this) document.activeElement = null;
      this.dispatchEvent({ type: "blur", bubbles: false });
    },
    click: function(){ this.dispatchEvent({ type: "click", bubbles: true }); },
    classList: null, /* assigned below, needs `el` */    dispatchEvent: function(ev){
      ev.target = ev.target || this;
      var stopped = false;
      ev.stopPropagation = function(){ stopped = true; };
      ev.preventDefault = function(){};
      var node = this;
      while (node && !stopped){
        var ls = (node._listeners[ev.type] || []).slice();
        for (var i = 0; i < ls.length; i++){ ls[i].call(node, ev); if (stopped) break; }
        var prop = node["on" + ev.type];
        if (typeof prop === "function" && !stopped) prop.call(node, ev);
        if (!ev.bubbles) break;
        node = node.parentNode;
      }
      return !stopped;
    }
  };
  Object.defineProperty(el, "textContent", { get: function(){ return this._text; }, set: function(v){ this._text = String(v); } });
  Object.defineProperty(el, "firstChild", { get: function(){ return this.children[0] || null; } });
  Object.defineProperty(el, "innerHTML", {
    get: function(){ return this._html; },
    set: function(v){ this._html = String(v); this.children.forEach(function(c){ c.parentNode = null; }); this.children = []; }
  });
  el.classList = {
    add: function(c){ var s = (el.className || "").split(/\s+/).filter(Boolean); if (s.indexOf(c) < 0) s.push(c); el.className = s.join(" "); },
    remove: function(c){ el.className = (el.className || "").split(/\s+/).filter(function(x){ return x && x !== c; }).join(" "); },
    contains: function(c){ return (el.className || "").split(/\s+/).indexOf(c) >= 0; },
    toggle: function(c){ if (this.contains(c)) this.remove(c); else this.add(c); }
  };
  allElements.push(el);
  return el;
}
var idRegistry = {};
var allElements = [];
function $(id){
  if (!idRegistry[id]){ var el = makeEl("div"); el.setAttribute("id", id); idRegistry[id] = el; }
  return idRegistry[id];
}
function docQueryAll(sel){
  /* simple selectors only: .class, #id, TAG */
  if (sel[0] === ".") return allElements.filter(function(e){ return (e.className || "").split(/\s+/).indexOf(sel.slice(1)) >= 0; });
  if (sel[0] === "#"){ var e = idRegistry[sel.slice(1)]; return e ? [e] : []; }
  var t = sel.toUpperCase();
  return allElements.filter(function(e){ return e.tagName === t; });
}
global.document = {
  createElement: makeEl,
  createTextNode: function(t){ return { nodeType: 3, text: t, parentNode: null }; },
  getElementById: $,
  querySelectorAll: docQueryAll,
  querySelector: function(sel){ var r = docQueryAll(sel); return r[0] || null; },
  activeElement: null,
  execCommand: function(){ return true; },
  head: makeEl("head"),
  body: makeEl("body")
};
global.window = {
  getSelection: function(){ return { toString: function(){ return ""; } }; },
  scrollTo: function(){}
};
global.location = { search: "" };
/* Node 24 ships a read-only global navigator; the app only reads
   navigator.userAgent / .share / .clipboard, all safe as-is. */
var _ls = {};
global.localStorage = {
  getItem: function(k){ return (k in _ls) ? _ls[k] : null; },
  setItem: function(k, v){ _ls[k] = String(v); },
  removeItem: function(k){ delete _ls[k]; }
};

/* ---------- eval the REAL app script ---------- */
var blocks = src.match(/<script>([\s\S]*?)<\/script>/g);
var main = blocks.filter(function(b){ return b.length > 10000; })[0]
  .replace(/^<script>/, "").replace(/<\/script>$/, "");
vm.runInThisContext(main, { filename: "index.html#main" });
console.debug = _dbg;
console.log("APP: real main script evaled (" + main.length + " chars)");

// silence further debug chatter
console.debug = function(){};

/* ---------- test helpers (T_ prefix avoids colliding with app vars) ---------- */
var T_pass = 0, T_fail = 0, T_notes = [];
function T_ok(cond, name, extra){
  if (cond){ T_pass++; }
  else { T_fail++; T_notes.push("FAIL: " + name + (extra ? " -- " + extra : "")); console.log("  FAIL " + name + (extra ? " -- " + extra : "")); }
}
function T_findAll(root, pred, out){
  out = out || [];
  if (!root || !root.children) return out;
  if (pred(root)) out.push(root);
  root.children.forEach(function(c){ T_findAll(c, pred, out); });
  return out;
}
function T_byClass(root, cls){ return T_findAll(root, function(e){ return (e.className || "").split(/\s+/).indexOf(cls) >= 0; }); }
function T_byText(root, tag, text){
  return T_findAll(root, function(e){ return e.tagName === tag && (e._text || "").indexOf(text) >= 0; });
}
function T_click(el){ el.dispatchEvent({ type: "click", bubbles: true }); }
function T_type(inp, text){
  /* keystroke-by-keystroke, the way a phone does it */
  inp.focus();
  var cur = "";
  for (var i = 0; i < text.length; i++){
    cur += text[i]; inp.value = cur;
    inp.dispatchEvent({ type: "input", bubbles: true });
  }
  inp.blur();
}
function T_change(sel, val){
  sel.value = val;
  sel.dispatchEvent({ type: "change", bubbles: true });
}
function T_clearInp(inp){
  /* clear a field the way a thumb does: focus, delete, input event, blur */
  inp.focus();
  inp.value = "";
  inp.dispatchEvent({ type: "input", bubbles: true });
  inp.blur();
}
function T_O(qid, label){
  return qById(qid).options.filter(function(o){ return o.label === label; })[0];
}
function T_tracked(name){
  return (Analytics._q || []).filter(function(e){ return e[0] === name; });
}
function T_clearLS(){ for (var k in _ls) delete _ls[k]; }

/* ---------- scenario A: cast state-loss fix ---------- */
console.log("A. cast state-loss (re-tap picked card = no-op)");
(function(){
  T_clearLS();
  for (var k in castStateByIdea) delete castStateByIdea[k];
  for (var k2 in panelOpenByIdea) delete panelOpenByIdea[k2];
  state = { qi: 0, answers: {} };
  state.answers = {
    q1: T_O("q1", "My family"), q2: T_O("q2", "Funny"),
    q4: T_O("q4", "Couch-level"), qocc: T_O("qocc", "Trick-or-treating"),
    qinterest: qById("qinterest").options.filter(function(o){ return o.tags.animals; })[0]
  };
  var res = scoreIdeas();
  T_ok(res[0].idea.id === "blue-dog-family", "A1 blue-dog-family is #1 for family/animals", res[0].idea.id);
  renderResults(res);
  var box = $("r-cards");
  var hero = T_byClass(box, "hero12")[0];
  T_ok(!!hero, "A2 hero wrapper present");
  var card = T_byClass(hero, "card")[0];
  var pickBtn = T_byText(card, "BUTTON", "This is my pick")[0];
  T_ok(!!pickBtn, "A3 pick button found in hero card");
  var nSaved0 = T_tracked("pick_saved").length;
  T_click(pickBtn); /* real bubbling click through the card wrapper */
  T_ok(T_tracked("pick_saved").length === nSaved0 + 1, "A4 pick_saved tracked once");
  var panel = T_byClass(card, "castbox")[0];
  T_ok(!!panel, "A5 cast panel mounted after pick");
  /* size 4, names typed keystroke-by-keystroke, a role changed, a kid toggled */
  var sizeBtns = T_byClass(panel, "castbtns")[0].children;
  T_click(sizeBtns.filter(function(b){ return b._text === "4"; })[0]);
  var rows = T_byClass(panel, "castrow");
  T_ok(rows.length === 4, "A6 four cast rows after size=4", rows.length);
  var inputs = rows.map(function(r){ return T_byClass(r, "castname")[0].children[1]; });
  T_type(inputs[0], "Dido"); T_type(inputs[1], "Billy");
  T_type(inputs[2], "Capri"); T_type(inputs[3], "Nana");
  var sels = rows.map(function(r){ return T_findAll(r, function(e){ return e.tagName === "SELECT"; })[0]; });
  T_change(sels[2], "little pup");
  var tg = T_byClass(rows[2], "casttoggle")[0];
  T_click(tg); /* Capri -> kid */
  var lineText = T_byClass(panel, "castline")[0];
  function lineStr(){ return lineText.children.map(function(c){ return c._text || c.text || ""; }).join(""); }
  T_ok(lineStr().indexOf("Dido") >= 0 && lineStr().indexOf("Capri") >= 0, "A7 cast line shows typed names", lineStr());
  /* THE BUG REPRO: re-tap the picked card body (title), the way a thumb does */
  var title = T_findAll(card, function(e){ return e.tagName === "H3"; })[0];
  var rowsBefore = T_byClass(card, "castrow").length;
  T_click(title);
  var rowsAfter = T_byClass(card, "castrow").length;
  T_ok(rowsAfter === rowsBefore && rowsBefore === 4, "A8 re-tap card body keeps 4 rows (was: rebuild to defaults)", rowsBefore + "->" + rowsAfter);
  var inputsAfter = T_byClass(card, "castrow").map(function(r){ return T_byClass(r, "castname")[0].children[1]; });
  T_ok(inputsAfter[0].value === "Dido" && inputsAfter[2].value === "Capri", "A9 names survive re-tap", inputsAfter.map(function(i){return i.value;}).join(","));
  T_ok(T_tracked("pick_saved").length === nSaved0 + 1, "A10 no duplicate pick_saved on re-tap");
  /* re-tap the pick BUTTON itself */
  T_click(pickBtn);
  var rowsAfter2 = T_byClass(card, "castrow").length;
  var namesAfter2 = T_byClass(card, "castrow").map(function(r){ return T_byClass(r, "castname")[0].children[1].value; });
  T_ok(rowsAfter2 === 4 && namesAfter2[1] === "Billy", "A11 re-tap pick button is a no-op", namesAfter2.join(","));
  /* bShare hidden after pick (dedupe) */
  var shareBtns = T_byText(card, "BUTTON", "Share this idea");
  T_ok(shareBtns.length === 0 || shareBtns[0].style.display === "none", "A12 card-level Share hidden once panel has its own");
  /* THE FIX REPRO: a full results re-render (fit refinement path) must restore
     the 4-person cast, not reset the panel to size 2 */
  renderResults(scoreIdeas());
  var cardR = T_byClass(T_byClass($("r-cards"), "hero12")[0], "card")[0];
  var rowsR = T_byClass(cardR, "castrow");
  T_ok(rowsR.length === 4, "A13 re-render restores 4 cast rows (not reset to 2)", rowsR.length);
  var namesR = rowsR.map(function(r){ return T_byClass(r, "castname")[0].children[1].value; });
  T_ok(namesR[0] === "Dido" && namesR[3] === "Nana", "A14 names survive full re-render", namesR.join(","));
  var kidBtns = T_byClass(cardR, "castbtns")[1].children;
  var kidSel = kidBtns.filter(function(b){ return (b.className || "").indexOf("sel") >= 0; });
  T_ok(kidSel.length === 1 && kidSel[0]._text === "1", "A15 kid count restored after re-render");
  var selR = T_findAll(rowsR[2], function(e){ return e.tagName === "SELECT"; })[0];
  var selOpt = T_findAll(selR, function(e){ return e.tagName === "OPTION"; }).filter(function(o){ return o.selected; })[0];
  T_ok(selOpt && selOpt.value === "little pup", "A16 role override restored after re-render", selOpt && selOpt.value);
  /* THE "pup 2" FIX: 6 people on blue-dog-family forces duplicate roles; the
     auto-assigner must hand out the base role as-is, never a " 2" suffix that
     exists in no dropdown and reads badly in headlines. */
  (function(){
    var people6 = [];
    for (var i = 0; i < 6; i++) people6.push({name: "P" + (i + 1), kid: false});
    var roles6 = assignCast("blue-dog-family", people6, {});
    var opts = castRoleOptions("blue-dog-family");
    var suffixed = roles6.filter(function(r){ return / \d+$/.test(r); });
    T_ok(suffixed.length === 0, "A17 no numeric-suffixed roles on overflow", roles6.join(","));
    var alien = roles6.filter(function(r){ return opts.indexOf(r) < 0; });
    T_ok(alien.length === 0, "A18 every assigned role is a real dropdown option", roles6.join(","));
  })();
})();

/* ---------- scenario B: fit refinement + panel restore ---------- */
console.log("B. fit refinement + panel restore on re-render");
(function(){
  T_clearLS();
  for (var k in castStateByIdea) delete castStateByIdea[k];
  for (var k2 in panelOpenByIdea) delete panelOpenByIdea[k2];
  state = { qi: 0, answers: {} };
  /* find a solo path where fit changes the top 3 */
  var found = null;
  var q2s = qById("q2").options, q4s = qById("q4").options;
  outer:
  for (var a = 0; a < q2s.length; a++) for (var b = 0; b < q4s.length; b++){
    var vis = qById("qinterest").options.filter(function(o){
      var kk = Object.keys(o.tags)[0];
      return IDEAS.some(function(i){ return i.audience.indexOf("solo") >= 0 && i.tags[kk] > 0; });
    });
    for (var c = 0; c < vis.length; c++){
      state.answers = { q1: T_O("q1","Solo"), q2: q2s[a], q4: q4s[b],
        qocc: T_O("qocc","Trick-or-treating"), qinterest: vis[c] };
      if (fitChangesTop3()){ found = {a:a,b:b,oi:vis[c]}; break outer; }
    }
  }
  T_ok(!!found, "B1 found a solo path where fit changes top-3");
  if (!found) return;
  renderResults(scoreIdeas());
  var box = $("r-cards");
  var fr = T_byClass(box, "fitref")[0];
  T_ok(!!fr, "B2 refinement row shown on results (not a 6th question)");
  var chips = T_findAll(fr, function(e){ return e.tagName === "BUTTON"; });
  T_ok(chips.length === 3, "B3 three fit chips", chips.length);
  var seenFit = {};
  [["Feminine looks", 0], ["Masculine looks", 1], ["Anything goes", 2]].forEach(function(pair){
    T_click(chips[pair[1]]); /* each tap re-scores AND re-renders; old chip refs still dispatch */
    seenFit[scoreIdeas().map(function(s){ return s.idea.id; }).join(",")] = true;
  });
  T_ok(T_tracked("fit_refined").length >= 3, "B4 fit_refined tracked per chip");
  T_ok(Object.keys(seenFit).length > 1, "B5 fit chips change the ordered top 3 (real assertion)",
    Object.keys(seenFit).join(" | "));
  /* family flow: no refinement row */
  state = { qi: 0, answers: {} };
  state.answers = { q1: T_O("q1","My family"), q2: T_O("q2","Funny"), q4: T_O("q4","Couch-level"),
    qocc: T_O("qocc","Trick-or-treating"),
    qinterest: qById("qinterest").options.filter(function(o){ return o.tags.animals; })[0] };
  renderResults(scoreIdeas());
  T_ok(T_byClass($("r-cards"), "fitref").length === 0, "B6 no refinement row for family flow");
  /* panel restore: pick a cast idea, type names, re-render, panel comes back */
  var card = T_byClass(T_byClass($("r-cards"), "hero12")[0], "card")[0];
  T_click(T_byText(card, "BUTTON", "This is my pick")[0]);
  var panel = T_byClass(card, "castbox")[0];
  var rows = T_byClass(panel, "castrow");
  var inputs = rows.map(function(r){ return T_byClass(r, "castname")[0].children[1]; });
  T_type(inputs[0], "Dido"); T_type(inputs[1], "Billy");
  renderResults(scoreIdeas()); /* simulate any re-render (e.g. refinement) */
  var card2 = T_byClass(T_byClass($("r-cards"), "hero12")[0], "card")[0];
  var panel2 = T_byClass(card2, "castbox")[0];
  T_ok(!!panel2, "B7 panel auto-restored after re-render");
  var names2 = T_byClass(card2, "castrow").map(function(r){ return T_byClass(r, "castname")[0].children[1].value; });
  T_ok(names2[0] === "Dido" && names2[1] === "Billy", "B8 names restored from castStateByIdea", names2.join(","));
})();

/* ---------- scenario C: one-hero results ---------- */
console.log("C. one-hero results");
(function(){
  T_clearLS();
  state = { qi: 0, answers: {} };
  state.answers = { q1: T_O("q1","Solo"), q2: T_O("q2","Scary"), q4: T_O("q4","Go all out"),
    qocc: T_O("qocc","Bar / club night"),
    qinterest: qById("qinterest").options.filter(function(o){ return o.tags.tv; })[0] };
  var res = scoreIdeas();
  renderResults(res);
  var box = $("r-cards");
  T_ok(T_byClass(box, "hero12").length === 1, "C1 exactly one hero wrapper");
  var heroCard = T_byClass(T_byClass(box, "hero12")[0], "card")[0];
  T_ok(T_byText(heroCard, "BUTTON", "This is my pick").length === 1, "C2 hero has the primary CTA");
  T_ok(T_byText(box, "H3", "Also made your top 3").length === 1, "C3 runners-up heading present");
  var grids = T_byClass(box, "bgrid");
  var ruGrid = grids[grids.length - 1];
  var ruCards = T_findAll(ruGrid, function(e){ return e.tagName === "DIV" && (e.className || "").split(/\s+/).indexOf("bcard") >= 0 && e.parentNode === ruGrid; });
  T_ok(ruCards.length === 2, "C4 two compact runner-up cards", ruCards.length);
  T_ok(T_byText(ruCards[0], "P", "Tap for the full plan").length === 1, "C5 runner-up shows tap hint, not full card");
  /* tap runner-up 1 -> shared detail opens below the grid */
  T_click(ruCards[0]);
  var detail = ruGrid.parentNode.children.filter(function(c){ return c.tagName === "DIV" && c.style.display !== "none" && c !== ruGrid; })[0];
  T_ok(!!detail && T_byClass(detail, "card").length === 1, "C6 tapping runner-up opens its full card inline");
  var dCard = T_byClass(detail, "card")[0];
  T_ok(T_byText(dCard, "BUTTON", "This is my pick").length === 1, "C7 detail card has pick CTA");
  T_ok(T_findAll(dCard, function(e){ return e.tagName === "IMG"; }).length === 0, "C8 detail card skips duplicate art/title (noArt)");
  T_ok(T_tracked("runnerup_opened").length === 1, "C9 runnerup_opened tracked");
  /* tap runner-up 2 -> replaces, only one open */
  T_click(ruCards[1]);
  var detailCards = T_byClass(box, "card").filter(function(c){
    var p = c.parentNode; while (p && p !== box) p = p.parentNode; return true;
  });
  var openDetails = T_findAll(box, function(e){ return e.tagName === "DIV" && e.style && e.style.display !== "none" && T_byClass(e, "card").length === 1 && e.children[0] && e.children[0].className === "card"; });
  T_ok(T_tracked("runnerup_opened").length === 2, "C10 second runner-up tracked");
  /* tap runner-up 2 again -> closes */
  T_click(ruCards[1]);
  var closedCard = T_byClass(detail, "card").length;
  T_ok(detail.style.display === "none" && closedCard === 0, "C11 tapping open runner-up closes it");
  /* pick inside a runner-up detail works (the LAST pick-button card in the
     box is the open detail; the first is the hero) */
  T_click(ruCards[0]);
  var pickCards = T_byClass(box, "card").filter(function(c){ return T_byText(c, "BUTTON", "This is my pick").length > 0; });
  var d2 = pickCards[pickCards.length - 1];
  T_ok(pickCards.length === 2, "C12x detail card is distinct from the hero card", pickCards.length);
  var dPick = T_byText(d2, "BUTTON", "This is my pick")[0];
  var nS = T_tracked("pick_saved").length;
  T_click(dPick);
  T_ok(T_tracked("pick_saved").length === nS + 1, "C12 pick works inside runner-up detail");
  T_ok(T_byClass(d2, "castbox").length + T_findAll(d2, function(e){ return e.tagName === "TEXTAREA"; }).length > 0, "C13 detail shows share/AI panel after pick");
  /* results header copy: one decision, not three (static HTML check) */
  T_ok(src.indexOf("Here is what you got") >= 0, "C14 header names the single decision");
  /* browse tail button, not a 76-card wall */
  var tail = T_byText(box, "BUTTON", "Browse all ")[0];
  T_ok(!!tail && tail._text.indexOf("76") >= 0, "C15 browse tail is one button", tail && tail._text);
  T_ok(T_byText(box, "BUTTON", "Show 3 more ideas").length === 0, "C16 no more-ideas stacking button");
  /* C12 picked inside the runner-up detail; a full re-render (the fit
     refinement path) must reopen that detail and remount the pick panel,
     not silently strand the pick. */
  renderResults(scoreIdeas());
  var box2 = $("r-cards");
  var remounted = T_byClass(box2, "card").filter(function(c){ return c.getAttribute("data-panel") === "1"; });
  T_ok(remounted.length === 1, "C17 picked runner-up detail auto-reopened with panel remounted", remounted.length);
  T_ok(T_tracked("runnerup_opened").length === 4, "C18 auto-reopen tracked", T_tracked("runnerup_opened").length);
})();

/* ---------- scenario D: personal role cards ---------- */
console.log("D. personal role cards");
(function(){
  T_clearLS();
  for (var k in castStateByIdea) delete castStateByIdea[k];
  for (var k2 in panelOpenByIdea) delete panelOpenByIdea[k2];
  state = { qi: 0, answers: {} };
  state.answers = { q1: T_O("q1","My family"), q2: T_O("q2","Funny"), q4: T_O("q4","Couch-level"),
    qocc: T_O("qocc","Trick-or-treating"),
    qinterest: qById("qinterest").options.filter(function(o){ return o.tags.animals; })[0] };
  renderResults(scoreIdeas());
  var card = T_byClass(T_byClass($("r-cards"), "hero12")[0], "card")[0];
  T_click(T_byText(card, "BUTTON", "This is my pick")[0]);
  var panel = T_byClass(card, "castbox")[0];
  var rows = T_byClass(panel, "castrow");
  var inputs = rows.map(function(r){ return T_byClass(r, "castname")[0].children[1]; });
  T_type(inputs[0], "Dido"); T_type(inputs[1], "Billy");
  var makeBtn = T_byText(panel, "BUTTON", "Make personal cards")[0];
  T_ok(!!makeBtn, "D1 Make personal cards button present");
  T_click(makeBtn);
  var pcards = T_byClass(panel, "pcard");
  T_ok(pcards.length === 2, "D2 one card per named person", pcards.length);
  var heads = pcards.map(function(c){ return T_byClass(c, "pcard-head")[0]._text; });
  T_ok(heads[0] === "Dido is going as Aussie Dog Family", "D3 personal headline", heads[0]);
  var sends = pcards.map(function(c){ return T_byText(c, "BUTTON", "Send this card to ")[0]; });
  T_ok(sends[0]._text === "Send this card to Dido", "D4 per-card send CTA", sends[0]._text);
  T_ok(T_byText(pcards[0], "TEXTAREA", "").length === 0, "D5 no share textarea clutter on cards");
  var nC = T_tracked("share_created").length;
  T_click(sends[0]);
  var st = T_byClass(pcards[0], "status");
  var stText = st.length ? st[st.length - 1]._text : "";
  T_ok(stText.indexOf("Copied") === 0, "D6 send copies share text", stText);
  T_ok(T_tracked("share_created").length === nC + 1, "D7 share_created tracked for personal card");
  var created = (Analytics._q || []).filter(function(e){ return e[0] === "share_created"; }).pop();
  T_ok(created && created[1].idea_id === "blue-dog-family", "D8 share_created carries idea_id");
  /* share-sheet branch: with navigator.share present, the CTA really sends */
  var T_shareArgs = null;
  navigator.share = function(opts){ T_shareArgs = opts; return { then: function(ok){ ok(); } }; };
  var nC2 = T_tracked("share_created").length;
  T_click(sends[0]);
  T_ok(!!T_shareArgs && T_shareArgs.text.indexOf("Dido is going as Aussie Dog Family") >= 0,
    "D12 native share sheet used when available", T_shareArgs && T_shareArgs.text);
  var stAfter = T_byClass(pcards[0], "status");
  var stText2 = stAfter.length ? stAfter[stAfter.length - 1]._text : "";
  T_ok(stText2 === "Shared.", "D13 status says Shared after share sheet", stText2);
  var created2 = (Analytics._q || []).filter(function(e){ return e[0] === "share_created"; }).pop();
  T_ok(T_tracked("share_created").length === nC2 + 1 && created2 && created2[1].via === "share_sheet",
    "D14 share_created carries via=share_sheet");
  delete navigator.share; /* restore: the clipboard fallback is the default */
  /* one blank name: no "Person 2" fallback card */
  T_clearInp(inputs[1]);
  /* Billy 2026-09-24: every cast member gets a card now; the unnamed card's
     send button reads plain "Send this card", never "Person 2" */
  T_click(makeBtn);
  var pcards2 = T_byClass(panel, "pcard");
  T_ok(pcards2.length === 2, "D15 blank name still gets a card (one per member)", pcards2.length);
  T_ok(T_byClass(pcards2[0], "pcard-head")[0]._text === "Dido is going as Aussie Dog Family", "D16 named card keeps its real name");
  var unnamedSend = T_byText(pcards2[1], "BUTTON", "Send this card")[0];
  T_ok(unnamedSend && unnamedSend._text === "Send this card", "D17 unnamed card send reads 'Send this card'", unnamedSend && unnamedSend._text);
  var noFallback = T_findAll(panel, function(e){ return e.tagName === "BUTTON" && (e._text || "").indexOf("Person ") >= 0; });
  T_ok(noFallback.length === 0, "D18 no send button says 'Person N'", noFallback.length);
})();

/* ---------- scenario E: browse parity + sticky bar ---------- */
console.log("E. browse parity + sticky filters");
(function(){
  /* static: sticky wrapper exists in the HTML and CSS */
  T_ok(src.indexOf('<div class="bsticky">') >= 0, "E1 bfilters wrapped in .bsticky");
  T_ok(src.indexOf(".bsticky{position:sticky") >= 0, "E2 .bsticky is position:sticky");
  openBrowse();
  var grid = $("b-grid");
  T_ok(grid.children.length > 40, "E3 browse grid renders the ideas", grid.children.length);
  var first = grid.children[0];
  T_ok((first.className || "").split(/\s+/).indexOf("bcard") >= 0, "E4 browse cards present");
  /* real bubbling tap on the card body (not a button) opens the full detail */
  var body = T_findAll(first, function(e){ return e.tagName === "H3"; })[0] || first;
  T_click(body);
  T_ok(T_tracked("browse_detail_opened").length >= 1, "E5 browse card body opens detail");
  var dCard = T_byClass($("d-card"), "card")[0] || T_byClass($("s-detail"), "card")[0];
  T_ok(!!dCard, "E6 detail card rendered");
  if (dCard){
    T_ok(T_byText(dCard, "BUTTON", "This is my pick").length === 1, "E7 detail has pick CTA");
    T_ok(T_byText(dCard, "BUTTON", "Share this idea").length === 1, "E8 detail has share CTA");
    /* full flow: pick -> AI prompt appears */
    T_click(T_byText(dCard, "BUTTON", "This is my pick")[0]);
    T_ok(T_findAll(dCard, function(e){ return e.tagName === "TEXTAREA"; }).length >= 1, "E9 AI prompt textarea appears after pick");
  }
})();

/* ---------- scenario F: quiz never exceeds 5 questions ---------- */
console.log("F. five-question maximum");
(function(){
  var qs = ["My kid","My family","Solo","Couple","Group"];
  var lens = qs.map(function(label){
    state = { qi: 0, answers: { q1: T_O("q1", label) } };
    return flowOrder();
  });
  var max = Math.max.apply(null, lens.map(function(o){ return o.length; }));
  T_ok(max <= 5, "F1 flowOrder never exceeds 5", lens.map(function(o){return o.length;}).join(","));
  state = { qi: 0, answers: { q1: T_O("q1","My kid") } };
  var kidFlow = flowOrder();
  T_ok(kidFlow.length <= 5 && kidFlow.indexOf("qfit") < 0, "F2 kid flow has no qfit", kidFlow.join(","));
  state = { qi: 0, answers: { q1: T_O("q1","Solo") } };
  var soloFlow = flowOrder();
  T_ok(soloFlow.length === 5 && soloFlow.indexOf("qfit") < 0, "F3 solo flow is exactly 5, no qfit", soloFlow.join(","));
})();

/* ---------- scenario G: E27 complete-the-cast ---------- */
console.log("G. complete-the-cast");
(function(){
  if (typeof castShareParam !== "function"){
    console.log("  (E27 not present in this build; skipping)");
    return;
  }
  var idea = IDEAS.filter(function(i){ return i.id === "blue-dog-family"; })[0];
  T_ok(!!idea, "G0 blue-dog-family found");

  /* sender: the cast rides on the share URL for multi-person named casts */
  var list = [
    {name: "Dido", rawName: "Dido", kid: false, role: "Mama dog"},
    {name: "Billy", rawName: "Billy", kid: false, role: "Dad dog"},
    {name: "Capri", rawName: "Capri", kid: true, role: "little pup"}
  ];
  var txt = buildCastShareText(idea, list, "sid00001");
  T_ok(txt.indexOf("&cast=") > 0, "G1 cast param appended to multi-person share", txt.slice(-48));
  var enc = /[?&]cast=([A-Za-z0-9\-_]+)/.exec(txt)[1];
  var back = parseCastParam(enc);
  T_ok(back && back.length === 3 && back[0].n === "Dido" && back[1].r === "Dad dog",
    "G2 cast param round-trips name+role", JSON.stringify(back));

  /* solo shares are byte-identical: no cast param */
  var soloIdea = IDEAS.filter(function(i){ return i.id === "tin-hero"; })[0];
  var soloTxt = buildCastShareText(soloIdea, [{name: "Billy", rawName: "Billy", kid: false, role: "The Tin Hero"}], "sid00002");
  T_ok(soloTxt.indexOf("&cast=") < 0 && soloTxt.indexOf("?s=sid00002") > 0,
    "G3 solo share has no cast param", soloTxt);

  /* unnamed multi-person share: no cast param */
  var blankList = [
    {name: "Person 1", rawName: "", kid: false, role: "Mama dog"},
    {name: "Person 2", rawName: "", kid: false, role: "Dad dog"}
  ];
  T_ok(buildCastShareText(idea, blankList, "sid00003").indexOf("&cast=") < 0,
    "G4 unnamed cast has no cast param");

  /* recipient landing: cast panel renders above the landing card */
  var hero = $("s-hero");
  global.location.search = "?idea=blue-dog-family&s=shr00001&cast=" + enc;
  VIA_SHARE = "shr00001";
  renderSharedLanding();
  var castBoxes = T_byClass(hero, "e27cast");
  T_ok(castBoxes.length >= 1, "G5 cast panel rendered on landing", castBoxes.length);
  var cbox = castBoxes[castBoxes.length - 1];
  /* element identity: the cast panel is a direct child of the hero, positioned
     above the landing card created in the same render */
  var heroKids = hero.children;
  var cboxIdx = heroKids.indexOf(cbox);
  var sibCards = heroKids.filter(function(k, i){ return i > cboxIdx && (k.className || "").split(/\s+/).indexOf("card") >= 0; });
  T_ok(cboxIdx >= 0 && sibCards.length >= 1,
    "G6 cast panel is above the landing card", "cboxIdx=" + cboxIdx);
  var lis = T_findAll(cbox, function(e){ return e.tagName === "LI"; });
  T_ok(lis.length === 3 && lis[0]._text === "Dido is the Mama dog",
    "G7 cast-so-far lists name + role", lis.map(function(l){ return l._text; }).join(" | "));
  var clv = T_tracked("cast_landing_viewed").pop();
  T_ok(clv && clv[1].cast_size === 3 && clv[1].share_id === "shr00001",
    "G8 cast_landing_viewed {share_id, cast_size}", JSON.stringify(clv && clv[1]));

  /* claim-button tap hits the claim handler: assert WHICH button was hit */
  var claimBtns = T_findAll(cbox, function(e){ return e.tagName === "BUTTON" && e.getAttribute("data-claim") === "Billy"; });
  T_ok(claimBtns.length === 1, "G9 claim button found for Billy (data-claim marker)");
  var nRc0 = T_tracked("role_claimed").length;
  T_click(claimBtns[0]); /* real bubbling click on Billy's button, not Dido's */
  var rc = T_tracked("role_claimed").pop();
  T_ok(T_tracked("role_claimed").length === nRc0 + 1 && rc && rc[1].role === "Dad dog" && rc[1].share_id === "shr00001",
    "G10 role_claimed {share_id, role} for the tapped name", JSON.stringify(rc && rc[1]));
  var youreIn = T_findAll(cbox, function(e){ return (e.className || "").split(/\s+/).indexOf("e27yourein") >= 0; });
  T_ok(youreIn.length === 1 && youreIn[0]._text === "You\u2019re in as Dad dog!",
    "G11 confirmation names the claimed role", youreIn[0] && youreIn[0]._text);
  var tellBtns = T_findAll(cbox, function(e){ return (e.className || "").split(/\s+/).indexOf("e27tell") >= 0; });
  T_ok(tellBtns.length === 1 && tellBtns[0]._text === "Tell the group", "G12 Tell the group CTA revealed");

  /* share-sheet branch: text shape, link params, event, status */
  var T_shareArgs = null;
  navigator.share = function(opts){ T_shareArgs = opts; return { then: function(ok){ ok(); } }; };
  var nRs0 = T_tracked("cast_reshare_created").length;
  T_click(tellBtns[0]);
  T_ok(!!T_shareArgs && T_shareArgs.text.indexOf("I\u2019m in as Dad dog!") === 0,
    "G13 reshare text leads with the claim", T_shareArgs && T_shareArgs.text.slice(0, 56));
  var linkM = /https:\/\/pickmycostume\.com\/c\/blue-dog-family\?s=([a-z0-9]+)&cast=([A-Za-z0-9\-_]+)&claimed=([^ ]+)/.exec(T_shareArgs.text);
  var claimedArr = null;
  try { claimedArr = JSON.parse(b64urlDecode(linkM[3])); } catch(e){ claimedArr = null; }
  T_ok(!!linkM && linkM[2] === enc && claimedArr && claimedArr.length === 1 && claimedArr[0] === "Billy",
    "G14 reshare link carries cast + claimed=[Billy]", linkM && linkM[3]);
  /* Regression: a comma inside a name must survive the claimed round-trip
     (the old comma-joined format corrupted these). Uses the page's own codec. */
  var commaRt = null;
  try { commaRt = JSON.parse(b64urlDecode(b64urlEncode(JSON.stringify(["Billy, Jr"])))); } catch(e){ commaRt = null; }
  T_ok(commaRt && commaRt.length === 1 && commaRt[0] === "Billy, Jr",
    "G14b comma in a name survives the claimed round-trip", JSON.stringify(commaRt));
  T_ok(T_shareArgs.text.indexOf("Dido, Capri, who\u2019s next?") > 0,
    "G15 reshare names the others", T_shareArgs && T_shareArgs.text.slice(0, 120));
  var rs = T_tracked("cast_reshare_created").pop();
  T_ok(T_tracked("cast_reshare_created").length === nRs0 + 1 && rs && rs[1].via === "share_sheet" && rs[1].via_share_id === "shr00001",
    "G16 cast_reshare_created {share_id, via, via_share_id}", JSON.stringify(rs && rs[1]));
  var stTxt = T_findAll(cbox, function(e){ return (e.className || "").split(/\s+/).indexOf("status") >= 0; }).map(function(e){ return e._text; });
  T_ok(stTxt.indexOf("Shared.") >= 0, "G17 status names the share-sheet outcome");
  delete navigator.share;

  /* clipboard fallback branch */
  global.location.search = "?idea=blue-dog-family&s=shr00002&cast=" + enc;
  VIA_SHARE = "shr00002";
  renderSharedLanding();
  /* newest render inserts at the front: [0] is this render's panel */
  var cbox2 = T_byClass($("s-hero"), "e27cast")[0];
  var claim2 = T_findAll(cbox2, function(e){ return e.tagName === "BUTTON" && e.getAttribute("data-claim") === "Capri"; })[0];
  T_click(claim2);
  var tell2 = T_findAll(cbox2, function(e){ return (e.className || "").split(/\s+/).indexOf("e27tell") >= 0; })[0];
  var nRs1 = T_tracked("cast_reshare_created").length;
  T_click(tell2);
  var rs2 = T_tracked("cast_reshare_created").pop();
  T_ok(T_tracked("cast_reshare_created").length === nRs1 + 1 && rs2 && rs2[1].via === "clipboard",
    "G18 clipboard fallback fires cast_reshare_created via=clipboard", JSON.stringify(rs2 && rs2[1]));
  var st2 = T_findAll(cbox2, function(e){ return (e.className || "").split(/\s+/).indexOf("status") >= 0; }).map(function(e){ return e._text; });
  T_ok(st2.indexOf("Copied. Paste it into any message.") >= 0, "G19 fallback status names clipboard");

  /* taps inside the cast panel never bubble to a parent (card) handler */
  var bubbled = 0;
  $("s-hero").addEventListener("click", function(){ bubbled++; });
  T_click(cbox2); /* bubbling click on the panel root itself, not a button */
  T_ok(bubbled === 0, "G20 cast panel stops click propagation at its root", "bubbled=" + bubbled);

  /* zero behavior change: no ?cast= means no cast panel */
  var nCast0 = T_byClass($("s-hero"), "e27cast").length;
  global.location.search = "?idea=blue-dog-family&s=shr00003";
  VIA_SHARE = "shr00003";
  renderSharedLanding();
  T_ok(T_byClass($("s-hero"), "e27cast").length === nCast0, "G21 no cast panel without ?cast=");

  /* garbage ?cast= is ignored: old flow intact */
  global.location.search = "?idea=blue-dog-family&s=shr00004&cast=bm90anNvbg"; /* b64url("notjson") */
  VIA_SHARE = "shr00004";
  renderSharedLanding();
  T_ok(T_byClass($("s-hero"), "e27cast").length === nCast0, "G22 garbage cast param ignored");

  global.location.search = "";
  VIA_SHARE = null;
})();

/* ---------- scenario H: post-pick reorder + AI plan reveal ---------- */
console.log("H. post-pick reorder + AI plan reveal");
(function(){
  T_clearLS();
  for (var k in castStateByIdea) delete castStateByIdea[k];
  for (var k2 in panelOpenByIdea) delete panelOpenByIdea[k2];
  state = { qi: 0, answers: {} };
  state.answers = { q1: T_O("q1","My family"), q2: T_O("q2","Funny"), q4: T_O("q4","Couch-level"),
    qocc: T_O("qocc","Trick-or-treating"),
    qinterest: qById("qinterest").options.filter(function(o){ return o.tags.animals; })[0] };
  renderResults(scoreIdeas());
  var card = T_byClass(T_byClass($("r-cards"), "hero12")[0], "card")[0];
  T_click(T_byText(card, "BUTTON", "This is my pick")[0]);
  var panel = T_byClass(card, "castbox")[0];
  /* section order: personal cards, then share box, then AI plan (Billy 2026-09-24:
     one flow -- the share comes after the personal card) */
  var shareBtn = T_byText(panel, "BUTTON", "Share this idea")[0];
  var makeBtn = T_byText(panel, "BUTTON", "Make personal cards")[0];
  var copyBtn = T_byText(panel, "BUTTON", "Copy AI prompt")[0];
  function topLevel(el){ while (el && el.parentNode && el.parentNode !== panel) el = el.parentNode; return el; }
  var shareBox = topLevel(shareBtn), pcWrap = topLevel(makeBtn), aiBox = topLevel(copyBtn);
  var order = panel.children;
  T_ok(!!(shareBox && pcWrap && aiBox), "H0 share/cards/AI sections present");
  T_ok(order.indexOf(pcWrap) >= 0 && order.indexOf(pcWrap) < order.indexOf(shareBox), "H1 personal cards come before the share box");
  T_ok(order.indexOf(shareBox) >= 0 && order.indexOf(shareBox) < order.indexOf(aiBox), "H2 share box comes before the AI plan");
  /* successful "Share this idea" reveals the AI plan (highlight class) */
  delete navigator.share; /* clipboard fallback branch */
  T_click(shareBtn);
  T_ok(aiBox.classList.contains("ai-flash"), "H3 AI plan highlighted after successful share");
  /* card send success reveals the AI plan too, share_created via=clipboard intact */
  var rows = T_byClass(panel, "castrow");
  var inputs = rows.map(function(r){ return T_byClass(r, "castname")[0].children[1]; });
  T_type(inputs[0], "Dido"); T_type(inputs[1], "Billy");
  T_click(makeBtn);
  var sends = T_byText(panel, "BUTTON", "Send this card to ");
  T_ok(sends.length >= 1 && sends[0]._text === "Send this card to Dido", "H4 card send CTA names the person", sends[0] && sends[0]._text);
  var nC = T_tracked("share_created").length;
  T_click(sends[0]);
  T_ok(T_tracked("share_created").length === nC + 1, "H5 share_created tracked for card send");
  var created = (Analytics._q || []).filter(function(e){ return e[0] === "share_created"; }).pop();
  T_ok(created && created[1].via === "clipboard", "H6 share_created carries via=clipboard", JSON.stringify(created && created[1]));
  T_ok(aiBox.classList.contains("ai-flash"), "H7 AI plan highlighted after card send");
  /* share-sheet branch: the AI plan is revealed there too */
  var T_shareArgs = null;
  navigator.share = function(opts){ T_shareArgs = opts; return { then: function(ok){ ok(); } }; };
  T_click(sends[0]);
  var created2 = (Analytics._q || []).filter(function(e){ return e[0] === "share_created"; }).pop();
  T_ok(!!T_shareArgs && created2 && created2[1].via === "share_sheet", "H8 share-sheet branch carries via=share_sheet");
  T_ok(aiBox.classList.contains("ai-flash"), "H9 AI plan highlighted after share-sheet send");
  delete navigator.share;
  /* propagation guard: typing + clicking inside the panel still never re-picks */
  var nSaved = T_tracked("pick_saved").length;
  T_click(inputs[0]); /* bubbling click on a name input, not a button */
  T_ok(T_tracked("pick_saved").length === nSaved, "H10 panel input click does not re-pick");
})();

console.log("\n==== e26-ship-test: " + T_pass + " passed, " + T_fail + " failed ====");
if (T_fail) process.exit(1);
})();
