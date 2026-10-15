#!/usr/bin/env python3
"""Build paper/manuscript_full.docx from the manuscript source.

Resolves numbered citations from the compiled .bbl so Word numbering matches the PDF,
embeds the PNG figures, and injects the abstract and keywords that pandoc otherwise drops.
Run after the PDF has been compiled, since it needs the .bbl.
"""
import re, subprocess, sys, os
from pathlib import Path

PB = Path(__file__).resolve().parents[1]
PAPER = PB / "paper"
os.chdir(PAPER)
tex = (PAPER / "manuscript_full.tex").read_text()
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
tex = re.sub(r'\\cite\{([^}]*)\}', cite_repl, tex)

# --- figures: PDF -> embedded PNG ---
tex = re.sub(r'\\includegraphics(\[[^\]]*\])?\{(fig[0-9][^}]*)\.pdf\}',
             lambda m: '\\includegraphics' + (m.group(1) or '') + '{' + m.group(2) + '.png}', tex)

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

open('/tmp/main_docx.tex', 'w').write(tex)
rc = subprocess.call(['pandoc', '/tmp/main_docx.tex', '--number-sections',
                      f'--resource-path={PAPER}',
                      '-o', str(PAPER / 'manuscript_full.docx')])
print('references:', len(entries), '| docx build exit:', rc)
sys.exit(rc)
