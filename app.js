
/* 2026-09-26: global image fallback. Any <img> that fails to load
   (missing deployed asset, CDN hiccup) swaps to a quiet branded placeholder
   instead of the broken-image icon. The dataset guard makes recursion
   impossible: the placeholder is a data URI and can never 404. */
(function(){
  var SVG = "<svg xmlns='http://www.w3.org/2000/svg' width='300' height='400'><rect width='300' height='400' fill='#241f3d'/><path d='M205 105a85 85 0 1 0 58 146A100 100 0 0 1 205 105z' fill='#f5eeda' opacity='0.92'/></svg>";
  var PLACEHOLDER = "data:image/svg+xml;utf8," + encodeURIComponent(SVG);
  window._pmcImgFallback = function(img){
    if (!img || img.tagName !== "IMG" || img.dataset.pmcFbk) return false;
    /* Element-level fallback wins: images with their own onerror (e.g. the
       browse cutout arm falling back to the photo) manage their own chain. */
    if (img.getAttribute("onerror")) return false;
    img.dataset.pmcFbk = "1";
    img.src = PLACEHOLDER;
    return true;
  };
  document.addEventListener("error", function(e){
    if (e.target && e.target.tagName === "IMG") window._pmcImgFallback(e.target);
  }, true);
  function sweep(){
    var imgs = document.getElementsByTagName("img");
    for (var i = 0; i < imgs.length; i++){
      var im = imgs[i];
      try {
        if (im.complete && im.naturalWidth === 0 && !im.dataset.pmcFbk) window._pmcImgFallback(im);
      } catch(e){}
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", sweep);
  else sweep();
})();
/* PostHog analytics: anonymous usage events only. Quiz answers are never sent. */
/* Internal-traffic marking (analytics only, no UX change). Visiting any page
   with ?internal=1 once sets localStorage pmc_internal=1 on that device
   (owner's own phone/laptop); ?internal=0 clears it. Every tracked event from
   a flagged device carries internal:true. ?probe=/ ?sim= QA runs are marked
   internal for that pageview without persisting the flag. The Monday digest
   filters internal:true out, so the funnel counts genuine visitors only.
   Family members on unflagged devices count as genuine. */
var _PMC_INTERNAL = null;
function pmcInternal(){
  if (_PMC_INTERNAL !== null) return _PMC_INTERNAL;
  var flag = false;
  try {
    var q = location.search || "";
    if (/[?&]internal=1(?:&|$)/.test(q)) { try { localStorage.setItem("pmc_internal", "1"); } catch(e){} flag = true; }
    else if (/[?&]internal=0(?:&|$)/.test(q)) { try { localStorage.removeItem("pmc_internal"); } catch(e){} }
    else if (/[?&](probe|sim)=/.test(q)) { flag = true; }
    else { try { flag = localStorage.getItem("pmc_internal") === "1"; } catch(e){} }
  } catch(e2){}
  _PMC_INTERNAL = flag;
  return flag;
}
var Analytics = {
  _q: [],
  track: function(name, props){
    props = props || {};
    try { if (typeof VIA_SHARE !== "undefined" && VIA_SHARE && !props.share_id && !props.via_share_id) props.via_share_id = VIA_SHARE; } catch(e){}
    try { if (pmcInternal()) props.internal = true; } catch(e){}
    try {
      if (window.posthog && posthog.capture) {
        posthog.capture(name, props);
      } else {
        this._q.push([name, props || {}]);
        if (this._q.length > 100) this._q.shift();
      }
    } catch(e){}
    if (window.console && console.debug) console.debug("[pmc]", name, props || {});
  },
  _flush: function(){
    try {
      while (this._q.length) {
        var e = this._q.shift();
        if (window.posthog && posthog.capture) posthog.capture(e[0], e[1]);
      }
    } catch(e2){}
  }
};

/* ============ UNIT ANALYTICS FOUNDATION (2026-09-28) ============
   Every content unit (rail, card, collection) on every page logs an
   impression and per-item clicks WITH POSITION. This is the foundation for
   reading CTR per unit, per position within a unit, and per page, both
   event-based (raw counts) and unique-user (distinct_id), once volume picks
   up. Standing rule: a new unit is not done until it is registered in
   UNIT_REGISTRY below. Query recipes: hour-session/unit-analytics.md */
var UNIT_REGISTRY = {
  /* unit_id: {type, container} — container is the element id holding the items */
  "kids-rail":         {type: "rail", container: "row-kids"},
  "discover-trending": {type: "rail", container: "row-trending"},
  "discover-tonight":  {type: "rail", container: "row-tonight"},
  "discover-new":      {type: "rail", container: "row-new"},
  /* 2026-09-28 (Phase-2 Variant A): storytime-card retired with the
     removed full-width hero card; the storytime rail and kids chip bar
     replace it. */
  "storytime-rail":    {type: "rail", container: "row-storytime"},
  "kids-bar":          {type: "bar",  container: "kidbar"},
  /* 2026-09-29: desktop hero mosaic (tiles link to /c/ guides) and the
     horizontal tool tabs (buttons carry explicit data-item-id). */
  "hero-mosaic":       {type: "mosaic", container: "hero-mosaic"},
  "tools-bar":         {type: "bar",  container: "tool-tabs"},
  /* 2026-09-30: results-page "More options" toggle (group vote, AI prompt,
     Refine). The container is built dynamically by renderResults, so it is
     instrumented via UnitTrack.instrumentUnit, not instrumentAll. */
  "more-options":      {type: "toggle", container: "more-opts"},
  /* 2026-09-30: visible FAQ section (static markup, instrumented on load). */
  "faq":               {type: "section", container: "faq"},
  /* 2026-09-30: detail-page pantry tile panel + primary action row
     (Plan + Share). Built dynamically by buildBrowseDetailCard, so they are
     instrumented via UnitTrack.instrumentUnit, not instrumentAll. */
  "detail-materials":  {type: "panel", container: "detail-mats"},
  "detail-actions":    {type: "bar", container: "detail-actions"},
  /* 2026-09-30 (Billy, Claude R2): "Pairs well with" rail on the detail
     page -- curated same-theme solo/couple/family versions. Built dynamically
     by buildBrowseDetailCard, so instrumented via UnitTrack.instrumentUnit. */
  "pairs-well":        {type: "rail", container: "pairs-well"},
  /* 2026-09-30: search-trends teaser card -> /whats-trending (real weekly
     Pinterest Trends data). Static markup in index.html, instrumented on
     load via instrumentAll. */
  "trends-search-teaser": {type: "card", container: "row-search-trends"}
};
var UnitTrack = (function(){
  "use strict";
  var seen = {}; /* unit_id -> true once its impression has fired this page load */
  function pageName(){ try { return location.pathname || "/"; } catch(e){ return "/"; } }
  function anchorsOf(container){
    /* 2026-09-29: tool tabs are <button>s, not anchors; they carry
       explicit data-item-id so the same impression/click logging applies. */
    var out = [], list = container.querySelectorAll("a,button[data-item-id]"), i;
    for (i = 0; i < list.length; i++) out.push(list[i]);
    return out;
  }
  function itemIdFor(el){
    if (el.getAttribute && el.getAttribute("data-item-id")) return el.getAttribute("data-item-id");
    var a = el, href = a.getAttribute("href") || "";
    var m = href.match(/[?&]idea=([^&#]+)/);
    if (m) { try { return decodeURIComponent(m[1]); } catch(e){ return m[1]; } }
    m = href.match(/\/c\/([^\/?#]+)/);
    if (m) return m[1];
    /* 2026-09-28 (Phase-2 Variant A): storytime rail tiles carry
       ?costume=<slug>; kids-bar chips carry ?game=<peekaboo|match>. */
    m = href.match(/[?&]costume=([a-z0-9-]+)/);
    if (m) return m[1];
    m = href.match(/[?&]game=([a-z]+)/);
    if (m) return "play-" + m[1];
    var clean = href.replace(/^[/#?]+/, "").split(/[?#]/)[0];
    return clean || "unknown";
  }
  function fireImpression(unitId, def, container){
    if (seen[unitId]) return; seen[unitId] = true;
    var ids = anchorsOf(container).map(itemIdFor);
    try {
      Analytics.track("unit_impression", {
        unit_id: unitId, unit_type: def.type, page: pageName(),
        item_count: ids.length, item_ids: ids.slice(0, 40)
      });
    } catch(e){}
  }
  function instrument(unitId, def){
    var container = $(def.container); if (!container) return;
    /* Clicks: delegated; position resolved live at click time. */
    container.addEventListener("click", function(e){
      var t = e.target;
      var a = (t && t.closest) ? t.closest("a,button[data-item-id]") : null;
      if (!a || !container.contains(a)) return;
      var pos = anchorsOf(container).indexOf(a);
      try {
        Analytics.track("unit_click", {
          unit_id: unitId, unit_type: def.type, page: pageName(),
          item_id: itemIdFor(a), position: pos
        });
      } catch(e2){}
    });
    /* Impressions: once per unit per page load, when substantially visible. */
    try {
      if ("IntersectionObserver" in window){
        var io = new IntersectionObserver(function(entries){
          for (var i = 0; i < entries.length; i++){
            if (entries[i].isIntersecting){ fireImpression(unitId, def, container); io.disconnect(); }
          }
        }, {threshold: 0.4});
        io.observe(container);
      } else { fireImpression(unitId, def, container); }
    } catch(e3){ fireImpression(unitId, def, container); }
  }
  function instrumentAll(){
    for (var id in UNIT_REGISTRY){
      if (Object.prototype.hasOwnProperty.call(UNIT_REGISTRY, id)){
        try { instrument(id, UNIT_REGISTRY[id]); } catch(e){}
      }
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", instrumentAll);
  else instrumentAll();
  /* 2026-09-30: dynamic units (built after DOMContentLoaded, e.g. the
     results "More options" toggle) instrument one unit by id. Re-running
     instrumentAll would double-bind click listeners on the static units. */
  function instrumentUnit(unitId){
    var def = UNIT_REGISTRY[unitId];
    if (def && Object.prototype.hasOwnProperty.call(UNIT_REGISTRY, unitId)){
      try { instrument(unitId, def); } catch(e){}
    }
  }
  return {instrumentAll: instrumentAll, instrumentUnit: instrumentUnit, registry: UNIT_REGISTRY};
})();
/* 2026-09-26 (proof-strip step-6 grade): tap->quiz-start within-session
   attribution. When a quiz_started fires and the same tab session recorded a
   proof-strip tap, also fire proofstrip_to_quiz with that idea_id — this is
   the decision metric the next grade needs (quiz starts attributable to the
   strip). sessionStorage survives the strip->/c/->quiz page loads. */
(function(){
  var _track = Analytics.track;
  Analytics.track = function(name, props){
    try {
      if (name === "quiz_started") {
        var raw = null;
        try { raw = sessionStorage.getItem("pmc_proofstrip_tap"); } catch(e){}
        if (raw) {
          var t = JSON.parse(raw);
          if (t && t.idea_id) _track.call(Analytics, "proofstrip_to_quiz", {idea_id: t.idea_id});
        }
      }
    } catch(e){}
    return _track.call(Analytics, name, props);
  };
})();

/* ================= Saved-not-shared recovery (2026-09-26 afternoon) =========
   PostHog 7-day funnel: 118 pick_saved vs 45 share_created. The cheapest new
   shares come from people who picked but never sent. Every save records
   pmc_recover_v1 (both doPick paths above); every completed share clears it.
   One choke point here: every share_created / second_share_created in this
   file goes through Analytics.track, so the marker clears without touching
   the 8+ share paths. Only clears when the shared idea matches the pending
   one: a re-pick updates the marker, so a share of the old pick must not
   cancel the nudge for the new one. The pure core (recoverShouldShow) is
   unit-tested by hour-session/recover-nudge-gate.js. */
function recoverMarkShared(ideaId){
  if (!ideaId) return;
  var rec = load("pmc_recover_v1");
  if (rec && rec.ideaId === ideaId) clearK("pmc_recover_v1");
}
(function(){
  var _track2 = Analytics.track;
  Analytics.track = function(name, props){
    try {
      if ((name === "share_created" || name === "second_share_created") && props && props.idea_id) recoverMarkShared(props.idea_id);
    } catch(e){}
    return _track2.call(Analytics, name, props);
  };
})();
var RECOVER_NUDGE_MIN_AGE_MS = 6*60*60*1000;
var RECOVER_NUDGE_SNOOZE_MS = 7*24*60*60*1000;
function recoverShouldShow(rec, snoozedAt, nowMs){
  if (!rec || !rec.ideaId || !rec.at) return false;
  if (snoozedAt && (nowMs - snoozedAt) < RECOVER_NUDGE_SNOOZE_MS) return false;
  if ((nowMs - rec.at) < RECOVER_NUDGE_MIN_AGE_MS) return false;
  return true;
}

/* ================= Quiz-abandon resume (2026-09-26 evening) ================
   Gap: quiz progress was never persisted; a user who closed the tab mid-quiz
   was gone. Every answered question now saves pmc_quiz_v1 {answers, at}.
   A return visit with answers but no completion gets one slim banner above
   the hero: "Pick up where you left off?" Continue restores the saved
   answers and resumes at the first unanswered question; Not now snoozes
   for 7 days (pmc_resume_snooze_v1), matching the recovery nudge and rally
   banner. Purely additive: finishers never see it (finishQuiz clears
   the marker), one-session users are untouched, and any query string (?s=
   arrivals, ?pick= detail views) suppresses the banner so recipients keep
   the normal recipient experience. Answers never leave the device; the
   resume events carry counts only. Pure core (quizResumeShouldShow,
   quizResumeIndex) is unit-tested by hour-session/quiz-resume-gate.js. */
var QUIZ_RESUME_MAX_AGE_MS = 30*24*60*60*1000;
var QUIZ_RESUME_SNOOZE_MS = 7*24*60*60*1000;
function quizResumeShouldShow(saved, snoozedAt, nowMs){
  if (!saved || !saved.answers || !saved.at) return false;
  if (Object.keys(saved.answers).length === 0) return false;
  if (snoozedAt && (nowMs - snoozedAt) < QUIZ_RESUME_SNOOZE_MS) return false;
  if ((nowMs - saved.at) > QUIZ_RESUME_MAX_AGE_MS) return false;
  return true;
}
function quizResumeSave(){
  /* Called after each answered question, once the answer set is cleaned for
     the current flow. finishQuiz clears the marker, so its presence always
     means "abandoned mid-quiz". Active quiz engagement also re-arms the
     banner: a fresh quiz abandoned later gets its own nag, not the old
     "Not now" snooze. */
  store("pmc_quiz_v1", {answers: state.answers, at: Date.now()});
  clearK("pmc_resume_snooze_v1");
}
function quizResumeIndex(){
  /* First question in the current flow with no answer. -1 when everything
     is answered (defensive; completion clears the marker first). */
  var order = flowOrder();
  for (var i = 0; i < order.length; i++) if (!state.answers[order[i]]) return i;
  return -1;
}

/* ================= Halloween-week sender rally (2026-09-26 evening) ======
   Gap: every share nudge is event-driven (save, arrival) or
   experiment-gated. During the Oct 25-31 decision crunch, past visitors
   with a saved pick get one honest date-gated hero line reusing the real
   daysToHalloween() count: "Halloween is N days away. Your pick is saved.
   Send it to the group chat." Time-boxed by construction: rallyInWindow
   checks the VISITOR's local calendar date, so it shows Oct 25-31 only and
   vanishes Nov 1 on its own. No countdown fudging, no fake scarcity.
   Targeting reuses the saved-pick marker (pmc_recover_v1), so the audience
   is exactly "saved a pick"; an active recovery "Not now" snooze also
   suppresses the rally (no double-nagging), and the rally has its own
   7-day snooze (pmc_rally_snooze_v1). Any query string suppresses it:
   ?s= share arrivals keep the friend banner, ?pick= views already have
   the share row. Runs last among the hero banners and yields when the
   recovery or resume banner is showing. Purely additive. The pure core
   (rallyInWindow, rallyCopyFor, rallyShouldShow) is unit-tested by
   hour-session/halloween-rally-gate.js. */
var RALLY_SNOOZE_MS = 7*24*60*60*1000;
function rallyInWindow(nowMs){
  /* Exact calendar gate in the visitor's local time: Oct 25-31 only.
     October has 31 days, so the lower bound is the whole test. */
  var d = new Date(nowMs);
  return d.getMonth() === 9 && d.getDate() >= 25;
}
function rallyCopyFor(nowMs){
  /* Honest copy off the real date. Oct 31 is "today", never "1 day away". */
  var d = new Date(nowMs);
  if (d.getMonth() === 9 && d.getDate() === 31)
    return "Halloween is today. Your pick is saved. Send it to the group chat.";
  var n = daysToHalloween();
  return "Halloween is " + n + (n === 1 ? " day" : " days") + " away. Your pick is saved. Send it to the group chat.";
}
function rallyShouldShow(rec, recoverSnoozedAt, rallySnoozedAt, search, nowMs){
  if (search) return false;                    /* arrivals keep the recipient experience */
  if (!rec || !rec.ideaId || !rec.at) return false;   /* no saved pick on record */
  if (!rallyInWindow(nowMs)) return false;     /* Oct 25-31 local only */
  if (rallySnoozedAt && (nowMs - rallySnoozedAt) < RALLY_SNOOZE_MS) return false;
  if (recoverSnoozedAt && (nowMs - recoverSnoozedAt) < RECOVER_NUDGE_SNOOZE_MS) return false;
  return true;
}

function $(id){ return document.getElementById(id); }
function store(k, v){ try { localStorage.setItem(k, JSON.stringify(v)); } catch(e){} }
function clearK(k){ try { localStorage.removeItem(k); } catch(e){} }
function load(k){ try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : null; } catch(e){ return null; } }
function isIOS(){ return /iPad|iPhone|iPod/.test(navigator.userAgent || ""); }

/* ================= CONFIG: QUESTIONS ================= */
var QUESTIONS = [
  {id:"q1", title:"Who is dressing up?", hint:"Pick the one that fits best.", options:[
    {label:"Solo", value:"solo", emoji:"\uD83D\uDC64", tags:{}},
    {label:"My kid", value:"kid", emoji:"\uD83E\uDDD2", tags:{}},
    {label:"My family", value:"family", emoji:"\uD83D\uDC6A", tags:{}},
    {label:"Couple", value:"couple", emoji:"\uD83D\uDC91", tags:{}},
    {label:"Group", value:"group", emoji:"\uD83D\uDC65", tags:{}},
    /* 2026-09-29: teacher/class audience. Filters to classroom-friendly
       group-costume ideas (non-scary, school-appropriate); "class" is added
       to those ideas' audience arrays. Bar / club night is hidden for this
       audience, like the kid and family flows. */
    {label:"Teacher / class", value:"class", emoji:"\uD83C\uDF4E", tags:{}},
    /* 2026-09-29: the old warm/cold fork ("One quick question first") is
       folded into Q1 so the "Question X of 5" count stays honest. Picking
       this branches straight to naming the costume (renderWarmCapture). */
    {label:"Already have one", value:"warm", emoji:"✅", tags:{}}
  ]},
  {id:"q2", title:"What vibe are you going for?", hint:"There are no wrong answers.", options:[
    {label:"Funny", emoji:"\uD83D\uDE02", tags:{funny:2}},
    {label:"Scary", emoji:"\uD83D\uDE31", tags:{scary:2}},
    {label:"Cute", emoji:"\uD83E\uDD70", tags:{cute:2}},
    {label:"Chill", emoji:"\uD83D\uDE0E", tags:{simple:2}}
  ]},
  {id:"q4", title:"How much effort?", hint:"Be honest. Couch-level is a fine answer.", options:[
    {label:"Couch-level", emoji:"\uD83D\uDECB\uFE0F", tags:{couch:2}},
    {label:"A little crafty", emoji:"\u2702\uFE0F", tags:{crafty:2}},
    {label:"Go all out", emoji:"\uD83D\uDE80", tags:{allout:2}}
  ]},
  {id:"q5kid", title:"How old?", hint:"So we keep it age-safe.", options:[
    {label:"Under 3", emoji:"\uD83D\uDC76", tags:{kidunder3:4}},
    {label:"3 to 6", emoji:"\uD83E\uDDD2", tags:{kid36:4}},
    {label:"7+", emoji:"\uD83C\uDF92", tags:{kid7plus:4}},
    /* Mara 2026-09-25: moms of 2+ bounced on the singular. Mixed ages gets
       the safest pool (toddler-safe picks work for the older ones too). */
    {label:"Mixed ages", emoji:"\uD83E\uDDF8", tags:{kidunder3:4}}
  ]},
  /* qfit retired 2026-09-24: the conditional fit follow-up ("Which look feels
     more like you?") could make a rare 6th quiz question, breaking the
     5-max. It now lives on the results screen as an optional refinement chip
     row, shown only when the answer can change the top 3. Same scoring
     effect, zero question tax. */
  {id:"qocc", title:"What's the Halloween plan?", hint:"So the pick fits the night.", options:[
    {label:"Trick-or-treating", emoji:"\uD83C\uDF6C", tags:{occtreat:2}},
    {label:"House party", emoji:"\uD83C\uDF89", tags:{occparty:2}},
    /* 2026-09-29: the kid-flow hint promised a school parade option that did
       not exist. It does now: daytime, classroom-safe picks. */
    {label:"School parade / class party", emoji:"\uD83C\uDFEB", tags:{occparade:2}},
    {label:"Bar / club night", value:"bar", emoji:"\uD83C\uDF78", tags:{occbar:2}},
    {label:"Handing out candy", emoji:"\uD83C\uDF6D", tags:{occcandy:2}},
    {label:"Low-key night in", emoji:"\uD83C\uDF19", tags:{occlowkey:2}}
  ]},
  {id:"qinterest", title:"What is your kid into?", hint:"Pick the closest match.", options:[
    {label:"Animals", emoji:"\uD83D\uDC3E", tags:{animals:2}},
    {label:"Princesses & fairy tales", emoji:"\uD83D\uDC51", tags:{princess:2}},
    {label:"Superheroes", emoji:"\uD83E\uDDB8", tags:{heroes:2}},
    {label:"Dinosaurs & monsters", emoji:"\uD83E\uDD96", tags:{dinos:2}},
    {label:"Video games", emoji:"\uD83C\uDFAE", tags:{games:2}},
    {label:"TV & movie characters", emoji:"\uD83D\uDCFA", tags:{tv:2}},
    {label:"Food & snacks", emoji:"\uD83C\uDF55", tags:{food:2}},
    {label:"Sports", emoji:"\u26BD", tags:{sports:2}},
    {label:"Surprise me", emoji:"\uD83C\uDFB2", tags:{}}
  ]}
];

/* ================= CONFIG: PINPOINT =================
   2026-09-25: kids don't think in categories ("superheroes"), they think
   in characters ("Spider-Man", "Ariel"). This optional hero-screen surface
   resolves any specific name or typed query to that costume's detail view:
   chips jump straight to their idea; typed text checks this alias map first
   (exact, then per-token), then fuzzy-matches idea titles via pinpointScore.
   A query with no real match shows the 3 closest ideas with honest copy and
   NEVER silently runs a generic quiz.
   Normalized key (lowercase, alphanumerics only) -> {idea, label}.
   Audited by hour-session/pinpoint-resolve.js: every key's idea must exist
   in the bank, and spot resolution cases must land on the right idea.
   Add keys here AND re-run the test.
   (hour-session/pinpoint-paths.js still verifies the legacy pin mechanism.) */
var PINPOINT_MAP = {"spiderman":{"idea":"web-slinger-crew","label":"Spider hero"},"spidermen":{"idea":"web-slinger-crew","label":"Spider hero"},"milesmorales":{"idea":"web-slinger-crew","label":"Spider hero"},"gwenstacy":{"idea":"web-slinger-crew","label":"Spider hero"},"ghostspider":{"idea":"web-slinger-crew","label":"Spider hero"},"spidergwen":{"idea":"web-slinger-crew","label":"Spider hero"},"ariel":{"idea":"mermaid-crew","label":"Mermaid princess"},"littlemermaid":{"idea":"mermaid-crew","label":"Mermaid princess"},"wednesday":{"idea":"deadpan-diva","label":"Goth girl"},"wednesdayaddams":{"idea":"deadpan-diva","label":"Goth girl"},"nezuko":{"idea":"bamboo-demon","label":"Bamboo demon"},"kpopdemonhunters":{"idea":"neon-demon-hunter","label":"Demon hunters"},"huntrix":{"idea":"neon-demon-hunter","label":"Demon hunters"},"rumi":{"idea":"neon-demon-hunter","label":"Demon hunters"},"bluey":{"idea":"blue-dog-family","label":"Blue dog"},"bingo":{"idea":"blue-dog-family","label":"Blue dog"},"mario":{"idea":"plumber-duo","label":"Plumber hero"},"luigi":{"idea":"plumber-duo","label":"Plumber hero"},"elsa":{"idea":"snow-sisters","label":"Ice princess"},"anna":{"idea":"snow-sisters","label":"Ice princess"},"frozen":{"idea":"snow-sisters","label":"Ice princess"},"olaf":{"idea":"snow-sisters","label":"Ice princess"},"elphaba":{"idea":"good-witch-bad-witch","label":"Green witch"},"glinda":{"idea":"good-witch-bad-witch","label":"Green witch"},"wicked":{"idea":"good-witch-bad-witch","label":"Green witch"},"pokemon":{"idea":"pocket-plush","label":"Plush monster"},"pikachu":{"idea":"pocket-plush","label":"Plush monster"},"minecraft":{"idea":"block-game-crew","label":"Block game"},"steve":{"idea":"block-game-crew","label":"Block game"},"creeper":{"idea":"block-game-crew","label":"Block game"},"amongus":{"idea":"space-crewmate","label":"Space crewmate"},"stitch":{"idea":"blue-alien-ohana","label":"Blue alien"},"fnaf":{"idea":"haunted-animatronics","label":"Haunted pizzeria"},"freddyfazbear":{"idea":"haunted-animatronics","label":"Haunted pizzeria"},"fivenightsatfreddys":{"idea":"haunted-animatronics","label":"Haunted pizzeria"},"minion":{"idea":"goggle-crew","label":"Yellow helpers"},"minions":{"idea":"goggle-crew","label":"Yellow helpers"},"ghostbusters":{"idea":"ghost-hunters","label":"Ghost hunters"},"peppa":{"idea":"little-pig-family","label":"Pig family"},"peppapig":{"idea":"little-pig-family","label":"Pig family"},"dracula":{"idea":"vampire","label":"Vampire"},"vampire":{"idea":"vampire","label":"Vampire"},"greekgods":{"idea":"the-olympians","label":"Greek gods"},"olympians":{"idea":"the-olympians","label":"Greek gods"},"zeus":{"idea":"the-olympians","label":"Zeus"},"athena":{"idea":"the-olympians","label":"Athena"},"odyssey":{"idea":"the-olympians","label":"The Odyssey"},"toystory":{"idea":"toy-box-crew","label":"Toy box crew"},"woody":{"idea":"toy-box-crew","label":"Toy box crew"},"buzzlightyear":{"idea":"toy-box-crew","label":"Toy box crew"},"sajaboys":{"idea":"demon-boy-band","label":"Demon hunters"},"jinu":{"idea":"demon-boy-band","label":"Demon hunters"},"babysaja":{"idea":"demon-boy-band","label":"Demon hunters"},"howtotrainyourdragon":{"idea":"dragon-rider-duo","label":"Dragon rider"},"hiccup":{"idea":"dragon-rider-duo","label":"Dragon rider"},"astrid":{"idea":"dragon-rider-duo","label":"Dragon rider"},"toothless":{"idea":"dragon-rider-duo","label":"Dragon rider"},"squidgame":{"idea":"numbered-players","label":"Numbered players"},"insideout":{"idea":"emotion-crew","label":"Emotion crew"},"insideout2":{"idea":"emotion-crew","label":"Emotion crew"},"anxiety":{"idea":"emotion-crew","label":"Emotion crew"},"mariokart":{"idea":"kart-racers","label":"Kart racers"},"catinthehat":{"idea":"tall-hat-crew","label":"Tall-hat cat"},"thing1":{"idea":"tall-hat-crew","label":"Tall-hat cat"},"thing2":{"idea":"tall-hat-crew","label":"Tall-hat cat"},"alvinandthechipmunks":{"idea":"chipmunk-trio","label":"Chipmunk trio"},"alvin":{"idea":"chipmunk-trio","label":"Chipmunk trio"},"starwars":{"idea":"galaxy-knights","label":"Galaxy knights"},"jedi":{"idea":"galaxy-knights","label":"Galaxy knights"},"lightsaber":{"idea":"galaxy-knights","label":"Galaxy knights"},"barbie":{"idea":"plastic-dream-crew","label":"Dream dolls"},"ken":{"idea":"plastic-dream-crew","label":"Dream dolls"},"wizard":{"idea":"wizard","label":"Wizard"},"wizards":{"idea":"wizard","label":"Wizard"},"belle":{"idea":"enchanted-castle-crew","label":"Enchanted princess"},"beautyandthebeast":{"idea":"enchanted-castle-crew","label":"Enchanted princess"},"beast":{"idea":"enchanted-castle-crew","label":"Enchanted princess"},"princess":{"idea":"fairy-tale-princesses","label":"Princess"},"princesses":{"idea":"fairy-tale-princesses","label":"Princess"},"superhero":{"idea":"superhero-family","label":"Superhero"},"superheroes":{"idea":"superhero-family","label":"Superhero"},"superheros":{"idea":"superhero-family","label":"Superhero"},"disney":{"idea":"enchanted-castle-crew","label":"Fairy-tale princess"},"disneyprincess":{"idea":"enchanted-castle-crew","label":"Fairy-tale princess"},"disneyprincesses":{"idea":"enchanted-castle-crew","label":"Fairy-tale princess"},"mermaid":{"idea":"mermaid-crew","label":"Mermaid"},"mermaids":{"idea":"mermaid-crew","label":"Mermaid"},"spider":{"idea":"web-slinger-crew","label":"Spider hero"},"spiders":{"idea":"web-slinger-crew","label":"Spider hero"},"spidey":{"idea":"web-slinger-crew","label":"Spider hero"},"cinderella":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"cinderela":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"cinderalla":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"cindrella":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"rapunzel":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"raponzel":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"tangled":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"snowwhite":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"aurora":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"arora":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"sleepingbeauty":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"tiana":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"tianna":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"princessandthefrog":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"frogprincess":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"jasmine":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"jasmin":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"mulan":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"merida":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"pocahontas":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"sofia":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"sofiaprincess":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"sofiathefirst":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"elenaofavalor":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"elena":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"mirabel":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"encanto":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"fiona":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"princesspeach":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"elza":{"idea":"snow-sisters","label":"Ice princess"},"ana":{"idea":"snow-sisters","label":"Ice princess"},"lumiere":{"idea":"enchanted-castle-crew","label":"Enchanted object"},"mrspotts":{"idea":"enchanted-castle-crew","label":"Enchanted object"},"cogsworth":{"idea":"enchanted-castle-crew","label":"Enchanted object"},"bell":{"idea":"enchanted-castle-crew","label":"Enchanted princess"},"ursula":{"idea":"mermaid-crew","label":"Sea witch"},"seawitch":{"idea":"mermaid-crew","label":"Sea witch"},"sebastian":{"idea":"mermaid-crew","label":"Crab"},"flounder":{"idea":"mermaid-crew","label":"Fish friend"},"princeeric":{"idea":"mermaid-crew","label":"Sea prince"},"kingtriton":{"idea":"mermaid-crew","label":"Sea king"},"mermade":{"idea":"mermaid-crew","label":"Mermaid"},"mermayd":{"idea":"mermaid-crew","label":"Mermaid"},"barby":{"idea":"plastic-dream-crew","label":"Dream dolls"},"barbi":{"idea":"plastic-dream-crew","label":"Dream dolls"},"moana":{"idea":"fairy-tale-princesses","label":"Fairy-tale princess"},"moanna":{"idea":"wayfinder-princess","label":"Wayfinder princess"},"maui":{"idea":"wayfinder-princess","label":"Wayfinder"},"nemo":{"idea":"under-the-sea","label":"Sea crew"},"dory":{"idea":"under-the-sea","label":"Sea crew"},"findingnemo":{"idea":"under-the-sea","label":"Sea crew"},"octonauts":{"idea":"under-the-sea","label":"Sea crew"},"aquaman":{"idea":"under-the-sea","label":"Sea crew"},"spiderverse":{"idea":"web-slinger-crew","label":"Spider hero"},"superman":{"idea":"superhero-family","label":"Superhero"},"wonderwoman":{"idea":"superhero-family","label":"Superhero"},"flash":{"idea":"superhero-family","label":"Superhero"},"hulk":{"idea":"superhero-family","label":"Superhero"},"blackpanther":{"idea":"superhero-family","label":"Superhero"},"blackwidow":{"idea":"superhero-family","label":"Superhero"},"captainamerica":{"idea":"superhero-family","label":"Superhero"},"deadpool":{"idea":"superhero-family","label":"Superhero"},"incredibles":{"idea":"superhero-family","label":"Superhero"},"mrincredible":{"idea":"superhero-family","label":"Superhero"},"elastigirl":{"idea":"superhero-family","label":"Superhero"},"myheroacademia":{"idea":"superhero-family","label":"Superhero"},"deku":{"idea":"superhero-family","label":"Superhero"},"onepunchman":{"idea":"superhero-family","label":"Superhero"},"saitama":{"idea":"superhero-family","label":"Superhero"},"sailormoon":{"idea":"superhero-family","label":"Superhero"},"ironman":{"idea":"tin-hero","label":"Tin hero"},"tonystark":{"idea":"tin-hero","label":"Tin hero"},"naruto":{"idea":"ninja","label":"Ninja"},"sasuke":{"idea":"ninja","label":"Ninja"},"kakashi":{"idea":"ninja","label":"Ninja"},"sakura":{"idea":"ninja","label":"Ninja"},"ninjaturtles":{"idea":"ninja","label":"Ninja"},"tmnt":{"idea":"ninja","label":"Ninja"},"leonardo":{"idea":"ninja","label":"Ninja"},"donatello":{"idea":"ninja","label":"Ninja"},"raphael":{"idea":"ninja","label":"Ninja"},"michelangelo":{"idea":"ninja","label":"Ninja"},"darthvader":{"idea":"galaxy-knights","label":"Galaxy knights"},"lukeskywalker":{"idea":"galaxy-knights","label":"Galaxy knights"},"luke":{"idea":"galaxy-knights","label":"Galaxy knights"},"princessleia":{"idea":"galaxy-knights","label":"Galaxy knights"},"leia":{"idea":"galaxy-knights","label":"Galaxy knights"},"yoda":{"idea":"galaxy-knights","label":"Galaxy knights"},"grogu":{"idea":"galaxy-knights","label":"Galaxy knights"},"babyyoda":{"idea":"galaxy-knights","label":"Galaxy knights"},"mandalorian":{"idea":"galaxy-knights","label":"Galaxy knights"},"mando":{"idea":"galaxy-knights","label":"Galaxy knights"},"chewbacca":{"idea":"galaxy-knights","label":"Galaxy knights"},"chewie":{"idea":"galaxy-knights","label":"Galaxy knights"},"r2d2":{"idea":"galaxy-knights","label":"Galaxy knights"},"stormtrooper":{"idea":"galaxy-knights","label":"Galaxy knights"},"harrypotter":{"idea":"wizard","label":"Wizard"},"hermione":{"idea":"wizard","label":"Wizard"},"ronweasley":{"idea":"wizard","label":"Wizard"},"ron":{"idea":"wizard","label":"Wizard"},"voldemort":{"idea":"wizard","label":"Wizard"},"dumbledore":{"idea":"wizard","label":"Wizard"},"hogwarts":{"idea":"wizard","label":"Wizard"},"doctorstrange":{"idea":"wizard","label":"Wizard"},"scoobydoo":{"idea":"mystery-crew","label":"Mystery crew"},"scooby":{"idea":"mystery-crew","label":"Mystery crew"},"shaggy":{"idea":"mystery-crew","label":"Mystery crew"},"velma":{"idea":"mystery-crew","label":"Mystery crew"},"daphne":{"idea":"mystery-crew","label":"Mystery crew"},"luffy":{"idea":"pirate-captain","label":"Pirate"},"onepiece":{"idea":"pirate-captain","label":"Pirate"},"captainhook":{"idea":"pirate-captain","label":"Pirate"},"zoro":{"idea":"pirate-captain","label":"Pirate"},"link":{"idea":"cardboard-knight","label":"Knight"},"zelda":{"idea":"cardboard-knight","label":"Knight"},"bumblebee":{"idea":"robot-crew","label":"Robot"},"optimusprime":{"idea":"robot-crew","label":"Robot"},"transformers":{"idea":"robot-crew","label":"Robot"},"baymax":{"idea":"robot-crew","label":"Robot"},"cyborg":{"idea":"robot-crew","label":"Robot"},"powerrangers":{"idea":"robot-ranger","label":"Robot ranger"},"powerranger":{"idea":"robot-ranger","label":"Robot ranger"},"redranger":{"idea":"robot-ranger","label":"Robot ranger"},"roblox":{"idea":"block-game-crew","label":"Block game"},"alex":{"idea":"block-game-crew","label":"Block game"},"enderman":{"idea":"block-game-crew","label":"Block game"},"piglin":{"idea":"block-game-crew","label":"Block game"},"impostor":{"idea":"space-crewmate","label":"Space crewmate"},"imposter":{"idea":"space-crewmate","label":"Space crewmate"},"crewmate":{"idea":"space-crewmate","label":"Space crewmate"},"eevee":{"idea":"pocket-plush","label":"Plush monster"},"squirtle":{"idea":"pocket-plush","label":"Plush monster"},"bulbasaur":{"idea":"pocket-plush","label":"Plush monster"},"charmander":{"idea":"pocket-plush","label":"Plush monster"},"labubu":{"idea":"pocket-plush","label":"Plush monster"},"pokeman":{"idea":"pocket-plush","label":"Plush monster"},"picachu":{"idea":"pocket-plush","label":"Plush monster"},"totoro":{"idea":"fuzzy-monster","label":"Fuzzy monster"},"kirby":{"idea":"fuzzy-monster","label":"Fuzzy monster"},"fallguys":{"idea":"fuzzy-monster","label":"Fuzzy monster"},"sulley":{"idea":"fuzzy-monster","label":"Fuzzy monster"},"mikewazowski":{"idea":"fuzzy-monster","label":"Fuzzy monster"},"monstersinc":{"idea":"fuzzy-monster","label":"Fuzzy monster"},"elmo":{"idea":"fuzzy-monster","label":"Fuzzy monster"},"cookiemonster":{"idea":"fuzzy-monster","label":"Fuzzy monster"},"yoshi":{"idea":"baby-dino","label":"Baby dino"},"dinosour":{"idea":"baby-dino","label":"Baby dino"},"dinosaur":{"idea":"baby-dino","label":"Baby dino"},"bowser":{"idea":"dino-herd","label":"Dino"},"charizard":{"idea":"dragon-rider-duo","label":"Dragon rider"},"simba":{"idea":"little-lion","label":"Little lion"},"nala":{"idea":"little-lion","label":"Little lion"},"scar":{"idea":"little-lion","label":"Little lion"},"bandit":{"idea":"blue-dog-family","label":"Blue dog"},"chilli":{"idea":"blue-dog-family","label":"Blue dog"},"muffin":{"idea":"blue-dog-family","label":"Blue dog"},"socks":{"idea":"blue-dog-family","label":"Blue dog"},"pawpatrol":{"idea":"rescue-pups","label":"Rescue pup"},"chase":{"idea":"rescue-pups","label":"Rescue pup"},"skye":{"idea":"rescue-pups","label":"Rescue pup"},"marshall":{"idea":"rescue-pups","label":"Rescue pup"},"rubble":{"idea":"rescue-pups","label":"Rescue pup"},"everest":{"idea":"rescue-pups","label":"Rescue pup"},"georgepig":{"idea":"little-pig-family","label":"Pig family"},"mummypig":{"idea":"little-pig-family","label":"Pig family"},"daddypig":{"idea":"little-pig-family","label":"Pig family"},"judyhopps":{"idea":"safari-zoo-crew","label":"Zoo crew"},"nickwilde":{"idea":"safari-zoo-crew","label":"Zoo crew"},"jessie":{"idea":"toy-box-crew","label":"Toy box crew"},"buzz":{"idea":"toy-box-crew","label":"Toy box crew"},"rex":{"idea":"toy-box-crew","label":"Toy box crew"},"hamm":{"idea":"toy-box-crew","label":"Toy box crew"},"slinky":{"idea":"toy-box-crew","label":"Toy box crew"},"forky":{"idea":"toy-box-crew","label":"Toy box crew"},"bopeep":{"idea":"toy-box-crew","label":"Toy box crew"},"lightningmcqueen":{"idea":"kart-racers","label":"Kart racers"},"mcqueen":{"idea":"kart-racers","label":"Kart racers"},"mater":{"idea":"kart-racers","label":"Kart racers"},"vanellope":{"idea":"kart-racers","label":"Kart racers"},"joy":{"idea":"emotion-crew","label":"Emotion crew"},"sadness":{"idea":"emotion-crew","label":"Emotion crew"},"anger":{"idea":"emotion-crew","label":"Emotion crew"},"disgust":{"idea":"emotion-crew","label":"Emotion crew"},"fear":{"idea":"emotion-crew","label":"Emotion crew"},"zoey":{"idea":"neon-demon-hunter","label":"Demon hunters"},"mira":{"idea":"neon-demon-hunter","label":"Demon hunters"},"bts":{"idea":"pop-star","label":"Pop star"},"blackpink":{"idea":"pop-star","label":"Pop star"},"tinkerbell":{"idea":"garden-fairy","label":"Fairy"},"tink":{"idea":"garden-fairy","label":"Fairy"},"fairygodmother":{"idea":"garden-fairy","label":"Fairy"},"isabela":{"idea":"garden-fairy","label":"Fairy"},"dwarfs":{"idea":"garden-gnome","label":"Garden gnome"},"sevendwarfs":{"idea":"garden-gnome","label":"Garden gnome"},"coco":{"idea":"glow-skeleton","label":"Glow skeleton"},"miguel":{"idea":"glow-skeleton","label":"Glow skeleton"},"jackskellington":{"idea":"glow-skeleton","label":"Glow skeleton"},"corpsebride":{"idea":"pumpkin-king-bride","label":"Spooky bride"},"sally":{"idea":"pumpkin-king-bride","label":"Ragdoll bride"},"hoteltransylvania":{"idea":"vampire","label":"Vampire"},"morticia":{"idea":"deadpan-diva","label":"Goth girl"},"cruella":{"idea":"deadpan-diva","label":"Goth girl"},"wendsday":{"idea":"deadpan-diva","label":"Goth girl"},"wensday":{"idea":"deadpan-diva","label":"Goth girl"},"enid":{"idea":"gloom-bloom","label":"Goth duo"},"hocuspocus":{"idea":"witchy-sisters","label":"Witch sisters"},"winifred":{"idea":"witchy-sisters","label":"Witch sisters"},"maleficent":{"idea":"emerald-witch","label":"Green witch"},"scarletwitch":{"idea":"little-witch","label":"Little witch"},"chica":{"idea":"haunted-animatronics","label":"Haunted pizzeria"},"bonnie":{"idea":"haunted-animatronics","label":"Haunted pizzeria"},"foxy":{"idea":"haunted-animatronics","label":"Haunted pizzeria"},"thor":{"idea":"the-olympians","label":"Norse god"},"loki":{"idea":"the-olympians","label":"Norse god"},"percyjackson":{"idea":"the-olympians","label":"Greek hero"},"ben10":{"idea":"hero-squad","label":"Hero squad"},"goku":{"idea":"hero-squad","label":"Hero squad"},"pjmasks":{"idea":"hero-squad","label":"Hero squad"},"catboy":{"idea":"hero-squad","label":"Hero squad"},"owlette":{"idea":"hero-squad","label":"Hero squad"},"gekko":{"idea":"hero-squad","label":"Hero squad"},"sonic":{"idea":"hero-squad","label":"Hero squad"},"princecharming":{"idea":"prince-princess","label":"Prince"},"flynnrider":{"idea":"prince-princess","label":"Prince"},"aladdin":{"idea":"prince-princess","label":"Prince"},"miraculousladybug":{"idea":"ladybug","label":"Ladybug"},"marinette":{"idea":"ladybug","label":"Ladybug"},"chatnoir":{"idea":"black-cat","label":"Cat burglar"},"fortnite":{"idea":"player-one-two","label":"Gamer"},"doctorwho":{"idea":"doctor-bride","label":"Time traveler"},"stich":{"idea":"blue-alien-ohana","label":"Blue alien"},"gru":{"idea":"goggle-crew","label":"Yellow helpers"},"despicableme":{"idea":"goggle-crew","label":"Yellow helpers"},"tanjiro":{"idea":"bamboo-demon","label":"Bamboo demon"},"zenitsu":{"idea":"bamboo-demon","label":"Bamboo demon"},"demonslayer":{"idea":"bamboo-demon","label":"Bamboo demon"},};
/* Homepage search chips (Variant C, 2026-09-25): popular searches
   wired to the full search intelligence (aliases + attribute filters) via
   the browse shelf. "tonight" uses the same <=30-min plan criterion as the
   Tonight-Ready result role. */
function pinpointNormalize(s){
  /* Fold diacritics first so "Pok\u00e9mon" -> "pokemon", not "pokmon". */
  var t = (s || "").toLowerCase();
  if (t.normalize) t = t.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  return t.replace(/[^a-z0-9]/g, "");
}
function pinpointMatch(raw){
  var key = pinpointNormalize(raw);
  if (!key) return null;
  var hit = PINPOINT_MAP[key];
  return hit ? {label: hit.label, idea: hit.idea, raw: raw} : null;
}
/* Token-overlap scoring against titles, blurbs, and tag keys. Powers the
   fuzzy typed-query match and the honest closest-3 fallback. titleHit marks
   that at least one query word landed in the idea's title, which is the
   bar a fuzzy match must clear. */
function pinpointScore(raw){
  var words = (raw || "").toLowerCase().replace(/[^a-z0-9 ]/g, " ").split(/ +/).filter(function(w){ return w.length >= 3; });
  var scored = IDEAS.map(function(idea){
    var title = idea.title.toLowerCase();
    var hay = (title + " " + idea.blurb).toLowerCase();
    var tags = Object.keys(idea.tags || {});
    var score = 0, titleHit = false;
    words.forEach(function(w){
      if (title.indexOf(w) !== -1){ score += 2; titleHit = true; }
      else if (hay.indexOf(w) !== -1) score += 2;
      for (var i = 0; i < tags.length; i++){
        if (tags[i].indexOf(w) !== -1 || w.indexOf(tags[i]) !== -1) score += 1;
      }
    });
    return {idea: idea, score: score, titleHit: titleHit};
  });
  scored.sort(function(a, b){ return (b.score - a.score) || (a.idea.rank - b.idea.rank); });
  return scored;
}
/* Pure resolution for a typed query: exact alias, then per-token alias
   ("Disney Halloween" -> the Disney alias), then a fuzzy title match.
   Anything else is an honest nomatch; the caller shows the closest 3. */
function pinpointResolve(raw){
  var hit = pinpointMatch(raw);
  if (hit) return {kind: "match", label: hit.label, idea: hit.idea};
  var words = (raw || "").toLowerCase().replace(/[^a-z0-9 ]/g, " ").split(/ +/).filter(Boolean);
  for (var i = 0; i < words.length; i++){
    var th = pinpointMatch(words[i]);
    if (th) return {kind: "match", label: th.label, idea: th.idea};
  }
  var scored = pinpointScore(raw);
  if (scored.length && scored[0].titleHit) return {kind: "fuzzy", label: (raw || "").trim(), idea: scored[0].idea.id};
  return {kind: "nomatch"};
}
/* 2026-09-30 (P0 fix batch): theme fallback for typed queries with no
   alias or fuzzy match. Keyword phrases are matched on word boundaries so
   "escape room" does not trip the "cape" theme. Pure function: no DOM, so
   the node gate (hour-session/pinpoint-resolve.js) asserts it directly.
   Returns curated idea ids, best-first, max 3. */
function pinpointThemeIdeas(raw){
  var themes = [
    {phrases: ["crown", "crowns", "tiara", "tiaras", "ball gown", "glass slipper"],
     ideas: ["fairy-tale-princesses", "enchanted-castle-crew", "snow-sisters"]},
    {phrases: ["cape", "capes", "mask", "masks"],
     ideas: ["superhero-family", "web-slinger-crew", "tin-hero"]}
  ];
  var spaced = " " + (raw || "").toLowerCase().replace(/[^a-z0-9 ]/g, " ").replace(/\s+/g, " ").trim() + " ";
  for (var i = 0; i < themes.length; i++){
    var t = themes[i];
    for (var j = 0; j < t.phrases.length; j++){
      if (spaced.indexOf(" " + t.phrases[j] + " ") !== -1) return t.ideas.slice();
    }
  }
  return [];
}


/* ================= CONFIG: IDEAS =================
   Standing rule (2026-09-25): a two-character costume is never
   solo-servable -- copy describing two people ("for one ... for the other",
   "duo") must not sit on a solo audience. venue:{bar:0|1|2} rates bar-night
   fitness: 0 = hard-excludes bar/club (face-covering masks, box heads,
   stilts, oversized/fragile/hot); 1 = tolerable; 2 = bar-native.
   rank = editorial order: browse-all sorting AND quiz tiebreak (lower wins).
   Rubric: (1) 2026 trend heat, (2) fit for the core audience (parents/kids/family),
   (3) thumbnail readability, (4) DIY ease and budget-friendliness. Owner finalizes. */
var IDEAS = [
  {id:"neon-demon-hunter", title:"Neon Demon Hunter", blurb:"Streetwear with glowing sigils, a foam sword, and pop-idol hair and makeup.", why:"Pop star by day, demon hunter by night. The year's biggest costume energy.", audience:["solo"], budget:["mid","diy"], tags:{allout:2,cute:2,funny:1,scary:1,crafty:1,tv:3,occbar:2,occparty:2}, fit:"U", venue:{bar:2}, rank:1},
  {id:"classic-ghost", title:"Classic Ghost", blurb:"A white sheet with cut-out eyes.", why:"Top five for kids and adults alike. The most universal costume there is.", audience:["kid","solo","family"], budget:["diy","low"], tags:{scary:2,couch:3,simple:3,kid36:2,kid7plus:2,cute:1,occcandy:2,occlowkey:1,occtreat:2}, trending:true, trendLane:"Ghost", trendStat:"a perennial favorite", fit:"U", venue:{bar:1}, rank:2},
  {id:"blue-dog-family", title:"Aussie Dog Family", blurb:"Dog-ear headbands and blue-or-orange shirts: mama, dad, and the pups.", why:"Blue and orange shirts, paper ears, and your kid completely loses it.", audience:["family","kid"], budget:["diy","low"], tags:{"cute":3,"funny":1,"simple":2,"couch":2,"kidunder3":2,"kid36":2,animals:1,tv:3,occcandy:1,occtreat:2,occparade:2}, fit:"U", venue:{bar:2}, rank:3, roles:{kid:["a pup","the blue pup"],adult:["dad","mama"]}},
  {id:"superhero-family", title:"Superhero Family", blurb:"Red sweatsuits, black eye masks, felt logo. The whole family goes super.", why:"Scales from two to six people, and every age knows the movie.", audience:["family"], budget:["low","mid"], tags:{cute:2,funny:1,couch:1,simple:2,heroes:3,tv:2,occparty:1,occtreat:2}, fit:"U", venue:{bar:1}, rank:4},
  {id:"blue-alien-ohana", title:"Blue Alien Ohana", blurb:"A blue hoodie and an antenna headband turn the kid into the alien.", why:"Everyone knows the alien without you saying a word, and the headband does all the work.", audience:["family","kid"], budget:["diy","low"], tags:{"cute":3,"funny":1,"simple":2,"couch":2,"kidunder3":3,"kid36":2,animals:1,tv:3,occcandy:1,occtreat:2,occparade:2}, fit:"U", venue:{bar:2}, rank:5, roles:{kid:["the alien"],adult:["the girl"]}},
  {id:"emerald-witch", title:"Emerald Witch", blurb:"An all-green-everything gown, dramatic makeup, and a pointy hat gone couture.", why:"Green is the color of the season, and you can thrift most of it.", audience:["solo"], budget:["mid","diy"], tags:{allout:2,cute:2,scary:1,crafty:1,princess:1,tv:3,occbar:2,occparty:2}, trending:true, trendLane:"Witch", trendStat:"a top pick for adults this year", fit:"F", venue:{bar:2}, rank:6},
  {id:"gloom-bloom", title:"Gloom & Bloom", blurb:"Braids and black for Gloom, color-pop and smiles for Bloom.", why:"The deadpan duo: one broods, one sparkles, both nail it.", audience:["group"], budget:["diy","low"], tags:{"funny":1,"scary":2,"simple":2,"couch":2,"kid7plus":2,tv:3,occbar:1,occparty:2}, fit:"F", venue:{bar:2}, rank:7, roles:{kid:["Gloom"],adult:["Bloom"]}},
  {id:"deadpan-diva", title:"Deadpan Diva", blurb:"Black dress, two braids, pale makeup, and a stare that ends conversations.", why:"The goth icon: closet-easy, instantly readable, and the braids do half the work.", audience:["solo"], budget:["diy","low"], tags:{tv:3,scary:3,simple:2,couch:2,occbar:2,occparty:1}, fit:"F", venue:{bar:2}, rank:8},
  {id:"safari-zoo-crew", title:"Safari / Zoo Crew", blurb:"Everyone picks an animal: closet clothes in matching colors plus an ear headband.", why:"One ear pack covers the whole group, and everyone still gets their own role.", audience:["group","family","class"], budget:["low","diy"], tags:{cute:3,simple:2,couch:1,animals:3,occparty:1,occtreat:2,occparade:2}, fit:"U", venue:{bar:2}, rank:9},
  {id:"fairy-tale-princesses", title:"Fairy Tale Princesses", blurb:"A dress or a crown from the closet. Every princess works.", why:"Most kids already have a favorite; the dress does the work.", audience:["kid","family","group","class"], budget:["diy","low"], tags:{"cute":3,"simple":1,"couch":2,"kid36":2,"kid7plus":1,princess:3,occparty:1,occtreat:2,occparade:2}, trending:true, trendLane:"Princess", trendStat:"a top pick for kids this year", fit:"F", venue:{bar:2}, rank:10},
  {id:"tin-hero", title:"The Tin Hero", blurb:"Red and gold plus a glowing chest circle: the suit does the talking.", why:"Kids lose their minds over the chest light, and it costs less than the candy.", audience:["solo","kid"], budget:["diy","low"], tags:{"cute":1,"funny":1,"simple":2,"couch":1,"crafty":1,"kid36":2,"kid7plus":2,heroes:3,tv:2,occbar:1,occparty:1,occtreat:2,occparade:2}, fit:"M", venue:{bar:2}, rank:11},
  {id:"good-witch-bad-witch", title:"Good Witch, Bad Witch", blurb:"Green face paint and black for one, pink gown and crown for the other.", why:"The duo of the year: one goes dark, one goes dazzling.", audience:["group"], budget:["diy","mid"], tags:{"cute":2,"scary":1,"crafty":2,"simple":1,"kid7plus":1,princess:2,tv:3,occbar:1,occparty:2}, trending:true, trendLane:"Witch", trendStat:"a top pick for adults this year", fit:"F", venue:{bar:2}, rank:12, roles:{kid:["the good witch"],adult:["the bad witch"]}},
  {id:"fuzzy-monster", title:"Fuzzy Monster", blurb:"A pastel fuzzy sweatsuit with giant googly eyes and an oversized stitched smile.", why:"Ugly-cute is the whole point, and it is basically pajamas.", audience:["kid"], budget:["low","diy"], tags:{couch:2,cute:3,funny:1,kidunder3:1,kid36:2,kid7plus:1,dinos:2,occlowkey:1,occtreat:2,occparade:2}, fit:"U", venue:{bar:1}, rank:13},
  {id:"pocket-plush", title:"Pocket Plush Monster", blurb:"A fuzzy one-piece, giant ears, a stitched smile, and an oversized collector tag.", why:"You become the toy-aisle icon: ugly-cute, comfy, and built for hugs.", audience:["kid"], budget:["diy","low"], tags:{cute:3,dinos:2,funny:2,simple:2,couch:1,kid36:2,kid7plus:2,kidunder3:1,occlowkey:1,occtreat:2,occparade:2}, fit:"U", venue:{bar:1}, rank:14},
  {id:"soccer-squad", title:"Soccer Squad", blurb:"Jerseys for the players, black for the ref, one red card.", why:"World Cup year: everyone already owns half of this.", audience:["family","group","class"], budget:["low","diy"], tags:{couch:2,cute:2,funny:2,simple:2,sports:2,occparty:2,occtreat:1,occparade:2}, fit:"U", venue:{bar:2}, rank:15, roles:{kid:["a player"],adult:["the ref"]}},
  {id:"glow-skeleton", title:"Glow Skeleton", blurb:"Black sweats with glow-in-the-dark bone tape, plus glow bracelets.", why:"Spooky after dark and visible to cars, which parents love.", audience:["kid"], budget:["low","diy"], tags:{couch:2,scary:2,cute:1,kid36:2,kid7plus:1,occcandy:1,occtreat:3}, fit:"U", venue:{bar:2}, rank:16},
  {id:"block-game-crew", title:"Block Game Crew", blurb:"Cardboard-box heads: pick your blocky hero.", why:"A box, some paint, and instant blockhead status.", audience:["kid","family","group","class"], budget:["diy","low"], tags:{"funny":2,"simple":2,"crafty":2,"kid36":2,"kid7plus":2,games:3,occparty:2,occtreat:2,occparade:2}, fit:"U", venue:{bar:0}, rank:17},
  {id:"web-slinger-crew", title:"Web Hero Crew", blurb:"Red, black, and pink hoodies plus masks. Pick your spider.", why:"Everyone gets their own color and nobody fights over it.", audience:["group","class"], budget:["low","mid"], tags:{cute:2,funny:1,couch:2,simple:2,heroes:3,tv:2,occbar:1,occparty:2,occparade:2}, trending:true, trendLane:"Spider hero", trendStat:"a top pick for kids this year", fit:"U", venue:{bar:2}, rank:18},
  {id:"mermaid-crew", title:"Mermaid Crew", blurb:"The mermaid, the prince, the sea king, the sea witch, or the crab: pick your role.", why:"No filler roles in this crew: even the crab gets to be the star.", audience:["family","group","class"], budget:["diy","low"], tags:{"cute":2,"funny":1,"simple":1,"couch":1,"crafty":1,"kid36":2,"kid7plus":1,princess:3,tv:2,occparty:2,occtreat:1,occparade:2}, fit:"F", venue:{bar:1}, rank:19, roles:{kid:["the mermaid","the crab"],adult:["the sea king","the sea witch","the prince"]}},
  {id:"little-pig-family", title:"Little Pig Family", blurb:"Pink clothes and a snout headband; little brother brings the dinosaur.", why:"Four matching snouts in one photo never miss, and little brother's dinosaur is the plot twist.", audience:["family","kid"], budget:["diy","low"], tags:{"cute":3,"dinos":1,"funny":1,"simple":2,"couch":2,"kidunder3":2,"kid36":2,animals:1,tv:3,occcandy:1,occtreat:2,occparade:2}, fit:"U", venue:{bar:2}, rank:20, roles:{kid:["a little pig","the dinosaur"],adult:["papa pig","mama pig"]}},
  {id:"enchanted-castle-crew", title:"Enchanted Castle Crew", blurb:"The bookish princess, the cursed prince, the talking candelabra, the talking clock, the talking teapot: pick your role.", why:"The enchanted objects steal the show, and they're all DIY.", audience:["family","group","class"], budget:["diy","low"], tags:{"cute":2,"funny":1,"crafty":2,"kid36":1,"kid7plus":1,princess:2,tv:2,occparty:2,occtreat:1,occparade:2}, fit:"F", venue:{bar:1}, rank:21, roles:{kid:["the bookish princess","the talking teapot"],adult:["the cursed prince","the talking candelabra","the talking clock"]}},
  {id:"bumble-bee", title:"Bumble Bee", blurb:"Black sweats with yellow tape stripes and soft felt antennae.", why:"Yellow tape stripes read as bee instantly, and it builds the night before.", audience:["kid"], budget:["diy","low"], tags:{cute:2,funny:1,crafty:1,kidunder3:1,kid36:2,animals:2,occtreat:2,occparade:2}, fit:"U", venue:{bar:2}, rank:22},
  {id:"baby-dino", title:"Baby Dinosaur", blurb:"Green hoodie, felt spikes down the back, stuffed tail.", why:"A hoodie costume means zero complaints about itching or slipping.", audience:["kid"], budget:["low","mid","diy"], tags:{cute:2,funny:1,couch:1,kidunder3:2,kid36:2,dinos:3,occtreat:2,occparade:2}, fit:"U", venue:{bar:2}, rank:23},
  {id:"little-lion", title:"Little Lion", blurb:"Tan sweatsuit plus a fuzzy mane hood.", why:"Head to toe warm, and the mane hood photographs perfectly.", audience:["kid"], budget:["mid"], tags:{couch:2,cute:3,kidunder3:2,kid36:2,animals:2,occtreat:2,occparade:2}, fit:"U", venue:{bar:1}, rank:24},
  {id:"tiny-firefighter", title:"Tiny Firefighter", blurb:"Red sweats, a plastic helmet, and a toy hose.", why:"The helmet does all the work, and other 3-year-olds will wave at yours.", audience:["kid"], budget:["low","mid"], tags:{couch:2,simple:2,kidunder3:1,kid36:2,kid7plus:1,occtreat:2,heroes:3,occparade:2}, fit:"U", venue:{bar:1}, rank:25},
  {id:"little-shark", title:"Little Shark", blurb:"Gray hoodie with a felt fin glued on the back.", why:"Sharks are timeless even when the song is not, and it is just a hoodie with a fin.", audience:["kid"], budget:["low","mid"], tags:{cute:2,couch:1,kidunder3:2,kid36:2,animals:2,occtreat:2,occparade:2}, fit:"U", venue:{bar:2}, rank:26},
  {id:"walking-taco", title:"Walking Taco", blurb:"Tan vest painted like a taco shell with felt toppings.", why:"Maximum laughs per dollar at the preschool parade.", audience:["kid"], budget:["diy","mid"], tags:{funny:3,crafty:2,kid36:2,kid7plus:1,food:2,occparty:1,occtreat:2,occparade:2}, fit:"U", venue:{bar:2}, rank:27},
  {id:"ramen-bowl", title:"Ramen Bowl", blurb:"Cardboard bowl rim, noodle-yarn hair, a foam egg on top.", why:"Cozy, funny, and the chopsticks make every photo.", audience:["kid","solo"], budget:["diy","low"], tags:{funny:2,cute:2,couch:2,kid36:2,food:2,occparty:2,occtreat:1,occparade:2}, fit:"U", venue:{bar:1}, rank:28},
  {id:"tiny-snail", title:"Tiny Snail", blurb:"Neutral clothes plus a lightweight spiral shell from cardboard worn like a backpack.", why:"Recognizable without anything on the head or face.", audience:["kid"], budget:["diy"], tags:{couch:2,cute:3,simple:2,kid36:2,kidunder3:2,animals:2,occtreat:2,occparade:2}, fit:"U", venue:{bar:1}, rank:29},
  {id:"little-witch", title:"Little Witch", blurb:"Black cape, pointy hat, striped tights, green face paint.", why:"Classic, comfortable, and the green face paint keeps it from being just-a-witch.", audience:["kid"], budget:["low","diy"], tags:{couch:2,cute:2,scary:1,kid36:2,kid7plus:1,occtreat:2}, fit:"F", venue:{bar:2}, rank:30},
  {id:"spider", title:"Eight-Legged Spider", blurb:"Black sweats with stuffed sock legs attached at the sides.", why:"Spooky from across the street, snuggly up close.", audience:["kid"], budget:["diy"], tags:{scary:2,crafty:2,kid36:2,kid7plus:1,occtreat:2}, fit:"U", venue:{bar:2}, rank:31},
  {id:"backyard-hero", title:"Backyard Superhero", blurb:"Short cape plus a first initial on the chest, mask optional.", why:"Skip the mask, add a face-paint lightning bolt, still a hero.", audience:["kid"], budget:["low","diy"], tags:{simple:2,cute:1,couch:1,kid36:2,kid7plus:1,heroes:3,occtreat:2,occparade:2}, fit:"U", venue:{bar:2}, rank:32},
  {id:"pickle", title:"Pickle", blurb:"Green tunic, bumpy texture, smug grin.", why:"A pickle costume has no business working this well. And yet.", audience:["solo"], budget:["diy","low"], tags:{funny:3,couch:2,food:2,occbar:2,occcandy:1,occparty:2}, fit:"U", venue:{bar:2}, rank:33},
  {id:"vampire", title:"Classic Vampire", blurb:"Black cape, fangs, slicked hair.", why:"Scary with 25 minutes of effort and it photographs great.", audience:["solo"], budget:["low","mid"], tags:{scary:3,couch:1,occbar:3,occparty:2}, trending:true, trendLane:"Vampire", trendStat:"a top pick for adults this year", fit:"M", venue:{bar:2}, rank:34},
  {id:"bamboo-demon", title:"Bamboo-Muzzle Demon", blurb:"Pink robe, long dark wig, and a cardboard bamboo muzzle tied with ribbon.", why:"Cute demon energy: anime fans clock it instantly, everyone else just sees adorable.", audience:["solo"], budget:["diy","low"], tags:{tv:3,cute:3,scary:1,simple:2,couch:1,occbar:2,occparty:2}, fit:"F", venue:{bar:0}, rank:35},
  {id:"emoji-crew", title:"Emoji Crew", blurb:"Everyone picks an emoji: a yellow tee plus a big printed face.", why:"Everyone picks their own emoji, and the group photo reads instantly.", audience:["group","family","class"], budget:["diy","low"], tags:{cute:3, funny:1, simple:2, couch:2,occparty:2,occtreat:1,occparade:2}, fit:"U", venue:{bar:2}, rank:36},
  {id:"robot-crew", title:"Cardboard Robot Crew", blurb:"Boxy robots built from cardboard boxes, foil, and bottle-cap buttons.", why:"Cardboard boxes scale to any headcount, and every robot looks intentionally janky.", audience:["group","family","class"], budget:["diy","low"], tags:{allout:2,funny:3,crafty:3,occparty:2,occparade:2}, fit:"U", venue:{bar:1}, rank:37},
  {id:"cereal-crew", title:"Cereal Crew", blurb:"Solid-color clothes plus a cereal-box front you decorate.", why:"Everyone designs their own box, and the breakfast lineup is adorable.", audience:["family","group","class"], budget:["diy","low"], tags:{cute:3,simple:2,crafty:2,food:2,occparty:2,occtreat:1,occparade:2}, fit:"U", venue:{bar:2}, rank:38},
  {id:"decades-crew", title:"Decades Crew", blurb:"Each person picks a decade and dresses from their own closet.", why:"Everyone gets their own era, and the decades together look intentional.", audience:["group","family","class"], budget:["diy","low"], tags:{funny:2, simple:2, couch:2, crafty:1,occbar:1,occparty:2,occparade:2}, fit:"U", venue:{bar:2}, rank:39},
  {id:"under-the-sea", title:"Under the Sea", blurb:"Jellyfish from an umbrella with ribbon tentacles, crab from red clothes and claw mittens, plus fish, seaweed, and waves.", why:"The go-all-out family theme; every age can scale their part up or down.", audience:["family","class"], budget:["diy","low"], tags:{cute:3,allout:2,crafty:1,kid36:1,animals:2,occparty:2,occtreat:1,occparade:2}, fit:"U", venue:{bar:1}, rank:40, roles:{kid:["the jellyfish","the crab"],adult:["a fish","seaweed","a wave"]}},
  {id:"dino-rangers", title:"Dino Rangers", blurb:"Khaki outfits for the grown-ups, dino hoods for the kids. Leash a toy raptor.", why:"The kids get to be dinosaurs; that's the whole sell.", audience:["family","class"], budget:["low","mid"], tags:{funny:2,cute:2,couch:1,simple:1,crafty:2,dinos:3,occtreat:2,occparade:2}, fit:"U", venue:{bar:2}, rank:41, roles:{kid:["a dino"],adult:["a ranger"]}},
  {id:"board-game-pieces", title:"Board Game Pieces", blurb:"Each person picks a piece: cardboard die, playing card, pawn, or domino over monochrome clothes.", why:"Everyone recognizes every piece, and the group looks like a set.", audience:["group","class"], budget:["diy","low"], tags:{funny:2,cute:1,crafty:1,games:2,occbar:1,occparty:2,occparade:2}, fit:"U", venue:{bar:1}, rank:42, roles:{kid:["the pawn","the playing card"],adult:["the cardboard die","the domino"]}},
  {id:"rain-cloud-rainbow", title:"Rain Cloud and Rainbow", blurb:"One wears gray with cotton clouds and paper raindrops; the other wears rainbow stripes.", why:"The two costumes clearly belong together without matching outfits.", audience:["couple"], budget:["diy","low"], tags:{couch:2,cute:3,matchyes:2,simple:1,occparty:2,occtreat:1}, fit:"U", venue:{bar:2}, rank:43},
  {id:"doctor-bride", title:"The Doctor & the Bride", blurb:"Green face paint and neck bolts for one; tall streaked wig and torn gown for the other.", why:"The classic monster duo: scary, cheap, and everyone knows who you are.", audience:["couple"], budget:["diy","low"], tags:{tv:2,scary:3,funny:1,simple:2,couch:1,matchyes:2,occbar:2,occparty:2}, fit:"U", venue:{bar:2}, rank:44},
  {id:"breakfast-buffet", title:"Breakfast Buffet", blurb:"Everyone picks a breakfast: egg, bacon, toast, pancake, OJ, coffee. Cardboard signs over normal clothes.", why:"Scales to any group size and nobody needs a full costume.", audience:["family","group","class"], budget:["diy","low"], tags:{couch:2,funny:3,simple:1,food:2,occparty:2,occtreat:1,occparade:2}, fit:"U", venue:{bar:2}, rank:45, roles:{kid:["the egg","the pancake"],adult:["the bacon","the coffee"]}},
  {id:"ghost-hunters", title:"Ghost Hunters", blurb:"Khaki jumpsuits, cardboard ghost-catching backpacks, name patches.", why:"Paranormal investigators for the night. Scare each other all night.", audience:["group","family"], budget:["mid","diy"], tags:{funny:2,scary:1,crafty:1,tv:3,occparty:1,occtreat:2}, fit:"U", venue:{bar:1}, rank:46},
  {id:"haunted-animatronics", title:"Haunted Animatronics", blurb:"Glitchy mascot heads from cardboard boxes, flickering LED eyes, jerky moves.", why:"Scary-funny in a group, and the photo booth line will find you.", audience:["group"], budget:["diy","mid"], tags:{scary:2,funny:2,crafty:2,allout:1,games:2,occbar:2,occparty:2}, fit:"U", venue:{bar:0}, rank:47},
  {id:"mystery-crew", title:"Mystery Crew", blurb:"Assign the leader, the style icon, the brains, the goofball, and one very good dog.", why:"Everyone gets a character and the dog steals the show.", audience:["group","family","class"], budget:["diy","mid"], tags:{couch:2,cute:3,funny:1,tv:3,occparty:2,occtreat:1,occparade:2}, fit:"U", venue:{bar:2}, rank:48, roles:{kid:["the goofball","the very good dog"],adult:["the leader","the brains","the style icon"]}},
  {id:"headless-horsemen", title:"Headless Horsemen", blurb:"Black capes, jack-o-lanterns held at shoulder height, group gallop.", why:"The visual is unreal in photos, and the bit is just walking menacingly together.", audience:["group"], budget:["low","diy"], tags:{couch:2,scary:2,funny:1,occbar:2,occparty:1}, fit:"M", venue:{bar:1}, rank:49},
  {id:"haunted-portraits", title:"Haunted Portraits", blurb:"Gray makeup, old-timey clothes, hold a gilt frame.", why:"Spooky, artsy, and you just stand still.", audience:["couple","group","family"], budget:["diy","mid"], tags:{allout:2,scary:2,crafty:2,matchloose:2,occbar:1,occparty:2}, fit:"U", venue:{bar:2}, rank:50},
  {id:"goggle-crew", title:"Goggle Crew", blurb:"Yellow tees, denim overalls, goggles, black gloves.", why:"Group chaos in its purest form, and overalls are just useful.", audience:["group","family","class"], budget:["low","mid"], tags:{couch:2,cute:2,funny:1,tv:3,occparty:1,occtreat:2,occparade:2}, fit:"U", venue:{bar:2}, rank:51},
  {id:"garden-gnome", title:"Garden Gnome", blurb:"Wear earth tones, make a pointy hat from cardboard, draw a white beard, carry a tiny fishing rod or garden shovel.", why:"Big silhouette, tiny fishing rod: the proportions are the whole joke.", audience:["solo"], budget:["diy","low"], tags:{couch:2,funny:2,simple:2,cute:1,occcandy:2,occlowkey:2}, fit:"M", venue:{bar:2}, rank:52},
  {id:"black-cat", title:"Black Cat Burglar", blurb:"Black sweatsuit, cat-ear headband, eye mask. Add a toy sack for burglar.", why:"Warm, cheap, and the ears do all the work.", audience:["solo"], budget:["low"], tags:{cute:2,funny:1,couch:3,simple:2,animals:3,occbar:2,occcandy:1,occlowkey:1}, fit:"F", venue:{bar:0}, rank:53},
  {id:"block-monster", title:"Block Monster", blurb:"Wear all one solid color, square up your silhouette with foam or cardboard blocks on shoulders/limbs, draw a pixelated face.", why:"Video game people recognize it instantly, pure geometry, works at any scale.", audience:["solo"], budget:["low","diy"], tags:{funny:2,couch:2,simple:1,crafty:2,games:3,occbar:1,occparty:2}, fit:"U", venue:{bar:1}, rank:54},
  {id:"space-crewmate", title:"Space Crewmate", blurb:"Colored sweatsuit plus a cardboard backpack.", why:"One shopping trip and you're done.", audience:["solo"], budget:["low"], tags:{funny:3,couch:3,simple:2,games:3,occbar:1,occlowkey:1,occparty:2}, fit:"U", venue:{bar:1}, rank:55},
  {id:"sun-moon", title:"Sun and Moon", blurb:"One in yellow with cardboard rays, one in navy with paper stars and a crescent.", why:"Two faces, one night: simple paint, big charm.", audience:["couple"], budget:["diy"], tags:{couch:2,cute:3,matchyes:2,simple:1,occlowkey:1,occparty:2}, fit:"U", venue:{bar:1}, rank:56},
  {id:"moth-porch-light", title:"Moth and Porch Light", blurb:"One wears neutrals with cardboard wings; the other wears yellow and carries a lampshade.", why:"The joke lands in one second and it builds in under an hour.", audience:["couple"], budget:["diy"], tags:{funny:3,crafty:1,matchyes:2,animals:1,occcandy:1,occparty:2}, fit:"U", venue:{bar:1}, rank:57},
  {id:"raptor-ranger", title:"Raptor & Ranger", blurb:"One khaki ranger, one green dino hood. The ranger holds the leash.", why:"Funny from across the parking lot.", audience:["couple"], budget:["low"], tags:{funny:3,couch:2,simple:1,matchyes:2,dinos:3,occparty:2,occtreat:1}, fit:"U", venue:{bar:2}, rank:58},
  {id:"cat-mouse", title:"Cat & Mouse", blurb:"Cat ears versus mouse ears. Spend the night chasing each other.", why:"Built-in party game, no props beyond the ears.", audience:["couple"], budget:["low"], tags:{funny:3,cute:2,couch:2,simple:2,matchyes:2,animals:2,occcandy:1,occparty:2}, fit:"U", venue:{bar:2}, rank:59},
  {id:"ketchup-mustard", title:"Ketchup & Mustard", blurb:"Red bottle tunic and cap for one, yellow for the other.", why:"The couple costume everyone recognizes from across the room.", audience:["couple"], budget:["diy","low"], tags:{funny:3,couch:2,matchyes:2,food:2,occbar:1,occparty:2}, fit:"U", venue:{bar:2}, rank:60},
  {id:"plumber-duo", title:"Plumber Duo", blurb:"Overalls, red and green caps and shirts, drawn mustaches.", why:"Matching without being cheesy, and the mustaches do the talking.", audience:["couple","family"], budget:["mid","diy"], tags:{couch:2,cute:2,funny:1,matchyes:2,games:2,occparty:1,occtreat:2}, fit:"M", venue:{bar:2}, rank:61, roles:{kid:["the green plumber"],adult:["the red plumber"]}},
  {id:"office-couple", title:"Office Couple", blurb:"White shirts, name tags, and a teapot. The office's finest.", why:"Instantly readable, and you can wear it to the office party.", audience:["couple"], budget:["low"], tags:{funny:3,couch:2,simple:2,matchyes:2,tv:3,occbar:2,occparty:2}, fit:"U", venue:{bar:2}, rank:62},
  {id:"burger-joint-couple", title:"Burger Joint Couple", blurb:"White apron plus fake mustache, curly red wig plus glasses. Burger shop owners.", why:"A couples costume people actually recognize across the room.", audience:["couple"], budget:["low"], tags:{funny:3,cute:1,couch:2,simple:2,matchyes:2,tv:3,food:2,occbar:1,occparty:2}, fit:"U", venue:{bar:2}, rank:63},
  {id:"plug-socket", title:"Plug and Socket", blurb:"Cardboard plug and outlet worn front and back.", why:"Peak pun-couple energy, built from boxes in an afternoon.", audience:["couple"], budget:["diy"], tags:{funny:3,crafty:2,matchyes:2,occbar:1,occparty:2}, fit:"U", venue:{bar:1}, rank:64},
  {id:"lost-tourist", title:"Lost Tourist", blurb:"Wear wrinkled clothes, carry a crumpled map, add one luggage tag backwards on your shoulder.", why:"Relatable, needs only closet pieces, instantly funny to wear.", audience:["solo"], budget:["diy","low"], tags:{funny:3,couch:2,simple:1,occbar:2,occcandy:1,occparty:1}, fit:"U", venue:{bar:2}, rank:66},
  {id:"tooth-fairy", title:"Tooth and Tooth Fairy", blurb:"One all-white with a cardboard tooth outline; the other adds wings and an envelope of tooth money.", why:"An obvious pair, playful instead of elaborate.", audience:["couple"], budget:["diy"], tags:{couch:2,funny:2,cute:2,matchyes:1,occparty:1,occtreat:1}, fit:"F", venue:{bar:1}, rank:67},
  {id:"web-hero-duo", title:"Web Hero Duo", blurb:"Red-blue sweatsuit plus web mask; partner gets the black jacket and attitude.", why:"Classic duo with zero sewing required.", audience:["couple"], budget:["low"], tags:{cute:2,funny:1,couch:2,simple:2,matchyes:2,heroes:3,tv:2,occbar:1,occparty:2}, fit:"U", venue:{bar:0}, rank:68},
  {id:"plague-doctor", title:"Plague Doctor", blurb:"Long coat, wide hat, beaked mask.", why:"Genuinely unsettling and you get to keep the mask for years.", audience:["solo"], budget:["mid","high"], tags:{scary:3,allout:2,occbar:3,occparty:1}, fit:"M", venue:{bar:0}, rank:69},
  {id:"crowd-camouflage", title:"Crowd Camouflage", blurb:"Gray hoodie, dark pants, blank expression. Vanish into any crowd.", why:"Six of you walk in dressed identically. Nobody knows who arrived with whom.", audience:["solo"], budget:["diy","low"], tags:{couch:2,simple:3,funny:1,occbar:1,occlowkey:2,occparty:1}, fit:"U", venue:{bar:2}, rank:70},
  {id:"error-404", title:"Error 404", blurb:"Wear all black with a blank white page taped to your chest; carry a phone with a cracked-screen prop.", why:"Instantly readable, tech crowd gets it, non-tech crowd gets it anyway.", audience:["solo"], budget:["diy"], tags:{funny:2,couch:3,simple:2,occbar:2,occlowkey:1,occparty:1}, fit:"U", venue:{bar:2}, rank:71},
  {id:"zombie-coworker", title:"Zombie Coworker", blurb:"Torn button-down, loosened tie, pale makeup, coffee mug.", why:"Scary with zero shopping: it's just your work clothes, ruined.", audience:["solo"], budget:["diy"], tags:{couch:2,scary:2,funny:1,make:2,occbar:2,occparty:2}, fit:"U", venue:{bar:2}, rank:72},
  {id:"the-olympians", title:"The Olympians", blurb:"Bedsheet togas, gold rope belts, laurel crowns. Pick your god: lightning bolt, owl, or trident.", why:"Greek myth went cinematic again this year, and a bedsheet toga is the cheapest epic costume ever made.", audience:["group","couple","family","class"], budget:["diy","low"], tags:{heroes:3,tv:2,allout:1,cute:1,funny:1,crafty:2,occparty:2,occbar:1,occparade:2}, fit:"U", venue:{bar:1}, rank:65, trending:true, trendLane:"Greek myth", trendStat:"Odyssey year", roles:{kid:["the owl god","the trident god"],adult:["the lightning god"]}},
  {id:"safari-photographer", title:"Safari Photographer", blurb:"Khaki vest, toy camera and binoculars, plus a stuffed lion cub under one arm.", why:"The camera does the talking, and the plush cub steals every photo.", audience:["solo"], budget:["diy","low"], tags:{funny:2,cute:2,couch:2,simple:1,animals:3,occcandy:1,occparty:1,occtreat:1}, fit:"U", venue:{bar:2}, rank:73},
  {id:"player-one-two", title:"Player One & Two", blurb:"Matching tees with 1 and 2, toy controllers in hand, ready for co-op.", why:"Zero sewing, instantly readable, and the controllers are the whole joke.", audience:["couple"], budget:["diy","low"], tags:{funny:3,couch:2,simple:2,matchyes:2,games:3,occbar:1,occparty:2}, fit:"U", venue:{bar:2}, rank:74},
  {id:"dinosaur-family", title:"Dinosaur Family", blurb:"Matching dino-hoodie sweatsuits for the whole crew, spikes down every back.", why:"Matching dino hoodies need zero coordination, and the spikes sell it from far away.", audience:["family","class"], budget:["low","diy"], tags:{cute:3,funny:1,couch:2,simple:2,dinos:3,occtreat:2,occparade:2}, fit:"U", venue:{bar:1}, rank:75},
  {id:"snow-sisters", title:"Ice Kingdom Crew", blurb:"The ice queen, the snow princess, the talking snowman, the reindeer: pick your role.", why:"The family costume every kid already knows by heart, and the snowman is basically pajamas.", audience:["family","group","kid","class"], budget:["diy","low"], tags:{cute:3,simple:2,couch:1,crafty:1,kidunder3:1,kid36:2,kid7plus:2,princess:3,tv:2,occparty:2,occtreat:2,occparade:2}, fit:"F", venue:{bar:1}, rank:76, roles:{kid:["the ice queen","the snow princess"],adult:["the talking snowman","the reindeer"]}},
  {id:"sushi-roll", title:"Sushi Roll", blurb:"A white-sheet wrap with felt salmon and pom-pom wasabi. Chopsticks optional.", why:"It turns bedsheets into the most photogenic thing at the party.", audience:["solo"], budget:["diy"], tags:{cute:2,crafty:2,food:2,occparty:2}, fit:"U", venue:{bar:2}, rank:77},
  {id:"deviled-egg", title:"Deviled Egg", blurb:"White shirt with a felt yolk, devil horns, and a red tail. Half egg, half devil.", why:"The yolk-and-horns combo reads from twenty feet away with zero explaining.", audience:["solo"], budget:["diy"], tags:{funny:2,couch:2,food:2,occbar:2}, fit:"U", venue:{bar:2}, rank:78},
  {id:"pizza-slice", title:"Pizza Slice", blurb:"A big cardboard triangle, painted golden with felt pepperoni.", why:"Cardboard and felt become the rare costume kids and adults both reach for.", audience:["solo","kid"], budget:["diy"], tags:{funny:2,crafty:2,kid36:2,food:2,occtreat:2,occparade:2}, fit:"U", venue:{bar:1}, rank:79},
  {id:"popcorn-bucket", title:"Popcorn Bucket", blurb:"A striped cardboard-box body with balloon popcorn on top.", why:"The balloon popcorn bounces when they walk, which sells the whole thing.", audience:["kid"], budget:["diy"], tags:{cute:2,crafty:2,kid36:2,food:2,occtreat:2,occparade:2}, fit:"U", venue:{bar:1}, rank:80},
  {id:"ice-cream-cone", title:"Ice Cream Cone", blurb:"A tan paper cone hat and a sprinkle-dotted scoop shirt.", why:"Three cheap pieces read as ice cream instantly, no explanation needed.", audience:["kid","solo"], budget:["diy"], tags:{cute:2,couch:2,kid36:2,food:2,occparty:2,occparade:2}, fit:"U", venue:{bar:2}, rank:81},
  {id:"pbj", title:"Peanut Butter & Jelly", blurb:"One in brown with a PB label, one in purple with a J label.", why:"Two solid-color outfits and two labels make the most recognizable duo in the room.", audience:["couple"], budget:["diy"], tags:{funny:2,couch:2,food:2,occparty:2}, fit:"U", venue:{bar:2}, rank:82},
  {id:"bacon-eggs", title:"Bacon & Eggs", blurb:"Wavy bacon stripes and a sunny-side-up egg yolk.", why:"The wavy bacon stripes make the pair readable from across the room.", audience:["couple"], budget:["diy"], tags:{funny:2,couch:2,food:2,occcandy:2}, fit:"U", venue:{bar:2}, rank:83},
  {id:"peas-pod", title:"Peas in a Pod", blurb:"Green shirts in a row under one long felt pod sash.", why:"The shared sash turns any group into one costume people actually remember.", audience:["family","group","class"], budget:["diy"], tags:{cute:2,allout:2,food:2,occparty:2,occparade:2}, fit:"U", venue:{bar:2}, rank:84},
  {id:"basketball-star", title:"Basketball Star", blurb:"Jersey, shorts, eye-black stripes, and a ball that never leaves your hand.", why:"Real gear plus one theatrical touch beats a store-bought uniform.", audience:["solo","kid"], budget:["diy"], tags:{simple:2,couch:2,kid7plus:2,sports:2,occparty:2,occparade:2}, fit:"U", venue:{bar:2}, rank:85},
  {id:"referee", title:"Referee", blurb:"A striped shirt, a whistle, and a yellow penalty flag.", why:"The whistle gives you a bit to perform instead of just standing around.", audience:["solo","group","class"], budget:["low","diy"], tags:{funny:2,couch:2,sports:2,occparty:2,occparade:2}, fit:"U", venue:{bar:2}, rank:86},
  {id:"boxer", title:"Boxer", blurb:"Bathrobe, toy gloves, bruise makeup, and entrance music.", why:"The entrance music does half the work before a single punch is thrown.", audience:["solo"], budget:["diy"], tags:{funny:2,couch:2,sports:2,occbar:2}, fit:"M", venue:{bar:1}, rank:87},
  {id:"cheerleader", title:"Cheerleader", blurb:"Team colors and pom-poms made from cut plastic bags.", why:"Homemade pom-poms and a chant beat a store costume for half the price.", audience:["kid"], budget:["diy"], tags:{cute:2,crafty:2,kid36:2,sports:2,occtreat:2,occparade:2}, fit:"F", venue:{bar:2}, rank:88},
  {id:"tennis-duo", title:"Tennis Duo", blurb:"All-white outfits, headbands, toy rackets, and a tube of balls.", why:"The all-white dress code makes two people look like a team instantly.", audience:["couple"], budget:["low","diy"], tags:{simple:2,couch:2,sports:2,occlowkey:2}, fit:"U", venue:{bar:2}, rank:89},
  {id:"bowling-pins", title:"Bowling Pins", blurb:"White outfits with red neck stripes, plus one bowler in black.", why:"The bowler-and-pins bit gives the group something to do all night.", audience:["group","family","class"], budget:["diy"], tags:{funny:2,crafty:2,sports:2,occparty:2,occparade:2}, fit:"U", venue:{bar:2}, rank:90, roles:{kid:["a bowling pin"],adult:["the bowler"]}},
  {id:"cardboard-knight", title:"Cardboard Knight", blurb:"Silver-painted cardboard armor and a pool-noodle sword.", why:"Spray paint turns moving boxes into armor that looks genuinely cool.", audience:["solo","kid"], budget:["diy"], tags:{funny:2,allout:2,kid7plus:2,heroes:3,occtreat:2,occparade:2}, fit:"U", venue:{bar:1}, rank:91},
  {id:"ninja", title:"Ninja", blurb:"All black with a belt sash and a slit headband.", why:"One headband turns pajamas into a stealth mission.", audience:["kid","solo"], budget:["diy"], tags:{scary:2,couch:2,kid36:2,occtreat:2}, fit:"U", venue:{bar:1}, rank:92},
  {id:"caped-duo", title:"Caped Duo", blurb:"Matching sheet capes, felt masks, and your own emblems.", why:"Matching emblems make it yours instead of a store superhero.", audience:["couple"], budget:["diy"], tags:{funny:2,crafty:2,heroes:3,occparty:2}, fit:"U", venue:{bar:2}, rank:93},
  {id:"hero-squad", title:"Hero Squad", blurb:"Color-coded capes and masks, one team pose for photos.", why:"Color-coded capes make a big group look coordinated with almost no sewing.", audience:["group","class"], budget:["diy"], tags:{funny:2,allout:2,heroes:3,occparty:2,occparade:2}, fit:"U", venue:{bar:2}, rank:94},
  {id:"astronaut", title:"Astronaut", blurb:"White sweats, a paper-bag helmet, and a flag patch.", why:"The paper-bag helmet is the whole trick and it actually works.", audience:["solo"], budget:["diy"], tags:{simple:2,couch:2,occbar:2}, fit:"U", venue:{bar:0}, rank:95},
  {id:"robot-ranger", title:"Robot Ranger", blurb:"Silver boxes, dryer-vent arms, and sticker dials.", why:"Boxes and stickers build a robot that moves and beeps on command.", audience:["kid","family"], budget:["diy"], tags:{cute:2,allout:2,kid36:2,occtreat:2,occparade:2}, fit:"U", venue:{bar:1}, rank:96},
  {id:"penguin-huddle", title:"Penguin Huddle", blurb:"Black shirts, felt bellies, beak headbands. Waddle together.", why:"The group waddle is funnier than any single penguin could be.", audience:["group","class"], budget:["diy"], tags:{funny:2,couch:2,animals:2,occparty:2,occparade:2}, fit:"U", venue:{bar:2}, rank:97},
  {id:"prince-princess", title:"Prince & Princess", blurb:"A crown and cape, a thrifted gown and tiara.", why:"Thrifted velvet reads richer than a plastic packaged costume.", audience:["couple"], budget:["low","diy"], tags:{cute:2,couch:2,princess:3,occbar:2}, fit:"U", venue:{bar:2}, rank:98},
  {id:"dino-herd", title:"Dino Herd", blurb:"Green ponchos with felt spikes and stuffed-sock tails.", why:"A line of stomping dinos gets a bigger reaction than one T-Rex alone.", audience:["group"], budget:["diy"], tags:{scary:2,crafty:2,dinos:2,occtreat:2}, fit:"U", venue:{bar:2}, rank:99},
  {id:"pixel-ghost", title:"Pixel Ghost", blurb:"A white sheet cut in chunky pixel squares with felt eyes.", why:"The zigzag pixel edge makes a sheet ghost feel brand new.", audience:["kid"], budget:["diy"], tags:{scary:2,crafty:2,kid36:2,games:3,occtreat:2}, fit:"U", venue:{bar:1}, rank:100},
  {id:"spaghetti-meatball", title:"Spaghetti & Meatball", blurb:"White shirt with yarn spaghetti glued on, brown pom-pom meatballs.", why:"Dinner you can wear, and the yarn survives the washing machine.", audience:["kid"], budget:["diy"], tags:{cute:2,couch:2,kid36:2,kidunder3:1,food:2,occtreat:2,occparade:2}, fit:"U", venue:{bar:2}, rank:101},
  {id:"cupcake", title:"Cupcake", blurb:"Brown tunic for the wrapper, white pillowcase for frosting, cherry on top.", why:"A pillowcase becomes frosting, which means the whole costume costs almost nothing.", audience:["kid"], budget:["diy"], tags:{cute:2,crafty:2,kid36:2,food:2,occtreat:2,occparty:1,occparade:2}, fit:"U", venue:{bar:2}, rank:102},
  {id:"banana", title:"Banana", blurb:"Yellow sweatsuit with a green felt stem hat.", why:"A single color all over, and the green stem hat makes it read instantly in photos.", audience:["kid","solo"], budget:["low"], tags:{funny:2,couch:2,kid36:2,food:2,occtreat:2,occparade:2}, fit:"U", venue:{bar:1}, rank:103},
  {id:"hot-dog", title:"Hot Dog", blurb:"Tan foam pool noodle bun, red shirt for the dog, mustard squiggle.", why:"Pool noodles were made for this costume, and you can actually sit down in it.", audience:["solo"], budget:["diy"], tags:{funny:2,couch:2,food:2,occparty:2,occbar:1}, fit:"U", venue:{bar:1}, rank:104},
  {id:"donut", title:"Donut", blurb:"Pink cardboard ring with sprinkles, worn like a sandwich board.", why:"Cardboard and pink paint, and the sprinkle pattern hides every brush mistake.", audience:["solo","kid"], budget:["diy"], tags:{cute:2,couch:2,kid36:2,food:2,occparty:2,occparade:2}, fit:"U", venue:{bar:1}, rank:105},
  {id:"coffee-cup", title:"Coffee Cup", blurb:"White trash bag over a cardboard tube, brown lid hat.", why:"The cardboard lid hat does the heavy lifting in every photo.", audience:["solo"], budget:["diy"], tags:{funny:2,couch:2,food:2,occbar:2,occparty:1}, fit:"U", venue:{bar:1}, rank:106},
  {id:"salt-pepper", title:"Salt & Pepper", blurb:"White and black outfits with shaker tops made from cardboard.", why:"The couple costume that never misses, and it packs flat for the ride over.", audience:["couple"], budget:["diy"], tags:{cute:2,couch:2,matchyes:2,food:2,occparty:2}, fit:"U", venue:{bar:2}, rank:107},
  {id:"fruit-salad", title:"Fruit Salad Crew", blurb:"Each person picks a fruit color, wears it head to toe with a leaf hat.", why:"Everyone picks their own fruit, so nobody argues about who gets to be what.", audience:["family","group","class"], budget:["low"], tags:{cute:2,crafty:2,food:2,occparty:2,occparade:2}, fit:"U", venue:{bar:2}, rank:108},
  {id:"wizard", title:"Classic Wizard", blurb:"Tall black pointy hat, flowing plain black robe, tall straight wooden staff, gray beard optional.", why:"The most recognizable silhouette in Halloween, and nearly all of it comes from a closet plus a craft store run.", audience:["solo","group"], budget:["diy","low"], tags:{scary:2,crafty:2,couch:1,allout:1,simple:1,occparty:2,occbar:2,occtreat:1,occlowkey:1}, fit:"U", venue:{bar:1}, rank:109},
  {id:"toy-box-crew", title:"Toy Box Crew", blurb:"A cowboy sheriff, a space ranger, and the rest of the toy box: pick your favorite.", why:"The sheriff and the space ranger arguing over who is the favorite toy. Two roles everyone recognizes instantly.", audience:["family","group","class"], budget:["diy","low"], tags:{cute:3,funny:1,couch:2,simple:2,kid36:2,kid7plus:2,tv:3,occtreat:2,occparty:2,occparade:2}, fit:"U", venue:{bar:2}, rank:110, roles:{kid:["the cowboy sheriff","the space ranger"],adult:["another toy from the box"]}},
  {id:"demon-boy-band", title:"Demon Boy Band", blurb:"Matching streetwear-idol outfits with glowing patterns for your whole boy band.", why:"Matching stage outfits, glowing patterns, and a synchronized dance break. The group photo basically takes itself.", audience:["group"], budget:["diy","mid"], tags:{allout:2,cute:2,funny:1,tv:3,occparty:3,occbar:1,matchyes:2}, fit:"U", venue:{bar:2}, rank:111},
  {id:"dragon-rider-duo", title:"Dragon Rider Duo", blurb:"A viking rider and a cardboard dragon, ready to fly over the neighborhood.", why:"One viking rider, one dragon built from a cardboard box. The dragon gets more compliments than the rider.", audience:["couple","family"], budget:["diy","low"], tags:{cute:2,funny:1,crafty:2,couch:1,simple:1,tv:2,kid36:1,occtreat:2,occparty:1,matchyes:2}, fit:"U", venue:{bar:1}, rank:112, roles:{kid:["the dragon"],adult:["the viking rider"]}},
  {id:"numbered-players", title:"Numbered Players", blurb:"Green tracksuits, numbered bibs, and a survival-game attitude.", why:"Green tracksuits and numbered bibs, ready for playground games. The dalgona cookie is the prop people talk about.", audience:["group"], budget:["diy","low"], tags:{funny:2,cute:1,simple:2,couch:2,tv:3,occparty:2,occbar:1,matchyes:3}, fit:"U", venue:{bar:2}, rank:113},
  {id:"emotion-crew", title:"Emotion Crew", blurb:"One loud color per person: each of you is a different emotion.", why:"Each person picks an emotion and wears one loud color head to toe. The lineup reads as one big feeling from the doorway.", audience:["group","family","class"], budget:["diy","low"], tags:{cute:3,funny:2,couch:2,simple:2,kid36:2,kid7plus:1,tv:2,occparty:2,occtreat:2,matchyes:2,occparade:2}, fit:"U", venue:{bar:2}, rank:114, roles:{kid:["the happy one","the sad one"],adult:["the angry one","the scared one","the disgusted one"]}},
  {id:"kart-racers", title:"Kart Racers", blurb:"Cardboard karts and racing caps for a full starting grid of friends.", why:"Your crew lined up like a starting grid, engines revving with mouth sounds. The build fits in one afternoon.", audience:["group","class"], budget:["diy","low"], tags:{funny:2,cute:2,crafty:2,games:3,tv:2,occparty:2,matchyes:2,occparade:2}, fit:"U", venue:{bar:1}, rank:115},
  {id:"tall-hat-crew", title:"Tall Hat Crew", blurb:"A striped stovepipe hat, a bow tie, and two wild blue-haired Things.", why:"The striped hat does most of the work. The Things just need blue wigs, red suits, and permission to cause trouble.", audience:["family","group","class"], budget:["diy","low"], tags:{cute:3,funny:2,couch:2,simple:2,kid36:2,kid7plus:1,tv:2,occtreat:2,occparty:1,occparade:2}, fit:"U", venue:{bar:2}, rank:116, roles:{kid:["a blue-haired Thing"],adult:["the tall-hatted cat"]}},
  {id:"chipmunk-trio", title:"Chipmunk Trio", blurb:"Letter sweaters, felt ears, and whiskers for a singing trio of chipmunks.", why:"Sweaters with big letters, felt ears, and drawn whiskers. The three-part harmony is optional but encouraged.", audience:["group","family","class"], budget:["diy","low"], tags:{cute:3,funny:2,couch:2,simple:2,kid36:2,kid7plus:2,tv:2,occtreat:2,occparty:2,matchyes:2,occparade:2}, fit:"U", venue:{bar:2}, rank:117},
  {id:"galaxy-knights", title:"Galaxy Knights", blurb:"Robes, belts, and toy energy blades for knights of a far-off galaxy.", why:"Robe, belt, and a toy energy blade. Two stances and the photo looks like a movie poster.", audience:["group","solo","couple","class"], budget:["diy","mid"], tags:{allout:1,cute:1,couch:2,simple:2,tv:3,occparty:2,occbar:1,matchyes:2,occparade:2}, fit:"U", venue:{bar:1}, rank:118},
  {id:"plastic-dream-crew", title:"Plastic Dream Crew", blurb:"Head-to-toe pink outfits with plastic accessories for the dream crew.", why:"All pink, head to toe, no notes. The matching sunglasses turn four friends into one unmistakable photo.", audience:["group","couple","class"], budget:["diy","low"], tags:{cute:3,funny:1,couch:2,simple:2,tv:2,occparty:2,matchyes:3,occparade:2}, fit:"U", venue:{bar:2}, rank:119},
  {id:"extinct-party-animal", title:"Extinct Party Animal", blurb:"Felt dino spikes on a normal jacket, plus a party hat and a badge that reads Last seen 66 million years ago.", why:"A punchline you wear: the extinct-for-66-million-years badge gets the laugh before you say a word.", audience:["solo"], budget:["diy","low"], tags:{crafty:2,dinos:3,funny:3,occparty:2,occbar:2}, fit:"U", venue:{bar:2}, rank:120},
  {id:"dino-tourist", title:"Dino Tourist", blurb:"Hawaiian shirt, dino tail, camera around your neck, and a fanny pack. The meteor missed this one.", why:"A dinosaur on vacation is inherently ridiculous, and the fanny pack sells it.", audience:["solo"], budget:["diy","low"], tags:{couch:2,simple:1,dinos:2,funny:3,occparty:2,occbar:2}, fit:"U", venue:{bar:2}, rank:121},
  {id:"raptor-barista", title:"Raptor Barista", blurb:"Green hoodie with a dino snout hood, tiny T. rex arms strapped on, and a coffee cup you can barely hold.", why:"The tiny arms are the whole bit: watching a raptor struggle with a latte never gets old.", audience:["solo"], budget:["diy","low"], tags:{couch:2,simple:1,dinos:3,funny:3,occparty:2,occbar:2}, fit:"U", venue:{bar:2}, rank:122},
  {id:"emotional-support-dinosaur", title:"Emotional Support Dinosaur", blurb:"Dino-spike vest over normal clothes with a badge that says Emotional Support Dinosaur. Do not pet.", why:"The vest turns a known internet joke into a costume, and strangers will read it out loud all night.", audience:["solo"], budget:["diy","low"], tags:{couch:2,dinos:2,funny:3,occparty:2,occbar:2}, fit:"U", venue:{bar:2}, rank:123},
  {id:"garden-fairy", title:"Garden Fairy", blurb:"Tulle wings, a flower crown, and a wand: the backyard turns into a fairy tale.", why:"She picks the wing color, and the wand is just a stick with a star on it.", audience:["kid"], budget:["diy","low"], tags:{cute:3,crafty:2,kid36:2,kid7plus:1,princess:2,occtreat:2,occparty:1,occparade:2}, fit:"F", venue:{bar:1}, rank:124},
  {id:"ballerina", title:"Ballerina", blurb:"A tulle tutu tied onto elastic, a leotard, and a neat ballerina bun.", why:"The tutu needs no sewing, and the twirl does the rest.", audience:["kid"], budget:["low","diy"], tags:{cute:3,simple:2,crafty:1,couch:1,kid36:2,kid7plus:2,occtreat:2,occparty:2,occparade:2}, fit:"F", venue:{bar:1}, rank:125},
  {id:"butterfly", title:"Butterfly", blurb:"Painted cardboard wings on black sweats: the garden's prettiest visitor.", why:"The wings fold flat for the car ride and open wide for photos.", audience:["kid"], budget:["diy","low"], tags:{cute:3,crafty:2,kid36:2,kidunder3:1,animals:2,occtreat:2,occparade:2}, fit:"F", venue:{bar:1}, rank:126},
  {id:"pop-star", title:"Pop Star", blurb:"A sparkly jacket, a toy microphone, and the biggest hair in the room.", why:"Hand her the mic and the living room becomes a stadium.", audience:["kid"], budget:["low","diy"], tags:{cute:3,funny:2,simple:2,couch:1,kid36:2,kid7plus:2,occparty:2,occtreat:1,occparade:2}, fit:"F", venue:{bar:1}, rank:127},
  {id:"ice-skater", title:"Ice Skater", blurb:"A white dress, tights, and a perfect bun: gold-medal energy, no ice required.", why:"The bun and the spin sell it; the dress can come straight from the closet.", audience:["kid"], budget:["low","diy"], tags:{cute:3,simple:2,couch:2,kid36:2,kid7plus:1,sports:2,occtreat:2,occparade:2}, fit:"F", venue:{bar:1}, rank:128},
  {id:"ladybug", title:"Ladybug", blurb:"Red sweats, black felt dots, and little spotted wings.", why:"Felt circles do all the work, and it is warm enough for a real October night.", audience:["kid"], budget:["diy","low"], tags:{cute:3,crafty:1,simple:1,kidunder3:2,kid36:2,animals:2,occtreat:2,occparade:2}, fit:"F", venue:{bar:1}, rank:129},
  {id:"daisy", title:"Daisy", blurb:"A yellow petal headband and a green dress: a walking flower.", why:"The petals are craft foam, and she chooses the middle color herself.", audience:["kid"], budget:["diy","low"], tags:{cute:3,simple:2,crafty:1,couch:1,kidunder3:3,kid36:2,occtreat:2,occparade:2}, fit:"F", venue:{bar:1}, rank:130},
  {id:"little-baker", title:"Little Baker", blurb:"A paper chef hat, an apron, and a toy whisk.", why:"The hat is one paper circle away, and the whisk doubles as a wand.", audience:["kid"], budget:["diy","low"], tags:{cute:2,funny:2,crafty:2,kid36:2,kid7plus:1,food:2,occtreat:2,occparade:2}, fit:"F", venue:{bar:1}, rank:131},
  {id:"little-artist", title:"Little Artist", blurb:"A beret, a cardboard paint palette, and a splatter-painted smock.", why:"The messier the smock looks, the more convincing the artist.", audience:["kid"], budget:["diy","low"], tags:{cute:3,crafty:2,funny:2,kid36:2,kid7plus:2,occtreat:2,occparty:1,occparade:2}, fit:"F", venue:{bar:1}, rank:132},
  {id:"beekeeper-bee", title:"Beekeeper & Bee", blurb:"One goes as the beekeeper in white with a mesh veil; the other wears yellow and black stripes with antennae.", why:"The veil sells the beekeeper, the stripes sell the bee, and together they read in a single glance.", audience:["couple"], budget:["diy","low"], tags:{animals:3,funny:2,cute:2,couch:2,simple:2,matchyes:2,occparty:2,occcandy:1}, fit:"U", venue:{bar:1}, rank:133},
  {id:"tetris-duo", title:"Tetris Duo", blurb:"Two interlocking tetromino shapes built from painted cardboard boxes, worn like sandwich boards.", why:"You click together for every photo, and strangers will try to name your pieces.", audience:["couple"], budget:["diy","low"], tags:{games:3,funny:2,crafty:2,simple:2,couch:1,matchyes:2,occparty:2}, fit:"U", venue:{bar:1}, rank:134},
  {id:"little-lifeguard", title:"Little Lifeguard", blurb:"Red tee, whistle, and a rescue buoy made from a pool noodle ring: an everyday hero costume.", why:"The whistle is real, the buoy is a pool noodle, and the whole thing reads official at a glance.", audience:["kid"], budget:["diy","low"], tags:{heroes:3,cute:2,couch:2,simple:2,funny:1,kidunder3:1,kid36:2,kid7plus:1,occtreat:2,occparty:1,occparade:2}, fit:"U", venue:{bar:1}, rank:135},
  {id:"little-prince", title:"Little Prince", blurb:"Crown, cape, and a royal sash from the dress-up box or the craft drawer.", why:"Every prince costume is a crown away from done, and the crooked crown is the whole charm.", audience:["kid"], budget:["diy","low"], tags:{princess:3,funny:2,cute:2,couch:2,simple:1,kidunder3:2,kid36:2,kid7plus:1,occtreat:2,occparty:1,occparade:2}, fit:"M", venue:{bar:2}, rank:136},
  {id:"fossil-hunter", title:"Fossil Hunter", blurb:"Khaki vest, toy brush, magnifying glass, and cardboard fossil bones in a belt pouch.", why:"The fossil bones look dug up and real, and the magnifying glass gives your hands something to do between photos.", audience:["solo","kid","class"], budget:["diy","low"], tags:{dinos:3,funny:2,couch:2,crafty:2,simple:2,cute:1,occparty:2,occbar:1,occparade:2}, fit:"U", venue:{bar:2}, rank:137},
  {id:"web-slinger-kid", title:"Web Hero", blurb:"Red sweatsuit, tape web lines, big white eye lenses.", why:"Ten minutes of tape webs on a red sweatsuit reads hero from across the street.", audience:["kid"], budget:["low","diy"], tags:{simple:2,cute:2,couch:1,kid36:1,kid7plus:2,heroes:3,occtreat:2,occparade:2}, fit:"M", venue:{bar:2}, rank:138},

  {id:"milk-cookies", title:"Milk & Cookies", blurb:"White carton tunic for one, brown cookie with felt chips for the other.", why:"Sweet without trying too hard, and the cookie costume photographs great.", audience:["couple"], budget:["diy","low"], tags:{cute:2,funny:1,couch:2,matchyes:2,food:2,occparty:2,occtreat:1}, fit:"U", venue:{bar:2}, rank:139},
  {id:"chips-guac", title:"Chips & Guac", blurb:"Green guac tunic with red tomato dots for one, giant triangle chip hat for the other.", why:"The party snack everyone fights over, now as a couples costume.", audience:["couple"], budget:["diy","low"], tags:{funny:3,couch:2,matchyes:2,food:2,occbar:1,occparty:2}, fit:"U", venue:{bar:2}, rank:140},
  {id:"sushi-soy", title:"Sushi & Soy Sauce", blurb:"White rice tunic with orange fish sash for one, dark soy bottle for the other.", why:"Clean, clever, and instantly readable from across the bar.", audience:["couple"], budget:["diy","low"], tags:{cute:2,couch:2,matchyes:2,food:2,occbar:2,occparty:1}, fit:"U", venue:{bar:2}, rank:141},
  {id:"burger-fries", title:"Burger & Fries", blurb:"Sesame-seed bun top for one, red fry carton with yellow fry sticks for the other.", why:"Fast food royalty, and the fry carton doubles as a candy holder.", audience:["couple"], budget:["diy","low"], tags:{funny:3,couch:2,matchyes:2,food:2,occparty:2,occtreat:1}, fit:"U", venue:{bar:2}, rank:142},
  {id:"donut-coffee", title:"Donut & Coffee", blurb:"Pink frosted ring tunic for one, takeout coffee cup for the other.", why:"The breakfast date look, built for couples who run on caffeine.", audience:["couple"], budget:["diy","low"], tags:{cute:2,funny:1,couch:2,matchyes:2,food:2,occbar:1,occparty:2}, fit:"U", venue:{bar:2}, rank:143},
  {id:"wine-cheese", title:"Wine & Cheese", blurb:"Burgundy wine glass tunic for one, yellow cheese wedge with holes for the other.", why:"Grown-up funny, and it hands you a toast all night long.", audience:["couple"], budget:["diy","low"], tags:{cute:2,couch:1,crafty:1,matchyes:2,food:2,occbar:2,occparty:1}, fit:"U", venue:{bar:2}, rank:144},
{id:"kpop-demon-huntresses", title:"KPop Demon Huntresses", blurb:"Matching stage outfits, toy microphones, and demon-hunter poses for three.", why:"Three matching looks and one shared pose make the group click instantly.", audience:["group","class"], budget:["diy","low"], tags:{cute:2,funny:1,tv:3,matchyes:2,crafty:2,occparty:2,occparade:2}, fit:"U", venue:{bar:2}, rank:145},
{id:"goth-braids", title:"Goth Girl with Braids", blurb:"Black dress, two tight braids, and a stare that ends conversations.", why:"Two braids and a black dress: the most recognizable solo of the season for pocket change.", audience:["solo"], budget:["low","diy"], tags:{cute:1,scary:2,simple:2,couch:2,tv:2,occparty:2}, fit:"F", venue:{bar:2}, rank:146},
{id:"juke-joint-vampires", title:"Juke-Joint Vampires", blurb:"Sharp vintage suits, fangs, and a trumpet one of you never puts down.", why:"Vintage suits plus fangs make the best-dressed scary couple in the room.", audience:["couple"], budget:["diy","mid"], tags:{scary:2,funny:1,matchyes:2,tv:2,occbar:2,occparty:2}, fit:"U", venue:{bar:2}, rank:147},
{id:"blue-heeler-pup", title:"Blue Heeler Pup", blurb:"Blue-gray hoodie, felt ears, and a painted nose for the littlest pup.", why:"Toddlers already act like puppies, so this costume just agrees with them.", audience:["kid"], budget:["diy","low"], tags:{cute:3,animals:2,simple:2,couch:2,tv:2,occtreat:2,occparade:2}, fit:"U", venue:{bar:2}, rank:148},
{id:"baby-pumpkin", title:"Baby Pumpkin", blurb:"An orange onesie, green felt leaves, and the easiest first Halloween ever.", why:"The canonical first costume: warm, soft, and finished in twenty minutes.", audience:["kid"], budget:["low","diy"], tags:{cute:3,simple:3,couch:3,kidunder3:2,occtreat:2,occparade:2}, fit:"U", venue:{bar:2}, rank:149},
{id:"pirate-captain", title:"Pirate Captain", blurb:"Striped shirt, cardboard captain hat, and a treasure map you drew yourself.", why:"Closet clothes plus one cardboard hat, and the whole crew looks the part.", audience:["solo","group"], budget:["diy","low"], tags:{funny:2,simple:2,crafty:1,matchyes:1,occparty:2,occtreat:1}, fit:"U", venue:{bar:2}, rank:150},
{id:"cowboy-duo", title:"Cowboy and Cowgirl", blurb:"Denim, cardboard hats, and bandanas for the pair that rides together.", why:"Thrifted denim does the work, and matching cardboard hats make you a set.", audience:["couple"], budget:["diy","low"], tags:{cute:2,funny:1,matchyes:2,couch:2,occtreat:2,occparty:2}, fit:"U", venue:{bar:2}, rank:151},
{id:"smores-duo", title:"S'mores Duo", blurb:"Two graham-cracker tunics with a marshmallow and chocolate candy square between you.", why:"Two crackers, one marshmallow, zero explanation needed at the door.", audience:["couple"], budget:["diy","low"], tags:{cute:2,funny:2,couch:2,matchyes:2,food:3,occparty:2}, fit:"U", venue:{bar:2}, rank:152},
{id:"scarecrow", title:"Friendly Scarecrow", blurb:"Plaid shirt, straw poking out, and a stitched smile.", why:"Straw in the sleeves and a painted smile: the friendliest scare on the block.", audience:["solo"], budget:["diy","low"], tags:{funny:2,simple:2,crafty:1,couch:2,occparty:2,occtreat:1}, fit:"U", venue:{bar:2}, rank:153},
{id:"yellow-henchmen", title:"Yellow Henchmen Crew", blurb:"Yellow shirts, blue overalls, and swim goggles for the whole crew.", why:"One color scheme for everybody, and the goggles get laughs on sight.", audience:["group","class"], budget:["diy","low"], tags:{funny:3,matchyes:2,tv:2,occparty:2,occparade:2}, fit:"U", venue:{bar:2}, rank:154},
{id:"mystery-teens", title:"Mystery-Solving Teens", blurb:"Color-coded outfits, a toy magnifying glass, and one giant sandwich.", why:"Everyone dresses from their own closet in one assigned color, and it clicks.", audience:["group","class"], budget:["diy","low"], tags:{funny:2,simple:2,tv:3,matchyes:1,couch:2,occparty:2,occparade:2}, fit:"U", venue:{bar:2}, rank:155},
{id:"pumpkin-king-bride", title:"Pumpkin King and Ragdoll Bride", blurb:"Pinstripe suit and pumpkin mask for one, patchwork dress and yarn hair for the other.", why:"Spooky-romantic and readable from far away, with thrifted pieces doing the lifting.", audience:["couple"], budget:["diy","mid"], tags:{cute:2,scary:1,crafty:2,matchyes:2,tv:2,occparty:2}, fit:"U", venue:{bar:2}, rank:156},
{id:"moonwalk-star", title:"Moonwalking Pop Star", blurb:"Red jacket, one glitter glove, and the lean everyone attempts.", why:"Nail the lean and the moonwalk and strangers will request songs all night.", audience:["solo"], budget:["diy","low"], tags:{funny:2,allout:1,occbar:2,occparty:2}, fit:"U", venue:{bar:2}, rank:157},
{id:"witchy-sisters", title:"Witchy Sister Trio", blurb:"Three color-coded witch dresses: green, purple, and orange.", why:"Each picks a color and cackles in harmony; trios out-photograph duos.", audience:["group"], budget:["diy","low"], tags:{funny:2,scary:1,matchyes:2,tv:2,crafty:2,occtreat:2,occparty:2}, fit:"U", venue:{bar:2}, rank:158},
{id:"macabre-couple", title:"Macabre Goth Couple", blurb:"Long black gown and calm stare for one, sharp suit for the other.", why:"The gothic couples standard: elegant, eerie, and almost entirely thrifted.", audience:["couple"], budget:["diy","low"], tags:{scary:2,cute:1,matchyes:2,tv:2,occbar:1,occparty:2}, fit:"U", venue:{bar:2}, rank:159},
{id:"party-pinata", title:"Party Pinata", blurb:"A cardboard box wrapped in rainbow fringe, with real candy inside.", why:"You hand out candy from inside the costume, which wins every single party.", audience:["solo"], budget:["diy","low"], tags:{funny:3,crafty:2,occcandy:2,occparty:2}, fit:"U", venue:{bar:2}, rank:160},
{id:"fuzzy-gremlin", title:"Fuzzy Gremlin Plush", blurb:"A furry brown onesie, big felt ears, and googly eyes.", why:"The viral plush as a toddler costume: soft, warm, and extremely huggable.", audience:["kid"], budget:["diy","low"], tags:{cute:3,animals:1,simple:2,couch:2,kidunder3:3,occtreat:2,occparade:2}, fit:"U", venue:{bar:2}, rank:161},
{id:"rescue-pups", title:"Rescue Pup Team", blurb:"Color-coded pup vests and felt ears for the whole preschool crew.", why:"Each kid picks a color, and the team photo looks straight off the show.", audience:["kid","family","class"], budget:["diy","low"], tags:{cute:3,animals:2,matchyes:1,tv:2,occtreat:2,occparade:2}, fit:"U", venue:{bar:2}, rank:162},
{id:"wayfinder-princess", title:"Wayfinder Princess", blurb:"A printed sailcloth top, grass skirt, and a cardboard hook.", why:"The accuracy favorite: the shell necklace and hook make it unmistakable.", audience:["kid"], budget:["diy","low"], tags:{cute:2,princess:2,crafty:2,tv:2,occtreat:1,occparade:2}, fit:"F", venue:{bar:2}, rank:163},
{id:"chill-painter", title:"Chill Painter with Fro", blurb:"A big brown afro wig, denim shirt, and a palette you painted yourself.", why:"The happiest costume in the room, and everyone asks for a photo with the painter.", audience:["solo"], budget:["diy","low"], tags:{funny:3,simple:3,couch:2,occparty:2}, fit:"U", venue:{bar:2}, rank:164},
];
/* In-site build steps for every idea: {m: materials[], s: steps[]}. */
var INSTRUCTIONS = {"astronaut":{"m":["White sweatshirt and sweatpants, 1 set (buy: clothing store, or use your own)","1 large brown paper grocery bag (buy: grocery store or craft store)","Silver duct tape, 1 roll (buy: dollar store)","Flag sticker or iron-on patch, 1 (buy: craft store)","Scissors, 1 pair"],"s":["Cut the face opening SMALLER than you think with the scissors, you can always widen it, but a too-big hole flops and ruins the bag.","Hold the bag up to the face and trace the opening first.","Wrap two silver duct tape stripes around each sleeve and pant leg. Press the flag sticker onto the chest of the sweatshirt.","Safety: cut the face opening wide enough that vision and hearing stay clear.","Pull on the white sweatshirt and sweatpants.","Slip the bag over your head so the face opening lines up. Crimp the top with a strip of duct tape so it holds its shape.","Optional pro finish: print a mission patch from home (a circle with your name and 'EST. 2026') and tape it to the opposite chest from the flag. Real astronauts wear two patches."],"time":"25 min","cost":"$8-10","effort":"Easy","sizing":"Built for teens and adults. Cut the paper-bag helmet opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["What size paper bag fits a kid astronaut helmet?","A standard large brown grocery bag fits kids and most adults. For a toddler, use a small paper gift bag and cut the face opening to match their face."],["How do you keep the paper bag helmet from slipping?","Crimp the top of the bag with a strip of duct tape so it holds its shape, and cut the face opening wide enough that it sits on the shoulders, not the head."]]},"baby-dino":{"m":["Green hoodie, 1 (buy: clothing store, or use your own)","2 sheets green craft felt, 9x12 inches each (buy: craft store, construction paper works too)","Pillow stuffing or 2 old socks (make: stuff from home)","Safety pins, 6 to 8 (buy: dollar store)","Masking tape, 1 roll","Scissors, 1 pair"],"s":["Cut a paper triangle template first and test the size on the hoodie.","Then cut 6 to 8 triangle spikes from the green craft felt with the scissors, spikes cut too small look lost on the back, so go palm-size.","Tape the spikes in a row down the back of the green hoodie with the masking tape. Pin each spike from inside the hoodie with a safety pin.","Stuff the old socks with the pillow stuffing and tape the open ends shut with the masking tape.","Safety: pin everything from inside the green hoodie, so pin backs face the fabric and never the skin.","Pin the stuffed tail to the back waistband of the green hoodie.","Optional pro finish: cut two small white felt triangles and pin them to the hoodie cuffs as claws. Claws sell the dinosaur more than the spikes do."],"time":"20 min","cost":"$6-8","effort":"Easy","sizing":"Built for ages 1 to 8. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How many spikes does a baby dinosaur need?","Six to eight palm-size triangles down the back reads as dinosaur instantly. Fewer looks sparse; more looks cluttered."],["How do you make a dinosaur tail that stays up?","Stuff two old socks firmly with pillow stuffing, tape the open ends shut, and pin the tail to the back waistband, not higher, or it flops forward."]]},"backyard-hero":{"m":["Old pillowcase or t-shirt for the cape, 1 (make: cut up)","Solid-color t-shirt to wear, 1 (own)","Cardstock or foam letter for the first initial, 1 sheet (make: cut from cardstock, or buy: craft store)","Ribbon or string for cape ties, about 2 feet (own, or buy: craft store)","Safety pins, 2","Scissors, 1 pair"],"s":["Measure first: hold the pillowcase against the back and mark waist length before cutting.","Cut the cape with the scissors, a cape cut too short cannot be lengthened, so leave it long and trim after the first fitting.","Cut the first initial from the cardstock with the scissors. Pin it to the chest of the solid-color t-shirt with a safety pin.","Safety: keep the neck bow loose and easy to pull free. Never tie anything tight around the neck.","Thread the ribbon through the top corners of the cape. Tie it at the front of the neck in a loose quick-release bow. Trim the ribbon ends with the scissors.","Optional pro finish: outline the felt initial with a fabric marker in a contrasting color. The outline makes the emblem readable from across the yard."],"time":"15 min","cost":"$2","effort":"Easy","sizing":"Built for kids ages 3 to 10. Size the cape to the wearer: it should fall above the knees, and the neck tie stays loose and easy to pull free.","faqs":[["How long should a kid superhero cape be?","Waist length for under-6s (no tripping), mid-back for older kids. When in doubt, cut long and trim after they try it on."],["How do you attach a cape without sewing?","Thread ribbon through the top corners and tie a loose quick-release bow at the front of the neck. Never tie it tight, it must pull free."]]},"bacon-eggs":{"m":["Dark red or brown shirt for the bacon, 1 (own)","White shirt for the egg, 1 (own)","1 sheet red-brown craft felt, 9x12 inches (buy: craft store, construction paper works too)","1 sheet each white and yellow craft felt, 9x12 inches (buy: craft store, construction paper works too)","Safety pins, 6 to 8 (buy: dollar store)","Scissors, 1 pair"],"s":["Lay out the felt on the shirts and pin the arrangement BEFORE cutting or pinning for real. Cut 4 wavy vertical strips from the red-brown craft felt with the scissors.","Cut one large white oval (dinner-plate size) and one yellow circle (saucer size) from the other felt sheets.","Pin the wavy strips down the front of the dark red or brown shirt with a safety pin.","Pin the white oval to the white shirt, then pin the yellow circle on top of it for the yolk.","Put on the shirts. Have the bacon stand just behind the egg for photos, yolk side out.","Optional pro finish: cut the bacon strips with pinking shears or a wavy line instead of straight, the sizzle edge is what makes people say 'oh! bacon' instead of 'red strips'."],"time":"20 min","cost":"$1-2","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you make the fried egg read clearly?","Scale is everything: the white oval should cover most of the shirt chest, with the yellow yolk circle about a third of its size, pinned on top center."],["Will safety pins hold felt all night?","Yes if you pin from inside the shirt so the pin backs face the fabric. Use two pins per strip for the bacon so nothing rotates."]]},"bamboo-demon":{"m":["Pink bathrobe or kimono-style robe, 1 (own, or buy: clothing store)","Long dark wig, 1 (buy: toy store or online)","1 cardboard tube from wrapping paper or paper towels (make: save from home)","Ribbon or string, about 3 feet (own, or buy: craft store)","Red non-toxic face paint, 1 tube (buy: toy store)","Scissors, 1 pair","Tape, 1 roll"],"s":["Measure the tube against the face first and mark chin width.","Cut the cardboard tube slightly LONG with the scissors, you can trim it down, but a tube cut too short cannot be fixed. Tape a length of ribbon to each end of the tube.","Safety: keep the knot loose enough to talk and breathe easily. Never tie anything tight around the head or neck.","Tie the cardboard tube across the mouth with the ribbon, knotting loosely at the back of the head.","Pull on the pink bathrobe. Put on the long dark wig.","Dab a small red mouth mark on the cardboard tube with the red non-toxic face paint.","Optional pro finish: draw bamboo segment lines along the tube with a brown marker. Three quick lines turn a cardboard tube into a bamboo muzzle."],"time":"20 min + drying","cost":"$20-26","effort":"Easy","sizing":"Built for teens and adults. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you keep the muzzle comfortable?","Tie the ribbon loosely at the back of the head with a bow, not a knot, so it can be loosened fast. It should rest against the mouth, never press on it."],["What can I use instead of a wig?","A dark towel draped over the head works for photos. The robe and muzzle carry the costume; the wig is optional."]]},"basketball-star":{"m":["Basketball jersey or numbered tank top, 1 (own, or buy: sporting goods store)","Basketball shorts, 1 pair (own)","Black non-toxic face paint or 1 eyeliner pencil (buy: toy store)","Basketball, 1 (own, or buy: toy store)"],"s":["Pull on the basketball jersey and the basketball shorts.","Safety: use only the black non-toxic face paint. Skip the eye black for very young kids who will rub their eyes.","Draw two short black stripes under each eye with the black non-toxic face paint. Keep the stripes short and below the eye, never on the eyelid, and skip them for kids who rub their eyes.","Carry the basketball everywhere, tucked under one arm.","Dribble it whenever you stand still.","Optional pro finish: add a wristband and tall socks. Athletes are uniforms plus accessories; the wristband is the cheapest one."],"time":"5 min + drying","cost":"$4-5","effort":"Easy","sizing":"One design, two builds: the kid build fits ages 3 to 10, and the teen and adult build fits everyone older. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Do I need a real jersey?","No. Any numbered tank top works, write a big number on a plain shirt with a fabric marker and it reads the same from ten feet away."],["Is eye black safe for kids?","Use only non-toxic face paint marketed for kids, keep it below the eye, and skip it for very young kids who rub their eyes."]]},"black-cat":{"m":["Black shirt and pants or sweatsuit, 1 set (own)","Plain headband, 1 (buy: dollar store)","1 sheet black craft felt, 9x12 inches (buy: craft store, construction paper works too)","Black construction paper, 1 sheet (make: cut a mask from it)","Black non-toxic face paint, 1 tube (buy: toy store)","Small drawstring bag or pillowcase, 1 (own)","Scissors, 1 pair","Tape, 1 roll"],"s":["Cut two triangle ears from the black craft felt with the scissors, about 4 inches tall. Cut one eye mask shape from the black construction paper.","Tape the ears upright to the plain headband.","Safety: cut the eye holes wide in the mask so vision stays clear.","Tape the mask on with long tape tabs at the temples. Or draw whiskers with the black non-toxic face paint.","Pull on the black shirt and pants and put on the plain headband. Carry the small drawstring bag over one shoulder.","Optional pro finish: tape three pipe cleaners to each cheek as whiskers instead of drawing them. Real whiskers catch the light and photograph ten times better."],"time":"20 min + drying","cost":"$13-18","effort":"Easy","sizing":"Built for teens and adults. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How do you make cat ears stand up?","Cut the triangles 4 inches tall and tape them to the headband with a 1-inch tape tab folded over the band on both sides. Felt alone flops; the double-sided tape tab is the trick."],["Mask or face paint whiskers for a toddler?","Face paint. A paper mask slips on small faces and the eye holes never line up. Paint three whisker lines per cheek and skip the mask."]]},"block-game-crew":{"m":["1 large cardboard box per person, big enough to fit over the torso (make: ask a grocery store for spares)","Acrylic paint in each hero's colors, 1 small bottle per color (buy: craft store, tempera paint works too)","Paintbrushes, 1 wide and 1 detail per person","Black marker, 1 (buy: dollar store)","Scissors, 1 pair"],"s":["Each person picks a blocky video-game hero look.","Safety: an adult should handle the heavy cutting, and cut the eye holes generously so everyone can see clearly.","Measure each person's head and shoulders first, then cut a head opening and eye holes in each large cardboard box with the scissors.","Cut the head opening smaller than you think, cardboard cut away cannot be put back. Cut the eye holes generously so everyone can see clearly.","Paint each box in the hero's main colors with the acrylic paint and paintbrushes. Let it dry fully.","Draw a pixel-style square face and details on the front of each box with the black marker. Wear the boxes over regular clothes once the paint is dry.","Optional pro finish: draw thin black grid lines across the painted box before it dries fully. The grid is what makes it read as pixels instead of just a painted box."],"time":"45 min + drying","cost":"$8-11","effort":"Medium","sizing":"One per person, so kids and adults each get a real fit. Have each wearer step into the box before you mark arm and leg holes, cut them a little wide, and tape every inside edge so cardboard never scratches.","faqs":[["How do you keep a box costume comfortable?","Cut arm holes wide, wear it over regular clothes, and tape the inside edges of every cut so cardboard never scratches. Keep the box at torso height, never over the face, for kids."],["How long does the paint take to dry?","Acrylic on cardboard needs about 1 hour to stop being tacky. Paint the night before if you can; wearing it damp smears the pixel face."]]},"block-monster":{"m":["Solid-color sweatsuit, any color, 1 set (own)","1 large cardboard box (make: cut it into square blocks)","Packing tape, 1 roll","Scissors, 1 pair","Non-toxic face paint, 1 tube (buy: toy store)"],"s":["Cut the large cardboard box into square blocks with the scissors: two large (shoulder size), four medium (forearm and shin size).","Test-hold each block against the body BEFORE taping, blocks taped in the wrong spot look lopsided all night.","Tape one large block to each shoulder with the packing tape.","Tape one medium block to each forearm and shin with the packing tape.","Pull on the solid-color sweatsuit under the blocks.","Safety: keep the face paint clear of the eyes.","Draw a blocky square-toothed grin on the face with the non-toxic face paint.","Optional pro finish: edge every block with silver duct tape. The metallic edge catches light and makes cardboard read as robot armor."],"time":"30 min + drying","cost":"$12-14","effort":"Easy","sizing":"Built for teens and adults. Have each wearer step into the box before you mark arm and leg holes, cut them a little wide, and tape every inside edge so cardboard never scratches.","faqs":[["How do the blocks stay on?","Packing tape loops: tape the block to the sweatsuit sleeve or pant leg with two strips. Tape sticks to fabric well enough for one evening and peels off after."],["What size blocks for a small kid?","Halve everything: medium blocks become the shoulder blocks. Oversized blocks on a small kid drag and bump doorways."]]},"blue-alien-ohana":{"m":["Blue hoodie per alien-role person, 1 each (own, or buy: clothing store)","Blue pipe cleaners, 2 per alien (buy: craft store)","Blue pom-poms, 2 per alien (buy: craft store)","Headband per alien-role person, 1 each (buy: dollar store)","Red t-shirt or dress per Lilo-role person, 1 each (make: from closet, or buy: thrift store)","White craft felt or paper, 1 sheet (buy: craft store)","Safety pins, 4 to 6 (buy: dollar store)","Scissors, 1 pair","Tape, 1 roll"],"s":["Wrap each headband in blue tape so the whole band reads blue from across the room.","Twist two blue pipe cleaners around the top of each headband so they stand up about 6 inches tall, then bend each tip into a small curl.","Tape one blue pom-pom to the tip of each pipe cleaner. The two bobbing balls are what read as antennae from ten feet away.","Pull on the blue hoodies.","Lilo: cut leaf shapes from the white felt or paper with the scissors. Pin or glue the leaves across the red t-shirt or dress.","Safety: pin from the front of the red shirt, so pin backs face the fabric and never the skin.","Wear dark hair down for Lilo. Put the antenna headbands on the aliens last.","Optional pro finish: twist each pipe cleaner into a loose zigzag before adding the pom-pom. The wobble makes the antennae bounce when the kid runs, and movement reads as alien better than any static shape."],"time":"30 min + drying","cost":"$12-15","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How do you keep the antennae from flopping?","Twist each pipe cleaner around the headband twice at the base before standing it up, the double wrap is the anchor. Then tape over the twist. Pipe cleaner alone flops by hour two; the tape wrap locks it."],["What if we only have one blue hoodie?","Make the second alien a different blue: navy t-shirt plus blue face paint on the arms. The antenna headbands match, so the pair still reads."]]},"blue-dog-family":{"m":["Blue or orange t-shirt per person, 1 each (own, or buy: clothing store)","Headband per person, 1 each (buy: dollar store)","Blue, orange, and white craft felt, 1 sheet of each color 9x12 inches (buy: craft store, construction paper works too)","Safety pins, 4 per person (buy: dollar store)","Scissors, 1 pair"],"s":["Cut one paper ear template and check it against the headband before cutting felt.","Cut two floppy dog ears from the craft felt with the scissors for each person, about 5 inches long. Match ear color to shirt color.","Pin the ears to each headband with the safety pins.","Pin a white craft felt belly spot to the front of each blue or orange t-shirt.","Pull on the blue or orange t-shirts.","Put on the headbands and decide who is mama, dad, and the pups.","Optional pro finish: stuff an old sock with tissue, pin it to the back waistband as a tail, and let it wag. Every dog family photo is better with a tail."],"time":"25 min","cost":"$4-6","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How do you tell the family members apart?","Match the show: blue shirt for the dad dog, orange for the mom dog, mix for the pups. Add a white belly spot to the pups only, the audience reads it instantly."],["Ears keep sliding off the headband. Fix?","Pin the ears to the headband with two safety pins each instead of tape. Pins survive hugs; tape gives up by the second photo."]]},"board-game-pieces":{"m":["Black or white monochrome clothes, 1 set per person (own)","Large cardboard boxes, 2 to 3 (make: collect spares)","White and black acrylic paint, 1 small bottle each (buy: craft store, tempera paint works too)","Paintbrushes, 1 wide and 1 detail","Black marker, 1 (buy: dollar store)","Ribbon or string for straps, about 4 feet per board (own)","Scissors, 1 pair","Tape, 1 roll"],"s":["Each person picks a game piece to be.","Sketch each piece on the cardboard with marker BEFORE cutting.","Cut a cube shape from a large cardboard box for the die with the scissors, measure the head first and cut the opening small, widening as needed.","Cut flat boards from another box for the playing card and the domino.","Paint the die and card white and the domino black with the acrylic paint and paintbrushes. Let the paint dry fully.","Add dots and card symbols with the black marker and the white acrylic paint once the base coats are dry.","Safety: cut the die box eye holes generously so you can see clearly. Only wear the die box once all paint is fully dry.","Tape ribbon straps to the flat boards so they hang front and back over the black or white monochrome clothes. Wear the die box over the head with the eye holes lined up.","Optional pro finish: paint a thin gold border around the card and domino edges. The border is what makes them read as game pieces instead of painted cardboard."],"time":"45 min + drying","cost":"$2-4","effort":"Medium","sizing":"One per person, so kids and adults each get a real fit. Have each wearer step into the box before you mark arm and leg holes, cut them a little wide, and tape every inside edge so cardboard never scratches.","faqs":[["Which game pieces are easiest to recognize?","The die (white cube, black dots), a playing card (white board, big red heart), and a domino (black board, white dots). Pick pieces with strong silhouettes."],["How do flat boards stay on?","Tape ribbon straps to the top corners so they hang front and back like a sandwich board over the monochrome clothes. Two straps, not one, so nothing spins."]]},"bowling-pins":{"m":["White shirt and pants per pin person, 1 set each (own)","Red duct or electrical tape, 1 roll (buy: dollar store)","Black shirt and pants for the bowler, 1 set (own)","Toy bowling ball or black playground ball, 1 (buy: toy store)","Scissors, 1 pair"],"s":["Measure first: the classic pin has two stripes around the neck area.","Each pin person cuts two 12-inch red tape stripes from the roll with the scissors, cut all stripes before sticking any, so they match.","Wrap two red tape stripes around the collar of the white shirt and one around each wrist.","The bowler pulls on the black shirt and pants.","Safety: use a lightweight toy ball, never a real bowling ball.","Carry the toy bowling ball. Line the pins up in formation with the bowler at the end for photos.","Optional pro finish: number the pins 1 through 10 with a black marker on the back. When the bowler 'knocks you down' you fall in number order, it gets the biggest laugh of the night."],"time":"15 min","cost":"$1-3","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Where exactly do the red stripes go?","Two stripes around the collar of the white shirt and one around each wrist. That is the whole pin read, collar plus wrists."],["Can the bowler use a real bowling ball?","No, use a lightweight toy ball or playground ball painted black. A real ball is a weapon in a crowd and most venues ban them."]]},"boxer":{"m":["Bathrobe, 1 (own)","Toy boxing gloves, 1 pair (buy: toy store)","Purple and yellow non-toxic face paint, 1 tube each (buy: toy store)","Athletic shorts and sneakers, 1 set (own)","Phone for entrance music, 1 (own)"],"s":["Pull on the athletic shorts, sneakers, and bathrobe with the hood up.","Safety: keep the face paint clear of the eyes.","Dab the purple and yellow face paint on one cheekbone and around one eye for bruise makeup.","Less is more, one bruise reads as boxer, five bruises reads as accident. Keep all paint clear of the eyes.","Pull on the toy boxing gloves.","Throw a few shadow punches and play entrance music from the phone as you walk in.","Optional pro finish: write your fighter name across the back of the robe with white duct tape letters. Walk-ins get twice the reaction when the robe has a name."],"time":"10 min + drying","cost":"$11-15","effort":"Easy","sizing":"Built for teens and adults. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you do bruise makeup that looks real?","Layer purple first, then dab yellow at the edges. Real bruises are darkest in the center and yellow at the healing edge. Blend with a fingertip, not a brush."],["Toy gloves or real gloves?","Toy gloves only. Real boxing gloves are heavy, sweaty, and you cannot hold a drink. Toy gloves photograph identically."]]},"breakfast-buffet":{"m":["Cardboard sheets, 1 per person about 2x2 feet (make: cut from boxes)","Markers in assorted colors, 1 pack (own, or buy: dollar store)","String or yarn, about 4 feet per person (own)","Scissors, 1 pair"],"s":["Each person picks a breakfast item.","Draw the food on paper FIRST to plan the layout, then cut a large circle or rectangle from the cardboard sheets with the scissors.","Draw big, the food must read from across the room, so fill the whole board.","Draw the food big on the cardboard with the markers. Draw a fried egg, bacon strips, buttered toast, a pancake stack, a glass of OJ, or a coffee mug.","Safety: an adult pokes the holes in the top corners with the tip of the scissors, since pushing through cardboard takes force.","Thread the string through the holes and wear the sign over normal clothes like a sandwich board.","Optional pro finish: make one extra small sign that says 'BREAKFAST BUFFET, all you can eat' and have the tallest person carry it. The sign turns five food boards into one group costume."],"time":"25 min","cost":"$0","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["What breakfast foods read best on a sign?","Fried egg, bacon strips, and a coffee mug, all three are recognizable in three marker strokes. Pancakes need more detail; skip them unless someone is artistic."],["How do you wear a cardboard sign comfortably?","Two strings through the top corners, worn like a sandwich board over normal clothes. Keep the board at chest height so it does not bang knees."]]},"bumble-bee":{"m":["Black sweatshirt and sweatpants, 1 set (own, or buy: clothing store)","Yellow duct or electrical tape, 1 roll (buy: dollar store)","Black headband, 1 (buy: dollar store)","2 yellow pipe cleaners, 12 inches each (buy: craft store, floral wire works too)","2 black pom-poms, 1 inch (buy: craft store, cotton balls work too)","Craft glue, 1 tube (buy: craft store)"],"s":["Mark stripe positions with chalk or a light pencil first so the spacing is even.","Wrap three yellow duct tape stripes around the torso of the black sweatshirt and one around each arm, even spacing is what makes it read as bee instead of random tape.","Twist the two yellow pipe cleaners into a V.","Safety: use non-toxic craft glue, and keep the pom-poms out of reach of toddlers.","Glue a black pom-pom to each tip of the V with the craft glue. Glue the base of the V to the black headband.","Let the glue dry fully, then pull on the black sweatshirt and sweatpants and the black headband.","Optional pro finish: cut two white ovals from a plastic bag and tape them to the back as wings. Bees have wings; the ten seconds it takes doubles the recognition."],"time":"20 min + drying","cost":"$18-20","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Will duct tape stick to a sweatshirt all night?","Yes on fleece and cotton. Press each stripe firmly and smooth from the center out. It peels off clean after one evening."],["How do you keep the antennae upright?","Twist the two pipe cleaners into a tight V and glue the base, not just the tips, to the headband. A wide glued base is what keeps them vertical."]]},"burger-joint-couple":{"m":["2 white aprons (buy: dollar store or online)","Fake mustache, 1 (buy: toy store)","Curly red wig, 1 (buy: toy store or online)","Costume glasses, 1 pair (buy: toy store)","Order pad and pencil, 1 set (own, or buy: dollar store)"],"s":["Test the mustache position in a mirror BEFORE peeling the adhesive, stick it on dry first, mark the spot lightly, then commit.","One partner pulls on a white apron and sticks on the fake mustache with its skin-safe adhesive.","The other partner pulls on the second white apron, the curly red wig, and the costume glasses.","Carry the order pad and pencil and take each other's burger orders all night.","Remove the fake mustache gently at the end of the night.","Optional pro finish: write 'BURGER JOINT' on both aprons with a red fabric marker, plus a fake name tag each ('Ask me about the secret sauce'). Named staff beats blank aprons."],"time":"10 min","cost":"$12-18","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you keep a fake mustache on all night?","Clean the skin first (no moisturizer), press for 30 seconds, and carry the adhesive for touch-ups. It loosens after eating, re-press in the bathroom."],["What if the wig is itchy?","Wear a thin headband or bandana underneath. The barrier layer is the difference between wearing it all night and ripping it off by nine."]]},"caped-duo":{"m":["2 old twin sheets or large fabric rectangles, about 4x5 feet each (make: cut from old sheets)","Craft felt for masks and emblems, 2 sheets 9x12 inches (buy: craft store, construction paper works too)","Ribbon or cord for cape ties, about 3 feet per cape (own, or buy: craft store)","Fabric glue, 1 tube (buy: craft store)","Paper and pencil for sketching, 1 set (own)","Scissors, 1 pair"],"s":["Sketch a matching emblem for each of you on the paper.","Cut the emblems from the craft felt with the scissors.","Sketch and cut the emblems from paper first and hold them against the cape to check the size, emblems should cover a third of the cape width.","Cut each sheet into a cape with the scissors, hem-side down. Glue a craft felt emblem to the back of each cape with the fabric glue.","Cut two eye masks from the craft felt, cutting the eye holes wide. Glue ribbon ties to the ends with the fabric glue and let the glue dry.","Safety: tie the cord in a loose bow that pulls free easily. Never tie anything tight around the neck. Keep the mask eye holes wide so vision stays clear.","Tie the capes at the neck with the cord in a loose bow and put on the masks.","Optional pro finish: cut the emblem in two felt colors, a base shape plus a smaller top shape. Layered emblems look designed; single-color looks cut-out."],"time":"30 min + drying","cost":"$2-3","effort":"Easy","sizing":"Each partner builds their half in their own size. Kids under 8 use a twin flat sheet, tweens and adults use a full flat, and trim the hem so it clears the ground by a few inches. Toddlers trip on hems an adult would clear.","faqs":[["How do you make two capes look like a matching duo?","Same cape length, same emblem shape, inverted colors (your emblem is red-on-black, theirs is black-on-red). Matching shape plus inverted color reads as team instantly."],["Fabric glue or safety pins for the emblem?","Glue for the emblem (flat, permanent for the night), pins for anything you might reposition. Glue the emblem the night before so it cures."]]},"cardboard-knight":{"m":["Large cardboard boxes, 2 to 3 (make: collect spares)","Silver acrylic paint, 1 bottle (buy: craft store, tempera paint works too)","Foam brush or paintbrush, 1 wide (own, or buy: craft store)","1 pool noodle (buy: toy store or dollar store)","Gray duct tape, 1 roll (buy: dollar store)","Black marker, 1 (buy: dollar store)","Scissors, 1 pair"],"s":["Safety: an adult should handle the heavy cutting. Cut generous eye holes in the helmet so vision stays clear.","Draw every piece on the cardboard with marker BEFORE cutting: chest plate, back plate, two shoulder pieces, helmet.","Cut the helmet eye holes generously, cardboard cut away cannot be added back, and a knight who cannot see is a hazard. Cut all pieces with the scissors.","Paint every armor piece silver with the silver acrylic paint and the foam brush. Let the paint dry fully.","Add rivet dots and edge lines with the black marker.","Tape the plates together with the gray duct tape so they hinge at the shoulders. Wrap the pool noodle in gray duct tape for the sword.","Put the armor on over dark clothes once the paint is dry. Carry the noodle sword.","Optional pro finish: tape a red crepe-paper plume to the helmet top. Knights are silver; knights with plumes are memorable."],"time":"60 min + drying","cost":"$11-15","effort":"Medium","sizing":"One design, two builds: the kid build fits ages 3 to 10, and the teen and adult build fits everyone older. Have each wearer step into the box before you mark arm and leg holes, cut them a little wide, and tape every inside edge so cardboard never scratches.","faqs":[["How do you keep cardboard armor from falling apart?","Gray duct tape hinges at the shoulders and sides, tape both sides of each joint. The tape is the armor's skeleton; the cardboard is just the skin."],["What is the safest sword option?","A pool noodle wrapped in gray duct tape. It looks metallic in photos and cannot hurt anyone. Never use wood or real metal, even blunted."]]},"cat-mouse":{"m":["2 headbands (buy: dollar store)","1 sheet black craft felt, 9x12 inches (buy: craft store, construction paper works too)","1 sheet gray craft felt, 9x12 inches (buy: craft store, construction paper works too)","Black eyeliner pencil or non-toxic face paint, 1 (buy: toy store)","Scissors, 1 pair","Tape, 1 roll"],"s":["Cut one paper ear template first, triangles for the cat, rounds for the mouse, and check both against the headbands. Cut two triangle ears from the black craft felt with the scissors.","Cut two round ears from the gray craft felt with the scissors, about 3 inches across.","Safety: keep the eyeliner clear of the eyes.","Put on the headbands and draw whiskers on both faces with the black eyeliner pencil.","Optional pro finish: glue a pink felt triangle inside each ear. Inner ears are the five-second detail that makes both animals read instantly."],"time":"15 min + drying","cost":"$6-8","effort":"Easy","sizing":"Each partner builds their half in their own size. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How do you tell the cat and mouse apart at a glance?","Cat gets triangle ears plus drawn whiskers; mouse gets round ears plus a pink nose dot. Different ear shape plus one face detail each, never rely on color alone."],["Eyeliner or face paint for whiskers?","Eyeliner pencil for teens and adults (precise), non-toxic face paint for kids (gentler). Either way keep it clear of the actual eyes."]]},"cereal-crew":{"m":["Solid-color shirt and pants per person, 1 set each (own)","Empty cereal boxes, 1 per person (make: save from home)","Markers or crayons in assorted colors, 1 pack (own)","String, about 4 feet per person (own)","Scissors, 1 pair","Tape, 1 roll"],"s":["Each person invents a cereal name.","Open the box along the side seam and flatten it BEFORE cutting, a flat box cuts cleanly, a 3D box wobbles.","Cut the front panel off an empty cereal box with the scissors, keeping the panel as large as possible.","Decorate the panel with the markers or crayons. Draw a mascot, add a prize burst, and write the cereal name in big letters.","Tape string to the top corners of each panel with the tape.","Wear the panel over the solid-color shirt like a sandwich board.","Optional pro finish: add a 'prize inside' burst and a fake nutrition joke ('100% daily value of fun') in the corner. Real cereal boxes have fine print; yours should too."],"time":"20 min","cost":"$0-1","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["What makes a fake cereal name funny?","Puns on the person's name or a group in-joke, in big block letters across the top. 'Captain Crunch' structure: [Title] + [Crunch/O's/Flakes]."],["How do you wear a cereal panel?","Tape string to the top corners and wear it like a sandwich board over the solid-color shirt. One panel on the front is enough, backs are optional."]]},"cheerleader":{"m":["Team-color t-shirt and skirt or shorts, 1 set (own)","4 to 6 white plastic grocery bags (make: save from home)","Hair ribbon in a team color, 1 (buy: dollar store)","Rubber bands or tape, 1 pack (own)","Scissors, 1 pair"],"s":["Safety: cut the bags up right away. Keep whole bags away from very small children.","Stack 2 to 3 white plastic grocery bags.","Cut them into long strips with the scissors, stopping 3 inches from one end, do NOT cut all the way through or the pom-pom falls apart. The uncut end becomes the handle.","Roll the uncut end tightly and wrap it with a rubber band or tape to make a handle. Fluff the strips.","Make a second pom-pom the same way.","Pull on the team-color t-shirt and skirt or shorts. Tie the hair ribbon in a bow and carry a pom-pom in each hand.","Optional pro finish: roll a sheet of paper into a cone megaphone and tape it. Shouting through a megaphone is the difference between wearing the costume and performing it."],"time":"15 min","cost":"$3","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How fluffy should the pom-poms be?","Fluff each strip individually after rolling the handle, the fluffing is 80% of the look. Flat strips read as trash bag; fluffed strips read as pom-pom."],["Are plastic bag pom-poms safe for toddlers?","Cut the bags up right away and keep whole bags away from very small children. For under-3s, use tissue paper pom-poms instead."]]},"classic-ghost":{"m":["1 white flat sheet: twin size for kids under 8, full size for tweens and adults (make: use an old sheet; buy: thrift store for a dollar or two)","Black marker, thick tip, 1 (buy: dollar store)","Scissors, 1 pair","2 small squares of black tulle or sheer fabric, about 4 inches each (optional, for see-through eyes; buy: craft store)"],"s":["Pick the sheet size first: twin flat for a small kid, full for a bigger kid or adult. Bigger than you need is fine; smaller is not.","Drape the sheet over the wearer and have them stand still. Mark both eye spots with the black marker while the sheet is on, marking blind never lines up.","Take the sheet off. Cut the eye holes SMALL first, about the size of a quarter. You can always widen them; you cannot shrink them.","Hold the sheet up and check: the wearer should see clearly through both holes. Widen a little at a time until they can.","Optional pro finish: tape a square of black tulle behind each hole. From outside the eyes look dark and hollow; from inside you see straight through the mesh.","Safety: trim the bottom so the hem clears the ground by several inches, a dragging hem is what trips a kid on a dark sidewalk. Keep nothing tight around the neck.","Draw a wavy or smiling mouth below the eyes with the black marker. Drape it back on and go."],"time":"10 min","cost":"$4-5","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Kids under 8 use a twin flat sheet, tweens and adults use a full flat, and trim the hem so it clears the ground by a few inches. Toddlers trip on hems an adult would clear.","faqs":[["How do I make eye holes safely?","Mark them while the sheet is on the wearer, cut small first, and widen until they see clearly. Back with black tulle so the eyes look dark but stay see-through."],["What size sheet for a toddler ghost?","A twin flat sheet, trimmed short. Cut it shorter than feels right, toddlers trip on hems adults would clear."]]},"crowd-camouflage":{"m":["Gray hoodie, 1 (own)","Dark pants, 1 pair (own)","Gray beanie, 1 (own, or buy: dollar store)","Blank adhesive name tag, 1 (buy: dollar store)","Pen, 1 (own)"],"s":["Pull on the gray hoodie with the hood up, the dark pants, and the gray beanie.","Leave the blank adhesive name tag blank, that IS the joke. Write nothing on it with the pen and stick it to the chest of the gray hoodie.","The one thing that ruins this costume is filling in the tag.","Keep a blank expression, hood up, and blend into the background of every group photo.","Optional pro finish: stand in the back row of every group photo with a perfectly blank expression. The costume only works if you commit to being forgettable, ham it up by being boring."],"time":"5 min","cost":"$1-2","effort":"Easy","sizing":"Built for teens and adults. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["What is the joke of this costume?","You are camouflaged as a random background person, the blank name tag, the gray hoodie, the neutral face. It is funniest in big group photos where nobody notices you until the second look."],["How do you make it read as a costume, not just gray clothes?","The blank name tag is the tell. Without it you are just underdressed; with it, people get the bit."]]},"deadpan-diva":{"m":["Black dress, 1 (own)","Very pale foundation or white non-toxic face paint, 1 (buy: toy store)","Dark eyeliner and lipstick, 1 set (own, or buy: dollar store)","2 hair ties (own)"],"s":["Braid the hair into two tight braids with the hair ties.","Buy the white non-toxic face paint if needed.","Test the pale foundation on the jawline first and blend fully, patchy pale makeup reads as sick, not deadpan.","Apply the pale foundation evenly over the face, blending into the neck so there is no mask line.","Add the dark eyeliner and lipstick for contrast.","Put on the black dress, fold the arms, and hold the stare.","Use skin-safe makeup and wash it all off before bed.","Optional pro finish: add a thin black ribbon choker. The choker plus the braids plus the stare is the complete silhouette, without it, it is just a black dress."],"time":"15 min + drying","cost":"$6-8","effort":"Easy","sizing":"Built for teens and adults. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you get the braids right?","Two tight braids, middle part, pulled flat against the head. Loose or messy braids break the severe look, tight is the whole point."],["How do you take off heavy pale makeup?","Wash with a gentle cleanser, not just water, stage-white needs soap. Moisturize after; pale foundation is drying. Never sleep in it."]]},"decades-crew":{"m":["Each person's own closet clothes (make: use what you own)","1 printed decade card per person, e.g. 70s, 80s, 90s, cardstock or paper (make: hand-letter on paper)","Scissors, 1 pair","Tape, 1 roll or safety pins, 1 pack","Hair gel or spray, 1 (buy: drugstore)"],"s":["Everyone digs through their closet clothes and picks a different decade.","Safety: adults handle the scissors when trimming the decade cards.","Letter the decade card BIG, 4-inch letters minimum, because the card is the costume's label.","Hand-letter a decade card on paper, like '80s, and tape it to each chest. A small card nobody can read defeats the purpose.","Build each look with closet props only: bell-bottoms and a headband for the 70s. Neon and high socks for the 80s. Flannel tied at the waist for the 90s.","Style hair with hair gel to sell the decade: a big part for the 70s. A scrunchie side-ponytail for the 80s.","Keep props light so the looks survive a whole night of walking.","Optional pro finish: give each decade one era-perfect prop, an inflatable microphone for the 80s, a fake vinyl record for the 70s. One prop per person keeps it cheap and specific."],"time":"20 min","cost":"$1-2","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How do you keep decades from looking random?","Assign decades first so no two people pick the same one, and give each person ONE signature item (neon for 80s, flannel for 90s). One signature item per decade beats five vague ones."],["What is the fastest 90s look?","Flannel tied around the waist over a plain tee, jeans, and a middle part. Three items, all from a closet, reads instantly."]]},"deviled-egg":{"m":["1 white t-shirt (buy: craft store, or use one you own)","1 sheet yellow felt, 9x12 inches (buy: craft store; construction paper works too)","2 sheets red felt, 9x12 inches each (buy: craft store; construction paper works too)","1 red headband (buy: dollar store)","2 red pipe cleaners, 12 inches each (buy: craft store; twisted strips of red paper work too)","Scissors, 1 pair; tape, 1 roll or glue, 1 bottle","Red face paint or lipstick, 1 (buy: drugstore)"],"s":["Safety: adults handle the scissors when cutting the felt.","Draw the egg-yolk oval on paper first and hold it against the white t-shirt to check the size, about dinner-plate size.","Cut it from the yellow felt with the scissors. Cut it bigger rather than smaller: a yolk that covers the chest reads instantly.","Tape or glue the yellow felt oval to the chest of the white t-shirt.","Twist the two red pipe cleaners into small horns, and tape them to the red headband.","Cut a long pointed tail from the red felt sheets with the scissors, about 18 inches long.","Tape it to the back of the white t-shirt at two points, shoulder blades and lower back, so it stands up. Sit down once to make sure it clears the chair.","Optional pro finish: cut a jagged white felt ring around the yellow yolk for the egg-white edge. The white rim is what makes it read as a fried egg instead of a yellow circle."],"time":"20 min + drying","cost":"$14-19","effort":"Easy","sizing":"Built for teens and adults. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How big should the yolk be?","Dinner-plate size, centered on the chest. Smaller than a dessert plate disappears across a room."],["How do you keep the tail from flopping?","Tape it at two points, shoulder blades and lower back. One tape point lets it swing; two keeps it standing."]]},"dino-herd":{"m":["1 green poncho or green bedsheet per person, about 50x60 inches (buy: craft store or online)","1 sheet green felt per person, 9x12 inches (buy: craft store; construction paper works too)","1 old sock per person, white or colored (make: use one you own)","Scrap fabric or cotton balls for stuffing, about 1 cup per person (make: use what you own)","Fabric glue, 1 tube, or 6 safety pins per person (buy: craft store or dollar store)","Scissors, 1 pair"],"s":["Buy one green poncho and one green felt sheet per person, and raid the sock drawer for an old sock.","Safety: adults handle the scissors when cutting the green felt.","Cut one paper triangle first and hold it against the green poncho to check the size: palm-size works best.","Cut 8 to 10 triangles from the green felt sheet per person with the scissors, all from the paper template so the row looks even.","Pin the green felt triangles in a row down the back of the green poncho.","Stuff the old sock with the scrap fabric, and pin the opening to the back waistband of the green poncho.","Wear the green poncho over a t-shirt and jeans. Pin the spikes and tail flat so they do not poke anyone in a crowd.","Optional pro finish: pin a row of small felt spikes along the sock tail too, so the tail matches the back and stops reading as a sock."],"time":"30 min","cost":"$2-4","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Kids under 8 use a twin flat sheet, tweens and adults use a full flat, and trim the hem so it clears the ground by a few inches. Toddlers trip on hems an adult would clear.","faqs":[["How do you keep the spikes upright in a crowd?","Pin each spike at two points, base and middle, flat against the poncho so they do not poke anyone. Flat-pinned spikes survive hugs."],["What size poncho for small kids?","Cut a twin bedsheet in half for kids under 8. A full poncho drags on small kids and trips them."]]},"dino-rangers":{"m":["Khaki shirt, 1, and khaki pants, 1 pair, per grown-up (make: use what you own)","Green hoodie per child, 1 each (buy: thrift store, or use one you own)","White paper or card, 2 sheets (make: use what you own)","1 toy dinosaur or plush per kid (buy: toy store)","Ribbon or string, 18 inches per kid (make: use what you own)","Tape, 1 roll and scissors, 1 pair"],"s":["Dress the grown-ups in the khaki shirt and pants, and roll the sleeves for the field-guide look.","Buy or dig out the green hoodie for each kid, the toy dinosaur, and the ribbon.","Safety: adults handle the scissors when cutting the white paper.","Draw the eye spots on paper first and hold them against the hood to check the placement.","Cut two oval eye spots from the white paper with the scissors, about 3 inches tall. Cut them smaller than you think: oversized eyes slide off the hood sides.","Safety: skip small plastic dinosaur toys for kids under three, since they are a choking hazard.","Loop the ribbon around the toy dinosaur like a leash, and tie the other end to the kid's wrist. Keep the leash short so the toy dinosaur does not drag.","Optional pro finish: write each kid's dinosaur name on masking tape and stick it on the khaki shirt like a field badge. Ranger plus name tag sells the explorer story."],"time":"15 min","cost":"$1-3","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Is the wrist leash safe for a kid?","Yes if you use a loose loop tied over the jacket sleeve, never tight on bare skin, and keep it short so it cannot catch on playground equipment."],["What if we have no khaki clothes?","Any neutral shirt and pants work: tan, olive, or beige. Roll the sleeves twice and the field-guide look comes through."]]},"dinosaur-family":{"m":["1 green sweatsuit per person (buy: discount store, or use one you own)","1 sheet green felt per person, 9x12 inches (buy: craft store; construction paper works too)","Scissors, 1 pair","Fabric glue, 1 tube, or 6 safety pins per person (buy: craft store or dollar store)","Green face paint, non-toxic, 1 tube (buy: drugstore)"],"s":["Buy one green sweatsuit and one sheet of green felt per person.","Safety: adults handle the scissors when cutting the green felt.","Trace your palm on paper first and use it as the triangle template: spikes about palm-size read best. Cut 8 to 10 triangles from the green felt per person with the scissors.","Glue or pin the green felt triangles in a row from the hood down the back of the green sweatsuit.","Paint green spots on each cheek with the green face paint, keeping it clear of the eyes.","Put the green sweatsuit on over regular clothes, and pin the spikes flat to the hood so they stay put.","Optional pro finish: cut two small white felt triangles and glue them to the hood cuffs as claws. Claws make the arms part of the costume, not just the back."],"time":"25 min + drying","cost":"$2-4","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you keep the spikes from flopping?","Pin them flat against the hood so they point back, not up. Spikes pinned upward on soft fleece flop by the second photo."],["Will the face paint stain?","Use non-toxic paint marketed for kids, keep it clear of the eyes, and wash it off the same night with soap and water, not just water."]]},"doctor-bride":{"m":["1 old dark suit or jacket (make: use what you own)","Green face paint, non-toxic, 1 tube (buy: drugstore)","2 plastic neck bolts, costume style (buy: craft store; foil-covered cardboard tubes work too)","1 white dress or old white sheet (make: use what you own)","White hair spray, 1 can (buy: drugstore)","Tape, 1 roll or glue, 1 bottle","Scissors, 1 pair","Dark eye shadow, 1 (make: use what you own)"],"s":["Safety: keep face paint away from the eyes, and patch-test it first on sensitive skin. Wash it off the same night.","The Doctor: paint the face and neck green with the green face paint.","Tape the two plastic bolts to the sides of the neck, and wear the dark suit with the collar up.","Put the white dress or sheet on first and mark the tear line with tape: knee length for walking, longer for photos.","Tear the bottom hem into strips with your hands, starting with small tears you can widen. Torn fabric cannot be untorn, so start shorter than you want.","Smudge dark eye shadow under the eyes.","Optional pro finish: smudge a little green face paint onto the bride's neck and hands too. The green spreading to the bride ties the two halves of the costume together."],"time":"25 min + drying","cost":"$10-14","effort":"Easy","sizing":"Each partner builds their half in their own size. Kids under 8 use a twin flat sheet, tweens and adults use a full flat, and trim the hem so it clears the ground by a few inches. Toddlers trip on hems an adult would clear.","faqs":[["How do you keep the neck bolts on?","Tape each bolt to the collar, not the skin, with two strips of fashion tape or bandage tape. Skin-safe tape only: never superglue."],["Will white hair spray wash out?","Yes with one shampoo. Spray it outside, keep it off clothes, and test a strand first on very dark hair since it can tint temporarily."]]},"emerald-witch":{"m":["1 long green dress, or green fabric, 3 yards (buy: fabric store)","1 sheet black cardboard, 22x28 inches, for the hat (buy: craft store; a box painted black works too)","Green face paint, non-toxic, 1 tube (buy: drugstore)","Black eyeliner, 1, and dark green eye shadow, 1 (buy: drugstore)","Hot glue gun with glue sticks, 1 set and scissors, 1 pair","1 broom from home for a prop (make: use what you own)"],"s":["Safety: let an adult handle the hot glue, since the nozzle and glue get very hot.","Sew or hot glue the green fabric into a long gown, leaving the hem ragged.","Measure the head first, then roll the black cardboard into a tall cone and tape it loosely to check the fit before gluing.","Glue a wide cardboard brim to its base with the hot glue. Hot glue sets fast and cannot be repositioned, so test the cone shape dry first.","Paint the face green with the green face paint. Draw on the black eyeliner and the dark green eye shadow.","Carry the broom bristle-up so it does not trip anyone.","Optional pro finish: fray the gown hem by cutting 2-inch slits every few inches. A ragged hem is the difference between green dress and witch's gown."],"time":"45 min + drying","cost":"$24-34","effort":"Medium","sizing":"Built for teens and adults. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you get green face paint off?","Wash with a gentle cleanser and soap, not just water: green needs soap. Moisturize after, and patch-test on the jawline first if skin is sensitive."],["What if I cannot sew the gown?","Hot glue works: fold the fabric around the body and glue the seam. It holds for one night and nobody sees the seam from the front."]]},"emoji-crew":{"m":["1 yellow t-shirt per person (buy: craft store, or use one you own)","1 large white paper plate, 10-inch, or cardboard circle per person (make: use what you own)","Markers in black, red, and blue, 1 set (make: use what you own)","Scissors, 1 pair and tape, 1 roll"],"s":["Buy yellow t-shirts if the crew does not own them.","Safety: adults handle the scissors when cutting the paper plates or cardboard circles.","Draw the emoji on the paper plate first in pencil, then go over it with the markers.","Trim the plate or cardboard circle only where it overhangs the design. Cut small: a plate trimmed too far looks like a scrap.","Tape the paper plate to the chest of the yellow t-shirt, centered like a face.","Gather the crew in a row for photos, keeping the paper plates taped flat so they do not swing.","Optional pro finish: outline the whole plate edge in black marker. The outline makes the face pop from across the room."],"time":"15 min","cost":"$0-1","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you pick emojis for the crew?","Assign them first so nobody duplicates. Crowd-pleasers: heart-eyes, laughing-crying, and the sunglasses face. Let the shyest person take the poop emoji: it gets the biggest laugh."],["How do you keep the plate from swinging?","Tape it at four points, top, bottom, and both sides, so it sits flat on the chest. Two tape points lets it flap all night."]]},"enchanted-castle-crew":{"m":["Princess: yellow fabric, 2 yards (buy: fabric store)","Prince: 1 blue jacket and 1 pair dark pants (make: use your closet)","Candelabra: gold face paint, 1 tube, and 1 gold headband (buy: craft store)","Clock: 1 brown cardboard circle, about 12 inches, and painted hands (make: from a box)","Teapot: 1 white pot or cardboard pot body (make: from a box)","Hot glue gun, 1; scissors, 1 pair; face paint, 1 set"],"s":["Princess: wrap and pin the yellow fabric as a simple gown. Prince: wear the blue jacket and dark pants with a sash of torn fabric.","Safety: let an adult handle the hot glue, and keep the face paint away from the eyes.","Cut three flame shapes from cardboard first and arrange them dry on the gold headband to check the spacing.","Glue them with the hot glue. Hot glue sets in seconds and cannot be repositioned, so the dry layout is the whole step.","Safety: adults handle the scissors when cutting the cardboard.","Clock: paint the brown cardboard circle cream and add painted hands. Teapot: cut a rounded cardboard pot body, add a handle and spout, and wear it over the shoulders.","Optional pro finish: add a red fabric sash to the prince's blue jacket. The sash is the one detail that turns jacket-and-pants into royalty."],"time":"40 min + drying","cost":"$5-7","effort":"Medium","sizing":"One per person, so kids and adults each get a real fit. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How do you assign roles without fights?","Assign before shopping: princess, prince, candelabra, clock, teapot. Write them on a list and let the youngest pick first."],["How do you keep the teapot body on?","Cut arm holes in the cardboard pot body and wear it like a vest over the shoulders. A body with no arm holes slides off by the second photo."]]},"error-404":{"m":["1 black hoodie (make: use your closet)","1 pair black pants (make: use your closet)","1 sheet white paper, blank (make: use what you own)","1 old phone case or cracked-screen phone protector prop (make: use an old case)","Tape, 1 roll (make: use what you own)"],"s":["Put on the black hoodie and black pants.","Tape a blank sheet of white paper to the front of the hoodie, taping all four corners.","Put the cracked-screen protector or old case on the phone and hold it as if it is still loading.","When asked about the costume, point to the blank page and announce that the costume cannot be found.","Freeze whenever someone talks to you, then reload.","Optional pro finish: let the tape job look slapdash. The messy tape is part of the joke."],"time":"10 min","cost":"$0","effort":"Easy","sizing":"Built for teens and adults. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How does the paper stay on?","Tape all four corners of the paper to the hoodie. Tape sticks to fleece well enough for one evening and peels off after."],["Why is the paper blank?","The blank page is the whole joke: a real 404 has nothing to load. Writing on it just spoils it."]]},"fairy-tale-princesses":{"m":["1 dress from the closet per person (make: use what you own)","1 cereal box per crown (make: from a cereal box)","Gold or silver paint or markers, 1 set (buy: craft store)","Scissors, 1 pair and tape, 1 roll","1 hair ribbon per person (buy: dollar store)"],"s":["Each princess picks any dress from her own closet.","Safety: adults handle the scissors when cutting the cardboard crowns.","Draw the crown shape on the cereal box in pencil first and hold it against the head to check the fit.","Cut the crown with the scissors, leaving a 1-inch tab to tape the ends together. Color it with the gold or silver paint or markers and let it dry.","Tie the hair ribbon as a bow, and tape the cardboard crown on top of the head.","Line up for a princess parade photo, and check that each cardboard crown sits snugly.","Optional pro finish: tie the ribbon as a bow under the crown, not on top. The bow peeking out below the crown looks styled; on top it looks like wrapping."],"time":"15 min + drying","cost":"$9-12","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you keep a cardboard crown on a kid's head?","Tape a bobby pin inside the crown and clip it to the hair. Crowns balanced on top slide off; pinned crowns survive the parade."],["Do the princesses need matching dresses?","No: any dress from the closet works, and different dresses look like different kingdoms. The crowns are what make it a group."]]},"fuzzy-monster":{"m":["1 pastel fuzzy sweatsuit (buy: discount store)","2 large googly eyes, 3 inches or bigger (buy: craft store; paper circles work too)","1 sheet white felt, 9x12 inches, for the smile (buy: craft store; construction paper works too)","Scissors, 1 pair","Fabric glue, 1 tube, or 4 safety pins"],"s":["Glue or pin the two googly eyes to the hood of the pastel fuzzy sweatsuit.","Safety: adults handle the scissors when cutting the white felt.","Draw the smile on paper first and hold it against the sweatsuit chest to check the size: it should span most of the chest.","Cut the stitched-style smile from the white felt with the scissors. Cut it bigger than feels right: small smiles disappear into the fuzz.","Let the fabric glue dry fully before wearing.","Wear the hood up so the googly eyes sit above the forehead.","Optional pro finish: cut two small felt fangs and glue them at the smile's corners. Fangs turn a friendly monster into a funny one."],"time":"15 min + drying","cost":"$14-27","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Googly eyes or paper circles for the eyes?","Googly eyes photograph ten times better and cost a dollar more. Paper circles work if the budget is zero, but they curl in humidity."],["Will the eyes stay on the hood?","Glue them the night before so the fabric glue cures, or pin them with two safety pins each. Same-day glue plus a bouncing kid equals lost eyes."]]},"garden-gnome":{"m":["Earth-tone shirt and pants, 1 set (own)","Cardboard for the hat, 1 sheet (make: from a box)","Blue paint for the hat, 1 small bottle (buy: craft store)","White face paint for the beard, non-toxic, 1 tube (buy: drugstore)","Toy fishing rod or small garden shovel, 1 (buy: dollar store)","Scissors, 1 pair","Tape, 1 roll"],"s":["Safety: adults handle the scissors when cutting the cardboard.","Cut the sheet cardboard to size, roll it into a tall cone, and tape it shut.","Paint the cone with the blue paint for the hat, and let it dry.","Test the face paint on the inside of the wrist first and wait 10 minutes, kids' skin reacts more than you expect.","Use the brown and black non-toxic face paint to draw a round nose and rosy cheeks. Keep all paint clear of the eyes and mouth.","Wear the cone hat with the earth-tone shirt and pants, and carry the toy fishing rod.","Optional pro finish: carry a tiny watering can or a foam mushroom. Gnomes have props, the hat and beard say gnome, the watering can says garden gnome."],"time":"30 min + drying","cost":"$16-22","effort":"Easy","sizing":"Built for teens and adults. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How tall should the gnome hat be?","About as tall as the head. Too short reads as a party hat; too tall flops. Roll the cone, tape it, and test the height before painting."],["Will the face-paint beard smear?","Let it dry fully before the hat goes on, and keep it below the mouth. Bring the tube for touch-ups; white shows every smudge."]]},"ghost-hunters":{"m":["1 khaki or tan jumpsuit, or matching shirt and pants, per person (buy: thrift store)","1 small cardboard box per person, shoebox size (make: use what you own)","White paper, 2 sheets, and markers for name patches (make: use what you own)","1 sheet black cardboard per person (make: from a box)","Packing tape or glue, scissors"],"s":["Tape the small cardboard box shut for the backpack.","Safety: adults handle the scissors when cutting the black cardboard.","Draw the straps, dial, and hose shapes on the black cardboard with marker first and hold them against the box to check the size.","Cut them with the scissors. Cut the hose shape last and widest: it is the most visible piece.","Mark each last name on the white paper with the markers. Tape it to the chest as a name patch.","Wear the backpack over the jumpsuit, and keep the box small and light so kids can wear it all night.","Optional pro finish: write each person's last name on the white paper patch in block letters and tape it to the chest. The name patch is the detail that turns khaki clothes into a uniform."],"time":"30 min","cost":"$3-8","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Have each wearer step into the box before you mark arm and leg holes, cut them a little wide, and tape every inside edge so cardboard never scratches.","faqs":[["How do you keep the backpack box light enough for kids?","Use a small box, shoebox size max, and tape it shut empty. Kids wear it all night only if it weighs almost nothing."],["How do you attach the box to the back?","Tape two ribbon straps to the box like a backpack. Tape alone on the shirt peels; straps distribute the weight."]]},"gloom-bloom":{"m":["1 set black clothes from the closet (make: use what you own)","1 set colorful clothes from the closet (make: use what you own)","Black and white face paint, non-toxic, 1 set (buy: drugstore)","2 hair ties for braids (make: use what you own)","3 to 5 fake flowers (buy: dollar store; paper flowers work too)"],"s":["Gloom: wear the black clothes, and braid the hair tightly with the hair ties.","Paint a small black teardrop under one eye with the black and white face paint.","Bloom: wear the colorful clothes, and pin the fake flowers in the hair.","Paint a small flower on one cheek with the face paint, keeping it clear of the eyes.","Stand side by side: Gloom frowns and looks away, Bloom smiles big.","Optional pro finish: braid the gloom hair tight with a middle part, and pin the bloom flowers all on one side. Opposite styling is what makes the pair read as opposites."],"time":"15 min + drying","cost":"$4-6","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you paint a teardrop that does not smear?","Paint it small under one eye with a thin brush, not a finger, and let it set before touching the face. Fingers smudge; brushes stay sharp."],["What makes the pair read as a duo?","The contrast: one frowns and looks away, one smiles big. Pose the attitude, not just the clothes."]]},"glow-skeleton":{"m":["Black sweatsuit, 1 (buy: discount store, or own)","Glow-in-the-dark bone tape, 1 roll (buy: craft store)","Glow bracelets, 1 pack (buy: dollar store)","Scissors, 1 pair","Black face paint, non-toxic, 1 tube (buy: drugstore)"],"s":["Charge the bone tape under a lamp for 20 minutes for maximum glow.","Safety: adults handle the scissors when cutting the bone tape.","Cut the bone tape into rib bones: lay strips horizontally across the chest and back. Add vertical spine segments down the center, and arm and leg bones down the limbs.","Snap the glow bracelets onto both wrists and both ankles right before heading out.","Test the face paint on the wrist first and wait 10 minutes for any reaction. Paint simple skull eye circles with the black face paint, keeping clear of the eyes so vision stays clear.","Optional pro finish: 'charge' the glow tape under a bright lamp for 10 minutes right before heading out. Freshly charged tape glows dramatically for the first hour, that is when the photos happen."],"time":"20 min + drying","cost":"$16-19","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Does glow tape really glow all night?","No, it fades over 1 to 2 hours. Charge it under bright light right before going out, and bring the roll for touch-ups. The first hour is the magic hour."],["Tape or paint for the bones?","Tape. It is faster, cleaner, peels off after, and actually glows. Painted bones look better in daylight but vanish at night, which defeats the costume."]]},"goggle-crew":{"m":["1 yellow t-shirt per person (buy: craft store, or use one you own)","1 pair denim overalls per person (buy: thrift store, or use one you own)","1 pair swim or safety goggles per person (buy: toy store)","1 pair black gloves per person (buy: dollar store)"],"s":["Each person puts on the yellow t-shirt, the denim overalls, and the black gloves.","Push the goggles up on the forehead like safety gear, not over the eyes, so everyone can see.","Walk in a pack and greet people in gibberish for the full effect.","Skip any real tools or hard hats so the look stays clearly costume, not work gear.","Optional pro finish: push the goggles up on the forehead, never over the eyes. Forehead goggles are the character's signature; over the eyes you just look like a swimmer."],"time":"10 min","cost":"$1-3","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Do the overalls have to be denim?","Denim reads best, but any overalls work. The yellow shirt plus goggles carry the costume; the overalls are the bonus."],["How do you do the voice without annoying everyone?","Keep the gibberish to greetings and photos, then talk normally. Full-time gibberish is funny for ten minutes and exhausting by hour two."]]},"good-witch-bad-witch":{"m":["1 black dress or set of black clothes for the bad witch (make: use your closet)","1 pink dress or set of pink clothes for the good witch (make: use your closet)","Green face paint, non-toxic, 1 tube (buy: drugstore)","1 cardboard crown (make: from a cereal box)","1 black cone hat (buy: dollar store)","Hot glue gun, scissors, 1 pink marker, tape"],"s":["Bad witch: wear the black dress or black clothes.","Safety: let an adult handle the hot glue, and keep the green face paint away from the eyes.","Test the hat brim bend dry before gluing: fold the brim, check it in a mirror, then hot glue it. Hot glue sets in seconds and cannot be repositioned.","Paint the bad witch's face and hands green with the green face paint, keeping paint away from the eyes and patch-testing sensitive skin first.","Good witch: wear the pink dress or pink clothes. Color the cardboard crown with the pink marker, and tape it on the head.","Optional pro finish: color the cardboard crown with the pink marker on both sides. A double-sided crown flashes pink in photos; single-sided flashes brown cardboard."],"time":"20 min + drying","cost":"$4-6","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you get green face paint off kids?","Wash with gentle cleanser and soap the same night, not just water. Green needs soap. Moisturize after and never let them sleep in it."],["What if the cone hat will not stay on?","Tape a bobby pin inside the hat and clip it to the hair. Cone hats are top-heavy and slide without an anchor."]]},"haunted-animatronics":{"m":["1 large cardboard box per person, big enough to cover the head (make: use what you own)","2 red LED tea lights per person (buy: dollar store)","Paint in gray, black, and one accent color, 1 small bottle each (buy: craft store)","1 set old clothes with holes or tears (make: use what you own)","Hot glue gun, 1; scissors, 1 pair; utility knife, 1 (adults only)"],"s":["Safety: an adult handles the utility knife and the hot glue for every cut and glue step.","Mark the eye holes and the wide jagged mouth on the OUTSIDE of the box first, then have the wearer hold the box up to check the eye placement before any cutting.","Cut with the utility knife, adults only, cutting the eye holes generous and the mouth wide. Cardboard cut away cannot be put back, and small eye holes make a blind hazard.","Paint the box gray with black scuffs and cracks. Glue one red LED tea light inside each eye hole.","Safety: make the eye holes large, and never wear the box near stairs or traffic, since side vision is limited.","Wear the box over the head with the eyes lined up to the holes. Wear the old clothes with holes underneath, and move in short jerky steps, freezing between moves.","Optional pro finish: paint black scuffs and cracks around the eye holes before adding the lights. The damage detail is what reads as haunted instead of just boxy."],"time":"60 min + drying","cost":"$3-5","effort":"Medium","sizing":"One per person, so kids and adults each get a real fit. Have each wearer step into the box before you mark arm and leg holes, cut them a little wide, and tape every inside edge so cardboard never scratches.","faqs":[["How do you see out of a box on your head?","Cut the eye holes large and line your eyes up to them before the paint goes on. Never wear it near stairs or traffic: side vision is almost zero."],["How do the red eyes stay lit all night?","LED tea lights run 24 hours plus on one battery. Tape one inside each eye hole with the light facing out, and carry a spare set just in case."]]},"haunted-portraits":{"m":["1 set old-fashioned dark clothes per person, e.g. a vest, long skirt, or button-up (make: use your closet)","Gray and white face paint, non-toxic, 1 set (buy: drugstore)","1 large picture frame or cardboard frame per person (buy: thrift store for the frame, or make from cardboard)","Hair spray or powder for a grayed look, 1 (buy: drugstore)"],"s":["Paint each face pale gray with white highlights on the cheekbones and nose, using the gray and white face paint.","Gray the hair with the hair powder.","Dress in the old-fashioned dark clothes from the closet.","Hold the picture frame or cardboard frame up around the face like a living portrait.","Pose together in a row of frames for group photos, keeping the face paint light around the eyes.","Optional pro finish: dust the hair with the gray powder and add white highlights on the cheekbones and nose. The highlights are what read as painted portrait instead of just pale."],"time":"25 min + drying","cost":"$3-4","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you hold the frame up all night?","You do not: use it for photos only, and set it down between shots. Holding a frame for hours is exhausting; the portrait pose is a photo bit."],["How do you gray the face without looking dirty?","Paint the face pale gray, not dark, and add white highlights on the cheekbones and nose. Dark gray reads as dirt; pale gray with highlights reads as a painting."]]},"headless-horsemen":{"m":["Black cape or black sheet, 1 per person (buy: dollar store, or own: black sheet)","Small jack-o-lantern bucket or foam pumpkin, 1 per person (buy: dollar store)","Broom or stick-horse substitute, 1 per person (own: broom from home)","Tape, 1 roll (own)","Glow bracelets, 1 pack (buy: dollar store)"],"s":["Drape the black cape or black sheet over the shoulders.","Safety: keep your real head tucked low so you can see the ground.","Tuck the chin into the chest, and hold the jack-o-lantern bucket up at shoulder height like a carried head.","Add a glow bracelet to each wrist so drivers can see you in the dark.","Hold the broom between the legs like a horse, and gallop in a group line.","Optional pro finish: put a battery tea light inside each jack-o-lantern bucket. A glowing 'head' reads from a block away and keeps the group visible."],"time":"20 min","cost":"$1-2","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Kids under 8 use a twin flat sheet, tweens and adults use a full flat, and trim the hem so it clears the ground by a few inches. Toddlers trip on hems an adult would clear.","faqs":[["How does the rider see if their head is tucked?","Tuck the chin but keep the eyes looking forward under the cape edge, the cape drapes like a hood, it does not cover the face. If vision is blocked at all, ditch the tuck and just carry the bucket high."],["What do we use if we have no capes?","Black trash bags with head and arm holes cut out, or any dark blanket. The silhouette is what matters: dark shoulders plus a glowing pumpkin at head height."]]},"hero-squad":{"m":["Cape per person in squad colors, 1 each (buy: craft store, or make: cut from 1 yard of fabric each)","Mask per person matching the cape color, 1 each (buy: craft store)","T-shirt per person in the cape color, 1 each (buy: craft store)","Fabric paint for the team emblem, 1 bottle (buy: craft store)","Safety pins, 2 per person (own)"],"s":["Sketch the team emblem on scrap paper and have the whole squad approve it BEFORE opening the paint, painted emblems cannot be unpainted.","Then each hero paints the same emblem, like a lightning bolt, on the t-shirt with the fabric paint.","Let the fabric paint dry fully before wearing.","Safety: keep each cape short enough to clear the ground so nobody trips.","Pin each cape at the shoulders with a safety pin, and wear the matching mask.","End every appearance with the team pose: fists on hips, capes billowing.","Optional pro finish: paint a matching emblem on each cape near the shoulder. Capes with emblems look designed; plain capes look borrowed."],"time":"40 min + drying","cost":"$3-5","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Size the cape to the wearer: it should fall above the knees, and the neck tie stays loose and easy to pull free.","faqs":[["How long does the fabric paint take to dry?","About 1 to 2 hours to stop being tacky, overnight to be safe. Paint the shirts the night before the event or the emblem smears when worn."],["How do you keep capes safe for small kids?","Keep each cape short enough to clear the ground, and pin them with safety pins instead of tying, pinned capes pull free if snagged. Never tie a cape tight around a small child's neck."]]},"ice-cream-cone":{"m":["Tan paper party hat or cone, 1 (buy: dollar store)","White t-shirt, 1 (buy: craft store, or use one you own)","Colored dot stickers or pom-poms for sprinkles, 1 pack (buy: craft store; cut paper dots work too)","Brown paint or marker for the cone crosshatch, 1 (buy: craft store)","Tape, 1 roll (own)"],"s":["Draw a waffle-cone crosshatch on the tan paper party hat with the brown marker.","Set the tan paper party hat on the head like a hat, and tape the elastic so it sits snugly.","Safety: keep small pom-poms away from kids under three, since they are a choking hazard.","Cover the white t-shirt with the colored dot stickers or pom-poms, scattered like sprinkles.","Keep the stickers off the skin.","Optional pro finish: add a red pom-pom 'cherry' to the tip of the hat with a dot of glue. The cherry is what makes strangers say the flavor out loud."],"time":"20 min + drying","cost":"$6-8","effort":"Easy","sizing":"One design, two builds: the kid build fits ages 3 to 10, and the teen and adult build fits everyone older. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you keep the cone hat on all night?","Tape the hat's elastic strap so it fits snug under the chin, and add a second piece of tape inside the hat brim. Paper hats are light; they fall off because the elastic is loose, not because of wind."],["Pom-poms or stickers for the sprinkles?","Stickers for under-5s (no choking risk, nothing falls off). Pom-poms photograph better but shed all night and are a choking hazard for toddlers."]]},"ketchup-mustard":{"m":["1 red t-shirt, 1 yellow t-shirt (make: raid the closet)","Red felt or construction paper, 1 sheet 9x12 inches (buy: craft store, or use paper from home)","Yellow felt or construction paper, 1 sheet 9x12 inches (buy: craft store, or use paper from home)","Safety pins, 8 (buy: dollar store, or raid the sewing kit)","Scissors, 1 pair"],"s":["Pick who is ketchup (red shirt) and who is mustard (yellow shirt). No wrong answer, but decide before you start cutting, it avoids the only argument this costume can cause.","Cut a big blob shape from the red paper, about the size of a dinner plate. Round the edges; a neat circle reads as a sticker, a blob reads as a squeeze of ketchup.","Cut a matching blob from the yellow paper.","Pin the red blob to the yellow shirt and the yellow blob to the red shirt with 4 safety pins each, pinned from inside. Each person wears the OTHER condiment's color, that is the joke.","Optional pro finish: write the nutrition facts on the back of each shirt with a marker ('Serving size: 1 awesome couple'). People will turn you around to read it.","Safety: pin from inside the shirt so no pin backs touch skin, and keep the pins flat, nobody wants a poke during a hug.","Stand side by side and take the photo. The internet has decided this is a top-10 couples costume; you are now contractually obligated to look delighted."],"time":"15 min","cost":"$1","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you keep the paper blobs from tearing?","Pin from inside the shirt with four pins each, and use felt instead of paper if it might rain. Felt survives weather; paper does not."],["Why does each person wear the other condiment's color?","That is the joke, ketchup wears mustard's blob and mustard wears ketchup's. Same-color blobs would just be two people in colored shirts."]]},"little-lion":{"m":["Tan or brown sweatsuit, 1 (buy: discount store, or use one you own)","Brown fuzzy fabric strip or old brown towel for the mane, about 24 inches long (buy: fabric store, or make: cut from a towel)","Scissors, 1 pair (own)","Safety pins or fabric glue, 6 to 8 pins or 1 tube glue (buy: dollar store or craft store)","Brown non-toxic face paint, 1 tube (buy: drugstore)"],"s":["Safety: adults handle the scissors when cutting the brown fuzzy fabric.","Cut a paper collar template first and test it around the sweatsuit hood, a mane cut too small looks like a bib, and fuzzy fabric cut away cannot be put back.","Then cut the brown fuzzy fabric into a wide collar for the mane, cutting generous and trimming after the fitting.","Pin the mane around the hood or neckline of the tan sweatsuit with the safety pins, fluffing it outward.","Safety: pin the mane from inside the sweatsuit, so pin backs face the fabric and never the skin.","Paint a brown nose and whiskers with the brown face paint, keeping clear of the eyes. Skip it for under-twos and any kid who rubs their face.","Pin the mane flat at the back so it does not slip over the eyes while the little lion runs.","Optional pro finish: cut a small triangle tail from the leftover fuzzy fabric and pin it to the back waistband. The tail is what other kids point at."],"time":"20 min + drying","cost":"$12-14","effort":"Easy","sizing":"Built for ages 1 to 8. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you keep the mane out of the kid's face?","Pin the mane around the hood or neckline, not the forehead, and fluff it outward. Pin the back of the mane flat so it cannot slip forward over the eyes when they run."],["Safety pins or fabric glue for the mane?","Pins for anything a toddler wears, you can reposition them, and glue needs 30 minutes of stillness no toddler provides. Glue works fine for older kids who will sit still."]]},"little-pig-family":{"m":["Pink t-shirts or pajamas, 1 per person (buy: thrift store, or own: from closet)","Pink headband, 1 per person (buy: dollar store)","Pink paper cup, 1 per snout (own: from the kitchen drawer)","Pink felt or construction paper, 2 triangles per ear (buy: craft store)","Pink string or yarn, 1 arm length per snout (own: from the craft drawer)","Scissors, 1 pair, and clear tape, 1 roll (own: household tools)","Pink blush or face paint for cheeks, 1 (buy: drugstore)"],"s":["Poke the holes SMALL first with the scissor tip and test the string fit, holes poked too big tear through the cup and the snout falls apart.","Poke two small holes in the sides of a pink paper cup.","Cut one paper ear template first and check the size on the headband, ears should stand about 3 inches tall.","Then cut two pink felt triangles with the scissors and tape them to the pink headband as ears.","Thread the pink string through the holes, then tie the cup gently in front of the nose.","Dab a little pink blush on each person's cheeks with a finger.","Hand the little brother a toy dinosaur from the toy store or one he owns. Now he is the pig who brings the dinosaur.","Optional pro finish: draw two small black nostril dots on the bottom of each cup snout with a marker. Nostrils are the detail that turns a taped cup into a snout."],"time":"25 min","cost":"$10-14","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How do you tie the snout on without it hurting?","Thread the pink string through the holes and tie it loosely behind the head with a bow, never a knot. It should rest against the nose, not press into it, if it leaves a mark, it is too tight."],["The ears keep flopping on the headband. Fix?","Tape each triangle with a tab folded over the band on both sides, not just stuck on one side. The double-sided tab is what keeps felt ears upright."]]},"little-shark":{"m":["Gray hoodie, 1 (buy: thrift store, or own: from closet)","Gray felt, 1 sheet 9x12 inches (buy: craft store; construction paper works too)","White felt, 1 small sheet (buy: craft store; white paper works too)","Fabric glue, 1 tube (buy: craft store)","Scissors, 1 pair (own: household tools)"],"s":["Cut a paper fin template first and hold it against the hoodie back, a fin cut too small disappears on the hoodie, and felt cut away cannot be put back.","Then cut a triangle fin about 8 inches tall from the gray felt, and a jagged row of teeth from the white felt.","Glue the teeth inside the hood edge of the gray hoodie so they show around the face.","Glue the fin to the back of the gray hoodie, low between the shoulders.","Let the fabric glue dry flat for 30 minutes.","Zip the gray hoodie over a white t-shirt and pull the hood up for the shark face.","Optional pro finish: glue two small black felt dots on the hood as eyes above the teeth. Eyes plus teeth is what makes it a shark face instead of a gray hood with trim."],"time":"25 min + drying","cost":"$5-6","effort":"Easy","sizing":"Built for ages 1 to 8. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do the teeth stay glued to the hood?","Fabric glue on the inside hood edge, pressed flat for 30 seconds per tooth, then left to dry flat for 30 minutes. Do not wear the hoodie until the glue is fully set or the teeth peel off."],["Where exactly does the fin go?","Low between the shoulders on the back, not up at the neck. A fin glued too high flops forward over the hood; low and centered stands upright when they walk."]]},"little-witch":{"m":["Black cape or black bedsheet, 1 (buy: dollar store, or make: cut a cape from a black t-shirt)","Pointy witch hat, 1 (buy: dollar store)","Black-and-white striped tights, 1 pair (buy: thrift store or online)","Green non-toxic face paint, 1 tube (buy: drugstore or craft store)","Safety pin or ribbon, 1 (own: from the sewing kit)"],"s":["Pin the cape at the shoulders with the safety pin or tie it with ribbon.","Paint the nose, chin, and forehead lightly green with a fingertip or sponge. Use non-toxic kids' green face paint only.","Pull on the black-and-white striped tights and the pointy witch hat.","Carry a branch from the yard as a broom if one is handy.","Optional pro finish: tie the ribbon in a bow at the front of the cape instead of using a safety pin. A bow at the neck reads as costume; a visible safety pin reads as craft project."],"time":"15 min + drying","cost":"$18-22","effort":"Easy","sizing":"Built for kids ages 3 to 10. Kids under 8 use a twin flat sheet, tweens and adults use a full flat, and trim the hem so it clears the ground by a few inches. Toddlers trip on hems an adult would clear.","faqs":[["How much green face paint for a little witch?","Just the nose, chin, and forehead dabbed on lightly with a fingertip or sponge. A fully green face looks great for ten minutes and then smears on everything they touch."],["What if the cape is too long for a toddler?","Pin it at the shoulders so it hits mid-back, and trim the bottom if it still drags. A cape that reaches the ground on a small kid is a tripping hazard on stairs."]]},"lost-tourist":{"m":["Button-down shirt, 1 (own, to wrinkle on purpose)","Sunglasses and camera or phone on a strap, 1 set (own)","Paper map, 1 (make: print one at home, or draw a fake map on printer paper)","Luggage tag, 1 (buy: office supply store, or make: index card with string)","Clear tape, 1 roll (own)"],"s":["Wrinkle the button-down shirt on purpose. Stuff it in a bag overnight, or ball it up and sit on it for ten minutes.","Write a fake name and hometown on an index card for the luggage tag. Punch a hole in the card and tie on the string.","Tape the luggage tag backwards on one shoulder with the clear tape so it faces the wrong way.","The map is the costume's punchline, fold it wrong-side-out and hold it upside down. A neatly folded map reads as prepared; an upside-down map reads as LOST. Commit to the upside-down.","Hang the camera or phone around the neck and put the sunglasses on top of the head.","Walk around looking at the map upside down.","Optional pro finish: ask strangers for directions to somewhere obvious, in character, all night. The costume is a performance, the map gets you noticed, the bit gets you remembered."],"time":"10 min","cost":"$0","effort":"Easy","sizing":"Built for teens and adults. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["What is the difference between Hawaiian shirt and lost tourist?","The map plus the confusion. Hawaiian shirt is a vibe; lost tourist is a character. Add the upside-down map and the asking-directions bit and it becomes a costume."],["Socks with sandals, really?","Really. It is the single most recognizable tourist signal on earth. White socks, sandals, confidence."]]},"mermaid-crew":{"m":["T-shirt or dress in a sea color (teal, purple, red, white), 1 per person (buy: thrift store, or own)","Face paint in a matching accent color, 1 tube (buy: drugstore)","Plastic trident prop, 1 (buy: toy store)","Toy crab or red paper for a cardboard crab, 1 (make: cut from red paper, or buy: toy store)","Shell necklace, 1 (buy: craft store, or make: string pasta shells)","Scissors and tape, 1 set (own)"],"s":["Sketch the cheek detail on paper first. Face paint is hard to remove and redo once applied. Paint one small matching detail per person: scales on a cheek, a seaweed swirl, or an anchor.","Cut a red paper body, legs, and claws with the scissors and tape them to the smallest person's shirt. Or hand them the toy crab instead.","The sea king carries the plastic trident prop. Everyone else picks one accessory, like the shell necklace, and stands tall for the crew photo.","Optional pro finish: dab the accent face paint along the cheekbones through a fishnet stocking as a stencil. The scale stencil photographs like movie makeup."],"time":"20 min + drying","cost":"$3-4","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["What if we cannot find sea-colored shirts?","Any solid tee works with the accessories doing the work. The trident plus the shell necklace plus one painted detail reads as mermaid crew on any color."],["How do you keep the crab on the shirt?","Tape it from inside the shirt with a big tape loop, or pin it. Do not tape it to bare skin; sweat loosens tape in an hour."]]},"moth-porch-light":{"m":["Neutral shirt and pants in gray, brown, or tan, 1 set (own: from closet)","Large cardboard box, 1 (own: cut two wing shapes from it)","Brown and tan markers or paint, 1 set (buy: craft store)","Brown craft pipe cleaners, 2 (buy: craft store; brown yarn works too)","Headband, 1 (own: from the drawer)","Yellow t-shirt and yellow pants, 1 set (buy: thrift store, or own: from closet)","Cone lampshade, 1 (buy: thrift store)","Tape, 1 roll, and scissors, 1 pair (own: household tools)"],"s":["Draw both wing ovals on the box first and have the moth hold their arms out to check the span.","Wings cut too small look like shoulder pads, and cardboard cut away cannot be put back.","Cut two large oval wing shapes from the large cardboard box with the scissors. Buy the brown craft pipe cleaners, brown and tan markers, and cone lampshade.","Draw eye spots and scalloped edges on the wings with the brown markers. Tape one wing to each arm of the neutral shirt and pants.","Bend the brown craft pipe cleaners into feathery antennae and tape them to the headband for the moth.","Put on the yellow t-shirt and yellow pants. Pop the cone lampshade over the head like a lampshade hat.","Stand next to the moth with arms out, buzzing.","Optional pro finish: curl the wing tips slightly forward and tape them so they cup inward. Real moth wings curve; flat cardboard reads as a sign."],"time":"40 min","cost":"$5-7","effort":"Medium","sizing":"Each partner builds their half in their own size. Have each wearer step into the box before you mark arm and leg holes, cut them a little wide, and tape every inside edge so cardboard never scratches.","faqs":[["How do the wings stay on the arms?","Tape one wing to each sleeve of the neutral shirt with two strips of tape per wing. Tape on fabric holds for an evening; tape the wings to the sleeves, not to skin."],["What size lampshade for the porch light person?","One that fits over the head like a hat without covering the eyes, a medium table-lamp shade works. Check thrift stores; they are a dollar or two."]]},"mystery-crew":{"m":["Orange, purple, blue, and red t-shirts, 1 each (buy: thrift store, or own: from closet)","Dog ears headband or a brown dog costume piece, 1 (buy: dollar store)","Fake magnifying glass, 1 (buy: dollar store, or make: a paper circle taped to a stick)","Headband or scarf in a matching color, 1 per person (own: from the drawer)","Brown non-toxic face paint for the dog's nose, 1 tube (buy: drugstore)"],"s":["Assign roles: orange leader, purple style icon, blue brains, red goofball, and the dog wears the ears.","Each person: put on their color's t-shirt and tie a matching headband or scarf.","The brains carries the fake magnifying glass. Paint a brown nose on the dog with the brown face paint.","Group the four humans in a line with the dog in front. All point at something suspicious for the classic pose.","Optional pro finish: write each person's role on a small paper name tag ('the brains', 'the leader'). The tags turn colored shirts into characters for anyone who does not know the reference."],"time":"15 min + drying","cost":"$2-4","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How do you assign the colors so people get the joke?","Orange leader, purple style icon, blue brains, red goofball, and the dog wears the ears. Assign before anyone dresses so no two people grab the same color."],["What if we only have four people, no dog?","Give the fourth person the dog ears over their colored shirt, the dog role is the most recognizable part, so it beats having a second of any human color."]]},"neon-demon-hunter":{"m":["Black hoodie, black pants, chunky sneakers, 1 set (own)","Neon fabric paint in 2 to 3 colors, 1 tube each (buy: craft store)","Glow-in-the-dark temporary tattoos or neon eyeliner, 1 pack (buy: drugstore)","Foam sword prop, 1 (buy: toy store)","Hair gel or temporary neon hair spray, 1 (buy: drugstore)","Black leather-look jacket or vest, 1 (buy: thrift store, optional)"],"s":["Sketch the demon-slaying symbols on paper FIRST. Crooked symbols cannot be unpainted. Draw sharp neon symbols on the hoodie sleeves and pant legs with the fabric paint. Let dry 2 hours.","Style the hair up with hair gel, or mist it with the temporary neon hair spray. Apply the neon eyeliner or glow-in-the-dark temporary tattoos on the cheeks and arms.","Wear the black leather-look jacket over the hoodie and carry the foam sword prop. Keep the painted side facing out so the neon sigils show.","Optional pro finish: charge the neon paint under bright light before heading out, and add one glowing green 'scar' across the cheek with face paint. The scar is the backstory, everyone will ask about it."],"time":"25 min + drying","cost":"$18-20","effort":"Easy","sizing":"Built for teens and adults. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Does neon fabric paint actually glow?","It glows under blacklight and looks electric in daylight. Under normal indoor light it is just bright. For true night glow, add glow-in-the-dark tape accents."],["Toy sword or foam sword?","Foam. Toy plastic swords snap and leave sharp edges; foam swords survive all-night duels and venue security."]]},"ninja":{"m":["All-black outfit: t-shirt, pants, and a black beanie, 1 set (own: from closet)","Black belt or sash, 1 (own: an old tie or scarf)","Black headband or strip of black t-shirt, 1 strip about 3 inches wide (own: cut from an old shirt)","Scissors, 1 pair, and tape, 1 roll (own: household tools)","Black non-toxic face paint for a mask stripe, 1 tube (buy: drugstore, optional)"],"s":["Measure the strip around the forehead first and mark 3 inches wide BEFORE cutting, a strip cut too narrow digs in, and fabric cut away cannot be put back.","Cut the strip a little long from the old black t-shirt with the scissors; long can be trimmed, short cannot. Put on the black beanie.","Tie the black sash around the waist with the knot at the back, and tuck the ends in.","Safety: keep the eyes and mouth uncovered, and wrap the black headband above the eyes.","Wrap the black headband around the forehead and tie it at the back, leaving the eyes clear.","Paint a thin black stripe across the bridge of the nose with the black face paint. Practice the silent sneaky walk.","Optional pro finish: tuck the headband ends in instead of letting them dangle. Clean lines read as trained ninja; loose ends read as pirate."],"time":"10 min + drying","cost":"$0","effort":"Easy","sizing":"One design, two builds: the kid build fits ages 3 to 10, and the teen and adult build fits everyone older. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How do you wrap the headband so it is safe?","Wrap it above the eyes on the forehead and tie it at the back with a quick-release knot. Eyes and mouth stay completely uncovered, vision first, costume second."],["Do I need the face paint stripe?","No. The all-black outfit plus the forehead wrap already reads as ninja. The stripe is a nice touch for photos but skip it for kids who rub their faces."]]},"office-couple":{"m":["White button-down shirts, 2 (own: from closet)","Name tags, 2 (buy: office supply store, or make: index cards with safety pins)","Toy teapot or a small real teapot, 1 (own: from the kitchen)","Black pants or skirts, 2 (own: from closet)","Marker for writing names, 1 (own: household)"],"s":["Buy name tags, or make them from index cards and safety pins. Pull the white button-down shirts and black pants or skirts from the closet.","Write joke job titles on the name tags with the marker and pin them on the white button-down shirts.","One person carries the toy teapot proudly all evening. The other carries a clipboard or a stack of papers.","Tuck the white button-down shirts in and straighten each other's collars. Introduce yourselves by your fake titles to everyone you meet.","Optional pro finish: write the fake titles in a dead-serious font, like 'Regional Teapot Manager'. The comedy is in how official the name tag looks."],"time":"10 min","cost":"$0","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["What are good joke job titles?","Pick titles that match the props: 'Director of Teapot Operations' for the teapot carrier, 'VP of Paperwork' for the clipboard holder. Specific beats random."],["Is a real teapot okay to carry around?","A small empty one is fine, but a toy or plastic teapot is better, real ceramic breaks if set down hard, and a full teapot is heavy by hour two."]]},"pbj":{"m":["Brown t-shirt, 1 (buy: thrift store, or own: from closet)","Purple t-shirt, 1 (buy: thrift store, or own: from closet)","White poster board, 2 sheets (buy: dollar store)","Markers, 1 set (own: household)","Scissors, 1 pair, and tape or string, 1 roll or spool (own: household tools)"],"s":["Draw the bread shape on the poster board first and hold it against the t-shirt to check the size.","Bread cut too small looks like a badge, and poster board cut away cannot be put back.","Cut two big sandwich-bread shapes from the white poster board with the scissors, cutting generous and trimming after the fitting. Buy the brown t-shirt, purple t-shirt, and white poster board if needed.","Write 'PB' in big letters on one bread shape and 'J' on the other with the markers.","Tape or string one bread sign to the front of the brown t-shirt. Tape or string the other to the front of the purple t-shirt.","Stand pressed together all evening, bread sides out. The brown-shirt person is the peanut butter and the purple-shirt person is the jelly.","Optional pro finish: draw a wavy crust edge around each bread shape with a tan marker. The crust line is what makes it read as bread instead of a white sign."],"time":"20 min","cost":"$1-2","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Which side is peanut butter and which is jelly?","Brown shirt is peanut butter, purple shirt is jelly. Label the bread signs 'PB' and 'J' big enough to read from ten feet away so nobody has to ask."],["How do you wear the bread signs?","Tape or string one bread sign to the front of each t-shirt like a sandwich board front panel. Two attachment points at the top corners keep it from spinning."]]},"peas-pod":{"m":["Green t-shirts, 1 per person for 3 to 5 people (buy: thrift store, or own: from closet)","Green felt, 1 yard (buy: craft store; green fabric works too)","Green fabric paint, 1 bottle (buy: craft store)","Hot glue gun or fabric glue, 1 (buy: craft store)","Green non-toxic face paint, 1 tube (buy: drugstore)","Scissors, 1 pair (own: household tools)"],"s":["Lay the group out and chalk the pod outline on the felt against their actual lineup BEFORE cutting, a pod cut too short strands a pea outside, and felt cut away cannot be put back.","Cut the green felt into one long pod shape with the scissors, about 6 feet long, with a pointed top, cutting long and trimming later.","Buy the green felt, green fabric paint, and hot glue gun.","Paint darker green stripes and a center seam line down the pod with the green fabric paint. Let the paint dry for 1 hour.","Safety: let an adult handle the hot glue gun, and keep fingers away from the nozzle.","Glue the pod to the front of the green t-shirts so it stretches across all of them. Space the wearers evenly.","Paint a small green circle on each person's cheek with the green face paint. Line everyone up in height order under the pod and walk together in a row.","Optional pro finish: paint each person's name on the pod next to their spot. Named peas turn a group costume into a keepsake photo."],"time":"60 min + drying","cost":"$4-6","effort":"Medium","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How many people make a good pea pod?","Three to five. Two looks thin, six stretches the felt so far the pod sags. Three peas in a pod is the classic for a reason."],["How do the peas stay lined up while walking?","Space the wearers evenly and walk in a row at the same pace, practice once before going out. The pod is one piece, so if one person rushes, the whole pod bunches."]]},"penguin-huddle":{"m":["Black long-sleeve shirts, 1 per person (buy: thrift store, or own: from closet)","White felt, 1 sheet 9x12 inches per person (buy: craft store; white paper works too)","Orange felt, 1 sheet 9x12 inches per person (buy: craft store; orange paper works too)","Headbands, 1 per person (buy: dollar store)","Fabric glue, 1 tube (buy: craft store)","Scissors, 1 pair (own: household tools)"],"s":["Cut one paper belly template first and check it against a shirt, a belly cut too small looks like a bib, and felt cut away cannot be put back.","Then cut an oval white belly from the white felt with the scissors for each person. Buy the white felt, orange felt, headbands, and fabric glue.","Cut a small orange triangle beak from the orange felt for each headband. Glue one beak to the front of each headband with the fabric glue.","Glue the white bellies to the front of the black long-sleeve shirts. Let the fabric glue dry for 30 minutes.","Each person: put on the black long-sleeve shirt and the headband with the beak. Tuck hands into the sleeves as flippers and waddle shoulder to shoulder in the huddle.","Optional pro finish: cut two small orange felt feet shapes and tape them over the toes of dark shoes. Feet are the detail people notice in full-body photos."],"time":"35 min + drying","cost":"$1-3","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How big should the white belly be?","An oval that covers the chest from collarbone to waistband. Too small reads as a badge; chest-size reads as a penguin belly instantly."],["How do you keep the beak on the headband?","Glue one orange triangle beak to the front of each headband with fabric glue and let it dry flat for 30 minutes. Glue beats tape here, tape peels off headbands by the second hour."]]},"pickle":{"m":["Green tunic or oversized green t-shirt, 1 (buy: thrift store, or own: from closet)","Green bubble wrap or green pom-poms, about 20 bumps (buy: craft store, or make: twist bits of green fabric)","Fabric glue, 1 tube (buy: craft store)","Green non-toxic face paint, 1 tube (buy: drugstore)"],"s":["Lay out all the bumps on the tunic DRY first and step back to check the pattern is even, once fabric glue sets, bumps cannot be moved.","Space them in a loose grid so no bare patches show. Glue the bumps all over the front and back of the tunic for the bumpy pickle texture.","Let the fabric glue dry flat for 30 minutes.","Paint the face, then draw on a smug grin with one raised eyebrow.","Wear the tunic over regular clothes and stand tall.","Optional pro finish: add a slightly darker green felt band at the top and bottom of the tunic. The bands frame the bumps and make it read as a whole pickle instead of a bumpy shirt."],"time":"30 min + drying","cost":"$12-14","effort":"Easy","sizing":"Built for teens and adults. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Bubble wrap or pom-poms for the bumps?","Pom-poms look better and stay put; bubble wrap pops when people hug you and goes flat by midnight. If you use bubble wrap, pop it yourself first for a dimpled texture that lasts."],["How much of the face should be green?","Full face in a light layer, keeping it clear of the eyes. A half-green face reads as sick; a full light-green face with a smug grin reads as pickle."]]},"pixel-ghost":{"m":["White bedsheet or white fabric, 1 twin-size (buy: thrift store)","Black felt, 1 sheet 9x12 inches (buy: craft store; black paper works too)","Fabric glue, 1 tube (buy: craft store)","Scissors, 1 pair (own: household tools)","Marker and ruler, 1 each (own: household)"],"s":["Fold the sheet in half and chalk the zigzag line first, holding it against the wearer to check the length.","A hem cut too short cannot be fixed, and this is the bottom edge of the whole costume.","Cut the bottom edge into chunky square zigzags with the scissors, about 4 inches per square, cutting long and trimming later. Buy the white bedsheet and the black felt.","Draw two square eyes and a square mouth on the black felt with the marker and ruler. Cut them out.","Glue the felt eyes and mouth onto the top third of the white bedsheet. Let the fabric glue dry for 30 minutes.","Safety: keep the eye area open so vision stays clear.","Wear dark clothes underneath and drape the white bedsheet over the head with the eyes lined up. Cut two small arm slits if reaching through is hard.","Optional pro finish: cut two small arm slits at the sides. Reaching through slits instead of lifting the whole sheet keeps the ghost shape intact all night."],"time":"30 min + drying","cost":"$7-9","effort":"Easy","sizing":"Built for kids, tweens, and adults. Kids under 8 use a twin flat sheet, tweens and adults use a full flat, and trim the hem so it clears the ground by a few inches. Toddlers trip on hems an adult would clear.","faqs":[["How do you keep the pixel edges crisp?","Use the ruler and marker to draw the zigzag grid before cutting, and cut on the lines. Freehand zigzags wobble; measured squares read as pixels."],["How does the wearer see?","Wear dark clothes underneath, drape the sheet over the head, and leave the face area open under the felt eyes, the eyes are decoration on the sheet, not eye holes. Vision stays fully clear."]]},"pizza-slice":{"m":["Large cardboard box, 1 (make: cut a big triangle, about 3 feet tall)","Yellow and orange acrylic paint, 1 bottle each (buy: craft store)","Red felt, 1 sheet (buy: craft store; red paper works too)","Brown felt scraps for crust, or 1 brown paper bag (buy: craft store)","Paintbrush, scissors, tape, 1 set (own)","Fabric glue, 1 tube (buy: craft store)"],"s":["Paint the whole triangle a golden yellow-orange with the paintbrush and let it dry 1 hour.","Arrange the pepperoni on the triangle DRY first. Pepperoni clusters in the middle if you glue as you go.","Cut red felt circles and glue them spread out, then add the brown crust strip along the wide end.","Tape two string loops to the back so it wears like a sandwich board. Keep the crust at the top and the point at the bottom.","Optional pro finish: add green felt 'peppers' and white felt 'cheese drips' along the top edge. Toppings are what separate a pizza slice from a yellow triangle."],"time":"45 min + drying","cost":"$6-7","effort":"Medium","sizing":"One design, two builds: the kid build fits ages 3 to 10, and the teen and adult build fits everyone older. Have each wearer step into the box before you mark arm and leg holes, cut them a little wide, and tape every inside edge so cardboard never scratches.","faqs":[["How do you make it read as pizza, not just yellow?","The crust strip along the bottom is the key, a yellow shirt with pepperoni is ambiguous, with a crust it is pizza. Add the crust."],["Slice or whole pizza for a group?","One slice each, standing in a circle, makes a whole pizza when you huddle. The group photo where you form the pizza is the whole point."]]},"plague-doctor":{"m":["Long black coat or black robe, 1 (buy: thrift store)","Wide-brim black hat, 1 (buy: dollar store)","Black half mask or sunglasses, 1 (buy: dollar store)","Cardboard or craft foam for the beak, 1 sheet 9x12 inches (buy: craft store; stiff paper works too)","Black gloves, 1 pair (buy: dollar store)","Hot glue gun, 1 (buy: craft store)","Black spray paint or black markers, 1 can or set (buy: craft store)"],"s":["Cut a paper beak template first and hold it against the mask to check the curve and length.","A beak cut too long looks silly and one cut too short looks stubby, and neither can be fixed after cutting.","Cut a long curved beak shape from the cardboard or craft foam with the scissors. Buy the coat, hat, mask, gloves, hot glue gun, and beak materials.","Safety: let an adult handle the hot glue gun, and keep fingers away from the nozzle.","Paint the beak black with the black spray paint and let it dry. Hot-glue the beak to the front of the black half mask so it juts out.","Safety: fit the black half mask so the eyes are fully open. Never wear a mask that blocks peripheral vision.","Cut round eye holes in the black half mask and fit it so the eyes are fully open.","Wear the long black coat, wide-brim black hat, black gloves, and the beaked mask together. Carry a wooden staff or walking stick for the full effect.","Optional pro finish: paint the finished beak with a second light coat and let it dry fully. One thin coat looks gray in flash photos; two coats read as true black."],"time":"60 min + drying","cost":"$25-44","effort":"Medium","sizing":"Built for teens and adults. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you attach the beak to the mask?","Hot-glue the beak to the front of the black half mask so it juts forward, with an adult handling the glue gun. Test the fit before gluing, the mask must sit so the eyes are fully open."],["Is the mask safe to wear while walking around?","Only if the eyes are fully open with clear peripheral vision. Never wear a mask that blocks side vision near stairs, streets, or crowds, take it off to walk between houses."]]},"player-one-two":{"m":["Matching t-shirts, 2, any color (buy: thrift store, or own: from closet)","Iron-on letters or fabric markers, spelling 1 and 2 (buy: craft store)","Toy game controllers, 2 (buy: toy store, or make: draw one on cardboard)","Iron, 1 (own: household)"],"s":["Put a big '1' on the front and back of one t-shirt with the iron-on letters. Put a big '2' on the front and back of the other t-shirt.","Safety: let an adult handle the hot iron on a hard surface.","Pin or tape the letters to the shirts and check the size and position in a mirror BEFORE heating the iron, ironed letters cannot be repositioned.","Iron the letters onto the t-shirts on a hard surface with an adult handling the iron, or draw them with the fabric markers.","Each player: wear their numbered t-shirt and carry a toy game controller.","Walk in together, controllers up, and argue good-naturedly all evening about who is really player one.","Optional pro finish: add a small 'INSERT COIN' label under each number with a fabric marker. It is the detail that gets the laugh from anyone over thirty."],"time":"20 min","cost":"$2","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["No iron, what is the best alternative?","Fabric markers, drawn big. Iron-on looks cleaner but marker numbers survive the night fine, and you can skip the whole adult-with-a-hot-iron step."],["How big should the numbers be?","Chest-filling: about 8 inches tall on an adult shirt, 5 inches on a kid shirt. Numbers smaller than that disappear in group photos."]]},"plug-socket":{"m":["Cardboard box, 1 large (own: cut two flat panels, one per person)","Gray and white acrylic paint, 1 small bottle each (buy: craft store)","Black markers, 1 set (own: household)","Craft foam, 1 sheet 9x12 inches (buy: craft store; cardboard works too)","Tape, 1 roll, and string, 1 spool, for wearing (own: household tools)","Scissors, 1 pair (own: household tools)"],"s":["Mark the panel size against each wearer BEFORE cutting, a panel cut too small looks like a badge and one cut too big bangs knees, and cardboard cut away cannot be put back.","Cut two cardboard panels from the large box with the scissors, each about 2 feet square, one per person, cutting generous and trimming later. Buy the gray and white acrylic paint and the craft foam.","Make the plug: paint one panel gray. Draw two prongs on the craft foam, cut them out, and tape them sticking up from the top edge.","Make the socket: paint the other panel white. Draw two dark slots and a round outlet face with the black markers.","Fix the string to the back corners of each panel with tape so they hang like sandwich boards. The plug person stands next to the socket person.","Optional pro finish: paint a small lightning bolt between the two panels' meeting edges. The bolt sells the 'about to connect' joke in photos."],"time":"45 min + drying","cost":"$1-2","effort":"Easy","sizing":"Each partner builds their half in their own size. Have each wearer step into the box before you mark arm and leg holes, cut them a little wide, and tape every inside edge so cardboard never scratches.","faqs":[["How do the panels stay on?","Fix string to the back corners of each panel with tape so they hang like sandwich boards, front and back. Two strings per panel, not one, so nothing spins around."],["Cardboard prongs or foam prongs for the plug?","Craft foam, it is light, it will not poke anyone, and it tapes on cleanly. Cardboard prongs snap off by the second hour."]]},"plumber-duo":{"m":["Blue overalls, 2 (buy: thrift store)","Red t-shirt and green t-shirt, 1 each (buy: thrift store, or own: from closet)","Red cap and green cap, 1 each (buy: dollar store)","Brown non-toxic face paint for mustaches, 1 tube (buy: drugstore)","White circle stickers or white paper, 2 about 2 inches across (buy: dollar store)","Marker, 1 (own: household)"],"s":["Write a big 'M' on one white circle and an 'L' on the other with the marker. Stick or tape them to the front of the red cap and green cap.","Each brother: wear the blue overalls over their colored t-shirt and cap. Paint on a mustache with the brown face paint.","The red brother gets a big bushy one, and the green brother gets a thinner one.","Roll the overall cuffs once and strike the jump pose with a fist in the air. Talk about fixing pipes all night.","Optional pro finish: roll the overall cuffs once and scuff the knees with a little brown face paint. Work-worn overalls read as plumbers; crisp new ones read as a uniform costume."],"time":"15 min + drying","cost":"$16-29","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you tell the two plumbers apart?","Red shirt and cap with an 'M' circle for the older brother, green with an 'L' for the younger. The cap letters are the tell, get them on straight and centered."],["How do you paint a mustache that lasts?","Brown face paint with a fingertip, two coats, keeping it above the lip line. It fades when eating, so bring the tube for a touch-up halfway through the night."]]},"pocket-plush":{"m":["Fuzzy one-piece pajamas or sweatsuit, 1 (buy: thrift store, or own: from closet)","Felt ears: two big felt circles, about 4 inches across (buy: craft store; construction paper works too)","Fabric glue, 1 tube (buy: craft store)","Black and white felt for eyes and smile, 1 small sheet each (buy: craft store; paper works too)","Large shipping tag or big index card, 1 (buy: office supply store)","Marker, 1 (own: household)"],"s":["Cut the eyes and smile from paper first and lay them on the pajama chest to check the size and spacing, glued felt cannot be repositioned.","Then cut two white felt eyes and a stitched-look smile from the black felt, and glue them to the chest of the fuzzy pajamas with the fabric glue.","Write a collector number like 'No. 001' on the large shipping tag with the marker. Tie the tag to the wrist or waistband with string.","Wear the fuzzy one-piece pajamas with the felt ears and large shipping tag showing. The smile goes on the chest like a plush's embroidered face.","Optional pro finish: stitch the smile with dashed lines using a white fabric marker instead of a solid line. Dashed stitches read as plush embroidery; a solid line reads as a drawing."],"time":"25 min + drying","cost":"$7-8","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do the ears stay on the hood?","Fabric glue with the hood laid flat, left to dry for 30 minutes before wearing. For a same-night build, safety-pin them from inside the hood instead, pins hold immediately."],["What do you write on the shipping tag?","A collector number like 'No. 001' plus the plush name. The tag is the joke, so make it look official: big number, neat letters."]]},"popcorn-bucket":{"m":["Cardboard box, 1 medium (make: tall enough to cover the torso)","Red and white striped wrapping paper or paint, 1 roll (buy: dollar store or craft store)","Yellow or white balloons, 8 to 10 (buy: dollar store)","Tape, string, scissors, 1 set (own)","Red marker for the label, 1 (own)"],"s":["Cut the head and arm holes SMALL first and test the fit. Holes cut too big cannot be shrunk. Tape the inside edges of the holes so the cardboard does not scratch.","Blow up the yellow or white balloons and tie them in a cluster. Tie the cluster to a string ring that sits on top of the box like overflowing popcorn.","Step into the box and pull the string straps over the shoulders. Carry the popcorn crown carefully through doorways.","Optional pro finish: glue a few 'popcorn' pieces to the rim as if overflowing. Overflowing reads as fresh and generous; a flat top reads as empty."],"time":"30 min + drying","cost":"$5-6","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Have each wearer step into the box before you mark arm and leg holes, cut them a little wide, and tape every inside edge so cardboard never scratches.","faqs":[["Balloons or tissue paper for the popcorn?","Tissue paper, crumpled white tissue looks like popcorn and weighs nothing. Balloons pop and squeak all night."],["How do you wear the bucket?","Cut the bottom out and wear it like a tunic: head through the top, arms through side holes. The popcorn sits on your shoulders like you are the bucket."]]},"prince-princess":{"m":["Gold paper crown or plastic crown, 1 (buy: dollar store, or make: cut one from gold poster board)","Cape or long piece of fabric, 1 about 3 feet long (buy: thrift store)","Thrifted gown or long dress, 1 (buy: thrift store)","Tiara, 1 (buy: dollar store)","Toy scepter or wand, 1 (buy: dollar store)"],"s":["The prince: wear the gold paper crown and cape over dark clothes, and carry the toy scepter.","The princess: wear the thrifted gown and tiara, and add the spare wand if there is one.","Walk in with royal posture, wave slowly with a bent wrist, and address everyone as 'my good subject'.","Optional pro finish: give the prince a sash of torn fabric across the chest. A sash plus a crown reads as royalty; a crown alone reads as a party hat."],"time":"10 min","cost":"$8-14","effort":"Easy","sizing":"Each partner builds their half in their own size. Size the cape to the wearer: it should fall above the knees, and the neck tie stays loose and easy to pull free.","faqs":[["How do you keep a paper crown on all night?","Size it snug and tape the join on the inside, then add two bobby pins through the crown into the hair. Paper crowns fail at the join, so reinforce the join before anything else."],["What should the prince wear under the cape?","Dark clothes, black pants and a dark shirt. The cape and crown are the costume; light or busy clothes underneath fight them."]]},"rain-cloud-rainbow":{"m":["Gray t-shirt or sweatshirt, 1 (buy: thrift store, or own: from closet)","White cotton balls or polyester stuffing, 1 bag (buy: dollar store or craft store)","Blue paper raindrops, about 15 (own: cut from blue construction paper)","String, 1 spool, and tape, 1 roll (own: household tools)","Fabric glue, 1 tube (buy: craft store)","Rainbow-striped shirt, 1, or a white shirt, 1, plus rainbow fabric markers, 1 set (buy: thrift store or craft store)","Blue non-toxic face paint for one rain streak, 1 tube (buy: drugstore, optional)"],"s":["Arrange the cotton balls on the shirt DRY first and step back to check the cloud coverage, once fabric glue sets, cotton balls cannot be moved.","Plan for full coverage with no gray showing through the middle. Then glue the cotton balls in clumps across the gray t-shirt to make clouds.","Fix the blue paper raindrops to short pieces of string with tape. Hang the strings from the bottom edge of the gray t-shirt so they dangle.","The rainbow person: wear the rainbow-striped shirt, or draw rainbow arcs across a white shirt with the rainbow fabric markers.","Stand side by side: the cloud holds arms out wide. The rainbow stands just behind, peeking out after the 'storm'.","Add one blue rain streak on a cheek with the blue face paint if you like.","Optional pro finish: hang the raindrops at staggered lengths, not all even. Uneven drops look like real rain; a straight row looks like a mobile."],"time":"30 min + drying","cost":"$5-6","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How many cotton balls for a full cloud shirt?","Most of a dollar-store bag, plan on 40 to 60 for an adult shirt, 25 to 35 for a kid. Skimpy clouds show gray through the middle and read as lint, not weather."],["How do the raindrops stay hanging?","Fix each blue paper raindrop to a short piece of string with tape, then tape the strings along the bottom edge of the shirt. Short strings, about 4 inches, tangle less than long ones."]]},"ramen-bowl":{"m":["Large cardboard circle, about 2 feet wide (make: cut from a big box)","White and red acrylic paint, 2 small bottles (buy: craft store)","Yellow yarn, 1 skein (buy: craft store; yellow string works too)","White craft foam or 1 foam ball (buy: craft store; white paper works too)","Chopsticks, 1 pair (own: kitchen drawer)","Tape and string, 1 roll and about 2 feet (own: household)","Scissors, 1 pair"],"s":["Test the bowl rim size before cutting: hold the cardboard up and mark where it should sit as a hat.","Cut the cardboard circle into a wide bowl rim shape with the scissors, cutting a little larger than you think since you can trim it down but cannot add cardboard back.","Paint it white with a red stripe and let it dry fully, about 1 hour.","Make the noodles: cut dozens of 12-inch yellow yarn strands. Fasten them in a tangled layer across the top of the dry bowl rim with the tape.","Cut the white craft foam into a half egg shape and paint a yellow yolk dot on it.","Let it dry, then tape the egg on top of the noodles and stick the chopsticks in at an angle.","Wear the bowl rim like a hat with string under the chin, noodles and egg on top. Slurp loudly for effect.","Optional pro finish: glue two real wooden chopsticks crossed at the top of the noodles, and tape a paper logo circle to the bowl rim so it reads as a branded ramen bowl."],"time":"50 min + drying","cost":"$6-7","effort":"Easy","sizing":"One design, two builds: the kid build fits ages 3 to 10, and the teen and adult build fits everyone older. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you wear the bowl so it does not fall off?","Wear the bowl rim like a hat with string tied under the chin, noodles and egg on top. Keep the string snug but loose enough to slip a finger under."],["What can you use instead of yellow yarn for the noodles?","Yellow string, shredded yellow paper, or thin strips of a yellow plastic bag all read as noodles. Tape them in a tangled layer so they look piled, not combed."]]},"raptor-ranger":{"m":["Khaki shirt and hat for the ranger, 1 set (own: from closet, or buy at a thrift store)","Green hoodie or green t-shirt for the raptor, 1 (own: from closet)","Green felt sheet, 9x12 inches, 1 (buy: craft store; construction paper works too)","Rope, 3 feet, or 1 toy dog leash (buy: pet aisle)","Face paint, green and black, 1 set (buy: costume aisle or craft store)","Scissors, 1 pair, and tape, 1 roll (own: household)"],"s":["Decide who is the ranger and who is the raptor, then lay out both outfits. Buy the 3 ft rope or toy dog leash and the face paint if you do not have them.","Safety: cut the green felt sheet slowly and keep fingers clear of the scissors.","Draw the tail shape on the felt first and hold it up to the raptor's back to check the length before cutting, since a too-short tail cannot be lengthened.","Then cut one long triangle from the green felt sheet for the tail. Tape it to the back of the raptor's green shirt so it hangs behind them.","The ranger wears the khaki shirt and hat with the toy dog leash in hand. The raptor wears the green shirt with the tail attached.","Safety: use non-toxic kids face paint, and skip any mask so the raptor can see clearly.","Paint the raptor's snout: use the green face paint to draw a snout and two black dots for nostrils. Then the ranger holds the toy dog leash out toward the raptor for photos.","Optional pro finish: tie the rope as a belt around the ranger's waist and clip a toy walkie-talkie to it for the field-guide look."],"time":"25 min + drying","cost":"$5-8","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How long should the leash be?","Keep the leash short, about 2 to 3 feet, so the toy dinosaur does not drag on the ground. Tie the wrist end in a loop so it cannot tighten."],["What face paint is safe for kids?","Use non-toxic kids face paint and skip any mask so the raptor can see clearly. Keep paint off the lips and wash it off the same night."]]},"referee":{"m":["Plain black t-shirt or long-sleeve shirt, 1 (own: from closet)","Black pants or shorts, 1 pair (own: from closet)","White athletic tape, 1 roll (buy: sporting goods or pharmacy)","Plastic whistle, 1 (buy: dollar store or sporting goods)","Yellow fabric square, 6x6 inches (own: cut from an old cloth or napkin)"],"s":["Tear horizontal strips of the white athletic tape across the front and back of the black shirt. Space them about 2 inches apart and press firmly so they stay.","Fold the yellow fabric square in half and tie it in a knot around the whistle lanyard. Or tape it to the whistle so it waves when you blow the whistle.","Wear the black outfit with the striped shirt and put the whistle around your neck. Tuck the yellow flag in a pocket.","Optional pro finish: add a black wristband on one wrist and carry the yellow flag tucked in a back pocket, hidden until the call."],"time":"20 min","cost":"$4-6","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Will the athletic tape stay on the shirt all night?","Press each strip firmly onto a clean, dry shirt and the tape holds for the evening. It peels off after, though it can pull lint on fuzzy fabrics, so test a hidden spot first."],["What can I use instead of a real whistle?","A toy whistle from a party favor pack works, or just mime blowing it. Skip loud metal whistles around small kids."]]},"robot-crew":{"m":["Medium cardboard box per person, 1 each (make: from home or moving boxes)","Small cardboard box per person for the head, 1 each (make: from cereal or shoe boxes)","Aluminum foil, 1 large roll (buy: grocery store)","Plastic bottle caps, about 20 total (own)","Duct tape, 1 roll (buy: hardware store)","Black permanent marker, 1 (own)","Elastic string or yarn, 6 feet (buy: craft store)","Glow sticks, 1 per person (buy: dollar store)"],"s":["Cut the eye holes BIG. You can cover extra space with foil, but you cannot add cardboard back. Cut the boxes slowly and keep fingers clear of the scissors.","Cut head and arm holes in each medium cardboard box so they slide over the torso. Cut eye holes in the small cardboard boxes for heads.","Wrap every box in aluminum foil, taping the foil down with duct tape.","Draw dials and gauges on the chest with the black permanent marker. Tape the plastic bottle caps next to the dials as buttons.","Wrap leftover aluminum foil around each arm from wrist to shoulder and tape the ends with duct tape. Or cut the armholes in the torso box big enough to slide bare arms through.","Each person slides into a torso box and holds or ties the small cardboard box on their head.","Tie the elastic string under the chin to keep the head box on. Crack a glow stick and tape it to the chest as a power light.","Optional pro finish: give each robot a name badge ('UNIT 7', 'BEEP BOOP'). Named robots get talked to; unnamed robots get looked at. The badge is the personality."],"time":"45 min","cost":"$3-4","effort":"Medium","sizing":"One per person, so kids and adults each get a real fit. Have each wearer step into the box before you mark arm and leg holes, cut them a little wide, and tape every inside edge so cardboard never scratches.","faqs":[["How do you keep a robot crew looking like a crew?","Same silver, same box proportions, different button layouts. Uniform base plus unique details, that is the crew formula."],["What is the best robot crew move?","Move in sync, stop, turn heads together, beep in unison. Synchronized robots are ten times funnier than individual robots."]]},"robot-ranger":{"m":["Medium cardboard box for the torso, 1 (own: from home)","Aluminum foil, 1 roll (buy: grocery store)","Flexible aluminum dryer vent hose, 1 section about 3 feet (buy: hardware store)","Sticker dots or round stickers, 1 sheet (buy: craft store; punched paper circles work too)","Duct tape, 1 roll (buy: hardware store)","Blue or gray sweatsuit to wear underneath, 1 set (own: from closet)","Black marker, 1 (own: from home)","Scissors, 1 pair"],"s":["Safety: cut the cardboard box slowly and keep fingers clear of the scissors. The dryer vent hose has sharp wire edges, so cut carefully and tape the ends right away.","Before cutting, wear the box over your head and trace circles for the head and arm holes a little bigger than you need.","Cut the holes SMALLER than traced first, since you can widen them but cannot shrink them. Then wrap the box in aluminum foil like a gift, taping the foil flat.","Draw two round gauges on the foil chest with the black marker. Stick the sticker dots on as dial needles and button lights.","Hold the hose pieces against your arms to measure the length before cutting, and cut longer than you need since cut hose cannot be repaired.","The dryer vent hose has sharp wire edges, so tape the ends right away so the wire ribs stay put.","Tape the top of each piece to the shoulder holes of the box so arms slide inside.","Dress in the blue or gray sweatsuit and slide the foil-wrapped cardboard box over the head and arms. Press the sticker dials on last so they sit on the chest.","Optional pro finish: add a big red sticker dot as an emergency button on the chest, and draw a small speaker grille under it with the black marker."],"time":"60 min","cost":"$17-20","effort":"Medium","sizing":"One per person, so kids and adults each get a real fit. Have each wearer step into the box before you mark arm and leg holes, cut them a little wide, and tape every inside edge so cardboard never scratches.","faqs":[["How do you handle the sharp edges on the vent hose?","Cut carefully and tape both ends immediately so the wire ribs stay put. Wear the sweatsuit underneath so no foil or wire touches bare skin."],["Can the kid see and breathe inside the box?","Cut the head hole generous and keep the box loose on the shoulders. Never tape the box to the head, and take it off indoors in crowds."]]},"safari-photographer":{"m":["Khaki vest with pockets, 1 (buy: thrift store, or wear a tan button-down from closet)","Khaki pants or shorts, 1 pair (own: from closet)","Toy camera, 1 (buy: dollar store, or make: draw a camera on cardboard and tape a strap)","Toy binoculars, 1 (buy: dollar store; two paper towel rolls taped together work too)","Stuffed lion or lion cub toy, 1 (buy: thrift store or toy aisle)","Safari hat, 1 (buy: costume aisle, or wear any wide-brim hat from home)","Scissors, 1 pair; tape, 1 roll; marker, 1 (own: household)"],"s":["Buy or gather the toy camera, toy binoculars, stuffed lion or lion cub toy, and safari hat.","Pull the khaki pants and khaki vest from the closet.","Safety: cut the cardboard slowly and keep fingers clear of the scissors.","Sketch the camera shape on the cardboard first and cut one size up, then trim down after a test fitting.","To make the camera: cut a camera shape from cardboard and draw a lens with a marker. Tape a ribbon or belt through it as a strap.","Dress in the khaki pants, khaki vest, and safari hat. Hang the toy camera around your neck and the toy binoculars over the shoulder.","Finishing touch: tuck the stuffed lion under one arm and practice your best explorer pose.","Optional pro finish: make a press pass on an index card (name plus STAFF PHOTOGRAPHER) and hang it from a lanyard or string."],"time":"20 min","cost":"$8-10","effort":"Easy","sizing":"Built for teens and adults. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["What is the cheapest way to make the binoculars?","Tape two empty paper towel rolls together and color them black with a marker. Thread a string through them as a neck strap."],["Do I need to buy a safari hat?","Any wide-brim hat from home works. A straw garden hat or a floppy sun hat reads as safari instantly with the khaki outfit."]]},"safari-zoo-crew":{"m":["Solid-color clothes in animal colors, 1 set per person (own)","Plastic headbands, 1 per person (buy: dollar store multi-pack)","Felt sheets in brown, black, pink, tan, 1 pack (buy: craft store; construction paper works too)","Face paint in brown and black, 1 tube each (buy: costume aisle or craft store)","Scissors and tape, 1 set (own)"],"s":["Assign roles BEFORE building. One guide per three animals keeps the ratio fun. Each person picks one animal and pulls matching solid-color clothes from the closet.","Safety: cut the felt slowly and keep fingers clear of the scissors.","Make each animal's ears from felt: cut two rounded ears and tape them to a plastic headband.","Safety: use non-toxic kids face paint, and keep it away from the eyes.","Paint faces: use the face paint to add each animal's nose, whiskers, or spots.","Wear the colored outfit and put on the ear headband. Add one felt detail, like a felt tail taped to the back, to complete each animal.","Optional pro finish: the guide 'discovers' each animal with the binoculars throughout the night, announcing the species dramatically. The discovery bit is the group performance."],"time":"25 min + drying","cost":"$2-4","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How many animals per guide?","Two to four. One guide herding six animals is chaos; one guide with two animals is a duo. Three animals is the sweet spot."],["What animals are easiest?","Lion (ears plus painted nose), zebra (striped face paint), giraffe (ears plus spot paint). Pick animals with one iconic feature each."]]},"salt-pepper":{"m":["White shirt, pants, and hat for Salt, 1 set (own)","Black shirt, pants, and hat for Pepper, 1 set (own)","Cardboard for 2 shaker tops (make: from home)","Gray paint or gray marker, 1 (buy: craft store)","Black marker for the S and P, 1 (own)","Tape or glue, 1 (own)"],"s":["Salt dresses all in white, Pepper all in black.","Cut two shaker tops from cardboard: a short wide cylinder or dome each, big enough to sit on a hat.","Paint them gray and dot holes on top like a real shaker. Let dry.","Tape each top to a hat so it rides on your head.","Letter the caps BIG. Four-inch letters minimum, because the letter is the costume. Write a big S on Salt's shaker and a big P on Pepper's with the black marker.","Optional pro finish: carry actual salt and pepper shakers and offer to 'season' people's costumes. The seasoning bit is the party trick, use it liberally."],"time":"15 min + drying","cost":"$1-2","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you make the shaker tops?","Cut a short wide cylinder or dome from cardboard that fits over a hat, tape it shut, paint it gray, and dot holes on top like a real shaker."],["Who is salt and who is pepper?","Taller person is pepper (the bigger shaker energy), or whoever wants to be. There is no wrong answer."]]},"snow-sisters":{"m":["Icy-blue dress or blue dress plus silver glitter glue, 1 set (buy glitter glue: craft store)","Pink or lavender dress, 1 (own)","White shirt, white pants, 3 large black felt circles (buy felt: craft store)","Brown clothes, 2 brown pipe cleaners, 1 red pom-pom (buy: craft store)","Silver headband, 1 (buy: dollar store)","Tape and scissors, 1 set (own)"],"s":["Assign roles, then buy the silver glitter glue, black felt circles, brown pipe cleaners, red pom-pom, and silver headband.","Pull the dresses and the white and brown clothes from closets. The snow princess just wears her dress, no crafting needed.","Test the glitter pattern on paper first. Glued glitter cannot be repositioned.","Spread the silver glitter glue in thin lines along the neckline and sleeves, and let it dry FLAT for one hour. Glue dried on a hanger drips.","Safety: cut slowly and keep fingers clear of the scissors.","Snowman: tape the 3 black felt circles down the front of the white shirt as coal buttons.","Reindeer: twist the 2 brown pipe cleaners into antler shapes and tape them to the silver headband. Tape the red pom-pom over the nose as a glowing nose.","Wear each outfit with its accessories. The ice queen adds the silver headband as a tiara.","Optional pro finish: the ice queen wears the silver headband as a tiara in every photo. The tiara is what separates the ice queen from a girl in a blue dress."],"time":"30 min + drying","cost":"$12-17","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How do you keep the glitter glue from cracking?","Thin lines, dried flat, fully cured. Thick blobs crack when the fabric moves. One thin coat beats two thick ones."],["What if the felt circles peel off the snowman?","Tape them from inside the shirt, not outside. Inside tape holds through a whole night of hugs; outside tape peels by hour two."]]},"soccer-squad":{"m":["Matching jerseys or same-color t-shirts, 1 per player (own: from closet, or buy a multi-pack at a sports store)","Black shirt and black shorts for the referee, 1 set (own: from closet)","Soccer ball, 1 any size (buy: sports store, or borrow from home)","Red cardstock rectangle, 3x4 inches, 1 (own: cut from a folder or colored paper)","Black marker, 1 (own: from home)","White athletic tape, 1 roll (buy: sports store or pharmacy)","Scissors, 1 pair"],"s":["Assign roles: most of the family are players, one person is the referee.","Players: wear matching jerseys or same-color shirts. Wrap a strip of white athletic tape around one upper arm as a captain's armband. Referee: wear all black.","Safety: cut the cardstock slowly and keep fingers clear of the scissors.","Cut the red cardstock rectangle a little larger than 3x4 inches first, then trim to size after holding it up to check it reads at arm's length.","Make the red card: cut the rectangle from the folder or colored paper. Draw a thick black border around it with the black marker so it reads as a card at a glance.","Players carry or dribble the soccer ball. The referee practices holding the red card high in the air.","Optional pro finish: give the referee a coin for the coin toss and a small notebook as the official match log."],"time":"25 min","cost":"$0-1","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["What if we do not own matching jerseys?","Same-color t-shirts from the closet work fine. A multi-pack of plain tees from a sports store is the cheap fix for a big squad."],["How does the captain's armband stay on?","Wrap one strip of white athletic tape around one upper arm over the sleeve and press the ends together. It holds for the night and peels off after."]]},"space-crewmate":{"m":["Plain sweatsuit in one solid color, red recommended, 1 set (own: from closet)","Cardboard, 1 sheet about 12x16 inches (own: from a box flap)","Aluminum foil, about 2 feet (own: from the kitchen)","Backpack straps, 2, or 2 long shoelaces (own: from home)","Markers, 3 to 4 colors (own: from home)","Tape, 1 roll (own: from home)","Scissors, 1 pair"],"s":["Dress in the solid-color sweatsuit.","If you have more than one person, give each a different color.","Wrap the cardboard in aluminum foil for the backpack. Draw vents, dials, and one big red button with the markers. Tape the two backpack straps to the back of the cardboard.","Wear the foil backpack with the straps over your shoulders. Tape the bottom corners snug to the sweatsuit so it does not swing.","Finishing touch: hold one finger to your lips and say sus for the photo.","Optional pro finish: draw a crewmate ID badge on an index card (name, color, and CREW) and tape it to the chest."],"time":"20 min","cost":"$0","effort":"Easy","sizing":"Built for teens and adults. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you keep the foil backpack from swinging?","Tape the bottom corners of the cardboard snug to the sweatsuit after the straps are on. Snug at the bottom stops the swing."],["What if more than one person wants to be the same color?","Give each person a different color sweatsuit. The joke lands harder when the group has red, blue, yellow, and one suspicious black."]]},"spider":{"m":["Black sweatshirt and black sweatpants, 1 set (own: from closet)","Black socks, 8 (4 pairs, own: from the sock drawer)","Newspaper or tissue paper, 3 to 4 sheets, for stuffing (own: from home)","Thin black rope or black yarn, 4 feet (buy: craft store)","Black fabric glue, 1 bottle, or a needle and black thread (buy: craft store)","Large googly eyes, 2 (buy: craft store; drawn paper circles work too)","White face paint, 1 tube (buy: craft store or costume aisle)"],"s":["Stuff each of the 8 socks about half full with crumpled newspaper or tissue. Leave the top half empty so each leg can bend.","Pin the stuffed socks in place on the sweatshirt first and check the spacing in a mirror before committing.","Then use the black fabric glue or a few stitches to attach 4 stuffed socks down each side of the sweatshirt, spaced so they stick out like legs, since glued legs cannot be moved.","Poke the black yarn through the middle of each stuffed sock and tie it for a knee bend.","Glue one googly eye on each shoulder of the sweatshirt. Dress in the black sweatshirt and black sweatpants, then put on the leg-covered sweatshirt.","Safety: use non-toxic face paint, and keep the googly eyes on the shoulders, not near the face.","Dot the white face paint around the eyes as spider markings.","Optional pro finish: run one long strand of black yarn across the back of the sweatshirt like a web anchor line, and add small white face-paint dots down the outside of each leg."],"time":"45 min + drying","cost":"$21-24","effort":"Medium","sizing":"Built for kids ages 3 to 10. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you keep the sock legs from drooping?","Stuff each sock only half full and leave the top half empty so the leg can bend. Poke the black yarn through the middle of each sock and tie it for a knee bend, which holds the shape up."],["Can the sweatshirt be washed after?","Spot clean only. The glued-on legs will not survive a wash, so use a sweatshirt you are fine retiring to the costume bin."]]},"sun-moon":{"m":["Yellow shirt and pants for the Sun, 1 set (own: from closet)","Navy or black shirt and pants for the Moon, 1 set (own: from closet)","Yellow cardstock, 2 sheets (buy: craft store; construction paper works too)","Silver star stickers, 1 sheet (buy: craft store; cut paper stars work too)","White and yellow paper, 1 sheet each, for the crescent (own: from home)","Tape, 1 roll, and scissors, 1 pair (own: from home)"],"s":["One person dresses head to toe in yellow, the other in navy or black.","Buy the yellow cardstock and the silver star stickers.","Safety: cut the cardstock slowly and keep fingers clear of the scissors.","Cut one ray first and tape it to the neckline to test the length before cutting the other nine, since cardstock cannot be lengthened.","Make the sun rays: cut 10 long triangles from the yellow cardstock, then tape them around the neckline and sleeves of the yellow shirt so they point outward.","Cut a large crescent from the white paper and tape it to the chest of the navy shirt. Scatter the silver star stickers across the shirt and arms.","Finishing touch: the Sun spreads arms wide to show the rays while the Moon holds one hand near the crescent.","Optional pro finish: glue the rays in pairs back to back so they are stiff and yellow on both sides, and edge the crescent with silver marker."],"time":"40 min + drying","cost":"$5-6","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you keep the sun rays from flopping over?","Tape each ray in pairs back to back so the cardstock is double thick, and tape a full inch of the ray base flat to the shirt. Short wide triangles flop less than long skinny ones."],["Will the tape damage the shirts?","Masking tape or painter's tape peels off clean. Packing tape holds better but can pull at fabric, so stick with the gentler tapes on clothes you want to keep."]]},"superhero-family":{"m":["Matching red sweatsuits, 1 per person (own: from closet, or buy a set at a discount store)","Black felt, 1 pack (buy: craft store; construction paper works too)","Yellow felt, 1 sheet (buy: craft store)","Plain headbands, 1 per person (buy: dollar store multi-pack)","Safety pins, 6 to 8, or tape, 1 roll (own: from home)","Scissors, 1 pair (own: from home)"],"s":["Have everyone dress in the red sweatsuits.","Safety: cut the eye holes wide enough so everyone can see clearly.","Trace the eye holes by holding the felt strip up to each face and marking the pupil spots.","Cut the eye holes SMALLER than the marks first and widen as needed, since cut felt cannot be uncut.","Make the eye masks: cut a mask strip from the black felt for each person with two eye holes. Attach it to the headband with the safety pins or tape.","Make the logos: cut one big first-initial letter per person from the yellow felt. Use the safety pins or tape to attach it to the chest of each sweatsuit.","Everyone wears the mask headband with the letter on the chest. Each person strikes their own hero pose for the group photo.","Optional pro finish: cut a small yellow felt lightning bolt and pin one to each sleeve, so the emblem repeats beyond the chest."],"time":"30 min","cost":"$0-2","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How do the masks stay on kids?","Attach the felt mask to a headband, not to the skin. The headband does the holding, so the mask never slips into the eyes."],["Are safety pins safe on kids' costumes?","Pin from the outside of the fabric so pin backs face the clothes, never the skin. For toddlers, use tape instead of pins everywhere."]]},"sushi-roll":{"m":["White bedsheet or large white t-shirt to wear, 1 (own: from closet)","Dark green felt, 1 large sheet (buy: craft store; construction paper works too)","Pink or orange felt, 1 large sheet (buy: craft store)","White pom-poms, 4 large, plus 1 green pom-pom (buy: craft store; cotton balls work too)","Toy chopsticks, 1 pair, or 2 wooden sticks (buy: toy store or craft store; pencils work too)","Fabric glue, 1 bottle (buy: craft store)","Scissors, 1 pair"],"s":["Dress in the white bedsheet or large white t-shirt.","Safety: cut the felt slowly and keep fingers clear of the scissors.","Wrap the felt band around the waist first and mark where it overlaps before cutting, since the band must meet around the body.","Make the wrap: cut the dark green felt sheet into a wide band that goes around your waist. Glue or pin it there as the seaweed wrap.","Make the toppings: cut the pink felt sheet into long strips and glue them across the white shirt as salmon.","Glue the white pom-poms near the shoulder as rice balls and the green pom-pom as wasabi.","Finishing touch: carry the toy chopsticks in one hand like you are about to pick up a bite.","Optional pro finish: tie a thin red ribbon belt over the seaweed wrap like the band on a real sushi roll, and glue sesame dots (tiny white paper circles) on the salmon strips."],"time":"40 min + drying","cost":"$10-12","effort":"Easy","sizing":"Built for teens and adults. Kids under 8 use a twin flat sheet, tweens and adults use a full flat, and trim the hem so it clears the ground by a few inches. Toddlers trip on hems an adult would clear.","faqs":[["How do you wear a bedsheet without it falling off?","Wear a white t-shirt under it and safety-pin the sheet at both shoulders like a toga. Belt it with the seaweed wrap so it cannot unwrap."],["Will the waistband be comfortable all night?","Keep the band snug but loose enough to sit down in. Pinning instead of gluing lets you adjust it, and felt has a little give."]]},"tennis-duo":{"m":["White t-shirts and white shorts or skirts, 1 set each (own: from closet)","White sweatbands, 2, or strips of white fabric (buy: sports store)","Toy tennis rackets, 2 (buy: toy store; cardboard rackets work too)","Tennis balls, 1 tube of 3 (buy: sports store)","White socks and sneakers, 1 pair each (own: from closet)","Scissors, 1 pair"],"s":["Pull the white outfits and sneakers from the closet.","Dress head to toe in white and tie the sweatband across the forehead.","Safety: cut the fabric slowly and keep fingers clear of the scissors.","Measure the strip around the head with a finger's width of slack before cutting, then cut the 2-inch strip of white fabric.","To make a sweatband: tie it around the head with a knot at the back, snug enough to stay but loose enough to be comfortable.","Finishing touch: carry the toy tennis rackets and tuck the tube of balls under one arm for the courtside pose.","Optional pro finish: add a white wristband on the racket arm and tuck one spare ball into the waistband for the between-points look."],"time":"20 min","cost":"$7-9","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you make a cardboard tennis racket?","Cut an oval with a handle from cardboard, cut out the middle, and weave string or yarn across the opening for the strings. Tape the handle for a grip."],["How do you keep the fabric sweatband from slipping?","Tie it with a knot at the back rather than relying on stretch. A knot you can retie stays put through the whole night."]]},"tin-hero":{"m":["Red sweatsuit, 1 (own)","Gold duct tape, 1 roll (buy: dollar store or hardware store)","Battery tea light, 1 (buy: dollar store)","Cardboard, 1 piece (own)","Tape, 1 roll (own)","Safety pin, 1 (own)"],"s":["Dress in the red sweatsuit.","Stripe the sweatsuit with the gold duct tape: strips across the chest, arms, and legs.","Draw the reactor circle on the cardboard BEFORE cutting, and measure it against the chest first. Cover it in gold tape, then tape the tea light behind its center.","Safety: pin from inside the sweatsuit, so the pin back faces the fabric and never the skin.","Pin the glowing circle to the chest of the sweatsuit.","Walk like the suit does the talking.","Optional pro finish: pin the reactor slightly off-center, like battle damage. Perfectly centered reads as costume; off-center reads as character."],"time":"25 min","cost":"$7-9","effort":"Easy","sizing":"One design, two builds: the kid build fits ages 3 to 10, and the teen and adult build fits everyone older. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How does the chest reactor glow?","A battery tea light taped behind a cardboard circle covered in gold tape. The tape diffuses the light so it glows instead of showing a bulb."],["Will the duct tape peel off the sweatsuit?","Press each strip down hard and smooth out air bubbles. Fresh duct tape holds all night; old tape from the junk drawer peels by dinner."]]},"tiny-firefighter":{"m":["Red sweatsuit, 1 (own: from closet)","Toy firefighter helmet, 1 (buy: toy store)","Toy fire hose or coiled garden hose, 1 (buy: toy store, or borrow a real coil of rope from home)","Yellow reflective tape, 1 roll (buy: hardware store)","Black marker, 1 (own: from home)"],"s":["Make the turnout stripes: wrap two horizontal bands of the yellow reflective tape around each sleeve and each leg. Press the tape firmly so it sticks.","Safety: keep the toy firefighter helmet snug so it does not slide over the eyes.","Put the toy firefighter helmet on and carry the toy fire hose coiled over one shoulder.","Finishing touch: the kid holds the hose nozzle out front for the hero photo.","Optional pro finish: wrap one band of reflective tape around the toy helmet too, so the whole uniform matches."],"time":"25 min","cost":"$9-11","effort":"Easy","sizing":"Built for ages 1 to 8. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Will the reflective tape come off the sweatsuit after?","It peels off, but it can leave sticky residue on some fabrics. Test a hidden spot first, and use a thrifted sweatsuit if you want zero risk."],["What if the toy helmet is too big and slides over the eyes?","Stuff folded paper towel inside the helmet until it sits snug. Keep it snug enough that it never slides over the eyes."]]},"tiny-snail":{"m":["Neutral beige or tan clothes, 1 set (own: from closet)","Large cardboard sheet or 1 flattened box (own: from home)","Brown and tan markers or crayons, 1 set (own: from home)","Backpack straps, 2, or 2 long ribbons (own: from home)","Headband, 1 (buy: dollar store)","Black pom-poms, 2 (buy: craft store; cotton balls work too)","Tape, 1 roll (own: from home)","Scissors, 1 pair"],"s":["Dress the kid in the beige or tan clothes.","Buy the headband and black pom-poms.","Safety: cut the cardboard slowly and keep fingers clear of the scissors.","Draw the oval on the cardboard first and hold it against the kid's back to check the size before cutting, since a too-small shell cannot be fixed.","Make the shell: cut the cardboard into a large oval. Draw a spiral from the center outward with the brown marker. Tape the two backpack straps to the back so it wears like a backpack.","Make the eyestalks: tape two short cardboard strips to the headband so they point up. Tape a black pom-pom to the top of each strip.","Wear the shell backpack and the headband with the pom-pom eyestalks. Keep the shell light and the straps snug so it rides comfortably.","Optional pro finish: edge the shell oval with a tan marker border and add a second smaller spiral inside the first for a realistic shell pattern."],"time":"30 min","cost":"$8-9","effort":"Easy","sizing":"Built for ages 1 to 8. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How do you keep the shell light enough for a small kid?","Use single-ply cardboard from a cereal-style box rather than a heavy shipping box, and keep the oval modest. Tape, don't glue, so it stays light."],["How do you keep the eyestalks standing up?","Use short cardboard strips, about 4 inches, and small pom-poms. Tall strips with big pom-poms flop over every time."]]},"tooth-fairy":{"m":["Tooth: all-white outfit, 1 set (own: from closet)","Tooth fairy: white dress or white shirt with a white skirt, 1 (own: from closet)","White cardstock, 1 large sheet (buy: craft store)","White felt wings, 1 pair, or 1 wire coat hanger with white pantyhose (buy: craft store, or make: from home)","Small envelope and play money or a coin, 1 (own: from home)","Glitter glue, 1 tube (buy: craft store)","Stick and aluminum foil for the wand, 1 (own: from home)","Tape, 1 roll, and scissors, 1 pair (own: from home)"],"s":["Pull the white clothes from the closet.","Draw the tooth outline lightly in pencil first and hold it against the chest to check the size before cutting.","Make the tooth: cut a large tooth shape with two roots from the white cardstock. Edge it with the glitter glue and let it dry. Tape it to the chest of the white outfit.","Safety: tape down any sharp wire ends from the wire coat hanger, and keep fingers clear of the scissors.","Make the wings: stretch the white pantyhose over a reshaped wire coat hanger to form two wing loops.","Tape the hanger ends to a piece of cardboard worn at the back. Tuck the envelope with play money into a pocket or waistband.","Tooth fairy: wear the white dress and strap on the wings. Carry the wand made from the stick with an aluminum foil star taped on top.","Optional pro finish: tuck a tiny card into the envelope that says the tooth exchange rate (one tooth equals one wish) for the full fairy bureaucracy joke."],"time":"45 min + drying","cost":"$3-4","effort":"Medium","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do two people split the tooth and the fairy?","One person wears the all-white outfit with the big tooth on the chest, the other wears the white dress with the wings and carries the wand and envelope. Both read clearly side by side."],["Is the wire hanger safe for wings?","Yes if you tape down every sharp wire end and keep the taped ends at the back on the cardboard. For small kids, use felt wings with no wire at all."]]},"under-the-sea":{"m":["Jellyfish: 1 clear umbrella (buy: dollar store)","Jellyfish: pastel ribbons, 1 spool (buy: craft store; crepe paper strips work too)","Crab: red shirt and pants, 1 set, plus red mittens or red socks, 1 pair, for hands (own: from closet)","Fish: silver or blue clothes, 1 set, and 1 large cardboard fish cutout (own: from home)","Seaweed: green clothes, 1 set, and long green streamers, 1 pack (buy: party store)","Waves: blue sheet or blue blanket, 1 (own: from home)","Tape, 1 roll, and scissors, 1 pair (own: from home)"],"s":["Assign one sea creature per person. Buy the clear umbrella, pastel ribbons, and green streamers. Pull the colored clothes from closets.","Safety: cut the ribbons slowly and keep fingers clear of the scissors. Hold the clear umbrella high and keep the tentacle ribbons clear of faces.","Cut one ribbon first and tape it to the umbrella edge to test the drape before cutting the rest.","Jellyfish: cut the pastel ribbons into 3-foot lengths. Tape them to the edge of the clear umbrella so they dangle like tentacles. Hold the clear umbrella overhead.","Crab: dress in red and slide the red mittens or red socks onto the hands.","Hold both hands up with fingers pinched like claws. Fish: tape the cardboard fish cutout to the chest over the silver clothes.","Seaweed: tape the green streamers to the shoulders and arms so they wave when the arms move. Everyone together can hold the blue sheet behind the group as a wave backdrop for the photo.","Optional pro finish: tape small silver star stickers to the ribbons as bubbles, and give the fish a paper gill slit detail with marker."],"time":"40 min","cost":"$2-4","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Is the umbrella safe in a crowd?","Hold the clear umbrella high and keep the tentacle ribbons clear of faces. In tight crowds, carry it closed until there is room to open it."],["What if it actually rains?","The jellyfish wins: the umbrella is real and functional. The ribbons may get soggy, so use crepe paper only if the forecast is dry."]]},"vampire":{"m":["Black cape or black bedsheet, 1 (buy cape: costume aisle; or make: from a black sheet from home)","Black shirt and pants, 1 set (own: from closet)","Plastic vampire fangs, 1 pair (buy: costume aisle or dollar store)","Hair gel or pomade, 1 (own: from home)","Red lipstick or red face paint, 1 (buy: pharmacy or costume aisle)","White face powder or pale face paint, 1 (buy: costume aisle)"],"s":["Dress in the black shirt and pants.","Make the hair: work the hair gel through the hair with your fingers. Press it straight back until it sits flat and slick.","Safety: use non-toxic costume makeup, and skip the vampire fangs for small kids who might choke on them.","Make the face: dust the pale face paint over the face and neck. Dab a thin line of red lipstick at each corner of the mouth like drips of blood.","Wear the black cape over the shoulders and pop the vampire fangs in last before photos.","Optional pro finish: paint the nails black and pop the cape collar up high, since the collar silhouette is what reads as vampire from across the room."],"time":"25 min + drying","cost":"$16-20","effort":"Easy","sizing":"Built for teens and adults. Kids under 8 use a twin flat sheet, tweens and adults use a full flat, and trim the hem so it clears the ground by a few inches. Toddlers trip on hems an adult would clear.","faqs":[["Are the plastic fangs safe for small kids?","Skip the fangs for small kids who might choke on them. Draw two white fang triangles on the lower lip with face paint instead."],["How do you get the pale face without buying special makeup?","White face powder from the costume aisle is cheapest. Whatever you use, patch-test it first on sensitive skin and wash it off the same night."]]},"walking-taco":{"m":["Tan vest or tan t-shirt, 1 (own: from closet)","Brown, red, green, and yellow felt sheets, 1 pack (buy: craft store; construction paper works too)","Fabric glue, 1 bottle (buy: craft store)","Headband, 1 (buy: dollar store)","Scissors, 1 pair (own: from home)"],"s":["Dress the kid in the tan vest or tan t-shirt.","Safety: cut the felt slowly and keep fingers clear of the scissors.","Pin or lay the brown felt strips on the vest first and check the fold placement in a mirror before gluing, since glued felt cannot be repositioned.","Glue two curved strips of brown felt down the front of the tan vest to form the shell fold.","Make the toppings: cut wavy strips of green felt for lettuce and red circles for tomatoes. Cut yellow rectangles for cheese and brown blobs for beef.","Glue them in a row across the chest and shoulders so they spill out like a taco filling.","Make the headband garnish: glue one green felt strip and one red felt circle to the headband. Wear it with the vest as a lettuce and tomato topper.","Optional pro finish: glue a fringe of thin yellow felt strips along the bottom edge of the vest so cheese spills out all around."],"time":"45 min + drying","cost":"$6-7","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["Can you wash the vest after Halloween?","No. The glued felt does not survive the washing machine. Spot clean only, and use a vest you are fine keeping as a costume."],["Felt or construction paper for the toppings?","Felt survives the whole night; construction paper tears and wilts with any moisture. Felt is worth it for a kid who will be running around."]]},"web-hero-duo":{"m":["Hero: red and blue sweatsuit, or red shirt with blue pants, 1 set (own: from closet)","Partner: black jacket and black pants, 1 set (own: from closet)","Black face paint or black eye mask, 1 (buy: costume aisle)","White face paint or white stickers, 1 (buy: craft store)","Red web gloves or red socks for hands, 1 pair (own: from closet)","Tape, 1 roll (own: from home)"],"s":["Pull the red and blue outfit and the black jacket and black pants from closets.","Safety: use non-toxic face paint, and keep paint out of the eyes.","Test the white web pattern on a paper towel first to check the paint flow, since painted lines cannot be undone on fabric.","Hero: paint a black eye mask with the black face paint across the eyes.","Add white web lines over the red shirt using the white face paint.","Or tear thin strips of tape in a web pattern over the shirt. Pull the red socks onto the hands as web gloves.","Partner: wear the black jacket and black pants and slick the hair back. Strike the brooding pose. No crafting needed beyond the outfit.","Finishing touch: the hero throws one arm out in a web-shooting pose while the partner crosses their arms behind them.","Optional pro finish: run the white tape web pattern across the back of the shirt too, so the costume reads from behind in photos."],"time":"25 min + drying","cost":"$3-4","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Will the white paint ruin the red shirt?","Yes, face paint stains fabric. If you want the shirt wearable after, use white stickers or thin tape strips in a web pattern instead of paint."],["What is safer around the eyes, paint or a mask?","A black eye mask avoids paint near the eyes entirely. If you paint, keep all paint above the cheekbones and below the brow, never on the lids."]]},"web-slinger-crew":{"m":["Hoodies in red, black, and pink, 1 per person (own: from closet)","Black fabric paint or black face paint, 1 tube (buy: craft store)","White stickers or white electrical tape, 1 roll (buy: hardware store)","Sunglasses or swim goggles, 1 per person (buy: dollar store multi-pack)","Tape, 1 roll (own: from home)"],"s":["Assign each person a hoodie color.","Buy the black fabric paint or black face paint, white stickers or white electrical tape, and the multi-pack of sunglasses.","Draw the eye-lens shape on paper first and hold it against the sunglasses to check the size before painting, since paint on lenses cannot be removed cleanly.","Stick white stickers or white electrical tape in a web pattern across the front of each pair of sunglasses.","Draw two black eye lenses on top with the black fabric paint or black face paint. Let them dry flat for 30 minutes.","Make the chest webs: stick short white tape strips in a web grid across the chest of each hoodie.","Wear the hoodie with the hood up and put on the web-patterned sunglasses. Each person picks their own web-shooting pose for the group shot.","Optional pro finish: run short white tape strips down the outside of each sleeve as web lines, so the arms match the chest."],"time":"30 min + drying","cost":"$1-3","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Sunglasses or swim goggles for the eye lenses?","Swim goggles stay on better, especially for kids running around. Sunglasses work for photos but slide off during the night."],["Will the electrical tape come off the hoodie after?","White electrical tape peels off clean from most hoodie fabrics. Test a hidden spot first on anything delicate."]]},"web-slinger-kid":{"m":["Red sweatsuit or red shirt and pants, 1 set (own, or buy: clothing store)","Blue craft felt for sleeve and boot accents, 1 sheet 9x12 inches (buy: craft store, blue paper works too)","Black electrical tape for web lines, 1 roll (buy: hardware store)","White paper or cardstock for eye lenses, 1 sheet (make: cut from paper)","Plain headband, 1 (buy: dollar store)","Scissors, 1 pair"],"s":["Lay the red sweatsuit flat and plan the web lines first: one center line down the chest, then fan lines out to each side.","Stick short strips of black electrical tape across the chest in a web grid, pressing each strip flat so it survives the night.","Cut two large white eye lenses from the white paper with the scissors. Hold them against the face to check the size before attaching.","Safety: tape the paper eyes to the plain headband, never tape paper to skin around the eyes. Skip the eyes for very young kids and draw web lines with face paint instead.","Cut blue felt rectangles and tape them around the sleeves and pant cuffs as hero accents.","Pull on the red sweatsuit, put on the eye headband, and strike the web-shooter pose: one hand up, fingers spread.","Optional pro finish: run short black tape strips down the outside of each sleeve as web lines, so the arms match the chest."],"time":"25 min + drying","cost":"$5-8","effort":"Easy","sizing":"Built for kids ages 5 to 9. Start from a sweatsuit the kid already owns in their size, and keep every tape strip on fabric, never on skin.","faqs":[["Will the tape ruin the sweatsuit?","Black electrical tape peels off most sweatshirt fabric cleanly. Test a hidden spot first, and pull it off slowly after the night."],["My kid will not wear a headband. What then?","Skip the paper eyes and draw simple black web lines on the cheeks with non-toxic face paint. The red suit plus web lines reads as the hero on its own."]]},"zombie-coworker":{"m":["Old button-down shirt you can cut up, 1 (own: from closet)","Old tie, 1 (own: from closet)","Pale face paint or white face powder, 1 (buy: costume aisle)","Dark eye makeup or black eyeshadow, 1 (buy: pharmacy)","Coffee mug, 1 (own: from home)","Scissors, 1 pair (own: from home)"],"s":["Pull the old button-down shirt, old tie, and coffee mug from home.","Safety: cut away from your fingers, and keep the scissors away from small kids. Use non-toxic costume makeup.","Decide where every slit goes and mark the spots with chalk before cutting, since cut fabric cannot be put back.","Make the torn shirt: cut jagged slits along the hem of the old button-down shirt and one sleeve. Tie the old tie loosely and crookedly around the neck.","Make the face: cover the face with the pale face paint. Ring the eyes with the dark eye makeup. Smudge a little down one cheek like a long night at the office.","Wear the torn shirt with the loosened tie and carry the coffee mug everywhere, mumbling about the quarterly review.","Optional pro finish: add a lanyard with a blank ID badge worn backwards, the universal sign of someone who gave up at 3pm."],"time":"20 min + drying","cost":"$8-10","effort":"Easy","sizing":"Built for teens and adults. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["What if I do not want to ruin a real work shirt?","Buy a thrift-store button-down for a few dollars and destroy that instead. It looks more authentically worn-out anyway."],["How do you get the zombie makeup off?","Wash it off the same night with soap and warm water. Pale face paint stains pillowcases, so wash before bed, not in the morning."]]},"the-olympians":{"m":["White bedsheets or large white fabric, 1 per person (own: raid the linen closet)","Gold rope or gold cord, 2 yards per person (buy: craft store)","Gold paper or gold craft leaves for laurel crowns, 1 pack (buy: craft store; gold paper works too)","Gold face paint or gold eyeliner, 1 (buy: drugstore)","Cardboard for the props, 3 pieces: lightning bolt, trident, owl (own: from boxes)","Gold markers or gold paint pen, 1 (buy: craft store)","Safety pins, 6 to 8; scissors, 1 pair; tape, 1 roll (own: household)"],"s":["Make the togas: wrap one sheet around each person over a plain t-shirt and shorts, pinning at the shoulder with a safety pin. Belt it with the gold rope.","Safety: pin from the outside of the fabric so pin backs face the clothes, never the skin. Keep the toga above the ankles so nobody trips.","Size the paper strip around each head and overlap it by an inch before taping, since tape cannot be repositioned cleanly.","Make the laurel crowns: cut leaf shapes from the gold paper and tape them along a paper strip sized to each head.","Make the god props: cut a lightning bolt, a trident, and an owl from the cardboard. Color them gold with the markers.","Paint one gold detail on each face: a lightning streak, an owl feather, or a wave. Each god picks a power pose for the group photo.","Optional pro finish: wrap gold cord around each wrist as a cuff and tie gold cord laces up the calves over the shoes for the sandal look."],"time":"45 min + drying","cost":"$2-4","effort":"Medium","sizing":"Each partner builds their half in their own size. Kids under 8 use a twin flat sheet, tweens and adults use a full flat, and trim the hem so it clears the ground by a few inches. Toddlers trip on hems an adult would clear.","faqs":[["How do you keep the toga from falling off?","Wear a plain t-shirt and shorts under it, pin the sheet at the shoulder, and belt it with the gold rope at the natural waist. The belt does most of the holding."],["Is a floor-length sheet a tripping hazard?","Keep the toga hem above the ankles and pin the extra fabric up. Test walking and stairs before leaving the house."]]},"spaghetti-meatball":{"m":["White t-shirt or sweatshirt, 1 (own: from closet)","Yellow or cream yarn, 1 skein (buy: craft store)","Brown pom-poms, 2 inch, 3 to 4 (buy: craft store)","Fabric glue or hot glue gun, 1 (buy: craft store)","Scissors, 1 pair"],"s":["Lay the white shirt flat.","Lay out the yarn strands on the shirt first WITHOUT glue to check the wavy rows cover the shirt the way you want.","Then cut the yarn into 12-inch strands and glue them across the shirt in wavy rows to look like spaghetti, since glued strands cannot be repositioned.","Glue 3-4 brown pom-poms on top as meatballs.","Let dry completely before wearing.","Optional pro finish: glue a few small white pom-poms among the yarn as grated parmesan, and add a red felt meatball-sauce splatter on one sleeve."],"time":"40 min + drying","cost":"$11","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Can you wash the shirt after?","No. The glued yarn does not survive the washing machine. Treat it as a single-use costume shirt, so use a thrifted one you do not mind retiring."],["How long does the glue need to dry?","Let it dry completely before wearing, at least 1 hour for fabric glue. Lay it flat while drying so the yarn rows do not slide."]]},"cupcake":{"m":["Brown t-shirt or tunic for the wrapper, 1 (make: from closet)","White pillowcase for the frosting, 1 (make: from home)","Red pom-pom or ball for the cherry, 1 about 2 inches (buy: craft store)","Fabric glue, 1 tube (buy: craft store)"],"s":["Put on the brown shirt. This is the cupcake wrapper.","Drape the white pillowcase over your head and shoulders like frosting.","Mark eye positions while wearing it, take it off, and trim eye holes SMALL first, then widen. Trim the bottom edge into a wavy frosting line.","Glue the red pom-pom on top as the cherry.","Fluff the pillowcase edges to look like frosting swirls.","Optional pro finish: dot the pillowcase with fabric markers in sprinkle colors before wearing. Sprinkles turn 'person in a pillowcase' into cupcake."],"time":"15 min + drying","cost":"$7","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you keep the pillowcase frosting on your head?","It drapes, no attachment needed if the pillowcase is adult-size on a kid. For adults, pin it to a headband at the forehead so it does not slide."],["What is the wrapper part?","The brown shirt is the cupcake liner. Vertical marker stripes on the brown shirt sell the wrapper ridges."]]},"banana":{"m":["Yellow sweatshirt and sweatpants, 1 set (make: from closet, or buy: clothing store)","Green felt, 1 sheet 9x12 inches (buy: craft store)","Headband, 1 (buy: dollar store)","Fabric glue, 1 tube (buy: craft store)"],"s":["Put on the yellow sweatshirt and sweatpants.","Cut a stem shape from green felt, about 4 inches tall.","Hold the stem against the headband and check the position in a mirror BEFORE gluing, once fabric glue sets, the stem cannot be moved. Glue the stem to the headband and let it dry flat.","Wear the headband. You are a banana.","Optional pro finish: glue a small brown felt rectangle at the bottom front of the sweatshirt as the banana tip. Top and bottom details make it read as banana, not yellow sweats."],"time":"10 min + drying","cost":"$6-8","effort":"Easy","sizing":"One design, two builds: the kid build fits ages 3 to 10, and the teen and adult build fits everyone older. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How big should the banana stem be?","About 4 inches tall and 2 inches wide. Bigger looks cartoonish in a good way; smaller disappears."],["Can I make this with zero shopping?","Yes if you own yellow sweats: cut the stem from a green t-shirt or paper bag painted green, and tape it to any headband or hat."]]},"hot-dog":{"m":["Red t-shirt, 1 (own)","Tan or beige foam pool noodle, 1 (buy: dollar store)","Yellow fabric paint for mustard, 1 bottle (buy: craft store)","Safety pins or fabric glue, 1 pack (buy: craft store)"],"s":["Put on the red shirt. You are the hot dog.","Cut the pool noodle in half lengthwise to make two bun halves.","Paint a thin mustard squiggle down one bun half with the yellow fabric paint. You can always add more paint, but you cannot remove it, so start thin. Let dry fully before attaching.","Attach the bun halves to your sides with safety pins or fabric glue, one on each side.","Optional pro finish: add a white paper vendor hat. The hat turns 'person in a bun' into a ballpark vendor, and vendors get offered tips."],"time":"15 min + drying","cost":"$7-8","effort":"Easy","sizing":"Built for teens and adults. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you make the bun halves stay on the shoulders?","Pin each half at the shoulder seam with two safety pins from inside the shirt. They sit like epaulettes, stable all night, no glue on skin."],["Ketchup and mustard or just mustard?","Both, in zigzag squiggles. The zigzag is the visual shorthand for condiments, straight lines read as stripes, zigzags read as sauce."]]},"donut":{"m":["1 large cardboard box, about 24x24 inches flat (make: from home)","Pink paint, 1 small bottle (buy: craft store)","Felt sprinkles, 12 to 15 small pieces, or sticker sprinkles (buy: craft store)","Ribbon or string, 4 feet (make: from home)","Scissors, 1 pair and glue, 1 bottle"],"s":["Draw the donut circle on the cardboard first and check it fits over the head: outer circle about 30 inches across, center hole about 12 inches.","Cut the center hole SMALLER than the head first, then widen. Cardboard cut away cannot be put back, and a too-big hole slides off the shoulders.","Paint it pink. Let dry.","Glue on felt sprinkles or stickers in bright colors.","Attach ribbon to the top so you can wear it like a sandwich board.","Optional pro finish: paint a thin brown ring around the center hole for the fried-dough edge. The brown edge is what separates donut from pink life preserver."],"time":"35 min + drying","cost":"$5-8","effort":"Easy","sizing":"One design, two builds: the kid build fits ages 3 to 10, and the teen and adult build fits everyone older. Have each wearer step into the box before you mark arm and leg holes, cut them a little wide, and tape every inside edge so cardboard never scratches.","faqs":[["How do you wear a big cardboard donut comfortably?","Hang it from two ribbon straps like a sandwich board at waist height, not neck height. Waist height clears doorways and lets the arms move."],["How long does the pink paint take to dry?","About 1 hour for acrylic on cardboard. Paint the night before: wearing it damp smears pink onto every hug."]]},"coffee-cup":{"m":["White trash bag or white sheet, 1 large (make: from home)","Cardboard tube or large cylinder, 1 (make: from home)","Brown paper or felt for the lid, 1 sheet (buy: craft store)","Brown marker, 1 thick (buy: dollar store)"],"s":["Cut the arm holes first, then the head hole SMALL, stretch the bag over the head to test before cutting bigger.","Cut holes in the white trash bag for head and arms with the scissors. This is the cup. A head hole cut too big slides off the shoulders.","Draw a coffee shop logo on the front with brown marker.","Make the lid: cut a brown paper circle bigger than your head, with a sip hole.","Wear the bag, then the lid hat on top.","Optional pro finish: cut a cardboard sleeve, write a coffee-shop pun on it ('Decaf? Never met her'), and tape it around the torso. The sleeve is what makes it a to-go cup instead of a white bag."],"time":"20 min","cost":"$4-6","effort":"Easy","sizing":"Built for teens and adults. Kids under 8 use a twin flat sheet, tweens and adults use a full flat, and trim the hem so it clears the ground by a few inches. Toddlers trip on hems an adult would clear.","faqs":[["How do you keep a trash-bag costume from looking like a trash bag?","The lid and the logo do all the work. A brown lid hat plus a big drawn logo reads as coffee cup; without them it reads as trash bag."],["Is a trash bag safe to wear?","Cut generous head and arm holes before putting it on, never pull it over the face, and keep it away from very small children. A white sheet is the safer alternative for toddlers."]]},"fruit-salad":{"m":["Solid-color outfits in fruit colors (red, yellow, green, orange), 1 set per person (own)","Green felt for leaf hats, 1 sheet 9x12 inches per person (buy: craft store)","Headbands, 1 per person (buy: dollar store)","Fabric glue, 1 tube (buy: craft store)"],"s":["Each person picks a fruit and wears that color head to toe. Red for strawberry, yellow for banana, green for lime, orange for orange.","Cut leaf shapes from green felt.","Glue one leaf to each headband and let it set fully before wearing. Glued leaves cannot be repositioned, so center each leaf on the band and press for 30 seconds.","Everyone wears their headband. Take a group photo as the fruit salad.","Optional pro finish: snip a center vein down each felt leaf with the scissors. The vein makes flat felt read as a real leaf in photos."],"time":"20 min + drying","cost":"$1-2","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How many fruits make a good salad?","Four to six. Three looks thin, more than six gets hard to photograph. Assign the biggest person the watermelon."],["How do you keep the leaf hats on?","Glue the leaf to the front-center of the headband and let it set fully. A leaf glued off-center flops forward all night."]]},"wizard":{"m":["Tall black pointy wizard hat, 1 (buy: costume aisle or craft store)","Long plain black robe or graduation gown, 1 (own, or buy: thrift store)","Tall straight wooden staff, about 5 feet (make: from a dowel or sturdy branch, or buy: craft store)","Gray face paint or stick-on gray beard, 1 (buy: costume aisle, optional)","Belt or rope sash, 1 (own)"],"s":["Size the hat to the head BEFORE decorating, a hat decorated then found too small is heartbreaking. Put on the robe.","Roll the paper into a tall wizard hat or use the store-bought one; confirm it sits without covering the eyes. Stick the star stickers on the robe and hat.","Safety: keep the hat brim above the eyes so vision stays clear, and carry the staff upright. Never swing it at anyone.","Draw on a gray beard with the face paint, or stick on the fake beard.","Tie the belt or rope sash around the waist over the robe.","Put on the pointy hat last, tap the staff on the ground, and strike a pose.","Optional pro finish: tape a battery tea light to the wand tip. A wand that glows when you cast is the detail kids remember for years, the gasps are worth the tape."],"time":"20 min + drying","cost":"$5-6","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How tall should the wizard hat be?","About as tall as the head. Taller looks impressive but flops without internal support, roll a cone of cardstock inside for structure."],["What goes in the spell book?","Write silly spells on the pages in marker ('Spell for extra dessert: say please three times'). People WILL open it, make it funny."]]},"toy-box-crew":{"m":["Cowboy hat, 1, and cow-print vest, 1, for the sheriff (buy: costume aisle or thrift store)","White shirt and pants, 1 set, with purple felt accents for the space ranger (own: from closet)","Cardboard wings and 1 clear plastic dome for the space ranger helmet (own: from craft supplies)","Brown boots or boot covers, 1 pair, for the sheriff (own: from closet)","Yellow shirt, 1, with a hand-drawn star badge for extra toy-box friends (own: from closet)","Toy pull-string name tags, 1 per person (own: index cards)","Marker, 1; scissors, 1 pair; glue, 1 bottle; tape, 1 roll (own: household)"],"s":["Sheriff: wear the cowboy hat, cow-print vest, and brown boots. Draw a star badge on the yellow shirt with a marker.","Lay the felt fins and buttons on the white shirt first and check the placement in a mirror before gluing, since glued felt cannot be moved.","Space ranger: cut purple felt fins and buttons and glue them to the white shirt. Tape the cardboard wings to the back and wear the clear plastic dome as a helmet.","Safety: keep the plastic dome above the shoulders with the face fully open, and carry any toy props low so nobody gets poked.","Tie a pull-string name tag to each wrist. Strike the sheriff pose and the space-ranger landing pose for the group photo.","Optional pro finish: draw a round speaker circle on the space ranger's chest and write PULL on it, so the pull-string joke lands without explanation."],"time":"35 min + drying","cost":"$2-5","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Will the clear plastic dome fog up or block vision?","Keep the dome above the shoulders with the face fully open, never sealed around the neck. It is a helmet prop, not a closed bubble."],["How do the pull-string name tags work?","Write each character name on an index card, punch a hole, and tie it to the wrist with string. It reads as the pull string and doubles as the name tag."]]},
"demon-boy-band":{"m":["Oversized black or white t-shirt per person, 1 each (make: from closet)","Baggy pants per person, 1 pair each (make: from closet)","Neon fabric paint, 1 small bottle each in 2 colors (buy: craft store)","Temporary tattoos or 1 neon eyeliner pencil (buy: drugstore)","Toy microphone per person, 1 each (buy: dollar store)","Hair gel, 1 travel-size tube (make: from the bathroom)","Sunglasses per person, 1 each, optional (make: from the drawer)"],"s":["Decide the pattern together first and sketch it on paper, then test the neon fabric paint on an inside seam so you know how it looks.","Paint matching glowing patterns on everyone: lightning marks on the sleeves, circles on the chest. Keep all paint on the clothes, off faces and away from eyes. Let the paint dry flat for 2 hours.","Apply neon eyeliner or temporary tattoos on cheeks and hands. Style hair up and forward with the gel.","Safety: keep paint off faces and away from eyes.","Wear the matching streetwear, carry a toy microphone each, line up shoulder to shoulder, and strike the synchronized album-cover pose.","Optional pro finish: give every member the same temporary tattoo on the same cheek. One matching detail is what turns matching shirts into a band."],"time":"40 min + drying","cost":"$2-3","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Will neon fabric paint glow without a black light?","No, it needs a black light to pop. Without one it still reads as bright neon color, so check what the venue has before you count on the glow."],["How do you keep the paint from cracking when they move?","Paint thin lines, not thick blobs, and let it dry the full 2 hours. Thick paint cracks the first time an arm bends."]]},
"dragon-rider-duo":{"m":["1 brown t-shirt and 1 pair dark pants for the rider (make: from closet)","Gray felt, 2 yards, or 1 old gray blanket for the dragon tunic (buy: craft store or thrift store)","1 large cardboard box for wings and tail (make: collect spares)","Black and yellow craft foam, 1 sheet each for the dragon eyes (buy: craft store)","1 faux-fur vest or brown scarf for the rider (make: from closet)","1 headband for the dragon eyes","Scissors, tape, and string, 6 feet (make: household tools)"],"s":["Draw the wing shape on paper first and hold it against the dragon person's back: wings should reach from shoulder to hip.","Cut two wing shapes and a long tail from the cardboard box with the scissors.","Cut the wings smaller than the paper test, not bigger: oversized cardboard wings hit every doorway. Tape all cut edges smooth before wearing.","Glue the black and yellow foam eyes to a headband for the dragon head. The rider wears the faux-fur vest over the brown t-shirt.","Safety: keep wing tips above waist height and tape all cardboard edges smooth so nobody gets scratched.","Rider stands in front with arms out like steering; dragon crouches behind with wings spread. Take the flying photo.","Optional pro finish: tape a row of small cardboard triangles along the dragon's shoulders as back ridges. Ridges plus wings read as dragon; wings alone read as bird."],"time":"60 min + drying","cost":"$4-6","effort":"Medium","sizing":"Each partner builds their half in their own size. Have each wearer step into the box before you mark arm and leg holes, cut them a little wide, and tape every inside edge so cardboard never scratches.","faqs":[["How do you keep cardboard wings up?","Tape them to the gray felt tunic, not the person, with wide packing-tape tabs on both sides. Taped wings stay up for hours; glued wings peel."],["What is the best pose for the photo?","Rider stands in front with arms out like steering, dragon crouches behind with wings spread. The crouch sells the size difference."]]},
"numbered-players":{"m":["Green sweatsuit per person, 1 each (buy: thrift store, or own: from closet)","White t-shirt per person, 1 each (own: from closet)","Iron-on number patches or white paper numbers, 1 per person (buy: craft store)","White sneakers, 1 pair per person (own: from closet)","Dalgona candy or a round cookie per person, 1 each (buy: bakery, optional prop)","Iron, 1 (own: household)"],"s":["Lay the numbers on each shirt and have the wearers confirm their number BEFORE heating the iron, iron-on numbers cannot be repositioned once pressed.","Iron or tape one number onto the front of each white t-shirt and the matching number on the back.","Wear the white t-shirt under the green sweatsuit jacket with the number showing, plus the white sneakers.","Hand each player a dalgona candy as the prop. Line up in number order for the photo.","Safety: if using an iron, have an adult do the pressing. Keep numbers readable and identical front and back.","Optional pro finish: draw a thin triangle border around each number with a black fabric marker. The border is what makes the number read as a player badge instead of a sticker."],"time":"30 min","cost":"$0-1","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Iron-on numbers or taped paper numbers?","Iron-on for teens and adults who will keep the shirt; taped paper numbers for kids or borrowed shirts. Tape survives one evening fine and peels off clean."],["What if we cannot find green sweatsuits?","Any green top and pants work, the white numbered t-shirt over green is the whole read. The sweatsuit is a nice-to-have, not the costume."]]},
"emotion-crew":{"m":["1 solid bright color outfit per person: yellow, blue, red, green, purple, or orange (make: from closet)","Face paint matching each outfit color, 1 per person (buy: drugstore)","1 white poster board per person (buy: dollar store)","Markers, 1 set (make: from the house)","Colored hair spray matching each outfit, 1 can per person, optional (buy: drugstore)"],"s":["Pull one loud solid-color outfit per person from the closet. Buy the face paint, poster board, and markers.","Each person picks an emotion and writes it big on poster board: Joy, Sadness, Anger, Fear, Disgust, Anxiety, Envy, Embarrassment, Ennui.","Paint a simple face design in the matching color: a big smile, a tear, furrowed brows. Mist hair with the matching color spray if you like.","Wear the full monochrome outfit with the emotion sign. Group up in a row like the control panel.","Optional pro finish: paint each face design in the matching outfit color only, one color per person. Mixed colors muddy the read; monochrome reads as a character."],"time":"25 min + drying","cost":"$2-3","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you stop two people picking the same emotion?","Assign emotions before anyone shops: Joy, Sadness, Anger, Fear, Disgust, Anxiety, Envy, Embarrassment, Ennui. First come first served, written on a list."],["How big should the emotion sign be?","Letter it 4 inches tall minimum on the poster board. The sign is the costume's label: if nobody can read it across the room, it is decoration."]]},
"kart-racers":{"m":["Large cardboard box, 1 per racer, big enough to fit around the torso (make: collect spares)","Red, blue, green, and yellow paint or wrapping paper, 1 bottle or roll per color (buy: dollar store)","Paper plates for wheels, 4 per kart (buy: dollar store)","Racing cap or helmet, 1 per person (own: from closet)","Scissors, 1 pair, tape, 1 roll, and string, 1 spool (own: household tools)","Ribbon for kart straps, about 3 feet per kart (own: from closet)"],"s":["Have each racer step inside the box first and mark where the waist sits BEFORE cutting, an opening cut too big slides down, and cardboard cut away cannot be put back.","Cut the top and bottom out of each box so it fits around the torso like a kart, starting with a smaller opening and widening. Paint each kart a different bright color.","Tape two paper-plate wheels to each side. Tape ribbon straps inside so the kart hangs at waist height.","Safety: keep the kart box at waist height so legs move freely, and tape all cut edges smooth.","Wear the kart with the racing cap, line up side by side, and strike the starting-grid pose.","Optional pro finish: number each kart with a big marker digit on the front. Numbered karts turn a row of boxes into a starting grid."],"time":"45 min + drying","cost":"$1-2","effort":"Medium","sizing":"One per person, so kids and adults each get a real fit. Have each wearer step into the box before you mark arm and leg holes, cut them a little wide, and tape every inside edge so cardboard never scratches.","faqs":[["How do you wear a cardboard kart without tripping?","Keep the box at waist height with the ribbon straps, and keep the bottom opening wide enough that legs move freely. Tape all cut edges smooth so cardboard never scratches thighs."],["Paint or wrapping paper for the kart color?","Wrapping paper is faster and has zero drying time; paint looks better up close. For kids, wrapping paper wins, they can help tape it on."]]},
"tall-hat-crew":{"m":["Tall red-and-white striped stovepipe hat, 1 (buy: costume aisle, or make: poster board)","Red bow tie, 1 (buy: dollar store, or make: paper)","Black shirt and pants for the cat, 1 set (own: from closet)","Red jumpsuits or red shirts and pants for the Things, 2 sets (own: from closet)","Blue wigs, 2 (buy: costume aisle)","Iron-on letters or paper that says Thing 1 and Thing 2, 1 set (buy: craft store)","Iron, 1, and scissors, 1 pair (own: household)"],"s":["Cat: wear the black shirt and pants, the tall striped hat, and the red bow tie.","Position the paper letters on each chest and check the spelling and straightness in a mirror BEFORE ironing, since iron-on letters cannot be removed.","Things: wear the red jumpsuits with the blue wigs. Iron or tape Thing 1 and Thing 2 onto the chests.","The Things bounce and cause trouble; the cat looks worried. That is the whole photo.","Optional pro finish: add white gloves for the Things and a red ribbon tail on the cat, both cheap and both sell the characters."],"time":"20 min","cost":"$10-13","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you make the tall hat from poster board?","Roll the poster board into a tall cone and tape the seam, then cut a wide circle with a hole for the brim and tape it to the base. Paint or tape on the red stripes."],["How does the tall hat stay on?","Thread an elastic chin string through the sides or anchor it with bobby pins through the hat into the hair. A snug inner band of folded paper helps too."]]},
"chipmunk-trio":{"m":["Red, blue, and green sweaters or sweatshirts, 1 each (buy: thrift store)","Iron-on letters A, S, T, 1 set (buy: craft store)","Brown felt for ears, 3 pairs worth, 1 sheet 9x12 inches (buy: craft store)","Headbands, 3 (buy: dollar store)","Brown eyeliner for whiskers and a nose, 1 (buy: drugstore)","Fabric glue, 1 tube (buy: craft store)"],"s":["Position the letters with the sweaters laid flat and have each person confirm their letter BEFORE heating the iron, iron-on letters cannot be repositioned.","Iron A onto the red sweater, S onto the blue, T onto the green. Let them cool flat.","Cut round chipmunk ears from the brown felt and glue one pair to each headband.","Wear the letter sweaters with the ear headbands. Draw three whisker dots and a nose on each cheek with the brown eyeliner.","Line up tallest to shortest and sing one note together for the photo.","Optional pro finish: stuff each cheek with a cotton ball for the group photo. Chipmunk cheeks full of 'acorns' get the laugh every single time."],"time":"25 min + drying","cost":"$7-12","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["Which chipmunk is which?","Red + A is the leader, blue + S is the cool one, green + T is the chubby one. Line up tallest to shortest in that order and the reference lands."],["No iron, can I still do the letters?","Yes: cut the letters from felt and fabric-glue them on, or safety-pin paper letters. Iron-on is cleanest, but glued felt survives the night."]]},
"galaxy-knights":{"m":["1 brown or beige bathrobe or long coat per knight (make: from closet)","1 toy energy-blade prop per knight (buy: toy store)","1 wide belt or rope sash per knight (make: from closet)","1 pair dark pants and boots per knight (make: from closet)","Brown face paint for a hood shadow, 1 tube, optional (buy: drugstore)"],"s":["Wear the bathrobe over dark pants with the belt tied at the waist. Pull the hood up.","Carry the energy blade unlit until the photo. Two stances: blade up ready, or blade down calm.","Safety: keep the toy blades pointed up or down, never at faces. Sparring stays slow and pretend.","Line up the knights in a row, ignite the blades, and take the council photo.","Optional pro finish: tie the belt over the robe at the natural waist and let the robe flare below it. Belted robes read as uniform; unbelted robes read as bath time."],"time":"10 min","cost":"$6-8","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Are toy energy blades safe for kids?","Yes if they are soft foam or plastic with rounded tips. Keep blades pointed up or down, never at faces, and skip hard plastic for kids under 6."],["How do you make a bathrobe not look like a bathrobe?","Belt it tight at the waist, pull the hood up, and wear dark pants and boots underneath. The belt and the boots do all the work."]]},
"plastic-dream-crew":{"m":["All-pink outfit per person: dress, suit, or sweatsuit, 1 set each (own)","Pink sunglasses, 1 per person (buy: dollar store)","Plastic play accessories: phone, tiara, handbag, 1 per person (own)","Pink feather boa, 1 to share (buy: dollar store, optional)","Blonde wig, 1 per person (buy: costume aisle, optional)"],"s":["Pull an all-pink outfit per person from the closet. Buy the pink sunglasses and feather boa.","Everyone wears pink head to toe with the pink sunglasses. Add the tiara, handbag, or toy phone.","Drape the feather boa over whoever is feeling the most plastic today.","Strike the wave-and-smile pose. Everything is pink, and that is the whole point.","Optional pro finish: give everyone the same accessory, matching sunglasses or matching purses. Uniform accessories are what turn pink outfits into a crew.","Optional pro finish: try the wig on for 20 minutes before the party. Itchy wigs get ripped off by nine."],"time":"15 min","cost":"$0-2","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Do you need the wigs?","No, matching pink outfits plus matching accessories carry it. Wigs help but the uniformity is the costume, not the hair."],["How do you keep it from looking like just pink clothes?","Commit to the bit: wave like a doll, pose like a doll, talk like everything is fantastic. The performance is the costume."]]},"extinct-party-animal":{"m":["1 jacket or blazer you own (own)","1 sheet green craft felt, 9x12 inches (buy: craft store; construction paper works too)","1 party hat (buy: dollar store or party aisle)","1 blank name badge (buy: office supply aisle)","Fabric glue, 1 tube (buy: craft store)","Marker, 1","Scissors, 1 pair"],"s":["Cut one paper spike first and check the size against the jacket shoulder, about 3 inches tall.","Cut 6 to 8 triangle spikes from the green craft felt with the scissors. Cut them all from the template so the row looks even.","Glue the spikes in a row along the shoulders of the jacket. Let dry 15 minutes.","Write 'Last seen 66 million years ago' on the badge with the marker.","Pin on the badge, put on the party hat, and work the room.","Optional pro finish: write 'Last seen 66 million years ago' in neat block letters on the badge. Neat handwriting sells the museum-label joke; scribble kills it."],"time":"20 min + drying","cost":"$11-14","effort":"Easy","sizing":"Built for teens and adults. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Will the spikes survive on a blazer all night?","Yes if you glue them the night before and let the glue cure. Same-day glue peels when the jacket moves."],["How do you make the party hat stay on?","Tape a bobby pin to the inside of the hat and clip it to the hair. Elastic straps slip; a bobby pin holds."]]},"dino-tourist":{"m":["1 Hawaiian shirt (buy: thrift store, or use your own)","1 fanny pack (own, or buy: thrift store)","1 plush dinosaur tail (buy: toy store or online)","1 toy camera, optional (own)","1 pair sunglasses, optional (own)"],"s":["Pull the Hawaiian shirt and fanny pack from the closet.","Clip or pin the plush tail to your waistband at the back.","Hang the toy camera around your neck.","Put on the sunglasses, ask strangers to take your picture, and complain about the meteor.","Optional pro finish: tuck a folded paper map into the fanny pack and let it stick out. The map is the tourist detail people laugh at."],"time":"10 min","cost":"$5-6","effort":"Easy","sizing":"Built for teens and adults. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you attach the tail so it stays on?","Clip or pin it to the waistband at the back center with two safety pins through the tail's seam. One pin spins; two pins hold."],["How do you make it read as dinosaur, not just tourist?","The tail does all the work. Without it you are just a tourist: wear it high on the waistband where people see it from the side."]]},"raptor-barista":{"m":["Green hoodie, 1 (buy: clothing store, or use your own)","Toy T. rex arms, 1 pair (buy: toy store or online)","Paper coffee cup, 1 (own: from home)","Brown eyeliner pencil, 1 (own, optional)"],"s":["Put on the green hoodie with the hood up.","Strap the tiny T. rex arms over your own arms at the elbows.","Grab the paper coffee cup with the tiny arms and serve.","Optional pro finish: write a fake coffee order on the cup in marker, like RAWR-LATTE, and tape a paper name tag to the hoodie as your barista badge."],"time":"10 min","cost":"$4-5","effort":"Easy","sizing":"Built for teens and adults. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do the tiny arms stay on?","Strap the tiny T. rex arms over your own arms at the elbows. They sit best on a hoodie with snug sleeves so they do not slide down."],["What if I cannot find toy dinosaur arms?","Cut two small arms from green felt and pin them to the hoodie sleeves at the elbows. They will not grip the cup, so tuck the cup between the felt arms for photos."]]},"emotional-support-dinosaur":{"m":["1 vest or sleeveless jacket you own (own)","1 sheet green craft felt, 9x12 inches (buy: craft store; construction paper works too)","1 blank badge or pin (buy: office supply aisle)","Fabric glue, 1 tube (buy: craft store)","Marker, 1","Scissors, 1 pair"],"s":["Cut one paper spike first and hold it against the vest shoulder to check the size, about 3 inches tall.","Cut 6 to 8 triangle spikes from the green craft felt with the scissors using the paper template. Uniform spikes look designed; freehand spikes look ragged.","Glue the spikes along the vest shoulders and back. Let dry 15 minutes.","Write 'Emotional Support Dinosaur. Do not pet.' on the badge with the marker.","Pin it on and refuse all pets.","Optional pro finish: write 'Emotional Support Dinosaur' in all caps on the badge, then add 'Do not pet.' underneath in smaller letters. The official-looking hierarchy sells the joke."],"time":"25 min + drying","cost":"$10-12","effort":"Easy","sizing":"Built for teens and adults. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Will fabric glue hold spikes through a night of hugs?","Yes if you glue the night before so it cures fully. Same-day glue is still tacky by party time and spikes slide."],["What vest works best?","Any vest or sleeveless jacket with structured shoulders: denim, fleece, or utility. Floppy vests let the spikes droop."]]},
  "garden-fairy":{"m":["Pink tulle, 1 yard (buy: craft store)","Cardboard for wings, 1 large piece about 2x3 feet (make: from a shipping box)","Fake flowers, 1 bunch (buy: dollar store)","Headband, 1 (buy: dollar store, or own)","Wooden dowel or stick for the wand, about 12 inches (make: from the yard)","Cardboard star for the wand tip, 1 (make: from scraps)","Elastic for wing straps, about 2 feet (buy: craft store)","Glitter glue, 1 tube (buy: craft store)","Tape, 1 roll","Glue, 1 bottle","Scissors, 1 pair"],"s":["Draw ONE wing on paper, cut it, and trace it flipped for the second. Symmetric wings are the fairy illusion. Cut two large wing shapes from the cardboard with the scissors.","Cover each wing with pink tulle and tape the edges down.","Glue fake flowers around the headband for the crown.","Tape the cardboard star to the top of the dowel for the wand.","Safety: keep the wand away from faces during photos.","Tape elastic straps to the back of the wings and slip arms through.","Optional pro finish: outline the wing edges with glitter glue and add three dots down the center. The glitter edge catches light in every photo."],"time":"20 min + drying","cost":"$16-19","effort":"Easy","sizing":"Built for kids ages 3 to 10. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How do you keep cardboard wings from flopping?","Score a center crease and tape a ruler or paint stick along the back as a spine. Flat cardboard folds; spined cardboard holds."],["What is the fastest fairy wand?","A stick with a star cut from cardboard, glittered, taped on. Five minutes, and every fairy photo needs the wand."]]},
  "ballerina":{"m":["Pink tulle, 2 to 3 yards (buy: craft store; about $1 a yard)","Wide elastic, 1 inch wide, cut to the waist size plus 1 inch overlap (buy: craft store)","Pink leotard or fitted shirt, 1 (own, or buy: clothing store)","Pink tights, 1 pair (own, or buy: clothing store)","Hair ties and bobby pins, 1 pack (own)","Scissors, 1 pair"],"s":["Measure the waist with the elastic: wrap it snug where the tutu will sit, overlap 1 inch, and cut.","Tie or knot the overlap into a loop, this is the waistband. Cut it to the waist, not the hips, or the tutu slides down while twirling.","Cut the tulle into strips about 3 inches wide and twice as long as you want the skirt. For a toddler, strips roughly 3 by 20 inches; longer for bigger kids.","Fold one strip in half to make a loop at the top. Slip the loop under the elastic, pull the strip ends through the loop, and pull tight.","Repeat side by side all the way around until the tutu looks full, usually 30 to 40 strips.","Fluff the strips outward. Trim the bottom edge even while the tutu hangs.","Safety: the elastic should sit snug on the waist, not the hips, so it stays up while twirling. Nothing tied around the neck.","Wear the tutu over the leotard and tights. Pull the hair into a high bun with the hair ties and bobby pins.","Optional pro finish: tie a short length of satin ribbon into a small bow and pin it at the back waistband. One bow is the difference between craft project and costume."],"time":"20 min","cost":"$10-11","effort":"Easy","sizing":"Built for kids ages 3 to 10. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How much tulle for a no-sew tutu?","2 yards for a toddler, 3 for a bigger kid. Cut strips 3 inches wide, with length equal to twice the finished skirt length."],["How do you keep a no-sew tutu from falling down?","Measure the elastic snug at the waist (not the hips) with a 1-inch overlap, and tie strips tight against each other so the weight stays balanced."]]},
  "butterfly":{"m":["Large cardboard for wings, 1 sheet about 3x2 feet (make: from a shipping box)","Acrylic paint set, 1 (buy: craft store)","Black sweatsuit, 1 set (own, or buy: clothing store)","Elastic for wing straps, about 2 feet (buy: craft store)","Headband, 1 (buy: dollar store, or use your own)","Pipe cleaners for antennae, 2 (buy: craft store)","Tape, 1 roll","Scissors, 1 pair"],"s":["Draw ONE wing on paper first, cut it out, and trace it flipped for the second, symmetric wings are the whole butterfly illusion.","Cut two big wing shapes from the cardboard with the scissors following the template.","Paint both wings with bright patterns and let them dry flat.","Tape elastic loops to the back of each wing for the arms.","Bend pipe cleaners into antennae and tape them to the headband.","Safety: keep wing edges away from doorways; turn sideways to pass through.","Wear the wings over the black sweats with the antennae headband.","Optional pro finish: outline the wing patterns with glitter glue after the paint dries. The glitter edge catches light and photographs like real wing scales."],"time":"40 min + drying","cost":"$12-14","effort":"Medium","sizing":"Built for ages 1 to 8. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How big should butterfly wings be?","Wingtip to wingtip about as wide as the wearer's arm span. Bigger looks majestic in photos but will not fit through doorways, turn sideways."],["How do you attach wings so they stay up?","Tape two elastic loops to the back of each wing and slip arms through like a backpack. Elastic, not ribbon, it flexes when they move."]]},
  "pop-star":{"m":["Sparkly or sequin jacket, 1 (buy: thrift store)","Toy microphone, 1 (buy: toy store or dollar store)","Hair teasing comb, 1 (own, or buy: drugstore)","Sunglasses, 1 pair (own, or buy: dollar store)","Dark jeans and a dark top, 1 set (own)"],"s":["Tease the hair big with the comb.","Safety: go easy teasing near the scalp; no pulling hard.","Wear the sparkly jacket over the dark jeans and top.","Put on the sunglasses.","Carry the toy microphone everywhere and take requests.","Optional pro finish: learn one 8-count of choreography and do it on request all night. A pop star who performs is unforgettable; one who just stands there is overdressed."],"time":"15 min","cost":"$5-7","effort":"Easy","sizing":"Built for kids ages 3 to 10. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Which pop star should I pick?","Whoever's outfit you can build from your closet, the hair and the attitude matter more than the exact outfit. Commit to one era, not a mashup."],["How do you get big pop-star hair?","Backcomb the crown, spray it, and let the ends stay smooth. Volume on top, smooth below, that is the silhouette."]]},
  "ice-skater":{"m":["White dress, 1 (buy: thrift store, or own)","White tights, 1 pair (own, or buy: clothing store)","Hair donut for the bun, 1 (buy: drugstore)","Blush, 1 (own, or buy: drugstore)","Bobby pins, 1 pack (own)"],"s":["Buy or pull the white dress, white tights, and hair donut.","Twist the hair into a high bun around the hair donut and pin it.","Dab a little blush on the cheeks for the cold-air glow.","Safety: skip real skates; this costume is for dry land only.","Wear the white dress with the tights and strike the finishing pose.","Optional pro finish: wrap white ribbon crisscrossed up the calves over the tights. The laced calves read as skates even in sneakers."],"time":"10 min","cost":"$3-4","effort":"Easy","sizing":"Built for kids ages 3 to 10. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["No ice skates, what goes on the feet?","White sneakers or white boots. Nobody sees feet past the laced calves; the ribbon lacing does the work."],["How do you get the perfect skater bun?","A hair donut plus bobby pins, twist the hair around the donut and pin every inch. The donut is the difference between a bun and a lump."]]},
  "ladybug":{"m":["Red shirt, 1 (own)","Black pants, 1 pair (own)","Black felt for dots, 1 sheet 9x12 inches (buy: craft store)","Headband, 1 (buy: dollar store)","Black pipe cleaners for antennae, 2 (buy: craft store)","Black pom-poms, 2 small (buy: craft store)","Scissors, 1 pair","Fabric glue, 1 tube (buy: craft store)"],"s":["Cut lots of circles from the black felt with the scissors.","Arrange all the dots on the shirt DRY first and step back to check, dots cluster in the middle if you glue as you go.","Cut 8 to 10 black felt circles with the scissors, arrange them spread across the red shirt, then glue.","Cut two small wing shapes from the felt scraps, dot them, and pin them at the back.","Bend pipe cleaners into antennae and attach them to the headband.","Safety: pin the wings where little hands cannot reach the pins.","Wear the dotted sweats with the antennae headband.","Optional pro finish: paint a black center line down the back of the shirt with fabric paint. The center line splits the wings, without it, the dots read as polka dots, not ladybug."],"time":"20 min + drying","cost":"$12-14","effort":"Easy","sizing":"Built for ages 1 to 8. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How many dots does a ladybug need?","Seven is the classic (like the seven-spotted ladybug), but 8 to 10 spread evenly photographs better. Odd numbers look natural; even numbers look patterned."],["How do you keep felt dots on through the night?","Fabric glue applied the night before, or safety pins from inside for day-of. Tape peels by hour two, do not trust tape."]]},
  "daisy":{"m":["Yellow craft foam sheets, 2 (buy: craft store)","Brown craft foam for the flower center, 1 sheet (buy: craft store)","Green dress, 1 (own, or buy: thrift store)","Headband, 1 (buy: dollar store, or use your own)","Glue, 1 tube craft glue (buy: craft store)","Scissors, 1 pair"],"s":["Cut 10 to 12 petal shapes from the yellow craft foam with the scissors.","Arrange all 10 to 12 petals around the headband DRY before gluing, once craft glue sets, petals cannot be repositioned. Glue the petals in a ring around the headband, tips pointing out, overlapping slightly.","Glue the brown foam circle in the center of the petals.","Safety: let the glue dry fully before wearing.","Wear the flower headband with the green dress.","Optional pro finish: dot the brown center with yellow fabric paint dots for pollen texture. The textured center is what makes it read as a real flower up close."],"time":"30 min + drying","cost":"$7","effort":"Easy","sizing":"Built for ages 1 to 8. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How many petals does a daisy need?","Ten to twelve. Fewer looks sparse, more looks like a sunflower. Overlap them slightly so no headband shows through."],["Foam or felt for the petals?","Craft foam holds its shape and springs back; felt flops by hour two. Foam costs a little more and looks twice as good."]]},
  "little-baker":{"m":["White paper or poster board for the hat, 2 sheets (buy: craft store, or use printer paper)","Apron, 1 (own, or buy: dollar store)","Toy whisk, 1 (buy: toy store or dollar store)","Flour from the kitchen, 1 pinch (optional, for the effect)","Tape, 1 roll","Scissors, 1"],"s":["Roll the paper into a tall chef hat shape and tape the seam.","Measure the head with a paper strip BEFORE cutting. The hat band must fit snug or it slides over the eyes. Trim the hat band to fit the head with the scissors.","Safety: keep real flour away from eyes; a tiny pinch on the apron only.","Wear the hat and the apron.","Carry the toy whisk and offer everyone imaginary cupcakes.","Optional pro finish: dust the apron with a little flour before heading out. One flour smudge is the difference between 'dressed as a baker' and 'is a baker.'"],"time":"15 min","cost":"$5-8","effort":"Easy","sizing":"Built for kids ages 3 to 10. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["Chef hat or baker hat, different?","Same hat, different props. Chefs carry the spoon; bakers carry the mixing bowl. The prop names the profession."],["How do you keep a paper hat on a toddler?","Elastic chin strap taped inside the band, loose enough for two fingers. Paper hats without straps last about four minutes on a toddler."]]},
  "little-artist":{"m":["Beret or flat cap, 1 (buy: thrift store)","Cardboard for the palette, 1 piece (make: from a shipping box)","Washable paint set, 1 (buy: craft store)","Old smock or oversized t-shirt, 1 (own)","Paintbrush, 1 (own, or buy: craft store)","Scissors, 1 (own)"],"s":["Draw the kidney-bean palette shape on the cardboard and check the size against the forearm BEFORE cutting. A palette cut too small looks like a toy. Cut it out with the scissors.","Paint dabs of bright color around the palette edge and let dry.","Flick a little paint onto the smock for splatters and let dry.","Safety: use washable paint only; cover the table before splattering.","Wear the smock and the tilted beret, and carry the palette and brush.","Optional pro finish: squeeze real paint dabs onto the cardboard palette and carry it. A palette with actual paint on it is the prop that makes strangers say 'oh, an artist!' instead of 'nice beret.'"],"time":"15 min + drying","cost":"$10-11","effort":"Easy","sizing":"Built for kids ages 3 to 10. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you keep the beret on a small head?","Bobby-pin it at both temples, tilted to one side. Berets slide straight back without pins, the tilt plus pins locks it."],["What is on the cardboard palette?","Dabs of the same face paint colors, arranged in a circle. Match the palette to the cheek dabs and the costume tells one coherent story."]]},
  "beekeeper-bee":{"m":["White long-sleeve shirt and white pants, 1 set (own, or buy: thrift store)","Fine mesh fabric or a mosquito head net, 1 (buy: craft store or camping aisle)","Wide-brim hat, 1 (own, or buy: dollar store)","Yellow shirt and yellow pants, 1 set (own, or buy: thrift store)","Black electrical tape, 1 roll (buy: dollar store)","Black pipe cleaners for antennae, 2 (buy: craft store)","Headband, 1 (buy: dollar store, or use your own)","Yellow and black face paint sticks, 1 set (buy: craft store)","Scissors, 1 pair"],"s":["Beekeeper: drape the mesh fabric over the wide-brim hat so it hangs past the shoulders, and tie it at the neck.","Cut the face opening wide first, you can trim it neater after the first fitting.","Bee: wrap 3 to 4 black tape stripes around the yellow shirt and pants, evenly spaced. Press the tape flat so the edges do not peel.","Bend the pipe cleaners into a V and tape them to the headband for antennae. Add two black face-paint dots on the cheeks.","Safety: cut the veil opening wide enough that vision stays clear, and tie nothing tight around the neck. Use tape, not string, for the stripes so nothing unravels.","The adult is the beekeeper: white outfit with the veil hat, since the mesh limits vision. The smaller of the two is the bee: stripes with the antennae headband.","Optional pro finish: the beekeeper carries a small cardboard sign that says HONEY, and the bee poses mid-buzz next to it. One shared prop is what makes a pair read as a pair."],"time":"25 min + drying","cost":"$8-11","effort":"Easy","sizing":"Each partner builds their half in their own size. Elastic headbands fit most kids and adults; if the costume uses a paper bag or mask, cut the face opening while it is on the wearer, small first, then widen until they see and breathe easily.","faqs":[["How do you make a beekeeper veil you can see through?","Use fine mesh fabric or a mosquito head net draped over a wide-brim hat, with the face opening cut wide and the fabric tied at the neck, never taped to the skin."],["Will the black tape stripes stay on all night?","Press electrical tape flat onto clean, dry fabric and it holds for an evening. For a longer night, use black felt strips with fabric glue instead."]]},
  "tetris-duo":{"m":["Two large cardboard boxes, flattened (make: from shipping boxes)","Acrylic paint in two bright colors, 1 set (buy: craft store)","Wide ribbon or webbing for shoulder straps, about 4 yards (buy: craft store)","Painter's tape, 1 roll (buy: dollar store)","Scissors or a box cutter, 1","Ruler or yardstick, 1 (own)"],"s":["Mark a grid of 12-inch squares on the cardboard with the ruler.","Each block shape is 4 squares: cut an L shape for one person and a T or square shape for the other. Cut the squares oversized first and trim after a fitting.","Paint each shape its color and let dry fully, flat, for at least 2 hours.","Tape ribbon loops to the top of each shape for shoulder straps. Test the hang before the party: each shape should sit at chest height.","Safety: cut on a protected surface with the blade pointed away from fingers, and round the cardboard corners so nobody gets poked in a crowd.","Each person wears one shape like a sandwich board, front and back panels tied with the ribbon straps.","Optional pro finish: stand so the two shapes interlock for photos, and let strangers name your pieces. The click-together pose is the whole costume."],"time":"45 min + drying","cost":"$8-10","effort":"Easy","sizing":"Each partner builds their half in their own size. Have each wearer step into the box before you mark arm and leg holes, cut them a little wide, and tape every inside edge so cardboard never scratches.","faqs":[["What are the easiest block shapes to build?","The 2 by 2 square and the L shape: both are rectangles with one extra cut, no fiddly notches. Paint them different colors so they read as two pieces."],["How do you keep the cardboard from flopping?","Use double-wall cardboard from a shipping box, not a cereal box, and keep each piece to 4 squares. Bigger pieces fold at the seams."]]},
  "little-lifeguard":{"m":["Red t-shirt, 1 (own, or buy: thrift store)","Plastic whistle on a lanyard, 1 (buy: dollar store or party store)","Pool noodle, 1 (buy: dollar store)","White duct tape, 1 roll (buy: dollar store)","Red shorts or swim trunks, 1 pair (own)","White face paint stick for the nose stripe, 1 (buy: craft store)","Scissors, 1 pair"],"s":["Cut the pool noodle with the scissors and curve it into a ring, taping the ends together with the white duct tape. An adult should do the cutting: pool noodles need firm pressure.","Wrap 4 white tape bands evenly around the ring so it reads as a rescue buoy.","Safety: the whistle is a photo prop the parent holds and brings out for pictures, not a blow-all-night toy.","Safety: The buoy is a costume prop, not a flotation device. Keep the lanyard short so it cannot catch on anything.","Wear the red tee and shorts and carry the buoy over one shoulder. The parent keeps the whistle and hands it over for photos.","Dab the white face paint stripe across the nose.","Optional pro finish: write LIFEGUARD across the back of the tee with the white duct tape in block letters. Back lettering is what strangers read first."],"time":"20 min + drying","cost":"$15-20","effort":"Easy","sizing":"Built for ages 1 to 8. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you make the pool noodle ring stay round?","Cut the noodle ends at an angle so they meet in a clean joint, then wrap the joint with 3 layers of duct tape. The tape joint is stronger than the foam."],["Is a real whistle too loud for a kid costume?","One toot at a time is the rule. Party-store whistles are plenty loud; skip the metal coach whistles."]]},
  "little-prince":{"m":["Gold cardstock or a paper crown, 1 (buy: party store, or make: from cardstock)","Red or purple fabric for the cape, about 1 yard (own, or buy: craft store)","Wide ribbon for the sash, about 2 yards (buy: craft store)","Stick-on plastic gems, 1 pack (buy: dollar store)","White gloves, 1 pair (buy: dollar store, optional)","Safety pins, 2","Scissors, 1 pair","Glue stick, 1"],"s":["Cut the cardstock into a crown band sized to the head, overlap 1 inch, and glue. Cut triangle points along the top edge.","Press the stick-on gems around the crown band, one big gem centered on the front.","Drape the fabric as a cape.","For under-5s, skip the pins: tie the cape's top corners to the shirt shoulders with short ribbon ties, or glue the top edge to the back of the shirt. Nothing tied around the neck.","Safety: no pins near little hands. Keep the cape above the knees so it cannot trip. Nothing tied around the neck.","Sash: drape the wide ribbon from one shoulder to the opposite hip and tape or glue it at the waist.","Optional pro finish: tilt the crown slightly to one side. A crooked crown is the whole charm of a little prince."],"time":"20 min + drying","cost":"$13-14","effort":"Easy","sizing":"Built for ages 1 to 8. Size the cape to the wearer: it should fall above the knees, and the neck tie stays loose and easy to pull free.","faqs":[["How do you keep a paper crown from tearing?","Use cardstock, not printer paper, and overlap the band a full inch before gluing. The stick-on gems add stiffness as a bonus."],["What if we have no cape fabric?","A red bath towel or a pillowcase works. Pin it at the shoulders, never tie it at the neck, and trim it above the knees."]]},
  "fossil-hunter":{"m":["Khaki or tan vest with pockets, 1 (own, or buy: thrift store)","Toy paintbrush or makeup brush, 1 (own, or buy: dollar store)","Toy magnifying glass, 1 (buy: dollar store)","Cardboard for fossil bones, 1 sheet (make: from a shipping box)","Small canvas pouch or fanny pack, 1 (own, or buy: dollar store)","Brown paper lunch bag, 1 (own)","Scissors, 1 pair","Pencil, 1"],"s":["Draw bone shapes on the cardboard with the pencil: a femur, a rib, a skull. Keep them chunky, thin cardboard bones snap.","Cut the bones out with the scissors and shade the edges with the pencil for the dug-up look.","Tuck the cardboard bones into the pouch so the tops peek out.","Safety: round all cardboard corners, and carry the brush bristles-down so nobody gets poked. Under 3: skip the bones and magnifying glass as carry props. Toddlers mouth everything and cardboard snaps. The vest and pouch alone carry the costume.","Wear the khaki vest over a plain shirt, the pouch on the belt, the brush in one pocket. Ages 3+: add the magnifying glass to the other pocket.","Optional pro finish: crumple the brown paper bag into a specimen bag and label it with the pencil. One labeled prop sells the whole expedition."],"time":"25 min","cost":"$4-5","effort":"Easy","sizing":"Built for kids and adults. Start from clothes the wearer already owns in their size, and size the vest and pouch against them before the fitting. The paper bag is a specimen bag, not a mask, so it needs no face opening.","faqs":[["How do you make cardboard bones look like fossils?","Cut them chunky, shade the edges with pencil, and rub a little dirt-colored eyeshadow into the surface. Uneven shading beats perfect coloring."],["What goes in the belt pouch?","The cardboard bones with their tops peeking out, plus the brush. A pouch that bulges with finds reads as a real dig kit."]]},
  "milk-cookies":{"m":["White t-shirt or tunic, 1 (own, or buy: thrift store)","Brown t-shirt or tunic, 1 (own, or buy: thrift store)","White craft felt, 1 sheet 9x12 inches (buy: craft store)","Brown craft felt, 2 sheets 9x12 inches (buy: craft store)","Black marker, 1 (own)","Fabric glue, 1 bottle (buy: craft store)","Safety pins, 4 (buy: dollar store, or raid the sewing kit)","Scissors, 1 pair"],"s":["Buy the felt, marker, and glue. Pull a white and a brown t-shirt from the closet.","Milk: cut the white felt into a carton-front rectangle about the size of a placemat. Write MILK across it in big block letters with the black marker.","Pin the carton front to the white t-shirt, pinning from inside the shirt so the pin backs face the fabric and never the skin.","Cookie: cut the biggest circle you can from the brown felt and pin it centered on the brown t-shirt.","Cut a dozen small chip shapes from the leftover brown felt and glue them onto the cookie circle. Uneven spacing looks more like a real cookie.","Safety: check every pin from the inside before heading out, and keep glued felt flat so edges do not curl and catch.","Optional pro finish: the milk person carries a paper straw. One shared prop is what makes a pair read as a pair."],"time":"25 min + drying","cost":"$4-5","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you keep the felt pieces from flopping?","Pin each felt piece at 4 points, not 2. Felt pinned at the corners stays flat all night, and fabric glue on the chips keeps them from peeling."],["What if we have no brown felt?","A brown paper grocery bag cut into a circle works for one night. Glue paper chips on and pin the circle to the shirt."]]},
  "chips-guac":{"m":["Green t-shirt or tunic, 1 (own, or buy: thrift store)","Tan t-shirt or tunic, 1 (own, or buy: thrift store)","Red craft felt, 1 sheet 9x12 inches (buy: craft store)","Yellow craft felt, 1 sheet 9x12 inches (buy: craft store)","Tan craft felt, 2 sheets 9x12 inches (buy: craft store)","Headband, 1 (buy: dollar store, or use your own)","Fabric glue, 1 bottle (buy: craft store)","Scissors, 1 pair"],"s":["Buy the felt and glue. Pull a green and a tan t-shirt from the closet.","Guac: cut small circles from the red and yellow felt, about quarter size. These are the tomato and onion.","Glue the dots scattered across the front of the green t-shirt. Let the glue dry flat for 20 minutes.","Chip: cut a triangle from the tan felt about 2 feet tall with a wide base.","Glue the base of the triangle to the headband so it stands upright. Add a second small triangle behind it for stiffness.","Safety: keep the chip triangle light, felt only, so it cannot poke anyone in a crowd. Skip cardboard for the tall piece.","Optional pro finish: the guac person carries a small bowl. Serving the chip person from it in photos is the whole joke."],"time":"30 min + drying","cost":"$3-4","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you keep the chip triangle standing up?","Two layers of felt glued together hold their shape. For a taller chip, glue a pipe cleaner up the center as a spine."],["Will the felt dots survive the night?","Fabric glue on clean, dry cotton holds for an evening. Press each dot flat for 30 seconds when you glue it."]]},
  "sushi-soy":{"m":["White t-shirt or tunic, 1 (own, or buy: thrift store)","Dark brown or black t-shirt, 1 (own, or buy: thrift store)","Orange craft felt, 1 sheet 9x12 inches (buy: craft store)","Black craft felt, 1 sheet 9x12 inches (buy: craft store)","Cardboard for the soy bottle, 1 sheet (make: from a shipping box)","Dark brown acrylic paint, 1 bottle (buy: craft store)","Red paper for the bottle cap, 1 sheet (buy: dollar store)","Ribbon for straps, about 2 yards (buy: craft store)","Tape, 1 roll","Scissors, 1 pair"],"s":["Buy the felt, paint, and ribbon. Pull a white and a dark t-shirt from the closet.","Sushi: cut an orange felt rectangle about the size of a paperback and glue it across the chest of the white t-shirt. This is the salmon.","Cut a black felt band 3 inches wide and glue it around the waist over the orange rectangle, like the seaweed holding the fish on.","Soy sauce: cut a tall bottle shape from the cardboard, about 2 feet tall, with a narrow neck.","Paint the bottle dark brown and let it dry flat. Fold red paper into a cap and tape it to the neck.","Tape ribbon loops to the top of the bottle and wear it like a sandwich board over the dark t-shirt.","Safety: round all cardboard corners with the scissors so nobody gets poked in a crowd.","Optional pro finish: the sushi person leans toward the soy bottle in every photo. The dip is the pose."],"time":"30 min + drying","cost":"$6-7","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you keep the cardboard bottle from folding?","Use double-wall cardboard from a shipping box, not a cereal box, and keep the bottle under 2 feet tall."],["What if the paint is still tacky at party time?","Paint the bottle first and let it dry while you build the sushi. Dark paint needs a full hour on cardboard."]]},
  "burger-fries":{"m":["Tan t-shirt, 1 (own, or buy: thrift store)","Red t-shirt, 1 (own, or buy: thrift store)","Green, red, and yellow craft felt, 1 sheet each 9x12 inches (buy: craft store)","Tan felt for the bun top, 1 sheet (buy: craft store)","Paper bowl for the bun, 1 large (buy: grocery store)","Cardboard for the fry carton, 1 sheet (make: from a shipping box)","Red acrylic paint or red paper, 1 (buy: craft store)","Yellow paper for fry sticks (buy: dollar store, or make: from paper)","Tape, 1 roll","Scissors, 1 pair"],"s":["Buy the felt, bowl, and paint. Pull a tan and a red t-shirt from the closet.","Burger: cut wavy felt strips, green for lettuce, red for tomato, yellow for cheese. Glue them in a stack across the tan t-shirt.","Cover the paper bowl with tan felt and wear it upside down as the bun top.","Fries: fold the cardboard into an open-top carton and paint it red, or cover it with red paper. Let it dry.","Cut yellow paper into fry sticks and glue them poking out of the carton top.","Wear the fry carton like a sandwich board over the red t-shirt, with ribbon straps over the shoulders.","Safety: round the cardboard corners, and keep the fry sticks soft paper, never wood, so the carton is crowd-safe.","Optional pro finish: drop real wrapped candy into the fry carton. A fry box that hands out candy wins every party."],"time":"35 min + drying","cost":"$2-4","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you keep the bun bowl on your head?","Wear it tilted back like a hat, not balanced on top. A strip of double-sided tape inside the rim keeps it put."],["Can the fry carton hold real candy?","Yes, line it with a plastic bag first so grease never touches the cardboard, and keep it to wrapped candy."]]},
  "donut-coffee":{"m":["White t-shirt, 1 (own, or buy: thrift store)","Brown t-shirt, 1 (own, or buy: thrift store)","Pink craft felt, 2 sheets 9x12 inches (buy: craft store)","Cardboard ring for the donut, 1 large (make: from a shipping box)","Tan fabric or paper to cover the ring (own, or buy: craft store)","Cardboard for the coffee cup, 1 sheet (make: from a shipping box)","Brown acrylic paint, 1 bottle (buy: craft store)","White paper for the cup lid, 1 sheet (buy: dollar store)","Tape, 1 roll","Scissors, 1 pair","Ribbon for straps, about 2 yards (buy: craft store)"],"s":["Buy the felt and paint. Pull a white and a brown t-shirt from the closet.","Donut: cut a large ring from the cardboard, about 2 feet across, with a 10-inch hole in the middle.","Cover the ring with tan fabric or paper, then glue a pink felt ring on top for the frosting. Dot it with small felt sprinkles in bright colors.","Tape ribbon loops to the ring and wear it over the white t-shirt like a sandwich board.","Coffee: roll cardboard into a tall cup shape and tape the seam. Paint it brown and let it dry.","Fold the white paper into a lid and tape it to the top of the cup. Wear the cup like a sandwich board over the brown t-shirt.","Safety: round all cardboard edges, and keep the donut hole big enough that arms move freely.","Optional pro finish: the coffee person links arms with the donut person. The breakfast-date pose photographs itself."],"time":"35 min + drying","cost":"$5-7","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you cut a clean donut ring?","Trace a large mixing bowl for the outside and a salad plate for the hole. Cut the hole first while the cardboard is whole, then the outside."],["How do you keep the frosting ring from peeling?","Glue the pink felt in sections and press each for 30 seconds. Felt glued all at once bubbles and lifts."]]},
  "wine-cheese":{"m":["Burgundy or maroon t-shirt, 1 (own, or buy: thrift store)","Yellow t-shirt, 1 (own, or buy: thrift store)","White craft felt, 1 sheet 9x12 inches (buy: craft store)","Burgundy craft felt, 1 sheet 9x12 inches (buy: craft store)","Fabric glue, 1 bottle (buy: craft store)","Scissors, 1 pair"],"s":["Buy the felt and glue. Pull a burgundy and a yellow t-shirt from the closet.","Wine: cut a wine glass shape from the white felt, bowl, stem, and base in one piece, about a foot tall.","Cut a smaller burgundy felt shape for the wine inside the glass and glue it onto the white glass.","Glue the finished glass centered on the burgundy t-shirt.","Cheese: cut round holes from a yellow felt triangle and pin it over the yellow t-shirt. Swiss reads instantly.","Safety: if cutting holes in the shirt itself, keep them small and away from the seams so the shirt holds its shape.","Optional pro finish: raise your glasses together for every photo. The toast is the costume, so commit to it."],"time":"25 min + drying","cost":"$2-3","effort":"Easy","sizing":"Each partner builds their half in their own size. Start with clothes the wearer already owns in their size. Hold any wearable pieces in place before cutting or taping so they sit comfortably.","faqs":[["How do you cut clean holes in the cheese?","Fold the felt and cut half-circles along the fold, then unfold for perfect circles. Small scissors beat big ones for the curves."],["What if we cannot find a burgundy shirt?","A dark red shirt works. The wine glass felt carries the costume either way."]]},
  "kpop-demon-huntresses":{"m":["Black leggings or pants, 3 (own, or buy: thrift store)","Metallic or shiny tops, 3 (buy: thrift store)","Toy microphones, 3 (buy: dollar store)","Cardboard for swords, 1 sheet (make: from a shipping box)","Silver duct tape, 1 roll (buy: dollar store)","Face paint in purple and black, 1 set (buy: craft store)","Hair gel, 1 (own)","Scissors, 1 pair"],"s":["Agree on one accent color for all three outfits so the trio reads as a unit.","Cut three sword shapes from the cardboard and wrap the blades in silver duct tape.","Dress each hunter in black pants, a metallic top, and bold face paint stripes.","Safety: keep the cardboard swords light and never swing them near faces in a crowd.","Practice one shared pose, microphones up, swords crossed, and hit it for every photo.","Optional pro finish: paint matching symbols on the back of each hand. The matching marks sell the team."],"time":"40 min + drying","cost":"$11-14","effort":"Medium","sizing":"Built for teens and adults. Size the stage outfits to each wearer; cut the cardboard swords to arm length.","safelink":null,"faqs":[["How do you keep three outfits matching without buying new clothes?","One shared accent color plus matching face paint unifies any three black outfits. The audience reads the trio, not the labels."],["What if we only have two people?","Two hunters still work: the duo is the core of the act, and a third friend can join as the villain."]]},
  "goth-braids":{"m":["Black dress, 1 (own, or buy: thrift store)","Black tights, 1 pair (own, or buy: dollar store)","Hair ties, 2 (own)","Black eyeliner, 1 (own, or buy: drugstore)","Pale foundation or white face paint, 1 (buy: drugstore or craft store)","Dark lipstick, 1 (own)"],"s":["Pull the hair into two tight braids, one behind each ear, and tie them off.","Apply the pale foundation lightly, then heavy black eyeliner.","Wear the black dress with black tights and dark lipstick.","Safety: test the face paint on the inside of the wrist first and wash it off before bed so it never stains the pillow.","Practice the stare in the mirror: calm, unimpressed, unblinking.","Optional pro finish: carry a black umbrella even if it is not raining. The prop completes the silhouette."] ,"time":"20 min + drying","cost":"$6-8","effort":"Easy","sizing":"Built for teens and adults. Braid extensions clip to your own hair; trim the colored streaks to match your length.","safelink":null,"faqs":[["How do you keep the braids tight all night?","Braid damp hair and tie each braid at two points, top and bottom. Damp braids set tighter as they dry."],["What if the dress is not quite black enough?","A very dark gray or navy reads black in party lighting. The braids and makeup carry the costume either way."]]},
  "juke-joint-vampires":{"m":["Vintage-style suits, 2 (buy: thrift store)","White dress shirts, 2 (own, or buy: thrift store)","Plastic vampire fangs, 2 sets (buy: dollar store or costume aisle)","Fake blood, 1 bottle (buy: costume aisle)","Hair gel, 1 (own)","Toy trumpet, 1 (buy: dollar store, or borrow one)","Red pocket squares, 2 (buy: thrift store, or cut from fabric)"],"s":["Thrift two suits with a vintage cut and press the shirts.","Slick the hair back with gel and fit the fangs.","Tuck a red pocket square into each jacket and dab fake blood at one corner of the mouth.","One of you carries the toy trumpet everywhere and mimes a solo on cue.","Safety: keep the fangs in a case when eating or drinking, and never share them between people.","Optional pro finish: learn one slow dance move together. A vampire couple that dances owns the room."],"time":"30 min","cost":"$19-41","effort":"Easy","sizing":"Built for teens and adults. Cut the vest and cape pieces to each wearer\u2019s torso; fangs are one-size.","safelink":null,"faqs":[["How do you talk with fangs in?","Moldable fangs fitted to your own teeth let you talk clearly. Practice your lines in the mirror before the party."],["Will the fake blood stain the thrifted suits?","Use washable fake blood and apply it only to the skin near the mouth, never the fabric."]]},
  "blue-heeler-pup":{"m":["Blue-gray hoodie, 1 (own, or buy: thrift store)","Blue-gray sweatpants, 1 (own, or buy: thrift store)","Blue and dark gray craft felt, 1 sheet each 9x12 inches (buy: craft store)","Black face paint or eyeliner, 1 (own)","Safety pins, 4 (buy: dollar store)","Fabric glue, 1 bottle (buy: craft store)","Scissors, 1 pair"],"s":["Cut two triangle ears from the blue felt and glue them to a strip that pins inside the hood.","Glue dark gray felt spots onto the hoodie and one pant leg.","Paint a black nose and a few whisker dots on the child's face with a fingertip.","Pin a short felt tail to the back of the sweatpants, pinning from inside so pin backs face the fabric.","Safety: use face paint, never a mask, on small kids so they can see and breathe easily, and keep pins inside the clothes.","Optional pro finish: teach the pup one trick, like sitting for a treat. A trick makes the costume."] ,"time":"25 min + drying","cost":"$6-7","effort":"Easy","sizing":"Built for kids ages 2 to 6. Start from the child\u2019s own clothes in their size; the ear headband adjusts to fit.","safelink":null,"faqs":[["How do you keep the ears up on the hood?","Glue each ear to a small cardboard triangle first, then pin the triangles inside the hood. Felt alone flops."],["What if the kid will not keep the hood up?","Pin the ears to a soft headband instead. The hood stays down and the ears still read."]]},
  "baby-pumpkin":{"m":["Orange onesie or footed pajamas, 1 (own, or buy: thrift store)","Green craft felt, 1 sheet 9x12 inches (buy: craft store)","Soft stuffing or an old pillow, 1 (own)","Brown felt for the stem, 1 small piece (buy: craft store)","Safety pins, 4 (buy: dollar store)","Scissors, 1 pair"],"s":["Lightly stuff the onesie arms and legs so the pumpkin looks plump, not tight.","Cut leaf shapes from the green felt and pin them around the collar.","Roll the brown felt into a stem and pin it to the top of the hood or a soft hat.","Safety: keep all pins on the outside of the onesie where you can see them, and never pin near the baby's skin. Skip small parts a baby could pull off.","Optional pro finish: photograph the pumpkin in a laundry basket lined with a blanket. The basket is the patch."] ,"time":"20 min","cost":"$3-4","effort":"Easy","sizing":"Built for babies and toddlers under 3. Use a onesie in the child\u2019s actual size; keep the green collar loose around the neck.","safelink":null,"faqs":[["How do you keep a baby warm in just a onesie?","Layer a long-sleeve shirt and tights underneath. The stuffing goes between the layers, never against the skin."],["What if the baby hates the stem hat?","Skip the hat. The orange onesie and leaves alone still read as pumpkin in every photo."]]},
  "pirate-captain":{"m":["Striped shirt, 1 (own, or buy: thrift store)","Dark pants, 1 (own)","Cardboard for the hat, 1 sheet (make: from a shipping box)","Black eye patch, 1 (buy: dollar store, or make: from felt and elastic)","Toy sword or cardboard cutlass, 1 (buy: dollar store, or make: from cardboard)","Brown paper for the treasure map, 1 sheet (own)","Black marker, 1 (own)","Gold plastic coins, 1 bag (buy: dollar store)","Scissors, 1 pair"],"s":["Cut the captain hat from cardboard: a wide crescent with the front folded up, and tape the seam.","Draw the treasure map on the brown paper with the black marker, with an X and a dotted route.","Wear the striped shirt with the pants, the eye patch, and the hat.","Safety: use a cardboard or foam sword, never a real blade, and keep the map rolled when walking in crowds.","Hand out gold coins to kids you meet. A pirate who shares treasure is remembered.","Optional pro finish: learn one pirate phrase and commit to it all night. The voice is half the costume."] ,"time":"30 min","cost":"$3-4","effort":"Easy","sizing":"Built for kids ages 3 to 10 and adults. Size the hat to the wearer\u2019s head; the coat should fall above the knees.","safelink":null,"faqs":[["How do you keep the cardboard hat on?","Cut the hat slightly small and add an elastic chin strap. A hat that fits snug beats one that fits pretty."],["Can a whole group do this together?","Yes: one captain hat for the leader, bandanas for the crew, same striped shirts. The crew reads instantly."]]},
  "cowboy-duo":{"m":["Denim shirts, 2 (own, or buy: thrift store)","Jeans, 2 (own)","Cardboard for two hats, 2 sheets (make: from shipping boxes)","Bandanas, 2 (buy: dollar store)","Brown paper bags for chaps, 2 (own)","Rope or twine, 1 coil (buy: hardware store)","Scissors, 1 pair","Tape, 1 roll"],"s":["Cut two cowboy hats from cardboard: wide brims with folded-up sides, taped at the seam.","Tie a bandana around each neck and coil the rope over one shoulder.","Cut chaps from the paper bags and tape them over the jeans.","Safety: round all cardboard edges, and keep the rope coiled, never looped around anyone.","Tip your hats to everyone you greet. The hat tip is the whole personality.","Optional pro finish: draw sheriff stars on paper and pin one on. The star upgrades the pair."] ,"time":"25 min","cost":"$4-7","effort":"Easy","sizing":"Built for teens and adults. Each partner builds their half in their own size; trim hat brims to fit.","safelink":null,"faqs":[["How do you make cardboard hats look like felt?","Paint them brown and add a darker band around the crown. In evening light, painted cardboard passes."],["What if it rains?","Wrap the hats in clear packing tape before the party. Taped cardboard shrugs off drizzle."]]},
  "smores-duo":{"m":["Tan t-shirts or tunics, 2 (own, or buy: thrift store)","White t-shirt for the marshmallow, 1 (own)","Brown craft felt, 1 sheet 9x12 inches (buy: craft store)","White pillow stuffing, 1 bag (buy: craft store)","Fabric glue, 1 bottle (buy: craft store)","Black marker, 1 (own)","Safety pins, 6 (buy: dollar store)","Scissors, 1 pair"],"s":["Decide who is the front cracker, who is the marshmallow, and who is the back cracker.","Marshmallow: stuff the white t-shirt lightly and wear it between the two tan tunics.","Chocolate: glue the brown felt square onto the front cracker's tunic.","Write GRAHAM in block letters on both tan tunics with the black marker.","Safety: keep the stuffing light so arms move freely, and pin from inside the shirts.","Optional pro finish: stand in cracker-marshmallow-cracker order for every photo. The sandwich order is the joke."] ,"time":"30 min + drying","cost":"$5-7","effort":"Easy","sizing":"Built for teens and adults. Cut the tunic panels to each wearer\u2019s torso width; the marshmallow pillow fits most adults.","safelink":null,"faqs":[["How do you keep the marshmallow puffy without overheating?","Stuff only the front of the shirt and leave the back flat for airflow. A little puff reads plenty."],["Can a third person join?","Yes: a second marshmallow makes it a double-decker. The formula scales."]]},
  "scarecrow":{"m":["Plaid flannel shirt, 1 (own, or buy: thrift store)","Jeans with patches, 1 (own, or buy: thrift store)","Straw, raffia, or yellow yarn, 1 bag (buy: craft store)","Old hat, 1 (own, or buy: thrift store)","Face paint in black and red, 1 set (buy: craft store)","Rope or twine, 1 coil (buy: hardware store)","Safety pins, 4 (buy: dollar store)","Scissors, 1 pair"],"s":["Stuff straw into the shirt cuffs, collar, and pant legs so it pokes out.","Tie straw bundles around the wrists and ankles with twine.","Paint a stitched smile and triangle nose on the face.","Wear the plaid shirt with patched jeans and the old hat.","Safety: test the face paint on a wrist first, and keep straw away from open flames.","Optional pro finish: stand perfectly still when trick-or-treaters approach, then wave. The stillness is the scare."],"time":"25 min + drying","cost":"$17-20","effort":"Easy","sizing":"Built for kids and adults. Size the flannel and overalls to the wearer; straw cuffs tie to fit any wrist or ankle.","safelink":null,"faqs":[["How do you keep the straw from falling out?","Tie each bundle with twine before stuffing it in. Loose straw migrates within an hour."],["What if it rains?","Swap real straw for yellow yarn. Yarn survives drizzle and still reads as straw."]]},
  "yellow-henchmen":{"m":["Yellow t-shirts, 1 per person (own, or buy: thrift store)","Blue overalls or blue jeans, 1 per person (own, or buy: thrift store)","Swim goggles, 1 per person (buy: dollar store)","Black gloves, 1 pair per person (buy: dollar store)","Black marker, 1 (own)","Bananas, 1 bunch (buy: grocery store)"],"s":["Everyone wears yellow on top and blue on the bottom. That is the whole uniform.","Wear the swim goggles on the forehead and draw one big eye on paper to tape inside each lens.","Carry the bananas everywhere and offer them to strangers.","Safety: wear the goggles on the forehead, not over the eyes, so vision stays clear while walking.","Learn one shared gibberish phrase and say it in unison. The unison is the comedy.","Optional pro finish: the tallest henchman stands in the middle for photos. The height lineup makes the crew."] ,"time":"25 min","cost":"$2-3","effort":"Easy","sizing":"Built for kids and adults. Overalls in each wearer\u2019s size; the goggle strap adjusts to fit.","safelink":null,"faqs":[["How many people do you need?","Two works, five is ideal. The joke scales with the headcount."],["What if someone has no overalls?","Blue jeans with suspenders read the same. The yellow shirt and goggles carry it."]]},
  "mystery-teens":{"m":["Solid-color tops in assigned colors, 1 per person (own: from closets)","Jeans or skirts, 1 per person (own)","Toy magnifying glass, 1 (buy: dollar store)","Paper for the sandwich prop, 1 sheet (own)","Dog plush or toy, 1 (own, or borrow one)","Scarves or ascots in matching colors (own, or buy: thrift store)"],"s":["Assign each person a color: orange, blue, purple, green, red.","Everyone builds their outfit from their own closet in their assigned color.","One person carries the magnifying glass, one carries the giant paper sandwich.","Safety: the sandwich prop stays paper and light, and nothing gets swung in crowds.","Introduce yourselves in character when people ask. The names are the costume.","Optional pro finish: bring the dog plush and let one person carry it everywhere. The dog gets more photos than the teens."] ,"time":"20 min","cost":"$0-1","effort":"Easy","sizing":"Built for teens and adults. T-shirts in each person\u2019s size; assign colors before anyone dresses so nothing doubles.","safelink":null,"faqs":[["What if our group has only three people?","Pick any three colors. The color coding reads with three just as well as five."],["How do you make it obvious without name tags?","The magnifying glass, the sandwich, and the dog plush together tell the story. Props beat labels."]]},
  "pumpkin-king-bride":{"m":["Pinstripe or black suit, 1 (buy: thrift store)","Cardboard for the pumpkin mask, 1 sheet (make: from a shipping box)","Orange and black paint, 1 set (buy: craft store)","Patchwork-style dress, 1 (buy: thrift store, or sew: from fabric scraps)","Red yarn for hair, 1 skein (buy: craft store)","Black boots or shoes, 1 pair (own)","Scissors, 1 pair"],"s":["Cut a pumpkin face mask from the cardboard with big eye holes, and paint it orange with black features.","Wear the pinstripe suit with the pumpkin mask.","For the bride: wear the patchwork dress and tie the red yarn into loose pigtails for hair.","Safety: cut the mask eye holes generous and test vision before the party, and keep the yarn hair tied back from candles.","Hold hands and walk slightly apart, like a royal procession.","Optional pro finish: practice one dramatic bow together. The bow is the photo."] ,"time":"45 min + drying","cost":"$8-19","effort":"Medium","sizing":"Built for teens and adults. Size the pinstripe suit and ragdoll dress to each wearer; the bow tie adjusts.","safelink":null,"faqs":[["How do you keep the pumpkin mask comfortable?","Line the inside edge with folded fabric tape. Bare cardboard rubs within an hour."],["What if we cannot find a pinstripe suit?","A plain black suit with white pinstripes drawn on in chalk works for one night."]]},
  "moonwalk-star":{"m":["Red jacket, 1 (buy: thrift store)","Black pants, 1 (own)","White glove, 1 (buy: dollar store)","Silver glitter glue, 1 tube (buy: craft store)","Black fedora or hat, 1 (buy: thrift store)","White socks, 1 pair (own)","Black loafers or dress shoes, 1 pair (own)"],"s":["Cover one white glove in glitter glue and let it dry flat completely.","Wear the red jacket with black pants, white socks, and the fedora.","Put the glitter glove on one hand only. One glove, never two.","Practice the moonwalk and the toe-stand in socks on a smooth floor.","Safety: practice the lean against a wall first, and never attempt it on a wet or crowded floor.","Optional pro finish: freeze mid-moonwalk when cameras appear. The frozen pose beats the dance."] ,"time":"25 min + drying","cost":"$20-36","effort":"Easy","sizing":"Built for teens and adults. The jacket and single glove fit most; size the fedora to your head.","safelink":null,"faqs":[["How do you keep the glitter on the glove?","Two thin coats of glitter glue, drying fully between coats, then a clear sealer. One thick coat sheds everywhere."],["What if we cannot find a red jacket?","A red hoodie with the hood down reads fine at party distance. The glove is the giveaway."]]},
  "witchy-sisters":{"m":["Dresses in green, purple, and orange, 3 (buy: thrift store)","Black witch hats, 3 (buy: dollar store, or make: from cardboard and felt)","Broomsticks, 3 (buy: dollar store, or make: from sticks and straw)","Face paint in matching colors, 1 set (buy: craft store)","Striped tights, 3 pairs (buy: dollar store)"],"s":["Each sister claims a color: green, purple, or orange, and builds around it.","Wear the colored dress with a black witch hat and striped tights.","Paint a matching beauty mark or stripe in your color.","Safety: keep broomsticks pointed down in crowds, and test face paint on a wrist first.","Cackle in unison when anyone takes your photo. The unison cackle is the act.","Optional pro finish: the green sister stands in the middle. The middle placement matches the legend."] ,"time":"35 min + drying","cost":"$13-25","effort":"Easy","sizing":"Built for teens and adults. Dresses in each sister\u2019s size; the hat elastic fits most heads.","safelink":null,"faqs":[["How do you keep three thrifted dresses looking like a set?","Matching hats and tights unify any three dresses. The accessories do the grouping, not the dresses."],["Can two people do this instead of three?","Two works, but the trio is the iconic number. Recruit a third; the spell needs three."]]},
  "macabre-couple":{"m":["Long black dress or gown, 1 (buy: thrift store)","Black wig or black hair dye, 1 (buy: costume aisle)","Pale foundation, 1 (buy: drugstore)","Dark lipstick, 1 (own)","Black pinstripe or plain suit, 1 (buy: thrift store)","White shirt, 1 (own)","Black tie or cravat, 1 (buy: thrift store)"],"s":["She wears the long black gown with pale makeup and dark lips; he wears the suit with a stern expression.","Style the hair severe: slicked back for him, straight and long for her.","Walk arm in arm and speak as little as possible.","Safety: test all makeup on a wrist first, and remove it fully before bed.","Never smile in photos. The unsmiling portrait is the entire aesthetic.","Optional pro finish: one shared prop, a black rose. The rose gives your hands something to do."] ,"time":"30 min","cost":"$15-28","effort":"Easy","sizing":"Built for teens and adults. Size the mourning clothes to each wearer; veils and cravats tie to fit.","safelink":null,"faqs":[["How do you keep the look elegant instead of sloppy?","Fit matters more than fabric: tailor the thrifted pieces or pin them to fit. Sharp lines read expensive."],["What if the gown is too long?","Hem it to ankle length with iron-on tape. Floor-length gowns trip on stairs."]]},
  "party-pinata":{"m":["Cardboard box, 1 large (make: from a shipping box)","Crepe paper in rainbow colors, 6 rolls (buy: dollar store)","Wrapped candy, 2 bags (buy: grocery store)","String for hanging strips, 1 roll (own)","Tape, 1 roll","Scissors, 1 pair"],"s":["Cut fringe strips from the crepe paper and glue them in overlapping rows over the whole box.","Cut arm and head holes in the box, with the opening at the bottom for candy.","Fill the box with wrapped candy before sealing the bottom flap loosely.","Safety: keep the head hole generous so vision and breathing stay easy, and use only wrapped candy.","Hand out candy from inside the costume all night. The giving is the costume.","Optional pro finish: let kids pull one candy each from the bottom flap. You become the party game."] ,"time":"40 min + drying","cost":"$20-22","effort":"Medium","sizing":"Built for teens and adults. The tunic fits most; cut the fringe strips to your torso length.","safelink":null,"faqs":[["How do you keep the fringe from tearing?","Glue each fringe row at the top edge only, overlapping downward. Rows glued flat across tear when you move."],["Will the box survive the whole party?","Double-wall cardboard survives a night. Single-ply boxes crush by midnight."]]},
  "fuzzy-gremlin":{"m":["Brown fuzzy onesie or footed pajamas, 1 (buy: thrift store or online)","Brown craft felt, 2 sheets 9x12 inches (buy: craft store)","Large googly eyes, 2 (buy: craft store)","White felt for teeth, 1 small piece (buy: craft store)","Fabric glue, 1 bottle (buy: craft store)","Safety pins, 4 (buy: dollar store)","Scissors, 1 pair"],"s":["Cut two big round ears from the brown felt and glue them to the onesie hood.","Glue the googly eyes to the forehead of the hood, above the face opening.","Glue two small white felt triangles under the hood edge as teeth.","Safety: glue the eyes to the hood, never near the child's face, and keep all small parts where little hands cannot pull them off.","Optional pro finish: carry the gremlin in a laundry basket for arrivals. The unboxing gets the biggest reaction."] ,"time":"25 min + drying","cost":"$22-31","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Use a fuzzy onesie in the wearer's actual size; the ear headband adjusts.","safelink":null,"faqs":[["How do you keep the big ears from flopping?","Glue each ear to a cardboard circle first, then glue the circles to the hood. The cardboard is the skeleton."],["What if the onesie is not fuzzy?","A brown sweatsuit works. The ears and eyes carry the costume, not the fabric texture."]]},
  "rescue-pups":{"m":["T-shirts in assigned colors, 1 per kid (own, or buy: thrift store)","Felt for pup badges, 1 sheet per color (buy: craft store)","Headbands, 1 per kid (buy: dollar store)","Brown felt for ears, 1 sheet per kid (buy: craft store)","Fabric glue, 1 bottle (buy: craft store)","Safety pins, 4 per kid (buy: dollar store)","Scissors, 1 pair"],"s":["Assign each kid a color and a matching felt badge shape.","Cut pup ears from the brown felt and glue them to each headband.","Glue the badge to the front of each colored shirt.","Safety: pin badges from inside the shirts, and keep headbands loose enough to slip two fingers underneath.","Line the pups up by color for the team photo.","Optional pro finish: give each pup a toy tool matching their badge. The props make the roles obvious."] ,"time":"30 min + drying","cost":"$9-11","effort":"Easy","sizing":"Built for kids ages 3 to 8. Vests in each child\u2019s size; pup-ear headbands fit most kids.","safelink":null,"faqs":[["How do you handle a kid who will not wear the headband?","Glue the ears to the shirt collar instead. Ears on the shoulders still read as pup."],["What if the kids argue over colors?","Assign colors by drawing from a hat. The draw itself becomes part of the game."]]},
  "wayfinder-princess":{"m":["Tan or brown tank top, 1 (own, or buy: thrift store)","Crepe paper or raffia for the skirt, 2 rolls (buy: craft store)","Cardboard for the hook, 1 sheet (make: from a shipping box)","Brown paint, 1 bottle (buy: craft store)","Shell necklace, 1 (buy: dollar store, or make: from pasta shells and string)","Fabric glue, 1 bottle (buy: craft store)","Scissors, 1 pair"],"s":["Cut the crepe paper into long strips and tie them around an elastic waistband for the skirt.","Paint a spiral design on the tank top with the brown paint.","Cut the hook shape from cardboard and paint it brown.","Wear the shell necklace and carry the cardboard hook.","Safety: keep the hook cardboard and light, never swung near faces, and round all edges.","Optional pro finish: practice one confident stance with the hook raised. The stance is the character."] ,"time":"35 min + drying","cost":"$7-9","effort":"Easy","sizing":"One per person, so kids and adults each get a real fit. Dress in the wearer's size; cut the paddle to their height.","safelink":null,"faqs":[["How do you keep the paper skirt from tearing?","Tie each strip separately rather than gluing a sheet. Separate strips move and survive sitting."],["What if the hook is too big to carry?","Scale it to forearm length. A smaller hook carried confidently beats a big one left at home."]]},
  "chill-painter":{"m":["Big brown afro wig, 1 (buy: costume aisle or online)","Denim shirt, 1 (own, or buy: thrift store)","Jeans, 1 (own)","Cardboard for the palette, 1 sheet (make: from a shipping box)","Acrylic paints in bright colors, 1 set (buy: craft store)","Toy paintbrush, 1 (buy: dollar store)","Scissors, 1 pair"],"s":["Cut a palette shape from the cardboard with a thumb hole.","Dab the bright paints onto the palette and let it dry completely.","Wear the denim shirt and jeans with the afro wig.","Carry the palette and brush everywhere, and narrate happy little details about the party.","Safety: let the palette dry fully before the party so wet paint never touches clothes or furniture.","Optional pro finish: compliment one thing about every costume you see, in character. The kindness is the performance."] ,"time":"20 min + drying","cost":"$14-18","effort":"Easy","sizing":"Built for teens and adults. The wig is one-size with an adjustable strap; the apron ties to fit.","safelink":null,"faqs":[["How do you keep the wig on all night?","Wear a wig cap underneath and pin the wig at four points. Afro wigs are top-heavy and slide without pins."],["What if the palette paint is still tacky?","Paint it the night before. Acrylic on cardboard needs hours, not minutes, to cure fully."]]}
};/* ================= MAKE PLANS =================
   "Make it this week" data: what to buy, est. cost/time, 3-5 steps.
   Generated in make-plans.js (same directory); inlined here so the
   site stays single-file. If make-plans.js is regenerated, re-inline it.
   2026-09-25: the concrete post-pick plan. */
var MAKE_PLANS = {
  "neon-demon-hunter": {buy: ["Neon fabric paint pens", "Foam sword", "Black eyeliner"], cost: "~$19", time: "~1 hr", steps: ["Paint glowing sigils on black clothes with the fabric pens.", "Tease hair big and add bold eyeliner and dark lipstick.", "Let the paint dry 20 minutes, then strap on the foam sword."]},
  "classic-ghost": {buy: ["White flat bed sheet (thrifted)"], cost: "~$4", time: "~20 min", steps: ["Drape the sheet and mark the eye spots with a pencil.", "Cut two eye holes, starting small and widening.", "Trim the bottom so it clears the ground."]},
  "blue-dog-family": {buy: ["Felt sheets (blue and orange)", "Plain headbands", "Blue and orange tees"], cost: "~$5", time: "~45 min", steps: ["Cut two triangle ears from felt per person.", "Hot-glue the ears to headbands.", "Pair with blue or orange shirts.", "Draw noses and whiskers with eyeliner."]},
  "superhero-family": {buy: ["Red sweatsuits", "Black felt", "Elastic cord"], cost: "~$1 each", time: "~1 hr", steps: ["Cut a bolt or star logo from black felt per suit.", "Glue each logo to a chest.", "Cut eye masks from felt and thread elastic through.", "Suit up and strike the team pose."]},
  "blue-alien-ohana": {buy: ["Blue pipe cleaners", "Blue pom-poms", "Headbands", "Red t-shirt or dress (closet, or thrift)", "White felt or paper"], cost: "~$14", time: "~35 min", steps: ["Alien: twist two blue pipe cleaners around a headband so they stand up, and tape a blue pom-pom to each tip.", "Wear with a blue hoodie; add big black oval eyes with eyeliner.", "Lilo: cut leaf shapes from white felt or paper and pin or glue them across a red t-shirt or dress.", "Wear dark hair down. The alien and Lilo make the ohana."]},
  "emerald-witch": {buy: ["Green dress (thrifted)", "Black poster board", "Green face paint", "False lashes"], cost: "~$29", time: "~1.5 hrs", steps: ["Roll poster board into a tall cone and tape the seam.", "Paint your face, then add black eyeliner and dark lips.", "Stick on the false lashes.", "Wear the dress and tilt the hat."]},
  "gloom-bloom": {buy: ["Black clothes (closet)", "Bright accessories", "Face paint"], cost: "~$5 each", time: "~45 min", steps: ["Gloom: braid hair tight, wear all black, paint a frown.", "Bloom: wear your brightest colors and add flower clips.", "Pose back to back for the full contrast."]},
  "deadpan-diva": {buy: ["Pale foundation", "Black lipstick"], cost: "~$7", time: "~40 min", steps: ["Part hair down the middle and braid two tight braids.", "Apply foundation a few shades lighter than your skin.", "Finish with black lipstick and heavy eyeliner.", "Practice the stare that ends conversations."]},
  "safari-zoo-crew": {buy: ["Felt sheets in animal colors", "Headbands", "Face paint"], cost: "~$3 each", time: "~1 hr", steps: ["Each person picks an animal and a matching closet outfit.", "Cut ears from felt and glue to headbands.", "Paint noses and whiskers.", "Do a group animal parade."]},
  "fairy-tale-princesses": {buy: ["Gold poster board", "Plastic gems"], cost: "~$10", time: "15 min + drying", steps: ["Cut a crown band from gold poster board and tape to fit.", "Glue on the plastic gems.", "Pair with the fanciest dress in the closet.", "Royal wave is mandatory."]},
  "tin-hero": {buy: ["Red shirt and pants", "Gold duct tape", "Battery tea light"], cost: "~$8", time: "~45 min", steps: ["Stripe the shirt and pants with the tape.", "Cover a cardboard circle in tape and fix a tea light behind it.", "Pin the glowing circle to your chest.", "Walk like the suit does the talking."]},
  "good-witch-bad-witch": {buy: ["Green face paint", "Pink dress (thrifted)", "Gold poster board", "Black clothes"], cost: "~$5 each", time: "~1 hr", steps: ["Bad witch: paint face green and wear all black with a pointy hat.", "Good witch: wear the pink gown and a poster-board crown.", "Arrive together for maximum effect."]},
  "fuzzy-monster": {buy: ["Pastel sweatsuit", "Jumbo googly eyes", "Black felt"], cost: "~$21", time: "~45 min", steps: ["Glue jumbo googly eyes to the hood.", "Cut a big smile from black felt and glue it below.", "Add felt stitches around the smile with a white paint pen."]},
  "pocket-plush": {buy: ["Fuzzy one-piece or sweatsuit", "Felt for ears", "Cardboard tag", "String"], cost: "~$7", time: "~45 min", steps: ["Cut big round ears from felt and glue to the hood.", "Draw a stitched smile with a paint pen.", "Write a collector number on the cardboard tag.", "Hang the tag from your wrist with string."]},
  "soccer-squad": {buy: ["Red cardstock", "Whistle"], cost: "~$1 each", time: "~20 min", steps: ["Players wear their own jerseys.", "The ref wears black with the whistle.", "Cut a red card from the cardstock.", "Brandish the red card at dramatic moments."]},
  "glow-skeleton": {buy: ["Glow-in-the-dark tape", "Glow bracelets", "Black sweats"], cost: "~$18", time: "~45 min", steps: ["Cut tape into rib shapes and stick down the front of black sweats.", "Add spine and limb bones with more tape strips.", "Charge under a lamp, then snap on glow bracelets.", "Turn off the lights to test."]},
  "block-game-crew": {buy: ["Cardboard boxes (one per person)", "Acrylic paint set"], cost: "~$10", time: "~1.5 hrs", steps: ["Cut eye and mouth holes in each box.", "Paint each box as your blocky hero.", "Let dry, then wear over your head.", "Move in chunky square steps."]},
  "web-slinger-crew": {buy: ["Red, black, or pink hoodies (closet)", "Black eyeliner"], cost: "~$2 each", time: "~30 min", steps: ["Each person picks red, black, or pink.", "Paint web lines fanning from the eyes with eyeliner.", "Strike a wall-crawling pose for photos."]},
  "mermaid-crew": {buy: ["Shiny fabric or scarves", "Seashell accessories", "Face paint"], cost: "~$4 each", time: "~1 hr", steps: ["Assign roles: mermaid, prince, sea king, sea witch, crab.", "Mermaid wraps shiny fabric as a tail skirt.", "Crab wears red with claw mittens.", "Sea witch adds dark makeup and a shell crown."]},
  "little-pig-family": {buy: ["Pink felt", "Headbands", "Toy dinosaur"], cost: "~$12", time: "~30 min", steps: ["Cut snouts and round ears from pink felt.", "Glue them to headbands.", "Dress in pink clothes.", "Hand little brother the toy dinosaur."]},
  "enchanted-castle-crew": {buy: ["Gold poster board", "LED tea lights", "Face paint"], cost: "~$6 each", time: "~1 hr", steps: ["Assign the five roles.", "Candelabra: tape tea lights to a gold headband.", "Clock and teapot: paint cardboard fronts.", "Princess and prince dress fancy from the closet."]},
  "bumble-bee": {buy: ["Yellow duct tape", "Black headband", "Yellow felt", "Pipe cleaners"], cost: "~$19", time: "~30 min", steps: ["Wrap yellow tape stripes around black sweats.", "Glue felt balls to pipe cleaners for antennae.", "Attach the antennae to the headband.", "Buzz everywhere you go."]},
  "baby-dino": {buy: ["Green hoodie", "Green felt", "Polyfill stuffing"], cost: "~$7", time: "~1 hr", steps: ["Cut triangles from green felt for back spikes.", "Glue the spikes down the back of the hoodie.", "Sew or glue a stuffed felt tail to the back.", "Roar at everyone."]},
  "little-lion": {buy: ["Tan sweatsuit", "Brown fuzzy fabric", "Elastic"], cost: "~$13", time: "~1 hr", steps: ["Cut a large circle of fuzzy brown fabric.", "Cut a face hole and fringe the edge into a mane.", "Wear it over the tan hood.", "Add whiskers with eyeliner."]},
  "tiny-firefighter": {buy: ["Plastic firefighter helmet", "Toy hose or rope", "Yellow reflective tape"], cost: "~$10", time: "~20 min", steps: ["Dress in red sweats.", "Add reflective tape stripes.", "Put on the helmet.", "Carry the hose over your shoulder."]},
  "little-shark": {buy: ["Gray hoodie", "Gray felt"], cost: "~$6", time: "~30 min", steps: ["Cut a tall triangle fin from gray felt.", "Glue the fin to the back of the hoodie.", "Draw gills on the sleeves with a marker.", "Chomp when you walk."]},
  "walking-taco": {buy: ["Tan vest or tan felt", "Felt sheets (green, red, yellow)", "Fabric paint"], cost: "~$6", time: "~1 hr", steps: ["Paint the tan vest with shell texture lines.", "Cut lettuce, tomato, and cheese shapes from felt.", "Glue the toppings along the vest top edge.", "Serve with a smile."]},
  "ramen-bowl": {buy: ["Yellow yarn", "White craft foam", "Cardboard"], cost: "~$6", time: "~45 min", steps: ["Cut a wide cardboard ring and paint it like a bowl rim.", "Glue wavy yellow yarn all over a swim cap for noodles.", "Cut a foam egg half and glue it on top.", "Wear the rim around your shoulders."]},
  "tiny-snail": {buy: ["Large cardboard", "Paint", "Ribbon for straps"], cost: "~$8", time: "~1 hr", steps: ["Cut a big spiral from cardboard.", "Paint it in swirls.", "Tape ribbon straps to the back.", "Wear it like a backpack and move slowly."]},
  "little-witch": {buy: ["Black fabric for cape", "Poster board", "Striped tights", "Green face paint"], cost: "~$20", time: "~45 min", steps: ["Cut a cape from black fabric and tie it at the neck.", "Roll poster board into a cone hat.", "Paint the face green.", "Pull on striped tights and cackle."]},
  "spider": {buy: ["4 pairs black socks", "Polyfill stuffing", "Black sweats"], cost: "~$22", time: "~45 min", steps: ["Stuff 8 socks with polyfill for legs.", "Sew or safety-pin 4 legs to each side of the sweats.", "Pose the legs outward.", "Crawl, do not walk."]},
  "backyard-hero": {buy: ["Fabric for cape", "Felt letter", "Velcro dots"], cost: "~$2", time: "~30 min", steps: ["Cut a short cape and attach it with velcro.", "Glue your felt initial to your shirt.", "Cut a simple eye mask from felt.", "Name your heroic alter ego."]},
  "pickle": {buy: ["Green tunic or oversized tee", "Green pom-poms", "Green face paint"], cost: "~$13", time: "~40 min", steps: ["Glue the pom-poms all over the tunic for bumps.", "Paint your face.", "Draw a smug grin.", "Act superior to all other foods."]},
  "vampire": {buy: ["Plastic fangs", "Black cape", "Hair gel", "Pale foundation"], cost: "~$18", time: "~30 min", steps: ["Slick hair back with gel.", "Apply pale foundation.", "Pop in the fangs.", "Drape the cape and avoid garlic."]},
  "bamboo-demon": {buy: ["Pink robe (thrifted)", "Long black wig", "Cardboard", "Ribbon"], cost: "~$23", time: "~45 min", steps: ["Cut a bamboo tube shape from cardboard and paint it tan.", "Tie it over your mouth with ribbon around your head.", "Put on the wig and pink robe.", "Stare intensely and say nothing."]},
  "emoji-crew": {buy: ["Yellow tees", "Printer paper", "Markers"], cost: "~$1 each", time: "~30 min", steps: ["Each person picks an emoji.", "Draw the giant face on paper.", "Tape or pin it to the yellow tee.", "Only communicate in emoji all night."]},
  "robot-crew": {buy: ["Cardboard boxes", "Aluminum foil", "Bottle caps", "Silver paint"], cost: "~$4 each", time: "~1.5 hrs", steps: ["Cover the boxes in foil for each robot body.", "Glue bottle caps on as buttons and dials.", "Cut arm and head holes.", "Move and talk like a robot."]},
  "cereal-crew": {buy: ["Empty cereal boxes", "Markers", "String"], cost: "~$1 each", time: "~30 min", steps: ["Each person picks a cereal.", "Decorate the box front with the name and art.", "Punch holes and string it like a sandwich board.", "Wear over solid-color clothes."]},
  "decades-crew": {buy: ["Thrift-store accessories (optional)"], cost: "~$1 each", time: "~30 min", steps: ["Each person claims a decade.", "Raid closets and thrift racks for the look.", "Add one era-defining accessory.", "Pose in chronological order."]},
  "under-the-sea": {buy: ["Clear umbrella", "Ribbon", "Red mittens", "Blue and green crepe paper"], cost: "~$3 each", time: "~1 hr", steps: ["Jellyfish: tape ribbon tentacles inside the umbrella.", "Crab: wear red and tape claws to red mittens.", "Fish and seaweed: dress in blue and green with crepe-paper fins.", "Move like you are underwater."]},
  "dino-rangers": {buy: ["Dino hoods or hats", "Toy raptor", "Rope leash"], cost: "~$2 each", time: "~30 min", steps: ["Grown-ups wear khaki outfits.", "Kids wear dino hoods.", "Tie the leash to the toy raptor.", "March the neighborhood on dino patrol."]},
  "board-game-pieces": {buy: ["Poster board", "Paint markers"], cost: "~$3 each", time: "~1 hr", steps: ["Each person picks a game piece.", "Build it large from poster board.", "Wear over monochrome clothes.", "Stand in a row like a game shelf."]},
  "rain-cloud-rainbow": {buy: ["Cotton balls", "Blue paper", "Rainbow accessories"], cost: "~$6 each", time: "~45 min", steps: ["Cloud: glue cotton balls to a gray shirt.", "Hang paper raindrops from the cotton with string.", "Rainbow: wear every bright color you own in stripes.", "Stay close together all night."]},
  "doctor-bride": {buy: ["Green face paint", "Silver bottle caps", "White wig", "Thrifted gown"], cost: "~$12 each", time: "~1 hr", steps: ["Doctor: paint face green and glue bottle-cap bolts to your neck.", "Bride: tease the wig tall with white streaks.", "Tear the gown hem for the lab-accident look.", "Lurch, do not walk."]},
  "breakfast-buffet": {buy: ["Poster board", "Markers", "String"], cost: "~$0 each", time: "~30 min", steps: ["Each person picks a breakfast item.", "Draw it big on poster board.", "Hang as a sandwich board with string.", "Line up as the full buffet."]},
  "ghost-hunters": {buy: ["Name patch stickers", "Small cardboard boxes", "Dryer vent hose (toy)"], cost: "~$6 each", time: "~1 hr", steps: ["Wear khaki or tan outfits.", "Build backpacks from the small boxes.", "Attach the hose as your ghost vacuum.", "Add name patches. Do not cross the streams."]},
  "haunted-animatronics": {buy: ["Cardboard boxes", "LED tea lights", "Paint"], cost: "~$4 each", time: "~1.5 hrs", steps: ["Paint each box as a creepy mascot face.", "Cut eye holes and mount tea lights behind them.", "Wear the box heads.", "Move in jerks and freeze mid-step."]},
  "mystery-crew": {buy: ["Colored accessories per role", "Dog bandana"], cost: "~$3 each", time: "15 min + drying", steps: ["Assign the five roles.", "Leader gets the ascot, brains gets the glasses.", "Goofball wears the silliest hat.", "Put the bandana on the very good dog.", "Travel everywhere in the same order."]},
  "headless-horsemen": {buy: ["Black fabric for capes", "Plastic pumpkins", "LED tea lights"], cost: "~$2 each", time: "~45 min", steps: ["Cut black capes and wear them high at the neck.", "Put tea lights inside the plastic pumpkins.", "Hold a pumpkin at shoulder height.", "Gallop everywhere in formation."]},
  "haunted-portraits": {buy: ["Gray face paint", "Gold spray paint", "Foam board"], cost: "~$3 each", time: "~1 hr", steps: ["Spray-paint foam board gold and cut out the center for frames.", "Paint faces gray with dark hollow eyes.", "Wear your oldest, fanciest clothes.", "Hold the frame and never blink."]},
  "goggle-crew": {buy: ["Yellow tees", "Swim goggles or safety glasses", "Black gloves"], cost: "~$2 each", time: "~20 min", steps: ["Wear yellow tees with denim overalls.", "Put on the goggles.", "Add black gloves.", "Speak only in excited gibberish."]},
  "garden-gnome": {buy: ["Cardboard", "White face paint", "Toy fishing rod"], cost: "~$19", time: "~40 min", steps: ["Cut and tape a tall pointy hat from cardboard.", "Paint a white beard on your chin.", "Wear earth-tone layers with a belt.", "Carry the tiny rod and guard the garden."]},
  "black-cat": {buy: ["Cat-ear headband", "Black eye mask", "Drawstring bag"], cost: "~$15", time: "~20 min", steps: ["Wear a black sweatsuit.", "Put on the ears and eye mask.", "Draw whiskers with eyeliner.", "Sling the sack over your shoulder for the burglar twist."]},
  "block-monster": {buy: ["Foam blocks or small boxes", "Face paint"], cost: "~$13", time: "~45 min", steps: ["Wear one solid color head to toe.", "Tape foam blocks to shoulders, elbows, and knees.", "Draw a pixelated face with square blocks of paint.", "Move in right angles only."]},
  "space-crewmate": {buy: ["Cardboard box", "Colored duct tape"], cost: "~$0", time: "~30 min", steps: ["Wear a bright solid sweatsuit.", "Tape the box shut and decorate it with duct-tape details.", "Strap it on as a backpack.", "Call emergency meetings and act suspicious."]},
  "sun-moon": {buy: ["Yellow poster board", "Gold paint", "Glow-in-the-dark stars"], cost: "~$6 each", time: "~45 min", steps: ["Sun: cut triangle rays and glue them around a yellow shirt.", "Moon: stick glow stars on navy clothes.", "Cut a big crescent from poster board for the moon.", "Rise and set together."]},
  "moth-porch-light": {buy: ["Cardboard", "Lampshade (thrifted)", "Tan paint"], cost: "~$6 each", time: "~45 min", steps: ["Moth: cut big wings from cardboard and paint them dusty tan.", "Strap the wings on with ribbon.", "Porch light: wear yellow and carry the lampshade.", "Moth, orbit the light all night."]},
  "raptor-ranger": {buy: ["Dino hood or hat", "Toy dinosaur", "Rope leash"], cost: "~$7 each", time: "~20 min", steps: ["Ranger wears khaki with a hat.", "Partner wears the dino hood.", "Tie the rope to the toy dino.", "Ranger leads, raptor lunges."]},
  "cat-mouse": {buy: ["Cat-ear headband", "Mouse-ear headband"], cost: "~$7 each", time: "~15 min", steps: ["One wears cat ears, the other mouse ears.", "Add whiskers to both.", "Spend the night chasing each other.", "Mouse always escapes at the last second."]},
  "ketchup-mustard": {buy: ["Red and yellow fabric or felt", "Poster board for caps"], cost: "~$1 each", time: "~1 hr", steps: ["Cut tunic shapes from red and yellow fabric.", "Write the labels in big letters.", "Make matching caps from poster board.", "Stick together like condiments."]},
  "plumber-duo": {buy: ["Red and green caps", "Fake mustaches or eyeliner"], cost: "~$22 each", time: "15 min + drying", steps: ["Wear overalls over red and green shirts.", "Add the matching caps.", "Draw big mustaches.", "Jump on imaginary turtles."]},
  "office-couple": {buy: ["Name tag stickers", "Toy teapot"], cost: "~$0 each", time: "~15 min", steps: ["Wear white button-downs.", "Write absurd job titles on the name tags.", "One of you carries the teapot everywhere.", "Discuss synergy loudly."]},
  "burger-joint-couple": {buy: ["White apron", "Fake mustache", "Curly red wig", "Costume glasses"], cost: "~$15 each", time: "~20 min", steps: ["One wears the apron and mustache.", "The other wears the red wig and glasses.", "Take everyone's order.", "Argue about the secret sauce."]},
  "plug-socket": {buy: ["Cardboard", "Black and white paint"], cost: "~$1 each", time: "~45 min", steps: ["Cut a big plug shape and a big outlet shape from cardboard.", "Paint them black and white.", "One wears the plug front and back, the other the outlet.", "Stay connected all night."]},
  "the-olympians": {buy: ["Gold rope or cord", "Green paper for laurels", "Bedsheets (closet)"], cost: "~$3 each", time: "~45 min", steps: ["Drape bedsheets as togas and pin at the shoulder.", "Tie gold rope as belts.", "Twist paper leaves into laurel crowns.", "Each god picks a prop: bolt, owl, or trident."]},
  "lost-tourist": {buy: ["Printed paper map", "Luggage tag"], cost: "~$0", time: "~15 min", steps: ["Wear your most wrinkled clothes.", "Crumple the map and carry it upside down.", "Hang the luggage tag backwards on your shoulder.", "Ask everyone for directions."]},
  "tooth-fairy": {buy: ["White poster board", "Fairy wings", "Play money"], cost: "~$4 each", time: "~30 min", steps: ["Tooth: cut a giant tooth outline and wear it.", "Fairy: wear all white with wings.", "Carry the envelope of tooth money.", "Collect teeth (candy) from strangers."]},
  "web-hero-duo": {buy: ["Web mask or black eyeliner", "Black jacket (closet)"], cost: "~$4 each", time: "~20 min", steps: ["Hero wears red-blue with a web mask.", "Partner wears the black jacket.", "Strike hero and anti-hero poses.", "Argue about responsibility."]},
  "plague-doctor": {buy: ["Beaked mask (costume shop)", "Wide-brim hat", "Long black coat (thrifted)"], cost: "~$35", time: "~30 min", steps: ["Buy or order the beaked mask early.", "Wear the long coat buttoned up.", "Add the wide hat and gloves.", "Carry a staff and speak ominously."]},
  "crowd-camouflage": {buy: ["Gray hoodie (closet)"], cost: "~$2", time: "~5 min", steps: ["Wear a gray hoodie and dark pants.", "Keep your expression completely blank.", "Stand near groups and blend in.", "Vanish when noticed."]},
  "error-404": {buy: ["White paper and tape", "Old phone case"], cost: "~$0", time: "~10 min", steps: ["Wear all black.", "Tape a blank white page to your chest.", "Crack an old screen protector for the prop phone.", "Freeze whenever someone talks to you."]},
  "zombie-coworker": {buy: ["Pale foundation", "Fake blood (optional)"], cost: "~$9", time: "~30 min", steps: ["Rip the collar and cuffs of an old button-down.", "Loosen the tie and smear on pale makeup.", "Add dark circles under your eyes.", "Clutch the coffee mug and moan about Mondays."]},
  "safari-photographer": {buy: ["Toy camera", "Toy binoculars", "Stuffed lion"], cost: "~$9", time: "~20 min", steps: ["Wear khaki layers with lots of pockets.", "Hang the camera and binoculars around your neck.", "Tuck the lion cub under one arm.", "Photograph everything, especially people."]},
  "player-one-two": {buy: ["Two plain tees", "Fabric markers", "Toy controllers"], cost: "~$2 each", time: "~30 min", steps: ["Write big 1 and 2 on the tees.", "Each carry a toy controller.", "Narrate your co-op moves.", "Blame player two for everything."]},
  "dinosaur-family": {buy: ["Green hoodies (one per person)", "Green felt"], cost: "~$3 each", time: "~1 hr", steps: ["Get green hoodies for everyone.", "Cut felt triangles for spikes.", "Glue spikes down every back.", "Stomp through the neighborhood as a herd."]},
  "snow-sisters": {buy: ["Blue and white fabric", "Snowflake stickers", "Carrot nose prop", "Antler headband"], cost: "~$14", time: "~1.5 hrs", steps: ["Assign the four roles.", "Ice queen: blue dress with snowflake stickers.", "Snowman: white clothes with black button dots and a carrot nose.", "Reindeer: brown clothes with the antler headband."]},
  "sushi-roll": {buy: ["White twin sheet", "Orange and green felt", "Pom-poms"], cost: "~$11", time: "~45 min", steps: ["Wrap the white sheet around you like a roll.", "Glue orange felt salmon strips around the middle.", "Stick green pom-pom wasabi on top.", "Carry chopsticks."]},
  "deviled-egg": {buy: ["Yellow felt", "Devil horn headband", "Red ribbon for tail"], cost: "~$17", time: "~30 min", steps: ["Cut a big yolk circle from yellow felt and pin it on.", "Put on the devil horns.", "Attach the red tail.", "Be half angel, half menace."]},
  "pizza-slice": {buy: ["Large cardboard", "Yellow and red paint", "Red felt"], cost: "~$6", time: "~1 hr", steps: ["Cut a giant triangle from cardboard.", "Paint it golden brown.", "Glue red felt pepperoni circles on.", "Wear it with straps like a sandwich board."]},
  "popcorn-bucket": {buy: ["Cardboard box", "Red and white paint", "White and yellow balloons"], cost: "~$6", time: "~1 hr", steps: ["Paint the box in stripes.", "Blow up small balloons in both colors.", "Glue the balloons spilling out of the top.", "Wear the box with arm holes cut."]},
  "ice-cream-cone": {buy: ["Tan poster board", "Colorful dot stickers", "White or pink shirt"], cost: "~$7", time: "~30 min", steps: ["Roll tan poster board into a big cone hat.", "Cover the shirt in dot stickers as sprinkles.", "Wear the cone on your head.", "Try not to melt."]},
  "pbj": {buy: ["Brown and purple tees", "Paper labels", "Markers"], cost: "~$2 each", time: "~20 min", steps: ["Write PB and J labels in big letters.", "Pin the labels to the brown and purple tees.", "Stick together.", "You are better together."]},
  "bacon-eggs": {buy: ["Red and white felt", "Yellow felt", "White shirt"], cost: "~$2 each", time: "~30 min", steps: ["Bacon: cut wavy stripes with fat lines.", "Eggs: glue a yolk onto the shirt.", "Wear and sizzle.", "Serve yourselves."]},
  "peas-pod": {buy: ["Green shirts", "Long green felt strip"], cost: "~$5 each", time: "~30 min", steps: ["Everyone wears green.", "Cut pea circles and pin them to each shirt.", "Drape the long felt pod sash over the row.", "Stay in pod formation."]},
  "basketball-star": {buy: ["Eye black stickers", "Basketball (borrow one)"], cost: "~$4", time: "~10 min", steps: ["Wear a jersey and shorts.", "Stick eye-black stripes under your eyes.", "Carry the ball everywhere.", "Never pass."]},
  "referee": {buy: ["Striped shirt", "Whistle", "Yellow fabric for flag"], cost: "~$5", time: "~15 min", steps: ["Wear the striped shirt.", "Hang the whistle around your neck.", "Keep the penalty flag in your pocket.", "Throw flags at bad behavior."]},
  "boxer": {buy: ["Toy boxing gloves", "Bruise makeup wheel"], cost: "~$13", time: "~25 min", steps: ["Wear a bathrobe over workout clothes.", "Add bruise makeup to one cheek.", "Pull on the toy gloves.", "Enter every room to your theme music."]},
  "cheerleader": {buy: ["Plastic bags in team colors", "Rubber bands"], cost: "~$3", time: "~20 min", steps: ["Cut plastic bags into long strips.", "Bunch and band them into pom-poms.", "Wear team colors.", "Lead a cheer for everything."]},
  "tennis-duo": {buy: ["Toy rackets", "Tennis balls", "White headbands"], cost: "~$8 each", time: "~15 min", steps: ["Dress head to toe in white.", "Add headbands and wristbands.", "Carry the rackets and ball tube.", "Shout the score after everything."]},
  "bowling-pins": {buy: ["Red tape or ribbon", "Black outfit for the bowler"], cost: "~$2 each", time: "~20 min", steps: ["Pins wear white with red stripes at the neck.", "One bowler wears all black.", "Line up the pins.", "Bowler charges, pins scatter."]},
  "cardboard-knight": {buy: ["Cardboard", "Silver spray paint", "Pool noodle"], cost: "~$13", time: "~1.5 hrs", steps: ["Cut a chest plate and arm guards from cardboard.", "Spray-paint everything silver.", "Cut the pool noodle into a sword.", "Kneel for your knighting."]},
  "ninja": {buy: ["Black fabric strip", "Black belt or sash"], cost: "~$0", time: "~20 min", steps: ["Dress in all black.", "Tie the sash around your waist.", "Cut eye slits in the fabric strip for a headband.", "Move silently."]},
  "caped-duo": {buy: ["Old sheet", "Felt for masks and emblems"], cost: "~$3 each", time: "~45 min", steps: ["Cut two capes from the sheet.", "Cut matching felt masks.", "Design your own emblems from felt.", "Glue the emblems on and take flight."]},
  "hero-squad": {buy: ["Colored fabric or old sheets", "Felt for masks"], cost: "~$4 each", time: "~1 hr", steps: ["Each hero picks a color.", "Cut a cape and mask per hero.", "Add a felt emblem.", "Assemble for the team pose photo."]},
  "astronaut": {buy: ["Large paper bag", "Flag patch or printout"], cost: "~$9", time: "~30 min", steps: ["Cut a face window in the paper bag.", "Decorate it with markers and the flag patch.", "Wear white sweats.", "Take small steps for mankind."]},
  "robot-ranger": {buy: ["Cardboard boxes", "Silver spray paint", "Stickers"], cost: "~$18", time: "~1.5 hrs", steps: ["Spray-paint the boxes silver.", "Attach dryer-vent arms with tape.", "Stick dials and buttons on the chest.", "Beep when you talk."]},
  "penguin-huddle": {buy: ["White and orange felt", "Headbands"], cost: "~$2 each", time: "~45 min", steps: ["Cut white felt bellies and pin them to black shirts.", "Make orange beak headbands.", "Waddle everywhere together.", "Huddle when it gets cold."]},
  "prince-princess": {buy: ["Gold poster board", "Tiara", "Thrifted gown", "Cape fabric"], cost: "~$11 each", time: "~30 min", steps: ["Cut a crown from gold poster board.", "Prince wears the cape.", "Princess wears the gown and tiara.", "Bow and curtsy to everyone."]},
  "dino-herd": {buy: ["Green ponchos or green fabric", "Green felt", "Socks and stuffing"], cost: "~$3 each", time: "~1 hr", steps: ["Everyone wears a poncho.", "Glue spikes down each back.", "Stuff socks for tails and pin them on.", "Migrate as a herd."]},
  "pixel-ghost": {buy: ["White sheet (thrifted)", "Black felt"], cost: "~$8", time: "~30 min", steps: ["Cut the sheet bottom into chunky squares.", "Cut square eyes from black felt.", "Glue the eyes on.", "Float in 8-bit."]},
  "spaghetti-meatball": {buy: ["Yellow yarn", "Brown pom-poms"], cost: "~$11", time: "~30 min", steps: ["Glue wavy yellow yarn all over a white shirt.", "Glue brown pom-poms on as meatballs.", "Wear a chef hat if you have one.", "Serve yourself."]},
  "cupcake": {buy: ["Brown tunic or brown paper", "White pillowcase", "Red balloon or pom-pom"], cost: "~$7", time: "15 min + drying", steps: ["Wear the brown tunic as the wrapper.", "Drape the pillowcase as frosting.", "Put the red cherry on your head.", "Be the sweetest thing there."]},
  "banana": {buy: ["Yellow sweatsuit", "Green felt"], cost: "~$7", time: "~20 min", steps: ["Wear the yellow sweatsuit.", "Cut a stem and leaf from green felt.", "Glue them to a headband.", "Peel out when the party ends."]},
  "hot-dog": {buy: ["Tan pool noodle", "Yellow fabric paint"], cost: "~$8", time: "15 min + drying", steps: ["Split the pool noodle lengthwise for the bun.", "Wear it around your red shirt.", "Paint a mustard squiggle down the front.", "Relish the attention."]},
  "donut": {buy: ["Large cardboard", "Pink paint", "Colorful dot stickers"], cost: "~$7", time: "~45 min", steps: ["Cut a giant ring from cardboard.", "Paint it pink frosting.", "Cover it with dot-sticker sprinkles.", "Wear it with straps front and back."]},
  "coffee-cup": {buy: ["Cardboard tube or box", "Brown poster board", "White trash bag"], cost: "~$5", time: "~30 min", steps: ["Wear the white trash bag as the cup sleeve.", "Make a brown lid hat from poster board.", "Write your coffee order on the front.", "Stay jittery."]},
  "salt-pepper": {buy: ["Cardboard", "Silver paint"], cost: "~$1 each", time: "15 min + drying", steps: ["One wears all white, the other all black.", "Build shaker-top hats from cardboard.", "Paint them silver.", "Season everything."]},
  "fruit-salad": {buy: ["Felt leaves", "Headbands"], cost: "~$2 each", time: "~30 min", steps: ["Each person picks a fruit and dresses in its color.", "Cut leaves from green felt.", "Glue the leaves to headbands.", "Toss yourselves together."]},
  "wizard": {buy: ["Black fabric for robe", "Poster board", "Wooden dowel", "Gray face paint"], cost: "~$6", time: "~1 hr", steps: ["Cut a flowing robe from black fabric.", "Roll a tall cone hat from poster board.", "Paint a gray beard on your chin.", "Carry the staff and speak in riddles."]},
  "toy-box-crew": {buy: ["Cowboy hat", "Sheriff badge printout", "Cardboard for wings"], cost: "~$4 each", time: "~1 hr", steps: ["Assign the toys: sheriff, space ranger, and the rest.", "Sheriff gets the hat and badge.", "Space ranger gets cardboard wings.", "Everyone picks a catchphrase."]},
  "demon-boy-band": {buy: ["Neon fabric paint", "Matching black tees"], cost: "~$2 each", time: "~1 hr", steps: ["Everyone wears black streetwear.", "Paint matching glowing patterns on each tee.", "Style hair idol-tall.", "Debut with a synchronized pose."]},
  "dragon-rider-duo": {buy: ["Cardboard", "Green and red paint", "Toy viking helmet"], cost: "~$5 each", time: "~1.5 hrs", steps: ["Build a dragon body from a big cardboard box.", "Paint it green with red wings.", "Rider wears the viking helmet.", "Fly over the neighborhood."]},
  "numbered-players": {buy: ["Numbered bibs or paper numbers", "Green tracksuits or sweats"], cost: "~$0 each", time: "~20 min", steps: ["Everyone wears green.", "Pin a big number on each chest.", "No smiling.", "Vote someone out at midnight."]},
  "emotion-crew": {buy: ["Face paint", "Colored accessories"], cost: "~$3 each", time: "~30 min", steps: ["Each person picks an emotion and its color.", "Dress head to toe in that color.", "Paint your face to match the mood.", "Stay in character all night."]},
  "kart-racers": {buy: ["Large cardboard boxes", "Paint", "Racing caps or hats"], cost: "~$1 each", time: "~1.5 hrs", steps: ["Cut box karts with a seat hole for each racer.", "Paint racing stripes and numbers.", "Wear with suspenders or straps.", "Race everywhere, no shortcuts."]},
  "tall-hat-crew": {buy: ["Poster board", "Red and white paint", "Blue wigs", "Bow tie"], cost: "~$11 each", time: "~1 hr", steps: ["Paint red and white stripes on poster board for the tall hat.", "Things wear blue wigs and red outfits.", "Add the bow tie.", "Cause delightful chaos."]},
  "chipmunk-trio": {buy: ["Felt letters", "Brown felt for ears", "Sweaters"], cost: "~$10 each", time: "~45 min", steps: ["Glue the letters onto three sweaters.", "Make ears on headbands.", "Draw whiskers and big front teeth.", "Sing in three-part harmony."]},
  "galaxy-knights": {buy: ["Toy energy blades", "Robe fabric or thrifted robes", "Belts"], cost: "~$7", time: "~45 min", steps: ["Wear the robes with belts.", "Ignite the toy blades.", "Practice slow, dramatic duels.", "May the force be with your group chat."]},
  "plastic-dream-crew": {buy: ["Pink accessories", "Plastic jewelry"], cost: "~$1 each", time: "~20 min", steps: ["Dress head to toe in pink.", "Layer every plastic accessory you own.", "Strike the dream pose.", "Everything is fantastic."]},
  "extinct-party-animal": {buy: ["Green felt sheet", "Party hat", "Blank name badge", "Fabric glue"], cost: "~$13", time: "~30 min", steps: ["Cut triangles from the green felt for spikes.", "Glue the spikes along the shoulders of your jacket.", "Write 'Last seen 66 million years ago' on the badge.", "Pin on the badge, put on the party hat, and mingle."]},
  "dino-tourist": {buy: ["Hawaiian shirt (thrifted)", "Plush dinosaur tail", "Toy camera (optional)"], cost: "~$6", time: "~20 min", steps: ["Put on the Hawaiian shirt and the fanny pack.", "Attach the dino tail at your waistband.", "Hang the camera around your neck.", "Ask strangers to take your picture."]},
  "raptor-barista": {buy: ["Green dino hoodie", "Toy T. rex arms", "Paper coffee cup"], cost: "~$4", time: "~30 min", steps: ["Put on the green hoodie with the snout hood up.", "Strap the tiny arms over your own arms.", "Grab a coffee cup with them.", "Serve looks and lattes."]},
  "emotional-support-dinosaur": {buy: ["Vest or sleeveless jacket (closet)", "Green felt sheet", "Blank badge or pin", "Fabric glue"], cost: "~$11", time: "~30 min", steps: ["Cut spike triangles from the green felt.", "Glue the spikes along the vest shoulders and back.", "Write 'Emotional Support Dinosaur' on the badge.", "Pin it on and refuse all pets."]},
  "garden-fairy": {buy: ["Pink tulle", "Cardboard", "Fake flowers", "Wooden dowel or stick", "Elastic"], cost: "~$18", time: "~45 min", steps: ["Cut two wing shapes from cardboard and cover them with pink tulle.", "Glue fake flowers around a headband for the crown.", "Tape a cardboard star to the dowel for the wand.", "Attach the wings with elastic straps and wear over a dress."]},
  "ballerina": {buy: ["Pink tulle", "Wide elastic", "Pink leotard or shirt"], cost: "~$10", time: "~30 min", steps: ["Cut the tulle into long strips.", "Tie the strips around the elastic, snug and side by side, until the tutu looks full.", "Wear the tutu over the leotard with tights.", "Pull hair into a high bun."]},
  "butterfly": {buy: ["Large cardboard", "Acrylic paint set", "Black sweats", "Elastic", "Headband", "Pipe cleaners"], cost: "~$13", time: "~1 hr", steps: ["Cut two big wing shapes from cardboard.", "Paint the wings with bright patterns and let them dry flat.", "Tape elastic loops to the wings for the arms.", "Bend pipe cleaners into antennae on the headband and wear over black sweats."]},
  "pop-star": {buy: ["Sparkly or sequin jacket (thrifted)", "Toy microphone", "Hair teasing comb", "Sunglasses"], cost: "~$6", time: "~25 min", steps: ["Tease the hair big with the comb.", "Wear the sparkly jacket over dark clothes.", "Add the sunglasses.", "Carry the toy microphone everywhere."]},
  "ice-skater": {buy: ["White dress (thrifted)", "White tights", "Hair donut for bun"], cost: "~$4", time: "~25 min", steps: ["Pull the white dress and tights from the closet.", "Twist the hair into a high bun with the hair donut.", "Dab a little blush on the cheeks for the cold-air glow.", "Practice the victory twirl."]},
  "ladybug": {buy: ["Red sweatsuit", "Black felt", "Headband", "Pipe cleaners"], cost: "~$13", time: "~35 min", steps: ["Cut circles from black felt for the dots.", "Glue the dots all over the red sweats.", "Cut two small wing shapes, dot them, and pin them at the back.", "Bend pipe cleaners into antennae on the headband."]},
  "daisy": {buy: ["Yellow craft foam", "Brown craft foam", "Green dress", "Headband"], cost: "~$7", time: "~30 min", steps: ["Cut 10 to 12 petal shapes from the yellow foam.", "Glue the petals in a ring around the headband, tips pointing out.", "Glue a brown circle in the center.", "Wear the flower headband with the green dress."]},
  "little-baker": {buy: ["White paper or poster board", "Apron", "Toy whisk"], cost: "~$7", time: "~25 min", steps: ["Roll the paper into a tall chef hat and tape the seam.", "Trim the hat band to fit.", "Wear the hat with the apron.", "Carry the toy whisk and offer everyone imaginary cupcakes."]},
  "little-artist": {buy: ["Beret or flat cap", "Cardboard for palette", "Washable paint set", "Old smock or oversized tee"], cost: "~$10", time: "~35 min", steps: ["Cut a palette shape from cardboard and paint dabs of color on it.", "Flick a little paint onto the smock for splatters and let dry.", "Wear the beret tilted.", "Carry the palette and a brush."]},
  "beekeeper-bee": {buy: ["White shirt and pants", "Mesh fabric or mosquito head net", "Wide-brim hat", "Yellow shirt and pants", "Black electrical tape", "Pipe cleaners", "Headband"], cost: "~$10 each", time: "~25 min", steps: ["Drape the mesh over the wide-brim hat for the veil, tying it at the neck.", "Wrap black tape stripes around the yellow shirt and pants.", "Tape pipe-cleaner antennae to the headband.", "The adult wears white with the veil, since the mesh limits vision; the smaller of the two wears the stripes with the antennae."]},
  "tetris-duo": {buy: ["Two large cardboard boxes", "Acrylic paint set", "Ribbon for shoulder straps", "Painter's tape"], cost: "~$9 each", time: "~1 hr", steps: ["Cut one L-shaped and one T-shaped tetromino from the cardboard.", "Paint each a bright color and let dry flat.", "Tape ribbon straps to the tops.", "Wear like sandwich boards and click together for photos."]},
  "little-lifeguard": {buy: ["Red t-shirt", "Plastic whistle with lanyard", "Pool noodle", "White duct tape"], cost: "~$18", time: "~20 min", steps: ["Curve the pool noodle into a ring and tape the joint.", "Wrap white tape bands around the ring for the buoy look.", "Wear the red tee and shorts; the parent holds the whistle for photos.", "Carry the buoy over one shoulder."]},
  "little-prince": {buy: ["Gold cardstock", "Cape fabric", "Wide ribbon for sash", "Stick-on gems"], cost: "~$14", time: "~20 min", steps: ["Cut and glue the cardstock into a crown band with points.", "Press the gems around the band.", "Drape the cape and tie or glue it at the shoulders, no pins for under-5s.", "Drape the ribbon sash shoulder to hip and wear the crown tilted."]},
  "fossil-hunter": {buy: ["Khaki vest", "Toy magnifying glass", "Canvas pouch or fanny pack", "Cardboard for bones"], cost: "~$4", time: "~25 min", steps: ["Cut chunky bone shapes from the cardboard and shade the edges.", "Tuck the bones into the pouch with tops peeking out.", "Wear the vest with the pouch on the belt.", "Carry the brush and magnifying glass in the vest pockets."]},
  "milk-cookies": {buy: ["White t-shirt or tunic", "Brown t-shirt or tunic", "White and brown craft felt", "Black marker", "Fabric glue or safety pins"], cost: "~$4 each", time: "~25 min", steps: ["Decide who is milk and who is the cookie before cutting anything.", "Milk: cut a white felt carton front, write MILK on it in block letters, and pin it to the white tunic.", "Cookie: pin a big brown felt circle to the brown tunic and glue on felt chips.", "Wear the tunics over regular clothes and pose side by side."]},
  "chips-guac": {buy: ["Green t-shirt or tunic", "Tan t-shirt or tunic", "Red, yellow, and tan felt", "Headband", "Fabric glue"], cost: "~$4 each", time: "~30 min", steps: ["Guac: glue red and yellow felt dots onto the green tunic.", "Chip: cut a giant tan felt triangle and glue it upright to the headband.", "Let the glue dry flat for 20 minutes before wearing.", "Pose with the guac serving the chip from a bowl."]},
  "sushi-soy": {buy: ["White t-shirt", "Dark t-shirt", "Orange and black felt", "Cardboard and dark brown paint", "Red paper for cap"], cost: "~$6 each", time: "~30 min", steps: ["Sushi: glue an orange felt salmon rectangle on the white tunic with a black seaweed waistband.", "Soy sauce: cut, paint, and wear a tall cardboard bottle like a sandwich board.", "Fold a red paper cap for the bottle top.", "The sushi dips toward the soy bottle in every photo."]},
  "burger-fries": {buy: ["Tan t-shirt", "Red t-shirt", "Green, red, yellow, and tan felt", "Paper bowl", "Cardboard, red paint, yellow paper"], cost: "~$3 each", time: "~35 min", steps: ["Burger: glue felt lettuce, tomato, and cheese layers on the tan tunic and wear the felt-covered bowl upside down as the bun.", "Fries: build a red cardboard carton with yellow paper fry sticks poking out.", "Wear the carton like a sandwich board over the red t-shirt.", "Line the carton with a plastic bag and fill it with wrapped candy."]},
  "donut-coffee": {buy: ["White and brown t-shirts", "Pink and tan felt", "Cardboard for ring and cup", "Brown paint", "White paper for lid"], cost: "~$6 each", time: "~35 min", steps: ["Donut: cover a big cardboard ring with tan fabric, add a pink felt frosting ring with sprinkles, and wear it like a sandwich board.", "Coffee: roll and paint a tall cardboard cup, add a white paper lid.", "Wear the cup over the brown t-shirt.", "Link arms for the full breakfast-date effect."]},
  "wine-cheese": {buy: ["Burgundy t-shirt", "Yellow t-shirt", "White and burgundy felt", "Fabric glue"], cost: "~$3 each", time: "~25 min", steps: ["Wine: glue a white felt wine glass with burgundy wine onto the burgundy tunic.", "Cheese: cut round holes in a yellow felt triangle and pin it over the yellow tunic.", "Raise your glasses together for every photo."]},
  "kpop-demon-huntresses": {buy: ["Black pants or leggings", "Metallic tops", "Toy microphones", "Cardboard and silver duct tape", "Face paint set"], cost: "~$12 each", time: "~40 min", steps: ["Agree on one accent color for all three outfits.", "Build three cardboard swords wrapped in silver duct tape.", "Dress in black with metallic tops and bold face paint stripes.", "Hit one shared pose for every photo."]},
  "goth-braids": {buy: ["Black dress", "Black tights", "Hair ties", "Black eyeliner", "Pale foundation"], cost: "~$7", time: "~20 min", steps: ["Braid the hair into two tight braids.", "Apply pale foundation and heavy black eyeliner.", "Wear the black dress with tights and dark lipstick.", "Practice the unimpressed stare."]},
  "juke-joint-vampires": {buy: ["Two vintage-style suits", "Plastic vampire fangs", "Fake blood", "Hair gel", "Toy trumpet"], cost: "~$30 each", time: "~30 min", steps: ["Thrift two vintage-cut suits and press the shirts.", "Slick hair back and fit the fangs.", "Add red pocket squares and a dab of fake blood.", "One of you carries the trumpet everywhere."]},
  "blue-heeler-pup": {buy: ["Blue-gray hoodie and sweatpants", "Blue and gray craft felt", "Black face paint", "Safety pins", "Fabric glue"], cost: "~$7", time: "~25 min", steps: ["Make felt ears and pin them inside the hood.", "Glue felt spots onto the hoodie.", "Paint a black nose and whisker dots.", "Pin a felt tail to the sweatpants."]},
  "baby-pumpkin": {buy: ["Orange onesie", "Green craft felt", "Soft stuffing", "Brown felt for stem", "Safety pins"], cost: "~$4", time: "~20 min", steps: ["Lightly stuff the onesie so it looks plump.", "Pin green felt leaves around the collar.", "Roll brown felt into a stem for the hood.", "Photograph the pumpkin in a lined laundry basket."]},
  "pirate-captain": {buy: ["Striped shirt", "Cardboard for hat", "Eye patch", "Toy sword", "Brown paper for map", "Gold plastic coins"], cost: "~$4", time: "~30 min", steps: ["Cut and tape the cardboard captain hat.", "Draw the treasure map with an X.", "Wear stripes, patch, and hat.", "Hand out gold coins to everyone you meet."]},
  "cowboy-duo": {buy: ["Two denim shirts", "Cardboard for two hats", "Two bandanas", "Paper bags for chaps", "Rope or twine"], cost: "~$6 each", time: "~25 min", steps: ["Cut two cardboard cowboy hats and tape the seams.", "Tie bandanas and coil the rope over a shoulder.", "Cut paper-bag chaps to tape over jeans.", "Tip your hats to everyone you greet."]},
  "smores-duo": {buy: ["Two tan t-shirts", "White t-shirt", "Brown craft felt", "Pillow stuffing", "Fabric glue", "Black marker"], cost: "~$6 each", time: "~30 min", steps: ["Decide the cracker-marshmallow-cracker order.", "Lightly stuff the white t-shirt for the marshmallow.", "Glue the chocolate felt square on the front cracker.", "Write GRAHAM on both tan tunics."]},
  "scarecrow": {buy: ["Plaid flannel shirt", "Jeans with patches", "Straw or raffia", "Old hat", "Face paint set", "Rope or twine"], cost: "~$18", time: "~25 min", steps: ["Stuff straw into cuffs, collar, and pant legs.", "Tie straw bundles at wrists and ankles.", "Paint a stitched smile and triangle nose.", "Wear plaid with the old hat and stand very still."]},
  "yellow-henchmen": {buy: ["Yellow t-shirts", "Blue overalls or jeans", "Swim goggles", "Black gloves", "Bananas"], cost: "~$3 each", time: "~25 min", steps: ["Everyone wears yellow on top, blue on bottom.", "Wear goggles on foreheads with a paper eye inside.", "Carry bananas everywhere.", "Say one shared gibberish phrase in unison."]},
  "mystery-teens": {buy: ["Solid-color tops in assigned colors", "Toy magnifying glass", "Paper for sandwich prop", "Dog plush"], cost: "~$1 each", time: "~20 min", steps: ["Assign each person a color.", "Build outfits from closets in the assigned colors.", "One carries the magnifying glass, one the sandwich.", "Introduce yourselves in character."]},
  "pumpkin-king-bride": {buy: ["Pinstripe suit", "Cardboard and orange paint", "Patchwork dress", "Red yarn", "Black shoes"], cost: "~$13 each", time: "~45 min", steps: ["Cut and paint the cardboard pumpkin mask.", "Wear the pinstripe suit with the mask.", "Bride wears the patchwork dress with yarn pigtails.", "Practice one dramatic bow together."]},
  "moonwalk-star": {buy: ["Red jacket", "White glove", "Glitter glue", "Black fedora", "White socks"], cost: "~$28", time: "~25 min", steps: ["Cover one white glove in glitter glue and dry fully.", "Wear the red jacket, black pants, and fedora.", "One glitter glove only, never two.", "Practice the moonwalk on a smooth floor."]},
  "witchy-sisters": {buy: ["Three colored dresses", "Three witch hats", "Three broomsticks", "Face paint set", "Striped tights"], cost: "~$19 each", time: "~35 min", steps: ["Each sister claims green, purple, or orange.", "Wear the colored dress with black hat and tights.", "Paint a matching mark in your color.", "Cackle in unison for every photo."]},
  "macabre-couple": {buy: ["Long black gown", "Black wig", "Pale foundation", "Dark lipstick", "Black suit"], cost: "~$22 each", time: "~30 min", steps: ["She wears the gown with pale makeup; he wears the suit.", "Style hair severe and slicked.", "Walk arm in arm, speaking little.", "Never smile in photos."]},
  "party-pinata": {buy: ["Large cardboard box", "Rainbow crepe paper", "Wrapped candy", "String and tape"], cost: "~$21", time: "~40 min", steps: ["Cover the box in overlapping crepe fringe rows.", "Cut arm, head, and bottom candy holes.", "Fill with wrapped candy before the party.", "Hand out candy from inside all night."]},
  "fuzzy-gremlin": {buy: ["Brown fuzzy onesie", "Brown craft felt", "Large googly eyes", "White felt", "Fabric glue"], cost: "~$26", time: "~25 min", steps: ["Glue big felt ears to the onesie hood.", "Glue googly eyes above the face opening.", "Add white felt teeth under the hood edge.", "Arrive in a laundry basket for the unboxing."]},
  "rescue-pups": {buy: ["Colored t-shirts", "Felt for badges", "Headbands", "Brown felt for ears", "Fabric glue"], cost: "~$10", time: "~30 min", steps: ["Assign each kid a color and badge shape.", "Glue felt ears to headbands.", "Glue badges to the shirts.", "Line the pups up by color for the photo."]},
  "wayfinder-princess": {buy: ["Tan tank top", "Crepe paper or raffia", "Cardboard and brown paint", "Shell necklace", "Fabric glue"], cost: "~$8", time: "~35 min", steps: ["Tie crepe strips around a waistband for the skirt.", "Paint a spiral on the tank top.", "Cut and paint the cardboard hook.", "Wear the shell necklace and carry the hook."]},
  "chill-painter": {buy: ["Brown afro wig", "Denim shirt", "Cardboard for palette", "Acrylic paints", "Toy paintbrush"], cost: "~$16", time: "~20 min", steps: ["Cut a palette from cardboard with a thumb hole.", "Dab bright paints on and dry fully.", "Wear denim with the afro wig.", "Narrate happy little details about the party."]},
};/* ================= CONFIG: SHARE ================= */
function newShareId(){var c="abcdefghijklmnopqrstuvwxyz0123456789",s="";for(var i=0;i<8;i++)s+=c[Math.floor(Math.random()*c.length)];return s;}
/* 2026-09-26 evening block-map experiment flag (OFF). With the flag off,
   ?o=block is not a recognized origin and every block-map builder returns
   null, so the rendered DOM is byte-identical to the pre-experiment tree. */
var BLOCK_MAP_EXP = false;
/* VIA_SHARE: anonymous id of the share link this visitor arrived through (?s=). Never an identity. */
var VIA_SHARE = null;
/* E29: origin label of the arriving share link (?o=card|generic|sms|vote).
   Read at landing time and carried into recipient_landing_viewed +
   quiz_started so friend-quiz-starts are measurable per share origin. */
var VIA_SHARE_ORIGIN = null;
/* 2026-09-26 duel experiment: ?duel=<sender idea slug> rides the /c/ quiz
   links on share arrivals so results can render the compare panel. */
var DUEL_IDEA_ID = null;
/* 2026-09-26 pair-share experiment: ?pair=<sender idea slug> rides the /c/
   quiz links on "Find my +1's costume" shares so the results page can render
   the "How you two pair up" panel. */
var PAIR_IDEA_ID = null;
/* 2026-09-26 costume roulette experiment: ?spin=<sender idea slug> rides
   the spin share link so the recipient banner can name the spin result. */
var SPIN_IDEA_ID = null;
/* 2026-09-26 wrapped W1 fix: ?wpick=<sender idea slug> rides the wrapped
   share link so the recipient banner can name the sharer's pick + rank.
   Parsed in init; null when absent, and a garbage id falls back to the
   Wrapped-branded generic banner. */
var WRAPPED_PICK_ID = null;
/* 2026-09-26 party link experiment: the group broadcast share. Flag-gated;
   PARTY_PARAMS is parsed in init. */
var PARTY_LINK_ENABLED = false;
var PARTY_PARAMS = null;
/* 2026-09-26 guess-game distribution experiment: decoded ?g= payload (sender answers + pick); null with the flag off or on garbage. */
var GUESS_GAME = null;
/* 2026-09-26 friend-challenge share experiment (BuddyMeter novel-find
   2026-09-26): close the share loop back at the sharer. "Would you pick
   the same costume as me?" The sender's results screen gets a challenge
   row; the recipient link carries ONLY the sender's pick slug:
     https://pickmycostume.com/?s=<sid>&o=challenge&chl=<pick slug>
   No names, no sender answers, no PII -- the slug is a public costume id.
   The recipient takes the normal quiz; the results screen shows a match
   score (100 for the identical pick, otherwise a shared-tag overlap
   percentage capped at 95) plus a "Send my score back" row whose link
   encodes only the score and the friend's pick slug:
     https://pickmycostume.com/?s=<sid>&o=challengeresult&r=<0-100>&rp=<pick slug>
   Opening that link records {score, pick slug, at} into the localStorage
   inbox pmc_challenge_inbox, keyed by the original challenge sid. Inbox
   entries are labelled "Answer 1/2/3..." by arrival order -- never names,
   never claims about who answered. Flag-gated OFF: the flag below is
   false, every builder returns null, both origins are unrecognized in
   init, and the rendered DOM is byte-identical to the pre-experiment tree.
   Staged for owner review: whether this loop runs at all is the owner's call. */
var CHALLENGE_SHARE_ENABLED = false;
var CHALLENGE_PICK_ID = null; /* recipient side: decoded ?chl= (flag-gated) */
var CHALLENGE_RESULT = null;  /* sharer side: decoded ?o=challengeresult payload (flag-gated) */
/* 2026-09-26 proxy-quiz distribution experiment: "Have a friend decide".
   The sender cannot decide, so they send the quiz itself: the recipient
   takes the quiz FOR them and sends one pick back. Flag-gated OFF: the
   flag below is false, every builder returns null, ?o=proxy and
   ?decidefor= are unrecognized in init, and the rendered DOM is
   byte-identical to the pre-experiment tree. The sender's name never goes
   to analytics (named-result rule); only idea ids and share ids do. */
var PROXY_QUIZ_ENABLED = false;
var PROXY_FOR = null;   /* recipient side: sanitized sender name from ?decidefor= (flag-gated) */
var VS_SHARE = null;    /* chained share id from ?vs= on proxy tell-back arrivals */
var _proxyOpenedFired = false;
/* 2026-09-26 collections experiment: ?src=collection-<key> marks arrivals
   from the intent-matched collection pages (/collections/*). 2026-09-27:
   ?src=print-<key> marks arrivals from printed artifacts (candy-bowl card,
   later printable build cards). ?src=share-<key> marks arrivals from
   copy-paste share texts (spread-the-word toolkit: office, parents,
   teachers). Carried into quiz_started (and
   recipient_landing_viewed) as landing_src so collection-, print-, and
   share-driven quiz starts are measurable per source. */
var LANDING_SRC = null;
(function(){ var m = /[?&]src=((?:collection|print|share)-[a-z-]+)/.exec(location.search || ""); if (m) LANDING_SRC = m[1]; })();
function viaShareProps(){
  var p = {};
  if (VIA_SHARE){ p.via_share_id = VIA_SHARE; if (VIA_SHARE_ORIGIN) p.share_origin = VIA_SHARE_ORIGIN; }
  if (LANDING_SRC) p.landing_src = LANDING_SRC;
  return p;
}
/* Inline trending stat: the evidence for the flag, visible with no tap. */
function trendStatEl(idea){
  if(!idea.trending || !idea.trendLane || !idea.trendStat) return null;
  var p = document.createElement("p"); p.className = "trendstat";
  p.textContent = "Trending \u00b7 " + idea.trendLane + ": " + idea.trendStat;
  return p;
}

/* E29 share-origin experiment (2026-09-24): every share link carries
   its origin in ?o= -- "card" for personal-card sends, "generic" for
   "Share this costume"/"Share" buttons. The /c/<slug> Pages function preserves
   extra query params across the redirect, so the origin survives to the
   recipient landing. Canonical share-text builder: shareTextFor(). */

var TAG_WORDS = {
  funny:"Funny", scary:"Scary", cute:"Cute", simple:"Simple",
  couch:"low effort", crafty:"a little crafty", allout:"all-out effort",
  buy:"store-bought", make:"homemade", mix:"mix of both",
  matchyes:"matching", matchloose:"coordinated",
  kidunder3:"toddler-friendly", kid36:"kid-approved", kid7plus:"big-kid approved"
};

/* ================= ENGINE ================= */
var state = { qi: 0, answers: {} }; // answers: {qid: option}

/* 2026-09-26 pm3 red-team: clumsy-thumbs double-tap guard. A second tap within
   the window is a finger bounce, not intent: options answer/advance one
   question per tap, so a 400ms window can never swallow a deliberate answer
   (humans cannot read options and tap twice in 400ms). Per-key timestamps so
   the quiz-option cooldown never blocks the Back button and vice versa. */
var _tapGuards = {};
function tapGuard(key, ms){
  var n = Date.now();
  if (n - (_tapGuards[key] || 0) < ms) return false;
  _tapGuards[key] = n;
  return true;
}

function qById(id){ return QUESTIONS.filter(function(q){ return q.id === id; })[0]; }
function qTitle(qid){
  if (qid === "qinterest") {
    var aud = state.answers.q1 ? state.answers.q1.value : null;
    return (aud === "kid" || aud === "family") ? "What is your kid into?" : "What are you into?";
  }
  return qById(qid).title;
}
function qHint(qid){
  if (qid === "qocc") {
    var aud = state.answers.q1 ? state.answers.q1.value : null;
    if (aud === "kid") return "Trick-or-treating, a party or school parade, or staying in?";
  }
  return qById(qid).hint;
}

/* E10: the kid-age question is asked only when the answer can change the
   ordered top-3. After qinterest is answered we score the three hypothetical
   age answers; if they all agree, q5kid is skipped (about 31% of kid quizzes
   in simulation, 0.00% regret). The interest question therefore comes before
   the age question in the kid flow. */
var _inAgeCheck = false;
function kidAgeNeeded(){
  var qi = state.answers.qinterest;
  if (!qi || !qi.tags) return true; /* undecidable yet: keep the question */
  _inAgeCheck = true;
  try {
    var seen = {};
    var saved = state.answers.q5kid;
    qById("q5kid").options.forEach(function(o){
      state.answers.q5kid = o;
      seen[scoreIdeas().map(function(s){ return s.idea.id; }).join(",")] = true;
    });
    if (saved) state.answers.q5kid = saved; else delete state.answers.q5kid;
    return Object.keys(seen).length > 1;
  } finally {
    _inAgeCheck = false;
  }
}
/* The fit follow-up used to be a conditional 6th quiz question here. It moved
   to the results screen (fitRefinement in renderResults); the quiz never
   exceeds 5 questions now. */
/* The age question retired from the quiz 2026-09-25 (same pattern as qfit
   2026-09-24): as a conditional 6th question it broke the 5-max on
   204/384 kid paths. It now lives on the results screen as an optional
   refinement chip row, shown only when the answer can change the top 3.
   Same scoring effect, zero question tax. */
function flowOrder(){
  var aud = state.answers.q1 ? state.answers.q1.value : null;
  if (aud === "kid") {
    /* Mara 2026-09-25: the occasion is the entire decision for a toddler
       (trick-or-treat vs party/school parade), so the kid flow asks it too.
       The quiz never exceeds 5 questions. */
    return ["q1","q2","q4","qocc","qinterest"];
  }
  /* Every non-kid flow gets the occasion question. It replaced the dead
     buy/make (q5other) and matching-theme (q5couple) questions, and it gives
     the family flow its fifth question. */
  var order2 = ["q1","q2","q4","qocc","qinterest"];
  return order2;
}

function answerTags(){
  var tags = {};
  flowOrder().forEach(function(qid){
    var a = state.answers[qid];
    if (!a || !a.tags) return;
    /* Q2 (vibe) and the kid-interest question are the identity of the answer; count them double so effort never drowns them. */
    var w = (qid === "q2" || qid === "qinterest") ? 2 : 1;
    Object.keys(a.tags).forEach(function(t){ tags[t] = (tags[t] || 0) + w * a.tags[t]; });
  });
  /* Results-screen refinements are not quiz questions, but their tags still
     count: q5kid (kid age) retired from the quiz 2026-09-25. */
  ["q5kid"].forEach(function(qid){
    var a = state.answers[qid];
    if (!a || !a.tags) return;
    Object.keys(a.tags).forEach(function(t){ tags[t] = (tags[t] || 0) + a.tags[t]; });
  });
  return tags;
}

function scoreIdeas(full){
  var aud = state.answers.q1.value;
  var tags = answerTags();
  /* q3 (budget) was retired: the pool is audience-only. */
  var pool = IDEAS.filter(function(i){ return i.audience.indexOf(aud) !== -1; });
  if (pool.length < 3) {
    pool = IDEAS.filter(function(i){ return i.audience.indexOf(aud) !== -1; });
  }
  /* Interest is a hard filter (2026-09-25: "that recommendation could
     only have come from my exact combination of answers"). An idea missing
     the answered interest tag never enters the pool. If the pool would drop
     below 3 we relax to the old -100 soft penalty instead -- scoreOne still
     applies it -- so we never show fewer than 3. */
  var _hIntAns = state.answers.qinterest;
  var _hIntTag = _hIntAns && _hIntAns.tags ? Object.keys(_hIntAns.tags)[0] : null;
  if (_hIntTag) {
    var _intPool = pool.filter(function(i){ return i.tags[_hIntTag]; });
    if (_intPool.length >= 3) pool = _intPool;
  }
  /* Vibe hard filter (2026-09-25, critic round 2): the vibe answer is a
     promise about the top 3, not a nudge. Funny needs funny>=2 AND
     scary<=funny (no scary-dominant "joke garnish"); Scary needs scary>=1;
     Cute needs cute>=1. Relax only if the pool would drop below 3 -- same
     pattern as the interest filter. */
  var _hVibeAns = state.answers.q2;
  var _hVibeTag = _hVibeAns && _hVibeAns.tags ? Object.keys(_hVibeAns.tags)[0] : null;
  function _vibeOk(i){
    var t = i.tags;
    if (_hVibeTag === "funny") return (t.funny||0) >= 2 && (t.scary||0) <= (t.funny||0);
    if (_hVibeTag === "scary") return (t.scary||0) >= 1;
    if (_hVibeTag === "cute") return (t.cute||0) >= 1;
    return true;
  }
  if (_hVibeTag){
    var _vibePool = pool.filter(_vibeOk);
    if (_vibePool.length >= 3) pool = _vibePool;
  }
  /* Kid safety hard filter (2026-09-26: optimize for kid safety): for
     kid quizzes where the age answer carries the kidunder3 tag ("Under 3" or
     "Mixed ages"), suppress any idea with scary>=1 that lacks the kidunder3
     tag. This is the Halloween Wrapped standard: zero scary picks for
     toddlers without an explicit toddler-safe tag. Safety overrides the
     vibe/interest promise. Unlike other filters, there is NO <3 relaxation
     that would reintroduce scary picks -- instead we backfill from safe
     (non-scary) kid ideas so the top 3 never comes back short. */
  var _hAgeAns = state.answers.q5kid;
  var _hAgeUnder3 = _hAgeAns && _hAgeAns.tags && _hAgeAns.tags.kidunder3;
  if (aud === "kid" && _hAgeUnder3){
    var _safePool = pool.filter(function(i){
      var t = i.tags || {};
      return !((t.scary||0) >= 1 && !((t.kidunder3||0) > 0));
    });
    if (_safePool.length < 3){
      /* Backfill from safe kid ideas (non-scary, kidunder3 preferred) so we
         never show fewer than 3, but never reintroduce a scary pick. */
      var _fill = IDEAS.filter(function(i){
        if (i.audience.indexOf("kid") === -1) return false;
        if (_safePool.indexOf(i) !== -1) return false;
        var t = i.tags || {};
        return !((t.scary||0) >= 1 && !((t.kidunder3||0) > 0));
      });
      /* Prefer kidunder3-tagged ideas in the backfill. */
      _fill.sort(function(a,b){ return ((b.tags.kidunder3||0) - (a.tags.kidunder3||0)); });
      _safePool = _safePool.concat(_fill);
    }
    pool = _safePool;
  }
  /* Bar/club night is a hard venue filter: venue.bar 0 ideas (face-covering
     masks, box heads, stilts, oversized/fragile/hot builds) cannot do bar
     night. Same <3 fallback. */
  var _hOccAns = state.answers.qocc;
  var _hOccTag = _hOccAns && _hOccAns.tags ? Object.keys(_hOccAns.tags)[0] : null;
  if (_hOccTag === "occbar") {
    function _barOk(i){ return !i.venue || (i.venue.bar === undefined ? 2 : i.venue.bar) !== 0; }
    var _barPool = pool.filter(_barOk);
    if (_barPool.length < 3){
      /* Bar:0 is an absolute ban (critic 2026-09-25 P8): a bar:0 idea
         (face-covering mask, box head, stilts) can never appear on a bar
         path, even when the pool is thin -- the old <3 fallback served the
         banned idea anyway. Backfill from the bar-safe audience pool
         so the top 3 never comes back short. */
      var _fill = IDEAS.filter(function(i){
        if (i.audience.indexOf(aud) === -1 || !_barOk(i) || _barPool.indexOf(i) !== -1) return false;
        return true;
      });
      _barPool = _barPool.concat(_fill);
    }
    pool = _barPool;
  }
  /* Time/budget constraint refinement (2026-09-26): the results-screen chips
     hard-filter the pool. Same <3 relaxation as the interest/vibe filters. */
  pool = applyConstraints(pool);
  /* Vibe-vs-interest resolution (2026-09-25: "wasn't actually scary tho
     I picked scary"): when the pool holds an idea matching BOTH the picked
     vibe and the picked interest, the vibe promise is absolute -- a non-vibe
     idea takes -100 and can never outrank it. When no idea matches both, the
     interest promise wins and the vibe penalty stays at the old -24. */
  var _vibeAns = state.answers.q2;
  var _vibeTag = _vibeAns && _vibeAns.tags ? Object.keys(_vibeAns.tags)[0] : null;
  var _intAns = state.answers.qinterest;
  var _intTag = _intAns && _intAns.tags ? Object.keys(_intAns.tags)[0] : null;
  var _vibeAndIntPossible = _vibeTag && _intTag && pool.some(function(i){ return i.tags[_vibeTag] && i.tags[_intTag]; });
  function scoreOne(idea){
    var contrib = {};
    var score = 0;
    Object.keys(idea.tags).forEach(function(t){
      if (tags[t]) { contrib[t] = tags[t] * idea.tags[t]; score += contrib[t]; }
    });
    /* Occasion is a promise: the night you picked shapes the pick. A -24
       mismatch penalty (same strength as vibe/effort) made the occasion
       answer move #1 on 13.9% of paths, up from 5.9%, so the question
       finally earns its place. Still far below the -100 interest promise,
       so the interest verdict always wins. */
    var occAns = state.answers.qocc;
    var occTag = occAns && occAns.tags ? Object.keys(occAns.tags)[0] : null;
    if (occTag && !idea.tags[occTag]) score -= 24;
    /* Vibe is a promise when the pool can keep it: see the resolution note above. */
    var vibeAns = state.answers.q2;
    var vibeTag = vibeAns && vibeAns.tags ? Object.keys(vibeAns.tags)[0] : null;
    if (vibeTag && !idea.tags[vibeTag]) score -= _vibeAndIntPossible ? 100 : 24;
    /* Effort is a promise too: a couch-level answer never surfaces an all-out build. */
    var effAns = state.answers.q4;
    var effTag = effAns && effAns.tags ? Object.keys(effAns.tags)[0] : null;
    if (effTag && !idea.tags[effTag]) score -= 24;
    /* 2026-09-26: "My family" means adults WITH kids. In the family
       flow, ideas built for families-with-kids (family-first audience, or kid
       in the audience) outrank group/couple-first ideas wearing a family tag,
       so the top 3 never reads as all adults. Weaker than the interest (-100)
       and occasion/vibe (-24) promises: identity breaks ties, it does not
       override what they asked for. */
    if (aud === "family" && (idea.audience[0] === "family" || idea.audience.indexOf("kid") !== -1)) score += 12;
    /* Presentation is a promise (E14): with a fit answer, an idea leaning the
       other way never outranks one that fits. Unisex ideas always pass, and
       the -6 can never override the -100 interest promise. */
    var fitAns = state.answers.qfit;
    var fitVal = fitAns && fitAns.fit ? fitAns.fit : null;
    if (fitVal === "F" && idea.fit === "M") score -= 6;
    else if (fitVal === "M" && idea.fit === "F") score -= 6;
    /* 2026-09-26: tapping "Masculine looks" must actually change the
       top pick (and its photo), not just quietly re-rank. A fit match earns
       the same weight as a mismatch costs, so a masculine-fitting idea can
       take #1 when the user asks for masculine. Unisex ideas stay neutral. */
    else if (fitVal && idea.fit === fitVal) score += 6;
    /* Interest is the strongest promise: a result that ignores what you're into is a broken promise. */
    var intAns = state.answers.qinterest;
    var intTag = intAns && intAns.tags ? Object.keys(intAns.tags)[0] : null;
    if (intTag && !idea.tags[intTag]) score -= 100;
    return {idea: idea, score: score, contrib: contrib};
  }
  var scored = pool.map(scoreOne);
  scored.sort(function(a, b){
    if (b.score !== a.score) return b.score - a.score;
    return a.idea.rank - b.idea.rank;
  });
  /* Funny guard (2026-09-25: results must read funny, not "scary with
     a joke garnish"). For a Funny answer the top 3 must have funny >= 2 AND
     scary <= funny. If fewer than 3 qualify, relax the scary cap first but
     keep funny >= 2. Never fewer than 3 results. */
  var _fVibeAns = state.answers.q2;
  var _fVibeTag = _fVibeAns && _fVibeAns.tags ? Object.keys(_fVibeAns.tags)[0] : null;
  if (_fVibeTag === "funny") {
    var _fStrict = scored.filter(function(s){ var t = s.idea.tags; return (t.funny||0) >= 2 && (t.scary||0) <= (t.funny||0); });
    var _fLoose = scored.filter(function(s){ return (s.idea.tags.funny||0) >= 2; });
    if (_fStrict.length >= 3) scored = _fStrict;
    else if (_fLoose.length >= 3) scored = _fLoose;
  }
  /* Pinpoint pin: a matched "who exactly?" answer pins its idea to #1. The
     named character outranks even the interest promise. If the audience
     filter excluded it, it is scored and added anyway so #1 is real. */
  if (state.pinpoint && state.pinpoint.idea){
    var pinId = state.pinpoint.idea, pinIdea = null, at = -1;
    for (var pi = 0; pi < IDEAS.length; pi++) if (IDEAS[pi].id === pinId){ pinIdea = IDEAS[pi]; break; }
    if (pinIdea){
      for (var si = 0; si < scored.length; si++) if (scored[si].idea.id === pinId){ at = si; break; }
      var pinned = (at === -1) ? scoreOne(pinIdea) : scored.splice(at, 1)[0];
      scored.unshift(pinned);
      /* 2026-09-26 party link experiment: theme + no-twins reordering for
         party guests. Stable demotion (ES2019 sort is stable): theme
         mismatches rank below theme matches, already-claimed ideas rank
         last. No-op unless a party arrival armed state.partyTheme /
         state.partyTaken. */
      if (typeof state !== "undefined" && state && (state.partyTheme || (state.partyTaken && state.partyTaken.length))){
        var _pt = state.partyTheme, _ptaken = {};
        (state.partyTaken || []).forEach(function(id){ _ptaken[id] = 1; });
        scored.sort(function(a, b){
          return partyDemoteKey(a.idea, _pt, _ptaken) - partyDemoteKey(b.idea, _pt, _ptaken);
        });
      }
      if (scored.length > 3 && !full) scored = scored.slice(0, 3);
    }
  }
  return full ? scored : scored.slice(0, 3);
}

/* E15: the "Why this fits you" line is composed from the user's actual answers,
   then the idea's own static line. The header promises the line is about YOU;
   a static line breaks that promise ("the 'why this fits' isn't curated
   to my picks"). Every dynamic line references at least one real answer; if
   composition fails, fall back to the static line. No em dashes.
   E15b ("clearly duplicate not contextual"): the line LEADS with the
   idea-specific reason, and each fragment has synonym variants picked by
   result index, so identical answers still read differently on #1/#2/#3. */
var FIT_FRAGMENTS = {
  couch:["Couch-level effort","Almost no effort required","A truly minimal build"],
  crafty:["A little crafty","A fun scissors-and-glue project","Some hands-on making involved"],
  allout:["Worth going all out","A go-big-or-go-home build","Full-commitment costume energy"],
  occtreat:["made for trick-or-treating","built for the trick-or-treat route","ready for door-to-door candy"],
  occparade:["made for the school parade","built for the class party","parade-ready and classroom-safe"],
  occparty:["party-ready","made for the party","built to be seen at the party"],
  occbar:["made for a night out","built for a night on the town","ready for the late-night scene"],
  occcandy:["easy to wear while handing out candy","comfortable for candy duty","great for greeting trick-or-treaters"],
  occlowkey:["made for a low-key night in","perfect for a quiet night in","built for staying in"]
};
/* The reader is the parent, even in kid mode: the header names whose fit
   it is. Kid answers keep the parent's perspective ("Why this fits your
   kid"), never the kid's. */
function whyHeader(){
  var a = (typeof state !== "undefined" && state.answers && state.answers.q1) ? state.answers.q1.value : null;
  return (a === "kid") ? "Why this fits your kid" : "Why this fits you";
}
function whyLine(scored, idx){
  var idea = scored.idea, dyn = [], v = ((idx||0)%3+3)%3;
  function firstTag(qid){
    var a = state.answers[qid];
    return (a && a.tags) ? Object.keys(a.tags)[0] : null;
  }
  function answerLabel(qid){
    var a = state.answers[qid];
    return (a && a.label) ? a.label : null;
  }
  /* Effort honesty (critic 2026-09-25 P5): the effort fragment describes the
     COSTUME, not the user's answer. ideaEffortKey reads the idea's own
     couch/crafty/allout tags; using the q4 answer here once claimed
     "Worth going all out" for a couch:2 costume. */
  var e = FIT_FRAGMENTS[ideaEffortKey(idea)], o = FIT_FRAGMENTS[firstTag("qocc")];
  if (e) dyn.push(e[v]);
  if (o) dyn.push(o[v]);
  var tail = dyn.length ? " " + dyn.join(", ") + "." : "";
  /* 2026-09-26 red-team P1: the line never cited the two double-weighted
     answers (vibe + interest), so it felt generic. Folded into tail so the
     return stays `idea.why + tail` (why-lint check 5). 2026-09-29 copy fix:
     noun-phrase fragments ("a funny vibe", "your interest in food & snacks")
     joined with "and" under "Picked for", so the composed line is
     grammatical and never stutters "picked because you picked". */
  var personal = [];
  var vibe = answerLabel("q2");
  if (vibe) personal.push("a " + vibe.toLowerCase() + " vibe");
  var interest = answerLabel("qinterest");
  if (interest && interest !== "Surprise me") personal.push("your interest in " + interest.toLowerCase());
  if (personal.length) tail += " Picked for " + personal.join(" and ") + ".";
  return whyHeader() + ": " + idea.why + tail;
}

/* Recipient-channel inference for recipient_landing_viewed. Open-time UA
   parsing only (the share sheet never reveals the destination app). Order
   matters: in-app UAs also contain Safari tokens, so app checks come first.
   iMessage opens are plain Safari and indistinguishable: safari_unknown. */
function recipientChannel(){
  var ua = navigator.userAgent || "";
  if (/WhatsApp\//i.test(ua)) return "whatsapp";
  if (/Instagram/i.test(ua)) return "instagram";
  if (/FB_IAB\/MESSENGER/i.test(ua) || /FBAN\/Messenger/i.test(ua)) return "messenger";
  if (/FBAN\//i.test(ua) || /FB_IAB/i.test(ua)) return "facebook_iab";
  if (/GSA\//i.test(ua)) return "google_app";
  if (/Safari\//.test(ua) && !/(Chrome|CriOS|FxiOS|EdgiOS|OPiOS)\//.test(ua)) return "safari_unknown";
  if (/Chrome|CriOS/i.test(ua)) return "chrome";
  return "other";
}
/* ================= SCREENS ================= */
/* 2026-09-28: the quiz is a bottom sheet over the current screen.
   openQuizSheet() shows it without hiding what sits underneath; any real
   screen navigation dismisses it first. */
/* 2026-09-30 delight P0: the quiz sheet must never move between questions.
   renderQ() re-ran openQuizSheet() on every question, replaying the entrance
   animation each time -- the sheet visibly slid up after every answer. The
   entrance now plays exactly once per opening; later renders swap content
   in place. _sheetOpenedAt arms the settle guard below (taps during the
   entrance are finger bounces, not answers). */
var _sheetOpenedAt = 0;
function openQuizSheet(){
  var q = $("s-quiz"); if (!q) return;
  if (q.classList.contains("on")) return; /* already open: content swaps in place, no re-animation */
  q.classList.add("sheet");
  q.classList.add("on");
  q.classList.add("pre");
  var bd = $("quizBackdrop"); if (bd) bd.classList.add("on");
  try { document.body.style.overflow = "hidden"; } catch(e){}
  void q.offsetHeight; /* reflow so the fade-in transition plays */
  q.classList.remove("pre");
  _sheetOpenedAt = Date.now();
  try { q.scrollTop = 0; } catch(e2){}
}
function closeQuizSheet(){
  var q = $("s-quiz"); if (!q) return;
  q.classList.remove("sheet"); q.classList.remove("on"); q.classList.remove("pre");
  var bd = $("quizBackdrop"); if (bd) bd.classList.remove("on");
  try { document.body.style.overflow = ""; } catch(e){}
}
document.addEventListener("click", function(e){
  if (e.target && e.target.id === "quizBackdrop"){
    try { Analytics.track("quiz_sheet_dismissed", {at_question: (typeof state !== "undefined" && state) ? state.qi : -1}); } catch(_){}
    closeQuizSheet();
  }
});
function show(id){
  closeQuizSheet();
  var screens = document.querySelectorAll(".screen");
  for (var i = 0; i < screens.length; i++) screens[i].classList.remove("on");
  $(id).classList.add("on");
  /* No self-link: the footer's About link hides while the About screen is up. */
  var f = document.querySelector("footer");
  if (f) f.style.display = (id === "s-about") ? "none" : "";
  window.scrollTo(0, 0);
}

/* ================= COUNTDOWN PLANNER + WHO'S-WHO SHUFFLER (2026-09-26) =================
   Integrated from the love-it prototypes (red-teamed 2026-09-26).
   Planner: works backwards from Oct 31 using real INSTRUCTIONS data.
   Shuffler: one-tap role dealer using the existing CASTS data.
   Privacy: typed names live in JS memory only, never in analytics. Only counts. */
(function(){
  "use strict";
  /* ---------- shared helpers ---------- */
  function esc(s){ return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
  function ideaById(id){
    for (var i = 0; i < IDEAS.length; i++) if (IDEAS[i].id === id) return IDEAS[i];
    return null;
  }
  function halloween(){
    var now = new Date();
    var hw = new Date(now.getFullYear(), 9, 31);
    if (now > hw) hw = new Date(now.getFullYear() + 1, 9, 31);
    return hw;
  }
  var toolReturnTo = "s-hero";

  /* ================= PLANNER ================= */
  var plannerPopulated = false;
  function plannerIdeas(){
    var out = [];
    for (var i = 0; i < IDEAS.length; i++){
      if (INSTRUCTIONS && INSTRUCTIONS[IDEAS[i].id]) out.push(IDEAS[i]);
    }
    out.sort(function(a,b){ return a.title.localeCompare(b.title); });
    return out;
  }
  function plannerParseMinutes(t){
    var m = String(t).match(/(\d+)\s*min/);
    var h = String(t).match(/(\d+)\s*hour/);
    var mins = 0;
    if (m) mins += parseInt(m[1], 10);
    if (h) mins += parseInt(h[1], 10) * 60;
    return mins || 30;
  }
  function plannerAddDays(d, n){ var x = new Date(d); x.setDate(x.getDate() + n); return x; }
  function plannerFmt(d){ return d.toLocaleDateString("en-US", {weekday:"short", month:"short", day:"numeric"}); }
  function plannerYmd(d){
    var p = function(n){ return (n < 10 ? "0" : "") + n; };
    return d.getFullYear() + p(d.getMonth()+1) + p(d.getDate());
  }
  function plannerDaysUntil(d){
    var now = new Date(); now.setHours(0,0,0,0);
    return Math.round((d - now) / 86400000);
  }
  function plannerCalUrl(title, date, details){
    return "https://calendar.google.com/calendar/render?action=TEMPLATE" +
      "&text=" + encodeURIComponent(title) +
      "&dates=" + plannerYmd(date) + "/" + plannerYmd(plannerAddDays(date, 1)) +
      "&details=" + encodeURIComponent(details);
  }
  function plannerIsBuy(m){ return /\(buy:/i.test(m); }
  function plannerPlanFor(ideaId){
    var ins = INSTRUCTIONS[ideaId];
    var mins = plannerParseMinutes(ins.time);
    var hasDrying = /dry/i.test(ins.time) || ins.s.some(function(s){ return /dry/i.test(s); });
    var buildOffset = mins <= 60 ? 1 : (mins <= 180 ? 2 : 3);
    if (hasDrying) buildOffset += 1;
    var hw = halloween();
    var buildDay = plannerAddDays(hw, -buildOffset);
    var buyDay = plannerAddDays(buildDay, -4);
    var buyList = ins.m.filter(plannerIsBuy);
    var ownList = ins.m.filter(function(m){ return !plannerIsBuy(m); });
    var buildSteps = ins.s.filter(function(s){ return !/^optional pro finish/i.test(s); });
    return {ins: ins, mins: mins, hasDrying: hasDrying, buildDay: buildDay,
            buyDay: buyDay, buyList: buyList, ownList: ownList, buildSteps: buildSteps, hw: hw};
  }
  function plannerCountText(d){
    var n = plannerDaysUntil(d);
    if (n < 0) return "That day has passed. Do it today instead.";
    if (n === 0) return "Today. No pressure.";
    if (n === 1) return "Tomorrow. You have got this.";
    return n + " days left.";
  }
  function renderPlanner(ideaId){
    var idea = ideaById(ideaId);
    var box = $("planner-plan");
    if (!idea || !INSTRUCTIONS[ideaId]){ box.innerHTML = ""; return; }
    var p = plannerPlanFor(ideaId);
    var ins = p.ins;
    var lastStep = p.buildSteps.length ? p.buildSteps[p.buildSteps.length-1] : "Gather everything in one spot the night before.";
    var buyDetails = "\uD83C\uDF83 Supply run: " + idea.title + " costume (about " + ins.cost + ")" + "\n\nSee the costume: https://pickmycostume.com/c/" + ideaId + "\n\n" +
      "You need:\n" +
      p.buyList.map(function(m,i){ return (i+1) + ". " + m; }).join("\n") +
      (p.ownList.length ? "\n\nCheck at home first:\n" + p.ownList.map(function(m,i){ return (i+1) + ". " + m; }).join("\n") : "") +
      "\n\n-- Pick My Costume";
    var buildDetails = "\uD83D\uDD28 Build day: " + idea.title + " costume (about " + ins.time + ")" + "\n\nSee the costume: https://pickmycostume.com/c/" + ideaId + "\n\n" +
      "Steps:\n" +
      p.buildSteps.map(function(s,i){ return (i+1) + ". " + s; }).join("\n") +
      "\n\n-- Pick My Costume";
    var h = '<div class="ptl">';
    /* Buy */
    h += '<div class="pms"><p class="pdate">Buy by ' + plannerFmt(p.buyDay) + '</p>';
    h += '<h3>Get the materials</h3>';
    h += '<p class="pcount">' + esc(plannerCountText(p.buyDay)) + ' Budget: ' + esc(ins.cost) + '.</p>';
    if (p.buyList.length){
      h += '<p class="psec">Shopping list</p><ul>' +
        p.buyList.map(function(m){ return "<li>" + esc(m) + "</li>"; }).join("") + '</ul>';
    } else {
      h += '<p>Nothing to buy for this one. Everything comes from your closet.</p>';
    }
    if (p.ownList.length){
      h += '<p class="psec">Check at home first</p><ul>' +
        p.ownList.map(function(m){ return "<li>" + esc(m) + "</li>"; }).join("") + '</ul>';
    }
    h += '<a class="pcal" data-cal="buy" href="' + plannerCalUrl("\uD83C\uDF83 Supply run: " + idea.title + " costume", p.buyDay < new Date(new Date().setHours(0,0,0,0)) ? new Date() : p.buyDay, buyDetails) + '" target="_blank" rel="noopener">Add buy day to calendar</a></div>';
    /* Build */
    h += '<div class="pms"><p class="pdate">Build on ' + plannerFmt(p.buildDay) + '</p>';
    h += '<h3>Build the costume</h3>';
    h += '<p class="pcount">' + esc(plannerCountText(p.buildDay)) + ' Takes about ' + esc(ins.time) + '.</p>';
    h += '<ol>' + p.buildSteps.map(function(s){ return "<li>" + esc(s) + "</li>"; }).join("") + '</ol>';
    if (p.hasDrying) h += '<p class="pnote">Something needs drying time, so build day is pushed one day earlier. Paint before dinner, not after.</p>';
    h += '<a class="pcal" data-cal="build" href="' + plannerCalUrl("\uD83D\uDD28 Build day: " + idea.title + " costume", p.buildDay < new Date(new Date().setHours(0,0,0,0)) ? new Date() : p.buildDay, buildDetails) + '" target="_blank" rel="noopener">Add build day to calendar</a></div>';
    /* Dress up */
    h += '<div class="pms"><p class="pdate">Dress up ' + plannerFmt(p.hw) + '</p>';
    h += '<h3>Wear it</h3>';
    h += '<p class="pcount">' + esc(plannerCountText(p.hw)) + '</p>';
    h += '<p>Last check: ' + esc(lastStep) + '</p>';
    h += '<a class="pcal" data-cal="dress" href="' + plannerCalUrl("\uD83C\uDF83 Dress-up day: " + idea.title, p.hw, "\uD83C\uDF83 Dress-up day: " + idea.title + "\n\nSee the costume: https://pickmycostume.com/c/" + ideaId + "\n\nFinal check: " + lastStep + "\n\nHave a great Halloween night.\n-- Pick My Costume") + '" target="_blank" rel="noopener">Add dress-up day to calendar</a></div>';
    h += '</div>';
    box.innerHTML = h;
    /* Calendar taps: track which milestone, counts only. */
    var cals = box.querySelectorAll("a.pcal");
    for (var i = 0; i < cals.length; i++){
      cals[i].addEventListener("click", function(){
        Analytics.track("planner_cal_added", {milestone: this.getAttribute("data-cal"), idea_id: ideaId});
      });
    }
  }
  window.openPlanner = function(ideaId, returnTo){
    var sel = $("planner-costume");
    if (!plannerPopulated){
      plannerIdeas().forEach(function(idea){
        var o = document.createElement("option");
        o.value = idea.id; o.textContent = idea.title;
        sel.appendChild(o);
      });
      plannerPopulated = true;
      sel.addEventListener("change", function(){ renderPlanner(sel.value); });
    }
    toolReturnTo = returnTo || "s-hero";
    var pick = (ideaId && INSTRUCTIONS[ideaId]) ? ideaId : (sel.options.length ? sel.options[0].value : null);
    if (pick) sel.value = pick;
    renderPlanner(sel.value);
    Analytics.track("planner_opened", {idea_id: sel.value, from: toolReturnTo});
    show("s-planner");
  };

  /* ================= SHUFFLER ================= */
  var shufflerPopulated = false;
  var shufflerLastDeal = null;
  function shufflerIds(){
    var ids = [];
    for (var k in CASTS){ if (CASTS.hasOwnProperty(k)) ids.push(k); }
    ids.sort(function(a,b){
      var ta = (ideaById(a) || {title: a}).title;
      var tb = (ideaById(b) || {title: b}).title;
      return ta.localeCompare(tb);
    });
    return ids;
  }
  function shufflerCap(s){ return s.charAt(0).toUpperCase() + s.slice(1); }
  function shufflerAddPerson(name, kid){
    var wrap = $("shuffler-people");
    var row = document.createElement("div");
    row.className = "sperson";
    var inp = document.createElement("input");
    inp.type = "text"; inp.maxLength = 24; inp.placeholder = "Name";
    if (name) inp.value = name;
    inp.setAttribute("aria-label", "Person name");
    var seg = document.createElement("div");
    seg.className = "sseg";
    var bKid = document.createElement("button"); bKid.type = "button"; bKid.textContent = "Kid";
    var bGrown = document.createElement("button"); bGrown.type = "button"; bGrown.textContent = "Grown-up";
    function setKid(v){
      bKid.classList.toggle("on", v);
      bGrown.classList.toggle("on", !v);
      row.setAttribute("data-kid", v ? "1" : "0");
    }
    bKid.addEventListener("click", function(){ setKid(true); });
    bGrown.addEventListener("click", function(){ setKid(false); });
    setKid(!!kid);
    seg.appendChild(bKid); seg.appendChild(bGrown);
    row.appendChild(inp); row.appendChild(seg);
    wrap.appendChild(row);
  }
  function shufflerReadPeople(){
    var out = [];
    var rows = $("shuffler-people").querySelectorAll(".sperson");
    for (var i = 0; i < rows.length; i++){
      var inp = rows[i].querySelector("input");
      var name = inp.value.trim() || ("Person " + (i+1));
      out.push({name: name, kid: rows[i].getAttribute("data-kid") === "1"});
    }
    return out;
  }
  function shufflerShuffle(a){
    for (var i = a.length - 1; i > 0; i--){
      var j = Math.floor(Math.random() * (i+1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }
  function shufflerDeal(){
    var id = $("shuffler-costume").value;
    var cast = CASTS[id];
    var idea = ideaById(id);
    if (!cast) return null;
    var people = shufflerShuffle(shufflerReadPeople().slice());
    var out = [], fillers = 0;
    if (cast.mode === "assign"){
      var roles = shufflerShuffle((cast.roles || []).slice());
      people.forEach(function(p){
        var idx = -1;
        for (var i = 0; i < roles.length; i++){
          var r = roles[i];
          if ((p.kid && r.kid) || (!p.kid && r.adult)){ idx = i; break; }
        }
        if (idx >= 0){ out.push({name: p.name, role: roles[idx].r}); roles.splice(idx, 1); }
        else { fillers++; out.push({name: p.name, role: cast.filler + " " + fillers}); }
      });
    } else {
      var pool = shufflerShuffle((cast.pool || []).slice());
      people.forEach(function(p){
        if (pool.length){ out.push({name: p.name, role: pool.pop()}); }
        else { fillers++; out.push({name: p.name, role: cast.filler + " " + fillers}); }
      });
    }
    var ul = $("shuffler-lineup");
    ul.innerHTML = "";
    out.forEach(function(a){
      var li = document.createElement("li");
      var w = document.createElement("span"); w.className = "swho"; w.textContent = a.name;
      var ar = document.createElement("span"); ar.className = "sarrow"; ar.textContent = "is";
      var r = document.createElement("span"); r.className = "srole"; r.textContent = shufflerCap(a.role);
      li.appendChild(w); li.appendChild(ar); li.appendChild(r);
      ul.appendChild(li);
    });
    $("shuffler-fillernote").textContent = fillers
      ? "More players than roles, so " + fillers + " got a bonus " + cast.filler + ". Pick a bigger-crew costume or drop a player."
      : "";
    $("shuffler-hint").textContent = "Dealt " + out.length + " roles for " + (idea ? idea.title : id) + ".";
    var res = $("shuffler-result");
    res.style.display = "block";
    if (res.scrollIntoView) res.scrollIntoView({behavior: scrollBehavior(), block: "nearest"});
    var deal = {costume: idea ? idea.title : id, idea_id: id, lineup: out};
    Analytics.track("shuffler_dealt", {idea_id: id, group_size: out.length,
      kid_count: people.filter(function(p){ return p.kid; }).length, fillers: fillers});
    return deal;
  }
  window.openShuffler = function(ideaId, returnTo){
    var sel = $("shuffler-costume");
    if (!shufflerPopulated){
      shufflerIds().forEach(function(id){
        var idea = ideaById(id);
        var o = document.createElement("option");
        o.value = id; o.textContent = idea ? idea.title : id;
        sel.appendChild(o);
      });
      shufflerPopulated = true;
      sel.addEventListener("change", function(){
        var idea = ideaById(sel.value);
        $("shuffler-blurb").textContent = idea ? idea.blurb : "";
        $("shuffler-result").style.display = "none";
        shufflerLastDeal = null;
      });
      $("shuffler-add").addEventListener("click", function(){ shufflerAddPerson("", false); });
      $("shuffler-remove").addEventListener("click", function(){
        var rows = $("shuffler-people").querySelectorAll(".sperson");
        if (rows.length > 1) rows[rows.length-1].parentNode.removeChild(rows[rows.length-1]);
      });
      $("shuffler-deal").addEventListener("click", function(){ shufflerLastDeal = shufflerDeal(); });
      $("shuffler-again").addEventListener("click", function(){ shufflerLastDeal = shufflerDeal(); });
      $("shuffler-share").addEventListener("click", function(){
        if (!shufflerLastDeal){
          $("shuffler-hint").textContent = "Deal the roles first.";
          return;
        }
        var lines = shufflerLastDeal.lineup.map(function(a){ return a.name + " is " + a.role; });
        var text = "Our " + shufflerLastDeal.costume + " lineup:\n" + lines.join("\n") +
          "\n\nDealt with the Pick My Costume who's-who shuffler: https://pickmycostume.com";
        Analytics.track("shuffler_shared", {idea_id: shufflerLastDeal.idea_id, group_size: shufflerLastDeal.lineup.length});
        if (navigator.share){
          navigator.share({title: "Our costume lineup", text: text}).catch(function(){});
        } else if (navigator.clipboard && navigator.clipboard.writeText){
          navigator.clipboard.writeText(text).then(
            function(){ $("shuffler-hint").textContent = "Lineup copied. Paste it in the group chat."; },
            function(){ $("shuffler-hint").textContent = "Could not copy. Screenshot it instead."; });
        } else {
          $("shuffler-hint").textContent = "Screenshot the lineup to share it.";
        }
      });
    }
    toolReturnTo = returnTo || "s-hero";
    /* Red-team fix: the prototype shipped with real family names as the
       default people. Never again. Start with blank rows. */
    $("shuffler-people").innerHTML = "";
    shufflerAddPerson("", false); shufflerAddPerson("", false); shufflerAddPerson("", false);
    $("shuffler-result").style.display = "none";
    $("shuffler-hint").textContent = "";
    shufflerLastDeal = null;
    var pick = (ideaId && CASTS[ideaId]) ? ideaId : (sel.options.length ? sel.options[0].value : null);
    if (pick) sel.value = pick;
    var idea = ideaById(sel.value);
    $("shuffler-blurb").textContent = idea ? idea.blurb : "";
    Analytics.track("shuffler_opened", {idea_id: sel.value, from: toolReturnTo});
    show("s-shuffler");
  };

  /* ---------- wire entry points ---------- */
  function wire(){
    var ph = $("btn-planner-hero");
    if (ph) ph.addEventListener("click", function(){ openPlanner(null, "s-hero"); });
    var sh = $("btn-shuffler-hero");
    if (sh) sh.addEventListener("click", function(){ openShuffler(null, "s-hero"); });
    var pb = $("btn-planner-back");
    if (pb) pb.addEventListener("click", function(){ show(toolReturnTo); });
    var phm = $("btn-planner-home");
    if (phm) phm.addEventListener("click", function(){ show("s-hero"); });
    var sb = $("btn-shuffler-back");
    if (sb) sb.addEventListener("click", function(){ show(toolReturnTo); });
    var shm = $("btn-shuffler-home");
    if (shm) shm.addEventListener("click", function(){ show("s-hero"); });
  }
  if (document.readyState === "loading"){
    document.addEventListener("DOMContentLoaded", wire);
  } else {
    wire();
  }
})();

/* ================= CLOSET-FIRST (2026-09-26) =================
   Integrated from the closet-first prototype (red-teamed 2026-09-26).
   Scores every idea against ticked pantry items with the live pantryScore()
   (the same walk the detail badge and pantry cards use). Rails are 0 / 1 /
   2 purchases away: each missing material line is satisfiable by a single
   purchase. No data duplication: labels and mats come from PANTRY_LABELS /
   PANTRY_MATS. Ticks are page-local; the saved pantry (if any) pre-ticks
   the boxes. Analytics carries counts only. */
(function(){
  "use strict";
  function $(id){ return document.getElementById(id); }
  function esc(s){ return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
  /* Tick groups ported from the red-teamed prototype: 55 checkboxes, zero
     dead, zero untickable against the live PANTRY_MATS. (hoodie is not here:
     its mappings are not in the live PANTRY_MATS yet.) */
  var CF_GROUPS = [
    ["Household staples", ["scissors","tape","paper-pen"]],
    ["Paper and boxes", ["cardboard","paper-bag","paper-plates","newspaper","paper-red","paper-yellow","paper-green","paper-blue","paper-black","paper-white","paper-orange","paper-pink","paper-brown","paper-gray"]],
    ["Clothes and linens", ["white-tshirt","tshirt","black-clothes","sweatsuit","bedsheet","pillowcase","socks","hat","sunglasses","headband","red-headband"]],
    ["Craft drawer", ["glue","markers","yarn","felt","pipe-cleaners","safety-pins","stickers","balloons","foil","stuffing","tape-white","tape-silver","tape-gray","tape-red","tape-yellow","tape-black"]],
    ["Face paint and makeup", ["paint-red","paint-black","paint-white","paint-green","paint-brown","paint-blue","paint-pink","paint-gold","paint-purple","paint-yellow","paint-gray"]]
  ];
  var STAPLES = null;
  function staples(){
    if (!STAPLES){
      STAPLES = {};
      /* Lazy: PANTRY_MATS is declared later in this file than this IIFE. */
      (PANTRY_MATS.staples || []).forEach(function(s){ STAPLES[s] = true; });
    }
    return STAPLES;
  }
  var cfReturnTo = "s-hero";
  var cfBuilt = false;

  function cfTicked(){
    var s = new Set();
    var boxes = document.querySelectorAll('#cf-groups input[type=checkbox]:checked');
    for (var i = 0; i < boxes.length; i++) s.add(boxes[i].getAttribute("data-pid"));
    return s;
  }

  function buildTick(){
    var saved = null;
    try { saved = pantryTicked(); } catch(_){ saved = null; }
    var html = "";
    CF_GROUPS.forEach(function(g){
      html += '<p class="cfgroup">' + esc(g[0]) + "</p>" + '<div class="cftickgrid">';
      g[1].forEach(function(pid){
        var label = PANTRY_LABELS[pid] || pid;
        var staple = !!staples()[pid];
        var checked = (staple || (saved && saved.has(pid))) ? " checked" : "";
        var dis = staple ? " disabled" : "";
        var note = staple ? ' <span class="cfstaple">(assumed)</span>' : "";
        html += '<label class="cftick"><input type="checkbox" data-pid="' + esc(pid) + '"' + checked + dis + ">" + esc(label) + note + "</label>";
      });
      html += "</div>";
    });
    $("cf-groups").innerHTML = html;
    cfBuilt = true;
  }

  function openCloset(returnTo){
    if (!cfBuilt) buildTick();
    cfReturnTo = returnTo || "s-hero";
    $("cf-tick").hidden = false;
    $("cf-results").hidden = true;
    Analytics.track("closet_opened", {from: cfReturnTo});
    show("s-closet");
  }

  function showCloset(){
    var ticked = cfTicked();
    var rails = [[], [], []];
    for (var i = 0; i < IDEAS.length; i++){
      var idea = IDEAS[i];
      var sc = pantryScore(idea.id, ticked);
      if (!sc) continue;
      if (sc.missing <= 2) rails[sc.missing].push({idea: idea, score: sc});
    }
    var total = IDEAS.length;
    var shown = rails[0].length + rails[1].length + rails[2].length;
    $("cf-summary").innerHTML = '<div class="cfsummary"><div class="big">' + rails[0].length + '</div><p>costumes you can build tonight with zero purchases</p></div>';
    var defs = [
      ["0 purchases away", "Build tonight with what you have"],
      ["1 purchase away", "One store item and you are set"],
      ["2 purchases away", "A quick store run covers it"]
    ];
    var html = "";
    defs.forEach(function(d, n){
      var items = rails[n];
      html += '<div class="cfrail"><div class="cfrailhead"><h3>' + d[0] + '</h3><span class="cfcount">' + items.length + '</span></div>';
      html += '<p class="blurb">' + d[1] + "</p>";
      if (!items.length){
        html += '<p class="cfempty">Nothing here yet. Tick more items you own.</p>';
      } else {
        items.slice(0, 20).forEach(function(it){
          html += '<div class="cfcard"><h4><button type="button" class="cfcardlink" data-idea="' + esc(it.idea.id) + '">' + esc(it.idea.title) + "</button></h4><p>" + esc(it.idea.blurb) + "</p>";
          if (n === 0){
            html += '<p class="cfallown">You have everything.</p>';
          } else if (it.score.missingNames){
            html += '<p class="cfneed">Need: ' + it.score.missingNames.map(esc).join(" + ") + "</p>";
          } else {
            html += '<p class="cfneed">' + n + (n === 1 ? " purchase" : " purchases") + " needed</p>";
          }
          html += "</div>";
        });
        if (items.length > 20) html += '<p class="cfempty">+' + (items.length - 20) + " more</p>";
      }
      html += "</div>";
    });
    if (total - shown > 0){
      html += '<p class="cfempty">+' + (total - shown) + " more costumes need 3 or more purchases.</p>";
    }
    $("cf-rails").innerHTML = html;
    $("cf-tick").hidden = true;
    $("cf-results").hidden = false;
    window.scrollTo(0, 0);
    Analytics.track("closet_shown", {zero: rails[0].length, one: rails[1].length, two: rails[2].length, ticked: ticked.size});
  }

  /* ---------- wire entry points ---------- */
  function wire(){
    var h = $("btn-closet-hero");
    if (h) h.addEventListener("click", function(){ openCloset("s-hero"); });
    var s = $("cf-show");
    if (s) s.addEventListener("click", showCloset);
    var r = $("cf-retick");
    if (r) r.addEventListener("click", function(){ $("cf-results").hidden = true; $("cf-tick").hidden = false; window.scrollTo(0, 0); });
    var b = $("btn-closet-back");
    if (b) b.addEventListener("click", function(){ show(cfReturnTo); });
    var hm = $("btn-closet-home");
    if (hm) hm.addEventListener("click", function(){ show("s-hero"); });
    /* Tap-to-detail on rail cards (2026-09-26 gap fix): the card title is a
       button; one delegated listener covers all rails. Guards on
       openIdeaDetail so the screen still renders if detail code is absent. */
    var railsEl = $("cf-rails");
    if (railsEl) railsEl.addEventListener("click", function(e){
      var t = (e.target && e.target.closest) ? e.target.closest(".cfcardlink") : null;
      if (t && t.getAttribute("data-idea") && typeof openIdeaDetail === "function"){
        openIdeaDetail(t.getAttribute("data-idea"), "Why it's great", "s-closet");
      }
    });
  }
  /* Deep-link entry from costume detail screens (2026-09-26 gap fix):
     window.openCloset(returnTo) mirrors window.openPlanner / openShuffler. */
  window.openCloset = openCloset;
  if (document.readyState === "loading"){
    document.addEventListener("DOMContentLoaded", wire);
  } else {
    wire();
  }
})();


function renderQ(){
  /* 2026-09-30: a tapped option keeps :focus, and on touch devices the
     browser paints it stuck-highlighted; clear it on question change. */
  try { if (document.activeElement && document.activeElement.blur) document.activeElement.blur(); } catch(_blur){}
  var order = flowOrder();
  var qid = order[state.qi];
  var q = qById(qid);
  $("q-progress").textContent = "Question " + (state.qi + 1) + " of " + flowOrder().length;
  /* 2026-09-27: name the one-question edit so the detour is explicit. */
  if (state.editQid) $("q-progress").textContent = "Changing one answer \u00B7 Question " + (state.qi + 1) + " of " + flowOrder().length;
  /* 2026-09-30: honest progress. The bar shows how much of the quiz is
     ANSWERED, so Q1 reads 0% and the last question reads 80%; 100% is set
     in the answer handler after the final answer (below), never here. */
  var _qn = flowOrder().length;
  var _qpct = _qn > 0 ? Math.round((state.qi / _qn) * 100) : 100;
  var _qbf = $("qbar-fill");
  if (_qbf) _qbf.style.width = _qpct + "%";
  $("q-title").textContent = qTitle(qid);
  $("q-hint").textContent = qHint(qid);
  /* 2026-09-26 proxy-quiz: recipient banner ("You are picking for X").
     Flag-off: PROXY_FOR is null, so the banner stays hidden and nothing
     fires. textContent only: the name is user input. */
  var _pb = $("q-proxybanner");
  if (_pb){
    if (typeof PROXY_QUIZ_ENABLED !== "undefined" && PROXY_QUIZ_ENABLED && PROXY_FOR){
      _pb.style.display = "block";
      _pb.textContent = "You are picking a costume for " + PROXY_FOR + ". Answer like you are them.";
      if (!_proxyOpenedFired && typeof Analytics !== "undefined" && Analytics.track){
        _proxyOpenedFired = true;
        var _pp = viaShareProps(); _pp.share_origin = "proxy";
        Analytics.track("proxy_quiz_opened", _pp);
      }
    } else {
      _pb.style.display = "none";
    }
  }
  var box = $("q-opts");
  box.innerHTML = "";
  var current = state.answers[qid];
  var opts = q.options;
  /* 2026-09-28: visual-first quiz. Option buttons render as
     emoji-led tiles (big emoji + short label) in a 2-col grid; the
     9-option interest question gets 3 cols. Duel/gift/warm keep the
     old .opt row look: they never touch #q-opts' classes. */
  box.className = "opts tiles" + (opts.length >= 7 ? " many" : "");
  if (qid === "qinterest") {
    var aud0 = state.answers.q1 && state.answers.q1.value;
    if (aud0) opts = opts.filter(function(opt){
      var keys = Object.keys(opt.tags);
      if (!keys.length) return true; /* "Surprise me": no interest filter, always offered */
      var k = keys[0];
      return IDEAS.some(function(i){ return i.audience.indexOf(aud0) !== -1 && (i.tags[k] > 0); });
    });
  }
  if (qid === "qocc") {
    /* Mara 2026-09-25: no bar night for the kid flow.
       2026-09-26: no bar night for the family flow either. "My family"
       means adults with kids; bar/club night was the adult option shown,
       and the bar paths were the only non-food family paths returning
       all-adult top 3s (Plumber Duo, Haunted Portraits, The Olympians).
       2026-09-29: no bar night for the teacher/class flow either; a classroom
       audience gets the same treatment as the kid flow. */
    var aud1 = state.answers.q1 && state.answers.q1.value;
    if (aud1 === "kid" || aud1 === "family" || aud1 === "class") opts = opts.filter(function(opt){ return opt.value !== "bar"; });
  }
  opts.forEach(function(opt){
    var b = document.createElement("button");
    b.type = "button";
    var sel = current && current.label === opt.label;
    b.className = "opt tile" + (sel ? " sel" : "");
    b.setAttribute("aria-pressed", sel ? "true" : "false");
    var tick = document.createElement("span");
    tick.className = "tick";
    tick.setAttribute("aria-hidden", "true");
    tick.textContent = "\u2713";
    var em = document.createElement("span");
    em.className = "opt-emoji";
    em.setAttribute("aria-hidden", "true");
    em.textContent = opt.emoji || "\uD83C\uDF83";
    var lab = document.createElement("span");
    lab.className = "opt-lab";
    lab.textContent = opt.label;
    b.appendChild(tick); b.appendChild(em); b.appendChild(lab);
    b.onclick = function(){
      /* 2026-09-26 pm3 red-team: ignore finger-bounce double-taps. Without
         this, tap 2 lands on the synchronously re-rendered next question and
         answers a question the user never saw (or double-fires finishQuiz). */
      if (!tapGuard("qopt", 400)) return;
      /* 2026-09-30 delight: ignore option taps while the sheet is still
         settling from its entrance fade. A tap aimed at a button that is
         still fading in records the wrong answer; the settle window stacks
         with tapGuard instead of replacing it. */
      if (Date.now() - _sheetOpenedAt < 350) return;
      state.answers[qid] = opt;
      /* 2026-09-29: "Already have one" folds the old warm/cold fork into Q1.
         It is not a quiz path: skip the remaining questions and go straight
         to naming the costume. The "Question X of 5" count stays honest. */
      if (qid === "q1" && opt.value === "warm") {
        Object.keys(state.answers).forEach(function(k){ if (k !== "q1") delete state.answers[k]; });
        quizResumeSave();
        state.warmMode = true;
        renderWarmCapture();
        return;
      }
      /* "Surprise me" on the interest question: no interest filter, just intent. */
      if (qid === "qinterest" && opt.label === "Surprise me") {
        try { Analytics.track("surprise_me", {source: "quiz_interest"}); } catch(_){}
      }
      /* Funnel: per-question drop-off analysis (which question loses people).
         Structural metadata only: NEVER send answer content (opt.label,
         q1 value, or anything the user picked). Privacy rule 2026-09-25. */
      try {
        Analytics.track("quiz_answered", {
          question_id: qid,
          question_index: state.qi + 1,
          question_count: flowOrder().length
        });
      } catch(_){}
      if (qid === "q1") {
        delete state.answers.qinterest; // interest options depend on audience
        /* 2026-09-27: the kid-age refinement answer is meaningless outside
           the kid flow; drop it so an edited q1 cannot score with a stale
           age answer. */
        if (opt.value !== "kid") delete state.answers.q5kid;
        /* 2026-09-26 pm3 red-team: switching to kid/family after picking
           "Bar / club night" left the now-unoffered answer in state, so a
           kid quiz could be scored with occbar tags. Drop it like qinterest.
           2026-09-29: same for the class flow. */
        var _na = opt.value;
        if ((_na === "kid" || _na === "family" || _na === "class") && state.answers.qocc && state.answers.qocc.value === "bar") delete state.answers.qocc;
      }
      // Q1 answer can change which Q5 shows; drop a stale Q5 answer.
      var order2 = flowOrder();
      Object.keys(state.answers).forEach(function(k){
        if (order2.indexOf(k) === -1) delete state.answers[k];
      });
      /* Quiz-abandon resume (2026-09-26 evening): persist per-question progress. */
      quizResumeSave();
      /* 2026-09-27: answer-chip edit mode. A chip tap set editQid;
         the replacement answer recomputes results directly instead of
         marching through the remaining questions, which is what the chip
         caption promises ("tap one to change it and see new picks"). No
         quiz_completed here: the original completion already fired it. */
      if (state.editQid && qid === state.editQid) {
        state.editQid = null;
        clearK("pmc_quiz_v1");
        var _er = scoreIdeas();
        store("pmc_last_v1", {results: _er.map(function(r){ return r.idea.id; }), answers: state.answers, at: Date.now()});
        try { Analytics.track("answer_edited", {question_id: qid}); } catch(_){}
        renderResults(_er);
        return;
      }
      if (state.qi < order2.length - 1) { state.qi++; renderQ(); }
      /* 2026-09-30: the final answer completes the quiz, so the bar
         may reach 100% only here, after the last answer is recorded. */
      else { var _qbf2 = $("qbar-fill"); if (_qbf2) _qbf2.style.width = "100%"; finishQuiz(); }
    };
    box.appendChild(b);
  });
  openQuizSheet();
}

/* Standing privacy rule: quiz answers never leave the device, and the idea
   bank is never sent to analytics. This logs only a non-reversible djb2 hash
   of the sorted "qid:value" answer pattern, so same-vs-different answer
   patterns across retakes are measurable without exposing what anyone picked. */
function finishQuiz(){
  clearK("pmc_quiz_v1"); /* completed quizzes have nothing to resume */
  var results = scoreIdeas();
  store("pmc_last_v1", {results: results.map(function(r){ return r.idea.id; }), answers: state.answers, at: Date.now()});
  Analytics.track("quiz_completed", {idea_ids: results.map(function(r){ return r.idea.id; }), question_count: Object.keys(state.answers).length});
  renderResults(results);
}

/* Detail media (2026-09-25): the photorealistic DIY concept photo only.
   Rule: tapping a card shows the single photo, no "See it in motion"
   animated-loop block on detail/share views. No cartoon sketches, no
   secondary illustrations. */
var PMC_SRCSET_960 = {"beekeeper-bee":1,"blue-alien-ohana":1,"blue-dog-family":1,"bowling-pins":1,"cardboard-knight":1,"chipmunk-trio":1,"classic-ghost":1,"demon-boy-band":1,"dragon-rider-duo":1,"emotion-crew":1,"enchanted-castle-crew":1,"fossil-hunter":1,"galaxy-knights":1,"haunted-portraits":1,"headless-horsemen":1,"kart-racers":1,"little-lifeguard":1,"little-prince":1,"media-generation-block-game-crew-0-714cf59b-a494-4827-a15d-b0de300cfe64":1,"media-generation-blue-alien-ohana-0-5fb5b27d-bed8-4c3f-a851-0a8fddf11ecc":1,"media-generation-blue-dog-family-0-9781d872-2ccc-4ad9-bf63-737c5e082a0c":1,"media-generation-blue-dog-family-0-c2dacb48-3da2-4fe4-9201-d1ace938df48":1,"media-generation-bowling-pins-0-eb41f22a-6e25-4188-a78c-9d613227998c":1,"media-generation-ghost-hunters-0-f247b83c-8820-413c-87af-b0df60264220":1,"media-generation-robot-crew-0-56397e70-2952-4d1f-9c65-af7ef7f762d4":1,"media-generation-safari-zoo-crew-0-e08e84d9-c66a-4378-9765-e8c9a1fc503a":1,"media-generation-soccer-squad-0-62dae7ff-bd00-45fb-abb2-5c7eb1fd9ca4":1,"media-generation-the-olympians-0-649cd90e-53c4-4fa2-aff3-48962d548a72":1,"media-generation-under-the-sea-0-46d2383a-c831-45bb-b6dd-5066bca3bdf2":1,"mermaid-crew":1,"numbered-players":1,"plastic-dream-crew":1,"plumber-duo":1,"robot-crew":1,"safari-zoo-crew":1,"snow-sisters":1,"spider":1,"tall-hat-crew":1,"tetris-duo":1,"the-olympians":1,"tin-hero":1,"toy-box-crew":1,"web-slinger-kid":1,"wizard":1}; /* 2026-09-30: slugs with a -960.webp variant (wide sources only) */
/* 2026-09-30: responsive photos. Every slug has -256/-480 variants; -960
   exists only for wide sources (see PMC_SRCSET_960). The browser picks the
   smallest sufficient file; plain src stays as the fallback. */
function pmcSrcset(img, slug, sizes){
  try {
    var ss = "photos/" + slug + "-256.webp 256w, photos/" + slug + "-480.webp 480w";
    if (PMC_SRCSET_960[slug]) ss += ", photos/" + slug + "-960.webp 960w";
    img.setAttribute("srcset", ss);
    if (sizes) img.setAttribute("sizes", sizes);
  } catch(_){}
}
function ideaMedia(idea, photoOnly){
  var wrap = document.createElement("div");
  /* 2026-09-27: AI loop videos left out on purpose. Motion magnifies AI
     artifacts and cheapens trust in the build guides, so cards and detail
     views show the static concept photo only. The mp4s stay in images/anim/
     if we ever reverse this. */
  var photo = document.createElement("img");
  photo.src = "photos/" + idea.id + ".webp";
  pmcSrcset(photo, idea.id, "(min-width:900px) 600px, 94vw");
  photo.alt = "";
  photo.style.width = "100%";
  photo.style.borderRadius = "10px";
  photo.style.marginBottom = "4px";
  photo.setAttribute("onerror", "this.style.display='none'");
  wrap.appendChild(photo);
  var tag = document.createElement("div");
  tag.textContent = "AI-generated concept photo";
  tag.style.cssText = "font-size:11px;color:#9a8fb8;margin-bottom:12px;";
  wrap.appendChild(tag);
  return wrap;
}

/* One result card, extracted so the "Still stuck?" section can render
   alternates (ranks 4-6) with the exact same card, including tap-to-pick. */
/* In-site build steps: "How to make it" (materials + steps) for every idea.
   This is now the primary "how to assemble" surface; the "Ask my AI" prompt
   stays as a secondary option. Cards get a <details> disclosure; the share
   landing renders it expanded, since the recipient's costume is the point. */
function buildInstructions(idea, opts){
  opts = opts || {};
  var ins = (typeof INSTRUCTIONS !== "undefined") ? INSTRUCTIONS[idea.id] : null;
  if (!ins || !ins.m || !ins.s) return null;
  var via = opts.via || "card";
  /* Audience-adaptive guide copy (Dev's blind review, 2026-09-25): the same
     build guide reads differently for a parent dressing a toddler vs. a
     24-year-old heading to a bar. For adult quiz audiences (solo/couple/
     group), kid-directed safety lines are dropped and "adults handle X"
     becomes "one person handles X". Kid/family flows and answer-less
     contexts (browse, share landings) keep the original family-safe copy. */
  function adultAudience(){
    try {
      var a = state.answers.q1 ? state.answers.q1.value : null;
      return a === "solo" || a === "couple" || a === "group";
    } catch(e){ return false; }
  }
  function adaptStep(step){
    if (!adultAudience()) return step;
    if (/kids under three|toddlers|very young kids|very small children|might choke/i.test(step) && /^Safety:/i.test(step)) return null;
    var s = step;
    s = s.replace(/adults handle the scissors/gi, "one person handles the cutting");
    s = s.replace(/an adult should handle/gi, "one person should handle");
    s = s.replace(/let an adult handle/gi, "let one person handle");
    s = s.replace(/an adult handles/gi, "one person handles");
    s = s.replace(/adults only/gi, "careful with these");
    s = s.replace(/,? and keep the scissors away from small kids\.?/gi, ".");
    s = s.replace(/so kids can wear it all night/gi, "so it stays comfortable all night");
    s = s.replace(/Dress the kid in/gi, "Put on");
    s = s.replace(/the kid holds/gi, "you hold");
    s = s.replace(/non-toxic kids' /gi, "non-toxic ");
    return s;
  }
  function adaptMaterial(m){
    if (!adultAudience()) return m;
    return m.replace(/^Kids:\s*/i, "").replace(/per kid\b/gi, "per person").replace(/per child\b/gi, "per person");
  }
  /* 2026-09-29: the fit line's paper-bag/mask clause is boilerplate that
     leaked onto costumes with no bag or mask (Elsa's page showed it). Keep
     the clause only when the costume's own materials or steps mention a
     paper bag or a mask; otherwise strip it so the fit note only says
     what applies to this costume. */
  function fitTextFor(){
    var t = ins.sizing || "";
    var marker = "if the costume uses a paper bag or mask";
    if (t.indexOf(marker) === -1) return t;
    var hay = ((ins.m || []).join(" ") + " " + (ins.s || []).join(" ")).toLowerCase();
    if (/paper bag/.test(hay) || /\bmask\b/.test(hay)) return t;
    var cut = t.indexOf("; " + marker);
    if (cut !== -1) return t.slice(0, cut) + ".";
    return t;
  }
  /* Plain-text build list for the copy button: decision triple, materials,
     numbered steps. */
  function tripleText(){
    var t = [ins.time, ins.cost, ins.effort].filter(function(x){ return x; });
    return t.length ? t.join(" \u00B7 ") : "";
  }
  function buildListText(){
    var lines = [idea.title + " - build list"];
    /* 2026-09-26: one build section. The copy matches what is visible:
       the weekly plan (cost/time/buy/steps), not a second materials list. */
    var mp = (typeof MAKE_PLANS !== "undefined") ? MAKE_PLANS[idea.id] : null;
    if (mp){
      lines.push("Est. cost " + mp.cost + " \u00B7 about " + String(mp.time).replace(/^~/, ""));
      lines.push("", "What to buy:");
      mp.buy.forEach(function(b){ lines.push("- " + b); });
    } else {
      var _tr = tripleText();
      if (_tr) lines.push(_tr);
      var _ft = fitTextFor();
      if (_ft) lines.push("Fit: " + _ft);
      lines.push("", "You need:");
      ins.m.forEach(function(m){ lines.push("- " + adaptMaterial(m)); });
    }
    lines.push("", "Steps:");
    var n = 0;
    ins.s.forEach(function(s){
      var a = adaptStep(s);
      if (a !== null){ n++; lines.push(n + ". " + a); }
    });
    /* Experiment 5 (stream B, 2026-09-26): viral footer on copied build list.
       Hypothesis: parents take the build list to the store and share it.
       A "made with" footer turns every copy into a distribution touchpoint.
       Measure: pickmycostume.com referrals from shared build lists. */
    lines.push("", "Made with Pick My Costume - https://pickmycostume.com");
    return lines.join("\n");
  }
  /* 2026-09-25: the quick version. ChatGPT's DIY format beats ours on
     readability: 5-word imperatives, materials folded into steps, one closing
     tip. This compresses the full guide to that shape for the app; the /c/
     pages keep the full version below it for search. */
  /* 2026-09-27 red-team: a naive indexOf(". ") split lands inside quoted
     phrases ('No. 001', 'Emotional Support Dinosaur. Do not pet.') and renders
     a dangling mid-sentence fragment. The same holds for the 110-char comma
     cut ('BREAKFAST BUFFET, all you can eat'). Quoted spans are atomic: an
     opening quote is a quote char followed by a non-space, so possessive
     apostrophes (panels') and decade shorthands ('80s) never pair up as
     bogus spans. */
  function delimOutsideQuotes(s, delim){
    var spans = [], m, re = /'[^'\s][^']*'|"[^"\s][^"]*"/g;
    while ((m = re.exec(s))) spans.push([m.index, m.index + m[0].length]);
    var k = 0;
    for (;;){
      k = s.indexOf(delim, k);
      if (k < 0) return -1;
      var inside = false;
      for (var j = 0; j < spans.length; j++){
        if (k > spans[j][0] && k < spans[j][1]){ inside = true; break; }
      }
      if (!inside) return k;
      k += 1;
    }
  }
  function sentenceEnd(s){ return delimOutsideQuotes(s, ". "); }
  function firstSentence(s){
    var i = sentenceEnd(s);
    var out = (i > 0 ? s.slice(0, i + 1) : s).trim();
    /* Long single sentences get cut at the first comma clause so the quick
       steps stay scannable like a text, not a paragraph. */
    if (out.length > 110){
      var c = delimOutsideQuotes(out, ", ");
      if (c > 40) out = out.slice(0, c) + ".";
    }
    return out;
  }
  function quickSectionBody(){
    var wrap = document.createElement("div");
    wrap.className = "howto-body howto-quick";
    var ins = INSTRUCTIONS[idea.id];
    if (!ins) return wrap;
    var head = document.createElement("p");
    head.className = "howto-triple";
    head.textContent = "DIY this week: ~" + ins.cost + ", " + ins.time;
    wrap.appendChild(head);
    /* Content layer 2026-09-25: sizing guidance, the fit note every parent
       asks about, right under the decision triple. */
    var _fitText = fitTextFor();
    if (_fitText){
      var _fit = document.createElement("p");
      _fit.className = "howto-fit"; _fit.textContent = "Fit: " + _fitText;
      wrap.appendChild(_fit);
    }
    var ul = document.createElement("ul");
    ul.className = "howto-quick-steps";
    var tip = null, n = 0;
    ins.s.forEach(function(s){
      var a = adaptStep(s);
      if (a === null) return;
      if (/^Optional pro finish:\s*/i.test(a)){
        if (!tip) tip = a.replace(/^Optional pro finish:\s*/i, "").trim();
        return;
      }
      if (/^Safety:\s*/i.test(a)) return; /* full version keeps safety */
      if (n >= 5) return;
      n++;
      var li = document.createElement("li");
      li.textContent = firstSentence(a);
      ul.appendChild(li);
    });
    wrap.appendChild(ul);
    if (tip){
      var tp = document.createElement("p");
      tp.className = "howto-tip";
      tp.textContent = "Tip: " + firstSentence(tip);
      wrap.appendChild(tp);
    }
    /* 2026-09-26 red-team P1: safety steps were stripped from the app
       with no path to the full guide (114/164 have them). They render here as
       a compact safety block, not counted in the 5 steps. */
    var safeties = [];
    ins.s.forEach(function(s){
      var a = adaptStep(s);
      if (a !== null && /^Safety:\s*/i.test(a)) safeties.push(a.replace(/^Safety:\s*/i, "").trim());
    });
    if (safeties.length){
      var sp = document.createElement("p");
      sp.className = "howto-safety";
      sp.textContent = "Safety: " + safeties.join(" ");
      wrap.appendChild(sp);
    }
    return wrap;
  }
  function sectionBody(){
    var wrap = document.createElement("div");
    wrap.className = "howto-body";
    var copyRow = document.createElement("div");
    copyRow.className = "howto-copyrow";
    var cb = document.createElement("button");
    cb.type = "button"; cb.className = "howto-copy";
    cb.textContent = "Copy build list";
    var cst = document.createElement("span"); cst.className = "status";
    cb.onclick = function(e){
      if (e && e.stopPropagation) e.stopPropagation();
      doCopy(buildListText(), function(ok, msg){
        cst.textContent = ok ? "Copied. Take it to the store." : msg;
        if (ok) Analytics.track("build_steps_copied", {idea_id: idea.id, via: via});
      });
    };
    copyRow.appendChild(cb);
    /* Email-me-the-list: mailto fallback, no backend, no capture. Graded step-6 option B.
       Poke-holes fixes 2026-09-25: honest event name, neutral status copy, in-app
       browser guidance, 1800-char href cap with truncation note, CRLF line breaks. */
    var eb = document.createElement("a");
    eb.className = "howto-copy"; eb.textContent = "Email me the build list"; eb.href = "#";
    eb.setAttribute("role", "button");
    eb.onclick = function(e){
      if (e && e.preventDefault) e.preventDefault();
      if (e && e.stopPropagation) e.stopPropagation();
      var inApp = /Instagram|FBAN|FBAV|TikTok/i.test(navigator.userAgent || "");
      var body = buildListText().replace(/\n/g, "\r\n");
      /* 2026-09-27 loop measurement: mint a share id and append a trackable
         guide link so the email recipient leg is measurable. The recipient
         lands on the /c/ guide (no analytics); tapping "Take the 2-minute
         quiz" carries ?s= to the homepage where recipient_landing_viewed
         fires with share_origin=emaillist. */
      var _elsid = (typeof newShareId === "function") ? newShareId() : "";
      var _elurl = _elsid ? ("https://pickmycostume.com/c/" + idea.id + "?s=" + _elsid + "&o=emaillist") : "https://pickmycostume.com";
      if (encodeURIComponent(body).length > 1500){
        var lines = body.split("\r\n");
        while (lines.length > 1 && encodeURIComponent(lines.join("\r\n")).length > 1400) lines.pop();
        body = lines.join("\r\n") + "\r\n...full list at " + _elurl;
      } else {
        body = body + "\r\n\r\nStep-by-step guide: " + _elurl;
      }
      var subj = "Build list: " + idea.title;
      var href = "mailto:?subject=" + encodeURIComponent(subj) + "&body=" + encodeURIComponent(body);
      Analytics.track("build_list_email_opened", {idea_id: idea.id, via: via, share_id: _elsid, share_origin: "emaillist"});
      if (inApp){
        cst.textContent = "In-app browsers can't open email - tap Copy build list, then paste it into your email app.";
      } else {
        cst.textContent = "Opening your email app - if nothing happens, use Copy build list.";
      }
      window.location.href = href;
      return false;
    };
    copyRow.appendChild(eb);
    copyRow.appendChild(cst);
    wrap.appendChild(copyRow);
    /* 2026-09-26: ONE build section. The weekly plan (est. cost/time +
       what to buy) leads; the old separate "You need" materials chips are
       dropped when the plan exists, because they described the same build. */
    var _mp = (typeof MAKE_PLANS !== "undefined") ? MAKE_PLANS[idea.id] : null;
    if (_mp){
      var meta = document.createElement("p");
      meta.className = "howto-triple";
      meta.textContent = "Est. cost " + _mp.cost + " \u00B7 about " + String(_mp.time).replace(/^~/, "");
      wrap.appendChild(meta);
      var buyh = document.createElement("h4"); buyh.textContent = "What to buy";
      wrap.appendChild(buyh);
      var buyul = document.createElement("ul");
      _mp.buy.forEach(function(b){
        var bli = document.createElement("li"); bli.textContent = b; buyul.appendChild(bli);
      });
      wrap.appendChild(buyul);
    } else {
      /* Decision triple: the guide's most quotable line, first under the h3. */
      var _tr = tripleText();
      if (_tr){
        var tp = document.createElement("p");
        tp.className = "howto-triple"; tp.textContent = _tr;
        wrap.appendChild(tp);
      }
      var mh = document.createElement("h4"); mh.textContent = "You need";
      wrap.appendChild(mh);
      var chips = document.createElement("div");
      chips.className = "howto-chips";
      ins.m.forEach(function(m){
        var c = document.createElement("span");
        c.className = "howto-chip"; c.textContent = adaptMaterial(m);
        chips.appendChild(c);
      });
      wrap.appendChild(chips);
    }
    var sh = document.createElement("h4"); sh.textContent = "Steps";
    wrap.appendChild(sh);
    var ol = document.createElement("ol");
    ins.s.forEach(function(s){
      var a = adaptStep(s);
      if (a === null) return; /* adult audience: kid-only safety line dropped */
      var li = document.createElement("li");
      var sm = /^Safety:\s*/.exec(a);
      if (sm){
        var b = document.createElement("b"); b.textContent = "Safety: ";
        li.appendChild(b);
        li.appendChild(document.createTextNode(a.slice(sm[0].length)));
      } else {
        li.textContent = a;
      }
      ol.appendChild(li);
    });
    wrap.appendChild(ol);
    /* Parent FAQs as a collapsible block: visible on expand, simple markup. */
    if (ins.faqs && ins.faqs.length){
      var fdet = document.createElement("details");
      fdet.className = "howto-faq";
      var fsum = document.createElement("summary");
      fsum.textContent = "Common questions";
      fdet.appendChild(fsum);
      var fdl = document.createElement("dl");
      ins.faqs.forEach(function(f){
        var dt = document.createElement("dt"); dt.textContent = f[0];
        var dd = document.createElement("dd"); dd.textContent = f[1];
        fdl.appendChild(dt); fdl.appendChild(dd);
      });
      fdet.appendChild(fdl);
      /* E17 lesson: taps inside the card must not re-run doPick and wipe
         state. The disclosure stops its own clicks. */
      fdet.addEventListener("click", function(e){ e.stopPropagation(); });
      wrap.appendChild(fdet);
    }
    return wrap;
  }
  var root;
  if (opts.expanded){
    root = document.createElement("div");
    root.className = "howto howto-open";
    var t = document.createElement("h3"); t.textContent = "Make it this week";
    root.appendChild(t);
    root.appendChild(quickSectionBody());
  } else {
    root = document.createElement("details");
    root.className = "howto";
    var sum = document.createElement("summary");
    sum.textContent = "Make it this week";
    root.appendChild(sum);
    root.appendChild(quickSectionBody());
    /* E17 lesson: a tap inside the card that is not on a button/link would
       re-run doPick and wipe state. The disclosure stops its own clicks. */
    root.addEventListener("click", function(e){ e.stopPropagation(); });
    /* A toggle-open is a genuine "build steps viewed" signal. */
    root.addEventListener("toggle", function(){
      if (root.open) Analytics.track("build_steps_viewed", {idea_id: idea.id, via: via});
    });
  }
  return root;
}
/* 2026-09-30 (Billy Issue 2): "Plan this costume" was save-not-plan. The
   pick panel now delivers the actual plan inline: the idea's own steps,
   materials, and time/cost/effort from INSTRUCTIONS, rendered with the
   howto styles. The AI prompt stays as a secondary option inside the
   "Keep building your costume" disclosure. Cast ideas keep their own
   per-person plans via buildCastPanel. */
function buildInlinePlan(idea){
  var box = document.createElement("div");
  /* 2026-09-30 (share-block spec): scroll target for "How to make it \u2192". */
  box.id = "build-guide";
  box.className = "howto howto-open plan-inline";
  /* E17 lesson: taps inside the pick card must not re-run doPick. */
  if (box.addEventListener) box.addEventListener("click", function(e){ e.stopPropagation(); });
  var ins = (typeof INSTRUCTIONS !== "undefined") ? INSTRUCTIONS[idea.id] : null;
  var h = document.createElement("h3");
  h.textContent = "Your plan";
  box.appendChild(h);
  if (!ins || !ins.m || !ins.s){
    /* No guide data: point at the guide instead of rendering an empty plan. */
    var p = document.createElement("p"); p.className = "status";
    var a = document.createElement("a"); a.href = "/c/" + idea.id;
    a.textContent = "See the step-by-step guide";
    p.appendChild(a); box.appendChild(p);
    return box;
  }
  var body = document.createElement("div");
  body.className = "howto-body";
  var tri = [ins.time, ins.cost, ins.effort].filter(function(x){ return x; }).join(" \u00B7 ");
  if (tri){
    var tp = document.createElement("p");
    tp.className = "howto-triple"; tp.textContent = tri;
    body.appendChild(tp);
    /* 2026-09-30 price rebase: honest pricing basis, one line. */
    var basis = document.createElement("p");
    basis.className = "howto-basis";
    basis.textContent = "Cost estimate: adds up the buy-list items at typical big-box prices (Target, Amazon, thrift store). Closet and made-from-scraps items count as $0. Group costume costs are per person, so your real total may be lower.";
    body.appendChild(basis);
  }
  var mh = document.createElement("h4"); mh.textContent = "You need";
  body.appendChild(mh);
  var ul = document.createElement("ul");
  ins.m.forEach(function(m){
    var li = document.createElement("li"); li.textContent = m; ul.appendChild(li);
  });
  body.appendChild(ul);
  var sh = document.createElement("h4"); sh.textContent = "Steps";
  body.appendChild(sh);
  var ol = document.createElement("ol");
  ins.s.forEach(function(s){
    var li = document.createElement("li");
    var sm = /^Safety:\s*/.exec(s);
    if (sm){
      var b = document.createElement("b"); b.textContent = "Safety: ";
      li.appendChild(b);
      li.appendChild(document.createTextNode(s.slice(sm[0].length)));
    } else {
      li.textContent = s;
    }
    ol.appendChild(li);
  });
  body.appendChild(ol);
  box.appendChild(body);
  /* 2026-09-30 (share-block spec): the AI plan left the share block; a quiet
     text link at the end of the build guide opens it in place. Event name
     "browse_ai_prompt_copied" is the existing event used for the identical
     showPromptPreview(div, buildIdeaPrompt(idea), ...) pattern on browse
     cards (line 10421). The link hides after one tap: one plan per guide. */
  var aiLink = document.createElement("button");
  aiLink.type = "button"; aiLink.className = "textlink"; aiLink.textContent = "Want a custom plan?";
  aiLink.onclick = function(){
    var d = document.createElement("div");
    box.appendChild(d);
    showPromptPreview(d, buildIdeaPrompt(idea), "browse_ai_prompt_copied", true, null, "Custom AI plan");
    aiLink.style.display = "none";
  };
  box.appendChild(aiLink);
  return box;
}
/* ================= SHAREABLE RESULT CARD =================
   The hero result is "Your <year> Halloween costume": kicker, big visual,
   fit reasons grounded in the user's actual answers, and a fact row
   (vibe / build time / budget / difficulty). Share captions are punchy,
   group-chat-ready lines per idea; the fallback stays plain. The loop
   question ("What are you going as?") always rides along so recipients
   get pulled into the quiz. */
var EFFORT_FACTS = {
  couch:  {build: "Under 30 minutes", difficulty: "Easy"},
  crafty: {build: "1 to 2 hours", difficulty: "Medium"},
  allout: {build: "A weekend project", difficulty: "Ambitious"}
};
var BUDGET_FACTS = {diy: "From your closet", low: "Under $20", mid: "$20 to $50"};
function ideaEffortKey(idea){
  var tags = idea.tags || {}, best = "crafty", bestV = 0;
  /* Ties resolve toward the higher effort: if an idea scores for both
     crafty and all-out, the build guide reflects the ambitious version. */
  ["couch", "crafty", "allout"].forEach(function(k){
    if ((tags[k] || 0) >= bestV){ bestV = tags[k] || 0; best = k; }
  });
  return bestV > 0 ? best : "crafty";
}
function ideaBudgetLabel(idea){
  var b = idea.budget || [];
  if (b.indexOf("diy") >= 0) return BUDGET_FACTS.diy;
  if (b.indexOf("low") >= 0) return BUDGET_FACTS.low;
  return BUDGET_FACTS.mid;
}
/* 2026-09-29 (claim 4): the result tile showed tag-derived Build/Budget
   ("From your closet" + "1 to 2 hours") while the build steps showed the
   INSTRUCTIONS plan's own time/cost ("~$5-10, 60 min") -- same idea, two
   answers. Build and Budget are now single-sourced from the INSTRUCTIONS
   build plan (the same fields "Make it this week" and the detail tri-rows
   read), so the tile can never disagree with the steps. Tag-derived labels
   remain only as a fallback for ideas without a build plan. Difficulty
   stays tag-derived: it feeds the effort fragments and role computation. */
function planFacts(idea){
  var ins = (typeof INSTRUCTIONS !== "undefined") ? INSTRUCTIONS[idea.id] : null;
  if (ins && (ins.time || ins.cost)) return {build: ins.time || null, budget: ins.cost || null};
  var _ek = ideaEffortKey(idea);
  return {build: EFFORT_FACTS[_ek].build, budget: ideaBudgetLabel(idea)};
}
/* Result roles (2026-09-25; expanded 2026-09-25 per his "be creative"
   brief): the top 3 earn their labels; labels are computed, never hardcoded.
   #1 is always "Best Match". Runner-up candidates, most defensible first:
   "Easiest" (unique lowest build difficulty, margin >= 2, never #1),
   "Zero-Dollar Build" (the make-plan cost is genuinely $0 -- a range like
   $0-10 is not zero), "Tonight-Ready" (make-plan time of 30 min or less),
   "Plot Twist" (its top interest differs from the user's picked interest
   while its vibe matches the user's picked vibe), "Wildcard" (clearly the
   largest tag distance from #1, margin >= 3). One role per result: the most
   defensible candidate wins, the rest are dropped, never stacked. When no
   candidate's evidence gate passes, the card keeps neutral numbering --
   never a forced label. */
function buildDifficulty(idea){
  var er = {couch:0, crafty:1, allout:2}[ideaEffortKey(idea)];
  var b = idea.budget || [], br = 3;
  if (b.indexOf("diy") >= 0) br = 0;
  else if (b.indexOf("low") >= 0) br = 1;
  else if (b.indexOf("mid") >= 0) br = 2;
  return er * 2 + br; /* 0 = closet + under-30-min, 7 = high-budget weekend project */
}
function tagDistance(a, b){
  var keys = {}, k;
  var ta = a.tags || {}, tb = b.tags || {};
  for (k in ta) keys[k] = 1;
  for (k in tb) keys[k] = 1;
  var d = 0;
  for (k in keys) d += Math.abs((ta[k] || 0) - (tb[k] || 0));
  return d;
}
/* Evidence gates for the newer roles. Each returns a hard yes/no from real
   data; a role renders only when its gate passes. */
function planCostIsZero(idea){
  /* "Zero-Dollar Build": the MAKE_PLANS cost is genuinely $0. A range like
     "~$0-10 total" is NOT zero -- it can cost money. Only an exact $0 parses. */
  if (typeof MAKE_PLANS === "undefined") return false;
  var p = MAKE_PLANS[idea.id];
  if (!p || !p.cost) return false;
  return /^\~?\$0(\.00)?$/.test(p.cost.trim());
}
function planMinutes(idea){
  /* Parses "~20 min" / "~1.5 hrs" to minutes; null when unparseable. */
  if (typeof MAKE_PLANS === "undefined") return null;
  var p = MAKE_PLANS[idea.id];
  if (!p || !p.time) return null;
  var m = p.time.match(/~?([\d.]+)\s*(min|hr)/i);
  if (!m) return null;
  var n = parseFloat(m[1]);
  return /hr/i.test(m[2]) ? Math.round(n * 60) : n;
}
function planIsTonightReady(idea){
  /* "Tonight-Ready": the make-plan builds in 30 minutes or less, end to end. */
  var mins = planMinutes(idea);
  return mins !== null && mins <= 30;
}
function planCostMax(idea){
  /* Parses "~$8" / "~$10 total" / "~$10 each" / "~$0-10 total" to the max
     dollar figure; null when unparseable. "each" is taken at face value
     (per costume); group headcounts are unknown to the quiz. */
  if (typeof MAKE_PLANS === "undefined") return null;
  var p = MAKE_PLANS[idea.id];
  if (!p || !p.cost) return null;
  var m = String(p.cost).match(/~?\$(\d+(?:\.\d+)?)(?:-(\d+(?:\.\d+)?))?/);
  if (!m) return null;
  return m[2] ? parseFloat(m[2]) : parseFloat(m[1]);
}
/* 2026-09-26 constraint refinement (CHC Costume Wizard steal, adapted): the
   Wizard asks time and money budget as first-class questions and then ignores
   them in results; we ask as results-screen chips (the 5-max keeps them
   out of the quiz; the q3 budget question was cut 2026-09-23 after moving
   outcomes on only 4.5% of kid paths) and hard-filter on them honestly.
   Same <3 relaxation as the interest/vibe filters: a constraint that would
   leave fewer than 3 ideas does not apply. */
var CONSTRAINT_CHIPS = [
  {key:"time", max:30, label:"30 min or less"},
  {key:"time", max:60, label:"An hour or less"},
  {key:"budget", max:10, label:"$10 or less"}
];
function constraintOk(idea, c){
  if (!c) return true;
  if (c.timeMax != null){
    var mins = planMinutes(idea);
    if (mins !== null && mins > c.timeMax) return false;
  }
  if (c.budgetMax != null){
    var cost = planCostMax(idea);
    if (cost !== null && cost > c.budgetMax) return false;
  }
  return true;
}
function applyConstraints(pool){
  var c = (typeof state !== "undefined" && state) ? state.constraints : null;
  if (!c || (c.timeMax == null && c.budgetMax == null)) return pool;
  var f = pool.filter(function(i){ return constraintOk(i, c); });
  return f.length >= 3 ? f : pool;
}
function planIsPlotTwist(idea){
  /* "Plot Twist": the pick's strongest interest tag differs from the user's
     picked interest, but its vibe matches the user's picked vibe (ranking
     thresholds, same as the quiz). No quiz interest or vibe answered, or an
     idea with no interest tag, means no evidence -- no role. */
  var qi = (typeof state !== "undefined" && state.answers) ? state.answers.qinterest : null;
  var qv = (typeof quizVibeTag === "function") ? quizVibeTag() : null;
  if (!qi || !qi.tags || !qv) return false;
  var userInt = null, k;
  for (k in qi.tags){ if (INTEREST_TAGS.indexOf(k) >= 0){ userInt = k; break; } }
  if (!userInt) return false;
  var t = (typeof moreLikeThisTag === "function") ? moreLikeThisTag(idea) : null;
  if (!t || t.kind !== "interest" || t.tag === userInt) return false;
  return vibeOkFor(qv, idea.tags || {});
}
/* One plain-English line per role, shown on first appearance per results
   screen. No em dashes. */
var ROLE_NOTES = {
  "Best Match": "The highest-scoring pick for your answers.",
  "Easiest": "The simplest build of your top 3, by a clear margin.",
  "Zero-Dollar Build": "Made entirely from things you already own. It costs $0.",
  "Tonight-Ready": "Builds in 30 minutes or less.",
  "Plot Twist": "A different interest than the one you picked, but the same vibe. Worth a look.",
  "Wildcard": "The most different pick from your best match. A curveball."
};
function resultRoles(results){
  var roles = ["Best Match", null, null];
  if (!results || results.length < 3) return roles;
  var diff = [0, 1, 2].map(function(i){ return buildDifficulty(results[i].idea); });
  var minD = Math.min(diff[0], diff[1], diff[2]);
  var minCount = diff.filter(function(d){ return d === minD; }).length;
  var nextD = Math.min.apply(null, diff.filter(function(d){ return d > minD; }));
  var minIdx = diff.indexOf(minD);
  var d2 = tagDistance(results[0].idea, results[1].idea);
  var d3 = tagDistance(results[0].idea, results[2].idea);
  var wildIdx = (Math.abs(d2 - d3) >= 3) ? (d2 > d3 ? 1 : 2) : -1;
  [1, 2].forEach(function(i){
    var idea = results[i].idea, c = [];
    if (minCount === 1 && minIdx === i && (nextD - minD) >= 2) c.push("Easiest");
    if (planCostIsZero(idea)) c.push("Zero-Dollar Build");
    if (planIsTonightReady(idea)) c.push("Tonight-Ready");
    if (planIsPlotTwist(idea)) c.push("Plot Twist");
    if (wildIdx === i) c.push("Wildcard");
    roles[i] = c.length ? c[0] : null;
  });
  return roles;
}
var AUDIENCE_PHRASE = {
  "Solo": "going solo", "My kid": "your kid", "My family": "the whole family",
  "Couple": "couples", "Group": "groups", "Teacher / class": "the classroom"
};
/* Fit reasons: the idea-specific why first, then the dynamic effort/occasion
   fragments, then plain-English reflections of the user's own answers. Every
   reason is grounded in real data, never invented. */
/* 2026-09-25: "Why this fits you" is a lie when we know nothing about
   the user (Surprise me, browse-without-quiz). With no quiz answers the
   header must not claim personal fit. */
function hasQuizAnswers(){
  for (var k in state.answers) if (Object.prototype.hasOwnProperty.call(state.answers, k)) return true;
  return false;
}
function fitReasons(scored, idx){
  var idea = scored.idea, out = [];
  /* Pinpoint: when this card IS the named character's match, lead with it. */
  if (state.pinpoint && state.pinpoint.idea === idea.id){
    out.push("You asked for " + state.pinpoint.label + ": this is our DIY take on it.");
  }
  out.push(idea.why);
  var wl = whyLine(scored, idx).replace(/^Why this fits (you|your kid): /, "");
  var tail = wl.slice(idea.why.length).trim();
  if (tail) out.push(tail.charAt(0).toUpperCase() + tail.slice(1));
  function ansLabel(qid){
    var a = state.answers[qid];
    return a ? a.label : null;
  }
  var vibe = ansLabel("q2");
  /* 2026-09-27 pm red-team: only claim the vibe matches when the idea
     actually carries the picked vibe tag. Snow Sisters (no scary tag)
     was telling "Scary" pickers "Matches the scary vibe you picked." */
  var vtags = (state.answers.q2 && state.answers.q2.tags) ? Object.keys(state.answers.q2.tags) : [];
  var vibeHit = vtags.some(function(k){ return idea.tags && idea.tags[k]; });
  if (vibe && vibeHit) out.push("Matches the " + vibe.toLowerCase() + " vibe you picked.");
  var aud = ansLabel("q1");
  if (aud && AUDIENCE_PHRASE[aud]) out.push("Built for " + AUDIENCE_PHRASE[aud] + ".");
  return out.slice(0, 4);
}
/* Punchy, group-chat-ready share captions, one per top idea. House voice:
   plainspoken, specific, funny. The loop question is appended by the share
   builder, not baked in here. */
var SHARE_CAPTIONS = {
  "wizard": "I know you're not a costume person. Remember the wizard from high school? Let's go trick or treating.",
  "web-slinger-crew": "Your friendly neighborhood crew is suiting up.",
  "blue-dog-family": "The whole family is going as cartoon dogs. The 4-year-old has completely lost it.",
  "block-game-crew": "We are going as the game. Built from actual boxes in the garage.",
  "bamboo-demon": "Pink kimono. Bamboo muzzle. Not saying a word all night.",
  "emerald-witch": "Green from head to toe. The hat alone took an hour.",
  "tin-hero": "The Tin Hero rides again. Cardboard never looked this good.",
  "snow-sisters": "The cold never bothered us anyway. (Sorry. Had to.)",
  "fairy-tale-princesses": "Every princess. One group photo. Zero fights over who is who.",
  "ramen-bowl": "Going as a bowl of ramen. The chopsticks are pool noodles.",
  "classic-ghost": "A sheet. Two eye holes. Peak Halloween.",
  "good-witch-bad-witch": "One of us is the good witch. Guess which.",
  "superhero-family": "The whole family is going super. Capes from old pillowcases.",
  "haunted-animatronics": "The animatronics are haunted. The kids are thrilled. The parents are tired.",
  "soccer-squad": "The whole squad is suiting up. Shin guards optional.",
  "mermaid-crew": "We are going as mermaids. No swimming involved.",
  "gloom-bloom": "Half gloom, half bloom. Like October itself.",
  "ghost-hunters": "We are busting ghosts on Saturday. Fight me.",
  "plumber-duo": "It is-a us. The plumbers.",
  "breakfast-buffet": "We are going as breakfast. All of it.",
  "burger-joint-couple": "We are the burger joint. Come hungry.",
  "neon-demon-hunter": "Pop star by day. Demon hunter by night.",
  "cereal-crew": "Part of a complete breakfast.",
  "safari-zoo-crew": "The zoo crew is loose.",
  "tooth-fairy": "The tooth fairy is collecting this year. Check under your pillow.",
  "bumble-bee": "Buzz buzz.",
  /* Kid-idea captions (Mara 2026-09-25: the kid costumes were getting the
     generic fallback while the adult ones got real captions). */
  "blue-alien-ohana": "Blue hoodie. Antenna headband. Ohana means nobody sits out Halloween.",
  "fuzzy-monster": "One googly eye. Zero scary. The toddler picked this one.",
  "pocket-plush": "Going as a pocketful of plush. The backpack is the costume.",
  "glow-skeleton": "Bones was a skeleton, and every one of her bones glowed. Her ribs glowed. Her funny little skull glowed. Even her toe bones glowed, all ten of them, like tiny flashlights.\n\nBones loved Halloween most of all, because on Halloween the streets filled with children, and the children filled the dark with laughter. But Bones had noticed something. When the sun went down and the streetlights buzzed on, some of the littlest trick-or-treaters held their grown-ups' hands a little tighter.\n\nSo Bones had an idea. She would be the nightlight.\n\nShe stood at the corner where the sidewalk was darkest, and she glowed. Her ribs lit up the path. Her skull lit up the smiles. And because she glowed, the cars could see every single child from far, far away, and the drivers slowed down and waved.\n\n\"Look,\" whispered a little girl dressed as a star. \"She's lighting the way.\"\n\nOne by one, the children fell into step behind Bones, like ducklings behind their mother. She led them past the creaky gate and around the puddle and right up to the house with the very best candy, her toe bones twinkling with every step.\n\nWhen the last porch light clicked off and the last costume was hung up for the night, Bones walked home under the real stars. She was tired, and her glow was getting softer, dimmer, sleepier.\n\nShe lay down in her cozy coffin bed, which was really just a bed with a very silly name, and her glow faded down, down, down, until it was no brighter than the moon through a window.\n\n\"Goodnight, street,\" yawned Bones. \"Goodnight, stars. My work here is done.\"\n\nAnd in houses all down the block, children slept soundly, dreaming in soft green light.",
  "fuzzy-monster": "Marnie was a monster, and Marnie was fuzzy. Very fuzzy. Extremely fuzzy. Her fur was the color of strawberry milk, and it was so soft that when she walked through the house, people reached out to pet her without even thinking about it.\n\nMarnie had tried to be scary once. She stood in a doorway and said, \"Roar.\" But her roar came out as a purr, a deep rumbly purr like a sleepy engine, and the toddler she was trying to scare crawled straight into her lap and fell asleep.\n\nAfter that, Marnie stopped trying to be scary. She had a much better job. Marnie collected lost socks.\n\nEvery night, she padded softly through the house on her big fuzzy feet, checking under beds and behind dressers. Left socks, right socks, striped socks, socks with holes in the toes. She gathered them all in her arms, a great soft bundle of them, and left them folded at the foot of each bed.\n\n\"How do the socks always come back?\" the children wondered.\n\nIt was Marnie, of course. It was always Marnie.\n\nTonight, Marnie found one last sock under the crib, a tiny one with a duck on it. She held it to her cheek because it was soft, and she was soft, and soft things understand each other. Then she folded it, placed it with the others, and curled up in the corner of the nursery, a great warm mountain of fur.\n\nThe baby sighed in her sleep and rolled toward the warmth. Marnie's purr started up, low and steady, like a lullaby with no words.\n\nMonsters, it turns out, are just pajamas that learned to walk around and love you. Goodnight, Marnie. Goodnight, socks. Goodnight.",
  "neon-demon-hunter": "By day, she was the biggest pop star in the world. Her concerts sold out. Her songs played in every car. Her jacket was covered in neon lights, pink and blue and electric purple, and when she danced, the whole stage danced with her.\n\nBut nobody knew about her night shift. Nobody except you, and now you must keep the secret.\n\nWhen the last encore ended and the crowd went home, she traded her microphone for a sword made of stage light. Because while the city slept, the bad dreams came out. Wobbly, wibbly bad dreams, drifting around the rooftops.\n\nAnd she hunted them. Oh, how she hunted them.\n\nShe moved across the rooftops without a sound, her neon jacket glowing, her light-sword humming a low, brave note. When a bad dream reached for a window, she was there first. One swing, and the bad dream popped like a bubble, turning into a puff of glitter that smelled faintly of strawberries.\n\nPop. There went the dream about the test. Pop. There went the dream about the dark basement. Pop, pop, pop, all the way down the street, until every window was safe and every child was dreaming about ice cream and birthday parties instead.\n\nOn your street, she paused. She looked at your window for a long moment. Then she hung her light-sword on the corner of your bed, where it glowed very, very softly, pink and blue and electric purple.\n\n\"For you,\" she whispered. \"So the dreams stay sweet.\"\n\nThen she was gone, back into the night, humming her biggest hit under her breath. The pop star's night shift was done. Goodnight, hunter. Goodnight, dreams.",
  "baby-dino": "Danny was a baby dinosaur, and Danny had a problem. He wanted to stomp. All the big dinosaurs stomped. His mother stomped and the ground went boom. His father stomped and the leaves shook off the trees. Danny stomped and the ground went, well, pat.\n\n\"Pat,\" said the ground, politely.\n\nDanny practiced every day. He lifted his little foot, which was cozy inside a soft hoodie costume with spikes down the back, and he brought it down with all his might. Pat. He tried roaring, too. \"Raar,\" he said, as fiercely as he could. It came out as a squeak. The butterflies were not impressed.\n\nOne evening, Danny sat down on a mossy rock and sighed a great big baby-dino sigh. \"I'll never be big,\" he said.\n\nHis mother sat beside him, which made the ground go boom in a nice way, and said, \"Watch.\"\n\nA tiny bird had fallen from its nest and was chirping on the ground, too little to fly home. Danny's mother leaned down, gentle as a whisper, and lifted the bird on the tip of her enormous claw, and placed it softly back in the nest.\n\n\"Big isn't the stomp,\" said his mother. \"Big is knowing when to be gentle.\"\n\nDanny thought about that all the way home. That night, he practiced his gentle. He tucked his blanket around his stuffed triceratops. He patted his pillow soft. And when he yawned, his roar came out as the softest thing of all.\n\n\"Raar,\" whispered Danny. \"I mean, goodnight.\"\n\nAnd the moon, which had seen many dinosaurs, smiled down at the littlest one of all.",
  "bumble-bee": "Bea was a bumblebee, and Bea was in a hurry. She had stripes painted on her back, yellow tape stripes, three of them, very official. She had wings that went buzz buzz buzz, and a list in her head that went flower, flower, flower, no time to waste.\n\n\"Hurry,\" she told her wings every morning. \"So much to do.\"\n\nShe zoomed to the roses. She zipped to the daisies. She did not stop to smell a single one, because smelling took time, and time was for the list.\n\nThen one afternoon, Bea zoomed straight into a spiderweb. Not a scary spiderweb, just a sticky one, strung between two sunflowers. She wriggled and buzzed, and the more she hurried, the more stuck she got.\n\n\"Stop hurrying,\" said a ladybug, who was sitting nearby doing absolutely nothing. \"Hurrying is how you got in.\"\n\nSo Bea stopped. She took a breath. She carefully, slowly, one leg at a time, unstuck herself from the web. It took a whole minute. A whole slow minute.\n\nAnd when she was free, she looked around, really looked, for the first time all day. The sunflowers were taller than houses. The air smelled like honey and warm grass. A drop of dew on a leaf held the whole sky inside it.\n\n\"Oh,\" said Bea.\n\nShe spent the rest of the afternoon doing one flower at a time. She counted the petals. She said thank you to each blossom. She was still a bee, and bees have work, but now she knew the secret the ladybug knew. Slow is also a speed.\n\nBy sunset, Bea's wings were too sleepy to buzz. They just hummed, low and soft, all the way home. She folded them neatly, tucked herself into the hive, and dreamed of sunflowers taller than houses.\n\nGoodnight, Bea. The flowers will wait.",
  "walking-taco": "Every year, the preschool held a Halloween parade, and every year, one costume got the biggest laugh. This year, it was Terry the Walking Taco.\n\nTerry was magnificent. His shell was golden and crunchy-looking, his lettuce was green streamers that tickled his ears, his cheese was soft yellow strips, and his tomatoes were two red pom-poms that bounced when he walked. Which was constantly, because Terry could not stop wiggling.\n\nThe parade began. The princesses waved. The superheroes posed. And then came Terry, wiggling down the sidewalk, tomatoes bouncing, lettuce tickling, and the crowd went wild.\n\n\"Look at the taco go!\" shouted someone's grandpa, laughing so hard his hat fell off.\n\nTerry did a spin. The cheese flew out sideways. Terry did a bow. A tomato pom-pom popped off and rolled into the grass, and a toddler in a pea pod solemnly rolled it back. Terry wiggled faster. The laughs got bigger. A baby laughed so hard she got the hiccups, and then everyone laughed at the hiccups, and Terry took a bow for the hiccups too.\n\nMaximum laughs per dollar. That was Terry's motto, though he had never said it out loud, because he was a taco, and tacos are humble.\n\nAfter the parade, after the trophies for scariest and cutest and most creative, the teacher gave Terry a special ribbon. It said Silliest, in big gold letters. Terry wore it on his shell all the way home, very proud.\n\nThat night, Terry settled into bed, shell and all. The lettuce stopped tickling. The cheese lay still like a blanket. The tomatoes rested.\n\n\"Being silly is hard work,\" yawned Terry. And he was asleep before his head hit the pillow, dreaming of parades, dreaming of laughter, the silliest taco in the world.",
  "blue-alien-ohana": "Kiko came from very far away. Past the moon, past the stars you know the names of, past the stars nobody has named yet. His skin was blue, his eyes were big, and his ears, oh, his ears were enormous. They heard everything.\n\nWhen Kiko's spaceship landed softly in a backyard in Hawaii, he was excited and also a little lonely. Everything was new. The air smelled like flowers and rain. The ocean went shhhh in the distance. He missed home.\n\nA little girl found him behind the banana tree. She was not scared, not even a little. \"You have big ears,\" she said.\n\n\"They hear everything,\" said Kiko sadly. \"That is the problem. I hear everything, and I do not know which sounds mean home.\"\n\nThe girl thought about this. Then she took his hand. \"I will teach you,\" she said.\n\nShe taught him the sound of the screen door, which meant someone you love is coming in. She taught him the rice cooker song, which meant dinner soon. She taught him the rain on the roof, which meant cozy. She taught him her grandmother's laugh, which meant everything is all right.\n\nKiko listened with his great big ears, and one by one, the sounds stopped being strange and started being home.\n\n\"Ohana means family,\" the girl told him. \"Family means nobody gets left behind. Even aliens. Especially aliens.\"\n\nThat night, Kiko lay in the hammock, listening. Screen door. Distant ocean. The little girl breathing softly in her sleep nearby. His enormous ears drooped, slowly, sleepily, like flowers closing at dusk.\n\nHe had traveled past a million stars to learn the best sound in the universe. It was the sound of belonging. Goodnight, Kiko. Goodnight, ohana.",
  "emerald-witch": "Emerald was a witch, and everything about her was green. Her dress was green. Her hat was green. Her boots were green, and they squeaked. She lived in a cottage covered in vines, and she collected green things: leaves, bottle caps, smooth sea glass, and frog songs, which she kept in a jar with holes in the lid so they could breathe.\n\nOther witches did spells with smoke and thunder. Emerald did spells with seeds.\n\n\"Watch,\" she would say, pressing a seed into the dark earth. She would whisper to it, not a magic word, just encouragement, the way you whisper to a friend. And the seed would listen. A sprout would push up, then a stem, then leaves, green as her boots.\n\nHer garden was the most magical place in the county. Moonflowers that glowed. Pumpkins the size of armchairs. Tomatoes so red the other witches were jealous, though they pretended not to be.\n\nBut Emerald's proudest magic was a seed she had saved for years, a wrinkled silver seed in a velvet pouch. \"What does it grow?\" the children asked.\n\n\"You will see,\" said Emerald. \"It only blooms for one reason.\"\n\nOn the last night of October, Emerald planted the silver seed in a pot by a child's window. She whispered to it, and she waited. And as the child's breathing slowed, and slowed, and settled into sleep, the seed trembled, and split, and bloomed.\n\nA moonflower, silver and glowing, opening one petal at a time, just for the moment a child falls asleep.\n\n\"That,\" whispered Emerald, \"is the whole spell. Everything I grow is just practice for this.\"\n\nShe pulled her green cloak around her shoulders and walked home under the stars, boots squeaking softly. Behind her, the moonflower glowed all night long. Goodnight, Emerald. Goodnight, garden."
};
  /* 2026-09-30 delight: path template only, not a narration claim. A tale
     counts as narrated only when probeNarr() verifies the file at the served
     path (see isNarrated). The MP3s live in hour-session/tales-audio, so the
     served probe fails and the player uses the browser voice. */
  var PILOT_AUDIO = {};
  Object.keys(PILOT_TALES).forEach(function(s){ PILOT_AUDIO[s] = "audio/storytime/" + s + ".mp3"; });
  /* ARCHIVED 2026-09-29: the assembled-tale path below is retired from
     the Storytime player, which now carries only the 10 narrated signature tales.
     Kept here for reference; a future expansion can re-enable it per-costume. */
  function taleFor(idea){
    var p = (typeof MAKE_PLANS !== "undefined") ? MAKE_PLANS[idea.id] : null;
    if (PILOT_TALES[idea.id]) return PILOT_TALES[idea.id];
    var tale = "Tonight's tale: " + idea.title + ". " + idea.why;
    if (p && p.buy && p.buy.length){
      tale += " To dress up as " + idea.title + ", you'll need " + p.buy.slice(0,3).join(", ") + ".";
    }
    if (p && (p.time || p.cost)){
      tale += " It takes " + (p.time || "some time") + " and costs " + (p.cost || "a few dollars") + ".";
    }
    return tale;
  }
  /* 2026-09-30 delight: no shuffle, ever. The player order matches the card
     order (and the channel's hand-defined order); deep links set the index,
     never reorder the list. The old shuffle() is retired with it. */
  function metaFor(idea){
    var t = PILOT_TALES[idea.id] || "";
    var words = t ? t.split(/\s+/).length : 0;
    var mins = Math.max(1, Math.round(words / 150));
    return "About " + mins + " minute" + (mins === 1 ? "" : "s");
  }

  function ideaById(id){ for (var k=0;k<IDEAS.length;k++) if (IDEAS[k].id===id) return IDEAS[k]; return null; }
  function buildOrder(channelId){
    var ch = CHANNELS[0];
    for (var i=0;i<CHANNELS.length;i++) if (CHANNELS[i].id===channelId) ch = CHANNELS[i];
    var list = [];
    for (var s2=0;s2<ch.slugs.length;s2++){ var it = ideaById(ch.slugs[s2]); if (it) list.push(it); }
    return {ch:ch, list:list};
  }

  /* 2026-09-30 delight: audio is guilty until proven innocent. No "Narrated"
     label and no narration attempt unless the tale's MP3 exists at the served
     path AND reports an audio content type. Probed per player open, per tale;
     the MP3s live in hour-session/tales-audio only, so every tale fails the
     check and the player uses the browser-voice path with the normal 15s
     timer. narrOK defaults to false (missing file, fetch error, wrong type). */
  var narrOK = {};
  function probeNarr(){
    for (var i=0;i<PILOT_ORDER.length;i++){
      (function(slug){
        if (narrOK[slug]) return;
        try {
          fetch("audio/storytime/" + slug + ".mp3", {method:"HEAD"}).then(function(r){
            var ct = "";
            try { ct = r.headers.get("content-type") || ""; } catch(e2){}
            narrOK[slug] = !!(r && r.ok && /^audio\//i.test(ct));
            if (narrOK[slug]){ try { Analytics.track("storytime_narr_verified", {costume: slug}); } catch(e3){} }
          }, function(){ narrOK[slug] = false; });
        } catch(e){ narrOK[slug] = false; }
      })(PILOT_ORDER[i]);
    }
  }
  function isNarrated(idea){ return !!(idea && narrOK[idea.id]); }
  var narrAudio = null, narrSlide = null, narratedHold = false;
  function stopNarr(){ try { if (narrAudio) narrAudio.pause(); } catch(e){} }
  /* 2026-09-30 audio fix: every stopSpeak bumps ttsGen so stale utterance
     callbacks (cancel races, onend from a killed utterance) can never
     restart or double-speak audio. */
  var ttsGen = 0, ttsOK = true;
  function stopSpeak(){
    ttsGen++;
    narratedHold = false;
    try { if (window.speechSynthesis) window.speechSynthesis.cancel(); } catch(e){} stopNarr();
  }
  function audioUnavailable(){
    ttsOK = false;
    try {
      var b = $("st-sound");
      b.setAttribute("aria-disabled", "true");
      b.style.opacity = "0.35";
    } catch(e){}
    try { Analytics.track("storytime_tts_unavailable", {}); } catch(e2){}
  }
  /* 2026-09-30 audio fix: cache voices on voiceschanged. On iOS the voice
     list is empty at first call; picking from an empty list left utterances
     voiceless (and sometimes silent). */
  var synthVoices = [];
  function cacheVoices(){
    try {
      var v = window.speechSynthesis.getVoices();
      if (v && v.length) synthVoices = v;
    } catch(e){}
  }
  try {
    if (window.speechSynthesis){
      cacheVoices();
      window.speechSynthesis.onvoiceschanged = cacheVoices;
    } else { audioUnavailable(); }
  } catch(e){}
  function setBarDur(s){ try { $("st-bar").style.transitionDuration = s ? (s + "s") : ""; } catch(e){} }
  function pickVoice(){
    try {
      var synth = window.speechSynthesis;
      if (!synth) return null;
      var vs = (synthVoices.length ? synthVoices :
        (synth.getVoices ? synth.getVoices() : [])).filter(function(v){ return v && /^en([-_]|$)/i.test(v.lang || ""); });
      if (!vs.length) return null;
      function score(v){
        var n = ((v.name || "") + " " + (v.voiceURI || "")).toLowerCase();
        var s = 0;
        if (n.indexOf("siri") > -1) s += 4;
        if (n.indexOf("natural") > -1 || n.indexOf("neural") > -1) s += 3;
        if (n.indexOf("enhanced") > -1 || n.indexOf("premium") > -1) s += 2;
        if (v.localService) s += 1;
        if (/^en[-_]us/i.test(v.lang || "")) s += 1;
        if (n.indexOf("compact") > -1) s -= 3;
        if (n.indexOf("robot") > -1) s -= 5;
        return s;
      }
      vs.sort(function(a, b){ return score(b) - score(a); });
      return vs[0];
    } catch(e){ return null; }
  }
  /* 2026-09-30 audio fix: iOS stalls long utterances, so tales are chunked
     into sentence-boundary pieces chained via onend. resume() first (iOS
     leaves the synth paused), a short delay after cancel() (the cancel-then-
     speak race silently drops utterances), and narratedHold suppresses the
     15s auto-advance until the final onend, which advances the slide. */
  function chunkTale(text){
    var parts = String(text || "").split(/\n\n+/);
    var out = [];
    parts.forEach(function(p){
      p = p.trim();
      if (!p) return;
      var sents = p.match(/[^.!?]+[.!?]+["']?\s*|\S[^.!?]*$/g) || [p];
      var buf = "";
      sents.forEach(function(s){
        s = s.trim();
        if (!s) return;
        if ((buf + " " + s).length > 400){ out.push(buf.trim()); buf = s; }
        else buf = buf ? buf + " " + s : s;
      });
      if (buf.trim()) out.push(buf.trim());
    });
    return out.length ? out : [String(text || "")];
  }
  /* 2026-09-30 (Billy phone QA): `immediate` skips the 120ms cancel-then-
     speak delay on user-gesture paths (speaker-button tap, play-resume tap,
     next/prev taps). iOS drops speechSynthesis.speak() issued outside the
     tap gesture, so the deferred path stays only for timer-driven
     auto-advance. */
  function speakSynth(text, immediate){
    var gen = ++ttsGen;
    try {
      var synth = window.speechSynthesis;
      if (!synth || !window.SpeechSynthesisUtterance){ audioUnavailable(); return; }
      try { if (synth.paused) synth.resume(); } catch(e){}
      var v = pickVoice();
      var chunks = chunkTale(text);
      var i = 0;
      try { synth.cancel(); } catch(e){}
      narratedHold = true;
      if (immediate){
        if (!speakOn || !playing){ narratedHold = false; return; }
        speakChunk();
      } else {
        setTimeout(function(){
          if (gen !== ttsGen) return;
          if (!speakOn || !playing){ narratedHold = false; return; }
          speakChunk();
        }, 120);
      }
      function speakChunk(){
        if (gen !== ttsGen) return;
        if (i >= chunks.length || !speakOn || !playing){
          narratedHold = false;
          if (i >= chunks.length && gen === ttsGen && playing && speakOn) next();
          return;
        }
        var u;
        try { u = new SpeechSynthesisUtterance(chunks[i]); }
        catch(e){ narratedHold = false; audioUnavailable(); return; }
        u.rate = 0.95;
        u.lang = "en-US";
        if (v) u.voice = v;
        u.onend = function(){ if (gen !== ttsGen) return; i++; speakChunk(); };
        u.onerror = function(ev){
          if (gen !== ttsGen) return;
          narratedHold = false;
          try { Analytics.track("storytime_tts_error", {error: (ev && ev.error) || "unknown", chunk: i}); } catch(e2){}
        };
        try { synth.speak(u); }
        catch(e){ narratedHold = false; audioUnavailable(); }
      }
    } catch(e){ narratedHold = false; audioUnavailable(); }
  }
  /* Prerecorded narration for the ten pilot tales. The slide holds until the
     audio ends, then advances. Any failure falls back to the browser voice
     plus the normal 15s timer, so a missing MP3 never silences a tale. */
  function speakNarr(idea, fromGesture){
    try {
      if (!narrAudio){
        narrAudio = new Audio();
        narrAudio.preload = "auto";
        narrAudio.addEventListener("ended", function(){
          narratedHold = false;
          if (playing && speakOn) next();
        });
        narrAudio.addEventListener("loadedmetadata", function(){
          if (narrAudio.duration && isFinite(narrAudio.duration)) setBarDur(narrAudio.duration);
        });
        narrAudio.addEventListener("error", function(){
          if (narrSlide && order[idx] && order[idx].id === narrSlide){
            var slug = narrSlide;
            narrAudio = null; narrSlide = null; narratedHold = false; setBarDur(0);
            try { Analytics.track("storytime_narr_fallback", {costume: slug, reason: "error"}); } catch(e){}
            speakSynth(taleFor(order[idx]), fromGesture); arm();
          }
        });
      }
      if (narrSlide !== idea.id){ narrAudio.src = PILOT_AUDIO[idea.id]; narrSlide = idea.id; }
      narratedHold = true;
      setBarDur(150);
      var pr = narrAudio.play();
      if (pr && pr.catch) pr.catch(function(){
        narrAudio = null; narrSlide = null; narratedHold = false; setBarDur(0);
        try { Analytics.track("storytime_narr_fallback", {costume: idea.id, reason: "play_rejected"}); } catch(e){}
        speakSynth(taleFor(idea), fromGesture); arm();
      });
    } catch(e){
      narrAudio = null; narrSlide = null; narratedHold = false; setBarDur(0);
      speakSynth(taleFor(idea), fromGesture);
    }
  }
  function speakTale(text, idea, fromGesture){
    stopSpeak();
    setBarDur(0);
    /* Paused means silent: advancing or toggling sound while paused must not
       start audio behind the user's back. Resume re-renders and continues. */
    if (!speakOn || !playing){ narratedHold = false; return; }
    if (isNarrated(idea)) speakNarr(idea, fromGesture);
    else { narratedHold = false; speakSynth(text, fromGesture); }
  }

  function render(fromGesture){
    var idea = order[idx];
    if (!idea) return;
    var tale = taleFor(idea);
    $("st-photo").src = "photos/" + idea.id + ".webp";
    pmcSrcset($("st-photo"), idea.id, "100vw");
    $("st-photo").alt = idea.title + " costume";
    $("st-kicker").textContent = currentLabel;
    $("st-title").textContent = idea.title;
    $("st-tale").textContent = tale;
    $("st-meta").textContent = metaFor(idea);
    $("st-count").textContent = (idx+1) + " of " + order.length;
    $("st-build").href = "/c/" + idea.id;
    var bar = $("st-bar");
    bar.classList.remove("run");
    void bar.offsetWidth;
    if (playing && !reduceMotion) bar.classList.add("run");
    var ph = $("st-photo");
    ph.classList.remove("kb"); ph.classList.remove("kb-rev");
    void ph.offsetWidth;
    var bot = $("st-bottom");
    bot.classList.remove("rise");
    void bot.offsetWidth;
    if (!reduceMotion){
      ph.classList.add(kbFlip ? "kb-rev" : "kb"); kbFlip = !kbFlip;
      bot.classList.add("rise");
    }
    speakTale(tale, idea, fromGesture);
    try { var nx = order[(idx+1)%order.length]; var im = new Image(); im.src = "photos/" + nx.id + ".webp"; } catch(e){}
    Analytics.track("storytime_slide", {n: idx+1, costume: idea.id, channel: currentId, narrated: isNarrated(idea)});
  }

  function arm(){
    if (timer) { clearInterval(timer); timer = null; }
    if (playing && !reduceMotion && !narratedHold && order.length > 1){
      timer = setInterval(function(){ if (!document.hidden) next(); }, ADV_MS);
    }
  }
  /* 2026-09-30 delight: the URL always names the on-screen tale, so deep
     links and back/forward stay honest. replaceState (not pushState): the
     back button exits the player instead of stepping through slides. */
  function storyUrl(slug){
    return location.pathname + "?storytime&costume=" + slug;
  }
  function syncStoryUrl(){
    try {
      if (order[idx] && window.history && history.replaceState)
        history.replaceState(null, "", storyUrl(order[idx].id));
    } catch(e){}
  }
  function clearStoryUrl(){
    try {
      if (window.history && history.replaceState)
        history.replaceState(null, "", location.pathname);
    } catch(e){}
  }
  function next(fromGesture){ idx = (idx+1) % order.length; render(fromGesture); arm(); syncStoryUrl(); }
  function prev(fromGesture){ idx = (idx-1+order.length) % order.length; return render(fromGesture), arm(), syncStoryUrl(); }

  /* 2026-09-30 (Billy phone QA): storytime opens fully at rest -- slideshow
     paused (big button reads "Play") and narration off. Two explicit play
     affordances: the Play button starts the 15s auto-advance, the speaker
     button starts read-aloud. reduceMotion keeps its paused default. */
  function open(channelId, startSlug, viaGesture){
    var built = buildOrder(channelId);
    if (!built.list.length) return;
    currentId = built.ch.id;
    currentLabel = built.ch.id === "all" ? "Storytime" : "Storytime: " + built.ch.label;
    order = built.list;
    idx = 0;
    if (startSlug){
      /* 2026-09-30 delight: a deep link starts AT the tale, in editorial
         order. The old unshift() moved the tale to the front, breaking the
         card order for every other slide. */
      for (var i=0;i<order.length;i++) if (order[i].id === startSlug){ idx = i; break; }
    }
    probeNarr();
    $("st-channels").hidden = true;
    show("s-storytime");
    document.body.classList.add("st-open");
    playing = false;
    $("st-play").textContent = "Play";
    $("st-play").setAttribute("aria-label", "Play slideshow");
    speakOn = false;
    $("st-sound").setAttribute("aria-pressed", "false");
    if (!started){ started = true; Analytics.track("storytime_started", {channel: currentId, via: startSlug ? "costume_link" : "channel", audio: speakOn ? "on" : "off"}); }
    render(); arm(); syncStoryUrl();
  }
  function renderChannels(){
    var box = $("st-chanlist");
    box.innerHTML = "";
    CHANNELS.forEach(function(ch){
      var n = ch.slugs.length;
      var b = document.createElement("button");
      b.type = "button"; b.className = "st-chan";
      b.innerHTML = esc(ch.label) + "<small>" + esc(ch.sub) + " \u00b7 " + n + "</small>";
      b.onclick = (function(id){ return function(){ open(id, null, true); }; })(ch.id);
      box.appendChild(b);
    });
  }
  function openPicker(){
    renderChannels();
    $("st-channels").hidden = false;
    show("s-storytime");
  }
  function close(){
    stopSpeak();
    if (timer){ clearInterval(timer); timer = null; }
    started = false;
    clearStoryUrl();
    document.body.classList.remove("st-open");
    show("s-hero");
  }

  var heroCard = $("storycard-hero");
  if (heroCard) heroCard.addEventListener("click", function(e){
    e.preventDefault();
    openPicker();
  });
  $("st-close").onclick = close;
  $("st-next").onclick = function(){ next(true); };
  $("st-prev").onclick = function(){ prev(true); };
  $("st-play").onclick = function(){
    playing = !playing;
    this.textContent = playing ? "Pause" : "Play";
    this.setAttribute("aria-label", playing ? "Pause slideshow" : "Play slideshow");
    /* Pause silences everything (no re-render, so narration does not restart).
       Resume re-renders: narration continues from its pause point, the
       browser voice re-reads the slide as before. Resume is a tap gesture,
       so speech starts immediately (iOS). */
    if (!playing) stopSpeak();
    else render(true);
    arm();
  };
  $("st-sound").onclick = function(){
    speakOn = !speakOn;
    this.setAttribute("aria-pressed", speakOn ? "true" : "false");
    /* Explicit play: the tap is a user gesture, so speech starts
       synchronously (iOS drops deferred speechSynthesis.speak). */
    if (speakOn && order.length) speakTale(taleFor(order[idx]), order[idx], true);
    else stopSpeak();
    arm();
  };
  $("st-build").onclick = function(){
    var idea = order[idx];
    Analytics.track("storytime_build_tap", {costume: idea ? idea.id : "", channel: currentId});
  };
  document.addEventListener("keydown", function(e){
    var st = $("s-storytime");
    if (!st || !st.classList.contains("on")) return;
    if (e.key === "Escape") close();
    else if (e.key === "ArrowRight") next();
    else if (e.key === "ArrowLeft") prev();
    else if (e.key === " "){ e.preventDefault(); $("st-play").click(); }
  });
  document.addEventListener("visibilitychange", function(){
    if (document.hidden) stopSpeak();
  });

  /* Deep link: /storytime?costume=<slug> redirects here as ?storytime&costume=<slug>. */
  function openFromUrl(){
    var q = location.search || "";
    if (!/[?&]storytime([&=]|$)/.test(q)) return;
    var cm = /[?&]costume=([a-z0-9-]+)/.exec(q);
    var slug = cm ? cm[1] : null;
    var ok = slug && PILOT_ORDER.indexOf(slug) >= 0;
    if (slug && ok) open("all", slug);
    else openPicker();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", openFromUrl);
  else openFromUrl();
})();

    /* 2026-09-26 costume roulette: ?spin=<sender idea slug> rides the spin
       share link so the recipient banner can name the spin result. */
    var spm = /[?&]spin=([a-z0-9-]+)/.exec(location.search || "");
    if (spm) SPIN_IDEA_ID = spm[1];
    /* 2026-09-26 wrapped W1 fix: ?wpick=<sender idea slug> rides the
       wrapped share link so the recipient banner can name the sharer's
       pick + rank. */
    var wpm = /[?&]wpick=([a-z0-9-]+)/.exec(location.search || "");
    if (wpm) WRAPPED_PICK_ID = wpm[1];
    /* 2026-09-26 party link experiment: ?party=<6-char code> carries the
       group broadcast share; ?theme=, ?pname=, ?taken=, ?claim= ride along. */
    PARTY_PARAMS = partyParseParams();
    /* 2026-09-26 guess-game experiment: ?g=<5 base36 digits>.<idea slug>
       carries the sender's answers. Decoded only with the flag on; garbage
       yields null and the arrival falls through to the generic banner. */
    var ggm = /[?&]g=([0-9a-z]{5}\.[a-z0-9-]+)/.exec(location.search || "");
    if (ggm) GUESS_GAME = guessDecode(ggm[1]);
    /* 2026-09-26 friend-challenge experiment: ?o=challenge&chl=<sender pick
       slug> decodes to the challenge pick (recipient side); a
       ?o=challengeresult&r=<score>&rp=<pick slug> arrival decodes to the
       score payload (sharer side). Both decode only with the flag on;
       garbage yields null and the arrival falls through to the generic
       friend banner, exactly as before the experiment existed. */
    CHALLENGE_PICK_ID = challengeDecodePick(location.search || "");
    CHALLENGE_RESULT = challengeDecodeResult(location.search || "");
    var m = /[?&]idea=([a-z0-9-]+)/.exec(location.search || "");
    if (!m) return;
    var idea = null;
    IDEAS.forEach(function(it){ if (it.id === m[1]) idea = it; });
    if (!idea) return;
    /* 2026-09-28 rail smoothing: a bare ?idea=<slug> (only idea/from/probe
       params, no share id and no experiment params) is on-site navigation
       from a homepage rail or a direct link. Open the dark in-app detail
       directly instead of the hero + landing card, so the journey stays
       dark end to end. Share arrivals (?s=) and experiment landings keep the
       existing banner/card flow below. */
    (function(){
      var q = location.search || "";
      if (isGenuineShareArrival(q)) return;
      var clean = q.replace(/[?&](idea|from|probe)=[^&]*/g, "");
      if (/[a-z0-9]+=/.test(clean)) return; /* other params: existing flow */
      var pt = "From browsing";
      var fm = /[?&]from=([a-z-]+)/.exec(q);
      if (fm){
        if (fm[1] === "rail-new") pt = "New this week";
        else if (fm[1] === "rail-tonight") pt = "Make tonight";
        else if (fm[1] === "hero" || fm[1] === "rail") pt = "Trending now";
      }
      try { openIdeaDetail(idea.id, null, "s-hero", pt); } catch(e){}
      /* 2026-09-28: the from tag did its job (the context line above). Scrub
         it from the visible URL so shared/copied links stay clean; the page
         state is already set and nothing downstream re-reads it. */
      try {
        var _u = new URL(location.href);
        if (_u.searchParams.has("from")){
          _u.searchParams.delete("from");
          var _qs = _u.searchParams.toString();
          history.replaceState(null, "", _u.pathname + (_qs ? "?" + _qs : "") + _u.hash);
        }
      } catch(e){}
    })();
    if ($("s-detail") && $("s-detail").classList.contains("on")) return;
    /* 2026-09-25 challenge mechanic (arm D): ?ch=1 means the sharer claimed
       they can make this tonight with stuff they own. The claim was computed
       at share time; the landing only mirrors it and dares the recipient to
       check their own pantry. The /c/ function preserves all query params
       across the redirect, so ch=1 survives. Non-challenge landings below are
       untouched. */
    var chm = /[?&]ch=1(?:&|$)/.exec(location.search || "");
    /* 2026-09-26 arm D store-run tier: &ch=2 is the store-run dare. Same dare
       UX as &ch=1 (the recipient checks their own pantry against the pick);
       only the headline names the store run. */
    var chm2 = /[?&]ch=2(?:&|$)/.exec(location.search || "");
    var box = document.createElement("div");
    box.className = "card";
    box.style.marginBottom = "16px";
    var im = ideaMedia(idea);
    var h = document.createElement("h3");
    /* 2026-09-25 recipient-handoff experiment: preserve the social context
       and ask the reciprocal question up front. Metric: recipient quiz
       starts per recipient_landing_viewed. 2026-09-25 bugfix: the friend
       headline renders only on genuine share arrivals (see
       shareLandingHeadline); homepage proof-rail taps show the title. */
    h.textContent = shareLandingHeadline(idea, location.search || "");
    var p = document.createElement("p");
    p.className = "blurb";
    p.textContent = idea.blurb;
    var b = document.createElement("button");
    b.type = "button";
    b.className = "cta";
    b.style.width = "100%";
    b.style.marginTop = "10px";
    /* 2026-09-26 pair-share: a recipient arriving to match a friend's pick
       gets the match ask on the primary CTA. Unknown slugs keep the default. */
    var _pairFor = (VIA_SHARE_ORIGIN === "pair" && typeof PAIR_IDEA_ID !== "undefined" && PAIR_IDEA_ID) ? pairIdeaById(PAIR_IDEA_ID) : null;
    b.textContent = (chm || chm2) ? "See what YOU can make" : (_pairFor ? "Find YOUR costume to match" : "What are you going as? Find my costume");
    b.onclick = function(){
      state = {qi: 0, answers: {}};
      clearK("pmc_pick_v1");
      /* E29: a quiz started from a shared landing attributes to the share id
         + origin, so friend-quiz-starts are measurable per share origin. */
      Analytics.track("quiz_started", viaShareProps());
      renderQ();
    };
    /* E17: the landing was quiz-or-nothing. A recipient who will not take a
       quiz can still browse; the browse screen now has its own quiz door
       (E16), so this is a loop, not a leak. */
    var bb = document.createElement("button");
    bb.type = "button";
    bb.className = "ghost";
    bb.style.width = "100%";
    bb.style.marginTop = "8px";
    bb.textContent = "Or browse all ideas";
    bb.onclick = function(){
      /* 2026-09-27 red-team: a recipient who browses instead of quizzing was
         unattributable -- landing_browse carried no via_share_id, so the
         share's browse leg never showed in the funnel. Additive: on
         non-share ?idea= arrivals viaShareProps() returns {}, unchanged. */
      Analytics.track("landing_browse", viaShareProps());
      openBrowse();
    };
    box.appendChild(im); box.appendChild(h); box.appendChild(p);
    /* 2026-09-26 red-team: a duel share recipient who taps the /c/ page's
       top banner CTA lands here (?idea= + ?duel=) with no duel entry -- the
       duel banner is suppressed on ?idea= landings, so the duel died on the
       most prominent tap target. A valid duel slug gets its own entry button
       ahead of the full-quiz CTA. */
    var _duelFor = (typeof duelIdeaById === "function" && typeof DUEL_IDEA_ID !== "undefined" && DUEL_IDEA_ID) ? duelIdeaById(DUEL_IDEA_ID) : null;
    if (_duelFor){
      var dbtn = document.createElement("button");
      dbtn.type = "button";
      dbtn.className = "cta";
      dbtn.style.width = "100%";
      dbtn.style.marginTop = "10px";
      dbtn.textContent = duelKidFrame(_duelFor) ? "Compare costumes: answer 2 questions" : "Duel " + _duelFor.title + ": answer 2 questions";
      dbtn.onclick = function(){ duelQuickCompare(_duelFor); };
      box.appendChild(dbtn);
    }
    /* 2026-09-25 recipient-handoff experiment: the quiz CTA comes before the
       build guide. A recipient who gets the full guide first can leave
       satisfied without ever participating. The guide stays one tap away,
       collapsed, and opening it still tracks build_steps_viewed. */
    box.appendChild(b); box.appendChild(bb);
    if (chm){
      /* Challenge landing only: the dare is "what can YOU make" -- the pantry
         page is the honest answer path. */
      var pb = document.createElement("button");
      pb.type = "button";
      pb.className = "ghost";
      pb.style.width = "100%";
      pb.style.marginTop = "8px";
      pb.textContent = "What do I have at home?";
      pb.onclick = function(){ location.href = "/pantry?for=" + encodeURIComponent(idea.id) + (VIA_SHARE ? "&s=" + VIA_SHARE : ""); };
      box.appendChild(pb);
    }
    var _howtoS = buildInstructions(idea, {via: "share_landing"});
    if (_howtoS) box.appendChild(_howtoS);
    var hero = $("s-hero");
    hero.insertBefore(box, hero.firstChild);
    /* Recipient-channel inference (analytics only, no UX change). The Web
       Share API never reveals the destination app at share time, so this is
       open-time inference from the UA: Messenger/WhatsApp in-app browsers
       tag their UAs; iMessage opens look like plain Safari and are
       indistinguishable, logged as safari_unknown. */
    var _rlv = {idea_id: idea.id, recipient_channel: recipientChannel()};
    if (chm || chm2){ _rlv.challenge_landing = true; _rlv.challenge_kind = chm2 ? "store-run" : "pantry-zero"; }
    /* The share this recipient arrived through is via_share_id (not share_id:
       share_id is reserved for the id a share CREATES). This lets one share be
       traced share_created.share_id -> recipient_landing_viewed.via_share_id. */
    if (VIA_SHARE) _rlv.via_share_id = VIA_SHARE;
    if (VIA_SHARE_ORIGIN) _rlv.share_origin = VIA_SHARE_ORIGIN;
    /* 2026-09-25 attribution fix: recipient_landing_viewed fires ONLY on
       genuine shared-link arrivals. Normal on-site ?idea=<slug> navigation
       (proof rail, direct, browse) must never count as a recipient landing;
       the old code fired on every ?idea= pageview and polluted the series. */
    if (isGenuineShareArrival(location.search || "")) Analytics.track("recipient_landing_viewed", _rlv);
    /* 2026-09-26 split-the-build: ?sp=<builders> marks arrivals from a /c/
       guide's "Split the build" link. The /c/ page has no analytics loader,
       so this is the measurable recipient leg of the split loop. Gated on a
       genuine share id exactly like recipient_landing_viewed. */
    var _spm = /[?&]sp=([2-8])(?:&|$)/.exec(location.search || "");
    if (_spm && isGenuineShareArrival(location.search || "")) Analytics.track("build_split_link_opened",
      {idea_id: idea.id, builders: parseInt(_spm[1], 10), via_share_id: VIA_SHARE, share_origin: VIA_SHARE_ORIGIN});
  })();
  /* 2026-09-26 red-team: a recipient who taps the /c/ page banner's
     "Find your costume" lands at /?s=<sid>&o=<origin> with NO friend
     context -- the hero read like a cold visit and the social loop leaked.
     When ?s= is present but there is no ?idea= / ?pick= landing (those have
     their own friend copy), show a small recipient banner above the hero so
     the social context survives the tap-through. One tap starts the quiz. */
  (function(){
    if (!VIA_SHARE) return;
    var q = location.search || "";
    if (/[?&](idea|pick|ch)=/.test(q)) return;
    var hero = $("s-hero");
    if (!hero || $("pmc-friend-banner")) return;
    /* 2026-09-26 teaser share: the sender withheld their pick (?o=teaser),
       so this banner must NOT reveal it -- no duel banner, no pick name.
       The full quiz is the dare; the results-page duel box reveals the
       friend's pick in the You-vs-friend compare after the recipient has
       their own pick. Fires recipient_landing_viewed here because the
       ?idea= block (the only other place that fires it) never runs on a
       bare /?s= arrival; without this the teaser funnel has no open rate. */
    /* 2026-09-26 party link experiment: ?o=party arrivals get the party
       banner (host intake, returning-host board, or guest invite, handled
       inside renderPartyBanner). With the flag off this never matches, so
       party links fall through to the generic banner exactly as before. */
    if (VIA_SHARE_ORIGIN === "party" && PARTY_LINK_ENABLED && PARTY_PARAMS && PARTY_PARAMS.code){
      renderPartyBanner(hero);
      return;
    }

    /* 2026-09-26 friend-challenge experiment: a ?o=challengeresult arrival is
       the loop closing -- the sharer opened a friend's score-back link. The
       score is recorded into the localStorage inbox and the inbox panel
       renders in the hero. With the flag off CHALLENGE_RESULT is always
       null, so the arrival falls through to the generic friend banner,
       exactly as before. */
    if (typeof CHALLENGE_RESULT !== "undefined" && CHALLENGE_RESULT){
      var cip = buildChallengeInboxPanel();
      if (cip){
        hero.insertBefore(cip, hero.firstChild);
        if (isGenuineShareArrival(location.search || "")) Analytics.track("recipient_landing_viewed", Object.assign({recipient_channel: recipientChannel()}, viaShareProps()));
        return;
      }
    }
    /* 2026-09-26 friend-challenge experiment: genuine ?o=challenge&chl=
       arrivals get the challenge banner naming the sender's pick. The
       friend takes the normal quiz; the match score renders on the results
       screen via CHALLENGE_PICK_ID. Unknown slugs fall through to the
       generic friend banner. With the flag off the pick never decodes, so
       nothing renders differently. */
    var _chlTheirs = (typeof CHALLENGE_PICK_ID !== "undefined" && CHALLENGE_PICK_ID) ? challengeIdeaById(CHALLENGE_PICK_ID) : null;
    if (_chlTheirs){
      var cb = document.createElement("button");
      cb.type = "button";
      cb.id = "pmc-challenge-banner";
      cb.style.cssText = "display:block;width:100%;text-align:left;font:inherit;color:inherit;background:#fff7ec;border:1px solid #ffd9a3;border-radius:14px;padding:12px 14px;margin:0 0 14px;cursor:pointer";
      cb.innerHTML = "<p style=\"margin:0 0 4px;font-weight:700;color:#333;line-height:1.4\">Costume challenge: your friend was picked " + _chlTheirs.title + ".</p>" +
        "<p style=\"margin:0;font-size:14px;color:#666;line-height:1.4\">Would you pick the same? Take the 2-minute quiz and send them your match score.</p>";
      cb.onclick = function(){
        state = {qi: 0, answers: {}};
        state.pinpoint = null;
        pinpointNote(""); pinpointClearNomatch();
        clearK("pmc_pick_v1");
        Analytics.track("quiz_started", viaShareProps());
        renderQ();
      };
      hero.insertBefore(cb, hero.firstChild);
      if (isGenuineShareArrival(location.search || "")) Analytics.track("recipient_landing_viewed", Object.assign({recipient_channel: recipientChannel()}, viaShareProps()));
      return;
    }
    /* 2026-09-26 pair-share: genuine ?o=pair arrivals get the match banner.
       The sender's pick IS the hook (unlike the teaser), so it names the
       costume. One tap starts the full quiz; the results page renders the
       "How you two pair up" panel via PAIR_IDEA_ID. Unknown slugs fall
       through to the duel/generic banners. Fires recipient_landing_viewed
       here because the ?idea= block never runs on a bare /?s= arrival. */
    var _pairTheirs = (VIA_SHARE_ORIGIN === "pair" && typeof PAIR_IDEA_ID !== "undefined" && PAIR_IDEA_ID) ? pairIdeaById(PAIR_IDEA_ID) : null;
    if (_pairTheirs){
      var pb = document.createElement("button");
      pb.type = "button";
      pb.id = "pmc-friend-banner";
      pb.style.cssText = "display:block;width:100%;text-align:left;font:inherit;color:inherit;background:#fff7ec;border:1px solid #ffd9a3;border-radius:14px;padding:12px 14px;margin:0 0 14px;cursor:pointer";
      pb.innerHTML = "<p style=\"margin:0 0 4px;font-weight:700;color:#333;line-height:1.4\">Your friend is going as " + _pairTheirs.title + ".</p>" +
        "<p style=\"margin:0;font-size:14px;color:#666;line-height:1.4\">Take the 2-minute quiz to find YOUR costume to match. When you finish, you will see how you two pair up.</p>";
      pb.onclick = function(){
        state = {qi: 0, answers: {}};
        state.pinpoint = null;
        pinpointNote(""); pinpointClearNomatch();
        clearK("pmc_pick_v1");
        Analytics.track("quiz_started", viaShareProps());
        renderQ();
      };
      hero.insertBefore(pb, hero.firstChild);
      if (isGenuineShareArrival(location.search || "")) Analytics.track("recipient_landing_viewed", Object.assign({recipient_channel: recipientChannel()}, viaShareProps()));
      return;
    }
    /* 2026-09-26 duel: genuine ?duel= arrivals get the duel banner and the
       lightweight 2-question flow instead of the full quiz. Unknown slugs
       fall through to the generic friend banner. */
    var _duelTheirs = (typeof DUEL_IDEA_ID !== "undefined" && DUEL_IDEA_ID) ? duelIdeaById(DUEL_IDEA_ID) : null;
    if (_duelTheirs){
      var _dbKf = duelKidFrame(_duelTheirs);
    /* 2026-09-26 red-team a11y: a button, not a div with onclick, so
         keyboard and screen-reader users can activate it too. */
      var db = document.createElement("button");
      db.type = "button";
      db.id = "pmc-friend-banner";
      db.style.cssText = "display:block;width:100%;text-align:left;font:inherit;color:inherit;background:#fff7ec;border:1px solid #ffd9a3;border-radius:14px;padding:12px 14px;margin:0 0 14px;cursor:pointer";
      db.innerHTML = "<p style=\"margin:0 0 4px;font-weight:700;color:#333;line-height:1.4\">" + (_dbKf ? "Costume compare: your friend picked " : "Costume duel: your friend picked ") + _duelTheirs.title + ".</p>" +
        "<p style=\"margin:0;font-size:14px;color:#666;line-height:1.4\">Answer 2 quick questions, see how you match up, and send your pick back.</p>" +
        /* 2026-09-27 watchdog red-team: the banner read as an info card and the
           big orange "Find my costume" hero CTA below it stole the tap (sending
           recipients into the full 5-question fork instead of the 2-question
           duel). An explicit tap cue keeps the duel entry obvious. */
        "<p style=\"margin:8px 0 0;font-size:15px;font-weight:700;color:#ff8c1a;line-height:1.4\">Tap to start &rarr;</p>";
      db.onclick = function(){ duelQuickCompare(_duelTheirs); };
      hero.insertBefore(db, hero.firstChild);
      /* 2026-09-30 delight: a valid cold duel arrival is duel-first. The
         standard hero (headline, CTA, moon) hides so it cannot steal the tap;
         the rails below stay as content. */
      var stdHero = hero.querySelector(".hero");
      if (stdHero) stdHero.style.display = "none";
      /* 2026-09-26 red-team: the duel banner branch never fired
         recipient_landing_viewed, so hand-crafted /?s=&o=duel&duel= arrivals
         undercounted recipient opens. Same payload as the teaser branch. */
      if (isGenuineShareArrival(location.search || "")) Analytics.track("recipient_landing_viewed", Object.assign({recipient_channel: recipientChannel()}, viaShareProps()));
      return;
    }
    /* 2026-09-26 costume roulette: genuine ?o=spin arrivals get the spin
       banner. The sender's spin result IS the hook (like the pair share),
       so it names the costume. One tap scrolls to the roulette and spins
       for the recipient. Unknown slugs fall through to the generic banner.
       Fires recipient_landing_viewed here because the ?idea= block never
       runs on a bare /?s= arrival. */
    var _spinTheirs = (VIA_SHARE_ORIGIN === "spin" && typeof SPIN_IDEA_ID !== "undefined" && SPIN_IDEA_ID) ? spinIdeaById(SPIN_IDEA_ID) : null;
    if (_spinTheirs){
      var spb = document.createElement("button");
      spb.type = "button";
      spb.id = "pmc-friend-banner";
      spb.style.cssText = "display:block;width:100%;text-align:left;font:inherit;color:inherit;background:#fff7ec;border:1px solid #ffd9a3;border-radius:14px;padding:12px 14px;margin:0 0 14px;cursor:pointer";
      spb.innerHTML = "<p style=\"margin:0 0 4px;font-weight:700;color:#333;line-height:1.4\">Your friend let the shuffle pick and got " + _spinTheirs.title + ".</p>" +
        "<p style=\"margin:0;font-size:14px;color:#666;line-height:1.4\">Get your pick. One tap, no questions.</p>";
      spb.onclick = function(){
        startSpin("recipient-banner");
        var panel = $("spin-panel");
        if (panel && panel.scrollIntoView) panel.scrollIntoView({block: "start"});
      };
      hero.insertBefore(spb, hero.firstChild);
      if (isGenuineShareArrival(location.search || "")) Analytics.track("recipient_landing_viewed", Object.assign({recipient_channel: recipientChannel()}, viaShareProps()));
      return;
    }
    /* 2026-09-26 evening block-map experiment: genuine ?o=block arrivals
       with a valid ?map= chain see the map roster and one tap to add their
       house (starts the quiz, attributed share_origin=block). With the flag
       off blockMapEntries() is always null, so this never renders. */
    var _bmChain = (typeof VIA_SHARE_ORIGIN !== "undefined" && VIA_SHARE_ORIGIN === "block") ? blockMapEntries() : null;
    if (_bmChain){
      var bb = document.createElement("button");
      bb.type = "button";
      bb.id = "pmc-friend-banner";
      bb.style.cssText = "display:block;width:100%;text-align:left;font:inherit;color:inherit;background:#fff7ec;border:1px solid #ffd9a3;border-radius:14px;padding:12px 14px;margin:0 0 14px;cursor:pointer";
      var _bmNames = _bmChain.slice(0, 3).map(function(e){
        var it = (typeof pairIdeaById === "function") ? pairIdeaById(e.idea) : null;
        return blockMapHouseName(e.name) + " (" + (it ? it.title : "secret pick") + ")";
      });
      var _bmMore = _bmChain.length > 3 ? " and " + (_bmChain.length - 3) + " more" : "";
      bb.innerHTML = "<p style=\"margin:0 0 4px;font-weight:700;color:#333;line-height:1.4\">The block costume map is live.</p>" +
        "<p style=\"margin:0;font-size:14px;color:#666;line-height:1.4\">" + _bmNames.join(", ") + _bmMore + " are on it. Take the 2-minute quiz to get your pick and add your house.</p>";
      bb.onclick = function(){
        /* Mirror the teaser banner start exactly: clean state, no pinpoint
           residue, old picks cleared, recipient-attributed event. */
        state = {qi: 0, answers: {}};
        state.pinpoint = null;
        pinpointNote(""); pinpointClearNomatch();
        clearK("pmc_pick_v1");
        Analytics.track("quiz_started", viaShareProps());
        renderQ();
      };
      hero.insertBefore(bb, hero.firstChild);
      if (isGenuineShareArrival(location.search || "")) Analytics.track("recipient_landing_viewed", Object.assign({recipient_channel: recipientChannel()}, viaShareProps()));
      return;
    }
    /* 2026-09-26 micro-quiz share: genuine ?o=micro arrivals get the question
       itself rendered in place, not a banner leading to the quiz. One tap
       answers; the panel shows the quiz's honest one-question guess, with
       the full quiz one tap away and a share-back that re-mints a micro
       link into the same chat (the duel-style return leg). Fires
       recipient_landing_viewed here because the ?idea= block never runs on
       a bare /?s= arrival. */

    /* 2026-09-26 guess-game distribution experiment: genuine ?o=guess
       arrivals with a valid ?g= payload get the game banner. GUESS_GAME is
       null with the flag off or on garbage, so those arrivals fall through
       to the generic banner exactly as before the experiment existed.
       Fires recipient_landing_viewed here because the ?idea= block never
       runs on a bare /?s= arrival. */
    if (VIA_SHARE_ORIGIN === "guess" && GUESS_GAME){
      var ggb = document.createElement("button");
      ggb.type = "button";
      ggb.id = "pmc-friend-banner";
      ggb.style.cssText = "display:block;width:100%;text-align:left;font:inherit;color:inherit;background:#fff7ec;border:1px solid #ffd9a3;border-radius:14px;padding:12px 14px;margin:0 0 14px;cursor:pointer";
      ggb.innerHTML = "<p style=\"margin:0 0 4px;font-weight:700;color:#333;line-height:1.4\">Your friend got " + GUESS_GAME.idea.title + ".</p>" +
        "<p style=\"margin:0;font-size:14px;color:#666;line-height:1.4\">Can you guess their 5 quiz answers? Play, then get your own pick.</p>";
      ggb.onclick = function(){ openGuessGame(GUESS_GAME); };
      hero.insertBefore(ggb, hero.firstChild);
      if (isGenuineShareArrival(location.search || "")) Analytics.track("recipient_landing_viewed", Object.assign({recipient_channel: recipientChannel()}, viaShareProps()));
      return;
    }
    /* 2026-09-26 match-pair experiment: genuine ?o=match arrivals with a
       valid ?match= payload get the pair banner. MATCH_PAIR is null with
       the flag off or on garbage, so those arrivals fall through to the
       generic banner exactly as before the experiment existed. Fires
       recipient_landing_viewed here because the ?idea= block never runs on
       a bare /?s= arrival. */
    if (VIA_SHARE_ORIGIN === "match" && MATCH_PAIR){
      var mpb = document.createElement("button");
      mpb.type = "button";
      mpb.id = "pmc-friend-banner";
      mpb.style.cssText = "display:block;width:100%;text-align:left;font:inherit;color:inherit;background:#fff7ec;border:1px solid #ffd9a3;border-radius:14px;padding:12px 14px;margin:0 0 14px;cursor:pointer";
      mpb.innerHTML = "<p style=\"margin:0 0 4px;font-weight:700;color:#333;line-height:1.4\">Your friend found a costume pair.</p>" +
        "<p style=\"margin:0;font-size:14px;color:#666;line-height:1.4\">" + MATCH_PAIR.a.title + " and " + MATCH_PAIR.b.title + ". Tap to take the 2-minute quiz and find your pair.</p>";
      mpb.onclick = function(){
        state = {qi: 0, answers: {}};
        state.pinpoint = null;
        pinpointNote(""); pinpointClearNomatch();
        clearK("pmc_pick_v1");
        Analytics.track("quiz_started", viaShareProps());
        renderQ();
      };
      hero.insertBefore(mpb, hero.firstChild);
      if (isGenuineShareArrival(location.search || "")) Analytics.track("recipient_landing_viewed", Object.assign({recipient_channel: recipientChannel()}, viaShareProps()));
      return;
    }
    /* 2026-09-26 pm8 glow-up experiment: genuine ?o=glow arrivals with a
       valid ?glow= payload get the glow-up banner. GLOW_PAIR is null with
       the flag off or on garbage, so those arrivals fall through to the
       generic banner exactly as before the experiment existed. Fires
       recipient_landing_viewed here because the ?idea= block never runs on
       a bare /?s= arrival. */
    if (VIA_SHARE_ORIGIN === "glow" && GLOW_PAIR){
      var gpb = document.createElement("button");
      gpb.type = "button";
      gpb.id = "pmc-friend-banner";
      gpb.style.cssText = "display:block;width:100%;text-align:left;font:inherit;color:inherit;background:#fff7ec;border:1px solid #ffd9a3;border-radius:14px;padding:12px 14px;margin:0 0 14px;cursor:pointer";
      gpb.innerHTML = "<p style=\"margin:0 0 4px;font-weight:700;color:#333;line-height:1.4\">Your friend is glowing up this Halloween.</p>" +
        "<p style=\"margin:0;font-size:14px;color:#666;line-height:1.4\">" + GLOW_PAIR.classic.label + " last year. " + GLOW_PAIR.idea.title + " this year. Tap to take the 2-minute quiz and find your glow-up.</p>";
      gpb.onclick = function(){
        state = {qi: 0, answers: {}};
        state.pinpoint = null;
        pinpointNote(""); pinpointClearNomatch();
        clearK("pmc_pick_v1");
        Analytics.track("quiz_started", viaShareProps());
        renderQ();
      };
      hero.insertBefore(gpb, hero.firstChild);
      if (isGenuineShareArrival(location.search || "")) Analytics.track("recipient_landing_viewed", Object.assign({recipient_channel: recipientChannel()}, viaShareProps()));
      return;
    }
    /* 2026-09-26 pm9 remix experiment: genuine ?o=remix arrivals with a
       valid ?remix= payload get the remix banner. REMIX_PAIR is null with
       the flag off or on garbage, so those arrivals fall through to the
       generic banner exactly as before the experiment existed. Fires
       recipient_landing_viewed here because the ?idea= block never runs on
       a bare /?s= arrival. */
    if (VIA_SHARE_ORIGIN === "remix" && REMIX_PAIR){
      var rpb = document.createElement("button");
      rpb.type = "button";
      rpb.id = "pmc-friend-banner";
      rpb.style.cssText = "display:block;width:100%;text-align:left;font:inherit;color:inherit;background:#fff7ec;border:1px solid #ffd9a3;border-radius:14px;padding:12px 14px;margin:0 0 14px;cursor:pointer";
      rpb.innerHTML = "<p style=\"margin:0 0 4px;font-weight:700;color:#333;line-height:1.4\">Your friend got " + REMIX_PAIR.idea.title + ".</p>" +
        "<p style=\"margin:0;font-size:14px;color:#666;line-height:1.4\">Remix it: take the 2-minute quiz and your card credits their pick.</p>";
      rpb.onclick = function(){
        state = {qi: 0, answers: {}};
        state.pinpoint = null;
        pinpointNote(""); pinpointClearNomatch();
        clearK("pmc_pick_v1");
        Analytics.track("quiz_started", viaShareProps());
        renderQ();
      };
      hero.insertBefore(rpb, hero.firstChild);
      if (isGenuineShareArrival(location.search || "")) Analytics.track("recipient_landing_viewed", Object.assign({recipient_channel: recipientChannel()}, viaShareProps()));
      return;
    }
    /* 2026-09-26 pm8 idea 2 first-Halloween milestone entry: genuine
       ?o=first arrivals with a valid ?first= payload get the milestone
       banner. FIRST_NAME is null with the flag off or on garbage, so those
       arrivals fall through to the generic banner exactly as before the
       experiment existed. One tap starts the quiz in first mode (kid +
       Under 3); the sender's name is cleared so the recipient's share-back
       uses their own. Fires recipient_landing_viewed here because the
       ?idea= block never runs on a bare /?s= arrival. */
    if (VIA_SHARE_ORIGIN === "first" && FIRST_NAME){
      var fpb = document.createElement("button");
      fpb.type = "button";
      fpb.id = "pmc-friend-banner";
      fpb.style.cssText = "display:block;width:100%;text-align:left;font:inherit;color:inherit;background:#fff7ec;border:1px solid #ffd9a3;border-radius:14px;padding:12px 14px;margin:0 0 14px;cursor:pointer";
      fpb.innerHTML = "<p style=\"margin:0 0 4px;font-weight:700;color:#333;line-height:1.4\">It's " + firstEsc(FIRST_NAME) + "'s first Halloween too?</p>" +
        "<p style=\"margin:0;font-size:14px;color:#666;line-height:1.4\">Find their first costume with the 2-minute quiz.</p>";
      fpb.onclick = function(){
        firstStartQuiz(null, "recipient-banner");
      };
      hero.insertBefore(fpb, hero.firstChild);
      if (isGenuineShareArrival(location.search || "")) Analytics.track("recipient_landing_viewed", Object.assign({recipient_channel: recipientChannel()}, viaShareProps()));
      return;
    }
    /* 2026-09-26 pm11 named-result experiment: genuine ?o=named arrivals
       with a valid ?named= payload get the named banner. NAMED_PICK is null
       with the flag off or on garbage, so those arrivals fall through to
       the generic banner exactly as before the experiment existed. The name
       is optional and sanitized; the nameless fallback reads as the
       sharer's pick without inventing a name. The CTA is the compare job:
       take the quiz and compare. Fires recipient_landing_viewed here
       because the ?idea= block never runs on a bare /?s= arrival. */
    if (VIA_SHARE_ORIGIN === "named" && NAMED_PICK){
      var npb = document.createElement("button");
      npb.type = "button";
      npb.id = "pmc-friend-banner";
      npb.style.cssText = "display:block;width:100%;text-align:left;font:inherit;color:inherit;background:#fff7ec;border:1px solid #ffd9a3;border-radius:14px;padding:12px 14px;margin:0 0 14px;cursor:pointer";
      npb.innerHTML = "<p style=\"margin:0 0 4px;font-weight:700;color:#333;line-height:1.4\">" + (NAMED_PICK.name ? namedEsc(NAMED_PICK.name) + "'s Halloween pick" : "Your friend's Halloween pick") + "</p>" +
        "<p style=\"margin:0;font-size:14px;color:#666;line-height:1.4\">" + (NAMED_PICK.name ? namedEsc(NAMED_PICK.name) + " got " : "Your friend got ") + namedEsc(NAMED_PICK.idea.title) + ". Tap to take the 2-minute quiz and compare.</p>";
      npb.onclick = function(){
        state = {qi: 0, answers: {}};
        state.pinpoint = null;
        pinpointNote(""); pinpointClearNomatch();
        clearK("pmc_pick_v1");
        Analytics.track("quiz_started", viaShareProps());
        renderQ();
      };
      hero.insertBefore(npb, hero.firstChild);
      if (isGenuineShareArrival(location.search || "")) Analytics.track("recipient_landing_viewed", Object.assign({recipient_channel: recipientChannel()}, viaShareProps()));
      return;
    }
    /* 2026-09-26 wrapped W1 fix: genuine ?o=wrapped arrivals get the
       Wrapped banner instead of the generic friend banner. The sharer's
       pick rides ?wpick= (minted by wrShareText); when it resolves in the
       live bank the banner names the pick + rank, otherwise (older links
       without ?wpick=, or a garbage id) it falls back to the
       Wrapped-branded generic. Wearer-safe: the headline names the
       Wrapped, never who wears the costume. One tap starts the normal
       quiz, attributed share_origin=wrapped. Fires
       recipient_landing_viewed here because the ?idea= block never runs on
       a bare /?s= arrival. */
    if (typeof VIA_SHARE_ORIGIN !== "undefined" && VIA_SHARE_ORIGIN === "wrapped"){
      var _wrTheirs = (typeof WRAPPED_PICK_ID !== "undefined" && WRAPPED_PICK_ID && typeof spinIdeaById === "function") ? spinIdeaById(WRAPPED_PICK_ID) : null;
      var _wrRank = (_wrTheirs && typeof _wrTheirs.rank === "number") ? ", ranked #" + _wrTheirs.rank + " of " + IDEAS.length : "";
      var wb = document.createElement("button");
      wb.type = "button";
      wb.id = "pmc-friend-banner";
      wb.style.cssText = "display:block;width:100%;text-align:left;font:inherit;color:inherit;background:#fff7ec;border:1px solid #ffd9a3;border-radius:14px;padding:12px 14px;margin:0 0 14px;cursor:pointer";
      wb.innerHTML = "<p style=\"margin:0 0 4px;font-weight:700;color:#333;line-height:1.4\">Your friend's Halloween Wrapped</p>" +
        "<p style=\"margin:0;font-size:14px;color:#666;line-height:1.4\">" + (_wrTheirs ? _wrTheirs.title + _wrRank + ". Take the 2-minute quiz to find your pick." : "They shared their 2026 Wrapped. Take the 2-minute quiz to find your pick and see your own.") + "</p>";
      wb.onclick = function(){
        state = {qi: 0, answers: {}};
        state.pinpoint = null;
        pinpointNote(""); pinpointClearNomatch();
        clearK("pmc_pick_v1");
        Analytics.track("quiz_started", viaShareProps());
        renderQ();
      };
      hero.insertBefore(wb, hero.firstChild);
      if (isGenuineShareArrival(location.search || "")) Analytics.track("recipient_landing_viewed", Object.assign({recipient_channel: recipientChannel()}, viaShareProps()));
      return;
    }
    /* 2026-09-26 pm12 living-share experiment: genuine ?o=living arrivals
       with a valid ?live= payload get the living banner. LIVING_SHARE is
       null with the flag off or on garbage, so those arrivals fall through
       to the generic banner exactly as before the experiment existed. The
       banner renders the sharer's declared progress strip, the live
       Halloween countdown, and the friend's own unfinished business as the
       persistent CTA. A second+ open of the same URL fires
       living_share_reopened: the Locket re-engagement event, measurable per
       share_id with the site's own events. The quiz CTA carries living_reopen
       so friend-quiz conversion on second+ opens is readable. Fires
       recipient_landing_viewed here because the ?idea= block never runs on
       a bare /?s= arrival. */
    if (VIA_SHARE_ORIGIN === "living" && LIVING_SHARE){
      var lsb = document.createElement("button");
      lsb.type = "button";
      lsb.id = "pmc-friend-banner";
      lsb.style.cssText = "display:block;width:100%;text-align:left;font:inherit;color:inherit;background:#fff7ec;border:1px solid #ffd9a3;border-radius:14px;padding:12px 14px;margin:0 0 14px;cursor:pointer";
      var _lsDays = daysToHalloween();
      lsb.innerHTML = "<p style=\"margin:0 0 4px;font-weight:700;color:#333;line-height:1.4\">Your friend shared a living costume link.</p>" +
        /* 2026-09-27 red-team: on Halloween day itself _lsDays is 0, so it
           says "today", never the awkward "0 days to Halloween". */
        "<p style=\"margin:0;font-size:14px;color:#666;line-height:1.4\">" + LIVING_SHARE.idea.title + " &middot; " + (_lsDays === 0 ? "Halloween is today" : _lsDays + " day" + (_lsDays === 1 ? "" : "s") + " to Halloween") + "</p>" +
        "<p style=\"margin:8px 0 0;font-size:13px;color:#666;line-height:1.6\">" + livingStripHtml(LIVING_SHARE.stage) + "</p>" +
        "<p style=\"margin:8px 0 0;font-size:14px;color:#333;line-height:1.4\"><b>You have not taken the quiz yet.</b> Take the 2-minute quiz and find your pick.</p>";
      lsb.onclick = function(){
        state = {qi: 0, answers: {}};
        state.pinpoint = null;
        pinpointNote(""); pinpointClearNomatch();
        clearK("pmc_pick_v1");
        var _lsReopen = false;
        try { _lsReopen = !!localStorage.getItem("pmc_seen_share_" + VIA_SHARE); } catch(e){}
        Analytics.track("quiz_started", Object.assign({living_reopen: _lsReopen}, viaShareProps()));
        renderQ();
      };
      hero.insertBefore(lsb, hero.firstChild);
      if (isGenuineShareArrival(location.search || "")){
        var _lsSeen = false;
        try {
          _lsSeen = !!localStorage.getItem("pmc_seen_share_" + VIA_SHARE);
          localStorage.setItem("pmc_seen_share_" + VIA_SHARE, "1");
        } catch(e){}
        Analytics.track("recipient_landing_viewed", Object.assign({recipient_channel: recipientChannel()}, viaShareProps()));
        if (_lsSeen) Analytics.track("living_share_reopened", {share_id: VIA_SHARE, living_stage: LIVING_SHARE.stage});
      }
      return;
    }
    /* 2026-09-26 red-team a11y: a button, not a div with onclick, so
       keyboard and screen-reader users can activate it too (matches the
       duel banner above). */
    var b = document.createElement("button");
    b.type = "button";
    b.id = "pmc-friend-banner";
    b.style.cssText = "display:block;width:100%;text-align:left;font:inherit;color:inherit;background:#fff7ec;border:1px solid #ffd9a3;border-radius:14px;padding:12px 14px;margin:0 0 14px;cursor:pointer";
    b.innerHTML = "<p style=\"margin:0 0 4px;font-weight:700;color:#333;line-height:1.4\">Your friend just found their costume.</p>" +
      "<p style=\"margin:0;font-size:14px;color:#666;line-height:1.4\">They sent you this link. Tap to take the 2-minute quiz and find yours.</p>";
    b.onclick = function(){
      /* Mirror the hero "Find my costume" start exactly: clean state, no
         pinpoint residue, old picks cleared, recipient-attributed event. */
      state = {qi: 0, answers: {}};
      state.pinpoint = null;
      pinpointNote(""); pinpointClearNomatch();
      clearK("pmc_pick_v1");
      Analytics.track("quiz_started", viaShareProps());
      renderQ();
    };
    hero.insertBefore(b, hero.firstChild);
    /* 2026-09-26 red-team: the plain /?s= friend banner never fired
       recipient_landing_viewed (only the teaser branch and the ?idea= block
       did), so bare-share arrivals undercounted recipient opens. */
    if (isGenuineShareArrival(location.search || "")) Analytics.track("recipient_landing_viewed", Object.assign({recipient_channel: recipientChannel()}, viaShareProps()));
  })();
  /* Saved-not-shared recovery nudge (2026-09-26 afternoon): a return visit
     with an unshared pick gets one slim banner above the hero. The save must
     be at least 6h old (someone sharing right away never sees it), the idea
     must still exist in the bank, and any query string suppresses the banner:
     share arrivals get the friend banner instead, and ?pick= detail views
     already have the share row. "Send it now" deep-links to ?pick=<slug>,
     which opens the same full pick flow with the share buttons; "Not now"
     snoozes 7 days. Additive: no existing element, event, or experiment is
     touched. Copy is plain English, no em dashes. */
  (function(){
    try {
      if (location.search) return;
      var hero = $("s-hero");
      if (!hero || $("pmc-recover-banner") || $("pmc-friend-banner")) return;
      var rec = load("pmc_recover_v1");
      var snoozedAt = load("pmc_recover_snooze_v1");
      if (!recoverShouldShow(rec, snoozedAt, Date.now())) return;
      var idea = null;
      if (typeof IDEAS !== "undefined") IDEAS.forEach(function(it){ if (it.id === rec.ideaId) idea = it; });
      if (!idea || !idea.title) return;
      var rb = document.createElement("div");
      rb.id = "pmc-recover-banner";
      rb.style.cssText = "background:#fff7ec;border:1px solid #ffd9a3;border-radius:14px;padding:12px 14px;margin:0 0 14px;";
      var p1 = document.createElement("p");
      p1.style.cssText = "margin:0 0 10px;font-weight:700;color:#333;line-height:1.4";
      p1.textContent = "You saved " + idea.title + " but never sent it.";
      var row = document.createElement("div");
      row.style.cssText = "display:flex;gap:10px;align-items:stretch;";
      var go = document.createElement("a");
      go.href = "/?pick=" + encodeURIComponent(rec.ideaId);
      go.textContent = "Send it now";
      go.style.cssText = "flex:1;text-align:center;text-decoration:none;font-weight:700;font-size:17px;color:#2a1500;background:#ff8c1a;border-radius:14px;padding:14px 0;display:block;";
      go.onclick = function(){ Analytics.track("recovery_nudge_sent", {idea_id: rec.ideaId}); };
      var no = document.createElement("button");
      no.type = "button";
      no.textContent = "Not now";
      no.style.cssText = "padding:14px 20px;font-size:17px;background:rgba(0,0,0,.04);color:#333;border:2px solid #d8c9ae;border-radius:14px;cursor:pointer;";
      no.onclick = function(){
        store("pmc_recover_snooze_v1", Date.now());
        Analytics.track("recovery_nudge_dismissed", {idea_id: rec.ideaId});
        if (rb.parentNode) rb.parentNode.removeChild(rb);
      };
      row.appendChild(go); row.appendChild(no);
      rb.appendChild(p1); rb.appendChild(row);
      hero.insertBefore(rb, hero.firstChild);
      Analytics.track("recovery_nudge_shown", {idea_id: rec.ideaId});
    } catch(e){}
  })();
  /* Quiz-abandon resume banner (2026-09-26 evening): a return visit with an
     abandoned quiz gets one slim banner above the hero. Continue restores the
     saved answers and resumes at the first unanswered question; Not now
     snoozes 7 days via pmc_resume_snooze_v1, matching the recovery nudge
     and rally banner. Any query string suppresses it: share
     arrivals (?s=) keep the normal recipient experience, and ?pick= detail
     views already have their own flow. Yields to the recovery nudge: one
     banner at a time above the hero (a completed pick's share nudge
     outranks resuming an abandoned quiz; resume re-offers on the next
     visit once the snooze lapses). Additive: no existing
     element, event, or experiment is touched. Copy is plain English, no
     em dashes. */
  (function(){
    try {
      if (location.search) return;
      var hero = $("s-hero");
      if (!hero || $("pmc-resume-banner") || $("pmc-friend-banner") || $("pmc-recover-banner")) return;
      var saved = load("pmc_quiz_v1");
      var rsnooze = load("pmc_resume_snooze_v1");
      if (!quizResumeShouldShow(saved, rsnooze, Date.now())) return;
      /* Drop answers for questions no longer in the bank (bank edits between
         visits); an empty set means there is nothing to resume. */
      var valid = {};
      Object.keys(saved.answers).forEach(function(k){ if (qById(k)) valid[k] = saved.answers[k]; });
      var n = Object.keys(valid).length;
      if (!n) return;
      var rb = document.createElement("div");
      rb.id = "pmc-resume-banner";
      rb.style.cssText = "background:#fff7ec;border:1px solid #ffd9a3;border-radius:14px;padding:12px 14px;margin:0 0 14px;";
      var p1 = document.createElement("p");
      p1.style.cssText = "margin:0 0 10px;font-weight:700;color:#333;line-height:1.4";
      p1.textContent = "Pick up where you left off? You answered " + n + " of " + flowOrder().length + ".";
      var row = document.createElement("div");
      row.style.cssText = "display:flex;gap:10px;align-items:stretch;";
      var go = document.createElement("button");
      go.type = "button";
      go.textContent = "Continue";
      go.style.cssText = "flex:1;text-align:center;font-weight:700;font-size:17px;color:#2a1500;background:#ff8c1a;border:0;border-radius:14px;padding:14px 0;display:block;cursor:pointer;";
      go.onclick = function(){
        var s2 = load("pmc_quiz_v1");
        if (!quizResumeShouldShow(s2, load("pmc_resume_snooze_v1"), Date.now())) { if (rb.parentNode) rb.parentNode.removeChild(rb); return; }
        state = {qi: 0, answers: {}};
        state.pinpoint = null;
        Object.keys(s2.answers).forEach(function(k){ if (qById(k)) state.answers[k] = s2.answers[k]; });
        /* The flow can shift with the q1 answer; drop anything no longer asked. */
        var order = flowOrder();
        Object.keys(state.answers).forEach(function(k){ if (order.indexOf(k) === -1) delete state.answers[k]; });
        state.qi = quizResumeIndex();
        if (state.qi < 0) { clearK("pmc_quiz_v1"); if (rb.parentNode) rb.parentNode.removeChild(rb); $("btn-start").onclick(); return; }
        Analytics.track("quiz_resume_continue", {answered_count: Object.keys(state.answers).length});
        if (rb.parentNode) rb.parentNode.removeChild(rb);
        renderQ();
      };
      var no = document.createElement("button");
      no.type = "button";
      no.textContent = "Not now";
      no.style.cssText = "padding:14px 20px;font-size:17px;background:rgba(0,0,0,.04);color:#333;border:2px solid #d8c9ae;border-radius:14px;cursor:pointer;";
      no.onclick = function(){
        store("pmc_resume_snooze_v1", Date.now());
        Analytics.track("quiz_resume_dismissed", {answered_count: n});
        if (rb.parentNode) rb.parentNode.removeChild(rb);
      };
      row.appendChild(go); row.appendChild(no);
      rb.appendChild(p1); rb.appendChild(row);
      hero.insertBefore(rb, hero.firstChild);
      Analytics.track("quiz_resume_shown", {answered_count: n});
    } catch(e){}
  })();
  /* Halloween-week sender rally (2026-09-26 evening): during Oct 25-31
     local, a return visit with a saved pick gets one slim banner above the
     hero with an honest date-gated line ("Halloween is N days away. Your
     pick is saved. Send it to the group chat." / "Halloween is today..."
     on Oct 31). "Send it now" deep-links to ?pick=<slug>, which opens the
     same full pick flow with the share buttons; "Not now" snoozes 7 days
     via pmc_rally_snooze_v1. Suppressed by any query string (?s= arrivals
     keep the friend banner), by an active recovery snooze (no
     double-nagging), and whenever the friend, recovery, or resume banner
     is already showing. Yields to every earlier banner; the whole thing
     vanishes by calendar math on Nov 1. Additive: no existing element,
     event, or experiment is touched. Copy is plain English, no em dashes. */
  (function(){
    try {
      var rec0 = load("pmc_recover_v1");
      var rsnooze = load("pmc_recover_snooze_v1");
      var rallySnooze = load("pmc_rally_snooze_v1");
      if (!rallyShouldShow(rec0, rsnooze, rallySnooze, location.search, Date.now())) return;
      var hero = $("s-hero");
      if (!hero || $("pmc-rally-banner") || $("pmc-friend-banner") || $("pmc-recover-banner") || $("pmc-resume-banner")) return;
      var idea = null;
      if (typeof IDEAS !== "undefined") IDEAS.forEach(function(it){ if (it.id === rec0.ideaId) idea = it; });
      if (!idea || !idea.title) return;
      var daysOut = daysToHalloween();
      var rb = document.createElement("div");
      rb.id = "pmc-rally-banner";
      rb.style.cssText = "background:#fff7ec;border:1px solid #ffd9a3;border-radius:14px;padding:12px 14px;margin:0 0 14px;";
      var p1 = document.createElement("p");
      p1.style.cssText = "margin:0 0 10px;font-weight:700;color:#333;line-height:1.4";
      p1.textContent = rallyCopyFor(Date.now());
      var row = document.createElement("div");
      row.style.cssText = "display:flex;gap:10px;align-items:stretch;";
      var go = document.createElement("a");
      go.href = "/?pick=" + encodeURIComponent(rec0.ideaId);
      go.textContent = "Send it now";
      go.style.cssText = "flex:1;text-align:center;text-decoration:none;font-weight:700;font-size:17px;color:#2a1500;background:#ff8c1a;border-radius:14px;padding:14px 0;display:block;";
      go.onclick = function(){ Analytics.track("rally_nudge_sent", {idea_id: rec0.ideaId, days_out: daysOut}); };
      var no = document.createElement("button");
      no.type = "button";
      no.textContent = "Not now";
      no.style.cssText = "padding:14px 20px;font-size:17px;background:rgba(0,0,0,.04);color:#333;border:2px solid #d8c9ae;border-radius:14px;cursor:pointer;";
      no.onclick = function(){
        store("pmc_rally_snooze_v1", Date.now());
        Analytics.track("rally_nudge_dismissed", {idea_id: rec0.ideaId, days_out: daysOut});
        if (rb.parentNode) rb.parentNode.removeChild(rb);
      };
      row.appendChild(go); row.appendChild(no);
      rb.appendChild(p1); rb.appendChild(row);
      hero.insertBefore(rb, hero.firstChild);
      Analytics.track("rally_nudge_shown", {idea_id: rec0.ideaId, days_out: daysOut});
    } catch(e){}
  })();
  /* Pantry parity (2026-09-25): pantry.html cards deep-link here with
     ?pick=<slug> so a pantry tap opens the SAME full pick flow
     (customization panel, AI plan, share text, claim flow) as a quiz result
     or browse card -- not the static /c/ guide. No ?s= param is minted here,
     so this never counts as a share arrival and attribution is untouched. */
  (function(){
    var m = /[?&]pick=([a-z0-9-]+)/.exec(location.search || "");
    if (!m) return;
    var idea = null;
    IDEAS.forEach(function(it){ if (it.id === m[1]) idea = it; });
    if (!idea) return;
    openIdeaDetail(idea.id, null, "s-pantry", "From your pantry");
  })();
  /* 2026-09-26: real moon phase. The hero moon shows tonight's actual
     phase, computed in pure JS with Paul Schlyter's low-precision lunar
     theory (sun/moon mean-anomaly corrections, no network, no API).
     Validated within 0.1pt of pyephem; see hour-session/moon-phase-build.md. */
  /* 2026-09-26: moonPhaseInfo extracted so the tap panel reuses the
     same calc for tonight and for Halloween night. */
  function moonPhaseName(elong){
    var names = ["New Moon","Waxing Crescent","First Quarter","Waxing Gibbous","Full Moon","Waning Gibbous","Last Quarter","Waning Crescent"];
    return names[Math.floor((((elong + 22.5) % 360) + 360) % 360 / 45) % 8];
  }
  function moonPhaseInfo(ms){
    /* Schlyter low-precision lunar phase. d = days since 1999-12-31 00:00 UTC.
       Computes the moon's true ecliptic longitude (with the five major
       perturbation terms) and the sun's true longitude; their difference is
       the elongation, which sets both the terminator geometry and the
       illumination fraction (1 - cos(elong)) / 2. */
    var rad = Math.PI / 180;
    var d = ms / 86400000 - 10956;
    var norm360 = function(x){ x = x % 360; return x < 0 ? x + 360 : x; };
    var mN = norm360(125.1228 - 0.0529538083 * d); /* moon ascending node */
    var mInc = 5.1454 * rad;
    var mW = norm360(318.0634 + 0.1643573223 * d); /* moon perigee longitude */
    var mA = 60.2666, mE = 0.054900;
    var mM = norm360(115.3654 + 13.0649929509 * d); /* moon mean anomaly */
    var mMr = mM * rad;
    var mEcc = mM + mE * (180 / Math.PI) * Math.sin(mMr) * (1 + mE * Math.cos(mMr));
    var mEr = mEcc * rad;
    var mXv = mA * (Math.cos(mEr) - mE);
    var mYv = mA * (Math.sqrt(1 - mE * mE) * Math.sin(mEr));
    var mV = Math.atan2(mYv, mXv) / rad;
    var mR = Math.sqrt(mXv * mXv + mYv * mYv);
    var mVw = (mV + mW) * rad, mNr = mN * rad;
    var mXh = mR * (Math.cos(mNr) * Math.cos(mVw) - Math.sin(mNr) * Math.sin(mVw) * Math.cos(mInc));
    var mYh = mR * (Math.sin(mNr) * Math.cos(mVw) + Math.cos(mNr) * Math.sin(mVw) * Math.cos(mInc));
    var mLon = norm360(Math.atan2(mYh, mXh) / rad);
    var sW = norm360(282.9404 + 4.70935e-5 * d); /* sun perigee longitude */
    var sE = 0.016709 - 1.151e-9 * d;
    var sM = norm360(356.0470 + 0.9856002585 * d); /* sun mean anomaly */
    var sMr = sM * rad;
    var sEcc = sM + sE * (180 / Math.PI) * Math.sin(sMr) * (1 + sE * Math.cos(sMr));
    var sEr = sEcc * rad;
    var sLon = norm360(Math.atan2(Math.sqrt(1 - sE * sE) * Math.sin(sEr), Math.cos(sEr) - sE) / rad + sW);
    var mLm = norm360(mN + mW + mM); /* moon mean longitude */
    var mD = norm360(mLm - sLon); /* mean elongation */
    mLon = norm360(mLon
      - 1.274 * Math.sin((mM - 2 * mD) * rad) /* Evection */
      + 0.658 * Math.sin(2 * mD * rad) /* Variation */
      - 0.186 * Math.sin(sM * rad) /* Yearly Equation */
      - 0.059 * Math.sin((2 * mM - 2 * mD) * rad)
      - 0.057 * Math.sin((mM - 2 * mD + sM) * rad));
    var elong = norm360(mLon - sLon); /* deg: 0 = new, 180 = full */
    return {elong: elong, phase: elong / 360,
      illum: (1 - Math.cos(elong * rad)) / 2, name: moonPhaseName(elong)};
  }
  /* 2026-09-30: moon-only sky. The day sun swap is gone; the hero, the
     detail view, and the tap panel all show the real computed moon phase.
     window._pmcIsDay survives only to gate the night shooting star. */
  function moonSVG(pathId){
    return '<svg class="moon" viewBox="0 0 100 100" aria-hidden="true" focusable="false">'
      + '<defs><radialGradient id="moonlit-' + pathId + '" cx="38%" cy="35%" r="75%">'
      + '<stop offset="0%" stop-color="#fdfbf3"/><stop offset="60%" stop-color="#f2edda"/><stop offset="100%" stop-color="#d9d2b4"/>'
      + '</radialGradient></defs>'
      + '<circle cx="50" cy="50" r="46" fill="#232338" stroke="#3d3d5c" stroke-width="1.5"/>'
      + '<path id="' + pathId + '" fill="url(#moonlit-' + pathId + ')" d=""/></svg>';
  }
  function setMoonPath(pathId, phase){
    var path = document.getElementById(pathId);
    if (!path) return;
    var r = 46, cx = 50, cy = 50;
    var c = Math.cos(2 * Math.PI * phase);
    var rx = Math.max(0.001, Math.abs(c) * r);
    var litSweep = phase < 0.5 ? 1 : 0; /* waxing: lit limb on the right */
    var termSweep = c > 0 ? (1 - litSweep) : litSweep; /* crescent: terminator on the lit side; gibbous: opposite side */
    path.setAttribute("d",
      "M " + cx + " " + (cy - r) +
      " A " + r + " " + r + " 0 0 " + litSweep + " " + cx + " " + (cy + r) +
      " A " + rx.toFixed(2) + " " + r + " 0 0 " + termSweep + " " + cx + " " + (cy - r) + " Z");
  }
  window._pmcIsDay = (function(){ var h = new Date().getHours(); return h >= 6 && h < 18; })();
  /* 2026-09-29: night class gates the shooting star (day sky gets none). */
  try { document.getElementById("s-hero").classList.toggle("night", !window._pmcIsDay); } catch(_night){}
  /* 2026-09-30: the day branch that swapped the moon for a sun is gone.
     The widget is moon-only now: the real computed phase, day and night. */
  function paintHeroSky(){
    var cap0 = document.getElementById("mooncap");
    if (cap0) cap0.setAttribute("title", "The real moon phase, new every night");
    setMoonPath("moon-lit", moonPhaseInfo(Date.now()).phase); /* 0 = new, 0.25 = first quarter, 0.5 = full */
  }
  paintHeroSky();
  function paintDetailSky(){
    var el = document.getElementById("detail-sky");
    if (!el || el.getAttribute("data-done")) return;
    el.setAttribute("data-done", "1");
    /* 2026-09-30: moon-only, like the hero. No day sun swap. */
    el.innerHTML = '<div class="halo" aria-hidden="true"></div>' + moonSVG("d-moon-lit");
    setMoonPath("d-moon-lit", moonPhaseInfo(Date.now()).phase);
  }
  (function(){
    paintDetailSky();
    /* 2026-09-26: tappable moon. The panel shows tonight's phase,
       Halloween night's moon (computed, never hardcoded), and days to go. */
    var mbtn = document.getElementById("moon-btn");
    var mpnl = document.getElementById("moon-panel");
    if (mbtn && mpnl){
      var mpop = false;
      var fillMoonPanel = function(){
        if (mpop) return; mpop = true;
        var tn = moonPhaseInfo(Date.now());
        /* 2026-09-26: Halloween night rolls over. Once Oct 31 has passed,
           point the panel at next year's Halloween so it never reads stale. */
        var nowT = Date.now();
        var nowY = new Date(nowT).getFullYear();
        var rolled = nowT > new Date(nowY, 9, 31, 23, 59, 59, 999).getTime();
        var hwY = rolled ? nowY + 1 : nowY;
        /* Halloween night, 8pm viewer-local: the moment you look up. */
        var hw = moonPhaseInfo(new Date(hwY, 9, 31, 20, 0, 0).getTime());
        var days = Math.ceil((new Date(hwY, 9, 31).getTime() - nowT) / 86400000);
        var tpct = Math.round(tn.illum * 100), hpct = Math.round(hw.illum * 100);
        var daybit = days > 1 ? " (" + days + " days away)" : days === 1 ? " (tomorrow night)" : days === 0 ? " (tonight!)" : "";
        var hwLabel = rolled ? "Next Halloween night" : "Halloween night";
        $("moon-tonight").textContent = "Tonight's moon: " + tn.name + ", " + tpct + "% lit."; /* 2026-09-30: moon-only widget, no day sun branch */
        $("moon-halloween").textContent = hwLabel + ": " + hw.name + ", " + hpct + "% lit" + daybit + ".";
        var fun;
        if (hw.illum >= 0.85) fun = "Full moon on Halloween. Spooky season is cooperating.";
        else if (hw.illum >= 0.4) fun = "A " + hpct + "% moon on Halloween night. Spooky enough.";
        else fun = "Just a sliver of moon on Halloween. Extra spooky.";
        $("moon-fun").textContent = fun;
      };
      var toggleMoon = function(){
        if (mpnl.hidden){
          fillMoonPanel();
          mpnl.hidden = false;
          mbtn.setAttribute("aria-expanded", "true");
          Analytics.track("moon_tapped");
        } else {
          mpnl.hidden = true;
          mbtn.setAttribute("aria-expanded", "false");
        }
      };
      mbtn.addEventListener("click", toggleMoon);
      mbtn.addEventListener("keydown", function(e){
        if (e.key === "Enter" || e.key === " "){ e.preventDefault(); toggleMoon(); }
      });
    }
  })();
  /* 2026-09-26: Discover tab switching with a subtle fade. */
  (function(){
    var chips = document.querySelectorAll("#discover .chip");
    if (!chips.length) return;
    var current = "row-trending";
    var pendingSwap = null;
    var rows = {"row-trending": $("row-trending"), "row-tonight": $("row-tonight"), "row-new": $("row-new")};
    /* 2026-09-26 red-team: skip the fade when the user prefers reduced motion. */
    var reduceMotion = false;
    try { reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches; } catch(e){}
    function activate(id, chip){
      if (id === current || !rows[id]) return;
      /* 2026-09-27: the tonight rail is data-driven; re-render on every
         activation so pantry ticks and quiz answers never go stale. */
      if (id === "row-tonight" && typeof renderTonightRail === "function"){
        try { renderTonightRail(); } catch(e){}
      }
      for (var i = 0; i < chips.length; i++){
        chips[i].classList.remove("on");
        chips[i].setAttribute("aria-selected", "false");
      }
      chip.classList.add("on");
      chip.setAttribute("aria-selected", "true");
      /* 2026-09-27: the tonight status line belongs to the tonight tab. */
      var tonightStatus = document.getElementById("row-tonight-status");
      if (tonightStatus) tonightStatus.hidden = (id !== "row-tonight");
      var oldRow = rows[current];
      current = id;
      var newRow = rows[id];
      var swap = function(){
        oldRow.hidden = true;
        oldRow.classList.remove("fading");
        newRow.hidden = false;
        newRow.scrollLeft = 0;
      };
      if (reduceMotion){ swap(); }
      else {
        oldRow.classList.add("fading");
        if (pendingSwap) clearTimeout(pendingSwap);
        pendingSwap = setTimeout(function(){ pendingSwap = null; swap(); }, 180);
      }
      Analytics.track("discover_tab", {tab: id});
    }
    for (var i = 0; i < chips.length; i++){
      (function(chip){
        chip.addEventListener("click", function(){ activate(chip.getAttribute("data-tab"), chip); });
      })(chips[i]);
    }
  })();
  /* 2026-09-29: tool tabs. One panel open at a time; re-tapping the
     open tab closes it. Impression + click logging comes from UnitTrack
     (tools-bar; tabs carry data-item-id). Panels reuse existing destinations,
     no new multi-step inline flows, so no tapGuard needed. */
  (function(){
    var tabs = Array.prototype.slice.call(document.querySelectorAll("#tool-tabs .tooltab"));
    if (!tabs.length) return;
    function panelFor(tab){ return document.getElementById(tab.getAttribute("aria-controls")); }
    function closeAll(){
      tabs.forEach(function(t){ t.setAttribute("aria-selected", "false"); t.setAttribute("tabindex", "-1"); });
      tabs.forEach(function(t){ var p = panelFor(t); if (p) p.hidden = true; });
    }
    function openTab(tab){
      var wasOpen = tab.getAttribute("aria-selected") === "true";
      closeAll();
      if (!wasOpen){
        tab.setAttribute("aria-selected", "true");
        tab.setAttribute("tabindex", "0");
        var p = panelFor(tab);
        if (p) p.hidden = false;
      }
    }
    tabs.forEach(function(tab, idx){
      tab.setAttribute("tabindex", idx === 0 ? "0" : "-1");
      tab.addEventListener("click", function(){ openTab(tab); });
      tab.addEventListener("keydown", function(e){
        var j = null;
        if (e.key === "ArrowRight") j = (idx + 1) % tabs.length;
        else if (e.key === "ArrowLeft") j = (idx - 1 + tabs.length) % tabs.length;
        else if (e.key === "Home") j = 0;
        else if (e.key === "End") j = tabs.length - 1;
        else if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openTab(tab); return; }
        if (j !== null){ e.preventDefault(); tabs[j].focus(); openTab(tabs[j]); }
      });
    });
  })();
  /* 2026-09-26 (landing refresh): the proof-card entrance runs once on
     first paint. The .fresh gate is retired ~1.2s after load so Discover tab
     switches never replay the stagger (un-hiding a row restarts its cards'
     CSS animations; QA 2026-09-26). */
  (function(){
    var strip = document.querySelector(".proofstrip");
    if (!strip) return;
    strip.classList.add("fresh");
    setTimeout(function(){ strip.classList.remove("fresh"); }, 1200);
  })();
  /* 2026-09-26: sticky mobile quiz CTA. Appears once the hero CTA
     scrolls out of view, and only on the landing screen. Stays hidden on
     quiz, results, browse, detail, about, and whenever the runner-up
     overlay is open (2026-09-26 red-team: it used to show on results and
     wipe them when tapped). */
  (function(){
    var bar = $("stickycta"), heroBtn = $("btn-start"), heroScreen = $("s-hero");
    if (!bar || !heroBtn || !heroScreen || !("IntersectionObserver" in window)) return;
    $("stickycta-btn").onclick = function(){ $("btn-start").onclick(); };
    var heroHidden = false;
    var landingActive = function(){
      if (!heroScreen.classList.contains("on")) return false;
      var ov = document.getElementById("ru-overlay");
      if (ov && ov.style.display !== "none") return false;
      return true;
    };
    var update = function(){
      bar.classList.toggle("show", heroHidden && landingActive());
    };
    /* Called by the runner-up overlay open/close paths. */
    window.pmcStickyUpdate = update;
    var io = new IntersectionObserver(function(entries){
      heroHidden = !entries[0].isIntersecting;
      update();
    }, {threshold: 0});
    io.observe(heroBtn);
    if ("MutationObserver" in window){
      var screens = document.querySelectorAll(".screen");
      var mo = new MutationObserver(update);
      for (var i = 0; i < screens.length; i++){
        mo.observe(screens[i], {attributes: true, attributeFilter: ["class"]});
      }
    }
  })();
  /* 2026-09-24: T-minus clock. Days until Halloween under the hero
     tagline. Copy escalates on its own in the final week; hides after Oct 31. */
  (function(){
    var el = $("tminus");
    if (!el) return;
    var now = new Date();
    var hw = new Date(now.getFullYear(), 9, 31);
    /* 2026-09-30: weekday dropped per Billy ("kill the (Saturday)").
       Just "N days until Halloween". */
    var days = Math.ceil((hw.getTime() - now.getTime()) / 86400000);
    /* 2026-09-26 red-team D11: the clock hid ON Halloween (days <= 0 at midnight).
       Halloween day deserves its own line, not silence. Hides only after Oct 31. */
    if (days < 0) return; /* hidden: style starts display:none */
    var msg;
    if (days === 0) msg = "🎃 Halloween is today: pick a costume you can build tonight";
    else if (days === 1) msg = "🎃 Halloween is tomorrow: pick a costume you can build tonight";
    else if (days <= 7) msg = "🎃 " + days + " days until Halloween: every idea here builds from your closet";
    else msg = "🎃 " + days + " days until Halloween";
    el.textContent = msg;
    el.style.display = "";
  })();
  /* 2026-09-26: Halloween night weather. On homepage load, check the
     cache; otherwise fetch the Oct 31 forecast from Open-Meteo (free, no
     key) once the visitor has interacted with the page. Renders a small line
     under the countdown, e.g. "Halloween night: 48°F, 20% chance of rain.
     Plan for a jacket." Denied geolocation, out-of-range forecast (Oct 31 is
     past Open-Meteo's 16-day window until mid-October), or fetch failure:
     stays silent, no nag. Async, never blocks load. Cached in
     pmc_hw_weather_v1 keyed by Halloween date.
     2026-09-26 pm7 red-team D1: NEVER request geolocation on page load. A
     cold visitor must not meet a location permission prompt before their
     first tap. Two gates: (1) outside Open-Meteo's ~16-day window the
     forecast cannot render, so skip entirely -- no prompt, no fetch;
     (2) inside the window, wait for the first pointerdown/keydown. */
  (function(){
    var el = $("hw-weather");
    if (!el) return;
    var now = new Date();
    var yr = now.getFullYear();
    /* Past Halloween: tminus hides too, nothing to forecast. */
    if (now.getTime() > new Date(yr, 9, 31, 23, 59, 59).getTime()) return;
    var hwDate = yr + "-10-31";
    function render(tmin, precip){
      var msg = "Halloween night: " + Math.round(tmin) + "°F";
      if (precip > 0) msg += ", " + Math.round(precip) + "% chance of rain";
      else msg += ", clear";
      var notes = [];
      if (tmin < 50) notes.push("Plan for a jacket");
      if (precip > 30) notes.push("Waterproof it");
      if (notes.length) msg += ". " + notes.join(". ");
      el.textContent = msg;
      el.hidden = false;
      try { Analytics.track("halloween_weather_shown", {tmin_f: Math.round(tmin), precip_pct: Math.round(precip)}); } catch(e){}
    }
    var cached = load("pmc_hw_weather_v1");
    if (cached && cached.date === hwDate && typeof cached.tmin === "number"){
      render(cached.tmin, cached.precip || 0);
      return;
    }
    if (!("geolocation" in navigator) || typeof fetch !== "function") return;
    /* D1 gate 1: Open-Meteo forecasts ~16 days out. Before ~Oct 15 the Oct 31
       forecast cannot exist, so skip the whole attempt: no prompt, no fetch. */
    if (new Date(yr, 9, 31).getTime() - Date.now() > 16*86400000) return;
    /* D1 gate 2: wait for the visitor's first interaction before asking for
       location. A cold user never sees a permission prompt before a tap. */
    var _wxAsked = false;
    function _wxAsk(){
      if (_wxAsked) return; _wxAsked = true;
    try {
      navigator.geolocation.getCurrentPosition(function(pos){
        var lat = pos.coords.latitude.toFixed(4);
        var lon = pos.coords.longitude.toFixed(4);
        var url = "https://api.open-meteo.com/v1/forecast?latitude=" + lat +
          "&longitude=" + lon +
          "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max" +
          "&temperature_unit=fahrenheit&timezone=auto" +
          "&start_date=" + hwDate + "&end_date=" + hwDate;
        fetch(url).then(function(r){ return r.json(); }).then(function(j){
          /* Oct 31 beyond the 16-day forecast window: no daily data yet.
             Stay silent; the line appears once the forecast reaches it. */
          if (!j || !j.daily || !j.daily.time || j.daily.time.indexOf(hwDate) < 0) return;
          var tmin = j.daily.temperature_2m_min[0];
          var precip = j.daily.precipitation_probability_max[0];
          if (typeof tmin !== "number") return;
          if (typeof precip !== "number" || precip === null) precip = 0;
          store("pmc_hw_weather_v1", {date: hwDate, tmin: tmin, precip: precip, at: Date.now()});
          render(tmin, precip);
        }).catch(function(){ /* silent */ });
      }, function(){ /* denied/unavailable: silent */ }, {timeout: 9000, maximumAge: 86400000});
    } catch(e){ /* silent */ }
    }
    document.addEventListener("pointerdown", _wxAsk);
    document.addEventListener("keydown", _wxAsk);
  })();
  var _dismissBtn = document.getElementById("btn-returndismiss");
  if (_dismissBtn) _dismissBtn.addEventListener("click", function(){
    var pk = load("pmc_pick_v1");
    try { localStorage.setItem("pmc_returnhero_dismissed_v1", JSON.stringify({ideaId: pk && pk.ideaId, at: Date.now()})); } catch(e){}
    var bx = document.getElementById("returnbox"); if (bx) bx.hidden = true;
    var hEl = document.querySelector(".hero"); if (hEl) hEl.classList.remove("returning");
    try { track("returnhero_dismissed", {}); } catch(e){}
    refreshReturnBox();
  });
  refreshReturnBox();
  renderPinpointChips();
  var _ic = document.getElementById("idea-count"); if (_ic) _ic.textContent = IDEAS.length;
})();
/* 2026-09-26: personalized returning hero. A fresh pmc_pick_v1 plus
   usable pmc_last_v1 leads with the saved pick (photo, "Still going as X?").
   The generic first-timer block hides via .returning on .hero. */
function refreshReturnBox(){
  var box = $("returnbox");
  if (!box) return;
  box.hidden = true;
  var heroEl = document.querySelector(".hero");
  if (heroEl) heroEl.classList.remove("returning");
  var pick = load("pmc_pick_v1");
  var last = load("pmc_last_v1");
  var fresh = pick && pick.at && (Date.now() - pick.at) < 300*24*3600*1000;
  /* 2026-09-28: the welcome-back card is dismissible. A dismissal is
     tied to the dismissed pick: retaking the quiz and landing a new pick
     re-shows the card. */
  var dismissed = load("pmc_returnhero_dismissed_v1");
  if (dismissed && pick && dismissed.ideaId === pick.ideaId) fresh = false;
  if (fresh && last && last.results && last.results.length) {
    var idea = null;
    for (var i = 0; i < IDEAS.length; i++) if (IDEAS[i].id === pick.ideaId){ idea = IDEAS[i]; break; }
    if (idea) {
      var photo = $("returnhero-photo");
      if (photo){ photo.src = "photos/" + idea.id + ".webp"; pmcSrcset(photo, idea.id, "52px"); photo.alt = idea.title + " costume"; }
      $("returnhero-title").textContent = "Still going as " + idea.title + "?";
      var st = $("returnhero-share-status");
      if (st) st.textContent = "";
      box.hidden = false;
      if (heroEl) heroEl.classList.add("returning");
    }
  }
  /* 2026-09-26 P4: stranded quiz results. pmc_last_v1 exists but no fresh
     pick (returnbox hidden) = results with no path back. Show the quiet
     resume link; it reuses the btn-return handler verbatim. */
  var resumeWrap = $("resume-wrap");
  if (resumeWrap){
    var hasLast = !!(last && last.results && last.results.length);
    resumeWrap.hidden = !(hasLast && box.hidden);
  }
}

/* 2026-09-30 (Week-2 traffic sprint): bundle extracted from index.html to /app.js
   (defer). Set when the whole script parsed and ran: the inline boot-guard
   uses this to detect a failed bundle load and arm retry buttons. */
window.__pmcBooted = true;
