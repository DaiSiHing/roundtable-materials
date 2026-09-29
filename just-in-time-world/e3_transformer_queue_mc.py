#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
E3 — the transformer queue (Monte Carlo engine). RE-WEIGHING ROUND (d042).

Seat: Complex-Systems & Polycrisis, Study 3 (just-in-time-world).
Design of record: memo-03 (605e52e) + d020 + iron-register e3_design
(joint_refit + referee_m003 blocks). Parameters: e3_energy_params.json
+ delta_d022 + delta_d026 + delta_d032, all LOADED AND ASSERTED (F3).

ENGINE STATE (accumulated d029 -> d034 -> d042):
- IMPORT HISTORY REPLACED: the engine consumes the slice's realized
  path directly (SOURCED, class-validated 617=617): 617/729/539/771/
  1372/1806 for 2019-24. The 2021 U(0.75,0.95) sensitivity member is
  RETIRED INTO THE DATA (this seat's call, offered by energy): the
  realized series carries the actual dip; keeping the member would
  double-count it. One less free knob.
- IMPORT-RESPONSE TERM (energy fit, primaries-only): dead-time
  U(12,30) mo central 18 + ramp U(0.30,0.55)/yr central 0.45 toward a
  ceiling U(2.5,3.5) x pre-boom baseline [ceiling ASSUMED, exposed
  knob]; symmetric-with-lag relaxation [ASSUMED]. Governs 2025+;
  the response state (signal ages) is carried through history so the
  2025 posture is emergent, not initialized by hand.
- TWO-CLASS QUEUE ACTIVATED (memo-03 machinery, dormant -> live):
  priority (queue-jumping direct purchase) and standard (utility)
  classes; priority is served first; per-class exact FIFO waits from
  per-class cumulative curves. Priority share sigma ramps 0 -> sigma
  over 2021-2022 and holds [shape ASSUMED]. Intake RE-SCOPES per
  d026: U(1.1,1.4) is the STANDARD-class 2022-24 multiplier
  (ratified conditioning, in history for two-class runs); the
  priority stream is the excess that carries total intake toward the
  DOE-implied 1.7-2.9x.
- SIGMA CLOSED FOR RENDER PURPOSES; TWO-CLASS DEMOTED (d042/m010):
  xfmr-f12 resolves by FIT at corroboration tier (sigma_arrival
  [0.05,0.21] central 0.09; three instruments one side of >=0.53); the
  purchase was DECLINED 2026-08-20; the derivation is KILLED for
  levels. The posture test failed (Leg-A share 0.053-0.105 vs
  predicted [0.27,0.51]) — the two-class mechanism demotes to MINOR
  CONTRIBUTOR (~1-3 mo at the approved band, arithmetically forced);
  the residual re-weighs toward quote-formation / f13 / f14 (re-rank
  in memo-08 SS3). Members are EMERGENT (s21,s24) pairs on the
  m010-APPROVED band [0.03,0.15]@2021 -> [0.05,0.25]@2024 (provenance
  string carried verbatim; headroom caveat stated) PLUS one MEMORIAL
  member at vendor-implied (0.30,0.45) so the grid spans the
  unresolved Mordor conflict (never-silently-pick). BIAS-DIRECTION
  (econ m005, binding, strengthened): rendered waits are FLOORS.
  The 7.5-year interconnection stock (384.5 GW IAs vs 51.2 GW 2024
  installs) sits beside every calibration block. [2026-09-18, memo-26:
  the SOLD-OUT HORIZONS that sat with it are WITHDRAWN (esr-d040/m043);
  no parameter ever read them; the top three residual candidates are
  now UNRANKED.]
- G-FIXES: G1 all floor blocks now carry render_gated: true with the
  xfmr-f12 gate (machine flag = posture; the QA sweep reads flags);
  G2 both wait metrics with exact shares, per class; G3 quote
  formation joins the resolution list (memo-06; ranked 4th); G4 every
  probe/impossibility sentence here and in results says
  "central-skeleton; MC share >=36 = 0 within ratified bands".

Standing: LEAD TIME IS AN OUTPUT (DO_NOT_INPUT; corridor is diagnostic
and is algebraically the target in backlog units — never counted as
independent, per m003); cause-agnostic pulses; no criticality scalar;
no bridge to grid-g2; K=2 size-classes built, LPT-first (distribution
class queued on its own B primary). SEED = 33.

Usage: full | --smoke | --anchor  (numpy only; energy JSONs required)
"""

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

SEED = 33
N_PATHS = 25_000
HERE = Path(__file__).resolve().parent
# The seven input files belong to the energy seat. Each is looked for
# BESIDE THIS FILE FIRST (the published folder ships them flat, next to
# the engine), then in the energy seat's folder in the study's working
# tree. The inputs are load-and-assert guards: every value the engine
# uses is a constant in this file, and the files are checked against it
# at start, so where they are found cannot change a single draw.
EB_DIR = HERE.parent.parent / "energy-biophysical-economics"
INPUT_NAMES = (
    "e3_energy_params.json",
    "e3_energy_params_delta_d022.json",
    "e3_energy_params_delta_d026.json",
    "e3_energy_params_delta_d032.json",
    "e3_energy_params_delta_esr040.json",
    "e3_energy_params_delta_d045.json",
    "eb_d039_sigma_fit_results.json",
)


def input_path(name):
    """Beside the engine first, then the energy seat's folder."""
    for d in (HERE, EB_DIR):
        p = d / name
        if p.is_file():
            return p
    raise FileNotFoundError(
        "input %s not found beside the engine (%s) or in %s; the engine "
        "needs all seven: %s" % (name, HERE, EB_DIR, ", ".join(INPUT_NAMES)))


PARAMS_PATH = input_path("e3_energy_params.json")
DELTA22_PATH = input_path("e3_energy_params_delta_d022.json")
DELTA26_PATH = input_path("e3_energy_params_delta_d026.json")
DELTA32_PATH = input_path("e3_energy_params_delta_d032.json")
DELTA45_PATH = input_path("e3_energy_params_delta_d045.json")

Y_BURN0 = 2019
Y_END = 2055
N_MON = (Y_END - Y_BURN0 + 1) * 12
def midx(year, mon=1):
    return (year - Y_BURN0) * 12 + (mon - 1)

MAX_AGE = 120

REALIZED_IMPORTS = {2019: 617, 2020: 729, 2021: 539, 2022: 771,
                    2023: 1372, 2024: 1806}   # SOURCED (8504230080)

BANDS = {
    "age_mean": (38.0, 40.0), "age_q25": (0.65, 0.75),
    "beta": (2.5, 4.5), "eta": (55.0, 75.0),
    "N0": (4900, 6799),
    "g_floor": (0.015, 0.03), "g_hist": (0.05, 0.10),
    "g_boom": (0.05, 0.10),
    "intake_standard": (1.1, 1.4),           # d026: STANDARD class band
    "r_max": (0.15, 0.30), "g_imp": (0.0, 0.02),
    "B_med": (7.0, 11.0), "B_sig": (0.25, 0.45),
    "dead_time_mo": (12.0, 30.0),            # d026 response term
    "r_imp": (0.30, 0.55),
    "ceiling_x": (2.5, 3.5),                 # ASSUMED knob (d026)
    "sigma_e_2021": (0.03, 0.15),            # m010-APPROVED band (d042)
    "sigma_e_2024": (0.05, 0.25),            # (supersedes d032's boxes)
    "demand_anchor_2019": 754.0,
    "dom_actual_2019": 137.0, "nameplate": 343.0, "imports_2019": 617.0,
}
D26_SIGMA_SPAN = (0.10, 0.50)                # historical (d026), asserted
D32_BOXES = ((0.15, 0.30), (0.30, 0.45))     # historical (d032), asserted

# d042/m010: variant members are (s21, s24) EMERGENT-share pairs on the
# APPROVED band's diagonal — emergent [0.03,0.15]@2021 -> [0.05,0.25]
# @2024 (m010, released d042; supersedes d032). ASSUMED-tier, variant
# grids ONLY. Provenance (m010 Attachment 1, verbatim, carried in
# results): "fit-derived at corroboration tier from a method killed for
# levels (reconciliation failure, Leg-C boundary); never renders; never
# upgrades without new evidence through the referee."
SIGMA_MEMBERS = ((0.03, 0.05), (0.06, 0.10), (0.09, 0.15),
                 (0.12, 0.20), (0.15, 0.25))
# m010 Attachment 3 — the MEMORIAL MEMBER (never-silently-pick): one
# clearly-labeled member at the superseded vendor-implied level, kept so
# the grid SPANS the unresolved Mordor instrument conflict (fit
# [0.05,0.21] vs corrected-Mordor unit-basis 0.33-0.42) instead of
# silently adjudicating it.
MEMORIAL_MEMBER = (0.30, 0.45)
SIGMA_PROVENANCE = (
    "m010 Attachment 1 (verbatim): fit-derived at corroboration tier "
    "from a method killed for levels (reconciliation failure, Leg-C "
    "boundary); never renders; never upgrades without new evidence "
    "through the referee. Attachment 2 (headroom): the legs see "
    "generation-developer and data-center priority demand only — "
    "non-generation industrial priority purchases (fabs, rail, mining, "
    "hydrogen) are invisible to the EIA-860+LBNL lens, so the fit's "
    "numerator undercounts an unknown amount; the 0.25 top (vs the "
    "fit's 0.21) is that softness made explicit.")
FIT_RESULTS_PATH_NAME = "eb_d039_sigma_fit_results.json"

# d045/d046 — the g-band closure (LTRA 2025, energy memo-10) at the
# PHASE/EXHIBIT layer. Per the delta's reproduction_call split, "the g
# closure touches the scenario axis, not the calibrated history": the
# MC demand bands below (g_floor, g_boom in BANDS) deliberately KEEP
# their pre-closure values this round — every MC output they feed is
# render-gated regardless (floor levels: sigma purchase; coupled:
# expansion increments) — and consume the closure at the next
# MC-touching round.
G_CLOSED_FLOOR = (0.02, 0.035)      # national, absolute clearance
G_CLOSED_COUPLED = (0.05, 0.12)     # 2025-2035; 0.12 = graduated top
G_SWEEP_REGIONAL = 0.14             # ERCOT-derived; NEVER a national render
G_TRIPWIRE = "LTRA-2026 10-yr summer growth outside [168, 280] GW fires a re-band round (closure is against the 2025 vintage of record)"
CORNER_SENTENCE_FIRED = (
    "the boundary is crossed at the corner: hot-zone demand against "
    "the slow end of skill formation is the one region of the map "
    "where the queue diverges")


def load_and_assert_params():
    """F3 load-and-assert across base + both deltas."""
    base = json.loads(PARAMS_PATH.read_text(encoding="utf-8"))
    d22 = json.loads(DELTA22_PATH.read_text(encoding="utf-8"))
    d26 = json.loads(DELTA26_PATH.read_text(encoding="utf-8"))
    def chk(name, got, want):
        assert np.allclose(got, want), (
            f"PARAMS DRIFT {name}: engine {got} vs file {want}")
    chk("hazard.beta", BANDS["beta"], base["hazard"]["beta_band"])
    chk("hazard.eta", BANDS["eta"], base["hazard"]["eta_band"])
    chk("demand.floor_g", BANDS["g_floor"],
        base["demand"]["floor_band_g_per_yr"])
    chk("demand.boom_g", BANDS["g_boom"],
        base["demand"]["coupled_boom"]["g_per_yr_band"])
    chk("demand.anchor", BANDS["demand_anchor_2019"],
        base["demand"]["level_anchor_LPT_class_2019_units"])
    chk("capacity.nameplate", BANDS["nameplate"],
        base["capacity"]["domestic_nameplate_2019_units_yr"])
    chk("capacity.dom", BANDS["dom_actual_2019"],
        base["capacity"]["domestic_actual_2019_units_yr"])
    chk("capacity.imports", BANDS["imports_2019"],
        base["capacity"]["import_2019_units_yr"])
    chk("capacity.g_imp", BANDS["g_imp"],
        base["capacity"]["import_baseline_growth_band_per_yr"])
    chk("capacity.r_max", BANDS["r_max"],
        base["capacity"]["ramp_cap"]["r_max_per_yr_band"])
    chk("build.B_med", BANDS["B_med"],
        base["build_time"]["LPT"]["median_band_mo"])
    chk("build.B_sig", BANDS["B_sig"],
        base["build_time"]["LPT"]["sigma_band"])
    chk("d22.history_g", BANDS["g_hist"],
        d22["history_g_2021_24"]["band_per_yr"])
    chk("d22.intake", BANDS["intake_standard"],
        d22["order_intake_history"]["band"])
    assert "NOT RATIFIED" in d22["import_crunch_2021_24"]["ruling"]
    # d026: realized imports, response term, sigma discipline
    for y, v in REALIZED_IMPORTS.items():
        chk(f"d26.imports.{y}", v,
            d26["import_history_2019_24"]["units_by_year"][str(y)])
    rt = d26["import_response_term"]
    chk("d26.dead_time", BANDS["dead_time_mo"], rt["dead_time_months_band"])
    chk("d26.r_imp", BANDS["r_imp"], rt["r_imp_per_yr_band"])
    chk("d26.ceiling", BANDS["ceiling_x"], rt["ceiling_x_pre_boom_baseline"])
    chk("d26.sigma_band", D26_SIGMA_SPAN,
        d26["intake_band"]["sigma_sensitivity_band_ASSUMED"])
    assert "REPLACED" in d26["import_history_2019_24"]["ruling"]
    assert "never tuned" in d26["intake_band"]["sigma_discipline"]
    assert base["calibration"]["DO_NOT_INPUT"] is True
    # d032: sigma adjudication + emergent sensitivity bands
    d32 = json.loads(DELTA32_PATH.read_text(encoding="utf-8"))
    # d032's boxes are HISTORICAL (superseded by m010's band, d042):
    chk("d32.sigma_e_2021.historical", D32_BOXES[0],
        d32["sigma_sensitivity_band_update"]["emergent_sigma_2021"])
    chk("d32.sigma_e_2024.historical", D32_BOXES[1],
        d32["sigma_sensitivity_band_update"]["emergent_sigma_2024"])
    assert "REJECTED" in d32["sigma_adjudication"]
    assert "variant grids ONLY" in \
        d32["sigma_sensitivity_band_update"]["status"]
    # memo-26 / eb memo-39 (esr-d040): the sold-out horizons are
    # WITHDRAWN. The gate checks the ruling IN FORCE, in energy's esr040
    # delta, and that d032 is flagged superseded - never the historical
    # string (energy's point, adopted: an assert that passes on a
    # withdrawn sentence checks the opposite of the truth). Nothing
    # downstream ever read the key.
    d40 = json.loads(input_path("e3_energy_params_delta_esr040.json")
                     .read_text(encoding="utf-8"))
    assert d40["f13_admissibility"]["soldout_horizons"].startswith(
        "WITHDRAWN IN FULL")
    assert "_superseded_in_part" in d32
    # d032's boxes are asserted as HISTORICAL (file unchanged) — the
    # active band is m010's (d042-released) and supersedes them:
    for s21, s24 in SIGMA_MEMBERS:
        assert BANDS["sigma_e_2021"][0] <= s21 <= BANDS["sigma_e_2021"][1]
        assert BANDS["sigma_e_2024"][0] <= s24 <= BANDS["sigma_e_2024"][1]
        assert s21 <= s24                      # monotone ramp
    # memorial member is exempt from the band boxes BY RULING (m010
    # Attachment 3) and must equal the superseded vendor-implied level:
    assert MEMORIAL_MEMBER == (0.30, 0.45)
    # consistency of the approved band with the sigma fit on record:
    fit = json.loads(input_path(FIT_RESULTS_PATH_NAME)
                     .read_text(encoding="utf-8"))
    c24 = fit["by_year"]["2024"]["sigma_arrival_central"]
    assert BANDS["sigma_e_2024"][0] <= c24 <= BANDS["sigma_e_2024"][1],         "approved 2024 box must contain the fit's arrival central"
    top_env = fit["window_2022_24"]["sigma_delivered_envelope"][1]
    assert BANDS["sigma_e_2024"][1] >= top_env,         "the 0.25 top is the ruled headroom over the window envelope"
    # d045: the g-band closure (exhibit layer)
    d45 = json.loads(DELTA45_PATH.read_text(encoding="utf-8"))
    gc = d45["g_band_closure"]
    chk("d45.floor", G_CLOSED_FLOOR, gc["floor_band_g"])
    chk("d45.coupled", G_CLOSED_COUPLED, gc["coupled_band_g"])
    chk("d45.sweep", G_SWEEP_REGIONAL, gc["sweep_member_g"])
    assert "REGIONAL-EXTREME" in gc["sweep_member_tag"]
    assert "[168, 280]" in gc["tripwire"]
    rr = d45["phase_diagram_render_ruling"]
    assert "CLOSED" in rr["gate"]
    assert CORNER_SENTENCE_FIRED in rr["condition_2_corner_sentence"],         "the fired third sentence must be verbatim from the pre-statement"
    return base, d22, d26, d32, d45


# ---- special functions (no scipy) --------------------------------------
def _gammainc_lower_reg(k, x, iters=200):
    k = np.asarray(k, dtype=np.float64)
    x = np.asarray(x, dtype=np.float64)
    k, x = np.broadcast_arrays(k, x)
    out = np.empty_like(x)
    ser = x < k + 1.0
    ks, xs = k[ser], x[ser]
    if ks.size:
        ap = ks.copy()
        summ = 1.0 / ks
        term = summ.copy()
        for _ in range(iters):
            ap += 1.0
            term = term * xs / ap
            summ += term
            if np.all(np.abs(term) < np.abs(summ) * 1e-14):
                break
        out[ser] = summ * np.exp(-xs + ks * np.log(np.where(xs > 0, xs, 1.0))
                                 - np.vectorize(math.lgamma)(ks))
        out[ser] = np.where(xs > 0, out[ser], 0.0)
    kc, xc = k[~ser], x[~ser]
    if kc.size:
        tiny = 1e-300
        b = xc + 1.0 - kc
        c = np.full_like(xc, 1.0 / tiny)
        d = 1.0 / b
        h = d.copy()
        for i in range(1, iters + 1):
            an = -i * (i - kc)
            b += 2.0
            d = an * d + b
            d = np.where(np.abs(d) < tiny, tiny, d)
            c = b + an / c
            c = np.where(np.abs(c) < tiny, tiny, c)
            d = 1.0 / d
            delt = d * c
            h *= delt
            if np.all(np.abs(delt - 1.0) < 1e-14):
                break
        q = np.exp(-xc + kc * np.log(xc) - np.vectorize(math.lgamma)(kc)) * h
        out[~ser] = 1.0 - q
    return np.clip(out, 0.0, 1.0)


def solve_gamma_k(mean, p_ge_25, lo=0.3, hi=25.0, iters=60):
    mean = np.asarray(mean, dtype=np.float64)
    target = np.asarray(p_ge_25, dtype=np.float64)
    klo = np.full_like(mean, lo)
    khi = np.full_like(mean, hi)
    for _ in range(iters):
        kmid = 0.5 * (klo + khi)
        p = 1.0 - _gammainc_lower_reg(kmid, 25.0 * kmid / mean)
        too_low = p < target
        klo = np.where(too_low, kmid, klo)
        khi = np.where(too_low, khi, kmid)
    return 0.5 * (klo + khi)


def erlang_c(c, rho):
    a = c * rho
    s = 1.0
    term = 1.0
    for n in range(1, c):
        term *= a / n
        s += term
    term_c = term * a / c
    ec = term_c / (1.0 - rho)
    return ec / (s + ec)


# ---- parameter draws ---------------------------------------------------
def draw_params(rng, n, band):
    P = {}
    P["age_mean"] = rng.uniform(*BANDS["age_mean"], n)
    P["age_q25"] = rng.uniform(*BANDS["age_q25"], n)
    P["age_k"] = solve_gamma_k(P["age_mean"], P["age_q25"])
    P["age_theta"] = P["age_mean"] / P["age_k"]
    P["beta"] = rng.uniform(*BANDS["beta"], n)
    P["eta"] = rng.uniform(*BANDS["eta"], n)
    P["N0"] = rng.uniform(*BANDS["N0"], n)
    P["g"] = rng.uniform(*BANDS["g_floor"], n)
    P["g_hist"] = rng.uniform(*BANDS["g_hist"], n)
    P["r_max"] = rng.uniform(*BANDS["r_max"], n)
    P["g_imp"] = rng.uniform(*BANDS["g_imp"], n)
    P["B_med"] = rng.uniform(*BANDS["B_med"], n)
    P["B_sig"] = rng.uniform(*BANDS["B_sig"], n)
    P["intake_std"] = rng.uniform(*BANDS["intake_standard"], n)
    P["dead_time"] = rng.uniform(*BANDS["dead_time_mo"], n)
    P["r_imp"] = rng.uniform(*BANDS["r_imp"], n)
    P["ceiling"] = rng.uniform(*BANDS["ceiling_x"], n)
    if band == "coupled":
        P["g_boom"] = rng.uniform(*BANDS["g_boom"], n)
        P["pulse_lam"] = rng.uniform(0.2, 1.0, n)
        P["fut_stress_on"] = rng.random(n) < 0.30
        P["fut_stress_mag"] = rng.uniform(0.2, 0.5, n)
        P["fut_stress_dur"] = rng.uniform(6, 24, n)
        P["fut_stress_t0"] = rng.uniform(midx(2025), midx(2050), n)
    return P


def annual_hazard(ages, beta, eta):
    a0 = (ages / eta) ** beta
    a1 = ((ages + 1.0) / eta) ** beta
    return 1.0 - np.exp(-(a1 - a0))


# ---- the engine (two-class) --------------------------------------------
def run_band(P, n, rng, band, sigma=None, intake_on=True, store_traj=False):
    """Two-class FIFO queue with priority service. sigma = None for
    one-class, else an (s21, s24) pair of EMERGENT arrival shares
    (d032/d034: consumed emergent-matched — lam_p = lam_s * s/(1-s), so
    the emergent share IS the member label). Share path [shape stated]:
    0 before 2020-07; linear 0 -> s21 over 2020-07..2021-06 (the class
    emerges, hitting its 2021 level mid-year); linear s21 -> s24 over
    2021-07..2024-12 (monotone per d032, linear chosen as the engine's
    call); holds s24 after [ASSUMED as before]. Standard-class intake
    multiplier (2022-24, d026 conditioning) applies when intake_on.
    Import history = realized slice path; 2025+ = response term."""
    ages = np.arange(MAX_AGE, dtype=np.float64)
    beta = P["beta"][:, None]
    eta = P["eta"][:, None]

    cdf_hi = _gammainc_lower_reg(P["age_k"][:, None],
                                 (ages[None, :] + 1.0) / P["age_theta"][:, None])
    cdf_lo = _gammainc_lower_reg(P["age_k"][:, None],
                                 ages[None, :] / P["age_theta"][:, None])
    pmf = np.clip(cdf_hi - cdf_lo, 0, None)
    pmf /= pmf.sum(axis=1, keepdims=True)
    N = pmf * P["N0"][:, None]
    haz = annual_hazard(ages, beta, eta)
    for _ in range(Y_BURN0 - 2014):
        repl = N * haz
        N = np.roll(N - repl, 1, axis=1)
        N[:, -1] += N[:, 0]
        N[:, 0] = repl.sum(axis=1)

    R2019 = (N * haz).sum(axis=1)
    growth0 = np.clip(BANDS["demand_anchor_2019"] - R2019, 50.0, None)

    dom = np.full(n, BANDS["dom_actual_2019"])
    nameplate = BANDS["nameplate"]
    imp_base0 = BANDS["imports_2019"]

    # import-response state (carried through history so 2025 is emergent)
    imp_level = np.full(n, float(REALIZED_IMPORTS[2019]))
    on_age = np.zeros(n)
    off_age = np.zeros(n)

    Qp = np.zeros(n)
    Qs = np.zeros(n)
    cumAp = np.zeros((n, N_MON))
    cumAs = np.zeros((n, N_MON))
    cumSp = np.zeros((n, N_MON))
    cumSs = np.zeros((n, N_MON))
    quote_s = np.zeros((n, N_MON), dtype=np.float32)
    quote_p = np.zeros((n, N_MON), dtype=np.float32)
    backlog_dec24 = None
    imp_2027 = None

    R_y = R2019.copy()
    boom = band == "coupled"
    growth_y = growth0.copy()
    growth_y_prev = growth0.copy()
    for m in range(N_MON):
        mon = m % 12 + 1
        yfrac = m / 12.0
        year = Y_BURN0 + m // 12

        if mon == 1 and m > 0:
            repl = N * haz
            N = np.roll(N - repl, 1, axis=1)
            N[:, -1] += N[:, 0]
            N[:, 0] = repl.sum(axis=1) + growth_y_prev
            R_y = (N * haz).sum(axis=1)

        if midx(2021) <= m <= midx(2024, 12):
            g_eff = P["g_hist"]
        elif boom and midx(2025) <= m <= midx(2032, 12):
            g_eff = P["g_boom"]
        else:
            g_eff = P["g"]
        growth_y = growth_y * (1.0 + g_eff) ** (1.0 / 12.0)
        if mon == 12:
            growth_y_prev = growth_y

        lam_base = (R_y + growth_y) / 12.0
        # emergent-share path (docstring): 0 -> s21 -> s24, then hold
        if sigma is None:
            sig_t = 0.0
        else:
            s21, s24 = sigma
            if m < midx(2020, 7):
                sig_t = 0.0
            elif m <= midx(2021, 6):
                sig_t = s21 * (m - midx(2020, 7) + 1) / 12.0
            elif m <= midx(2024, 12):
                sig_t = s21 + (s24 - s21) * ((m - midx(2021, 7))
                                             / (midx(2024, 12) - midx(2021, 7)))
            else:
                sig_t = s24
        lam_s = lam_base                    # standard = the legacy stream
        if intake_on and midx(2022) <= m <= midx(2024, 12):
            w = 1.0 if m <= midx(2023, 12) else 1.0 - (m - midx(2024)) / 12.0
            lam_s = lam_s * (1.0 + (P["intake_std"] - 1.0) * w)
        # priority stream, EMERGENT-MATCHED (d032/d034): lam_p =
        # lam_s * s/(1-s) including the intake-multiplied standard rate,
        # so the emergent arrival share equals sig_t by construction
        lam_p = lam_s * (sig_t / (1.0 - sig_t)) if sig_t > 0 else 0.0
        A_s = rng.poisson(np.clip(lam_s, 0, None)).astype(np.float64)
        A_p = (rng.poisson(np.clip(lam_p, 0, None)).astype(np.float64)
               if np.any(np.asarray(lam_p) > 0) else np.zeros(n))

        if boom:
            n_ev = rng.poisson(P["pulse_lam"] / 12.0)
            if n_ev.any():
                sizes = np.round(np.exp(rng.normal(math.log(6.0), 0.8, n))
                                 ).clip(2, 60)
                A_s += n_ev * sizes         # pulses replace utility units

        # imports: realized history, response term 2025+
        if year <= 2024:
            imp = np.full(n, float(REALIZED_IMPORTS[year]))
            imp_level = imp.copy()
        else:
            imp = imp_level
        if boom:
            st = (P["fut_stress_on"]
                  & (m >= P["fut_stress_t0"])
                  & (m < P["fut_stress_t0"] + P["fut_stress_dur"]))
            imp = np.where(st, imp * (1.0 - P["fut_stress_mag"]), imp)
        C_m = (dom + imp) / 12.0

        # priority served first (memo-03 mechanics)
        starts_p = np.minimum(C_m, Qp + A_p)
        rem = C_m - starts_p
        starts_s = np.minimum(rem, Qs + A_s)
        Qp = Qp + A_p - starts_p
        Qs = Qs + A_s - starts_s
        cumAp[:, m] = (cumAp[:, m - 1] if m else 0) + A_p
        cumAs[:, m] = (cumAs[:, m - 1] if m else 0) + A_s
        cumSp[:, m] = (cumSp[:, m - 1] if m else 0) + starts_p
        cumSs[:, m] = (cumSs[:, m - 1] if m else 0) + starts_s
        # quote metrics (G2: approximations, formulas stated in spec):
        # a standard order sits behind BOTH backlogs and its service
        # rate is the residual after ongoing priority arrivals —
        # quote_s = (Qp+Qs)/(C - lam_p) + B, clipped where lam_p >= C;
        # a priority order sits behind Qp only at full capacity.
        resid = np.maximum(C_m - (lam_p if np.ndim(lam_p) else
                                  np.full(n, lam_p)), 1e-9)
        quote_s[:, m] = np.minimum((Qp + Qs) / resid, 600.0) + P["B_med"]
        quote_p[:, m] = Qp / np.maximum(C_m, 1e-9) + P["B_med"]
        if m == midx(2024, 12):
            backlog_dec24 = (Qp + Qs).copy()
        if m == midx(2027, 6):
            imp_2027 = imp.copy()

        # response-term state update (signal = total backlog pressure)
        signal = (Qp + Qs) > 3.0 * C_m
        on_age = np.where(signal, on_age + 1, 0.0)
        off_age = np.where(signal, 0.0, off_age + 1)
        if year >= 2025:
            base_now = imp_base0 * (1.0 + P["g_imp"]) ** yfrac
            cap = P["ceiling"] * imp_base0
            grow = signal & (on_age > P["dead_time"]) & (imp_level < cap)
            fall = (~signal) & (off_age > P["dead_time"])
            imp_level = np.where(grow,
                                 np.minimum(cap,
                                            imp_level * (1 + P["r_imp"] / 12)),
                                 imp_level)
            imp_level = np.where(fall,
                                 np.maximum(base_now,
                                            imp_level * (1 - P["r_imp"] / 12)),
                                 imp_level)

        pressured = (Qp + Qs) > 3.0 * C_m
        cap_limit = np.where(P.get("expandable", np.zeros(1, bool)),
                             np.inf, nameplate)
        dom = np.where(pressured,
                       np.minimum(cap_limit, dom * (1.0 + P["r_max"] / 12.0)),
                       dom)

    def cohort_wait(cumA, cumS, y, mo=6):
        t0 = midx(y, mo)
        target = cumA[:, t0]
        covered = cumS >= target[:, None]
        covered[:, :t0] = False
        idx = np.argmax(covered, axis=1)
        never = ~covered.any(axis=1)
        delay = np.where(never, N_MON - t0, idx - t0).astype(np.float64)
        Bdraw = np.exp(rng.normal(np.log(P["B_med"]), P["B_sig"]))
        return delay + Bdraw, never

    waits_s, waits_p = {}, {}
    for y in (2024, 2025, 2027, 2030, 2035, 2040, 2050):
        w, cen = cohort_wait(cumAs, cumSs, y)
        waits_s[y] = {"wait_mo": w, "censored": cen}
        if sigma is not None:
            wp, cenp = cohort_wait(cumAp, cumSp, y)
            waits_p[y] = {"wait_mo": wp, "censored": cenp}

    # diagnostic: emergent total-intake multiple 2022-24 vs pre-boom
    tot_2224 = (cumAs[:, midx(2024, 12)] - cumAs[:, midx(2021, 12)]
                + cumAp[:, midx(2024, 12)] - cumAp[:, midx(2021, 12)])
    base_2224 = 3.0 * BANDS["demand_anchor_2019"]
    ap = cumAp[:, midx(2024, 12)] - cumAp[:, midx(2021, 12)]
    emergent_share = ap / np.maximum(tot_2224, 1e-9)
    return {"emergent_priority_share_2224": emergent_share,
            "waits_s": waits_s, "waits_p": waits_p,
            "quote_s": quote_s, "quote_p": quote_p,
            "backlog_dec24": backlog_dec24,
            "Q_end": Qp + Qs, "R2019": R2019,
            "intake_multiple_2224": tot_2224 / base_2224,
            "imp_2027": imp_2027}


class DetRng:
    def poisson(self, lam):
        return np.asarray(lam, dtype=np.float64)
    def normal(self, mu, sig, size=None):
        return np.asarray(mu, dtype=np.float64)


CENTRAL = {"beta": 3.5, "eta": 65.0, "N0": 5850.0, "age_mean": 39.0,
           "age_q25": 0.70, "g_imp": 0.01, "B_med": 9.0, "B_sig": 0.3448,
           "age_k": 3.047, "age_theta": 12.798, "g": 0.0231,
           "r_max": 0.225, "g_hist": 0.075, "intake_std": 1.25,
           "dead_time": 18.0, "r_imp": 0.45, "ceiling": 3.0}


def fine_boundary(g_vals, r_step=0.005, r_max_hi=0.40,
                  thresholds=(80.0, 60.0, 40.0)):
    """r_needed(g) per m012's boundary rule OF RECORD (SS2: first r with
    quote(2055) <= threshold; thresholds 80/60/40 mo; r step 0.005) —
    the boundary is a BAND across thresholds, drawn as such on the
    exhibit; the strict (thr-40) member is the corner-clearance basis
    (d046). Deterministic central skeleton, one-class, no intake,
    expandable nameplate; quote(2055) = the shipped grid's
    lead_2055_mo (mid-2055)."""
    r_vals = np.round(np.arange(0.0, r_max_hi + 1e-9, r_step), 4)
    _, lead55 = skeleton_grid(np.asarray(g_vals), r_vals)
    out = {}
    for i, g in enumerate(g_vals):
        row = {}
        for thr in thresholds:
            ok = [float(r_vals[j]) for j in range(len(r_vals))
                  if lead55[i, j] <= thr]
            row[f"thr{int(thr)}"] = (ok[0] if ok else None)
        out[f"{g:.4f}"] = row
    return out


def skeleton_grid(g_grid, r_grid):
    G, R = np.meshgrid(g_grid, r_grid, indexing="ij")
    n = G.size
    P = {k: np.full(n, v) for k, v in CENTRAL.items()}
    P["g"] = G.ravel()
    P["r_max"] = R.ravel()
    P["expandable"] = np.ones(n, dtype=bool)
    out = run_band(P, n, DetRng(), "floor", sigma=None, intake_on=False)
    lead = out["quote_s"]
    l2045 = lead[:, midx(2045, 6)]
    l2055 = lead[:, midx(2055, 6)]
    diverges = (l2055 > 60.0) & (l2055 > l2045 + 1.0)
    drains = (l2055 <= 24.0) & (l2055 <= l2045 + 0.5)
    cls = np.where(diverges, 2, np.where(drains, 0, 1))
    return cls.reshape(G.shape), l2055.reshape(G.shape)


# ---- analytic anchors (unchanged, exact forms) -------------------------
def _slot_sim(rng, n_orders, c, service_draw, lam):
    arr = np.cumsum(rng.exponential(1.0 / lam, n_orders))
    free = np.zeros(c)
    waits = np.empty(n_orders)
    for i, t in enumerate(arr):
        j = free.argmin()
        start = max(t, free[j])
        waits[i] = start - t
        free[j] = start + service_draw()
    tail = waits[n_orders // 3:]
    nb = 40
    bm = tail[: (tail.size // nb) * nb].reshape(nb, -1).mean(axis=1)
    return float(tail.mean()), float(bm.std(ddof=1) / math.sqrt(nb))


def anchor_check(seed=SEED, n_orders=400_000):
    out = {}
    rho, B = 0.90, 9.0
    lam = rho / B
    rng = np.random.default_rng(seed + 7)
    wq_sim, se = _slot_sim(rng, n_orders, 1, lambda: B, lam)
    wq_exact = rho * B / (2.0 * (1.0 - rho))
    out["MD1"] = {"rho": rho, "B_mo": B, "Wq_exact_mo": wq_exact,
                  "Wq_sim_mo": wq_sim, "sim_se_mo": se,
                  "matches": bool(abs(wq_sim - wq_exact) < 4 * se)}
    c = 8
    lam = rho * c / B
    rng = np.random.default_rng(seed + 9)
    wq_sim2, se2 = _slot_sim(rng, n_orders, c,
                             lambda: rng.exponential(B), lam)
    wq_exact2 = erlang_c(c, rho) / (c / B - lam)
    out["MMc"] = {"c": c, "rho": rho, "mean_B_mo": B,
                  "Wq_exact_mo": wq_exact2, "Wq_sim_mo": wq_sim2,
                  "sim_se_mo": se2,
                  "matches": bool(abs(wq_sim2 - wq_exact2) < 4 * se2)}
    return out


def pct(x, ps=(5, 25, 50, 75, 95)):
    return {f"p{p}": float(np.percentile(x, p)) for p in ps}


FLOOR_GATE = ("FLOOR COHORT LEVELS GATED — sigma CLOSED for this "
              "study's render purposes (m010): xfmr-f12 resolves by "
              "FIT at corroboration tier (three instruments, one side "
              "of >=0.53); the purchase was DECLINED 2026-08-20 (spec "
              "+ symmetric acceptance stay frozen on file; "
              "Newton-Evans sole cheaper-candidate, item-4 pre-sale "
              "mandatory); the gate stands permanently unless a "
              "referee-routed v3 or a spec-satisfying purchase reopens "
              "it. An ASSUMED sigma cannot carry a rendered number. "
              "BIAS-DIRECTION CONDITION (econ m005, binding — "
              "strengthened by the demotion): the residual is "
              "supply/quote-side — any cohort wait that EVER renders "
              "is a FLOOR and carries 'at least this long' language")


ORDERS_NOTE = (
    "INTERCONNECTION-STOCK FACT (d042/memo-09 A-prime, Queued Up tab 17, "
    "pinned): 384.5 GW of active capacity with signed/draft "
    "interconnection agreements vs 51.2 GW of 2024 installs = 7.5 YEARS "
    "OF INSTALLS - an orders-side PRESSURE fact. These are "
    "interconnection agreements, not transformer purchase orders, and "
    "the fact does not discriminate between quote formation and a real "
    "backlog. SOLD-OUT HORIZONS WITHDRAWN (esr-d040/m043 on d161 s2; eb "
    "memo-39; csp memo-26; 2026-09-18): the 'some lines quoting 2031' and "
    "'Hitachi committed through 2029' clauses this field carried were "
    "never sourced and are struck. What is pinned is one officer's "
    "forward expectation (GE Vernova CEO, press interview, March 2025) "
    "pooled over gas turbines, transformers and switchgear; per m043 it "
    "bounds the transformer line neither above nor below and is not a "
    "quote. Mordor's 'as long as 210 weeks' is a market-research "
    "teaser: diagnostic, corroborates nothing. NOTHING HERE "
    "CORROBORATES A QUOTE LEVEL, and no draw, prior, band or target "
    "ever read this field. The $-to-units conversion stays INADMISSIBLE "
    "as a level (price-vintage wedge +14% realized vs +80% quoted).")


def class_report(out, member):
    ws = {str(y): {**pct(d["wait_mo"]),
                   "censored_share": float(d["censored"].mean())}
          for y, d in out["waits_s"].items()}
    rep = {
        "sigma_member": (None if member is None else
                         {"s21_emergent": member[0],
                          "s24_emergent": member[1]}),
        "standard_class": {
            "order_cohort_realized_wait_months": ws,
            "calibration_2024": {
                "realized_wait_orders_2024_06": {
                    **pct(out["waits_s"][2024]["wait_mo"]),
                    "share_ge_36": float(
                        (out["waits_s"][2024]["wait_mo"] >= 36).mean())},
                "quote_metric_dec24": {
                    **pct(out["quote_s"][:, midx(2024, 12)].astype(float)),
                    "share_ge_36": float(
                        (out["quote_s"][:, midx(2024, 12)] >= 36).mean())},
            },
        },
        "corridor_diagnostic_backlog_dec24": {
            **pct(out["backlog_dec24"]),
            "share_in_1462_3612": float(((out["backlog_dec24"] >= 1462) &
                                         (out["backlog_dec24"] <= 3612)
                                         ).mean()),
            "note": ("diagnostic only; algebraically the target in "
                     "backlog units (m003) — never counted as "
                     "independent evidence"),
        },
        "intake_multiple_2022_24": pct(out["intake_multiple_2224"]),
        "intake_multiple_denominator_note": (
            "multiple = total two-class arrivals 2022-24 / (3 x 754), "
            "the FIXED 2019 LPT-class anchor — not a per-year growing "
            "base (m004 H1, seconding the Author's A1)"),
        "emergent_priority_share_2022_24": pct(
            out["emergent_priority_share_2224"]),
        "share_definition_note": (
            "d032/d034: the priority stream is EMERGENT-MATCHED — "
            "lam_p = lam_s x s/(1-s) including the intake-multiplied "
            "standard rate, so the member labels ARE emergent shares "
            "(the m004 H4 nominal-vs-emergent wedge is retired); the "
            "reported emergent share verifies the construction and "
            "averages the ramp path, so it reads below s24"),
    }
    if member is not None:
        rep["priority_class"] = {
            "calibration_2024_realized": pct(
                out["waits_p"][2024]["wait_mo"]),
            "wait_2027_realized": pct(out["waits_p"][2027]["wait_mo"]),
        }
    return rep


def main(argv):
    smoke = "--smoke" in argv
    anchor_only = "--anchor" in argv
    n = 500 if smoke else N_PATHS

    t0 = time.time()
    load_and_assert_params()
    print(f"E3 re-weighing round (d042) — seed {SEED}, N={n}/run; params "
          f"asserted (base + d022 + d026 + d032 + fit consistency)")

    anchor = anchor_check()
    print(f"  anchors: MD1 {anchor['MD1']['Wq_exact_mo']:.2f}/"
          f"{anchor['MD1']['Wq_sim_mo']:.2f} {anchor['MD1']['matches']}; "
          f"MMc {anchor['MMc']['Wq_exact_mo']:.2f}/"
          f"{anchor['MMc']['Wq_sim_mo']:.2f} {anchor['MMc']['matches']}")
    if anchor_only:
        return 0

    results = {
        "engine": "e3_transformer_queue_mc.py (re-weighing round, d042)",
        "seed": SEED, "n_paths_per_run": n, "class": "LPT (>=100 MVA)",
        "horizon": "2025-2055 monthly (burn-in 2019-2024; age anchor 2014)",
        "params_assert": "PASS (base + d022 + d026 + d032)",
        "sigma_discipline": (
            "d042/m010: sigma members are EMERGENT (s21, s24) ramp "
            "pairs on the APPROVED band's diagonal — emergent "
            "[0.03,0.15]@2021 -> [0.05,0.25]@2024 (supersedes d032) — "
            "ASSUMED-tier, VARIANT GRIDS ONLY, plus ONE MEMORIAL "
            "MEMBER at the superseded vendor-implied (0.30,0.45) so "
            "the grid spans the unresolved Mordor instrument conflict "
            "(never-silently-pick, m010 Attachment 3); a consistency "
            "map, not a fit; no member selected by outcome"),
        "sigma_band_provenance": SIGMA_PROVENANCE,
        "residual_finding": (
            "RE-WEIGHED (d042, on m010): the TWO-CLASS mechanism is "
            "DEMOTED from leading resolution to MINOR CONTRIBUTOR — "
            "the posture test failed (Leg-A delivered share "
            "0.053-0.105 vs engine-derived prediction [0.27,0.51]) "
            "and at the approved band sigma buys ~1-3 months of "
            "standard quote (arithmetically forced on the map). The "
            "~20-24-vs-36 residual belongs to THREE CANDIDATES, "
            "UNRANKED (memo-26, 2026-09-18, superseding memo-08 SS3's "
            "order): QUOTE FORMATION (G3; quoting under a 7.5-year "
            "interconnection stock makes protective quotes rational, "
            "but no quotes-vs-realized primary exists and its ceiling "
            "is unbounded) / f14 DOMESTIC PATH (un-primaried half of "
            "supply; moves the whole map; carries the FLOOR "
            "condition's bias direction) / f13 BACKLOG STATE "
            "(adjudicator if a real backlog primary lands). LAST, and "
            "this one is MEASURED: two-class sigma (minor, ~1-3 mo, "
            "three-instrument corroboration at low levels). Quote "
            "formation was ranked first at d042 on two grounds; the "
            "sold-out-horizon quotes are WITHDRAWN (esr-d040/m043) and "
            "the surviving ground, the interconnection stock, presses "
            "on quote formation and on backlog state alike. An order "
            "among the three is not established"),
        "member_2021_retired": (
            "the U(0.75,0.95) 2021 sensitivity member is RETIRED into "
            "the realized import series (this seat's call per d026): the "
            "539-unit dip is data now; the member would double-count it"),
        "anchor_check": anchor}

    # one-class reference (sigma=0): realized imports + response term,
    # standard intake in history — the new one-class baseline the
    # impossibility statement conditions on (G4: probes central-skeleton;
    # MC share >=36 = 0 within ratified bands)
    rng = np.random.default_rng(SEED)
    P = draw_params(rng, n, "floor")
    out0 = run_band(P, n, rng, "floor", sigma=None, intake_on=True)
    results["floor_oneclass_reference"] = {
        "render_gated": True, "gate": FLOOR_GATE,
        "history": "realized imports (SOURCED) + response term 2025+; "
                   "standard intake U(1.1,1.4) 2022-24; one class",
        "orders_side_context": ORDERS_NOTE,
        **class_report(out0, None)}

    # sigma grid (common random numbers across members) + the memorial
    grid_summary = {}
    for member in SIGMA_MEMBERS + (MEMORIAL_MEMBER,):
        rng_s = np.random.default_rng(SEED)
        P_s = draw_params(rng_s, n, "floor")
        out_s = run_band(P_s, n, rng_s, "floor", sigma=member,
                         intake_on=True)
        memorial = member == MEMORIAL_MEMBER
        lbl = (f"MEMORIAL_vendor_implied_s21_{member[0]:.2f}"
               f"_s24_{member[1]:.2f}" if memorial else
               f"s21_{member[0]:.2f}_s24_{member[1]:.2f}")
        key = f"floor_twoclass_{lbl}"
        results[key] = {
            "render_gated": True, "gate": FLOOR_GATE,
            "orders_side_context": ORDERS_NOTE,
            **({"memorial_member_note": (
                "m010 Attachment 3 (never-silently-pick): the "
                "superseded vendor-implied level, kept so the grid "
                "SPANS the unresolved Mordor instrument conflict (fit "
                "[0.05,0.21] vs corrected-Mordor unit-basis 0.33-0.42) "
                "instead of silently adjudicating it; NOT a band "
                "member")} if memorial else {}),
            **class_report(out_s, member)}
        c = results[key]["standard_class"]["calibration_2024"]
        grid_summary[lbl] = {
            "std_quote_dec24_p50": round(c["quote_metric_dec24"]["p50"], 1),
            "std_realized24_p50": round(
                c["realized_wait_orders_2024_06"]["p50"], 1),
            "std_wait2027_p50": round(
                results[key]["standard_class"]
                ["order_cohort_realized_wait_months"]["2027"]["p50"], 1),
            "prio_wait2027_p50": round(
                results[key]["priority_class"]["wait_2027_realized"]["p50"],
                1),
            "backlog_dec24_p50": round(
                results[key]["corridor_diagnostic_backlog_dec24"]["p50"]),
            "intake_multiple_p50": round(
                results[key]["intake_multiple_2022_24"]["p50"], 2),
        }
        print(f"  {lbl}: std quote-dec24 p50 "
              f"{grid_summary[lbl]['std_quote_dec24_p50']}, "
              f"intake-mult p50 "
              f"{grid_summary[lbl]['intake_multiple_p50']}")

    results["sigma_consistency_map"] = {
        "render_gated": True, "gate": FLOOR_GATE,
        "acceptance_rules_prestated": (
            "memo-06 SS2, written before these runs: R1 the map reports "
            "ALL members; R2 classification thresholds: 'reaches DOE "
            "band' if std quote-dec24 p50 in [30.6, 66.0] (0.85x36 to "
            "1.1x60), 'under' below, 'over' above — G3 quote formation "
            "means 'under' members are noted, not excluded; R3 no "
            "assumed-sigma cohort level renders (xfmr-f12); R4 nothing "
            "in the build consumed 36/60/corridor as input"),
        "map": grid_summary,
        "sigma_ill_conditioning_note": (
            "m004 H4, render-binding on any future f12 render: near the "
            "DOE band the map moves ~4 mo per 0.01 of sigma — sigma "
            "enters as a BAND matched on the EMERGENT share; this "
            "round's members are emergent-matched by construction "
            "(d032/d034)"),
        "classification": {
            k: ("reaches" if 30.6 <= v["std_quote_dec24_p50"] <= 66.0
                else ("under" if v["std_quote_dec24_p50"] < 30.6
                      else "over"))
            for k, v in grid_summary.items()},
    }

    # coupled (render-gated; upper-central member ASSUMED)
    rng_c = np.random.default_rng(SEED + 1000)
    P_c = draw_params(rng_c, n, "coupled")
    out_c = run_band(P_c, n, rng_c, "coupled", sigma=(0.06, 0.10),
                     intake_on=True)
    results["coupled"] = {
        "render_gated": True,
        "gate": "expansion increments + NERC LTRA + sigma gate (band "
                "member (0.06,0.10) ASSUMED here — nearest the fit's "
                "arrival central 0.09)",
        **class_report(out_c, (0.06, 0.10))}

    # phase diagram — EXTENDED AXIS (d045 condition 1: computed, not
    # extrapolated) + LTRA gate CLOSED (d046)
    g_grid = np.round(np.arange(0.0, 0.141, 0.005), 4)
    r_grid = np.round(np.arange(0.0, 0.401, 0.02), 3)
    cls, lead55 = skeleton_grid(g_grid, r_grid)
    fine_g = np.round(np.arange(0.0, 0.141, 0.0025), 4)
    stated = np.array([0.023, 0.048, 0.056, 0.065, 0.139])  # m012 cells
    fine_g = np.unique(np.concatenate([fine_g, stated]))
    fb = fine_boundary(fine_g, r_step=0.005)
    corner_r = fb.get("0.1200", {}).get("thr40")
    results["phase_diagram"] = {
        "render_gated": False,
        "gate": ("LTRA GATE CLOSED (d045 delta / d046): renders subject "
                 "to the fired condition-2 sentence ON the exhibit and "
                 "the m012 caveat package; corner clearance -0.03 at "
                 "(g=0.12, r=0.15)"),
        "g_grid": g_grid.tolist(), "r_max_grid": r_grid.tolist(),
        "classification_0drains_1marginal_2diverges": cls.tolist(),
        "lead_2055_mo": np.round(lead55, 1).tolist(),
        "fine_boundary_r_needed_by_g": fb,
        "boundary_rule_of_record": (
            "m012 SS2: first r with quote(2055) <= threshold; thresholds "
            "80/60/40 mo; r step 0.005; the boundary is a BAND across "
            "thresholds and the exhibit draws it as one; the strict "
            "thr-40 member is the corner-clearance basis (d046)"),
        "corner_computed": {
            "g": 0.12,
            "r_needed_thr80_60_40": [fb.get("0.1200", {}).get("thr80"),
                                     fb.get("0.1200", {}).get("thr60"),
                                     fb.get("0.1200", {}).get("thr40")],
            "clearance_to_cap_floor_0.15_strict": (
                None if corner_r is None else round(0.15 - corner_r, 4)),
            "note": "COMPUTED (d045 condition 1) — energy's linear-local "
                    "extrapolation 0.148-0.158 undershot; the boundary "
                    "steepens beyond g=0.10",
        },
        "condition_2_sentence_fired": CORNER_SENTENCE_FIRED,
        "us_placement": {
            "national_floor_g": list(G_CLOSED_FLOOR),
            "coupled_band_g": list(G_CLOSED_COUPLED),
            "regional_sweep_member_g": G_SWEEP_REGIONAL,
            "regional_tag": "ERCOT-derived REGIONAL-EXTREME: sweep/"
                            "regional annotation only, NEVER a national "
                            "render (d045 delta)",
            "tripwire": G_TRIPWIRE,
        },
        "definition": ("central params, no noise; one-class, no intake; "
                       "r_max = skill-capped growth of capacity itself "
                       "(expandable, no start delay — optimistic bound); "
                       "import-response term ACTIVE; response-term "
                       "CEILING (ASSUMED, central 3x). 2026-09-19 (csp-"
                       "d076; energy memo-43, Erratum 3): where the "
                       "boundary sits depends on that ceiling from about "
                       "3%/yr and MOST at 3.5-5.6%/yr, not at the "
                       "right-hand edge; every published rate clears at "
                       "every ceiling in 2.5-3.5x. Above about 6%/yr "
                       "r_needed is good to two or three search steps "
                       "and the SIGN of the ceiling's effect is not "
                       "resolved: the import response is a delayed "
                       "on/off rule (dead time; symmetric relaxation, "
                       "ASSUMED), and whether its relaxation triggers "
                       "changes the late path (e3_boundary_oscillation_"
                       "probe.py). Energy's replacement sentence (memo-"
                       "43 SS5) is carried on the exhibit verbatim"),
        "m012_caveat_package_verbatim": (
            # RULED esr-d050 / m053 (2026-09-19): csp-d072 s4's text with
            # the referee's one sentence inserted. Supersedes m040 s4.2.
            # AMENDED esr-d052 the same day, three strings: fractions
            # (one rendering on all four carriers); "about 7 to 9 1/2";
            # and "up to 7%/yr" replaced by the margin at the hottest
            # published rate (at 7% it cleared by ONE search step).
            # The old literal said "beyond ~6.5%/yr": 6.5 was a sensitivity
            # onset wearing the wedge's name (eb-d047), and "7.75 to 8.5"
            # was one curve's crossing and re-crossing (memo-22).
            "At the forecast range NERC publishes, the expansion "
            "capability the skill cap permits clears the divergence "
            "boundary — by ×1.3 at the hottest stated regional rate "
            "(5.6%/yr) and absolutely at the national rate, where the "
            "fitted import response alone prevents divergence. The "
            "divergence wedge is real and visible on the diagram: "
            "sustained demand growth beyond roughly 7¾%/yr on the "
            "strictest reading of \"cleared\" and 10½%/yr on the "
            "loosest — the record draws a band, not a line, and all of "
            "it is hotter than any published forecast — pushes the "
            "required expansion rate through the primaried skill-cap "
            "floor (boundary 0.145–0.16/yr at g=0.10). The strictest "
            "curve sits within one search step of that floor from about "
            "7 to 9½%/yr, so its first crossing is located no more "
            "finely than that. Where the boundary sits leans on the "
            "assumed import ceiling from about 3%/yr upward (the ×1.3 "
            "is ×1.25 to ×1.5 across that assumption); that every "
            "published rate clears does not: at the hottest, 5.6%/yr, "
            "the margin is six search steps at the least favorable "
            "ceiling. "
            "Boundaries computed on an optimistic no-start-delay bound "
            "(true clearances are smaller), and the x-axis itself is a "
            "moving forecast: NERC's own 10-year growth projection rose "
            "55→80→132→224 GW across four vintages — the "
            "diagram's placement moves right if the escalation "
            "continues."),
        "mc_band_carry_note": (
            "the MC demand bands (floor g, coupled boom g) deliberately "
            "keep pre-closure values this round per the d045 "
            "reproduction-call split; they feed only render-gated "
            "outputs; the closed bands carry into MC at the next "
            "MC-touching round"),
    }
    print(f"  phase corner(0.12): {fb.get('0.1200')} "
          f"(strict clearance {0.15-corner_r:+.3f})")
    for gq in ("0.0230", "0.0480", "0.0560", "0.0650", "0.1000", "0.1390"):
        print(f"    g={gq}: {fb.get(gq)}")

    dt = time.time() - t0
    results["runtime_s"] = round(dt, 1)
    print(f"  done in {dt:.0f}s")

    if smoke:
        print("  smoke run — no artifacts written")
        return 0

    (HERE / "e3_results.json").write_text(
        json.dumps(results, indent=1), encoding="utf-8")
    # raw draws + per-path outputs (reference + the 0.30 member)
    rng_r = np.random.default_rng(SEED)
    P_r = draw_params(rng_r, n, "floor")
    out_r = run_band(P_r, n, rng_r, "floor", sigma=(0.06, 0.10),
                     intake_on=True)
    np.savez_compressed(
        HERE / "e3_raw.npz",
        **{f"floor_params__{k}": np.asarray(v) for k, v in P.items()},
        oneclass_wait2027_std=out0["waits_s"][2027]["wait_mo"],
        oneclass_quote_dec24=out0["quote_s"][:, midx(2024, 12)],
        oneclass_backlog_dec24=out0["backlog_dec24"],
        central_member_wait2027_std=out_r["waits_s"][2027]["wait_mo"],
        central_member_wait2027_prio=out_r["waits_p"][2027]["wait_mo"],
        central_member_quote_dec24_std=out_r["quote_s"][:, midx(2024, 12)],
        central_member_backlog_dec24=out_r["backlog_dec24"],
        central_member_intake_multiple=out_r["intake_multiple_2224"],
        central_member_imports_2027=out_r["imp_2027"])
    cols = ["beta", "eta", "N0", "g", "g_hist", "r_max", "B_med", "B_sig",
            "intake_std", "dead_time", "r_imp", "ceiling"]
    header = cols + ["oneclass_wait2027", "central_std_wait2027",
                     "central_prio_wait2027", "central_std_quote_dec24"]
    body = np.column_stack(
        [np.asarray(P[c])[:200] for c in cols] +
        [out0["waits_s"][2027]["wait_mo"][:200],
         out_r["waits_s"][2027]["wait_mo"][:200],
         out_r["waits_p"][2027]["wait_mo"][:200],
         out_r["quote_s"][:200, midx(2024, 12)]])
    with open(HERE / "e3_sample.csv", "w", encoding="utf-8") as f:
        f.write(",".join(header) + "\n")
        np.savetxt(f, body, delimiter=",", fmt="%.4f")
    print("  wrote e3_results.json, e3_raw.npz, e3_sample.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
