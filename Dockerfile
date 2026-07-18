FROM node:22-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ .
ENV VITE_BASE=/static/
ENV VITE_SHOW_DEV_PIN=false
RUN npm run build

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_DEBUG=False \
    TZ=America/Costa_Rica

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-spa libpq5 curl gosu \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY backend/ .
COPY --from=frontend-build /frontend/dist /app/frontend_dist

RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && sed -i 's/\r$//' /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh \
    && chown -R app:app /app

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
