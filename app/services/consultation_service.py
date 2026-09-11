from pydantic import BaseModel

from app.models.user_situation import UserSituation
from app.services.situation_extractor import extract_user_situation
from app.services.missing_fields import get_missing_fields
from app.services.follow_up_questions import get_next_question
from app.services.situation_updater import update_user_situation


class ConsultationResult(BaseModel):
    situation: UserSituation
    missing_fields: list[str]
    current_field: str | None = None
    next_question: str | None = None
    ready_for_recommendation: bool = False


def _build_result(situation: UserSituation) -> ConsultationResult:
    missing_fields = get_missing_fields(situation)

    if not missing_fields:
        return ConsultationResult(
            situation=situation,
            missing_fields=[],
            current_field=None,
            next_question=None,
            ready_for_recommendation=True,
        )

    return ConsultationResult(
        situation=situation,
        missing_fields=missing_fields,
        current_field=missing_fields[0],
        next_question=get_next_question(missing_fields),
        ready_for_recommendation=False,
    )


def start_consultation(user_text: str) -> ConsultationResult:
    situation = extract_user_situation(user_text)

    return _build_result(situation)


def continue_consultation(
    situation: UserSituation,
    user_answer: str,
) -> ConsultationResult:

    missing_fields = get_missing_fields(situation)

    if not missing_fields:
        return _build_result(situation)

    current_field = missing_fields[0]

    updated_situation = update_user_situation(
        situation=situation,
        field_name=current_field,
        user_answer=user_answer,
    )

    return _build_result(updated_situation)