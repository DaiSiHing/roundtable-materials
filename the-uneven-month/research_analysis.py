"""
Research-grade extensions to the deterministic 'Uneven Month' model:
(1) Monte Carlo predictive distribution of cumulative Dec inflation and aggregate burden.
(2) Parametric bootstrap of the Suits/Kakwani incidence indices (pre- & after-tax bases).
Reproducible: fixed seed. Figures + results JSON written to /home/claude.
"""
import numpy as np, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

rng = np.random.default_rng(20260605)
N = 200_000

# ---------- deterministic core (from the workbook) ----------
# Monthly MoM central paths Jun..Dec (consensus engine)
MoM = {
    "C": np.array([0.004,0.003,0.002,0.001,0.001,0.000,0.000]),
    "S": np.array([0.005,0.005,0.004,0.004,0.004,0.003,0.003]),
    "E": np.array([0.008,0.009,0.008,0.007,0.007,0.006,0.006]),
}
def cum(path): return np.prod(1+path)-1
CUM = {k: cum(v) for k,v in MoM.items()}            # 0.01105 / 0.02834 / 0.05212
w0 = np.array([0.30,0.45,0.25])                      # central scenario weights
K  = 847.45236                                       # aggregate($B/mo) = rate * K

det_rate = float(w0 @ np.array([CUM["C"],CUM["S"],CUM["E"]]))
det_agg  = det_rate*K
print(f"deterministic: rate={det_rate*100:.3f}%  aggregate=${det_agg:.2f}B/mo")
print(f"deterministic envelope (corners): ${CUM['C']*K:.2f}B .. ${CUM['E']*K:.2f}B")

# ---------- Monte Carlo predictive distribution ----------
# Two uncertainty sources:
#  (a) epistemic: scenario weights ~ Dirichlet(kappa*w0)   -> "which path are we on"
#  (b) aleatoric: realized monthly path = central + persistent level shock + iid monthly noise
KAPPA       = 20.0      # weight-confidence (sensitivity below)
SIG_LEVEL   = 0.0008    # persistent (compounding) monthly level surprise, per-month sd
SIG_MONTH   = 0.0015    # transitory month-to-month surprise sd

def run_mc(n, kappa=KAPPA, sig_level=SIG_LEVEL, sig_month=SIG_MONTH, rng=rng):
    w   = rng.dirichlet(kappa*w0, size=n)                      # (n,3) weight draws
    # (A) distribution of the MODEL'S EXPECTED rate, from weight uncertainty only
    exp_rate = w @ np.array([CUM["C"],CUM["S"],CUM["E"]])
    # (B) PREDICTIVE distribution of the REALIZED rate
    s   = (rng.random(n)[:,None] < np.cumsum(w,axis=1)).argmax(axis=1)  # categorical per row
    paths = np.stack([MoM["C"],MoM["S"],MoM["E"]])[s]          # (n,7) central path for drawn scenario
    level = rng.normal(0, sig_level, size=(n,1))               # persistent shift
    noise = rng.normal(0, sig_month, size=(n,7))               # transitory
    realized = paths + level + noise
    real_rate = np.prod(1+realized, axis=1) - 1
    return exp_rate, real_rate, s

exp_rate, real_rate, s_draw = run_mc(N)
real_agg = real_rate*K

def pct(a,p): return float(np.percentile(a,p))
def summ(a):
    return dict(mean=float(a.mean()), median=pct(a,50), p05=pct(a,5), p95=pct(a,95),
                p25=pct(a,25), p75=pct(a,75), sd=float(a.std()))

res = {"deterministic":{"rate":det_rate,"aggregate":det_agg,
                        "env_lo":CUM['C']*K,"env_hi":CUM['E']*K},
       "mc":{"expected_rate":summ(exp_rate),"realized_rate":summ(real_rate),
             "realized_aggregate":summ(real_agg),
             "params":{"kappa":KAPPA,"sig_level":SIG_LEVEL,"sig_month":SIG_MONTH,"N":N}}}

# Law-of-total-variance: condition on scenario s -> between-scenario (structural) vs within (path noise)
gm = np.array([real_rate[s_draw==k].mean() for k in range(3)])
gv = np.array([real_rate[s_draw==k].var()  for k in range(3)])
freq = np.array([(s_draw==k).mean() for k in range(3)])
var_total = real_rate.var()
var_between = float(((gm-real_rate.mean())**2*freq).sum())     # which-scenario (structural)
var_within  = float((gv*freq).sum())                           # path noise given scenario
# odds (weight) epistemic layer: how much the 90% CI moves if weights are FIXED vs Dirichlet
_,rr_fixed,_ = run_mc(80000, kappa=1e6)                         # ~fixed weights at w0
res["mc"]["variance_decomp"]={"total":var_total,
    "between_scenario_frac":var_between/var_total,
    "within_scenario_noise_frac":var_within/var_total,
    "ci90_fixed_weights":[pct(rr_fixed,5),pct(rr_fixed,95)],
    "ci90_uncertain_weights":[pct(real_rate,5),pct(real_rate,95)]}

# decision-relevant tail probabilities
res["mc"]["tail_probs"]={
    "P_rate_gt_4pct":float((real_rate>0.04).mean()),
    "P_rate_lt_1pct":float((real_rate<0.01).mean()),
    "P_agg_gt_envHi_44B":float((real_agg>CUM['E']*K).mean()),
    "P_agg_lt_envLo_9_4B":float((real_agg<CUM['C']*K).mean()),
    "P_agg_gt_det_24_7B":float((real_agg>det_agg).mean())}

# sensitivity to kappa and sigma
sens=[]
for kp in (10,20,50):
    _,rr,_=run_mc(60000,kappa=kp); sens.append(("kappa",kp,pct(rr*K,5),pct(rr*K,95)))
for sm in (0.0010,0.0015,0.0030):
    _,rr,_=run_mc(60000,sig_month=sm); sens.append(("sig_month",sm,pct(rr*K,5),pct(rr*K,95)))
res["mc"]["sensitivity"]=sens

print(f"MC realized rate 90% CI: [{pct(real_rate,5)*100:.2f}%, {pct(real_rate,95)*100:.2f}%] median {pct(real_rate,50)*100:.2f}%")
print(f"MC realized aggregate 90% CI: [${pct(real_agg,5):.1f}B, ${pct(real_agg,95):.1f}B] median ${pct(real_agg,50):.1f}B")
print(f"variance: between-scenario={var_between/var_total:.0%}  within-scenario noise={var_within/var_total:.0%}")
print(f"P(agg>$44B)={res['mc']['tail_probs']['P_agg_gt_envHi_44B']:.3f}  P(agg<$9.4B)={res['mc']['tail_probs']['P_agg_lt_envLo_9_4B']:.3f}")

# ---------- Incidence index bootstrap ----------
labels=["<$25k","$25-50k","$50-75k","$75-100k","$100-150k","$150-200k","$200k+"]
hh   = np.array([18.5,21.9,19.0,18.2,21.1,12.1,21.1])
spend= np.array([2750,3500,4580,5830,7500,9580,12500.])
bf0  = np.array([1.32,1.24,1.14,1.06,1.00,0.90,0.80])
incM0= np.array([1250,3125,5208,7292,10417,14583,25000.])
tax0 = np.array([.05,.10,.15,.18,.21,.24,.28])
r_fixed = det_rate   # indices are scenario-invariant; r cancels, value irrelevant

def indices(hh,spend,bf,incM,tax,base="pre"):
    hit = spend*r_fixed*bf
    income = incM if base=="pre" else incM*(1-tax)
    order=np.argsort(income)
    I=(hh*income)[order]; B=(hh*hit)[order]; pop=hh[order]/hh.sum()
    p =np.concatenate([[0],np.cumsum(pop)])
    Ly=np.concatenate([[0],np.cumsum(I)/I.sum()])
    By=np.concatenate([[0],np.cumsum(B)/B.sum()])
    G=1-2*np.trapezoid(Ly,p); C=1-2*np.trapezoid(By,p)
    S=1-2*np.trapezoid(By,Ly)            # Suits: burden share vs cumulative income share (Ly)
    return S, C-G, C, G

point={b:indices(hh,spend,bf0,incM0,tax0,b)[:2] for b in ("pre","after")}

# Parametric bootstrap over MODELED inputs (sourced hh/spend get small survey noise):
NB=100_000
def boot(n, base="pre", rng=rng):
    Sv=np.empty(n); Kv=np.empty(n)
    # vectorized draws
    bf  = bf0*np.exp(rng.normal(0,0.06,size=(n,7)))                 # basket factor ~6% CV (modeled)
    incM= incM0*np.exp(rng.normal(0,0.10,size=(n,7)))               # representative income ~10% CV (modeled)
    tax = np.clip(tax0+rng.normal(0,0.02,size=(n,7)),0,0.6)         # +/-2pp effective rate
    hhd = hh*np.exp(rng.normal(0,0.025,size=(n,7)))                 # survey sampling ~2.5%
    spd = spend*np.exp(rng.normal(0,0.03,size=(n,7)))               # survey sampling ~3%
    for i in range(n):
        Sv[i],Kv[i],_,_=indices(hhd[i],spd[i],bf[i],incM[i],tax[i],base)
    return Sv,Kv

boot_res={}
for base in ("pre","after"):
    Sv,Kv=boot(NB,base)
    boot_res[base]={"suits":{"point":point[base][0],"median":pct(Sv,50),"p05":pct(Sv,5),"p95":pct(Sv,95)},
                    "kakwani":{"point":point[base][1],"median":pct(Kv,50),"p05":pct(Kv,5),"p95":pct(Kv,95)},
                    "prob_regressive":float((Sv<0).mean())}
    print(f"[{base}] Suits point {point[base][0]:.3f}  90% CI [{pct(Sv,5):.3f},{pct(Sv,95):.3f}]  P(reg)={(Sv<0).mean():.4f}")
res["incidence_bootstrap"]={"params":{"bf_cv":0.06,"income_cv":0.10,"tax_sd":0.02,"hh_cv":0.025,"spend_cv":0.03,"NB":NB},
                            **boot_res}
# keep arrays for plotting
Sv_pre,Kv_pre=boot(40000,"pre"); Sv_aft,Kv_aft=boot(40000,"after")

with open("research_results.json","w") as f: json.dump(res,f,indent=2)
print("results written.")

# =================== FIGURES ===================
INK="#211C18"; ACCENT="#A3301B"; BLUE="#2B6CB0"; GREEN="#3B7A52"; GRID="#d8cfc0"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.edgecolor":INK,
    "axes.linewidth":0.8,"figure.dpi":150})

# Figure A: MC predictive distribution (rate + aggregate)
fig,axes=plt.subplots(1,2,figsize=(11,4.2))
SC=[("Ceasefire",CUM["C"],"#2E7D6B"),("Status quo",CUM["S"],"#C99A2E"),("Escalation",CUM["E"],ACCENT)]
ax=axes[0]
ax.hist(real_rate*100,bins=140,color=BLUE,alpha=.30,density=True,label="realized (predictive)")
lo,hi=pct(real_rate,5)*100,pct(real_rate,95)*100
ax.axvspan(lo,hi,color=BLUE,alpha=.08)
for nm,v,c in SC:
    ax.axvline(v*100,color=c,lw=1.3,ls="-")
    ax.annotate(nm,(v*100,ax.get_ylim()[1]*.96),fontsize=7,rotation=90,va="top",ha="right",color=c)
ax.axvline(det_rate*100,color=INK,lw=1.6,ls="--",label=f"deterministic mean {det_rate*100:.2f}%")
ax.axvline(pct(real_rate,50)*100,color=BLUE,lw=1.4,label=f"predictive median {pct(real_rate,50)*100:.2f}%")
ax.set_title("Cumulative price rise by Dec (%)",fontsize=11,weight="bold")
ax.set_xlabel("cumulative % since May"); ax.set_ylabel("density"); ax.set_xlim(-0.5,7.5)
ax.legend(fontsize=7.5,frameon=False,loc="upper right")
ax.annotate(f"90% CI  {lo:.1f}–{hi:.1f}%",(hi,ax.get_ylim()[1]*.55),fontsize=8,color=BLUE)

ax=axes[1]
ax.hist(real_agg,bins=140,color=GREEN,alpha=.32,density=True)
loA,hiA=pct(real_agg,5),pct(real_agg,95)
ax.axvspan(loA,hiA,color=GREEN,alpha=.10)
ax.axvline(det_agg,color=INK,lw=1.6,ls="--",label=f"deterministic mean ${det_agg:.0f}B")
ax.axvline(pct(real_agg,50),color=GREEN,lw=1.4,label=f"predictive median ${pct(real_agg,50):.0f}B")
for x,lab in [(res['deterministic']['env_lo'],"brief corner: all-ceasefire"),
              (res['deterministic']['env_hi'],"brief corner: all-escalation")]:
    ax.axvline(x,color="#8A8175",lw=1,ls=":")
    ax.annotate(lab,(x,ax.get_ylim()[1]*.9),fontsize=6.5,rotation=90,va="top",color="#8A8175")
ax.set_title("Added household cost, nationwide ($B / month)",fontsize=11,weight="bold")
ax.set_xlabel("$B per month (Dec run-rate)"); ax.set_ylabel("density"); ax.set_xlim(0,52)
ax.legend(fontsize=7.5,frameon=False,loc="upper right")
ax.annotate(f"90% CI  ${loA:.0f}–{hiA:.0f}B",(hiA,ax.get_ylim()[1]*.55),fontsize=8,color=GREEN)
fig.suptitle("Monte Carlo predictive distribution — spread is driven by which scenario realizes",
             fontsize=12,weight="bold",y=1.02)
fig.tight_layout(); fig.savefig("fig_mc.png",bbox_inches="tight",facecolor="white")
print("fig_mc.png saved")

# Figure B: incidence index bootstrap (forest + densities)
fig,axes=plt.subplots(1,2,figsize=(11,4.2))
ax=axes[0]
for vals,c,lab in [(Sv_pre,BLUE,"Suits (pre-tax)"),(Sv_aft,ACCENT,"Suits (after-tax)")]:
    ax.hist(vals,bins=100,color=c,alpha=.30,density=True,label=lab)
ax.axvspan(-0.35,-0.25,color="#C99A2E",alpha=.16); ax.annotate("gasoline-tax band",(-0.30,ax.get_ylim()[1]*.9),
    fontsize=7.5,ha="center",color="#8a6d1f")
ax.axvline(0,color=INK,lw=1,ls=":"); ax.annotate("proportional",(0.002,ax.get_ylim()[1]*.5),fontsize=7.5,color=INK)
ax.set_title("Bootstrap distribution — Suits index",fontsize=11,weight="bold")
ax.set_xlabel("Suits index (<0 regressive)"); ax.set_ylabel("density")
ax.legend(fontsize=8,frameon=False)

ax=axes[1]; y=0; ticks=[]; tlab=[]
rows=[("Suits pre-tax",boot_res["pre"]["suits"],BLUE),
      ("Kakwani pre-tax",boot_res["pre"]["kakwani"],BLUE),
      ("Suits after-tax",boot_res["after"]["suits"],ACCENT),
      ("Kakwani after-tax",boot_res["after"]["kakwani"],ACCENT)]
for name,d,c in rows:
    ax.plot([d["p05"],d["p95"]],[y,y],color=c,lw=2.4)
    ax.plot(d["point"],y,"o",color=c,ms=7)
    ax.annotate(f'{d["point"]:.2f}  [{d["p05"]:.2f}, {d["p95"]:.2f}]',(d["p95"],y),
                xytext=(6,0),textcoords="offset points",va="center",fontsize=8)
    ticks.append(y); tlab.append(name); y-=1
ax.axvspan(-0.35,-0.25,color="#C99A2E",alpha=.16)
ax.axvline(0,color=INK,lw=1,ls=":")
ax.set_yticks(ticks); ax.set_yticklabels(tlab,fontsize=9); ax.set_ylim(-3.6,0.6)
ax.set_xlim(-0.42,0.06); ax.set_xlabel("index value (90% bootstrap CI)")
ax.set_title("Incidence indices with 90% CIs",fontsize=11,weight="bold")
fig.suptitle("Incidence is robustly regressive — parametric bootstrap over modeled inputs",
             fontsize=12,weight="bold",y=1.02)
fig.tight_layout(); fig.savefig("fig_incidence.png",bbox_inches="tight",facecolor="white")
print("fig_incidence.png saved")
