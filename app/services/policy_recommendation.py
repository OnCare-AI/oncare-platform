# app/services/policy_recommendation.py
# RAG 검색 + Rule Engine 결과를 합쳐 최종 PolicyRecommendation을 만드는 모듈
# 참고: 데이터명세 섹션 10 (Rule Engine 출력 상태 - 예선 권장 흐름)

from app.models.user_situation import UserSituation
from app.services.rule_engine import evaluate as rule_evaluate, STATUS_LIKELY_NOT_MATCH, STATUS_NEEDS_CHECK
from app.services.rag_search import RagIndex

# 서버 시작 시 한 번만 RAG 인덱스를 만들어서 재사용 (매번 새로 임베딩하면 느림)
_rag_index = RagIndex()


def _build_query_text(situation: UserSituation) -> str:
    """UserSituation의 care_needs를 RAG 검색 질의문으로 변환."""
    if situation.care_needs:
        return " ".join(situation.care_needs)
    return "돌봄 서비스"  # care_needs가 비어있을 때의 기본 질의


def recommend(situation: UserSituation) -> dict:
    """
    UserSituation을 받아 최종 PolicyRecommendation을 반환한다.
    반환값: {status, reason, matched_services, missing_fields, source_ids, institution_review_required}
    """
    rule_result = rule_evaluate(situation)

    # 명백히 부적합/정보부족인 경우엔 굳이 RAG 검색까지 할 필요 없음
    if rule_result["status"] in (STATUS_LIKELY_NOT_MATCH, STATUS_NEEDS_CHECK):
        return {
            **rule_result,
            "matched_services": [],
            "source_ids": [],
        }

    # 그 외(POTENTIAL_MATCH, OFFICIAL_ASSESSMENT_REQUIRED)는 RAG로 관련 서비스를 찾음
    query = _build_query_text(situation)
    top_chunks = _rag_index.search(query, top_k=3)

    matched_services = [
        {"chunk_id": c["chunk_id"], "name": c["retrieval_text"].split(":")[0]}
        for c in top_chunks if c["chunk_type"] == "SERVICES"
    ]

    # 검색된 chunk들의 출처를 중복 없이 모음
    source_ids = sorted({sid for c in top_chunks for sid in c["source_ids"]})

    return {
        **rule_result,
        "matched_services": matched_services,
        "source_ids": source_ids,
    }