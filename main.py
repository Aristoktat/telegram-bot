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
# .env faylidan sozlamalarni yuklash
load_dotenv()
# ===== SOZLAMALAR =====
API_TOKEN = os.getenv("BOT_TOKEN", "6252362558:AAFzmD_nSmcj12XvPtCA-aeaBruQl3WTakI")
# Admin ID'larini ro'yxatga kiriting
ADMINS = [689757167, 6252362558] # Ikkinchi ID'ni ham qo'shib qo'ydim
# Majburiy obuna kanallari ID'si
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
    if user_id in ADMINS: # Adminlar har doim o'tadi
        return True
    if not CHANNELS:
        return True
    try:
        for ch in CHANNELS:
            member = await bot.get_chat_member(chat_id=ch, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        return True
    except Exception as e:
        print(f"Obuna tekshirishda xatolik: {e}")
        return False
# ===== START / BOOTSTRAP =====
@dp.message(Command("start"))
async def start(msg: types.Message):
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?)", (msg.from_user.id,))
    db.commit()
    
    is_admin = msg.from_user.id in ADMINS
    menu = get_admin_menu() if is_admin else get_user_menu()
    
    if await check_sub(msg.from_user.id):
        await msg.answer(
            f"🎬 <b>Xush kelibsiz!</b>\n\nKino kodini yuboring:",
            reply_markup=menu
        )
    else:
        # Obuna bo'lmaganlar uchun inline tugma
        kb_inline = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url="https://t.me/Islomiy_kinolar_20")],
            [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
        ])
        await msg.answer("<b>Botdan foydalanish uchun kanalga a’zo bo‘ling!</b>", reply_markup=kb_inline)
@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await call.message.answer("✅ Rahmat! Endi kino kodini yuboring.", reply_markup=get_user_menu())
    else:
        await call.answer("❌ Siz hali kanalga a’zo bo‘lmadingiz!", show_alert=True)
# ===== ADMIN PANEL FUNKSIYALARI =====
@dp.message(F.text == "📊 Statistika")
async def stat_cmd(msg: types.Message):
    if msg.from_user.id not in ADMINS: return
    cursor.execute("SELECT COUNT(*) FROM users")
    u_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM movies")
    m_count = cursor.fetchone()[0]
    await msg.answer(f"📊 <b>Bot statistikasi:</b>\n\n👤 Foydalanuvchilar: {u_count}\n🎬 Kinolar: {m_count}")
@dp.message(F.text == "💾 Bazani yuklash")
async def download_db(msg: types.Message):
    if msg.from_user.id not in ADMINS: return
    file = types.FSInputFile("bot.db")
    await msg.answer_document(file, caption="Bot ma'lumotlar bazasi (SQLite)")
@dp.message(Command("send"))
async def send_ads(msg: types.Message):
    if msg.from_user.id not in ADMINS: return
    text = msg.text.replace("/send", "").strip()
    if not text:
        return await msg.answer("❗ Reklama matni yozing. Masalan: <code>/send Salom hammaga!</code>")
    
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    await msg.answer(f"🚀 {len(users)} kishiga xabar yuborish boshlandi...")
    
    ok, bad = 0, 0
    for (uid,) in users:
        try:
            await bot.send_message(uid, text)
            ok += 1
            await asyncio.sleep(0.05)
        except:
            bad += 1
    await msg.answer(f"✅ Tugadi!\nYetkazildi: {ok}\nBloklangan: {bad}")
# ===== KINO QO'SHISH (ADMIN) =====
@dp.message(F.video)
async def handle_video(msg: types.Message):
    if msg.from_user.id not in ADMINS: return
    
    # Oxirgi raqamni aniqlash
    cursor.execute("SELECT code FROM movies")
    rows = cursor.fetchall()
    numeric_codes = [int(r[0]) for r in rows if r[0].isdigit()]
    next_code = max(numeric_codes) + 1 if numeric_codes else 1
    
    # Nomi va Kodini aniqlash
    if msg.caption and "|" in msg.caption:
        code, title = map(str.strip, msg.caption.split("|", 1))
    else:
        code = str(next_code)
        title = msg.caption if msg.caption else f"Kino #{code}"
        
    cursor.execute("INSERT OR REPLACE INTO movies VALUES (?, ?, ?)", (code, title, msg.video.file_id))
    db.commit()
    await msg.answer(f"✅ <b>Bazaga qo'shildi!</b>\n\n🔑 Kodi: <code>{code}</code>\n🎬 Nomi: {title}")
# ===== QIDIRISH (HAMMA UCHUN) =====
@dp.message()
async def search_movie(msg: types.Message):
    if not msg.text: return
    if msg.text in ["📊 Statistika", "📢 Reklama", "➕ Kino qo'shish yordami", "ℹ️ Ma'lumot", "🔍 Qanday qidirish?", "💾 Bazani yuklash"]:
        if msg.text == "ℹ️ Ma'lumot":
            await msg.answer("🤖 Ushbu bot orqali kinolarni maxsus kodlar bilan topishingiz mumkin.")
        elif msg.text == "🔍 Qanday qidirish?":
            await msg.answer("Kino topish uchun uning kodini (masalan: 12) botga yuboring.")
        elif msg.text == "➕ Kino qo'shish yordami" and msg.from_user.id in ADMINS:
            await msg.answer("Kino qo'shish uchun videoni botga yuboring. Avtomatik kod beriladi.")
        return
    # Obunani tekshirish
    if not await check_sub(msg.from_user.id):
        return await msg.answer("❗ Avval kanalga a'zo bo'ling!")
    # Qidiruv
    code = msg.text.strip()
    cursor.execute("SELECT title, file_id FROM movies WHERE code=?", (code,))
    res = cursor.fetchone()
    
    if res:
        title, file_id = res
        await bot.send_video(
            chat_id=msg.from_user.id,
            video=file_id,
            caption=f"🎬 <b>{title}</b>\n🔑 Kodi: <code>{code}</code>\n\n@Islomiy_kinolar_20"
        )
    else:
        await msg.answer("😔 Kechirasiz, ushbu kod bilan kino topilmadi.")
# ===== WEB SERVER (RENDER UCHUN) =====
async def handle_ping(request):
    return web.Response(text="Bot is online")
async def main_loop():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000)))
    await site.start()
    
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main_loop())
