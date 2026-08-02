# -*- coding: utf-8 -*-
"""
context.py — 컨텍스트 수집 노드 (병렬 개념: 3개 소스를 한 노드에서 모아 반환)

  1) 트렌드 조회      : 네이버 데이터랩            [전민재]
  2) 경쟁사 리뷰 요약 : 리뷰 수집 → 차별점 추출   [윤승준]
  3) 업종 벤치마크    : RAG 검색                   [김재헌]

라우팅에서 켜진 소스(use_trend/use_competitor/use_benchmark)만 수집한다.
결과는 하나의 context 문자열 + 근거(sources)로 합쳐 카피 생성 노드에 넘긴다.
"""
import os
import json
from nodes.trend import fetch_trend
from retrieval import search_benchmark
from llm import call_gpt

_HERE = os.path.dirname(os.path.dirname(__file__))
_REVIEW_PATH = os.path.join(_HERE, "data", "competitor_reviews.json")
with open(_REVIEW_PATH, encoding="utf-8") as f:
    _REVIEWS = json.load(f)


# ── 경쟁사 리뷰 요약 [윤승준] ──────────────────────────────────────────────
def summarize_competitors(industry: str, my_store: str = "") -> dict:
    """
    업종의 경쟁사 리뷰를 모아 LLM으로 '공통 불만 → 우리 차별점'을 추출한다.
    POC는 샘플 리뷰(JSON)를 사용. 실서비스에선 상권정보 OpenAPI + 네이버지도
    리뷰 API로 이 부분만 교체(요약/차별점 로직은 그대로 재사용).
    """
    comps = _REVIEWS.get(industry, [])
    if not comps:
        return {"summary": "", "diff_points": [], "n_competitors": 0}

    joined = "\n".join(
        f"- {c['name']}: " + " / ".join(c["reviews"]) for c in comps
    )
    messages = [
        {"role": "system", "content":
            "너는 소상공인 마케팅 분석가다. 경쟁사 리뷰에서 '고객이 불편해하는 공통점'을 찾고, "
            "우리 가게가 내세울 차별점 3가지를 뽑아라. 반드시 아래 JSON만 출력:\n"
            '{"common_pain": "공통 불만 요약", "diff_points": ["차별점1","차별점2","차별점3"]}'},
        {"role": "user", "content":
            f"업종: {industry}\n우리 가게: {my_store or '(정보없음)'}\n\n경쟁사 리뷰:\n{joined}"},
    ]
    text, _ = call_gpt(messages)
    try:
        cleaned = text.strip().replace("```json", "").replace("```", "").strip()
        parsed = json.loads(cleaned)
    except Exception:
        parsed = {"common_pain": "리뷰 분석 실패", "diff_points": []}
    return {
        "summary": parsed.get("common_pain", ""),
        "diff_points": parsed.get("diff_points", []),
        "n_competitors": len(comps),
    }


# ── 컨텍스트 수집 노드 ──────────────────────────────────────────────────────
def collect_context_node(state) -> dict:
    """state.config의 토글에 따라 3개 소스를 수집해 context 텍스트로 합친다."""
    cfg = state.get("config", {})
    q = state.get("rewritten_question") or state["question"]
    industry = state.get("industry", "") or cfg.get("industry", "")

    blocks, sources = [], []

    # 1) 트렌드 [전민재]
    if cfg.get("use_trend", True):
        # 질문에서 키워드 추출은 간단히: 질문 자체 + 업종. (고도화 시 키워드 추출 노드 분리)
        kw = [q[:12], industry] if industry else [q[:12]]
        trend = fetch_trend([k for k in kw if k])
        blocks.append(f"[검색 트렌드] '{trend['keyword']}' 관심도 {trend['direction']} "
                      f"(최신 지수 {trend['latest_ratio']}, 출처 {trend['source']})")
        sources.append({"type": "trend", "data": trend})

    # 2) 경쟁사 리뷰 [윤승준]
    if cfg.get("use_competitor", True) and industry:
        comp = summarize_competitors(industry, state.get("store_name", ""))
        if comp["n_competitors"]:
            dp = ", ".join(comp["diff_points"])
            blocks.append(f"[경쟁사 분석] 경쟁사 {comp['n_competitors']}곳 공통 불만: "
                          f"{comp['summary']} → 우리 차별점: {dp}")
            sources.append({"type": "competitor", "data": comp})

    # 3) 업종 벤치마크 RAG [김재헌]
    if cfg.get("use_benchmark", True):
        hits = search_benchmark(q, industry=industry, k=cfg.get("top_k", 3))
        if hits:
            bench = " / ".join(h["text"] for h in hits)
            blocks.append(f"[업종 벤치마크] {bench}")
            sources.append({"type": "benchmark", "data": hits})

    context = "\n".join(blocks) if blocks else "(수집된 외부 컨텍스트 없음)"
    return {"context": context, "sources": sources}


if __name__ == "__main__":
    st = {"question": "여름 신메뉴 홍보 문구", "industry": "카페",
          "store_name": "민재커피", "config": {"top_k": 3}}
    out = collect_context_node(st)
    print(out["context"])
    print("---")
    print("소스 수:", len(out["sources"]))
