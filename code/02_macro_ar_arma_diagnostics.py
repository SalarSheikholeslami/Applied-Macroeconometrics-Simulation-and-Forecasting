"""Autoregressive and ARMA diagnostics for U.S. macroeconomic series.

Based on the applied exercises in Financial and Macroeconometrics, JKU, 2025.
Requires data/quarterly.xlsx with DATE, INDPRO, UNRATE and FINISHED.
This is a cleaned analytic reproduction, not a verbatim assignment submission.
"""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import acf, pacf

ROOT = Path(__file__).resolve().parents[1]


def read_series(filename: Path) -> pd.DataFrame:
    if not filename.exists():
        raise FileNotFoundError(f"Missing {filename}; see data/README.md")
    df = pd.read_excel(filename, sheet_name="QUARTERLY")
    df.columns = df.columns.str.strip().str.upper()
    required = {"INDPRO", "UNRATE", "FINISHED"}
    if not required.issubset(df.columns):
        raise ValueError(f"Required columns absent: {sorted(required - set(df.columns))}")
    for name in required: df[name] = pd.to_numeric(df[name], errors="coerce")
    return df


def diagnostic(name: str, values: pd.Series, orders: list[tuple[int, int, int]]) -> None:
    y = values.dropna().astype(float).reset_index(drop=True)
    print(f"\n{name}: n={len(y)}")
    if len(y)<30: raise ValueError(f"Too few observations for {name}")
    for order in orders:
        fit = ARIMA(y, order=order, trend="c").fit()
        residual_tests = acorr_ljungbox(fit.resid, lags=[4, 8, 12], return_df=True)
        print(f"  ARIMA{order}: AIC={fit.aic:.2f}, BIC={fit.bic:.2f}")
        print(f"  coefficients: {fit.params.round(4).to_dict()}")
        print(f"  Ljung–Box p-values: {residual_tests.lb_pvalue.round(4).to_dict()}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT/"data/quarterly.xlsx")
    args=parser.parse_args()
    df=read_series(args.data)
    for name in ["INDPRO", "FINISHED"]:
        if (df[name].dropna() <= 0).any(): raise ValueError(f"{name} must be positive for log-growth rates")
    indpro_growth = np.log(df["INDPRO"]).diff()
    finished_growth = np.log(df["FINISHED"]).diff()
    print("U.S. unemployment levels: first three sample ACF coefficients:",
          np.round(acf(df["UNRATE"].dropna(), nlags=3)[1:], 3))
    print("U.S. unemployment levels: first three sample PACF coefficients:",
          np.round(pacf(df["UNRATE"].dropna(), nlags=3)[1:], 3))
    diagnostic("Industrial production log-growth", indpro_growth, [(1,0,0)])
    diagnostic("Unemployment rate (level)", df["UNRATE"], [(2,0,0)])
    diagnostic("Finished-goods PPI log-growth", finished_growth, [(1,0,1),(3,0,0)])
    print("Note: AIC/BIC summarize in-sample fit; forecast superiority requires held-out evaluation.")

if __name__ == "__main__": main()
