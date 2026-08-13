"""毎日のGemini AI TOP10を履歴保存し、1/5/20営業日後を自動で答え合わせする修正版。"""
from __future__ import annotations
import json, re
from datetime import datetime, timedelta
from pathlib import Path
import yfinance as yf

BASE=Path(__file__).resolve().parent
DATA=BASE/'data'
CURRENT=DATA/'ai_predictions.json'
HISTORY=DATA/'ai_prediction_history.json'

def load_json(path, default):
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding='utf-8-sig'))
    except Exception as e:
        print(f'[WARN] JSON読み込み失敗: {path} / {e}')
        return default

def save_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def looks_like_stock(d):
    if not isinstance(d,dict): return False
    return bool(str(d.get('ticker') or d.get('symbol') or d.get('code') or '').strip())

def normalize_item(item,rank):
    if not isinstance(item,dict): return None
    ticker=str(item.get('ticker') or item.get('symbol') or item.get('code') or item.get('銘柄コード') or '').strip()
    if ticker and ticker.endswith('.T') is False and ticker.isdigit(): ticker += '.T'
    if not ticker: return None
    return {
        'ticker':ticker,
        'name':item.get('name') or item.get('company_name') or item.get('銘柄名') or ticker,
        'rank':rank,
        'score':item.get('total_score',item.get('score',item.get('総合スコア',item.get('final_score')))),
        'reason':item.get('reason') or item.get('reasons') or item.get('ai_reason') or item.get('選定理由') or item.get('comment') or item.get('analysis') or '',
        'volume_rank':item.get('volume_rank',item.get('volumeRank',item.get('出来高順位'))),
        'volume_ratio':item.get('volume_ratio',item.get('volumeRatio',item.get('出来高倍率',item.get('volume_spike_ratio')))),
        'funda_score':item.get('funda_score',item.get('funda',item.get('ファンダ'))),
        'chart_score':item.get('chart_score',item.get('chart',item.get('チャート'))),
        'price':item.get('price',item.get('current_price',item.get('株価',item.get('close')))),
        'verdict':item.get('verdict',item.get('判定',item.get('recommendation',''))),
    }

def extract_rows(payload):
    # まず既知のキーを優先
    if isinstance(payload,dict):
        keys=('ai_top10','ai_predictions','predictions','top10','AI_TOP10','AI TOP10','aiTop10','gemini_top10','gemini_predictions')
        for key in keys:
            v=payload.get(key)
            if isinstance(v,list):
                rows=[normalize_item(x,i) for i,x in enumerate(v,1)]
                rows=[x for x in rows if x]
                if rows: return rows
        for container_key in ('data','result','result_data','gemini','ai'):
            v=payload.get(container_key)
            if isinstance(v,dict):
                rows=extract_rows(v)
                if rows: return rows
            if isinstance(v,list):
                rows=[normalize_item(x,i) for i,x in enumerate(v,1)]
                rows=[x for x in rows if x]
                if rows: return rows
        # payload自体が {ticker: {...}, ...} 型なら拾う
        vals=list(payload.values())
        stock_vals=[x for x in vals if looks_like_stock(x)]
        if stock_vals:
            rows=[normalize_item(x,i) for i,x in enumerate(stock_vals,1)]
            return [x for x in rows if x]
    elif isinstance(payload,list):
        rows=[normalize_item(x,i) for i,x in enumerate(payload,1)]
        rows=[x for x in rows if x]
        if rows: return rows
    return []

def update_outcomes(history):
    updated=0
    end=(datetime.now()+timedelta(days=35)).strftime('%Y-%m-%d')
    for row in history:
        if not isinstance(row,dict) or not row.get('ticker') or not row.get('date'): continue
        try: base=datetime.strptime(str(row['date'])[:10],'%Y-%m-%d')
        except ValueError: continue
        try:
            hist=yf.Ticker(row['ticker']).history(start=base.strftime('%Y-%m-%d'),end=end,auto_adjust=False)
        except Exception as e:
            row['last_error']=str(e); continue
        if hist is None or hist.empty or 'Close' not in hist: continue
        closes=hist['Close'].dropna()
        if closes.empty: continue
        try: base_price=float(row.get('price_at_prediction')) if row.get('price_at_prediction') is not None else float(closes.iloc[0])
        except Exception: base_price=float(closes.iloc[0])
        if not base_price: continue
        row['price_at_prediction']=round(base_price,2)
        for n,key in ((1,'1d'),(5,'5d'),(20,'20d')):
            if len(closes)>n:
                px=float(closes.iloc[n]); row[f'price_{key}']=round(px,2); row[f'outcome_{key}']=round((px/base_price-1)*100,2); updated+=1
        row['checked_at']=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return updated

def main():
    print(f'[INFO] 読み込み: {CURRENT}')
    if not CURRENT.exists():
        print('[ERROR] data/ai_predictions.json がありません。先に daily_volume_scanner.py を実行してください。'); return
    payload=load_json(CURRENT,{})
    print(f'[INFO] JSON形式: {type(payload).__name__}')
    if isinstance(payload,dict): print(f'[INFO] キー: {list(payload.keys())[:30]}')
    rows=extract_rows(payload)
    if not rows:
        print('[ERROR] AI TOP10を読み取れませんでした。')
        print('[HINT] data\\ai_predictions.json の先頭50行を確認してください。')
        return
    print(f'[OK] AI予想を{len(rows)}件検出しました。')
    date=str(payload.get('date') or payload.get('scan_date') or payload.get('updated_at',''))[:10] if isinstance(payload,dict) else ''
    if not re.match(r'^\d{4}-\d{2}-\d{2}$',date): date=datetime.now().strftime('%Y-%m-%d')
    history=load_json(HISTORY,[])
    if not isinstance(history,list): history=[]
    existing={(str(x.get('date')),str(x.get('ticker'))) for x in history if isinstance(x,dict)}
    added=0
    for row in rows:
        key=(date,row['ticker'])
        if key in existing: continue
        history.append({**row,'date':date,'price_at_prediction':row.get('price'),'price_1d':None,'price_5d':None,'price_20d':None,'outcome_1d':None,'outcome_5d':None,'outcome_20d':None,'checked_at':None}); added+=1
    updated=update_outcomes(history)
    history.sort(key=lambda x:(str(x.get('date','')),int(x.get('rank',999) or 999)),reverse=True)
    save_json(HISTORY,history)
    print(f'[OK] AI予想を{added}件追加 / 答え合わせを{updated}項目更新')
    print(f'[OK] 保存先: {HISTORY}')

if __name__=='__main__': main()
