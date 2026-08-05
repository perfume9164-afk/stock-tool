# 日本株 AI スコアボード

ファンダ＋チャートの両面から日本株に点数をつけ、売買タイミングを判断するツール。

---

## セットアップ（ローカル）

```bash
# 1. このフォルダをクローン or ダウンロード
cd stock_tool

# 2. 仮想環境を作成（推奨）
python -m venv .venv
source .venv/bin/activate      # Mac/Linux
.venv\Scripts\activate         # Windows

# 3. 依存パッケージをインストール
pip install -r requirements.txt

# 4. アプリ起動
streamlit run app.py
```

ブラウザで http://localhost:8501 が開く。

---

## 毎朝自動更新の設定

### ① GitHub Actions（クラウド・無料・推奨）

1. このフォルダをGitHubのプライベートリポジトリにpush
2. `.github/workflows/daily.yml` がすでに設定済み
3. 毎週月〜金 09:15 JST に自動でスコアを保存し、`score_history.json` を更新

### ② cron（ローカルMac/Linux）

```bash
# crontab -e で以下を追加
15 9 * * 1-5 cd /path/to/stock_tool && /path/to/.venv/bin/python daily_update.py
```

---

## ファイル構成

```
stock_tool/
├── app.py               # Streamlit メインアプリ
├── daily_update.py      # 毎朝のスコア自動保存スクリプト
├── requirements.txt     # 依存パッケージ
├── watchlist.json       # ウォッチリスト（自動生成）
├── score_history.json   # スコア履歴DB（自動生成）
└── .github/
    └── workflows/
        └── daily.yml    # GitHub Actions 設定
```

---

## スコア基準

| 合計点 | 判定 |
|--------|------|
| 80〜100点 | 🟢 強買い |
| 65〜79点  | 🔵 買い |
| 50〜64点  | 🟡 様子見 |
| ～49点    | 🔴 見送り |

### ファンダスコア（50点満点）

| 指標 | 満点 |
|------|------|
| PER  | 10点 |
| PBR  | 10点 |
| ROE  | 10点 |
| 売上成長率 | 10点 |
| 配当利回り | 5点 |
| 財務健全性（D/E比率） | 5点 |

### チャートスコア（50点満点）

| 指標 | 満点 |
|------|------|
| RSI（14日） | 10点 |
| MA配列（25/75/200） | 15点 |
| 出来高トレンド | 10点 |
| ボリンジャーバンド位置 | 10点 |
| 52週レンジ位置 | 5点 |

---

## データソース

- **株価・テクニカル**: Yahoo Finance（yfinance経由）
- **ファンダメンタルズ**: Yahoo Finance（yfinance経由）

## 今後の拡張ポイント（Phase 2以降）

- [ ] J-Quants API 連携（より正確な財務データ）
- [ ] EDINET API 連携（決算短信の自動取込み）
- [ ] スコア重みの学習・最適化
- [ ] Streamlit Cloud でのデプロイ（URL共有）
- [ ] Slack/LINE通知（強買い銘柄をアラート）
