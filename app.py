"""
日本株 AI スコアボード
依存: streamlit, yfinance, pandas, plotly
起動: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
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

html, body, [class*="css"] {
    font-family: 'Noto Sans JP', sans-serif;
}

/* ヘッダー */
.main-header {
    background: linear-gradient(135deg, #0a0f1e 0%, #0d1f3c 100%);
    border-bottom: 1px solid #1e3a5f;
    padding: 1.5rem 2rem;
    margin: -1rem -1rem 2rem -1rem;
    border-radius: 0 0 12px 12px;
}
.main-header h1 {
    font-family: 'IBM Plex Mono', monospace;
    color: #e8f4ff;
    font-size: 1.6rem;
    font-weight: 600;
    letter-spacing: -0.02em;
    margin: 0;
}
.main-header .subtitle {
    color: #4a7fa5;
    font-size: 0.8rem;
    font-family: 'IBM Plex Mono', monospace;
    margin-top: 0.3rem;
}

/* スコアカード */
.score-card {
    background: #0d1f3c;
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
    transition: border-color 0.2s;
    cursor: pointer;
}
.score-card:hover { border-color: #2d6a9f; }

.score-badge {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2.2rem;
    font-weight: 600;
    line-height: 1;
}
.score-strong-buy  { color: #00e5a0; }
.score-buy         { color: #4fc3f7; }
.score-watch       { color: #ffd54f; }
.score-pass        { color: #ef5350; }

.ticker-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: #4a7fa5;
    letter-spacing: 0.08em;
}
.company-name {
    font-size: 1rem;
    font-weight: 700;
    color: #e8f4ff;
    margin: 0.15rem 0;
}
.price-display {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.1rem;
    color: #e8f4ff;
}
.price-change-pos { color: #00e5a0; }
.price-change-neg { color: #ef5350; }

/* メトリクスバー */
.metric-row {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-top: 0.7rem;
}
.metric-pill {
    background: #0a0f1e;
    border: 1px solid #1e3a5f;
    border-radius: 4px;
    padding: 0.2rem 0.6rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #7fb3d3;
}
.metric-pill span { color: #e8f4ff; }

/* 判定バッジ */
.verdict {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    font-family: 'IBM Plex Mono', monospace;
}
.verdict-sb { background: #003d28; color: #00e5a0; border: 1px solid #00e5a0; }
.verdict-b  { background: #003366; color: #4fc3f7; border: 1px solid #4fc3f7; }
.verdict-w  { background: #3d2e00; color: #ffd54f; border: 1px solid #ffd54f; }
.verdict-p  { background: #3d0000; color: #ef5350; border: 1px solid #ef5350; }

/* セクションヘッダー */
.section-head {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: #4a7fa5;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    border-bottom: 1px solid #1e3a5f;
    padding-bottom: 0.4rem;
    margin-bottom: 1rem;
}

/* サイドバー */
section[data-testid="stSidebar"] {
    background: #0a0f1e;
    border-right: 1px solid #1e3a5f;
}

/* Streamlitデフォルトの上書き */
.stMetric { background: transparent !important; }
[data-testid="metric-container"] { background: #0d1f3c; border: 1px solid #1e3a5f; border-radius: 8px; padding: 0.8rem; }
.stAlert { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


# ─── データレイヤー ────────────────────────────────────────────
SCORE_HISTORY_FILE = "score_history.json"
WATCHLIST_FILE = "watchlist.json"

DEFAULT_WATCHLIST = {
    "8113.T": "ユニ・チャーム",
    "5243.T": "note",
    "4588.T": "オンコリスバイオ",
    "6702.T": "富士通",
    "5016.T": "JX金属",
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
def compute_chart_score(hist: pd.DataFrame) -> dict:
    """テクニカル指標からスコアを計算（50点満点）"""
    if hist is None or len(hist) < 30:
        return {"total": 0, "details": {}, "error": "データ不足"}

    close = hist["Close"]
    volume = hist["Volume"]

    scores = {}

    # RSI（10点）
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, float("nan"))
    rsi = (100 - 100 / (1 + rs)).iloc[-1]
    if 30 <= rsi <= 50:
        scores["RSI"] = 10
    elif 50 < rsi <= 60:
        scores["RSI"] = 7
    elif 20 <= rsi < 30:
        scores["RSI"] = 5
    elif rsi < 20:
        scores["RSI"] = 8  # 売られすぎ
    else:
        scores["RSI"] = max(0, int(10 - (rsi - 60) * 0.4) if not (rsi != rsi) else 0)

    # MA配列（15点）
    ma25  = close.rolling(25).mean().iloc[-1]
    ma75  = close.rolling(75).mean().iloc[-1] if len(close) >= 75 else None
    ma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None
    price = close.iloc[-1]

    ma_score = 0
    if price > ma25:  ma_score += 5
    if ma75 and price > ma75:  ma_score += 5
    if ma200 and price > ma200: ma_score += 5
    scores["MA配列"] = ma_score

    # 出来高トレンド（10点）
    vol_recent = volume.iloc[-10:].mean()
    vol_past   = volume.iloc[-30:-10].mean()
    vol_ratio  = vol_recent / vol_past if vol_past > 0 else 1
    scores["出来高"] = min(10, int(vol_ratio * 7))

    # ボリンジャーバンド（10点）
    ma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    bb_lower = (ma20 - 2 * std20).iloc[-1]
    bb_upper = (ma20 + 2 * std20).iloc[-1]
    bb_pos = (price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5
    if bb_pos <= 0.2:
        scores["BB"] = 10
    elif bb_pos <= 0.4:
        scores["BB"] = 7
    elif bb_pos <= 0.6:
        scores["BB"] = 5
    else:
        scores["BB"] = max(0, int(10 - bb_pos * 10))

    # 52週レンジ位置（5点）
    hi52 = close.rolling(252).max().iloc[-1] if len(close) >= 252 else close.max()
    lo52 = close.rolling(252).min().iloc[-1] if len(close) >= 252 else close.min()
    range_pos = (price - lo52) / (hi52 - lo52) if (hi52 - lo52) > 0 else 0.5
    if range_pos <= 0.3:
        scores["52週位置"] = 5
    elif range_pos <= 0.5:
        scores["52週位置"] = 3
    else:
        scores["52週位置"] = 1

    return {
        "total": sum(scores.values()),
        "details": scores,
        "rsi": round(rsi, 1),
        "ma25": round(ma25, 1),
        "ma75": round(ma75, 1) if ma75 else None,
        "ma200": round(ma200, 1) if ma200 else None,
        "bb_pos": round(bb_pos * 100, 1),
        "range_pos": round(range_pos * 100, 1),
    }


def compute_funda_score(info: dict) -> dict:
    """ファンダメンタルズからスコアを計算（50点満点）"""
    scores = {}

    # PER（10点）
    per = info.get("trailingPE") or info.get("forwardPE")
    if per:
        if per < 15:      scores["PER"] = 10
        elif per < 20:    scores["PER"] = 8
        elif per < 30:    scores["PER"] = 6
        elif per < 40:    scores["PER"] = 4
        else:             scores["PER"] = 2
    else:
        scores["PER"] = 0

    # PBR（10点）
    pbr = info.get("priceToBook")
    if pbr:
        if pbr < 1:       scores["PBR"] = 10
        elif pbr < 2:     scores["PBR"] = 8
        elif pbr < 3:     scores["PBR"] = 6
        elif pbr < 5:     scores["PBR"] = 4
        else:             scores["PBR"] = 2
    else:
        scores["PBR"] = 0

    # ROE（10点）
    roe = info.get("returnOnEquity")
    if roe:
        roe_pct = roe * 100
        if roe_pct >= 20:    scores["ROE"] = 10
        elif roe_pct >= 15:  scores["ROE"] = 8
        elif roe_pct >= 10:  scores["ROE"] = 6
        elif roe_pct >= 5:   scores["ROE"] = 4
        else:                scores["ROE"] = 2
    else:
        scores["ROE"] = 0

    # 売上成長率（10点）
    rev_growth = info.get("revenueGrowth")
    if rev_growth:
        g = rev_growth * 100
        if g >= 15:     scores["売上成長"] = 10
        elif g >= 10:   scores["売上成長"] = 8
        elif g >= 5:    scores["売上成長"] = 6
        elif g >= 0:    scores["売上成長"] = 4
        else:           scores["売上成長"] = 1
    else:
        scores["売上成長"] = 0

    # 配当利回り（5点）
    div_yield = info.get("dividendYield")
    if div_yield:
        dy = div_yield * 100
        if dy >= 3:      scores["配当"] = 5
        elif dy >= 2:    scores["配当"] = 4
        elif dy >= 1:    scores["配当"] = 3
        else:            scores["配当"] = 2
    else:
        scores["配当"] = 1

    # 自己資本比率（5点）
    equity_ratio = info.get("debtToEquity")
    if equity_ratio is not None:
        if equity_ratio < 30:    scores["財務"] = 5
        elif equity_ratio < 60:  scores["財務"] = 4
        elif equity_ratio < 100: scores["財務"] = 3
        else:                    scores["財務"] = 1
    else:
        scores["財務"] = 0

    return {
        "total": sum(scores.values()),
        "details": scores,
        "per": per,
        "pbr": pbr,
        "roe": round(roe * 100, 1) if roe else None,
        "rev_growth": round(rev_growth * 100, 1) if rev_growth else None,
        "div_yield": round(div_yield * 100, 2) if div_yield else None,
    }


def verdict(score: int) -> tuple[str, str, str]:
    """スコア → (ラベル, CSSクラス, 絵文字)"""
    if score >= 80:  return "強買い", "score-strong-buy", "verdict-sb"
    if score >= 65:  return "買い",   "score-buy",        "verdict-b"
    if score >= 50:  return "様子見", "score-watch",      "verdict-w"
    return "見送り", "score-pass", "verdict-p"


@st.cache_data(ttl=3600)
def fetch_stock_data(ticker: str):
    """yfinanceからデータ取得（1時間キャッシュ）"""
    try:
        import yfinance as yf
        tk = yf.Ticker(ticker)
        hist = tk.history(period="2y")
        info = tk.info
        return hist, info, None
    except ImportError:
        return None, {}, "yfinanceが見つかりません。`pip install yfinance`を実行してください。"
    except Exception as e:
        return None, {}, str(e)


def score_stock(ticker: str, name: str) -> dict:
    hist, info, err = fetch_stock_data(ticker)

    if err:
        return {"ticker": ticker, "name": name, "error": err}

    chart = compute_chart_score(hist)
    funda = compute_funda_score(info)
    total = chart["total"] + funda["total"]
    label, score_cls, verdict_cls = verdict(total)

    price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
    prev  = info.get("regularMarketPreviousClose", price)
    chg   = price - prev
    chg_pct = chg / prev * 100 if prev else 0

    return {
        "ticker":      ticker,
        "name":        name,
        "price":       price,
        "chg":         chg,
        "chg_pct":     chg_pct,
        "total":       total,
        "funda":       funda,
        "chart":       chart,
        "label":       label,
        "score_cls":   score_cls,
        "verdict_cls": verdict_cls,
        "updated_at":  datetime.now().isoformat(),
    }


# ─── UI コンポーネント ─────────────────────────────────────────
def render_card(r: dict):
    if "error" in r:
        st.error(f"**{r['name']}（{r['ticker']}）** — {r['error']}")
        return

    chg_cls = "price-change-pos" if r["chg"] >= 0 else "price-change-neg"
    chg_sign = "+" if r["chg"] >= 0 else ""
    v_label, _, v_cls = verdict(r["total"])

    fa = r["funda"]
    ch = r["chart"]

    per_str = f"PER {fa['per']:.1f}x"  if fa.get("per")        else "PER —"
    pbr_str = f"PBR {fa['pbr']:.2f}x"  if fa.get("pbr")        else "PBR —"
    roe_str = f"ROE {fa['roe']:.1f}%"   if fa.get("roe")        else "ROE —"
    rsi_str = f"RSI {ch.get('rsi','—')}"
    rng_str = f"52W位置 {ch.get('range_pos','—')}%"
    div_str = f"配当 {fa['div_yield']:.2f}%"  if fa.get("div_yield") else "配当 —"

    st.markdown(f"""
    <div class="score-card">
      <div style="display:flex; justify-content:space-between; align-items:flex-start;">
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
    """銘柄詳細パネル"""
    if "error" in r:
        return

    st.markdown(f'<div class="section-head">詳細分析 — {r["name"]}</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📊 ファンダスコア内訳**")
        fa_items = list(r["funda"]["details"].items())
        fa_df = pd.DataFrame(fa_items, columns=["指標", "スコア"])
        fig = px.bar(
            fa_df, x="スコア", y="指標", orientation="h",
            color="スコア", color_continuous_scale=["#ef5350","#ffd54f","#00e5a0"],
            range_color=[0, 10],
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e8f4ff", margin=dict(l=0, r=0, t=10, b=0),
            height=220, showlegend=False, coloraxis_showscale=False,
        )
        fig.update_xaxes(gridcolor="#1e3a5f", range=[0, 10])
        fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**📈 チャートスコア内訳**")
        ch_items = list(r["chart"]["details"].items())
        ch_df = pd.DataFrame(ch_items, columns=["指標", "スコア"])
        max_scores = {"RSI": 10, "MA配列": 15, "出来高": 10, "BB": 10, "52週位置": 5}
        fig2 = px.bar(
            ch_df, x="スコア", y="指標", orientation="h",
            color="スコア", color_continuous_scale=["#ef5350","#ffd54f","#00e5a0"],
            range_color=[0, 10],
        )
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e8f4ff", margin=dict(l=0, r=0, t=10, b=0),
            height=220, showlegend=False, coloraxis_showscale=False,
        )
        fig2.update_xaxes(gridcolor="#1e3a5f", range=[0, 15])
        fig2.update_yaxes(gridcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    # 株価チャート
    hist, _, _ = fetch_stock_data(r["ticker"])
    if hist is not None and len(hist) > 0:
        st.markdown("**🕯 株価チャート（2年）**")
        hist = hist.reset_index()

        # MAを計算
        hist["MA25"]  = hist["Close"].rolling(25).mean()
        hist["MA75"]  = hist["Close"].rolling(75).mean()
        hist["MA200"] = hist["Close"].rolling(200).mean()

        fig3 = go.Figure()
        fig3.add_trace(go.Candlestick(
            x=hist["Date"], open=hist["Open"], high=hist["High"],
            low=hist["Low"], close=hist["Close"],
            name="株価",
            increasing_line_color="#00e5a0", decreasing_line_color="#ef5350",
        ))
        for col, color, label in [("MA25","#ffd54f","MA25"),("MA75","#4fc3f7","MA75"),("MA200","#ff7043","MA200")]:
            fig3.add_trace(go.Scatter(
                x=hist["Date"], y=hist[col],
                line=dict(color=color, width=1.2),
                name=label, opacity=0.8,
            ))
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0a0f1e",
            font_color="#e8f4ff",
            xaxis=dict(gridcolor="#1e3a5f", rangeslider_visible=False),
            yaxis=dict(gridcolor="#1e3a5f"),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            height=350, margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig3, use_container_width=True)


def render_history_chart(ticker: str, history: dict):
    """スコア履歴チャート"""
    if ticker not in history or len(history[ticker]) < 2:
        st.info("スコア履歴は2日分以上のデータが蓄積されると表示されます。")
        return

    records = history[ticker]
    dates  = [r["date"] for r in records]
    totals = [r["total"] for r in records]
    prices = [r["price"] for r in records]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=totals,
        name="合計スコア", line=dict(color="#4fc3f7", width=2),
        yaxis="y",
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=prices,
        name="株価", line=dict(color="#ffd54f", width=1.5, dash="dot"),
        yaxis="y2",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0a0f1e",
        font_color="#e8f4ff",
        yaxis=dict(title="スコア", gridcolor="#1e3a5f", range=[0,100]),
        yaxis2=dict(title="株価", overlaying="y", side="right", gridcolor="rgba(0,0,0,0)"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        height=250, margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)


# ─── メインUI ─────────────────────────────────────────────────
def main():
    # ヘッダー
    st.markdown(f"""
    <div class="main-header">
      <h1>📈 日本株 AI スコアボード</h1>
      <div class="subtitle">FUNDA + CHART SCORING ENGINE &nbsp;|&nbsp; {datetime.now().strftime('%Y-%m-%d %H:%M')} 更新</div>
    </div>
    """, unsafe_allow_html=True)

    watchlist = load_watchlist()
    history   = load_history()

    # ─── サイドバー ─────────────────────────────────
    with st.sidebar:
        st.markdown('<div class="section-head">ウォッチリスト管理</div>', unsafe_allow_html=True)

        # 銘柄追加
        with st.expander("＋ 銘柄を追加", expanded=False):
            new_ticker = st.text_input("ティッカー（例: 7203.T）").strip().upper()
            new_name   = st.text_input("銘柄名（例: トヨタ自動車）").strip()
            if st.button("追加", use_container_width=True):
                if new_ticker and new_name:
                    watchlist[new_ticker] = new_name
                    save_watchlist(watchlist)
                    st.success(f"{new_name} を追加しました")
                    st.rerun()

        # 銘柄削除
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
                    # 同日は上書き
                    history[ticker] = [h for h in history[ticker] if h.get("date") != today]
                    history[ticker].append({
                        "date":  today,
                        "total": r["total"],
                        "funda": r["funda"]["total"],
                        "chart": r["chart"]["total"],
                        "price": r["price"],
                        "note":  save_note,
                    })
            save_history(history)
            st.success("保存しました ✅")

    # ─── メインエリア ─────────────────────────────
    tabs = st.tabs(["📋 スコアボード", "🔍 銘柄詳細", "📈 スコア履歴"])

    # --- タブ1: スコアボード ---
    with tabs[0]:
        if not watchlist:
            st.info("サイドバーから銘柄を追加してください。")
        else:
            results = []
            with st.spinner("データ取得中…"):
                for ticker, name in watchlist.items():
                    results.append(score_stock(ticker, name))

            # スコア順にソート
            results_ok = [r for r in results if "error" not in r]
            results_ng = [r for r in results if "error" in r]
            results_ok.sort(key=lambda r: r["total"], reverse=True)

            # サマリーメトリクス
            if results_ok:
                avg = sum(r["total"] for r in results_ok) / len(results_ok)
                best = results_ok[0]
                sb_count = sum(1 for r in results_ok if r["total"] >= 80)
                b_count  = sum(1 for r in results_ok if 65 <= r["total"] < 80)

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("📊 平均スコア",  f"{avg:.1f}点")
                c2.metric("🏆 最高スコア",  f"{best['total']}点", best["name"])
                c3.metric("🟢 強買い銘柄",  f"{sb_count}銘柄")
                c4.metric("🔵 買い銘柄",    f"{b_count}銘柄")
                st.divider()

            for r in results_ok:
                render_card(r)
            for r in results_ng:
                st.error(f"**{r['name']}（{r['ticker']}）** — {r['error']}")

    # --- タブ2: 銘柄詳細 ---
    with tabs[1]:
        if not watchlist:
            st.info("サイドバーから銘柄を追加してください。")
        else:
            selected = st.selectbox(
                "銘柄を選択",
                list(watchlist.keys()),
                format_func=lambda t: f"{t}　{watchlist[t]}",
            )
            with st.spinner("分析中…"):
                r = score_stock(selected, watchlist[selected])
            render_detail(r)

    # --- タブ3: スコア履歴 ---
    with tabs[2]:
        if not watchlist:
            st.info("サイドバーから銘柄を追加してください。")
        else:
            selected_h = st.selectbox(
                "銘柄を選択（履歴）",
                list(watchlist.keys()),
                format_func=lambda t: f"{t}　{watchlist[t]}",
                key="history_select",
            )
            st.markdown(f'<div class="section-head">スコア推移 — {watchlist[selected_h]}</div>',
                        unsafe_allow_html=True)
            render_history_chart(selected_h, history)

            if selected_h in history and history[selected_h]:
                df_h = pd.DataFrame(history[selected_h])
                df_h = df_h.sort_values("date", ascending=False).reset_index(drop=True)
                df_h.columns = ["日付", "合計", "ファンダ", "チャート", "株価", "メモ"]
                st.dataframe(df_h, use_container_width=True)


if __name__ == "__main__":
    main()
