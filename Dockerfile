FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x /app/docker/entrypoint.sh

EXPOSE 8003

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["uvicorn", "src.interface.http.main:app", "--host", "0.0.0.0", "--port", "8003"]
