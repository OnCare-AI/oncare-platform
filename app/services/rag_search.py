# 정책 데이터를 RAG용 chunk로 쪼개고, 사용자 상황과 의미적으로 유사한 chunk를 찾아주는 모듈
# 참고: 데이터명세 섹션 8 (RAG 적재 구조)
# 임베딩은 OpenAI API(유료) 대신, 로컬에서 무료로 실행되는 한국어 임베딩 모델을 사용

import numpy as np
from sentence_transformers import SentenceTransformer

from app.data.policy_data import MASTER_POLICY, CARE_GROUPS, SERVICES

# 한국어 문장 임베딩에 널리 쓰이는 무료 오픈소스 모델
# 최초 1회만 자동으로 다운로드되고(수백 MB), 그 이후엔 로컬에 저장된 걸 사용 (비용 없음)
EMBEDDING_MODEL_NAME = "jhgan/ko-sroberta-multitask"
_model = SentenceTransformer(EMBEDDING_MODEL_NAME)


def build_chunks() -> list[dict]:
    """policy_data.py의 원본 데이터를 chunk_type별 텍스트 목록으로 변환한다."""
    chunks = []

    chunks.append({
        "chunk_id": "POLICY_SUMMARY_001",
        "chunk_type": "POLICY_SUMMARY",
        "retrieval_text": (
            f"{MASTER_POLICY['policy_name']}: {MASTER_POLICY['purpose']} "
            f"소관: {MASTER_POLICY['agency']}. 비용: {MASTER_POLICY['cost']}. "
            f"신청장소: {MASTER_POLICY['application_place']}."
        ),
        "source_ids": ["정1", "하4"],
    })

    for group in CARE_GROUPS:
        chunks.append({
            "chunk_id": f"CARE_GROUP_{group['segment_id']}",
            "chunk_type": "CARE_GROUP",
            "retrieval_text": f"{group['name']}: {group['summary']} ({group['service_scope']})",
            "source_ids": ["정2", "하4"],
        })

    for service in SERVICES:
        keywords = ", ".join(service["rag_keywords"])
        chunks.append({
            "chunk_id": f"SERVICE_{service['service_id']}",
            "chunk_type": "SERVICES",
            "retrieval_text": f"{service['name']}: {service['description']} (관련 키워드: {keywords})",
            "source_ids": ["정2", "하4"],
        })

    return chunks


def embed_text(text: str) -> np.ndarray:
    """텍스트를 무료 로컬 모델로 임베딩 벡터로 변환 (API 호출/비용 없음)."""
    return _model.encode(text)


class RagIndex:
    """chunk들을 미리 임베딩해두고, 질의와 유사한 chunk를 찾아주는 인메모리 검색기."""

    def __init__(self):
        self.chunks = build_chunks()
        texts = [c["retrieval_text"] for c in self.chunks]
        # 여러 문장을 한 번에 넣으면 하나씩 넣는 것보다 훨씬 빠름
        self.embeddings = _model.encode(texts)

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """질의(query)와 코사인 유사도가 가장 높은 상위 top_k개 chunk를 반환."""
        query_vec = embed_text(query)

        similarities = self.embeddings @ query_vec / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_vec)
        )

        top_indices = np.argsort(similarities)[::-1][:top_k]
        results = []
        for idx in top_indices:
            chunk = self.chunks[idx].copy()
            chunk["score"] = float(similarities[idx])
            results.append(chunk)
        return results