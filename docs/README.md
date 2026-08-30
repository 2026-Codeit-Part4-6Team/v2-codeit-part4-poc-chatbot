<div align="center">

# 매출부스터 (Sales Booster)

### 상권 데이터로 전략을, 전략으로 광고를

**근거 기반 전략 수립과 안전한 광고 생성을 연결한 소상공인 마케팅 AI 플랫폼**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2-1C3C3C?logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)

**코드잇 스프린트 AI 엔지니어 10기 · 파트4 고급 프로젝트 · 6팀**

</div>

---

## 🎬 라이브 시연 영상

<div align="center">

[![매출부스터 시연 영상](assets/thumbnail.png)](https://www.youtube.com/watch?v=N4SLRAgrLik)

**▶️ 이미지를 클릭하면 유튜브로 이동합니다**

</div>

---

## 목차

1. [프로젝트 개요](#1--프로젝트-개요)
2. [주요 기능](#2--주요-기능)
3. [시스템 아키텍처](#3--시스템-아키텍처)
4. [설치 및 실행 방법](#4--설치-및-실행-방법)
5. [프로젝트 구조](#5--프로젝트-구조)
6. [성능 측정 결과](#6--성능-측정-결과)
7. [팀 소개](#7--팀-소개)
8. [타임라인](#8--타임라인)
9. [산출물](#9--산출물)
10. [기술 스택 및 라이선스](#10--기술-스택-및-라이선스)

---

## 1. 📌 프로젝트 개요

### 배경

소상공인 사장님의 고민은 세 가지입니다.

| 고민 | 현실 |
| --- | --- |
| **무엇을 팔아야 할지 모른다** | 상권 데이터를 볼 줄도, 볼 시간도 없다 |
| **어떻게 알려야 할지 모른다** | 광고 대행사를 쓸 예산이 없다 |
| **광고가 법에 걸리는지 모른다** | 표시광고법을 아는 사장님은 드물다 |

직접 만든 광고 문구가 이렇게 나오는 경우가 있습니다.

> "우리 동네 **최고**의 카페, 이 **커피 한 잔이 피로를 풀어드립니다**"

두 군데가 법에 걸립니다. `"최고"`는 표시광고법 시행령 제3조 제1항의 객관적 근거 없는 절대적 표현, `"피로를 풀어드립니다"`는 식품표시광고법 제8조 제1항 제1호의 질병 예방·치료 효능 표현입니다.

**문제는 사장님이 이 사실을 모른다는 것입니다.** 그대로 인쇄되어 가게 앞에 걸립니다.

### 목표

- 상권·트렌드 데이터를 근거로 **무엇을 팔지** 제안한다
- 그 전략을 이어받아 **광고 문구와 이미지**를 만든다
- 만든 결과가 **법에 걸리지 않는지 자동으로 검증**하고, 걸리면 **대안 문구를 제시**한다

### 기대 효과

| 항목 | 내용 |
| --- | --- |
| **의사결정 근거 확보** | 감이 아니라 반경 내 동일 업종 수·검색 추이로 판단 |
| **제작 시간 단축** | 문구 3안 + 채널별 이미지를 한 번의 요청으로 |
| **법적 위험 감소** | 위반 문구를 차단하고 바로 쓸 수 있는 대안을 제시 |

---

## 2. 🚀 주요 기능

### 분석이 — 컨설턴트 챗봇

상권과 트렌드를 근거로 실행 가능한 전략을 제안합니다.

- 질문을 재작성하고 검색 키워드를 추출
- **상권·트렌드·추천질문·계절성을 4-way 병렬 조회**
- 요약 + 실행안 1~3개 + **근거(reasons)** 를 함께 제시
- 이어서 물어볼 만한 **추천 질문 3개** 자동 생성

### 카피니 — 기본 챗봇

전략이나 요청을 받아 광고 문구와 이미지를 만듭니다.

- 톤이 다른 **광고 문구 3안 동시 생성** → LLM Judge 랭킹
- **규제 검증을 이미지 생성 앞에 배치** — 위반 문구로 이미지를 만들지 않는다
- Instagram(정사각) / X-배너(세로형 상하단 합성) 채널별 대응

### 공용 검증 계층

두 챗봇이 **같은 검증 함수를 공유**합니다.

| 함수 | 검사 대상 | 연결 |
| --- | --- | --- |
| `check_input` | 사용자 질문 | 두 챗봇 |
| `check_regulation` | 생성된 카피 | 기본 챗봇 |
| `check_output` | 최종 응답 | 두 챗봇 |
| `self_check` | 응답 근거·완결성 | 두 챗봇 |

**차단만 하지 않습니다.** `"최고의 카페"`가 걸리면 법에 맞는 대안 문구를 만들어 돌려주고, **그 대안을 다시 한 번 검사**합니다.

### 전략 → 광고 연계

컨설턴트 결과 화면의 **[이 전략으로 광고 만들기]** 버튼을 누르면, 서비스가 저장된 전략을 조회·재검증해 기본 챗봇에 넘깁니다. **두 챗봇이 직접 통신하지 않습니다.**

---

## 3. 🏗 시스템 아키텍처

![시스템 아키텍처](images/pipeline_overview.png)

### `check_regulation` — 2단 구조

```
카피 입력
   ├─[1단] 키워드 스크리닝 ── 명백한 위반은 LLM 호출 0회로 즉시 차단
   │         └ 애매하면 ↓
   └─[2단] 벡터 검색(top-k=3) → LLM 판정(temperature 0)
             └ 검색된 조문만 근거로 사용 → 조문을 지어내지 않는다
```

**LLM 출력을 그대로 믿지 않는 3중 안전장치**

1. 조문 번호(`law`)는 LLM 값을 버리고 **KB에서 직접 복사** — 실측 24건 중 3건이 불일치
2. `block` 정규화 — 불법 품목 근거가 있을 때만 차단으로 인정
3. 생성된 대안을 **재검사** — 또 걸리면 폐기

---

## 4. ⚙️ 설치 및 실행 방법

### 1) 사전 요구사항

| 항목 | 버전 |
| --- | --- |
| Python | 3.11 (3.12 미만) |
| Node.js | 20 이상 |
| Docker / Docker Compose | 최신 |
| [uv](https://docs.astral.sh/uv/) | 0.11.32 |

### 2) 저장소 클론 및 의존성 설치

```bash
git clone https://github.com/2026-Codeit-Part4-6Team/codeit-part4-6team-project.git
cd codeit-part4-6team-project

uv sync --locked --all-groups
```

### 3) 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 를 열어 아래 값을 채웁니다. **실제 키는 커밋하지 않습니다.**

```bash
# ── 실행 환경 ──────────────────────────────
APP_ENV=demo                      # development | test | demo | production
CHATBOT_MODE=actual               # mock | actual  ← 실제 모델을 쓰려면 actual

# ── 모델 ──────────────────────────────────
OPENAI_API_KEY=                   # 필수
OPENAI_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.3

# ── 외부 데이터 API ────────────────────────
MARKET_API_KEY=                   # 소상공인시장진흥공단 상권정보 (디코딩 키)
NAVER_CLIENT_ID=                  # 네이버 검색어 트렌드
NAVER_CLIENT_SECRET=
NAVER_MAPS_API_KEY_ID=            # 네이버 지도 (회원가입 지오코딩)
NAVER_MAPS_API_KEY=

# ── 검증 계층 ──────────────────────────────
VALIDATION_RAG_ENABLED=1
VALIDATION_TOP_K=3
VALIDATION_REQUIRE_LEGAL_KB=1

# ── 요금 정책 ──────────────────────────────
DAILY_FREE_LIMIT=10               # 일일 무료 생성 횟수
BASIC_CREDIT_COST=50              # 광고 생성 1회
CONSULTANT_CREDIT_COST=10         # 컨설팅 1회
```

### 4) 지식베이스·인덱스 빌드

법령 KB와 벡터 인덱스는 저장소에 커밋하지 않습니다. **최초 1회 빌드가 필요합니다.**

```bash
# 법령 KB (36청크) 생성
uv run python -m validation.scripts.build_legal_kb

# 벡터 인덱스 생성 (text-embedding-3-small)
uv run python -m validation.scripts.build_legal_index

# 업종 벤치마크 인덱스 (기본 챗봇용)
uv run python -m models.basic.scripts.build_benchmark_index
```

### 5) 실행

```bash
docker compose up --build
```

| 서비스 | 주소 |
| --- | --- |
| 프론트엔드 | http://localhost:8501 |
| 백엔드 API | http://localhost:18000 |
| API 문서 | http://localhost:18000/docs |

### 6) 시연용 계정 생성 (선택)

```bash
DEMO_ACCOUNTS_ENABLED=true \
DEMO_ACCOUNT_PASSWORD=<로컬에서만 입력> \
docker compose run --rm backend python -m backend.demo_seed

# 계정과 이력을 초기화하고 다시 만들려면
docker compose run --rm backend python -m backend.demo_seed --reset
```

### 7) 테스트 및 평가 실행

```bash
# 전체 테스트
uv run --locked --all-groups pytest

# 린트
uv run --locked --group dev ruff check .

# 검증 함수 평가 (골든 67문항)
uv run python -m validation.eval.eval_refusal --full

# 기본 챗봇 평가
uv run python -m models.basic.eval.eval_generation \
    --dataset shared_data/golden_dataset.json --area basic

# 컨설턴트 평가 (60문항)
uv run python -m models.consult.eval.eval_strategy --full

# 회차 간 비교 (조건이 다르면 비교를 거부한다)
uv run python -m models.shared.eval.compare_reports <before.json> <after.json>
```

> ⚠️ 평가 실행은 실제 LLM API를 호출합니다. 전체 실행 전 팀 예산을 확인하세요.

---

## 5. 📂 프로젝트 구조

```
codeit-part4-6team-project/
├── backend/                    # FastAPI — 인증 · 생성 · 결제 · 이력
│   ├── routers/                #   HTTP 엔드포인트
│   ├── services/               #   생성 유스케이스 · 크레딧 차감/롤백
│   ├── clients/                #   챗봇 클라이언트 (mock / actual)
│   ├── schemas.py              #   ★ 서비스 ↔ 모델 계약 (ModelRequest/ModelResult)
│   └── demo_seed.py            #   시연용 계정 seed
│
├── frontend/                   # React 18 + Vite — 화면 8종
│   └── src/
│       ├── features/generation/#   생성 흐름 (Estimate → 동의 → 대기 → 결과 → 승인)
│       ├── components/         #   대시보드 · 마이페이지 · 설정
│       └── contract.ts         #   ★ 프론트 ↔ 서비스 payload 계약
│
├── models/
│   ├── basic/                  # 카피니 — LangGraph 15노드
│   │   ├── graph/              #   상태 정의 · 그래프 조립
│   │   ├── nodes/              #   카피 생성 · 랭킹 · 규제 · 이미지 · 검수
│   │   └── eval/               #   생성·이미지·검색 평가기
│   ├── consult/                # 분석이 — LangGraph 9노드
│   │   ├── nodes/              #   질문분석 · 상권 · 트렌드 · 계절성 · 전략
│   │   └── eval/               #   전략 평가기 (60문항)
│   └── shared/                 # 두 챗봇 공용 (LLM 호출 · 계절성 · 평가 유틸)
│
├── validation/                 # ★ 공용 검증 계층 — 두 챗봇이 import
│   ├── regulation.py           #   check_regulation (1단 키워드 + 2단 RAG)
│   ├── security.py             #   check_input · check_output
│   ├── self_check.py           #   self_check
│   ├── legal_retriever.py      #   법령 KB 벡터 검색
│   └── eval/                   #   3계층 지표 계산기
│
├── cache/                      # 상권·트렌드 Cache-Aside (TTL 7일)
├── shared_data/                # 골든 데이터셋 · 법령 KB · 업종코드 맵
├── tests/                      # 서비스 계층 테스트
├── docs/                       # 설계 문서 · 계약서 · 보고서 · E2E 결과서
├── compose.yaml                # 로컬 개발
├── compose.deploy.yaml         # GCP 배포
└── scripts/deploy.sh           # 배포 스크립트
```

---

## 6. 📊 성능 측정 결과

### 검증 계층 — 골든 데이터셋 67문항

| 지표 | 목표 | 결과 | 판정 |
| --- | --- | --- | --- |
| 위반 차단률 | 100% | **100%** | ✅ |
| 과잉 차단률 | 10% 이하 | **0%** | ✅ |
| 대안 제시율 | 100% | **100%** | ✅ |
| 대안 유효성 (재검사 통과) | 95% 이상 | **100%** | ✅ |
| 표현 불변성 | 95% 이상 | **98.8%** | ✅ |
| RAGAS 종합 | 0.70 이상 | 0.6545 | ❌ |

> **RAGAS 미달은 트레이드오프의 결과입니다.** `context_recall` 1.000, `faithfulness` 1.000인데 `context_precision` 0.3871이 종합을 끌어내렸습니다. top-k=3 고정 구조에서 정답 조문이 1개인 문항의 precision 상한은 0.333입니다. 동적 top-k로 바꾸면 precision은 오르지만 **과잉 차단이 8.3% → 25%로 악화**되어 채택하지 않았습니다.

### 컨설턴트 챗봇 — 골든 60문항

| 지표 | 결과 |
| --- | --- |
| 실패율 | **0%** (0/60) |
| 계약 준수율 | **100%** (60/60) |
| 트렌드 경로 일치율 | **100%** (60/60) |
| 허용되지 않은 숫자 사용률 | **0%** (0/60) |
| LLM Judge 평균 | 4.325 / 5.0 |
| 응답시간 P50 / P95 | 5.20초 / 6.97초 |
| I/O 구간 응답시간 | 2.87초 → **1.64초** (4-way 병렬화, 42.8% 감소) |

### 기본 챗봇 — 프롬프트 18라운드

| 지표 | Baseline | 최종 채택 | 변화 |
| --- | --- | --- | --- |
| LLM Judge 평균 | 4.66 | **4.72** | +0.06 |
| 구체성 | 3.86 | **4.07** | +0.21 |
| X-배너 가독성 | 4.13 | **4.60** | +0.47 |

> **7차 프롬프트는 롤백했습니다.** 금지어를 늘릴수록 카피가 밋밋해졌고, 위반은 줄지 않는데 구체성만 떨어졌습니다. 방어는 프롬프트가 아니라 **사후 검증**에 맡기기로 했습니다.

### E2E 테스트 — 43 시나리오 · 2회 실행

| 회차 | 전체 통과율 | P0 통과율 |
| --- | --- | --- |
| 1차 (2026-08-26) | 69.8% (30/43) | 72.4% (21/29) |
| 2차 (2026-08-28) | **76.7%** (33/43) | **82.8%** (24/29) |

---

## 7. 👥 팀 소개

<div align="center">

| 역할 | 이름 | 담당 |
| :---: | :---: | --- |
| **PM · 검증** | **전민재** | 검증 함수 4종 · 법령 RAG · 골든 데이터셋 · 일정·예산 조율 |
| **기본 챗봇** | **조희원** | 카피니 파이프라인 · 프롬프트 튜닝 · 이미지 생성 |
| **컨설턴트 챗봇** | **김재헌** | 분석이 파이프라인 · 상권·트렌드 연동 · 전략 평가 |
| **서비스 · 인프라** | **윤승준** | React · FastAPI · DB · 크레딧 정책 · CI/CD · 배포 |

</div>

### 협업 방식

- **계약 우선** — 인터페이스(`backend/schemas.py`·`contract.ts`)를 먼저 고정하고 Mock으로 병렬 개발
- **의사결정 로그** — 판단과 근거를 `docs/decisions.md` 에 613건 기록
- **PR 리뷰** — 전 PR 리뷰 필수, 머지 순서와 리베이스를 로그로 관리

---

## 8. 📅 타임라인

| 기간 | 마일스톤 | 주요 산출물 |
| --- | --- | --- |
| D1 | 설계·계약 확정 | SDP 4종 · 인터페이스 계약 · Mock 응답 형식 |
| D2~D3 | 데이터 계층 | 상권·트렌드 API 연동 · Cache-Aside · 법령 KB |
| D4~D6 | 파이프라인 구현 | LangGraph 그래프 · 검증 함수 4종 · 화면 8종 |
| D7 | 실제 모델 연동 | Mock → Actual 교체 |
| D8~D10 | 평가·튜닝 | 골든 데이터셋 측정 · 프롬프트 18라운드 · UI 개선 |
| 최종 | 검증·배포 | E2E 2회차 · GCP 배포 · 발표 |

---

## 9. 📎 산출물

| 문서 | 내용 |
| --- | --- |
| [팀 최종 보고서](docs/reports/팀_최종_프로젝트_보고서.md) | 전체 설계·측정·한계 (7절 구성) |
| [검증 함수 보고서](docs/reports/validation_최종_보고서.md) | 검증 4종 설계·구현·3계층 평가 |
| [기본 챗봇 보고서](docs/reports/Basic_Model_최종보고서_v2.md) | 카피니 파이프라인·프롬프트 튜닝 |
| [컨설턴트 보고서](docs/reports/컨설턴트_챗봇_최종_보고서.md) | 분석이 파이프라인·60문항 측정 |
| [서비스 개발 보고서](docs/reports/서비스_개발_최종보고서.md) | 서비스·인프라·배포 |
| [검증 함수 계약서](docs/validation_contract.md) | 4종 반환 계약·챗봇별 연결 |
| [골든 데이터셋 규격](docs/golden_dataset.md) | 문항 설계·평가 실행 규칙 |
| [E2E 테스트 결과서](docs/e2e_reports/) | 43 시나리오 · 2회차 실행 결과 |
| [의사결정 로그](docs/decisions.md) | 판단과 근거 613건 |

---

## 10. 🛠 기술 스택 및 라이선스

### 기술 스택

| 구분 | 기술 |
| --- | --- |
| **Frontend** | React 18 · TypeScript · Vite · Vitest |
| **Backend** | FastAPI · SQLAlchemy 2.0 · Pydantic · pytest |
| **AI / ML** | LangGraph · OpenAI API · FAISS · Transformers (CLIP) |
| **Database** | SQLite |
| **Infra** | Docker Compose · GitHub Actions · GCP Compute Engine |
| **Tooling** | uv · ruff |

### 사용 모델

| 용도 | 모델 |
| --- | --- |
| 카피·전략 생성 | `gpt-4o-mini` (temperature 0.3) |
| 법률 규제 판정 | `gpt-5.4-mini` (temperature 0) |
| 임베딩 | `text-embedding-3-small` (1536차원) |
| 이미지 생성 | `gpt-image-2` |
| 이미지-텍스트 정합도 | `openai/clip-vit-base-patch32` |

### 외부 데이터

| 출처 | 용도 |
| --- | --- |
| [소상공인시장진흥공단 상권정보](https://www.data.go.kr/) | 반경 내 상가업소 · 업종코드 기반 판정 |
| [네이버 검색어 트렌드](https://developers.naver.com/) | 검색 추이 · 연관 검색어 |
| [네이버 지도](https://www.ncloud.com/product/applicationService/maps) | 회원가입 주소 지오코딩 |
| 표시광고법 · 식품표시광고법 | 법령 KB 36청크 |

### 알려진 한계

| 항목 | 내용 |
| --- | --- |
| **이미지 내 텍스트 미검증** | `check_regulation`은 카피 문자열만 본다. 이미지에 박힌 문구는 검증 범위 밖 — OCR 기반 검증이 후속 과제 |
| **판정 재현성** | `temperature=0`이 완전한 재현성을 보장하지 않는다. 5회 반복 중 1문항에서 판정이 갈림 |
| **KB 커버리지** | 도달 가능한 34조문에 대해 100%. 2개 조문은 트리거 우선순위가 겹쳐 구조적으로 검색 1위가 되지 않음 |
| **X-배너 비율** | 이미지 모델 최대 1.5:1 제약으로 1:3 배너를 두 장 합성으로 우회 |

---

<div align="center">

**코드잇 스프린트 AI 엔지니어 10기 · 파트4 6팀**

이 저장소는 교육 과정의 팀 프로젝트 산출물입니다.

</div>
