import telebot
from telebot import types
import sqlite3
from flask import Flask, request

# ====================== API ======================
TOKEN = "8504419294:AAFZrDw8pUVrAG29E0it-fZHlN_g3q9PSAs"
bot = telebot.TeleBot(TOKEN)
ADMIN_IDS = [8063642030, 8453400444]

# ====================== Flask ======================
app = Flask(__name__)

# ====================== БД ======================
def db(sql, params=()):
    with sqlite3.connect("bot.db", check_same_thread=False) as c:
        cur = c.cursor()
        cur.execute(sql, params)
        res = cur.fetchall()
        c.commit()
        return res

def init_db():
    db("""CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance REAL DEFAULT 0,
        referrals INTEGER DEFAULT 0,
        referrer INTEGER,
        is_activated INTEGER DEFAULT 0,
        is_banned INTEGER DEFAULT 0
    )""")
    db("""CREATE TABLE IF NOT EXISTS sponsors(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel TEXT,
        link TEXT,
        limit_count INTEGER DEFAULT 0
    )""")
    db("""CREATE TABLE IF NOT EXISTS sponsor_rewards(
        user_id INTEGER,
        sponsor TEXT,
        PRIMARY KEY (user_id, sponsor)
    )""")
    db("""CREATE TABLE IF NOT EXISTS promocodes(
        code TEXT PRIMARY KEY,
        amount REAL,
        max_uses INTEGER,
        uses INTEGER DEFAULT 0
    )""")
    db("""CREATE TABLE IF NOT EXISTS used_promos(
        user_id INTEGER,
        code TEXT,
        PRIMARY KEY (user_id, code)
    )""")
    db("""CREATE TABLE IF NOT EXISTS comment_screens(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        file_id TEXT,
        approved INTEGER DEFAULT 0
    )""")

# ====================== СПОНСОРЫ ======================
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

def sub_keyboard():
    kb = types.InlineKeyboardMarkup()
    sponsors = db("SELECT channel, link FROM sponsors")
    for s in sponsors:
        kb.add(types.InlineKeyboardButton(f"⭐ {s[0]}", url=s[1]))
    kb.add(types.InlineKeyboardButton("✅ Я подписался", callback_data="sub_check"))
    return kb

def block_user(uid):
    db("UPDATE users SET is_activated=0 WHERE user_id=?", (uid,))

def unlock_user(uid):
    db("UPDATE users SET is_activated=1 WHERE user_id=?", (uid,))

# ====================== МЕНЮ ======================
def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🌟 Заработать", callback_data="earn"),
        types.InlineKeyboardButton("📩 Вывод", callback_data="withdraw"),
        types.InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        types.InlineKeyboardButton("🎁 Промокод", callback_data="promo"),
        types.InlineKeyboardButton("🏆 Топ", callback_data="top"),
        types.InlineKeyboardButton("🎁 Бонус", callback_data="bonus")
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

def sponsor_tasks_kb(uid, only_unsub=False):
    kb = types.InlineKeyboardMarkup()
    sponsors = db("SELECT channel, link FROM sponsors")
    for channel, link in sponsors:
        if only_unsub:
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

# ====================== START ======================
@bot.message_handler(commands=["start"])
def start(m):
    uid = m.from_user.id
    uname = m.from_user.username or "user"
    args = m.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

    if not db("SELECT 1 FROM users WHERE user_id=?", (uid,)):
        db("INSERT INTO users (user_id, username, referrer) VALUES (?,?,?)",
           (uid, uname, ref_id if ref_id != uid else None))
        if ref_id and db("SELECT 1 FROM users WHERE user_id=?", (ref_id,)):
            db("UPDATE users SET referrals=referrals+1, balance=balance+8 WHERE user_id=?", (ref_id,))

    if not ensure_subscription(uid):
        block_user(uid)
        bot.send_message(uid, "🔒 Для использования бота подпишитесь на всех спонсоров:", reply_markup=sub_keyboard())
        return

    unlock_user(uid)
    bot.send_message(uid, "✨ Добро пожаловать в <b>DROPSTARSS</b>", reply_markup=main_menu(), parse_mode="HTML")

# ====================== CALLBACK ======================
@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    uid = c.from_user.id

    if not ensure_subscription(uid):
        block_user(uid)
        unsubscribed_channels = []
        for (channel,) in db("SELECT channel FROM sponsors"):
            try:
                status = bot.get_chat_member(channel, uid).status
                if status not in ("member", "administrator", "creator"):
                    unsubscribed_channels.append(channel)
            except:
                unsubscribed_channels.append(channel)
        text = "⚠️ Упс! Ты отписался, подпишись обратно, чтобы продолжить зарабатывать ⭐"
        kb = types.InlineKeyboardMarkup()
        for ch in unsubscribed_channels:
            link = db("SELECT link FROM sponsors WHERE channel=?", (ch,))[0][0]
            kb.add(types.InlineKeyboardButton(f"Подписаться на {ch}", url=link))
        kb.add(types.InlineKeyboardButton("✅ Я подписался", callback_data="check_sponsor_tasks"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=kb)
        return
    else:
        unlock_user(uid)

    # Главное меню
    if c.data == "earn":
        bot.edit_message_text("🌟 Забирай звёзды любым удобным способом:", c.message.chat.id,
                              c.message.message_id, reply_markup=earn_menu())
        return
    if c.data == "back_main":
        bot.edit_message_text("✨ Главное меню:", c.message.chat.id,
                              c.message.message_id, reply_markup=main_menu())
        return
    if c.data == "earn_sub":
        sponsors_list = db("SELECT channel, link FROM sponsors")
        if not sponsors_list:
            bot.edit_message_text("❌ Пока нет доступных спонсоров для подписки", c.message.chat.id, c.message.message_id)
            return
        kb = sponsor_tasks_kb(uid)
        bot.edit_message_text("⭐ За каждую подписку ты получишь <b>0.5 ⭐</b>", c.message.chat.id,
                              c.message.message_id, reply_markup=kb, parse_mode="HTML")
        return
    if c.data == "check_sponsor_tasks":
        total = 0
        for channel, _ in db("SELECT channel, link FROM sponsors"):
            try:
                status = bot.get_chat_member(channel, uid).status
                if status in ("member", "administrator", "creator"):
                    if not db("SELECT 1 FROM sponsor_rewards WHERE user_id=? AND sponsor=?", (uid, channel)):
                        db("INSERT INTO sponsor_rewards VALUES (?,?)", (uid, channel))
                        total += 0.5
            except:
                pass
        if total > 0:
            db("UPDATE users SET balance=balance+? WHERE user_id=?", (total, uid))
            bot.send_message(uid, f"🎉 Начислено {total} ⭐")
        bot.edit_message_text("🌟 Забирай звёзды любым удобным способом:", c.message.chat.id,
                              c.message.message_id, reply_markup=earn_menu())
        return
    if c.data == "earn_refs":
        bot.edit_message_text(f"👥 Пригласи друга и получи <b>8 ⭐</b>\n\n🔗 Твоя ссылка:\nhttps://t.me/{bot.get_me().username}?start={uid}",
                              c.message.chat.id, c.message.message_id, reply_markup=earn_menu(), parse_mode="HTML")
        return

# ====================== ПРОМОКОД ======================
@bot.message_handler(commands=["promo"])
def promo_cmd(m):
    bot.send_message(m.from_user.id, "🎁 Введите промокод:")
    bot.register_next_step_handler(m, use_promo)

def use_promo(m):
    uid = m.from_user.id
    code = m.text.strip().upper()
    promo = db("SELECT amount, max_uses, uses FROM promocodes WHERE code=?", (code,))
    if not promo:
        bot.send_message(uid, "❌ Промокод не найден")
        return
    amount, max_uses, uses = promo[0]
    if uses >= max_uses:
        bot.send_message(uid, "❌ Лимит исчерпан")
        return
    if db("SELECT 1 FROM used_promos WHERE user_id=? AND code=?", (uid, code)):
        bot.send_message(uid, "❌ Вы уже использовали этот код")
        return
    db("UPDATE users SET balance=balance+? WHERE user_id=?", (amount, uid))
    db("UPDATE promocodes SET uses=uses+1 WHERE code=?", (code,))
    db("INSERT INTO used_promos VALUES (?,?)", (uid, code))
    bot.send_message(uid, f"🎉 Промокод активирован! +{amount} ⭐")

# ====================== АДМИН ======================
def notify_all(text):
    for (uid,) in db("SELECT user_id FROM users"):
        try:
            bot.send_message(uid, text, parse_mode="HTML")
        except:
            pass

@bot.message_handler(commands=["add_sponsor"])
def add_sponsor(m):
    if m.from_user.id not in ADMIN_IDS:
        return
    try:
        _, channel, link, limit_ = m.text.split()
        limit_ = int(limit_)
    except:
        bot.send_message(m.chat.id, "❌ /add_sponsor @channel link limit")
        return
    db("INSERT INTO sponsors (channel, link, limit_count) VALUES (?,?,?)", (channel, link, limit_))
    db("UPDATE users SET is_activated=0")
    notify_all("📢 <b>Добавлен новый спонсор!</b>\nПодпишитесь на всех спонсоров для продолжения работы 👇")
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
    db("INSERT INTO sponsors (channel, link) VALUES (?,?)", (channel, link))
    bot.send_message(m.chat.id, "✅ Спонсор добавлен в меню заработка")

# ====================== WEBHOOK ======================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.stream.read().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/")
def index():
    return "DROPSTARSS BOT is running", 200

# ====================== RUN ======================
if __name__ == "__main__":
    init_db()
    bot.remove_webhook()
    WEBHOOK_URL = "https://YOUR_RENDER_DOMAIN.com/" + TOKEN
    bot.set_webhook(WEBHOOK_URL)
    print("DROPSTARSS запущен через webhook на Render")
    app.run(host="0.0.0.0", port=5000)
