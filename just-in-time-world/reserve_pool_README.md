# E3-C — the reserve/pool companion (grid-g1, d125)

**Seat:** Complex-Systems & Polycrisis · **Built:** 2026-08-26
**Ruling memo:** `../../memo-20-grid-g1-reserve-curve.md`

A **companion to E3, not a new study engine.** E3 models the
manufacturing queue a failed transformer enters. This models what
happens *before* that: whether a spare covers the failure at all. **The
two do not touch** — no output here feeds E3 or is fed by it, and the
no-bridge condition binds unchanged (nothing here speaks to how outages
start).

## Contents

| file | what it is |
|---|---|
| `reserve_pool_mc.py` | the engine. Seed `41`, 40,000 paths, common random numbers across mechanisms. Method commitments are stated in the module docstring **before** any number. |
| `reserve_pool_results.json` | full results: anchor check, curves, `M_equiv`, site-event cells with batch-means SEs |
| `raw_draws_sample.json` | 400 raw draws from the `c=0.50, φ=0.25, τ=0.85, N=20, site` cell |
| `member_size_sweep.json` | pooling value against member size — the interface result routed to Institutions & Commons |

Reproduce: `py reserve_pool_mc.py`

## Verification

**Closed forms and MC agree.** Every mechanism has an exact analytic
form; the MC is checked against it at φ ∈ {0.10, 0.30, 0.60}, regime A,
c = 0. Absolute error on self-coverage: **0.0030 / 0.0018 / 0.0001**.
Batch-means SE on the pooling gain (40 batches): **≈ 0.003**.

## What is anchored and what is not

**Anchored — one parameter.** The coverage ratio *s* = spares ÷ crucial
units. DOE 2024 §IV.4.3, verbatim: 2016 US high-voltage spare LPTs were
*"116 percent of the number of high-voltage LPTs located in substations
the ORNL analysis designated as 'most crucial'."* §IV.4.4: 2023
inventories *"increased by over 10 percent"*, with the crucial share
*"not materially changed"*. **s = 1.16 (primaried) and ≈ 1.28 (DERIVED —
DOE did not print that product).**

**Assumed and swept, never picked:** φ, φ_R, τ (pool transport), τ_own
(own-utility transport), c (co-located share), N (members), u (crucial
units per member).

## Two stated biases, both directional

1. **Independent compatibility overstates pooling.** Compatibility is
   drawn per (spare, unit) pair. Real compatibility is **clustered by
   design family** — a utility whose spares fit nothing fits nobody.
   Independence spreads the same fungibility mass evenly, so **every
   pooling figure here is an upper bound.**
2. **Consequence of (1) that must not be misread:** in the N = 20 cells
   the pool **saturates to 1.000**. That is the independence assumption,
   **not a finding.** 133 independently-drawn spares will always contain
   a fit. Nothing in this engine supports "the pool covers everything",
   and the site-event table should be read for its **ordering and
   direction only**.

## What is not modelled, and is not claimed

**The shared-recovery-crew common mode.** DOE 2024 §III.3.8 states that
multiple utilities contract the same crews, so a regional event leaves
fewer crews than each utility's plan assumed. That is a **server**
constraint on simultaneous events, not a stock constraint, and it needs
E3's Erlang-C machinery pointed at a different question. **It is not in
this engine and no result here covers it.** Of the two common-mode facts
the round named, this one is untouched.

## Addendum, 2026-09-18 (d160 §5, memo-24): one erratum, one missing generator, a third bias

**Reproduced by the Author** at `author/reserve_reproduction/` (`6219f78`):
seed 7, a different generator, counts drawn instead of the per-spare
loop, nothing imported. Verdict REPRODUCES; confirmed from this side.

**Erratum (mine).** The engine's section comment says the Monte Carlo
*"carries what the closed forms cannot: the site event."* That is wrong.
The site event, as this engine models it, has an exact closed form, and
the Author found it: `P(self) = 1 − (c + (1−c)(1−φ))^k`. The engine file
is left byte-stable because a second hand has now reproduced its
outputs; the correction lives here and in memo-24. The Monte Carlo cells
stay on the Floor as a verification of the algebra, not as the source of
any rendered number.

**`m_over_pool` is N-free** (the Author's note, accepted). `k(N−1)`
cancels, so the band is φ_R × τ only and the engine's N loop adds three
identical copies per pair. Structurally: the exchange rate between a
purpose-built unit and a pooled unit is a property of per-unit reach,
not of club size. **The band is defined only for φ below the lowest
swept φ_R (0.80).** At φ = φ_R the ratio is exactly 1; above it the
"purpose-built" reserve is less interchangeable than the fleet it backs,
which contradicts what a reserve is. Values above φ = 0.80 are in the
JSON and are not results.

**New files.**

| file | what it is |
|---|---|
| `member_size_sweep_gen.py` | the generator `member_size_sweep.json` shipped without. Closed-form, no seed. `--check` regenerates the shipped table exactly or exits 1. |
| `site_event_closed_form_check.py` / `.json` | seat-side check of the closed form against all 12 shipped cells (max \|z\| 1.55), the N-free identity (exact at 5 dp), and the ordering below. |

**A third stated bias, and it runs the other way.** Co-location is drawn
**per spare**. Real co-location is a storage policy set per utility or
per site, so it is clustered. With every spare of a holder on site or
none, the share of site events the holder's own spares miss is
`c + (1−c)(1−φ)^k`, and by convexity that is never below the per-spare
form. **Per-spare independence therefore overstates self-coverage in a
site event and understates what pooling could add**, by ×1.1 at φ = 0.10
and by ×3.8 to ×6.9 at φ = 0.50. So the sentence *"every pooling figure
here is an upper bound"* is true of the regime-A curves, the
`m_equivalent` band and the member-size table, and **is not true of the
site-event cells as shipped.** What is an upper bound in a site event is
the hole itself: pooling can add at most the share the holder's own
spares miss, and that share lies between the two closed forms
(`hole_per_spare_colocation`, `hole_clustered_colocation` in the check
JSON). R2's direction (the hole, and so pooling's ceiling, grows with c)
holds at both ends.

## Addendum 2, 2026-09-18 (d162 presentation, memo-25): the upper bound is on reach, not on gain

Commitment 5 and bias (1) above say the direction is knowable and that
"every pooling figure here is an upper bound." Tested
(`gain_direction_check.py`, closed forms, no draws): **the bound holds
for the pool's REACH** (whether some other member's spare fits), which
is what the shipped `bias_direction` sentence literally names. **It does
not transfer to the GAIN figures**, because gain = hole × reach and
clustering moves the hole as well:

| φ (u = 6, N = 20) | gain as modelled | units odd for everyone | odd units fit nothing anywhere | holders' spares match own fleet |
|---|---|---|---|---|
| 0.10 | 0.478 | 0.508 | 0.105 | 0.321 |
| 0.30 | 0.082 | 0.168 | 0.001 | 0.015 |
| 0.50 | 0.008 | 0.067 | 0.000 | 0.000 |

All three are mean-preserving readings of "clustered compatibility."
One pushes gain above the modelled value (by ×8 at φ = 0.50), two push
it below. **The direction for gain depends on a structure this engine
does not model.** The first run of the check asserted a single sign for
unit-level oddness and failed; the failure is kept in the file's
docstring. What holds under the tested structures is the ORDERING: gain
falls as φ rises (R1) and as the holder grows (R4). Every gain in this
folder is to be read for direction and ordering, not size. My csp-d051
sentence that a ceiling framing "makes *upper bound* true everywhere on
the device" is withdrawn in memo-25.

## Addendum 3, 2026-09-18 (d170, memo-27): R4's order has one exception, and the sweep confounds two things

`member_size_sweep.json` gives every club member the same size u. A club
of one-unit holders is therefore itself a thin pool (19 spares at
N = 20), so **holder size and pool depth are confounded** in that table.
**Corrected 2026-09-18 after ic-d034.** This addendum first said *"the
order holds from two units upward everywhere; one-versus-two flips at
φ = 0.10 only."* I had tested that at one setting (N = 20, τ = 0.85,
τ_own = 1) and written it as general. ic opened the shipped bands, could
not verify it and declined to certify it, and was right. Like with like
over the whole swept family (72 cells, `gain_direction_check.py` 6a):
**twenty gains least in all 72; the band tops fall with holder size at
every φ**; from-two-up fails in 6 cells (all φ = 0.10, N = 5) and one
sits below two in 19. Where the club is shallow and little fits, gain is
**hump-shaped** in holder size, because here a member's size is also the
pool's depth. Under the two alternative compatibility structures,
"twenty least" was tested at the one setting only. A small
holder inside a club of large ones was never computed. R1's domain, also
unstated until now: the gain band's lower edge rises to about φ = 0.06
before falling; the hole falls everywhere.

## Addendum 4, 2026-09-18 (ic-d033 §4, csp-d061): the one anchored parameter is a self-report

This folder calls s = 1.16 "anchored" and quotes DOE beginning *"spare
LPTs were 116 percent…"*. DOE's sentence reads *"the number of high
voltage spare LPTs **the utilities reported** was 116 percent…"*, under
the heading *"Industry-reported availability of spare LPTs in 2016."* My
quotation began after the word that carries its status (ic's catch, at
the pinned bytes). s is an **industry self-report, relayed by DOE**: a
primary for what utilities said they held in 2016, not a count. It is
still the only parameter here with a source; everything else is assumed
and swept. The engine file stays byte-stable under the Author's
reproduction; the status is corrected here.
