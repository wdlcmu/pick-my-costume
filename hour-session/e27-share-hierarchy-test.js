/* E27 ship QA: Billy 2026-09-24 share-hierarchy production push.
   Usage: node hour-session/e27-share-hierarchy-test.js
   Evals the REAL main script from index.html against a fake DOM with real event
   semantics (bubbling, focus/blur, stopPropagation, closest), then drives:
     P1. cast panel: personal-cards section ABOVE the generic share; generic
         "Share this idea" is ghost (quiet), not cta -- and asserts WHICH
         element (the one inside .castbox)
     P2. solo idea: generic "Share this idea" keeps the orange cta primary
     P3. send wording: named -> "Send this card to {name}"; unnamed ->
         "Send this card"; never "Person N"
     P4. names copy: Billy's exact wording; old "stay on this phone" gone
     P5. propagation guard intact: panel input clicks never re-pick
     P6. send still copies + tracks share_created (no behavior loss)
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


/* doc-order index for "A above B" assertions */
function T_order(root){
  var idx = {}, n = 0;
  (function walk(e){ idx[e._uid = (e._uid || ("u"+(++n)))] = n; (e.children||[]).forEach(walk); })(root);
  return idx;
}
function T_posOf(orderMap, el){ return orderMap[el._uid]; }

/* ---------- scenario P1: cast panel hierarchy ---------- */
console.log("P1. cast panel: cards above generic share, generic share is ghost");
(function(){
  T_clearLS();
  for (var k in castStateByIdea) delete castStateByIdea[k];
  for (var k2 in panelOpenByIdea) delete panelOpenByIdea[k2];
  state = { qi: 0, answers: {} };
  state.answers = { q1: T_O("q1","My family"), q2: T_O("q2","Funny"), q4: T_O("q4","Couch-level"),
    qocc: T_O("qocc","Trick-or-treating"),
    qinterest: qById("qinterest").options.filter(function(o){ return o.tags.animals; })[0] };
  var res = scoreIdeas();
  T_ok(res[0].idea.id === "blue-dog-family", "P1.1 family/animals hero is blue-dog-family", res[0].idea.id);
  renderResults(res);
  var card = T_byClass(T_byClass($("r-cards"), "hero12")[0], "card")[0];
  T_click(T_byText(card, "BUTTON", "This is my pick")[0]);
  var panel = T_byClass(card, "castbox")[0];
  T_ok(!!panel, "P1.2 cast panel mounted");
  var order = T_order(panel);
  var pcards = T_byClass(panel, "pcards")[0];
  T_ok(!!pcards, "P1.3 personal-cards section present");
  /* WHICH share button: the one inside this cast panel */
  var shareBtn = T_byText(panel, "BUTTON", "Share this idea")[0];
  T_ok(!!shareBtn, "P1.4 generic share button present in cast panel");
  T_ok(shareBtn.closest(".castbox") === panel, "P1.5 WHICH element: share btn is inside THIS castbox", "");
  T_ok(T_posOf(order, pcards) < T_posOf(order, shareBtn), "P1.6 personal cards ABOVE generic share in DOM order");
  T_ok(shareBtn.className.split(/\s+/).indexOf("ghost") >= 0, "P1.7 generic share is ghost (quiet)", shareBtn.className);
  T_ok(shareBtn.className.split(/\s+/).indexOf("cta") < 0, "P1.8 generic share is NOT cta", shareBtn.className);
  var makeBtn = T_byText(panel, "BUTTON", "Make personal cards")[0];
  T_ok(T_posOf(order, makeBtn) < T_posOf(order, shareBtn), "P1.9 Make-personal-cards above generic share too");
})();

/* ---------- scenario P2: solo keeps the orange primary ---------- */
console.log("P2. solo idea: generic share stays cta");
(function(){
  T_clearLS();
  for (var k in castStateByIdea) delete castStateByIdea[k];
  for (var k2 in panelOpenByIdea) delete panelOpenByIdea[k2];
  state = { qi: 0, answers: {} };
  state.answers = { q1: T_O("q1","Solo"), q2: T_O("q2","Scary"), q4: T_O("q4","Go all out"),
    qocc: T_O("qocc","Bar / club night"),
    qinterest: qById("qinterest").options.filter(function(o){ return o.tags.tv; })[0] };
  var res = scoreIdeas();
  T_ok(res[0].idea.id === "neon-demon-hunter" && !CASTS[res[0].idea.id], "P2.1 solo hero is neon-demon-hunter (no cast)", res[0].idea.id);
  renderResults(res);
  var card = T_byClass(T_byClass($("r-cards"), "hero12")[0], "card")[0];
  T_click(T_byText(card, "BUTTON", "This is my pick")[0]);
  T_ok(T_byClass(card, "castbox").length === 0, "P2.2 no cast panel for solo idea");
  var shareBtn = T_byText(card, "BUTTON", "Share this idea")[0];
  T_ok(!!shareBtn, "P2.3 solo share button present");
  T_ok(shareBtn.className.split(/\s+/).indexOf("cta") >= 0, "P2.4 WHICH element: SOLO share btn keeps cta primary", shareBtn.className);
})();

/* ---------- scenario P3: send-button wording ---------- */
console.log("P3. send wording: named vs unnamed");
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
  T_type(inputs[0], "Dido"); /* second person left blank on purpose */
  T_click(T_byText(panel, "BUTTON", "Make personal cards")[0]);
  var pcards = T_byClass(panel, "pcard");
  T_ok(pcards.length === 2, "P3.1 one card per cast member (named or not)", pcards.length);
  var sends = pcards.map(function(c){ return T_byText(c, "BUTTON", "Send this card")[0]; });
  T_ok(sends[0]._text === "Send this card to Dido", "P3.2 named: 'Send this card to Dido'", sends[0]._text);
  T_ok(sends[1]._text === "Send this card", "P3.3 WHICH element: 2nd card (unnamed) send = plain 'Send this card'", sends[1]._text);
  var personN = T_findAll(panel, function(e){ return e.tagName === "BUTTON" && (e._text || "").indexOf("Person ") >= 0; });
  T_ok(personN.length === 0, "P3.4 no send button ever says 'Person N'", personN.length);
  T_ok(sends[0].className.split(/\s+/).indexOf("cta") >= 0, "P3.5 send buttons keep orange cta emphasis", sends[0].className);
})();

/* ---------- scenario P4: names copy ---------- */
console.log("P4. names copy");
(function(){
  var want = "Names are optional and never stored anywhere. I never see them.";
  /* idRegistry elements are not parented under document.body in the fake DOM;
     scan every created element instead */
  var hits = allElements.filter(function(e){ return (e._text || "").indexOf(want) >= 0; });
  T_ok(hits.length >= 1, "P4.1 Billy's names wording present", hits.length);
  var old = allElements.filter(function(e){ return (e._text || "").indexOf("stay on this phone") >= 0; });
  T_ok(old.length === 0, "P4.2 old 'stay on this phone' copy gone", old.length);
})();

/* ---------- scenario P5+P6: guard intact, send still works ---------- */
console.log("P5/P6. propagation guard + send behavior preserved");
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
  var nSaved = T_tracked("pick_saved").length;
  var inp = T_byClass(T_byClass(panel, "castrow")[0], "castname")[0].children[1];
  T_click(inp); /* bubbling click on a name input */
  T_ok(T_tracked("pick_saved").length === nSaved, "P5.1 panel input click does not re-pick");
  T_type(inp, "Dido");
  T_click(T_byText(panel, "BUTTON", "Make personal cards")[0]);
  var send = T_byText(T_byClass(panel, "pcard")[0], "BUTTON", "Send this card to Dido")[0];
  var nC = T_tracked("share_created").length;
  T_click(send);
  T_ok(T_tracked("share_created").length === nC + 1, "P6.1 card send still tracks share_created");
  var st = T_byClass(T_byClass(panel, "pcard")[0], "status");
  var stText = st.length ? st[st.length - 1]._text : "";
  T_ok(stText.indexOf("Copied") === 0, "P6.2 clipboard fallback still works", stText);
})();

/* ---------- scenario P7: AI plan copy (Billy 2026-09-24) ---------- */
console.log("P7. AI plan copy");
(function(){
  T_clearLS();
  for (var k in castStateByIdea) delete castStateByIdea[k];
  for (var k2 in panelOpenByIdea) delete panelOpenByIdea[k2];
  state = { qi: 0, answers: {} };
  state.answers = { q1: T_O("q1","Solo"), q2: T_O("q2","Scary"), q4: T_O("q4","Go all out"),
    qocc: T_O("qocc","Bar / club night"),
    qinterest: qById("qinterest").options.filter(function(o){ return o.tags.tv; })[0] };
  renderResults(scoreIdeas());
  var card = T_byClass(T_byClass($("r-cards"), "hero12")[0], "card")[0];
  T_click(T_byText(card, "BUTTON", "This is my pick")[0]);
  var header = T_byText(card, "P", "Plan my costume")[0];
  T_ok(!!header, "P7.1 'Plan my costume' header present");
  var helper = T_byText(card, "P", "Paste it into any AI for a step-by-step plan")[0];
  T_ok(!!helper, "P7.2 helper text present");
  T_ok(!!T_byText(card, "BUTTON", "Copy AI prompt")[0], "P7.3 'Copy AI prompt' button unchanged");
  var old = T_findAll(card, function(e){ return (e._text || "").indexOf("Get your AI costume plan") >= 0; });
  T_ok(old.length === 0, "P7.4 old header gone", old.length);
})();

console.log("\n==== e27-share-hierarchy-test: " + T_pass + " passed, " + T_fail + " failed ====");
if (T_fail) process.exit(1);

})();
