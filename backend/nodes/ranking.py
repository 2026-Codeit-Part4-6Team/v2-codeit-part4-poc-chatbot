# -*- coding: utf-8 -*-
"""
ranking.py — 배리언트 랭킹 노드 (LLM-as-Judge) [김재헌 담당 영역]

3~5개 카피 후보를 LLM이 채점(관련성/구체성/톤/규제안전성 종합 10점)해
최고 안을 고르고 최고 점수를 기록한다. 최고 점수가 임계값 미만이면
build.py 조건부 엣지가 copy_gen으로 되돌려 재생성(agentic 품질 게이트).
"""
import json
from llm import call_gpt

_SYSTEM = """너는 광고 카피 심사위원(LLM Judge)이다. 후보 카피들을 다음 기준으로 채점하라.
- 요청/컨텍스트 반영도, 구체성, 톤 적합성, 광고 규제 안전성(과장·허위 없음).
각 후보에 0~10 점수를 주고 최고 후보 인덱스(0부터)를 골라라.
반드시 아래 JSON만 출력:
{"scores": [점수,...], "best_index": 정수, "reason": "선정 이유 한 줄"}"""


def ranking_node(state) -> dict:
    cfg = state.get("config", {})
    variants = state.get("variants", [])
    q = state.get("rewritten_question") or state["question"]

    if not variants:
        return {"best_copy": "", "best_score": 0.0, "regen_count": state.get("regen_count", 0) + 1}

    listed = "\n".join(f"[{i}] {v}" for i, v in enumerate(variants))
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"[요청]\n{q}\n\n[후보]\n{listed}"},
    ]
    text, tokens = call_gpt(messages)
    try:
        cleaned = text.strip().replace("```json", "").replace("```", "").strip()
        r = json.loads(cleaned)
        scores = [float(s) for s in r.get("scores", [])]
        best_idx = int(r.get("best_index", 0))
        reason = r.get("reason", "")
    except Exception:
        scores, best_idx, reason = [7.0] * len(variants), 0, "파싱 실패 → 1안 선택"

    best_idx = best_idx if 0 <= best_idx < len(variants) else 0
    best_score = max(scores) if scores else 7.0

    return {
        "best_copy": variants[best_idx],
        "best_score": best_score,
        "rank_reason": reason,
        "regen_count": state.get("regen_count", 0) + 1,  # 이 노드를 지날 때마다 +1(루프 상한용)
        "tokens_used": state.get("tokens_used", 0) + tokens,
    }
