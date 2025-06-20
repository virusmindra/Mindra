#!/usr/bin/env bash

# Установка FFmpeg
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz | tar -xJ
mv ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/
chmod +x /usr/local/bin/ffmpeg

# Установка Python-зависимостей
pip install -r requirements.txt
