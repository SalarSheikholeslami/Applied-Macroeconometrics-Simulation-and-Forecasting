"""Augmented Dickey-Fuller Tests for Treasury Rates.

Examine the spread between long- and short-term U.S. Treasury rates and compare ADF statistics under the original lag specifications.

Input workbook : quarterly.xlsx
Excel worksheet: QUARTERLY
Input variables: SPREAD, R10, TB3MS
"""

from pathlib import Path
import re
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.tsa.stattools as ts
from statsmodels.tsa.stattools import acf, pacf, adfuller
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.filters.hp_filter import hpfilter
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.stats.diagnostic import acorr_ljungbox

# ===================== INPUT SETTINGS =====================
# Place the Excel file in the project data/ folder or next to this script.
# Alternatively set DATA_FILE to an absolute path such as:
# DATA_FILE = r"C:\Users\Salar\Desktop\Project\data\quarterly.xlsx"
DATA_FILE = 'quarterly.xlsx'

# =========================================================
def project_folder():
    if "__file__" in globals():
        folder = Path(__file__).resolve().parent
        return folder.parent if folder.name.lower() == "code" else folder
    return Path.cwd()  # When pasted directly into a Jupyter cell

ROOT = project_folder()
SCRIPT = '05_treasury_adf_tests'
OUTPUT = ROOT / "Applied_Macroeconometric"
FIGURES = OUTPUT / "figures" / SCRIPT
TABLES = OUTPUT / "tables" / SCRIPT
for folder in (FIGURES, TABLES):
    folder.mkdir(parents=True, exist_ok=True)


def find_data(filename):
    """Locate one Excel workbook; set DATA_FILE above to override the search."""
    if filename is None:
        return None
    requested = Path(filename)
    candidates = [
        requested, ROOT / "data" / requested.name, ROOT / requested.name,
        ROOT / "code" / requested.name, Path.cwd() / "data" / requested.name,
        Path.cwd() / requested.name,
        Path("C:/Users/Salar/Desktop") / requested.name,
    ]
    for path in candidates:
        if path.is_file():
            print(f"Input data: {path.resolve()}")
            return str(path.resolve())
    raise FileNotFoundError(
        f"Could not find {requested.name}. Put it in {ROOT / 'data'}, "
        f"beside this script, or set DATA_FILE to its full path."
    )


def save_table(values, filename):
    """Save standard, reusable result tables as CSV and HTML."""
    table = pd.DataFrame(values).copy()
    show_index = not isinstance(table.index, pd.RangeIndex)
    table.to_csv(TABLES / f"{filename}.csv", index=show_index,
                 float_format="%.6f", encoding="utf-8-sig")
    html_table = table.round(6).to_html(index=show_index, border=0)
    styles = """<style>body{font-family:Arial,sans-serif;margin:28px;color:#243147}
      table{border-collapse:collapse;font-size:13px;min-width:540px}
      th,td{padding:8px 13px;text-align:right;border-bottom:1px solid #d9dfe7}
      th:first-child,td:first-child{text-align:left}
      thead th{border-bottom:2px solid #35465b;background:#f4f6fa}
      tr:hover{background:#f9fbfe}</style>"""
    (TABLES / f"{filename}.html").write_text(
        "<!doctype html><meta charset='utf-8'>" + styles + html_table,
        encoding="utf-8"
    )


def save_model(model, filename):
    """Save model estimates, standard errors and original summary output."""
    params = model.params
    names = (list(params.index) if isinstance(params, pd.Series)
             else list(getattr(model, "param_names", model.model.exog_names)))
    estimates = pd.DataFrame({
        "Estimate": np.asarray(model.params),
        "Std. error": np.asarray(model.bse),
        "t/z statistic": np.asarray(model.tvalues),
        "p-value": np.asarray(model.pvalues)
    }, index=names)
    save_table(estimates, filename)
    (TABLES / f"{filename}_full_summary.txt").write_text(
        model.summary().as_text(), encoding="utf-8"
    )


_figures_saved = 0

def save_plot():
    """Save the current plots (including ACF/PACF plots) and show them."""
    global _figures_saved
    for figure_number in list(plt.get_fignums()):
        figure = plt.figure(figure_number)
        has_content = any(ax.lines or ax.collections or ax.patches or ax.images
                          or ax.containers for ax in figure.axes)
        if not has_content:
            plt.close(figure)
            continue
        _figures_saved += 1
        title = next((ax.get_title() for ax in figure.axes if ax.get_title()), "figure")
        slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:65] or "figure"
        destination = FIGURES / f"{_figures_saved:02d}_{slug}.png"
        figure.savefig(destination, dpi=220, bbox_inches="tight")
        print(f"Saved figure: {destination.name}")
    if "agg" not in plt.get_backend().lower():
        plt.show()
    plt.close("all")


# Names here allow the original computational statements to remain unchanged.
export_model = save_model
export_table = save_table

def export_statistics(stats, name):
    save_table(pd.DataFrame([stats]), name)

print(f"Outputs: {OUTPUT}")

import pandas as pd
from statsmodels.tsa.stattools import acf

file_path = find_data(DATA_FILE)
df = pd.read_excel(file_path)

spread = df['SPREAD'].dropna()
ACF = acf(spread, nlags=12)

plt.figure(figsize=(8, 5))
plt.stem(range(1, 13), ACF[1:13])
plt.title("ACF of Spread")
plt.xlabel("Lag")
plt.ylabel("ACF Coefficient")
plt.tight_layout()
save_plot()

print("First 12 ACF values :")
for i, val in enumerate(ACF[1:13], 1):
    print(f"Lag {i}: {round(val, 4)}")


# === Treasury yield spread: sample ACF ===
# Plot short-run autocorrelation in the spread.


import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller

st_lag = spread.shift(1)
diffs = pd.concat([spread.diff().shift(i) for i in range(1, 9)], axis=1)
diffs.columns = [f'd{i}' for i in range(1, 9)]

X = pd.concat([st_lag, diffs], axis=1).dropna()
X = sm.add_constant(X)  # add intercept
y = spread.diff().loc[X.index]
model = sm.OLS(y, X).fit()
print(model.summary())

result = adfuller(spread, maxlag=8, regression='c', autolag=None)

print("\nADF t-statistic:", round(result[0], 4))
print("p-value:", round(result[1], 4))
print("Lags Used:", result[2])
print("Critical Values:")
for key, value in result[4].items():
    print(f"  {key}: {round(value, 4)}")


# === Yield spread: ADF(8) ===
# Test the spread for a unit root with eight lagged differences.


r10 = df['R10'].dropna()
delta_r10 = r10.diff()
r10_lag = r10.shift(1)

diff_lags = pd.concat([delta_r10.shift(i) for i in range(1, 9)], axis=1)
diff_lags.columns = [f'd{i}' for i in range(1, 9)]

X = pd.concat([r10_lag, diff_lags], axis=1).dropna()
X = sm.add_constant(X)
y = delta_r10.loc[X.index]
model = sm.OLS(y, X).fit()
print("\n=== Regression Summary (ADF Model) ===")
print(model.summary())

adf_result = adfuller(r10, maxlag=8, regression='c', autolag=None)

print("ADF Test Statistic:", round(adf_result[0], 4))
print("p-value:", round(adf_result[1], 4))
print("Lags Used:", adf_result[2])
print("Dickey-Fuller Critical Values:")
for key, value in adf_result[4].items():
    print(f"  {key}: {round(value, 4)}")


# === 10-year Treasury rate: ADF(8) ===
# Assess the unit-root hypothesis for the long-term interest rate.


tbill = df['TB3MS'].dropna()
delta_tbill = tbill.diff()
tbill_lag = tbill.shift(1)

diff_lags = pd.concat([delta_tbill.shift(i) for i in range(1, 9)], axis=1)
diff_lags.columns = [f'd{i}' for i in range(1, 9)]

X = pd.concat([tbill_lag, diff_lags], axis=1).dropna()
X = sm.add_constant(X)
y = delta_tbill.loc[X.index]
model = sm.OLS(y, X).fit()
print("\n=== Regression Summary (ADF Model for T-bill) ===")
print(model.summary())
adf_result = adfuller(tbill, maxlag=8, regression='c', autolag=None)

print("ADF Test Statistic:", round(adf_result[0], 4))
print("p-value:", round(adf_result[1], 4))
print("Lags Used:", adf_result[2])
print("Number of Observations:", adf_result[3])
print("Dickey-Fuller Critical Values:")
for key, value in adf_result[4].items():
    print(f"  {key}: {round(value, 4)}")


# === 3-month Treasury bill rate: ADF(8) ===
# Assess the unit-root hypothesis for the short-term interest rate.


# === Comparison of stationarity findings ===
# Compare evidence across the spread and the underlying interest rates.


tbill = df['TB3MS'].dropna()
delta_tbill = tbill.diff()
tbill_lag = tbill.shift(1)

diff_lags = pd.concat([delta_tbill.shift(i) for i in range(1, 6)], axis=1)
diff_lags.columns = [f'd{i}' for i in range(1, 6)]

X = pd.concat([tbill_lag, diff_lags], axis=1).dropna()
X = sm.add_constant(X)
y = delta_tbill.loc[X.index]

model = sm.OLS(y, X).fit()
print("\n=== Regression Summary (ADF Model for T-bill, 5 Lags) ===")
print(model.summary())

adf_result = adfuller(tbill, maxlag=5, regression='c', autolag=None)

print("ADF Test Statistic:", round(adf_result[0], 4))
print("p-value:", round(adf_result[1], 4))
print("Lags Used:", adf_result[2])
print("Dickey-Fuller Critical Values:")
for key, value in adf_result[4].items():
    print(f"  {key}: {round(value, 4)}")


# === Export computed ADF test results with original lag specifications ===
def adf_row(series, label, lags):
    res = adfuller(series.dropna(), maxlag=lags, regression='c', autolag=None)
    return {'Series':label, 'ADF_lags':lags, 'ADF_statistic':res[0],
            'p_value':res[1], 'Observations':res[3],
            'Critical_1pct':res[4]['1%'], 'Critical_5pct':res[4]['5%'],
            'Critical_10pct':res[4]['10%']}
export_table(pd.DataFrame([adf_row(spread,'Treasury spread',8), adf_row(r10,'10-year rate',8),
                           adf_row(tbill,'3-month bill rate',8),adf_row(tbill,'3-month bill rate',5)]),
             'treasury_adf_results')

