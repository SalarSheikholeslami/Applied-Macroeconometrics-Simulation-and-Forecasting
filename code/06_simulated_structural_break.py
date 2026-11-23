"""Explore a known level shift in a simulated time series.

Uses data/ybreak.xlsx (100 observations; column Y), with a specified shift at
t=51. This is a diagnostic illustration, NOT a full Perron (1989) test.
"""
from pathlib import Path
import argparse
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
from statsmodels.stats.diagnostic import acorr_ljungbox
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',type=Path,default=ROOT/'data/ybreak.xlsx')
    p.add_argument('--break-observation',type=int,default=51)
    p.add_argument('--output',type=Path,default=ROOT/'results')
    a=p.parse_args()
    if not a.data.exists(): raise FileNotFoundError(f"Missing {a.data}; see data/README.md")
    df=pd.read_excel(a.data); df.columns=df.columns.str.strip().str.upper()
    if 'Y' not in df: raise ValueError("Expected a column named Y")
    y=pd.to_numeric(df['Y'],errors='coerce').dropna().to_numpy(dtype=float)
    t=np.arange(1,len(y)+1)
    if len(y)<30 or not 2 <= a.break_observation < len(y):
        raise ValueError('Invalid sample size or break location')
    dl=(t>=a.break_observation).astype(float)
    detrending=sm.OLS(y,sm.add_constant(np.column_stack((t,dl)))).fit()
    resid=detrending.resid
    test=adfuller(resid,maxlag=0,autolag=None,regression='n')
    # This statistic uses generated residuals; standard ADF critical values are
    # not valid for the structural-break test. Do not claim it is Perron (1989).
    print(f'Level shift estimate: {detrending.params[-1]:.4f}')
    print(f'Residual-based t-statistic (descriptive): {test[0]:.4f}')
    print('No formal break-adjusted unit-root inference is reported.')
    print('Residual autocorrelation diagnostic (Ljung–Box):',
          acorr_ljungbox(detrending.resid,lags=[4,8],return_df=True).round(4).to_string())
    a.output.mkdir(parents=True,exist_ok=True)
    fig,ax=plt.subplots(figsize=(9,4.5))
    ax.plot(t,y,label='Simulated series')
    ax.plot(t,detrending.fittedvalues,label='Fitted broken trend')
    ax.axvline(a.break_observation,color='gray',linestyle='--',label='Specified break')
    ax.set(xlabel='Observation',ylabel='Value',title='Simulated series with specified level shift')
    ax.legend(); fig.tight_layout()
    fig.savefig(a.output/'simulated_structural_break.png',dpi=180);plt.close(fig)

if __name__=='__main__':main()
