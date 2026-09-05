# Conference demo direction

## Primary surface

Keep the existing single-page browser demo as the primary surface. Do not split the
story across a dashboard, benchmark page, or simulated second app.

## Audience

Technical conference attendees evaluating whether an agent memory layer can make a
later engineering task start with the right context. They need to see the product
boundary, the observable benefit, and which parts are real without reading the
implementation.

## Short story (3–5 minutes)

1. Start a fresh private demo scope and show the intentional empty BEFORE state.
2. Capture three clearly labeled, browser-supplied example memories (decision,
   convention, fact) through the real Vault engine.
3. Show capture progress and the actual failure boundary if any write fails.
4. Repeat the task query and show only the relevant returned subset, including what
   was left out.
5. Prepare the bounded, selectable context block and show how many saved memories
   it actually contains.
6. Explain the result in user language: the next task can start with the relevant
   past instead of rediscovering it. Reset and replay the story before the next run.

## Reality boundary

- **Real:** `app.py` calls the deployed `perseus-vault` binary for remember, recall,
  context, and feedback operations. The public flow is browser-scoped and uses the
  hosted wrapper.
- **Seeded/illustrative:** the example query and three memory texts live in
  `index.html` and are supplied by the browser story. They are not customer data.
- **Not demonstrated:** no LLM call, agent action, provider-billed event, customer
  outcome, or benchmark result. Optional Ledger evidence is a separate, scoped
  inspection path.

## Current boundary and risk

Source of truth: `Perseus-Computing-LLC/perseus-vault-demo`, `origin/main` at
`327e325`. Deployment ownership is the Portainer stack described by
`docker-compose.yml`; the public artifact is `https://vault-demo.perseus.observer/`.
The live root matches the checked-in page apart from Cloudflare-injected scripts;
`/healthz` reports hosted runtime Vault `2.22.0` with `source_revision: main`.

The highest-impact credibility risk is a false USE success: Vault's context API can
return a non-empty generic markdown block with `entities_injected: 0`. The current
browser code accepts any non-empty text, so a summary can look ready even when no
saved memory reached it.

The source tree can be exercised locally with a real Vault binary, but the available
standalone binaries reject fresh-demo writes as non-serveable without the deployed
runtime's authority/bootstrap state. The successful remember → recall → context
path was therefore verified against the current public service before editing; the
local source path was still exercised for empty, reset, error, and bounded-context
responses without claiming a local success run.

## Focused slice and acceptance criteria

Make USE fail closed unless the real context response reports at least one injected
memory. Show the actual injected-memory count beside the character count and carry
that count into the final success state. Preserve the current reset, empty, error,
responsive, and claim-safe boundaries.

Acceptance:

- a zero-memory context response cannot produce a successful USE phase or final
  story success;
- a successful story shows `N memories included` from the context response, not the
  recall count alone;
- the bounded context remains selectable/copyable and still shows its character cap;
- reset clears the injected-memory count and visible result;
- existing tests remain green and new static contracts cover the fail-closed rule.
