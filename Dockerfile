FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY backend /app/backend
COPY backend/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt || true \
 && pip install --no-cache-dir fastapi uvicorn[standard] pydantic pydantic-settings pandas numpy

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]