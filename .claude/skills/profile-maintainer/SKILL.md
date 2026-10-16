---
name: profile-maintainer
description: Add or update facts in profile/master.md after a new mission, achievement, metric, certification or correction. Use when the user says they finished a mission, earned something, has new numbers, or wants to correct their profile.
---
# Profile maintainer

Goal: keep `profile/master.md` the single, truthful source for every document.

1. Find the right place cheaply: `python cvbuild.py facts` (index) and `python cvbuild.py fact <ID>` (one block). Do not read the whole file.
2. Ask at most 5 short questions, only for missing fields:
   what was done · user's exact role (led / delivered / assisted) · outcome · numbers (approximate is fine, invented is not) · confidentiality (client name allowed? internals?).
3. Draft the block in the existing format:
   ```
   ### F-<AREA>-<NN> · <title>
   - what: …
   - metrics: …
   - confidence: verified | exposure | pending
   - cv: "<approved bullet, starts with a varied action verb>"
   ```
   Next ID = highest existing number in that area + 1. Never reuse or delete IDs; mark old facts `retired`.
4. Show the block, wait for approval, then insert it with a targeted edit (not a full rewrite).
5. If it changes eligibility or claims, update `## Constraints`, `## Do-not-claim` (e.g. remove a certification once earned) or `## Confidential`.
6. Append one line to `## Changelog`: `- YYYY-MM-DD · <ID> added/updated · <reason>`.

Never upgrade `exposure` to `verified` without the user's explicit confirmation.
