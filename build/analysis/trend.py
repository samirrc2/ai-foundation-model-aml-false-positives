import csv, glob, math, random
from collections import defaultdict
from scipy import stats as sp
CAP="/Users/samirchincholikar/Desktop/NIW/Paper 4/capsule/data/capture"
NICE={"gemini_flash":"Gemini Flash","gemini_flash_lite":"Gemini Flash-Lite",
      "openai_4o_mini":"GPT-4o-mini","openai_41_mini":"GPT-4.1-mini","openai_4o":"GPT-4o"}
rows=[r for f in sorted(glob.glob(CAP+"/runs_full_*.csv")) for r in csv.DictReader(open(f)) if r.get("mode")=="REAL"]
V=defaultdict(lambda: defaultdict(list)); strat={}
for r in rows:
    if r["decision"]=="ERROR" or r["label"]!="benign": continue
    V[r["model_key"]][r["case_id"]].append(1 if r["decision"]=="flag" else 0)
    strat[r["case_id"]]=r["stratum"]
esc=lambda v: 1 if 2*sum(v)>=len(v) else 0
st =lambda v: 1 if sum(v)>len(v)/2 else 0
cases=sorted(set.intersection(*[set(V[m]) for m in V]))
print(f"n benign cases = {len(cases)}, strata = {len(set(strat.values()))}")

def mcn(a,b,rule):
    bb=sum(1 for c in cases if rule(V[a][c])==1 and rule(V[b][c])==0)
    cc=sum(1 for c in cases if rule(V[a][c])==0 and rule(V[b][c])==1)
    n=bb+cc; k=min(bb,cc)
    p=min(1.0,2*sum(sp.binom.pmf(i,n,0.5) for i in range(k+1))) if n else 1.0
    return bb,cc,p

print("\n=== ADJACENT-TIER paired McNemar (the trend test for a paired design) ===")
ADJ=[("OpenAI","openai_4o","openai_41_mini"),("OpenAI","openai_41_mini","openai_4o_mini"),
     ("Google","gemini_flash","gemini_flash_lite")]
for nm,rule in [("D4/strict",st),("escalate",esc)]:
    print(f"  -- {nm} --")
    for fam,a,b in ADJ:
        bb,cc,p=mcn(a,b,rule)
        print(f"     {fam:<7}{NICE[a]:<16}-> {NICE[b]:<18} b={bb:<4} c={cc:<4} "
              f"p={p:.3e}  p_bonf3={min(1,p*3):.3e}  direction={'lower->higher tier flags MORE' if cc>bb else 'REVERSED'}")

print("\n=== cluster-robust (8 typology strata) bootstrap CI on adjacent-tier FP difference, pp ===")
by=defaultdict(list)
for c in cases: by[strat[c]].append(c)
keys=sorted(by)
def cl_ci(a,b,rule,draws=2000,seed=4242):
    rng=random.Random(seed); vals=[]
    for _ in range(draws):
        rs=[]
        for _i in range(len(keys)): rs.extend(by[keys[rng.randrange(len(keys))]])
        d=100*(sum(rule(V[b][c]) for c in rs)-sum(rule(V[a][c]) for c in rs))/len(rs)
        vals.append(d)
    vals.sort(); return vals[int(.025*draws)], vals[int(.975*draws)-1]
for nm,rule in [("D4/strict",st),("escalate",esc)]:
    print(f"  -- {nm} --")
    for fam,a,b in ADJ:
        pt=100*(sum(rule(V[b][c]) for c in cases)-sum(rule(V[a][c]) for c in cases))/len(cases)
        lo,hi=cl_ci(a,b,rule)
        print(f"     {fam:<7}{NICE[b]:<18} minus {NICE[a]:<16} = {pt:+.1f} pp  cluster 95% CI [{lo:+.1f}, {hi:+.1f}]"
              f"  {'excludes 0' if lo>0 or hi<0 else 'INCLUDES 0'}")

print("\n=== cluster-robust permutation test of overall FP heterogeneity ===")
# permute model labels within each case (exchangeable under H0), resampling strata as clusters
def Qstat(rule, cs):
    ms=sorted(V); mat=[[rule(V[m][c]) for m in ms] for c in cs]
    k=len(ms); Cj=[sum(r[j] for r in mat) for j in range(k)]; Ri=[sum(r) for r in mat]
    Cb=sum(Cj)/k; den=k*sum(Ri)-sum(r*r for r in Ri)
    return ((k-1)*sum((c-Cb)**2 for c in Cj)/den) if den else 0.0
for nm,rule in [("D4/strict",st),("escalate",esc)]:
    obs=Qstat(rule,cases); rng=random.Random(99); ge=0; B=2000
    ms=sorted(V)
    for _ in range(B):
        rs=[]
        for _i in range(len(keys)): rs.extend(by[keys[rng.randrange(len(keys))]])
        mat=[]
        for c in rs:
            row=[rule(V[m][c]) for m in ms]; rng.shuffle(row); mat.append(row)
        k=len(ms); Cj=[sum(r[j] for r in mat) for j in range(k)]; Ri=[sum(r) for r in mat]
        Cb=sum(Cj)/k; den=k*sum(Ri)-sum(r*r for r in Ri)
        q=((k-1)*sum((cc-Cb)**2 for cc in Cj)/den) if den else 0.0
        if q>=obs: ge+=1
    print(f"  {nm:<10} observed Q={obs:.1f}   cluster-permutation p = {(ge+1)/(B+1):.2e}  ({ge}/{B} draws >= observed)")
