---
name: application-writer
description: Write a tailored cover letter and a short motivation email for an assessed job, grounded only in master.md facts. Use after the CV passes checks, or when the user asks for a cover letter or application email.
---
# Application writer

Inputs: `<folder>/posting.md` (Extracted), `<folder>/fit.md`, and only the facts cited there (`python cvbuild.py fact <IDs>`).

## cover-letter.md (250–330 words, 4 short paragraphs)
1. Why this role and this company: one specific, verifiable detail from the posting. No flattery.
2. Most relevant evidence: two facts that match must-haves, with one number each if available.
3. How the user works: client collaboration, careful production change, clear handover (only what facts support).
4. Practical close: availability, relocation / remote, languages; polite request for a conversation.
Address the hiring manager by name only if the posting names one, otherwise "Dear Hiring Team".

## email.md (≤ 140 words)
`Subject: Application – <Role> – <Full name from master.md>`, three short paragraphs, mention attached CV and cover letter, sign-off with phone + LinkedIn.

## contact.md (always written; decides how to send)
Sources, in order. Stop at the first that gives a recruiting channel:
1. `## Contacts (auto-extracted)` in posting.md (emails, hiring team, hints).
2. Only if none: at most **2 web searches restricted to the company domain** (`site:<domain> careers OR jobs OR recrutement OR contact`) and **1 fetch** of the best result.
Allowed: the posting, the company's own careers/recruitment or contact page. Not allowed: third-party email finders, guessed patterns (`first.last@…`), personal addresses that are not published for recruiting.

Channel rules:
- Posting says apply via portal/ATS → `portal`; if an email is also published → `portal+follow-up` (email only after applying).
- Published recruiting address and no portal-only rule → `email`.
- Only a recruiter name → `linkedin-message` (no address).
```
channel: email | portal | portal+follow-up | linkedin-message
to: <address or —>
name: <recruiter name or —>
domain: <company website domain, e.g. example.com>
source: posting | <URL on the company domain> | none   (no address → `none` or the URL that was checked)
confidence: posting | official-hr | general-contact | none
checked: YYYY-MM-DD
notes: <one line, e.g. "apply via Workday first, then follow up">
```
If `to:` has an address, start email.md with `To: <address>` above the `Subject:` line. For `portal+follow-up`, phrase email.md as a short follow-up ("I have applied via your portal…").

## answers.md (form answers for ATS portals, ≤ 25 lines)
Ready-to-paste answers built only from master.md `## Identity` and `## Constraints`: work authorization / visa sponsorship · notice period / start date · location & relocation · remote preference · languages · certifications (only those held) · "Why this company?" (2–3 sentences from the posting) · salary expectation as `[fill in]` (never invent one).

## Tone rules
Professional, respectful, modest. No stock AI phrasing ("I am thrilled to", "leverage", "fast-paced", "passionate about", "proven track record", "delve", "seamless", "in today's…"); at most two em-dashes per document. Every number must come from master.md or the posting (the `letter` command fails otherwise). No superlatives, no claims of being "the perfect fit", no repeated CV bullets verbatim, no pronoun-heavy storytelling. Write in the posting's language if it is French; otherwise English. If a French CV (`*_FR.pdf`) was built, the French letter and email refer to it as the attachment.
Never mention confidential or do-not-claim items (see master.md sections).
Render and check (letter, email, answers, contact): `python cvbuild.py letter <folder>/cover-letter.md --cv <folder>/cv.json` (PDF + DOCX of the letter; checks email.md and contact.md; writes a ready `mailto:` link into contact.md). Fix any FAIL.
Reply with the file paths only.
