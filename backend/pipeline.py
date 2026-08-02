# -*- coding: utf-8 -*-
"""
pipeline.py — 서비스/평가 공통 진입점 get_ai_response.
LangGraph 앱을 1회 컴파일해 캐싱하고, 결과를 프론트가 쓰기 좋은 dict로 변환한다.
"""
import time
from config import load_config
from graph.build import build_graph

_app = None


def _get_app():
    global _app
    if _app is None:
        _app = build_graph()
    return _app


def get_ai_response(question: str, history: list[dict] = None,
                    industry: str = "", store_name: str = "",
                    config: dict = None) -> dict:
    """
    Args:
        question  : 사용자 요청
        history   : [{"role","content"}, ...]
        industry  : 업종(카페/식당/의류...)
        store_name: 가게명
        config    : plan/channel/토글 등 (없으면 config.yaml)
    Returns:
        answer / image_path / best_score / channel / sources / check_flags /
        is_clarification / tokens_used / elapsed_sec
    """
    start = time.time()
    cfg = config or load_config()
    cfg.setdefault("industry", industry)

    result = _get_app().invoke({
        "question": question,
        "history": history or [],
        "industry": industry,
        "store_name": store_name,
        "config": cfg,
        "regen_count": 0,
        "tokens_used": 0,
    })

    return {
        "answer": result.get("answer", ""),
        "image_path": result.get("image_path", ""),
        "best_copy": result.get("best_copy", ""),
        "best_score": result.get("best_score", 0.0),
        "rank_reason": result.get("rank_reason", ""),
        "channel": result.get("channel", cfg.get("channel", "instagram")),
        "variants": result.get("variants", []),
        "sources": result.get("sources", []),
        "check_flags": result.get("check_flags", []),
        "risky_terms": result.get("risky_terms", []),
        "is_clarification": result.get("is_clarification", False),
        "tokens_used": result.get("tokens_used", 0),
        "elapsed_sec": round(time.time() - start, 2),
    }


if __name__ == "__main__":
    print("=== 케이스1: 정보 충분 (카페 여름 신메뉴) ===")
    r = get_ai_response(
        "강남역 근처 카페인데 여름 신메뉴 홍보 인스타 문구 만들어줘. 20대 타겟, 감성 톤.",
        industry="카페", store_name="민재커피",
        config={**load_config(), "plan": "free", "channel": "instagram"},
    )
    print("반문 여부:", r["is_clarification"])
    print("최고점수:", r["best_score"], "| 채널:", r["channel"])
    print("답변:\n", r["answer"][:300])
    print("소스 수:", len(r["sources"]), "| 플래그:", r["check_flags"], "| 토큰:", r["tokens_used"])

    print("\n=== 케이스2: 유료(이미지 포함) ===")
    r2 = get_ai_response(
        "여름 아이스 음료 인스타 홍보물 만들어줘. 시원한 느낌.",
        industry="카페", store_name="민재커피",
        config={**load_config(), "plan": "paid", "channel": "instagram"},
    )
    print("이미지 경로:", r2["image_path"])
    print("소요:", r2["elapsed_sec"], "초")
