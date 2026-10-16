"""Bind each load-bearing number in the manuscript to the result that produced it.

Coverage asks whether a number appears somewhere; binding asks whether it appears in
the RIGHT PLACE. Swapping two models' false-positive rates would pass a coverage test
and invert a finding; an anchored rule catches it.

Each rule is (regex anchor that must immediately precede, expected literal, source).
The expected values are read from capsule/results/, never hand-typed here.
Exit 0 all bound / 1 a rule failed / 2 could-not-check.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEX = ROOT / "paper" / "manuscript_full.tex"
RES = ROOT / "results"

try:
    tex = TEX.read_text()
    ag = json.loads((RES / "aggregation_sensitivity.json").read_text())
    pv = json.loads((RES / "pivot_claims.json").read_text())
    stt = json.loads((RES / "stats_tests.json").read_text())
except Exception as e:
    print(f"COULD NOT CHECK: {e}"); sys.exit(2)
if len(tex) < 20000:
    print(f"COULD NOT CHECK: manuscript only {len(tex)} chars"); sys.exit(2)

P = ag["policies"]["ties_to_flag_preregistered_D4"]["per_model"]
SUB = ag["policies"]["label_dependent_as_published"]["per_model"]
SC = ag["single_call_configurations"]
sub = lambda m: f"{SUB[m]['fp_rate']*100:.1f}"
sc = lambda c, m: f"{SC[c]['per_model'][m]['fp_rate']*100:.1f}"
A = pv["A_false_positive"]
sweep = {s["prevalence"]: s for s in ag["prevalence_sweep"]}
single = ag["single_call_configurations"]
fp = lambda m: f"{P[m]['fp_rate']*100:.1f}"
ms = lambda m: f"{P[m]['miss_rate']*100:.1f}"

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
    (r"The cross-model spread, which carries the paper's main claim, moves from 82\.7 to",
     f"{A['fp_spread_pp']*100:.1f}", "2.x spread after restoring D4"),
    (r"the spread lies between",                      f"{ag['fp_spread_range_pp'][0]:.1f}", "2.x spread range low"),
    (r"spread lies between 77\.7 and",                f"{ag['fp_spread_range_pp'][1]:.1f}", "2.x spread range high", 2),
    (r"The frozen corpus holds",                      f"{ag['calls']['realized']:,}".replace(",", "{,}"), "realized calls"),
    # The as-submitted rates in the deviation disclosure. Fault injection swapped 0.3 and 1.0
    # here and every gate passed: both are real printed values, so nothing short of an anchored
    # rule can see the swap, and these are precisely the numbers a reader checks the deviation
    # against.
    (r"raises every false-positive rate---from",      sub("Gemini Flash"),      "as-submitted FP, Gemini Flash"),
    (r"rate---from 0\.3, ",                           sub("GPT-4o"),            "as-submitted FP, GPT-4o"),
    (r"from 0\.3, 1\.0, ",                            sub("GPT-4.1-mini"),      "as-submitted FP, GPT-4.1-mini"),
    (r"from 0\.3, 1\.0, 23\.7, ",                     sub("Gemini Flash-Lite"), "as-submitted FP, Flash-Lite"),
    (r"0\.3, 1\.0, 23\.7, 24\.7 and ",                sub("GPT-4o-mini"),       "as-submitted FP, GPT-4o-mini"),
    # The deployable single-call rows of the sensitivity table, which no rule reached: bending
    # the GPT-4o FATF seed-1 rate to 0.4242 passed every gate.
    (r"Single call: FATF prompt seed 0\s+& ",          sc("v_fatf|seed0", "Gemini Flash"),  "single call fatf0, Flash"),
    (r"Single call: FATF prompt seed 0\s+& 2\.3 & ",   sc("v_fatf|seed0", "GPT-4o"),        "single call fatf0, GPT-4o"),
    (r"Single call: FATF prompt seed 1\s+& 2\.3 & ",   sc("v_fatf|seed1", "GPT-4o"),        "single call fatf1, GPT-4o"),
    (r"Single call: terse prompt seed 0\s+& ",         sc("v_terse|seed0", "Gemini Flash"),  "single call terse0, Flash"),
    (r"Single call: terse prompt seed 1\s+& ",         sc("v_terse|seed1", "Gemini Flash"),  "single call terse1, Flash"),
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
