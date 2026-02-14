import telebot
import os
import time
import threading

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

OWNER_ID = 8213465894
GROUP_ID = -1003377826935

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
# HOŞGELDİN
# ==========================
@bot.message_handler(content_types=['new_chat_members'])
def welcome(message):
    if message.chat.id != GROUP_ID:
        return

    for user in message.new_chat_members:
        text = f"""
🔥 Hosgeldin {user.first_name}

Burası karanlık esprilerin, ters köşe mizahın ve filtresiz zekânın buluştuğu bir alan.
Mizah sert olabilir, espri karanlık olabilir ama illegal tek bir adım bile yoktur.

#KAOS
"""
        msg = bot.send_message(message.chat.id, text)
        delete_later(message.chat.id, msg.message_id)

# ==========================
# INFO (REPLY DESTEKLİ)
# ==========================
@bot.message_handler(commands=['info'])
def info_command(message):
    if message.chat.id != GROUP_ID:
        return

    if message.reply_to_message:
        user = message.reply_to_message.from_user
    else:
        user = message.from_user

    username = f"@{user.username}" if user.username else "Yok"

    role = "Üye"
    try:
        member = bot.get_chat_member(message.chat.id, user.id)
        if member.status == "creator":
            role = "Owner 👑"
        elif member.status == "administrator":
            role = "Admin 🛡"
    except:
        pass

    text = f"""
📌 KULLANICI BİLGİSİ

👤 İsim: {user.first_name}
🔗 Kullanıcı Adı: {username}
🆔 Kullanıcı ID: {user.id}
🎖 Yetki: {role}

📍 Grup ID: {message.chat.id}
"""

    msg = bot.send_message(message.chat.id, text)
    delete_later(message.chat.id, msg.message_id)

# ==========================
# STAFF
# ==========================
@bot.message_handler(commands=['staff'])
def staff_command(message):
    if message.chat.id != GROUP_ID:
        return

    try:
        admins = bot.get_chat_administrators(message.chat.id)

        text = "👑 KAOS STAFF\n\n"

        for admin in admins:
            user = admin.user
            if admin.status == "creator":
                text += f"👑 Owner: {user.first_name}\n"
            else:
                text += f"🛡 Admin: {user.first_name}\n"

        msg = bot.send_message(message.chat.id, text)
        delete_later(message.chat.id, msg.message_id)
    except:
        pass

# ==========================
# MUTE
# ==========================
@bot.message_handler(commands=['mute'])
def mute_user(message):
    if not is_authorized(message.from_user.id, message.chat.id):
        bot.delete_message(message.chat.id, message.message_id)
        return

    if not message.reply_to_message:
        return

    target = message.reply_to_message.from_user

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
        bot.delete_message(message.chat.id, message.message_id)
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
        bot.delete_message(message.chat.id, message.message_id)
        return

    if not message.reply_to_message:
        return

    target = message.reply_to_message.from_user

    if is_owner(target.id):
        msg = bot.send_message(message.chat.id, "❌ Owner banlanamaz.")
        delete_later(message.chat.id, msg.message_id)
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
        bot.delete_message(message.chat.id, message.message_id)
        return

    try:
        user_id = int(message.text.split()[1])
    except:
        return

    bot.unban_chat_member(message.chat.id, user_id)

    msg = bot.send_message(message.chat.id, "✅ Ban kaldırıldı.")
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
/info
/staff
""")
    delete_later(message.chat.id, msg.message_id)

# ==========================
# SPAM + KÜFÜR + REKLAM
# ==========================
@bot.message_handler(func=lambda m: m.content_type == "text")
def guard_system(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.lower()
    now = time.time()

    if text.startswith("/") and not is_authorized(user_id, chat_id):
        bot.delete_message(chat_id, message.message_id)
        return

    if is_authorized(user_id, chat_id):
        return

    if user_id not in user_messages:
        user_messages[user_id] = []

    user_messages[user_id] = [t for t in user_messages[user_id] if now - t < 5]
    user_messages[user_id].append(now)

    if len(user_messages[user_id]) > 5:
        bot.delete_message(chat_id, message.message_id)
        return

    bad_words = [
        "amk","aq","amq","amina","amına","amcik","amcık",
        "orospu","oc","oç","pic","piç",
        "sik","sikerim","siktir",
        "yarak","yarrak",
        "got","göt",
        "ibne",
        "anan","ananı",
        "bacini","bacını",
        "pezevenk","kahpe","şerefsiz","serefsiz"
    ]

    links = ["http", "https", "t.me", ".com", ".net", ".org"]

    if any(word in text for word in bad_words) or any(link in text for link in links):
        bot.delete_message(chat_id, message.message_id)
        return

print("Guard Bot Aktif 🔥")
bot.infinity_polling()
