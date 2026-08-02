# 파트4-1 Docker 원칙 그대로: slim 베이스 · 레이어 캐싱 · 비밀값 분리 · .dockerignore
FROM python:3.11-slim
WORKDIR /app

# [우리 프로젝트 전용] 한글 폰트.
#   nodes/image_gen.py 가 /usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc 로
#   PIL 광고카드에 한글을 그린다. slim 이미지엔 이 폰트가 없어서, 없으면 한글이
#   □□□(두부)로 깨진다. fonts-noto-cjk 가 정확히 그 경로를 제공한다.
RUN apt-get update \
 && apt-get install -y --no-install-recommends fonts-noto-cjk \
 && rm -rf /var/lib/apt/lists/*

# 레이어 캐싱: requirements 를 먼저 복사 → 코드만 바뀌면 pip install 캐시 재사용
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 나머지 코드/설정/데이터 전부 복사 (config.yaml, data/*.json 포함)
COPY . .

# 컨테이너 로그가 실시간으로 보이도록(모델·그래프 로드 로그 확인용)
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Chapter 2에서 손으로 치던 명령을 컨테이너 시작 시 자동 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
