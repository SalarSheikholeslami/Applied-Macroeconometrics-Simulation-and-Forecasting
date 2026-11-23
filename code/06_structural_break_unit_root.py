"""Unit Roots and a Known Structural Break.

Visualise a simulated series with a break at observation 51 and examine DF regressions, break-adjusted detrending, and serial correlation.

Input workbook : ybreak.xlsx
Excel worksheet: Break
Input variables: Y
Original input location: C:/Users/Salar/Desktop/ybreak.xlsx

Run as a standalone .py file or paste into a Jupyter notebook.
Outputs are written automatically to Applied_Macroeconometric/figures and /tables.
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
# DATA_FILE = r"C:\Users\Salar\Desktop\Project\data\ybreak.xlsx"
DATA_FILE = 'ybreak.xlsx'

# =========================================================

# Paths and output routines are included here; no project-specific module is used.
def project_folder():
    if "__file__" in globals():
        folder = Path(__file__).resolve().parent
        return folder.parent if folder.name.lower() == "code" else folder
    return Path.cwd()  # When pasted directly into a Jupyter cell

ROOT = project_folder()
SCRIPT = '06_structural_break_unit_root'
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

file_path = find_data(DATA_FILE)
df = pd.read_excel(file_path)

plt.figure(figsize=(10, 5))
plt.plot(df['Y'], label='Y series')
plt.axvline(x=50, color='red', linestyle='--', label='Structural Break at t=51')
plt.title("Simulated Time Series with Structural Break at t = 51")
plt.xlabel("Time")
plt.ylabel("Y")
plt.grid(True)
plt.legend()
plt.tight_layout()
save_plot()


# === Time-series profile and break location ===
# Visualise the series and its known break at observation 51.


from statsmodels.graphics.tsaplots import plot_pacf, plot_acf
import matplotlib.pyplot as plt
import pandas as pd

y = df['Y'].dropna()
dy = y.diff().dropna()

acf_vals = acf(y, nlags=20, fft=False)

plt.figure(figsize=(8, 4))
plt.stem(range(len(acf_vals)), acf_vals, basefmt=" ")
plt.title("ACF of Y ")
plt.xlabel("Lag")
plt.ylabel("ACF")
plt.grid(True)
plt.tight_layout()
save_plot()

plt.figure(figsize=(8, 4))
plot_pacf(y, lags=20)
plt.title("PACF of Y ")
plt.tight_layout()
save_plot()

fig, axes = plt.subplots(2, 1, figsize=(10, 6))
plot_acf(dy, ax=axes[0], lags=20, title="ACF of ΔY (First Difference)")
plot_pacf(dy, ax=axes[1], lags=20, title="PACF of ΔY (First Difference)")
plt.tight_layout()
save_plot()


# === Autocorrelation before and after differencing ===
# Inspect ACF and PACF of the series and its first difference.


y_diff = y.diff().dropna()
yt_1 = y.shift(1).dropna()
trend = pd.Series(range(1, len(y) + 1), index=y.index)
trend = trend[y_diff.index]

X = pd.concat([trend, yt_1], axis=1).dropna()
X.columns = ['time', 'yt_1']
X = sm.add_constant(X)
y_diff = y_diff.loc[X.index]

model = sm.OLS(y_diff, X).fit()
print("\n=== OLS Regression Summary (DF with constant + trend) ===")
print(model.summary())

adf_result = adfuller(y, maxlag=0, regression='ct', autolag=None)

print("ADF Test Statistic:", round(adf_result[0], 4))
print("p-value:", round(adf_result[1], 4))
print("Dickey-Fuller Critical Values:")
for key, value in adf_result[4].items():
    print(f"  {key}: {round(value, 4)}")


# === Dickey–Fuller regression with linear trend ===
# Estimate the original standard specification that omits the break.


import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import acf, pacf, adfuller
import matplotlib.pyplot as plt

y = df['Y'].dropna()
T = len(y)

time = np.arange(1, T + 1)
DL = np.where(time >= 51, 1, 0)

X_alt = sm.add_constant(np.column_stack((time, DL)))
model_alt = sm.OLS(y, X_alt).fit()
residuals = model_alt.resid

yt_hat_lag = residuals.shift(1).dropna()
dyt_hat = residuals.diff().dropna()
yt_hat_lag = yt_hat_lag.loc[dyt_hat.index]
X_df = sm.add_constant(yt_hat_lag)
model_df = sm.OLS(dyt_hat, X_df).fit()
print(model_df.summary())

t_statistic = round(model_df.tvalues.iloc[1], 4)
print(f"\nADF-type t-statistic for H₀: a₁ = 1 → {t_statistic}")

perron_crit_values = { '1%': -4.90, '5%': -4.28, '10%': -3.96}

print("\n=== Perron (1989) Critical Values (λ = 0.5, T = 100, Intercept Shift) ===")
for level, value in perron_crit_values.items():
    print(f"  {level}: {value}")

print("\n→ Decision Summary:")

coef_summary = pd.DataFrame({ 'Coefficient': model_df.params, 'T-Statistic': model_df.tvalues,'P-Value': model_df.pvalues})
print("\n=== Coefficient Summary ===")
print(coef_summary)

plt.figure(figsize=(10, 4))
plt.stem(acf(model_df.resid, nlags=10))
plt.title("ACF of Residuals")
plt.xlabel("Lag")
plt.ylabel("ACF")
plt.grid(True)
plt.tight_layout()
save_plot()

plt.figure(figsize=(10, 4))
plt.stem(pacf(model_df.resid, nlags=10))
plt.title("PACF of Residuals")
plt.xlabel("Lag")
plt.ylabel("PACF")
plt.grid(True)
plt.tight_layout()
save_plot()

k = 3
dy_lags = pd.concat([dyt_hat.shift(i) for i in range(1, k + 1)], axis=1)
dy_lags.columns = [f'dy_lag{i}' for i in range(1, k + 1)]

X_aug = pd.concat([yt_hat_lag, dy_lags], axis=1).dropna()
X_aug = sm.add_constant(X_aug)
y_aug = dyt_hat.loc[X_aug.index]

model_aug = sm.OLS(y_aug, X_aug).fit()
print("\n=== Augmented Regression for Serial Correlation Check ===")
print(model_aug.summary())


# === Export break-adjusted regression output ===
export_model(model_alt, 'structural_break_detrending')
export_model(model_df, 'structural_break_residual_df')
export_model(model_aug, 'structural_break_augmented_diagnostics')

