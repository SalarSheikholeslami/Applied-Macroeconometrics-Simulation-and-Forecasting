"""Compare U.S. real GDP trends with and without a pre-specified 1973 break.

This is a descriptive trend-and-cycle comparison, NOT a fully implemented
Perron (1989) unit-root test. Requires data/rgdp.xlsx.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.filters.hp_filter import hpfilter


def read_gdp(path: Path) -> pd.Series:
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}; see data/README.md")
    frame = pd.read_excel(path)
    frame.columns = frame.columns.str.strip().str.upper()
    numeric_cols = [c for c in frame.columns if c not in {"DATE", "QUARTER"}
                    and pd.api.types.is_numeric_dtype(frame[c])]
    if not numeric_cols:
        raise ValueError("Input needs at least one numeric real-GDP column")
    value = frame[numeric_cols[0]].dropna().astype(float)
    if "DATE" in frame:
        dates = pd.to_datetime(frame.loc[value.index, "DATE"])
        return pd.Series(value.to_numpy(), index=pd.PeriodIndex(dates.dt.to_period("Q")), name="real_gdp")
    # If no date column exists, label observations by sequence. The known
    # mid-1973 position then needs explicit confirmation for this dataset.
    raise ValueError("Input needs a DATE column for a defensible 1973 break specification")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[1] / "data/rgdp.xlsx")
    parser.add_argument("--break-quarter", default="1973Q2")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "results")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    series = read_gdp(args.data)
    t = np.arange(len(series), dtype=float)
    period = pd.Period(args.break_quarter, freq="Q")
    after = np.maximum(0.0, t - np.flatnonzero(series.index >= period)[0])
    x = sm.add_constant(np.column_stack((t, after)))
    fitted = sm.OLS(series.to_numpy(), x).fit()
    break_trend = fitted.fittedvalues
    hp_cycle, hp_trend = hpfilter(series, lamb=1600)
    output = pd.DataFrame({
        "quarter": series.index.astype(str),
        "gdp": series.to_numpy(),
        "hp_cycle": hp_cycle.to_numpy(),
        "piecewise_trend_cycle": series.to_numpy() - break_trend,
    })
    output.to_csv(args.output / "gdp_trend_comparison.csv", index=False)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(output["quarter"], output["hp_cycle"], label="HP-cycle, lambda=1600")
    ax.plot(output["quarter"], output["piecewise_trend_cycle"], label="Piecewise linear trend residual")
    ax.axhline(0, linewidth=1, color="gray")
    ax.set(title="Real GDP: alternative trend-cycle decompositions", ylabel="Deviation from estimated trend")
    ax.set_xticks(np.arange(0, len(output), max(1, len(output)//8)))
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.output / "gdp_trend_comparison.png", dpi=180)
    plt.close(fig)
    print(fitted.summary())
    print("Note: This is NOT a formal structural-break unit-root test.")


if __name__ == "__main__":
    main()
