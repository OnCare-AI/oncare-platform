from app.models.user_situation import UserSituation
from app.services.missing_fields import get_missing_fields


situation = UserSituation(
    age=79,
    residence="성남시",
    living_alone=True,
    care_needs=["식사 준비 어려움"],
    meal_difficulty=True,
)

missing_fields = get_missing_fields(situation)

print(missing_fields)