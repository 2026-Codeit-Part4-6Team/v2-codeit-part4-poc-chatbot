# -*- coding: utf-8 -*-
"""
routing.py — 체크박스 라우터 노드 [김재헌 담당 영역]

프론트 체크박스/플랜 선택값(config)에 따라 실행 모드를 정한다.
  - plan: "free"(카피만) | "paid"(카피+이미지)
  - 컨텍스트 소스 on/off: use_trend / use_competitor / use_benchmark
이 노드는 route(=plan)만 기록. 실제 이미지 분기는 build.py 조건부 엣지가 수행.
"""


def routing_node(state) -> dict:
    cfg = state.get("config", {})
    plan = cfg.get("plan", "free")
    if plan not in ("free", "paid"):
        plan = "free"
    return {"route": plan}
