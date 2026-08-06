"""
日本株 AI スコアボード
依存: streamlit, yfinance, pandas, plotly
起動: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
import os

# ─── ページ設定 ────────────────────────────────────────────────
st.set_page_config(
    page_title="日本株スコアボード",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── スタイル ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Noto+Sans+JP:wght@400;500;700&display=swap');

html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; }

.main-header {
    background: linear-gradient(135deg, #0a0f1e 0%, #0d1f3c 100%);
    border-bottom: 1px solid #1e3a5f;
    padding: 1.5rem 2rem;
    margin: -1rem -1rem 2rem -1rem;
    border-radius: 0 0 12px 12px;
}
.main-header h1 {
    font-family: 'IBM Plex Mono', monospace;
    color: #e8f4ff; font-size: 1.6rem; font-weight: 600;
    letter-spacing: -0.02em; margin: 0;
}
.main-header .subtitle {
    color: #4a7fa5; font-size: 0.8rem;
    font-family: 'IBM Plex Mono', monospace; margin-top: 0.3rem;
}

/* 市場環境パネル */
.market-panel {
    background: #060d1a;
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 1.2rem 1.6rem;
    margin-bottom: 1.5rem;
}
.market-panel-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem; color: #4a7fa5;
    letter-spacing: 0.15em; text-transform: uppercase;
    margin-bottom: 1rem;
    border-bottom: 1px solid #1e3a5f; padding-bottom: 0.4rem;
}
.market-index-card {
    background: #0d1f3c;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 0.8rem 1rem;
}
.market-verdict-good  { color: #00e5a0; font-weight: 700; }
.market-verdict-caution { color: #ffd54f; font-weight: 700; }
.market-verdict-bad   { color: #ef5350; font-weight: 700; }

.score-card {
    background: #0d1f3c; border: 1px solid #1e3a5f;
    border-radius: 10px; padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem; transition: border-color 0.2s; cursor: pointer;
}
.score-card:hover { border-color: #2d6a9f; }

.score-badge { font-family: 'IBM Plex Mono', monospace; font-size: 2.2rem; font-weight: 600; line-height: 1; }
.score-strong-buy { color: #00e5a0; }
.score-buy        { color: #4fc3f7; }
.score-watch      { color: #ffd54f; }
.score-pass       { color: #ef5350; }

.ticker-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #4a7fa5; letter-spacing: 0.08em; }
.company-name { font-size: 1rem; font-weight: 700; color: #e8f4ff; margin: 0.15rem 0; }
.price-display { font-family: 'IBM Plex Mono', monospace; font-size: 1.1rem; color: #e8f4ff; }
.price-change-pos { color: #00e5a0; }
.price-change-neg { color: #ef5350; }

.metric-row { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.7rem; }
.metric-pill {
    background: #0a0f1e; border: 1px solid #1e3a5f; border-radius: 4px;
    padding: 0.2rem 0.6rem; font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem; color: #7fb3d3;
}

.verdict {
    display: inline-block; padding: 0.2rem 0.7rem; border-radius: 4px;
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.06em;
    font-family: 'IBM Plex Mono', monospace;
}
.verdict-sb { background: #003d28; color: #00e5a0; border: 1px solid #00e5a0; }
.verdict-b  { background: #003366; color: #4fc3f7; border: 1px solid #4fc3f7; }
.verdict-w  { background: #3d2e00; color: #ffd54f; border: 1px solid #ffd54f; }
.verdict-p  { background: #3d0000; color: #ef5350; border: 1px solid #ef5350; }

.section-head {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: #4a7fa5;
    letter-spacing: 0.15em; text-transform: uppercase;
    border-bottom: 1px solid #1e3a5f; padding-bottom: 0.4rem; margin-bottom: 1rem;
}

section[data-testid="stSidebar"] { background: #0a0f1e; border-right: 1px solid #1e3a5f; }
.stMetric { background: transparent !important; }
[data-testid="metric-container"] { background: #0d1f3c; border: 1px solid #1e3a5f; border-radius: 8px; padding: 0.8rem; }
.stAlert { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


# ─── データレイヤー ────────────────────────────────────────────
SCORE_HISTORY_FILE = "score_history.json"
WATCHLIST_FILE     = "watchlist.json"

DEFAULT_WATCHLIST = {
    "8113.T": "ユニ・チャーム",
    "5243.T": "note",
    "4588.T": "オンコリスバイオ",
    "6702.T": "富士通",
    "5016.T": "JX金属",
}

# 市場指標の定義
MARKET_INDICES = {
    "^N225":  {"name": "日経平均",  "emoji": "🗾"},
    "1306.T": {"name": "TOPIX ETF", "emoji": "📊"},
    "1321.T": {"name": "日経ETF",   "emoji": "⚡"},
    "JPY=X":  {"name": "ドル円",    "emoji": "💱"},
}

def load_watchlist() -> dict:
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE) as f:
            return json.load(f)
    return DEFAULT_WATCHLIST

def save_watchlist(wl: dict):
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(wl, f, ensure_ascii=False, indent=2)

def load_history() -> dict:
    if os.path.exists(SCORE_HISTORY_FILE):
        with open(SCORE_HISTORY_FILE) as f:
            return json.load(f)
    return {}

def save_history(history: dict):
    with open(SCORE_HISTORY_FILE, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


# ─── スコアリングエンジン ──────────────────────────────────────
def safe_float(val):
    try:
        v = float(val)
        return None if (v != v) else v  # NaN check
    except:
        return None

def compute_chart_score(hist: pd.DataFrame) -> dict:
    if hist is None or len(hist) < 30:
        return {"total": 0, "details": {}, "error": "データ不足"}

    close  = hist["Close"]
    volume = hist["Volume"]
    scores = {}

    # RSI（10点）
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

    # MA配列（15点）
    price = safe_float(close.iloc[-1]) or 0
    ma25  = safe_float(close.rolling(25).mean().iloc[-1])
    ma75  = safe_float(close.rolling(75).mean().iloc[-1])  if len(close) >= 75  else None
    ma200 = safe_float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None

    ms = 0
    if ma25  and price > ma25:  ms += 5
    if ma75  and price > ma75:  ms += 5
    if ma200 and price > ma200: ms += 5
    scores["MA配列"] = ms

    # 出来高（10点）
    vol_recent = volume.iloc[-10:].mean()
    vol_past   = volume.iloc[-30:-10].mean()
    vol_ratio  = vol_recent / vol_past if vol_past > 0 else 1
    scores["出来高"] = min(10, int(vol_ratio * 7))

    # ボリンジャーバンド（10点）
    ma20     = close.rolling(20).mean()
    std20    = close.rolling(20).std()
    bb_lower = safe_float((ma20 - 2 * std20).iloc[-1]) or 0
    bb_upper = safe_float((ma20 + 2 * std20).iloc[-1]) or 0
    bb_pos   = (price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5

    if bb_pos <= 0.2:   scores["BB"] = 10
    elif bb_pos <= 0.4: scores["BB"] = 7
    elif bb_pos <= 0.6: scores["BB"] = 5
    else:               scores["BB"] = max(0, int(10 - bb_pos * 10))

    # 52週レンジ（5点）
    hi52      = safe_float(close.rolling(252).max().iloc[-1]) if len(close) >= 252 else safe_float(close.max())
    lo52      = safe_float(close.rolling(252).min().iloc[-1]) if len(close) >= 252 else safe_float(close.min())
    range_pos = (price - lo52) / (hi52 - lo52) if (hi52 and lo52 and hi52 - lo52 > 0) else 0.5

    scores["52週位置"] = 5 if range_pos <= 0.3 else (3 if range_pos <= 0.5 else 1)

    return {
        "total": sum(scores.values()),
        "details": scores,
        "rsi": round(rsi, 1),
        "ma25": round(ma25, 1) if ma25 else None,
        "ma75": round(ma75, 1) if ma75 else None,
        "ma200": round(ma200, 1) if ma200 else None,
        "bb_pos": round(bb_pos * 100, 1),
        "range_pos": round(range_pos * 100, 1),
    }


def compute_funda_score(info: dict) -> dict:
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
        "total": sum(scores.values()),
        "details": scores,
        "per": per, "pbr": pbr,
        "roe": round(roe * 100, 1) if roe else None,
        "rev_growth": round(rg * 100, 1) if rg else None,
        "div_yield": round(dy * 100, 2) if dy else None,
    }


def compute_market_chart_score(hist: pd.DataFrame, ticker: str) -> dict:
    """市場指標専用スコア（チャートのみ・30点満点）"""
    if hist is None or len(hist) < 30:
        return {"total": 0, "trend": "—", "rsi": None, "chg_pct": None}

    close = hist["Close"]
    price = safe_float(close.iloc[-1]) or 0
    prev  = safe_float(close.iloc[-2]) if len(close) >= 2 else price
    chg_pct = (price - prev) / prev * 100 if prev else 0

    # RSI
    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, float("nan"))
    rsi_s = (100 - 100 / (1 + rs)).iloc[-1]
    rsi   = safe_float(rsi_s) or 50.0

    # MA
    ma25  = safe_float(close.rolling(25).mean().iloc[-1])
    ma75  = safe_float(close.rolling(75).mean().iloc[-1]) if len(close) >= 75 else None
    ma200 = safe_float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None

    score = 0

    # 日経VI・ドル円は逆方向判定
    if ticker == "^JNIV":
        # VI：低いほど市場が安定 → 高スコア
        score = 10 if price < 20 else 7 if price < 25 else 4 if price < 30 else 1
        trend = "安定" if price < 20 else "やや不安" if price < 25 else "警戒"
    elif ticker == "JPY=X":
        # ドル円：適正レンジ（140〜155円）を高スコアに
        score = 8 if 140 <= price <= 155 else 5 if 130 <= price < 140 else 3
        trend = "適正" if 140 <= price <= 155 else "円高" if price < 140 else "円安"
    else:
        # 日経・TOPIX：MA配列と位置で判定
        ma_ok = sum([
            1 if (ma25 and price > ma25) else 0,
            1 if (ma75 and price > ma75) else 0,
            1 if (ma200 and price > ma200) else 0,
        ])
        rsi_ok = 1 if 40 <= rsi <= 65 else 0
        score = ma_ok * 3 + rsi_ok * 1  # 最大10点
        trend = "上昇トレンド" if ma_ok >= 2 else "調整中" if ma_ok == 1 else "下降トレンド"

    return {
        "total": score,
        "trend": trend,
        "rsi": round(rsi, 1),
        "chg_pct": round(chg_pct, 2),
        "price": price,
        "ma25": ma25, "ma75": ma75, "ma200": ma200,
    }


def market_environment_verdict(scores: dict) -> tuple[str, str]:
    """市場全体の環境判定"""
    n225  = scores.get("^N225", {}).get("total", 0)
    topix = scores.get("^TOPX", {}).get("total", 0)
    vi    = scores.get("^JNIV", {}).get("total", 5)
    fx    = scores.get("JPY=X", {}).get("total", 5)

    total = n225 + topix + vi + fx  # 最大40点

    if total >= 28:   return "買い場", "market-verdict-good"
    elif total >= 18: return "中立",   "market-verdict-caution"
    else:             return "慎重",   "market-verdict-bad"


def verdict(score: int) -> tuple[str, str, str]:
    if score >= 80: return "強買い", "score-strong-buy", "verdict-sb"
    if score >= 65: return "買い",   "score-buy",        "verdict-b"
    if score >= 50: return "様子見", "score-watch",      "verdict-w"
    return "見送り", "score-pass", "verdict-p"


@st.cache_data(ttl=3600)
def fetch_stock_data(ticker: str):
    try:
        import yfinance as yf
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y")
        info = tk.info
        return hist, info, None
    except ImportError:
        return None, {}, "yfinanceが見つかりません。`pip install yfinance`を実行してください。"
    except Exception as e:
        return None, {}, str(e)


@st.cache_data(ttl=1800)
def fetch_market_indices():
    """市場指標を取得（stooq経由・30分キャッシュ）"""
    from pandas_datareader import data as pdr
    import datetime

import yfinance as yf
    results = {}
    for ticker in MARKET_INDICES:
        try:
            tk   = yf.Ticker(ticker)
            hist = tk.history(period="1y")
            if hist is None or len(hist) == 0:
                raise ValueError("データなし")
            results[ticker] = compute_market_chart_score(hist, ticker)
        except:
            results[ticker] = {"total": 0, "trend": "取得失敗", "chg_pct": None, "price": None}
    return results


def score_stock(ticker: str, name: str) -> dict:
    hist, info, err = fetch_stock_data(ticker)
    if err:
        return {"ticker": ticker, "name": name, "error": err}

    chart = compute_chart_score(hist)
    funda = compute_funda_score(info)
    total = chart["total"] + funda["total"]
    label, score_cls, verdict_cls = verdict(total)

    price = safe_float(info.get("currentPrice") or info.get("regularMarketPrice")) or 0
    prev  = safe_float(info.get("regularMarketPreviousClose")) or price
    chg   = price - prev
    chg_pct = chg / prev * 100 if prev else 0

    return {
        "ticker": ticker, "name": name,
        "price": price, "chg": chg, "chg_pct": chg_pct,
        "total": total, "funda": funda, "chart": chart,
        "label": label, "score_cls": score_cls, "verdict_cls": verdict_cls,
        "updated_at": datetime.now().isoformat(),
    }


# ─── UI コンポーネント ─────────────────────────────────────────
def render_market_panel(market_scores: dict):
    """市場環境パネル"""
    env_label, env_cls = market_environment_verdict(market_scores)

    st.markdown(f"""
    <div class="market-panel">
      <div class="market-panel-title">
        🌐 市場環境スコア &nbsp;｜&nbsp;
        <span class="{env_cls}">総合判定：{env_label}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    for i, (ticker, meta) in enumerate(MARKET_INDICES.items()):
        s = market_scores.get(ticker, {})
        price   = s.get("price")
        chg_pct = s.get("chg_pct")
        trend   = s.get("trend", "—")
        score   = s.get("total", 0)

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


def render_card(r: dict):
    if "error" in r:
        st.error(f"**{r['name']}（{r['ticker']}）** — {r['error']}")
        return

    chg_cls  = "price-change-pos" if r["chg"] >= 0 else "price-change-neg"
    chg_sign = "+" if r["chg"] >= 0 else ""
    v_label, _, v_cls = verdict(r["total"])

    fa = r["funda"]
    ch = r["chart"]

    per_str = f"PER {fa['per']:.1f}x"      if fa.get("per")       else "PER —"
    pbr_str = f"PBR {fa['pbr']:.2f}x"      if fa.get("pbr")       else "PBR —"
    roe_str = f"ROE {fa['roe']:.1f}%"       if fa.get("roe")       else "ROE —"
    rsi_str = f"RSI {ch.get('rsi','—')}"
    rng_str = f"52W位置 {ch.get('range_pos','—')}%"
    div_str = f"配当 {fa['div_yield']:.2f}%" if fa.get("div_yield") else "配当 —"

    st.markdown(f"""
    <div class="score-card">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
          <div class="ticker-label">{r['ticker']}</div>
          <div class="company-name">{r['name']}</div>
          <div class="price-display">
            ¥{r['price']:,.0f}&nbsp;
            <span class="{chg_cls}">{chg_sign}{r['chg']:,.0f}（{chg_sign}{r['chg_pct']:.2f}%）</span>
          </div>
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
          <div style="background:#1e3a5f;border-radius:3px;height:6px;">
            <div style="background:#4fc3f7;width:{fa['total']*2}%;height:6px;border-radius:3px;"></div>
          </div>
        </div>
        <div style="flex:1;background:#0a0f1e;border-radius:6px;padding:0.5rem 0.8rem;">
          <div style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;color:#4a7fa5;margin-bottom:0.3rem;">CHART {ch['total']}/50</div>
          <div style="background:#1e3a5f;border-radius:3px;height:6px;">
            <div style="background:#00e5a0;width:{ch['total']*2}%;height:6px;border-radius:3px;"></div>
          </div>
        </div>
      </div>
      <div class="metric-row">
        <div class="metric-pill">{per_str}</div>
        <div class="metric-pill">{pbr_str}</div>
        <div class="metric-pill">{roe_str}</div>
        <div class="metric-pill">{rsi_str}</div>
        <div class="metric-pill">{rng_str}</div>
        <div class="metric-pill">{div_str}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_detail(r: dict):
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
                          font_color="#e8f4ff", margin=dict(l=0,r=0,t=10,b=0),
                          height=220, showlegend=False, coloraxis_showscale=False)
        fig.update_xaxes(gridcolor="#1e3a5f", range=[0,10])
        fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**📈 チャートスコア内訳**")
        ch_df = pd.DataFrame(list(r["chart"]["details"].items()), columns=["指標", "スコア"])
        fig2 = px.bar(ch_df, x="スコア", y="指標", orientation="h",
                      color="スコア", color_continuous_scale=["#ef5350","#ffd54f","#00e5a0"], range_color=[0,10])
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="#e8f4ff", margin=dict(l=0,r=0,t=10,b=0),
                           height=220, showlegend=False, coloraxis_showscale=False)
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
        fig3.add_trace(go.Candlestick(
            x=hist["Date"], open=hist["Open"], high=hist["High"],
            low=hist["Low"], close=hist["Close"], name="株価",
            increasing_line_color="#00e5a0", decreasing_line_color="#ef5350",
        ))
        for col, color, lbl in [("MA25","#ffd54f","MA25"),("MA75","#4fc3f7","MA75"),("MA200","#ff7043","MA200")]:
            fig3.add_trace(go.Scatter(x=hist["Date"], y=hist[col],
                                      line=dict(color=color, width=1.2), name=lbl, opacity=0.8))
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0a0f1e", font_color="#e8f4ff",
            xaxis=dict(gridcolor="#1e3a5f", rangeslider_visible=False),
            yaxis=dict(gridcolor="#1e3a5f"), legend=dict(bgcolor="rgba(0,0,0,0)"),
            height=350, margin=dict(l=0,r=0,t=10,b=0),
        )
        st.plotly_chart(fig3, use_container_width=True)


def render_history_chart(ticker: str, history: dict):
    if ticker not in history or len(history[ticker]) < 2:
        st.info("スコア履歴は2日分以上のデータが蓄積されると表示されます。")
        return

    records = history[ticker]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[r["date"] for r in records], y=[r["total"] for r in records],
                             name="合計スコア", line=dict(color="#4fc3f7", width=2), yaxis="y"))
    fig.add_trace(go.Scatter(x=[r["date"] for r in records], y=[r["price"] for r in records],
                             name="株価", line=dict(color="#ffd54f", width=1.5, dash="dot"), yaxis="y2"))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0a0f1e", font_color="#e8f4ff",
        yaxis=dict(title="スコア", gridcolor="#1e3a5f", range=[0,100]),
        yaxis2=dict(title="株価", overlaying="y", side="right", gridcolor="rgba(0,0,0,0)"),
        legend=dict(bgcolor="rgba(0,0,0,0)"), height=250, margin=dict(l=0,r=0,t=10,b=0),
    )
    st.plotly_chart(fig, use_container_width=True)


# ─── メインUI ─────────────────────────────────────────────────
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
        st.markdown('<div class="section-head">ウォッチリスト管理</div>', unsafe_allow_html=True)

        with st.expander("＋ 銘柄を追加", expanded=False):
            new_ticker = st.text_input("ティッカー（例: 7203.T）").strip().upper()
            new_name   = st.text_input("銘柄名（例: トヨタ自動車）").strip()
            if st.button("追加", use_container_width=True):
                if new_ticker and new_name:
                    watchlist[new_ticker] = new_name
                    save_watchlist(watchlist)
                    st.success(f"{new_name} を追加しました")
                    st.rerun()

        if watchlist:
            with st.expander("－ 銘柄を削除", expanded=False):
                del_ticker = st.selectbox("削除する銘柄", list(watchlist.keys()),
                                          format_func=lambda t: f"{t} {watchlist[t]}")
                if st.button("削除", use_container_width=True):
                    del watchlist[del_ticker]
                    save_watchlist(watchlist)
                    st.rerun()

        st.divider()
        st.markdown('<div class="section-head">スコア基準</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:0.75rem;color:#7fb3d3;line-height:1.9;">
        🟢 <b>80〜100点</b>　強買い<br>
        🔵 <b>65〜79点</b>　　買い<br>
        🟡 <b>50〜64点</b>　　様子見<br>
        🔴 <b>〜49点</b>　　　見送り
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        if st.button("🔄 データ更新（全銘柄）", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()

        st.markdown('<div class="section-head" style="margin-top:1.5rem;">スコアを保存</div>', unsafe_allow_html=True)
        save_note = st.text_input("メモ（任意）", placeholder="今日の相場メモ...")
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

    tabs = st.tabs(["📋 スコアボード", "🔍 銘柄詳細", "📈 スコア履歴"])

    with tabs[0]:
        # 市場環境パネル
        with st.spinner("市場指標を取得中…"):
            market_scores = fetch_market_indices()
        render_market_panel(market_scores)

        if not watchlist:
            st.info("サイドバーから銘柄を追加してください。")
        else:
            results = []
            with st.spinner("銘柄データ取得中…"):
                for ticker, name in watchlist.items():
                    results.append(score_stock(ticker, name))

            results_ok = sorted([r for r in results if "error" not in r], key=lambda r: r["total"], reverse=True)
            results_ng = [r for r in results if "error" in r]

            if results_ok:
                avg = sum(r["total"] for r in results_ok) / len(results_ok)
                best = results_ok[0]
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("📊 平均スコア", f"{avg:.1f}点")
                c2.metric("🏆 最高スコア", f"{best['total']}点", best["name"])
                c3.metric("🟢 強買い銘柄", f"{sum(1 for r in results_ok if r['total'] >= 80)}銘柄")
                c4.metric("🔵 買い銘柄",   f"{sum(1 for r in results_ok if 65 <= r['total'] < 80)}銘柄")
                st.divider()

            for r in results_ok:
                render_card(r)
            for r in results_ng:
                st.error(f"**{r['name']}（{r['ticker']}）** — {r['error']}")

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
            selected_h = st.selectbox("銘柄を選択（履歴）", list(watchlist.keys()),
                                      format_func=lambda t: f"{t}　{watchlist[t]}", key="history_select")
            st.markdown(f'<div class="section-head">スコア推移 — {watchlist[selected_h]}</div>', unsafe_allow_html=True)
            render_history_chart(selected_h, history)

            if selected_h in history and history[selected_h]:
                df_h = pd.DataFrame(history[selected_h])
                df_h = df_h.sort_values("date", ascending=False).reset_index(drop=True)
                df_h.columns = ["日付", "合計", "ファンダ", "チャート", "株価", "メモ"]
                st.dataframe(df_h, use_container_width=True)


if __name__ == "__main__":
    main()
