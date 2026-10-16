---
name: fit-assessor
description: Score a candidate's fit against an extracted job posting, flag blockers, and give a go / borderline / no-go verdict with matches and gaps. Use after job-intake and before tailoring any CV.
---
# Fit assessor

Inputs: `<folder>/posting.md` (Extracted section only) and the profile via `python cvbuild.py facts --grep <term>` / `fact <ID>`. Do not read master.md in full.

## Rating each requirement
- match = 1.0 · direct verified evidence of the same activity (cite fact IDs)
- partial = 0.5 · related or narrower evidence, or `exposure` confidence
- learnable = 0.25 · adjacent skill, plausible to close in weeks
- gap = 0 · no evidence
Evidence rules:
- A fact whose entry still contains `TODO` or `pending` counts as **partial at most**.
- Cite a fact only for the activity it describes (a Defender for Identity workshop is not AD design).
- Generic soft requirements (communication, mindset, "follows evolutions") are rated but marked `soft`.
- **Language requirements are eligibility, not skills:** list them under Blockers (met / soft / hard) and leave them out of the score.

## Weights
- **core** ×3: must-haves that define the role's stated focus (title, "clear focus on…", first responsibilities). Mark 3–5 requirements as core.
- must-have ×2 · nice-to-have ×1 · `soft` requirements ×1 whatever their label.
Score = weighted sum / max × 100.

## Blockers (reported separately, never averaged in)
Language the user lacks, location / work permit, mandatory certification not held, clearance, years of experience far above the profile, role family excluded in `## Constraints` (e.g. SOC/SIEM-centred).

## Verdict
- GO: score ≥ 65, no blockers, and no core requirement rated gap/learnable
- BORDERLINE: 50–64; or ≥ 65 with a soft blocker; or **2+ core requirements rated gap/learnable (cap)**
- NO-GO: < 50, any hard blocker, or 3+ core requirements rated gap
(Threshold can be changed by the user; record it in fit.md.)

## Output: `<folder>/fit.md` (max ~45 lines)
```
# Fit: <role> @ <company> — <VERDICT> (<score>%)
Blockers: …
| Requirement | Core/Must/Nice/Soft | Rating | Evidence (fact IDs) |
Strengths to lead with: 3 bullets
Gaps to address honestly: 3 bullets (what to say in interview)
Recommended CV emphasis: which facts to move up / swap in from the evidence bank
```
Then STOP and ask the user: "Proceed with CV, cover letter, email and interview prep?" Never generate documents for NO-GO unless the user explicitly overrides.
Append a row to `tracker.csv`: date,company,role,score,verdict,status=assessed,folder,channel (leave channel empty).
