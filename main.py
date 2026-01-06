import telebot
from telebot import types
import sqlite3
from flask import Flask, request
import os

# ================== КОНФИГ ==================
TOKEN = "8504419294:AAFZrDw8pUVrAG29E0it-fZHlN_g3q9PSAs"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Админы
ADMIN_IDS = [8063642030, 8453400444]

# ================== БАЗА ДАННЫХ ==================
def db(sql, params=()):
    with sqlite3.connect("bot.db", check_same_thread=False) as c:
        cur = c.cursor()
        cur.execute(sql, params)
        res = cur.fetchall()
        c.commit()
        return res

def init_db():
    db("""
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance REAL DEFAULT 0,
        referrals INTEGER DEFAULT 0,
        referrer INTEGER,
        is_activated INTEGER DEFAULT 0
    )""")
    db("""
    CREATE TABLE IF NOT EXISTS sponsors(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel TEXT,
        link TEXT
    )""")
    db("""
    CREATE TABLE IF NOT EXISTS sponsor_tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel TEXT,
        link TEXT
    )""")
    db("""
    CREATE TABLE IF NOT EXISTS promocodes(
        code TEXT PRIMARY KEY,
        amount REAL,
        max_uses INTEGER,
        uses INTEGER DEFAULT 0
    )""")
    db("""
    CREATE TABLE IF NOT EXISTS used_promos(
        user_id INTEGER,
        code TEXT,
        PRIMARY KEY(user_id, code)
    )""")
    db("""
    CREATE TABLE IF NOT EXISTS sponsor_rewards(
        user_id INTEGER,
        sponsor TEXT,
        PRIMARY KEY(user_id, sponsor)
    )""")
    db("""
    CREATE TABLE IF NOT EXISTS comment_screens(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        file_id TEXT,
        approved INTEGER DEFAULT 0
    )""")

# ================== КЛАВИАТУРЫ ==================
def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🌟 Заработать", callback_data="earn"),
        types.InlineKeyboardButton("📩 Вывод", callback_data="withdraw"),
        types.InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        types.InlineKeyboardButton("🎁 Промокод", callback_data="promo"),
        types.InlineKeyboardButton("🏆 Топ", callback_data="top")
    )
    return kb

def earn_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("⭐ Подписка на канал", callback_data="earn_sub"),
        types.InlineKeyboardButton("👥 Рефералы", callback_data="earn_refs"),
        types.InlineKeyboardButton("💬 Комментарии", callback_data="earn_comments"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data="back_main")
    )
    return kb

def sub_keyboard():
    kb = types.InlineKeyboardMarkup()
    sponsors = db("SELECT channel, link FROM sponsors")
    for s in sponsors:
        kb.add(types.InlineKeyboardButton(f"⭐ {s[0]}", url=s[1]))
    kb.add(types.InlineKeyboardButton("✅ Я подписался", callback_data="sub_check"))
    return kb

def sponsor_tasks_kb(uid, show_only_unsub=False):
    kb = types.InlineKeyboardMarkup()
    sponsors = db("SELECT channel, link FROM sponsor_tasks")
    if not sponsors:
        return None
    for channel, link in sponsors:
        if show_only_unsub:
            try:
                status = bot.get_chat_member(channel, uid).status
                if status not in ("member", "administrator", "creator"):
                    kb.add(types.InlineKeyboardButton(f"Подписаться на {channel}", url=link))
            except:
                kb.add(types.InlineKeyboardButton(f"Подписаться на {channel}", url=link))
        else:
            kb.add(types.InlineKeyboardButton(f"⭐ {channel}", url=link))
    kb.add(types.InlineKeyboardButton("✅ Я подписался", callback_data="check_sponsor_tasks"))
    return kb

# ================== ФУНКЦИИ ==================
def ensure_subscription(uid):
    sponsors = db("SELECT channel FROM sponsors")
    for (channel,) in sponsors:
        try:
            status = bot.get_chat_member(channel, uid).status
            if status not in ("member", "administrator", "creator"):
                return False
        except:
            return False
    return True

def block_user(uid):
    db("UPDATE users SET is_activated=0 WHERE user_id=?", (uid,))

def unlock_user(uid):
    db("UPDATE users SET is_activated=1 WHERE user_id=?", (uid,))

def notify_all(text):
    for (uid,) in db("SELECT user_id FROM users"):
        try:
            bot.send_message(uid, text, parse_mode="HTML")
        except:
            pass

# ================== СТАРТ ==================
@bot.message_handler(commands=["start"])
def start(m):
    uid = m.from_user.id
    uname = m.from_user.username or "user"
    args = m.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

    if not db("SELECT 1 FROM users WHERE user_id=?", (uid,)):
        db("INSERT INTO users (user_id, username, referrer) VALUES (?,?,?)", (uid, uname, ref_id if ref_id != uid else None))
        if ref_id and db("SELECT 1 FROM users WHERE user_id=?", (ref_id,)):
            db("UPDATE users SET referrals=referrals+1, balance=balance+8 WHERE user_id=?", (ref_id,))
            bot.send_message(ref_id, "🎉 Новый реферал! +8 ⭐")

    if not ensure_subscription(uid):
        block_user(uid)
        bot.send_message(uid, "🔒 Подпишись на всех спонсоров:", reply_markup=sub_keyboard())
        return

    unlock_user(uid)
    bot.send_message(uid, "✨ Добро пожаловать", reply_markup=main_menu(), parse_mode="HTML")

# ================== CALLBACK ==================
@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    uid = c.from_user.id

    # Проверка подписки
    if not ensure_subscription(uid):
        kb = types.InlineKeyboardMarkup()
        unsubscribed_channels = []
        for (channel,) in db("SELECT channel FROM sponsors"):
            try:
                status = bot.get_chat_member(channel, uid).status
                if status not in ("member", "administrator", "creator"):
                    unsubscribed_channels.append(channel)
            except:
                unsubscribed_channels.append(channel)
        text = "⚠️ Упс! Ты отписался, подпишись обратно, чтобы продолжить зарабатывать ⭐"
        for ch in unsubscribed_channels:
            link = db("SELECT link FROM sponsors WHERE channel=?", (ch,))[0][0]
            kb.add(types.InlineKeyboardButton(f"Подписаться на {ch}", url=link))
        kb.add(types.InlineKeyboardButton("✅ Я подписался", callback_data="check_sponsor_tasks"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=kb)
        return
    else:
        unlock_user(uid)

    if c.data == "earn":
        bot.edit_message_text("🌟 Забирай звёзды любым способом:", c.message.chat.id, c.message.message_id, reply_markup=earn_menu())
        return

    if c.data == "back_main":
        bot.edit_message_text("✨ Главное меню:", c.message.chat.id, c.message.message_id, reply_markup=main_menu())
        return

# ================== АДМИН ==================
@bot.message_handler(commands=["add_sponsor"])
def add_sponsor(m):
    if m.from_user.id not in ADMIN_IDS:
        return
    try:
        _, channel, link = m.text.split()
    except:
        bot.send_message(m.chat.id, "❌ /add_sponsor @channel link")
        return
    db("INSERT INTO sponsors (channel, link) VALUES (?,?)", (channel, link))
    db("UPDATE users SET is_activated=0")
    notify_all("📢 <b>Добавлен новый спонсор! Подпишитесь на всех спонсоров для продолжения работы 👇</b>")
    bot.send_message(m.chat.id, "✅ Спонсор добавлен и пользователи уведомлены")

@bot.message_handler(commands=["add_sponsor_menu"])
def add_sponsor_menu(m):
    if m.from_user.id not in ADMIN_IDS:
        return
    try:
        _, channel, link = m.text.split()
    except:
        bot.send_message(m.chat.id, "❌ /add_sponsor_menu @channel link")
        return
    db("INSERT INTO sponsor_tasks (channel, link) VALUES (?,?)", (channel, link))
    bot.send_message(m.chat.id, "✅ Спонсор добавлен в меню ‘Заработать’")

# ================== WEBHOOK FLASK ==================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def index():
    return "Bot is running", 200

# ================== ЗАПУСК ==================
if __name__ == "__main__":
    init_db()
    bot.remove_webhook()
    # Вставь сюда реальный URL своего Render сервиса
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")  # Render автоматически ставит переменную
    webhook_url = f"{RENDER_URL}/{TOKEN}"
    bot.set_webhook(url=webhook_url)
    print("DROPSTARSS запущен через webhook на Render")
    app.run(host="0.0.0.0", port=5000)
