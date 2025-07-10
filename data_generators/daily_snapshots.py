import datetime
import pandas as pd
import random
from config import get_utc_timestamp, TODAY_STR, LOOP, EPISODE

def convert_market_data_to_symbols_format(market_data_dict):
    """
    daily_market_pipeline.py에서 생성하는 market_data 딕셔너리를 
    market_snapshot.json의 symbols 형태로 변환합니다.
    
    Args:
        market_data_dict: {symbol: {chart_data, technical_indicators}} 형태
    
    Returns:
        symbols 딕셔너리 (market_snapshot.json 형태)
    """
    symbols = {}

    for symbol, data in market_data_dict.items():
        chart_data = data.get('chart_data', {})
        technical_indicators = data.get('technical_indicators', {})
        
        # 기본 가격/거래량
        symbol_data = {
            "p": chart_data.get('close', 0.0),
            "v": chart_data.get('volume', 0.0)
        }
        
        # ========== 주요 지표들 ========== #
        # RSI
        for period, val in technical_indicators.get('RSI', {}).items():
            k = f"rsi{period.split('-')[-1]}"
            symbol_data[k] = val
        # MACD (히스토그램 포함)
        for macd_name, macd_val in technical_indicators.get('MACD', {}).items():
            symbol_data[macd_name.lower()] = macd_val
        # MA, EMA (전부 다 담기)
        for k, v in technical_indicators.get('MA', {}).items():
            symbol_data[k.lower()] = v
        for k, v in technical_indicators.get('EMA', {}).items():
            symbol_data[k.lower()] = v
        # 볼린저밴드
        for bb_period, bb_val in technical_indicators.get('BBANDS', {}).items():
            for bb_type, bb in bb_val.items():
                symbol_data[f'bb{bb_type.lower()}_{bb_period}'] = bb
        # ATR
        for k, v in technical_indicators.get('ATR', {}).items():
            symbol_data[k.lower()] = v
        # Ichimoku
        for k, v in technical_indicators.get('ICHIMOKU', {}).items():
            symbol_data[k.lower()] = v
        # Supertrend
        for period, st in technical_indicators.get('SUPERTREND', {}).items():
            for typ, val in st.items():
                symbol_data[f'supert_{typ.lower()}_{period}'] = val
        # 피보나치
        for k, v in technical_indicators.get('FIB', {}).items():
            symbol_data[k.lower()] = v
        # OBV
        for k, v in technical_indicators.get('OBV', {}).items():
            symbol_data[k.lower()] = v
        # STOCH
        for period, st in technical_indicators.get('STOCH', {}).items():
            for typ, val in st.items():
                symbol_data[f"stoch{typ.lower()}_{period}"] = val

        # ========== 기타 지표 추가시 위와 같은 패턴 ========== #

        symbols[symbol] = symbol_data

    return symbols

def create_market_snapshot(market_data_dict=None):
    """
    시장 스냅샷 데이터를 생성합니다.
    market_data_dict가 제공되면 이를 사용하고, 없으면 더미 데이터를 생성합니다.
    """
    if market_data_dict:
        # daily_market_pipeline.py에서 생성한 실제 데이터 사용
        symbols = convert_market_data_to_symbols_format(market_data_dict)
    else:
        # 더미 데이터 생성
        symbols = {
            "BTCUSDT": {
                "p": 61234.5 + random.uniform(-100, 100),
                "v": 34750.2,
                "rsi14": 62.1,
                "macd": -45.3
            },
            "ETHUSDT": {
                "p": 3412.7,
                "v": 18210.1,
                "rsi14": 58.8,
                "macd": 3.4
            }
        }
    
    return {
        "date": TODAY_STR,
        "timestamp_utc": get_utc_timestamp(),
        "symbols": symbols,
        "research_reports": [
            "Glassnode Report (Summary): BTC futures open interest reaches 6-month high."
        ]
    }

def create_portfolio_snapshot():
    """포트폴리오 스냅샷 데이터를 생성합니다."""
    return {
        "timestamp_utc": get_utc_timestamp(),
        "cash": 20500.0,
        "positions": {
            "BTCUSDT": {
                "side": "long",
                "qty": 0.25,
                "avg_entry": 61120.0,
                "leverage": 3
            }
        },
        "pending_orders": []
    }

def create_decision(dept, strategy_id):
    """의사결정 데이터를 생성합니다."""
    return {
        "ts": get_utc_timestamp(),
        "symbol": "BTCUSDT",
        "market": "futures",
        "position_side": "long",
        "side": "buy",
        "qty": round(random.uniform(0.05, 0.2), 2),
        "price": 60500.0,
        "leverage": 3,
        "order_type": "limit",
        "strategy_case_id": strategy_id,
        "decision_reason": f"Decision by {dept}",
        "comment": "<ASSUMPTION: Market rebound>",
        "risk_reward": 2.4,
        "checklist_pass_rate": 0.83,
        "expected_drawdown_pct": 1.2
    }

def create_executions_data():
    """체결 데이터를 JSON(딕셔너리 리스트) 형식으로 생성합니다."""
    data = [
        {
            'ts': datetime.datetime(2025, 6, 30, 9, 18, 2, 317000),
            'order_id': 'o-abc123',
            'exec_id': 'e-x1',
            'symbol': 'BTCUSDT',
            'position_side': 'long',
            'side': 'buy',
            'price': 60500.0,
            'qty': 0.10,
            'fee': 0.030,
            'realized_pnl': 0.0,
            'status': 'filled'
        }
    ]
    return data

def create_trade_memory(period):
    """거래 기억 데이터를 생성합니다."""
    return {
        "updated_at": get_utc_timestamp(),
        "period": period,
        "lookback_days": {"short": 3, "mid": 20, "long": 90}[period],
        "market_summary": "Market is in a consolidation phase.",
        "strategy_notes": [],
        "risk_events": "None",
        "keywords": []
    }

def insert_daily_snapshots(dept_db, dept_name, use_real_market_data=False):
    """
    daily_snapshots 폴더 구조 생성:
    /{YYYY-MM-DD}/{loop}/{episode}/
    ├─ market_snapshot.json
    ├─ portfolio_snapshot.json  
    ├─ trading_agent/
    │  └─ decision.json
    ├─ executions.arrow
    └─ memory_update_snapshot/
       ├─ trade_memory_short.json
       ├─ trade_memory_mid.json
       └─ trade_memory_long.json
    """
    daily_snapshots = dept_db['daily_snapshots']
    
    # 각 스냅샷 문서의 고유 ID 생성: {date}_{loop}_{episode}_{type}
    base_id = f"{TODAY_STR}_{LOOP}_{EPISODE}"
    
    # 더미 데이터 생성
    snapshot_docs = {
        'market': create_market_snapshot(None if not use_real_market_data else None),  # 항상 더미 데이터 사용
        'portfolio': create_portfolio_snapshot(),
        'decision': create_decision(dept_name, f"strategy_{dept_name.lower()}_001"),
        'executions': create_executions_data(),
        'trade_memory_short': create_trade_memory('short'),
        'trade_memory_mid': create_trade_memory('mid'),
        'trade_memory_long': create_trade_memory('long'),
    }
    
    # market_snapshot.json
    daily_snapshots.update_one(
        {'_id': f"{base_id}_market_snapshot"},
        {'$set': {'_id': f"{base_id}_market_snapshot", 'date': TODAY_STR, 'loop': LOOP, 'episode': EPISODE, **snapshot_docs['market']}},
        upsert=True
    )
    
    # portfolio_snapshot.json
    daily_snapshots.update_one(
        {'_id': f"{base_id}_portfolio_snapshot"},
        {'$set': {'_id': f"{base_id}_portfolio_snapshot", 'date': TODAY_STR, 'loop': LOOP, 'episode': EPISODE, **snapshot_docs['portfolio']}},
        upsert=True
    )
    
    # trading_agent/decision.json
    daily_snapshots.update_one(
        {'_id': f"{base_id}_trading_agent_decision"},
        {'$set': {'_id': f"{base_id}_trading_agent_decision", 'date': TODAY_STR, 'loop': LOOP, 'episode': EPISODE, **snapshot_docs['decision']}},
        upsert=True
    )
    
    # executions.arrow
    daily_snapshots.update_one(
        {'_id': f"{base_id}_executions"},
        {'$set': {'_id': f"{base_id}_executions", 'date': TODAY_STR, 'loop': LOOP, 'episode': EPISODE, 'executions_data': snapshot_docs['executions']}},
        upsert=True
    )
    
    # memory_update_snapshot/trade_memory_short.json
    daily_snapshots.update_one(
        {'_id': f"{base_id}_memory_update_snapshot_trade_memory_short"},
        {'$set': {'_id': f"{base_id}_memory_update_snapshot_trade_memory_short", 'date': TODAY_STR, 'loop': LOOP, 'episode': EPISODE, **snapshot_docs['trade_memory_short']}},
        upsert=True
    )
    
    # memory_update_snapshot/trade_memory_mid.json
    daily_snapshots.update_one(
        {'_id': f"{base_id}_memory_update_snapshot_trade_memory_mid"},
        {'$set': {'_id': f"{base_id}_memory_update_snapshot_trade_memory_mid", 'date': TODAY_STR, 'loop': LOOP, 'episode': EPISODE, **snapshot_docs['trade_memory_mid']}},
        upsert=True
    )
    
    # memory_update_snapshot/trade_memory_long.json
    daily_snapshots.update_one(
        {'_id': f"{base_id}_memory_update_snapshot_trade_memory_long"},
        {'$set': {'_id': f"{base_id}_memory_update_snapshot_trade_memory_long", 'date': TODAY_STR, 'loop': LOOP, 'episode': EPISODE, **snapshot_docs['trade_memory_long']}},
        upsert=True
    ) 