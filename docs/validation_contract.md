# 검증 함수 계약서 (Validation Contract) v1.0

> **작성**: 전민재 PM · **작성일**: 2026-08-12
> **파일 위치**: `docs/validation_contract.md` (단일 소스)
> **구현 위치**: `validation/` (전민재 PM 관리 — 두 챗봇 담당자는 **import만**)
> **연관 문서**: `docs/golden_dataset.md` · `docs/decisions.md` · API Contract v0.3

---

## 1. 이 문서를 왜 만드는가

### 1.1 실제로 있었던 일

2026-08-12, 검증 함수 스텁에 이런 코드가 있었다.

```python
return {"action": "pass"/"warn"/"block", ...}   # ← 문자열 나눗셈
```

**`import`는 통과하고 호출하는 순간 `TypeError`로 터졌다.** 명세표의 표기(`허용값: pass / warn / block`)를 코드에 그대로 옮긴 실수였다.

발견자는 검증 함수를 **쓰는 쪽**(컨설턴트 담당)이었다. 만드는 쪽은 몰랐고, 쓰는 쪽이 연결하다 알았다.

> **교훈**: 함수 시그니처만 합의하면 부족하다.
> **반환값의 의미·처리 규칙·실패 시 동작**까지 문서로 못 박아야 한다. 그것이 이 계약서다.

### 1.2 이 계약서가 답하는 질문 5가지

```
① 함수 4종은 무엇을 받고 무엇을 돌려주는가
② action 값을 받으면 노드는 무엇을 해야 하는가       ← 가장 중요
③ 어떤 판정이 서비스까지 도달하는가
④ 판정이 크레딧 차감·롤백에 어떻게 연결되는가
⑤ 스텁이 실구현으로 바뀔 때 내 코드를 고쳐야 하는가  ← 답: 아니오
```

---

## 2. 책임 경계

| 구분 | 담당 | 내용 |
| --- | --- | --- |
| **함수 구현** | **전민재 PM** | `validation/` 4종 판정 로직 · 키워드 사전 · 규제 RAG |
| **노드 래핑** | 각 챗봇 담당 | 함수를 LangGraph 노드로 감싸 그래프에 연결 |
| **판정 결과 전달** | 각 챗봇 담당 | 서비스 API 응답 형식으로 변환 |
| **크레딧 롤백** | 서비스 개발 담당 | `blocked`·`error` 수신 시 차감분 되돌리기 |

> ⚠️ **`validation/` 내부는 수정하지 않는다.** 필요하면 전민재 PM에게 요청한다.
> 두 챗봇이 같은 파일을 쓰므로, 한쪽이 고치면 다른 쪽이 깨진다.

---

## 3. ★ 핵심 개념 — 판정값은 2층에서 소비된다

> **여기를 이해하지 못하면 노드를 잘못 만든다.**

```
[1층] 노드 내부 처리
      · pass  → 다음 노드로 진행
      · warn  → 재생성 루프 또는 마스킹 (상한 내에서 자체 해결)
      · block → 즉시 그래프 종료
              ↓ 자체 해결에 실패했을 때만
[2층] 서비스 도달 (최종 응답)
      · status = "blocked" (단일값)
      · action = "block" | "reask" | "warn" (상세)
      · message / alternative (사용자 안내)
```

**왜 두 층인가**

| 문서 | 표현 | 실제 의미 |
| --- | --- | --- |
| `decisions.md` **D-011** | *"blocked 단일화, warn/reask 미노출"* | **1층**: warn은 노드 내부 재생성으로 소화 |
| API Contract **v0.3 §6.5** | *"block/reask/warn 세분화 유지"* | **2층**: 서비스로 나갈 땐 상세를 실어 보냄 |

**두 문서는 충돌이 아니라 서로 다른 층을 말한 것이다.**
대부분의 `warn`은 노드 안에서 재생성으로 해결되고, **재생성 상한(D-019)을 넘겼을 때만** 서비스로 나간다.

---

## 4. 함수 4종 시그니처

```python
# validation/security.py
def check_input(text: str) -> dict: ...
def check_output(text: str) -> dict: ...

# validation/regulation.py
def check_regulation(copy: str) -> dict: ...

# validation/self_check.py
def self_check(result: dict, context: dict) -> dict: ...
```

| 함수 | 입력 | 검사 대상 | 파이프라인 위치 |
| --- | --- | --- | --- |
| `check_input` | 사용자 질문 | **입력** — 불법 키워드·프롬프트 인젝션 | 맨 앞 (LLM 호출 전) |
| `check_regulation` | 생성된 카피 | **출력** — 표시광고법·식품표시광고법 | 카피 생성 직후 |
| `check_output` | 최종 답변 | **출력** — 민감정보·시스템 프롬프트 누출 | 응답 직전 |
| `self_check` | 결과 + 컨텍스트 | **품질** — 근거 유무·완결성 | 맨 끝 |

> **`check_input`만 "막는" 검사이고, 나머지는 "고쳐서 내보내는" 검사다.**
> 그래서 `check_input`은 LLM 호출 **전**에 두어 비용을 0원으로 만든다.

---

## 5. 반환 규격

### 5.1 `check_input` / `check_output`

```python
{
    "action": "pass",      # "pass" | "warn" | "block"
    "message": ""          # 사용자 안내 문구 (pass면 빈 문자열)
}
```

| 필드 | 타입 | 필수 | Nullable | 설명 |
| --- | --- | --- | --- | --- |
| `action` | string | O | X | `pass` \| `warn` \| `block` |
| `message` | string | O | X | 사용자 표시 문구. `pass`일 때 `""` |

### 5.2 `check_regulation`

```python
{
    "action": "warn",
    "law": "표시광고법 제3조",
    "reason": "객관적 근거 없는 최상급 표현",
    "alternative": "정성껏 볶은 원두",
    "message": "'최고'는 부당광고가 될 수 있어요. 다른 표현을 제안드릴까요?"
}
```

| 필드 | 타입 | 필수 | Nullable | 설명 |
| --- | --- | --- | --- | --- |
| `action` | string | O | X | `pass` \| `warn` \| `block` |
| `law` | string | O | X | 근거 조문. `pass`면 `""` |
| `reason` | string | O | X | 왜 문제인지. `pass`면 `""` |
| `alternative` | string | O | X | **대안 문구**. `pass`면 `""` |
| `message` | string | O | X | 사용자 안내. `pass`면 `""` |

> ★ **`alternative`가 이 함수의 존재 이유다.**
> *"'최고'는 쓸 수 없습니다"* 만 주면 사용자는 *"그럼 뭘 쓰라고?"* 가 된다.
> **차단이 아니라 대안 제시가 목적**이므로, `warn`일 때 `alternative`는 반드시 채워진다.

### 5.3 `self_check`

```python
{
    "action": "reject",
    "reasons": ["근거 없음", "제안 개수 부족"],
    "message": "생성 결과에 근거가 부족합니다."
}
```

| 필드 | 타입 | 필수 | Nullable | 설명 |
| --- | --- | --- | --- | --- |
| `action` | string | O | X | `pass` \| `warn` \| **`reject`** |
| `reasons` | string[] | O | X | 실패 사유 목록. `pass`면 `[]` |
| `message` | string | O | X | 사용자 안내. `pass`면 `""` |

> ⚠️ **`self_check`만 세 번째 값이 `block`이 아니라 `reject`다.**
> 보안·규제는 "막는다(block)"이고, 품질은 "되돌린다(reject)"라 의미가 다르다.

### 5.4 ⚠️ 절대 규칙 3가지

```
① action 값은 문자열 하나만 반환한다
   ✅ "action": "pass"
   ❌ "action": "pass"/"warn"/"block"     ← 파이썬에서 TypeError

② pass일 때도 모든 필드를 채운다 (빈 문자열/빈 배열)
   ✅ {"action":"pass", "law":"", "reason":"", "alternative":"", "message":""}
   ❌ {"action":"pass"}                    ← 받는 쪽이 KeyError

③ 받는 쪽은 message를 직접 만들지 않는다
   PM이 준 message를 그대로 사용자에게 전달한다
   → 안내 문구가 팀마다 달라지면 서비스 톤이 무너진다
```

---

## 6. ★ action 값별 노드 처리 규칙

> **이 표가 계약서의 본체다.** 노드를 만들 때 이대로 구현한다.

### 6.1 `check_input` (보안1)

| action | 노드가 할 일 | 서비스 도달 | 크레딧 |
| --- | --- | --- | --- |
| `pass` | 다음 노드로 진행 | — | — |
| `warn` | **사용자에게 재질문 후 그래프 종료** | ✅ `status="blocked"`, `action="reask"` | **롤백** |
| `block` | **즉시 종료. LLM 호출 0회** | ✅ `status="blocked"`, `action="block"` | **롤백** |

> **`block`에서 LLM을 부르지 않는 것이 핵심이다.** 여기서 막아야 비용이 0원이다.

### 6.2 `check_regulation` (규제 검증)

| action | 노드가 할 일 | 서비스 도달 | 크레딧 |
| --- | --- | --- | --- |
| `pass` | 다음 노드로 진행 | — | 차감 유지 |
| `warn` | **카피 생성으로 재생성 (상한 2회 — D-019)** | 상한 초과 시만 ✅ | 차감 유지 |
| `block` | 즉시 종료 | ✅ `status="blocked"` | **롤백** |

**재생성 루프 상세**
```
카피 생성 → check_regulation → warn
   ↓ (1회차 재생성)
카피 생성 → check_regulation → warn
   ↓ (2회차 재생성 — 상한)
카피 생성 → check_regulation → warn
   ↓ 상한 초과
서비스에 반환: status="blocked", action="warn",
              law·reason·alternative 포함
```

> **상한을 두는 이유**: 무한 재생성은 OpenAI $30 한도를 태운다.
> 2회 초과 시 사용자에게 **대안 문구를 주고 판단을 넘긴다.**

### 6.3 `check_output` (보안2)

| action | 노드가 할 일 | 서비스 도달 | 크레딧 |
| --- | --- | --- | --- |
| `pass` | 다음 노드로 진행 | — | 차감 유지 |
| `warn` | **해당 부분 마스킹 후 진행** | — | 차감 유지 |
| `block` | 즉시 종료 | ✅ `status="blocked"` | **롤백** |

> `warn`은 *"전화번호가 노출됐다"* 같은 경우다. **답변 전체를 버릴 필요는 없고** 해당 부분만 가린다.

### 6.4 `self_check` (답변 검증)

| action | 노드가 할 일 | 서비스 도달 | 크레딧 |
| --- | --- | --- | --- |
| `pass` | 응답 반환 | — | 차감 유지 |
| `warn` | **로그만 남기고 응답은 반환** | — | 차감 유지 |
| `reject` | **재생성 1회 → 실패 시 error** | 재시도 실패 시 ✅ | **롤백** |

> `self_check`의 `warn`은 *"근거가 좀 약하다"* 수준이라 **사용자에게 보여줘도 된다.**
> `reject`는 *"근거가 아예 없다"* 라 되돌린다.

---

## 7. 크레딧 롤백 규칙 (서비스 개발 담당용)

> 서비스는 **모델 호출 전에 크레딧을 차감**한다(서비스 SDP §6.5).
> 따라서 아래 경우 **반드시 롤백**해야 한다. (S-11 · D-020 연계)

| 모델 응답 | 크레딧 | 무료 횟수 | 근거 |
| --- | --- | --- | --- |
| `status="ok"` (카피 1개 이상 성공) | **차감 유지** | 차감 유지 | D-020 |
| `status="ok"` (이미지만 실패) | **차감 유지** | 차감 유지 | D-020 — 카피가 핵심 산출물 |
| **`status="blocked"`** | **전액 롤백** | **롤백** | 사용자가 결과물을 못 받음 |
| **`status="error"`** | **전액 롤백** | **롤백** | S-11 |

> ⚠️ **`blocked`도 롤백 대상이다.** `error`만 롤백하도록 구현하면,
> 불법 키워드를 입력한 사용자가 **크레딧만 잃고 아무것도 못 받는다.** 컴플레인 1순위.

---

## 8. 노드 래핑 예시 (두 챗봇 담당자용)

> **이대로 복사해서 쓰면 된다.** 함수 내부가 스텁이든 실구현이든 코드는 동일하다.

### 8.1 보안1 노드

```python
# models/basic/nodes/security_input.py
from validation.security import check_input


def security_input_node(state: dict) -> dict:
    """보안1 — PM의 check_input()을 그래프 노드로 감싼다."""
    verdict = check_input(state["question"])

    state.setdefault("validation", {})["input"] = verdict

    if verdict["action"] == "block":
        state["status"] = "blocked"
        state["blocked"] = {
            "action": "block",
            "reason": "illegal_or_injection",
            "message": verdict["message"],
        }
    elif verdict["action"] == "warn":
        state["status"] = "blocked"
        state["blocked"] = {
            "action": "reask",
            "reason": "need_clarification",
            "message": verdict["message"],
        }

    return state
```

### 8.2 규제 검증 노드 (재생성 루프 포함)

```python
# models/basic/nodes/regulation_node.py
from validation.regulation import check_regulation

MAX_RETRY = 2   # D-019 재생성 상한


def regulation_node(state: dict) -> dict:
    """규제 검증 — warn이면 재생성, 상한 초과 시 대안과 함께 반환."""
    copy_text = state["proposals"][0]["copy"]
    verdict = check_regulation(copy_text)

    state.setdefault("validation", {})["regulation"] = verdict

    if verdict["action"] == "pass":
        return state

    if verdict["action"] == "block":
        state["status"] = "blocked"
        state["blocked"] = {
            "action": "block",
            "reason": "prohibited_item",
            "message": verdict["message"],
        }
        return state

    # warn — 재생성 루프
    retry = state.get("retry_count", 0)
    if retry < MAX_RETRY:
        state["retry_count"] = retry + 1
        state["_goto"] = "copy_gen"          # 조건부 엣지가 읽는 값
        return state

    # 상한 초과 — 대안과 함께 서비스로 반환
    state["status"] = "blocked"
    state["blocked"] = {
        "action": "warn",
        "reason": "regulation_risk",
        "law": verdict["law"],
        "alternative": verdict["alternative"],
        "message": verdict["message"],
    }
    return state
```

### 8.3 조건부 엣지 연결

```python
# models/basic/graph/build_basic.py
def route_after_regulation(state: dict) -> str:
    if state.get("status") == "blocked":
        return "END"
    if state.get("_goto") == "copy_gen":
        return "copy_gen"          # 재생성 루프
    return "image_gen"


graph.add_conditional_edges("regulation", route_after_regulation)
```

---

## 9. 스텁 → 실구현 전환

> ★ **핵심 원칙: 반환 형식이 같으므로 받는 쪽 코드는 수정할 필요가 없다.**

| 함수 | 현재 상태 | 실구현 예정 | 실구현 시 달라지는 것 |
| --- | --- | --- | --- |
| `check_input` | 스텁(`pass`) | **8/12(D2)** | 실제 `block` 반환 시작 |
| `check_regulation` 1단 | 스텁(`pass`) | **8/13(D3)** | 키워드 기반 `warn` 반환 시작 |
| `check_output` | 스텁(`pass`) | **8/14(D4)** | 누출 탐지 시 `warn`/`block` |
| `self_check` (A)규칙 | 스텁(`pass`) | **8/14(D4)** | 근거·개수 검사 시작 |
| `check_regulation` 2단 RAG | 미구현 | **8/19(D7)** [SHOULD] | `law`·`alternative`가 조문 기반으로 채워짐 |

**전환 시 전민재 PM이 할 일**
```
① validation/ 내부만 수정
② 반환 형식은 그대로 유지 (필드 추가·삭제 금지)
③ 팀 채널에 "○○ 실구현 완료" 공지
④ decisions.md 에 기록
```

**전환 시 두 챗봇 담당자가 할 일**
```
아무것도 없음. 다만 실구현 후 자기 파이프라인을 한 번 돌려
warn/block 분기가 정상 동작하는지 확인한다.
```

---

## 10. 계약 위반 방지 — 스모크 테스트

> `tests/validation/test_contract.py` 가 이 계약을 자동 검증한다. **CI에서 매 PR마다 실행된다.**

```python
"""검증 함수 4종 계약 스모크 테스트 — 스텁이든 실구현이든 항상 통과해야 함"""
from validation.regulation import check_regulation
from validation.security import check_input, check_output
from validation.self_check import self_check


def test_check_input():
    r = check_input("테스트 질문")
    assert r["action"] in ("pass", "warn", "block")
    assert isinstance(r["message"], str)


def test_check_output():
    r = check_output("테스트 답변")
    assert r["action"] in ("pass", "warn", "block")
    assert isinstance(r["message"], str)


def test_check_regulation():
    r = check_regulation("우리 가게가 최고입니다")
    assert r["action"] in ("pass", "warn", "block")
    for k in ("law", "reason", "alternative", "message"):
        assert isinstance(r[k], str), f"{k} 는 문자열이어야 함"


def test_self_check():
    r = self_check({"proposals": []}, {})
    assert r["action"] in ("pass", "warn", "reject")
    assert isinstance(r["reasons"], list)
    assert isinstance(r["message"], str)
```

> **이 테스트가 잡는 것**: 반환 타입 오류, 필드 누락, `action` 오타.
> **import만으로는 안 잡힌다** — 반드시 **호출**해야 잡히므로 함수를 실제로 실행한다.

**실행**
```bash
uv run --locked --all-groups pytest tests/validation/test_contract.py -q
uv run --locked --group dev ruff check . --fix
```

---

## 11. 골든 데이터셋과의 연결

> 이 계약이 **실제로 잘 지켜지는지**는 골든 데이터셋 거부 영역(`R-` 15문항)이 검증한다.
> 상세는 `docs/golden_dataset.md` §3.4 참조.

| 골든 문항 | 검증 대상 함수 | 기대 `action` |
| --- | --- | --- |
| `R-001`~`R-003` (불법 품목) | `check_input` | `block` |
| `R-004`~`R-005` (인젝션) | `check_input` | `block` |
| `R-006`~`R-008` (과장 표현) | `check_regulation` | `warn` + `alternative` |
| `R-009`~`R-010` (의학 효능) | `check_regulation` | `warn` + `alternative` |
| **`R-011`~`R-015` (과잉 차단 가드)** | `check_input`·`check_regulation` | **`pass`** |

**측정 지표**

| 지표 | 계산 | 목표 |
| --- | --- | --- |
| 차단 정확도(Recall) | `R-001`~`R-010` 중 정답 일치 비율 | **100%** (불법은 하나도 놓치면 안 됨) |
| **과잉 차단률(FPR)** | `R-011`~`R-015` 중 잘못 막은 비율 | **10% 이하** |
| 대안 제시율 | `warn` 판정 중 `alternative` 채워진 비율 | **100%** |

> ⚠️ **차단 문항만 있으면 "전부 막는 함수"도 100점을 받는다.**
> 과잉 차단 가드 5문항이 실제 품질을 드러낸다.

---

## 12. 서비스 API 계약과의 매핑

> 노드가 만든 `state["blocked"]` 를 서비스 응답으로 어떻게 바꾸는지.
> API Contract v0.3 §6.5 기준.

**모델 → 서비스 응답**
```json
{
  "status": "blocked",
  "action": "warn",
  "reason": "regulation_risk",
  "message": "'최고'와 같은 표현은 부당광고가 될 수 있어요. 다른 표현을 제안드릴까요?"
}
```

| 검증 함수 결과 | 서비스 `status` | 서비스 `action` |
| --- | --- | --- |
| `check_input` → `block` | `blocked` | `block` |
| `check_input` → `warn` | `blocked` | `reask` |
| `check_regulation` → `block` | `blocked` | `block` |
| `check_regulation` → `warn` (상한 초과) | `blocked` | `warn` |
| `check_output` → `block` | `blocked` | `block` |
| `self_check` → `reject` (재시도 실패) | `error` | — |

> **`self_check` 실패만 `error`인 이유**: 보안·규제는 *"의도적으로 막았다"* 이고,
> 품질 실패는 *"만들지 못했다"* 라 성격이 다르다. HTTP 매핑도 달라진다.

---

## 13. ⚠️ 받는 쪽이 하면 안 되는 것

```
① validation/ 내부 파일을 수정한다
   → 두 챗봇이 같은 파일을 쓴다. 한쪽이 고치면 다른 쪽이 깨진다
   → 필요하면 전민재 PM에게 요청

② action 값을 임의로 추가한다
   → "skip", "retry" 같은 값을 만들면 다른 챗봇과 규격이 어긋난다

③ message 를 직접 작성한다
   → PM이 준 문구를 그대로 전달한다. 안내 톤이 팀마다 달라지면 안 된다

④ pass 가 아닌데 그냥 통과시킨다
   → 검증 함수를 붙인 의미가 사라진다. 스텁 기간에도 분기는 만들어 둔다

⑤ 크레딧 롤백을 모델 쪽에서 처리한다
   → 과금은 서비스 개발 담당 영역. 모델은 판정 결과만 정확히 전달한다
```

---

## 14. 변경 절차

> 계약을 바꿔야 할 때 **코드보다 문서를 먼저** 고친다.

```
① 변경 필요 발견 → 스크럼 또는 팀 채널에 공유
② 전민재 PM이 본 문서(validation_contract.md) 수정
③ decisions.md 에 변경 이력 기록 (원래 줄은 지우지 않음)
④ tests/validation/test_contract.py 갱신
⑤ validation/ 구현 수정
⑥ 팀 채널 공지 → 두 챗봇 담당자가 노드 확인
```

> **④를 ⑤보다 먼저 하는 이유**: 테스트를 먼저 고치면 **구현이 계약을 어겼을 때 CI가 잡는다.**

---

## 15. 미확정 사항

| ID | 항목 | 현재 기본안 | Owner | Due |
| --- | --- | --- | --- | --- |
| V-01 | `check_input` `warn` 시 재질문 UX | 그래프 종료 후 서비스가 재질문 화면 표시 | 전민재 PM | 8/14 |
| V-02 | `check_output` `warn` 마스킹 방식 | 해당 부분을 `***` 로 치환 | 전민재 PM | 8/14 |
| V-03 | `self_check` `reject` 재시도 횟수 | **1회** | 전민재 PM | 8/14 |
| V-04 | `check_regulation` 2단 RAG 전환 | 1주차 키워드 → 2주차 RAG [SHOULD] | 전민재 PM | 8/19 |
| V-05 | `self_check` (B) 사실성 검증 | SHOULD, OpenAI 예산 여유 시 | 전민재 PM | 8/21 |

---

## 부록 A. 빠른 참조 — action 값 요약

```
check_input      : pass | warn(→reask) | block
check_regulation : pass | warn(→재생성 2회) | block
check_output     : pass | warn(→마스킹) | block
self_check       : pass | warn(→로그만) | reject(→재시도 1회)

서비스 도달 시:
  status = "blocked"  → action = block | reask | warn   → 크레딧 롤백
  status = "error"    → self_check reject 재시도 실패    → 크레딧 롤백
  status = "ok"       → 정상                             → 차감 유지
```

## 부록 B. 참고 문서
- 요구사항 명세서 v10 (`v10_sw_req_spec.md`)
- 프로젝트 가이드 · 프로젝트 팁 (`project_tip.md`)
- 의사결정 로그 (`docs/decisions.md`) — D-011 · D-018 · D-019 · D-020
- 디렉토리 구조 (`docs/directory_structure.md`)
- **골든 데이터셋 기준 문서** (`docs/golden_dataset.md`) — `R-` 15문항이 본 계약을 검증
- 서비스 API/DB Contract v0.3 — §6.5 정책 검증 결과 · S-11 롤백
- 4개 담당자 SDP (`docs/sdp_pm.md` / `sdp_service.md` / `sdp_basic.md` / `sdp_consult.md`)