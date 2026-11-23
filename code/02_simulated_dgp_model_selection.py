"""Autoregressive Model Identification for a Simulated Series.

Use sample ACF/PACF and fitted AR(2), AR(3), and ARMA(2,1) models to evaluate the dynamics of a stationary simulated time series.

Input workbook : unknown.xlsx
Excel worksheet: data
Input variables: One numeric series (yt)
Original input location: C:/Users/Salar/Desktop/unknown.xlsx

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
# DATA_FILE = r"C:\Users\Salar\Desktop\Project\data\unknown.xlsx"
DATA_FILE = 'unknown.xlsx'

# =========================================================

# Paths and output routines are included here; no project-specific module is used.
def project_folder():
    if "__file__" in globals():
        folder = Path(__file__).resolve().parent
        return folder.parent if folder.name.lower() == "code" else folder
    return Path.cwd()  # When pasted directly into a Jupyter cell

ROOT = project_folder()
SCRIPT = '02_simulated_dgp_model_selection'
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
import numpy as np
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

file_path1 = find_data(DATA_FILE)
data1 = pd.read_excel(file_path1, sheet_name="data", header=None)
data1.columns = ['yt']

plt.figure(figsize=(10, 4))
plot_acf(data1['yt'], lags=12)
plt.title("ACF of the series")
plt.tight_layout()
save_plot()

plt.figure(figsize=(10, 4))
plot_pacf(data1['yt'], lags=12, method='ywm')
plt.title("PACF of the series")
plt.tight_layout()
save_plot()


# === Simulated series: candidate models ===
# Estimate AR(2), AR(3), and ARMA(2,1) with the original model specifications.


import warnings
warnings.filterwarnings("ignore")
data1.columns = ['yt']
yt = data1['yt']

def model_summary(model_result, model_name):
    print(f"\n {model_name} Model:")
    print("Coefficient Estimates:")
    print(model_result.params)
    print("\nT-statistics:")
    print(model_result.tvalues)
    print("\nP-values:")
    print(model_result.pvalues)

ar2_model = ARIMA(yt, order=(2, 0, 0)).fit()
model_summary(ar2_model, "AR(2)")

ar3_model = ARIMA(yt, order=(3, 0, 0)).fit()
model_summary(ar3_model, "AR(3)")

arma21_model = ARIMA(yt, order=(2, 0, 1)).fit()
model_summary(arma21_model, "ARMA(2,1)")


print(" AR(2) Model Summary:")
print(ar2_model.summary())

print("\n AR(3) Model Summary:")
print(ar3_model.summary())

print("\n ARMA(2,1) Model Summary:")
print(arma21_model.summary())


# === Simulated series: residual diagnostics ===
# Evaluate the remaining serial correlation of alternative fitted models.


data1.columns = ['yt']
yt = data1['yt']

def residual_diagnostics(model_result, model_name):
    resid = model_result.resid
    plt.figure(figsize=(8, 4))
    plot_acf(resid, lags=8)
    plot_acf(resid, lags=12)
    plt.title(f"Residual ACF - {model_name}")
    plt.tight_layout()
    save_plot()

    print(f"\n Ljung-Box Q-statistics for {model_name} residuals:")
    ljung_box_result = acorr_ljungbox(resid, lags=[8, 12], return_df=True)
    print(ljung_box_result.round(4))
    export_table(ljung_box_result, "residual_ljung_box_" + model_name.replace("(", "").replace(")", "").replace(",", "_"))

ar2_model = ARIMA(yt, order=(2, 0, 0)).fit()
ar3_model = ARIMA(yt, order=(3, 0, 0)).fit()
arma21_model = ARIMA(yt, order=(2, 0, 1)).fit()

residual_diagnostics(ar2_model, "AR(2)")
residual_diagnostics(ar3_model, "AR(3)")
residual_diagnostics(arma21_model, "ARMA(2,1)")


# === Simulated series: information criteria ===
# Compare AIC and BIC of candidate models estimated on the same sample.


data1.columns = ['yt']
yt = data1['yt'].dropna()

ar2_model = ARIMA(yt, order=(2, 0, 0)).fit()
ar3_model = ARIMA(yt, order=(3, 0, 0)).fit()
arma21_model = ARIMA(yt, order=(2, 0, 1)).fit()

print("\n AIC and SIC (BIC) Comparison:")
print(f"AR(2):     AIC = {ar2_model.aic:.2f}, BIC = {ar2_model.bic:.2f}")
print(f"AR(3):     AIC = {ar3_model.aic:.2f}, BIC = {ar3_model.bic:.2f}")
print(f"ARMA(2,1): AIC = {arma21_model.aic:.2f}, BIC = {arma21_model.bic:.2f}")


# === Model identification summary ===
# Interpret the evidence from the correlograms, model fit, and residual tests.



# === Model comparison tables ===
for label, fitted in [('AR2', ar2_model), ('AR3', ar3_model), ('ARMA21', arma21_model)]:
    export_model(fitted, 'simulated_series_'+label)
export_table(pd.DataFrame({'Model': ['AR(2)', 'AR(3)', 'ARMA(2,1)'],
                           'AIC':[ar2_model.aic, ar3_model.aic, arma21_model.aic],
                           'BIC':[ar2_model.bic, ar3_model.bic, arma21_model.bic]}),
             'simulated_series_model_selection')

