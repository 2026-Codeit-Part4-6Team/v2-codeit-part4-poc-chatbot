# -*- coding: utf-8 -*-
"""
main.py — FastAPI 백엔드 (파트4-3 Ch8 CORS/API키 + Ch10 라우팅 패턴 계승)

엔드포인트:
  GET  /                     헬스체크
  POST /auth/register        회원가입              [김재헌 CASE2]
  POST /auth/login           로그인
  GET  /users/{id}           사용자 조회 (CRUD-R)
  PATCH/users/{id}           프로필 수정 (CRUD-U)
  POST /payments             결제(크레딧 충전)      [김재헌 CASE2/3]
  GET  /payments/{user_id}   결제내역 조회
  POST /generate             광고 생성(무료/유료)   ← LangGraph 파이프라인 호출
  GET  /generations/{uid}    생성 이력 (CRUD-R)
  DELETE /generations/{gid}  생성 이력 삭제 (CRUD-D)
  GET  /stats                전체 통계(관리자)

DB는 sqlite3(db.py)만 사용. 유료 생성은 크레딧을 차감하고 결제/생성 로그를 남긴다.
"""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from typing import Optional
import os

import db
from pipeline import get_ai_response
from config import load_config

app = FastAPI(title="AdCopilot POC API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # POC: 개발 편의. 배포 시 Streamlit 주소로 좁힐 것.
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 유료 생성 이미지를 HTTP 로 서빙 ────────────────────────────────────────────
# 분리 배포(Cloud Run 백엔드 ↔ Streamlit Cloud 프론트)에서는 프론트가 백엔드의
# 파일시스템을 볼 수 없다. 그래서 백엔드가 /static/xxx.png 로 이미지를 URL 서빙하고,
# /generate 응답에 절대경로(image_path) 대신 절대 URL(image_url)을 함께 실어 보낸다.
# Cloud Run 컨테이너 파일시스템은 휘발성이므로 쓰기 가능한 /tmp 하위에 둔다.
_STATIC_DIR = os.getenv("STATIC_DIR", "/tmp/adcopilot_output")
os.makedirs(_STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

# API 키 인증(파트4-3 Ch8). 환경변수 API_KEYS(콤마구분). 없으면 인증 비활성(개발 편의).
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_VALID_KEYS = set(k for k in os.getenv("API_KEYS", "").split(",") if k)


def verify_api_key(api_key: str = Depends(_api_key_header)):
    if not _VALID_KEYS:            # 키 미설정 → 개발 모드(검증 skip)
        return "dev"
    if api_key is None:
        raise HTTPException(status_code=401, detail="X-API-Key 헤더가 필요합니다")
    if api_key not in _VALID_KEYS:
        raise HTTPException(status_code=403, detail="유효하지 않은 API 키입니다")
    return api_key


@app.on_event("startup")
def _startup():
    db.init_db()                  # 서버 시작 시 테이블 보장


# ── 스키마 ──
class RegisterReq(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=4, max_length=100)
    store_name: str = ""
    industry: str = ""

class LoginReq(BaseModel):
    username: str
    password: str

class ProfileReq(BaseModel):
    store_name: str
    industry: str

class PaymentReq(BaseModel):
    user_id: int
    amount: int = 1000            # 1건 1,000원 가정
    credits: int = 1

class GenerateReq(BaseModel):
    user_id: int
    question: str
    channel: str = "instagram"    # instagram / blog / banner
    plan: str = "free"            # free / paid
    history: list[dict] = []
    use_trend: bool = True
    use_competitor: bool = True
    use_benchmark: bool = True


# ── 헬스 ──
@app.get("/")
def root():
    return {"status": "ok", "service": "AdCopilot POC"}


# ── Auth ──
@app.post("/auth/register")
def register(req: RegisterReq, _=Depends(verify_api_key)):
    uid = db.create_user(req.username, req.password, req.store_name, req.industry)
    if uid is None:
        raise HTTPException(status_code=409, detail="이미 존재하는 사용자명입니다")
    return {"user_id": uid, "username": req.username}


@app.post("/auth/login")
def login(req: LoginReq, _=Depends(verify_api_key)):
    user = db.authenticate(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="사용자명 또는 비밀번호가 올바르지 않습니다")
    return {"user_id": user["id"], "username": user["username"],
            "store_name": user["store_name"], "industry": user["industry"],
            "credits": user["credits"]}


# ── Users CRUD ──
@app.get("/users/{user_id}")
def read_user(user_id: int, _=Depends(verify_api_key)):
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    user.pop("password_hash", None)     # 해시는 응답에서 제외
    return user


@app.patch("/users/{user_id}")
def update_user(user_id: int, req: ProfileReq, _=Depends(verify_api_key)):
    if not db.update_user_profile(user_id, req.store_name, req.industry):
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return {"message": "프로필이 수정되었습니다"}


# ── Payments ──
@app.post("/payments")
def pay(req: PaymentReq, _=Depends(verify_api_key)):
    if not db.get_user_by_id(req.user_id):
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    pid = db.create_payment(req.user_id, req.amount, req.credits)
    bal = db.get_user_by_id(req.user_id)["credits"]
    return {"payment_id": pid, "credits_balance": bal}


@app.get("/payments/{user_id}")
def payments(user_id: int, _=Depends(verify_api_key)):
    return db.get_payments(user_id)


# ── Generate (파이프라인 호출) ──
@app.post("/generate")
def generate(req: GenerateReq, request: Request, _=Depends(verify_api_key)):
    user = db.get_user_by_id(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    # 유료 플랜: 크레딧 선차감(부족하면 402)
    if req.plan == "paid":
        if not db.use_credit(req.user_id, 1):
            raise HTTPException(status_code=402,
                                detail="크레딧이 부족합니다. 결제 후 이용해 주세요")

    cfg = {**load_config(), "plan": req.plan, "channel": req.channel,
           "use_trend": req.use_trend, "use_competitor": req.use_competitor,
           "use_benchmark": req.use_benchmark, "industry": user["industry"]}

    result = get_ai_response(
        req.question, history=req.history,
        industry=user["industry"], store_name=user["store_name"], config=cfg,
    )

    # ── 이미지 경로 → 공개 URL 변환 ──
    # 파이프라인은 이미지 파일의 서버 절대경로(image_path)를 반환한다.
    # 분리 배포에서는 프론트가 그 경로에 접근할 수 없으므로, 파일명만 뽑아
    # /static/<파일명> 형태의 절대 URL(image_url)을 응답에 추가한다.
    img_path = result.get("image_path", "")
    if img_path:
        fname = os.path.basename(img_path)
        # PUBLIC_BASE_URL 이 있으면 그걸 쓰고(권장), 없으면 요청 헤더 기반으로 유추.
        base = os.getenv("PUBLIC_BASE_URL", "").rstrip("/") or str(request.base_url).rstrip("/")
        result["image_url"] = f"{base}/static/{fname}"

    # 반문(꼬리질문)이면 생성 로그를 남기지 않고 그대로 반환
    if result["is_clarification"]:
        return result

    # 생성 로그 저장(CRUD-C)
    gid = db.create_generation(
        req.user_id, req.question, req.channel, req.plan,
        result["answer"], result.get("image_path", ""), result["tokens_used"],
    )
    result["generation_id"] = gid
    return result


# ── Generations CRUD ──
@app.get("/generations/{user_id}")
def list_generations(user_id: int, _=Depends(verify_api_key)):
    return db.get_generations(user_id)


@app.delete("/generations/{gen_id}")
def remove_generation(gen_id: int, user_id: int, _=Depends(verify_api_key)):
    if not db.delete_generation(gen_id, user_id):
        raise HTTPException(status_code=404, detail="생성물을 찾을 수 없습니다")
    return {"message": "삭제되었습니다"}


# ── Stats ──
@app.get("/stats")
def stats(_=Depends(verify_api_key)):
    return db.get_stats()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
