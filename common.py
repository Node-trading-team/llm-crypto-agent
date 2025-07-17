import os
import time
import pandas as pd
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv
import numpy as np
import pandas_ta as ta
import requests
import openai

# 환경 변수 로드
load_dotenv()

# Binance API 키와 시크릿
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_SECRET_KEY')

# OpenAI API 키
openai_api_key = os.getenv('OPENAI_API_KEY')

# MongoDB 연결
mongo_uri = os.getenv('MONGO_URI', "mongodb://localhost:27017/")
client_mongo = MongoClient(mongo_uri)
db = client_mongo['crypto_data'] # 데이터베이스 이름

# 날짜별 통합 문서 컬렉션
# 반드시 date 필드에 unique index를 생성할 것(db.daily_market.create_index('date', unique=True))
daily_market_collection = db['daily_market']

# --- 함수들 ---
def interval_to_milliseconds(interval_str):
    seconds_per_unit = {
        "m": 60, "h": 60 * 60, "d": 24 * 60 * 60, "w": 7 * 24 * 60 * 60, "M": 30 * 24 * 60 * 60
    }
    unit = interval_str[-1]
    if unit in seconds_per_unit:
        try:
            ms = int(interval_str[:-1]) * seconds_per_unit[unit] * 1000
            return ms
        except ValueError:
            pass
    return None

# Binance API를 통해 캔들 데이터를 가져오는 함수
def fetch_historical_klines(binance_client, symbol, interval, start_str, end_str=None):
    print(f"{symbol} {interval} 캔들 데이터 가져오기 시작: {start_str} ~ {end_str if end_str else '현재'}")
    try:
        start_dt = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S') if ' ' in start_str else datetime.strptime(start_str, '%Y-%m-%d')
    except ValueError:
        print(f"오류: start_str '{start_str}' 형식이 올바르지 않습니다. 'YYYY-MM-DD' 또는 'YYYY-MM-DD HH:MM:SS' 형식을 사용하세요.")
        return pd.DataFrame()
    end_dt = datetime.utcnow()
    if end_str:
        try:
            end_dt = datetime.strptime(end_str, '%Y-%m-%d %H:%M:%S') if ' ' in end_str else datetime.strptime(end_str, '%Y-%m-%d')
            end_dt = end_dt + timedelta(days=1) # 해당 날짜까지 캔들 추출하기 위해 1일 더함
        except ValueError:
            print(f"오류: end_str '{end_str}' 형식이 올바르지 않습니다. 'YYYY-MM-DD' 또는 'YYYY-MM-DD HH:MM:SS' 형식을 사용하세요.")
            return pd.DataFrame()
    start_time_ms = int(start_dt.timestamp() * 1000)
    end_time_ms = int(end_dt.timestamp() * 1000)
    all_klines_data = []
    limit = 1000
    current_start_time = start_time_ms
    while current_start_time < end_time_ms:
        try:
            klines = binance_client.get_klines(
                symbol=symbol,
                interval=interval,
                startTime=current_start_time,
                endTime=end_time_ms,
                limit=limit
            )
            if not klines:
                break
            all_klines_data.extend(klines)
            current_start_time = klines[-1][0] + 1
            time.sleep(0.1)
        except Exception as e:
            print(f"API 호출 중 오류 발생: {e}. 다음 시도로 넘어갑니다.")
            time.sleep(5)
            current_start_time += limit * (interval_to_milliseconds(interval) if interval_to_milliseconds(interval) else 86400000)
    if not all_klines_data:
        print(f"{symbol} {interval} 데이터가 없습니다.")
        return pd.DataFrame()
    df = pd.DataFrame(all_klines_data, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time',
        'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
        'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
    numeric_cols = ['open', 'high', 'low', 'close', 'volume',
                    'quote_asset_volume', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col])
    df = df.set_index('open_time')
    df = df[['close_time', 'open', 'high', 'low', 'close', 'volume']].copy()
    print(f"{symbol} {interval} 캔들 데이터 {len(df)}개 로드 완료.")
    return df

def calculate_all_indicators(df):
    """길이에 맞는 지표만 계산하고, 예상치 못한 예외는 건너뛴다."""
    if df.empty:
        print("지표 계산용 데이터가 부족합니다.")
        return df

    df = df.dropna(subset=["high", "low", "close", "volume"]).copy()

    # ───────── MA / EMA ─────────
    for p in [5, 10, 20, 50, 60, 100, 200]:
        if len(df) >= p:
            # df.ta.sma(length=p, append=True)
            df.ta.ema(length=p, append=True)

    # ───────── MACD (길이 + try/except) ─────────
    for fast, slow, sig in [(12, 26, 9), (24, 52, 18), (19, 39, 9)]:
        need = slow + sig                    # 안전 최소 길이
        if len(df) >= need:
            try:
                df.ta.macd(fast=fast, slow=slow, signal=sig, append=True)
            except Exception as e:
                print(f"[WARN] MACD({fast},{slow},{sig}) 계산 실패 → 건너뜀: {e}")

    # ───────── RSI ─────────
    for L in [7, 14, 21]:
        if len(df) >= L:
            df.ta.rsi(length=L, append=True)

    # ───────── Stochastic ─────────
    for k, d in [(5, 3), (9, 3), (14, 3)]:
        need = k + d + 1
        if len(df) >= need:
            try:
                df.ta.stoch(k=k, d=d, append=True)
            except Exception as e:
                print(f"[WARN] Stoch(k={k},d={d}) 계산 실패: {e}")

    # ───────── Bollinger Bands ─────────
    for L in [10, 20, 50]:
        if len(df) >= L:
            df.ta.bbands(length=L, std=2, append=True)

    # ───────── ATR ─────────
    for L in [7, 14, 28]:
        if len(df) >= L:
            df.ta.atr(length=L, append=True)

    # ───────── OBV ─────────
    if len(df) >= 2:
        df.ta.obv(append=True)
        for L in [10, 20, 50]:
            if len(df) >= L:
                df.ta.sma(close=df["OBV"], length=L, append=True, prefix="OBV_")

    # ───────── Ichimoku ─────────
    if len(df) >= 52:
        df.ta.ichimoku(tenkan=9, kijun=26, senkou_b=52, append=True)

    # ───────── Supertrend ─────────
    for L in [10, 14, 21]:
        if len(df) >= L:
            df.ta.supertrend(length=L, multiplier=3, append=True)

    # ───────── Fibonacci ─────────
    recent = df.tail(30)
    if len(recent) > 1:
        hi, lo = recent["high"].max(), recent["low"].min()
        span = hi - lo
        rising = recent["close"].iloc[-1] > recent["close"].iloc[0]
        for r in [0, .236, .382, .5, .618, .786, 1, 1.272, 1.618]:
            df[f"FIB_{r}"] = (hi - span * r) if rising else (lo + span * r)

    return df

# MongoDB에 저장할 시장 데이터 계층 구조 준비
def prepare_market_data_documents_for_mongo(df, symbol, interval):
    doc = []
    for idx, row in df.iterrows():
        chart_data = {
            "open": float(row['open']),
            "high": float(row['high']),
            "low": float(row['low']),
            "close": float(row['close']),
            "volume": float(row['volume'])
        }
        ti = {}
        for col, val in row.items():
            if pd.isna(val):
                continue
            if col in ['close_time', 'open', 'high', 'low', 'close', 'volume']:
                continue
            
            if col.startswith("EMA"):
                period = col.split("_",1)[1]
                ti.setdefault("EMA", {})[f"EMA-{period}"] = float(val)

            elif col.startswith("SMA"):
                period = col.split("_",1)[1]
                ti.setdefault("MA", {})[f"MA-{period}"] = float(val)

            elif col.startswith("MACD") or col.startswith("MACDh") or col.startswith("MACDs"):
                kind, grp = col.split("_",1)
                grp = grp.replace("_", "-")
                key = f"{kind}-{grp}"
                ti.setdefault("MACD", {})[key] = float(val)

            elif col.startswith("RSI"):
                period = col.split("_",1)[1]
                ti.setdefault("RSI", {})[f"RSI-{period}"] = float(val)

            elif col.startswith("STOCHk") or col.startswith("STOCHd"):
                kind, grp = col.split("_",1)
                grp = grp.replace("_", "-")
                bucket = ti.setdefault("STOCH", {}).setdefault(grp, {})
                if kind == "STOCHk":
                    bucket["STOCHk"] = float(val)
                else:
                    bucket["STOCHd"] = float(val)

            elif col.startswith(("BBL", "BBM", "BBU", "BBB", "BBP")):
                prefix, grp = col.split("_",1)
                grp = grp.replace("_", "-")
                bb = ti.setdefault("BBANDS", {}).setdefault(grp, {})
                bb[prefix] = float(val)

            elif col.startswith("ATR"):
                period = col.split("_",1)[1]
                ti.setdefault("ATR", {})[f"ATR-{period}"] = float(val)

            elif col == "OBV":
                ti.setdefault("OBV", {})["OBV"] = float(val)
            elif col.startswith("OBV_SMA_") or col.startswith("OBV_MA_") or col.startswith("OBV_"):
                parts = col.split("_")[-1]
                ti.setdefault("OBV", {})[f"OBV-MA-{parts}"] = float(val)

            elif col.startswith("ISA"):
                col = col.replace("_", "-")
                ti.setdefault("ICHIMOKU", {})[col] = float(val)
            elif col.startswith("ISB"):
                col = col.replace("_", "-")
                ti.setdefault("ICHIMOKU", {})[col] = float(val)
            elif col.startswith("ITS"):
                col = col.replace("_", "-")
                ti.setdefault("ICHIMOKU", {})[col] = float(val)
            elif col.startswith("IKS"):
                col = col.replace("_", "-")
                ti.setdefault("ICHIMOKU", {})[col] = float(val)
            elif col.startswith("ICS"):
                col = col.replace("_", "-")
                ti.setdefault("ICHIMOKU", {})[col] = float(val)

            elif col.startswith("SUPERT"):
                kind = col.split("_")[0]
                length = col.split("_")[1]
                multiplier = col.split("_")[2]
                bucket = ti.setdefault("SUPERTREND", {}).setdefault(f"{length}-{multiplier}", {})
                bucket[kind] = float(val)
            elif col.startswith("FIB"):
                ratio = col.split("_",1)[1]
                ti.setdefault("FIB", {})[f"FIB-level-{ratio}"] = float(val)
        # docs.append(doc)
    return {
            # "symbol": symbol,
            "chart_data": chart_data,
            "technical_indicators": ti
        }

def upsert_daily_market_document(date, market_data=None, community_summary=None, macro_summary=None):
    update_fields = {}
    if market_data is not None:
        update_fields["market_data"] = market_data
    if community_summary is not None:
        update_fields["community_summary"] = community_summary
    if macro_summary is not None:
        update_fields["macro_summary"] = macro_summary
    if not update_fields:
        return
    daily_market_collection.update_one(
        {"date": date},
        {"$set": update_fields},
        upsert=True
    )

# GPT-4o를 활용한 커뮤니티 요약 생성
def call_gpt_community_summary(date_str):
    if not openai_api_key:
        print("OPENAI_API_KEY가 설정되지 않았습니다. GPT API 호출을 건너뜁니다.")
        return "API 키 없음"
    prompt = f"{date_str}에 작성된 암호화폐 관련 레딧, 트위터, 커뮤니티 게시글과 반응을 요약해줘. 주요 이슈, 투자심리, 논쟁거리, 시장 분위기를 한글로 10문장 이내로 정리해줘."
    try:
        client = openai.OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1024
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"GPT 커뮤니티 요약 오류: {e}")
        return f"GPT 커뮤니티 요약 오류: {e}"

# GPT-4o를 활용한 거시경제 뉴스 요약 생성
def call_gpt_macro_summary(date_str):
    if not openai_api_key:
        print("OPENAI_API_KEY가 설정되지 않았습니다. GPT API 호출을 건너뜁니다.")
        return "API 키 없음"
    prompt = f"{date_str}에 발표된 암호화폐 및 거시경제 관련 주요 뉴스, 정책, 경제지표, 글로벌 이슈를 한글로 10문장 이내로 요약해줘. 암호화폐 시장에 영향을 줄 만한 거시경제 이벤트를 중심으로 정리해줘."
    try:
        client = openai.OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1024
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"GPT 거시경제 요약 오류: {e}")
        return f"GPT 거시경제 요약 오류: {e}"