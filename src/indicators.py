"""テクニカル指標の計算ロジック。外部のTAライブラリに依存せず、
pandasだけで標準的な定義に沿って計算する(検証しやすくするため)。
"""
from __future__ import annotations

import pandas as pd


def sma(close: pd.Series, window: int) -> pd.Series:
    return close.rolling(window=window).mean()


def ema(close: pd.Series, span: int) -> pd.Series:
    return close.ewm(span=span, adjust=False).mean()


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """Wilderの平滑化によるRSI。"""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    ranges = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    )
    return ranges.max(axis=1)


def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    tr = true_range(high, low, close)
    return tr.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()


def bollinger_bands(close: pd.Series, window: int = 20, num_std: float = 2.0):
    mid = sma(close, window)
    std = close.rolling(window=window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return upper, mid, lower


def classify_trend(price: float, sma20: float, sma50: float, sma200: float) -> str:
    """移動平均線の並び順に基づく単純なルールベースのトレンド分類。"""
    if any(pd.isna(v) for v in (sma20, sma50, sma200)):
        return "判定不可(データ不足)"
    if price > sma20 > sma50 > sma200:
        return "上昇トレンド"
    if price < sma20 < sma50 < sma200:
        return "下降トレンド"
    return "レンジ/方向感なし"


def classify_rsi(value: float) -> str:
    if pd.isna(value):
        return "判定不可"
    if value >= 70:
        return "買われすぎ水準"
    if value <= 30:
        return "売られすぎ水準"
    return "中立"


def classify_macd(macd_value: float, signal_value: float) -> str:
    if pd.isna(macd_value) or pd.isna(signal_value):
        return "判定不可"
    return "強気(MACD > シグナル)" if macd_value > signal_value else "弱気(MACD < シグナル)"
