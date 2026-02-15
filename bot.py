import telebot
import os
import json
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")  # veya direkt token yaz
bot = telebot.TeleBot(BOT_TOKEN)

OWNER_ID = 8213465894
LOG_CHANNEL_ID = -1003592251366  # LOG KANAL ID

ADMIN_FILE = "admins.json"

FLOOD_LIMIT = 5
FLOOD_TIME = 10

bad_words = ["amk", "orospu", "piç"]

user_messages = {}

# ==========================
# ADMIN DOSYA
# ==========================
def load_admins():
    try:
        with open(ADMIN_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_admins():
    with open(ADMIN_FILE, "w") as f:
        json.dump(admins, f)

admins = load_admins()

# ==========================
# YETKİ SİSTEMİ
# ==========================
def get_level(user_id, chat_id):

    if user_id == OWNER_ID:
        return 4

    if str(user_id) in admins:
        return admins[str(user_id)]

    try:
        member = bot.get_chat_member(chat_id, user_id)
        if member.status in ["creator", "administrator"]:
            return 1
    except:
        pass

    return 0

def is_protected(user_id):
    return user_id == OWNER_ID

# ==========================
# LOG
# ==========================
def log(text):
    try:
        bot.send_message(LOG_CHANNEL_ID, text)
    except:
        pass

# ==========================
# HOŞGELDİN
# ==========================
@bot.message_handler(content_types=['new_chat_members'])
def welcome(message):
    for user in message.new_chat_members:
        text = f"""
Hoşgeldin {user.first_name}

Burası karanlık esprilerin, ters köşe mizahın ve filtresiz zekânın buluştuğu bir alan.
Mizah sert olabilir, espri karanlık olabilir ama illegal tek bir adım bile yoktur.

#KAOS
by Guard System
"""
        bot.send_message(message.chat.id, text)

# ==========================
# INFO
# ==========================
@bot.message_handler(commands=['info'])
def info_user(message):

    if message.reply_to_message:
        user = message.reply_to_message.from_user
    else:
        user = message.from_user

    level = get_level(user.id, message.chat.id)

    roles = {
        4: "Owner 👑",
        3: "Super Admin 🔥",
        2: "Mod ⚡",
        1: "Admin 🛡",
        0: "Üye"
    }

    text = f"""
📌 KULLANICI BİLGİSİ

👤 İsim: {user.first_name}
🆔 ID: {user.id}
🎖 Yetki: {roles.get(level)}
"""

    bot.send_message(message.chat.id, text)

# ==========================
# YETKİ VER / AL
# ==========================
@bot.message_handler(commands=['yetki'])
def set_permission(message):

    if get_level(message.from_user.id, message.chat.id) < 4:
        return

    if not message.reply_to_message:
        bot.send_message(message.chat.id, "Bir kullanıcıya reply yap.")
        return

    try:
        level = int(message.text.split()[1])
    except:
        bot.send_message(message.chat.id, "Seviye gir: 0-3")
        return

    target = message.reply_to_message.from_user

    if is_protected(target.id):
        return

    if level == 0:
        if str(target.id) in admins:
            del admins[str(target.id)]
    else:
        admins[str(target.id)] = level

    save_admins()

    bot.send_message(message.chat.id, f"{target.first_name} yetki seviyesi {level} yapıldı.")
    log(f"⚙️ Yetki değişti: {target.id} → {level}")

# ==========================
# ADMİN LİSTESİ
# ==========================
@bot.message_handler(commands=['adminlist'])
def admin_list(message):

    if get_level(message.from_user.id, message.chat.id) < 4:
        return

    text = "👑 Yetkili Listesi\n\n"

    if not admins:
        text += "Ekstra yetkili yok."
    else:
        for uid, level in admins.items():
            text += f"{uid} → Seviye {level}\n"

    bot.send_message(message.chat.id, text)

# ==========================
# SİSTEM DURUMU
# ==========================
@bot.message_handler(commands=['durum'])
def system_status(message):

    if get_level(message.from_user.id, message.chat.id) < 4:
        return

    text = f"""
📊 SİSTEM DURUMU

Ekstra Admin: {len(admins)}
Flood Limit: {FLOOD_LIMIT}
Flood Süresi: {FLOOD_TIME} sn
Küfür Filtresi: Aktif
"""

    bot.send_message(message.chat.id, text)

# ==========================
# BAN
# ==========================
@bot.message_handler(commands=['ban'])
def ban_user(message):

    if get_level(message.from_user.id, message.chat.id) < 2:
        return

    if not message.reply_to_message:
        return

    target = message.reply_to_message.from_user

    if is_protected(target.id):
        return

    bot.ban_chat_member(message.chat.id, target.id)
    bot.send_message(message.chat.id, "Kullanıcı banlandı.")
    log(f"🚫 Ban: {target.id}")

# ==========================
# UNBAN
# ==========================
@bot.message_handler(commands=['unban'])
def unban_user(message):

    if get_level(message.from_user.id, message.chat.id) < 2:
        return

    try:
        user_id = int(message.text.split()[1])
    except:
        return

    if is_protected(user_id):
        return

    bot.unban_chat_member(message.chat.id, user_id)
    bot.send_message(message.chat.id, "Ban kaldırıldı.")
    log(f"♻️ Unban: {user_id}")

# ==========================
# MUTE
# ==========================
@bot.message_handler(commands=['mute'])
def mute_user(message):

    if get_level(message.from_user.id, message.chat.id) < 2:
        return

    if not message.reply_to_message:
        return

    try:
        minutes = int(message.text.split()[1])
    except:
        return

    target = message.reply_to_message.from_user

    if is_protected(target.id):
        return

    until = int(time.time()) + minutes * 60

    bot.restrict_chat_member(
        message.chat.id,
        target.id,
        until_date=until,
        can_send_messages=False
    )

    bot.send_message(message.chat.id, f"{minutes} dakika susturuldu.")
    log(f"🔇 Mute: {target.id} ({minutes} dk)")

# ==========================
# UNMUTE
# ==========================
@bot.message_handler(commands=['unmute'])
def unmute_user(message):

    if get_level(message.from_user.id, message.chat.id) < 2:
        return

    if not message.reply_to_message:
        return

    target = message.reply_to_message.from_user

    if is_protected(target.id):
        return

    bot.restrict_chat_member(
        message.chat.id,
        target.id,
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True
    )

    bot.send_message(message.chat.id, "Mute kaldırıldı.")
    log(f"🔊 Unmute: {target.id}")

# ==========================
# FLOOD + KÜFÜR
# ==========================
@bot.message_handler(func=lambda m: True, content_types=['text'])
def message_control(message):

    uid = message.from_user.id
    text = message.text.lower()

    for word in bad_words:
        if word in text:
            bot.delete_message(message.chat.id, message.message_id)
            return

    now = time.time()

    if uid not in user_messages:
        user_messages[uid] = []

    user_messages[uid] = [t for t in user_messages[uid] if now - t < FLOOD_TIME]
    user_messages[uid].append(now)

    if len(user_messages[uid]) > FLOOD_LIMIT:
        bot.restrict_chat_member(
            message.chat.id,
            uid,
            until_date=int(now) + 60,
            can_send_messages=False
        )
        log(f"🔇 Flood mute: {uid}")

# ==========================
# RUN
# ==========================
print("FULL GUARD BOT AKTİF")
bot.infinity_polling()
