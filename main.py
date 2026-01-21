import os
import sqlite3
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# SIZNING YAKUNIY MA'LUMOTLARINGIZ
API_TOKEN = '7607759837:AAExI6W2Y66r1m7N6K691B6Yk6fO0wYqW6A'
ADMIN_ID = 689757167  # Sizning ID raqamingiz muvaffaqiyatli kiritildi
CHANNELS = ['@Islomiy_kinolar_20']

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Ma'lumotlar bazasini sozlash (SQLite)
conn = sqlite3.connect('bot_database.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
cursor.execute('CREATE TABLE IF NOT EXISTS movies (code TEXT PRIMARY KEY, file_id TEXT)')
conn.commit()

# Obunani tekshirish funksiyasi
async def check_sub(user_id):
    try:
        for channel in CHANNELS:
            status = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if status.status == 'left':
                return False
        return True
    except Exception:
        # Agar bot kanalga admin bo'lmasa, tekshirish o'chib turadi (xato bermaslik uchun)
        return True

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    # Foydalanuvchini bazaga qo'shish
    try:
        cursor.execute('INSERT INTO users VALUES (?)', (message.from_id,))
        conn.commit()
    except:
        pass
    
    if await check_sub(message.from_id):
        await message.answer("✅ **Xush kelibsiz!**\n\nKino kodini raqamlar bilan yuboring.")
    else:
        markup = InlineKeyboardMarkup()
        for ch in CHANNELS:
            markup.add(InlineKeyboardButton(text="Kanalga a'zo bo'lish", url=f"https://t.me/{ch[1:]}"))
        markup.add(InlineKeyboardButton(text="Tekshirish ✅", callback_data="check_subscription"))
        await message.answer(f"Botdan foydalanish uchun {CHANNELS[0]} kanaliga a'zo bo'ling:", reply_markup=markup)

@dp.callback_query_handler(text="check_subscription")
async def check_callback(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await call.message.answer("✅ Rahmat! Endi kino kodini yuborishingiz mumkin.")
    else:
        await call.answer("❌ Siz hali kanalga a'zo bo'lmagansiz!", show_alert=True)

@dp.message_handler(commands=['stat'])
async def statistika(message: types.Message):
    if message.from_id == ADMIN_ID:
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        await message.answer(f"📊 **Bot statistikasi:**\n\nA'zolar soni: {count} ta")

@dp.message_handler(content_types=['video'])
async def add_movie(message: types.Message):
    if message.from_id == ADMIN_ID:
        movie_code = message.caption
        if movie_code:
            cursor.execute('INSERT OR REPLACE INTO movies VALUES (?, ?)', (movie_code, message.video.file_id))
            conn.commit()
            await message.answer(f"🎬 **Kino saqlandi!**\n\nKod: `{movie_code}`\n\nEndi foydalanuvchilar shu kodni yozsa, bot videoni yuboradi.")
        else:
            await message.answer("⚠️ **Xato!**\n\nVideoni yuborayotganda 'Izoh' (caption) qismiga kino kodini yozib yuboring.")

@dp.message_handler()
async def search_movie(message: types.Message):
    if not await check_sub(message.from_id):
        return await start(message)
        
    code = message.text
    cursor.execute('SELECT file_id FROM movies WHERE code=?', (code,))
    result = cursor.fetchone()
    if result:
        await bot.send_video(message.from_id, result[0], caption=f"🎥 **Kino topildi!**\nKod: {code}\n\n@Islomiy_kinolar_20")
    else:
        await message.answer("😔 **Kechirasiz, bunday kodli kino topilmadi.**\n\nKodni to'g'ri yozganingizni tekshiring.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
