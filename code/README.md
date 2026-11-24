# Python Scripts: Econometric Analyses

This directory contains **seven standalone Python programs**, organised by substantive econometric topic.

## Script overview

| Script | Purpose | Excel input | Output examples |
|---|---|---|---|
| [`01_macro_ar_arma_models.py`](01_macro_ar_arma_models.py) | Industrial-production log changes, unemployment persistence, and modelling of log changes in `FINISHED` | `quarterly.xlsx` → `QUARTERLY`; `DATE`, `INDPRO`, `UNRATE`, `FINISHED` | AR(1)/AR(2)/ARMA(1,1)/AR(3) coefficient tables, residual ACF, Ljung–Box and AIC/BIC |
| [`02_simulated_dgp_model_selection.py`](02_simulated_dgp_model_selection.py) | Identify a plausible model for a stationary simulated series | `unknown.xlsx` → `data`; **no header**, 250 numeric values | ACF/PACF, AR(2)/AR(3)/ARMA(2,1) comparisons and residual tests |
| [`03_recursive_yield_spread_forecasting.py`](03_recursive_yield_spread_forecasting.py) | AR(7) versus ARMA(2,1) forecasts of the 10-year/3-month U.S. yield spread | `quarterly.xlsx` → `QUARTERLY`; `DATE`, `SPREAD` | 60 one-quarter-ahead forecasts, bias regression, forecast losses and comparison plot |
| [`04_monte_carlo_unit_root_inference.py`](04_monte_carlo_unit_root_inference.py) | Monte Carlo distributions of Dickey–Fuller and related t-statistics | No external workbook | Simulation histograms and percentile tables |
| [`05_treasury_adf_tests.py`](05_treasury_adf_tests.py) | ADF stationarity diagnostics for the Treasury yield spread and component interest rates | `quarterly.xlsx` → `QUARTERLY`; `SPREAD`, `R10`, `TB3MS` | ACF and lag-specific ADF results |
| [`06_structural_break_unit_root.py`](06_structural_break_unit_root.py) | DF and break-adjusted diagnostics for simulated observations | `ybreak.xlsx` → `Break`; `Y` | Time series and correlograms; original detrending and residual regressions |
| [`07_real_gdp_trend_decomposition.py`](07_real_gdp_trend_decomposition.py) | HP-filter and broken-trend decomposition of real GDP | `rgdp.xlsx` → `RGDP`; unnamed date column and `RGDP` | GDP trend/cycle charts; fitted models and components table |

**Not used:** `break.xlsx` was distributed with the course material, but no matching analysis was present in the original Python files selected for this repository.

## How to run a script

1. Place the matching Excel workbook in the repository's `data/` directory. The Monte Carlo script does not need Excel input.
2. If required libraries are missing, from the repository root run `python -m pip install -r requirements.txt`.
3. Run one standalone script from the repository root, for example:

```bash
python code/01_macro_ar_arma_models.py
```

To run in Jupyter Notebook without pasting the Python source into a cell:

```python
%run code/01_macro_ar_arma_models.py
```

Scripts 03 and 04 may take longer with their defaults. For a **temporary test**, change `FORECAST_HORIZON = 60` in script 03 or `REPETITIONS = 10000` in script 04, then restore the defaults when generating final output.

## Input settings in the source

Every data-based script declares its exact workbook and worksheet near the top, for example:

```python
DATA_FILE = 'quarterly.xlsx'
DATA_SHEET = 'QUARTERLY'
```

The readers find the named workbook in common locations (`data/`, project root or the directory next to the script). To use a different local file, edit **only** `DATA_FILE` to a full path. For the original spreadsheet structures, column names and record counts, read [`data/README.md`](../data/README.md).

## Outputs

After each run, the script automatically creates directories below the repository root:

```text
Applied_Macroeconometric/
├── figures/
│   └── <script name>/           # numbered PNG figures
└── tables/
    └── <script name>/           # CSV and HTML tables, TXT model summaries
```

Saved outputs reflect the underlying script, original model design and input data. Running a script again can **overwrite** earlier files with the same names. Keep a copy if you need to preserve a previous run.

## Interpretation and scope

- For the forecasts, the paired t-test of absolute errors is reported **as a paired t-test**, not as a fully HAC-adjusted Diebold–Mariano statistic.
- The simulated-series comparisons use all **250 observations**, reading `unknown.xlsx` with `header=None`.
- The real-GDP script preserves the original `break_index = 107` model convention, which in the supplied workbook makes **1973Q4** the first affected quarter. A separate chart marker at **1973Q2** is an oil-shock reference date, not the trend-model breakpoint.
- The code is a research-skills portfolio developed from course-related work. It should not be described as a published research paper, a formal teaching solution set, or a fully validated implementation of every structural-break test mentioned in the original teaching material.

Further context: [main README](../README.md) · [Data formats and access](../data/README.md) · [Selected results](../results.md).
