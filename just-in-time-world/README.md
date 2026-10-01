# The Just-in-Time World

Six raw materials - sand, salt, iron, copper, oil, lithium - and the supply chains that deliver them: which links actually break, how long before the shelves, the grid and the fab lines feel it, and which disruptions pass in weeks versus redraw the map. Honest bands, not one scare number.

Read the study: https://thethirdattractor.org/studies/just-in-time-world/

This folder is a byte-identical mirror of the study's public reproducibility set
("the Floor"), served at https://thethirdattractor.org/studies/just-in-time-world/materials/. The descriptions
below are the ones published in the Floor section at the bottom of the study page.
`MANIFEST.sha256` lists a SHA-256 for every file here.

| File | What it is | Size | License |
|---|---|---|---|
| `e3_energy_params.json` | Transformer-queue input: energy parameters. The base parameters from the Energy & Biophysical Economics seat. One of seven input files the engine reads from this folder at start; each is a check, not a source of numbers: every value the engine uses is a constant inside it, checked against these files. If one is missing it stops and names all seven. | 6.4 kB | CC BY 4.0 |
| `e3_energy_params_delta_d022.json` | Transformer-queue input: parameter revision. A dated revision to the energy parameters above, checked by the engine at start. | 2.6 kB | CC BY 4.0 |
| `e3_energy_params_delta_d026.json` | Transformer-queue input: parameter revision. A dated revision to the energy parameters above, checked by the engine at start. | 3.5 kB | CC BY 4.0 |
| `e3_energy_params_delta_d032.json` | Transformer-queue input: parameter revision. A dated revision to the energy parameters, partly superseded by later ones; it carries a flag saying so, which the engine checks. | 4.0 kB | CC BY 4.0 |
| `e3_energy_params_delta_d045.json` | Transformer-queue input: parameter revision. A dated revision to the energy parameters, checked by the engine at start. | 3.1 kB | CC BY 4.0 |
| `e3_energy_params_delta_esr040.json` | Transformer-queue input: parameter revision. A dated revision to the energy parameters, from the Economics & Statistics referee’s review, checked by the engine at start. | 2.8 kB | CC BY 4.0 |
| `e3_mc_specification.md` | The transformer-queue specification. What the engine is built to, parameter by parameter, and how to run it. | 15.1 kB | CC BY 4.0 |
| `e3_raw.npz` | The transformer-queue raw draws. Every draw the engine made, so any percentile can be recomputed without trusting ours. | 4.1 MB | CC BY 4.0 |
| `e3_results.json` | Transformer-queue results. What the engine recorded: every statistic and knob setting. | 75.8 kB | CC BY 4.0 |
| `e3_sample.csv` | Sample draws. A subsample for eyeballing, without loading the full set. | 24.2 kB | CC BY 4.0 |
| `e3_transformer_queue_mc.py` | The transformer-queue engine (Complex-Systems & Polycrisis seat). Seed 33, 25,000 paths per run. Writes e3_results.json, the raw draws and the sample. | 53.2 kB | MIT |
| `eb_d039_sigma_fit.py` | The sigma fit (Energy & Biophysical Economics seat): deterministic, no draws. Writes eb_d039_sigma_fit_results.json. It reads ferc1_acct353_additions.json and ppi_PCU3353113353111.json (both in this folder) and four public files too large to ship: three EIA-860 zips and an LBNL workbook, whose sources and checksums are in the paper’s Appendix B. Fetch those into this folder, unopened, and run it; it names anything missing. The one engine here not yet reproduced by a second hand. | 16.2 kB | MIT |
| `eb_d039_sigma_fit_results.json` | Sigma-fit results. What eb_d039_sigma_fit.py writes. Also the seventh input the transformer-queue engine checks at start. | 5.5 kB | CC BY 4.0 |
| `ferc1_acct353_additions.json` | Sigma-fit input: FERC Form 1 station-equipment additions. Utilities’ reported additions to transmission station equipment (FERC Account 353), as pulled for the fit, where it serves as a cross-check. Read by eb_d039_sigma_fit.py from this folder. | 341.3 kB | CC BY 4.0 |
| `just-in-time-world-paper.pdf` | The paper. The study as a single printable document. | 3.8 MB | CC BY 4.0 |
| `ppi_PCU3353113353111.json` | Sigma-fit input: transformer producer price index. The BLS producer price index for power and distribution transformer manufacturing (PCU3353113353111), monthly for 2014–2023, where the series ends; the fit’s deflator. Read by eb_d039_sigma_fit.py from this folder. | 18.2 kB | CC BY 4.0 |
| `raw_draws_sample.json` | Reserve-pool raw-draw sample. A sample of the companion engine’s draws. | 44.5 kB | CC BY 4.0 |
| `reserve_pool_mc.py` | The reserve-pool companion engine (Complex-Systems & Polycrisis seat). Seed 41. Writes reserve_pool_results.json and a raw-draw sample. | 17.7 kB | MIT |
| `reserve_pool_README.md` | Reserve-pool README. How the companion engine is run and what it answers. | 10.1 kB | CC BY 4.0 |
| `reserve_pool_results.json` | Reserve-pool results. What the companion engine recorded. | 28.2 kB | CC BY 4.0 |

## How to reproduce

Three engines. Run each from this folder; none takes arguments, and each
rewrites its own outputs in place, so `git status` afterwards shows you what
moved. The first two need only numpy; the sigma fit also needs pandas and
openpyxl, and four public files described below.

```
pip install -r ../requirements.txt
cd just-in-time-world
python e3_transformer_queue_mc.py   # seed 33; about a minute
python reserve_pool_mc.py           # seed 41; a few seconds
python eb_d039_sigma_fit.py         # deterministic, no seed; needs the four files below
python ../verify_rerun.py           # compares what you just produced with what we published
```

| Script | Reads | Rewrites |
|---|---|---|
| `e3_transformer_queue_mc.py` | the seven input files beside it: `e3_energy_params.json`, its five `e3_energy_params_delta_*.json`, and `eb_d039_sigma_fit_results.json` | `e3_results.json`, `e3_raw.npz`, `e3_sample.csv` |
| `reserve_pool_mc.py` | nothing | `reserve_pool_results.json`, `raw_draws_sample.json` |
| `eb_d039_sigma_fit.py` | `ferc1_acct353_additions.json`, `ppi_PCU3353113353111.json`, and four public files you fetch | `eb_d039_sigma_fit_results.json` |

**The transformer-queue engine's seven inputs are checks, not sources.** Every
value it uses is a constant inside the script. At start it compares those
constants with the seven files and stops if one disagrees; if a file is
missing, it stops and names all seven.

**The sigma fit needs four files we do not redistribute.** They are public,
large (about 74 MB together), and pinned by checksum rather than copied. The
paper's Appendix B lists each one with its MD5 and source address:
`eia860_2022.zip`, `eia860_2023.zip`, `eia860_2024.zip` (the EIA's Form 860
annual files) and `lbnl_ix_queue_data_file_thru2024_v2.xlsx` (Berkeley Lab's
interconnection-queue workbook). Put them in this folder, **unopened and under
those names**. The EIA serves the zips as `eia8602022.zip` and so on, so
rename them. The script reads the zips directly and, if anything is missing,
names every file it could not find. Check each file's MD5 against Appendix B
before running: a file the EIA has since revised will not give our numbers.
The 2024 file sits at the EIA's current-year address and will move to its
archive when the next year is released.

**What we got when we re-ran the published files** (2026-09-29, a fresh clone
of this repository, Windows 11, Python 3.14.5, numpy 2.5.1, pandas 3.0.5,
openpyxl 3.1.5):

- `e3_transformer_queue_mc.py` (46 s): `e3_raw.npz` and `e3_sample.csv`
  byte-identical. In `e3_results.json` exactly one value differs:
  `runtime_s`, the wall-clock time of the run (50.7 published, 45.8 here). It
  will differ on every run, so `verify_rerun.py` always reports this one file
  as DIFFERS by one number. Every modeled value in it is identical.
- `reserve_pool_mc.py` (1.5 s): both outputs byte-identical.
- `eb_d039_sigma_fit.py` (23 s), with the four files fetched and their MD5s
  matching Appendix B: `eb_d039_sigma_fit_results.json` byte-identical.
  Run without them, it stopped and named all seven missing sheet sources.

The scripts' SHA-256 values in the paper's Appendix B (taken with line endings
normalized to LF) match the files here.

**The sigma fit is the one engine in this study that nobody but its author
has reproduced.** Every other engine was reimplemented or probed during review
by someone who did not write it. Our re-run above shows that the file on disk
is what the script produces. It does not test the choices inside the script.

The transformer-queue engine and its specification carry references to the
study's internal review (dispatch and memo numbers such as `d045` or
`memo-10`) in comments and in some input file names. They record where each
constant came from, and they are left as the referees accepted them.

If a number in the report and a number in these files disagree, the files win,
and we want to know: https://thethirdattractor.org/corrections?study=just-in-time-world
