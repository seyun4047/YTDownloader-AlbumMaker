FROM python:3.12-slim
WORKDIR /app

# ffmpeg 설치 (yt-dlp 오디오/비디오 변환 필수)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 코드 복사
COPY . .

EXPOSE 10210

# uvicorn으로 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10210"]