# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем ffmpeg и зависимости
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Устанавливаем зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё остальное в контейнер
COPY . /app
WORKDIR /app

# Указываем команду запуска
CMD ["python", "main.py"]
