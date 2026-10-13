/* Cast-card visual harness (2026-10-13, Billy).
   Billy on the Ice Kingdom Crew cast flow: "I love this, except I don't
   know what 'snowflake sprite' and others look like." Role cards were
   text-only. renderPersonalCards now puts the role's own share-card art
   (images/og/<idea>--<role>.jpg) and, where ROLE_DIY has one, the role's
   one-line look from the per-person plan on every card.

   Loads the real index.html with app.js inlined, builds the real cast
   panel via window.buildCastPanel, and asserts:
   SNOW (snow-sisters, 3 people, 1 kid, Billy's exact cast)
     - 3 cards; heads read Capri/snow princess, Daddy/talking snowman,
       Mommy/snowflake sprite
     - each card's img.pcard-role-img points at that role's card art and
       the file exists on disk; the crew-photo onerror fallback is armed
     - each card's .pcard-look equals the exact ROLE_DIY line
     - Send + Try it on still present per card
     - changing Mommy's picker to ice queen swaps her art + look line
   SAFARI (safari-zoo-crew, choose mode)
     - cards carry role art (files exist) AND the verbatim ROLE_DIY look
       line for the assigned animal (ROLE_DIY covers every cast idea
       since the 2026-10-13 expansion; coverage + exceptions are guarded
       by cast-role-look-coverage-harness.cjs)
     - picker change to elephant swaps the art and the look line
   HERO (superhero-family, assign mode)
     - cards carry role art and the verbatim ROLE_DIY look line
   Run: node hour-session/cast-card-visual-harness.cjs
   Exit code 1 on any failure. */
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("/home/hatch/workspace/.rt-node/node_modules/jsdom");

const ROOT = path.resolve(__dirname, "..");
let html = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
const appjs = fs.readFileSync(path.join(ROOT, "app.js"), "utf8");
if (!/<script src="\/app\.js[^"]*" defer><\/script>/.test(html)) {
  console.error("FAIL: app.js script tag not found in index.html");
  process.exit(1);
}
html = html.replace(/<script src="\/app\.js[^"]*" defer><\/script>/,
  function(){ return "<script>\n" + appjs + "\n</script>"; });

let pass = 0, fail = 0;
function ok(cond, name, extra){
  if (cond){ pass++; console.log("  ok:", name); }
  else { fail++; console.log("  FAIL:", name, extra || ""); }
}
function after(t){ return new Promise(r => setTimeout(r, t)); }

const dom = new JSDOM(html, {
  url: "http://localhost:8901/?pick=snow-sisters",
  runScripts: "dangerously",
  pretendToBeVisual: true,
  beforeParse(window){
    window.matchMedia = window.matchMedia || function(){ return {matches: false, addListener: function(){}, removeListener: function(){}}; };
    window.scrollTo = function(){};
    if (window.Element && window.Element.prototype && !window.Element.prototype.scrollIntoView){
      window.Element.prototype.scrollIntoView = function(){};
    }
    if (!window.navigator.clipboard){
      window.navigator.clipboard = { writeText: function(){ return Promise.resolve(); } };
    }
  }
});
const { window } = dom;
const { document } = window;

function buildPanel(ideaId){
  const idea = window.IDEAS.filter(function(i){ return i.id === ideaId; })[0];
  const shareBox = document.createElement("div");
  const aiPlanBox = document.createElement("div");
  const box = window.buildCastPanel(idea, window.CASTS[ideaId], shareBox, aiPlanBox);
  document.body.appendChild(box);
  return box;
}
function clickBtn(container, text){
  const b = Array.from(container.querySelectorAll("button")).filter(function(x){
    return (x.textContent || "").trim() === text;
  })[0];
  if (b) b.click();
  return b;
}
function setName(box, i, val){
  const inp = box.querySelectorAll(".castrow input")[i];
  inp.value = val;
  inp.dispatchEvent(new window.Event("input", {bubbles: true}));
}
function setRole(box, i, role){
  const sel = box.querySelectorAll(".castrow select")[i];
  sel.value = role;
  sel.dispatchEvent(new window.Event("change", {bubbles: true}));
}
function cards(box){ return Array.from(box.querySelectorAll(".pclist .pcard")); }
function cardParts(card){
  return {
    head: card.querySelector(".pcard-head"),
    img: card.querySelector("img.pcard-role-img"),
    look: card.querySelector(".pcard-look"),
    send: Array.from(card.querySelectorAll("button")).some(function(b){ return /send .*card/i.test(b.textContent || ""); }),
    tryon: Array.from(card.querySelectorAll("button")).some(function(b){ return (b.textContent || "").trim() === "Try it on"; })
  };
}

(async function(){
  await after(900);
  ok(!!window.CASTS && !!window.IDEAS, "app booted in jsdom");

  /* ---------- SNOW: Billy's exact cast ---------- */
  console.log("snow-sisters:");
  const box = buildPanel("snow-sisters");
  await after(300);
  const btnRows = box.querySelectorAll(".castbtns");
  ok(!!clickBtn(btnRows[0], "3"), "size set to 3 people");
  await after(150);
  /* Capri is the kid: toggle person 1 individually (kid-count button
     would mark the LAST person instead). */
  const tg = box.querySelectorAll(".castrow .casttoggle")[0];
  if (tg && (tg.textContent || "").trim() === "Adult") tg.click();
  await after(150);
  setName(box, 0, "Capri"); setName(box, 1, "Daddy"); setName(box, 2, "Mommy");
  setRole(box, 0, "snow princess");
  setRole(box, 1, "talking snowman");
  setRole(box, 2, "snowflake sprite");
  await after(300);

  const cs = cards(box);
  ok(cs.length === 3, "3 personal cards rendered", "found " + cs.length);
  const expect = [
    {head: "Capri is the snow princess", art: "images/og/snow-sisters--snow-princess.jpg",
     look: "Blue or white dress with a few snowflake stickers, lighter than the queen."},
    {head: "Daddy is the talking snowman", art: "images/og/snow-sisters--talking-snowman.jpg",
     look: "White clothes, black button dots down the front, and the carrot nose."},
    {head: "Mommy is the snowflake sprite", art: "images/og/snow-sisters--snowflake-sprite.jpg",
     look: "White or silver clothes with snowflake stickers, like the queen in miniature."}
  ];
  cs.forEach(function(card, i){
    const p = cardParts(card), e = expect[i];
    if (!e) return;
    ok(p.head && p.head.textContent === e.head, "card " + i + " head", p.head && p.head.textContent);
    ok(!!p.img, "card " + i + " has role art img");
    if (p.img){
      ok(p.img.getAttribute("src") === e.art, "card " + i + " art is the role card", p.img.getAttribute("src"));
      ok(fs.existsSync(path.join(ROOT, e.art)), "card " + i + " art file exists on disk", e.art);
      ok(typeof p.img.onerror === "function", "card " + i + " crew-photo fallback armed");
    }
    ok(!!p.look, "card " + i + " has look line");
    if (p.look) ok(p.look.textContent === e.look, "card " + i + " look = ROLE_DIY line verbatim", p.look.textContent);
    ok(p.send, "card " + i + " Send card button intact");
    ok(p.tryon, "card " + i + " Try it on intact");
  });

  /* Picker change: Mommy becomes the ice queen; her card must follow. */
  setRole(box, 2, "ice queen");
  await after(300);
  const p2 = cardParts(cards(box)[2]);
  ok(p2.head && p2.head.textContent === "Mommy is the ice queen", "picker change updates head", p2.head && p2.head.textContent);
  ok(p2.img && p2.img.getAttribute("src") === "images/og/snow-sisters--ice-queen.jpg",
    "picker change swaps role art", p2.img && p2.img.getAttribute("src"));
  ok(p2.look && p2.look.textContent === "Blue dress or a blue top and skirt, then stick snowflake stickers all over it.",
    "picker change swaps look line", p2.look && p2.look.textContent);

  /* Every selectable snow-sisters role (incl. filler) resolves: named
     roles have card art on disk; the filler relies on the fallback. */
  const opts = window.castRoleOptions("snow-sisters");
  opts.forEach(function(r){
    const f = "images/og/snow-sisters--" + window.roleSlugFor(r) + ".jpg";
    const has = fs.existsSync(path.join(ROOT, f));
    if (r === "snow friend") ok(!has, "filler 'snow friend' has no card art (fallback path)", f);
    else ok(has, "role art exists: " + r, f);
  });

  /* ---------- SAFARI smoke (choose mode, ROLE_DIY since 2026-10-13) ---------- */
  console.log("safari-zoo-crew:");
  const sbox = buildPanel("safari-zoo-crew");
  await after(300);
  const scs = cards(sbox);
  ok(scs.length >= 2, "safari cards rendered", "found " + scs.length);
  scs.forEach(function(card, i){
    const p = cardParts(card);
    ok(!!p.img && /^images\/og\/safari-zoo-crew--[a-z0-9-]+\.jpg$/.test(p.img.getAttribute("src") || ""),
      "safari card " + i + " carries role art", p.img && p.img.getAttribute("src"));
    if (p.img) ok(fs.existsSync(path.join(ROOT, p.img.getAttribute("src"))), "safari card " + i + " art exists");
    var expLook = ["Solid-color clothes in lion colors, felt ears taped to a plastic headband, and face paint details.",
                   "Solid-color clothes in elephant colors, felt ears taped to a plastic headband, and face paint details."][i];
    ok(!!p.look, "safari card " + i + " has look line");
    if (p.look && expLook) ok(p.look.textContent === expLook, "safari card " + i + " look = ROLE_DIY line verbatim", p.look.textContent);
  });
  setRole(sbox, 0, "elephant");
  await after(300);
  const sp0 = cardParts(cards(sbox)[0]);
  ok(sp0.img && sp0.img.getAttribute("src") === "images/og/safari-zoo-crew--elephant.jpg",
    "safari picker change swaps art to elephant", sp0.img && sp0.img.getAttribute("src"));
  ok(sp0.look && sp0.look.textContent === "Solid-color clothes in elephant colors, felt ears taped to a plastic headband, and face paint details.",
    "safari picker change swaps look line to elephant", sp0.look && sp0.look.textContent);

  /* ---------- SUPERHERO smoke (assign mode, ROLE_DIY since 2026-10-13) ---------- */
  console.log("superhero-family:");
  const hbox = buildPanel("superhero-family");
  await after(300);
  const hcs = cards(hbox);
  ok(hcs.length >= 2, "hero cards rendered", "found " + hcs.length);
  hcs.forEach(function(card, i){
    const p = cardParts(card);
    ok(!!p.img && /^images\/og\/superhero-family--[a-z0-9-]+\.jpg$/.test(p.img.getAttribute("src") || ""),
      "hero card " + i + " carries role art", p.img && p.img.getAttribute("src"));
    if (p.img) ok(fs.existsSync(path.join(ROOT, p.img.getAttribute("src"))), "hero card " + i + " art exists");
    ok(!!p.look, "hero card " + i + " has look line");
    if (p.look) ok(p.look.textContent === "Red sweatsuit, black felt eye mask on a headband, and a yellow felt initial pinned to your chest.",
      "hero card " + i + " look = ROLE_DIY line verbatim", p.look.textContent);
  });

  console.log("\n" + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
})().catch(function(e){ console.error("HARNESS ERROR", e); process.exit(1); });
