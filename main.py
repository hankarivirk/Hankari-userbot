import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from telethon import TelegramClient
from telethon.sessions import StringSession

# Config from Heroku/GitHub secrets
API_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)
running_clients = {}

async def start_userbot(user_id, string_session):
    client = TelegramClient(StringSession(string_session), API_ID, API_HASH)
    await client.start()
    running_clients[user_id] = client
    print(f"[✅] Userbot started for {user_id}")

async def save_session(user_id, string_session):
    with open(f"{SESSIONS_DIR}/{user_id}.session", "w") as f:
        f.write(string_session)

async def load_sessions():
    for file in os.listdir(SESSIONS_DIR):
        if file.endswith(".session"):
            user_id = file.replace(".session", "")
            with open(f"{SESSIONS_DIR}/{file}", "r") as f:
                string_session = f.read().strip()
            await start_userbot(user_id, string_session)
    print("[♻] All saved sessions loaded.")

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.reply("🤖 Welcome! Use /login to start your own Userbot.")

@dp.message_handler(commands=["login"])
async def login_cmd(message: types.Message):
    await message.reply("📱 Send your **phone number** with country code.\nExample: `+1234567890`", parse_mode="Markdown")
    dp.register_message_handler(get_phone, state="get_phone", content_types=types.ContentTypes.TEXT)

async def get_phone(message: types.Message):
    phone = message.text.strip()
    await message.reply("📩 Now send the code you receive on Telegram.")
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()
    try:
        await client.send_code_request(phone)
        dp.register_message_handler(lambda m: get_code(m, phone, client), state="get_code", content_types=types.ContentTypes.TEXT)
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

async def get_code(message: types.Message, phone, client):
    code = message.text.strip()
    try:
        await client.sign_in(phone=phone, code=code)
        string_sess = client.session.save()
        await save_session(message.from_user.id, string_sess)
        await start_userbot(message.from_user.id, string_sess)
        await message.reply("✅ Userbot started and hosted automatically!")
    except Exception as e:
        await message.reply(f"❌ Login failed: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(load_sessions())
    executor.start_polling(dp, skip_updates=True)
