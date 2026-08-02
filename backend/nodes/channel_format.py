# -*- coding: utf-8 -*-
"""
channel_format.py — 채널별 리포맷 노드 [윤승준 담당 영역]

같은 카피를 채널 특성에 맞게 변환한다.
  - instagram : 짧고 감성적 + 해시태그 5~10개 + CTA(DM/방문)
  - blog      : 제목 + 3~4문장 본문 + 정보(위치/영업시간 자리표시)
  - banner    : 현수막용 8~12자 핵심 문구 + 큰 숫자/연락처 강조
"""
from llm import call_gpt

_GUIDE = {
    "instagram": "인스타그램 게시물: 첫 문장에 후킹, 감성 톤, 해시태그 5~10개(지역명+메뉴명), 끝에 CTA(DM 문의/지금 방문).",
    "blog": "블로그 게시물: 제목 1줄 + 본문 3~4문장(스토리+정보), 위치/영업시간은 [] 자리표시로.",
    "banner": "현수막 문구: 멀리서 3초에 읽히게 8~12자 핵심 메시지 + 큰 숫자(할인/가격) + 전화번호 자리표시. 군더더기 금지.",
}


def channel_format_node(state) -> dict:
    channel = state.get("config", {}).get("channel", "instagram")
    base = state.get("best_copy", "") or state.get("variants_raw", "")
    guide = _GUIDE.get(channel, _GUIDE["instagram"])

    messages = [
        {"role": "system", "content":
            "너는 채널별 카피 편집자다. 아래 카피를 지정 채널 형식으로 다시 써라. "
            "과장·허위 금지. 결과 카피 텍스트만 출력.\n" + guide},
        {"role": "user", "content": f"[원본 카피]\n{base}\n\n[채널] {channel}"},
    ]
    text, tokens = call_gpt(messages)
    return {
        "answer": text.strip(),
        "channel": channel,
        "tokens_used": state.get("tokens_used", 0) + tokens,
    }
