**Salar Sheikholeslami**  
**Institution:** Johannes Kepler University Linz (JKU), Austria  
**Academic context:** Financial and Macroeconometrics, Jun 2025  
**Language:** Python  
**Focus:** Time-series econometrics, Monte Carlo simulation, unit-root testing, structural change and macroeconomic forecasting

## Overview

This repository brings together a selection of applied macroeconometric analyses implemented in Python. It examines the dynamic behaviour of U.S. macroeconomic time series, compares alternative autoregressive specifications, studies statistical inference in nonstationary processes, and evaluates short-horizon forecasts of the U.S. Treasury yield spread.

The analyses are organised into **seven standalone scripts**, grouped by their econometric objectives rather than by coursework question numbers. The scripts retain the original estimation approaches and model specifications, with minor adjustments for data loading, execution and automatic export of figures and tables. The project is a **course-based quantitative portfolio**, not a peer-reviewed research paper.

## Analyses

| Script | Econometric analysis | Methods |
|---|---|---|
| [`01_macro_ar_arma_models.py`](code/01_macro_ar_arma_models.py) | Dynamics of U.S. industrial production, unemployment and the `FINISHED` index | Log differences; AR(1), AR(2), ARMA(1,1), AR(3); ACF/PACF; Ljung–Box; AIC/BIC |
| [`02_simulated_dgp_model_selection.py`](code/02_simulated_dgp_model_selection.py) | Identifying a plausible time-series specification from simulated observations | ACF/PACF; AR(2), AR(3), ARMA(2,1); residual diagnostics; AIC/BIC |
| [`03_recursive_yield_spread_forecasting.py`](code/03_recursive_yield_spread_forecasting.py) | One-quarter-ahead forecasts of the U.S. Treasury yield spread | AR(7) vs. ARMA(2,1); expanding-window estimation; forecast bias; absolute forecast errors |
| [`04_monte_carlo_unit_root_inference.py`](code/04_monte_carlo_unit_root_inference.py) | Sampling distributions of unit-root test statistics under different deterministic specifications | Random-walk simulations; Dickey–Fuller statistics; Monte Carlo percentiles |
| [`05_treasury_adf_tests.py`](code/05_treasury_adf_tests.py) | Stationarity of U.S. Treasury interest rates and their spread | Augmented Dickey–Fuller tests; alternative lag lengths |
| [`06_structural_break_unit_root.py`](code/06_structural_break_unit_root.py) | Unit-root diagnostics in a simulated series with a known structural break | Break inspection; ACF/PACF; Dickey–Fuller and residual diagnostics |
| [`07_real_gdp_trend_decomposition.py`](code/07_real_gdp_trend_decomposition.py) | Structural change and decomposition of U.S. real GDP | Break-adjusted trend specifications; HP filter (λ = 1,600); piecewise linear trend |

### Selected results

- **Dynamic macroeconomic models:** The industrial production series is analysed in log differences with an AR(1) model; unemployment persistence is examined with an AR(2) specification. For the log-differenced `FINISHED` index, AR(3) has a slightly lower AIC than ARMA(1,1), whereas ARMA(1,1) has the lower BIC.
- **Simulated model identification:** AR(3) is preferred among the three evaluated candidate models by both AIC and BIC when all 250 observations in `unknown.xlsx` are included.
- **Yield-spread forecasting:** The original specification generates **60 expanding-window, one-quarter-ahead forecasts**. The mean absolute errors are approximately **0.286** for AR(7) and **0.283** for ARMA(2,1). The difference is not statistically significant under the original paired t-test on absolute errors (p ≈ 0.724).
- **Unit-root diagnostics:** With eight ADF lags, the Treasury yield spread rejects the unit-root null, whereas the two individual interest-rate series do not reject it at conventional levels. Results for the short-term rate are sensitive to the selected lag length.
- **Simulation and structural change:** **10,000 Monte Carlo replications per scenario** illustrate the influence of deterministic terms on unit-root inference; separate analyses examine a simulated structural break and alternative real-GDP trend decompositions.

Detailed results and source-linked outputs are collected in [RESULTS.md](RESULTS.md).

![Recursive one-quarter-ahead Treasury spread forecasts](Applied_Macroeconometric/figures/03_recursive_yield_spread_forecasting/01_recursive_one_quarter_ahead_forecasts_treasury_yield_spread.png)

## Repository structure

```text
.
├── README.md
├── RESULTS.md
├── requirements.txt
├── .gitignore
├── code/
│   ├── 01_macro_ar_arma_models.py
│   ├── 02_simulated_dgp_model_selection.py
│   ├── 03_recursive_yield_spread_forecasting.py
│   ├── 04_monte_carlo_unit_root_inference.py
│   ├── 05_treasury_adf_tests.py
│   ├── 06_structural_break_unit_root.py
│   └── 07_real_gdp_trend_decomposition.py
├── data/
│   └── README.md
└── Applied_Macroeconometric/
    ├── figures/                    # PNG figures, grouped by script
    └── tables/                     # CSV, HTML and model-summary TXT files
```

All scripts are **self-contained**: no custom helper module such as `project_io.py` is required. Each script creates its own output subdirectories automatically.

## Data requirements and availability

The Monte Carlo script generates its observations internally and **does not require an external dataset**. The empirical analyses use the following Excel workbooks:

| Workbook | Excel sheet | Main variables / contents | Used by |
|---|---|---|---|
| `quarterly.xlsx` | `QUARTERLY` | `DATE`, `INDPRO`, `UNRATE`, `FINISHED`, `SPREAD`, `R10`, `TB3MS` | Scripts 01, 03 and 05 |
| `unknown.xlsx` | `data` | One numeric simulated series, **250 observations without a header** | Script 02 |
| `ybreak.xlsx` | `Break` | Simulated series `Y` with a break at observation 51 | Script 06 |
| `rgdp.xlsx` | `RGDP` | Quarterly U.S. real GDP and observation dates | Script 07 |

The supplied course materials also contained `break.xlsx`, but **no corresponding implementation was present in the original Python scripts** used for this repository; it is therefore not an input to the seven scripts listed above.

**The original course-provided Excel datasets are not redistributed in this public repository.** To reproduce the data-based analyses, obtain the workbooks from an authorised source and place them in a local `data/` folder, retaining the filenames and worksheet names. The U.S. macroeconomic series originate from the course-provided material; independently downloaded replacements may differ in definitions, revisions or sample coverage and therefore may not reproduce the same numbers. See [data/README.md](data/README.md) for the expected layout.

## Running the code

### 1. Install the Python packages

Install the dependencies once, if they are not already available in your Python environment:

```bash
python -m pip install -r requirements.txt
```

The project uses NumPy, pandas, matplotlib, seaborn, SciPy, statsmodels and openpyxl.

### 2. Provide the input data

Put the required `.xlsx` workbooks into a local `data/` folder alongside `code/`. By default, each empirical script searches for its named workbook automatically. If a file is stored elsewhere, change only the `DATA_FILE` setting near the beginning of that script:

```python
DATA_FILE = r"C:\path\to\quarterly.xlsx"
```

The Monte Carlo script has `DATA_FILE = None` because its observations are simulated within Python.

### 3. Run a script

From the repository's main directory, for example:

```bash
python code/01_macro_ar_arma_models.py
python code/02_simulated_dgp_model_selection.py
python code/03_recursive_yield_spread_forecasting.py
python code/04_monte_carlo_unit_root_inference.py
python code/05_treasury_adf_tests.py
python code/06_structural_break_unit_root.py
python code/07_real_gdp_trend_decomposition.py
```

You may also run a script from Jupyter Notebook when the notebook's working directory is the project root:

```python
%run code/01_macro_ar_arma_models.py
```

For a short computational check, the relevant scripts expose two settings near the top:

```python
REPETITIONS = 10000      # Monte Carlo: code/04
FORECAST_HORIZON = 60   # Recursive forecasting: code/03
```

Reducing these values speeds up a test run; restore their defaults for the reported analyses.

### 4. Find the exported results

On execution, each script creates directories within `Applied_Macroeconometric/` and saves:

- **Figures:** `.png` files, grouped by script under `figures/`.
- **Tables:** `.csv` and `.html` files containing model estimates, diagnostics, simulations and forecasting results, as applicable.
- **Model summaries:** `.txt` files where full fitted-model output is exported.

Existing exported outputs included in the public package can be viewed without rerunning the scripts.

## Reproducibility and methodological notes

- The project retains the original model orders, estimation approaches and main calculations, but the scripts are **not byte-for-byte copies** of the initial coursework code. They include execution, data-import and export adjustments.
- `unknown.xlsx` is read without treating its first observation as a header, so all **250 observations** are included. This corrects a data-reading issue in the earlier script and may affect its reported estimates.
- Forecast comparison preserves the original **paired t-test of absolute prediction errors**. It is **not** presented as a fully heteroskedasticity-and-autocorrelation-robust Diebold–Mariano test.
- The real-GDP structural-break and residual regressions reflect the original implemented specifications; the repository does **not** claim a complete, independently validated Perron (1989) testing procedure.
- Numerical results depend on the source workbooks, data revisions, estimation windows, test specifications and package versions.

## Academic context and attribution

This repository presents Python analyses developed in connection with the *Financial and Macroeconometrics* course at Johannes Kepler University Linz in 2025. **Salar Sheikholeslami** prepared this GitHub portfolio. The underlying coursework reports list **Salar Sheikholeslami and Amirhossein Sheikholeslami**; their respective contributions should be acknowledged where applicable.

The repository is intended to demonstrate applied econometric programming and empirical analysis. It is **not an official solution set, a peer-reviewed publication, or a claim of unrestricted rights over course-provided datasets**.


