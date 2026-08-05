"""
毎朝の自動スコア保存スクリプト
実行: python daily_update.py
cronまたはGitHub Actionsで自動実行する
"""

import json
import os
from datetime import datetime

SCORE_HISTORY_FILE = "score_history.json"
WATCHLIST_FILE = "watchlist.json"

DEFAULT_WATCHLIST = {
    "8113.T": "ユニ・チャーム",
    "5243.T": "note",
    "4588.T": "オンコリスバイオ",
    "6702.T": "富士通",
    "5016.T": "JX金属",
}


def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def compute_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, float("nan"))
    return 100 - 100 / (1 + rs)


def score_chart(hist):
    if hist is None or len(hist) < 30:
        return 0

    close  = hist["Close"]
    volume = hist["Volume"]
    price  = close.iloc[-1]
    scores = {}

    # RSI
    rsi = compute_rsi(close).iloc[-1]
    if 30 <= rsi <= 50:   scores["rsi"] = 10
    elif 50 < rsi <= 60:  scores["rsi"] = 7
    elif rsi < 30:        scores["rsi"] = 8
    else:                 scores["rsi"] = max(0, int(10 - (rsi - 60) * 0.4))

    # MA配列
    ma25  = close.rolling(25).mean().iloc[-1]
    ma75  = close.rolling(75).mean().iloc[-1] if len(close) >= 75 else None
    ma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None
    ms = 0
    if price > ma25: ms += 5
    if ma75 and price > ma75: ms += 5
    if ma200 and price > ma200: ms += 5
    scores["ma"] = ms

    # 出来高
    vr = volume.iloc[-10:].mean() / volume.iloc[-30:-10].mean()
    scores["vol"] = min(10, int(vr * 7))

    # BB
    ma20  = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    bl = (ma20 - 2 * std20).iloc[-1]
    bu = (ma20 + 2 * std20).iloc[-1]
    bp = (price - bl) / (bu - bl) if (bu - bl) > 0 else 0.5
    if bp <= 0.2:   scores["bb"] = 10
    elif bp <= 0.4: scores["bb"] = 7
    elif bp <= 0.6: scores["bb"] = 5
    else:           scores["bb"] = max(0, int(10 - bp * 10))

    # 52週
    hi = close.rolling(252).max().iloc[-1] if len(close) >= 252 else close.max()
    lo = close.rolling(252).min().iloc[-1] if len(close) >= 252 else close.min()
    rp = (price - lo) / (hi - lo) if (hi - lo) > 0 else 0.5
    scores["range"] = 5 if rp <= 0.3 else (3 if rp <= 0.5 else 1)

    return sum(scores.values())


def score_funda(info):
    scores = {}

    per = info.get("trailingPE") or info.get("forwardPE")
    if per:
        scores["per"] = 10 if per < 15 else 8 if per < 20 else 6 if per < 30 else 4 if per < 40 else 2
    else:
        scores["per"] = 0

    pbr = info.get("priceToBook")
    if pbr:
        scores["pbr"] = 10 if pbr < 1 else 8 if pbr < 2 else 6 if pbr < 3 else 4 if pbr < 5 else 2
    else:
        scores["pbr"] = 0

    roe = info.get("returnOnEquity")
    if roe:
        r = roe * 100
        scores["roe"] = 10 if r >= 20 else 8 if r >= 15 else 6 if r >= 10 else 4 if r >= 5 else 2
    else:
        scores["roe"] = 0

    rg = info.get("revenueGrowth")
    if rg:
        g = rg * 100
        scores["rev"] = 10 if g >= 15 else 8 if g >= 10 else 6 if g >= 5 else 4 if g >= 0 else 1
    else:
        scores["rev"] = 0

    dy = info.get("dividendYield")
    if dy:
        d = dy * 100
        scores["div"] = 5 if d >= 3 else 4 if d >= 2 else 3 if d >= 1 else 2
    else:
        scores["div"] = 1

    de = info.get("debtToEquity")
    if de is not None:
        scores["debt"] = 5 if de < 30 else 4 if de < 60 else 3 if de < 100 else 1
    else:
        scores["debt"] = 0

    return sum(scores.values())


def run():
    import yfinance as yf

    watchlist = load_json(WATCHLIST_FILE, DEFAULT_WATCHLIST)
    history   = load_json(SCORE_HISTORY_FILE, {})
    today     = datetime.now().strftime("%Y-%m-%d")

    print(f"=== 日次スコア更新 {today} ===")

    for ticker, name in watchlist.items():
        try:
            tk   = yf.Ticker(ticker)
            hist = tk.history(period="2y")
            info = tk.info

            c_score = score_chart(hist)
            f_score = score_funda(info)
            total   = c_score + f_score
            price   = info.get("currentPrice") or info.get("regularMarketPrice", 0)

            if ticker not in history:
                history[ticker] = []

            # 同日分は上書き
            history[ticker] = [h for h in history[ticker] if h.get("date") != today]
            history[ticker].append({
                "date":  today,
                "total": total,
                "funda": f_score,
                "chart": c_score,
                "price": price,
                "note":  "auto",
            })
            print(f"  ✅ {name}（{ticker}）: {total}点（F:{f_score} C:{c_score}）株価:{price}")

        except Exception as e:
            print(f"  ❌ {name}（{ticker}）: {e}")

    save_json(SCORE_HISTORY_FILE, history)
    print("保存完了 → score_history.json")


if __name__ == "__main__":
    run()
