# test_policy_recommendation.py
from app.models.user_situation import UserSituation
from app.services.policy_recommendation import recommend

t1 = UserSituation(age=78, welfare_status="기초연금수급자", care_needs=["안부확인"],
                    duplicate_services=[], duplicate_service_unknown=False)
result = recommend(t1)
print("status:", result.status)
print("reason:", result.reason)
print("matched_services:", result.matched_services)
print("source_ids:", result.source_ids)