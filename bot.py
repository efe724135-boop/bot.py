import telebot
import os
import time
import threading

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

OWNER_ID = 8213465894 # BURAYA KENDİ ID'NI YAZ
WELCOME_IMAGE = "https://i.imgur.com/MDqyHge.jpg"

user_messages = {}

# ==========================
# MESAJI 15 SN SONRA SİL
# ==========================
def delete_later(chat_id, message_id, delay=15):
    def task():
        time.sleep(delay)
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
    threading.Thread(target=task).start()

# ==========================
# YETKİ KONTROL
# ==========================
def is_owner(user_id):
    return user_id == OWNER_ID

def is_admin(user_id, chat_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False

def is_authorized(user_id, chat_id):
    return is_owner(user_id) or is_admin(user_id, chat_id)

# ==========================
# FOTOĞRAFLI HOŞGELDİN
# ==========================
@bot.message_handler(content_types=['new_chat_members'])
def welcome(message):
    for user in message.new_chat_members:
        msg = bot.send_photo(
            message.chat.id,
            WELCOME_IMAGE,
            caption=f"🔥 Türkiye'nin en iyi hile kanalına hoş geldin {user.first_name}!"
        )
        delete_later(message.chat.id, msg.message_id)

# ==========================
# MUTE
# ==========================
@bot.message_handler(commands=['mute'])
def mute_user(message):
    if not is_authorized(message.from_user.id, message.chat.id):
        msg = bot.reply_to(message, "❌ Yetkili değilsin.")
        delete_later(message.chat.id, msg.message_id)
        return

    if not message.reply_to_message:
        return

    target = message.reply_to_message.from_user

    if is_owner(target.id):
        return

    try:
        minutes = int(message.text.split()[1])
    except:
        return

    if minutes not in [5, 10, 15]:
        return

    until = int(time.time()) + minutes * 60

    bot.restrict_chat_member(
        message.chat.id,
        target.id,
        until_date=until,
        can_send_messages=False
    )

    msg = bot.send_message(message.chat.id, f"🔇 {target.first_name} {minutes} dakika susturuldu.")
    delete_later(message.chat.id, msg.message_id)

# ==========================
# UNMUTE
# ==========================
@bot.message_handler(commands=['unmute'])
def unmute_user(message):
    if not is_authorized(message.from_user.id, message.chat.id):
        return

    if not message.reply_to_message:
        return

    target = message.reply_to_message.from_user

    bot.restrict_chat_member(
        message.chat.id,
        target.id,
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_other_messages=True
    )

    msg = bot.send_message(message.chat.id, f"🔊 {target.first_name} susturma kaldırıldı.")
    delete_later(message.chat.id, msg.message_id)

# ==========================
# BAN
# ==========================
@bot.message_handler(commands=['ban'])
def ban_user(message):
    if not is_authorized(message.from_user.id, message.chat.id):
        return

    if not message.reply_to_message:
        return

    target = message.reply_to_message.from_user

    if is_owner(target.id):
        return

    bot.ban_chat_member(message.chat.id, target.id)

    msg = bot.send_message(message.chat.id, f"🚫 {target.first_name} banlandı.")
    delete_later(message.chat.id, msg.message_id)

# ==========================
# UNBAN
# ==========================
@bot.message_handler(commands=['unban'])
def unban_user(message):
    if not is_authorized(message.from_user.id, message.chat.id):
        return

    try:
        user_id = int(message.text.split()[1])
    except:
        return

    bot.unban_chat_member(message.chat.id, user_id)

    msg = bot.send_message(message.chat.id, "✅ Kullanıcının banı kaldırıldı.")
    delete_later(message.chat.id, msg.message_id)

# ==========================
# START
# ==========================
@bot.message_handler(commands=['start'])
def start(message):
    msg = bot.send_message(message.chat.id,
"""🔥 Guard Bot Aktif

Komutlar:
/mute 5-10-15
/unmute
/ban
/unban
""")
    delete_later(message.chat.id, msg.message_id)

# ==========================
# SPAM KORUMA (EN ALTTA!)
# ==========================
@bot.message_handler(func=lambda m: m.content_type == "text" and not m.text.startswith("/"))
def spam_control(message):
    user_id = message.from_user.id
    now = time.time()

    if user_id not in user_messages:
        user_messages[user_id] = []

    user_messages[user_id] = [t for t in user_messages[user_id] if now - t < 5]
    user_messages[user_id].append(now)

    if len(user_messages[user_id]) > 5:
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass

print("Bot aktif...")
bot.infinity_polling()
