from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from app.models.user_situation import UserSituation


load_dotenv()

client = OpenAI()


class FollowUpUpdate(BaseModel):
    answer_relevant: bool = False

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

가장 중요한 규칙:

사용자의 답변이 현재 질문에 실제로 답하고 있는지 먼저 판단한다.

- 현재 질문에 명확하게 답했다면 answer_relevant=true
- 질문과 관계없는 이야기를 했다면 answer_relevant=false
- 관련 단어나 지역명 등이 문장에 우연히 포함되어 있어도,
  현재 질문에 대한 답변이 아니라면 answer_relevant=false

예시:

field_name = residence

사용자:
"성남시에 살고 있어요."
→ answer_relevant=true
→ residence="성남시"

사용자:
"대구 형제는 형이 잘생겼어요? 동생이 잘생겼어요?"
→ answer_relevant=false
→ residence=null


field_name = welfare_status

사용자:
"기초연금을 받고 있어요."
→ answer_relevant=true
→ welfare_status="기초연금수급자"

사용자:
"오늘 날씨가 좋아요."
→ answer_relevant=false
→ welfare_status=null


추가 규칙:

1. 현재 질문과 관련된 정보만 추출한다.

2. 사용자가 말하지 않은 내용은 추측하지 않는다.

3. 불명확한 값은 null로 둔다.

4. 다른 필드의 값을 임의로 생성하지 않는다.

5. answer_relevant=false인 경우
   어떤 정보도 추측하거나 업데이트하지 않는다.


welfare_status의 경우 가능한 한 다음 표현으로 정규화한다.

- 기초생활수급자
- 차상위계층
- 기초연금수급자
- 해당 없음


duplicate_services의 경우:

- 이용 중인 서비스가 명확하면 해당 서비스명을 배열에 넣는다.
- 이용 중인 서비스가 없다고 명확히 말하면 빈 배열로 둔다.
- 이용 여부가 확인되면 duplicate_service_unknown=false
- 답변만으로 알 수 없다면 duplicate_service_unknown=null


care_needs의 경우:

- 사용자가 실제로 말한 어려움만 기록한다.
- 지원 방법을 임의로 추론하지 않는다.
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
) -> tuple[UserSituation, bool]:

    update = parse_follow_up_answer(
        field_name=field_name,
        user_answer=user_answer,
    )

    # 현재 질문과 관계없는 답변이면
    # 기존 UserSituation을 수정하지 않는다.
    if not update.answer_relevant:
        return situation, False

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

    return UserSituation(**data), True