# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend

ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
