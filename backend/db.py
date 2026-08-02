# -*- coding: utf-8 -*-
"""
db.py — SQLite 연동 & CRUD (sqlite3 표준 패키지만 사용, SQLAlchemy 미사용)

설계 테이블 (김재헌 CASE 3 요구사항 반영):
  - users        : 사용자 정보(로그인)
  - payments     : 게시물 생성 건당 유료 결제 내역
  - generations  : 생성 요청/결과 로그 (무료=카피 / 유료=카피+이미지)

비밀번호는 평문 저장 금지 → SHA-256 해시 저장 (파트4-3 Ch7.2 원칙).
DB 파일은 상대경로(app.db)로 생성 → 컨테이너 Bind Mount 시 호스트에 영속.
모든 쿼리는 파라미터화(?)로 SQL 인젝션을 방지한다.
"""
import sqlite3
import hashlib
import hmac
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "app.db"))


# ── 연결 & 스키마 ──────────────────────────────────────────────────────────
def get_connection() -> sqlite3.Connection:
    """SQLite 연결 반환. FastAPI 멀티스레드 대응 위해 check_same_thread=False."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row              # 컬럼명으로 접근(dict 변환 편의)
    conn.execute("PRAGMA foreign_keys = ON")    # 외래키 제약 on
    return conn


def init_db() -> None:
    """테이블이 없으면 생성(IF NOT EXISTS → 여러 번 호출 안전)."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            store_name    TEXT,                  -- 가게 이름
            industry      TEXT,                  -- 업종(카페/식당/의류 등)
            credits       INTEGER DEFAULT 0,     -- 유료 크레딧(게시물 생성권) 잔액
            created_at    TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS payments (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            amount     INTEGER NOT NULL,          -- 결제 금액(원)
            credits    INTEGER NOT NULL,          -- 충전 크레딧 수
            method     TEXT DEFAULT 'mock',       -- 결제수단(POC=mock)
            status     TEXT DEFAULT 'paid',       -- paid / refunded
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS generations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            question    TEXT,                     -- 사용자 요청
            channel     TEXT,                     -- instagram / blog / banner
            plan        TEXT DEFAULT 'free',      -- free(카피) / paid(카피+이미지)
            copy_text   TEXT,                     -- 생성된 카피
            image_path  TEXT,                     -- 생성 이미지 경로(유료)
            tokens_used INTEGER DEFAULT 0,
            created_at  TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()


# ── 비밀번호 해시(평문 저장 금지) ─────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, stored_hash: str) -> bool:
    # 상수 시간 비교로 타이밍 공격 방지
    return hmac.compare_digest(hash_password(password), stored_hash)


# ── users : C R U D ────────────────────────────────────────────────────────
def create_user(username: str, password: str,
                store_name: str = "", industry: str = "") -> Optional[int]:
    """사용자 등록. username 중복이면 None."""
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO users (username, password_hash, store_name, industry, credits, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (username, hash_password(password), store_name, industry, 0,
             datetime.now().isoformat()),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user(username: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def authenticate(username: str, password: str) -> Optional[dict]:
    """로그인 검증. 성공 시 사용자 dict, 실패 시 None."""
    user = get_user(username)
    if user and verify_password(password, user["password_hash"]):
        return user
    return None


def update_user_profile(user_id: int, store_name: str, industry: str) -> bool:
    conn = get_connection()
    cur = conn.execute(
        "UPDATE users SET store_name = ?, industry = ? WHERE id = ?",
        (store_name, industry, user_id),
    )
    conn.commit()
    conn.close()
    return cur.rowcount > 0


def use_credit(user_id: int, amount: int = 1) -> bool:
    """유료 생성 시 크레딧 차감. 잔액 부족이면 False(차감 안 함)."""
    conn = get_connection()
    row = conn.execute("SELECT credits FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row or row["credits"] < amount:
        conn.close()
        return False
    conn.execute("UPDATE users SET credits = credits - ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()
    return True


def delete_user(user_id: int) -> bool:
    conn = get_connection()
    cur = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0


# ── payments : C R ─────────────────────────────────────────────────────────
def create_payment(user_id: int, amount: int, credits: int, method: str = "mock") -> int:
    """결제 기록 + 크레딧 충전을 한 커넥션(원자적)으로 처리."""
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO payments (user_id, amount, credits, method, status, created_at)
           VALUES (?, ?, ?, ?, 'paid', ?)""",
        (user_id, amount, credits, method, datetime.now().isoformat()),
    )
    conn.execute("UPDATE users SET credits = credits + ? WHERE id = ?", (credits, user_id))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def get_payments(user_id: int, limit: int = 50) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── generations : C R D ────────────────────────────────────────────────────
def create_generation(user_id: int, question: str, channel: str, plan: str,
                      copy_text: str, image_path: str = "", tokens_used: int = 0) -> int:
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO generations
           (user_id, question, channel, plan, copy_text, image_path, tokens_used, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, question, channel, plan, copy_text, image_path, tokens_used,
         datetime.now().isoformat()),
    )
    conn.commit()
    gid = cur.lastrowid
    conn.close()
    return gid


def get_generations(user_id: int, limit: int = 20) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM generations WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_generation(gen_id: int, user_id: int) -> bool:
    """본인 소유 생성물만 삭제(user_id 조건으로 소유권 확인)."""
    conn = get_connection()
    cur = conn.execute(
        "DELETE FROM generations WHERE id = ? AND user_id = ?", (gen_id, user_id)
    )
    conn.commit()
    conn.close()
    return cur.rowcount > 0


def get_stats() -> dict:
    """전체 사용 통계(관리자 대시보드용) — 집계 한 번에."""
    conn = get_connection()
    row = conn.execute("""
        SELECT
            (SELECT COUNT(*) FROM users)                         AS total_users,
            (SELECT COUNT(*) FROM generations)                   AS total_generations,
            (SELECT COUNT(*) FROM generations WHERE plan='paid') AS paid_generations,
            (SELECT COALESCE(SUM(amount),0) FROM payments)       AS total_revenue
    """).fetchone()
    conn.close()
    return dict(row)


# 직접 실행 시 스키마 생성 + 스모크 테스트
if __name__ == "__main__":
    DB_PATH = os.path.join(os.path.dirname(__file__), "smoke_test.db")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()

    uid = create_user("minjae", "pw1234", store_name="민재커피", industry="카페")
    print("user 생성:", uid, "| 중복 재생성(None 기대):", create_user("minjae", "x"))
    print("로그인 성공:", authenticate("minjae", "pw1234") is not None)
    print("로그인 실패:", authenticate("minjae", "wrong") is None)

    pid = create_payment(uid, amount=1000, credits=1)
    print("결제 생성:", pid, "| 크레딧:", get_user_by_id(uid)["credits"])
    print("크레딧 차감:", use_credit(uid, 1), "| 잔액:", get_user_by_id(uid)["credits"])
    print("잔액부족 차감(False 기대):", use_credit(uid, 1))

    gid = create_generation(uid, "여름 신메뉴 홍보", "instagram", "paid",
                            "시원한 여름, 민재커피의 새로운 시작", "output/img_1.png", 320)
    print("생성 로그:", gid, "| 목록 수:", len(get_generations(uid)))
    print("통계:", get_stats())
    os.remove(DB_PATH)
    print("스모크 테스트 통과 ✅")
