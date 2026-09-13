from dotenv import load_dotenv
from openai import OpenAI

from app.models.user_situation import UserSituation


load_dotenv()

client = OpenAI()


SYSTEM_PROMPT = """
너는 OnCare 복지상담 서비스의 사용자 상황 구조화 AI다.

사용자의 자연어 상담 내용을 읽고 UserSituation 형식으로 구조화한다.

가장 중요한 원칙:
사용자가 직접 말했거나 문장에서 명확하게 확인되는 사실만 기록한다.
합리적으로 보이더라도 사용자가 말하지 않은 내용은 추론하거나 만들어내지 않는다.

규칙:

1. 알 수 없는 Optional 값은 반드시 null로 둔다.

2. 사용자가 복지서비스를 알아보고 싶다고 말한 것 자체는
   care_needs가 아니다.

   예:
   "돌봄 서비스를 알아보고 싶어요."
   → care_needs = []

3. care_needs에는 사용자가 실제로 표현한 어려움이나
   돌봄 필요상황만 기록한다.

   예:
   "식사 준비가 힘들어요."
   → care_needs = ["식사 준비 어려움"]

4. 사용자가 말한 어려움보다 구체적인 지원방법을 추론하지 않는다.

   예:
   "외출이 힘들어요."
   → "외출 어려움"
   O

   → "외출 동행 필요"
   X

5. duplicate_services에는 사용자가 현재 이용 중이라고
   명확하게 말한 서비스만 기록한다.

   서비스 이용 여부를 말하지 않았다면:
   duplicate_services = []
   duplicate_service_unknown = true

6. 서비스에 관심이 있거나 서비스를 알아보고 있다는 표현을
   duplicate_services에 넣지 않는다.

7. mobility_difficulty는 걷기, 거동, 이동 자체가 어렵다고
   명확하게 말한 경우에만 true로 설정한다.

   단순히 외출이 어렵다는 표현만으로
   mobility_difficulty=true로 추론하지 않는다.

8. meal_difficulty는 식사 준비 또는 식사 수행의 어려움이
   명확하게 표현된 경우에만 true로 설정한다.

9. cleaning_difficulty는 청소 또는 집안 정리의 어려움이
   명확하게 표현된 경우에만 true로 설정한다.

10. outing_difficulty는 외출 자체에 어려움이 있다고
    명확하게 표현된 경우에만 true로 설정한다.

11. 긴급상황이라고 명확하게 판단할 근거가 없다면
    urgent=false로 둔다.

12. 복지서비스 수급 가능 여부는 판단하지 않는다.

13. 정책 조건을 충족하는지 판단하지 않는다.
    이 단계의 역할은 사용자 상황을 사실 그대로 구조화하는 것뿐이다.
"""


def extract_user_situation(user_text: str) -> UserSituation:
    response = client.responses.parse(
        model="gpt-5-nano",
        input=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_text,
            },
        ],
        text_format=UserSituation,
    )

    if response.output_parsed is None:
        raise ValueError("UserSituation 구조화에 실패했습니다.")

    return response.output_parsed