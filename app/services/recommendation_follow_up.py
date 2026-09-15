import json

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from app.models.user_situation import UserSituation
from app.services.policy_recommendation import PolicyRecommendationResult


load_dotenv()

client = OpenAI()


class RecommendationFollowUpResult(BaseModel):
    answer: str


def answer_recommendation_follow_up(
    situation: UserSituation,
    recommendation: PolicyRecommendationResult,
    user_message: str,
    conversation_history: list[dict[str, str]] | None = None,
) -> RecommendationFollowUpResult:

    history = conversation_history or []

    prompt = f"""
너는 OnCare의 복지상담 후속 상담 AI다.

사용자는 이미 복지상담을 진행했고
정책 추천 또는 판정 결과까지 받은 상태다.

사용자가 상담 종료를 누르기 전까지
이전 상담의 맥락을 유지하면서 질문에 답해야 한다.


[현재 상담 대상자의 상황]

{json.dumps(
    situation.model_dump(),
    ensure_ascii=False,
    indent=2
)}


[현재 추천/판정 결과]

{json.dumps(
    recommendation.model_dump(),
    ensure_ascii=False,
    indent=2
)}


[이전 대화 내용]

{json.dumps(
    history,
    ensure_ascii=False,
    indent=2
)}


[사용자의 현재 질문]

{user_message}


반드시 다음 규칙을 따른다.

1. 이전 상담에서 확인된 대상자의 정보를 기억하고 답한다.

2. 이미 나온 추천 또는 판정 결과를 고려해서 답한다.

3. 사용자가
   "왜 추천됐어요?"
   "아까 어떤 서비스였어요?"
   "제가 말한 상황이 뭐였죠?"
   같은 질문을 하면
   이전 상담 내용을 바탕으로 설명한다.

4. AI가 복지서비스 대상 여부를 최종 확정했다고 말하지 않는다.

5. 기관의 공식 선정조사나 확인이 필요한 경우
   그 사실을 명확하게 안내한다.

6. 사용자가 말하지 않은 사실을 임의로 만들어내지 않는다.

7. 현재 제공된 정보만으로 확실하게 알 수 없는 내용은
   모른다고 설명하고 공식 확인이 필요하다고 안내한다.

8. 답변은 일반 시민이 이해하기 쉽게 작성한다.

9. 불필요하게 길게 답하지 않는다.

10. 기존 상담 대상자와
    현재 질문을 하는 사람을 혼동하지 않는다.

11. 이전 판정 결과와 모순되는 내용을 임의로 생성하지 않는다.

12. source_ids가 존재하더라도
    실제 확인하지 않은 문서 내용을 만들어내지 않는다.

13. 사용자가 단순한 사실을 물으면 해당 질문에만 간결하게 답한다.

예:
"우리 어머니 몇 살이야?"
→ "어머니는 78세입니다."

"어디 사신다고 했지?"
→ "성남시에 거주한다고 말씀하셨습니다."

단순 질문에 사용자가 묻지 않은 추천 결과,
서비스 목록, 기관 판단 내용을 반복해서 설명하지 않는다.

14. 추천 이유, 신청 방법, 대상 조건 등
정책에 관한 질문을 했을 때만 관련 추천 결과와
정책 정보를 자세히 설명한다.
"""

    response = client.responses.parse(
        model="gpt-5-nano",
        input=prompt,
        text_format=RecommendationFollowUpResult,
    )

    if response.output_parsed is None:
        raise ValueError("후속 상담 답변 생성에 실패했습니다.")

    return response.output_parsed