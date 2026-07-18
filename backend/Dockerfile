FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-spa libpq5 curl gosu \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .
RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && sed -i 's/\r$//' /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh \
    && chown -R app:app /app

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "120"]
