import pandas as pd
import random
from config import get_utc_timestamp, TODAY_STR, LOOP, EPISODE

def create_episode_trades_data():
    """체결 데이터 (스키마에 맞는 컬럼명 사용)"""
    df = pd.DataFrame(
        {
            'ts': [pd.Timestamp.now().isoformat()],  # ISO 8601
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
            'strategy_case_id': ['rsi_macd_long'],
            'decision_ts': [pd.Timestamp.now().isoformat()],
            'loop': [LOOP],
            'episode': [EPISODE]
        }
    )
    return df.to_dict(orient='records')

def create_metrics():
    """metrics.json (스키마 준수)"""
    case_stats = {
        "rsi_macd_long": {"trades": 5, "win": 4, "pnl": 72.0},
        "breakout_short": {"trades": 3, "win": 1, "pnl": -25.0}
    }
    return {
        "episode_id": f"{LOOP}_{EPISODE}",
        "start_ts": "2025-06-28T23:00:00Z",
        "end_ts": "2025-06-29T23:59:59Z",
        "total_realized_pnl": round(random.uniform(-50, 200), 2),
        "avg_trade_rr": round(random.uniform(1.0, 2.5), 2),
        "win_rate": round(random.uniform(0.4, 0.7), 2),
        "max_drawdown_pct": round(random.uniform(-5, 0), 2),
        "sharpe_ratio": round(random.uniform(0.5, 2.0), 2),
        "avg_slippage_pct": round(random.uniform(-0.2, 0.2), 3),
        "checklist_pass_rate": round(random.uniform(0.7, 1.0), 2),
        "var_95_usd": round(random.uniform(-300, 0), 1),
        "case_stats": case_stats
    }

def create_problem_recognition_agent():
    """problem_recognition_agent.json"""
    return {
        "episode_id": f"{LOOP}_{EPISODE}",
        "generated_at": get_utc_timestamp(),
        "problem_recognition": [
            {
                "id": "pr1",
                "description": "평균 진입가가 지나치게 높음",
                "evidence": ["trade_001", "rsi_macd_long"]
            },
            {
                "id": "pr2",
                "description": "과도한 슬리피지 발생",
                "evidence": ["trade_002"]
            }
        ]
    }

def create_hypothesis_agent():
    """hypothesis_agent.json"""
    return {
        "episode_id": f"{LOOP}_{EPISODE}",
        "generated_at": get_utc_timestamp(),
        "hypotheses": [
            {
                "ref": "pr1",
                "hypothesis": "진입 타이밍 지연으로 인한 가격 상승"
            },
            {
                "ref": "pr2",
                "hypothesis": "시장가 주문 사용 증가 때문"
            }
        ]
    }

def create_strategy_cases():
    """strategy_cases.json (스키마 준수)"""
    return {
        "version": f"{TODAY_STR}_1",
        "updated_at": get_utc_timestamp(),
        "cases": [
            {
                "id": "rsi_macd_long",
                "name": "RSI<30 & MACD- 진입",
                "condition": "RSI14 < 30 AND MACD < 0",
                "predicted_scenario": "과매도 구간에서 매수세 반등 가능성",
                "recommended_response": "저가 매수 후 RR 2.0 지점 부분 익절",
                "market": "futures",
                "position_side": "long",
                "preferred_action": "long",
                "confidence": 0.74
            },
            {
                "id": "breakout_short",
                "name": "BB 하단 돌파 숏",
                "condition": "Price < BB_Lower",
                "predicted_scenario": "지지선 이탈 후 추가 하락 가능성",
                "recommended_response": "지지선 이탈시 부분 진입, RR 1.7 지점 익절",
                "market": "futures",
                "position_side": "short",
                "preferred_action": "short",
                "confidence": 0.71
            }
        ]
    }

def create_strategy_checklists():
    """strategy_checklists.json (스키마 준수)"""
    return {
        "version": f"{TODAY_STR}_1",
        "updated_at": get_utc_timestamp(),
        "checklists": [
            {
                "id": "min_rr",
                "item": "리스크/보상 ≥ 1.5",
                "metric": "rr",
                "threshold": 1.5,
                "critical": True
            },
            {
                "id": "max_drawdown",
                "item": "MDD ≤ 5%",
                "metric": "drawdown_pct",
                "threshold": 5.0,
                "critical": False
            }
        ]
    }

def create_memory_guideline():
    """memory_guideline.json (스키마 준수)"""
    return {
        "version": f"{TODAY_STR}_1",
        "updated_at": get_utc_timestamp(),
        "short_memory_rule": "최근 5~20일간 시장 주요 변화와 수익률을 중심으로 요약한다.",
        "mid_memory_rule": "최근 20~60일간 주요 전략별 성공/실패 사례 분석을 중점적으로 기록한다.",
        "long_memory_rule": "60일 이상의 거시 트렌드 및 지표 변화를 추적한다.",
        "length_limit_tokens": 350,
        "style_guide": "모든 용어와 톤을 부서 기준에 맞춰 일관되게 기록한다."
    }

def insert_episodes_meta(dept_db, dept_name):
    """
    episodes_meta/{loop}/{episode}/ 하위에 각 JSON 문서를 폴더+파일명(_id)으로 저장
    """
    episodes_meta = dept_db['episodes_meta']
    loop, episode = LOOP, EPISODE
    base_path = f"{loop}/{episode}/"

    # 1. episode_trades.json
    episodes_meta.update_one(
        {'_id': f"{base_path}episode_trades.json"},
        {'$set': {
            '_id': f"{base_path}episode_trades.json",
            'trades': create_episode_trades_data()
        }},
        upsert=True
    )

    # 2. metrics.json
    episodes_meta.update_one(
        {'_id': f"{base_path}metrics.json"},
        {'$set': {
            '_id': f"{base_path}metrics.json",
            **create_metrics()
        }},
        upsert=True
    )

    # 3. feedback_agent/problem_recognition_agent.json
    episodes_meta.update_one(
        {'_id': f"{base_path}feedback_agent/problem_recognition_agent.json"},
        {'$set': {
            '_id': f"{base_path}feedback_agent/problem_recognition_agent.json",
            **create_problem_recognition_agent()
        }},
        upsert=True
    )
    # 4. feedback_agent/hypothesis_agent.json
    episodes_meta.update_one(
        {'_id': f"{base_path}feedback_agent/hypothesis_agent.json"},
        {'$set': {
            '_id': f"{base_path}feedback_agent/hypothesis_agent.json",
            **create_hypothesis_agent()
        }},
        upsert=True
    )
    # 5. case_update_agent/strategy_cases.json
    episodes_meta.update_one(
        {'_id': f"{base_path}case_update_agent/strategy_cases.json"},
        {'$set': {
            '_id': f"{base_path}case_update_agent/strategy_cases.json",
            **create_strategy_cases()
        }},
        upsert=True
    )
    # 6. checklist_update_agent/strategy_checklists.json
    episodes_meta.update_one(
        {'_id': f"{base_path}checklist_update_agent/strategy_checklists.json"},
        {'$set': {
            '_id': f"{base_path}checklist_update_agent/strategy_checklists.json",
            **create_strategy_checklists()
        }},
        upsert=True
    )
    # 7. memory_guideline_update_agent/memory_guideline.json
    episodes_meta.update_one(
        {'_id': f"{base_path}memory_guideline_update_agent/memory_guideline.json"},
        {'$set': {
            '_id': f"{base_path}memory_guideline_update_agent/memory_guideline.json",
            **create_memory_guideline()
        }},
        upsert=True
    )
