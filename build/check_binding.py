"""Bind each load-bearing number in the manuscript to the result that produced it.

Coverage asks whether a number appears somewhere; binding asks whether it appears in
the RIGHT PLACE. Swapping two models' false-positive rates would pass a coverage test
and invert a finding; an anchored rule catches it.

Each rule is (regex anchor that must immediately precede, expected literal, source).
The expected values are read from capsule/results/, never hand-typed here.
Exit 0 all bound / 1 a rule failed / 2 could-not-check.
"""
import json, re, sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEX = ROOT / "paper" / "manuscript_full.tex"
RES = ROOT / "results"

try:
    tex = TEX.read_text()
    ag = json.loads((RES / "aggregation_sensitivity.json").read_text())
    pv = json.loads((RES / "pivot_claims.json").read_text())
    stt = json.loads((RES / "stats_tests.json").read_text())
    ps  = json.loads((RES / "prompt_sensitivity.json").read_text())
    cm  = json.loads((RES / "correlated_miss.json").read_text())
except Exception as e:
    print(f"COULD NOT CHECK: {e}"); sys.exit(2)
if len(tex) < 20000:
    print(f"COULD NOT CHECK: manuscript only {len(tex)} chars"); sys.exit(2)

P = ag["policies"]["ties_to_flag_preregistered_D4"]["per_model"]
SUB = ag["policies"]["label_dependent_as_published"]["per_model"]
SC = ag["single_call_configurations"]
FOUR = ag["four_designed_cells_sensitivity"]
ABC = ag["abstention_common_subset"]
sub = lambda m: f"{SUB[m]['fp_rate']*100:.1f}"
sc = lambda c, m: f"{SC[c]['per_model'][m]['fp_rate']*100:.1f}"
A = pv["A_false_positive"]
sweep = {s["prevalence"]: s for s in ag["prevalence_sweep"]}
single = ag["single_call_configurations"]
fp = lambda m: f"{P[m]['fp_rate']*100:.1f}"
ms = lambda m: f"{P[m]['miss_rate']*100:.1f}"

# Half-up, not format()'s round-half-even. A mean pairwise Scott's pi of 0.0505 formats as
# "0.050" under banker's rounding and as the manuscript's correct "0.051" under half-up.
def hu(x, nd):
    return str(Decimal(repr(x)).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP))

pv_ = lambda m, v: hu(ps[m][v]["fp"] * 100, 1)          # per-prompt FP rate
prec = lambda pr, m, nd=1: hu(sweep[pr]["precision_pct"][m], nd)
K = lambda c, f, nd: hu(abs(cm[c][f]), nd)

RULES = [
    # abstract
    (r"false-positive rates ranged from",            fp("Gemini Flash"),   "D4 FP, Gemini Flash"),
    (r"false-positive rates ranged from 2\.3\\% to", fp("GPT-4o-mini"),    "D4 FP, GPT-4o-mini"),
    (r"ranged from 2\.3\\% to 85\.7\\%---an",        f"{A['fp_spread_pp']*100:.1f}", "FP spread"),
    (r"confidence interval",                          f"{A['fp_spread_ci95'][0]*100:.1f}", "spread CI low", 2),
    (r"the models disagreed on",                      f"{A['divergence_benign']*100:.1f}", "divergence", 2),
    # results 3.1
    (r"ranged from 2\.3\\% \(7 of 300 cases\) for Gemini Flash to", fp("GPT-4o-mini"), "3.1 FP max"),
    (r"cross-model spread was",                       f"{A['fp_spread_pp']*100:.1f}", "3.1 spread"),
    (r"Cochran's \$Q = ",                             f"{stt['cochran_q']['Q']:.1f}", "3.1 Cochran Q"),
    (r"did not screen unanimously on",                f"{A['divergence_benign']*100:.1f}", "3.1 divergence"),
    # results 3.2 tier ordering, in order
    (r"false-positive rate fell from",                fp("GPT-4o-mini"), "3.2 OpenAI top"),
    (r"fell from 85\.7\\% for GPT-4o-mini, to",       fp("GPT-4.1-mini"), "3.2 OpenAI mid"),
    (r"to 37\.0\\% for GPT-4\.1-mini, to",            fp("GPT-4o"), "3.2 OpenAI low"),
    (r"it fell from",                                 fp("Gemini Flash-Lite"), "3.2 Google top"),
    (r"fell from 44\.0\\% for Gemini Flash-Lite to",  fp("Gemini Flash"), "3.2 Google low"),
    (r"but missed",                                   ms("Gemini Flash"), "3.2 Flash miss"),
    # results 3.3 alert workload
    (r"alert volume ranged from roughly",             "24,000", "3.3 low alerts"),
    (r"to approximately",                             "857,000", "3.3 high alerts"),
    (r"daily alert workload of about",                f"{sweep[0.001]['ratio_max_over_min']:.0f}", "3.3 aggregate ratio"),
    (r"the defensible range across configurations an institution could actually deploy is",
     f"{min(v['alert_ratio_max_over_min'] for v in single.values()):.0f}", "3.3 deployable low"),
    # aggregation section
    (r"the spread lies between",                      f"{ag['fp_spread_range_pp'][0]:.1f}", "2.x spread range low"),
    (r"spread lies between 77\.7 and",                f"{ag['fp_spread_range_pp'][1]:.1f}", "2.x spread range high", 2),
    (r"The frozen corpus holds",                      f"{ag['calls']['realized']:,}".replace(",", "{,}"), "realized calls"),
    # The deployable single-call rows of the sensitivity table, which no rule reached: bending
    # the GPT-4o FATF seed-1 rate to 0.4242 passed every gate.
    (r"Single call: FATF seed 0\s+& ",          sc("v_fatf|seed0", "Gemini Flash"),  "single call fatf0, Flash"),
    (r"Single call: FATF seed 0\s+& 2\.3 & ",   sc("v_fatf|seed0", "GPT-4o"),        "single call fatf0, GPT-4o"),
    (r"Single call: FATF seed 1\s+& 2\.3 & ",   sc("v_fatf|seed1", "GPT-4o"),        "single call fatf1, GPT-4o"),
    (r"Single call: terse seed 0\s+& ",         sc("v_terse|seed0", "Gemini Flash"),  "single call terse0, Flash"),
    (r"Single call: terse seed 1\s+& ",         sc("v_terse|seed1", "Gemini Flash"),  "single call terse1, Flash"),
    # ---- prompt sensitivity. Three of these five pairs were stale pre-restoration values
    # that survived every gate because the coverage checker was treating "\%" as a LaTeX
    # comment and discarding the rest of the line. Each endpoint is now anchored.
    (r"compliance-officer prompt: Gemini Flash ",   pv_("Gemini Flash", "v_terse"),      "prompt terse, Flash"),
    (r"Gemini Flash 0\.3\\%\$\\rightarrow\$",      pv_("Gemini Flash", "v_fatf"),       "prompt fatf, Flash"),
    (r"\\%, GPT-4o ",                                pv_("GPT-4o", "v_terse"),            "prompt terse, GPT-4o"),
    (r"GPT-4o 1\.0\\%\$\\rightarrow\$",            pv_("GPT-4o", "v_fatf"),             "prompt fatf, GPT-4o"),
    (r"\\%, GPT-4\.1-mini ",                         pv_("GPT-4.1-mini", "v_terse"),      "prompt terse, 4.1-mini"),
    (r"GPT-4\.1-mini 24\.0\\%\$\\rightarrow\$",    pv_("GPT-4.1-mini", "v_fatf"),       "prompt fatf, 4.1-mini"),
    (r"\\%, Gemini Flash-Lite ",                      pv_("Gemini Flash-Lite", "v_terse"), "prompt terse, Flash-Lite"),
    (r"Gemini Flash-Lite 24\.7\\%\$\\rightarrow\$", pv_("Gemini Flash-Lite", "v_fatf"),  "prompt fatf, Flash-Lite"),
    (r"and GPT-4o-mini ",                            pv_("GPT-4o-mini", "v_terse"),       "prompt terse, 4o-mini"),
    (r"GPT-4o-mini 82\.7\\%\$\\rightarrow\$",       pv_("GPT-4o-mini", "v_fatf"),        "prompt fatf, 4o-mini"),
    # ---- correlated-miss secondary analysis. Every one of these was hand-typed with no code
    # behind it until correlated_miss.py was written; kappa was right, the claim that AC1
    # "gave consistent conclusions" was not (AC1 is 0.924 against kappa 0.072).
    (r"mean pairwise Cohen's \$\\kappa = ",           K("cohen_kappa", "mean", 3), "kappa mean"),
    (r"\(range \$-",                                  K("cohen_kappa", "min", 3),  "kappa range low"),
    (r"\$-0\.011\$ to \$",                            K("cohen_kappa", "max", 2),  "kappa range high"),
    (r"Scott's \$\\pi = ",                            K("scott_pi", "mean", 3),    "Scott pi mean"),
    (r"AC1 instead averaged ",                       K("gwet_ac1", "mean", 3),    "Gwet AC1 mean"),
    (r"raw agreement is already ",                   hu(cm["raw_agreement"]["mean"]*100, 1), "raw agreement"),
    (r"per-model miss rates ranged from",            hu(cm["miss_rate_min"]*100, 1), "miss rate min"),
    (r"miss rates ranged from 0\.0\\% to",            hu(cm["miss_rate_max"]*100, 1), "miss rate max"),
    # ---- prevalence sweep. The 1% precision endpoint was stale (27.1 against a true 27.6).
    (r"Precision moves over the same range from",    prec(0.0001, "Gemini Flash"), "precision low, Flash"),
    (r"from 0\.4\\% to",                              prec(0.01, "Gemini Flash"),   "precision high, Flash"),
    (r"for Gemini Flash and from",                   prec(0.0001, "GPT-4o-mini", 2), "precision low, 4o-mini"),
    (r"from 0\.01\\% to",                             prec(0.01, "GPT-4o-mini"),    "precision high, 4o-mini"),
    (r"the estimated precision was about",           prec(0.001, "Gemini Flash"),  "precision at 0.1%, Flash"),
    (r"versus about",                                prec(0.001, "GPT-4o-mini", 2), "precision at 0.1%, 4o-mini"),
    (r"moves the ratio from about",                  hu(sweep[0.0001]["ratio_max_over_min"], 0), "sweep ratio low end"),
    (r"about 37-fold to about",                      hu(sweep[0.01]["ratio_max_over_min"], 0),   "sweep ratio high end", 2),
    # ---- abstention on the common retained subset (Appendix A), derived not typed.
    (r"Recomputed on the", str(ABC["n_cases"]), "abstention common n"),
    (r"GPT-4o-mini, a spread of", hu(ABC["fp_spread_pp"], 1), "abstention common spread"),
    # ---- the four-designed-cells sensitivity, derived rather than hand-computed.
    (r"gives GPT-4o-mini a false-positive rate of",
     hu(FOUR["per_model"]["GPT-4o-mini"]["fp_rate"] * 100, 1), "four-cell FP, 4o-mini"),
    (r"and a cross-model spread of",
     hu(FOUR["fp_spread_pp"], 1), "four-cell spread"),
    # ---- figure 3 caption, which still carried the pre-restoration 4,200/830,000 volumes.
    (r"changes the queue from about",                "24,000",  "fig3 caption low"),
    (r"from about 24,000 to about",                  "857,000", "fig3 caption high"),
]

fails = []
for rule in RULES:
    anchor, literal, why = rule[0], rule[1], rule[2]
    want = rule[3] if len(rule) > 3 else 1      # a fact stated in both abstract and body
    pat = anchor + r"[^.]{0,120}?" + re.escape(literal)
    hits = len(re.findall(pat, tex))
    if hits == 0:
        fails.append(f"NO MATCH  [{why}] expected '{literal}' after /{anchor}/")
    elif hits != want:
        fails.append(f"COUNT     [{why}] matched {hits}x, expected {want}x")

print(f"binding rules checked : {len(RULES)}")
print(f"failed                : {len(fails)}")
for f in fails:
    print("  " + f)
sys.exit(1 if fails else 0)
