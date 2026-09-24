// Per-idea share pages: /c/<slug> unfurls the shared costume's own
// illustration for messengers, then redirects humans to /?idea=<slug>.
// Regenerate with gen_share_function.py when the idea bank changes.
var IDEAS = {"neon-demon-hunter": {"t": "Neon Demon Hunter", "b": "Streetwear with glowing sigils, a toy sword, and pop-idol hair and makeup."}, "classic-ghost": {"t": "Classic Ghost", "b": "A white sheet with cut-out eyes. The easiest costume ever made."}, "blue-dog-family": {"t": "Heeler Family", "b": "Dog-ear headbands and blue-or-orange shirts: mama, dad, and the pups."}, "superhero-family": {"t": "Superhero Family", "b": "Red sweatsuits, black eye masks, felt logo -- the whole family goes super."}, "blue-alien-ohana": {"t": "Blue Alien Ohana", "b": "Blue hoodie, big ears: the alien, the girl, or the whole ohana."}, "emerald-witch": {"t": "Emerald Witch", "b": "An all-green-everything gown, dramatic makeup, and a pointy hat gone couture."}, "gloom-bloom": {"t": "Gloom & Bloom", "b": "Braids and black for Gloom, color-pop and smiles for Bloom."}, "deadpan-diva": {"t": "Deadpan Diva", "b": "Black dress, two braids, pale makeup, and a stare that ends conversations."}, "safari-zoo-crew": {"t": "Safari / Zoo Crew", "b": "Everyone picks an animal: closet clothes in matching colors plus an ear headband."}, "fairy-tale-princesses": {"t": "Fairy Tale Princesses", "b": "A dress or a crown from the closet. Every princess works."}, "tin-hero": {"t": "The Tin Hero", "b": "Red and gold plus a glowing chest circle: the suit does the talking."}, "good-witch-bad-witch": {"t": "Good Witch, Bad Witch", "b": "Green face paint and black for one, pink gown and crown for the other."}, "fuzzy-monster": {"t": "Fuzzy Monster", "b": "A pastel fuzzy sweatsuit with giant googly eyes and an oversized stitched smile."}, "pocket-plush": {"t": "Pocket Plush Monster", "b": "A fuzzy one-piece, giant ears, a stitched smile, and an oversized collector tag."}, "soccer-squad": {"t": "Soccer Squad", "b": "Jerseys for the players, black for the ref, one red card for the drama."}, "glow-skeleton": {"t": "Glow Skeleton", "b": "Black sweats with glow-in-the-dark bone tape, plus glow bracelets."}, "block-game-crew": {"t": "Block Game Crew", "b": "Cardboard-box heads: pick your blocky hero. Pixelated and perfect."}, "web-slinger-crew": {"t": "Web-Slinger Crew", "b": "Red, black, and pink hoodies plus masks -- pick your spider."}, "mermaid-crew": {"t": "Mermaid Crew", "b": "The mermaid, the prince, the sea king, the sea witch, or the crab: pick your role."}, "little-pig-family": {"t": "Little Pig Family", "b": "Pink clothes and a snout headband; little brother brings the dinosaur."}, "enchanted-castle-crew": {"t": "Enchanted Castle Crew", "b": "The bookish princess, the cursed prince, the talking candelabra, the talking clock, the talking teapot: pick your role."}, "bumble-bee": {"t": "Bumble Bee", "b": "Black sweats with yellow tape stripes and soft felt antennae."}, "baby-dino": {"t": "Baby Dinosaur", "b": "Green hoodie, felt spikes down the back, stuffed tail."}, "little-lion": {"t": "Little Lion", "b": "Tan sweatsuit plus a fuzzy mane hood."}, "tiny-firefighter": {"t": "Tiny Firefighter", "b": "Red sweats, a plastic helmet, and a toy hose if you are feeling it."}, "little-shark": {"t": "Little Shark", "b": "Gray hoodie with a felt fin glued on the back."}, "walking-taco": {"t": "Walking Taco", "b": "Tan vest painted like a taco shell with felt toppings."}, "ramen-bowl": {"t": "Ramen Bowl", "b": "Cardboard bowl rim, noodle-yarn hair, a foam egg on top."}, "tiny-snail": {"t": "Tiny Snail", "b": "Neutral clothes plus a lightweight spiral shell from cardboard worn like a backpack."}, "little-witch": {"t": "Little Witch", "b": "Black cape, pointy hat, striped tights, green face paint."}, "spider": {"t": "Eight-Legged Spider", "b": "Black sweats with stuffed sock legs attached at the sides."}, "backyard-hero": {"t": "Backyard Superhero", "b": "Short cape plus a first initial on the chest, mask optional."}, "pickle": {"t": "Pickle", "b": "Green tunic, bumpy texture, smug grin. Peak comedy, zero effort."}, "vampire": {"t": "Classic Vampire", "b": "Black cape, fangs, slicked hair."}, "bamboo-demon": {"t": "Bamboo-Muzzle Demon", "b": "Pink robe, long dark wig, and a cardboard bamboo muzzle tied with ribbon."}, "emoji-crew": {"t": "Emoji Crew", "b": "Everyone picks an emoji: a yellow tee plus a big printed face."}, "robot-crew": {"t": "Cardboard Robot Crew", "b": "Boxy robots built from cardboard boxes, foil, and bottle-cap buttons."}, "cereal-crew": {"t": "Cereal Crew", "b": "Solid-color clothes plus a cereal-box front you decorate."}, "decades-crew": {"t": "Decades Crew", "b": "Each person picks a decade and dresses from their own closet."}, "under-the-sea": {"t": "Under the Sea", "b": "Jellyfish from an umbrella with ribbon tentacles, crab from red clothes and claw mittens, plus fish, seaweed, and waves."}, "dino-rangers": {"t": "Dino Rangers", "b": "Khaki outfits for the grown-ups, dino hoods for the kids -- leash a toy raptor."}, "board-game-pieces": {"t": "Board Game Pieces", "b": "Each person picks a piece: cardboard die, playing card, pawn, or domino over monochrome clothes."}, "rain-cloud-rainbow": {"t": "Rain Cloud and Rainbow", "b": "One wears gray with cotton clouds and paper raindrops; the other wears rainbow stripes."}, "doctor-bride": {"t": "The Doctor & the Bride", "b": "Green face paint and neck bolts for one; tall streaked wig and torn gown for the other."}, "breakfast-buffet": {"t": "Breakfast Buffet", "b": "Everyone picks a breakfast: egg, bacon, toast, pancake, OJ, coffee. Cardboard signs over normal clothes."}, "ghost-hunters": {"t": "Ghost Hunters", "b": "Khaki jumpsuits, cardboard ghost-catching backpacks, name patches."}, "haunted-animatronics": {"t": "Haunted Animatronics", "b": "Glitchy mascot heads from cardboard boxes, flickering LED eyes, jerky moves."}, "mystery-crew": {"t": "Mystery Crew", "b": "Assign the leader, the style icon, the brains, the goofball, and one very good dog."}, "headless-horsemen": {"t": "Headless Horsemen", "b": "Black capes, jack-o-lanterns held at shoulder height, group gallop."}, "haunted-portraits": {"t": "Haunted Portraits", "b": "Gray makeup, old-timey clothes, hold a gilt frame."}, "goggle-crew": {"t": "Goggle Crew", "b": "Yellow tees, denim overalls, goggles, black gloves."}, "garden-gnome": {"t": "Garden Gnome", "b": "Wear earth tones, make a pointy hat from cardboard, draw a white beard, carry a tiny fishing rod or garden shovel."}, "black-cat": {"t": "Black Cat Burglar", "b": "Black sweatsuit, cat-ear headband, eye mask -- add a toy sack for burglar."}, "block-monster": {"t": "Block Monster", "b": "Wear all one solid color, square up your silhouette with foam or cardboard blocks on shoulders/limbs, draw a pixelated face."}, "space-crewmate": {"t": "Space Crewmate", "b": "Colored sweatsuit plus a cardboard backpack -- pick red, you're always sus."}, "sun-moon": {"t": "Sun and Moon", "b": "One in yellow with cardboard rays, one in navy with paper stars and a crescent."}, "moth-porch-light": {"t": "Moth and Porch Light", "b": "One wears neutrals with cardboard wings; the other wears yellow and carries a lampshade."}, "raptor-ranger": {"t": "Raptor & Ranger", "b": "One khaki ranger, one green dino hood -- the ranger holds the leash."}, "cat-mouse": {"t": "Cat & Mouse", "b": "Cat ears versus mouse ears -- spend the night chasing each other."}, "ketchup-mustard": {"t": "Ketchup & Mustard", "b": "Red bottle tunic and cap for one, yellow for the other."}, "plumber-duo": {"t": "Plumber Brothers", "b": "Overalls, red and green caps and shirts, drawn mustaches."}, "office-couple": {"t": "Office Couple", "b": "White shirts, name tags, and a teapot -- the office's finest."}, "burger-joint-couple": {"t": "Burger Joint Couple", "b": "White apron plus fake mustache, curly red wig plus glasses -- burger shop owners."}, "plug-socket": {"t": "Plug and Socket", "b": "Cardboard plug and outlet worn front and back."}, "salt-pepper": {"t": "Salt and Pepper", "b": "One all-white, one all-black, with S and P signs."}, "lost-tourist": {"t": "Lost Tourist", "b": "Wear wrinkled clothes, carry a crumpled map, add one luggage tag backwards on your shoulder."}, "tooth-fairy": {"t": "Tooth and Tooth Fairy", "b": "One all-white with a cardboard tooth outline; the other adds wings and an envelope of tooth money."}, "web-hero-duo": {"t": "Web Hero Duo", "b": "Red-blue sweatsuit plus web mask; partner gets the black jacket and attitude."}, "plague-doctor": {"t": "Plague Doctor", "b": "Long coat, wide hat, beaked mask."}, "crowd-camouflage": {"t": "Crowd Camouflage", "b": "Gray hoodie, dark pants, blank expression. Vanish into any crowd."}, "error-404": {"t": "Error 404", "b": "Wear all black with 'Page Not Found' printed on your chest; carry a phone with a cracked-screen prop or broken GPS."}, "zombie-coworker": {"t": "Zombie Coworker", "b": "Torn button-down, loosened tie, pale makeup, coffee mug."}, "safari-photographer": {"t": "Safari Photographer", "b": "Khaki vest, toy camera and binoculars, plus a stuffed lion cub under one arm."}, "player-one-two": {"t": "Player One & Two", "b": "Matching tees with 1 and 2, toy controllers in hand, ready for co-op."}, "dinosaur-family": {"t": "Dinosaur Family", "b": "Matching dino-hoodie sweatsuits for the whole crew, spikes down every back."}, "snow-sisters": {"t": "Snow Sisters", "b": "The ice queen, the snow princess, the talking snowman, the reindeer: pick your role."}};

// Old slugs renamed in the Sep 2026 IP sweep: keep every share link ever
// minted working by resolving them to the current canonical slug.
var ALIASES = {"bluey-family": "blue-dog-family", "incredibles-family": "superhero-family", "stitch-ohana": "blue-alien-ohana", "wednesday-enid": "gloom-bloom", "iron-man": "tin-hero", "elphaba-glinda": "good-witch-bad-witch", "minecraft-crew": "block-game-crew", "spider-verse": "web-slinger-crew", "spider-man-mj": "web-hero-duo", "peppa-pig": "little-pig-family", "jurassic-rangers": "dino-rangers", "creeper": "block-monster", "among-us": "space-crewmate", "little-mermaid-crew": "mermaid-crew", "bumblebee": "bumble-bee", "jim-pam": "office-couple", "bob-linda": "burger-joint-couple", "be-our-guest": "enchanted-castle-crew", "disney-princesses": "fairy-tale-princesses"};

function esc(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;")
          .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

export function onRequest(context) {
  var slug = context.params.slug || "";
  if (ALIASES[slug]) slug = ALIASES[slug]; /* renamed slug -> canonical */
  var idea = IDEAS[slug];
  if (!idea) return new Response("Not found", { status: 404 });
  var title = esc(idea.t), blurb = esc(idea.b);
  var img = "https://pickmycostume.com/images/og/" + slug + ".jpg";
  /* Preserve any extra query params (e.g. tracking tags) across the redirect. */
  var _qp = new URLSearchParams(new URL(context.request.url).search);
  _qp.set("idea", slug);
  var target = "/?" + _qp.toString();
  /* Shared metadata head: identical for every visitor. iMessage's
     sender-side preview fetch uses a spoofed composite UA (Safari plus
     Facebook/Twitter crawler strings); per Apple TN3156 it runs no JS and
     follows no meta refresh, so it gets clean metadata-only HTML with no
     redirect machinery. The tags are identical for everyone: not cloaking. */
  var head = "<!DOCTYPE html>" +
    "<html lang=\"en\"><head><meta charset=\"utf-8\">" +
    "<title>" + title + " - Pick My Costume</title>" +
    "<meta property=\"og:type\" content=\"website\">" +
    "<meta property=\"og:url\" content=\"https://pickmycostume.com/c/" + slug + "\">" +
    "<meta property=\"og:title\" content=\"" + title + " - Pick My Costume\">" +
    "<meta property=\"og:description\" content=\"" + blurb + "\">" +
    "<meta property=\"og:image\" content=\"" + img + "\">" +
    "<meta property=\"og:image:secure_url\" content=\"" + img + "\">" +
    "<meta property=\"og:image:type\" content=\"image/jpeg\">" +
    "<meta property=\"og:image:width\" content=\"1200\">" +
    "<meta property=\"og:image:height\" content=\"630\">" +
    "<meta property=\"og:image:alt\" content=\"" + title + " costume idea\">" +
    "<meta name=\"twitter:card\" content=\"summary_large_image\">" +
    "<meta name=\"twitter:title\" content=\"" + title + " - Pick My Costume\">" +
    "<meta name=\"twitter:description\" content=\"" + blurb + "\">" +
    "<meta name=\"twitter:image\" content=\"" + img + "\">" +
    "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">";
  var _ua = (context.request.headers.get("user-agent") || "").toLowerCase();
  var _imsgFetch = _ua.indexOf("facebookexternalhit") !== -1 &&
                   _ua.indexOf("facebot") !== -1 &&
                   _ua.indexOf("twitterbot") !== -1;
  var html;
  if (_imsgFetch) {
    html = head +
      "</head><body><h1>" + title + "</h1><p>" + blurb + "</p>" +
      "<p><a href=\"https://pickmycostume.com/\">Pick My Costume</a></p></body></html>";
  } else {
    html = head +
      "<noscript><meta http-equiv=\"refresh\" content=\"0;url=" + target + "\"></noscript>" +
      "<script>location.replace(\"" + target + "\");</script>" +
      "</head><body><p>Taking you to Pick My Costume&hellip; " +
      "<a href=\"" + target + "\">" + title + "</a></p></body></html>";
  }
  return new Response(html, {
    headers: {
      "Content-Type": "text/html;charset=utf-8",
      "Cache-Control": "public, max-age=3600"
    }
  });
}
