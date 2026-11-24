# Data: File Formats, Variables and Reproducibility

This directory holds the **local Excel inputs** for the applied time-series analyses. The Python source files are distributed publicly, but the original workbooks provided in the *Financial and Macroeconometrics* course at Johannes Kepler University Linz (Summer Term 2025) are **not redistributed in the public repository**.

The information below was checked against the original course workbooks and the data-loading commands used in the seven Python scripts. It is a description of the expected input **format**, not a claim that the course datasets are freely redistributable.

## 1. Which files are needed?

| File | Required worksheet | Expected format | Sample in original material | Script(s) |
|---|---|---|---|---|
| `quarterly.xlsx` | `QUARTERLY` | Header in row 1; seven named columns | 260 quarterly observations, **1960Q1–2024Q4** | `01`, `03`, `05` |
| `unknown.xlsx` | `data` | A single numerical column **without a header** | **250 observations** | `02` |
| `ybreak.xlsx` | `Break` | Header `Y` in cell A1, then one numeric observation per row | **100 observations**, with a specified break at observation 51 | `06` |
| `rgdp.xlsx` | `RGDP` | **Unnamed date column A** and named numeric series in subsequent columns | **312 quarterly observations, 1947Q1–2024Q4** | `07` |
| *(none)* | *(none)* | Observations simulated directly in Python | **10,000 Monte Carlo replications per scenario** by default | `04` |

The original course materials also included `break.xlsx` (worksheet `data`, 200 simulated observations, no header). **None of the seven scripts currently uses `break.xlsx`.** It is not required to reproduce the published code outputs. Do not confuse it with `ybreak.xlsx`.

### Workbook details

#### `quarterly.xlsx` — U.S. macroeconomic and interest-rate series

- **Worksheet:** exactly `QUARTERLY` (case matters).
- **First row:** column headers `DATE`, `INDPRO`, `UNRATE`, `FINISHED`, `SPREAD`, `R10`, `TB3MS`.
- **Frequency:** quarterly, 1960Q1 through 2024Q4 (260 rows excluding the header).
- **`DATE`:** Excel-formatted quarterly dates, read by pandas as dates; the original file begins with `1960-01-01` for 1960Q1.
- **`INDPRO`:** U.S. industrial-production index. Script 01 uses `log(INDPRO).diff()`.
- **`UNRATE`:** U.S. unemployment rate. Script 01 uses levels, ACF/PACF and an AR(2) regression.
- **`FINISHED`:** finished-goods producer-price index, as described in the source coursework. Script 01 uses `log(FINISHED).diff()` for ARMA and AR comparisons. This is a **price index**, not a quantity of finished goods.
- **`R10`:** 10-year U.S. government bond interest rate.
- **`TB3MS`:** 3-month U.S. Treasury bill interest rate.
- **`SPREAD`:** the 10-year minus 3-month interest-rate spread, i.e. **`R10 - TB3MS`**, in percentage points. This column is **required** by scripts 03 and 05; the forecasting script reads it directly rather than recomputing it.

Exact input use: `01_macro_ar_arma_models.py` needs `DATE`, `INDPRO`, `UNRATE`, `FINISHED`; `03_recursive_yield_spread_forecasting.py` needs `DATE`, `SPREAD`; `05_treasury_adf_tests.py` needs `SPREAD`, `R10`, `TB3MS`.

#### `unknown.xlsx` — stationary simulated time series

- **Worksheet:** exactly `data`.
- **Cell A1 is a numerical observation, not a column name.** The workbook contains no header row.
- **Column:** one numeric series, interpreted by the Python script as `yt`.
- **Original sample:** 250 observations.
- The reader uses `pd.read_excel(..., sheet_name="data", header=None)` and then assigns the column name `yt`. Using the default Excel header behaviour would incorrectly drop the first observation and change the estimation sample.

#### `ybreak.xlsx` — simulated structural-break series

- **Worksheet:** exactly `Break`.
- **Cell A1:** the literal column name `Y`.
- **Rows below the header:** 100 numeric observations.
- **Known break:** at observation **t = 51**, as specified in the original course material. The Python script's plot uses zero-based positions; the marker is therefore placed at index 50.
- The script reads the series in levels, differences it for correlograms, and runs the original break-adjusted regressions and residual diagnostics.

#### `rgdp.xlsx` — quarterly U.S. real GDP

- **Worksheet:** exactly `RGDP`.
- **Column A:** quarterly Excel dates with **no name in the first header cell** (`A1` is blank).
- **Column B:** `RGDP`, U.S. real GDP (numeric).
- **Additional columns:** `RCONS`, `RINV`, and `RGOVT` are present in the supplied workbook; **the current Python script does not use them**.
- **Frequency:** 1947Q1 through 2024Q4; 312 observations.
- Script 07 accesses the dates from the **first column by position** and accesses the **first numeric column** as the real-GDP series. Do not prepend a numeric identifier or change the column order: doing so would make a different numeric column the model input.
- The original script contains a fixed break index (`break_index = 107`, zero-based). In this workbook it corresponds to **1973Q4** as the first period affected by the break dummy / slope-change term. Some plots separately mark **1973Q2 as an oil-shock reference date**. These markers are not interchangeable; the script retains the original fixed model index rather than silently changing its specification.

## 2. Local directory layout

Keep the workbooks **on your own computer** in the repository's `data/` directory:

```text
Applied-Macroeconometrics-Simulation-and-Forecasting/
├── README.md
├── code/
│   ├── README.md
│   ├── 01_macro_ar_arma_models.py
│   ├── 02_simulated_dgp_model_selection.py
│   ├── ...
│   └── 07_real_gdp_trend_decomposition.py
└── data/
    ├── README.md
    ├── quarterly.xlsx    # local only; do not commit publicly
    ├── unknown.xlsx      # local only; do not commit publicly
    ├── ybreak.xlsx       # local only; do not commit publicly
    └── rgdp.xlsx         # local only; do not commit publicly
```

The `data/README.md` file **is published** so that users know what to provide. The `.xlsx` files are **not part of the public release**.

## 3. How the scripts locate their inputs

Each empirical script is independent, includes its own output-saving functions, and has **one filename setting** near the top:

```python
DATA_FILE = 'quarterly.xlsx'
DATA_SHEET = 'QUARTERLY'
```

When launched from the repository, the scripts search for a workbook with that name, including `data/`, the project root and the script directory. The notebook working directory is also checked. The original Windows desktop path may be available as a final fallback, but it is **not required**.

If the workbook is elsewhere, supply its path by changing only `DATA_FILE`:

```python
DATA_FILE = r"C:\path\to\quarterly.xlsx"
```

`DATA_SHEET` must match the actual worksheet name. Do **not** rename source columns unless you also adjust the reader. Do **not** move the data into an unspecified sheet or CSV file and expect an unchanged result.

Run from the project root with:

```bash
python code/01_macro_ar_arma_models.py
```

Or in a Jupyter notebook whose working directory is the project root:

```python
%run code/01_macro_ar_arma_models.py
```

The Monte Carlo script (`04`) creates its observations internally: it has **no Excel input**.

## 4. How to check the input files

The following commands can be run locally after installing the packages listed in the repository's `requirements.txt`:

```python
import pandas as pd
from pathlib import Path

folder = Path('data')

quarterly = pd.read_excel(folder / 'quarterly.xlsx', sheet_name='QUARTERLY')
print(quarterly.shape)                 # Expected: (260, 7)
print(quarterly.columns.tolist())      # DATE, INDPRO, UNRATE, FINISHED, SPREAD, R10, TB3MS

unknown = pd.read_excel(folder / 'unknown.xlsx', sheet_name='data', header=None)
print(unknown.shape)                   # Expected: (250, 1)

ybreak = pd.read_excel(folder / 'ybreak.xlsx', sheet_name='Break')
print(ybreak.shape)                    # Expected: (100, 1)
print(ybreak.columns.tolist())         # ['Y']

rgdp = pd.read_excel(folder / 'rgdp.xlsx', sheet_name='RGDP')
print(rgdp.shape)                      # Expected: (312, 5)
print(rgdp.columns.tolist())           # ['Unnamed: 0', 'RGDP', 'RCONS', 'RINV', 'RGOVT']
```

The dimensions and names above describe **the original course workbooks**. If you use replacement data, differences in data vintage, source, frequency or missing-value treatment can change the estimates, forecasts and plots.

## 5. Data availability, reuse and attribution

The original input workbooks were provided for coursework at JKU Linz. **They are not included in this public GitHub repository**, and this README does not grant permission to redistribute them.

- For publicly accessible macroeconomic series, obtain the underlying data independently from an authorised source; course documentation identifies FRED as a source for the macroeconomic variables. Check each series' source and applicable reuse terms.
- For the simulated workbooks (`unknown.xlsx`, `ybreak.xlsx`, and unused `break.xlsx`), obtain the original data through an authorised course channel or with the instructor's permission. They cannot be exactly reconstructed from the description in this README alone.
- Cite the original data providers and recognise contributors to the underlying course materials as appropriate.
- The generated PNG plots and result tables are outputs of the scripts, not substitutes for the underlying raw observations.

For details of the methods and code organisation, see the [main README].
