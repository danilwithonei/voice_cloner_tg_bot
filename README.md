# Voice Cloner Telegram Bot 🎙️

Бот для клонирования голоса на базе [OmniVoice](https://github.com/k2-fsa/OmniVoice) и [OpenAI Whisper](https://github.com/openai/whisper).

## ✨ Возможности
*   **Транскрипция:** Преобразование аудио в текст.
*   **Клонирование голоса:** Генерация речи на основе короткого примера (голосового сообщения).
*   **Telegram-интерфейс:** Удобное взаимодействие через бота.
*   **GPU Ускорение:** Поддержка NVIDIA CUDA для быстрой обработки.

## 🛠 Стек технологий
*   **Backend:** Python 3.12, FastAPI, Uvicorn
*   **AI Models:** OmniVoice (K2-FSA), OpenAI Whisper (Base)
*   **Telegram Bot:** Aiogram 3.x
*   **Infrastructure:** Docker, Docker Compose, NVIDIA Container Toolkit (CUDA 12.8)

## 🚀 Быстрый старт

### Требования
*   Установленные Docker и Docker Compose.
*   NVIDIA GPU с установленными драйверами и [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

### Установка

1. Клонируйте репозиторий:
   ```bash
   git clone git@github.com:danilwithonei/voice_cloner_tg_bot.git
   cd voice_cloner_tg_bot
   ```

2. Создайте файл `.env` и добавьте ваш токен бота:
   ```env
   BOT_TOKEN=ваш_токен_от_BotFather
   ```

3. Запустите проект через Docker Compose:
   ```bash
   docker compose up --build -d
   ```

## 📂 Структура проекта
*   `main.py` — FastAPI сервер для обработки аудио и клонирования.
*   `bot.py` — Telegram-бот на aiogram.
*   `services/` — Логика работы с моделями (transcriber, cloner).
*   `temp_audio/` — Временная директория для обработки файлов.
*   `Dockerfile` & `docker-compose.yml` — Конфигурация для контейнеризации.

## 📝 Использование
1. Отправьте боту голосовое сообщение или аудиофайл.
2. Выберите действие: "Транскрибировать" или "Клонировать".
3. Если выбрано "Клонирование", бот сначала транскрибирует образец для лучшего качества, а затем попросит ввести текст для озвучки.
4. Получите результат в виде голосового сообщения!

---
Разработано с использованием передовых технологий синтеза речи.
