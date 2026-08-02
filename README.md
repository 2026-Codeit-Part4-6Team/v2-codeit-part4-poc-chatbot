# AdCopilot — 소상공인 광고 콘텐츠 생성 (파트4 고급 프로젝트 대비 POC)

LangGraph 기반 **Agentic-RAG** 파이프라인으로 소상공인의 광고 카피(무료)와
광고 이미지+카피(유료)를 생성하는 MVP. **1인 · 4일(7/30~8/3) 개발 범위**.

> DB는 `sqlite3` 표준 라이브러리만 사용(SQLAlchemy 미사용). 보안 노드는 POC 범위에서 제외.

## 팀 기능 매핑 (POC 반영)
| 담당 | 기능 | 구현 위치 |
| --- | --- | --- |
| 전민재 | 네이버 데이터랩 트렌드 조회 | `backend/nodes/trend.py` |
| 윤승준 | 경쟁사 리뷰 요약·차별점 / 채널별 리포맷 | `backend/nodes/context.py`, `channel_format.py` |
| 김재헌 | 체크박스 라우터 / 업종 벤치마크 RAG / 이미지·게시물(유료) / 로그인·결제 DB / 평가 | `routing.py`, `retrieval.py`, `image_gen.py`, `db.py`, `eval/` |
| 조희원 | 정보 충분성 판단→꼬리질문(반문) / 대안(배리언트) 제시 | `question_analysis.py`, `ranking.py` |

## 구조
```
adcopilot/
├── backend/
│   ├── db.py                 # sqlite3 CRUD (users/payments/generations)
│   ├── config.py / config.yaml
│   ├── llm.py                # gpt-5-mini 래퍼(+오프라인 목)
│   ├── retrieval.py          # 업종 벤치마크 RAG(코사인)
│   ├── nodes/                # 그래프 노드들
│   ├── graph/                # state + build_graph
│   ├── pipeline.py           # get_ai_response 진입점
│   ├── main.py               # FastAPI
│   └── data/                 # 벤치마크 KB / 경쟁사 리뷰 샘플
├── frontend/streamlit_app.py
├── eval/                     # HitRate@k / MRR / LLM Judge
└── scripts/seed.py           # demo 계정
```

## 실행
```bash
pip install -r requirements.txt
cp .env.example .env          # 키 입력(없어도 목 모드로 동작)

# 1) 백엔드
cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000
# (별 터미널) 데모 계정: python ../scripts/seed.py  → demo / demo123

# 2) 프론트
cd ../frontend && BACKEND_URL=http://localhost:8000 streamlit run streamlit_app.py
```

## 시연 시나리오
1. `demo/demo123` 로그인 → 사이드바에서 컨텍스트 소스 체크박스, 플랜/채널 선택
2. "강남역 카페 여름 신메뉴 인스타 문구 만들어줘" → 카피 3안 + 최고안 + 근거
3. 정보 부족 질문("홍보 좀 해줘") → **꼬리질문 반문** 확인
4. 크레딧 충전 → **유료(paid)** → 광고 이미지 생성 확인
5. 채널을 banner로 바꿔 **현수막 문구** 리포맷 확인
6. `python eval/evaluate.py` → HitRate@5 / MRR / LLM Judge

## 오프라인 모드
`OPENAI_API_KEY`/네이버 키가 없으면 자동으로 목 응답·mock 트렌드로 폴백하여
파이프라인 흐름 전체를 키 없이 검증할 수 있음(실 시연 시 키 입력).

## 실서비스 확장 슬롯(인터페이스 유지 교체 지점)
- `retrieval.py` → FAISS/Chroma
- `nodes/image_gen.py` → 팀 `backend_image_generator.py`(SDXL RealVisXL+IP-Adapter)
- `nodes/context.py` 경쟁사 → 상권정보 OpenAPI + 네이버지도 리뷰 API
- `eval/` → RAGAS(Context Recall/Precision, Faithfulness)
