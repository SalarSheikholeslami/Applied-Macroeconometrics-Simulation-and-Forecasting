# Applied Macroeconometrics

## 1. Analyses and input data

| Script | Primary analysis | Excel input | Worksheet |
|---|---|---|---|
| `01_macro_ar_arma_models.py` | Growth of industrial production; AR(1); unemployment AR(2); FINISHED log changes, ARMA(1,1) vs AR(3), ACF and Ljung–Box | `quarterly.xlsx` | `QUARTERLY` |
| `02_simulated_dgp_model_selection.py` | ACF/PACF, AR(2), AR(3), ARMA(2,1), model residuals, AIC/BIC | `unknown.xlsx` | `data` |
| `03_recursive_yield_spread_forecasting.py` | AR(7) and ARMA(2,1) expanding-window forecasts; forecast bias and loss comparison | `quarterly.xlsx` | `QUARTERLY` |
| `04_monte_carlo_unit_root_inference.py` | Random-walk, trend and deterministic-term Monte Carlo simulations | None; simulated internally | — |
| `05_treasury_adf_tests.py` | ADF(8) of the spread and two rates; sensitivity to ADF(5) | `quarterly.xlsx` | `QUARTERLY` |
| `06_structural_break_unit_root.py` | Known structural break at observation 51; ACF/PACF, DF and residual regressions | `ybreak.xlsx` | `Break` |
| `07_real_gdp_trend_decomposition.py` | Break-adjusted trend and unit-root diagnostics; HP(1600) and piecewise trend | `rgdp.xlsx` | `RGDP` |

`FINISHED` is the variable name from the original dataset; its log difference is analysed without inventing new variables such as `PPI`.

## 3. Saved results

No setup is required. Each script automatically creates a project output directory alongside `code/`:

```text
Applied_Macroeconometric/
  figures/
    01_macro_ar_arma_models/              # PNG figures at 220 dpi
    02_simulated_dgp_model_selection/
    ...
  tables/
    01_macro_ar_arma_models/              # regression estimates as CSV/HTML
    02_simulated_dgp_model_selection/     # model comparisons / diagnostics
    ...
```

Regression coefficient tables and Ljung–Box/ADF results appear as CSV and HTML. Full fitted-model summary text files are retained where model results are exported. Plot creation and export occur directly in each independent script.

Generated outputs from complete execution are included in the downloadable archive and summarized in results folder. The compiled public package contains derived figures and tables, but not the input workbooks.

## 4. Longer runs

The Monte Carlo uses 10,000 replications. Recursive forecast evaluation covers 60 one-quarter-ahead forecasts. Both programs can take time. For a quick smoke test, you may temporarily edit just the top-line settings:

```python
REPETITIONS = 50        # in code/04 only; restore to 10000
FORECAST_HORIZON = 8    # in code/03 only; restore to 60
```

## 5. Method and data notes

- Original quarterly series are dated 1960Q1–2024Q4 in the supplied workbook, and the real GDP workbook covers 1947Q1–2024Q4.
- `unknown.xlsx` contains **250 numeric observations and no column header**. This code explicitly reads `header=None`, correcting a data-import issue in the earlier script that discarded the first value. This is an input correction, not a model change.
- The forecasting script calls the Granger–Newbold procedure only **after** computing forecast errors, correcting the original statement order so execution succeeds.
- The absolute-error comparison is the **paired t-test** originally calculated with `scipy.stats.ttest_rel`. It should not be described as a fully serial-correlation-robust Diebold–Mariano test.
- The break-adjusted residual regressions reproduce the original specifications; they are not represented as a verified general-purpose implementation of Perron (1989).
- The other course-supplied `break.xlsx` workbook relates to a parameter-instability analysis for which **no corresponding Python code was in the two original files**. No new analytical method was invented for it.

- 
