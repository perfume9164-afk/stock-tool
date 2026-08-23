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
/* compact dashboard */
.block-container { padding-top:0.7rem !important; padding-bottom:0.7rem !important; max-width:100% !important; }
.main-header { padding:0.75rem 1rem; margin:-0.7rem -0.7rem 0.7rem -0.7rem; border-radius:0 0 8px 8px; }
.main-header h1 { font-size:1.25rem; }
.main-header .subtitle { font-size:0.68rem; margin-top:0.1rem; }
.score-card { padding:0.7rem 0.85rem; margin-bottom:0.4rem; border-radius:8px; }
.section-head { margin-bottom:0.4rem; padding-bottom:0.25rem; }
.market-panel { padding:0.65rem 0.8rem; margin-bottom:0.65rem; border-radius:8px; }
.market-panel-title { margin-bottom:0.45rem; }
.market-index-card { padding:0.5rem 0.65rem; }
.metric-row { gap:0.3rem; margin-top:0.4rem; }
.metric-pill { padding:0.16rem 0.4rem; font-size:0.64rem; }
.journal-card { padding:0.6rem 0.7rem; margin-bottom:0.3rem; border-radius:7px; }
[data-testid="stVerticalBlock"] { gap:0.4rem; }
div[data-testid="stHorizontalBlock"] { gap:0.5rem; }
.stButton > button { min-height:2rem; padding:0.2rem 0.65rem; }
.stock-grid-card {
    background:#0d1f3c;
    border:1px solid #1e3a5f;
    border-radius:10px;
    padding:0.85rem 0.95rem;
    min-height:205px;
    margin-bottom:0.15rem;
}
.stock-grid-head {
    display:flex;
    justify-content:space-between;
    align-items:flex-start;
    gap:.7rem;
}
.stock-grid-name { font-size:1.05rem; font-weight:700; color:#e8f4ff; line-height:1.25; }
.stock-grid-price { font-family:'IBM Plex Mono',monospace; font-size:1rem; color:#e8f4ff; margin-top:.35rem; }
.score-split {
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:.55rem;
    margin-top:.75rem;
}
.score-box {
    background:#0a0f1e;
    border:1px solid #1e3a5f;
    border-radius:7px;
    padding:.5rem .6rem;
}
.score-box-title { color:#7fb3d3; font-size:.66rem; margin-bottom:.2rem; }
.score-box-value { color:#e8f4ff; font-family:'IBM Plex Mono',monospace; font-size:.9rem; font-weight:700; }


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
    "6315.T": "TOWA",
    "6526.T": "ソシオネクスト",
    "5803.T": "フジクラ",
    "6702.T": "富士通",
    "7013.T": "IHI",
    "3660.T": "アイスタイル",
    "3962.T": "チェンジホールディングス",
    "6653.T": "正興電機製作所",
    "6405.T": "鈴茂器工",
    "8309.T": "三井住友トラストグループ",
    "4188.T": "三菱ケミカルグループ",
    "4519.T": "中外製薬",
    "5595.T": "QPS研究所",
    "3901.T": "マークラインズ",
    "1882.T": "東亜道路工業",
    "9513.T": "電源開発",
    "9348.T": "ispace",
    "3741.T": "セック",
    "7157.T": "ライフネット生命保険",
    "8136.T": "サンリオ",
    "5020.T": "ENEOSホールディングス",
    "8604.T": "野村ホールディングス",
    "7269.T": "スズキ",
    "8750.T": "第一生命ホールディングス",
    "4901.T": "富士フイルムホールディングス",
    "7267.T": "本田技研工業",
    "5101.T": "横浜ゴム",
    "9432.T": "NTT",
    "8306.T": "三菱UFJフィナンシャル・グループ",
    "8309.T": "三井住友トラストグループ",
    "8113.T": "ユニ・チャーム",
    "6702.T": "富士通",
    "5016.T": "JX金属",
    "1332.T": "ニッスイ",
    "1333.T": "マルハニチロ",
    "1605.T": "INPEX",
    "1801.T": "大成建設",
    "1802.T": "大林組",
    "1925.T": "大和ハウス工業",
    "1928.T": "積水ハウス",
    "2002.T": "日清製粉グループ本社",
    "2502.T": "アサヒグループホールディングス",
    "2503.T": "キリンホールディングス",
    "2768.T": "双日",
    "2801.T": "キッコーマン",
    "2802.T": "味の素",
    "2914.T": "日本たばこ産業",
    "3382.T": "セブン＆アイ・ホールディングス",
    "3861.T": "王子ホールディングス",
    "4005.T": "住友化学",
    "4188.T": "三菱ケミカルグループ",
    "4502.T": "武田薬品工業",
    "4503.T": "アステラス製薬",
    "4519.T": "中外製薬",
    "4568.T": "第一三共",
    "4661.T": "オリエンタルランド",
    "4902.T": "コニカミノルタ",
    "4911.T": "資生堂",
    "5021.T": "コスモエネルギーホールディングス",
    "5201.T": "AGC",
    "5401.T": "日本製鉄",
    "5411.T": "JFEホールディングス",
    "5801.T": "古河電気工業",
    "5802.T": "住友電気工業",
    "5803.T": "フジクラ",
    "6098.T": "リクルートホールディングス",
    "6301.T": "小松製作所",
    "6367.T": "ダイキン工業",
    "6501.T": "日立製作所",
    "6503.T": "三菱電機",
    "6504.T": "富士電機",
    "6758.T": "ソニーグループ",
    "6861.T": "キーエンス",
    "7011.T": "三菱重工業",
    "7013.T": "IHI",
    "7201.T": "日産自動車",
    "7203.T": "トヨタ自動車",
    "7205.T": "日野自動車",
    "7270.T": "SUBARU",
    "7741.T": "HOYA",
    "7974.T": "任天堂",
    "8001.T": "伊藤忠商事",
    "8002.T": "丸紅",
    "8031.T": "三井物産",
    "8035.T": "東京エレクトロン",
    "8053.T": "住友商事",
    "8058.T": "三菱商事",
    "8136.T": "サンリオ",
    "8308.T": "りそなホールディングス",
    "8316.T": "三井住友フィナンシャルグループ",
    "8411.T": "みずほフィナンシャルグループ",
    "8601.T": "大和証券グループ本社",
    "8766.T": "東京海上ホールディングス",
    "8801.T": "三井不動産",
    "8802.T": "三菱地所",
    "9020.T": "東日本旅客鉄道",
    "9021.T": "西日本旅客鉄道",
    "9022.T": "東海旅客鉄道",
    "9101.T": "日本郵船",
    "9104.T": "商船三井",
    "9107.T": "川崎汽船",
    "9433.T": "KDDI",
    "9434.T": "ソフトバンク",
    "9501.T": "東京電力ホールディングス",
    "9503.T": "関西電力",
    "9513.T": "電源開発",
    "9613.T": "NTTデータグループ",
    "9735.T": "セコム",
    "9843.T": "ニトリホールディングス",
    "9983.T": "ファーストリテイリング",
    "9984.T": "ソフトバンクグループ",
}

def load_json(path, default):
    """
    JSONを文字コード違いに強く読み込む。
    UTF-8 / UTF-8 BOM / CP932 / Shift-JIS に対応。
    """
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
            # 別の文字コードで再試行
            continue

        except json.JSONDecodeError as e:
            print(f"[JSON ERROR] {path}")
            print(f"[ENCODING] {encoding}")
            print(f"[DETAIL] {e}")
            return default

        except FileNotFoundError:
            return default

        except Exception as e:
            print(f"[LOAD ERROR] {path}: {e}")
            return default

    print(f"[ENCODING ERROR] 対応可能な文字コードで読み込めませんでした: {path}")
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8-sig") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

def load_watchlist():
    """
    GitHub上のwatchlist.jsonを優先して読み込む。
    GitHub取得に失敗した場合のみローカルを使用。
    """
    # まずローカル
    try:
        if os.path.exists(WATCHLIST_FILE):
            data = load_json(WATCHLIST_FILE, {})
            if data:
                return data
    except Exception:
        pass

    # GitHubから取得
    try:
        import urllib.request
        import base64

        token = st.secrets.get("GITHUB_TOKEN", "")
        repo = st.secrets.get(
            "GITHUB_REPO",
            "perfume9164-afk/stock-tool"
        )

        url = f"https://api.github.com/repos/{repo}/contents/watchlist.json"

        headers = {
            "Accept": "application/vnd.github+json"
        }

        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = urllib.request.Request(
            url,
            headers=headers
        )

        with urllib.request.urlopen(req, timeout=10) as res:
            obj = json.loads(res.read())

        content = base64.b64decode(
            obj["content"]
        ).decode("utf-8")

        data = json.loads(content)

        # ローカルにも保存
        save_json(WATCHLIST_FILE, data)

        return data

    except Exception as e:
        print(f"[GitHub watchlist read error] {e}")
        return DEFAULT_WATCHLIST.copy()


def save_watchlist(d):
    """
    watchlist.jsonをローカル＋GitHubへ保存。
    """
    # ローカル保存
    save_json(WATCHLIST_FILE, d)

    try:
        import urllib.request
        import base64

        token = st.secrets.get("GITHUB_TOKEN", "")
        repo = st.secrets.get(
            "GITHUB_REPO",
            "perfume9164-afk/stock-tool"
        )

        if not token:
            print("[WARN] GITHUB_TOKENがありません")
            return

        url = f"https://api.github.com/repos/{repo}/contents/watchlist.json"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        }

        # 現在のファイル情報を取得してSHAを取得
        req = urllib.request.Request(
            url,
            headers=headers
        )

        with urllib.request.urlopen(req, timeout=10) as res:
            current = json.loads(res.read())

        sha = current.get("sha")

        content = json.dumps(
            d,
            ensure_ascii=False,
            indent=2
        )

        encoded = base64.b64encode(
            content.encode("utf-8")
        ).decode("ascii")

        payload = {
            "message": "auto: update watchlist",
            "content": encoded,
            "sha": sha,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="PUT"
        )

        with urllib.request.urlopen(req, timeout=15) as res:
            result = json.loads(res.read())

        print("[OK] watchlist.jsonをGitHubへ保存しました")

    except Exception as e:
        print(f"[GitHub watchlist write error] {e}")
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
    # 配当利回りは「年間配当金 ÷ 株価 × 100」で再計算する。
    # dividendYield の返却形式に依存しないため、銘柄ごとの表示が正しくなる。
    dividend_rate = safe_float(info.get("dividendRate"))
    current_price = safe_float(info.get("currentPrice") or info.get("regularMarketPrice"))
    dy_raw = safe_float(info.get("dividendYield"))
    if dividend_rate is not None and current_price and current_price > 0:
        dy = dividend_rate / current_price * 100
    elif dy_raw is not None:
        # fallback: 0.0095 = 0.95% の通常形式を想定
        dy = dy_raw * 100 if dy_raw <= 1 else dy_raw
    else:
        dy = None
    if dy is not None:
        scores["配当"] = 5 if dy >= 3 else 4 if dy >= 2 else 3 if dy >= 1 else 2
    else:
        scores["配当"] = 1
    de = safe_float(info.get("debtToEquity"))
    scores["財務"] = (5 if de < 30 else 4 if de < 60 else 3 if de < 100 else 1) if de is not None else 0
    return {
        "total": sum(scores.values()), "details": scores,
        "per": per, "pbr": pbr,
        "roe": round(roe * 100, 1) if roe else None,
        "rev_growth": round(rg * 100, 1) if rg else None,
        "div_yield": round(dy, 2) if dy is not None else None,
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
    """会社名を取得（日本語優先。マスタ→Yahoo!ファイナンス日本版→yfinanceの順）"""
    # 1. 日本語名マスタに登録済みなら最優先
    if ticker in JP_NAME_MASTER:
        return JP_NAME_MASTER[ticker]

    code = ticker.replace(".T", "")

    # 2. Yahoo!ファイナンス日本版から日本語社名を取得
    #    マスタ未登録の日本株でも日本語表示できるようにする
    try:
        import requests, re, html as html_lib
        url = f"https://finance.yahoo.co.jp/quote/{code}"
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5
        )
        if resp.ok:
            m = re.search(r"<title[^>]*>(.*?)</title>", resp.text, re.I | re.S)
            if m:
                title = html_lib.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
                # 例:「トヨタ自動車(7203) 株価｜...」から会社名だけ抽出
                title = re.split(r"[（(]" + re.escape(code) + r"[）)]", title)[0].strip()
                title = re.sub(r"\s*[-|｜].*$", "", title).strip()
                if title and code not in title and len(title) <= 80:
                    return title
    except Exception:
        pass

    # 3. yfinanceから取得（日本語が返る場合はそのまま利用）
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info
        for field in ["longName", "shortName"]:
            name = info.get(field, "")
            if name:
                ascii_ratio = sum(1 for c in name if ord(c) < 128) / max(len(name), 1)
                if ascii_ratio < 0.7:
                    return name
        # 英語名しか返らない場合は、英語名を画面に出さずコードへフォールバック。
        # 日本語名マスタまたはYahoo!ファイナンス日本版から取れた名前を優先する。
        candidate = info.get("shortName") or info.get("longName") or ""
        ascii_ratio = sum(1 for c in candidate if ord(c) < 128) / max(len(candidate), 1)
        return candidate if candidate and ascii_ratio < 0.7 else ticker
    except Exception:
        return ticker

def score_stock(ticker, name):
    # 保存済みwatchlistに古い英語名が残っていても、表示時は日本語名を再解決する。
    display_name = get_company_name(ticker)
    if display_name and display_name != ticker:
        name = display_name
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
        add_btn = st.button("追加", width='stretch', type="primary")
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
    """スコアボード用カード。main側で2列に配置する。"""
    if "error" in r:
        st.error(f"**{r.get('name', r['ticker'])}（{r['ticker']}）** — {r['error']}")
        if st.button("削除", key=f"del_{r['ticker']}"):
            watchlist.pop(r["ticker"], None)
            save_watchlist(watchlist)
            st.cache_data.clear()
            st.rerun()
        return

    chg = safe_float(r.get("chg")) or 0
    chg_pct = safe_float(r.get("chg_pct")) or 0
    chg_cls = "price-change-pos" if chg >= 0 else "price-change-neg"
    chg_sign = "+" if chg >= 0 else ""
    v_label, _, v_cls = verdict(r["total"])
    fa, ch = r["funda"], r["chart"]

    def fmt(v, suffix=""):
        return f"{v}{suffix}" if v is not None else "—"

    st.markdown(f"""
    <div class="stock-grid-card">
      <div class="stock-grid-head">
        <div>
          <div class="ticker-label">{r['ticker']}</div>
          <div class="stock-grid-name">{r['name']}</div>
          <div class="stock-grid-price">
            ¥{r['price']:,.0f}
            <span class="{chg_cls}">{chg_sign}{chg:,.0f}（{chg_sign}{chg_pct:.2f}%）</span>
          </div>
        </div>
        <div style="text-align:right;min-width:70px">
          <div class="score-badge {r['score_cls']}" style="font-size:1.85rem">{r['total']}</div>
          <div style="font-size:.58rem;color:#4a7fa5">/ 100点</div>
          <div style="margin-top:.3rem"><span class="verdict {v_cls}">{v_label}</span></div>
        </div>
      </div>

      <div class="score-split">
        <div class="score-box">
          <div class="score-box-title">ファンダ</div>
          <div class="score-box-value">{fa['total']} / 50点</div>
          <div style="height:5px;background:#1e3a5f;border-radius:4px;margin-top:.35rem">
            <div style="width:{min(100, fa['total']*2)}%;height:5px;background:#4fc3f7;border-radius:4px"></div>
          </div>
        </div>
        <div class="score-box">
          <div class="score-box-title">チャート</div>
          <div class="score-box-value">{ch['total']} / 50点</div>
          <div style="height:5px;background:#1e3a5f;border-radius:4px;margin-top:.35rem">
            <div style="width:{min(100, ch['total']*2)}%;height:5px;background:#00e5a0;border-radius:4px"></div>
          </div>
        </div>
      </div>

      <div class="metric-row">
        <div class="metric-pill">PER {fmt(fa.get('per'),'倍')}</div>
        <div class="metric-pill">PBR {fmt(fa.get('pbr'),'倍')}</div>
        <div class="metric-pill">ROE {fmt(fa.get('roe'),'%')}</div>
        <div class="metric-pill">RSI {fmt(ch.get('rsi'))}</div>
        <div class="metric-pill">52週 {fmt(ch.get('range_pos'),'%')}</div>
        <div class="metric-pill">配当 {fmt(fa.get('div_yield'),'%')}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("✕ 削除", key=f"del_{r['ticker']}", help=f"{r['name']}を削除"):
        watchlist.pop(r["ticker"], None)
        save_watchlist(watchlist)
        st.cache_data.clear()
        st.rerun()

def _latest_journal_for_ticker(ticker):
    entries = [j for j in load_journal() if j.get("ticker") == ticker]
    return entries[0] if entries else None


def _fmt_yen(v):
    return f"¥{v:,.0f}" if v is not None else "—"


def render_detail(r):
    """銘柄詳細＋トレード日誌を一体化したコンパクト画面"""
    if "error" in r:
        st.error(r.get("error", "データ取得エラー"))
        return
    fa, ch = r["funda"], r["chart"]
    latest = _latest_journal_for_ticker(r["ticker"])
    current_price = safe_float(r.get("price")) or 0
    chg_cls = "price-change-pos" if r.get("chg", 0) >= 0 else "price-change-neg"
    chg_sign = "+" if r.get("chg", 0) >= 0 else ""
    v_label, _, v_cls = verdict(r["total"])

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0b1830,#0d223f);border:1px solid #1e3a5f;border-radius:8px;padding:.72rem .9rem;margin-bottom:.4rem">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:1rem">
        <div><div class="ticker-label">{r['ticker']}</div><div style="font-size:1.35rem;font-weight:700;color:#e8f4ff;line-height:1.1">{r['name']}</div></div>
        <div style="display:flex;align-items:center;gap:1.25rem;text-align:right">
          <div><div style="font-family:'IBM Plex Mono',monospace;font-size:1.5rem;color:#e8f4ff">¥{current_price:,.0f}</div><div class="{chg_cls}" style="font-family:'IBM Plex Mono',monospace;font-size:.72rem">{chg_sign}{r.get('chg',0):,.0f} ({chg_sign}{r.get('chg_pct',0):.2f}%)</div></div>
          <div><div class="score-badge {r['score_cls']}" style="font-size:2rem">{r['total']}</div><div style="font-size:.58rem;color:#4a7fa5">/ 100点</div></div>
          <span class="verdict {v_cls}">{v_label}</span>
        </div>
      </div>
      <div style="display:grid;grid-template-columns:repeat(7,1fr);margin-top:.55rem;border-top:1px solid #1e3a5f;padding-top:.45rem;font-size:.72rem">
        <div><span style="color:#4a7fa5;font-size:.58rem">PER</span><br><b>{fa.get('per'):.1f}倍</b></div>
        <div><span style="color:#4a7fa5;font-size:.58rem">PBR</span><br><b>{fa.get('pbr'):.2f}倍</b></div>
        <div><span style="color:#4a7fa5;font-size:.58rem">ROE</span><br><b>{fa.get('roe')}%</b></div>
        <div><span style="color:#4a7fa5;font-size:.58rem">RSI</span><br><b>{ch.get('rsi','—')}</b></div>
        <div><span style="color:#4a7fa5;font-size:.58rem">52週位置</span><br><b>{ch.get('range_pos','—')}%</b></div>
        <div><span style="color:#4a7fa5;font-size:.58rem">配当利回り</span><br><b>{fa.get('div_yield','—')}%</b></div>
        <div><span style="color:#4a7fa5;font-size:.58rem">ファンダ</span><br><b>{fa['total']}/50</b></div>
      </div>
    </div>""", unsafe_allow_html=True)

    left, right = st.columns([0.72, 1.9], gap="small")
    with left:
        st.markdown('<div class="section-head">スコア内訳</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:#0d1f3c;border:1px solid #1e3a5f;border-radius:7px;padding:.65rem .75rem">
          <div style="display:flex;justify-content:space-between;font-size:.72rem"><span>ファンダメンタルズ</span><b>{fa['total']}/50</b></div>
          <div style="height:5px;background:#1e3a5f;border-radius:4px;margin:.2rem 0 .6rem"><div style="width:{fa['total']*2}%;height:5px;background:#4fc3f7;border-radius:4px"></div></div>
          <div style="display:flex;justify-content:space-between;font-size:.72rem"><span>テクニカル</span><b>{ch['total']}/50</b></div>
          <div style="height:5px;background:#1e3a5f;border-radius:4px;margin-top:.2rem"><div style="width:{ch['total']*2}%;height:5px;background:#00e5a0;border-radius:4px"></div></div>
        </div>""", unsafe_allow_html=True)
        with st.expander("🤖 AIコメント", expanded=False):
            if st.button("AI分析を生成", key=f"detail_ai_{r['ticker']}"):
                with st.spinner("AI分析中…"):
                    ms = fetch_market_indices()
                    entries = [j for j in load_journal() if j.get("ticker") == r["ticker"]]
                    st.session_state[f"detail_ai_result_{r['ticker']}"] = call_gemini(build_analysis_prompt(r["ticker"], r["name"], r, entries, ms))
            if st.session_state.get(f"detail_ai_result_{r['ticker']}"):
                st.markdown(st.session_state[f"detail_ai_result_{r['ticker']}"])
            else:
                st.caption("必要なときだけAI分析を生成できます。")

    with right:
        st.markdown('<div class="section-head">株価チャート（2年）</div>', unsafe_allow_html=True)
        hist, _, _ = fetch_stock_data(r["ticker"])
        if hist is not None and len(hist) > 0:
            hist = hist.reset_index()
            for ma in (25,75,200): hist[f"MA{ma}"] = hist["Close"].rolling(ma).mean()
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=hist["Date"],open=hist["Open"],high=hist["High"],low=hist["Low"],close=hist["Close"],name="株価",increasing_line_color="#00e5a0",decreasing_line_color="#ef5350"))
            for col,color,lbl in [("MA25","#ffd54f","25MA"),("MA75","#4fc3f7","75MA"),("MA200","#ff7043","200MA")]:
                fig.add_trace(go.Scatter(x=hist["Date"],y=hist[col],line=dict(color=color,width=1),name=lbl,opacity=.75))
            if current_price:
                fig.add_hline(y=current_price,line_dash="dot",line_color="#00e5a0",opacity=.75,annotation_text=f"IN / 現在値 ¥{current_price:,.0f}",annotation_position="top left")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#0a0f1e",font_color="#e8f4ff",xaxis=dict(gridcolor="#1e3a5f",rangeslider_visible=False),yaxis=dict(gridcolor="#1e3a5f"),legend=dict(bgcolor="rgba(0,0,0,0)",orientation="h",y=1.02),height=300,margin=dict(l=0,r=0,t=16,b=0))
            st.plotly_chart(fig,width='stretch',config={"displayModeBar":False})
        else:
            st.info("チャートデータを取得できませんでした。")

    st.markdown('<div class="section-head" style="margin-top:.05rem">トレード計画 ＆ トレード日誌</div>', unsafe_allow_html=True)
    plan_col, journal_col = st.columns([0.72,1.45], gap="small")
    with plan_col:
        stop_default = safe_float(latest.get("stop_point")) if latest else None
        target_default = safe_float(latest.get("target_point")) if latest else None
        rr = None
        if current_price and stop_default and target_default and abs(current_price-stop_default)>0: rr=abs(target_default-current_price)/abs(current_price-stop_default)
        st.markdown(f"""
        <div style="background:#0d1f3c;border:1px solid #1e3a5f;border-radius:7px;padding:.6rem .7rem">
          <div style="font-size:.88rem;font-weight:700;margin-bottom:.4rem">トレードプラン</div>
          <div style="display:grid;grid-template-columns:1fr auto;gap:.3rem .6rem;font-size:.75rem">
            <span style="color:#7fb3d3">IN（エントリー）</span><b style="color:#00e5a0">{_fmt_yen(current_price)}（現在価格）</b>
            <span style="color:#7fb3d3">利益目標（TGT）</span><b style="color:#4fc3f7">{_fmt_yen(target_default)}</b>
            <span style="color:#7fb3d3">損切り（STOP）</span><b style="color:#ef5350">{_fmt_yen(stop_default)}</b>
            <span style="color:#7fb3d3">リスク/リワード</span><b>{f'1 : {rr:.2f}' if rr else '—'}</b>
          </div>
        </div>""", unsafe_allow_html=True)
        with st.expander("✏️ 新しいトレード記録", expanded=False):
            journal=load_journal()
            j_date=st.date_input("日付",value=datetime.now().date(),key=f"jdate_{r['ticker']}")
            position_type=st.selectbox("種別",["現物買い","信用買い","仮想（検討中）","売り"],key=f"ptype_{r['ticker']}")
            in_point=st.number_input("INライン（現在値）",min_value=0.0,value=float(current_price),step=1.0,format="%.0f",key=f"in_{r['ticker']}")
            p1,p2=st.columns(2)
            with p1: stop_point=st.number_input("損切り",min_value=0.0,value=float(stop_default or 0),step=1.0,format="%.0f",key=f"stop_{r['ticker']}")
            with p2: target_point=st.number_input("目標",min_value=0.0,value=float(target_default or 0),step=1.0,format="%.0f",key=f"tgt_{r['ticker']}")
            trend_dir=st.selectbox("トレンド",["上昇","下降","横ばい（保ち合い）","底値圏","天井圏"],key=f"trend_{r['ticker']}")
            volume_judge=st.selectbox("出来高",["増加（買い圧力あり）","減少","変化なし","急増（注目）"],key=f"vol_{r['ticker']}")
            ma_status=st.selectbox("MA状況",["25MA > 75MA > 200MA（強気配列）","200MAを上抜け（転換シグナル）","200MAに接触中（サポート確認）","25MA < 75MA < 200MA（弱気配列）","MA収束中（ブレイク待ち）","その他"],key=f"ma_{r['ticker']}")
            pattern=st.selectbox("チャートパターン",["底値圏での出来高増加","ダブルボトム形成中","ゴールデンクロス直前","三角保ち合いブレイク","高値更新（上昇継続）","デッドクロス警戒","特になし"],key=f"pattern_{r['ticker']}")
            tech_comment=st.text_area("テクニカル根拠",height=55,key=f"tech_{r['ticker']}")
            general_comment=st.text_area("総合所見",height=55,key=f"general_{r['ticker']}")
            confidence=st.select_slider("確信度",options=[1,2,3,4,5],format_func=lambda x:"★"*x,key=f"conf_{r['ticker']}")
            if st.button("📝 保存",type="primary",width='stretch',key=f"savej_{r['ticker']}"):
                if tech_comment or general_comment:
                    risk=abs(in_point-stop_point) if in_point and stop_point else 0; reward=abs(target_point-in_point) if in_point and target_point else 0; rr_ratio=round(reward/risk,2) if risk else None
                    journal.insert(0,{"id":datetime.now().strftime("%Y%m%d%H%M%S%f"),"date":str(j_date),"ticker":r["ticker"],"name":r["name"],"position_type":position_type,"current_price":current_price,"in_point":current_price,"stop_point":stop_point or None,"target_point":target_point or None,"rr_ratio":rr_ratio,"trend_dir":trend_dir,"volume_judge":volume_judge,"ma_status":ma_status,"pattern":pattern,"tech_comment":tech_comment,"general_comment":general_comment,"confidence":confidence,"exit_date":None,"exit_price":None,"pnl":None,"pnl_pct":None,"result":"保有中","score_at_entry":r["total"]})
                    save_journal(journal); st.success("保存しました"); st.rerun()
                else: st.warning("テクニカル根拠または総合所見を入力してください")

    with journal_col:
        journal=load_journal(); entries=[j for j in journal if j.get("ticker")==r["ticker"]]
        st.markdown(f'<div style="font-size:.88rem;font-weight:700;margin-bottom:.3rem">トレード日誌 <span style="color:#4a7fa5;font-size:.66rem">{len(entries)}件</span></div>',unsafe_allow_html=True)
        if not entries: st.info("この銘柄の記録はまだありません。")
        else:
            for entry in entries[:6]:
                result=entry.get("result","保有中"); result_color="#00e5a0" if result=="利確" else "#ef5350" if result=="損切" else "#ffd54f"; pnl=entry.get("pnl_pct"); pnl_text=f" / {pnl:+.2f}%" if pnl is not None else ""
                st.markdown(f"""
                <div style="background:#0d1f3c;border:1px solid #1e3a5f;border-radius:6px;padding:.45rem .6rem;margin-bottom:.28rem">
                  <div style="display:grid;grid-template-columns:85px 1fr auto;gap:.45rem;align-items:center"><span style="font-family:'IBM Plex Mono',monospace;font-size:.62rem;color:#7fb3d3">{entry.get('date','')}</span><span style="font-size:.7rem;color:#e8f4ff">{entry.get('general_comment') or entry.get('tech_comment') or 'メモ'}</span><span style="font-size:.65rem;color:{result_color};font-weight:700">{result}{pnl_text}</span></div>
                  <div style="display:flex;gap:.7rem;margin-top:.2rem;font-size:.61rem;color:#7fb3d3"><span>IN {_fmt_yen(entry.get('in_point'))}</span><span>損切 {_fmt_yen(entry.get('stop_point'))}</span><span>目標 {_fmt_yen(entry.get('target_point'))}</span><span>★{entry.get('confidence',1)}</span></div>
                </div>""",unsafe_allow_html=True)
                if result=="保有中" and entry.get("in_point"):
                    with st.expander(f"決済を記録　{entry.get('date','')}",expanded=False):
                        ex1,ex2,ex3=st.columns(3)
                        with ex1: exit_price_input=st.number_input("決済価格",min_value=0.0,step=1.0,format="%.0f",key=f"exit_price_{entry['id']}")
                        with ex2: exit_date_input=st.date_input("決済日",value=datetime.now().date(),key=f"exit_date_{entry['id']}")
                        with ex3: exit_result=st.selectbox("結果",["利確","損切","期限切れ"],key=f"exit_result_{entry['id']}")
                        if st.button("決済を保存",key=f"exit_save_{entry['id']}",type="primary") and exit_price_input>0:
                            in_p=entry.get("in_point",0); pnl_val=exit_price_input-in_p; pnl_pct_val=round(pnl_val/in_p*100,2) if in_p else 0
                            for j in journal:
                                if j.get("id")==entry.get("id"):
                                    j.update({"exit_price":exit_price_input,"exit_date":str(exit_date_input),"pnl":round(pnl_val,0),"pnl_pct":pnl_pct_val,"result":exit_result}); break
                            save_journal(journal); st.rerun()
                if st.button("削除",key=f"jdel_detail_{entry['id']}"):
                    save_journal([j for j in journal if j.get("id")!=entry.get("id")]); st.rerun()

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
    st.plotly_chart(fig, width='stretch')

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

    if st.button("📝 メモを保存", type="primary", width='stretch'):
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
                # 決済フィールド（初期値はNone）
                "exit_date":     None,
                "exit_price":    None,
                "pnl":           None,
                "pnl_pct":       None,
                "result":        "保有中",
                "score_at_entry": None,
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

            # 決済済みか判定
            result      = entry.get("result", "保有中")
            pnl_pct     = entry.get("pnl_pct")
            exit_price  = entry.get("exit_price")
            result_color = "#00e5a0" if result == "利確" else "#ef5350" if result == "損切" else "#7fb3d3"
            pnl_str = f"{pnl_pct:+.2f}%" if pnl_pct is not None else ""

            card_col, del_col = st.columns([12, 1])
            with card_col:
                st.markdown(f"""
                <div class="journal-card">
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">
                    <div>
                      <span class="journal-ticker">{entry['ticker']} {entry['name']}</span>
                      <span style="font-family:'IBM Plex Mono',monospace;font-size:0.7rem;color:#4a7fa5;margin-left:0.8rem;">{entry['date']}</span>
                      <span style="font-size:0.7rem;color:{pcolor};margin-left:0.8rem;font-weight:700;">{ptype}</span>
                      <span style="font-size:0.7rem;color:{result_color};margin-left:0.8rem;font-weight:700;">{result} {pnl_str}</span>
                    </div>
                    <span class="confidence-star" style="font-size:0.8rem;">{stars}</span>
                  </div>
                  <div style="display:flex;gap:1rem;margin-bottom:0.6rem;background:#0a0f1e;border-radius:6px;padding:0.5rem 0.8rem;">
                    <span style="font-size:0.7rem;color:#7fb3d3;">{cur_p}</span>
                    <span class="price-line-in">IN {in_str}</span>
                    <span class="price-line-stop">損切 {stop_str}</span>
                    <span class="price-line-tgt">目標 {tgt_str}</span>
                    <span style="font-family:'IBM Plex Mono',monospace;font-size:0.7rem;color:#a78bfa;">{rr_str}</span>
                    {"<span style='font-family:IBM Plex Mono,monospace;font-size:0.7rem;color:#7fb3d3;'>決済 ¥" + f"{exit_price:,.0f}" + "</span>" if exit_price else ""}
                  </div>
                  <div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:0.6rem;">
                    <span style="background:#0a2a1a;color:#00e5a0;border:1px solid #00e5a040;border-radius:4px;padding:0.15rem 0.5rem;font-size:0.68rem;">{entry.get('trend_dir','')}</span>
                    <span style="background:#1a1a0a;color:#ffd54f;border:1px solid #ffd54f40;border-radius:4px;padding:0.15rem 0.5rem;font-size:0.68rem;">{entry.get('volume_judge','')}</span>
                    <span style="background:#0a1a2a;color:#4fc3f7;border:1px solid #4fc3f740;border-radius:4px;padding:0.15rem 0.5rem;font-size:0.68rem;">{entry.get('pattern','')}</span>
                  </div>
                  <div style="font-size:0.75rem;color:#7fb3d3;margin-bottom:0.4rem;">📐 {entry.get('ma_status','')}</div>
                  {"<div style='font-size:0.85rem;color:#b0c4d8;margin-bottom:0.3rem;'>🔍 " + entry['tech_comment'] + "</div>" if entry.get('tech_comment') else ""}
                  {"<div style='font-size:0.85rem;color:#e8f4ff;'>💬 " + entry['general_comment'] + "</div>" if entry.get('general_comment') else ""}
                </div>
                """, unsafe_allow_html=True)

                # 決済記録フォーム（保有中のみ表示）
                if result == "保有中" and entry.get("in_point"):
                    with st.expander(f"📤 決済を記録する"):
                        ex1, ex2, ex3 = st.columns(3)
                        with ex1:
                            exit_price_input = st.number_input(
                                "決済価格（円）", min_value=0.0, step=1.0, format="%.0f",
                                key=f"exit_price_{entry['id']}"
                            )
                        with ex2:
                            exit_date_input = st.date_input(
                                "決済日", value=datetime.now().date(),
                                key=f"exit_date_{entry['id']}"
                            )
                        with ex3:
                            exit_result = st.selectbox(
                                "結果", ["利確", "損切", "期限切れ"],
                                key=f"exit_result_{entry['id']}"
                            )
                        if st.button("決済を保存", key=f"exit_save_{entry['id']}", type="primary"):
                            if exit_price_input > 0:
                                in_p = entry.get("in_point", 0)
                                pnl_val = exit_price_input - in_p
                                pnl_pct_val = round(pnl_val / in_p * 100, 2) if in_p > 0 else 0
                                for j in journal:
                                    if j["id"] == entry["id"]:
                                        j["exit_price"] = exit_price_input
                                        j["exit_date"]  = str(exit_date_input)
                                        j["pnl"]        = round(pnl_val, 0)
                                        j["pnl_pct"]    = pnl_pct_val
                                        j["result"]     = exit_result
                                        break
                                save_journal(journal)
                                st.success(f"決済記録を保存しました（損益: {pnl_pct_val:+.2f}%）")
                                st.rerun()

            with del_col:
                st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
                if st.button("✕", key=f"jdel_{entry['id']}", help="削除"):
                    journal = [j for j in journal if j["id"] != entry["id"]]
                    save_journal(journal)
                    st.rerun()

def call_gemini(prompt: str) -> str:
    """Gemini APIを呼び出す"""
    try:
        import urllib.request, urllib.error
        api_key = st.secrets.get("GEMINI_API_KEY", "")
        if not api_key:
            return "APIキーが設定されていません。StreamlitのSecretsにGEMINI_API_KEYを追加してください。"
        models = [
            "gemini-3-flash-preview",
            "gemini-3.1-flash-lite",
            "gemini-flash-latest",
        ]
        last_error = ""
        for model in models:
            try:
                url  = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                body = json.dumps({
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048}
                }).encode("utf-8")
                req = urllib.request.Request(
                    url, data=body,
                    headers={"Content-Type": "application/json; charset=utf-8"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=30) as res:
                    data = json.loads(res.read().decode("utf-8"))
                    return data["candidates"][0]["content"]["parts"][0]["text"]
            except urllib.error.HTTPError as e:
                last_error = f"モデル{model}: HTTP {e.code} / {e.read().decode('utf-8', errors='ignore')}"
                continue
            except Exception as e:
                last_error = str(e)
                continue
        return f"全モデルで失敗しました。最後のエラー：{last_error}"
    except Exception as e:
        return f"エラー：{e}"


def build_analysis_prompt(ticker, name, score_data, journal_entries, market_scores):
    fa = score_data.get("funda", {})
    ch = score_data.get("chart", {})
    n225  = market_scores.get("^N225",  {}).get("trend", "—")
    topix = market_scores.get("1306.T", {}).get("trend", "—")
    fx    = market_scores.get("JPY=X",  {}).get("trend", "—")

    journal_text = ""
    if journal_entries:
        for e in journal_entries[:20]:
            journal_text += f"""
  【{e['date']} / {e.get('position_type','')} / {e.get('result','保有中')}】
  トレンド: {e.get('trend_dir','')} / 出来高: {e.get('volume_judge','')}
  MA状況: {e.get('ma_status','')} / パターン: {e.get('pattern','')}
  IN: {e.get('in_point','—')}円 / 損切: {e.get('stop_point','—')}円 / 目標: {e.get('target_point','—')}円
  損益率: {e.get('pnl_pct','—')}%
  テクニカル根拠: {e.get('tech_comment','')}
  総合所見: {e.get('general_comment','')}
  確信度: {'★' * e.get('confidence', 1)}
"""
    else:
        journal_text = "  （メモなし）"

    return f"""
あなたは経験豊富な日本株アナリストです。以下のデータをもとに投資家への分析コメントを日本語で提供してください。

## 対象銘柄
{name}（{ticker}）

## スコアサマリー
- 総合スコア: {score_data.get('total', 0)}/100点
- ファンダスコア: {fa.get('total', 0)}/50点
- チャートスコア: {ch.get('total', 0)}/50点

## ファンダメンタルズ
- PER: {fa.get('per', '—')}倍 / PBR: {fa.get('pbr', '—')}倍
- ROE: {fa.get('roe', '—')}% / 売上成長率: {fa.get('rev_growth', '—')}%
- 配当利回り: {fa.get('div_yield', '—')}%

## テクニカル指標
- RSI(14): {ch.get('rsi', '—')}
- MA25: {ch.get('ma25', '—')}円 / MA75: {ch.get('ma75', '—')}円 / MA200: {ch.get('ma200', '—')}円
- BB位置: {ch.get('bb_pos', '—')}% / 52週レンジ位置: {ch.get('range_pos', '—')}%

## 市場環境
- 日経平均: {n225} / TOPIX ETF: {topix} / ドル円: {fx}

## 投資家のトレード日誌（直近20件）
{journal_text}

## 回答形式（400〜600文字）

【総合判断】買い / 様子見 / 見送り のいずれかと理由

【ポジティブ要因】箇条書き2〜3点

【リスク・懸念点】箇条書き2〜3点

【具体的なアクション提案】
INタイミング、損切水準、目標株価を数字で示してください。

【一言コメント】投資家へのメッセージ
"""

from pathlib import Path

AI_PREDICTIONS_FILE = Path("data/ai_predictions.json")

def load_daily_ai_predictions():
    """GitHub上の最新 predictions.json を直接取得する"""

    try:
        import urllib.request
        import time

        repo = "perfume9164-afk/stock-tool"

        # GitHubのrawファイルを直接取得
        url = (
            f"https://raw.githubusercontent.com/"
            f"{repo}/main/data/ai_predictions.json"
            f"?t={int(time.time())}"
        )

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "stock-tool-streamlit"
            }
        )

        with urllib.request.urlopen(req, timeout=15) as res:
            text = res.read().decode("utf-8-sig")

        return json.loads(text)

    except Exception as e:
        st.error(f"AI予想データの読み込みに失敗しました: {e}")
        return {}

def render_daily_ai_prediction_tab(watchlist):
    """毎日の出来高スキャン＋AI予想を表示"""

    data = load_daily_ai_predictions()

    st.markdown(
        '<div class="section-head">📡 DAILY VOLUME SCAN & AI予想</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div style="
        background:#0d1f3c;
        border:1px solid #1e3a5f;
        border-radius:9px;
        padding:.8rem 1rem;
        margin-bottom:.8rem;
        color:#9db7cf;
        font-size:.78rem;
        line-height:1.7;
    ">
    <b style="color:#e8f4ff;">毎日自動スキャン：</b>
    主要プライム銘柄 約300社 → 当日出来高TOP50 → ファンダ＋チャート採点 → GeminiでTOP10を選定。
    </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # データがない場合
    # ---------------------------------------------------------
    if not data:
        st.info(
            "まだ自動スキャン結果がありません。\n\n"
            "GitHub Actionsを手動実行するか、PowerShellで "
            "`python screener.py` を実行してください。"
        )
        st.divider()
        render_ai_tab(watchlist)
        return

    # ---------------------------------------------------------
    # predictions.json の形式に対応
    # ---------------------------------------------------------
    if isinstance(data, list):
        if len(data) == 0:
            st.info("AI予想データがありません。")
            return
        entry = data[0]
    else:
        entry = data

    date_str = entry.get("date", "—")
    generated = entry.get("generated_at", "—")

    if generated and len(generated) >= 16:
        generated = generated[:16]

    top10 = entry.get("top10", entry.get("ai_top10", []))
    ai_comment = entry.get("ai_comment", "")
    user_comments = entry.get("user_comments", [])

    # ---------------------------------------------------------
    # 更新日時
    # ---------------------------------------------------------
    st.markdown(
        f"**{date_str} 引け後スキャン** ｜ 生成: {generated}"
    )

        # =========================================================
    # 本日のTOP10
    # =========================================================

    # predictions.json / ai_predictions.json の両方に対応
    if isinstance(data, list):
        top10 = data[0].get("top10", data[0].get("ai_top10", [])) if data else []
    else:
        top10 = data.get("top10", data.get("ai_top10", []))

    if top10:

        st.markdown(
            '<div class="section-head" style="margin-top:.8rem;">🎯 本日の注目10銘柄</div>',
            unsafe_allow_html=True
        )

        # ---------------------------------------------------------
        # 日本語会社名
        # ---------------------------------------------------------
        company_names = {
            "1332.T": "ニッスイ",
            "1605.T": "INPEX",
            "1801.T": "大成建設",
            "1802.T": "大林組",
            "1803.T": "清水建設",
            "1925.T": "大和ハウス工業",
            "1928.T": "積水ハウス",
            "2181.T": "パーソルホールディングス",
            "2413.T": "エムスリー",
            "2502.T": "アサヒグループホールディングス",
            "2802.T": "味の素",
            "2914.T": "日本たばこ産業",
            "3382.T": "セブン＆アイ・ホールディングス",
            "3402.T": "東レ",
            "3407.T": "旭化成",
            "4004.T": "レゾナック・ホールディングス",
            "4005.T": "住友化学",
            "4188.T": "三菱ケミカルグループ",
            "4502.T": "武田薬品工業",
            "4519.T": "中外製薬",
            "4523.T": "エーザイ",
            "4568.T": "第一三共",
            "4661.T": "オリエンタルランド",
            "4901.T": "富士フイルムホールディングス",
            "5020.T": "ENEOSホールディングス",
            "5108.T": "ブリヂストン",
            "5401.T": "日本製鉄",
            "5406.T": "神戸製鋼所",
            "5411.T": "JFEホールディングス",
            "5802.T": "住友電気工業",
            "6098.T": "リクルートホールディングス",
            "6178.T": "日本郵政",
            "6301.T": "コマツ",
            "6501.T": "日立製作所",
            "6503.T": "三菱電機",
            "6504.T": "富士電機",
            "6752.T": "パナソニック ホールディングス",
            "6758.T": "ソニーグループ",
            "6861.T": "キーエンス",
            "6902.T": "デンソー",
            "7011.T": "三菱重工業",
            "7013.T": "IHI",
            "7201.T": "日産自動車",
            "7203.T": "トヨタ自動車",
            "7267.T": "ホンダ",
            "7733.T": "オリンパス",
            "7741.T": "HOYA",
            "7751.T": "キヤノン",
            "7974.T": "任天堂",
            "8001.T": "伊藤忠商事",
            "8002.T": "丸紅",
            "8031.T": "三井物産",
            "8053.T": "住友商事",
            "8058.T": "三菱商事",
            "8306.T": "三菱UFJフィナンシャル・グループ",
            "8308.T": "りそなホールディングス",
            "8309.T": "三井住友トラストグループ",
            "8316.T": "三井住友フィナンシャルグループ",
            "8411.T": "みずほフィナンシャルグループ",
            "8601.T": "大和証券グループ本社",
            "8604.T": "野村ホールディングス",
            "8750.T": "第一生命ホールディングス",
            "8766.T": "東京海上ホールディングス",
            "8801.T": "三井不動産",
            "8802.T": "三菱地所",
            "8830.T": "住友不動産",
            "9020.T": "東日本旅客鉄道",
            "9021.T": "西日本旅客鉄道",
            "9022.T": "東海旅客鉄道",
            "9101.T": "日本郵船",
            "9104.T": "商船三井",
            "9107.T": "川崎汽船",
            "9201.T": "日本航空",
            "9202.T": "ANAホールディングス",
            "9432.T": "NTT",
            "9433.T": "KDDI",
            "9434.T": "ソフトバンク",
            "9501.T": "東京電力ホールディングス",
            "9502.T": "中部電力",
            "9503.T": "関西電力",
            "9513.T": "電源開発",
            "9531.T": "東京ガス",
            "9532.T": "大阪ガス",
            "9983.T": "ファーストリテイリング",
            "9984.T": "ソフトバンクグループ",
        }

        cols = st.columns(2)

        for i, s in enumerate(top10, 1):

            ticker = s.get("ticker", "")

            # 日本語名が登録されていれば使用
            # なければJSONのnameを使用
            name = company_names.get(
                ticker,
                s.get("name", "")
            )

            price = safe_float(
                s.get("price")
            ) or 0

            score = safe_float(
                s.get("total_score", s.get("total", 0))
            ) or 0

            chg = safe_float(
                s.get("chg_pct")
            ) or 0

            volume = s.get("volume", 0)

            # chartの中に入っている場合にも対応
            chart = s.get("chart", {})

            if not isinstance(chart, dict):
                chart = {}

            rsi = s.get(
                "rsi",
                chart.get("rsi", "—")
            )

            range_pos = s.get(
                "range_pos",
                chart.get("range_pos", "—")
            )

            # -------------------------------------------------
            # AI個別理由
            #
            # JSONの形式が多少違っても拾えるようにする
            # -------------------------------------------------
            reason = (
                s.get("reason")
                or s.get("ai_reason")
                or s.get("analysis")
                or s.get("comment")
                or s.get("ai_comment")
                or ""
            )

            verdict_text = (
                s.get("verdict")
                or s.get("prediction")
                or s.get("forecast")
                or ""
            )

            # -------------------------------------------------
            # スコアカラー
            # -------------------------------------------------
            if score >= 80:
                score_color = "#00e5a0"
            elif score >= 65:
                score_color = "#4fc3f7"
            elif score >= 50:
                score_color = "#ffd54f"
            else:
                score_color = "#ef5350"

            # -------------------------------------------------
            # 騰落率
            # -------------------------------------------------
            chg_color = "#00a67d" if chg >= 0 else "#e5484d"

            # -------------------------------------------------
            # 2列表示
            # -------------------------------------------------
            with cols[(i - 1) % 2]:

                st.markdown(
                    f"### #{i} {name}"
                )

                st.caption(ticker)

                c1, c2 = st.columns(2)

                with c1:
                    st.metric(
                        "株価",
                        f"¥{price:,.0f}",
                        f"{chg:+.2f}%"
                    )

                with c2:
                    st.metric(
                        "総合スコア",
                        f"{score:.0f} / 100"
                    )

                st.write(
                    f"出来高：{volume:,}　"
                    f"RSI：{rsi}　"
                    f"52週位置：{range_pos}%"
                )

                # -------------------------------------------------
                # AI予想
                # -------------------------------------------------
                if verdict_text:
                    st.markdown(
                        f"**予想：{verdict_text}**"
                    )

                # -------------------------------------------------
                # AI個別理由
                # -------------------------------------------------
                if reason:

                    st.info(
                        f"🤖 AI判断\n\n{reason}"
                    )

                else:

                    st.caption(
                        "🤖 個別のAI判断理由は、下の「AIトレード予想・市場コメント」を参照してください。"
                    )

                st.divider()

    # =========================================================
    # GeminiによるAIトレード予想・市場コメント
    # =========================================================

    if ai_comment:

        st.divider()

        st.markdown(
            "### 🤖 AIトレード予想・市場コメント"
        )

        # AIの文章をそのままMarkdownとして表示
        # HTMLとして解釈させないので途中で構文が壊れにくい
        st.markdown(
            ai_comment
        )

    # =========================================================
    # ユーザーコメント
    # =========================================================

    st.divider()

    st.markdown(
        "### 💬 あなたのコメントを追加"
    )

    with st.expander(
        "コメントを追加する",
        expanded=True
    ):

        comment_ticker = st.selectbox(
            "対象銘柄",
            ["全体へのコメント"]
            + [
                f"{s.get('ticker', '')} "
                f"{company_names.get(s.get('ticker', ''), s.get('name', ''))}"
                for s in top10
            ],
            key="pred_ticker"
        )

        comment_text = st.text_area(
            "コメント・見解",
            height=100,
            key="pred_comment"
        )

        agree = st.radio(
            "AI予想との一致度",
            [
                "同意",
                "部分同意",
                "異論あり",
                "コメントのみ"
            ],
            horizontal=True,
            key="pred_agree"
        )

        if st.button(
            "💾 コメントを保存",
            type="primary"
        ):

            if comment_text:

                predictions = load_json(
                    "predictions.json",
                    []
                )

                if isinstance(predictions, list) and predictions:

                    predictions[0].setdefault(
                        "user_comments",
                        []
                    ).insert(
                        0,
                        {
                            "id": datetime.now().strftime(
                                "%Y%m%d%H%M%S"
                            ),
                            "timestamp": datetime.now().isoformat(),
                            "ticker": comment_ticker,
                            "comment": comment_text,
                            "agree": agree,
                        }
                    )

                    save_json(
                        "predictions.json",
                        predictions
                    )

                    st.success(
                        "コメントを保存しました ✅"
                    )

                    st.rerun()

    # =========================================================
    # 過去コメント
    # =========================================================
    if user_comments:

        st.markdown(
            f'<div class="section-head" style="margin-top:1rem;">'
            f'過去のコメント（{len(user_comments)}件）'
            f'</div>',
            unsafe_allow_html=True
        )

        for c in user_comments:

            agree = c.get("agree", "")

            if agree == "同意":
                agree_color = "#00e5a0"
            elif agree == "部分同意":
                agree_color = "#ffd54f"
            elif agree == "異論あり":
                agree_color = "#ef5350"
            else:
                agree_color = "#7fb3d3"

            st.markdown(f"""
            <div style="
                background:#0d1f3c;
                border:1px solid #1e3a5f;
                border-radius:8px;
                padding:.7rem .9rem;
                margin-bottom:.4rem;
            ">

                <div style="
                    display:flex;
                    justify-content:space-between;
                    margin-bottom:.3rem;
                ">

                    <span style="
                        font-family:'IBM Plex Mono',monospace;
                        font-size:.65rem;
                        color:#4a7fa5;
                    ">
                        {c.get('timestamp','')[:16]}
                        {c.get('ticker','')}
                    </span>

                    <span style="
                        font-size:.65rem;
                        font-weight:700;
                        color:{agree_color};
                    ">
                        {agree}
                    </span>

                </div>

                <div style="
                    font-size:.85rem;
                    color:#e8f4ff;
                    line-height:1.6;
                ">
                    {c.get('comment','')}
                </div>

            </div>
            """, unsafe_allow_html=True)

def render_ai_tab(watchlist):
    """AI分析タブ"""
    st.markdown('<div class="section-head">🤖 AI投資分析（Gemini）</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#0d1f3c;border:1px solid #1e3a5f;border-radius:8px;padding:0.8rem 1rem;margin-bottom:1rem;font-size:0.8rem;color:#7fb3d3;">
    ⚠️ 本機能はAIによる参考情報です。投資判断はご自身の責任で行ってください。
    </div>
    """, unsafe_allow_html=True)

    if not watchlist:
        st.info("サイドバーから銘柄を追加してください。")
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        selected = st.selectbox(
            "分析する銘柄を選択",
            list(watchlist.keys()),
            format_func=lambda t: f"{t}　{watchlist[t]}"
        )
    with col2:
        analyze_btn = st.button("🤖 AI分析を実行", type="primary", width='stretch')

    if analyze_btn:
        with st.spinner("データを収集してAIが分析中…（10〜20秒かかります）"):
            score_data    = score_stock(selected, watchlist[selected])
            market_scores = fetch_market_indices()
            journal       = load_journal()
            journal_entries = [j for j in journal if j["ticker"] == selected][:20]
            prompt = build_analysis_prompt(selected, watchlist[selected], score_data, journal_entries, market_scores)
            result = call_gemini(prompt)

        st.markdown(f"""
        <div style="background:#060d1a;border:1px solid #2d6a9f;border-radius:12px;padding:1.5rem;margin-top:1rem;line-height:1.8;color:#e8f4ff;font-size:0.9rem;white-space:pre-wrap;">{result}</div>
        """, unsafe_allow_html=True)

        st.divider()
        if st.button("📝 この分析をトレード日誌に保存"):
            journal = load_journal()
            entry = {
                "id":              datetime.now().strftime("%Y%m%d%H%M%S"),
                "date":            datetime.now().strftime("%Y-%m-%d"),
                "ticker":          selected,
                "name":            watchlist.get(selected, selected),
                "position_type":   "AI分析",
                "current_price":   score_data.get("price"),
                "in_point":        None, "stop_point": None, "target_point": None,
                "rr_ratio":        None,
                "trend_dir":       "—", "volume_judge": "—", "ma_status": "—",
                "pattern":         "AI自動分析",
                "tech_comment":    "",
                "general_comment": result,
                "confidence":      3,
                "exit_date":       None, "exit_price": None,
                "pnl":             None, "pnl_pct": None,
                "result":          "保有中", "score_at_entry": None,
            }
            journal.insert(0, entry)
            save_journal(journal)
            st.success("トレード日誌に保存しました ✅")


def render_correlation_tab(watchlist):
    """損益×スコア相関分析タブ"""
    st.markdown('<div class="section-head">📊 スコア × 損益 相関分析</div>', unsafe_allow_html=True)

    journal = load_journal()

    # 決済済みデータだけ抽出
    closed = [j for j in journal if j.get("result") in ["利確", "損切", "期限切れ"] and j.get("pnl_pct") is not None and j.get("in_point")]

    if len(closed) < 3:
        st.info(f"決済記録が3件以上になると分析が表示されます。現在: {len(closed)}件\n\nトレード日誌タブで決済を記録してください。")
        return

    df = pd.DataFrame(closed)

    # ─── サマリー指標 ───────────────────────────────
    total      = len(df)
    wins       = len(df[df["pnl_pct"] > 0])
    win_rate   = wins / total * 100
    avg_pnl    = df["pnl_pct"].mean()
    avg_win    = df[df["pnl_pct"] > 0]["pnl_pct"].mean() if wins > 0 else 0
    avg_loss   = df[df["pnl_pct"] <= 0]["pnl_pct"].mean() if (total - wins) > 0 else 0
    pf         = abs(avg_win / avg_loss) if avg_loss != 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("総トレード数", f"{total}件")
    c2.metric("勝率", f"{win_rate:.1f}%")
    c3.metric("平均損益", f"{avg_pnl:+.2f}%")
    c4.metric("平均利益", f"{avg_win:+.2f}%")
    c5.metric("プロフィットファクター", f"{pf:.2f}")

    st.divider()

    # ─── スコア帯別勝率 ───────────────────────────────
    st.markdown("**📈 スコア帯別 勝率・平均損益**")

    def score_band(s):
        if s is None: return "不明"
        if s >= 80: return "80〜100点（強買い）"
        if s >= 65: return "65〜79点（買い）"
        if s >= 50: return "50〜64点（様子見）"
        return "〜49点（見送り）"

    # score_at_entryがない場合はconfidenceで代替表示
    if df["score_at_entry"].isna().all():
        st.info("💡 スコアとの相関を見るには、銘柄詳細タブでスコアを確認してからトレード日誌に記録してください。現在は確信度ベースで集計します。")
        df["band"] = df["confidence"].apply(lambda x: f"確信度 {'★'*int(x) if x else '—'}")
    else:
        df["band"] = df["score_at_entry"].apply(score_band)

    band_order = ["80〜100点（強買い）", "65〜79点（買い）", "50〜64点（様子見）", "〜49点（見送り）"]
    band_stats = df.groupby("band").agg(
        件数=("pnl_pct", "count"),
        勝率=("pnl_pct", lambda x: (x > 0).mean() * 100),
        平均損益=("pnl_pct", "mean"),
        最大利益=("pnl_pct", "max"),
        最大損失=("pnl_pct", "min"),
    ).round(2)

    st.dataframe(
        band_stats.style
            .format({"勝率": "{:.1f}%", "平均損益": "{:+.2f}%", "最大利益": "{:+.2f}%", "最大損失": "{:+.2f}%"})
            .background_gradient(subset=["勝率"], cmap="RdYlGn", vmin=0, vmax=100),
        width='stretch'
    )

    st.divider()

    # ─── 散布図：スコア vs 損益率 ───────────────────────────────
    if not df["score_at_entry"].isna().all():
        st.markdown("**🔵 スコア vs 損益率（散布図）**")
        fig = go.Figure()

        wins_df  = df[df["pnl_pct"] > 0]
        loses_df = df[df["pnl_pct"] <= 0]

        if len(wins_df) > 0:
            fig.add_trace(go.Scatter(
                x=wins_df["score_at_entry"], y=wins_df["pnl_pct"],
                mode="markers", name="利確",
                marker=dict(color="#00e5a0", size=10, opacity=0.8),
                text=wins_df["name"], hovertemplate="%{text}<br>スコア:%{x}<br>損益:%{y:.2f}%",
            ))
        if len(loses_df) > 0:
            fig.add_trace(go.Scatter(
                x=loses_df["score_at_entry"], y=loses_df["pnl_pct"],
                mode="markers", name="損切",
                marker=dict(color="#ef5350", size=10, opacity=0.8),
                text=loses_df["name"], hovertemplate="%{text}<br>スコア:%{x}<br>損益:%{y:.2f}%",
            ))

        # ゼロライン
        fig.add_hline(y=0, line_dash="dash", line_color="#4a7fa5", opacity=0.5)

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0a0f1e", font_color="#e8f4ff",
            xaxis=dict(title="エントリー時スコア", gridcolor="#1e3a5f", range=[0, 100]),
            yaxis=dict(title="損益率（%）", gridcolor="#1e3a5f"),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            height=350, margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig, width='stretch')
        st.divider()

    # ─── 損益推移 ───────────────────────────────
    st.markdown("**📉 損益推移（累積）**")
    df_sorted = df.sort_values("date")
    df_sorted["累積損益"] = df_sorted["pnl_pct"].cumsum()

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_sorted["date"], y=df_sorted["累積損益"],
        fill="tozeroy",
        line=dict(color="#4fc3f7", width=2),
        fillcolor="rgba(79,195,247,0.1)",
        name="累積損益",
    ))
    fig2.add_hline(y=0, line_dash="dash", line_color="#4a7fa5", opacity=0.5)
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0a0f1e", font_color="#e8f4ff",
        xaxis=dict(gridcolor="#1e3a5f"),
        yaxis=dict(title="累積損益率（%）", gridcolor="#1e3a5f"),
        height=250, margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig2, width='stretch')

    st.divider()

    # ─── 全決済記録テーブル ───────────────────────────────
    st.markdown("**📋 全決済記録**")
    df_display = df[["date", "name", "result", "in_point", "exit_price", "pnl_pct", "confidence"]].copy()
    df_display.columns = ["日付", "銘柄", "結果", "IN価格", "決済価格", "損益率(%)", "確信度"]
    df_display = df_display.sort_values("日付", ascending=False).reset_index(drop=True)
    st.dataframe(
        df_display.style.format({"損益率(%)": "{:+.2f}%", "IN価格": "¥{:,.0f}", "決済価格": "¥{:,.0f}"}),
        width='stretch'
    )


# ─── メイン ───────────────────────────────────────────────────
def main():
    st.markdown(f"""
    <div class="main-header">
      <h1>📈 日本株 AI スコアボード</h1>
      <div class="subtitle">ファンダメンタルズ＋チャート スコアリングエンジン</div>
    </div>
    """, unsafe_allow_html=True)

    watchlist = load_watchlist()

    # 既存watchlistの会社名を日本語へ更新
    changed = False

    for _ticker in list(watchlist.keys()):
        _jp_name = get_company_name(_ticker)

        if _jp_name and _jp_name != watchlist[_ticker]:
            watchlist[_ticker] = _jp_name
            changed = True

    if changed:
        save_watchlist(watchlist)

    history = load_history()

    # 以下、今までのmain処理

    with st.sidebar:
        render_watchlist_manager(watchlist)
        watchlist = load_watchlist()
        # 追加・再読込後も日本語名を維持
        for _ticker in list(watchlist.keys()):
            _jp_name = get_company_name(_ticker)
            if _jp_name and _jp_name != _ticker:
                watchlist[_ticker] = _jp_name
        save_watchlist(watchlist)
        st.divider()
        st.markdown('<div class="section-head">スコア基準</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:0.75rem;color:#7fb3d3;line-height:1.9;">
        🟢 <b>80〜100点</b>　強買い<br>🔵 <b>65〜79点</b>　　買い<br>
        🟡 <b>50〜64点</b>　　様子見<br>🔴 <b>〜49点</b>　　　見送り
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        if st.button("🔄 データ更新", width='stretch', type="primary"):
            st.cache_data.clear()
            st.rerun()
        st.markdown('<div class="section-head" style="margin-top:1.5rem;">スコアを保存</div>', unsafe_allow_html=True)
        save_note = st.text_input("メモ", placeholder="今日の相場メモ...")
        if st.button("📝 本日スコアを保存", width='stretch'):
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

    tabs = st.tabs(["📋 スコアボード", "🔍 銘柄詳細・トレード日誌", "📈 スコア履歴", "📊 損益分析", "📡 AI予想"])

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
                # 平均スコア・最高スコアなどの大きなサマリー欄は削除。
                # 銘柄カード自体を左右2列にして、各銘柄のファンダ/チャートを横並び表示。
                for i in range(0, len(results_ok), 2):
                    cols = st.columns(2, gap="small")
                    with cols[0]:
                        render_card_with_delete(results_ok[i], watchlist)
                    if i + 1 < len(results_ok):
                        with cols[1]:
                            render_card_with_delete(results_ok[i + 1], watchlist)

            if results_ng:
                st.markdown('<div class="section-head" style="margin-top:.6rem">取得できなかった銘柄</div>', unsafe_allow_html=True)
                for r in results_ng:
                    render_card_with_delete(r, watchlist)

    with tabs[1]:
        if not watchlist:
            st.info("サイドバーから銘柄を追加してください。")
        else:
            selected = st.selectbox("銘柄を選択", list(watchlist.keys()),
                                    format_func=lambda t: f"{t}　{watchlist[t]}", key="detail_trade_select")
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
                st.dataframe(df_h, width='stretch')

    with tabs[3]:
        render_correlation_tab(watchlist)

    with tabs[4]:
        render_daily_ai_prediction_tab(watchlist)

if __name__ == "__main__":
    main()

