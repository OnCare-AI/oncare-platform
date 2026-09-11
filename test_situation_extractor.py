from app.services.situation_extractor import extract_user_situation


test_cases = [
    "어머니 돌봄 서비스를 알아보고 싶어요.",
    "아버지는 62세이고 혼자 살고 계세요.",
    """
    79세 어머니가 성남시에 혼자 살고 계시고,
    최근 식사 준비와 외출이 많이 힘들어졌어요.
    """,
]


for index, user_text in enumerate(test_cases, start=1):
    print(f"\n===== 테스트 {index} =====")

    situation = extract_user_situation(user_text)

    print(situation.model_dump_json(indent=2))