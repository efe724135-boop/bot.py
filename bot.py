import asyncio
import os
import time
import re
from datetime import datetime, timedelta

import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, BotCommand
from aiogram.filters import Command

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = 8213465894
LOG_GROUP_ID = -1003592251366

DB_NAME = "bot.db"

WARN_LIMIT = 20
WARN_TRACK_TIME = 300  # 5 dakika

# ================= INIT =================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

tracked_users = {}  # warn limit sonrası takip modu


# ================= DATABASE =================

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS roles(
            user_id INTEGER PRIMARY KEY,
            level INTEGER
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS warns(
            user_id INTEGER PRIMARY KEY,
            count INTEGER
        )
        """)
        await db.commit()


async def get_role(user_id):
    if user_id == OWNER_ID:
        return 4

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT level FROM roles WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            if row:
                return row[0]
    return 0


async def set_role(user_id, level):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("REPLACE INTO roles(user_id, level) VALUES (?,?)", (user_id, level))
        await db.commit()


async def log(text):
    try:
        await bot.send_message(LOG_GROUP_ID, text)
    except:
        pass


# ================= TIME PARSER =================

def parse_time(text):
    match = re.match(r"(\d+)([mhd])", text)
    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)

    if unit == "m":
        return timedelta(minutes=value)
    if unit == "h":
        return timedelta(hours=value)
    if unit == "d":
        return timedelta(days=value)

    return None


# ================= COMMAND MENU =================

async def set_commands():
    await bot.set_my_commands([
        BotCommand("panel", "Admin Panel"),
        BotCommand("mute", "Mute (10m, 2h, 1d)"),
        BotCommand("tempban", "Geçici ban"),
        BotCommand("ban", "Kalıcı ban"),
        BotCommand("unban", "Ban kaldır"),
        BotCommand("warn", "Warn ver"),
        BotCommand("info", "Kullanıcı bilgisi"),
    ])


# ================= HOŞGELDİN =================

@dp.message(F.new_chat_members)
async def welcome(message: Message):
    await message.answer("""
Hoşgeldin 👋

Burası karanlık esprilerin, ters köşe mizahın ve filtresiz zekânın buluştuğu bir alan.
Mizah sert olabilir, espri karanlık olabilir ama illegal tek bir adım bile yoktur.

#KAOS
""")


# ================= INFO =================

@dp.message(Command("info"))
async def info(message: Message):
    user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    role = await get_role(user.id)

    roles = {
        4: "Owner 👑",
        3: "Super Admin 🔥",
        2: "Admin ⚡",
        1: "Mod 🛡",
        0: "Üye"
    }

    await message.answer(
        f"👤 {user.full_name}\n"
        f"🆔 {user.id}\n"
        f"🎖 Yetki: {roles.get(role)}"
    )


# ================= YETKİ =================

@dp.message(Command("yetki"))
async def yetki(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    if not message.reply_to_message:
        await message.answer("Reply yap.")
        return

    try:
        level = int(message.text.split()[1])
    except:
        await message.answer("Seviye gir (0-3)")
        return

    target = message.reply_to_message.from_user
    await set_role(target.id, level)

    await message.answer(f"{target.full_name} → Seviye {level}")
    await log(f"👑 Yetki değişti | {target.id} → {level}")


# ================= WARN =================

@dp.message(Command("warn"))
async def warn_user(message: Message):
    role = await get_role(message.from_user.id)
    if role < 2:
        return

    if not message.reply_to_message:
        return

    target = message.reply_to_message.from_user

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT count FROM warns WHERE user_id=?", (target.id,)) as cur:
            row = await cur.fetchone()

        count = row[0] + 1 if row else 1

        await db.execute("REPLACE INTO warns(user_id, count) VALUES (?,?)", (target.id, count))
        await db.commit()

    if count >= WARN_LIMIT:
        tracked_users[target.id] = time.time() + WARN_TRACK_TIME

        await message.answer(
            f"⚠ Warn limiti aşıldı.\n"
            f"{WARN_TRACK_TIME//60} dakika takip moduna alındı."
        )

        await log(f"⚠ TRACK MODE | {target.id}")
    else:
        await message.answer(f"⚠ Warn verildi ({count}/{WARN_LIMIT})")


# ================= TRACK MODE =================

@dp.message()
async def track_mode(message: Message):
    uid = message.from_user.id

    if uid in tracked_users:
        if time.time() < tracked_users[uid]:
            try:
                await message.delete()
            except:
                pass
        else:
            del tracked_users[uid]


# ================= MUTE =================

@dp.message(Command("mute"))
async def mute_user(message: Message):
    role = await get_role(message.from_user.id)
    if role < 2:
        return

    if not message.reply_to_message:
        return

    args = message.text.split()
    if len(args) < 2:
        return

    duration = parse_time(args[1])
    if not duration:
        return

    target = message.reply_to_message.from_user
    until = datetime.now() + duration

    await bot.restrict_chat_member(
        message.chat.id,
        target.id,
        until_date=until,
        permissions={"can_send_messages": False}
    )

    await message.answer(f"🔇 Susturuldu ({args[1]})")
    await log(f"🔇 MUTE | {target.id} | {args[1]}")


# ================= TEMPBAN =================

@dp.message(Command("tempban"))
async def tempban_user(message: Message):
    role = await get_role(message.from_user.id)
    if role < 2:
        return

    if not message.reply_to_message:
        return

    args = message.text.split()
    if len(args) < 2:
        return

    duration = parse_time(args[1])
    if not duration:
        return

    target = message.reply_to_message.from_user
    until = datetime.now() + duration

    await bot.ban_chat_member(
        message.chat.id,
        target.id,
        until_date=until
    )

    await message.answer(f"🚫 Tempban ({args[1]})")
    await log(f"🚫 TEMPBAN | {target.id} | {args[1]}")


# ================= BAN =================

@dp.message(Command("ban"))
async def ban_user(message: Message):
    role = await get_role(message.from_user.id)
    if role < 2:
        return

    if not message.reply_to_message:
        return

    target = message.reply_to_message.from_user

    await bot.ban_chat_member(message.chat.id, target.id)
    await message.answer("🚫 Banlandı.")
    await log(f"🚫 BAN | {target.id}")


# ================= UNBAN =================

@dp.message(Command("unban"))
async def unban_user(message: Message):
    role = await get_role(message.from_user.id)
    if role < 2:
        return

    if not message.reply_to_message:
        return

    target = message.reply_to_message.from_user

    await bot.unban_chat_member(message.chat.id, target.id)
    await message.answer("♻ Ban kaldırıldı.")
    await log(f"♻ UNBAN | {target.id}")


# ================= RUN =================

async def main():
    await init_db()
    await set_commands()
    print("ULTRA BOT AKTİF")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
