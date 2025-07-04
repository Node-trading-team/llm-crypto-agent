from config import get_utc_timestamp, TODAY_STR

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

def insert_central_memory(dept_db, dept_name):
    """
    central_memory 폴더 구조 생성:
    - strategy_cases_checklist.json
    - memory_guideline.json
    """
    central_memory = dept_db['central_memory']
    
    # 문서 생성
    strategy_doc = create_strategy_cases_checklist(dept_name)
    guideline_doc = create_memory_guideline(dept_name)
    
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