---
name: interview-prep
description: Produce a concise interview preparation sheet for an assessed job, with likely questions, STAR stories from real facts, gap-handling answers and curated learning resources. Use when the user asks to prepare for an interview or after application documents are done.
---
# Interview prep

Inputs: `<folder>/fit.md` and the facts it cites. Do not re-read the posting in full.

Write `<folder>/interview-prep.md` (max ~80 lines):
1. **Likely questions** (8–10): mix technical (from must-haves) and behavioural (consulting, production change, conflict, handover).
2. **STAR stories** (3–4): each built from one fact ID; Situation, Task, Action, Result in 4 short lines; respect confidentiality (anonymise clients listed under `## Confidential` in master.md). Use only details present in the fact; where context is missing, write `[add context]` instead of inventing it. If a cited fact still contains `TODO` or `pending` in master.md, add `[fill F-ID in master.md before the interview]` next to it.
3. **Gap answers** (for each gap / partial in fit.md): honest framing in the user's voice. State only actions that exist in master.md. Anything the user *could* do to close the gap goes on a separate line starting `[suggestion – confirm]`. Never imply experience that is in Do-not-claim.
4. **Resources** (max 8, prioritised): prefer official sources (Microsoft Learn modules and docs, vendor docs, the company's own engineering blog). Use at most 2 web searches; include the URL and a one-line reason. If unsure a link exists, say "search: <title>" instead of guessing a URL.
5. **Questions to ask them** (3): about the team, delivery model, and success in the first 90 days.

Reply with the file path only.
