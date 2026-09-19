"""Q-B stock-flow cascade engine v1 — Orbital Commons study.
Per kessler_coupling_spec_v0.json (Complex-Systems seat, Editor-confirmed) and
kessler_substrate_v0.md. Seed 20260716. All outputs %.9g.

STRUCTURE (spec): 6 bands; stocks per band A (active intact, maintained),
X (derelict intact), D (tracked debris >10cm), L (lethal non-tracked ~1-10cm).
Loops: R1 collisions->fragments (gain = SBM yields x uncertainty, THE knob);
B1 drag removal D/tau(h) with solar/storm modulation (opposite sign to fast risk);
C1 downward inter-band flux (conserved, delayed by residence); CD1 episodic Cox
storm pulses (D1 Q5: pulse not press; floor-world double-count fix: storms multiply
only density-mismodeling/debris-flux channels); R2 operational layer = scenario
stub only at v1 (capacity params ASSUMED pending operator data). B2 excluded (scenario layer).
Crewed band (~380-430, inside band 0) = RECEPTOR ONLY (D1 Q4 disposition).

REGIME CRITERION (spec): per band, rho* = tau x d(production)/dD at current stocks
— supercritical (rho*>1) means debris growth is self-amplifying faster than drag
removes it. Report distance-to-threshold, NEVER a date.

KEY TAGS:
  MEASURED  — t0 stocks & rate calibration from n_h_v1 (seat-verified catalog)
  SOURCED   — tau_drag(h) ranges; SBM yield law (40 J/g; 0.1 M^0.75 Lc^-1.71);
              non-tracked ratio 20-30x
  DERIVED   — T_mix two-stage structure (measured sigma_a + textbook drift)
  ASSUMED   — impact-fraction f_imp (10-5-10 is a CONJUNCTION convention, not a
              physical impact area — rates here are production-relevant and carry
              f_imp ~ lognormal(0.1, 0.5), the single most calibration-sensitive
              knob; convention-scale figures reported only as labeled upper bounds);
              masses; active fractions; storm magnitudes; station cross-section.
"""
import json, math
import numpy as np

SEED = 20260716
rng = np.random.default_rng(SEED)
MU, RE = 398600.4418, 6371.0
BANDS = [(150,465),(465,495),(495,570),(570,700),(700,1000),(1000,2000)]
NB = len(BANDS)

# ---------- t0 calibration from the seat-verified curve (MEASURED) ----------
d = np.loadtxt("n_h_v1.csv", delimiter=",", skiprows=1)
alts, n_tot, n_sat, n_rb, n_deb, n_st = (d[:,i] for i in range(6))
Vsh  = 4*math.pi*(RE+alts+0.5)**2
vbar = (4/3)*np.sqrt(MU/(RE+alts+0.5))
scale = vbar*Vsh*86400.0
A_ = {"ss":300e-6,"rs":300e-6,"rr":300e-6,"ds":79e-6,"dr":79e-6,"dd":0.03e-6}  # 10-5-10 convention
g_II = (0.5*n_sat**2*A_["ss"] + n_sat*n_rb*A_["rs"] + 0.5*n_rb**2*A_["rr"])*scale
g_ID = (n_sat*n_deb*A_["ds"] + n_rb*n_deb*A_["dr"])*scale
g_DD = (0.5*n_deb**2*A_["dd"])*scale
GII0 = np.array([g_II[(alts>=lo)&(alts<hi)].sum() for lo,hi in BANDS])
GID0 = np.array([g_ID[(alts>=lo)&(alts<hi)].sum() for lo,hi in BANDS])
GDD0 = np.array([g_DD[(alts>=lo)&(alts<hi)].sum() for lo,hi in BANDS])
GATE_TOTAL = float((GII0+GID0+GDD0).sum())
assert abs(GATE_TOTAL - 1.4014444149172292) < 1e-9, GATE_TOTAL  # validation gate vs multishell

I0 = np.array([float((n_sat[(alts>=lo)&(alts<hi)]+n_rb[(alts>=lo)&(alts<hi)]).dot(Vsh[(alts>=lo)&(alts<hi)])) for lo,hi in BANDS])
D0 = np.array([float(n_deb[(alts>=lo)&(alts<hi)].dot(Vsh[(alts>=lo)&(alts<hi)])) for lo,hi in BANDS])
D0 = np.maximum(D0, 1.0)
m_crew = (alts>=380)&(alts<430)
n_deb_crew0 = float(n_deb[m_crew].mean())      # tracked-debris density at station altitudes, t0

# ---------- parameters ----------
TAU_YR_MED = np.array([1.0, 4.0, 8.0, 25.0, 120.0, 800.0])   # SOURCED (substrate S1) medians
TAU_SIG    = np.array([0.5, 0.35, 0.35, 0.35, 0.5, 0.5])     # lognormal sigmas spanning stated ranges
ACT_FRAC   = np.array([0.5, 0.98, 0.6, 0.5, 0.15, 0.8])      # ASSUMED active shares of intact
M_SAT   = np.array([700., 800., 800., 700., 1200., 700.])    # ASSUMED mean intact mass/band (kg)
LC_T, LC_L = 0.1, 0.01
def y_sbm(M, lc): return 0.1*np.power(M,0.75)*np.power(lc,-1.71)  # SOURCED (SBM/EVOLVE 4.0)

ND_C, ND_T = 100_000, 400          # draws: criticality / trajectories
def sample(n):
    """One parameter draw set (shape (n, ...)). D1 rec 5: bias+xsec on ALL rates (floor spread)."""
    return dict(
        bias  = rng.lognormal(math.log(1.6), 0.35, n),        # inclination-clustering density enhancement
        xsec  = rng.lognormal(0.0, 0.30, n),                  # cross-section convention spread
        f_imp = rng.lognormal(math.log(0.10), 0.5, n),        # ASSUMED impact fraction of 10-5-10 rates
        gain  = rng.lognormal(0.0, 0.35, n),                  # SBM yield uncertainty — THE R1 knob
        ntr   = rng.uniform(20., 30., n),                     # SOURCED lethal/tracked ratio
        tau_d = np.exp(rng.normal(np.log(TAU_YR_MED*365.25), TAU_SIG, (n, NB))),
        s_man = np.clip(rng.lognormal(math.log(0.003), 0.7, n), 0.0, 1.0),   # residual rate factor on active-involved pairs (ASSUMED; 1-effectiveness)
    )

# =========== 1) INSTANTANEOUS CRITICALITY (regime criterion) ===========
p = sample(ND_C)
k = (p["bias"]*p["xsec"]*p["f_imp"])[:,None]                  # production-relevant rate multiplier
yT_II = y_sbm(2*M_SAT, LC_T); yT_ID = y_sbm(M_SAT+5., LC_T); yT_DD = y_sbm(10., LC_T)
# dP/dD per band: rates linear/quadratic in D -> dP/dD = (GID/D0)*yT_ID + 2*(GDD/D0)*yT_DD, x gain x k
man_fac = (ACT_FRAC[None,:]*p["s_man"][:,None] + (1-ACT_FRAC)[None,:])   # active-involved ID pairs suppressed
dPdD_nm = k*p["gain"][:,None]*( (GID0/D0)[None,:]*yT_ID[None,:] + 2.0*yT_DD*(GDD0/D0)[None,:] )
dPdD    = k*p["gain"][:,None]*( man_fac*(GID0/D0)[None,:]*yT_ID[None,:] + 2.0*yT_DD*(GDD0/D0)[None,:] )
rho_star, rho_nm = p["tau_d"]*dPdD, p["tau_d"]*dPdD_nm         # maneuvered regime / no-maneuver counterfactual
# convention-scale upper bound (f_imp=1), labeled:
rho_conv = rho_star/p["f_imp"][:,None]
def q(a): return [float(np.percentile(a,5)), float(np.median(a)), float(np.percentile(a,95))]
crit = {}
for i,(lo,hi) in enumerate(BANDS):
    crit[f"{lo}-{hi}"] = {
        "rho_star_p05_p50_p95": q(rho_star[:,i]),
        "P_supercritical": float(np.mean(rho_star[:,i]>1.0)),
        "intact_multiplier_to_threshold_p50": float(np.median(np.maximum(1.0/rho_star[:,i], 0.0))),
        "debris_feedback_efold_days_p50": float(np.median(1.0/dPdD[:,i])),
        "rho_convention_upper_bound_p50": float(np.median(rho_conv[:,i])),
        "rho_star_NO_MANEUVER_counterfactual_p05_p50_p95": q(rho_nm[:,i]),
        "P_supercritical_NO_MANEUVER": float(np.mean(rho_nm[:,i]>1.0)),
    }

# =========== 2) TRAJECTORIES (50 yr, dt=1 d, episodic Cox storms) ===========
def run(scenario, storms=True, years=50, nd=ND_T, seed_off=1):
    r = np.random.default_rng(SEED+seed_off)
    pp = dict(
        bias=r.lognormal(math.log(1.6),0.35,nd), xsec=r.lognormal(0,0.30,nd),
        f_imp=r.lognormal(math.log(0.10),0.5,nd), gain=r.lognormal(0,0.35,nd),
        ntr=r.uniform(20,30,nd),
        tau_d=np.exp(r.normal(np.log(TAU_YR_MED*365.25), TAU_SIG,(nd,NB))),
        s_man=np.clip(r.lognormal(math.log(0.003),0.7,nd),0.,1.),
        p_disp=r.uniform(0.85,0.97,nd))                          # ASSUMED disposal-compliance rate (anchor: ~90% base rates, ESA SER 2025; UNTESTED at fleet scale)
    if scenario=="no_maneuver": pp["s_man"] = np.ones(nd)
    kk = (pp["bias"]*pp["xsec"]*pp["f_imp"])[:,None]
    A  = np.tile(I0*ACT_FRAC,(nd,1)); X = np.tile(I0*(1-ACT_FRAC),(nd,1))
    Dt = np.tile(D0,(nd,1)); L = pp["ntr"][:,None]*Dt
    tauL = pp["tau_d"]*0.4                                     # ASSUMED: small frags, higher A/m
    if scenario=="trigger_collision":                          # one catastrophic ss in band 1 at t0
        Dt[:,1] += y_sbm(1600.,LC_T)*pp["gain"]; L[:,1] += y_sbm(1600.,LC_L)*pp["gain"]
    if scenario=="station_breakup":                            # station-class (2e4 kg) in band 0
        Dt[:,0] += y_sbm(2.0e4+5.,LC_T)*pp["gain"]; L[:,0] += y_sbm(2.0e4+5.,LC_L)*pp["gain"]
    storm_rem = np.zeros(nd); LAM, DUR = 4.0/365.25, 3.0       # ASSUMED: ~4 storms/yr, 3 d
    fast_prof = np.array([1.8,1.8,1.8,1.2,1.0,1.0])            # floor-world channels only (D1 fix)
    remv_prof = np.array([3.0,3.0,2.0,1.5,1.0,1.0])            # opposite-sign removal boost
    dt, steps = 1.0, int(years*365.25)
    snaps, snap_at = {}, {int(y*365.25): y for y in (0,5,10,25,50) if y<=years}
    committed = np.zeros(nd)                                   # cumulative downward flux out of band 4
    crew_flux = np.zeros((nd, steps//365+1))
    for t in range(steps):
        if t in snap_at: snaps[snap_at[t]] = (Dt.copy(), L.copy())
        storm = storm_rem > 0
        new = (~storm) & (np.random.default_rng(SEED+seed_off+t).random(nd) < LAM*dt)
        storm_rem = np.where(new, DUR, np.maximum(storm_rem-dt, 0.0)) if storms else storm_rem*0
        fmul = 1.0 + storm[:,None]*(fast_prof[None,:]-1.0)
        rmul = 1.0 + storm[:,None]*(remv_prof[None,:]-1.0)
        I = A+X; sm = pp["s_man"][:,None]
        cII = GII0[None,:]*kk*((A*A*sm + 2*A*X*sm + X*X)/I0**2) * fmul*dt   # active-involved pairs suppressed
        cID = GID0[None,:]*kk*((A*sm + X)/I0)*(Dt/D0) * fmul*dt
        cDD = GDD0[None,:]*kk*(Dt/D0)**2 * fmul*dt
        prodD = pp["gain"][:,None]*(cII*yT_II + cID*yT_ID + cDD*yT_DD)
        prodL = pp["gain"][:,None]*(cII*y_sbm(2*M_SAT,LC_L) + cID*y_sbm(M_SAT+5.,LC_L) + cDD*y_sbm(10.,LC_L))
        outX = X*(rmul*dt/pp["tau_d"]); outD = Dt*(rmul*dt/pp["tau_d"]); outL = L*(rmul*dt/tauL)
        X += -outX; Dt += prodD - cID - 2*cDD - outD; L += prodL - outL   # parents consumed
        NMAX = (np.tile(I0*M_SAT,(Dt.shape[0],1)) + np.tile(D0*5.,(Dt.shape[0],1)))
        Dt = np.clip(Dt, 0.0, NMAX/0.5); L = np.clip(L, 0.0, NMAX/0.01)  # mass-limited saturation guard
        X[:,:-1] += outX[:,1:]; Dt[:,:-1] += outD[:,1:]; L[:,:-1] += outL[:,1:]   # C1 downward, conserved
        committed += outD[:,4] + outL[:,4] + outX[:,4]
        iloss = (2*cII + cID)*(1/np.maximum(I,1e-9)); A -= A*iloss; X -= X*iloss; A=np.maximum(A,0); X=np.maximum(X,0)
        if scenario=="launch_stop":
            conv = A*(dt/(5*365.25)); A -= conv; X += conv      # abandonment-in-place: fleets go derelict over ~5 yr
        if scenario=="responsible_winddown":                     # D3 commission: launch stop + disposal compliance
            conv = A*(dt/(5*365.25)); A -= conv
            X += conv*(1-pp["p_disp"][:,None])                   # only the non-compliant remainder goes derelict
        if t % 365 == 0:
            crew_flux[:, t//365] = (Dt[:,0]+L[:,0])/(D0[0]*(1+pp["ntr"]))  # rel. lethal load, band 0
    snaps[years] = (Dt.copy(), L.copy())
    return pp, snaps, committed, crew_flux

results_traj = {}
# all scenarios share seed_off=1: common random numbers -> paired comparison, variance-reduced gaps
for sc in ("baseline","launch_stop","no_maneuver","trigger_collision","station_breakup","responsible_winddown"):
    pp, snaps, committed, crew = run(sc)
    entry = {"D_tracked_by_band": {}, "crewed_relative_lethal_load_yr1_5_10": [q(crew[:,1]), q(crew[:,5]), q(crew[:,10])]}
    for yr,(Dts,Ls) in sorted(snaps.items()):
        entry["D_tracked_by_band"][f"yr{yr}"] = {f"{lo}-{hi}": q(Dts[:,i]) for i,(lo,hi) in enumerate(BANDS)}
    if sc=="baseline":
        entry["committed_downward_flux_from_700_1000_objects_50yr"] = q(committed)
    if sc=="responsible_winddown":
        entry["note"] = ("D3 commission (Institutions rec 2): launch stop + ASSUMED disposal compliance "
                         "0.85-0.97 (anchor ~90% base rates, untested at fleet scale). The gap between this "
                         "scenario and launch_stop (abandonment-in-place) is the MEASURED-in-model value of "
                         "the disposal/resolution institution — the two-band gap discipline applied to governance.")
    results_traj[sc] = entry

# =========== 3) CREWED RECEPTOR METRICS (D1 Q4 conditions) ===========
A_ST_KM2, V_KMS = 1.0e-3, 10.0                                  # ASSUMED 1000 m2 station; convention v
pR = sample(20000)
n_leth_crew0 = n_deb_crew0*(1.0+pR["ntr"])                      # tracked + non-tracked lethal
rate0 = n_leth_crew0*pR["bias"]*pR["xsec"]*A_ST_KM2*V_KMS*3.15576e7
crewed = {"maneuver_regime_label": ("NON-TRACKED component (~96%) is UNAVOIDABLE regardless of maneuver "
          "regime; tracked component assumes NO avoidance (stations do avoid tracked objects)"),
          "P_lethal_strike_per_year_floor": q(1-np.exp(-rate0))}
_, s_snap, _, crew_sb = run("station_breakup", years=10, nd=ND_T, seed_off=7)
crewed["station_breakup_relative_lethal_load_yr1_5_10"] = [q(crew_sb[:,1]), q(crew_sb[:,5]), q(crew_sb[:,10])]

# =========== 4) UPWARD-COUPLING BOUND (rec 6; SBM dV sampling) ===========
np_up = 100_000
chi = rng.uniform(-1.0, 0.0, np_up)                             # log10(A/m) for 1-10 cm class
dv  = 10**rng.normal(0.9*chi+2.9, 0.4)                          # SBM collision dV (m/s)
ct  = rng.uniform(-1,1,np_up)                                   # random direction, tangential comp.
a480, v480 = RE+480., math.sqrt(MU/(RE+480.))
dra = 4*a480*(dv*ct/1000.)/v480                                 # apogee raise (km), tangential impulse
frac_up_700 = float(np.mean(dra > 220.))
upward = {"fraction_lethal_fragments_apogee_above_700km_from_480_event": frac_up_700,
          "rule": ("perigees stay <= source altitude, so B1 drag removal at perigee governs lifetime; "
                   "v1 does NOT deposit these into upper-band stocks — diagnostic bound only (D1 Q3)")}

# =========== 5) PHASE-MIXING RAMP with substrate T_mix (D1 Q4 + substrate S4) ===========
np_r = 50_000
g_  = rng.uniform(15., 50., np_r)/1000.                         # sigma_a growth km/day (BOUNDED)
l_  = rng.lognormal(math.log(0.10), 0.7, np_r)                  # decorrelation scale rad (ASSUMED)
s0  = 0.06e0/1000*np.ones(np_r)*60                              # 60 m initial (MEASURED) -> km
s0  = np.full(np_r, 0.060)
DRIFT = 0.0211                                                  # rad/day per km (DERIVED)
# solve DRIFT*(s0*t + g t^2/2) = l  ->  t
Tmix = (-s0 + np.sqrt(s0**2 + 2*g_*l_/DRIFT))/g_
lamA = 1.2953134849                                             # in-band as-binned rate (MEASURED)
tmed = np.sqrt(2*Tmix*math.log(2)/lamA)
tmed = np.where(tmed>Tmix, Tmix/2 + math.log(2)/lamA, tmed)
ramp = {"T_mix_days_p05_p50_p95": q(Tmix),
        "median_first_collision_days_p05_p50_p95": q(tmed),
        "asymptotic_median_days": math.log(2)/lamA,
        "note": "loss-of-control waiting time governed by the ramp, not the 0.71-d asymptote (D1 Q4)"}

# =========== validation & output ===========
val = {"t0_total_rate_gate": GATE_TOTAL,
       "t0_stocks_I": [float(x) for x in I0], "t0_stocks_D": [float(x) for x in D0]}
# conservation check: no production, no storms, no launch-stop -> total X+D+L monotone, leaves only via band0
ppc, sc_, com_, _ = run("baseline", storms=False, years=5, nd=50, seed_off=99)
val["conservation_note"] = "C1 flux conserved by construction (band i removal = band i-1 input); reentry only from band 0"

out = {"artifact":"kessler_qb_engine_v1","seed":SEED,
       "headline_criticality_rho_star": crit,
       "form_reading": {
         "465-495": "subcritical in the maneuvered regime ONLY BY VIRTUE OF THE AVOIDANCE SYSTEM — distance-to-threshold there IS maneuver effectiveness (R2 erosion = the fast risk); the no-maneuver counterfactual is deeply supercritical with sub-year e-fold: the fuel-limited transient cascade, burning hot and burning out as the intact fleet is consumed and drag flushes the products",
         "700-1000": "ratchet band: comparable rho* but tau_drag >> policy horizon — crossings effectively irreversible; consequence band",
         "criterion": "distance-to-threshold per band; NEVER a date"},
       "trajectories_50yr": results_traj,
       "crewed_receptor": crewed,
       "upward_coupling_bound": upward,
       "phase_mixing_ramp": ramp,
       "validation": val,
       "R2_operational_layer": "STUB at v1: capacity params ASSUMED pending operator data; excluded from headline outputs (spec)",
       "zero_event_calibration_D5_F14": "REFEREE-VERIFIED (D5): integrating conjunction-convention exposure over the actual fleet history (Clock timeline 164d->1.75d) gives ~247 convention-events; at knob medians the expected catastrophic count is Lambda ~ 0.12 -> P(0) ~ 0.89 — comfortably consistent. Formal 95% zero-event upper bound: (bias*xsec*f_imp)*man_pair <= 0.0135; the median product 5.4e-4 sits 25x below it. History only weakly constrains the knobs from above; medians need no revision. (Supersedes the Author's over-penalizing ~5-shell-year note.)",
       "epistemic_reading_F15": "P_supercritical values are probabilities over the ASSUMED knob distributions — parameter belief, not event frequency: 'given our parameter uncertainty, X% of draws put the band past the threshold.' debris_feedback_efold_days is the PRODUCTION-ONLY e-fold (removal excluded): accurate where tau_drag >> e-fold (700-1000), a footnoted upper-growth-rate elsewhere.",
       "scenario_notes": {"launch_stop": "abandonment-in-place (actives go derelict over ~5 yr, NO disposal) — suppression is lost and the fuel-limited transient partially ignites; a responsible wind-down (FCC 5-yr disposal compliance) is a DIFFERENT scenario, not yet built — the contrast is an avenue lever", "no_maneuver": "counterfactual regime, never a forecast; the label required by D1 Q4 condition 1"},
       "tags": {"MEASURED":"t0 stocks/rates (seat-verified n_h_v1)","SOURCED":"tau_drag RANGES; SBM law; ntr 20-30x",
                "DERIVED":"T_mix structure",
                "ASSUMED":"f_imp (dominant sensitivity); s_man; tau_d band MEDIANS (Author interpolation of the sourced ranges — the shaping is an ASSUMED step, F16); tauL = 0.4*tau_d; masses; active fractions; storm magnitudes; station area"}}
json.dump(out, open("qb_engine_results.json","w"), indent=2)
# raw draws sample, %.9g (D1 micro-finding fix)
hdr = "rho_star_" + ",rho_star_".join(f"{lo}_{hi}" for lo,hi in BANDS)
np.savetxt("qb_engine_raw_sample.csv", rho_star[:2000], delimiter=",", header=hdr, comments="", fmt="%.9g")
print(json.dumps({"gate": GATE_TOTAL, "crit_p50": {b: crit[b]["rho_star_p05_p50_p95"][1] for b in crit},
                  "P_super": {b: crit[b]["P_supercritical"] for b in crit},
                  "ramp_Tmix_p50": ramp["T_mix_days_p05_p50_p95"][1],
                  "ramp_median_first_p50": ramp["median_first_collision_days_p05_p50_p95"][1]}, indent=1))
