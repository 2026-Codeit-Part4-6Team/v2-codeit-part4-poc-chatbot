# 요구사항 명세서 v4

## 1. 문서 개요
- **목적**: 소상공인이 생성형 AI로 광고 콘텐츠(문구·이미지)를 손쉽게 제작하는 웹 서비스의 요구사항 정의.
- **범위**: 광고 콘텐츠 생성 챗봇을 메인으로 하고, 상권 분석은 공공데이터 기반 정량 컨설팅으로 정의.
- **핵심 변경(v2 대비)**:
    - (1) 네이버 트렌드 API → **NAVER API HUB로 이관 확정**(개발자센터 신규 발급 불가, 2026-07-31부)
    - (2) 경쟁사 리뷰 분석 → **[확장]으로 분리**(공식 API 부재, Selenium 크롤링은 약관·안정성 리스크)
    - (3) 이미지 생성 → **GCP L4 서버에서 자체 호스팅(self-hosted) SDXL + Triton 서빙**
      (로컬 PC 아님 — 개발·서빙 모두 GCP VM에서 수행, GPU 활용으로 평가 가점)
    - (4) 지오코딩 → **카카오 로컬 API 채택**(발급 간단, 무료 일 10만/월 300만)
    - (5) 상권 API 활용 필드 확장(업종 3단계 분류·좌표·행정동·totalCount → 파생 지표 산출)
- **용어**: 소상공인(사용자), 노드(파이프라인 기능 단위), 라우터(질의 분기 로직),
  크레딧(선불 충전형 유료 재화), 경쟁 밀도(반경 내 동일 소분류 업종 수 기반 지표),
  자체 호스팅(self-hosted, 외부 API가 아닌 우리 GCP 서버에서 직접 모델을 구동·서빙).

## 2. 시스템 개요
사용자는 로그인 후 광고 콘텐츠 생성 챗봇을 이용한다. 챗봇은
(a) 주소를 **카카오 지오코딩**으로 좌표 변환 →
(b) **소상공인시장진흥공단 상권 API**로 반경 내 업종 분포·경쟁 밀도(정량) 분석 →
(c) **네이버 데이터랩(NAVER API HUB) 검색어 트렌드**로 시의성 키워드 반영 →
(d) 플랫폼별 광고 문구+이미지(유료) 생성한다.(필요 시 문구(무료) 추가)
내부적으로 라우터가 질의를 Agentic-RAG / 문구생성 / 이미지생성 노드로 분기한다.

> ⚠️ 경쟁사 "리뷰" 정성 분석은 네이버가 리뷰 API를 제공하지 않아 MVP에서 제외.
> 리뷰 기반 분석은 [확장]에서 사전 수집(배치) 캐시 데이터로만 제한적으로 다룬다.
> 실시간 크롤링은 이용약관·안정성 리스크로 서비스 핵심 경로에 넣지 않는다.

## 3. 기능 요구사항

### [MVP] 필수 구현 (발표·시연 대상)
| ID | 기능 | 입력 | 출력 |
| --- | --- | --- | --- |
| FR-01 | 주소→좌표 지오코딩 | 주소 문자열 | lat, lng |
| FR-02 | 상권 정보 조회 | 좌표+반경(≤2000m) | 반경 내 매장 리스트(업종3단계·좌표·행정동 포함) |
| FR-03 | 상권 정량 분석 | FR-02 결과 | 경쟁밀도·동일업종수·최근접거리·업종다양성 |
| FR-04 | 업종 트렌드 조회 | 업종·키워드 | 검색어 트렌드 추이 |
| FR-05 | 플랫폼별 문구 생성 | 소재+플랫폼(인스타/블로그/현수막) | 플랫폼별 문구 3안 |
| FR-06 | 광고 이미지 생성(유료) | 문구+스타일 | 광고 이미지(SDXL) |
| FR-07 | 게시물 생성(유료) | 생성요청+플랜 | 유료:문구+이미지(필요 시 무료:문구 추가) |
| FR-08 | 대안 제시·재생성 | 최초 생성물 | 1안/2안 선택지 |
| FR-09 | 꼬리질문 정보 보완 | 최초 질문 | 반문 질문→반영 결과 |
| FR-10 | 회원가입·로그인 | 이메일·비밀번호·가게정보 | 세션 발급 |
| FR-11 | 크레딧 결제·차감 | 충전 요청 / 유료 생성 | 크레딧 잔액·차감 결과 |
| FR-12 | 라우터 분기 | 사용자 질의 | 적합 노드로 라우팅 |
| FR-13 | 품질 평가(개발용) | 생성물·참조데이터 | HitRate@k / MRR / LLM Judge |

### [확장] 시간 허락 시 (필요 시 진행)
| ID | 기능 | 비고 |
| --- | --- | --- |
| EX-01 | 경쟁사 리뷰 감성·차별점 분석 | 사전 수집 리뷰 캐시 →
  ① KcELECTRA 계열 감성분석 모델로 긍/부정·측면 분류(CPU) →
  ② LLM으로 부정 측면 기반 차별화 전략 요약. 실시간 크롤링 경로 금지 |
| EX-02 | 경쟁사 리뷰 정성 분석 | 네이버 플레이스 Selenium 크롤링. **약관·안정성 리스크로 사전 배치 수집 캐시만 사용**. 실시간 경로 금지 |
| EX-03 | 실시간 날씨·뉴스 반영 카피 | 기상청/뉴스 API. MVP는 트렌드만으로 시의성 확보 |
| EX-04 | 마케팅 전략 제안 | 상권 정량 분석→프로모션/타겟팅 전략 텍스트 |
| EX-05 | 컨설팅→콘텐츠 연계 | 전략 승인 시 문구 생성 자동 트리거 |
| EX-06 | 이미지 제품 보존 생성 | IP-Adapter/ControlNet으로 제품 사진 보존 광고 이미지(가이드 '이미지 만들기 3') |

## 4. 비기능 요구사항
- **성능**:
  - 텍스트 생성: OpenAI API(gpt 계열). 응답 목표 p95 < 15초.
  - 이미지 생성: **GCP VM(L4 GPU)에서 자체 호스팅 SDXL(Stable Diffusion XL) + Triton 서빙.**
    - 실행 위치: 개발·추론 모두 **GCP 서버**에서 수행(로컬 PC GPU 미사용).
      로컬은 편집만, 실행은 VSCode Remote-SSH로 서버에서.
    - 구현 순서(서버 내부에서): ① diffusers로 SDXL 직접 로드·품질/프롬프트 확보
      → ② ONNX/TensorRT 변환 → ③ Triton 서빙 + FastAPI↔Triton gRPC 연결.
      **①을 건너뛰고 Triton부터 붙이지 않는다.**(Triton은 품질 확보 후 서빙 최적화 단계)
    - 폴백: Triton 전환이 지연될 경우, ①의 diffusers 직접 서빙 상태로도 시연 가능하게 유지.
    - 모델 가중치는 GCP 디스크에 캐싱(재다운로드 방지, 디스크 100GB 한도 내 관리).
    - 이미지 응답은 base64 인라인 반환(파일경로/URL 아님).
    - 이미지 생성 목표 지연: 1장 기준 p95 < 20초(콜드스타트 제외).
- **배포/운영**: GitHub Actions 자동배포(main merge→빌드→VM pull&restart)만 허용.
  VM 직접 코드 수정 금지. SSH는 트러블슈팅 전용, 팀원 전원 개방.
  **GPU 컨테이너는 nvidia-container-toolkit로 GPU 접근 보장(--gpus all).**
- **보안**: 비밀번호 해시 저장(평문 금지), API 키는 .env(서버)·GitHub 금지,
  카카오/네이버/OpenAI 키 분리 관리, 결제정보 최소 보관.
- **사용성**: 비전문가용 클릭·대화 흐름. 로딩 상태·실패 메시지 노출.
  **이미지 생성처럼 수 초 이상 걸리는 작업은 진행 표시(스피너/예상 시간) 필수.**
- **확장성**: 노드 기반 구조로 신규 노드 추가 용이.
- **모니터링**: 구조화 로그 필수. GPU 사용량(nvidia-smi) 주기 확인. Prometheus/Grafana는 [확장].

## 5. 데이터 요구사항 (DB: SQLAlchemy, SQLite3)

### users
| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| id | INTEGER PK AUTOINCREMENT | 사용자 ID |
| username | TEXT UNIQUE NOT NULL | 사용자 이름 |
| email | TEXT UNIQUE | 로그인 아이디 |
| password_hash | TEXT NOT NULL | 비밀번호 해시(**구현 방식 팀 통일 필요**: 현행 POC=SHA-256+hmac / 권장=bcrypt) |
| business_name | TEXT | 가게명 |
| business_type | TEXT | 업종(상권·트렌드에 사용) |
| lat | REAL | 위도(상권 API용, 지오코딩 결과 저장) |
| lng | REAL | 경도 |
| address | TEXT | 원본 주소 |
| credits | INTEGER DEFAULT 0 | 보유 크레딧(유료 차감 대상) |
| is_admin | BOOLEAN DEFAULT FALSE | 관리자 여부 |
| created_at | DATETIME NOT NULL | 가입일시 |

### payments
| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| id | INTEGER PK AUTOINCREMENT | 결제 ID |
| user_id | INTEGER NOT NULL FK→users.id | 결제자 |
| amount | INTEGER NOT NULL | 결제 금액(원) |
| credits | INTEGER NOT NULL | 충전된 크레딧 수 |
| method | TEXT DEFAULT 'mock' | 결제수단(POC=mock) |
| status | TEXT DEFAULT 'paid' | pending/refunded/completed/failed |
| created_at | DATETIME NOT NULL | 결제 일시 |

### generations  (※ v1의 content/contents 명칭 혼용 → generations 통일)
| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| id | INTEGER PK AUTOINCREMENT | 생성물 ID |
| user_id | INTEGER NOT NULL FK→users.id | 요청자 |
| question | TEXT | 사용자 요청 |
| type | TEXT NOT NULL | 'copy+image(카피+이미지)'(필요 시 'copy(카피)'/ 추가) |
| platform | TEXT | instagram/blog/banner |
| copy_content | TEXT | 생성 문구 |
| image_path | TEXT | 생성 이미지 경로(유료) |
| image_b64 | TEXT nullable | 유료 이미지(**base64 인라인**, 파일경로/URL 아님) |
| plan | TEXT | free/paid |
| tokens_used | INTEGER DEFAULT 0 | 토큰 사용량 |
| created_at | DATETIME NOT NULL | 생성 일시 |

### market_cache (신규 — 상권 조회 결과 캐시)
| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| id | INTEGER PK AUTOINCREMENT | 캐시 ID |
| lat | REAL | 조회 중심 위도 |
| lng | REAL | 조회 중심 경도 |
| radius | INTEGER | 조회 반경(m) |
| result_json | TEXT | 상권 API 응답(JSON 직렬화) |
| created_at | DATETIME | 조회 일시(TTL 관리용) |

## 6. 인터페이스 요구사항
- **외부 API**
  - **카카오 로컬(지오코딩)**: `https://dapi.kakao.com/v2/local/search/address.json`
    (헤더 `Authorization: KakaoAK {REST_KEY}`, 무료 일 10만/월 300만, JSON/XML)
  - **소상공인시장진흥공단 상권정보** `storeListInRadius`
    (`http://apis.data.go.kr/B553077/api/open/sdsc2/storeListInRadius`,
     좌표 기반, 반경≤2000m, 30tps, 페이지≤1000, xml/json,
     활용 필드: indsLclsNm/indsMclsNm/indsSclsNm, lon/lat, adongNm, totalCount)
  - **네이버 데이터랩 검색어 트렌드 (NAVER API HUB)**
    (`https://naverapihub.apigw.ntruss.com`, 헤더 `X-NCP-APIGW-API-KEY-ID`/`X-NCP-APIGW-API-KEY`,
     ⚠️ 개발자센터(developers) 신규 발급 2026-07-31 종료 → **HUB로 발급**,
     현행 POC trend.py의 X-Naver-Client-* 헤더를 HUB 방식으로 수정 필요)
  - **OpenAI API**: 문구 생성·임베딩(gpt 계열, text-embedding-3-small)
- **내부 연동**: FastAPI ↔ Triton Inference Server(gRPC, 이미지 생성)
- **정적 데이터(참고 KB)**: 업종분류(2302) xlsx, 주요상권현황 csv → 업종코드 매핑·상권명 참조
- **UI**: 로그인, 메인 사이드바(플랜·채널·컨텍스트 체크박스), 생성 결과·대안·이미지 표시
````
````

## 참고

> "우리가 하고 싶은 것(리뷰 크롤링, 실시간 반영)과 안정적으로 되는 것(공식 API 정량 분석)을 구분했어요. **시연에서 확실히 되는 것을 MVP에, 리스크 있는 것을 확장에** 뒀습니다. 특히 네이버 트렌드는 HUB 이관이 강제라 선택지가 없고, 지오코딩은 카카오가 제일 편해서 정했어요. 이미지는 SDXL+Triton으로 가되, 품질부터 잡고 서빙 최적화를 나중에 붙이는 순서로."

**추가 논의 사항**: (1) NCP 계정 만들어서 트렌드 HUB 키 발급 담당자 지정, (2) 카카오 REST 키 발급, (3) `password_hash` 방식 최종 통일(SHA-256 유지 vs bcrypt 전환).

SDXL+Triton 구현 로드맵(diffusers 프로토타입 → ONNX 변환 → Triton 서빙)을 주차별 태스크로 쪼갠 표가 필요 시 AI 도구 활용 예정.