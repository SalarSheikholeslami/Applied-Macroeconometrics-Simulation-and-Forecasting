"""Real GDP Trend Decomposition and Structural Change.

Evaluate real GDP with the original break-adjusted trend regression, HP filter, and a piecewise linear deterministic trend.

Input workbook : rgdp.xlsx
Excel worksheet: RGDP
Input variables: First date column; RGDP
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
# DATA_FILE = r"C:\Users\Salar\Desktop\Project\data\rgdp.xlsx"
DATA_FILE = 'rgdp.xlsx'
# =========================================================
def project_folder():
    if "__file__" in globals():
        folder = Path(__file__).resolve().parent
        return folder.parent if folder.name.lower() == "code" else folder
    return Path.cwd()  # When pasted directly into a Jupyter cell

ROOT = project_folder()
SCRIPT = '07_real_gdp_trend_decomposition'
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

import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import acf, pacf
file_path = find_data(DATA_FILE)
df = pd.read_excel(file_path)
gdp = df.select_dtypes(include=[np.number]).iloc[:, 0].dropna()
T = len(gdp)

break_index = 107
time = np.arange(1, T + 1)
DL = np.where(time > break_index, 1, 0)

X_alt = sm.add_constant(np.column_stack((time, DL)))
model_alt = sm.OLS(gdp.values, X_alt).fit()
residuals = model_alt.resid

yt_hat_lag = pd.Series(residuals).shift(1).dropna()
dyt_hat = pd.Series(residuals).diff().dropna()
yt_hat_lag = yt_hat_lag.loc[dyt_hat.index]
X_df = sm.add_constant(yt_hat_lag)
model_df = sm.OLS(dyt_hat, X_df).fit()
print(model_df.summary())

print("\n=== Perron (1989) Critical Values (λ = 0.5, Intercept Shift) ===")
perron_crit_values = {'1%': -4.90, '5%': -4.28, '10%': -3.96}
for level, val in perron_crit_values.items():
    print(f"{level} : {val}")


# === Real GDP: break-adjusted unit-root diagnostics ===
# Use the original detrending specification at the presumed break date.


from statsmodels.tsa.filters.hp_filter import hpfilter

gdp = df.select_dtypes(include=[np.number]).iloc[:, 0].dropna()
dates = pd.to_datetime(df.iloc[:, 0])
gdp.index = dates[:len(gdp)]
gdp_cycle, gdp_trend = hpfilter(gdp, lamb=1600)

trend_values = gdp_trend.values.astype(float)
cycle_values = gdp_cycle.values.astype(float)
reconstructed_values = trend_values + cycle_values
date_index = gdp_trend.index.to_numpy()

break_date = pd.Timestamp("1973-06-30")

plt.figure(figsize=(12, 5))
plt.plot(date_index, trend_values, label="Trend Component", color="green")
plt.plot(date_index, reconstructed_values, label="GDP (Trend + Cycle)", color="black", alpha=0.6)
plt.fill_between(date_index, reconstructed_values, trend_values, color="blue", alpha=0.3, label="Cycle Deviation")
plt.axvline(x=break_date, color='red', linestyle='--', label="Structural Break (1973Q2)")
plt.title("Real GDP with HP Trend and Cyclical Deviations (λ = 1600)")
plt.xlabel("Date")
plt.ylabel("GDP Level")
plt.legend()
plt.grid(True)
plt.tight_layout()
save_plot()

plt.figure(figsize=(12, 5))
plt.plot(gdp_cycle, label="Transitory Component (Cycle)", color="blue")
plt.axhline(0, linestyle="--", color="black", linewidth=0.7)
plt.axvline(x=break_date, color='red', linestyle='--', label="Structural Break (1973Q2)")
plt.title("Transitory Component of Real GDP (HP Filter, λ = 1600)")
plt.xlabel("Date")
plt.ylabel("Deviation from Trend")
plt.grid(True)
plt.legend()
plt.tight_layout()
save_plot()



# === Real GDP: HP-filter decomposition ===
# Separate real GDP into smooth trend and cyclical deviations using lambda=1600.


# === Real GDP: piecewise linear trend ===
# Compare residuals from the broken deterministic trend with the HP cycle.


break_index = 107  
T = len(gdp)
time = np.arange(1, T + 1)
DT = np.where(time > break_index, time - break_index, 0)  # slope change after break

X_break = np.column_stack([np.ones(T), time, DT])
model_break = sm.OLS(gdp.values, X_break).fit()
trend_fitted = model_break.fittedvalues
transitory_break = gdp.values - trend_fitted
break_date = gdp.index[break_index]

plt.figure(figsize=(12, 5))
plt.plot(gdp.index, gdp_cycle, label="HP Filter Cycle", color="blue")
plt.plot(gdp.index, transitory_break, label="Piecewise Linear Trend", color="orange")
plt.axvline(x=break_date, color='red', linestyle='--', label="Structural Break (1973Q3)")
plt.axhline(0, linestyle="--", color="black", linewidth=0.7)
plt.title("Comparison of Transitory Components: HP Filter vs Trend Break Model")
plt.xlabel("Date")
plt.ylabel("Deviation from Trend")
plt.legend()
plt.grid(True)
plt.tight_layout()
save_plot()


# === Export GDP trend decomposition and original fitted models ===
export_model(model_alt, 'gdp_intercept_shift_trend_model')
export_model(model_df, 'gdp_residual_df_regression')
export_model(model_break, 'gdp_piecewise_linear_trend')
export_table(pd.DataFrame({'Date':gdp.index.astype(str), 'Real_GDP':gdp.values,
                           'HP_Trend':gdp_trend.values, 'HP_Cycle':gdp_cycle.values,
                           'Piecewise_Trend':trend_fitted,
                           'Piecewise_Residual':transitory_break}), 'gdp_trend_components')

