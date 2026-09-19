"""D15d — re-size R1 (trust principal) and R3 (f2 bridge-opex exposure) against the
STAGED (15-yr) wind-down, per Editor D12-addendum A1. Economics & Statistics Referee.
Fresh seed 20260720 (same as D15 R1/R3 — this is a re-sizing of the same object, so the
disposal-cost draw is held identical; only the wind-down TAPER changes).

WHAT CHANGES, AND WHAT DOES NOT (the load-bearing result):
  R1 (terminal-disposal PRINCIPAL, T = N*d) is TAPER-INVARIANT. You dispose of the same N
      satellites at the same per-object cost d regardless of whether the taper is 5 or 15 yr.
      D13's staged lever confirms "staging moves timing, not total" (cumulative controlled
      deorbit -> N in the limit for both). So R1 = $759M median [$131M,$4.42B] on the census,
      UNCHANGED. D14's $0.76B floor is likewise unaffected.
  R3 (f2 through-window OPEX EXPOSURE) TRIPLES. Exposure = integral_0^inf A(t) dt = N*tau
      satellite-years, where tau is the wind-down e-fold. The D13 staged_winddown scenario
      stretches tau from 5 yr (compressed) to 15 yr (staged), so exposure goes N*5 -> N*15.
      The opex RATE remains NEEDS-DATA; the exposure MULTIPLICAND is exact and triples.

WHY THIS IS THE D6-RECONCILED DESIGN POINT (D13 staged_winddown_lever, read at HEAD):
  staged/compressed peak annual controlled (intact) reentry ratio = 0.356 (~1/3) while the
  trigger-band DEBRIS benefit is retained (staged yr5 2,099 vs compressed 2,407 - marginally
  better, suppression persists over the longer active tail). So the D6-optimal design (lower
  reentry-mass peak, same debris benefit) costs MORE on the needs-data f2 axis: the trust
  sized against the staged wind-down loads 3x the opex-window onto R3, sharpening the D15
  finding that R1 alone under-sizes the trust.
"""
import json, math
import numpy as np

SEED = 20260720
NDRAW = 400_000
D_LO, D_HI = 10_000.0, 500_000.0
TAU_COMPRESSED_YR = 5.0     # kessler_qb_engine.py responsible_winddown e-fold
TAU_STAGED_YR = 15.0        # d13_partial_failure staged_winddown e-fold (D6-reconciled)

# D13 staged_winddown_lever ratios (read at HEAD from d13_partial_failure_results.json), for context:
D13_PEAK_RATIO_STAGED_OVER_COMPRESSED_P50 = 0.35584373713420364
D13_CUMULATIVE_RATIO_P50 = 0.827530428075464   # <1 only because the 26-yr engine horizon truncates the 15-yr taper
D13_HORIZON_YR = 26

FLEETS = {
    "current_census_starlink_active":  10_736,
    "trigger_band_density_effective":   7_482,
    "filed_queue_ITU_M1_10pct":       125_160,
    "filed_queue_FCC_50pct":          625_800,
    "filed_queue_total_100pct":     1_251_600,
}

def pctiles(a, ps=(5, 50, 95)):
    return {f"p{p}": float(np.percentile(a, p)) for p in ps}

rng = np.random.default_rng(SEED)
d = np.exp(rng.uniform(math.log(D_LO), math.log(D_HI), NDRAW))   # identical draw to D15 R1
d_stats = pctiles(d); d_stats["mean"] = float(d.mean())

out = {
    "artifact": "d15d_staged_winddown_resize",
    "author_seat": "Economics & Statistics Referee",
    "round": "D15d (D12-addendum A1 re-sizing, pre-launch)",
    "seed": SEED, "ndraw": NDRAW,
    "disposal_cost_d_p5_p50_p95_mean": d_stats,
    "R1_principal_TAPER_INVARIANT": {},
    "R3_opex_exposure_compressed_vs_staged": {},
    "D13_lever_context": {
        "peak_reentry_ratio_staged_over_compressed_p50": D13_PEAK_RATIO_STAGED_OVER_COMPRESSED_P50,
        "cumulative_ratio_p50_horizon_truncated": D13_CUMULATIVE_RATIO_P50,
        "note": ("staged cuts PEAK intact-reentry to ~1/3 while retaining the debris benefit; "
                 "cumulative<1 is a %d-yr horizon artifact, not a lost-fleet effect - in the limit "
                 "both dispose N (staging moves timing, not total)." % D13_HORIZON_YR),
    },
}

for name, N in FLEETS.items():
    T = N * d
    st = pctiles(T); st["mean"] = float(T.mean()); st["N"] = N
    st["note"] = "unchanged from D15 R1 - terminal disposal cost does not depend on taper length"
    out["R1_principal_TAPER_INVARIANT"][name] = st

    exp_c = N * TAU_COMPRESSED_YR
    exp_s = N * TAU_STAGED_YR
    out["R3_opex_exposure_compressed_vs_staged"][name] = {
        "N": N,
        "compressed_5yr_fleet_sat_years": exp_c,
        "staged_15yr_fleet_sat_years": exp_s,
        "ratio_staged_over_compressed": exp_s / exp_c,   # exactly 3.0 by construction
        "opex_per_sat_yr_usd": "NEEDS-DATA (unsourced)",
    }

out["ruling"] = (
    "Staging the wind-down 5->15 yr (the D6-reconciled design point) leaves R1 (terminal-disposal "
    "principal) UNCHANGED and TRIPLES R3 (f2 through-window opex exposure): N*5 -> N*15 sat-yr. "
    "R1 is a per-object terminal cost; R3 is a per-object-year flow cost - only the flow cost is "
    "taper-sensitive. The trust sized against the staged wind-down = R1 principal (invariant floor) "
    "+ R3 opex reserve (tripled, needs-data rate). D14's $0.76B floor and the covered-vs-aspirational "
    "split are unaffected. Second-order (flagged, not priced): a 15-yr reserve is drawn down over 15 "
    "yr not 5, so its present value/carry differs from a naive 3x of an annual rate - immaterial while "
    "the per-sat-yr rate is needs-data."
)

with open("d15d_staged_resize_results.json", "w") as f:
    json.dump(out, f, indent=2, default=float)

print("R1 census principal (taper-invariant) p5/p50/p95 ($M): %.1f / %.1f / %.1f" %
      (out["R1_principal_TAPER_INVARIANT"]["current_census_starlink_active"]["p5"]/1e6,
       out["R1_principal_TAPER_INVARIANT"]["current_census_starlink_active"]["p50"]/1e6,
       out["R1_principal_TAPER_INVARIANT"]["current_census_starlink_active"]["p95"]/1e6))
print()
print("R3 opex exposure (fleet-sat-years), compressed 5yr -> staged 15yr (x3):")
for name, N in FLEETS.items():
    r = out["R3_opex_exposure_compressed_vs_staged"][name]
    print("  %-34s N=%9d  %10d -> %10d  (x%.1f)" %
          (name, N, r["compressed_5yr_fleet_sat_years"], r["staged_15yr_fleet_sat_years"], r["ratio_staged_over_compressed"]))
