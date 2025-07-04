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
        
        # 기본 가격/거래량 정보
        symbol_data = {
            "p": chart_data.get('close', 0.0),  # 현재가 (종가)
            "v": chart_data.get('volume', 0.0)  # 거래량
        }
        
        # 기술적 지표 추가
        # RSI 14
        rsi_data = technical_indicators.get('RSI', {})
        if 'RSI-14' in rsi_data:
            symbol_data['rsi14'] = rsi_data['RSI-14']
        
        # MACD (기본 12-26-9)
        macd_data = technical_indicators.get('MACD', {})
        if 'MACD-12-26-9' in macd_data:
            symbol_data['macd'] = macd_data['MACD-12-26-9']
        elif 'MACDh-12-26-9' in macd_data:  # 히스토그램이 있으면 사용
            symbol_data['macd'] = macd_data['MACDh-12-26-9']
        
        # 추가 기술적 지표들 (선택적)
        # MA 20
        ma_data = technical_indicators.get('MA', {})
        if 'MA-20' in ma_data:
            symbol_data['ma20'] = ma_data['MA-20']
            
        # EMA 20  
        ema_data = technical_indicators.get('EMA', {})
        if 'EMA-20' in ema_data:
            symbol_data['ema20'] = ema_data['EMA-20']
            
        # 볼린저 밴드 (20)
        bb_data = technical_indicators.get('BBANDS', {})
        if '20' in bb_data:
            bb_20 = bb_data['20']
            if 'BBU' in bb_20:
                symbol_data['bb_upper'] = bb_20['BBU']
            if 'BBL' in bb_20:
                symbol_data['bb_lower'] = bb_20['BBL']
            if 'BBM' in bb_20:
                symbol_data['bb_middle'] = bb_20['BBM']
        
        # ATR 14
        atr_data = technical_indicators.get('ATR', {})
        if 'ATR-14' in atr_data:
            symbol_data['atr14'] = atr_data['ATR-14']
            
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