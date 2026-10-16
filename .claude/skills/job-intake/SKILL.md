---
name: job-intake
description: Turn a job posting URL, saved HTML page or pasted text into a compact requirements file. Use at the start of every application, when the user shares a job link or job description.
---
# Job intake

1. Create the folder `applications/<YYYY-MM-DD>_<company>_<role>/` (lowercase, hyphens).
2. Fetch: `python cvbuild.py fetch "<url or file>" --out <folder>/posting.md`.
   - Login-walled pages (LinkedIn, some Workday): ask the user to save the page as HTML or paste the text into `<folder>/posting.txt`, then fetch that file.
   - Never read raw HTML or open the page in a browser yourself.
3. Read `posting.md` once and append this section to it (max ~35 lines, terse):
   ```
   ## Extracted
   company: … | role: … | location/remote: … | language(s): … | seniority: … | posted: …
   must-have:
   - …
   nice-to-have:
   - …
   language signal: stated languages, else infer "likely" from location (Flanders/NL → Dutch, Wallonia/Brussels/FR → French, DE/AT/CH-DE → German, LU → French/German)
   eligibility blockers to check: work permit / visa sponsorship / location / language / clearance / years
   keywords: comma-separated exact terms from the posting (max 25)
   ```
4. Pasted descriptions often lack the job card header. If **location or work mode** (remote / hybrid / on-site) is missing, ask the user one question ("Location and work mode shown on the job card?") and record the answer in `## Extracted` before fit assessment. Tip for the user: paste the card header line (title · company · location · work mode) together with the description.
5. `fetch` appends `## Contacts (auto-extracted)` (emails, hiring team, portal/email hints). Keep it; do not search for contacts at this stage.
6. Reply with one line: folder path + role + any obvious blocker. Do not summarise the posting.
