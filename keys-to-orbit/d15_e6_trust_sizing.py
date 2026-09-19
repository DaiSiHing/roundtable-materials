"""D15 — E6 continuity/resolution regime: fleet-level trust sizing (R1) + f2 opex exposure (R3).
Economics & Statistics Referee, independent reimplementation. Fresh seed 20260720
(distinct from the race engine's 26716 — this is a reimplementation, not a re-run of the
delivered JSON, per RR#2/RR#3).

WHAT THIS PRICES
  R1: the fleet-level disposal-trust PRINCIPAL as a distribution, T = N * d, where d is the
      E2 per-satellite disposal cost the race model draws as  d ~ logU($10k, $500k)
      (race_model_d3b.py line 41 / Module C). d's geometric mean is exactly the paper's
      §7.1 $71k/sat median [$12k, $411k]. This is the CAPABILITY-INTACT orderly-disposal
      cost — D12 Components 1+2 (funded trust + resolution plan), D14's "affordable regime".

  R3: the f2 operational-bridge OPEX EXPOSURE = fleet-satellite-years flown during the
      wind-down window * per-satellite-year station-keeping opex. The window is NOT a
      distribution in the engine: kessler_qb_engine.py lines 152-156 hard-code the
      wind-down as a first-order exponential decay with a fixed 5-yr e-fold
      (conv = A*dt/(5*365.25)). So the exposure integral is deterministic:
      integral_0^inf A0*exp(-t/tau) dt = A0 * tau = N * 5 satellite-years.
      The opex RATE is unsourced -> needs-data ruling; the exposure MULTIPLICAND is exact.

METHODOLOGICAL RULING (the load-bearing choice in R1):
  d is EPISTEMIC uncertainty about a COMMON disposal-technology cost for a HOMOGENEOUS
  fleet -- one uncertain number applied fleet-wide -- NOT aleatory per-satellite variation.
  => fleet principal T = N * d  (COMMON-MODE): inherits d's full multiplicative spread.
  The alternative (iid per-satellite draws, T = sum_i d_i) is computed here ONLY to show it
  is wrong for this object: it collapses the distribution to a near-point at N*E[d] and
  RE-CENTERS on the MEAN ($125k), contradicting both "never a point" (dispatch R1) and
  D14's floor arithmetic ($0.76B = N * $71k MEDIAN, dispersion [$0.13B,$4.4B] = N*[p5,p95]).
"""
import json, math
import numpy as np

SEED = 20260720
NDRAW = 400_000
D_LO, D_HI = 10_000.0, 500_000.0          # race_model_d3b.py: d ~ logU($10k, $500k)
TAU_WINDDOWN_YR = 5.0                       # kessler_qb_engine.py: hard-coded 5-yr e-fold ramp

# Fleets to size the trust against (all SOURCED anchors, tags in the memo):
FLEETS = {
    "current_census_starlink_active":      10_736,     # §2.1 GCAT 8 Jul 2026
    "trigger_band_density_effective":       7_482,     # incidence-bases density_ratio window (MEASURED, density-effective, NOT a payload census)
    "burden_shift_nonmaneuverable":         2_113,     # §2.1 (context bracket, whole-fleet)
    "filed_queue_ITU_M1_10pct":           125_160,     # §4.7/§6.3
    "filed_queue_FCC_50pct":              625_800,     # §6.3 (race-model absolute)
    "filed_queue_total_100pct":         1_251_600,     # §6.3
}

def pctiles(a, ps=(5, 50, 95)):
    return {f"p{p}": float(np.percentile(a, p)) for p in ps}

rng = np.random.default_rng(SEED)
# d ~ logU(lo,hi): exp of a uniform in log-space
d = np.exp(rng.uniform(math.log(D_LO), math.log(D_HI), NDRAW))

# --- Reproduction check on the unit anchor (must land on §7.1's [$12k, $71k, $411k]) ---
d_stats = pctiles(d)
d_mean = float(d.mean())
# analytic closed forms for a log-uniform, for the memo's verification log
an_median = math.sqrt(D_LO * D_HI)
an_mean = (D_HI - D_LO) / (math.log(D_HI) - math.log(D_LO))
an_p5 = D_LO * (D_HI / D_LO) ** 0.05
an_p95 = D_LO * (D_HI / D_LO) ** 0.95

out = {
    "artifact": "d15_e6_trust_sizing",
    "author_seat": "Economics & Statistics Referee",
    "round": "D15 (E6 pricing/incidence, pre-launch final referee round)",
    "seed": SEED, "ndraw": NDRAW,
    "disposal_cost_d_logU_10k_500k": {
        "reimplemented_p5_p50_p95": d_stats,
        "reimplemented_mean": d_mean,
        "analytic_p5_p50_p95_mean": {"p5": an_p5, "p50": an_median, "p95": an_p95, "mean": an_mean},
        "paper_anchor_7_1": {"p50": 71_000, "p5": 12_000, "p95": 411_000},
        "note": "geometric mean (median) reproduces §7.1 $71k; arithmetic mean $125k is the higher moment iid-summing would wrongly re-center on.",
    },
    "R1_fleet_trust_principal_common_mode": {},
    "R1_iid_sum_contrast_WRONG_for_homogeneous_fleet": {},
    "R3_f2_bridge_opex_exposure": {},
}

for name, N in FLEETS.items():
    T = N * d                              # COMMON-MODE: one epistemic cost draw applied fleet-wide
    st = pctiles(T)
    st["mean"] = float(T.mean())
    st["N"] = N
    out["R1_fleet_trust_principal_common_mode"][name] = st

    # iid-sum contrast (sum of N independent per-sat draws) — analytic via CLT to avoid
    # materializing N*NDRAW draws; shows collapse to a near-point at N*mean.
    var_single = float(d.var())
    sd_sum = math.sqrt(N * var_single)
    mean_sum = N * d_mean
    out["R1_iid_sum_contrast_WRONG_for_homogeneous_fleet"][name] = {
        "N": N, "mean": mean_sum,
        "p5_approx": mean_sum - 1.645 * sd_sum,
        "p95_approx": mean_sum + 1.645 * sd_sum,
        "coefficient_of_variation": sd_sum / mean_sum,
    }

    # R3 exposure: N * 5 satellite-years of station-keeping opex (deterministic multiplicand).
    exposure_satyr = N * TAU_WINDDOWN_YR
    out["R3_f2_bridge_opex_exposure"][name] = {
        "N": N,
        "winddown_fleet_satellite_years": exposure_satyr,
        "opex_per_sat_yr_usd": "NEEDS-DATA (unsourced in this record)",
        "opex_total_usd": "= %d sat-yr * (unsourced $/sat-yr)" % exposure_satyr,
    }

out["R3_ruling"] = (
    "Window duration is a HARD-CODED 5-yr e-fold (kessler_qb_engine.py L152-156), not a "
    "drawn distribution; exposure = N*5 sat-yr is exact. Per-sat-yr station-keeping opex is "
    "UNSOURCED -> needs-data (matches §7.1 pass-through discipline). Direction: this is the "
    "genuinely-new cost E6 carries beyond the terminal disposal bond (R1); the trust must "
    "fund it too (D12 Component 1), so R1 alone UNDER-sizes the trust."
)
out["reconciliation"] = {
    "vs_D14_floor": "D14's $0.76B floor = 10,736*$71k = R1 census p50 ($759M). D14's dispersion "
                    "[$0.13B,$4.4B] = R1 census [p5,p95] ($131M,$4.41B). EXACT agreement — same object, "
                    "same common-mode reading. Both tagged FLOOR / capability-intact orderly disposal.",
    "vs_D13_partition": "D13 gives failure STATES + the ~84% avoidance-effectiveness criticality threshold, "
                        "NOT a probability of landing covered-vs-residual (structural scenarios, no frequencies). "
                        "So R3 opex is priceable PER UNIT of covered wind-down but the covered FRACTION is not a "
                        "number this record contains. R3 opex is what keeps the fleet ABOVE D13's ~84% threshold "
                        "during descent — i.e. buys the 'self-limiting wind-down' rather than the 'zombie'.",
}

with open("d15_e6_trust_sizing_results.json", "w") as f:
    json.dump(out, f, indent=2, default=float)

# raw sample: first 1000 d draws for the reproducibility package
np.savetxt("d15_e6_trust_sizing_raw_sample.csv", d[:1000], fmt="%.6f", header="d_disposal_cost_usd_per_sat", comments="")

# --- console summary ---
print("d reimplemented p5/p50/p95/mean: %.1f / %.1f / %.1f / %.1f" % (d_stats['p5'], d_stats['p50'], d_stats['p95'], d_mean))
print("d analytic    p5/p50/p95/mean: %.1f / %.1f / %.1f / %.1f" % (an_p5, an_median, an_p95, an_mean))
print()
print("R1 fleet-trust principal (COMMON-MODE), $ millions p5/p50/p95/mean:")
for name, N in FLEETS.items():
    s = out["R1_fleet_trust_principal_common_mode"][name]
    print("  %-34s N=%9d  %10.1f / %10.1f / %10.1f / %10.1f" %
          (name, N, s['p5']/1e6, s['p50']/1e6, s['p95']/1e6, s['mean']/1e6))
print()
print("iid-sum contrast (census): mean $%.1fM, CV=%.4f  <- collapses to a near-point, re-centered on MEAN" %
      (out['R1_iid_sum_contrast_WRONG_for_homogeneous_fleet']['current_census_starlink_active']['mean']/1e6,
       out['R1_iid_sum_contrast_WRONG_for_homogeneous_fleet']['current_census_starlink_active']['coefficient_of_variation']))
print()
print("R3 exposure (census): %d fleet-sat-years * (unsourced $/sat-yr)" %
      out['R3_f2_bridge_opex_exposure']['current_census_starlink_active']['winddown_fleet_satellite_years'])
