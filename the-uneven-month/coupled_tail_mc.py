"""
Coupled-tail Monte Carlo for 'The Uneven Month' magnitude forecast.
Two runs, identical scenario core, differing ONLY in the coupling layer:
  FLOOR    : historical-vol calibration, independent Gaussian innovations, no crisis regime,
             consensus basket (BFADD=0). Treats the future as a draw from the past => LOWER BOUND.
  COUPLED  : tail-dependent copula (Student-t default; rotated-Clayton variant), fat-tailed
             (Student-t) marginals, a crisis regime (Bernoulli) that multiplies variance, and a
             STATE-DEPENDENT basket broadening (BFADD larger in the crisis tail). Channels go
             wrong together; 'oil is the economy' enters as non-separable breadth in the tail.

Knobs (coupling layer):  p_crisis, nu_cop (tail-dependence; lower=more), crisis_mult, bfadd_crisis.
Everything is drawn from a fixed seed and dumped raw so percentiles can be reproduced, not trusted.
"""
import numpy as np, json
from scipy import stats
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

SEED = 20260605
N    = 200_000
rng  = np.random.default_rng(SEED)

# ---------------- deterministic scenario core (from workbook) ----------------
MoM = {"C": np.array([0.004,0.003,0.002,0.001,0.001,0.000,0.000]),
       "S": np.array([0.005,0.005,0.004,0.004,0.004,0.003,0.003]),
       "E": np.array([0.008,0.009,0.008,0.007,0.007,0.006,0.006])}
PATHS = np.stack([MoM["C"],MoM["S"],MoM["E"]])           # (3,7)
w0    = np.array([0.30,0.45,0.25]); KAPPA = 20.0
CUM   = np.array([np.prod(1+PATHS[i])-1 for i in range(3)])

# burden conversion: aggregate($B) = rate * K(BFADD); K(a)=K0 + a*Kslope
hh   = np.array([18.5,21.9,19.0,18.2,21.1,12.1,21.1])
spend= np.array([2750,3500,4580,5830,7500,9580,12500.])
bf   = np.array([1.32,1.24,1.14,1.06,1.00,0.90,0.80])
K0     = float((hh*spend*bf).sum()/1000)                 # 847.45  (consensus, BFADD=0)
Kslope = float((hh*spend).sum()/1000)                    # dK/dBFADD
print(f"K0={K0:.2f}  Kslope={Kslope:.2f}  (K(0.12)={K0+0.12*Kslope:.1f})")

# ---------------- floor-calibration noise (historical) ----------------
SIG_LEVEL = 0.0008      # persistent monthly level shock sd (compounding)
SIG_MONTH = 0.0015      # transitory monthly innovation sd
# Calibration window: approximate dispersion of monthly headline CPI MoM, ~2021-2026
# (order-of-magnitude; a fitted GARCH on the actual series would refine, see spec sheet).

def draw_core(n):
    w = rng.dirichlet(KAPPA*w0, size=n)
    s = (rng.random(n)[:,None] < np.cumsum(w,axis=1)).argmax(axis=1)
    return PATHS[s], s

def gaussian_indep(n, sigma):
    return rng.normal(0,1,size=(n,7))*sigma[:,None]

def t_copula(n, rho, nu_cop):
    F = rng.normal(0,1,size=(n,1)); eta = rng.normal(0,1,size=(n,7))
    Z = np.sqrt(rho)*F + np.sqrt(1-rho)*eta              # equicorrelation rho
    W = rng.chisquare(nu_cop, size=(n,1))                # shared chi2 -> tail dependence
    T = Z/np.sqrt(W/nu_cop)
    return stats.t.cdf(T, df=nu_cop)

def rot_clayton_copula(n, theta):
    V = rng.gamma(1.0/theta, 1.0, size=(n,1))            # frailty
    E = rng.exponential(1.0, size=(n,7))
    U = (1 + E/V)**(-1.0/theta)                          # Clayton (lower-tail)
    return 1 - U                                         # rotate -> UPPER-tail dependence

def t_marginal(U, nu_marg, sigma):
    z = stats.t.ppf(np.clip(U,1e-9,1-1e-9), df=nu_marg)
    z = z/np.sqrt(nu_marg/(nu_marg-2))                   # standardize to unit variance
    return z*sigma[:,None]

def run_floor(n):
    central, s = draw_core(n)
    level = rng.normal(0,SIG_LEVEL,size=(n,1))
    eps   = gaussian_indep(n, np.full(n, SIG_MONTH))
    realized = central + level + eps
    rate = np.prod(1+realized,axis=1)-1
    return rate, rate*K0, s                              # BFADD=0

def run_coupled(n, family="t", rho=0.35, nu_cop=4.0, nu_marg=5.0, theta=2.0,
                p_crisis=0.15, crisis_mult=2.5, bfadd_normal=0.0, bfadd_crisis=0.18):
    central, s = draw_core(n)
    crisis = rng.random(n) < p_crisis
    sig     = np.where(crisis, SIG_MONTH*crisis_mult, SIG_MONTH)
    lvl_sig = np.where(crisis, SIG_LEVEL*crisis_mult, SIG_LEVEL)
    level = rng.normal(0,1,size=(n,1))*lvl_sig[:,None]
    U = t_copula(n,rho,nu_cop) if family=="t" else rot_clayton_copula(n,theta)
    eps = t_marginal(U, nu_marg, sig)
    realized = central + level + eps
    rate = np.prod(1+realized,axis=1)-1
    K = K0 + np.where(crisis, bfadd_crisis, bfadd_normal)*Kslope   # state-dependent breadth
    return rate, rate*K, s, crisis

def q(a,p): return float(np.percentile(a,p))
def band(a): return dict(mean=float(a.mean()),median=q(a,50),p05=q(a,5),p25=q(a,25),
                         p75=q(a,75),p95=q(a,95),p99=q(a,99),sd=float(a.std()))
def lam_t(rho,nu): return float(2*stats.t.cdf(-np.sqrt((nu+1)*(1-rho)/(1+rho)),df=nu+1))
DEF=dict(rho=0.35,nu_cop=4.0,nu_marg=5.0,p_crisis=0.12,crisis_mult=2.5,bfadd_crisis=0.18,theta=2.0)
CK=('rho','nu_cop','nu_marg','p_crisis','crisis_mult','bfadd_crisis')

# ---------------- run ----------------
fr_rate, fr_agg, _            = run_floor(N)
cp_rate, cp_agg, _, cp_crisis = run_coupled(N, family="t", **{k:DEF[k] for k in CK})
cl_rate, cl_agg, _, _         = run_coupled(N, family="rot_clayton", theta=DEF['theta'],
                                  nu_marg=DEF['nu_marg'], p_crisis=DEF['p_crisis'],
                                  crisis_mult=DEF['crisis_mult'], bfadd_crisis=DEF['bfadd_crisis'])

res={"seed":SEED,"N":N,
     "floor":{"rate":band(fr_rate),"aggregate":band(fr_agg),
              "noise":{"sig_level":SIG_LEVEL,"sig_month":SIG_MONTH,"family":"gaussian-indep","BFADD":0.0}},
     "coupled_t":{"rate":band(cp_rate),"aggregate":band(cp_agg),
                  "params":DEF,"tail_dependence_lambda":lam_t(DEF['rho'],DEF['nu_cop'])},
     "coupled_clayton":{"rate":band(cl_rate),"aggregate":band(cl_agg),
                        "params":{**DEF,"family":"rot_clayton"},
                        "tail_dependence_lambda_U":2**(-1/DEF['theta'])},
     "novel_territory":{
        "ci90_floor":[q(fr_agg,5),q(fr_agg,95)],
        "ci90_coupled_t":[q(cp_agg,5),q(cp_agg,95)],
        "upper_tail_gap_p95":q(cp_agg,95)-q(fr_agg,95),
        "upper_tail_gap_p99":q(cp_agg,99)-q(fr_agg,99),
        "P_agg_gt_44_floor":float((fr_agg>44.17).mean()),
        "P_agg_gt_44_coupled":float((cp_agg>44.17).mean()),
        "P_agg_gt_60_floor":float((fr_agg>60).mean()),
        "P_agg_gt_60_coupled":float((cp_agg>60).mean())}}

# ---------------- knob sensitivity (coupled-t) ----------------
sens={}
for kn,vals in {"p_crisis":[0.05,0.15,0.30],"nu_cop":[200,6,4,2.5],
                "crisis_mult":[1.5,2.5,4.0],"bfadd_crisis":[0.12,0.18,0.25]}.items():
    sens[kn]=[]
    for v in vals:
        kw={k:DEF[k] for k in CK}; kw[kn]=v
        r,a,_,_=run_coupled(60000, family="t", **kw)
        sens[kn].append({"value":v,"agg_p95":q(a,95),"agg_p99":q(a,99),"rate_p95":q(r,95)})
res["sensitivity"]=sens

# ---------------- thesis check: index sign vs BFADD ----------------
incM=np.array([1250,3125,5208,7292,10417,14583,25000.])
def suits_pre(a):
    hit=spend*0.029096*(bf+a); order=np.argsort(incM)
    I=(hh*incM)[order];B=(hh*hit)[order]
    Tx=np.concatenate([[0],np.cumsum(I)/I.sum()]);By=np.concatenate([[0],np.cumsum(B)/B.sum()])
    return float(1-2*np.trapezoid(By,Tx))
res["thesis_check_suits_vs_bfadd"]={f"BFADD={a}":round(suits_pre(a),3) for a in (0.0,0.12,0.18,0.30,0.50)}

json.dump(res,open("coupled_mc_results.json","w"),indent=2)
np.savez_compressed("coupled_mc_raw.npz", floor_rate=fr_rate, floor_agg=fr_agg,
                    coupled_t_rate=cp_rate, coupled_t_agg=cp_agg,
                    coupled_clayton_rate=cl_rate, coupled_clayton_agg=cl_agg)
idx=rng.choice(N,20000,replace=False)
np.savetxt("coupled_mc_sample.csv",
           np.column_stack([fr_rate[idx],fr_agg[idx],cp_rate[idx],cp_agg[idx]]),
           delimiter=",", header="floor_rate,floor_agg,coupled_t_rate,coupled_t_agg",
           comments="", fmt="%.6f")

print(f"\nFLOOR     agg 90% CI [{q(fr_agg,5):.1f}, {q(fr_agg,95):.1f}]  p99 {q(fr_agg,99):.1f}  median {q(fr_agg,50):.1f}")
print(f"COUPLED-t agg 90% CI [{q(cp_agg,5):.1f}, {q(cp_agg,95):.1f}]  p99 {q(cp_agg,99):.1f}  median {q(cp_agg,50):.1f}")
print(f"COUPLED-Clayton agg 90% CI [{q(cl_agg,5):.1f}, {q(cl_agg,95):.1f}]  p99 {q(cl_agg,99):.1f}")
print(f"t-copula tail-dependence lambda = {lam_t(DEF['rho'],DEF['nu_cop']):.3f}  | Clayton lambda_U = {2**(-1/DEF['theta']):.3f}")
print(f"novel-territory upper-tail gap: p95 +{res['novel_territory']['upper_tail_gap_p95']:.1f}B  p99 +{res['novel_territory']['upper_tail_gap_p99']:.1f}B")
print(f"P(agg>$44B): floor {res['novel_territory']['P_agg_gt_44_floor']:.3f} -> coupled {res['novel_territory']['P_agg_gt_44_coupled']:.3f}")
print(f"P(agg>$60B): floor {res['novel_territory']['P_agg_gt_60_floor']:.3f} -> coupled {res['novel_territory']['P_agg_gt_60_coupled']:.3f}")
print("thesis check Suits vs BFADD:", res["thesis_check_suits_vs_bfadd"])

# ---------------- figure ----------------
INK="#211C18"; FL="#2B6CB0"; CP="#A3301B"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"figure.dpi":150})
fig,axes=plt.subplots(1,2,figsize=(11.5,4.4))
for ax,fr,cp,xlab,xlim,title in [
    (axes[0],fr_rate*100,cp_rate*100,"cumulative % since May",(-1,12),"Cumulative price rise by Dec (%)"),
    (axes[1],fr_agg,cp_agg,"$B per month (Dec run-rate)",(0,90),"Added household cost ($B / month)")]:
    ax.hist(fr,bins=160,density=True,color=FL,alpha=.32,label="floor (historical vol)")
    ax.hist(cp,bins=160,density=True,color=CP,alpha=.32,label="coupled tail (t-copula)")
    for a,c in [(fr,FL),(cp,CP)]:
        ax.axvline(np.percentile(a,95),color=c,lw=1.2,ls="--")
    ax.set_title(title,fontsize=11,weight="bold"); ax.set_xlabel(xlab); ax.set_ylabel("density")
    ax.set_xlim(*xlim); ax.legend(fontsize=8,frameon=False,loc="upper right")
ax=axes[1]; frhi=q(fr_agg,95); cphi=q(cp_agg,95)
ax.annotate("",xy=(cphi,ax.get_ylim()[1]*.5),xytext=(frhi,ax.get_ylim()[1]*.5),
            arrowprops=dict(arrowstyle="<->",color=INK,lw=1.2))
ax.annotate(f"'novel territory'\nP95 gap +${cphi-frhi:.0f}B",((frhi+cphi)/2,ax.get_ylim()[1]*.57),
            ha="center",fontsize=8,color=INK)
fig.suptitle("Floor vs coupled-tail magnitude — the gap is the quantified 'novel territory'",
             fontsize=12,weight="bold",y=1.02)
fig.tight_layout(); fig.savefig("fig_coupled.png",bbox_inches="tight",facecolor="white")
print("fig_coupled.png saved")
