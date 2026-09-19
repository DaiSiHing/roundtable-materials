# The Uneven Month - How a 2026 Oil Shock Lands on U.S. Households

How a 2026 Strait-of-Hormuz oil shock lands on U.S. households. Most dollars at the top, most pain at the bottom: the bottom bracket loses ~8.9% of after-tax income, the top ~1.6%. An exposure-and-incidence study, not a forecast.

Read the study: https://thethirdattractor.org/studies/the-uneven-month/

This folder is a byte-identical mirror of the study's public reproducibility set
("the Floor"), served at https://thethirdattractor.org/studies/the-uneven-month/materials/. The descriptions
below are the ones published in the Floor section at the bottom of the study page.
`MANIFEST.sha256` lists a SHA-256 for every file here.

| File | What it is | Size | License |
|---|---|---|---|
| `coupled_mc.py` | Independent reimplementation, written to check the engine below without reusing its code. Writes coupled_results.json; not meant to match the published results line for line. | 11.2 kB | MIT |
| `coupled_mc_raw.npz` | The raw draw vectors - all 200,000. Every draw the engine made, floor and coupled, rate and aggregate. Recompute any percentile yourself without trusting ours: np.load(…)['coupled_t_agg'] → p99 = 68.704. This is the file that makes “the files win” literally true rather than approximately true. | 8.9 MB | CC BY 4.0 |
| `coupled_mc_results.json` | Recorded statistics. Every percentile, probability, and knob setting reported above. | 5.2 kB | CC BY 4.0 |
| `coupled_mc_sample.csv` | Sample draws. A 20,000-draw random subsample of the 200,000, for eyeballing the distributions without loading the full set. Tail percentiles recompute to within roughly ±$0.2B of the published values - ordinary subsampling noise. For exact figures, use the raw draws above. | 755.6 kB | CC BY 4.0 |
| `coupled_mc_specification.md` | Coupled-tail Monte Carlo - specification & disclosure. Exactly what is drawn: copula family, crisis regime, knob grid, calibration base. Written to be checked rather than trusted. | 10.6 kB | CC BY 4.0 |
| `coupled_results.json` | Cross-check results. What coupled_mc.py writes: the independent reimplementation’s statistics. | 5.1 kB | CC BY 4.0 |
| `coupled_tail_mc.py` | The engine that produced the published numbers - Student-t copula, rotated-Clayton directional bound. Writes coupled_mc_results.json and the raw draws. | 10.5 kB | MIT |
| `household_shock_model.xlsx` | The live model. Formula-driven workbook behind every figure: assumptions, model by bracket, triage logic, incidence & sensitivity, predictive distribution. | 49.2 kB | CC BY 4.0 |
| `research_analysis.py` | Predictive distribution and the 100,000-replicate incidence bootstrap. | 12.7 kB | MIT |
| `research_results.json` | Incidence & bootstrap results. Suits and Kakwani indices with confidence intervals. | 3.3 kB | CC BY 4.0 |
| `uneven_month_research_paper.pdf` | From Brief to Estimate: A Probabilistic and Causal Footing. The methodological supplement. Monte Carlo predictive distribution (two bands - historical floor vs. tail-dependent coupled), bootstrap confidence intervals on the incidence indices, and an event-study design for the debt-triage claim. 7 pages. | 1.3 MB | CC BY 4.0 |

## How to reproduce

Each engine is a plain script with its seed fixed inside it (`20260605`,
N = 200,000). Run it from this folder; it takes no arguments and rewrites its
own outputs in place, so `git status` afterwards shows you what moved.

```
pip install -r ../requirements.txt
cd the-uneven-month
python coupled_tail_mc.py      # the full engine: floor + coupled-t + rotated-Clayton, raw draws
python coupled_mc.py           # the independent reimplementation (cross-check)
python research_analysis.py    # predictive distribution, variance split, incidence bootstrap
python ../verify_rerun.py      # compares what you just produced with what we published
```

| Script | Rewrites | Run time |
|---|---|---|
| `coupled_tail_mc.py` (needs scipy) | `coupled_mc_results.json`, `coupled_mc_raw.npz`, `coupled_mc_sample.csv`, `fig_coupled.png` | under a minute |
| `coupled_mc.py` | `coupled_results.json`, `fig_coupled.png` | seconds |
| `research_analysis.py` | `research_results.json`, `fig_mc.png`, `fig_incidence.png` | seconds |

Which script is which (the study page's provenance note says the same):
`coupled_tail_mc.py` produced the published numbers: `coupled_mc_results.json`,
the two-band figures and the raw draws, with the Student-t copula and the
rotated-Clayton bound. `coupled_mc.py` is a deliberately independent
reimplementation, written to check the first without reusing its code. It sets up
the crisis regime differently, writes `coupled_results.json`, and is not meant to
reproduce `coupled_mc_results.json` line for line. Both ship so the check itself
can be audited. (Until 19 Sep 2026 the site's file list had the one-line
descriptions of these two scripts attached to the wrong files; see the
corrections log.)

The `fig_*.png` files are new files, not part of the published set. Both
coupled scripts write a figure with the same name, `fig_coupled.png`.

To check a percentile without running anything of ours, load the 200,000 raw
draws directly: `numpy.load("coupled_mc_raw.npz")` holds `floor_*`, `coupled_t_*`
and `coupled_clayton_*` arrays, as monthly rate and as aggregate $B/month.

**What we got when we re-ran the published files** (2026-09-19, Windows 11,
Python 3.12.10, numpy 2.5.0, scipy 1.18.1, matplotlib 3.11.0):

- `coupled_mc.py`: results identical.
- `coupled_tail_mc.py`: results JSON and sample CSV identical; in the raw draws
  the floor arrays are bit-identical and the coupled arrays agree to a relative
  4e-11 or better (the copula step goes through scipy, whose last floating-point
  digits vary by platform). No published figure changes.
- `research_analysis.py`: two values differ in the last floating-point digit
  (relative 3e-16); everything else identical.

On Windows, Python writes text files with CRLF line endings, so a byte-level hash
of a re-run JSON or CSV will differ from `MANIFEST.sha256` even when every number
is the same. `verify_rerun.py` compares content, not line endings.

If a number in the report and a number in these files disagree, the files win,
and we want to know: https://thethirdattractor.org/corrections?study=the-uneven-month
