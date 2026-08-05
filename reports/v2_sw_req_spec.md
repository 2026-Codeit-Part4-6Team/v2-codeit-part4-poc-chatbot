# 요구사항 명세서 v2

## 1. 문서 개요
- **목적**: 소상공인이 생성형 AI로 광고 콘텐츠(문구·이미지)를 손쉽게 제작하는 웹 서비스의 요구사항 정의.
- **범위**: 광고 콘텐츠 생성 챗봇을 메인으로 하고, 상권 분석은 "공공데이터 기반 컨설팅"으로 축소 정의.
- **핵심 변경(v1 대비)**: (1) 네이버 지도 리뷰 API 의존 제거 (2) 범위를 MVP/확장으로 2단계 분리
  (3) 코드·DB 스키마와 문서 일치 (4) 미확정 아키텍처는 '결정 필요'로 명시.
- **용어**: 소상공인(사용자), 노드(파이프라인 기능 단위), 라우터(질의 분기 로직), 크레딧(선불 충전형 유료 재화).

## 2. 시스템 개요
사용자는 로그인 후 광고 콘텐츠 생성 챗봇을 이용한다. 챗봇은 (a) 위치·업종 기반
**공공데이터(소상공인시장진흥공단 상권 API)**로 반경 내 경쟁 밀도·업종 분포를 분석하고,
(b) **네이버 데이터랩 검색어 트렌드 API**로 시의성 키워드를 반영해,
(c) 플랫폼별 광고 문구(무료)와 문구+이미지(유료)를 생성한다.
내부적으로 라우터가 질의를 Agentic-RAG / 문구생성 / 이미지생성 노드로 분기한다.

> ⚠️ v1의 "네이버 지도 리뷰 분석"은 공식 API 부재로 제거. 경쟁사 분석은 상권 API의
> **정량 데이터(업종별 매장 수·밀도)**로 대체하고, 리뷰 기반 정성 분석은 [확장]으로 분리.

## 3. 기능 요구사항

### [MVP] 반드시 구현 (발표·시연 대상)
| ID | 기능 | 입력 | 출력 | 담당 |
| --- | --- | --- | --- | --- |
| FR-01 | 상권 정보 조회 | 좌표(lat,lng)+반경(≤2000m) | 반경 내 업종별 매장 리스트·수 | 윤승준 |
| FR-01a | 주소→좌표 변환(지오코딩) | 주소 문자열 | lat, lng | 윤승준 |
| FR-02 | 상권 밀도·경쟁 분석 | FR-01 결과 | 업종 밀도·경쟁강도 요약 | 윤승준 |
| FR-03 | 업종 트렌드 조회 | 업종·키워드 | 검색어 트렌드 추이 | 전민재 |
| FR-04 | 플랫폼별 문구 생성 | 소재+플랫폼(인스타/블로그/현수막) | 플랫폼별 문구 3안 | 전민재 |
| FR-05 | 게시물 생성(유·무료) | 생성요청+플랜 | 무료:문구 / 유료:문구+이미지 | 김재헌 |
| FR-06 | 대안 제시·재생성 | 최초 생성물 | 1안/2안 선택지 | 조희원 |
| FR-07 | 꼬리질문 정보 보완 | 최초 질문 | 반문 질문→반영 결과 | 조희원 |
| FR-08 | 회원가입·로그인 | 이메일·비밀번호·가게정보 | 세션 발급 | 김재헌 |
| FR-09 | 크레딧 결제·차감 | 충전 요청 / 유료 생성 | 크레딧 잔액·차감 결과 | 김재헌 |
| FR-10 | 라우터 분기 | 사용자 질의 | 적합 노드로 라우팅 | 김재헌 |
| FR-11 | 품질 평가(개발용) | 생성물·참조데이터 | HitRate@k / MRR / LLM Judge | 김재헌 |

### [확장] 시간 허락 시 (3~4주차, 필요 시 진행)
| ID | 기능 | 비고 |
| --- | --- | --- |
| EX-01 | 경쟁사 리뷰 정성 분석 | 네이버 플레이스 크롤링(셀레니움). 약관·안정성 리스크로 확장 분리 |
| EX-02 | 실시간 날씨·뉴스 반영 카피 | 기상청/뉴스 API. MVP는 트렌드만으로 시의성 확보 |
| EX-03 | 마케팅 전략 제안 | 상권 분석→프로모션/타겟팅 전략 텍스트 |
| EX-04 | 컨설팅→콘텐츠 연계 | 전략 승인 시 문구 생성 자동 트리거 |

## 4. 비기능 요구사항
- **성능**:
  - 텍스트 생성: OpenAI API(gpt 계열). 응답 목표 p95 < 15초.
  - 이미지 생성: **[결정 필요]** ①GPT-Image API(서빙 불필요) vs ②로컬 SDXL+Triton(GPU 활용, 평가가점).
    → 2주차 스탠드업에서 확정. Triton/ONNX는 ②를 택할 때만 적용.
- **배포/운영**: GitHub Actions 자동배포(main merge→빌드→VM pull&restart)만 허용.
  VM 직접 코드 수정 금지. SSH는 트러블슈팅 전용, 팀원 전원 개방.
- **보안**: 비밀번호 해시 저장(평문 금지), API 키는 .env(서버)·GitHub 금지, 결제정보 최소 보관.
- **사용성**: 비전문가용 클릭·대화 흐름. 로딩 상태·실패 메시지 노출.
- **확장성**: 노드 기반 구조로 신규 노드 추가 용이.
- **모니터링**: 구조화 로그 필수. Prometheus/Grafana는 [확장].

## 5. 데이터 요구사항 (DB: SQLite3)

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
| type | TEXT DEFAULT 'copy(카피)' | 'copy(카피)'/'copy+image(카피+이미지)' |
| platform | TEXT | instagram/blog/banner |
| copy_content | TEXT | 생성 문구 |
| image_path | TEXT | 생성 이미지 경로(유료) |
| image_b64 | TEXT nullable | 유료 이미지(**base64 인라인**, 파일경로/URL 아님) |
| plan | TEXT | free/paid |
| tokens_used | INTEGER DEFAULT 0 | 토큰 사용량 |
| created_at | DATETIME NOT NULL | 생성 일시 |

## 6. 인터페이스 요구사항
- **외부 API**
  - 소상공인시장진흥공단 상권정보 `storeListInRadius`
    (REST, `apis.data.go.kr/B553077/...`, 좌표 기반, 반경≤2000m, 30tps, 페이지≤1000, xml/json)
  - 주소→좌표 지오코딩 API (예: 공공데이터/네이버/카카오 중 [결정 필요])
  - 네이버 데이터랩 검색어 트렌드
    (**인증 방식 팀 통일**: 현행 POC=developers `X-Naver-Client-Id/Secret` / NCP=`X-NCP-APIGW-*`)
- **내부 연동**: FastAPI ↔ 이미지 생성(로컬 택1 시 Triton gRPC)
- **UI**: 로그인, 메인 사이드바(플랜·채널·컨텍스트 체크박스), 생성 결과·대안·이미지 표시