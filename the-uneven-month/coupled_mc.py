"""
Coupled-tail Monte Carlo for 'The Uneven Month' magnitude distribution.
Implements the reviewer's deep-uncertainty proposal:
  - FLOOR run: historical-vol calibration (Gaussian, independent months) -> LOWER BOUND on uncertainty.
  - COUPLED run: (i) crisis-regime probability, (ii) tail-dependence via multivariate-t copula
    (df nu) + raised crisis correlation, (iii) crisis-state variance multiplier, and
    (iv) STATE-DEPENDENT basket broadening (the +0.12 realist adder appears/enlarges only in the tail).
Reports TWO headline intervals (floor vs coupled); the gap = quantified 'novel territory'.
Full disclosure of every drawn quantity. Reproducible: fixed seed.
"""
import numpy as np, json
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

SEED = 20260605
rng  = np.random.default_rng(SEED)
N    = 200_000

# ---------------- deterministic core ----------------
MoM = {"C":np.array([0.004,0.003,0.002,0.001,0.001,0.000,0.000]),
       "S":np.array([0.005,0.005,0.004,0.004,0.004,0.003,0.003]),
       "E":np.array([0.008,0.009,0.008,0.007,0.007,0.006,0.006])}
CUM = {k:np.prod(1+v)-1 for k,v in MoM.items()}
PATHS = np.stack([MoM["C"],MoM["S"],MoM["E"]])           # (3,7)
w0  = np.array([0.30,0.45,0.25])
# bracket arrays for the K-factor and state-dependent breadth
hh   = np.array([18.5,21.9,19.0,18.2,21.1,12.1,21.1])
spend= np.array([2750,3500,4580,5830,7500,9580,12500.])
bf   = np.array([1.32,1.24,1.14,1.06,1.00,0.90,0.80])
K0   = float((hh*spend*bf).sum()/1000)                   # 847.45 ; aggregate = rate * K(delta)
Kd   = float((hh*spend).sum()/1000)                      # per-unit-delta uplift to K (858.57)
det_rate = float(w0 @ np.array([CUM["C"],CUM["S"],CUM["E"]]))

# ---------------- shared draw helpers ----------------
def draw_weights_scenarios(n, kappa, rng):
    w = rng.dirichlet(kappa*w0, size=n)
    s = (rng.random(n)[:,None] < np.cumsum(w,axis=1)).argmax(axis=1)
    return s

def exchangeable_chol(rho, d=7):
    Sig = (1-rho)*np.eye(d) + rho*np.ones((d,d))
    return np.linalg.cholesky(Sig)

def mvt_innovations(n, rho, nu, sd, rng):
    """Multivariate-t innovations (df nu), exchangeable corr rho, standardized to marginal sd.
       nu=inf (np.inf) -> Gaussian. Standardization makes nu a PURE tail knob (central sd fixed)."""
    L = exchangeable_chol(rho)
    Z = rng.standard_normal((n,7)) @ L.T
    if np.isinf(nu):
        base = Z
    else:
        g = rng.chisquare(nu, size=n)/nu
        base = Z/np.sqrt(g)[:,None]
        base = base/np.sqrt(nu/(nu-2))      # rescale to unit marginal variance
    return base*sd

def t_level(n, nu, sd, rng):
    if np.isinf(nu): z = rng.standard_normal(n)
    else:
        g = rng.chisquare(nu, size=n)/nu
        z = rng.standard_normal(n)/np.sqrt(g)/np.sqrt(nu/(nu-2))
    return z*sd

def pct(a,p): return float(np.percentile(a,p))
def interval(a): return {"median":pct(a,50),"p05":pct(a,5),"p95":pct(a,95),
                         "p01":pct(a,1),"p99":pct(a,99),"mean":float(a.mean()),"sd":float(a.std())}
def cvar(a,q=95):  # expected shortfall: mean beyond the q-th percentile (upper tail = worse)
    thr=np.percentile(a,q); return float(a[a>=thr].mean())

# ---------------- the engine ----------------
def simulate(n, *, kappa=20.0, sig_month=0.0015, sig_level=0.0008,
             rho=0.0, nu=np.inf, rho_crisis=0.0,
             crisis_mult=0.0, p_crisis=(0.03,0.08,0.30), m_crisis=1.0,
             crisis_drift=0.0, delta_crisis=0.0, rng=rng):
    """crisis_mult scales per-scenario crisis probabilities (0 => floor: no crisis regime).
       Crisis regime is an UPSIDE cascade: monthly drift +crisis_drift, variance x m_crisis,
       correlation -> rho_crisis. nu sets tail fatness/dependence. delta_crisis broadens the
       basket (K) only in crisis."""
    s = draw_weights_scenarios(n, kappa, rng)
    mu = PATHS[s]                                            # (n,7)
    pc = np.array(p_crisis)[s]*crisis_mult
    crisis = rng.random(n) < pc
    innov = mvt_innovations(n, rho, nu, sig_month, rng)
    lev   = t_level(n, nu, sig_level, rng)[:,None]
    if crisis.any():
        innov_c = mvt_innovations(n, rho_crisis, nu, sig_month*np.sqrt(m_crisis), rng)
        lev_c   = t_level(n, nu, sig_level*np.sqrt(m_crisis), rng)[:,None]
        innov[crisis] = innov_c[crisis]
        lev[crisis]   = lev_c[crisis]
    drift = np.where(crisis, crisis_drift, 0.0)[:,None]      # upside cascade shift, per month
    realized = mu + drift + lev + innov
    rate = np.prod(1+realized, axis=1) - 1
    delta = np.where(crisis, delta_crisis, 0.0)
    Krow  = K0 + delta*Kd
    agg   = rate*Krow
    return rate, agg, crisis

# ---------- FLOOR (historical) ----------
FLOOR = dict(kappa=20.0, sig_month=0.0015, sig_level=0.0008, rho=0.0, nu=np.inf,
             crisis_mult=0.0, m_crisis=1.0, delta_crisis=0.0)
r_f, a_f, _ = simulate(N, **FLOOR)

# ---------- COUPLED (default deep-uncertainty knobs) ----------
COUP = dict(kappa=20.0, sig_month=0.0015, sig_level=0.0008,
            rho=0.35, nu=4.0, rho_crisis=0.70,
            crisis_mult=1.0, p_crisis=(0.03,0.08,0.30), m_crisis=4.0,
            crisis_drift=0.004, delta_crisis=0.12)
r_c, a_c, cr_c = simulate(N, **COUP)

# ---------- decomposition: floor -> +tail-dependent rate -> +crisis breadth ----------
r_rate, a_rate, _ = simulate(N, **{**COUP, "delta_crisis":0.0})   # coupling on rate only (K fixed)

res = {"seed":SEED,"N":N,"deterministic":{"rate":det_rate,"aggregate":det_rate*K0,"K0":K0,"Kdelta":Kd},
       "floor_params":{k:(None if v is np.inf else v) for k,v in FLOOR.items()},
       "coupled_params":{k:(None if v is np.inf else v) for k,v in COUP.items()},
       "floor":{"rate":interval(r_f),"aggregate":interval(a_f),
                "VaR95":pct(a_f,95),"VaR99":pct(a_f,99),"CVaR95":cvar(a_f),
                "P_gt_44":float((a_f>CUM['E']*K0).mean()),"P_gt_60":float((a_f>60).mean())},
       "coupled_rateonly":{"aggregate":interval(a_rate),"VaR95":pct(a_rate,95),"CVaR95":cvar(a_rate)},
       "coupled":{"rate":interval(r_c),"aggregate":interval(a_c),
                  "VaR95":pct(a_c,95),"VaR99":pct(a_c,99),"CVaR95":cvar(a_c),
                  "P_gt_44":float((a_c>CUM['E']*K0).mean()),"P_gt_60":float((a_c>60).mean()),
                  "crisis_share":float(cr_c.mean())}}

print("=== HEADLINE: two intervals ($B/mo, 90% CI) ===")
print(f"FLOOR (historical):  median ${pct(a_f,50):.1f}B  90% CI [${pct(a_f,5):.1f}, ${pct(a_f,95):.1f}]  VaR99 ${pct(a_f,99):.1f}  CVaR95 ${cvar(a_f):.1f}")
print(f"COUPLED (deep-unc):  median ${pct(a_c,50):.1f}B  90% CI [${pct(a_c,5):.1f}, ${pct(a_c,95):.1f}]  VaR99 ${pct(a_c,99):.1f}  CVaR95 ${cvar(a_c):.1f}")
print(f"GAP at 95th pct: ${pct(a_c,95)-pct(a_f,95):.1f}B   at 99th: ${pct(a_c,99)-pct(a_f,99):.1f}B   CVaR95 gap: ${cvar(a_c)-cvar(a_f):.1f}B")
print(f"P(agg>$44B): floor {(a_f>CUM['E']*K0).mean():.3f} -> coupled {(a_c>CUM['E']*K0).mean():.3f};  P(agg>$60B): {(a_f>60).mean():.3f} -> {(a_c>60).mean():.3f}")
print(f"decomp 95th pct: floor ${pct(a_f,95):.1f} -> rate-coupled ${pct(a_rate,95):.1f} -> +breadth ${pct(a_c,95):.1f}")
print(f"crisis share of draws (coupled): {cr_c.mean():.3f}")

# ---------- sensitivity over the three knobs (+ delta) ----------
def quick(**kw):
    _,a,_=simulate(70000, **{**COUP, **kw}); return pct(a,95), pct(a,99), float((a>60).mean())
sens={}
for nu_ in (3,4,8,np.inf):
    v95,v99,p60=quick(nu=nu_); sens[f"nu={'inf' if np.isinf(nu_) else nu_}"]={"VaR95":v95,"VaR99":v99,"P_gt60":p60}
for cm in (0.5,1.0,2.0):
    v95,v99,p60=quick(crisis_mult=cm); sens[f"crisis_mult={cm}"]={"VaR95":v95,"VaR99":v99,"P_gt60":p60}
for mc in (2,4,8):
    v95,v99,p60=quick(m_crisis=mc); sens[f"m_crisis={mc}"]={"VaR95":v95,"VaR99":v99,"P_gt60":p60}
for dr in (0.000,0.004,0.008):
    v95,v99,p60=quick(crisis_drift=dr); sens[f"crisis_drift={dr}"]={"VaR95":v95,"VaR99":v99,"P_gt60":p60}
for rc in (0.30,0.70,0.95):
    v95,v99,p60=quick(rho_crisis=rc); sens[f"rho_crisis={rc}"]={"VaR95":v95,"VaR99":v99,"P_gt60":p60}
for dc in (0.06,0.12,0.18):
    v95,v99,p60=quick(delta_crisis=dc); sens[f"delta_crisis={dc}"]={"VaR95":v95,"VaR99":v99,"P_gt60":p60}
res["sensitivity"]=sens
print("\n=== sensitivity (aggregate $B/mo: VaR95 / VaR99 / P(>$60B)) ===")
for k,v in sens.items(): print(f"  {k:18} VaR95 ${v['VaR95']:.1f}  VaR99 ${v['VaR99']:.1f}  P(>60) {v['P_gt60']:.3f}")

# ---------- incidence attenuation under state-dependent breadth (thesis robustness) ----------
def suits_pretax(delta):
    r=det_rate; hit=spend*r*(bf+delta); income=np.array([1250,3125,5208,7292,10417,14583,25000.])
    order=np.argsort(income); I=(hh*income)[order]; B=(hh*hit)[order]
    Tx=np.concatenate([[0],np.cumsum(I)/I.sum()]); By=np.concatenate([[0],np.cumsum(B)/B.sum()])
    return 1-2*np.trapezoid(By,Tx)
inc={f"delta={d}":suits_pretax(d) for d in (0.0,0.12,0.24)}
res["incidence_breadth_attenuation"]=inc
print("\n=== incidence (pre-tax Suits) under uniform basket broadening (thesis check) ===")
for k,v in inc.items(): print(f"  {k:11} Suits {v:.3f}")

json.dump(res, open("coupled_results.json","w"), indent=2)
print("\nwrote coupled_results.json")

# ===================== FIGURES =====================
INK="#211C18"; FL="#2B6CB0"; CO="#A3301B"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"figure.dpi":150,
    "axes.edgecolor":INK,"axes.linewidth":0.8})

fig,axes=plt.subplots(1,2,figsize=(11.5,4.4))
ax=axes[0]
bins=np.linspace(0,90,160)
ax.hist(a_f,bins=bins,density=True,color=FL,alpha=.32,label="floor (historical)")
ax.hist(a_c,bins=bins,density=True,color=CO,alpha=.30,label="coupled (deep-uncertainty)")
for a,c,ls in [(a_f,FL,"--"),(a_c,CO,"-")]:
    ax.axvline(pct(a,95),color=c,lw=1.3,ls=ls)
ax.axvline(det_rate*K0,color=INK,lw=1.4,ls=":",label=f"deterministic ${det_rate*K0:.0f}B")
ax.set_xlim(0,80); ax.set_xlabel("$B per month (Dec run-rate)"); ax.set_ylabel("density")
ax.set_title("Floor vs coupled predictive distribution",fontsize=11,weight="bold")
ax.legend(fontsize=8,frameon=False)
ax.annotate(f"95th pct\n${pct(a_f,95):.0f}B  ${pct(a_c,95):.0f}B",(pct(a_c,95)+1,ax.get_ylim()[1]*.55),fontsize=7.5,color=INK)

ax=axes[1]   # tail focus, log-y
ax.hist(a_f,bins=np.linspace(0,120,200),density=True,color=FL,alpha=.32)
ax.hist(a_c,bins=np.linspace(0,120,200),density=True,color=CO,alpha=.30)
ax.set_yscale("log"); ax.set_xlim(20,110); ax.set_ylim(1e-5,5e-2)
for a,c in [(a_f,FL),(a_c,CO)]:
    ax.axvline(cvar(a),color=c,lw=1.4)
ax.axvline(CUM['E']*K0,color="#8A8175",lw=1,ls=":")
ax.annotate("brief 'all-escalation'\ncorner $44B",(CUM['E']*K0,2e-2),fontsize=6.5,color="#8A8175",ha="right")
ax.set_xlabel("$B per month  (upper tail, log density)"); ax.set_ylabel("log density")
ax.set_title("Upper tail — where the coupling bites (lines = CVaR95)",fontsize=11,weight="bold")
ax.annotate(f"CVaR95\nfloor ${cvar(a_f):.0f}B\ncoupled ${cvar(a_c):.0f}B",(85,1.2e-2),fontsize=8,color=INK)
fig.suptitle("Historical floor understates the cascade tail — the gap quantifies 'novel territory'",
             fontsize=12,weight="bold",y=1.02)
fig.tight_layout(); fig.savefig("fig_coupled.png",bbox_inches="tight",facecolor="white")
print("fig_coupled.png saved")
