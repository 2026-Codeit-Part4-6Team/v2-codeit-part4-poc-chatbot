# -*- coding: utf-8 -*-
"""
question_analysis.py — 질문 분석 노드 [조희원 담당 영역]

두 가지 일을 한다:
  1) 대명사/지시어 해소(재작성): "이 사업" "그 메뉴" → history 참고해 구체화.
  2) 정보 충분성 판단: 광고 카피를 만들기에 정보가 부족하면 '꼬리질문' 생성.
     (예: 가격대? 주요 타겟 연령? 원하는 톤? 채널?) → 사용자에게 반문.

부족한 정보가 있으면 needs_clarification=True로 그래프를 조기 종료(반문)한다.
"""
import json
from llm import call_gpt

_SYSTEM = """너는 소상공인 광고 제작 어시스턴트의 질문 분석기다.
사용자 요청을 보고 (1) 지시어를 해소한 재작성 질문과 (2) 광고 카피를 만들기에
정보가 충분한지 판단하라. 부족하면 사용자에게 물어볼 꼬리질문 1개를 만들어라.

카피 제작에 필요한 핵심 정보: 업종/가게, 홍보 대상(메뉴·상품·이벤트), 타겟 고객, 톤/분위기.
이 중 2개 이상 빠지면 부족(sufficient=false)으로 본다. 채널은 선택이라 없어도 충분.

반드시 아래 JSON 한 줄만 출력:
{"rewritten": "재작성 질문", "sufficient": true|false, "missing": ["빠진항목"], "clarify_question": "부족할 때 물어볼 한 문장(충분하면 빈 문자열)"}"""


def question_analysis_node(state) -> dict:
    question = state["question"]
    history = state.get("history", [])
    hist_text = "\n".join(f'{m["role"]}: {m["content"]}' for m in history[-4:])

    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"[이전 대화]\n{hist_text or '(없음)'}\n\n[현재 요청]\n{question}"},
    ]
    text, tokens = call_gpt(messages)
    try:
        cleaned = text.strip().replace("```json", "").replace("```", "").strip()
        r = json.loads(cleaned)
    except Exception:
        # 파싱 실패 시 원문 사용 + 충분으로 간주(흐름 계속)
        r = {"rewritten": question, "sufficient": True, "missing": [], "clarify_question": ""}

    return {
        "rewritten_question": r.get("rewritten", question),
        "needs_clarification": not r.get("sufficient", True),
        "clarify_question": r.get("clarify_question", ""),
        "missing_info": r.get("missing", []),
        "tokens_used": state.get("tokens_used", 0) + tokens,
    }


def clarify_node(state) -> dict:
    """정보 부족 시: 꼬리질문을 answer로 담아 사용자에게 반문하고 종료."""
    cq = state.get("clarify_question") or "광고를 만들려면 정보가 조금 더 필요해요. 어떤 상품/메뉴를 홍보할까요?"
    missing = state.get("missing_info", [])
    hint = f" (부족한 정보: {', '.join(missing)})" if missing else ""
    return {"answer": f"❓ {cq}{hint}", "is_clarification": True}
