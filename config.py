import datetime
from pymongo import MongoClient

# MongoDB 연결
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
    dept_dbs[dept] = dept_db

TODAY_STR = datetime.date(2025, 6, 30).strftime("%Y-%m-%d")
LOOP = 12
EPISODE = 5

def get_utc_timestamp():
    """현재 UTC 타임스탬프를 ISO 형식으로 반환합니다."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def clear_databases():
    """모든 부서 데이터베이스 초기화"""
    for dept in DEPARTMENTS:
        dept_db = client[dept]
        # 이전 실행 데이터를 초기화하여 항상 새로운 상태에서 시작
        for collection_name in dept_db.list_collection_names():
            dept_db[collection_name].drop()
        print(f"Database '{dept}' cleared and ready.") 