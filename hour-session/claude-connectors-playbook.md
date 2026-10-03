# Claude Connectors Playbook — Pick My Costume
Researched Sep 26, 2026. Sources: official Anthropic docs (claude.com/docs/connectors/building/submission, claude.com/docs/plugins/submit), the official Anthropic Software Directory Policy (support.claude.com), plus recent community submission notes. This is research only — nothing submitted, no accounts created.

## The short version

Submit the worker as an **MCP connector** (not a plugin bundle) through Anthropic's developer portal at **claude.ai/directory/manage** → "Submit new" → "MCP connector". The plugin-bundle path forces open-sourcing the code on GitHub (public repo required before listing goes live) — wrong for us. The connector path keeps the server closed-source and lists it in the in-app Connectors Directory (Claude.ai, Desktop, Mobile, Code, Cowork, one-click install).

Biggest differences from the OpenAI path: no domain-verification challenge token (the portal connects to the server directly), no identity-document verification, but Anthropic **requires a `title` on every tool** (our worker does not have them yet), and review is an **automatic scan that lists us as a Community connector by default** (community reports: minutes for clean servers; human review only for some, queue-dependent).

## Where we stand today

Ready now:
- Worker live: `https://pick-my-costume-mcp.wdlcmu.workers.dev` (POST /mcp), verified: 3 tools, all read-only, no auth, Streamable HTTP. Matches the connector transport requirement.
- Tool names are 12–16 chars (policy cap is 64). Fine.
- Adversarial pass already proved: no stack traces, no prompt-injection behavior change, no hidden instructions (policy 2F/2G clean), no IP infringement (policy 1E clean — bank is trademark-free).
- Submission assets already staged from the ChatGPT prep: `privacy.md`, `terms.md`, icon (512 + 64), listing copy, 4 starter prompts, 5 positive + 3 negative test cases.

Still needed (see split below):
- **`title` on all three tools** — policy-required (Software Directory Policy 5E; the portal flags tools missing titles). Muse prep: add, rebuild, redeploy.
- **Publish privacy + terms to the worker** (`/privacy-policy` update, `/terms` new route) so the URLs the portal asks for are live.
- **Public icon URL** — the portal reads the MCP host's favicon by default and it 404s on a worker; a custom icon URL is needed. Muse prep: host the generated icon publicly.
- **Documentation URL** — community wisdom: it must be the MCP setup page, not the marketing page. Muse can draft a small `pickmycostume.com/mcp` page.
- **Billy's Claude plan/org eligibility** — official docs say "any paid Claude plan" can submit; community experience (Sep 2026) says the portal lived inside Team/Enterprise org admin settings with the submitter as Owner. Cheapest Team org is two seats, monthly — a real cost. Verify in-portal; Billy's call on spend.

## What Anthropic requires (official)

**Access.** Developer portal at `claude.ai/directory/manage`. Official docs (Sep 2026): "Anyone on a paid Claude plan can submit through the portal" — plan, role, and organization requirements are the same for connectors and plugins. Community-verified as of Sep 11, 2026: the submission portal appeared only inside a Team or Enterprise org where the submitter is Owner (a personal Max plan did not have it). **Treat this as verify-at-submission-time**: if the portal shows "Submit new", we're in; if it demands a Team org, that's a spend decision for Billy (two seats minimum).

**No domain challenge.** Unlike OpenAI, there is no `/.well-known/` token to host. The portal verifies by connecting to the server directly (Connection step: paste the `https://` URL, Universal URL, Connect). The URL slug for the listing page is **permanent once published** — choose `pick-my-costume` and never change the server URL afterward.

**No identity documents.** No individual/business ID verification like OpenAI. The Company step collects company name, website, and a primary contact for review updates — the paid-plan org is the identity anchor.

**The portal steps** (progress autosaves in the browser):
1. **Connection** — paste `https://pick-my-costume-mcp.wdlcmu.workers.dev/mcp`, Universal URL (same for everyone). Portal reads `tools/list` once here; tools/prompts/resources sync automatically. If we change tools later, reconnect/rescan or review runs against the old list.
2. **Tools** — auto-synced; flags any tool missing `title` or annotations. Ours will flag until titles are added.
3. **Listing** — server name (≤100 chars), one-liner (≤200 chars), description (≤2,000 chars), 1–5 categories, documentation URL, privacy policy URL, support contact, icon, permanent slug. The detail-card description is submitter-written; Anthropic can't edit it.
4. **Use cases** — primary use cases (community format: ~5 lines, each a use case with an example prompt in quotes), what users need before connecting (nothing — no account), and whether the connector reads data, writes data, or both. Ours: **reads only** (all three tools `readOnlyHint: true`).
5. **Company** — company name, website, primary contact name + email for review updates.
6. **Authentication** — OAuth 2.0 with dynamic client registration, client ID metadata documents, Anthropic-held credentials, custom connection, or **no authentication**. Official docs: "no authentication for public data" is explicitly supported. Ours: **none**.
7. **Data handling** — is the underlying API your own / proxied with permission / third-party you don't control; personal health data? sponsored content? Ours: **our own first-party API** (the 169-idea bank on our worker), no health data, no sponsored content.
8. **Test & launch** — test-account setup and access instructions detailed enough for a reviewer to connect and run the tools (for us: "no account needed; here are three prompts to try"), plus confirmation that **you ran every tool yourself** (via MCP Inspector or as a custom connector in Claude). The review account must keep working after approval — N/A for no-auth.
9. **Compliance** — seven required acknowledgments: directory guidelines read, first-party API, no financial transactions, no AI media generation, no prompt injection, no conversation-data collection, public docs by publish date. All clean for us.
10. **Review** — final read-through; quality warnings shown; Submit.

**After submit.** "Anthropic scans your submission automatically for policy compliance and, by default, lists it as a **Community connector** with no action from you. Some submissions also get a review from a person, and those review times vary with queue volume." Community data point (Sep 11, 2026): two clean submissions approved by the automated scan within minutes; a third was held in human review until a charging tool was removed. There is a **Community → Verified** upgrade path (docs: "Connector verification"), with Verified presumably requiring human review.

**Post-publish.** Tool renames/re-schemas change the scanned surface — expect re-review. Listing edits, reviewer feedback, and server health/usage metrics are managed in the portal. Escalations: `mcp-review@anthropic.com`.

**Policy hard lines that matter for us (Software Directory Policy):**
- 5E: every tool needs `title` + `readOnlyHint`/`destructiveHint` — titles missing today, must fix.
- 5C: tool names ≤ 64 chars — fine.
- 2A/2B: tool descriptions must be narrow, unambiguous, and match actual functionality — ours are; the adversarial pass confirmed no behavioral drift.
- 3E: at least three working example prompts — we have four starter prompts ready.
- 3F: must own/control the endpoint — Billy's Cloudflare account owns the worker. Fine.
- 4A–4C: no financial transactions, no AI media generation, no ads — clean.

## How this differs from the OpenAI submission (cheat sheet)

| | OpenAI plugins | Anthropic connectors |
|---|---|---|
| Portal | platform.openai.com submission portal | claude.ai/directory/manage → MCP connector |
| Cost to submit | Free org | Paid Claude plan (possibly Team org = 2 seats) |
| Identity | Verified individual/business ID (documents) | None — company name + contact in the form |
| Domain verification | Challenge token at `/.well-known/openai-apps-challenge` | None — portal connects to the server directly |
| Tool metadata | readOnlyHint/openWorldHint/destructiveHint | readOnlyHint/destructiveHint **+ required `title`** |
| Review | Human, unpublished timeline, expect weeks | Auto-scan → Community listing by default (minutes possible); human review for some |
| Test evidence | Paste 5 positive + 3 negative test cases | Test-account box + self-test confirmation |
| Auth for no-auth server | Fine, simplest path | Fine — "no authentication for public data" explicit |
| Where it appears | Universal Plugins Directory (ChatGPT + Codex) | Connectors Directory (Claude.ai, Desktop, Mobile, Code, Cowork) |
| Post-publish | Re-scans tools; listing changes need new version + review | Tool changes → reconnect, expect re-review; slug permanent |

## What we reuse from the ChatGPT prep (no rework)

- **privacy.md** → the privacy policy URL. Host at the worker (`/privacy-policy`) once published; the listing field just needs a live URL.
- **terms.md** → Anthropic's Listing step has no explicit terms field, but keep it live at `/terms` anyway (linked from the privacy policy; OpenAI still needs it).
- **Icon** (512 + 64 PNG) → the custom icon. Must be hosted at a public URL (worker favicon 404s).
- **Listing copy** → adapted to Anthropic caps below (one-liner ≤200, description ≤2000).
- **4 starter prompts** → the Use cases step (reformatted as use case + quoted prompt) and the ≥3 working examples the policy demands.
- **5 positive + 3 negative test cases** → become the self-test evidence for Test & launch (run every tool, record results) plus reviewer guidance in the test-account box.
- **Bio wording** (once Billy approves) → Company step / author fields.

## Muse can prep (reversible, no Billy taps)

1. **Add `title` to all three tools** in `src/mcp.mjs` (policy-required; portal flags missing titles): `pick_costume` → "Pick a costume"; `get_build_guide` → "Get a build guide"; `search_by_owning` → "Search by owned items". Then `npm run build` + redeploy the worker and re-verify `tools/list`.
2. **Publish privacy + terms to the worker**: replace `src/privacy.html` with the final privacy.md content, add a `/terms` route in `src/server.mjs` + `src/worker.mjs`, rebuild + redeploy, curl-verify both 200.
3. **Host the icon publicly** (e.g. on the worker or pickmycostume.com) and record the URL for the icon field.
4. **Draft a small MCP docs page** (`pickmycostume.com/mcp` or a worker route): what the connector does, the three tools, example prompts, support contact, privacy link. This is the Documentation URL the portal wants (setup page, not marketing).
5. **Write the 5 use-case lines** (use case + example prompt in quotes), adapted from the starter prompts plus one search-by-owning case.
6. **Self-test every tool** via MCP Inspector against the live worker and save the evidence (the 5 positive + 3 negative cases, adapted) for the Test & launch step.
7. **Assemble the portal answer sheet** (below) so the portal fill takes Billy ~15–20 minutes.
8. **Confirm the "who can submit" requirement** is still as documented — re-check the docs on submission day (the portal moved fast in Sep 2026).

## Draft listing copy (Billy approves before use)

- **Name:** Pick My Costume
- **Slug:** `pick-my-costume` (permanent once published — double-check spelling before submitting)
- **One-liner (≤200 chars):** Halloween costume ideas from stuff you already own, with step-by-step build guides. 2-minute quiz: 3 ideas, materials, and build steps.
- **Description (≤2000 chars):** Pick My Costume turns your closet into a costume shop. Tell it who the costume is for, the vibe you want, and how much effort you'll spend — or list household items you already have — and it recommends from 169 original, trademark-free costume ideas with materials lists, build steps, time estimates, and parent-tested safety notes. Three read-only tools: pick a costume from a 2-minute quiz, get the full build guide for any idea, or search by what you already own. No account, no login, no data collected. Every idea links to its full guide at pickmycostume.com.
- **Categories:** Lifestyle + (confirm available labels in the portal; community notes say up to 5, and there is no "Data" category — pick exact labels from the picker)
- **Documentation URL:** the MCP setup page from prep #4
- **Privacy policy URL:** `https://pick-my-costume-mcp.wdlcmu.workers.dev/privacy-policy`
- **Terms URL:** `https://pick-my-costume-mcp.wdlcmu.workers.dev/terms` (linked from privacy; not a portal field)
- **Support contact:** hello@pickmycostume.com
- **Icon:** public URL from prep #3
- **Company name:** "Pick My Costume" (Billy's call — individual, no company; alternatives: William Litner)
- **Company website:** https://pickmycostume.com
- **Primary contact:** William Litner, hello@pickmycostume.com

## Draft use cases (Use cases step)

1. A parent needs a last-minute toddler costume from a bedsheet: "I need a Halloween costume for my 3-year-old. I have a bedsheet and about 20 minutes."
2. Checking materials before committing: "What materials do I need for a ballerina costume?"
3. Couples brainstorming: "Give me 3 funny couples costume ideas, something easy."
4. Building from scrap: "What can I make with cardboard and tape?"
5. Step-by-step build night: "How do I make a ghost costume step by step?"

## Draft test-account box (Test & launch step)

"No account needed — the connector has no authentication and stores no user data. To verify: connect the server, then try: (1) 'I need a Halloween costume for my 3-year-old, I have a bedsheet' — expect classic-ghost as the top pick; (2) 'What materials do I need for a ballerina costume?' — expect a materials list with buy/own/make tags and numbered steps; (3) 'What can I make with cardboard and tape?' — expect results ranked by coverage of the owned items. All tools were self-tested via MCP Inspector against the production worker on [date]; evidence saved."

---

## Billy must tap himself (human-only, by design)

1. **Check submission eligibility.** Open `claude.ai/directory/manage` on his Claude account. If "Submit new" is there, we're clear on his current plan. If the portal demands a Team/Enterprise org, that's a **spend decision** (cheapest: two seats, monthly) — his call before anything else.
2. **Approve the listing packet**: icon, one-liner, description, use cases, and the company-name question ("Pick My Costume" vs his own name — he's an individual, no company).
3. **In the portal himself** (~15–20 min with the packet ready), in a normal browser:
   a. Submit new → **MCP connector**.
   b. Connection: paste `https://pick-my-costume-mcp.wdlcmu.workers.dev/mcp`, Universal URL, Connect. Confirm 3 tools sync with titles and read-only annotations.
   c. Listing: paste the approved copy, URLs, icon, slug `pick-my-costume`.
   d. Use cases: paste the 5 use cases; reads-data-only; "no account needed" for connection requirements.
   e. Company: approved name + pickmycostume.com + William Litner / hello@pickmycostume.com.
   f. Authentication: **no authentication**.
   g. Data handling: own first-party API; no health data; no sponsored content.
   h. Test & launch: paste the test-account box; tick the self-test confirmation only if true.
   i. Compliance: read and tick all seven acknowledgments honestly.
   j. Review: read the final check, **Submit**.
4. **After the scan**: by default it lists as a Community connector automatically. Watch the portal for status/reviewer feedback; a human review may follow for Verified status.
5. **Keep the worker URL and tool surface stable** afterward — tool renames/re-schemas trigger re-review, and the slug can never change.

## Bot-flagging risk (Billy asked)

Risk is low if Billy does the portal taps himself in a normal browser. What to avoid:
- Don't let an automated agent click through the developer portal — same rule as OpenAI. Portal automation on claude.ai is the one thing that could get the account flagged.
- Don't create extra Claude orgs or duplicate connector submissions to game review — one connector, one org.
- The `title` fix and doc pages are normal code deploys on his own Cloudflare account — no flag risk.

## Rejection risks to watch

- **Tools missing `title`** — the portal flags this; fixed in Muse-prep #1.
- **Tool descriptions that read as instructions to the model** ("always call X first") — policy treats this as prompt injection. Ours are descriptive; the adversarial pass confirmed no behavioral drift. Keep them that way.
- **Privacy policy doesn't match reality** — must say: no accounts, no data collected, queries not stored. The final privacy.md says exactly that.
- **Documentation URL is the marketing page** — community reports this gets flagged; the setup page (prep #4) fixes it.
- **Slug typo** — permanent once published. Triple-check `pick-my-costume`.
- **Changing tools after connecting** — reconnect/rescan before submitting, or review runs against the old list.

## Which path first: OpenAI or Anthropic?

They're independent and can run in parallel. Anthropic's auto-scan may list us as a Community connector within minutes of submission (for a clean read-only server), while OpenAI's human review is expected to take weeks. If Billy wants a fast win, Anthropic first is the better bet — but only after the `title` fix is deployed, and only if his Claude plan shows the "Submit new" portal without buying a Team org.

## Sources

- Official connector submission flow: https://claude.com/docs/connectors/building/submission
- Official plugin submission flow (for the bundle path we are NOT taking): https://claude.com/docs/plugins/submit
- Official connector review criteria (referenced by the docs; read alongside): https://claude.com/docs/connectors/building/review-criteria
- Official Software Directory Policy: https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy
- Official Software Directory Terms: https://support.claude.com/en/articles/13145338-anthropic-software-directory-terms
- Connector verification (Community → Verified): https://claude.com/docs/connectors/directory/verification
- Remote MCP submission guide: https://support.claude.com/en/articles/12922490-remote-mcp-server-submission-guide
- Community submission notes (Sep 2026, three connectors submitted, two auto-approved in minutes): https://github.com/tarasshyn/skills/blob/HEAD/skills/mcp-directory-submission/references/claude-directory.md
- Eleven-step field table: https://github.com/vibetechnologies/vibe-mcp/blob/HEAD/worklog/anthropic-submission-pack.md
- Two-track (plugin vs connector) comparison: https://github.com/contentrain/studio/blob/HEAD/docs/REMOTE_MCP_SUBMISSION.md
- New plugins portal (opened Sep 25, 2026): https://www.unite.ai/anthropic-opens-directory-submission-portal-for-claude-plugins/
