import os
import sqlite3
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# YANGILANGAN MA'LUMOTLAR
API_TOKEN = '6092087398:AAGZw3TVrL3-lhDMrGgTGzSquW1_kj3AaqY'
ADMIN_ID = 689757167 
CHANNELS = [-1003537169311] # Islomiy kinolar kanali IDsi

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# Ma'lumotlar bazasi
conn = sqlite3.connect('bot_database.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
cursor.execute('CREATE TABLE IF NOT EXISTS movies (code TEXT PRIMARY KEY, file_id TEXT)')
conn.commit()

# Render uchun kichik Web-server (Bot o'chib qolmasligi uchun)
async def handle(request):
    return web.Response(text="Bot is running!")

async def on_startup(dp):
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000)))
    await site.start()

# Obunani tekshirish
async def check_sub(user_id):
    try:
        for channel in CHANNELS:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status == 'left':
                return False
        return True
    except:
        return True

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    try:
        cursor.execute('INSERT INTO users VALUES (?)', (message.from_id,))
        conn.commit()
    except: pass
    
    if await check_sub(message.from_id):
        await message.answer("<b>✅ Xush kelibsiz!</b>\nKino kodini yuboring.")
    else:
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Kanalga o'tish", url="https://t.me/Islomiy_kinolar_20"))
        markup.add(InlineKeyboardButton("Tekshirish ✅", callback_data="check"))
        await message.answer("Botdan foydalanish uchun kanalimizga a'zo bo'ling:", reply_markup=markup)

@dp.callback_query_handler(text="check")
async def check_call(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await call.message.answer("✅ Rahmat! Endi kino kodini yuborishingiz mumkin.")
    else:
        await call.answer("❌ Siz hali a'zo emassiz!", show_alert=True)

@dp.message_handler(commands=['stat'])
async def stat(message: types.Message):
    if message.from_id == ADMIN_ID:
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        await message.answer(f"📊 <b>Bot statistikasi:</b>\nA'zolar: {count} ta")

@dp.message_handler(content_types=['video'])
async def add_movie(message: types.Message):
    if message.from_id == ADMIN_ID:
        if message.caption:
            cursor.execute('INSERT OR REPLACE INTO movies VALUES (?, ?)', (message.caption, message.video.file_id))
            conn.commit()
            await message.answer(f"🎬 <b>Kino bazaga qo'shildi!</b>\nKod: <code>{message.caption}</code>")
        else:
            await message.answer("⚠️ <b>Xato!</b>\nVideoni yuborayotganda izohiga (caption) kino kodini yozing!")

@dp.message_handler()
async def search(message: types.Message):
    if not await check_sub(message.from_id):
        return await start(message)
    
    cursor.execute('SELECT file_id FROM movies WHERE code=?', (message.text,))
    res = cursor.fetchone()
    if res:
        await bot.send_video(message.from_id, res[0], caption=f"🎥 Kino kodi: {message.text}\n\n@Islomiy_kinolar_20")
    else:
        await message.answer("😔 Bunday kodli kino topilmadi.")

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
