"""毎営業日の出来高TOP50スキャナー
固定300銘柄 → yfinance出来高 → TOP50 → スコア → Gemini TOP10。
"""
import json, os, math
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pandas as pd
import yfinance as yf

JST = timezone(timedelta(hours=9))
OUTPUT = Path("data/ai_predictions.json")
TICKERS = [c + ".T" for c in ['1301', '1332', '1333', '1605', '1721', '1801', '1802', '1803', '1808', '1812', '1925', '1928', '1963', '2002', '2267', '2269', '2282', '2502', '2503', '2531', '2768', '2801', '2802', '2871', '2914', '3003', '3038', '3086', '3092', '3101', '3103', '3105', '3116', '3141', '3197', '3289', '3291', '3382', '3401', '3402', '3405', '3407', '3436', '3861', '3863', '4004', '4005', '4021', '4042', '4043', '4044', '4045', '4061', '4062', '4063', '4088', '4091', '4114', '4183', '4188', '4202', '4203', '4204', '4205', '4206', '4208', '4212', '4272', '4307', '4324', '4452', '4502', '4503', '4506', '4507', '4519', '4523', '4528', '4530', '4543', '4568', '4578', '4612', '4631', '4633', '4661', '4680', '4681', '4704', '4716', '4732', '4751', '4755', '4901', '4902', '4911', '4912', '4927', '5020', '5021', '5101', '5105', '5108', '5201', '5202', '5214', '5232', '5233', '5301', '5332', '5333', '5334', '5401', '5406', '5411', '5541', '5631', '5703', '5711', '5713', '5801', '5802', '5803', '5831', '5901', '6098', '6103', '6113', '6134', '6141', '6146', '6178', '6301', '6302', '6305', '6326', '6361', '6367', '6370', '6383', '6406', '6417', '6471', '6472', '6473', '6501', '6503', '6504', '6506', '6508', '6516', '6526', '6594', '6645', '6674', '6701', '6702', '6724', '6752', '6758', '6762', '6770', '6841', '6845', '6857', '6861', '6869', '6871', '6920', '6923', '6952', '6954', '6963', '6971', '6981', '7003', '7011', '7012', '7013', '7201', '7202', '7203', '7205', '7211', '7267', '7269', '7270', '7272', '7276', '7282', '7283', '7309', '7313', '7453', '7459', '7701', '7731', '7733', '7735', '7739', '7741', '7751', '7832', '7911', '7912', '7951', '8001', '8002', '8015', '8031', '8035', '8053', '8058', '8233', '8252', '8253', '8267', '8273', '8304', '8306', '8308', '8309', '8316', '8331', '8354', '8355', '8411', '8418', '8473', '8591', '8601', '8604', '8630', '8697', '8725', '8750', '8766', '8795', '8801', '8802', '8830', '9001', '9005', '9007', '9008', '9009', '9020', '9021', '9022', '9064', '9101', '9104', '9107', '9147', '9432', '9433', '9434', '9435', '9501', '9502', '9503', '9504', '9602', '9613', '9684', '9697', '9719', '9735', '9744', '9766', '9843', '9983', '9984', '1334', '1662', '1893', '1944', '2121', '2154', '2206', '2331', '2413', '2427', '2730', '2733', '2784', '2788', '2897', '3028', '3048', '3050', '3064', '3167', '3186', '3201', '3231', '3254', '3276', '3288', '3391']]

def sf(v):
    try:
        v = float(v)
        return None if math.isnan(v) else v
    except Exception:
        return None

def chart_score(hist):
    if hist is None or len(hist) < 30:
        return {"total": 0, "rsi": None, "range_pos": None}
    close = hist["Close"].astype(float)
    vol = hist["Volume"].astype(float)
    d = close.diff()
    gain = d.clip(lower=0).rolling(14).mean()
    loss = (-d.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, float("nan"))
    rsi = sf((100 - 100 / (1 + rs)).iloc[-1]) or 50
    price = sf(close.iloc[-1]) or 0
    ma25 = sf(close.rolling(25).mean().iloc[-1])
    ma75 = sf(close.rolling(75).mean().iloc[-1])
    ma200 = sf(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
    ma_score = sum([
        5 if ma25 and price > ma25 else 0,
        5 if ma75 and price > ma75 else 0,
        5 if ma200 and price > ma200 else 0,
    ])
    rsi_score = 10 if 30 <= rsi <= 50 else 7 if 50 < rsi <= 60 else 5 if 20 <= rsi < 30 else 8 if rsi < 20 else max(0, int(10 - (rsi - 60) * .4))
    avg_old = vol.iloc[-30:-10].mean()
    vr = vol.iloc[-10:].mean() / avg_old if avg_old > 0 else 1
    vol_score = min(10, int(vr * 7))
    ma20 = close.rolling(20).mean()
    sd = close.rolling(20).std()
    upper = ma20 + 2 * sd
    lower = ma20 - 2 * sd
    width = upper.iloc[-1] - lower.iloc[-1]
    bb = (price - lower.iloc[-1]) / width if width > 0 else .5
    bb_score = 10 if bb <= .2 else 7 if bb <= .4 else 5 if bb <= .6 else max(0, int(10 - bb * 10))
    hi = close.rolling(252).max().iloc[-1] if len(close) >= 252 else close.max()
    lo = close.rolling(252).min().iloc[-1] if len(close) >= 252 else close.min()
    rp = (price - lo) / (hi - lo) if hi and hi - lo > 0 else .5
    range_score = 5 if rp <= .3 else 3 if rp <= .5 else 1
    return {"total": int(ma_score + rsi_score + vol_score + bb_score + range_score),
            "rsi": round(rsi, 1), "range_pos": round(rp * 100, 1),
            "volume_ratio": round(vr, 2)}

def funda_score(info):
    per = sf(info.get("trailingPE") or info.get("forwardPE"))
    pbr = sf(info.get("priceToBook"))
    roe = sf(info.get("returnOnEquity"))
    rg = sf(info.get("revenueGrowth"))
    de = sf(info.get("debtToEquity"))
    ps = (10 if per < 15 else 8 if per < 20 else 6 if per < 30 else 4 if per < 40 else 2) if per else 0
    bs = (10 if pbr < 1 else 8 if pbr < 2 else 6 if pbr < 3 else 4 if pbr < 5 else 2) if pbr else 0
    rs = (10 if roe * 100 >= 20 else 8 if roe * 100 >= 15 else 6 if roe * 100 >= 10 else 4 if roe * 100 >= 5 else 2) if roe else 0
    gs = (10 if rg * 100 >= 15 else 8 if rg * 100 >= 10 else 6 if rg * 100 >= 5 else 4 if rg * 100 >= 0 else 1) if rg else 0
    dy = sf(info.get("dividendYield"))
    dy = (dy * 100 if dy is not None and dy <= 1 else dy) if dy is not None else None
    ds = 5 if dy is not None and dy >= 3 else 4 if dy is not None and dy >= 2 else 3 if dy is not None and dy >= 1 else 2 if dy is not None else 1
    fs = (5 if de < 30 else 4 if de < 60 else 3 if de < 100 else 1) if de is not None else 0
    return {"total": int(ps + bs + rs + gs + ds + fs), "per": per, "pbr": pbr,
            "roe": round(roe * 100, 1) if roe else None,
            "div_yield": round(dy, 2) if dy is not None else None}

def get_volume_ranking():
    raw = yf.download(TICKERS, period="5d", interval="1d", auto_adjust=False,
                      progress=False, threads=True, group_by="column")
    if raw.empty:
        raise RuntimeError("yfinanceから出来高データを取得できませんでした")
    rows = []
    if isinstance(raw.columns, pd.MultiIndex):
        volumes = raw["Volume"]
        closes = raw["Close"] if "Close" in raw.columns.get_level_values(0) else None
        for t in TICKERS:
            if t not in volumes.columns:
                continue
            vv = volumes[t].dropna()
            v = sf(vv.iloc[-1]) if len(vv) else None
            if not v:
                continue
            avg = sf(vv.iloc[-21:-1].mean()) or v
            price = sf(closes[t].dropna().iloc[-1]) if closes is not None and t in closes.columns else None
            rows.append((t, v, price, v / avg if avg else 1))
    return sorted(rows, key=lambda x: x[1], reverse=True)[:50]

def detailed(top50):
    out = []
    for rank, (ticker, volume, close, ratio) in enumerate(top50, 1):
        try:
            tk = yf.Ticker(ticker)
            hist = tk.history(period="2y", auto_adjust=False)
            info = tk.get_info()
            fa = funda_score(info)
            ch = chart_score(hist)
            total = fa["total"] + ch["total"]
            out.append({
                "volume_rank": rank, "ticker": ticker,
                "name": info.get("longName") or info.get("shortName") or ticker,
                "price": sf(close) or sf(info.get("currentPrice")),
                "volume": int(volume), "volume_ratio": round(ratio, 2),
                "funda_score": fa["total"], "chart_score": ch["total"], "total_score": total,
                "rsi": ch["rsi"], "range_pos": ch["range_pos"],
                "per": fa["per"], "pbr": fa["pbr"], "roe": fa["roe"], "div_yield": fa["div_yield"]
            })
        except Exception as e:
            out.append({"volume_rank": rank, "ticker": ticker, "name": ticker,
                        "price": close, "volume": int(volume), "volume_ratio": round(ratio, 2),
                        "funda_score": 0, "chart_score": 0, "total_score": 0,
                        "rsi": None, "range_pos": None, "error": str(e)})
    return sorted(out, key=lambda x: x.get("total_score", 0), reverse=True)

def gemini_top10(candidates):
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return []
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        fields = ["ticker", "name", "volume_rank", "volume_ratio", "total_score", "funda_score", "chart_score", "rsi", "range_pos", "per", "pbr", "roe", "div_yield"]
        compact = [{k: x.get(k) for k in fields} for x in candidates]
        prompt = """あなたは日本株の中長期投資アナリストです。以下は引け後に抽出した出来高上位50銘柄です。総合スコア、ファンダ、チャート、出来高急増率、RSI、52週位置を重視し、翌営業日から数日〜数週間の監視優先度が高い10銘柄を選んでください。短期的な出来高だけでなく、過熱しすぎていないか、ファンダの裏付けがあるかも評価してください。JSON配列だけを返してください。各要素は rank,ticker,reason,verdict を持たせてください。verdictは「強買い」「買い」「注目」「様子見」のいずれか。\n\n""" + json.dumps(compact, ensure_ascii=False)
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = resp.text.strip().replace("```json", "").replace("```", "")
        arr = json.loads(text)
        by = {x["ticker"]: x for x in candidates}
        result = []
        for a in arr[:10]:
            if a.get("ticker") in by:
                x = by[a["ticker"]].copy()
                x.update({"ai_rank": a.get("rank"), "reason": a.get("reason", ""), "verdict": a.get("verdict", "注目")})
                result.append(x)
        return result
    except Exception as e:
        print("Gemini error:", e)
        return []

def main():
    top50 = get_volume_ranking()
    candidates = detailed(top50)
    ai = gemini_top10(candidates)
    if not ai:
        ai = [dict(x, ai_rank=i + 1, reason="総合スコア上位のフォールバック",
                   verdict="注目" if x["total_score"] < 65 else "買い")
              for i, x in enumerate(candidates[:10])]
    now = datetime.now(JST)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {"date": now.strftime("%Y-%m-%d"),
               "generated_at": now.strftime("%Y-%m-%d %H:%M JST"),
               "universe_size": len(TICKERS), "top50": candidates, "ai_top10": ai}
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved {OUTPUT}: TOP50={len(candidates)}, AI TOP10={len(ai)}")

if __name__ == "__main__":
    main()
