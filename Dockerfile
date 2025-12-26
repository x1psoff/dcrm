FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Установка Python зависимостей
# Используем отдельный requirements для Docker
COPY requirements.docker.txt /tmp/requirements.txt
# Печатаем для отладки, чтобы убедиться, что mysql не тянется
RUN echo "=== USING REQUIREMENTS (docker) ===" && \
    cat /tmp/requirements.txt && \
    (grep -i "mysql" /tmp/requirements.txt || true) && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Копирование проекта
COPY . .

# Открываем порт
EXPOSE 8000

# Запуск Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
