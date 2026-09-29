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
| `just-in-time-world-paper.pdf` | The paper. The study as a single printable document. | 3.9 MB | CC BY 4.0 |
| `ppi_PCU3353113353111.json` | Sigma-fit input: transformer producer price index. The BLS producer price index for power and distribution transformer manufacturing (PCU3353113353111), monthly for 2014–2023, where the series ends; the fit’s deflator. Read by eb_d039_sigma_fit.py from this folder. | 18.2 kB | CC BY 4.0 |
| `raw_draws_sample.json` | Reserve-pool raw-draw sample. A sample of the companion engine’s draws. | 44.5 kB | CC BY 4.0 |
| `reserve_pool_mc.py` | The reserve-pool companion engine (Complex-Systems & Polycrisis seat). Seed 41. Writes reserve_pool_results.json and a raw-draw sample. | 17.7 kB | MIT |
| `reserve_pool_README.md` | Reserve-pool README. How the companion engine is run and what it answers. | 10.1 kB | CC BY 4.0 |
| `reserve_pool_results.json` | Reserve-pool results. What the companion engine recorded. | 28.2 kB | CC BY 4.0 |

## How to reproduce

Each engine is a plain Python script with its seed fixed inside it. Run it from
this folder (`pip install -r ../requirements.txt` first); it takes no arguments
and rewrites its own outputs in place. Then run `python ../verify_rerun.py` to
compare what you produced with what we published.

If a number in the report and a number in these files disagree, the files win,
and we want to know: https://thethirdattractor.org/corrections?study=just-in-time-world
