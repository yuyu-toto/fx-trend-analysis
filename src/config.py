"""対象通貨ペアの設定。

yf_symbol は Yahoo Finance (yfinance) のティッカーシンボル。
oanda_instrument は OANDA v20 REST APIのinstrument名(アンダースコア区切り)。
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class PairConfig:
    key: str
    name: str
    yf_symbol: str
    oanda_instrument: str
    data_file: str


PAIRS: Tuple[PairConfig, ...] = (
    PairConfig(
        key="usdjpy", name="USD/JPY (ドル円)", yf_symbol="USDJPY=X",
        oanda_instrument="USD_JPY", data_file="data/usdjpy.csv",
    ),
    PairConfig(
        key="eurusd", name="EUR/USD (ユーロドル)", yf_symbol="EURUSD=X",
        oanda_instrument="EUR_USD", data_file="data/eurusd.csv",
    ),
    PairConfig(
        key="eurjpy", name="EUR/JPY (ユーロ円)", yf_symbol="EURJPY=X",
        oanda_instrument="EUR_JPY", data_file="data/eurjpy.csv",
    ),
)

PAIRS_BY_KEY = {p.key: p for p in PAIRS}

# 取得する過去データの期間 (yfinanceのperiod指定)
FETCH_PERIOD = "5y"
FETCH_INTERVAL = "1d"
