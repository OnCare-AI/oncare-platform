from dotenv import load_dotenv
from openai import OpenAI

from app.models.user_situation import UserSituation


load_dotenv()

client = OpenAI()


SYSTEM_PROMPT = """
너는 OnCare 복지상담 서비스의 사용자 상황 구조화 AI다.

사용자의 자연어 상담 내용을 읽고 UserSituation 형식으로 구조화한다.

규칙:
1. 사용자가 명확하게 말한 정보만 채운다.
2. 알 수 없는 값은 추측하지 않는다.
3. 알 수 없는 Optional 값은 null로 둔다.
4. care_needs에는 사용자가 표현한 돌봄 필요사항을 간단한 문자열로 정리한다.
5. duplicate_services는 사용자가 현재 이용 중이라고 명시한 유사 돌봄서비스만 넣는다.
6. 중복서비스 이용 여부를 알 수 없다면 duplicate_service_unknown은 true로 둔다.
7. 긴급상황이라고 명확히 판단할 근거가 없으면 urgent는 false로 둔다.
8. 복지서비스 수급 가능 여부를 판단하지 않는다.
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