from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from app.models.user_situation import UserSituation


load_dotenv()

client = OpenAI()


class FollowUpUpdate(BaseModel):
    age: Optional[int] = None
    residence: Optional[str] = None
    welfare_status: Optional[str] = None
    care_needs: Optional[list[str]] = None

    duplicate_services: Optional[list[str]] = None
    duplicate_service_unknown: Optional[bool] = None


def parse_follow_up_answer(
    field_name: str,
    user_answer: str,
) -> FollowUpUpdate:

    prompt = f"""
너는 OnCare 복지상담 서비스의 추가답변 구조화 AI다.

현재 확인하고 있는 필드는 다음과 같다.

field_name: {field_name}

사용자의 답변:
{user_answer}

규칙:

1. 현재 질문과 관련된 정보만 추출한다.
2. 사용자가 말하지 않은 내용은 추측하지 않는다.
3. 불명확한 값은 null로 둔다.
4. 다른 필드의 값을 임의로 생성하지 않는다.

welfare_status의 경우 가능한 한 다음 표현으로 정규화한다.
- 기초생활수급자
- 차상위계층
- 기초연금수급자
- 해당 없음

duplicate_services의 경우:
- 이용 중인 서비스가 명확하면 해당 서비스명을 배열에 넣는다.
- 이용 중인 서비스가 없다고 명확히 말하면 빈 배열로 둔다.
- 이용 여부가 확인되면 duplicate_service_unknown은 false다.
- 답변만으로 알 수 없다면 duplicate_service_unknown은 null이다.

care_needs의 경우 사용자가 실제로 말한 어려움만 기록한다.
지원 방법을 임의로 추론하지 않는다.
"""

    response = client.responses.parse(
        model="gpt-5-nano",
        input=prompt,
        text_format=FollowUpUpdate,
    )

    if response.output_parsed is None:
        raise ValueError("추가답변 구조화에 실패했습니다.")

    return response.output_parsed


def update_user_situation(
    situation: UserSituation,
    field_name: str,
    user_answer: str,
) -> UserSituation:

    update = parse_follow_up_answer(
        field_name=field_name,
        user_answer=user_answer,
    )

    data = situation.model_dump()

    if field_name == "duplicate_services":
        if update.duplicate_services is not None:
            data["duplicate_services"] = update.duplicate_services

        if update.duplicate_service_unknown is not None:
            data["duplicate_service_unknown"] = (
                update.duplicate_service_unknown
            )

    else:
        value = getattr(update, field_name, None)

        if value is not None:
            data[field_name] = value

    return UserSituation(**data)