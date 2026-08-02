# -*- coding: utf-8 -*-
"""state.py — LangGraph 공유 상태(GraphState). total=False라 노드가 점진적으로 채운다."""
from typing import TypedDict, Literal, Optional


class GraphState(TypedDict, total=False):
    # ── 입력 ──
    question: str
    history: list[dict]
    industry: str
    store_name: str
    config: dict                 # plan, channel, use_trend/competitor/benchmark, top_k 등

    # ── question_analysis 산출 [조희원] ──
    rewritten_question: str
    needs_clarification: bool
    clarify_question: str
    missing_info: list[str]
    is_clarification: bool

    # ── routing 산출 [김재헌] ──
    route: Literal["free", "paid"]

    # ── context 산출 [전민재/윤승준/김재헌] ──
    context: str
    sources: list[dict]

    # ── copy_gen / ranking 산출 ──
    variants: list[str]
    variants_raw: str
    best_copy: str
    best_score: float
    rank_reason: str
    regen_count: int             # 재생성 루프 상한(agentic)

    # ── image / channel 산출 ──
    image_path: str
    channel: str

    # ── 최종 ──
    answer: str
    tokens_used: int
    check_passed: bool
    check_flags: list[str]
    risky_terms: list[str]
