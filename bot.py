import asyncio
import logging
import os
import requests
import subprocess
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BufferedInputFile
from dotenv import load_dotenv

load_dotenv()

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")  # URL of your FastAPI app

# States
class VoiceAction(StatesGroup):
    choose_action = State()
    clone_text = State()

# Initialize bot and dispatcher
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

def convert_wav_to_ogg(wav_data: bytes) -> bytes:
    """Converts WAV audio data to OGG using ffmpeg."""
    ffmpeg_command = [
        "ffmpeg", "-i", "pipe:0",
        "-c:a", "libopus", "-b:a", "32k",
        "-f", "ogg", "pipe:1"
    ]
    try:
        process = subprocess.run(
            ffmpeg_command,
            input=wav_data,
            capture_output=True,
            check=True
        )
        logging.info(f"✅ OGG conversion successful: {len(process.stdout)} bytes")
        return process.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"ffmpeg error: {e.stderr.decode()}")
        raise
    except FileNotFoundError:
        logging.error("ffmpeg not found. Please install ffmpeg to enable voice message conversion.")
        raise


# Handlers
@dp.message(CommandStart())
async def start_handler(message: Message):
    """Greets the user and provides instructions."""
    await message.answer(
        "Привет! Я бот для клонирования голоса. "
        "Отправьте мне голосовое сообщение, и я его обработаю."
    )

@dp.message(F.voice | F.audio)
async def voice_handler(message: Message, state: FSMContext):
    """Handles incoming voice/audio messages."""
    file_id = message.voice.file_id if message.voice else message.audio.file_id
    await state.update_data(file_id=file_id)

    # Create keyboard for action selection
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Транскрибировать", callback_data="transcribe"),
            InlineKeyboardButton(text="Клонировать", callback_data="clone"),
        ]
    ])
    await message.reply(
        "Что вы хотите сделать с этим аудио?", reply_markup=keyboard
    )
    await state.set_state(VoiceAction.choose_action)


@dp.callback_query(VoiceAction.choose_action)
async def choose_action_handler(
    callback_query: CallbackQuery, state: FSMContext, bot: Bot
):
    """Handles the user's choice of action (transcribe or clone)."""
    action = callback_query.data
    await callback_query.answer()
    data = await state.get_data()
    file_id = data.get("file_id")

    if action == "transcribe":
        await transcribe_audio(callback_query.message, state, bot)
        await state.clear()
    elif action == "clone":
        await callback_query.message.edit_text("Транскрибирую аудио для повышения качества...")
        transcribed_text = await get_transcription(file_id, bot)
        if transcribed_text:
            await state.update_data(ref_text=transcribed_text)
            await callback_query.message.answer("Транскрипция завершена. Теперь введите текст, который вы хотите озвучить этим голосом.")
            await state.set_state(VoiceAction.clone_text)
        else:
            await callback_query.message.answer("Не удалось транскрибировать аудио. Попробуйте еще раз.")
            await state.clear()

async def get_transcription(file_id: str, bot: Bot) -> str | None:
    """Transcribes audio and returns the text."""
    try:
        file = await bot.get_file(file_id)
        file_path = file.file_path
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

        response = requests.get(file_url)
        response.raise_for_status()

        audio_file = {"audio_file": ("audio.oga", response.content, "audio/ogg")}

        api_response = requests.post(f"{API_URL}/transcribe", files=audio_file)
        api_response.raise_for_status()

        return api_response.json()["text"]
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
        return None

async def transcribe_audio(message: Message, state: FSMContext, bot: Bot):
    """Sends audio to the transcription service and replies with the text."""
    data = await state.get_data()
    file_id = data.get("file_id")
    transcribed_text = await get_transcription(file_id, bot)
    if transcribed_text:
        await message.reply(f"Транскрипция:\n\n{transcribed_text}")
    else:
        await message.reply("Не удалось обработать аудио. Попробуйте еще раз.")


@dp.message(VoiceAction.clone_text)
async def clone_text_handler(message: Message, state: FSMContext, bot: Bot):
    """Handles the target text for voice cloning."""
    target_text = message.text
    data = await state.get_data()
    file_id = data.get("file_id")
    ref_text = data.get("ref_text")

    await message.answer("Клонирую голос... Это может занять некоторое время.")

    try:
        file = await bot.get_file(file_id)
        file_path = file.file_path
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        
        # Download reference audio
        response = requests.get(file_url)
        response.raise_for_status()
        ref_audio_content = response.content

        # Prepare data for API request
        files = {"ref_audio": ("ref_audio.oga", ref_audio_content, "audio/ogg")}
        payload = {"target_text": target_text, "ref_text": ref_text}

        # Call the clone API
        api_response = requests.post(f"{API_URL}/clone", files=files, data=payload)
        api_response.raise_for_status()
        wav_audio = api_response.content

        # Convert WAV to OGG and send as a voice message
        try:
            ogg_audio = convert_wav_to_ogg(wav_audio)
            await message.reply_voice(BufferedInputFile(ogg_audio, filename="voice.ogg"))
        except Exception as e:
            logging.error(f"Audio conversion failed: {e}")
            await message.answer("Не удалось конвертировать аудио в голосовое сообщение. Отправляю как файл.")
            # Fallback to sending WAV file
            await message.reply_audio(BufferedInputFile(wav_audio, filename="cloned_voice.wav"))

    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
        await message.reply("Не удалось клонировать голос. Попробуйте еще раз.")
    finally:
        await state.clear()


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(token=BOT_TOKEN)
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
