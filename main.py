import telebot
from telebot import types
import sqlite3
import time
import os
from flask import Flask
from threading import Thread

# --- НАСТРОЙКИ ---
TOKEN = "8575208075:AAGPuQWeTjo8DbQQgKrJdK4ww86RDvp5vuA"
bot = telebot.TeleBot(TOKEN)

# Список ID админов
ADMIN_IDS = [8063642030, 8453400444] 

# Канал для заявок на вывод
PAYMENT_CHANNEL_ID = "@bobroplata" 

# --- ФЕЙКОВЫЙ СЕРВЕР ДЛЯ RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "EliteStars System Active"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- БАЗА ДАННЫХ ---
DB_PATH = 'bot_database.db'

def db_query(sql, params=()):
    with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        res = cursor.fetchall()
        conn.commit()
        return res

def init_db():
    db_query('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        username TEXT, 
        balance REAL DEFAULT 0, 
        last_bonus INTEGER DEFAULT 0,
        referrals INTEGER DEFAULT 0,
        referrer_id INTEGER DEFAULT 0,
        is_activated INTEGER DEFAULT 0,
        is_banned INTEGER DEFAULT 0,
        last_seen INTEGER DEFAULT 0)''')
    
    db_query('''CREATE TABLE IF NOT EXISTS sponsors (
        channel_id TEXT PRIMARY KEY, 
        link TEXT)''')

    db_query('''CREATE TABLE IF NOT EXISTS promocodes (
        code TEXT PRIMARY KEY, 
        amount REAL, 
        max_uses INTEGER, 
        current_uses INTEGER DEFAULT 0)''')
    
    db_query('''CREATE TABLE IF NOT EXISTS used_promos (
        user_id INTEGER, 
        code TEXT)''')
    
    check = db_query("SELECT count(*) FROM sponsors")
    if check[0][0] == 0:
        db_query("INSERT INTO sponsors (channel_id, link) VALUES (?, ?)", ("@EliteStarsH", "https://t.me/EliteStarsH"))

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def update_activity(uid):
    db_query("UPDATE users SET last_seen = ? WHERE user_id = ?", (int(time.time()), uid))

def get_sponsors():
    return db_query("SELECT channel_id, link FROM sponsors")

def check_sub(user_id):
    sponsors = get_sponsors()
    if not sponsors: return True
    for s in sponsors:
        try:
            status = bot.get_chat_member(s[0], user_id).status
            if status not in ['member', 'administrator', 'creator']:
                return False
        except: continue
    return True

# --- КЛАВИАТУРЫ ---
def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🌟 Заработать звёзды", callback_data="earn"),
        types.InlineKeyboardButton("📩 Вывести звёзды", callback_data="withdraw_menu"),
        types.InlineKeyboardButton("👤 Мой профиль", callback_data="profile"),
        types.InlineKeyboardButton("🎁 Ежедневный бонус", callback_data="bonus"), 
        types.InlineKeyboardButton("🎁 Промокод", callback_data="promo"),          
        types.InlineKeyboardButton("🏆 Топ рефоводов", callback_data="top")
    )
    return markup

def get_withdraw_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("15 ⭐️", callback_data="wd_15"),
        types.InlineKeyboardButton("25 ⭐️", callback_data="wd_25"),
        types.InlineKeyboardButton("50 ⭐️", callback_data="wd_50"),
        types.InlineKeyboardButton("100 ⭐️", callback_data="wd_100"),
        types.InlineKeyboardButton("PREMIUM (350⭐️)", callback_data="wd_350"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")
    )
    return markup

# --- ЛОГИКА ПРОМОКОДОВ ---
def process_promo(message):
    uid = message.from_user.id
    code_text = message.text.strip().upper()
    update_activity(uid)
    
    promo = db_query("SELECT amount, max_uses, current_uses FROM promocodes WHERE code = ?", (code_text,))
    if not promo:
        bot.send_message(message.chat.id, "❌ <b>Промокод не найден.</b>", reply_markup=get_main_menu(), parse_mode="HTML")
        return
    
    amount, max_uses, current_uses = promo[0]
    already_used = db_query("SELECT 1 FROM used_promos WHERE user_id = ? AND code = ?", (uid, code_text))
    
    if already_used:
        bot.send_message(message.chat.id, "⚠️ <b>Вы уже использовали этот код.</b>", reply_markup=get_main_menu(), parse_mode="HTML")
        return

    if current_uses >= max_uses:
        bot.send_message(message.chat.id, "🚫 <b>Лимит активаций исчерпан.</b>", reply_markup=get_main_menu(), parse_mode="HTML")
        return

    db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
    db_query("UPDATE promocodes SET current_uses = current_uses + 1 WHERE code = ?", (code_text,))
    db_query("INSERT INTO used_promos (user_id, code) VALUES (?, ?)", (uid, code_text))
    
    bot.send_message(message.chat.id, f"✅ <b>Начислено {amount} ⭐️</b>", reply_markup=get_main_menu(), parse_mode="HTML")

# --- АДМИН КОМАНДЫ (УПРАВЛЕНИЕ) ---

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id in ADMIN_IDS:
        total = db_query("SELECT count(*) FROM users")[0][0]
        text = (f"🛠 <b>Админ-панель EliteStars</b>\n\n"
                f"📊 Юзеров в базе: <code>{total}</code>\n\n"
                f"➕ <code>/give ID СУММА</code> - Начислить\n"
                f"➖ <code>/take ID СУММА</code> - Забрать\n"
                f"💎 <code>/setbal ID СУММА</code> - Установить\n"
                f"🚫 <code>/ban ID</code> - Забанить\n"
                f"🔓 <code>/unban ID</code> - Разбанить\n"
                f"📢 <code>/send ТЕКСТ</code> - Рассылка")
        bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['give'])
def give_stars(message):
    if message.from_user.id in ADMIN_IDS:
        try:
            parts = message.text.split()
            tid, amt = int(parts[1]), float(parts[2])
            db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amt, tid))
            bot.send_message(message.chat.id, f"✅ Выдано {amt} ⭐️ пользователю <code>{tid}</code>", parse_mode="HTML")
            try: bot.send_message(tid, f"🎁 Админ начислил вам <b>{amt} ⭐️</b>!", parse_mode="HTML")
            except: pass
        except: bot.send_message(message.chat.id, "Ошибка! Формат: `/give ID СУММА`")

@bot.message_handler(commands=['take'])
def take_stars(message):
    if message.from_user.id in ADMIN_IDS:
        try:
            parts = message.text.split()
            tid, amt = int(parts[1]), float(parts[2])
            res = db_query("SELECT balance FROM users WHERE user_id = ?", (tid,))
            if res:
                new_bal = max(0, res[0][0] - amt)
                db_query("UPDATE users SET balance = ? WHERE user_id = ?", (new_bal, tid))
                bot.send_message(message.chat.id, f"✅ Списано {amt} ⭐️. Текущий баланс <code>{tid}</code>: {new_bal}", parse_mode="HTML")
                try: bot.send_message(tid, f"⚠️ С вашего баланса списано <b>{amt} ⭐️</b>.", parse_mode="HTML")
                except: pass
        except: bot.send_message(message.chat.id, "Ошибка! Формат: `/take ID СУММА`")

@bot.message_handler(commands=['setbal'])
def set_balance(message):
    if message.from_user.id in ADMIN_IDS:
        try:
            parts = message.text.split()
            tid, amt = int(parts[1]), float(parts[2])
            db_query("UPDATE users SET balance = ? WHERE user_id = ?", (amt, tid))
            bot.send_message(message.chat.id, f"✅ Баланс <code>{tid}</code> установлен на <b>{amt} ⭐️</b>", parse_mode="HTML")
        except: bot.send_message(message.chat.id, "Ошибка! Формат: `/setbal ID СУММА`")

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id in ADMIN_IDS:
        try:
            tid = int(message.text.split()[1])
            db_query("UPDATE users SET is_banned = 1 WHERE user_id = ?", (tid,))
            bot.send_message(message.chat.id, f"🚫 Юзер <code>{tid}</code> забанен.", parse_mode="HTML")
        except: bot.send_message(message.chat.id, "Формат: `/ban ID`")

@bot.message_handler(commands=['send'])
def broadcast(message):
    if message.from_user.id in ADMIN_IDS:
        text = message.text.replace('/send', '').strip()
        if not text: return bot.send_message(message.chat.id, "Введите текст после /send")
        users = db_query("SELECT user_id FROM users")
        for u in users:
            try: bot.send_message(u[0], text, parse_mode="HTML")
            except: continue
        bot.send_message(message.chat.id, "✅ Рассылка завершена.")

# --- ОСНОВНЫЕ ОБРАБОТЧИКИ ---

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    uname = message.from_user.username or "User"
    update_activity(uid)
    user = db_query("SELECT is_activated, referrer_id, is_banned FROM users WHERE user_id = ?", (uid,))
    
    if user and user[0][2] == 1:
        bot.send_message(message.chat.id, "🚫 Вы заблокированы в системе.")
        return

    if not user:
        ref_id = 0
        args = message.text.split()
        if len(args) > 1:
            try:
                ref_id = int(args[1])
                if ref_id == uid: ref_id = 0
            except: pass
        db_query("INSERT INTO users (user_id, username, referrer_id, is_activated, is_banned, last_seen) VALUES (?, ?, ?, 0, 0, ?)", (uid, uname, ref_id, int(time.time())))
    
    if check_sub(uid):
        user_now = db_query("SELECT is_activated, referrer_id FROM users WHERE user_id = ?", (uid,))
        if user_now and user_now[0][0] == 0:
            rid = user_now[0][1]
            db_query("UPDATE users SET is_activated = 1 WHERE user_id = ?", (uid,))
            if rid != 0:
                db_query("UPDATE users SET balance = balance + 5, referrals = referrals + 1 WHERE user_id = ?", (rid,))
                try: bot.send_message(rid, f"🎉 +5 ⭐️ (реферал @{uname})")
                except: pass
        bot.send_message(message.chat.id, "✨ <b>EliteStars приветствует тебя!</b>", reply_markup=get_main_menu(), parse_mode="HTML")
    else:
        sponsors = get_sponsors()
        markup = types.InlineKeyboardMarkup()
        for i, s in enumerate(sponsors, 1): markup.add(types.InlineKeyboardButton(f"⭐️ Канал №{i}", url=s[1]))
        markup.add(types.InlineKeyboardButton("✅ Я подписался", callback_data="sub_check"))
        bot.send_message(message.chat.id, "⚠️ <b>Подпишитесь:</b>", reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    uid = call.from_user.id
    update_activity(uid)
    
    user_status = db_query("SELECT is_banned FROM users WHERE user_id = ?", (uid,))
    if user_status and user_status[0][0] == 1:
        bot.answer_callback_query(call.id, "🚫 Бан!")
        return

    if call.data.startswith("adm_"):
        if uid not in ADMIN_IDS: return
        action = call.data.split("_")[1]
        try:
            target_uid = int(call.message.text.split("ID ")[1].split("\n")[0])
            status_text = "✅ <b>Выплачено</b>" if action == "ok" else "❌ <b>Отклонено</b>"
            bot.edit_message_text(call.message.text.split("🔄")[0] + status_text, call.message.chat.id, call.message.message_id, parse_mode="HTML")
            bot.send_message(target_uid, f"🔔 Ваша заявка на вывод: {status_text}", parse_mode="HTML")
        except: pass
        return

    if call.data == "sub_check":
        if check_sub(uid):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "✅ Доступ открыт!", reply_markup=get_main_menu())
        return

    res = db_query("SELECT balance, referrals, last_bonus, username FROM users WHERE user_id = ?", (uid,))
    if not res: return
    balance, refs, last_bonus, u_name = res[0]

    if call.data == "main_menu":
        bot.edit_message_text("✨ <b>Меню:</b>", call.message.chat.id, call.message.message_id, reply_markup=get_main_menu(), parse_mode="HTML")
    elif call.data == "profile":
        bot.edit_message_text(f"👤 @{u_name}\n🆔 {uid}\n💰 {balance:.2f} ⭐️\n👥 {refs} реф.", call.message.chat.id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️", callback_data="main_menu")), parse_mode="HTML")
    elif call.data == "earn":
        link = f"https://t.me/{(bot.get_me().username)}?start={uid}"
        bot.edit_message_text(f"🔗 Ссылка:\n<code>{link}</code>", call.message.chat.id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️", callback_data="main_menu")), parse_mode="HTML")
    elif call.data == "bonus":
        now = int(time.time())
        if now - last_bonus >= 86400:
            db_query("UPDATE users SET balance = balance + 1, last_bonus = ? WHERE user_id = ?", (now, uid))
            bot.answer_callback_query(call.id, "🎁 +1 ⭐️!", show_alert=True)
        else: bot.answer_callback_query(call.id, "⏰ Завтра!", show_alert=True)
    elif call.data == "promo":
        msg = bot.send_message(call.message.chat.id, "🎁 Введите код:")
        bot.register_next_step_handler(msg, process_promo)
    elif call.data == "withdraw_menu":
        bot.edit_message_text("💳 Сумма вывода:", call.message.chat.id, call.message.message_id, reply_markup=get_withdraw_keyboard(), parse_mode="HTML")
    elif call.data.startswith("wd_"):
        amount = int(call.data.split("_")[1])
        if balance >= amount:
            pay_text = f"🌟 <b>Заявка!</b>\n👤 ID <code>{uid}</code>\n💰 <b>{amount} ⭐️</b>\n🔄 Статус: Ожидает обработки ⚙️"
            m = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("✅", callback_data="adm_ok"), types.InlineKeyboardButton("❌", callback_data="adm_no"))
            bot.send_message(PAYMENT_CHANNEL_ID, pay_text, reply_markup=m, parse_mode="HTML")
            db_query("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, uid))
            bot.answer_callback_query(call.id, "✅ Создано!", show_alert=True)
        else: bot.answer_callback_query(call.id, "❌ Мало звёзд!", show_alert=True)
    elif call.data == "top":
        top = db_query("SELECT username, referrals FROM users ORDER BY referrals DESC LIMIT 10")
        text = "🏆 <b>Топ рефоводов:</b>\n\n"
        for i, u in enumerate(top, 1): text += f"{i}. @{u[0]} — {u[1]} реф.\n"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️", callback_data="main_menu")), parse_mode="HTML")

if __name__ == '__main__':
    init_db()
    Thread(target=run_web).start()
    bot.infinity_polling()
    
