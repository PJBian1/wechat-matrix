# ── Stage 1: Build frontend ──
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python runtime ──
FROM python:3.12-slim
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY app/ app/
COPY init_db.py .

# 复制前端构建产物
COPY --from=frontend-build /app/frontend/dist/ frontend/dist/

# 创建上传目录
RUN mkdir -p /data/uploads

EXPOSE 8000

CMD ["sh", "-c", "python init_db.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
