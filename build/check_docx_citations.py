"""Reject any citation number that renders INSIDE an em-dash aside in the converted
Word file (Reviewer 2, minor point 13). The compiled PDF hides this defect, so the
DOCX is the artifact that must be checked.
Exit 0 clean / 1 defect found / 2 could-not-check."""
import re, sys, zipfile
from pathlib import Path

DOCX = Path(__file__).resolve().parents[1] / "paper" / "manuscript_full.docx"

try:
    xml = zipfile.ZipFile(DOCX).read("word/document.xml").decode("utf-8", "replace")
except Exception as e:
    print(f"COULD NOT CHECK: {e}"); sys.exit(2)

text = re.sub(r"<[^>]+>", "", re.sub(r"</w:p>", "\n", xml))
text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
if len(text) < 20000:
    print(f"COULD NOT CHECK: extracted only {len(text)} chars from {DOCX.name}"); sys.exit(2)

EM = "—"
# A bracketed reference number sitting BETWEEN two em dashes, i.e. inside the aside.
# NOTE: a citation immediately BEFORE an opening em dash ("models [8, 9]---trained ...")
# is the correct placement and must NOT be flagged. An earlier version of this check
# also matched that form and would have forced a wrong fix.
bad = re.findall(EM + r"[^" + EM + r"]{0,200}\[\d+[^\]]{0,40}\]" + EM, text)

print(f"docx                       : {DOCX.name}")
print(f"em dashes found            : {text.count(EM)}")
print(f"citations inside an aside  : {len(bad)}")
for b in dict.fromkeys(bad):
    print("  DEFECT:", repr(b[:120]))
sys.exit(1 if bad else 0)
