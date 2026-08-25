"""OANDA v20 REST API のうち、練習(デモ)環境専用の薄いラッパー。

【重要な安全策】本番(実資金)環境である api-fxtrade.oanda.com には
絶対に接続しない。ベースURLは練習環境(api-fxpractice.oanda.com)に
固定してあり、設定や環境変数から変更することはできない。
"""
from __future__ import annotations

import os
from typing import List, Optional

import requests

# 安全のため練習(デモ)環境のホストだけをハードコードする。
# 本番環境は意図的にサポートしない。
PRACTICE_BASE_URL = "https://api-fxpractice.oanda.com"


class OandaClientError(RuntimeError):
    pass


def _get_config_value(key: str) -> Optional[str]:
    """環境変数を優先し、なければ(Streamlit実行時のみ)st.secretsを見る。"""
    value = os.environ.get(key)
    if value:
        return value
    try:
        import streamlit as st  # noqa: PLC0415

        return st.secrets.get(key)
    except Exception:  # noqa: BLE001
        return None


class OandaClient:
    def __init__(self, api_token: Optional[str] = None, account_id: Optional[str] = None):
        self.api_token = api_token or _get_config_value("OANDA_API_TOKEN")
        self.account_id = account_id or _get_config_value("OANDA_ACCOUNT_ID")
        if not self.api_token or not self.account_id:
            raise OandaClientError(
                "OANDA_API_TOKEN / OANDA_ACCOUNT_ID が設定されていません。"
                "OANDAの練習(デモ)口座で発行したAPIトークンとアカウントIDを、"
                "環境変数またはStreamlit Secretsに設定してください。詳細はREADME参照。"
            )
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
        )

    def _url(self, path: str) -> str:
        return f"{PRACTICE_BASE_URL}{path}"

    def get_account_summary(self) -> dict:
        resp = self._session.get(self._url(f"/v3/accounts/{self.account_id}/summary"), timeout=10)
        resp.raise_for_status()
        return resp.json()["account"]

    def get_pricing(self, instruments: List[str]) -> dict:
        params = {"instruments": ",".join(instruments)}
        resp = self._session.get(
            self._url(f"/v3/accounts/{self.account_id}/pricing"), params=params, timeout=10
        )
        resp.raise_for_status()
        prices = {}
        for p in resp.json()["prices"]:
            prices[p["instrument"]] = {
                "bid": float(p["bids"][0]["price"]),
                "ask": float(p["asks"][0]["price"]),
                "time": p["time"],
            }
        return prices

    def get_candles(self, instrument: str, granularity: str = "M5", count: int = 200) -> List[dict]:
        params = {"granularity": granularity, "count": count, "price": "M"}
        resp = self._session.get(
            self._url(f"/v3/instruments/{instrument}/candles"), params=params, timeout=10
        )
        resp.raise_for_status()
        candles = []
        for c in resp.json()["candles"]:
            if not c["complete"]:
                continue
            mid = c["mid"]
            candles.append(
                {
                    "time": c["time"],
                    "open": float(mid["o"]),
                    "high": float(mid["h"]),
                    "low": float(mid["l"]),
                    "close": float(mid["c"]),
                }
            )
        return candles

    def get_open_positions(self) -> List[dict]:
        resp = self._session.get(self._url(f"/v3/accounts/{self.account_id}/openPositions"), timeout=10)
        resp.raise_for_status()
        return resp.json()["positions"]

    def place_market_order(self, instrument: str, units: int) -> dict:
        """成行注文を送信する。units: 正の値=買い、負の値=売り。"""
        body = {
            "order": {
                "instrument": instrument,
                "units": str(units),
                "type": "MARKET",
                "timeInForce": "FOK",
                "positionFill": "DEFAULT",
            }
        }
        resp = self._session.post(self._url(f"/v3/accounts/{self.account_id}/orders"), json=body, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def close_position(self, instrument: str, side: str) -> dict:
        """side: 'long' または 'short'。保有分を全決済する。"""
        if side not in ("long", "short"):
            raise ValueError("side must be 'long' or 'short'")
        key = "longUnits" if side == "long" else "shortUnits"
        body = {key: "ALL"}
        resp = self._session.put(
            self._url(f"/v3/accounts/{self.account_id}/positions/{instrument}/close"),
            json=body,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
