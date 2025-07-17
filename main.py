#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메인 실행 파일 - 모든 더미 데이터를 생성하고 MongoDB에 저장합니다.
"""

from config import clear_databases, DEPARTMENTS, dept_dbs, TODAY_STR, LOOP, EPISODE
from data_generators.central_memory import (
    insert_central_memory  # <- 최신 구조 함수만 import
)
from data_generators.daily_snapshots import (
    insert_daily_snapshots
)
from data_generators.episodes_meta import (
    insert_episodes_meta
)

def main():
    """메인 함수 - 모든 더미 데이터를 생성하고 MongoDB에 저장"""
    print("🚀 더미 데이터 생성 및 MongoDB 저장을 시작합니다...")
    print(f"📅 오늘 날짜: {TODAY_STR}")
    print(f"🔄 반복 횟수: {LOOP}")
    print(f"📊 에피소드 수: {EPISODE}")
    print("-" * 50)

    # 1. 기존 데이터 정리
    print("🗑️  기존 데이터베이스를 정리합니다...")
    clear_databases()

    # 2. 각 부서별로 더미 데이터 생성 및 저장
    for dept in DEPARTMENTS:
        print(f"\n📂 [{dept}] 부서 데이터 생성 중...")
        db = dept_dbs[dept]

        # Central Memory 데이터 삽입 (strategy_cases, strategy_checklists, memory_guideline 분리)
        print(f"  📋 {dept} - Central Memory 데이터 생성 중...")
        insert_central_memory(db, dept)   # 이 함수가 내부적으로 3개의 JSON 각각 저장함

        # Daily Snapshots 데이터 삽입 (더미 데이터 사용)
        print(f"  📈 {dept} - Daily Snapshots 데이터 생성 중...")
        insert_daily_snapshots(db, dept, use_real_market_data=False)

        # Episodes Meta 데이터 삽입 (스키마에 맞춘 파일/경로 구조)
        print(f"  🎯 {dept} - Episodes Meta 데이터 생성 중...")
        insert_episodes_meta(db, dept)

        print(f"  ✅ {dept} 부서 데이터 생성 완료!")

    # 3. 결과 확인
    print("\n" + "=" * 50)
    print("📊 데이터 생성 결과:")
    print("=" * 50)

    total_documents = 0
    for dept in DEPARTMENTS:
        db = dept_dbs[dept]

        central_memory_count = db.central_memory.count_documents({})
        daily_snapshots_count = db.daily_snapshots.count_documents({})
        episodes_meta_count = db.episodes_meta.count_documents({})

        dept_total = central_memory_count + daily_snapshots_count + episodes_meta_count
        total_documents += dept_total

        print(f"🏢 {dept}:")
        print(f"   📋 central_memory: {central_memory_count}개 문서")
        print(f"   📈 daily_snapshots: {daily_snapshots_count}개 문서")
        print(f"   🎯 episodes_meta: {episodes_meta_count}개 문서")
        print(f"   📊 부서 총합: {dept_total}개 문서")
        print()

    print(f"🎉 전체 생성된 문서 수: {total_documents}개")
    print(f"🎉 생성된 데이터베이스 수: {len(DEPARTMENTS)}개")
    print("\n✨ 모든 더미 데이터 생성이 완료되었습니다!")

if __name__ == "__main__":
    main()