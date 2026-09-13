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