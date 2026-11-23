"""Monte Carlo distributions for Dickey-Fuller type t statistics.

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller


def simulate_df_null(repetitions: int = 10000, size: int = 100, seed: int = 42) -> np.ndarray:
    """ADF/DF t statistic under a random walk, including an intercept in test regression."""
    rng = np.random.default_rng(seed)
    statistics = np.empty(repetitions)
    for r in range(repetitions):
        series = rng.normal(size=size).cumsum()
        statistics[r] = adfuller(series, maxlag=0, regression="c", autolag=None)[0]
    return statistics


def simulate_trend_regression(
    repetitions: int = 10000, size: int = 250, intercept: float = 1.0,
    trend_coefficient: float = 0.65, seed: int = 0,
) -> np.ndarray:
    """Estimate Δy_t on an intercept, y_(t-1), and a time trend under a unit root.

    DGP: y_t = intercept + y_(t-1) + trend_coefficient*t + epsilon_t.
    Note: time t starts at 1 for the first transition.
    """
    rng = np.random.default_rng(seed)
    statistics = np.empty(repetitions)
    trend = np.arange(1, size)
    for r in range(repetitions):
        errors = rng.normal(size=size - 1)
        y = np.empty(size)
        y[0] = intercept
        for t in range(1, size):
            y[t] = intercept + y[t - 1] + trend_coefficient * t + errors[t - 1]
        x = sm.add_constant(np.column_stack((y[:-1], trend)))
        fit = sm.OLS(np.diff(y), x).fit()
        statistics[r] = fit.tvalues[1]
    return statistics


def save_distribution(values: np.ndarray, title: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(values, bins=50, density=True, alpha=0.85)
    ax.set(title=title, xlabel="t statistic", ylabel="Density")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repetitions", type=int, default=10000)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "results")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    cases = {
        "random_walk_with_intercept_test": simulate_df_null(args.repetitions),
        "unit_root_with_deterministic_terms": simulate_trend_regression(args.repetitions),
        "unit_root_without_deterministic_terms": simulate_trend_regression(
            args.repetitions, intercept=0, trend_coefficient=0
        ),
    }
    for name, stats in cases.items():
        print(f"\n{name}: {args.repetitions} replications")
        for p in [1, 5, 10, 50, 90, 95, 99]:
            print(f"  {p:2d}th percentile: {np.percentile(stats, p):.4f}")
        save_distribution(stats, name.replace("_", " ").title(), args.output / f"{name}.png")


if __name__ == "__main__":
    main()
