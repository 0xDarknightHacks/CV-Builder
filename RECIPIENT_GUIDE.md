# CV Builder: getting started

You receive: `cv-builder.zip` and `CLAUDE_SETUP_PROMPT.md`.

## Step 1: Personalise (Claude chat, ~10 minutes)
1. In Claude settings, turn on **Code execution and file creation**.
2. Open a new chat. Attach `cv-builder.zip` and your current resume (PDF or DOCX; a LinkedIn "Save to PDF" export also works).
3. Paste the full text of `CLAUDE_SETUP_PROMPT.md` and send it.
4. Answer Claude's questions (about 10, in one message), especially work authorization, confidential clients and things you must never claim.
5. Download `cv-builder-<first>-<last>.zip`. Review the master CV PDF and confirm the facts listed as `pending`.

## Step 2: Install (your computer, ~10 minutes)
1. Install Python 3.9+, VS Code and the **Claude Code** extension. Optional but recommended: LibreOffice (enables the Word one-page check; Windows: `winget install --id TheDocumentFoundation.LibreOffice -e`).
2. Unzip your personalised ZIP, then open the `cv-builder` folder in VS Code.
3. In the VS Code terminal:
   ```
   python -m venv .venv
   .venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   python cvbuild.py build profile/base_cv.json --out applications/_master
   ```
   Expect `PASS`. Then follow `SETUP_AND_TEST.md` for a full test.
4. Recommended: `git init && git add -A && git commit -m "My profile"` (your profile history).

## Step 3: Use it (Claude Code panel)
- `/clear`, then `apply <job URL>`, or `apply` followed by the pasted description **including the card header line (title · company · location · work mode)**. LinkedIn links can't be read automatically, so paste the text.
- Claude scores the fit and **stops to ask you** before writing the CV, cover letter, email, contact sheet and interview prep into `applications/<date>_<company>_<role>/`.
- New mission, achievement or number: tell Claude "add a new achievement". It updates `profile/master.md` after your approval.
- Edit `profile/master.md` by hand any time: Constraints (availability, visa), Confidential, Do-not-claim and Clients are enforced automatically on every build.

## Good to know
- Everything stays in files on your computer. Claude only uses what is in your profile and never invents experience.
- `TOKEN_EFFICIENCY.md` explains how to keep usage low (one application per session, `/clear` between them).
- Always review documents before sending them.
