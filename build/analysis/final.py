import csv, glob, math, random
from collections import defaultdict
from scipy import stats as sp
CAP="/Users/samirchincholikar/Desktop/NIW/Paper 4/capsule/data/capture"
NICE={"gemini_flash":"Gemini Flash","gemini_flash_lite":"Gemini Flash-Lite",
      "openai_4o_mini":"GPT-4o-mini","openai_41_mini":"GPT-4.1-mini","openai_4o":"GPT-4o"}
ORDER=["gemini_flash","openai_4o","openai_41_mini","gemini_flash_lite","openai_4o_mini"]
rows=[r for f in sorted(glob.glob(CAP+"/runs_full_*.csv")) for r in csv.DictReader(open(f)) if r.get("mode")=="REAL"]
V=defaultdict(lambda: defaultdict(lambda: defaultdict(list))); strat={}
for r in rows:
    if r["decision"]=="ERROR": continue
    V[r["model_key"]][r["label"]][r["case_id"]].append(1 if r["decision"]=="flag" else 0)
    if r["label"]=="benign": strat[r["case_id"]]=r["stratum"]
esc=lambda v: 1 if 2*sum(v)>=len(v) else 0
st =lambda v: 1 if sum(v)>len(v)/2 else 0
bc=sorted(set.intersection(*[set(V[m]["benign"]) for m in ORDER]))
sc=sorted(set.intersection(*[set(V[m]["suspicious"]) for m in ORDER]))

# --- repo's OWN cluster bootstrap: resample whole strata with replacement ---
def repo_cluster_ci(rule, draws=2000, seed=4242):
    by=defaultdict(list)
    for c in bc: by[strat[c]].append(c)
    keys=sorted(by); n=len(keys); rng=random.Random(seed); vals=[]
    for _ in range(draws):
        rs=[]
        for _i in range(n): rs.extend(by[keys[rng.randrange(n)]])
        fr=[100*sum(rule(V[m]["benign"][c]) for c in rs)/len(rs) for m in ORDER]
        vals.append(max(fr)-min(fr))
    vals.sort()
    return vals[int(.025*len(vals))], vals[int(.975*len(vals))-1], n

print("=== FP spread + repo-definition cluster bootstrap CI (2000 draws, seed 4242) ===")
for nm,rule in [("D4 as published / strict-majority",st),("ties->flag escalate (label-indep)",esc)]:
    fr=[100*sum(rule(V[m]["benign"][c]) for c in bc)/len(bc) for m in ORDER]
    lo,hi,ns=repo_cluster_ci(rule)
    print(f"  {nm:<36} {max(fr)-min(fr):.1f} pp   95% CI [{lo:.1f}, {hi:.1f}]   strata={ns}")

# --- Cochran Q with survival function (no underflow) ---
def Qp(rule):
    mat=[[rule(V[m]["benign"][c]) for m in ORDER] for c in bc]
    k=len(ORDER); Cj=[sum(r[j] for r in mat) for j in range(k)]; Ri=[sum(r) for r in mat]
    Cb=sum(Cj)/k; num=(k-1)*sum((c-Cb)**2 for c in Cj); den=k*sum(Ri)-sum(r*r for r in Ri)
    Q=num/den; return Q, sp.chi2.sf(Q,k-1)
print("\n=== Cochran's Q, p via chi2.sf (survival fn) ===")
for nm,rule in [("D4 as published / strict-majority",st),("ties->flag escalate (label-indep)",esc)]:
    Q,p=Qp(rule); print(f"  {nm:<36} Q={Q:.3f}  df=4  p={p:.3e}")
print("  NOTE deposited stats_tests.json records p=0.0 for Q=131.553 because")
print("       classification.py uses 1-chi2.cdf() which underflows; sf() gives 1.81e-27.")

# --- Cochran-Armitage trend across OpenAI tiers (3 ordered tiers) ---
print("\n=== monotone trend in FP rate across model tier ===")
for fam,ms,sc_ in [("OpenAI",["openai_4o","openai_41_mini","openai_4o_mini"],[0,1,2]),
                   ("Google",["gemini_flash","gemini_flash_lite"],[0,1])]:
    for nm,rule in [("D4/strict",st),("escalate",esc)]:
        xs=[]; ys=[]
        for s,m in zip(sc_,ms):
            k=sum(rule(V[m]["benign"][c]) for c in bc)
            xs += [s]*len(bc); ys += [1]*k + [0]*(len(bc)-k)
        N=len(ys); T=sum(x*y for x,y in zip(xs,ys)); R=sum(ys)
        xb=sum(xs)/N; Sxx=sum((x-xb)**2 for x in xs); pbar=R/N
        var=pbar*(1-pbar)*Sxx; z=(T-R*xb)/math.sqrt(var) if var>0 else float('nan')
        rates=[100*sum(rule(V[m]["benign"][c]) for c in bc)/len(bc) for m in ms]
        print(f"  {fam:<7} {nm:<10} rates={[f'{r:.1f}' for r in rates]}  "
              f"Cochran-Armitage z={z:.2f}  p={2*sp.norm.sf(abs(z)):.3e}")

# --- prevalence sweep (R2 #8) ---
print("\n=== alert volume per 1,000,000 transactions/day across prevalence ===")
rec={m: sum(esc(V[m]["suspicious"][c]) for c in sc)/len(sc) for m in ORDER}
fpr={m: sum(st(V[m]["benign"][c]) for c in bc)/len(bc) for m in ORDER}
print(f"{'prevalence':<12}" + "".join(f"{NICE[m][:12]:>13}" for m in ORDER) + f"{'max/min':>9}")
for pi in (0.0001,0.0005,0.001,0.002,0.005,0.01):
    a=[1_000_000*(pi*rec[m]+(1-pi)*fpr[m]) for m in ORDER]
    print(f"{pi*100:>9.2f}%  " + "".join(f"{x:>13,.0f}" for x in a) + f"{max(a)/min(a):>9.1f}")
print("\n  precision (%) at each prevalence, same order:")
for pi in (0.0001,0.0005,0.001,0.002,0.005,0.01):
    pr=[100*pi*rec[m]/(pi*rec[m]+(1-pi)*fpr[m]) for m in ORDER]
    print(f"{pi*100:>9.2f}%  " + "".join(f"{x:>13.2f}" for x in pr))
print("\n  ordering of models by alert volume identical at every prevalence:",
      all([sorted(range(5), key=lambda i:[1_000_000*(pi*rec[ORDER[i]]+(1-pi)*fpr[ORDER[i]])][0])
           ==sorted(range(5), key=lambda i:[1_000_000*(0.001*rec[ORDER[i]]+0.999*fpr[ORDER[i]])][0])
           for pi in (0.0001,0.0005,0.001,0.002,0.005,0.01)]))
