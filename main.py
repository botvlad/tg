from flask import Flask, request
import telebot
from telebot import types
import sqlite3

TOKEN = "8504419294:AAFZrDw8pUVrAG29E0it-fZHlN_g3q9PSAs"
WEBHOOK_URL = "https://YOUR_RENDER_URL.onrender.com/"  # <-- сюда URL Render

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

app = Flask(__name__)

ADMIN_IDS = [8063642030, 8453400444]

# ===================== DATABASE =====================
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
        link TEXT,
        limit_count INTEGER,
        joined INTEGER DEFAULT 0
    )""")

    db("""
    CREATE TABLE IF NOT EXISTS sponsor_rewards(
        user_id INTEGER,
        sponsor TEXT,
        PRIMARY KEY (user_id, sponsor)
    )""")
    
    db("""
    CREATE TABLE IF NOT EXISTS comment_screens(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        file_id TEXT,
        approved INTEGER DEFAULT 0
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
        PRIMARY KEY (user_id, code)
    )""")
    
    db("""
    CREATE TABLE IF NOT EXISTS sponsors_menu(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel TEXT,
        link TEXT,
        limit_count INTEGER
    )""")

# ===================== UTIL =====================
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

def sponsor_tasks_kb(uid):
    kb = types.InlineKeyboardMarkup()
    sponsors = db("SELECT channel, link FROM sponsors")
    for channel, link in sponsors:
        try:
            status = bot.get_chat_member(channel, uid).status
            if status not in ("member", "administrator", "creator"):
                kb.add(types.InlineKeyboardButton(f"Подписаться на {channel}", url=link))
        except:
            kb.add(types.InlineKeyboardButton(f"Подписаться на {channel}", url=link))
    kb.add(types.InlineKeyboardButton("✅ Я подписался", callback_data="check_sponsor_tasks"))
    return kb

# ===================== START =====================
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

    if not ensure_subscription(uid):
        block_user(uid)
        bot.send_message(uid, "🔒 Подпишись на всех спонсоров:", reply_markup=sponsor_tasks_kb(uid))
        return

    unlock_user(uid)
    bot.send_message(uid, "✨ Добро пожаловать в <b>DROPSTARSS</b>", reply_markup=main_menu(), parse_mode="HTML")

# ===================== CALLBACK =====================
@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    uid = c.from_user.id
    if not ensure_subscription(uid):
        block_user(uid)
        bot.edit_message_text(
            "⚠️ Ты отписался. Подпишись обратно, чтобы продолжить ⭐",
            c.message.chat.id,
            c.message.message_id,
            reply_markup=sponsor_tasks_kb(uid)
        )
        return
    else:
        unlock_user(uid)

    if c.data == "earn":
        bot.edit_message_text("🌟 Выбери способ заработка:", c.message.chat.id, c.message.message_id, reply_markup=earn_menu())
        return

    if c.data == "earn_sub":
        bot.edit_message_text("⭐ За подписку на каждый канал начисляется 0.5 ⭐", c.message.chat.id, c.message.message_id, reply_markup=sponsor_tasks_kb(uid))
        return

    if c.data == "check_sponsor_tasks":
        total = 0
        for (channel,) in db("SELECT channel FROM sponsors"):
            try:
                status = bot.get_chat_member(channel, uid).status
                if status in ("member","administrator","creator") and not db("SELECT 1 FROM sponsor_rewards WHERE user_id=? AND sponsor=?", (uid, channel)):
                    db("INSERT INTO sponsor_rewards VALUES (?,?)", (uid, channel))
                    total += 0.5
            except:
                pass
        if total > 0:
            db("UPDATE users SET balance=balance+? WHERE user_id=?", (total, uid))
            bot.send_message(uid, f"🎉 Начислено {total} ⭐")
        bot.edit_message_text("🌟 Выбери способ заработка:", c.message.chat.id, c.message.message_id, reply_markup=earn_menu())
        return

    if c.data == "earn_refs":
        bot.edit_message_text(
            f"👥 Пригласи друга и получи 8 ⭐\nТвоя ссылка:\nhttps://t.me/{bot.get_me().username}?start={uid}",
            c.message.chat.id, c.message.message_id, reply_markup=earn_menu(), parse_mode="HTML"
        )
        return

    if c.data == "back_main":
        bot.edit_message_text("✨ Главное меню:", c.message.chat.id, c.message.message_id, reply_markup=main_menu())
        return

# ===================== ADMIN =====================
@bot.message_handler(commands=["add_sponsor"])
def add_sponsor(m):
    if m.from_user.id not in ADMIN_IDS:
        return
    try:
        _, channel, link, limit_ = m.text.split()
        limit_ = int(limit_)
    except:
        bot.send_message(m.chat.id, "❌ Использование: /add_sponsor @channel link limit")
        return
    db("INSERT INTO sponsors (channel, link, limit_count) VALUES (?,?,?)", (channel, link, limit_))
    db("UPDATE users SET is_activated=0")
    bot.send_message(m.chat.id, "✅ Спонсор добавлен, пользователи заблокированы")
    for (uid,) in db("SELECT user_id FROM users"):
        try:
            bot.send_message(uid, "📢 Новый спонсор! Подпишись для продолжения работы:", reply_markup=sponsor_tasks_kb(uid))
        except:
            pass

@bot.message_handler(commands=["add_sponsor_menu"])
def add_sponsor_menu(m):
    if m.from_user.id not in ADMIN_IDS:
        return
    try:
        _, channel, link, limit_ = m.text.split()
        limit_ = int(limit_)
    except:
        bot.send_message(m.chat.id, "❌ Использование: /add_sponsor_menu @channel link limit")
        return
    db("INSERT INTO sponsors_menu (channel, link, limit_count) VALUES (?,?,?)", (channel, link, limit_))
    bot.send_message(m.chat.id, "✅ Спонсор для заданий добавлен")

# ===================== RUN =====================
@app.route("/", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

if __name__ == "__main__":
    init_db()
    print("DROPSTARSS запущен через webhook на Render")
    app.run(host="0.0.0.0", port=5000)
