# -*- coding: utf-8 -*-
import datetime
import pandas as pd
from pymongo import MongoClient
import random

# --- 1. 기본 설정 및 DB 연결 ---
client = MongoClient('mongodb://localhost:27017/')

# 기획서에 명시된 5개의 전문 부서
DEPARTMENTS = [
    "Trend_Analyst",
    "Mean-Reversion_Specialist", 
    "Volatility_Scout",
    "Fundamental_Reader",
    "News-Sentiment_Reader"
]

# 각 부서별로 개별 데이터베이스 생성 및 초기화
dept_dbs = {}
for dept in DEPARTMENTS:
    dept_db = client[dept]
    # 이전 실행 데이터를 초기화하여 항상 새로운 상태에서 시작
    for collection_name in dept_db.list_collection_names():
        dept_db[collection_name].drop()
    dept_dbs[dept] = dept_db
    print(f"Database '{dept}' cleared and ready.")

TODAY_STR = datetime.date(2025, 6, 30).strftime("%Y-%m-%d")
LOOP = 12
EPISODE = 5

def get_utc_timestamp():
    """현재 UTC 타임스탬프를 ISO 형식으로 반환합니다."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

# --- 2. 더미 데이터 생성 함수 (스키마 기반) ---
# 이 함수들은 DB 스키마에 따라 Python 딕셔너리 또는 딕셔너리 리스트를 생성합니다.
# 각 부서의 특성을 반영하기 위해 일부 값을 동적으로 생성합니다.

def create_strategy_cases_checklist(dept):
    """부서(dept) 특성에 맞는 전략 케이스와 체크리스트를 생성합니다."""
    # 부서별로 다른 전략 케이스 예시
    cases = {
        "Trend_Analyst": {
            "id": "ma_cross_long",
            "name": "MA 골든크로스 추세추종",
            "condition": "MA5 > MA20",
            "confidence": 0.75
        },
        "Mean-Reversion_Specialist": {
            "id": "rsi_oversold_long",
            "name": "RSI 과매도 반전 매수",
            "condition": "RSI14 < 30",
            "confidence": 0.80
        },
        "Volatility_Scout": {
            "id": "bb_breakout_long",
            "name": "볼린저밴드 상단 돌파",
            "condition": "Price > BB_Upper",
            "confidence": 0.72
        },
        "Fundamental_Reader": {
            "id": "halving_narrative_long",
            "name": "반감기 내러티브 기반 매수",
            "condition": "days_to_halving < 180",
            "confidence": 0.85
        },
        "News-Sentiment_Reader": {
            "id": "positive_news_spike_long",
            "name": "긍정 뉴스 스파이크 매수",
            "condition": "sentiment_score > 0.8",
            "confidence": 0.68
        },
    }
    base_case = {
        "predicted_scenario": "상승 추세 전환 또는 지속 가능성",
        "recommended_response": "분할 매수 진입 후 2.0 RR 익절",
        "market": "futures",
        "position_side": "long",
        "preferred_action": "long"
    }
    specific_case = {**cases[dept], **base_case} # 딕셔너리 언패킹 사용

    return {
        "version": f"{TODAY_STR}_1",
        "updated_at": get_utc_timestamp(),
        "cases": [specific_case],
        "checklists": [
            {
                "id": "min_rr",
                "item": "리스크/보상 비율 >= 1.5",
                "metric": "rr",
                "threshold": 1.5,
                "critical": True
            }
        ]
    }

def create_memory_guideline(dept):
    """부서(dept) 특성에 맞는 기억 지침을 생성합니다."""
    # 부서별로 집중하는 메모리 규칙이 다를 수 있습니다.
    style_guide_map = {
        "Trend_Analyst": "추세의 강도와 지속성을 중심으로 기록한다.",
        "Mean-Reversion_Specialist": "과매수/과매도 지표의 반전 성공/실패 사례를 중심으로 기록한다.",
        "Volatility_Scout": "변동성 확대/축소 국면과 주요 이벤트의 상관관계를 중심으로 기록한다.",
        "Fundamental_Reader": "온체인 데이터 및 거시 경제 지표 변화를 중심으로 기록한다.",
        "News-Sentiment_Reader": "주요 뉴스와 커뮤니티 반응이 시장 가격에 미친 영향을 중심으로 기록한다.",
    }
    return {
        "version": f"{TODAY_STR}_1",
        "updated_at": get_utc_timestamp(),
        "short_memory_rule": "최근 5일간의 주요 시장 이벤트와 PnL을 중심으로 요약한다.",
        "mid_memory_rule": "최근 20일간의 주요 전략 성공/실패 사례를 분석한다.",
        "long_memory_rule": "지난 60일 이상의 거시 경제 지표 변화와 장기 추세를 기록한다.",
        "length_limit_tokens": 350,
        "style_guide": style_guide_map[dept]
    }

def create_market_snapshot():
    """시장 스냅샷 데이터를 생성합니다."""
    return {
        "date": TODAY_STR,
        "timestamp_utc": get_utc_timestamp(),
        "symbols": {
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
        },
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

def create_episode_trades_data():
    """에피소드 거래 데이터를 JSON(딕셔너리 리스트) 형식으로 생성합니다."""
    df = pd.DataFrame(
        {
            'ts': [pd.Timestamp.now()],
            'symbol': ['BTCUSDT'],
            'position_side': ['long'],
            'side': ['buy'],
            'price': [60500.0],
            'qty': [0.10],
            'notional_usd': [6050.0],
            'order_type': ['limit'],
            'fee': [0.03],
            'realized_pnl': [0.0],
            'cum_realized_pnl': [0.0],
            'slippage_pct': [0.0],
            'strategy_case_id': ['test_case'],
            'decision_ts': [pd.Timestamp.now()],
            'loop': LOOP,
            'episode': EPISODE
        }
    )
    return df.to_dict(orient='records')

def create_metrics():
    """성과 지표 데이터를 생성합니다."""
    return {
        "episode_id": f"{LOOP}_{EPISODE}",
        "start_ts": "2025-06-28T23:00:00Z",
        "end_ts": "2025-06-30T23:59:59Z",
        "total_realized_pnl": round(random.uniform(-50, 200), 2),
        "win_rate": round(random.uniform(0.4, 0.7), 2),
        "sharpe_ratio": round(random.uniform(0.5, 2.0), 2)
    }

def create_feedback():
    """피드백 데이터를 생성합니다."""
    return {
        "episode_id": f"{LOOP}_{EPISODE}",
        "generated_at": get_utc_timestamp(),
        "summary": {
            "overall_grade": random.choice(["A", "B+", "B-", "C"]),
            "key_stat": "PnL +102.5, Sharpe 1.43"
        },
        "problem_recognition": [],
        "hypotheses": [],
        "recommendations": {}
    }

def create_strategy_update_agent_config():
    """전략 업데이트 에이전트의 설정 데이터를 생성합니다."""
    return {
        "version": f"{TODAY_STR}_strategy_update_agent_1",
        "updated_at": get_utc_timestamp(),
        "cases": [
            {
                "id": "model_retrain_trigger",
                "name": "모델 재학습 트리거 조건",
                "condition": "SharpeRatio < 1.0 or PnL_Drop > 0.05",
                "confidence": 0.95,
                "predicted_scenario": "전략 성능 저하 감지",
                "recommended_response": "전략 모델 재학습 및 배포",
                "market": "n/a",
                "position_side": "n/a",
                "preferred_action": "retrain_strategy_model"
            }
        ],
        "checklists": [
            {
                "id": "data_freshness_check",
                "item": "최신 시장 데이터 확보 여부",
                "metric": "data_age_hours",
                "threshold": 24,
                "critical": True
            },
            {
                "id": "compute_resource_check",
                "item": "재학습 컴퓨팅 자원 확인",
                "metric": "cpu_utilization_pct",
                "threshold": 80,
                "critical": False
            }
        ]
    }

def create_memory_guideline_update_agent_config():
    """기억 지침 업데이트 에이전트의 설정 데이터를 생성합니다."""
    return {
        "version": f"{TODAY_STR}_memory_guideline_update_agent_1",
        "updated_at": get_utc_timestamp(),
        "short_memory_rule": "최근 7일간의 피드백 분석 결과를 바탕으로 단기 기억 지침을 조정한다.",
        "mid_memory_rule": "지난 30일간의 에피소드 요약에서 반복되는 문제점을 식별하여 중기 기억 지침을 개선한다.",
        "long_memory_rule": "분기별 전체 성능 지표를 검토하여 장기 기억 지침의 방향성을 설정한다.",
        "length_limit_tokens": 500, # 업데이트 에이전트의 규칙은 더 많은 토큰을 필요로 할 수 있음
        "style_guide": "기억 지침 업데이트 시, 명확하고 간결하며 측정 가능한 기준을 제시한다."
    }

# --- 3. 컬렉션별 데이터 삽입 함수 ---

def insert_central_memory(dept_db, strategy_doc, guideline_doc):
    """
    central_memory 폴더 구조 생성:
    - strategy_cases_checklist.json
    - memory_guideline.json
    """
    central_memory = dept_db['central_memory']
    
    # strategy_cases_checklist.json
    central_memory.update_one(
        {'_id': 'strategy_cases_checklist'},
        {'$set': {'_id': 'strategy_cases_checklist', **strategy_doc}},
        upsert=True
    )
    
    # memory_guideline.json  
    central_memory.update_one(
        {'_id': 'memory_guideline'},
        {'$set': {'_id': 'memory_guideline', **guideline_doc}},
        upsert=True
    )

def insert_daily_snapshots(dept_db, date, loop, episode, snapshot_docs):
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
    base_id = f"{date}_{loop}_{episode}"
    
    # market_snapshot.json
    daily_snapshots.update_one(
        {'_id': f"{base_id}_market_snapshot"},
        {'$set': {'_id': f"{base_id}_market_snapshot", 'date': date, 'loop': loop, 'episode': episode, **snapshot_docs['market']}},
        upsert=True
    )
    
    # portfolio_snapshot.json
    daily_snapshots.update_one(
        {'_id': f"{base_id}_portfolio_snapshot"},
        {'$set': {'_id': f"{base_id}_portfolio_snapshot", 'date': date, 'loop': loop, 'episode': episode, **snapshot_docs['portfolio']}},
        upsert=True
    )
    
    # trading_agent/decision.json
    daily_snapshots.update_one(
        {'_id': f"{base_id}_trading_agent_decision"},
        {'$set': {'_id': f"{base_id}_trading_agent_decision", 'date': date, 'loop': loop, 'episode': episode, **snapshot_docs['decision']}},
        upsert=True
    )
    
    # executions.arrow
    daily_snapshots.update_one(
        {'_id': f"{base_id}_executions"},
        {'$set': {'_id': f"{base_id}_executions", 'date': date, 'loop': loop, 'episode': episode, 'executions_data': snapshot_docs['executions']}},
        upsert=True
    )
    
    # memory_update_snapshot/trade_memory_short.json
    daily_snapshots.update_one(
        {'_id': f"{base_id}_memory_update_snapshot_trade_memory_short"},
        {'$set': {'_id': f"{base_id}_memory_update_snapshot_trade_memory_short", 'date': date, 'loop': loop, 'episode': episode, **snapshot_docs['trade_memory_short']}},
        upsert=True
    )
    
    # memory_update_snapshot/trade_memory_mid.json
    daily_snapshots.update_one(
        {'_id': f"{base_id}_memory_update_snapshot_trade_memory_mid"},
        {'$set': {'_id': f"{base_id}_memory_update_snapshot_trade_memory_mid", 'date': date, 'loop': loop, 'episode': episode, **snapshot_docs['trade_memory_mid']}},
        upsert=True
    )
    
    # memory_update_snapshot/trade_memory_long.json
    daily_snapshots.update_one(
        {'_id': f"{base_id}_memory_update_snapshot_trade_memory_long"},
        {'$set': {'_id': f"{base_id}_memory_update_snapshot_trade_memory_long", 'date': date, 'loop': loop, 'episode': episode, **snapshot_docs['trade_memory_long']}},
        upsert=True
    )

def insert_episodes_meta(dept_db, loop, episode, episode_docs):
    """
    episodes_meta 폴더 구조 생성:
    /{loop}/{episode}/
    ├─ episode_trades.arrow
    ├─ metrics.json
    ├─ feedback_agent.json
    ├─ strategy_update_agent.json
    └─ memory_guideline_update_agent.json
    """
    episodes_meta = dept_db['episodes_meta']
    
    # 각 에피소드 문서의 고유 ID 생성: {loop}_{episode}_{type}
    base_id = f"{loop}_{episode}"
    
    # episode_trades.arrow
    episodes_meta.update_one(
        {'_id': f"{base_id}_episode_trades"},
        {'$set': {'_id': f"{base_id}_episode_trades", 'loop': loop, 'episode': episode, 'trades_data': episode_docs['trades_data']}},
        upsert=True
    )
    
    # metrics.json
    episodes_meta.update_one(
        {'_id': f"{base_id}_metrics"},
        {'$set': {'_id': f"{base_id}_metrics", 'loop': loop, 'episode': episode, **episode_docs['metrics']}},
        upsert=True
    )
    
    # feedback_agent.json
    episodes_meta.update_one(
        {'_id': f"{base_id}_feedback_agent"},
        {'$set': {'_id': f"{base_id}_feedback_agent", 'loop': loop, 'episode': episode, **episode_docs['feedback']}},
        upsert=True
    )
    
    # strategy_update_agent.json
    episodes_meta.update_one(
        {'_id': f"{base_id}_strategy_update_agent"},
        {'$set': {'_id': f"{base_id}_strategy_update_agent", 'loop': loop, 'episode': episode, **episode_docs['strategy_update_agent_config']}},
        upsert=True
    )
    
    # memory_guideline_update_agent.json
    episodes_meta.update_one(
        {'_id': f"{base_id}_memory_guideline_update_agent"},
        {'$set': {'_id': f"{base_id}_memory_guideline_update_agent", 'loop': loop, 'episode': episode, **episode_docs['memory_guideline_update_agent_config']}},
        upsert=True
    )

# --- 4. 메인 실행 함수 ---

def seed_database_for_presentation():
    """
    5개 부서별로 개별 데이터베이스를 생성하고, 각 데이터베이스에 폴더 구조를 모방한 컬렉션을 구축합니다.
    """
    print("="*50)
    print("Starting database seeding for all 5 departments...")
    print("="*50)

    for dept in DEPARTMENTS:
        print(f"\nProcessing Department: [ {dept} ]")
        dept_db = dept_dbs[dept]

        # 1. central_memory 폴더 생성
        strategy_doc = create_strategy_cases_checklist(dept)
        guideline_doc = create_memory_guideline(dept)
        insert_central_memory(dept_db, strategy_doc, guideline_doc)
        print(f"   - Created central_memory/ (strategy_cases_checklist.json, memory_guideline.json)")

        # 2. daily_snapshots 폴더 생성
        snapshot_docs = {
            'market': create_market_snapshot(),
            'portfolio': create_portfolio_snapshot(),
            'decision': create_decision(dept, strategy_doc['cases'][0]['id']),
            'executions': create_executions_data(),
            'trade_memory_short': create_trade_memory('short'),
            'trade_memory_mid': create_trade_memory('mid'),
            'trade_memory_long': create_trade_memory('long'),
        }
        insert_daily_snapshots(dept_db, TODAY_STR, LOOP, EPISODE, snapshot_docs)
        print(f"   - Created daily_snapshots/{TODAY_STR}/{LOOP}/{EPISODE}/ (all snapshot files)")

        # 3. episodes_meta 폴더 생성
        episode_docs = {
            'trades_data': create_episode_trades_data(),
            'metrics': create_metrics(),
            'feedback': create_feedback(),
            'strategy_update_agent_config': create_strategy_update_agent_config(),
            'memory_guideline_update_agent_config': create_memory_guideline_update_agent_config(),
        }
        insert_episodes_meta(dept_db, LOOP, EPISODE, episode_docs)
        print(f"   - Created episodes_meta/{LOOP}/{EPISODE}/ (all episode files)")

    print("\n" + "="*50)
    print("Database seeding completed successfully for all departments.")
    print("="*50)
    client.close()

if __name__ == "__main__":
    seed_database_for_presentation()
