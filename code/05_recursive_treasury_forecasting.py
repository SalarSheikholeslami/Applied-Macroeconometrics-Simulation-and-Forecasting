"""Recursive one-step-ahead U.S. Treasury yield-spread forecasts.

Compare AR(7) and ARMA(2,1) models on the same 60-quarter evaluation sample.
Requires data/quarterly.xlsx. See README for data setup and limitations.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA


def load_spread(path: Path) -> pd.Series:
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. See data/README.md")
    df = pd.read_excel(path, sheet_name="QUARTERLY")
    df.columns = df.columns.str.strip().str.upper()
    if "DATE" not in df:
        raise ValueError("Expected DATE column in QUARTERLY worksheet")
    if "SPREAD" in df:
        spread = pd.to_numeric(df["SPREAD"], errors="coerce")
    elif {"R10", "TB3MS"} <= set(df.columns):
        spread = pd.to_numeric(df["R10"], errors="coerce") - pd.to_numeric(df["TB3MS"], errors="coerce")
    else:
        raise ValueError("Expected SPREAD, or both R10 and TB3MS, in the dataset")
    # Convert timestamps to quarterly periods to avoid ambiguities between
    # quarter-start and quarter-end date conventions.
    periods = pd.to_datetime(df["DATE"]).dt.to_period("Q")
    series = pd.Series(spread.to_numpy(), index=pd.PeriodIndex(periods, freq="Q"), name="spread")
    series = series.dropna().sort_index()
    if series.index.has_duplicates:
        raise ValueError("Quarterly dates contain duplicates")
    expected = pd.period_range(series.index.min(), series.index.max(), freq="Q")
    if not series.index.equals(expected):
        raise ValueError("Quarterly spread has missing periods; prepare a continuous sample before forecasting")
    return series


def rolling_forecasts(series: pd.Series, order: tuple[int, int, int],
                      start: str, horizon: int) -> pd.DataFrame:
    first = pd.Period(start, freq="Q")
    positions = np.flatnonzero(series.index >= first)
    if not len(positions):
        raise ValueError(f"No observations from {start}")
    start_idx = int(positions[0])
    end_idx = start_idx + horizon
    if end_idx > len(series):
        raise ValueError(f"Need {horizon} post-{start} quarters, found {len(series) - start_idx}")
    rows = []
    for idx in range(start_idx, end_idx):
        # The forecast for time idx is estimated using observations through idx-1.
        train = pd.Series(series.iloc[:idx].to_numpy(), dtype=float)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            fitted = ARIMA(train, order=order, trend="c").fit()
        pred = float(fitted.forecast(steps=1).iloc[0])
        actual = float(series.iloc[idx])
        rows.append((str(series.index[idx]), actual, pred, actual - pred))
    return pd.DataFrame(rows, columns=["quarter", "actual", "forecast", "error"])


def report(name: str, forecast: pd.DataFrame) -> None:
    err = forecast["error"].to_numpy()
    print(f"\n{name}: n={len(err)}, MAE={np.mean(np.abs(err)):.4f}, RMSE={np.sqrt(np.mean(err**2)):.4f}")
    # Forecast-unbiasedness regression; two-sided joint F test of a=0, b=1.
    if len(err) < 5:
        print("  Forecast-unbiasedness F-test skipped: fewer than 5 forecasts")
        return
    x = sm.add_constant(forecast["forecast"].to_numpy())
    fitted = sm.OLS(forecast["actual"].to_numpy(), x).fit()
    test = fitted.f_test((np.eye(2), np.array([0.0, 1.0])))
    print(f"  Forecast unbiasedness: F={float(test.fvalue):.4f}, p={float(test.pvalue):.4f}")


def compare_accuracy(ar: pd.DataFrame, arma: pd.DataFrame) -> None:
    if not ar["quarter"].equals(arma["quarter"]):
        raise ValueError("Forecast evaluation samples do not match")
    # HAC-robust mean-loss-difference test. This supersedes the simple paired
    # t-test in the author's initial coursework implementation and should not
    # be misrepresented as a fully validated small-sample DM procedure.
    difference = np.abs(ar["error"].to_numpy()) - np.abs(arma["error"].to_numpy())
    if len(difference) < 5:
        print("  Accuracy comparison skipped: fewer than 5 forecasts")
        return
    maxlags = min(4, len(difference) - 1)
    fit = sm.OLS(difference, np.ones((len(difference), 1))).fit(
        cov_type="HAC", cov_kwds={"maxlags": maxlags}
    )
    print("\nHAC-robust test of mean absolute forecast-loss difference (AR - ARMA):")
    print(f"  mean difference={difference.mean():.5f}, t={fit.tvalues[0]:.3f}, p={fit.pvalues[0]:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[1] / "data/quarterly.xlsx")
    parser.add_argument("--start", default="2010Q1")
    parser.add_argument("--horizon", type=int, default=60)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "results")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    series = load_spread(args.data)
    ar = rolling_forecasts(series, (7, 0, 0), args.start, args.horizon)
    arma = rolling_forecasts(series, (2, 0, 1), args.start, args.horizon)
    report("AR(7)", ar)
    report("ARMA(2,1)", arma)
    compare_accuracy(ar, arma)
    out = ar[["quarter", "actual"]].copy()
    out["AR7"] = ar["forecast"].to_numpy()
    out["ARMA21"] = arma["forecast"].to_numpy()
    out.to_csv(args.output / "recursive_forecasts.csv", index=False)
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(out["quarter"], out["actual"], label="Actual")
    ax.plot(out["quarter"], out["AR7"], label="AR(7)")
    ax.plot(out["quarter"], out["ARMA21"], label="ARMA(2,1)")
    ax.set(title="U.S. Treasury yield spread: recursive one-step forecasts", ylabel="Percentage points")
    ax.set_xticks(np.arange(0, len(out), max(1, len(out)//8)))
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.output / "recursive_forecasts.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
