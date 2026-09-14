# 노인맞춤돌봄서비스 정책 데이터 (OnCare 개발용 구조화 값)
# 참고: 데이터명세 섹션 2(Master Policy), 3(Rule), 4(대상군), 5(세부서비스)

# [설계 노트] 현재는 정책 데이터를 Python dict(JSON 형태)로 구성함.
# 담당(B)의 기술 스택은 RAG+DB+Backend+UI이나, 예선 마감(9/18) 안에
# 핵심 파이프라인(RAG 검색 + Rule Engine + 추천)을 먼저 완성하는 것을 우선순위로 두고
# DB 연결은 이후 단계에서 진행할 예정.

# 데이터 구조는 섹션 9(권장 DB/JSON 구조)의 테이블 스키마를 그대로 반영해 설계했으므로,
# 추후 SQLite/PostgreSQL로 마이그레이션 시 이 dict 구조를 테이블로 옮기기만 하면 됨.
# (참고: 데이터명세 섹션 12 - "정책 데이터 일부(JSON/DB seed)" 형태 제출 허용)


MASTER_POLICY = {
    "policy_id": "CARE_NAT_001",
    "policy_name": "노인맞춤돌봄서비스",
    "agency": "보건복지부 노인정책과",
    "effective_year": 2026,
    "purpose": "일상생활 영위가 어려운 취약노인에게 적절한 돌봄서비스를 제공하여 안정적인 노후생활을 보장하고 기능·건강 유지 및 악화 예방",
    "cost": "무료",
    "application_place": "주민등록상 주소지 읍·면·동 행정복지센터",
    "official_assessment_required": True,  # 선정조사 및 지자체 결정 필요
    "active_status": "ACTIVE",
}

# 대상군 (Care Group) - child entity
CARE_GROUPS = [
    {
        "segment_id": "CARE_NAT_001_DISCHARGE",
        "name": "퇴원후돌봄군",
        "summary": "급성기병원 또는 요양병원 등 퇴원 후 일정기간 집중돌봄 필요",
        "service_scope": "월 44시간 이하 단기집중 서비스",
    },
    {
        "segment_id": "CARE_NAT_001_INTENSIVE",
        "name": "중점돌봄군",
        "summary": "거동불편 등 신체 기능제한으로 일상생활지원 필요가 높은 노인",
        "service_scope": "월 21시간 이상 40시간 미만 직접서비스 + 필요 시 연계",
    },
    {
        "segment_id": "CARE_NAT_001_GENERAL",
        "name": "일반돌봄군",
        "summary": "사회적 관계단절·일상생활 어려움으로 예방적 돌봄 필요",
        "service_scope": "월 16시간 미만 직접서비스 + 필요 시 연계, 주기적 가사지원 제한",
    },
    {
        "segment_id": "CARE_NAT_001_FOLLOWUP",
        "name": "사후관리대상",
        "summary": "종결자 중 사후관리가 필요한 사람",
        "service_scope": "정기 모니터링 및 자원연계",
    },
]

# 세부서비스 (Service) - child entity, RAG 검색키워드 포함
SERVICES = [
    {"service_id": "..._SAFETY", "name": "안전지원",
     "description": "전화·방문·AI/디지털 안부확인, 생활안전, 말벗, 정보제공",
     "rag_keywords": ["독거", "안부확인", "AI 안부", "생활안전", "말벗", "재난"]},
    {"service_id": "..._SOCIAL", "name": "사회참여지원",
     "description": "사회참여 활동, 자조모임 등",
     "rag_keywords": ["사회적 고립", "외로움", "사회관계", "여가", "참여"]},
    {"service_id": "..._EDU", "name": "생활교육지원",
     "description": "신체·정신영역 활동, 건강·우울·인지 관련 예방교육",
     "rag_keywords": ["건강교육", "정신건강", "우울예방", "인지", "생활교육"]},
    {"service_id": "..._DAILY", "name": "일상생활지원",
     "description": "이동활동지원, 가사활동지원",
     "rag_keywords": ["외출동행", "병원동행", "이동지원", "가사지원", "청소"]},
    {"service_id": "..._SPECIAL", "name": "특화지원",
     "description": "정서적 위험이 높은 취약노인 대상 사례관리·상담·프로그램·치료지원",
     "rag_keywords": ["우울", "고독사 위험", "정서위험", "상담", "인지저하 우려"]},
    {"service_id": "..._POSTDISCHARGE", "name": "퇴원환자 단기지원",
     "description": "재입원 예방과 일상회복을 위한 영양·가사·동행 등",
     "rag_keywords": ["퇴원", "회복", "영양", "가사", "병원동행"]},
    {"service_id": "..._LINKAGE", "name": "연계서비스",
     "description": "민간자원 등을 연계한 생활·주거·건강지원",
     "rag_keywords": ["생활지원", "주거지원", "건강지원", "지역자원", "기관연계"]},
]

# Eligibility / Exclusion Rule 데이터 (섹션 3, Rule Engine 조건검증용)
RULES = [
    {"rule_id": "R01", "field": "age", "criterion": "만 65세 이상",
     "treatment": "미만이면 LIKELY_NOT_MATCH", "official_required": False},
    {"rule_id": "R02", "field": "welfare_status", "criterion": "기초생활수급자·차상위층·기초연금수급자 중 해당",
     "treatment": "미확인이면 NEEDS_CHECK", "official_required": False},
    {"rule_id": "R03", "field": "care_needs", "criterion": "일상생활·안전·사회관계 등 돌봄 필요 상황",
     "treatment": "LLM 구조화, 단독 확정 금지", "official_required": True},
    {"rule_id": "R04", "field": "duplicate_services", "criterion": "장기요양보험 등 유사·중복사업 해당",
     "treatment": "해당 시 우선사업/예외 확인 (무조건 탈락 금지)", "official_required": "경우에 따라"},
    {"rule_id": "R05", "field": "residence", "criterion": "주민등록상 주소지",
     "treatment": "신청기관 안내용", "official_required": False},
    {"rule_id": "R06", "field": "official_assessment", "criterion": "신체·정신·사회 영역 선정조사 및 심의",
     "treatment": "OFFICIAL_ASSESSMENT_REQUIRED", "official_required": True},
]