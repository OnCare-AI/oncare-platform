# app/services/policy_recommendation.py
# RAG 검색 + Rule Engine 결과를 합쳐 최종 PolicyRecommendation을 만드는 모듈
# 참고: 데이터명세 섹션 10 (Rule Engine 출력 상태 - 예선 권장 흐름)

from pydantic import BaseModel

from app.models.user_situation import UserSituation
from app.services.rule_engine import evaluate as rule_evaluate, STATUS_LIKELY_NOT_MATCH, STATUS_NEEDS_CHECK
from app.services.rag_search import RagIndex

# 서버 시작 시 한 번만 RAG 인덱스를 만들어서 재사용 (매번 새로 임베딩하면 느림)
_rag_index = RagIndex()


class MatchedService(BaseModel):
    chunk_id: str
    name: str


class PolicyRecommendationResult(BaseModel):
    status: str
    reason: str
    matched_services: list[MatchedService]
    missing_fields: list[str]
    source_ids: list[str]
    institution_review_required: bool


def _build_query_text(situation: UserSituation) -> str:
    """UserSituation의 care_needs를 RAG 검색 질의문으로 변환."""
    if situation.care_needs:
        return " ".join(situation.care_needs)
    return "돌봄 서비스"  # care_needs가 비어있을 때의 기본 질의


def recommend(situation: UserSituation) -> PolicyRecommendationResult:
    """UserSituation을 받아 최종 PolicyRecommendation을 반환한다."""
    rule_result = rule_evaluate(situation)

    # 명백히 부적합/정보부족인 경우엔 RAG 검색을 건너뜀
    if rule_result["status"] in (STATUS_LIKELY_NOT_MATCH, STATUS_NEEDS_CHECK):
        return PolicyRecommendationResult(
            **rule_result,
            matched_services=[],
            source_ids=[],
        )

    query = _build_query_text(situation)
    top_chunks = _rag_index.search(query, top_k=3)

    matched_services = [
        MatchedService(chunk_id=c["chunk_id"], name=c["retrieval_text"].split(":")[0])
        for c in top_chunks if c["chunk_type"] == "SERVICES"
    ]
    source_ids = sorted({sid for c in top_chunks for sid in c["source_ids"]})

    return PolicyRecommendationResult(
        **rule_result,
        matched_services=matched_services,
        source_ids=source_ids,
    )