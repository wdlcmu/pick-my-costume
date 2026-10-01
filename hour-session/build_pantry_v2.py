#!/usr/bin/env python3
"""Build pantry.html v2 — accuracy-first 'what do you have' prototype.
Reads costume build instructions, applies the hand-audited requirement mapping,
and emits a standalone HTML page. No deploy, no nav changes.

TEMPLATE IS THE SOURCE OF TRUTH (2026-09-26): it now carries everything that
was previously maintained by direct pantry.html edits — photo thumbnails,
IDEA_EMOJI emoji-tile map + ideaEmoji() + cardHtml tile markup, search-first
supply picker, supply emoji, the "Beat my pantry" challenge flow (?kit= links,
dare banner, recipient pre-tick), and the 2026-09-26 challenge honesty fixes
D1-D6 (honest challengeClaim(), stable supply-ID kit encoding, track() analytics
fix, challengeLink kit+pick+sid), and the 2026-09-27 cold-user QA fixes
(pantryTapGuard 400ms bounce guard on supply ticks, .frow min-height:44px) --
ported from direct pantry.html edits into TEMPLATE on 2026-09-27 so the next
regen no longer wipes them. NEVER edit pantry.html directly; change
TEMPLATE and regenerate.
"""
import json, re, collections, html as htmllib, os

BANK_HTML = '/home/hatch/workspace/builds/pick-my-costume/index.html'
OUT = '/home/hatch/workspace/builds/pick-my-costume/pantry.html'
# Harness override for the output path (the store-run tier gate runs the
# generator to a temp file and byte-compares). Never set on real runs.
OUT = os.environ.get('PMC_OUT', OUT)

N = None
def o(*ids): return [list(ids)]            # one requirement, one OR-group
def a(*gs):  return [list(g) for g in gs]  # AND of groups
X = [[N]]                                   # unmapped: honestly "still need"

# ---------------------------------------------------------------- pantry
PANTRY = [
    {'id':'scissors','label':'Scissors','group':'staples','staple':True},
    {'id':'tape','label':'Tape (any kind)','group':'staples','staple':True},
    {'id':'paper-pen','label':'Paper and pen','group':'staples','staple':True},
    {'id':'cardboard','label':'Cardboard box','group':'paper'},
    {'id':'construction-paper','label':'Construction paper','group':'paper'},
    {'id':'paper-bag','label':'Brown paper bag','group':'paper'},
    {'id':'paper-plates','label':'Paper plates','group':'paper'},
    {'id':'newspaper','label':'Newspaper','group':'paper'},
    {'id':'white-tshirt','label':'White t-shirt','group':'clothes','staple':True},
    {'id':'tshirt','label':'T-shirt (any color)','group':'clothes','staple':True},
    {'id':'black-clothes','label':'Black clothes','group':'clothes','staple':True},
    {'id':'hoodie','label':'Hoodie','group':'clothes'},
    {'id':'sweatsuit','label':'Sweatshirt + sweatpants','group':'clothes'},
    {'id':'bedsheet','label':'Old bedsheet','group':'clothes','staple':True},
    {'id':'pillowcase','label':'Pillowcase','group':'clothes','staple':True},
    {'id':'socks','label':'Old socks','group':'clothes'},
    {'id':'hat','label':'Hat or cap','group':'clothes'},
    {'id':'sunglasses','label':'Sunglasses','group':'clothes'},
    {'id':'headband','label':'Headband (any color)','group':'clothes'},
    {'id':'red-headband','label':'Red headband','group':'clothes'},
    {'id':'glue','label':'Craft glue','group':'craft'},
    {'id':'markers','label':'Markers','group':'craft','staple':True},
    {'id':'yarn','label':'Yarn, string, or ribbon','group':'craft'},
    {'id':'felt','label':'Felt sheets','group':'craft'},
    {'id':'pipe-cleaners','label':'Pipe cleaners','group':'craft'},
    {'id':'safety-pins','label':'Safety pins','group':'craft'},
    {'id':'stickers','label':'Stickers','group':'craft'},
    {'id':'balloons','label':'Balloons','group':'craft'},
    {'id':'foil','label':'Aluminum foil','group':'craft'},
    {'id':'stuffing','label':'Pillow stuffing / cotton balls','group':'craft'},
    {'id':'face-paint','label':'Face paint or makeup','group':'face'},
]
GROUPS = [
    {'id':'staples','label':'Household staples'},
    {'id':'paper','label':'Paper and boxes'},
    {'id':'clothes','label':'Clothes and linens'},
    {'id':'craft','label':'Craft drawer'},
    {'id':'face','label':'Face and makeup'},
]
VALID_IDS = {p['id'] for p in PANTRY}

# ---------------------------------------------------------------- audit
# Every material text -> (requirement groups, confidence tag).
# Tags: exact   = text names the pantry item (or a true subtype of it)
#       blessed = substitution explicitly permitted by that costume's own instructions
#       lenient = deliberate documented leniency (craft consumables are multi-variant;
#                 tape label says "any kind"; garments are NOT lenient on color)
AUDIT = {}
def put(text, groups, tag):
    # id validity is checked once, after the color-qualification pass
    AUDIT[text] = (groups, tag)

E='exact'; B='blessed'; L='lenient'
# -- staples & tools
put("Scissors", o('scissors'), E)
put("Scissors (make: household tools)", o('scissors'), E)
put("Scissors (make: from home)", o('scissors'), E)
put("Tape", o('tape'), E)
put("Tape (make: from home)", o('tape'), E)
put("Tape (make: use what you own)", o('tape'), E)
put("Clear tape (make: household tools)", o('tape'), E)
put("Masking tape", o('tape'), L)
put("Packing tape", o('tape'), L)
put("Duct tape, 1 roll", o('tape'), L)
put("Silver duct tape", o('tape'), L)
put("Gray duct tape", o('tape'), L)
put("Yellow duct or electrical tape", o('tape'), L)
put("Red duct or electrical tape", o('tape'), L)
put("White athletic tape, 1 roll", o('tape'), L)
# 2026-09-27 red-team: web-slinger-kid (bank 138). Black tape checkbox exists
# (tape-black); TAPE_HINTS refines the generic 'tape' group to it.
put("Black electrical tape for web lines, 1 roll", o('tape'), B)
put("Yellow reflective tape, 1 roll", o('tape'), L)
put("Tape and scissors (make: from home)", a(['tape'],['scissors']), E)
put("Tape and scissors (make: household tools)", a(['tape'],['scissors']), E)
put("Scissors and tape (make: household tools)", a(['scissors'],['tape']), E)
put("Scissors and tape (make: from home)", a(['scissors'],['tape']), E)
put("Scissors, tape", a(['scissors'],['tape']), E)
put("Tape, scissors", a(['tape'],['scissors']), E)
put("Scissors and clear tape (make: household tools)", a(['scissors'],['tape']), E)
put("Tape, string, scissors (make: household tools)", a(['tape'],['yarn'],['scissors']), E)
put("String and tape (make: household tools)", a(['yarn'],['tape']), E)
put("Tape and string (make: household tools)", a(['tape'],['yarn']), E)
put("Tape and string for wearing (make: household tools)", a(['tape'],['yarn']), E)
put("Scissors and tape or string (make: household tools)", a(['scissors'],['tape','yarn']), E)
put("Paintbrush, scissors, tape (make: household tools)", a([N],['scissors'],['tape']), E)
put("Packing tape or glue, scissors", a(['tape','glue'],['scissors']), E)
put("Scissors, tape or glue", o('scissors','tape','glue'), E)
put("Tape or glue", o('tape','glue'), E)
put("Hot glue and scissors", a([N],['scissors']), E)
put("Hot glue, scissors, face paint", a([N],['scissors'],['face-paint']), E)
put("Hot glue, scissors, pink marker, tape", a([N],['scissors'],['markers'],['tape']), E)
put("Hot glue, scissors, a utility knife (adults only)", a([N],['scissors']), E)
put("Hot glue gun", X, E)
put("Hot glue gun or fabric glue", o(N,'glue'), E)
put("Fabric glue", o('glue'), E)
put("Craft glue", o('glue'), E)
put("Fabric glue or safety pins", o('glue','safety-pins'), E)
put("Safety pins or fabric glue", o('safety-pins','glue'), E)
put("Scissors, fabric glue or safety pins", a(['scissors'],['glue','safety-pins']), E)
put("Black fabric glue or a needle and black thread", o('glue'), L)
put("Glitter glue, 1 tube", X, E)
put("Silver glitter glue, 1 tube", X, E)
put("Safety pins", o('safety-pins'), E)
put("Safety pins (make: use what you own)", o('safety-pins'), E)
put("Safety pins, 4", o('safety-pins'), E)
put("Safety pins, 6", o('safety-pins'), E)
put("Safety pins, 4 per kid", o('safety-pins'), E)
put("Tan or brown tank top, 1 (own, or buy: thrift store)", X, E)
put("Plaid flannel shirt, 1 (own, or buy: thrift store)", X, E)
put("Old hat, 1 (own, or buy: thrift store)", X, E)
put("Black fedora or hat, 1", X, E)
put("Black witch hats, 3", X, E)
put("Safety pins or tape (make: from home)", o('safety-pins','tape'), E)
put("Tape or safety pins", o('tape','safety-pins'), E)
put("Safety pin or ribbon, 1 (make: from sewing kit)", o('safety-pins','yarn'), E)
put("Rubber bands or tape (own)", o('tape'), E)
put("Pen (own)", o('paper-pen'), E)
put("Paper and pencil for sketching (own)", o('paper-pen'), E)
put("Order pad and pencil (own, or buy: dollar store)", o('paper-pen'), E)
put("Paper map, 1", o('paper-pen'), L)
put("1 printed decade card per person, e.g. 70s, 80s, 90s (make: hand-letter on paper)", o('paper-pen'), E)
put("Large shipping tag or big index card", o(N,'paper-pen'), L)
put("Marker (make: household)", o('markers'), E)
put("Marker for writing names (make: household)", o('markers'), E)
put("Markers (own, or buy: dollar store)", o('markers'), E)
put("Markers (make: household)", o('markers'), E)
put("Markers, several colors (make: from home)", o('markers'), E)
put("Markers or crayons (own)", o('markers'), L)
put("Markers in black, red, blue (make: use what you own)", o('markers'), L)
put("Black marker", o('markers'), E)
put("Black marker, 1 (make: from home)", o('markers'), E)
put("Black permanent marker, 1 (make: from home)", o('markers'), E)
put("Black markers (make: household)", o('markers'), E)
put("Black marker, 1 (own)", o('markers'), E)
put("Black spray paint or black markers", o('markers'), E)
put("Brown and tan markers or crayons (make: from home)", o('markers'), L)
put("Brown and tan markers or paint", o('markers'), E)
put("Brown paint or marker for the cone crosshatch", o('markers'), E)
put("Red marker for the label (make: household)", o('markers'), E)
put("Marker and ruler (make: household)", a(['markers'],[N]), E)
put("Gold or silver paint or markers", o(N,'markers'), E)
put("Iron-on letters or fabric markers, spelling 1 and 2", o(N,'markers'), E)
put("White paper and markers for name patches (make: use what you own)", a(['construction-paper'],['markers']), E)
put("Paintbrushes", X, E)
put("Toy paintbrush, 1", X, E)
put("Foam brush or paintbrush (own, or buy: craft store)", X, E)
put("Acrylic paint in each hero's colors", X, E)
put("White and black acrylic paint", X, E)
put("Silver acrylic paint", X, E)
put("Yellow and orange acrylic paint", X, E)
put("Gray and white acrylic paint", X, E)
put("Dark brown acrylic paint, 1 bottle", X, E)
put("Brown acrylic paint, 1 bottle", X, E)
put("Blue paint for the hat", X, E)
put("White and red paint for the bowl", X, E)
put("White fabric paint for the labels", X, E)
put("White fabric paint or white paper", o(N,'construction-paper'), B)
put("Green fabric paint", X, E)
put("Fabric paint for the team emblem", X, E)
put("Neon fabric paint in 2 to 3 colors", X, E)
put("Black fabric paint or black face paint, 1 tube", o('face-paint'), E)
put("Paint in gray, black, and one accent color", X, E)
put("Orange and black paint, 1 set", X, E)
put("Brown paint, 1 bottle", X, E)
put("Acrylic paints in bright colors, 1 set", X, E)
put("Patchwork-style dress, 1", X, E)
put("Black boots or shoes, 1 pair (own)", X, E)
put("Black loafers or dress shoes, 1 pair (own)", X, E)
put("Dresses in green, purple, and orange, 3", X, E)
put("Long black dress or gown, 1", X, E)

# -- paper & boxes
put("Large cardboard boxes (make: collect spares)", o('cardboard'), E)
put("1 large cardboard box per person (make: ask a grocery store for spares)", o('cardboard'), E)
put("1 large cardboard box (make: cut it into square blocks)", o('cardboard'), E)
put("Large cardboard box, 1 (make: cut two wing shapes from it)", o('cardboard'), E)
put("Large cardboard box, 1 (make: cut a big triangle, about 3 feet tall)", o('cardboard'), E)
put("Large cardboard circle or shallow bowl shape, 1 (make: cut from a big box, about 2 feet wide)", o('cardboard'), E)
put("1 large cardboard box per person, big enough to cover the head (make: use what you own)", o('cardboard'), E)
put("1 medium cardboard box per person, big enough to fit over the torso (make: from home or moving boxes)", o('cardboard'), E)
put("1 small cardboard box per person, for the head (make: from cereal or shoe boxes)", o('cardboard'), E)
put("1 medium cardboard box for the torso (make: from home)", o('cardboard'), E)
put("Cardboard box, 1 large (make: cut two flat panels, one per person)", o('cardboard'), E)
put("Cardboard box, 1 medium (make: tall enough to cover the torso)", o('cardboard'), E)
put("Cardboard box, 1 large (make: from a shipping box)", o('cardboard'), E)
put("Crepe paper in rainbow colors, 6 rolls", X, E)
put("Crepe paper or raffia for the skirt, 2 rolls", X, E)
put("Wrapped candy, 2 bags", X, E)
put("1 small cardboard box per person (make: use what you own)", o('cardboard'), E)
put("Cardboard sheets, 1 per person (make: cut from boxes)", o('cardboard'), E)
put("1 large cardboard sheet or a flattened box (make: from home)", o('cardboard'), E)
put("Cardboard, 1 sheet about 12x16 inches (make: from a box flap)", o('cardboard'), E)
put("Empty cereal boxes, 1 per person (make: save from home)", o('cardboard'), E)
put("1 cardboard crown per person (make: from a cereal box)", o('cardboard'), E)
put("1 cardboard crown (make: from a cereal box)", o('cardboard'), E)
put("1 sheet cardboard for the hat (make: from a box)", o('cardboard'), E)
put("1 cardboard tube from wrapping paper or paper towels (make: save from home)", o('cardboard'), L)
put("1 sheet black cardboard for the hat", o('cardboard'), E)
put("1 sheet black cardboard per person (make: from a box)", o('cardboard'), E)
put("Clock: brown cardboard circle and hands (make: from a box)", o('cardboard'), E)
put("Teapot: white pot or cardboard pot body (make: from a box)", o(N,'cardboard'), E)
put("Fish: silver or blue clothes and 1 large cardboard fish cutout (make: from home)", a([N],['cardboard']), E)
put("Toy crab or cardboard crab (make: cut one from red paper, or buy: toy store)", o(N,'cardboard'), E)
put("Cardboard or craft foam for the beak, 1 sheet", o('cardboard','construction-paper'), B)
put("Black gloves, 1 pair", X, E)
put("Black sweatshirt and black sweatpants (make: from closet)", o('black-clothes'), E)
put("Green bubble wrap or green pom-poms, about 20", X, E)
put("Jellyfish: 1 clear umbrella and pastel ribbons (buy umbrella: dollar store; buy ribbons: craft store; crepe paper strips work too)", X, E)
put("White craft foam or a foam ball, 1", o(N,'paper-white'), B)
put("White stickers or white electrical tape, 1 roll", o('stickers','tape'), B)
put("Pink paper cup, 1 per snout (make: from kitchen drawer)", X, E)
put("Craft foam, 1 sheet", o(N,'cardboard'), B)
put("1 large picture frame or cardboard frame per person", o(N,'cardboard'), E)
put("Toy binoculars", o(N,'cardboard'), B)
put("2 toy tennis rackets", o(N,'cardboard'), B)
put("Toy game controllers, 2", X, E)
put("Toy camera", X, E)
put("1 large brown paper bag", o('paper-bag'), E)
put("Brown felt scraps for crust, or a brown paper bag", o(N,'paper-bag'), E)
put("1 large white paper plate or cardboard circle per person (make: use what you own)", o('paper-plates','cardboard'), E)
put("2 white paper plates for the caps (make: use what you own)", o('paper-plates'), E)
put("2 white paper plates or cardstock sheets (make: from home)", o('paper-plates','construction-paper'), E)
put("Paper plate, 1 (make: from home)", o('paper-plates'), E)
put("Newspaper or tissue paper for stuffing (make: from home)", o('newspaper'), E)
put("White cardstock, 1 large sheet", o('construction-paper'), E)
put("White poster board, 2 sheets", o('construction-paper'), L)
put("Cardstock or foam letter for the first initial (make: cut from cardstock, or buy: craft store)", o('construction-paper'), E)
put("White paper or card for the eye spots (make: use what you own)", o('construction-paper'), L)
# 2026-09-27 red-team: web-slinger-kid (bank 138). "White" auto-qualifies the
# construction-paper group to paper-white via _qualify_groups.
put("White paper or cardstock for eye lenses, 1 sheet (make: cut from paper)", o('construction-paper'), E)
put("Blue paper raindrops, about 15 (make: cut from blue construction paper)", o('construction-paper'), B)
put("White and yellow paper for the crescent (make: from home)", o('construction-paper'), L)
put("Paper for the sandwich prop, 1 sheet (own)", o('construction-paper'), L)
put("Red paper for the bottle cap, 1 sheet", o('paper-red'), E)
put("Red acrylic paint or red paper, 1", o(N,'paper-red'), B)
put("Yellow paper for fry sticks", o('paper-yellow'), E)
put("Yellow cardstock, 2 sheets", o(N,'construction-paper'), B)
put("Red cardstock rectangle, 3x4 inches (make: cut from a folder or colored paper)", o('construction-paper'), E)
put("Black construction paper (make: cut a mask from it)", o('construction-paper'), E)
put("2 large googly eyes, 3 inches or bigger", o(N,'construction-paper'), B)
put("2 googly eyes, large", o(N,'construction-paper'), B)
put("Sticker dots or round stickers, 1 sheet", o('stickers','construction-paper'), B)
put("Silver star stickers, 1 sheet", o('stickers','construction-paper'), B)
put("Colored dot stickers or pom-poms for sprinkles", o('stickers','construction-paper'), B)
put("White circle stickers or white paper, 2", o('stickers','construction-paper'), L)
put("Flag sticker or iron-on patch", o('stickers'), E)
put("Fake flowers", o(N,'construction-paper'), B)
put("Fake magnifying glass", X, E)
put("4 to 6 white plastic grocery bags (make: save from home)", X, E)
put("1 tan paper party hat or cone", X, E)
put("Gold paper crown or plastic crown", X, E)
put("Luggage tag, 1", X, E)
put("Blank adhesive name tag", X, E)
put("Name tags, 2", X, E)
put("Large shipping tag or big index card", o(N,'paper-pen'), L)
put("Red and white striped wrapping paper or paint", X, E)
# -- clothes & linens
put("1 white t-shirt", o('white-tshirt'), E)
put("White t-shirt, 1 (own, or buy: thrift store)", o('white-tshirt'), E)
put("White t-shirt for the marshmallow, 1 (own)", o('white-tshirt'), E)
put("White shirt for the egg (own)", o('white-tshirt'), L)
put("1 white bedsheet or large white t-shirt to wear (make: from closet)", o('bedsheet','white-tshirt'), E)
put("White t-shirts and white shorts or skirts, one set each (make: from closet)", a(['white-tshirt'],[N]), E)
put("White t-shirt or tunic, 1 (own, or buy: thrift store)", o('white-tshirt'), E)
put("Brown t-shirt or tunic, 1 (own, or buy: thrift store)", X, E)
put("Brown t-shirt, 1 (own, or buy: thrift store)", X, E)
put("Burgundy or maroon t-shirt, 1 (own, or buy: thrift store)", X, E)
put("Yellow t-shirt, 1 (own, or buy: thrift store)", X, E)
put("Yellow t-shirts, 1 per person (own, or buy: thrift store)", X, E)
put("T-shirts in assigned colors, 1 per kid (own, or buy: thrift store)", X, E)
put("Green t-shirt or tunic, 1 (own, or buy: thrift store)", X, E)
put("Tan t-shirt or tunic, 1 (own, or buy: thrift store)", o('tshirt'), E)
put("Tan t-shirt, 1 (own, or buy: thrift store)", o('tshirt'), E)
put("Tan t-shirts or tunics, 2 (own, or buy: thrift store)", o('tshirt'), E)
put("Dark brown or black t-shirt, 1 (own, or buy: thrift store)", X, E)
put("Snowman: white shirt, white pants, 3 large black felt circles (buy felt: craft store; construction paper works too)", a(['white-tshirt'],[N],['felt','construction-paper']), B)
put("All-white outfit for the Salt: white shirt, pants, and hat (make: from closet)", a(['white-tshirt'],[N],['hat']), E)
put("Tooth: all-white outfit (make: from closet)", X, E)
put("Solid-color t-shirt to wear (own)", o('tshirt'), E)
put("Solid-color tops in assigned colors, 1 per person (own: from closets)", o('tshirt'), E)
put("Matching t-shirts, 2, any color", o('tshirt'), E)
put("Old pillowcase or t-shirt for the cape (make: cut up)", o('pillowcase','tshirt'), E)
put("Black shirt and pants or sweatsuit (own)", o('black-clothes','sweatsuit'), E)
put("Vintage-style suits, 2", X, E)
put("White dress shirts, 2 (own, or buy: thrift store)", X, E)
put("Black t-shirt and black pants (make: use your closet)", o('black-clothes'), E)
put("Black shirt and pants (make: from closet)", o('black-clothes'), E)
put("Black shirt and pants for the bowler (own)", o('black-clothes'), E)
put("Black leggings or pants, 3 (own, or buy: thrift store)", o('black-clothes'), E)
put("Metallic or shiny tops, 3", X, E)
put("Black shirt and black shorts for the referee (make: from closet)", o('black-clothes'), E)
put("Black pants or skirts, 2 (make: from closet)", o('black-clothes'), E)
put("Black pants or shorts (make: from closet)", o('black-clothes'), E)
put("Plain black t-shirt or long-sleeve shirt (make: from closet)", o('black-clothes'), E)
put("Black long-sleeve shirts, 1 per person", o('black-clothes'), E)
put("All-black outfit: t-shirt, pants, and a black beanie (make: from closet)", o('black-clothes'), E)
put("Black or white monochrome clothes (own)", o('black-clothes'), L)
put("Gloom: black clothes from your closet (make: use what you own)", o('black-clothes'), E)
put("Navy or black shirt and pants for the Moon (make: from closet)", o(N,'black-clothes'), E)
put("Bad witch: black dress or black clothes (make: use your closet)", o(N,'black-clothes'), E)
put("Partner: black jacket and black pants (make: from closet)", o('black-clothes'), E)
put("Black headband or strip of black t-shirt, 1 (make: cut from an old shirt)", o(N,'black-clothes'), E)
put("Black cape or black bedsheet, 1", X, E)
put("All-black outfit for the Pepper: black shirt, pants, and hat (make: from closet)", a(['black-clothes'],['hat']), E)
put("Dark pants (own)", o('black-clothes'), L)
put("Dark pants, 1 (own)", o('black-clothes'), L)
put("Solid-color sweatsuit, any color (own)", o('sweatsuit'), E)
put("Fuzzy one-piece pajamas or sweatsuit, 1", o(N,'sweatsuit'), E)
put("Plain sweatsuit in one solid color, red recommended (make: from closet)", o('sweatsuit'), E)
put("White sweatshirt and sweatpants", o('sweatsuit'), E)
put("Black sweatshirt and sweatpants (own, or buy: clothing store)", o('black-clothes'), E)
put("Black sweatshirt and sweatpants (make: from closet)", o('black-clothes'), E)
put("1 black sweatsuit", o('sweatsuit'), E)
put("Red sweatsuit (make: from closet)", X, E)
put("1 tan or brown sweatsuit", X, E)
put("1 green sweatsuit per person", o('sweatsuit'), E)
put("Matching red sweatsuits, one per person (make: from closet, or buy a set at a discount store)", X, E)
put("Blue or gray sweatsuit to wear underneath (make: from closet)", X, E)
put("Hero: red and blue sweatsuit or red shirt with blue pants (make: from closet)", o('sweatsuit'), E)
put("1 pastel fuzzy sweatsuit", X, E)
put("Green hoodie", X, E)
put("Blue hoodie per alien-role person (own, or buy: clothing store)", X, E)
put("Gray hoodie (own)", X, E)
put("Gray hoodie, 1", X, E)
put("1 black hoodie (make: use your closet)", X, E)
put("Blue-gray hoodie, 1 (own, or buy: thrift store)", X, E)
put("Blue-gray sweatpants, 1 (own, or buy: thrift store)", X, E)
put("Kids: green hoodie per child", X, E)
put("Green hoodie or green t-shirt for the raptor (make: from closet)", X, E)
put("Hoodies in red, black, and pink, one per person (make: from closet)", X, E)
put("Streetwear outfit: black hoodie, black pants, chunky sneakers (make: from closet)", X, E)
put("Old white sheet or white fabric (make: use an old sheet)", o('bedsheet'), E)
put("White bedsheet or white fabric, 1 twin-size", o('bedsheet'), E)
put("2 old twin sheets or large fabric rectangles (make: cut from old sheets)", o('bedsheet'), E)
put("The Bride: white dress or old white sheet (make: use what you own)", o(N,'bedsheet'), E)
put("Small drawstring bag or pillowcase (own)", o(N,'pillowcase'), E)
put("1 old white or colored sock per person (make: use one you own)", o('socks'), E)
put("Pillow stuffing or 2 old socks (make: stuff from home)", o('stuffing','socks'), E)
put("4 pairs of black socks (make: from the sock drawer)", o('socks'), E)
put("White socks, 1 pair (own)", o('socks'), E)
put("Red web gloves or red socks for hands (make: from closet)", o('socks'), E)
put("White socks and sneakers (make: from closet)", X, E)
put("Athletic shorts and sneakers (own)", X, E)
put("1 headband", o('headband'), E)
put("2 headbands", o('headband'), E)
put("Plain headband", o('headband'), E)
put("Headbands, 1 per kid", o('headband'), E)
put("Headband per person", o('headband'), E)
put("Headband per alien-role person", o('headband'), E)
put("Headbands, 1 per person", o('headband'), E)
put("Headband, 1 (make: from the drawer)", o('headband'), E)
put("1 plain headband per person", o('headband'), E)
put("1 plastic headband per person", o('headband'), E)
put("Red headband", o('red-headband'), E)
put("Black headband", o('headband'), E)
put("Silver headband", o('headband'), E)
put("Pink headband, one per person", o('headband'), E)
put("Headband or scarf in a matching color, 1 per person (make: from the drawer)", o('headband'), E)
put("Dog ears headband or a brown dog costume piece", X, E)
put("Khaki shirt and hat for the ranger (make: from closet, or buy at a thrift store)", a([N],['hat']), E)
put("Safari hat", X, E)
put("Gray beanie (own, or buy: dollar store)", o('hat'), E)
put("Wide-brim black hat", o('hat'), E)
put("Pointy witch hat", X, E)
put("1 black cone hat", X, E)
put("Red cap and green cap, 1 each", X, E)
put("Black half mask or sunglasses", o(N,'sunglasses'), E)
put("Sunglasses or swim goggles, one per person", o('sunglasses'), E)
put("Tourist accessories: sunglasses, camera or phone on a strap (make: from around the house)", a(['sunglasses'],[N]), E)

# -- more clothes (color-specific garments stay unmapped: the checkbox must be
#    same-or-narrower than the requirement, read plainly)
put("Dark red or brown shirt for the bacon (own)", X, E)
put("1 yellow t-shirt per person", X, E)
put("Blue or orange t-shirt per person (own, or buy: clothing store)", X, E)
put("Team-color t-shirt and skirt or shorts (own)", X, E)
put("Brown t-shirt", X, E)
put("Purple t-shirt", X, E)
put("Green t-shirts, 1 per person, 3 to 5 people", X, E)
put("Red t-shirt and green t-shirt, 1 each", X, E)
put("Ketchup: 1 red tunic or oversized red t-shirt", X, E)
# 2026-09-27 red-team: web-slinger-kid (bank 138). Red is required, so the
# color-garment rule applies: stays X (honestly still need), like the red
# shirts above. Unblocks regen for the 138-idea bank.
put("Red sweatsuit or red shirt and pants, 1 set (own, or buy: clothing store)", X, E)
put("Mustard: 1 yellow tunic or oversized yellow t-shirt", X, E)
put("Pink t-shirts or pajamas, one per person", X, E)
put("Gray t-shirt or sweatshirt", X, E)
put("Tan vest or tan t-shirt (make: from closet)", o('tshirt'), E)
put("Orange, purple, blue, and red t-shirts, 1 each", X, E)
put("Yellow t-shirt and yellow pants", X, E)
put("Yellow shirt and pants for the Sun (make: from closet)", X, E)
put("Green tunic or oversized green t-shirt, 1", X, E)
put("1 t-shirt per person in the cape color", X, E)
put("Matching jerseys or same-color t-shirts, one per player (make: from closet, or buy a multi-pack at a sports store)", X, E)
put("T-shirt or dress in a sea color (teal, purple, red, white), 1 per person", X, E)
put("Rainbow-striped shirt or a white shirt plus rainbow fabric markers", X, E)
put("White shirt and pants per pin person (own)", X, E)
put("Crab: red shirt and pants plus red mittens or red socks for hands (make: from closet)", X, E)
put("Black dress (own)", X, E)
put("Black dress, 1 (own, or buy: thrift store)", X, E)
put("Good witch: pink dress or pink clothes (make: use your closet)", X, E)
put("Each person: a dress from their closet (make: use what you own)", X, E)
put("1 long green dress or green fabric, 3 yards", X, E)
put("Princess: yellow dress or fabric, 2 yards", X, E)
put("Snow princess: pink or lavender dress (make: from closet)", X, E)
put("Ice queen: icy-blue dress or blue dress plus silver glitter glue (buy glitter glue: craft store)", X, E)
put("Thrifted gown or long dress, 1", X, E)
put("Tooth fairy: white dress or white shirt with a white skirt (make: from closet)", X, E)
put("Wrinkled button-down shirt (make: from closet, slept on or stuffed in a bag)", X, E)
put("White button-down shirts, 2 (make: from closet)", X, E)
put("Old button-down shirt you can cut up (make: from closet)", X, E)
put("Khaki vest with pockets", X, E)
put("Khaki pants or shorts (make: from closet)", X, E)
put("Grown-ups: khaki shirt and pants from your closet (make: use what you own)", X, E)
put("The Doctor: old dark suit or jacket from your closet (make: use what you own)", X, E)
put("Long black coat or black robe, 1", X, E)
put("Black leather-look jacket or vest", X, E)
put("Prince: blue jacket and dark pants (make: use your closet)", X, E)
put("Red jacket, 1", X, E)
put("Pink bathrobe or kimono-style robe (own, or buy: clothing store)", X, E)
put("Bathrobe (own)", X, E)
put("Blue overalls, 2", X, E)
put("1 pair denim overalls per person", X, E)
put("1 pair swim or safety goggles per person", X, E)
put("Swim goggles, 1 per person", X, E)
put("1 pair black gloves per person", X, E)
put("Black gloves, 1 pair per person", X, E)
put("White glove, 1", X, E)
put("Bananas, 1 bunch", X, E)
put("Black belt or sash, 1 (make: an old tie or scarf)", X, E)
put("Old tie (make: from closet)", X, E)
put("1 cape per person in squad colors", X, E)
put("1 mask per person, matching the cape color", X, E)
put("Cape or long piece of fabric, 1", X, E)
put("Black cape or black bedsheet (buy cape: costume aisle; or make: from a black sheet from home)", X, E)
put("Each person: 1 black cape or black sheet", X, E)
put("2 white aprons", X, E)
put("2 white sweatbands or strips of white fabric", X, E)
put("Black-and-white striped tights", X, E)
put("1 pair black gloves per person", X, E)
put("Solid-color shirt and pants per person (own)", X, E)
put("Neutral shirt and pants in gray, brown, or tan (make: from closet)", X, E)
put("Earth-tone shirt and pants (make: use your closet)", X, E)
put("Neutral beige or tan clothes (make: from closet)", X, E)
put("Solid-color clothes in animal colors from each person's closet (make: from closet)", X, E)
put("Bloom: colorful clothes from your closet (make: use what you own)", X, E)
put("Each person's own closet clothes (make: use what you own)", X, E)
put("Old clothes with holes or tears (make: use what you own)", X, E)
put("Each person: old-fashioned dark clothes, e.g. a vest, long skirt, or button-up (make: use your closet)", X, E)
put("Basketball jersey or numbered tank top (own, or buy: sporting goods store)", X, E)
put("Basketball shorts (own)", X, E)
put("1 khaki or tan jumpsuit or matching shirt and pants per person", X, E)
put("1 green poncho or green bedsheet per person", X, E)
put("Seaweed: green clothes and long green streamers", X, E)
put("Waves: blue sheet or blue blanket to drape (make: from home)", X, E)
put("Reindeer: brown clothes, 2 brown pipe cleaners, 1 red pom-pom (buy pipe cleaners and pom-pom: craft store)", a([N],['pipe-cleaners'],[N]), E)
put("1 brown fuzzy fabric strip or old brown towel for the mane", X, E)
put("2 hair ties (own)", X, E)
put("Hair ties for braids (make: use what you own)", X, E)
put("Hair ribbon in a team color", o('yarn'), E)
put("Red yarn for hair, 1 skein", o('yarn'), E)
put("Hair ribbon", o('yarn'), E)
put("Hair gel or spray", X, E)
put("Hair gel or pomade (make: from home)", X, E)
put("Hair gel or temporary neon hair spray", X, E)
put("Hair gel, 1 (own)", X, E)
put("Hair spray or powder for a grayed look", X, E)
put("Long dark wig", X, E)
put("Curly red wig", X, E)
put("Black wig or black hair dye, 1", X, E)
put("Big brown afro wig, 1", X, E)
# -- craft drawer
put("1 sheet black craft felt", o('felt','construction-paper'), B)
put("1 sheet gray craft felt", o('felt','construction-paper'), B)
put("2 sheets green craft felt", o('felt','construction-paper'), B)
put("1 sheet green felt per person", o('felt','construction-paper'), B)
put("1 sheet red-brown craft felt", o('felt','construction-paper'), B)
put("1 sheet each white and yellow craft felt", o('felt','construction-paper'), B)
put("1 sheet yellow felt", o('felt','construction-paper'), B)
put("2 red felt sheets or red fabric for the tail", o('felt','construction-paper'), B)
put("Blue craft felt, 1 sheet per alien", o('felt','construction-paper'), B)
# 2026-09-27 red-team: web-slinger-kid (bank 138). Same craft-felt convention.
put("Blue craft felt for sleeve and boot accents, 1 sheet 9x12 inches", o('felt','construction-paper'), B)
put("Blue, orange, and white craft felt", o('felt','construction-paper'), B)
put("Craft felt for masks and emblems", o('felt','construction-paper'), B)
put("Felt sheets in brown, black, pink, and tan, 1 pack", o('felt','construction-paper'), B)
put("Felt ears: two big circles of felt", o('felt','construction-paper'), B)
put("Black and white felt for eyes and smile", o('felt','construction-paper'), B)
put("White felt for the smile", o('felt','construction-paper'), B)
put("Gray felt, 1 sheet", o('felt','construction-paper'), B)
put("White felt, 1 small sheet", o('felt','construction-paper'), B)
put("White felt, 1 sheet per person", o('felt','construction-paper'), B)
put("Orange felt, 1 sheet per person", o('felt','construction-paper'), B)
put("Black felt, 1 sheet", o('felt','construction-paper'), B)
put("White craft felt, 1 sheet 9x12 inches", o('felt','construction-paper'), B)
put("Brown craft felt, 2 sheets 9x12 inches", o('felt','construction-paper'), B)
put("Red craft felt, 1 sheet 9x12 inches", o('felt','construction-paper'), B)
put("Yellow craft felt, 1 sheet 9x12 inches", o('felt','construction-paper'), B)
put("Tan craft felt, 2 sheets 9x12 inches", o('felt','construction-paper'), B)
put("Orange craft felt, 1 sheet 9x12 inches", o('felt','construction-paper'), B)
put("Black craft felt, 1 sheet 9x12 inches", o('felt','construction-paper'), B)
put("Green, red, and yellow craft felt, 1 sheet each 9x12 inches", o('felt','construction-paper'), B)
put("Tan felt for the bun top, 1 sheet", o('felt','construction-paper'), B)
put("Pink craft felt, 2 sheets 9x12 inches", o('felt','construction-paper'), B)
put("Tan fabric or paper to cover the ring (own, or buy: craft store)", o(N,'construction-paper'), B)
put("Burgundy craft felt, 1 sheet 9x12 inches", o('felt','construction-paper'), B)
put("Blue and dark gray craft felt, 1 sheet each 9x12 inches", o('felt','construction-paper'), B)
put("Green craft felt, 1 sheet 9x12 inches", o('felt','construction-paper'), B)
put("Brown felt for the stem, 1 small piece", o('felt','construction-paper'), B)
put("White felt for teeth, 1 small piece", o('felt','construction-paper'), B)
put("Felt for pup badges, 1 sheet per color", o('felt','construction-paper'), B)
put("Brown felt for ears, 1 sheet per kid", o('felt','construction-paper'), B)
put("Brown craft felt, 1 sheet 9x12 inches", o('felt','construction-paper'), B)
put("Paper bowl for the bun, 1 large", X, E)
put("Black felt sheet, 1 pack", o('felt','construction-paper'), B)
put("Red felt, 1 sheet", o('felt','construction-paper'), B)
put("Gold felt sheet, 1 large", o('felt','construction-paper'), B)
put("Yellow felt sheet, 1 sheet", o('felt'), E)
put("Green felt, 1 yard", o('felt'), E)
put("Dark green felt sheet, 1 large", o('felt','construction-paper'), B)
put("Pink or orange felt sheet, 1 large", o('felt'), E)
put("Pink felt or construction paper, 2 triangles per ear", o(N,'construction-paper'), B)
put("Green felt sheet for the tail (make: cut and tape; construction paper works too)", o('felt','construction-paper'), B)
put("Brown, red, green, and yellow felt sheets, 1 pack", o('felt','construction-paper'), B)
put("White felt wings or a wire coat hanger with white pantyhose", o('felt'), E)
put("2 red pipe cleaners", o('pipe-cleaners','construction-paper'), B)
put("2 yellow pipe cleaners", o('pipe-cleaners'), E)
put("Blue pipe cleaners, 2 per alien", o('pipe-cleaners'), E)
put("Brown craft pipe cleaners, 2", o('pipe-cleaners','yarn'), B)
put("Ribbon or string (own, or buy: craft store)", o('yarn'), E)
put("Ribbon or string for cape ties (own, or buy: craft store)", o('yarn'), E)
put("Ribbon or string for straps (own)", o('yarn'), E)
put("Ribbon for straps, about 2 yards", o('yarn'), E)
put("Ribbon or cord for cape ties (own, or buy: craft store)", o('yarn'), E)
put("String or yarn (own)", o('yarn'), E)
put("String for hanging strips, 1 roll (own)", o('yarn'), E)
put("String (own)", o('yarn'), E)
put("Elastic string or yarn, 6 ft", o('yarn'), E)
put("1 short ribbon or string leash (make: use what you own)", o('yarn'), E)
put("Yellow yarn, 1 skein", o('yarn'), E)
put("Pink string or yarn, 1 arm length per snout (make: from craft drawer)", o(N,'yarn'), E)
put("2 backpack straps or 2 long shoelaces (make: from home)", o('yarn'), L)
put("2 backpack straps or 2 long ribbons (make: from home)", o('yarn'), E)
put("3 ft rope or a toy dog leash", X, E)
put("4 feet of thin black rope or black yarn", o('yarn'), E)
put("Aluminum foil, 1 large roll", o('foil'), E)
put("Aluminum foil, 1 roll", o('foil'), E)
put("Aluminum foil, enough to cover the cardboard (make: from the kitchen)", o('foil'), E)
put("1 stick and aluminum foil for the wand (make: from home)", a([N],['foil']), E)
put("White cotton balls or polyester stuffing, 1 bag", o('stuffing'), E)
put("Scrap fabric or cotton balls for stuffing (make: use what you own)", o(N,'stuffing'), E)
put("Soft stuffing or an old pillow, 1 (own)", o(N,'stuffing'), E)
put("White pillow stuffing, 1 bag", o('stuffing'), E)
put("2 black pom-poms", o(N,'stuffing'), B)
put("Blue pom-poms, 2 per alien", o(N,'stuffing'), B)
put("White pom-poms, 4 large, plus 1 green pom-pom", o(N,'stuffing'), B)
put("Yellow or white balloons, 8 to 10", o('balloons'), E)
put("1 pool noodle", X, E)
put("Glow sticks, 1 per person", X, E)
put("Glow bracelets", X, E)
put("1 pack glow bracelets", X, E)
put("Glow stick, 1 blue or white", X, E)
put("1 roll glow-in-the-dark bone tape or white tape", o(N,'tape'), E)
put("2 red LED tea lights per person", X, E)
put("Plastic bottle caps, about 20 total (make: save from drinks)", X, E)
put("Dryer vent hose, 1 flexible aluminum section", X, E)
put("Chopsticks, 1 pair (make: from the kitchen drawer)", X, E)
put("1 pair of toy chopsticks or 2 wooden sticks", X, E)
put("Plastic whistle", X, E)
put("Yellow fabric square, 6 inches (make: cut from an old cloth or napkin)", X, E)
put("Iron (make: household)", X, E)
put("Phone for entrance music (own)", X, E)
put("Basketball (own, or buy: toy store)", X, E)
put("1 soccer ball, any size", X, E)
put("1 tube of tennis balls", X, E)
put("Toy bowling ball or black playground ball", X, E)
put("Toy boxing gloves", X, E)
put("Toy sword prop", X, E)
put("Toy microphones, 3", X, E)
# 2026-09-27 pantry sync: neon-demon-hunter bank material (buy: toy store) --
# a purchased prop, so it honestly maps to "still need" (X), same as Toy sword.
put("Foam sword prop, 1", X, E)
put("Toy firefighter helmet", X, E)
put("Toy fire hose or coiled garden hose", X, E)
put("Toy camera", X, E)
put("Toy binoculars", o(N,'cardboard'), B)
put("Toy crab or cardboard crab (make: cut one from red paper, or buy: toy store)", o(N,'cardboard'), E)
put("Toy teapot or a small real teapot (make: from the kitchen)", X, E)
put("1 toy dinosaur or plush per kid", X, E)
put("Dog plush or toy, 1 (own, or borrow one)", X, E)
put("Scarves or ascots in matching colors (own, or buy: thrift store)", X, E)
put("Pinstripe or black suit, 1", X, E)
put("Black pinstripe or plain suit, 1", X, E)
put("White shirt, 1 (own)", X, E)
put("Black tie or cravat, 1", X, E)
put("Stuffed lion or lion cub toy", X, E)
put("Plastic vampire fangs", X, E)
put("Plastic vampire fangs, 2 sets", X, E)
put("Fake blood, 1 bottle", X, E)
put("Toy trumpet, 1", X, E)
put("Red pocket squares, 2", X, E)
put("Plastic trident prop", X, E)
put("Fake mustache", X, E)
put("Costume glasses", X, E)
put("Tiara", X, E)
put("Toy scepter or wand", X, E)
put("Shell necklace", X, E)
put("Cone lampshade, 1", X, E)
put("1 small envelope and play money or a coin (make: from home)", X, E)
put("Coffee mug (make: from home)", X, E)
put("Old phone case or a cracked-screen phone protector prop (make: use an old case)", X, E)
put("The Doctor: 2 plastic bolts, e.g. costume bolts", X, E)
put("The Bride: white hair spray", X, E)
put("1 toy fishing rod or small garden shovel", X, E)
put("Each person: 1 small jack-o-lantern bucket or foam pumpkin", X, E)
put("Each person: 1 broom or stick horse substitute (make: use a broom from home)", X, E)
put("1 broom from home for a prop (make: use what you own)", X, E)
put("Broomsticks, 3", X, E)
# -- face & makeup (multi-variant consumable: color qualifiers are lenient)
put("Red face paint or lipstick", o('face-paint'), E)
put("Red lipstick or red face paint", o('face-paint'), E)
put("Black non-toxic face paint or eyeliner pencil", o('face-paint'), E)
put("Black eyeliner pencil or non-toxic face paint", o('face-paint'), E)
put("Black non-toxic face paint", o('face-paint'), L)
put("Black face paint, non-toxic", o('face-paint'), L)
put("Black face paint or a black eye mask", o('face-paint'), E)
put("Black face paint for a mask stripe", o('face-paint'), L)
put("White face paint or white stickers", o('face-paint','stickers'), E)
put("White face paint", o('face-paint'), L)
put("White face paint for the beard, non-toxic", o('face-paint'), L)
put("White face powder or pale face paint", o('face-paint'), E)
put("Pale face paint or white face powder", o('face-paint'), E)
put("Very pale foundation or white non-toxic face paint", o('face-paint'), E)
put("Non-toxic face paint", o('face-paint'), E)
put("Red non-toxic face paint", o('face-paint'), L)
put("Green face paint, non-toxic", o('face-paint'), L)
put("Green face paint", o('face-paint'), L)
put("Brown face paint, non-toxic", o('face-paint'), L)
put("Brown face paint for mustaches", o('face-paint'), L)
put("Brown face paint for the dog's nose", o('face-paint'), L)
put("Purple and yellow non-toxic face paint", o('face-paint'), L)
put("Face paint, green and black", o('face-paint'), L)
put("Face paint, brown and black", o('face-paint'), L)
put("Face paint in a matching accent color", o('face-paint'), L)
put("Face paint in purple and black, 1 set", o('face-paint'), L)
put("Pale foundation or white face paint, 1", o('face-paint'), L)
put("Face paint in black and red, 1 set", o('face-paint'), L)
put("Face paint in matching colors, 1 set", o('face-paint'), L)
put("Pale foundation, 1", o('paint-white'), E)
put("Black and white face paint, non-toxic", o('face-paint'), L)
put("Gray and white face paint, non-toxic", o('face-paint'), L)
put("Blue face paint for one rain streak", o('face-paint'), L)
put("Pink blush or face paint for cheeks", o('face-paint'), E)
put("Dark eyeliner and lipstick (own, or buy: dollar store)", o('face-paint'), E)
put("Dark lipstick, 1 (own)", o('paint-red'), E)
put("Dark eye makeup or black eyeshadow", o('face-paint'), E)
put("Dark eye shadow (make: use what you own)", o('face-paint'), E)
put("Black eyeliner and dark green eye shadow", o('face-paint'), E)
put("Black eyeliner, 1 (own, or buy: drugstore)", o('face-paint'), E)
put("Black face paint or eyeliner, 1 (own)", o('face-paint'), E)
put("Orange onesie or footed pajamas, 1 (own, or buy: thrift store)", X, E)
put("Brown fuzzy onesie or footed pajamas, 1", X, E)
put("Striped shirt, 1 (own, or buy: thrift store)", X, E)
put("Black eye patch, 1", X, E)
put("Toy sword or cardboard cutlass, 1", o(N,'cardboard'), B)
put("Brown paper for the treasure map, 1 sheet (own)", o('paper-brown'), E)
put("Gold plastic coins, 1 bag", X, E)
put("Denim shirts, 2 (own, or buy: thrift store)", X, E)
put("Denim shirt, 1 (own, or buy: thrift store)", X, E)
put("Jeans, 2 (own)", X, E)
put("Jeans, 1 (own)", X, E)
put("Jeans with patches, 1 (own, or buy: thrift store)", X, E)
put("Blue overalls or blue jeans, 1 per person (own, or buy: thrift store)", X, E)
put("Jeans or skirts, 1 per person (own)", X, E)
put("Bandanas, 2", X, E)
put("Brown paper bags for chaps, 2 (own)", o('paper-bag'), E)
put("Rope or twine, 1 coil", o('yarn'), E)
put("Straw, raffia, or yellow yarn, 1 bag", o(N,'yarn'), B)
put("Glow-in-the-dark temporary tattoos or neon eyeliner", o(N,'face-paint'), E)
put("The Doctor: green face paint, non-toxic", o('face-paint'), L)
put("Candelabra: gold face paint and a gold headband", a(['face-paint'],[N]), L)

# -- bank expansion: ranks 124-132 (Sept 2026 enrichment; quantified materials)
# Buy-only / specialty materials stay honestly unmapped (X = still need).
# Garments are not lenient on color; color-qualified garments stay X per audit.
put("Pink tulle, 1 yard", X, E)
put("Pink tulle, 2 to 3 yards", X, E)
put("Fake flowers, 1 bunch", X, E)
put("Wooden dowel or stick for the wand, about 12 inches (make: from the yard)", X, E)
put("Elastic for wing straps, about 2 feet", X, E)
put("Wide elastic, 1 inch wide, cut to the waist size plus 1 inch overlap", X, E)
put("Pink leotard or fitted shirt, 1 (own, or buy: clothing store)", X, E)
put("Pink tights, 1 pair (own, or buy: clothing store)", X, E)
put("Hair ties and bobby pins, 1 pack (own)", X, E)
put("Hair ties, 2 (own)", X, E)
put("Bobby pins, 1 pack (own)", X, E)
put("Acrylic paint set, 1", X, E)
put("Washable paint set, 1", X, E)
put("Black sweatsuit, 1 set (own, or buy: clothing store)", o('sweatsuit'), E)
put("Sparkly or sequin jacket, 1", X, E)
put("Toy microphone, 1", X, E)
put("Toy whisk, 1", X, E)
put("Hair teasing comb, 1 (own, or buy: drugstore)", X, E)
put("Dark jeans and a dark top, 1 set (own)", X, E)
put("White dress, 1", X, E)
put("White tights, 1 pair (own, or buy: clothing store)", X, E)
put("Black tights, 1 pair (own, or buy: dollar store)", X, E)
put("Striped tights, 3 pairs", X, E)
put("Hair donut for the bun, 1", X, E)
put("Red shirt, 1 (own)", X, E)
put("Black pants, 1 pair (own)", o('black-clothes'), E)
put("Black pants, 1 (own)", o('black-clothes'), E)
put("Black pom-poms, 2 small", X, E)
put("Yellow craft foam sheets, 2", X, E)
put("Brown craft foam for the flower center, 1 sheet", X, E)
put("Green dress, 1 (own, or buy: thrift store)", X, E)
put("Apron, 1 (own, or buy: dollar store)", X, E)
put("Flour from the kitchen, 1 pinch (optional, for the effect)", X, E)
put("Paintbrush, 1 (own, or buy: craft store)", X, E)
put("Cardboard for wings, 1 large piece about 2x3 feet (make: from a shipping box)", o('cardboard'), E)
put("Cardboard star for the wand tip, 1 (make: from scraps)", o('cardboard'), E)
put("Cardboard for the palette, 1 piece (make: from a shipping box)", o('cardboard'), E)
put("Cardboard for the palette, 1 sheet (make: from a shipping box)", o('cardboard'), E)
put("Cardboard for the soy bottle, 1 sheet (make: from a shipping box)", o('cardboard'), E)
put("Cardboard for the fry carton, 1 sheet (make: from a shipping box)", o('cardboard'), E)
put("Cardboard ring for the donut, 1 large (make: from a shipping box)", o('cardboard'), E)
put("Cardboard for the coffee cup, 1 sheet (make: from a shipping box)", o('cardboard'), E)
put("Cardboard for swords, 1 sheet (make: from a shipping box)", o('cardboard'), E)
put("Cardboard for the hat, 1 sheet (make: from a shipping box)", o('cardboard'), E)
put("Cardboard for two hats, 2 sheets (make: from shipping boxes)", o('cardboard'), E)
put("Cardboard for the pumpkin mask, 1 sheet (make: from a shipping box)", o('cardboard'), E)
put("Cardboard for the hook, 1 sheet (make: from a shipping box)", o('cardboard'), E)
put("Large cardboard for wings, 1 sheet about 3x2 feet (make: from a shipping box)", o('cardboard'), E)
put("Headband, 1", o('headband'), E)
put("Pipe cleaners for antennae, 2", o('pipe-cleaners'), E)
put("Black pipe cleaners for antennae, 2", o('pipe-cleaners'), E)
put("Black felt for dots, 1 sheet 9x12 inches", o('felt','paper-black'), E)
put("Tape, 1 roll", o('tape'), E)
put("Scissors, 1 pair", o('scissors'), E)
put("Scissors, 1", o('scissors'), E)
put("Scissors, 1 (own)", o('scissors'), E)
put("Glue, 1 bottle", o('glue'), E)
put("Glue, 1 tube craft glue", o('glue'), E)
put("Fabric glue, 1 tube", o('glue'), E)
put("Blush, 1 (own, or buy: drugstore)", o('paint-pink'), E)
put("Sunglasses, 1 pair (own, or buy: dollar store)", o('sunglasses'), E)
put("Beret or flat cap, 1", o('hat'), E)
put("Old smock or oversized t-shirt, 1 (own)", o('tshirt'), E)
put("White paper or poster board for the hat, 2 sheets", o('paper-white'), E)
put("1 sheet white paper, blank (make: use what you own)", o('paper-white'), E)
put("White paper for the cup lid, 1 sheet", o('paper-white'), E)

# -- enriched-bank audit (Sept 2026): 526 rephrased material strings --------
# build_pantry_v2 fails loudly on any unmapped string; the Sept 2026 guide
# enrichment rephrased/quantified materials bank-wide, so the new strings are
# audited in pantry_audit_enriched.py (pure data: 282 inherited verbatim from
# audited sources + 244 hand-audited). Applied here so the color-qualification
# pass and the id-validity asserts below cover the new entries too.
_sys_path0 = os.path.dirname(os.path.abspath(__file__))
if _sys_path0 not in __import__('sys').path:
    __import__('sys').path.insert(0, _sys_path0)
from pantry_audit_enriched import NEW_AUDIT as _NEW_AUDIT
for _text, _groups, _tag in _NEW_AUDIT:
    if _text in AUDIT:
        raise SystemExit('AUDIT COLLISION: %r already mapped' % _text)
    AUDIT[_text] = (_groups, _tag)
del _NEW_AUDIT, _text, _groups, _tag, _sys_path0

# ================= COLOR QUALIFICATION PASS =================
# The coarse 'construction-paper' and 'face-paint' slots over-claimed: a user
# with only red+yellow paper would wrongly "own" black felt. Color-specific
# requirements now need the matching color checkbox. Required colors must match.
PAPER_IDS = ['paper-'+c for c in ['red','yellow','green','blue','black','white','orange','pink','brown','gray']]
PAINT_IDS = ['paint-'+c for c in ['red','black','white','green','brown','blue','pink','gold','purple','yellow','gray']]
TAPE_COLOR_IDS = ['tape-'+c for c in ['white','silver','gray','red','yellow','black']]

_COLOR_WORDS = [
    ('red-brown','red'), ('dark green','green'), ('tan','brown'), ('grey','gray'),
    ('red','red'), ('yellow','yellow'), ('green','green'), ('blue','blue'),
    ('black','black'), ('white','white'), ('orange','orange'), ('pink','pink'),
    ('brown','brown'), ('gray','gray'), ('silver','silver'), ('gold','gold'),
    ('purple','purple'),
]
_PAPER_CANON = {'silver':'gray', 'gold':'yellow'}  # closest paper stock
_PAPER_COLORS = ['red','yellow','green','blue','black','white','orange','pink','brown','gray']
_PAINT_COLORS = ['red','black','white','green','brown','blue','pink','gold','purple','yellow','gray']
def _colors_in(text, palette):
    pal = _PAPER_COLORS if palette == 'paper' else _PAINT_COLORS
    low = text.lower(); found = []
    for word, canon in _COLOR_WORDS:
        c = _PAPER_CANON.get(canon, canon) if palette == 'paper' else canon
        if c in pal and c not in [x[1] for x in found] and re.search(r'\b'+re.escape(word)+r'\b', low):
            m = re.search(r'\b'+re.escape(word)+r'\b', low)
            found.append((m.start(), c))
    found.sort()
    return [c for _, c in found]

# Full group replacements for texts the auto-rule would get wrong.
QHINTS = {
    "1 roll glow-in-the-dark bone tape or white tape": (o(N,'tape-white'), L),
    "White stickers or white electrical tape": (o('stickers','tape-white'), B),
    "White stickers or white electrical tape, 1 roll": (o('stickers','tape-white'), B),
    "Snowman: white shirt, white pants, 3 large black felt circles (buy felt: craft store; construction paper works too)":
        (a(['white-tshirt'],[N],['paper-black']), B),
    "Cardboard or craft foam for the beak, 1 sheet": (o('cardboard'), B),
    "Dark eyeliner and lipstick (own, or buy: dollar store)": (a(['paint-black','paint-brown'],['paint-red']), L),
    "Dark eye makeup or black eyeshadow": (o('paint-black'), L),
    "Dark eye shadow (make: use what you own)": (o('paint-black','paint-brown'), L),
    "Black eyeliner and dark green eye shadow": (a(['paint-black'],['paint-green']), L),
    "Pink blush or face paint for cheeks": (o(*PAINT_IDS), L),
    "Glow-in-the-dark temporary tattoos or neon eyeliner": (o(N,*PAINT_IDS), L),
    "Face paint in a matching accent color": (o(*PAINT_IDS), L),
    "Candelabra: gold face paint and a gold headband": (a(['paint-gold'],[N]), L),
    "1 sheet red-brown craft felt": (o('paper-red'), B),
    "Gold felt sheet, 1 large": (o('felt'), E),
    "Glow-in-the-dark temporary tattoos or neon eyeliner": (X, E),
    "Yellow reflective tape, 1 roll": (X, E),
    "Silver star stickers, 1 sheet": (o('paper-gray'), B),
    "Dark green felt sheet, 1 large": (o('paper-green'), B),
    "White poster board, 2 sheets": (o('paper-white'), L),
    "Felt sheets in brown, black, pink, and tan, 1 pack": (a(['paper-brown'],['paper-black'],['paper-pink']), B),
}
TAPE_HINTS = {
    "Silver duct tape": 'tape-silver',
    "Gray duct tape": 'tape-gray',
    "White athletic tape, 1 roll": 'tape-white',
    "Red duct or electrical tape": 'tape-red',
    "Yellow duct or electrical tape": 'tape-yellow',
    "Black electrical tape, 1 roll": 'tape-black',
    "Black electrical tape for web lines, 1 roll": 'tape-black',
    "Reflective tape strips": 'tape-silver',
}

def _qualify_groups(text, groups):
    out = []
    for g in groups:
        if 'construction-paper' in g:
            rest = [i for i in g if i != 'construction-paper']
            cols = _colors_in(text, 'paper')
            if cols:
                for c in cols:
                    out.append(rest + ['paper-'+c])   # AND: each color needed
            else:
                out.append(rest + PAPER_IDS)          # OR: any color works
        elif 'face-paint' in g:
            rest = [i for i in g if i != 'face-paint']
            cols = _colors_in(text, 'paint')
            if cols:
                for c in cols:
                    out.append(rest + ['paint-'+c])
            else:
                out.append(rest + PAINT_IDS)
        elif 'tape' in g and text in TAPE_HINTS:
            out.append([TAPE_HINTS[text] if i == 'tape' else i for i in g])
        else:
            out.append(g)
    return out

for _t in list(AUDIT.keys()):
    if _t in QHINTS:
        AUDIT[_t] = QHINTS[_t]
        continue
    _groups, _tag = AUDIT[_t]
    if any('construction-paper' in (i or '') or 'face-paint' in (i or '') for _g in _groups for i in _g) \
       or _t in TAPE_HINTS:
        AUDIT[_t] = (_qualify_groups(_t, _groups), _tag)

# ================= STORE-RUN TIER (flag-gated, 2026-09-26) =================
# Four-state pantry badge: make-tonight / store-run / needs-things /
# shop-for-this. house taste calls (store-run wording A/B/C, garment-color
# leniency, the hoodie pantry id) are still open, so every piece of this
# section is behind flags that default OFF. With all flags OFF this section
# changes NOTHING: no new pantry ids, no AUDIT edits, no template bytes.
#
# Flags are env vars (never a committed constant) so a stray edit can never
# land them "on":
#   PMC_STORE_RUN_WORDING=OFF|A|B|C  WORDING_SELECTOR for the store-run tier
#                                    copy. OFF (default) = tier fully dormant.
#   PMC_GARMENT_COLOR_LENIENT=1      Tag-L mappings: color-specific garments
#                                    satisfy the generic clothing checkbox.
#   PMC_HOODIE_PANTRY_ID=1           Add the 'hoodie' checkbox to the pantry.
#   PMC_PANTRY_GROUP_AND=1           Stage the index.html ANY->AND alignment
#                                    snippet (AND_ALIGN_JS). OFF (default) =
#                                    snippet dormant (empty string).
STORE_RUN_WORDING = os.environ.get('PMC_STORE_RUN_WORDING', 'OFF').upper()
assert STORE_RUN_WORDING in ('OFF', 'A', 'B', 'C'), \
    'PMC_STORE_RUN_WORDING must be OFF, A, B, or C'
GARMENT_COLOR_LENIENT = os.environ.get('PMC_GARMENT_COLOR_LENIENT', '') == '1'
# The hoodie checkbox was approved 2026-09-26 (decision brief #9).
# Default ON; the env var can still force it off.
HOODIE_PANTRY_ID = os.environ.get('PMC_HOODIE_PANTRY_ID', '1') == '1'
_PANTRY_GROUP_AND_RAW = os.environ.get('PMC_PANTRY_GROUP_AND', '')
assert _PANTRY_GROUP_AND_RAW in ('', '0', '1'), \
    'PMC_PANTRY_GROUP_AND must be 0/empty (off) or 1 (on)'
PANTRY_GROUP_AND = _PANTRY_GROUP_AND_RAW == '1'

# Exact public copy for the store-run tier, per
# hour-session/store-run-copy-2026-09-26.md. Option A is the analysis pick;
# House wording ships verbatim if edited. No em dashes anywhere.
STORE_RUN_COPY = {
    'A': {'badge1': 'One store run',
          'badgeN': 'A store run',
          'detail': 'Your closet is done. What is left needs a store trip.',
          'head': 'One store run away',
          'headSub': 'You own everything else for these. A quick trip finishes the costume.'},
    'B': {'badge1': 'Buy the rest',
          'badgeN': 'Buy the rest',
          'detail': 'Your closet is done. The rest you would buy.',
          'head': 'Buy the rest',
          'headSub': 'Everything in your closet is checked off. These only need store items.'},
    'C': {'badge1': 'Closet complete',
          'badgeN': 'Closet complete',
          'detail': 'Everything you own is checked. What is left needs a store trip.',
          'head': 'Closet complete',
          'headSub': 'You have ticked all you can for these. A store trip finishes the costume.'},
}
# State 4 ("shop-for-this"): ideas whose every material is buy-only. No tick
# can ever move these, so the badge is a pure shopping list, not a summit.
SHOP_FOR_THIS_COPY = {'badge': 'Shop for this',
                      'detail': 'Everything for this one comes from a store.'}

def badge_tier(mats, ticked, wording=STORE_RUN_WORDING):
    """Four-state badge tier for one idea's materials.

    mats: [{'t': text, 'g': [[pantry ids or None]...]}] (generator format).
    ticked: set of pantry ids.
    Returns (state, label). States:
      make-tonight  missing == 0 (unchanged, still literal)
      shop-for-this every material is buy-only (no tick can ever help)
      store-run     missing > 0 but nothing left to tick: every non-null id
                    of every missing material is already ticked, so the only
                    way forward is a store trip
      needs-things  missing > 0 with unticked tickable ids (ticking helps)

    Group semantics are AND across groups (a() means AND), matching
    pantry.html's reqOk (m.g.every(groupOk)) and this module's house-sim.
    NOTE: index.html's pantryMissing / pantryBuyOnlyMissing use an ANY-group
    early-exit walk, so the live quiz badges can disagree with this tier on
    multi-group materials. That divergence predates this tier and is NOT
    changed here (flag-off byte-identity); it is recorded as a finding for
    the main agent. The tier's own walk is self-contained and literal, so
    "Make tonight" can never over-claim.
    label is None for store-run when wording is OFF (tier dormant).
    """
    def _ok(g):
        return any(i in ticked for i in g if i is not None)
    total = len(mats)
    missing = [m for m in mats if not all(_ok(g) for g in m['g'])]
    if not missing:
        return ('make-tonight', 'Make tonight')
    buy_only = [m for m in missing
                if not any(i is not None for g in m['g'] for i in g)]
    if len(buy_only) == total:
        return ('shop-for-this', SHOP_FOR_THIS_COPY['badge'])
    # Nothing left to tick: every tickable id of every missing material is
    # already ticked. The remaining gaps are store-only.
    if all(all(i in ticked for g in m['g'] for i in g if i is not None)
           for m in missing):
        # store items ~= missing materials with an untickable ([None]) group
        n = sum(1 for m in missing
                if any(all(i is None for i in g) for g in m['g']))
        label = None
        if wording != 'OFF':
            c = STORE_RUN_COPY[wording]
            label = c['badge1'] if n <= 1 else c['badgeN']
        return ('store-run', label)
    n = len(missing)
    return ('needs-things', 'Needs %d thing%s' % (n, '' if n == 1 else 's'))

def _tier_js(wording=STORE_RUN_WORDING):
    """Reference port snippet for index.html (NOT spliced into the pantry
    template: the quiz/detail badges live in index.html, which this generator
    does not emit). Self-contained: its own AND-across-groups walk, because
    index.html's pantryMissing / pantryBuyOnlyMissing use an ANY-group
    early-exit that can over-claim "Make tonight" on multi-group materials
    (see badge_tier docstring). Syntax-checked by node --check in the
    store-run tier gate."""
    if wording == 'OFF':
        return ''
    a1, aN = STORE_RUN_COPY['A']['badge1'], STORE_RUN_COPY['A']['badgeN']
    b = STORE_RUN_COPY['B']['badge1']
    c = STORE_RUN_COPY['C']['badge1']
    shop = SHOP_FOR_THIS_COPY['badge']
    return (
"""/* ===== 2026-09-26 store-run tier (PORT SNIPPET - spec lives in
   hour-session/build_pantry_v2.py badge_tier(); WORDING_SELECTOR picked "%s") =====
   Four-state pantry badge. Paste next to pantryMissing/pantryBuyOnlyMissing.
   Self-contained AND-across-groups walk (a material needs ALL its groups),
   matching pantry.html's reqOk - deliberately NOT reusing pantryMissing,
   whose ANY-group early-exit can over-claim on multi-group materials.
   States: make-tonight | store-run | needs-things | shop-for-this.
   make-tonight keeps its literal meaning; nothing redefined. */
var STORE_RUN_WORDING = "%s"; /* A | B | C - house pick */
function storeRunBadgeLabel(n){
  if (STORE_RUN_WORDING === "B") return "%s";
  if (STORE_RUN_WORDING === "C") return "%s";
  return n <= 1 ? "%s" : "%s";
}
/* pantryBadgeState: the four-state tier. Reads the viewer's pantry the same
   way pantryMissing does (pantryTicked), walks PANTRY_MATS with AND
   semantics. Unknown idea -> "unknown" so callers keep today's guards. */
function pantryBadgeState(ideaId){
  var list = (typeof PANTRY_MATS !== "undefined" && PANTRY_MATS.mats[ideaId]) || [];
  if (!list.length) return {state: "unknown", label: ""};
  var ticked = (typeof pantryTicked === "function") ? pantryTicked() : new Set();
  function grpOk(g){ for (var k = 0; k < g.length; k++){ if (g[k] && ticked.has(g[k])) return true; } return false; }
  var missing = [], m, g;
  for (m = 0; m < list.length; m++){
    var okAll = true;
    for (g = 0; g < list[m].length; g++){ if (!grpOk(list[m][g])){ okAll = false; break; } }
    if (!okAll) missing.push(list[m]);
  }
  if (!missing.length) return {state: "make-tonight", label: "Make tonight"};
  function hasId(mat){ for (var gg = 0; gg < mat.length; gg++) for (var kk = 0; kk < mat[gg].length; kk++) if (mat[gg][kk]) return true; return false; }
  var buyOnly = missing.filter(function(mt){ return !hasId(mt); });
  if (buyOnly.length === list.length) return {state: "shop-for-this", label: "%s"};
  var nothingLeftToTick = missing.every(function(mt){
    return mt.every(function(gg){ return gg.every(function(id){ return !id || ticked.has(id); }); });
  });
  if (nothingLeftToTick){
    var n = missing.filter(function(mt){
      return mt.some(function(gg){ return gg.length && gg.every(function(id){ return !id; }); });
    }).length;
    return {state: "store-run", label: storeRunBadgeLabel(n)};
  }
  return {state: "needs-things",
    label: "Needs " + missing.length + " thing" + (missing.length === 1 ? "" : "s")};
}
/* ===== end store-run tier snippet ===== */
""" % (wording, wording, b, c, a1, aN, shop))
TIER_JS = _tier_js()

def _and_align_js(on=PANTRY_GROUP_AND):
    """Port snippet aligning index.html's pantry walks to AND group semantics
    (STAGED, flag-gated; NOT spliced into the pantry template: the quiz/detail
    badges live in index.html, which this generator does not emit).

    Canonical semantics: pantry.html's reqOk (m.g.every(groupOk)), this
    module's badge_tier(), and the audit's literal English ("Marker and ruler,
    1 each" needs BOTH). index.html's pantryMissing / pantryScore /
    pantryBuyOnlyMissing use an ANY-group early-exit that over-claims
    "Make tonight" on multi-group materials. This snippet is the drop-in
    replacement: same function names, signatures, and edge behaviors
    (pantryMissing -1 / pantryBuyOnlyMissing 0 / pantryScore null for unknown
    ideas); only the group walk changes from ANY-early-exit to ALL-groups.

    Flag OFF (default) -> '' so the generator output stays byte-identical.
    Flip: PMC_PANTRY_GROUP_AND=1, take AND_ALIGN_JS, paste over the three
    functions in index.html, run pantry-group-semantics-gate.py, then deploy
    only on the house tap. pantryStoreRunTier() needs no change (it reuses
    pantryMissing)."""
    if not on:
        return ''
    return """/* ===== 2026-09-26 pantry group-semantics alignment (PORT SNIPPET - spec
   lives in hour-session/build_pantry_v2.py _and_align_js(); staged behind
   PMC_PANTRY_GROUP_AND, the call to flip) =====
   Drop-in AND replacements for pantryMissing / pantryScore /
   pantryBuyOnlyMissing. Same names, signatures, and edge behaviors as today;
   only the group walk changed: a material is satisfied when EVERY group has
   a ticked pantry id (AND), matching pantry.html's reqOk. The old
   ANY-early-exit counted a material satisfied when ANY single group had a
   tick, which over-claimed "Make tonight" on multi-group materials
   (e.g. "Marker and ruler, 1 each" counted as owned from the marker alone).
   Paste over the existing three function definitions in index.html. */
function __pmcGrpOk(g, ticked){
  for (var k = 0; k < g.length; k++){ if (g[k] && ticked.has(g[k])) return true; }
  return false;
}
function __pmcMatOk(mat, ticked){
  for (var g = 0; g < mat.length; g++){ if (!__pmcGrpOk(mat[g], ticked)) return false; }
  return true;
}
function pantryMissing(ideaId){
  var list = PANTRY_MATS.mats[ideaId];
  if (!list) return -1;
  var ticked = pantryTicked();
  var n = 0;
  for (var i = 0; i < list.length; i++){ if (!__pmcMatOk(list[i], ticked)) n++; }
  return n;
}
function pantryScore(ideaId, ticked){
  var list = PANTRY_MATS.mats[ideaId];
  if (!list || !list.length) return null;
  var tk = (ticked instanceof Set) ? ticked : pantryTicked();
  var texts = pantryMaterialTexts(ideaId);
  var total = list.length, missing = 0, names = [];
  for (var i = 0; i < list.length; i++){
    var mat = list[i], rep = null;
    for (var g = 0; g < mat.length; g++){
      var grp = mat[g];
      for (var k = 0; k < grp.length; k++){
        var id = grp[k];
        if (!id) continue;
        if (!rep && PANTRY_LABELS[id]) rep = PANTRY_LABELS[id];
      }
    }
    if (!__pmcMatOk(mat, tk)){
      missing++;
      if (names.length < 2){
        var nm = rep || shortMaterialName(texts[i]);
        if (nm) names.push(nm);
      }
    }
  }
  return {have: total - missing, total: total, missing: missing,
    missingNames: (missing >= 1 && missing <= 2 && names.length === missing) ? names : null};
}
function pantryBuyOnlyMissing(ideaId){
  var list = PANTRY_MATS.mats[ideaId];
  if (!list) return 0;
  var ticked = pantryTicked();
  var n = 0;
  for (var i = 0; i < list.length; i++){
    var mat = list[i], hasId = false;
    for (var g = 0; g < mat.length; g++){
      var grp = mat[g];
      for (var k = 0; k < grp.length; k++){ if (grp[k]){ hasId = true; break; } }
      if (hasId) break;
    }
    if (!__pmcMatOk(mat, ticked) && !hasId) n++;
  }
  return n;
}
/* ===== end pantry group-semantics alignment snippet ===== */
"""
AND_ALIGN_JS = _and_align_js()

# new pantry: color-qualified paper / paint / tape
def _P(pid, label, group, staple=False):
    return {'id': pid, 'label': label, 'group': group, 'staple': staple}
_NEW = []
_NEW += [_P('scissors','Scissors','tools',True), _P('tape','Tape (any kind)','tools',True),
         _P('paper-pen','Paper and pen','tools',True)]
_NEW += [_P('tape-white','White tape','tools'), _P('tape-silver','Silver tape','tools'),
         _P('tape-gray','Gray tape','tools'), _P('tape-red','Red tape','tools'),
         _P('tape-yellow','Yellow tape','tools'), _P('tape-black','Black tape','tools')]
_NEW += [_P('glue','Glue (any kind)','tools'), _P('safety-pins','Safety pins','tools'),
         _P('markers','Markers','tools',True), _P('stickers','Stickers','tools'),
         _P('foil','Aluminum foil','tools',True), _P('balloons','Balloons','tools')]
_NEW += [_P('paper-red','Red paper','paper'), _P('paper-yellow','Yellow paper','paper'),
         _P('paper-green','Green paper','paper'), _P('paper-blue','Blue paper','paper'),
         _P('paper-black','Black paper','paper'), _P('paper-white','White paper','paper'),
         _P('paper-orange','Orange paper','paper'), _P('paper-pink','Pink paper','paper'),
         _P('paper-brown','Brown paper','paper'), _P('paper-gray','Gray paper','paper')]
_NEW += [_P('cardboard','Cardboard / boxes','paper',True), _P('paper-bag','Brown paper bags','paper'),
         _P('paper-plates','Paper plates','paper'), _P('newspaper','Newspaper','paper')]
_NEW += [_P('white-tshirt','White t-shirt','clothes',True), _P('tshirt','T-shirt (any color)','clothes',True),
         _P('black-clothes','Black clothes','clothes',True), _P('sweatsuit','Sweatsuit','clothes'),
         _P('bedsheet','Old bedsheet','clothes',True), _P('pillowcase','Pillowcase','clothes',True),
         _P('socks','Socks','clothes',True), _P('stuffing','Stuffing / cotton balls','clothes'),
         _P('headband','Headband (any color)','clothes'), _P('red-headband','Red headband','clothes'),
         _P('sunglasses','Sunglasses','clothes'), _P('yarn','String / yarn / ribbon','clothes'),
         _P('hat','Hat (any kind)','clothes')]
_NEW += [_P('paint-red','Red face paint / lipstick','paint'), _P('paint-black','Black face paint','paint'),
         _P('paint-white','White face paint','paint'), _P('paint-green','Green face paint','paint'),
         _P('paint-brown','Brown face paint','paint'), _P('paint-blue','Blue face paint','paint'),
         _P('paint-pink','Pink face paint / blush','paint'), _P('paint-gold','Gold face paint','paint'),
         _P('paint-purple','Purple face paint','paint'), _P('paint-yellow','Yellow face paint','paint'),
         _P('paint-gray','Gray face paint','paint')]
_NEW += [_P('felt','Felt (multi-color stash)','craft'), _P('pipe-cleaners','Pipe cleaners (multi-color pack)','craft')]
PANTRY = _NEW
GROUPS = [
    {'id':'tools','label':'Tools & tape'},
    {'id':'paper','label':'Paper (which colors?)'},
    {'id':'clothes','label':'Clothes & linens'},
    {'id':'paint','label':'Face paint & makeup (which colors?)'},
    {'id':'craft','label':'Craft drawer'},
]
# ---- flag-gated data changes (all OFF by default; see STORE-RUN TIER above)
# Starter set only: exact AUDIT keys (the enriched audit rephrased the raw
# texts, so raw-text keys would silently miss). Single-kind color-specific
# garments only; multi-kind texts ("black hoodie, black pants, chunky
# sneakers", "t-shirt and skirt or shorts", cross-kind ORs like "t-shirt or
# dress", and multi-count lists like "red t-shirt and green t-shirt, 1 each")
# stay X per the never-partial-mapping rule. Hoodie lines need the 'hoodie'
# checkbox, itself behind HOODIE_PANTRY_ID. Only ever flips X -> id: the
# assert below refuses to clobber an existing real mapping. The full audit
# of remaining color-specific garments is the Phase-2 stream's job after
# House rules on leniency.
_LENIENT_GARMENTS = [
    ("Blue hoodie per alien-role person (own, or buy: clothing store)", 'hoodie'),
    ("Blue hoodie per alien-role person, 1 each (own, or buy: clothing store)", 'hoodie'),
    ("Gray hoodie (own)", 'hoodie'),
    ("Gray hoodie, 1", 'hoodie'),
    ("Gray hoodie, 1 (own)", 'hoodie'),
    ("Green hoodie", 'hoodie'),
    ("Green hoodie, 1", 'hoodie'),
    ("Green hoodie per child, 1 each", 'hoodie'),
    ("Hoodies in red, black, and pink, 1 per person (own: from closet)", 'hoodie'),
    ("Hoodies in red, black, and pink, one per person (make: from closet)", 'hoodie'),
    ("Kids: green hoodie per child", 'hoodie'),
    ("1 pastel fuzzy sweatsuit", 'sweatsuit'),
    ("1 tan or brown sweatsuit", 'sweatsuit'),
    ("Blue or gray sweatsuit to wear underneath (make: from closet)", 'sweatsuit'),
    ("Blue or gray sweatsuit to wear underneath, 1 set (own: from closet)", 'sweatsuit'),
    ("Green sweatsuit per person, 1 each", 'sweatsuit'),
    ("Matching red sweatsuits, one per person (make: from closet, or buy a set at a discount store)", 'sweatsuit'),
    ("Red sweatsuit (make: from closet)", 'sweatsuit'),
    ("Red sweatsuit, 1 (own)", 'sweatsuit'),
    ("Red sweatsuit, 1 (own: from closet)", 'sweatsuit'),
    ("Tan or brown sweatsuit, 1", 'sweatsuit'),
    ("1 t-shirt per person in the cape color", 'tshirt'),
    # 2026-09-30: ("1 yellow t-shirt per person", 'tshirt') removed -- it now
    # maps via the Billy phone-QA block below, so the lenient loop's X-assert
    # would trip on it if the flag were ever flipped.
    ("Blue or orange t-shirt per person (own, or buy: clothing store)", 'tshirt'),
    ("Blue or orange t-shirt per person, 1 each (own, or buy: clothing store)", 'tshirt'),
    ("Brown t-shirt", 'tshirt'),
    ("Brown t-shirt, 1", 'tshirt'),
    ("Purple t-shirt", 'tshirt'),
    ("Purple t-shirt, 1", 'tshirt'),
    ("Red t-shirt, 1 (own)", 'tshirt'),
    ("Red t-shirt, 1 (own, or buy: thrift store)", 'tshirt'),
    ("T-shirt per person in the cape color, 1 each", 'tshirt'),
]
if HOODIE_PANTRY_ID:
    PANTRY.append(_P('hoodie', 'Hoodie (any color)', 'clothes'))
# Hoodie mappings: The hoodie checkbox was approved 2026-09-26 (decision
# brief #9), so these apply whenever the checkbox exists, independent of
# GARMENT_COLOR_LENIENT (STRICT was chosen for the general garment rule,
# decision brief #8, but the hoodie was approved separately). Only flips
# X -> hoodie; the assert refuses to clobber an existing real mapping.
_HOODIE_MAPPINGS = [
    "Blue hoodie per alien-role person (own, or buy: clothing store)",
    "Blue hoodie per alien-role person, 1 each (own, or buy: clothing store)",
    "Gray hoodie (own)",
    "Gray hoodie, 1",
    "Gray hoodie, 1 (own)",
    "Green hoodie",
    "Green hoodie, 1",
    "Green hoodie per child, 1 each",
    "Hoodies in red, black, and pink, 1 per person (own: from closet)",
    "Hoodies in red, black, and pink, one per person (make: from closet)",
    "Kids: green hoodie per child",
]
if HOODIE_PANTRY_ID:
    for _text in _HOODIE_MAPPINGS:
        if _text in AUDIT and AUDIT[_text][0] == X:
            AUDIT[_text] = (o('hoodie'), L)
    del _text
if GARMENT_COLOR_LENIENT:
    for _text, _pid in _LENIENT_GARMENTS:
        assert _text in AUDIT, ('lenient text missing from AUDIT', _text)
        assert AUDIT[_text][0] == X, ('lenient text not buy-only', _text)
        if _pid == 'hoodie' and not HOODIE_PANTRY_ID:
            continue  # the hoodie checkbox is the house call too; skip without it
        AUDIT[_text] = (o(_pid), L)
    del _text, _pid
# ================= BILLY PHONE-QA MAPPINGS (2026-09-30) =================
# House ruling from Billy's 2026-09-30 phone QA: ownable materials sitting in
# all-null groups map to their real stashes; genuinely buy-only items (foam
# sword, glow tattoos, hair gel, toy trumpet, fangs) stay X. This is a
# deliberate, named exception to the never-partial-mapping rule for multi-kind
# (own) texts: the OR-group means ticking ANY listed stash satisfies the
# material, matching the black-cat precedent ("Black shirt and pants or
# sweatsuit (own)" -> o('black-clothes','sweatsuit')). Only ever flips
# X -> ids; the assert refuses to clobber a real mapping.
_BILLY_MAPPINGS = [
    ("Black hoodie, black pants, chunky sneakers, 1 set (own)", o('hoodie', 'black-clothes')),
    ("Neon fabric paint in 2 to 3 colors, 1 tube each", o(*PAINT_IDS)),
    ("1 yellow t-shirt per person", o('tshirt')),
]
for _text, _groups in _BILLY_MAPPINGS:
    assert _text in AUDIT, ('billy mapping text missing from AUDIT', _text)
    assert AUDIT[_text][0] == X, ('billy mapping text not buy-only', _text)
    AUDIT[_text] = (_groups, L)
del _text, _groups
# validate: every referenced id exists
_pids = {p['id'] for p in PANTRY}
for _t, (_groups, _tag) in AUDIT.items():
    for _g in _groups:
        for _i in _g:
            if _i is not None:
                assert _i in _pids, ('dangling pantry id', _i, _t)
assert not any('construction-paper' in (i or '') or 'face-paint' in (i or '')
               for _t, (_g2, _tag2) in AUDIT.items() for _gg in _g2 for i in _gg), 'coarse slot left'
print('pantry items:', len(PANTRY))

# ---------------------------------------------------------------- live bank
def _extract_balanced(html, marker, open_c, close_c):
    """Extract a balanced {...} or [...] JS literal starting after marker."""
    s = html.index(marker)
    i = html.index(open_c, s)
    depth = 0
    j = i
    instr = False
    q = ''
    while j < len(html):
        c = html[j]
        if instr:
            if c == '\\':
                j += 2
                continue
            if c == q:
                instr = False
            j += 1
            continue
        if c == '"' or c == "'":
            instr = True
            q = c
        elif c == open_c:
            depth += 1
        elif c == close_c:
            depth -= 1
            if depth == 0:
                return html[i:j + 1]
        j += 1
    raise SystemExit('LIVE BANK READ FAILED: unbalanced literal after %r' % marker)

def read_live_bank():
    """Read the live bank from index.html.

    Returns [{id, title, materials}] in bank order, with materials from the
    enriched INSTRUCTIONS entries. Fails loudly if IDEAS and INSTRUCTIONS
    disagree or the bank cannot be parsed -- never silently use stale or
    partial data.
    """
    html = open(BANK_HTML).read()
    s = html.index('var IDEAS =')
    e = html.index('var INSTRUCTIONS =')
    ideas_region = html[s:e]
    titles = dict(re.findall(r'\{id:"([^"]+)",\s*title:"((?:[^"\\]|\\.)*)"',
                             ideas_region))
    ins_src = _extract_balanced(html, 'var INSTRUCTIONS =', '{', '}')
    ins_src = re.sub(r',\s*([}\]])', r'\1', ins_src)  # tolerate JS trailing commas
    try:
        ins = json.loads(ins_src)
    except ValueError as ex:
        raise SystemExit('LIVE BANK READ FAILED: INSTRUCTIONS parse: %s' % ex)
    if set(titles) != set(ins):
        raise SystemExit(
            'BANK DIVERGENCE: IDEAS has %d ids, INSTRUCTIONS has %d ids; '
            'only-in-IDEAS=%s only-in-INSTRUCTIONS=%s'
            % (len(titles), len(ins),
               sorted(set(titles) - set(ins))[:10],
               sorted(set(ins) - set(titles))[:10]))
    bank = []
    for iid, entry in ins.items():
        if 'm' not in entry or not entry['m']:
            raise SystemExit('BANK DIVERGENCE: INSTRUCTIONS id %r has no materials' % iid)
        bank.append({'id': iid, 'title': titles[iid], 'materials': entry['m']})
    print('live bank: %d ideas' % len(bank))
    return bank

# ---------------------------------------------------------------- build
def parse_materials(mats):
    out = []
    for mat in mats:
        mm = re.match(r'^(.*?)\s*\((buy:[^)]*)\)\s*$', mat)
        if mm:
            out.append((mm.group(1).strip(), mm.group(2).strip()))
        else:
            out.append((mat.strip(), ''))
    return out

def main():
    bank = read_live_bank()
    ideas = []
    total_mats = 0
    tag_counts = collections.Counter()
    unmapped_texts = []
    for it in bank:
        mats = []
        for raw in it['materials']:
            # 2026-09-26 P5-5: optional materials never gate the badge. They
            # stay in the instructions for users who want them, but
            # PANTRY_MATS drops them so "Make tonight" stays reachable.
            # index.html's inline PANTRY_MATS tests the FULL text (paren
            # intact), so the skip must too -- testing post-split text/note
            # can never match (the paren is stripped by the split). A future
            # regen keeps the two in sync. "optional" may sit anywhere
            # inside the paren, e.g. "(buy: thrift store, optional)".
            # 2026-09-26 pm3 red-team D1: moved the test to the raw string.
            if re.search(r'\([^)]*optional', raw, re.I):
                continue
            text, note = parse_materials([raw])[0]
            total_mats += 1
            if text not in AUDIT:
                raise SystemExit('UNMAPPED MATERIAL: %r (idea %s)' % (text, it['id']))
            groups, tag = AUDIT[text]
            tag_counts[tag] += 1
            if groups == X:
                unmapped_texts.append(text)
            mats.append({'t': text, 'g': groups})
        ideas.append({'id': it['id'], 'title': it['title'], 'mats': mats})
    # ---- divergence guard: the pantry must cover the whole live bank ----
    # Never silently permit missing ideas again.
    bank_ids = [it['id'] for it in bank]
    out_ids = set(it['id'] for it in ideas)
    missing = [i for i in bank_ids if i not in out_ids]
    if missing:
        raise SystemExit('PANTRY/BANK DIVERGENCE: %d bank ideas missing from pantry output: %s'
                         % (len(missing), missing))
    if len(ideas) != len(bank_ids):
        raise SystemExit('PANTRY/BANK COUNT DIVERGENCE: bank=%d pantry=%d'
                         % (len(bank_ids), len(ideas)))
    print('divergence guard: pantry covers all %d live-bank ideas' % len(bank_ids))
    print('ideas:', len(ideas), '| material strings:', total_mats, '| audit entries:', len(AUDIT))
    print('confidence tags:', dict(tag_counts))
    print('unmapped (honest still-need):', len(unmapped_texts))

    # sanity: every pantry id referenced exists; every idea has >=1 requirement
    for it in ideas:
        assert it['mats'], it['id']

    data = {'pantry': PANTRY, 'groups': GROUPS, 'ideas': ideas}
    data_json = json.dumps(data, separators=(',', ':'))
    html_out = TEMPLATE.replace('__DATA__', data_json).replace('__COUNT__', str(len(ideas)))
    # Chopped preservation guard (2026-09-29): the game must survive
    # every regen. Refuse to write output that dropped it.
    for _marker in ('id="chopped"', 'function chopNewRound', 'function chopReveal',
                    'chopped_started', 'chopped_revealed'):
        assert _marker in html_out, ('chopped game missing from generated output', _marker)
    open(OUT, 'w').write(html_out)
    print('wrote', OUT, len(html_out), 'bytes')

    # Exposed for the store-run tier gate: the harness imports this module,
    # calls main(), and cross-checks badge_tier against the emitted DATA.
    global _LAST_BUILD
    _LAST_BUILD = {'ideas': ideas, 'pantry': PANTRY}

    # ---- House simulation ----
    # inventory: white t-shirt, yellow+red construction paper, tape, scissors,
    # lipstick/makeup; staples default ticked (scissors, tape, paper-pen,
    # cardboard, socks, foil).
    # NOT owned: red headband.
    # Enriched bank (Sept 2026): deviled-egg's materials now name felt and pipe
    # cleaners explicitly, so the assumed craft-drawer inventory includes them.
    # The scenario is unchanged: everything covered except the red headband.
    ticked = {'white-tshirt', 'paper-yellow', 'paper-red', 'paint-red', 'scissors', 'tape', 'paper-pen',
              'felt', 'pipe-cleaners'}
    # clearer: group ok if any option ticked
    def group_ok(g): return any(i in ticked for i in g if i is not None)
    # 2026-09-30 focus dead-tap fix (P0): Python mirror of the template's
    # reqOk -- a buy-only group ([None]) counts when its synthetic buy key is
    # ticked. The house sim's ticked set holds no buy keys, so its assertions
    # are unchanged; the mirror keeps future sims honest.
    def pantry_buy_key(idea_id, mi): return 'buy:%s#%s' % (idea_id, mi)
    def req_ok(m, idea_id, mi):
        _key = pantry_buy_key(idea_id, mi)
        return all(group_ok(g) or (all(i is None for i in g) and _key in ticked)
                   for g in m['g'])
    for it in ideas:
        if it['id'] == 'deviled-egg':
            missing = [mm['t'] for mi_, mm in enumerate(it['mats']) if not req_ok(mm, it['id'], mi_)]
            have = len(it['mats']) - len(missing)
            print('HOUSE-SIM deviled-egg: have %d/%d, missing=%s' % (have, len(it['mats']), missing))
            assert missing == ['1 red headband'], missing
            print('HOUSE-SIM PASS: Almost - missing 1: Red headband')
    # tier distribution under test inventory
    tiers = collections.Counter()
    for it in ideas:
        m = sum(1 for xi, x in enumerate(it['mats']) if not req_ok(x, it['id'], xi))
        tiers[0 if m == 0 else (1 if m <= 2 else 2)] += 1
    print('tier distribution (test inventory): make-tonight=%d almost=%d bigger=%d' % (tiers[0], tiers[1], tiers[2]))
    if STORE_RUN_WORDING != 'OFF':
        # Four-state distribution under the same inventory, for the tier gate.
        four = collections.Counter()
        for it in ideas:
            s, _ = badge_tier(it['mats'], ticked)
            four[s] += 1
        print('four-state tiers (test inventory): ' +
              ' '.join('%s=%d' % kv for kv in sorted(four.items())))

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Costumes From Clothes You Already Have | Pick My Costume</title>
<meta name="description" content="Costumes from clothes you already have. Tick what is in your house and we rank all __COUNT__ costume ideas by how little you still need. Updated for Halloween 2026.">
<link rel="canonical" href="https://pickmycostume.com/pantry">
<meta property="og:type" content="website">
<meta property="og:title" content="Costumes From Clothes You Already Have | Pick My Costume">
<meta property="og:description" content="Tick what is already in your house and we will rank all __COUNT__ costume ideas by how little you still need.">
<meta property="og:url" content="https://pickmycostume.com/pantry">
<meta property="og:image" content="https://pickmycostume.com/images/og/classic-ghost.jpg">
<meta property="og:image:secure_url" content="https://pickmycostume.com/images/og/classic-ghost.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://pickmycostume.com/images/og/classic-ghost.jpg">
<style>
  :root{
    --bg:#14101f; --card:#1e1830; --card2:#2a2145; --line:#352a55;
    --ink:#f6f1e7; --muted:#b9a9d9; --accent:#ff8c42; --accent-ink:#2a1500;
    --green:#7ee2a8; --yellow:#ffd166;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    -webkit-font-smoothing:antialiased}
  .wrap{max-width:600px;margin:0 auto;padding:0 16px 64px}
  .topbar{display:flex;align-items:center;justify-content:space-between;padding:14px 0}
  .brand{color:var(--ink);text-decoration:none;font-weight:800;font-size:17px}
  .brand span{color:var(--accent)}
  .proto{font-size:11px;color:var(--muted);border:1px solid var(--line);border-radius:20px;padding:4px 10px}
  h1{font-size:34px;line-height:1.1;margin:18px 0 8px;letter-spacing:-.5px}
  .sub{color:var(--muted);font-size:16px;line-height:1.5;margin:0 0 20px}
  .fresh{color:var(--muted);font-size:13px;margin:-12px 0 20px}
  .staple-fold{background:var(--card2);border:1px solid var(--line);border-radius:12px;
    padding:0 14px;font-size:13.5px;line-height:1.5;color:var(--muted);margin:0 0 6px}
  .staple-fold summary{cursor:pointer;font-weight:700;color:var(--ink);font-size:14px;
    padding:12px 0;min-height:44px;display:flex;align-items:center;list-style:none}
  .staple-fold summary::-webkit-details-marker{display:none}
  .staple-fold p{margin:0 0 12px}
  .staple-fold b{color:var(--ink)}
  /* 2026-09-28: collapsed rows need a visible tap affordance. */
  .staple-fold summary::after,.needs summary::after{content:"+";margin-left:auto;
    color:var(--muted);font-size:18px;font-weight:400;flex:0 0 auto}
  .staple-fold[open]>summary::after,.needs[open]>summary::after{content:"\2013"}
  fieldset{border:0;margin:0 0 8px;padding:0}
  legend{font-size:13px;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);margin:18px 0 8px;padding:0}
  .checks{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
  @media (min-width:480px){.checks{grid-template-columns:repeat(3,minmax(0,1fr))}}
  .check{display:flex;align-items:center;gap:10px;background:var(--card);border:1px solid var(--line);
    border-radius:12px;padding:12px;cursor:pointer;min-height:52px;font-size:14px;line-height:1.25;
    -webkit-tap-highlight-color:transparent;user-select:none;min-width:0}
  /* 2026-09-26 red-team: flex children default min-width:auto, so a tile with
     the nowrap "assumed" tag forced its 1fr column wider than the viewport
     and the right column bled off-screen on phones. Let everything shrink. */
  .check>*{min-width:0}
  /* 2026-09-27 pm red-team: the nowrap tag still clipped ~5px past the tile
     edge at 390px (label min-content + tag exceeded the 1fr column).
     Tighten tile/tag spacing on phones so the pill fits inside the tile. */
  @media (max-width:480px){
    .check{padding:10px;gap:8px}
    .check .tag{padding:2px 5px;white-space:normal}
  }
  .check input{appearance:none;-webkit-appearance:none;flex:0 0 22px;width:22px;height:22px;margin:0;
    border:2px solid var(--muted);border-radius:7px;background:transparent;cursor:pointer;position:relative}
  .check input:checked{background:var(--accent);border-color:var(--accent)}
  .check input:checked::after{content:"";position:absolute;left:6px;top:2px;width:6px;height:11px;
    border:solid var(--accent-ink);border-width:0 3px 3px 0;transform:rotate(42deg)}
  .check.on{border-color:var(--accent);background:var(--card2)}
  /* 2026-09-26 supply ask: a friend asked to borrow these supplies. The
     yellow ring marks them in the list so the recipient can find and tick
     them without hunting. */
  .check.asked{border-color:var(--yellow);box-shadow:0 0 0 1px var(--yellow)}
  .check .tag{font-size:10px;color:var(--muted);border:1px solid var(--line);border-radius:10px;
    padding:2px 7px;margin-left:auto;white-space:nowrap}
  .check .emo{font-size:17px;line-height:1}
  .chip .emo{font-size:13px}
  .actions{display:flex;gap:10px;margin:22px 0 6px}
  .searchrow{margin:14px 0 2px}
  .searchrow input{width:100%;border:1px solid var(--line);border-radius:12px;background:var(--card);
    color:var(--ink);font-size:16px;padding:13px 14px;min-height:52px;-webkit-appearance:none;appearance:none}
  /* 2026-09-26 red-team D12: was 15px, which triggers iOS Safari auto-zoom on focus. 16px+ avoids it. */
  .searchrow input::placeholder{color:var(--muted)}
  .searchrow input:focus{outline:2px solid var(--accent);outline-offset:1px}
  .matchnote{font-size:12.5px;color:var(--muted);margin:6px 2px 0;display:none}
  .copylist{flex:0 0 auto;min-height:0;padding:8px 14px;font-size:13px;font-weight:700}
  .btn{flex:1;border:0;border-radius:12px;padding:14px;font-size:15px;font-weight:700;cursor:pointer;min-height:52px}
  .btn-ghost{background:transparent;color:var(--muted);border:1px solid var(--line)}
  .stat{background:var(--card2);border:1px solid var(--line);border-radius:14px;padding:16px;margin:20px 0 6px}
  .stat b{font-size:26px;color:var(--green)}
  .stat p{margin:6px 0 0;color:var(--muted);font-size:14px;line-height:1.45}
  .unlock{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin:14px 0 6px}
  .unlock h2{font-size:17px;margin:0 0 4px}
  .unlock .lede{font-size:13.5px;color:var(--muted);margin:0 0 10px;line-height:1.45}
  .unlock-row{display:flex;gap:10px;align-items:baseline;padding:9px 0;border-top:1px solid var(--line);font-size:14px;line-height:1.4}
  .unlock-row:first-of-type{border-top:0}
  .unlock-row .n{color:var(--yellow);font-weight:800}
  .unlock-row .w{color:var(--muted);font-size:12.5px;display:block;margin-top:2px}
  .pvvote{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin:18px 0 6px}
  .pvvote h3{font-size:17px;margin:0 0 4px}
  .pvvote p{font-size:13.5px;color:var(--muted);margin:0 0 10px;line-height:1.45}
  /* Chopped game (2026-09-29): the 5-supply pantry game. No animation
     anywhere in this block, so there is nothing to disable for
     prefers-reduced-motion. */
  .chop-note{font-size:13px;color:var(--muted);line-height:1.5;margin:10px 2px 0}
  .chop-basket{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 16px}
  .chop-chip{display:inline-flex;align-items:center;gap:7px;background:var(--card2);
    border:1px solid var(--accent);border-radius:999px;padding:9px 14px;
    font-size:14px;font-weight:600;min-height:44px}
  .chop-opts{display:grid;gap:10px}
  .chop-opt{display:flex;align-items:center;gap:12px;width:100%;text-align:left;
    background:var(--card);border:1px solid var(--line);border-radius:12px;
    padding:14px;cursor:pointer;min-height:60px;color:var(--ink);
    font-size:16px;font-weight:700;font-family:inherit}
  .chop-opt:active{border-color:var(--accent)}
  .chop-emo{font-size:26px;line-height:1;flex:0 0 auto}
  .chop-verdict{font-size:16px;font-weight:700;margin:12px 2px;line-height:1.4}
  .chop-verdict.good{color:var(--green)}
  .chop-verdict.bad{color:var(--yellow)}
  .chop-reveal{display:grid;gap:10px;margin:12px 0}
  .chop-row{display:flex;gap:12px;align-items:flex-start;background:var(--card);
    border:1px solid var(--line);border-radius:12px;padding:12px 14px}
  .chop-row.ok{border-color:var(--green)}
  .chop-row.picked:not(.ok){border-color:var(--yellow)}
  .chop-rtitle{font-size:15px;font-weight:700;line-height:1.35;min-width:0}
  .chop-tag{display:inline-block;font-size:11px;font-weight:700;border-radius:999px;
    padding:2px 9px;margin-left:8px;vertical-align:1px;white-space:nowrap}
  .chop-tag.good{background:var(--green);color:#0c2b1a}
  .chop-tag.bad{background:transparent;border:1px solid var(--muted);color:var(--muted)}
  .chop-miss{display:block;font-weight:400;font-size:13px;color:var(--muted);
    margin-top:4px;line-height:1.45}
  .chop-score{font-size:14px;color:var(--muted);margin:12px 2px 0}
  .pvvote .pvrow{display:flex;gap:8px;flex-wrap:wrap}
  .pvvote textarea{background:var(--bg);color:var(--ink);border:1px solid var(--line);border-radius:10px;padding:10px}
  .pvstatus{font-size:13px;color:var(--muted);min-height:18px}
  .reshead{display:flex;align-items:baseline;justify-content:space-between;margin:24px 0 10px}
  .reshead h2{font-size:20px;margin:0}
  .reshead span{font-size:13px;color:var(--muted)}
  .tier-sub{font-size:13.5px;color:var(--muted);margin:-6px 0 10px;line-height:1.45}
  /* 2026-09-28: visual-first cards -- the costume photo leads as a
     full-bleed banner, text collapses beneath it. Was a 76px floated thumb. */
  .card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:0;margin:0 0 12px;cursor:pointer;overflow:hidden}
  .card.zero{border-color:var(--green)}
  .card.almost{border-color:var(--yellow)}
  .card .tile{position:relative;overflow:hidden;display:grid;place-items:center;aspect-ratio:16/10;
    background:linear-gradient(135deg,#2a2145,#3d2b63)}
  .card .tile .temo{font-size:64px;line-height:1}
  .card .tile .thumb{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;
    border-radius:0;margin:0;background:transparent}
  .card .cbody{padding:14px}
  .card .rank{font-size:12px;color:var(--muted);font-weight:700}
  .card h3{margin:4px 0 6px;font-size:19px}
  .likely{font-size:14px;color:var(--ink);margin:6px 0 2px;}
  .likely b{color:var(--ink);}
  .card .have{font-size:14px;color:var(--muted);margin:0 0 8px}
  .card .have b{color:var(--ink)}
  .chips{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px}
  .chip{font-size:12.5px;background:#171226;border:1px dashed var(--line);color:var(--muted);
    border-radius:20px;padding:5px 10px;overflow-wrap:anywhere}
  .chip-label{font-size:12.5px;color:var(--muted);align-self:center}
  .ready{font-size:14px;color:var(--green);margin:0 0 10px;font-weight:600}
  /* 2026-09-27: recipe-first card rows -- the full build, each
     requirement marked have (green check) vs still-need (open circle). */
  .mrows{margin:0 0 10px}
  .mrow{display:flex;align-items:baseline;gap:8px;font-size:13.5px;padding:3px 0;color:var(--ink);overflow-wrap:anywhere}
  .mrow .mi{flex:0 0 16px;text-align:center;font-weight:800}
  .mrow.have .mi{color:var(--green)}
  .mrow.miss .mi{color:var(--yellow)}
  .mrow.have{color:var(--muted)}
  .mrow .memo{font-size:14px;flex:0 0 auto}
  .go{display:block;text-align:center;background:var(--accent);color:var(--accent-ink);font-weight:800;font-size:15px;
    text-decoration:none;border-radius:10px;padding:12px 16px;min-height:48px;line-height:1.4;margin-top:10px}
  /* 2026-09-28: the full materials checklist collapses behind one
     tap -- the card leads with photo + title + the likely-have line. */
  .needs{margin:8px 0 4px;border:1px solid var(--line);border-radius:10px}
  .needs summary{cursor:pointer;padding:12px;font-size:13.5px;font-weight:700;color:var(--ink);
    list-style:none;min-height:44px;display:flex;align-items:center}
  .needs summary::-webkit-details-marker{display:none}
  .needs .mrows{margin:0;padding:0 12px 10px}
  .challenge{background:#2a1a08;border:1px solid var(--accent);border-radius:14px;
    padding:14px 16px;font-size:14px;line-height:1.5;margin:0 0 16px}
  .challenge b{color:var(--accent)}
  .challenge .csub{color:var(--muted);font-size:13px;margin:6px 0 0}
  .cdismiss{margin-top:8px;min-height:44px;padding:8px 18px;border-radius:10px;border:1px solid var(--accent);background:transparent;color:var(--accent);font-size:14px;cursor:pointer;font-family:inherit}
  .foot{margin-top:28px;color:var(--muted);font-size:13px;line-height:1.6;text-align:center}
  /* 2026-09-27 red-team: footer links were bare inline text (~21px tap rows).
     12px vertical padding makes the classroom-planner link a 44px target. */
  .foot a{display:inline-block;padding:12px 6px;color:var(--accent)}
  .empty{color:var(--muted);font-size:14px;text-align:center;padding:18px 0}
  .jumprow{display:flex;flex-wrap:wrap;gap:10px;align-items:center;font-size:14px;margin:6px 0 0}
  .jumprow a{color:var(--accent);font-weight:700}
  .basics-line{font-size:13px;color:var(--muted);line-height:1.55;margin:0 0 6px}
  .tphotos{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:8px 0 4px}
  .tphoto{display:block;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;text-decoration:none;color:var(--ink)}
  .tphoto img{width:100%;aspect-ratio:4/3;object-fit:cover;display:block;background:var(--card2)}
  .tphoto span{display:block;font-size:12.5px;font-weight:700;padding:8px 10px;line-height:1.3}
  /* 2026-09-26 pantry deep-link: focused checklist card for one costume.
     Sits at the top when arriving via ?for=<idea-id>. Missing rows are
     tappable (44px) and tick the matching supply in the main list. */
  .focus{background:var(--card2);border:1px solid var(--accent);border-radius:14px;
    padding:16px;margin:0 0 16px}
  .focus h2{font-size:19px;margin:0 0 4px;letter-spacing:0}
  .focus .fsub{color:var(--muted);font-size:13.5px;margin:0 0 12px}
  .frow{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:10px;
    font-size:14px;line-height:1.35;margin:0 0 6px;background:var(--card);
    border:1px solid var(--line);-webkit-tap-highlight-color:transparent;user-select:none;
    min-height:44px;box-sizing:border-box}
  .frow .fi{flex:0 0 22px;width:22px;height:22px;border-radius:50%;display:flex;
    align-items:center;justify-content:center;font-size:14px;font-weight:800}
  .frow.have .fi{background:var(--green);color:#0c2b18}
  .frow.have{color:var(--muted)}
  .frow.missing{cursor:pointer;border-color:var(--accent)}
  .frow.missing .fi{border:2px solid var(--accent);color:var(--accent)}
  .frow.missing:active{background:var(--card2)}
  .frow .fbuy{margin-left:auto;flex:0 0 auto;font-size:11px;color:var(--muted);
    border:1px solid var(--line);border-radius:10px;padding:2px 8px;white-space:nowrap}
  .fneed{font-size:14px;margin:12px 0 0;color:var(--ink)}
  .fneed b{color:var(--accent)}
  .fready{font-size:14px;margin:12px 0 0;color:var(--green);font-weight:600}
  .fgo{display:inline-block;margin-top:12px;color:var(--accent);font-size:14px;font-weight:700;text-decoration:none}
  /* 2026-09-28: materials go visual -- big emoji tiles with 1-3 word
     labels instead of long text rows. Used by the focus card, the result-card
     "What you need" details, and the assumed-basics chips. */
  .mtiles{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:0 0 10px}
  .mtile{position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;
    gap:2px;padding:12px 6px 10px;border-radius:12px;background:var(--card);
    border:1px solid var(--line);text-align:center;min-height:96px;box-sizing:border-box;
    -webkit-tap-highlight-color:transparent;user-select:none}
  .mtile .mtemo{font-size:38px;line-height:1.1}
  .mtile .mtlabel{font-size:11px;line-height:1.25;color:var(--ink);overflow-wrap:anywhere}
  .mtile.have{border-color:var(--green)}
  .mtile.have .mtlabel{color:var(--muted)}
  .mtile.miss{border-style:dashed}
  .mtile .mtbadge{position:absolute;top:6px;right:6px;width:20px;height:20px;border-radius:50%;
    display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800}
  .mtile.have .mtbadge{background:var(--green);color:#0c2b18}
  .mtile.miss .mtbadge{border:2px solid var(--accent);color:var(--accent)}
  .mtile.missing{cursor:pointer;border-color:var(--accent);border-style:solid}
  .mtile.missing:active{background:var(--card2)}
  .mchips{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 10px}
  .mchip{display:inline-flex;align-items:center;gap:6px;font-size:13px;padding:6px 10px;
    border-radius:999px;background:var(--card);border:1px solid var(--line);color:var(--ink)}
  .mchip .memo{font-size:16px}
  .staple-note{font-size:13px;color:var(--muted);margin:0 0 4px}
  .vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
</style>
</head>
<body>
<div class="wrap">
  <div class="topbar">
    <a class="brand" href="/">Pick My <span>Costume</span></a>
  </div>

  <h1>What can you make tonight from stuff already in your house?</h1>
  <p class="sub">We assume your home has the basics, so these costumes lead. Tick anything else you own below and the list reshuffles around your stuff.</p>
  <p class="fresh">Updated for Halloween 2026</p>

  <!-- 2026-09-26 pantry deep-link: arriving from a costume detail's
       "Check my pantry" (?for=<idea-id>) renders a focused checklist card
       here at the top: everything that costume needs, marked have vs
       missing. Tapping a missing row ticks it in the main list below. -->
  <div class="focus" id="focus" hidden></div>

  <!-- 2026-09-28: the assumed-basics list collapses behind one tap --
       the page leads with costumes, not a wall of text. -->
  <p class="basics-line">We assume you have: <span id="basicsline"></span> &mdash; untick any you don&rsquo;t actually have in the grid below.</p>
  <!-- 2026-09-25: the opening leads with the alive number, not a dead
       "0 you can make tonight". With just the assumed basics, the count is
       already real the moment the page loads. -->
  <div class="stat" id="stat" role="status" aria-live="polite" style="margin:12px 0"></div>
  <p class="jumprow"><a href="#supply-search">Tick what&apos;s in your house ↓</a>
    <button class="btn btn-ghost" id="sharesheet" type="button">Send this list to your partner</button></p>
  <p class="matchnote" id="sharestatus" role="status"></p>
  <div class="challenge" id="challenge-banner" hidden></div>
  <div class="challenge" id="ask-banner" hidden></div>

  <div class="reshead"><h2>Make tonight</h2><span>you have everything</span></div>
  <p class="tier-sub">Zero extra shopping. Every requirement is something you ticked or we assumed.</p>
  <div id="tier0"></div>

  <div class="reshead"><h2>Almost: 1 or 2 things away</h2><span>one quick grab</span></div>
  <p class="tier-sub">One quick grab and these are yours.</p>
  <div id="tier1"></div>

  <div id="tonight-photos"></div>
  <div class="reshead"><h2>Own more than the basics?</h2><span>fine-tune the list</span></div>
  <p class="tier-sub">Tick anything else already in your house and the costumes above reshuffle around your stuff.</p>
  <div class="searchrow">
    <input type="search" id="supply-search" placeholder="Type a supply, like tape or socks" aria-label="Search supplies" autocomplete="off">
    <p class="matchnote" id="matchnote" role="status"></p>
  </div>

  <p id="tickpulse" class="matchnote" role="status"></p>
  <div id="groups"></div>

  <div class="actions">
    <button class="btn btn-ghost" id="reset" type="button">Start over</button>
  </div>
  <!-- 2026-09-27: the "Challenge a friend" CTA felt out of place on
       this page. Removed. Experiment data backed it: 1 challenge started,
       0 completed in 7 days. The ?kit= rematch arrival still renders its
       own "Send the rematch" button on demand (see applyChallenge). -->
  <div class="unlock" id="unlock" hidden></div>



  <div class="pvvote" id="pvote" hidden></div>

  <div class="pvvote" id="sask" hidden></div>
  <div class="pvvote" id="atell" hidden></div>

  <div class="reshead"><h2>Bigger build</h2><span>3+ things to gather</span></div>
  <p class="tier-sub">Worth it if you love the idea, but plan a real shopping trip.</p>
  <div id="tier2"></div>

  <!-- Chopped (2026-09-29): the pantry's 5-supply game. We deal 5 real
       supplies from actual costume builds; the player picks the ONE costume
       they could honestly build with just the basket plus the household
       basics, then we reveal what each option was really missing. -->
  <div class="reshead"><h2>Chopped</h2><span>the 5-supply game</span></div>
  <div id="chopped"></div>
  <p class="foot">More games: <a href="/play?game=peekaboo">Peekaboo</a> and <a href="/play?game=match">Match the pieces</a></p>

  <p class="foot">Tap a costume to see the full build guide with materials and steps.</p>
  <p class="foot">Free, no signup. Built with Muse. <a href="/classroom">Planning costumes for a classroom? Whole-class planner</a></p>
</div>

<script>
const DATA = __DATA__;
const LS_KEY = 'pantry2';
/* PostHog: anonymous usage stats only. Queued until the library loads. */
const _phq = [];
function track(name, props){
  try {
    if (window.posthog && posthog.capture) posthog.capture(name, props || {});
    else _phq.push([name, props || {}]);
  } catch (e) {}
}
(function(){
  var s = document.createElement('script');
  s.async = true;
  s.src = 'https://us.i.posthog.com/static/array.js';
  s.onload = function(){
    try {
      if (window.posthog && posthog.init) {
        posthog.init('phc_t9dkHXAZR5VEjPFm3K5JDzGKFsNNxKcwSxxcEBEeLbS7', {
          api_host: 'https://us.i.posthog.com', autocapture: false,
          capture_pageview: true, disable_session_recording: true
        });
        _phq.splice(0).forEach(function(e){ try { posthog.capture(e[0], e[1]); } catch (x) {} });
      }
    } catch (e) {}
  };
  try { document.head.appendChild(s); } catch (e) {}
})();
const STAPLES = DATA.pantry.filter(p => p.staple).map(p => p.id);
let ticked;
/* 2026-09-30 Tab 4 A1: the assumed basics read as one line, not a grid. */
try {
  const bl = document.getElementById('basicsline');
  if (bl) bl.textContent = STAPLES.map(id => lc1(supplyLabel(id))).join(', ') + '.';
} catch (e) {}
/* 2026-09-26 challenge rematch: when the page loads from a ?kit= dare link,
   CH holds the challenger's kit so the recipient can answer the dare back. */
let CH = null;
/* 2026-09-26 supply ask: when the page loads from an ?ask= link, ASK holds
   the supplies the sender asked to borrow, so the recipient's tiles can be
   highlighted and the covered state detected. */
let ASK = null;
try {
  ticked = new Set(JSON.parse(localStorage.getItem(LS_KEY) || 'null') || STAPLES);
} catch (e) { ticked = new Set(STAPLES); }
/* 2026-09-26 recipient-harness: a challenge recipient arrived through a
   share (?s=<sid>). Their share id rides along on card deep-links so the
   main site's VIA_SHARE parse can attribute their quiz start back to the
   challenge share. Own pantry taps mint no ?s=, so this never invents
   share arrivals (see arrival-context-gate.js). */
var VIA_S = (function(){ try {
  var m = /[?&]s=([a-z0-9]+)/.exec(location.search || ''); return m ? m[1] : '';
} catch (e){ return ''; } })();
/* 2026-09-26 pantry deep-link: arriving from a costume detail's
   "Check my pantry" carries ?for=<idea-id>. renderFocus() then shows a
   focused checklist card for that costume at the top. Idea ids are public
   catalog data; the param is validated against DATA.ideas, never trusted. */
var FOCUS_ID = (function(){ try {
  var m = /[?&]for=([a-z0-9-]+)/.exec(location.search || ''); return m ? m[1] : '';
} catch (e){ return ''; } })();
let lastUnlocks = [];

function esc(s){
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

const SUPPLY_EMOJI = {
  "scissors": "\u2702\uFE0F",
  "tape": "🩹",
  "paper-pen": "📝",
  "tape-white": "\u2B1C",
  "tape-silver": "\u26AA",
  "tape-gray": "🔘",
  "tape-red": "🟥",
  "tape-yellow": "🟨",
  "tape-black": "\u2B1B",
  "glue": "🧴",
  "safety-pins": "📎",
  "markers": "🖊\uFE0F",
  "stickers": "\u2B50",
  "foil": "\u2728",
  "balloons": "🎈",
  "paper-red": "🟥",
  "paper-yellow": "🟨",
  "paper-green": "🟩",
  "paper-blue": "🟦",
  "paper-black": "\u2B1B",
  "paper-white": "\u2B1C",
  "paper-orange": "🟧",
  "paper-pink": "🩷",
  "paper-brown": "🟫",
  "paper-gray": "🔘",
  "cardboard": "📦",
  "paper-bag": "🛍\uFE0F",
  "paper-plates": "🍽\uFE0F",
  "newspaper": "📰",
  "white-tshirt": "👕",
  "tshirt": "🎽",
  "black-clothes": "👕",
  "sweatsuit": "🧥",
  "bedsheet": "🛏\uFE0F",
  "pillowcase": "💤",
  "socks": "🧦",
  "stuffing": "\u2601\uFE0F",
  "headband": "🎀",
  "red-headband": "🔴",
  "sunglasses": "😎",
  "yarn": "🧶",
  "hat": "🧢",
  "paint-red": "💄",
  "paint-black": "\u26AB",
  "paint-white": "\u26AA",
  "paint-green": "🟢",
  "paint-brown": "🟤",
  "paint-blue": "🔵",
  "paint-pink": "🩷",
  "paint-gold": "🌟",
  "paint-purple": "🟣",
  "paint-yellow": "🟡",
  "paint-gray": "🔘",
  "felt": "🧣",
  "pipe-cleaners": "🖍\uFE0F"
};
function emo(id){
  const e = id && SUPPLY_EMOJI[id];
  return e ? '<span class="emo" aria-hidden="true">' + e + '</span> ' : '';
}
/* 2026-09-28: visual materials -- raw emoji char for the big tiles,
   and a 1-3 word label (bank label) instead of the full requirement sentence. */
function emoChar(id){
  const e = id && SUPPLY_EMOJI[id];
  return e || '';
}
/* 2026-09-28: visual materials -- one primary emoji plus a 1-3 word
   label per requirement. Multi-group requirements show the first group's
   label with a +N. Unmapped (buy-only) requirements fall back to a shortened
   noun phrase from the raw text. */
function matBits(m){
  const groups = (m && m.g) || [];
  const reps = [];
  groups.forEach(g => {
    for (const id of (g || [])){
      if (id && SUPPLY_EMOJI[id]){ if (reps.indexOf(id) === -1) reps.push(id); break; }
    }
  });
  if (reps.length){
    const label = reps.length === 1 ? supplyLabel(reps[0])
      : supplyLabel(reps[0]) + ' +' + (groups.length - 1);
    return { e: SUPPLY_EMOJI[reps[0]], label: label, buy: false, id: reps[0] };
  }
  let s = String((m && m.t) || '');
  s = s.replace(/\s*\(.*?\)\s*$/, '')
       .replace(/^\d+\s+(sheets?|pair|large|medium|small|rolls?|pack|ft\s)?/i, '')
       .replace(/^\d+\s+/, '').replace(/\s+/g, ' ').trim();
  s = s.split(',')[0].trim();
  if (s.length > 26 && /\sor\s/i.test(s)) s = s.split(/\sor\s/i)[0].trim();
  /* 2026-09-30: never an empty label and never the literal "Supply" -- fall
     back to the raw text's comma-head, truncated. */
  if (!s) s = String((m && m.t) || '').split(',')[0].replace(/\s+/g, ' ').trim().slice(0, 26);
  return { e: '🛒', label: s, buy: true, id: null };
}
/* 2026-09-28: emoji audit -- every tile emoji must read as the actual
   material. felt was a rainbow (reads as a rainbow costume, not felt) -> scarf
   (textile); pipe-cleaners was an artist palette -> crayon (colorful stick).
   Audit the rest the same way before adding new supplies. */
/* 2026-09-26 pantry thumbnails: per-idea emoji shown as an instant tile behind
   the lazy photo. Generated by hour-session/gen_idea_emoji.py; re-run it and
   paste the output here if ideas change. Covers all 164 ideas; unknown ids get 🎃. */
const IDEA_EMOJI = {
  "astronaut": "🧑‍🚀",
  "baby-dino": "🐣",
  "baby-pumpkin": "🎃",
  "backyard-hero": "🦸",
  "bacon-eggs": "🍳",
  "ballerina": "🩰",
  "bamboo-demon": "😈",
  "banana": "🍌",
  "basketball-star": "🏀",
  "beekeeper-bee": "🐝",
  "black-cat": "🐈‍⬛",
  "block-game-crew": "🧱",
  "block-monster": "👹",
  "blue-alien-ohana": "👽",
  "blue-dog-family": "🐶",
  "blue-heeler-pup": "🐶",
  "board-game-pieces": "🎲",
  "bowling-pins": "🎳",
  "boxer": "🥊",
  "breakfast-buffet": "🥞",
  "bumble-bee": "🐝",
  "burger-fries": "🍔",
  "burger-joint-couple": "🍔",
  "butterfly": "🦋",
  "caped-duo": "🦸",
  "cardboard-knight": "⚔️",
  "cat-mouse": "🐱",
  "cereal-crew": "🥣",
  "cheerleader": "📣",
  "chill-painter": "🎨",
  "chipmunk-trio": "🐿",
  "chips-guac": "🥑",
  "classic-ghost": "👻",
  "coffee-cup": "☕",
  "cowboy-duo": "🤠",
  "crowd-camouflage": "🔍",
  "cupcake": "🧁",
  "daisy": "🌼",
  "deadpan-diva": "😐",
  "decades-crew": "📻",
  "demon-boy-band": "😈",
  "deviled-egg": "🥚",
  "dino-herd": "🦕",
  "dino-rangers": "🦕",
  "dino-tourist": "🦕",
  "dinosaur-family": "🦕",
  "doctor-bride": "🩺",
  "donut": "🍩",
  "donut-coffee": "🍩",
  "dragon-rider-duo": "🐉",
  "emerald-witch": "🧙‍♀️",
  "emoji-crew": "😎",
  "emotion-crew": "🙂",
  "emotional-support-dinosaur": "🧸",
  "enchanted-castle-crew": "🏰",
  "error-404": "🚫",
  "extinct-party-animal": "🦕",
  "fairy-tale-princesses": "👸",
  "fossil-hunter": "🦴",
  "fruit-salad": "🍓",
  "fuzzy-gremlin": "👹",
  "fuzzy-monster": "🐹",
  "galaxy-knights": "⚔️",
  "garden-fairy": "🧚",
  "garden-gnome": "🧙",
  "ghost-hunters": "🔎",
  "gloom-bloom": "🥀",
  "glow-skeleton": "💀",
  "goggle-crew": "🥽",
  "good-witch-bad-witch": "🧙‍♀️",
  "goth-braids": "🖤",
  "haunted-animatronics": "🤖",
  "haunted-portraits": "🖼️",
  "headless-horsemen": "🎩",
  "hero-squad": "🦸",
  "hot-dog": "🌭",
  "ice-cream-cone": "🍦",
  "ice-skater": "⛸️",
  "juke-joint-vampires": "🎷",
  "kart-racers": "🏎️",
  "ketchup-mustard": "🍅",
  "kpop-demon-huntresses": "🎤",
  "ladybug": "🐞",
  "little-artist": "🎨",
  "little-baker": "👨‍🍳",
  "little-lifeguard": "🏊",
  "little-lion": "🦁",
  "little-pig-family": "🐖",
  "little-prince": "👑",
  "little-shark": "🦈",
  "little-witch": "🧙‍♀️",
  "lost-tourist": "📷",
  "macabre-couple": "💀",
  "mermaid-crew": "🧜‍♀️",
  "milk-cookies": "🍪",
  "moonwalk-star": "🌙",
  "moth-porch-light": "💡",
  "mystery-crew": "🔍",
  "mystery-teens": "🔍",
  "neon-demon-hunter": "🔎",
  "ninja": "🥷",
  "numbered-players": "🏁",
  "office-couple": "💼",
  "party-pinata": "🪅",
  "pbj": "🥜",
  "peas-pod": "🫛",
  "penguin-huddle": "🐧",
  "pickle": "🥒",
  "pirate-captain": "🏴‍☠️",
  "pixel-ghost": "👾",
  "pizza-slice": "🍕",
  "plague-doctor": "🐦",
  "plastic-dream-crew": "💖",
  "player-one-two": "🎮",
  "plug-socket": "🔌",
  "plumber-duo": "🔧",
  "pocket-plush": "🧸",
  "pop-star": "🎤",
  "popcorn-bucket": "🍿",
  "prince-princess": "👑",
  "pumpkin-king-bride": "👑",
  "rain-cloud-rainbow": "🌈",
  "ramen-bowl": "🍜",
  "raptor-barista": "☕",
  "raptor-ranger": "🦖",
  "referee": "🏁",
  "rescue-pups": "🐕‍🦺",
  "robot-crew": "🤖",
  "robot-ranger": "🤖",
  "safari-photographer": "📸",
  "safari-zoo-crew": "🦒",
  "salt-pepper": "🧂",
  "scarecrow": "🌾",
  "smores-duo": "🍫",
  "snow-sisters": "❄️",
  "soccer-squad": "⚽",
  "space-crewmate": "👾",
  "spaghetti-meatball": "🍝",
  "spider": "🕷️",
  "sun-moon": "🌞",
  "superhero-family": "🦸",
  "sushi-roll": "🍣",
  "sushi-soy": "🍱",
  "tall-hat-crew": "🎩",
  "tennis-duo": "🎾",
  "tetris-duo": "🧩",
  "the-olympians": "🏅",
  "tin-hero": "🥫",
  "tiny-firefighter": "🧑‍🚒",
  "tiny-snail": "🐌",
  "tooth-fairy": "🧚",
  "toy-box-crew": "🧸",
  "under-the-sea": "🐠",
  "vampire": "🧛",
  "walking-taco": "🌮",
  "wayfinder-princess": "🌊",
  "web-hero-duo": "🕸️",
  "web-slinger-crew": "🕸️",
  "web-slinger-kid": "🕷️",
  "wine-cheese": "🍷",
  "witchy-sisters": "🧙‍♀️",
  "wizard": "🧙",
  "yellow-henchmen": "💛",
  "zombie-coworker": "🧟",
};
function ideaEmoji(id){ return (id && IDEA_EMOJI[id]) || '🎃'; }

function repId(m){
  for (const g of (m.g || [])) for (const id of (g || [])) if (id && SUPPLY_EMOJI[id]) return id;
  return null;
}
/* 2026-09-30 focus dead-tap fix (P0): nextTickId() scans ALL unsatisfied
   groups for a tickable pantry id. It replaces nextTapId(), which only looked
   at the FIRST unsatisfied group and returned null when that group was
   buy-only -- but a mixed material like [[null],['scissors']] still has
   scissors to tick, and the null left its tile dead (19 such materials in the
   bank). Returns null only when no unsatisfied group has a tickable id, so
   every tap still makes progress. */
function nextTickId(m){
  for (const g of (m.g || [])){
    if ((g || []).some(id => id && ticked.has(id))) continue;
    for (const id of (g || [])) if (id && SUPPLY_EMOJI[id]) return id;
  }
  return null;
}
function groupOk(g){ return g.some(id => id && ticked.has(id)); }
/* 2026-09-30 focus dead-tap fix (P0): buy-only requirements have no pantry
   id, so a ticked buy persists in the pantry2 set under a synthetic key shared
   with the detail page: 'buy:' + ideaId + '#' + material index. */
function pantryBuyKey(ideaId, mi){ return 'buy:' + ideaId + '#' + mi; }
/* 2026-09-30 focus dead-tap fix (P0): a material is satisfied when every
   group is satisfied -- a buy-only group ([null]) counts when its buy key is
   ticked. Callers pass the idea id and material index. */
function reqOk(m, ideaId, mi){ return m.g.every((g) => groupOk(g) || (g.every((id) => !id) && ticked.has(pantryBuyKey(ideaId, mi)))); }
/* 2026-09-30 focus dead-tap fix (P0): true when the material has an
   unsatisfied group with no pantry ids at all -- the tap falls back to
   toggling the buy key instead of ticking a supply. */
function hasBuyGap(m){
  return (m.g || []).some(g => !(g || []).some(id => id && ticked.has(id)) && (g || []).every(id => !id));
}
/* 2026-09-27 cold-user QA: finger-bounce guard for supply ticks. A double-tap
   on a checkbox tile fires two native toggles (tick then untick) -- a silent
   net no-op that eats the user's tick. Same 400ms tapGuard class as the
   quiz/gift/duel flows in index.html: the bounce event is ignored and the DOM
   is re-synced to the kept state instead of toggling. */
var _pantryTapGuards = {};
function pantryTapGuard(key, ms){
  var n = Date.now();
  if (n - (_pantryTapGuards[key] || 0) < ms) return false;
  _pantryTapGuards[key] = n;
  return true;
}

function supplyHit(labelText, q){
  q = (q || '').toLowerCase().trim();
  if (!q) return true;
  var label = labelText.toLowerCase();
  if (label.indexOf(q) !== -1) return true;
  /* Experiment 7 (stream B, 2026-09-26): typo-tolerant pantry search.
     Hypothesis: "scisors" returning nothing is a dead end. Fuzzy match
     with Levenshtein distance <= 2 catches typos.
     Measure: search success rate (non-zero results).
     2026-09-26 red-team D7: a flat <= 2 threshold is far too loose for short
     queries. "tape" (4 chars) matched "paper" (distance 2), so searching
     "tape" returned 32 of 55 supplies including every paper color. Scale the
     threshold by query length: 1 typo for short queries, 2 for longer ones. */
  var maxDist = Math.max(1, Math.floor(q.length / 4));
  var words = label.split(/[^a-z0-9]+/);
  for (var i = 0; i < words.length; i++){
    if (words[i].length < 3) continue;
    if (levenshtein(words[i], q) <= maxDist) return true;
  }
  return false;
}
/* Levenshtein distance for typo tolerance. */
function levenshtein(a, b){
  if (a.length === 0) return b.length;
  if (b.length === 0) return a.length;
  var m = [], i, j;
  for (i = 0; i <= b.length; i++) m[i] = [i];
  for (j = 0; j <= a.length; j++) m[0][j] = j;
  for (i = 1; i <= b.length; i++){
    for (j = 1; j <= a.length; j++){
      m[i][j] = b.charAt(i-1) === a.charAt(j-1)
        ? m[i-1][j-1]
        : Math.min(m[i-1][j-1] + 1, m[i][j-1] + 1, m[i-1][j] + 1);
    }
  }
  return m[b.length][a.length];
}
function applySearch(){
  const input = document.getElementById('supply-search');
  const note = document.getElementById('matchnote');
  if (!input || !note) return;
  const q = input.value;
  let shown = 0, total = 0;
  document.querySelectorAll('#groups fieldset').forEach(fs => {
    let fsShown = 0;
    fs.querySelectorAll('.check').forEach(lb => {
      total++;
      const hit = supplyHit(lb.textContent || '', q);
      lb.style.display = hit ? '' : 'none';
      if (hit) { shown++; fsShown++; }
    });
    fs.style.display = fsShown ? '' : 'none';
  });
  if ((q || '').trim()) {
    note.style.display = 'block';
    note.textContent = shown + ' of ' + total + ' supplies match';
  } else {
    note.style.display = 'none';
    note.textContent = '';
  }
}
function unlockLine(u){
  const n = u.ideas.length;
  return 'Buy ' + u.display.charAt(0).toLowerCase() + u.display.slice(1) +
    ': unlocks ' + n + ' costume' + (n > 1 ? 's' : '') +
    ' (' + u.ideas.slice(0, 6).join(', ') + (n > 6 ? ', +' + (n - 6) + ' more' : '') + ')';
}
function fallbackCopy(text, done){
  const ta = document.createElement('textarea');
  ta.value = text; ta.setAttribute('readonly', '');
  ta.style.position = 'fixed'; ta.style.opacity = '0';
  document.body.appendChild(ta); ta.select();
  try { document.execCommand('copy'); } catch (e) {}
  document.body.removeChild(ta); done();
}
function copyUnlocks(){
  const btn = document.getElementById('copylist');
  const text = 'Costume shopping list (Pick My Costume)\n' +
    lastUnlocks.map(u => '- ' + unlockLine(u)).join('\n');
  const done = function(){
    if (!btn) return;
    const old = btn.textContent; btn.textContent = 'Copied!';
    setTimeout(function(){ btn.textContent = old; }, 2000);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(function(){ done(); }, function(){ fallbackCopy(text, done); });
  } else { fallbackCopy(text, done); }
}

/* Beat-my-pantry challenge: encode ticked supplies in the URL so a friend
   opens the pantry with your kit pre-ticked. Fully client-side. */
/* 2026-09-26 red-team D5: encode stable supply IDs, not positional indices.
   Indices rot silently whenever the pantry order changes (bank rebuilds do
   reorder), so a week-old dare link would pre-tick the wrong supplies.
   IDs are URL-safe ([a-z0-9-], verified) and human-readable in the link.
   kitDecode still accepts the old base36-index format so links shared
   before this change keep working. */
const PANTRY_IDS = new Set(DATA.pantry.map(p => p.id));
function kitEncode(ids){
  return ids.filter(id => PANTRY_IDS.has(id)).join('.');
}
function kitDecode(kit){
  const order = DATA.pantry.map(p => p.id);
  const out = [];
  String(kit || '').split('.').forEach(t => {
    if (PANTRY_IDS.has(t)) { if (out.indexOf(t) === -1) out.push(t); return; }
    /* Legacy base36-index format. The token must be clean alphanumerics so
       a hand-mangled value like '0 1 2' (from a + in the URL) cannot
       partially decode via parseInt's leading-char parsing. */
    if (!/^[0-9a-z]+$/i.test(t)) return;
    const i = parseInt(t, 36);
    if (!isNaN(i) && i >= 0 && i < order.length && out.indexOf(order[i]) === -1) out.push(order[i]);
  });
  return out;
}
function newShareId(){
  let s = '';
  try {
    const a = new Uint8Array(6); crypto.getRandomValues(a);
    s = Array.from(a).map(b => b.toString(36)).join('').replace(/[^a-z0-9]/g, '');
  } catch (e) {}
  while (s.length < 8) s += Math.floor(Math.random() * 36).toString(36);
  return s.slice(0, 8);
}
function topIdeaId(){
  const rows = DATA.ideas.map(score);
  const byMissing = (a, b) => (a.missing.length - b.missing.length) || (a.total - b.total);
  rows.sort(byMissing);
  return rows.length ? rows[0].it.id : null;
}
function ideaTitle(id){
  const it = DATA.ideas.find(x => x.id === id);
  return it ? it.title : null;
}
function challengeLink(){
  const kit = kitEncode([...ticked]);
  const pick = topIdeaId();
  const sid = newShareId();
  return { url: 'https://pickmycostume.com/pantry?kit=' + kit + '&pick=' + pick + '&s=' + sid,
           pick: pick, sid: sid, count: ticked.size };
}
/* 2026-09-26 red-team D4: the old caption always claimed "I can make X
   tonight with stuff already in my house", naming the fewest-missing idea
   even when it still needed supplies (the default staples-only state names
   an idea 2 supplies short). Name a fully-makeable idea when one exists;
   otherwise tell the truth about the gap. No em dashes, house voice. */
function challengeClaim(){
  const rows = DATA.ideas.map(score);
  rows.sort((a, b) => (a.missing.length - b.missing.length) || (a.total - b.total));
  const top = rows[0];
  if (!top) return 'What can you make with what is in your house? ';
  if (top.missing.length === 0)
    return 'I can make ' + top.it.title + ' tonight with stuff already in my house. ' +
      'What can you make with yours? ';
  const n = top.missing.length;
  return 'I am ' + n + ' ' + (n === 1 ? 'supply' : 'supplies') +
    ' away from making ' + top.it.title + ' tonight. What can you make with yours? ';
}
/* 2026-09-26 challenge rematch: the answerer's kit travels in ?kit= and the
   challenger's kit travels in ?opp=, so the original challenger gets a real
   verdict on arrival instead of a second one-way dare. ?vs= chains the share
   ids for attribution. Fully client-side, like the challenge itself. */
function rematchLink(){
  const kit = kitEncode([...ticked]);
  const pick = topIdeaId();
  const sid = newShareId();
  return { url: 'https://pickmycostume.com/pantry?kit=' + kit + '&opp=' + kitEncode(CH.kit) +
           '&pick=' + pick + '&s=' + sid + '&vs=' + (CH.sid || ''),
           pick: pick, sid: sid, count: ticked.size };
}
/* Same honest structure as challengeClaim: name a fully-makeable idea when
   one exists, otherwise tell the truth about the gap. Framed as an answer. */
function rematchClaim(){
  const rows = DATA.ideas.map(score);
  rows.sort((a, b) => (a.missing.length - b.missing.length) || (a.total - b.total));
  const top = rows[0];
  if (!top) return 'I answered your pantry dare. ';
  if (top.missing.length === 0)
    return 'I can make ' + top.it.title + ' tonight with stuff in my house. Beat that. ';
  const n = top.missing.length;
  return 'I am ' + n + ' ' + (n === 1 ? 'supply' : 'supplies') +
    ' away from ' + top.it.title + '. Beat that. ';
}
/* 2026-09-26 pm3 red-team P2: the synchronous fallbackCopy path re-enabled
   the challenge button inside the same task, so a desktop double-click fired
   two pantry_challenge_created events. Timestamp backstop: one challenge per
   2s no matter how the button state settles. */
var lastChallengeAt = 0;
function onChallenge(){
  const btn = document.getElementById('challenge');
  /* 2026-09-26 recipient-harness: double-tap guard. A second tap before the
     share sheet opens must not fire a second native share (or a second
     pantry_challenge_shared track). Re-enabled when the share settles. */
  if (btn && btn.disabled) return;
  if (Date.now() - lastChallengeAt < 2000) return;
  if (btn) btn.disabled = true;
  /* 2026-09-26 rematch: a dare recipient answers instead of starting a new
     dare. The rematch link carries both kits so the original challenger
     gets a verdict. */
  const isRematch = !!CH;
  /* 2026-09-26 pm3 red-team P1: on a rematch arrival the ticked set IS the
     friend's kit. Sending before ticking your own mints kit == opp, a
     degenerate round whose verdict always reads "dead even". Refuse until the
     reader's kit differs from the friend's. */
  if (isRematch && CH.kit && CH.kit.length && ticked.size === CH.kit.length &&
      CH.kit.every(id => ticked.has(id))){
    if (btn){
      btn.disabled = false;
      btn.textContent = 'Tick what you own first, then send it back.';
      setTimeout(function(){ btn.textContent = 'Send the rematch'; }, 2600);
    }
    return;
  }
  /* 2026-09-26 pm3 red-team P2: an empty kit mints a dead link (the
     recipient's applyChallenge returns early with no dare banner). Refuse. */
  if (!isRematch && ticked.size === 0){
    if (btn){
      btn.disabled = false;
      btn.textContent = 'Tick a few supplies first.';
      setTimeout(function(){ btn.textContent = 'Challenge a friend'; }, 2600);
    }
    return;
  }
  lastChallengeAt = Date.now();
  const ch = isRematch ? rematchLink() : challengeLink();
  const text = (isRematch ? rematchClaim() : challengeClaim()) + ch.url;
  const done = function(ok){
    if (btn) {
      btn.disabled = false;
      const old = isRematch ? 'Send the rematch' : 'Challenge a friend';
      btn.textContent = ok
        ? (isRematch ? 'Copied. Send it back to your friend.' : 'Copied. Send it to a friend.')
        : 'Copy failed. Long-press the link.';
      setTimeout(function(){ btn.textContent = old; }, 2600);
    }
  };
  track('pantry_challenge_created', { supply_count: ch.count, top_idea: ch.pick, share_id: ch.sid, is_rematch: isRematch });
  if (isRematch) track('pantry_challenge_answered', { share_id: ch.sid, vs_share_id: CH.sid, supply_count: ch.count, top_idea: ch.pick });
  /* 2026-09-26 red-team: navigator.share can throw synchronously (not just
     reject) on some browsers; without a catch the button stays disabled
     forever. Match the index.html share path: try/catch around the call,
     fallback copy on any failure. */
  var usedNative = false;
  if (navigator.share) {
    try {
      usedNative = true;
      navigator.share({ title: 'Beat my pantry', text: text }).then(
        function(){ track('pantry_challenge_shared', { share_id: ch.sid }); done(true); },
        function(err){
          /* 2026-09-26 red-team: a dismissed share sheet (AbortError) is a
             cancel, not a share: no clipboard copy, no event, button back to
             idle. Only genuine failures fall back to copy. */
          if (err && err.name === 'AbortError'){
            if (btn){ btn.disabled = false; btn.textContent = isRematch ? 'Send the rematch' : 'Challenge a friend'; }
            return;
          }
          fallbackCopy(text, function(){ done(true); });
        });
    } catch (e) { usedNative = false; }
  }
  if (!usedNative) fallbackCopy(text, function(){ done(true); });
}
/* Recipient side: pre-tick the challenger's kit and show the dare banner.
   2026-09-26 rematch: remember the challenger's kit (CH) so the recipient's
   challenge button becomes "Send the rematch"; a ?opp= arrival renders the
   verdict comparing both kits instead of a second one-way dare. */
function applyChallenge(){
  let q = {};
  try {
    q = Object.fromEntries(new URLSearchParams(location.search || '').entries());
  } catch (e) { return; }
  if (!q.kit) return;
  const ids = kitDecode(q.kit);
  if (!ids.length) return;
  CH = { kit: ids, pick: q.pick || null, sid: q.s || q.vs || null };
  /* 2026-09-27 red-team: a link that lost ?s= (chat-app truncation, hand
     edit) left CH.sid null, so the next rematch minted vs= empty and the
     attribution chain died. Falling back to ?vs= keeps the chain rooted. */
  /* The recipient answers the dare, so the button offers the rematch.
     2026-09-27: the challenge CTA was removed from the pantry page,
     so on a ?kit= arrival the rematch button is rendered on demand here. */
  let cbtn = document.getElementById('challenge');
  if (!cbtn) {
    cbtn = document.createElement('button');
    cbtn.id = 'challenge';
    cbtn.type = 'button';
    cbtn.className = 'btn';
    cbtn.style.cssText = 'background:var(--accent);color:var(--accent-ink)';
    const acts = document.querySelector('.actions');
    if (acts) acts.appendChild(cbtn);
  }
  if (cbtn) cbtn.textContent = 'Send the rematch';
  /* 2026-09-26 red-team: keep the challenger's kit in memory only. A cold
     recipient just peeking at the dare must not have their OWN saved pantry
     (pantry2) silently replaced before they touch anything. The recipient's
     first tick/untick persists naturally via the change handler, which the
     banner below already instructs them to do. */
  ticked = new Set(ids);
  const idea = DATA.ideas.find(x => x.id === q.pick);
  const title = idea ? idea.title : null;
  /* 2026-09-26 red-team D4b: the banner used to claim "Your friend can make
     X with what is in their house" even when the challenger's own kit was
     still short of X (the default staples-only kit is 2 supplies short of
     its top pick), contradicting the now-honest share caption. Score the
     pick against the challenger's kit (ticked === their kit here) and tell
     the truth about the gap. */
  const gap = idea ? score(idea).missing.length : 0;
  const oppIds = q.opp ? kitDecode(q.opp) : [];
  const isRematch = oppIds.length > 0 && !!idea;
  const banner = document.getElementById('challenge-banner');
  if (banner) {
    banner.hidden = false;
    let html;
    if (isRematch) {
      /* Verdict: both kits scored against the featured pick. ticked is the
         answerer's kit here (it arrived in ?kit=); the READER's own kit --
         the original challenger, who received this rematch link -- arrives
         in ?opp=. So friendGap = the friend who answered (ticked), youGap =
         you, the reader (?opp=). 2026-09-26 red-team recipient audit: these
         were swapped -- the banner told the challenger the ANSWERER's gap
         was theirs and vice versa, and the closer/further call was inverted. */
      const friendGap = gap;
      const youGap = scoreAgainst(idea, new Set(oppIds)).missing.length;
      const line = (friendGap === 0 && youGap === 0)
        ? 'You can both make <b>' + esc(title) + '</b> tonight. First one finished sends a photo.'
        : 'Rematch: your friend is <b>' + friendGap + ' ' + (friendGap === 1 ? 'supply' : 'supplies') +
          '</b> away from <b>' + esc(title) + '</b>. You are <b>' + youGap + ' ' +
          (youGap === 1 ? 'supply' : 'supplies') + '</b> away. ' +
          (friendGap < youGap ? 'They are closer. Time to catch up.'
            : friendGap > youGap ? 'You are closer. Finish it.'
            : 'Dead even.');
      html = line + ' We ticked the supplies your friend answered with below. Your own saved list is untouched.' +
        /* 2026-09-26 red-team recipient audit: without this instruction the
           challenger taps "Send the rematch" with the FRIEND's kit still
           ticked, minting a degenerate round-3 link (kit == opp) whose
           verdict always reads "dead even". Tell them to tick their own. */
        ' Tick what <b>you</b> own below, then send the rematch back.' +
        /* 2026-09-26 red-team D5: the dare banner had no dismiss. Once the
           recipient starts unticking, the banner has served its purpose but
           kept shouting. A small dismiss is reversible and low-risk. */
        ' <button type="button" id="challenge-dismiss" class="cdismiss">Got it</button>';
      track('pantry_rematch_opened', { supply_count: ids.length, opp_supply_count: oppIds.length,
        pick: q.pick, share_id: q.s || null, vs_share_id: q.vs || null });
    } else {
      html = (title
        ? (gap === 0
            ? 'Your friend can make <b>' + esc(title) + '</b> with what is in their house. '
            : 'Your friend is <b>' + gap + ' ' + (gap === 1 ? 'supply' : 'supplies') +
              '</b> away from making <b>' + esc(title) + '</b>. ')
        : 'Your friend challenged you to a pantry cook-off. ') +
          'We ticked their supplies below. Untick what you do not own and see what <b>you</b> can make.' +
        /* 2026-09-26 red-team D5: the dare banner had no dismiss. Once the
           recipient starts unticking, the banner has served its purpose but
           kept shouting. A small dismiss is reversible and low-risk. */
        ' <button type="button" id="challenge-dismiss" class="cdismiss">Got it</button>';
    }
    banner.innerHTML = html;
    const dis = document.getElementById('challenge-dismiss');
    if (dis) dis.addEventListener('click', function(){ banner.hidden = true; });
  }
  track('pantry_challenge_opened', { supply_count: ids.length, pick: q.pick || null, share_id: q.s || null, is_rematch: isRematch });
}
/* 2026-09-26 supply ask: the dare challenge is competitive ("what can YOU
   make"); the ask is cooperative. When the closest costume is 1-2 supplies
   away, the sender asks the house group chat to borrow exactly the missing
   supplies. The recipient's tiles for the asked supplies get a yellow ring;
   ticking all of them marks the ask covered and offers the tell-back copy.
   Fully client-side, additive only: no challenge/rematch/vote code path
   changes, and the ask box never renders for share recipients (CH set),
   because the pre-ticked kit on arrival is the challenger's, not theirs. */
function askDecode(ask){
  const out = [];
  String(ask || '').split('.').forEach(t => {
    if (PANTRY_IDS.has(t) && out.indexOf(t) === -1) out.push(t);
  });
  return out;
}
function supplyLabel(id){
  const p = DATA.pantry.find(x => x.id === id);
  return p ? p.label : id;
}
function lc1(s){ return s ? s.charAt(0).toLowerCase() + s.slice(1) : s; }
function artFor(s){ return /^[aeiou]/i.test(s || '') ? 'an' : 'a'; }
/* "a red headband" / "a red headband and black face paint". Labels are
   title-cased in the bank; the first letter drops to lowercase for prose. */
/* 2026-09-26 red-team pm4: plural supply labels (Markers, Socks, Paper plates,
   ...) take no article. Every label ending in "s" in the bank is plural,
   so the ends-in-s test is safe here. */
function needList(ids){
  const names = ids.map(id => { const n = lc1(supplyLabel(id)); return /s$/i.test(n) ? n : artFor(n) + ' ' + n; });
  if (names.length <= 1) return names[0] || '';
  if (names.length === 2) return names[0] + ' and ' + names[1];
  return names.slice(0, -1).join(', ') + ', and ' + names[names.length - 1];
}
function askLink(r){
  const kit = kitEncode([...ticked]);
  const sid = newShareId();
  return { url: 'https://pickmycostume.com/pantry?kit=' + kit +
           '&ask=' + r.missingIds.join('.') + '&pick=' + r.it.id + '&s=' + sid,
           sid: sid, pick: r.it.id, gap: r.missing.length };
}
function buildSupplyAskText(r, ch){
  const n = r.missing.length;
  return 'Anyone have ' + needList(r.missingIds) + ' I can borrow? ' +
    'I am ' + n + ' ' + (n === 1 ? 'supply' : 'supplies') + ' away from making ' +
    r.it.title + ' for Halloween. ' +
    'Lend ' + (n === 1 ? 'it' : 'them') + ' to me and I will send you a photo of the finished thing. ' +
    ch.url;
}
function renderSupplyAsk(t1){
  var box = document.getElementById('sask');
  var r = (t1 && t1.length) ? t1[0] : null;
  /* Only the single closest costume, only a 1-2 supply gap (a 3+ gap is a
     shopping list, handled by "Copy shopping list"), and never for share
     recipients: their ticked set is the challenger's kit, so an ask built
     from it would name the challenger's gap as their own. */
  if (!r || r.missing.length < 1 || r.missing.length > 2 || CH){
    box.hidden = true; box.innerHTML = ''; return;
  }
  box.hidden = false;
  var n = r.missing.length;
  box.innerHTML =
    '<h3>Only ' + (n === 1 ? 'one thing' : 'two things') + ' standing between you and ' +
    esc(r.it.title) + '?</h3>' +
    '<p>You need: <b>' + esc(r.missing.map(s => s.replace(/\s*\((own|make|buy)\)$/, '')).join(', ')) + '</b>. Ask the house group chat. ' +
    'Someone might have ' + (n === 1 ? 'it' : 'them') + ' to lend.</p>' +
    '<div class="pvrow"><button class="btn" id="sask-btn" type="button">Ask the group chat</button></div>' +
    '<div id="sask-panel" style="display:none;margin-top:10px"></div>';
  document.getElementById('sask-btn').addEventListener('click', function(){
    var panel = document.getElementById('sask-panel');
    var btn = this;
    if (panel.style.display !== 'none'){
      panel.style.display = 'none'; btn.textContent = 'Ask the group chat'; return;
    }
    /* Minted fresh on each open: the text embeds the live kit, so a stale
       panel between ticks would name the wrong supplies. */
    var ch = askLink(r);
    var text = buildSupplyAskText(r, ch);
    track('supply_ask_composed', { share_id: ch.sid, idea_id: ch.pick, gap_count: ch.gap });
    panel.innerHTML = '';
    var ta = document.createElement('textarea');
    ta.readOnly = true; ta.rows = 6;
    ta.style.cssText = 'width:100%;box-sizing:border-box;font-size:14px';
    ta.value = text;
    var row = document.createElement('div'); row.className = 'pvrow'; row.style.marginTop = '8px';
    var bCopy = document.createElement('button');
    bCopy.type = 'button'; bCopy.className = 'btn btn-ghost'; bCopy.textContent = 'Copy ask text';
    var bShare = document.createElement('button');
    bShare.type = 'button'; bShare.className = 'btn btn-ghost'; bShare.textContent = 'Share';
    var st = document.createElement('div'); st.className = 'pvstatus'; st.style.marginTop = '6px';
    bCopy.onclick = function(){
      var doneCopy = function(){
        bCopy.textContent = 'Copied';
        setTimeout(function(){ bCopy.textContent = 'Copy ask text'; }, 2000);
        track('supply_ask_copied', { share_id: ch.sid, idea_id: ch.pick, gap_count: ch.gap, via: 'clipboard' });
        st.textContent = 'Copied. Paste it in the group chat.';
      };
      if (navigator.clipboard && navigator.clipboard.writeText){
        navigator.clipboard.writeText(text).then(doneCopy, function(){ fallbackCopy(text, doneCopy); });
      } else { fallbackCopy(text, doneCopy); }
    };
    bShare.onclick = function(){
      if (bShare.disabled) return; /* double-tap guard: one share per tap */
      bShare.disabled = true;
      var rearm = function(){ bShare.disabled = false; };
      var viaCopy = function(){
        fallbackCopy(text, function(){
          track('supply_ask_shared', { share_id: ch.sid, idea_id: ch.pick, gap_count: ch.gap, via: 'clipboard' });
          st.textContent = 'Copied. Paste it in the group chat.';
          rearm();
        });
      };
      /* Red-team pattern from the challenge share: navigator.share can
         throw synchronously on some browsers, so try/catch the call. */
      if (navigator.share){
        try {
          navigator.share({ title: 'Can I borrow this?', text: text }).then(
            function(){
              track('supply_ask_shared', { share_id: ch.sid, idea_id: ch.pick, gap_count: ch.gap, via: 'share_sheet' });
              st.textContent = 'Sent. Fingers crossed someone has it.';
              rearm();
            },
            function(){ viaCopy(); });
        } catch (e) { viaCopy(); }
      } else { viaCopy(); }
    };
    panel.appendChild(ta);
    row.appendChild(bCopy); row.appendChild(bShare);
    panel.appendChild(row); panel.appendChild(st);
    panel.style.display = 'block';
    btn.textContent = 'Hide the ask text';
  });
}
/* Recipient side: the asked supplies get the yellow ring in renderGroups;
   this banner names the ask and tells the recipient what to do. Runs right
   after applyChallenge so CH (and the pre-ticked kit) already exists. */
function applySupplyAsk(){
  let q = {};
  try {
    q = Object.fromEntries(new URLSearchParams(location.search || '').entries());
  } catch (e) { return; }
  const ids = askDecode(q.ask);
  if (!ids.length) return;
  ASK = { ids: ids, pick: q.pick || null, sid: q.s || null, covered: false };
  const idea = DATA.ideas.find(x => x.id === q.pick);
  const title = idea ? idea.title : null;
  const banner = document.getElementById('ask-banner');
  if (banner){
    banner.hidden = false;
    const n = ids.length;
    const need = ids.map(id => '<b>' + esc(supplyLabel(id)) + '</b>')
      .join(n === 2 ? ' and ' : ', ');
    banner.innerHTML =
      (title
        ? 'Your friend is <b>' + n + ' ' + (n === 1 ? 'supply' : 'supplies') +
          '</b> away from making <b>' + esc(title) + '</b>: they need ' + need + '. '
        : 'Your friend needs ' + need + ' for a Halloween costume. ') +
      'If you have ' + (n === 1 ? 'it' : 'them') + ' to lend, tick ' +
      (n === 1 ? 'it' : 'them') + ' below and tell them it is covered.' +
      ' <button type="button" id="ask-dismiss" class="cdismiss">Got it</button>';
    const dis = document.getElementById('ask-dismiss');
    if (dis) dis.addEventListener('click', function(){ banner.hidden = true; });
  }
  track('supply_ask_opened', { supply_count: (CH && CH.kit) ? CH.kit.length : 0,
    pick: q.pick || null, share_id: q.s || null, gap_count: ids.length });
}
/* Called at the end of every render(): when every asked supply is ticked,
   the ask is covered. Shows once per page load, then the flag holds so the
   box cannot nag back after an untick. */
function checkAskCovered(){
  var box = document.getElementById('atell');
  if (!ASK){ box.hidden = true; box.innerHTML = ''; return; }
  const stillMissing = ASK.ids.filter(id => !ticked.has(id));
  /* 2026-09-26 pm3 red-team P2: unticking a covered supply must hide the
     success box again. The old early-return on ASK.covered left "That covers
     it" stale. Coverage is recomputed on every change; the celebration (and
     its analytics) still fires only on the false->true transition. */
  if (stillMissing.length) { ASK.covered = false; box.hidden = true; box.innerHTML = ''; return; }
  if (ASK.covered) return;
  ASK.covered = true;
  track('supply_ask_covered', { share_id: ASK.sid, pick: ASK.pick, gap_count: ASK.ids.length });
  const idea = DATA.ideas.find(x => x.id === ASK.pick);
  const title = idea ? idea.title : 'their costume';
  const n = ASK.ids.length;
  const tellText = 'Covered! I have ' + needList(ASK.ids) + ' for ' + title +
    '. Come grab ' + (n === 1 ? 'it' : 'them') + ' anytime.';
  box.hidden = false;
  box.innerHTML =
    '<h3>That covers it.</h3>' +
    '<p>You have everything your friend needs for <b>' + esc(title) + '</b>. Send them the good news.</p>' +
    '<div class="pvrow"><button class="btn" id="atell-btn" type="button">Copy the good news</button></div>' +
    '<div class="pvstatus" id="atell-status" style="margin-top:6px"></div>';
  document.getElementById('atell-btn').addEventListener('click', function(){
    const btn = this, st = document.getElementById('atell-status');
    const doneTell = function(){
      btn.textContent = 'Copied';
      setTimeout(function(){ btn.textContent = 'Copy the good news'; }, 2000);
      track('supply_ask_tellback_sent', { share_id: ASK.sid, pick: ASK.pick, via: 'clipboard' });
      if (st) st.textContent = 'Copied. Paste it back in the chat.';
    };
    if (navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(tellText).then(doneTell, function(){ fallbackCopy(tellText, doneTell); });
    } else { fallbackCopy(tellText, doneTell); }
  });
}
/* 2026-09-26 pantry house vote: the pantry ranks by makeability, and the
   top of that list is exactly where household indecision lives ("we could
   make three of these tonight - which one?"). The vote box turns that
   indecision into a share: the top 3 make-tonight/almost candidates,
   numbered 1-2-3 with honest gap stakes and their own ?s=&o=pantryvote
   links. The vote itself happens in the chat via replies - no backend,
   no tally UI, nothing to maintain.
   Measure: pantry_vote_opened -> pantry_vote_copied / pantry_vote_shared,
   all with share_origin "pantryvote"; recipient opens attribute through
   the existing ?s=&o= allowlist in index.html. */
function daysToHalloween(){
  var now = new Date();
  var h = new Date(now.getFullYear(), 9, 31, 23, 59, 59);
  if (h.getTime() < now.getTime()) h = new Date(now.getFullYear() + 1, 9, 31, 23, 59, 59);
  return Math.max(0, Math.round((h.getTime() - now.getTime()) / 86400000));
}
function pvGapLine(r){
  if (r.missing.length === 0) return 'nothing to buy';
  var what = r.missing.length === 1 ? '1 thing away' : r.missing.length + ' things away';
  return what + ': ' + r.missing.join(', ');
}
function buildPantryVoteText(cands, sid){
  var lines = ['Help us pick what to make for Halloween! Reply with 1, 2, or 3.'];
  cands.slice(0, 3).forEach(function(r, i){
    lines.push((i + 1) + '. ' + r.it.title + ' (' + pvGapLine(r) + ') - ' +
      'https://pickmycostume.com/c/' + r.it.id + '?s=' + sid + '&o=pantryvote');
  });
  var d = daysToHalloween();
  lines.push(d > 1 ? 'Halloween is ' + d + ' days out. Decide fast.'
    : (d === 1 ? 'Halloween is tomorrow. Decide fast.' : 'Halloween is today. Decide fast.'));
  return lines.join('\n');
}
function renderPantryVote(t0, t1){
  var box = document.getElementById('pvote');
  var cands = t0.concat(t1).slice(0, 3);
  if (cands.length < 2){ box.hidden = true; box.innerHTML = ''; return; }
  box.hidden = false;
  /* Rebuilt on every render() because each tick reshuffles the list. The
     panel starts closed so no share text can go stale between ticks; the
     share id is minted fresh on each panel open. */
  box.innerHTML =
    '<h3>Can\'t decide what to make?</h3>' +
    '<p>Send your top ' + cands.length + ' to the house group chat in one text. ' +
    'Everyone replies 1, 2, or 3 and the costume picks itself.</p>' +
    '<div class="pvrow"><button class="btn" id="pvote-btn" type="button">Let the house vote</button></div>' +
    '<div id="pvote-panel" style="display:none;margin-top:10px"></div>';
  document.getElementById('pvote-btn').addEventListener('click', function(){
    var panel = document.getElementById('pvote-panel');
    var btn = this;
    if (panel.style.display !== 'none'){
      panel.style.display = 'none'; btn.textContent = 'Let the house vote'; return;
    }
    var sid = newShareId();
    var ids = cands.map(function(r){ return r.it.id; });
    var text = buildPantryVoteText(cands, sid);
    track('pantry_vote_opened', { share_id: sid, idea_ids: ids, share_origin: 'pantryvote' });
    panel.innerHTML = '';
    var ta = document.createElement('textarea');
    ta.readOnly = true; ta.rows = 7 + cands.length;
    ta.style.cssText = 'width:100%;box-sizing:border-box;font-size:14px';
    ta.value = text;
    var row = document.createElement('div'); row.className = 'pvrow'; row.style.marginTop = '8px';
    var bCopy = document.createElement('button');
    bCopy.type = 'button'; bCopy.className = 'btn btn-ghost'; bCopy.textContent = 'Copy vote text';
    var bShare = document.createElement('button');
    bShare.type = 'button'; bShare.className = 'btn btn-ghost'; bShare.textContent = 'Share';
    var st = document.createElement('div'); st.className = 'pvstatus'; st.style.marginTop = '6px';
    bCopy.onclick = function(){
      var doneCopy = function(){
        bCopy.textContent = 'Copied \u2713';
        setTimeout(function(){ bCopy.textContent = 'Copy vote text'; }, 2000);
        track('pantry_vote_copied', { share_id: sid, idea_ids: ids, share_origin: 'pantryvote', via: 'clipboard' });
        st.textContent = 'Copied. Paste it in the group chat.';
      };
      if (navigator.clipboard && navigator.clipboard.writeText){
        navigator.clipboard.writeText(text).then(doneCopy, function(){ fallbackCopy(text, doneCopy); });
      } else { fallbackCopy(text, doneCopy); }
    };
    bShare.onclick = function(){
      if (bShare.disabled) return; /* double-tap guard: one share per tap */
      bShare.disabled = true;
      var rearm = function(){ bShare.disabled = false; };
      var viaCopy = function(){
        fallbackCopy(text, function(){
          track('pantry_vote_shared', { share_id: sid, idea_ids: ids, share_origin: 'pantryvote', via: 'clipboard' });
          st.textContent = 'Copied. Paste it in the group chat.';
          rearm();
        });
      };
      /* Red-team pattern from the challenge share: navigator.share can
         throw synchronously on some browsers, so try/catch the call. */
      if (navigator.share){
        try {
          navigator.share({ title: 'What should we make?', text: text }).then(
            function(){
              track('pantry_vote_shared', { share_id: sid, idea_ids: ids, share_origin: 'pantryvote', via: 'share_sheet' });
              st.textContent = 'Sent. Whoever replies first wins.';
              rearm();
            },
            function(){ viaCopy(); });
        } catch (e) { viaCopy(); }
      } else { viaCopy(); }
    };
    panel.appendChild(ta);
    row.appendChild(bCopy); row.appendChild(bShare);
    panel.appendChild(row); panel.appendChild(st);
    panel.style.display = 'block';
    btn.textContent = 'Hide the vote text';
  });
}

function renderGroups(){
  const host = document.getElementById('groups');
  host.innerHTML = DATA.groups.map(gr => {
    const items = DATA.pantry.filter(p => p.group === gr.id);
    return '<fieldset><legend>' + esc(gr.label) + '</legend><div class="checks">' +
      items.map(p =>
        '<label class="check' + (ticked.has(p.id) ? ' on' : '') +
        /* 2026-09-26 supply ask: ring the supplies the friend asked to
           borrow. typeof-guard: some test harnesses eval this function in
           isolation, like cardHtml's guard below. */
        ((typeof ASK !== 'undefined' && ASK && ASK.ids.indexOf(p.id) !== -1) ? ' asked' : '') + '">' +
        '<input type="checkbox" data-id="' + p.id + '"' + (ticked.has(p.id) ? ' checked' : '') +
        ' aria-label="' + esc(p.label) + '">' +
        '<span>' + emo(p.id) + esc(p.label) + '</span>' +
        /* 2026-09-27 cold-user QA: the space before the tag is load-bearing.
           Without it, textContent glues "assumed" onto the label
           ("Scissorsassumed"), so the typo-tolerant fuzzy search -- which
           matches whole words -- never matches a staple supply. */
        (p.staple ? ' <span class="tag">assumed</span>' : '') + '</label>'
      ).join('') + '</div></fieldset>';
  }).join('');
  host.querySelectorAll('input[type=checkbox]').forEach(cb => {
    cb.addEventListener('change', () => {
      /* 2026-09-27 cold-user QA: finger-bounce guard. Without this, a
         double-tap on the tile toggles twice (tick then untick) and the
         user's tick is silently eaten. The bounce's second change event is
         dropped and the DOM re-synced to the kept state. */
      if (!pantryTapGuard('tick-' + cb.dataset.id, 400)) {
        cb.checked = ticked.has(cb.dataset.id);
        cb.closest('.check').classList.toggle('on', cb.checked);
        return;
      }
      if (cb.checked) ticked.add(cb.dataset.id); else ticked.delete(cb.dataset.id);
      cb.closest('.check').classList.toggle('on', cb.checked);
      /* 2026-09-26 pm3 red-team P1: on a challenge arrival the recipient's own
         saved pantry stays in localStorage (applyChallenge keeps the kit in
         memory only). Persisting here would silently replace their list with
         the challenger's kit on the first tick, so the dare is answered
         in-memory only. */
      if (!(typeof CH !== 'undefined' && CH)) {
        try { localStorage.setItem(LS_KEY, JSON.stringify([...ticked])); } catch (e) {}
      }
      /* 2026-09-26: engagement instrumentation. Counts only -- never
         which materials (that's what's in their house). Debounced. */
      if (window._phT) clearTimeout(window._phT);
      window._phT = setTimeout(function(){ track('pantry_materials_changed', { ticked_count: ticked.size }); }, 1500);
      /* 2026-09-30 Tab 6 fix 3 (tap lag): the checkbox tile's own class
         flipped synchronously above -- defer the full render() a frame so the
         164-card rebuild can't block the tick's paint. */
      requestAnimationFrame(() => setTimeout(() => { render(); }, 0));
    });
  });
  applySearch();
}

function score(it){
  const missing = [];
  const missingIds = [];
  it.mats.forEach((m, i) => { if (!reqOk(m, it.id, i)) { missing.push(m.t); missingIds.push(repId(m)); } });
  return { it: it, have: it.mats.length - missing.length, total: it.mats.length, missing: missing, missingIds: missingIds };
}
/* 2026-09-26 challenge rematch: score one idea against an arbitrary kit
   without disturbing the live ticked set, so the verdict can compare the
   answerer's kit against the challenger's kit honestly. */
function scoreAgainst(it, kitSet){
  const saved = ticked;
  ticked = kitSet;
  try { return score(it); }
  finally { ticked = saved; }
}

function normUnlock(t){
  let s = t.toLowerCase().trim();
  s = s.replace(/^(a|an|the)\s+/, '');
  s = s.replace(/^\d+\s+(sheets?|pair|large|medium|small|roll|pack|ft\s)?/, '');
  s = s.replace(/^\d+\s+/, '');
  s = s.replace(/\s*\(.*?\)\s*$/, '');
  s = s.replace(/,?\s*(per|one per|\d+ per)\s+(person|kid|player|alien-role person).*$/, '');
  s = s.replace(/\s+/g, ' ').trim();
  return s;
}

function cardHtml(r, i, firstEager){
  /* typeof-guard: some test harnesses eval this function in isolation. */
  const viaS = (typeof VIA_S !== 'undefined' && VIA_S) ? '&s=' + VIA_S : '';
  const cls = r.missing.length === 0 ? ' zero' : (r.missing.length <= 2 ? ' almost' : '');
  /* 2026-09-27: work the cards backwards -- lead with the costume's
     full build ("here is how you make this with X"), every requirement
     marked have vs still-need, instead of the coverage-stats framing
     ("based on XYZ you can be this"). Replaces the old Still-need chips. */
  const rows = r.it.mats.map(m => {
    const ok = (typeof reqOk !== 'undefined') ? reqOk(m) : true;
    const b = (typeof matBits !== 'undefined') ? matBits(m) : { e: '🛒', label: (m.t || '') };
    const lbl = b.label;
    const e = b.e;
    const buyNote = (!ok && b.buy) ? '<span class="vh">buy it</span>' : '';
    return '<div class="mtile ' + (ok ? 'have' : 'miss') + '">' +
      '<span class="mtbadge" aria-hidden="true">' + (ok ? '\u2713' : '\u25CB') + '</span>' +
      '<span class="mtemo" aria-hidden="true">' + e + '</span>' +
      '<span class="mtlabel">' + esc(lbl) + '</span>' + buyNote + '</div>';
  }).join('');
  /* 2026-09-27: lead with what they likely have -- the
     requirements satisfied by the assumed basics -- so each card reads
     "here's what you likely have" instead of coverage stats. */
  const _staples = (typeof STAPLES !== 'undefined') ? STAPLES : [];
  const likely = r.it.mats.filter(m => {
    const ok = (typeof reqOk !== 'undefined') ? reqOk(m) : true;
    if (!ok) return false;
    const rid = (typeof repId !== 'undefined') ? repId(m) : null;
    return rid && _staples.indexOf(rid) !== -1;
  }).map(m => {
    const lbl = (typeof supplyLabel !== 'undefined') ? supplyLabel(repId(m)) : repId(m);
    return (typeof lc1 !== 'undefined') ? lc1(lbl) : lbl;
  }).filter((v, i, a) => a.indexOf(v) === i);
  /* 2026-09-30 Tab 6 fix 4: name the gap when it is 1-2 things; fix 11: strip (own)/(make)/(buy) tags. */
  const needNames = (r.missing || []).map(s => s.replace(/\s*\((own|make|buy)\)$/, '').replace(/^./, c => c.toLowerCase()));
  const likelyHtml = (r.missing.length === 1 || r.missing.length === 2)
    ? '<p class="likely">Just need: <b>' + esc(needNames.join(', ')) + '</b></p>'
    : (likely.length ? '<p class="likely">You likely have: <b>' + esc(likely.join(', ')) + '</b></p>' : '');
  /* 2026-09-28: visual-first -- the full have/miss checklist
     collapses into one tap so the card leads with the costume photo. */
  const needsHtml = rows
    ? '<details class="needs"><summary>What you need (' + r.it.mats.length + ')</summary>' +
      '<div class="mtiles">' + rows + '</div></details>' : '';
  return '<div class="card' + cls + '">' +
    '<div class="tile"><span class="temo" aria-hidden="true">' + ideaEmoji(r.it.id) + '</span>' +
    '<img class="thumb" src="photos/' + r.it.id + '.webp" alt="' + esc(r.it.title) + '"' +
    (firstEager && i === 0 ? ' loading="eager" fetchpriority="high"' : ' loading="lazy"') +
    ' onerror="this.remove()"></div>' +
    '<div class="cbody"><div class="rank">#' + (i + 1) + '</div>' +
    '<h3>' + esc(r.it.title) + '</h3>' + likelyHtml + needsHtml +
    '<a class="go" href="index.html?pick=' + r.it.id + viaS + '">How to make it</a></div></div>';
}

/* 2026-09-26 pantry deep-link: focused checklist for one costume.
   Arriving from a costume detail's "Check my pantry" (?for=<idea-id>) shows
   this card at the top: every requirement for that costume, each marked have
   vs missing against the live ticked set. Tapping a missing row ticks its
   representative supply in the main list below; the main checkboxes re-render
   this card too, so it stays live both ways. No ?for=, or an unknown id,
   renders nothing and the page behaves exactly as before. Analytics carries
   counts only, never material ids or ticked contents. */
function focusIdea(){
  if (!FOCUS_ID) return null;
  for (const it of (DATA.ideas || [])) if (it.id === FOCUS_ID) return it;
  return null;
}
function renderFocus(){
  const host = document.getElementById('focus');
  if (!host) return;
  const it = focusIdea();
  if (!it){ host.hidden = true; host.innerHTML = ''; return; }
  const r = score(it);
  /* 2026-09-28: visual materials -- tappable emoji tiles instead of
     text rows. Same tick behavior, same data-i hooks. */
  /* 2026-09-30 dup-tiles: one tile per pantry stash, not per material.
     Two materials that resolve to the same stash (two black-clothes slots,
     two felt colors via the multi-color stash) render a single tile. The
     tile reads have only when every material sharing the stash is covered. */
  const seenTiles = {};
  const tileOrder = [];
  it.mats.forEach((m, i) => {
    const b = matBits(m);
    const key = b.buy ? 'buy:' + b.label : 'id:' + b.id;
    const ok = reqOk(m, it.id, i);
    /* 2026-09-30 focus dead-tap fix (P0): keep EVERY material sharing the
       stash key, not just the first -- the tap target is the first entry
       still missing (root cause b). */
    if (seenTiles[key]){ seenTiles[key].mats.push({ m: m, i: i, ok: ok }); if (!ok) seenTiles[key].ok = false; return; }
    seenTiles[key] = { b: b, ok: ok, mats: [{ m: m, i: i, ok: ok }] };
    tileOrder.push(key);
  });
  const rows = tileOrder.map((key) => {
    const t = seenTiles[key];
    /* 2026-09-30 focus dead-tap fix (P0): the tap target is the FIRST material
       sharing this tile's stash key that is still missing. The old code used
       only the first material's nextTapId: when that material was satisfied
       but a later-sharing one wasn't, the tile showed missing with no tap
       handler (root cause b). nextTickId() scans every unsatisfied group; the
       hasBuyGap() fallback covers buy-only tiles and mixed materials whose
       stash groups are already covered (root cause a). */
    const target = t.mats.find(e => !e.ok) || t.mats[0];
    const m = target.m, i = target.i;
    const ok = t.ok;
    const tickId = nextTickId(m);
    const tappable = !ok && (!!tickId || hasBuyGap(m));
    const cls = ok ? 'have' : 'missing';
    const b = t.b;
    const label = b.label;
    /* 2026-09-30: a ticked buy tile drops the cart -- the checkmark alone
       says "handled". Missing buy tiles keep cart + "buy it". */
    const e = (b.buy && ok) ? '' : b.e;
    const buyNote = (!ok && b.buy) ? '<span class="vh">buy it</span>' : '';
    return '<div class="mtile ' + cls + '" data-key="' + esc(key) + '"' +
      (tappable ? ' role="button" tabindex="0" aria-label="Tick ' + esc(label) + '"' : '') + '>' +
      '<span class="mtbadge" aria-hidden="true">' + (ok ? '\u2713' : '\u25CB') + '</span>' +
      '<span class="mtemo" aria-hidden="true">' + e + '</span>' +
      '<span class="mtlabel">' + esc(label) + '</span>' + buyNote + '</div>';
  }).join('');
  const head = '<h2>' + esc(it.title) + ' needs:</h2>' +
    '<p class="fsub">You have <b>' + r.have + ' of ' + r.total + '</b>.' +
    (r.missing.length ? ' Tap a missing supply to tick it below.' : '') + '</p>';
  const needSeen = {};
  const needMats = it.mats.filter((mm, mi) => {
    if (reqOk(mm, it.id, mi)) return false;
    const nb = matBits(mm);
    const nk = nb.buy ? 'buy:' + nb.label : 'id:' + nb.id;
    if (needSeen[nk]) return false;
    needSeen[nk] = 1;
    return true;
  });
  const need = needMats.length === 0
    ? '<p class="fready">Nothing to buy. You are ready.</p>'
    : '<p class="fneed"><b>Still need:</b></p><div class="mchips">' + needMats.map(mm => {
        const b = matBits(mm);
        return '<span class="mchip"><span class="memo" aria-hidden="true">' +
          b.e + '</span>' + esc(lc1(b.label)) + '</span>';
      }).join('') + '</div>';
  const viaS = (typeof VIA_S !== 'undefined' && VIA_S) ? '&s=' + VIA_S : '';
  host.innerHTML = head + '<div class="mtiles">' + rows + '</div>' + need +
    '<a class="fgo" href="index.html?pick=' + encodeURIComponent(it.id) + viaS + '">See the full build guide &rarr;</a>';
  host.hidden = false;
  host.querySelectorAll('.mtile.missing[role="button"]').forEach(row => {
    const keyOf = (mm) => { const mb = matBits(mm); return mb.buy ? 'buy:' + mb.label : 'id:' + mb.id; };
    const tileEntries = () => {
      const out = [];
      for (let mi = 0; mi < it.mats.length; mi++){
        if (keyOf(it.mats[mi]) === row.dataset.key) out.push({ m: it.mats[mi], i: mi });
      }
      return out;
    };
    const tap = () => {
      /* 2026-09-30 focus dead-tap fix (P0): the tap target is the FIRST
         material sharing this tile's stash that is still missing, recomputed
         against the live ticked set (root cause b). */
      const entries = tileEntries();
      const target = entries.find(e => !reqOk(e.m, it.id, e.i));
      if (!target) return;
      /* 2026-09-27 cold-user QA: 400ms finger-bounce guard (same class as the
         checkbox tiles). A bounce on a buy tile would toggle twice and eat
         the tick. */
      if (!pantryTapGuard('ftap-' + row.dataset.key, 400)) return;
      const tickId = nextTickId(target.m);
      if (tickId) ticked.add(tickId);
      else {
        /* No tickable supply left: a buy-only tile, or a mixed material whose
           stash groups are already covered -- toggle the shared buy key. */
        const bk = pantryBuyKey(it.id, target.i);
        if (ticked.has(bk)) ticked.delete(bk); else ticked.add(bk);
      }
      /* 2026-09-30 Tab 6 fix 3 (tap lag): paint the tapped tile synchronously
         FIRST -- class, badge, emoji -- then defer the renderGroups()/render()
         rebuild a frame so the 164-card rebuild can't block the tile's own
         paint. One change covers the dead-tap fix and the tap-lag fix. */
      let tileOkNow = true;
      for (const e of tileEntries()){ if (!reqOk(e.m, it.id, e.i)){ tileOkNow = false; break; } }
      const badge = row.querySelector('.mtbadge');
      const emo = row.querySelector('.mtemo');
      const tb = matBits(target.m);
      row.classList.toggle('have', tileOkNow);
      row.classList.toggle('missing', !tileOkNow);
      if (badge) badge.textContent = tileOkNow ? '\u2713' : '\u25CB';
      if (emo) emo.textContent = (tb.buy && tileOkNow) ? '' : tb.e;
      if (tileOkNow){
        row.removeAttribute('role'); row.removeAttribute('tabindex'); row.removeAttribute('aria-label');
      } else {
        row.setAttribute('role', 'button'); row.setAttribute('tabindex', '0');
        const lbl = row.querySelector('.mtlabel');
        row.setAttribute('aria-label', 'Tick ' + (lbl ? lbl.textContent : 'supply'));
      }
      /* 2026-09-26 pm3 red-team P1: same challenge-arrival guard as the
         checkbox handler -- never persist the challenger's kit over the
         recipient's saved pantry. */
      if (!(typeof CH !== 'undefined' && CH)) {
        try { localStorage.setItem(LS_KEY, JSON.stringify([...ticked])); } catch (e) {}
      }
      track('pantry_focus_tick', { idea_id: it.id });
      requestAnimationFrame(() => setTimeout(() => { renderGroups(); render(); }, 0));
    };
    row.addEventListener('click', tap);
    row.addEventListener('keydown', (ev) => {
      if (ev.key === 'Enter' || ev.key === ' '){ ev.preventDefault(); tap(); }
    });
  });
  if (!window._phFv){ window._phFv = 1; track('pantry_focus_viewed', { idea_id: it.id, have_count: r.have, total_count: r.total }); }
}

/* 2026-09-30 Tab 6 fixes 1/6: Almost and Bigger build render capped; one tap reveals the full list.
   Persisted across render() ticks. */
let showAllT1 = false, showAllT2 = false;
function render(){
  const rows = DATA.ideas.map(score);
  const byMissing = (a, b) =>
    (a.missing.length - b.missing.length) ||
    (a.total - b.total) ||
    (a.it.title < b.it.title ? -1 : 1);
  const t0 = rows.filter(r => r.missing.length === 0).sort(byMissing);
  const t1 = rows.filter(r => r.missing.length >= 1 && r.missing.length <= 2).sort(byMissing);
  const t2 = rows.filter(r => r.missing.length >= 3).sort(byMissing);

  const stat = document.getElementById('stat');
  /* 2026-09-25: alive opening. The count is real on first paint because
     the assumed basics (scissors, tape, paper+pen) are pre-ticked.
     2026-09-26 red-team: the lead must match the actual ticked set ("just the
     basics" is wrong once the user ticks more), the almost-bucket is 1-or-2
     away (not "one supply away"), and a zero make-tonight count gets an
     honest zero-state instead of "you can make 0 tonight". */
  const onlyBasics = ticked.size === STAPLES.length && STAPLES.every(id => ticked.has(id));
  const lead = onlyBasics ? 'With just the basics' : 'With what you have ticked';
  const madeBit = t0.length ? lead + ', you can make <b>' + t0.length + '</b> tonight'
    : 'Nothing is fully covered yet';
  const almostBit = t1.length ? (t0.length ? ', and ' : ' - ') + '<b>' + t1.length + '</b> ' +
    (t1.length === 1 ? 'is' : 'are') + ' 1 or 2 supplies away.' : '.';
  /* 2026-09-28: the reshuffle hint lives on the supply-picker section below;
     the stat stays one line of alive numbers. */
  stat.innerHTML = madeBit + almostBit;
  /* 2026-09-30 Tab 6 fix 5: visible result right above the supply tiles. */
  (function(){
    const tp = document.getElementById('tickpulse');
    if (!tp) return;
    if (t0.length || t1.length) {
      tp.innerHTML = 'Now: ' + t0.length + ' tonight · ' + t1.length + ' almost — <a href="#tier1">see them</a>';
      tp.style.display = 'block';
    } else { tp.innerHTML = ''; tp.style.display = 'none'; }
  })();

  /* 2026-09-30 Tab 4 A2: 3 make-tonight photo cards above the supply grid. */
  (function(){
    const host = document.getElementById('tonight-photos');
    if (!host) return;
    const viaS = (typeof VIA_S !== 'undefined' && VIA_S) ? '&s=' + VIA_S : '';
    const top = t0.slice(0, 3);
    if (!top.length) { host.innerHTML = ''; return; }
    host.innerHTML =
      '<div class="reshead"><h2>Ready to make tonight</h2><span>with what you have ticked</span></div>' +
      '<div class="tphotos">' + top.map(r =>
        '<a class="tphoto" href="index.html?pick=' + r.it.id + viaS + '">' +
        '<img src="photos/' + r.it.id + '.webp" alt="' + esc(r.it.title) + '" loading="lazy" onerror="this.remove()">' +
        '<span>' + esc(r.it.title) + '</span></a>').join('') + '</div>';
  })();
  // unlock suggestions: single-item gaps only, ranked by costumes unlocked
  const unlockMap = {};
  rows.forEach(r => {
    if (r.missing.length !== 1) return;
    const t = r.missing[0];
    if (/ and |,/.test(t)) return; // multi-part gaps are not one purchase
    const k = normUnlock(t);
    if (!k) return;
    (unlockMap[k] = unlockMap[k] || { display: t, ideas: [] }).ideas.push(r.it.title);
  });
  const unlocks = Object.values(unlockMap)
    .sort((x, y) => y.ideas.length - x.ideas.length || (x.display < y.display ? -1 : 1))
    .slice(0, 5);
  const uh = document.getElementById('unlock');
  if (unlocks.length) {
    uh.hidden = false;
    uh.innerHTML = '<h2>One store trip away</h2>' +
      '<p class="lede">Grab one of these to unlock more costumes. ' +
      '<button class="btn btn-ghost copylist" id="copylist" type="button">Copy shopping list</button></p>' +
      unlocks.map(u =>
        '<div class="unlock-row"><span class="n">Buy ' + esc(u.display.charAt(0).toLowerCase() + u.display.slice(1)) +
        '</span><span> &middot; unlocks <b>' + u.ideas.length + '</b> costume' + (u.ideas.length > 1 ? 's' : '') +
        '<span class="w">' + esc(u.ideas.slice(0, 6).join(', ')) +
        (u.ideas.length > 6 ? ', +' + (u.ideas.length - 6) + ' more' : '') + '</span></span></div>'
      ).join('');
    lastUnlocks = unlocks;
    document.getElementById('copylist').addEventListener('click', copyUnlocks);
    /* 2026-09-27: removed the "Dare 3 friends to beat me" experiment
       CTA (Experiment 2, stream B 2026-09-26). It felt out of place on this
       page, and the data backed the cut: 1 challenge started, 0 completed
       in 7 days. The underlying ?kit= challenge/rematch flow is untouched. */
  } else { uh.hidden = true; uh.innerHTML = ''; lastUnlocks = []; }

  const put = (id, list, emptyMsg, firstEager) => {
    document.getElementById(id).innerHTML = list.length
      ? list.map(function(r, i){ return cardHtml(r, i, firstEager); }).join('')
      : '<p class="empty">' + emptyMsg + '</p>';
  };
  put('tier0', t0, 'Nothing fully covered yet. Tick what you own, or grab one item below.', true);
  put('tier1', showAllT1 ? t1 : t1.slice(0,3), 'Nothing is just 1 or 2 things away right now.');
  /* 2026-09-30 Tab 6 fix 1: capped Almost gets a one-tap reveal. */
  (function(){
    const host = document.getElementById('tier1');
    if (!host || showAllT1 || t1.length <= 3) return;
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'btn btn-ghost'; b.style.margin = '10px auto'; b.style.display = 'block';
    b.textContent = 'Show all ' + t1.length;
    b.addEventListener('click', function(){ showAllT1 = true; render(); });
    host.appendChild(b);
  })();
  put('tier2', showAllT2 ? t2 : t2.slice(0,8), '');
  /* 2026-09-30 Tab 6 fix 6: capped Bigger build gets a one-tap reveal. */
  (function(){
    const host = document.getElementById('tier2');
    if (!host || showAllT2 || t2.length <= 8) return;
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'btn btn-ghost'; b.style.margin = '10px auto'; b.style.display = 'block';
    b.textContent = 'Show all ' + t2.length + ' bigger builds';
    b.addEventListener('click', function(){ showAllT2 = true; render(); });
    host.appendChild(b);
  })();
  /* 2026-09-26: engagement instrumentation. Counts only, once per
     page load: did the ranked list actually render for them. */
  if (!window._phRv) { window._phRv = 1; track('pantry_results_viewed', { ready_count: t0.length, almost_count: t1.length, ticked_count: ticked.size }); }
  /* 2026-09-26: Make tonight instrumentation (traffic-pulse night2 finding:
     the Make tonight surface fired no analytics event at all). Once per
     page load, same shape as pantry_results_viewed. Purely additive. */
  if (!window._phMt) { window._phMt = 1; track('make_tonight_viewed', { ready_count: t0.length, ticked_count: ticked.size }); }
  /* 2026-09-26: the whole result card opens the full detail screen,
     not just the "How to make it" link. Taps on links/buttons/inputs keep
     their own behavior. */
  ['tier0','tier1','tier2'].forEach(function(tid){
    var t = document.getElementById(tid);
    if (t && !t.dataset.cardtap){
      t.dataset.cardtap = '1';
      t.addEventListener('click', function(ev){
        var card = ev.target.closest('.card');
        if (!card) return;
        var link = card.querySelector('a.go');
        if (!link) return;
        /* 2026-09-26: Make tonight tap instrumentation (traffic-pulse night2
           finding: the Make tonight surface fired no analytics). Fires for
           both whole-card taps and direct taps of the card's own
           "How to make it" link -- the only link inside a card is a.go, so
           button/input/select/textarea are the only exclusions. idea_id comes
           from the card's pick link. Additive only; the navigation below is
           unchanged. */
        /* 2026-09-28: summary taps toggle the collapsed details (what-you-need,
           assumed basics) instead of navigating away. */
        if (card.classList.contains('zero') && !ev.target.closest('button,input,select,textarea,summary')){
          var mtId = (link.getAttribute('href').match(/[?&]pick=([^&#]+)/) || [])[1];
          track('make_tonight_tapped', { idea_id: mtId ? decodeURIComponent(mtId) : '' });
        }
        if (ev.target.closest('a,button,input,select,textarea,summary')) return;
        location.href = link.getAttribute('href');
      });
    }
  });
  renderPantryVote(t0, t1);
  /* 2026-09-26 supply ask: sender box for the closest 1-2-away costume,
     then the recipient covered-state check. Both are no-ops when their
     preconditions fail, so existing renders are untouched. */
  renderSupplyAsk(t1);
  checkAskCovered();
  /* 2026-09-26 pantry deep-link: re-render the focused ?for= card on every
     tick so the have/missing checklist stays live. No-op without ?for=. */
  renderFocus();
}

document.getElementById('reset').addEventListener('click', () => {
  /* 2026-09-26 red-team recipient audit: on a challenge arrival (CH set) the
     recipient's OWN saved pantry is still in localStorage -- applyChallenge
     keeps the challenger's kit in memory only. "Start over" must restore
     their list, not staples: resetting a peeking recipient to STAPLES would
     silently destroy their saved pantry with one tap. */
  let restore = null;
  if (typeof CH !== 'undefined' && CH) {
    try { restore = JSON.parse(localStorage.getItem(LS_KEY) || 'null'); } catch (e) { restore = null; }
  }
  ticked = new Set(Array.isArray(restore) && restore.length ? restore : STAPLES);
  try { localStorage.setItem(LS_KEY, JSON.stringify([...ticked])); } catch (e) {}
  /* 2026-09-26 pm3 red-team P2: "Start over" on a challenge arrival left CH,
     the banner, and "Send the rematch" active, with the banner claiming the
     friend's supplies were ticked when they were not. Reset the challenge
     context and its UI alongside the ticked set. */
  CH = null; ASK = null;
  const _cb = document.getElementById('challenge-banner');
  if (_cb){ _cb.hidden = true; _cb.innerHTML = ''; }
  const _chb = document.getElementById('challenge');
  if (_chb) _chb.textContent = 'Challenge a friend';
  const _at = document.getElementById('atell');
  if (_at){ _at.hidden = true; _at.innerHTML = ''; }
  renderGroups();
  render();
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

/* ================= Chopped: the 5-supply pantry game (2026-09-29) ==
   We deal 5 real pantry supplies pulled from actual costume builds. The
   player picks the ONE costume they could honestly build with just the
   basket plus the household basics, then we reveal what each option was
   really missing. That reveal is the Chopped tension.
   HONEST RULE (also stated in the UI): the household staples are always
   assumed owned (scissors, tape, markers, paper and pen, foil, cardboard,
   and the plain clothes marked staple:true in DATA). Everything else must
   come from the 5 dealt supplies. A costume is buildable when every one of
   its materials is covered: each requirement group needs at least one of
   its pantry ids in (basket + staples). The player's own ticked pantry does
   NOT count: this game is about the dealt basket, not what is in the house.
   Materials the audit could not map to a pantry supply ([[null]] groups)
   can never be covered by a basket.
   ROUND CONSTRUCTION: pure random dealing would leave most rounds with no
   buildable option at all, which is a dud round for a kid. So the basket is
   built from one answer costume's own required supplies plus decoys, and the
   three distractors are verified NOT buildable from it. Every round has
   exactly one honest answer. */
var CHOP = { round: null, played: 0, correct: 0 };
var CHOP_STAPLES = {};
DATA.pantry.forEach(function(p){ if (p.staple) CHOP_STAPLES[p.id] = 1; });

function chopShuffle(a){
  for (var i = a.length - 1; i > 0; i--){
    var j = Math.floor(Math.random() * (i + 1));
    var t = a[i]; a[i] = a[j]; a[j] = t;
  }
  return a;
}
/* Non-staple pantry ids this costume needs, one per unsatisfied OR-group.
   impossible=true when a material has a group no basket could ever cover. */
function chopNeeds(idea){
  var need = [], impossible = false;
  (idea.mats || []).forEach(function(m){
    ((m.g) || []).forEach(function(grp){
      var real = (grp || []).filter(function(id){ return !!id; });
      if (!real.length){ impossible = true; return; }
      if (real.some(function(id){ return CHOP_STAPLES[id]; })) return;
      var pick = real[0];
      if (need.indexOf(pick) === -1) need.push(pick);
    });
  });
  return { need: need, impossible: impossible };
}
function chopHave(basket){
  var have = {};
  (basket || []).forEach(function(id){ have[id] = 1; });
  for (var id in CHOP_STAPLES) have[id] = 1;
  return have;
}
function chopBuildable(idea, basket){
  var have = chopHave(basket);
  return (idea.mats || []).every(function(m){
    return ((m.g) || []).every(function(grp){
      return (grp || []).some(function(id){ return id && have[id]; });
    });
  });
}
/* The missing pieces: raw material texts of every unsatisfied material. */
function chopMissing(idea, basket){
  var have = chopHave(basket);
  return (idea.mats || []).filter(function(m){
    return !((m.g) || []).every(function(grp){
      return (grp || []).some(function(id){ return id && have[id]; });
    });
  }).map(function(m){ return m.t; });
}
function chopNewRound(){
  var cands = DATA.ideas.filter(function(it){
    var r = chopNeeds(it);
    return !r.impossible && r.need.length >= 1 && r.need.length <= 5;
  });
  if (!cands.length) return null;
  var ans = cands[Math.floor(Math.random() * cands.length)];
  var need = chopShuffle(chopNeeds(ans).need.slice());
  var basket = need.slice(0, 5);
  var decoys = chopShuffle(DATA.pantry.map(function(p){ return p.id; }).filter(function(id){
    return !CHOP_STAPLES[id] && basket.indexOf(id) === -1;
  }));
  while (basket.length < 5 && decoys.length) basket.push(decoys.pop());
  chopShuffle(basket);
  var pool = chopShuffle(DATA.ideas.filter(function(it){ return it.id !== ans.id; }));
  var distract = [];
  for (var k = 0; k < pool.length && distract.length < 3; k++){
    if (!chopBuildable(pool[k], basket)) distract.push(pool[k]);
  }
  return { answer: ans, basket: basket, options: chopShuffle([ans].concat(distract)) };
}
function chopBasketChips(basket){
  return basket.map(function(id){
    var e = emoChar(id);
    return '<span class="chop-chip">' +
      (e ? '<span aria-hidden="true">' + e + '</span>' : '') +
      esc(supplyLabel(id)) + '</span>';
  }).join('');
}
function chopRenderIntro(){
  var el = document.getElementById('chopped');
  if (!el) return;
  el.innerHTML =
    '<p class="tier-sub">We deal you 5 mystery supplies pulled from real costume builds. ' +
    'Pick the ONE costume you could honestly build with just those plus the household basics. ' +
    'Then we reveal what each costume was really missing.</p>' +
    '<div class="actions"><button class="btn" id="chop-deal" type="button">Deal the basket</button></div>' +
    '<p class="chop-note">The basics are always assumed: scissors, tape, markers, paper, foil, ' +
    'cardboard, and plain clothes. Your ticked pantry does not count here. Only the basket does.</p>';
  document.getElementById('chop-deal').addEventListener('click', function(){
    if (!pantryTapGuard('chopped-deal', 400)) return;
    CHOP.round = chopNewRound();
    if (!CHOP.round) return;
    track('chopped_started', { basket: CHOP.round.basket });
    chopRenderBasket();
  });
}
function chopRenderBasket(){
  var r = CHOP.round;
  if (!r) return;
  var el = document.getElementById('chopped');
  el.innerHTML =
    '<p class="tier-sub">Your basket. Which ONE of these could you honestly build with only this plus the basics?</p>' +
    '<div class="chop-basket" aria-label="Your basket">' + chopBasketChips(r.basket) + '</div>' +
    '<div class="chop-opts">' +
    r.options.map(function(it){
      return '<button class="chop-opt" type="button" data-id="' + esc(it.id) + '">' +
        '<span class="chop-emo" aria-hidden="true">' + ideaEmoji(it.id) + '</span>' +
        '<span>' + esc(it.title) + '</span></button>';
    }).join('') + '</div>';
  Array.prototype.forEach.call(el.querySelectorAll('.chop-opt'), function(btn){
    btn.addEventListener('click', function(){
      /* 400ms tapGuard like every other multi-step flow: a finger bounce
         must not double-fire the pick. */
      if (!pantryTapGuard('chopped-pick', 400)) return;
      chopReveal(btn.getAttribute('data-id'));
    });
  });
}
function chopReveal(pickedId){
  var r = CHOP.round;
  if (!r) return;
  var correct = (pickedId === r.answer.id);
  CHOP.played++;
  if (correct) CHOP.correct++;
  track('chopped_revealed', { picked: pickedId, answer: r.answer.id, correct: correct, played: CHOP.played });
  var el = document.getElementById('chopped');
  var verdict = correct
    ? '<p class="chop-verdict good">You got it. ' + esc(r.answer.title) + ' is the one your basket can honestly build.</p>'
    : '<p class="chop-verdict bad">Not quite. The honest build was ' + esc(r.answer.title) + '.</p>';
  var rows = r.options.map(function(it){
    var ok = chopBuildable(it, r.basket);
    var missHtml = '';
    if (!ok){
      var missing = chopMissing(it, r.basket);
      missHtml = '<span class="chop-miss">Missing: ' + esc(missing.slice(0, 3).join('; ')) +
        (missing.length > 3 ? '; and ' + (missing.length - 3) + ' more' : '') + '</span>';
    }
    return '<div class="chop-row' + (ok ? ' ok' : '') + (it.id === pickedId ? ' picked' : '') + '">' +
      '<span class="chop-emo" aria-hidden="true">' + ideaEmoji(it.id) + '</span>' +
      '<span class="chop-rtitle">' + esc(it.title) +
      (ok ? '<span class="chop-tag good">buildable</span>' : '<span class="chop-tag bad">not buildable</span>') +
      missHtml + '</span></div>';
  }).join('');
  el.innerHTML = verdict +
    '<div class="chop-reveal">' + rows + '</div>' +
    '<p class="chop-score">You have called ' + CHOP.correct + ' of ' + CHOP.played + ' baskets right.</p>' +
    '<div class="actions"><button class="btn" id="chop-again" type="button">Deal again</button></div>';
  document.getElementById('chop-again').addEventListener('click', function(){
    if (!pantryTapGuard('chopped-deal', 400)) return;
    CHOP.round = chopNewRound();
    if (!CHOP.round) return;
    track('chopped_started', { basket: CHOP.round.basket });
    chopRenderBasket();
  });
  try { el.scrollIntoView({ block: 'nearest' }); } catch (e) {}
}

applyChallenge();
applySupplyAsk();
renderGroups();
render();
chopRenderIntro();
document.getElementById('supply-search').addEventListener('input', applySearch);
/* 2026-09-30 Tab 4 A4: share the pantry list with a partner. */
(function(){
  const btn = document.getElementById('sharesheet');
  if (!btn) return;
  const status = document.getElementById('sharestatus');
  const url = 'https://pickmycostume.com/pantry';
  const text = 'I ticked what we already own \u2014 see what costumes we can make tonight: ' + url;
  const done = function(via){
    if (status){ status.style.display = 'block'; status.textContent = 'Copied \u2014 send it to your partner.'; }
    track('pantry_share', { via: via });
  };
  btn.addEventListener('click', function(){
    if (navigator.share) {
      navigator.share({ title: 'Pick My Costume \u2014 pantry', text: text, url: url }).catch(function(){});
    } else if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function(){ done('clipboard'); }, function(){});
    } else { fallbackCopy(text, function(){ done('fallback'); }); }
  });
})();
const _chInit = document.getElementById('challenge');
if (_chInit) _chInit.addEventListener('click', onChallenge);
</script>
</body>
</html>

"""

if __name__ == "__main__":
    main()
