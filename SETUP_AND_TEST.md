# Setup & Test (≈10 minutes)

Assumes: kit extracted, folder opened in VS Code, Claude Code extension installed.

## 1. Python environment
Open a VS Code terminal in the `cv-builder` folder:

```bash
python --version                      # needs 3.9+ (Windows: py --version)
python -m venv .venv
source .venv/bin/activate             # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
If PowerShell blocks activation: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then retry.

## 2. Smoke test the builder (no Claude needed)
```bash
python cvbuild.py build profile/base_cv.json --out applications/_master
```
Expected last line: `PASS`. Open `applications/_master/*.pdf` and `*.docx`; they should match your current CV.
`WARN DOCX page count not checked` only means LibreOffice isn't installed (optional).

```bash
python cvbuild.py facts                    # lists your fact IDs
python cvbuild.py fact <any ID from the list>   # prints one fact block
```

## 3. Safety-check test (should FAIL on purpose)
Copy the master CV, add a forbidden term, build:
```bash
cp profile/base_cv.json /tmp/test.json     # Windows: copy profile\base_cv.json %TEMP%\test.json
```
Edit `/tmp/test.json`: append one term from your `## Do-not-claim` section (master.md) to any skills line. Then:
```bash
python cvbuild.py build /tmp/test.json --out /tmp/test-out
```
Expected: `FAIL Do-not-claim term used: <term>`. The guardrails work.

## 4. First run in Claude Code
1. Open the Claude Code panel. Run `/permissions` and confirm the `cvbuild.py` allow rules and binary deny rules from `.claude/settings.json` are listed.
2. Type `/clear`, then: `apply <job posting URL>` (a role you know well is best for a first test).
   - LinkedIn or login-walled page: save it as HTML (Ctrl+S) into the project and use `apply ./saved-page.html`.
3. Expect, in order:
   - `applications/<date>_<company>_<role>/posting.md` with an `## Extracted` section
   - `fit.md` with a score, verdict, blockers (visa sponsorship is applied automatically) and a **question asking you to proceed**
4. Answer `yes`. Expect `cv.json`, the PDF + DOCX (build prints `PASS`), `cover-letter.md`, `email.md`, `interview-prep.md`, and a row in `tracker.csv`.
5. Review everything before sending. Check `/context` once to see the token footprint.

## 5. Profile update test
Type: `I want to add a new achievement` → profile-maintainer should ask ≤5 questions, show the new fact block, and edit `profile/master.md` only after you approve.

## Troubleshooting
| Symptom | Fix |
|---|---|
| `ModuleNotFoundError` | venv not active, rerun step 1 activation + `pip install -r requirements.txt` |
| `fetch` fails / empty posting | site blocks scripts: save page as HTML or paste text into `posting.txt` |
| `FAIL font … below floor` | content too long: let Claude cut the least relevant bullet (never lower the floor) |
| Skills not triggering | ensure VS Code opened the `cv-builder` folder itself (where `CLAUDE.md` lives) |
| Claude uses `python3` vs `python` | both are allowed in settings; on Windows use `python` |
