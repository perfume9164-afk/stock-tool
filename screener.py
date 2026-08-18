"""
毎日16:15に起動する自動スクリーニングスクリプト
出来高上位50銘柄を抽出 → スコアリング → Geminiでトレード予想生成 → GitHubに保存
"""

import json
import os
import time
from datetime import datetime, date

# ─── プライム主要銘柄リスト（300銘柄）────────────────────────
PRIME_TICKERS = [
    # 自動車・輸送機器
    "7203.T","7267.T","7269.T","7270.T","7201.T","7202.T","7211.T","7261.T",
    # 電機・精密
    "6758.T","6501.T","6702.T","6723.T","6752.T","6754.T","6762.T","6770.T",
    "6857.T","6861.T","6902.T","6952.T","6954.T","6971.T","7735.T","7751.T",
    "7752.T","6503.T","6504.T","6506.T","6645.T","6701.T","6724.T","6727.T",
    # 半導体・電子部品
    "8035.T","4063.T","6526.T","6315.T","5803.T","6723.T","6594.T","6981.T",
    "4452.T","6146.T","3436.T","6641.T","6963.T","6967.T","7744.T","7741.T",
    # 情報・通信
    "9984.T","9432.T","9433.T","9434.T","9437.T","4689.T","3659.T","4755.T",
    "3765.T","2432.T","3632.T","3668.T","3673.T","3851.T","4307.T","4371.T",
    "4726.T","4739.T","9613.T","9618.T","9766.T","9104.T","2371.T","3994.T",
    # 金融・銀行
    "8306.T","8316.T","8411.T","8001.T","8002.T","8031.T","8053.T","8058.T",
    "8309.T","8308.T","8304.T","7186.T","8355.T","8359.T","8377.T","8386.T",
    "8418.T","8253.T","8591.T","8601.T","8604.T","8630.T","8750.T","8766.T",
    "8795.T","8801.T","8802.T","8804.T","8830.T","3289.T","8698.T","8697.T",
    # 医薬・ヘルスケア
    "4519.T","4502.T","4503.T","4506.T","4507.T","4523.T","4528.T","4536.T",
    "4541.T","4568.T","4578.T","2135.T","4588.T","4563.T","4592.T","6869.T",
    "7731.T","7733.T","7741.T","4543.T","6841.T","6849.T","7832.T","4151.T",
    # 素材・化学
    "4188.T","4183.T","4185.T","4208.T","4272.T","4901.T","4911.T","4005.T",
    "4021.T","4042.T","4043.T","4061.T","4062.T","5019.T","5020.T","5101.T",
    "5108.T","5110.T","5201.T","5202.T","5214.T","5232.T","5233.T","5301.T",
    "5332.T","5333.T","5401.T","5406.T","5411.T","5541.T","5703.T","5707.T",
    "5711.T","5713.T","5714.T","5715.T","5801.T","5802.T","5803.T","3407.T",
    # エネルギー・資源
    "5016.T","5019.T","5020.T","1605.T","1662.T","5401.T","5406.T","9513.T",
    "9502.T","9503.T","9504.T","9531.T","9532.T",
    # 小売・消費財
    "9983.T","8267.T","8268.T","8028.T","8270.T","7309.T","7453.T","7455.T",
    "7532.T","7544.T","7581.T","8273.T","3382.T","2651.T","2670.T","2674.T",
    "3086.T","3099.T","3092.T","2809.T","2802.T","2897.T","2914.T","2587.T",
    "2503.T","2502.T","2501.T","2269.T","2282.T","2267.T","2264.T","2212.T",
    # 不動産・建設
    "1925.T","1928.T","1801.T","1802.T","1803.T","1808.T","1812.T","1820.T",
    "1821.T","1833.T","1963.T","3003.T","3105.T","3201.T","3231.T","3278.T",
    "8801.T","8802.T","8804.T","8830.T","3289.T","8986.T","3234.T","3240.T",
    # 機械・重工
    "6326.T","6301.T","6302.T","6305.T","6361.T","6367.T","6471.T","6472.T",
    "6473.T","6481.T","6506.T","6586.T","6588.T","7011.T","7012.T","7013.T",
    "7004.T","7003.T","7014.T","7102.T","7105.T","7240.T","7242.T","7259.T",
    # サービス・レジャー
    "4661.T","9602.T","9603.T","9604.T","9605.T","4689.T","2181.T","2185.T",
    "2413.T","6098.T","7974.T","9684.T","3697.T","2121.T","6254.T","4324.T",
    # 流通・物流
    "9064.T","9062.T","9065.T","9101.T","9104.T","9107.T","9020.T","9021.T",
    "9022.T","9001.T","9005.T","9007.T","9008.T","9009.T","9010.T","9011.T",
    # その他注目
    "8113.T","5243.T","6702.T","4519.T","7203.T","6758.T","9984.T","8306.T",
    "4661.T","6861.T","8035.T","4063.T","6526.T","5803.T","7013.T","9348.T",
    "8136.T","7157.T","5595.T","3901.T","1882.T",
]
# 重複を除去
PRIME_TICKERS = list(dict.fromkeys(PRIME_TICKERS))


PREDICTIONS_FILE = "predictions.json"
SCORE_HISTORY_FILE = "score_history.json"

def load_json(path, default):
    """
    JSONを文字コード違いに強く読み込む。
    UTF-8 / UTF-8 BOM / CP932 / Shift-JIS に対応。
    """
    if not os.path.exists(path):
        return default

    encodings = [
        "utf-8-sig",
        "utf-8",
        "cp932",
        "shift_jis",
    ]

    for encoding in encodings:
        try:
            with open(path, "r", encoding=encoding) as f:
                return json.load(f)

        except UnicodeDecodeError:
            continue

        except json.JSONDecodeError as e:
            print(f"[JSON ERROR] {path}")
            print(f"[ENCODING] {encoding}")
            print(f"[DETAIL] {e}")
            return default

        except Exception as e:
            print(f"[LOAD ERROR] {path}: {e}")
            return default

    print(f"[ENCODING ERROR] 読み込み失敗: {path}")
    return default


def save_json(path, data):
    """
    JSONはUTF-8で統一して保存。
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


def safe_float(val):
    try:
        v = float(val)
        return None if v != v else v
    except:
        return None


def get_volume_ranking(top_n=50):
    """出来高上位N銘柄を取得"""
    import yfinance as yf

    print(f"出来高ランキング取得中（{len(PRIME_TICKERS)}銘柄）…")
    results = []
    batch_size = 20

    for i in range(0, len(PRIME_TICKERS), batch_size):
        batch = PRIME_TICKERS[i:i+batch_size]
        try:
            data = yf.download(
                batch, period="2d", interval="1d",
                auto_adjust=True, progress=False, threads=True
            )
            if "Volume" not in data:
                continue
            vol = data["Volume"].iloc[-1]
            for ticker in batch:
                if ticker in vol.index:
                    v = safe_float(vol[ticker])
                    if v and v > 0:
                        results.append({"ticker": ticker, "volume": v})
        except Exception as e:
            print(f"  バッチエラー {batch[:3]}…: {e}")
        time.sleep(0.5)

    results.sort(key=lambda x: x["volume"], reverse=True)
    top = results[:top_n]
    print(f"出来高上位{len(top)}銘柄を取得しました")
    return [r["ticker"] for r in top]


def compute_chart_score(hist):
    if hist is None or len(hist) < 30:
        return {"total": 0, "details": {}}
    close  = hist["Close"]
    volume = hist["Volume"]
    scores = {}

    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, float("nan"))
    rsi_s = (100 - 100 / (1 + rs)).iloc[-1]
    rsi   = safe_float(rsi_s) or 50.0

    if 30 <= rsi <= 50:   scores["RSI"] = 10
    elif 50 < rsi <= 60:  scores["RSI"] = 7
    elif 20 <= rsi < 30:  scores["RSI"] = 5
    elif rsi < 20:        scores["RSI"] = 8
    else:                 scores["RSI"] = max(0, int(10 - (rsi - 60) * 0.4))

    price = safe_float(close.iloc[-1]) or 0
    ma25  = safe_float(close.rolling(25).mean().iloc[-1])
    ma75  = safe_float(close.rolling(75).mean().iloc[-1])  if len(close) >= 75  else None
    ma200 = safe_float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
    ms = 0
    if ma25  and price > ma25:  ms += 5
    if ma75  and price > ma75:  ms += 5
    if ma200 and price > ma200: ms += 5
    scores["MA配列"] = ms

    vol_ratio = volume.iloc[-10:].mean() / volume.iloc[-30:-10].mean() if volume.iloc[-30:-10].mean() > 0 else 1
    scores["出来高"] = min(10, int(vol_ratio * 7))

    ma20     = close.rolling(20).mean()
    std20    = close.rolling(20).std()
    bl       = safe_float((ma20 - 2 * std20).iloc[-1]) or 0
    bu       = safe_float((ma20 + 2 * std20).iloc[-1]) or 0
    bb_pos   = (price - bl) / (bu - bl) if (bu - bl) > 0 else 0.5
    if bb_pos <= 0.2:   scores["BB"] = 10
    elif bb_pos <= 0.4: scores["BB"] = 7
    elif bb_pos <= 0.6: scores["BB"] = 5
    else:               scores["BB"] = max(0, int(10 - bb_pos * 10))

    hi52 = safe_float(close.rolling(252).max().iloc[-1]) if len(close) >= 252 else safe_float(close.max())
    lo52 = safe_float(close.rolling(252).min().iloc[-1]) if len(close) >= 252 else safe_float(close.min())
    rp   = (price - lo52) / (hi52 - lo52) if (hi52 and lo52 and hi52 - lo52 > 0) else 0.5
    scores["52週位置"] = 5 if rp <= 0.3 else (3 if rp <= 0.5 else 1)

    return {
        "total": sum(scores.values()), "details": scores,
        "rsi": round(rsi, 1), "price": round(price, 1),
        "ma25": round(ma25, 1) if ma25 else None,
        "ma75": round(ma75, 1) if ma75 else None,
        "ma200": round(ma200, 1) if ma200 else None,
        "bb_pos": round(bb_pos * 100, 1),
        "range_pos": round(rp * 100, 1),
    }


def compute_funda_score(info):
    scores = {}
    per = safe_float(info.get("trailingPE") or info.get("forwardPE"))
    scores["PER"] = (10 if per < 15 else 8 if per < 20 else 6 if per < 30 else 4 if per < 40 else 2) if per else 0
    pbr = safe_float(info.get("priceToBook"))
    scores["PBR"] = (10 if pbr < 1 else 8 if pbr < 2 else 6 if pbr < 3 else 4 if pbr < 5 else 2) if pbr else 0
    roe = safe_float(info.get("returnOnEquity"))
    if roe:
        r = roe * 100
        scores["ROE"] = 10 if r >= 20 else 8 if r >= 15 else 6 if r >= 10 else 4 if r >= 5 else 2
    else:
        scores["ROE"] = 0
    rg = safe_float(info.get("revenueGrowth"))
    if rg:
        g = rg * 100
        scores["売上成長"] = 10 if g >= 15 else 8 if g >= 10 else 6 if g >= 5 else 4 if g >= 0 else 1
    else:
        scores["売上成長"] = 0
    dr = safe_float(info.get("dividendRate"))
    cp = safe_float(info.get("currentPrice") or info.get("regularMarketPrice"))
    dy_raw = safe_float(info.get("dividendYield"))
    dy = (dr / cp * 100) if (dr and cp and cp > 0) else (dy_raw * 100 if dy_raw and dy_raw <= 1 else dy_raw)
    scores["配当"] = (5 if dy >= 3 else 4 if dy >= 2 else 3 if dy >= 1 else 2) if dy else 1
    de = safe_float(info.get("debtToEquity"))
    scores["財務"] = (5 if de < 30 else 4 if de < 60 else 3 if de < 100 else 1) if de is not None else 0
    return {
        "total": sum(scores.values()),
        "per": per, "pbr": pbr,
        "roe": round(roe * 100, 1) if roe else None,
        "div_yield": round(dy, 2) if dy else None,
    }


def score_ticker(ticker):
    """1銘柄をスコアリング"""
    import yfinance as yf
    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y")
        info = tk.info
        if hist is None or len(hist) < 30:
            return None
        chart = compute_chart_score(hist)
        funda = compute_funda_score(info)
        total = chart["total"] + funda["total"]
        name  = info.get("shortName") or info.get("longName") or ticker
        price = safe_float(info.get("currentPrice") or info.get("regularMarketPrice")) or 0
        prev  = safe_float(info.get("regularMarketPreviousClose")) or price
        chg_pct = (price - prev) / prev * 100 if prev else 0
        vol   = safe_float(hist["Volume"].iloc[-1]) or 0
        return {
            "ticker":   ticker,
            "name":     name,
            "price":    price,
            "chg_pct":  round(chg_pct, 2),
            "volume":   int(vol),
            "total":    total,
            "funda":    funda,
            "chart":    chart,
        }
    except:
        return None


def call_gemini(prompt, api_key):
    """Gemini APIを呼び出す"""
    import urllib.request, urllib.error
    models = ["gemini-3-flash-preview", "gemini-3.1-flash-lite", "gemini-flash-latest"]
    for model in models:
        try:
            import json as _json
            url  = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            body = _json.dumps({
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
    "temperature": 0.5,
    "maxOutputTokens": 8192
}
            }).encode("utf-8")
            req = urllib.request.Request(url, data=body,
                headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
            with urllib.request.urlopen(req, timeout=30) as res:
                data = _json.loads(res.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except:
            continue
    return "AI予想の生成に失敗しました"


def build_screening_prompt(top10):
    """スクリーニング結果からGeminiプロンプトを構築"""
    stocks_text = ""
    for i, s in enumerate(top10, 1):
        fa = s["funda"]
        ch = s["chart"]
        stocks_text += f"""
{i}. {s['name']}（{s['ticker']}）
   株価: ¥{s['price']:,.0f}（前日比 {s['chg_pct']:+.2f}%）
   出来高: {s['volume']:,}
   総合スコア: {s['total']}/100点
   PER:{fa.get('per','—')}倍 PBR:{fa.get('pbr','—')}倍 ROE:{fa.get('roe','—')}%
   RSI:{ch.get('rsi','—')} MA25:{ch.get('ma25','—')}円 BB位置:{ch.get('bb_pos','—')}%
   52週位置:{ch.get('range_pos','—')}%
"""

    today = datetime.now().strftime("%Y年%m月%d日")
    return f"""あなたは経験豊富な日本株トレーダー兼アナリストです。
本日（{today}）の出来高上位銘柄の中からスコアリングで選出した以下の10銘柄について、
翌営業日〜数日間のトレード予想を提供してください。

## 選出銘柄（出来高上位・スコア順）

{stocks_text}

## 各銘柄について以下の形式で回答してください

【銘柄名（コード）】
- 予想: 上昇/下落/横ばい
- 根拠: 2〜3行でテクニカル・ファンダの観点から
- 注目ポイント: 明日見るべき価格帯や出来高水準
- リスク: 注意すべき点1つ

最後に【総合市場コメント】として今日の出来高動向から読み取れる市場の地合いを3〜4行でまとめてください。
"""


def save_to_github(path, data, token, repo):
    """GitHubにJSONを保存"""
    import base64, urllib.request
    api_url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}", "Content-Type": "application/json"}
    content = base64.b64encode(
        json.dumps(data, ensure_ascii=False, indent=2).encode()
    ).decode()
    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req) as res:
            sha = json.loads(res.read())["sha"]
    except:
        sha = None
    payload = json.dumps({
        "message": f"auto: screening {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": content,
        **({"sha": sha} if sha else {}),
    }).encode()
    req2 = urllib.request.Request(api_url, data=payload, headers=headers, method="PUT")
    urllib.request.urlopen(req2)
    print(f"GitHubに保存しました: {path}")


def run():
    import yfinance as yf

    # 環境変数からキーを取得（GitHub Actions用）
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    github_token = os.environ.get("GITHUB_TOKEN", "")
    github_repo  = os.environ.get("GITHUB_REPO", "perfume9164-afk/stock-tool")

    today = datetime.now().strftime("%Y-%m-%d")
    print(f"=== スクリーニング開始 {today} ===")

    # STEP 1: 出来高上位50銘柄を取得
    top50 = get_volume_ranking(50)
    print(f"出来高上位50銘柄: {top50[:10]}…")

    # STEP 2: スコアリング
    print("スコアリング中…")
    scored = []
    for ticker in top50:
        result = score_ticker(ticker)
        if result:
            scored.append(result)
            print(f"  {ticker}: {result['total']}点")
        time.sleep(0.3)

    # STEP 3: 上位10銘柄を選出
    scored.sort(key=lambda x: x["total"], reverse=True)
    top10 = scored[:10]
    print(f"\n選出10銘柄: {[s['ticker'] for s in top10]}")

    # STEP 4: Geminiでトレード予想生成
    ai_comment = ""
    if gemini_key:
        print("AI予想生成中…")
        prompt = build_screening_prompt(top10)
        ai_comment = call_gemini(prompt, gemini_key)
        print("AI予想生成完了")
    else:
        ai_comment = "GEMINI_API_KEYが設定されていません"

    # STEP 5: 結果を保存
    predictions = load_json(PREDICTIONS_FILE, [])
    new_entry = {
        "date":       today,
        "generated_at": datetime.now().isoformat(),
        "top10":      top10,
        "ai_comment": ai_comment,
        "user_comments": [],  # Fujioさんのコメントを格納
    }

    # 同日分は上書き
    predictions = [p for p in predictions if p.get("date") != today]
    predictions.insert(0, new_entry)
    # 直近30日分のみ保持
    predictions = predictions[:30]

    save_json(PREDICTIONS_FILE, predictions)
    print(f"ローカルに保存: {PREDICTIONS_FILE}")

    # GitHubにも保存
    if github_token:
        try:
            save_to_github(PREDICTIONS_FILE, predictions, github_token, github_repo)
        except Exception as e:
            print(f"GitHub保存エラー: {e}")

    print("\n=== スクリーニング完了 ===")
    print(f"選出銘柄: {[s['name'] for s in top10]}")


if __name__ == "__main__":
    run()
