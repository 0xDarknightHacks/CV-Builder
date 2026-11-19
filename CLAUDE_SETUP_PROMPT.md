# Copy everything below the line into a new Claude chat, together with (1) cv-builder.zip and (2) your resume.
# Turn on "Code execution and file creation" in Claude settings first.

---

You are setting up a CV-builder repository for me. Attached: `cv-builder.zip` (the tool, with an empty template profile) and my current resume. Produce a personalised copy of the repository as a new ZIP.

**Rules**
- Use only facts from my resume and my answers. Never invent numbers, tools, clients, employers, dates or certifications. If something is unclear, ask.
- Do not change `cvbuild.py`, the skills logic, the fonts or the settings. Only fill in the profile and remove placeholders.
- Keep my exact spelling of names, titles, employers and dates.

**Steps**
1. Unzip the repository. Read `README.md`, `CLAUDE.md`, `profile/master.md`, `profile/base_cv.json` and `.claude/skills/profile-bootstrap/SKILL.md`. They define the formats you must follow exactly.
2. Read my resume completely.
3. Ask me **one message** with at most 10 short questions, only for what the resume does not answer:
   target headline and roles · location, relocation, remote preference · work authorization / visa sponsorship needs · notice period · certifications held · confidential clients or projects that must never be named · tools or certifications I must never claim · clients that must always appear on my CV · role families or required languages to avoid · the language my CV should be written in · numbers worth adding (users, systems, % improvements, time saved).
   Then wait for my answers.
4. Write `profile/master.md` following the template structure:
   - Identity, Constraints, Confidential, Do-not-claim, Clients, Experience (one section per employer), Projects, Evidence bank, Skills, Education, Pending verification, Changelog;
   - under each employer heading, an `Official title:` line with my exact job title (the build compares CV titles against it);
   - one `### F-<AREA>-<NN> · title` fact block per distinct achievement, with `what`, `metrics` (if any), `confidence`, `cv:` (approved bullet wording);
   - `confidence: verified` for what my resume or my answers state; `pending` for anything you inferred;
   - terms in Confidential, Do-not-claim and Clients wrapped in backticks;
   - remove the template's example fact and all `<…>` placeholders.
5. Write `profile/base_cv.json` using the template's schema:
   - `file_stem`: `First_Last_Resume`; header name in capitals; contact lines with markdown links `[text](url)`;
   - summary: two plain lines about how I work, with no technology list and no self-praise ("passionate", "results-driven", "proven");
   - each job: company and location, official title, date range; bullets start with a **bold action phrase**, vary verbs, use no pronouns, and cite fact IDs in `"facts"`;
   - projects: start year only (`"year": "2024"`), never "Present";
   - skills grouped by capability (2–4 groups); education; languages.
6. Install dependencies if missing (`pip install -r requirements.txt`; if there's no network, check that reportlab, python-docx, pypdf, requests and beautifulsoup4 import). Then run:
   `python cvbuild.py build profile/base_cv.json --out applications/_master`
   Fix every FAIL and rebuild until it prints PASS:
   - font below floor → shorten or remove the least important bullets (never shrink text);
   - orphan line → trim a few words in that bullet;
   - client dropped / forbidden term → restore or remove as instructed.
   If possible, render the PDF to an image and check the layout visually: one page, nothing cut off.
7. Final checks: no `<…>`, `FIRST LAST`, `First_Last`, `example.com`, `F-EXAMPLE` or `Official Job Title` remain in `profile/`; `tracker.csv` has only its header; `python cvbuild.py facts` lists my facts. Add a Changelog line to master.md. Delete `applications/_master/`.
8. Zip the repository as `cv-builder-<first>-<last>.zip` (same folder structure) and give it to me as a downloadable file, along with:
   - a ≤ 10-line report: number of facts, which facts are `pending` and what I must confirm, build result and font size;
   - the PDF of my master CV for review.
