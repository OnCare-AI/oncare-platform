from app.models.user_situation import UserSituation
from app.services.missing_fields import get_missing_fields
from app.services.situation_updater import update_user_situation


situation = UserSituation(
    age=79,
    residence="성남시",
    living_alone=True,
    care_needs=["식사 준비 어려움"],
    meal_difficulty=True,
)

print("=== 답변 반영 전 ===")
print(situation.model_dump_json(indent=2))

print("\n부족한 정보:")
print(get_missing_fields(situation))


situation = update_user_situation(
    situation=situation,
    field_name="welfare_status",
    user_answer="기초연금을 받고 있어요.",
)


print("\n=== 답변 반영 후 ===")
print(situation.model_dump_json(indent=2))

print("\n남은 부족한 정보:")
print(get_missing_fields(situation))

situation = update_user_situation(
    situation=situation,
    field_name="duplicate_services",
    user_answer="현재 다른 돌봄서비스는 이용하고 있지 않아요.",
)

print("\n=== 두 번째 답변 반영 후 ===")
print(situation.model_dump_json(indent=2))

print("\n최종 부족한 정보:")
print(get_missing_fields(situation))