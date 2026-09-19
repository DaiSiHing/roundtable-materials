"""
Q-B multi-shell two-band run v1 — on MEASURED n(h) (2026-07-15 catalog).

Floor band: no-maneuver time-to-first-collision from the v3 Eq.7 rate on the
measured per-km densities (10-5-10 cross-sections, 1/2 same-population factor).
Coupled band: global rate-elevation knobs (ASSUMED, flagged; D1 rules on regime
duration and altitude-dependence before these harden).

Carried throughout as a STRUCTURAL SENSITIVITY, never averaged:
  treatment A = as-binned (raw 1-km bins; slot concentration fully expressed)
  treatment B = smoothed-465-495 (that band replaced by its 30-km mean)

Per-band outputs answer "where does the risk live": rate share, P(first
collision in band), and interaction-type split (sat-sat vs debris-involved) —
the bimodal thesis, quantified on measured data.
"""
import json, math
import numpy as np

SEED = 20260715
RNG = np.random.default_rng(SEED)
MU, R_E = 398600.4418, 6371.0

d = np.loadtxt("n_h_v1.csv", delimiter=",", skiprows=1)
alts, n_sat, n_rb, n_deb = d[:,0], d[:,2], d[:,3], d[:,4]
Vsh = 4*math.pi*(R_E+alts+0.5)**2
vbar = (4/3)*np.sqrt(MU/(R_E+alts+0.5))
A = {"ss":300e-6,"rs":300e-6,"rr":300e-6,"ds":79e-6,"dr":79e-6,"dd":0.03e-6}

def rates(ns):
    g_ss = 0.5*ns**2*A["ss"]
    g_debinv = ns*n_deb*A["ds"] + n_rb*n_deb*A["dr"] + 0.5*n_deb**2*A["dd"]
    g_rb = ns*n_rb*A["rs"] + 0.5*n_rb**2*A["rr"]
    scale = vbar*Vsh*86400.0          # per day per shell
    return g_ss*scale, g_debinv*scale, g_rb*scale

BANDS = [(150,465,"below 465 (incl. transit)"),(465,495,"Starlink 480 shell"),
         (495,540,"495-540"),(540,570,"old Starlink 550 shell"),
         (570,700,"570-700"),(700,1000,"legacy debris band"),
         (1000,2000,"upper LEO (OneWeb etc.)")]

def analyze(ns, label):
    g_ss, g_deb, g_rb = rates(ns)
    g_tot = g_ss + g_deb + g_rb
    G = float(g_tot.sum())
    bands = []
    for lo,hi,name in BANDS:
        m = (alts>=lo)&(alts<hi)
        bt = float(g_tot[m].sum())
        bands.append({"band_km":[lo,hi],"name":name,
                      "rate_share":bt/G, "P_first_collision_here":bt/G,
                      "tau_band_days":(1.0/bt if bt>0 else None),
                      "satsat_share_of_band":(float(g_ss[m].sum())/bt if bt>0 else None),
                      "debris_involved_share_of_band":(float(g_deb[m].sum())/bt if bt>0 else None)})
    return {"treatment":label, "total_rate_per_day":G, "clock_days":1.0/G,
            "P_24h":1.0-math.exp(-G) if G<50 else 1.0, "bands":bands}, G

nsA = n_sat.copy()
nsB = n_sat.copy()
mB = (alts>=465)&(alts<495)
nsB[mB] = n_sat[mB].mean()
resA, GA = analyze(nsA, "A_as_binned")
resB, GB = analyze(nsB, "B_smoothed_465_495")

def two_band(G, n_draws=100_000):
    floor_t = RNG.exponential(1.0/G, n_draws)
    dens = RNG.lognormal(np.log(1.6),0.35,n_draws)
    xsec = RNG.lognormal(np.log(1.0),0.30,n_draws)
    storm = np.where(RNG.random(n_draws)<0.10, RNG.uniform(2.,5.,n_draws), 1.0)
    k = dens*xsec*storm
    coup_t = RNG.exponential(1.0/(G*k))
    S = lambda t: {"median_days":float(np.median(t)),"p_24h":float(np.mean(t<=1.0)),
                   "p05":float(np.percentile(t,5)),"p95":float(np.percentile(t,95))}
    return {"floor":S(floor_t),"coupled":S(coup_t)}, floor_t, coup_t

mcA, fA, cA = two_band(GA)
mcB, fB, cB = two_band(GB)

out = {"epoch":"2026-07-15 catalog","seed":SEED,"n_draws":100000,
       "coupled_knobs":"ASSUMED (lognorm 1.6x/0.35; lognorm 1.0x/0.30; p_storm 0.10, 2-5x) — pending D1",
       "treatment_A":resA|{"two_band":mcA}, "treatment_B":resB|{"two_band":mcB},
       "note":"A vs B is a structural sensitivity bracket; never average. Bands' "
              "P_first_collision assumes first event under the global no-maneuver process."}
json.dump(out, open("multishell_results.json","w"), indent=2)
np.savetxt("multishell_raw_sample.csv",
           np.column_stack([fA[:2000],cA[:2000],fB[:2000],cB[:2000]]), delimiter=",",
           header="floorA_days,coupledA_days,floorB_days,coupledB_days", comments="")

for r,mc in ((resA,mcA),(resB,mcB)):
    print(f"\n=== {r['treatment']} — Clock {r['clock_days']:.2f} d, P(<24h) {r['P_24h']:.1%} ===")
    print(f"  floor : median {mc['floor']['median_days']:.2f} d  P(<24h) {mc['floor']['p_24h']:.3f}")
    print(f"  coupled: median {mc['coupled']['median_days']:.2f} d  P(<24h) {mc['coupled']['p_24h']:.3f}")
    for b in r["bands"]:
        if b["rate_share"] > 0.005:
            print(f"    {b['name']:28s} {b['rate_share']:6.1%} of rate | sat-sat {b['satsat_share_of_band']:.0%} | debris-inv {b['debris_involved_share_of_band']:.0%}")
print("\nwrote multishell_results.json, multishell_raw_sample.csv")
