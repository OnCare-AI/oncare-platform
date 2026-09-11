from app.models.user_situation import UserSituation


situation = UserSituation(
    age=78,
    residence="성남시",
    welfare_status="기초연금수급자",
    living_alone=True,
    care_needs=["식사 지원"],
    meal_difficulty=True,
)

print(situation.model_dump_json(indent=2))