"""Monte Carlo Inference for Unit-Root Processes.

Simulate random-walk and deterministic-trend processes to examine the empirical distributions of Dickey-Fuller-type statistics. No external dataset is required.

Input workbook : None — data are simulated internally
Excel worksheet: Not applicable
Input variables: Generated in Python
Data source: Generated in Python (no input file)

Run as a standalone .py file or paste into a Jupyter notebook.
Outputs are written automatically to Applied_Macroeconometric/figures and /tables.
"""

from pathlib import Path
import re
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import statsmodels.tsa.stattools as ts
from statsmodels.tsa.stattools import acf, pacf, adfuller
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.filters.hp_filter import hpfilter
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.stats.diagnostic import acorr_ljungbox

# ===================== INPUT SETTINGS =====================
# All observations are simulated; no Excel file needs to be supplied.
DATA_FILE = None
REPETITIONS = 10000  # Set e.g. 50 for a quick check; restore 10000 for final results.
# =========================================================

# Paths and output routines are included here; no project-specific module is used.
def project_folder():
    if "__file__" in globals():
        folder = Path(__file__).resolve().parent
        return folder.parent if folder.name.lower() == "code" else folder
    return Path.cwd()  # When pasted directly into a Jupyter cell

ROOT = project_folder()
SCRIPT = '04_monte_carlo_unit_root_inference'
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

# === Random-walk Dickey–Fuller test statistic ===
# Generate integrated series and estimate the empirical distribution of the DF statistic.

import numpy as np
import matplotlib.pyplot as plt
import statsmodels.tsa.stattools as ts
import seaborn as sns

T = 100  # sample size
replications = REPETITIONS  # number of Monte Carlo replications
df_statistics = []

np.random.seed(42)  

for _ in range(replications):
    y = np.random.normal(0, 1, T).cumsum()  
    result = ts.adfuller(y, maxlag=0, regression='c', autolag=None)
    df_statistics.append(result[0])  # store test statistic

plt.figure(figsize=(10, 6))
sns.histplot(df_statistics, kde=True, stat="density", bins=50, color='skyblue')
sns.kdeplot(df_statistics, color='red', linewidth=2)
plt.title("Distribution of Dickey-Fuller t-statistic")
plt.xlabel("x")
plt.ylabel("f(x)")
plt.grid(True)
plt.tight_layout()
save_plot()



# === Unit-root process with deterministic intercept and trend ===
# Estimate the statistic under a data-generating process with drift and trend.
export_table(pd.DataFrame({'percentile':[1,5,10,50,90,95,99],
                           'DF_statistic':np.percentile(df_statistics,[1,5,10,50,90,95,99])}),
             'mc_random_walk_df_percentiles')


import statsmodels.api as sm

T = 250
replications = REPETITIONS
a0 = 1.0
a2 = 0.65
t_stats = []
estimates = []

np.random.seed(0)

for _ in range(replications):
    y = np.zeros(T)
    y[0] = a0
    for t in range(1, T):
        y[t] = a0 + y[t - 1] + a2 * t + np.random.normal()

    dy = np.diff(y)
    y_lag = y[:-1]
    trend = np.arange(1, T)
    X = np.column_stack([np.ones(T - 1), y_lag, trend])
    model = sm.OLS(dy, X).fit()
    t_stats.append(model.tvalues[1])       
    estimates.append(model.params)        

plt.figure(figsize=(10, 6))
sns.histplot(t_stats, kde=True, stat='density', bins=50, color='steelblue')
plt.title("Monte Carlo Distribution of t-Statistic for H₀: γ = 0")
plt.xlabel("t-statistic value")
plt.ylabel("Density f(x)")
plt.grid(True)
plt.tight_layout()
save_plot()

print("Estimated coefficients (from final simulation):")
print(f"a₀: {estimates[-1][0]:.4f}, γ: {estimates[-1][1]:.4f}, a₂: {estimates[-1][2]:.4f}")

percentiles = [1, 5, 10, 90, 95, 99]
percentile_values = np.percentile(t_stats, percentiles)

print("\nSelected percentiles of the t-statistic for γ = 0:")
for p, v in zip(percentiles, percentile_values):
    print(f"{p}th percentile: {v:.4f}")


# Export the deterministic-trend t-statistic percentiles before resetting the simulation.
export_table(pd.DataFrame({'percentile':percentiles, 't_statistic':percentile_values}),
             'mc_deterministic_trend_percentiles')

# === Random walk estimated with deterministic terms ===
# Test how the statistic behaves when the estimating equation includes a trend
# but the data-generating process does not.
T = 250
replications = REPETITIONS
a0 = 0
a2 = 0
t_stats = []
estimates = []

np.random.seed(0)

for _ in range(replications):
    y = np.zeros(T)
    y[0] = a0
    for t in range(1, T):
        y[t] = a0 + y[t - 1] + a2 * t + np.random.normal()

    dy = np.diff(y)
    y_lag = y[:-1]
    trend = np.arange(1, T)
    X = np.column_stack([np.ones(T - 1), y_lag, trend])
    model = sm.OLS(dy, X).fit()
    t_stats.append(model.tvalues[1])       
    estimates.append(model.params)        

plt.figure(figsize=(10, 6))
sns.histplot(t_stats, kde=True, stat='density', bins=50, color='steelblue')
plt.title("Monte Carlo Distribution of t-Statistic for H₀: γ = 0")
plt.xlabel("x")
plt.ylabel("f(x)")
plt.grid(True)
plt.tight_layout()
save_plot()

print("Estimated coefficients (from final simulation):")
print(f"a₀: {estimates[-1][0]:.4f}, γ: {estimates[-1][1]:.4f}, a₂: {estimates[-1][2]:.4f}")

percentiles = [1, 5, 10, 90, 95, 99]
percentile_values = np.percentile(t_stats, percentiles)

print("\nSelected percentiles of the t-statistic for γ = 0:")
for p, v in zip(percentiles, percentile_values):
    print(f"{p}th percentile: {v:.4f}")


# Export the random-walk data-generating process scenario.
export_table(pd.DataFrame({'percentile':percentiles,
                           't_statistic':percentile_values}),
             'mc_random_walk_dgp_percentiles')
