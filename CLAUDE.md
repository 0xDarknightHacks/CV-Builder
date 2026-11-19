# CV Builder

Truthful, tailored job applications from one profile. Python 3.9+, run from repo root.

## Pipeline: user says "apply <url>"
1. job-intake → `applications/<date>_<company>_<role>/posting.md`
2. fit-assessor → `fit.md` + tracker row → **stop and ask** before continuing
3. cv-tailor → `cv.json` → `python cvbuild.py build …` must print PASS
4. application-writer → `cover-letter.md`, `email.md`, `contact.md`, `answers.md` → `cvbuild.py letter …` must print PASS
5. interview-prep → `interview-prep.md`
6. Update the tracker row (status `documents-ready`, channel from contact.md) and write `summary.md` (≤ 6 lines: verdict + score, how to send, files, open questions, any build WARN such as an unverified DOCX page count, and TODO facts cited).
New mission / achievement / correction → profile-maintainer. First-time setup (empty profile) → profile-bootstrap.

## Commands
- `python cvbuild.py facts [--grep X]` · `fact <ID…>` — profile lookup (use instead of reading master.md)
- `python cvbuild.py fetch <url|file> --out <path>` — clean posting markdown
- `python cvbuild.py build <cv.json>` — PDF + DOCX + checks (exit 1 = fix FAILs)
- `python cvbuild.py ats <pdf> --keywords "a,b"` — literal keyword coverage
- `python cvbuild.py letter <cover-letter.md> --cv <cv.json>` — letter PDF + DOCX, checks letter + email
- `python cvbuild.py diff <cv.json>` — changes versus base_cv.json

## Hard rules
- Facts only from `profile/master.md`; every CV bullet cites fact IDs. Never invent tools, numbers, clients or certifications.
- Respect `## Confidential`, `## Do-not-claim` and `## Clients` in master.md (enforced by build/letter).
- `profile/base_cv.json` is the approved master CV: edit copies, change the master only when the user asks.
- Never open PDF/DOCX/fonts; trust `build` output.
- Contacts: only addresses published by the company or in the posting; never guess emails; respect "apply via portal" instructions.

## When compacting, preserve
current application folder, verdict + score, open FAILs, decisions made, next step.

@TOKEN_EFFICIENCY.md
