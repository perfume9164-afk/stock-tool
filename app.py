"""
日本株 AI スコアボード v4
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
import os

st.set_page_config(
    page_title="日本株スコアボード",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Noto+Sans+JP:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; }
.main-header {
    background: linear-gradient(135deg, #0a0f1e 0%, #0d1f3c 100%);
    border-bottom: 1px solid #1e3a5f; padding: 1.5rem 2rem;
    margin: -1rem -1rem 2rem -1rem; border-radius: 0 0 12px 12px;
}
.main-header h1 { font-family:'IBM Plex Mono',monospace; color:#e8f4ff; font-size:1.6rem; font-weight:600; letter-spacing:-0.02em; margin:0; }
.main-header .subtitle { color:#4a7fa5; font-size:0.8rem; font-family:'IBM Plex Mono',monospace; margin-top:0.3rem; }
.market-panel { background:#060d1a; border:1px solid #1e3a5f; border-radius:12px; padding:1.2rem 1.6rem; margin-bottom:1.5rem; }
.market-panel-title { font-family:'IBM Plex Mono',monospace; font-size:0.65rem; color:#4a7fa5; letter-spacing:0.15em; text-transform:uppercase; margin-bottom:1rem; border-bottom:1px solid #1e3a5f; padding-bottom:0.4rem; }
.market-index-card { background:#0d1f3c; border:1px solid #1e3a5f; border-radius:8px; padding:0.8rem 1rem; }
.market-verdict-good { color:#00e5a0; font-weight:700; }
.market-verdict-caution { color:#ffd54f; font-weight:700; }
.market-verdict-bad { color:#ef5350; font-weight:700; }
.score-card { background:#0d1f3c; border:1px solid #1e3a5f; border-radius:10px; padding:1.2rem 1.4rem; margin-bottom:0.8rem; }
.score-badge { font-family:'IBM Plex Mono',monospace; font-size:2.2rem; font-weight:600; line-height:1; }
.score-strong-buy { color:#00e5a0; } .score-buy { color:#4fc3f7; } .score-watch { color:#ffd54f; } .score-pass { color:#ef5350; }
.ticker-label { font-family:'IBM Plex Mono',monospace; font-size:0.75rem; color:#4a7fa5; letter-spacing:0.08em; }
.company-name { font-size:1rem; font-weight:700; color:#e8f4ff; margin:0.15rem 0; }
.price-display { font-family:'IBM Plex Mono',monospace; font-size:1.1rem; color:#e8f4ff; }
.price-change-pos { color:#00e5a0; } .price-change-neg { color:#ef5350; }
.metric-row { display:flex; gap:0.5rem; flex-wrap:wrap; margin-top:0.7rem; }
.metric-pill { background:#0a0f1e; border:1px solid #1e3a5f; border-radius:4px; padding:0.2rem 0.6rem; font-family:'IBM Plex Mono',monospace; font-size:0.7rem; color:#7fb3d3; }
.verdict { display:inline-block; padding:0.2rem 0.7rem; border-radius:4px; font-size:0.7rem; font-weight:700; letter-spacing:0.06em; font-family:'IBM Plex Mono',monospace; }
.verdict-sb { background:#003d28; color:#00e5a0; border:1px solid #00e5a0; }
.verdict-b  { background:#003366; color:#4fc3f7; border:1px solid #4fc3f7; }
.verdict-w  { background:#3d2e00; color:#ffd54f; border:1px solid #ffd54f; }
.verdict-p  { background:#3d0000; color:#ef5350; border:1px solid #ef5350; }
.section-head { font-family:'IBM Plex Mono',monospace; font-size:0.65rem; color:#4a7fa5; letter-spacing:0.15em; text-transform:uppercase; border-bottom:1px solid #1e3a5f; padding-bottom:0.4rem; margin-bottom:1rem; }
.journal-card { background:#0d1f3c; border:1px solid #1e3a5f; border-radius:10px; padding:1rem 1.2rem; margin-bottom:0.6rem; }
.journal-ticker { font-family:'IBM Plex Mono',monospace; font-size:0.7rem; color:#4a7fa5; }
.journal-comment { font-size:0.9rem; color:#e8f4ff; margin:0.3rem 0; }
.journal-meta { font-family:'IBM Plex Mono',monospace; font-size:0.7rem; color:#7fb3d3; }
.confidence-star { color:#ffd54f; }
.price-line-in   { color:#00e5a0; font-family:'IBM Plex Mono',monospace; font-size:0.75rem; }
.price-line-stop { color:#ef5350; font-family:'IBM Plex Mono',monospace; font-size:0.75rem; }
.price-line-tgt  { color:#4fc3f7; font-family:'IBM Plex Mono',monospace; font-size:0.75rem; }
section[data-testid="stSidebar"] { background:#0a0f1e; border-right:1px solid #1e3a5f; }
[data-testid="metric-container"] { background:#0d1f3c; border:1px solid #1e3a5f; border-radius:8px; padding:0.8rem; }
</style>
""", unsafe_allow_html=True)

# ─── ファイル管理 ──────────────────────────────────────────────
SCORE_HISTORY_FILE = "score_history.json"
WATCHLIST_FILE     = "watchlist.json"
JOURNAL_FILE       = "journal.json"

DEFAULT_WATCHLIST = {
    "8113.T": "ユニ・チャーム",
    "5243.T": "note",
    "4588.T": "オンコリスバイオ",
    "6702.T": "富士通",
    "5016.T": "JX金属",
}

MARKET_INDICES = {
    "^N225":  {"name": "日経平均",  "emoji": "🗾"},
    "1306.T": {"name": "TOPIX ETF", "emoji": "📊"},
    "JPY=X":  {"name": "ドル円",    "emoji": "💱"},
}

# 日本語名マスタ（yfinanceが英語を返す場合の補完用）
JP_NAME_MASTER = {
    "7203.T": "トヨタ自動車",
    "6758.T": "ソニーグループ",
    "9984.T": "ソフトバンクグループ",
    "8306.T": "三菱UFJフィナンシャル・グループ",
    "6861.T": "キーエンス",
    "9432.T": "NTT",
    "7974.T": "任天堂",
    "4063.T": "信越化学工業",
    "8035.T": "東京エレクトロン",
    "6098.T": "リクルートホールディングス",
    "9983.T": "ファーストリテイリング",
    "4661.T": "オリエンタルランド",
    "6367.T": "ダイキン工業",
    "7741.T": "HOYA",
    "2914.T": "日本たばこ産業",
}

def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_watchlist():  return load_json(WATCHLIST_FILE, DEFAULT_WATCHLIST)
def save_watchlist(d): save_json(WATCHLIST_FILE, d)
def load_history():    return load_json(SCORE_HISTORY_FILE, {})
def save_history(d):   save_json(SCORE_HISTORY_FILE, d)
def load_journal():    return load_json(JOURNAL_FILE, [])
def save_journal(d):   save_json(JOURNAL_FILE, d)

# ─── スコアリング ──────────────────────────────────────────────
def safe_float(val):
    try:
        v = float(val)
        return None if (v != v) else v
    except:
        return None

def compute_chart_score(hist):
    if hist is None or len(hist) < 30:
        return {"total": 0, "details": {}, "error": "データ不足"}
    close  = hist["Close"]
    volume = hist["Volume"]
    scores = {}

    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, float("nan"))
    rsi   = safe_float((100 - 100 / (1 + rs)).iloc[-1]) or 50.0

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
    bb_lower = safe_float((ma20 - 2 * std20).iloc[-1]) or 0
    bb_upper = safe_float((ma20 + 2 * std20).iloc[-1]) or 0
    bb_pos   = (price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5
    if bb_pos <= 0.2:   scores["BB"] = 10
    elif bb_pos <= 0.4: scores["BB"] = 7
    elif bb_pos <= 0.6: scores["BB"] = 5
    else:               scores["BB"] = max(0, int(10 - bb_pos * 10))

    hi52      = safe_float(close.rolling(252).max().iloc[-1]) if len(close) >= 252 else safe_float(close.max())
    lo52      = safe_float(close.rolling(252).min().iloc[-1]) if len(close) >= 252 else safe_float(close.min())
    range_pos = (price - lo52) / (hi52 - lo52) if (hi52 and lo52 and hi52 - lo52 > 0) else 0.5
    scores["52週位置"] = 5 if range_pos <= 0.3 else (3 if range_pos <= 0.5 else 1)

    return {
        "total": sum(scores.values()), "details": scores,
        "rsi": round(rsi, 1),
        "ma25": round(ma25, 1) if ma25 else None,
        "ma75": round(ma75, 1) if ma75 else None,
        "ma200": round(ma200, 1) if ma200 else None,
        "bb_pos": round(bb_pos * 100, 1),
        "range_pos": round(range_pos * 100, 1),
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
    dy = safe_float(info.get("dividendYield"))
    if dy:
        d = dy * 100
        scores["配当"] = 5 if d >= 3 else 4 if d >= 2 else 3 if d >= 1 else 2
    else:
        scores["配当"] = 1
    de = safe_float(info.get("debtToEquity"))
    scores["財務"] = (5 if de < 30 else 4 if de < 60 else 3 if de < 100 else 1) if de is not None else 0
    return {
        "total": sum(scores.values()), "details": scores,
        "per": per, "pbr": pbr,
        "roe": round(roe * 100, 1) if roe else None,
        "rev_growth": round(rg * 100, 1) if rg else None,
        "div_yield": round(dy * 100, 2) if dy else None,
    }

def compute_market_chart_score(hist, ticker):
    if hist is None or len(hist) < 30:
        return {"total": 0, "trend": "—", "rsi": None, "chg_pct": None, "price": None}
    close   = hist["Close"]
    price   = safe_float(close.iloc[-1]) or 0
    prev    = safe_float(close.iloc[-2]) if len(close) >= 2 else price
    chg_pct = (price - prev) / prev * 100 if prev and prev != 0 else 0
    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, float("nan"))
    rsi   = safe_float((100 - 100 / (1 + rs)).iloc[-1]) or 50.0
    ma25  = safe_float(close.rolling(25).mean().iloc[-1])
    ma75  = safe_float(close.rolling(75).mean().iloc[-1])  if len(close) >= 75  else None
    ma200 = safe_float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
    if ticker == "JPY=X":
        score = 8 if 140 <= price <= 155 else 5 if 130 <= price < 140 else 3
        trend = "適正" if 140 <= price <= 155 else "円高" if price < 140 else "円安"
    else:
        ma_ok = sum([1 if (ma25 and price > ma25) else 0, 1 if (ma75 and price > ma75) else 0, 1 if (ma200 and price > ma200) else 0])
        score = ma_ok * 3 + (1 if 40 <= rsi <= 65 else 0)
        trend = "上昇トレンド" if ma_ok >= 2 else "調整中" if ma_ok == 1 else "下降トレンド"
    return {"total": score, "trend": trend, "rsi": round(rsi, 1), "chg_pct": round(chg_pct, 2), "price": price}

def market_environment_verdict(scores):
    total = sum(s.get("total", 0) for s in scores.values())
    if total >= 20:   return "買い場", "market-verdict-good"
    elif total >= 12: return "中立",   "market-verdict-caution"
    else:             return "慎重",   "market-verdict-bad"

def verdict(score):
    if score >= 80: return "強買い", "score-strong-buy", "verdict-sb"
    if score >= 65: return "買い",   "score-buy",        "verdict-b"
    if score >= 50: return "様子見", "score-watch",      "verdict-w"
    return "見送り", "score-pass", "verdict-p"

@st.cache_data(ttl=3600)
def fetch_stock_data(ticker):
    try:
        import yfinance as yf
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y")
        info = tk.info
        return hist, info, None
    except ImportError:
        return None, {}, "yfinanceが見つかりません"
    except Exception as e:
        return None, {}, str(e)

@st.cache_data(ttl=1800)
def fetch_market_indices():
    import yfinance as yf
    results = {}
    for ticker in MARKET_INDICES:
        try:
            tk   = yf.Ticker(ticker)
            hist = tk.history(period="1y", auto_adjust=True)
            info = tk.fast_info
            latest     = getattr(info, "last_price", None)
            prev_close = getattr(info, "previous_close", None)
            if latest and prev_close and not hist.empty and len(hist) >= 2:
                hist.loc[hist.index[-2], "Close"] = prev_close
                hist.loc[hist.index[-1], "Close"] = latest
            results[ticker] = compute_market_chart_score(hist, ticker)
        except:
            results[ticker] = {"total": 0, "trend": "取得失敗", "chg_pct": None, "price": None}
    return results

@st.cache_data(ttl=86400)
def get_company_name(ticker):
    """Yahoo!ファイナンス日本版から日本語銘柄名を取得"""
    if ticker in JP_NAME_MASTER:
        return JP_NAME_MASTER[ticker]
    try:
        import urllib.request
        code = ticker.replace(".T", "")
        url  = f"https://finance.yahoo.co.jp/quote/{code}.T"
        req  = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as res:
            html = res.read().decode("utf-8")
        # <title>銘柄名 【証券コード】...</title> から抽出
        import re
        m = re.search(r"<title>([^【\(（]+)", html)
        if m:
            name = m.group(1).strip()
            if name and len(name) > 1:
                return name
    except:
        pass
    # フォールバック：yfinance
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info
        return info.get("shortName") or info.get("longName") or ticker
    except:
        return ticker

def score_stock(ticker, name):
    hist, info, err = fetch_stock_data(ticker)
    if err:
        return {"ticker": ticker, "name": name, "error": err}
    chart = compute_chart_score(hist)
    funda = compute_funda_score(info)
    total = chart["total"] + funda["total"]
    label, score_cls, verdict_cls = verdict(total)
    price   = safe_float(info.get("currentPrice") or info.get("regularMarketPrice")) or 0
    prev    = safe_float(info.get("regularMarketPreviousClose")) or price
    chg     = price - prev
    chg_pct = chg / prev * 100 if prev else 0
    return {
        "ticker": ticker, "name": name,
        "price": price, "chg": chg, "chg_pct": chg_pct,
        "total": total, "funda": funda, "chart": chart,
        "label": label, "score_cls": score_cls, "verdict_cls": verdict_cls,
        "updated_at": datetime.now().isoformat(),
    }

# ─── UI ───────────────────────────────────────────────────────
def render_market_panel(market_scores):
    env_label, env_cls = market_environment_verdict(market_scores)
    st.markdown(f"""
    <div class="market-panel">
      <div class="market-panel-title">🌐 市場環境スコア &nbsp;｜&nbsp; <span class="{env_cls}">総合判定：{env_label}</span></div>
    </div>
    """, unsafe_allow_html=True)
    cols = st.columns(len(MARKET_INDICES))
    for i, (ticker, meta) in enumerate(MARKET_INDICES.items()):
        s         = market_scores.get(ticker, {})
        price     = s.get("price")
        chg_pct   = s.get("chg_pct")
        trend     = s.get("trend", "—")
        price_str = f"{price:,.1f}" if price else "—"
        chg_str   = f"{chg_pct:+.2f}%" if chg_pct is not None else "—"
        chg_color = "#00e5a0" if (chg_pct or 0) >= 0 else "#ef5350"
        with cols[i]:
            st.markdown(f"""
            <div class="market-index-card">
              <div style="font-size:0.65rem;color:#4a7fa5;font-family:'IBM Plex Mono',monospace;">{meta['emoji']} {meta['name']}</div>
              <div style="font-family:'IBM Plex Mono',monospace;font-size:1.1rem;color:#e8f4ff;margin:0.3rem 0;">{price_str}</div>
              <div style="font-size:0.75rem;color:{chg_color};font-family:'IBM Plex Mono',monospace;">{chg_str}</div>
              <div style="margin-top:0.5rem;font-size:0.7rem;color:#7fb3d3;">{trend}</div>
            </div>
            """, unsafe_allow_html=True)

def render_watchlist_manager(watchlist):
    st.markdown('<div class="section-head">銘柄追加</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        code = st.text_input("証券コード", placeholder="例: 7203", label_visibility="collapsed").strip()
    with col2:
        add_btn = st.button("追加", use_container_width=True, type="primary")
    if add_btn and code:
        ticker = code + ".T" if not code.endswith(".T") else code
        if ticker in watchlist:
            st.warning("すでに追加済みです")
        else:
            with st.spinner("銘柄情報を取得中…"):
                name = get_company_name(ticker)
            watchlist[ticker] = name
            save_watchlist(watchlist)
            st.cache_data.clear()
            st.success(f"✅ {name} を追加しました")
            st.rerun()

def render_card_with_delete(r, watchlist):
    if "error" in r:
        col1, col2 = st.columns([10, 1])
        with col1:
            st.error(f"**{r['name']}（{r['ticker']}）** — {r['error']}")
        with col2:
            if st.button("✕", key=f"del_{r['ticker']}"):
                del watchlist[r["ticker"]]
                save_watchlist(watchlist)
                st.rerun()
        return

    chg_cls  = "price-change-pos" if r["chg"] >= 0 else "price-change-neg"
    chg_sign = "+" if r["chg"] >= 0 else ""
    v_label, _, v_cls = verdict(r["total"])
    fa = r["funda"]
    ch = r["chart"]
    per_str = f"PER {fa['per']:.1f}x"       if fa.get("per")       else "PER —"
    pbr_str = f"PBR {fa['pbr']:.2f}x"       if fa.get("pbr")       else "PBR —"
    roe_str = f"ROE {fa['roe']:.1f}%"        if fa.get("roe")       else "ROE —"
    rsi_str = f"RSI {ch.get('rsi','—')}"
    rng_str = f"52W {ch.get('range_pos','—')}%"
    div_str = f"配当 {fa['div_yield']:.2f}%" if fa.get("div_yield") else "配当 —"

    card_col, del_col = st.columns([12, 1])
    with card_col:
        st.markdown(f"""
        <div class="score-card">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
              <div class="ticker-label">{r['ticker']}</div>
              <div class="company-name">{r['name']}</div>
              <div class="price-display">¥{r['price']:,.0f}&nbsp;<span class="{chg_cls}">{chg_sign}{r['chg']:,.0f}（{chg_sign}{r['chg_pct']:.2f}%）</span></div>
            </div>
            <div style="text-align:right;">
              <div class="score-badge {r['score_cls']}">{r['total']}</div>
              <div style="font-family:'IBM Plex Mono',monospace;font-size:0.65rem;color:#4a7fa5;margin-top:0.2rem;">/ 100点</div>
              <div style="margin-top:0.4rem;"><span class="verdict {v_cls}">{v_label}</span></div>
            </div>
          </div>
          <div style="display:flex;gap:0.8rem;margin-top:0.8rem;">
            <div style="flex:1;background:#0a0f1e;border-radius:6px;padding:0.5rem 0.8rem;">
              <div style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;color:#4a7fa5;margin-bottom:0.3rem;">FUNDA {fa['total']}/50</div>
              <div style="background:#1e3a5f;border-radius:3px;height:6px;"><div style="background:#4fc3f7;width:{fa['total']*2}%;height:6px;border-radius:3px;"></div></div>
            </div>
            <div style="flex:1;background:#0a0f1e;border-radius:6px;padding:0.5rem 0.8rem;">
              <div style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;color:#4a7fa5;margin-bottom:0.3rem;">CHART {ch['total']}/50</div>
              <div style="background:#1e3a5f;border-radius:3px;height:6px;"><div style="background:#00e5a0;width:{ch['total']*2}%;height:6px;border-radius:3px;"></div></div>
            </div>
          </div>
          <div class="metric-row">
            <div class="metric-pill">{per_str}</div><div class="metric-pill">{pbr_str}</div>
            <div class="metric-pill">{roe_str}</div><div class="metric-pill">{rsi_str}</div>
            <div class="metric-pill">{rng_str}</div><div class="metric-pill">{div_str}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with del_col:
        st.markdown("<div style='margin-top:1.2rem;'></div>", unsafe_allow_html=True)
        if st.button("✕", key=f"del_{r['ticker']}", help=f"{r['name']}を削除"):
            del watchlist[r["ticker"]]
            save_watchlist(watchlist)
            st.cache_data.clear()
            st.rerun()

def render_detail(r):
    if "error" in r:
        return
    st.markdown(f'<div class="section-head">詳細分析 — {r["name"]}</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**📊 ファンダスコア内訳**")
        fa_df = pd.DataFrame(list(r["funda"]["details"].items()), columns=["指標", "スコア"])
        fig = px.bar(fa_df, x="スコア", y="指標", orientation="h",
                     color="スコア", color_continuous_scale=["#ef5350","#ffd54f","#00e5a0"], range_color=[0,10])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#e8f4ff", margin=dict(l=0,r=0,t=10,b=0), height=220, showlegend=False, coloraxis_showscale=False)
        fig.update_xaxes(gridcolor="#1e3a5f", range=[0,10])
        fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("**📈 チャートスコア内訳**")
        ch_df = pd.DataFrame(list(r["chart"]["details"].items()), columns=["指標", "スコア"])
        fig2 = px.bar(ch_df, x="スコア", y="指標", orientation="h",
                      color="スコア", color_continuous_scale=["#ef5350","#ffd54f","#00e5a0"], range_color=[0,10])
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="#e8f4ff", margin=dict(l=0,r=0,t=10,b=0), height=220, showlegend=False, coloraxis_showscale=False)
        fig2.update_xaxes(gridcolor="#1e3a5f", range=[0,15])
        fig2.update_yaxes(gridcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    hist, _, _ = fetch_stock_data(r["ticker"])
    if hist is not None and len(hist) > 0:
        st.markdown("**🕯 株価チャート（2年）**")
        hist = hist.reset_index()
        hist["MA25"]  = hist["Close"].rolling(25).mean()
        hist["MA75"]  = hist["Close"].rolling(75).mean()
        hist["MA200"] = hist["Close"].rolling(200).mean()
        fig3 = go.Figure()
        fig3.add_trace(go.Candlestick(x=hist["Date"], open=hist["Open"], high=hist["High"],
            low=hist["Low"], close=hist["Close"], name="株価",
            increasing_line_color="#00e5a0", decreasing_line_color="#ef5350"))
        for col, color, lbl in [("MA25","#ffd54f","MA25"),("MA75","#4fc3f7","MA75"),("MA200","#ff7043","MA200")]:
            fig3.add_trace(go.Scatter(x=hist["Date"], y=hist[col], line=dict(color=color, width=1.2), name=lbl, opacity=0.8))
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0a0f1e", font_color="#e8f4ff",
            xaxis=dict(gridcolor="#1e3a5f", rangeslider_visible=False), yaxis=dict(gridcolor="#1e3a5f"),
            legend=dict(bgcolor="rgba(0,0,0,0)"), height=350, margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig3, use_container_width=True)

def render_history_chart(ticker, history):
    if ticker not in history or len(history[ticker]) < 2:
        st.info("スコア履歴は2日分以上のデータが蓄積されると表示されます。")
        return
    records = history[ticker]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[r["date"] for r in records], y=[r["total"] for r in records],
                             name="合計スコア", line=dict(color="#4fc3f7", width=2), yaxis="y"))
    fig.add_trace(go.Scatter(x=[r["date"] for r in records], y=[r["price"] for r in records],
                             name="株価", line=dict(color="#ffd54f", width=1.5, dash="dot"), yaxis="y2"))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0a0f1e", font_color="#e8f4ff",
        yaxis=dict(title="スコア", gridcolor="#1e3a5f", range=[0,100]),
        yaxis2=dict(title="株価", overlaying="y", side="right", gridcolor="rgba(0,0,0,0)"),
        legend=dict(bgcolor="rgba(0,0,0,0)"), height=250, margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(fig, use_container_width=True)

def render_journal_tab(watchlist):
    """トレード日誌タブ"""
    journal = load_journal()

    st.markdown('<div class="section-head">新規メモを追加</div>', unsafe_allow_html=True)

    # 行1：銘柄・日付・ポジション種別
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        ticker_options  = list(watchlist.keys())
        selected_ticker = st.selectbox("銘柄", ticker_options,
                                       format_func=lambda t: f"{t} {watchlist[t]}")
    with c2:
        j_date = st.date_input("日付", value=datetime.now().date())
    with c3:
        position_type = st.selectbox("種別", ["現物買い", "信用買い", "仮想（検討中）", "売り"])

    # 行2：価格ライン
    st.markdown("**📌 価格ライン**")
    p1, p2, p3 = st.columns(3)
    with p1:
        in_point   = st.number_input("INライン（円）",   min_value=0.0, step=1.0, format="%.0f")
    with p2:
        stop_point = st.number_input("損切ライン（円）", min_value=0.0, step=1.0, format="%.0f")
    with p3:
        target_point = st.number_input("目標ライン（円）", min_value=0.0, step=1.0, format="%.0f")

    # 行3：チャートコメント（構造化）
    st.markdown("**📊 チャート分析**")
    ca1, ca2 = st.columns(2)
    with ca1:
        trend_dir = st.selectbox("トレンド方向", ["上昇", "下降", "横ばい（保ち合い）", "底値圏", "天井圏"])
        volume_judge = st.selectbox("出来高", ["増加（買い圧力あり）", "減少", "変化なし", "急増（注目）"])
    with ca2:
        ma_status = st.selectbox("MA状況", [
            "25MA > 75MA > 200MA（強気配列）",
            "200MAを上抜け（転換シグナル）",
            "200MAに接触中（サポート確認）",
            "25MA < 75MA < 200MA（弱気配列）",
            "MA収束中（ブレイク待ち）",
            "その他",
        ])
        pattern = st.selectbox("チャートパターン", [
            "底値圏での出来高増加",
            "ダブルボトム形成中",
            "ゴールデンクロス直前",
            "三角保ち合いブレイク",
            "高値更新（上昇継続）",
            "デッドクロス警戒",
            "特になし",
        ])

    # 自由記述
    tech_comment = st.text_area("テクニカル根拠（自由記述）",
        placeholder="例：RSI30台で売られすぎ。VRVPのボリュームノード（950円帯）がサポートとして機能している。",
        height=80)
    general_comment = st.text_area("総合所見・投資判断",
        placeholder="例：ファンダ的に割安。チャートは底値圏。ただし200MAの下降トレンドが続いており、上抜け確認まで様子見。",
        height=80)

    # 確信度
    confidence = st.select_slider("確信度", options=[1,2,3,4,5], format_func=lambda x: "★"*x)

    if st.button("📝 メモを保存", type="primary", use_container_width=True):
        if tech_comment or general_comment:
            # 現在株価を取得
            hist, info, _ = fetch_stock_data(selected_ticker)
            current_price = safe_float(info.get("currentPrice") or info.get("regularMarketPrice")) if info else None

            # リスクリワード計算
            rr_ratio = None
            if in_point > 0 and stop_point > 0 and target_point > 0:
                risk   = abs(in_point - stop_point)
                reward = abs(target_point - in_point)
                rr_ratio = round(reward / risk, 2) if risk > 0 else None

            entry = {
                "id":            datetime.now().strftime("%Y%m%d%H%M%S"),
                "date":          str(j_date),
                "ticker":        selected_ticker,
                "name":          watchlist.get(selected_ticker, selected_ticker),
                "position_type": position_type,
                "current_price": current_price,
                "in_point":      in_point      if in_point > 0      else None,
                "stop_point":    stop_point    if stop_point > 0    else None,
                "target_point":  target_point  if target_point > 0  else None,
                "rr_ratio":      rr_ratio,
                "trend_dir":     trend_dir,
                "volume_judge":  volume_judge,
                "ma_status":     ma_status,
                "pattern":       pattern,
                "tech_comment":  tech_comment,
                "general_comment": general_comment,
                "confidence":    confidence,
            }
            journal.insert(0, entry)
            save_journal(journal)
            st.success("保存しました ✅")
            st.rerun()
        else:
            st.warning("テクニカル根拠または総合所見を入力してください")

    st.divider()
    st.markdown('<div class="section-head">メモ一覧</div>', unsafe_allow_html=True)

    # フィルター
    fc1, fc2 = st.columns([2, 2])
    with fc1:
        filter_ticker = st.selectbox("銘柄フィルター", ["すべて"] + list(watchlist.keys()),
                                     format_func=lambda t: "すべて" if t == "すべて" else f"{t} {watchlist.get(t,'')}")
    with fc2:
        filter_type = st.selectbox("種別フィルター", ["すべて", "現物買い", "信用買い", "仮想（検討中）", "売り"])

    filtered = [j for j in journal
                if (filter_ticker == "すべて" or j["ticker"] == filter_ticker)
                and (filter_type == "すべて" or j.get("position_type") == filter_type)]

    if not filtered:
        st.info("メモがまだありません。上のフォームから追加してください。")
    else:
        for entry in filtered:
            stars    = "★" * entry.get("confidence", 1) + "☆" * (5 - entry.get("confidence", 1))
            cur_p    = f"現在値 ¥{entry['current_price']:,.0f}" if entry.get("current_price") else "現在値 —"
            in_str   = f"¥{entry['in_point']:,.0f}"     if entry.get("in_point")     else "—"
            stop_str = f"¥{entry['stop_point']:,.0f}"   if entry.get("stop_point")   else "—"
            tgt_str  = f"¥{entry['target_point']:,.0f}" if entry.get("target_point") else "—"
            rr_str   = f"RR {entry['rr_ratio']:.1f}x"  if entry.get("rr_ratio")     else ""
            ptype    = entry.get("position_type", "")
            pcolor   = "#00e5a0" if "買い" in ptype else "#ef5350" if "売り" in ptype else "#ffd54f"

            card_col, del_col = st.columns([12, 1])
            with card_col:
                st.markdown(f"""
                <div class="journal-card">
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">
                    <div>
                      <span class="journal-ticker">{entry['ticker']} {entry['name']}</span>
                      <span style="font-family:'IBM Plex Mono',monospace;font-size:0.7rem;color:#4a7fa5;margin-left:0.8rem;">{entry['date']}</span>
                      <span style="font-size:0.7rem;color:{pcolor};margin-left:0.8rem;font-weight:700;">{ptype}</span>
                    </div>
                    <span class="confidence-star" style="font-size:0.8rem;">{stars}</span>
                  </div>

                  <!-- 価格ライン -->
                  <div style="display:flex;gap:1rem;margin-bottom:0.6rem;background:#0a0f1e;border-radius:6px;padding:0.5rem 0.8rem;">
                    <span style="font-size:0.7rem;color:#7fb3d3;">{cur_p}</span>
                    <span class="price-line-in">IN {in_str}</span>
                    <span class="price-line-stop">損切 {stop_str}</span>
                    <span class="price-line-tgt">目標 {tgt_str}</span>
                    <span style="font-family:'IBM Plex Mono',monospace;font-size:0.7rem;color:#a78bfa;">{rr_str}</span>
                  </div>

                  <!-- チャート分析 -->
                  <div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:0.6rem;">
                    <span style="background:#0a2a1a;color:#00e5a0;border:1px solid #00e5a040;border-radius:4px;padding:0.15rem 0.5rem;font-size:0.68rem;">{entry.get('trend_dir','')}</span>
                    <span style="background:#1a1a0a;color:#ffd54f;border:1px solid #ffd54f40;border-radius:4px;padding:0.15rem 0.5rem;font-size:0.68rem;">{entry.get('volume_judge','')}</span>
                    <span style="background:#0a1a2a;color:#4fc3f7;border:1px solid #4fc3f740;border-radius:4px;padding:0.15rem 0.5rem;font-size:0.68rem;">{entry.get('pattern','')}</span>
                  </div>

                  <!-- MA状況 -->
                  <div style="font-size:0.75rem;color:#7fb3d3;margin-bottom:0.4rem;">📐 {entry.get('ma_status','')}</div>

                  <!-- コメント -->
                  {"<div style='font-size:0.85rem;color:#b0c4d8;margin-bottom:0.3rem;'>🔍 " + entry['tech_comment'] + "</div>" if entry.get('tech_comment') else ""}
                  {"<div style='font-size:0.85rem;color:#e8f4ff;'>💬 " + entry['general_comment'] + "</div>" if entry.get('general_comment') else ""}
                </div>
                """, unsafe_allow_html=True)
            with del_col:
                st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
                if st.button("✕", key=f"jdel_{entry['id']}", help="削除"):
                    journal = [j for j in journal if j["id"] != entry["id"]]
                    save_journal(journal)
                    st.rerun()

# ─── メイン ───────────────────────────────────────────────────
def main():
    st.markdown(f"""
    <div class="main-header">
      <h1>📈 日本株 AI スコアボード</h1>
      <div class="subtitle">FUNDA + CHART SCORING ENGINE &nbsp;|&nbsp; {datetime.now().strftime('%Y-%m-%d %H:%M')} 更新</div>
    </div>
    """, unsafe_allow_html=True)

    watchlist = load_watchlist()
    history   = load_history()

    with st.sidebar:
        render_watchlist_manager(watchlist)
        watchlist = load_watchlist()
        st.divider()
        st.markdown('<div class="section-head">スコア基準</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:0.75rem;color:#7fb3d3;line-height:1.9;">
        🟢 <b>80〜100点</b>　強買い<br>🔵 <b>65〜79点</b>　　買い<br>
        🟡 <b>50〜64点</b>　　様子見<br>🔴 <b>〜49点</b>　　　見送り
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        if st.button("🔄 データ更新", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()
        st.markdown('<div class="section-head" style="margin-top:1.5rem;">スコアを保存</div>', unsafe_allow_html=True)
        save_note = st.text_input("メモ", placeholder="今日の相場メモ...")
        if st.button("📝 本日スコアを保存", use_container_width=True):
            today = datetime.now().strftime("%Y-%m-%d")
            for ticker, name in watchlist.items():
                r = score_stock(ticker, name)
                if "error" not in r:
                    if ticker not in history:
                        history[ticker] = []
                    history[ticker] = [h for h in history[ticker] if h.get("date") != today]
                    history[ticker].append({
                        "date": today, "total": r["total"],
                        "funda": r["funda"]["total"], "chart": r["chart"]["total"],
                        "price": r["price"], "note": save_note,
                    })
            save_history(history)
            st.success("保存しました ✅")

    tabs = st.tabs(["📋 スコアボード", "🔍 銘柄詳細", "📈 スコア履歴", "📓 トレード日誌"])

    with tabs[0]:
        with st.spinner("市場指標を取得中…"):
            market_scores = fetch_market_indices()
        render_market_panel(market_scores)
        if not watchlist:
            st.info("左のサイドバーから証券コードを入力して銘柄を追加してください。")
        else:
            results = []
            with st.spinner("データ取得中…"):
                for ticker, name in watchlist.items():
                    results.append(score_stock(ticker, name))
            results_ok = sorted([r for r in results if "error" not in r], key=lambda r: r["total"], reverse=True)
            results_ng = [r for r in results if "error" in r]
            if results_ok:
                avg  = sum(r["total"] for r in results_ok) / len(results_ok)
                best = results_ok[0]
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("📊 平均スコア", f"{avg:.1f}点")
                c2.metric("🏆 最高スコア", f"{best['total']}点", best["name"])
                c3.metric("🟢 強買い銘柄", f"{sum(1 for r in results_ok if r['total'] >= 80)}銘柄")
                c4.metric("🔵 買い銘柄",   f"{sum(1 for r in results_ok if 65 <= r['total'] < 80)}銘柄")
                st.divider()
            for r in results_ok:
                render_card_with_delete(r, watchlist)
            for r in results_ng:
                render_card_with_delete(r, watchlist)

    with tabs[1]:
        if not watchlist:
            st.info("サイドバーから銘柄を追加してください。")
        else:
            selected = st.selectbox("銘柄を選択", list(watchlist.keys()),
                                    format_func=lambda t: f"{t}　{watchlist[t]}")
            with st.spinner("分析中…"):
                r = score_stock(selected, watchlist[selected])
            render_detail(r)

    with tabs[2]:
        if not watchlist:
            st.info("サイドバーから銘柄を追加してください。")
        else:
            selected_h = st.selectbox("銘柄を選択", list(watchlist.keys()),
                                      format_func=lambda t: f"{t}　{watchlist[t]}", key="history_select")
            st.markdown(f'<div class="section-head">スコア推移 — {watchlist[selected_h]}</div>', unsafe_allow_html=True)
            render_history_chart(selected_h, history)
            if selected_h in history and history[selected_h]:
                df_h = pd.DataFrame(history[selected_h])
                df_h = df_h.sort_values("date", ascending=False).reset_index(drop=True)
                df_h.columns = ["日付", "合計", "ファンダ", "チャート", "株価", "メモ"]
                st.dataframe(df_h, use_container_width=True)

    with tabs[3]:
        render_journal_tab(watchlist)

if __name__ == "__main__":
    main()
