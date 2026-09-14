# test_rule_engine.py
from app.models.user_situation import UserSituation
from app.services.rule_engine import evaluate

# T1: 기본충족 - 78세, 기초연금, 중복없음 → POTENTIAL_MATCH 기대
t1 = UserSituation(age=78, welfare_status="기초연금수급자", care_needs=["안부확인"],
                    duplicate_services=[], duplicate_service_unknown=False)
print("T1:", evaluate(t1))

# T2: 연령미달 - 62세 → LIKELY_NOT_MATCH 기대
t2 = UserSituation(age=62)
print("T2:", evaluate(t2))

# T3: 정보부족 - 79세, welfare_status=None → NEEDS_CHECK 기대
t3 = UserSituation(age=79, welfare_status=None)
print("T3:", evaluate(t3))

# T4: 장기요양 유효 - 80세, 장기요양 이용 중(만료 아님) → 중복 확인 필요 반영 기대
t4 = UserSituation(age=80, welfare_status="기초연금수급자", care_needs=["가사지원"],
                    duplicate_services=["노인장기요양보험"], duplicate_service_unknown=False,
                    long_term_care_expired=False)
print("T4:", evaluate(t4))

# T5: 장기요양 만료 - 80세, long_term_care_expired=True → 예외 가능성 반영 기대
t5 = UserSituation(age=80, welfare_status="기초연금수급자", care_needs=["가사지원"],
                    duplicate_services=["노인장기요양보험"], duplicate_service_unknown=False,
                    long_term_care_expired=True)
print("T5:", evaluate(t5))

# T6: 긴급돌봄 - urgent=True → 기본결과 + 긴급 안내 기대
t6 = UserSituation(age=78, welfare_status="기초연금수급자", care_needs=["가사지원"],
                    duplicate_services=[], duplicate_service_unknown=False, urgent=True)
print("T6:", evaluate(t6))

# T7: 기관판단 - 기본조건 일부 충족, 돌봄필요도 애매 → OFFICIAL_ASSESSMENT_REQUIRED 기대
t7 = UserSituation(age=80, welfare_status="기초연금수급자", care_needs=["돌봄필요"],
                    duplicate_services=[], duplicate_service_unknown=False)
print("T7:", evaluate(t7))