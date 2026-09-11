from app.services.consultation_service import (
    start_consultation,
    continue_consultation,
)


print("===== 최초 상담 =====")

result = start_consultation(
    """
    79세 어머니가 성남시에 혼자 살고 계시고
    최근 식사 준비가 힘들어졌어요.
    """
)

print(result.situation.model_dump_json(indent=2))
print("부족한 정보:", result.missing_fields)
print("현재 확인할 필드:", result.current_field)
print("다음 질문:", result.next_question)
print("추천 준비 완료:", result.ready_for_recommendation)


print("\n===== 첫 번째 추가답변 =====")

result = continue_consultation(
    situation=result.situation,
    user_answer="기초연금을 받고 있어요.",
)

print(result.situation.model_dump_json(indent=2))
print("부족한 정보:", result.missing_fields)
print("현재 확인할 필드:", result.current_field)
print("다음 질문:", result.next_question)
print("추천 준비 완료:", result.ready_for_recommendation)


print("\n===== 두 번째 추가답변 =====")

result = continue_consultation(
    situation=result.situation,
    user_answer="현재 다른 돌봄서비스는 이용하고 있지 않아요.",
)

print(result.situation.model_dump_json(indent=2))
print("부족한 정보:", result.missing_fields)
print("현재 확인할 필드:", result.current_field)
print("다음 질문:", result.next_question)
print("추천 준비 완료:", result.ready_for_recommendation)