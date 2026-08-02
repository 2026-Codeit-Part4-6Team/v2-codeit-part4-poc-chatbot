# 강의 Ch11.6 frontend/Dockerfile 패턴 그대로
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# Streamlit 을 외부(0.0.0.0)에서 접속 가능하게 실행
CMD ["streamlit", "run", "streamlit_app.py", \
     "--server.address=0.0.0.0", "--server.port=8501"]
