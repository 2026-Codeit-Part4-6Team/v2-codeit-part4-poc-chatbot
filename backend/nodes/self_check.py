# -*- coding: utf-8 -*-
"""
self_check.py — 자체 검증 노드 (룰 기반 최종 게이트)

파트3 self_check 패턴 계승. 광고 카피 맥락에 맞춘 룰:
  - 과장/단정 표현(최고, 100%, 무조건, 완치 등) 감지 → 경고 플래그(차단은 안 함, 사용자 확인용).
  - 빈 답변 → 안내 문구로 대체.
플래그를 check_flags에 담아 반환(프론트가 '표현 주의' 배지로 노출).
"""
import re

_RISKY = ["최고", "100%", "완치", "무조건", "확실히 낫", "부작용 없", "국내 유일"]


def self_check_node(state) -> dict:
    answer = state.get("answer", "").strip()
    flags = []

    if not answer:
        return {"answer": "카피 생성에 실패했습니다. 요청을 조금 더 구체적으로 입력해 주세요.",
                "check_passed": False, "check_flags": ["empty"]}

    hit = [w for w in _RISKY if w in answer]
    if hit:
        flags.append("risky_expression")

    return {
        "check_passed": len(flags) == 0,
        "check_flags": flags,
        "risky_terms": hit,
    }
