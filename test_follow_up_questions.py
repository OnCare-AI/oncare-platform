from app.models.user_situation import UserSituation
from app.services.missing_fields import get_missing_fields
from app.services.follow_up_questions import get_next_question


situation = UserSituation(
    age=79,
    residence="성남시",
    living_alone=True,
    care_needs=["식사 준비 어려움"],
    meal_difficulty=True,
)

missing_fields = get_missing_fields(situation)

print("부족한 정보:", missing_fields)
print("다음 질문:", get_next_question(missing_fields))