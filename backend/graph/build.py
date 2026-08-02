# -*- coding: utf-8 -*-
"""
build.py — Agentic-RAG 그래프 조립 (보안 노드 제외 MVP)

흐름:
  START → question_analysis
    ├─(정보부족)→ clarify → END                      [조희원: 꼬리질문]
    └─(충분)→ routing → collect_context → copy_gen → ranking
                 ├─(품질미달 & 재시도여유)→ copy_gen ↺  (agentic 품질 루프) [김재헌]
                 └─(통과 or 상한초과)→ 분기
                        ├─(paid)→ image_gen → channel_format
                        └─(free)→ channel_format
                 → self_check → END
"""
from langgraph.graph import StateGraph, START, END

from graph.state import GraphState
from nodes.question_analysis import question_analysis_node, clarify_node
from nodes.routing import routing_node
from nodes.context import collect_context_node
from nodes.copy_gen import copy_gen_node
from nodes.ranking import ranking_node
from nodes.image_gen import image_gen_node
from nodes.channel_format import channel_format_node
from nodes.self_check import self_check_node


# ── 조건부 분기 선택자 ──
def _after_analysis(state: GraphState) -> str:
    return "clarify" if state.get("needs_clarification") else "routing"


def _after_ranking(state: GraphState) -> str:
    """품질 게이트 + 재시도 상한 → 재생성 / 이미지 / 채널포맷."""
    cfg = state.get("config", {})
    threshold = cfg.get("quality_threshold", 7.0)
    max_regen = cfg.get("max_regen", 2)
    if state.get("best_score", 0) < threshold and state.get("regen_count", 0) < max_regen:
        return "copy_gen"                       # ↺ 재생성 루프
    return "image_gen" if state.get("route") == "paid" else "channel_format"


def build_graph():
    g = StateGraph(GraphState)

    g.add_node("question_analysis", question_analysis_node)
    g.add_node("clarify", clarify_node)
    g.add_node("routing", routing_node)
    g.add_node("collect_context", collect_context_node)
    g.add_node("copy_gen", copy_gen_node)
    g.add_node("ranking", ranking_node)
    g.add_node("image_gen", image_gen_node)
    g.add_node("channel_format", channel_format_node)
    g.add_node("self_check", self_check_node)

    g.add_edge(START, "question_analysis")
    # 정보 충분성 분기
    g.add_conditional_edges("question_analysis", _after_analysis,
                            {"clarify": "clarify", "routing": "routing"})
    g.add_edge("clarify", END)                  # 꼬리질문은 여기서 사용자에게 반환

    g.add_edge("routing", "collect_context")
    g.add_edge("collect_context", "copy_gen")
    g.add_edge("copy_gen", "ranking")
    # 품질 게이트(agentic 루프)
    g.add_conditional_edges("ranking", _after_ranking, {
        "copy_gen": "copy_gen",                 # ↺ 재생성
        "image_gen": "image_gen",               # 유료 → 이미지
        "channel_format": "channel_format",     # 무료 → 바로 채널포맷
    })
    g.add_edge("image_gen", "channel_format")
    g.add_edge("channel_format", "self_check")
    g.add_edge("self_check", END)

    return g.compile()


if __name__ == "__main__":
    app = build_graph()
    print("그래프 컴파일 완료. 노드:", list(app.get_graph().nodes.keys()))
