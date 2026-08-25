#!/usr/bin/env python3
"""Yahoo Finance (yfinance) から為替の日足データを取得し、
data/{pair}.csv に正規化して保存する。
"""
from __future__ import annotations

import sys
from pathlib import Path

import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import FETCH_INTERVAL, FETCH_PERIOD, PAIRS, PairConfig  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def fetch_pair(pair: PairConfig):
    df = yf.download(
        pair.yf_symbol,
        period=FETCH_PERIOD,
        interval=FETCH_INTERVAL,
        auto_adjust=False,
        progress=False,
    )
    if df.empty:
        raise RuntimeError(f"{pair.name}: {pair.yf_symbol} のデータが取得できませんでした")

    # yfinanceはマルチインデックス列になる場合があるため平坦化する
    if isinstance(df.columns, __import__("pandas").MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df[["Open", "High", "Low", "Close"]].dropna()
    df.index.name = "date"
    df.columns = ["open", "high", "low", "close"]
    return df


def write_csv(pair: PairConfig, df) -> None:
    out_path = ROOT / pair.data_file
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, date_format="%Y-%m-%d")
    print(f"[{pair.key}] {out_path} に {len(df)} 件を書き込みました "
          f"({df.index.min().date()} 〜 {df.index.max().date()})")


def main() -> None:
    for pair in PAIRS:
        df = fetch_pair(pair)
        write_csv(pair, df)


if __name__ == "__main__":
    main()
