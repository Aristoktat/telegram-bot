import os
import time
import sqlite3
import asyncio
import yt_dlp
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiohttp import web

# ===== SOZLAMALAR =====
API_TOKEN = "6252362558:AAFzmD_nSmcj12XvPtCA-aeaBruQl3WTakI"
ADMINS = [689757167, 6252362558]

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Database ulash
db = sqlite3.connect("bot.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS movies (code TEXT PRIMARY KEY, title TEXT, file_id TEXT)")
db.commit()

# YouTube yuklash funksiyasi (Faqat Render xotirasi uchun xavfsiz qismi)
def download_yt(url):
    # Fayl nomi takrorlanmasligi uchun timestamp ishlatamiz
    file_name = f"temp_vid_{int(time.time())}.mp4"
    ydl_opts = {
        'format': 'best[ext=mp4][filesize<50M]/worst', # 50MB dan kichigini qidiradi
        'outtmpl': file_name,
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return file_name, info.get('title', 'YouTube Video')

# ===== ADMIN: LINK YUBORGANDA =====
@dp.message(F.from_user.id.in_(ADMINS), F.text.regexp(r'^https?://'))
async def handle_link(msg: types.Message):
    # Navbatdagi raqamni aniqlash
    cursor.execute("SELECT code FROM movies")
    rows = cursor.fetchall()
    numeric_codes = [int(r[0]) for r in rows if r[0].isdigit()]
    next_code = max(numeric_codes) + 1 if numeric_codes else 1
    
    status_msg = await msg.answer("🔍 Link tekshirilmoqda va yuklanmoqda...")
    
    file_path = None
    try:
        # Yuklab olish (asinxron rejimda server qotmasligi uchun)
        file_path, title = await asyncio.to_thread(download_yt, msg.text)
        
        if os.path.exists(file_path):
            # Telegramga yuborish
            video_input = types.FSInputFile(file_path)
            sent_msg = await bot.send_video(
                chat_id=msg.chat.id, 
                video=video_input, 
                caption=f"✅ Yuklandi!\n\n🎬 <b>{title}</b>\n🔑 Kodi: <code>{next_code}</code>"
            )
            
            # Bazaga file_id ni saqlash (faylni o'zini emas!)
            cursor.execute("INSERT INTO movies VALUES (?, ?, ?)", (str(next_code), title, sent_msg.video.file_id))
            db.commit()
            
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Fayl yuklanmadi (ehtimol 50MB dan katta).")

    except Exception as e:
        await status_msg.edit_text(f"❌ Xatolik: {str(e)}")
    
    finally:
        # Eng muhim joyi: SERVERDA JOY QOLDIRMASLIK UCHUN FAYLNI O'CHIRAMIZ
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            print(f"DEBUG: {file_path} serverdan o'chirildi.")

# ===== QIDIRUV =====
@dp.message(F.text.isdigit())
async def search_movie(msg: types.Message):
    code = msg.text.strip()
    cursor.execute("SELECT title, file_id FROM movies WHERE code=?", (code,))
    res = cursor.fetchone()
    
    if res:
        title, file_id = res
        await bot.send_video(msg.chat.id, video=file_id, caption=f"🎬 {title}\n🔑 Kodi: {code}")
    else:
        await msg.answer("Bu kod bilan hech narsa topilmadi.")

# Render uxlab qolmasligi uchun Web Server
async def handle_ping(request):
    return web.Response(text="Bot is running")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000)))
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
