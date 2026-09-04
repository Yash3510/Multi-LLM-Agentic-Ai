FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends python3-tk && rm -rf /var/lib/apt/lists/*
COPY . .
ENV SOVEREIGN_DATA_DIR=/app/data
EXPOSE 8000
CMD ["python", "-m", "sovereign_ai", "--api", "--host", "0.0.0.0", "--port", "8000"]
