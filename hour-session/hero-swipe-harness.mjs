/* Hero rotation swipe-nav harness (2026-10-13, v3).
   Extracts the REAL hero rotation <script> from ../index.html and runs it
   in jsdom against the real mosaic markup, with fake timers (deterministic
   300/700ms fade, 5s interval, 10s resume), a stub Image that "preloads"
   instantly, and Math.random pinned so the random start lands on slide 0.
   Covers: tap navigates, swipe L/R, wrap both ends, click suppression,
   under-threshold drag, vertical drag, ~10s auto-pause + resume, dots,
   rapid double-swipe guard, auto-advance still intact. */
import { createRequire } from "module";
import fs from "fs";

const require = createRequire(import.meta.url);
const { JSDOM, VirtualConsole } = require("/home/hatch/workspace/.rt-node/node_modules/jsdom");

const html = fs.readFileSync(new URL("../index.html", import.meta.url), "utf8");
const marker = html.indexOf('querySelector("#hero-mosaic a")');
if (marker < 0) { console.error("FAIL: rotation script marker not found"); process.exit(1); }
const sStart = html.lastIndexOf("<script>", marker);
const sEnd = html.indexOf("</script>", marker);
const code = html.slice(sStart + "<script>".length, sEnd);

const ORDER = ["bumble-bee", "block-monster", "baby-pumpkin", "pickle",
  "haunted-animatronics", "bacon-eggs", "board-game-pieces"];
const TITLES = ["Bumble Bee", "Block Monster", "Baby Pumpkin", "Pickle",
  "Haunted Animatronics", "Bacon & Eggs", "Board Game Pieces"];

const vc = new VirtualConsole(); /* swallow jsdom navigation noise */
const dom = new JSDOM(`<!DOCTYPE html><body>
<div class="hero-mosaic" id="hero-mosaic" aria-label="Popular costume ideas">
  <a href="/c/bumble-bee" aria-label="Bumble Bee costume guide"><img src="photos/bumble-bee.webp" alt="Bumble Bee costume"><span>Bumble Bee</span></a>
  <a href="/c/baby-dino" aria-label="Baby Dinosaur costume guide"><img src="photos/baby-dino.webp" alt="Baby Dinosaur costume"><span>Baby Dinosaur</span></a>
  <a href="/c/emerald-witch" aria-label="Emerald Witch costume guide"><img src="photos/emerald-witch.webp" alt="Emerald Witch costume"><span>Emerald Witch</span></a>
</div></body>`, { url: "https://pickmycostume.com/", virtualConsole: vc, runScripts: "dangerously" });
const { window } = dom;
const { document } = window;
/* jsdom defaults document.hidden to true; a real visible tab has it false,
   and advance() rightly refuses to run while hidden. Model a visible tab. */
Object.defineProperty(document, "hidden", { value: false, configurable: true });

/* --- fake timers inside the page realm --- */
const timeouts = new Map(), intervals = new Map();
let nextId = 1;
window.setTimeout = (fn, ms) => { const id = nextId++; timeouts.set(id, { fn, ms }); return id; };
window.clearTimeout = (id) => timeouts.delete(id);
window.setInterval = (fn, ms) => { const id = nextId++; intervals.set(id, { fn, ms }); return id; };
window.clearInterval = (id) => intervals.delete(id);

function runTimeoutsWhere(pred) {
  for (let round = 0; round < 12; round++) {
    const due = [...timeouts.entries()].filter(([, t]) => pred(t.ms));
    if (!due.length) return;
    for (const [id, t] of due) { timeouts.delete(id); t.fn(); }
  }
}
const flushFade = () => runTimeoutsWhere((ms) => ms <= 1000); /* 300/700 fade, 350/400 guards */
const fireIntervals = () => { for (const [, t] of [...intervals.entries()]) t.fn(); };
const hasTimeout = (ms) => [...timeouts.values()].some((t) => t.ms === ms);
const intervalCount = (ms) => [...intervals.values()].filter((t) => t.ms === ms).length;

/* --- stub Image: every preload succeeds on a microtask --- */
window.Image = class {
  set onload(f) { this._onload = f; }
  get onload() { return this._onload; }
  set src(v) { this._src = v; const f = this._onload; if (f) queueMicrotask(() => f.call(this)); }
  set srcset(v) { this._srcset = v; }
  set sizes(v) { this._sizes = v; }
};
window.Math.random = () => 0; /* random start = slide 0, no jump */

window.eval(code);

const anchor = document.querySelector("#hero-mosaic a");
const caption = anchor.querySelector("span");

function curIdx() {
  const href = anchor.getAttribute("href") || "";
  return ORDER.indexOf(href.replace("/c/", ""));
}
function dotIdx() {
  const dots = anchor.querySelectorAll(".hero-dots i");
  for (let i = 0; i < dots.length; i++) if (dots[i].className === "on") return i;
  return -1;
}
function pe(type, x, y) {
  const Ctor = window.PointerEvent || window.MouseEvent;
  const e = new Ctor(type, { bubbles: true, cancelable: true, clientX: x, clientY: y });
  anchor.dispatchEvent(e);
  return e;
}
function click() {
  const e = new window.MouseEvent("click", { bubbles: true, cancelable: true });
  anchor.dispatchEvent(e);
  return e;
}
function tap() { pe("pointerdown", 200, 100); pe("pointermove", 204, 102); pe("pointerup", 204, 102); }
function smallDrag() { pe("pointerdown", 200, 100); pe("pointermove", 225, 104); pe("pointerup", 225, 104); }
function vertDrag() { pe("pointerdown", 200, 100); pe("pointermove", 210, 185); pe("pointerup", 210, 185); }
function swipeLeft() { pe("pointerdown", 300, 100); pe("pointermove", 255, 102); pe("pointermove", 200, 103); pe("pointerup", 200, 103); }
function swipeRight() { pe("pointerdown", 100, 100); pe("pointermove", 148, 102); pe("pointermove", 200, 103); pe("pointerup", 200, 103); }

let pass = 0, fail = 0;
function check(name, cond) {
  if (cond) { pass++; console.log("ok   -", name); }
  else { fail++; console.log("FAIL -", name); }
}
const flushMicro = async () => { for (let i = 0; i < 6; i++) await Promise.resolve(); };

await flushMicro(); /* let preloads land */

/* 1. setup */
check("dots rendered (7)", anchor.querySelectorAll(".hero-dots i").length === 7);
check("starts on slide 0 (bee)", curIdx() === 0 && caption.textContent === "Bumble Bee");
check("auto-rotate interval armed (5s)", intervalCount(5000) === 1);

/* 2. tap still navigates */
tap();
const tapClick = click();
check("tap: click not suppressed", tapClick.defaultPrevented === false);
check("tap: slide unchanged", curIdx() === 0);

/* 3. under-threshold drag: no slide change, click intact */
smallDrag();
const sdClick = click();
check("small drag (25px): click not suppressed", sdClick.defaultPrevented === false);
check("small drag (25px): slide unchanged", curIdx() === 0);

/* 4. vertical-dominant drag: ignored */
vertDrag();
const vdClick = click();
check("vertical drag: click not suppressed", vdClick.defaultPrevented === false);
check("vertical drag: slide unchanged", curIdx() === 0);

/* 5. swipe left advances + suppresses click + pauses auto-rotation */
swipeLeft();
check("swipe left: auto interval paused", intervalCount(5000) === 0);
check("swipe left: ~10s resume timer set", hasTimeout(10000));
const swClick = click();
check("swipe left: gesture click suppressed", swClick.defaultPrevented === true);
flushFade();
check("swipe left: advanced to slide 1", curIdx() === 1);
check("swipe left: caption swapped", caption.textContent === TITLES[1]);
check("swipe left: dots track", dotIdx() === 1);
check("after fade: auto still paused", intervalCount(5000) === 0);

/* 6. resume after ~10s, auto-advance continues from manual slide */
runTimeoutsWhere((ms) => ms === 10000);
check("resume: interval re-armed", intervalCount(5000) === 1);
fireIntervals();
flushFade();
check("resume: auto-advance moves to slide 2", curIdx() === 2);

/* 7. swipe right goes back */
swipeRight();
const srClick = click();
check("swipe right: click suppressed", srClick.defaultPrevented === true);
flushFade();
check("swipe right: back to slide 1", curIdx() === 1 && dotIdx() === 1);

/* 8. wrap backward: slide 1 -> 0 -> last */
swipeRight(); click(); flushFade();
check("nav to slide 0", curIdx() === 0);
swipeRight(); click(); flushFade();
check("wrap backward: slide 0 -> slide 6", curIdx() === 6);
check("wrap backward: caption + dots", caption.textContent === TITLES[6] && dotIdx() === 6);

/* 9. wrap forward: last -> 0 */
swipeLeft(); click(); flushFade();
check("wrap forward: slide 6 -> slide 0", curIdx() === 0 && dotIdx() === 0);

/* 10. rapid double-swipe: one gesture outcome only */
const before = curIdx();
swipeLeft();
swipeLeft(); /* second gesture lands mid-fade: busy guard must eat it */
click();
flushFade();
check("rapid double-swipe: advanced exactly once", curIdx() === (before + 1) % ORDER.length);

/* 11. after the dust settles, a fresh swipe works again */
swipeLeft(); click(); flushFade();
check("post-guard swipe advances", curIdx() === (before + 2) % ORDER.length);

/* 12. plain auto-rotation still intact after manual use + resume */
runTimeoutsWhere((ms) => ms === 10000);
fireIntervals(); flushFade();
check("auto-advance after manual session", curIdx() === (before + 3) % ORDER.length);

/* 13. 2026-10-13 swipe-pan fix (Billy): two static guards on index.html.
   (a) The tile anchor must carry touch-action:pan-y, or Safari takes a
   horizontal drag on the tile as a page pan (pointercancel) and the
   swipe handlers above never see the gesture.
   (b) Every hero sky decoration must live inside .heroskyclip: #s-hero
   is position:static, so uncontained decorations resolve against a box
   their flights (to 118vw) escape, widening the page's scrollable
   overflow and letting the whole page pan sideways. */
const cssText = html.slice(0, html.indexOf("<body"));
check("tile CSS: #hero-mosaic a has touch-action:pan-y",
  /#hero-mosaic\s+a\s*\{[^}]*touch-action\s*:\s*pan-y/.test(cssText));
const dom2 = new JSDOM(html, { url: "https://pickmycostume.com/", virtualConsole: vc });
const skyEls = dom2.window.document.querySelectorAll(
  "#s-hero .bat, #s-hero .herostar, #s-hero .herofly, #s-hero .heroleaf, #s-hero .herocloud, #s-hero .heroshoot");
let skyInside = 0;
skyEls.forEach((el) => { if (el.closest(".heroskyclip")) skyInside++; });
check("sky decorations exist in markup", skyEls.length > 0);
check("all sky decorations inside .heroskyclip", skyInside === skyEls.length);

console.log(`\n${pass} pass, ${fail} fail`);
process.exit(fail ? 1 : 0);
