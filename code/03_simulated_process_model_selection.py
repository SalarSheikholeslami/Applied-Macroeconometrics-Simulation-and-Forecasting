"""Identify a simulated time-series process using ACF/PACF and AR/ARMA comparisons.

Requires data/unknown.xlsx with worksheet 'data' and a series in the first
numeric column. Reported model preference is conditional on the supplied data.
"""
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import acf, pacf
from statsmodels.stats.diagnostic import acorr_ljungbox

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT/"data/unknown.xlsx")
    args=parser.parse_args()
    if not args.data.exists(): raise FileNotFoundError(f"Missing {args.data}; see data/README.md")
    df=pd.read_excel(args.data, sheet_name="data")
    cols=[col for col in df.columns if pd.to_numeric(df[col], errors="coerce").notna().sum() > 20]
    if not cols: raise ValueError("No numeric time series was found in worksheet 'data'")
    y=pd.to_numeric(df[cols[0]], errors="coerce").dropna().astype(float).reset_index(drop=True)
    print(f"Observed sample size: {len(y)}")
    print("ACF(1:6):", np.round(acf(y, nlags=6)[1:],3))
    print("PACF(1:6):", np.round(pacf(y, nlags=6)[1:],3))
    fits={"AR(2)":(2,0,0),"AR(3)":(3,0,0),"ARMA(2,1)":(2,0,1)}
    results=[]
    for label,order in fits.items():
        fit=ARIMA(y,order=order,trend="c").fit()
        lb=acorr_ljungbox(fit.resid,lags=[8,12],return_df=True)
        results.append((label,fit.aic,fit.bic,lb['lb_pvalue'].iloc[0],lb['lb_pvalue'].iloc[1]))
    table=pd.DataFrame(results,columns=['model','AIC','BIC','LB_p_8','LB_p_12'])
    print(table.round(4).to_string(index=False))
    print("Minimum AIC:",table.loc[table['AIC'].idxmin(),'model'])
    print("Minimum BIC:",table.loc[table['BIC'].idxmin(),'model'])
    print("Model selection must consider diagnostics, not just the minimum information criterion.")

if __name__ == '__main__':main()
