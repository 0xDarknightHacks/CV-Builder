#!/usr/bin/env python3
"""cvbuild — lightweight CV toolkit for Claude Code.

Commands (all print short, token-friendly output):
  facts [--grep TERM]          list fact IDs + titles from profile/master.md
  fact ID [ID ...]             print only the requested fact blocks
  fetch URL|FILE --out PATH    job posting -> clean, truncated markdown
  build CV.json [--out DIR]    render cv.pdf + cv.docx, then run all checks
  ats CV.pdf --keywords "a,b"  literal keyword coverage of the rendered PDF
  letter LETTER.md --cv CV.json render cover letter to PDF + DOCX; check letter + email.md
  diff CV.json                 what changed versus profile/base_cv.json
"""
import argparse, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path

import os

def _data_root():
    """Folder holding profile/, applications/ and tracker.csv: $CVBUILD_HOME, else the
    current folder if it has a profile, else the script's own folder (repo layout)."""
    env = os.environ.get("CVBUILD_HOME")
    if env: return Path(env).expanduser().resolve()
    if (Path.cwd() / "profile" / "master.md").exists(): return Path.cwd().resolve()
    return Path(__file__).resolve().parent

ROOT = _data_root()
MASTER = ROOT / "profile" / "master.md"

def _font_files():
    """Carlito (bundled or installed) or Calibri (Windows / Office), else None → Helvetica."""
    dirs = [Path(__file__).resolve().parent / "fonts", ROOT / "fonts",
            Path("/usr/share/fonts/truetype/crosextra"), Path("/usr/share/fonts/carlito"),
            Path("/usr/share/fonts/google-carlito-fonts"), Path.home() / ".local/share/fonts",
            Path.home() / "Library/Fonts", Path("/Library/Fonts"),
            Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts",
            Path("/Applications/Microsoft Word.app/Contents/Resources/DFonts")]
    names = [("Carlito-Regular.ttf", "Carlito-Bold.ttf", "Carlito-Italic.ttf", "Carlito-BoldItalic.ttf"),
             ("calibri.ttf", "calibrib.ttf", "calibrii.ttf", "calibriz.ttf"),
             ("Calibri.ttf", "Calibri Bold.ttf", "Calibri Italic.ttf", "Calibri Bold Italic.ttf")]
    for d in dirs:
        for n in names:
            if all((d / f).exists() for f in n): return [str(d / f) for f in n]
    return None

def register_fonts(pdfmetrics, TTFont):
    files = _font_files()
    if not files:
        print("WARN no Carlito/Calibri font found: using Helvetica (wider, may need shorter text). "
              "Install Carlito (fonts-crosextra-carlito) or put Carlito-*.ttf in a fonts/ folder.")
        return {"r": "Helvetica", "b": "Helvetica-Bold", "i": "Helvetica-Oblique"}
    for k, f in zip(("CVF", "CVF-Bold", "CVF-Italic", "CVF-BoldItalic"), files):
        pdfmetrics.registerFont(TTFont(k, f))
    pdfmetrics.registerFontFamily("CVF", normal="CVF", bold="CVF-Bold", italic="CVF-Italic", boldItalic="CVF-BoldItalic")
    return {"r": "CVF", "b": "CVF-Bold", "i": "CVF-Italic"}

# ---------------------------------------------------------------- config
CFG = {
    "font_max": 10.0, "font_floor": 9.5, "leading": 1.24,
    "margins_pt": (34, 28, 34, 26),          # left, top, right, bottom
    "navy": "#1F3864", "text": "#2B2B2B",
    "orphan_fill": 0.18,                      # last line < 18% wide = orphan
    "fetch_max_chars": 12000,
}

# ---------------------------------------------------------------- languages
LABELS = {
    "en": {"summary": "SUMMARY", "experience": "PROFESSIONAL EXPERIENCE", "projects": "PROJECTS",
           "skills": "SKILLS", "education": "EDUCATION", "languages": "LANGUAGES", "colon": ":"},
    "fr": {"summary": "PROFIL", "experience": "EXPÉRIENCE PROFESSIONNELLE", "projects": "PROJETS",
           "skills": "COMPÉTENCES", "education": "FORMATION", "languages": "LANGUES", "colon": "\u00a0:"},
}
def labels(cv): return LABELS.get(cv.get("lang", "en"), LABELS["en"])

# ---------------------------------------------------------------- style lint (common resume mistakes)
STYLE = {
    "en": {"pronoun": r"\b(I|me|my|mine|we|our)\b",
           "weak": r"^(responsible for|worked on|helped|assisted with|involved in|participated in|tasked with)\b",
           "vague": r"\b(various|etc\.?|and so on|many different|several things)\b"},
    "fr": {"pronoun": r"\b(je|j'|moi|mon|ma|mes|nous|notre|nos)\b",
           "weak": r"^(responsable de|participé à|aidé|chargé de|impliqué dans)\b",
           "vague": r"\b(divers(es)?|etc\.?|plusieurs choses)\b"},
}

def style_warnings(cv):
    rules, out, leads = STYLE.get(cv.get("lang", "en"), STYLE["en"]), [], {}
    items = [("summary", cv.get("summary", ""))] + [
        (sec, b["text"]) for sec in ("experience", "projects") for e in cv.get(sec, []) for b in e["bullets"]]
    for where, text in items:
        t = plain(text).strip()
        short = t[:45] + "…"
        if re.search(rules["pronoun"], t, re.I if cv.get("lang") == "fr" else 0): out.append(f"pronoun in {where}: “{short}”")
        if where != "summary" and re.search(rules["weak"], t, re.I): out.append(f"weak opener: “{short}”")
        if re.search(rules["vague"], t, re.I): out.append(f"vague wording: “{short}”")
        if where != "summary" and t:
            w = t.split()[0].lower().strip(",:;"); leads[w] = leads.get(w, 0) + 1
    out += [f"lead verb “{w}” used {n}× (vary verbs)" for w, n in leads.items() if n > 2]
    return out

# ---------------------------------------------------------------- profile index
FACT_RE = re.compile(r"^### (F-[A-Z0-9-]+)\s*·\s*(.+)$", re.M)

def master_text():
    return MASTER.read_text(encoding="utf-8")

def fact_index():
    return {m.group(1): m.group(2).strip() for m in FACT_RE.finditer(master_text())}

def section_terms(title):
    """Backticked terms listed under '## <title>' in master.md."""
    txt = master_text()
    m = re.search(rf"^## {re.escape(title)}\s*$(.*?)(?=^## |\Z)", txt, re.M | re.S)
    return re.findall(r"`([^`]+)`", m.group(1)) if m else []

# ---------------------------------------------------------------- number provenance
NUM_RE = re.compile(r"(?<![A-Za-z0-9#.\-/])\d[\d,]*(?:\.\d+)?(?![A-Za-z0-9])")
NUM_ALLOW = {365.0}                     # product names (Microsoft 365) are not claims

def numbers(text):
    out = set()
    for m in NUM_RE.findall(plain(text)):
        try: out.add(float(m.replace(",", "")))
        except ValueError: pass
    return out

def fact_text(ids):
    txt = master_text(); parts = []
    for fid in ids:
        m = re.search(rf"^### {re.escape(fid)} .*?(?=^### |^## |\Z)", txt, re.M | re.S)
        if m: parts.append(m.group(0))
    return "\n".join(parts)

def unsupported_numbers(text, source):
    allowed = {float(x.replace(",", "")) for x in NUM_RE.findall(source)} | NUM_ALLOW
    return sorted(n for n in numbers(text) if n not in allowed)

def fmt(n): return str(int(n)) if n == int(n) else str(n)

def official_titles():
    """{employer heading text: official title} from '## Experience — X' sections."""
    txt, out = master_text(), {}
    for m in re.finditer(r"^## Experience — (.+?)$(.*?)(?=^## |\Z)", txt, re.M | re.S):
        t = re.search(r"^Official title:\s*(.+?)\s*(?:\(|$)", m.group(2), re.M)
        if t: out[m.group(1)] = t.group(1).strip()
    return out

def cmd_facts(a):
    for fid, title in fact_index().items():
        if not a.grep or a.grep.lower() in (fid + " " + title).lower():
            print(f"{fid} · {title}")

def cmd_fact(a):
    txt = master_text()
    for fid in a.ids:
        m = re.search(rf"^### {re.escape(fid)} .*?(?=^### |^## |\Z)", txt, re.M | re.S)
        print(m.group(0).strip() + "\n" if m else f"{fid}: not found\n")

# ---------------------------------------------------------------- fetch
ANCHOR_RE = re.compile(r"^(about the job|job description|about the role|the role|role description|"
                       r"your (role|mission|responsibilities)|description du poste|votre mission|"
                       r"functieomschrijving|vacature|stellenbeschreibung|ihre aufgaben)\b", re.I)

END_RE = re.compile(r"^(about the company|about us|interested in working with us|more jobs|similar jobs|"
                    r"people also viewed|meet the hiring team|trending employee content|set alert|"
                    r"show more jobs|job search faster with premium|à propos de l.entreprise|over het bedrijf)\b", re.I)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PORTAL_RE = re.compile(r"(apply|applications?)\s+(only\s+)?(via|through|on)\s+(our|the)\s+(online\s+)?"
                       r"(portal|website|career|careers|ats|application)|no e-?mail applications|"
                       r"applications?\s+(sent\s+)?by\s+e-?mail\s+will\s+not|"
                       r"postulez\s+(uniquement\s+)?(via|sur)\s+(notre|le)\s+(site|portail)|candidatures?\s+par\s+e-?mail\s+ne", re.I)
INVITE_RE = re.compile(r"(send|e-?mail|mail)\s+(us\s+)?(your\s+)?(cv|resume|résumé|application|candidature)\s+(to|at)|"
                       r"envoye[rz]\s+(votre\s+)?(cv|candidature)\s+(à|a)", re.I)

WORDNUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
           "ten": 10, "twelve": 12, "fifteen": 15, "un": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "dix": 10}
YEARS_RE = re.compile(r"(\d{1,2}|" + "|".join(WORDNUM) + r")\s*(?:\(\d{1,2}\)\s*)?(\+|or more|ou plus)?\s*"
                      r"(?:(?:-|–|to|à)\s*(\d{1,2})\s*)?\+?\s*(?:years?|yrs|ans|an)\b", re.I)
EXP_RE = re.compile(r"experience|expérience|expertise|background|track record", re.I)
NOT_EXP_RE = re.compile(r"years old|ans? d'âge|founded|since \d{4}|anniversary|history|vesting|contract of|degree|diplôme", re.I)
PREF_RE = re.compile(r"preferred|nice to have|a plus|an advantage|bonus|ideally|desirable|souhait|un plus|idéalement|serait un atout", re.I)
SKILL_RE = re.compile(r"(?:years?|ans)\s+(?:of\s+)?(?:hands-on\s+)?(?:experience\s+)?(?:with|using|in using|d'expérience (?:avec|sur|en))\s+[A-Z]", re.I)
CONTRACT_RE = re.compile(r"\bB2B\b|independent contractor|\bcontractor\b|freelance|self-employed|\b1099\b|\bIR35\b|"
                         r"umowa o prac|\bCDI\b|\bCDD\b|contrat de prestation|fixed-term|\bpermanent\b|interim|"
                         r"temporary|consulting agreement|service agreement", re.I)
SALARY_RE = re.compile(r"(?:€|EUR|PLN|zł|£|GBP|\$|USD|CHF|AED|SAR|QAR)\s?(?:\d{1,3}[\s.,]?\d{3}|\d{2,3}\s?k)\b|"
                       r"(?:\d{1,3}[\s.,]?\d{3}|\d{2,3}\s?k)\s?(?:€|EUR|PLN|zł|£|CHF|AED|SAR)\b", re.I)
SALARY_WORD_RE = re.compile(r"\b(?:salary|salaire|compensation|rémunération|per annum)\b", re.I)
AGE_RE = re.compile(r"\b(?:re)?posted\b[^.\n]{0,25}?\b\d+\s+(?:hours?|days?|weeks?|months?)\s+ago|\b\d+\s+(?:hours?|days?|weeks?|months?)\s+ago|"
                    r"il y a \d+\s+(?:heures?|jours?|semaines?|mois)", re.I)

def years_signals(text):
    """Required years, read like career-ops' jd-years rule: only required, overall
    experience figures gate; skill-specific and preferred figures never do."""
    rows, gate = [], []
    for sent in re.split(r"(?<=[.!?;])\s+|\n|•", text):
        if not EXP_RE.search(sent) or NOT_EXP_RE.search(sent): continue
        for m in YEARS_RE.finditer(sent):
            lo = m.group(1).lower(); lo = WORDNUM.get(lo, None) or int(lo) if not lo.isdigit() else int(lo)
            kind = "preferred" if PREF_RE.search(sent) else "required"
            scope = "skill" if SKILL_RE.search(sent[m.start():m.start() + 80]) else "overall"
            rng = f"{lo}–{m.group(3)}" if m.group(3) else f"{lo}{'+' if m.group(2) else ''}"
            rows.append(f"- {rng} years · {kind} · {scope} · “{' '.join(sent.split())[:110]}”")
            if kind == "required" and scope == "overall": gate.append(lo)
    gating = f"{min(gate)} years (lowest required overall figure)" if gate else "none stated"
    return gating, rows[:6]

def signals_section(text):
    gating, rows = years_signals(text)
    contract = sorted({m.group(0).strip() for m in CONTRACT_RE.finditer(text)}, key=str.lower)
    salary = SALARY_RE.search(text); age = AGE_RE.search(text)
    return ("\n\n## Signals (auto-extracted, advisory)\n"
            f"years gate: {gating}\n" + ("\n".join(rows) + "\n" if rows else "") +
            f"contract terms: {', '.join(contract) or 'none found'}\n"
            f"salary: {('figure: ' + ' '.join(salary.group(0).split())) if salary else ('mentioned, no figure' if SALARY_WORD_RE.search(text) else 'not stated')}\n"
            f"posting age: {' '.join(age.group(0).split()) if age else 'unknown'}")

def contacts_section(text, hiring=()):
    """Deterministic contact hints appended to posting.md (no tokens spent by Claude)."""
    emails = sorted({e.rstrip(".").lower() for e in EMAIL_RE.findall(text)
                     if not re.search(r"no-?reply|\.(png|jpe?g|gif|svg)$", e, re.I)})
    hints = (["apply-via-portal stated"] if PORTAL_RE.search(text) else []) + \
            (["email application invited"] if INVITE_RE.search(text) else [])
    return ("\n\n## Contacts (auto-extracted)\n"
            f"emails: {', '.join(emails) or 'none'}\n"
            f"hiring team: {', '.join(hiring) or 'none'}\n"
            f"channel hints: {', '.join(hints) or 'none'}" + signals_section(text))

def cmd_fetch(a):
    from bs4 import BeautifulSoup
    src = a.source
    if re.match(r"https?://", src):
        import requests
        r = requests.get(src, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status(); html = r.text
    else:
        html = Path(src).read_text(encoding="utf-8", errors="ignore")
        if not re.search(r"<html|<body|<div", html, re.I):        # plain text / md
            return _write_posting(a.out, src, html + contacts_section(html))
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript", "svg", "nav", "footer", "header", "form", "iframe"]):
        t.decompose()
    main = soup.find("main") or soup.find("article") or soup.body or soup
    lines = []
    for el in main.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        t = " ".join(el.get_text(" ", strip=True).split())
        if len(t) < 3: continue
        if el.name.startswith("h"): lines.append("\n" + "#" * min(int(el.name[1]) + 1, 4) + " " + t)
        elif el.name == "li": lines.append("- " + t)
        else: lines.append(t)
    out, seen = [], set()
    for l in lines:                                                # de-duplicate boilerplate
        if l not in seen: seen.add(l); out.append(l)
    hiring = []
    ht = next((k for k, l in enumerate(out) if re.search(r"meet the hiring team", l, re.I)), None)
    if ht is not None:
        for l in out[ht + 1: ht + 6]:
            t = l.strip("#- ").strip()
            if re.fullmatch(r"[A-ZÀ-Ý][\w'’.-]+(\s+[A-ZÀ-Ý][\w'’.-]+){1,3}", t) and len(t) <= 40: hiring.append(t)
    mailtos = [m["href"][7:].split("?")[0] for m in main.select('a[href^="mailto:"]')]
    # Job boards (LinkedIn, Indeed, Workday…) wrap the posting in sidebars and listings.
    # Start at the first description anchor; otherwise drop short, non-sentence lines.
    idx = next((k for k, l in enumerate(out) if ANCHOR_RE.search(l.strip().lstrip("#- ").strip())), None)
    if idx is not None:
        out = out[idx:]
        end = next((k for k, l in enumerate(out) if k and END_RE.search(l.strip().lstrip("#- ").strip())), None)
        if end: out = out[:end]
        longs = [l for l in out if len(l) > 400]                    # boards repeat text as paragraph + list
        out = [l for l in out if len(l) > 400 or len(l.strip("- ")) < 15
               or not any(l.strip("- ") in L for L in longs)]
    else:
        out = [l for l in out if l.startswith(("#", "\n#", "- ")) or len(l.split()) >= 5]
    title = " ".join((soup.title.get_text(" ", strip=True) if soup.title else "").split())
    head = f"# {title}\n" if title else ""
    body = head + "\n".join(out)
    _write_posting(a.out, src, body + contacts_section(body + " " + " ".join(mailtos), hiring))

def _write_posting(out, src, body):
    body = body.strip()
    contacts = ""
    if "\n## Contacts (auto-extracted)" in body:
        body, contacts = body.split("\n## Contacts (auto-extracted)", 1)
        contacts = "\n\n## Contacts (auto-extracted)" + contacts
    if len(body) > CFG["fetch_max_chars"]:
        body = body[:CFG["fetch_max_chars"]] + "\n\n[truncated]"
    body = body.rstrip() + contacts
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    body = body.replace("\r\n", "\n").replace("\r", "\n")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:      # LF on every OS
        fh.write(f"<!-- source: {src} -->\n{body}\n")
    print(f"saved {out} ({len(body)} chars, ~{len(body)//4} tokens)")

# ---------------------------------------------------------------- inline markup
# **bold**, *italic*, [text](url)  ->  list of (text, bold, italic, url)
TOK = re.compile(r"\[(.+?)\]\((.+?)\)|\*\*(.+?)\*\*|\*(.+?)\*")

def segs(text, b=False, i=False, url=None):
    out, pos = [], 0
    for m in TOK.finditer(text):
        if m.start() > pos: out.append((text[pos:m.start()], b, i, url))
        if m.group(1) is not None: out += segs(m.group(1), b, i, m.group(2))
        elif m.group(3) is not None: out += segs(m.group(3), True, i, url)
        else: out += segs(m.group(4), b, True, url)
        pos = m.end()
    if pos < len(text): out.append((text[pos:], b, i, url))
    return out

def plain(text):
    return "".join(s[0] for s in segs(text))

def to_rl(text, navy):
    """segments -> ReportLab paragraph markup."""
    h = []
    for t, b, i, u in segs(text):
        t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if b: t = f"<b>{t}</b>"
        if i: t = f"<i>{t}</i>"
        if u: t = f'<a href="{u}" color="{navy}">{t}</a>'
        h.append(t)
    return "".join(h)

# ---------------------------------------------------------------- PDF
def render_pdf(cv, path):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    F = register_fonts(pdfmetrics, TTFont)

    W, H = A4
    ML, MT, MR, MB = CFG["margins_pt"]
    CW = W - ML - MR
    NAVY, TEXT = HexColor(CFG["navy"]), HexColor(CFG["text"])
    hd = cv["header"]; L = labels(cv)
    sections = [s for s in ["summary", "experience", "projects", "skills", "education", "languages"] if cv.get(s)]
    n_flex = len(sections) + max(len(cv.get("projects", [])) - 1, 0) + max(len(cv.get("education", [])) - 1, 0)

    def layout(fs, c=None, extra=0.0):
        lead = fs * CFG["leading"]
        body = ParagraphStyle("b", fontName=F["r"], fontSize=fs, leading=lead, alignment=TA_LEFT, textColor=TEXT)
        bul = ParagraphStyle("u", parent=body, leftIndent=10, bulletIndent=1)
        ctr = ParagraphStyle("c", parent=body, alignment=TA_CENTER)
        st = {"y": H - MT, "used": 0.0, "orphans": []}

        def adv(h, fx=0.0): st["y"] -= h + fx; st["used"] += h
        def para(text, style, track=False, **kw):
            p = Paragraph(text, style, **kw); _, h = p.wrap(CW, 10000)
            if track and len(p.blPara.lines) > 1:
                ln = p.blPara.lines[-1]
                ex = ln[0] if isinstance(ln, tuple) else getattr(ln, "extraSpace", 0)
                if 1 - ex / (CW - style.leftIndent) < CFG["orphan_fill"]:
                    st["orphans"].append(re.sub("<[^>]+>", "", text)[:60])
            if c: p.drawOn(c, ML, st["y"] - h)
            adv(h)
        def gap(g, flex=True): adv(g, extra if flex else 0)
        def heading(t):
            hs = fs + 1.6; gap(fs * 0.85)
            if c:
                y = st["y"]; c.setFont(F["b"], hs); c.setFillColor(NAVY); c.drawString(ML, y - hs * 0.8, t)
                c.setStrokeColor(NAVY); c.setLineWidth(0.7); c.line(ML, y - hs - 1.2, W - MR, y - hs - 1.2)
            adv(hs + 3.8)
        def entry(title, rest="", right="", url=None):
            if c:
                base = st["y"] - fs * 0.88; ts = fs + 0.4
                c.setFillColor(TEXT); c.setFont(F["b"], ts); c.drawString(ML, base, title)
                wt = pdfmetrics.stringWidth(title, F["b"], ts)
                if url: c.linkURL(url, (ML, base - 2, ML + wt, base + ts * 0.8), relative=0, thickness=0)
                if rest: c.setFont(F["i"], fs); c.drawString(ML + wt, base, rest)
                if right: c.setFont(F["b"], fs); c.drawRightString(W - MR, base, right)
            adv(fs * 1.25)
        def bullets(items):
            for b in items:
                para(to_rl(b["text"], CFG["navy"]), bul, track=True, bulletText="•"); gap(0.6, False)

        ns = fs + 11
        if c:
            c.setFont(F["b"], ns); c.setFillColor(NAVY); c.drawCentredString(W / 2, st["y"] - ns * 0.78, hd["name"])
        adv(ns * 1.02)
        para(f'<font name="{F["b"]}" size="{fs + 2.5}" color="{CFG["navy"]}">{hd["title"]}</font>',
             ParagraphStyle("t", parent=ctr, leading=(fs + 2.5) * 1.25))
        gap(1, False)
        for line in hd["lines"]: para(to_rl(line, CFG["navy"]), ctr)

        if cv.get("summary"):
            heading(L["summary"]); para(to_rl(cv["summary"], CFG["navy"]), body, track=True)
        if cv.get("experience"):
            heading(L["experience"])
            for e in cv["experience"]:
                entry(e["company"], " | " + e["location"], e["date"])
                para(f'<i>{e["title"]}</i>', body); gap(0.6, False); bullets(e["bullets"])
        if cv.get("projects"):
            heading(L["projects"])
            for k, p in enumerate(cv["projects"]):
                if k: gap(1.8)
                entry(p["title"], f' ({p["year"]})', "", p.get("url")); gap(0.4, False); bullets(p["bullets"])
        if cv.get("skills"):
            heading(L["skills"])
            for s in cv["skills"]:
                para(f'<b>{s["label"]}{L["colon"]}</b> ' + to_rl(s["text"], CFG["navy"]), bul, track=True, bulletText="•")
                gap(0.6, False)
        if cv.get("education"):
            heading(L["education"])
            for k, e in enumerate(cv["education"]):
                if k: gap(2.0)
                entry(e["title"], e.get("rest", ""), e["date"], e.get("url"))
                if e.get("detail"): para(f'<i>{to_rl(e["detail"], CFG["navy"])}</i>', body)
        if cv.get("languages"):
            heading(L["languages"]); para(to_rl(cv["languages"], CFG["navy"]), body)
        return st

    avail = H - MT - MB
    fs = CFG["font_max"]
    while layout(fs)["used"] > avail and fs > CFG["font_floor"] - 1:
        fs = round(fs - 0.05, 2)
    extra = max(avail - layout(fs)["used"], 0) / max(n_flex, 1)
    c = canvas.Canvas(str(path), pagesize=A4, initialFontName=F["r"], initialFontSize=10)
    c.setTitle(f'{hd["name"].title()} – {hd["title"]} CV'); c.setAuthor(hd["name"].title())
    st = layout(fs, c, extra); c.showPage(); c.save()
    return {"font": fs, "overflow": layout(fs)["used"] > avail, "orphans": st["orphans"]}

# ---------------------------------------------------------------- DOCX
def render_docx(cv, path, font=10.0):
    """font = size chosen by the PDF fit, rounded down to Word's half-point steps."""
    fs = max(int(font * 2) / 2, 8.5)
    from docx import Document
    from docx.shared import Pt, Mm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    navy = RGBColor.from_string(CFG["navy"][1:]); text = RGBColor.from_string(CFG["text"][1:])
    doc = Document(); sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(210), Mm(297)
    ML, MT, MR, MB = CFG["margins_pt"]
    sec.left_margin, sec.top_margin, sec.right_margin, sec.bottom_margin = Pt(ML), Pt(MT), Pt(MR), Pt(MB)
    cw = sec.page_width - sec.left_margin - sec.right_margin
    normal = doc.styles["Normal"]; normal.font.name = "Calibri"; normal.font.size = Pt(fs)
    normal.font.color.rgb = text
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    normal.paragraph_format.space_after = Pt(0); normal.paragraph_format.line_spacing = 1.0

    def run(p, t, b=False, i=False, size=None, color=None):
        r = p.add_run(t); r.bold = b; r.italic = i
        if size: r.font.size = Pt(size)
        if color: r.font.color.rgb = color
        return r
    def link(p, t, url, b=False, i=False, color=None):
        rid = p.part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
                               is_external=True)
        hl = OxmlElement("w:hyperlink"); hl.set(qn("r:id"), rid)
        r = OxmlElement("w:r"); rpr = OxmlElement("w:rPr")
        col = OxmlElement("w:color"); col.set(qn("w:val"), (color or CFG["navy"])[1:]); rpr.append(col)
        if b: rpr.append(OxmlElement("w:b"))
        if i: rpr.append(OxmlElement("w:i"))
        r.append(rpr); tx = OxmlElement("w:t"); tx.text = t; tx.set(qn("xml:space"), "preserve"); r.append(tx)
        hl.append(r); p._p.append(hl)
    def rich(p, txt, base_i=False):
        for t, b, i, u in segs(txt):
            link(p, t, u, b, i or base_i) if u else run(p, t, b, i or base_i)
    def heading(t):
        p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(5); p.paragraph_format.space_after = Pt(2)
        run(p, t, b=True, size=fs + 1.5, color=navy)
        pPr = p._p.get_or_add_pPr(); bdr = OxmlElement("w:pBdr"); bt = OxmlElement("w:bottom")
        for k, v in [("val", "single"), ("sz", "6"), ("space", "1"), ("color", CFG["navy"][1:])]: bt.set(qn(f"w:{k}"), v)
        bdr.append(bt); pPr.append(bdr)
    def entry(title, rest="", right="", url=None):
        p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(2); p.paragraph_format.keep_with_next = True
        p.paragraph_format.tab_stops.add_tab_stop(cw, WD_TAB_ALIGNMENT.RIGHT)
        link(p, title, url, b=True, color=CFG["text"]) if url else run(p, title, b=True)
        if rest: run(p, rest, i=True)
        if right: run(p, "\t"); run(p, right, b=True)
    def bullet(txt, label=None):
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.left_indent = Pt(11); p.paragraph_format.first_line_indent = Pt(-10)
        p.paragraph_format.space_after = Pt(0.5)
        if label: run(p, label + labels(cv)["colon"] + " ", b=True)
        rich(p, txt)

    hd = cv["header"]; L = labels(cv)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; run(p, hd["name"], b=True, size=fs + 11, color=navy)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; run(p, hd["title"], b=True, size=fs + 2.5, color=navy)
    for line in hd["lines"]:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; rich(p, line)
    if cv.get("summary"):
        heading(L["summary"]); rich(doc.add_paragraph(), cv["summary"])
    if cv.get("experience"):
        heading(L["experience"])
        for e in cv["experience"]:
            entry(e["company"], " | " + e["location"], e["date"])
            p = doc.add_paragraph(); p.paragraph_format.keep_with_next = True; run(p, e["title"], i=True)
            for b in e["bullets"]: bullet(b["text"])
    if cv.get("projects"):
        heading(L["projects"])
        for pr in cv["projects"]:
            entry(pr["title"], f' ({pr["year"]})', "", pr.get("url"))
            for b in pr["bullets"]: bullet(b["text"])
    if cv.get("skills"):
        heading(L["skills"])
        for s in cv["skills"]: bullet(s["text"], s["label"])
    if cv.get("education"):
        heading(L["education"])
        for e in cv["education"]:
            entry(e["title"], e.get("rest", ""), e["date"], e.get("url"))
            if e.get("detail"): rich(doc.add_paragraph(), e["detail"], base_i=True)
    if cv.get("languages"):
        heading(L["languages"]); rich(doc.add_paragraph(), cv["languages"])
    doc.core_properties.author = hd["name"].title(); doc.core_properties.title = f'{hd["name"].title()} CV'
    doc.save(str(path))

def docx_pages(path):
    exe = shutil.which("soffice") or shutil.which("libreoffice")
    for cand in (r"C:\Program Files\LibreOffice\program\soffice.exe",
                 r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
                 "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        if not exe and Path(cand).exists(): exe = cand
    if not exe: return None
    with tempfile.TemporaryDirectory() as d:
        subprocess.run([exe, "--headless", "--convert-to", "pdf", "--outdir", d, str(path)],
                       capture_output=True, timeout=120)
        out = Path(d) / (Path(path).stem + ".pdf")
        if not out.exists(): return None
        from pypdf import PdfReader
        return len(PdfReader(str(out)).pages)

# ---------------------------------------------------------------- checks
def all_text(cv):
    parts = [cv.get("summary", ""), cv.get("languages", "")] + cv["header"]["lines"]
    for sec in ("experience", "projects"):
        for e in cv.get(sec, []):
            parts += [e.get("title", ""), e.get("company", "")] + [b["text"] for b in e["bullets"]]
    parts += [s["label"] + " " + s["text"] for s in cv.get("skills", [])]
    parts += [e["title"] + " " + e.get("detail", "") for e in cv.get("education", [])]
    return plain("\n".join(parts))

def run_checks(cv, pdf, res, docx_path):
    errs, warns = [], []
    known = fact_index()
    for sec in ("experience", "projects"):
        for e in cv.get(sec, []):
            for b in e["bullets"]:
                ids = b.get("facts", [])
                if not ids: errs.append(f"no fact reference: “{plain(b['text'])[:50]}…”")
                for f in ids:
                    if f not in known: errs.append(f"unknown fact {f}")
                bad = unsupported_numbers(b["text"], fact_text(ids)) if ids else []
                if bad: errs.append(f"number(s) {', '.join(map(fmt, bad))} not in cited facts {', '.join(ids)}: “{plain(b['text'])[:50]}…”")
    for where, text in [("summary", cv.get("summary", ""))] + [(f"skills/{s['label']}", s["text"]) for s in cv.get("skills", [])]:
        bad = unsupported_numbers(text, master_text())
        if bad: errs.append(f"number(s) {', '.join(map(fmt, bad))} in {where} not found in master.md")
    titles = official_titles()
    for e in cv.get("experience", []):
        match = [t for k, t in titles.items() if e["company"].lower() in k.lower()]
        if not match: warns.append(f"no 'Official title:' in master.md for {e['company']}")
        elif e["title"].strip() != match[0]:
            errs.append(f"job title changed for {e['company']}: “{e['title']}” ≠ official “{match[0]}”")
    txt = all_text(cv)
    for title in ("Confidential", "Do-not-claim"):
        for term in section_terms(title):
            if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", txt, re.I): errs.append(f"{title} term used: {term}")
    for p in cv.get("projects", []):
        if re.search(r"present|présent|aujourd|–|-", str(p.get("year", "")), re.I): errs.append(f"project uses a date range: {p['title']}")
    for client in section_terms("Clients"):
        if client.lower() not in txt.lower():
            errs.append(f"client dropped: {client} (keep every named client; compress into one line if needed)")
    from pypdf import PdfReader
    rd = PdfReader(str(pdf)); pages = len(rd.pages)
    if pages != 1 or res["overflow"]: errs.append(f"PDF does not fit one page (pages={pages})")
    if res["font"] < CFG["font_floor"]:
        errs.append(f"font {res['font']}pt below floor {CFG['font_floor']}pt: cut content, do not shrink")
    for o in res["orphans"]: errs.append(f"orphan line in: “{o}…”")
    ext = rd.pages[0].extract_text() or ""
    warns += [f"style: {w}" for w in style_warnings(cv)]
    for h in (labels(cv)["experience"].split()[0], cv["header"]["name"].split()[0]):
        if h.lower() not in ext.lower(): warns.append(f"text extraction missing '{h}'")
    dp = docx_pages(docx_path)
    if dp is None: warns.append("DOCX page count NOT verified (LibreOffice not installed): open the DOCX in Word and confirm one page, and note this in summary.md")
    elif dp != 1: errs.append(f"DOCX does not fit one page (pages={dp})")
    return errs, warns, len(txt.split())

def cmd_build(a):
    cv = json.loads(Path(a.cv).read_text(encoding="utf-8"))
    out = Path(a.out or Path(a.cv).parent); out.mkdir(parents=True, exist_ok=True)
    stem = cv.get("file_stem", "cv")
    pdf, docx_path = out / f"{stem}.pdf", out / f"{stem}.docx"
    res = render_pdf(cv, pdf); render_docx(cv, docx_path, res["font"])
    errs, warns, words = run_checks(cv, pdf, res, docx_path)
    print(f"built {pdf.name} + {docx_path.name} | font {res['font']}pt | {words} words")
    for w in warns: print("WARN", w)
    for e in errs: print("FAIL", e)
    print("PASS" if not errs else f"{len(errs)} issue(s) to fix")
    sys.exit(1 if errs else 0)

def cmd_ats(a):
    from pypdf import PdfReader
    txt = " ".join((pg.extract_text() or "") for pg in PdfReader(a.pdf).pages).lower()
    txt = re.sub(r"\s+", " ", txt)
    kws = [k.strip() for k in a.keywords.split(",") if k.strip()]
    hit = [k for k in kws if k.lower() in txt]; miss = [k for k in kws if k.lower() not in txt]
    print(f"coverage {len(hit)}/{len(kws)} ({100 * len(hit) // max(len(kws), 1)}%) — heuristic, not a real ATS score")
    if miss: print("missing:", ", ".join(miss))

# ---------------------------------------------------------------- letter
def term_errors(text):
    errs = []
    for title in ("Confidential", "Do-not-claim"):
        for term in section_terms(title):
            if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text, re.I): errs.append(f"{title} term used: {term}")
    return errs

AI_PHRASES_RE = re.compile(
    r"\b(?:I am (?:thrilled|excited|delighted) to|I'm (?:thrilled|excited)|delve|leverag(?:e|ing)|synerg(?:y|ies)|"
    r"fast-paced|cutting-edge|game-chang\w+|passionate about|results-driven|proven track record|"
    r"dynamic (?:environment|team)|spearhead(?:ed|ing)?|unwavering|in today's\b|tapestry|seamless(?:ly)?|"
    r"robust solutions?|hit the ground running|wear many hats|je suis ravi|passionné par|dynamique et motivé)", re.I)

def cmd_letter(a):
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from docx import Document
    from docx.shared import Pt, Mm, RGBColor

    cv = json.loads(Path(a.cv).read_text(encoding="utf-8"))
    hd, folder = cv["header"], Path(a.letter).parent
    raw = Path(a.letter).read_text(encoding="utf-8").replace("\r\n", "\n")
    blocks = [b.strip() for b in re.split(r"\n\s*\n", raw) if b.strip()]
    if blocks and plain(blocks[0]).splitlines()[0].strip().lower() == hd["name"].lower():
        blocks = blocks[1:]                                        # letterhead comes from cv.json
    errs = term_errors(plain(raw)); words = len(plain(" ".join(blocks)).split())
    if not 200 <= words <= 360: errs.append(f"cover letter length {words} words (target 250–330)")
    email = folder / "email.md"
    if email.exists():
        et = plain(email.read_text(encoding="utf-8")); ew = len(et.split())
        errs += [f"email.md: {e}" for e in term_errors(et)]
        if ew > 160: errs.append(f"email.md length {ew} words (target ≤ 140)")

    errs += check_contact(folder)
    # numbers in candidate-facing prose must exist in the profile or the posting
    src = master_text() + "\n" + ((folder / "posting.md").read_text(encoding="utf-8") if (folder / "posting.md").exists() else "")
    docs = {"cover-letter.md": raw}
    for extra in ("email.md", "answers.md"):
        if (folder / extra).exists(): docs[extra] = (folder / extra).read_text(encoding="utf-8")
    for name, text in docs.items():
        body = re.sub(r"^(To|Subject):.*$", "", text, flags=re.M)
        bad = unsupported_numbers(body, src)
        if bad: errs.append(f"{name}: number(s) {', '.join(map(fmt, bad))} not found in master.md or posting.md")
        for p in AI_PHRASES_RE.findall(plain(text)):
            print(f"WARN {name}: stock AI phrasing “{p}” — rewrite in plain words")
        if text.count("—") > 2: print(f"WARN {name}: {text.count('—')} em-dashes — use commas or full stops")
        if name == "answers.md": errs += [f"answers.md: {e}" for e in term_errors(plain(text))]

    stem = cv.get("file_stem", "cv").replace("_Resume", "") + "_Cover_Letter"
    pdf, docx_path = folder / f"{stem}.pdf", folder / f"{stem}.docx"
    _F = register_fonts(pdfmetrics, TTFont); fr, fb = _F["r"], _F["b"]
    navy, text = HexColor(CFG["navy"]), HexColor(CFG["text"])
    st_name = ParagraphStyle("n", fontName=fb, fontSize=18, leading=22, textColor=navy)
    st_meta = ParagraphStyle("m", fontName=fr, fontSize=9.5, leading=12, textColor=text)
    st_body = ParagraphStyle("b", fontName=fr, fontSize=10.5, leading=14.5, textColor=text, spaceAfter=8)
    story = [Paragraph(hd["name"].title(), st_name)]
    story += [Paragraph(to_rl(l, CFG["navy"]), st_meta) for l in hd["lines"]] + [Spacer(1, 18)]
    story += [Paragraph(to_rl(b, CFG["navy"]).replace("\n", "<br/>"), st_body) for b in blocks]
    ML, MT, MR, MB = CFG["margins_pt"]
    doc = SimpleDocTemplate(str(pdf), pagesize=A4, leftMargin=ML + 20, rightMargin=MR + 20,
                            topMargin=MT + 20, bottomMargin=MB + 20,
                            title=f'{hd["name"].title()} – Cover Letter', author=hd["name"].title())
    doc.build(story)
    from pypdf import PdfReader
    if len(PdfReader(str(pdf)).pages) != 1: errs.append("cover letter PDF is longer than one page")

    d = Document(); sec = d.sections[0]
    sec.page_width, sec.page_height = Mm(210), Mm(297)
    for side, v in zip(("left_margin", "top_margin", "right_margin", "bottom_margin"), CFG["margins_pt"]):
        setattr(sec, side, Pt(v + 20))
    normal = d.styles["Normal"]; normal.font.name = "Calibri"; normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor.from_string(CFG["text"][1:])
    r = d.add_paragraph().add_run(hd["name"].title()); r.bold = True; r.font.size = Pt(18)
    r.font.color.rgb = RGBColor.from_string(CFG["navy"][1:])
    for l in hd["lines"]:
        p = d.add_paragraph(); p.paragraph_format.space_after = Pt(0); p.add_run(plain(l)).font.size = Pt(9.5)
    d.add_paragraph()
    for b in blocks:
        p = d.add_paragraph(); p.paragraph_format.space_after = Pt(8)
        for t, bold, ital, _ in segs(b):
            rr = p.add_run(t); rr.bold = bold; rr.italic = ital
    d.save(str(docx_path))
    print(f"built {pdf.name} + {docx_path.name} | {words} words")
    for e in errs: print("FAIL", e)
    print("PASS" if not errs else f"{len(errs)} issue(s) to fix")
    sys.exit(1 if errs else 0)

# ---------------------------------------------------------------- contact
ATS_DOMAINS = ("myworkdayjobs.com", "workday.com", "greenhouse.io", "lever.co", "smartrecruiters.com",
               "teamtailor.com", "recruitee.com", "workable.com", "personio.de", "personio.com", "jobvite.com",
               "icims.com", "successfactors.com", "successfactors.eu", "taleo.net", "bamboohr.com", "ashbyhq.com")
CHANNELS = {"email", "portal", "portal+follow-up", "linkedin-message"}
CONFIDENCE = {"posting", "official-hr", "general-contact", "none"}

def check_contact(folder):
    """Validate contact.md and write a ready mailto link. Returns a list of errors."""
    from urllib.parse import urlparse, quote
    cpath = folder / "contact.md"
    if not cpath.exists():
        print("WARN contact.md missing (application-writer should create it)"); return []
    txt = cpath.read_text(encoding="utf-8")
    f = {k.lower(): v.strip() for k, v in re.findall(r"^([A-Za-z]+):[ \t]*(.*)$", txt, re.M)}
    errs, to = [], f.get("to", "").strip(" —-")
    domain = f.get("domain", "").lower().removeprefix("www.")
    if f.get("channel") not in CHANNELS: errs.append(f"contact.md: channel must be one of {sorted(CHANNELS)}")
    if f.get("confidence") not in CONFIDENCE: errs.append(f"contact.md: confidence must be one of {sorted(CONFIDENCE)}")
    if f.get("channel") == "email" and not to: errs.append("contact.md: channel email needs a 'to:' address")
    if not to:
        src = f.get("source", "").strip()
        if f.get("confidence") != "none":
            errs.append("contact.md: no address, so confidence must be 'none'")
        if src.lower() != "none" and not src.startswith("http"):
            errs.append("contact.md: no address, so source must be 'none' or the URL that was checked")
    if to:
        if not EMAIL_RE.fullmatch(to): errs.append(f"contact.md: invalid email '{to}'")
        host = to.split("@")[-1].lower()
        if not (domain and (host == domain or host.endswith("." + domain))) and not host.endswith(ATS_DOMAINS):
            errs.append(f"contact.md: {host} does not match company domain '{domain or '?'}' or a known ATS")
        posting = (folder / "posting.md").read_text(encoding="utf-8").lower() if (folder / "posting.md").exists() else ""
        conf, src = f.get("confidence"), f.get("source", "")
        if conf == "posting" and to.lower() not in posting:
            errs.append("contact.md: confidence 'posting' but the address is not in posting.md (never guess addresses)")
        if conf in ("official-hr", "general-contact"):
            sh = (urlparse(src).hostname or "").lower()
            if not (src.startswith("http") and domain and (sh == domain or sh.endswith("." + domain))):
                errs.append("contact.md: source must be a URL on the company's own domain")
        if conf == "none": errs.append("contact.md: an address cannot have confidence 'none'")
        em = folder / "email.md"
        if em.exists():
            et = em.read_text(encoding="utf-8")
            if not re.search(rf"^To:\s*{re.escape(to)}\s*$", et, re.M | re.I):
                errs.append(f"email.md: missing 'To: {to}' line")
            if errs: return errs                                     # no mailto until contact is valid
            subj = (re.search(r"^Subject:\s*(.+)$", et, re.M) or [None, ""])[1].strip()
            body = re.sub(r"^(To|Subject):.*$\n?", "", et, flags=re.M | re.I).strip()
            link = f"mailto:{to}?subject={quote(subj)}&body={quote(plain(body))}"
            line = f"mailto: {link}"
            txt = re.sub(r"^mailto:.*$", line, txt, flags=re.M) if re.search(r"^mailto:", txt, re.M) else txt.rstrip() + "\n" + line + "\n"
            with open(cpath, "w", encoding="utf-8", newline="\n") as fh: fh.write(txt)
            print("mailto link written to contact.md (attach the CV + letter PDFs manually)")
    return errs

# ---------------------------------------------------------------- diff
def cmd_diff(a):
    base = json.loads((ROOT / "profile" / "base_cv.json").read_text(encoding="utf-8"))
    cv = json.loads(Path(a.cv).read_text(encoding="utf-8"))
    out = []
    if base["header"]["title"] != cv["header"]["title"]:
        out.append(f'headline: "{base["header"]["title"]}" -> "{cv["header"]["title"]}"')
    if base.get("summary") != cv.get("summary"): out.append("summary: changed")
    for sec in ("experience", "projects"):
        b = {plain(x["text"]): x.get("facts") for e in base.get(sec, []) for x in e["bullets"]}
        c = [plain(x["text"]) for e in cv.get(sec, []) for x in e["bullets"]]
        bl = list(b)
        for t in c:
            if t not in b: out.append(f"{sec} + {t[:90]}…")
        for t in bl:
            if t not in c: out.append(f"{sec} - {t[:90]}…")
        common = [t for t in c if t in b]
        if common != [t for t in bl if t in common]: out.append(f"{sec}: order changed")
    bt = {e["title"] for e in base.get("projects", [])}; ct = {e["title"] for e in cv.get("projects", [])}
    out += [f"project removed: {t}" for t in sorted(bt - ct)] + [f"project added: {t}" for t in sorted(ct - bt)]
    bs = {s["label"]: s["text"] for s in base.get("skills", [])}
    out += [f"skills changed: {s['label']}" for s in cv.get("skills", []) if bs.get(s["label"]) != s["text"]]
    print("\n".join(out) if out else "no changes versus base_cv.json")

# ---------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("facts"); p.add_argument("--grep"); p.set_defaults(fn=cmd_facts)
    p = sp.add_parser("fact"); p.add_argument("ids", nargs="+"); p.set_defaults(fn=cmd_fact)
    p = sp.add_parser("fetch"); p.add_argument("source"); p.add_argument("--out", required=True); p.set_defaults(fn=cmd_fetch)
    p = sp.add_parser("build"); p.add_argument("cv"); p.add_argument("--out"); p.set_defaults(fn=cmd_build)
    p = sp.add_parser("ats"); p.add_argument("pdf"); p.add_argument("--keywords", required=True); p.set_defaults(fn=cmd_ats)
    p = sp.add_parser("letter"); p.add_argument("letter"); p.add_argument("--cv", required=True); p.set_defaults(fn=cmd_letter)
    p = sp.add_parser("diff"); p.add_argument("cv"); p.set_defaults(fn=cmd_diff)
    a = ap.parse_args(); a.fn(a)

if __name__ == "__main__":
    main()
