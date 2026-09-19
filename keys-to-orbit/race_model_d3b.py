"""D3b quantitative race model v1 — Game Theory & Mechanism Design seat.
Commissioned by Editor 2026-07-16 (D3 GT memo rec 7). Seed 26716. Outputs %.9g.

PURPOSE (dispatch): map the region of ASSUMED payoff space where the deployment
layer is a genuine multipolar trap vs where the paper mountain never becomes
hardware; run E1/E2/E5 mechanism tests through the model. THE DELIVERABLE IS THE
MAP, NEVER A POINT OR A FORECAST. Region shares are shares of assumed-payoff-space
draws — parameter belief over payoff assumptions, not probabilities of the future.

STRUCTURE:
  Module A — deployment-stage game, symmetric n-player Cournot with an unpriced
    collision externality, plus the open-access limit (two-band discipline applied
    to market structure: Cournot floor / open-access band). Entrant stock Q adds to
    the incumbent fleet N0 (incumbent held as fixed background — SIMPLIFICATION,
    flagged; the incumbent's own expansion is not modeled here).
  Module B — filing-option module (E5 test): two-period real option; deadline
    regime (deploy-or-forfeit, FCC/ITU milestones) vs holding-price regime.
  Module C — disposal-bond module (E2 test): dispose-or-forfeit per satellite,
    the two D3 design conditions made quantitative.

CITED ANCHORS (never re-derived; f_imp conditionality + F15 parameter-belief
reading travel with every one):
  N0    = 10,736  active incumbent-fleet satellites (GCAT 8 Jul 2026, SOURCED)
  lam0  = 0.2/yr  expected catastrophic collisions at current trigger-band stocks,
                  engine knob medians (ledger SectionH, ASSUMED-knob-conditional)
  mu0   = 3/N0 /yr mission-kill hazard (D5 F17, second-order today, v2-scoped)
  M     = 1/rho*_465-495 (maneuvered) resampled from qb_engine_raw_sample.csv —
          the engine's intact-multiplier-to-threshold as a DISTRIBUTION (p50 7.36,
          [1.83, 29.8]); maneuvered regime = conditional on avoidance continuing.
  Rao et al. PNAS 2020 fee anchors: ~$15k/sat-yr (2020) -> ~$235k (2040), SOURCED.
  FCC 25.165 bond cap $5M; FCC 25.164 milestones 50%/6yr, 100%/9yr; ITU Res.35
  10%/50%/100% at 2/5/7 yr post-regulatory-period (rule texts, D3-verified).

ASSUMED SWEEPS (the payoff space; all labels ASSUMED):
  theta ~ logU($300, $3M)   private value per deployed sat-year (THE unknown)
  k     ~ logU($30k, $1M)   cost per sat-year (capex amortized + opex)
  L     ~ logU($0.3M, $10M) loss per destroyed satellite
  Q_d   ~ logU(10k, 1M)     market depth (demand crowding scale, satellites)
  n     ~ U{2..10}          number of racing entrants
  u     ~ lognormal(0,0.7)  hazard-scale uncertainty multiplier
  d     ~ logU($10k, $500k) disposal cost per satellite (Module C)
"""
import json, math, csv
import numpy as np

SEED = 26716
ND   = 100_000
N0   = 10_736.0
LAM0 = 0.2
MU0  = 3.0 / N0
RAW_RHO_CSV = "/root/.claude/uploads/49347731-b291-566f-8980-cd45e28fe77b/1bd8de69-qb_engine_raw_sample.csv"
FEES = [0.0, 15_000.0, 50_000.0, 100_000.0, 235_000.0]

def q_(a, ps=(5, 50, 95)):
    return [float(np.percentile(a, p)) for p in ps]

def draws(rng, nd):
    lu = lambda lo, hi: np.exp(rng.uniform(math.log(lo), math.log(hi), nd))
    return dict(theta=lu(3e2, 3e6), k=lu(3e4, 1e6), L=lu(3e5, 1e7),
                Qd=lu(1e4, 1e6), n=rng.integers(2, 11, nd).astype(float),
                u=rng.lognormal(0.0, 0.7, nd), d=lu(1e4, 5e5))

def solve_layerA(p, M, fee=0.0, hazard_on=True):
    """Closed-form symmetric equilibria. Returns dict of arrays."""
    th, k, L, Qd, n, u = p["theta"], p["k"], p["L"], p["Qd"], p["n"], p["u"]
    hz = (u if hazard_on else 0.0) * L
    a    = th - k - fee - hz * (MU0 + LAM0 / N0)          # entry margin at Q->0
    astar= th - k - fee - hz * (MU0 + 2 * LAM0 / N0)      # planner margin at Q->0
    b_eq = (1 + 1 / n) * (th / Qd + hz * LAM0 / N0**2)
    b_oa = th / Qd + hz * LAM0 / N0**2
    b_st = th / Qd + 2 * hz * LAM0 / N0**2   # FULL-WELFARE planner (consumer surplus included): P(Q)=MC, not MR=MC
    Qeq  = np.maximum(0.0, a / b_eq)
    Qoa  = np.maximum(0.0, a / b_oa)
    Qst  = np.maximum(0.0, astar / b_st)
    def region(Q):
        r = np.zeros_like(Q)                    # 0 = paper
        entered = Q > 0
        trap = entered & (N0 + Q > M * N0)      # covers M<=1: any entry is critical
        r[entered] = 1                          # 1 = race-subcritical
        r[trap] = 2                             # 2 = trap-critical
        return r
    return dict(Qeq=Qeq, Qoa=Qoa, Qst=Qst, reg_eq=region(Qeq), reg_oa=region(Qoa),
                a=a, b_eq=b_eq, b_oa=b_oa, astar=astar)

def shares(reg):
    return {"paper": float(np.mean(reg == 0)), "race_subcritical": float(np.mean(reg == 1)),
            "trap_critical": float(np.mean(reg == 2))}

def run_map(seed):
    rng = np.random.default_rng(seed)
    p = draws(rng, ND)
    rho = np.loadtxt(RAW_RHO_CSV, delimiter=",", skiprows=1)[:, 1]   # rho*_465_495, maneuvered
    M = 1.0 / rho[rng.integers(0, len(rho), ND)]
    base = solve_layerA(p, M)
    return p, M, base

rng0 = np.random.default_rng(SEED)
p, M, base = run_map(SEED)

# ---------- Module A outputs: the map ----------
out_map = {
    "region_shares_cournot": shares(base["reg_eq"]),
    "region_shares_open_access": shares(base["reg_oa"]),
    "note_regions": ("shares of ASSUMED payoff-space draws (parameter belief over payoff "
                     "assumptions) - NOT probabilities of the future; the map is the deliverable"),
    "overentry_ratio_openaccess_Qoa_over_Qstar_p05_p50_p95": 
        q_((base["Qoa"] / np.maximum(base["Qst"], 1e-9))[(base["Qoa"] > 0) & (base["Qst"] > 0)]),
    "overentry_ratio_cournot_Qeq_over_Qstar_p05_p50_p95":
        q_((base["Qeq"] / np.maximum(base["Qst"], 1e-9))[(base["Qeq"] > 0) & (base["Qst"] > 0)]),
    "share_cournot_UNDERproduces_vs_planner": float(np.mean((base["Qeq"] < base["Qst"])[(base["Qeq"] > 0) & (base["Qst"] > 0)])),
    "share_Qstar_zero_but_entry": float(np.mean((base["Qeq"] > 0) & (base["Qst"] == 0))),
    "note_welfare_standard": ("planner = FULL WELFARE (consumer surplus included). Invariant: "
                              "open access strictly over-enters whenever the externality is positive "
                              "(a>a*, b_oa<b*). Cournot is MEASURED, not assumed: market power can "
                              "under-produce vs the optimum - the trap gradient is an open-access "
                              "claim, and it sharpens as n grows"),
}
# boundaries in theta-space, per draw (analytic): entry boundary theta_paper solves a=0;
# critical boundary theta_crit solves Qeq = (M-1)*N0  (both linear in theta)
th, k, L, Qd, n, u = (p[x] for x in ("theta", "k", "L", "Qd", "n", "u"))
hzL = u * L
theta_paper = k + hzL * (MU0 + LAM0 / N0)
Qc = np.maximum((M - 1.0), 0.0) * N0
# a(theta) = theta - theta_paper ; b_eq(theta) = (1+1/n)(theta/Qd + hzL*lam0/N0^2)
# Qeq(theta) = (theta - theta_paper)/b_eq(theta) = Qc  ->  linear solve:
cc = (1 + 1 / n) * hzL * LAM0 / N0**2
theta_crit = (theta_paper + Qc * cc) / np.maximum(1.0 - Qc * (1 + 1 / n) / Qd, 1e-12)
valid = (1.0 - Qc * (1 + 1 / n) / Qd) > 0        # else demand can never carry stock to threshold
thin = theta_crit[valid] / theta_paper[valid]
out_map["theta_paper_usd_per_satyr_p05_p50_p95"] = q_(theta_paper)
out_map["theta_crit_usd_per_satyr_p05_p50_p95_reachable"] = q_(theta_crit[valid])
out_map["share_threshold_unreachable_by_demand"] = float(np.mean(~valid))
out_map["thin_middle_theta_crit_over_theta_paper_p05_p50_p95"] = q_(thin)
out_map["share_thin_middle_below_2x"] = float(np.mean(thin < 2.0))
out_map["share_thin_middle_below_5x"] = float(np.mean(thin < 5.0))

# private collision cost AT the physical threshold (the deterrent that would have to stop the race)
cthr = hzL * (LAM0 * M / N0 + MU0)
out_map["private_collision_cost_at_threshold_usd_per_satyr_p05_p50_p95"] = q_(cthr)
out_map["share_entering_draws_where_cthr_exceeds_10pct_theta"] = float(
    np.mean((cthr > 0.1 * th)[base["Qeq"] > 0]))
# physics self-enforcement: does private collision cost ALONE keep equilibrium below threshold?
nohaz = solve_layerA(p, M, hazard_on=False)
flip = (nohaz["reg_eq"] == 2) & (base["reg_eq"] == 1)
out_map["physics_self_enforcement_share_of_nohaz_trap_draws"] = float(
    np.sum(flip) / max(np.sum(nohaz["reg_eq"] == 2), 1))

# boundary-sized fee: the fee that holds Cournot equilibrium exactly at the threshold, per trap draw
trap_mask = base["reg_eq"] == 2
f_boundary = np.maximum(0.0, (base["a"] - base["b_eq"] * Qc))[trap_mask]
out_map["boundary_fee_usd_per_satyr_trap_draws_p05_p50_p95"] = q_(f_boundary)
out_map["boundary_fee_share_below_235k"] = float(np.mean(f_boundary <= 235e3))
out_map["boundary_fee_share_above_235k"] = float(np.mean(f_boundary > 235e3))
out_map["note_boundary_fee"] = ("fee required to keep equilibrium stock at/below the threshold in "
                                "draws that are trap-critical unpriced; compare Rao anchors - this, "
                                "not the static Pigouvian f*, is the fee that moves the boundary")

# ---------- milestone arithmetic (docket-anchored illustrative ceiling) ----------
FILED = {"spacex_odc": 1_000_000, "blue_origin_sunrise": 51_600,
         "orbital_compute": 100_000, "spacex_gen3": 100_000}
tot = float(sum(FILED.values()))
m1_itu, m_fcc50 = 0.10 * tot, 0.50 * tot
rho_all = np.loadtxt(RAW_RHO_CSV, delimiter=",", skiprows=1)[:, 1]
M_all = 1.0 / rho_all
mult_m1, mult_f50 = (N0 + m1_itu) / N0, (N0 + m_fcc50) / N0
out_miles = {
    "filed_totals_sats": FILED, "sum_filed": tot,
    "itu_res35_M1_10pct_stock": m1_itu, "fcc_25164_50pct_stock": m_fcc50,
    "multiplier_if_M1_honored": float(mult_m1),
    "multiplier_if_fcc50_honored": float(mult_f50),
    "share_engine_draws_threshold_below_M1_multiplier": float(np.mean(M_all < mult_m1)),
    "share_engine_draws_threshold_below_fcc50_multiplier": float(np.mean(M_all < mult_f50)),
    "share_engine_draws_already_supercritical_maneuvered": float(np.mean(M_all < 1.0)),
    "conditions": ("ILLUSTRATIVE CEILING, three loud IFs: all filings granted; milestones "
                   "honored; stock concentrated at trigger-band-like shells. Filings span "
                   "150-2000 km (Gen3 323-477 km straddles bands 0/1, where drag is stronger). "
                   "Column-level arithmetic, not a band forecast; distance-to-threshold only, "
                   "no dates. Threshold multiplier is maneuvered-regime, f_imp-conditional, "
                   "parameter belief (F15)."),
}

# ---------- Module A mechanism test: fees (E1 family) ----------
out_fees = {}
for f in FEES:
    s = solve_layerA(p, M, fee=f)
    out_fees[f"fee_{int(f/1000)}k"] = {
        "cournot": shares(s["reg_eq"]), "open_access": shares(s["reg_oa"]),
        "median_Qeq_entering": float(np.median(s["Qeq"][s["Qeq"] > 0])) if np.any(s["Qeq"] > 0) else 0.0}
# Pigouvian fee f*: fee aligning Qeq (resp. Qoa) with planner Qst, per draw, entering draws
ent = base["Qeq"] > 0
fstar_c  = np.where(base["Qst"] > 0, base["a"] - base["b_eq"] * base["Qst"], base["a"])
fstar_oa = np.where(base["Qst"] > 0, base["a"] - base["b_oa"] * base["Qst"], base["a"])
out_fees["pigouvian_fstar_cournot_p05_p50_p95_entering"] = q_(fstar_c[ent])
out_fees["pigouvian_fstar_open_access_p05_p50_p95_entering"] = q_(fstar_oa[ent])
out_fees["share_fstar_cournot_negative"] = float(np.mean(fstar_c[ent] < 0))
oa_ent = base["Qoa"] > 0
out_fees["rao_bracket_check_open_access"] = {
    "share_fstar_below_15k": float(np.mean(fstar_oa[oa_ent] < 15e3)),
    "share_fstar_in_15k_235k": float(np.mean((fstar_oa[oa_ent] >= 15e3) & (fstar_oa[oa_ent] <= 235e3))),
    "share_fstar_above_235k": float(np.mean(fstar_oa[oa_ent] > 235e3)),
    "note": ("our f* is STATIC (current-stock externality incl. threshold-crossing NOT priced); "
             "Rao et al. price the DYNAMIC accumulation path - our f* is a floor on theirs, "
             "not an estimate of it; both cited, neither re-derived")}

# ---------- Module B: E5 deadline vs holding price ----------
TPV, DT, DELTA, B_PS = 10.0, 3.0, 0.86, 5e6 / 50_000.0     # PV yrs; hold period; discount; bond $/sat
gh_x, gh_w = np.polynomial.hermite_e.hermegauss(21)
gh_w = gh_w / math.sqrt(2 * math.pi)
def e5(sigma, h_levels):
    hz1 = u * L * (LAM0 / N0 + MU0)
    v1 = (th - k - hz1) * TPV
    th2 = th[:, None] * np.exp(sigma * gh_x[None, :] - 0.5 * sigma**2)   # martingale: E[theta2]=theta1
    v2 = (th2 - k[:, None] - hz1[:, None]) * TPV
    Ev2p = (np.maximum(v2, 0.0) * gh_w[None, :]).sum(1)
    P_v2pos = ((v2 > 0) * gh_w[None, :]).sum(1)
    E_v2neg_mass = ((v2 < 0) * gh_w[None, :]).sum(1)
    res = {}
    dep_dead = v1 > -B_PS
    stranded_dead = float(np.mean(E_v2neg_mass[dep_dead])) if np.any(dep_dead) else 0.0
    res["deadline"] = {"P_hardware": float(np.mean(dep_dead)),
                       "stranded_share_of_deployed": stranded_dead,
                       "mean_pv_margin_deployed": float(np.mean(v1[dep_dead]))}
    for h in h_levels:
        W = -DT * h + DELTA * Ev2p
        dep1 = v1 >= np.maximum(W, 0.0)
        hold = (~dep1) & (W > 0)
        P_hw = float(np.mean(dep1) + np.mean(hold * P_v2pos))
        stranded = (float(np.mean(E_v2neg_mass[dep1])) * float(np.mean(dep1)) / max(P_hw, 1e-12)
                    if np.any(dep1) else 0.0)   # t2 deploys have v2>0 by construction
        res[f"holding_{int(h/1000)}k"] = {
            "P_hardware": P_hw, "P_deploy_t1": float(np.mean(dep1)),
            "P_hold_paper": float(np.mean(hold)), "P_exit_t1": float(np.mean((~dep1) & (~hold))),
            "stranded_share_of_deployed": stranded,
            "hardware_ratio_deadline_over_holding": res["deadline"]["P_hardware"] / max(P_hw, 1e-12)}
    return res
out_e5 = {"sigma_0p6": e5(0.6, [1e3, 3e3, 1e4, 3e4]),
          "sigma_0p3": e5(0.3, [3e3]), "sigma_1p0": e5(1.0, [3e3]),
          "spec": {"TPV_years": TPV, "hold_period_years": DT, "discount": DELTA,
                   "bond_forfeit_usd_per_sat": B_PS, "sigma_theta_default": 0.6,
                   "note": ("partial-equilibrium option module (rival quantities not fed back - "
                            "SIMPLIFICATION, flagged); 'stranded' = deployed capacity whose t2 "
                            "value is negative: in-orbit hardware in low-value states, the "
                            "physical-externality carrier")}}

# ---------- Module C: E2 dispose-or-forfeit bond ----------
d = p["d"]
B_LEVELS = {"fcc_cap_scale_50usd": np.full(ND, 5e6 / 100_000.0),
            "half_d": 0.5 * d, "at_d": d, "twice_d": 2.0 * d}
out_e2 = {"dispose_share_by_bond_level": {kk: float(np.mean(d <= vv)) for kk, vv in B_LEVELS.items()},
          "disposal_cost_d_p05_p50_p95": q_(d),
          "design_conditions": ("dispose iff d <= B (weak tie disposes): the two D3 conditions "
                                "quantified - (a) B >= d or forfeit-and-abandon dominates; "
                                "(b) bankruptcy-remote escrow assumed here (a bond inside the "
                                "estate is a creditor claim, not a mechanism)")}
# entry-margin side effect of internalizing disposal: k -> k + d/TPV-equivalent annualized (d over 10yr)
p_d = dict(p); p_d["k"] = p["k"] + d / TPV
withd = solve_layerA(p_d, M)
out_e2["trap_share_shift_from_internalizing_d"] = {
    "cournot_before": out_map["region_shares_cournot"]["trap_critical"],
    "cournot_after": shares(withd["reg_eq"])["trap_critical"]}

# ---------- coverage matrix (model-measured effect sizes) ----------
f235 = solve_layerA(p, M, fee=235e3)
cov = {
  "fee_235k":      {"filing_volume": "no effect modeled (fees bill deployed sats; filing stays ~free)",
                    "trap_share_cournot": [out_map["region_shares_cournot"]["trap_critical"],
                                           shares(f235["reg_eq"])["trap_critical"]],
                    "disposal_outcome": "no effect (fee does not touch end-of-life choice)"},
  "holding_price_3k": {"filing_volume_P_exit_t1": out_e5["sigma_0p6"]["holding_3k"]["P_exit_t1"],
                    "hardware_ratio_deadline_over_holding":
                        out_e5["sigma_0p6"]["holding_3k"]["hardware_ratio_deadline_over_holding"],
                    "disposal_outcome": "no effect"},
  "disposal_bond_at_d": {"filing_volume": "no effect",
                    "trap_share_shift": out_e2["trap_share_shift_from_internalizing_d"],
                    "disposal_outcome_dispose_share": [
                        out_e2["dispose_share_by_bond_level"]["fcc_cap_scale_50usd"],
                        out_e2["dispose_share_by_bond_level"]["at_d"]]},
  "sentence_under_test": ("'no single instrument unpicks both games' - the matrix bears it out: "
                          "fee moves the deployment boundary only; holding price moves the "
                          "filing->hardware conversion only; bond moves the disposal outcome "
                          "(totally, at B>=d) and the deployment boundary only marginally")}

# ---------- cross-seed stability ----------
p2, M2, base2 = run_map(SEED + 1)
s1, s2 = shares(base["reg_eq"]), shares(base2["reg_eq"])
ent2 = base2["Qeq"] > 0
fstar2 = np.where(base2["Qst"] > 0, base2["a"] - base2["b_eq"] * base2["Qst"], base2["a"])
xseed = {"seed_pair": [SEED, SEED + 1],
         "max_abs_region_share_dev": float(max(abs(s1[kk] - s2[kk]) for kk in s1)),
         "fstar_cournot_median_rel_dev": float(abs(np.median(fstar_c[ent]) - np.median(fstar2[ent2]))
                                               / abs(np.median(fstar_c[ent])))}

# ---------- assemble ----------
def r9(o):
    if isinstance(o, float): return float(f"{o:.9g}")
    if isinstance(o, dict): return {kk: r9(vv) for kk, vv in o.items()}
    if isinstance(o, list): return [r9(vv) for vv in o]
    return o

out = {
 "artifact": "race_model_d3b_v1", "seat": "Game Theory & Mechanism Design", "seed": SEED,
 "depends_on": {"qb_engine": "kessler_qb_engine_v1 seed 20260716 (v1.2 results JSON; criticality layer verified identical to D5-accepted)",
                "M_source": "qb_engine_raw_sample.csv col rho_star_465_495 (2000 draws, resampled)",
                "anchors": {"N0": N0, "lam0_per_yr": LAM0, "mu0_per_satyr": MU0}},
 "language_conditions": ("F13/F15 bind; gradient discipline binds: the externality is unpriced, "
                         "therefore whatever entry occurs is over-entry - never 'a million "
                         "satellites will fly'; no dates, distance-to-boundary only"),
 "payoff_space_map": out_map,
 "milestone_arithmetic": out_miles,
 "mechanism_tests": {"E1_fees": out_fees, "E5_deadline_vs_holding": out_e5, "E2_disposal_bond": out_e2},
 "coverage_matrix": cov,
 "cross_seed": xseed,
 "robustness_ledger": {
   "invariant_under_payoff_monotonicity": [
     "file-big weak dominance at ~zero filing cost (analytic; not simulated here)",
     "Qeq >= Qstar direction (over-entry) whenever the externality term is positive and market power does not dominate; the exceptions are measured (share_fstar_negative)",
     "dispose iff B >= d (Module C decision rule is analytic)",
     "deadline deploys weakly more marginal-value states than holding for any h > 0 (option-value argument)"],
   "magnitude_dependent_ASSUMED": [
     "all region shares and boundary locations (theta/k/L/Qd/n/u sweeps are assumed)",
     "fstar distributions and the Rao bracket shares",
     "stranded-capacity shares and hardware ratios (sigma_theta, TPV, DT, delta assumed)",
     "private-collision-cost-at-threshold magnitudes (lam0 knob-median, f_imp-conditional)",
     "milestone arithmetic conditions as stated"]},
}
json.dump(r9(out), open("/home/claude/race_model_d3b_results.json", "w"), indent=1)

# raw sweep sample, %.9g
hdr = ["theta","k","L","Qd","n","u","M","Qeq","Qstar","Qoa","region_eq","fstar_cournot"]
mat = np.column_stack([th, k, L, Qd, n, u, M, base["Qeq"], base["Qst"], base["Qoa"],
                       base["reg_eq"], fstar_c])[:2000]
np.savetxt("/home/claude/race_model_d3b_raw_sample.csv", mat, delimiter=",",
           header=",".join(hdr), comments="", fmt="%.9g")

print(json.dumps(r9({
 "regions_cournot": out_map["region_shares_cournot"],
 "regions_open_access": out_map["region_shares_open_access"],
 "thin_middle_p50": out_map["thin_middle_theta_crit_over_theta_paper_p05_p50_p95"][1],
 "cthr_p50": out_map["private_collision_cost_at_threshold_usd_per_satyr_p05_p50_p95"][1],
 "deterrence_share": out_map["share_entering_draws_where_cthr_exceeds_10pct_theta"],
 "physics_self_enforce": out_map["physics_self_enforcement_share_of_nohaz_trap_draws"],
 "milestone_M1_share": out_miles["share_engine_draws_threshold_below_M1_multiplier"],
 "fee235_trap": out_fees["fee_235k"]["cournot"]["trap_critical"],
 "fstar_oa_p50": out_fees["pigouvian_fstar_open_access_p05_p50_p95_entering"][1],
 "fstar_neg_share": out_fees["share_fstar_cournot_negative"],
 "e5_hw_ratio_h3k": out_e5["sigma_0p6"]["holding_3k"]["hardware_ratio_deadline_over_holding"],
 "e5_stranded_deadline": out_e5["sigma_0p6"]["deadline"]["stranded_share_of_deployed"],
 "e5_stranded_holding3k": out_e5["sigma_0p6"]["holding_3k"]["stranded_share_of_deployed"],
 "xseed": xseed}), indent=1))

# =====================================================================================
# D8 ADDITIVE SECTION — payoff-map grid emission (Editor dispatch D8, 2026-07-16).
# Constraints honored: (1) runs strictly AFTER all v1 outputs are written and contains
# NO random draws (deterministic at median knobs), so the v1 outputs cannot be
# disturbed — asserted below against their D7-certified hashes, not assumed;
# (2) ONE reachability definition, named in-file (D7 F21 certified convention);
# (3) the F13/F15 assumed-space caption block travels inside the grid file;
# (4) no new headline statistics — grid-vs-sweep reconciliation only.
# =====================================================================================
import hashlib
_CERT = {"/home/claude/race_model_d3b_results.json": "6f0165edf79c",
         "/home/claude/race_model_d3b_raw_sample.csv": "72b8b25b706c"}
_att = {}
for _p, _e in _CERT.items():
    _g = hashlib.sha256(open(_p, "rb").read()).hexdigest()[:12]
    assert _g == _e, f"BYTE-IDENTITY VIOLATION: {_p} emitted {_g} != certified {_e}"
    _att[_p.split('/')[-1]] = {"certified_sha256_12": _e, "emitted_sha256_12": _g}

# knob medians: log-uniform -> geometric mean; lognormal(0,s) -> 1; U{2..10} -> 6;
# M -> empirical median of the engine raw-draw multiplier distribution (M_all, above)
K_MED, L_MED, U_MED, N_MED = math.sqrt(3e4 * 1e6), math.sqrt(3e5 * 1e7), 1.0, 6.0
M_MED = float(np.median(M_all))
NG = 200
theta_g = np.exp(np.linspace(math.log(3e2), math.log(3e6), NG))
qd_g    = np.exp(np.linspace(math.log(1e4), math.log(1e6), NG))
TH_G, QD_G = np.meshgrid(theta_g, qd_g)                 # row index = Q_d, col index = theta
hz_m  = U_MED * L_MED
a_g   = TH_G - K_MED - hz_m * (MU0 + LAM0 / N0)
Qc_m  = max(M_MED - 1.0, 0.0) * N0

def _grid_region(bcoef):
    Qg = np.maximum(0.0, a_g / bcoef)
    reg = np.zeros(Qg.shape, dtype=int)
    entered = Qg > 0
    reg[entered] = 1
    reg[entered & (N0 + Qg > M_MED * N0)] = 2           # covers M_MED<=1: any entry critical
    return reg

reg_c  = _grid_region((1 + 1 / N_MED) * (TH_G / QD_G + hz_m * LAM0 / N0**2))
reg_oa = _grid_region(TH_G / QD_G + hz_m * LAM0 / N0**2)
theta_paper_med = K_MED + hz_m * (MU0 + LAM0 / N0)      # scalar: theta- and Qd-independent

# REACHABILITY CONVENTION (D7 F21; certified = this script's sweep definition, used
# identically here): a draw/column is REACHABLE iff the linear-solve denominator
# 1 - Qc*(1+1/n)/Q_d > 0. Already-supercritical cases (M <= 1) have Qc = 0, ARE
# reachable, and enter the thin-middle ratio at exactly 1; their share is stated in-file.
den_col = 1.0 - Qc_m * (1 + 1 / N_MED) / qd_g
cc_m = (1 + 1 / N_MED) * hz_m * LAM0 / N0**2
theta_crit_col = np.where(den_col > 0,
                          (theta_paper_med + Qc_m * cc_m) / np.where(den_col > 0, den_col, 1.0),
                          np.nan)

# thin-middle CDF: rank-uniform 500-point downsample of the SWEEP's sorted reachable ratios
thin_sorted = np.sort(thin)
_idx = np.linspace(0, len(thin_sorted) - 1, 500).round().astype(int)
thin_cdf_500 = thin_sorted[_idx]
share_reachable = 1.0 - out_map["share_threshold_unreachable_by_demand"]
share_ratio1_of_reachable = float(np.mean(thin <= 1.0 + 1e-12))

def _shares_int(reg):
    tot = reg.size
    return {"paper": float(np.sum(reg == 0) / tot), "race_subcritical": float(np.sum(reg == 1) / tot),
            "trap_critical": float(np.sum(reg == 2) / tot)}
grid_shares_c, grid_shares_oa = _shares_int(reg_c), _shares_int(reg_oa)
sweep_shares_c = out_map["region_shares_cournot"]
recon_max_dev = max(abs(grid_shares_c[kk] - sweep_shares_c[kk]) for kk in sweep_shares_c)

grid_out = {
 "artifact": "race_map_grid_v1",
 "parent": "race_model_d3b_v1 (seed 26716; D7 referee-certified)",
 "seed": SEED,
 "emitted_by": ("D8 additive section of race_model_d3b.py — deterministic (no random draws), "
                "runs after all parent outputs are written; parent outputs asserted "
                "byte-identical to D7-certified hashes at emission (attestation below)"),
 "byte_identity_attestation": _att,
 "caption_block_F13_F15": ("REGION SHARES AND CLASSES ARE PAYOFF-BELIEF OVER AN ASSUMED BOX — "
                           "parameter belief over ASSUMED payoff sweeps, never probabilities of "
                           "the future. The threshold multiplier M is engine-MODELED, maneuvered-"
                           "regime (conditional on the avoidance system continuing to operate), "
                           "f_imp-conditional, read per F15 as parameter belief. Gradient "
                           "discipline binds: the externality is unpriced, therefore whatever "
                           "entry occurs is over-entry — never 'a million satellites will fly'. "
                           "No dates; distance-to-boundary only. This block travels with the "
                           "data: any consumer (page, figure, caption) inherits it."),
 "grid_spec": {
   "axes": "theta (col, USD/sat-yr) x Q_d (row, satellites), both log-spaced over the sweep box",
   "n_theta": NG, "n_qd": NG,
   "theta_range": [3e2, 3e6], "qd_range": [1e4, 1e6],
   "knob_medians": {"k_usd_per_satyr": K_MED, "L_usd": L_MED, "u": U_MED, "n": N_MED,
                    "M_median_from_engine_raw_draws": M_MED,
                    "theta_paper_at_medians_usd": float(theta_paper_med)},
   "region_encoding": ("region_grid_* : list of n_qd strings (row = Q_d index, ascending); "
                       "each string has n_theta digit chars (col = theta index, ascending); "
                       "0=paper, 1=race-subcritical, 2=trap-critical"),
   "conditioning_note": ("the grid CONDITIONS k, L, u, n, M at their medians; the parent sweep "
                         "INTEGRATES over them — the two agree where conditioning is benign and "
                         "the reconciliation block quantifies the residual")},
 "theta_grid": [float(x) for x in theta_g],
 "qd_grid": [float(x) for x in qd_g],
 "region_grid_cournot": ["".join(str(int(v)) for v in row) for row in reg_c],
 "region_grid_open_access": ["".join(str(int(v)) for v in row) for row in reg_oa],
 "theta_paper_usd_at_medians": float(theta_paper_med),
 "theta_crit_per_qd_column_usd": [None if not np.isfinite(x) else float(x) for x in theta_crit_col],
 "reachability_convention": ("D7 F21 CERTIFIED, one definition throughout: reachable iff "
                             "1 - Qc*(1+1/n)/Q_d > 0 (Qc = max(M-1,0)*N0). M<=1 cases are "
                             "reachable with Qc=0 and enter the thin-middle ratio at exactly 1. "
                             "Unreachable columns carry null theta_crit (demand saturates below "
                             "the cliff — the 'demand ceiling' annotation of fig_racemap)."),
 "thin_middle_cdf": {
   "n_points": 500,
   "source": "parent SWEEP (100k draws), reachable draws under the certified convention — not the grid",
   "downsample": "rank-uniform: sorted ratios sampled at 500 evenly spaced ranks",
   "values": [float(x) for x in thin_cdf_500],
   "share_reachable_of_sweep": float(share_reachable),
   "share_at_ratio_1_of_reachable": share_ratio1_of_reachable,
   "sweep_reference_stats": {"p50": out_map["thin_middle_theta_crit_over_theta_paper_p05_p50_p95"][1],
                             "share_below_2x": out_map["share_thin_middle_below_2x"],
                             "share_below_5x": out_map["share_thin_middle_below_5x"]}},
 "reconciliation_grid_vs_sweep": {
   "sweep_shares_cournot": sweep_shares_c,
   "grid_shares_cournot": grid_shares_c,
   "grid_shares_open_access": grid_shares_oa,
   "max_abs_share_dev_cournot": float(recon_max_dev),
   "note": ("grid cells are equal-weight in log-log (theta, Q_d) — matching the sweep's "
            "log-uniform marginals — but condition the remaining knobs at medians; the "
            "deviation quantifies that conditioning, stated here per dispatch constraint 4")},
}
json.dump(r9(grid_out), open("/home/claude/race_map_grid_v1.json", "w"), indent=1)
print(json.dumps(r9({"D8_grid": {"emitted": "race_map_grid_v1.json",
                                 "byte_identity": "PASS (asserted)",
                                 "grid_shares_cournot": grid_shares_c,
                                 "sweep_shares_cournot": sweep_shares_c,
                                 "max_abs_share_dev": recon_max_dev,
                                 "M_MED": M_MED,
                                 "theta_paper_at_medians": float(theta_paper_med),
                                 "share_at_ratio_1_of_reachable": share_ratio1_of_reachable}}), indent=1))
