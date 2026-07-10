FROM python:3.12-slim

WORKDIR /app

# تثبيت الاعتماديات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY backend/ ./backend/
COPY enjazi/ ./enjazi/
COPY config/ ./config/

RUN mkdir -p /app/db

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
