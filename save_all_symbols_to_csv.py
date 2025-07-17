import os
import datetime
import pandas as pd
from binance.client import Client

BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_SECRET_KEY')

SYMBOL_LISTING_DATE = {
    "BTCUSDT": datetime.datetime(2017, 8, 17),
    "ETHUSDT": datetime.datetime(2017, 8, 17),
    "XRPUSDT": datetime.datetime(2017, 8, 17),
    "BNBUSDT": datetime.datetime(2019, 11, 15),
    "ADAUSDT": datetime.datetime(2018, 3, 13),
    "DOGEUSDT": datetime.datetime(2019, 7, 5),
    "SOLUSDT": datetime.datetime(2020, 8, 11),
}

SYMBOLS = list(SYMBOL_LISTING_DATE.keys())
TODAY = datetime.datetime.now().date()

def fetch_historical_klines(client, symbol, interval, start_str, end_str=None):
    # Binance API에서 일봉 데이터 가져오기
    klines = []
    start_dt = pd.to_datetime(start_str)
    end_dt = pd.to_datetime(end_str) if end_str else pd.Timestamp(TODAY)
    limit = 1000
    current_start = start_dt
    while current_start < end_dt:
        current_end = min(current_start + pd.Timedelta(days=limit), end_dt)
        klines_batch = client.get_klines(
            symbol=symbol,
            interval=interval,
            startTime=int(current_start.timestamp() * 1000),
            endTime=int(current_end.timestamp() * 1000)
        )
        if not klines_batch:
            break
        klines.extend(klines_batch)
        current_start = pd.to_datetime(klines_batch[-1][0], unit='ms') + pd.Timedelta(days=1)
    if not klines:
        return pd.DataFrame()
    df = pd.DataFrame(klines, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time',
        'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
        'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df.set_index('open_time', inplace=True)
    return df

def main():
    client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
    os.makedirs("csv", exist_ok=True)
    for symbol in SYMBOLS:
        start_date = SYMBOL_LISTING_DATE[symbol].date()
        print(f"⏳ {symbol}: {start_date} ~ {TODAY} 데이터 저장 중...")
        df = fetch_historical_klines(
            client, symbol, Client.KLINE_INTERVAL_1DAY,
            start_date.strftime('%Y-%m-%d'),
            TODAY.strftime('%Y-%m-%d')
        )
        if df.empty:
            print(f"⚠️ {symbol} 데이터 없음")
            continue
        csv_path = f"csv/{symbol.lower()}.csv"
        df.to_csv(csv_path)
        print(f"✅ {symbol} 저장 완료: {csv_path}")

if __name__ == "__main__":
    main()