# CV Builder

Turns a job link into an honest fit verdict and, if it's a match, a tailored one-page CV (PDF + Word), a cover letter, a motivation email and an interview prep sheet. Everything comes from one profile file you maintain, and every claim is traceable to a fact in it.

## Setup (≈5 minutes)
1. Install Python 3.9+ and the Claude Code extension for VS Code (or the Claude Code CLI).
2. Open this folder in VS Code, then in a terminal:
   ```
   python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   python cvbuild.py build profile/base_cv.json --out applications/_master
   ```
   You should see `PASS`. Optional: install LibreOffice so the build can also verify the Word file stays on one page.
3. Personalize the profile: either the one-time chat setup described in `RECIPIENT_GUIDE.md`, or put your resume in `profile/source/` and ask Claude Code to "set up my profile" (profile-bootstrap skill). Fit verdicts rely on `## Constraints`, so fill it carefully.

## Daily use (in Claude Code)
- `apply https://…job-link…` → intake, fit verdict, then it stops and asks you before writing anything.
- After you confirm → tailored CV + cover letter + email + interview prep in `applications/<date>_<company>_<role>/`.
- LinkedIn or other login-walled postings: paste the description directly after `apply` — include the job card header line (title · company · location · work mode), which the description itself does not contain. Saving the page as HTML also works.
- `I finished a new mission …` → profile-maintainer interviews you briefly and adds a fact to `master.md`.
- Start each application with `/clear` (see TOKEN_EFFICIENCY.md).

## Files
```
CLAUDE.md               pipeline + hard rules (always loaded, kept short)
TOKEN_EFFICIENCY.md     token rules (imported by CLAUDE.md)
SETUP_AND_TEST.md       step-by-step setup and first test
cvbuild.py              the builder: facts | fact | fetch | build | ats | letter | diff
profile/master.md       single source of truth (facts, confidential, do-not-claim, education…)
profile/source/         your resume and notes (input for profile setup)
profile/base_cv.json    your approved master CV content (inline: **bold**, *italic*, [text](url))
.claude/skills/         profile-bootstrap, profile-maintainer, job-intake, fit-assessor, cv-tailor,
                        application-writer, interview-prep
.claude/settings.json   allows cvbuild commands, blocks reading binaries/fonts
fonts/                  Carlito (metric-compatible with Calibri, SIL OFL 1.1)
applications/           one folder per application (posting, fit, cv.json, PDF, DOCX, letters, prep)
tracker.csv             one row per application
```

## What `build` checks (exit code 1 on any FAIL)
- one A4 page (PDF, and DOCX when LibreOffice is installed)
- body font ≥ 9.5 pt: it cuts content instead of shrinking text
- no orphan lines (last line of a bullet under 18% of the width)
- every experience/project bullet cites existing fact IDs
- no `Confidential` or `Do-not-claim` terms anywhere
- projects use a start year only (no "Present" ranges that parsers mistake for jobs)
- every client listed in `master.md → ## Clients` is still present
- every number in a bullet appears in the facts it cites (summary/skills: anywhere in master.md); job titles equal `Official title:` in master.md
- style warnings (not blocking): personal pronouns, weak openers ("responsible for", "helped"), vague words ("various", "etc."), the same lead verb more than twice; English and French rules

French CVs: set `"lang": "fr"` in a cv.json for French headings (PROFIL, EXPÉRIENCE PROFESSIONNELLE…) and French punctuation; cv-tailor produces `cv.fr.json` automatically for French postings.

`fetch` also appends auto-extracted contacts (emails, hiring team, "apply via portal" hints). The application writer turns them into `contact.md` (channel, address, source, confidence) and `letter` validates it and writes a ready `mailto:` link (attachments must be added manually).

`fetch` also appends advisory signals: years required (only required, overall figures gate), contract terms (B2B, contractor, CDI/CDD…), salary figure, posting age.

`letter` also fails on numbers not found in master.md or the posting (letter, email, answers.md), checks answers.md for forbidden terms, and warns on stock AI phrasing.

`letter` renders the cover letter to PDF + DOCX (one page, 200–360 words) and checks `email.md` (≤ 140 words) for forbidden terms. `diff` lists every change versus `base_cv.json` for a quick review before sending.

## Maintaining and extending
- Profile changes: edit `master.md` directly or via profile-maintainer; keep IDs stable and add a Changelog line. Once you earn a certification, remove it from `## Do-not-claim`.
- Master CV changes: edit `profile/base_cv.json`, then rebuild it.
- Layout tuning: the `CFG` block at the top of `cvbuild.py` (font range, margins, colours, orphan threshold).
- New output type: add one skill folder with a short `SKILL.md`; keep CLAUDE.md unchanged unless the pipeline changes.
- Use Git: every profile and CV change becomes a reviewable diff.

## Notes
- Data location: `cvbuild.py` uses `$CVBUILD_HOME` if set, else the current folder when it contains `profile/master.md`, else its own folder.
- Fonts: bundled Carlito (metric-compatible with Calibri); falls back to an installed Carlito or Calibri, then Helvetica with a warning.
- Keyword coverage from `ats` is a heuristic, not a real ATS score.
- Fit thresholds (GO ≥ 65%, BORDERLINE 50–64%) live in `fit-assessor/SKILL.md`. Adjust to taste.
- Always review documents before sending; the tools enforce truthfulness and layout, not judgment.
