import os
import time
import datetime
import pandas as pd
from pymongo import MongoClient
import concurrent.futures

# 1. 외부 함수/상수 import
from common import calculate_all_indicators, prepare_market_data_documents_for_mongo
from config import get_utc_timestamp, DEPARTMENTS, clear_databases

# 2. 상수/설정
MONGO_URI = os.getenv('MONGO_URI', "mongodb://localhost:27017/")
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
        result = {}
        for group, vals in ti.items():
            if isinstance(vals, dict):
                for k, v in vals.items():
                    if isinstance(v, dict):
                        for subk, subv in v.items():
                            key = f"{subk.lower()}_{k.lower()}"
                            if subv is not None and not (isinstance(subv, float) and math.isnan(subv)):
                                result[key] = subv
                    else:
                        key = k.lower()
                        if key.startswith(group.lower() + "-"):
                            outkey = key
                        else:
                            outkey = f"{group.lower()}-{key}"
                        if v is not None and not (isinstance(v, float) and math.isnan(v)):
                            result[outkey] = v
            else:
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
        symbol_data.update(flatten_tech_indicators(technical_indicators))
        symbols[symbol] = symbol_data
    return symbols

def fetch_symbol_data_from_csv(symbol, start_dt, end_dt, lookback_days=250):
    csv_path = f"csv/{symbol.lower()}.csv"
    if not os.path.exists(csv_path):
        print(f"CSV 파일 없음: {csv_path}")
        return symbol, None
    # lookback_days 만큼 과거 데이터 포함
    extended_start_dt = start_dt - pd.Timedelta(days=lookback_days)
    df = pd.read_csv(csv_path, parse_dates=['open_time'])
    df = df.set_index('open_time')
    # 필요한 기간만 슬라이싱 (lookback 포함)
    df = df.loc[extended_start_dt:end_dt]
    return symbol, df

def insert_market_snapshots(
    dept_db, dept_name, symbol_list, start_date, end_date, loop_num, episode
):
    daily_snapshots = dept_db['daily_snapshots']
    dates = pd.date_range(start=start_date, end=end_date)
    symbol_dfs = {}

    start_dt = (
        start_date if isinstance(start_date, datetime.datetime)
        else datetime.datetime.combine(start_date, datetime.time.min)
    )
    end_dt = (
        end_date if isinstance(end_date, datetime.datetime)
        else datetime.datetime.combine(end_date, datetime.time.min)
    )
    # 병렬로 CSV에서 심볼별 데이터 가져오기 (lookback_days=250)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(fetch_symbol_data_from_csv, symbol, start_dt, end_dt, 250)
            for symbol in symbol_list
        ]
        for future in concurrent.futures.as_completed(futures):
            symbol, df = future.result()
            if df is not None and not df.empty:
                symbol_dfs[symbol] = df

    # 날짜별로 기술지표 계산 및 DB 저장
    for day in dates:
        date_str = day.strftime('%Y-%m-%d')
        market_data = {}
        for symbol, df in symbol_dfs.items():
            listing_date = SYMBOL_LISTING_DATE[symbol]
            if day.date() < listing_date.date():
                continue
            if df.empty or day not in df.index:
                continue
            # 해당 날짜까지 충분한 데이터로 기술지표 계산
            df_until_day = df.loc[:day]
            df_with_indicators = calculate_all_indicators(df_until_day)
            if day in df_with_indicators.index:
                daily_row = df_with_indicators.loc[[day]]
                market_data[symbol] = prepare_market_data_documents_for_mongo(
                    daily_row, symbol, "1d"
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
    print("🚀 CSV 기반으로 market_snapshot 생성 시작!")
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
