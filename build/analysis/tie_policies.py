"""Standalone recomputation of the P4 operating points under every tie policy.
Deliberately does NOT import the repository's own modules (con1 doctrine:
re-derive the estimator from its definition)."""
import csv, glob, math
from collections import defaultdict

CAP = "/Users/samirchincholikar/Desktop/NIW/Paper 4/capsule/data/capture"
NICE = {"gemini_flash":"Gemini Flash","gemini_flash_lite":"Gemini Flash-Lite",
        "openai_4o_mini":"GPT-4o-mini","openai_41_mini":"GPT-4.1-mini","openai_4o":"GPT-4o"}
ORDER = ["gemini_flash","openai_4o","openai_41_mini","gemini_flash_lite","openai_4o_mini"]

rows=[]
for f in sorted(glob.glob(CAP+"/runs_full_*.csv")):
    for r in csv.DictReader(open(f)):
        if r.get("mode")=="REAL": rows.append(r)
print(f"total REAL rows: {len(rows)}")
err=[r for r in rows if r["decision"]=="ERROR"]
print(f"ERROR rows: {len(err)}  ({100*len(err)/len(rows):.2f}%)")

# votes[model][label][case] = list of 0/1
votes=defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
for r in rows:
    if r["decision"]=="ERROR": continue
    votes[r["model_key"]][r["label"]][r["case_id"]].append(1 if r["decision"]=="flag" else 0)

# ---- distribution of valid-call counts, and tie census -------------------
print("\n=== valid calls per model-case, and ties (2-2 splits) ===")
print(f"{'model':<18}{'k=4':>6}{'other k':>9}{'benign ties':>13}{'susp ties':>11}")
tie_tab={}
for m in ORDER:
    kc=defaultdict(int); tb=ts=0
    for lab in ("benign","suspicious"):
        for c,v in votes[m][lab].items():
            kc[len(v)]+=1
            if 2*sum(v)==len(v):
                if lab=="benign": tb+=1
                else: ts+=1
    other=sum(n for k,n in kc.items() if k!=4)
    tie_tab[m]=(tb,ts)
    print(f"{NICE[m]:<18}{kc.get(4,0):>6}{other:>9}{tb:>13}{ts:>11}")
print(f"{'TOTAL':<18}{'':>6}{'':>9}{sum(v[0] for v in tie_tab.values()):>13}"
      f"{sum(v[1] for v in tie_tab.values()):>11}")

# ---- tie policies --------------------------------------------------------
def published(v, lab):                       # D4: label-dependent
    return (1 if sum(v) > len(v)/2 else 0) if lab=="benign" else (1 if 2*sum(v)>=len(v) else 0)
def escalate(v, lab):  return 1 if 2*sum(v) >= len(v) else 0      # ties -> flag
def strict(v, lab):    return 1 if sum(v) > len(v)/2 else 0        # ties -> no flag
def unanimous(v, lab): return 1 if sum(v)==len(v) else 0
def abstain(v, lab):
    return None if 2*sum(v)==len(v) else (1 if 2*sum(v)>len(v) else 0)

POL=[("D4 as published (label-DEPENDENT)",published),
     ("ties -> flag / escalate (label-indep)",escalate),
     ("ties -> no flag / strict majority (label-indep)",strict),
     ("ties -> abstention, dropped (label-indep)",abstain),
     ("unanimity required to flag (label-indep)",unanimous)]

def rates(rule):
    out={}
    for m in ORDER:
        fp=fpn=0
        for c,v in votes[m]["benign"].items():
            d=rule(v,"benign")
            if d is None: continue
            fpn+=1; fp+=d
        ms=msn=0
        for c,v in votes[m]["suspicious"].items():
            d=rule(v,"suspicious")
            if d is None: continue
            msn+=1; ms+=(1-d)
        out[m]=(fp,fpn,ms,msn)
    return out

print("\n=== FALSE-POSITIVE RATE (%) on the 300 legitimate cases ===")
hdr=f"{'policy':<48}" + "".join(f"{NICE[m][:13]:>14}" for m in ORDER) + f"{'spread pp':>11}"
print(hdr); print("-"*len(hdr))
store={}
for name,rule in POL:
    r=rates(rule); store[name]=r
    vals=[100*r[m][0]/r[m][1] for m in ORDER]
    print(f"{name:<48}" + "".join(f"{v:>14.1f}" for v in vals) + f"{max(vals)-min(vals):>11.1f}")

print("\n=== MISS RATE (%) on the 300 suspicious cases ===")
print(hdr); print("-"*len(hdr))
for name,rule in POL:
    r=store[name]
    vals=[100*r[m][2]/r[m][3] for m in ORDER]
    print(f"{name:<48}" + "".join(f"{v:>14.1f}" for v in vals) + f"{max(vals)-min(vals):>11.1f}")

print("\n=== denominators retained (benign / suspicious) ===")
for name,rule in POL:
    r=store[name]
    print(f"  {name:<48}" + " ".join(f"{r[m][1]}/{r[m][3]}" for m in ORDER))
