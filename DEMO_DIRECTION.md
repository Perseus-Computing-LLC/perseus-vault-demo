# Perseus Vault conference demo direction

## Primary surface

This is an **Operate** surface with a short **Explore** layer: the visitor watches a
real memory workflow change state, then can inspect the bounded result. It is not a
generic marketing landing page and it is not a benchmark dashboard.

## Audience

Technical conference attendees, engineering leaders, and agent builders deciding
whether durable memory can prevent repeated discovery work. The page must read from
the back of a room: one promise, one live transformation, one honest boundary.

## 3–5 minute story

1. Start in a fresh browser-scoped demo scope.
2. Show the honest BEFORE state: zero relevant memories.
3. Run one guided scenario that captures three clearly labeled illustrative
   decisions/conventions/facts through the real Vault service.
4. Show actual progress and stop visibly on any failed child operation.
5. Ask the later-task question and show only the relevant subset, including what was
   left out.
6. Prepare the bounded context block and show the exact included-memory count and
   character cap.
7. Translate the result: the next task can begin with the relevant past instead of
   re-deriving it.
8. Open the run observation, copy it if useful, reset, and replay.

## Surface decisions

- The first viewport is an outcome-first BEFORE → AFTER stage, not a feature grid.
- The live proof console keeps the four beats visible: START, SAVE, FIND, USE.
- Secondary measurement, provenance, and support explanations are collapsed below
  the proof so they do not compete with the conference narrative.
- Presentation mode increases projection contrast and type, hides secondary content,
  preserves the live proof, and can be toggled from the header or with `P`.
- The final observation is explicitly bounded: it is inspectable demo evidence, not
  a production audit receipt.

## Reality boundary

- **Real:** `app.py` invokes the deployed `perseus-vault` binary for remember,
  recall, context, and feedback operations. The source UI was exercised through a
  local same-origin QA proxy forwarding API calls to the live service.
- **Seeded/illustrative:** the example query and three memory texts in `index.html`
  are browser-supplied story inputs. They are not customer data.
- **Not demonstrated:** no LLM call, agent action, customer outcome, provider-billed
  event, provider savings, benchmark result, or production audit receipt.

## Credibility and failure contract

- A non-empty generic context block is not enough for success. USE requires the
  real response to report at least one `entities_injected` memory.
- The hero BEFORE state remains `0 relevant memories · empty by design` after the
  run; it does not rewrite history with the post-capture count.
- Reset clears visible captures, context, receipt, counts, and the opaque session.
- The run observation reports the actual captured, selected, omitted, included, and
  bounded values, plus the real-vs-illustrative boundary.
- No metric or receipt is presented as a customer result.

## Source and live boundary

Canonical source: `Perseus-Computing-LLC/perseus-vault-demo`, local branch
`demo/conference-observable-proof`. Deployment ownership remains the Portainer stack
specified by `docker-compose.yml`; no deployment, push, or PR is part of this pass.
The public URL is `https://vault-demo.perseus.observer/`.

The public service was exercised with a real browser before and after the source
work through a local QA proxy. The live runtime remains the prior deployed source;
the new conference surface is not claimed live until an authorized deployment and
fresh public verification occur.

## Acceptance criteria

- The first viewport is readable at 1440×900 and has no CTA overlap.
- Idle state says what happens next and visibly starts empty.
- Guided run reaches success only after real BEFORE → SAVE → FIND → USE responses.
- Success shows a relevant subset, omitted memory language, bounded context metadata,
  and an inspectable observation artifact.
- Receipt copy feedback works or states that manual selection is available.
- Reset, invalid query, repeated run, projector mode, and narrow layout are tested.
- Inline JavaScript parses, static contracts pass, and the browser path has no page
  errors through the local-source/live-API QA proxy.

## Anti-slop check

Current composition scores **2/10** on the design slop checklist: the page retains a
technical dark palette and a small run-fact strip, but it removes the generic feature
wall, collapses secondary proof, commits to one live Operate surface, and makes the
observable outcome the visual endpoint.
