#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
E3-C — the reserve-value-versus-phi companion (grid-g1, d125).

Seat: Complex-Systems & Polycrisis, Study 3. A COMPANION to E3, not a
new study engine: E3 models the manufacturing queue, this models what
happens BEFORE a failure reaches that queue — whether a spare covers it.
The two do not touch, and the no-bridge condition binds: nothing here
speaks to how outages start, and no output of this file feeds E3 or is
fed by it.

Run:  py reserve_pool_mc.py   (writes reserve_pool_results.json + a raw
                               draw sample)

--------------------------------------------------------------------
METHOD COMMITMENTS — STATED BEFORE THE NUMBERS, per this seat's rules
--------------------------------------------------------------------

1. WHAT IS MEASURED. P(covered): the probability that a failed crucial
   LPT is matched to an available, compatible, reachable spare. NOT
   restoration time, NOT outage consequence. A failure not covered
   here enters the manufacturing queue, which is E3's object and is
   not computed here.

2. THE EXPERIMENT IS DOE'S OWN. DOE 2024 IV.4.4, verbatim: the sharing
   programs "do not increase the number of LPT spares, but they do
   improve the ability to deploy spare LPTs when needed." So POOL is
   run at IDENTICAL TOTAL STOCK to SELF - access varies, stock does
   not. A strategic RESERVE is the opposite: it adds stock, remotely,
   and (this is the point of it) at a fungibility of its own choosing.

3. ONE PARAMETER IS ANCHORED. The coverage ratio s = spares / crucial
   units. DOE 2024 IV.4.3: 2016 US high-voltage spare LPTs were "116
   percent of the number of high-voltage LPTs located in substations
   the ORNL analysis designated as 'most crucial'". IV.4.4: 2023
   inventories "increased by over 10 percent", with DOE stating the
   crucial share "has not materially changed". s = 1.16 (2016) and
   s ~= 1.28 (2023) - the second is DERIVED (1.16 x 1.10) under DOE's
   own stated assumption, and is labelled derived everywhere it
   appears. DOE did not publish that product.

4. EVERY OTHER PARAMETER IS ASSUMED AND SWEPT, NEVER PICKED.
   phi (fungibility of the installed base), phi_R (fungibility of a
   purpose-built reserve), tau (transport feasibility), c (fraction of
   spares co-located with the units they would replace), N (pool
   members), u (crucial units per member). The deliverable is the
   SHAPE and the THRESHOLD, never a valuation. DOE IV.4 on the
   underlying question, verbatim: "These are not questions that can be
   answered precisely." A curve that answered it precisely would be
   contradicting its own source.

5. THE COMPATIBILITY MODEL IS OPTIMISTIC FOR POOLING, AND THE
   DIRECTION IS KNOWABLE. Compatibility is drawn independently per
   (spare, failed-unit) pair. Real compatibility is CLUSTERED by
   design family: a utility whose spares fit nothing will fit nobody,
   and a spare that fits one 500/345 unit likely fits its siblings.
   Independence spreads the same fungibility mass evenly and so
   OVERSTATES the pool's reach. Every pooling number here is therefore
   an UPPER BOUND. Biased, not conservative - stated rather than
   buried, per the rule energy set in the seismicity round.

6. TWO EVENT REGIMES, because DOE names both.
   A - INDEPENDENT: one crucial unit fails on its own.
   B - SITE EVENT: a substation is lost, and any spare stored there is
       lost with it. DOE 2024 IV.1: many self-supplied spares are
       "stored in the same substations as the in-service LPTs, making
       the spare LPTs vulnerable to the same events that affect the
       in-service LPTs". c is the co-located fraction; DOE says "many"
       and gives no number, so c is swept and never chosen.

7. WHAT THE HEADLINE IS. M_equiv(phi): the number of purpose-built
   reserve units that would deliver the same coverage gain as the
   whole voluntary pool. It is in units of transformers, so the
   governance half can ask who owns them and who is covered by them.
"""

import json
import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent

SEED = 41
N_PATHS = 40_000
RAW_SAMPLE = 400          # raw draws shipped, per charter engine discipline

# --- anchored ----------------------------------------------------------
S_ANCHORS = {
    "2016_primaried": 1.16,
    "2023_derived": 1.276,       # 1.16 * 1.10, DERIVED - see commitment 3
}

# --- swept (all ASSUMED) -----------------------------------------------
PHI_GRID = [round(0.02 + 0.02 * i, 2) for i in range(49)]   # 0.02 .. 0.98
PHI_R_MEMBERS = (0.80, 0.90, 0.95)      # a purpose-built reserve's own phi
TAU_MEMBERS = (0.70, 0.85, 1.00)        # transport feasibility, POOL
TAU_OWN_MEMBERS = (0.85, 1.00)          # transport feasibility, OWN spares
C_MEMBERS = (0.0, 0.25, 0.50, 0.75)     # co-located share of self-spares
N_MEMBERS = (5, 20, 50)                 # pool members
U_PER_MEMBER = 6                        # crucial units per member


# ======================================================================
# Closed forms - the analytic anchors the MC is checked against
# ======================================================================

def p_uncovered_self(phi, k, tau_own=1.0):
    """No compatible, reachable spare among the failed unit's own k.

    tau_own < 1 because DOE IV.4 says proximity binds WITHIN a utility
    too: a spare "must be close enough to the failed LPT and its
    transportation path must be feasible". tau_own = 1 is generous to
    self-supply and therefore UNDERSTATES pooling; it is kept in the
    sweep as the optimistic-for-self edge, never as the only case.
    """
    return (1.0 - phi * tau_own) ** k


def p_uncovered_pool(phi, tau, k, n_members, tau_own=1.0):
    """Own k at tau_own; the other members' spares at tau."""
    return ((1.0 - phi * tau_own) ** k
            * (1.0 - phi * tau) ** (k * (n_members - 1)))


def p_uncovered_reserve(phi, phi_r, tau, k, m_units):
    """Own spares, plus m purpose-built remote reserve units at phi_R."""
    return (1.0 - phi) ** k * (1.0 - phi_r * tau) ** m_units


def m_equivalent(phi, phi_r, tau, k, n_members):
    """
    How many purpose-built reserve units match the WHOLE pool's gain.

    Solve  (1 - phi_R*tau)^M = (1 - phi*tau)^((N-1)k)  for M.
    Returned as a real number; it is a ratio of logs, not a count of
    procurable objects, and rounds only at render.
    """
    a = math.log(1.0 - phi * tau)
    b = math.log(1.0 - phi_r * tau)
    if b == 0.0:
        return float("inf")
    return (k * (n_members - 1)) * (a / b)


# ======================================================================
# Monte Carlo - carries what the closed forms cannot: the site event
# ======================================================================

def run_cell(rng, phi, tau, c, k, n_members, u, phi_r, m_units, regime):
    """
    One cell of the sweep. Returns coverage probabilities for the three
    mechanisms under the given regime, on COMMON RANDOM NUMBERS: every
    mechanism sees the same failure and the same compatibility draws,
    so differences are the mechanism and not the sampling.
    """
    hit_self = hit_pool = hit_res = 0
    raw = []

    for path in range(N_PATHS):
        # --- which of the failed unit's own spares survive the event ---
        if regime == "site":
            # the failed unit's substation is lost; co-located spares
            # go with it. Each own-spare is co-located with prob c.
            own_alive = sum(1 for _ in range(k) if rng.random() >= c)
        else:
            own_alive = k

        # --- compatibility draws, shared across mechanisms ------------
        own_fit = any(rng.random() < phi for _ in range(own_alive))

        # other members' spares: compatible AND transportable
        others = k * (n_members - 1)
        pool_fit = False
        for _ in range(others):
            if rng.random() < phi and rng.random() < tau:
                pool_fit = True
                break

        # purpose-built remote reserve at its own fungibility
        res_fit = False
        for _ in range(m_units):
            if rng.random() < phi_r and rng.random() < tau:
                res_fit = True
                break

        cov_self = own_fit
        cov_pool = own_fit or pool_fit
        cov_res = own_fit or res_fit

        hit_self += cov_self
        hit_pool += cov_pool
        hit_res += cov_res

        if path < RAW_SAMPLE:
            raw.append({"path": path, "own_alive": own_alive,
                        "own_fit": own_fit, "pool_fit": pool_fit,
                        "res_fit": res_fit})

    n = float(N_PATHS)
    return ({"self": hit_self / n, "pool": hit_pool / n,
             "reserve": hit_res / n}, raw)


def batch_se(rng_seed, phi, tau, c, k, n_members, u, phi_r, m_units,
             regime, batches=40):
    """Batch-means standard error on the pooling gain, per E3's practice."""
    rng = random.Random(rng_seed)
    per = max(N_PATHS // batches, 1)
    gains = []
    for _ in range(batches):
        hs = hp = 0
        for _ in range(per):
            own_alive = (sum(1 for _ in range(k) if rng.random() >= c)
                         if regime == "site" else k)
            own_fit = any(rng.random() < phi for _ in range(own_alive))
            pool_fit = False
            for _ in range(k * (n_members - 1)):
                if rng.random() < phi and rng.random() < tau:
                    pool_fit = True
                    break
            hs += own_fit
            hp += (own_fit or pool_fit)
        gains.append((hp - hs) / float(per))
    m = sum(gains) / len(gains)
    var = sum((g - m) ** 2 for g in gains) / (len(gains) - 1)
    return m, math.sqrt(var / len(gains))


# ======================================================================

def main():
    rng = random.Random(SEED)
    out = {
        "engine": "E3-C reserve/pool companion (grid-g1)",
        "seat": "complex-systems-polycrisis",
        "seed": SEED,
        "n_paths": N_PATHS,
        "dispatch": "d125",
        "method_commitments": "see module docstring - stated before the run",
        "anchored": {
            "coverage_ratio_s": S_ANCHORS,
            "s_2016_source": "DOE 2024 IV.4.3, verbatim: US high-voltage "
                             "spare LPTs were '116 percent of the number "
                             "of high-voltage LPTs located in substations "
                             "the ORNL analysis designated as most "
                             "crucial'",
            "s_2023_status": "DERIVED, not published: 1.16 x 'over 10 "
                             "percent' growth (IV.4.4), under DOE's own "
                             "stated finding that the crucial share 'has "
                             "not materially changed'. DOE did NOT print "
                             "this product and it renders as derived or "
                             "not at all.",
        },
        "assumed_and_swept": {
            "phi": [PHI_GRID[0], PHI_GRID[-1], "step 0.02"],
            "phi_R": PHI_R_MEMBERS, "tau_pool": TAU_MEMBERS,
            "tau_own": TAU_OWN_MEMBERS,
            "c_colocated": C_MEMBERS, "N_members": N_MEMBERS,
            "u_per_member": U_PER_MEMBER,
        },
        "bias_direction": "INDEPENDENT compatibility OVERSTATES pooling. "
                          "Real compatibility is clustered by design "
                          "family. Every pooling figure here is an UPPER "
                          "BOUND on the voluntary substitute's reach.",
        "anchor_check": {},
        "curves": {},
        "m_equivalent": {},
        "site_event": {},
    }

    # ---- anchor check: MC against closed form, regime A, c = 0 --------
    k_probe = max(int(round(S_ANCHORS["2016_primaried"] * U_PER_MEMBER)), 1)
    for phi in (0.10, 0.30, 0.60):
        for tau in (0.85,):
            for nm in (20,):
                cf_self = 1.0 - p_uncovered_self(phi, k_probe)
                cf_pool = 1.0 - p_uncovered_pool(phi, tau, k_probe, nm)
                mc, _ = run_cell(random.Random(SEED + 7), phi, tau, 0.0,
                                 k_probe, nm, U_PER_MEMBER, 0.95, 0,
                                 "independent")
                out["anchor_check"][f"phi={phi}"] = {
                    "closed_form_self": round(cf_self, 5),
                    "mc_self": round(mc["self"], 5),
                    "abs_err_self": round(abs(cf_self - mc["self"]), 5),
                    "closed_form_pool": round(cf_pool, 5),
                    "mc_pool": round(mc["pool"], 5),
                    "abs_err_pool": round(abs(cf_pool - mc["pool"]), 5),
                }

    # ---- the curve: pooling gain vs phi, over the sweep family --------
    for label, s in S_ANCHORS.items():
        k = max(int(round(s * U_PER_MEMBER)), 1)
        rows = []
        for phi in PHI_GRID:
            fam = []
            for tau in TAU_MEMBERS:
                for nm in N_MEMBERS:
                    for t_own in TAU_OWN_MEMBERS:
                        self_cov = 1.0 - p_uncovered_self(phi, k, t_own)
                        pool_cov = 1.0 - p_uncovered_pool(phi, tau, k, nm,
                                                          t_own)
                        fam.append(pool_cov - self_cov)
            selfs = [1.0 - p_uncovered_self(phi, k, t) for t in
                     TAU_OWN_MEMBERS]
            rows.append({"phi": phi,
                         "gain_min": round(min(fam), 5),
                         "gain_max": round(max(fam), 5),
                         "self_cov_min": round(min(selfs), 5),
                         "self_cov_max": round(max(selfs), 5)})
        out["curves"][label] = {"k_spares_per_member": k, "rows": rows}

    # ---- M_equivalent: reserve units that match the whole pool --------
    for label, s in S_ANCHORS.items():
        k = max(int(round(s * U_PER_MEMBER)), 1)
        rows = []
        for phi in PHI_GRID:
            fam = []
            for phi_r in PHI_R_MEMBERS:
                for tau in TAU_MEMBERS:
                    for nm in N_MEMBERS:
                        pool_units = k * (nm - 1)
                        m = m_equivalent(phi, phi_r, tau, k, nm)
                        fam.append(m / pool_units)     # as a FRACTION
            rows.append({"phi": phi,
                         "m_over_pool_min": round(min(fam), 5),
                         "m_over_pool_max": round(max(fam), 5)})
        out["m_equivalent"][label] = rows

    # ---- the site event: what co-location does to each mechanism -----
    k = max(int(round(S_ANCHORS["2016_primaried"] * U_PER_MEMBER)), 1)
    for c in C_MEMBERS:
        cell = {}
        for phi in (0.10, 0.25, 0.50):
            mc, raw = run_cell(random.Random(SEED + 11), phi, 0.85, c, k,
                               20, U_PER_MEMBER, 0.95,
                               m_units=int(round(0.10 * k * 20)),
                               regime="site")
            gain, se = batch_se(SEED + 13, phi, 0.85, c, k, 20,
                                U_PER_MEMBER, 0.95, 0, "site")
            cell[f"phi={phi}"] = {
                "self": round(mc["self"], 5),
                "pool": round(mc["pool"], 5),
                "reserve_at_10pct": round(mc["reserve"], 5),
                "pool_gain": round(mc["pool"] - mc["self"], 5),
                "pool_gain_batch_mean": round(gain, 5),
                "pool_gain_se": round(se, 5),
            }
            if c == 0.50 and phi == 0.25:
                (HERE / "raw_draws_sample.json").write_text(
                    json.dumps({"cell": "c=0.50 phi=0.25 tau=0.85 N=20 "
                                        "regime=site", "seed": SEED + 11,
                                "draws": raw}, indent=1), encoding="utf-8")
        out["site_event"][f"c={c}"] = cell

    (HERE / "reserve_pool_results.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")

    # ---- console summary ---------------------------------------------
    print("anchor check (MC vs closed form):")
    for kk, vv in out["anchor_check"].items():
        print(f"  {kk}: self err {vv['abs_err_self']}  "
              f"pool err {vv['abs_err_pool']}")
    print("\npooling gain vs phi (2016 anchor, min-max over sweep family):")
    for r in out["curves"]["2016_primaried"]["rows"]:
        if abs(r["phi"] * 100 - round(r["phi"] * 100)) < 1e-9 and \
           int(round(r["phi"] * 100)) % 10 == 0:
            print(f"  phi={r['phi']:.2f}  gain {r['gain_min']:.4f}"
                  f"-{r['gain_max']:.4f}   self_cov "
                  f"{r['self_cov_min']:.4f}-{r['self_cov_max']:.4f}")
    print("\nM_equiv / pool size (fraction), 2016 anchor:")
    for r in out["m_equivalent"]["2016_primaried"]:
        if int(round(r["phi"] * 100)) % 10 == 0:
            print(f"  phi={r['phi']:.2f}  {r['m_over_pool_min']:.4f}"
                  f"-{r['m_over_pool_max']:.4f}")
    print("\nsite event, pool gain by co-location fraction c:")
    for ck, cv in out["site_event"].items():
        bits = "  ".join(f"{pk} gain {pv['pool_gain']:.4f}"
                         for pk, pv in cv.items())
        print(f"  {ck}: {bits}")
    print("\nwrote reserve_pool_results.json + raw_draws_sample.json")


if __name__ == "__main__":
    main()
