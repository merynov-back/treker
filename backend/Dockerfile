FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app/

# Не запускаємо застосунок від root
RUN useradd --create-home --uid 1000 app
USER app

# Міграції — окремий сервіс migrate у docker-compose, тут лише API
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
