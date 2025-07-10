import os
import time
import datetime
import pandas as pd
from pymongo import MongoClient

# 1. 외부 함수/상수 import
from common import fetch_historical_klines, calculate_all_indicators, prepare_market_data_documents_for_mongo
# from data_generators.daily_snapshots import convert_market_data_to_symbols_format
from config import get_utc_timestamp, DEPARTMENTS, clear_databases

from binance.client import Client

# 2. 상수/설정
MONGO_URI = os.getenv('MONGO_URI', "mongodb://localhost:27017/")
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_SECRET_KEY')
SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT"]
LOOPS = 10
START_MONTH = datetime.date(2017, 1, 1)
END_MONTH = datetime.date(2023, 6, 30)
MONTH_LIST = pd.date_range(start=START_MONTH, end=END_MONTH, freq='MS') # 월초

# **추가: 심볼별 상장일**
SYMBOL_LISTING_DATE = {
    "BTCUSDT": datetime.datetime(2017, 8, 17),
    "ETHUSDT": datetime.datetime(2017, 8, 17),
    "XRPUSDT": datetime.datetime(2017, 8, 17),
    "BNBUSDT": datetime.datetime(2019, 11, 15),
    "ADAUSDT": datetime.datetime(2018, 3, 13),
    "DOGEUSDT": datetime.datetime(2019, 7, 5),
    "SOLUSDT": datetime.datetime(2020, 8, 11),
}

def convert_market_data_to_symbols_format(market_data_dict):
    import math

    def flatten_tech_indicators(ti):
        """
        ti(dict): prepare_market_data_documents_for_mongo에서 반환된 'technical_indicators'
        ex: {'RSI': {'RSI-14': 52.3}, 'MA': {'MA-20': 100.1}, ...}
        -> {'rsi-14': 52.3, 'ma-20': 100.1, ...}
        """
        result = {}
        for group, vals in ti.items():
            if isinstance(vals, dict):
                for k, v in vals.items():
                    if isinstance(v, dict):
                        # 3-depth (ex: BBANDS, SUPERTREND 등)
                        for subk, subv in v.items():
                            key = f"{subk.lower()}_{k.lower()}"
                            if subv is not None and not (isinstance(subv, float) and math.isnan(subv)):
                                result[key] = subv
                    else:
                        key = k.lower()
                        if key.startswith(group.lower() + "-"):
                            # 'rsi-14'처럼 이미 group명이 있으면 그대로
                            outkey = key
                        else:
                            outkey = f"{group.lower()}-{key}"
                        if v is not None and not (isinstance(v, float) and math.isnan(v)):
                            result[outkey] = v
            else:
                # 2-depth 아닌 경우 (ex: FIB처럼 바로 key:value로 들어올 수 있음)
                if vals is not None and not (isinstance(vals, float) and math.isnan(vals)):
                    result[group.lower()] = vals
        return result

    symbols = {}
    for symbol, data in market_data_dict.items():
        chart_data = data.get('chart_data', {})
        technical_indicators = data.get('technical_indicators', {})
        symbol_data = {
            "p": chart_data.get('close', 0.0),
            "v": chart_data.get('volume', 0.0)
        }
        # 기술지표 flatten해서 추가
        symbol_data.update(flatten_tech_indicators(technical_indicators))
        symbols[symbol] = symbol_data
    return symbols

# 3. market_snapshot만 적재하는 함수만 정의(나머지는 import 사용)
def insert_market_snapshots(
    dept_db, dept_name, symbol_list, start_date, end_date, loop_num, episode
):
    client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
    daily_snapshots = dept_db['daily_snapshots']
    dates = pd.date_range(start=start_date, end=end_date)
    for day in dates:
        date_str = day.strftime('%Y-%m-%d')
        market_data = {}
        for symbol in symbol_list:
            listing_date = SYMBOL_LISTING_DATE[symbol]
            if day.date() < listing_date.date():
                # 상장 이전이면 skip
                continue

            lookback_start_date = max(listing_date, day - pd.Timedelta(days=250))
            lookback_start = lookback_start_date.strftime('%Y-%m-%d')
            df = fetch_historical_klines(
                client, symbol, Client.KLINE_INTERVAL_1DAY, lookback_start, date_str
            )
            if df.empty or day not in df.index:
                continue

            df_with_indicators = calculate_all_indicators(df)
            daily_row = df_with_indicators[df_with_indicators.index.date == day.date()]
            if daily_row.empty:
                continue

            market_data[symbol] = prepare_market_data_documents_for_mongo(
                daily_row, symbol, Client.KLINE_INTERVAL_1DAY
            )

        symbols = convert_market_data_to_symbols_format(market_data)

        if not symbols:
            print(f"⏩ {date_str} SKIP (no symbols)")
            continue

        market_snapshot = {
            "date": date_str,
            "loop": loop_num,
            "episode": episode,
            "timestamp_utc": get_utc_timestamp(),
            "symbols": symbols,
            "research_reports": [
                "Glassnode Report (Summary): BTC futures open interest reaches 6-month high."
            ]
        }
        base_id = f"{date_str}_{loop_num}_{episode}_market_snapshot"
        daily_snapshots.update_one(
            {"_id": base_id},
            {"$set": {"_id": base_id, **market_snapshot}},
            upsert=True
        )

def main():
    print("🗑️  기존 데이터베이스를 정리합니다...")
    clear_databases()
    print("🚀 실전 Binance 데이터로 market_snapshot 생성 시작!")
    mongo_client = MongoClient(MONGO_URI)
    for dept in DEPARTMENTS:
        db = mongo_client[dept]
        print(f"\n📂 [{dept}] 부서 market_snapshot 저장 시작...")
        for loop in range(1, LOOPS+1):
            print(f"  🔄 loop {loop}/10")
            for episode_num, month_start in enumerate(MONTH_LIST, 1):
                month_end = (month_start + pd.offsets.MonthEnd(0)).date()
                month_start = month_start.date()

                episode_label = f"{month_start:%Y.%m}"
                print(f"    🗓️  episode={episode_label} ({month_start} ~ {month_end})")
                insert_market_snapshots(
                    db, dept, SYMBOLS, month_start, month_end, loop, episode_label
                )
    print("\n✨ 모든 부서/loop/월 market_snapshot 저장 완료!")

if __name__ == "__main__":
    main()
