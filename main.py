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
load_dotenv()
# ===== SOZLAMALAR =====
API_TOKEN = os.getenv("BOT_TOKEN", "6092087398:AAGZw3TVrL3-lhDMrGgTGzSquW1_kj3AaqY")
ADMINS = [689757167, 6252362558]
CHANNELS = [-1003537169311]
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
# ===== DATABASE =====
db = sqlite3.connect("bot.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
cursor.execute("CREATE TABLE IF NOT EXISTS movies (code TEXT PRIMARY KEY, title TEXT, file_id TEXT)")
db.commit()
# ===== TUGMALAR =====
def get_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="📢 Reklama")],
            [KeyboardButton(text="➕ Kino qo'shish yordami"), KeyboardButton(text="💾 Bazani yuklash")]
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
# ===== OBUNA TEKSHIRISH =====
async def check_sub(user_id):
    if user_id in ADMINS: return True
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
    db.commit()
    is_admin = msg.from_user.id in ADMINS
    menu = get_admin_menu() if is_admin else get_user_menu()
    if await check_sub(msg.from_user.id):
        await msg.answer("🎬 <b>Xush kelibsiz!</b>\n\nKino kodini yuboring:", reply_markup=menu)
    else:
        kb_inline = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanal", url="https://t.me/Islomiy_kinolar_20")],
            [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
        ])
        await msg.answer("<b>Botdan foydalanish uchun kanalga a’zo bo‘ling!</b>", reply_markup=kb_inline)
@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await call.message.answer("✅ Rahmat! Kino kodini yuboring.", reply_markup=get_user_menu())
    else:
        await call.answer("❌ A’zo bo‘lmadingiz!", show_alert=True)
@dp.message(F.text == "📊 Statistika")
async def stat_cmd(msg: types.Message):
    if msg.from_user.id not in ADMINS: return
    cursor.execute("SELECT COUNT(*) FROM users"); u = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM movies"); m = cursor.fetchone()[0]
    await msg.answer(f"📊 <b>Statistika:</b>\n👤 {u} ta foydalanuvchi\n🎬 {m} ta kino")
@dp.message(Command("send"))
async def send_ads(msg: types.Message):
    if msg.from_user.id not in ADMINS: return
    text = msg.text.replace("/send", "").strip()
    if not text: return await msg.answer("❗ Reklama matni yozing!")
    cursor.execute("SELECT user_id FROM users"); users = cursor.fetchall()
    ok, bad = 0, 0
    await msg.answer(f"🚀 {len(users)} kishiga yuborilmoqda...")
    for (uid,) in users:
        try:
            await bot.send_message(uid, text)
            ok += 1
            await asyncio.sleep(0.05)
        except: bad += 1
    await msg.answer(f"✅ Tugadi. Yetkazildi: {ok}, Bloklangan: {bad}")
@dp.message(F.video)
async def handle_video(msg: types.Message):
    if msg.from_user.id not in ADMINS: return
    cursor.execute("SELECT code FROM movies")
    codes = [int(r[0]) for r in cursor.fetchall() if r[0].isdigit()]
    next_code = max(codes) + 1 if codes else 1
    if msg.caption and "|" in msg.caption:
        code, title = map(str.strip, msg.caption.split("|", 1))
    else:
        code, title = str(next_code), msg.caption or f"Kino #{next_code}"
    cursor.execute("INSERT OR REPLACE INTO movies VALUES (?, ?, ?)", (code, title, msg.video.file_id))
    db.commit()
    await msg.answer(f"✅ <b>Qo'shildi!</b>\n🔑 Kod: <code>{code}</code>\n🎬 Nomi: {title}")
@dp.message()
async def search_movie(msg: types.Message):
    if not msg.text or msg.text.startswith('/'): return
    if msg.text in ["📊 Statistika", "📢 Reklama", "➕ Kino qo'shish yordami", "ℹ️ Ma'lumot", "🔍 Qanday qidirish?", "💾 Bazani yuklash"]:
        # Menyudagi boshqa tugmalar uchun handlers...
        return
    if not await check_sub(msg.from_user.id): return await msg.answer("❗ Avval kanalga a'zo bo'ling!")
    cursor.execute("SELECT title, file_id FROM movies WHERE code=?", (msg.text.strip(),))
    res = cursor.fetchone()
    if res:
        await bot.send_video(msg.from_user.id, video=res[1], caption=f"🎬 <b>{res[0]}</b>\n\n@Islomiy_kinolar_20")
    else:
        await msg.answer("😔 Kino topilmadi.")
async def handle_ping(request): return web.Response(text="Online")
async def main_loop():
    app = web.Application(); app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app); await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000)))
    await asyncio.gather(site.start(), dp.start_polling(bot))
if __name__ == "__main__":
    asyncio.run(main_loop())
