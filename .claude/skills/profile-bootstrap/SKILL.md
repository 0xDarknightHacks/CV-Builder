---
name: profile-bootstrap
description: First-time setup. Builds profile/master.md and profile/base_cv.json from the resume and notes in profile/source/. Use when the profile still contains template placeholders, or when the user asks to set up or rebuild their profile from a resume.
---
# Profile bootstrap

1. Read every file in `profile/source/` once (resume PDF/DOCX, LinkedIn export, notes). Read the templates `profile/master.md` and `profile/base_cv.json` for the exact format.
2. Ask the user **one message** with at most 10 short questions, only for what the sources don't answer: target headline and roles · location, relocation, remote · work authorization / visa sponsorship · notice period · certifications held · confidential clients or projects · tools or certifications to never claim · clients that must always appear · role families or required languages to avoid · missing numbers worth adding. Wait for answers.
3. Write `profile/master.md` in the template's structure:
   - one `### F-<AREA>-<NN> · title` block per distinct achievement (AREA = short employer/project code);
   - `confidence: verified` only for what the resume or user states; anything inferred = `pending`;
   - a `cv:` line per fact (approved bullet wording, varied action verbs, no pronouns);
   - Confidential, Do-not-claim and Clients terms each wrapped in backticks;
   - never invent numbers, tools, clients or certifications.
4. Write `profile/base_cv.json` (same schema as the template): `file_stem` = `First_Last_Resume`; company line first with the official title; every bullet cites fact IDs; projects use a start year only; skills grouped by capability; summary = two plain lines about how the person works.
5. `python cvbuild.py build profile/base_cv.json --out applications/_master` → fix every FAIL (cut content instead of shrinking; trim orphans; keep all clients) until PASS.
6. Check no placeholders remain (`<`, `FIRST LAST`, `First_Last`, `example.com`, `F-EXAMPLE`). Add a Changelog line.
7. Reply with: number of facts, list of `pending` facts the user must confirm, build result.
