from pathlib import Path
from dotenv import load_dotenv

# 현재 파일(main.py) 기준으로 프로젝트 루트의 .env 파일 경로를 명확하게 지정
# (uvicorn --reload가 별도 프로세스를 띄우면서 자동 탐색이 실패하는 경우가 있어서 명시적으로 지정)
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI
from pydantic import BaseModel

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


app = FastAPI(
    title="OnCare API",
    description="AI 기반 성남형 복지연계 에이전트",
)

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)


class StartConsultationRequest(BaseModel):
    message: str


class ContinueConsultationRequest(BaseModel):
    situation: UserSituation
    message: str


class RecommendationRequest(BaseModel):
    situation: UserSituation


@app.get("/", include_in_schema=False)
def home():
    return FileResponse("app/static/index.html")


@app.get("/health")
def health():
    return {
        "service": "OnCare",
        "status": "running",
    }


@app.post(
    "/consultation/start",
    response_model=ConsultationResult,
)
def start(request: StartConsultationRequest):
    return start_consultation(request.message)


@app.post(
    "/consultation/continue",
    response_model=ConsultationResult,
)
def continue_chat(request: ContinueConsultationRequest):
    return continue_consultation(
        situation=request.situation,
        user_answer=request.message,
    )


@app.post(
    "/recommendations",
    response_model=PolicyRecommendationResult,
)
def get_recommendation(request: RecommendationRequest):
    return recommend(request.situation)