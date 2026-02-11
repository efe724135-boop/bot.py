import telebot
from telebot.types import ChatPermissions
import re

BOT_TOKEN = "8326281735:AAFJG7wfgzozpEMuKG5V_nAkM6oD2ivMH74"
bot = telebot.TeleBot(BOT_TOKEN)

warnings = {}  # kullanıcı uyarı sayacı

bad_words = ["küfür1", "küfür2"]  # buraya kendin ekle

# Admin kontrol
def is_admin(chat_id, user_id):
    admins = bot.get_chat_administrators(chat_id)
    return any(admin.user.id == user_id for admin in admins)

# Yeni üye mesajı
@bot.message_handler(content_types=["new_chat_members"])
def welcome(message):
    for user in message.new_chat_members:
        bot.send_message(message.chat.id, f"Hoşgeldin {user.first_name} 👋")

# Mesaj koruma sistemi
@bot.message_handler(func=lambda m: True)
def protect(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text.lower()

    if is_admin(chat_id, user_id):
        return  # adminlere dokunma

    # Reklam kontrol (link)
    if re.search(r"(http|t\.me|www\.)", text):
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, "🚫 Reklam yasak!")
        add_warning(chat_id, user_id)
        return

    # Küfür kontrol
    for word in bad_words:
        if word in text:
            bot.delete_message(chat_id, message.message_id)
            bot.send_message(chat_id, "🚫 Küfür yasak!")
            add_warning(chat_id, user_id)
            return

# Uyarı sistemi
def add_warning(chat_id, user_id):
    key = f"{chat_id}_{user_id}"
    warnings[key] = warnings.get(key, 0) + 1

    if warnings[key] >= 3:
        bot.ban_chat_member(chat_id, user_id)
        bot.send_message(chat_id, "⛔ 3 uyarı aldın. Banlandın.")

# ADMIN KOMUTLARI

@bot.message_handler(commands=["ban"])
def ban_user(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        bot.ban_chat_member(message.chat.id, user_id)
        bot.send_message(message.chat.id, "⛔ Kullanıcı banlandı.")

@bot.message_handler(commands=["unban"])
def unban_user(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        bot.unban_chat_member(message.chat.id, user_id)
        bot.send_message(message.chat.id, "✅ Ban kaldırıldı.")

@bot.message_handler(commands=["warn"])
def warn_user(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        add_warning(message.chat.id, user_id)
        bot.send_message(message.chat.id, "⚠️ Uyarı verildi.")

print("Koruma botu aktif...")
bot.infinity_polling()
