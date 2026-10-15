import csv, glob, math
from collections import defaultdict
from itertools import combinations
try:
    from scipy import stats as sp; HAVE=True
except Exception: HAVE=False

CAP="/Users/samirchincholikar/Desktop/NIW/Paper 4/capsule/data/capture"
NICE={"gemini_flash":"Gemini Flash","gemini_flash_lite":"Gemini Flash-Lite",
      "openai_4o_mini":"GPT-4o-mini","openai_41_mini":"GPT-4.1-mini","openai_4o":"GPT-4o"}
ORDER=["gemini_flash","openai_4o","openai_41_mini","gemini_flash_lite","openai_4o_mini"]
rows=[r for f in sorted(glob.glob(CAP+"/runs_full_*.csv")) for r in csv.DictReader(open(f)) if r.get("mode")=="REAL"]

# --- 1. exact k distribution + where the 120 extra calls sit ---------------
print("=== valid-call count k per model-case ===")
for m in ORDER:
    kc=defaultdict(int)
    for lab in ("benign","suspicious"):
        d=defaultdict(list)
        for r in rows:
            if r["model_key"]==m and r["label"]==lab and r["decision"]!="ERROR": d[r["case_id"]].append(1)
        for c,v in d.items(): kc[len(v)]+=1
    print(f"  {NICE[m]:<18} " + "  ".join(f"k={k}:{n}" for k,n in sorted(kc.items())))
raw=defaultdict(int); errs=defaultdict(int)
for r in rows:
    raw[r["model_key"]]+=1
    if r["decision"]=="ERROR": errs[r["model_key"]]+=1
print("\n=== raw rows / ERRORs per model ===")
for m in ORDER: print(f"  {NICE[m]:<18} rows={raw[m]:<6} errors={errs[m]}")
print(f"  {'TOTAL':<18} rows={sum(raw.values())}  errors={sum(errs.values())}")

votes=defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
vs=defaultdict(lambda: defaultdict(lambda: defaultdict(list)))   # by (variant,seed)
for r in rows:
    if r["decision"]=="ERROR": continue
    f=1 if r["decision"]=="flag" else 0
    votes[r["model_key"]][r["label"]][r["case_id"]].append(f)
    vs[(r["prompt_variant"],r["seed_index"])][r["model_key"]][r["label"]+"|"+r["case_id"]].append(f)

esc=lambda v: 1 if 2*sum(v)>=len(v) else 0
strict=lambda v: 1 if sum(v)>len(v)/2 else 0

# --- 2. Cochran Q + McNemar under each label-independent rule -------------
def qtest(rule):
    cases=sorted(set.intersection(*[set(votes[m]["benign"]) for m in ORDER]))
    mat=[[rule(votes[m]["benign"][c]) for m in ORDER] for c in cases]
    k=len(ORDER); Cj=[sum(r[j] for r in mat) for j in range(k)]
    Ri=[sum(r) for r in mat]; Cb=sum(Cj)/k
    num=(k-1)*sum((c-Cb)**2 for c in Cj); den=k*sum(Ri)-sum(r*r for r in Ri)
    Q=num/den if den else 0.0
    p=(1-sp.chi2.cdf(Q,k-1)) if HAVE else None
    return Q,k-1,p,len(cases),mat,cases
print("\n=== Cochran's Q on the 300 legitimate cases (H0: equal FP rates) ===")
for nm,rule in [("D4 / strict majority (FP side identical)",strict),("ties -> flag (escalate)",esc)]:
    Q,df,p,n,mat,cases=qtest(rule)
    print(f"  {nm:<42} Q={Q:.1f}  df={df}  p={p:.3e}  n={n}")
print("\n=== pairwise McNemar exact, ties->flag (escalate), Bonferroni x10 ===")
Q,df,p,n,mat,cases=qtest(esc)
pos={m:i for i,m in enumerate(ORDER)}
worst=0
for a,b in combinations(ORDER,2):
    bb=sum(1 for i,c in enumerate(cases) if mat[i][pos[a]]==1 and mat[i][pos[b]]==0)
    cc=sum(1 for i,c in enumerate(cases) if mat[i][pos[a]]==0 and mat[i][pos[b]]==1)
    tot=bb+cc; kk=min(bb,cc)
    pe=min(1.0,2*sum(sp.binom.pmf(i,tot,0.5) for i in range(kk+1))) if (tot and HAVE) else (1.0 if not tot else None)
    pb=min(1.0,pe*10); worst=max(worst,pb)
    print(f"  {NICE[a]:<18} vs {NICE[b]:<18} b={bb:<4} c={cc:<4} p={pe:.3e}  p_bonf={pb:.3e}")
print(f"  -> largest Bonferroni-adjusted p across all 10 pairs: {worst:.3e}")

# --- 3. cluster bootstrap of the FP spread over the 8 typology strata -----
strata={}
for r in rows:
    if r["label"]=="benign": strata[r["case_id"]]=r["stratum"]
import random
def spread_ci(rule,B=10000,seed=20260713):
    rnd=random.Random(seed)
    bc=sorted(set.intersection(*[set(votes[m]["benign"]) for m in ORDER]))
    by=defaultdict(list)
    for c in bc: by[strata[c]].append(c)
    keys=sorted(by); out=[]
    for _ in range(B):
        samp=[c for k in keys for c in (rnd.choice(by[k]) for _ in range(len(by[k])))]
        vals=[100*sum(rule(votes[m]["benign"][c]) for c in samp)/len(samp) for m in ORDER]
        out.append(max(vals)-min(vals))
    out.sort(); return out[int(.025*B)], out[int(.975*B)]
print("\n=== FP spread (pp) with cluster bootstrap 95% CI over benign strata ===")
for nm,rule in [("D4 / strict majority",strict),("ties -> flag (escalate)",esc)]:
    bc=sorted(set.intersection(*[set(votes[m]["benign"]) for m in ORDER]))
    vals=[100*sum(rule(votes[m]["benign"][c]) for c in bc)/len(bc) for m in ORDER]
    lo,hi=spread_ci(rule)
    print(f"  {nm:<28} spread={max(vals)-min(vals):.1f} pp   95% CI [{lo:.1f}, {hi:.1f}]  (n strata={len(set(strata.values()))})")

# --- 4. the four single-call deployable configurations --------------------
print("\n=== single-call configurations (no aggregation at all) ===")
cfgs=sorted(vs)
print(f"{'config':<22}" + "".join(f"{NICE[m][:13]:>14}" for m in ORDER) + f"{'spread':>9}")
for cfg in cfgs:
    fp=[]
    for m in ORDER:
        d=vs[cfg][m]; k=n=0
        for key,v in d.items():
            if key.startswith("benign|"): n+=1; k+=v[0]
        fp.append(100*k/n if n else float('nan'))
    print(f"{str(cfg):<22}" + "".join(f"{v:>14.1f}" for v in fp) + f"{max(fp)-min(fp):>9.1f}")
# pooled call level
print(f"\n{'pooled call-level':<22}", end="")
pf=[]
for m in ORDER:
    k=n=0
    for r in rows:
        if r["model_key"]==m and r["label"]=="benign" and r["decision"]!="ERROR":
            n+=1; k+= (1 if r["decision"]=="flag" else 0)
    pf.append(100*k/n); print(f"{100*k/n:>14.1f}", end="")
print(f"{max(pf)-min(pf):>9.1f}")
