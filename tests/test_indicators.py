import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import indicators as ind  # noqa: E402


def test_sma_basic():
    close = pd.Series([1, 2, 3, 4, 5], dtype=float)
    result = ind.sma(close, window=3)
    assert pd.isna(result.iloc[0])
    assert pd.isna(result.iloc[1])
    assert result.iloc[2] == 2.0  # (1+2+3)/3
    assert result.iloc[4] == 4.0  # (3+4+5)/3


def test_rsi_all_gains_approaches_100():
    close = pd.Series(range(1, 40), dtype=float)  # 単調増加
    result = ind.rsi(close, window=14)
    assert result.iloc[-1] > 95  # ずっと上げ続けているのでRSIは100に近づく


def test_rsi_all_losses_approaches_0():
    close = pd.Series(range(40, 1, -1), dtype=float)  # 単調減少
    result = ind.rsi(close, window=14)
    assert result.iloc[-1] < 5


def test_macd_shapes_match_input():
    close = pd.Series(range(1, 100), dtype=float)
    macd_line, signal_line, hist = ind.macd(close)
    assert len(macd_line) == len(close)
    assert len(signal_line) == len(close)
    assert len(hist) == len(close)
    # histは定義上 macd_line - signal_line
    assert abs((macd_line.iloc[-1] - signal_line.iloc[-1]) - hist.iloc[-1]) < 1e-9


def test_atr_nonnegative():
    high = pd.Series([10, 11, 12, 11, 13], dtype=float)
    low = pd.Series([9, 9, 10, 9, 11], dtype=float)
    close = pd.Series([9.5, 10.5, 11.5, 10.5, 12.5], dtype=float)
    result = ind.atr(high, low, close, window=3)
    assert (result.dropna() >= 0).all()


def test_bollinger_bands_ordering():
    close = pd.Series([100, 101, 99, 102, 98, 103, 97, 104, 96, 105, 95, 106], dtype=float)
    upper, mid, lower = ind.bollinger_bands(close, window=5)
    valid = upper.dropna().index
    assert (upper[valid] >= mid[valid]).all()
    assert (mid[valid] >= lower[valid]).all()


def test_classify_trend_up_down_range():
    assert ind.classify_trend(price=110, sma20=108, sma50=105, sma200=100) == "上昇トレンド"
    assert ind.classify_trend(price=90, sma20=92, sma50=95, sma200=100) == "下降トレンド"
    assert ind.classify_trend(price=100, sma20=101, sma50=99, sma200=100) == "レンジ/方向感なし"
    assert ind.classify_trend(price=100, sma20=float("nan"), sma50=99, sma200=100) == "判定不可(データ不足)"


def test_classify_rsi_thresholds():
    assert ind.classify_rsi(75) == "買われすぎ水準"
    assert ind.classify_rsi(25) == "売られすぎ水準"
    assert ind.classify_rsi(50) == "中立"


def test_classify_macd():
    assert ind.classify_macd(1.0, 0.5) == "強気(MACD > シグナル)"
    assert ind.classify_macd(0.5, 1.0) == "弱気(MACD < シグナル)"
