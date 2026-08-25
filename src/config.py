"""対象通貨ペアの設定。

yf_symbol は Yahoo Finance (yfinance) のティッカーシンボル。
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class PairConfig:
    key: str
    name: str
    yf_symbol: str
    data_file: str


PAIRS: Tuple[PairConfig, ...] = (
    PairConfig(key="usdjpy", name="USD/JPY (ドル円)", yf_symbol="USDJPY=X", data_file="data/usdjpy.csv"),
    PairConfig(key="eurusd", name="EUR/USD (ユーロドル)", yf_symbol="EURUSD=X", data_file="data/eurusd.csv"),
    PairConfig(key="eurjpy", name="EUR/JPY (ユーロ円)", yf_symbol="EURJPY=X", data_file="data/eurjpy.csv"),
)

PAIRS_BY_KEY = {p.key: p for p in PAIRS}

# 取得する過去データの期間 (yfinanceのperiod指定)
FETCH_PERIOD = "5y"
FETCH_INTERVAL = "1d"
