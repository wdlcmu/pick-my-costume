# Pick My Costume : plugin directory listing copy (draft, Billy approves before use)

## Info tab

- **Name:** Pick My Costume
- **Short description:** Get Halloween costume ideas from stuff you already
  own, with step-by-step build guides.
- **Long description:** Pick My Costume turns your closet into a costume shop.
  Tell it who the costume is for, the vibe you want, and how much effort you
  can spend, or list household items you already have. It recommends from 169
  original costume ideas, each with a materials list, build steps, time and
  cost estimates, and safety notes written for parents. Every idea links to its
  full guide at pickmycostume.com.
- **Category:** Lifestyle (confirm available categories in the portal)
- **Website:** https://pickmycostume.com
- **Support URL:** https://pickmycostume.com
- **Privacy policy URL:**
  https://mcp.pickmycostume.com/privacy-policy
- **Terms URL:** https://mcp.pickmycostume.com/terms

## Server instructions (contract snapshot — matches initialize response verbatim)

Pick My Costume recommends Halloween costumes you can actually build. Call
pick_costume when the user wants concrete costume ideas: it returns 3 picks,
each with a why-line, a photo thumbnail, and a link to its full build page.
Call get_build_guide when the user settles on one idea and wants the
step-by-step build (materials, steps, time, cost, effort). Call search_by_owning
when the user wants ideas based on items they already own. Keep answers to what
the tools return: do not invent costume ideas, materials, or build steps. All
tools are read-only; nothing is bought, sold, or booked.

## Tool annotation justifications (ChatGPT Apps portal: per-annotation)

- readOnlyHint true: tools only read the bundled costume bank; nothing is
  created, updated, deleted, bought, sold, or booked.
- destructiveHint false: no destructive action exists; the server is
  stateless and every call is a pure read.
- idempotentHint true: identical arguments always return identical results.
- openWorldHint false: tools operate only on the bundled 169-idea dataset;
  they never browse the web or call external services.

## Starter prompts (Prompts tab)

1. I need a Halloween costume for my 3-year-old. I have a bedsheet and about
   20 minutes.
2. What materials do I need for a ballerina costume?
3. Give me 3 funny couples costume ideas, something easy.
4. What can I make with cardboard and tape?

## Release notes (Submit tab)

Initial submission. Pick My Costume MCP server: three read-only tools
(pick_costume, get_build_guide, search_by_owning) over a 169-idea costume bank.
No authentication, no user data collected, no UI component. Tested locally and
against the production worker.

## Global tab

Suggested countries to start: United States, Canada, United Kingdom, Australia
(Halloween-heavy markets; support and privacy are US-ready).

## Staged optional copy (no portal field: official docs list no developer-bio
field on the Info tab; kept ready in case the portal shows one or for reuse)

- **Developer bio:** I'm a dad making tiny Halloween tools. Pick My Costume
  is a 2-minute quiz that picks your Halloween costume: a few questions,
  3 ideas, each with build instructions. (Approved by Billy 2026-09-25.)
