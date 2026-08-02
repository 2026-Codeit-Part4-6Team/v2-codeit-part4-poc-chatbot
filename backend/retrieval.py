# -*- coding: utf-8 -*-
"""
retrieval.py — 업종 벤치마크 지식베이스(RAG) 경량 검색기. [김재헌 담당 영역]

POC 원칙: 4일 안에 안정적으로 돌게 하려고 외부 벡터DB(FAISS/Chroma) 없이
numpy 코사인 유사도로 구현. (KB가 수십 건 규모라 이 정도로 충분)
→ 규모가 커지면 이 파일만 FAISS/Chroma로 교체(인터페이스 유지).

임베딩: OPENAI_API_KEY 있으면 text-embedding-3-small,
        없으면 자모/토큰 겹침 기반 폴백(오프라인에서도 검색 흐름 시연 가능).
"""
import os
import json
import math

_HERE = os.path.dirname(__file__)
_KB_PATH = os.path.join(_HERE, "data", "benchmark_kb.json")
_HAS_KEY = bool(os.getenv("OPENAI_API_KEY"))

with open(_KB_PATH, encoding="utf-8") as f:
    _KB = json.load(f)

_EMB_CACHE = None  # KB 임베딩 캐시(1회 계산)


# ── 임베딩 ─────────────────────────────────────────────────────────────────
def _embed(texts: list[str]) -> list[list[float]]:
    if _HAS_KEY:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.embeddings.create(model="text-embedding-3-small", input=texts)
        return [d.embedding for d in resp.data]
    # 오프라인 폴백: 문자 bigram 해시 기반 희소 벡터(정확도↓, 흐름 검증용)
    return [_bow_vector(t) for t in texts]


def _bow_vector(text: str, dim: int = 512) -> list[float]:
    vec = [0.0] * dim
    tokens = text.replace("\n", " ").split()
    for tok in tokens:
        for i in range(len(tok) - 1):
            h = hash(tok[i:i + 2]) % dim
            vec[h] += 1.0
    return vec


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(y * y for y in b)) or 1e-9
    return dot / (na * nb)


def _ensure_kb_embeddings():
    global _EMB_CACHE
    if _EMB_CACHE is None:
        _EMB_CACHE = _embed([item["text"] for item in _KB])
    return _EMB_CACHE


# ── 검색 ───────────────────────────────────────────────────────────────────
def search_benchmark(query: str, industry: str = "", k: int = 3) -> list[dict]:
    """
    질문 + 업종으로 벤치마크 KB에서 상위 k개 청크를 반환.
    industry가 주어지면 해당 업종 + '공통' 항목만 후보로 좁힌다.

    Returns: [{text, industry, score}, ...]
    """
    kb_emb = _ensure_kb_embeddings()
    q_emb = _embed([query])[0]

    scored = []
    for item, emb in zip(_KB, kb_emb):
        if industry and item["industry"] not in (industry, "공통"):
            continue
        scored.append({
            "text": item["text"],
            "industry": item["industry"],
            "score": round(_cosine(q_emb, emb), 4),
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]


if __name__ == "__main__":
    hits = search_benchmark("여름 신메뉴 홍보 문구", industry="카페", k=3)
    for h in hits:
        print(f"[{h['score']}] ({h['industry']}) {h['text'][:40]}...")
