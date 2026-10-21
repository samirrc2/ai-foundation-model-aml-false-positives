#!/usr/bin/env python3
"""Build the .docx companions from the manuscript sources.

  manuscript_full.docx           <- manuscript_full.tex    clean
  manuscript_full_tracked.docx   <- _marked.tex            tracked changes

Resolves numbered citations from the compiled .bbl so Word numbering matches the PDF,
embeds the PNG figures, and injects the abstract and keywords that pandoc otherwise drops.
Run after the PDFs have been compiled, since it needs the .bbl and _marked.tex.

The tracked copy needs one rewrite that is easy to miss and silent when wrong: pandoc does not
know soul's \\texthl, so it DROPS \\HLtext without any error, which would delete every added run
from the tracked document and leave a file that looks clean and is not. \\HLtext, \\HLcode and
\\HLhead are therefore rewritten to \\hl and \\HLdel to \\sout, both of which pandoc maps to real
docx highlight and strikethrough formatting. The injected LaTeX preamble is stripped whole,
because the multi-line \\HLlegend definition stops pandoc's parser.
"""
import re, subprocess, sys, os
from pathlib import Path

PB = Path(__file__).resolve().parents[1]
PAPER = PB / "paper"
os.chdir(PAPER)
SRC = (PAPER / "manuscript_full.tex").read_text()
bbl_path = PAPER / "manuscript_full.bbl"
if not bbl_path.exists():
    sys.exit("ERROR: manuscript_full.bbl missing -- compile the PDF first")
bbl = bbl_path.read_text()

# --- parse compiled bibliography into ordered (key, body); number = position ---
zone = bbl.split(r'\bibcommenthead', 1)[-1]
entries = []
for chunk in re.split(r'\\bibitem\[[^\]]*\]\{', zone)[1:]:
    key = chunk[:chunk.index('}')]
    body = chunk[chunk.index('}') + 1:].split(r'\end{thebibliography}')[0]
    body = re.sub(r'\s+', ' ', body).strip()
    body = re.sub(r'\\doi\{([^}]*)\}',
                  lambda m: r'\url{https://doi.org/' + m.group(1) + '}', body)
    entries.append((key, body))
keymap = {k: i + 1 for i, (k, _) in enumerate(entries)}

# --- resolve \cite{...} -> [n, m] using the bibliography numbering ---
def cite_repl(m):
    nums = sorted(keymap[k.strip()] for k in m.group(1).split(',') if k.strip() in keymap)
    return '[' + ', '.join(map(str, nums)) + ']'


# --- byline: rebuild the author block pandoc cannot see -------------------------------------
# \author[1]{\fnm{Samir} \sur{Chincholikar}} nests braces, so the argument has to be matched by
# counting them. A non-greedy regex stops inside \fnm{..} and yields first names only.
def _arg_at(s: str, i: int):
    """Text of the {...} group starting at s[i] == '{', plus the index just past it."""
    depth, j = 0, i
    while j < len(s):
        if s[j] == '{':
            depth += 1
        elif s[j] == '}':
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    return '', len(s)


def _macro_args(tex: str, macro: str):
    """Every argument of \\macro / \\macro* , skipping an optional [..]; with its end index."""
    out = []
    for m in re.finditer(r'\\' + macro + r'(\*?)(\[[^\]]*\])?\s*\{', tex):
        star = bool(m.group(1))
        arg, end = _arg_at(tex, m.end() - 1)
        out.append((arg, end, star))
    return out


def _names(block: str) -> str:
    """\\fnm{Samir} \\sur{Chincholikar} -> Samir Chincholikar."""
    parts = re.findall(r'\\(?:fnm|sur)\s*\{([^}]*)\}', block)
    if parts:
        return ' '.join(p.strip() for p in parts if p.strip())
    return re.sub(r'\s+', ' ', re.sub(r'\\[a-zA-Z]+\*?|[{}]', ' ', block)).strip()


def authors_in(tex: str):
    """(display name, email, is_corresponding) for each \\author in source order."""
    people = []
    for arg, end, star in _macro_args(tex, 'author'):
        em = re.match(r'\s*\\email\s*\{([^}]*)\}', tex[end:])
        people.append((_names(arg), (em.group(1).strip() if em else ''), star))
    return people


def build_byline(tex: str) -> str:
    people = authors_in(tex)
    if not people:
        sys.exit('ERROR: no \\author found in the manuscript source -- refusing to build a '
                 'docx with no byline')
    out = '\\noindent\\textbf{' + ', '.join(n for n, _, _ in people) + '}\n\n'
    affils = _macro_args(tex, 'affil')
    if affils:
        a = re.sub(r'\\[a-zA-Z]+\*?|[{}]', ' ', affils[0][0])
        a = re.sub(r'\s+', ' ', a).strip(' ,')
        if a:
            out += '\\noindent ' + a + '\n\n'
    for n, e, corr in people:
        if corr and e:
            out += '\\noindent Corresponding author: ' + n + ' (' + e + ')\n\n'
    return out

MARK_LEGEND = (
    "\\section*{Marked copy, revision 1}\n"
    "Text added since the original submission is highlighted. Text removed since the original "
    "submission is shown struck through at the point where it stood. Table bodies are "
    "reproduced in final form without internal marks. A table or figure that is new or revised "
    "is labelled in its caption.\n")


def assert_byline(docx_path, tex: str) -> int:
    """Fail loudly if a built .docx lost its authors. pandoc drops what it cannot parse
    without erroring, so the only safe check is to read the built file back."""
    import zipfile
    try:
        xml = zipfile.ZipFile(docx_path).read('word/document.xml').decode('utf8', 'ignore')
    except Exception as exc:                       # noqa: BLE001 - report, do not mask
        print(f'   BYLINE CHECK: cannot read {docx_path.name}: {exc}')
        return 2
    text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', xml))
    head = text[:4000]                             # byline must be near the top, not a citation
    # every word of the name must appear, so "Samir" alone cannot pass for "Samir Chincholikar"
    missing = [n for n, _, _ in authors_in(tex)
               if not (n.split() and all(w in head for w in n.split()))]
    if missing:
        print(f'   BYLINE CHECK FAILED: {docx_path.name} has no byline for: '
              f'{", ".join(missing)} -- do NOT submit this file')
        return 2
    print(f'   byline check: {docx_path.name} names all authors')
    return 0


def build(tex, out_name, tracked=False):
    tex = re.sub(r'\\cite\{([^}]*)\}', cite_repl, tex)

    # pdfTeX-only typesetting directives. pandoc warns "Could not load include file
    # glyphtounicode.tex" and they affect the PDF text layer, not the docx, so drop them.
    tex = tex.replace(r"\input{glyphtounicode}", "").replace(r"\pdfgentounicode=1", "")

    # --- figures: PDF -> embedded PNG ---
    tex = re.sub(r'\\includegraphics(\[[^\]]*\])?\{(fig[0-9][^}]*)\.pdf\}',
                 lambda m: '\\includegraphics' + (m.group(1) or '') + '{' + m.group(2) + '.png}', tex)

    if tracked:
        # Strip the injected marking preamble whole. The \HLlegend definition spans lines and
        # pandoc stops at it, which would truncate the document rather than fail loudly.
        tex = re.sub(r'\\usepackage\{soul\}.*?\\par\\vspace\{6pt\}\}\n', '', tex, flags=re.S)
        tex = tex.replace('\n\\HLlegend\n', '\n' + MARK_LEGEND, 1).replace('\\HLlegend', '')
        # \HLtext/\HLcode/\HLhead -> \hl, \HLdel -> \sout. Without this pandoc silently
        # discards every addition, because it does not know soul's \texthl.
        tex = re.sub(r'\\HL(?:text|code|head)\{', r'\\hl{', tex)
        tex = re.sub(r'\\HLdel\{', r'\\sout{', tex)
        tex = re.sub(r'\\HLtag\{([^}]*)\}', r'[\1] ', tex)

    # --- inject byline + abstract + keywords into the body (pandoc drops the macros) ---
    # pandoc does not know Springer's \author[n]{\fnm{..} \sur{..}} or \affil[n]{\orgname{..}},
    # so \maketitle renders the TITLE ONLY and every author silently disappears -- the same
    # silent-drop class as \HLtext above. A manuscript submitted without its authors is
    # returned by the journal, so the byline is rebuilt here and asserted after the build.
    byline = build_byline(tex)
    abstract = re.search(r'\\abstract\{(.*?)\}\s*\\keywords', tex, re.S).group(1).strip()
    keywords = re.search(r'\\keywords\{([^}]*)\}', tex).group(1).strip()
    block = ('\\maketitle\n\n' + byline + '\\section*{Abstract}\n' + abstract +
             '\n\n\\noindent\\textbf{Keywords:} ' + keywords + '\n')
    tex = tex.replace('\\maketitle', block, 1)

    # --- references as a numbered list pandoc will render ---
    refs = '\\section*{References}\n\\begin{enumerate}\n' + \
           '\n'.join('\\item ' + b for _, b in entries) + '\n\\end{enumerate}\n'
    tex = re.sub(r'\\bibliography\{references_discover\}', lambda m: refs, tex)

    tmp = f'/tmp/{out_name}.tex'
    open(tmp, 'w').write(tex)
    rc = subprocess.call(['pandoc', tmp, '--number-sections',
                          f'--resource-path={PAPER}',
                          '-o', str(PAPER / out_name)])
    print(f'   {out_name}: pandoc exit {rc}')
    if rc == 0:
        rc |= assert_byline(PAPER / out_name, tex)
    return rc


# The cover letter's .docx was previously produced by hand and therefore went stale the moment
# the letter changed -- exactly the hand-maintained duplicate this build exists to prevent.
def build_letter(stem):
    src = PAPER / f'{stem}.tex'
    if not src.exists():
        print(f'   WARNING: {stem}.tex absent, {stem}.docx NOT rebuilt')
        return 2
    tex = src.read_text()
    tex = tex.replace(r"\input{glyphtounicode}", "").replace(r"\pdfgentounicode=1", "")
    tmp = f'/tmp/{stem}_docx.tex'
    open(tmp, 'w').write(tex)
    rc = subprocess.call(['pandoc', tmp, f'--resource-path={PAPER}', '-o', str(PAPER / f'{stem}.docx')])
    print(f'   {stem}.docx: pandoc exit {rc}')
    return rc


rc = build(SRC, 'manuscript_full.docx')
rc |= build_letter('cover_letter')
marked = PAPER / "_marked.tex"
if marked.exists():
    rc |= build(marked.read_text(), 'manuscript_full_tracked.docx', tracked=True)
else:
    print('   WARNING: _marked.tex absent -- tracked docx NOT built '
          '(run build/build_highlighted.sh first)')
    rc = rc or 2
print('references:', len(entries), '| docx build exit:', rc)
sys.exit(rc)
