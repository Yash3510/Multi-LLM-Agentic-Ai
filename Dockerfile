FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends python3-tk tesseract-ocr tesseract-ocr-eng poppler-utils && rm -rf /var/lib/apt/lists/*
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
ENV SOVEREIGN_DATA_DIR=/app/data
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --retries=5 CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/api/health', timeout=3)"
CMD ["python", "-m", "sovereign_ai", "--api", "--host", "0.0.0.0", "--port", "8000"]
