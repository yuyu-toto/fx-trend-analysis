# fx-trend-analysis

USD/JPY・EUR/USD・EUR/JPY の為替レートを自動取得し、移動平均線・RSI・
MACD・ボリンジャーバンドなどのテクニカル指標を計算してレポート化する
ツールです。

## 最初に知っておいてほしいこと (重要)

**このツールは投資助言ではありません。** ここで出しているのは、過去の
値動きから計算した「移動平均線が上向きか」「RSIが買われすぎ水準か」と
いった、テクニカル指標に基づく現状の機械的な描写だけです。

- テクニカル指標はあくまで過去のデータに基づく統計量であり、将来の
  値動きを保証するものではありません。
- FXはレバレッジを伴う取引で、証拠金以上の損失が生じる可能性もある
  リスクの高い金融商品です。
- このレポートは「買いシグナル」「売りシグナル」を出すものではなく、
  現状を整理して眺めるための参考資料です。
- 実際の売買判断・資金管理・損切りルールの設定は、必ずご自身の判断と
  責任で行ってください。当ツールの内容によって生じた損失について、
  作成者は一切の責任を負いません。

## 機能

- `src/fetch_data.py`: Yahoo Finance (yfinance) から USD/JPY・EUR/USD・
  EUR/JPY の日足データ(過去5年分)を取得し、`data/{pair}.csv` に保存
- `src/indicators.py`: SMA・EMA・RSI・MACD・ATR・ボリンジャーバンドの
  計算ロジック(pandasのみで実装、外部TAライブラリ不使用)
- `src/analyze.py`: 指標を計算し、`reports/{pair}_report.md` / `.json`
  にレポートを生成
  - トレンド判定(移動平均線の並び順による単純なルールベース)
  - RSI(14)とその水準判定(買われすぎ/売られすぎ/中立)
  - MACDとシグナルラインの状態(強気/弱気)
  - ATR(14)によるボラティリティの目安
  - ボリンジャーバンド(20, ±2σ)
  - 直近60日の高値/安値(目安のレジスタンス/サポート)
  - 直近10日分のOHLC
- `.github/workflows/update.yml`: 平日にデータ取得・分析・コミットを
  自動実行

## セットアップ (ローカルで実行する場合)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python src/fetch_data.py   # data/{pair}.csv を取得
python src/analyze.py      # reports/ にレポートを生成
```

## データ取得元について

Yahoo Finance の非公式データ取得ライブラリ [yfinance](https://github.com/ranaroussi/yfinance)
を使っています。無料で使える一方、Yahoo側の仕様変更やレート制限で
一時的に取得できなくなることがあります。**もしGitHub Actionsのログで
データ取得に失敗した場合**、エラーメッセージを確認のうえ、必要であれば
別のデータ取得元(Alpha Vantage、Twelve Dataなど、要APIキー)への
切り替えを検討してください。

ロト分析ツール(別リポジトリ)を作った際、当初想定していたデータ元が
GitHub ActionsのIPをブロックしていて使えなかった、という経緯があった
ため、最初のワークフロー実行時にうまく取得できるか確認することを
おすすめします。

## ディレクトリ構成

```
src/
  config.py       # 対象通貨ペアの設定
  fetch_data.py   # 為替データの取得・正規化
  indicators.py   # テクニカル指標の計算ロジック
  analyze.py      # 指標計算・レポート生成
tests/
  test_indicators.py  # 指標計算ロジックの単体テスト
  test_analyze.py     # 合成データによるレポート生成のテスト
data/             # 正規化済みの為替データ (Actionsが自動更新)
reports/          # 生成されたレポート (Actionsが自動更新)
.github/workflows/
  update.yml      # 定期データ取得・分析ワークフロー
  ci.yml          # プッシュ時にテストを実行するCI
```

## テスト

```bash
pytest -q
```

合成データを使って、各テクニカル指標の計算が定義通りに動くこと
(例: 単調増加する価格系列ではRSIが100に近づく、ボリンジャーバンドの
上限≥中央値≥下限が常に成り立つ、など)を検証しています。
