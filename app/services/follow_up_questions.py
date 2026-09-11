QUESTION_MAP = {
    "age": "대상자의 만 나이가 어떻게 되나요?",
    "residence": "현재 어느 지역에 거주하고 계신가요?",
    "welfare_status": (
        "기초생활수급자, 차상위계층 또는 기초연금을 받고 계신가요?"
    ),
    "care_needs": (
        "현재 일상생활에서 어떤 도움이 필요하신가요? "
        "예: 식사 준비, 청소, 외출, 이동 등"
    ),
    "duplicate_services": (
        "현재 장기요양서비스 등 다른 돌봄서비스를 이용하고 계신가요?"
    ),
}


def get_follow_up_question(field_name: str) -> str:
    return QUESTION_MAP.get(
        field_name,
        "추가 확인이 필요한 정보가 있습니다."
    )


def get_next_question(missing_fields: list[str]) -> str | None:
    if not missing_fields:
        return None

    first_missing_field = missing_fields[0]

    return get_follow_up_question(first_missing_field)