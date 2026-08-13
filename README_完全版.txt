日本株AIスコアボード 完全版

【入れ替えるファイル】
1. app.py → C:\Users\perfu\Documents\stock_tool\app.py
2. daily_volume_scanner_fixed.py → C:\Users\perfu\Documents\stock_tool\daily_volume_scanner_fixed.py

【重要】
既存の data フォルダは削除しないでください。
- data/ai_predictions.json
- data/ai_prediction_history.json
- data/journal.json
- data/watchlist.json
- data/score_history.json
これらは履歴・日誌の永続保存に使います。

【今回の修正】
- 📡 AI予想：本日のAI TOP10 / 出来高TOP50 / AIコメント / 過去のAI予想 / 的中実績
- AIコメントのフォールバックを銘柄ごとに異なる内容へ変更
- 銘柄名を日本語優先で保存し、UIで毎回Web取得しない
- data/jp_name_cache.json に日本語社名をキャッシュ
- 出来高TOP50表示で get_company_name を50回連続実行しない
- 平均スコア・最高スコアの大型表示を削除
- 各銘柄カードの右側にファンダ/チャートスコアを表示
- トレード日誌を data/journal.json に永続保存
- 銘柄を切り替えても日誌は初期化されない
- AI予想履歴を日付単位で蓄積（同日の再実行は置換）
- Gemini APIキーは環境変数または stock_tool/.env から読み込み可能

【起動】
PowerShell:
cd "C:\Users\perfu\Documents\stock_tool"
py daily_volume_scanner_fixed.py
py -m streamlit run app.py

ブラウザ:
http://localhost:8501

【Gemini】
.env を使う場合は stock_tool フォルダに以下を作成:
GEMINI_API_KEY=あなたのAPIキー

APIキーがない場合でもスキャナーは停止せず、総合スコア上位10銘柄をフォールバックとして表示します。
その場合、AIコメントは各銘柄のファンダ/チャート/出来高/RSIを使った個別コメントになります。
