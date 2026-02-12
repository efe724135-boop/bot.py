import telebot
import os
import time
import threading

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

OWNER_ID = 8213465894 # BURAYA KENDİ ID'NI YAZ

SECURITY_LEVEL = 2
MAX_WARN = 3
WELCOME_DELETE_TIME = 30
FLOOD_LIMIT = 5
FLOOD_TIME = 5

BAD_WORDS = ["oç", "amk", "piç"]

warnings = {}
message_tracker = {}

# ================= YETKİ =================

def is_admin(chat_id, user_id):
    member = bot.get_chat_member(chat_id, user_id)
    return member.status in ["administrator", "creator"]

def is_owner(user_id):
    return user_id == OWNER_ID

def delete_later(chat_id, message_id, delay):
    time.sleep(delay)
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass

# ================= ANİMASYONLU HOŞ GELDİN =================

@bot.message_handler(content_types=['new_chat_members'])
def welcome(message):
    for user in message.new_chat_members:

        sent = bot.send_message(
            message.chat.id,
            "🔄 Yeni üye katılıyor..."
        )

        def animate():
            frames = [
                f"👀 Profil kontrol ediliyor...",
                f"📡 Sisteme ekleniyor...",
                f"🔥 Hoş geldin *{user.first_name}* !\n\n💎 En iyi hile burada!\n⚡ Kurallara uymayı unutma."
            ]

            for frame in frames:
                time.sleep(1.2)
                try:
                    bot.edit_message_text(
                        frame,
                        message.chat.id,
                        sent.message_id
                    )
                except:
                    pass

            # 30 saniye sonra sil
            time.sleep(WELCOME_DELETE_TIME)
            try:
                bot.delete_message(message.chat.id, sent.message_id)
            except:
                pass

        threading.Thread(target=animate).start()

# ================= WARN SİSTEMİ =================

def add_warn(chat_id, user):

    user_id = user.id

    if user_id not in warnings:
        warnings[user_id] = 0

    warnings[user_id] += 1

    warn_msg = bot.send_message(
        chat_id,
        f"⚠️ *{user.first_name}* uyarıldı! ({warnings[user_id]}/{MAX_WARN})"
    )

    threading.Thread(
        target=delete_later,
        args=(chat_id, warn_msg.message_id, 10)
    ).start()

    if warnings[user_id] >= MAX_WARN:

        admins = bot.get_chat_administrators(chat_id)
        admin_mentions = ""

        for admin in admins:
            if not admin.user.is_bot:
                admin_mentions += f"[{admin.user.first_name}](tg://user?id={admin.user.id}) "

        bot.send_message(
            chat_id,
            f"🚨 *{user.first_name}* 3 uyarıya ulaştı!\nAdminler ilgilensin.\n\n{admin_mentions}"
        )

        warnings[user_id] = 0

# ================= BAN =================

@bot.message_handler(commands=['ban'])
def ban_user(message):

    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "❌ Sadece admin ban atabilir.")
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        bot.ban_chat_member(message.chat.id, user_id)
        bot.reply_to(message, "✅ Kullanıcı banlandı.")

# ================= UNBAN =================

@bot.message_handler(commands=['unban'])
def unban_user(message):

    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "❌ Sadece admin unban yapabilir.")
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        bot.unban_chat_member(message.chat.id, user_id)
        bot.reply_to(message, "✅ Ban kaldırıldı.")

# ================= MUTE =================

@bot.message_handler(commands=['mute'])
def mute_user(message):

    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "❌ Sadece admin mute atabilir.")
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        bot.restrict_chat_member(
            message.chat.id,
            user_id,
            can_send_messages=False
        )
        bot.reply_to(message, "🔇 Kullanıcı susturuldu.")

# ================= UNMUTE =================

@bot.message_handler(commands=['unmute'])
def unmute_user(message):

    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "❌ Sadece admin unmute yapabilir.")
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        bot.restrict_chat_member(
            message.chat.id,
            user_id,
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True
        )
        bot.reply_to(message, "🔊 Susturma kaldırıldı.")

# ================= KORUMA =================

@bot.message_handler(func=lambda message: True)
def protect(message):

    if not message.text:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.lower()

    if is_admin(chat_id, user_id):
        return

    # Küfür
    for word in BAD_WORDS:
        if word in text:
            bot.delete_message(chat_id, message.message_id)
            add_warn(chat_id, message.from_user)
            return

    # Reklam
    if "http://" in text or "https://" in text or "t.me/" in text:
        bot.delete_message(chat_id, message.message_id)
        add_warn(chat_id, message.from_user)
        return

    # Spam
    now = time.time()

    if user_id not in message_tracker:
        message_tracker[user_id] = []

    message_tracker[user_id].append(now)

    message_tracker[user_id] = [
        t for t in message_tracker[user_id] if now - t < FLOOD_TIME
    ]

    if len(message_tracker[user_id]) > FLOOD_LIMIT:
        bot.delete_message(chat_id, message.message_id)
        add_warn(chat_id, message.from_user)
        return


bot.infinity_polling()
