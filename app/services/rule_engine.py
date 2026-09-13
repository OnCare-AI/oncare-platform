# app/services/rule_engine.py
# 노인맞춤돌봄서비스 자격조건을 UserSituation 기준으로 검증하는 Rule Engine
# 참고: 데이터명세 섹션 3(Eligibility/Exclusion Rule), 섹션 10(Rule Engine 출력 상태), 섹션 11(테스트케이스)

from app.models.user_situation import UserSituation
from app.data.policy_data import SERVICES

# Rule Engine이 반환하는 4가지 상태 (섹션 10)
STATUS_POTENTIAL_MATCH = "POTENTIAL_MATCH"
STATUS_NEEDS_CHECK = "NEEDS_CHECK"
STATUS_LIKELY_NOT_MATCH = "LIKELY_NOT_MATCH"
STATUS_OFFICIAL_ASSESSMENT_REQUIRED = "OFFICIAL_ASSESSMENT_REQUIRED"

MIN_AGE = 65
# R02 판정에 쓰는 welfare_status 키워드
WELFARE_KEYWORDS = ["기초생활수급자", "차상위", "기초연금수급자", "차상위계층"]

# 모든 서비스의 rag_keywords를 하나로 모아둠 (care_needs가 구체적인지 판단할 때 사용)
_ALL_SERVICE_KEYWORDS = set()
for _service in SERVICES:
    _ALL_SERVICE_KEYWORDS.update(_service["rag_keywords"])


def _care_needs_are_specific(care_needs: list[str]) -> bool:
    """care_needs 중 하나라도 알려진 서비스 키워드와 일치하면 '구체적'으로 판단."""
    return any(need in _ALL_SERVICE_KEYWORDS for need in care_needs)


def evaluate(situation: UserSituation) -> dict:
    """
    UserSituation을 받아 Rule Engine 판정 결과를 반환한다.
    반환값: {status, reason, missing_fields, institution_review_required}
    """
    missing_fields = []
    reasons = []

    # R01: 나이 (65세 이상) - 미달이면 바로 종료
    if situation.age is None:
        missing_fields.append("age")
    elif situation.age < MIN_AGE:
        return {
            "status": STATUS_LIKELY_NOT_MATCH,
            "reason": f"연령이 {situation.age}세로 만 {MIN_AGE}세 미만이라 명시적 공개 기준과 맞지 않을 가능성이 큽니다.",
            "missing_fields": [],
            "institution_review_required": False,
        }

    # R02: 복지자격 (기초생활수급자/차상위/기초연금수급자 등)
    if situation.welfare_status is None:
        missing_fields.append("welfare_status")
    elif not any(keyword in situation.welfare_status for keyword in WELFARE_KEYWORDS):
        missing_fields.append("welfare_status")  # 명확히 해당 안 됨으로 단정하지 않고 재확인 요청

    # R03: 돌봄 필요 상황
    if not situation.care_needs:
        missing_fields.append("care_needs")

    # R04: 유사·중복사업 확인 (장기요양보험 등) - 있다고 무조건 탈락시키지 않음
    institution_review_required = False
    if situation.duplicate_service_unknown:
        missing_fields.append("duplicate_services")
    elif situation.duplicate_services:
        if situation.long_term_care_expired is True:
            reasons.append("장기요양 등급이 만료되어 중복 예외 가능성이 있습니다 (원문 확인 필요).")
            institution_review_required = True
        elif situation.long_term_care_expired is None:
            missing_fields.append("long_term_care_expired")
        else:
            reasons.append("현재 유사·중복 서비스를 이용 중으로 확인되어, 우선사업/예외 여부를 기관에서 확인해야 합니다.")
            institution_review_required = True

    # 긴급돌봄 여부 - 상태를 바꾸진 않고 안내 문구만 추가
    if situation.urgent:
        reasons.append("긴급돌봄이 필요한 상황으로 확인되어, 선제공 후 사후승인 제도 안내가 가능합니다.")

    # 부족정보가 있으면 NEEDS_CHECK로 반환 (A의 추가질문 로직과 연결되는 지점)
    if missing_fields:
        return {
            "status": STATUS_NEEDS_CHECK,
            "reason": "필수 정보가 부족하여 추가 확인이 필요합니다: " + ", ".join(missing_fields),
            "missing_fields": missing_fields,
            "institution_review_required": institution_review_required,
        }

    # 돌봄필요 내용이 막연해서 어떤 서비스가 맞는지 특정하기 어려운 경우
    if not _care_needs_are_specific(situation.care_needs):
        return {
            "status": STATUS_OFFICIAL_ASSESSMENT_REQUIRED,
            "reason": "돌봄필요 내용이 구체적이지 않아 어떤 서비스가 적합한지 특정하기 어렵습니다. 선정조사를 통한 기관 판단이 필요합니다.",
            "missing_fields": [],
            "institution_review_required": True,
        }

    # 여기까지 왔으면 명시적 조건은 충족 - 다만 최종 확정은 R06(선정조사) 영역
    reasons.append("연령·복지자격·돌봄필요 등 명시적 기본조건을 충족한 것으로 보입니다.")
    return {
        "status": STATUS_POTENTIAL_MATCH,
        "reason": " ".join(reasons),
        "missing_fields": [],
        "institution_review_required": True,  # R06: 최종 확정은 항상 선정조사·시군구 심의 필요
    }