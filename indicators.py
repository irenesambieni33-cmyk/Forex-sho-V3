"""Requested technical indicators implemented with pandas/numpy only."""

from __future__ import annotations

import numpy as np
import pandas as pd

from config import *


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    close, high, low = out["close"], out["high"], out["low"]

    out["ema20"] = close.ewm(span=EMA_FAST, adjust=False, min_periods=EMA_FAST).mean()
    out["ema50"] = close.ewm(span=EMA_SLOW, adjust=False, min_periods=EMA_SLOW).mean()
    out["sma200"] = close.rolling(SMA_LONG, min_periods=SMA_LONG).mean()

    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / RSI_PERIOD, adjust=False, min_periods=RSI_PERIOD).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / RSI_PERIOD, adjust=False, min_periods=RSI_PERIOD).mean()
    rs = gain / loss.replace(0, np.nan)
    out["rsi14"] = 100 - 100 / (1 + rs)
    out.loc[(loss == 0) & (gain > 0), "rsi14"] = 100.0
    out.loc[(gain == 0) & (loss > 0), "rsi14"] = 0.0

    fast = close.ewm(span=MACD_FAST, adjust=False, min_periods=MACD_FAST).mean()
    slow = close.ewm(span=MACD_SLOW, adjust=False, min_periods=MACD_SLOW).mean()
    out["macd"] = fast - slow
    out["macd_signal"] = out["macd"].ewm(span=MACD_SIGNAL, adjust=False, min_periods=MACD_SIGNAL).mean()
    out["macd_hist"] = out["macd"] - out["macd_signal"]

    prev_close = close.shift(1)
    tr = pd.concat([(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    out["tr"] = tr
    out["atr14"] = tr.ewm(alpha=1 / ATR_PERIOD, adjust=False, min_periods=ATR_PERIOD).mean()

    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=out.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=out.index)
    plus_sm = plus_dm.ewm(alpha=1 / ADX_PERIOD, adjust=False, min_periods=ADX_PERIOD).mean()
    minus_sm = minus_dm.ewm(alpha=1 / ADX_PERIOD, adjust=False, min_periods=ADX_PERIOD).mean()
    atr_safe = out["atr14"].replace(0, np.nan)
    out["di_plus"] = 100 * plus_sm / atr_safe
    out["di_minus"] = 100 * minus_sm / atr_safe
    di_sum = (out["di_plus"] + out["di_minus"]).replace(0, np.nan)
    dx = 100 * (out["di_plus"] - out["di_minus"]).abs() / di_sum
    out["adx14"] = dx.ewm(alpha=1 / ADX_PERIOD, adjust=False, min_periods=ADX_PERIOD).mean()

    mid = close.rolling(BB_PERIOD, min_periods=BB_PERIOD).mean()
    sd = close.rolling(BB_PERIOD, min_periods=BB_PERIOD).std(ddof=0)
    out["bb_mid"] = mid
    out["bb_upper"] = mid + BB_STD * sd
    out["bb_lower"] = mid - BB_STD * sd

    lowest = low.rolling(STOCH_PERIOD, min_periods=STOCH_PERIOD).min()
    highest = high.rolling(STOCH_PERIOD, min_periods=STOCH_PERIOD).max()
    denom = (highest - lowest).replace(0, np.nan)
    raw_k = 100 * (close - lowest) / denom
    out["stoch_k"] = raw_k.rolling(STOCH_K_SMOOTH, min_periods=STOCH_K_SMOOTH).mean()
    out["stoch_d"] = out["stoch_k"].rolling(STOCH_D_SMOOTH, min_periods=STOCH_D_SMOOTH).mean()
    return out
