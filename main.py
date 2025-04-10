import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from gtts import gTTS
from deep_translator import GoogleTranslator
from dotenv import load_dotenv
import asyncio

load_dotenv()
TOKEN = os.getenv("TOKEN")

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Отправь мне слово или фразу, и я:\n"
        "- Определю язык 🌍\n"
        "- Переведу в нужную сторону 🔄\n" 
        "- Произнесу его вслух 🎙️"
    )

# Обработка текста
async def translate_and_pronounce(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()

    if not text:
        await update.message.reply_text("Пожалуйста, отправь слово или фразу.")
        return

    try:
        is_russian = any('\u0400' <= char <= '\u04FF' for char in text)

        if is_russian:
            translation = GoogleTranslator(source='ru', target='en').translate(text)
            pronunciation_text = translation
        else:
            translation = GoogleTranslator(source='en', target='ru').translate(text)
            pronunciation_text = text

        # Генерация голосового сообщения
        tts = gTTS(text=pronunciation_text, lang="en")
        filename = "pronounce.mp3"
        tts.save(filename)

        await update.message.reply_text(
            f"🔹 *Исходный текст:* {text}\n"
            f"🔸 *Перевод:* {translation}\n"
            f"🎙️ *Произношение (на английском):*",
            parse_mode="Markdown"
        )

        with open(filename, "rb") as audio:
            await update.message.reply_voice(voice=audio)

        os.remove(filename)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка при обработке: {e}")

# Регистрируем хендлеры
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_and_pronounce))

# Вебхук маршрут
@app.route(f'/{TOKEN}', methods=['POST'])
async def webhook() -> str:
    if request.method == "POST":
        await application.update_queue.put(Update.de_json(request.get_json(force=True), application.bot))
        return "ok"


# Запуск вебхука

if __name__ == '__main__':
    WEBHOOK_URL = f"https://rejenta-english-bot.onrender.com/{TOKEN}"

    async def setup():
        await application.bot.set_webhook(WEBHOOK_URL)
        print("Вебхук установлен")

    asyncio.run(setup())  # Устанавливаем вебхук
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

