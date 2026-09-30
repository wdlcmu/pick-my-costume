/* Pinpoint resolution audit (Billy 2026-09-25, standing gate):
   the "Already have someone in mind?" surface must resolve a specific name
   or typed query to that costume's detail, never to a generic quiz.
   Asserts:
     1. Every PINPOINT_MAP key points at an idea that exists in the bank.
     2. Every PINPOINT_CHIPS label resolves via pinpointMatch to a real idea
        (a chip that leads nowhere is a bug).
     3. Spot resolution cases land on the right idea, including the
        descriptive queries ("Disney Halloween" -> closest princess idea).
   Usage: node hour-session/pinpoint-resolve.js */
var fs = require("fs"), vm = require("vm");
var src = fs.readFileSync(__dirname + "/../index.html", "utf8");
var block = [...src.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join("\n");

function grab(name){
  var pat = new RegExp("(?:var|function)\\s+" + name + "\\b");
  var m = pat.exec(block);
  if (!m) throw new Error("not found: " + name);
  var bi = block.indexOf("[", m.index), br = block.indexOf("{", m.index);
  var i, open, close;
  if (name === "IDEAS" || name === "PINPOINT_CHIPS"){
    i = bi; open = "["; close = "]";
  } else if (name === "PINPOINT_MAP"){
    i = br; open = "{"; close = "}";
  } else {
    /* function: first brace after the closing paren of the signature */
    i = block.indexOf("{", block.indexOf(")", m.index)); open = "{"; close = "}";
  }
  var depth = 0, j = i, inStr = null, esc = false;
  for (; j < block.length; j++){
    var ch = block[j];
    if (inStr){
      if (esc) esc = false;
      else if (ch === "\\") esc = true;
      else if (ch === inStr) inStr = null;
      continue;
    }
    if (ch === "/" && block[j+1] === "*"){
      var ce = block.indexOf("*/", j+2);
      if (ce === -1) throw new Error("unbalanced comment: " + name);
      j = ce + 1; continue;
    }
    if (ch === "/" && block[j+1] === "/"){
      var le = block.indexOf("\n", j+2);
      j = (le === -1) ? block.length : le; continue;
    }
    if (ch === '"' || ch === "'") inStr = ch;
    else if (ch === open) depth++;
    else if (ch === close){
      depth--;
      if (depth === 0){
        var end = (block[j+1] === ";") ? j + 2 : j + 1;
        return block.slice(m.index, end);
      }
    }
  }
  throw new Error("unbalanced: " + name);
}

/* 2026-09-26: PINPOINT_CHIPS UI was removed (red-team: dead code with licensed
   labels). The grab is now optional: absence skips assertion 2. */
var chipsSrc = "";
try { chipsSrc = grab("PINPOINT_CHIPS"); } catch(e){ /* chips UI removed */ }
var names = ["IDEAS","PINPOINT_MAP",
  "pinpointNormalize","pinpointMatch","pinpointScore","pinpointResolve",
  "pinpointThemeIdeas"];
var lib = names.map(grab).join("\n;\n") + "\n;\n" + chipsSrc + "\nvar PINPOINT_CHIPS = (typeof PINPOINT_CHIPS === 'undefined') ? null : PINPOINT_CHIPS;\n";

var driver = `
;(function(){
  var failures = 0, assertions = 0;
  var byId = {};
  IDEAS.forEach(function(i){ byId[i.id] = i; });

  function ok(cond, msg){
    assertions++;
    if (!cond){ console.log("FAIL " + msg); failures++; }
  }

  /* 1. Every map key points at a real idea. */
  Object.keys(PINPOINT_MAP).forEach(function(k){
    ok(byId[PINPOINT_MAP[k].idea], "map key " + k + " -> unknown idea " + PINPOINT_MAP[k].idea);
  });

  /* 2. Every chip resolves to a real idea (skipped when the chips UI is absent). */
  if (PINPOINT_CHIPS){
    ok(PINPOINT_CHIPS.length > 0, "chips non-empty");
    PINPOINT_CHIPS.forEach(function(label){
      var hit = pinpointMatch(label);
      ok(hit, "chip " + JSON.stringify(label) + " does not resolve");
      if (hit) ok(byId[hit.idea], "chip " + JSON.stringify(label) + " -> unknown idea " + hit.idea);
    });
    ok(PINPOINT_CHIPS.indexOf("Belle") !== -1, "Belle chip present");
  } else {
    console.log("SKIP chips UI removed; assertion 2 not applicable");
  }

  /* 3. Spot resolution cases. */
  function resCase(raw, wantKind, wantIdea){
    var r = pinpointResolve(raw);
    ok(r.kind === wantKind, "resolve " + JSON.stringify(raw) + " kind=" + r.kind + " want " + wantKind);
    if (wantIdea) ok(r.idea === wantIdea, "resolve " + JSON.stringify(raw) + " idea=" + r.idea + " want " + wantIdea);
  }
  resCase("Belle", "match", "enchanted-castle-crew");
  resCase("belle", "match", "enchanted-castle-crew");
  resCase("Disney Halloween", "match", "enchanted-castle-crew");
  resCase("princess", "match", "fairy-tale-princesses");
  resCase("a princess", "match", "fairy-tale-princesses");
  resCase("superhero", "match", "superhero-family");
  resCase("super hero", "match", "superhero-family");
  resCase("Spider-Man", "match", "web-slinger-crew");
  resCase("spider man", "match", "web-slinger-crew");
  resCase("Ariel", "match", "mermaid-crew");
  resCase("Frozen", "match", "snow-sisters");
  resCase("Elsa", "match", "snow-sisters");
  resCase("castle", "fuzzy", "enchanted-castle-crew");
  resCase("ghost", "fuzzy", "classic-ghost");
  resCase("qzxwkv zzz", "nomatch", null);
  /* Trademarked characters deliberately removed from the bank must NOT
     silently resolve to some random idea. */
  var bat = pinpointResolve("batman");
  ok(bat.kind === "nomatch", "batman should be nomatch, got " + bat.kind + " " + bat.idea);
  /* 4. New alias map (P0 item 1, 2026-09-30): required characters first. */
  resCase("Cinderella", "match", "fairy-tale-princesses");
  resCase("cinderella", "match", "fairy-tale-princesses");
  resCase("Cinderella dress", "match", "fairy-tale-princesses");
  resCase("Rapunzel", "match", "fairy-tale-princesses");
  resCase("Moana", "match", "wayfinder-princess");
  resCase("moana", "match", "wayfinder-princess");
  resCase("Snow White", "match", "fairy-tale-princesses");
  resCase("snow white", "match", "fairy-tale-princesses");
  resCase("Aurora", "match", "fairy-tale-princesses");
  resCase("Tiana", "match", "fairy-tale-princesses");
  resCase("Jasmine", "match", "fairy-tale-princesses");
  resCase("Mulan", "match", "fairy-tale-princesses");
  resCase("Merida", "match", "fairy-tale-princesses");
  resCase("Sofia the First", "match", "fairy-tale-princesses");
  resCase("Tangled", "match", "fairy-tale-princesses");
  resCase("Sleeping Beauty", "match", "fairy-tale-princesses");
  resCase("Princess and the Frog", "match", "fairy-tale-princesses");
  resCase("Ursula", "match", "mermaid-crew");
  resCase("Prince Eric", "match", "mermaid-crew");
  resCase("Maui", "match", "wayfinder-princess");
  resCase("Nemo", "match", "under-the-sea");
  resCase("Dory", "match", "under-the-sea");
  resCase("Octonauts", "match", "under-the-sea");
  resCase("Superman", "match", "superhero-family");
  resCase("Wonder Woman", "match", "superhero-family");
  resCase("Iron Man", "match", "tin-hero");
  resCase("Tony Stark", "match", "tin-hero");
  resCase("Captain America", "match", "superhero-family");
  resCase("Deadpool", "match", "superhero-family");
  resCase("Incredibles", "match", "superhero-family");
  resCase("Naruto", "match", "ninja");
  resCase("Sasuke", "match", "ninja");
  resCase("TMNT", "match", "ninja");
  resCase("Leonardo", "match", "ninja");
  resCase("Luffy", "match", "pirate-captain");
  resCase("Captain Hook", "match", "pirate-captain");
  resCase("Zelda", "match", "cardboard-knight");
  resCase("Link", "match", "cardboard-knight");
  resCase("Optimus Prime", "match", "robot-crew");
  resCase("Bumblebee", "match", "robot-crew");
  resCase("Baymax", "match", "robot-crew");
  resCase("Power Rangers", "match", "robot-ranger");
  resCase("Harry Potter", "match", "wizard");
  resCase("Hermione", "match", "wizard");
  resCase("Hogwarts", "match", "wizard");
  resCase("Doctor Strange", "match", "wizard");
  resCase("Scooby-Doo", "match", "mystery-crew");
  resCase("Scooby", "match", "mystery-crew");
  resCase("Darth Vader", "match", "galaxy-knights");
  resCase("Baby Yoda", "match", "galaxy-knights");
  resCase("Grogu", "match", "galaxy-knights");
  resCase("Mandalorian", "match", "galaxy-knights");
  resCase("Chewbacca", "match", "galaxy-knights");
  resCase("R2D2", "match", "galaxy-knights");
  resCase("Leia", "match", "galaxy-knights");
  resCase("Yoshi", "match", "baby-dino");
  resCase("Bowser", "match", "dino-herd");
  resCase("Charizard", "match", "dragon-rider-duo");
  resCase("Simba", "match", "little-lion");
  resCase("Paw Patrol", "match", "rescue-pups");
  resCase("Chase", "match", "rescue-pups");
  resCase("Skye", "match", "rescue-pups");
  resCase("Bandit", "match", "blue-dog-family");
  resCase("Chilli", "match", "blue-dog-family");
  resCase("George Pig", "match", "little-pig-family");
  resCase("Jessie", "match", "toy-box-crew");
  resCase("Buzz", "match", "toy-box-crew");
  resCase("Forky", "match", "toy-box-crew");
  resCase("Lightning McQueen", "match", "kart-racers");
  resCase("Mater", "match", "kart-racers");
  resCase("Joy", "match", "emotion-crew");
  resCase("Sadness", "match", "emotion-crew");
  resCase("BTS", "match", "pop-star");
  resCase("Blackpink", "match", "pop-star");
  resCase("Tinker Bell", "match", "garden-fairy");
  resCase("Fairy Godmother", "match", "garden-fairy");
  resCase("Jack Skellington", "match", "glow-skeleton");
  resCase("Coco", "match", "glow-skeleton");
  resCase("Tanjiro", "match", "bamboo-demon");
  resCase("Demon Slayer", "match", "bamboo-demon");
  resCase("Morticia", "match", "deadpan-diva");
  resCase("Cruella", "match", "deadpan-diva");
  resCase("Enid", "match", "gloom-bloom");
  resCase("Hocus Pocus", "match", "witchy-sisters");
  resCase("Maleficent", "match", "emerald-witch");
  resCase("Scarlet Witch", "match", "little-witch");
  resCase("Foxy", "match", "haunted-animatronics");
  resCase("Thor", "match", "the-olympians");
  resCase("Percy Jackson", "match", "the-olympians");
  resCase("Sonic", "match", "hero-squad");
  resCase("Goku", "match", "hero-squad");
  resCase("PJ Masks", "match", "hero-squad");
  resCase("Prince Charming", "match", "prince-princess");
  resCase("Flynn Rider", "match", "prince-princess");
  resCase("Aladdin", "match", "prince-princess");
  resCase("Corpse Bride", "match", "pumpkin-king-bride");
  resCase("Sally", "match", "pumpkin-king-bride");
  resCase("Miraculous Ladybug", "match", "ladybug");
  resCase("Chat Noir", "match", "black-cat");
  resCase("Fortnite", "match", "player-one-two");
  resCase("Doctor Who", "match", "doctor-bride");
  resCase("Judy Hopps", "match", "safari-zoo-crew");
  resCase("Gru", "match", "goggle-crew");
  resCase("Totoro", "match", "fuzzy-monster");
  resCase("Kirby", "match", "fuzzy-monster");
  resCase("Elmo", "match", "fuzzy-monster");
  resCase("Sulley", "match", "fuzzy-monster");
  resCase("Eevee", "match", "pocket-plush");
  resCase("Labubu", "match", "pocket-plush");
  resCase("Roblox", "match", "block-game-crew");
  resCase("Enderman", "match", "block-game-crew");
  resCase("Impostor", "match", "space-crewmate");
  resCase("Dwarfs", "match", "garden-gnome");
  resCase("Lumiere", "match", "enchanted-castle-crew");
  resCase("Spider-Verse", "match", "web-slinger-crew");
  resCase("Hotel Transylvania", "match", "vampire");
  resCase("Vanellope", "match", "kart-racers");
  /* Common misspellings. */
  resCase("Cinderela", "match", "fairy-tale-princesses");
  resCase("Raponzel", "match", "fairy-tale-princesses");
  resCase("Moanna", "match", "wayfinder-princess");
  resCase("Arora", "match", "fairy-tale-princesses");
  resCase("Wendsday", "match", "deadpan-diva");
  resCase("Pokeman", "match", "pocket-plush");
  resCase("Picachu", "match", "pocket-plush");
  resCase("Mermade", "match", "mermaid-crew");
  resCase("Barby", "match", "plastic-dream-crew");
  resCase("Barbi", "match", "plastic-dream-crew");
  resCase("Elza", "match", "snow-sisters");
  /* 5. Theme fallback (P0 item 2): the typed query has no alias or fuzzy
     match, so the theme layer decides what shows. */
  function themeFirst(raw, wantFirst){
    var ids = pinpointThemeIdeas(raw);
    ok(ids.length > 0, "theme " + JSON.stringify(raw) + " returned no ideas");
    if (wantFirst) ok(ids[0] === wantFirst, "theme " + JSON.stringify(raw) + " first=" + JSON.stringify(ids[0]) + " want " + wantFirst);
  }
  function noTheme(raw){
    var ids = pinpointThemeIdeas(raw);
    ok(ids.length === 0, "theme " + JSON.stringify(raw) + " should be empty, got " + ids.join(","));
  }
  function nomatchThenTheme(raw, wantFirst){
    var r = pinpointResolve(raw);
    ok(r.kind === "nomatch", "resolve " + JSON.stringify(raw) + " kind=" + r.kind + " want nomatch");
    themeFirst(raw, wantFirst);
  }
  nomatchThenTheme("glass slipper", "fairy-tale-princesses");
  nomatchThenTheme("tiara", "fairy-tale-princesses");
  nomatchThenTheme("ball gown", "fairy-tale-princesses");
  nomatchThenTheme("crown", "fairy-tale-princesses");
  themeFirst("cape", "superhero-family");
  themeFirst("mask", "superhero-family");
  noTheme("qzxwkv zzz");
  noTheme("toaster oven repair");

  console.log("assertions: " + assertions);
  console.log(failures === 0 ? "PINPOINT RESOLVE: ALL PASS" : "PINPOINT RESOLVE: " + failures + " FAILURES");
  return failures;
})
`;

var sandbox = {console: console};
vm.createContext(sandbox);
var failures = vm.runInContext(lib + "\n" + driver + "()", sandbox);
process.exit(failures ? 1 : 0);
