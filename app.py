#!/usr/bin/env python3
"""OANDA練習(デモ)口座のライブ相場を使った、実資金リスクゼロの
FX売買練習ダッシュボード。

【重要】これは投資助言ではありません。表示される価格は本物のライブ相場
ですが、接続先はOANDAの練習(デモ)環境のみで、実際の資金は動きません。
テクニカル指標(SMA/RSI)は現状の機械的な描写であり、売買シグナルでは
ありません。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import indicators as ind  # noqa: E402
from config import PAIRS  # noqa: E402
from oanda_client import OandaClient, OandaClientError  # noqa: E402

st.set_page_config(page_title="FXライブ練習ダッシュボード", layout="wide")

st.title("FXライブ練習ダッシュボード (OANDA練習口座)")
st.caption(
    "⚠️ これは投資助言ではありません。OANDAの**練習(デモ)口座**に接続しており、"
    "実際の資金リスクはありませんが、表示される価格・約定は本物のライブ相場に"
    "基づきます。売買の最終判断は必ずご自身の責任で行ってください。"
)

try:
    client = OandaClient()
except OandaClientError as exc:
    st.error(str(exc))
    st.info(
        "OANDAの練習口座を開設し、APIトークンとアカウントIDを取得してから、"
        "環境変数(ローカル実行時)または Streamlit Secrets(デプロイ時)に"
        "OANDA_API_TOKEN / OANDA_ACCOUNT_ID として設定してください。"
        "手順はREADMEの「OANDA練習口座との連携」を参照してください。"
    )
    st.stop()

st_autorefresh(interval=5000, key="refresh")

pair_names = [p.name for p in PAIRS]
selected_name = st.sidebar.selectbox("通貨ペア", pair_names)
pair = next(p for p in PAIRS if p.name == selected_name)
granularity = st.sidebar.selectbox("時間足", ["M1", "M5", "M15", "H1"], index=1)

try:
    account = client.get_account_summary()
    prices = client.get_pricing([pair.oanda_instrument])
    candles = client.get_candles(pair.oanda_instrument, granularity=granularity, count=200)
    positions = client.get_open_positions()
except Exception as exc:  # noqa: BLE001
    st.error(f"OANDA APIへの接続に失敗しました: {exc}")
    st.stop()

price = prices[pair.oanda_instrument]
col1, col2, col3, col4 = st.columns(4)
col1.metric("Bid", price["bid"])
col2.metric("Ask", price["ask"])
col3.metric("スプレッド", round(price["ask"] - price["bid"], 5))
col4.metric("口座残高(NAV)", f"{float(account['NAV']):,.2f} {account['currency']}")

if not candles:
    st.warning("ローソク足データがまだありません。しばらくしてから再読み込みしてください。")
    st.stop()

df = pd.DataFrame(candles)
df["time"] = pd.to_datetime(df["time"])
df = df.set_index("time")
df["sma20"] = ind.sma(df["close"], 20)
df["sma50"] = ind.sma(df["close"], 50)
df["rsi14"] = ind.rsi(df["close"], 14)

st.subheader(f"{pair.name} ローソク足 ({granularity})")
fig = go.Figure(
    data=[
        go.Candlestick(
            x=df.index, open=df["open"], high=df["high"], low=df["low"], close=df["close"], name="価格"
        ),
        go.Scatter(x=df.index, y=df["sma20"], line=dict(width=1), name="SMA20"),
        go.Scatter(x=df.index, y=df["sma50"], line=dict(width=1), name="SMA50"),
    ]
)
fig.update_layout(xaxis_rangeslider_visible=False, height=500, margin=dict(t=20, b=20))
st.plotly_chart(fig, use_container_width=True)

rsi_col, pos_col = st.columns([1, 1])
with rsi_col:
    st.subheader("RSI(14)")
    st.line_chart(df[["rsi14"]])
    latest_rsi = df["rsi14"].iloc[-1]
    if pd.notna(latest_rsi):
        st.caption(f"現在値: {latest_rsi:.1f} ({ind.classify_rsi(latest_rsi)})")

with pos_col:
    st.subheader("保有ポジション")
    if positions:
        for p in positions:
            st.write(p)
    else:
        st.write("現在ポジションはありません。")

st.subheader("練習売買 (OANDAデモ口座に発注されます)")
units = st.number_input("数量(通貨単位、例: 1000)", min_value=1, value=1000, step=1000)
c1, c2, c3, c4 = st.columns(4)
if c1.button("買い(Long)"):
    result = client.place_market_order(pair.oanda_instrument, units)
    st.success("買い注文を送信しました")
    st.json(result)
if c2.button("売り(Short)"):
    result = client.place_market_order(pair.oanda_instrument, -units)
    st.success("売り注文を送信しました")
    st.json(result)
if c3.button("ロングを決済"):
    result = client.close_position(pair.oanda_instrument, "long")
    st.success("ロングポジションを決済しました")
    st.json(result)
if c4.button("ショートを決済"):
    result = client.close_position(pair.oanda_instrument, "short")
    st.success("ショートポジションを決済しました")
    st.json(result)
