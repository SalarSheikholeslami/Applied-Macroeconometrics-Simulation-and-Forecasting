"""Unit-root diagnostics for U.S. Treasury rates and their spread.

Requires data/quarterly.xlsx, described in data/README.md. The results can be
consistent with cointegration but are not a standalone formal cointegration test.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd
from statsmodels.tsa.stattools import adfuller, acf


def load_rates(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. See data/README.md")
    df = pd.read_excel(path, sheet_name="QUARTERLY")
    df.columns = df.columns.str.strip().str.upper()
    if "R10" not in df or "TB3MS" not in df:
        raise ValueError("Expected columns R10 and TB3MS in QUARTERLY sheet")
    df["R10"] = pd.to_numeric(df["R10"], errors="coerce")
    df["TB3MS"] = pd.to_numeric(df["TB3MS"], errors="coerce")
    df["SPREAD"] = df["R10"] - df["TB3MS"]
    return df[["R10", "TB3MS", "SPREAD"]].dropna()


def adf_report(series: pd.Series, lags: int = 8) -> None:
    statistic, pvalue, usedlag, obs, critical, *_ = adfuller(
        series, maxlag=lags, autolag=None, regression="c"
    )
    print(f"{series.name}: ADF({usedlag}), n={obs}")
    print(f"  statistic={statistic:.3f}, MacKinnon p={pvalue:.4f}, critical values={critical}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[1] / "data/quarterly.xlsx")
    args = parser.parse_args()
    rates = load_rates(args.data)
    print("First 12 ACF values, spread:", acf(rates["SPREAD"], nlags=12)[1:].round(3))
    for col in ["R10", "TB3MS", "SPREAD"]:
        adf_report(rates[col], lags=8)
    print("Sensitivity: 3-month rate with five lags")
    adf_report(rates["TB3MS"], lags=5)
    print("Interpret stationarity evidence cautiously: lag choice and sample matter.")


if __name__ == "__main__":
    main()
