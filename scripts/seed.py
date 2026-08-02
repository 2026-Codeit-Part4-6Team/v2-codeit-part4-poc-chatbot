# -*- coding: utf-8 -*-
"""scripts/seed.py — 데모용 계정 시딩(demo/demo123, 카페, 크레딧 3)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import db
db.init_db()
if not db.get_user("demo"):
    uid = db.create_user("demo", "demo123", store_name="데모커피", industry="카페")
    db.create_payment(uid, amount=3000, credits=3)
    print("데모 계정 생성: demo / demo123 (크레딧 3)")
else:
    print("이미 존재: demo")
