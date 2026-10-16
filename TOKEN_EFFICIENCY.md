# Token efficiency rules (always apply)

## Read less
- Profile: `cvbuild.py facts --grep` then `fact <ID>`; never load all of master.md.
- Postings: only via `cvbuild.py fetch` (clean, truncated markdown). Never read raw HTML.
- Read `posting.md` once per application; afterwards use its `## Extracted` section only.
- Never open binaries (PDF, DOCX, TTF). Build and ats print everything needed.
- Read files in ranges or with grep when you need one part; don't re-read files already in context.

## Write less
- Edit with targeted replacements; never rewrite whole files to change a line.
- Replies: short status lines and file paths. Don't restate the posting, the profile or documents you just wrote.
- Generated files have hard length caps (see each skill). Prefer tables and bullets over prose in fit/prep files.

## Work deterministically
- Let `cvbuild.py` do layout, checks and keyword counts; don't reason about them manually.
- Fix build FAILs from the printed message; max 4 rebuild loops, then ask the user.
- Web search only in interview-prep (max 2 searches) or when a fetch fails.

## Session hygiene (for the user)
- One application per session: `/clear` between applications; the folder holds all state.
- `/compact` at phase boundaries in long sessions, before context fills.
- `/context` shows what fills the window; keep MCP servers you don't need disabled.
- Keep this file and CLAUDE.md short. Detailed procedures belong in skills, which load only when used.
