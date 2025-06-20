#!/usr/bin/env bash

# Устанавливаем ffmpeg локально в директорию проекта
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz | tar -xJ
mkdir -p ./bin
mv ffmpeg-*-amd64-static/ffmpeg ./bin/
chmod +x ./bin/ffmpeg

# Добавляем ffmpeg в PATH
export PATH=$PATH:$(pwd)/bin

# Установка Python-зависимостей
pip install --upgrade pip
pip install --no-cache-dir --upgrade setuptools wheel
pip install -r requirements.txt
