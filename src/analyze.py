#!/usr/bin/env python3
"""data/{pair}.csv からテクニカル指標を計算し、
reports/{pair}_report.md / .json にレポートを出力する。

ここで出すのはあくまで「現状を機械的に描写したテクニカル指標」であり、
売買を推奨するものではない。最終的な投資判断は必ず自己責任で行うこと。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import indicators as ind  # noqa: E402
from config import PAIRS, PairConfig  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LOOKBACK_HIGH_LOW_DAYS = 60
RECENT_ROWS_IN_REPORT = 10


def load_prices(pair: PairConfig) -> pd.DataFrame:
    path = ROOT / pair.data_file
    if not path.exists():
        raise FileNotFoundError(f"{path} が見つかりません。先に src/fetch_data.py を実行してください。")
    df = pd.read_csv(path, parse_dates=["date"], index_col="date")
    df = df.sort_index()
    if len(df) < 60:
        raise ValueError(f"{pair.name}: データが{len(df)}件しかなく、分析には不十分です(60件以上推奨)。")
    return df


def build_report(pair: PairConfig) -> dict:
    df = load_prices(pair)
    close, high, low = df["close"], df["high"], df["low"]

    sma20, sma50, sma200 = ind.sma(close, 20), ind.sma(close, 50), ind.sma(close, 200)
    rsi14 = ind.rsi(close, 14)
    macd_line, signal_line, hist = ind.macd(close)
    atr14 = ind.atr(high, low, close, 14)
    bb_upper, bb_mid, bb_lower = ind.bollinger_bands(close, 20)

    latest_date = df.index[-1]
    price = float(close.iloc[-1])
    prev_price = float(close.iloc[-2]) if len(close) > 1 else price
    change_pct = round((price - prev_price) / prev_price * 100, 3) if prev_price else 0.0

    recent_window = df.tail(LOOKBACK_HIGH_LOW_DAYS)
    period_high = float(recent_window["high"].max())
    period_low = float(recent_window["low"].min())

    rsi_value = float(rsi14.iloc[-1]) if not pd.isna(rsi14.iloc[-1]) else None
    macd_value = float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None
    signal_value = float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else None
    atr_value = float(atr14.iloc[-1]) if not pd.isna(atr14.iloc[-1]) else None

    recent_rows = []
    for date, row in df.tail(RECENT_ROWS_IN_REPORT).iterrows():
        recent_rows.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "open": round(float(row["open"]), 4),
                "high": round(float(row["high"]), 4),
                "low": round(float(row["low"]), 4),
                "close": round(float(row["close"]), 4),
            }
        )

    return {
        "pair": pair.name,
        "latest_date": latest_date.strftime("%Y-%m-%d"),
        "price": round(price, 4),
        "change_pct": change_pct,
        "sma20": round(float(sma20.iloc[-1]), 4) if not pd.isna(sma20.iloc[-1]) else None,
        "sma50": round(float(sma50.iloc[-1]), 4) if not pd.isna(sma50.iloc[-1]) else None,
        "sma200": round(float(sma200.iloc[-1]), 4) if not pd.isna(sma200.iloc[-1]) else None,
        "trend": ind.classify_trend(
            price,
            float(sma20.iloc[-1]) if not pd.isna(sma20.iloc[-1]) else float("nan"),
            float(sma50.iloc[-1]) if not pd.isna(sma50.iloc[-1]) else float("nan"),
            float(sma200.iloc[-1]) if not pd.isna(sma200.iloc[-1]) else float("nan"),
        ),
        "rsi14": round(rsi_value, 2) if rsi_value is not None else None,
        "rsi_status": ind.classify_rsi(rsi_value if rsi_value is not None else float("nan")),
        "macd": round(macd_value, 5) if macd_value is not None else None,
        "macd_signal": round(signal_value, 5) if signal_value is not None else None,
        "macd_status": ind.classify_macd(
            macd_value if macd_value is not None else float("nan"),
            signal_value if signal_value is not None else float("nan"),
        ),
        "atr14": round(atr_value, 4) if atr_value is not None else None,
        "bollinger_upper": round(float(bb_upper.iloc[-1]), 4) if not pd.isna(bb_upper.iloc[-1]) else None,
        "bollinger_lower": round(float(bb_lower.iloc[-1]), 4) if not pd.isna(bb_lower.iloc[-1]) else None,
        f"period_high_{LOOKBACK_HIGH_LOW_DAYS}d": round(period_high, 4),
        f"period_low_{LOOKBACK_HIGH_LOW_DAYS}d": round(period_low, 4),
        "recent_candles": recent_rows,
    }


def render_markdown(report: dict) -> str:
    lines = []
    lines.append(f"# {report['pair']} トレンドレポート")
    lines.append("")
    lines.append(
        "> ⚠️ これは投資助言ではありません。移動平均線・RSI・MACDなどの"
        "テクニカル指標に基づく現状の機械的な描写であり、将来の値動きを"
        "保証するものではありません。FXはレバレッジを伴い損失リスクが"
        "大きい商品です。売買の最終判断・資金管理は必ずご自身の責任で"
        "行ってください。"
    )
    lines.append("")
    lines.append(f"- 基準日: {report['latest_date']}")
    lines.append(f"- 終値: {report['price']} (前日比 {report['change_pct']}%)")
    lines.append("")

    lines.append("## トレンド判定 (移動平均線)")
    lines.append("")
    lines.append(f"- 判定: **{report['trend']}**")
    lines.append(f"- SMA20: {report['sma20']}")
    lines.append(f"- SMA50: {report['sma50']}")
    lines.append(f"- SMA200: {report['sma200']}")
    lines.append("")

    lines.append("## モメンタム指標")
    lines.append("")
    lines.append(f"- RSI(14): {report['rsi14']} → {report['rsi_status']}")
    lines.append(
        f"- MACD: {report['macd']} / シグナル: {report['macd_signal']} → {report['macd_status']}"
    )
    lines.append("")

    lines.append("## ボラティリティ・レンジ")
    lines.append("")
    lines.append(f"- ATR(14) (1日あたりの平均的な値動き幅の目安): {report['atr14']}")
    lines.append(f"- ボリンジャーバンド(20, ±2σ): 上限 {report['bollinger_upper']} / 下限 {report['bollinger_lower']}")
    high_key = [k for k in report if k.startswith("period_high_")][0]
    low_key = [k for k in report if k.startswith("period_low_")][0]
    window_days = high_key.split("_")[-1]
    lines.append(f"- 直近{window_days}の高値/安値(目安のレジスタンス/サポート): {report[high_key]} / {report[low_key]}")
    lines.append("")

    lines.append("## 直近の値動き")
    lines.append("")
    lines.append("| 日付 | 始値 | 高値 | 安値 | 終値 |")
    lines.append("|---|---|---|---|---|")
    for row in report["recent_candles"]:
        lines.append(f"| {row['date']} | {row['open']} | {row['high']} | {row['low']} | {row['close']} |")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    out_dir = ROOT / "reports"
    out_dir.mkdir(exist_ok=True)
    for pair in PAIRS:
        report = build_report(pair)
        (out_dir / f"{pair.key}_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (out_dir / f"{pair.key}_report.md").write_text(render_markdown(report), encoding="utf-8")
        print(f"[{pair.key}] レポートを reports/{pair.key}_report.md に出力しました")


if __name__ == "__main__":
    main()
