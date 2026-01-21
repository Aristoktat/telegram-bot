import os
import time
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiohttp import web
from dotenv import load_dotenv
# .env faylidan yuklash (agar serverda ishlatsangiz)
load_dotenv()
# ===== SOZLAMALAR =====
API_TOKEN = os.getenv("BOT_TOKEN", "6252362558:AAFzmD_nSmcj12XvPtCA-aeaBruQl3WTakI")
ADMINS = [689757167]
CHANNELS = [-1003537169311]
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
# ===== DATABASE =====
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
cursor.execute("CREATE TABLE IF NOT EXISTS movies (code TEXT PRIMARY KEY, title TEXT, file_id TEXT)")
conn.commit()
# ===== TUGMALAR =====
def get_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="📢 Reklama")],
            [KeyboardButton(text="➕ Kino qo'shish yordami")]
        ],
        resize_keyboard=True
    )
def get_user_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="ℹ️ Ma'lumot"), KeyboardButton(text="🔍 Qanday qidirish?")]
        ],
        resize_keyboard=True
    )
# ===== FUNKSIYALAR =====
async def check_sub(user_id):
    if not CHANNELS: return True
    try:
        for ch in CHANNELS:
            member = await bot.get_chat_member(chat_id=ch, user_id=user_id)
            if member.status in ["left", "kicked"]: return False
        return True
    except: return False
# ===== HANDLERS =====
@dp.message(Command("start"))
async def start(msg: types.Message):
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?)", (msg.from_user.id,))
    conn.commit()
    
    is_admin = msg.from_user.id in ADMINS
    menu = get_admin_menu() if is_admin else get_user_menu()
    
    if is_admin or await check_sub(msg.from_user.id):
        await msg.answer("🎬 <b>Kino botiga xush kelibsiz!</b>\n\nKino kodini yuboring:", reply_markup=menu)
    else:
        kb_inline = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanal", url="https://t.me/Islomiy_kinolar_20")],
            [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check")]
        ])
        await msg.answer("Botdan foydalanish uchun kanalga a’zo bo‘ling:", reply_markup=kb_inline)
@dp.callback_query(F.data == "check")
async def check_callback(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await call.message.answer("✅ Rahmat! Endi kino kodini yuboring.", reply_markup=get_user_menu())
    else:
        await call.answer("❌ A’zo emassiz", show_alert=True)
@dp.message(F.text == "📊 Statistika")
async def stat(msg: types.Message):
    if msg.from_user.id in ADMINS:
        cursor.execute("SELECT COUNT(*) FROM users")
        u = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM movies")
        m = cursor.fetchone()[0]
        await msg.answer(f"📊 <b>Statistika:</b>\n\n👤 Foydalanuvchilar: {u}\n🎬 Kinolar: {m}")
@dp.message(F.text == "📢 Reklama")
async def ads_help(msg: types.Message):
    if msg.from_user.id in ADMINS:
        await msg.answer("Reklama yuborish uchun: <code>/send Xabar matni</code>")
@dp.message(Command("send"))
async def send_ads(msg: types.Message):
    if msg.from_user.id not in ADMINS: return
    txt = msg.text.replace("/send", "").strip()
    if not txt: return await msg.answer("Xabar yozing!")
    
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    await msg.answer("🚀 Yuborilmoqda...")
    done, fail = 0, 0
    for (uid,) in users:
        try:
            await bot.send_message(uid, txt)
            done += 1
            await asyncio.sleep(0.05)
        except: fail += 1
    await msg.answer(f"✅ Tugadi. Yetkazildi: {done}, Bloklangan: {fail}")
@dp.message(F.video)
async def add_movie(msg: types.Message):
    if msg.from_user.id not in ADMINS: return
    
    cursor.execute("SELECT code FROM movies")
    codes = [int(c[0]) for c in cursor.fetchall() if str(c[0]).isdigit()]
    next_code = max(codes) + 1 if codes else 1
    
    title = msg.caption if msg.caption else f"Kino #{next_code}"
    code = str(next_code)
    
    if msg.caption and "|" in msg.caption:
        try:
            c, t = map(str.strip, msg.caption.split("|", 1))
            code, title = c, t
        except: pass
    cursor.execute("INSERT OR REPLACE INTO movies VALUES (?, ?, ?)", (code, title, msg.video.file_id))
    conn.commit()
    await msg.answer(f"✅ Qo'shildi: {title}\n🔑 Kod: <code>{code}</code>")
@dp.message()
async def search(msg: types.Message):
    if not msg.text: return
    if msg.from_user.id not in ADMINS and not await check_sub(msg.from_user.id):
        return await msg.answer("Avval kanalga a'zo bo'ling!")
        
    cursor.execute("SELECT title, file_id FROM movies WHERE code=?", (msg.text.strip(),))
    res = cursor.fetchone()
    if res:
        await bot.send_video(msg.from_user.id, res[1], caption=f"🎬 <b>{res[0]}</b>\n\n@Islomiy_kinolar_20")
    elif msg.text not in ["ℹ️ Ma'lumot", "🔍 Qanday qidirish?", "➕ Kino qo'shish yordami"]:
        await msg.answer("😔 Kino topilmadi")
# ===== WEB SERVER & RUN =====
async def handle(request): return web.Response(text="Bot is running")
async def main():
    app = web.Application(); app.router.add_get("/", handle)
    runner = web.AppRunner(app); await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000)))
    await asyncio.gather(site.start(), dp.start_polling(bot))
if __name__ == "__main__":
    asyncio.run(main())
