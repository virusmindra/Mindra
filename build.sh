#!/usr/bin/env bash

# Скачиваем и устанавливаем ffmpeg локально
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz | tar -xJ
mkdir -p ./bin
mv ffmpeg-*-amd64-static/ffmpeg ./bin/
chmod +x ./bin/ffmpeg

# Добавляем ffmpeg в PATH
export PATH=$PATH:$(pwd)/bin

# Обновляем pip и setuptools
pip install --upgrade pip setuptools wheel

# Устанавливаем зависимости
pip install -r requirements.txt
