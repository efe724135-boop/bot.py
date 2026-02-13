import telebot
import time
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

OWNER_ID = 6393604989
ADMIN_IDS = [8213465894]

BAD_WORDS = ["oç", "amk", "ananı", "piç", "sik"]

last_messages = {}
flood_count = {}

# ===== YETKI =====
def is_owner(user_id):
    return user_id == OWNER_ID

def is_admin(user_id):
    return user_id == OWNER_ID or user_id in ADMIN_IDS

def delete_later(chat_id, message_id, seconds=15):
    time.sleep(seconds)
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass

# ===== HOSGELDIN MESAJI =====
@bot.message_handler(content_types=['new_chat_members'])
def welcome(message):
    for user in message.new_chat_members:
        msg = bot.send_message(
            message.chat.id,
            f"Türkiye'nin en iyi hile kanalına hoşgeldin {user.first_name} 🔥"
        )
        delete_later(message.chat.id, msg.message_id)

# ===== SURELI MUTE =====
@bot.message_handler(commands=['mute'])
def mute_user(message):

    if not is_admin(message.from_user.id):
        return

    if not message.reply_to_message:
        return

    args = message.text.split()

    if len(args) < 2:
        msg = bot.reply_to(message, "Süre yaz: /mute 5")
        delete_later(message.chat.id, msg.message_id)
        return

    try:
        minutes = int(args[1])
    except:
        return

    if minutes not in [5,10,15]:
        msg = bot.reply_to(message, "Sadece 5, 10 veya 15 dk.")
        delete_later(message.chat.id, msg.message_id)
        return

    target = message.reply_to_message.from_user

    if target.id == OWNER_ID:
        msg = bot.reply_to(message, "Owner'a işlem yapamazsın.")
        delete_later(message.chat.id, msg.message_id)
        return

    until_time = int(time.time()) + (minutes * 60)

    bot.restrict_chat_member(message.chat.id, target.id, until_date=until_time)

    msg = bot.reply_to(message, f"{target.first_name} {minutes} dk susturuldu.")
    delete_later(message.chat.id, msg.message_id)

# ===== UNMUTE =====
@bot.message_handler(commands=['unmute'])
def unmute_user(message):

    if not is_admin(message.from_user.id):
        return

    if not message.reply_to_message:
        return

    target = message.reply_to_message.from_user

    bot.restrict_chat_member(
        message.chat.id,
        target.id,
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True
    )

    msg = bot.reply_to(message, f"{target.first_name} susturma kaldırıldı.")
    delete_later(message.chat.id, msg.message_id)

# ===== BAN =====
@bot.message_handler(commands=['ban'])
def ban_user(message):

    if not is_admin(message.from_user.id):
        return

    if not message.reply_to_message:
        return

    target = message.reply_to_message.from_user

    if target.id == OWNER_ID:
        msg = bot.reply_to(message, "Owner'a işlem yapamazsın.")
        delete_later(message.chat.id, msg.message_id)
        return

    bot.ban_chat_member(message.chat.id, target.id)

    msg = bot.reply_to(message, f"{target.first_name} banlandı.")
    delete_later(message.chat.id, msg.message_id)

# ===== UNBAN =====
@bot.message_handler(commands=['unban'])
def unban_user(message):

    if not is_admin(message.from_user.id):
        return

    if not message.reply_to_message:
        return

    target = message.reply_to_message.from_user

    bot.unban_chat_member(message.chat.id, target.id)

    msg = bot.reply_to(message, f"{target.first_name} ban kaldırıldı.")
    delete_later(message.chat.id, msg.message_id)

# ===== FILTRE SISTEMI =====
@bot.message_handler(func=lambda m: True)
def filter_messages(message):

    if is_admin(message.from_user.id):
        return

    text = message.text.lower()

    # Küfür
    for word in BAD_WORDS:
        if word in text:
            bot.delete_message(message.chat.id, message.message_id)
            return

    # Link
    if "http" in text or "t.me" in text or "@" in text:
        bot.delete_message(message.chat.id, message.message_id)
        return

    # Flood
    user_id = message.from_user.id
    now = time.time()

    if user_id not in last_messages:
        last_messages[user_id] = now
        flood_count[user_id] = 1
    else:
        if now - last_messages[user_id] < 2:
            flood_count[user_id] += 1
        else:
            flood_count[user_id] = 1

        last_messages[user_id] = now

        if flood_count[user_id] >= 5:
            until_time = int(time.time()) + (10 * 60)
            bot.restrict_chat_member(message.chat.id, user_id, until_date=until_time)
            bot.delete_message(message.chat.id, message.message_id)

print("Bot aktif...")
bot.infinity_polling()
