import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from oanda_client import PRACTICE_BASE_URL, OandaClient, OandaClientError  # noqa: E402


def test_missing_credentials_raises(monkeypatch):
    monkeypatch.delenv("OANDA_API_TOKEN", raising=False)
    monkeypatch.delenv("OANDA_ACCOUNT_ID", raising=False)
    with pytest.raises(OandaClientError):
        OandaClient()


def test_practice_base_url_is_hardcoded():
    # 安全策: 本番環境(api-fxtrade.oanda.com)には絶対に接続しない
    assert PRACTICE_BASE_URL == "https://api-fxpractice.oanda.com"
    assert "fxtrade" not in PRACTICE_BASE_URL


def _client() -> OandaClient:
    return OandaClient(api_token="dummy-token", account_id="001-000-1234567-001")


def test_get_account_summary(requests_mock):
    client = _client()
    requests_mock.get(
        f"{PRACTICE_BASE_URL}/v3/accounts/001-000-1234567-001/summary",
        json={"account": {"NAV": "100000.00", "currency": "JPY"}},
    )
    account = client.get_account_summary()
    assert account["NAV"] == "100000.00"
    assert account["currency"] == "JPY"


def test_get_pricing(requests_mock):
    client = _client()
    requests_mock.get(
        f"{PRACTICE_BASE_URL}/v3/accounts/001-000-1234567-001/pricing",
        json={
            "prices": [
                {
                    "instrument": "USD_JPY",
                    "bids": [{"price": "159.100"}],
                    "asks": [{"price": "159.120"}],
                    "time": "2026-08-25T00:00:00Z",
                }
            ]
        },
    )
    prices = client.get_pricing(["USD_JPY"])
    assert prices["USD_JPY"]["bid"] == 159.100
    assert prices["USD_JPY"]["ask"] == 159.120


def test_get_candles_skips_incomplete(requests_mock):
    client = _client()
    requests_mock.get(
        f"{PRACTICE_BASE_URL}/v3/instruments/USD_JPY/candles",
        json={
            "candles": [
                {
                    "complete": True,
                    "time": "2026-08-25T00:00:00Z",
                    "mid": {"o": "159.0", "h": "159.5", "l": "158.8", "c": "159.2"},
                },
                {
                    "complete": False,
                    "time": "2026-08-25T00:05:00Z",
                    "mid": {"o": "159.2", "h": "159.3", "l": "159.1", "c": "159.15"},
                },
            ]
        },
    )
    candles = client.get_candles("USD_JPY")
    assert len(candles) == 1
    assert candles[0]["close"] == 159.2


def test_place_market_order_sends_units_as_string(requests_mock):
    client = _client()
    m = requests_mock.post(
        f"{PRACTICE_BASE_URL}/v3/accounts/001-000-1234567-001/orders",
        json={"orderFillTransaction": {"id": "1"}},
    )
    client.place_market_order("USD_JPY", -1000)
    assert m.last_request.json()["order"]["units"] == "-1000"
    assert m.last_request.json()["order"]["type"] == "MARKET"


def test_close_position_invalid_side_raises():
    client = _client()
    with pytest.raises(ValueError):
        client.close_position("USD_JPY", "sideways")
