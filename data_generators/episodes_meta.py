import pandas as pd
import random
from config import get_utc_timestamp, TODAY_STR, LOOP, EPISODE

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

def insert_episodes_meta(dept_db, dept_name):
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
    
    # 에피소드 문서들 생성
    episode_docs = {
        'trades_data': create_episode_trades_data(),
        'metrics': create_metrics(),
        'feedback': create_feedback(),
        'strategy_update_agent_config': create_strategy_update_agent_config(),
        'memory_guideline_update_agent_config': create_memory_guideline_update_agent_config(),
    }
    
    # 각 에피소드 문서의 고유 ID 생성: {loop}_{episode}_{type}
    base_id = f"{LOOP}_{EPISODE}"
    
    # episode_trades.arrow
    episodes_meta.update_one(
        {'_id': f"{base_id}_episode_trades"},
        {'$set': {'_id': f"{base_id}_episode_trades", 'loop': LOOP, 'episode': EPISODE, 'trades_data': episode_docs['trades_data']}},
        upsert=True
    )
    
    # metrics.json
    episodes_meta.update_one(
        {'_id': f"{base_id}_metrics"},
        {'$set': {'_id': f"{base_id}_metrics", 'loop': LOOP, 'episode': EPISODE, **episode_docs['metrics']}},
        upsert=True
    )
    
    # feedback_agent.json
    episodes_meta.update_one(
        {'_id': f"{base_id}_feedback_agent"},
        {'$set': {'_id': f"{base_id}_feedback_agent", 'loop': LOOP, 'episode': EPISODE, **episode_docs['feedback']}},
        upsert=True
    )
    
    # strategy_update_agent.json
    episodes_meta.update_one(
        {'_id': f"{base_id}_strategy_update_agent"},
        {'$set': {'_id': f"{base_id}_strategy_update_agent", 'loop': LOOP, 'episode': EPISODE, **episode_docs['strategy_update_agent_config']}},
        upsert=True
    )
    
    # memory_guideline_update_agent.json
    episodes_meta.update_one(
        {'_id': f"{base_id}_memory_guideline_update_agent"},
        {'$set': {'_id': f"{base_id}_memory_guideline_update_agent", 'loop': LOOP, 'episode': EPISODE, **episode_docs['memory_guideline_update_agent_config']}},
        upsert=True
    ) 