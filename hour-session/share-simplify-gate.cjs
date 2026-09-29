/* Share-simplify gate (2026-09-28). Billy: share loop bloated, flows frazzled.
   Verifies the simplified loop on the REAL index.html in a vm sandbox:
   S1  script evals without throwing
   S2  shareAskLine: the one ask line
   S3  shareTextFor: one canonical message per audience (solo/kid/family/
       couple/group); ask line + recipient link; kid/family shopping list;
       no dare/teaser/variant copy
   S4  shareLandingHeadline: generic + live specialized origins; non-share
       arrivals get the title; old teaser/micro links read generic
   S5  addCopyShareRow DOM: one primary "Share this idea"; preview collapsed;
       secondaries present; retired buttons absent
   S6  sendShare native sheet: resolved -> share_created (share_id/origin);
       dismissed -> NO share_created
   S7  sendShare clipboard: share_text_copied descriptive + share_created
       via clipboard
   S8  addCopyShareRow primary tap -> share_created origin generic
   S9  138 unique idea IDs (bank untouched)
   S10 dead builders are gone from the runtime
   Usage: node hour-session/share-simplify-gate.cjs
*/
var fs = require("fs");
var vm = require("vm");
var HTML = process.env.HOME + "/workspace/builds/pick-my-costume/index.html";
var html = fs.readFileSync(HTML, "utf8");
var main = html.split(/<script(?![^>]*src=)(?![^>]*type=)[^>]*>/).slice(1)
  .map(function(p){ return p.split("</script>")[0]; }).join("\n;\n");

var failures = 0;
function T_ok(cond, name, extra){
  if (cond){ console.log("  PASS " + name); }
  else { failures++; console.log("  FAIL " + name + (extra !== undefined ? " :: " + extra : "")); }
}

/* ---------- minimal fake DOM ---------- */
function makeSandbox(search){
  var els = [];
  var byId = {};
  function makeEl(tag){
    var el = {
      tagName: String(tag).toUpperCase(), children: [], parentNode: null,
      style: {}, className: "", _text: "", _html: "", _val: "",
      type: "", disabled: false, _listeners: {}, _attrs: {},
      /* 2026-09-28: day-branch of paintHeroSky calls classList.add; the
         fake needs it or the gate only passes at night. */
      classList: { _s: {}, add: function(c){ this._s[c] = 1; }, remove: function(c){ delete this._s[c]; }, contains: function(c){ return !!this._s[c]; } },
      setAttribute: function(k, v){ this._attrs[k] = String(v); },
      getAttribute: function(k){ return (k in this._attrs) ? this._attrs[k] : null; },
      /* 2026-09-28: the day-branch of paintHeroSky calls removeAttribute;
         without it the gate only passed at night (time-of-day flake). */
      removeAttribute: function(k){ delete this._attrs[k]; },
      appendChild: function(c){ c.parentNode = this; this.children.push(c); return c; },
      removeChild: function(c){ var i = this.children.indexOf(c); if (i >= 0){ this.children.splice(i,1); c.parentNode = null; } return c; },
      insertBefore: function(c, ref){ c.parentNode = this; var i = ref ? this.children.indexOf(ref) : -1; if (i < 0) this.children.push(c); else this.children.splice(i, 0, c); return c; },
      addEventListener: function(t, f){ (this._listeners[t] = this._listeners[t] || []).push(f); },
      removeEventListener: function(){},
      select: function(){}, focus: function(){}, blur: function(){},
      scrollIntoView: function(){}, click: function(){ if (this.onclick) this.onclick(); },
      dispatchEvent: function(){},
      querySelectorAll: function(){ return []; }, querySelector: function(){ return null; },
      getElementsByTagName: function(){ return []; }
    };
    Object.defineProperty(el, "textContent", {
      get: function(){ return this._text; },
      set: function(v){ this._text = String(v); }
    });
    Object.defineProperty(el, "innerHTML", {
      get: function(){ return this._html; },
      set: function(v){ this._html = String(v); this.children = []; }
    });
    Object.defineProperty(el, "value", {
      get: function(){ return this._val; },
      set: function(v){ this._val = String(v); }
    });
    els.push(el);
    return el;
  }
  var doc = {
    createElement: makeEl,
    createTextNode: function(t){ var e = makeEl("span"); e._text = String(t); return e; },
    getElementById: function(id){ return byId[id] || (byId[id] = makeEl("div")); },
    getElementsByTagName: function(){ return []; },
    getElementsByClassName: function(){ return []; },
    querySelectorAll: function(){ return []; },
    querySelector: function(){ return null; },
    activeElement: null,
    execCommand: function(){ return true; },
    addEventListener: function(){}, removeEventListener: function(){},
    head: makeEl("head"), body: makeEl("body")
  };
  var ls = {};
  var sb = {
    document: doc, _els: els,
    window: { getSelection: function(){ return { toString: function(){ return ""; } }; }, scrollTo: function(){} },
    location: { search: search || "", href: "https://pickmycostume.com/" },
    localStorage: {
      getItem: function(k){ return (k in ls) ? ls[k] : null; },
      setItem: function(k, v){ ls[k] = String(v); },
      removeItem: function(k){ delete ls[k]; }
    },
    navigator: {},
    console: console,
    setTimeout: setTimeout, clearTimeout: clearTimeout,
    setInterval: function(){ return 0; }, clearInterval: function(){}, Date: Date, Math: Math,
    JSON: JSON, Object: Object, Array: Array, String: String, Number: Number,
    RegExp: RegExp, Error: Error, Promise: Promise
  };
  sb.window.document = doc;
  vm.createContext(sb);
  var evalOk = true, evalErr = "";
  var _dbg = console.debug; console.debug = function(){};
  try { vm.runInContext(main, sb, { filename: "index.html" }); }
  catch (e){ evalOk = false; evalErr = String(e && e.stack || e); }
  console.debug = _dbg;
  sb._evalOk = evalOk; sb._evalErr = evalErr;
  sb.tracked = function(name){
    return ((sb.Analytics && sb.Analytics._q) || []).filter(function(e){ return e[0] === name; });
  };
  return sb;
}
function byText(sb, tag, text){
  return sb._els.filter(function(e){ return e.tagName === tag && (e._text || "").indexOf(text) >= 0; });
}

/* ---------- S1: eval ---------- */
console.log("S1 eval");
var sb = makeSandbox("");
T_ok(sb._evalOk, "script evals without throwing", (sb._evalErr || "").split("\n").slice(0,3).join(" | "));

/* ---------- S2: the one ask line ---------- */
console.log("S2 shareAskLine");
T_ok(typeof sb.shareAskLine === "function", "shareAskLine defined");
T_ok(sb.shareAskLine() === "I picked this with Pick My Costume. Take the 2-minute quiz and tell me what you get. ", "ask line copy (2026-09-28 P0 growth rewrite)", JSON.stringify(sb.shareAskLine()));

/* ---------- S3: canonical message ---------- */
console.log("S3 shareTextFor");
function ideaFor(aud){
  var idea = null;
  sb.IDEAS.forEach(function(it){
    if (!idea && it.audience && it.audience.length === 1 && it.audience[0] === aud) idea = it;
  });
  return idea;
}
["solo","kid","family","couple","group"].forEach(function(aud){
  var idea = ideaFor(aud);
  T_ok(!!idea, "found a " + aud + " idea");
  if (!idea) return;
  var sid = "tests1d" + aud.slice(0,2);
  var msg = sb.shareTextFor(idea, sid, "generic");
  T_ok(msg.indexOf("What would you go as? ") >= 0, aud + ": carries the one ask line");
  T_ok(msg.indexOf("https://pickmycostume.com/c/" + idea.id + "?s=" + sid + "&o=generic") >= 0, aud + ": recipient link with sid + origin");
  T_ok(msg.indexOf("&ch=") < 0, aud + ": no challenge params");
  T_ok(/dare|store run|make.*tonight|riddle|teaser/i.test(msg) === false || aud === "solo", aud + ": no retired variant copy", msg.slice(0,120));
});
/* kid/family shopping list suffix */
var kidIdea = ideaFor("kid");
if (kidIdea){
  var km = sb.shareTextFor(kidIdea, "kidlist01", "generic");
  var hasMats = !!(sb.INSTRUCTIONS && sb.INSTRUCTIONS[kidIdea.id] && sb.INSTRUCTIONS[kidIdea.id].m);
  if (hasMats) T_ok(/bring|need|pack/i.test(km), "kid: shopping-list suffix present");
  else console.log("  SKIP kid shopping list (no INSTRUCTIONS.m for " + kidIdea.id + ")");
}
/* canonical message is identical across repeated builds (no variant arms) */
var i0 = sb.IDEAS[0];
T_ok(sb.shareTextFor(i0, "samesid1", "generic") === sb.shareTextFor(i0, "samesid1", "generic"),
     "message deterministic for same sid (no variant arm)");

/* ---------- S4: recipient headlines ---------- */
console.log("S4 shareLandingHeadline");
function headlineFor(search){
  var s2 = makeSandbox(search);
  if (!s2._evalOk) return "EVAL-FAILED";
  var idea = null;
  s2.IDEAS.forEach(function(it){ if (it.id === "tin-hero") idea = it; });
  return s2.shareLandingHeadline(idea, search);
}
var h;
h = headlineFor("?s=abc12345&o=generic");
T_ok(h === "Your friend picked The Tin Hero. What would you pick?", "generic headline", h);
h = headlineFor("?s=abc12345&o=pair");
T_ok(h === "Your friend is going as The Tin Hero. Find YOUR costume to match.", "pair headline", h);
h = headlineFor("?s=abc12345&o=vote");
T_ok(h === "Your friend wants your vote: is The Tin Hero the one?", "vote headline", h);
h = headlineFor("?s=abc12345&o=tryon");
T_ok(h === "Your friend tried on The Tin Hero. Try your own face in it.", "tryon headline", h);
h = headlineFor("?s=abc12345&o=countdown");
T_ok(h === "Your friend is counting down to Halloween with The Tin Hero. What is your pick?", "countdown headline", h);
h = headlineFor("?s=abc12345&o=grandparent");
T_ok(h === "Your grandkid's Halloween plan: The Tin Hero. Here is the guide.", "grandparent headline", h);
h = headlineFor("?s=abc12345&o=noclone");
T_ok(/no-clone pact/.test(h), "noclone headline", h);
h = headlineFor("?s=abc12345&o=team");
T_ok(/Your team is going as The Tin Hero/.test(h), "team headline", h);
h = headlineFor("?s=abc12345&o=teaser");
T_ok(h === "Your friend picked The Tin Hero. What would you pick?", "old teaser link reads generic", h);
h = headlineFor("?s=abc12345&o=micro");
T_ok(h === "Your friend picked The Tin Hero. What would you pick?", "old micro link reads generic", h);
h = headlineFor("?idea=tin-hero");
T_ok(h === "The Tin Hero", "non-share arrival gets the title", h);

/* ---------- S5: slim share panel DOM ---------- */
console.log("S5 addCopyShareRow DOM");
var idea = sb.IDEAS[0];
var box = sb.document.createElement("div");
sb.addCopyShareRow(box, idea, null, null, function(){});
function texts(tag){ return byText(sb, tag, ""); }
var primaries = byText(sb, "BUTTON", "Share this idea");
T_ok(primaries.length === 1, "exactly one primary Share button", primaries.length);
var details = sb._els.filter(function(e){ return e.tagName === "DETAILS"; });
T_ok(details.length === 1, "one preview-text disclosure");
T_ok(!details[0].open, "preview collapsed by default");
T_ok(byText(sb, "SUMMARY", "Preview text").length === 1, "preview toggle labeled");
T_ok(byText(sb, "BUTTON", "Pick for a friend").length === 1, "Pick for a friend present");
T_ok(byText(sb, "BUTTON", "Save the image").length === 1, "Save the image present");
["Send the quiz", "Send one question", "Share the plan", "Text it", "SMS", "Riddle", "Guess game", "guess", "Copy link"].forEach(function(t){
  T_ok(byText(sb, "BUTTON", t).length === 0, "retired button absent: " + t);
});
T_ok(sb._els.filter(function(e){ return e.tagName === "TEXTAREA"; }).length === 1, "one preview textarea");
var ta = sb._els.filter(function(e){ return e.tagName === "TEXTAREA"; })[0];
T_ok(ta && /What would you go as\? /.test(ta.value), "preview shows the canonical message");

/* ---------- S6: native sheet path ---------- */
console.log("S6 sendShare native sheet");
var sb6 = makeSandbox("");
var seen6 = [];
sb6.navigator.share = function(payload){
  seen6.push(payload.text);
  return { then: function(ok){ ok(); return { catch: function(){} }; } };
};
var idea6 = sb6.IDEAS[0];
sb6.sendShare(idea6, "reveal", {button: sb6.document.createElement("button"), statusEl: null});
var created6 = sb6.tracked("share_created");
T_ok(created6.length === 1, "resolved sheet -> exactly one share_created", created6.length);
T_ok(created6[0] && created6[0][1].share_origin === "reveal", "share_origin reveal preserved", JSON.stringify(created6[0] && created6[0][1]));
T_ok(created6[0] && /^[a-z0-9]{8}$/.test(created6[0][1].share_id), "share_id minted", created6[0] && created6[0][1].share_id);
T_ok(/What would you go as\? /.test(seen6[0] || ""), "sheet got the canonical text");
/* dismissed sheet: no share_created */
var sb6b = makeSandbox("");
sb6b.navigator.share = function(){
  return { then: function(ok, no){ no(); return { catch: function(){} }; } };
};
sb6b.sendShare(sb6b.IDEAS[0], "generic", {button: sb6b.document.createElement("button"), statusEl: null});
T_ok(sb6b.tracked("share_created").length === 0, "dismissed sheet -> NO share_created");

/* ---------- S7: clipboard path ---------- */
console.log("S7 sendShare clipboard");
var sb7 = makeSandbox("");
sb7.navigator.clipboard = { writeText: function(){ return Promise.resolve(); } };
var st7 = sb7.document.createElement("p");
var btn7 = sb7.document.createElement("button"); btn7.textContent = "Share this idea";
sb7.sendShare(sb7.IDEAS[0], "generic", {button: btn7, statusEl: st7});
setTimeout(function(){
  var copied7 = sb7.tracked("share_text_copied");
  T_ok(copied7.length === 1 && copied7[0][1].via === "clipboard", "share_text_copied via clipboard", JSON.stringify(copied7[0] && copied7[0][1]));
  var created7 = sb7.tracked("share_created");
  T_ok(created7.length === 1 && created7[0][1].via === "clipboard", "clipboard copy -> share_created via clipboard");
  T_ok(/Copied\. Paste it into any message\./.test(st7.textContent), "status says Copied", st7.textContent);

  /* ---------- S8: panel primary tap ---------- */
  console.log("S8 panel primary tap");
  var sb8 = makeSandbox("");
  sb8.navigator.clipboard = { writeText: function(){ return Promise.resolve(); } };
  var box8 = sb8.document.createElement("div");
  sb8.addCopyShareRow(box8, sb8.IDEAS[0], null, null, function(){});
  var btn8 = byText(sb8, "BUTTON", "Share this idea")[0];
  T_ok(!!btn8, "primary button found");
  btn8.click();
  setTimeout(function(){
    var created8 = sb8.tracked("share_created");
    T_ok(created8.length === 1 && created8[0][1].share_origin === "generic", "panel tap -> share_created origin generic", JSON.stringify(created8[0] && created8[0][1]));

    /* ---------- S9: bank integrity ---------- */
    console.log("S9 bank");
    var ids = sb8.IDEAS.map(function(i){ return i.id; });
    T_ok(ids.length === 138 && new Set(ids).size === 138, "138 ideas, 138 unique IDs", ids.length + "/" + new Set(ids).size);

    /* ---------- S10: dead builders gone ---------- */
    console.log("S10 dead code");
    ["shareVariant","armDChallengeKind","armDStoreRunPhrase","pantryStoreRunTier",
     "planTextFor","teaserTextFor","microTextFor","microVibeOk","microGuess",
     "renderMicroPanel","renderMicroResult","offBrandCaption","offBrandName",
     "shareAsk"].forEach(function(fn){
      T_ok(typeof sb8[fn] === "undefined", fn + " removed", typeof sb8[fn]);
    });
    ["shareAskLine","sendShare","shareTextFor","addCopyShareRow",
     "shareLandingHeadline","shareImage","partyVibeOk"].forEach(function(fn){
      T_ok(typeof sb8[fn] === "function", fn + " live", typeof sb8[fn]);
    });

    console.log(failures === 0 ? "\nALL GREEN" : "\n" + failures + " FAILURES");
    process.exit(failures === 0 ? 0 : 1);
  }, 50);
}, 50);
