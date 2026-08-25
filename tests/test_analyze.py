import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from config import PAIRS_BY_KEY  # noqa: E402
import analyze  # noqa: E402


def _write_fixture_csv(path: Path, n_days: int = 300, seed: int = 7) -> None:
    import random

    rng = random.Random(seed)
    price = 150.0
    dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
    rows = []
    for d in dates:
        change = rng.uniform(-1.0, 1.0)
        open_ = price
        close = price + change
        high = max(open_, close) + rng.uniform(0, 0.3)
        low = min(open_, close) - rng.uniform(0, 0.3)
        rows.append([d.strftime("%Y-%m-%d"), round(open_, 4), round(high, 4), round(low, 4), round(close, 4)])
        price = close

    df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close"])
    df.to_csv(path, index=False)


def test_build_report_pipeline(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_fixture_csv(data_dir / "usdjpy.csv")
    monkeypatch.setattr(analyze, "ROOT", tmp_path)

    pair = PAIRS_BY_KEY["usdjpy"]
    report = analyze.build_report(pair)

    assert report["pair"] == pair.name
    assert report["trend"] in {"上昇トレンド", "下降トレンド", "レンジ/方向感なし", "判定不可(データ不足)"}
    assert report["rsi14"] is None or 0 <= report["rsi14"] <= 100
    assert len(report["recent_candles"]) == analyze.RECENT_ROWS_IN_REPORT

    md = analyze.render_markdown(report)
    assert pair.name in md
    assert "投資助言ではありません" in md


def test_load_prices_rejects_too_little_data(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_fixture_csv(data_dir / "usdjpy.csv", n_days=10)
    monkeypatch.setattr(analyze, "ROOT", tmp_path)

    pair = PAIRS_BY_KEY["usdjpy"]
    try:
        analyze.load_prices(pair)
        assert False, "should have raised"
    except ValueError as exc:
        assert "不十分" in str(exc)


def test_load_prices_missing_file_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(analyze, "ROOT", tmp_path)
    pair = PAIRS_BY_KEY["eurusd"]
    try:
        analyze.load_prices(pair)
        assert False, "should have raised"
    except FileNotFoundError:
        pass
