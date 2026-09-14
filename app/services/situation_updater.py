from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from app.models.user_situation import UserSituation


load_dotenv()

client = OpenAI()


class FollowUpUpdate(BaseModel):
    # 현재 질문에 대한 답변인지
    answer_relevant: bool = False

    # 질문은 이해했지만 사용자가 정보를 모르는지
    answer_unknown: bool = False

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

먼저 사용자의 답변을 아래 3가지 경우 중 하나로 판단한다.


[1. 질문에 정상적으로 답한 경우]

현재 질문에 필요한 정보를 사용자가 명확하게 답했다면:

answer_relevant=true
answer_unknown=false

그리고 현재 field_name에 해당하는 값만 추출한다.


[2. 질문은 이해했지만 정보를 모르는 경우]

사용자가 다음과 같은 취지로 답했다면:

- "잘 모르겠어요"
- "모르겠어요"
- "모릅니다"
- "확인하지 못했어요"
- "잘 모르겠는데요"
- "기억이 안 나요"
- "확인해봐야 해요"

현재 질문과 관계없는 답변으로 판단하지 않는다.

이 경우 반드시:

answer_relevant=true
answer_unknown=true

로 판단한다.

그리고 알 수 없는 값을 임의로 추측하지 말고 null로 둔다.


[3. 질문과 관계없는 답변인 경우]

현재 질문과 관계없는 이야기를 했다면:

answer_relevant=false
answer_unknown=false

관련 단어나 지역명 등이 문장에 우연히 포함되어 있더라도
현재 질문에 대한 답변이 아니라면 answer_relevant=false로 판단한다.


예시 1: residence

사용자:
"성남시에 살고 있어요."

→ answer_relevant=true
→ answer_unknown=false
→ residence="성남시"


사용자:
"어디 사는지는 잘 모르겠어요."

→ answer_relevant=true
→ answer_unknown=true
→ residence=null


사용자:
"대구 형제는 형이 잘생겼어요? 동생이 잘생겼어요?"

→ answer_relevant=false
→ answer_unknown=false
→ residence=null


예시 2: welfare_status

사용자:
"기초연금을 받고 있어요."

→ answer_relevant=true
→ answer_unknown=false
→ welfare_status="기초연금수급자"


사용자:
"그건 잘 모르겠어요."

→ answer_relevant=true
→ answer_unknown=true
→ welfare_status=null


사용자:
"확인해봐야 알 것 같아요."

→ answer_relevant=true
→ answer_unknown=true
→ welfare_status=null


사용자:
"오늘 날씨가 좋아요."

→ answer_relevant=false
→ answer_unknown=false
→ welfare_status=null


예시 3: age

사용자:
"82세예요."

→ answer_relevant=true
→ answer_unknown=false
→ age=82


사용자:
"정확한 나이는 잘 모르겠어요."

→ answer_relevant=true
→ answer_unknown=true
→ age=null


추가 규칙:

1. 현재 질문과 관련된 정보만 추출한다.

2. 사용자가 말하지 않은 내용은 추측하지 않는다.

3. 불명확한 값은 null로 둔다.

4. 다른 필드의 값을 임의로 생성하지 않는다.

5. answer_relevant=false인 경우
   어떤 정보도 추측하거나 업데이트하지 않는다.

6. answer_unknown=true인 경우
   해당 필드의 실제 값을 임의로 만들지 않는다.

7. answer_unknown=true와 answer_relevant=false를 동시에 사용하지 않는다.


welfare_status의 경우 가능한 한 다음 표현으로 정규화한다.

- 기초생활수급자
- 차상위계층
- 기초연금수급자
- 해당 없음


duplicate_services의 경우:

- 이용 중인 서비스가 명확하면 해당 서비스명을 배열에 넣는다.
- 이용 중인 서비스가 없다고 명확히 말하면 빈 배열로 둔다.
- 이용 여부가 확인되면 duplicate_service_unknown=false
- 사용자가 이용 여부를 모른다고 답했다면
  answer_unknown=true
  duplicate_service_unknown=true
- 답변만으로 판단할 수 없다면 임의로 추측하지 않는다.


care_needs의 경우:

- 사용자가 실제로 말한 어려움만 기록한다.
- 지원 방법을 임의로 추론하지 않는다.
- 사용자가 어려움을 잘 모르겠다고 답했다면
  answer_unknown=true로 판단한다.
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
) -> tuple[UserSituation, bool, bool]:
    """
    반환값:
    (
        수정된 UserSituation,
        answer_relevant,
        answer_unknown
    )

    예:
    정상 답변
    → (updated_situation, True, False)

    "잘 모르겠어요"
    → (기존 situation, True, True)

    엉뚱한 답변
    → (기존 situation, False, False)
    """

    update = parse_follow_up_answer(
        field_name=field_name,
        user_answer=user_answer,
    )

    # 질문과 관계없는 답변
    if not update.answer_relevant:
        return situation, False, False

    # 질문은 이해했지만 사용자가 정보를 모르는 경우
    #
    # 여기서는 UserSituation에 가짜 값을 넣지 않는다.
    # consultation_service에서 이 필드를
    # "사용자가 모른다고 확인한 필드"로 처리한다.
    if update.answer_unknown:
        return situation, True, True

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

    return UserSituation(**data), True, False