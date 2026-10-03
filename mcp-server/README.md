# Pick My Costume MCP server — the connector moat

A remote MCP server (Streamable HTTP) exposing the site's 169 costume ideas as
three read-only tools AI assistants can call. One server serves both ChatGPT
Apps and Claude Connectors, since both speak MCP over Streamable HTTP.

**The moat logic:** citations are rented land (per-query, ungameable for
evergreen questions). A connector is owned land — when the assistant can *call*
Pick My Costume as a tool, we are infrastructure, not a search result.

## File layout

```
mcp-server/
  package.json            zero dependencies; npm run build / npm start
  wrangler.toml           Cloudflare Worker deploy scaffold (DO NOT deploy without Billy)
  bank.json               generated snapshot of the 169-idea bank (regenerate after bank changes)
  TEST-CASES.md           5 reviewer test cases (user query -> expected tool)
  test-local.mjs          24-assertion local test suite (node test-local.mjs)
  scripts/build-bank.mjs  extracts bank.json from ../index.html + ../pantry-mats.json
  src/
    tools.mjs             pure tool implementations (pick_costume, get_build_guide, search_by_owning)
    aliases.mjs           old-slug -> current-slug map (copied from gen_share_function.py)
    mcp.mjs               JSON-RPC dispatch: initialize, tools/list, tools/call
    server.mjs            local Node HTTP server (POST /mcp, /privacy-policy, /.well-known/...)
    worker.mjs            Cloudflare Worker entry (reuses mcp.mjs + tools.mjs, bundles bank.json)
    privacy.html          privacy-policy draft page (read-only, no data collected)
```

## Local dev

```bash
npm run build   # regenerate bank.json from the repo (run after any bank change)
npm start       # serve on :8787
node test-local.mjs   # 24 assertions, all green
```

## What Billy needs to provide (accounts, not code)

1. **Deploy:** his Cloudflare account — `wrangler login`, then `npm run build && wrangler deploy`.
   Deploys to `pick-my-costume-mcp.<his-subdomain>.workers.dev`; point a custom
   domain/path at it if desired. No code changes needed.
2. **ChatGPT Apps submission:** OpenAI will issue a domain-verification challenge
   during submission — set it as `wrangler secret put OPENAI_APPS_CHALLENGE`
   (the `/.well-known/openai-apps-challenge` endpoint serves it verbatim).
   Privacy policy is code-final: src/privacy.html carries the contact email
   (hello@pickmycostume.com) and effective date (September 25, 2026), served at
   /privacy-policy once the worker is live. Submit through the ChatGPT Apps
   directory flow.
3. **Claude Connectors:** publish the MCP server URL as a remote MCP connector;
   follows Anthropic's connector submission process (no code changes needed).
4. **Ongoing:** re-run `npm run build` + redeploy whenever the idea bank changes
   (new ideas, guide rewrites), or the tools serve stale data.

## Design notes

- **Read-only, no auth, no user data.** The server never sees who is asking.
- **pick_costume** mirrors the site's own quiz scoring (answer-weight x tag-weight,
  minus the -24 promise penalties), so tool picks agree with site picks.
- **search_by_owning** reuses `pantry-mats.json`; the 6 household staples
  (scissors, tape, paper+pen, foil, cardboard, socks) are assumed present, matching
  the site's pantry defaults. Ideas rank by coverage, then by whether the user's
  own items (not staples) are the hero materials.
- Every tool response links `https://pickmycostume.com/c/<id>` pages and
  `images/og/<id>.jpg` thumbnails, so in-assistant usage drives site traffic.
- Tool descriptions are tuned toward transactional queries ("what materials do I
  need", "step by step build instructions", "costumes from stuff at home") where
  models reach for tools — not "pick a costume", which models answer from knowledge.
