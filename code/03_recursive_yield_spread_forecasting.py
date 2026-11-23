"""Recursive Forecasting of the U.S. Treasury Yield Spread.

Estimate AR(7) and ARMA(2,1) models and compare one-quarter-ahead forecasts from expanding estimation windows. Retains the original Granger-Newbold calculation and a paired t-test of absolute forecast errors.

Input workbook : quarterly.xlsx
Excel worksheet: QUARTERLY
Input variables: DATE, SPREAD
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
from scipy.stats import t, ttest_rel

# ===================== INPUT SETTINGS =====================
# Place the Excel file in the project data/ folder or next to this script.
# Alternatively set DATA_FILE to an absolute path such as:
# DATA_FILE = r"C:\Users\Salar\Desktop\Project\data\quarterly.xlsx"
DATA_FILE = 'quarterly.xlsx'
FORECAST_HORIZON = 60 
# =========================================================

def project_folder():
    if "__file__" in globals():
        folder = Path(__file__).resolve().parent
        return folder.parent if folder.name.lower() == "code" else folder
    return Path.cwd()  # When pasted directly into a Jupyter cell

ROOT = project_folder()
SCRIPT = '03_recursive_yield_spread_forecasting'
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

data = pd.read_excel(file_path, sheet_name="QUARTERLY")
data['DATE'] = pd.to_datetime(data['DATE'])
data.set_index('DATE', inplace=True)
spread = data['SPREAD'].dropna()

ar7_model = ARIMA(spread, order=(7, 0, 0)).fit()
print(" AR(7) Model Summary:")
print(ar7_model.summary())

arma21_model = ARIMA(spread, order=(2, 0, 1)).fit()
print("\n ARMA(2,1) Model Summary:")
print(arma21_model.summary())


# === Initial one-step-ahead forecast ===
# Train through 2009Q4 and predict the next quarter.


in_sample_data = spread[:'10/1/2009']
forecast_target = spread['1/1/2010':'4/1/2010']

ar7_fitted = ARIMA(in_sample_data, order=(7, 0, 0)).fit()
ar7_forecast = ar7_fitted.get_forecast(steps=1).predicted_mean.iloc[0]
ar7_actual = forecast_target.iloc[0]
ar7_error = ar7_actual - ar7_forecast
print(ar7_fitted.summary())

arma21_fitted = ARIMA(in_sample_data, order=(2, 0, 1)).fit()
arma21_forecast = arma21_fitted.get_forecast(steps=1).predicted_mean.iloc[0]
arma21_actual = forecast_target.iloc[0]
arma21_error = arma21_actual - arma21_forecast
print(arma21_fitted.summary())

print(" One-Step-Ahead Forecast for 2010Q1:\n")
print(f"AR(7) Forecast:          {ar7_forecast:.4f}")
print(f"AR(7) Forecast Error:    {ar7_error:.4f}\n")

print(f"ARMA(2,1) Forecast:      {arma21_forecast:.4f}")
print(f"ARMA(2,1) Forecast Error:{arma21_error:.4f}")
export_table(pd.DataFrame([{
    "Forecast quarter": "2010Q1",
    "Actual": float(ar7_actual),
    "AR(7) forecast": float(ar7_forecast),
    "AR(7) error": float(ar7_error),
    "ARMA(2,1) forecast": float(arma21_forecast),
    "ARMA(2,1) error": float(arma21_error),
}]), "initial_one_quarter_forecast")


# === Recursive expanding-window forecast evaluation ===
# Produce 60 one-step-ahead forecasts and regress realised values on forecasts.


spread = data['SPREAD'].dropna()
initial_estimation_end = '10/1/2009'
forecast_horizon = FORECAST_HORIZON
start_index = spread.index.get_loc(initial_estimation_end) + 1

def recursive_forecast_and_bias_test(series, model_order, model_name):
    forecast_values = []
    actual_values = []

    for i in range(forecast_horizon):
        end_idx = start_index + i - 1
        estimation_data = series.iloc[:end_idx + 1]

        if len(estimation_data) < 30:
            continue

        model = ARIMA(estimation_data, order=model_order).fit()
        forecast = model.get_forecast(steps=1).predicted_mean.iloc[0]
        actual = series.iloc[end_idx + 1]

        forecast_values.append(forecast)
        actual_values.append(actual)

    X = sm.add_constant(np.array(forecast_values))
    y = np.array(actual_values)
    reg_model = sm.OLS(y, X).fit()

    R = np.array([[1, 0], [0, 1]])
    q = np.array([0, 1])
    f_test = reg_model.wald_test((R, q), use_f=True)

    print(f"\n Results for {model_name}")
    print(reg_model.summary())
    export_model(reg_model, "forecast_bias_" + model_name.replace("(", "").replace(")", "").replace(",", "_"))
    print(f"F-statistic (H0: α=0, β=1): {float(f_test.fvalue):.4f}")
    print(f"p-value: {float(f_test.pvalue):.4f}")


recursive_forecast_and_bias_test(spread, (2, 0, 1), "ARMA(2,1)")

recursive_forecast_and_bias_test(spread, (7, 0, 0), "AR(7)")


# === Granger–Newbold-style comparison ===
# Define the original loss-comparison routine based on squared prediction errors.


from scipy.stats import t

def granger_newbold_test(errors_model1, errors_model2, alpha=0.05):

    x_i = errors_model1 + errors_model2
    z_i = errors_model1 - errors_model2
    r_xz = np.corrcoef(x_i, z_i)[0, 1]
    H = len(errors_model1)

    gn_t_stat = r_xz / np.sqrt((1 - r_xz**2) / (H - 1))

    p_value = 2 * (1 - t.cdf(abs(gn_t_stat), df=H-2))  # Two-tailed test

    mspe_model1 = np.mean(errors_model1**2)
    mspe_model2 = np.mean(errors_model2**2)

    print(f"\nGranger-Newbold Test Based on Slide Definition:")
    print(f"Sample correlation r_xz: {r_xz:.4f}")
    print(f"GN t-statistic: {gn_t_stat:.4f}")
    print(f"p-value: {p_value:.4f}")
    print(f"Critical t-value (α={alpha}): ±{t.ppf(1-alpha/2, df=H-2):.2f}")

    if r_xz > 0:
        print(" Model with higher MSPE: AR(7)")
    else:
        print("Model with higher MSPE: ARMA(2,1)")

    if p_value < alpha:
        print("Conclusion: Reject H₀ - Significant difference in accuracy")
    else:
        print("Conclusion: Fail to reject H₀ - No significant difference")

    print(f"\nMSPE Values:")
    print(f"AR(7): {mspe_model1:.4f}")
    print(f"ARMA(2,1): {mspe_model2:.4f}")

    return gn_t_stat, p_value

# Invocation moved below the creation of forecast errors.


# === Absolute-error forecast comparison ===
# Evaluate paired differences in absolute forecast errors; see methodology note.


from scipy.stats import ttest_rel
data = pd.read_excel(file_path, sheet_name="QUARTERLY")
data.columns = [col.lower() for col in data.columns]
spread = [col for col in data.columns if 'spread' in col][0]
data = data[['date', spread]].dropna()
data.columns = ['date', 'spread']
data['date'] = pd.to_datetime(data['date'])
data.set_index('date', inplace=True)
spread = data['spread']

initial_estimation_end = '10/1/2009'
forecast_horizon = FORECAST_HORIZON
start_index = spread.index.get_loc(initial_estimation_end) + 1

def recursive_forecast(series, model_order, maxiter=50):
    forecast_values = []
    actual_values = []
    for i in range(forecast_horizon):
        end_idx = start_index + i - 1
        estimation_data = series.iloc[:end_idx + 1]
        if len(estimation_data) < 30:
            continue
        try:
            model = ARIMA(estimation_data, order=model_order)
            fitted = model.fit(method_kwargs={"maxiter": maxiter})
            forecast = fitted.get_forecast(steps=1).predicted_mean.iloc[0]
            actual = series.iloc[end_idx + 1]
            forecast_values.append(forecast)
            actual_values.append(actual)
        except:
            continue
    return np.array(actual_values), np.array(forecast_values)

actuals_ar7, forecasts_ar7 = recursive_forecast(spread, (7, 0, 0))
actuals_arma, forecasts_arma = recursive_forecast(spread, (2, 0, 1))

errors_ar7 = actuals_ar7 - forecasts_ar7
errors_arma = actuals_arma - forecasts_arma

loss_ar7 = np.abs(errors_ar7)
loss_arma = np.abs(errors_arma)

dm_stat, dm_pvalue = ttest_rel(loss_ar7, loss_arma)

print("Paired t-test of absolute forecast errors (original calculation; not HAC-adjusted DM):")
print(f"Paired t-statistic: {dm_stat:.4f}")
print(f"p-value: {dm_pvalue:.4f}")

if loss_arma.mean() < loss_ar7.mean():
    print("→ ARMA(2,1) has lower MAE (better out-of-sample accuracy)")
else:
    print("→ AR(7) has lower MAE (better out-of-sample accuracy)")



# === Granger–Newbold comparison on the generated forecast errors ===
# Compute the forecast errors before applying the loss-comparison statistic.
if len(errors_ar7) == len(errors_arma) and len(errors_ar7) > 2:
    gn_t_stat, p_value = granger_newbold_test(errors_ar7, errors_arma)
else:
    print('GN comparison skipped: forecast error vectors have incompatible lengths.')

# This is a paired t-test of absolute errors, not a HAC-robust Diebold-Mariano test.
export_table(pd.DataFrame({
    'actual': actuals_ar7, 'AR7_forecast': forecasts_ar7,
    'ARMA21_forecast': forecasts_arma,
    'AR7_error': errors_ar7, 'ARMA21_error': errors_arma,
    'AR7_abs_error': loss_ar7, 'ARMA21_abs_error': loss_arma
}), 'recursive_forecast_results')
export_statistics({'AR7_MAE': float(loss_ar7.mean()), 'ARMA21_MAE': float(loss_arma.mean()),
                   'paired_t_on_absolute_loss': float(dm_stat), 'paired_t_p_value': float(dm_pvalue)},
                  'forecast_error_comparison')



# === Forecast Visualisation and Model Estimates ===
export_model(ar7_model, 'yield_spread_full_sample_AR7')
export_model(arma21_model, 'yield_spread_full_sample_ARMA21')
forecast_dates = spread.index[start_index:start_index+len(forecasts_ar7)]
plt.figure(figsize=(10, 5))
plt.plot(forecast_dates, actuals_ar7, label='Observed yield spread', linewidth=2)
plt.plot(forecast_dates, forecasts_ar7, label='AR(7) forecast', linestyle='--')
plt.plot(forecast_dates, forecasts_arma, label='ARMA(2,1) forecast', linestyle=':')
plt.title('Recursive One-Quarter-Ahead Forecasts: Treasury Yield Spread')
plt.xlabel('Quarter')
plt.ylabel('Percentage points')
plt.legend()
plt.tight_layout()
save_plot()
