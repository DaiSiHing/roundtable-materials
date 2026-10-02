# E3 MC specification — the transformer queue (RE-WEIGHING ROUND, d042)

**Engine:** `e3_transformer_queue_mc.py` · **Seed:** 33 · **N:** 25,000
per run · **Class run:** LPT (≥100 MVA); K=2 size-classes built,
distribution class queued (d020). **Horizon:** reporting 2025–2055
monthly; simulation 2019-01–2055-12; age anchor 2014. **Design of
record:** memo-03 (`605e52e`) + d020 + iron-register `e3_design`
(joint_refit + referee_m003 blocks). **Parameters:**
`e3_energy_params.json` + `delta_d022` + `delta_d026` + `delta_d032`,
all **loaded and asserted at startup** (F3); drift aborts the run.

**Running it (added 2026-09-29).** The engine reads seven input files,
all from the energy seat:
- `e3_energy_params.json`
- `e3_energy_params_delta_d022.json`
- `e3_energy_params_delta_d026.json`
- `e3_energy_params_delta_d032.json`
- `e3_energy_params_delta_esr040.json`
- `e3_energy_params_delta_d045.json`
- `eb_d039_sigma_fit_results.json`

It looks for each one **beside itself first**, then in the energy seat's
folder of the study's working tree. So a published folder that ships the
seven flat next to the engine runs as downloaded:

    python e3_transformer_queue_mc.py

This needs only numpy. It writes `e3_results.json`, `e3_raw.npz` and
`e3_sample.csv` beside itself. The inputs are guards, not sources of
numbers: every value the engine uses is a constant in the engine, and the
files are checked against those constants at start. Run from a flat
folder, it reproduces `e3_raw.npz` and `e3_sample.csv` byte for byte, and
`e3_results.json` byte for byte except `runtime_s`, which is wall-clock
time.

`eb_d039_sigma_fit_results.json` is written by `eb_d039_sigma_fit.py`,
the energy seat's fit, an engine in its own right. It ships in the same
folder with its two small inputs. Its four large public inputs are
fetched by the reader, and how to run it is in the folder's README and
the paper's Appendix B. **This engine does not need the fit to be run.**
It reads only the fit's results file, and only to check, at start, that
its own 2024 sigma band contains the fit's 2024 arrival central value,
and that the band's top is at or above the top of the fit's 2022–24
delivered envelope. No number this engine produces comes from the fit.
*(Paragraph corrected 2026-10-01. The first version said the fit's script
did not travel with this engine; the fit then graduated as its own engine
and shipped in the same folder, so that sentence became false.)*

## History and supply (this round)

- **Imports 2019–24: the realized slice path, consumed directly**
  (SOURCED, class-validated 617=617): 617/729/539/771/1,372/1,806.
  **The 2021 U(0.75,0.95) sensitivity member is RETIRED into the
  data** (this seat's call, offered by d026): the 539 dip is realized
  history; keeping the member would double-count it.
- **Imports 2025+: the fitted response term** (energy, primaries-only):
  dead time U(12,30) mo (central 18), ramp U(0.30,0.55)/yr (central
  0.45), ceiling U(2.5,3.5)× the 617 pre-boom baseline [ASSUMED,
  exposed knob], symmetric-with-lag relaxation [ASSUMED]. The response
  state (backlog-signal ages) is carried through history, so the 2025
  posture is emergent.
- **Domestic path:** unchanged (137 → utilization ramp under pressure,
  skill-capped, nameplate 343 frozen in MC runs). Now the
  **un-primaried half of supply** — xfmr-f14 names the upgrade
  (EIA-860M / Commerce survey / filings); a domestic-path revision
  moves the map below.

## The two-class queue (emergent-matched as of d034)

Priority (direct-purchase, queue-jumping) and standard (utility)
classes; priority is served first; per-class exact FIFO waits from
per-class cumulative curves. **The priority stream is EMERGENT-MATCHED
(d032/d034):** λ_p = λ_s·s/(1−s) including the intake-multiplied
standard rate, so a member's labels are its emergent arrival shares by
construction; the share path runs 0 (pre-2020-07) → s21 (mid-2021) →
s24 (end-2024), linear, then holds [ASSUMED]. Intake per d026: the
U(1.1,1.4) multiplier is the **standard class's** 2022–24 history; the
priority stream is the excess carrying total intake toward the
DOE-implied 1.7–2.9× (the MEMORIAL member (0.30,0.45): intake
multiple p50 2.39, emergent share over the window p50 0.389; band
members sit at 1.52–1.85). The reported
emergent share verifies the construction and averages the ramp, so it
reads below s24.

**Quote metrics (G2, formulas stated):** standard quote =
(Q_p+Q_s)/(C − λ_p) + B_med (a standard order sits behind both
backlogs at the residual rate after ongoing priority arrivals; clipped
at 600 mo where λ_p ≥ C); priority quote = Q_p/C + B_med. Realized
waits are exact per-class FIFO (order→energization incl. build draw)
and are the primary wait objects; quotes are the DOE-comparable
approximation. **(m004 H5):** the standard quote is clipped at 600
months where λ_p ≥ C (a reporting bound on a divergent expression,
never binding in any run at N=25k); and the corridor share is
implementation-sensitive at the corridor edge — the Author's
reimplementation read 0.348 vs this build's 0.392, a spread large
against same-construction MC noise but expected for tail mass under
different constructions, **acceptable only because the quantity is
diagnostic** — it would not be acceptable on a rendered number. The
convergence the verification rests on is the percentile map, which
agreed cross-implementation to 0.01–0.03 months.

## σ discipline — CLOSED FOR RENDER PURPOSES (d042/m010 supersede d032/d034)

**σ is closed for this study's render purposes** (m010): the vendor
derivation is **killed for levels** (reconciliation failure, third leg
confirmed); the purchase was **declined 2026-08-20** (the 6-item spec
and its symmetric acceptance stay frozen on file; Newton-Evans the
sole cheaper-candidate, item-4 pre-sale mandatory); **xfmr-f12
resolves by FIT at corroboration tier** — σ_arrival [0.05, 0.21]
central 0.09, three instruments on one side of ≥0.53. The gate stands
permanently unless a referee-routed v3 or a spec-satisfying purchase
reopens it.

**The two-class mechanism is DEMOTED to minor contributor:** the
posture test failed (Leg-A delivered share 0.053–0.105 vs the
engine-derived prediction [0.27, 0.51]) and at the approved band σ
buys ~1–3 months of standard quote — arithmetically forced, and
measured on this round's map (≤0.5 mo at the Dec-24 quote median;
~1–3 mo on cohort waits at the band's top).

Members are **(s21, s24) EMERGENT ramp pairs on the m010-APPROVED
band's diagonal** — σ_e(2021) ∈ [0.03, 0.15] → σ_e(2024) ∈
[0.05, 0.25]: {(0.03,0.05), (0.06,0.10), (0.09,0.15), (0.12,0.20),
(0.15,0.25)} — **plus one MEMORIAL MEMBER at the superseded
vendor-implied (0.30, 0.45)** (m010 Attachment 3, never-silently-pick:
the fit [0.05,0.21] and the corrected-Mordor unit-basis 0.33–0.42
cannot both describe the same object; the conflict is real, named,
and unresolved by choice — the grid SPANS it instead of silently
adjudicating it). The band carries m010's provenance string verbatim
(results: `sigma_band_provenance`): *"fit-derived at corroboration
tier from a method killed for levels (reconciliation failure, Leg-C
boundary); never renders; never upgrades without new evidence through
the referee"* — with the headroom caveat (fab/rail/mining/hydrogen
priority purchases are invisible to the EIA-860+LBNL lens; 0.25 vs
the fit's 0.21 is that softness made explicit). Consumed
emergent-matched (λ_p = λ_s·s/(1−s)); share path unchanged;
ASSUMED-tier, **variant grids only**, common random numbers. The
loader asserts band-vs-fit consistency (the 2024 box contains the
arrival central; the top is the ruled headroom over the window
envelope) and pins d032's boxes as historical.

**Floor cohort LEVELS stay gated** (the gate string carries the full
m010 posture). **Bias-direction render condition (econ m005, BINDING —
strengthened by the demotion):** the residual is supply/quote-side —
any cohort wait that ever renders is a **FLOOR** and carries "at least
this long" language.

**The residual's candidates (memo-26, 2026-09-18, superseding the
d042 order of memo-08 §3): three, UNRANKED** — **quote formation**
(protective quoting is rational under a 7.5-year interconnection
stock; no quotes-vs-realized primary exists; ceiling unbounded);
**f14 domestic path** (un-primaried half of supply; moves the whole
map; carries the FLOOR bias direction); **f13 backlog state**
(adjudicator if a real backlog primary lands). **Last, and measured:
two-class σ** (minor, ~1–3 mo, three-instrument corroboration at low
levels). Quote formation was ranked first at d042 on two grounds; the
sold-out-horizon quotes are withdrawn (esr-d040/m043) and the
surviving ground presses on quote formation and backlog state alike.
**Interconnection-stock fact beside every calibration block:** 384.5
GW of active capacity with signed/draft IAs vs 51.2 GW of 2024
installs = **7.5 years of installs** (Queued Up tab 17, pinned).
These are interconnection agreements, not transformer purchase
orders. **Acceptance rules pre-stated (memo-06 §2, written before the
runs):** R1 the map reports all members, none selected by outcome;
R2 classification thresholds fixed in advance — "reaches" if
standard-class Dec-24 quote p50 ∈ [30.6, 66.0] (0.85×36 to 1.1×60),
"under"/"over" otherwise; G3 (quote formation) means "under" members
are noted, never excluded; R3 no assumed-σ cohort level renders
(xfmr-f12 is the gate — G1 machine flags on every floor block);
R4 nothing in the build consumed 36/60/corridor as an input
(DO_NOT_INPUT asserted; the corridor is algebraically the target in
backlog units and is never counted as independent — m003).

**Process rule going forward (m004 H2):** R2's numeric thresholds were
attestation-only this round and are FROZEN by the referee's blessing;
any future numeric acceptance rule commits to the repo *before* the
run commit, as d029 did for the structure.

**σ ill-conditioning (m004 H4, render-binding):** near the DOE band
the map moves ≈4 months per 0.01 of σ (the band sat at σ 0.53–0.60
central in σ-space — now REJECTED territory per eb memo-06). Any
xfmr-f12-driven render consumes σ as a **band matched on the emergent
share**, never a point; this round's members are emergent-matched by
construction, retiring the old nominal-vs-emergent wedge.

## Result of the out-of-sample check (seed 33, N=25k; m010 band + memorial)

**All six members classify "under"** (R2 thresholds frozen per H2):
standard-class Dec-24 quote p50 = 9.0 / 9.0 / 9.0 / 9.1 / 9.5 across
the approved band's diagonal, and **20.7 at the memorial member** —
the map now *shows* the demotion (band members sit ≤0.5 mo above the
one-class reference at the Dec-24 quote median; ~1–3 mo on cohort
waits at the band's top) and *spans* the unresolved Mordor conflict
(the memorial's 11-month distance from the band top is the conflict's
size in quote-months). Prior maps are superseded and preserved in git
history (`8b86c28` nominal grid; `dcf66f4` d032 boxes).
Monotone in s24 and strong: the two-class mechanism moves the queue
onto the standard class exactly as hypothesized (priority 2027
realized wait p50 8.9 mo ≈ build time at every member; standard 13.5
mo at the top member — who waits when someone pays to jump).
**Ceiling-convergence render wording (m004 H3): "both structures cap
standard-facing quotes at ≈24–25 months."** The sub-month agreement
(24.2 vs m003's 24.6) is two ≈5-month effects offsetting — m004's
decomposition: one-class at intake 2.9× reads 24.65 in this engine,
and the two-class 24.4 = 19.6 at multiple 2.52 + a 4.8-month
residual-rate wedge. Render the decomposition, not the coincidence.
**Provenance, stated 2026-09-18 (d171, csp-d063):** the ceiling's basis
is the ONE-CLASS intake probe (m003; 24.65 on this engine), now
reproducible from this folder as `e3_ceiling_probe.py`. The two-class
24.2 / 24.41 is the NOMINAL σ = 0.50 member of the d029 grid (commit
`8b86c28`), a grid superseded at d042; it is in no shipped results file.
In the shipped file the approved band's top member reads 9.5 and the
memorial member 20.7. The two-class cap is conditional on the priority
share's bound, not on intake alone (m004: 0.53 → 30.3, 0.55 → 35.7).
The quote bound tracks the total intake multiple; σ redistributes who
bears it. The intake multiple's denominator is fixed (3 × 754, the
2019 anchor — m004 H1) and stated in results. Backlog Dec-24 at the
top member: p50 1,241, corridor share 0.306 (diagnostic only).
**The residual is adjudicated as a finding** (see σ-discipline above);
its decomposition across xfmr-f14 / xfmr-f13 / quote formation is the
open work. **Horizons corroboration: WITHDRAWN (esr-d040/m043,
memo-26).** The "some lines quoting 2031" and "Hitachi through 2029"
clauses were never sourced and are struck; the one pinned statement is
an officer's forward expectation pooled over three product lines and
bounds the transformer line neither above nor below; Mordor's 210
weeks is a market-research teaser. Nothing here corroborates a quote
level, and no parameter ever read these. The $-to-units conversion
remains INADMISSIBLE as a level (price-vintage wedge: +14% realized
vs +80% quoted).

## Verification hooks

Exact anchors unchanged and PASS (M/D/1 P–K 40.50/40.98; M/M/c
Erlang-C 7.89/8.02; batch-means SE). F3 assert PASS across all three
parameter files. Author re-reproduction (d029 item 5) runs against
this build: the reimplementation needs the realized-import path, the
response term, and the two-class allocation (priority-first starts);
the σ map's five members reproduce under CRN from seed 33; raw npz
carries the one-class reference and the σ=0.30 member per-path
outputs. Convergence: ratified at 25k (m002), unchanged machinery.

## Phase diagram (RENDER-GATED: LTRA)

Semantics unchanged (one-class, central skeleton, expandable nameplate
= capacity-growth capability, optimistic bound). **New this round: the
import-response term is active in the skeleton** — the boundary
reflects import elasticity as well as domestic ramp. Corner-margin
caveat carries forward render-binding (m002/m003).

## G-fixes ledger (d029 item 3)

G1 — every floor block carries `render_gated: true` with the xfmr-f12
gate string (machine flag = posture). G2 — both metrics, exact shares,
per class, formulas above. G3 — quote formation is ranked 4th in
memo-06's resolution list. G4 — every impossibility/probe sentence in
results and spec reads "central-skeleton; MC share ≥36 = 0 within
ratified bands."

## Files

Engine · `e3_results.json` (map + members + reference + coupled +
phase, gates inline) · `e3_raw.npz` · `e3_sample.csv` (first 200
paths) · this spec. Run: full | `--smoke` | `--anchor`. numpy only;
all three energy JSONs required (F3).
