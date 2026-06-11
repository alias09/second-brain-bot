#!/bin/bash
# Скрипт запуска бота "Второй Мозг"

# Переходим в папку проекта
cd "/Users/kvp/Documents/ИИ проекты/Второй мозг"

# Прописываем пути к вашему Python и FFMPEG
export PATH="/Users/kvp/miniconda3/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

# Устанавливаем зависимости (если чего-то не хватает)
python3 -m pip install -r requirements.txt

# Запускаем бота
exec python3 bot/main.py
