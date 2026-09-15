from pathlib import Path

from dotenv import load_dotenv

# 현재 파일(main.py) 기준으로 프로젝트 루트의 .env 파일 경로를 명확하게 지정
# (uvicorn --reload가 별도 프로세스를 띄우면서 자동 탐색이 실패하는 경우가 있어서 명시적으로 지정)
load_dotenv(
    dotenv_path=Path(__file__).resolve().parent.parent / ".env"
)

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.models.user_situation import UserSituation

from app.services.consultation_service import (
    ConsultationResult,
    start_consultation,
    continue_consultation,
)

from app.services.policy_recommendation import (
    PolicyRecommendationResult,
    recommend,
)

# 판정 이후 추가 상담
from app.services.recommendation_follow_up import (
    RecommendationFollowUpResult,
    answer_recommendation_follow_up,
)


app = FastAPI(
    title="OnCare API",
    description="AI 기반 성남형 복지연계 에이전트",
)

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)


# -----------------------------
# Request Models
# -----------------------------


class StartConsultationRequest(BaseModel):
    message: str


class ContinueConsultationRequest(BaseModel):
    situation: UserSituation
    message: str
    unknown_fields: list[str] = Field(default_factory=list)


class RecommendationRequest(BaseModel):
    situation: UserSituation


class RecommendationFollowUpRequest(BaseModel):
    situation: UserSituation
    recommendation: PolicyRecommendationResult
    message: str
    conversation_history: list[dict[str, str]] = Field(
        default_factory=list
    )


# -----------------------------
# 기본 페이지
# -----------------------------


@app.get("/", include_in_schema=False)
def home():
    return FileResponse("app/static/index.html")


@app.get("/health")
def health():
    return {
        "service": "OnCare",
        "status": "running",
    }


# -----------------------------
# 상담 시작
# -----------------------------


@app.post(
    "/consultation/start",
    response_model=ConsultationResult,
)
def start(request: StartConsultationRequest):
    return start_consultation(request.message)


# -----------------------------
# 상담 추가질문
# -----------------------------


@app.post(
    "/consultation/continue",
    response_model=ConsultationResult,
)
def continue_chat(request: ContinueConsultationRequest):
    return continue_consultation(
        situation=request.situation,
        user_answer=request.message,
        unknown_fields=request.unknown_fields,
    )


# -----------------------------
# 정책 추천
# -----------------------------


@app.post(
    "/recommendations",
    response_model=PolicyRecommendationResult,
)
def get_recommendation(request: RecommendationRequest):
    return recommend(request.situation)


# -----------------------------
# 판정 이후 후속 상담
# -----------------------------


@app.post(
    "/consultation/follow-up",
    response_model=RecommendationFollowUpResult,
)
def recommendation_follow_up(
    request: RecommendationFollowUpRequest,
):
    return answer_recommendation_follow_up(
        situation=request.situation,
        recommendation=request.recommendation,
        user_message=request.message,
        conversation_history=request.conversation_history,
    )