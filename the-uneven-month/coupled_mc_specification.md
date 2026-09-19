# Coupled-Tail Monte Carlo — Specification, Results, and Reproduction

*Response to the calibration-base point. The historical-vol run is retained but relabeled the **floor** on uncertainty; a tunable coupling layer is added on top, and two bands are reported so the gap between them is the quantified "novel territory" rather than a single false-precision interval. The regressivity thesis is untouched (and shown robust to the new coupling — §6).*

This sheet answers, in order, exactly what you asked for: what is drawn, the within-scenario variance and its calibration window, the correlation/copula structure and distribution family, the draw count and seed, and where the raw outputs and code live.

---

## 1. Framing

You are right that a Monte Carlo calibrated on historical monthly-inflation variance prices the future as a draw from the past, and that this **understates** a correlated, cascading tail — a Gulf oil shock co-moving with shipping, food/fertilizer, goods passthrough, and the liquidity channel. We treat the historical run as a **lower bound** and add an explicit, tunable coupling layer. Because the coupling strength is partly deep/Knightian, the goal is not to pin it down but to make it a **visible assumption with reported robustness** — in the spirit of forward scenarios over stale history (NGFS), tail-dependent (copula) rather than linear dependence, and decision-under-deep-uncertainty framings (RDM, polycrisis). The deliverable is the **two bands and the gap between them.**

---

## 2. What is drawn (per Monte Carlo draw)

| Quantity | Floor | Coupled | Notes |
|---|---|---|---|
| Scenario weights | Dirichlet(κ·w₀), κ=20 | same | w₀=(0.30, 0.45, 0.25); **drawn**, not fixed. Shown negligible in the earlier run; retained for completeness. |
| Realized scenario s | Categorical(weights) | same | which of ceasefire / status-quo / escalation actually occurs |
| Central path μₛ | from workbook | same | the 7 monthly MoM values for the drawn scenario |
| Persistent level shock δ | N(0, σ_level) | N(0, σ_level·m) in crisis | one common shift applied to all 7 months (compounds) |
| Monthly innovations ε | **independent Gaussian** | **copula-coupled, fat-tailed** | the coupling layer lives here (§4) |
| Crisis regime c | — (off) | Bernoulli(p_crisis) | a deep-uncertainty regime that fattens variance and broadens the basket |
| Basket broadening BFADD | 0 (consensus) | 0 normal / bfadd_crisis in crisis | **state-dependent**, the in-model "oil is the economy" hook (§5) |

Realized monthly rate: `MoMₘ = μₛ,ₘ + δ + εₘ`. Cumulative: `rate = Π(1+MoMₘ) − 1`. Aggregate burden: `agg = rate × K(BFADD)`, with `K(a) = K₀ + a·K_slope`, `K₀ = 847.45`, `K_slope = 858.57` ($B per month per unit rate). So in a crisis draw, the burden is amplified through **two non-separable channels**: a higher/fatter realized rate *and* a broader basket (higher K).

---

## 3. Within-scenario variance and calibration window

- σ_level = 0.0008 (0.08 pp/month persistent), σ_month = 0.0015 (0.15 pp/month transitory).
- **Calibration window:** approximate dispersion of monthly headline CPI MoM over roughly 2021–2026 (the report's own realized anchors were +0.9% and +0.6% MoM). This is an **order-of-magnitude calibration, not a fitted GARCH** — I could not pull the CPI series here to estimate volatility formally. Because it is historical, it is deliberately the floor; the coupling layer is what represents the un-historical tail.

In the **coupled** run, both σ's are multiplied by `crisis_mult` when the draw is in the crisis regime.

---

## 4. Correlation / copula structure and distribution family

**Floor:** monthly innovations are **independent Gaussian** (no copula coupling beyond the common level shock δ).

**Coupled (default):** **Student-t copula** across the 7 months — equicorrelation ρ = 0.35, copula dof ν_cop = 4 — composed with **fat-tailed Student-t marginals** (ν_marg = 5, standardized to unit variance then scaled by the regime σ). The t-copula's symmetric tail-dependence coefficient at these settings is **λ = 0.181**.

**Coupled (variant):** **rotated (survival) Clayton copula**, θ = 2, giving **upper-tail** dependence λ_U = 2^(−1/θ) = **0.707** — asymmetric, so months cluster specifically in the *high-inflation* (bad) tail. This is the more faithful representation of a directional cascade and is reported as the upper bound.

The crisis regime (a discrete Bernoulli mixture) is itself a strong tail-coupling mechanism — in a crisis, all months fatten simultaneously — which is why (see §7) the continuous copula dof turns out second-order once the regime is present.

---

## 5. The in-model "oil is the economy" hook

Per your item 3, the energy-realist basket-broadening is **state-dependent**, not a fixed switch: BFADD = 0 in normal draws, BFADD = bfadd_crisis (default 0.18, above the static realist 0.12) in crisis draws. Operationally this raises K from $847B to ≈ $1,002B per unit rate in a crisis, so a tail draw is hit on both the rate and the breadth — expressing the non-separability of the channels inside the framework rather than as an external multiplier.

---

## 6. Results — two bands, and the gap

Draw count **N = 200,000**, seed **20260605**.

### Aggregate added cost ($B / month, December run-rate)

| Run | mean | median | 90% CI | p99 | sd |
|---|---:|---:|---:|---:|---:|
| **Floor** (historical) | 24.7 | 23.3 | **[3.7, 49.3]** | 54.8 | 14.2 |
| **Coupled — t-copula** | 25.4 | 23.8 | **[0.4, 53.5]** | **71.5** | 17.6 |
| Coupled — rotated-Clayton (upper bound) | 25.4 | 23.5 | [−1.2, 55.9] | **78.8** | 19.0 |

### Cumulative rate (%)

| Run | median | 90% CI | p99 |
|---|---:|---:|---:|
| Floor | 2.75 | [0.44, 5.81] | 6.47 |
| Coupled — t | 2.76 | [0.05, 6.12] | 7.45 |
| Coupled — Clayton | 2.73 | [−0.14, 6.38] | 8.23 |

**The center is preserved** (median ≈ $23–24B in every run); coupling does not move the central estimate, it **reweights the upper tail**. The "novel territory" is therefore best read off the tail, not the median:

- **Upper-tail gap (coupled-t − floor):** p95 **+$4.3B**, **p99 +$16.7B**.
- **P(burden > $44B/mo)** (the brief's old upper corner): floor 12.5% → coupled **15.2%**.
- **P(burden > $60B/mo):** floor 0.1% → coupled **2.4%** (≈ 24× more likely once coupling is admitted).

The gap between the floor and the coupled p99 — roughly **$17–24B/month** depending on copula family — is the quantification of how much the historical calibration was understating the cascade tail. That gap, not a single percentile, is the answer.

### Knob sensitivity (coupled-t, aggregate p95 / p99)

| Knob | values → p99 |
|---|---|
| p_crisis | 0.05 → 61.9 · 0.15 → 71.3 · 0.30 → 80.7 |
| crisis_mult | 1.5 → 63.6 · 2.5 → 71.4 · 4.0 → 87.6 |
| bfadd_crisis | 0.12 → 68.8 · 0.18 → 72.4 · 0.25 → 76.6 |
| ν_cop (tail-dep) | 200(≈Gaussian) → 71.4 · 6 → 70.6 · 4 → 71.7 · 2.5 → 71.8 |

**Reading:** the tail is governed by *how likely and how severe the crisis regime is* (p_crisis, crisis_mult) and *how far the basket broadens* (bfadd_crisis). The copula tail-dependence parameter ν_cop is **second-order** — because the discrete regime-switch already supplies most of the joint-tail co-movement. This is itself a finding: with a regime mixture present, the headline result is robust to the exact copula dof, and the honest levers to argue over are the regime probability/severity and the breadth.

---

## 7. The thesis is untouched (and robust to broadening)

You noted the regressivity is scenario-invariant, so none of this should touch it. Confirmed, with one nuance worth stating. The rate cancels from the burden *shares*, so the indices are invariant to the rate distribution entirely. The only new channel that *could* touch them is the state-dependent BFADD, because it enters the basket factor. Checking the pre-tax Suits index as BFADD grows:

| BFADD | 0.00 | 0.12 | 0.18 | 0.30 | 0.50 |
|---|---:|---:|---:|---:|---:|
| Suits (pre-tax) | −0.260 | −0.250 | −0.246 | −0.239 | −0.229 |

The sign and rough magnitude are preserved across the entire plausible broadening range; a uniform additive broadening *attenuates* regressivity only slightly (it dilutes the basket-factor gradient). So the coupling layer widens the magnitude error bars — correctly — without disturbing the incidence conclusion.

---

## 8. Honest caveats

- The coupled lower tail drifts toward $0 (and slightly below for the symmetric t-copula / Clayton fat marginals). Values ≤ 0 are the benign-disinflation case — *no* added burden — not a negative cost; the analysis focuses on the upper (cascade) tail, where the rotated-Clayton is the directionally faithful choice and the t-copula a symmetric conservative default.
- The floor σ's are an order-of-magnitude historical calibration, not a fitted volatility model (no CPI series access here). The coupling parameters are deliberately assumptions, not estimates — the point is the reported range, not a fitted coupling.
- This remains a magnitude exercise on a partial-equilibrium model; it prices neither behavioral substitution nor the policy (Fed) response.

---

## 9. Reproduction

All artifacts use seed 20260605, N = 200,000.

- **`coupled_tail_mc.py`** — the full engine (numpy/scipy/matplotlib). All four knobs plus copula family are function arguments; run it to regenerate every number here and the figure.
- **`coupled_mc_results.json`** — every reported statistic (both bands, Clayton variant, novel-territory metrics, full knob sensitivity, the BFADD thesis check, tail-dependence coefficients).
- **`coupled_mc_raw.npz`** — the raw draw vectors (floor/coupled-t/coupled-Clayton, rate and aggregate, 200k each) so you can recompute any percentile yourself rather than trust mine: `np.load('coupled_mc_raw.npz')['coupled_t_agg']`.
- **`coupled_mc_sample.csv`** — a 20,000-row sample (floor_rate, floor_agg, coupled_t_rate, coupled_t_agg) for quick eyeballing in any tool.
- **`fig_coupled.png`** — floor vs coupled densities with the p95 gap annotated.

I left the live workbook's deterministic engine unchanged; this probabilistic layer sits alongside it. If you're satisfied with the structure, the next step is to splice the two-band result into Section 3 of the research paper (replacing the single-band MC), which I can do on your word. Happy to take a call if it's faster to tune the knobs together.
