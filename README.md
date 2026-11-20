# Applied Macroeconometrics: Simulation and Forecasting in Python

**Salar Sheikholeslami**  
**Institution:** Johannes Kepler University Linz (JKU), Austria  
**Year:** 2025  
**Language:** Python  
**Area:** Applied time-series econometrics, simulation, and macroeconomic forecasting

## Overview

This repository presents selected applied macroeconometric analyses developed in Python during the *Financial and Macroeconometrics* course at JKU Linz. It focuses on two related questions:

1. How do deterministic terms and unit-root dynamics affect time-series inference?
2. How accurately do autoregressive and ARMA models forecast the U.S. Treasury yield spread out of sample?

The project combines **Monte Carlo simulation**, **unit-root diagnostics**, **recursive forecasting**, and an additional illustration of **structural change in U.S. real GDP**. It is a course-based applied econometrics portfolio project, **not a published research paper**.

## Methods and Analyses

### Monte Carlo simulation of Dickey–Fuller statistics

- Simulate the finite-sample distribution of a Dickey–Fuller statistic under a random-walk null.
- Use **10,000 replications** to explore inference with and without deterministic terms in the data-generating process.
- Visualise the resulting sampling distributions and compare empirical percentiles.

**Script:** `code/01_monte_carlo_dickey_fuller.py` (runs without external data).

### Unit roots and U.S. interest rates

- Apply Augmented Dickey–Fuller (ADF) tests to the 10-year Treasury yield, the three-month Treasury bill rate, and their spread.
- Examine sensitivity to lag length and the implications for stationarity.
- A stationary spread alongside evidence consistent with I(1) individual rates is *suggestive of cointegration*, but is **not presented here as a separately estimated formal cointegration test**.

**Script:** `code/02_unit_roots_interest_rates.py`.

### Recursive out-of-sample forecasting

- Fit **AR(7)** and **ARMA(2,1)** models to the Treasury yield spread.
- Generate **60 expanding-window, one-quarter-ahead forecasts** beginning in **2010Q1**.
- Evaluate forecast bias and compare **MAE/RMSE** and forecast-loss differences.
- The cleaned code uses a **HAC-robust test of the mean absolute forecast-loss differential**, rather than claiming that a basic paired t-test is a complete Diebold–Mariano implementation.

**Script:** `code/03_treasury_spread_forecasting.py`.

### Structural change and U.S. real GDP

- Compare the transitory component of U.S. real GDP obtained from an **HP filter (λ = 1600)** with that from a piecewise linear trend allowing a change around **1973Q2**.
- This is a *trend/cycle illustration*. The code does **not** claim to implement the full **Perron (1989)** structural-break unit-root test.

**Script:** `code/04_gdp_structural_breaks.py`.

## Repository Structure

```text
applied-macroeconometrics-python/
├── README.md
├── requirements.txt
├── .gitignore
├── code/
│   ├── 01_monte_carlo_dickey_fuller.py
│   ├── 02_unit_roots_interest_rates.py
│   ├── 03_treasury_spread_forecasting.py
│   └── 04_gdp_structural_breaks.py
├── data/
│   └── README.md
├── figures/
│   └── (three Monte Carlo distribution plots)
└── results/
    └── .gitkeep
```

## Data Requirements

The Monte Carlo simulation is self-contained, and its three figures were generated with 10,000 replications using the included script. The remaining scripts use workbook inputs from the original course-based empirical exercises:

| Input file | Expected contents | Required for |
|---|---|---|
| `data/quarterly.xlsx` | Worksheet `QUARTERLY`; columns `DATE`, `R10`, `TB3MS`, optionally `SPREAD` | Interest-rate diagnostics and forecasting |
| `data/rgdp.xlsx` | Quarterly U.S. real GDP with a `DATE` column and numeric GDP series | GDP trend analysis |

**These Excel files are not distributed with this repository.** The course datasets included U.S. macroeconomic series sourced in part from FRED. Users must supply equivalent data, check series definitions and date ranges, and place the workbooks in the `data/` directory. Because the precise original workbooks are unavailable here, numerical reproduction of every original coursework estimate is **not yet verified**.

See [`data/README.md`](data/README.md) for details.

## Running the Code

Create a Python environment and install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the Monte Carlo experiment (default: 10,000 replications):

```bash
python code/01_monte_carlo_dickey_fuller.py
```

After supplying the Excel data files, run:

```bash
python code/02_unit_roots_interest_rates.py
python code/03_treasury_spread_forecasting.py --start 2010Q1 --horizon 60
python code/04_gdp_structural_breaks.py --break-quarter 1973Q2
```

Outputs (figures and result tables) are written to `results/`. Running the forecast script requires time because it re-estimates both models at each forecast origin.

## Reproducibility and Limitations

- The code has been **reorganised and clarified** from the author's original Python exercises. It should not be treated as byte-for-byte archival coursework code.
- Only the **Monte Carlo analysis** can run without external data.
- Other analyses require input workbooks with the documented structure, and have not been validated against the original Excel files.
- Results of statistical tests depend on sample construction, deterministic specifications, lag selection, and model assumptions.
- This repository is an illustration of applied quantitative methods, not a peer-reviewed empirical contribution or an official course solution package.

## Attribution

The work builds on material taught in the Financial and Macroeconometrics course at Johannes Kepler University Linz (Summer 2025). The concepts referenced include Dickey–Fuller unit-root testing, AR/ARMA forecasting, forecast comparison, and structural breaks in macroeconomic time series. Mathematical and methodological concepts are attributed to the original literature where appropriate.

## Usage and Rights

© 2026 Salar Sheikholeslami. All rights reserved for the author's original code and documentation. No open-source licence has been granted. Third-party data and materials retain their respective rights.
