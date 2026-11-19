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
   - **Domain context:** when a fact has `domain:` and the posting's sector or scale matches (e.g. banking, insurance, regulated industry), weave it in ("for a regulated retail bank, …"). Never add domain details that are not in the fact.
   - Rewrites follow XYZ: action + what + context + measurable result; keep the fact's numbers exactly.
   - Summary: human, plain, ≤ 2 lines, no tech list, no self-praise. Adapt at most one phrase to the role.
3. Build: `python cvbuild.py build <folder>/cv.json`. Read only its printed output; never open the PDF/DOCX.
4. Fix every FAIL, then rebuild (max 4 iterations):
   - font below floor → remove the least relevant bullet or shorten lines; never shrink further
   - orphan line → trim 5–15 characters in that bullet (drop filler, not facts)
   - confidential / do-not-claim term → remove it
   - `WARN style:` (pronoun, weak opener, vague wording, repeated lead verb) → fix all of them; they are recruiter red flags even though the build passes
   - client dropped → restore it; if space is tight, merge clients into one compact bullet (e.g. the "Executed production Microsoft changes" format)
5. Optional keyword check: `python cvbuild.py ats <folder>/<stem>.pdf --keywords "<keywords from posting.md>"`; add missing terms only if a fact supports them.
5b. **French CV** (posting written in French, or user asks): after the English CV passes, copy `cv.json` to `cv.fr.json`, set `"lang": "fr"` and `file_stem` + `_FR`, and adapt every text naturally (not word-for-word): French headline, summary, bullets, skills, dates ("févr. 2025 – Présent"), degree names as recognised in French ("Diplôme national d'ingénieur…"). Keep fact IDs, numbers, product names and client names unchanged. Build it the same way until PASS.
6. Review: `python cvbuild.py diff <folder>/cv.json` — confirm every change is intended.
7. Reply: one line with PASS, font size, and the 3 most important changes.

House rules (learned from real reviews and ATS tests):
- Keep every named client from `## Clients` (enforced by build).
- Numbers: every number in a bullet must appear in the facts it cites; numbers in the summary/skills must exist in master.md. Job titles must equal `Official title:` in master.md. Both are enforced by build.
- Company line first, title on the next line (prevents Workday mis-parsing "Microsoft …" titles).
- Projects show a start year only — never a date range or "Present".
- Official job title stays "Microsoft Security Consultant"; headline may differ.
- Skills are capability-led; no domain tagline under the name.
- Vary verbs; no personal pronouns; no "passionate", "results-driven", "proven".
- Left-aligned text, body 9.5–10 pt, one page, no orphan lines.
