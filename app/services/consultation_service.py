from pydantic import BaseModel, Field

from app.models.user_situation import UserSituation
from app.services.situation_extractor import extract_user_situation
from app.services.missing_fields import get_missing_fields
from app.services.follow_up_questions import get_next_question
from app.services.situation_updater import update_user_situation


class ConsultationResult(BaseModel):
    situation: UserSituation
    missing_fields: list[str]

    # 사용자가 "잘 모르겠어요"라고 답해서
    # 더 이상 반복해서 묻지 않을 필드
    unknown_fields: list[str] = Field(default_factory=list)

    current_field: str | None = None
    next_question: str | None = None
    ready_for_recommendation: bool = False


def _build_result(
    situation: UserSituation,
    unknown_fields: list[str] | None = None,
) -> ConsultationResult:

    if unknown_fields is None:
        unknown_fields = []

    # UserSituation 기준으로 원래 부족한 필드
    all_missing_fields = get_missing_fields(situation)

    # 사용자가 이미 "모른다"고 답한 필드는
    # 다시 질문하지 않는다.
    remaining_missing_fields = [
        field
        for field in all_missing_fields
        if field not in unknown_fields
    ]

    # 더 이상 질문할 필드가 없으면
    # B의 추천/판정 단계로 이동
    if not remaining_missing_fields:
        return ConsultationResult(
            situation=situation,
            missing_fields=[],
            unknown_fields=unknown_fields,
            current_field=None,
            next_question=None,
            ready_for_recommendation=True,
        )

    return ConsultationResult(
        situation=situation,
        missing_fields=remaining_missing_fields,
        unknown_fields=unknown_fields,
        current_field=remaining_missing_fields[0],
        next_question=get_next_question(remaining_missing_fields),
        ready_for_recommendation=False,
    )


def start_consultation(user_text: str) -> ConsultationResult:
    situation = extract_user_situation(user_text)

    return _build_result(
        situation=situation,
        unknown_fields=[],
    )


def continue_consultation(
    situation: UserSituation,
    user_answer: str,
    unknown_fields: list[str] | None = None,
) -> ConsultationResult:

    if unknown_fields is None:
        unknown_fields = []

    # 현재 UserSituation에서 부족한 필드 확인
    all_missing_fields = get_missing_fields(situation)

    # 이미 "모른다"고 답한 필드는 다시 묻지 않는다.
    remaining_missing_fields = [
        field
        for field in all_missing_fields
        if field not in unknown_fields
    ]

    # 더 이상 질문할 내용이 없으면 추천 단계로 이동
    if not remaining_missing_fields:
        return _build_result(
            situation=situation,
            unknown_fields=unknown_fields,
        )

    current_field = remaining_missing_fields[0]

    updated_situation, answer_relevant, answer_unknown = (
        update_user_situation(
            situation=situation,
            field_name=current_field,
            user_answer=user_answer,
        )
    )

    # 질문과 전혀 관계없는 답변
    if not answer_relevant:
        return ConsultationResult(
            situation=situation,
            missing_fields=remaining_missing_fields,
            unknown_fields=unknown_fields,
            current_field=current_field,
            next_question=(
                "방금 답변에서는 현재 질문에 필요한 정보를 "
                "확인하지 못했어요. "
                + get_next_question(remaining_missing_fields)
            ),
            ready_for_recommendation=False,
        )

    # 질문은 이해했지만 사용자가 정보를 모르는 경우
    if answer_unknown:
        updated_unknown_fields = unknown_fields.copy()

        if current_field not in updated_unknown_fields:
            updated_unknown_fields.append(current_field)

        return _build_result(
            situation=situation,
            unknown_fields=updated_unknown_fields,
        )

    # 정상적으로 값을 받은 경우
    return _build_result(
        situation=updated_situation,
        unknown_fields=unknown_fields,
    )