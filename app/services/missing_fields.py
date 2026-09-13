from app.models.user_situation import UserSituation


def get_missing_fields(situation: UserSituation) -> list[str]:
    missing_fields: list[str] = []

    # 노인맞춤돌봄서비스 예선 판단에 필요한 핵심 정보
    if situation.age is None:
        missing_fields.append("age")

    if situation.residence is None:
        missing_fields.append("residence")

    if situation.welfare_status is None:
        missing_fields.append("welfare_status")

    if not situation.care_needs:
        missing_fields.append("care_needs")

    # duplicate_services가 []라고 해서
    # 반드시 "이용 중인 서비스가 없다"는 뜻은 아님.
    # 이용 여부를 모르는 경우에는 추가 확인이 필요함.
    if situation.duplicate_service_unknown:
        missing_fields.append("duplicate_services")

    return missing_fields