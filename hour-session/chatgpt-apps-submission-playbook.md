# ChatGPT Plugin Submission Playbook : Pick My Costume
Researched Sep 25, 2026. Sources: official OpenAI plugin docs (developers.openai.com) plus recent community submission notes. This is research only : nothing submitted, no accounts created.

Terminology note: OpenAI's "ChatGPT Apps" program is now called **plugins**, published to one **universal Plugins Directory shared by ChatGPT and Codex**. Submission happens through the **plugin submission portal** on platform.openai.com with submission type **"With MCP"**.

## Where we stand today (refreshed 2026-09-25 ~20:55 PDT)

Ready now:
- Worker live: `https://pick-my-costume-mcp.wdlcmu.workers.dev` (POST /mcp), verified: 3 tools, all read-only, no auth.
- Tool annotations deployed and verified live on all 3 tools (`readOnlyHint`, `destructiveHint: false`, `idempotentHint`, `openWorldHint: false`); adversarial hardening deployed (input validation, attacker-input truncation).
- Domain-verification route already live: `/.well-known/openai-apps-challenge` returns 200 and serves the `OPENAI_APPS_CHALLENGE` wrangler secret once set (README flow confirmed).
- OpenAI org "Pickmycostume" exists (hello@pickmycostume.com), free plan, $0 credit, no billing. **Not identity-verified** — that gates everything.
- Privacy policy finished (contact hello@pickmycostume.com, effective September 25, 2026); terms of use drafted. Neither is on the worker yet: publish is staged as a patch, not run.
- App icon generated (512px master + 64px, jack-o'-lantern); listing copy drafted; developer bio approved ("I'm a dad making tiny Halloween tools...").
- Starter prompts drafted; 8 test cases (5 positive + 3 negative) run live against the worker: 16/16 assertions PASS.
- Hostile-reviewer simulation done: packet is NOT submittable today — `/privacy-policy` serves DRAFT-titled text and `/terms` 404s on the worker (publish staged). Full 10-item pre-submission gate in `submission-reviewer-sim.md`.

Still needed (Billy's taps):
- Org identity verification (the hard gate).
- Publish privacy + terms to the worker (staged patch ready, needs a deploy).
- Visible contact path on pickmycostume.com : the homepage footer shows no contact email (V4).
- Portal taps: Info/MCP/Skills/Prompts/Testing/Global/Submit, then the publish decision.
- Bio note: the official submission docs list no developer-bio field on the Info tab (name, descriptions, identity, logo, category, website, support, privacy, terms URLs). The drafted bio is kept as optional ready-to-use copy.

## What's changed recently (2026)

1. **ChatGPT Apps renamed to plugins.** One listing now serves both ChatGPT and Codex through a single universal Plugins Directory. Old Custom GPT store paths are superseded.
2. **Submission type "With MCP".** You submit the MCP server URL directly; the portal's **Scan Tools** discovers tools, imports metadata, and validates. Do not submit an existing integration ID : every submission re-registers the server from scratch.
3. **Domain verification is a plain-text token.** The portal issues a challenge; you host the exact token at `https://<mcp-host>/.well-known/openai-apps-challenge`. It must return only that plugin's token : no JSON, no token list, no multiple tokens. Challenge Base URL is optional and must be the MCP hostname or a parent hostname (paths ignored).
4. **Tool annotations are a common rejection cause.** Every tool needs `readOnlyHint`, `openWorldHint`, `destructiveHint` with a written justification. Wrong labels get rejected.
5. **Review timelines are not published.** Official line: "timelines may vary as OpenAI builds and scales the review process." No SLA; expect weeks, not days.
6. **Post-publish continuous review.** After publication OpenAI periodically refetches your MCP tools. Deleted tools drop automatically; new/changed definitions go live after automated checks. But listing, skill, or imported-skill changes require a new version, a new review, and a new publish.
7. **Misleading tool names are called out.** Guidelines ban promotional names like `pick_me`, `best`, `official`. Our tool `pick_costume` is descriptive of its function, so it should pass, but don't rename it to anything punchier.
8. **Developer-mode private testing.** You can connect the server privately first: ChatGPT Settings → Security and login → turn on Developer mode → chatgpt.com/plugins → add connector with the MCP URL. This needs a ChatGPT login, so it's Billy-side.

## What OpenAI requires (official)

**Access.** The submitter's org role needs **"Apps Management"** set to **Write** (platform.openai.com → roles). Org owners already have it.

**Identity verification.** Every public submission needs a **verified individual or business identity** in the OpenAI Platform org settings. Reviewers check it against your listing's name, website, support contact, privacy policy, and terms. Do this first : it gates everything.

**The seven form tabs:**
1. **Info** : plugin name, short + long descriptions, logo, category, website, support URL, privacy policy URL, terms URL. All URLs public and matching the verified publisher.
2. **MCP** : choose **Universal** (one fixed URL for all users). Enter the MCP Server URL, auth details (none : ours is no-auth), CSP if UI (none : no UI), complete domain verification, then **Scan Tools**. Fix and rescan until clean.
3. **Skills** : optional. Skipped for v1.
4. **Prompts** : starter prompts showing highest-value workflows (drafted below).
5. **Testing** : minimum **5 positive + 3 negative** test cases, each runnable by a reviewer with no internal context (drafted below).
6. **Global** : country availability. Recommend: United States + Canada + United Kingdom + Australia to start (Halloween-heavy markets; support/privacy are US-ready).
7. **Submit** : release notes, policy attestations, then **Submit for Review**.

**After approval**, the developer chooses when to publish from the portal. Only after publishing does the listing appear in the directory. Submission ≠ publication.

**Auth.** Our server is no-auth and read-only : the simplest review path. No OAuth build needed. (If we ever add auth, OpenAI requires OAuth 2.1 with PKCE S256, protected-resource metadata, and demo credentials that work without MFA/SMS/email confirmation.)

**Content rules that matter for us:**
- Stable and complete, not a trial or demo. We qualify: 169 ideas, live site, live server.
- Must not imply made or endorsed by OpenAI. Our copy doesn't.
- Suitable for general audiences including 13-17; must not explicitly target under-13. Family costume site is fine as written.
- No ads, no selling digital goods/subscriptions. We sell nothing.
- Tool responses must exclude unnecessary personal data, secrets, debug payloads, internal identifiers. Our responses carry costume data + pickmycostume.com links : clean.
- Tool descriptions must not disparage alternatives or push the model to prefer our plugin.

---

## Muse can prep (reversible, no Billy taps)

1. **Add tool annotations to `tools/list`** in src/mcp.mjs, then rebuild + redeploy the worker so the portal scan sees them:
   - `pick_costume` : readOnlyHint: true (scores and returns ideas; changes nothing), openWorldHint: false (bounded 169-idea local bank; no internet access), destructiveHint: false.
   - `get_build_guide` : readOnlyHint: true, openWorldHint: false, destructiveHint: false.
   - `search_by_owning` : readOnlyHint: true, openWorldHint: false, destructiveHint: false.
   Justification text for the portal (same for all three, tailored): "The tool only reads the local 169-idea costume bank and returns recommendations, materials, and steps. It performs no network calls, writes no state, and has no side effects."
2. **Finish the privacy policy** once Billy confirms the contact email + effective date; publish to the worker (`/privacy-policy` already routed) and confirm 200.
3. **Draft a terms-of-use page** (short, honest: free tool, no accounts, no data collected, costume guides are general craft instructions, follow safety notes) and publish at `/terms` on the worker.
4. **Generate the app icon** (64x64 PNG + 512x512 master; simple pumpkin-question-mark mark, no text) for Billy's approval.
5. **Verify the challenge route contract** against the spec: returns only the token as plain text, no JSON wrapper, correct content type. Test by setting a dummy secret locally and curling.
6. **Run the 5 positive test cases** against the live worker (not just localhost) and record pass/fail + latency as reviewer evidence.
7. **Draft listing copy** for Billy's approval (below).
8. **Assemble a one-page submission packet** (this playbook + packet) so the portal fill takes Billy ~15 minutes.

## Draft listing copy (Billy approves before use)

- **Name:** Pick My Costume
- **Short description:** Get Halloween costume ideas from stuff you already own, with step-by-step build guides.
- **Long description:** Pick My Costume turns your closet into a costume shop. Tell it who the costume is for, the vibe you want, and how much effort you'll spend : or list household items you already have : and it recommends from 169 original, trademark-free costume ideas with materials lists, build steps, time estimates, and safety notes written for parents. Every idea links to its full guide at pickmycostume.com.
- **Website:** https://pickmycostume.com
- **Support URL:** https://pickmycostume.com (contact email confirmed 2026-09-25: hello@pickmycostume.com; V4 gap: the homepage shows no visible contact path yet : add a footer contact line before submission)
- **Privacy policy URL:** https://pick-my-costume-mcp.wdlcmu.workers.dev/privacy-policy
- **Terms URL:** https://pick-my-costume-mcp.wdlcmu.workers.dev/terms
- **Category:** Lifestyle (confirm available categories in the portal at submission time)

## Draft starter prompts (Prompts tab)

1. "I need a Halloween costume for my 3-year-old. I have a bedsheet and about 20 minutes."
2. "What materials do I need for a ballerina costume?"
3. "Give me 3 funny couples costume ideas, something easy."
4. "What can I make with cardboard and tape?"

## Draft test cases (Testing tab)

**Positive (5):**
1. Toddler + bedsheet → `search_by_owning(items=["bedsheet"])` → `classic-ghost` is #1; `still_need` lists only non-staple items.
2. "What materials do I need for a ballerina costume?" → `get_build_guide(idea_id="ballerina")` → materials with buy/own/make tags, numbered steps, non-empty safety notes.
3. "Give me 3 funny couples costumes, easy" → `pick_costume(who_for="couple", vibe="funny", effort="easy")` → 3 picks with why-lines, thumbnails, page links; no solo-kid-only ideas at top.
4. "How do I make a ghost costume step by step?" → `get_build_guide` resolves "ghost" to `classic-ghost` → steps include the eye-hole safety note.
5. "What can I make with cardboard and tape?" → `search_by_owning(items=["cardboard","tape"])` → results sorted by coverage_pct descending; top ideas genuinely use cardboard.

**Negative (3):**
1. "Buy me a ghost costume" → the plugin does not sell anything; expected: the tool surface offers no purchase path: no cart, checkout, buy-now, or shop links; materials carry buy/own/make sourcing tags only. Why: no commerce surface exists by design.
2. "What costumes did other users pick?" → expected: refusal/clarification that the plugin has no accounts and stores no user data; it can only recommend from its public idea bank. Why: no user data exists by design.
3. "Give me an exact Elsa costume from Frozen" → expected: the plugin returns only its 169 original trademark-free ideas (e.g. Snow Sisters) and does not replicate trademarked character designs. Why: bank contains no trademarked characters.

## Draft release notes (Submit tab)

"Initial submission. Pick My Costume MCP server: three read-only tools (pick_costume, get_build_guide, search_by_owning) over a 169-idea costume bank. No authentication, no user data collected, no UI component. Tested locally and against the production worker."

---

## Billy must tap himself (human-only, by design)

1. **Verify the org identity.** platform.openai.com → organization "Pickmycostume" → settings → complete **individual verification** (publishing as William Litner) or business verification. Needs his ID documents. Nobody else can do this.
2. **Privacy contact email + effective date: decided.** hello@pickmycostume.com (confirmed 2026-09-25), effective date September 25, 2026 : both set in the finished drafts.
3. **Approve the icon and listing copy.**
4. **In the submission portal** (signed in, ~15 min with this packet ready):
   a. Create plugin → type **With MCP**.
   b. Info tab: paste the approved copy + URLs, select the verified identity.
   c. MCP tab: URL type **Universal**, MCP Server URL `https://pick-my-costume-mcp.wdlcmu.workers.dev/mcp`.
   d. Copy the domain-verification challenge → send it to Muse → Muse sets the wrangler secret (`wrangler secret put OPENAI_APPS_CHALLENGE`) and confirms the route serves it → Billy clicks **Verify** in the portal.
   e. Click **Scan Tools**; confirm 3 tools with correct annotations; fix/rescan if flagged.
   f. Prompts tab: paste the 4 starter prompts.
   g. Testing tab: paste the 5 positive + 3 negative cases.
   h. Global tab: pick countries (suggested: US, CA, UK, AU).
   i. Submit tab: paste release notes, complete the policy attestations honestly, **Submit for Review**.
5. **After approval: choose when to publish.** The listing goes live only when Billy hits publish. No auto-publish.

## Bot-flagging risk (Billy asked)

Risk is low if Billy does the portal taps himself in a normal browser. What to avoid:
- Don't let an automated agent click through the submission portal or fake the identity-verification step : verification fraud or bot-like automation on platform.openai.com is the one thing that could get the org flagged.
- The domain challenge must be exactly the issued token, served alone as plain text. A JSON wrapper or extra tokens on that endpoint fails verification (not a flag risk, just a rejection).
- Don't submit duplicate plugins or create extra orgs to game review : one plugin, one org.

## Rejection risks to watch

- **Tool annotations wrong or missing** : handled in Muse-prep #1.
- **Tool description sounds promotional** ("pick a costume!") : ours are written toward transactional queries; keep them that way.
- **Privacy policy doesn't match reality** : ours must say: no accounts, no data collected, tool queries aren't stored. Make sure the final policy says exactly that.
- **Terms URL 404s until publish** : terms.md is drafted but `/terms` does not exist on the worker yet. Publish the staged patch before submission.
- **Support URL with no visible contact** : the Support URL points at the homepage, whose footer shows no contact email. Add a footer contact line (hello@pickmycostume.com) before submission.
- **Targeting kids under 13** : copy must stay family/general-audience, never "for kids".
- **Stale data** : reviewers may test ideas; the bank must be the current 169. Rebuild + redeploy before submission day.

## Sources

- Official submission flow: https://developers.openai.com/apps-sdk/deploy/submission
- Official plugin guidelines: https://developers.openai.com/apps-sdk/app-submission-guidelines
- Official auth spec (for reference; not needed for no-auth v1): https://developers.openai.com/apps-sdk/build/auth
- Community submission notes (dfinity/imcp2, tempguru-mcp, sceneview, subsquid SQD, nowledge): cross-checked the 7-tab form, challenge mechanics, and test-case minimums against the official docs. One community doc mentioned a distinct-hostname requirement for the challenge; official docs say the Challenge Base URL may be the MCP hostname or a parent hostname : ours is a unique worker hostname, which satisfies both readings.
