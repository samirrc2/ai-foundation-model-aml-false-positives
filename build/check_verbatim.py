"""Verify every reviewer sentence in reviewer_comments_verbatim.txt survives into
the compiled letter. Exit 0 pass, 1 fail, 2 could-not-check."""
import re, sys, unicodedata
from pathlib import Path
from pypdf import PdfReader

PB = Path(__file__).resolve().parents[1]

def norm(s):
    s = unicodedata.normalize("NFKD", s)
    for a,b in [("ﬁ","fi"),("ﬂ","fl"),("ﬀ","ff"),("’","'"),("\u00d7","x"),("\u2212","-"),
                ("‘","'"),("“",'"'),("”",'"'),("—","-"),
                ("–","-"),("−","-"),(" "," ")]:
        s = s.replace(a,b)
    s = s.replace("-","").replace("`","'").replace("''",'"')
    return re.sub(r"[^a-z0-9%.]+","", s.lower())

try:
    pages=[re.sub(r"\s*\d+\s*$","",(p.extract_text() or "")) for p in PdfReader(str(PB / "paper/response_to_reviewers.pdf")).pages]
    pdf = norm("".join(pages))
    raw = open(str(PB / "paper/reviewer_comments_verbatim.txt")).read()
except Exception as e:
    print(f"COULD NOT CHECK: {e}"); sys.exit(2)
if len(pdf) < 5000:
    print(f"COULD NOT CHECK: pdf text only {len(pdf)} chars"); sys.exit(2)

# reviewer prose = everything outside headers/banners
blocks = re.split(r"={10,}", raw)
# Banner blocks at the head of the referee file, matched by shape rather than by their
# literal text: the journal name and the submission identifier do not belong in source
# that ships in the public archive.
sent = []
SKIP = re.compile(r"^(RAW\s|Submission\s|Discover\s|DO NOT EDIT)", re.I)
for b in blocks:
    b = b.strip()
    if not b or b.isupper() or SKIP.match(b): continue
    for s in re.split(r"(?<=[.;:])\s+", b.replace("\n"," ")):
        s = s.strip()
        # a leading "-" marks the signature line in the referee file
        if len(s) > 45 and not s.startswith("-") \
           and not re.match(r"^(EDITOR|REVIEWER|RAW)\b", s): sent.append(s)

miss = [s for s in sent if norm(s) not in pdf]
print(f"reviewer sentences checked : {len(sent)}")
print(f"missing from compiled PDF  : {len(miss)}")
for s in miss: print("  MISSING:", s[:110])
sys.exit(1 if miss else 0)
