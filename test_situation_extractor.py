from app.services.situation_extractor import extract_user_situation


user_text = """
78세인 어머니가 혼자 살고 계십니다.
기초연금을 받고 계시고 최근에는 식사 준비가 힘들다고 하세요.
"""

situation = extract_user_situation(user_text)

print(situation.model_dump_json(indent=2))