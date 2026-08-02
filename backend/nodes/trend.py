# -*- coding: utf-8 -*-
"""
trend.py — 네이버 데이터랩 통합검색어 트렌드 조회 노드 [전민재 담당]

엔드포인트: POST https://openapi.naver.com/v1/datalab/search
헤더: X-Naver-Client-Id / X-Naver-Client-Secret / Content-Type: application/json
바디: {startDate, endDate, timeUnit, keywordGroups:[{groupName, keywords}], ...}
문서: https://developers.naver.com/docs/serviceapi/datalab/search/search.md

키가 없으면 mock 시계열을 반환 → API 신청 전에도 파이프라인 시연 가능.
"""
import os
import json
import urllib.request
from datetime import date, timedelta

_URL = "https://openapi.naver.com/v1/datalab/search"


def fetch_trend(keywords: list[str], months: int = 6, time_unit: str = "week") -> dict:
    """
    키워드들의 최근 N개월 검색 트렌드를 조회한다.

    Args:
        keywords : 조회할 키워드 리스트 (예: ["여름 신메뉴", "아이스라떼"])
        months   : 조회 기간(개월)
        time_unit: "date" | "week" | "month"

    Returns:
        {"keyword": str, "direction": "상승|하락|유지",
         "latest_ratio": float, "series": [...], "source": "naver|mock"}
    """
    cid = os.getenv("NAVER_CLIENT_ID")
    csec = os.getenv("NAVER_CLIENT_SECRET")
    end = date.today()
    start = end - timedelta(days=30 * months)

    if not (cid and csec):
        return _mock_trend(keywords[0] if keywords else "트렌드")

    body = {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "timeUnit": time_unit,
        "keywordGroups": [{"groupName": kw, "keywords": [kw]} for kw in keywords[:5]],
    }
    req = urllib.request.Request(
        _URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "X-Naver-Client-Id": cid,
            "X-Naver-Client-Secret": csec,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return _summarize(data)
    except Exception as e:  # 네트워크/쿼터 실패 시에도 파이프라인은 계속 진행
        print(f"[trend] 네이버 API 실패 → mock 폴백: {e}")
        return _mock_trend(keywords[0] if keywords else "트렌드")


def _summarize(data: dict) -> dict:
    """API 응답에서 첫 키워드 그룹의 추세(상승/하락/유지)를 요약한다."""
    results = data.get("results", [])
    if not results or not results[0].get("data"):
        return _mock_trend("트렌드")
    series = results[0]["data"]           # [{period, ratio}, ...]
    first, last = series[0]["ratio"], series[-1]["ratio"]
    direction = "상승" if last > first * 1.1 else "하락" if last < first * 0.9 else "유지"
    return {
        "keyword": results[0]["title"],
        "direction": direction,
        "latest_ratio": round(last, 1),
        "series": series[-8:],
        "source": "naver",
    }


def _mock_trend(keyword: str) -> dict:
    # 상승 추세 예시 시계열(시연용)
    series = [{"period": f"2025-{m:02d}-01", "ratio": r}
              for m, r in zip(range(1, 9), [30, 35, 40, 52, 61, 70, 82, 95])]
    return {"keyword": keyword, "direction": "상승", "latest_ratio": 95.0,
            "series": series, "source": "mock"}


if __name__ == "__main__":
    t = fetch_trend(["여름 신메뉴", "아이스라떼"])
    print(f"키워드={t['keyword']} 추세={t['direction']} 최신지수={t['latest_ratio']} (source={t['source']})")
