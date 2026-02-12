import telebot
import re
import os
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_ID = 8213465894  # BURAYA KENDİ TELEGRAM ID'NI YAZ

warnings = {}
last_messages = {}

bad_words = ["oç", "ananı", "amk", "sikim", "piç"]


# /start komutu (özel mesaj için)
@bot.message_handler(commands=['start'])
def start_message(message):
    pass  # start bir şey demesin


# Admin kontrol
def is_admin(chat_id, user_id):
    admins = bot.get_chat_administrators(chat_id)
    return any(admin.user.id == user_id for admin in admins)


# Uyarı sistemi
def add_warning(chat_id, user_id):
    if user_id not in warnings:
        warnings[user_id] = 0
    warnings[user_id] += 1

    if warnings[user_id] >= 3:
        bot.ban_chat_member(chat_id, user_id)
        bot.send_message(chat_id, "🚫 3 uyarı aldın, banlandın.")


# Yeni gelen üyeye hoşgeldin
@bot.message_handler(content_types=['new_chat_members'])
def welcome(message):
    for user in message.new_chat_members:
        bot.send_message(message.chat.id, f"Hoşgeldin {user.first_name} 👋")


# 🔥 MANUEL BAN
@bot.message_handler(commands=['ban'])
def manual_ban(message):
    if message.from_user.id != ADMIN_ID:
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        bot.ban_chat_member(message.chat.id, user_id)
        bot.send_message(message.chat.id, "🚫 Kullanıcı banlandı.")


# 🔥 MANUEL UNBAN
@bot.message_handler(commands=['unban'])
def manual_unban(message):
    if message.from_user.id != ADMIN_ID:
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        bot.unban_chat_member(message.chat.id, user_id)
        bot.send_message(message.chat.id, "✅ Kullanıcının banı kaldırıldı.")


# Mesaj kontrol sistemi
@bot.message_handler(func=lambda m: True)
def protect(message):
    if not message.text:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text.lower()

    if is_admin(chat_id, user_id):
        return

    # Küfür kontrol
    for word in bad_words:
        if word in text:
            bot.delete_message(chat_id, message.message_id)
            bot.send_message(chat_id, "🚫 Küfür yasak!")
            add_warning(chat_id, user_id)
            return

    # Reklam kontrol
    if re.search(r"(http|t\.me|www\.)", text):
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, "🚫 Reklam yasak!")
        add_warning(chat_id, user_id)
        return

    # Spam kontrol (5 saniyede 3 mesaj)
    now = time.time()

    if user_id not in last_messages:
        last_messages[user_id] = []

    last_messages[user_id] = [
        t for t in last_messages[user_id] if now - t < 5
    ]

    last_messages[user_id].append(now)

    if len(last_messages[user_id]) >= 3:
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, "🚫 Spam yapma!")
        add_warning(chat_id, user_id)
        return


print("Koruma botu aktif 🔥")

bot.infinity_polling()
