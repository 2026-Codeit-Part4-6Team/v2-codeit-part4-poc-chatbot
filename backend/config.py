# -*- coding: utf-8 -*-
"""config.py — config.yaml + .env 로드. 우선순위: 인자 > .env > yaml > 기본값."""
import os
import yaml
from dotenv import load_dotenv

load_dotenv()
_CFG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")


def load_config() -> dict:
    with open(_CFG_PATH, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    # 경로/키 등 환경 종속값은 .env로 덮어쓰기
    cfg["openai_api_key"] = os.getenv("OPENAI_API_KEY", "")
    cfg["naver_client_id"] = os.getenv("NAVER_CLIENT_ID", "")
    cfg["naver_client_secret"] = os.getenv("NAVER_CLIENT_SECRET", "")
    return cfg
