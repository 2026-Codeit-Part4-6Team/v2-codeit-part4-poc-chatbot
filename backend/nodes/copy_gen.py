# -*- coding: utf-8 -*-
"""
copy_gen.py — 광고 카피 생성 노드 (컨텍스트 반영 + 3안 생성)

수집된 context(트렌드·경쟁사·벤치마크)를 근거로 서로 다른 톤의 카피 N안을 만든다.
재생성 루프(agentic)로 다시 들어오면 regen_count를 보고 '직전보다 개선'을 지시한다.
"""
from llm import call_gpt

_SYSTEM = """너는 소상공인 전문 광고 카피라이터다. 주어진 컨텍스트(검색 트렌드, 경쟁사 차별점,
업종 벤치마크)를 실제로 반영해, 서로 다른 톤의 광고 카피 {n}개를 만들어라.
규칙:
- 각 안은 서로 톤/각도가 달라야 한다(예: 감성형 / 혜택강조형 / 트렌드형).
- 과장·허위·의학적 효능 단정 금지(광고 규제 준수).
- 각 안은 2~3줄 이내, 해시태그가 어울리면 2~4개 포함.
출력 형식(정확히 이 형식):
[안1] ...
[안2] ...
[안3] ..."""


def copy_gen_node(state) -> dict:
    cfg = state.get("config", {})
    n = cfg.get("max_variants", 3)
    q = state.get("rewritten_question") or state["question"]
    context = state.get("context", "(컨텍스트 없음)")
    regen = state.get("regen_count", 0)

    improve = ""
    if regen > 0:
        prev = state.get("variants_raw", "")
        improve = (f"\n\n[재생성 지시] 직전 결과가 품질 기준에 미달했다. 아래보다 더 구체적이고 "
                   f"컨텍스트를 더 살려 개선하라:\n{prev}")

    messages = [
        {"role": "system", "content": _SYSTEM.format(n=n)},
        {"role": "user", "content": f"[요청]\n{q}\n\n[컨텍스트]\n{context}{improve}"},
    ]
    text, tokens = call_gpt(messages)
    variants = _parse_variants(text)
    return {
        "variants": variants,
        "variants_raw": text,
        "tokens_used": state.get("tokens_used", 0) + tokens,
    }


def _parse_variants(text: str) -> list[str]:
    """[안N] 마커로 카피를 분리. 마커가 없으면 줄 단위로 폴백."""
    import re
    parts = re.split(r"\[안\s*\d+\]", text)
    variants = [p.strip() for p in parts if p.strip()]
    if not variants:
        variants = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return variants[:5]
