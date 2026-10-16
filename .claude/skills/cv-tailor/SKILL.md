---
name: cv-tailor
description: Build a tailored one-page CV (PDF + DOCX) for an assessed job from profile/base_cv.json and master.md facts, then pass all automated checks. Use after fit-assessor when the user approves.
---
# CV tailor

1. Copy `profile/base_cv.json` to `<folder>/cv.json`; set `"target"` and set `file_stem` to `<First>_<Last>_<Role>_Resume` (name from master.md → Identity).
2. Edit with targeted changes only, guided by fit.md:
   - Reorder bullets so the strongest matches come first; swap in evidence-bank facts when they match a must-have.
   - Reuse the posting's exact wording only where the cited fact supports it. Never add a skill, tool, metric or client that is not in master.md.
   - Every experience/project bullet keeps `"facts": [...]`.
   - Summary: human, plain, ≤ 2 lines, no tech list, no self-praise. Adapt at most one phrase to the role.
3. Build: `python cvbuild.py build <folder>/cv.json`. Read only its printed output; never open the PDF/DOCX.
4. Fix every FAIL, then rebuild (max 4 iterations):
   - font below floor → remove the least relevant bullet or shorten lines; never shrink further
   - orphan line → trim 5–15 characters in that bullet (drop filler, not facts)
   - confidential / do-not-claim term → remove it
   - client dropped → restore it; if space is tight, merge clients into one compact bullet (e.g. the "Executed production Microsoft changes" format)
5. Optional keyword check: `python cvbuild.py ats <folder>/<stem>.pdf --keywords "<keywords from posting.md>"`; add missing terms only if a fact supports them.
6. Review: `python cvbuild.py diff <folder>/cv.json` — confirm every change is intended.
7. Reply: one line with PASS, font size, and the 3 most important changes.

House rules (learned from real reviews and ATS tests):
- Keep every named client from `## Clients` (enforced by build).
- Company line first, title on the next line (prevents ATS such as Workday mis-parsing titles that start with a famous brand).
- Projects show a start year only — never a date range or "Present".
- Official job titles stay exactly as recorded in master.md; the headline under the name may differ.
- Skills are capability-led; no domain tagline under the name.
- Vary verbs; no personal pronouns; no "passionate", "results-driven", "proven".
- Left-aligned text, body 9.5–10 pt, one page, no orphan lines.
