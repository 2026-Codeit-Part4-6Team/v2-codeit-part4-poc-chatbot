# -*- coding: utf-8 -*-
"""
streamlit_app.py — AdCopilot POC 데모 UI

파트4-3 Ch7(로그인/세션) + Ch10.6(백엔드 API 호출) 패턴.
백엔드(FastAPI /generate 등)를 requests로 호출한다.
  - 로그인/회원가입
  - 사이드바 체크박스 라우터: 컨텍스트 소스 on/off + 플랜(무료/유료) + 채널
  - 생성 결과: 카피(+유료 이미지) 표시, 꼬리질문(반문) 처리, 대안(배리언트) 노출
  - 크레딧 결제, 생성 이력
"""
import streamlit as st
import requests
import os

API_URL = st.secrets.get("api", {}).get("backend_url", None) or os.environ.get("BACKEND_URL", "http://localhost:8000")
API_KEY = st.secrets.get("api", {}).get("api_key", None) or os.environ.get("API_KEY", "")
HEADERS = {"X-API-Key": API_KEY} if API_KEY else {}

st.set_page_config(page_title="AdCopilot — 소상공인 광고 생성", page_icon="📣", layout="centered")


def api(method, path, **kw):
    try:
        r = requests.request(method, f"{API_URL}{path}", headers=HEADERS, timeout=180, **kw)
        return r.status_code, r.json()
    except requests.exceptions.RequestException as e:
        return 0, {"detail": f"백엔드 연결 실패: {e}"}


# ── 세션 초기화 ──
for k, v in {"user": None, "history": [], "last": None}.items():
    st.session_state.setdefault(k, v)


# ── 로그인 화면 ──
def login_view():
    st.title("📣 AdCopilot")
    st.caption("소상공인을 위한 광고 카피·이미지 생성 (POC)")
    tab_login, tab_reg = st.tabs(["로그인", "회원가입"])

    with tab_login:
        with st.form("login"):
            u = st.text_input("사용자명")
            p = st.text_input("비밀번호", type="password")
            if st.form_submit_button("로그인", use_container_width=True):
                code, data = api("POST", "/auth/login", json={"username": u, "password": p})
                if code == 200:
                    st.session_state.user = data
                    st.rerun()
                else:
                    st.error(data.get("detail", "로그인 실패"))

    with tab_reg:
        with st.form("register"):
            u = st.text_input("사용자명 ")
            p = st.text_input("비밀번호 ", type="password")
            store = st.text_input("가게 이름")
            industry = st.selectbox("업종", ["카페", "식당", "의류", "기타"])
            if st.form_submit_button("회원가입", use_container_width=True):
                code, data = api("POST", "/auth/register",
                                 json={"username": u, "password": p, "store_name": store, "industry": industry})
                if code == 200:
                    st.success("가입 완료! 로그인 해주세요.")
                else:
                    st.error(data.get("detail", "가입 실패"))


# ── 메인 화면 ──
def main_view():
    user = st.session_state.user
    with st.sidebar:
        st.markdown(f"👤 **{user['username']}** ({user.get('store_name','')})")
        code, fresh = api("GET", f"/users/{user['user_id']}")
        credits = fresh.get("credits", user.get("credits", 0)) if code == 200 else 0
        st.metric("보유 크레딧", credits)
        if st.button("＋ 크레딧 충전(1건 1,000원)", use_container_width=True):
            api("POST", "/payments", json={"user_id": user["user_id"], "amount": 1000, "credits": 1})
            st.rerun()
        st.divider()

        st.markdown("**⚙️ 컨텍스트 소스 (체크박스 라우터)**")
        use_trend = st.checkbox("트렌드 조회(네이버 데이터랩)", value=True)
        use_comp = st.checkbox("경쟁사 리뷰 분석", value=True)
        use_bench = st.checkbox("업종 벤치마크 RAG", value=True)
        st.divider()
        plan = st.radio("플랜", ["free (카피만)", "paid (카피+이미지)"], horizontal=False)
        channel = st.selectbox("채널", ["instagram", "blog", "banner"])
        if st.button("로그아웃", use_container_width=True):
            st.session_state.user = None
            st.session_state.history = []
            st.rerun()

    st.title("📣 광고 콘텐츠 생성")

    # 이전 대화(꼬리질문 맥락) 표시
    for m in st.session_state.history:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    q = st.chat_input("예) 강남역 근처 카페인데 여름 신메뉴 홍보 문구 만들어줘")
    if q:
        st.session_state.history.append({"role": "user", "content": q})
        with st.chat_message("user"):
            st.write(q)
        with st.spinner("생성 중... (트렌드·경쟁사·벤치마크 수집 → 카피 3안 → 랭킹)"):
            code, res = api("POST", "/generate", json={
                "user_id": user["user_id"], "question": q,
                "channel": channel, "plan": "paid" if plan.startswith("paid") else "free",
                "history": st.session_state.history[:-1],
                "use_trend": use_trend, "use_competitor": use_comp, "use_benchmark": use_bench,
            })
        _render_result(code, res)


def _render_result(code, res):
    if code == 402:
        st.warning(res.get("detail")); return
    if code != 200:
        st.error(res.get("detail", "생성 실패")); return

    with st.chat_message("assistant"):
        if res.get("is_clarification"):
            # 꼬리질문(반문) — 조희원 기능
            st.info(res["answer"])
            st.session_state.history.append({"role": "assistant", "content": res["answer"]})
            return

        st.write(res["answer"])
        st.session_state.history.append({"role": "assistant", "content": res["answer"]})

        # 분리 배포에서는 백엔드가 반환한 image_url(HTTP)만 사용해야 한다.
        # image_path(서버 파일시스템 절대경로)는 로컬 docker-compose 에서만 유효.
        img_src = res.get("image_url") or res.get("image_path")
        if img_src:
            st.image(img_src, caption="생성된 광고 이미지(유료)", use_column_width=True)

        # 대안(배리언트) 노출 — 조희원 '다른 안 제시'
        if res.get("variants"):
            with st.expander(f"💡 다른 안 {len(res['variants'])}개 보기 (LLM Judge 최고점 {res.get('best_score')})"):
                for i, v in enumerate(res["variants"], 1):
                    st.markdown(f"**안 {i}.** {v}")
                if res.get("rank_reason"):
                    st.caption(f"선정 이유: {res['rank_reason']}")

        # 표현 주의 배지 — self_check
        if res.get("check_flags"):
            st.caption(f"⚠️ 표현 주의: {', '.join(res.get('risky_terms', []))} (광고 규제 확인 권장)")

        # 근거 소스
        if res.get("sources"):
            with st.expander("🔎 사용된 컨텍스트 근거"):
                for s in res["sources"]:
                    st.markdown(f"- **{s['type']}**")
        st.caption(f"⏱ {res.get('elapsed_sec')}초 · 토큰 {res.get('tokens_used')}")


if st.session_state.user is None:
    login_view()
else:
    main_view()
