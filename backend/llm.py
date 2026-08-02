# -*- coding: utf-8 -*-
"""
llm.py — gpt-5-mini 호출 래퍼 (파트3 backend_generation.py의 call_gpt 패턴 계승)

특징:
  - OPENAI_API_KEY가 있으면 실제 gpt-5-mini 호출.
  - 없으면 오프라인 목(mock) 응답으로 폴백 → API 키 없이도 그래프 전체 흐름 검증 가능.
    (POC 개발 초기·CI에서 유용. 실제 시연 땐 키를 넣어 실호출.)
반환: (텍스트, 사용 토큰 수) 튜플로 통일.
"""
import os
import json

_HAS_KEY = bool(os.getenv("OPENAI_API_KEY"))

if _HAS_KEY:
    from openai import OpenAI
    _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def call_gpt(messages: list[dict], model: str = "gpt-5-mini") -> tuple[str, int]:
    """chat.completions 호출. 키 없으면 목 응답."""
    if not _HAS_KEY:
        return _mock_response(messages), 0
    resp = _client.chat.completions.create(model=model, messages=messages)
    return resp.choices[0].message.content, resp.usage.total_tokens


def call_gpt_json(messages: list[dict], model: str = "gpt-5-mini") -> tuple[dict, int]:
    """JSON 응답 강제 호출. 파싱 실패 시 빈 dict."""
    text, tokens = call_gpt(messages, model)
    try:
        # ```json 펜스가 붙어오는 경우 제거 후 파싱
        cleaned = text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned), tokens
    except (json.JSONDecodeError, AttributeError):
        return {}, tokens


# ── 오프라인 목: 마지막 user 메시지를 보고 그럴듯한 응답 반환 ──
def _mock_response(messages: list[dict]) -> str:
    sys = " ".join(m["content"] for m in messages if m["role"] == "system")
    user = " ".join(m["content"] for m in messages if m["role"] == "user")

    if "JSON" in sys or "json" in sys:
        # 정보충분성/랭킹/라우팅 등 JSON 요구 노드용 기본값
        if "충분" in sys or "clarify" in sys or "부족" in sys:
            return '{"sufficient": true, "missing": [], "clarify_question": ""}'
        if "점수" in sys or "score" in sys or "Judge" in sys:
            return '{"scores": [8, 7, 6], "best_index": 0, "reason": "가장 구체적이고 톤이 맞음(mock)"}'
        return "{}"

    if "카피" in sys or "광고 문구" in user or "카피" in user:
        return ("[안1] 시원한 여름, 오늘의 특별한 한 잔 ☕ #신메뉴\n"
                "[안2] 무더위엔 역시! 새로 나온 여름 메뉴 만나보세요\n"
                "[안3] 지금 방문하면 여름 신메뉴 첫 손님 혜택 (mock)")
    return "이것은 오프라인 목 응답입니다. 실제 시연 시 OPENAI_API_KEY를 설정하세요."


if __name__ == "__main__":
    txt, tok = call_gpt([
        {"role": "system", "content": "너는 광고 카피라이터다."},
        {"role": "user", "content": "카페 여름 신메뉴 광고 문구 만들어줘"},
    ])
    print("응답:", txt)
    print("토큰:", tok, "| 실호출:", _HAS_KEY)
