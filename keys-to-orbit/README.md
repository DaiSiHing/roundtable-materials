# The Keys to Orbit - Who Controls Low-Earth Orbit, and How Close Is the Cascade?

Who controls low-Earth orbit - by law, or by physics? One company now operates roughly two of every three active satellites, and if every satellite stopped dodging, the expected time to a possible collision is measured in days. A structural occupancy study with two honest bands, not one scare number. Not a forecast.

Read the study: https://thethirdattractor.org/studies/keys-to-orbit/

This folder is a byte-identical mirror of the study's public reproducibility set
("the Floor"), served at https://thethirdattractor.org/studies/keys-to-orbit/materials/. The descriptions
below are the ones published in the Floor section at the bottom of the study page.
`MANIFEST.sha256` lists a SHA-256 for every file here.

| File | What it is | Size | License |
|---|---|---|---|
| `d15_e6_trust_sizing.py` | E6 trust sizing. The Referee seat’s independent pricing of the fleet-level disposal-trust principal as a distribution: $759M median, band [$131M, $4.42B] - terminal disposal only, a floor and the smallest of four cost lines. Fresh seed 20260720. | 8.3 kB | MIT |
| `d15_e6_trust_sizing_raw_sample.csv` | Trust-sizing raw draw sample. | 14.4 kB | CC BY 4.0 |
| `d15_e6_trust_sizing_results.json` | Trust-sizing recorded statistics. | 6.3 kB | CC BY 4.0 |
| `d15d_staged_resize.py` | the staged wind-down re-sizing. Re-sizes the trust principal and bridge-opex exposure against the staged 15-year wind-down; the principal is taper-invariant - the load-bearing result. | 5.9 kB | MIT |
| `d15d_staged_resize_results.json` | Staged re-sizing recorded statistics. | 4.3 kB | CC BY 4.0 |
| `fig_guardianship.png` | Fig. 4 - the guardianship fork. The three-state service fork with the 30× gap. MODELED; conditioning printed inside the figure. | 216.8 kB | CC BY 4.0 |
| `fig_racemap.png` | Fig. 3 - the payoff-space map. Two-panel: structure plot at median knobs + thin-middle CDF over the whole sweep. MODELED; conditioning printed inside the figure. | 219.8 kB | CC BY 4.0 |
| `kessler_model.xlsx` | The live workbook. Formula-driven system of record - 35 formulas, 0 errors; MEASURED/SOURCED vs MODELED tags on inputs; imported simulation results static and anchored to the live cells. | 21.0 kB | CC BY 4.0 |
| `kessler_qb_engine.py` | the stock-flow cascade engine (v1.2). Six altitude bands, four coupled stocks per band; collision-production and drag-removal loops. Seed 20260716. Produced the criticality and trajectory results (ρ* ≈ 0.14 maneuvered vs ≈ 5.8 without). | 18.5 kB | MIT |
| `kessler_reentry_mass.py` | the reentry bulk-mass module. Seeded Monte Carlo for satellite reentry mass against the ~15,000 t/yr natural meteoric infall. Seed 20260717, n = 100,000, cross-checked on 20260718. | 4.4 kB | MIT |
| `kessler_staged_annex_e6.md` | E6 continuity regime - source of record. The full E6 specification the paper’s §7.3 reconciles: the function trip-wire, the pre-funded disposal trust, the wind-down plan, the bridge operator - with tiers, primary citations, and the reconciliation trail. | 23.6 kB | CC BY 4.0 |
| `kessler_stakes_build.py` | the stakes-table builder. Deterministic (no draws): band → ground-level dependencies, measured from the verified 15 Jul 2026 catalog pull - the whitelist for every ground-level claim on the surface. | 4.5 kB | MIT |
| `kessler_stakes_table_v1.json` | The stakes table. | 3.4 kB | CC BY 4.0 |
| `keys_to_orbit_paper.pdf` | Who Holds the Keys to Orbit? - the research-footing supplement. The depth layer. The occupancy spine on five disclosed bases; the stock-flow engine’s criticality result (the trigger band subcritical only by virtue of collision avoidance); the governance analysis; the race model; mechanism tests; the E6 continuity regime; limitations and the established-vs-not ledger; the full source list. 24 pages. | 776.2 kB | CC BY 4.0 |
| `multishell_raw_sample.csv` | Multi-shell raw draw sample. | 200.1 kB | CC BY 4.0 |
| `multishell_results.json` | Multi-shell recorded statistics. Per-shell floor and coupled bands as reported. | 7.3 kB | CC BY 4.0 |
| `multishell_run.py` | the multi-shell two-band run. The §3 clock numbers on the measured per-km densities: the 0.71 / 1.75-day asymptote/counterfactual pair and the 2.785× altitude-spreading lever. Seed 20260715, n = 100,000. | 5.5 kB | MIT |
| `n_h_v1.csv` | n(h) - the measured altitude profile. Per-km object densities from the 15 Jul 2026 catalog (32,010 objects); the measured input under the multi-shell run. | 104.0 kB | CC BY 4.0 |
| `n_h_v1_summary.json` | n(h) summary. | 1.4 kB | CC BY 4.0 |
| `qb_engine_raw_sample.csv` | Cascade-engine raw draw sample. Raw draw vectors - recompute the parameter-belief statements without trusting ours. | 141.0 kB | CC BY 4.0 |
| `qb_engine_results.json` | Cascade-engine recorded statistics. Every criticality, trajectory, and calibration statistic the paper and report quote. | 35.3 kB | CC BY 4.0 |
| `race_map_grid_v1.json` | The race-map grid. The grid behind the §4 interactive map; the map’s data blob descends from this file. | 101.3 kB | CC BY 4.0 |
| `race_model_d3b.py` | the deployment-race model. Maps where the filing queue becomes a genuine multipolar trap over assumed payoffs - the 69 / ~17 / ~14 region shares are shares of the assumed box, never probabilities. Seed 26716, cross-checked on 26717 (deviations recorded in the results file). | 29.9 kB | MIT |
| `race_model_d3b_raw_sample.csv` | Race-model raw sweep. The 2,000-row raw sweep - reproduced byte-identically in review. | 192.6 kB | CC BY 4.0 |
| `race_model_d3b_results.json` | Race-model recorded statistics. Region shares, mechanism-test results, and the cross-seed record. | 11.0 kB | CC BY 4.0 |
| `reentry_mass_raw_sample.csv` | Reentry raw draw sample. | 87.2 kB | CC BY 4.0 |
| `reentry_mass_results.json` | Reentry recorded statistics. | 1.9 kB | CC BY 4.0 |

## How to reproduce

Each engine is a plain script with its seed fixed inside it (the seed for each
is in the table above and at the top of the file). Run it from this folder; it
takes no arguments and rewrites its own outputs in place, so `git status`
afterwards shows you what moved. Only numpy is needed.

```
pip install -r ../requirements.txt
cd keys-to-orbit
python race_model_d3b.py           # reads qb_engine_raw_sample.csv; checks its own output hashes
python kessler_qb_engine.py        # reads n_h_v1.csv; under a minute
python multishell_run.py           # reads n_h_v1.csv
python kessler_reentry_mass.py
python d15_e6_trust_sizing.py
python d15d_staged_resize.py
python ../verify_rerun.py          # compares what you just produced with what we published
```

| Script | Reads | Rewrites |
|---|---|---|
| `race_model_d3b.py` | `qb_engine_raw_sample.csv` | `race_model_d3b_results.json`, `race_model_d3b_raw_sample.csv`, `race_map_grid_v1.json` |
| `kessler_qb_engine.py` | `n_h_v1.csv` | `qb_engine_results.json`, `qb_engine_raw_sample.csv` |
| `multishell_run.py` | `n_h_v1.csv` | `multishell_results.json`, `multishell_raw_sample.csv` |
| `kessler_reentry_mass.py` | nothing | `reentry_mass_results.json`, `reentry_mass_raw_sample.csv` |
| `d15_e6_trust_sizing.py` | nothing | `d15_e6_trust_sizing_results.json`, `d15_e6_trust_sizing_raw_sample.csv` |
| `d15d_staged_resize.py` | nothing | `d15d_staged_resize_results.json` |

**One script cannot be re-run from these files.** `kessler_stakes_build.py`
builds `kessler_stakes_table_v1.json` from a Space-Track satellite-catalog export
(`../sources/Space-track.txt`, pulled 15 Jul 2026) that we do not redistribute.
The script documents the derivation; the table is its output, and it was
independently re-derived during review. A catalog you pull yourself today will
differ from that day's.

**Corrected 19 Sep 2026** (see the corrections log on the site):
`race_model_d3b.py` used to carry file paths from the machine it was built on
and would not run elsewhere, and `multishell_run.py` wrote an earlier wording of
two annotation fields than the published results file carries. Both were fixed
without touching a model line, and every output they produce is byte-identical
to the published files.

**What we got when we re-ran the published files** (2026-09-19, Windows 11,
Python 3.12.10, numpy 2.5.0):

- `race_model_d3b.py`: all three outputs byte-identical; its built-in check
  passes.
- `d15_e6_trust_sizing.py`, `d15d_staged_resize.py`, `kessler_reentry_mass.py`:
  every number identical.
- `multishell_run.py`: results file byte-identical; the raw sample differs in
  the last floating-point digit (relative 4e-16).
- `kessler_qb_engine.py`: raw sample identical; 50 values in the results file
  differ in the last floating-point digits (relative 2e-14 at most).

Last-digit differences come from platform arithmetic, not from the model. On
Windows, scripts that do not force line endings write CRLF, so a byte-level hash
of a re-run JSON or CSV can differ from `MANIFEST.sha256` even when every number
is the same. `verify_rerun.py` compares content, not line endings.

If a number in the report and a number in these files disagree, the files win,
and we want to know: https://thethirdattractor.org/corrections?study=keys-to-orbit
