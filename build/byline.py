#!/usr/bin/env python3
"""The author byline: parse it from the manuscript source, and prove it survived into a .docx.

pandoc does not know Springer's \\author[n]{\\fnm{..} \\sur{..}} or \\affil[n]{\\orgname{..}}.
It drops what it cannot parse WITHOUT erroring, so \\maketitle renders the title alone and
every author silently disappears from the Word companion. The PDF is unaffected, so the fault
is invisible unless the built .docx is read back.

This module is imported by make_docx.py (which builds the byline) and by check_docx_byline.py
(which verifies it). One parser, so the builder and the gate cannot drift apart.
"""
import re
import sys
import zipfile
from pathlib import Path


# \author[1]{\fnm{Samir} \sur{Chincholikar}} nests braces, so the argument has to be matched by
# counting them. A non-greedy regex stops inside \fnm{..} and yields first names only -- which
# looks plausible in the output ("Samir, Robin") and is still wrong.
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
        arg, end = _arg_at(tex, m.end() - 1)
        out.append((arg, end, bool(m.group(1))))
    return out


def _names(block: str) -> str:
    """\\fnm{Samir} \\sur{Chincholikar} -> Samir Chincholikar."""
    parts = re.findall(r'\\(?:fnm|sur)\s*\{([^}]*)\}', block)
    if parts:
        return ' '.join(p.strip() for p in parts if p.strip())
    return re.sub(r'\s+', ' ', re.sub(r'\\[a-zA-Z]+\*?|[{}]', ' ', block)).strip()


def authors_in(tex: str):
    """(display name, email, is_corresponding) for each \\author, in source order."""
    people = []
    for arg, end, star in _macro_args(tex, 'author'):
        em = re.match(r'\s*\\email\s*\{([^}]*)\}', tex[end:])
        people.append((_names(arg), (em.group(1).strip() if em else ''), star))
    return people


def build_byline(tex: str) -> str:
    """LaTeX for the byline block, to be injected where pandoc can see it."""
    people = authors_in(tex)
    if not people:
        sys.exit('ERROR: no \\author found in the manuscript source -- refusing to build a '
                 'docx with no byline')
    out = '\\noindent\\textbf{' + ', '.join(n for n, _, _ in people) + '}\n\n'
    affils = _macro_args(tex, 'affil')
    if affils:
        a = re.sub(r'\s+', ' ', re.sub(r'\\[a-zA-Z]+\*?|[{}]', ' ', affils[0][0])).strip(' ,')
        if a:
            out += '\\noindent ' + a + '\n\n'
    for n, e, corr in people:
        if corr and e:
            out += '\\noindent Corresponding author: ' + n + ' (' + e + ')\n\n'
    return out


def docx_head(docx_path, chars: int = 4000) -> str:
    """Visible text from the start of a .docx. Raises if the file cannot be read."""
    xml = zipfile.ZipFile(docx_path).read('word/document.xml').decode('utf8', 'ignore')
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', xml))[:chars]


def missing_authors(docx_path, tex: str):
    """Authors whose name does not appear near the top of the built .docx.

    Every word of the name must appear, so a byline reading "Samir, Robin" -- the exact output
    of a non-greedy parse -- cannot pass for "Samir Chincholikar, Robin Chawla".
    """
    head = docx_head(docx_path)
    return [n for n, _, _ in authors_in(tex)
            if not (n.split() and all(w in head for w in n.split()))]


def assert_byline(docx_path, tex: str) -> int:
    """0 if every author is named near the top of the .docx, 2 otherwise. Never raises."""
    docx_path = Path(docx_path)
    try:
        missing = missing_authors(docx_path, tex)
    except Exception as exc:                       # noqa: BLE001 - report, do not mask
        print(f'   BYLINE CHECK: cannot read {docx_path.name}: {exc}')
        return 2
    if missing:
        print(f'   BYLINE CHECK FAILED: {docx_path.name} has no byline for: '
              f'{", ".join(missing)} -- do NOT submit this file')
        return 2
    print(f'   byline check: {docx_path.name} names all authors')
    return 0
