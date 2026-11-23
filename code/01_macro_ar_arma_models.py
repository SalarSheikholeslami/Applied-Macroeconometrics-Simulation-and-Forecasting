"""AR and ARMA Dynamics in U.S. Macroeconomic Series.

Industrial production log changes, unemployment persistence, and log changes in FINISHED. The original AR(1), AR(2), ARMA(1,1), and AR(3) specifications are compared through residual and information-criterion diagnostics.

Input workbook : quarterly.xlsx
Excel worksheet: QUARTERLY
Input variables: DATE, INDPRO, UNRATE, FINISHED
Original input location: C:/Users/Salar/Desktop/quarterly.xlsx

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
# DATA_FILE = r"C:\Users\Salar\Desktop\Project\data\quarterly.xlsx"
DATA_FILE = 'quarterly.xlsx'

# =========================================================

# Paths and output routines are included here; no project-specific module is used.
def project_folder():
    if "__file__" in globals():
        folder = Path(__file__).resolve().parent
        return folder.parent if folder.name.lower() == "code" else folder
    return Path.cwd()  # When pasted directly into a Jupyter cell

ROOT = project_folder()
SCRIPT = '01_macro_ar_arma_models'
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
file_path = find_data(DATA_FILE)
data = pd.read_excel(file_path, sheet_name="QUARTERLY")



# === Industrial production growth ===
# Construct log differences of the U.S. industrial production index.


data.set_index('DATE', inplace=True)

data['growth_indprod'] = np.log(data['INDPRO']).diff()

print(data[['INDPRO', 'growth_indprod']].head(10))



# === Industrial production: AR(1) ===
# Estimate the autoregressive persistence of industrial production growth.


import statsmodels.api as sm
data['yt_1'] = data['growth_indprod'].shift(1)

regression_data = data[['growth_indprod', 'yt_1']].dropna()

Y = regression_data['growth_indprod']
X = sm.add_constant(regression_data['yt_1'])

model = sm.OLS(Y, X).fit()

print(model.summary())
export_model(model, "industrial_production_AR1")



# === Industrial production: residual diagnostics ===
# Inspect residual autocorrelation using sample ACF and Ljung–Box Q-statistics.


from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.stats.diagnostic import acorr_ljungbox
import matplotlib.pyplot as plt
residuals = model.resid

plt.figure(figsize=(8, 4))
plot_acf(residuals, lags=20)
plt.title("ACF of Residuals from AR(1) Model")
save_plot()

ljung_box = acorr_ljungbox(residuals, lags=[4, 8, 12], return_df=True)
print("Ljung-Box Q-statistics:")
print(ljung_box)
export_table(ljung_box, "industrial_production_AR1_ljung_box")


# === Unemployment dynamics: correlograms ===
# Plot ACF and PACF for unemployment in levels.


from statsmodels.graphics.tsaplots import plot_acf, plot_pacf


unrate = data['UNRATE'].dropna()

plt.figure(figsize=(10, 4))
plot_acf(unrate, lags=12)
plt.title("ACF of UNRATE (Level)")
save_plot()

plt.figure(figsize=(10, 4))
plot_pacf(unrate, lags=12, method='ols')  
plt.title("PACF of UNRATE ")
save_plot()


# === Unemployment dynamics: AR(2) ===
# Estimate an AR(2) model and inspect the summed persistence parameters.


data['lag1'] = data['UNRATE'].shift(1)
data['lag2'] = data['UNRATE'].shift(2)

df = data[['UNRATE', 'lag1', 'lag2']].dropna()

X = sm.add_constant(df[['lag1', 'lag2']])
y = df['UNRATE']
model = sm.OLS(y, X).fit()

print(model.summary())
print("\nSum of coefficients (lag1 + lag2):", round(model.params['lag1'] + model.params['lag2'], 4))
export_model(model, "unemployment_AR2")


# === FINISHED Index: Log-Difference Transformation ===
# Calculate quarterly log changes of the FINISHED index.


data['growth_finished'] = np.log(data['FINISHED']).diff()
print(data[['FINISHED', 'growth_finished']].head(10))



# === FINISHED Index: ARMA(1,1) Model ===
# Estimate the ARMA specification and test residual autocorrelation.


from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_acf


data.index = pd.date_range(start=data.index[0], periods=len(data), freq='QE-DEC')
data['growth_finished'] = np.log(data['FINISHED']).diff()
growth = data['growth_finished'].dropna()

model = ARIMA(growth, order=(1, 0, 1))
result = model.fit()
print(result.summary())
export_model(result, "finished_goods_ARMA11")
resid = result.resid

plot_acf(resid, lags=12)
plt.title("ACF of ARMA(1,1) Residuals")
plt.tight_layout()
save_plot()

ljung = acorr_ljungbox(resid, lags=[4, 8, 12], return_df=True)
print("\nLjung-Box Q-statistics:")
print(ljung)


# === FINISHED Index: AR(3) versus ARMA(1,1) ===
# Compare residual diagnostics and AIC/BIC across AR and ARMA models.


data['growth_finished'] = np.log(data['FINISHED']).diff()
growth = data['growth_finished'].dropna()

ar3_model = ARIMA(growth, order=(3, 0, 0)).fit()
print(" AR(3) Model Summary:")
print(ar3_model.summary())

resid_ar3 = ar3_model.resid
ljung_ar3 = acorr_ljungbox(resid_ar3, lags=[4, 8, 12], return_df=True)
print("Ljung-Box Q-statistics for AR(3):")
print(ljung_ar3)

arma11_model = ARIMA(growth, order=(1, 0, 1)).fit()

print("\n AIC and BIC (SIC) Comparison:")
print(f"AR(3)     AIC: {ar3_model.aic:.2f}, BIC: {ar3_model.bic:.2f}")
print(f"ARMA(1,1) AIC: {arma11_model.aic:.2f}, BIC: {arma11_model.bic:.2f}")
plot_acf(resid_ar3, lags=20)
plt.title("ACF of AR(3) Residuals")
plt.tight_layout()
save_plot()


# === Model Diagnostics and Information Criteria ===
export_model(ar3_model, 'finished_goods_AR3')
export_table(pd.DataFrame({'Model':['AR(3)','ARMA(1,1)'],
                           'AIC':[ar3_model.aic, arma11_model.aic],
                           'BIC':[ar3_model.bic, arma11_model.bic]}), 'finished_goods_information_criteria')
export_table(ljung, 'finished_goods_ARMA11_ljung_box')
export_table(ljung_ar3, 'finished_goods_AR3_ljung_box')

