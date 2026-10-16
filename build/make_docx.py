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

MARK_LEGEND = (
    "\\section*{Marked copy, revision 1}\n"
    "Text added since the original submission is highlighted. Text removed since the original "
    "submission is shown struck through at the point where it stood. Table bodies are "
    "reproduced in final form without internal marks. A table or figure that is new or revised "
    "is labelled in its caption.\n")


def build(tex, out_name, tracked=False):
    tex = re.sub(r'\\cite\{([^}]*)\}', cite_repl, tex)

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

    # --- inject abstract + keywords into the body (pandoc drops the macros) ---
    abstract = re.search(r'\\abstract\{(.*?)\}\s*\\keywords', tex, re.S).group(1).strip()
    keywords = re.search(r'\\keywords\{([^}]*)\}', tex).group(1).strip()
    block = ('\\maketitle\n\n\\section*{Abstract}\n' + abstract +
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
    return rc


rc = build(SRC, 'manuscript_full.docx')
marked = PAPER / "_marked.tex"
if marked.exists():
    rc |= build(marked.read_text(), 'manuscript_full_tracked.docx', tracked=True)
else:
    print('   WARNING: _marked.tex absent -- tracked docx NOT built '
          '(run build/build_highlighted.sh first)')
    rc = rc or 2
print('references:', len(entries), '| docx build exit:', rc)
sys.exit(rc)
