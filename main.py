import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from aiohttp import web

# SOZLAMALAR
# Renderda portni os.environ orqali olish kerak
PORT = int(os.environ.get("PORT", 8080))
API_TOKEN = '6092087398:AAGZw3TVrL3-lhDMrGgTGzSquW1_kj3AaqY'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- WEB SERVER (Render aktiv turishi uchun) ---
async def handle(request):
    return web.Response(text="Bot ishlayapti!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Web server {PORT}-portda ishga tushdi.")

# --- KINO BAZASI ---
movies = {
    "1": "BAACAgIAAxkBAAIBy2lw4h8DfXD-5UrdgtEO8j5F9OTuAAKWiAACj_8JSwKIXfSeA1E8OAQ",
    "2": "BAACAgIAAxkBAAIBzmlw4kKR5fEH7M4brlj8--RpKajuAAKYiAACj_8JS8ahu1EXIkl1OAQ",
    "3": "BAACAgIAAxkBAAIB0mlw4kJx8OYGBP_kEsRlJfUP9hwqAAKciAACj_8JSzSD672LXumiOAQ",
    "4": "BAACAgIAAxkBAAIB1Glw4kKQA9WwpZZMWnBk058SqhvUAAKfiAACj_8JS_iqB_wg5t5EOAQ",
    "5": "BAACAgIAAxkBAAIB02lw4kJeX6pNm4OXY-s3I6GrKQABkQACnYgAAo__CUuyIqjpufIMKzgE",
    "6": "BAACAgIAAxkBAAIB1Wlw4kIOygnLF0_IzjAMo7a-S5yQAAKgiAACj_8JS7Pmo5ozRqFnOAQ",
    "7": "BAACAgIAAxkBAAIB1mlw4kI-lu9WO3kJch3cOC9s4HDFAAKkiAACj_8JS9FwUK3ECugYOAQ",
    "8": "BAACAgIAAxkBAAIBz2lw4kJQDIQCvXcGHxVoQScX7Mi6AAKZiAACj_8JSzJK6a5N-s9kOAQ",
    "9": "BAACAgIAAxkBAAIB0Glw4kIosKbGjlKMy5LkPuBKeKfsAAKaiAACj_8JS68Nd1Gb7iWTOAQ",
    "10": "BAACAgIAAxkBAAIB0Wlw4kJ15KHr6BIDKlNQVwvMN6xaAAKbiAACj_8JS42_Vhb7VoaXOAQ",
}

@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "🎬 **Kino Botga xush kelibsiz!**\n\n"
        "Bot Render serverida ishga tushirildi. Kino kodini yuboring."
    )

@dp.message(F.text)
async def send_movie(message: Message):
    user_code = message.text
    if user_code in movies:
        try:
            await message.answer_video(
                video=movies[user_code], 
                caption=f"✅ So'ralgan kino (Kod: {user_code})"
            )
        except Exception as e:
            await message.answer(f"❌ Xatolik: {e}")
    else:
        await message.answer("❌ Bunday kodli kino topilmadi.")

async def main():
    # Web serverni alohida boshlash
    await start_web_server()
    
    # Bot pollingni boshlash
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")



