FROM python:3.12-slim
WORKDIR /app/backend
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
COPY backend/requirements.txt backend/requirements.lock backend/requirements-pipeline.lock ./
RUN pip install --no-cache-dir -r requirements.lock -r requirements-pipeline.lock
COPY pipeline /app/pipeline
COPY backend .
RUN useradd --create-home appuser && mkdir -p /app/storage && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
