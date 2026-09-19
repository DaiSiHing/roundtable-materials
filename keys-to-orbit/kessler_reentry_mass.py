"""Reentry bulk-mass module v1 — formalizes D6 SS3's hand arithmetic as a seeded MC.
Commissioned by Editor 2026-07-16 (D6 rec 5 / Editor Q4: harden the bracket for
reproducibility). STANDALONE by design: touches no engine, no existing artifact —
D7's verification targets stay frozen; integration of these numbers into paper SS4.7
is queued for D7-return.

Construction is FAITHFUL to the D6 memo: replacement-cadence flux = stock / design_life
x unit_mass, with unit masses as DISTRIBUTIONS over the memo's stated ranges (uniform —
the least-informative shape over a stated range) and design life FIXED at 5 yr (ASSUMED,
per Maloney et al.'s scenario convention, matching the memo). Natural background is NOT
modeled as a distribution (shape unknown; inventing one would be false precision): ratios
are reported against the 15,000 t/yr central anchor with the [2,000, 110,000] method
range carried alongside, exactly as the memo does.
Tags: stocks MEASURED/SOURCED (census 8 Jul; race-model milestone stocks); unit masses
ASSUMED (ranges from disclosed/claimed figures; filed-queue upper 2.0 t is CLAIMED-only);
design life ASSUMED; every output MODELED/DERIVED, three-IFs armor on milestone rows.
"""
import numpy as np, json

SEED, ND = 20260717, 100_000
rng = np.random.default_rng(SEED)
NATURAL_CENTRAL, NATURAL_RANGE = 15_000.0, [2_000.0, 110_000.0]  # t/yr, Duprat 2021 + method range
LIFE = 5.0                                                        # yr, ASSUMED (fixed, per memo)

STOCKS = {  # satellites; provenance in comments
  "starlink_current":   10_736.0,   # census 8 Jul 2026, SOURCED
  "all_active_current": 16_234.0,   # census 8 Jul 2026, SOURCED
  "itu_m1_increment":  125_160.0,   # race_model_d3b_results.json milestone_arithmetic, 10% of filed
  "fcc_50pct_increment":625_800.0,  # same source — closes the D6 seat's declined re-derivation
}
MASS = {  # unit-mass draws, tonnes, uniform over memo ranges (ASSUMED)
  "starlink_current":   rng.uniform(0.80, 1.25, ND),
  "all_active_current": rng.uniform(0.25, 1.25, ND),
  "itu_m1_increment":   rng.uniform(0.25, 2.00, ND),   # incl. CLAIMED ~2 t AI-datacenter class
  "fcc_50pct_increment":rng.uniform(0.25, 2.00, ND),
}
q = lambda a: [float(np.percentile(a, p)) for p in (5, 50, 95)]
out = {"artifact":"kessler_reentry_mass_v1","seed":SEED,"n_draws":ND,
       "design_life_yr_ASSUMED":LIFE,
       "natural_background_t_yr":{"central_duprat2021":NATURAL_CENTRAL,"method_range":NATURAL_RANGE,
         "note":"background carried as anchor+range, NOT drawn — its distribution shape is unknown and would be invented"},
       "flux_t_yr":{}, "ratio_to_central_background":{},
       "conditions":"milestone rows carry THREE LOUD IFs (granted / honored / trigger-band-like shells); "
                    "bracket never a date; unit-mass is the dominant ASSUMED sensitivity (SS8 analog of f_imp)"}
raw = {}
for k, s in STOCKS.items():
    flux = s / LIFE * MASS[k]
    out["flux_t_yr"][k] = q(flux)
    out["ratio_to_central_background"][k] = q(flux / NATURAL_CENTRAL)
    raw[k] = flux
# cross-seed stability
rng2 = np.random.default_rng(SEED + 1)
f2 = STOCKS["itu_m1_increment"]/LIFE*rng2.uniform(0.25,2.00,ND)
out["cross_seed"] = {"seed_pair":[SEED,SEED+1],
  "itu_m1_p50_rel_dev": abs(np.percentile(f2,50)-np.percentile(raw["itu_m1_increment"],50))/np.percentile(raw["itu_m1_increment"],50)}
# memo-bracket containment check (the hand arithmetic must sit inside/at the MC support)
mem = {"starlink_current":(1720,2680),"all_active_current":(810,4060),"itu_m1_increment":(6260,50060)}
out["d6_memo_bracket_check"] = {k:{"memo_endpoints_t_yr":list(v),
    "mc_support_p0_p100":[float(raw[k].min()),float(raw[k].max())],
    "endpoints_match_to_rounding":bool(abs(raw[k].min()-v[0])<=10 and abs(raw[k].max()-v[1])<=10)} for k,v in mem.items()}

def r9(o):
    if isinstance(o,dict): return {k:r9(v) for k,v in o.items()}
    if isinstance(o,list): return [r9(v) for v in o]
    if isinstance(o,float): return float(f"{o:.9g}")
    return o
json.dump(r9(out), open("reentry_mass_results.json","w"), indent=1)
idx = np.sort(rng.choice(ND, 2000, replace=False))
with open("reentry_mass_raw_sample.csv","w") as f:
    f.write(",".join(STOCKS.keys())+"\n")
    for i in idx: f.write(",".join(f"{raw[k][i]:.9g}" for k in STOCKS)+"\n")
print(json.dumps(r9(out["flux_t_yr"]),indent=1)); print(json.dumps(r9(out["d6_memo_bracket_check"]),indent=1))
